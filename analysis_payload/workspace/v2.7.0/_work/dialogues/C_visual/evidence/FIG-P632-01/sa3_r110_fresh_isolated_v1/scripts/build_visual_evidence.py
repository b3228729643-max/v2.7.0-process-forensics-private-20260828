from __future__ import annotations

import csv
import itertools
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa3_r110_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
FULL = ROOT / "render" / "native300_full_p682.png"
SCALE = 300.0 / 72.0
FIGURE_CROP = (260, 250, 2220, 1780)


OBJECTS = [
    ("O01", "formula_block", (550, 275, 1180, 555)),
    ("O02", "joint_axes_contours", (475, 565, 1225, 1215)),
    ("O03", "horizontal_slice", (465, 600, 1235, 830)),
    ("O04", "vertical_slice", (955, 545, 1090, 1195)),
    ("O05", "condition_point", (970, 600, 1160, 830)),
    ("O06", "joint_explanation", (385, 1205, 1290, 1325)),
    ("O07", "horizontal_map", (1130, 610, 1425, 840)),
    ("O08", "upper_formula_block", (1380, 275, 2155, 555)),
    ("O09", "upper_density_plot", (1390, 540, 2070, 900)),
    ("O10", "vertical_map", (955, 990, 1415, 1330)),
    ("O11", "lower_formula_block", (1380, 845, 2155, 1125)),
    ("O12", "lower_density_plot", (1390, 1080, 2070, 1435)),
    ("O13", "zero_denominator_note", (1280, 1440, 2100, 1625)),
    ("O14", "caption", (300, 1635, 2200, 1765)),
]


ROIS = [
    ("R01_joint_formula", (535, 260, 1200, 570)),
    ("R02_joint_slice_intersection", (780, 560, 1165, 860)),
    ("R03_upper_conditional", (1350, 255, 2180, 925)),
    ("R04_lower_conditional", (1350, 825, 2180, 1450)),
    ("R05_mapping_junctions", (930, 570, 1450, 1350)),
    ("R06_note_and_caption", (285, 1415, 2210, 1775)),
]


COLORS = {
    "formula_block": (183, 28, 28),
    "joint_axes_contours": (17, 105, 180),
    "horizontal_slice": (0, 137, 123),
    "vertical_slice": (67, 73, 160),
    "condition_point": (230, 81, 0),
    "joint_explanation": (111, 78, 55),
    "horizontal_map": (0, 121, 107),
    "upper_formula_block": (173, 20, 87),
    "upper_density_plot": (0, 105, 92),
    "vertical_map": (48, 63, 159),
    "lower_formula_block": (123, 31, 162),
    "lower_density_plot": (21, 101, 192),
    "zero_denominator_note": (211, 47, 47),
    "caption": (69, 90, 100),
}


def get_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def crop_box(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    left, top, _, _ = FIGURE_CROP
    x0, y0, x1, y1 = box
    return x0 - left, y0 - top, x1 - left, y1 - top


def gap_and_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ox = max(0, min(ax1, bx1) - max(ax0, bx0))
    oy = max(0, min(ay1, by1) - max(ay0, by0))
    overlap = ox * oy
    gx = max(0, max(ax0, bx0) - min(ax1, bx1))
    gy = max(0, max(ay0, by0) - min(ay1, by1))
    if overlap > 0:
        relation = "bbox_overlap"
    elif gx == 0:
        relation = "vertical_separation"
    elif gy == 0:
        relation = "horizontal_separation"
    else:
        relation = "diagonal_separation"
    return relation, overlap, gx, gy


def main() -> None:
    image = Image.open(FULL).convert("RGB")
    if image.size != (2481, 3508):
        raise RuntimeError(f"unexpected page raster size: {image.size}")

    figure = image.crop(FIGURE_CROP)
    figure.save(ROOT / "render" / "native300_figure_caption_p682.png")
    figure.convert("L").save(ROOT / "render" / "native300_figure_grayscale_p682.png")

    font = get_font(28)
    object_overlay = figure.copy()
    draw = ImageDraw.Draw(object_overlay)
    for object_id, kind, box in OBJECTS:
        local = crop_box(box)
        color = COLORS[kind]
        draw.rectangle(local, outline=color, width=5)
        label_box = (local[0], local[1], local[0] + 118, local[1] + 34)
        draw.rectangle(label_box, fill=(255, 255, 255), outline=color, width=2)
        draw.text((local[0] + 4, local[1] + 1), object_id, fill=color, font=font)
    object_overlay.save(ROOT / "overlays" / "object_overlay_p682.png")

    semantic_overlay = figure.copy().convert("RGBA")
    layer = Image.new("RGBA", semantic_overlay.size, (0, 0, 0, 0))
    sem_draw = ImageDraw.Draw(layer)
    for object_id, kind, box in OBJECTS:
        local = crop_box(box)
        color = COLORS[kind]
        sem_draw.rectangle(local, fill=(*color, 28), outline=(*color, 220), width=4)
        sem_draw.text((local[0] + 5, local[1] + 3), f"{object_id}:{kind}", fill=(*color, 255), font=get_font(22))
    Image.alpha_composite(semantic_overlay, layer).convert("RGB").save(ROOT / "overlays" / "semantic_overlay_p682.png")

    with (ROOT / "tables" / "objects_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["object_id", "kind", "x0_px", "y0_px", "x1_px", "y1_px"])
        for object_id, kind, box in OBJECTS:
            writer.writerow([object_id, kind, *box])

    with (ROOT / "tables" / "pairs_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "object_a", "object_b", "bbox_relation", "bbox_overlap_area_px2", "edge_gap_x_px", "edge_gap_y_px"])
        for index, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
            relation, overlap, gx, gy = gap_and_overlap(a[2], b[2])
            writer.writerow([f"P{index:03d}", a[0], b[0], relation, overlap, gx, gy])

    text_overlay = figure.copy()
    text_draw = ImageDraw.Draw(text_overlay)
    words = []
    chars = []
    with pdfplumber.open(PDF) as pdf:
        page = pdf.pages[681]
        for idx, word in enumerate(page.extract_words(extra_attrs=["fontname", "size"]), 1):
            box = tuple(round(float(word[k]) * SCALE) for k in ("x0", "top", "x1", "bottom"))
            if box[2] < FIGURE_CROP[0] or box[0] > FIGURE_CROP[2] or box[3] < FIGURE_CROP[1] or box[1] > FIGURE_CROP[3]:
                continue
            words.append((f"W{len(words)+1:03d}", word["text"], word["fontname"], float(word["size"]), box))
        for ch in page.chars:
            box = tuple(round(float(ch[k]) * SCALE) for k in ("x0", "top", "x1", "bottom"))
            if box[2] < FIGURE_CROP[0] or box[0] > FIGURE_CROP[2] or box[3] < FIGURE_CROP[1] or box[1] > FIGURE_CROP[3]:
                continue
            chars.append((ch.get("text", ""), ch.get("fontname", ""), float(ch.get("size", 0.0)), box))

    for word_id, _, _, size, box in words:
        local = crop_box(box)
        text_draw.rectangle(local, outline=(230, 81, 0), width=2)
        if int(word_id[1:]) % 4 == 1:
            text_draw.text((local[0], max(0, local[1] - 19)), f"{word_id}/{size:.1f}pt", fill=(183, 28, 28), font=get_font(14))
    text_overlay.save(ROOT / "overlays" / "text_glyph_overlay_p682.png")

    with (ROOT / "tables" / "text_spans_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["text_span_id", "text", "fontname", "source_size_pt", "x0_px", "y0_px", "x1_px", "y1_px"])
        for word_id, txt, fontname, size, box in words:
            writer.writerow([word_id, txt, fontname, f"{size:.6f}", *box])

    with (ROOT / "tables" / "glyphs_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["glyph_index", "codepoint", "glyph", "fontname", "source_size_pt", "x0_px", "y0_px", "x1_px", "y1_px", "bbox_height_px"])
        for idx, (txt, fontname, size, box) in enumerate(chars, 1):
            cp = " ".join(f"U+{ord(c):04X}" for c in txt)
            writer.writerow([idx, cp, txt, fontname, f"{size:.6f}", *box, box[3] - box[1]])

    gray = image.convert("L")
    with (ROOT / "tables" / "text_pixel_metrics_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["text_span_id", "source_size_pt", "bbox_width_px", "bbox_height_px", "dark_pixel_count", "dark_ink_width_px", "dark_ink_height_px"])
        for word_id, _, _, size, box in words:
            x0, y0, x1, y1 = box
            patch = gray.crop((max(0, x0 - 2), max(0, y0 - 2), min(gray.width, x1 + 2), min(gray.height, y1 + 2)))
            px = patch.load()
            dark = []
            for yy in range(patch.height):
                for xx in range(patch.width):
                    if px[xx, yy] < 210:
                        dark.append((xx, yy))
            if dark:
                xs = [p[0] for p in dark]
                ys = [p[1] for p in dark]
                ink_w = max(xs) - min(xs) + 1
                ink_h = max(ys) - min(ys) + 1
            else:
                ink_w = 0
                ink_h = 0
            writer.writerow([word_id, f"{size:.6f}", x1 - x0, y1 - y0, len(dark), ink_w, ink_h])

    for roi_id, box in ROIS:
        crop = image.crop(box)
        crop.save(ROOT / "rois" / f"{roi_id}_native1x.png")
        crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(ROOT / "rois" / f"{roi_id}_nearest8x.png")

    with (ROOT / "tables" / "rois_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["roi_id", "x0_px", "y0_px", "x1_px", "y1_px", "native_width_px", "native_height_px", "nearest_width_px", "nearest_height_px"])
        for roi_id, box in ROIS:
            width = box[2] - box[0]
            height = box[3] - box[1]
            writer.writerow([roi_id, *box, width, height, width * 8, height * 8])


if __name__ == "__main__":
    main()
