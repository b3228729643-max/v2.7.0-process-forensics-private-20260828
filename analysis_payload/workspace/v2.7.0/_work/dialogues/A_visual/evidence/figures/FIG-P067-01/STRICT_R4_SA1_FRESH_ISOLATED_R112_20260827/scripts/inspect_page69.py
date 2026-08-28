from __future__ import annotations

import json
from pathlib import Path

import pdfplumber


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R4_SA1_FRESH_ISOLATED_R112_20260827")
PAGE_INDEX = 68


def rounded_bbox(obj: dict[str, object]) -> list[float]:
    return [round(float(obj[k]), 3) for k in ("x0", "top", "x1", "bottom")]


def main() -> None:
    with pdfplumber.open(PDF) as doc:
        page = doc.pages[PAGE_INDEX]
        words = [
            {"text": w["text"], "bbox_pt": rounded_bbox(w)}
            for w in page.extract_words(x_tolerance=1, y_tolerance=1)
            if 45 <= float(w["top"]) <= 255
        ]
        chars = [
            {
                "text": c["text"],
                "bbox_pt": rounded_bbox(c),
                "fontname": c.get("fontname"),
                "size_pt": round(float(c.get("size", 0)), 4),
                "stroking_color": c.get("stroking_color"),
                "non_stroking_color": c.get("non_stroking_color"),
            }
            for c in page.chars
            if 45 <= float(c["top"]) <= 255
        ]

        def filtered(items: list[dict[str, object]]) -> list[dict[str, object]]:
            answer = []
            for index, item in enumerate(items):
                top = float(item.get("top", 0))
                bottom = float(item.get("bottom", 0))
                if bottom < 45 or top > 255:
                    continue
                bbox = rounded_bbox(item)
                answer.append(
                    {
                        "source_index": index,
                        "bbox_pt": bbox,
                        "linewidth_pt": item.get("linewidth"),
                        "stroke": item.get("stroke"),
                        "fill": item.get("fill"),
                        "stroking_color": item.get("stroking_color"),
                        "non_stroking_color": item.get("non_stroking_color"),
                        "pts": item.get("pts"),
                    }
                )
            return answer

        record = {
            "physical_page_1based": PAGE_INDEX + 1,
            "page_width_pt": page.width,
            "page_height_pt": page.height,
            "words_top_45_255pt": words,
            "chars_top_45_255pt": chars,
            "lines_top_45_255pt": filtered(page.lines),
            "curves_top_45_255pt": filtered(page.curves),
            "rects_top_45_255pt": filtered(page.rects),
        }
    out = ROOT / "page69_inspection.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "page": PAGE_INDEX + 1,
        "page_pt": [record["page_width_pt"], record["page_height_pt"]],
        "word_count": len(words),
        "char_count": len(chars),
        "line_count": len(record["lines_top_45_255pt"]),
        "curve_count": len(record["curves_top_45_255pt"]),
        "rect_count": len(record["rects_top_45_255pt"]),
        "words": words,
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
