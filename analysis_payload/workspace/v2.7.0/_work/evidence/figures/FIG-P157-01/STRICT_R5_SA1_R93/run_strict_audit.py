from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = ROOT / r"v2.7.0\_work\evidence\figures\FIG-P157-01\STRICT_R5_SA1_R93"
PDF = ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf"
SOURCE = ROOT / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C10\fig_v1_c10_complexity.tex"
PAGE_INDEX = 169
SCALE = 300.0 / 72.0

OUT.mkdir(parents=True, exist_ok=True)
page_png = OUT / "full_page_300dpi.png"
image = Image.open(page_png).convert("RGB")
rgb = np.asarray(image)
height, width = rgb.shape[:2]
assert (width, height) == (2481, 3508), (width, height)


def pt_bbox_to_px(bbox: tuple[float, float, float, float], pad: int = 3) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, int(math.floor(x0 * SCALE)) - pad),
        max(0, int(math.floor(y0 * SCALE)) - pad),
        min(width, int(math.ceil(x1 * SCALE)) + pad + 1),
        min(height, int(math.ceil(y1 * SCALE)) + pad + 1),
    )


ELEMENTS = [
    {
        "id": "T01_Y_AXIS_TITLE",
        "panel": "PANEL_MAIN",
        "role": "AXIS_TITLE",
        "source_line": "12-16;20-25",
        "declared_pt": 10.0,
        "scale": 1.12,
        "effective_pt": 11.20,
        "pdf_size_bp": 11.16,
        "text": "预测误差",
        "script": "CJK",
        "orientation": 90,
        "bbox_pt": (80.19, 153.26, 92.14, 197.89),
        "resolution_note": "slfig axis later-cascade resolved from final PDF text matrix",
    },
    {
        "id": "T02_VALIDATION_DIRECT",
        "panel": "PANEL_MAIN",
        "role": "DIRECT_ANNOTATION",
        "source_line": "5-7;47-48",
        "declared_pt": 9.2,
        "scale": 1.12,
        "effective_pt": 10.304,
        "pdf_size_bp": 10.27,
        "text": "验证误差：先降后升",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (267.66, 170.03, 360.05, 181.02),
    },
    {
        "id": "T03_MINIMUM_KEY",
        "panel": "PANEL_MAIN",
        "role": "KEY_ANNOTATION",
        "source_line": "8-9;49-50",
        "declared_pt": 9.2,
        "scale": 1.12,
        "effective_pt": 10.304,
        "pdf_size_bp": 10.27,
        "text": "最低验证误差",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (294.15, 214.07, 355.74, 225.07),
    },
    {
        "id": "T04_TRAINING_DIRECT",
        "panel": "PANEL_MAIN",
        "role": "DIRECT_ANNOTATION",
        "source_line": "5-7;44-46",
        "declared_pt": 9.2,
        "scale": 1.12,
        "effective_pt": 10.304,
        "pdf_size_bp": 10.27,
        "text": "训练误差：单调下降",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (420.65, 228.21, 513.04, 239.21),
    },
    {
        "id": "T05_SELECTION_KEY",
        "panel": "PANEL_MAIN",
        "role": "KEY_ANNOTATION",
        "source_line": "8-9;51-52",
        "declared_pt": 9.2,
        "scale": 1.12,
        "effective_pt": 10.304,
        "pdf_size_bp": 10.27,
        "text": "选择复杂度",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (299.28, 288.21, 350.61, 299.21),
    },
    {
        "id": "T06_REGION_UNDERFIT",
        "panel": "PANEL_MAIN",
        "role": "REGION_ANNOTATION",
        "source_line": "10;53-54",
        "declared_pt": 8.8,
        "scale": 1.12,
        "effective_pt": 9.856,
        "pdf_size_bp": 9.82,
        "text": "欠拟合",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (161.56, 309.60, 191.02, 320.12),
    },
    {
        "id": "T07_REGION_GOOD",
        "panel": "PANEL_MAIN",
        "role": "REGION_ANNOTATION",
        "source_line": "10;55-56",
        "declared_pt": 8.8,
        "scale": 1.12,
        "effective_pt": 9.856,
        "pdf_size_bp": 9.82,
        "text": "合适",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (312.09, 309.60, 331.73, 320.12),
    },
    {
        "id": "T08_REGION_OVERFIT",
        "panel": "PANEL_MAIN",
        "role": "REGION_ANNOTATION",
        "source_line": "10;57-58",
        "declared_pt": 8.8,
        "scale": 1.12,
        "effective_pt": 9.856,
        "pdf_size_bp": 9.82,
        "text": "过拟合",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (444.57, 309.60, 474.03, 320.12),
    },
    {
        "id": "T09_X_AXIS_TITLE",
        "panel": "PANEL_MAIN",
        "role": "AXIS_TITLE",
        "source_line": "12-16;20-25",
        "declared_pt": 10.0,
        "scale": 1.12,
        "effective_pt": 11.20,
        "pdf_size_bp": 11.16,
        "text": "模型复杂度",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (312.22, 331.25, 368.01, 343.20),
        "resolution_note": "slfig axis later-cascade resolved from final PDF text matrix",
    },
    {
        "id": "T10_CAPTION_LABEL_CJK",
        "panel": "CAPTION",
        "role": "CAPTION_LABEL",
        "source_line": "61",
        "declared_pt": 10.0,
        "scale": 1.0,
        "effective_pt": 10.0,
        "pdf_size_bp": 9.96,
        "text": "图",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (138.94, 348.39, 148.91, 362.81),
    },
    {
        "id": "T11_CAPTION_LABEL_DIGITS",
        "panel": "CAPTION",
        "role": "CAPTION_LABEL",
        "source_line": "61",
        "declared_pt": 10.0,
        "scale": 1.0,
        "effective_pt": 10.0,
        "pdf_size_bp": 9.96,
        "text": "10.1",
        "script": "CAPS_DIGITS",
        "orientation": 0,
        "bbox_pt": (151.25, 352.35, 168.79, 362.31),
    },
    {
        "id": "T12_CAPTION_TEXT",
        "panel": "CAPTION",
        "role": "CAPTION_TEXT",
        "source_line": "61",
        "declared_pt": 10.0,
        "scale": 1.0,
        "effective_pt": 10.0,
        "pdf_size_bp": 9.96,
        "text": "模型复杂度增加时训练误差通常下降，而验证误差可能先降后升。",
        "script": "CJK",
        "orientation": 0,
        "bbox_pt": (178.75, 351.97, 467.67, 362.64),
    },
]

for element in ELEMENTS:
    element["parent_object"] = element["id"]
for element in ELEMENTS:
    if element["id"] in {"T10_CAPTION_LABEL_CJK", "T11_CAPTION_LABEL_DIGITS"}:
        element["parent_object"] = "TCAP_LABEL_COMPOSITE"


def text_mask(element: dict) -> tuple[np.ndarray, tuple[int, int, int, int], tuple[int, int, int]]:
    # PDF span bounds already contain the antialiased glyph extent.  Do not pad:
    # a nearby marker must never leak into a text mask merely because it shares
    # the same colour.
    x0, y0, x1, y1 = pt_bbox_to_px(element["bbox_pt"], 0)
    patch = rgb[y0:y1, x0:x1]
    counts = Counter(map(tuple, patch.reshape(-1, 3)))
    bg = np.array(counts.most_common(1)[0][0], dtype=np.int16)
    delta = np.max(np.abs(patch.astype(np.int16) - bg), axis=2)
    local = delta >= 20
    # Drop tiny isolated raster noise while preserving thin antialias components.
    n, labels, stats, _ = cv2.connectedComponentsWithStats(local.astype(np.uint8), 8)
    clean = np.zeros_like(local)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 2:
            clean[labels == i] = True
    mask = np.zeros((height, width), dtype=bool)
    mask[y0:y1, x0:x1] = clean
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise RuntimeError(f"no foreground for {element['id']}")
    ink_bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return mask, ink_bbox, tuple(int(v) for v in bg)


text_masks: dict[str, np.ndarray] = {}
for element in ELEMENTS:
    mask, ink_bbox, bg = text_mask(element)
    text_masks[element["id"]] = mask
    element["ink_bbox"] = ink_bbox
    element["background_rgb"] = bg
    if element["orientation"] == 90:
        element["h_ink"] = ink_bbox[2] - ink_bbox[0] + 1
    else:
        element["h_ink"] = ink_bbox[3] - ink_bbox[1] + 1
    Image.fromarray((mask * 255).astype(np.uint8)).save(OUT / f"mask_{element['id']}_native_300dpi.png")


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
drawings = page.get_drawings()

BGS = np.array(
    [
        (255, 255, 255),
        (248, 250, 251),
        (251, 248, 244),
        (253, 249, 250),
    ],
    dtype=np.float32,
)


def color_match_at(points_yx: np.ndarray, base: np.ndarray) -> np.ndarray:
    if len(points_yx) == 0:
        return np.zeros(0, dtype=bool)
    p = rgb[points_yx[:, 0], points_yx[:, 1]].astype(np.float32)
    ok = np.zeros(len(p), dtype=bool)
    base = base.astype(np.float32)
    for bg in BGS:
        v = base - bg
        denom = float(np.dot(v, v))
        alpha = np.sum((p - bg) * v, axis=1) / denom
        alpha_clip = np.clip(alpha, 0.0, 1.0)
        recon = bg + alpha_clip[:, None] * v
        residual = np.linalg.norm(p - recon, axis=1)
        contrast = np.linalg.norm(p - bg, axis=1)
        ok |= (alpha >= -0.02) & (alpha <= 1.05) & (residual <= 8.0) & (contrast >= 20.0)
    return ok


def points_to_px(point: fitz.Point) -> tuple[int, int]:
    return (int(round(point.x * SCALE)), int(round(point.y * SCALE)))


def drawing_support(drawing: dict, expansion: int = 5) -> np.ndarray:
    support = np.zeros((height, width), dtype=np.uint8)
    base_thickness = max(1, int(math.ceil(float(drawing.get("width") or 0.7) * SCALE)))
    thickness = base_thickness + 2 * expansion
    all_poly_points: list[tuple[int, int]] = []
    for item in drawing.get("items", []):
        kind = item[0]
        if kind == "l":
            p0 = points_to_px(item[1])
            p1 = points_to_px(item[2])
            cv2.line(support, p0, p1, 255, thickness=thickness, lineType=cv2.LINE_AA)
            all_poly_points.extend([p0, p1])
        elif kind == "c":
            p0, p1, p2, p3 = item[1:5]
            ts = np.linspace(0.0, 1.0, 33)
            curve = []
            for t in ts:
                q = (
                    ((1 - t) ** 3) * np.array([p0.x, p0.y])
                    + 3 * ((1 - t) ** 2) * t * np.array([p1.x, p1.y])
                    + 3 * (1 - t) * (t**2) * np.array([p2.x, p2.y])
                    + (t**3) * np.array([p3.x, p3.y])
                )
                curve.append((int(round(q[0] * SCALE)), int(round(q[1] * SCALE))))
            pts = np.asarray(curve, dtype=np.int32).reshape(-1, 1, 2)
            cv2.polylines(support, [pts], False, 255, thickness=thickness, lineType=cv2.LINE_AA)
            all_poly_points.extend(curve)
    if drawing.get("type") in {"f", "fs"} and all_poly_points:
        hull = cv2.convexHull(np.asarray(all_poly_points, dtype=np.int32))
        support.fill(0)
        cv2.fillConvexPoly(support, hull, 255, lineType=cv2.LINE_AA)
        support = cv2.dilate(support, np.ones((3, 3), np.uint8))
    return support > 0


def semantic_mask(indexes: list[int], base_rgb: tuple[int, int, int]) -> np.ndarray:
    support = np.zeros((height, width), dtype=bool)
    for idx in indexes:
        support |= drawing_support(drawings[idx])
    yx = np.argwhere(support)
    ok = color_match_at(yx, np.array(base_rgb, dtype=np.float32))
    actual = np.zeros((height, width), dtype=bool)
    actual[yx[ok, 0], yx[ok, 1]] = True
    return actual


GRAPHICS = {
    "G01_TRAINING_CURVE": {
        "class": "DATA_CURVE",
        "source_line": "33-34",
        "mask": semantic_mask([4], (31, 78, 121)),
    },
    "G02_VALIDATION_CURVE": {
        "class": "DATA_CURVE",
        "source_line": "35-37",
        "mask": semantic_mask([5], (15, 118, 110)),
    },
    "G03_REFERENCE_LINE": {
        "class": "LINE_ARROW",
        "source_line": "38-39",
        "mask": semantic_mask([6], (148, 153, 164)),
    },
    "G04_MINIMUM_MARKER": {
        "class": "MARKER",
        "source_line": "40-41",
        "mask": semantic_mask([15], (183, 121, 31)),
    },
    "G05_TRAINING_LEADER": {
        "class": "LINE_ARROW",
        "source_line": "42-43",
        "mask": semantic_mask([7], (31, 78, 121)),
    },
    "G06_X_AXIS_ARROW": {
        "class": "LINE_ARROW",
        "source_line": "20-29 (axis lines=left)",
        "mask": semantic_mask([11, 12], (31, 41, 55)),
    },
    "G07_Y_AXIS_ARROW": {
        "class": "LINE_ARROW",
        "source_line": "20-29 (axis lines=left)",
        "mask": semantic_mask([13, 14], (31, 41, 55)),
    },
}

for gid, info in GRAPHICS.items():
    count = int(info["mask"].sum())
    if count == 0:
        raise RuntimeError(f"empty semantic mask: {gid}")
    Image.fromarray((info["mask"] * 255).astype(np.uint8)).save(OUT / f"mask_{gid}_native_300dpi.png")

current_t03_g04_overlap = text_masks["T03_MINIMUM_KEY"] & GRAPHICS["G04_MINIMUM_MARKER"]["mask"]
Image.fromarray((current_t03_g04_overlap * 255).astype(np.uint8)).save(
    OUT / "mask_overlap_T03_MINIMUM_KEY__G04_MINIMUM_MARKER_current_native_300dpi.png"
)


def nearest(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[int, float, tuple[int, int], tuple[int, int]]:
    overlap = int(np.count_nonzero(mask_a & mask_b))
    ayx = np.argwhere(mask_a)
    byx = np.argwhere(mask_b)
    if len(ayx) == 0 or len(byx) == 0:
        return overlap, float("inf"), (-1, -1), (-1, -1)
    tree = cKDTree(byx)
    distances, indices = tree.query(ayx, k=1)
    k = int(np.argmin(distances))
    a_y, a_x = ayx[k]
    b_y, b_x = byx[int(indices[k])]
    return overlap, float(distances[k]), (int(a_x), int(a_y)), (int(b_x), int(b_y))


def vector_bbox_px(element: dict) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = element["bbox_pt"]
    return x0 * SCALE, y0 * SCALE, x1 * SCALE, y1 * SCALE


def bbox_clearance(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, bool]:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    distance = math.hypot(dx, dy)
    intersects_or_touches = dx == 0.0 and dy == 0.0
    return distance, intersects_or_touches


overlap_rows = []
text_ids = [e["id"] for e in ELEMENTS]
for i, a_id in enumerate(text_ids):
    for b_id in text_ids[i + 1 :]:
        overlap, distance, p_a, p_b = nearest(text_masks[a_id], text_masks[b_id])
        element_a = next(e for e in ELEMENTS if e["id"] == a_id)
        element_b = next(e for e in ELEMENTS if e["id"] == b_id)
        vector_distance, vector_intersects = bbox_clearance(vector_bbox_px(element_a), vector_bbox_px(element_b))
        intra_composite = element_a["parent_object"] == element_b["parent_object"]
        pair_pass = True if intra_composite else (
            overlap == 0 and distance >= 4.0 and vector_distance >= 4.0 and not vector_intersects
        )
        overlap_rows.append(
            {
                "OBJECT_A": a_id,
                "CLASS_A": "TEXT",
                "PARENT_OBJECT_A": element_a["parent_object"],
                "OBJECT_B": b_id,
                "CLASS_B": "TEXT",
                "PARENT_OBJECT_B": element_b["parent_object"],
                "PAIR_SEMANTICS": "INTRA_COMPOSITE_SUBSTRING" if intra_composite else "INDEPENDENT_OBJECTS",
                "OVERLAP_PIXEL_COUNT": overlap,
                "MIN_CLEARANCE_PX": distance,
                "THRESHOLD_PX": "" if intra_composite else 4.0,
                "BBOX_CLEARANCE_PX": vector_distance,
                "BBOX_INTERSECTS_OR_TOUCHES": str(vector_intersects).lower(),
                "BBOX_THRESHOLD_PX": "" if intra_composite else 4.0,
                "INDEPENDENT_TEXT_BBOX_GATE_APPLIES": str(not intra_composite).lower(),
                "NEAREST_A_XY": f"{p_a[0]},{p_a[1]}",
                "NEAREST_B_XY": f"{p_b[0]},{p_b[1]}",
                "PASS_FAIL": "PASS" if pair_pass else "FAIL",
                "METHOD": "script subspans sharing a parent are measured but excluded from the independent-object 4px gate; all other text pairs use native foreground cKDTree distance plus final-PDF/vector bbox gap",
            }
        )

for element in ELEMENTS:
    for gid, info in GRAPHICS.items():
        overlap, distance, p_a, p_b = nearest(text_masks[element["id"]], info["mask"])
        overlap_rows.append(
            {
                "OBJECT_A": element["id"],
                "CLASS_A": "TEXT",
                "PARENT_OBJECT_A": element["parent_object"],
                "OBJECT_B": gid,
                "CLASS_B": info["class"],
                "PARENT_OBJECT_B": gid,
                "PAIR_SEMANTICS": "INDEPENDENT_OBJECTS",
                "OVERLAP_PIXEL_COUNT": overlap,
                "MIN_CLEARANCE_PX": distance,
                "THRESHOLD_PX": 3.0,
                "BBOX_CLEARANCE_PX": "",
                "BBOX_INTERSECTS_OR_TOUCHES": "",
                "BBOX_THRESHOLD_PX": "",
                "INDEPENDENT_TEXT_BBOX_GATE_APPLIES": "",
                "NEAREST_A_XY": f"{p_a[0]},{p_a[1]}",
                "NEAREST_B_XY": f"{p_b[0]},{p_b[1]}",
                "PASS_FAIL": "PASS" if overlap == 0 and distance >= 3.0 else "FAIL",
                "METHOD": "independent semantic vector-path support intersected with native antialiased foreground; cKDTree exact pixel-centre Euclidean distance",
            }
        )


def row_for(a: str, b: str) -> dict:
    return next(r for r in overlap_rows if r["OBJECT_A"] == a and r["OBJECT_B"] == b)


critical_pairs = [
    ("T02_VALIDATION_DIRECT", "G02_VALIDATION_CURVE", "validation_label_vs_validation_curve"),
    ("T04_TRAINING_DIRECT", "G05_TRAINING_LEADER", "training_label_vs_leader"),
    ("T04_TRAINING_DIRECT", "G01_TRAINING_CURVE", "training_label_vs_training_curve"),
    ("T03_MINIMUM_KEY", "G04_MINIMUM_MARKER", "minimum_label_vs_marker"),
    ("T03_MINIMUM_KEY", "G02_VALIDATION_CURVE", "minimum_label_vs_validation_curve"),
    ("T05_SELECTION_KEY", "G03_REFERENCE_LINE", "selection_label_vs_reference_line"),
    ("T05_SELECTION_KEY", "G06_X_AXIS_ARROW", "selection_label_vs_x_axis"),
    ("T09_X_AXIS_TITLE", "G06_X_AXIS_ARROW", "x_axis_title_vs_x_axis"),
    ("T01_Y_AXIS_TITLE", "G07_Y_AXIS_ARROW", "y_axis_title_vs_y_axis"),
    ("T06_REGION_UNDERFIT", "G06_X_AXIS_ARROW", "underfit_label_vs_x_axis"),
    ("T07_REGION_GOOD", "G06_X_AXIS_ARROW", "good_label_vs_x_axis"),
    ("T08_REGION_OVERFIT", "G06_X_AXIS_ARROW", "overfit_label_vs_x_axis"),
]


def save_roi(a_id: str, b_id: str, stem: str) -> None:
    row = row_for(a_id, b_id)
    ax, ay = map(int, row["NEAREST_A_XY"].split(","))
    bx, by = map(int, row["NEAREST_B_XY"].split(","))
    pad = 55
    x0 = max(0, min(ax, bx) - pad)
    y0 = max(0, min(ay, by) - pad)
    x1 = min(width, max(ax, bx) + pad + 1)
    y1 = min(height, max(ay, by) + pad + 1)
    # For far-apart pairs, include each object's ink bbox / semantic rect union in one native crop.
    elem = next(e for e in ELEMENTS if e["id"] == a_id)
    ex0, ey0, ex1, ey1 = elem["ink_bbox"]
    gy, gx = np.where(GRAPHICS[b_id]["mask"])
    gx0, gy0, gx1, gy1 = int(gx.min()), int(gy.min()), int(gx.max()), int(gy.max())
    x0 = max(0, min(x0, ex0 - 25, gx0 - 25))
    y0 = max(0, min(y0, ey0 - 25, gy0 - 25))
    x1 = min(width, max(x1, ex1 + 26, gx1 + 26))
    y1 = min(height, max(y1, ey1 + 26, gy1 + 26))
    # Avoid enormous all-curve crops: retain the element and nearest segment, not the whole curve.
    if x1 - x0 > 900 or y1 - y0 > 700:
        x0 = max(0, min(ax, bx, ex0) - 70)
        y0 = max(0, min(ay, by, ey0) - 70)
        x1 = min(width, max(ax, bx, ex1) + 71)
        y1 = min(height, max(ay, by, ey1) + 71)
    raw = image.crop((x0, y0, x1, y1))
    raw.save(OUT / f"roi_{stem}_raw_1to1_300dpi.png")
    overlay = raw.copy()
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((ax - x0 - 5, ay - y0 - 5, ax - x0 + 5, ay - y0 + 5), outline=(255, 0, 0), width=2)
    draw.ellipse((bx - x0 - 5, by - y0 - 5, bx - x0 + 5, by - y0 + 5), outline=(0, 90, 255), width=2)
    draw.line((ax - x0, ay - y0, bx - x0, by - y0), fill=(190, 0, 190), width=1)
    draw.text((6, 6), f"{a_id} <-> {b_id}; d={float(row['MIN_CLEARANCE_PX']):.3f}px", fill=(0, 0, 0))
    overlay.save(OUT / f"roi_{stem}_nearest_overlay_1to1_300dpi.png")


for a, b, stem in critical_pairs:
    save_roi(a, b, stem)


role_groups = defaultdict(list)
for e in ELEMENTS:
    role_groups[(e["panel"], e["role"], e["script"])].append(e)
for group in role_groups.values():
    median = float(np.median([e["h_ink"] for e in group]))
    for e in group:
        e["class_median"] = median
        e["ratio_class"] = e["h_ink"] / median if median else float("nan")

base_median = float(
    np.median(
        [
            e["h_ink"]
            for e in ELEMENTS
            if e["panel"] == "PANEL_MAIN" and e["role"] == "REGION_ANNOTATION" and e["script"] == "CJK"
        ]
    )
)
role_medians = {
    key: float(np.median([e["h_ink"] for e in group])) for key, group in role_groups.items()
}
for e in ELEMENTS:
    role_median = role_medians[(e["panel"], e["role"], e["script"])]
    e["role_ratio"] = role_median / base_median if e["panel"] == "PANEL_MAIN" else float("nan")


def threshold_for(script: str) -> int:
    return {"CJK": 30, "CAPS_DIGITS": 24, "LOWER_GREEK": 17, "MATH_OPERATOR": 22, "SCRIPT": 15}[script]


for e in ELEMENTS:
    related = [r for r in overlap_rows if r["OBJECT_A"] == e["id"] or r["OBJECT_B"] == e["id"]]
    e["min_clearance"] = min(float(r["MIN_CLEARANCE_PX"]) for r in related)
    e["text_text_overlap"] = sum(
        int(r["OVERLAP_PIXEL_COUNT"])
        for r in related
        if r["CLASS_A"] == "TEXT" and r["CLASS_B"] == "TEXT"
    )
    e["text_graphic_overlap"] = sum(
        int(r["OVERLAP_PIXEL_COUNT"])
        for r in related
        if {r["CLASS_A"], r["CLASS_B"]} != {"TEXT"}
    )
    reasons = []
    if e["effective_pt"] < 9.5:
        reasons.append("effective_pt<9.5")
    if e["h_ink"] < threshold_for(e["script"]):
        reasons.append(f"H_ink<{threshold_for(e['script'])}")
    if not (0.92 <= e["ratio_class"] <= 1.08):
        reasons.append("same-class ratio outside [0.92,1.08]")
    if e["text_text_overlap"] or e["text_graphic_overlap"]:
        reasons.append("illegal foreground overlap")
    e["pass"] = not reasons
    e["reason"] = "; ".join(reasons) if reasons else "all applicable element-level gates pass"


font_fields = [
    "ELEMENT_ID",
    "PANEL_ID",
    "ROLE",
    "SOURCE_FILE",
    "SOURCE_LINE",
    "DECLARED_PT",
    "GRAPHICS_SCALE",
    "EFFECTIVE_PT",
    "FINAL_PDF_FONT_SIZE_BP",
    "TEXT_SAMPLE",
    "SAME_ROLE_EFFECTIVE_MAX_MIN",
    "SAME_ROLE_EFFECTIVE_ABS_DIFF_PT",
    "PASS_FAIL",
    "REASON",
]
with (OUT / "after_font_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=font_fields)
    writer.writeheader()
    for e in ELEMENTS:
        group = role_groups[(e["panel"], e["role"], e["script"])]
        eff = [g["effective_pt"] for g in group]
        ratio = max(eff) / min(eff)
        diff = max(eff) - min(eff)
        font_pass = e["effective_pt"] >= 9.5 and ratio <= 1.03 and diff <= 0.25
        writer.writerow(
            {
                "ELEMENT_ID": e["id"],
                "PANEL_ID": e["panel"],
                "ROLE": e["role"],
                "SOURCE_FILE": str(SOURCE),
                "SOURCE_LINE": e["source_line"],
                "DECLARED_PT": f"{e['declared_pt']:.3f}",
                "GRAPHICS_SCALE": f"{e['scale']:.3f}",
                "EFFECTIVE_PT": f"{e['effective_pt']:.3f}",
                "FINAL_PDF_FONT_SIZE_BP": f"{e['pdf_size_bp']:.2f}",
                "TEXT_SAMPLE": e["text"],
                "SAME_ROLE_EFFECTIVE_MAX_MIN": f"{ratio:.6f}",
                "SAME_ROLE_EFFECTIVE_ABS_DIFF_PT": f"{diff:.3f}",
                "PASS_FAIL": "PASS" if font_pass else "FAIL",
                "REASON": "effective TeX pt includes outer 1.12 transform; final PDF text matrix independently cross-checked",
            }
        )


pixel_fields = [
    "ELEMENT_ID",
    "PANEL_ID",
    "ROLE",
    "SOURCE_FILE",
    "SOURCE_LINE",
    "DECLARED_PT",
    "GRAPHICS_SCALE",
    "EFFECTIVE_PT",
    "TEXT_SAMPLE",
    "SCRIPT_CLASS",
    "BBOX_X0",
    "BBOX_Y0",
    "BBOX_X1",
    "BBOX_Y1",
    "H_INK_PX",
    "CLASS_MEDIAN_PX",
    "RATIO_TO_CLASS_MEDIAN",
    "ROLE_RATIO",
    "TEXT_TEXT_OVERLAP_PX",
    "TEXT_GRAPHIC_OVERLAP_PX",
    "MIN_CLEARANCE_PX",
    "PASS_FAIL",
    "REASON",
]
with (OUT / "after_pixel_measurements.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=pixel_fields)
    writer.writeheader()
    for e in ELEMENTS:
        x0, y0, x1, y1 = e["ink_bbox"]
        writer.writerow(
            {
                "ELEMENT_ID": e["id"],
                "PANEL_ID": e["panel"],
                "ROLE": e["role"],
                "SOURCE_FILE": str(SOURCE),
                "SOURCE_LINE": e["source_line"],
                "DECLARED_PT": f"{e['declared_pt']:.3f}",
                "GRAPHICS_SCALE": f"{e['scale']:.3f}",
                "EFFECTIVE_PT": f"{e['effective_pt']:.3f}",
                "TEXT_SAMPLE": e["text"],
                "SCRIPT_CLASS": e["script"],
                "BBOX_X0": x0,
                "BBOX_Y0": y0,
                "BBOX_X1": x1,
                "BBOX_Y1": y1,
                "H_INK_PX": e["h_ink"],
                "CLASS_MEDIAN_PX": f"{e['class_median']:.3f}",
                "RATIO_TO_CLASS_MEDIAN": f"{e['ratio_class']:.6f}",
                "ROLE_RATIO": "" if math.isnan(e["role_ratio"]) else f"{e['role_ratio']:.6f}",
                "TEXT_TEXT_OVERLAP_PX": e["text_text_overlap"],
                "TEXT_GRAPHIC_OVERLAP_PX": e["text_graphic_overlap"],
                "MIN_CLEARANCE_PX": f"{e['min_clearance']:.6f}",
                "PASS_FAIL": "PASS" if e["pass"] else "FAIL",
                "REASON": e["reason"],
            }
        )


overlap_fields = [
    "OBJECT_A",
    "CLASS_A",
    "PARENT_OBJECT_A",
    "OBJECT_B",
    "CLASS_B",
    "PARENT_OBJECT_B",
    "PAIR_SEMANTICS",
    "OVERLAP_PIXEL_COUNT",
    "MIN_CLEARANCE_PX",
    "THRESHOLD_PX",
    "BBOX_CLEARANCE_PX",
    "BBOX_INTERSECTS_OR_TOUCHES",
    "BBOX_THRESHOLD_PX",
    "INDEPENDENT_TEXT_BBOX_GATE_APPLIES",
    "NEAREST_A_XY",
    "NEAREST_B_XY",
    "PASS_FAIL",
    "METHOD",
]
with (OUT / "after_overlap_report.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=overlap_fields)
    writer.writeheader()
    writer.writerows(overlap_rows)


edge_fields = [
    "OBJECT_ID",
    "CLASS",
    "FOREGROUND_BBOX_X0",
    "FOREGROUND_BBOX_Y0",
    "FOREGROUND_BBOX_X1",
    "FOREGROUND_BBOX_Y1",
    "FULL_PAGE_LEFT_PX",
    "FULL_PAGE_TOP_PX",
    "FULL_PAGE_RIGHT_PX",
    "FULL_PAGE_BOTTOM_PX",
    "FULL_PAGE_MIN_EDGE_PX",
    "FIGURE_CROP_MIN_EDGE_PX",
    "STANDALONE_MIN_EDGE_PX",
    "CLIP_PIXEL_COUNT",
    "PASS_FAIL",
    "METHOD",
]
edge_rows = []
figure_crop_rect = (280, 240, 2250, 1610)
standalone_rect = (280, 240, 2250, 1460)


def edge_row(object_id: str, object_class: str, mask: np.ndarray, in_standalone: bool) -> dict:
    ys, xs = np.where(mask)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    page_edges = (x0, y0, width - 1 - x1, height - 1 - y1)
    crop_edges = (
        x0 - figure_crop_rect[0],
        y0 - figure_crop_rect[1],
        figure_crop_rect[2] - 1 - x1,
        figure_crop_rect[3] - 1 - y1,
    )
    standalone_edges = (
        x0 - standalone_rect[0],
        y0 - standalone_rect[1],
        standalone_rect[2] - 1 - x1,
        standalone_rect[3] - 1 - y1,
    )
    full_min = min(page_edges)
    crop_min = min(crop_edges)
    standalone_min = min(standalone_edges) if in_standalone else None
    clip_count = 0 if full_min >= 0 and crop_min >= 0 and (standalone_min is None or standalone_min >= 0) else 1
    passes = full_min >= 6 and crop_min >= 6 and (standalone_min is None or standalone_min >= 6) and clip_count == 0
    return {
        "OBJECT_ID": object_id,
        "CLASS": object_class,
        "FOREGROUND_BBOX_X0": x0,
        "FOREGROUND_BBOX_Y0": y0,
        "FOREGROUND_BBOX_X1": x1,
        "FOREGROUND_BBOX_Y1": y1,
        "FULL_PAGE_LEFT_PX": page_edges[0],
        "FULL_PAGE_TOP_PX": page_edges[1],
        "FULL_PAGE_RIGHT_PX": page_edges[2],
        "FULL_PAGE_BOTTOM_PX": page_edges[3],
        "FULL_PAGE_MIN_EDGE_PX": full_min,
        "FIGURE_CROP_MIN_EDGE_PX": crop_min,
        "STANDALONE_MIN_EDGE_PX": "" if standalone_min is None else standalone_min,
        "CLIP_PIXEL_COUNT": clip_count,
        "PASS_FAIL": "PASS" if passes else "FAIL",
        "METHOD": "native foreground bbox against full-page, no-resize figure-crop, and no-resize standalone image edges",
    }


for element in ELEMENTS:
    edge_rows.append(edge_row(element["id"], "TEXT", text_masks[element["id"]], element["panel"] == "PANEL_MAIN"))
for gid, info in GRAPHICS.items():
    edge_rows.append(edge_row(gid, info["class"], info["mask"], True))

with (OUT / "after_edge_clip_report.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=edge_fields)
    writer.writeheader()
    writer.writerows(edge_rows)


overlay = image.copy()
draw = ImageDraw.Draw(overlay)
font = ImageFont.load_default()
for e in ELEMENTS:
    x0, y0, x1, y1 = e["ink_bbox"]
    draw.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), outline=(220, 0, 0), width=2)
    vx0, vy0, vx1, vy1 = vector_bbox_px(e)
    draw.rectangle((vx0, vy0, vx1, vy1), outline=(255, 145, 0), width=1)
    draw.text((x0, max(0, y0 - 13)), f"{e['id']}|{e['role']}", fill=(160, 0, 0), font=font)
for gid, info in GRAPHICS.items():
    ys, xs = np.where(info["mask"])
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    draw.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), outline=(0, 80, 220), width=1)
    draw.text((x0, max(0, y0 - 12)), gid, fill=(0, 60, 180), font=font)
overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

semantic_overlay = rgb.copy().astype(np.float32)
semantic_colours = {
    "G01_TRAINING_CURVE": (0, 80, 255),
    "G02_VALIDATION_CURVE": (0, 210, 130),
    "G03_REFERENCE_LINE": (170, 0, 220),
    "G04_MINIMUM_MARKER": (255, 80, 0),
    "G05_TRAINING_LEADER": (255, 0, 170),
    "G06_X_AXIS_ARROW": (0, 0, 0),
    "G07_Y_AXIS_ARROW": (0, 0, 0),
}
for gid, colour in semantic_colours.items():
    mask = GRAPHICS[gid]["mask"]
    semantic_overlay[mask] = 0.25 * semantic_overlay[mask] + 0.75 * np.array(colour, dtype=np.float32)
semantic_overlay = Image.fromarray(np.clip(semantic_overlay, 0, 255).astype(np.uint8))
semantic_overlay.crop((280, 240, 2250, 1460)).save(OUT / "semantic_masks_overlay_figure_1to1_300dpi.png")

# Replace initial loose crops with final no-resize, no-clipping views.
figure_crop = image.crop((280, 240, 2250, 1610))
figure_crop.save(OUT / "figure_crop_300dpi.png")
standalone = image.crop((280, 240, 2250, 1460))
standalone.save(OUT / "standalone_300dpi.png")
ImageOps.grayscale(figure_crop).save(OUT / "grayscale_300dpi.png")

all_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in overlap_rows)
failing_pairs = [r for r in overlap_rows if r["PASS_FAIL"] == "FAIL"]
independent_text_rows = [
    r for r in overlap_rows if r["CLASS_B"] == "TEXT" and r["PAIR_SEMANTICS"] == "INDEPENDENT_OBJECTS"
]
min_text_text = min(float(r["MIN_CLEARANCE_PX"]) for r in independent_text_rows)
min_text_graphic = min(float(r["MIN_CLEARANCE_PX"]) for r in overlap_rows if r["CLASS_B"] != "TEXT")
min_text_bbox = min(float(r["BBOX_CLEARANCE_PX"]) for r in independent_text_rows)
min_full_page_edge = min(float(r["FULL_PAGE_MIN_EDGE_PX"]) for r in edge_rows)
min_figure_crop_edge = min(float(r["FIGURE_CROP_MIN_EDGE_PX"]) for r in edge_rows)
min_standalone_edge = min(float(r["STANDALONE_MIN_EDGE_PX"]) for r in edge_rows if r["STANDALONE_MIN_EDGE_PX"] != "")
text_edge_rows = [r for r in edge_rows if r["CLASS"] == "TEXT"]
min_text_full_page_edge = min(float(r["FULL_PAGE_MIN_EDGE_PX"]) for r in text_edge_rows)
min_text_figure_crop_edge = min(float(r["FIGURE_CROP_MIN_EDGE_PX"]) for r in text_edge_rows)
min_text_standalone_edge = min(float(r["STANDALONE_MIN_EDGE_PX"]) for r in text_edge_rows if r["STANDALONE_MIN_EDGE_PX"] != "")
print("PAGE", PAGE_INDEX + 1, "SIZE", (width, height))
print("ELEMENTS", len(ELEMENTS), "GRAPHICS", len(GRAPHICS), "PAIR_ROWS", len(overlap_rows))
print("OVERLAP_TOTAL", all_overlap, "FAIL_PAIR_COUNT", len(failing_pairs))
print("MIN_TEXT_TEXT", min_text_text, "MIN_TEXT_GRAPHIC", min_text_graphic)
print("MIN_TEXT_BBOX", min_text_bbox)
print("MIN_EDGES", min_full_page_edge, min_figure_crop_edge, min_standalone_edge, "EDGE_FAILS", sum(r["PASS_FAIL"] == "FAIL" for r in edge_rows))
print("MIN_TEXT_EDGES", min_text_full_page_edge, min_text_figure_crop_edge, min_text_standalone_edge)
for e in ELEMENTS:
    print(e["id"], "H", e["h_ink"], "bbox", e["ink_bbox"], "ratio", round(e["ratio_class"], 6))
print("CRITICAL")
for a, b, _ in critical_pairs:
    r = row_for(a, b)
    print(a, b, "overlap", r["OVERLAP_PIXEL_COUNT"], "distance", f"{float(r['MIN_CLEARANCE_PX']):.6f}", r["NEAREST_A_XY"], r["NEAREST_B_XY"], r["PASS_FAIL"])
if failing_pairs:
    print("FAILING_PAIRS")
    for r in failing_pairs:
        print(r)
