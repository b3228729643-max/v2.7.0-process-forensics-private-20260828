from __future__ import annotations

import json
from pathlib import Path

import pdfplumber


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
PHYSICAL_PAGE = 691


with pdfplumber.open(PDF) as pdf:
    page = pdf.pages[PHYSICAL_PAGE - 1]
    print(
        json.dumps(
            {
                "physical_page": PHYSICAL_PAGE,
                "width_pt": page.width,
                "height_pt": page.height,
                "char_count": len(page.chars),
                "line_count": len(page.lines),
                "rect_count": len(page.rects),
                "curve_count": len(page.curves),
            },
            ensure_ascii=False,
        )
    )
    words = page.extract_words(
        x_tolerance=1,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    figure_chars = [
        char
        for char in page.chars
        if 550 <= float(char["top"])
        and float(char["bottom"]) <= 730
        and str(char.get("text", "")).strip()
    ]
    print("figure_nonspace_char_count", len(figure_chars))
    for word in words:
        if 525 <= word["top"] <= 790:
            print(
                f'{word["top"]:8.2f} {word["bottom"]:8.2f} '
                f'{word["x0"]:8.2f} {word["x1"]:8.2f} {word["text"]}'
            )
    for kind in ("lines", "rects", "curves"):
        print(f"--- {kind} ---")
        for idx, obj in enumerate(getattr(page, kind)):
            top = float(obj.get("top", 0.0))
            bottom = float(obj.get("bottom", 0.0))
            if 545 <= top <= 705 or 545 <= bottom <= 705:
                keep = {
                    key: obj.get(key)
                    for key in (
                        "x0",
                        "x1",
                        "top",
                        "bottom",
                        "width",
                        "height",
                        "linewidth",
                        "stroking_color",
                        "non_stroking_color",
                        "dash",
                        "fill",
                        "evenodd",
                    )
                    if key in obj
                }
                print(idx, json.dumps(keep, ensure_ascii=False, default=str))
