"""Native-pixel component and semantic checks for the official 300 dpi raster.

All analysis in this file reads the 2481 x 3508 official page.  No resized
review image or resampled ROI is used for measurements.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, find_objects, label

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P186-01\STRICT_R1B")
PAGE = ROOT / "renders" / "official_p200_300dpi.png"
COMPONENTS_CSV = ROOT / "metrics" / "native_color_components.csv"
SEMANTICS_CSV = ROOT / "metrics" / "semantic_recompute.csv"
VIEWS_CSV = ROOT / "metrics" / "view_inventory.csv"
TEXT_CSV = ROOT / "metrics" / "text_element_audit.csv"
GLYPH_CSV = ROOT / "metrics" / "text_glyph_spans_native.csv"
GEOMETRY_CSV = ROOT / "metrics" / "geometry_ledger_native.csv"

img = Image.open(PAGE).convert("RGB")
assert img.size == (2481, 3508), img.size
pixels = np.asarray(img)

# Exact opaque element colours sampled from the official raster.  The crop
# reduces irrelevant page text while preserving the entire plotted diagram.
CROP_L, CROP_T, CROP_R, CROP_B = 690, 1760, 1840, 2860
crop = pixels[CROP_T:CROP_B, CROP_L:CROP_R]
COLOURS = {
    "blue": (31, 78, 121),
    "teal": (15, 118, 110),
    "gold": (183, 121, 31),
    "ink": (31, 35, 40),
    "axis_ink": (31, 42, 57),
}

component_rows = []
component_lookup: dict[str, list[dict[str, float]]] = {}
for name, rgb in COLOURS.items():
    mask = np.all(crop == rgb, axis=2)
    labels, count = label(mask, structure=np.ones((3, 3), dtype=int))
    slices = find_objects(labels)
    found = []
    for index, slc in enumerate(slices, start=1):
        if slc is None:
            continue
        ysl, xsl = slc
        local = labels[ysl, xsl] == index
        area = int(local.sum())
        if area < 5:
            continue
        left, top = CROP_L + xsl.start, CROP_T + ysl.start
        right, bottom = CROP_L + xsl.stop, CROP_T + ysl.stop
        record = {
            "colour": name,
            "component": index,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": right - left,
            "height": bottom - top,
            "area_px": area,
            "centre_x": round((left + right - 1) / 2, 3),
            "centre_y": round((top + bottom - 1) / 2, 3),
        }
        found.append(record)
        component_rows.append(record)
    component_lookup[name] = found

with COMPONENTS_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(component_rows[0]))
    writer.writeheader()
    writer.writerows(component_rows)

# The five blue disks are the only near-square blue connected components with
# their plotted marker dimensions.  Use their native centres to fit the plot's
# data-to-pixel affine map.  This is a measurement check against the official
# page, not an image rescale.
blue_disks = [
    c for c in component_lookup["blue"]
    if 18 <= c["width"] <= 30 and 18 <= c["height"] <= 30 and c["area_px"] >= 250
]
blue_disks.sort(key=lambda c: c["centre_y"])
assert len(blue_disks) == 5, blue_disks
positive_points = np.array([
    (-2.15, 2.15), (-1.25, 1.85), (-0.35, 1.25), (0.75, 0.95), (1.55, 0.40)
])
pixel_centres = np.array([(p["centre_x"], p["centre_y"]) for p in blue_disks])
x_slope, x_intercept = np.polyfit(positive_points[:, 0], pixel_centres[:, 0], 1)
y_slope, y_intercept = np.polyfit(positive_points[:, 1], pixel_centres[:, 1], 1)
assert x_slope > 0 and y_slope < 0
px_per_data_unit = (x_slope + abs(y_slope)) / 2

# Separating line: y=-0.68 x + 0.2.  Its upward/right normal is (0.68, 1).
normal = np.array([0.68, 1.0])
normal_norm = float(np.linalg.norm(normal))
normal_arrow = np.array([0.82, 1.405 - 0.2])
normal_cross = float(normal[0] * normal_arrow[1] - normal[1] * normal_arrow[0])
normal_dot = float(np.dot(normal, normal_arrow))

negative_points = np.array([
    (-1.70, -1.35), (-0.65, -1.25), (0.15, -0.75), (1.10, -1.35), (2.10, -1.05)
])

semantic_rows = []
for i, (x, y) in enumerate(positive_points, start=1):
    g = 0.68 * x + y - 0.2
    semantic_rows.append({
        "element": f"positive_disk_{i}", "declared_class": "+", "x": x, "y": y,
        "g=0.68x+y-0.2": round(g, 6), "correct_side": g > 0,
        "distance_to_boundary_data": round(abs(g) / normal_norm, 6),
        "distance_to_boundary_native_px": round(abs(g) / normal_norm * px_per_data_unit, 3),
    })
for i, (x, y) in enumerate(negative_points, start=1):
    g = 0.68 * x + y - 0.2
    semantic_rows.append({
        "element": f"negative_triangle_{i}", "declared_class": "-", "x": x, "y": y,
        "g=0.68x+y-0.2": round(g, 6), "correct_side": g < 0,
        "distance_to_boundary_data": round(abs(g) / normal_norm, 6),
        "distance_to_boundary_native_px": round(abs(g) / normal_norm * px_per_data_unit, 3),
    })
semantic_rows.extend([
    {
        "element": "normal_arrow_parallelism", "declared_class": "normal",
        "x": "", "y": "", "g=0.68x+y-0.2": "",
        "correct_side": abs(normal_cross) < 0.001 and normal_dot > 0,
        "distance_to_boundary_data": f"cross={normal_cross:.6f}; dot={normal_dot:.6f}",
        "distance_to_boundary_native_px": "",
    },
    {
        "element": "pixel_affine_scale", "declared_class": "measurement",
        "x": "", "y": "", "g=0.68x+y-0.2": "",
        "correct_side": True,
        "distance_to_boundary_data": f"x={x_slope:.6f}px/unit; y={y_slope:.6f}px/unit",
        "distance_to_boundary_native_px": f"mean={px_per_data_unit:.6f}px/unit",
    },
])
with SEMANTICS_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(semantic_rows[0]))
    writer.writeheader()
    writer.writerows(semantic_rows)

view_rows = [
    {"view": "whole_page_100pct", "file": "renders/official_p200_300dpi.png", "pixels": "2481x3508", "used_for_geometry": "yes", "resampled": "no"},
    {"view": "local_100pct_figure_caption", "file": "roi/figure_and_caption_native_1x.png", "pixels": "1480x1300", "used_for_geometry": "yes", "resampled": "no (native crop)"},
    {"view": "local_100pct_plot", "file": "roi/plot_native_1x.png", "pixels": "1150x1100", "used_for_geometry": "yes", "resampled": "no (native crop)"},
    {"view": "local_100pct_labels_normal", "file": "roi/labels_and_normal_native_1x.png", "pixels": "510x530", "used_for_geometry": "yes", "resampled": "no (native crop)"},
    {"view": "local_100pct_boundary_samples", "file": "roi/boundary_samples_native_1x.png", "pixels": "1110x890", "used_for_geometry": "yes", "resampled": "no (native crop)"},
    {"view": "local_100pct_boundary_label", "file": "roi/boundary_label_native_1x.png", "pixels": "310x95", "used_for_geometry": "yes", "resampled": "no (native crop)"},
    {"view": "local_100pct_misclassified_triangle", "file": "roi/misclassified_triangle_native_1x.png", "pixels": "160x160", "used_for_geometry": "yes", "resampled": "no (native crop)"},
    {"view": "fit_page", "file": "renders/official_p200_fitpage_review_only.png", "pixels": "708x1001", "used_for_geometry": "no", "resampled": "yes; visual review only"},
    {"view": "grayscale_native", "file": "renders/official_p200_300dpi_grayscale_native.png", "pixels": "2481x3508", "used_for_geometry": "yes", "resampled": "no"},
]
with VIEWS_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(view_rows[0]))
    writer.writeheader()
    writer.writerows(view_rows)

# Per-text-element source and raster audit.  ``window`` bounds isolate the
# indicated text in the native raster; no resizing is performed.  Direct
# labels inherit the 9.2 pt figure font; axis labels explicitly set 9.5 pt.
text_specs = [
    ("T01", r"w^T x+b>0", "direct label", 9.2, "blue", (800, 1810, 1100, 1890)),
    ("T02", r"w^T x+b<0", "direct label", 9.2, "teal", (1330, 2550, 1620, 2630)),
    ("T03", r"w^T x+b=0", "direct label", 9.2, "blue", (1460, 2340, 1730, 2415)),
    ("T04", r"w: 分数增大", "normal label", 9.2, "gold", (1415, 1990, 1720, 2080)),
    ("T05", r"x^(2)", "axis label", 9.5, "ink", (1270, 1780, 1370, 1900)),
    ("T06", r"x^(1)", "axis label", 9.5, "ink", (1710, 2200, 1810, 2275)),
]

def target_mask(window, rgb):
    left, top, right, bottom = window
    arr = pixels[top:bottom, left:right].astype(np.int16)
    target = np.asarray(rgb, dtype=np.int16)
    # Includes antialiased foreground but excludes white label backgrounds.
    return np.max(np.abs(arr - target), axis=2) <= 70

def bbox_from_mask(mask, window):
    left, top, _, _ = window
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return (int(left + xs.min()), int(top + ys.min()), int(left + xs.max() + 1), int(top + ys.max() + 1))

text_rows = []
glyph_rows = []
text_masks = {}
for text_id, content, role, point_size, colour, window in text_specs:
    mask = target_mask(window, COLOURS[colour])
    bbox = bbox_from_mask(mask, window)
    assert bbox is not None, text_id
    full_mask = np.zeros(pixels.shape[:2], dtype=bool)
    left_w, top_w, right_w, bottom_w = window
    full_mask[top_w:bottom_w, left_w:right_w] = mask
    text_masks[text_id] = full_mask
    left, top, right, bottom = bbox
    text_rows.append({
        "id": text_id,
        "content": content,
        "role": role,
        "declared_effective_pt": point_size,
        "pt_gate_ge_9_5": point_size >= 9.5,
        "native_bbox_ltrb": f"{left},{top},{right},{bottom}",
        "native_ink_width_px": right - left,
        "native_ink_height_px": bottom - top,
        "pixel_grid": "official 2481x3508 @300dpi; no resampling",
    })
    # Segment visible glyph spans from the row/column projection.  A one-pixel
    # horizontal closing keeps strokes of one glyph together but does not turn
    # the full label into one component.
    cols = mask.any(axis=0)
    padded = np.pad(cols.astype(np.int8), (1, 1))
    # Fill isolated one-pixel gaps only.
    cols = np.logical_or(cols, (padded[:-2] & padded[2:]))
    starts = np.flatnonzero(np.diff(np.r_[False, cols, False].astype(int)) == 1)
    stops = np.flatnonzero(np.diff(np.r_[False, cols, False].astype(int)) == -1)
    for ordinal, (start, stop) in enumerate(zip(starts, stops), start=1):
        sub = mask[:, start:stop]
        ys, xs = np.nonzero(sub)
        if not len(xs):
            continue
        glyph_rows.append({
            "text_id": text_id,
            "span_ordinal": ordinal,
            "left": window[0] + int(start + xs.min()),
            "top": window[1] + int(ys.min()),
            "right": window[0] + int(start + xs.max() + 1),
            "bottom": window[1] + int(ys.max() + 1),
            "width_px": int(xs.max() - xs.min() + 1),
            "height_px": int(ys.max() - ys.min() + 1),
        })

with TEXT_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(text_rows[0]))
    writer.writeheader()
    writer.writerows(text_rows)
with GLYPH_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(glyph_rows[0]))
    writer.writeheader()
    writer.writerows(glyph_rows)

# Native geometry ledger.  Distances below are pixel-centre distances on the
# official page, calculated before any fit-page derivative is created.
full_blue = np.all(pixels == COLOURS["blue"], axis=2)
full_gold = np.all(pixels == COLOURS["gold"], axis=2)
full_axis_ink = np.all(pixels == COLOURS["axis_ink"], axis=2)
yy, xx = np.indices(pixels.shape[:2])

def x_pixel(x):
    return x_slope * x + x_intercept

def y_pixel(y):
    return y_slope * y + y_intercept

# Separating line y=-0.68x+0.2 in source coordinates, transformed to pixels.
p0 = np.array([x_pixel(0.0), y_pixel(0.2)])
p1 = np.array([x_pixel(1.0), y_pixel(-0.48)])
sep_slope = (p1[1] - p0[1]) / (p1[0] - p0[0])
sep_intercept = p0[1] - sep_slope * p0[0]
separator_visible = full_blue & (xx >= 715) & (xx <= 1812) & (np.abs(yy - (sep_slope * xx + sep_intercept)) <= 2.5)

def min_distance_px(source_mask, target_mask):
    # scipy returns Euclidean distance to the nearest target pixel in the
    # original 1:1 grid.
    values = distance_transform_edt(~target_mask)[source_mask]
    return float(values.min()) if values.size else float("nan")

# T03 shares the separator colour.  Restrict its glyph pixels to the native
# label window and remove pixels classified as the visible separator.
t03_text = text_masks["T03"] & ~separator_visible
t03_sep_gap = min_distance_px(t03_text, separator_visible)

# The arrow has no gold glyph pixels to the left of x=1415; the normal label
# begins at x=1421, so this cleanly separates the two visible objects.
normal_arrow_visible = full_gold & (xx < 1415)
t04_arrow_gap = min_distance_px(text_masks["T04"], normal_arrow_visible)
y_axis_arrow = full_axis_ink & (xx <= 1270) & (yy < 1814)
x_axis_arrow = full_axis_ink & (xx >= 1800) & (yy >= 2268) & (yy <= 2300)
t05_axis_gap = min_distance_px(text_masks["T05"], y_axis_arrow)
t06_axis_gap = min_distance_px(text_masks["T06"], x_axis_arrow)

# Text-to-text minima, excluding the separator from T03.
text_for_spacing = dict(text_masks)
text_for_spacing["T03"] = t03_text
pair_distances = []
ids = list(text_for_spacing)
for i, first in enumerate(ids):
    for second in ids[i + 1:]:
        pair_distances.append((first, second, min_distance_px(text_for_spacing[first], text_for_spacing[second])))
min_pair = min(pair_distances, key=lambda value: value[2])

# Plot and region-fill margins are calculated from their stated source extents.
plot_left, plot_right = x_pixel(-3.25), x_pixel(3.25)
plot_top, plot_bottom = y_pixel(2.85), y_pixel(-2.45)
fill_left, fill_right = x_pixel(-3.2), x_pixel(3.2)
fill_top, fill_bottom = y_pixel(2.8), y_pixel(-2.4)
edge_margin = min(fill_left - plot_left, plot_right - fill_right, fill_top - plot_top, plot_bottom - fill_bottom)

teal_triangles = [
    c for c in component_lookup["teal"]
    if 20 <= c["width"] <= 28 and 20 <= c["height"] <= 25 and c["area_px"] >= 180
]
assert len(teal_triangles) == 5, teal_triangles
blue_width_ratio = min(c["width"] for c in blue_disks) / max(c["width"] for c in blue_disks)
blue_height_ratio = min(c["height"] for c in blue_disks) / max(c["height"] for c in blue_disks)
teal_width_ratio = min(c["width"] for c in teal_triangles) / max(c["width"] for c in teal_triangles)
teal_height_ratio = min(c["height"] for c in teal_triangles) / max(c["height"] for c in teal_triangles)

geometry_rows = [
    {"criterion": "region-fill to plot edge", "elements": "upper/lower half-space fills", "observed_native_px": f"{edge_margin:.3f}", "threshold_px": ">=6", "verdict": edge_margin >= 6, "method": "source coordinates mapped through native marker-fit affine transform"},
    {"criterion": "separator endpoint to horizontal plot edge", "elements": "separator at x=±3.2", "observed_native_px": f"{min(fill_left - plot_left, plot_right - fill_right):.3f}", "threshold_px": ">=6", "verdict": min(fill_left - plot_left, plot_right - fill_right) >= 6, "method": "same native affine transform"},
    {"criterion": "text-to-separator visible gap", "elements": "T03 boundary label / separator", "observed_native_px": f"{t03_sep_gap:.3f}", "threshold_px": ">=3", "verdict": t03_sep_gap >= 3, "method": "1:1 RGB masks; separator classified by source line transformed onto the raster"},
    {"criterion": "text-to-arrow visible gap", "elements": "T04 normal label / gold normal arrow", "observed_native_px": f"{t04_arrow_gap:.3f}", "threshold_px": ">=3", "verdict": t04_arrow_gap >= 3, "method": "1:1 RGB masks"},
    {"criterion": "text-to-arrow visible gap", "elements": "T05 y-axis label / y-axis arrowhead", "observed_native_px": f"{t05_axis_gap:.3f}", "threshold_px": ">=3", "verdict": t05_axis_gap >= 3, "method": "1:1 RGB masks"},
    {"criterion": "text-to-arrow visible gap", "elements": "T06 x-axis label / x-axis arrowhead", "observed_native_px": f"{t06_axis_gap:.3f}", "threshold_px": ">=3", "verdict": t06_axis_gap >= 3, "method": "1:1 RGB masks"},
    {"criterion": "text-to-text visible gap", "elements": f"{min_pair[0]} / {min_pair[1]}", "observed_native_px": f"{min_pair[2]:.3f}", "threshold_px": ">=4", "verdict": min_pair[2] >= 4, "method": "all six text masks, native pixels"},
    {"criterion": "positive disk same-class pixel ratio", "elements": "five blue disks", "observed_native_px": f"width={blue_width_ratio:.4f}; height={blue_height_ratio:.4f}", "threshold_px": "[0.92,1.08]", "verdict": blue_width_ratio >= .92 and blue_height_ratio >= .92, "method": "opaque blue connected components"},
    {"criterion": "negative triangle same-class pixel ratio", "elements": "five teal triangles", "observed_native_px": f"width={teal_width_ratio:.4f}; height={teal_height_ratio:.4f}", "threshold_px": "[0.92,1.08]", "verdict": teal_width_ratio >= .92 and teal_height_ratio >= .92, "method": "opaque teal connected components"},
    {"criterion": "cross-panel / node-border", "elements": "single panel; labels have no drawn node borders", "observed_native_px": "N/A", "threshold_px": "N/A", "verdict": True, "method": "source inventory"},
]
with GEOMETRY_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(geometry_rows[0]))
    writer.writeheader()
    writer.writerows(geometry_rows)

print(f"native size: {img.size}; components: {len(component_rows)}")
print("blue disk centres:", [(c["centre_x"], c["centre_y"]) for c in blue_disks])
print(f"affine: x={x_slope:.6f}*x+{x_intercept:.6f}, y={y_slope:.6f}*y+{y_intercept:.6f}")
print(f"normal: cross={normal_cross:.6f}, dot={normal_dot:.6f}")
print("text element bboxes:")
for row in text_rows:
    print(row)
print("glyph spans:")
for row in glyph_rows:
    print(row)
print("geometry ledger:")
for row in geometry_rows:
    print(row)
for row in semantic_rows:
    print(row)
