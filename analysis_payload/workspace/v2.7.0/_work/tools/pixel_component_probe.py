from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report native-pixel connected components near an RGB colour without resampling."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--rgb", nargs=3, type=int, required=True, metavar=("R", "G", "B"))
    parser.add_argument("--tol", type=int, default=8, help="Maximum per-channel absolute deviation")
    parser.add_argument("--box", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--min-area", type=int, default=3)
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()

    with Image.open(args.source) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.int16)

    left = top = 0
    right, bottom = rgb.shape[1], rgb.shape[0]
    if args.box:
        left, top, right, bottom = args.box
        if not (0 <= left < right <= rgb.shape[1] and 0 <= top < bottom <= rgb.shape[0]):
            raise SystemExit(f"invalid crop {args.box} for {rgb.shape[1]}x{rgb.shape[0]}")
        rgb = rgb[top:bottom, left:right]

    target = np.asarray(args.rgb, dtype=np.int16)
    mask = np.max(np.abs(rgb - target), axis=2) <= args.tol
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    objects = ndimage.find_objects(labels)
    components: list[tuple[int, int, int, int, int, int]] = []
    for label_id, slices in enumerate(objects, start=1):
        if slices is None:
            continue
        ys, xs = slices
        area = int(np.count_nonzero(labels[ys, xs] == label_id))
        if area < args.min_area:
            continue
        components.append(
            (area, xs.start + left, ys.start + top, xs.stop - 1 + left, ys.stop - 1 + top, label_id)
        )

    components.sort(reverse=True)
    print(
        f"source={args.source} size={right-left}x{bottom-top} origin=({left},{top}) "
        f"rgb={tuple(args.rgb)} tol={args.tol} matched={int(mask.sum())} "
        f"components={len(components)}/{count}"
    )
    for area, x0, y0, x1, y1, label_id in components[: args.top]:
        print(f"area={area:6d} bbox=({x0},{y0})-({x1},{y1}) label={label_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
