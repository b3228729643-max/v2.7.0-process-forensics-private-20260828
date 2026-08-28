from pathlib import Path

import fitz


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R1_SA1_REQUAL_R98_20260824\renders")
PHYSICAL_PAGES = (742, 743, 765, 787, 789)

doc = fitz.open(PDF)
for physical in PHYSICAL_PAGES:
    page = doc[physical - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), colorspace=fitz.csRGB, alpha=False)
    pix.save(OUT / f"reference_candidate_fullpage_physical_{physical:03d}_300dpi.png")
    print(physical, page.get_label(), pix.width, pix.height)
