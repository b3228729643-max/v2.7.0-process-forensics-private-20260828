from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


R9 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828")
R11 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R11_SA2_STATIC_LABEL6_REPOSITION_R115_20260828")
SCALE = 300 / 72
TEX_PT_TO_BP = 72 / 72.27


def box(row):
    return tuple(float(row[k]) for k in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))


def gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def px_box(b):
    return tuple(round(v * SCALE) for v in b)


with (R9 / "MACHINE_OBJECTS.csv").open("r", encoding="utf-8-sig", newline="") as f:
    rows = {r["object_id"]: r for r in csv.DictReader(f)}

old_glyph = box(rows["T010"])
old_bg = box(rows["B001"])
q6_x = float(rows["L009"]["x0_pt"])
q6_y = float(rows["L005"]["top_pt"])
bg_w = old_bg[2] - old_bg[0]
bg_h = old_bg[3] - old_bg[1]
new_bg_bottom = q6_y - 4 * TEX_PT_TO_BP
new_bg = (q6_x - bg_w / 2, new_bg_bottom - bg_h, q6_x + bg_w / 2, new_bg_bottom)
glyph_rel = (old_glyph[0] - old_bg[0], old_glyph[1] - old_bg[1], old_glyph[2] - old_bg[0], old_glyph[3] - old_bg[1])
new_glyph = (new_bg[0] + glyph_rel[0], new_bg[1] + glyph_rel[1], new_bg[0] + glyph_rel[2], new_bg[1] + glyph_rel[3])

targets = {
    "digit4_T009": box(rows["T009"]),
    "q4_marker_C016": box(rows["C016"]),
    "q6_marker_C017": box(rows["C017"]),
    "label5_T012": box(rows["T012"]),
    "label7_T015": box(rows["T015"]),
    "horizontal_arrow_L005": box(rows["L005"]),
    "vertical_arrow_L009": box(rows["L009"]),
    "inner_contour_C006": box(rows["C006"]),
}
gaps = {}
for name, target in targets.items():
    gaps[name] = {
        "glyph_gap_pt": gap(new_glyph, target),
        "glyph_gap_px_300dpi": gap(new_glyph, target) * SCALE,
        "background_gap_pt": gap(new_bg, target),
        "background_gap_px_300dpi": gap(new_bg, target) * SCALE,
    }

full = Image.open(R9 / "full_page_300.png").convert("RGB")
arr = np.asarray(full)
old_union = (min(old_glyph[0], old_bg[0]), min(old_glyph[1], old_bg[1]), max(old_glyph[2], old_bg[2]), max(old_glyph[3], old_bg[3]))
old_px = px_box(old_union)
dx_px = round((new_bg[0] - old_bg[0]) * SCALE)
dy_px = round((new_bg[1] - old_bg[1]) * SCALE)
new_px = (old_px[0] + dx_px, old_px[1] + dy_px, old_px[2] + dx_px, old_px[3] + dy_px)

# Count all pre-existing nonwhite pixels that the translated opaque background would cover.
nb = px_box(new_bg)
dest = arr[nb[1]:nb[3], nb[0]:nb[2], :]
dest_nonwhite = int((np.min(dest, axis=2) < 245).sum())
dest_dark = int((np.max(dest, axis=2) < 110).sum())

projected = full.copy()
draw = ImageDraw.Draw(projected)
# Reconstruct only the authorized node effect: an opaque white background and the
# black digit pixels. Do not translate the blue marker that overlaps the old node.
new_bg_px = px_box(new_bg)
draw.rectangle(new_bg_px, fill=(255, 255, 255))
old_glyph_px = px_box(old_glyph)
glyph_crop = np.asarray(full.crop(old_glyph_px).convert("RGB"))
glyph_black = np.max(glyph_crop, axis=2) < 110
glyph_rgba = np.zeros((glyph_crop.shape[0], glyph_crop.shape[1], 4), dtype=np.uint8)
glyph_rgba[glyph_black, :3] = glyph_crop[glyph_black]
glyph_rgba[glyph_black, 3] = 255
new_glyph_px = px_box(new_glyph)
projected.paste(Image.fromarray(glyph_rgba, mode="RGBA"), (new_glyph_px[0], new_glyph_px[1]), Image.fromarray(glyph_rgba, mode="RGBA"))
projected_arr = np.asarray(projected.convert("RGB"))
glyph_abs = np.zeros(projected_arr.shape[:2], dtype=bool)
gh, gw = glyph_black.shape
glyph_abs[new_glyph_px[1]:new_glyph_px[1] + gh, new_glyph_px[0]:new_glyph_px[0] + gw] = glyph_black
other_visible = np.min(projected_arr, axis=2) < 245
other_visible[glyph_abs] = False
gyx = np.argwhere(glyph_abs)
oyx = np.argwhere(other_visible)
minimum_d2 = min(float(np.min(np.sum((oyx - p) ** 2, axis=1))) for p in gyx)
visible_distance_px = math.sqrt(minimum_d2)
visible_blank_px = max(0, math.floor(visible_distance_px) - 1)
draw = ImageDraw.Draw(projected)
draw.rectangle(px_box(old_bg), outline=(0, 80, 255), width=2)
draw.rectangle(new_bg_px, outline=(255, 0, 0), width=2)
crop = projected.crop((1125, 430, 1260, 570))
crop.save(R11 / "STATIC_LABEL6_REPOSITION_PROJECTION_NATIVE1X.png")
crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(R11 / "STATIC_LABEL6_REPOSITION_PROJECTION_NEAREST8X.png")

result = {
    "schema": "P126_R11_STATIC_PROJECTION_V1",
    "dpi": 300,
    "source_pdf": str(R9 / "build" / "v260_FIG-P126-01_standalone.pdf"),
    "placement": "anchor=south,yshift=4pt",
    "q6_axis_point_pt": [q6_x, q6_y],
    "old_glyph_bbox_pt": old_glyph,
    "new_glyph_bbox_pt": new_glyph,
    "old_background_bbox_pt": old_bg,
    "new_background_bbox_pt": new_bg,
    "translation_pt": [new_bg[0] - old_bg[0], new_bg[1] - old_bg[1]],
    "translation_px_300dpi_rounded": [dx_px, dy_px],
    "gaps": gaps,
    "new_background_destination_nonwhite_pixels": dest_nonwhite,
    "new_background_destination_dark_pixels": dest_dark,
    "authorized_background_erases_only_nondark_contour_pixels": dest_nonwhite > 0 and dest_dark == 0,
    "projected_final_visible_ink_center_distance_px": visible_distance_px,
    "projected_final_visible_blank_px": visible_blank_px,
    "legend_predicted_blank_pt": (0.3 * 72 / 2.54) - 3.6,
    "legend_predicted_blank_px_300dpi": ((0.3 * 72 / 2.54) - 3.6) * SCALE,
    "all_noncontour_named_bbox_gaps_positive": all(min(v["glyph_gap_pt"], v["background_gap_pt"]) > 0 for k, v in gaps.items() if k != "inner_contour_C006"),
    "verdict": "STATIC_PROJECTION_PASS" if dest_dark == 0 and visible_blank_px > 0 and all(min(v["glyph_gap_pt"], v["background_gap_pt"]) > 0 for k, v in gaps.items() if k != "inner_contour_C006") else "STATIC_PROJECTION_FAIL",
}
(R11 / "STATIC_PROJECTION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
