from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def page_number(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    if match is None:
        raise ValueError(f"page number missing from {path.name}")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("page_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--rows", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=390)
    args = parser.parse_args()

    pages = sorted(args.page_dir.glob("page-*.png"), key=page_number)
    if not pages:
        raise SystemExit("no page PNGs found")
    expected = list(range(1, len(pages) + 1))
    actual = [page_number(path) for path in pages]
    if actual != expected:
        raise SystemExit("page PNG sequence is incomplete")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_sheet = args.columns * args.rows
    label_height = 30
    margin = 16

    with Image.open(pages[0]) as sample:
        thumb_height = round(sample.height * args.thumb_width / sample.width)
    cell_width = args.thumb_width + margin
    cell_height = thumb_height + label_height + margin
    sheet_size = (
        margin + args.columns * cell_width,
        margin + args.rows * cell_height,
    )
    font = ImageFont.load_default(size=20)

    for sheet_index in range(math.ceil(len(pages) / per_sheet)):
        start = sheet_index * per_sheet
        batch = pages[start : start + per_sheet]
        sheet = Image.new("RGB", sheet_size, "#d8d8d8")
        draw = ImageDraw.Draw(sheet)
        for offset, path in enumerate(batch):
            row, column = divmod(offset, args.columns)
            x = margin + column * cell_width
            y = margin + row * cell_height
            with Image.open(path) as page:
                thumb = page.convert("RGB")
                thumb.thumbnail((args.thumb_width, thumb_height), Image.Resampling.LANCZOS)
                sheet.paste(thumb, (x, y))
            label = f"PDF page {page_number(path)}"
            draw.text((x, y + thumb_height + 3), label, fill="black", font=font)
        first = page_number(batch[0])
        last = page_number(batch[-1])
        output = args.output_dir / f"contact-{sheet_index + 1:03d}-p{first:03d}-p{last:03d}.jpg"
        sheet.save(output, "JPEG", quality=92, optimize=True)

    print(f"pages={len(pages)} sheets={math.ceil(len(pages) / per_sheet)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
