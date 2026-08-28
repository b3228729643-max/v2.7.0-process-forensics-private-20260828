import json
from pathlib import Path

import pdfplumber


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf")
OUT = Path(__file__).with_name("02_page_geometry.json")
PHYSICAL_PAGE = 632


def keep(obj, keys):
    result = {}
    for key in keys:
        if key in obj:
            value = obj[key]
            if isinstance(value, tuple):
                value = list(value)
            result[key] = value
    return result


with pdfplumber.open(PDF) as pdf:
    page = pdf.pages[PHYSICAL_PAGE - 1]
    words = page.extract_words(
        x_tolerance=1,
        y_tolerance=1,
        keep_blank_chars=False,
        use_text_flow=False,
        extra_attrs=["fontname", "size", "stroking_color", "non_stroking_color"],
    )
    word_keys = [
        "text", "x0", "top", "x1", "bottom", "fontname", "size",
        "stroking_color", "non_stroking_color",
    ]
    char_keys = [
        "text", "x0", "top", "x1", "bottom", "width", "height", "fontname",
        "size", "stroking_color", "non_stroking_color", "upright", "adv",
    ]
    graphic_keys = [
        "x0", "top", "x1", "bottom", "width", "height", "linewidth",
        "stroke", "fill", "stroking_color", "non_stroking_color", "dash",
        "pts", "path", "evenodd",
    ]
    payload = {
        "physical_page": PHYSICAL_PAGE,
        "page_pt": {"width": page.width, "height": page.height},
        "rotation": page.rotation,
        "words": [keep(w, word_keys) for w in words],
        "chars": [keep(c, char_keys) for c in page.chars],
        "lines": [keep(o, graphic_keys) for o in page.lines],
        "curves": [keep(o, graphic_keys) for o in page.curves],
        "rects": [keep(o, graphic_keys) for o in page.rects],
        "images": [keep(o, graphic_keys) for o in page.images],
    }

OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "physical_page": PHYSICAL_PAGE,
    "page_pt": payload["page_pt"],
    "words": len(payload["words"]),
    "chars": len(payload["chars"]),
    "lines": len(payload["lines"]),
    "curves": len(payload["curves"]),
    "rects": len(payload["rects"]),
    "images": len(payload["images"]),
}, ensure_ascii=False, indent=2))
