from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--box", nargs=4, type=int, required=True, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    args = parser.parse_args()

    with Image.open(args.source) as image:
        left, top, right, bottom = args.box
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise SystemExit(f"invalid crop {args.box} for {image.width}x{image.height}")
        crop = image.crop((left, top, right, bottom))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        crop.save(args.output)
        print(f"source={image.width}x{image.height} crop={crop.width}x{crop.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
