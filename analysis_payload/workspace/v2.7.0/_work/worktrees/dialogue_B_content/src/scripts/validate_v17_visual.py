from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import fitz
import numpy as np
from PIL import Image


WORKSPACE = Path(__file__).resolve().parents[1]
TEST_DIR = WORKSPACE / "tests"
EXPECTED_FULL_NAME = "统计学习方法初学者讲义_合并总册v1.7.0_完整解析版.pdf"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def scan_rendered_pages(directory: Path, expected: int) -> dict[str, object]:
    images = sorted(directory.glob("page-*.png"))
    dimensions: Counter[tuple[int, int]] = Counter()
    sparse: list[dict[str, object]] = []
    edge_hits: list[int] = []
    for page_number, path in enumerate(images, 1):
        with Image.open(path) as image:
            dimensions[image.size] += 1
            gray = image.convert("L").resize((150, 212))
            pixels = np.asarray(gray)
        ink = pixels < 248
        coverage = float(ink.mean())
        if coverage < 0.006:
            sparse.append({"page": page_number, "ink_coverage": round(coverage, 6)})
        border = np.concatenate((ink[:2, :].ravel(), ink[-2:, :].ravel(), ink[:, :2].ravel(), ink[:, -2:].ravel()))
        if border.mean() > 0.002:
            edge_hits.append(page_number)
    return {
        "expected_pages": expected,
        "rendered_pages": len(images),
        "dimensions": {f"{width}x{height}": count for (width, height), count in dimensions.items()},
        "sparse_pages": sparse,
        "edge_ink_pages": edge_hits,
    }


def scan_fonts(pdf: Path) -> dict[str, object]:
    executable = shutil.which("pdffonts")
    if not executable:
        raise RuntimeError("pdffonts is not available on PATH")
    result = subprocess.run([executable, str(pdf)], check=True, capture_output=True, text=True, errors="replace")
    rows = [line for line in result.stdout.splitlines()[2:] if line.strip()]
    not_embedded = [line for line in rows if not re.search(r"\byes\s+(?:yes|no)\s+yes\b", line)]
    return {"font_rows": len(rows), "not_embedded_or_not_unicode": not_embedded}


def scan_pdf(pdf: Path) -> dict[str, object]:
    document = fitz.open(pdf)
    out_of_bounds: list[dict[str, object]] = []
    invalid_links: list[dict[str, object]] = []
    launch_files: Counter[str] = Counter()
    contract_links = 0
    empty_text_pages: list[int] = []
    for page_number, page in enumerate(document, 1):
        page_rect = page.rect
        if not page.get_text().strip():
            empty_text_pages.append(page_number)
        for block in page.get_text("blocks"):
            block_rect = fitz.Rect(block[:4])
            if not page_rect.contains(block_rect + (-0.5, -0.5, 0.5, 0.5)):
                out_of_bounds.append({"page": page_number, "bbox": [round(value, 3) for value in block[:4]]})
        for link in page.get_links():
            target = link.get("page", -1)
            if target is not None and target >= len(document):
                invalid_links.append({"page": page_number, "target": target})
            if link.get("nameddest") == "SL:algorithm-contract":
                contract_links += 1
            if link.get("kind") == fitz.LINK_GOTOR and link.get("file"):
                launch_files[unquote(str(link["file"]))] += 1
    return {
        "pages": len(document),
        "empty_text_pages": empty_text_pages,
        "out_of_bounds_text_blocks": out_of_bounds,
        "invalid_links": invalid_links,
        "contract_links": contract_links,
        "launch_files": dict(launch_files),
        "fonts": scan_fonts(pdf),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v1.7.0 PDFs and 180 dpi page renders.")
    parser.add_argument("--render-root", type=Path, required=True)
    parser.add_argument("--default", dest="default_pdf", type=Path, required=True)
    parser.add_argument("--student", type=Path, required=True)
    parser.add_argument("--full", type=Path, required=True)
    args = parser.parse_args()
    paths = {"default": args.default_pdf.resolve(), "student": args.student.resolve(), "full": args.full.resolve()}
    render_root = args.render_root.resolve()
    pdfs = {name: scan_pdf(path) for name, path in paths.items()}
    renders = {name: scan_rendered_pages(render_root / name, pdfs[name]["pages"]) for name in paths}
    checks = {
        "all_pages_rendered": all(r["rendered_pages"] == r["expected_pages"] for r in renders.values()),
        "all_renders_are_180dpi_a4": all(r["dimensions"] == {"1489x2105": r["expected_pages"]} for r in renders.values()),
        "no_rendered_page_has_edge_ink": all(not r["edge_ink_pages"] for r in renders.values()),
        "no_empty_text_pages": all(not p["empty_text_pages"] for p in pdfs.values()),
        "no_out_of_bounds_text_blocks": all(not p["out_of_bounds_text_blocks"] for p in pdfs.values()),
        "no_invalid_internal_links": all(not p["invalid_links"] for p in pdfs.values()),
        "fonts_embedded_and_unicode": all(not p["fonts"]["not_embedded_or_not_unicode"] for p in pdfs.values()),
        "all_editions_have_70_algorithm_contract_links": all(p["contract_links"] == 70 for p in pdfs.values()),
        "student_has_37_full_edition_links": (
            pdfs["student"]["launch_files"].get(EXPECTED_FULL_NAME, 0) == 37
            and sum(pdfs["student"]["launch_files"].values()) == 37
        ),
    }
    passed = all(checks.values())
    report = {
        "generated_at": now_iso(),
        "passed": passed,
        "checks": checks,
        "pdfs": pdfs,
        "renders": renders,
    }
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_DIR / "v1.7_visual_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# v1.7.0 PDF 全页视觉与结构审计",
        "",
        f"生成时间：{report['generated_at']}",
        f"结论：{'通过' if passed else '未通过'}（{sum(checks.values())}/{len(checks)} checks passed）",
        "",
        "| Check | 结果 |",
        "|---|---|",
    ]
    lines.extend(f"| {name} | {'PASS' if value else 'FAIL'} |" for name, value in checks.items())
    lines += ["", "## 稀疏页候选（供人工复核）", ""]
    for name, evidence in renders.items():
        pages = ", ".join(str(row["page"]) for row in evidence["sparse_pages"]) or "无"
        lines.append(f"- {name}: {pages}")
    lines.append("")
    (TEST_DIR / "v1.7_visual_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"checks": len(checks), "passed": passed, "failed": len(checks)-sum(checks.values())}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
