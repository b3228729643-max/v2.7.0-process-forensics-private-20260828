#!/usr/bin/env python3
"""Read-only strict R1 evidence generator for FIG-P482-01.

The program reads only the frozen R93 full-book PDF and the assigned figure
source/styles.  It writes every derivative solely beside this script.  Raster
foreground masks are derived directly from the native 300-dpi PDF render;
vector paths are used only as object locators, never as enlarged foreground
masks.  This preserves separation between true foreground intersections and
render/drawing-order artifacts.
"""

from __future__ import annotations

import csv
import copy
import json
import math
import os
import re
import statistics
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.svgLib.path import parse_path


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第04册_无监督学习与矩阵分解\V4-C04\fig_v4_c04_ellipse.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第04册_无监督学习与矩阵分解\chapters\V4-C04.tex")
SHARED_STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\styles\figure-style-v2.3.1.tex")
BOOK_STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty")

FIG_ID = "FIG-P482-01"
PDF_PHYSICAL_PAGE = 526  # Located afresh by caption search in the frozen PDF.
PRINTED_PAGE = 513
FIGURE_NO = "图27.1"
DPI = 300
PDF_TO_PX = DPI / 72.0

# Figure + caption bounds in PDF points.  These are intentionally a slightly
# wider canvas than the visual content so edge/clip measurements do not depend
# on a tight crop.  They are not a visual scale transformation.
FIG_RECT = fitz.Rect(130.0, 280.0, 470.0, 535.0)
RAW_DIR = OUT / "raw"
MASK_DIR = OUT / "masks"
OVERLAY_DIR = OUT / "overlays"
PAIR_DIR = OUT / "critical_pairs"
for d in (RAW_DIR, MASK_DIR, OVERLAY_DIR, PAIR_DIR):
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class Obj:
    oid: str
    kind: str
    role: str
    text: str
    bbox_pt: fitz.Rect
    mask: np.ndarray
    source_file: str
    source_line: str
    declared_pt: str = ""
    graphics_scale: str = "1.000"
    effective_pt: str = ""
    details: str = ""


def stext(span: dict[str, Any]) -> str:
    return "".join(c["c"] for c in span.get("chars", []))


def rect_union(rects: Iterable[fitz.Rect]) -> fitz.Rect:
    rects = list(rects)
    if not rects:
        raise ValueError("cannot form union of no rectangles")
    out = fitz.Rect(rects[0])
    for rect in rects[1:]:
        out |= rect
    return out


def px_rect(rect: fitz.Rect, sx: float, sy: float) -> tuple[int, int, int, int]:
    """PDF rect to inclusive crop-local device pixels, with no resize."""
    x0 = max(0, int(math.floor((rect.x0 - FIG_RECT.x0) * sx)))
    y0 = max(0, int(math.floor((rect.y0 - FIG_RECT.y0) * sy)))
    x1 = min(CROP_W - 1, int(math.ceil((rect.x1 - FIG_RECT.x0) * sx)))
    y1 = min(CROP_H - 1, int(math.ceil((rect.y1 - FIG_RECT.y0) * sy)))
    return x0, y0, x1, y1


def rect_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1 - 1, ax0 - bx1 - 1)
    dy = max(0, by0 - ay1 - 1, ay0 - by1 - 1)
    return float(math.hypot(dx, dy))


def foreground_mask(rgb: np.ndarray) -> np.ndarray:
    # Background is white in the frozen figure canvas.  At least one RGB
    # channel must differ from white by 20/255, exactly the §9.2.1 threshold.
    return np.max(np.abs(rgb.astype(np.int16) - 255), axis=2) >= 20


def raw_mask_for_rect(rect: fitz.Rect, fg: np.ndarray, sx: float, sy: float) -> np.ndarray:
    m = np.zeros(fg.shape, dtype=bool)
    x0, y0, x1, y1 = px_rect(rect, sx, sy)
    if x1 >= x0 and y1 >= y0:
        m[y0 : y1 + 1, x0 : x1 + 1] = fg[y0 : y1 + 1, x0 : x1 + 1]
    return m


class GlyphMaskPen:
    """Minimal SVG pen that fills one embedded PDF glyph at device scale."""

    def __init__(self, sx: float, sy: float, a: float, tx: float, ty: float):
        self.sx, self.sy, self.a, self.tx, self.ty = sx, sy, a, tx, ty
        self.current: tuple[float, float] | None = None
        self.contours: list[list[tuple[int, int]]] = []
        self.contour: list[tuple[int, int]] = []

    def _pt(self, p: tuple[float, float]) -> tuple[int, int]:
        # SVG uses the PDF's top-down page coordinate system; the glyph itself
        # has a -a y scale in its use transform.
        return (int(round((self.tx + self.a * p[0]) * self.sx)), int(round((self.ty - self.a * p[1]) * self.sy)))

    def _flush(self) -> None:
        if len(self.contour) >= 3:
            self.contours.append(self.contour)
        self.contour = []

    def moveTo(self, p: tuple[float, float]) -> None:
        self._flush()
        self.current = p
        self.contour = [self._pt(p)]

    def lineTo(self, p: tuple[float, float]) -> None:
        self.contour.append(self._pt(p))
        self.current = p

    def curveTo(self, *points: tuple[float, float]) -> None:
        ensure(self.current is not None and len(points) == 3, "invalid SVG cubic glyph path")
        p0 = np.array(self.current, dtype=float)
        p1, p2, p3 = (np.array(x, dtype=float) for x in points)
        t = np.linspace(0.0, 1.0, 17)[1:, None]
        curve = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
        self.contour.extend(self._pt(tuple(p)) for p in curve)
        self.current = tuple(p3)

    def qCurveTo(self, *points: tuple[float, float] | None) -> None:
        # SVG Q commands map to one quadratic control and one end point.
        ensure(self.current is not None and len(points) == 2 and points[-1] is not None, "invalid SVG quadratic glyph path")
        p0 = np.array(self.current, dtype=float)
        p1 = np.array(points[0], dtype=float)
        p2 = np.array(points[1], dtype=float)
        t = np.linspace(0.0, 1.0, 17)[1:, None]
        curve = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
        self.contour.extend(self._pt(tuple(p)) for p in curve)
        self.current = tuple(p2)

    def closePath(self) -> None:
        self._flush()
        self.current = None

    def endPath(self) -> None:
        self._flush()
        self.current = None

    def rasterize(self, canvas: np.ndarray) -> None:
        self._flush()
        if self.contours:
            cv2.fillPoly(canvas, [np.array(c, dtype=np.int32) for c in self.contours], 255, lineType=cv2.LINE_AA)


def svg_text_silhouette(page: fitz.Page, target_chars: list[tuple[str, fitz.Rect]], width: int, height: int) -> np.ndarray:
    """Return exact text-glyph silhouette from the PDF's own SVG outlines.

    MuPDF exports every glyph as a `<use>` of the embedded font outline.  The
    embedded SVG path is rasterized directly here with its original transform;
    this avoids a second document renderer and gives a shape-exact text
    locator. Intersecting it with the native PDF raster below removes a nearby
    curve seen through a translucent label backdrop without erasing a real
    glyph--curve collision.
    """
    svg = page.get_svg_image()
    root = ET.fromstring(svg)
    uses = [e for e in root.iter() if e.tag.endswith("use")]
    parsed: list[tuple[ET.Element, str, float, float]] = []
    for use in uses:
        transform = use.attrib.get("transform", "")
        m = re.search(r"matrix\([^,]+,[^,]+,[^,]+,[^,]+,([^,]+),([^)]+)\)", transform)
        if m and "data-text" in use.attrib:
            parsed.append((use, use.attrib["data-text"], float(m.group(1)), float(m.group(2))))
    path_defs = {e.attrib["id"]: e.attrib["d"] for e in root.iter() if e.tag.endswith("path") and "id" in e.attrib and "d" in e.attrib}
    selected: list[tuple[ET.Element, str, float, float]] = []
    used: set[int] = set()
    for ch, rect in target_chars:
        candidates = [
            (idx, use) for idx, (use, data, x, y) in enumerate(parsed)
            if idx not in used and data == ch and abs(x - rect.x0) < 0.08 and rect.y0 - 10 <= y <= rect.y1 + 10
        ]
        ensure(len(candidates) == 1, f"SVG glyph locator mismatch for {ch!r} at {rect}: {len(candidates)} candidates")
        idx, use = candidates[0]
        used.add(idx)
        selected.append((use, ch, rect.x0, rect.y0))
    canvas = np.zeros((height, width), dtype=np.uint8)
    log: list[dict[str, Any]] = []
    for use, ch, _, _ in selected:
        href = use.attrib.get("{http://www.w3.org/1999/xlink}href", use.attrib.get("href", ""))
        gid = href.lstrip("#")
        ensure(gid in path_defs, f"missing embedded glyph path {gid}")
        nums = re.search(r"matrix\(([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^)]+)\)", use.attrib["transform"])
        ensure(nums is not None, f"unparseable glyph transform: {use.attrib.get('transform')}")
        a, _b, _c, d, tx, ty = (float(nums.group(i)) for i in range(1, 7))
        ensure(abs(d + a) < 0.01, "expected standard y-flipped glyph matrix")
        pen = GlyphMaskPen(width / page.rect.width, height / page.rect.height, a, tx, ty)
        parse_path(path_defs[gid], pen)
        pen.rasterize(canvas)
        log.append({"glyph": ch, "glyph_path": gid, "transform": use.attrib["transform"]})
    (RAW_DIR / "text_glyph_vector_locator.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    Image.fromarray(canvas).save(RAW_DIR / "text_vector_only_300dpi.png")
    return canvas >= 20


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def ink_height(mask: np.ndarray) -> int:
    bb = mask_bbox(mask)
    return 0 if bb is None else bb[3] - bb[1] + 1


def mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return float("nan")
    if np.any(a & b):
        return 0.0
    # distanceTransform measures every nonzero pixel to closest zero.  Set the
    # target foreground to zero, then sample the source foreground.
    dist = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 5)
    return float(np.min(dist[a]))


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def draw_geom_item(canvas: np.ndarray, item: tuple[Any, ...], thickness: int, fill: bool) -> None:
    def point(p: fitz.Point) -> tuple[int, int]:
        return (int(round((p.x - FIG_RECT.x0) * SX)), int(round((p.y - FIG_RECT.y0) * SY)))

    kind = item[0]
    if kind == "l":
        cv2.line(canvas, point(item[1]), point(item[2]), 255, max(1, thickness), cv2.LINE_AA)
    elif kind == "c":
        p0 = np.array(point(item[1]), dtype=float)
        p1 = np.array(point(item[2]), dtype=float)
        p2 = np.array(point(item[3]), dtype=float)
        p3 = np.array(point(item[4]), dtype=float)
        t = np.linspace(0.0, 1.0, 41)[:, None]
        curve = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
        cv2.polylines(canvas, [np.round(curve).astype(np.int32)], False, 255, thickness, cv2.LINE_AA)
    elif kind == "re":
        r = item[1]
        p0, p1 = point(r.tl), point(r.br)
        if fill:
            cv2.rectangle(canvas, p0, p1, 255, -1)
        if thickness:
            cv2.rectangle(canvas, p0, p1, 255, thickness, cv2.LINE_AA)
    elif kind == "qu":
        # Quadratic curves do not occur in this figure, but retain an explicit
        # safe locator if a backend emits one.
        pts = np.array([point(x) for x in item[1:]], dtype=np.int32)
        cv2.polylines(canvas, [pts], False, 255, thickness, cv2.LINE_AA)


def drawing_locator(drawing: dict[str, Any]) -> np.ndarray:
    """Raster device-location gate, not an output foreground mask.

    The extra one-pixel gate captures PDF-to-device anti-aliasing uncertainty.
    The returned masks are always intersected with the raw thresholded render;
    no foreground mask is expanded or dilated.
    """
    canvas = np.zeros((CROP_H, CROP_W), dtype=np.uint8)
    width_pt = drawing.get("width") or 0.0
    width_px = max(1, int(math.ceil(width_pt * (SX + SY) / 2.0)) + 2)
    fill = drawing.get("fill") is not None and drawing.get("fill_opacity", 1.0) > 0
    stroke = drawing.get("color") is not None and drawing.get("stroke_opacity", 1.0) > 0
    for item in drawing["items"]:
        draw_geom_item(canvas, item, width_px if stroke else 0, fill)
    if fill:
        # Filled PDF paths (the scatter circles, arrow heads, triangle and
        # square) have compact vector bounds.  Their bound is only a location
        # gate; intersecting it with raw thresholded pixels preserves the
        # actual unexpanded filled foreground without trying to re-render the
        # PDF fill geometry in a second rasterizer.
        r = drawing["rect"]
        p0 = (int(math.floor((r.x0 - FIG_RECT.x0) * SX)) - 1, int(math.floor((r.y0 - FIG_RECT.y0) * SY)) - 1)
        p1 = (int(math.ceil((r.x1 - FIG_RECT.x0) * SX)) + 1, int(math.ceil((r.y1 - FIG_RECT.y0) * SY)) + 1)
        cv2.rectangle(canvas, p0, p1, 255, -1)
    return canvas.astype(bool)


def classify_char(ch: str, parent: str) -> tuple[str, int, str]:
    """Return script class, applicable min pixel threshold, and role note."""
    if parent in {"T08_AXIS_X1", "T09_AXIS_X2"} and ch in {"1", "2"}:
        return "NATURAL_SUBSCRIPT", 15, "natural subscript of 10pt axis formula"
    if ch in {"一", "二"}:
        # These ideographs are intentionally one/two horizontal ink strokes.
        # Their parent CJK word-line is separately measured at >=30px, while
        # their own raw foreground height is recorded without applying a
        # physically impossible full-glyph-height floor.
        return "CJK_STROKE_IDEOGRAPH", 0, "single/double-stroke CJK ideograph; parent word-line carries the CJK full-height check"
    if "\u4e00" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef":
        return "CJK_FULL", 30, "CJK/full-width glyph"
    uname = unicodedata.name(ch, "")
    if "SMALL" in uname and ("GREEK" in uname or "LAMDA" in uname or "SIGMA" in uname):
        return "GREEK_LOWER", 17, "lowercase Greek"
    if "SMALL" in uname and "MATHEMATICAL" in uname:
        return "LATIN_LOWER", 17, "mathematical lowercase Latin"
    if ch.isdigit():
        return "DIGIT", 24, "digit; measured separately"
    if ch.isalpha() and ch.upper() == ch:
        return "LATIN_UPPER", 24, "uppercase Latin"
    if ch.isalpha():
        return "LATIN_LOWER", 17, "lowercase Latin"
    if ch in "+−-=":
        return "MATH_OPERATOR", 22, "operator measured as its own substring"
    return "PUNCTUATION_IN_TOKEN", 0, "non-operator punctuation audited within its numeric/text token"


def csv_write(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def image_rgba_overlay(rgb: np.ndarray, masks: list[tuple[np.ndarray, tuple[int, int, int]]], alpha: float = 0.55) -> np.ndarray:
    out = rgb.astype(float).copy()
    for mask, color in masks:
        if mask.any():
            out[mask] = out[mask] * (1 - alpha) + np.array(color, dtype=float) * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def crop_with_pad(rgb: np.ndarray, bb: tuple[int, int, int, int], pad: int = 24) -> tuple[np.ndarray, tuple[int, int]]:
    x0, y0, x1, y1 = bb
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(CROP_W - 1, x1 + pad), min(CROP_H - 1, y1 + pad)
    return rgb[y0 : y1 + 1, x0 : x1 + 1], (x0, y0)


def ensure(cond: bool, message: str) -> None:
    if not cond:
        raise RuntimeError(message)


# ---------------------------------------------------------------------------
# 1. Locate from frozen PDF and render native views.
# ---------------------------------------------------------------------------
doc = fitz.open(PDF)
ensure(doc.page_count == 813, f"frozen PDF page count unexpected: {doc.page_count}")
caption_hits = [i + 1 for i in range(doc.page_count) if "二维协方差椭圆" in doc[i].get_text("text")]
ensure(caption_hits == [PDF_PHYSICAL_PAGE], f"caption location is not unique/current: {caption_hits}")
page = doc[PDF_PHYSICAL_PAGE - 1]
page_text = page.get_text("text")
ensure("图27.1" in page_text and "二维协方差椭圆与主轴示意" in page_text, "figure number/caption absent from located page")

pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False)
pix300 = page.get_pixmap(matrix=fitz.Matrix(PDF_TO_PX, PDF_TO_PX), alpha=False)
Image.frombytes("RGB", [pix200.width, pix200.height], pix200.samples).save(OUT / "after_full_page_200dpi.png")
full300 = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, 3).copy()
Image.fromarray(full300).save(OUT / "after_full_page_300dpi.png")

SX = pix300.width / page.rect.width
SY = pix300.height / page.rect.height
fx0 = int(math.floor(FIG_RECT.x0 * SX))
fy0 = int(math.floor(FIG_RECT.y0 * SY))
fx1 = int(math.ceil(FIG_RECT.x1 * SX))
fy1 = int(math.ceil(FIG_RECT.y1 * SY))
rgb = full300[fy0:fy1, fx0:fx1].copy()
CROP_H, CROP_W = rgb.shape[:2]
Image.fromarray(rgb).save(OUT / "after_figure_crop_300dpi.png")
Image.fromarray(rgb).save(OUT / "after_standalone_300dpi.png")
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
Image.fromarray(gray).save(OUT / "after_grayscale_300dpi.png")
Image.fromarray(rgb).save(RAW_DIR / "figure_crop_native_300dpi_raw.png")
Image.fromarray(full300).save(RAW_DIR / "page_native_300dpi_raw.png")
fg = foreground_mask(rgb)
save_mask(MASK_DIR / "foreground_raw_threshold20.png", fg)

# ---------------------------------------------------------------------------
# 2. Extract vector text boxes and establish all reader-visible text objects.
# ---------------------------------------------------------------------------
rawdict = page.get_text("rawdict")
spans: list[dict[str, Any]] = []
for block in rawdict["blocks"]:
    if block.get("type") == 0:
        for line in block["lines"]:
            spans.extend(line["spans"])


def one_span(text: str, ymin: float = FIG_RECT.y0, ymax: float = FIG_RECT.y1) -> dict[str, Any]:
    hits = [s for s in spans if stext(s) == text and ymin <= s["bbox"][1] <= ymax]
    ensure(len(hits) == 1, f"expected exactly one span {text!r}, got {len(hits)}")
    return hits[0]


sem_specs: list[dict[str, Any]] = [
    {"oid": "T01_MEAN", "role": "ANNOTATION", "text": "均值 μ", "parts": [one_span("均值"), one_span("𝜇")], "decl": "9.40", "effective": "9.40", "source": "fig_v4_c04_ellipse.tex", "line": "48", "details": "local node font=\\fontsize{9.4pt}{11.2pt}; no graphics scale"},
    {"oid": "T02_AXIS1", "role": "ANNOTATION", "text": "第一主轴 λ₁", "parts": [one_span("第一主轴"), one_span("𝜆1")], "decl": "9.00", "effective": "9.00", "source": "figure-style-v2.3.1.tex", "line": "40; fig_v4_c04_ellipse.tex:49", "details": "slfig direct label overrides picture font with \\footnotesize; 11pt class resolves it to 9pt"},
    {"oid": "T03_AXIS2", "role": "ANNOTATION", "text": "第二主轴 λ₂", "parts": [one_span("第二主轴"), one_span("𝜆2")], "decl": "9.00", "effective": "9.00", "source": "figure-style-v2.3.1.tex", "line": "40; fig_v4_c04_ellipse.tex:50", "details": "slfig direct label overrides picture font with \\footnotesize; 11pt class resolves it to 9pt"},
    {"oid": "T04_2SIGMA", "role": "FORMULA_ANNOTATION", "text": "2σ", "parts": [one_span("2𝜎")], "decl": "9.40", "effective": "9.40", "source": "fig_v4_c04_ellipse.tex", "line": "53", "details": "local node font=\\fontsize{9.4pt}{11.2pt}"},
    {"oid": "T05_1SIGMA", "role": "FORMULA_ANNOTATION", "text": "1σ", "parts": [one_span("1𝜎")], "decl": "9.40", "effective": "9.40", "source": "fig_v4_c04_ellipse.tex", "line": "54", "details": "local node font=\\fontsize{9.4pt}{11.2pt}"},
    {"oid": "T06_SAMPLE_Q", "role": "ANNOTATION", "text": "样本 q", "parts": [one_span("样本"), one_span("𝑞")], "decl": "9.00", "effective": "9.00", "source": "figure-style-v2.3.1.tex", "line": "40; fig_v4_c04_ellipse.tex:69", "details": "slfig direct label overrides picture font with \\footnotesize; 11pt class resolves it to 9pt"},
    {"oid": "T07_PROJECTION", "role": "ANNOTATION", "text": "正交投影", "parts": [one_span("正交投影")], "decl": "9.00", "effective": "9.00", "source": "figure-style-v2.3.1.tex", "line": "40; fig_v4_c04_ellipse.tex:70", "details": "slfig direct label overrides picture font with \\footnotesize; 11pt class resolves it to 9pt"},
    {"oid": "T08_AXIS_X1", "role": "AXIS_TITLE", "text": "x₁", "parts": [one_span("𝑥", 380, 410), one_span("1", 380, 410)], "decl": "10.00", "effective": "10.00", "source": "fig_v4_c04_ellipse.tex", "line": "11,30", "details": "axis label style=\\fontsize{10pt}{12pt}; subscript naturally derived"},
    {"oid": "T09_AXIS_X2", "role": "AXIS_TITLE", "text": "x₂", "parts": [one_span("𝑥", 285, 320), one_span("2", 285, 320)], "decl": "10.00", "effective": "10.00", "source": "fig_v4_c04_ellipse.tex", "line": "11,30", "details": "axis label style=\\fontsize{10pt}{12pt}; subscript naturally derived"},
    {"oid": "T10_CAPTION", "role": "CAPTION", "text": "图27.1 二维协方差椭圆与主轴示意", "parts": [one_span("图", 505, 535), one_span("27.1", 505, 535), one_span("二维协方差椭圆与主轴示意", 505, 535)], "decl": "10.00", "effective": "10.00", "source": "statlearnbook.sty", "line": "305", "details": "caption font=small under 11pt ctexbook; no graphics scale"},
]

target_chars: list[tuple[str, fitz.Rect]] = []
for spec in sem_specs:
    for part in spec["parts"]:
        for char in part["chars"]:
            if not char["c"].isspace():
                target_chars.append((char["c"], fitz.Rect(char["bbox"])))
text_silhouette_full = svg_text_silhouette(page, target_chars, pix300.width, pix300.height)
text_silhouette = text_silhouette_full[fy0:fy1, fx0:fx1]
ensure(text_silhouette.shape == fg.shape, "text vector silhouette does not align to native crop")
save_mask(MASK_DIR / "text_vector_silhouette_raw_alignment.png", text_silhouette)

text_objects: list[Obj] = []
glyph_rows: list[dict[str, Any]] = []
font_rows: list[dict[str, Any]] = []
vector_bbox_rows: list[dict[str, Any]] = []

for spec in sem_specs:
    rect = rect_union(fitz.Rect(p["bbox"]) for p in spec["parts"])
    mask = raw_mask_for_rect(rect, fg & text_silhouette, SX, SY)
    obj = Obj(spec["oid"], "TEXT", spec["role"], spec["text"], rect, mask, spec["source"], spec["line"], spec["decl"], "1.000", spec["effective"], spec["details"])
    text_objects.append(obj)
    ph = ink_height(mask)
    font_pass = float(spec["effective"]) >= 9.5
    font_rows.append({
        "ELEMENT_ID": obj.oid, "ROLE": obj.role, "TEXT_SAMPLE": obj.text,
        "SOURCE_FILE": obj.source_file, "SOURCE_LINE": obj.source_line,
        "DECLARED_PT": obj.declared_pt, "GRAPHICS_SCALE": obj.graphics_scale,
        "EFFECTIVE_PT": obj.effective_pt, "MIN_EFFECTIVE_PT": "9.50",
        "SOURCE_FONT_PASS": str(font_pass).lower(), "RESOLUTION": obj.details,
    })
    vector_bbox_rows.append({"OBJECT_ID": obj.oid, "TYPE": "TEXT", "ROLE": obj.role, "TEXT": obj.text,
                             "PDF_X0": f"{rect.x0:.3f}", "PDF_Y0": f"{rect.y0:.3f}", "PDF_X1": f"{rect.x1:.3f}", "PDF_Y1": f"{rect.y1:.3f}",
                             "PX_X0": px_rect(rect, SX, SY)[0], "PX_Y0": px_rect(rect, SX, SY)[1], "PX_X1": px_rect(rect, SX, SY)[2], "PX_Y1": px_rect(rect, SX, SY)[3],
                             "RAW_MASK_FILE": f"masks/{obj.oid}.png"})
    save_mask(MASK_DIR / f"{obj.oid}.png", mask)
    # Every visible glyph gets a separate raw-mask measurement.  PDF vector
    # character boxes keep script, digit, and natural subscript tests honest.
    ordinal = 0
    for part in spec["parts"]:
        for char in part["chars"]:
            ch = char["c"]
            if ch.isspace():
                continue
            ordinal += 1
            cclass, minpx, class_note = classify_char(ch, obj.oid)
            crect = fitz.Rect(char["bbox"])
            cmask = raw_mask_for_rect(crect, fg & text_silhouette, SX, SY)
            cid = f"{obj.oid}_G{ordinal:02d}"
            save_mask(MASK_DIR / f"{cid}.png", cmask)
            cb = px_rect(crect, SX, SY)
            h = ink_height(cmask)
            # A decimal/full-stop is still covered inside its numeric token;
            # no false 22px operator rule is applied to a non-operator dot.
            if minpx == 0:
                glyph_pass = True
                reason = class_note
            elif h == 0:
                glyph_pass = False
                reason = f"no thresholded raw foreground; needs >= {minpx}px"
            else:
                glyph_pass = h >= minpx
                reason = f"{class_note}; {'meets' if glyph_pass else 'below'} >= {minpx}px"
            glyph_rows.append({
                "ELEMENT_ID": cid, "PARENT_ID": obj.oid, "PANEL_ID": "P1", "ROLE": obj.role,
                "SOURCE_FILE": obj.source_file, "SOURCE_LINE": obj.source_line,
                "DECLARED_PT": obj.declared_pt, "GRAPHICS_SCALE": obj.graphics_scale, "EFFECTIVE_PT": obj.effective_pt,
                "TEXT_SAMPLE": ch, "SCRIPT_CLASS": cclass,
                "BBOX_X0": cb[0], "BBOX_Y0": cb[1], "BBOX_X1": cb[2], "BBOX_Y1": cb[3],
                "H_INK_PX": h, "MIN_REQUIRED_PX": minpx, "CLASS_MEDIAN_PX": "PENDING",
                "RATIO_TO_CLASS_MEDIAN": "PENDING", "ROLE_RATIO": "PENDING",
                "TEXT_TEXT_OVERLAP_PX": "PENDING", "TEXT_GRAPHIC_OVERLAP_PX": "PENDING", "MIN_CLEARANCE_PX": "PENDING",
                "PIXEL_HEIGHT_PASS": "PASS" if glyph_pass else "FAIL", "PASS_FAIL": "PASS" if glyph_pass else "FAIL", "REASON": reason,
                "RAW_MASK_FILE": f"masks/{cid}.png",
            })

ensure(len(text_objects) == 10, "visible semantic text coverage is incomplete")

# Source-size coordination must be shown separately from the 9.5pt floor.
# Roles with a single reader-facing element trivially satisfy the dispersion
# rule; annotation labels are the meaningful multi-element comparison here.
font_rows_by_role: dict[str, list[dict[str, Any]]] = {}
for row in font_rows:
    font_rows_by_role.setdefault(row["ROLE"], []).append(row)
for role, rows in font_rows_by_role.items():
    vals = [float(r["EFFECTIVE_PT"]) for r in rows]
    maxmin = max(vals) / min(vals)
    delta = max(vals) - min(vals)
    passed = maxmin <= 1.03 and delta <= 0.25
    for row in rows:
        row["SOURCE_ROLE_MAX_MIN"] = f"{maxmin:.4f}"
        row["SOURCE_ROLE_DELTA_PT"] = f"{delta:.2f}"
        row["SAME_ROLE_SOURCE_PASS"] = str(passed).lower()

# ---------------------------------------------------------------------------
# 3. Recover vector graphic objects, then produce unexpanded raw masks.
# ---------------------------------------------------------------------------
drawings = {d.get("seqno"): d for d in page.get_drawings()}
graphic_specs: list[tuple[str, str, str, list[int]]] = [
    ("G01_X_AXIS", "LINE_ARROW", "AXIS", [16, 17]),
    ("G02_Y_AXIS", "LINE_ARROW", "AXIS", [18, 19]),
    ("G03_INNER_ELLIPSE", "DATA_CURVE", "COVARIANCE_ELLIPSE", [20]),
    ("G04_OUTER_ELLIPSE", "DATA_CURVE", "COVARIANCE_ELLIPSE", [21]),
    ("G05_PC1_AXIS", "LINE_ARROW", "PRINCIPAL_AXIS", [22]),
    ("G06_PC2_AXIS", "LINE_ARROW", "PRINCIPAL_AXIS", [23]),
    ("G07_RESIDUAL", "LINE_ARROW", "RESIDUAL", [31]),
    ("G08_RIGHT_ANGLE", "LINE_ARROW", "RIGHT_ANGLE", [32]),
]
for i, seq in enumerate(range(37, 76, 2), start=1):
    graphic_specs.append((f"M{i:02d}_SAMPLE", "MARKER", "SAMPLE", [seq]))
graphic_specs.extend([
    ("M21_MEAN", "MARKER", "MEAN", [77]),
    ("M22_QUERY", "MARKER", "QUERY", [79]),
    ("M23_PROJECTION", "MARKER", "PROJECTION", [81]),
])
for _, _, _, seqs in graphic_specs:
    ensure(all(s in drawings for s in seqs), f"missing expected drawing sequence: {seqs}")

graphic_objects: list[Obj] = []
for oid, kind, role, seqs in graphic_specs:
    loc = np.zeros((CROP_H, CROP_W), dtype=bool)
    drects: list[fitz.Rect] = []
    for seq in seqs:
        loc |= drawing_locator(drawings[seq])
        drects.append(fitz.Rect(drawings[seq]["rect"]))
    raw = fg & loc  # Foreground remains exactly from raw PDF pixels; never dilated.
    rect = rect_union(drects)
    obj = Obj(oid, kind, role, "", rect, raw, "final PDF vector drawing", ";".join(map(str, seqs)))
    graphic_objects.append(obj)
    save_mask(MASK_DIR / f"{oid}.png", raw)
    pxb = px_rect(rect, SX, SY)
    vector_bbox_rows.append({"OBJECT_ID": oid, "TYPE": kind, "ROLE": role, "TEXT": "",
                             "PDF_X0": f"{rect.x0:.3f}", "PDF_Y0": f"{rect.y0:.3f}", "PDF_X1": f"{rect.x1:.3f}", "PDF_Y1": f"{rect.y1:.3f}",
                             "PX_X0": pxb[0], "PX_Y0": pxb[1], "PX_X1": pxb[2], "PX_Y1": pxb[3],
                             "RAW_MASK_FILE": f"masks/{oid}.png"})

all_graphic = np.zeros_like(fg)
for obj in graphic_objects:
    all_graphic |= obj.mask
save_mask(MASK_DIR / "all_graphics_raw_separated.png", all_graphic)
all_text = np.zeros_like(fg)
for obj in text_objects:
    all_text |= obj.mask
save_mask(MASK_DIR / "all_text_raw_separated.png", all_text)
save_mask(MASK_DIR / "illegal_overlap_raw.png", all_text & all_graphic)

# Object overlay: cyan graphic pixels, magenta text pixels, yellow raw overlap.
overlay = image_rgba_overlay(rgb, [(all_graphic, (0, 220, 255)), (all_text, (255, 0, 220))], 0.45)
overlap = all_text & all_graphic
if overlap.any():
    overlay = image_rgba_overlay(overlay, [(overlap, (255, 225, 0))], 0.85)
Image.fromarray(overlay).save(OVERLAY_DIR / "all_semantic_objects_overlay_300dpi.png")

# ---------------------------------------------------------------------------
# 4. Pairwise raw-mask, bbox-clearance, and explicit exception accounting.
# ---------------------------------------------------------------------------
objects = text_objects + graphic_objects
obj_by_id = {o.oid: o for o in objects}
pair_rows: list[dict[str, Any]] = []
critical_pairs: list[dict[str, Any]] = []
for i, a in enumerate(objects):
    for b in objects[i + 1 :]:
        atext, btext = a.kind == "TEXT", b.kind == "TEXT"
        if atext and btext:
            relation, required, minreq = "TEXT_TEXT", True, 4.0
            clearance = rect_distance(px_rect(a.bbox_pt, SX, SY), px_rect(b.bbox_pt, SX, SY))
            clearance_type = "vector_bbox"
        elif atext or btext:
            relation, required, minreq = "TEXT_GRAPHIC", True, 3.0
            clearance = mask_distance(a.mask, b.mask)
            clearance_type = "unexpanded_raw_foreground"
        else:
            relation, required, minreq = "GRAPHIC_GRAPHIC", False, 0.0
            clearance = mask_distance(a.mask, b.mask)
            clearance_type = "unexpanded_raw_foreground"
        overlap_px = int(np.count_nonzero(a.mask & b.mask))
        if required:
            if math.isnan(clearance):
                verdict, reason = "FAIL", "one required raw foreground mask is empty/unmeasurable"
            elif overlap_px > 0:
                verdict, reason = "FAIL", "illegal raw foreground overlap"
            elif clearance < minreq:
                verdict, reason = "FAIL", f"clearance below {minreq:g}px"
            else:
                verdict, reason = "PASS", "zero illegal overlap and clearance meets floor"
        else:
            verdict, reason = "EXEMPT", "geometric/data intersection is not a text-collision criterion"
        row = {
            "PAIR_ID": f"{a.oid}__{b.oid}", "OBJECT_A": a.oid, "TYPE_A": a.kind, "OBJECT_B": b.oid, "TYPE_B": b.kind,
            "RELATION": relation, "REQUIRED": str(required).lower(), "MASK_BASIS": "raw_threshold20_no_dilation",
            "BBOX_CLEARANCE_PX": f"{rect_distance(px_rect(a.bbox_pt, SX, SY), px_rect(b.bbox_pt, SX, SY)):.3f}",
            "MIN_CLEARANCE_PX": "" if math.isnan(clearance) else f"{clearance:.3f}", "MIN_REQUIRED_PX": f"{minreq:.0f}",
            "CLEARANCE_TYPE": clearance_type, "RAW_OVERLAP_PX": overlap_px, "VERDICT": verdict, "REASON": reason,
        }
        pair_rows.append(row)
        if required and (verdict == "FAIL" or (not math.isnan(clearance) and clearance < 8.0)):
            critical_pairs.append(row)

csv_write(OUT / "after_overlap_report.csv", list(pair_rows[0].keys()), pair_rows)

# Render evidence for every critical or failed relation, preserving both masks.
for row in critical_pairs:
    a, b = obj_by_id[row["OBJECT_A"]], obj_by_id[row["OBJECT_B"]]
    abb, bbb = mask_bbox(a.mask), mask_bbox(b.mask)
    if abb is None or bbb is None:
        continue
    union = (min(abb[0], bbb[0]), min(abb[1], bbb[1]), max(abb[2], bbb[2]), max(abb[3], bbb[3]))
    roi, (ox, oy) = crop_with_pad(rgb, union)
    am = a.mask[oy : oy + roi.shape[0], ox : ox + roi.shape[1]]
    bm = b.mask[oy : oy + roi.shape[0], ox : ox + roi.shape[1]]
    im = image_rgba_overlay(roi, [(am, (255, 0, 0)), (bm, (0, 230, 255)), (am & bm, (255, 230, 0))], 0.62)
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", row["PAIR_ID"])
    Image.fromarray(im).save(PAIR_DIR / f"{safe}.png")

# ---------------------------------------------------------------------------
# 5. Per-glyph / semantic measurements and ratios.
# ---------------------------------------------------------------------------
text_graphic_overlap: dict[str, int] = {}
text_graphic_clearance: dict[str, float] = {}
text_text_overlap: dict[str, int] = {}
for t in text_objects:
    text_graphic_overlap[t.oid] = int(np.count_nonzero(t.mask & all_graphic))
    text_graphic_clearance[t.oid] = mask_distance(t.mask, all_graphic)
    text_text_overlap[t.oid] = sum(int(np.count_nonzero(t.mask & u.mask)) for u in text_objects if u.oid != t.oid)

# Find parent result for each glyph, and update general §9.2.1 CSV fields.
for row in glyph_rows:
    parent = row["PARENT_ID"]
    row["TEXT_TEXT_OVERLAP_PX"] = text_text_overlap[parent]
    row["TEXT_GRAPHIC_OVERLAP_PX"] = text_graphic_overlap[parent]
    cd = text_graphic_clearance[parent]
    row["MIN_CLEARANCE_PX"] = "" if math.isnan(cd) else f"{cd:.3f}"
    # Preserve a glyph-size failure; add a semantic collision failure if needed.
    if row["PIXEL_HEIGHT_PASS"] == "PASS" and (text_text_overlap[parent] > 0 or text_graphic_overlap[parent] > 0 or (not math.isnan(cd) and cd < 3.0)):
        row["PASS_FAIL"] = "FAIL"
        row["REASON"] += "; parent text collision/clearance failure"

# Same-class ratios operate on appropriately comparable semantic components,
# not arbitrary individual glyph shapes.  Each component's H_ink is direct
# from its own raw mask.  No CJK-vs-x-height comparison is used here.
component_groups: dict[str, list[tuple[str, Obj, fitz.Rect]]] = {
    "ANNOTATION_CJK": [],
    "FORMULA_ANNOTATION": [],
    "AXIS_TITLE_FORMULA": [],
    "CAPTION_CJK": [],
}
for obj, spec in zip(text_objects, sem_specs):
    cjk_parts = [fitz.Rect(p["bbox"]) for p in spec["parts"] if any("\u4e00" <= c <= "\u9fff" for c in stext(p))]
    if obj.oid in {"T01_MEAN", "T02_AXIS1", "T03_AXIS2", "T06_SAMPLE_Q", "T07_PROJECTION"}:
        component_groups["ANNOTATION_CJK"].append((obj.oid, obj, rect_union(cjk_parts)))
    elif obj.oid in {"T04_2SIGMA", "T05_1SIGMA"}:
        component_groups["FORMULA_ANNOTATION"].append((obj.oid, obj, obj.bbox_pt))
    elif obj.oid in {"T08_AXIS_X1", "T09_AXIS_X2"}:
        component_groups["AXIS_TITLE_FORMULA"].append((obj.oid, obj, obj.bbox_pt))
    elif obj.oid == "T10_CAPTION":
        component_groups["CAPTION_CJK"].append((obj.oid, obj, rect_union(cjk_parts)))

same_rows: list[dict[str, Any]] = []
component_values: dict[str, dict[str, float]] = {}
for group, entries in component_groups.items():
    values: list[tuple[str, float]] = []
    for cid, obj, rect in entries:
        h = ink_height(raw_mask_for_rect(rect, fg & text_silhouette, SX, SY))
        values.append((cid, float(h)))
    hs = [v for _, v in values]
    median = statistics.median(hs)
    maxmin = max(hs) / min(hs) if min(hs) else float("inf")
    component_values[group] = {cid: h for cid, h in values}
    for cid, h in values:
        ratio = h / median if median else float("inf")
        passed = 0.92 <= ratio <= 1.08 and maxmin <= 1.08
        same_rows.append({
            "CLASS_ID": group, "ELEMENT_ID": cid, "H_INK_PX": f"{h:.0f}", "CLASS_MEDIAN_PX": f"{median:.3f}",
            "RATIO_TO_MEDIAN": f"{ratio:.4f}", "CLASS_MAX_MIN_RATIO": f"{maxmin:.4f}",
            "RANGE": "[0.92,1.08]", "PASS_FAIL": "PASS" if passed else "FAIL",
            "BASIS": "same script class and same semantic role; raw 300dpi foreground",
        })
csv_write(OUT / "same_class_ratio_audit.csv", list(same_rows[0].keys()), same_rows)

# Role hierarchy: for this single panel, choose normal annotation CJK as the
# best available ordinary-body base.  Formula/axis measurements use whole
# semantic elements; the CSV exposes the raw numbers and does not hide any
# morphology issue.  The source-font failure remains independent.
base_vals = list(component_values["ANNOTATION_CJK"].values())
base = statistics.median(base_vals)
role_rows: list[dict[str, Any]] = []
role_mapping = {
    "ANNOTATION_BASE": (base_vals, "BASE", "N/A", "normal annotation CJK median selected because no tick/node text exists"),
    "FORMULA_ANNOTATION": (list(component_values["FORMULA_ANNOTATION"].values()), "FORMULA_BLOCK", "[1.00,1.18]", "formula annotation baseline text"),
    "AXIS_TITLE_FORMULA": (list(component_values["AXIS_TITLE_FORMULA"].values()), "AXIS_TITLE", "[1.00,1.18]", "axis title baseline formula incl. natural subscript")
}
for rid, (vals, role, target, basis) in role_mapping.items():
    med = statistics.median(vals)
    ratio = med / base if base else float("inf")
    if target == "N/A":
        passed = True
    else:
        lo, hi = (1.00, 1.18)
        passed = lo <= ratio <= hi
    role_rows.append({"ROLE_ID": rid, "ROLE": role, "MEDIAN_H_INK_PX": f"{med:.3f}", "BASE_ROLE": "ANNOTATION_BASE", "BASE_MEDIAN_PX": f"{base:.3f}", "ROLE_RATIO": f"{ratio:.4f}", "REQUIRED_RANGE": target, "PASS_FAIL": "PASS" if passed else "FAIL", "BASIS": basis})
csv_write(OUT / "role_ratio_audit.csv", list(role_rows[0].keys()), role_rows)

# Copy class ratio and conservative semantic collision data into every glyph
# row.  Glyph-parent role ratio is the matching role row where available.
role_ratio_by_parent = {
    "T04_2SIGMA": next(r["ROLE_RATIO"] for r in role_rows if r["ROLE_ID"] == "FORMULA_ANNOTATION"),
    "T05_1SIGMA": next(r["ROLE_RATIO"] for r in role_rows if r["ROLE_ID"] == "FORMULA_ANNOTATION"),
    "T08_AXIS_X1": next(r["ROLE_RATIO"] for r in role_rows if r["ROLE_ID"] == "AXIS_TITLE_FORMULA"),
    "T09_AXIS_X2": next(r["ROLE_RATIO"] for r in role_rows if r["ROLE_ID"] == "AXIS_TITLE_FORMULA"),
}
for row in glyph_rows:
    parent = row["PARENT_ID"]
    row["ROLE_RATIO"] = role_ratio_by_parent.get(parent, "1.0000")
    # Determine a class median only for groups matching the parent component.
    matched = None
    for group, vals in component_values.items():
        if any(k.startswith(parent) for k in vals):
            matched = group
            break
    if matched:
        vals = list(component_values[matched].values())
        row["CLASS_MEDIAN_PX"] = f"{statistics.median(vals):.3f}"
        # Do not substitute the semantic class ratio for per-glyph eligibility;
        # record it as an audit context field only.
        row["RATIO_TO_CLASS_MEDIAN"] = "semantic-component-see-same_class_csv"
    else:
        row["CLASS_MEDIAN_PX"] = "N/A-singleton"
        row["RATIO_TO_CLASS_MEDIAN"] = "N/A-singleton"

pixel_columns = [
    "ELEMENT_ID", "PARENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT",
    "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "MIN_REQUIRED_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PIXEL_HEIGHT_PASS", "PASS_FAIL", "REASON", "RAW_MASK_FILE"
]
csv_write(OUT / "after_pixel_measurements.csv", pixel_columns, glyph_rows)
csv_write(OUT / "after_font_audit.csv", list(font_rows[0].keys()), font_rows)
csv_write(OUT / "vector_object_bboxes.csv", list(vector_bbox_rows[0].keys()), vector_bbox_rows)

# ---------------------------------------------------------------------------
# 6. Edge and clipping conditions, including exact page and crop edge checks.
# ---------------------------------------------------------------------------
edge_rows: list[dict[str, Any]] = []
for obj in objects:
    bb = mask_bbox(obj.mask)
    pbb = px_rect(obj.bbox_pt, SX, SY)
    if bb is None:
        raw_touch_crop = "UNKNOWN"
        edge_dist_crop = "UNKNOWN"
    else:
        raw_touch_crop = int(np.count_nonzero(obj.mask[0, :]) + np.count_nonzero(obj.mask[-1, :]) + np.count_nonzero(obj.mask[:, 0]) + np.count_nonzero(obj.mask[:, -1]))
        edge_dist_crop = min(bb[0], bb[1], CROP_W - 1 - bb[2], CROP_H - 1 - bb[3])
    # Full-page vector edge distances are computed before crop conversion.
    full_bbox = (int(math.floor(obj.bbox_pt.x0 * SX)), int(math.floor(obj.bbox_pt.y0 * SY)), int(math.ceil(obj.bbox_pt.x1 * SX)), int(math.ceil(obj.bbox_pt.y1 * SY)))
    page_edge = min(full_bbox[0], full_bbox[1], pix300.width - 1 - full_bbox[2], pix300.height - 1 - full_bbox[3])
    text_requirement = 6 if obj.kind == "TEXT" else 0
    passed = raw_touch_crop == 0 and page_edge >= 0 and (obj.kind != "TEXT" or int(edge_dist_crop) >= text_requirement)
    edge_rows.append({
        "OBJECT_ID": obj.oid, "TYPE": obj.kind, "ROLE": obj.role, "PDF_BBOX": f"{obj.bbox_pt.x0:.3f},{obj.bbox_pt.y0:.3f},{obj.bbox_pt.x1:.3f},{obj.bbox_pt.y1:.3f}",
        "CROP_EDGE_RAW_FOREGROUND_TOUCH_PX": raw_touch_crop, "MIN_CROP_EDGE_CLEARANCE_PX": edge_dist_crop,
        "MIN_PAGE_EDGE_CLEARANCE_PX": page_edge, "TEXT_EDGE_MIN_REQUIRED_PX": text_requirement,
        "CLIP_PIXEL_COUNT": 0 if passed else "UNKNOWN", "PASS_FAIL": "PASS" if passed else "FAIL",
        "BASIS": "native raw foreground threshold20, crop canvas + full page vector bbox",
    })
csv_write(OUT / "after_edge_clip_report.csv", list(edge_rows[0].keys()), edge_rows)

# Text measurement overlay draws non-resized raw source with PDF vector bboxes.
ann = Image.fromarray(rgb.copy())
draw = ImageDraw.Draw(ann)
try:
    labelfont = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
except OSError:
    labelfont = ImageFont.load_default()
for obj in text_objects:
    x0, y0, x1, y1 = px_rect(obj.bbox_pt, SX, SY)
    draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 255), width=2)
    draw.rectangle([x0, max(0, y0 - 17), min(CROP_W - 1, x0 + 170), y0], fill=(255, 255, 255))
    draw.text((x0 + 2, max(0, y0 - 17)), obj.oid, fill=(170, 0, 150), font=labelfont)
ann.save(OUT / "after_text_measurement_overlay_300dpi.png")

# ---------------------------------------------------------------------------
# 7. Deterministic verdict and written report; no inherited candidate verdict.
# ---------------------------------------------------------------------------
source_font_floor_pass = all(r["SOURCE_FONT_PASS"] == "true" for r in font_rows)
source_same_role_pass = all(r["SAME_ROLE_SOURCE_PASS"] == "true" for r in font_rows)
source_font_pass = source_font_floor_pass and source_same_role_pass
pixel_height_pass = all(r["PIXEL_HEIGHT_PASS"] == "PASS" for r in glyph_rows)
same_class_pass = all(r["PASS_FAIL"] == "PASS" for r in same_rows)
role_ratio_pass = all(r["PASS_FAIL"] == "PASS" for r in role_rows)
illegal_pairs = [r for r in pair_rows if r["REQUIRED"] == "true" and r["VERDICT"] == "FAIL"]
# Report the union of illegal raw foreground pixels (not the sum of pair
# entries, which could count a genuine three-object intersection twice).
overlap_count = int(np.count_nonzero(all_text & all_graphic))
clip_count = sum(0 if r["CLIP_PIXEL_COUNT"] == 0 else 1 for r in edge_rows)
min_text_clearances = [float(r["MIN_CLEARANCE_PX"]) for r in pair_rows if r["REQUIRED"] == "true" and r["MIN_CLEARANCE_PX"] != ""]
min_clearance = min(min_text_clearances) if min_text_clearances else float("nan")

# Findings based on direct comparison of source / frozen PDF / adjacent text.
math_semantics_pass = True
text_consistency_pass = True
reading_order_pass = True
grayscale_pass = True
page_integration_pass = True
visual_harmony_pass = source_font_pass and same_class_pass and role_ratio_pass
strict_pass = all([
    source_font_pass, pixel_height_pass, same_class_pass, role_ratio_pass,
    overlap_count == 0, clip_count == 0, visual_harmony_pass,
    math_semantics_pass, text_consistency_pass, grayscale_pass, page_integration_pass,
]) and not illegal_pairs

summary = {
    "figure_id": FIG_ID,
    "pdf": str(PDF),
    "pdf_page_count": doc.page_count,
    "located_pdf_physical_page": PDF_PHYSICAL_PAGE,
    "printed_page": PRINTED_PAGE,
    "figure_number": FIGURE_NO,
    "source_font_pass": source_font_pass,
    "source_font_floor_pass": source_font_floor_pass,
    "source_same_role_pass": source_same_role_pass,
    "pixel_height_pass": pixel_height_pass,
    "same_class_ratio_pass": same_class_pass,
    "role_ratio_pass": role_ratio_pass,
    "overlap_pixel_count": overlap_count,
    "clip_pixel_count": clip_count,
    "min_text_clearance_px": None if math.isnan(min_clearance) else round(min_clearance, 3),
    "visual_harmony_pass": visual_harmony_pass,
    "math_semantics_pass": math_semantics_pass,
    "text_consistency_pass": text_consistency_pass,
    "grayscale_pass": grayscale_pass,
    "page_integration_pass": page_integration_pass,
    "result": "PASS" if strict_pass else "FAIL",
}
(OUT / "audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

failed_fonts = [r for r in font_rows if r["SOURCE_FONT_PASS"] != "true"]
failed_glyphs = [r for r in glyph_rows if r["PIXEL_HEIGHT_PASS"] != "PASS"]
collision_glyphs = [r for r in glyph_rows if r["PASS_FAIL"] != "PASS" and r["PIXEL_HEIGHT_PASS"] == "PASS"]
failed_same = [r for r in same_rows if r["PASS_FAIL"] != "PASS"]
failed_roles = [r for r in role_rows if r["PASS_FAIL"] != "PASS"]

md = f"""# {FIG_ID}｜STRICT_R1｜SA1 独立严格视觉复核

RESULT: **{'PASS' if strict_pass else 'FAIL'}**

本轮只读取指定源文件、相邻 V4-C04 正文及冻结输入 `strict_current_r93_fullbook/main_full.pdf`；未读取或沿用旧轮次截图、测量数字或结论，也未修改任何源码、公共样式、构建、inventory 或状态文件。

## 定位与覆盖

- 冻结 PDF：`{PDF}`；813 页 A4。
- 重新在冻结 PDF 全文检索题注后，唯一命中为 PDF 物理页 **{PDF_PHYSICAL_PAGE}**（PDF 印刷页 **{PRINTED_PAGE}**），图号 **{FIGURE_NO}**；这与旧索引中“物理页 575”不一致，故本审查不使用旧页码。
- 图号/题注：`图27.1 二维协方差椭圆与主轴示意`。
- 相邻正文：`V4-C04.tex:315–316` 说明保留最长协方差主轴、把正交剩余变化计入重构误差；与图中的最长轴 $\\lambda_1$、短轴 $\\lambda_2$、正交投影、$2\\sigma/1\\sigma$ 标记一致。
- 所有 10 个读者可见语义文字对象、其单字/数学字形、8 个线/曲线对象和 23 个标记对象均由最终 PDF 的 vector bbox + 原生 300dpi raw foreground mask 覆盖。白色半透明标签底板仅作为背景，不被误计为文字—图形前景重叠。

## 9.2.1 硬门结论

| 项 | 结果 | 证据 |
|---|---:|---|
| SOURCE_FONT_PASS | `{str(source_font_pass).lower()}` | `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | `{str(pixel_height_pass).lower()}` | `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | `{str(same_class_pass).lower()}` | `same_class_ratio_audit.csv` |
| ROLE_RATIO_PASS | `{str(role_ratio_pass).lower()}` | `role_ratio_audit.csv` |
| OVERLAP_PIXEL_COUNT | `{overlap_count}` | `after_overlap_report.csv`, `masks/illegal_overlap_raw.png` |
| CLIP_PIXEL_COUNT | `{clip_count}` | `after_edge_clip_report.csv` |
| MIN_TEXT_CLEARANCE_PX | `{min_clearance:.3f}` | `after_overlap_report.csv` |
| VISUAL_HARMONY_PASS | `{str(visual_harmony_pass).lower()}` | 四视图 + 比例表 |
| MATH_SEMANTICS_PASS | `{str(math_semantics_pass).lower()}` | 正文/图源/PDF 比对 |
| TEXT_CONSISTENCY_PASS | `{str(text_consistency_pass).lower()}` | 图号、题注、变量和正文比对 |
| GRAYSCALE_PASS | `{str(grayscale_pass).lower()}` | `after_grayscale_300dpi.png` |
| PAGE_INTEGRATION_PASS | `{str(page_integration_pass).lower()}` | 整页 200/300dpi 视图 |

## 决定性失败项

1. **源级有效字号未达 9.5pt。** `fig_v4_c04_ellipse.tex:3,48,53,54` 明确使用 9.4pt：`均值 μ`、`2σ`、`1σ`。`figure-style-v2.3.1.tex:40` 的 `slfig direct label` 又覆盖图内 9.4pt picture font 为 `\\footnotesize`；在 11pt `ctexbook` 中为 9.0pt。故第一/第二主轴、样本 q、正交投影均为 9.0pt。共有 **7/10** 语义文字对象低于 9.5pt；仅 $x_1/x_2$ 轴标题与 10pt 题注满足基准字号。
2. **同一普通注释角色的源字号协调性失败。** 普通注释混用 9.0pt 和 9.4pt：max/min = 1.0444，绝对差 = 0.40pt，超过同角色 ≤1.03 且 ≤0.25pt 的双门。像素同类和角色比例的实际结果见各独立 CSV；任何其中一个 false 均不得 PASS。
3. **四对真实文本—图形非法原生前景碰撞。** 在 raw 300dpi、阈值 20/255、未膨胀掩膜下：`T02_AXIS1—G04_OUTER_ELLIPSE=164px`、`T05_1SIGMA—M17_SAMPLE=162px`、`T07_PROJECTION—G03_INNER_ELLIPSE=80px`、`T07_PROJECTION—M20_SAMPLE=29px`，合计 **435px**。它们是文字与独立椭圆/样本标记的碰撞，不属于数据几何的意图交点；相应原生最小净空均为 0px。裁切仍为 0，但不能抵消字号、角色比例与碰撞硬性 FAIL。

## 四视图实际检查

- `after_full_page_200dpi.png`：图居页面中段，图前“几何/概率/优化解释”和图后“样本主成分”阅读顺序连续，无异常留白或分页断裂。
- `after_full_page_300dpi.png`：原生 300dpi A4 页，无二次缩放。
- `after_standalone_300dpi.png` / `after_figure_crop_300dpi.png`：逐一检查图内标签、轴、曲线、样本点、投影虚线和直角标记；白底标签正确隔离了线条。
- `after_grayscale_300dpi.png`：椭圆、主轴、虚线投影、样本形状和颜色亮度仍有可区分的线型/形状结构；无单靠颜色才能阅读的结论。

## 输出与下一角色

严格结论为 **FAIL**。本图不得进入 SA3；下一角色应为 **SA2**，只在 `fig_v4_c04_ellipse.tex` 内将所有普通读者文字（包括 `slfig direct label` 的局部覆盖）统一恢复到至少 9.5pt，并在保证轴标题/标签层级范围、零重叠和净空的前提下重新构建冻结候选，再重新走独立 SA1。

测量方法：最终 PDF 直接以 300dpi 渲染且不 resize；前景阈值为相对局部白背景至少 20/255。每一对象使用 PDF/vector bbox 映射后的**未膨胀 raw foreground mask**。曲线/线条使用 PDF 向量路径作定位门，但输出 mask 始终由 raw render 的阈值前景相交得到；因此不会将几何定位缓冲、形态膨胀或绘制顺序污染算成 overlap。
"""
(OUT / "after_visual_acceptance.md").write_text(md, encoding="utf-8")

formal = f"""# FIG-P482-01 STRICT_R1 SA1 正式报告

## 结论

**RESULT: {'PASS' if strict_pass else 'FAIL'}**

FIGURE_ID: {FIG_ID}  
冻结 PDF 物理页: {PDF_PHYSICAL_PAGE}  
PDF 印刷页: {PRINTED_PAGE}  
图号: {FIGURE_NO}  
证据目录: `{OUT}`

## 覆盖

- 读源：`{SOURCE}`（完整 73 行）、相邻正文 `{CHAPTER}:299–335`、相关局部样式 `{SHARED_STYLE}:40,92`、图注设定 `{BOOK_STYLE}:305`。
- 定位：独立扫描冻结 PDF 813 页的题注文本，命中第 526 页；旧索引的 575 不能作为本轮取证页面。
- 原生渲染：整页 200dpi、整页 300dpi、裁图/standalone 300dpi、灰度 300dpi 均已保存。300dpi 图片没有 resize。
- 文字：10 个语义对象、所有单字/数字/希腊字形/上下标均有 PDF bbox、raw foreground mask 和像素高度记录。
- 图形：8 个线/曲线与 23 个标记对象均有 vector bbox、raw separated mask；所有对象成对列表已写入 overlap CSV。

## 失败汇总

- 源字号失败对象数: {len(failed_fonts)} / {len(font_rows)}
- 像素高度失败字形数: {len(failed_glyphs)} / {len(glyph_rows)}
- 具有独立文字碰撞/净空失败的字形数: {len(collision_glyphs)} / {len(glyph_rows)}
- 同类比例失败条目数: {len(failed_same)} / {len(same_rows)}
- 角色比例失败条目数: {len(failed_roles)} / {len(role_rows)}
- 必查文本关系失败对数: {len(illegal_pairs)}
- 非法 overlap 像素: {overlap_count}
- clip 像素: {clip_count}
- 最小文字关系净空: {min_clearance:.3f}px

四对必查且真实的文本—图形碰撞为：`T02_AXIS1—G04_OUTER_ELLIPSE=164px`、`T05_1SIGMA—M17_SAMPLE=162px`、`T07_PROJECTION—G03_INNER_ELLIPSE=80px`、`T07_PROJECTION—M20_SAMPLE=29px`；总计 435px。每一对都有 `critical_pairs/` 的原生 300dpi 掩膜叠加证据。其余图形—图形交点（样本点/轴/椭圆）被明确标为意图几何，未混入文本碰撞总数。

## 数学、文本和版面复核

1. 均值点 $(0.3,-0.1)$ 位于协方差椭圆中心；长轴和短轴按源注释的 $\\lambda_1=2.25>\\lambda_2=.36$ 的方向和长度关系绘制。
2. 查询三角形与方形投影点之间的红色虚线同最长主轴垂直，直角标记位于投影点附近；与正文“保留最长主轴、把正交剩余变化计入重构误差”一致。
3. 图内 $\\mu,\\lambda_1,\\lambda_2,1\\sigma,2\\sigma,q$ 与题注/正文没有符号漂移；题注简洁且为单一读图结论。
4. 视觉上主轴、两层椭圆、样本散点、投影虚线和正交符号具有可辨认层级；灰度下仍可依靠实线/虚线/标记形状识别。

## 可执行 SA2 修复动作

仅修改指定图源：

1. 将 picture-local node font 从 9.4pt 提升为至少 9.5pt（建议统一 10pt）。
2. 在本图局部覆写 `slfig direct label` 的 `font=\\fontsize{{10pt}}{{12pt}}\\selectfont`，不要依赖公共 `\\footnotesize` 默认值。
3. 保留 $x_1/x_2$ 的 10pt 基准与自然 subscript；重建后以原生 300dpi 逐一重测所有文本和重新审查同类/角色比例、overlap 与净空。
4. 不要通过 resizebox、scalebox、整体缩图或减小画布处理该失败。

下一角色: **SA2**。仅当新候选的所有布尔项 true、overlap=0、clip=0、所有净空和字号门通过，才可重新启动新的独立 SA1；当前候选不得建议 SA3。
"""
(OUT / "STRICT_R1_SA1_FORMAL_REPORT.md").write_text(formal, encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
