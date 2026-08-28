from __future__ import annotations

import json
from pathlib import Path

import fitz


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
OUT = Path(__file__).with_name("page633_structure.json")

doc = fitz.open(PDF)
page = doc[632]
raw = page.get_text("rawdict")
chars = []
spans = []
for block_index, block in enumerate(raw["blocks"]):
    if block.get("type") != 0:
        continue
    for line_index, line in enumerate(block.get("lines", [])):
        for span_index, span in enumerate(line.get("spans", [])):
            span_chars = span.get("chars", [])
            spans.append({
                "block": block_index,
                "line": line_index,
                "span": span_index,
                "text": "".join(ch.get("c", "") for ch in span_chars),
                "bbox": [round(v, 4) for v in span.get("bbox", [])],
                "font": span.get("font"),
                "size": span.get("size"),
                "color": span.get("color"),
            })
            for char_index, ch in enumerate(span_chars):
                chars.append({
                    "block": block_index,
                    "line": line_index,
                    "span": span_index,
                    "char": char_index,
                    "c": ch.get("c"),
                    "bbox": [round(v, 4) for v in ch.get("bbox", [])],
                    "origin": [round(v, 4) for v in ch.get("origin", [])],
                    "font": span.get("font"),
                    "size": span.get("size"),
                    "color": span.get("color"),
                })

drawings = []
for index, d in enumerate(page.get_drawings()):
    drawings.append({
        "index": index,
        "type": d.get("type"),
        "rect": [round(v, 4) for v in d["rect"]],
        "color": d.get("color"),
        "fill": d.get("fill"),
        "width": d.get("width"),
        "closePath": d.get("closePath"),
        "items": [str(item) for item in d.get("items", [])],
    })

OUT.write_text(json.dumps({
    "page_rect": [float(v) for v in page.rect],
    "spans": spans,
    "chars": chars,
    "drawings": drawings,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"chars={len(chars)} drawings={len(drawings)} out={OUT}")
