from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828")
REVIEW = ROOT / "review"
IMAGE = np.asarray(Image.open(REVIEW / "full_page_300.png").convert("RGB"))


def read_boxes() -> dict[str, tuple[int, int, int, int]]:
    result = {}
    with (REVIEW / "OBJECT_CATALOG_MACHINE.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            result[row["OBJECT_ID"]] = tuple(int(row[key]) for key in ("X0_PX", "TOP_PX", "X1_PX", "BOTTOM_PX"))
    return result


def points(box: tuple[int, int, int, int], selector) -> np.ndarray:
    x0, y0, x1, y1 = box
    tile = IMAGE[y0:y1+1, x0:x1+1]
    mask = selector(tile)
    ys, xs = np.nonzero(mask)
    return np.column_stack((xs + x0, ys + y0))


def min_gap(a: np.ndarray, b: np.ndarray) -> dict:
    if len(a) == 0 or len(b) == 0:
        return {"point_count_a": int(len(a)), "point_count_b": int(len(b)), "minimum_center_distance_px": None, "blank_gap_px": None, "shared_pixels": 0}
    shared = len(set(map(tuple, a)).intersection(map(tuple, b)))
    best = math.inf
    for chunk_start in range(0, len(a), 256):
        chunk = a[chunk_start:chunk_start+256]
        delta = chunk[:, None, :] - b[None, :, :]
        value = float(np.sqrt(np.min(np.sum(delta * delta, axis=2))))
        best = min(best, value)
    return {
        "point_count_a": int(len(a)),
        "point_count_b": int(len(b)),
        "minimum_center_distance_px": round(best, 6),
        "blank_gap_px": max(0, int(math.ceil(best)) - 1),
        "shared_pixels": int(shared),
    }


def dark(tile: np.ndarray) -> np.ndarray:
    return np.max(tile, axis=2) <= 105


def blue(tile: np.ndarray) -> np.ndarray:
    r, g, b = tile[..., 0], tile[..., 1], tile[..., 2]
    return (b.astype(int)-r.astype(int) >= 45) & (b.astype(int)-g.astype(int) >= 20) & (g.astype(int)-r.astype(int) >= 20) & (b <= 190)


def teal(tile: np.ndarray) -> np.ndarray:
    r, g, b = tile[..., 0], tile[..., 1], tile[..., 2]
    return (g.astype(int)-r.astype(int) >= 45) & (b.astype(int)-r.astype(int) >= 38) & (np.abs(g.astype(int)-b.astype(int)) <= 45) & (g <= 190)


def gray(tile: np.ndarray) -> np.ndarray:
    spread = np.max(tile, axis=2).astype(int) - np.min(tile, axis=2).astype(int)
    mean = np.mean(tile, axis=2)
    return (spread <= 18) & (mean >= 125) & (mean <= 215)


def color_summary(box: tuple[int, int, int, int], selector) -> dict:
    x0, y0, x1, y1 = box
    tile = IMAGE[y0:y1, x0:x1]
    mask = selector(tile)
    selected = tile[mask]
    return {
        "selected_pixels": int(len(selected)),
        "mean_rgb": [round(float(v), 3) for v in selected.mean(axis=0)] if len(selected) else None,
        "median_rgb": [int(v) for v in np.median(selected, axis=0)] if len(selected) else None,
    }


def expanded(box: tuple[int, int, int, int], pad: int) -> tuple[int, int, int, int]:
    return (max(0, box[0]-pad), max(0, box[1]-pad), min(IMAGE.shape[1]-1, box[2]+pad), min(IMAGE.shape[0]-1, box[3]+pad))


def main() -> None:
    boxes = read_boxes()
    digit6 = points(boxes["O039"], dark)
    digit7 = points(boxes["O040"], dark)
    digit4 = points(boxes["O037"], dark)
    digit5 = points(boxes["O038"], dark)
    q6_blue = points(expanded(boxes["O027"], 2), blue)
    q7_teal = points(expanded(boxes["O060"], 2), teal)
    local6_gray = points(expanded(boxes["O039"], 22), gray)
    local7_gray = points(expanded(boxes["O040"], 22), gray)
    local7_axis = points(expanded(boxes["O040"], 22), dark)
    local7_axis = np.array([p for p in local7_axis if p[1] >= boxes["O040"][3]], dtype=int)

    audit = {
        "schema": "P126_R17_PIXEL_AUDIT_V1",
        "legend": {
            "x1_color": color_summary((1020, 960, 1120, 975), blue),
            "x2_color": color_summary((1245, 960, 1350, 975), teal),
            "runs": json.loads((REVIEW / "LEGEND_PIXEL_RUNS.json").read_text(encoding="utf-8")),
        },
        "critical_clearances": {
            "digit6_to_q6_blue_marker": min_gap(digit6, q6_blue),
            "digit6_to_digit4": min_gap(digit6, digit4),
            "digit6_to_local_gray_contour_pixels": min_gap(digit6, local6_gray),
            "digit7_to_q7_teal_marker": min_gap(digit7, q7_teal),
            "digit7_to_digit5": min_gap(digit7, digit5),
            "digit7_to_local_gray_contour_pixels": min_gap(digit7, local7_gray),
            "digit7_to_x_axis_ink_below": min_gap(digit7, local7_axis),
        },
    }
    (REVIEW / "PIXEL_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
