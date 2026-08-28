from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Measure the nearest native-pixel distance between occupied pixels in two explicit ROIs. "
            "No crop is resampled."
        )
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--a", nargs=4, type=int, required=True,
                        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--b", nargs=4, type=int, required=True,
                        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--background", nargs=3, type=int, default=(255, 255, 255),
                        metavar=("R", "G", "B"))
    parser.add_argument("--delta", type=int, default=1)
    args = parser.parse_args()

    with Image.open(args.source) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    height, width = rgb.shape[:2]
    boxes = [tuple(args.a), tuple(args.b)]
    for box in boxes:
        left, top, right, bottom = box
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise SystemExit(f"invalid crop {box} for {width}x{height}")

    background = np.asarray(args.background, dtype=np.int16)
    masks: list[np.ndarray] = []
    for left, top, right, bottom in boxes:
        roi = rgb[top:bottom, left:right]
        local = np.max(np.abs(roi - background), axis=2) >= args.delta
        full = np.zeros((height, width), dtype=bool)
        full[top:bottom, left:right] = local
        masks.append(full)

    a_mask, b_mask = masks
    if not a_mask.any() or not b_mask.any():
        raise SystemExit(f"empty occupied mask: A={int(a_mask.sum())} B={int(b_mask.sum())}")

    overlap = int(np.count_nonzero(a_mask & b_mask))
    euclidean = float(ndimage.distance_transform_edt(~b_mask)[a_mask].min())
    chessboard = int(ndimage.distance_transform_cdt(~b_mask, metric="chessboard")[a_mask].min())
    print(
        f"source={args.source} image={width}x{height} delta={args.delta} "
        f"A={boxes[0]} occupiedA={int(a_mask.sum())} "
        f"B={boxes[1]} occupiedB={int(b_mask.sum())}"
    )
    print(f"overlap_pixels={overlap}")
    print(f"nearest_center_euclidean_px={euclidean:.6f}")
    print(f"nearest_center_chebyshev_px={chessboard}")
    print(f"native_blank_pixel_clearance={max(0, chessboard - 1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
