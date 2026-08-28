#!/usr/bin/env python3
"""Run/finalize the single v1.8.0 G3 content and visual release gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


# Keep the user-visible C: workspace spelling.  ``resolve()`` follows a local
# junction to a legacy D: alias whose non-ASCII name cannot be opened by the
# bundled Poppler executable.
ROOT = Path(__file__).absolute().parents[1]
OUT = ROOT / "qa" / "gates" / "G3"
VISUAL = OUT / "visual"
CANDIDATE = ROOT / "candidate-build" / "merged_full" / "main_full.pdf"
BASELINE = ROOT / "baseline-build" / "merged_full" / "main_full.pdf"
PRELIMINARY = OUT / "G3_visual_numeric_preliminary.json"
FINAL_REPORT = OUT / "G3_gate_report.json"

CASES = {
    "P1_ALG001_gradient": {"fragment": "算法3.1：固定步长梯度下降", "baseline_page": 42},
    "P1_ALG002_dirichlet": {"fragment": "闭式更新与后验预测", "baseline_page": 600},
    "P1_ALG003_rejection": {"fragment": "31.3A输入归一化密度", "baseline_page": 527},
    "P1_MATH001_svd": {"fragment": "截断奇异值分解", "baseline_page": 414},
    "RISK_PLSA": {"fragment": "一次完整E步与M步"},
    "RISK_Gibbs": {"fragment": "五分类模型的可复算Gibbs目标"},
    "RISK_Dirichlet_evidence": {"fragment": "计数证据与序列证据"},
    "RISK_PageRank": {"fragment": "三结点幂法与概率归一化"},
}


def normalized(text: str) -> str:
    return "".join(text.split())


def locate_pages(pdf: Path) -> dict[str, int]:
    with fitz.open(pdf) as document:
        texts = [normalized(page.get_text()) for page in document]
    pages: dict[str, int] = {}
    for name, spec in CASES.items():
        hits = [index + 1 for index, text in enumerate(texts) if str(spec["fragment"]) in text]
        if not hits:
            raise ValueError(f"{name}: no page found for {spec['fragment']!r}")
        # Subject/symbol indexes can repeat a title near the end of the book;
        # the earliest hit is the chapter-body occurrence under review.
        pages[name] = hits[0]
    return pages


def render_mupdf(pdf: Path, page_number: int, output: Path, dpi: float, grayscale: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf) as document:
        colorspace = fitz.csGRAY if grayscale else fitz.csRGB
        pixmap = document[page_number - 1].get_pixmap(
            matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0),
            colorspace=colorspace,
            alpha=False,
        )
        pixmap.save(output)


def render_poppler(pdf: Path, page_number: int, output: Path, dpi: float, grayscale: bool = False) -> None:
    # Prefer the real executable.  The dependency runtime also exposes a
    # ``pdftoppm.CMD`` override that cannot forward this Chinese-path cwd.
    executable = shutil.which("pdftoppm.exe") or shutil.which("pdftoppm")
    if not executable:
        raise RuntimeError("pdftoppm is unavailable")
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = output.with_suffix("")
    arguments = [
        executable, "-f", str(page_number), "-l", str(page_number),
        "-r", str(dpi), "-singlefile",
    ]
    arguments.append("-gray" if grayscale else "-png")
    if grayscale:
        arguments.append("-png")
    # The bundled Windows Poppler executable is not reliable with a Chinese
    # absolute path.  Both inputs are inside ROOT, so use portable relative
    # paths under a controlled working directory.
    arguments.extend([
        str(pdf.relative_to(ROOT)),
        str(prefix.relative_to(ROOT)),
    ])
    completed = subprocess.run(arguments, cwd=ROOT, capture_output=True, check=False)
    if completed.returncode != 0 or not output.is_file():
        raise RuntimeError(
            f"Poppler render failed for page {page_number}: "
            + completed.stderr.decode(errors="replace")
        )


def structural_correlation(first: Path, second: Path) -> dict[str, object]:
    with Image.open(first) as left_raw, Image.open(second) as right_raw:
        left = left_raw.convert("L")
        right = right_raw.convert("L")
        dimensions_equal = left.size == right.size
        target = (256, 362)
        left_array = np.asarray(left.resize(target, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(0.7)), dtype=float)
        right_array = np.asarray(right.resize(target, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(0.7)), dtype=float)
    correlation = float(np.corrcoef(left_array.ravel(), right_array.ravel())[0, 1])
    return {
        "dimensions_equal": dimensions_equal,
        "first_size": list(left.size),
        "second_size": list(right.size),
        "correlation": round(correlation, 6),
        "first_stddev": round(float(left_array.std()), 3),
        "second_stddev": round(float(right_array.std()), 3),
        "passed": bool(
            dimensions_equal
            and correlation >= 0.985
            and left_array.std() >= 10
            and right_array.std() >= 10
        ),
    }


def make_contact_sheet(items: list[tuple[str, Path]], output: Path, columns: int = 2, cell_width: int = 440) -> None:
    margin = 14
    label_height = 24
    thumbnails: list[tuple[str, Image.Image]] = []
    for label, path in items:
        with Image.open(path) as raw:
            image = raw.convert("RGB")
            height = round(cell_width * image.height / image.width)
            thumbnails.append((label, image.resize((cell_width, height), Image.Resampling.LANCZOS)))
    cell_height = max(image.height for _, image in thumbnails) + label_height
    rows = math.ceil(len(thumbnails) / columns)
    sheet = Image.new(
        "RGB",
        (columns * (cell_width + margin) + margin, rows * (cell_height + margin) + margin),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(thumbnails):
        row, column = divmod(index, columns)
        x = margin + column * (cell_width + margin)
        y = margin + row * (cell_height + margin)
        draw.text((x, y), label, fill="black")
        sheet.paste(image, (x, y + label_height))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def make_spread(left_path: Path, right_path: Path, output: Path) -> None:
    with Image.open(left_path) as left_raw, Image.open(right_path) as right_raw:
        left = left_raw.convert("RGB")
        right = right_raw.convert("RGB")
        height = max(left.height, right.height)
        canvas = Image.new("RGB", (left.width + right.width + 20, height), "#e6e6e6")
        canvas.paste(left, (0, 0))
        canvas.paste(right, (left.width + 20, 0))
    canvas.save(output)


def make_mobile_crops(source: Path, output_dir: Path) -> list[Path]:
    with Image.open(source) as raw:
        image = raw.convert("RGB")
        width = 1280
        scaled = image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
    positions = {
        "top": 0,
        "middle": max(0, (scaled.height - 720) // 2),
        "bottom": max(0, scaled.height - 720),
    }
    outputs = []
    for label, top in positions.items():
        crop = scaled.crop((0, top, width, min(top + 720, scaled.height)))
        if crop.height < 720:
            crop = ImageOps.pad(crop, (width, 720), color="white", centering=(0.5, 0.0))
        path = output_dir / f"mobile-landscape-{label}.png"
        crop.save(path)
        outputs.append(path)
    return outputs


def run_numeric_tests() -> dict[str, object]:
    arguments = [
        sys.executable, "-m", "unittest", "-v",
        "tests.test_p1_algorithms",
        "tests.test_svd_boundaries",
        "tests.test_high_complexity_examples",
    ]
    completed = subprocess.run(
        arguments, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=False,
    )
    log = OUT / "G3_independent_numeric_tests.log"
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    match = __import__("re").search(r"Ran\s+(\d+)\s+tests?", completed.stdout + completed.stderr)
    count = int(match.group(1)) if match else None
    return {
        "passed": completed.returncode == 0 and count == 24,
        "tests_run": count,
        "command": arguments,
        "log": str(log.relative_to(ROOT).as_posix()),
    }


def render_and_test() -> int:
    if PRELIMINARY.exists() or FINAL_REPORT.exists():
        raise FileExistsError("refusing to repeat the one-time G3 gate")
    OUT.mkdir(parents=True, exist_ok=True)
    VISUAL.mkdir(parents=True, exist_ok=True)
    if not CANDIDATE.is_file() or not BASELINE.is_file():
        raise FileNotFoundError("candidate or baseline merged PDF is missing")

    pages = locate_pages(CANDIDATE)
    comparisons = {}
    mupdf_items = []
    poppler_items = []
    for name, page_number in pages.items():
        mupdf_path = VISUAL / "mupdf" / f"{name}-p{page_number:03d}.png"
        poppler_path = VISUAL / "poppler" / f"{name}-p{page_number:03d}.png"
        render_mupdf(CANDIDATE, page_number, mupdf_path, 150)
        render_poppler(CANDIDATE, page_number, poppler_path, 150)
        metric = structural_correlation(mupdf_path, poppler_path)
        metric.update({
            "page": page_number,
            "mupdf": str(mupdf_path.relative_to(ROOT).as_posix()),
            "poppler": str(poppler_path.relative_to(ROOT).as_posix()),
        })
        comparisons[name] = metric
        mupdf_items.append((f"{name} p{page_number}", mupdf_path))
        poppler_items.append((f"{name} p{page_number}", poppler_path))

    make_contact_sheet(mupdf_items[:4], VISUAL / "dual-render-p1-mupdf.png", columns=2)
    make_contact_sheet(poppler_items[:4], VISUAL / "dual-render-p1-poppler.png", columns=2)
    make_contact_sheet(mupdf_items[4:], VISUAL / "dual-render-risk-mupdf.png", columns=2)
    make_contact_sheet(poppler_items[4:], VISUAL / "dual-render-risk-poppler.png", columns=2)

    baseline_pairs = []
    for name, spec in CASES.items():
        if "baseline_page" not in spec:
            continue
        baseline_page = int(spec["baseline_page"])
        candidate_page = pages[name]
        baseline_path = VISUAL / "baseline" / f"{name}-baseline-p{baseline_page:03d}.png"
        candidate_path = VISUAL / "baseline" / f"{name}-candidate-p{candidate_page:03d}.png"
        render_mupdf(BASELINE, baseline_page, baseline_path, 110)
        render_mupdf(CANDIDATE, candidate_page, candidate_path, 110)
        baseline_pairs.extend([
            (f"{name} BASE p{baseline_page}", baseline_path),
            (f"{name} CAND p{candidate_page}", candidate_path),
        ])
    make_contact_sheet(baseline_pairs, VISUAL / "p1-baseline-regression.png", columns=2, cell_width=400)

    hundred_percent = []
    for name in list(CASES)[:4]:
        path = VISUAL / "scenarios" / f"100pct-{name}.png"
        render_mupdf(CANDIDATE, pages[name], path, 96)
        hundred_percent.append((f"{name} 100pct", path))
    make_contact_sheet(hundred_percent, VISUAL / "scenario-100pct.png", columns=2)

    grayscale_items = []
    for name in list(CASES)[4:]:
        path = VISUAL / "scenarios" / f"gray-{name}.png"
        render_poppler(CANDIDATE, pages[name], path, 150, grayscale=True)
        grayscale_items.append((f"{name} gray", path))
    make_contact_sheet(grayscale_items, VISUAL / "scenario-grayscale.png", columns=2)

    spread_left = VISUAL / "scenarios" / "spread-left.png"
    spread_right = VISUAL / "scenarios" / "spread-right.png"
    spread_page = pages["RISK_PageRank"]
    render_mupdf(CANDIDATE, spread_page, spread_left, 96)
    render_mupdf(CANDIDATE, spread_page + 1, spread_right, 96)
    make_spread(spread_left, spread_right, VISUAL / "scenario-double-page.png")
    mobile_paths = make_mobile_crops(
        VISUAL / "mupdf" / f"RISK_PageRank-p{spread_page:03d}.png",
        VISUAL / "scenarios",
    )

    numeric = run_numeric_tests()
    dual_passed = all(item["passed"] for item in comparisons.values())
    preliminary = {
        "schema_version": 1,
        "gate": "G3",
        "phase": "visual_numeric_complete_waiting_manual_and_closure",
        "executed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "candidate_pdf": str(CANDIDATE.relative_to(ROOT).as_posix()),
        "baseline_pdf": str(BASELINE.relative_to(ROOT).as_posix()),
        "candidate_pages": pages,
        "dual_renderer": {
            "passed": dual_passed,
            "engines": ["MuPDF via PyMuPDF", "Poppler via pdftoppm"],
            "comparisons": comparisons,
        },
        "numeric_tests": numeric,
        "scenario_evidence": {
            "one_hundred_percent": "qa/gates/G3/visual/scenario-100pct.png",
            "grayscale": "qa/gates/G3/visual/scenario-grayscale.png",
            "double_page": "qa/gates/G3/visual/scenario-double-page.png",
            "mobile_landscape": [str(path.relative_to(ROOT).as_posix()) for path in mobile_paths],
            "baseline_regression": "qa/gates/G3/visual/p1-baseline-regression.png",
        },
        "automatic_passed": dual_passed and bool(numeric["passed"]),
    }
    PRELIMINARY.write_text(json.dumps(preliminary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": "G3", "phase": "preliminary", "passed": preliminary["automatic_passed"], "pages": pages}, ensure_ascii=False))
    return 0 if preliminary["automatic_passed"] else 1


def recover_preliminary() -> int:
    """Recover the report after the completed run hit JSON serialization."""
    if PRELIMINARY.exists() or FINAL_REPORT.exists():
        raise FileExistsError("G3 report already exists")
    pages = locate_pages(CANDIDATE)
    comparisons = {}
    for name, page_number in pages.items():
        mupdf_path = VISUAL / "mupdf" / f"{name}-p{page_number:03d}.png"
        poppler_path = VISUAL / "poppler" / f"{name}-p{page_number:03d}.png"
        if not mupdf_path.is_file() or not poppler_path.is_file():
            raise FileNotFoundError(f"missing completed renderer evidence for {name}")
        metric = structural_correlation(mupdf_path, poppler_path)
        metric.update({
            "page": page_number,
            "mupdf": str(mupdf_path.relative_to(ROOT).as_posix()),
            "poppler": str(poppler_path.relative_to(ROOT).as_posix()),
        })
        comparisons[name] = metric
    log = OUT / "G3_independent_numeric_tests.log"
    text = log.read_text(encoding="utf-8")
    match = __import__("re").search(r"Ran\s+(\d+)\s+tests?", text)
    count = int(match.group(1)) if match else None
    numeric = {
        "passed": count == 24 and "\nOK\n" in f"\n{text}",
        "tests_run": count,
        "command": [
            sys.executable, "-m", "unittest", "-v",
            "tests.test_p1_algorithms", "tests.test_svd_boundaries",
            "tests.test_high_complexity_examples",
        ],
        "log": str(log.relative_to(ROOT).as_posix()),
        "report_recovered_without_rerun": True,
    }
    required = [
        VISUAL / "scenario-100pct.png",
        VISUAL / "scenario-grayscale.png",
        VISUAL / "scenario-double-page.png",
        VISUAL / "p1-baseline-regression.png",
        VISUAL / "scenarios" / "mobile-landscape-top.png",
        VISUAL / "scenarios" / "mobile-landscape-middle.png",
        VISUAL / "scenarios" / "mobile-landscape-bottom.png",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing scenario evidence: " + ", ".join(missing))
    dual_passed = all(item["passed"] for item in comparisons.values())
    preliminary = {
        "schema_version": 1,
        "gate": "G3",
        "phase": "visual_numeric_complete_waiting_manual_and_closure",
        "executed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "candidate_pdf": str(CANDIDATE.relative_to(ROOT).as_posix()),
        "baseline_pdf": str(BASELINE.relative_to(ROOT).as_posix()),
        "candidate_pages": pages,
        "dual_renderer": {
            "passed": dual_passed,
            "engines": ["MuPDF via PyMuPDF", "Poppler via pdftoppm"],
            "comparisons": comparisons,
            "report_recovered_from_existing_renders": True,
        },
        "numeric_tests": numeric,
        "scenario_evidence": {
            "one_hundred_percent": "qa/gates/G3/visual/scenario-100pct.png",
            "grayscale": "qa/gates/G3/visual/scenario-grayscale.png",
            "double_page": "qa/gates/G3/visual/scenario-double-page.png",
            "mobile_landscape": [str(path.relative_to(ROOT).as_posix()) for path in required[-3:]],
            "baseline_regression": "qa/gates/G3/visual/p1-baseline-regression.png",
        },
        "automatic_passed": dual_passed and bool(numeric["passed"]),
    }
    PRELIMINARY.write_text(json.dumps(preliminary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": "G3", "phase": "recovered", "passed": preliminary["automatic_passed"], "pages": pages}, ensure_ascii=False))
    return 0 if preliminary["automatic_passed"] else 1


def closure_status(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = list(reader)
    statuses: dict[str, int] = {}
    for row in rows:
        statuses[row[14]] = statuses.get(row[14], 0) + 1
    passed = len(rows) == 199 and statuses == {"verified": 196, "not_applicable_verified": 3}
    return {"passed": passed, "rows": len(rows), "columns": len(header), "status_counts": statuses}


def finalize(final_closure: Path, manual_record: Path) -> int:
    if not PRELIMINARY.is_file():
        raise FileNotFoundError(PRELIMINARY)
    if FINAL_REPORT.exists():
        raise FileExistsError("refusing to repeat G3 finalization")
    preliminary = json.loads(PRELIMINARY.read_text(encoding="utf-8"))
    if not preliminary.get("automatic_passed"):
        raise RuntimeError("automatic G3 phase did not pass")
    if not manual_record.is_file():
        raise FileNotFoundError(manual_record)
    manual = json.loads(manual_record.read_text(encoding="utf-8"))
    closure = closure_status(final_closure)
    passed = bool(manual.get("passed")) and bool(closure["passed"])
    report = {
        "schema_version": 1,
        "gate": "G3",
        "scope": "release content and visual gate",
        "executed_at": preliminary["executed_at"],
        "finalized_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "passed": passed,
        "automatic": preliminary,
        "manual_visual_review": manual,
        "final_closure": {
            **closure,
            "file": str(final_closure.relative_to(ROOT).as_posix()),
        },
        "limitations": [
            "The third authority PDF remains missing, so H0 cannot yet be produced.",
        ],
    }
    FINAL_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": "G3", "passed": passed, "report": str(FINAL_REPORT)}, ensure_ascii=False))
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("render-and-test")
    subparsers.add_parser("recover-report")
    final_parser = subparsers.add_parser("finalize")
    final_parser.add_argument("--closure", type=Path, required=True)
    final_parser.add_argument("--manual-record", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "render-and-test":
        return render_and_test()
    if args.command == "recover-report":
        return recover_preliminary()
    # Keep Windows junction/redirected Desktop paths on the same drive spelling as ROOT.
    # Path.resolve() dereferences the workspace junction from C: to D: on this host,
    # which makes an otherwise in-tree closure fail relative_to(ROOT).
    return finalize(args.closure.absolute(), args.manual_record.absolute())


if __name__ == "__main__":
    raise SystemExit(main())
