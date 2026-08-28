from pathlib import Path
import csv
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R7_SA2_REPAIR_R97_LOCAL_20260824\final_audit")
OUT = ROOT / "supplemental_prior_fail_pair_cards"
PAGE = np.asarray(Image.open(ROOT / "renders" / "page_300dpi_native.png").convert("RGB"))


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


GLYPHS = {r["glyph_id"]: r for r in read_rows(ROOT / "glyphs" / "all_visible_glyph_raw_measurements.csv")}
GRAPHICS = {r["object_id"]: r for r in read_rows(ROOT / "graphics" / "graphic_object_inventory.csv")}


def parse_box(value):
    return tuple(int(x) for x in value.split(","))


def object_mask(identifier):
    if identifier.startswith("C"):
        row = GLYPHS[identifier]
        box = parse_box(row["roi_bbox_px"])
        path = Path(row["mask_only_1x"])
    else:
        row = GRAPHICS[identifier]
        box = parse_box(row["bbox_px"])
        path = Path(row["mask_only_1x"])
    mask = np.asarray(Image.open(path).convert("L")) < 128
    assert mask.shape == (box[3] - box[1], box[2] - box[0])
    return box, mask


def font():
    try:
        return ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        return ImageFont.load_default()


def card(pair_id, panels):
    scaled = [(label, im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST)) for label, im in panels]
    header_h, gap = 28, 8
    width = sum(im.width for _, im in scaled) + gap * (len(scaled) + 1)
    height = header_h + max(im.height for _, im in scaled) + gap * 2 + 14
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    x = gap
    for label, im in scaled:
        draw.text((x, 5), label, fill="black", font=font())
        canvas.paste(im, (x, header_h + gap))
        x += im.width + gap
    draw.text((gap, height - 13), pair_id + "; 8x nearest only", fill="black", font=font())
    return canvas


def generate(pair_id, a_id, b_id):
    abox, amask = object_mask(a_id)
    bbox, bmask = object_mask(b_id)
    box = (
        max(0, min(abox[0], bbox[0]) - 5),
        max(0, min(abox[1], bbox[1]) - 5),
        min(PAGE.shape[1], max(abox[2], bbox[2]) + 5),
        min(PAGE.shape[0], max(abox[3], bbox[3]) + 5),
    )
    roi = PAGE[box[1]:box[3], box[0]:box[2]].copy()
    ma = np.zeros(roi.shape[:2], dtype=bool)
    mb = np.zeros_like(ma)
    for obox, omask, target in ((abox, amask, ma), (bbox, bmask, mb)):
        x0, y0 = max(obox[0], box[0]), max(obox[1], box[1])
        x1, y1 = min(obox[2], box[2]), min(obox[3], box[3])
        target[y0-box[1]:y1-box[1], x0-box[0]:x1-box[0]] |= omask[y0-obox[1]:y1-obox[1], x0-obox[0]:x1-obox[0]]
    inter = ma & mb
    original = Image.fromarray(roi, "RGB")
    overlay_arr = roi.astype(np.float32)
    overlay_arr[ma] = 0.45 * overlay_arr[ma] + 0.55 * np.array([230, 30, 30])
    overlay_arr[mb] = 0.45 * overlay_arr[mb] + 0.55 * np.array([36, 88, 238])
    overlay_arr[inter] = np.array([180, 0, 180])
    overlay = Image.fromarray(np.clip(overlay_arr, 0, 255).astype(np.uint8), "RGB")
    def mono(mask):
        arr = np.full((*mask.shape, 3), 255, dtype=np.uint8)
        arr[mask] = (0, 0, 0)
        return Image.fromarray(arr, "RGB")
    aim, bim, iim = mono(ma), mono(mb), mono(inter)
    outputs = {
        "original_1x": original,
        "mask_A_1x": aim,
        "mask_B_1x": bim,
        "intersection_mask_1x": iim,
        "overlay_1x": overlay,
    }
    for suffix, image in outputs.items():
        image.save(OUT / f"{pair_id}_{suffix}.png")
    card(pair_id, [("ORIGINAL", original), ("A MASK", aim), ("B MASK", bim), ("INTERSECTION", iim), ("OVERLAY", overlay)]).save(OUT / f"{pair_id}_contact_8x_nearest.png")


generate("PAIR_C0031_G10", "C0031", "G10")
generate("PAIR_C0116_G27", "C0116", "G27")
