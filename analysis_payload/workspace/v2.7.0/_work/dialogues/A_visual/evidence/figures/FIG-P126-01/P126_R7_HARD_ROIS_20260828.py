import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828")
RENDER = ROOT / "render"
MACHINE = ROOT / "machine"
COLOR = Image.open(RENDER / "full_page_300.png").convert("RGB")
GRAY = Image.open(RENDER / "grayscale_300.png").convert("RGB")
SCALE = COLOR.width / 595.276


def make_roi(name, ptbox, participants):
    pad = 18
    box = (
        max(0, round(ptbox[0] * SCALE) - pad), max(0, round(ptbox[1] * SCALE) - pad),
        min(COLOR.width, round(ptbox[2] * SCALE) + pad), min(COLOR.height, round(ptbox[3] * SCALE) + pad),
    )
    result = {"name": name, "participants": participants, "pdf_box_pt": ptbox, "pixel_box": box}
    for label, source in (("color", COLOR), ("gray", GRAY)):
        raw = source.crop(box)
        raw.save(RENDER / f"{name}_{label}_native1x.png")
        raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(RENDER / f"{name}_{label}_nearest8x.png")
        overlay = raw.copy()
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except OSError:
            font = ImageFont.load_default()
        for participant in participants:
            b = participant["bbox_pt"]
            x0 = round(b[0] * SCALE) - box[0]
            y0 = round(b[1] * SCALE) - box[1]
            x1 = round(b[2] * SCALE) - box[0]
            y1 = round(b[3] * SCALE) - box[1]
            draw.rectangle((x0, y0, x1, y1), outline=(230, 25, 25), width=2)
            draw.text((x0, max(0, y0 - 13)), participant["id"], fill=(230, 25, 25), font=font)
        overlay.save(RENDER / f"{name}_{label}_overlay1x.png")
        overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(RENDER / f"{name}_{label}_overlay_nearest8x.png")
    return result


rois = []
rois.append(make_roi(
    "H01_label6_axis_contour",
    (296.5, 103.5, 309.0, 121.0),
    [
        {"id": "G010", "bbox_pt": (300.96, 107.57, 305.20, 116.13)},
        {"id": "L002", "bbox_pt": (303.30, 71.19, 303.30, 211.27)},
        {"id": "C005", "bbox_pt": (244.03, 98.24, 362.56, 182.06)},
    ],
))
rois.append(make_roi(
    "H02_label7_arrow_marker",
    (276.0, 112.0, 290.0, 131.0),
    [
        {"id": "G011", "bbox_pt": (281.07, 116.67, 285.31, 125.23)},
        {"id": "C008", "bbox_pt": (279.10, 119.15, 281.31, 120.50)},
        {"id": "C016", "bbox_pt": (281.08, 117.93, 284.87, 121.72)},
    ],
))
rois.append(make_roi(
    "H03_legend_compare",
    (244.0, 225.0, 322.0, 240.5),
    [
        {"id": "C019", "bbox_pt": (247.92, 232.04, 264.93, 232.04)},
        {"id": "C020", "bbox_pt": (302.21, 232.04, 319.22, 232.04)},
    ],
))
with (MACHINE / "HARD_ROI_INDEX.json").open("w", encoding="utf-8") as handle:
    json.dump(rois, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps(rois, ensure_ascii=False, indent=2))
