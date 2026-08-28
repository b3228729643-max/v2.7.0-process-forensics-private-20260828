import csv
import json
from pathlib import Path

import fitz

PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R2_SA3_FRESH_ISOLATED_R104_R168_20260826")

doc = fitz.open(PDF)
page = doc[649]
raw = page.get_text("rawdict")
spans = []
chars = []
for block_index, block in enumerate(raw.get("blocks", [])):
    if block.get("type") != 0:
        continue
    for line_index, line in enumerate(block.get("lines", [])):
        for span_index, span in enumerate(line.get("spans", [])):
            text = "".join(ch.get("c", "") for ch in span.get("chars", []))
            row = {
                "block": block_index,
                "line": line_index,
                "span": span_index,
                "text": text,
                "font": span.get("font"),
                "size_pt": span.get("size"),
                "color": span.get("color"),
                "bbox_pt": list(span.get("bbox", [])),
            }
            spans.append(row)
            for char_index, ch in enumerate(span.get("chars", [])):
                chars.append({
                    "block": block_index,
                    "line": line_index,
                    "span": span_index,
                    "char_index": char_index,
                    "char": ch.get("c", ""),
                    "origin_pt": list(ch.get("origin", [])),
                    "bbox_pt": list(ch.get("bbox", [])),
                    "font": span.get("font"),
                    "size_pt": span.get("size"),
                    "color": span.get("color"),
                })

drawings = []
for i, d in enumerate(page.get_drawings()):
    drawings.append({
        "drawing_index": i,
        "type": d.get("type"),
        "rect_pt": list(d.get("rect", ())),
        "width_pt": d.get("width"),
        "color": d.get("color"),
        "fill": d.get("fill"),
        "dashes": d.get("dashes"),
        "closePath": d.get("closePath"),
        "layer": d.get("layer"),
        "seqno": d.get("seqno"),
        "item_count": len(d.get("items", [])),
        "items": [repr(item) for item in d.get("items", [])],
    })

(ROOT / "page_raw_inventory.json").write_text(json.dumps({
    "pdf": str(PDF),
    "physical_page": 650,
    "page_index_zero_based": 649,
    "page_rect_pt": list(page.rect),
    "rotation": page.rotation,
    "span_count": len(spans),
    "char_count": len(chars),
    "drawing_count": len(drawings),
    "spans": spans,
    "chars": chars,
    "drawings": drawings,
}, ensure_ascii=False, indent=2), encoding="utf-8")

with (ROOT / "page_text_spans.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(spans[0].keys()))
    w.writeheader()
    w.writerows(spans)

with (ROOT / "page_drawings.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = ["drawing_index", "type", "rect_pt", "width_pt", "color", "fill", "dashes", "closePath", "layer", "seqno", "item_count"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for d in drawings:
        w.writerow({k: d[k] for k in fields})

for s in spans:
    b = s["bbox_pt"]
    if b and b[1] < 260:
        print(f"SPAN {s['block']:03d}/{s['line']:02d}/{s['span']:02d} {s['text']!r} size={s['size_pt']:.3f} font={s['font']} bbox={b}")
print(f"PAGE_RECT={list(page.rect)} SPANS={len(spans)} CHARS={len(chars)} DRAWINGS={len(drawings)}")
