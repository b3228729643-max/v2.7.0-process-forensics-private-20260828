#!/usr/bin/env python3
"""Create provenance-sealed, native-1x glyph masks for FIG-P608-01.

The old review cards remain the human original/overlay/8x views.  This helper
does *not* accept their bbox threshold as an object identity.  For every
native target crop it independently verifies that each retained dark pixel is
chromatically compatible with the rawdict glyph colour composited toward
white.  The resulting mask is kept in the unpadded native target coordinate
system used by all relation tools.  No resampling or morphology is used, and
the script writes no manual-acceptance verdict.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


DPI = 300
S = DPI / 72.0


def pxbox(row, image):
    return (
        max(0, math.floor(float(row["x0_pt"]) * S)),
        max(0, math.floor(float(row["y0_pt"]) * S)),
        min(image.width, math.ceil(float(row["x1_pt"]) * S)),
        min(image.height, math.ceil(float(row["y1_pt"]) * S)),
    )


def rgb_from_pdf_int(value):
    n = int(value)
    return np.array(((n >> 16) & 255, (n >> 8) & 255, n & 255), dtype=float)


def seal_mask(native, rgb):
    """Return a non-morphological chromatic source-compatible mask.

    A glyph is painted from its rawdict RGB toward a light substrate.  Pixels
    belonging to an unrelated blue/gold/hatch object do not lie on that colour
    line, so they cannot be silently carried into a glyph relationship mask.
    The underlying raw threshold remains recorded only as a reconciliation
    source, never as the sole identity proof.
    """
    arr = np.asarray(native.convert("RGB"), dtype=float)
    candidate = arr.min(axis=2) < 230
    toward_white = 255.0 - rgb
    displacement = arr - rgb
    denom = float(np.dot(toward_white, toward_white))
    t = (displacement * toward_white).sum(axis=2) / denom
    residual = np.sqrt(((displacement - t[..., None] * toward_white) ** 2).sum(axis=2))
    compatible = (t >= -0.02) & (t <= 1.05) & (residual <= 2.0)
    return candidate, candidate & compatible, residual


def contact(paths, out, title):
    ims = [Image.open(p).convert("RGB") for p in paths]
    cols, per_sheet, pad, label_h = 3, 6, 12, 24
    for start in range(0, len(paths), per_sheet):
        part = ims[start:start + per_sheet]
        names = paths[start:start + per_sheet]
        cell_w = max(i.width for i in part) + 2 * pad
        cell_h = max(i.height for i in part) + 2 * pad + label_h
        rows = math.ceil(len(part) / cols)
        sheet = Image.new("RGB", (cols * cell_w, 36 + rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((pad, 8), title, fill="black")
        for n, (im, path) in enumerate(zip(part, names)):
            col, row = n % cols, n // cols
            x, y = col * cell_w + pad, 36 + row * cell_h + label_h + pad
            sheet.paste(im, (x, y))
            draw.text((x, y - label_h), path.name.split("_")[0], fill="black")
            draw.rectangle((col * cell_w, 36 + row * cell_h,
                            (col + 1) * cell_w - 1, 36 + (row + 1) * cell_h - 1), outline="gray")
        sheet.save(out / f"sealed_unique_mask_1x_sheet_{start // per_sheet + 1:02d}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", type=Path, required=True)
    ap.add_argument("--glyph-csv", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    masks = args.out / "sealed_unique_glyph_masks"
    contacts = args.out / "sealed_mask_contacts"
    masks.mkdir(parents=True, exist_ok=True)
    contacts.mkdir(parents=True, exist_ok=True)
    image = Image.open(args.png).convert("RGB")
    with args.glyph_csv.open("r", newline="", encoding="utf-8-sig") as fh:
        glyphs = list(csv.DictReader(fh))
    rows, paths = [], []
    for row in glyphs:
        box = pxbox(row, image)
        native = image.crop(box)
        candidate, sealed, residual = seal_mask(native, rgb_from_pdf_int(row["color"]))
        path = masks / f"{row['glyph_id']}_sealed_unique_mask_1x.png"
        Image.fromarray(np.where(sealed, 0, 255).astype(np.uint8), "L").save(path)
        paths.append(path)
        ys, xs = np.where(sealed)
        rows.append({
            "glyph_id": row["glyph_id"], "char": row["char"], "codepoint": row["codepoint"],
            "font": row["font"], "effective_pt": row["font_size_pt"], "rotation_deg": row["rotation_deg"],
            "native_target_px": str(box), "raw_threshold_area_px": int(candidate.sum()),
            "sealed_unique_area_px": int(sealed.sum()),
            "removed_non_glyph_candidate_px": int(candidate.sum() - sealed.sum()),
            "candidate_missing_after_seal_px": int(candidate.sum() - sealed.sum()),
            "max_colorline_residual_of_retained_px": "" if not sealed.any() else f"{float(residual[sealed].max()):.4f}",
            "sealed_h_ink_px": 0 if not len(ys) else int(ys.max() - ys.min() + 1),
            "sealed_w_ink_px": 0 if not len(xs) else int(xs.max() - xs.min() + 1),
            "mask_filename": path.name,
            "machine_identity_method": "rawdict_RGB_to_white_colorline_at_native_1x; no_bbox_only_identity; no_morphology",
            "manual_decision": "PENDING_MANUAL_LEDGER",
        })
    with (args.out / "glyph_mask_seal_machine.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    contact(paths, contacts, "FIG-P608-01 sealed glyph-only masks, native 1x")
    (args.out / "glyph_mask_seal_method.json").write_text(json.dumps({
        "native_coordinate": "direct 300dpi raster, no scale/morphology",
        "threshold_reconciliation": "RGB min < 230 is compared but never used alone",
        "identity": "rawdict foreground RGB chromatic-line compatibility",
        "manual": "All glyph decisions remain pending until original/overlay/mask/8x visual ledger is written",
        "visible_slots": sum(1 for r in rows if r["char"].strip()),
        "whitespace_slots": sum(1 for r in rows if not r["char"].strip()),
    }, indent=2), encoding="utf-8")
    print(json.dumps({"glyphs": len(rows), "sealed_area_total": sum(r["sealed_unique_area_px"] for r in rows),
                      "removed_total": sum(r["removed_non_glyph_candidate_px"] for r in rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
