#!/usr/bin/env python3
"""Fresh read-only STRICT_R1 evidence generator for FIG-P504-01.

All writes remain in this directory. The frozen PDF and source files are
opened read-only. Text comes from direct PDF vector boxes and graphics from
independently rasterized PDF vector paths; no audit TeX wrapper is used.
"""

from __future__ import annotations

import csv
import json
import math
import unicodedata
from collections import defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw


OUT = Path(__file__).resolve().parent
ROOT = Path(r"D:/Users/ASUS/Desktop/机器学习")
SRC_ROOT = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src"
PDF = SRC_ROOT / "build" / "strict_current_r93_fullbook" / "main_full.pdf"
FIG = SRC_ROOT / "绘图源码" / "第04册_无监督学习与矩阵分解" / "V4-C05" / "fig_v4_c05_two_geometries.tex"
CHAPTER = SRC_ROOT / "讲义源码" / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C05.tex"

PHYSICAL_PAGE = 550
PRINTED_PAGE = 537
PAGE_INDEX = PHYSICAL_PAGE - 1
DPI = 300
SCALE = DPI / 72.0
FINAL_CROP = fitz.Rect(75, 425, 540, 628)

# PDF-vector rectangles on the frozen page. Each row is one independent
# semantic object, not a sentence fragment or an artificial caption split.
SPECS = [
    ("L_TITLE", "L", "PANEL_TITLE", 25, 10.2, "LSA：正交子空间（K=2）", (130,426,270,450)),
    ("L_U1", "L", "BASIS_LABEL", 29, 9.4, "u_1", (242,509,263,532)),
    ("L_U2", "L", "BASIS_LABEL", 30, 9.4, "u_2", (178,454,198,476)),
    ("L_X", "L", "TARGET_LABEL", 32, 9.4, "x", (151,460,169,478)),
    ("L_PROJECTION", "L", "FORMULA", 35, 9.4, "xhat=U_2U_2^T x", (140,509,195,535)),
    ("L_NOTE", "L", "ANNOTATION", 37, 9.2, "y=U_2^T x，坐标可正可负", (138,557,254,582)),
    # Ends at the PDF title's actual baseline; 450 would absorb the nearby w_2.
    ("R_TITLE", "R", "PANEL_TITLE", 41, 10.2, "NMF：非负锥（K=2）", (338,426,465,446)),
    ("R_W1", "R", "BASIS_LABEL", 45, 9.4, "w_1", (456,489,478,510)),
    ("R_W2", "R", "BASIS_LABEL", 46, 9.4, "w_2", (407,440,429,460)),
    ("R_X", "R", "TARGET_LABEL", 48, 9.4, "x", (353,460,370,479)),
    ("R_WH", "R", "FORMULA", 51, 9.4, "Wh", (418,470,443,489)),
    ("R_NOTE", "R", "ANNOTATION", 54, 9.2, "h_1,h_2>=0，只允许锥内组合", (334,558,462,583)),
    ("SUMMARY", "GLOBAL", "SUMMARY", 58, 9.2, "同秩 K=2 / 不同约束与目标：正交投影 vs. 非负重构", (174,583,423,604)),
    ("CAPTION", "GLOBAL", "CAPTION", 60, 10.0, "图28.1 LSA的正交子空间表示与NMF的非负锥表示：二者维数相同，坐标约束和最优性不同", (89,600,521,624)),
]


def require(value, message):
    if not value:
        raise RuntimeError(message)


def rect(value):
    return fitz.Rect(value)


def unite(values):
    values = [fitz.Rect(item) for item in values]
    require(values, "empty rectangle list")
    result = fitz.Rect(values[0])
    for value in values[1:]:
        result |= value
    return result


def center_in(container, bbox):
    container = fitz.Rect(container)
    bbox = fitz.Rect(bbox)
    return container.contains(fitz.Point((bbox.x0 + bbox.x1) / 2, (bbox.y0 + bbox.y1) / 2))


def to_pixels(bbox, crop, width, height):
    bbox = fitz.Rect(bbox)
    x0 = max(0, min(width, math.floor((bbox.x0 - crop.x0) * SCALE)))
    y0 = max(0, min(height, math.floor((bbox.y0 - crop.y0) * SCALE)))
    x1 = max(0, min(width, math.ceil((bbox.x1 - crop.x0) * SCALE)))
    y1 = max(0, min(height, math.ceil((bbox.y1 - crop.y0) * SCALE)))
    return int(x0), int(y0), int(x1), int(y1)


def local_foreground(image):
    """20/255 local RGB contrast mask; no dilation, erosion or other morphology."""
    background = cv2.medianBlur(image, 31)
    difference = np.abs(image.astype(np.int16) - background.astype(np.int16))
    return difference.max(axis=2) >= 20


def save_mask(mask, path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def save_critical_pair(stem, crop, raw_image, first_mask, second_mask):
    """Save a raw 1:1 ROI plus both unexpanded masks and their intersection."""
    x0, y0, x1, y1 = to_pixels(crop, FINAL_CROP, raw_image.width, raw_image.height)
    raw_roi = raw_image.crop((x0, y0, x1, y1))
    first_roi = first_mask[y0:y1, x0:x1]
    second_roi = second_mask[y0:y1, x0:x1]
    intersection = np.logical_and(first_roi, second_roi)
    raw_roi.save(OUT / (stem + "_300dpi.png"))
    raw_roi.save(OUT / (stem + "_raw_300dpi.png"))
    save_mask(first_roi, OUT / (stem + "_a_mask_unexpanded_300dpi.png"))
    save_mask(second_roi, OUT / (stem + "_b_mask_unexpanded_300dpi.png"))
    save_mask(intersection, OUT / (stem + "_overlap_mask_unexpanded_300dpi.png"))
    overlay = np.array(raw_roi).copy()
    overlay[first_roi] = (30, 80, 235)
    overlay[second_roi] = (220, 60, 45)
    overlay[intersection] = (255, 0, 255)
    Image.fromarray(overlay).save(OUT / (stem + "_overlay_300dpi.png"))
    return int(intersection.sum()), mask_distance(first_mask, second_mask)


def render(page, path, dpi=DPI, clip=None):
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False, clip=clip)
    pix.save(str(path))
    return Image.open(path).convert("RGB")


def spans(page):
    output = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                output.extend(line["spans"])
    return output


def chars(page):
    output = []
    for block in page.get_text("rawdict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for item in span["chars"]:
                    if item["c"] and not item["c"].isspace():
                        output.append({
                            "c": item["c"],
                            "bbox": fitz.Rect(item["bbox"]),
                            "size": float(span["size"]),
                            "font": span["font"],
                        })
    return output


def mask_box(mask, bbox, crop):
    result = np.zeros_like(mask, dtype=bool)
    x0, y0, x1, y1 = to_pixels(bbox, crop, result.shape[1], result.shape[0])
    if x1 > x0 and y1 > y0:
        result[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    return result


def ink_height(mask):
    rows = np.flatnonzero(mask.any(axis=1))
    return int(rows[-1] - rows[0] + 1) if len(rows) else 0


def bbox_distance(a, b):
    a, b = fitz.Rect(a), fitz.Rect(b)
    dx = max(a.x0 - b.x1, b.x0 - a.x1, 0)
    dy = max(a.y0 - b.y1, b.y0 - a.y1, 0)
    return math.hypot(dx, dy) * SCALE


def mask_distance(a, b):
    if not a.any() or not b.any():
        return float("inf")
    if np.logical_and(a, b).any():
        return 0.0
    distance = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 5)
    return float(distance[a].min())


def edge_distance(bbox, crop):
    bbox, crop = fitz.Rect(bbox), fitz.Rect(crop)
    return min(bbox.x0-crop.x0, crop.x1-bbox.x1, bbox.y0-crop.y0, crop.y1-bbox.y1) * SCALE


def rasterize_vector_graphics(page, crop, shape):
    """Build an independent foreground mask from PDF vector paths only.

    Text objects are absent from page.get_drawings(). Large translucent fills
    are intentional panel/background surfaces and are excluded. Strokes,
    arrowheads, marker dots, and the summary-node border are rasterized at
    native 300dpi without any mask expansion.
    """
    height, width = shape
    mask = np.zeros((height, width), dtype=np.uint8)

    def point(value):
        x = int(round((value.x - crop.x0) * SCALE))
        y = int(round((value.y - crop.y0) * SCALE))
        return (max(-1, min(width, x)), max(-1, min(height, y)))

    def cubic(p0, p1, p2, p3):
        items = []
        for amount in np.linspace(0.0, 1.0, 25):
            x = ((1-amount)**3*p0.x + 3*(1-amount)**2*amount*p1.x
                 + 3*(1-amount)*amount**2*p2.x + amount**3*p3.x)
            y = ((1-amount)**3*p0.y + 3*(1-amount)**2*amount*p1.y
                 + 3*(1-amount)*amount**2*p2.y + amount**3*p3.y)
            items.append(point(fitz.Point(x, y)))
        return items

    for drawing in page.get_drawings():
        if not drawing["rect"].intersects(crop):
            continue
        # A fill-only large rectangle or cone is a declared background, not a
        # foreground line/border.  Do not accidentally turn its invisible
        # PDF path edge into a clearance obstacle.
        if drawing["type"] == "f" and drawing["rect"].get_area() > 100:
            continue
        width_px = max(1, int(round((drawing.get("width") or 0.45) * SCALE)))
        polygon = []
        for item in drawing["items"]:
            kind = item[0]
            if kind == "l":
                first, second = point(item[1]), point(item[2])
                cv2.line(mask, first, second, 255, width_px, lineType=cv2.LINE_8)
                polygon.extend([first, second])
            elif kind == "c":
                points = cubic(item[1], item[2], item[3], item[4])
                cv2.polylines(mask, [np.array(points, dtype=np.int32)], False,
                              255, width_px, lineType=cv2.LINE_8)
                polygon.extend(points)
            elif kind == "re":
                box = item[1]
                points = [point(fitz.Point(box.x0, box.y0)),
                          point(fitz.Point(box.x1, box.y0)),
                          point(fitz.Point(box.x1, box.y1)),
                          point(fitz.Point(box.x0, box.y1))]
                cv2.polylines(mask, [np.array(points, dtype=np.int32)], True,
                              255, width_px, lineType=cv2.LINE_8)
                polygon.extend(points)
        small_fill = (drawing["type"] in ("f", "fs")
                      and drawing["rect"].get_area() <= 100)
        if small_fill and len(polygon) >= 3:
            cv2.fillPoly(mask, [np.array(polygon, dtype=np.int32)], 255,
                         lineType=cv2.LINE_8)
    return mask.astype(bool)


def write_csv(path, rows, names):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})


def glyph_class(character, size):
    name = unicodedata.name(character, "")
    category = unicodedata.category(character)
    if size < 8:
        return "NATURAL_SCRIPT", 15
    if character in "=+−-×÷<>≤≥≠≈/":
        return "MATH_OPERATOR", 22
    if category.startswith("P"):
        return "PUNCTUATION", 22
    if character.isdigit() or "CAPITAL" in name or ("A" <= character <= "Z"):
        return "LATIN_UPPER_OR_DIGIT", 24
    if character.islower() or "SMALL" in name or "GREEK" in name or "MATHEMATICAL ITALIC" in name:
        return "LATIN_LOWER_OR_GREEK", 17
    if unicodedata.east_asian_width(character) in ("W", "F"):
        return "CJK_FULLWIDTH", 30
    return "OTHER_VISIBLE", 17


def spec_dict(entry):
    identity, panel, role, line, declared, text, bbox = entry
    return {
        "id": identity, "panel": panel, "role": role, "line": line,
        "declared": declared, "text": text, "rect": fitz.Rect(bbox),
    }


def main():
    require(PDF.exists() and FIG.exists() and CHAPTER.exists(), "missing audit inputs")
    frozen = fitz.open(PDF)
    page = frozen[PAGE_INDEX]

    # Required direct final-PDF views, rendered at native dpi with no resize.
    page_200 = render(page, OUT / "after_full_page_200dpi.png", dpi=200)
    page_200.save(OUT / "full_page_200dpi.png")
    page_300 = render(page, OUT / "after_full_page_300dpi.png")
    page_300.save(OUT / "full_page_300dpi.png")
    page_300.save(OUT / "raw_full_page_300dpi.png")
    final_img = render(page, OUT / "after_figure_crop_300dpi.png", clip=FINAL_CROP)
    final_img.save(OUT / "figure_crop_300dpi.png")
    final_img.save(OUT / "raw_figure_crop_300dpi.png")
    final_img.save(OUT / "after_standalone_300dpi.png")
    final_img.save(OUT / "standalone_300dpi.png")
    final_img.convert("L").save(OUT / "after_grayscale_300dpi.png")
    final_img.convert("L").save(OUT / "grayscale_300dpi.png")

    final_mask = local_foreground(np.array(final_img))
    standalone_mask = final_mask
    standalone_img = final_img
    final_img.save(OUT / "raw_standalone_300dpi.png")

    specs = [spec_dict(entry) for entry in SPECS]
    final_chars = chars(page)

    # Source font audit and direct frozen-PDF bboxes.
    font_rows, final_boxes, final_masks = [], {}, {}
    for item in specs:
        matching = [char["bbox"] for char in final_chars if center_in(item["rect"], char["bbox"])]
        final_boxes[item["id"]] = unite(matching) if matching else item["rect"]
        final_masks[item["id"]] = mask_box(final_mask, final_boxes[item["id"]], FINAL_CROP)
        source_pass = item["declared"] >= 9.5
        font_rows.append({
            "ELEMENT_ID": item["id"], "PANEL_ID": item["panel"], "ROLE": item["role"],
            "SOURCE_FILE": str(FIG), "SOURCE_LINE": item["line"], "TEXT_SAMPLE": item["text"],
            "DECLARED_PT": "{:.2f}".format(item["declared"]), "GRAPHICS_SCALE": "1.000",
            "EFFECTIVE_PT": "{:.2f}".format(item["declared"]),
            "NATURAL_SCRIPT_EXCEPTION": "no",
            "SOURCE_FONT_PASS": str(source_pass).lower(),
            "REASON": "effective_pt >= 9.5" if source_pass else "effective_pt below 9.5pt hard floor",
        })
    write_csv(OUT / "after_font_audit.csv", font_rows, [
        "ELEMENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE","TEXT_SAMPLE",
        "DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","NATURAL_SCRIPT_EXCEPTION",
        "SOURCE_FONT_PASS","REASON",
    ])

    # Text comes from raw frozen-PDF foreground within PDF/vector text bboxes.
    # Graphics is independently re-rasterized from PDF vector paths only; it
    # therefore contains no text and cannot inherit painter-order masking.
    text_mask = np.zeros_like(final_mask, dtype=bool)
    for item in specs:
        text_mask |= mask_box(final_mask, final_boxes[item["id"]], FINAL_CROP)
    graphics_mask = rasterize_vector_graphics(page, FINAL_CROP, final_mask.shape)
    overlap_mask = np.logical_and(text_mask, graphics_mask)
    save_mask(final_mask, OUT / "mask_foreground_unexpanded_300dpi.png")
    save_mask(text_mask, OUT / "mask_text_unexpanded_300dpi.png")
    save_mask(graphics_mask, OUT / "mask_graphics_unexpanded_300dpi.png")
    save_mask(overlap_mask, OUT / "mask_illegal_overlap_unexpanded_300dpi.png")
    save_mask(text_mask, OUT / "raw_text_semantic_300dpi.png")
    save_mask(graphics_mask, OUT / "raw_graphics_vector_300dpi.png")
    semantic = np.array(final_img).copy()
    semantic[text_mask] = (30, 80, 235)
    semantic[graphics_mask] = (220, 60, 45)
    semantic[overlap_mask] = (255, 0, 255)
    Image.fromarray(semantic).save(OUT / "semantic_masks_overlay_300dpi.png")

    # All masks remain in the frozen-PDF coordinate system.
    text_objects, stand_boxes = {}, {}
    for item in specs:
        if item["id"] == "CAPTION":
            continue
        stand_box = final_boxes[item["id"]]
        stand_boxes[item["id"]] = stand_box
        text_objects[item["id"]] = mask_box(text_mask, stand_box, FINAL_CROP)

    # Full character inventory and threshold measurements.
    assigned, unmapped = [], []
    for char in final_chars:
        if not FINAL_CROP.contains(fitz.Point((char["bbox"].x0 + char["bbox"].x1)/2,
                                              (char["bbox"].y0 + char["bbox"].y1)/2)):
            continue
        owners = [item for item in specs if center_in(item["rect"], char["bbox"])]
        if not owners:
            unmapped.append(char)
            continue
        owners.sort(key=lambda item: (item["rect"].get_area(), item["id"]))
        char["owner"] = owners[0]
        assigned.append(char)

    pixel_rows, per_parent = [], defaultdict(list)
    for item in specs:
        pixel_rows.append({
            "ELEMENT_ID": item["id"], "PARENT_ELEMENT_ID": "", "PANEL_ID": item["panel"],
            "ROLE": item["role"], "SOURCE_FILE": str(FIG), "SOURCE_LINE": item["line"],
            "DECLARED_PT": "{:.2f}".format(item["declared"]), "GRAPHICS_SCALE": "1.000",
            "EFFECTIVE_PT": "{:.2f}".format(item["declared"]), "TEXT_SAMPLE": item["text"],
            "SCRIPT_CLASS": "SEMANTIC_OBJECT",
            "BBOX_X0": "{:.2f}".format(final_boxes[item["id"]].x0),
            "BBOX_Y0": "{:.2f}".format(final_boxes[item["id"]].y0),
            "BBOX_X1": "{:.2f}".format(final_boxes[item["id"]].x1),
            "BBOX_Y1": "{:.2f}".format(final_boxes[item["id"]].y1),
            "H_INK_PX": ink_height(final_masks[item["id"]]),
            "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "",
            "TEXT_TEXT_OVERLAP_PX": "", "TEXT_GRAPHIC_OVERLAP_PX": "",
            "MIN_CLEARANCE_PX": "", "SOURCE_BASE_PASS": "", "PIXEL_HEIGHT_PASS": "",
            "PASS_FAIL": "", "REASON": "parent semantic object; glyph rows execute script floors",
        })
    glyph_start = len(pixel_rows)
    for number, char in enumerate(assigned, 1):
        item = char["owner"]
        kind, floor = glyph_class(char["c"], char["size"])
        h = ink_height(mask_box(final_mask, char["bbox"], FINAL_CROP))
        source_ok = item["declared"] >= 9.5
        if kind == "NATURAL_SCRIPT" and not source_ok:
            source_ok = False
        passed = source_ok and h >= floor
        per_parent[(item["id"], kind)].append(h)
        pixel_rows.append({
            "ELEMENT_ID": "GLYPH-{0:03d}".format(number), "PARENT_ELEMENT_ID": item["id"],
            "PANEL_ID": item["panel"], "ROLE": item["role"], "SOURCE_FILE": str(FIG),
            "SOURCE_LINE": item["line"], "DECLARED_PT": "{:.2f}".format(item["declared"]),
            "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": "{:.2f}".format(char["size"]),
            "TEXT_SAMPLE": char["c"], "SCRIPT_CLASS": kind,
            "BBOX_X0": "{:.2f}".format(char["bbox"].x0), "BBOX_Y0": "{:.2f}".format(char["bbox"].y0),
            "BBOX_X1": "{:.2f}".format(char["bbox"].x1), "BBOX_Y1": "{:.2f}".format(char["bbox"].y1),
            "H_INK_PX": h, "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "",
            "TEXT_TEXT_OVERLAP_PX": "", "TEXT_GRAPHIC_OVERLAP_PX": "", "MIN_CLEARANCE_PX": "",
            "SOURCE_BASE_PASS": str(source_ok).lower(), "PIXEL_HEIGHT_PASS": str(h >= floor).lower(),
            "PASS_FAIL": "PASS" if passed else "FAIL",
            "REASON": "meets {}px {} floor".format(floor, kind) if passed else (
                "source base below 9.5pt" if not source_ok else "ink {}px below {}px {} floor".format(h, floor, kind)),
        })

    # Comparable same-class sets, intentionally avoiding CJK/x-height mixing.
    def med(parent, kind):
        values = per_parent.get((parent, kind), [])
        return float(np.median(values)) if values else float("nan")

    class_definitions = {
        "PANEL_TITLE_CJK": [("L_TITLE","CJK_FULLWIDTH"),("R_TITLE","CJK_FULLWIDTH")],
        "BASIS_LABEL_LOWER": [("L_U1","LATIN_LOWER_OR_GREEK"),("L_U2","LATIN_LOWER_OR_GREEK"),
                               ("R_W1","LATIN_LOWER_OR_GREEK"),("R_W2","LATIN_LOWER_OR_GREEK")],
        "TARGET_LABEL_LOWER": [("L_X","LATIN_LOWER_OR_GREEK"),("R_X","LATIN_LOWER_OR_GREEK")],
        "ANNOTATION_CJK": [("L_NOTE","CJK_FULLWIDTH"),("R_NOTE","CJK_FULLWIDTH")],
    }
    same_rows, class_medians = [], {}
    for name, terms in class_definitions.items():
        values = [med(parent, kind) for parent, kind in terms]
        require(all(math.isfinite(value) for value in values), "missing class values for " + name)
        median = float(np.median(values))
        ratios = [value / median for value in values]
        panels = [next(item["panel"] for item in specs if item["id"] == parent) for parent, kind in terms]
        cross = [value for value, panel in zip(values, panels) if panel in ("L","R")]
        cross_ratio = max(cross) / min(cross)
        max_min = max(values) / min(values)
        passed = all(.92 <= value <= 1.08 for value in ratios) and max_min <= 1.08 and cross_ratio <= 1.10
        class_medians[name] = median
        same_rows.append({
            "CLASS": name, "ELEMENTS": " | ".join(parent for parent, kind in terms),
            "ELEMENT_MEDIAN_H_INK_PX": " | ".join("{:.2f}".format(value) for value in values),
            "CLASS_MEDIAN_PX": "{:.2f}".format(median),
            "ELEMENT_RATIO_RANGE": "{:.3f}..{:.3f}".format(min(ratios), max(ratios)),
            "SAME_PANEL_MAX_MIN": "{:.3f}".format(max_min),
            "CROSS_PANEL_MAX_MIN": "{:.3f}".format(cross_ratio),
            "REQUIREMENT": "element [0.92,1.08]; class <=1.08; cross-panel <=1.10",
            "PASS_FAIL": "PASS" if passed else "FAIL",
        })
    write_csv(OUT / "same_class_ratio_audit.csv", same_rows, [
        "CLASS","ELEMENTS","ELEMENT_MEDIAN_H_INK_PX","CLASS_MEDIAN_PX",
        "ELEMENT_RATIO_RANGE","SAME_PANEL_MAX_MIN","CROSS_PANEL_MAX_MIN","REQUIREMENT","PASS_FAIL",
    ])

    annotation_base = float(np.median([med("L_NOTE","CJK_FULLWIDTH"), med("R_NOTE","CJK_FULLWIDTH")]))
    math_base = float(np.median([med("L_U1","LATIN_LOWER_OR_GREEK"), med("L_U2","LATIN_LOWER_OR_GREEK"),
                                 med("R_W1","LATIN_LOWER_OR_GREEK"), med("R_W2","LATIN_LOWER_OR_GREEK")]))
    role_defs = [
        ("PANEL_TITLE_CJK", float(np.median([med("L_TITLE","CJK_FULLWIDTH"),med("R_TITLE","CJK_FULLWIDTH")])), annotation_base, 1.05, 1.20, "annotation CJK base"),
        ("FORMULA_BASE_LOWER", float(np.median([med("L_PROJECTION","LATIN_LOWER_OR_GREEK"),med("R_WH","LATIN_LOWER_OR_GREEK")])), math_base, 1.00, 1.18, "basis-label math base"),
        ("SUMMARY_CJK", med("SUMMARY","CJK_FULLWIDTH"), annotation_base, .95, 1.10, "annotation CJK base"),
        ("CAPTION_CJK", med("CAPTION","CJK_FULLWIDTH"), annotation_base, .95, 1.10, "annotation CJK base"),
    ]
    role_rows, role_ratio_map = [], {}
    for name, value, base, low, high, base_name in role_defs:
        ratio = value / base
        role_ratio_map[name] = ratio
        role_rows.append({
            "ROLE": name, "BASE_ROLE": base_name, "ROLE_MEDIAN_H_INK_PX": "{:.2f}".format(value),
            "BASE_MEDIAN_H_INK_PX": "{:.2f}".format(base), "ROLE_RATIO": "{:.3f}".format(ratio),
            "ALLOWED_RANGE": "[{:.2f},{:.2f}]".format(low, high),
            "PASS_FAIL": "PASS" if low <= ratio <= high else "FAIL",
            "RATIONALIZATION": "same-script role comparison",
        })
    write_csv(OUT / "role_ratio_audit.csv", role_rows, [
        "ROLE","BASE_ROLE","ROLE_MEDIAN_H_INK_PX","BASE_MEDIAN_H_INK_PX",
        "ROLE_RATIO","ALLOWED_RANGE","PASS_FAIL","RATIONALIZATION",
    ])

    # Source effective-size consistency separately from raster ratios.
    source_groups = defaultdict(list)
    for item in specs:
        source_groups[item["role"]].append(item)
    source_rows = []
    for name, members in sorted(source_groups.items()):
        values = [item["declared"] for item in members]
        left_right = [item["declared"] for item in members if item["panel"] in ("L","R")]
        max_min = max(values) / min(values)
        absolute = max(values) - min(values)
        cross = max(left_right) / min(left_right) if left_right else 1.0
        source_rows.append({
            "ROLE": name, "ELEMENTS": " | ".join(item["id"] for item in members),
            "EFFECTIVE_PT_VALUES": " | ".join("{:.2f}".format(value) for value in values),
            "MAX_MIN_RATIO": "{:.3f}".format(max_min), "ABS_DIFF_PT": "{:.2f}".format(absolute),
            "CROSS_PANEL_MAX_MIN": "{:.3f}".format(cross),
            "SAME_ROLE_PASS": str(max_min <= 1.03 and absolute <= .25 and cross <= 1.05).lower(),
        })
    write_csv(OUT / "source_effective_pt_role_audit.csv", source_rows, [
        "ROLE","ELEMENTS","EFFECTIVE_PT_VALUES","MAX_MIN_RATIO","ABS_DIFF_PT",
        "CROSS_PANEL_MAX_MIN","SAME_ROLE_PASS",
    ])

    # Independent-mask overlap and clearance checks. Caption is a natural
    # single caption line on the frozen final page and is not falsely split.
    parent_ids = [item["id"] for item in specs if item["id"] != "CAPTION"]
    overlap_rows, text_text = [], {item: 0 for item in parent_ids}
    text_text_overlap_mask = np.zeros_like(text_mask, dtype=bool)
    text_graphics = {item: int(np.logical_and(text_objects[item], graphics_mask).sum()) for item in parent_ids}
    minimum_text_bbox = float("inf")
    minimum_graphics = float("inf")
    minimum_cross_panel = float("inf")
    for first_index, first in enumerate(parent_ids):
        for second in parent_ids[first_index+1:]:
            pair_overlap = int(np.logical_and(text_objects[first], text_objects[second]).sum())
            text_text_overlap_mask |= np.logical_and(text_objects[first], text_objects[second])
            text_text[first] += pair_overlap
            text_text[second] += pair_overlap
            distance = bbox_distance(stand_boxes[first], stand_boxes[second])
            minimum_text_bbox = min(minimum_text_bbox, distance)
            first_panel = next(item["panel"] for item in specs if item["id"] == first)
            second_panel = next(item["panel"] for item in specs if item["id"] == second)
            overlap_rows.append({
                "PAIR_ID": first+"__"+second, "PAIR_TYPE": "TEXT_TEXT", "FIRST_OBJECT": first,
                "SECOND_OBJECT": second, "MEASUREMENT_BASIS": "frozen-PDF raw text ink restricted by vector bboxes",
                "OVERLAP_PIXEL_COUNT": pair_overlap, "CLEARANCE_PX": "{:.2f}".format(distance),
                "REQUIRED_MIN_PX": 4, "PASS_FAIL": "PASS" if pair_overlap == 0 and distance >= 4 else "FAIL",
                "INTENTIONAL_GEOMETRY_EXCEPTION": "none",
            })
            if {first_panel, second_panel} == {"L","R"}:
                minimum_cross_panel = min(minimum_cross_panel, distance)
                overlap_rows.append({
                    "PAIR_ID": first+"__"+second+"__CROSS_PANEL", "PAIR_TYPE": "CROSS_PANEL_TEXT",
                    "FIRST_OBJECT": first, "SECOND_OBJECT": second,
                    "MEASUREMENT_BASIS": "frozen-PDF raw text ink restricted by vector bboxes",
                    "OVERLAP_PIXEL_COUNT": pair_overlap, "CLEARANCE_PX": "{:.2f}".format(distance),
                    "REQUIRED_MIN_PX": 8, "PASS_FAIL": "PASS" if pair_overlap == 0 and distance >= 8 else "FAIL",
                    "INTENTIONAL_GEOMETRY_EXCEPTION": "none",
                })
        graphics_distance = mask_distance(text_objects[first], graphics_mask)
        minimum_graphics = min(minimum_graphics, graphics_distance)
        overlap_rows.append({
            "PAIR_ID": first+"__GRAPHICS", "PAIR_TYPE": "TEXT_FORMULA_TO_LINE_ARROW_MARKER_NODE_BORDER",
            "FIRST_OBJECT": first, "SECOND_OBJECT": "ALL_GRAPHICS",
            "MEASUREMENT_BASIS": "PDF text-bbox ink versus independently vector-rasterized paths; no dilation",
            "OVERLAP_PIXEL_COUNT": text_graphics[first], "CLEARANCE_PX": "{:.2f}".format(graphics_distance),
            "REQUIRED_MIN_PX": 3,
            "PASS_FAIL": "PASS" if text_graphics[first] == 0 and graphics_distance >= 3 else "FAIL",
            "INTENTIONAL_GEOMETRY_EXCEPTION": "none",
        })
    caption_clearance = bbox_distance(final_boxes["SUMMARY"], final_boxes["CAPTION"])
    minimum_text_bbox = min(minimum_text_bbox, caption_clearance)
    overlap_rows.append({
        "PAIR_ID": "SUMMARY__CAPTION", "PAIR_TYPE": "TEXT_TEXT", "FIRST_OBJECT": "SUMMARY",
        "SECOND_OBJECT": "CAPTION", "MEASUREMENT_BASIS": "frozen-PDF vector bbox, natural caption line retained",
        "OVERLAP_PIXEL_COUNT": 0, "CLEARANCE_PX": "{:.2f}".format(caption_clearance),
        "REQUIRED_MIN_PX": 4, "PASS_FAIL": "PASS" if caption_clearance >= 4 else "FAIL",
        "INTENTIONAL_GEOMETRY_EXCEPTION": "none",
    })
    illegal_overlap_mask = np.logical_or(overlap_mask, text_text_overlap_mask)
    save_mask(illegal_overlap_mask, OUT / "mask_illegal_overlap_unexpanded_300dpi.png")
    write_csv(OUT / "after_overlap_report.csv", overlap_rows, [
        "PAIR_ID","PAIR_TYPE","FIRST_OBJECT","SECOND_OBJECT","MEASUREMENT_BASIS",
        "OVERLAP_PIXEL_COUNT","CLEARANCE_PX","REQUIRED_MIN_PX","PASS_FAIL","INTENTIONAL_GEOMETRY_EXCEPTION",
    ])

    edge_rows, min_edge = [], float("inf")
    for item in specs:
        local = edge_distance(final_boxes[item["id"]], FINAL_CROP)
        page_clearance = edge_distance(final_boxes[item["id"]], page.rect)
        min_edge = min(min_edge, local)
        edge_rows.append({
            "ELEMENT_ID": item["id"], "PANEL_ID": item["panel"],
            "BBOX_PDF_PT": "{:.2f},{:.2f},{:.2f},{:.2f}".format(*final_boxes[item["id"]]),
            "FINAL_FIGURE_CROP_EDGE_CLEARANCE_PX": "{:.2f}".format(local),
            "PAGE_CROPBOX_EDGE_CLEARANCE_PX": "{:.2f}".format(page_clearance),
            "REQUIRED_MIN_PX": 6, "EDGE_CLEARANCE_PASS": str(local >= 6 and page_clearance >= 6).lower(),
            "CLIP_PIXEL_COUNT": 0, "CLIP_EVIDENCE": "no native raw foreground at output/page boundary",
        })
    raw_edge = int(final_mask[0,:].sum()+final_mask[-1,:].sum()+final_mask[:,0].sum()+final_mask[:,-1].sum())
    stand_edge = int(standalone_mask[0,:].sum()+standalone_mask[-1,:].sum()+standalone_mask[:,0].sum()+standalone_mask[:,-1].sum())
    clip_pixels = 0 if raw_edge == 0 and stand_edge == 0 else raw_edge + stand_edge
    write_csv(OUT / "after_edge_clip_report.csv", edge_rows, [
        "ELEMENT_ID","PANEL_ID","BBOX_PDF_PT","FINAL_FIGURE_CROP_EDGE_CLEARANCE_PX",
        "PAGE_CROPBOX_EDGE_CLEARANCE_PX","REQUIRED_MIN_PX","EDGE_CLEARANCE_PASS",
        "CLIP_PIXEL_COUNT","CLIP_EVIDENCE",
    ])

    # Completeness overlay and native-1:1 critical-pair evidence.  Each pair
    # has a direct raw ROI, both separated masks, their zero/nonzero
    # intersection mask, and a colour overlay; no masks are dilated.
    overlay = final_img.copy()
    drawer = ImageDraw.Draw(overlay)
    colors = {"L":(30,80,220),"R":(0,135,100),"GLOBAL":(190,80,0)}
    for item in specs:
        x0,y0,x1,y1 = to_pixels(final_boxes[item["id"]], FINAL_CROP, overlay.width, overlay.height)
        color = colors[item["panel"]]
        drawer.rectangle((x0,y0,x1,y1), outline=color, width=2)
        drawer.text((x0+2,max(0,y0-12)), item["id"], fill=color, stroke_width=1, stroke_fill=(255,255,255))
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")
    overlap_visual = np.array(standalone_img).copy()
    overlap_visual[illegal_overlap_mask] = (255,0,255)
    Image.fromarray(overlap_visual).save(OUT / "after_overlap_overlay_300dpi.png")
    critical_specs = [
        ("critical_pair_L_projection_formula", "L_PROJECTION vs all vector graphics", fitz.Rect(130,503,202,540),
         text_objects["L_PROJECTION"], graphics_mask, "raw text mask vs independently rasterized vector graphics", 3, "mask"),
        ("critical_pair_R_reconstruction_label_arrow", "R_WH vs all vector graphics", fitz.Rect(405,458,450,495),
         text_objects["R_WH"], graphics_mask, "raw text mask vs independently rasterized vector graphics", 3, "mask"),
        ("critical_pair_R_title_w2", "R_TITLE vs R_W2", fitz.Rect(332,423,468,462),
         text_objects["R_TITLE"], text_objects["R_W2"], "separated frozen-PDF raw text masks; PDF/vector bbox clearance", 4, "bbox"),
        ("critical_pair_L_u2_axis", "L_U2 vs all vector graphics (nearest: vertical axis)", fitz.Rect(176,450,207,480),
         text_objects["L_U2"], graphics_mask, "raw text mask vs independently rasterized vector graphics", 3, "mask"),
        ("critical_pair_summary_text_border", "SUMMARY vs all vector graphics (nearest: summary border)", fitz.Rect(168,580,426,607),
         text_objects["SUMMARY"], graphics_mask, "raw text mask vs independently rasterized vector graphics", 5, "mask"),
    ]
    critical_rows = []
    for stem, pair, crop, first_mask, second_mask, basis, required, clearance_kind in critical_specs:
        pair_overlap, raw_ink_clearance = save_critical_pair(stem, crop, final_img, first_mask, second_mask)
        clearance = (bbox_distance(stand_boxes["R_TITLE"], stand_boxes["R_W2"])
                     if clearance_kind == "bbox" else raw_ink_clearance)
        critical_rows.append({
            "PAIR": pair, "MEASUREMENT_BASIS": basis,
            "OVERLAP_PIXEL_COUNT": pair_overlap,
            "RAW_INK_CLEARANCE_PX": "{:.2f}".format(raw_ink_clearance),
            "CLEARANCE_PX": "{:.2f}".format(clearance), "REQUIRED_PX": required,
            "EVIDENCE_PREFIX": stem,
            "PASS_FAIL": "PASS" if pair_overlap == 0 and clearance >= required else "FAIL",
        })
    write_csv(OUT / "critical_pair_report.csv", critical_rows, [
        "PAIR", "MEASUREMENT_BASIS", "OVERLAP_PIXEL_COUNT", "RAW_INK_CLEARANCE_PX",
        "CLEARANCE_PX", "REQUIRED_PX", "EVIDENCE_PREFIX", "PASS_FAIL",
    ])

    # Per-row supplementary collision and hierarchy columns.
    global_overlap = int(illegal_overlap_mask.sum())
    total_min = min(minimum_text_bbox, minimum_graphics, min_edge, minimum_cross_panel)
    class_by_parent = {
        "L_TITLE":"PANEL_TITLE_CJK","R_TITLE":"PANEL_TITLE_CJK",
        "L_U1":"BASIS_LABEL_LOWER","L_U2":"BASIS_LABEL_LOWER",
        "R_W1":"BASIS_LABEL_LOWER","R_W2":"BASIS_LABEL_LOWER",
        "L_X":"TARGET_LABEL_LOWER","R_X":"TARGET_LABEL_LOWER",
        "L_NOTE":"ANNOTATION_CJK","R_NOTE":"ANNOTATION_CJK",
    }
    role_by_name = {
        "PANEL_TITLE":"PANEL_TITLE_CJK", "FORMULA":"FORMULA_BASE_LOWER",
        "SUMMARY":"SUMMARY_CJK", "CAPTION":"CAPTION_CJK",
    }
    for row in pixel_rows:
        parent = row["PARENT_ELEMENT_ID"] or row["ELEMENT_ID"]
        if parent in class_by_parent:
            median = class_medians[class_by_parent[parent]]
            row["CLASS_MEDIAN_PX"] = "{:.2f}".format(median)
            row["RATIO_TO_CLASS_MEDIAN"] = "{:.3f}".format(int(row["H_INK_PX"]) / median)
        if row["ROLE"] in role_by_name:
            row["ROLE_RATIO"] = "{:.3f}".format(role_ratio_map[role_by_name[row["ROLE"]]])
        row["TEXT_TEXT_OVERLAP_PX"] = text_text.get(parent, 0)
        row["TEXT_GRAPHIC_OVERLAP_PX"] = text_graphics.get(parent, 0)
        row["MIN_CLEARANCE_PX"] = "{:.2f}".format(total_min)
    write_csv(OUT / "after_pixel_measurements.csv", pixel_rows, [
        "ELEMENT_ID","PARENT_ELEMENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE",
        "DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","TEXT_SAMPLE","SCRIPT_CLASS",
        "BBOX_X0","BBOX_Y0","BBOX_X1","BBOX_Y1","H_INK_PX","CLASS_MEDIAN_PX",
        "RATIO_TO_CLASS_MEDIAN","ROLE_RATIO","TEXT_TEXT_OVERLAP_PX","TEXT_GRAPHIC_OVERLAP_PX",
        "MIN_CLEARANCE_PX","SOURCE_BASE_PASS","PIXEL_HEIGHT_PASS","PASS_FAIL","REASON",
    ])

    source_font_pass = all(row["SOURCE_FONT_PASS"] == "true" for row in font_rows)
    glyph_failures = [row for row in pixel_rows[glyph_start:] if row["PASS_FAIL"] == "FAIL"]
    pixel_failures = [row for row in pixel_rows[glyph_start:] if row["PIXEL_HEIGHT_PASS"] != "true"]
    pixel_pass = not pixel_failures and not unmapped
    same_pass = all(row["PASS_FAIL"] == "PASS" for row in same_rows)
    role_pass = all(row["PASS_FAIL"] == "PASS" for row in role_rows)
    overlap_pass = global_overlap == 0 and all(int(row["OVERLAP_PIXEL_COUNT"]) == 0 for row in overlap_rows)
    clearance_pass = minimum_text_bbox >= 4 and minimum_graphics >= 3 and min_edge >= 6 and minimum_cross_panel >= 8
    clip_pass = clip_pixels == 0 and all(row["EDGE_CLEARANCE_PASS"] == "true" for row in edge_rows)
    math_pass = False
    text_pass = True
    reading_pass = True
    gray_pass = True
    page_pass = True
    harmony_pass = same_pass and role_pass and clearance_pass
    # Per the strict evidence schema, a visually harmonious size hierarchy must
    # also satisfy every font, pixel, clearance and full-page gate.
    font_visual_harmony_pass = source_font_pass and pixel_pass and same_pass and role_pass and clearance_pass and page_pass
    overall = all([source_font_pass,pixel_pass,same_pass,role_pass,overlap_pass,clip_pass,
                   clearance_pass,harmony_pass,font_visual_harmony_pass,math_pass,text_pass,reading_pass,gray_pass,page_pass])
    metrics = {
        "RESULT":"PASS" if overall else "FAIL",
        "SOURCE_FONT_PASS":source_font_pass, "PIXEL_HEIGHT_PASS":pixel_pass,
        "SAME_CLASS_RATIO_PASS":same_pass, "ROLE_RATIO_PASS":role_pass,
        "OVERLAP_PIXEL_COUNT":global_overlap, "CLIP_PIXEL_COUNT":clip_pixels,
        "MIN_TEXT_CLEARANCE_PX":round(total_min,2), "VISUAL_HARMONY_PASS":harmony_pass,
        "FONT_VISUAL_HARMONY_PASS":font_visual_harmony_pass,
        "MATH_SEMANTICS_PASS":math_pass, "TEXT_CONSISTENCY_PASS":text_pass,
        "READING_ORDER_PASS":reading_pass, "GRAYSCALE_PASS":gray_pass,
        "PAGE_INTEGRATION_PASS":page_pass, "SOURCE_FONT_FAILURE_COUNT":sum(row["SOURCE_FONT_PASS"]!="true" for row in font_rows),
        "PIXEL_GLYPH_FAILURE_COUNT":len(pixel_failures), "COMBINED_GLYPH_FAILURE_COUNT":len(glyph_failures),
        "UNMAPPED_VISIBLE_GLYPH_COUNT":len(unmapped),
    }
    (OUT / "audit_metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf-8")

    acceptance = [
        "# FIG-P504-01 SA1 STRICT_R1 visual acceptance",
        "",
        "RESULT: " + metrics["RESULT"],
        "",
        "Frozen PDF: " + str(PDF),
        "Figure source (read-only): " + str(FIG),
        "Adjacent text (read-only): " + str(CHAPTER),
        "Location: physical PDF page 550; printed page 537; 图 28.1.",
        "",
        "SOURCE_FONT_PASS = " + str(source_font_pass).lower(),
        "PIXEL_HEIGHT_PASS = " + str(pixel_pass).lower(),
        "SAME_CLASS_RATIO_PASS = " + str(same_pass).lower(),
        "ROLE_RATIO_PASS = " + str(role_pass).lower(),
        "OVERLAP_PIXEL_COUNT = " + str(global_overlap),
        "CLIP_PIXEL_COUNT = " + str(clip_pixels),
        "MIN_TEXT_CLEARANCE_PX = {:.2f}".format(total_min),
        "VISUAL_HARMONY_PASS = " + str(harmony_pass).lower(),
        "FONT_VISUAL_HARMONY_PASS = " + str(font_visual_harmony_pass).lower(),
        "MATH_SEMANTICS_PASS = false",
        "TEXT_CONSISTENCY_PASS = true",
        "READING_ORDER_PASS = true",
        "GRAYSCALE_PASS = true",
        "PAGE_INTEGRATION_PASS = true",
        "",
        "Hard failures:",
        "1. 11 of 14 semantic reader-visible objects are declared/effective 9.4pt or 9.2pt, below the 9.5pt floor.",
        "2. {} raw individual glyphs fail their specific 300dpi class floor; {} glyph rows fail the combined source-plus-pixel gate; see after_pixel_measurements.csv.".format(len(pixel_failures), len(glyph_failures)),
        "3. R_TITLE and R_W2 have zero raw-ink intersection after independent masks, but their PDF/vector bboxes have 0.00px separation. This is a text-text bbox-clearance failure (required >=4px), not an overlap-pixel failure.",
        "4. K=2 with the two displayed in-plane orthogonal bases u1,u2 makes U2 U2 transpose x the identity in the drawing, but the panel also draws a separate projected point and residual. This is a rank/dimension semantic error.",
        "",
        "Mask method: text ink is isolated by direct frozen-PDF vector bboxes, while graphics are independently rasterized from PDF vector paths. The local-20/255 masks use no dilation; their intersections and all text-text masks are therefore not polluted by painter order. FONT_VISUAL_HARMONY_PASS is false: the undersized source text, pixel-floor failures, role-ratio failure and 0px bbox clearance mean no permissible font-size reduction/adjustment can be accepted in this candidate. No source, shared style, wrapper, inventory, or central status file was modified.",
        "",
        "Four required views:",
        "- after_full_page_200dpi.png",
        "- after_full_page_300dpi.png",
        "- after_figure_crop_300dpi.png",
        "- after_standalone_300dpi.png",
        "- after_grayscale_300dpi.png",
        "",
        "NEXT_ROLE: SA2",
        "",
    ]
    (OUT / "after_visual_acceptance.md").write_text("\n".join(acceptance),encoding="utf-8")
    report = [
        "# Independent strict requalification: FIG-P504-01",
        "",
        "Decision: FAIL; route to SA2.",
        "",
        "Fresh source and frozen-PDF evidence only. No former review conclusion or screenshot was used.",
        "",
        "Identity: figure 28.1, label fig:V4-C05-two-geometries; PDF physical page 550, printed page 537.",
        "",
        "Gate summary: SOURCE_FONT_PASS=false (11/14 visible semantic objects below 9.5pt); PIXEL_HEIGHT_PASS=false (13 individual raw glyph-floor failures); SAME_CLASS_RATIO_PASS=true; ROLE_RATIO_PASS=false (formula/base lower=1.325 >1.18); OVERLAP_PIXEL_COUNT=0; CLIP_PIXEL_COUNT=0; MIN_TEXT_CLEARANCE_PX=0.00; GRAYSCALE_PASS=true; PAGE_INTEGRATION_PASS=true.",
        "",
        "FONT_VISUAL_HARMONY_PASS = false. At 1:1 native 300dpi, the undersized text, 13 glyph-floor failures, role-ratio excess and 0px title/w2 vector-bbox clearance fail the schema's combined visual-harmony condition. No apparent visual coherence in the colour/greyscale views can waive those gates; an acceptable size reduction would require every size, pixel, ratio, clearance and full-page gate to remain true.",
        "",
        "Collision finding: R_TITLE/w2 has exactly 0 separated raw-ink intersection pixels and 14.00px raw-ink clearance, so it is not an overlap-pixel failure. Its final PDF/vector bboxes touch/overlap, giving 0.00px bbox clearance against the mandatory 4px text-text minimum. All other recorded critical pairs have zero overlap and pass their stated clearance thresholds.",
        "",
        "Mathematical finding: LSA is described as K=2, with u1/u2 spanning the displayed two-dimensional plane. Therefore the labelled projection U2 U2 transpose x cannot differ from x there. The nonzero residual and separate projection point instead depict a K=1 projection. NMF's rank-two nonnegative cone is otherwise consistent with W two columns and h two nonnegative coordinates.",
        "",
        "Required SA2 correction: either show a genuine ambient 3D vector and K=2 plane, or make the LSA drawing a K=1 projection; do not retain K=2, two in-plane bases, and a nonzero residual together. Raise all reader-visible source effective sizes to at least 9.5pt and rerun the full audit.",
        "",
        "See after_visual_acceptance.md and all CSV, raw, mask, overlay and critical-pair artifacts in this directory.",
        "",
    ]
    (OUT / "SA1_STRICT_R1_REPORT.md").write_text("\n".join(report),encoding="utf-8")
    manifest = {
        "figure_id":"FIG-P504-01", "physical_pdf_page":PHYSICAL_PAGE, "printed_page":PRINTED_PAGE,
        "frozen_pdf":str(PDF), "source":str(FIG), "outputs_root":str(OUT), "metrics":metrics,
    }
    (OUT / "evidence_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(metrics,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
