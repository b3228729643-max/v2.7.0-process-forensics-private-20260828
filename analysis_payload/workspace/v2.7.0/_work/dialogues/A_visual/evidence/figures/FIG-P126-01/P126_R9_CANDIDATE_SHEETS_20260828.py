import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828")
SCALE = 300 / 72.0
full = Image.open(ROOT / "full_page_300.png").convert("RGB")

with (ROOT / "MACHINE_OBJECTS.csv").open(encoding="utf-8-sig") as f:
    objects = {r["object_id"]: r for r in csv.DictReader(f)}
with (ROOT / "MACHINE_ALL_PAIRS.csv").open(encoding="utf-8-sig") as f:
    candidates = [r for r in csv.DictReader(f) if r["machine_candidate"] == "1"]


def box(row):
    return tuple(float(row[k]) for k in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))


def focus(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if ix1 >= ix0 and iy1 >= iy0:
        cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
    else:
        acx, acy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
        bcx, bcy = (bx0 + bx1) / 2, (by0 + by1) / 2
        cx, cy = (acx + bcx) / 2, (acy + bcy) / 2
    return (cx - 14, cy - 10, cx + 14, cy + 10)


panel_w, panel_h = 360, 280
per_sheet = 20
for sheet_index in range(math.ceil(len(candidates) / per_sheet)):
    subset = candidates[sheet_index * per_sheet:(sheet_index + 1) * per_sheet]
    sheet = Image.new("RGB", (panel_w * 4, panel_h * 5), "white")
    draw = ImageDraw.Draw(sheet)
    for index, pair in enumerate(subset):
        a = objects[pair["object_a"]]
        b = objects[pair["object_b"]]
        fb = focus(box(a), box(b))
        px = tuple(max(0, int(round(v * SCALE))) for v in fb)
        px = (px[0], px[1], min(full.width, px[2]), min(full.height, px[3]))
        crop = full.crop(px)
        crop.thumbnail((panel_w - 8, panel_h - 42), Image.Resampling.NEAREST)
        x = (index % 4) * panel_w
        y = (index // 4) * panel_h
        sheet.paste(crop, (x + 4, y + 38))
        draw.text((x + 4, y + 3), f"{pair['pair_id']} {pair['object_a']}↔{pair['object_b']}", fill="black")
        draw.text((x + 4, y + 18), f"gap={pair['bbox_gap_pt']} overlap={pair['bbox_overlap_area_pt2']}", fill="black")
    sheet.save(ROOT / f"candidate_relations_part{sheet_index+1:02d}.png")

print(f"candidate_sheets={math.ceil(len(candidates)/per_sheet)} candidates={len(candidates)}")
