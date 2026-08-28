from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "pair_contact_sheets"
OUT.mkdir(exist_ok=True)
font = ImageFont.load_default()

with (ROOT / "machine_critical_pair_index.csv").open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))

cell_w, cell_h = 500, 230
cols, rows_per_sheet = 2, 20
for sheet_no, start in enumerate(range(0, len(rows), rows_per_sheet), 1):
    batch = rows[start : start + rows_per_sheet]
    canvas = Image.new("RGB", (cols * cell_w, 10 * cell_h + 30), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 8), f"FIG-P067-01 independent near-pair overview {sheet_no:02d}", fill="black", font=font)
    for offset, row in enumerate(batch):
        col, line = offset % cols, offset // cols
        x, y = col * cell_w, 30 + line * cell_h
        overlay_path = ROOT / "critical_pairs" / row["evidence_overlay_1x"]
        original_path = ROOT / "critical_pairs" / row["evidence_original_1x"]
        original = Image.open(original_path).convert("RGB")
        overlay = Image.open(overlay_path).convert("RGB")
        max_w, max_h = 238, 165
        scale = min(max_w / max(original.width, 1), max_h / max(original.height, 1), 1.0)
        size = (max(1, int(original.width * scale)), max(1, int(original.height * scale)))
        original = original.resize(size, Image.Resampling.LANCZOS)
        overlay = overlay.resize(size, Image.Resampling.LANCZOS)
        header = (
            f"{row['pair_id']} {row['a_id']}:{row['a_role']} / {row['b_id']}:{row['b_role']} "
            f"ov={row['raw_mask_intersection_px']} clr={row['raw_mask_clearance_px']}"
        )
        draw.text((x + 6, y + 4), header[:105], fill="black", font=font)
        canvas.paste(original, (x + 6, y + 26))
        canvas.paste(overlay, (x + 256, y + 26))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(180, 180, 180), width=1)
    canvas.save(OUT / f"pair_overview_{sheet_no:02d}.png")

print(f"pair_rows={len(rows)} sheets={(len(rows) + rows_per_sheet - 1) // rows_per_sheet}")
