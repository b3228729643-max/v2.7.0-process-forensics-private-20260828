"""Read-only discovery of FIG-P634-01 in the frozen final PDF.

This helper writes only the dedicated evidence directory.  It neither mutates
the source tree nor consults prior audit material.
"""
from __future__ import annotations

import json
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[6]
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r93_fullbook" / "main_full.pdf"
OUT = Path(__file__).resolve().parent


def clean(value: object) -> object:
    if isinstance(value, fitz.Rect):
        return [round(value.x0, 4), round(value.y0, 4), round(value.x1, 4), round(value.y1, 4)]
    if isinstance(value, fitz.Point):
        return [round(value.x, 4), round(value.y, 4)]
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


def main() -> None:
    document = fitz.open(PDF)
    needles = ["图33.3", "系统扫描按固定次序立即写回", "轮内状态", "轮末样本"]
    candidates = []
    for index, page in enumerate(document):
        page_text = page.get_text("text")
        hits = [needle for needle in needles if needle in page_text]
        if hits:
            candidates.append(
                {
                    "pdf_physical_page": index + 1,
                    "zero_based_index": index,
                    "hits": hits,
                    "page_text": page_text,
                    "page_rect_pt": clean(page.rect),
                }
            )

    exact_candidates = [
        row
        for row in candidates
        if "图33.3" in row["hits"] and "系统扫描按固定次序立即写回" in row["hits"]
    ]
    payload = {
        "frozen_pdf": str(PDF),
        "pdf_page_count": document.page_count,
        "needles": needles,
        "search_hits": candidates,
        "exact_figure_candidates": exact_candidates,
    }
    (OUT / "page_discovery.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if len(exact_candidates) != 1:
        raise SystemExit(f"Expected exactly one FIG-P634-01 candidate; got {len(exact_candidates)}")

    page = document[exact_candidates[0]["zero_based_index"]]
    blocks = page.get_text("dict", sort=True)["blocks"]
    drawings = page.get_drawings()
    (OUT / "page_text_blocks.json").write_text(
        json.dumps(clean(blocks), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "page_drawings.json").write_text(
        json.dumps(clean(drawings), ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
