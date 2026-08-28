from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
REVIEW = ROOT / "review"
RENDER = REVIEW / "render"
MACHINE = REVIEW / "machine"
ROI = REVIEW / "roi"
PDF_SHA = "58BA180DBC92ED6DFEECCA2D77FE021C55B9D9B5DE0A1F6DB5F4B8D7316CAD06"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def crop_box_px(box_pt, scale, pad_px, image_size):
    x0 = max(0, int(box_pt[0] * scale) - pad_px)
    y0 = max(0, int(box_pt[1] * scale) - pad_px)
    x1 = min(image_size[0], int(box_pt[2] * scale + 0.999) + pad_px)
    y1 = min(image_size[1], int(box_pt[3] * scale + 0.999) + pad_px)
    return (x0, y0, x1, y1)


def nonwhite_bbox(image: Image.Image, threshold: int = 248):
    gray = image.convert("L")
    mask = gray.point(lambda value: 255 if value < threshold else 0)
    return mask.getbbox()


def main():
    if PDF.stat().st_size != 33952 or sha256(PDF) != PDF_SHA:
        raise RuntimeError("PDF identity mismatch")
    raw_path = MACHINE / "RAW_VISIBLE_OBJECTS.csv"
    pairs_path = MACHINE / "RAW_ALL_UNORDERED_PAIRS.csv"
    if not raw_path.is_file() or not pairs_path.is_file():
        raise RuntimeError("first-pass raw denominator is absent")
    raw = read_csv(raw_path)
    pairs = read_csv(pairs_path)

    with pdfplumber.open(PDF) as document:
        page = document.pages[0]
        words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
        legend_chars = [
            char
            for char in page.chars
            if 220.0 <= float(char["top"]) <= 242.0
            and 220.0 <= float(char["bottom"]) <= 242.0
        ]
        if len(legend_chars) != 8:
            raise RuntimeError(f"expected 8 legend characters, got {len(legend_chars)}")
        legend_pt = (
            max(0.0, min(float(c["x0"]) for c in legend_chars) - 35.0),
            min(float(c["top"]) for c in legend_chars) - 8.0,
            min(float(page.width), max(float(c["x1"]) for c in legend_chars) + 8.0),
            max(float(c["bottom"]) for c in legend_chars) + 8.0,
        )

    color = Image.open(RENDER / "full_page_300dpi.png").convert("RGB")
    gray = Image.open(RENDER / "full_page_300dpi_gray.png").convert("L")
    scale = color.width / 595.276
    ink_box = nonwhite_bbox(color)
    if ink_box is None:
        raise RuntimeError("empty rendered page")
    figure_box = (
        max(0, ink_box[0] - 30),
        max(0, ink_box[1] - 30),
        min(color.width, ink_box[2] + 30),
        min(color.height, ink_box[3] + 30),
    )
    color.crop(figure_box).save(ROI / "FIGURE_NATIVE300.png")
    gray.crop(figure_box).save(ROI / "FIGURE_GRAY_NATIVE300.png")

    legend_px = crop_box_px(legend_pt, scale, 8, color.size)
    legend_color = color.crop(legend_px)
    legend_gray = gray.crop(legend_px)
    legend_color.save(ROI / "LEGEND_NATIVE1X.png")
    legend_gray.save(ROI / "LEGEND_GRAY_NATIVE1X.png")
    legend_color.resize(
        (legend_color.width * 8, legend_color.height * 8), Image.Resampling.NEAREST
    ).save(ROI / "LEGEND_NEAREST8X.png")
    legend_gray.resize(
        (legend_gray.width * 8, legend_gray.height * 8), Image.Resampling.NEAREST
    ).save(ROI / "LEGEND_GRAY_NEAREST8X.png")

    overlay = color.copy()
    draw = ImageDraw.Draw(overlay)
    for obj in raw:
        box = tuple(float(obj[key]) for key in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))
        px = crop_box_px(box, scale, 0, overlay.size)
        draw.rectangle(px, outline=(220, 0, 170), width=1)
        draw.text((px[0], max(0, px[1] - 10)), obj["object_id"], fill=(140, 0, 100))
    overlay.crop(figure_box).save(ROI / "RAW_OBJECT_OVERLAY.png")

    counters = Counter(row["kind"] for row in raw)
    summary = {
        "schema": "P126_R5_MACHINE_EVIDENCE_V1_CONTINUED_AFTER_LEGEND_COORDINATE_CORRECTION",
        "first_pass_failure": "legend locator assumed top > 240pt; current legend text is at top 228.015..228.344pt",
        "first_pass_outputs_reused_without_pair_rescan": [str(raw_path), str(pairs_path)],
        "pdf_path": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": PDF_SHA,
        "page_count": 1,
        "page_width_pt": 595.276,
        "page_height_pt": 841.89,
        "render_width_px_300dpi": color.width,
        "render_height_px_300dpi": color.height,
        "render_scale_px_per_pt": scale,
        "raw_counts": dict(counters),
        "raw_visible_object_count": len(raw),
        "raw_unordered_pair_count": len(pairs),
        "raw_bbox_candidate_count": sum(int(row["bbox_intersects"]) for row in pairs),
        "nonwhite_page_bbox_px": list(ink_box),
        "figure_crop_bbox_px": list(figure_box),
        "legend_bbox_pt": list(legend_pt),
        "legend_bbox_px": list(legend_px),
        "legend_character_count": len(legend_chars),
        "extracted_words": words,
        "manual_fields_generated": 0,
    }
    (MACHINE / "MACHINE_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
