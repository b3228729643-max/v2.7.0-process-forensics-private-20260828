from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def runs(indices: np.ndarray) -> list[tuple[int, int]]:
    if indices.size == 0:
        return []
    starts = indices[np.r_[True, np.diff(indices) > 1]]
    ends = indices[np.r_[np.diff(indices) > 1, True]]
    return list(zip(starts.tolist(), ends.tolist(), strict=True))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report native-pixel non-background bounds and occupied row/column runs "
            "inside an explicit ROI; the image is never resampled."
        )
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--box", nargs=4, type=int, required=True,
                        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--background", nargs=3, type=int, default=(255, 255, 255),
                        metavar=("R", "G", "B"))
    parser.add_argument(
        "--delta",
        type=int,
        default=1,
        help="A pixel is occupied when any channel differs from the background by at least DELTA.",
    )
    parser.add_argument("--components", action="store_true")
    parser.add_argument("--min-area", type=int, default=3)
    parser.add_argument("--top", type=int, default=50)
    args = parser.parse_args()

    with Image.open(args.source) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.int16)

    left, top, right, bottom = args.box
    if not (0 <= left < right <= rgb.shape[1] and 0 <= top < bottom <= rgb.shape[0]):
        raise SystemExit(f"invalid crop {args.box} for {rgb.shape[1]}x{rgb.shape[0]}")
    roi = rgb[top:bottom, left:right]
    background = np.asarray(args.background, dtype=np.int16)
    mask = np.max(np.abs(roi - background), axis=2) >= args.delta
    ys, xs = np.nonzero(mask)

    print(
        f"source={args.source} image={rgb.shape[1]}x{rgb.shape[0]} "
        f"roi=({left},{top})-({right - 1},{bottom - 1}) size={right-left}x{bottom-top} "
        f"background={tuple(args.background)} delta={args.delta} occupied={int(mask.sum())}"
    )
    if not xs.size:
        print("bbox=EMPTY")
        return 0

    row_ids = np.flatnonzero(mask.any(axis=1)) + top
    col_ids = np.flatnonzero(mask.any(axis=0)) + left
    print(f"bbox=({int(xs.min()) + left},{int(ys.min()) + top})-"
          f"({int(xs.max()) + left},{int(ys.max()) + top})")
    print("row_runs=" + ",".join(f"{a + top}-{b + top}" for a, b in runs(row_ids - top)))
    print("col_runs=" + ",".join(f"{a + left}-{b + left}" for a, b in runs(col_ids - left)))
    if args.components:
        labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
        objects = ndimage.find_objects(labels)
        components: list[tuple[int, int, int, int, int]] = []
        for label_id, slices in enumerate(objects, start=1):
            if slices is None:
                continue
            y_slice, x_slice = slices
            area = int(np.count_nonzero(labels[y_slice, x_slice] == label_id))
            if area >= args.min_area:
                components.append(
                    (area, x_slice.start + left, y_slice.start + top,
                     x_slice.stop - 1 + left, y_slice.stop - 1 + top)
                )
        components.sort(reverse=True)
        print(f"components={len(components)}/{count}")
        for area, x0, y0, x1, y1 in components[:args.top]:
            print(f"area={area:6d} bbox=({x0},{y0})-({x1},{y1})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
