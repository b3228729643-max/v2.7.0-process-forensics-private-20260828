from __future__ import annotations

import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825")
OUT = ROOT / "contact_sheets" / "critical"
ROWS_PER_SHEET = 18
COLS = 3
CELL_W = 720
CELL_H = 470
LABEL_H = 70


def fit_image(source: Image.Image, width: int, height: int) -> Image.Image:
    scale = min(width / source.width, height / source.height)
    size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
    return source.resize(size, Image.Resampling.NEAREST)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("critical_contact_*.png"):
        old.unlink()
    with (ROOT / "CRITICAL_PAIR_LEDGER.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 173:
        raise RuntimeError(f"critical denominator changed: {len(rows)} != 173")
    dirs = {p.name.split("_", 1)[0]: p for p in (ROOT / "critical_pairs").iterdir() if p.is_dir()}
    if set(dirs) != {r["PAIR_ID"] for r in rows}:
        raise RuntimeError("critical directory set does not match critical ledger")
    font = ImageFont.load_default()
    sheet_count = math.ceil(len(rows) / ROWS_PER_SHEET)
    for sheet_index in range(sheet_count):
        subset = rows[sheet_index * ROWS_PER_SHEET : (sheet_index + 1) * ROWS_PER_SHEET]
        row_count = math.ceil(len(subset) / COLS)
        canvas = Image.new("RGB", (COLS * CELL_W, row_count * CELL_H), "white")
        draw = ImageDraw.Draw(canvas)
        for cell_index, row in enumerate(subset):
            col = cell_index % COLS
            grid_row = cell_index // COLS
            x0, y0 = col * CELL_W, grid_row * CELL_H
            pair_id = row["PAIR_ID"]
            source_path = dirs[pair_id] / "OVERLAY_8X_NEAREST.png"
            with Image.open(source_path) as source:
                thumb = fit_image(source.convert("RGB"), CELL_W - 16, CELL_H - LABEL_H - 16)
            ix = x0 + (CELL_W - thumb.width) // 2
            iy = y0 + LABEL_H + (CELL_H - LABEL_H - thumb.height) // 2
            canvas.paste(thumb, (ix, iy))
            decision = row["DECISION"]
            color = (190, 0, 0) if decision == "FAIL" else (0, 105, 55)
            label1 = f"{pair_id} {row['A_ID']} <-> {row['B_ID']} {row['CATEGORY']} {decision}"
            label2 = f"overlap={row['OVERLAP_PIXEL_COUNT']} clearance={row['MIN_CLEARANCE_PX']} gate={row['HARD_GATE_PX'] or '-'} allowed={row['ALLOWED_DESIGN_RELATION']}"
            draw.text((x0 + 8, y0 + 8), label1, font=font, fill=color)
            draw.text((x0 + 8, y0 + 34), label2, font=font, fill=(25, 25, 25))
            draw.rectangle((x0, y0, x0 + CELL_W - 1, y0 + CELL_H - 1), outline=(190, 190, 190), width=1)
        path = OUT / f"critical_contact_{sheet_index + 1:02d}.png"
        canvas.save(path, optimize=True)
    print(f"CRITICAL_CONTACT_COMPLETE rows={len(rows)} sheets={sheet_count}")


if __name__ == "__main__":
    main()
