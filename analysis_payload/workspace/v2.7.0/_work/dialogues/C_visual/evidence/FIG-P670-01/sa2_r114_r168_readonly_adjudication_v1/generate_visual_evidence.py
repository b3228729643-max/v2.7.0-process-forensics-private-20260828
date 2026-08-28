from pathlib import Path
import csv

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa2_r114_r168_readonly_adjudication_v1")
FULL = ROOT / "page_717_full_300dpi.png"


def save_crop(source: Image.Image, name: str, box: tuple[int, int, int, int]) -> Image.Image:
    crop = source.crop(box)
    crop.save(ROOT / name, dpi=(300, 300))
    return crop


def save_nn8(crop: Image.Image, name: str) -> None:
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(ROOT / name)


image = Image.open(FULL).convert("RGB")
if image.size != (2481, 3508):
    raise RuntimeError(f"unexpected page dimensions: {image.size}")

figure_box = (255, 275, 2225, 955)
diagram_box = (270, 285, 2215, 775)
figure = save_crop(image, "figure_with_caption_native_300dpi.png", figure_box)
diagram = save_crop(image, "figure_diagram_native_300dpi.png", diagram_box)
figure.convert("L").save(ROOT / "figure_with_caption_grayscale_300dpi.png", dpi=(300, 300))

rois = {
    "roi_left_formula": (285, 540, 850, 675),
    "roi_center_transition": (920, 285, 1485, 665),
    "roi_right_update": (1390, 470, 2205, 680),
    "roi_new_category2_token": (1870, 380, 2050, 515),
    "roi_takeaway": (430, 655, 2050, 770),
    "roi_caption": (270, 760, 2220, 950),
}
for stem, box in rois.items():
    crop = save_crop(image, f"{stem}_native1x.png", box)
    save_nn8(crop, f"{stem}_nearest8x.png")

# Coordinates are page-native 300 dpi pixels. Boxes represent the frozen visible
# inspection-object denominator; composite nodes include their reader-visible
# label plus the immediately enclosing border/fill.
objects = [
    ("O001", (285, 345, 905, 405)),
    ("O002", (280, 405, 355, 485)), ("O003", (355, 405, 435, 485)),
    ("O004", (435, 405, 515, 485)), ("O005", (515, 405, 595, 485)),
    ("O006", (595, 405, 675, 485)), ("O007", (675, 405, 755, 485)),
    ("O008", (755, 405, 835, 485)), ("O009", (835, 405, 915, 485)),
    ("O010", (915, 405, 995, 485)),
    ("O011", (310, 488, 850, 545)),
    ("O012", (360, 490, 485, 545)), ("O013", (585, 490, 705, 545)),
    ("O014", (755, 490, 835, 545)),
    ("O015", (315, 555, 855, 655)),
    ("O016", (840, 480, 1105, 560)), ("O017", (960, 330, 1060, 405)),
    ("O018", (1060, 420, 1280, 625)),
    ("O019", (1260, 480, 1485, 560)), ("O020", (1265, 275, 1425, 420)),
    ("O021", (1500, 345, 2040, 405)),
    ("O022", (1390, 405, 1470, 485)), ("O023", (1470, 405, 1550, 485)),
    ("O024", (1550, 405, 1630, 485)), ("O025", (1630, 405, 1710, 485)),
    ("O026", (1710, 405, 1790, 485)), ("O027", (1790, 405, 1870, 485)),
    ("O028", (1870, 405, 1950, 485)), ("O029", (1950, 405, 2030, 485)),
    ("O030", (2030, 405, 2110, 485)), ("O031", (2110, 405, 2190, 485)),
    ("O032", (1425, 488, 2035, 545)),
    ("O033", (1480, 490, 1625, 545)), ("O034", (1715, 490, 1860, 545)),
    ("O035", (1900, 490, 2015, 545)),
    ("O036", (1400, 550, 2190, 655)),
    ("O037", (435, 655, 2035, 765)),
    ("O038", (285, 770, 500, 825)),
    ("O039", (480, 760, 2205, 950)),
]

metadata = {
    "O001": ("TITLE", "left state title: time N and pseudo-count vector", "text+math"),
    "O002": ("TOKEN_NODE", "left category-1 token 1 of 4", "digit+circle border/fill"),
    "O003": ("TOKEN_NODE", "left category-1 token 2 of 4", "digit+circle border/fill"),
    "O004": ("TOKEN_NODE", "left category-1 token 3 of 4", "digit+circle border/fill"),
    "O005": ("TOKEN_NODE", "left category-1 token 4 of 4", "digit+circle border/fill"),
    "O006": ("TOKEN_NODE", "left category-2 token 1 of 3", "digit+circle border/fill"),
    "O007": ("TOKEN_NODE", "left category-2 token 2 of 3", "digit+circle border/fill"),
    "O008": ("TOKEN_NODE", "left category-2 token 3 of 3", "digit+circle border/fill"),
    "O009": ("TOKEN_NODE", "left category-3 token 1 of 2", "digit+circle border/fill"),
    "O010": ("TOKEN_NODE", "left category-3 token 2 of 2", "digit+circle border/fill"),
    "O011": ("PROPORTION_BAR", "left three-segment probability bar", "fills+outer border+dividers"),
    "O012": ("RATIO_LABEL", "left ratio 4/9", "math text"),
    "O013": ("RATIO_LABEL", "left ratio 3/9", "math text"),
    "O014": ("RATIO_LABEL", "left ratio 2/9", "math text"),
    "O015": ("FORMULA", "one-step posterior predictive formula", "math text+fraction rule"),
    "O016": ("ARROW", "left-to-observation prediction arrow", "shaft+arrowhead"),
    "O017": ("ARROW_LABEL", "prediction label", "Chinese text"),
    "O018": ("OBSERVATION_NODE", "observed class j equals 2", "text+math+circle border/fill"),
    "O019": ("ARROW", "observation-to-updated-state arrow", "shaft+arrowhead"),
    "O020": ("ARROW_LABEL", "update-only-class-j label", "Chinese text+math"),
    "O021": ("TITLE", "right state title: time N+1 and vector", "text+math"),
    "O022": ("TOKEN_NODE", "right category-1 token 1 of 4", "digit+circle border/fill"),
    "O023": ("TOKEN_NODE", "right category-1 token 2 of 4", "digit+circle border/fill"),
    "O024": ("TOKEN_NODE", "right category-1 token 3 of 4", "digit+circle border/fill"),
    "O025": ("TOKEN_NODE", "right category-1 token 4 of 4", "digit+circle border/fill"),
    "O026": ("TOKEN_NODE", "right category-2 token 1 of 4", "digit+circle border/fill"),
    "O027": ("TOKEN_NODE", "right category-2 token 2 of 4", "digit+circle border/fill"),
    "O028": ("TOKEN_NODE", "right category-2 token 3 of 4", "digit+circle border/fill"),
    "O029": ("TOKEN_NODE_NEW", "right new category-2 token 4 of 4", "digit+hatching+circle border/fill"),
    "O030": ("TOKEN_NODE", "right category-3 token 1 of 2", "digit+circle border/fill"),
    "O031": ("TOKEN_NODE", "right category-3 token 2 of 2", "digit+circle border/fill"),
    "O032": ("PROPORTION_BAR_UPDATED", "right three-segment probability bar with new-mass hatch", "fills+hatching+outer border+dividers"),
    "O033": ("RATIO_LABEL", "right ratio 4/10 for class 1", "math text"),
    "O034": ("RATIO_LABEL", "right ratio 4/10 for class 2", "math text"),
    "O035": ("RATIO_LABEL", "right ratio 2/10 for class 3", "math text"),
    "O036": ("UPDATE_FORMULA", "class-2 count and total pseudo-count updates", "math text"),
    "O037": ("TAKEAWAY_BOX", "smoothing reinforcement exchangeability and non-iid takeaway", "text+rounded border/background"),
    "O038": ("CAPTION_NUMBER", "figure number 34.10", "bold text"),
    "O039": ("CAPTION_TEXT", "posterior-predictive explanatory caption", "Chinese text+math"),
}

with (ROOT / "visible_object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.writer(handle)
    writer.writerow(["OBJECT_ID", "ROLE", "DESCRIPTION", "INTERNAL_COMPONENTS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"])
    for object_id, box in objects:
        role, description, components = metadata[object_id]
        writer.writerow([object_id, role, description, components, *box])

with (ROOT / "unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.writer(handle)
    writer.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B"])
    pair_index = 0
    for left in range(len(objects) - 1):
        for right in range(left + 1, len(objects)):
            pair_index += 1
            writer.writerow([f"P{pair_index:04d}", objects[left][0], objects[right][0]])

overlay = image.copy()
draw = ImageDraw.Draw(overlay)
font = ImageFont.load_default()
palette = [(200, 0, 0), (0, 115, 205), (0, 145, 70), (165, 70, 190)]
for index, (object_id, box) in enumerate(objects):
    color = palette[index % len(palette)]
    draw.rectangle(box, outline=color, width=3)
    label_box = (box[0], max(0, box[1] - 13), box[0] + 34, box[1])
    draw.rectangle(label_box, fill=(255, 255, 255), outline=color, width=1)
    draw.text((box[0] + 2, max(0, box[1] - 12)), object_id, fill=color, font=font)
overlay.crop(figure_box).save(ROOT / "semantic_object_overlay_300dpi.png", dpi=(300, 300))

print(f"PAGE_SIZE={image.width}x{image.height}")
print(f"DENOMINATOR_OBJECTS={len(objects)}")
print(f"UNORDERED_PAIRS={len(objects) * (len(objects) - 1) // 2}")
