from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826")
PDF = ROOT / "build" / "v260_FIG-P582-01_standalone.pdf"
OUT = ROOT / "rois"
OUT.mkdir(exist_ok=True)

doc = fitz.open(PDF)
page = doc[0]
targets = {
    "value_640_and_first_down": [".640", "↓ 下降"],
    "value_380_and_second_down": [".380", "↓ 再下降"],
    "value_325_left": [".325"],
    "truth_and_axis": ["真值 1/3", "样本编号"],
}
for name, needles in targets.items():
    rects = []
    for needle in needles:
        rects.extend(page.search_for(needle))
    if not rects:
        continue
    rect = rects[0]
    for item in rects[1:]:
        rect |= item
    rect = fitz.Rect(rect.x0 - 12, rect.y0 - 12, rect.x1 + 12, rect.y1 + 12) & page.rect
    pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), clip=rect, alpha=False)
    path = OUT / f"{name}_native1x.png"
    pix.save(path)
    image = Image.open(path).convert("RGB")
    image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(OUT / f"{name}_8x_nearest.png")
