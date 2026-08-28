from __future__ import annotations

import csv
import itertools
import math
from collections import Counter
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa1_r114_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
PAGE_NUMBER = 729
SCALE_300 = 300.0 / 72.0


def px_box(pdf_box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(v * SCALE_300) for v in pdf_box)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    native = Image.open(ROOT / "native_page_300dpi.png").convert("RGB")
    gray = Image.open(ROOT / "grayscale_page_300dpi.png").convert("L")

    # Fixed page-level crops in native 300 dpi pixel coordinates.
    figure_caption_box = (300, 520, 2200, 1450)
    figure_box = (300, 520, 2200, 1260)
    native.crop(figure_caption_box).save(ROOT / "figure_caption_300dpi.png")
    gray.crop(figure_caption_box).save(ROOT / "grayscale_figure_caption_300dpi.png")

    roi_box = (900, 585, 1580, 930)
    roi = native.crop(roi_box)
    roi.save(ROOT / "critical_roi_native1x.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "critical_roi_nearest8x.png"
    )

    with pdfplumber.open(PDF) as document:
        page = document.pages[PAGE_NUMBER - 1]
        words = page.extract_words(
            x_tolerance=1,
            y_tolerance=2,
            keep_blank_chars=False,
            use_text_flow=True,
            extra_attrs=["fontname", "size"],
        )
        chars = page.chars

    word_rows: list[dict[str, object]] = []
    for index, word in enumerate(words, start=1):
        if 120 <= float(word["top"]) <= 370:
            word_rows.append(
                {
                    "word_id": f"W{index:04d}",
                    "text": word["text"],
                    "x0_pt": f'{float(word["x0"]):.3f}',
                    "top_pt": f'{float(word["top"]):.3f}',
                    "x1_pt": f'{float(word["x1"]):.3f}',
                    "bottom_pt": f'{float(word["bottom"]):.3f}',
                    "x0_px": round(float(word["x0"]) * SCALE_300),
                    "top_px": round(float(word["top"]) * SCALE_300),
                    "x1_px": round(float(word["x1"]) * SCALE_300),
                    "bottom_px": round(float(word["bottom"]) * SCALE_300),
                    "fontname": word.get("fontname", ""),
                    "size_pt": f'{float(word.get("size", 0.0)):.3f}',
                }
            )
    write_csv(
        ROOT / "page729_figure_words.csv",
        [
            "word_id",
            "text",
            "x0_pt",
            "top_pt",
            "x1_pt",
            "bottom_pt",
            "x0_px",
            "top_px",
            "x1_px",
            "bottom_px",
            "fontname",
            "size_pt",
        ],
        word_rows,
    )

    char_rows: list[dict[str, object]] = []
    for index, char in enumerate(chars, start=1):
        top = float(char["top"])
        if 120 <= top <= 370:
            char_rows.append(
                {
                    "char_id": f"C{index:05d}",
                    "text": char["text"],
                    "codepoint": f'U+{ord(char["text"]):04X}' if len(char["text"]) == 1 else "MULTI",
                    "x0_pt": f'{float(char["x0"]):.3f}',
                    "top_pt": f'{top:.3f}',
                    "x1_pt": f'{float(char["x1"]):.3f}',
                    "bottom_pt": f'{float(char["bottom"]):.3f}',
                    "fontname": char.get("fontname", ""),
                    "size_pt": f'{float(char.get("size", 0.0)):.3f}',
                }
            )
    write_csv(
        ROOT / "page729_figure_chars.csv",
        [
            "char_id",
            "text",
            "codepoint",
            "x0_pt",
            "top_pt",
            "x1_pt",
            "bottom_pt",
            "fontname",
            "size_pt",
        ],
        char_rows,
    )

    objects = [
        ("T01", "TEXT", "shared_line_1", (240.831, 147.397, 390.669, 157.071)),
        ("T02", "TEXT", "shared_line_2", (250.196, 159.064, 381.304, 168.429)),
        ("T03", "TEXT", "row_model", (107.035, 198.766, 146.089, 208.530)),
        ("T04", "TEXT", "full_line_1", (195.670, 192.298, 260.082, 201.972)),
        ("T05", "FORMULA", "full_line_2", (191.387, 203.655, 264.365, 213.329)),
        ("T06", "TEXT", "point_line_1", (368.679, 192.298, 438.570, 201.972)),
        ("T07", "FORMULA", "point_line_2", (371.587, 203.655, 435.661, 213.329)),
        ("T08", "TEXT", "row_inference", (107.035, 244.120, 146.089, 253.884)),
        ("T09", "TEXT", "gibbs_line_1", (205.967, 237.652, 249.786, 247.326)),
        ("T10", "FORMULA", "gibbs_line_2", (200.752, 249.009, 254.994, 258.683)),
        ("T11", "TEXT", "vem_line_1", (371.990, 238.106, 435.259, 247.780)),
        ("T12", "TEXT", "vem_line_2", (371.779, 249.463, 435.470, 259.137)),
        ("T13", "TEXT", "warning", (219.511, 285.265, 411.989, 294.431)),
        ("T14", "TEXT", "caption_label", (76.138, 308.361, 105.456, 318.822)),
        ("T15", "TEXT", "caption_line_1", (115.419, 308.361, 507.799, 318.653)),
        ("T16", "TEXT", "caption_line_2", (76.138, 321.750, 469.801, 332.042)),
        ("N01", "NODE_BORDER", "shared", (232.0, 139.0, 400.0, 174.0)),
        ("N02", "NODE_BORDER", "full", (162.5, 185.0, 293.2, 219.5)),
        ("N03", "NODE_BORDER", "point", (338.3, 185.0, 469.0, 219.5)),
        ("N04", "NODE_BORDER", "gibbs", (162.5, 228.0, 293.2, 262.5)),
        ("N05", "NODE_BORDER", "vem", (338.3, 228.0, 469.0, 262.5)),
        ("N06", "NODE_BORDER", "warning", (151.4, 277.0, 480.3, 302.5)),
        ("E01", "LINE_ARROW", "shared_to_full", (228.0, 172.0, 298.0, 186.5)),
        ("E02", "LINE_ARROW", "shared_to_point", (334.0, 172.0, 404.0, 186.5)),
        ("E03", "LINE_ARROW", "full_to_gibbs", (225.8, 219.0, 230.0, 228.5)),
        ("E04", "LINE_ARROW", "point_to_vem", (401.4, 219.0, 405.7, 228.5)),
    ]
    object_rows = []
    for object_id, object_class, label, pdf_bbox in objects:
        pixel_bbox = px_box(pdf_bbox)
        object_rows.append(
            {
                "object_id": object_id,
                "object_class": object_class,
                "label": label,
                "x0_pt": pdf_bbox[0],
                "top_pt": pdf_bbox[1],
                "x1_pt": pdf_bbox[2],
                "bottom_pt": pdf_bbox[3],
                "x0_px": pixel_bbox[0],
                "top_px": pixel_bbox[1],
                "x1_px": pixel_bbox[2],
                "bottom_px": pixel_bbox[3],
            }
        )
    write_csv(
        ROOT / "frozen_reader_visible_objects.csv",
        [
            "object_id",
            "object_class",
            "label",
            "x0_pt",
            "top_pt",
            "x1_pt",
            "bottom_pt",
            "x0_px",
            "top_px",
            "x1_px",
            "bottom_px",
        ],
        object_rows,
    )

    text_object_boxes = {
        object_id: pdf_bbox
        for object_id, object_class, _label, pdf_bbox in objects
        if object_class in {"TEXT", "FORMULA"}
    }
    glyph_rows = []
    for char in chars:
        cx = (float(char["x0"]) + float(char["x1"])) / 2
        cy = (float(char["top"]) + float(char["bottom"])) / 2
        owner = None
        for object_id, box in text_object_boxes.items():
            if box[0] <= cx <= box[2] and box[1] <= cy <= box[3]:
                owner = object_id
                break
        if owner is None:
            continue
        text = str(char["text"])
        glyph_rows.append(
            {
                "glyph_id": f"G{len(glyph_rows) + 1:03d}",
                "object_id": owner,
                "text": text,
                "codepoint": f"U+{ord(text):04X}" if len(text) == 1 else "MULTI",
                "x0_pt": f'{float(char["x0"]):.3f}',
                "top_pt": f'{float(char["top"]):.3f}',
                "x1_pt": f'{float(char["x1"]):.3f}',
                "bottom_pt": f'{float(char["bottom"]):.3f}',
                "fontname": char.get("fontname", ""),
                "size_pt": f'{float(char.get("size", 0.0)):.3f}',
            }
        )
    write_csv(
        ROOT / "frozen_reader_visible_glyphs.csv",
        [
            "glyph_id",
            "object_id",
            "text",
            "codepoint",
            "x0_pt",
            "top_pt",
            "x1_pt",
            "bottom_pt",
            "fontname",
            "size_pt",
        ],
        glyph_rows,
    )

    object_by_id = {object_id: pdf_bbox for object_id, _cls, _label, pdf_bbox in objects}
    containment_links = [
        ("T01", "N01"),
        ("T02", "N01"),
        ("T04", "N02"),
        ("T05", "N02"),
        ("T06", "N03"),
        ("T07", "N03"),
        ("T09", "N04"),
        ("T10", "N04"),
        ("T11", "N05"),
        ("T12", "N05"),
        ("T13", "N06"),
    ]
    containment_rows = []
    for text_id, node_id in containment_links:
        text_box = px_box(object_by_id[text_id])
        node_box = px_box(object_by_id[node_id])
        clearances = {
            "left_clearance_px": text_box[0] - node_box[0],
            "top_clearance_px": text_box[1] - node_box[1],
            "right_clearance_px": node_box[2] - text_box[2],
            "bottom_clearance_px": node_box[3] - text_box[3],
        }
        containment_rows.append(
            {
                "text_object_id": text_id,
                "node_object_id": node_id,
                **clearances,
                "minimum_bbox_clearance_px": min(clearances.values()),
            }
        )
    write_csv(
        ROOT / "containment_clearance_metrics.csv",
        [
            "text_object_id",
            "node_object_id",
            "left_clearance_px",
            "top_clearance_px",
            "right_clearance_px",
            "bottom_clearance_px",
            "minimum_bbox_clearance_px",
        ],
        containment_rows,
    )

    text_metrics = []
    for object_id, object_class, label, pdf_bbox in objects:
        if object_class not in {"TEXT", "FORMULA"}:
            continue
        box = px_box(pdf_bbox)
        crop = native.crop(box)
        pixels = list(crop.getdata())
        background = Counter(pixels).most_common(1)[0][0]
        foreground = []
        for y in range(crop.height):
            for x in range(crop.width):
                pixel = crop.getpixel((x, y))
                if max(abs(pixel[c] - background[c]) for c in range(3)) >= 20:
                    foreground.append((x, y))
        active_rows = sorted({y for _x, y in foreground})
        active_columns = sorted({x for x, _y in foreground})
        text_metrics.append(
            {
                "object_id": object_id,
                "label": label,
                "object_class": object_class,
                "bbox_height_px": crop.height,
                "bbox_width_px": crop.width,
                "background_rgb": "/".join(map(str, background)),
                "foreground_pixel_count": len(foreground),
                "ink_height_px": (active_rows[-1] - active_rows[0] + 1) if active_rows else 0,
                "ink_width_px": (active_columns[-1] - active_columns[0] + 1) if active_columns else 0,
                "first_ink_row": active_rows[0] if active_rows else "",
                "last_ink_row": active_rows[-1] if active_rows else "",
            }
        )
    write_csv(
        ROOT / "pixel_ink_metrics.csv",
        [
            "object_id",
            "label",
            "object_class",
            "bbox_height_px",
            "bbox_width_px",
            "background_rgb",
            "foreground_pixel_count",
            "ink_height_px",
            "ink_width_px",
            "first_ink_row",
            "last_ink_row",
        ],
        text_metrics,
    )

    pair_rows = []
    for index, (left, right) in enumerate(itertools.combinations(objects, 2), start=1):
        left_box = px_box(left[3])
        right_box = px_box(right[3])
        dx = max(left_box[0] - right_box[2], right_box[0] - left_box[2], 0)
        dy = max(left_box[1] - right_box[3], right_box[1] - left_box[3], 0)
        ix = max(0, min(left_box[2], right_box[2]) - max(left_box[0], right_box[0]))
        iy = max(0, min(left_box[3], right_box[3]) - max(left_box[1], right_box[1]))
        pair_rows.append(
            {
                "pair_id": f"P{index:03d}",
                "left_object_id": left[0],
                "right_object_id": right[0],
                "left_class": left[1],
                "right_class": right[1],
                "bbox_dx_px": dx,
                "bbox_dy_px": dy,
                "bbox_distance_px": f"{math.hypot(dx, dy):.3f}",
                "bbox_intersection_area_px": ix * iy,
            }
        )
    write_csv(
        ROOT / "all_unordered_pairs.csv",
        [
            "pair_id",
            "left_object_id",
            "right_object_id",
            "left_class",
            "right_class",
            "bbox_dx_px",
            "bbox_dy_px",
            "bbox_distance_px",
            "bbox_intersection_area_px",
        ],
        pair_rows,
    )

    replacement_count = sum(1 for row in glyph_rows if row["codepoint"] == "U+FFFD")
    glyph_count_rows = [
        {"metric": "reader_visible_glyph_count", "value": len(glyph_rows)},
        {"metric": "replacement_character_count", "value": replacement_count},
        {
            "metric": "distinct_font_count",
            "value": len({str(row["fontname"]) for row in glyph_rows}),
        },
        {
            "metric": "distinct_codepoint_count",
            "value": len({str(row["codepoint"]) for row in glyph_rows}),
        },
    ]
    write_csv(ROOT / "glyph_machine_counts.csv", ["metric", "value"], glyph_count_rows)

    overlay = native.copy()
    draw = ImageDraw.Draw(overlay)
    palette = {
        "TEXT": (220, 20, 60),
        "FORMULA": (148, 0, 211),
        "NODE_BORDER": (0, 120, 255),
        "LINE_ARROW": (0, 160, 80),
    }
    for object_id, object_class, _label, pdf_bbox in objects:
        box = px_box(pdf_bbox)
        color = palette[object_class]
        draw.rectangle(box, outline=color, width=4)
        draw.text((box[0] + 3, max(0, box[1] - 16)), object_id, fill=color)
    overlay.crop(figure_caption_box).save(ROOT / "object_id_overlay_300dpi.png")

    semantic = native.copy()
    sem_draw = ImageDraw.Draw(semantic, "RGBA")
    for _object_id, object_class, _label, pdf_bbox in objects:
        box = px_box(pdf_bbox)
        color = palette[object_class] + (52,)
        sem_draw.rectangle(box, fill=color, outline=palette[object_class] + (255,), width=3)
    semantic.crop(figure_caption_box).save(ROOT / "semantic_class_overlay_300dpi.png")

    metrics = [
        {"metric": "page_number_physical", "value": PAGE_NUMBER, "unit": "page"},
        {"metric": "native_width", "value": native.width, "unit": "px"},
        {"metric": "native_height", "value": native.height, "unit": "px"},
        {"metric": "reader_visible_object_count", "value": len(objects), "unit": "objects"},
        {"metric": "all_unordered_pair_count", "value": len(pair_rows), "unit": "pairs"},
        {"metric": "reader_visible_glyph_count", "value": len(glyph_rows), "unit": "glyphs"},
        {"metric": "extracted_figure_word_count", "value": len(word_rows), "unit": "words"},
        {"metric": "extracted_figure_char_count", "value": len(char_rows), "unit": "chars"},
    ]
    write_csv(ROOT / "machine_summary_metrics.csv", ["metric", "value", "unit"], metrics)


if __name__ == "__main__":
    main()
