import pdfplumber

pdf_path = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828\build\v260_FIG-P126-01_standalone.pdf"

with pdfplumber.open(pdf_path) as document:
    page = document.pages[0]
    print(f"PAGE {page.width} {page.height} CHARS {len(page.chars)}")
    for index, char in enumerate(page.chars, 1):
        text = char.get("text", "")
        codepoints = "+".join(f"U+{ord(value):04X}" for value in text)
        print(
            f"{index:03d} {codepoints} "
            f"x0={char['x0']:.3f} x1={char['x1']:.3f} "
            f"top={char['top']:.3f} bottom={char['bottom']:.3f}"
        )
    print(f"LINES {len(page.lines)}")
    for index, line in enumerate(page.lines, 1):
        print(
            f"L{index:03d} x0={line['x0']:.3f} x1={line['x1']:.3f} "
            f"top={line['top']:.3f} bottom={line['bottom']:.3f} "
            f"color={line.get('stroking_color')!r}"
        )
    print(f"CURVES {len(page.curves)}")
    for index, curve in enumerate(page.curves, 1):
        print(
            f"V{index:03d} x0={curve['x0']:.3f} x1={curve['x1']:.3f} "
            f"top={curve['top']:.3f} bottom={curve['bottom']:.3f} "
            f"color={curve.get('stroking_color')!r}"
        )
