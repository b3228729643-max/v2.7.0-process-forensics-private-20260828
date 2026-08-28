#!/usr/bin/env python3
"""Extract final Gate C page metrics used by the visual-audit workbook."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import fitz


def weighted_median(values: list[tuple[float, int]]) -> float:
    if not values:
        return 0.0
    expanded_weight = sum(weight for _, weight in values)
    midpoint = expanded_weight / 2
    cumulative = 0
    for value, weight in sorted(values):
        cumulative += weight
        if cumulative >= midpoint:
            return value
    return values[-1][0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    output_path = Path(args.output).resolve()
    doc = fitz.open(pdf_path)
    pages = []
    for page_number, page in enumerate(doc, start=1):
        font_weights: list[tuple[float, int]] = []
        raw = page.get_text("dict")
        for block in raw.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = str(span.get("text", "")).strip()
                    if not text:
                        continue
                    font_weights.append((round(float(span.get("size", 0.0)), 3), max(1, len(text))))
        sizes = [value for value, _ in font_weights]
        pages.append(
            {
                "page": page_number,
                "median_font_pt": round(weighted_median(font_weights), 3),
                "minimum_font_pt": round(min(sizes), 3) if sizes else 0.0,
                "mean_font_pt": round(statistics.fmean(sizes), 3) if sizes else 0.0,
                "link_count": len(page.get_links()),
            }
        )
    payload = {"schema_version": 1, "pdf": str(pdf_path), "page_count": len(doc), "pages": pages}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output_path), "page_count": len(doc)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
