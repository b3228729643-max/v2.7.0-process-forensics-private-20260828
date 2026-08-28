from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def parse_mask(spec: str, rgb: np.ndarray, background: np.ndarray, delta: int) -> np.ndarray:
    """Return a mask for `foreground` or `R,G,B,TOL`."""
    if spec == "foreground":
        return np.max(np.abs(rgb - background), axis=2) >= delta
    parts = [int(value) for value in spec.split(",")]
    if len(parts) != 4:
        raise ValueError("mask must be 'foreground' or R,G,B,TOL")
    target = np.asarray(parts[:3], dtype=np.int16)
    tolerance = parts[3]
    return np.max(np.abs(rgb - target), axis=2) <= tolerance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure native-pixel gap between colour-filtered objects; no resampling."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--a", nargs=4, type=int, required=True)
    parser.add_argument("--b", nargs=4, type=int, required=True)
    parser.add_argument("--a-mask", default="foreground")
    parser.add_argument("--b-mask", default="foreground")
    parser.add_argument("--background", nargs=3, type=int, default=(255, 255, 255))
    parser.add_argument("--delta", type=int, default=20)
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
    specs = [args.a_mask, args.b_mask]
    masks: list[np.ndarray] = []
    occupied_boxes: list[tuple[int, int, int, int]] = []
    for box, spec in zip(boxes, specs):
        left, top, right, bottom = box
        roi = rgb[top:bottom, left:right]
        local = parse_mask(spec, roi, background, args.delta)
        if not local.any():
            raise SystemExit(f"empty occupied mask for {spec} in {box}")
        ys, xs = np.nonzero(local)
        occupied_boxes.append(
            (int(xs.min() + left), int(ys.min() + top), int(xs.max() + left), int(ys.max() + top))
        )
        full = np.zeros((height, width), dtype=bool)
        full[top:bottom, left:right] = local
        masks.append(full)

    a_mask, b_mask = masks
    overlap = int(np.count_nonzero(a_mask & b_mask))
    euclidean = float(ndimage.distance_transform_edt(~b_mask)[a_mask].min())
    chessboard = int(ndimage.distance_transform_cdt(~b_mask, metric="chessboard")[a_mask].min())
    print(
        f"source={args.source} image={width}x{height} delta={args.delta} "
        f"A={boxes[0]} maskA={args.a_mask} occupiedA={int(a_mask.sum())} bboxA={occupied_boxes[0]} "
        f"B={boxes[1]} maskB={args.b_mask} occupiedB={int(b_mask.sum())} bboxB={occupied_boxes[1]}"
    )
    print(f"overlap_pixels={overlap}")
    print(f"nearest_center_euclidean_px={euclidean:.6f}")
    print(f"nearest_center_chebyshev_px={chessboard}")
    print(f"native_blank_pixel_clearance={max(0, chessboard - 1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
