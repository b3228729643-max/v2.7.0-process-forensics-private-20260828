from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


R9 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828")
R10 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R10_SA2_STATIC_TWO_HARD_PATCH_R115_20260828")
SCALE = 300 / 72
SHIFT_PT = 5.0
SHIFT_PX = round(SHIFT_PT * SCALE)


def pt_box(row: dict[str, str]) -> tuple[float, float, float, float]:
    return tuple(float(row[k]) for k in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))


def px_box(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(v * SCALE) for v in box)


def overlap_area(a, b) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def bbox_gap(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


with (R9 / "MACHINE_OBJECTS.csv").open("r", encoding="utf-8-sig", newline="") as f:
    rows = {r["object_id"]: r for r in csv.DictReader(f)}

full = Image.open(R9 / "full_page_300.png").convert("RGB")
arr = np.asarray(full)
t9 = pt_box(rows["T009"])
t10 = pt_box(rows["T010"])
b1 = pt_box(rows["B001"])
c16 = pt_box(rows["C016"])
t10_new = (t10[0], t10[1] - SHIFT_PT, t10[2], t10[3] - SHIFT_PT)
b1_new = (b1[0], b1[1] - SHIFT_PT, b1[2], b1[3] - SHIFT_PT)

# Actual R9 digit-4 dark pixels that would lie under the translated opaque white background.
t9_px = px_box(t9)
b1_new_px = px_box(b1_new)
black = np.max(arr, axis=2) < 110
x0 = max(t9_px[0], b1_new_px[0])
y0 = max(t9_px[1], b1_new_px[1])
x1 = min(t9_px[2], b1_new_px[2])
y1 = min(t9_px[3], b1_new_px[3])
covered_digit4_pixels = int(black[y0:y1, x0:x1].sum()) if x1 > x0 and y1 > y0 else 0

# Static visual overlay: current node remains blue-boxed; translated opaque node is pasted and red-boxed.
node_union = (min(t10[0], b1[0]), min(t10[1], b1[1]), max(t10[2], b1[2]), max(t10[3], b1[3]))
node_px = px_box(node_union)
patch = full.crop(node_px)
projected = full.copy()
projected.paste(patch, (node_px[0], node_px[1] - SHIFT_PX))
draw = ImageDraw.Draw(projected)
draw.rectangle(node_px, outline=(0, 80, 255), width=2)
new_node_px = (node_px[0], node_px[1] - SHIFT_PX, node_px[2], node_px[3] - SHIFT_PX)
draw.rectangle(new_node_px, outline=(255, 0, 0), width=2)
crop_box = (1125, 420, 1225, 525)
projection_crop = projected.crop(crop_box)
projection_crop.save(R10 / "STATIC_LABEL6_SHIFT_PROJECTION_NATIVE1X.png")
projection_crop.resize((projection_crop.width * 8, projection_crop.height * 8), Image.Resampling.NEAREST).save(R10 / "STATIC_LABEL6_SHIFT_PROJECTION_NEAREST8X.png")

result = {
    "schema": "P126_R10_STATIC_PROJECTION_V1",
    "source_pdf": str(R9 / "build" / "v260_FIG-P126-01_standalone.pdf"),
    "dpi": 300,
    "authorized_shift_pt": SHIFT_PT,
    "rounded_shift_px": SHIFT_PX,
    "legend": {
        "sample_centers_cm": [0.0, 0.3, 0.6],
        "mark": "-",
        "mark_size_pt": 1.8,
        "bar_length_pt": 3.6,
        "center_distance_pt": 0.3 * 72 / 2.54,
        "predicted_blank_pt": (0.3 * 72 / 2.54) - 3.6,
        "predicted_blank_px_300dpi": ((0.3 * 72 / 2.54) - 3.6) * SCALE,
        "static_direction": "THREE_DISCONNECTED_HORIZONTAL_MARKS",
    },
    "label6": {
        "old_t010_bbox_pt": t10,
        "new_t010_bbox_pt": t10_new,
        "old_background_bbox_pt": b1,
        "new_background_bbox_pt": b1_new,
        "new_t010_to_q4_marker_bbox_gap_pt": bbox_gap(t10_new, c16),
        "new_t010_to_q4_marker_bbox_gap_px_300dpi": bbox_gap(t10_new, c16) * SCALE,
        "new_background_to_digit4_bbox_overlap_pt2": overlap_area(b1_new, t9),
        "digit4_dark_pixels_inside_new_background": covered_digit4_pixels,
        "static_direction": "Q4_CONTACT_REMOVED_BUT_DIGIT4_OCCLUSION_PREDICTED",
    },
    "verdict": "STATIC_SCOPE_BLOCKED_BY_PREDICTED_DIGIT4_OCCLUSION",
}
(R10 / "STATIC_PROJECTION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
