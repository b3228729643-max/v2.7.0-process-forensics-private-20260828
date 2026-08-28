"""Build native-pixel graphic-object review cards for the 69-object census.

This is evidence tooling only.  It reads the already frozen candidate render and
the audit's per-object masks; it never alters the PDF or TeX source.  Every
semantic GRAPHIC object receives a raw native crop, a uniquely coloured mask
overlay, and a mask-only tile.  G031 deliberately uses its separately stored
white opaque-path geometry: its final dark-foreground mask is empty by design.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


OUT = Path(__file__).resolve().parent
PAGE = OUT / "full_page_native_300dpi-801.png"
OBJECTS = OUT / "object_inventory.json"
CARD_DIR = OUT / "graphic_object_cards_native"
SHEET_DIR = OUT / "graphic_object_contact_sheets"


def safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def mask_for(obj: dict) -> tuple[np.ndarray, str, tuple[int, int, int, int]]:
    # White opaque PDF fills do not leave dark foreground pixels, so their
    # separate geometry mask is the only truthful way to display the actual
    # occluding path.  Dark badge fills remain represented by final pixels.
    use_opaque_geometry = bool(obj.get("empty_allowed", False) and obj["opaque_geometry_mask_file"])
    rel = obj["opaque_geometry_mask_file"] if use_opaque_geometry else obj["mask_file"]
    data = np.asarray(Image.open(OUT / rel).convert("L")) > 0
    bbox = tuple(obj["opaque_geometry_bbox"]) if use_opaque_geometry else tuple(obj["bbox"])
    return data, "OPAQUE_PATH_GEOMETRY" if use_opaque_geometry else "FINAL_VISIBLE_MASK", bbox


def card(page: np.ndarray, obj: dict) -> tuple[Image.Image, dict]:
    mask, kind, selected_bbox = mask_for(obj)
    x0, y0, x1, y1 = map(int, selected_bbox)
    expected = (max(1, y1 - y0), max(1, x1 - x0))
    if mask.shape != expected:
        raise RuntimeError(f"{obj['id']} mask shape {mask.shape} does not match bbox {expected}")
    pad = 3
    px0, py0 = max(0, x0 - pad), max(0, y0 - pad)
    px1, py1 = min(page.shape[1], x1 + pad), min(page.shape[0], y1 + pad)
    raw = page[py0:py1, px0:px1].copy()
    local = np.zeros(raw.shape[:2], dtype=bool)
    local[y0 - py0:y1 - py0, x0 - px0:x1 - px0] = mask
    overlay = raw.copy()
    # Cyan is reserved for the intentionally white G031 separator; red is
    # used for every other final-visible component.
    colour = (0, 220, 255) if obj.get("empty_allowed", False) and obj["opaque_geometry_mask_file"] else (255, 0, 0)
    overlay[local] = colour
    mono = np.zeros_like(raw)
    mono[local] = colour
    scale = 2
    imgs = [Image.fromarray(a).resize((a.shape[1] * scale, a.shape[0] * scale), Image.Resampling.NEAREST)
            for a in (raw, overlay, mono)]
    header = 29
    canvas = Image.new("RGB", (sum(im.width for im in imgs) + 8, max(im.height for im in imgs) + header), "white")
    d = ImageDraw.Draw(canvas)
    d.text((2, 2), f"{obj['id']} | {obj['role']} | {kind}", fill="black")
    d.text((2, 15), "native 1x crop     unique-mask overlay (2x nearest)     mask only (2x nearest)", fill="black")
    xpos = 2
    for im in imgs:
        canvas.paste(im, (xpos, header))
        xpos += im.width + 2
    row = {
        "OBJECT_ID": obj["id"], "ROLE": obj["role"], "DRAWING_INDEX": obj["drawing_index"],
        "PDF_PATH_COMPONENT": obj["path_component"], "BACKGROUND_ONLY": obj["background"],
        "MASK_KIND_REVIEWED": kind, "BBOX": f"{x0},{y0},{x1},{y1}",
        "RAW_MASK_FILE": obj["mask_file"], "OPAQUE_GEOMETRY_MASK_FILE": obj["opaque_geometry_mask_file"],
        "SOURCE": obj["source"], "Z_ORDER_NOTE": obj["z_order_note"],
    }
    return canvas, row


def main() -> None:
    CARD_DIR.mkdir(exist_ok=True)
    SHEET_DIR.mkdir(exist_ok=True)
    page = np.asarray(Image.open(PAGE).convert("RGB"))
    objects = json.loads(OBJECTS.read_text(encoding="utf-8"))
    graphics = [o for o in objects if o["kind"] == "GRAPHIC"]
    if len(graphics) != 44:
        raise RuntimeError(f"expected 44 semantic graphic objects, got {len(graphics)}")
    rows: list[dict] = []
    cards: list[tuple[str, Image.Image]] = []
    for obj in graphics:
        rendered, row = card(page, obj)
        filename = f"{safe(obj['id'])}_native_overlay_mask.png"
        rendered.save(CARD_DIR / filename)
        row["CARD_FILE"] = f"graphic_object_cards_native/{filename}"
        rows.append(row)
        cards.append((obj["id"], rendered))
    with (OUT / "graphic_object_review_card_index.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    sheet_rows = []
    for batch_no, start in enumerate(range(0, len(cards), 4), start=1):
        batch = cards[start:start + 4]
        width = max(im.width for _, im in batch)
        height = sum(im.height for _, im in batch) + 6 * (len(batch) - 1)
        sheet = Image.new("RGB", (width, height), "white")
        y = 0
        for ident, im in batch:
            sheet.paste(im, (0, y)); y += im.height + 6
        filename = f"graphic_sheet_{batch_no:02d}_{batch[0][0]}_to_{batch[-1][0]}.png"
        sheet.save(SHEET_DIR / filename)
        sheet_rows.append({"SHEET": batch_no, "OBJECT_IDS": ";".join(i for i, _ in batch),
                           "PATH": f"graphic_object_contact_sheets/{filename}", "OBJECT_COUNT": len(batch)})
    with (OUT / "graphic_object_contact_sheet_index.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(sheet_rows[0]))
        writer.writeheader(); writer.writerows(sheet_rows)
    print(f"graphic_cards={len(rows)} sheets={len(sheet_rows)}")


if __name__ == "__main__":
    main()
