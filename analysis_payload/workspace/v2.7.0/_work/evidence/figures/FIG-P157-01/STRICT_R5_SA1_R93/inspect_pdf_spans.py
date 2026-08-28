import fitz

PDF = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf"

doc = fitz.open(PDF)
page = doc[169]
data = page.get_text("dict")
for block in data["blocks"]:
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            x0, y0, x1, y1 = span["bbox"]
            if y0 < 410 and y1 > 40:
                print(
                    f"bbox={x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f} "
                    f"size={span['size']:.2f} font={span['font']} "
                    f"text={span['text']!r}"
                )
