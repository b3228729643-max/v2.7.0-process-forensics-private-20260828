from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CONTACTS = ROOT / "contacts"
CRITICAL = ROOT / "critical"
FONT = ImageFont.load_default()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def labeled_native_row(row_id: str, paths: list[Path], labels: list[str]) -> Image.Image:
    images = [Image.open(path).convert("RGB") for path in paths]
    title_h = 18
    gap = 4
    widths = [image.width for image in images]
    width = sum(widths) + gap * (len(images) - 1)
    height = title_h + max(image.height for image in images)
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((2, 2), f"{row_id} | " + " | ".join(labels), fill="black", font=FONT)
    x = 0
    for image in images:
        canvas.paste(image, (x, title_h))
        x += image.width + gap
    return canvas


def stack_rows(rows: list[Image.Image], output: Path) -> None:
    gap = 6
    width = max(image.width for image in rows)
    height = sum(image.height for image in rows) + gap * (len(rows) - 1)
    sheet = Image.new("RGB", (width, height), "white")
    y = 0
    for image in rows:
        sheet.paste(image, (0, y))
        y += image.height + gap
    sheet.save(output)


glyph_rows = read_csv(ROOT / "inventory" / "glyph_inventory.csv")
for sheet_number in range(1, (len(glyph_rows) + 3) // 4 + 1):
    chunk = glyph_rows[(sheet_number - 1) * 4: sheet_number * 4]
    rows = [
        labeled_native_row(
            row["object_id"],
            [ROOT / row["original_1x"], ROOT / row["overlay_1x"], ROOT / row["mask_only_1x"]],
            ["ORIGINAL_NATIVE_1X", "TARGET_OVERLAY_NATIVE_1X", "MASK_ONLY_NATIVE_1X"],
        )
        for row in chunk
    ]
    stack_rows(rows, CONTACTS / f"glyph_native_1x_sheet_{sheet_number:03d}.png")


graphic_rows = read_csv(ROOT / "inventory" / "graphic_path_inventory.csv")
for sheet_number in range(1, (len(graphic_rows) + 3) // 4 + 1):
    chunk = graphic_rows[(sheet_number - 1) * 4: sheet_number * 4]
    rows = [
        labeled_native_row(
            row["object_id"],
            [ROOT / row["original_1x"], ROOT / row["overlay_1x"], ROOT / row["mask_only_1x"]],
            ["ORIGINAL_NATIVE_1X", "TARGET_OVERLAY_NATIVE_1X", "MASK_ONLY_NATIVE_1X"],
        )
        for row in chunk
    ]
    stack_rows(rows, CONTACTS / f"graphic_native_1x_sheet_{sheet_number:03d}.png")
    cards = [Image.open(ROOT / row["card_8x"]).convert("RGB") for row in chunk]
    stack_rows(cards, CONTACTS / f"graphic_sheet_{sheet_number:03d}.png")


critical_rows = read_csv(ROOT / "ledgers" / "critical_pair_manual_review.csv")
for row in critical_rows:
    pair_id = row["pair_id"]
    native_paths = [
        CRITICAL / f"{pair_id}_raw_1x.png",
        CRITICAL / f"{pair_id}_overlay_1x.png",
        CRITICAL / f"{pair_id}_intersection_1x.png",
        CRITICAL / f"{pair_id}_A_mask_1x.png",
        CRITICAL / f"{pair_id}_B_mask_1x.png",
    ]
    native_row = labeled_native_row(
        pair_id,
        native_paths,
        ["RAW_NATIVE_1X", "OVERLAY_NATIVE_1X", "INTERSECTION_NATIVE_1X", "A_MASK_NATIVE_1X", "B_MASK_NATIVE_1X"],
    )
    native_row.save(CRITICAL / f"{pair_id}_native_1x_contact.png")


print({
    "glyph_native_1x_sheets": (len(glyph_rows) + 3) // 4,
    "graphic_native_1x_sheets": (len(graphic_rows) + 3) // 4,
    "graphic_8x_sheets": (len(graphic_rows) + 3) // 4,
    "critical_native_1x_contacts": len(critical_rows),
})
