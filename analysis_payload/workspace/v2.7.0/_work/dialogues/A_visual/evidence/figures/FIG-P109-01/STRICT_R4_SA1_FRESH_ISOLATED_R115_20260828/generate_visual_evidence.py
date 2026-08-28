from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FULL_300 = ROOT / "r115_p116_full_300dpi.png"
FULL_200 = ROOT / "r115_p116_full_200dpi.png"

# Coordinates are frozen in final 300 dpi page pixels, derived from the
# official R115 page geometry (595.276 x 841.89 pt -> 2481 x 3508 px).
FIGURE_BOX = (630, 1430, 1890, 2390)

OBJECT_BOXES = {
    "O01": (650, 1520, 1870, 2205),  # convex region (fill + boundary)
    "O02": (880, 1735, 1665, 2045),  # chord x--y
    "O03": (875, 1990, 900, 2020),   # endpoint marker x
    "O04": (1635, 1720, 1665, 1750), # endpoint marker y
    "O05": (1065, 1930, 1095, 1960), # interior marker lambda=.25
    "O06": (1255, 1850, 1285, 1880), # interior marker lambda=.50
    "O07": (1450, 1770, 1480, 1800), # interior marker lambda=.75
    "O08": (820, 2020, 865, 2095),   # x label
    "O09": (1670, 1640, 1745, 1720), # y label
    "O10": (930, 1765, 1285, 1855),  # z formula compound label
    "O11": (1550, 1580, 1785, 1695), # convex feasible-region compound label
    "O12": (845, 2190, 1695, 2310),  # rounded note border
    "O13": (870, 2210, 1660, 2290),  # implication formula text
    "O14": (825, 2285, 955, 2380),   # caption number
    "O15": (960, 2290, 1720, 2380),  # caption text
}

OBJECTS = {
    "O01": ("GEOMETRY", "CONVEX_REGION", "convex feasible region C: fill plus boundary"),
    "O02": ("GEOMETRY", "CHORD", "complete line segment from x to y"),
    "O03": ("MARKER", "ENDPOINT_X", "dark endpoint marker at x"),
    "O04": ("MARKER", "ENDPOINT_Y", "dark endpoint marker at y"),
    "O05": ("MARKER", "INTERIOR_025", "teal convex-combination marker lambda=0.25"),
    "O06": ("MARKER", "INTERIOR_050", "teal convex-combination marker lambda=0.50"),
    "O07": ("MARKER", "INTERIOR_075", "teal convex-combination marker lambda=0.75"),
    "O08": ("TEXT", "ENDPOINT_LABEL", "math label x"),
    "O09": ("TEXT", "ENDPOINT_LABEL", "math label y"),
    "O10": ("FORMULA", "CONVEX_COMBINATION_LABEL", "z=lambda*x+(1-lambda)*y, including white backing"),
    "O11": ("TEXT_FORMULA", "REGION_LABEL", "convex feasible region C, including white backing"),
    "O12": ("NODE_BORDER", "CONCLUSION_BORDER", "rounded border enclosing the defining implication"),
    "O13": ("FORMULA", "CONCLUSION_TEXT", "x,y in C and lambda in [0,1] implies convex combination in C"),
    "O14": ("TEXT", "CAPTION_NUMBER", "Figure 7.1 caption number"),
    "O15": ("TEXT", "CAPTION_TEXT", "convex-set caption conclusion"),
}

TEXT_BOXES_PT = {
    "O08": (197.900, 488.157468, 203.469116, 498.120108),
    "O09": (405.804, 398.737468, 410.884946, 408.700108),
    "O10": (228.579, 430.867790, 303.013081, 440.033420),
    "O11": (378.261, 388.352496, 423.951222, 398.168886),
    "O13": (213.102, 535.713790, 393.133304, 544.879420),
    "O14": (201.195, 551.752338, 226.091777, 566.178240),
    "O15": (236.054, 555.338888, 405.418880, 566.008875),
}

ROIS = {
    "roi_01_x_marker_label": (790, 1940, 975, 2115),
    "roi_02_y_marker_region_label": (1510, 1540, 1825, 1790),
    "roi_03_z_formula_over_chord": (885, 1695, 1340, 1895),
    "roi_04_note_formula_border": (805, 2140, 1740, 2335),
    "roi_05_caption_clearance": (790, 2260, 1760, 2410),
    "roi_06_region_chord_geometry": (610, 1460, 1920, 2235),
}


def to_px(box_pt):
    scale = 300.0 / 72.0
    return tuple(round(v * scale) for v in box_pt)


def label(draw, xy, text, color):
    x, y = xy
    draw.rectangle((x, y, x + 47, y + 20), fill="white", outline=color, width=2)
    draw.text((x + 3, y + 2), text, fill=color, font=ImageFont.load_default())


page300 = Image.open(FULL_300).convert("RGB")
page200 = Image.open(FULL_200).convert("RGB")

native = page300.crop(FIGURE_BOX)
native.save(ROOT / "figure_current_native1x_300dpi.png")
native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(
    ROOT / "figure_current_nearest8x.png"
)
native.convert("L").save(ROOT / "figure_current_grayscale_300dpi.png")

integration = page200.copy()
d = ImageDraw.Draw(integration)
ratio = 200.0 / 300.0
box200 = tuple(round(v * ratio) for v in FIGURE_BOX)
d.rectangle(box200, outline=(200, 0, 0), width=5)
label(d, (box200[0], max(0, box200[1] - 24)), "FIG-P109-01", (200, 0, 0))
integration.save(ROOT / "page_integration_p116_200dpi.png")

overlay = native.copy()
d = ImageDraw.Draw(overlay)
for oid, box in OBJECT_BOXES.items():
    rel = (box[0] - FIGURE_BOX[0], box[1] - FIGURE_BOX[1],
           box[2] - FIGURE_BOX[0], box[3] - FIGURE_BOX[1])
    color = (210, 0, 0) if int(oid[1:]) >= 8 else (0, 90, 210)
    d.rectangle(rel, outline=color, width=3)
    label(d, (rel[0], rel[1]), oid, color)
overlay.save(ROOT / "object_denominator_overlay_300dpi.png")

text_overlay = native.copy()
d = ImageDraw.Draw(text_overlay)
for oid, box_pt in TEXT_BOXES_PT.items():
    box = to_px(box_pt)
    pad = 5
    rel = (box[0] - FIGURE_BOX[0] - pad, box[1] - FIGURE_BOX[1] - pad,
           box[2] - FIGURE_BOX[0] + pad, box[3] - FIGURE_BOX[1] + pad)
    d.rectangle(rel, outline=(180, 0, 180), width=3)
    label(d, (rel[0], rel[1]), oid, (180, 0, 180))
text_overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

for name, box in ROIS.items():
    roi = page300.crop(box)
    roi.save(ROOT / f"{name}_native1x.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
        ROOT / f"{name}_nearest8x.png"
    )

# These two files freeze only the mechanical denominator and pair keys.
# They deliberately contain no reviewer verdict, note, or PASS/FAIL field.
with (ROOT / "frozen_object_denominator.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["OBJECT_ID", "PANEL_ID", "KIND", "ROLE", "DESCRIPTION", "BBOX_300DPI"])
    for oid, (kind, role, description) in OBJECTS.items():
        w.writerow([oid, "P1", kind, role, description, " ".join(map(str, OBJECT_BOXES[oid]))])

with (ROOT / "frozen_unordered_pair_denominator.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B"])
    ids = list(OBJECTS)
    pair_index = 0
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            pair_index += 1
            w.writerow([f"P{pair_index:03d}", a, b])

print({
    "page300": page300.size,
    "page200": page200.size,
    "figure_box": FIGURE_BOX,
    "native": native.size,
    "objects": len(OBJECT_BOXES),
    "unordered_pairs": len(OBJECT_BOXES) * (len(OBJECT_BOXES) - 1) // 2,
    "text_boxes": len(TEXT_BOXES_PT),
    "rois": len(ROIS),
})
