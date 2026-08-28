import json
import fitz

PDF = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf"
PAGE_INDEX = 703
BODY = fitz.Rect(65, 55, 530, 220)

doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
raw = page.get_text("rawdict")
chars = []
for block in raw.get("blocks", []):
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            for char in span.get("chars", []):
                rect = fitz.Rect(char["bbox"])
                if rect.intersects(BODY):
                    chars.append({
                        "c": char.get("c"),
                        "bbox": [round(v, 3) for v in rect],
                        "font": span.get("font"),
                        "size": span.get("size"),
                        "color": span.get("color"),
                        "origin": [round(v, 3) for v in char.get("origin", (0, 0))],
                    })
drawings = []
for idx, drawing in enumerate(page.get_drawings()):
    rect = fitz.Rect(drawing["rect"])
    probe = fitz.Rect(rect.x0 - 1, rect.y0 - 1, rect.x1 + 1, rect.y1 + 1)
    if probe.intersects(BODY):
        drawings.append({
            "index": idx,
            "rect": [round(v, 3) for v in rect],
            "type": drawing.get("type"),
            "fill": drawing.get("fill"),
            "color": drawing.get("color"),
            "width": drawing.get("width"),
            "closePath": drawing.get("closePath"),
            "items": [str(x) for x in drawing.get("items", [])],
        })
compact_drawings = [{k: d[k] for k in ("index", "rect", "type", "fill", "color", "width")} | {"item_count": len(d["items"])} for d in drawings]
print(json.dumps({
    "page_rect": list(page.rect),
    "char_count_including_spaces": len(chars),
    "visible_char_count": sum(c["c"] != " " for c in chars),
    "unique_fonts": sorted({c["font"] for c in chars}),
    "font_sizes": sorted({round(c["size"], 4) for c in chars}),
    "drawing_count": len(drawings),
    "drawings": compact_drawings,
}, ensure_ascii=False, indent=2))
