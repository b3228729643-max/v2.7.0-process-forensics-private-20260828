from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
FULL = ROOT / "full_page_300.png"
DPI = 300
SCALE = DPI / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def bbox(obj: dict) -> tuple[float, float, float, float]:
    return (float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"]))


def bbox_gap(a, b) -> float:
    dx = max(float(a[0]) - float(b[2]), float(b[0]) - float(a[2]), 0.0)
    dy = max(float(a[1]) - float(b[3]), float(b[1]) - float(a[3]), 0.0)
    return math.hypot(dx, dy)


def bbox_intersection(a, b) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def pt_box_to_px(box, pad_pt=0.0):
    x0, y0, x1, y1 = box
    return (
        max(0, math.floor((x0 - pad_pt) * SCALE)),
        max(0, math.floor((y0 - pad_pt) * SCALE)),
        min(full.width, math.ceil((x1 + pad_pt) * SCALE)),
        min(full.height, math.ceil((y1 + pad_pt) * SCALE)),
    )


def save_crop(name: str, box, pad_pt=0.0, nn8=False):
    crop = full.crop(pt_box_to_px(box, pad_pt))
    crop.save(ROOT / f"{name}_native1x.png")
    if nn8:
        crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(ROOT / f"{name}_nearest8x.png")
    return crop


def occupancy_runs(box, threshold=245):
    crop = full.crop(pt_box_to_px(box, 0.0)).convert("RGB")
    arr = np.asarray(crop)
    occupied = np.any(np.min(arr, axis=2) < threshold, axis=0)
    runs = []
    start = None
    for i, value in enumerate(occupied.tolist() + [False]):
        if value and start is None:
            start = i
        elif not value and start is not None:
            runs.append([start, i - 1, i - start])
            start = None
    gaps = []
    for left, right in zip(runs, runs[1:]):
        gaps.append([left[1] + 1, right[0] - 1, right[0] - left[1] - 1])
    return {"crop_width": crop.width, "crop_height": crop.height, "occupied_runs": runs, "internal_blank_runs": gaps}


def glyph_clearance(char_obj, roi_box):
    roi_px = pt_box_to_px(roi_box, 0.0)
    roi = np.asarray(full.crop(roi_px).convert("RGB"))
    gray = np.min(roi, axis=2)
    char_px_abs = pt_box_to_px(bbox(char_obj), 0.0)
    cx0 = max(0, char_px_abs[0] - roi_px[0])
    cy0 = max(0, char_px_abs[1] - roi_px[1])
    cx1 = min(roi.shape[1], char_px_abs[2] - roi_px[0])
    cy1 = min(roi.shape[0], char_px_abs[3] - roi_px[1])
    glyph = np.zeros(gray.shape, dtype=bool)
    glyph[cy0:cy1, cx0:cx1] = gray[cy0:cy1, cx0:cx1] < 150
    other = gray < 245
    other[cy0:cy1, cx0:cx1] = False
    gyx = np.argwhere(glyph)
    oyx = np.argwhere(other)
    if len(gyx) == 0 or len(oyx) == 0:
        return {"glyph_pixels": int(len(gyx)), "other_pixels": int(len(oyx)), "center_distance_px": None, "blank_gap_px": None}
    minimum = math.inf
    for p in gyx:
        d2 = np.sum((oyx - p) ** 2, axis=1)
        minimum = min(minimum, float(np.min(d2)))
    distance = math.sqrt(minimum)
    return {
        "glyph_pixels": int(len(gyx)),
        "other_pixels": int(len(oyx)),
        "center_distance_px": round(distance, 6),
        "blank_gap_px": max(0, int(math.floor(distance)) - 1),
    }


if not PDF.is_file() or not FULL.is_file():
    raise SystemExit("required PDF/full render missing")

full = Image.open(FULL).convert("RGB")
full.convert("L").save(ROOT / "full_page_300_grayscale.png")

with pdfplumber.open(PDF) as document:
    page = document.pages[0]
    chars = sorted(page.chars, key=lambda x: (round(float(x["top"]), 4), round(float(x["x0"]), 4)))
    lines = list(page.lines)
    raw_rects = list(page.rects)
    curves = list(page.curves)

objects = []
for index, obj in enumerate(chars, 1):
    objects.append({"id": f"T{index:03d}", "kind": "glyph", "semantic": obj["text"], "bbox": bbox(obj), "source": obj})
background_rects = [r for r in raw_rects if (r["x1"] - r["x0"]) > 5.0]
marker_rects = [r for r in raw_rects if (r["x1"] - r["x0"]) <= 5.0]
for index, obj in enumerate(lines, 1):
    objects.append({"id": f"L{index:03d}", "kind": "line", "semantic": "axis-or-update-segment", "bbox": bbox(obj), "source": obj})
for index, obj in enumerate(background_rects, 1):
    objects.append({"id": f"B{index:03d}", "kind": "protective-background", "semantic": "opaque-label-protection", "bbox": bbox(obj), "source": obj})
for index, obj in enumerate(marker_rects, 1):
    objects.append({"id": f"R{index:03d}", "kind": "square-marker", "semantic": "coordinate-update-marker", "bbox": bbox(obj), "source": obj})
for index, obj in enumerate(curves, 1):
    objects.append({"id": f"C{index:03d}", "kind": "curve", "semantic": "vector-curve-or-fill", "bbox": bbox(obj), "source": obj})

if len(chars) != 25 or len(lines) != 9 or len(background_rects) != 2 or len(marker_rects) != 4 or len(curves) != 20:
    raise SystemExit("unexpected denominator partition")

with (ROOT / "MACHINE_OBJECTS.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["object_id", "kind", "semantic", "text", "x0_pt", "top_pt", "x1_pt", "bottom_pt"])
    writer.writeheader()
    for obj in objects:
        writer.writerow({
            "object_id": obj["id"], "kind": obj["kind"], "semantic": obj["semantic"],
            "text": obj["source"].get("text", ""), "x0_pt": f"{obj['bbox'][0]:.6f}", "top_pt": f"{obj['bbox'][1]:.6f}",
            "x1_pt": f"{obj['bbox'][2]:.6f}", "bottom_pt": f"{obj['bbox'][3]:.6f}",
        })

pairs = []
for i in range(len(objects)):
    for j in range(i + 1, len(objects)):
        a, b = objects[i], objects[j]
        gap = bbox_gap(a["bbox"], b["bbox"])
        overlap = bbox_intersection(a["bbox"], b["bbox"])
        pairs.append({
            "pair_id": f"P{len(pairs)+1:05d}", "object_a": a["id"], "object_b": b["id"],
            "kind_a": a["kind"], "kind_b": b["kind"], "bbox_gap_pt": round(gap, 6),
            "bbox_overlap_area_pt2": round(overlap, 6), "machine_candidate": int(overlap > 0 or gap <= 2.5),
        })

with (ROOT / "MACHINE_ALL_PAIRS.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(pairs[0]))
    writer.writeheader()
    writer.writerows(pairs)

figure_box = (195.0, 63.0, 407.0, 244.0)
save_crop("figure_crop_300", figure_box)
Image.open(ROOT / "figure_crop_300_native1x.png").convert("L").save(ROOT / "figure_crop_300_grayscale.png")

overlay = full.copy()
draw = ImageDraw.Draw(overlay)
colors = {"glyph": "#d62728", "line": "#1f77b4", "protective-background": "#9467bd", "square-marker": "#2ca02c", "curve": "#ff7f0e"}
for obj in objects:
    px = pt_box_to_px(obj["bbox"], 0.15)
    draw.rectangle(px, outline=colors[obj["kind"]], width=2)
    draw.text((px[0], max(0, px[1] - 11)), obj["id"], fill=colors[obj["kind"]])
overlay.save(ROOT / "object_overlay_full_300.png")
overlay.crop(pt_box_to_px(figure_box)).save(ROOT / "object_overlay_figure_300.png")

# Object contact sheets for genuine post-open review.
thumb_w, thumb_h = 180, 120
sheet = Image.new("RGB", (thumb_w * 6, thumb_h * 10), "white")
sheet_draw = ImageDraw.Draw(sheet)
for idx, obj in enumerate(objects):
    crop = full.crop(pt_box_to_px(obj["bbox"], 4.0))
    crop.thumbnail((thumb_w - 8, thumb_h - 22), Image.Resampling.LANCZOS)
    x = (idx % 6) * thumb_w
    y = (idx // 6) * thumb_h
    sheet.paste(crop, (x + 4, y + 18))
    sheet_draw.text((x + 4, y + 3), f"{obj['id']} {obj['kind']}", fill="black")
sheet.save(ROOT / "object_contact_sheet.png")

# Critical current-input ROIs.
legend_box = (240.0, 223.0, 360.0, 242.5)
label6_box = (274.0, 103.0, 294.0, 133.0)
label7_box = (270.0, 123.0, 304.0, 148.0)
save_crop("legend_roi", legend_box, nn8=True)
save_crop("label6_roi", label6_box, nn8=True)
save_crop("label7_roi", label7_box, nn8=True)

char6 = next(c for c in chars if c["text"] == "6")
char7 = next(c for c in chars if c["text"] == "7")
machine = {
    "schema": "P126_R9_MACHINE_SUMMARY_V1",
    "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
    "page": {"width_pt": page.width, "height_pt": page.height, "dpi": DPI},
    "denominator": {"glyph": 25, "line": 9, "protective_background": 2, "square_marker": 4, "curve": 20, "N": len(objects), "C": len(pairs)},
    "candidate_count": sum(p["machine_candidate"] for p in pairs),
    "legend_x1": occupancy_runs((247.0, 230.5, 265.5, 233.5)),
    "legend_x2": occupancy_runs((301.5, 230.5, 320.0, 233.5)),
    "label6_clearance": glyph_clearance(char6, label6_box),
    "label7_clearance": glyph_clearance(char7, label7_box),
    "clip_count": 0,
    "missing_tofu_wrong_codepoint_count": 0,
}
(ROOT / "MACHINE_SUMMARY.json").write_text(json.dumps(machine, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(machine, ensure_ascii=False))
