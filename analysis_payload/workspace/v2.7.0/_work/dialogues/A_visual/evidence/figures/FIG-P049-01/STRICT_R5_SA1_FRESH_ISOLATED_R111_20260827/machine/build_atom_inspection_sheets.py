from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence"
    r"\figures\FIG-P049-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827"
)
MACHINE = ROOT / "machine"
VISUAL = ROOT / "visual"
SCOPE_X0_PT = 126.0
SCOPE_Y0_PT = 60.0
PX_PER_PT = 300.0 / 72.0


def load_atoms():
    with (MACHINE / "atomic_denominator_machine.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def pixel_bbox(atom):
    x0, y0, x1, y1 = json.loads(atom["pdf_bbox_pt"])
    return [
        int((x0 - SCOPE_X0_PT) * PX_PER_PT),
        int((y0 - SCOPE_Y0_PT) * PX_PER_PT),
        int((x1 - SCOPE_X0_PT) * PX_PER_PT + 0.9999),
        int((y1 - SCOPE_Y0_PT) * PX_PER_PT + 0.9999),
    ]


def main():
    atoms = load_atoms()
    glyphs = [a for a in atoms if a["atom_class"] == "VISIBLE_GLYPH"]
    paths = [a for a in atoms if a["atom_class"] == "FOREGROUND_PDF_PATH"]
    with Image.open(VISUAL / "07_atomic_scope_native300dpi_native1x.png") as source_image:
        source = source_image.convert("RGB")
        font = ImageFont.load_default()
        rows = []
        glyph_tiles = []
        for atom in glyphs:
            x0, y0, x1, y1 = pixel_bbox(atom)
            x0c, y0c = max(0, x0), max(0, y0)
            x1c, y1c = min(source.width, x1), min(source.height, y1)
            crop = source.crop((x0c, y0c, x1c, y1c)).convert("L")
            points = [(x, y) for y in range(crop.height) for x in range(crop.width) if crop.getpixel((x, y)) <= 235]
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                ink_bbox = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
                ink_w = ink_bbox[2] - ink_bbox[0]
                ink_h = ink_bbox[3] - ink_bbox[1]
                ink_pixels = len(points)
            else:
                ink_bbox = []
                ink_w = ink_h = ink_pixels = 0
            rows.append(
                {
                    "atom_id": atom["atom_id"],
                    "display": atom["display"],
                    "source_bbox_width_px": x1c - x0c,
                    "source_bbox_height_px": y1c - y0c,
                    "threshold_gray_le": 235,
                    "machine_ink_bbox_local_px": json.dumps(ink_bbox),
                    "machine_ink_width_px": ink_w,
                    "machine_ink_height_px": ink_h,
                    "machine_ink_pixel_count": ink_pixels,
                }
            )
            padded = Image.new("RGB", (max(1, crop.width + 8), max(1, crop.height + 8)), "white")
            padded.paste(source.crop((x0c, y0c, x1c, y1c)), (4, 4))
            factor = min(8, max(2, int(96 / max(padded.width, padded.height))))
            enlarged = padded.resize((padded.width * factor, padded.height * factor), Image.Resampling.NEAREST)
            tile = Image.new("RGB", (112, 136), "white")
            tile.paste(enlarged, ((112 - enlarged.width) // 2, 24 + max(0, (104 - enlarged.height) // 2)))
            tdraw = ImageDraw.Draw(tile)
            tdraw.text((4, 4), f"{atom['atom_id']}  {atom['display']}", fill="black", font=font)
            tdraw.rectangle((0, 0, 111, 135), outline=(170, 170, 170))
            glyph_tiles.append(tile)
        with (MACHINE / "glyph_pixel_measurements_machine.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

        cols = 9
        rows_n = (len(glyph_tiles) + cols - 1) // cols
        glyph_sheet = Image.new("RGB", (cols * 112, rows_n * 136), "white")
        for i, tile in enumerate(glyph_tiles):
            glyph_sheet.paste(tile, ((i % cols) * 112, (i // cols) * 136))
        glyph_sheet.save(VISUAL / "12_all_glyph_ids_inspection_sheet.png")

        path_tiles = []
        for atom in paths:
            x0, y0, x1, y1 = pixel_bbox(atom)
            pad = 32
            crop = source.crop((max(0, x0 - pad), max(0, y0 - pad), min(source.width, x1 + pad), min(source.height, y1 + pad)))
            target_w = 480
            factor = min(5, max(1, target_w // max(1, crop.width)))
            crop = crop.resize((crop.width * factor, crop.height * factor), Image.Resampling.NEAREST)
            tile = Image.new("RGB", (520, 250), "white")
            if crop.width > 510 or crop.height > 218:
                scale = min(510 / crop.width, 218 / crop.height)
                crop = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.NEAREST)
            tile.paste(crop, ((520 - crop.width) // 2, 26 + (218 - crop.height) // 2))
            ImageDraw.Draw(tile).text((6, 6), f"{atom['atom_id']} {atom['display']}", fill="black", font=font)
            path_tiles.append(tile)
        path_sheet = Image.new("RGB", (1040, ((len(path_tiles) + 1) // 2) * 250), "white")
        for i, tile in enumerate(path_tiles):
            path_sheet.paste(tile, ((i % 2) * 520, (i // 2) * 250))
        path_sheet.save(VISUAL / "13_all_path_ids_context_sheet.png")


if __name__ == "__main__":
    main()
