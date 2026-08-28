#!/usr/bin/env python3
"""Native-300-dpi evidence helpers for FIG-P608-01.

The helpers never resize a measurement image.  They only crop native pixels,
threshold a crop for a review mask, or enlarge an already-measured crop by
nearest neighbour for human inspection.  They intentionally do not perform
morphology, interpolation, or automatic manual-acceptance decisions.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw


DPI = 300
PX_PER_PT = DPI / 72.0


def _pxbox(box_pt: tuple[float, float, float, float], image: Image.Image, pad: int = 0):
    x0, y0, x1, y1 = box_pt
    left = max(0, math.floor(x0 * PX_PER_PT) - pad)
    top = max(0, math.floor(y0 * PX_PER_PT) - pad)
    right = min(image.width, math.ceil(x1 * PX_PER_PT) + pad)
    bottom = min(image.height, math.ceil(y1 * PX_PER_PT) + pad)
    return left, top, right, bottom


def collect_glyphs(pdf: Path, page_index: int, scope: tuple[float, float, float, float]):
    doc = fitz.open(pdf)
    page = doc[page_index]
    raw = page.get_text("rawdict")
    sx0, sy0, sx1, sy1 = scope
    rows = []
    gid = 0
    span_id = 0
    for bidx, block in enumerate(raw["blocks"]):
        if block["type"] != 0:
            continue
        for lidx, line in enumerate(block["lines"]):
            direction = line.get("dir", (1.0, 0.0))
            dx, dy = float(direction[0]), float(direction[1])
            if abs(dx) >= abs(dy):
                rotation_deg = 0 if dx >= 0 else 180
                local_axis = "PAGE_X"
            else:
                # The precise sign only records reading direction.  Both 90-degree
                # cases must swap page H/W before applying local-text glyph gates.
                rotation_deg = 90 if dy < 0 else 270
                local_axis = "PAGE_Y_ROTATED"
            for sidx, span in enumerate(line["spans"]):
                span_id += 1
                for cidx, char in enumerate(span["chars"]):
                    x0, y0, x1, y1 = char["bbox"]
                    if x1 < sx0 or x0 > sx1 or y1 < sy0 or y0 > sy1:
                        continue
                    gid += 1
                    rows.append({
                        "glyph_id": f"G{gid:03d}",
                        "span_id": f"T{span_id:03d}",
                        "block": bidx,
                        "line": lidx,
                        "span": sidx,
                        "char_index": cidx,
                        "char": char["c"],
                        "codepoint": f"U+{ord(char['c']):04X}",
                        "font": span.get("font", ""),
                        "font_size_pt": round(float(span.get("size", 0)), 5),
                        "color": span.get("color", 0),
                        "line_dir_x": round(dx, 5),
                        "line_dir_y": round(dy, 5),
                        "rotation_deg": rotation_deg,
                        "local_text_axis": local_axis,
                        "x0_pt": round(x0, 5),
                        "y0_pt": round(y0, 5),
                        "x1_pt": round(x1, 5),
                        "y1_pt": round(y1, 5),
                    })
    return rows


def raw_mask(image: Image.Image, box_pt: tuple[float, float, float, float], threshold: int):
    """Return only the native-pixel crop and a no-morphology dark-ink mask."""
    crop_box = _pxbox(box_pt, image, 0)
    crop = image.crop(crop_box).convert("RGB")
    arr = np.asarray(crop)
    mask = arr.min(axis=2) < threshold
    return crop_box, crop, mask


def save_glyph_artifacts(image: Image.Image, rows: list[dict], output_dir: Path, threshold: int = 230, pad: int = 3):
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = []
    for row in rows:
        box = tuple(float(row[k]) for k in ("x0_pt", "y0_pt", "x1_pt", "y1_pt"))
        outer = _pxbox(box, image, pad)
        original = image.crop(outer).convert("RGB")
        inner = _pxbox(box, image, 0)
        draw = ImageDraw.Draw(original)
        draw.rectangle((inner[0]-outer[0], inner[1]-outer[1], inner[2]-outer[0]-1, inner[3]-outer[1]-1), outline=(255, 0, 0), width=1)
        _, raw, mask = raw_mask(image, box, threshold)
        mask_img = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L")
        gid = row["glyph_id"]
        original_path = output_dir / f"{gid}_original_1x.png"
        overlay_path = output_dir / f"{gid}_target_overlay_1x.png"
        mask_path = output_dir / f"{gid}_unique_rawmask_1x.png"
        zoom_path = output_dir / f"{gid}_original_8x_nearest.png"
        image.crop(outer).convert("RGB").save(original_path)
        original.save(overlay_path)
        mask_img.save(mask_path)
        image.crop(outer).convert("RGB").resize((original.width * 8, original.height * 8), Image.Resampling.NEAREST).save(zoom_path)
        ys, xs = np.where(mask)
        metrics.append({
            **row,
            "raw_mask_threshold_rgb_min_lt": threshold,
            "raw_mask_area_px": int(mask.sum()),
            "raw_mask_h_ink_px": int(ys.max()-ys.min()+1) if len(ys) else 0,
            "raw_mask_w_ink_px": int(xs.max()-xs.min()+1) if len(xs) else 0,
            "local_h_ink_px": int((xs.max()-xs.min()+1) if len(xs) and row["local_text_axis"] == "PAGE_Y_ROTATED" else (ys.max()-ys.min()+1) if len(ys) else 0),
            "local_w_ink_px": int((ys.max()-ys.min()+1) if len(ys) and row["local_text_axis"] == "PAGE_Y_ROTATED" else (xs.max()-xs.min()+1) if len(xs) else 0),
            "original_1x": str(original_path.name),
            "overlay_1x": str(overlay_path.name),
            "mask_1x": str(mask_path.name),
            "nearest_8x": str(zoom_path.name),
        })
    return metrics


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    names = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        writer.writerows(rows)


def parse_scope(s: str):
    vals = tuple(float(x) for x in s.split(","))
    if len(vals) != 4:
        raise ValueError("scope must be x0,y0,x1,y1 in PDF points")
    return vals


def make_contacts(cards: list[Path], output: Path, columns: int = 3, title: str = ""):
    if not cards:
        raise ValueError("no cards")
    ims = [Image.open(p).convert("RGB") for p in cards]
    pad = 12
    label_h = 28
    cell_w = max(im.width for im in ims) + 2 * pad
    cell_h = max(im.height for im in ims) + label_h + 2 * pad
    rows = math.ceil(len(ims) / columns)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h + (36 if title else 0)), "white")
    draw = ImageDraw.Draw(sheet)
    yoff = 36 if title else 0
    if title:
        draw.text((pad, 8), title, fill="black")
    for idx, (path, im) in enumerate(zip(cards, ims), 1):
        col = (idx - 1) % columns
        row = (idx - 1) // columns
        x = col * cell_w + pad
        y = yoff + row * cell_h + label_h + pad
        sheet.paste(im, (x, y))
        draw.text((x, y - label_h + 3), path.name.split("_")[0], fill="black")
        draw.rectangle((col * cell_w, yoff + row * cell_h, (col + 1) * cell_w - 1, yoff + (row + 1) * cell_h - 1), outline="gray")
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("glyphs")
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--page", type=int, required=True, help="zero-based page index")
    p.add_argument("--scope", required=True)
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--json", type=Path, required=True)
    q = sub.add_parser("artifacts")
    q.add_argument("--png", type=Path, required=True)
    q.add_argument("--glyph-csv", type=Path, required=True)
    q.add_argument("--out", type=Path, required=True)
    q.add_argument("--metrics", type=Path, required=True)
    q.add_argument("--threshold", type=int, default=230)
    r = sub.add_parser("contacts")
    r.add_argument("--dir", type=Path, required=True)
    r.add_argument("--suffix", required=True)
    r.add_argument("--out-dir", type=Path, required=True)
    r.add_argument("--per-sheet", type=int, default=6)
    r.add_argument("--columns", type=int, default=3)
    r.add_argument("--title", default="")
    args = parser.parse_args()
    if args.cmd == "glyphs":
        rows = collect_glyphs(args.pdf, args.page, parse_scope(args.scope))
        write_csv(args.csv, rows)
        args.json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"glyph_count": len(rows), "scope_pt": parse_scope(args.scope)}, ensure_ascii=False))
    elif args.cmd == "artifacts":
        with args.glyph_csv.open("r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        metrics = save_glyph_artifacts(Image.open(args.png), rows, args.out, args.threshold)
        write_csv(args.metrics, metrics)
        print(json.dumps({"artifact_count": len(metrics), "threshold": args.threshold}, ensure_ascii=False))
    else:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        cards = sorted(args.dir.glob(f"*{args.suffix}"))
        for start in range(0, len(cards), args.per_sheet):
            part = cards[start:start + args.per_sheet]
            out = args.out_dir / f"{args.suffix.strip('.').replace('*','')}_sheet_{start//args.per_sheet+1:02d}.png"
            make_contacts(part, out, args.columns, args.title)
        print(json.dumps({"card_count": len(cards), "sheet_count": math.ceil(len(cards)/args.per_sheet)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
