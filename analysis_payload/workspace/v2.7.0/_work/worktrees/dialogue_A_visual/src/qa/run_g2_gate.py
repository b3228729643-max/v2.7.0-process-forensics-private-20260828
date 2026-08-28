#!/usr/bin/env python3
"""Run the formal v1.8.0 G2 candidate-PDF technical gate."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import fitz

from pdf_layout_audit import audit_pdf


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "讲义源码"
OUT = ROOT / "qa" / "gates" / "G2"
TEXT_WIDTH_PT = (210.0 - 28.0 - 24.0) / 25.4 * 72.0

PDF_SPECS = {
    "merged_full": (ROOT / "candidate-build" / "merged_full" / "main_full.pdf", 718),
    "volume1": (ROOT / "candidate-build" / "volume1" / "main.pdf", 179),
    "volume2": (ROOT / "candidate-build" / "volume2" / "main.pdf", 98),
    "volume3": (ROOT / "candidate-build" / "volume3" / "main.pdf", 150),
    "volume4": (ROOT / "candidate-build" / "volume4" / "main.pdf", 121),
    "volume5": (ROOT / "candidate-build" / "volume5" / "main.pdf", 198),
}

LOG_BLOCKERS = {
    "latex_error": re.compile(r"LaTeX Error|Undefined control sequence|Emergency stop|Fatal error", re.I),
    "undefined_reference": re.compile(r"Reference .* undefined|There were undefined references", re.I),
    "undefined_citation": re.compile(r"Citation .* undefined|There were undefined citations", re.I),
    "missing_character": re.compile(r"Missing character:", re.I),
    "overfull": re.compile(r"Overfull \\hbox|Overfull \\vbox", re.I),
    "duplicate_destination": re.compile(r"destination with the same identifier|duplicate destination", re.I),
    "multiply_defined_label": re.compile(r"multiply[- ]defined labels?|Label .* multiply defined", re.I),
    "unstable_cross_reference": re.compile(r"Label\(s\) may have changed|Rerun to get cross-references right", re.I),
}


def log_path(pdf: Path) -> Path:
    return pdf.with_suffix(".log")


def audit_logs() -> dict[str, object]:
    reports: dict[str, object] = {}
    passed = True
    for name, (pdf, _) in PDF_SPECS.items():
        path = log_path(pdf)
        text = path.read_text(encoding="utf-8", errors="replace")
        counts = {key: len(pattern.findall(text)) for key, pattern in LOG_BLOCKERS.items()}
        underfull = len(re.findall(r"Underfull \\hbox|Underfull \\vbox", text, re.I))
        current_pass = all(value == 0 for value in counts.values())
        passed &= current_pass
        reports[name] = {
            "passed": current_pass,
            "log": str(path.relative_to(ROOT).as_posix()),
            "blocker_counts": counts,
            "underfull_nonblocking": underfull,
        }
    return {"passed": passed, "pdfs": reports}


def audit_fonts() -> dict[str, object]:
    executable = shutil.which("pdffonts") or shutil.which("pdffonts.exe")
    if not executable:
        return {"passed": False, "error": "pdffonts is unavailable"}
    reports: dict[str, object] = {}
    passed = True
    for name, (pdf, _) in PDF_SPECS.items():
        completed = subprocess.run(
            [executable, str(pdf)], capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
        (OUT / f"{name}-pdffonts.txt").write_text(
            completed.stdout + completed.stderr, encoding="utf-8"
        )
        rows = []
        for line in completed.stdout.splitlines()[2:]:
            parts = line.split()
            if len(parts) >= 8:
                rows.append({"name": parts[0], "embedded": parts[-5], "subset": parts[-4], "unicode": parts[-3]})
        not_embedded = [row["name"] for row in rows if row["embedded"].lower() != "yes"]
        current_pass = completed.returncode == 0 and bool(rows) and not not_embedded
        passed &= current_pass
        reports[name] = {
            "passed": current_pass,
            "font_rows": len(rows),
            "not_embedded": not_embedded,
            "evidence": str((OUT / f"{name}-pdffonts.txt").relative_to(ROOT).as_posix()),
        }
    return {"passed": passed, "pdfs": reports}


def audit_layouts() -> dict[str, object]:
    reports = {}
    passed = True
    for name, (pdf, expected_pages) in PDF_SPECS.items():
        report = audit_pdf(pdf, exempt_pages=range(1, 5))
        summary = report["summary"]
        minimum = min(
            stat["minimum_font_pt"]
            for stat in report["pages"]
            if stat["minimum_font_pt"] is not None
        )
        current_pass = (
            report["page_count"] == expected_pages
            and not summary["pages_with_characters_below_6pt"]
            and not summary["pages_with_characters_below_7_5pt"]
            and not summary["sparse_pages"]
            and not summary["incomplete_chapter_cards"]
            and not summary["oversized_chapter_cards"]
        )
        passed &= current_pass
        reports[name] = {
            "passed": current_pass,
            "pdf": str(pdf.relative_to(ROOT).as_posix()),
            "bytes": pdf.stat().st_size,
            "page_count": report["page_count"],
            "minimum_font_pt": minimum,
            "summary": summary,
        }
    path = OUT / "candidate_layout_audit.json"
    path.write_text(json.dumps({"reports": reports}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"passed": passed, "reports": reports, "evidence": str(path.relative_to(ROOT).as_posix())}


def audit_links_metadata() -> dict[str, object]:
    reports = {}
    passed = True
    for name, (pdf, expected_pages) in PDF_SPECS.items():
        with fitz.open(pdf) as document:
            toc = document.get_toc(simple=True)
            internal_links = 0
            unresolved_internal = 0
            for page in document:
                for link in page.get_links():
                    if link.get("kind") in {fitz.LINK_GOTO, fitz.LINK_NAMED}:
                        internal_links += 1
                        if int(link.get("page", -1)) < 0:
                            unresolved_internal += 1
            metadata = document.metadata or {}
            cover_text = document[0].get_text()
            toc_pages_valid = all(1 <= int(item[2]) <= expected_pages for item in toc if len(item) >= 3)
        version_fields = {
            key: "v1.8.0" in str(metadata.get(key, ""))
            for key in ("title", "subject", "keywords")
        }
        current_pass = (
            len(toc) >= 10
            and toc_pages_valid
            and internal_links > expected_pages
            and unresolved_internal == 0
            and all(version_fields.values())
            and "v1.8.0" in cover_text
        )
        passed &= current_pass
        reports[name] = {
            "passed": current_pass,
            "toc_entries": len(toc),
            "toc_pages_valid": toc_pages_valid,
            "internal_links": internal_links,
            "unresolved_internal_links": unresolved_internal,
            "version_in_metadata": version_fields,
            "version_on_cover": "v1.8.0" in cover_text,
            "metadata": metadata,
        }
    return {"passed": passed, "pdfs": reports}


def source_inventory() -> dict[str, object]:
    chapters = sorted(path for path in SOURCE.rglob("V*-C*.tex") if "chapters" in path.parts)
    texts = [path.read_text(encoding="utf-8") for path in chapters]
    corpus = "\n".join(texts)
    example_labels = re.findall(r"\\label\{(exm:[^{}]+)\}", corpus)
    exercise_labels = re.findall(r"\\label\{(ex:[^{}]+)\}", corpus)
    solution_labels = re.findall(r"\\label\{(sol:[^{}]+)\}", corpus)
    exercise_suffixes = {label[3:] for label in exercise_labels}
    solution_suffixes = {label[4:] for label in solution_labels}
    checks = {
        "chapter_files_37": len(chapters) == 37,
        "chapter_declarations_37": corpus.count(r"\chapter{") == 37,
        "examples_64": corpus.count(r"\begin{example}") == corpus.count(r"\end{example}") == 64,
        "example_labels_64_unique": len(example_labels) == len(set(example_labels)) == 64,
        "exercises_553": corpus.count(r"\begin{exercise}") == 553,
        "exercise_labels_553_unique": len(exercise_labels) == len(set(exercise_labels)) == 553,
        "solution_labels_553_unique": len(solution_labels) == len(set(solution_labels)) == 553,
        "exercise_solution_suffixes_pair": exercise_suffixes == solution_suffixes,
        "solution_environments_balanced": corpus.count(r"\begin{solution}") == corpus.count(r"\end{solution}") == 558,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "counts": {
            "chapters": len(chapters),
            "examples": corpus.count(r"\begin{example}"),
            "example_labels": len(example_labels),
            "exercises": len(exercise_labels),
            "solutions": len(solution_labels),
            "solution_environments": corpus.count(r"\begin{solution}"),
        },
    }


def find_page(document: fitz.Document, normalized_fragment: str) -> int:
    for index, page in enumerate(document):
        normalized = "".join(page.get_text().split())
        if normalized_fragment in normalized:
            return index
    raise ValueError(f"caption fragment not found: {normalized_fragment}")


def target_figure_widths() -> dict[str, object]:
    cases = {
        "figure_4_1": ("volume1", "离散随机变量的分布函数", "离散随机"),
        "figure_31_2": ("volume5", "蒙特卡罗积分把曲线下的面积", "蒙特卡罗积分"),
        "figure_35_3": ("volume5", "生成过程先为每个主题", "生成过程"),
    }
    reports = {}
    passed = True
    for label, (pdf_name, normalized_fragment, search_fragment) in cases.items():
        pdf = PDF_SPECS[pdf_name][0]
        with fitz.open(pdf) as document:
            page_index = find_page(document, normalized_fragment)
            page = document[page_index]
            hits = page.search_for(search_fragment)
            if not hits:
                raise ValueError(f"caption anchor not found for {label}")
            anchor = hits[-1]
            drawings = [
                item["rect"] for item in page.get_drawings()
                if item["rect"].y1 <= anchor.y0 + 2 and item["rect"].y1 >= anchor.y0 - 350
            ]
            if not drawings:
                raise ValueError(f"no vector drawing found for {label}")
            region = fitz.Rect(drawings[0])
            for drawing in drawings[1:]:
                region |= drawing
            sizes = []
            text_region = fitz.Rect(
                region.x0 - 12, region.y0 - 12, region.x1 + 12, region.y1 + 12
            )
            for block in page.get_text("dict").get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = str(span.get("text", ""))
                        if not text.strip():
                            continue
                        bbox = fitz.Rect(span["bbox"])
                        if bbox.intersects(text_region):
                            sizes.append(float(span["size"]))
        ratio = region.width / TEXT_WIDTH_PT
        minimum = min(sizes) if sizes else None
        current_pass = ratio >= 0.6 and minimum is not None and minimum >= 8.5
        passed &= current_pass
        reports[label] = {
            "passed": current_pass,
            "pdf": str(pdf.relative_to(ROOT).as_posix()),
            "page": page_index + 1,
            "vector_region": [round(value, 3) for value in region],
            "width_pt": round(region.width, 3),
            "textwidth_ratio": round(ratio, 3),
            "minimum_region_font_pt": None if minimum is None else round(minimum, 3),
        }
    return {"passed": passed, "figures": reports}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    missing = [str(pdf) for pdf, _ in PDF_SPECS.values() if not pdf.is_file() or not log_path(pdf).is_file()]
    if missing:
        raise FileNotFoundError("missing candidate inputs: " + ", ".join(missing))

    checks = {
        "build_logs": audit_logs(),
        "fonts_embedded": audit_fonts(),
        "layout_and_font_floor": audit_layouts(),
        "links_bookmarks_metadata": audit_links_metadata(),
        "source_inventory": source_inventory(),
        "required_figure_widths": target_figure_widths(),
    }
    passed = all(bool(check["passed"]) for check in checks.values())
    report = {
        "schema_version": 1,
        "gate": "G2",
        "scope": "clean candidate PDF technical gate",
        "executed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "passed": passed,
        "checks": checks,
        "limitations": [
            "G2 does not replace the dual-renderer and scenario sampling required by G3.",
            "H0 remains unavailable while the third authority PDF is missing.",
        ],
    }
    report_path = OUT / "G2_gate_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": "G2", "passed": passed, "report": str(report_path)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
