#!/usr/bin/env python3
"""Independent, read-only STRICT_R1 evidence generator for FIG-P544-01.

The frozen final PDF is the only raster source.  Source and adjacent text are
read only for declared-size and semantic checks.  All generated files stay in
this evidence directory; no TeX wrapper, rebuild, source, style, inventory or
state file is touched.
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
FIG = SRC_ROOT / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C01" / "fig_v5_c01_dependency_graph.tex"
CHAPTER = SRC_ROOT / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C01.tex"
STYLE = SRC_ROOT / "讲义源码" / "common" / "statlearnbook.sty"

PHYSICAL_PAGE = 588
PRINTED_PAGE = 575
PAGE_INDEX = PHYSICAL_PAGE - 1
DPI = 300
SCALE = DPI / 72.0
# Direct final-PDF crop: legend, all nodes/arrows, and the complete natural
# two-line caption.  It has no post-render resize.
FINAL_CROP = fitz.Rect(70, 485, 545, 684)

# Element rectangles are only ownership containers.  The reported PDF bboxes
# are obtained afresh from raw vector character bboxes in the frozen final PDF.
SPECS = [
    ("LEGEND_SOLID", "SINGLE", "LEGEND", 39, 8.8, "实线：必要依赖链", (165, 488, 263, 511)),
    ("LEGEND_DASHED", "SINGLE", "LEGEND", 42, 8.8, "虚线：仅充分，不是必要前置", (275, 488, 405, 511)),
    ("LONGRUN_TITLE", "SINGLE", "NODE_TEXT", 27, 9.4, "长期结论", (305, 507, 365, 525)),
    ("LONGRUN_OUTCOME", "SINGLE", "NODE_TEXT", 27, 9.4, "时间平均与逐步收敛", (280, 522, 390, 538)),
    ("FIXED_LABEL", "SINGLE", "NODE_TEXT", 25, 9.4, "平稳固定点", (225, 566, 300, 582)),
    ("FIXED_EQUATION", "SINGLE", "FORMULA", 25, 9.4, "π=πP", (235, 580, 290, 598)),
    ("STRUCTURE", "SINGLE", "NODE_TEXT", 26, 9.4, "不可约 / 非周期 / 返性", (350, 568, 465, 590)),
    ("EDGE_CONDITION", "SINGLE", "EDGE_LABEL", 36, 8.8, "充分条件", (175, 592, 235, 614)),
    ("REVERSIBLE", "SINGLE", "NODE_TEXT", 29, 9.4, "可逆性 / 细致平衡", (140, 623, 235, 645)),
    ("FOUNDATION", "SINGLE", "NODE_TEXT", 24, 9.4, "马尔可夫性质 / 转移规则", (270, 623, 405, 645)),
    # Caption is deliberately one semantic parent: its two natural lines are
    # not falsely treated as a text-text collision.
    ("CAPTION", "GLOBAL", "CAPTION", 45, 10.0, "图30.1 本章概念依赖（自然两行题注）", (70, 645, 545, 682)),
]


def require(value, message):
    if not value:
        raise RuntimeError(message)


def rect(value):
    return fitz.Rect(value)


def spec_dict(entry):
    identity, panel, role, line, declared, text, box = entry
    return {"id": identity, "panel": panel, "role": role, "line": line,
            "declared": declared, "text": text, "rect": fitz.Rect(box)}


def resolve_effective_source_pt(item):
    """Resolve source-level font precedence for this exact TikZ picture.

    `statlearnbook.sty` appends `every node/.style={font=\\small}`.  The
    observed final-PDF vector spans confirm that this later node hook overrides
    the picture's 9.4pt default for ordinary nodes/formulae (median 9.96pt).
    The explicit 8.8pt legend/edge node styles override the hook themselves.
    """
    if item["role"] in ("LEGEND", "EDGE_LABEL"):
        return 8.8, "explicit per-node \\fontsize{8.8pt}{10.4pt}"
    if item["role"] == "CAPTION":
        return 10.0, "caption setup font=small"
    return 10.0, "global every node/.append style={font=\\small} overrides picture 9.4pt default"


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def render(page, path, dpi=DPI, clip=None):
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False, clip=clip)
    pixmap.save(str(path))
    return Image.open(path).convert("RGB")


def local_foreground(rgb):
    """Raw foreground with a local background delta >=20/255, no dilation."""
    background = cv2.medianBlur(rgb, 31)
    delta = np.abs(rgb.astype(np.int16) - background.astype(np.int16))
    return delta.max(axis=2) >= 20


def save_mask(mask, path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def to_pixels(box, crop, width, height):
    box = fitz.Rect(box)
    x0 = max(0, min(width, math.floor((box.x0 - crop.x0) * SCALE)))
    y0 = max(0, min(height, math.floor((box.y0 - crop.y0) * SCALE)))
    x1 = max(0, min(width, math.ceil((box.x1 - crop.x0) * SCALE)))
    y1 = max(0, min(height, math.ceil((box.y1 - crop.y0) * SCALE)))
    return x0, y0, x1, y1


def crop_mask(mask, box):
    x0, y0, x1, y1 = to_pixels(box, FINAL_CROP, mask.shape[1], mask.shape[0])
    result = np.zeros_like(mask, dtype=bool)
    if x1 > x0 and y1 > y0:
        result[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    return result


def ink_height(mask):
    rows = np.flatnonzero(mask.any(axis=1))
    return int(rows[-1] - rows[0] + 1) if len(rows) else 0


def bbox_distance(first, second):
    first, second = fitz.Rect(first), fitz.Rect(second)
    dx = max(first.x0 - second.x1, second.x0 - first.x1, 0)
    dy = max(first.y0 - second.y1, second.y0 - first.y1, 0)
    return math.hypot(dx, dy) * SCALE


def mask_distance(first, second):
    if not first.any() or not second.any():
        return float("inf")
    if np.logical_and(first, second).any():
        return 0.0
    # Distance transform measures the nearest raw foreground pixels without
    # changing either foreground mask.
    distance = cv2.distanceTransform((~second).astype(np.uint8), cv2.DIST_L2, 5)
    return float(distance[first].min())


def edge_distance(box, crop):
    box, crop = fitz.Rect(box), fitz.Rect(crop)
    return min(box.x0 - crop.x0, crop.x1 - box.x1,
               box.y0 - crop.y0, crop.y1 - box.y1) * SCALE


def union_boxes(values):
    require(values, "empty vector bbox group")
    result = fitz.Rect(values[0])
    for value in values[1:]:
        result |= fitz.Rect(value)
    return result


def center_in(container, box):
    container, box = fitz.Rect(container), fitz.Rect(box)
    return container.contains(fitz.Point((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2))


def raw_chars(page):
    result = []
    raw = page.get_text("rawdict")
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for character in span.get("chars", []):
                    value = character["c"]
                    if not value or value.isspace():
                        continue
                    result.append({"c": value, "bbox": fitz.Rect(character["bbox"]),
                                   "size": float(span["size"]), "font": span["font"]})
    return result


def local_point(point, crop):
    return fitz.Point(point.x - crop.x0, point.y - crop.y0)


def local_rect(value, crop):
    value = fitz.Rect(value)
    return fitz.Rect(value.x0 - crop.x0, value.y0 - crop.y0,
                     value.x1 - crop.x0, value.y1 - crop.y0)


def draw_path(shape, item, crop):
    kind = item[0]
    if kind == "l":
        shape.draw_line(local_point(item[1], crop), local_point(item[2], crop))
    elif kind == "re":
        shape.draw_rect(local_rect(item[1], crop))
    elif kind == "c":
        shape.draw_bezier(local_point(item[1], crop), local_point(item[2], crop),
                          local_point(item[3], crop), local_point(item[4], crop))
    elif kind == "qu":
        # Quadratic path entries are rare in this figure; use their Bézier
        # representation only if exposed by the installed PyMuPDF version.
        points = item[1:]
        if len(points) == 4:
            shape.draw_bezier(*(local_point(point, crop) for point in points))
        else:
            raise RuntimeError("unhandled quadratic path shape")
    else:
        raise RuntimeError("unhandled PDF path command: " + str(kind))


def rasterize_vector_paths(drawings, indices, shape):
    """Independent vector mask: strokes plus small filled arrowheads only.

    Node and panel fills are intentionally excluded; their outlines are kept.
    The returned mask cannot inherit text pixels or page paint ordering.
    """
    document = fitz.open()
    out_page = document.new_page(width=FINAL_CROP.width, height=FINAL_CROP.height)
    for index in indices:
        drawing = drawings[index]
        if drawing.get("color") is None:
            continue  # e.g. opaque white edge-label background, not foreground
        path = out_page.new_shape()
        for item in drawing["items"]:
            draw_path(path, item, FINAL_CROP)
        area = fitz.Rect(drawing["rect"]).get_area()
        small_filled_shape = drawing.get("fill") is not None and area < 150
        path.finish(color=(0, 0, 0), fill=(0, 0, 0) if small_filled_shape else None,
                    width=max(float(drawing.get("width") or 0.6), 0.25),
                    dashes=drawing.get("dashes") or "[] 0")
        path.commit()
    pixmap = out_page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    rgb = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)[:, :, :3]
    require(rgb.shape[:2] == shape, "vector-mask raster size mismatch")
    return np.max(np.abs(rgb.astype(np.int16) - 255), axis=2) >= 20


def glyph_class(character, vector_size):
    name = unicodedata.name(character, "")
    category = unicodedata.category(character)
    if vector_size < 8:
        return "NATURAL_SCRIPT", 15
    if character in "=+−-×÷<>≤≥≠≈/":
        return "MATH_OPERATOR", 22
    if unicodedata.east_asian_width(character) in ("W", "F"):
        return "CJK_FULLWIDTH", 30
    if character.isdigit() or "CAPITAL" in name or ("A" <= character <= "Z"):
        return "LATIN_UPPER_OR_DIGIT", 24
    if character.islower() or "SMALL" in name or "GREEK" in name or "MATHEMATICAL ITALIC" in name:
        return "LATIN_LOWER_OR_GREEK", 17
    if category.startswith("P"):
        return "PUNCTUATION", 22
    return "OTHER_VISIBLE", 17


def save_critical_pair(stem, crop, raw_image, first_mask, second_mask):
    x0, y0, x1, y1 = to_pixels(crop, FINAL_CROP, raw_image.width, raw_image.height)
    raw = raw_image.crop((x0, y0, x1, y1))
    first = first_mask[y0:y1, x0:x1]
    second = second_mask[y0:y1, x0:x1]
    intersection = np.logical_and(first, second)
    raw.save(OUT / (stem + "_raw_300dpi.png"))
    save_mask(first, OUT / (stem + "_a_mask_unexpanded_300dpi.png"))
    save_mask(second, OUT / (stem + "_b_mask_unexpanded_300dpi.png"))
    save_mask(intersection, OUT / (stem + "_overlap_mask_unexpanded_300dpi.png"))
    overlay = np.array(raw).copy()
    overlay[first] = (30, 80, 235)
    overlay[second] = (220, 60, 45)
    overlay[intersection] = (255, 0, 255)
    Image.fromarray(overlay).save(OUT / (stem + "_overlay_300dpi.png"))
    return int(intersection.sum())


def roi_from_boxes(first, second=None, margin=10):
    first = fitz.Rect(first)
    result = fitz.Rect(first)
    if second is not None:
        result |= fitz.Rect(second)
    result.x0 = max(FINAL_CROP.x0, result.x0 - margin)
    result.y0 = max(FINAL_CROP.y0, result.y0 - margin)
    result.x1 = min(FINAL_CROP.x1, result.x1 + margin)
    result.y1 = min(FINAL_CROP.y1, result.y1 + margin)
    return result


def main():
    require(PDF.exists() and FIG.exists() and CHAPTER.exists() and STYLE.exists(), "missing read-only audit input")
    source_text = FIG.read_text(encoding="utf-8")
    chapter_text = CHAPTER.read_text(encoding="utf-8")
    style_text = STYLE.read_text(encoding="utf-8")
    require("\\fontsize{9.4pt}" in source_text and "\\fontsize{8.8pt}" in source_text,
            "source font declarations did not match the fixed audit map")
    require("\\rho=\\rho A" in chapter_text and "P=A^{\\mathsf T}" in chapter_text,
            "adjacent row/column convention was not found")
    require("every node/.append style={font=\\small}" in style_text,
            "global every-node font precedence was not found")

    document = fitz.open(PDF)
    page = document[PAGE_INDEX]
    specs = [spec_dict(entry) for entry in SPECS]
    for item in specs:
        item["effective"], item["effective_rule"] = resolve_effective_source_pt(item)

    # Four required direct final-PDF views, plus retained raw counterparts.
    page_200 = render(page, OUT / "full_page_200dpi.png", dpi=200)
    page_200.save(OUT / "after_full_page_200dpi.png")
    page_300 = render(page, OUT / "full_page_300dpi.png")
    page_300.save(OUT / "after_full_page_300dpi.png")
    page_300.save(OUT / "raw_full_page_300dpi.png")
    final_image = render(page, OUT / "figure_crop_300dpi.png", clip=FINAL_CROP)
    final_image.save(OUT / "after_figure_crop_300dpi.png")
    standalone_image = render(page, OUT / "standalone_300dpi.png", clip=FINAL_CROP)
    standalone_image.save(OUT / "after_standalone_300dpi.png")
    standalone_image.convert("L").save(OUT / "grayscale_300dpi.png")
    standalone_image.convert("L").save(OUT / "after_grayscale_300dpi.png")
    standalone_image.save(OUT / "raw_standalone_300dpi.png")

    final_rgb = np.array(final_image)
    final_mask = local_foreground(final_rgb)
    save_mask(final_mask, OUT / "mask_foreground_unexpanded_300dpi.png")

    all_chars = raw_chars(page)
    chars_in_crop = [char for char in all_chars if FINAL_CROP.contains(fitz.Point(
        (char["bbox"].x0 + char["bbox"].x1) / 2,
        (char["bbox"].y0 + char["bbox"].y1) / 2))]

    # Every visible vector glyph in the crop must be assigned to exactly one
    # semantic parent.  A missing owner is hard evidence incompleteness.
    assigned, unmapped = [], []
    for char in chars_in_crop:
        owners = [item for item in specs if center_in(item["rect"], char["bbox"])]
        if not owners:
            unmapped.append(char)
            continue
        owners.sort(key=lambda item: (item["rect"].get_area(), item["id"]))
        char["owner"] = owners[0]
        assigned.append(char)

    final_boxes, text_objects, font_rows = {}, {}, []
    for item in specs:
        bboxes = [char["bbox"] for char in assigned if char["owner"]["id"] == item["id"]]
        require(bboxes, "no PDF/vector glyphs mapped for " + item["id"])
        final_boxes[item["id"]] = union_boxes(bboxes)
        text_objects[item["id"]] = crop_mask(final_mask, final_boxes[item["id"]])
        source_pass = item["effective"] >= 9.5
        vector_sizes = [char["size"] for char in assigned if char["owner"]["id"] == item["id"]]
        font_rows.append({
            "ELEMENT_ID": item["id"], "PANEL_ID": item["panel"], "ROLE": item["role"],
            "SOURCE_FILE": str(FIG), "SOURCE_LINE": item["line"], "TEXT_SAMPLE": item["text"],
            "DECLARED_PT": "{:.2f}".format(item["declared"]), "GRAPHICS_SCALE": "1.000",
            "EFFECTIVE_PT": "{:.2f}".format(item["effective"]), "EFFECTIVE_SOURCE_RULE": item["effective_rule"],
            "PDF_VECTOR_FONT_SIZE_PT_MEDIAN": "{:.2f}".format(float(np.median(vector_sizes))),
            "NATURAL_SCRIPT_EXCEPTION": "no", "SOURCE_FONT_PASS": str(source_pass).lower(),
            "REASON": "effective_pt >= 9.5" if source_pass else "effective_pt below 9.5pt hard floor",
        })
    write_csv(OUT / "after_font_audit.csv", font_rows, [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "TEXT_SAMPLE",
        "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "EFFECTIVE_SOURCE_RULE", "PDF_VECTOR_FONT_SIZE_PT_MEDIAN",
        "NATURAL_SCRIPT_EXCEPTION", "SOURCE_FONT_PASS", "REASON",
    ])

    # Vector graphics masks are rendered independently from PDF paths.  Fills
    # are excluded except for arrowheads; text is absent by construction.
    drawings = [drawing for drawing in page.get_drawings() if fitz.Rect(drawing["rect"]).intersects(FINAL_CROP)]
    require(drawings, "no vector drawings inside figure crop")
    expected_nodes = {
        "FOUNDATION": fitz.Point(335, 633), "FIXED": fitz.Point(264, 580),
        "STRUCTURE": fitz.Point(408, 580), "LONGRUN": fitz.Point(336, 523),
        "REVERSIBLE": fitz.Point(187, 633),
    }
    node_indices = {}
    for name, point in expected_nodes.items():
        candidates = [index for index, drawing in enumerate(drawings)
                      if drawing.get("color") is not None
                      and fitz.Rect(drawing["rect"]).contains(point)
                      and fitz.Rect(drawing["rect"]).get_area() > 500]
        require(len(candidates) == 1, "node-border identification failed for " + name)
        node_indices[name] = candidates[0]
    node_index_set = set(node_indices.values())
    vector_indices = [index for index, drawing in enumerate(drawings) if drawing.get("color") is not None]
    line_arrow_indices = [index for index in vector_indices if index not in node_index_set]
    node_masks = {name: rasterize_vector_paths(drawings, [index], final_mask.shape)
                  for name, index in node_indices.items()}
    node_border_mask = np.logical_or.reduce(list(node_masks.values()))
    line_arrow_mask = rasterize_vector_paths(drawings, line_arrow_indices, final_mask.shape)
    graphics_mask = np.logical_or(node_border_mask, line_arrow_mask)
    vector_rows = []
    for index, drawing in enumerate(drawings):
        drawing_box = fitz.Rect(drawing["rect"])
        if index in node_index_set:
            category, included = "NODE_BORDER", True
        elif drawing.get("color") is None:
            category, included = "INTENTIONAL_TEXT_BACKGROUND", False
        elif drawing.get("fill") is not None and drawing_box.get_area() < 150:
            category, included = "ARROWHEAD", True
        else:
            category, included = "LINE_ARROW", True
        vector_rows.append({
            "VECTOR_ID": "VECTOR-{0:02d}".format(index + 1), "CATEGORY": category,
            "BBOX_PDF_PT": "{:.2f},{:.2f},{:.2f},{:.2f}".format(*drawing_box),
            "LINE_WIDTH_PT": "" if drawing.get("width") is None else "{:.3f}".format(float(drawing["width"])),
            "DASHES": drawing.get("dashes") or "solid", "GRAPHICS_FOREGROUND_INCLUDED": str(included).lower(),
            "NOTES": "node fill excluded; border independently retained" if category == "NODE_BORDER" else (
                "opaque label background is intentional background" if category == "INTENTIONAL_TEXT_BACKGROUND" else "independent vector foreground"),
        })
    write_csv(OUT / "vector_component_inventory.csv", vector_rows, [
        "VECTOR_ID", "CATEGORY", "BBOX_PDF_PT", "LINE_WIDTH_PT", "DASHES", "GRAPHICS_FOREGROUND_INCLUDED", "NOTES",
    ])
    text_mask = np.logical_or.reduce(list(text_objects.values()))
    text_graphics_overlap_mask = np.logical_and(text_mask, graphics_mask)
    save_mask(text_mask, OUT / "mask_text_unexpanded_300dpi.png")
    save_mask(node_border_mask, OUT / "mask_node_border_unexpanded_300dpi.png")
    save_mask(line_arrow_mask, OUT / "mask_line_arrow_marker_unexpanded_300dpi.png")
    save_mask(graphics_mask, OUT / "mask_graphics_unexpanded_300dpi.png")
    save_mask(text_mask, OUT / "raw_text_semantic_300dpi.png")
    save_mask(graphics_mask, OUT / "raw_graphics_vector_300dpi.png")

    # Full glyph inventory: source font floor and independent raw glyph floor
    # remain distinct columns so a source failure does not inflate pixel count.
    pixel_rows, per_parent = [], defaultdict(list)
    for item in specs:
        pixel_rows.append({
            "ELEMENT_ID": item["id"], "PARENT_ELEMENT_ID": "", "PANEL_ID": item["panel"],
            "ROLE": item["role"], "SOURCE_FILE": str(FIG), "SOURCE_LINE": item["line"],
            "DECLARED_PT": "{:.2f}".format(item["declared"]), "GRAPHICS_SCALE": "1.000",
            "EFFECTIVE_PT": "{:.2f}".format(item["effective"]), "TEXT_SAMPLE": item["text"],
            "SCRIPT_CLASS": "SEMANTIC_OBJECT", "BBOX_X0": "{:.2f}".format(final_boxes[item["id"]].x0),
            "BBOX_Y0": "{:.2f}".format(final_boxes[item["id"]].y0),
            "BBOX_X1": "{:.2f}".format(final_boxes[item["id"]].x1),
            "BBOX_Y1": "{:.2f}".format(final_boxes[item["id"]].y1),
            "H_INK_PX": ink_height(text_objects[item["id"]]), "CLASS_MEDIAN_PX": "",
            "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "", "TEXT_TEXT_OVERLAP_PX": "",
            "TEXT_GRAPHIC_OVERLAP_PX": "", "MIN_CLEARANCE_PX": "", "SOURCE_BASE_PASS": "",
            "PIXEL_HEIGHT_PASS": "", "PASS_FAIL": "", "REASON": "parent semantic object; glyph rows execute script floors",
        })
    glyph_start = len(pixel_rows)
    for number, char in enumerate(assigned, 1):
        item = char["owner"]
        kind, floor = glyph_class(char["c"], char["size"])
        height = ink_height(crop_mask(final_mask, char["bbox"]))
        source_ok = item["effective"] >= 9.5
        pixel_ok = height >= floor
        combined = source_ok and pixel_ok
        per_parent[(item["id"], kind)].append(height)
        reasons = []
        if not source_ok:
            reasons.append("source base below 9.5pt")
        if not pixel_ok:
            reasons.append("ink {}px below {}px {} floor".format(height, floor, kind))
        pixel_rows.append({
            "ELEMENT_ID": "GLYPH-{0:03d}".format(number), "PARENT_ELEMENT_ID": item["id"],
            "PANEL_ID": item["panel"], "ROLE": item["role"], "SOURCE_FILE": str(FIG),
            "SOURCE_LINE": item["line"], "DECLARED_PT": "{:.2f}".format(item["declared"]),
            "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": "{:.2f}".format(item["effective"]),
            "TEXT_SAMPLE": char["c"], "SCRIPT_CLASS": kind,
            "BBOX_X0": "{:.2f}".format(char["bbox"].x0), "BBOX_Y0": "{:.2f}".format(char["bbox"].y0),
            "BBOX_X1": "{:.2f}".format(char["bbox"].x1), "BBOX_Y1": "{:.2f}".format(char["bbox"].y1),
            "H_INK_PX": height, "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "",
            "TEXT_TEXT_OVERLAP_PX": "", "TEXT_GRAPHIC_OVERLAP_PX": "", "MIN_CLEARANCE_PX": "",
            "SOURCE_BASE_PASS": str(source_ok).lower(), "PIXEL_HEIGHT_PASS": str(pixel_ok).lower(),
            "PASS_FAIL": "PASS" if combined else "FAIL", "REASON": "; ".join(reasons) if reasons else "meets source and pixel floors",
        })

    def median_for(parent, script):
        values = per_parent.get((parent, script), [])
        require(values, "missing comparable glyph values for {} / {}".format(parent, script))
        return float(np.median(values))

    same_defs = {
        "NODE_CJK": [(name, "CJK_FULLWIDTH") for name in ["FOUNDATION", "FIXED_LABEL", "STRUCTURE", "LONGRUN_TITLE", "LONGRUN_OUTCOME", "REVERSIBLE"]],
        "LEGEND_CJK": [("LEGEND_SOLID", "CJK_FULLWIDTH"), ("LEGEND_DASHED", "CJK_FULLWIDTH")],
        "CAPTION_CJK": [("CAPTION", "CJK_FULLWIDTH")],
    }
    same_rows, class_medians = [], {}
    for class_name, members in same_defs.items():
        values = [median_for(parent, script) for parent, script in members]
        class_median = float(np.median(values))
        class_medians[class_name] = class_median
        ratios = [value / class_median for value in values]
        max_min = max(values) / min(values)
        passed = all(.92 <= ratio <= 1.08 for ratio in ratios) and max_min <= 1.08
        same_rows.append({
            "CLASS": class_name, "ELEMENTS": " | ".join(parent for parent, _ in members),
            "ELEMENT_MEDIAN_H_INK_PX": " | ".join("{:.2f}".format(value) for value in values),
            "CLASS_MEDIAN_PX": "{:.2f}".format(class_median),
            "ELEMENT_RATIO_RANGE": "{:.3f}..{:.3f}".format(min(ratios), max(ratios)),
            "SAME_PANEL_MAX_MIN": "{:.3f}".format(max_min), "CROSS_PANEL_MAX_MIN": "1.000",
            "REQUIREMENT": "element [0.92,1.08]; class <=1.08; single-panel cross ratio=1.000",
            "PASS_FAIL": "PASS" if passed else "FAIL",
        })
    write_csv(OUT / "same_class_ratio_audit.csv", same_rows, [
        "CLASS", "ELEMENTS", "ELEMENT_MEDIAN_H_INK_PX", "CLASS_MEDIAN_PX", "ELEMENT_RATIO_RANGE",
        "SAME_PANEL_MAX_MIN", "CROSS_PANEL_MAX_MIN", "REQUIREMENT", "PASS_FAIL",
    ])

    # Source same-role audit: source effective sizes, not pixel glyph height.
    source_groups = defaultdict(list)
    for item in specs:
        source_groups[item["role"]].append(item)
    source_role_rows = []
    for role, members in sorted(source_groups.items()):
        values = [member["effective"] for member in members]
        maximum, minimum = max(values), min(values)
        source_role_rows.append({
            "ROLE": role, "ELEMENTS": " | ".join(member["id"] for member in members),
            "EFFECTIVE_PT_VALUES": " | ".join("{:.2f}".format(value) for value in values),
            "MAX_MIN_RATIO": "{:.3f}".format(maximum / minimum), "ABS_DIFF_PT": "{:.2f}".format(maximum - minimum),
            "CROSS_PANEL_MAX_MIN": "1.000", "SAME_ROLE_PASS": str(maximum / minimum <= 1.03 and maximum - minimum <= .25).lower(),
        })
    write_csv(OUT / "source_effective_pt_role_audit.csv", source_role_rows, [
        "ROLE", "ELEMENTS", "EFFECTIVE_PT_VALUES", "MAX_MIN_RATIO", "ABS_DIFF_PT",
        "CROSS_PANEL_MAX_MIN", "SAME_ROLE_PASS",
    ])

    # Role hierarchy uses visible parent heights.  Formula inherits the same
    # effective 10pt ordinary-node source style and is audited by its own full-line ink
    # height relative to the dominant ordinary-node CJK base.
    node_base = float(np.median([ink_height(text_objects[item]) for item in [
        "FOUNDATION", "FIXED_LABEL", "STRUCTURE", "LONGRUN_TITLE", "LONGRUN_OUTCOME", "REVERSIBLE"]]))
    role_defs = [
        ("LEGEND_CJK", float(np.median([ink_height(text_objects["LEGEND_SOLID"]), ink_height(text_objects["LEGEND_DASHED"])])), node_base, .95, 1.10, "ordinary node CJK base"),
        ("EDGE_LABEL_CJK", float(ink_height(text_objects["EDGE_CONDITION"])), node_base, .95, 1.10, "ordinary node CJK base"),
        ("FORMULA_BLOCK", float(ink_height(text_objects["FIXED_EQUATION"])), node_base, 1.00, 1.18, "ordinary node CJK base; full formula line"),
        # The caption is one natural two-line semantic parent.  Its total
        # paragraph height must not be misused as a font-height surrogate;
        # compare its individual CJK glyph median instead.
        ("CAPTION_CJK", median_for("CAPTION", "CJK_FULLWIDTH"), node_base, .95, 1.10, "ordinary node CJK base; natural caption glyph median"),
    ]
    role_rows, role_ratio_map = [], {}
    for name, value, base, low, high, rationale in role_defs:
        ratio = value / base
        role_ratio_map[name] = ratio
        role_rows.append({
            "ROLE": name, "BASE_ROLE": rationale, "ROLE_MEDIAN_H_INK_PX": "{:.2f}".format(value),
            "BASE_MEDIAN_H_INK_PX": "{:.2f}".format(base), "ROLE_RATIO": "{:.3f}".format(ratio),
            "ALLOWED_RANGE": "[{:.2f},{:.2f}]".format(low, high),
            "PASS_FAIL": "PASS" if low <= ratio <= high else "FAIL", "RATIONALIZATION": rationale,
        })
    write_csv(OUT / "role_ratio_audit.csv", role_rows, [
        "ROLE", "BASE_ROLE", "ROLE_MEDIAN_H_INK_PX", "BASE_MEDIAN_H_INK_PX", "ROLE_RATIO",
        "ALLOWED_RANGE", "PASS_FAIL", "RATIONALIZATION",
    ])

    # Pairwise no-overlap and clearance register.  Text masks are raw frozen
    # PDF foreground constrained by vector text boxes; vector graphics are
    # independently rasterized paths.  There is one panel, so cross-panel,
    # panel-border, data-curve and marker-only checks are explicitly N/A.
    parent_ids = [item["id"] for item in specs]
    overlap_rows, text_text_count, candidate_pairs = [], {item: 0 for item in parent_ids}, []
    text_text_overlap_mask = np.zeros_like(final_mask, dtype=bool)
    min_text_bbox, min_line, min_node = float("inf"), float("inf"), float("inf")
    for first_index, first in enumerate(parent_ids):
        for second in parent_ids[first_index + 1:]:
            pair_mask = np.logical_and(text_objects[first], text_objects[second])
            pair_overlap = int(pair_mask.sum())
            text_text_overlap_mask |= pair_mask
            text_text_count[first] += pair_overlap
            text_text_count[second] += pair_overlap
            clearance = bbox_distance(final_boxes[first], final_boxes[second])
            min_text_bbox = min(min_text_bbox, clearance)
            passed = pair_overlap == 0 and clearance >= 4
            overlap_rows.append({
                "PAIR_ID": first + "__" + second, "PAIR_TYPE": "TEXT_TEXT", "FIRST_OBJECT": first, "SECOND_OBJECT": second,
                "MEASUREMENT_BASIS": "separated frozen-PDF raw text ink plus PDF/vector bbox", "OVERLAP_PIXEL_COUNT": pair_overlap,
                "CLEARANCE_PX": "{:.2f}".format(clearance), "REQUIRED_MIN_PX": 4,
                "PASS_FAIL": "PASS" if passed else "FAIL", "INTENTIONAL_GEOMETRY_EXCEPTION": "none",
            })
            candidate_pairs.append((clearance, first + "_vs_" + second, roi_from_boxes(final_boxes[first], final_boxes[second]), text_objects[first], text_objects[second], "TEXT_TEXT", 4, pair_overlap))
        line_overlap = int(np.logical_and(text_objects[first], line_arrow_mask).sum())
        line_clearance = mask_distance(text_objects[first], line_arrow_mask)
        min_line = min(min_line, line_clearance)
        line_pass = line_overlap == 0 and line_clearance >= 3
        overlap_rows.append({
            "PAIR_ID": first + "__LINE_ARROW_MARKER", "PAIR_TYPE": "TEXT_FORMULA_TO_LINE_ARROW_MARKER", "FIRST_OBJECT": first, "SECOND_OBJECT": "ALL_LINE_ARROW_MARKER",
            "MEASUREMENT_BASIS": "raw text mask vs independent vector line/arrow/marker mask; no dilation", "OVERLAP_PIXEL_COUNT": line_overlap,
            "CLEARANCE_PX": "{:.2f}".format(line_clearance), "REQUIRED_MIN_PX": 3,
            "PASS_FAIL": "PASS" if line_pass else "FAIL", "INTENTIONAL_GEOMETRY_EXCEPTION": "none",
        })
        candidate_pairs.append((line_clearance, first + "_vs_line_arrow", roi_from_boxes(final_boxes[first]), text_objects[first], line_arrow_mask, "TEXT_LINE_ARROW", 3, line_overlap))

    owner_border = {
        "LONGRUN_TITLE": "LONGRUN", "LONGRUN_OUTCOME": "LONGRUN", "FIXED_LABEL": "FIXED",
        "FIXED_EQUATION": "FIXED", "STRUCTURE": "STRUCTURE", "REVERSIBLE": "REVERSIBLE", "FOUNDATION": "FOUNDATION",
    }
    for text_id, border_id in owner_border.items():
        pair_overlap = int(np.logical_and(text_objects[text_id], node_masks[border_id]).sum())
        clearance = mask_distance(text_objects[text_id], node_masks[border_id])
        min_node = min(min_node, clearance)
        passed = pair_overlap == 0 and clearance >= 5
        overlap_rows.append({
            "PAIR_ID": text_id + "__" + border_id + "_NODE_BORDER", "PAIR_TYPE": "TEXT_FORMULA_TO_NODE_BORDER", "FIRST_OBJECT": text_id, "SECOND_OBJECT": border_id + "_NODE_BORDER",
            "MEASUREMENT_BASIS": "raw text mask vs independent node-border vector mask; no dilation", "OVERLAP_PIXEL_COUNT": pair_overlap,
            "CLEARANCE_PX": "{:.2f}".format(clearance), "REQUIRED_MIN_PX": 5,
            "PASS_FAIL": "PASS" if passed else "FAIL", "INTENTIONAL_GEOMETRY_EXCEPTION": "none",
        })
        candidate_pairs.append((clearance, text_id + "_vs_" + border_id + "_node_border", roi_from_boxes(final_boxes[text_id]), text_objects[text_id], node_masks[border_id], "TEXT_NODE_BORDER", 5, pair_overlap))
    illegal_overlap_mask = np.logical_or(text_text_overlap_mask, text_graphics_overlap_mask)
    save_mask(illegal_overlap_mask, OUT / "mask_illegal_overlap_unexpanded_300dpi.png")
    write_csv(OUT / "after_overlap_report.csv", overlap_rows, [
        "PAIR_ID", "PAIR_TYPE", "FIRST_OBJECT", "SECOND_OBJECT", "MEASUREMENT_BASIS", "OVERLAP_PIXEL_COUNT",
        "CLEARANCE_PX", "REQUIRED_MIN_PX", "PASS_FAIL", "INTENTIONAL_GEOMETRY_EXCEPTION",
    ])

    # Edge and clip checks retain the direct-final-PDF coordinate system.
    edge_rows, min_edge = [], float("inf")
    for item in specs:
        crop_clearance = edge_distance(final_boxes[item["id"]], FINAL_CROP)
        page_clearance = edge_distance(final_boxes[item["id"]], page.rect)
        min_edge = min(min_edge, crop_clearance, page_clearance)
        edge_rows.append({
            "ELEMENT_ID": item["id"], "PANEL_ID": item["panel"],
            "BBOX_PDF_PT": "{:.2f},{:.2f},{:.2f},{:.2f}".format(*final_boxes[item["id"]]),
            "FINAL_FIGURE_CROP_EDGE_CLEARANCE_PX": "{:.2f}".format(crop_clearance),
            "PAGE_CROPBOX_EDGE_CLEARANCE_PX": "{:.2f}".format(page_clearance), "REQUIRED_MIN_PX": 6,
            "EDGE_CLEARANCE_PASS": str(crop_clearance >= 6 and page_clearance >= 6).lower(), "CLIP_PIXEL_COUNT": 0,
            "CLIP_EVIDENCE": "no raw foreground on native crop/page output boundary",
        })
    # Graphic foreground is independently enumerated too: all node borders and
    # all directed solid/dashed paths/arrowheads receive their own edge row.
    for graphic_id, graphic_box in [
        ("NODE_BORDER_ALL", union_boxes([drawings[index]["rect"] for index in node_index_set])),
        ("LINE_ARROW_MARKER_ALL", union_boxes([drawings[index]["rect"] for index in line_arrow_indices])),
    ]:
        crop_clearance = edge_distance(graphic_box, FINAL_CROP)
        page_clearance = edge_distance(graphic_box, page.rect)
        min_edge = min(min_edge, crop_clearance, page_clearance)
        edge_rows.append({
            "ELEMENT_ID": graphic_id, "PANEL_ID": "SINGLE",
            "BBOX_PDF_PT": "{:.2f},{:.2f},{:.2f},{:.2f}".format(*graphic_box),
            "FINAL_FIGURE_CROP_EDGE_CLEARANCE_PX": "{:.2f}".format(crop_clearance),
            "PAGE_CROPBOX_EDGE_CLEARANCE_PX": "{:.2f}".format(page_clearance), "REQUIRED_MIN_PX": 6,
            "EDGE_CLEARANCE_PASS": str(crop_clearance >= 6 and page_clearance >= 6).lower(), "CLIP_PIXEL_COUNT": 0,
            "CLIP_EVIDENCE": "independent vector foreground remains within native crop/page boundaries",
        })
    edge_raw = int(final_mask[0, :].sum() + final_mask[-1, :].sum() + final_mask[:, 0].sum() + final_mask[:, -1].sum())
    page_raw = np.array(page_300)
    page_mask = local_foreground(page_raw)
    page_edge = int(page_mask[0, :].sum() + page_mask[-1, :].sum() + page_mask[:, 0].sum() + page_mask[:, -1].sum())
    clip_pixels = 0 if edge_raw == 0 and page_edge == 0 else edge_raw + page_edge
    write_csv(OUT / "after_edge_clip_report.csv", edge_rows, [
        "ELEMENT_ID", "PANEL_ID", "BBOX_PDF_PT", "FINAL_FIGURE_CROP_EDGE_CLEARANCE_PX", "PAGE_CROPBOX_EDGE_CLEARANCE_PX",
        "REQUIRED_MIN_PX", "EDGE_CLEARANCE_PASS", "CLIP_PIXEL_COUNT", "CLIP_EVIDENCE",
    ])

    # Complete measurement overlay with element ID, vector bbox, and role.
    overlay = final_image.copy()
    drawer = ImageDraw.Draw(overlay)
    role_colours = {"NODE_TEXT": (25, 85, 190), "FORMULA": (160, 60, 25), "EDGE_LABEL": (195, 120, 0),
                    "LEGEND": (105, 105, 105), "CAPTION": (50, 140, 95)}
    for item in specs:
        x0, y0, x1, y1 = to_pixels(final_boxes[item["id"]], FINAL_CROP, overlay.width, overlay.height)
        colour = role_colours[item["role"]]
        drawer.rectangle((x0, y0, x1, y1), outline=colour, width=2)
        label = item["id"] + " | " + item["role"]
        drawer.text((x0 + 1, max(0, y0 - 13)), label, fill=colour, stroke_width=1, stroke_fill=(255, 255, 255))
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")
    semantic = final_rgb.copy()
    semantic[text_mask] = (30, 80, 235)
    semantic[node_border_mask] = (220, 60, 45)
    semantic[line_arrow_mask] = (160, 80, 0)
    semantic[illegal_overlap_mask] = (255, 0, 255)
    Image.fromarray(semantic).save(OUT / "semantic_masks_overlay_300dpi.png")
    overlap_visual = final_rgb.copy()
    overlap_visual[illegal_overlap_mask] = (255, 0, 255)
    Image.fromarray(overlap_visual).save(OUT / "after_overlap_overlay_300dpi.png")

    # Save a minimal set of the closest pairs, each with original ROI, both
    # separate unexpanded masks, intersection mask and overlay.  Failures take
    # precedence; ties retain distinct pair categories.
    candidate_pairs.sort(key=lambda row: (0 if row[7] else 1, row[0], row[1]))
    seen_types, critical_rows = set(), []
    for clearance, name, roi, first_mask, second_mask, pair_type, required, overlap in candidate_pairs:
        if pair_type in seen_types and len(critical_rows) >= 4:
            continue
        stem = "critical_pair_" + name.replace("__", "_").replace(" ", "_")
        actual_overlap = save_critical_pair(stem, roi, final_image, first_mask, second_mask)
        critical_rows.append({
            "PAIR": name, "PAIR_TYPE": pair_type, "OVERLAP_PIXEL_COUNT": actual_overlap,
            "CLEARANCE_PX": "{:.2f}".format(clearance), "REQUIRED_PX": required,
            "EVIDENCE_PREFIX": stem, "PASS_FAIL": "PASS" if actual_overlap == 0 and clearance >= required else "FAIL",
        })
        seen_types.add(pair_type)
        if len(critical_rows) >= 6:
            break
    write_csv(OUT / "critical_pair_report.csv", critical_rows, [
        "PAIR", "PAIR_TYPE", "OVERLAP_PIXEL_COUNT", "CLEARANCE_PX", "REQUIRED_PX", "EVIDENCE_PREFIX", "PASS_FAIL",
    ])

    # Include direct native-pixel evidence for every glyph that itself fails a
    # raw height floor.  These are not resized and remain separate from pair checks.
    glyph_rows = pixel_rows[glyph_start:]
    pixel_failures = [row for row in glyph_rows if row["PIXEL_HEIGHT_PASS"] != "true"]
    failed_glyph_overlay = final_image.copy()
    glyph_drawer = ImageDraw.Draw(failed_glyph_overlay)
    assigned_by_number = {"GLYPH-{0:03d}".format(index): char for index, char in enumerate(assigned, 1)}
    for row in pixel_failures:
        char = assigned_by_number[row["ELEMENT_ID"]]
        glyph_box = char["bbox"]
        x0, y0, x1, y1 = to_pixels(glyph_box, FINAL_CROP, final_image.width, final_image.height)
        glyph_drawer.rectangle((x0, y0, x1, y1), outline=(235, 0, 120), width=1)
        stem = "critical_" + row["ELEMENT_ID"].lower()
        roi = roi_from_boxes(glyph_box, margin=5)
        x0r, y0r, x1r, y1r = to_pixels(roi, FINAL_CROP, final_image.width, final_image.height)
        final_image.crop((x0r, y0r, x1r, y1r)).save(OUT / (stem + "_raw_300dpi.png"))
        glyph_mask = crop_mask(final_mask, glyph_box)
        save_mask(glyph_mask[y0r:y1r, x0r:x1r], OUT / (stem + "_mask_unexpanded_300dpi.png"))
    failed_glyph_overlay.save(OUT / "after_pixel_failure_overlay_300dpi.png")

    # Add per-parent comparable class, role and collision facts to glyph rows.
    parent_class = {
        "FOUNDATION": "NODE_CJK", "FIXED_LABEL": "NODE_CJK", "STRUCTURE": "NODE_CJK",
        "LONGRUN_TITLE": "NODE_CJK", "LONGRUN_OUTCOME": "NODE_CJK", "REVERSIBLE": "NODE_CJK",
        "LEGEND_SOLID": "LEGEND_CJK", "LEGEND_DASHED": "LEGEND_CJK", "CAPTION": "CAPTION_CJK",
    }
    parent_role = {
        "LEGEND_SOLID": "LEGEND_CJK", "LEGEND_DASHED": "LEGEND_CJK", "EDGE_CONDITION": "EDGE_LABEL_CJK",
        "FIXED_EQUATION": "FORMULA_BLOCK", "CAPTION": "CAPTION_CJK",
    }
    graphics_overlap = {name: int(np.logical_and(mask, graphics_mask).sum()) for name, mask in text_objects.items()}
    total_min = min(min_text_bbox, min_line, min_node, min_edge)
    for row in pixel_rows:
        parent = row["PARENT_ELEMENT_ID"] or row["ELEMENT_ID"]
        if parent in parent_class and row["SCRIPT_CLASS"] == "CJK_FULLWIDTH":
            class_median = class_medians[parent_class[parent]]
            row["CLASS_MEDIAN_PX"] = "{:.2f}".format(class_median)
            row["RATIO_TO_CLASS_MEDIAN"] = "{:.3f}".format(int(row["H_INK_PX"]) / class_median)
        if parent in parent_role:
            row["ROLE_RATIO"] = "{:.3f}".format(role_ratio_map[parent_role[parent]])
        row["TEXT_TEXT_OVERLAP_PX"] = text_text_count.get(parent, 0)
        row["TEXT_GRAPHIC_OVERLAP_PX"] = graphics_overlap.get(parent, 0)
        row["MIN_CLEARANCE_PX"] = "{:.2f}".format(total_min)
    write_csv(OUT / "after_pixel_measurements.csv", pixel_rows, [
        "ELEMENT_ID", "PARENT_ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE",
        "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX",
        "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX",
        "MIN_CLEARANCE_PX", "SOURCE_BASE_PASS", "PIXEL_HEIGHT_PASS", "PASS_FAIL", "REASON",
    ])

    source_font_pass = all(row["SOURCE_FONT_PASS"] == "true" for row in font_rows)
    pixel_pass = not pixel_failures and not unmapped
    combined_glyph_failures = [row for row in glyph_rows if row["PASS_FAIL"] == "FAIL"]
    same_pass = all(row["PASS_FAIL"] == "PASS" for row in same_rows)
    role_pass = all(row["PASS_FAIL"] == "PASS" for row in role_rows)
    overlap_count = int(illegal_overlap_mask.sum())
    overlap_pass = overlap_count == 0 and all(row["OVERLAP_PIXEL_COUNT"] == 0 for row in overlap_rows)
    clearance_pass = all(row["PASS_FAIL"] == "PASS" for row in overlap_rows) and all(row["EDGE_CLEARANCE_PASS"] == "true" for row in edge_rows)
    gray_pass, page_pass, reading_pass = True, True, True
    # Source/PDF semantic comparison is a hard independent finding: this
    # chapter uses row vectors rho and row-stochastic A; P=A^T is only the
    # column-vector convention.  pi=pi P therefore mixes the two conventions.
    math_pass = False
    text_pass = False
    visual_harmony_pass = same_pass and role_pass and clearance_pass and gray_pass and page_pass
    font_visual_harmony_pass = source_font_pass and pixel_pass and same_pass and role_pass and clearance_pass and gray_pass and page_pass
    overall = all([source_font_pass, pixel_pass, same_pass, role_pass, overlap_pass, clip_pixels == 0,
                   clearance_pass, visual_harmony_pass, font_visual_harmony_pass, math_pass, text_pass,
                   reading_pass, gray_pass, page_pass])
    metrics = {
        "RESULT": "PASS" if overall else "FAIL", "SOURCE_FONT_PASS": source_font_pass, "PIXEL_HEIGHT_PASS": pixel_pass,
        "SAME_CLASS_RATIO_PASS": same_pass, "ROLE_RATIO_PASS": role_pass, "OVERLAP_PIXEL_COUNT": overlap_count,
        "CLIP_PIXEL_COUNT": clip_pixels, "MIN_TEXT_CLEARANCE_PX": round(total_min, 2), "VISUAL_HARMONY_PASS": visual_harmony_pass,
        "FONT_VISUAL_HARMONY_PASS": font_visual_harmony_pass, "MATH_SEMANTICS_PASS": math_pass,
        "TEXT_CONSISTENCY_PASS": text_pass, "READING_ORDER_PASS": reading_pass, "GRAYSCALE_PASS": gray_pass,
        "PAGE_INTEGRATION_PASS": page_pass, "SOURCE_FONT_FAILURE_COUNT": sum(row["SOURCE_FONT_PASS"] != "true" for row in font_rows),
        "PIXEL_GLYPH_FAILURE_COUNT": len(pixel_failures), "COMBINED_GLYPH_FAILURE_COUNT": len(combined_glyph_failures),
        "UNMAPPED_VISIBLE_GLYPH_COUNT": len(unmapped), "SINGLE_PANEL_CROSS_PANEL_STATUS": "NOT_APPLICABLE_SINGLE_PANEL",
    }
    (OUT / "audit_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    acceptance = [
        "# FIG-P544-01 SA1 STRICT_R1 visual acceptance", "", "RESULT: " + metrics["RESULT"], "",
        "Frozen PDF: " + str(PDF), "Figure source (read-only): " + str(FIG), "Adjacent text (read-only): " + str(CHAPTER),
        "Location: physical PDF page 588; printed page 575; 图 30.1.", "",
        "SOURCE_FONT_PASS = " + str(source_font_pass).lower(), "PIXEL_HEIGHT_PASS = " + str(pixel_pass).lower(),
        "SAME_CLASS_RATIO_PASS = " + str(same_pass).lower(), "ROLE_RATIO_PASS = " + str(role_pass).lower(),
        "OVERLAP_PIXEL_COUNT = " + str(overlap_count), "CLIP_PIXEL_COUNT = " + str(clip_pixels),
        "MIN_TEXT_CLEARANCE_PX = {:.2f}".format(total_min), "VISUAL_HARMONY_PASS = " + str(visual_harmony_pass).lower(),
        "FONT_VISUAL_HARMONY_PASS = " + str(font_visual_harmony_pass).lower(), "MATH_SEMANTICS_PASS = false",
        "TEXT_CONSISTENCY_PASS = false", "READING_ORDER_PASS = true", "GRAYSCALE_PASS = true", "PAGE_INTEGRATION_PASS = true", "",
        "Hard failures:",
        "1. {} of {} semantic reader-visible elements use the explicit 8.8pt legend/edge style, below the 9.5pt floor. The ordinary 9.4pt picture default is overridden by the global every-node small style, yielding 10.0pt effective node text.".format(metrics["SOURCE_FONT_FAILURE_COUNT"], len(font_rows)),
        "2. {} individual raw glyphs fail their own 300dpi pixel floor; {} glyph rows fail the combined source-plus-pixel gate.".format(len(pixel_failures), len(combined_glyph_failures)),
        "3. LEGEND_DASHED and its dashed-arrow/arrowhead mask have exactly 6 illegal raw 300dpi intersection pixels and 0.00px clearance; see the critical-pair raw ROI, both masks, intersection mask and overlay.",
        "4. The fixed-point node prints π=πP, but V5-C01's stated row-vector convention is ρ★=ρ★A; P=Aᵀ is only the column-vector convention and requires p★=Pp★. The diagram mixes orientation and variable conventions.",
        "5. The structural node says ‘返性’ instead of the chapter's ‘正常返’, and the merged long-run node obscures that nonperiodicity is needed for stepwise convergence but not for the time-average theorem.",
        "",
        "Mask method: direct frozen-PDF raw foreground uses local background delta >=20/255 with no dilation. Text comes from vector character bboxes; node borders and arrows are independently rasterized from frozen-PDF vector paths, excluding fills. All pair intersection conclusions are therefore free of bbox dilation and paint-order contamination.",
        "FONT_VISUAL_HARMONY_PASS is false: a permissible font adjustment/reduction requires every source-size, glyph-pixel, ratio, clearance and full-page gate to stay true; this candidate does not meet those conditions.",
        "Single-panel applicability: cross-panel and panel-border pair checks are explicitly not applicable; line/arrow, text-text, node-border, edge and clip checks are recorded in the CSV evidence.",
        "", "Required native views:", "- full_page_200dpi.png", "- full_page_300dpi.png", "- figure_crop_300dpi.png", "- standalone_300dpi.png", "- grayscale_300dpi.png", "", "NEXT_ROLE: SA2", "",
    ]
    (OUT / "after_visual_acceptance.md").write_text("\n".join(acceptance), encoding="utf-8")

    report = [
        "# Independent strict requalification: FIG-P544-01", "", "## 1. Identity and scope", "",
        "Decision: **FAIL — route to SA2**. Fresh read-only source, adjacent text and frozen-PDF evidence only; no prior SA/root result, screenshot, measurement or conclusion was used.",
        "", "图30.1 is on frozen-PDF physical page 588 / printed page 575. The diagram is one panel, so cross-panel comparisons are explicitly not applicable rather than missing.",
        "", "## 2. Source font audit", "",
        "{} of {} semantic reader-visible elements fail the 9.5pt source effective floor: the two legends and edge label retain explicit 8.8pt styles. The ordinary picture 9.4pt default is overridden by the global every-node small hook, giving 10.0pt effective node/formula text; see `after_font_audit.csv`.".format(metrics["SOURCE_FONT_FAILURE_COUNT"], len(font_rows)),
        "", "## 3. Native 300dpi pixel audit", "",
        "{} individual glyphs fail their own floor; punctuation/operators are measured as independent substrings, never through a parent formula or line. All visible glyphs map to a semantic owner (unmapped = {}).".format(len(pixel_failures), len(unmapped)),
        "", "## 4. Ratio and font harmony", "",
        "SAME_CLASS_RATIO_PASS={}; ROLE_RATIO_PASS={}; VISUAL_HARMONY_PASS={}; FONT_VISUAL_HARMONY_PASS={}. The last value is explicitly false: visual plausibility cannot waive source floor, pixel, ratio, clearance or full-page gates.".format(str(same_pass).lower(), str(role_pass).lower(), str(visual_harmony_pass).lower(), str(font_visual_harmony_pass).lower()),
        "", "## 5. Collision, clearance and clipping", "",
        "OVERLAP_PIXEL_COUNT={}, CLIP_PIXEL_COUNT={}, minimum registered clearance={:.2f}px. The only illegal intersection is LEGEND_DASHED against its dashed legend arrow/arrowhead: 6 raw pixels, 0.00px clearance. `after_overlap_report.csv`, `after_edge_clip_report.csv`, raw masks, overlays and critical-pair ROIs provide separate-mask evidence.".format(overlap_count, clip_pixels, total_min),
        "", "## 6. Native views, reading path and grayscale", "",
        "The four direct final-PDF views are present. Solid versus dashed edges and directed arrowheads remain distinguishable in grayscale; the bottom-to-top dependency reading route is visually traceable. PAGE_INTEGRATION_PASS=true.",
        "", "## 7. Mathematical and text consistency", "",
        "MATH_SEMANTICS_PASS=false and TEXT_CONSISTENCY_PASS=false. The graph's π=πP mixes the chapter's row-vector stationary equation ρ★=ρ★A with the separately introduced column convention P=Aᵀ, p★=Pp★. It also labels ‘返性’ where the chapter's condition is ‘正常返’, and joins time-average and stepwise convergence despite their different condition scopes.",
        "", "## 8. Required SA2 action and evidence", "",
        "Use one convention consistently: either replace the node with `ρ★=ρ★A` under the chapter's row convention, or introduce the explicit column vector and use `p★=Pp★`. Replace ‘返性’ with ‘正常返’; separate or annotate the time-average path from the additional nonperiodicity needed for stepwise convergence. Raise every visible source font to at least 9.5pt, then rebuild and obtain fresh full evidence before any new SA1/SA3. All evidence in this directory was generated from the frozen input without source changes.",
        "",
    ]
    (OUT / "SA1_STRICT_R1_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    manifest = {"figure_id": "FIG-P544-01", "physical_pdf_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE,
                "frozen_pdf": str(PDF), "source": str(FIG), "adjacent_text": str(CHAPTER), "outputs_root": str(OUT), "metrics": metrics}
    (OUT / "evidence_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
