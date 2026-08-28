#!/usr/bin/env python3
"""Audit an existing Gate-C full-book render without rendering any PDF pages.

The script validates the one-to-one page inventory, computes conservative
blank/dark/edge metrics for every page, and prepares deterministic contact
sheets for human review.  It never invokes a PDF renderer.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PAGE_RE = re.compile(r"page-(\d+)\.png$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("page_image_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--visual-dir", type=Path, required=True)
    return parser.parse_args()


def page_number(path: Path) -> int:
    match = PAGE_RE.match(path.name)
    if not match:
        raise ValueError(f"unexpected page-image name: {path.name}")
    return int(match.group(1))


def contact_sheet(
    pages: list[int],
    image_by_page: dict[int, Path],
    output: Path,
    title: str,
) -> None:
    if not pages:
        return
    cols, rows = 4, 3
    cell_w, cell_h = 420, 610
    header_h = 42
    font = ImageFont.load_default()
    for batch_index in range(0, len(pages), cols * rows):
        batch = pages[batch_index : batch_index + cols * rows]
        canvas = Image.new("RGB", (cols * cell_w, rows * cell_h + header_h), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 12), title, fill="black", font=font)
        for slot, page in enumerate(batch):
            row, col = divmod(slot, cols)
            x0, y0 = col * cell_w, header_h + row * cell_h
            with Image.open(image_by_page[page]) as source:
                thumb = source.convert("RGB")
                thumb.thumbnail((cell_w - 18, cell_h - 32), Image.Resampling.LANCZOS)
            x = x0 + (cell_w - thumb.width) // 2
            y = y0 + 24
            canvas.paste(thumb, (x, y))
            draw.rectangle((x0, y0, x0 + cell_w - 1, y0 + cell_h - 1), outline="#777777")
            draw.text((x0 + 8, y0 + 6), f"PDF p.{page}", fill="black", font=font)
        suffix = batch_index // (cols * rows) + 1
        canvas.save(output.with_name(f"{output.stem}-{suffix:02d}{output.suffix}"))


def main() -> int:
    args = parse_args()
    pdf = args.pdf.resolve()
    image_dir = args.page_image_dir.resolve()
    output = args.output.resolve()
    visual_dir = args.visual_dir.resolve()

    images = sorted(image_dir.glob("page-*.png"), key=page_number)
    numbers = [page_number(path) for path in images]
    with fitz.open(pdf) as document:
        pdf_pages = document.page_count
    expected = list(range(1, pdf_pages + 1))
    if numbers != expected:
        missing = sorted(set(expected) - set(numbers))
        extra = sorted(set(numbers) - set(expected))
        raise RuntimeError(f"page inventory mismatch: missing={missing}, extra={extra}")

    metrics: list[dict[str, float | int | str]] = []
    dimensions: set[tuple[int, int]] = set()
    for page, path in zip(numbers, images, strict=True):
        encoded = np.fromfile(path, dtype=np.uint8)
        gray = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError(f"cannot read {path}")
        height, width = gray.shape
        dimensions.add((width, height))
        ink = gray < 245
        dark = gray < 32
        edge_width = max(4, round(min(width, height) * 0.006))
        edge_mask = np.zeros_like(ink)
        edge_mask[:edge_width, :] = True
        edge_mask[-edge_width:, :] = True
        edge_mask[:, :edge_width] = True
        edge_mask[:, -edge_width:] = True

        small_dark = cv2.resize(
            dark.astype(np.uint8),
            (max(1, width // 4), max(1, height // 4)),
            interpolation=cv2.INTER_AREA,
        )
        binary = (small_dark >= 128).astype(np.uint8)
        component_count, _, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        if component_count > 1:
            largest_component = int(stats[1:, cv2.CC_STAT_AREA].max()) * 16
        else:
            largest_component = 0

        metrics.append(
            {
                "page": page,
                "image": path.name,
                "width": width,
                "height": height,
                "file_bytes": path.stat().st_size,
                "mean_gray": round(float(gray.mean()), 6),
                "ink_fraction": round(float(ink.mean()), 8),
                "dark_fraction": round(float(dark.mean()), 8),
                "edge_ink_fraction": round(float(ink[edge_mask].mean()), 8),
                "largest_dark_component_fraction": round(
                    largest_component / float(width * height), 8
                ),
            }
        )

    if len(dimensions) != 1:
        raise RuntimeError(f"inconsistent page dimensions: {sorted(dimensions)}")

    near_blank = [
        int(row["page"])
        for row in sorted(metrics, key=lambda row: float(row["ink_fraction"]))[:12]
    ]
    darkest = [
        int(row["page"])
        for row in sorted(
            metrics,
            key=lambda row: float(row["largest_dark_component_fraction"]),
            reverse=True,
        )[:12]
    ]
    most_ink = [
        int(row["page"])
        for row in sorted(metrics, key=lambda row: float(row["ink_fraction"]), reverse=True)[:12]
    ]
    edge_pages = [
        int(row["page"])
        for row in sorted(
            metrics, key=lambda row: float(row["edge_ink_fraction"]), reverse=True
        )
        if float(row["edge_ink_fraction"]) > 0
    ][:12]
    algorithm_risk = [503, 504, 525, 526, 589, 616, 617, 674, 703, 704, 726, 727]

    image_by_page = {page: path for page, path in zip(numbers, images, strict=True)}
    visual_dir.mkdir(parents=True, exist_ok=True)
    contact_sheet(near_blank, image_by_page, visual_dir / "near-blank.png", "Lowest ink fraction")
    contact_sheet(darkest, image_by_page, visual_dir / "darkest-block.png", "Largest dark components")
    contact_sheet(most_ink, image_by_page, visual_dir / "most-ink.png", "Highest ink fraction")
    contact_sheet(edge_pages, image_by_page, visual_dir / "edge-ink.png", "Non-white page edges")
    contact_sheet(
        algorithm_risk,
        image_by_page,
        visual_dir / "algorithm-risk.png",
        "Gate-B repaired algorithm/strip pages",
    )

    hard_failures = {
        "dimension_mismatch": len(dimensions) != 1,
        "zero_byte_images": [
            int(row["page"]) for row in metrics if int(row["file_bytes"]) == 0
        ],
        "near_blank_nonstructural_pages": [
            int(row["page"])
            for row in metrics
            if float(row["ink_fraction"]) < 0.00005
        ],
        "large_black_block_pages": [
            int(row["page"])
            for row in metrics
            if float(row["largest_dark_component_fraction"]) > 0.08
        ],
        "edge_clipping_candidates": [
            int(row["page"])
            for row in metrics
            if float(row["edge_ink_fraction"]) > 0.02
        ],
    }
    payload = {
        "schema_version": 1,
        "pdf": str(pdf),
        "page_image_dir": str(image_dir),
        "pdf_page_count": pdf_pages,
        "image_count": len(images),
        "dimensions": [list(item) for item in sorted(dimensions)],
        "thresholds": {
            "ink_gray_below": 245,
            "dark_gray_below": 32,
            "near_blank_ink_fraction": 0.00005,
            "large_black_component_fraction": 0.08,
            "edge_clipping_fraction": 0.02,
        },
        "hard_failures": hard_failures,
        "review_pages": {
            "near_blank": near_blank,
            "darkest": darkest,
            "most_ink": most_ink,
            "edge": edge_pages,
            "algorithm_risk": algorithm_risk,
        },
        "metrics": metrics,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failure_count = sum(
        len(value) if isinstance(value, list) else int(bool(value))
        for value in hard_failures.values()
    )
    print(f"GATE_C_RENDER_PAGES={len(images)}")
    print(f"GATE_C_RENDER_DIMENSIONS={sorted(dimensions)}")
    print(f"GATE_C_RENDER_HARD_FAILURES={failure_count}")
    print(f"GATE_C_RENDER_OUTPUT={output}")
    return 0 if failure_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
