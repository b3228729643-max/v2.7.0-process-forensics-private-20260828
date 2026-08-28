import json
from pathlib import Path

import fitz

PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R13_SA1_FRESH_ISOLATED_R105_20260826\analysis")

doc = fitz.open(PDF)
page = doc[660]
raw = page.get_text("rawdict")
spans = []
for block in raw.get("blocks", []):
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            bbox = span.get("bbox")
            if bbox and bbox[1] < 450 and bbox[3] > 200:
                text = "".join(ch.get("c", "") for ch in span.get("chars", []))
                spans.append({
                    "text": text,
                    "bbox": bbox,
                    "font": span.get("font"),
                    "size": span.get("size"),
                    "color": span.get("color"),
                    "chars": span.get("chars", []),
                })

drawings = []
for i, d in enumerate(page.get_drawings()):
    r = d.get("rect")
    if r and r.y0 < 450 and r.y1 > 200:
        drawings.append({
            "index": i,
            "rect": [r.x0, r.y0, r.x1, r.y1],
            "type": d.get("type"),
            "color": d.get("color"),
            "fill": d.get("fill"),
            "width": d.get("width"),
            "items": [[str(v) for v in item] for item in d.get("items", [])],
        })

(OUT / "probe_spans.json").write_text(json.dumps(spans, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "probe_drawings.json").write_text(json.dumps(drawings, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"page_rect": list(page.rect), "span_count": len(spans), "drawing_count": len(drawings)}, ensure_ascii=False))
for s in spans:
    print(f"TEXT {s['bbox']} size={s['size']:.3f} font={s['font']} color={s['color']} :: {s['text']}")
for d in drawings:
    print(f"DRAW {d['index']} {d['rect']} type={d['type']} width={d['width']} color={d['color']} fill={d['fill']} items={len(d['items'])}")
