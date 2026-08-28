import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
FROZEN = json.loads(Path(__file__).with_name("03_objects_frozen.json").read_text(encoding="utf-8"))
BODY_IMG = Image.open(ROOT / "render" / "standalone_300dpi.png").convert("RGB")
BODY_SHAPE = (BODY_IMG.height, BODY_IMG.width)
GRAPHICS = [o for o in FROZEN["objects"] if o["object_type"] == "GRAPHIC"]

for old in (ROOT / "contact").glob("graphic_contact_*.png"):
    old.unlink()


def load_full_mask(obj):
    x0, y0, x1, y1 = map(int, obj["bbox_crop_native_px"])
    local = np.asarray(Image.open(ROOT / "masks" / obj["safe_filename"]).convert("L")) > 0
    full = np.zeros(BODY_SHAPE, dtype=bool)
    full[y0:y1, x0:x1] = local
    return full


MASKS = {o["object_id"]: load_full_mask(o) for o in GRAPHICS}


def bbox(mask):
    ys, xs = np.where(mask)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def triptych(obj, crop, scale):
    x0, y0, x1, y1 = crop
    original = BODY_IMG.crop((x0, y0, x1, y1))
    mask = MASKS[obj["object_id"]][y0:y1, x0:x1]
    over_arr = np.asarray(original).copy(); over_arr[mask] = [255, 0, 0]
    mono_arr = np.full_like(over_arr, 255); mono_arr[mask] = [0, 0, 0]
    images = [original, Image.fromarray(over_arr), Image.fromarray(mono_arr)]
    if scale != 1:
        images = [im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST) for im in images]
    out = Image.new("RGB", (sum(im.width for im in images) + 12, max(im.height for im in images) + 20), "white")
    d = ImageDraw.Draw(out); d.text((2, 1), f"{obj['object_id']} ORIGINAL | TARGET OVERLAY | MASK ONLY", fill="black")
    x = 0
    for im in images:
        out.paste(im, (x, 20)); x += im.width + 6
    return out


index = []
# Compact full-object native 1x sheets: one cell per row so long axes remain inspectable.
for sheet_no, start in enumerate(range(0, len(GRAPHICS), 7), start=1):
    subset = GRAPHICS[start:start+7]
    cells = []
    for cell_no, obj in enumerate(subset, start=1):
        b = bbox(MASKS[obj["object_id"]]); pad = 5
        crop = [max(0, b[0]-pad), max(0, b[1]-pad), min(BODY_IMG.width, b[2]+pad), min(BODY_IMG.height, b[3]+pad)]
        cells.append(triptych(obj, crop, 1))
        index.append({"object_id": obj["object_id"], "scale": "1x", "sheet": sheet_no, "cell": cell_no, "tile": "FULL", "crop_px": crop})
    sheet = Image.new("RGB", (max(c.width for c in cells), sum(c.height+6 for c in cells)), "white")
    y = 0
    for cell in cells: sheet.paste(cell, (0, y)); y += cell.height + 6
    sheet.save(ROOT / "contact" / f"graphic_contact_1x_sheet_{sheet_no:02d}.png")

# Native 8x: small objects are full; long objects are exhaustively tiled before nearest-neighbour enlargement.
tile_records = []
for obj in GRAPHICS:
    b = bbox(MASKS[obj["object_id"]]); pad = 5
    whole = [max(0, b[0]-pad), max(0, b[1]-pad), min(BODY_IMG.width, b[2]+pad), min(BODY_IMG.height, b[3]+pad)]
    w, h = whole[2]-whole[0], whole[3]-whole[1]
    tile_size = 260
    if w <= tile_size and h <= tile_size:
        tile_records.append((obj, "FULL", whole))
    else:
        tile_no = 0
        for y0 in range(whole[1], whole[3], tile_size):
            for x0 in range(whole[0], whole[2], tile_size):
                tile_no += 1
                tile_records.append((obj, f"TILE_{tile_no:02d}", [x0, y0, min(whole[2], x0+tile_size), min(whole[3], y0+tile_size)]))

for sheet_no, start in enumerate(range(0, len(tile_records), 2), start=1):
    subset = tile_records[start:start+2]
    cells = []
    for cell_no, (obj, tile, crop) in enumerate(subset, start=1):
        cell = triptych(obj, crop, 8)
        d = ImageDraw.Draw(cell); d.text((2, 10), tile, fill="black")
        cells.append(cell)
        index.append({"object_id": obj["object_id"], "scale": "8x", "sheet": sheet_no, "cell": cell_no, "tile": tile, "crop_px": crop})
    sheet = Image.new("RGB", (max(c.width for c in cells), sum(c.height+8 for c in cells)), "white")
    y = 0
    for cell in cells: sheet.paste(cell, (0, y)); y += cell.height + 8
    sheet.save(ROOT / "contact" / f"graphic_contact_8x_sheet_{sheet_no:02d}.png")

with Path(__file__).with_name("05_graphic_contact_index.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["object_id", "scale", "sheet", "cell", "tile", "crop_px"])
    writer.writeheader()
    for row in index:
        cooked = dict(row); cooked["crop_px"] = json.dumps(cooked["crop_px"])
        writer.writerow(cooked)

print(json.dumps({
    "graphic_objects": len(GRAPHICS),
    "sheets_1x": len(list((ROOT / "contact").glob("graphic_contact_1x_sheet_*.png"))),
    "tiles_8x": len(tile_records),
    "sheets_8x": len(list((ROOT / "contact").glob("graphic_contact_8x_sheet_*.png"))),
}, indent=2))
