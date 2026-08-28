from __future__ import annotations

import json
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[5]
PDF = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.pdf"
PHYSICAL_PAGE = 628
DPI = 300
SCALE = DPI / 72.0


def main() -> None:
    renders = ROOT / "renders"
    reports = ROOT / "reports"
    renders.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF)
    page = doc.load_page(PHYSICAL_PAGE - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    pix.save(renders / "full_page_300dpi.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False)
    pix200.save(renders / "full_page_200dpi.png")

    raw = page.get_text("rawdict")
    lines = []
    chars = []
    for b_idx, block in enumerate(raw.get("blocks", [])):
        for l_idx, line in enumerate(block.get("lines", [])):
            span_text = ""
            for s_idx, span in enumerate(line.get("spans", [])):
                span_text += span.get("text", "")
                for c_idx, ch in enumerate(span.get("chars", [])):
                    chars.append({
                        "block": b_idx,
                        "line": l_idx,
                        "span": s_idx,
                        "char": c_idx,
                        "c": ch.get("c", ""),
                        "bbox_pt": [round(v, 4) for v in ch.get("bbox", [])],
                        "origin_pt": [round(v, 4) for v in ch.get("origin", [])],
                        "font": span.get("font", ""),
                        "size_pt": span.get("size", None),
                        "flags": span.get("flags", None),
                        "color": span.get("color", None),
                    })
            lines.append({
                "block": b_idx,
                "line": l_idx,
                "bbox_pt": [round(v, 4) for v in line.get("bbox", [])],
                "text": span_text,
            })
    payload = {
        "pdf": str(PDF),
        "physical_page": PHYSICAL_PAGE,
        "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
        "dpi": DPI,
        "scale_px_per_pdf_pt": SCALE,
        "native_px": [pix.width, pix.height],
        "lines": lines,
        "chars": chars,
    }
    (reports / "page_628_raw_text_geometry.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for row in lines:
        bbox = ",".join(str(v) for v in row["bbox_pt"])
        print(f"{row['block']:03d}:{row['line']:02d} [{bbox}] {row['text']}")


if __name__ == "__main__":
    main()
