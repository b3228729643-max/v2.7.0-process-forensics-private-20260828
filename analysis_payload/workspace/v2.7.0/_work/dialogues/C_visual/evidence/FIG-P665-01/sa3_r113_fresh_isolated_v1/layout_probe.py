import sys

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

PDF = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf"

with pdfplumber.open(PDF) as doc:
    page = doc.pages[712]
    print(f"page={page.page_number} width_pt={page.width:.6f} height_pt={page.height:.6f}")
    print(f"chars={len(page.chars)} lines={len(page.lines)} rects={len(page.rects)} curves={len(page.curves)}")
    for word in page.extract_words(
        x_tolerance=1,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=False,
        extra_attrs=["fontname", "size"],
    ):
        if word["top"] <= 285:
            print(
                "WORD\t"
                f"{word['text']}\t"
                f"x0={word['x0']:.3f}\ttop={word['top']:.3f}\t"
                f"x1={word['x1']:.3f}\tbottom={word['bottom']:.3f}\t"
                f"font={word['fontname']}\tsize={word['size']}"
            )
    for i, line in enumerate(page.lines, 1):
        if min(line["top"], line["bottom"]) <= 285:
            print(
                f"LINE\t{i}\tx0={line['x0']:.3f}\ttop={line['top']:.3f}\t"
                f"x1={line['x1']:.3f}\tbottom={line['bottom']:.3f}\t"
                f"linewidth={line.get('linewidth')}\tstroking_color={line.get('stroking_color')}"
            )
    for i, rect in enumerate(page.rects, 1):
        if rect["top"] <= 285:
            print(
                f"RECT\t{i}\tx0={rect['x0']:.3f}\ttop={rect['top']:.3f}\t"
                f"x1={rect['x1']:.3f}\tbottom={rect['bottom']:.3f}\t"
                f"linewidth={rect.get('linewidth')}\tstroke={rect.get('stroking_color')}\t"
                f"fill={rect.get('non_stroking_color')}"
            )
    for i, curve in enumerate(page.curves, 1):
        if curve["top"] <= 285:
            print(
                f"CURVE\t{i}\tx0={curve['x0']:.3f}\ttop={curve['top']:.3f}\t"
                f"x1={curve['x1']:.3f}\tbottom={curve['bottom']:.3f}\t"
                f"linewidth={curve.get('linewidth')}\tstroke={curve.get('stroking_color')}\t"
                f"fill={curve.get('non_stroking_color')}"
            )
