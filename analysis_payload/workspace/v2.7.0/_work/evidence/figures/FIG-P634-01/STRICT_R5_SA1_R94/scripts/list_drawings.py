import fitz

PDF = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf"
page = fitz.open(PDF)[681]
for i, d in enumerate(page.get_drawings()):
    r = d["rect"]
    if 405 <= r.y0 <= 590 or 405 <= r.y1 <= 590:
        print(i, "type=", d.get("type"), "rect=", tuple(round(v, 3) for v in r), "color=", d.get("color"), "fill=", d.get("fill"), "width=", d.get("width"), "items=", len(d.get("items", [])), "seqno=", d.get("seqno"), "close=", d.get("closePath"))
        for item in d.get("items", [])[:6]:
            print("   ", item)
