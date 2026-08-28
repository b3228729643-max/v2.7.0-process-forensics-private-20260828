from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r110_fullbook\main_full.pdf"
)
PAGE_INDEX = 681
DPI = 300
SCALE = DPI / 72.0


# Mechanical denominator only.  Human reviewer fields are intentionally absent.
# Coordinates are PDF points on physical page 682 and cover the complete figure,
# its caption marker, and caption text.
OBJECTS = [
    ("O01", "FORMULA", "joint-model formula block", (130, 65, 292, 127)),
    ("O02", "LINE_ARROW", "joint x1 axis", (116, 210, 300, 238)),
    ("O03", "LINE_ARROW", "joint x2 axis", (198, 132, 224, 321)),
    ("O04", "DATA_CURVE", "outer joint contour", (136, 132, 291, 288)),
    ("O05", "DATA_CURVE", "middle joint contour", (154, 153, 270, 267)),
    ("O06", "DATA_CURVE", "inner joint contour", (177, 177, 246, 244)),
    ("O07", "LINE_ARROW", "horizontal slice line", (124, 181, 306, 205)),
    ("O08", "FORMULA", "horizontal slice label", (101, 160, 166, 201)),
    ("O09", "LINE_ARROW", "vertical slice line", (230, 139, 237, 286)),
    ("O10", "FORMULA", "vertical slice label and leader", (232, 127, 304, 153)),
    ("O11", "MARKER", "slice intersection marker", (228, 179, 242, 195)),
    ("O12", "FORMULA", "intersection label and leader", (236, 153, 286, 195)),
    ("O13", "TEXT", "joint-contour geometry statement", (101, 292, 309, 307)),
    ("O14", "LINE_ARROW", "horizontal-section mapping arrow", (284, 169, 333, 206)),
    ("O15", "FORMULA", "horizontal-section mapping label", (275, 150, 332, 187)),
    ("O16", "FORMULA", "upper conditional formula block", (329, 64, 520, 148)),
    ("O17", "LINE_ARROW", "upper conditional axes", (332, 125, 506, 189)),
    ("O18", "DATA_CURVE", "upper conditional density", (341, 140, 499, 207)),
    ("O19", "LINE_ARROW", "upper mean guide", (412, 140, 428, 208)),
    ("O20", "FORMULA", "upper mean label 12/25", (405, 202, 435, 228)),
    ("O21", "LINE_ARROW", "vertical-section mapping arrow", (226, 282, 336, 335)),
    ("O22", "FORMULA", "vertical-section mapping label", (264, 246, 326, 289)),
    ("O23", "FORMULA", "lower conditional formula block", (329, 210, 520, 293)),
    ("O24", "LINE_ARROW", "lower conditional axes", (332, 255, 506, 319)),
    ("O25", "DATA_CURVE", "lower conditional density", (341, 281, 499, 348)),
    ("O26", "LINE_ARROW", "lower mean guide", (416, 281, 432, 349)),
    ("O27", "FORMULA", "lower mean label 3/5", (410, 343, 439, 369)),
    ("O28", "NODE_BORDER", "zero-denominator notice border", (306, 346, 510, 403)),
    ("O29", "TEXT", "zero-denominator notice text", (319, 352, 499, 397)),
    ("O30", "TEXT", "caption marker Figure 33.2", (72, 404, 114, 428)),
    ("O31", "TEXT", "caption statement", (112, 403, 523, 446)),
]


COLORS = {
    "TEXT": (230, 55, 55, 58),
    "FORMULA": (245, 145, 20, 58),
    "LINE_ARROW": (35, 105, 220, 52),
    "MARKER": (125, 45, 185, 70),
    "NODE_BORDER": (210, 30, 150, 52),
    "DATA_CURVE": (15, 155, 105, 52),
}


def px_box(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(v * SCALE) for v in box)  # type: ignore[return-value]


def intersection_area(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def ink_height(gray: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int]:
    crop = gray.crop(box)
    extrema = crop.getextrema()
    if extrema is None:
        return 0, 0
    local_bg = extrema[1]
    threshold = max(0, local_bg - 20)
    mask = crop.point(lambda p: 255 if p <= threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return 0, 0
    return bbox[3] - bbox[1], sum(1 for p in mask.getdata() if p)


def save_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    page_image = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
    gray = page_image.convert("L")
    figure_crop = px_box((62, 55, 533, 451))
    page_image.crop(figure_crop).save(ROOT / "figure_caption_300dpi_native1x.png")
    gray.crop(figure_crop).save(ROOT / "grayscale_300dpi_native1x.png")

    critical_rois = {
        "roi_joint_cross_nearest8x.png": (214, 143, 289, 213),
        "roi_upper_peak_nearest8x.png": (398, 132, 450, 230),
        "roi_lower_peak_nearest8x.png": (402, 273, 454, 371),
        "roi_notice_caption_nearest8x.png": (302, 340, 525, 449),
        "roi_lower_map_geometry_nearest8x.png": (220, 276, 326, 318),
    }
    for name, box in critical_rois.items():
        roi = page_image.crop(px_box(box))
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(ROOT / name)

    object_rows: list[dict[str, object]] = []
    object_overlay = page_image.convert("RGBA")
    object_draw = ImageDraw.Draw(object_overlay, "RGBA")
    semantic_overlay = page_image.convert("RGBA")
    semantic_draw = ImageDraw.Draw(semantic_overlay, "RGBA")
    font = ImageFont.load_default()
    for object_id, object_class, label, pdf_box in OBJECTS:
        pbox = px_box(pdf_box)
        h_ink, ink_px = ink_height(gray, pbox)
        object_rows.append(
            {
                "object_id": object_id,
                "object_class": object_class,
                "label": label,
                "pdf_x0": pdf_box[0],
                "pdf_y0": pdf_box[1],
                "pdf_x1": pdf_box[2],
                "pdf_y1": pdf_box[3],
                "px_x0": pbox[0],
                "px_y0": pbox[1],
                "px_x1": pbox[2],
                "px_y1": pbox[3],
                "mechanical_ink_bbox_height_px": h_ink,
                "mechanical_dark_pixel_count": ink_px,
            }
        )
        outline = COLORS[object_class][:3] + (220,)
        fill = COLORS[object_class]
        object_draw.rectangle(pbox, outline=outline, width=3)
        object_draw.rectangle((pbox[0], pbox[1], pbox[0] + 35, pbox[1] + 14), fill=(255, 255, 255, 230))
        object_draw.text((pbox[0] + 1, pbox[1] + 1), object_id, fill=outline, font=font)
        semantic_draw.rectangle(pbox, fill=fill, outline=outline, width=2)

    object_overlay.crop(figure_crop).convert("RGB").save(ROOT / "object_overlay_300dpi.png")
    semantic_overlay.crop(figure_crop).convert("RGB").save(ROOT / "semantic_overlay_300dpi.png")
    save_csv(
        ROOT / "mechanical_object_denominator.csv",
        [
            "object_id",
            "object_class",
            "label",
            "pdf_x0",
            "pdf_y0",
            "pdf_x1",
            "pdf_y1",
            "px_x0",
            "px_y0",
            "px_x1",
            "px_y1",
            "mechanical_ink_bbox_height_px",
            "mechanical_dark_pixel_count",
        ],
        object_rows,
    )

    pair_rows: list[dict[str, object]] = []
    for pair_index, (left, right) in enumerate(itertools.combinations(OBJECTS, 2), start=1):
        left_id, left_class, _, left_pdf_box = left
        right_id, right_class, _, right_pdf_box = right
        left_box, right_box = px_box(left_pdf_box), px_box(right_pdf_box)
        pair_rows.append(
            {
                "pair_id": f"P{pair_index:03d}",
                "object_a": left_id,
                "object_b": right_id,
                "class_a": left_class,
                "class_b": right_class,
                "mechanical_bbox_intersection_px2": intersection_area(left_box, right_box),
                "mechanical_bbox_gap_px": f"{bbox_gap(left_box, right_box):.2f}",
            }
        )
    save_csv(
        ROOT / "mechanical_unordered_pairs.csv",
        [
            "pair_id",
            "object_a",
            "object_b",
            "class_a",
            "class_b",
            "mechanical_bbox_intersection_px2",
            "mechanical_bbox_gap_px",
        ],
        pair_rows,
    )

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    text_overlay = page_image.convert("RGBA")
    text_draw = ImageDraw.Draw(text_overlay, "RGBA")
    span_rows: list[dict[str, object]] = []
    span_index = 0
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                x0, y0, x1, y1 = span["bbox"]
                if y1 < 55 or y0 > 451:
                    continue
                span_index += 1
                span_id = f"T{span_index:03d}"
                pbox = px_box((x0, y0, x1, y1))
                h_ink, ink_px = ink_height(gray, pbox)
                span_rows.append(
                    {
                        "span_id": span_id,
                        "text": span["text"],
                        "font": span["font"],
                        "font_size_pt": f"{span['size']:.4f}",
                        "pdf_x0": f"{x0:.3f}",
                        "pdf_y0": f"{y0:.3f}",
                        "pdf_x1": f"{x1:.3f}",
                        "pdf_y1": f"{y1:.3f}",
                        "px_x0": pbox[0],
                        "px_y0": pbox[1],
                        "px_x1": pbox[2],
                        "px_y1": pbox[3],
                        "mechanical_ink_bbox_height_px": h_ink,
                        "mechanical_dark_pixel_count": ink_px,
                    }
                )
                text_draw.rectangle(pbox, outline=(230, 30, 30, 210), width=2)
                text_draw.text((pbox[0], max(0, pbox[1] - 12)), span_id, fill=(180, 0, 0, 255), font=font)
    text_overlay.crop(figure_crop).convert("RGB").save(ROOT / "text_overlay_300dpi.png")
    save_csv(
        ROOT / "mechanical_text_spans.csv",
        [
            "span_id",
            "text",
            "font",
            "font_size_pt",
            "pdf_x0",
            "pdf_y0",
            "pdf_x1",
            "pdf_y1",
            "px_x0",
            "px_y0",
            "px_x1",
            "px_y1",
            "mechanical_ink_bbox_height_px",
            "mechanical_dark_pixel_count",
        ],
        span_rows,
    )

    with (ROOT / "mechanical_summary.txt").open("w", encoding="utf-8") as stream:
        stream.write(f"page_image_px={page_image.width}x{page_image.height}\n")
        stream.write(f"figure_crop_px={figure_crop}\n")
        stream.write(f"visible_object_count={len(OBJECTS)}\n")
        stream.write(f"unordered_pair_count={len(pair_rows)}\n")
        stream.write(f"text_span_count={len(span_rows)}\n")


if __name__ == "__main__":
    main()
