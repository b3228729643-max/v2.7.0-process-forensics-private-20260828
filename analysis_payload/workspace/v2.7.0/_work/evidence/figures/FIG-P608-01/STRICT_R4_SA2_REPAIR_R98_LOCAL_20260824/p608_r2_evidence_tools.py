#!/usr/bin/env python3
"""Produce non-measuring R2 visual evidence from the local LuaLaTeX PDF.

The final 300-dpi source raster is never resized for measurement.  This tool
only makes direct crops, red-bbox review overlays, nearest-neighbour viewing
copies, and vector-isolated supporting masks for individual PDF drawing paths.
All acceptance decisions remain in the human ledgers.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps


DPI = 300
SCALE = DPI / 72.0


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refuse empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def pxbox(rect: fitz.Rect | tuple[float, float, float, float], image: Image.Image, pad: int = 0):
    r = fitz.Rect(rect)
    return (
        max(0, math.floor(r.x0 * SCALE) - pad),
        max(0, math.floor(r.y0 * SCALE) - pad),
        min(image.width, math.ceil(r.x1 * SCALE) + pad),
        min(image.height, math.ceil(r.y1 * SCALE) + pad),
    )


def color_text(value):
    if value is None:
        return ""
    return ";".join(f"{float(v):.6f}" for v in value)


def extract_spans(pdf: Path) -> list[dict]:
    page = fitz.open(pdf)[0]
    raw = page.get_text("rawdict")
    rows, span_id = [], 0
    for bidx, block in enumerate(raw["blocks"]):
        if block["type"] != 0:
            continue
        for lidx, line in enumerate(block["lines"]):
            dx, dy = (float(line.get("dir", (1.0, 0.0))[0]), float(line.get("dir", (1.0, 0.0))[1]))
            rotated = abs(dy) > abs(dx)
            for sidx, span in enumerate(line["spans"]):
                span_id += 1
                chars = span["chars"]
                if chars:
                    rect = fitz.Rect(chars[0]["bbox"])
                    for char in chars[1:]:
                        rect |= fitz.Rect(char["bbox"])
                else:
                    rect = fitz.Rect(span["bbox"])
                text = "".join(char["c"] for char in chars)
                rows.append({
                    "element_id": f"T{span_id:03d}",
                    "object_class": "TEXT_OR_FORMULA",
                    "block_index": bidx,
                    "line_index": lidx,
                    "span_index": sidx,
                    "text": text,
                    "visible_char_count": sum(1 for c in text if not c.isspace()),
                    "font": span.get("font", ""),
                    "effective_pt": f"{float(span.get('size', 0)):.5f}",
                    "color_pdf_int": span.get("color", 0),
                    "line_dir_x": f"{dx:.5f}",
                    "line_dir_y": f"{dy:.5f}",
                    "rotation_deg": 90 if rotated and dy < 0 else 270 if rotated else 0 if dx >= 0 else 180,
                    "bbox_x0_pt": f"{rect.x0:.5f}",
                    "bbox_y0_pt": f"{rect.y0:.5f}",
                    "bbox_x1_pt": f"{rect.x1:.5f}",
                    "bbox_y1_pt": f"{rect.y1:.5f}",
                    "source": "PDF_rawdict",
                })
    return rows


def serial_items(items):
    chunks = []
    for item in items:
        kind = item[0]
        vals = []
        for v in item[1:]:
            if isinstance(v, fitz.Point):
                vals.append(f"({v.x:.5f},{v.y:.5f})")
            elif isinstance(v, fitz.Rect):
                vals.append(f"[{v.x0:.5f},{v.y0:.5f},{v.x1:.5f},{v.y1:.5f}]")
            else:
                vals.append(str(v))
        chunks.append(kind + ":" + ",".join(vals))
    return " | ".join(chunks)


def drawing_rows(pdf: Path) -> tuple[list[dict], list[dict]]:
    page = fitz.open(pdf)[0]
    rows, raw_drawings = [], page.get_drawings()
    for idx, drawing in enumerate(raw_drawings, 1):
        rect = drawing["rect"]
        rows.append({
            "element_id": f"D{idx:03d}",
            "drawing_index_zero_based": idx - 1,
            "object_class": "PDF_DRAWING_PATH",
            "pdf_type": drawing.get("type", ""),
            "bbox_x0_pt": f"{rect.x0:.5f}",
            "bbox_y0_pt": f"{rect.y0:.5f}",
            "bbox_x1_pt": f"{rect.x1:.5f}",
            "bbox_y1_pt": f"{rect.y1:.5f}",
            "stroke_width_pt": "" if drawing.get("width") is None else f"{float(drawing['width']):.5f}",
            "stroke_rgb": color_text(drawing.get("color")),
            "fill_rgb": color_text(drawing.get("fill")),
            "stroke_opacity": f"{float(drawing.get('stroke_opacity') or 1):.5f}",
            "fill_opacity": f"{float(drawing.get('fill_opacity') or 1):.5f}",
            "line_cap": drawing.get("lineCap", ""),
            "line_join": drawing.get("lineJoin", ""),
            "dashes": drawing.get("dashes", ""),
            "item_count": len(drawing.get("items", [])),
            "items_serialized": serial_items(drawing.get("items", [])),
            "extractor": "PyMuPDF_page.get_drawings",
        })
    return rows, raw_drawings


def replay_drawing_mask(drawing: dict, page_rect: fitz.Rect) -> Image.Image:
    """Render one PDF path in isolation; used only for a target-object mask."""
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
    for item in drawing.get("items", []):
        kind = item[0]
        if kind == "l":
            shape.draw_line(item[1], item[2])
        elif kind == "re":
            shape.draw_rect(item[1])
        elif kind == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif kind == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"unhandled drawing item {kind!r}")
    color = drawing.get("color")
    fill = drawing.get("fill")
    cap = drawing.get("lineCap") or 0
    if isinstance(cap, tuple):
        cap = cap[0]
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=color,
        fill=fill,
        lineCap=int(cap),
        lineJoin=int(drawing.get("lineJoin") or 0),
        dashes=drawing.get("dashes") or None,
        closePath=True,
        stroke_opacity=float(drawing.get("stroke_opacity") or 1),
        fill_opacity=float(drawing.get("fill_opacity") or 1),
    )
    shape.commit()
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, colorspace=fitz.csRGB)
    isolated = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return isolated


def target_mask_card(full: Image.Image, outer: tuple[int, int, int, int], target: tuple[int, int, int, int], mask_source: Image.Image | None = None) -> Image.Image:
    """Build one target-only black mask in the original crop coordinate system."""
    if mask_source is None:
        source = full.crop(outer).convert("RGB")
    else:
        source = mask_source.crop(outer).convert("RGB")
    arr = np.asarray(source)
    mask = arr.min(axis=2) < 230
    canvas = np.full(mask.shape, 255, dtype=np.uint8)
    tx0, ty0, tx1, ty1 = target
    ox0, oy0, _, _ = outer
    sx0, sy0 = max(0, tx0 - ox0), max(0, ty0 - oy0)
    sx1, sy1 = min(mask.shape[1], tx1 - ox0), min(mask.shape[0], ty1 - oy0)
    canvas[sy0:sy1, sx0:sx1][mask[sy0:sy1, sx0:sx1]] = 0
    return Image.fromarray(canvas, "L")


def card_from_rect(full: Image.Image, name: str, rect: fitz.Rect, card_dir: Path, isolated: Image.Image | None = None, pad: int = 3) -> dict:
    outer = pxbox(rect, full, pad)
    target = pxbox(rect, full, 0)
    original = full.crop(outer).convert("RGB")
    overlay = original.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((target[0] - outer[0], target[1] - outer[1], target[2] - outer[0] - 1, target[3] - outer[1] - 1), outline=(255, 0, 0), width=1)
    mask = target_mask_card(full, outer, target, isolated)
    original.save(card_dir / f"{name}_original_1x.png")
    overlay.save(card_dir / f"{name}_target_overlay_1x.png")
    mask.save(card_dir / f"{name}_unique_vector_mask_1x.png")
    original.resize((original.width * 8, original.height * 8), Image.Resampling.NEAREST).save(card_dir / f"{name}_original_8x_nearest.png")
    arr = np.asarray(mask)
    return {
        "element_id": name,
        "safe_filename": name,
        "card_original_1x": f"{name}_original_1x.png",
        "card_overlay_1x": f"{name}_target_overlay_1x.png",
        "card_mask_1x": f"{name}_unique_vector_mask_1x.png",
        "card_nearest_8x": f"{name}_original_8x_nearest.png",
        "native_crop_x0_px": outer[0], "native_crop_y0_px": outer[1],
        "native_crop_x1_px": outer[2], "native_crop_y1_px": outer[3],
        "mask_area_px": int((arr == 0).sum()),
    }


def contacts(cards: list[Path], out_dir: Path, suffix: str, title: str, per_sheet: int = 6, columns: int = 3):
    out_dir.mkdir(parents=True, exist_ok=True)
    for page_idx in range(0, len(cards), per_sheet):
        part = cards[page_idx:page_idx + per_sheet]
        ims = [Image.open(p).convert("RGB") for p in part]
        pad, label_h = 12, 24
        cw = max(im.width for im in ims) + 2 * pad
        ch = max(im.height for im in ims) + label_h + 2 * pad
        rows = math.ceil(len(ims) / columns)
        sheet = Image.new("RGB", (columns * cw, rows * ch + 36), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((pad, 8), title, fill="black")
        for n, (path, im) in enumerate(zip(part, ims)):
            col, row = n % columns, n // columns
            x, y = col * cw + pad, 36 + row * ch + label_h + pad
            sheet.paste(im, (x, y))
            draw.text((x, y - label_h), path.name.split("_")[0], fill="black")
            draw.rectangle((col * cw, 36 + row * ch, (col + 1) * cw - 1, 36 + (row + 1) * ch - 1), outline="gray")
        sheet.save(out_dir / f"{suffix}_sheet_{page_idx // per_sheet + 1:02d}.png")


def make_overlay(full: Image.Image, glyph_csv: Path, output: Path):
    with glyph_csv.open("r", newline="", encoding="utf-8-sig") as fh:
        glyphs = list(csv.DictReader(fh))
    image = full.copy().convert("RGB")
    draw = ImageDraw.Draw(image)
    for row in glyphs:
        rect = (float(row["x0_pt"]), float(row["y0_pt"]), float(row["x1_pt"]), float(row["y1_pt"]))
        x0, y0, x1, y1 = pxbox(rect, image, 0)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(220, 0, 0), width=1)
        draw.text((x0, max(0, y0 - 10)), row["glyph_id"], fill=(180, 0, 0))
    image.save(output)


def colorblind(full: Image.Image, matrix: np.ndarray, output: Path):
    arr = np.asarray(full.convert("RGB"), dtype=np.float32) / 255.0
    transformed = np.clip(arr @ matrix.T, 0, 1)
    Image.fromarray(np.rint(transformed * 255).astype(np.uint8), "RGB").save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--glyph-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    full = Image.open(args.png).convert("RGB")
    page = fitz.open(args.pdf)[0]
    spans = extract_spans(args.pdf)
    drawings, raw_drawings = drawing_rows(args.pdf)
    write_csv(out / "after_final_text_spans_machine.csv", spans)
    write_csv(out / "after_final_drawing_paths_machine.csv", drawings)
    make_overlay(full, args.glyph_csv, out / "after_text_measurement_overlay_300dpi.png")
    # Integer native-pixel crop of the standalone page; no resampling occurs.
    figure_crop_px = (560, 270, 1960, 1130)
    full.save(out / "standalone_300dpi.png")
    full.crop(figure_crop_px).save(out / "figure_crop_300dpi.png")
    ImageOps.grayscale(full).save(out / "grayscale_300dpi.png")
    colorblind(full, np.array(((0.567, 0.433, 0.0), (0.558, 0.442, 0.0), (0.0, 0.242, 0.758)), dtype=np.float32), out / "protanopia_simulated_300dpi.png")
    colorblind(full, np.array(((0.625, 0.375, 0.0), (0.700, 0.300, 0.0), (0.0, 0.300, 0.700)), dtype=np.float32), out / "deuteranopia_simulated_300dpi.png")
    colorblind(full, np.array(((0.950, 0.050, 0.0), (0.0, 0.433, 0.567), (0.0, 0.475, 0.525)), dtype=np.float32), out / "tritanopia_simulated_300dpi.png")
    card_dir = out / "drawing_cards"
    card_dir.mkdir(parents=True, exist_ok=True)
    card_rows = []
    for row, drawing in zip(drawings, raw_drawings):
        isolated = replay_drawing_mask(drawing, page.rect)
        card_rows.append({**row, **card_from_rect(full, row["element_id"], drawing["rect"], card_dir, isolated)})
    write_csv(out / "after_final_drawing_cards_machine.csv", card_rows)
    for suffix, title in (("_original_1x.png", "drawing original native 1x"), ("_target_overlay_1x.png", "drawing target overlay native 1x"), ("_unique_vector_mask_1x.png", "drawing isolated vector mask native 1x"), ("_original_8x_nearest.png", "drawing original 8x nearest")):
        cards = sorted(card_dir.glob(f"*{suffix}"))
        contacts(cards, out / f"drawing_contacts_{suffix[1:].split('.')[0]}", suffix[1:].split(".")[0], title)
    summary = {
        "pdf": str(args.pdf), "page_pt": [page.rect.width, page.rect.height],
        "native_png": str(args.png), "native_px": [full.width, full.height],
        "figure_crop_integer_px_in_standalone": list(figure_crop_px),
        "text_span_count": len(spans), "drawing_path_count": len(drawings),
        "note": "D001-D061 are every get_drawings() record; source-only pattern fills are separately inventoried in manual tables.",
    }
    (out / "after_final_vector_inventory_machine.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
