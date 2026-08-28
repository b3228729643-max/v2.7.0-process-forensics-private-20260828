from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "machine" / "object_ledger.csv"
PAGE = ROOT / "renders" / "full_page_300dpi.png"
OUT = ROOT / "review"


def parse_box(raw: str) -> tuple[int, int, int, int]:
    values = json.loads(raw)
    return tuple(int(v) for v in values)


def fit_nearest(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = min(width / image.width, height / image.height)
    target = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(target, Image.Resampling.NEAREST)


def tile(original: Image.Image, mask: Image.Image, label: str) -> Image.Image:
    mask_l = mask.convert("L")
    overlay = original.convert("RGBA")
    red = Image.new("RGBA", original.size, (230, 20, 20, 235))
    overlay.alpha_composite(Image.composite(red, Image.new("RGBA", original.size, (0, 0, 0, 0)), mask_l))
    mask_only = Image.new("RGB", original.size, "white")
    mask_only.paste(Image.new("RGB", original.size, "black"), mask=mask_l)

    canvas = Image.new("RGB", (900, 290), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 7), label, fill="black", font=ImageFont.load_default())
    for col, (name, view) in enumerate((
        ("ORIGINAL", original.convert("RGB")),
        ("TARGET OVERLAY", overlay.convert("RGB")),
        ("MASK ONLY", mask_only),
    )):
        x0 = col * 300
        draw.text((x0 + 8, 27), name, fill=(60, 60, 60), font=ImageFont.load_default())
        fitted = fit_nearest(view, 280, 235)
        x = x0 + 10 + (280 - fitted.width) // 2
        y = 48 + (235 - fitted.height) // 2
        canvas.paste(fitted, (x, y))
    return canvas


def main() -> None:
    with LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["kind"] == "GRAPHIC"]
    page = Image.open(PAGE).convert("RGB")
    sheet_paths = sorted(OUT.glob("graphic_contact_sheet_*.png"))
    for path in sheet_paths:
        path.unlink()

    index = []
    for sheet_no, start in enumerate(range(0, len(rows), 12), 1):
        group = rows[start : start + 12]
        sheet = Image.new("RGB", (1800, 1740), (238, 240, 243))
        for local, row in enumerate(group):
            x0, y0, x1, y1 = parse_box(row["bbox_px"])
            original = page.crop((x0, y0, x1, y1))
            mask = Image.open(ROOT / row["mask_path"]).convert("L")
            if mask.size != original.size:
                raise ValueError(f"mask size mismatch for {row['id']}: {mask.size} != {original.size}")
            label = f"{row['id']} {row['graphic_type']} seq={row['drawing_seqno']} px={row['mask_pixel_count']}"
            cell = tile(original, mask, label)
            col = local % 2
            line = local // 2
            sheet.paste(cell, (col * 900, line * 290))
        name = f"graphic_contact_sheet_{sheet_no:03d}.png"
        sheet.save(OUT / name)
        index.append({
            "sheet": name,
            "object_count": len(group),
            "first_id": group[0]["id"],
            "last_id": group[-1]["id"],
            "native_dimensions": list(sheet.size),
        })
    (ROOT / "machine" / "graphic_contact_sheet_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"graphic_objects": len(rows), "sheets": len(index)}))


if __name__ == "__main__":
    main()
