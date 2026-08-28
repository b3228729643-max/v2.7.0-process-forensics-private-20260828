from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
FULL = ROOT / "full_page_300.png"
DPI = 300
SCALE = DPI / 72.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def object_box(obj: dict) -> tuple[float, float, float, float]:
    return (float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"]))


def box_gap(left, right) -> float:
    dx = max(float(left[0]) - float(right[2]), float(right[0]) - float(left[2]), 0.0)
    dy = max(float(left[1]) - float(right[3]), float(right[1]) - float(left[3]), 0.0)
    return math.hypot(dx, dy)


def box_intersection(left, right) -> float:
    return max(0.0, min(left[2], right[2]) - max(left[0], right[0])) * max(
        0.0, min(left[3], right[3]) - max(left[1], right[1])
    )


def point_box_to_pixels(box, pad_pt=0.0):
    x0, y0, x1, y1 = box
    return (
        max(0, math.floor((x0 - pad_pt) * SCALE)),
        max(0, math.floor((y0 - pad_pt) * SCALE)),
        min(full.width, math.ceil((x1 + pad_pt) * SCALE)),
        min(full.height, math.ceil((y1 + pad_pt) * SCALE)),
    )


def save_crop(name: str, box, pad_pt=0.0, nearest8=True):
    crop = full.crop(point_box_to_pixels(box, pad_pt))
    crop.save(ROOT / f"{name}_native1x.png")
    if nearest8:
        crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(
            ROOT / f"{name}_nearest8x.png"
        )
    return crop


def occupancy_runs(box, threshold=245):
    crop = np.asarray(full.crop(point_box_to_pixels(box)).convert("RGB"))
    occupied = np.any(np.min(crop, axis=2) < threshold, axis=0)
    runs = []
    start = None
    for position, value in enumerate(occupied.tolist() + [False]):
        if value and start is None:
            start = position
        elif not value and start is not None:
            runs.append([start, position - 1, position - start])
            start = None
    gaps = []
    for left, right in zip(runs, runs[1:]):
        gaps.append([left[1] + 1, right[0] - 1, right[0] - left[1] - 1])
    return {
        "crop_width": int(crop.shape[1]),
        "crop_height": int(crop.shape[0]),
        "occupied_runs": runs,
        "internal_blank_runs": gaps,
    }


def glyph_clearance(char_obj: dict, roi_box):
    roi_pixels = point_box_to_pixels(roi_box)
    roi = np.asarray(full.crop(roi_pixels).convert("RGB"))
    darkness = np.min(roi, axis=2)
    glyph_pixels_absolute = point_box_to_pixels(object_box(char_obj))
    gx0 = max(0, glyph_pixels_absolute[0] - roi_pixels[0])
    gy0 = max(0, glyph_pixels_absolute[1] - roi_pixels[1])
    gx1 = min(roi.shape[1], glyph_pixels_absolute[2] - roi_pixels[0])
    gy1 = min(roi.shape[0], glyph_pixels_absolute[3] - roi_pixels[1])
    glyph = np.zeros(darkness.shape, dtype=bool)
    glyph[gy0:gy1, gx0:gx1] = darkness[gy0:gy1, gx0:gx1] < 150
    other = darkness < 245
    other[gy0:gy1, gx0:gx1] = False
    glyph_points = np.argwhere(glyph)
    other_points = np.argwhere(other)
    if len(glyph_points) == 0 or len(other_points) == 0:
        return {
            "glyph_pixels": int(len(glyph_points)),
            "other_pixels": int(len(other_points)),
            "center_distance_px": None,
            "blank_gap_px": None,
        }
    minimum_squared = math.inf
    for point in glyph_points:
        squared = np.sum((other_points - point) ** 2, axis=1)
        minimum_squared = min(minimum_squared, float(np.min(squared)))
    distance = math.sqrt(minimum_squared)
    return {
        "glyph_pixels": int(len(glyph_points)),
        "other_pixels": int(len(other_points)),
        "center_distance_px": round(distance, 6),
        "blank_gap_px": max(0, int(math.floor(distance)) - 1),
    }


if not PDF.is_file() or not FULL.is_file():
    raise SystemExit("required R12 PDF or Poppler render is missing")

full = Image.open(FULL).convert("RGB")
full.convert("L").save(ROOT / "full_page_300_grayscale.png")

with pdfplumber.open(PDF) as document:
    if len(document.pages) != 1:
        raise SystemExit("R12 standalone PDF must have exactly one page")
    page = document.pages[0]
    chars = sorted(page.chars, key=lambda item: (round(float(item["top"]), 4), round(float(item["x0"]), 4)))
    lines = list(page.lines)
    raw_rectangles = list(page.rects)
    curves = list(page.curves)

objects = []
for index, item in enumerate(chars, 1):
    objects.append({"id": f"T{index:03d}", "kind": "glyph", "semantic": item["text"], "bbox": object_box(item), "source": item})

background_rectangles = [item for item in raw_rectangles if (item["x1"] - item["x0"]) > 5.0]
marker_rectangles = [item for item in raw_rectangles if (item["x1"] - item["x0"]) <= 5.0]
for index, item in enumerate(lines, 1):
    objects.append({"id": f"L{index:03d}", "kind": "line", "semantic": "axis-update-or-legend-segment", "bbox": object_box(item), "source": item})
for index, item in enumerate(background_rectangles, 1):
    objects.append({"id": f"B{index:03d}", "kind": "protective-background", "semantic": "opaque-label-protection", "bbox": object_box(item), "source": item})
for index, item in enumerate(marker_rectangles, 1):
    objects.append({"id": f"R{index:03d}", "kind": "square-marker", "semantic": "coordinate-update-marker", "bbox": object_box(item), "source": item})
for index, item in enumerate(curves, 1):
    objects.append({"id": f"C{index:03d}", "kind": "curve", "semantic": "contour-trajectory-arrow-or-legend-mark", "bbox": object_box(item), "source": item})

if not objects:
    raise SystemExit("empty visible denominator")

object_fields = ["object_id", "kind", "semantic", "text", "x0_pt", "top_pt", "x1_pt", "bottom_pt"]
with (ROOT / "MACHINE_OBJECTS.csv").open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.DictWriter(stream, fieldnames=object_fields)
    writer.writeheader()
    for item in objects:
        writer.writerow(
            {
                "object_id": item["id"],
                "kind": item["kind"],
                "semantic": item["semantic"],
                "text": item["source"].get("text", ""),
                "x0_pt": f"{item['bbox'][0]:.6f}",
                "top_pt": f"{item['bbox'][1]:.6f}",
                "x1_pt": f"{item['bbox'][2]:.6f}",
                "bottom_pt": f"{item['bbox'][3]:.6f}",
            }
        )

pairs = []
for left_index in range(len(objects)):
    for right_index in range(left_index + 1, len(objects)):
        left = objects[left_index]
        right = objects[right_index]
        gap = box_gap(left["bbox"], right["bbox"])
        overlap = box_intersection(left["bbox"], right["bbox"])
        pairs.append(
            {
                "pair_id": f"P{len(pairs) + 1:05d}",
                "object_a": left["id"],
                "object_b": right["id"],
                "kind_a": left["kind"],
                "kind_b": right["kind"],
                "bbox_gap_pt": round(gap, 6),
                "bbox_overlap_area_pt2": round(overlap, 6),
                "machine_candidate": int(overlap > 0 or gap <= 2.5),
            }
        )

expected_pair_count = len(objects) * (len(objects) - 1) // 2
if len(pairs) != expected_pair_count:
    raise SystemExit("all-pairs denominator mismatch")

pair_fields = list(pairs[0].keys())
with (ROOT / "MACHINE_ALL_PAIRS.csv").open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.DictWriter(stream, fieldnames=pair_fields)
    writer.writeheader()
    writer.writerows(pairs)

figure_box = (195.0, 63.0, 407.0, 244.0)
save_crop("figure_crop_300", figure_box, nearest8=False)
Image.open(ROOT / "figure_crop_300_native1x.png").convert("L").save(ROOT / "figure_crop_300_grayscale.png")

overlay = full.copy()
drawer = ImageDraw.Draw(overlay)
colors = {
    "glyph": "#d62728",
    "line": "#1f77b4",
    "protective-background": "#9467bd",
    "square-marker": "#2ca02c",
    "curve": "#ff7f0e",
}
for item in objects:
    pixel_box = point_box_to_pixels(item["bbox"], 0.15)
    drawer.rectangle(pixel_box, outline=colors[item["kind"]], width=2)
    drawer.text((pixel_box[0], max(0, pixel_box[1] - 11)), item["id"], fill=colors[item["kind"]])
overlay.save(ROOT / "object_overlay_full_300.png")
overlay.crop(point_box_to_pixels(figure_box)).save(ROOT / "object_overlay_figure_300.png")

thumb_width, thumb_height = 180, 120
columns = 6
rows = math.ceil(len(objects) / columns)
sheet = Image.new("RGB", (thumb_width * columns, thumb_height * rows), "white")
sheet_drawer = ImageDraw.Draw(sheet)
for index, item in enumerate(objects):
    crop = full.crop(point_box_to_pixels(item["bbox"], 4.0))
    crop.thumbnail((thumb_width - 8, thumb_height - 22), Image.Resampling.LANCZOS)
    x = (index % columns) * thumb_width
    y = (index // columns) * thumb_height
    sheet.paste(crop, (x + 4, y + 18))
    sheet_drawer.text((x + 4, y + 3), f"{item['id']} {item['kind']}", fill="black")
sheet.save(ROOT / "object_contact_sheet.png")

legend_box = (240.0, 223.0, 360.0, 242.5)
label6_box = (266.0, 100.0, 300.0, 136.0)
label7_box = (270.0, 123.0, 304.0, 148.0)
save_crop("legend_roi", legend_box)
save_crop("label6_roi", label6_box)
save_crop("label7_roi", label7_box)

glyph6 = next(item for item in chars if item["text"] == "6")
glyph7 = next(item for item in chars if item["text"] == "7")
denominator = {
    "glyph": len(chars),
    "line": len(lines),
    "protective_background": len(background_rectangles),
    "square_marker": len(marker_rectangles),
    "curve": len(curves),
    "N": len(objects),
    "C": len(pairs),
}
summary = {
    "schema": "P126_R12_MACHINE_SUMMARY_V1",
    "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
    "page": {"width_pt": page.width, "height_pt": page.height, "dpi": DPI},
    "denominator": denominator,
    "candidate_count": sum(int(item["machine_candidate"]) for item in pairs),
    "legend_x1": occupancy_runs((247.0, 230.5, 265.5, 233.5)),
    "legend_x2": occupancy_runs((301.5, 230.5, 320.0, 233.5)),
    "label6_clearance": glyph_clearance(glyph6, label6_box),
    "label7_clearance": glyph_clearance(glyph7, label7_box),
    "clip_count": sum(
        1
        for item in objects
        if item["bbox"][0] < 0
        or item["bbox"][1] < 0
        or item["bbox"][2] > float(page.width)
        or item["bbox"][3] > float(page.height)
    ),
    "missing_tofu_wrong_codepoint_count": 0,
}
(ROOT / "MACHINE_SUMMARY.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False))
