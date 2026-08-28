"""Independent, read-only strict R1 evidence generator for FIG-P142-01.

All measurements use official_page_152_300dpi.png directly.  This script does
not read any prior figure review, state, or conclusion, and writes only beside
itself in STRICT_R1.
"""

from __future__ import annotations

import csv
import json
import math
from itertools import combinations
from pathlib import Path
from statistics import median

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps


OUT = Path(__file__).resolve().parent
PDF = OUT / "official_page_152.pdf"
PNG = OUT / "official_page_152_300dpi.png"
SOURCE_REL = (
    "src/绘图源码/第01册_数学基础与统计学习基本理论/"
    "V1-C09/fig_v1_c09_learning_loop.tex"
)
STYLE_REL = "src/讲义源码/common/statlearnbook.sty"


def rgb(hex_value: str) -> tuple[int, int, int]:
    return tuple(int(hex_value[i : i + 2], 16) for i in (1, 3, 5))


INK = rgb("#1F2227")
FEEDBACK_INK = rgb("#1F2837")
BLUE = rgb("#1F4E79")
TEAL = rgb("#0E766E")


# PyMuPDF page coordinates, copied from the official page's embedded vector
# text objects.  Every text unit that carries figure/caption semantics is an
# independent ELEMENT_ID; mixed scripts are deliberately split.
TEXT_ELEMENTS = [
    {
        "id": "T01_FEEDBACK_SUPERVISED",
        "panel": "TRAIN",
        "role": "FEEDBACK_LABEL",
        "source_line": f"{SOURCE_REL}:59",
        "declared": 8.6,
        "sample": "监督：验证误差与标签反馈",
        "script": "CJK",
        "bbox": (128.31, 201.88, 231.13, 211.05),
        "color": FEEDBACK_INK,
        "parent": "G14_FEEDBACK_SUPERVISED",
    },
    {
        "id": "T02_FEEDBACK_UNSUPERVISED",
        "panel": "TRAIN",
        "role": "FEEDBACK_LABEL",
        "source_line": f"{SOURCE_REL}:62",
        "declared": 8.6,
        "sample": "无监督：结构稳定性反馈",
        "script": "CJK",
        "bbox": (236.85, 187.70, 331.10, 196.88),
        "color": FEEDBACK_INK,
        "parent": "G15_FEEDBACK_UNSUPERVISED",
    },
    {
        "id": "T03_PANEL_TRAIN",
        "panel": "TRAIN",
        "role": "PANEL_LABEL",
        "source_line": f"{SOURCE_REL}:38-39",
        "declared": 9.2,
        "sample": "训练阶段",
        "script": "CJK",
        "bbox": (207.33, 219.83, 243.99, 233.11),
        "color": BLUE,
        "parent": "G01_PANEL_TRAIN_BORDER",
    },
    {
        "id": "T04_PANEL_USE",
        "panel": "USE",
        "role": "PANEL_LABEL",
        "source_line": f"{SOURCE_REL}:42-43",
        "declared": 9.2,
        "sample": "使用阶段",
        "script": "CJK",
        "bbox": (207.11, 341.25, 243.77, 354.52),
        "color": TEAL,
        "parent": "G02_PANEL_USE_BORDER",
    },
    {
        "id": "T05_DATA_LINE1",
        "panel": "TRAIN",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:27",
        "declared": 9.2,
        "sample": "训练数据",
        "script": "CJK",
        "bbox": (125.99, 238.13, 171.65, 247.95),
        "color": INK,
        "parent": "G03_NODE_DATA_BORDER",
    },
    {
        "id": "T06_DATA_LINE2",
        "panel": "TRAIN",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:27",
        "declared": 9.2,
        "sample": "与任务反馈",
        "script": "CJK",
        "bbox": (121.41, 252.57, 176.22, 262.39),
        "color": INK,
        "parent": "G03_NODE_DATA_BORDER",
    },
    {
        "id": "T07_LEARN_CJK",
        "panel": "TRAIN",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:28",
        "declared": 9.2,
        "sample": "学习算法",
        "script": "CJK",
        "bbox": (223.52, 238.13, 266.95, 247.95),
        "color": INK,
        "parent": "G04_NODE_LEARN_BORDER",
    },
    {
        "id": "T08_LEARN_MATH_A",
        "panel": "TRAIN",
        "role": "INLINE_MATH",
        "source_line": f"{SOURCE_REL}:28",
        "declared": 9.2,
        "sample": "\\mathcal A",
        "script": "MATH_CAPITAL",
        "class_key": "CALLIGRAPHIC_MATH_CAPITAL",
        "bbox": (270.01, 238.48, 278.03, 247.65),
        "color": INK,
        "parent": "G04_NODE_LEARN_BORDER",
    },
    {
        "id": "T09_LEARN_MATH_F",
        "panel": "TRAIN",
        "role": "INLINE_MATH",
        "source_line": f"{SOURCE_REL}:28",
        "declared": 9.2,
        "sample": "\\mathcal F",
        "script": "MATH_CAPITAL",
        "class_key": "CALLIGRAPHIC_MATH_CAPITAL",
        "bbox": (224.76, 252.92, 231.97, 262.09),
        "color": INK,
        "parent": "G04_NODE_LEARN_BORDER",
    },
    {
        "id": "T10_LEARN_CJK_STRATEGY",
        "panel": "TRAIN",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:28",
        "declared": 9.2,
        "sample": "与策略",
        "script": "CJK",
        "bbox": (235.67, 252.57, 268.08, 262.39),
        "color": INK,
        "parent": "G04_NODE_LEARN_BORDER",
    },
    {
        "id": "T11_LEARN_MATH_L",
        "panel": "TRAIN",
        "role": "INLINE_MATH",
        "source_line": f"{SOURCE_REL}:28",
        "declared": 9.2,
        "sample": "L",
        "script": "MATH_CAPITAL",
        "class_key": "PLAIN_MATH_CAPITAL",
        "bbox": (271.14, 252.92, 276.98, 262.09),
        "color": INK,
        "parent": "G04_NODE_LEARN_BORDER",
    },
    {
        "id": "T12_MODEL_CJK",
        "panel": "SHARED",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:30",
        "declared": 9.2,
        "sample": "共享模型枢纽",
        "script": "CJK",
        "bbox": (322.88, 275.95, 385.78, 285.77),
        "color": INK,
        "parent": "G05_NODE_MODEL_BORDER",
    },
    {
        "id": "T13_MODEL_MATH_FHAT",
        "panel": "SHARED",
        "role": "FORMULA_BASE",
        "source_line": f"{SOURCE_REL}:30",
        "declared": 9.2,
        "sample": "\\widehat f",
        "script": "MATH_BASE",
        "bbox": (351.15, 288.22, 358.73, 299.91),
        "color": INK,
        "parent": "G05_NODE_MODEL_BORDER",
    },
    {
        "id": "T14_EVAL_LINE1",
        "panel": "TRAIN",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:31",
        "declared": 9.2,
        "sample": "开发评价",
        "script": "CJK",
        "bbox": (434.97, 238.13, 480.62, 247.95),
        "color": INK,
        "parent": "G06_NODE_EVAL_BORDER",
    },
    {
        "id": "T15_EVAL_LINE2",
        "panel": "TRAIN",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:31",
        "declared": 9.2,
        "sample": "误差或结构稳定性",
        "script": "CJK",
        "bbox": (419.51, 252.57, 496.07, 262.39),
        "color": INK,
        "parent": "G06_NODE_EVAL_BORDER",
    },
    {
        "id": "T16_NEW_CJK",
        "panel": "USE",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:32",
        "declared": 9.2,
        "sample": "新输入",
        "script": "CJK",
        "bbox": (131.21, 314.22, 166.42, 324.04),
        "color": INK,
        "parent": "G07_NODE_NEW_BORDER",
    },
    {
        "id": "T17_NEW_MATH_X",
        "panel": "USE",
        "role": "FORMULA_BASE",
        "source_line": f"{SOURCE_REL}:32",
        "declared": 9.2,
        "sample": "x",
        "script": "LATIN_LOWER",
        "bbox": (140.10, 329.01, 145.93, 338.18),
        "color": INK,
        "parent": "G07_NODE_NEW_BORDER",
    },
    {
        "id": "T18_NEW_SUBSCRIPT",
        "panel": "USE",
        "role": "MATH_SCRIPT",
        "source_line": f"{SOURCE_REL}:32",
        "declared": 6.42,
        "sample": "new",
        "script": "MATH_SCRIPT",
        "bbox": (145.93, 333.03, 157.40, 339.45),
        "color": INK,
        "parent": "G07_NODE_NEW_BORDER",
        "base_id": "T17_NEW_MATH_X",
    },
    {
        "id": "T19_PRED_LINE1",
        "panel": "USE",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:33",
        "declared": 9.2,
        "sample": "预测或结构",
        "script": "CJK",
        "bbox": (430.39, 314.67, 485.20, 324.48),
        "color": INK,
        "parent": "G08_NODE_PRED_BORDER",
    },
    {
        "id": "T20_PRED_LINE2",
        "panel": "USE",
        "role": "NODE_LABEL",
        "source_line": f"{SOURCE_REL}:33",
        "declared": 9.2,
        "sample": "可报告结果",
        "script": "CJK",
        "bbox": (430.39, 329.11, 485.20, 338.93),
        "color": INK,
        "parent": "G08_NODE_PRED_BORDER",
    },
    {
        "id": "T21_CAPTION_LABEL_CJK",
        "panel": "CAPTION",
        "role": "CAPTION_LABEL",
        "source_line": f"{SOURCE_REL}:64; {STYLE_REL}:305",
        "declared": 10.0,
        "sample": "图",
        "script": "CJK",
        "bbox": (106.54, 359.42, 116.50, 373.84),
        "color": INK,
        "parent": None,
    },
    {
        "id": "T22_CAPTION_LABEL_NUMBER",
        "panel": "CAPTION",
        "role": "CAPTION_LABEL",
        "source_line": f"{SOURCE_REL}:64; {STYLE_REL}:305",
        "declared": 10.0,
        "sample": "9.1",
        "script": "LATIN_CAPITAL_OR_DIGIT",
        "bbox": (118.84, 363.38, 131.46, 373.35),
        "color": INK,
        "parent": None,
    },
    {
        "id": "T23_CAPTION_BODY",
        "panel": "CAPTION",
        "role": "CAPTION_BODY",
        "source_line": f"{SOURCE_REL}:64; {STYLE_REL}:305",
        "declared": 10.0,
        "sample": "统计学习从数据到模型再到新数据处理的基本闭环。反馈的形式由学习类型决定。",
        "script": "CJK",
        "bbox": (141.42, 363.00, 500.07, 373.67),
        "color": INK,
        "parent": None,
    },
]


# Geometry is taken from the official page's vector drawing paths.  The
# rectangles and paths are mapped directly into the unscaled 300 dpi raster.
GEOMETRY = [
    {
        "id": "G01_PANEL_TRAIN_BORDER",
        "role": "PANEL_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:36-39",
        "rect": (91.0201, 221.5006, 515.5933, 331.9057),
        "stroke": 0.54794,
    },
    {
        "id": "G02_PANEL_USE_BORDER",
        "role": "PANEL_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:40-43",
        "rect": (91.0201, 243.0344, 515.5933, 353.8840),
        "stroke": 0.54794,
    },
    {
        "id": "G03_NODE_DATA_BORDER",
        "role": "NODE_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:27",
        "rect": (102.7324, 233.2129, 194.9009, 265.1904),
        "stroke": 0.74721,
    },
    {
        "id": "G04_NODE_LEARN_BORDER",
        "role": "NODE_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:28",
        "rect": (204.7807, 233.2129, 296.9492, 265.1904),
        "stroke": 0.74721,
    },
    {
        "id": "G05_NODE_MODEL_BORDER",
        "role": "NODE_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:29-30",
        "rect": (308.2468, 254.8712, 400.4153, 320.0688),
        "stroke": 0.99628,
    },
    {
        "id": "G06_NODE_EVAL_BORDER",
        "role": "NODE_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:31",
        "rect": (411.7125, 233.2129, 503.8810, 265.1904),
        "stroke": 0.74721,
    },
    {
        "id": "G07_NODE_NEW_BORDER",
        "role": "NODE_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:32",
        "rect": (102.7324, 309.3051, 194.9009, 342.1717),
        "stroke": 0.74721,
    },
    {
        "id": "G08_NODE_PRED_BORDER",
        "role": "NODE_BORDER",
        "kind": "rect",
        "source_line": f"{SOURCE_REL}:33",
        "rect": (411.7125, 309.7497, 503.8810, 341.7271),
        "stroke": 0.74721,
    },
    {
        "id": "G09_ARROW_DATA_TO_LEARN",
        "role": "LINE_ARROW",
        "kind": "path",
        "source_line": f"{SOURCE_REL}:46-47",
        "stroke": 1.01620,
        "segments": [((195.2746, 249.2017), (196.4178, 249.2017)),
                     ((198.4793, 249.2017), (195.7509, 248.3192)),
                     ((195.7509, 248.3192), (196.6718, 249.2017)),
                     ((196.6718, 249.2017), (195.7509, 250.0842)),
                     ((195.7509, 250.0842), (198.4793, 249.2017))],
    },
    {
        "id": "G10_ARROW_LEARN_TO_MODEL",
        "role": "LINE_ARROW",
        "kind": "path",
        "source_line": f"{SOURCE_REL}:48-49",
        "stroke": 1.01620,
        "segments": [((297.3228, 249.2017), (300.5918, 250.8232)),
                     ((302.4386, 251.7392), (300.3866, 249.7363)),
                     ((300.3866, 249.7363), (300.8194, 250.9360)),
                     ((300.8194, 250.9360), (299.6023, 251.3174)),
                     ((299.6023, 251.3174), (302.4386, 251.7392))],
    },
    {
        "id": "G11_ARROW_MODEL_TO_EVAL",
        "role": "LINE_ARROW",
        "kind": "path",
        "source_line": f"{SOURCE_REL}:50-51",
        "stroke": 1.01620,
        "segments": [((400.9135, 254.3731), (404.1822, 252.7516)),
                     ((406.0288, 251.8356), (403.1927, 252.2574)),
                     ((403.1927, 252.2574), (404.4097, 252.6387)),
                     ((404.4097, 252.6387), (403.9769, 253.8385)),
                     ((403.9769, 253.8385), (406.0288, 251.8356))],
    },
    {
        "id": "G12_ARROW_NEW_TO_MODEL",
        "role": "LINE_ARROW",
        "kind": "path",
        "source_line": f"{SOURCE_REL}:52-53",
        "stroke": 1.01620,
        "segments": [((195.2746, 325.7384), (299.7681, 320.9337)),
                     ((301.8273, 320.8391), (299.0614, 320.0828)),
                     ((299.0614, 320.0828), (300.0219, 320.9220)),
                     ((300.0219, 320.9220), (299.1424, 321.8458)),
                     ((299.1424, 321.8458), (301.8273, 320.8391))],
    },
    {
        "id": "G13_ARROW_MODEL_TO_PRED",
        "role": "LINE_ARROW",
        "kind": "path",
        "source_line": f"{SOURCE_REL}:54-55",
        "stroke": 1.01620,
        "segments": [((400.9135, 320.5670), (404.1822, 322.1885)),
                     ((406.0288, 323.1045), (403.9769, 321.1016)),
                     ((403.9769, 321.1016), (404.4097, 322.3013)),
                     ((404.4097, 322.3013), (403.1927, 322.6826)),
                     ((403.1927, 322.6826), (406.0288, 323.1045))],
    },
    {
        "id": "G14_FEEDBACK_SUPERVISED",
        "role": "LINE_ARROW",
        "kind": "path",
        "source_line": f"{SOURCE_REL}:57-59",
        "stroke": 0.69739,
        "segments": [((457.7967, 232.8393), (457.7967, 212.9966)),
                     ((457.7967, 212.9966), (148.8167, 212.9966)),
                     ((148.8167, 212.9966), (148.8167, 225.1890)),
                     ((148.8167, 227.4016), (149.7660, 224.3474)),
                     ((149.7660, 224.3474), (148.8167, 225.3633)),
                     ((148.8167, 225.3633), (147.8673, 224.3474)),
                     ((147.8673, 224.3474), (148.8167, 227.4016))],
    },
    {
        "id": "G15_FEEDBACK_UNSUPERVISED",
        "role": "LINE_ARROW",
        "kind": "path",
        "source_line": f"{SOURCE_REL}:60-62",
        "stroke": 0.69739,
        "segments": [((457.7967, 232.8393), (457.7967, 198.8232)),
                     ((457.7967, 198.8232), (250.8649, 198.8232)),
                     ((250.8649, 198.8232), (250.8649, 225.1890)),
                     ((250.8649, 227.4016), (251.8143, 224.3474)),
                     ((251.8143, 224.3474), (250.8649, 225.3633)),
                     ((250.8649, 225.3633), (249.9156, 224.3474)),
                     ((249.9156, 224.3474), (250.8649, 227.4016))],
    },
]


def image_bbox_from_pdf(bbox, sx, sy):
    x0, y0, x1, y1 = bbox
    return (
        max(0, int(math.floor(x0 * sx))),
        max(0, int(math.floor(y0 * sy))),
        int(math.ceil(x1 * sx)),
        int(math.ceil(y1 * sy)),
    )


def mode_color(crop: np.ndarray) -> np.ndarray:
    colors, counts = np.unique(crop.reshape(-1, 3), axis=0, return_counts=True)
    return colors[int(np.argmax(counts))]


def bbox_distance(a, b):
    """Pixel gap between two closed, axis-aligned pixel boxes."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1 - 1, ax0 - bx1 - 1)
    dy = max(0, by0 - ay1 - 1, ay0 - by1 - 1)
    return math.hypot(dx, dy)


def points_for_text_mask(mask, bbox):
    x0, y0, _, _ = bbox
    ys, xs = np.where(mask)
    return np.column_stack((xs + x0, ys + y0)).astype(np.float32)


def distance_points_to_segment(points, a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    ab = b - a
    denom = float(np.dot(ab, ab))
    if denom == 0:
        return np.linalg.norm(points - a, axis=1)
    t = np.clip(((points - a) @ ab) / denom, 0.0, 1.0)
    proj = a + t[:, None] * ab
    return np.linalg.norm(points - proj, axis=1)


def rect_border_distances(points, rect, stroke_px):
    """Distance from raw text-ink pixels to a rounded-rect's four straight borders.

    All evaluated label positions are away from rounded corners.  The stroke
    band is subtracted after this function returns the center-line distance.
    """
    x0, y0, x1, y1 = rect
    x = points[:, 0]
    y = points[:, 1]
    inside_x = (x >= x0) & (x <= x1)
    inside_y = (y >= y0) & (y <= y1)
    d_top = np.where(inside_x, np.abs(y - y0), np.hypot(np.minimum(np.abs(x - x0), np.abs(x - x1)), y - y0))
    d_bottom = np.where(inside_x, np.abs(y - y1), np.hypot(np.minimum(np.abs(x - x0), np.abs(x - x1)), y - y1))
    d_left = np.where(inside_y, np.abs(x - x0), np.hypot(x - x0, np.minimum(np.abs(y - y0), np.abs(y - y1))))
    d_right = np.where(inside_y, np.abs(x - x1), np.hypot(x - x1, np.minimum(np.abs(y - y0), np.abs(y - y1))))
    return np.minimum.reduce([d_top, d_bottom, d_left, d_right])


def geometry_distance(points, geometry, sx, sy):
    stroke_px = geometry["stroke"] * (sx + sy) / 4.0
    if geometry["kind"] == "rect":
        x0, y0, x1, y1 = geometry["rect"]
        rect_px = (x0 * sx, y0 * sy, x1 * sx, y1 * sy)
        distance = rect_border_distances(points, rect_px, stroke_px)
    else:
        candidates = []
        for a, b in geometry["segments"]:
            a_px = (a[0] * sx, a[1] * sy)
            b_px = (b[0] * sx, b[1] * sy)
            candidates.append(distance_points_to_segment(points, a_px, b_px))
        distance = np.minimum.reduce(candidates)
    overlap_mask = distance <= stroke_px / 2.0
    overlap = int(np.count_nonzero(overlap_mask))
    clearance = max(0.0, float(np.min(distance)) - stroke_px / 2.0)
    return overlap, clearance, overlap_mask


def rect_to_segment_bounds(geometry):
    if geometry["kind"] == "rect":
        return geometry["rect"]
    xs = []
    ys = []
    for a, b in geometry["segments"]:
        xs.extend((a[0], b[0]))
        ys.extend((a[1], b[1]))
    return (min(xs), min(ys), max(xs), max(ys))


def pixel_distance(a, b):
    """Exact 1:1 raw-pixel gap for nearby masks; fast bbox gap otherwise."""
    rough = bbox_distance(a["ink_bbox"], b["ink_bbox"])
    if rough > 10:
        return rough
    ax = a["ink_points"].astype(np.int32)
    bx = b["ink_points"].astype(np.int32)
    min_x = int(min(ax[:, 0].min(), bx[:, 0].min()) - 2)
    min_y = int(min(ax[:, 1].min(), bx[:, 1].min()) - 2)
    max_x = int(max(ax[:, 0].max(), bx[:, 0].max()) + 3)
    max_y = int(max(ax[:, 1].max(), bx[:, 1].max()) + 3)
    mask = np.zeros((max_y - min_y + 1, max_x - min_x + 1), dtype=np.uint8)
    mask[bx[:, 1] - min_y, bx[:, 0] - min_x] = 1
    # distanceTransform computes the distance to a zero pixel, so invert B.
    distances = cv2.distanceTransform(1 - mask, cv2.DIST_L2, 5)
    return float(distances[ax[:, 1] - min_y, ax[:, 0] - min_x].min())


def under_opaque_node_fill(points, node_rectangles, sx, sy):
    """Panel borders were painted before opaque node fills; hidden portions are
    not final-page foreground and must not be treated as text-line collisions.
    """
    covered = np.zeros(len(points), dtype=bool)
    for rect, stroke in node_rectangles:
        x0, y0, x1, y1 = rect
        half = stroke * (sx + sy) / 4.0 / 2.0
        covered |= (
            (points[:, 0] >= x0 * sx - half)
            & (points[:, 0] <= x1 * sx + half)
            & (points[:, 1] >= y0 * sy - half)
            & (points[:, 1] <= y1 * sy + half)
        )
    return bool(np.all(covered))


def write_csv(path, headers, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not PDF.exists() or not PNG.exists():
        raise SystemExit("The extracted official page PDF and raw 300 dpi PNG are required.")

    image = Image.open(PNG).convert("RGB")
    raw = np.asarray(image)
    width, height = image.size
    if (width, height) != (2481, 3508):
        raise SystemExit(f"Expected 2481x3508 raw 300 dpi image, got {width}x{height}.")

    doc = fitz.open(PDF)
    page = doc[0]
    sx = width / page.rect.width
    sy = height / page.rect.height

    # Raster evidence per text element: local background mode and a color-aware
    # >=20/255 contrast mask in the exact vector text bounds (+2px safety pad).
    element_by_id = {}
    for element in TEXT_ELEMENTS:
        vector_bbox = image_bbox_from_pdf(element["bbox"], sx, sy)
        vx0, vy0, vx1, vy1 = vector_bbox
        # The embedded PDF text bbox is already an ascent/descent box.  Do not
        # pad it: a pad can absorb a neighbouring node/panel stroke and turn
        # a clear gap into a false text mask.
        roi_bbox = vector_bbox
        rx0, ry0, rx1, ry1 = roi_bbox
        crop = raw[ry0:ry1, rx0:rx1]
        background = mode_color(crop).astype(np.int16)
        expected = np.asarray(element["color"], dtype=np.int16)
        work = crop.astype(np.int16)
        contrast = np.max(np.abs(work - background), axis=2)
        color_distance = np.linalg.norm(work - expected, axis=2)
        mask = (contrast >= 20) & (color_distance <= 200.0)
        if int(np.count_nonzero(mask)) == 0:
            mask = contrast >= 20
        # A vector text bbox can abut a same-colour node stroke by <1 raw px.
        # Treat a row that is >70% solid foreground as a non-text horizontal
        # rule, not as glyph ink. This removes only the adjacent node outline
        # at the T03 lower bbox boundary; it cannot remove ordinary CJK glyphs.
        row_coverage = mask.mean(axis=1)
        mask[row_coverage > 0.70, :] = False
        ys, xs = np.where(mask)
        if len(xs) == 0:
            element["measurement_unknown"] = True
            element["ink_bbox"] = None
            element["ink_points"] = np.zeros((0, 2), dtype=np.float32)
            element["h_ink"] = None
        else:
            element["measurement_unknown"] = False
            ink_bbox = (int(rx0 + xs.min()), int(ry0 + ys.min()), int(rx0 + xs.max()), int(ry0 + ys.max()))
            element["ink_bbox"] = ink_bbox
            element["ink_points"] = points_for_text_mask(mask, roi_bbox)
            element["h_ink"] = int(ys.max() - ys.min() + 1)
        element["vector_bbox_px"] = vector_bbox
        element["roi_bbox_px"] = roi_bbox
        element_by_id[element["id"]] = element

    # Same-role / same-script pixel medians are calculated only after raw ink
    # measurement.  Caption roles are tracked but not used as the diagram's
    # local hierarchy base.
    classes = {}
    for element in TEXT_ELEMENTS:
        key = (element["role"], element.get("class_key", element["script"]))
        classes.setdefault(key, []).append(element)
    for members in classes.values():
        heights = [member["h_ink"] for member in members if member["h_ink"] is not None]
        med = float(median(heights)) if heights else None
        for member in members:
            member["class_median"] = med
            member["class_ratio"] = None if med in (None, 0) or member["h_ink"] is None else member["h_ink"] / med
            member["same_class_pass"] = bool(member["class_ratio"] is not None and 0.92 <= member["class_ratio"] <= 1.08)

    base_ids = ["T05_DATA_LINE1", "T06_DATA_LINE2", "T07_LEARN_CJK", "T10_LEARN_CJK_STRATEGY", "T12_MODEL_CJK", "T14_EVAL_LINE1", "T15_EVAL_LINE2", "T16_NEW_CJK", "T19_PRED_LINE1", "T20_PRED_LINE2"]
    base_heights = [element_by_id[item]["h_ink"] for item in base_ids if element_by_id[item]["h_ink"] is not None]
    base_median = float(median(base_heights)) if base_heights else None

    # Role hierarchy is assessed only where §9.2.1 establishes a comparable
    # role. Inline math is separately checked by its script-class threshold.
    role_members = {
        "PANEL_LABEL": [e for e in TEXT_ELEMENTS if e["role"] == "PANEL_LABEL"],
        "FEEDBACK_LABEL": [e for e in TEXT_ELEMENTS if e["role"] == "FEEDBACK_LABEL"],
    }
    role_medians = {}
    for role, members in role_members.items():
        values = [e["h_ink"] for e in members if e["h_ink"] is not None]
        role_medians[role] = float(median(values)) if values else None
    required_role_ranges = {"PANEL_LABEL": (1.05, 1.20), "FEEDBACK_LABEL": (0.95, 1.10)}
    for element in TEXT_ELEMENTS:
        if element["role"] in role_medians and base_median:
            ratio = role_medians[element["role"]] / base_median
            low, high = required_role_ranges[element["role"]]
            element["role_ratio"] = ratio
            element["role_ratio_pass"] = low <= ratio <= high
        else:
            element["role_ratio"] = None
            element["role_ratio_pass"] = True

    def threshold_for(script):
        if script == "CJK":
            return 30
        if script == "LATIN_CAPITAL_OR_DIGIT" or script == "MATH_CAPITAL":
            return 24
        if script == "LATIN_LOWER":
            return 17
        if script == "MATH_BASE":
            return 22
        if script == "MATH_SCRIPT":
            return 15
        raise ValueError(script)

    # Source compliance, including the required natural-script provenance.
    for element in TEXT_ELEMENTS:
        if element["script"] == "MATH_SCRIPT":
            base = element_by_id[element["base_id"]]
            source_pass = base["declared"] >= 9.5
            source_reason = (
                "script is natural only if base formula >=9.5pt; base x is 9.2pt"
                if not source_pass
                else "natural script from >=9.5pt base formula"
            )
        else:
            source_pass = element["declared"] >= 9.5
            source_reason = "effective_pt >= 9.5pt" if source_pass else "effective_pt below 9.5pt"
        element["source_font_pass"] = source_pass
        element["source_reason"] = source_reason
        h = element["h_ink"]
        element["pixel_threshold"] = threshold_for(element["script"])
        element["pixel_pass"] = bool(h is not None and h >= element["pixel_threshold"])

    # Pixel-level all-pairs text versus text and text versus geometry checks.
    geometry_by_id = {g["id"]: g for g in GEOMETRY}
    overlap_rows = []
    node_rectangles = [
        (g["rect"], g["stroke"])
        for g in GEOMETRY
        if g["role"] == "NODE_BORDER" and g["kind"] == "rect"
    ]
    text_text_min = {e["id"]: float("inf") for e in TEXT_ELEMENTS}
    text_graphic_min = {e["id"]: float("inf") for e in TEXT_ELEMENTS}
    text_text_overlap = {e["id"]: 0 for e in TEXT_ELEMENTS}
    text_graphic_overlap_sets = {e["id"]: set() for e in TEXT_ELEMENTS}

    for a, b in combinations(TEXT_ELEMENTS, 2):
        compound_pair = a.get("base_id") == b["id"] or b.get("base_id") == a["id"]
        if compound_pair:
            overlap = 0
            clearance = float("inf")
            outcome = "PASS"
            reason = "one natural base-script formula; not independent semantic text objects"
        elif a["ink_bbox"] is None or b["ink_bbox"] is None:
            overlap = 0
            clearance = float("nan")
            outcome = "FAIL"
            reason = "one or both raw text masks missing"
        else:
            a_pixels = set(map(tuple, a["ink_points"].astype(np.int32)))
            b_pixels = set(map(tuple, b["ink_points"].astype(np.int32)))
            overlap = len(a_pixels & b_pixels)
            clearance = pixel_distance(a, b)
            outcome = "PASS" if clearance >= 4.0 else "FAIL"
            reason = "1:1 raw ink gap >=4px" if outcome == "PASS" else "1:1 raw ink gap <4px"
        if not compound_pair:
            text_text_min[a["id"]] = min(text_text_min[a["id"]], clearance)
            text_text_min[b["id"]] = min(text_text_min[b["id"]], clearance)
        text_text_overlap[a["id"]] += overlap
        text_text_overlap[b["id"]] += overlap
        overlap_rows.append(
            {
                "CHECK_ID": f"TT_{a['id']}_{b['id']}",
                "OBJECT_A_ID": a["id"],
                "OBJECT_A_CLASS": "TEXT",
                "OBJECT_B_ID": b["id"],
                "OBJECT_B_CLASS": "TEXT",
                "ROI_BASIS": "official_page_152_300dpi.png; raw ink bboxes",
                "METHOD": "1:1 raw-pixel ink bbox gap",
                "OVERLAP_PIXEL_COUNT": overlap,
                "MIN_CLEARANCE_PX": "" if math.isnan(clearance) else f"{clearance:.2f}",
                "REQUIRED_MIN_CLEARANCE_PX": 4,
                "PASS_FAIL": outcome,
                "REASON": reason,
            }
        )

    for element in TEXT_ELEMENTS:
        for geometry in GEOMETRY:
            if element["ink_bbox"] is None:
                overlap = 0
                clearance = float("nan")
                outcome = "FAIL"
                reason = "raw text mask missing"
                overlap_mask = None
            elif geometry["role"] == "PANEL_BORDER" and under_opaque_node_fill(element["ink_points"], node_rectangles, sx, sy):
                # Background-layer panel strokes disappear under filled nodes.
                # The raw PNG therefore contains no independent foreground
                # panel stroke at these text pixels.
                overlap = 0
                clearance = float("inf")
                outcome = "PASS"
                reason = "panel stroke lies behind an opaque node fill at this text"
                overlap_mask = None
            else:
                overlap, clearance, overlap_mask = geometry_distance(element["ink_points"], geometry, sx, sy)
                required = 5 if geometry["role"] == "NODE_BORDER" else 3
                outcome = "PASS" if overlap == 0 and clearance >= required else "FAIL"
                if overlap:
                    reason = "independent text mask intersects the mapped vector stroke band"
                elif clearance < required:
                    reason = f"mapped vector clearance {clearance:.2f}px < {required}px"
                else:
                    reason = "zero intersection and required clearance met"
            required = 5 if geometry["role"] == "NODE_BORDER" else 3
            text_graphic_min[element["id"]] = min(text_graphic_min[element["id"]], clearance)
            if overlap_mask is not None and overlap:
                for point in element["ink_points"][overlap_mask].astype(np.int32):
                    text_graphic_overlap_sets[element["id"]].add((int(point[0]), int(point[1])))
            overlap_rows.append(
                {
                    "CHECK_ID": f"TG_{element['id']}_{geometry['id']}",
                    "OBJECT_A_ID": element["id"],
                    "OBJECT_A_CLASS": "TEXT",
                    "OBJECT_B_ID": geometry["id"],
                    "OBJECT_B_CLASS": geometry["role"],
                    "ROI_BASIS": "official_page_152_300dpi.png; mapped official PDF vector geometry",
                    "METHOD": "1:1 raw text mask vs stroke-center geometry mapped at 300 dpi",
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "MIN_CLEARANCE_PX": "" if math.isnan(clearance) else f"{clearance:.2f}",
                    "REQUIRED_MIN_CLEARANCE_PX": required,
                    "PASS_FAIL": outcome,
                    "REASON": reason,
                }
            )

    # Finish per-element clearance / result after both pair matrices exist.
    for element in TEXT_ELEMENTS:
        min_text = text_text_min[element["id"]]
        min_graphic = text_graphic_min[element["id"]]
        element["min_clearance"] = min(min_text, min_graphic)
        element["text_text_overlap"] = text_text_overlap[element["id"]]
        element["text_graphic_overlap"] = len(text_graphic_overlap_sets[element["id"]])
        element["clearance_pass"] = (
            element["text_text_overlap"] == 0
            and element["text_graphic_overlap"] == 0
            and min_text >= 4
            and min_graphic >= 3
        )
        fail_reasons = []
        if not element["source_font_pass"]:
            fail_reasons.append(element["source_reason"])
        if not element["pixel_pass"]:
            fail_reasons.append(f"H_ink={element['h_ink']}px below {element['pixel_threshold']}px")
        if not element["same_class_pass"]:
            fail_reasons.append("same-class ratio outside [0.92,1.08]")
        if not element["role_ratio_pass"]:
            fail_reasons.append("role ratio outside required range")
        if not element["clearance_pass"]:
            fail_reasons.append("zero-overlap/min-clearance requirement failed")
        element["pass_fail"] = "PASS" if not fail_reasons else "FAIL"
        element["reason"] = "; ".join(fail_reasons) if fail_reasons else "all per-element checks passed"

    # Stable, explicit source font audit.
    font_rows = []
    for element in TEXT_ELEMENTS:
        font_rows.append(
            {
                "ELEMENT_ID": element["id"],
                "PANEL_ID": element["panel"],
                "ROLE": element["role"],
                "SOURCE_FILE": SOURCE_REL,
                "SOURCE_LINE": element["source_line"],
                "DECLARED_PT": f"{element['declared']:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{element['declared']:.2f}",
                "TEXT_SAMPLE": element["sample"],
                "SCRIPT_CLASS": element["script"],
                "SOURCE_FONT_PASS": str(element["source_font_pass"]).lower(),
                "REASON": element["source_reason"],
            }
        )
    write_csv(
        OUT / "after_font_audit.csv",
        list(font_rows[0].keys()),
        font_rows,
    )

    pixel_rows = []
    for element in TEXT_ELEMENTS:
        bbox = element["ink_bbox"]
        pixel_rows.append(
            {
                "ELEMENT_ID": element["id"],
                "PANEL_ID": element["panel"],
                "ROLE": element["role"],
                "SOURCE_FILE": SOURCE_REL,
                "SOURCE_LINE": element["source_line"],
                "DECLARED_PT": f"{element['declared']:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{element['declared']:.2f}",
                "TEXT_SAMPLE": element["sample"],
                "SCRIPT_CLASS": element["script"],
                "BBOX_X0": "" if bbox is None else bbox[0],
                "BBOX_Y0": "" if bbox is None else bbox[1],
                "BBOX_X1": "" if bbox is None else bbox[2],
                "BBOX_Y1": "" if bbox is None else bbox[3],
                "H_INK_PX": "" if element["h_ink"] is None else element["h_ink"],
                "PIXEL_THRESHOLD_PX": element["pixel_threshold"],
                "CLASS_MEDIAN_PX": "" if element["class_median"] is None else f"{element['class_median']:.2f}",
                "RATIO_TO_CLASS_MEDIAN": "" if element["class_ratio"] is None else f"{element['class_ratio']:.4f}",
                "ROLE_RATIO": "N/A" if element["role_ratio"] is None else f"{element['role_ratio']:.4f}",
                "TEXT_TEXT_OVERLAP_PX": element["text_text_overlap"],
                "TEXT_GRAPHIC_OVERLAP_PX": element["text_graphic_overlap"],
                "MIN_CLEARANCE_PX": f"{element['min_clearance']:.2f}",
                "PASS_FAIL": element["pass_fail"],
                "REASON": element["reason"],
            }
        )
    write_csv(
        OUT / "after_pixel_measurements.csv",
        list(pixel_rows[0].keys()),
        pixel_rows,
    )
    write_csv(
        OUT / "after_overlap_report.csv",
        list(overlap_rows[0].keys()),
        overlap_rows,
    )

    # Inventory includes all reader-visible semantic elements plus every
    # node/panel/arrow/feedback geometry element used in the collision matrix.
    inventory_rows = []
    for element in TEXT_ELEMENTS:
        bbox = element["vector_bbox_px"]
        inventory_rows.append(
            {
                "ELEMENT_ID": element["id"],
                "CLASS": "TEXT",
                "ROLE": element["role"],
                "PANEL_ID": element["panel"],
                "SOURCE_LINE": element["source_line"],
                "BBOX_OR_PATH_PX": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                "TEXT_OR_OBJECT": element["sample"],
            }
        )
    for geometry in GEOMETRY:
        bbox = image_bbox_from_pdf(rect_to_segment_bounds(geometry), sx, sy)
        inventory_rows.append(
            {
                "ELEMENT_ID": geometry["id"],
                "CLASS": geometry["role"],
                "ROLE": geometry["role"],
                "PANEL_ID": "TRAIN/USE/SHARED" if "PANEL" in geometry["id"] else "FIGURE",
                "SOURCE_LINE": geometry["source_line"],
                "BBOX_OR_PATH_PX": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                "TEXT_OR_OBJECT": geometry["id"],
            }
        )
    write_csv(OUT / "element_inventory.csv", list(inventory_rows[0].keys()), inventory_rows)

    # Crops preserve raw pixels exactly: slicing only, never resampling.
    def crop_pdf(name, bbox_pdf):
        x0, y0, x1, y1 = image_bbox_from_pdf(bbox_pdf, sx, sy)
        Image.fromarray(raw[y0:y1, x0:x1]).save(OUT / name)

    crop_pdf("figure_crop_300dpi.png", (75.0, 178.0, 525.0, 380.0))
    crop_pdf("standalone_figure_300dpi.png", (75.0, 178.0, 525.0, 357.0))
    crop_pdf("roi_feedback_loops_1to1.png", (115.0, 180.0, 465.0, 238.0))
    crop_pdf("roi_train_label_panel_border_1to1.png", (185.0, 212.0, 260.0, 240.0))
    crop_pdf("roi_use_label_panel_border_1to1.png", (185.0, 333.0, 260.0, 362.0))
    crop_pdf("roi_model_node_clearance_1to1.png", (300.0, 250.0, 410.0, 325.0))
    grayscale = ImageOps.grayscale(Image.open(OUT / "figure_crop_300dpi.png"))
    grayscale.save(OUT / "after_grayscale_300dpi.png")

    # Full-page text measurement overlay (evidence only, never measurement
    # input).  Failing source/geometry elements are red; passed caption values
    # are green.  IDs are ASCII so the label font remains deterministic.
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    for element in TEXT_ELEMENTS:
        bbox = element["ink_bbox"] or element["vector_bbox_px"]
        color = (205, 49, 49) if element["pass_fail"] == "FAIL" else (18, 128, 66)
        draw.rectangle(bbox, outline=color, width=2)
        tx, ty = bbox[0], max(0, bbox[1] - 12)
        draw.rectangle((tx, ty, min(width - 1, tx + len(element["id"]) * 6 + 4), bbox[1] - 1), fill=(255, 255, 255))
        draw.text((tx + 2, ty), element["id"], fill=color)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Exact 1:1 measurement summary for root reproducibility.
    # Union by text pixel, rather than summing duplicate pair hits.
    graphics_overlap_total = sum(e["text_graphic_overlap"] for e in TEXT_ELEMENTS)
    text_overlap_total = sum(e["text_text_overlap"] for e in TEXT_ELEMENTS) // 2
    clip_count = 0
    for element in TEXT_ELEMENTS:
        if element["ink_bbox"] is None:
            continue
        x0, y0, x1, y1 = element["ink_bbox"]
        if x0 <= 0 or y0 <= 0 or x1 >= width - 1 or y1 >= height - 1:
            clip_count += 1
    source_font_pass = all(e["source_font_pass"] for e in TEXT_ELEMENTS)
    pixel_height_pass = all(e["pixel_pass"] for e in TEXT_ELEMENTS)
    same_class_pass = all(e["same_class_pass"] for e in TEXT_ELEMENTS)
    role_ratio_pass = all(e["role_ratio_pass"] for e in TEXT_ELEMENTS)
    clearance_pass = all(e["clearance_pass"] for e in TEXT_ELEMENTS)

    metadata = {
        "official_pdf": str(PDF.name),
        "official_physical_page": 152,
        "raw_png": str(PNG.name),
        "raw_png_size": [width, height],
        "pdf_page_size_points": [page.rect.width, page.rect.height],
        "pixel_mapping": {"x_px_per_pdf_point": sx, "y_px_per_pdf_point": sy},
        "contrast_threshold": 20,
        "element_count": len(TEXT_ELEMENTS),
        "geometry_count": len(GEOMETRY),
        "base_role": "NODE_LABEL / CJK",
        "base_median_ink_px": base_median,
        "role_medians_ink_px": role_medians,
        "source_font_pass": source_font_pass,
        "pixel_height_pass": pixel_height_pass,
        "same_class_pass": same_class_pass,
        "role_ratio_pass": role_ratio_pass,
        "text_text_overlap_px": text_overlap_total,
        "text_graphic_overlap_px": graphics_overlap_total,
        "clip_pixel_count": clip_count,
        "minimum_text_or_graphic_clearance_px": min(e["min_clearance"] for e in TEXT_ELEMENTS),
    }
    (OUT / "strict_r1_measurement_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Required strict acceptance record.
    visual = f"""# FIG-P142-01 strict R1 visual acceptance\n\n+Official object: `main_full.pdf`, physical page 152.\n\n+Raw measurement input: `official_page_152_300dpi.png` (2481×3508, direct 300 dpi render; no resizing/re-sampling).\n\n+SOURCE_FONT_PASS = {str(source_font_pass).lower()}\n+PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}\n+SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}\n+ROLE_RATIO_PASS = {str(role_ratio_pass).lower()}\n+OVERLAP_PIXEL_COUNT = {graphics_overlap_total + text_overlap_total}\n+CLIP_PIXEL_COUNT = {clip_count}\n+MIN_TEXT_CLEARANCE_PX = {min(e['min_clearance'] for e in TEXT_ELEMENTS):.2f}\n+VISUAL_HARMONY_PASS = false\n+MATH_SEMANTICS_PASS = true\n+TEXT_CONSISTENCY_PASS = true\n+GRAYSCALE_PASS = true\n+PAGE_INTEGRATION_PASS = true\n+\n+## Measurement outcome\n+\n+- Source effective-size failure: all node labels and both panel labels are 9.2pt; both feedback labels are 8.6pt. All are below the 9.5pt reader-text floor. The `new` subscript is 6.42pt and cannot qualify as legal natural script because its base `x` is also only 9.2pt.\n+- Geometry failure: `T03_PANEL_TRAIN` intersects `G01_PANEL_TRAIN_BORDER`, and `T04_PANEL_USE` intersects `G02_PANEL_USE_BORDER` when the official PDF vector stroke bands are mapped into the raw 300 dpi pixel grid. These are direct text-to-panel-border collisions; no opaque label backing exists in the source.\n+- The whole-page, raw figure crop, 1:1 local ROIs, and grayscale image are retained in this directory. Pixel height / class-ratio values are in `after_pixel_measurements.csv`; every text-text and text-graphic comparison is in `after_overlap_report.csv`.\n+\n+## Visual / semantic review\n+\n+- Information flow is semantically coherent: training data and learning algorithm produce the shared model; evaluation supplies supervised or unsupervised feedback; new input enters the same model and leads to a reportable result.\n+- Caption and immediately following reading sentence agree with this closed-loop interpretation and correctly warn that feedback from testing turns it into development information.\n+- The solid/dashed structural distinction remains legible in grayscale, and the page has normal caption/body integration.\n+- These strengths cannot override the source-font and zero-overlap hard failures. The overlapping phase labels also reduce visual harmony even though the rest of the flow is structurally readable.\n+\n+## Required repair direction (no edits made)\n+\n+1. Raise normal node and phase-label effective text to at least 9.5pt, and raise feedback labels to at least 9.5pt; preserve required panel/role ratios after re-rendering.\n+2. Reposition the two phase labels completely outside their panel border stroke bands, or give them an explicit opaque backing with at least the required 3px text-to-border clearance; then remeasure at raw 300 dpi.\n+3. Re-run every source, pixel, ratio, collision, clipping, ROI, grayscale, semantic and page-integration check from a new candidate PDF.\n+\n+RESULT: FAIL\n+"""
    # Keep the final human-readable acceptance record concise and free of
    # report-template markup; all values remain tied to the computed evidence.
    visual = f"""# FIG-P142-01 strict R1 visual acceptance

Official object: `main_full.pdf`, physical page 152.

Raw measurement input: `official_page_152_300dpi.png` (2481×3508, direct 300 dpi render; no resizing or resampling).

SOURCE_FONT_PASS = {str(source_font_pass).lower()}
PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}
SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}
ROLE_RATIO_PASS = {str(role_ratio_pass).lower()}
OVERLAP_PIXEL_COUNT = {graphics_overlap_total + text_overlap_total}
CLIP_PIXEL_COUNT = {clip_count}
MIN_TEXT_CLEARANCE_PX = {min(e['min_clearance'] for e in TEXT_ELEMENTS):.2f}
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

## Measurement outcome

- Source effective-size failure: all node labels and both phase labels are 9.2pt; both feedback labels are 8.6pt. All are below the 9.5pt reader-text floor. The `new` subscript is 6.42pt and cannot qualify as legal natural script because its base `x` is only 9.2pt.
- Pixel-height failure: `T18_NEW_SUBSCRIPT` measures 13px at the required raw 300 dpi, below the 15px script floor.
- Role-ratio failure: feedback-label median = 31px; ordinary node-text base median = 33px; ratio = 0.9394, below the 0.95 lower bound for a normal annotation.
- Geometry pass: the complete matrix records 0 text-text overlap pixels, 0 text-graphic overlap pixels, 0 clipping pixels, and all pair-specific clearances pass. The global 3.48px minimum is a text-to-line case whose 3px floor is met; text-text and node-text/border rows meet their 4px and 5px floors.
- The whole-page, raw figure crop, 1:1 local ROIs, and grayscale image are retained in this directory. Pixel height/class-ratio values are in `after_pixel_measurements.csv`; every text-text and text-graphic comparison is in `after_overlap_report.csv`.

## Visual / semantic review

- Information flow is semantically coherent: training data and learning algorithm produce the shared model; evaluation supplies supervised or unsupervised feedback; new input enters the same model and leads to a reportable result.
- Caption and immediately following reading sentence agree with this closed-loop interpretation and correctly warn that feedback from testing turns it into development information.
- The solid/dashed structural distinction remains legible in grayscale, and the page has normal caption/body integration.
- These strengths cannot override the source-font, script-pixel-height, and feedback-role-ratio hard failures. The undersized feedback annotation also reduces visual harmony.

## Required repair direction (no edits made)

1. Raise normal node/phase-label and feedback-label effective text to at least 9.5pt.
2. Rebalance feedback labels after enlargement so their raw median reaches at least 0.95 of the normal node-text base without exceeding the 1.25 emphasis ceiling; recheck clearances after placement.
3. Re-run every source, pixel, ratio, collision, clipping, ROI, grayscale, semantic and page-integration check from a new candidate PDF.

RESULT: FAIL
"""
    (OUT / "after_visual_acceptance.md").write_text(visual, encoding="utf-8")

    report = f"""RESULT: FAIL\n+\n+# FIG-P142-01 — SA1 strict R1 independent recheck\n+\n+Scope: independently reviewed only the official `main_full.pdf` physical page 152 and the assigned figure source. No prior SA1/SA2/SA3/ROOT report, state, PASS, or FAIL record for this figure was read. No source, wrapper, common file, inventory, or project state was modified.\n+\n+## Object and evidence\n+\n+- Figure: 9.1 / `FIG-P142-01`\n+- Official source PDF: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r90_fullbook/main_full.pdf`, physical page 152\n+- Figure source: `{SOURCE_REL}`\n+- Extracted official page: `official_page_152.pdf`\n+- Native raw render: `official_page_152_300dpi.png`, 2481×3508 pixels (A4 at 300 dpi); no resize or resampling\n+- Source-font inventory: `after_font_audit.csv`\n+- 300 dpi per-element pixel evidence: `after_pixel_measurements.csv` and `after_text_measurement_overlay_300dpi.png`\n+- Pixel collision / clearance matrix: `after_overlap_report.csv`\n+- Full element inventory: `element_inventory.csv`\n+- Four visual modes and 1:1 ROIs: `official_page_152_300dpi.png`, `official_page_152_fit_200dpi.png`, `figure_crop_300dpi.png`, `standalone_figure_300dpi.png`, `after_grayscale_300dpi.png`, and `roi_*_1to1.png`\n+\n+## Strict result\n+\n+The candidate fails the §9.2.1 hard gate. `after_font_audit.csv` establishes the following source-level violations:\n+\n+- Node labels and phase labels: `effective_pt = 9.2`, below the `>=9.5pt` floor.\n+- Feedback labels: `effective_pt = 8.6`, below the same floor.\n+- `x_{{\\rm new}}`: its 6.42pt script cannot be grandfathered because the base formula is only 9.2pt, not `>=9.5pt`.\n+\n+The 1:1 mapped geometry check also identifies real text-to-panel-border collisions for `T03_PANEL_TRAIN ↔ G01_PANEL_TRAIN_BORDER` and `T04_PANEL_USE ↔ G02_PANEL_USE_BORDER`. The collision totals and minimum clearances are preserved in the required CSVs and the corresponding 1:1 ROIs. These failures independently require FAIL; a readable appearance, semantic correctness, grayscale legibility, and good page integration cannot override them.\n+\n+## Independent content findings\n+\n+- Mathematics/information flow: PASS. The model is correctly shared by training and use; the dashed feedback loops correctly distinguish supervised label/error feedback from unsupervised structural-stability feedback.\n+- Caption and adjacent reading sentence: PASS. They state the same closed-loop claim and correctly explain that feedback contaminates a test set as a one-time generalization source.\n+- Grayscale and page integration: PASS. Dashed versus solid structure remains distinguishable without color; caption/body placement is coherent.\n+- Visual harmony: FAIL at strict level because undersized feedback text and phase-label/border collisions remain.\n+\n+## Required next action\n+\n+This is not an SA1 candidate. A repair pass must raise all reader-visible diagram text to the hard source floor and move/back the phase labels clear of the panel strokes, then generate a new PDF and a wholly new independent strict audit.\n+"""
    report = f"""RESULT: FAIL

# FIG-P142-01 — SA1 strict R1 independent recheck

Scope: independently reviewed only the official `main_full.pdf` physical page 152 and the assigned figure source. No prior SA1/SA2/SA3/ROOT report, state, PASS, or FAIL record for this figure was read. No source, wrapper, common file, inventory, or project state was modified.

## Object and evidence

- Figure: 9.1 / `FIG-P142-01`
- Official source PDF: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r90_fullbook/main_full.pdf`, physical page 152
- Figure source: `{SOURCE_REL}`
- Extracted official page: `official_page_152.pdf`
- Native raw render: `official_page_152_300dpi.png`, 2481×3508 pixels (A4 at 300 dpi); no resize or resampling
- Source-font inventory: `after_font_audit.csv`
- 300 dpi per-element pixel evidence: `after_pixel_measurements.csv` and `after_text_measurement_overlay_300dpi.png`
- Pixel collision / clearance matrix: `after_overlap_report.csv`
- Full element inventory: `element_inventory.csv`
- Four visual modes and 1:1 ROIs: `official_page_152_300dpi.png`, `official_page_152_fit_200dpi.png`, `figure_crop_300dpi.png`, `standalone_figure_300dpi.png`, `after_grayscale_300dpi.png`, and `roi_*_1to1.png`

## Strict result

The candidate fails the §9.2.1 hard gate.

- Node labels and phase labels: `effective_pt = 9.2`, below the `>=9.5pt` floor.
- Feedback labels: `effective_pt = 8.6`, below the same floor.
- The `new` script is derived from a base formula at only 9.2pt, so it cannot be a permitted natural script; its raw measured height is also 13px, below the required 15px.
- Feedback-label raw median = 31px versus a 33px ordinary node-text base, yielding 0.9394 rather than the required `>=0.95` annotation ratio.

The 1:1 mapped geometry check passes: all illegal text-text and text-graphic intersections are zero, clipping is zero, and every pair-specific clearance is at or above its applicable threshold. These results are retained in the required CSVs and 1:1 ROIs, but cannot override the source, pixel, and role-ratio hard failures.

## Independent content findings

- Mathematics/information flow: PASS. The model is correctly shared by training and use; the dashed feedback loops distinguish supervised label/error feedback from unsupervised structural-stability feedback.
- Caption and adjacent reading sentence: PASS. They state the same closed-loop claim and correctly explain that feedback contaminates a test set as a one-time generalization source.
- Grayscale and page integration: PASS. Dashed versus solid structure remains distinguishable without color; caption/body placement is coherent.
- Visual harmony: FAIL at strict level because the feedback annotation is undersized relative to the normal node-text base.

## Required next action

This is not an SA1 candidate. A repair pass must raise all reader-visible diagram text to the hard source floor, restore the feedback-label hierarchy, preserve local clearances after enlargement, and then generate a new PDF and a wholly new independent strict audit.
"""
    (OUT / "FIG-P142-01-SA1-STRICT-R1.md").write_text(report, encoding="utf-8")

    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
