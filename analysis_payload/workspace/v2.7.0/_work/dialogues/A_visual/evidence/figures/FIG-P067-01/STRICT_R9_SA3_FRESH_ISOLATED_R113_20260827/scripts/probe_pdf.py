import json
from pathlib import Path

import fitz


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf")


doc = fitz.open(PDF)
page = doc[68]
raw = page.get_text("rawdict")
text_rows = []
for block in raw["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            chars = span.get("chars", [])
            text_rows.append(
                {
                    "text": "".join(char.get("c", "") for char in chars),
                    "bbox": [round(value, 3) for value in span["bbox"]],
                    "size": round(span["size"], 3),
                    "font": span["font"],
                    "color": span["color"],
                    "char_count": len(chars),
                }
            )

draw_rows = []
for index, drawing in enumerate(page.get_drawings(extended=True), start=1):
    rect = drawing["rect"]
    draw_rows.append(
        {
            "index": index,
            "rect": [round(rect.x0, 3), round(rect.y0, 3), round(rect.x1, 3), round(rect.y1, 3)],
            "type": drawing.get("type"),
            "fill": drawing.get("fill"),
            "color": drawing.get("color"),
            "width": drawing.get("width"),
            "dashes": drawing.get("dashes"),
            "items": [str(item) for item in drawing.get("items", [])],
        }
    )

payload = {
    "page_rect": list(page.rect),
    "text_rows_y_lt_260": [row for row in text_rows if row["bbox"][1] < 260],
    "draw_rows_y_lt_260": [row for row in draw_rows if row["rect"][1] < 260],
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
