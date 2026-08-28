from __future__ import annotations

import csv
import itertools
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa1_r115_fresh_isolated_v1")
PAGE_300 = ROOT / "full_page_300dpi.png"
PAGE_GRAY_300 = ROOT / "full_page_grayscale_300dpi.png"
DENOMINATOR = ROOT / "reader_visible_denominator.csv"

PT_TO_PX = 300.0 / 72.0
CROP = (235, 1560, 2230, 2690)

ROI_RECTS = {
    "roi01_step1": (688, 1563, 1375, 1792),
    "roi02_document_counts": (208, 1771, 1000, 2042),
    "roi03_topic_word_counts": (1083, 1771, 1875, 2042),
    "roi04_full_conditional": (542, 2021, 1542, 2283),
    "roi05_sample_restore": (646, 2271, 1425, 2467),
    "roi06_loop_topology_note": (1313, 1646, 2229, 2417),
    "roi07_minus_i_note_caption": (208, 2450, 2229, 2690),
}

CLASS_COLORS = {
    "TEXT": (0, 102, 204, 70),
    "BADGE": (130, 0, 180, 85),
    "CAPTION": (0, 145, 80, 70),
    "CONTAINER": (255, 140, 0, 60),
    "CONNECTOR": (220, 20, 60, 90),
}


def read_objects() -> list[dict[str, str]]:
    with DENOMINATOR.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def bbox_pixels(row: dict[str, str], *, relative_to_crop: bool) -> tuple[int, int, int, int]:
    box = tuple(round(float(row[key]) * PT_TO_PX) for key in ("pdf_x0_pt", "pdf_y0_pt", "pdf_x1_pt", "pdf_y1_pt"))
    if not relative_to_crop:
        return box
    return (box[0] - CROP[0], box[1] - CROP[1], box[2] - CROP[0], box[3] - CROP[1])


def label_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, color: tuple[int, int, int, int], width: int = 4) -> None:
    draw.rectangle(box, outline=color[:3] + (255,), width=width)
    font = ImageFont.load_default()
    text_box = draw.textbbox((0, 0), label, font=font)
    tw = text_box[2] - text_box[0]
    th = text_box[3] - text_box[1]
    x = max(0, box[0])
    y = max(0, box[1] - th - 4)
    draw.rectangle((x, y, x + tw + 6, y + th + 4), fill=color[:3] + (235,))
    draw.text((x + 3, y + 2), label, fill=(255, 255, 255, 255), font=font)


def make_overlays(crop: Image.Image, objects: list[dict[str, str]]) -> None:
    object_overlay = crop.convert("RGBA")
    object_draw = ImageDraw.Draw(object_overlay, "RGBA")
    semantic_overlay = crop.convert("RGBA")
    semantic_draw = ImageDraw.Draw(semantic_overlay, "RGBA")
    text_overlay = crop.convert("RGBA")
    text_draw = ImageDraw.Draw(text_overlay, "RGBA")

    for row in objects:
        box = bbox_pixels(row, relative_to_crop=True)
        color = CLASS_COLORS[row["class"]]
        semantic_draw.rectangle(box, fill=color, outline=color[:3] + (255,), width=3)
        label_box(object_draw, box, row["object_id"], color, width=4)
        if row["class"] in {"TEXT", "BADGE", "CAPTION"}:
            label_box(text_draw, box, row["object_id"], color, width=4)

    object_overlay.save(ROOT / "object_overlay_300dpi.png")
    semantic_overlay.save(ROOT / "semantic_overlay_300dpi.png")
    text_overlay.save(ROOT / "text_overlay_300dpi.png")


def make_masks(crop: Image.Image, objects: list[dict[str, str]]) -> None:
    gray = crop.convert("L")
    ink = gray.point(lambda p: 0 if p < 220 else 255, mode="1").convert("L")
    ink.save(ROOT / "visible_ink_mask_all_300dpi.png")

    text_regions = Image.new("L", crop.size, 0)
    region_draw = ImageDraw.Draw(text_regions)
    for row in objects:
        if row["class"] in {"TEXT", "BADGE", "CAPTION"}:
            region_draw.rectangle(bbox_pixels(row, relative_to_crop=True), fill=255)
    text_mask = Image.new("L", crop.size, 255)
    text_mask.paste(ink, mask=text_regions)
    text_mask.save(ROOT / "visible_ink_mask_text_300dpi.png")

    graphics_mask = Image.new("L", crop.size, 255)
    graphics_regions = Image.eval(text_regions, lambda p: 255 - p)
    graphics_mask.paste(ink, mask=graphics_regions)
    graphics_mask.save(ROOT / "visible_ink_mask_graphics_300dpi.png")

    overlay = crop.convert("RGBA")
    red = Image.new("RGBA", crop.size, (255, 0, 0, 120))
    ink_alpha = Image.eval(ink, lambda p: 255 - p)
    overlay.alpha_composite(Image.composite(red, Image.new("RGBA", crop.size, (0, 0, 0, 0)), ink_alpha))
    overlay.save(ROOT / "visible_ink_overlay_300dpi.png")


def make_rois(page: Image.Image) -> None:
    for name, rect in ROI_RECTS.items():
        roi = page.crop(rect)
        roi.save(ROOT / f"{name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(ROOT / f"{name}_nearest8x.png")


def make_pair_skeleton(objects: list[dict[str, str]]) -> None:
    with (ROOT / "pair_skeleton.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["pair_id", "object_a", "object_b"])
        for index, (left, right) in enumerate(itertools.combinations(objects, 2), 1):
            writer.writerow([f"P{index:03d}", left["object_id"], right["object_id"]])


def main() -> None:
    objects = read_objects()
    if len(objects) != 24:
        raise SystemExit(f"unexpected denominator size: {len(objects)}")
    page = Image.open(PAGE_300).convert("RGB")
    gray_page = Image.open(PAGE_GRAY_300).convert("L")
    crop = page.crop(CROP)
    crop.save(ROOT / "figure_caption_native1x_300dpi.png")
    gray_page.crop(CROP).save(ROOT / "figure_caption_grayscale_native1x_300dpi.png")
    make_overlays(crop, objects)
    make_masks(crop, objects)
    make_rois(page)
    make_pair_skeleton(objects)
    pair_count = sum(1 for _ in itertools.combinations(objects, 2))
    if pair_count != 276:
        raise SystemExit(f"unexpected pair count: {pair_count}")
    print(f"objects={len(objects)} pairs={pair_count} crop={crop.size} rois={len(ROI_RECTS)}")


if __name__ == "__main__":
    main()
