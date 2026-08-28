from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa2_r108_r168_readonly_adjudication_v1")


def save_nearest_8x(name: str) -> None:
    src = Image.open(ROOT / f"{name}_native1x.png")
    out = src.resize((src.width * 8, src.height * 8), Image.Resampling.NEAREST)
    out.save(ROOT / f"{name}_nearest8x.png")


for roi_name in ("roi_formula", "roi_axis_trunc", "roi_caption", "roi_arrow"):
    save_nearest_8x(roi_name)


gray = Image.open(ROOT / "figure_caption_grayscale_300dpi.pgm").convert("L")
gray.save(ROOT / "figure_caption_grayscale_300dpi.png")


standalone = Image.open(ROOT / "standalone_pdf_extract_300dpi.png").convert("RGB")
ink_gray = ImageOps.grayscale(standalone)
# This is a rendered-ink diagnostic mask, not a PDF text-box mask. Pale panel
# fills are excluded so that glyphs, strokes, borders, and markers remain visible.
ink_mask = ink_gray.point(lambda p: 0 if p < 220 else 255, mode="1")
ink_mask.save(ROOT / "rendered_ink_mask_300dpi.png")


base = Image.open(ROOT / "figure_caption_300dpi.png").convert("RGB")
overlay = base.copy()
draw = ImageDraw.Draw(overlay)
try:
    font = ImageFont.truetype("arial.ttf", 22)
except OSError:
    font = ImageFont.load_default()

# Rectangles are view-coordinate object envelopes on the PDF-derived crop.
# They are intentionally outside the semantic ink where possible and are not
# used to infer collisions from invisible PDF text boxes.
objects = [
    ("O01 left title", (340, 10, 800, 80), "#d62728"),
    ("O02 axes/ticks/labels", (20, 115, 800, 680), "#1f77b4"),
    ("O03 included-window fill", (70, 135, 545, 590), "#9467bd"),
    ("O04 stems+markers k=0..6", (20, 120, 535, 605), "#17becf"),
    ("O05 K=6 boundary+label", (385, 125, 555, 585), "#ff7f0e"),
    ("O06 omitted-lag ellipsis", (560, 390, 655, 515), "#8c564b"),
    ("O07 inter-panel arrow", (690, 305, 770, 410), "#2ca02c"),
    ("O08 ESS panel border/title", (760, 70, 1845, 625), "#bcbd22"),
    ("O09 ESS equations", (790, 155, 1565, 415), "#e377c2"),
    ("O10 ESS conditions/readout", (790, 405, 1805, 610), "#7f7f7f"),
    ("O11 caption", (0, 685, 1955, 835), "#d62728"),
]
for label, box, color in objects:
    draw.rectangle(box, outline=color, width=3)
    tx, ty = box[0] + 4, box[1] + 4
    draw.rectangle((tx - 2, ty - 2, tx + draw.textlength(label, font=font) + 4, ty + 26), fill="white")
    draw.text((tx, ty), label, fill=color, font=font)
overlay.save(ROOT / "object_geometry_overlay_300dpi.png")

