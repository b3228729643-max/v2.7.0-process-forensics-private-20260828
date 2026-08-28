import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828")
RENDER = ROOT / "render"
MACHINE = ROOT / "machine"
COLOR = Image.open(RENDER / "full_page_300.png").convert("RGB")
GRAY = Image.open(RENDER / "grayscale_300.png").convert("RGB")
SCALE = COLOR.width / 595.276


def pxbox(ptbox, pad=16):
    return (
        max(0, round(ptbox[0] * SCALE) - pad), max(0, round(ptbox[1] * SCALE) - pad),
        min(COLOR.width, round(ptbox[2] * SCALE) + pad), min(COLOR.height, round(ptbox[3] * SCALE) + pad),
    )


def save_pair(name, ptbox, pad=16):
    box = pxbox(ptbox, pad)
    for prefix, image in (("color", COLOR), ("gray", GRAY)):
        crop = image.crop(box)
        crop.save(RENDER / f"{name}_{prefix}_native1x.png")
        crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(RENDER / f"{name}_{prefix}_nearest8x.png")
    return box


relation_boxes = {
    "R01_legend_x1": (245.5, 227.0, 266.8, 237.0),
    "R02_legend_x2": (299.8, 227.0, 321.2, 237.0),
    "R03_q0_x0": (215.0, 65.0, 244.0, 101.0),
    "R04_labels_1_2": (205.0, 82.0, 269.0, 108.0),
    "R05_labels_3_4": (244.0, 95.0, 289.0, 126.0),
    "R06_labels_5_6_7": (267.0, 104.0, 308.0, 138.0),
    "R07_star_xstar_axes": (292.0, 124.0, 326.0, 160.0),
    "R08_axis_labels": (300.0, 65.0, 402.0, 143.0),
}
resolved_boxes = {name: save_pair(name, box) for name, box in relation_boxes.items()}

with (MACHINE / "MACHINE_OBJECTS.csv").open("r", encoding="utf-8-sig", newline="") as handle:
    glyphs = [row for row in csv.DictReader(handle) if row["object_type"] == "glyph"]
try:
    label_font = ImageFont.truetype("arial.ttf", 18)
except OSError:
    label_font = ImageFont.load_default()
cell_w, cell_h = 260, 220
sheet = Image.new("RGB", (cell_w * 5, cell_h * 5), "white")
draw = ImageDraw.Draw(sheet)
for index, row in enumerate(glyphs):
    x0 = max(0, round(float(row["x0"]) * SCALE) - 14)
    y0 = max(0, round(float(row["top"]) * SCALE) - 14)
    x1 = min(COLOR.width, round(float(row["x1"]) * SCALE) + 14)
    y1 = min(COLOR.height, round(float(row["bottom"]) * SCALE) + 14)
    crop = COLOR.crop((x0, y0, x1, y1))
    factor = min(6.0, (cell_w - 12) / max(1, crop.width), (cell_h - 34) / max(1, crop.height))
    resized = crop.resize((max(1, round(crop.width * factor)), max(1, round(crop.height * factor))), Image.Resampling.NEAREST)
    col, row_index = index % 5, index // 5
    cx, cy = col * cell_w, row_index * cell_h
    sheet.paste(resized, (cx + (cell_w - resized.width) // 2, cy + 26 + (cell_h - 30 - resized.height) // 2))
    draw.text((cx + 5, cy + 4), f"{row['object_id']} {row['text']}", fill=(0, 0, 0), font=label_font)
    draw.rectangle((cx, cy, cx + cell_w - 1, cy + cell_h - 1), outline=(180, 180, 180))
sheet.save(RENDER / "glyph_contact_sheet_nearest.png")


def horizontal_runs(path):
    image = Image.open(path).convert("L")
    center = image.height // 2
    active = []
    for x in range(image.width):
        active.append(any(image.getpixel((x, y)) < 210 for y in range(max(0, center - 5), min(image.height, center + 6))))
    runs, start = [], None
    for i, value in enumerate(active + [False]):
        if value and start is None:
            start = i
        elif not value and start is not None:
            runs.append({"x0": start, "x1": i - 1, "length_px": i - start})
            start = None
    gaps = []
    for a, b in zip(runs, runs[1:]):
        gaps.append({"x0": a["x1"] + 1, "x1": b["x0"] - 1, "length_px": b["x0"] - a["x1"] - 1})
    return {"width": image.width, "height": image.height, "center_y": center, "runs": runs, "gaps": gaps}


measure = {
    "scale_px_per_pt": SCALE,
    "resolved_relation_boxes_px": resolved_boxes,
    "x1_color": horizontal_runs(RENDER / "R01_legend_x1_color_native1x.png"),
    "x1_gray": horizontal_runs(RENDER / "R01_legend_x1_gray_native1x.png"),
    "x2_color": horizontal_runs(RENDER / "R02_legend_x2_color_native1x.png"),
    "x2_gray": horizontal_runs(RENDER / "R02_legend_x2_gray_native1x.png"),
}
with (MACHINE / "LEGEND_COLOR_GRAY_RUNS.json").open("w", encoding="utf-8") as handle:
    json.dump(measure, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps(measure, ensure_ascii=False, indent=2))
