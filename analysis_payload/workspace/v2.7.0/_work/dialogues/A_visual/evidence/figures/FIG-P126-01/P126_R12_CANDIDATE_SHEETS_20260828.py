import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828")
SCALE = 300 / 72.0
full = Image.open(ROOT / "full_page_300.png").convert("RGB")

with (ROOT / "MACHINE_OBJECTS.csv").open(encoding="utf-8-sig") as stream:
    objects = {row["object_id"]: row for row in csv.DictReader(stream)}
with (ROOT / "MACHINE_ALL_PAIRS.csv").open(encoding="utf-8-sig") as stream:
    candidates = [row for row in csv.DictReader(stream) if row["machine_candidate"] == "1"]


def box(row):
    return tuple(float(row[key]) for key in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))


def focus(left, right):
    lx0, ly0, lx1, ly1 = left
    rx0, ry0, rx1, ry1 = right
    ix0, iy0, ix1, iy1 = max(lx0, rx0), max(ly0, ry0), min(lx1, rx1), min(ly1, ry1)
    if ix1 >= ix0 and iy1 >= iy0:
        cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
    else:
        lcx, lcy = (lx0 + lx1) / 2, (ly0 + ly1) / 2
        rcx, rcy = (rx0 + rx1) / 2, (ry0 + ry1) / 2
        cx, cy = (lcx + rcx) / 2, (lcy + rcy) / 2
    return (cx - 14, cy - 10, cx + 14, cy + 10)


panel_width, panel_height = 360, 280
pairs_per_sheet = 20
sheet_count = math.ceil(len(candidates) / pairs_per_sheet)
for sheet_index in range(sheet_count):
    subset = candidates[sheet_index * pairs_per_sheet : (sheet_index + 1) * pairs_per_sheet]
    sheet = Image.new("RGB", (panel_width * 4, panel_height * 5), "white")
    drawer = ImageDraw.Draw(sheet)
    for index, pair in enumerate(subset):
        left = objects[pair["object_a"]]
        right = objects[pair["object_b"]]
        focus_box = focus(box(left), box(right))
        pixel_box = tuple(max(0, int(round(value * SCALE))) for value in focus_box)
        pixel_box = (pixel_box[0], pixel_box[1], min(full.width, pixel_box[2]), min(full.height, pixel_box[3]))
        crop = full.crop(pixel_box)
        crop.thumbnail((panel_width - 8, panel_height - 42), Image.Resampling.NEAREST)
        x = (index % 4) * panel_width
        y = (index // 4) * panel_height
        sheet.paste(crop, (x + 4, y + 38))
        drawer.text((x + 4, y + 3), f"{pair['pair_id']} {pair['object_a']}<->{pair['object_b']}", fill="black")
        drawer.text(
            (x + 4, y + 18),
            f"gap={pair['bbox_gap_pt']} overlap={pair['bbox_overlap_area_pt2']}",
            fill="black",
        )
    sheet.save(ROOT / f"candidate_relations_part{sheet_index + 1:02d}.png")

print(f"candidate_sheets={sheet_count} candidates={len(candidates)}")
