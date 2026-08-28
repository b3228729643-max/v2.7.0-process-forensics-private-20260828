from __future__ import annotations

"""Fresh SA1 evidence generator for FIG-P582-01.

It reads only the frozen candidate PDF and writes artifacts below this audit
directory.  Native rasters are rendered directly with PyMuPDF at the requested
matrix; every crop is an integer-coordinate crop of that native raster.
"""

import csv
import json
import math
from collections import Counter
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path.cwd()
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P582-01" / "STRICT_R1" / "SA1_20260824_R1"
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r95_fullbook" / "main_full.pdf"
PAGE_INDEX = 629  # PDF physical page 630; discovered from candidate text anchor.
PRINTED_PAGE = 617
DPI = 300
SCALE = DPI / 72.0

# PDF point rectangles determined from the candidate page's caption / graphic
# anchors, not from a supplied page number.  They are deliberately inclusive
# of all chart text and the two-line caption, while excluding neighbor prose.
BODY_PT = fitz.Rect(155.0, 322.0, 451.0, 481.0)
FIGURE_PT = fitz.Rect(67.0, 322.0, 535.0, 513.0)


def int_crop(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * SCALE),
        math.floor(rect.y0 * SCALE),
        math.ceil(rect.x1 * SCALE),
        math.ceil(rect.y1 * SCALE),
    )


def safe_text(value: str) -> str:
    return value.replace("\u00a0", " ").replace("\n", " ").strip()


def rgb_from_pdf_color(color: int) -> tuple[int, int, int]:
    return ((color >> 16) & 255, (color >> 8) & 255, color & 255)


def png_save(img: Image.Image, path: Path, dpi: int | None = None) -> None:
    kwargs = {"optimize": False}
    if dpi:
        kwargs["dpi"] = (dpi, dpi)
    img.save(path, **kwargs)


def within(rect: fitz.Rect, area: fitz.Rect) -> bool:
    # A character whose center is inside the target is included; this handles
    # descenders/subscripts that sit on a crop boundary without including prose.
    return area.contains(rect.tl + (rect.br - rect.tl) * 0.5)


def write_raw_text(page: fitz.Page) -> list[dict]:
    raw = page.get_text("rawdict", sort=True)
    chars: list[dict] = []
    spans: list[dict] = []
    element_idx = 0
    char_idx = 0
    for block_index, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            for span_index, span in enumerate(line.get("spans", [])):
                span_chars = span.get("chars", [])
                text = "".join(c.get("c", "") for c in span_chars)
                bbox = fitz.Rect(span["bbox"])
                if not text.strip() or not within(bbox, FIGURE_PT):
                    continue
                element_idx += 1
                element_id = f"E{element_idx:03d}"
                rec = {
                    "element_id": element_id,
                    "text": safe_text(text),
                    "bbox_pt": [round(v, 4) for v in bbox],
                    "font": span.get("font", ""),
                    "size_pt_pdf": round(float(span.get("size", 0.0)), 4),
                    "flags": span.get("flags"),
                    "color_rgb": rgb_from_pdf_color(int(span.get("color", 0))),
                    "block": block_index,
                    "line": line_index,
                    "span": span_index,
                    "char_ids": [],
                }
                for position, char in enumerate(span_chars):
                    c = char.get("c", "")
                    cbbox = fitz.Rect(char["bbox"])
                    if not c or c.isspace():
                        continue
                    char_idx += 1
                    glyph_id = f"G{char_idx:04d}"
                    char_rec = {
                        "glyph_id": glyph_id,
                        "element_id": element_id,
                        "position": position,
                        "char": c,
                        "bbox_pt": [round(v, 4) for v in cbbox],
                        "font": span.get("font", ""),
                        "size_pt_pdf": round(float(span.get("size", 0.0)), 4),
                        "color_rgb": rgb_from_pdf_color(int(span.get("color", 0))),
                    }
                    chars.append(char_rec)
                    rec["char_ids"].append(glyph_id)
                spans.append(rec)
    (OUT / "extracted_text_elements.json").write_text(
        json.dumps({"page_index": PAGE_INDEX, "elements": spans, "glyphs": chars}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return chars


def render_page() -> tuple[fitz.Page, Image.Image, Image.Image]:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, colorspace=fitz.csRGB)
    full300 = Image.frombytes("RGB", [pix300.width, pix300.height], pix300.samples)
    pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False, colorspace=fitz.csRGB)
    full200 = Image.frombytes("RGB", [pix200.width, pix200.height], pix200.samples)
    png_save(full300, OUT / "renders" / "full_page_native_300dpi.png", DPI)
    png_save(full200, OUT / "full_page_200dpi.png", 200)
    return page, full300, full200


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "renders").mkdir(exist_ok=True)
    page, full300, _ = render_page()
    body_box = int_crop(BODY_PT)
    figure_box = int_crop(FIGURE_PT)
    standalone = full300.crop(body_box)
    figure_crop = full300.crop(figure_box)
    png_save(standalone, OUT / "standalone_300dpi.png", DPI)
    png_save(figure_crop, OUT / "figure_crop_300dpi.png", DPI)
    png_save(ImageOps.grayscale(figure_crop), OUT / "grayscale_300dpi.png", DPI)
    chars = write_raw_text(page)
    manifest = {
        "figure_id": "FIG-P582-01",
        "candidate_pdf": str(PDF),
        "candidate_pdf_name": PDF.name,
        "pdf_physical_page": PAGE_INDEX + 1,
        "printed_page": PRINTED_PAGE,
        "page_size_pt": [round(page.rect.width, 4), round(page.rect.height, 4)],
        "native_300dpi_full_px": list(full300.size),
        "native_200dpi_full_px": [int(round(page.rect.width * 200 / 72)), int(round(page.rect.height * 200 / 72))],
        "body_crop_pt": list(BODY_PT),
        "body_crop_native_300dpi_xyxy": list(body_box),
        "body_crop_native_px": list(standalone.size),
        "figure_crop_pt": list(FIGURE_PT),
        "figure_crop_native_300dpi_xyxy": list(figure_box),
        "figure_crop_native_px": list(figure_crop.size),
        "render_method": "PyMuPDF Page.get_pixmap direct final candidate PDF; no resize after rasterization",
        "crop_method": "integer-coordinate crop of native 300dpi full-page raster; no resize",
        "glyph_count_nonspace": len(chars),
    }
    (OUT / "render_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
