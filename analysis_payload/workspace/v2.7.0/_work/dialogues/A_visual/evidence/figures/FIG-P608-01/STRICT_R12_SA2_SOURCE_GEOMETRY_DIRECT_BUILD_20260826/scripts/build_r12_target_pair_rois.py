from __future__ import annotations

import ast
import csv
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R12_SA2_SOURCE_GEOMETRY_DIRECT_BUILD_20260826")
VIEWS = ROOT / "views"
MASKS = ROOT / "masks"
ROIS = ROOT / "rois"
MACHINE = ROOT / "machine"
TARGETS = [
    ("PAIR-06596", "GFX-D004", "GFX-D013", "TOP_Y_AXIS_vs_FIRST_MARKER"),
    ("PAIR-06650", "GFX-D005", "GFX-D013", "TOP_Y_ARROWHEAD_vs_FIRST_MARKER"),
]


def font(size: int = 16):
    for path in [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\msyh.ttc"]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main() -> None:
    ROIS.mkdir(parents=True, exist_ok=True)
    image = Image.open(VIEWS / "standalone_300dpi.png").convert("RGB")
    with (MACHINE / "object_manifest.csv").open("r", encoding="utf-8-sig", newline="") as f:
        objects = {row["element_id"]: row for row in csv.DictReader(f)}
    with (MACHINE / "all_unordered_pairs.csv").open("r", encoding="utf-8-sig", newline="") as f:
        pairs = {row["pair_id"]: row for row in csv.DictReader(f)}

    rows = []
    sheet = Image.new("RGB", (1900, len(TARGETS) * 420), "white")
    draw = ImageDraw.Draw(sheet)
    label_font = font(16)
    for row_no, (pair_id, aid, bid, label) in enumerate(TARGETS):
        pair = pairs[pair_id]
        if pair["object_a"] != aid or pair["object_b"] != bid:
            raise RuntimeError(f"Pair identity mismatch for {pair_id}")
        abox = tuple(ast.literal_eval(objects[aid]["bbox_px"]))
        bbox = tuple(ast.literal_eval(objects[bid]["bbox_px"]))
        amask_local = np.asarray(Image.open(MASKS / objects[aid]["safe_filename"]).convert("L")) < 128
        bmask_local = np.asarray(Image.open(MASKS / objects[bid]["safe_filename"]).convert("L")) < 128
        ga = np.zeros((image.height, image.width), dtype=bool)
        gb = np.zeros((image.height, image.width), dtype=bool)
        ga[abox[1]:abox[3], abox[0]:abox[2]] = amask_local[: abox[3]-abox[1], : abox[2]-abox[0]]
        gb[bbox[1]:bbox[3], bbox[0]:bbox[2]] = bmask_local[: bbox[3]-bbox[1], : bbox[2]-bbox[0]]
        pad = 20
        x0 = max(0, min(abox[0], bbox[0]) - pad)
        y0 = max(0, min(abox[1], bbox[1]) - pad)
        x1 = min(image.width, max(abox[2], bbox[2]) + pad)
        y1 = min(image.height, max(abox[3], bbox[3]) + pad)
        raw = image.crop((x0, y0, x1, y1))
        a = ga[y0:y1, x0:x1]
        b = gb[y0:y1, x0:x1]
        a_img = Image.fromarray(np.where(a, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        b_img = Image.fromarray(np.where(b, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        inter_img = Image.fromarray(np.where(a & b, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        overlay_array = np.asarray(raw).copy()
        overlay_array[a] = [255, 0, 0]
        overlay_array[b] = [0, 0, 255]
        overlay_array[a & b] = [255, 0, 255]
        overlay = Image.fromarray(overlay_array)
        zoom = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)

        prefix = f"target_{pair_id}"
        files = {
            "raw_1x": f"{prefix}_raw_1x.png",
            "a_mask_1x": f"{prefix}_A_mask_1x.png",
            "b_mask_1x": f"{prefix}_B_mask_1x.png",
            "intersection_1x": f"{prefix}_intersection_1x.png",
            "overlay_1x": f"{prefix}_overlay_1x.png",
            "overlay_8x_nearest": f"{prefix}_overlay_8x_nearest.png",
        }
        raw.save(ROIS / files["raw_1x"])
        a_img.save(ROIS / files["a_mask_1x"])
        b_img.save(ROIS / files["b_mask_1x"])
        inter_img.save(ROIS / files["intersection_1x"])
        overlay.save(ROIS / files["overlay_1x"])
        zoom.save(ROIS / files["overlay_8x_nearest"])

        y = row_no * 420
        draw.text((8, y + 5), f"{pair_id} {label} intersection={pair['intersection_px']}px clearance={pair['clearance_px']}px", fill="black", font=label_font)
        parts = [(raw, "RAW 1x"), (a_img, "A MASK 1x"), (b_img, "B MASK 1x"), (inter_img, "INTERSECTION 1x"), (overlay, "OVERLAY 1x"), (zoom, "OVERLAY 8x NEAREST")]
        xpos = 8
        for part, part_label in parts:
            draw.text((xpos, y + 34), part_label, fill="black", font=label_font)
            shown = part
            if shown.width > 285 or shown.height > 330:
                ratio = min(285 / shown.width, 330 / shown.height)
                shown = shown.resize((max(1, round(shown.width * ratio)), max(1, round(shown.height * ratio))), Image.Resampling.NEAREST)
            sheet.paste(shown, (xpos, y + 60))
            xpos += 310
        rows.append({
            "pair_id": pair_id,
            "object_a": aid,
            "object_b": bid,
            "relationship": label,
            "intersection_px": pair["intersection_px"],
            "clearance_px": pair["clearance_px"],
            "machine_result": pair["machine_result"],
            **files,
        })

    sheet.save(VIEWS / "target_pair_relation_sheet.png")
    with (MACHINE / "target_pair_metrics.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
