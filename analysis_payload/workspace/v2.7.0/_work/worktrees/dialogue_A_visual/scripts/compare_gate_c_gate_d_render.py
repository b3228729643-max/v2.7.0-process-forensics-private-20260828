#!/usr/bin/env python3
"""Perform the single planned full-book pixel comparison at Gate D."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def read_image(path: Path) -> np.ndarray:
    payload = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(payload, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"cannot decode {path}")
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate_c")
    parser.add_argument("gate_d")
    parser.add_argument("--output", required=True)
    parser.add_argument("--visual-dir", required=True)
    args = parser.parse_args()

    gate_c = Path(args.gate_c).resolve()
    gate_d = Path(args.gate_d).resolve()
    output = Path(args.output).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    visual_dir.mkdir(parents=True, exist_ok=True)
    c_files = sorted(gate_c.glob("page-*.png"))
    d_files = sorted(gate_d.glob("page-*.png"))
    if len(c_files) != 771 or len(d_files) != 771:
        raise RuntimeError(f"expected 771+771 pages, got {len(c_files)}+{len(d_files)}")

    metrics = []
    for index, (c_path, d_path) in enumerate(zip(c_files, d_files), start=1):
        c_image = read_image(c_path)
        d_image = read_image(d_path)
        if c_image.shape != d_image.shape:
            raise RuntimeError(f"dimension mismatch at page {index}: {c_image.shape} != {d_image.shape}")
        delta = cv2.absdiff(c_image, d_image)
        changed = delta > 2
        metrics.append(
            {
                "page": index,
                "mean_absolute_difference": round(float(delta.mean()), 8),
                "maximum_difference": int(delta.max()),
                "changed_pixel_fraction": round(float(changed.mean()), 10),
            }
        )

    ranked = sorted(metrics, key=lambda item: (item["changed_pixel_fraction"], item["mean_absolute_difference"]), reverse=True)
    selected = ranked[:32]
    cell_width, cell_height = 400, 590
    thumb_width, thumb_height = 390, 552
    font = ImageFont.load_default()
    contacts = []
    for sheet_index, offset in enumerate(range(0, len(selected), 16), start=1):
        batch = selected[offset : offset + 16]
        canvas = Image.new("RGB", (cell_width * 4, cell_height * 4), "#d9e2f3")
        draw = ImageDraw.Draw(canvas)
        for position, metric in enumerate(batch):
            row, col = divmod(position, 4)
            page = metric["page"]
            with Image.open(d_files[page - 1]) as image:
                preview = image.convert("RGB")
                preview.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                x = col * cell_width + (cell_width - preview.width) // 2
                y = row * cell_height + 30
                canvas.paste(preview, (x, y))
            label = f"p{page} changed={metric['changed_pixel_fraction']:.8f} mean={metric['mean_absolute_difference']:.6f}"
            draw.text((col * cell_width + 6, row * cell_height + 6), label, fill="#000000", font=font)
        contact = visual_dir / f"highest-diff-{sheet_index:02d}.png"
        canvas.save(contact, optimize=True)
        contacts.append(str(contact))

    payload = {
        "schema_version": 1,
        "comparison_scope": "single_full_book_pixel_comparison_at_gate_d",
        "gate_c_render": str(gate_c),
        "gate_d_render": str(gate_d),
        "page_count": 771,
        "exactly_identical_pages": sum(item["maximum_difference"] == 0 for item in metrics),
        "pages_with_changed_pixels": sum(item["maximum_difference"] > 0 for item in metrics),
        "maximum_changed_pixel_fraction": max(item["changed_pixel_fraction"] for item in metrics),
        "maximum_mean_absolute_difference": max(item["mean_absolute_difference"] for item in metrics),
        "highest_difference_pages": selected,
        "contact_sheets": contacts,
        "metrics": metrics,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("page_count", "exactly_identical_pages", "pages_with_changed_pixels", "maximum_changed_pixel_fraction", "maximum_mean_absolute_difference")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
