#!/usr/bin/env python3
"""Independent, candidate-locked evidence generator for FIG-P756-01.

The script deliberately keeps the native 300 dpi page raster immutable: all
measurements use its integer pixel grid.  It produces machine measurements
only; the reviewer ledger is completed after opening every contact sheet.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.spatial import cKDTree


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C08.tex")
AUX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.aux")
FLS = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.fls")

PDF_PAGE = 801  # PyMuPDF uses zero based positions; this is the physical PDF page.
PRINTED_PAGE = 788
EXPECTED_PDF_SHA256 = "062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814"

# Integer coordinates in the unscaled 300 dpi page raster.  The crop includes
# the complete TikZ body (panel labels through legend), with >= 6 px padding.
CROP = (300, 700, 2150, 1995)  # x0, y0, x1, y1, exclusive
FIGURE_PT = (70.0, 167.0, 515.0, 479.0)


@dataclass(frozen=True)
class Group:
    ident: str
    role: str
    panel: str
    bbox: tuple[float, float, float, float]
    declared_pt: float
    source_line: int


# Source-defined semantic text objects. Each member receives all of its
# visible glyphs from the current candidate; no text is inferred from OCR.
GROUPS = [
    Group("T001_PANEL_A", "PANEL_TITLE", "A", (70, 167, 210, 190), 10.2, 35),
    Group("T002_FEEDBACK", "ANNOTATION", "A", (205, 188, 375, 205), 9.6, 52),
    Group("T003_STATION_PROBLEM", "STATION_TEXT", "A", (78, 235, 150, 281), 9.6, 37),
    Group("T004_STATION_MODEL", "STATION_TEXT", "A", (166, 235, 239, 281), 9.6, 38),
    Group("T005_STATION_COMPUTE", "STATION_TEXT", "A", (254, 235, 328, 281), 9.6, 39),
    Group("T006_STATION_EVIDENCE", "STATION_TEXT", "A", (342, 235, 417, 281), 9.6, 40),
    Group("T007_STATION_BOUNDARY", "STATION_TEXT", "A", (431, 235, 504, 281), 9.6, 41),
    Group("T008_BADGE_1", "BADGE_DIGIT", "A", (75, 220, 95, 239), 9.6, 47),
    Group("T009_BADGE_2", "BADGE_DIGIT", "A", (164, 220, 184, 239), 9.6, 47),
    Group("T010_BADGE_3", "BADGE_DIGIT", "A", (253, 220, 273, 239), 9.6, 47),
    Group("T011_BADGE_4", "BADGE_DIGIT", "A", (341, 220, 361, 239), 9.6, 47),
    Group("T012_BADGE_5", "BADGE_DIGIT", "A", (430, 220, 450, 239), 9.6, 47),
    Group("T013_PANEL_B", "PANEL_TITLE", "B", (70, 308, 250, 331), 10.2, 56),
    Group("T014_ROUTE_SUPERVISED", "ROUTE_TEXT", "B", (78, 347, 151, 395), 9.6, 57),
    Group("T015_ROUTE_UNSUPERVISED", "ROUTE_TEXT", "B", (78, 398, 151, 447), 9.6, 59),
    Group("T016_POOL_TITLE", "PANEL_TITLE", "B", (200, 340, 310, 364), 10.2, 63),
    Group("T017_POOL_NOTE", "ANNOTATION", "B", (200, 362, 310, 382), 9.6, 64),
    Group("T018_CHIP_LINALG", "ENGINE_CHIP", "B", (190, 384, 256, 413), 9.6, 65),
    Group("T019_CHIP_OPTIM", "ENGINE_CHIP", "B", (255, 384, 326, 413), 9.6, 66),
    Group("T020_CHIP_PROB", "ENGINE_CHIP", "B", (190, 412, 256, 441), 9.6, 67),
    Group("T021_CHIP_INFER", "ENGINE_CHIP", "B", (255, 412, 326, 441), 9.6, 68),
    Group("T022_VALIDATION", "VALIDATION_TEXT", "B", (339, 367, 424, 426), 9.6, 70),
    Group("T023_REPORT", "REPORT_TEXT", "B", (430, 365, 516, 431), 9.6, 72),
    Group("T024_EXIT_NOTE", "ANNOTATION", "B", (438, 340, 510, 365), 9.6, 74),
    Group("T025_LEGEND", "LEGEND", "B", (80, 459, 510, 480), 9.6, 80),
]

DRAWING_NAMES = {
    4: ("G001_STATION_PROBLEM_BORDER", "NODE_BORDER", 37),
    5: ("G002_STATION_MODEL_BORDER", "NODE_BORDER", 38),
    6: ("G003_STATION_COMPUTE_BORDER", "NODE_BORDER", 39),
    7: ("G004_STATION_EVIDENCE_BORDER", "NODE_BORDER", 40),
    8: ("G005_STATION_BOUNDARY_BORDER", "NODE_BORDER", 41),
    9: ("G006_MAIN_ARROW_1_SHAFT", "LINE_ARROW", 43),
    10: ("G007_MAIN_ARROW_1_HEAD", "ARROWHEAD", 43),
    11: ("G008_MAIN_ARROW_2_SHAFT", "LINE_ARROW", 44),
    12: ("G009_MAIN_ARROW_2_HEAD", "ARROWHEAD", 44),
    13: ("G010_MAIN_ARROW_3_SHAFT", "LINE_ARROW", 45),
    14: ("G011_MAIN_ARROW_3_HEAD", "ARROWHEAD", 45),
    15: ("G012_MAIN_ARROW_4_SHAFT", "LINE_ARROW", 46),
    16: ("G013_MAIN_ARROW_4_HEAD", "ARROWHEAD", 46),
    # Each badge is emitted as one PDF `fs` path, but that path has two
    # semantically distinct final-visible constituents: opaque dark fill and
    # the white vector stroke.  The fill is deliberately a background object;
    # it must never be used for the digit-to-border clearance gate.
    17: ("G014_BADGE_1_FILL", "OPAQUE_NODE_FILL", 47),
    18: ("G015_BADGE_2_FILL", "OPAQUE_NODE_FILL", 47),
    19: ("G016_BADGE_3_FILL", "OPAQUE_NODE_FILL", 47),
    20: ("G017_BADGE_4_FILL", "OPAQUE_NODE_FILL", 47),
    21: ("G018_BADGE_5_FILL", "OPAQUE_NODE_FILL", 47),
    22: ("G019_FEEDBACK_SHAFT", "LINE_ARROW", 50),
    23: ("G020_FEEDBACK_HEAD", "ARROWHEAD", 50),
    24: ("G021_FEEDBACK_OPAQUE_LABEL_BACKGROUND", "OPAQUE_BACKGROUND", 52),
    25: ("G022_ROUTE_SUPERVISED_BORDER", "NODE_BORDER", 57),
    26: ("G023_ROUTE_UNSUPERVISED_BORDER", "NODE_BORDER", 59),
    27: ("G024_ENGINE_POOL_BORDER", "PANEL_BORDER", 62),
    28: ("G025_CHIP_LINALG_BORDER", "NODE_BORDER", 65),
    29: ("G026_CHIP_OPTIM_BORDER", "NODE_BORDER", 66),
    30: ("G027_CHIP_PROB_BORDER", "NODE_BORDER", 67),
    31: ("G028_CHIP_INFER_BORDER", "NODE_BORDER", 68),
    32: ("G029_VALIDATION_BORDER", "NODE_BORDER", 70),
    33: ("G030_REPORT_OUTER_BORDER", "DOUBLE_NODE_BORDER", 72),
    34: ("G031_REPORT_WHITE_SEPARATOR", "OPAQUE_WHITE_SEPARATOR", 72),
    35: ("G032_SUPERVISED_ARROW_SHAFT", "LINE_ARROW", 76),
    36: ("G033_SUPERVISED_ARROW_HEAD", "ARROWHEAD", 76),
    37: ("G034_UNSUPERVISED_ARROW_SHAFT", "LINE_ARROW", 77),
    38: ("G035_UNSUPERVISED_ARROW_HEAD", "ARROWHEAD", 77),
    39: ("G036_POOL_TO_VALIDATION_SHAFT", "LINE_ARROW", 78),
    40: ("G037_POOL_TO_VALIDATION_HEAD", "ARROWHEAD", 78),
    41: ("G038_VALIDATION_TO_REPORT_SHAFT", "LINE_ARROW", 79),
    42: ("G039_VALIDATION_TO_REPORT_HEAD", "ARROWHEAD", 79),
}

# Companion stroke objects for the five `fs` badge paths above.  This is an
# intentional one-PDF-path-to-two-semantic-objects mapping, recorded in both
# directions in the drawing census and object inventory.
BADGE_BORDER_DEFS = {
    17: ("G014_BADGE_1_BORDER", "NODE_BORDER", 47),
    18: ("G015_BADGE_2_BORDER", "NODE_BORDER", 47),
    19: ("G016_BADGE_3_BORDER", "NODE_BORDER", 47),
    20: ("G017_BADGE_4_BORDER", "NODE_BORDER", 47),
    21: ("G018_BADGE_5_BORDER", "NODE_BORDER", 47),
}

# Intended final-visible connections. The whitelist is deliberately pair-level,
# never class-wide: every contact remains in the unabridged pair table.
INTENTIONAL = {
    # Each of the following is a separately inspected source-anchor relation.
    # They are intentionally listed pair-by-pair rather than inferred from a
    # role or geometry class; see reviewer_pair_manual_ledger.csv.
    frozenset(("G001_STATION_PROBLEM_BORDER", "G006_MAIN_ARROW_1_SHAFT")): "source line 43: main line exits only problem.east toward model.west",
    frozenset(("G001_STATION_PROBLEM_BORDER", "G014_BADGE_1_BORDER")): "source lines 47-49: badge 1 is intentionally placed at problem.north west",
    frozenset(("G002_STATION_MODEL_BORDER", "G008_MAIN_ARROW_2_SHAFT")): "source line 44: main line exits only model.east toward compute.west",
    frozenset(("G002_STATION_MODEL_BORDER", "G015_BADGE_2_BORDER")): "source lines 47-49: badge 2 is intentionally placed at model.north west",
    frozenset(("G003_STATION_COMPUTE_BORDER", "G010_MAIN_ARROW_3_SHAFT")): "source line 45: main line exits only compute.east toward evidence.west",
    frozenset(("G003_STATION_COMPUTE_BORDER", "G016_BADGE_3_BORDER")): "source lines 47-49: badge 3 is intentionally placed at compute.north west",
    frozenset(("G004_STATION_EVIDENCE_BORDER", "G012_MAIN_ARROW_4_SHAFT")): "source line 46: main line exits only evidence.east toward boundary.west",
    frozenset(("G004_STATION_EVIDENCE_BORDER", "G017_BADGE_4_BORDER")): "source lines 47-49: badge 4 is intentionally placed at evidence.north west",
    frozenset(("G005_STATION_BOUNDARY_BORDER", "G018_BADGE_5_BORDER")): "source lines 47-49: badge 5 is intentionally placed at boundary.north west",
    frozenset(("G005_STATION_BOUNDARY_BORDER", "G019_FEEDBACK_SHAFT")): "source lines 50-53: feedback route exits only boundary.north",
    frozenset(("G022_ROUTE_SUPERVISED_BORDER", "G032_SUPERVISED_ARROW_SHAFT")): "source line 76: supervised route exits only supervised.east",
    frozenset(("G023_ROUTE_UNSUPERVISED_BORDER", "G034_UNSUPERVISED_ARROW_SHAFT")): "source line 77: unsupervised route exits only unsupervised.east",
    frozenset(("G024_ENGINE_POOL_BORDER", "G036_POOL_TO_VALIDATION_SHAFT")): "source line 78: main line exits only pool.east toward validation.west",
    frozenset(("G029_VALIDATION_BORDER", "G038_VALIDATION_TO_REPORT_SHAFT")): "source line 79: main line exits only validation.east toward report.west",
    frozenset(("G006_MAIN_ARROW_1_SHAFT", "G007_MAIN_ARROW_1_HEAD")): "one TikZ main-line arrow: shaft to its arrowhead",
    frozenset(("G008_MAIN_ARROW_2_SHAFT", "G009_MAIN_ARROW_2_HEAD")): "one TikZ main-line arrow: shaft to its arrowhead",
    frozenset(("G010_MAIN_ARROW_3_SHAFT", "G011_MAIN_ARROW_3_HEAD")): "one TikZ main-line arrow: shaft to its arrowhead",
    frozenset(("G012_MAIN_ARROW_4_SHAFT", "G013_MAIN_ARROW_4_HEAD")): "one TikZ main-line arrow: shaft to its arrowhead",
    frozenset(("G019_FEEDBACK_SHAFT", "G020_FEEDBACK_HEAD")): "one TikZ feedback arrow: dashed shaft to its arrowhead",
    frozenset(("G032_SUPERVISED_ARROW_SHAFT", "G033_SUPERVISED_ARROW_HEAD")): "one TikZ supervised-route arrow: shaft to its arrowhead",
    frozenset(("G034_UNSUPERVISED_ARROW_SHAFT", "G035_UNSUPERVISED_ARROW_HEAD")): "one TikZ unsupervised-route arrow: shaft to its arrowhead",
    frozenset(("G036_POOL_TO_VALIDATION_SHAFT", "G037_POOL_TO_VALIDATION_HEAD")): "one TikZ output arrow: shaft to its arrowhead",
    frozenset(("G038_VALIDATION_TO_REPORT_SHAFT", "G039_VALIDATION_TO_REPORT_HEAD")): "one TikZ output arrow: shaft to its arrowhead",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")


def to_rgb(color: Any) -> tuple[int, int, int]:
    if color is None:
        return (255, 255, 255)
    if isinstance(color, int):
        return ((color >> 16) & 255, (color >> 8) & 255, color & 255)
    if isinstance(color, (list, tuple)) and len(color) >= 3:
        if max(color[:3]) <= 1.001:
            return tuple(int(round(255 * x)) for x in color[:3])
        return tuple(int(round(x)) for x in color[:3])
    raise TypeError(f"unexpected color {color!r}")


def pt_to_px(box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (math.floor(x0 * sx), math.floor(y0 * sy), math.ceil(x1 * sx), math.ceil(y1 * sy))


def bbox_of_coords(coords: np.ndarray) -> tuple[int, int, int, int]:
    if len(coords) == 0:
        return (0, 0, 0, 0)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)
    return (int(x0), int(y0), int(x1) + 1, int(y1) + 1)


def classify_char(c: str) -> tuple[str, int | None]:
    low = set(",.;:，。；：、…")
    if c in low:
        return "LOW_PROFILE_PUNCTUATION", None
    if "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf":
        return "CJK", 30
    if c.isdigit():
        return "DIGIT", 24
    if c.isascii() and c.isalpha() and c.isupper():
        return "LATIN_CAPITAL", 24
    if c.isascii() and c.isalpha() and c.islower():
        return "LATIN_LOWER", 17
    if c in "()[]{}（）【】":
        return "FULL_HEIGHT_SYMBOL", 22
    if c in "+-=<>→←↦/／|":
        return "BASE_MATH_OR_SYMBOL", 22
    # Full-width non-low-profile marks have an upright/full-height contour.
    if ord(c) >= 0xFF00:
        return "CJK_FULLWIDTH", 30
    return "BASE_MATH_OR_SYMBOL", 22


def local_mask(image: np.ndarray, rect: tuple[int, int, int, int]) -> tuple[np.ndarray, tuple[int, int, int], np.ndarray]:
    """Return a non-dilated raw foreground mask using the local modal RGB bg."""
    x0, y0, x1, y1 = rect
    region = image[y0:y1, x0:x1, :3]
    flat = region.reshape(-1, 3)
    # A node fill or the page itself overwhelmingly dominates a glyph bbox.
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    bg = tuple(int(v) for v in colors[counts.argmax()])
    delta = np.abs(region.astype(np.int16) - np.asarray(bg, dtype=np.int16))
    mask = np.max(delta, axis=2) >= 20
    return mask, bg, region


def color_mask(
    image: np.ndarray,
    rect: tuple[int, int, int, int],
    target: tuple[int, int, int],
    backgrounds: list[tuple[int, int, int]],
    edge_band: bool = False,
    ellipse_band: bool = False,
    band: int = 5,
) -> np.ndarray:
    """Final-visible vector stroke/fill mask constrained by its path geometry.

    The color-direction calculation accepts native antialias pixels whenever
    their contrast to a permitted local background is at least 20/255.
    """
    x0, y0, x1, y1 = rect
    rgb = image[y0:y1, x0:x1, :3].astype(np.float32)
    target_a = np.asarray(target, dtype=np.float32)
    out = np.zeros(rgb.shape[:2], dtype=bool)
    for bg in backgrounds:
        bg_a = np.asarray(bg, dtype=np.float32)
        direction = target_a - bg_a
        denom = float(np.dot(direction, direction))
        if denom <= 0:
            continue
        delta = rgb - bg_a
        alpha = np.sum(delta * direction, axis=2) / denom
        residual = np.linalg.norm(delta - alpha[..., None] * direction, axis=2)
        contrast = np.max(np.abs(delta), axis=2)
        # A colour may be antialiased, but it still has to follow the exact
        # source-colour / actual-background direction.  The former 28-unit
        # residual admitted pale text and unrelated blue borders into an
        # orange feedback-path mask.  Eight RGB units accommodates Poppler's
        # native antialiasing while retaining colour ownership.
        out |= (alpha >= 0.02) & (alpha <= 1.2) & (residual <= 8.0) & (contrast >= 20.0)
    h, w = out.shape
    if edge_band:
        yy, xx = np.ogrid[:h, :w]
        # ogrid produces complementary (1,w)/(h,1) arrays; explicitly
        # broadcast them before reduction so rectangular drawing boxes work.
        xx_b, yy_b = np.broadcast_arrays(xx, yy)
        geom = np.minimum.reduce((xx_b, yy_b, w - 1 - xx_b, h - 1 - yy_b)) <= band
        out &= geom
    if ellipse_band:
        yy, xx = np.ogrid[:h, :w]
        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        rx, ry = max(1.0, (w - 1) / 2.0), max(1.0, (h - 1) / 2.0)
        r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        out &= (r >= 1.0 - (band / max(1, min(rx, ry)))) & (r <= 1.05)
    return out


def point_px(point: Any, sx: float, sy: float) -> np.ndarray:
    return np.asarray((float(point.x) * sx, float(point.y) * sy), dtype=np.float64)


def drawing_segments(drawing: dict[str, Any], sx: float, sy: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """Approximate only the PDF path geometry, never a surrounding bbox."""
    segments: list[tuple[np.ndarray, np.ndarray]] = []
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            segments.append((point_px(item[1], sx, sy), point_px(item[2], sx, sy)))
        elif op == "c":
            p0, p1, p2, p3 = (point_px(p, sx, sy) for p in item[1:5])
            estimate = float(np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1) + np.linalg.norm(p3 - p2))
            n = max(8, int(math.ceil(estimate / 0.50)))
            ts = np.linspace(0.0, 1.0, n + 1)
            curve = np.asarray([
                ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * (t ** 2) * p2 + (t ** 3) * p3
                for t in ts
            ])
            segments.extend((curve[i], curve[i + 1]) for i in range(len(curve) - 1))
        elif op == "re":
            r = item[1]
            p = [
                np.asarray((float(r.x0) * sx, float(r.y0) * sy)),
                np.asarray((float(r.x1) * sx, float(r.y0) * sy)),
                np.asarray((float(r.x1) * sx, float(r.y1) * sy)),
                np.asarray((float(r.x0) * sx, float(r.y1) * sy)),
            ]
            segments.extend((p[i], p[(i + 1) % 4]) for i in range(4))
    return segments


def restrict_to_stroke_path(
    candidate: np.ndarray,
    rect: tuple[int, int, int, int],
    drawing: dict[str, Any],
    sx: float,
    sy: float,
    antialias_allowance_px: float = 1.75,
) -> np.ndarray:
    """Keep existing native foreground pixels only when close to its own path.

    This is a selection stencil based on the PDF path; it never dilates or
    paints pixels into a mask.  It is essential for long arrows sharing a
    colour with labels or borders.
    """
    ys, xs = np.where(candidate)
    if len(xs) == 0:
        return candidate
    segs = drawing_segments(drawing, sx, sy)
    if not segs:
        return np.zeros_like(candidate)
    pts = np.column_stack((xs + rect[0], ys + rect[1])).astype(np.float64)
    min_d2 = np.full(len(pts), np.inf, dtype=np.float64)
    for a, b in segs:
        ab = b - a
        denom = float(np.dot(ab, ab))
        if denom <= 1e-12:
            d2 = np.sum((pts - a) ** 2, axis=1)
        else:
            t = np.clip(np.sum((pts - a) * ab, axis=1) / denom, 0.0, 1.0)
            nearest = a + t[:, None] * ab
            d2 = np.sum((pts - nearest) ** 2, axis=1)
        min_d2 = np.minimum(min_d2, d2)
    # Native stroke half-width plus antialias support; this constrains the
    # selector but cannot manufacture a foreground pixel.
    radius = float(drawing.get("width") or 0.8) * (sx + sy) / 4.0 + antialias_allowance_px
    keep = min_d2 <= radius * radius
    out = np.zeros_like(candidate)
    out[ys[keep], xs[keep]] = True
    return out


def arrowhead_polygon_mask(
    candidate: np.ndarray,
    rect: tuple[int, int, int, int],
    drawing: dict[str, Any],
    sx: float,
    sy: float,
) -> np.ndarray:
    """Select a filled arrowhead by its closed PDF polygon, not its bbox."""
    vertices: list[tuple[float, float]] = []
    for item in drawing["items"]:
        if item[0] == "l":
            for point in item[1:3]:
                p = point_px(point, sx, sy)
                q = (float(p[0] - rect[0]), float(p[1] - rect[1]))
                if not vertices or q != vertices[-1]:
                    vertices.append(q)
    if len(vertices) < 3:
        return restrict_to_stroke_path(candidate, rect, drawing, sx, sy)
    geom = Image.new("L", (candidate.shape[1], candidate.shape[0]), 0)
    draw = ImageDraw.Draw(geom)
    draw.polygon(vertices, fill=255)
    # The one native-pixel edge allowance is a geometry stencil for actual AA
    # edge pixels, not a dilation of the resulting foreground mask.
    draw.line(vertices + [vertices[0]], fill=255, width=3)
    return candidate & (np.asarray(geom) > 0)


def filled_path_geometry(
    shape: tuple[int, int],
    rect: tuple[int, int, int, int],
    drawing: dict[str, Any],
    sx: float,
    sy: float,
) -> np.ndarray:
    """Closed vector-fill stencil used only to select existing raw pixels."""
    points: list[tuple[float, float]] = []
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            segment = [point_px(item[1], sx, sy), point_px(item[2], sx, sy)]
        elif op == "c":
            p0, p1, p2, p3 = (point_px(p, sx, sy) for p in item[1:5])
            estimate = float(np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1) + np.linalg.norm(p3 - p2))
            n = max(12, int(math.ceil(estimate / 0.35)))
            ts = np.linspace(0.0, 1.0, n + 1)
            segment = [
                ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * (t ** 2) * p2 + (t ** 3) * p3
                for t in ts
            ]
        elif op == "re":
            r = item[1]
            segment = [
                np.asarray((float(r.x0) * sx, float(r.y0) * sy)),
                np.asarray((float(r.x1) * sx, float(r.y0) * sy)),
                np.asarray((float(r.x1) * sx, float(r.y1) * sy)),
                np.asarray((float(r.x0) * sx, float(r.y1) * sy)),
            ]
        else:
            continue
        for p in segment:
            q = (float(p[0] - rect[0]), float(p[1] - rect[1]))
            if not points or q != points[-1]:
                points.append(q)
    geom = Image.new("L", (shape[1], shape[0]), 0)
    if len(points) >= 3:
        ImageDraw.Draw(geom).polygon(points, fill=255)
    return np.asarray(geom) > 0


def badge_fill_mask(
    image: np.ndarray,
    rect: tuple[int, int, int, int],
    drawing: dict[str, Any],
    sx: float,
    sy: float,
) -> np.ndarray:
    """Final-visible opaque dark badge fill, excluding white stroke/digit."""
    fill = to_rgb(drawing.get("fill"))
    fill_candidate = color_mask(image, rect, fill, [(255, 255, 255)])
    return fill_candidate & filled_path_geometry(fill_candidate.shape, rect, drawing, sx, sy)


def badge_border_mask(
    image: np.ndarray,
    rect: tuple[int, int, int, int],
    drawing: dict[str, Any],
    sx: float,
    sy: float,
) -> np.ndarray:
    """Final-visible white badge stroke only, never page-white or fill pixels.

    The white rim is rendered on a white page.  Geometry alone would therefore
    also select indistinguishable exterior page-white pixels.  Intersecting
    with the closed fill interior retains only the visible inner stroke band;
    the result is still a selection from native pixels, never a drawn/dilated
    substitute mask.  The central white numeral is outside the stroke stencil.
    """
    fill = to_rgb(drawing.get("fill"))
    stroke = to_rgb(drawing.get("color"))
    stroke_candidate = color_mask(image, rect, stroke, [fill])
    fill_interior = filled_path_geometry(stroke_candidate.shape, rect, drawing, sx, sy)
    stroke_mask = restrict_to_stroke_path(stroke_candidate, rect, drawing, sx, sy)
    return stroke_mask & fill_interior


def mask_to_coords(mask: np.ndarray, rect: tuple[int, int, int, int]) -> np.ndarray:
    y, x = np.where(mask)
    return np.column_stack((y + rect[1], x + rect[0])).astype(np.int32)


def write_mask_png(path: Path, coords: np.ndarray, bbox: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = bbox
    canvas = np.zeros((max(1, y1 - y0), max(1, x1 - x0)), dtype=np.uint8)
    if len(coords):
        canvas[coords[:, 0] - y0, coords[:, 1] - x0] = 255
    Image.fromarray(canvas, mode="L").save(path)


def make_card(
    rgb: np.ndarray,
    mask_coords: np.ndarray,
    bbox: tuple[int, int, int, int],
    label: str,
    out_path: Path,
    scale: int = 8,
) -> None:
    x0, y0, x1, y1 = bbox
    pad = 3
    x0p, y0p = max(0, x0 - pad), max(0, y0 - pad)
    x1p, y1p = min(rgb.shape[1], x1 + pad), min(rgb.shape[0], y1 + pad)
    original = Image.fromarray(rgb[y0p:y1p, x0p:x1p, :3], mode="RGB")
    overlay_a = np.asarray(original).copy()
    local = np.zeros(overlay_a.shape[:2], dtype=bool)
    if len(mask_coords):
        local[mask_coords[:, 0] - y0p, mask_coords[:, 1] - x0p] = True
    overlay_a[local] = (255, 0, 0)
    overlay = Image.fromarray(overlay_a, mode="RGB")
    mono = np.zeros_like(overlay_a)
    mono[local] = (255, 0, 0)
    only = Image.fromarray(mono, mode="RGB")
    pieces = [im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST) for im in (original, overlay, only)]
    header = 22
    canvas = Image.new("RGB", (sum(im.width for im in pieces) + 4 * 2, max(im.height for im in pieces) + header), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((2, 2), label, fill="black")
    xpos = 2
    for part in pieces:
        canvas.paste(part, (xpos, header))
        xpos += part.width + 2
    canvas.save(out_path)


def nearest_pair(a: np.ndarray, b: np.ndarray) -> tuple[int, float, tuple[int, int], tuple[int, int]]:
    if len(a) == 0 or len(b) == 0:
        return 0, float("inf"), (-1, -1), (-1, -1)
    ea = a[:, 0].astype(np.int64) * 100000 + a[:, 1]
    eb = b[:, 0].astype(np.int64) * 100000 + b[:, 1]
    overlap = int(np.intersect1d(ea, eb, assume_unique=False).size)
    # cKDTree gives a true nearest foreground-pixel distance, not a bbox proxy.
    if len(a) <= len(b):
        tree = cKDTree(b[:, ::-1])  # x,y order for the tree
        dist, pos = tree.query(a[:, ::-1], k=1)
        i = int(np.argmin(dist))
        pa, pb = a[i], b[int(pos[i])]
    else:
        tree = cKDTree(a[:, ::-1])
        dist, pos = tree.query(b[:, ::-1], k=1)
        i = int(np.argmin(dist))
        pb, pa = b[i], a[int(pos[i])]
    return overlap, float(np.min(dist)), (int(pa[1]), int(pa[0])), (int(pb[1]), int(pb[0]))


def threshold_for(a: dict[str, Any], b: dict[str, Any]) -> int:
    if a["kind"] == b["kind"] == "TEXT":
        return 4
    if a["kind"] == "TEXT" or b["kind"] == "TEXT":
        graphic = b if b["kind"] == "GRAPHIC" else a
        return 5 if "BORDER" in graphic["role"] else 3
    # The strict task itself requires every non-contact object pair, including
    # graphic/graphic, to retain >=3 native pixels of clearance.
    return 3


def visual_card_for_pair(rgb: np.ndarray, a: dict[str, Any], b: dict[str, Any], out_dir: Path) -> list[str]:
    coords = np.vstack((a["coords"], b["coords"]))
    x0, y0, x1, y1 = bbox_of_coords(coords)
    pad = 8
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(rgb.shape[1], x1 + pad), min(rgb.shape[0], y1 + pad)
    native = Image.fromarray(rgb[y0:y1, x0:x1, :3], mode="RGB")
    native_name = f"{safe_name(a['id'])}__{safe_name(b['id'])}_native1x.png"
    native.save(out_dir / native_name)
    ma = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    mb = np.zeros_like(ma)
    ma[a["coords"][:, 0] - y0, a["coords"][:, 1] - x0] = 255
    mb[b["coords"][:, 0] - y0, b["coords"][:, 1] - x0] = 255
    Image.fromarray(ma, mode="L").save(out_dir / native_name.replace("native1x", "mask_a"))
    Image.fromarray(mb, mode="L").save(out_dir / native_name.replace("native1x", "mask_b"))
    ov = np.asarray(native).copy()
    ov[ma.astype(bool)] = (255, 0, 0)
    ov[mb.astype(bool)] = (0, 0, 255)
    both = ma.astype(bool) & mb.astype(bool)
    ov[both] = (255, 0, 255)
    overlay = Image.fromarray(ov, mode="RGB")
    overlay_name = native_name.replace("native1x", "overlay")
    overlay.save(out_dir / overlay_name)
    nearest = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
    nearest_name = native_name.replace("native1x", "8x_nearest")
    nearest.save(out_dir / nearest_name)
    return [native_name, native_name.replace("native1x", "mask_a"), native_name.replace("native1x", "mask_b"), overlay_name, nearest_name]


def fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    return keys


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    (OUT / "glyph_masks").mkdir(exist_ok=True)
    (OUT / "glyph_preseg_claim_masks").mkdir(exist_ok=True)
    (OUT / "glyph_cards_8x").mkdir(exist_ok=True)
    (OUT / "glyph_contact_sheets").mkdir(exist_ok=True)
    (OUT / "semantic_masks").mkdir(exist_ok=True)
    (OUT / "graphic_masks").mkdir(exist_ok=True)
    (OUT / "z_order_pre_occlusion_masks").mkdir(exist_ok=True)
    (OUT / "white_occlusion_masks").mkdir(exist_ok=True)
    (OUT / "opaque_fill_geometry_masks").mkdir(exist_ok=True)
    (OUT / "badge_component_evidence").mkdir(exist_ok=True)
    (OUT / "badge_padding_evidence").mkdir(exist_ok=True)
    (OUT / "critical_pair_cards").mkdir(exist_ok=True)
    (OUT / "low_profile_calibration").mkdir(exist_ok=True)

    document = fitz.open(PDF)
    page = document[PDF_PAGE - 1]
    page_rect = page.rect
    full_path = OUT / "full_page_native_300dpi-801.png"
    page_rgb = np.asarray(Image.open(full_path).convert("RGB"))
    height, width = page_rgb.shape[:2]
    sx, sy = width / page_rect.width, height / page_rect.height
    crop_x0, crop_y0, crop_x1, crop_y1 = CROP
    crop_rgb = page_rgb[crop_y0:crop_y1, crop_x0:crop_x1, :3]
    Image.fromarray(crop_rgb, mode="RGB").save(OUT / "figure_crop_300dpi.png")
    Image.fromarray(crop_rgb, mode="RGB").save(OUT / "standalone_300dpi.png")
    ImageOps.grayscale(Image.fromarray(crop_rgb, mode="RGB")).save(OUT / "grayscale_300dpi.png")
    Image.open(OUT / "full_page_200dpi-801.png").save(OUT / "full_page_200dpi.png")

    raw = page.get_text("rawdict")
    glyphs: list[dict[str, Any]] = []
    rawdict_rows: list[dict[str, Any]] = []
    rawdict_seq = 0
    group_map = {g.ident: g for g in GROUPS}

    def assign_group(cx: float, cy: float) -> Group:
        hits = [g for g in GROUPS if g.bbox[0] <= cx <= g.bbox[2] and g.bbox[1] <= cy <= g.bbox[3]]
        if len(hits) != 1:
            raise RuntimeError(f"glyph at ({cx:.2f},{cy:.2f}) maps to {len(hits)} semantic groups")
        return hits[0]

    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                font = span.get("font", "")
                size = float(span.get("size", 0))
                color = to_rgb(span.get("color"))
                flags = span.get("flags", "")
                for char in span["chars"]:
                    c = char["c"]
                    x0, y0, x1, y1 = char["bbox"]
                    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                    if not (FIGURE_PT[0] <= cx <= FIGURE_PT[2] and FIGURE_PT[1] <= cy <= FIGURE_PT[3]):
                        continue
                    rawdict_seq += 1
                    zero_width = (x1 - x0) <= 0.0 or (y1 - y0) <= 0.0
                    combining = bool(c and unicodedata.combining(c))
                    raw_record = {
                        "RAWDICT_SEQ": rawdict_seq,
                        "CHAR": c,
                        "UNICODE": "EMPTY" if not c else "+".join(f"U+{ord(q):04X}" for q in c),
                        "PDF_FONT": font,
                        "PDF_FONT_SIZE": f"{size:.6f}",
                        "PDF_COLOR_RGB": "/".join(map(str, color)),
                        "BBOX_PT": f"{x0:.6f},{y0:.6f},{x1:.6f},{y1:.6f}",
                        "WHITESPACE": bool(c and c.isspace()),
                        "COMBINING": combining,
                        "ZERO_WIDTH_OR_HEIGHT": zero_width,
                    }
                    if not c or c.isspace():
                        raw_record.update({"MAPPED_GLYPH_ID": "", "STATUS": "NONINK_WHITESPACE_OR_EMPTY"})
                        rawdict_rows.append(raw_record)
                        continue
                    if combining or zero_width:
                        raw_record.update({"MAPPED_GLYPH_ID": "", "STATUS": "FAIL_UNRESOLVED_COMBINING_OR_ZERO_WIDTH"})
                        rawdict_rows.append(raw_record)
                        continue
                    group = assign_group(cx, cy)
                    px_box = pt_to_px((x0, y0, x1, y1), sx, sy)
                    mask, bg, _region = local_mask(page_rgb, px_box)
                    coords = mask_to_coords(mask, px_box)
                    gid = f"C{len(glyphs)+1:04d}"
                    script, lower = classify_char(c)
                    raw_bbox = bbox_of_coords(coords)
                    h_ink = raw_bbox[3] - raw_bbox[1] if len(coords) else 0
                    w_ink = raw_bbox[2] - raw_bbox[0] if len(coords) else 0
                    effective = group.declared_pt
                    row = {
                        "GLYPH_ID": gid,
                        "RAWDICT_SEQ": rawdict_seq,
                        "ELEMENT_ID": group.ident,
                        "PANEL_ID": group.panel,
                        "ROLE": group.role,
                        "SOURCE_FILE": str(SOURCE),
                        "SOURCE_LINE": group.source_line,
                        "CHAR": c,
                        "UNICODE": f"U+{ord(c):04X}",
                        "SCRIPT_CLASS": script,
                        "DECLARED_PT": f"{group.declared_pt:.2f}",
                        "GRAPHICS_SCALE": "1.000000",
                        "EFFECTIVE_PT": f"{effective:.2f}",
                        "PDF_FONT": font,
                        "PDF_FONT_SIZE": f"{size:.6f}",
                        "PDF_COLOR_RGB": "/".join(map(str, color)),
                        "FONT_FLAGS": flags,
                        "BBOX_X0": px_box[0], "BBOX_Y0": px_box[1], "BBOX_X1": px_box[2], "BBOX_Y1": px_box[3],
                        "BBOX_RAW_WIDTH_PX": w_ink, "BBOX_RAW_HEIGHT_PX": h_ink,
                        "H_INK_PX": h_ink,
                        "RAW_MASK_AREA_PX": int(len(coords)),
                        "LOCAL_BACKGROUND_RGB": "/".join(map(str, bg)),
                        "THRESHOLD_CONTRAST": "20/255",
                        "LOWER_LIMIT_PX": "CALIBRATE" if lower is None else lower,
                        "FONT_PASS": effective >= 9.5,
                        "PIXEL_PASS_PRECAL": (len(coords) > 0 and (lower is None or h_ink >= lower)),
                        "SAFE_FILENAME": safe_name(gid),
                    }
                    glyphs.append({"row": row, "coords": coords, "px_box": px_box, "group": group, "font": font, "size": size, "color": color})
                    raw_record.update({"MAPPED_GLYPH_ID": gid, "ELEMENT_ID": group.ident, "STATUS": "MAPPED_VISIBLE_GLYPH"})
                    rawdict_rows.append(raw_record)

    if sum(r["STATUS"] == "MAPPED_VISIBLE_GLYPH" for r in rawdict_rows) != len(glyphs):
        raise RuntimeError("rawdict-to-glyph visible count does not reconcile")
    unresolved_rawdict = [r for r in rawdict_rows if r["STATUS"] == "FAIL_UNRESOLVED_COMBINING_OR_ZERO_WIDTH"]

    # Isolate each glyph from its neighbours.  Rawdict bboxes legitimately
    # share a one-pixel AA fringe in tightly spaced text.  Preserve a complete
    # pre-seg claim mask, then assign every contested *existing* native pixel
    # to exactly one rawdict glyph by normalized distance to that glyph's own
    # bbox centre.  This is a traceable PDF-glyph-level re-segmentation, not a
    # crop, dilation, or global automatic PASS.
    ownership: dict[tuple[int, int], list[int]] = defaultdict(list)
    for idx, item in enumerate(glyphs):
        for y, x in item["coords"]:
            ownership[(int(y), int(x))].append(idx)
    preseg_collisions = defaultdict(int)
    assigned: list[list[tuple[int, int]]] = [[] for _ in glyphs]
    for (y, x), owners in ownership.items():
        if len(owners) > 1:
            for idx in owners:
                preseg_collisions[idx] += 1
            def owner_score(idx: int) -> tuple[float, int]:
                x0, y0, x1, y1 = glyphs[idx]["px_box"]
                cx, cy = (x0 + x1 - 1) / 2.0, (y0 + y1 - 1) / 2.0
                scale_x = max(1.0, x1 - x0)
                scale_y = max(1.0, y1 - y0)
                return (((x - cx) / scale_x) ** 2 + ((y - cy) / scale_y) ** 2, idx)
            winner = min(owners, key=owner_score)
        else:
            winner = owners[0]
        assigned[winner].append((y, x))

    for idx, item in enumerate(glyphs):
        item["preseg_coords"] = item["coords"].copy()
        item["coords"] = np.asarray(assigned[idx], dtype=np.int32).reshape((-1, 2)) if assigned[idx] else np.empty((0, 2), dtype=np.int32)
        row = item["row"]
        final_bbox = bbox_of_coords(item["coords"])
        h_ink = final_bbox[3] - final_bbox[1] if len(item["coords"]) else 0
        w_ink = final_bbox[2] - final_bbox[0] if len(item["coords"]) else 0
        row["BBOX_RAW_WIDTH_PX"] = w_ink
        row["BBOX_RAW_HEIGHT_PX"] = h_ink
        row["H_INK_PX"] = h_ink
        row["RAW_MASK_AREA_PX"] = int(len(item["coords"]))
        lower = row["LOWER_LIMIT_PX"]
        row["PIXEL_PASS_PRECAL"] = len(item["coords"]) > 0 and (lower == "CALIBRATE" or h_ink >= int(lower))
        row["PRESEGMENT_CLAIM_COLLISION_PX"] = preseg_collisions[idx]
        row["RESEGMENTATION_METHOD"] = "rawdict-claim union; contested native pixels assigned once by normalized bbox-centre distance"

    glyph_rows: list[dict[str, Any]] = []
    filename_rows: list[dict[str, Any]] = []
    for idx, item in enumerate(glyphs):
        row = item["row"].copy()
        mask_name = f"glyph_masks/{row['SAFE_FILENAME']}.png"
        claim_name = f"glyph_preseg_claim_masks/{row['SAFE_FILENAME']}_preseg_claim.png"
        card_name = f"glyph_cards_8x/{row['SAFE_FILENAME']}_card_8x.png"
        write_mask_png(OUT / claim_name, item["preseg_coords"], item["px_box"])
        write_mask_png(OUT / mask_name, item["coords"], item["px_box"])
        make_card(page_rgb, item["coords"], item["px_box"], f"{row['GLYPH_ID']} {row['UNICODE']} ORIGINAL | TARGET | MASK", OUT / card_name)
        row["RAW_MASK_FILE"] = mask_name
        row["PRESEGMENT_CLAIM_MASK_FILE"] = claim_name
        row["CARD_8X_FILE"] = card_name
        row["FOREIGN_GLYPH_PIXEL_COUNT"] = 0
        row["MASK_PURITY_PASS_PREGRAPHIC"] = len(item["coords"]) > 0
        glyph_rows.append(row)
        filename_rows.append({"ID": row["GLYPH_ID"], "SAFE_FILENAME": row["SAFE_FILENAME"], "PATH": mask_name, "KIND": "GLYPH_MASK"})

    # Semantic text foreground masks are unions of their individually isolated
    # glyph masks. This preserves 100% glyph evidence while making pair gates
    # meaningful for independent semantic objects rather than adjacent letters.
    text_objects: list[dict[str, Any]] = []
    for group in GROUPS:
        members = [g for g in glyphs if g["group"].ident == group.ident]
        if not members:
            raise RuntimeError(f"semantic text element has no visible glyphs: {group.ident}")
        coords = np.vstack([m["coords"] for m in members])
        bbox = bbox_of_coords(coords)
        file_name = f"semantic_masks/{safe_name(group.ident)}.png"
        write_mask_png(OUT / file_name, coords, bbox)
        text_objects.append({"id": group.ident, "kind": "TEXT", "role": group.role, "panel": group.panel, "coords": coords, "bbox": bbox, "source": f"{SOURCE}:{group.source_line}", "mask_file": file_name, "background": False})
        filename_rows.append({"ID": group.ident, "SAFE_FILENAME": safe_name(group.ident), "PATH": file_name, "KIND": "SEMANTIC_TEXT_MASK"})

    drawings = page.get_drawings()
    # Bidirectional drawing/path census.  Do not assume a source-object list
    # is complete: begin with every emitted PDF drawing and require the figure
    # crop to contain exactly the named drawing indices.  The current source
    # contains no TeX math-rule constructs; nevertheless the explicit field
    # records that the 39 visible paths were checked for rawdict-external
    # overlines, fraction bars, radicals, hats, vectors, and cancellations.
    source_text = SOURCE.read_text(encoding="utf-8", errors="replace")
    math_rule_tokens = (r"\overline", r"\underline", r"\hat", r"\widehat", r"\vec", r"\sqrt", r"\frac", r"\cancel")
    declared_math_rule_tokens = [token for token in math_rule_tokens if token in source_text]
    all_drawing_path_rows: list[dict[str, Any]] = []
    figure_drawing_indices: list[int] = []
    for drawing_index, emitted in enumerate(drawings):
        rect_pt = emitted["rect"]
        in_figure = not (
            rect_pt.x1 < FIGURE_PT[0] or rect_pt.x0 > FIGURE_PT[2]
            or rect_pt.y1 < FIGURE_PT[1] or rect_pt.y0 > FIGURE_PT[3]
        )
        if in_figure:
            figure_drawing_indices.append(drawing_index)
        if drawing_index in DRAWING_NAMES:
            covered_id, covered_role, covered_line = DRAWING_NAMES[drawing_index]
            component_ids = [covered_id]
            component_roles = [covered_role]
            if drawing_index in BADGE_BORDER_DEFS:
                border_id, border_role, border_line = BADGE_BORDER_DEFS[drawing_index]
                component_ids.append(border_id)
                component_roles.append(border_role)
                if border_line != covered_line:
                    raise RuntimeError("badge fill/stroke source-line mapping diverged")
            coverage = "PASS_MAPPED_FIGURE_PATH"
        elif in_figure:
            covered_id, covered_role, covered_line = "", "", ""
            component_ids, component_roles = [], []
            coverage = "FAIL_UNMAPPED_FIGURE_PATH"
        else:
            covered_id, covered_role, covered_line = "", "", ""
            component_ids, component_roles = [], []
            coverage = "OUTSIDE_FIGURE_BODY"
        all_drawing_path_rows.append({
            "DRAWING_INDEX": drawing_index,
            "TYPE": emitted["type"],
            "RECT_PT": f"{rect_pt.x0:.6f},{rect_pt.y0:.6f},{rect_pt.x1:.6f},{rect_pt.y1:.6f}",
            "ITEM_COUNT": len(emitted["items"]),
            "STROKE_RGB": "/".join(map(str, to_rgb(emitted.get("color")))) if emitted.get("color") is not None else "NONE",
            "FILL_RGB": "/".join(map(str, to_rgb(emitted.get("fill")))) if emitted.get("fill") is not None else "NONE",
            "STROKE_WIDTH_PT": f"{float(emitted.get('width') or 0.0):.6f}",
            "INTERSECTS_FIGURE_BODY": in_figure,
            "COVERAGE_ID": ";".join(component_ids),
            "COVERAGE_ROLE": ";".join(component_roles),
            "PATH_TO_OBJECT_COUNT": len(component_ids),
            "SOURCE_LINE": covered_line,
            "MATH_RULE_CLASS": "NONE_TIKZ_NONFORMULA_PATH" if in_figure else "OUTSIDE_FIGURE",
            "COVERAGE_STATUS": coverage,
        })
    if figure_drawing_indices != list(range(4, 43)):
        raise RuntimeError(f"figure drawing census mismatch: {figure_drawing_indices}")
    if declared_math_rule_tokens:
        raise RuntimeError(f"source declares math-rule tokens requiring additional objects: {declared_math_rule_tokens}")
    if sorted(DRAWING_NAMES) != list(range(4, 43)):
        raise RuntimeError("drawing inventory definition is not contiguous")
    graphics: list[dict[str, Any]] = []
    graphic_rows: list[dict[str, Any]] = []
    badge_component_rows: list[dict[str, Any]] = []
    badge_text_owner = {
        17: "T008_BADGE_1", 18: "T009_BADGE_2", 19: "T010_BADGE_3",
        20: "T011_BADGE_4", 21: "T012_BADGE_5",
    }

    def append_graphic_component(
        *,
        ident: str,
        role: str,
        source_line: int,
        idx: int,
        drawing: dict[str, Any],
        rect: tuple[int, int, int, int],
        coords: np.ndarray,
        background: bool,
        path_component: str,
        z_order_note: str = "NONE",
        pre_occlusion_coords: np.ndarray | None = None,
        opaque_geometry_coords: np.ndarray | None = None,
        opaque_geometry_file: str = "",
        empty_allowed: bool = False,
    ) -> dict[str, Any]:
        """Persist one semantic object with an auditable PDF-path mapping."""
        if pre_occlusion_coords is None:
            pre_occlusion_coords = coords.copy()
        if opaque_geometry_coords is None:
            opaque_geometry_coords = np.empty((0, 2), dtype=np.int32)
        z_order_removed = max(0, int(len(pre_occlusion_coords) - len(coords)))
        bbox = bbox_of_coords(coords) if len(coords) else rect
        # White opaque fills have no dark final-foreground pixels.  Preserve
        # their own native-coordinate bounding box so downstream review cards
        # can show the actual PDF path rather than stretching it to a parent
        # drawing rectangle.
        opaque_geometry_bbox = bbox_of_coords(opaque_geometry_coords) if len(opaque_geometry_coords) else (0, 0, 0, 0)
        mask_file = f"graphic_masks/{safe_name(ident)}.png"
        pre_mask_file = ""
        if z_order_removed:
            pre_bbox = bbox_of_coords(pre_occlusion_coords)
            pre_mask_file = f"z_order_pre_occlusion_masks/{safe_name(ident)}_pre_occlusion.png"
            write_mask_png(OUT / pre_mask_file, pre_occlusion_coords, pre_bbox)
        if len(coords):
            write_mask_png(OUT / mask_file, coords, bbox)
        else:
            Image.new("L", (max(1, rect[2] - rect[0]), max(1, rect[3] - rect[1])), 0).save(OUT / mask_file)
        obj = {
            "id": ident,
            "kind": "GRAPHIC",
            "role": role,
            "panel": "A" if idx <= 24 else "B",
            "coords": coords,
            "bbox": bbox,
            "source": f"{SOURCE}:{source_line}; PDF drawing index {idx}; path component {path_component}",
            "mask_file": mask_file,
            "background": background,
            "drawing_index": idx,
            "path_component": path_component,
            "paint_rank": idx * 10 + (1 if path_component == "STROKE" else 0),
            "pre_occlusion_mask_file": pre_mask_file,
            "opaque_geometry_coords": opaque_geometry_coords,
            "opaque_geometry_mask_file": opaque_geometry_file,
            "opaque_geometry_bbox": opaque_geometry_bbox,
            "z_order_removed_pixels": z_order_removed,
            "z_order_note": z_order_note,
            "empty_allowed": empty_allowed,
        }
        graphics.append(obj)
        graphic_rows.append({
            "OBJECT_ID": ident,
            "DRAWING_INDEX": idx,
            "TYPE": drawing["type"],
            "PDF_PATH_COMPONENT": path_component,
            "ROLE": role,
            "SOURCE_LINE": source_line,
            "BBOX_X0": rect[0], "BBOX_Y0": rect[1], "BBOX_X1": rect[2], "BBOX_Y1": rect[3],
            "RAW_FOREGROUND_PIXELS": int(len(coords)),
            "BACKGROUND_ONLY": background,
            "MASK_FILE": mask_file,
            "PRE_OCCLUSION_MASK_FILE": pre_mask_file,
            "OPAQUE_GEOMETRY_MASK_FILE": opaque_geometry_file,
            "OPAQUE_GEOMETRY_BBOX_X0": opaque_geometry_bbox[0],
            "OPAQUE_GEOMETRY_BBOX_Y0": opaque_geometry_bbox[1],
            "OPAQUE_GEOMETRY_BBOX_X1": opaque_geometry_bbox[2],
            "OPAQUE_GEOMETRY_BBOX_Y1": opaque_geometry_bbox[3],
            "Z_ORDER_TEXT_OCCLUSION_REMOVED_PIXELS": z_order_removed,
            "Z_ORDER_NOTE": z_order_note,
            "MASK_NONEMPTY_PASS": "N/A_OPAQUE_WHITE_OCCLUSION" if empty_allowed else bool(len(coords)),
        })
        filename_rows.append({"ID": ident, "SAFE_FILENAME": safe_name(ident), "PATH": mask_file, "KIND": "GRAPHIC_MASK"})
        return obj

    for idx in range(4, 43):
        drawing = drawings[idx]
        ident, role, source_line = DRAWING_NAMES[idx]
        x0, y0, x1, y1 = pt_to_px(tuple(drawing["rect"]), sx, sy)
        # Retain a one-pixel box around vector rects, without changing the
        # native source image or doing any morphological dilation.
        rect = (max(0, x0 - 1), max(0, y0 - 1), min(width, x1 + 1), min(height, y1 + 1))

        if idx == 34:
            # TikZ double emits a dark fs stroke (index 33), then a white
            # overprint on the same path (index 34).  Index 34 is not a
            # second dark foreground border: treating the preceding blue
            # substrate as its final mask manufactured the old 819px
            # magenta overlap.  Preserve its true opaque-white geometry
            # separately, while the final dark frame mask belongs solely to
            # index 33 and is selected from actual final dark pixels.
            # Use actual final white pixels constrained to the narrow center
            # band of this own PDF path.  A full geometric stencil would mix
            # page-white outside the dark double stroke into the separator.
            dark_underlay = to_rgb(drawings[33].get("color"))
            white_candidate = color_mask(page_rgb, rect, to_rgb(drawing.get("color")), [dark_underlay])
            geometry_mask = restrict_to_stroke_path(
                white_candidate, rect, drawing, sx, sy, antialias_allowance_px=0.75
            )
            opaque_geometry_coords = mask_to_coords(geometry_mask, rect)
            opaque_geometry_file = f"white_occlusion_masks/{safe_name(ident)}_opaque_geometry.png"
            write_mask_png(OUT / opaque_geometry_file, opaque_geometry_coords, bbox_of_coords(opaque_geometry_coords))
            append_graphic_component(
                ident=ident, role=role, source_line=source_line, idx=idx, drawing=drawing, rect=rect,
                coords=np.empty((0, 2), dtype=np.int32), background=True, path_component="OPAQUE_WHITE_SEPARATOR",
                z_order_note="PDF drawing 34 is a white overprint on drawing 33 (TikZ double separator); actual final white raw mask is selected only within its narrow own path band and stored separately; final dark-foreground mask intentionally empty.",
                opaque_geometry_coords=opaque_geometry_coords, opaque_geometry_file=opaque_geometry_file, empty_allowed=True,
            )
            continue

        if idx in badge_text_owner:
            # A badge is one PDF `fs` path with a dark opaque fill and a white
            # stroke.  Split it before any pair calculation.  Only the
            # stroke becomes NODE_BORDER; the fill is explicitly background.
            fill_geometry = filled_path_geometry((rect[3] - rect[1], rect[2] - rect[0]), rect, drawing, sx, sy)
            stroke_geometry = restrict_to_stroke_path(np.ones_like(fill_geometry, dtype=bool), rect, drawing, sx, sy)
            opaque_geometry_coords = mask_to_coords(fill_geometry | stroke_geometry, rect)
            opaque_geometry_file = f"opaque_fill_geometry_masks/{safe_name(ident)}_opaque_fill_stroke_geometry.png"
            write_mask_png(OUT / opaque_geometry_file, opaque_geometry_coords, bbox_of_coords(opaque_geometry_coords))
            fill_pre = mask_to_coords(badge_fill_mask(page_rgb, rect, drawing, sx, sy), rect)
            border_ident, border_role, border_line = BADGE_BORDER_DEFS[idx]
            border_pre = mask_to_coords(badge_border_mask(page_rgb, rect, drawing, sx, sy), rect)
            text_owner = next(obj for obj in text_objects if obj["id"] == badge_text_owner[idx])
            covered = set((int(y), int(x)) for y, x in text_owner["coords"])
            keep = np.asarray([(int(y), int(x)) not in covered for y, x in border_pre], dtype=bool)
            border_coords = border_pre[keep]
            # `fs` paints fill then stroke.  At the antialiased boundary a
            # permissive colour-direction candidate may contain a physical
            # pixel in both preliminary selections.  Assign every such pixel
            # uniquely to the later final-visible STROKE, never to the fill.
            # This is a traceable paint-order allocation, not a dilation or a
            # fabricated replacement pixel.
            border_owned = set((int(y), int(x)) for y, x in border_coords)
            fill_keep = np.asarray([(int(y), int(x)) not in border_owned for y, x in fill_pre], dtype=bool)
            fill_coords = fill_pre[fill_keep]
            fill_removed_by_stroke = int(np.count_nonzero(~fill_keep))
            fill_obj = append_graphic_component(
                ident=ident, role=role, source_line=source_line, idx=idx, drawing=drawing, rect=rect,
                coords=fill_coords, background=True, path_component="FILL",
                z_order_note=(
                    "PDF fs fill phase; opaque dark badge interior. Final STROKE owns "
                    f"{fill_removed_by_stroke} antialiased candidate pixel(s) by source paint order. "
                    "Exempt from foreground clearance; retained as an explicit object and raw mask."
                ),
                opaque_geometry_coords=opaque_geometry_coords, opaque_geometry_file=opaque_geometry_file,
            )
            border_obj = append_graphic_component(
                ident=border_ident, role=border_role, source_line=border_line, idx=idx, drawing=drawing, rect=rect,
                coords=border_coords, background=False, path_component="STROKE",
                z_order_note=(
                    f"PDF fs stroke phase, selected as native white pixels on its own path ∩ closed fill interior; "
                    f"final {badge_text_owner[idx]} mask excluded only if it intersected the vector-path selector."
                ),
                pre_occlusion_coords=border_pre,
            )
            badge_component_rows.append({
                "DRAWING_INDEX": idx,
                "PDF_TYPE": drawing["type"],
                "TEXT_OBJECT": badge_text_owner[idx],
                "FILL_OBJECT": fill_obj["id"],
                "BORDER_OBJECT": border_obj["id"],
                "FILL_PRE_STROKE_CANDIDATE_PIXELS": len(fill_pre),
                "FILL_STROKE_OWNERSHIP_REMOVED_PIXELS": fill_removed_by_stroke,
                "FILL_PIXELS": len(fill_obj["coords"]),
                "OPAQUE_FILL_STROKE_GEOMETRY_PIXELS": len(opaque_geometry_coords),
                "OPAQUE_FILL_STROKE_GEOMETRY_MASK": opaque_geometry_file,
                "BORDER_PIXELS": len(border_obj["coords"]),
                "BORDER_PRE_FINAL_TEXT_SELECTOR_PIXELS": len(border_pre),
                "BORDER_TEXT_ZORDER_REMOVED_PIXELS": len(border_pre) - len(border_coords),
                "PATH_TO_OBJECT_MAPPING": "one PDF fs drawing -> FILL opaque background + STROKE final-visible border",
            })
            continue

        bg_only = role == "OPAQUE_BACKGROUND"
        if bg_only:
            coords = np.empty((0, 2), dtype=np.int32)
            geometry_mask = filled_path_geometry((rect[3] - rect[1], rect[2] - rect[0]), rect, drawing, sx, sy)
            opaque_geometry_coords = mask_to_coords(geometry_mask, rect)
            opaque_geometry_file = f"white_occlusion_masks/{safe_name(ident)}_opaque_geometry.png"
            write_mask_png(OUT / opaque_geometry_file, opaque_geometry_coords, bbox_of_coords(opaque_geometry_coords))
            append_graphic_component(
                ident=ident, role=role, source_line=source_line, idx=idx, drawing=drawing, rect=rect,
                coords=coords, background=True, path_component="OPAQUE_BACKGROUND",
                z_order_note="Declared opaque white feedback-label background; its exact PDF fill geometry is retained separately; no independent final dark foreground mask.",
                opaque_geometry_coords=opaque_geometry_coords, opaque_geometry_file=opaque_geometry_file, empty_allowed=True,
            )
            continue
        if role == "ARROWHEAD":
            fill = to_rgb(drawing.get("fill"))
            mask = color_mask(page_rgb, rect, fill, [(255, 255, 255)])
            mask = arrowhead_polygon_mask(mask, rect, drawing, sx, sy)
            coords = mask_to_coords(mask, rect)
        else:
            color = to_rgb(drawing.get("color"))
            fill = to_rgb(drawing.get("fill")) if drawing.get("fill") is not None else (255, 255, 255)
            mask = color_mask(page_rgb, rect, color, [(255, 255, 255), fill])
            mask = restrict_to_stroke_path(mask, rect, drawing, sx, sy)
            coords = mask_to_coords(mask, rect)
        append_graphic_component(
            ident=ident, role=role, source_line=source_line, idx=idx, drawing=drawing, rect=rect,
            coords=coords, background=False, path_component="WHOLE_DRAWING",
        )

    # Resolve all later-paint ownership before pair measurement.  A pixel that
    # an opaque later PDF component owns cannot remain in an earlier object's
    # final-visible mask merely because both source paths use a similar colour.
    # This applies to explicit badge fills as well as normal arrow heads/shafts.
    # The ledger makes every removed set traceable rather than concealing it in
    # a colour selector.
    z_order_rows: list[dict[str, Any]] = []
    graphic_row_by_id = {row["OBJECT_ID"]: row for row in graphic_rows}
    ordered_graphics = sorted(graphics, key=lambda g: (g["paint_rank"], g["id"]))
    for later in ordered_graphics:
        later_opaque = later["opaque_geometry_coords"] if len(later["opaque_geometry_coords"]) else later["coords"]
        if len(later_opaque) == 0:
            continue
        later_keys = set((int(y), int(x)) for y, x in later_opaque)
        for earlier in ordered_graphics:
            if earlier["paint_rank"] >= later["paint_rank"] or len(earlier["coords"]) == 0:
                continue
            before = earlier["coords"]
            keep = np.asarray([(int(y), int(x)) not in later_keys for y, x in before], dtype=bool)
            removed = before[~keep]
            if len(removed) == 0:
                continue
            if not earlier["pre_occlusion_mask_file"]:
                pre_file = f"z_order_pre_occlusion_masks/{safe_name(earlier['id'])}_pre_occlusion.png"
                write_mask_png(OUT / pre_file, before, bbox_of_coords(before))
                earlier["pre_occlusion_mask_file"] = pre_file
            earlier["coords"] = before[keep]
            earlier["bbox"] = bbox_of_coords(earlier["coords"])
            earlier["z_order_removed_pixels"] += int(len(removed))
            prior_note = earlier["z_order_note"]
            allocation_note = f"later PDF component {later['id']} (drawing {later['drawing_index']}, {later['path_component']}) owns {len(removed)} final pixel(s)"
            earlier["z_order_note"] = allocation_note if prior_note == "NONE" else f"{prior_note}; {allocation_note}"
            write_mask_png(OUT / earlier["mask_file"], earlier["coords"], earlier["bbox"])
            table = graphic_row_by_id[earlier["id"]]
            table.update({
                "BBOX_X0": earlier["bbox"][0], "BBOX_Y0": earlier["bbox"][1],
                "BBOX_X1": earlier["bbox"][2], "BBOX_Y1": earlier["bbox"][3],
                "RAW_FOREGROUND_PIXELS": int(len(earlier["coords"])),
                "PRE_OCCLUSION_MASK_FILE": earlier["pre_occlusion_mask_file"],
                "Z_ORDER_TEXT_OCCLUSION_REMOVED_PIXELS": earlier["z_order_removed_pixels"],
                "Z_ORDER_NOTE": earlier["z_order_note"],
            })
            z_order_rows.append({
                "EARLIER_OBJECT": earlier["id"],
                "EARLIER_DRAWING_INDEX": earlier["drawing_index"],
                "LATER_OBJECT": later["id"],
                "LATER_DRAWING_INDEX": later["drawing_index"],
                "LATER_PATH_COMPONENT": later["path_component"],
                "REMOVED_FINAL_PIXEL_COUNT": int(len(removed)),
                "OWNERSHIP_METHOD": "PDF draw order; later opaque geometry/raw mask owns final pixels",
                "EARLIER_PRE_MASK": earlier["pre_occlusion_mask_file"],
                "EARLIER_FINAL_MASK": earlier["mask_file"],
                "LATER_OPAQUE_GEOMETRY_MASK": later["opaque_geometry_mask_file"],
            })

    all_objects = text_objects + graphics
    # Five badge PDF `fs` paths map two ways to FILL/BORDER semantic objects.
    # Produce direct requalification evidence before pair enumeration so the
    # old whole-disk "border" cards cannot be mistaken for this result.
    for badge_row in badge_component_rows:
        fill_obj = next(g for g in graphics if g["id"] == badge_row["FILL_OBJECT"])
        border_obj = next(g for g in graphics if g["id"] == badge_row["BORDER_OBJECT"])
        text_obj = next(t for t in text_objects if t["id"] == badge_row["TEXT_OBJECT"])
        fill_border_overlap, fill_border_clearance, _, _ = nearest_pair(fill_obj["coords"], border_obj["coords"])
        digit_border_overlap, digit_border_clearance, _, _ = nearest_pair(text_obj["coords"], border_obj["coords"])
        split_files = visual_card_for_pair(page_rgb, fill_obj, border_obj, OUT / "badge_component_evidence")
        padding_files = visual_card_for_pair(page_rgb, text_obj, border_obj, OUT / "badge_padding_evidence")
        badge_row.update({
            "FILL_BORDER_OVERLAP_PIXELS": fill_border_overlap,
            "FILL_BORDER_CLEARANCE_PX": f"{fill_border_clearance:.6f}",
            "FILL_BORDER_RELATION": "INTENTIONAL_SAME_PDF_FS_FILL_STROKE_COMPONENTS",
            "FILL_BORDER_PIXEL_EVIDENCE": ";".join(f"badge_component_evidence/{p}" for p in split_files),
            "DIGIT_BORDER_OVERLAP_PIXELS": digit_border_overlap,
            "DIGIT_BORDER_CLEARANCE_PX": f"{digit_border_clearance:.6f}",
            "DIGIT_BORDER_REQUIRED_CLEARANCE_PX": 5,
            "DIGIT_BORDER_STATUS": "FAIL_ILLEGAL_OVERLAP" if digit_border_overlap else ("FAIL_CLEARANCE" if digit_border_clearance < 5 else "PASS"),
            "DIGIT_BORDER_PIXEL_EVIDENCE": ";".join(f"badge_padding_evidence/{p}" for p in padding_files),
        })

    # Empty output is permitted only for explicitly documented opaque-white
    # occluders; an opaque dark badge FILL still must have a nonempty mask.
    graphic_mask_failures = [g["id"] for g in graphics if not g["empty_allowed"] and len(g["coords"]) == 0]

    # Purity also requires that a glyph contains no final-visible graphic
    # foreground. This is tested after source-vector masks are available.
    for i, item in enumerate(glyphs):
        encoded = set((int(y), int(x)) for y, x in item["coords"])
        foreign = 0
        for g in graphics:
            if g["background"] or len(g["coords"]) == 0:
                continue
            foreign += sum((int(y), int(x)) in encoded for y, x in g["coords"])
        glyph_rows[i]["FOREIGN_GRAPHIC_PIXEL_COUNT"] = foreign
        glyph_rows[i]["MASK_PURITY_PASS"] = glyph_rows[i]["MASK_PURITY_PASS_PREGRAPHIC"] and foreign == 0

    # Build every unordered semantic-object pair: 25 TEXT plus 44 semantic
    # graphics (39 emitted PDF paths, with five badge fs paths split FILL /
    # STROKE) = 69 objects and exactly 2,346 pairs.
    pair_rows: list[dict[str, Any]] = []
    critical_rows: list[dict[str, Any]] = []
    tt = tg = gg = 0
    for no, (a, b) in enumerate(combinations(all_objects, 2), start=1):
        if a["kind"] == b["kind"] == "TEXT":
            category = "TT"; tt += 1
        elif a["kind"] == b["kind"] == "GRAPHIC":
            category = "GG"; gg += 1
        else:
            category = "TG"; tg += 1
        whitelist_reason = INTENTIONAL.get(frozenset((a["id"], b["id"])), "")
        if a["background"] or b["background"]:
            overlap, clearance, pa, pb = 0, float("inf"), (-1, -1), (-1, -1)
            status = "EXEMPT_OPAQUE_BACKGROUND"
            threshold = 0
        else:
            overlap, clearance, pa, pb = nearest_pair(a["coords"], b["coords"])
            threshold = threshold_for(a, b)
            if len(a["coords"]) == 0 or len(b["coords"]) == 0:
                status = "FAIL_EMPTY_MASK"
            elif whitelist_reason:
                status = "INTENTIONAL_CONTACT" if overlap or clearance < threshold else "INTENTIONAL_SEPARATE"
            elif overlap > 0:
                status = "FAIL_ILLEGAL_OVERLAP"
            elif threshold and clearance < threshold:
                status = "FAIL_CLEARANCE"
            else:
                status = "PASS"
        pair_id = f"PAIR_{no:04d}"
        row = {"PAIR_ID": pair_id, "CATEGORY": category, "OBJECT_A": a["id"], "ROLE_A": a["role"], "OBJECT_B": b["id"], "ROLE_B": b["role"], "OVERLAP_PIXELS": overlap, "MIN_CLEARANCE_PX": "INF" if math.isinf(clearance) else f"{clearance:.6f}", "NEAREST_A_XY": f"{pa[0]},{pa[1]}", "NEAREST_B_XY": f"{pb[0]},{pb[1]}", "REQUIRED_CLEARANCE_PX": threshold, "WHITELIST_REASON": whitelist_reason, "STATUS": status}
        pair_rows.append(row)
        if (not math.isinf(clearance) and clearance < 12.0) or overlap > 0 or status.startswith("FAIL"):
            if len(a["coords"]) and len(b["coords"]):
                files = visual_card_for_pair(page_rgb, a, b, OUT / "critical_pair_cards")
                row["PIXEL_EVIDENCE"] = ";".join(f"critical_pair_cards/{p}" for p in files)
                critical_rows.append(row.copy())

    if len(pair_rows) != len(all_objects) * (len(all_objects) - 1) // 2:
        raise RuntimeError("pair-count identity failed")

    # Crop-edge / clip audit uses actual foreground masks, again on native grid.
    clip_count = 0
    crop_rows: list[dict[str, Any]] = []
    for obj in all_objects:
        # Opaque node fills remain subject to crop-edge audit even though they
        # are exempt from foreground-pair clearance.  Only genuinely empty
        # white occluder masks have no pixels to measure.
        if len(obj["coords"]) == 0:
            continue
        c = obj["coords"]
        left = int(c[:, 1].min() - crop_x0)
        right = int((crop_x1 - 1) - c[:, 1].max())
        top = int(c[:, 0].min() - crop_y0)
        bottom = int((crop_y1 - 1) - c[:, 0].max())
        min_edge = min(left, right, top, bottom)
        touch = int(np.sum((c[:, 1] == crop_x0) | (c[:, 1] == crop_x1 - 1) | (c[:, 0] == crop_y0) | (c[:, 0] == crop_y1 - 1)))
        clip_count += touch
        crop_rows.append({"OBJECT_ID": obj["id"], "MIN_CROP_EDGE_CLEARANCE_PX": min_edge, "CROP_EDGE_TOUCH_PIXELS": touch, "TEXT_EDGE_PASS": "N/A" if obj["kind"] != "TEXT" else min_edge >= 6})

    # Low-profile punctuation needs an independently matched calibration glyph.
    calibration_rows: list[dict[str, Any]] = []
    # Candidate-only scans found exact independent references.  p623 supplies
    # the dark feedback colon; p793 supplies the gray legend colon/semicolon/
    # full-stop.  Both were Poppler-rendered at native 300 dpi before use.
    reference_pages = []
    for physical, png in (
        (623, OUT / "calibration_reference_page_623_native_300dpi-623.png"),
        (626, OUT / "calibration_reference_page_626_native_300dpi-626.png"),
        (793, OUT / "calibration_reference_page_793_native_300dpi-793.png"),
        # p789 remains an independently rendered corroborating page for the
        # same gray class and is retained in the evidence package.
        (789, OUT / "calibration_reference_page_789_native_300dpi-789.png"),
    ):
        if png.exists():
            reference_pages.append((physical, document[physical - 1], np.asarray(Image.open(png).convert("RGB"))))
    reference_chars = []
    for ref_physical, ref_page, ref_rgb in reference_pages:
        for span in ref_page.get_text("rawdict")["blocks"]:
            if span.get("type") != 0:
                continue
            for line in span["lines"]:
                for sp in line["spans"]:
                    for ch in sp["chars"]:
                        if ch["c"] in ",.;:，。；：、…":
                            reference_chars.append((ref_physical, ref_page, ref_rgb, ch["c"], sp.get("font", ""), float(sp.get("size", 0)), to_rgb(sp.get("color")), tuple(ch["bbox"])))
    # These are independently selected from the exhaustive candidate scan and
    # its native measurements: each has the matching font/weight/colour/size,
    # a clean white (or matching gray-text) context, and a complete raw glyph.
    # Pinning them prevents a later run from silently changing reference glyph.
    reference_selection = {
        ("：", "NotoSerifSC-ExtraLight", (31, 35, 40)): (626, (327.572052, 645.221741, 337.136200, 655.464905)),
        ("：", "NotoSerifSC-ExtraLight", (77, 83, 88)): (793, (126.667709, 555.980713, 136.231842, 566.223907)),
        ("；", "NotoSerifSC-ExtraLight", (77, 83, 88)): (793, (203.486893, 555.980713, 213.051025, 566.223907)),
        ("。", "NotoSerifSC-ExtraLight", (77, 83, 88)): (793, (490.907318, 555.980713, 500.471466, 566.223907)),
    }
    selection_rows: list[dict[str, Any]] = []
    for gi, item in enumerate(glyphs):
        row = glyph_rows[gi]
        if row["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION":
            row["LOW_PROFILE_CALIBRATION"] = "N/A"
            row["PIXEL_PASS"] = row["PIXEL_PASS_PRECAL"]
            continue
        candidates = [r for r in reference_chars if r[3] == row["CHAR"] and r[4] == item["font"] and abs(r[5] - item["size"]) <= 0.25 and r[6] == item["color"]]
        if not candidates:
            row["LOW_PROFILE_CALIBRATION"] = "MISSING"
            row["PIXEL_PASS"] = False
            calibration_rows.append({"GLYPH_ID": row["GLYPH_ID"], "CHAR": row["CHAR"], "STATUS": "FAIL_MISSING_MATCHED_REFERENCE"})
            continue
        selection = reference_selection.get((row["CHAR"], item["font"], item["color"]))
        if selection is None:
            row["LOW_PROFILE_CALIBRATION"] = "MISSING_PINNED_SELECTION"
            row["PIXEL_PASS"] = False
            calibration_rows.append({"GLYPH_ID": row["GLYPH_ID"], "CHAR": row["CHAR"], "STATUS": "FAIL_MISSING_PINNED_SELECTION"})
            continue
        selected = [r for r in candidates if r[0] == selection[0] and all(abs(a - b) <= 0.002 for a, b in zip(r[7], selection[1]))]
        if len(selected) != 1:
            row["LOW_PROFILE_CALIBRATION"] = "MISSING_PINNED_REFERENCE"
            row["PIXEL_PASS"] = False
            calibration_rows.append({"GLYPH_ID": row["GLYPH_ID"], "CHAR": row["CHAR"], "STATUS": "FAIL_MISSING_PINNED_REFERENCE"})
            continue
        ref_physical, ref_page, ref_rgb, char, font, size, color, ref_box_pt = selected[0]
        rsx, rsy = ref_rgb.shape[1] / ref_page.rect.width, ref_rgb.shape[0] / ref_page.rect.height
        ref_box_px = pt_to_px(ref_box_pt, rsx, rsy)
        ref_mask, ref_bg, _ = local_mask(ref_rgb, ref_box_px)
        ref_coords = mask_to_coords(ref_mask, ref_box_px)
        ref_bbox = bbox_of_coords(ref_coords)
        ref_h = ref_bbox[3] - ref_bbox[1] if len(ref_coords) else 0
        target_h = int(row["H_INK_PX"])
        target_area = int(row["RAW_MASK_AREA_PX"])
        h_ratio = target_h / ref_h if ref_h else 0.0
        a_ratio = target_area / len(ref_coords) if len(ref_coords) else 0.0
        passed = len(ref_coords) > 0 and 0.92 <= h_ratio <= 1.08 and 0.92 <= a_ratio <= 1.08
        cbase = f"CAL_{safe_name(row['GLYPH_ID'])}_{ord(row['CHAR']):04X}"
        write_mask_png(OUT / "low_profile_calibration" / f"{cbase}_reference_mask.png", ref_coords, ref_box_px)
        make_card(ref_rgb, ref_coords, ref_box_px, f"REF p{ref_physical} {cbase} ORIGINAL | TARGET | MASK", OUT / "low_profile_calibration" / f"{cbase}_reference_card_8x.png")
        row["LOW_PROFILE_CALIBRATION"] = f"physical_page_{ref_physical}; H_RATIO={h_ratio:.6f}; AREA_RATIO={a_ratio:.6f}"
        row["PIXEL_PASS"] = passed
        calibration_rows.append({"GLYPH_ID": row["GLYPH_ID"], "CHAR": row["CHAR"], "STATUS": "PASS" if passed else "FAIL_RATIO", "REFERENCE_PHYSICAL_PAGE": ref_physical, "REFERENCE_FONT": font, "REFERENCE_PDF_SIZE": f"{size:.6f}", "REFERENCE_COLOR_RGB": "/".join(map(str, color)), "REFERENCE_BBOX": ",".join(map(str, ref_box_px)), "REFERENCE_H_INK_PX": ref_h, "REFERENCE_AREA_PX": len(ref_coords), "TARGET_H_RATIO": f"{h_ratio:.6f}", "TARGET_AREA_RATIO": f"{a_ratio:.6f}", "REFERENCE_MASK": f"low_profile_calibration/{cbase}_reference_mask.png", "REFERENCE_CARD_8X": f"low_profile_calibration/{cbase}_reference_card_8x.png"})
        selection_rows.append({"GLYPH_ID": row["GLYPH_ID"], "CHAR": row["CHAR"], "TARGET_FONT": item["font"], "TARGET_COLOR_RGB": "/".join(map(str, item["color"])), "REFERENCE_PHYSICAL_PAGE": ref_physical, "REFERENCE_BBOX_PT": ",".join(f"{v:.6f}" for v in ref_box_pt), "SELECTION_METHOD": "pinned_after_exhaustive_locked-candidate_scan_and_native_clean-mask_review"})

    # Role / panel medians use only comparable script classes; one-off roles
    # are recorded N/A rather than manufactured comparisons.
    comparable = defaultdict(list)
    for row in glyph_rows:
        if row["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION" and row["H_INK_PX"]:
            comparable[(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])].append(int(row["H_INK_PX"]))
    medians = {k: float(np.median(v)) for k, v in comparable.items()}
    role_stats = []
    for key, vals in sorted(comparable.items()):
        panel, role, script = key
        role_stats.append({"PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script, "N_GLYPHS": len(vals), "MEDIAN_H_INK_PX": f"{np.median(vals):.6f}", "MIN_H_INK_PX": min(vals), "MAX_H_INK_PX": max(vals), "MAX_TO_MIN": f"{max(vals)/min(vals):.6f}" if min(vals) else "INF"})
    for row in glyph_rows:
        key = (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        median = medians.get(key)
        ratio = float(row["H_INK_PX"]) / median if median else 0.0
        row["CLASS_MEDIAN_PX"] = "N/A" if median is None else f"{median:.6f}"
        row["RATIO_TO_CLASS_MEDIAN"] = "N/A" if median is None else f"{ratio:.6f}"
        row["SAME_CLASS_RATIO_PASS"] = "N/A" if median is None else (0.92 <= ratio <= 1.08)

    base_key = ("A", "STATION_TEXT", "CJK")
    base = medians.get(base_key, 0.0)
    role_ratio_rules = {"PANEL_TITLE": (1.05, 1.20), "LEGEND": (0.95, 1.10), "ANNOTATION": (0.95, 1.10), "ROUTE_TEXT": (0.95, 1.10), "ENGINE_CHIP": (0.95, 1.10), "VALIDATION_TEXT": (0.95, 1.10), "REPORT_TEXT": (0.95, 1.10), "STATION_TEXT": (0.95, 1.10)}
    for row in glyph_rows:
        if row["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION" or not base:
            row["ROLE_RATIO"] = "N/A"; row["ROLE_RATIO_PASS"] = "N/A"
            continue
        ratio = float(row["H_INK_PX"]) / base
        lo, hi = role_ratio_rules.get(row["ROLE"], (0.90, 1.25))
        row["ROLE_RATIO"] = f"{ratio:.6f}"
        row["ROLE_RATIO_PASS"] = lo <= ratio <= hi

    # Text measurement overlay (native crop coordinate; labels are evidence
    # annotations only and never re-enter a measurement).
    overlay = Image.fromarray(crop_rgb, mode="RGB").copy()
    draw = ImageDraw.Draw(overlay)
    for obj in text_objects:
        x0, y0, x1, y1 = obj["bbox"]
        draw.rectangle((x0 - crop_x0, y0 - crop_y0, x1 - crop_x0 - 1, y1 - crop_y0 - 1), outline=(255, 0, 0), width=1)
        draw.text((x0 - crop_x0, max(0, y0 - crop_y0 - 11)), obj["id"], fill=(220, 0, 0))
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Contact sheets: 16 individual 8x triptychs per sheet, with every glyph
    # addressable by sheet and cell in the reviewer ledger.
    contact_rows = []
    cards = [Image.open(OUT / row["CARD_8X_FILE"]).convert("RGB") for row in glyph_rows]
    for sheet_no, start in enumerate(range(0, len(cards), 16), start=1):
        subset = cards[start:start + 16]
        cell_w = max(im.width for im in subset)
        cell_h = max(im.height for im in subset)
        canvas = Image.new("RGB", (4 * cell_w, 4 * cell_h), "white")
        for j, card in enumerate(subset):
            x, y = (j % 4) * cell_w, (j // 4) * cell_h
            canvas.paste(card, (x, y))
            glyph_rows[start + j]["CONTACT_SHEET"] = f"glyph_contact_sheets/contact_sheet_{sheet_no:03d}.png"
            glyph_rows[start + j]["CONTACT_CELL"] = j + 1
            contact_rows.append({"GLYPH_ID": glyph_rows[start + j]["GLYPH_ID"], "SHEET": sheet_no, "CELL": j + 1, "CARD": glyph_rows[start + j]["CARD_8X_FILE"]})
        canvas.save(OUT / "glyph_contact_sheets" / f"contact_sheet_{sheet_no:03d}.png")

    # Reviewer ledger deliberately exposes every glyph rather than hiding the
    # manual reading step in one global automatic boolean.
    ledger_rows = []
    for row in glyph_rows:
        decision = "PASS_PENDING_MANUAL_OPEN" if row["MASK_PURITY_PASS"] and row["PIXEL_PASS"] else "FAIL_MACHINE"
        ledger_rows.append({"GLYPH_ID": row["GLYPH_ID"], "SHEET": row["CONTACT_SHEET"], "CELL": row["CONTACT_CELL"], "ORIGINAL_MATCH": "PENDING_MANUAL_OPEN", "OVERLAY_COMPLETE": "PENDING_MANUAL_OPEN", "MASK_ONLY_PURE": "PENDING_MANUAL_OPEN", "MISSING_STROKE_PX": "PENDING_MANUAL_OPEN", "FOREIGN_PIXEL_PX": row["FOREIGN_GLYPH_PIXEL_COUNT"] + row["FOREIGN_GRAPHIC_PIXEL_COUNT"], "DECISION": decision, "NOTE": "Machine output only; reviewer must replace after opening card."})

    # Per-element font source audit and all required identity data.
    font_rows = []
    for group in GROUPS:
        rows = [r for r in glyph_rows if r["ELEMENT_ID"] == group.ident]
        font_rows.append({"ELEMENT_ID": group.ident, "PANEL_ID": group.panel, "ROLE": group.role, "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": group.source_line, "DECLARED_PT": f"{group.declared_pt:.2f}", "GRAPHICS_SCALE": "1.000000", "EFFECTIVE_PT": f"{group.declared_pt:.2f}", "VISIBLE_GLYPH_COUNT": len(rows), "MIN_GLYPH_H_INK_PX": min(int(r["H_INK_PX"]) for r in rows), "MAX_GLYPH_H_INK_PX": max(int(r["H_INK_PX"]) for r in rows), "SOURCE_FONT_PASS": group.declared_pt >= 9.5, "FONT_FILES": ";".join(sorted(set(r["PDF_FONT"] for r in rows)) )})

    # Machine consistency summary. It does not convert PENDING manual evidence
    # into PASS; final report uses it to state the gate truthfully.
    failed_glyphs = [r["GLYPH_ID"] for r in glyph_rows if not r["MASK_PURITY_PASS"] or not r["PIXEL_PASS"] or float(r["EFFECTIVE_PT"]) < 9.50]
    failed_pairs = [r["PAIR_ID"] for r in pair_rows if r["STATUS"].startswith("FAIL")]
    summary = {
        "uid": "FIG-P756-01",
        "candidate_pdf": str(PDF),
        "candidate_sha256": sha256(PDF),
        "candidate_sha256_expected": EXPECTED_PDF_SHA256,
        "candidate_page_count": len(document),
        "physical_page": PDF_PAGE,
        "printed_page": PRINTED_PAGE,
        "page_size_pt": [page_rect.width, page_rect.height],
        "native_300dpi_dimensions": [width, height],
        "native_crop_xyxy": list(CROP),
        "source_file": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "aux_label_present": "fig:V5-C08-course-map" in AUX.read_text(encoding="utf-8", errors="replace"),
        "fls_source_present": "full_course_synthesis_map.tex" in FLS.read_text(encoding="utf-8", errors="replace"),
        "glyph_count": len(glyph_rows),
        "rawdict_figure_char_count": len(rawdict_rows),
        "rawdict_visible_mapped_count": sum(r["STATUS"] == "MAPPED_VISIBLE_GLYPH" for r in rawdict_rows),
        "rawdict_nonink_whitespace_or_empty_count": sum(r["STATUS"] == "NONINK_WHITESPACE_OR_EMPTY" for r in rawdict_rows),
        "rawdict_unresolved_combining_or_zero_width_count": len(unresolved_rawdict),
        "text_object_count": len(text_objects),
        "graphic_drawing_object_count": len(graphics),
        "graphic_semantic_object_count": len(graphics),
        "pdf_page_drawing_count": len(drawings),
        "figure_drawing_indices": figure_drawing_indices,
        "figure_drawing_path_count": len(figure_drawing_indices),
        "badge_fs_paths_split_to_fill_and_border": len(BADGE_BORDER_DEFS),
        "figure_path_coverage_failures": [r["DRAWING_INDEX"] for r in all_drawing_path_rows if r["COVERAGE_STATUS"] == "FAIL_UNMAPPED_FIGURE_PATH"],
        "math_rule_object_count": 0,
        "declared_math_rule_tokens": declared_math_rule_tokens,
        "object_count": len(all_objects),
        "pair_count": len(pair_rows),
        "pair_expected": len(all_objects) * (len(all_objects) - 1) // 2,
        "pair_partition": {"TT": tt, "TG": tg, "GG": gg, "sum": tt + tg + gg},
        "critical_pair_count": len(critical_rows),
        "graphic_empty_mask_failures": graphic_mask_failures,
        "glyph_failures_machine": failed_glyphs,
        "pair_failures_machine": failed_pairs,
        "clip_pixel_count": clip_count,
        "manual_ledger_status": "SEPARATE_MANUAL_LEDGER_REQUIRED; see reviewer_glyph_manual_ledger.csv",
    }

    write_csv(OUT / "after_font_audit.csv", font_rows)
    write_csv(OUT / "after_pixel_measurements.csv", glyph_rows)
    write_csv(OUT / "rawdict_character_reconciliation.csv", rawdict_rows)
    write_csv(OUT / "glyph_filename_map.csv", filename_rows)
    write_csv(OUT / "glyph_contact_sheet_index.csv", contact_rows)
    write_csv(OUT / "reviewer_glyph_ledger.csv", ledger_rows)
    write_csv(OUT / "graphic_object_inventory.csv", graphic_rows)
    write_csv(OUT / "all_pdf_drawing_path_inventory.csv", all_drawing_path_rows)
    write_csv(OUT / "badge_fill_border_requalification.csv", badge_component_rows)
    write_csv(OUT / "z_order_occlusion_ledger.csv", z_order_rows)
    write_csv(OUT / "object_pair_report.csv", pair_rows)
    write_csv(OUT / "after_overlap_report.csv", pair_rows)
    write_csv(OUT / "critical_pair_index.csv", critical_rows)
    write_csv(OUT / "crop_edge_clip_audit.csv", crop_rows)
    write_csv(OUT / "low_profile_calibration.csv", calibration_rows)
    write_csv(OUT / "role_pixel_statistics.csv", role_stats)
    (OUT / "candidate_identity.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "object_inventory.json").write_text(json.dumps([
        {k: v for k, v in obj.items() if k not in {"coords", "opaque_geometry_coords"}}
        for obj in all_objects
    ], ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "machine_crosscheck.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
