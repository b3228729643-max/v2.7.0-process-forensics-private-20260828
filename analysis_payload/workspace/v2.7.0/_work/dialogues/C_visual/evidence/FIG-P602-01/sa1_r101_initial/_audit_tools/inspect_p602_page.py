from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF = ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf"
EV = ROOT / r"v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa1_r101_initial"
PAGE_INDEX = 650


def serializable(value):
    if isinstance(value, fitz.Rect):
        return [value.x0, value.y0, value.x1, value.y1]
    if isinstance(value, fitz.Point):
        return [value.x, value.y]
    if isinstance(value, tuple):
        return [serializable(v) for v in value]
    if isinstance(value, list):
        return [serializable(v) for v in value]
    if isinstance(value, dict):
        return {k: serializable(v) for k, v in value.items()}
    return value


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
raw = page.get_text("rawdict")
drawings = page.get_drawings(extended=True)
out = EV / "03_objects" / "page651_rawdict_drawings.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(
    json.dumps({"page_rect": list(page.rect), "rawdict": raw, "drawings": serializable(drawings)}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"PAGE_RECT={page.rect}")
print(f"RAW_JSON={out}")
print("TEXT_SPANS_Y250_PLUS")
for block_no, block in enumerate(raw.get("blocks", [])):
    if block.get("type") != 0:
        continue
    for line_no, line in enumerate(block.get("lines", [])):
        for span_no, span in enumerate(line.get("spans", [])):
            bbox = span.get("bbox", [0, 0, 0, 0])
            if bbox[3] < 250:
                continue
            text = "".join(ch.get("c", "") for ch in span.get("chars", []))
            print(
                f"B{block_no:02d} L{line_no:02d} S{span_no:02d} "
                f"bbox={tuple(round(float(v), 3) for v in bbox)} size={span.get('size')} "
                f"font={span.get('font')} color={span.get('color')} text={text!r}"
            )

print("DRAWINGS_INTERSECT_Y250_PLUS")
for idx, drawing in enumerate(drawings):
    rect = drawing.get("rect")
    if rect is None or rect.y1 < 250:
        continue
    print(
        f"D{idx:03d} type={drawing.get('type')} rect={tuple(round(float(v), 3) for v in rect)} "
        f"width={drawing.get('width')} color={drawing.get('color')} fill={drawing.get('fill')} "
        f"dashes={drawing.get('dashes')!r} items={len(drawing.get('items', []))}"
    )
