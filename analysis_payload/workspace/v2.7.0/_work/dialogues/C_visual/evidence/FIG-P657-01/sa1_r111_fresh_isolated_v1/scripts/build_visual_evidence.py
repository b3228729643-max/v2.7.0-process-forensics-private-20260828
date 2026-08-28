from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa1_r111_fresh_isolated_v1")
PAGE = ROOT / "raw" / "page706_native300dpi.png"

img = Image.open(PAGE).convert("RGB")

# Coordinates are native pixels in the direct 300 dpi Poppler render.
STANDALONE_BOX = (400, 1120, 2160, 1785)

boxes = {
    "figure_with_caption_native300dpi": (330, 1100, 2210, 1925),
    "standalone_figure_native300dpi": STANDALONE_BOX,
    "roi_top_relations_native1x": (650, 1110, 1740, 1445),
    "roi_bottom_relations_native1x": (650, 1410, 1740, 1785),
    "roi_legend_native1x": (1750, 1250, 2140, 1500),
    "roi_caption_native1x": (380, 1780, 2160, 1920),
    "roi_glyph_dirichlet_beta_native1x": (700, 1130, 1710, 1305),
    "roi_glyph_categorical_bernoulli_native1x": (700, 1570, 1720, 1775),
}

for name, box in boxes.items():
    crop = img.crop(box)
    out_dir = ROOT / ("raw" if name.startswith(("figure_", "standalone_")) else "rois")
    crop.save(out_dir / f"{name}.png")
    if name.startswith("roi_"):
        crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(
            ROOT / "rois" / f"{name.replace('_native1x', '_nearest8x')}.png"
        )

standalone = Image.open(ROOT / "raw" / "standalone_figure_native300dpi.png").convert("RGB")
ImageOps.grayscale(standalone).save(ROOT / "raw" / "standalone_figure_grayscale300dpi.png")

# Coordinate reference overlay for the frozen visible-object denominator.
overlay = standalone.copy()
draw = ImageDraw.Draw(overlay)
sx, sy = img.width / 595.276, img.height / 841.89
ox, oy = STANDALONE_BOX[0], STANDALONE_BOX[1]

def ptbox_to_crop(box):
    x0, top, x1, bottom = box
    return (round(x0 * sx - ox), round(top * sy - oy), round(x1 * sx - ox), round(bottom * sy - oy))

object_boxes_pdf = {
    "O01_ROLE_PRIOR": (115.0, 282.0, 149.0, 297.0),
    "O02_DIRICHLET": (172.5, 272.5, 258.5, 303.2),
    "O03_BETA_K2": (318.5, 272.5, 404.5, 303.2),
    "O04_ROLE_LIKELIHOOD": (115.0, 343.0, 149.0, 358.0),
    "O05_MULTINOMIAL": (172.5, 333.4, 258.5, 364.2),
    "O06_BINOMIAL_K2": (318.5, 333.4, 404.5, 364.2),
    "O07_ROLE_SINGLE": (110.0, 404.0, 153.5, 419.0),
    "O08_CATEGORICAL_N1": (172.5, 394.3, 258.5, 425.1),
    "O09_BERNOULLI_K2N1": (318.5, 394.3, 404.5, 425.1),
    "O10_REL_DIR_BETA": (258.0, 273.5, 318.2, 290.0),
    "O11_REL_MULTI_BINOM": (258.0, 334.5, 318.2, 351.0),
    "O12_REL_MULTI_CAT": (213.5, 363.5, 247.0, 394.0),
    "O13_REL_BINOM_BERN": (359.5, 363.5, 393.0, 394.0),
    "O14_REL_CAT_BERN": (258.0, 396.8, 318.2, 412.0),
    "O15_REL_DIR_MULTI": (213.5, 302.3, 217.5, 333.0),
    "O16_REL_BETA_BINOM": (359.5, 302.3, 363.5, 333.0),
    "O17_LEGEND_CONJ": (420.5, 312.0, 481.0, 323.0),
    "O18_LEGEND_SPECIAL": (420.5, 336.0, 498.5, 347.5),
}
object_boxes = {name: ptbox_to_crop(box) for name, box in object_boxes_pdf.items()}
colors = [(214, 39, 40), (31, 119, 180), (44, 160, 44), (148, 103, 189)]
for i, (name, box) in enumerate(object_boxes.items()):
    color = colors[i % len(colors)]
    draw.rectangle(box, outline=color, width=3)
    draw.text((box[0] + 3, box[1] + 3), name, fill=color)
overlay.save(ROOT / "review" / "visible_object_denominator_overlay.png")
