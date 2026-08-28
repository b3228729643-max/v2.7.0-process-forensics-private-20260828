from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "figure_and_caption_native_300dpi.png"

# Coordinates are in the unscaled 300 dpi crop: (x0, y0, x1, y1).
OBJECTS = {
    "R01": (505, 35, 590, 115),
    "R02": (625, 60, 1125, 208),
    "R03": (40, 275, 120, 355),
    "R04": (135, 270, 730, 460),
    "R05": (917, 275, 995, 355),
    "R06": (1020, 270, 1615, 460),
    "R07": (355, 515, 435, 590),
    "R08": (475, 505, 1272, 710),
    "R09": (480, 740, 555, 820),
    "R10": (595, 750, 1155, 900),
    "R11": (430, 205, 630, 275),
    "R12": (1120, 205, 1320, 275),
    "R13": (430, 455, 490, 510),
    "R14": (1265, 455, 1325, 510),
    "R15": (855, 705, 890, 755),
    "R16": (1125, 130, 1665, 830),
    "R17": (1680, 410, 1940, 555),
    "R18": (370, 915, 1390, 985),
    "R19": (35, 995, 1985, 1155),
}

CATEGORIES = {
    **{k: "BADGE" for k in ("R01", "R03", "R05", "R07", "R09")},
    **{k: "CARD" for k in ("R02", "R04", "R06", "R08", "R10")},
    **{k: "ARROW" for k in ("R11", "R12", "R13", "R14", "R15", "R16")},
    "R17": "ANNOTATION",
    "R18": "NOTE",
    "R19": "CAPTION",
}

TEXT_RUNS = {
    "T01": (525, 55, 570, 100),
    "T02": (725, 85, 1035, 135),
    "T03": (685, 130, 1060, 185),
    "T04": (60, 295, 105, 340),
    "T05": (235, 295, 635, 345),
    "T06": (335, 340, 525, 395),
    "T07": (335, 390, 525, 445),
    "T08": (935, 295, 980, 340),
    "T09": (1120, 295, 1515, 345),
    "T10": (1220, 340, 1415, 395),
    "T11": (1220, 390, 1415, 445),
    "T12": (375, 535, 420, 580),
    "T13": (675, 525, 1085, 575),
    "T14": (545, 565, 1200, 685),
    "T15": (495, 760, 540, 805),
    "T16": (680, 775, 1090, 830),
    "T17": (680, 820, 1090, 875),
    "T18": (1690, 410, 1915, 455),
    "T19": (1690, 450, 1940, 500),
    "T20": (1690, 495, 1790, 545),
    "T21": (370, 915, 1390, 985),
    "T22": (35, 995, 1985, 1070),
    "T23": (35, 1060, 1515, 1155),
}

ROIS = {
    "roi_01_badge2_left_card_entry": (20, 210, 760, 505),
    "roi_02_badge3_right_card_entry": (875, 210, 1640, 505),
    "roi_03_full_formula_connectors": (330, 455, 1340, 770),
    "roi_04_loop_annotation_return": (1060, 90, 1980, 910),
    "roi_05_sample_and_bottom_note": (400, 700, 1450, 1010),
    "roi_06_caption": (0, 985, 2040, 1190),
}


def font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\consola.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def labelled_overlay(
    source: Image.Image,
    boxes: dict[str, tuple[int, int, int, int]],
    color_for,
    output: str,
) -> None:
    out = source.copy().convert("RGBA")
    draw = ImageDraw.Draw(out, "RGBA")
    label_font = font(22)
    for item_id, box in boxes.items():
        color = color_for(item_id)
        draw.rectangle(box, outline=(*color, 255), width=4)
        x0, y0, _, _ = box
        draw.rectangle((x0, y0, x0 + 60, y0 + 28), fill=(*color, 225))
        draw.text((x0 + 4, y0 + 2), item_id, font=label_font, fill=(255, 255, 255, 255))
    out.convert("RGB").save(ROOT / output)


def main() -> None:
    source = Image.open(SOURCE).convert("RGB")
    if source.size != (2040, 1190):
        raise RuntimeError(f"unexpected crop size: {source.size}")

    labelled_overlay(
        source,
        OBJECTS,
        lambda _item_id: (220, 40, 40),
        "object_overlay_300dpi.png",
    )

    palette = {
        "BADGE": (122, 73, 170),
        "CARD": (35, 135, 88),
        "ARROW": (230, 126, 34),
        "ANNOTATION": (176, 40, 130),
        "NOTE": (70, 90, 200),
        "CAPTION": (30, 120, 180),
    }
    labelled_overlay(
        source,
        OBJECTS,
        lambda item_id: palette[CATEGORIES[item_id]],
        "semantic_overlay_300dpi.png",
    )
    labelled_overlay(
        source,
        TEXT_RUNS,
        lambda _item_id: (40, 110, 220),
        "text_overlay_300dpi.png",
    )

    gray = source.convert("L")
    mask = gray.point(lambda value: 255 if value < 190 else 0, mode="1")
    mask.save(ROOT / "visible_ink_mask_threshold190_300dpi.png")

    for name, box in ROIS.items():
        roi = source.crop(box)
        roi.save(ROOT / f"{name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
            ROOT / f"{name}_nearest8x.png"
        )

    with (ROOT / "pair_ids_machine.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["PAIR_ID", "A_ID", "B_ID"])
        for index, (a_id, b_id) in enumerate(combinations(OBJECTS, 2), start=1):
            writer.writerow([f"P{index:03d}", a_id, b_id])

    with (ROOT / "mechanical_geometry.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["OBJECT_ID", "CATEGORY", "X0", "Y0", "X1", "Y1"])
        for item_id, (x0, y0, x1, y1) in OBJECTS.items():
            writer.writerow([item_id, CATEGORIES[item_id], x0, y0, x1, y1])

    expected_pairs = len(OBJECTS) * (len(OBJECTS) - 1) // 2
    print(f"OBJECT_COUNT={len(OBJECTS)}")
    print(f"PAIR_COUNT={expected_pairs}")
    print(f"TEXT_RUN_COUNT={len(TEXT_RUNS)}")
    print(f"ROI_COUNT={len(ROIS)}")


if __name__ == "__main__":
    main()
