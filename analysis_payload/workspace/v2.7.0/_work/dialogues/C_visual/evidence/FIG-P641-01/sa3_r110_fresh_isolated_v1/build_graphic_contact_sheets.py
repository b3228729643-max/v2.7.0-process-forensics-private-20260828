from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PAGE = Image.open(ROOT / "full_page_300dpi_native.png").convert("RGB")


def font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def fit_nearest(im: Image.Image, box: tuple[int, int]) -> Image.Image:
    scale = min(box[0] / im.width, box[1] / im.height)
    size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
    return im.resize(size, Image.Resampling.NEAREST)


with (ROOT / "graphics_inventory.csv").open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

out_dir = ROOT / "graphic_contact_sheets"
out_dir.mkdir(exist_ok=True)
cell_w, cell_h = 1260, 560
for sheet_i in range(3):
    sheet = Image.new("RGB", (cell_w * 2, cell_h * 3), "white")
    draw = ImageDraw.Draw(sheet)
    for slot, row in enumerate(rows[sheet_i * 6 : sheet_i * 6 + 6]):
        col, rr = slot % 2, slot // 2
        ox, oy = col * cell_w, rr * cell_h
        x0, y0, x1, y1 = map(int, row["bbox_px"].split(","))
        pad = 18
        cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
        cx1, cy1 = min(PAGE.width, x1 + pad), min(PAGE.height, y1 + pad)
        original = PAGE.crop((cx0, cy0, cx1, cy1))
        object_mask = Image.open(ROOT / row["mask_path"]).convert("L")
        canvas_mask = Image.new("L", original.size, 0)
        canvas_mask.paste(object_mask, (x0 - cx0, y0 - cy0))
        overlay = original.copy()
        red = Image.new("RGB", original.size, (255, 0, 0))
        overlay.paste(red, mask=canvas_mask)
        mask_view = Image.new("RGB", original.size, "black")
        white = Image.new("RGB", original.size, "white")
        mask_view.paste(white, mask=canvas_mask)
        title = f'{row["object_id"]} class={row["object_class"]} ink={row["ink_area_px"]}px'
        draw.text((ox + 8, oy + 6), title, fill="black", font=font(19))
        for k, (label, panel) in enumerate((
            ("ORIGINAL", original), ("TARGET OVERLAY", overlay), ("MASK ONLY", mask_view)
        )):
            px = ox + 8 + k * 414
            draw.text((px, oy + 36), label, fill="black", font=font(16))
            fitted = fit_nearest(panel, (395, 480))
            sheet.paste(fitted, (px, oy + 68))
    sheet.save(out_dir / f"graphic_contact_sheet_{sheet_i + 1:02d}.png")

print(f"graphic_objects={len(rows)} sheets=3")
