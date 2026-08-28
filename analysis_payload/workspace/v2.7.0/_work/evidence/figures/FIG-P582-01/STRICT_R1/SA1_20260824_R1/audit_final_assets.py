"""Render-only auxiliary artifacts for the frozen FIG-P582-01 audit.

This does not make a pass/fail determination.  It only projects already-measured
native-PDF coordinates into a labelled review overlay and copies the existing
object inventory into compact machine-readable listings.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent


def main() -> None:
    inventory_path = ROOT / "object_inventory.csv"
    manifest = json.loads((ROOT / "render_manifest.json").read_text(encoding="utf-8"))
    # object_inventory.csv is already expressed in the native 300-dpi figure
    # crop system (not the full-page system), as established by audit_measure.
    # Keep those raw coordinates unchanged for the required 1:1 overlay.
    _crop = manifest["figure_crop_native_300dpi_xyxy"]

    with inventory_path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    # The inventory coordinates are in the 300-dpi full-page system.  The
    # figure crop is a native integer crop, so subtract only its integer origin.
    image = Image.open(ROOT / "figure_crop_300dpi.png").convert("RGB")
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    for row in rows:
        if row["OBJECT_KIND"] not in {"TEXT", "FORMULA"}:
            continue
        x0 = int(float(row["BBOX_X0"]))
        y0 = int(float(row["BBOX_Y0"]))
        x1 = int(float(row["BBOX_X1"]))
        y1 = int(float(row["BBOX_Y1"]))
        draw.rectangle((x0, y0, x1, y1), outline=(220, 0, 0), width=1)
        draw.text((x0, max(0, y0 - 11)), row["OBJECT_ID"], fill=(220, 0, 0))
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    with (ROOT / "semantic_text_inventory_machine.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        out = csv.DictWriter(
            fh,
            fieldnames=[
                "ELEMENT_ID", "CATEGORY", "EXACT_NATIVE_PDF_TEXT", "SOURCE_FILE",
                "SOURCE_LINE", "FINAL_VISIBLE_MASK", "BBOX_NATIVE_300DPI",
            ],
        )
        out.writeheader()
        for row in rows:
            if row["OBJECT_KIND"] not in {"TEXT", "FORMULA"}:
                continue
            out.writerow({
                "ELEMENT_ID": row["OBJECT_ID"],
                "CATEGORY": row["CATEGORY"],
                "EXACT_NATIVE_PDF_TEXT": row["NAME_OR_TEXT"],
                "SOURCE_FILE": row["SOURCE_FILE"],
                "SOURCE_LINE": row["SOURCE_LINE"],
                "FINAL_VISIBLE_MASK": row["FINAL_VISIBLE_MASK"],
                "BBOX_NATIVE_300DPI": ",".join(
                    row[k] for k in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1")
                ),
            })

    with (ROOT / "graphic_object_inventory.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        out = csv.DictWriter(
            fh,
            fieldnames=[
                "OBJECT_ID", "CATEGORY", "NAME_OR_TEXT", "DRAW_ORDER",
                "FINAL_VISIBLE_MASK", "PRE_OCCLUSION_MASK", "HALO_OR_BACKGROUND",
                "BBOX_NATIVE_300DPI", "MASK_FOREGROUND_PX", "EMPTY_MASK",
            ],
        )
        out.writeheader()
        for row in rows:
            if row["OBJECT_KIND"] != "GRAPHIC":
                continue
            out.writerow({
                "OBJECT_ID": row["OBJECT_ID"],
                "CATEGORY": row["CATEGORY"],
                "NAME_OR_TEXT": row["NAME_OR_TEXT"],
                "DRAW_ORDER": row["DRAW_ORDER"],
                "FINAL_VISIBLE_MASK": row["FINAL_VISIBLE_MASK"],
                "PRE_OCCLUSION_MASK": row["PRE_OCCLUSION_MASK"],
                "HALO_OR_BACKGROUND": row["HALO_OR_BACKGROUND"],
                "BBOX_NATIVE_300DPI": ",".join(
                    row[k] for k in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1")
                ),
                "MASK_FOREGROUND_PX": row["MASK_FOREGROUND_PX"],
                "EMPTY_MASK": row["EMPTY_MASK"],
            })

    # Native-size per-glyph overlays: these are rendered in exactly the raw
    # mask bbox.  Contact sheets provide the enlarged human view; these files
    # preserve the sole counting coordinate (1:1) for every glyph.
    target_dir = ROOT / "glyph_target_overlay"
    target_dir.mkdir(exist_ok=True)
    for original in sorted((ROOT / "glyph_original").glob("G*_original_1x.png")):
        glyph_id = original.name.split("_")[0]
        mask_path = ROOT / "glyph_masks" / f"{glyph_id}_mask_only_1x.png"
        base = Image.open(original).convert("RGB")
        mask = Image.open(mask_path).convert("L")
        px = base.load()
        mp = mask.load()
        for y in range(base.height):
            for x in range(base.width):
                if mp[x, y] < 128:
                    px[x, y] = (255, 0, 0)
        base.save(target_dir / f"{glyph_id}_target_overlay_1x.png")


if __name__ == "__main__":
    main()
