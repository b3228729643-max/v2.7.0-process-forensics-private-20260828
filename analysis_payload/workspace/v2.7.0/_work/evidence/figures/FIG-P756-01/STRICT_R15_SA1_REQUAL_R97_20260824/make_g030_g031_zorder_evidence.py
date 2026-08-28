"""Produce native-pixel evidence for the report double frame and its separator."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
EVID = OUT / "z_order_evidence"
EVID.mkdir(exist_ok=True)
PAGE = np.asarray(Image.open(OUT / "full_page_native_300dpi-801.png").convert("RGB"))
OBJECTS = {o["id"]: o for o in json.loads((OUT / "object_inventory.json").read_text(encoding="utf-8"))}

def load_coords(obj: dict, opaque: bool = False) -> np.ndarray:
    rel = obj["opaque_geometry_mask_file"] if opaque else obj["mask_file"]
    bbox = obj["opaque_geometry_bbox"] if opaque else obj["bbox"]
    data = np.asarray(Image.open(OUT / rel).convert("L")) > 0
    yy, xx = np.where(data)
    return np.column_stack((yy + int(bbox[1]), xx + int(bbox[0]))).astype(np.int32)

def raster(coords: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    ans = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    ans[coords[:, 0] - y0, coords[:, 1] - x0] = True
    return ans

def mono(mask: np.ndarray, colour: tuple[int, int, int]) -> Image.Image:
    a = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    a[mask] = colour
    return Image.fromarray(a)

def labelled_tiles(tiles: list[tuple[str, Image.Image]], scale: int = 2) -> Image.Image:
    scaled = [(label, im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)) for label, im in tiles]
    header = 22
    canvas = Image.new("RGB", (sum(im.width for _, im in scaled) + 3 * (len(scaled) - 1), max(im.height for _, im in scaled) + header), "white")
    draw = ImageDraw.Draw(canvas)
    x = 0
    for label, im in scaled:
        draw.text((x + 2, 3), label, fill="black")
        canvas.paste(im, (x, header)); x += im.width + 3
    return canvas

def main() -> None:
    dark_obj = OBJECTS["G030_REPORT_OUTER_BORDER"]
    white_obj = OBJECTS["G031_REPORT_WHITE_SEPARATOR"]
    dark = load_coords(dark_obj)
    white = load_coords(white_obj, opaque=True)
    both = np.vstack((dark, white))
    x0, y0 = np.min(both[:, 1]) - 6, np.min(both[:, 0]) - 6
    x1, y1 = np.max(both[:, 1]) + 7, np.max(both[:, 0]) + 7
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(PAGE.shape[1], int(x1)), min(PAGE.shape[0], int(y1))
    box = (x0, y0, x1, y1)
    dark_m, white_m = raster(dark, box), raster(white, box)
    raw = PAGE[y0:y1, x0:x1].copy()
    overlay = raw.copy()
    overlay[dark_m] = (255, 0, 0)
    overlay[white_m] = (0, 220, 255)
    overlap = dark_m & white_m
    overlay[overlap] = (255, 0, 255)
    gray = Image.fromarray(raw).convert("L").convert("RGB")
    Image.fromarray(raw).save(EVID / "G030_G031_native1x.png")
    mono(dark_m, (255, 0, 0)).save(EVID / "G030_G031_G030_final_dark_mask.png")
    mono(white_m, (0, 220, 255)).save(EVID / "G030_G031_G031_white_separator_geometry.png")
    Image.fromarray(overlay).save(EVID / "G030_G031_overlay.png")
    gray.save(EVID / "G030_G031_grayscale_native1x.png")
    Image.fromarray(overlay).resize((overlay.shape[1] * 8, overlay.shape[0] * 8), Image.Resampling.NEAREST).save(EVID / "G030_G031_overlay_8x_nearest.png")
    four = labelled_tiles([
        ("native 1x", Image.fromarray(raw)), ("G030 unique dark", mono(dark_m, (255, 0, 0))),
        ("G031 actual white geometry", mono(white_m, (0, 220, 255))), ("unique-mask overlay", Image.fromarray(overlay)),
    ], scale=2)
    four.save(EVID / "G030_G031_four_view.png")
    # Raw colour values inside each selected geometry prove the native render
    # is a dark outer path plus a later white separator, not a single polluted
    # mask.  AA variations are retained rather than threshold-smoothed.
    dark_colours, dark_counts = np.unique(raw[dark_m].reshape(-1, 3), axis=0, return_counts=True)
    white_colours, white_counts = np.unique(raw[white_m].reshape(-1, 3), axis=0, return_counts=True)
    z_rows = list(csv.DictReader((OUT / "z_order_occlusion_ledger.csv").open(encoding="utf-8-sig")))
    reassigned = next((r for r in z_rows if r["EARLIER_OBJECT"] == "G030_REPORT_OUTER_BORDER" and r["LATER_OBJECT"] == "G031_REPORT_WHITE_SEPARATOR"), None)
    rows = [{
        "G030_OBJECT": dark_obj["id"], "G031_OBJECT": white_obj["id"],
        "SOURCE_LINE": 72, "SOURCE_STYLE_LINE": 25,
        "PDF_DRAWINGS": "33 fs dark report; 34 s white double separator",
        "NATIVE_CROP_BBOX": f"{x0},{y0},{x1},{y1}",
        "G030_FINAL_DARK_PIXELS": int(dark_m.sum()), "G031_WHITE_GEOMETRY_PIXELS": int(white_m.sum()),
        "UNIQUE_MASK_INTERSECTION_PIXELS": int(overlap.sum()),
        "G030_Z_ORDER_REASSIGNED_TO_G031_PIXELS": reassigned["REMOVED_FINAL_PIXEL_COUNT"] if reassigned else "MISSING",
        "G030_RAW_RGB_COUNTS": ";".join(f"{tuple(c)}:{n}" for c, n in zip(dark_colours.tolist(), dark_counts.tolist())),
        "G031_RAW_RGB_COUNTS": ";".join(f"{tuple(c)}:{n}" for c, n in zip(white_colours.tolist(), white_counts.tolist())),
        "NATIVE_1X": "z_order_evidence/G030_G031_native1x.png",
        "DARK_MASK": "z_order_evidence/G030_G031_G030_final_dark_mask.png",
        "WHITE_MASK": "z_order_evidence/G030_G031_G031_white_separator_geometry.png",
        "OVERLAY": "z_order_evidence/G030_G031_overlay.png",
        "OVERLAY_8X_NEAREST": "z_order_evidence/G030_G031_overlay_8x_nearest.png",
        "GRAYSCALE_1X": "z_order_evidence/G030_G031_grayscale_native1x.png",
        "FOUR_VIEW": "z_order_evidence/G030_G031_four_view.png",
    }]
    with (EVID / "G030_G031_zorder_measurement.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(f"dark={dark_m.sum()} white={white_m.sum()} intersection={overlap.sum()} box={box}")

if __name__ == "__main__":
    main()
