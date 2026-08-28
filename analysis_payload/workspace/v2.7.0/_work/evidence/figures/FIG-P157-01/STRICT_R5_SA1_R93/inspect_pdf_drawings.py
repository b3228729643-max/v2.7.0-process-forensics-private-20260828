import fitz

PDF = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf"

doc = fitz.open(PDF)
page = doc[169]
for idx, drawing in enumerate(page.get_drawings()):
    rect = drawing["rect"]
    if rect.y0 < 350 and rect.y1 > 60:
        print(
            idx,
            "rect=",
            tuple(round(v, 3) for v in rect),
            "type=",
            drawing["type"],
            "color=",
            drawing.get("color"),
            "fill=",
            drawing.get("fill"),
            "width=",
            drawing.get("width"),
            "items=",
            len(drawing.get("items", [])),
        )
        if idx in {4, 5, 6, 7, 11, 12, 13, 14, 15}:
            print("  first_items=", drawing.get("items", [])[:5])
