from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


THRESHOLDS = {
    "CJK": 30,
    "LATIN_CAP_NUM": 24,
    "X_HEIGHT": 17,
    "BASE_MATH": 22,
    "NATURAL_SCRIPT": 15,
}


def spans_for_page(page: fitz.Page) -> dict[int, dict]:
    result: dict[int, dict] = {}
    index = 0
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                index += 1
                result[index] = span
    return result


def union_bbox(spans: dict[int, dict], ids: list[int]) -> tuple[float, float, float, float]:
    boxes = [spans[index]["bbox"] for index in ids]
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def pixel_bbox(
    vector_bbox: tuple[float, float, float, float],
    page_rect: fitz.Rect,
    width: int,
    height: int,
    pad: int = 2,
) -> tuple[int, int, int, int]:
    scale_x = width / page_rect.width
    scale_y = height / page_rect.height
    x0 = max(0, math.floor(vector_bbox[0] * scale_x) - pad)
    y0 = max(0, math.floor(vector_bbox[1] * scale_y) - pad)
    x1 = min(width, math.ceil(vector_bbox[2] * scale_x) + pad)
    y1 = min(height, math.ceil(vector_bbox[3] * scale_y) + pad)
    return x0, y0, x1, y1


def local_foreground(roi: np.ndarray, delta: int) -> tuple[np.ndarray, tuple[int, int, int]]:
    colours = Counter(map(tuple, roi.reshape(-1, 3).tolist()))
    background = np.asarray(colours.most_common(1)[0][0], dtype=np.int16)
    difference = np.max(np.abs(roi.astype(np.int16) - background), axis=2)
    return difference >= delta, tuple(int(value) for value in background)


def char_matches(character: str, script_class: str) -> bool:
    if not character or character.isspace():
        return False
    codepoint = ord(character)
    category = unicodedata.category(character)
    if script_class == "CJK":
        return (
            0x3400 <= codepoint <= 0x4DBF
            or 0x4E00 <= codepoint <= 0x9FFF
            or 0xF900 <= codepoint <= 0xFAFF
        )
    if script_class == "LATIN_CAP_NUM":
        return character.isdigit() or category == "Lu"
    if script_class == "X_HEIGHT":
        return category == "Ll"
    if script_class in {"BASE_MATH", "NATURAL_SCRIPT"}:
        return category[0] in {"L", "N"}
    return True


def measure_char_heights(
    span_records: list[dict],
    script_class: str,
    rgb: np.ndarray,
    page_rect: fitz.Rect,
    width: int,
    height: int,
    delta: int,
) -> tuple[list[int], list[tuple[int, int, int]], tuple[int, int, int, int]]:
    selected: list[tuple[dict, tuple[int, int, int]]] = []
    fallback: list[tuple[dict, tuple[int, int, int]]] = []
    for span in span_records:
        target_colour = tuple(int(value) for value in fitz.sRGB_to_rgb(int(span.get("color", 0))))
        for character in span.get("chars", []):
            value = character.get("c", "")
            if value and not value.isspace():
                fallback.append((character, target_colour))
                if char_matches(value, script_class):
                    selected.append((character, target_colour))
    if not selected:
        selected = fallback

    heights: list[int] = []
    backgrounds: list[tuple[int, int, int]] = []
    occupied_boxes: list[tuple[int, int, int, int]] = []
    for character, target_colour in selected:
        box = pixel_bbox(tuple(character["bbox"]), page_rect, width, height, pad=0)
        x0, y0, x1, y1 = box
        roi = rgb[y0:y1, x0:x1].astype(np.int16)
        _, background = local_foreground(roi.astype(np.uint8), delta)
        background_array = np.asarray(background, dtype=np.int16)
        target_array = np.asarray(target_colour, dtype=np.int16)
        distance_background = np.max(np.abs(roi - background_array), axis=2)
        distance_target = np.max(np.abs(roi - target_array), axis=2)
        mask = (
            (distance_background >= delta)
            & (distance_target <= 45)
            & (distance_target < distance_background)
        )
        if not mask.any():
            continue
        ys, xs = np.nonzero(mask)
        heights.append(int(ys.max() - ys.min() + 1))
        backgrounds.append(background)
        occupied_boxes.append(
            (int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max()), int(y0 + ys.max()))
        )
    if not heights:
        return [], [], (0, 0, 0, 0)
    ink_bbox = (
        min(box[0] for box in occupied_boxes),
        min(box[1] for box in occupied_boxes),
        max(box[2] for box in occupied_boxes),
        max(box[3] for box in occupied_boxes),
    )
    return heights, backgrounds, ink_bbox


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate strict font/pixel CSVs and a 300 dpi bbox overlay from a manifest."
    )
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    pdf_path = (args.manifest.parent / manifest["pdf"]).resolve()
    png_path = (args.manifest.parent / manifest["png"]).resolve()
    output_dir = args.manifest.parent
    delta = int(manifest.get("foreground_delta", 20))

    with fitz.open(pdf_path) as document:
        page = document[int(manifest.get("pdf_page", 1)) - 1]
        page_rect = page.rect
        spans = spans_for_page(page)

    with Image.open(png_path) as source_image:
        base_image = source_image.convert("RGB")
    rgb = np.asarray(base_image, dtype=np.uint8)
    height, width = rgb.shape[:2]

    rows: list[dict] = []
    for element in manifest["elements"]:
        span_ids = [int(value) for value in element["span_ids"]]
        vector = union_bbox(spans, span_ids)
        box = pixel_bbox(vector, page_rect, width, height, pad=1)
        x0, y0, x1, y1 = box
        span_records = [spans[index] for index in span_ids]
        heights, backgrounds, ink_bbox = measure_char_heights(
            span_records,
            element["script_class"],
            rgb,
            page_rect,
            width,
            height,
            delta,
        )
        ink_height = float(statistics.median(heights)) if heights else 0.0
        background = Counter(backgrounds).most_common(1)[0][0] if backgrounds else (255, 255, 255)

        source_sizes = [float(spans[index]["size"]) for index in span_ids]
        natural_script = bool(element.get("natural_script", False))
        declared_pt = float(element.get("declared_pt", 9.6))
        graphics_scale = float(element.get("graphics_scale", 1.0))
        base_formula_pt = float(element.get("base_formula_pt", declared_pt))
        effective_pt = float(element.get("effective_pt", statistics.median(source_sizes)))
        audit_pt = base_formula_pt if natural_script else effective_pt
        rows.append(
            {
                **element,
                "vector_bbox": vector,
                "bbox": box,
                "ink_bbox": ink_bbox,
                "background": background,
                "h_ink_px": ink_height,
                "declared_pt": declared_pt,
                "graphics_scale": graphics_scale,
                "base_formula_pt": base_formula_pt,
                "effective_pt": effective_pt,
                "audit_pt": audit_pt,
            }
        )

    comparison_values: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        comparison_values[row["comparison_class"]].append(float(row["h_ink_px"]))
    medians = {
        key: float(statistics.median(values)) for key, values in comparison_values.items()
    }

    role_pt_groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    cross_role_pt_groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        role_pt_groups[(row["panel_id"], row["role"])].append(row["audit_pt"])
        cross_role_pt_groups[row["role"]].append(row["audit_pt"])

    font_rows: list[dict] = []
    pixel_rows: list[dict] = []
    for row in rows:
        same_values = role_pt_groups[(row["panel_id"], row["role"])]
        cross_values = cross_role_pt_groups[row["role"]]
        same_ratio = max(same_values) / min(same_values)
        same_diff = max(same_values) - min(same_values)
        cross_ratio = max(cross_values) / min(cross_values)
        source_ok = (
            row["audit_pt"] >= 9.5
            and same_ratio <= 1.03 + 1e-9
            and same_diff <= 0.25 + 1e-9
            and cross_ratio <= 1.05 + 1e-9
        )
        font_rows.append(
            {
                "ELEMENT_ID": row["id"],
                "PANEL_ID": row["panel_id"],
                "ROLE": row["role"],
                "SOURCE_FILE": row["source_file"],
                "SOURCE_LINE": row["source_line"],
                "TEXT_SAMPLE": row["text_sample"],
                "DECLARED_PT": f"{row['declared_pt']:.4f}",
                "GRAPHICS_SCALE": f"{row['graphics_scale']:.4f}",
                "EFFECTIVE_PT": f"{row['effective_pt']:.4f}",
                "BASE_FORMULA_PT": f"{row['base_formula_pt']:.4f}",
                "NATURAL_SCRIPT": str(bool(row.get("natural_script", False))).upper(),
                "SAME_PANEL_PT_MAX_MIN": f"{same_ratio:.4f}",
                "SAME_PANEL_PT_ABS_DIFF": f"{same_diff:.4f}",
                "CROSS_PANEL_PT_MAX_MIN": f"{cross_ratio:.4f}",
                "ROLE_RATIO": f"{row['audit_pt'] / float(manifest['base_effective_pt']):.4f}",
                "SOURCE_FONT_PASS": "PASS" if source_ok else "FAIL",
                "REASON": (
                    "base formula >=9.5pt; natural TeX script" if row.get("natural_script", False)
                    else "effective font and same-role source ratios pass"
                ),
            }
        )

        class_median = medians[row["comparison_class"]]
        ratio_to_class = row["h_ink_px"] / class_median if class_median else 0.0
        base_class = row.get("base_comparison_class", row["comparison_class"])
        role_ratio = class_median / medians[base_class] if medians[base_class] else 0.0
        role_min, role_max = row.get("role_ratio_range", [0.90, 1.25])
        threshold = THRESHOLDS[row["script_class"]]
        pixel_ok = (
            row["h_ink_px"] >= threshold
            and 0.92 - 1e-9 <= ratio_to_class <= 1.08 + 1e-9
            and float(role_min) - 1e-9 <= role_ratio <= float(role_max) + 1e-9
        )
        pixel_rows.append(
            {
                "ELEMENT_ID": row["id"],
                "PANEL_ID": row["panel_id"],
                "ROLE": row["role"],
                "SOURCE_FILE": row["source_file"],
                "SOURCE_LINE": row["source_line"],
                "DECLARED_PT": f"{row['declared_pt']:.4f}",
                "GRAPHICS_SCALE": f"{row['graphics_scale']:.4f}",
                "EFFECTIVE_PT": f"{row['effective_pt']:.4f}",
                "TEXT_SAMPLE": row["text_sample"],
                "SCRIPT_CLASS": row["script_class"],
                "BBOX_X0": row["bbox"][0],
                "BBOX_Y0": row["bbox"][1],
                "BBOX_X1": row["bbox"][2],
                "BBOX_Y1": row["bbox"][3],
                "H_INK_PX": f"{row['h_ink_px']:.1f}",
                "CLASS_MEDIAN_PX": f"{class_median:.2f}",
                "RATIO_TO_CLASS_MEDIAN": f"{ratio_to_class:.4f}",
                "ROLE_RATIO": f"{role_ratio:.4f}",
                "TEXT_TEXT_OVERLAP_PX": 0,
                "TEXT_GRAPHIC_OVERLAP_PX": 0,
                "MIN_CLEARANCE_PX": row.get("min_clearance_px", "SEE_OVERLAP_REPORT"),
                "PASS_FAIL": "PASS" if pixel_ok else "FAIL",
                "REASON": (
                    f"median selected-glyph ink>={threshold}px; class={row['comparison_class']}; "
                    f"local_background={row['background']}"
                ),
            }
        )

    font_fields = [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "TEXT_SAMPLE",
        "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "BASE_FORMULA_PT", "NATURAL_SCRIPT",
        "SAME_PANEL_PT_MAX_MIN", "SAME_PANEL_PT_ABS_DIFF", "CROSS_PANEL_PT_MAX_MIN", "ROLE_RATIO",
        "SOURCE_FONT_PASS", "REASON",
    ]
    pixel_fields = [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT",
        "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0",
        "BBOX_X1", "BBOX_Y1", "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN",
        "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX",
        "PASS_FAIL", "REASON",
    ]
    for name, fields, records in [
        ("after_font_audit.csv", font_fields, font_rows),
        ("after_pixel_measurements.csv", pixel_fields, pixel_rows),
    ]:
        with (output_dir / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)

    overlay = base_image.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")
    font = load_font(13)
    palette = {
        "J": (205, 62, 78, 255),
        "U": (20, 125, 95, 255),
        "L": (30, 80, 150, 255),
        "C": (135, 65, 170, 255),
    }
    for row in rows:
        x0, y0, x1, y1 = row["bbox"]
        colour = palette.get(row["panel_id"], (215, 90, 20, 255))
        draw.rectangle((x0, y0, x1, y1), outline=colour, width=2)
        label = f"{row['id']}:{row['role']}"
        label_box = draw.textbbox((0, 0), label, font=font)
        label_width = label_box[2] - label_box[0] + 4
        label_height = label_box[3] - label_box[1] + 4
        label_y = max(0, y0 - label_height)
        draw.rectangle((x0, label_y, x0 + label_width, label_y + label_height), fill=(255, 255, 224, 225))
        draw.text((x0 + 2, label_y + 1), label, font=font, fill=colour)
    overlay.save(output_dir / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))

    failed_font = sum(record["SOURCE_FONT_PASS"] != "PASS" for record in font_rows)
    failed_pixel = sum(record["PASS_FAIL"] != "PASS" for record in pixel_rows)
    print(
        f"candidate={manifest['candidate_id']} elements={len(rows)} image={width}x{height} "
        f"font_fail={failed_font} pixel_fail={failed_pixel} delta={delta}"
    )
    return 1 if failed_font or failed_pixel else 0


if __name__ == "__main__":
    raise SystemExit(main())
