from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt


HERE = Path(__file__).resolve().parent
R92 = HERE.parent / "STRICT_R3_SA1_R92"


def load_mask(name: str) -> np.ndarray:
    image = np.asarray(Image.open(R92 / "masks" / name).convert("L"))
    return image > 0


def nearest_pair(mask_a: np.ndarray, mask_b: np.ndarray):
    intersection = np.logical_and(mask_a, mask_b)
    if intersection.any():
        y, x = np.argwhere(intersection)[0]
        return int(intersection.sum()), (int(x), int(y)), (int(x), int(y))
    distances, nearest = distance_transform_edt(~mask_a, return_indices=True)
    ys, xs = np.where(mask_b)
    index = int(np.argmin(distances[ys, xs]))
    by, bx = int(ys[index]), int(xs[index])
    ay, ax = int(nearest[0, by, bx]), int(nearest[1, by, bx])
    return 0, (ax, ay), (bx, by)


def main() -> None:
    text = load_mask("T04_selection_key_text_mask_300dpi.png")
    axis = load_mask("G06_x_axis_arrow_foreground_mask_300dpi.png")
    overlap, text_xy, axis_xy = nearest_pair(text, axis)
    center_distance = math.dist(text_xy, axis_xy)
    result = {
        "official_baseline": "strict_current_r92_fullbook/main_full.pdf physical page 170",
        "mask_source": "STRICT_R3_SA1_R92 independent native 300dpi semantic masks",
        "text_element": "T04_SELECTION_KEY",
        "graphic_element": "G06_X_AXIS_ARROW",
        "overlap_pixel_count": overlap,
        "nearest_text_foreground_xy": list(text_xy),
        "nearest_graphic_foreground_xy": list(axis_xy),
        "center_distance_px": round(center_distance, 4),
        "foreground_clearance_px": round(max(0.0, center_distance - 1.0), 4),
        "pass_hard_3px": overlap == 0 and center_distance - 1.0 >= 3.0,
        "pass_target_8px": overlap == 0 and center_distance - 1.0 >= 8.0,
        "method": "independent masks; scipy EDT nearest foreground centers; clearance=center distance-1px",
    }
    (HERE / "r92_baseline_reproduction.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
