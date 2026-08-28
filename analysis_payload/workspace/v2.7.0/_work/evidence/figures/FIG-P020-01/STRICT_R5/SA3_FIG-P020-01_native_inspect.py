#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent SA3 native-PDF inspection helper for FIG-P020-01.

This script only reads the R90 official PDF and the designated figure source.
It emits source/vector/text inventories into this SA3 evidence directory; it
does not read any earlier figure-review evidence or masks.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import fitz  # PyMuPDF


ROOT = Path(__file__).resolve().parents[6]
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r90_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第01册_数学基础与统计学习基本理论" / "V1-C01" / "fig_v1_c01_language_flow.tex"
OUT = Path(__file__).resolve().parent
PAGE_INDEX = 16  # physical page 17, zero indexed in PyMuPDF


def clean_text(text: str) -> str:
    return "".join(text.split())


def main() -> None:
    if not PDF.is_file():
        raise FileNotFoundError(PDF)
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = page.get_text("rawdict")
    text_rows: list[dict[str, object]] = []
    span_id = 0
    for block_no, block in enumerate(raw["blocks"]):
        if block["type"] != 0:
            continue
        for line_no, line in enumerate(block["lines"]):
            for local_no, span in enumerate(line["spans"]):
                chars = span.get("chars", [])
                text = "".join(ch["c"] for ch in chars)
                span_id += 1
                text_rows.append(
                    {
                        "SPAN_ID": f"S{span_id:03d}",
                        "BLOCK": block_no,
                        "LINE": line_no,
                        "LOCAL": local_no,
                        "TEXT": text,
                        "TEXT_COMPACT": clean_text(text),
                        "FONT": span.get("font", ""),
                        "SIZE_PT": span.get("size", ""),
                        "FLAGS": span.get("flags", ""),
                        "X0_PT": span["bbox"][0],
                        "Y0_PT": span["bbox"][1],
                        "X1_PT": span["bbox"][2],
                        "Y1_PT": span["bbox"][3],
                        "CHARS": [
                            {"c": ch["c"], "bbox": ch["bbox"]}
                            for ch in chars
                        ],
                    }
                )

    with (OUT / "SA3_FIG-P020-01_pdf_text_spans.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "SPAN_ID", "BLOCK", "LINE", "LOCAL", "TEXT", "TEXT_COMPACT", "FONT", "SIZE_PT", "FLAGS",
            "X0_PT", "Y0_PT", "X1_PT", "Y1_PT",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: row[key] for key in fields} for row in text_rows])

    drawings = page.get_drawings()
    drawing_rows = []
    for idx, path in enumerate(drawings, start=1):
        rect = path["rect"]
        drawing_rows.append(
            {
                "DRAWING_ID": f"D{idx:03d}",
                "TYPE": path.get("type"),
                "RECT": [rect.x0, rect.y0, rect.x1, rect.y1],
                "WIDTH_PT": path.get("width"),
                "COLOR": path.get("color"),
                "FILL": path.get("fill"),
                "LINE_CAP": path.get("lineCap"),
                "LINE_JOIN": path.get("lineJoin"),
                "DASHES": path.get("dashes"),
                "CLOSE_PATH": path.get("closePath"),
                "EVEN_ODD": path.get("even_odd"),
                "ITEMS": [
                    [item[0], *[
                        ([value.x, value.y] if isinstance(value, fitz.Point) else [value.x0, value.y0, value.x1, value.y1] if isinstance(value, fitz.Rect) else value)
                        for value in item[1:]
                    ]]
                    for item in path.get("items", [])
                ],
            }
        )

    payload = {
        "pdf": str(PDF),
        "source": str(SOURCE),
        "physical_page": PAGE_INDEX + 1,
        "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
        "span_count": len(text_rows),
        "drawing_count": len(drawing_rows),
        "text_rows": text_rows,
        "drawing_rows": drawing_rows,
    }
    (OUT / "SA3_FIG-P020-01_native_pdf_inventory.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    targets = [
        "对象声明", "集合、类型与维数", "关系与映射", "定义域", "值域", "运算与逻辑",
        "复合、量词与约束", "可核验任务", "输入、输出与判据", "逆向核对：任务所用定义逐项返回检查",
        "数学语言从对象声明到任务陈述的依赖关系", "每一条箭头都表示右侧内容使用左侧定义",
    ]
    print(f"PAGE_RECT_PT={page.rect}")
    print(f"TEXT_SPANS={len(text_rows)} DRAWINGS={len(drawing_rows)}")
    for target in targets:
        hits = [row for row in text_rows if target in str(row["TEXT_COMPACT"])]
        print(f"TARGET={target!r} HITS={len(hits)}")
        for hit in hits:
            print(json.dumps({key: hit[key] for key in ["SPAN_ID", "TEXT", "FONT", "SIZE_PT", "X0_PT", "Y0_PT", "X1_PT", "Y1_PT"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
