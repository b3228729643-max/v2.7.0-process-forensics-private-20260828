from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R18_SA1_FRESH_ISOLATED_R116_20260828")
OUTPUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_R116_20260828")

CASES = [
    {
        "id": "x0",
        "input": "ROI-10_x0_outer_contour_clearance_native1x.png",
        "target_bbox": [17, 31, 86, 72],
        "shift_px": [17, 0],
        "source_delta": "xshift=4pt",
        "inner_sep_pt": 0.8,
        "protected_regions": {
            "q0_marker_and_vertical_update": [0, 72, 16, 105],
        },
    },
    {
        "id": "digit5",
        "input": "ROI-13_step5_contour_contact_native1x.png",
        "target_bbox": [59, 55, 78, 85],
        "shift_px": [-17, 0],
        "source_delta": "xshift=-2pt -> -6pt",
        "inner_sep_pt": 0.8,
        "protected_regions": {
            "incoming_vertical_update": [0, 0, 22, 43],
            "outgoing_horizontal_update": [20, 20, 100, 36],
            "q5_marker": [87, 55, 100, 85],
            "x_axis": [0, 98, 100, 105],
            "label7_region": [78, 86, 100, 105],
        },
    },
]


def min_distance(a: np.ndarray, b: np.ndarray) -> float | None:
    ayx = np.argwhere(a)
    byx = np.argwhere(b)
    if len(ayx) == 0 or len(byx) == 0:
        return None
    best = float("inf")
    for start in range(0, len(ayx), 128):
        chunk = ayx[start : start + 128]
        delta = chunk[:, None, :] - byx[None, :, :]
        d2 = np.sum(delta * delta, axis=2)
        best = min(best, float(np.min(d2)))
    return float(best**0.5)


def rectangle_gap(a: list[int], b: list[int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return float((dx * dx + dy * dy) ** 0.5)


def rectangle_overlap_area(a: list[int], b: list[int]) -> int:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return max(0, min(ax1, bx1) - max(ax0, bx0)) * max(0, min(ay1, by1) - max(ay0, by0))


def project(case: dict) -> dict:
    image = Image.open(SOURCE / case["input"]).convert("RGB")
    rgb = np.asarray(image)
    h, w, _ = rgb.shape
    x0, y0, x1, y1 = case["target_bbox"]
    dx, dy = case["shift_px"]

    neutral = (np.max(rgb, axis=2) - np.min(rgb, axis=2)) <= 12
    dark = neutral & (np.max(rgb, axis=2) < 125)
    neutral_ink = neutral & (np.min(rgb, axis=2) < 248)
    colored = (~neutral) & (np.min(rgb, axis=2) < 245)

    target = np.zeros((h, w), dtype=bool)
    target_region = np.zeros((h, w), dtype=bool)
    target_region[y0:y1, x0:x1] = True
    target[y0:y1, x0:x1] = dark[y0:y1, x0:x1]
    shifted = np.zeros_like(target)
    sy, sx = np.nonzero(target)
    nx = sx + dx
    ny = sy + dy
    keep = (nx >= 0) & (nx < w) & (ny >= 0) & (ny < h)
    shifted[ny[keep], nx[keep]] = True

    sep_px = int(np.ceil(case["inner_sep_pt"] * 300.0 / 72.0))
    target_points = np.argwhere(shifted)
    if len(target_points) == 0:
        raise RuntimeError(f"empty target mask: {case['id']}")
    min_y, min_x = target_points.min(axis=0)
    max_y, max_x = target_points.max(axis=0)
    bx0 = max(0, int(min_x) - sep_px)
    by0 = max(0, int(min_y) - sep_px)
    bx1 = min(w, int(max_x) + sep_px + 1)
    by1 = min(h, int(max_y) + sep_px + 1)
    background = np.zeros((h, w), dtype=bool)
    background[by0:by1, bx0:bx1] = True

    obstacle = (neutral_ink | colored) & ~target
    protected_colored = colored & ~target_region
    colored_erased = int(np.count_nonzero(protected_colored & background))
    neutral_erased = int(np.count_nonzero(neutral_ink & ~target & background))
    visible_obstacles = obstacle & ~background
    clearance = min_distance(shifted, visible_obstacles)
    background_bbox = [bx0, by0, bx1, by1]
    protected_gaps = {
        name: rectangle_gap(background_bbox, box)
        for name, box in case["protected_regions"].items()
    }
    protected_overlap = {
        name: rectangle_overlap_area(background_bbox, box)
        for name, box in case["protected_regions"].items()
    }

    canvas = np.full_like(rgb, 255)
    canvas[obstacle] = rgb[obstacle]
    canvas[background] = np.array([255, 250, 210], dtype=np.uint8)
    canvas[shifted] = np.array([20, 20, 20], dtype=np.uint8)
    projected = Image.fromarray(canvas)
    draw = ImageDraw.Draw(projected)
    draw.rectangle([bx0, by0, bx1 - 1, by1 - 1], outline=(210, 90, 0), width=1)
    native_path = OUTPUT / f"STATIC_{case['id']}_projection_native1x.png"
    nearest_path = OUTPUT / f"STATIC_{case['id']}_projection_nearest8x.png"
    projected.save(native_path)
    projected.resize((w * 8, h * 8), Image.Resampling.NEAREST).save(nearest_path)

    return {
        "id": case["id"],
        "source_roi": str(SOURCE / case["input"]),
        "roi_size_px": [w, h],
        "target_bbox_current_xyxy": case["target_bbox"],
        "shift_px_300dpi": case["shift_px"],
        "source_delta": case["source_delta"],
        "inner_sep_pt": case["inner_sep_pt"],
        "inner_sep_px_300dpi_ceiling": sep_px,
        "projected_background_bbox_xyxy": background_bbox,
        "target_ink_pixels": int(np.count_nonzero(shifted)),
        "allowed_neutral_contour_antialias_pixels_under_background": neutral_erased,
        "unclassified_color_like_antialias_pixels_under_background": colored_erased,
        "protected_region_bboxes_xyxy": case["protected_regions"],
        "projected_background_to_protected_region_gap_px": protected_gaps,
        "projected_background_protected_region_overlap_area_px": protected_overlap,
        "minimum_target_ink_to_remaining_visible_obstacle_px": clearance,
        "native_projection": native_path.name,
        "nearest8x_projection": nearest_path.name,
    }


results = [project(case) for case in CASES]
(OUTPUT / "STATIC_PROJECTION.json").write_text(
    json.dumps({"schema": "P126_R19_STATIC_PROJECTION_V1", "results": results}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(results, ensure_ascii=False))
