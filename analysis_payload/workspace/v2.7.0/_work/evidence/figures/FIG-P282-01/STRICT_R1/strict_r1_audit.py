"""Independent, read-only SA1 raster audit for FIG-P282-01.

Inputs are the specified official R92 full-book PDF and its source.  All
outputs remain beside this script in STRICT_R1.  No source files are changed.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


WORKSPACE = Path.cwd()
OUT = Path(__file__).resolve().parent
PDF = WORKSPACE / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r92_fullbook" / "main_full.pdf"
PAGE_NUMBER = 303  # independently located by searchable caption text in the official candidate
PAGE_INDEX = PAGE_NUMBER - 1
SOURCE_FIG = "src/绘图源码/第03册_优化模型与序列模型/V3-C01/fig_v3_c01_simplex.tex"
SOURCE_CHAPTER = "src/讲义源码/第03册_优化模型与序列模型/chapters/V3-C01.tex"
SOURCE_STYLE = "src/讲义源码/common/statlearnbook.sty"
RAW_PAGE = OUT / "official_page_303_300dpi.png"


def bbox_union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def fmt_bbox(b: tuple[int, int, int, int]) -> str:
    return f"({b[0]},{b[1]})-({b[2]},{b[3]})"


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_rect = page.rect
page_image = Image.open(RAW_PAGE).convert("RGB")
rgb = np.asarray(page_image)
height, width = rgb.shape[:2]
sx = width / page_rect.width
sy = height / page_rect.height


def pdf_to_px(b: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return (
        max(0, int(math.floor(b[0] * sx))),
        max(0, int(math.floor(b[1] * sy))),
        min(width, int(math.ceil(b[2] * sx))),
        min(height, int(math.ceil(b[3] * sy))),
    )


rawdict = page.get_text("rawdict")
lines: list[dict] = []
for block in rawdict["blocks"]:
    if block["type"] != 0:
        continue
    for line in block["lines"]:
        text = "".join(ch["c"] for span in line["spans"] for ch in span["chars"])
        lines.append({"text": text, "spans": line["spans"], "bbox": tuple(line["bbox"])})


def get_line(text: str) -> dict:
    found = [line for line in lines if line["text"] == text]
    if len(found) != 1:
        raise RuntimeError(f"Expected one extracted line {text!r}, found {len(found)}")
    return found[0]


def span_box(line: dict, span_idx: int) -> tuple[float, float, float, float]:
    return tuple(line["spans"][span_idx]["bbox"])


def char_box(line: dict, span_idx: int, char_indices: list[int]) -> tuple[float, float, float, float]:
    chars = line["spans"][span_idx]["chars"]
    return bbox_union([tuple(chars[i]["bbox"]) for i in char_indices])


elements: list[dict] = []


def add_element(
    element_id: str,
    line_text: str,
    pdf_bbox: tuple[float, float, float, float],
    role: str,
    display_id: str,
    font_group: str,
    source_file: str,
    source_line: str,
    declared_pt: float,
    effective_pt: float,
    script_class: str,
    source_font_pass: bool,
    source_note: str,
) -> None:
    elements.append(
        {
            "id": element_id,
            "text": line_text,
            "pdf_bbox": pdf_bbox,
            "bbox": pdf_to_px(pdf_bbox),
            "role": role,
            "display": display_id,
            "font_group": font_group,
            "source_file": source_file,
            "source_line": source_line,
            "declared_pt": declared_pt,
            "graphics_scale": 1.0,
            "effective_pt": effective_pt,
            "script_class": script_class,
            "source_font_pass": source_font_pass,
            "source_note": source_note,
        }
    )


# In-figure labels.  Every bbox is extracted afresh from official page 303.
line = get_line("唯一可行")
add_element("E01_FOCUS_UNIQUE", "唯一可行", span_box(line, 0), "ANNOTATION", "FOCUS_1", "FOCUS_CJK", SOURCE_FIG, "9;147-148", 9.4, 9.4, "CJK", False, "direct focus label is below 9.5pt")
line = get_line("最大熵点")
add_element("E02_FOCUS_MAXENT", "最大熵点", span_box(line, 0), "ANNOTATION", "FOCUS_2", "FOCUS_CJK", SOURCE_FIG, "9;147-148", 9.4, 9.4, "CJK", False, "direct focus label is below 9.5pt")

line = get_line("等高线")
add_element("E03_CONTOUR_HEADER", "等高线", span_box(line, 0), "ANNOTATION", "CONTOUR_HEADER", "CONTOUR_CJK", SOURCE_FIG, "13;149-150", 9.0, 9.0, "CJK", False, "direct contour annotation is below 9.5pt")
for prefix, rendered in (("OUTER", "外层：𝐻= 0.80"), ("MID", "中层：𝐻= 0.95"), ("INNER", "内层：𝐻= 1.05")):
    line = get_line(rendered)
    display = f"CONTOUR_{prefix}"
    add_element(f"E{len(elements)+1:02d}_{prefix}_CJK", rendered.split("𝐻")[0], span_box(line, 0), "ANNOTATION", display, "CONTOUR_CJK", SOURCE_FIG, "13;149-150", 9.0, 9.0, "CJK", False, "direct contour annotation is below 9.5pt")
    add_element(f"E{len(elements)+1:02d}_{prefix}_H", "H", char_box(line, 1, [0]), "FORMULA", display, "CONTOUR_MATH_H", SOURCE_FIG, "13;149-150", 9.0, 9.0, "LATIN_UPPER", False, "formula baseline is below 9.5pt")
    add_element(f"E{len(elements)+1:02d}_{prefix}_EQUAL", "=", char_box(line, 1, [1]), "FORMULA", display, "CONTOUR_MATH_EQUAL", SOURCE_FIG, "13;149-150", 9.0, 9.0, "MATH_OPERATOR", False, "formula baseline is below 9.5pt")
    chars = line["spans"][1]["chars"]
    value_indices = [i for i, ch in enumerate(chars) if ch["c"] not in {"𝐻", "=", " "}]
    add_element(f"E{len(elements)+1:02d}_{prefix}_VALUE", "".join(chars[i]["c"] for i in value_indices), char_box(line, 1, value_indices), "FORMULA", display, "CONTOUR_MATH_VALUE", SOURCE_FIG, "13;149-150", 9.0, 9.0, "DIGIT", False, "formula baseline is below 9.5pt")

for number in ("1", "2"):
    line = get_line(f"约束{number}")
    display = f"CONSTRAINT_{number}"
    add_element(f"E{len(elements)+1:02d}_CONSTRAINT_{number}_CJK", "约束", span_box(line, 0), "ANNOTATION", display, "CONSTRAINT_CJK", SOURCE_FIG, f"17;{151 if number == '1' else 153}-{152 if number == '1' else 154}", 9.2, 9.2, "CJK", False, "direct constraint label is below 9.5pt")
    add_element(f"E{len(elements)+1:02d}_CONSTRAINT_{number}_DIGIT", number, span_box(line, 1), "ANNOTATION", display, "CONSTRAINT_DIGIT", SOURCE_FIG, f"17;{151 if number == '1' else 153}-{152 if number == '1' else 154}", 9.2, 9.2, "DIGIT", False, "direct constraint label is below 9.5pt")

for number in ("1", "2", "3"):
    line = get_line(f"𝑝{number} = 1")
    display = f"VERTEX_{number}"
    add_element(f"E{len(elements)+1:02d}_VERTEX_{number}_P", "p", char_box(line, 0, [0]), "FORMULA", display, "VERTEX_BASE_LOWER", SOURCE_FIG, str(154 + int(number)), 9.6, 9.6, "LATIN_LOWER", True, "baseline formula font is 9.6pt")
    add_element(f"E{len(elements)+1:02d}_VERTEX_{number}_SUBSCRIPT", number, char_box(line, 1, [0]), "FORMULA", display, "VERTEX_SCRIPT", SOURCE_FIG, str(154 + int(number)), 9.6, 6.69, "MATH_SCRIPT", True, "natural script derived from a 9.6pt baseline")
    add_element(f"E{len(elements)+1:02d}_VERTEX_{number}_EQUAL", "=", char_box(line, 3, [0]), "FORMULA", display, "VERTEX_BASE_EQUAL", SOURCE_FIG, str(154 + int(number)), 9.6, 9.6, "MATH_OPERATOR", True, "baseline formula font is 9.6pt")
    add_element(f"E{len(elements)+1:02d}_VERTEX_{number}_DIGIT", "1", char_box(line, 3, [2]), "FORMULA", display, "VERTEX_BASE_DIGIT", SOURCE_FIG, str(154 + int(number)), 9.6, 9.6, "DIGIT", True, "baseline formula font is 9.6pt")

# Caption and immediately following explanatory prose are included as directly associated text.
line = get_line("图17.1")
add_element(f"E{len(elements)+1:02d}_CAPTION_LABEL_CJK", "图", span_box(line, 0), "CAPTION", "CAPTION_LABEL", "CAPTION_LABEL_CJK", SOURCE_FIG, f"160; {SOURCE_STYLE}:305", 10.0, 10.0, "CJK", True, "caption inherits 11pt-book \\small = 10pt")
add_element(f"E{len(elements)+1:02d}_CAPTION_LABEL_NUMBER", "17.1", span_box(line, 1), "CAPTION", "CAPTION_LABEL", "CAPTION_LABEL_DIGIT", SOURCE_FIG, f"160; {SOURCE_STYLE}:305", 10.0, 10.0, "DIGIT", True, "caption inherits 11pt-book \\small = 10pt")
caption_body = "概率单纯形上的熵等高线与线性约束；本例约束交点是唯一可行的最大熵点"
line = get_line(caption_body)
add_element(f"E{len(elements)+1:02d}_CAPTION_TEXT", caption_body, span_box(line, 0), "CAPTION", "CAPTION_BODY", "CAPTION_TEXT_CJK", SOURCE_FIG, f"160; {SOURCE_STYLE}:305", 10.0, 10.0, "CJK", True, "caption inherits 11pt-book \\small = 10pt")
direct_1 = "图17.1 把概率归一化表示为单纯形，把已知统计量表示为线性约束；可行集是两者的交集，"
line = get_line(direct_1)
add_element(f"E{len(elements)+1:02d}_DIRECT_BODY_1_CJK_PREFIX", "图", span_box(line, 0), "DIRECT_TEXT", "DIRECT_BODY_1", "DIRECT_PREFIX_CJK", SOURCE_CHAPTER, "245", 11.0, 11.0, "CJK", True, "chapter body is normal 11pt text")
add_element(f"E{len(elements)+1:02d}_DIRECT_BODY_1_FIGURE_NUMBER", "17.1", span_box(line, 1), "DIRECT_TEXT", "DIRECT_BODY_1", "DIRECT_BODY_DIGIT", SOURCE_CHAPTER, "245", 11.0, 11.0, "DIGIT", True, "chapter body is normal 11pt text")
add_element(f"E{len(elements)+1:02d}_DIRECT_BODY_1_CJK", "把概率归一化表示为单纯形，把已知统计量表示为线性约束；可行集是两者的交集，", span_box(line, 2), "DIRECT_TEXT", "DIRECT_BODY_1", "DIRECT_BODY_1_CJK", SOURCE_CHAPTER, "245", 11.0, 11.0, "CJK", True, "automatic line fragment of one normal-11pt direct-prose object")
direct_2 = "最大熵解是在该交集内而不是在整个单纯形内选择熵最大点。"
line = get_line(direct_2)
add_element(f"E{len(elements)+1:02d}_DIRECT_BODY_2_CJK", direct_2, span_box(line, 0), "DIRECT_TEXT", "DIRECT_BODY_2", "DIRECT_BODY_2_CJK", SOURCE_CHAPTER, "245", 11.0, 11.0, "CJK", True, "automatic line fragment of one normal-11pt direct-prose object")


def local_text_mask(bbox: tuple[int, int, int, int]) -> np.ndarray:
    """Threshold only actual rendered ink, using the local background and Δ>=20."""
    x0, y0, x1, y1 = bbox
    pad = 4
    px0, py0 = max(0, x0 - pad), max(0, y0 - pad)
    px1, py1 = min(width, x1 + pad), min(height, y1 + pad)
    patch = rgb[py0:py1, px0:px1]
    border = np.concatenate((patch[0], patch[-1], patch[:, 0], patch[:, -1]), axis=0)
    background = np.median(border, axis=0)
    delta = np.max(np.abs(patch.astype(np.int16) - background.astype(np.int16)), axis=2)
    foreground = delta >= 20
    mask = np.zeros((height, width), dtype=bool)
    # Restrict to the PDF/vector bbox; no geometric expansion changes the reported bbox.
    ix0, iy0 = x0 - px0, y0 - py0
    ix1, iy1 = x1 - px0, y1 - py0
    mask[y0:y1, x0:x1] = foreground[iy0:iy1, ix0:ix1]
    return mask


def ink_height(mask: np.ndarray) -> int:
    rows = np.where(mask.any(axis=1))[0]
    return int(rows[-1] - rows[0] + 1) if rows.size else 0


thresholds = {
    "CJK": 30,
    "DIGIT": 24,
    "LATIN_UPPER": 24,
    "LATIN_LOWER": 17,
    "MATH_OPERATOR": 22,
    "MATH_SCRIPT": 15,
}
for e in elements:
    e["mask"] = local_text_mask(e["bbox"])
    e["h_ink"] = ink_height(e["mask"])
    e["pixel_threshold"] = thresholds[e["script_class"]]
    e["pixel_pass"] = e["h_ink"] >= e["pixel_threshold"]
    e["pdf_vector_pt"] = None

# Bind the vector font size for traceability.
for e in elements:
    candidates = []
    for line in lines:
        for span in line["spans"]:
            box = pdf_to_px(tuple(span["bbox"]))
            if box == e["bbox"]:
                candidates.append(span["size"])
    if candidates:
        e["pdf_vector_pt"] = round(float(candidates[0]), 2)


# Build an independent graphics mask from official-PDF vector paths, not from a screenshot.
drawings = page.get_drawings()
graphic_objects: list[dict] = []
semantic_names = {
    7: ("G01_SIMPLEX_BORDER", "LINE_ARROW"),
    8: ("G02_ENTROPY_CONTOUR_SET", "DATA_CURVE"),
    9: ("G03_CONSTRAINT_1_EXTENSION", "LINE_ARROW"),
    10: ("G04_CONSTRAINT_2_EXTENSION", "LINE_ARROW"),
    11: ("G05_CONSTRAINT_1_FEASIBLE_SEGMENT", "LINE_ARROW"),
    12: ("G06_CONSTRAINT_2_FEASIBLE_SEGMENT", "LINE_ARROW"),
    13: ("G07_FOCUS_LEADER", "LINE_ARROW"),
    14: ("G08_UNIQUE_MAXENT_MARKER", "MARKER"),
}


def point_px(point: fitz.Point) -> tuple[int, int]:
    return int(round(point.x * sx)), int(round(point.y * sy))


def parse_dashes(value) -> list[float]:
    if not value:
        return []
    nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", str(value))]
    # PyMuPDF's representation ends with the dash phase after the bracketed array.
    return nums[:-1] if len(nums) >= 2 else []


def draw_dashed_segment(canvas: np.ndarray, a: tuple[int, int], b: tuple[int, int], dash_pt: list[float], thickness: int) -> None:
    if not dash_pt:
        cv2.line(canvas, a, b, 255, thickness=thickness, lineType=cv2.LINE_8)
        return
    length = math.dist(a, b)
    if length == 0:
        return
    dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    pattern = [max(1.0, d * sx) for d in dash_pt]
    distance = 0.0
    idx = 0
    draw = True
    while distance < length:
        step = min(pattern[idx % len(pattern)], length - distance)
        if draw:
            s = (int(round(a[0] + dx * distance)), int(round(a[1] + dy * distance)))
            t = (int(round(a[0] + dx * (distance + step))), int(round(a[1] + dy * (distance + step))))
            cv2.line(canvas, s, t, 255, thickness=thickness, lineType=cv2.LINE_8)
        distance += step
        idx += 1
        draw = not draw


def bezier_points(p0, p1, p2, p3, n=96):
    result = []
    for t in np.linspace(0.0, 1.0, n):
        mt = 1.0 - t
        x = mt**3 * p0.x + 3 * mt**2 * t * p1.x + 3 * mt * t**2 * p2.x + t**3 * p3.x
        y = mt**3 * p0.y + 3 * mt**2 * t * p1.y + 3 * mt * t**2 * p2.y + t**3 * p3.y
        result.append((int(round(x * sx)), int(round(y * sy))))
    return np.array(result, dtype=np.int32)


for drawing_index, drawing in enumerate(drawings):
    rect = drawing["rect"]
    if rect.y1 < 400 or rect.y0 > 650:
        continue
    if drawing_index not in semantic_names:
        continue
    object_id, object_kind = semantic_names[drawing_index]
    canvas = np.zeros((height, width), dtype=np.uint8)
    thickness = max(1, int(math.ceil((drawing.get("width") or 0.55) * sy)) + 1)
    dashes = parse_dashes(drawing.get("dashes"))
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            draw_dashed_segment(canvas, point_px(item[1]), point_px(item[2]), dashes, thickness)
        elif kind == "c":
            curve = bezier_points(item[1], item[2], item[3], item[4])
            cv2.polylines(canvas, [curve], False, 255, thickness=thickness, lineType=cv2.LINE_8)

    # One-pixel conservative fringe includes original 300dpi anti-alias coverage.
    canvas = cv2.dilate(canvas, np.ones((3, 3), dtype=np.uint8), iterations=1).astype(bool)
    graphic_objects.append({"id": object_id, "kind": object_kind, "mask": canvas})

line_mask = np.zeros((height, width), dtype=bool)
marker_mask = np.zeros((height, width), dtype=bool)
for graphic in graphic_objects:
    if graphic["kind"] == "MARKER":
        marker_mask |= graphic["mask"]
    else:
        line_mask |= graphic["mask"]
graphics_mask = line_mask | marker_mask


def min_mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return float("inf")
    distances = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 5)
    return float(distances[a].min())


display_members: dict[str, list[dict]] = defaultdict(list)
for e in elements:
    display_members[e["display"]].append(e)

display_masks: dict[str, np.ndarray] = {}
display_boxes: dict[str, tuple[int, int, int, int]] = {}
display_h: dict[str, int] = {}
for display, members in display_members.items():
    combined = np.zeros((height, width), dtype=bool)
    for e in members:
        combined |= e["mask"]
    display_masks[display] = combined
    display_boxes[display] = bbox_union([e["bbox"] for e in members])
    display_h[display] = ink_height(combined)

display_text_overlap = {}
display_text_clearance = {}
displays = list(display_members)
for display in displays:
    overlap = 0
    minimum = float("inf")
    for other in displays:
        if other == display:
            continue
        overlap += int(np.count_nonzero(display_masks[display] & display_masks[other]))
        minimum = min(minimum, bbox_distance(display_boxes[display], display_boxes[other]))
    display_text_overlap[display] = overlap
    display_text_clearance[display] = minimum

for e in elements:
    e["text_text_overlap"] = display_text_overlap[e["display"]]
    e["text_graphic_overlap"] = sum(int(np.count_nonzero(e["mask"] & graphic["mask"])) for graphic in graphic_objects)
    e["line_clearance"] = min_mask_distance(e["mask"], line_mask)
    e["marker_clearance"] = min_mask_distance(e["mask"], marker_mask)
    e["text_clearance"] = display_text_clearance[e["display"]]
    e["min_clearance"] = min(e["line_clearance"], e["marker_clearance"], e["text_clearance"])


# Same-class ratios use only like script / semantic roles.
class_groups: dict[str, list[dict]] = defaultdict(list)
for e in elements:
    class_groups[e["font_group"]].append(e)
for members in class_groups.values():
    med = float(np.median([e["h_ink"] for e in members]))
    for e in members:
        e["class_median"] = med
        e["class_ratio"] = e["h_ink"] / med if med else 0.0
    heights = [e["h_ink"] for e in members]
    group_pass = all(0.92 <= e["class_ratio"] <= 1.08 for e in members) and max(heights) / min(heights) <= 1.08
    for e in members:
        e["same_class_pass"] = group_pass

# Source effective-point consistency is audited separately for like roles.
font_groups: dict[str, list[dict]] = defaultdict(list)
for e in elements:
    font_groups[e["font_group"]].append(e)
for members in font_groups.values():
    pts = [e["effective_pt"] for e in members]
    ratio = max(pts) / min(pts)
    delta = max(pts) - min(pts)
    pass_value = ratio <= 1.03 and delta <= 0.25
    for e in members:
        e["source_ratio"] = ratio
        e["source_delta"] = delta
        e["source_consistency_pass"] = pass_value

# Role hierarchy: the two constraint labels are the ordinary in-figure base (no ticks exist).
role_display_sets = {
    "ANNOTATION_FOCUS": ["FOCUS_1", "FOCUS_2"],
    "ANNOTATION_CONTOUR": ["CONTOUR_HEADER", "CONTOUR_OUTER", "CONTOUR_MID", "CONTOUR_INNER"],
    "ANNOTATION_CONSTRAINT": ["CONSTRAINT_1", "CONSTRAINT_2"],
    "FORMULA_VERTEX": ["VERTEX_1", "VERTEX_2", "VERTEX_3"],
}
role_medians = {name: float(np.median([display_h[d] for d in ids])) for name, ids in role_display_sets.items()}
base_h = role_medians["ANNOTATION_CONSTRAINT"]
role_ranges = {
    "ANNOTATION_FOCUS": (0.95, 1.10),
    "ANNOTATION_CONTOUR": (0.95, 1.10),
    "ANNOTATION_CONSTRAINT": (0.95, 1.10),
    "FORMULA_VERTEX": (1.00, 1.18),
}
role_results = {}
for name, value in role_medians.items():
    ratio = value / base_h
    low, high = role_ranges[name]
    role_results[name] = {"median_h": value, "ratio_to_base": ratio, "range": [low, high], "pass": low <= ratio <= high}

display_to_role = {d: name for name, ids in role_display_sets.items() for d in ids}
for e in elements:
    category = display_to_role.get(e["display"])
    if category:
        e["role_ratio"] = role_results[category]["ratio_to_base"]
        e["role_pass"] = role_results[category]["pass"]
    else:
        e["role_ratio"] = "N/A"
        e["role_pass"] = True


def output_crop(pdf_box: tuple[float, float, float, float], name: str) -> tuple[int, int, int, int]:
    box = pdf_to_px(pdf_box)
    page_image.crop(box).save(OUT / name)
    return box


figure_crop_box = output_crop((90, 400, 500, 660), "figure_crop_300dpi.png")
crop_image = page_image.crop(figure_crop_box)
ImageOps.grayscale(crop_image).save(OUT / "grayscale_300dpi.png")
output_crop((370, 442, 465, 515), "roi_contour_labels_1to1_300dpi.png")
output_crop((370, 540, 440, 593), "roi_focus_leader_1to1_300dpi.png")
output_crop((248, 404, 298, 442), "roi_top_vertex_1to1_300dpi.png")
output_crop((125, 607, 420, 635), "roi_lower_vertices_1to1_300dpi.png")
output_crop((180, 458, 225, 492), "roi_constraint_1_1to1_300dpi.png")
output_crop((55, 668, 540, 708), "roi_caption_direct_text_1to1_300dpi.png")
analysis_crop_box = pdf_to_px((55, 400, 540, 710))

# Overlay traceability: show every PDF-mapped bbox and ELEMENT_ID on the native-pixel crop.
overlay = page_image.copy()
draw = ImageDraw.Draw(overlay)
font = ImageFont.load_default()
role_colors = {
    "ANNOTATION": (220, 30, 30),
    "FORMULA": (20, 100, 220),
    "CAPTION": (150, 30, 180),
    "DIRECT_TEXT": (0, 130, 75),
}
for e in elements:
    color = role_colors[e["role"]]
    draw.rectangle(e["bbox"], outline=color, width=1)
    draw.text((e["bbox"][0], max(0, e["bbox"][1] - 10)), e["id"], fill=color, font=font, stroke_width=1, stroke_fill=(255, 255, 255))
overlay.crop(analysis_crop_box).save(OUT / "after_text_measurement_overlay_300dpi.png")

# Semantic masks are native-pixel crops: text=red, lines=cyan, marker=yellow, overlap=magenta.
all_text_mask = np.zeros((height, width), dtype=bool)
for e in elements:
    all_text_mask |= e["mask"]
semantic = np.full((height, width, 3), 255, dtype=np.uint8)
semantic[line_mask] = (0, 190, 230)
semantic[marker_mask] = (240, 175, 0)
semantic[all_text_mask] = (220, 30, 30)
semantic[all_text_mask & graphics_mask] = (255, 0, 255)
Image.fromarray(semantic).crop(analysis_crop_box).save(OUT / "semantic_masks_300dpi.png")
Image.fromarray((all_text_mask.astype(np.uint8) * 255)).crop(analysis_crop_box).save(OUT / "mask_text_300dpi.png")
Image.fromarray((graphics_mask.astype(np.uint8) * 255)).crop(analysis_crop_box).save(OUT / "mask_graphics_300dpi.png")
Image.fromarray(((all_text_mask & graphics_mask).astype(np.uint8) * 255)).crop(analysis_crop_box).save(OUT / "mask_overlap_300dpi.png")


font_header = [
    "ELEMENT_ID", "SOURCE_FILE", "SOURCE_LINE", "TEXT_SAMPLE", "ROLE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT",
    "PDF_VECTOR_PT", "SOURCE_SAME_ROLE_MAX_MIN", "SOURCE_SAME_ROLE_ABS_DIFF_PT", "SOURCE_CONSISTENCY_PASS", "SOURCE_FONT_PASS", "PASS_FAIL", "REASON",
]
with (OUT / "after_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=font_header)
    writer.writeheader()
    for e in elements:
        passed = e["source_font_pass"] and e["source_consistency_pass"]
        writer.writerow({
            "ELEMENT_ID": e["id"], "SOURCE_FILE": e["source_file"], "SOURCE_LINE": e["source_line"], "TEXT_SAMPLE": e["text"], "ROLE": e["role"],
            "DECLARED_PT": f"{e['declared_pt']:.2f}", "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{e['effective_pt']:.2f}",
            "PDF_VECTOR_PT": "" if e["pdf_vector_pt"] is None else f"{e['pdf_vector_pt']:.2f}",
            "SOURCE_SAME_ROLE_MAX_MIN": f"{e['source_ratio']:.4f}", "SOURCE_SAME_ROLE_ABS_DIFF_PT": f"{e['source_delta']:.2f}",
            "SOURCE_CONSISTENCY_PASS": str(e["source_consistency_pass"]).lower(), "SOURCE_FONT_PASS": str(e["source_font_pass"]).lower(),
            "PASS_FAIL": "PASS" if passed else "FAIL", "REASON": "" if passed else e["source_note"],
        })


pixel_header = [
    "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS",
    "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "PIXEL_THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO",
    "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON",
]
with (OUT / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=pixel_header)
    writer.writeheader()
    for e in elements:
        metric_pass = e["pixel_pass"] and e["same_class_pass"] and e["role_pass"] and e["text_text_overlap"] == 0 and e["text_graphic_overlap"] == 0
        reasons = []
        if not e["pixel_pass"]:
            reasons.append(f"H_ink={e['h_ink']}px < {e['pixel_threshold']}px {e['script_class']} threshold")
        if not e["same_class_pass"]:
            reasons.append("same-class pixel ratio outside [0.92,1.08] or max/min >1.08")
        if not e["role_pass"]:
            reasons.append("role ratio outside required band")
        if e["text_text_overlap"]:
            reasons.append(f"text-text overlap {e['text_text_overlap']}px")
        if e["text_graphic_overlap"]:
            reasons.append(f"text-graphic overlap {e['text_graphic_overlap']}px")
        writer.writerow({
            "ELEMENT_ID": e["id"], "PANEL_ID": "P1", "ROLE": e["role"], "SOURCE_FILE": e["source_file"], "SOURCE_LINE": e["source_line"],
            "DECLARED_PT": f"{e['declared_pt']:.2f}", "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{e['effective_pt']:.2f}", "TEXT_SAMPLE": e["text"], "SCRIPT_CLASS": e["script_class"],
            "BBOX_X0": e["bbox"][0], "BBOX_Y0": e["bbox"][1], "BBOX_X1": e["bbox"][2], "BBOX_Y1": e["bbox"][3],
            "H_INK_PX": e["h_ink"], "PIXEL_THRESHOLD_PX": e["pixel_threshold"], "CLASS_MEDIAN_PX": f"{e['class_median']:.2f}", "RATIO_TO_CLASS_MEDIAN": f"{e['class_ratio']:.4f}",
            "ROLE_RATIO": e["role_ratio"] if isinstance(e["role_ratio"], str) else f"{e['role_ratio']:.4f}",
            "TEXT_TEXT_OVERLAP_PX": e["text_text_overlap"], "TEXT_GRAPHIC_OVERLAP_PX": e["text_graphic_overlap"],
            "MIN_CLEARANCE_PX": "N/A" if math.isinf(e["min_clearance"]) else f"{e['min_clearance']:.2f}",
            "PASS_FAIL": "PASS" if metric_pass else "FAIL", "REASON": "; ".join(reasons),
        })


overlap_header = ["CHECK_ID", "OBJECT_A", "OBJECT_B", "CATEGORY", "OVERLAP_PIXEL_COUNT", "MIN_CLEARANCE_PX", "THRESHOLD", "PASS_FAIL", "METHOD"]
overlap_rows = []
for display in displays:
    for graphic in graphic_objects:
        overlap_rows.append({
            "CHECK_ID": f"TG_{display}_{graphic['id']}", "OBJECT_A": display, "OBJECT_B": graphic["id"], "CATEGORY": f"TEXT_{graphic['kind']}",
            "OVERLAP_PIXEL_COUNT": int(np.count_nonzero(display_masks[display] & graphic["mask"])), "MIN_CLEARANCE_PX": f"{min_mask_distance(display_masks[display], graphic['mask']):.2f}", "THRESHOLD": "overlap=0; clearance>=3px", "PASS_FAIL": "",
            "METHOD": "native 300dpi PDF-vector semantic-object mask ∩ local-background Δ>=20 text-ink mask",
        })
for i, a in enumerate(displays):
    for b in displays[i + 1:]:
        overlap_rows.append({
            "CHECK_ID": f"TT_{a}_{b}", "OBJECT_A": a, "OBJECT_B": b, "CATEGORY": "TEXT_TEXT",
            "OVERLAP_PIXEL_COUNT": int(np.count_nonzero(display_masks[a] & display_masks[b])), "MIN_CLEARANCE_PX": f"{bbox_distance(display_boxes[a], display_boxes[b]):.2f}", "THRESHOLD": "overlap=0; bbox clearance>=4px", "PASS_FAIL": "",
            "METHOD": "300dpi Δ>=20 text-ink mask intersection; PDF-mapped bbox distance",
        })
for row in overlap_rows:
    overlap = int(row["OVERLAP_PIXEL_COUNT"])
    clearance = float(row["MIN_CLEARANCE_PX"])
    threshold = 4.0 if row["CATEGORY"] == "TEXT_TEXT" else 3.0
    row["PASS_FAIL"] = "PASS" if overlap == 0 and clearance >= threshold else "FAIL"
for category, note in (("TEXT_NODE_BORDER", "N/A: no node border exists in this simplex figure"), ("TEXT_PANEL_BORDER", "N/A: single unframed panel; page edge checked separately"), ("LEGEND_DATA_CURVE", "N/A: no legend exists"), ("ARROWHEAD_TEXT", "N/A: no arrowhead exists")):
    overlap_rows.append({"CHECK_ID": category, "OBJECT_A": "N/A", "OBJECT_B": "N/A", "CATEGORY": category, "OVERLAP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": "N/A", "THRESHOLD": note, "PASS_FAIL": "PASS", "METHOD": "semantic-object inventory"})

with (OUT / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=overlap_header)
    writer.writeheader()
    writer.writerows(overlap_rows)


overall_text_graphic_overlap = int(np.count_nonzero(all_text_mask & graphics_mask))
overall_text_text_overlap = sum(int(np.count_nonzero(display_masks[a] & display_masks[b])) for i, a in enumerate(displays) for b in displays[i + 1:])
minimum_text_text = min((bbox_distance(display_boxes[a], display_boxes[b]) for i, a in enumerate(displays) for b in displays[i + 1:]), default=float("inf"))
minimum_text_graphic = min((min_mask_distance(display_masks[d], graphics_mask) for d in displays), default=float("inf"))
minimum_page_edge = min(min(e["bbox"][0], e["bbox"][1], width - e["bbox"][2], height - e["bbox"][3]) for e in elements)
clip_count = 0
for e in elements:
    x0, y0, x1, y1 = e["bbox"]
    if x0 <= 0 or y0 <= 0 or x1 >= width or y1 >= height:
        clip_count += 1
for d in drawings:
    r = d["rect"]
    if 400 <= r.y0 <= 650 and (r.x0 <= 0 or r.y0 <= 0 or r.x1 >= page_rect.width or r.y1 >= page_rect.height):
        clip_count += 1

summary = {
    "figure_id": "FIG-P282-01",
    "official_pdf": str(PDF),
    "official_pdf_page": PAGE_NUMBER,
    "page_png": {"file": RAW_PAGE.name, "dpi": 300, "pixels": [width, height], "resampled": False},
    "source_font_pass": all(e["source_font_pass"] and e["source_consistency_pass"] for e in elements),
    "pixel_height_pass": all(e["pixel_pass"] for e in elements),
    "same_class_ratio_pass": all(e["same_class_pass"] for e in elements),
    "role_ratio_pass": all(result["pass"] for result in role_results.values()),
    "role_results": role_results,
    "overlap_pixel_count": overall_text_graphic_overlap + overall_text_text_overlap,
    "text_graphic_overlap_pixel_count": overall_text_graphic_overlap,
    "text_text_overlap_pixel_count": overall_text_text_overlap,
    "clip_pixel_count": clip_count,
    "min_text_text_bbox_clearance_px": minimum_text_text,
    "min_text_graphic_ink_clearance_px": minimum_text_graphic,
    "min_text_page_edge_px": minimum_page_edge,
    "semantic_graphic_objects": [graphic["id"] for graphic in graphic_objects],
    "failed_source_elements": [e["id"] for e in elements if not e["source_font_pass"]],
    "failed_pixel_elements": [e["id"] for e in elements if not e["pixel_pass"]],
    "pixel_rows_failed": [e["id"] for e in elements if not (e["pixel_pass"] and e["same_class_pass"] and e["role_pass"])],
}
with (OUT / "strict_r1_audit_summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2))
