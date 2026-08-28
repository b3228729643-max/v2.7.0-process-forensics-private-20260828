#!/usr/bin/env python3
"""Render a deterministic PDF page set and prepare review contact sheets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=120)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--page-list-json", type=Path)
    group.add_argument("--pages", help="comma-separated one-based page numbers and ranges")
    parser.add_argument("--page-list-key", default="exercise_section_pages")
    return parser.parse_args()


def page_set(args: argparse.Namespace, page_count: int) -> list[int]:
    if args.all:
        return list(range(1, page_count + 1))
    if args.pages:
        values: set[int] = set()
        for item in args.pages.split(","):
            item = item.strip()
            if "-" in item:
                start, end = (int(value) for value in item.split("-", 1))
                values.update(range(start, end + 1))
            elif item:
                values.add(int(item))
        pages = sorted(values)
    else:
        payload = json.loads(args.page_list_json.read_text(encoding="utf-8"))
        pages = sorted({int(value) for value in payload[args.page_list_key]})
    if not pages or pages[0] < 1 or pages[-1] > page_count:
        raise ValueError(f"invalid page set for {page_count}-page PDF")
    return pages


def make_contacts(images: list[tuple[int, Path]], contact_dir: Path) -> list[str]:
    contact_dir.mkdir(parents=True, exist_ok=True)
    columns, rows = 4, 3
    cell_width, cell_height, header = 420, 610, 30
    font = ImageFont.load_default()
    outputs: list[str] = []
    for offset in range(0, len(images), columns * rows):
        batch = images[offset : offset + columns * rows]
        canvas = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
        draw = ImageDraw.Draw(canvas)
        for slot, (page_number, path) in enumerate(batch):
            row, column = divmod(slot, columns)
            x0, y0 = column * cell_width, row * cell_height
            with Image.open(path) as source:
                thumbnail = source.convert("RGB")
                thumbnail.thumbnail(
                    (cell_width - 16, cell_height - header - 12),
                    Image.Resampling.LANCZOS,
                )
            x = x0 + (cell_width - thumbnail.width) // 2
            y = y0 + header + (cell_height - header - thumbnail.height) // 2
            canvas.paste(thumbnail, (x, y))
            draw.text((x0 + 8, y0 + 8), f"PDF p.{page_number}", fill="black", font=font)
            draw.rectangle(
                (x0, y0, x0 + cell_width - 1, y0 + cell_height - 1),
                outline="#777777",
                width=1,
            )
        output = contact_dir / f"contact-{offset // (columns * rows) + 1:03d}.png"
        canvas.save(output, optimize=True)
        outputs.append(str(output.resolve()))
    return outputs


def image_metrics(image: Image.Image) -> dict[str, float]:
    gray = np.asarray(image.convert("L"), dtype=np.uint8)
    ink = gray < 245
    dark = gray < 32
    edge_width = max(4, round(min(gray.shape) * 0.006))
    edge = np.zeros_like(ink)
    edge[:edge_width, :] = True
    edge[-edge_width:, :] = True
    edge[:, :edge_width] = True
    edge[:, -edge_width:] = True
    return {
        "mean_gray": round(float(gray.mean()), 6),
        "ink_fraction": round(float(ink.mean()), 8),
        "dark_fraction": round(float(dark.mean()), 8),
        "edge_ink_fraction": round(float(ink[edge].mean()), 8),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    pdf_path = args.pdf.resolve()
    output_dir = args.output_dir.resolve()
    page_dir = output_dir / "pages"
    contact_dir = output_dir / "contacts"
    page_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[tuple[int, Path]] = []
    metrics: list[dict[str, object]] = []
    dimensions: set[tuple[int, int]] = set()
    with fitz.open(pdf_path) as document:
        pages = page_set(args, document.page_count)
        matrix = fitz.Matrix(args.dpi / 72.0, args.dpi / 72.0)
        for page_number in pages:
            pixmap = document[page_number - 1].get_pixmap(matrix=matrix, alpha=False)
            output = page_dir / f"page-{page_number:04d}.png"
            pixmap.save(output)
            with Image.open(output) as image:
                dimensions.add(image.size)
                row = {"page": page_number, "image": output.name, "file_bytes": output.stat().st_size}
                row.update(image_metrics(image))
            rendered.append((page_number, output))
            metrics.append(row)

    contacts = make_contacts(rendered, contact_dir)
    hard_failures = {
        "render_count_mismatch": len(rendered) != len(pages),
        "dimension_mismatch": len(dimensions) != 1,
        "zero_byte_images": [int(row["page"]) for row in metrics if int(row["file_bytes"]) == 0],
        "near_blank_pages": [
            int(row["page"]) for row in metrics if float(row["ink_fraction"]) < 0.00005
        ],
        "edge_clipping_candidates": [
            int(row["page"]) for row in metrics if float(row["edge_ink_fraction"]) > 0.02
        ],
    }
    failure_count = sum(
        len(value) if isinstance(value, list) else int(bool(value))
        for value in hard_failures.values()
    )
    payload = {
        "schema_version": 1,
        "pdf": str(pdf_path),
        "dpi": args.dpi,
        "page_count": len(pages),
        "pages": pages,
        "image_dimensions": [list(value) for value in sorted(dimensions)],
        "contact_count": len(contacts),
        "contacts": contacts,
        "hard_failures": hard_failures,
        "metrics": metrics,
        "result": "PASS" if failure_count == 0 else "FAIL",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RENDERED_PAGES={len(rendered)}")
    print(f"CONTACT_SHEETS={len(contacts)}")
    print(f"HARD_FAILURES={failure_count}")
    print(f"RESULT={payload['result']}")
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
