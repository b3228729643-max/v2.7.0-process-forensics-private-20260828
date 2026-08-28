from __future__ import annotations

import argparse
import csv
import json
from itertools import combinations
from statistics import median
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--page", required=True, type=int)
    parser.add_argument("--png", required=True)
    parser.add_argument("--root", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    image = Image.open(args.png).convert("RGB")
    document = fitz.open(args.pdf)
    page = document[args.page - 1]
    scale_x = image.width / page.rect.width
    scale_y = image.height / page.rect.height

    words = []
    for word in page.get_text("words"):
        x0, y0, x1, y1, text, block, line, ordinal = word
        words.append(
            {
                "text": text,
                "bbox_pt": [x0, y0, x1, y1],
                "bbox_px": [
                    round(x0 * scale_x),
                    round(y0 * scale_y),
                    round(x1 * scale_x),
                    round(y1 * scale_y),
                ],
                "block": block,
                "line": line,
                "word": ordinal,
            }
        )

    metadata = {
        "physical_page": args.page,
        "pdf_page_size_pt": [page.rect.width, page.rect.height],
        "native_png_size_px": [image.width, image.height],
        "scale_px_per_pt": [scale_x, scale_y],
        "words": words,
    }
    (root / "mechanical_word_boxes.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Fixed after inspecting the native full page: includes both panels and the
    # complete Figure 35.5 caption, excluding adjacent body prose.
    crop_pt = (60.0, 320.0, 535.0, 530.0)
    crop_px = tuple(
        round(value * scale)
        for value, scale in zip(crop_pt, (scale_x, scale_y, scale_x, scale_y))
    )
    crop = image.crop(crop_px)
    crop.save(root / "target_figure_caption_native_300dpi.png")
    crop.convert("L").save(root / "target_figure_caption_grayscale_native_300dpi.png")

    figure_only_pt = (85.0, 320.0, 535.0, 475.0)
    figure_only_px = tuple(
        round(value * scale)
        for value, scale in zip(
            figure_only_pt, (scale_x, scale_y, scale_x, scale_y)
        )
    )
    image.crop(figure_only_px).save(root / "target_figure_only_native_300dpi.png")

    region_words = [
        word
        for word in words
        if word["bbox_pt"][0] >= crop_pt[0]
        and word["bbox_pt"][1] >= crop_pt[1]
        and word["bbox_pt"][2] <= crop_pt[2]
        and word["bbox_pt"][3] <= crop_pt[3]
    ]
    with (root / "mechanical_region_words.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "text",
                "x0_pt",
                "y0_pt",
                "x1_pt",
                "y1_pt",
                "x0_px",
                "y0_px",
                "x1_px",
                "y1_px",
                "block",
                "line",
                "word",
            ]
        )
        for word in region_words:
            writer.writerow(
                [
                    word["text"],
                    *word["bbox_pt"],
                    *word["bbox_px"],
                    word["block"],
                    word["line"],
                    word["word"],
                ]
            )

    overlay = crop.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for index, word in enumerate(region_words, start=1):
        x0, y0, x1, y1 = word["bbox_px"]
        local = (x0 - crop_px[0], y0 - crop_px[1], x1 - crop_px[0], y1 - crop_px[1])
        draw.rectangle(local, outline=(255, 0, 180), width=2)
        draw.rectangle((local[0], local[1] - 11, local[0] + 32, local[1]), fill=(255, 255, 255))
        draw.text((local[0], local[1] - 11), f"W{index:03d}", fill=(150, 0, 90), font=font)
    overlay.save(root / "target_text_overlay_native_300dpi.png")

    # The semantic overlay uses region bands and does not assert verdicts.
    semantic = crop.copy()
    sdraw = ImageDraw.Draw(semantic)
    bands_pt = [
        ("LEFT_PANEL", 91.0, 320.5, 299.0, 472.0, (0, 90, 255)),
        ("RIGHT_PANEL", 323.0, 320.5, 531.0, 472.0, (255, 90, 0)),
        ("CAPTION", 60.0, 480.0, 535.0, 530.0, (160, 0, 180)),
    ]
    for label, x0, y0, x1, y1, color in bands_pt:
        local = (
            round(x0 * scale_x) - crop_px[0],
            round(y0 * scale_y) - crop_px[1],
            round(x1 * scale_x) - crop_px[0],
            round(y1 * scale_y) - crop_px[1],
        )
        sdraw.rectangle(local, outline=color, width=4)
        sdraw.rectangle((local[0], local[1], local[0] + 90, local[1] + 14), fill=(255, 255, 255))
        sdraw.text((local[0] + 2, local[1] + 2), label, fill=color, font=font)
    semantic.save(root / "target_semantic_overlay_native_300dpi.png")

    objects = [
        ("O01", "PANEL_BORDER", "left panel border", (114, 43, 909, 670)),
        ("O02", "TEXT", "left panel title", (353, 47, 671, 113)),
        ("O03", "LINE_ARROW", "log-evidence bidirectional arrow", (190, 180, 856, 205)),
        ("O04", "FORMULA", "log p(w) arrow label", (452, 119, 596, 158)),
        ("O05", "NODE_BORDER", "ELBO-KL decomposition bar border", (191, 218, 855, 311)),
        ("O06", "LINE", "ELBO-KL bar divider", (664, 218, 668, 311)),
        ("O07", "TEXT_FORMULA", "ELBO bar label", (292, 247, 567, 288)),
        ("O08", "TEXT", "KL gap bar label", (693, 249, 827, 290)),
        ("O09", "FORMULA", "log-evidence identity formula", (163, 368, 822, 407)),
        ("O10", "TEXT_FORMULA", "KL inequality annotation line 1", (163, 489, 861, 530)),
        ("O11", "TEXT", "KL inequality annotation line 2", (163, 535, 546, 576)),
        ("O12", "PANEL_BORDER", "right panel border", (1025, 43, 1818, 670)),
        ("O13", "TEXT", "right panel title", (1122, 47, 1722, 113)),
        ("O14", "LINE_ARROW", "x axis", (1060, 492, 1759, 510)),
        ("O15", "LINE_ARROW", "y axis", (1051, 94, 1070, 501)),
        ("O16", "LINE", "x tick marks group", (1057, 489, 1735, 512)),
        ("O17", "TEXT", "x tick label 0", (1051, 519, 1073, 557)),
        ("O18", "TEXT", "x tick label 1", (1163, 519, 1183, 557)),
        ("O19", "TEXT", "x tick label 2", (1273, 519, 1294, 557)),
        ("O20", "TEXT", "x tick label 3", (1384, 519, 1404, 557)),
        ("O21", "TEXT", "x tick label 4", (1494, 519, 1516, 557)),
        ("O22", "TEXT", "x tick label 5", (1606, 518, 1625, 557)),
        ("O23", "TEXT", "x tick label 6", (1716, 519, 1737, 557)),
        ("O24", "TEXT", "x axis label", (1299, 582, 1523, 622)),
        ("O25", "DATA_REFERENCE", "unknown-upper-bound dashed line", (1060, 125, 1748, 137)),
        ("O26", "TEXT", "unknown global upper bound label", (1094, 165, 1318, 205)),
        ("O27", "DATA_CURVE", "ELBO nondecreasing step curve", (1056, 203, 1735, 464)),
        ("O28", "MARKER", "ELBO update markers group", (1050, 198, 1741, 470)),
        ("O29", "TEXT", "coordinate-stable/local-stationary label", (1395, 344, 1731, 384)),
        ("O30", "TEXT", "figure caption label", (67, 683, 198, 743)),
        ("O31", "TEXT", "figure caption line 1", (239, 698, 1866, 742)),
        ("O32", "TEXT", "figure caption line 2", (67, 753, 1866, 798)),
        ("O33", "TEXT", "figure caption line 3", (67, 810, 316, 854)),
    ]

    category_colors = {
        "TEXT": (210, 0, 160),
        "TEXT_FORMULA": (210, 0, 160),
        "FORMULA": (150, 0, 220),
        "PANEL_BORDER": (0, 110, 255),
        "NODE_BORDER": (0, 160, 255),
        "LINE": (0, 150, 80),
        "LINE_ARROW": (0, 150, 80),
        "DATA_REFERENCE": (255, 120, 0),
        "DATA_CURVE": (255, 0, 0),
        "MARKER": (120, 0, 255),
    }
    object_overlay = crop.copy()
    odraw = ImageDraw.Draw(object_overlay)
    for object_id, category, label, bbox in objects:
        color = category_colors[category]
        odraw.rectangle(bbox, outline=color, width=3)
        odraw.rectangle((bbox[0], bbox[1], bbox[0] + 37, bbox[1] + 13), fill=(255, 255, 255))
        odraw.text((bbox[0] + 1, bbox[1] + 1), object_id, fill=color, font=font)
    object_overlay.save(root / "target_object_overlay_native_300dpi.png")

    with (root / "mechanical_object_index.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["object_id", "category", "label", "x0", "y0", "x1", "y1"])
        for object_id, category, label, bbox in objects:
            writer.writerow([object_id, category, label, *bbox])

    with (root / "mechanical_pair_index.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["pair_id", "object_a", "object_b"])
        for pair_number, (left, right) in enumerate(combinations(objects, 2), start=1):
            writer.writerow([f"P{pair_number:03d}", left[0], right[0]])

    def ink_metrics(bbox: tuple[int, int, int, int]) -> tuple[int, tuple[int, int, int, int] | None]:
        x0, y0, x1, y1 = bbox
        pad = 6
        ex0, ey0 = max(0, x0 - pad), max(0, y0 - pad)
        ex1, ey1 = min(crop.width, x1 + pad), min(crop.height, y1 + pad)
        patch = crop.crop((ex0, ey0, ex1, ey1))
        pixels = patch.load()
        border = []
        for x in range(patch.width):
            border.append(pixels[x, 0])
            border.append(pixels[x, patch.height - 1])
        for y in range(patch.height):
            border.append(pixels[0, y])
            border.append(pixels[patch.width - 1, y])
        bg = tuple(round(median(channel)) for channel in zip(*border))
        foreground = []
        for y in range(y0 - ey0, y1 - ey0):
            for x in range(x0 - ex0, x1 - ex0):
                rgb = pixels[x, y]
                if max(abs(rgb[channel] - bg[channel]) for channel in range(3)) >= 20:
                    foreground.append((x + ex0, y + ey0))
        if not foreground:
            return 0, None
        ix0 = min(point[0] for point in foreground)
        iy0 = min(point[1] for point in foreground)
        ix1 = max(point[0] for point in foreground) + 1
        iy1 = max(point[1] for point in foreground) + 1
        return iy1 - iy0, (ix0, iy0, ix1, iy1)

    text_categories = {"TEXT", "TEXT_FORMULA", "FORMULA"}
    with (root / "mechanical_text_ink_measurements.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["object_id", "label", "bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1", "h_ink_px", "ink_bbox"]
        )
        for object_id, category, label, bbox in objects:
            if category in text_categories:
                height, ink_bbox = ink_metrics(bbox)
                writer.writerow([object_id, label, *bbox, height, ink_bbox])

    with (root / "mechanical_vector_spans.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["text", "font", "size_pt", "flags", "x0_pt", "y0_pt", "x1_pt", "y1_pt"])
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    x0, y0, x1, y1 = span["bbox"]
                    if x0 >= crop_pt[0] and y0 >= crop_pt[1] and x1 <= crop_pt[2] and y1 <= crop_pt[3]:
                        writer.writerow([span["text"], span["font"], span["size"], span["flags"], x0, y0, x1, y1])

    rois = [
        ("roi01_left_identity", (150, 350, 835, 425)),
        ("roi02_left_kl_inequality", (150, 470, 880, 590)),
        ("roi03_right_unknown_upper", (1035, 105, 1360, 220)),
        ("roi04_right_stationary_curve", (1360, 245, 1755, 405)),
        ("roi05_right_ticks_xlabel", (1030, 475, 1770, 635)),
        ("roi06_caption_label", (55, 670, 335, 865)),
        ("roi07_interpanel_gap", (875, 25, 1065, 680)),
    ]
    for roi_id, bbox in rois:
        roi = crop.crop(bbox)
        roi.save(root / f"{roi_id}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
            root / f"{roi_id}_nearest8x.png"
        )

    print(
        json.dumps(
            {
                "crop_pt": crop_pt,
                "crop_px": crop_px,
                "region_words": len(region_words),
                "objects": len(objects),
                "pairs": len(objects) * (len(objects) - 1) // 2,
                "rois": len(rois),
            }
        )
    )


if __name__ == "__main__":
    main()
