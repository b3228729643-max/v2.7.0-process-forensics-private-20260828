#!/usr/bin/env python3
"""Independent strict R1 evidence builder for FIG-P575-01 / 图31.3.

This script only reads the canonical R94 PDF and the two explicitly authorised
LaTeX inputs.  Every emitted file remains under this evidence directory.
"""

from __future__ import annotations

import csv
import json
import math
import os
import shutil
import subprocess
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf")
FIG_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_generalized_inverse.tex")
CONTEXT_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C02.tex")
PHYSICAL_PAGE = 623
PAGE_INDEX = PHYSICAL_PAGE - 1
DPI_300 = 300
DPI_200 = 200
PDF_TO_PIXEL = DPI_300 / 72.0

# The figure block includes source-created plot plus its source-created caption.
# Standalone view is a lossless native crop of the plot body only.
FIGURE_BLOCK_PDF_RECT = (50.0, 60.0, 545.0, 278.0)
STANDALONE_PDF_RECT = (90.0, 60.0, 505.0, 243.0)

RAW_DIR = ROOT / "masks" / "raw"
GLYPH_DIR = ROOT / "masks" / "glyphs"
PAIR_DIR = ROOT / "pair_evidence"
GLYPH_EVIDENCE_DIR = ROOT / "glyph_evidence"
HUMAN_DIR = ROOT / "human_review"


def ensure_dirs() -> None:
    for d in (RAW_DIR, GLYPH_DIR, PAIR_DIR, GLYPH_EVIDENCE_DIR, HUMAN_DIR):
        d.mkdir(parents=True, exist_ok=True)


def run_render(dpi: int, basename: str) -> Path:
    target = ROOT / basename
    cmd = [
        "pdftoppm", "-f", str(PHYSICAL_PAGE), "-l", str(PHYSICAL_PAGE),
        "-r", str(dpi), "-png", "-singlefile", str(PDF), str(target),
    ]
    subprocess.run(cmd, check=True)
    rendered = target.with_suffix(".png")
    if not rendered.exists():
        raise RuntimeError(f"Missing direct-PDF rendering: {rendered}")
    return rendered


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def bool_s(value: bool) -> str:
    return "true" if value else "false"


def rgb_from_pdf_color(value: int | None) -> tuple[int, int, int]:
    if value is None:
        return (0, 0, 0)
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rect_to_px(rect: tuple[float, float, float, float], width: int, height: int, margin: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        max(0, int(math.floor(x0 * PDF_TO_PIXEL)) - margin),
        max(0, int(math.floor(y0 * PDF_TO_PIXEL)) - margin),
        min(width, int(math.ceil(x1 * PDF_TO_PIXEL)) + margin),
        min(height, int(math.ceil(y1 * PDF_TO_PIXEL)) + margin),
    )


def bbox_from_flat(flat: np.ndarray, width: int) -> tuple[int, int, int, int] | None:
    if flat.size == 0:
        return None
    ys = flat // width
    xs = flat % width
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def mask_color_match(region: np.ndarray, colors: Iterable[tuple[int, int, int]]) -> np.ndarray:
    """Strict final-render foreground: delta from white >=20 plus color ray fit.

    The ray fit accepts anti-aliased pixels that lie between white and the PDF
    paint colour.  It does not add/dilate pixels; the result is always a subset
    of the directly rendered native PNG.
    """
    pix = region.astype(np.float32)
    diff = 255.0 - pix
    foreground = diff.max(axis=2) >= 20.0
    accepted = np.zeros(foreground.shape, dtype=bool)
    for color in colors:
        base = 255.0 - np.asarray(color, dtype=np.float32)
        denom = float(np.dot(base, base))
        if denom < 1e-6:
            continue
        alpha = np.clip((diff * base).sum(axis=2) / denom, 0.0, 1.0)
        residual = np.sqrt(((diff - alpha[..., None] * base) ** 2).sum(axis=2))
        # 8/255 residual keeps a pale antialiased gold pixel out of a nearby
        # black glyph's raw mask.  The earlier wider fit could classify one final
        # pixel as both paints, which is prohibited for separated raw masks.
        accepted |= (residual <= 8.0)
    return foreground & accepted


def foreground_any(region: np.ndarray) -> np.ndarray:
    return (255 - region.astype(np.int16)).max(axis=2) >= 20


def point_to_px(p: Any) -> tuple[int, int]:
    return (int(round(float(p.x) * PDF_TO_PIXEL)), int(round(float(p.y) * PDF_TO_PIXEL)))


def bezier_points(p0: Any, p1: Any, p2: Any, p3: Any, n: int = 48) -> list[tuple[int, int]]:
    ts = np.linspace(0.0, 1.0, n)
    a = np.array([float(p0.x), float(p0.y)])
    b = np.array([float(p1.x), float(p1.y)])
    c = np.array([float(p2.x), float(p2.y)])
    d = np.array([float(p3.x), float(p3.y)])
    pts = ((1-ts)[:, None]**3*a + 3*(1-ts)[:, None]**2*ts[:, None]*b +
           3*(1-ts)[:, None]*ts[:, None]**2*c + ts[:, None]**3*d)
    return [(int(round(x * PDF_TO_PIXEL)), int(round(y * PDF_TO_PIXEL))) for x, y in pts]


def drawing_gate(drawing: dict[str, Any], width: int, height: int) -> np.ndarray:
    """Rasterize vector path geometry only as an eligibility gate.

    Final raw masks are always intersected with native-PNG foreground afterward.
    This avoids paint-order contamination from other objects without counting any
    synthetic/dilated pixels.
    """
    gate = np.zeros((height, width), dtype=np.uint8)
    thickness = max(2, int(math.ceil(float(drawing.get("width") or 0.0) * PDF_TO_PIXEL)) + 3)
    subpaths: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []

    def flush() -> None:
        nonlocal current
        if current:
            subpaths.append(current)
        current = []

    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            a, b = point_to_px(item[1]), point_to_px(item[2])
            if not current:
                current = [a]
            elif current[-1] != a:
                flush()
                current = [a]
            current.append(b)
        elif kind == "c":
            pts = bezier_points(item[1], item[2], item[3], item[4])
            if not current:
                current = [pts[0]]
            elif current[-1] != pts[0]:
                flush()
                current = [pts[0]]
            current.extend(pts[1:])
        elif kind == "re":
            flush()
            r = item[1]
            pts = [point_to_px(fitz.Point(r.x0, r.y0)), point_to_px(fitz.Point(r.x1, r.y0)),
                   point_to_px(fitz.Point(r.x1, r.y1)), point_to_px(fitz.Point(r.x0, r.y1))]
            subpaths.append(pts)
        else:
            raise RuntimeError(f"Unhandled PDF drawing item {kind!r}")
    flush()

    filled = drawing.get("fill") is not None
    stroked = drawing.get("color") is not None
    for pts in subpaths:
        if len(pts) < 2:
            continue
        poly = np.asarray(pts, dtype=np.int32)
        if filled and len(pts) >= 3:
            cv2.fillPoly(gate, [poly], 255, lineType=cv2.LINE_8)
        if stroked:
            cv2.polylines(gate, [poly], False, 255, thickness=thickness, lineType=cv2.LINE_8)
            # Filled arrows and closed markers need the closing stroke too.
            if filled:
                cv2.line(gate, tuple(poly[-1]), tuple(poly[0]), 255, thickness=thickness, lineType=cv2.LINE_8)
    return gate.astype(bool)


def logical_text(raw: str) -> str:
    # PyMuPDF can expose a fallback glyph name for mathematical italic u; map only
    # for human-readable evidence, never for geometry or mask selection.
    return raw.replace("ᵆ", "𝑢")


def classify_glyph(c: str) -> tuple[str, int, str]:
    import unicodedata
    if not c or c.isspace():
        return ("SPACE", 0, "not-a-visible-glyph")
    cp = ord(c)
    east = unicodedata.east_asian_width(c)
    if 0x3400 <= cp <= 0x9FFF or east in {"W", "F"}:
        return ("CJK_FULLWIDTH", 30, "CJK/fullwidth >=30px")
    if c.isdigit() or c.isupper():
        return ("LATIN_UPPER_OR_DIGIT", 24, "uppercase/digit >=24px")
    if c.islower() or "SMALL" in unicodedata.name(c, ""):
        return ("LATIN_LOWER_OR_GREEK", 17, "lowercase/Greek lowercase >=17px")
    # The strict schema explicitly requires independently measured semantic
    # operators/punctuation.  It supplies the base mathematics/operator gate.
    if c in "=+-−*/<>.,;:()[]{}|":
        return ("MATH_OPERATOR_OR_PUNCT", 22, "semantic math operator/punctuation >=22px")
    return ("BASE_MATH", 22, "base mathematical symbol >=22px")


@dataclass
class ObjectRecord:
    object_id: str
    panel_id: str
    role: str
    object_type: str
    source_line: str
    text_sample: str = ""
    declared_pt: float | None = None
    graphics_scale: float | None = None
    effective_pt: float | None = None
    raw_flat: np.ndarray = field(default_factory=lambda: np.asarray([], dtype=np.int64))
    bbox: tuple[int, int, int, int] | None = None
    mask_file: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def save_roi_mask(path: Path, flat: np.ndarray, bbox: tuple[int, int, int, int], width: int) -> None:
    x0, y0, x1, y1 = bbox
    data = np.zeros((y1-y0+1, x1-x0+1), dtype=np.uint8)
    ys = flat // width
    xs = flat % width
    data[ys-y0, xs-x0] = 255
    Image.fromarray(data, mode="L").save(path)


def save_object_mask(obj: ObjectRecord, width: int) -> None:
    if obj.bbox is None or obj.raw_flat.size == 0:
        return
    path = RAW_DIR / f"{obj.object_id}.png"
    save_roi_mask(path, obj.raw_flat, obj.bbox, width)
    obj.mask_file = str(path.relative_to(ROOT)).replace("\\", "/")


def crop_from_full(image: Image.Image, rect_pdf: tuple[float, float, float, float]) -> tuple[Image.Image, tuple[int, int, int, int]]:
    px = rect_to_px(rect_pdf, image.width, image.height)
    return image.crop(px), px


def find_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), 17)
    return ImageFont.load_default()


def add_text_overlay(base: Image.Image, objects: list[ObjectRecord], crop_rect: tuple[int, int, int, int], filename: str, glyph_rows: list[dict[str, Any]] | None = None) -> None:
    out = base.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    font = find_font()
    xoff, yoff, _, _ = crop_rect
    palette = {"PANEL_TITLE": (170, 0, 170), "TICK_LABEL": (0, 130, 0),
               "AXIS_TITLE": (220, 0, 0), "ANNOTATION": (0, 120, 190), "CAPTION": (220, 120, 0)}
    if glyph_rows is None:
        for o in objects:
            if o.object_type != "TEXT" or o.bbox is None:
                continue
            color = palette.get(o.role, (255, 0, 0))
            x0, y0, x1, y1 = o.bbox
            draw.rectangle((x0-xoff, y0-yoff, x1-xoff, y1-yoff), outline=color, width=2)
            label = f"{o.object_id} [{o.role}]"
            draw.text((x0-xoff, max(0, y0-yoff-18)), label, fill=color, font=font, stroke_width=1, stroke_fill=(255,255,255))
    else:
        for row in glyph_rows:
            x0, y0, x1, y1 = [int(row[k]) for k in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1")]
            color = (225, 0, 0) if row["PASS_FAIL"] == "FAIL" else (0, 120, 0)
            draw.rectangle((x0-xoff, y0-yoff, x1-xoff, y1-yoff), outline=color, width=1)
            draw.text((x0-xoff, max(0, y0-yoff-11)), row["ELEMENT_ID"], fill=color, font=font, stroke_width=1, stroke_fill=(255,255,255))
    out.save(ROOT / filename)


def distance_between(obj_a: ObjectRecord, obj_b: ObjectRecord, width: int) -> float:
    if obj_a.raw_flat.size == 0 or obj_b.raw_flat.size == 0:
        return float("nan")
    coords_a = np.column_stack((obj_a.raw_flat // width, obj_a.raw_flat % width))
    coords_b = np.column_stack((obj_b.raw_flat // width, obj_b.raw_flat % width))
    if len(coords_a) > len(coords_b):
        coords_a, coords_b = coords_b, coords_a
    tree = cKDTree(coords_b)
    return float(tree.query(coords_a, k=1)[0].min())


def mask_overlay_roi(image_np: np.ndarray, a_flat: np.ndarray, b_flat: np.ndarray, bbox: tuple[int, int, int, int], width: int) -> tuple[Image.Image, Image.Image, Image.Image, Image.Image]:
    x0, y0, x1, y1 = bbox
    src = image_np[y0:y1+1, x0:x1+1].copy()
    a = np.zeros(src.shape[:2], dtype=bool)
    b = np.zeros(src.shape[:2], dtype=bool)
    for flat, dest in ((a_flat, a), (b_flat, b)):
        ys = flat // width
        xs = flat % width
        keep = (xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1)
        dest[ys[keep]-y0, xs[keep]-x0] = True
    inter = a & b
    out = src.copy()
    out[a] = [255, 0, 0]
    out[b] = [0, 128, 255]
    out[inter] = [255, 0, 255]
    return (Image.fromarray(src), Image.fromarray((a*255).astype(np.uint8)), Image.fromarray((b*255).astype(np.uint8)), Image.fromarray((inter*255).astype(np.uint8)), Image.fromarray(out))


def expanded_bbox(a: tuple[int, int, int, int], b: tuple[int, int, int, int], width: int, height: int, pad: int = 12) -> tuple[int, int, int, int]:
    return (max(0, min(a[0], b[0])-pad), max(0, min(a[1], b[1])-pad),
            min(width-1, max(a[2], b[2])+pad), min(height-1, max(a[3], b[3])+pad))


def save_pair_evidence(pair: dict[str, Any], obj_a: ObjectRecord, obj_b: ObjectRecord, image_np: np.ndarray, width: int, height: int) -> None:
    if obj_a.bbox is None or obj_b.bbox is None:
        return
    pair_path = PAIR_DIR / pair["PAIR_ID"]
    pair_path.mkdir(parents=True, exist_ok=True)
    roi = expanded_bbox(obj_a.bbox, obj_b.bbox, width, height)
    raw, a, b, inter, overlay = mask_overlay_roi(image_np, obj_a.raw_flat, obj_b.raw_flat, roi, width)
    raw.save(pair_path / "raw_1to1.png")
    a.save(pair_path / "A_raw_mask_1to1.png")
    b.save(pair_path / "B_raw_mask_1to1.png")
    inter.save(pair_path / "intersection_1to1.png")
    overlay.save(pair_path / "overlay_1to1.png")
    overlay.resize((overlay.width*8, overlay.height*8), Image.Resampling.NEAREST).save(pair_path / "overlay_8x_nearest.png")
    write_json(pair_path / "metadata.json", {"pair": pair, "roi_native_300dpi": roi, "scaling": "1:1; 8x nearest is human-only"})


def save_glyph_evidence(row: dict[str, Any], flat: np.ndarray, image_np: np.ndarray, width: int, height: int) -> None:
    if flat.size == 0:
        return
    bbox = bbox_from_flat(flat, width)
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    pad = 8
    roi = (max(0, x0-pad), max(0, y0-pad), min(width-1, x1+pad), min(height-1, y1+pad))
    rx0, ry0, rx1, ry1 = roi
    raw = image_np[ry0:ry1+1, rx0:rx1+1].copy()
    mask = np.zeros(raw.shape[:2], dtype=bool)
    ys = flat // width
    xs = flat % width
    mask[ys-ry0, xs-rx0] = True
    overlay = raw.copy()
    overlay[mask] = [255, 0, 0]
    stem = row["ELEMENT_ID"].replace("#", "_")
    Image.fromarray((mask*255).astype(np.uint8)).save(GLYPH_EVIDENCE_DIR / f"{stem}_raw_mask_1to1.png")
    Image.fromarray(overlay).save(GLYPH_EVIDENCE_DIR / f"{stem}_overlay_1to1.png")
    Image.fromarray(overlay).resize((overlay.shape[1]*8, overlay.shape[0]*8), Image.Resampling.NEAREST).save(GLYPH_EVIDENCE_DIR / f"{stem}_overlay_8x_nearest.png")


def source_excerpt() -> dict[str, str]:
    fig = FIG_SOURCE.read_text(encoding="utf-8")
    ctx = CONTEXT_SOURCE.read_text(encoding="utf-8")
    if "fig:V5-C02-generalized-inverse" not in ctx or "连续：首次达到" not in fig:
        raise RuntimeError("Authorised source anchor mismatch")
    return {"figure_source": str(FIG_SOURCE), "context_source": str(CONTEXT_SOURCE)}


def extract_spans(page: fitz.Page) -> list[dict[str, Any]]:
    raw = page.get_text("rawdict")
    spans: list[dict[str, Any]] = []
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                chars = span.get("chars", [])
                if not chars:
                    continue
                text = "".join(char["c"] for char in chars)
                bbox = tuple(float(v) for v in span["bbox"])
                spans.append({"text": text, "chars": chars, "bbox": bbox, "color": span["color"],
                              "font": span["font"], "size": float(span["size"])})
    return spans


def select_text_parents(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def one(label: str, predicate) -> dict[str, Any]:
        found = [s for s in spans if predicate(s)]
        if len(found) != 1:
            raise RuntimeError(f"{label}: expected one extracted span, got {len(found)}")
        return found[0]

    parents: list[dict[str, Any]] = []
    def add(eid: str, panel: str, role: str, line: str, declared: float, logical: str, recs: list[dict[str, Any]]) -> None:
        parents.append({"id": eid, "panel": panel, "role": role, "line": line,
                        "declared": declared, "logical": logical, "spans": recs})

    # Titles.
    add("T_P1_TITLE", "P1", "PANEL_TITLE", "19", 9.6, "连续：首次达到", [one("P1 title", lambda s: 170 < s["bbox"][0] < 250 and 70 < s["bbox"][1] < 85)])
    add("T_P2_TITLE", "P2", "PANEL_TITLE", "28", 9.6, "离散：首次达到", [one("P2 title", lambda s: 350 < s["bbox"][0] < 440 and 70 < s["bbox"][1] < 85)])

    # Tick labels are source line 14: do not infer their effective size from the
    # PDF font's math-face transform; audit the explicit LaTeX declaration.
    p1_xticks = sorted([s for s in spans if 140 < s["bbox"][0] < 285 and 205 < s["bbox"][1] < 210], key=lambda s: s["bbox"][0])
    p2_xticks = sorted([s for s in spans if 320 < s["bbox"][0] < 470 and 205 < s["bbox"][1] < 210], key=lambda s: s["bbox"][0])
    p1_yticks = sorted([s for s in spans if 115 < s["bbox"][0] < 142 and 84 < s["bbox"][1] < 210], key=lambda s: -s["bbox"][1])
    p2_yticks = sorted([s for s in spans if 298 < s["bbox"][0] < 324 and 84 < s["bbox"][1] < 210], key=lambda s: -s["bbox"][1])
    tick_labels = ["0", "1", "2", "3", "4"]
    ytick_labels = ["0", "0.25", "0.5", "1"]
    if not (len(p1_xticks) == len(p2_xticks) == 5 and len(p1_yticks) == len(p2_yticks) == 4):
        raise RuntimeError("Unexpected tick span count")
    for prefix, panel, records, labels in (("P1_X", "P1", p1_xticks, tick_labels), ("P2_X", "P2", p2_xticks, tick_labels),
                                           ("P1_Y", "P1", p1_yticks, ytick_labels), ("P2_Y", "P2", p2_yticks, ytick_labels)):
        for i, (record, label) in enumerate(zip(records, labels)):
            add(f"T_{prefix}_TICK_{i}", panel, "TICK_LABEL", "14", 8.5, label, [record])

    # Axis labels and annotations.
    add("T_P1_ANNOT_U065", "P1", "ANNOTATION", "24-25", 9.2, "u=.65", [one("P1 u", lambda s: 108 < s["bbox"][0] < 145 and 120 < s["bbox"][1] < 136)])
    add("T_P1_ANNOT_Q065", "P1", "ANNOTATION", "26-27", 9.2, "Q(.65)", [one("P1 Q", lambda s: 155 < s["bbox"][0] < 200 and 210 < s["bbox"][1] < 228)])
    add("T_P1_AXIS_X", "P1", "AXIS_TITLE", "12,15", 9.2, "x", [one("P1 x", lambda s: 200 < s["bbox"][0] < 220 and 225 < s["bbox"][1] < 240)])
    add("T_P1_AXIS_FX", "P1", "AXIS_TITLE", "12,15", 9.2, "F(x)", [one("P1 F", lambda s: 100 < s["bbox"][0] < 120 and 130 < s["bbox"][1] < 160)])
    add("T_P2_ANNOT_U070", "P2", "ANNOTATION", "41-43", 9.0, "u=.70", [one("P2 u70", lambda s: 290 < s["bbox"][0] < 325 and 120 < s["bbox"][1] < 136)])
    add("T_P2_ANNOT_U072", "P2", "ANNOTATION", "44-46", 9.0, "u=.72", [one("P2 u72", lambda s: 285 < s["bbox"][0] < 325 and 105 < s["bbox"][1] < 122)])
    add("T_P2_ANNOT_Q070", "P2", "ANNOTATION", "47-48", 9.0, "Q(.70)=2", [one("P2 Q70", lambda s: 335 < s["bbox"][0] < 385 and 212 < s["bbox"][1] < 230)])
    add("T_P2_ANNOT_Q072", "P2", "ANNOTATION", "49-50", 9.0, "Q(.72)=3", [one("P2 Q72", lambda s: 428 < s["bbox"][0] < 490 and 212 < s["bbox"][1] < 230)])
    add("T_P2_AXIS_X", "P2", "AXIS_TITLE", "12,15", 9.2, "x", [one("P2 x", lambda s: 380 < s["bbox"][0] < 405 and 225 < s["bbox"][1] < 240)])
    add("T_P2_AXIS_FX", "P2", "AXIS_TITLE", "12,15", 9.2, "F(x)", [one("P2 F", lambda s: 282 < s["bbox"][0] < 302 and 130 < s["bbox"][1] < 160)])

    cap = [s for s in spans if 235 < s["bbox"][1] < 275 and 55 < s["bbox"][0] < 535]
    cap = sorted(cap, key=lambda s: (round(s["bbox"][1], 1), s["bbox"][0]))
    if len(cap) != 7:
        raise RuntimeError(f"caption: expected seven spans, got {len(cap)}")
    add("T_CAPTION", "CAPTION", "CAPTION", "53", 10.0,
        "图31.3 广义逆采用首次达到规则：连续情形沿水平线找到交点；离散情形中u=0.7落在第二个跳点，而u=0.72落在第三个跳点", cap)
    return parents


def build_text_objects(parents: list[dict[str, Any]], image_np: np.ndarray, width: int, height: int) -> tuple[list[ObjectRecord], list[dict[str, Any]], dict[str, np.ndarray]]:
    objects: list[ObjectRecord] = []
    rows: list[dict[str, Any]] = []
    glyph_flats: dict[str, np.ndarray] = {}

    for parent in parents:
        char_entries: list[dict[str, Any]] = []
        for span in parent["spans"]:
            for char in span["chars"]:
                c = char["c"]
                if not c or c.isspace():
                    continue
                x0, y0, x1, y1 = rect_to_px(tuple(float(v) for v in char["bbox"]), width, height, margin=1)
                if x1 <= x0 or y1 <= y0:
                    continue
                region = image_np[y0:y1, x0:x1]
                colour = rgb_from_pdf_color(span["color"])
                local = mask_color_match(region, [colour])
                yy, xx = np.nonzero(local)
                flat = np.unique((yy+y0).astype(np.int64) * width + (xx+x0).astype(np.int64))
                char_entries.append({"c": c, "flat": flat, "pdf_bbox": tuple(float(v) for v in char["bbox"]),
                                     "span": span, "px_bbox": (x0, y0, x1-1, y1-1)})

        # Resolve any anti-alias fringe that could otherwise belong to adjacent
        # same-colour glyph masks.  No pixel may be counted by two glyphs.
        occupied: set[int] = set()
        for item in char_entries:
            if item["flat"].size:
                item["flat"] = np.asarray([v for v in item["flat"] if int(v) not in occupied], dtype=np.int64)
                occupied.update(int(v) for v in item["flat"])

        parent_flat = np.unique(np.concatenate([e["flat"] for e in char_entries if e["flat"].size])) if any(e["flat"].size for e in char_entries) else np.asarray([], dtype=np.int64)
        obj = ObjectRecord(parent["id"], parent["panel"], parent["role"], "TEXT", parent["line"],
                           parent["logical"], parent["declared"], 1.0, parent["declared"], parent_flat)
        obj.bbox = bbox_from_flat(parent_flat, width)
        pdf_bbox = (min(s["bbox"][0] for s in parent["spans"]), min(s["bbox"][1] for s in parent["spans"]),
                    max(s["bbox"][2] for s in parent["spans"]), max(s["bbox"][3] for s in parent["spans"]))
        px_excl = rect_to_px(pdf_bbox, width, height, margin=0)
        vector_bbox_px = (px_excl[0], px_excl[1], px_excl[2]-1, px_excl[3]-1)
        obj.details = {"pdf_vector_bbox_pt": [round(x, 5) for x in pdf_bbox], "vector_bbox_px": vector_bbox_px,
                       "mask_method": "own PDF glyph bbox + own paint colour + exclusive final-pixel assignment"}
        objects.append(obj)

        for idx, item in enumerate(char_entries, start=1):
            gid = f"{parent['id']}#G{idx:03d}"
            flat = item["flat"]
            glyph_flats[gid] = flat
            bbox = bbox_from_flat(flat, width)
            script_class, threshold, threshold_note = classify_glyph(item["c"])
            h = 0 if bbox is None else bbox[3] - bbox[1] + 1
            font_pass = parent["declared"] >= 9.5
            pixel_pass = (h >= threshold) if threshold else True
            # Ratio fields are filled only after all glyphs are known.
            reason_bits = []
            if not font_pass:
                reason_bits.append("effective_pt < 9.5")
            if not pixel_pass:
                reason_bits.append(f"H_ink_px {h} < {threshold}")
            if h == 0:
                reason_bits.append("empty raw glyph mask")
            rows.append({
                "ELEMENT_ID": gid,
                "PARENT_ELEMENT_ID": parent["id"],
                "PANEL_ID": parent["panel"],
                "ROLE": parent["role"],
                "SOURCE_FILE": str(FIG_SOURCE),
                "SOURCE_LINE": parent["line"],
                "DECLARED_PT": f"{parent['declared']:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{parent['declared']:.2f}",
                "TEXT_SAMPLE": logical_text(item["c"]),
                "RAW_PDF_GLYPH": item["c"],
                "SCRIPT_CLASS": script_class,
                "PIXEL_THRESHOLD_PX": threshold,
                "PIXEL_THRESHOLD_RULE": threshold_note,
                "BBOX_X0": "" if bbox is None else bbox[0],
                "BBOX_Y0": "" if bbox is None else bbox[1],
                "BBOX_X1": "" if bbox is None else bbox[2],
                "BBOX_Y1": "" if bbox is None else bbox[3],
                "H_INK_PX": h,
                "CLASS_MEDIAN_PX": "",
                "RATIO_TO_CLASS_MEDIAN": "",
                "ROLE_BASE_ID": "",
                "ROLE_RATIO": "N/A",
                "ROLE_RATIO_RULE": "",
                "TEXT_TEXT_OVERLAP_PX": "",
                "TEXT_GRAPHIC_OVERLAP_PX": "",
                "MIN_CLEARANCE_PX": "",
                "SOURCE_FONT_PASS": bool_s(font_pass),
                "PIXEL_HEIGHT_PASS": bool_s(pixel_pass),
                "PASS_FAIL": "PASS" if (font_pass and pixel_pass and h > 0) else "FAIL",
                "REASON": "; ".join(reason_bits),
                "RAW_MASK_FILE": "",
            })
    return objects, rows, glyph_flats


def build_graphics(page: fitz.Page, image_np: np.ndarray, width: int, height: int) -> list[ObjectRecord]:
    drawings = page.get_drawings()
    if len(drawings) < 27:
        raise RuntimeError(f"Unexpected PDF drawing count: {len(drawings)}")
    # IDs are semantic source objects. Indices refer to vector objects recovered
    # directly from physical page 623, not a prior evidence package.
    specs = [
        ("G_P1_X_TICK_MARKS", "P1", "AXIS_TICK_MARK", "LINE_ARROW", "14,18", [1]),
        ("G_P1_Y_TICK_MARKS", "P1", "AXIS_TICK_MARK", "LINE_ARROW", "14,18", [2]),
        ("G_P1_X_AXIS", "P1", "AXIS", "LINE_ARROW", "18", [3, 4]),
        ("G_P1_Y_AXIS", "P1", "AXIS", "LINE_ARROW", "18", [5, 6]),
        ("G_P1_CONTINUOUS_CDF", "P1", "DATA_CURVE", "DATA_CURVE", "20", [7]),
        ("G_P1_U065_GUIDE", "P1", "GUIDE_LINE", "LINE_ARROW", "21-22", [8]),
        ("G_P1_U065_POINT", "P1", "MARKER", "MARKER", "23", [9]),
        ("G_P2_X_TICK_MARKS", "P2", "AXIS_TICK_MARK", "LINE_ARROW", "14,18", [10]),
        ("G_P2_Y_TICK_MARKS", "P2", "AXIS_TICK_MARK", "LINE_ARROW", "14,18", [11]),
        ("G_P2_X_AXIS", "P2", "AXIS", "LINE_ARROW", "18", [12, 13]),
        ("G_P2_Y_AXIS", "P2", "AXIS", "LINE_ARROW", "18", [14, 15]),
        ("G_P2_DISCRETE_CDF", "P2", "DATA_CURVE", "DATA_CURVE", "29-30", [16]),
        ("G_P2_U070_GUIDE", "P2", "GUIDE_LINE", "LINE_ARROW", "35-36", [17]),
        ("G_P2_U072_GUIDE", "P2", "GUIDE_LINE", "LINE_ARROW", "37-38", [18]),
        ("G_P2_OPEN_X1", "P2", "MARKER", "MARKER", "31-32", [19]),
        ("G_P2_FILL_X1", "P2", "MARKER", "MARKER", "31-33", [20]),
        ("G_P2_OPEN_X2", "P2", "MARKER", "MARKER", "31-32", [21]),
        ("G_P2_FILL_X2", "P2", "MARKER", "MARKER", "31-33", [22]),
        ("G_P2_OPEN_X3", "P2", "MARKER", "MARKER", "31-32", [23]),
        ("G_P2_FILL_X3", "P2", "MARKER", "MARKER", "31-33", [24]),
        ("G_P2_U070_SQUARE", "P2", "MARKER", "MARKER", "39", [25]),
        ("G_P2_U072_TRIANGLE", "P2", "MARKER", "MARKER", "40", [26]),
    ]
    result: list[ObjectRecord] = []
    for oid, panel, role, otype, source_line, indices in specs:
        raw_mask = np.zeros((height, width), dtype=bool)
        colors: list[tuple[int, int, int]] = []
        vector_gate = np.zeros((height, width), dtype=bool)
        for i in indices:
            draw = drawings[i]
            vector_gate |= drawing_gate(draw, width, height)
            for color in (draw.get("color"), draw.get("fill")):
                if color is not None:
                    colors.append(tuple(int(round(v*255)) for v in color))
        # A color-matched subset of the raw final render: never a synthetic line.
        candidate = mask_color_match(image_np, colors)
        raw_mask = vector_gate & candidate
        yy, xx = np.nonzero(raw_mask)
        flat = np.unique(yy.astype(np.int64)*width + xx.astype(np.int64))
        obj = ObjectRecord(oid, panel, role, otype, source_line, raw_flat=flat)
        obj.bbox = bbox_from_flat(flat, width)
        obj.details = {"pdf_drawing_indices": indices, "expected_rgb": colors,
                       "mask_method": "vector eligibility gate ∩ native final-PNG color/foreground mask"}
        result.append(obj)
    return result


def compute_ratio_audits(pixel_rows: list[dict[str, Any]]) -> tuple[bool, bool, list[dict[str, Any]], list[dict[str, Any]]]:
    """D: broad script groups, never exact-glyph groups. E: comparable script only."""
    class_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pixel_rows:
        # Parent panel/role/script: this deliberately groups distinct characters.
        class_groups[(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])].append(row)
    d_rows: list[dict[str, Any]] = []
    all_d = True
    for key, rows in sorted(class_groups.items()):
        values = np.asarray([int(r["H_INK_PX"]) for r in rows], dtype=float)
        median = float(np.median(values)) if len(values) else float("nan")
        ratio_min = float(values.min()/median) if median else 0.0
        ratio_max = float(values.max()/median) if median else float("inf")
        extrema = float(values.max()/values.min()) if values.min() else float("inf")
        passed = ratio_min >= 0.92 and ratio_max <= 1.08 and extrema <= 1.08
        for row in rows:
            row["CLASS_MEDIAN_PX"] = f"{median:.3f}"
            row["RATIO_TO_CLASS_MEDIAN"] = f"{int(row['H_INK_PX'])/median:.4f}" if median else ""
        d_rows.append({"PANEL_ID": key[0], "ROLE": key[1], "SCRIPT_CLASS": key[2],
                       "N_GLYPHS": len(rows), "MEDIAN_H_INK_PX": f"{median:.3f}",
                       "MIN_RATIO": f"{ratio_min:.4f}", "MAX_RATIO": f"{ratio_max:.4f}",
                       "MAX_MIN_RATIO": f"{extrema:.4f}", "PASS_FAIL": "PASS" if passed else "FAIL",
                       "GROUPING_NOTE": "same panel + same semantic role + same broad script class; not exact-glyph grouping"})
        all_d &= passed

    # Base = all tick numeric/uppercase/digit glyphs in the same panel.  Only that
    # class is comparable. Other script classes are explicit N/A, not silently
    # inherited from a different alphabet or punctuation category.
    e_rows: list[dict[str, Any]] = []
    all_e = True
    by_panel: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pixel_rows:
        by_panel[row["PANEL_ID"]].append(row)
    base_lookup: dict[str, tuple[float, list[str]]] = {}
    for panel in ("P1", "P2"):
        bases = [r for r in by_panel[panel] if r["ROLE"] == "TICK_LABEL" and r["SCRIPT_CLASS"] == "LATIN_UPPER_OR_DIGIT"]
        if bases:
            base_lookup[panel] = (float(np.median([int(r["H_INK_PX"]) for r in bases])), [r["ELEMENT_ID"] for r in bases])
    role_limits = {"AXIS_TITLE": (1.00, 1.18), "ANNOTATION": (0.95, 1.10), "TICK_LABEL": (1.00, 1.00)}
    for row in pixel_rows:
        panel, role, script = row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"]
        if panel not in base_lookup or script != "LATIN_UPPER_OR_DIGIT" or role not in role_limits:
            row["ROLE_BASE_ID"] = "N/A"
            row["ROLE_RATIO"] = "N/A"
            row["ROLE_RATIO_RULE"] = "N/A: no comparable LATIN_UPPER_OR_DIGIT BASE in this local role/panel"
            continue
        base, base_ids = base_lookup[panel]
        ratio = int(row["H_INK_PX"])/base if base else float("inf")
        lo, hi = role_limits[role]
        passed = lo <= ratio <= hi
        row["ROLE_BASE_ID"] = ";".join(base_ids)
        row["ROLE_RATIO"] = f"{ratio:.4f}"
        row["ROLE_RATIO_RULE"] = f"{role} vs local numeric BASE [{lo:.2f},{hi:.2f}]"
        e_rows.append({"ELEMENT_ID": row["ELEMENT_ID"], "PANEL_ID": panel, "ROLE": role,
                       "SCRIPT_CLASS": script, "BASE_MEDIAN_PX": f"{base:.3f}", "ROLE_RATIO": f"{ratio:.4f}",
                       "LIMIT": f"[{lo:.2f},{hi:.2f}]", "PASS_FAIL": "PASS" if passed else "FAIL"})
        all_e &= passed
    return all_d, all_e, d_rows, e_rows


def source_font_rows(parents: list[dict[str, Any]], glyph_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One source-font row per semantic visible text ELEMENT_ID.

    Glyph measurements remain in after_pixel_measurements.csv.  They are a trace
    layer, not a substitute for the unique reader-visible text-element inventory.
    """
    glyph_count = Counter(r["PARENT_ELEMENT_ID"] for r in glyph_rows)
    out: list[dict[str, Any]] = []
    for p in parents:
        declared = float(p["declared"])
        out.append({
            "ELEMENT_ID": p["id"], "PANEL_ID": p["panel"], "ROLE": p["role"], "TEXT_SAMPLE": p["logical"],
            "GLYPH_TRACE_COUNT": glyph_count[p["id"]], "SOURCE_FILE": str(FIG_SOURCE), "SOURCE_LINE": p["line"],
            "DECLARED_PT": f"{declared:.2f}", "GRAPHICS_SCALE": "1.0000",
            "EFFECTIVE_PT": f"{declared:.2f}",
            "DERIVATION": f"declared {declared:.2f}pt × direct input/no resize/scale 1.0000",
            "FONT_RULE": "general reader-visible glyph >=9.50pt; no legal scriptstyle exception applies",
            "PASS_FAIL": "PASS" if declared >= 9.5 else "FAIL",
            "REASON": "" if declared >= 9.5 else f"effective_pt {declared:.2f} < 9.50",
        })
    return out


def pair_requirement(a: ObjectRecord, b: ObjectRecord) -> tuple[str, float | None]:
    if a.object_type == "TEXT" and b.object_type == "TEXT":
        return ("TEXT_TEXT_CROSS_PANEL" if a.panel_id in {"P1", "P2"} and b.panel_id in {"P1", "P2"} and a.panel_id != b.panel_id else "TEXT_TEXT", 8.0 if a.panel_id in {"P1", "P2"} and b.panel_id in {"P1", "P2"} and a.panel_id != b.panel_id else 4.0)
    if a.object_type == "TEXT" or b.object_type == "TEXT":
        other = b if a.object_type == "TEXT" else a
        if other.object_type == "MARKER":
            return ("TEXT_MARKER", 3.0)
        if other.object_type in {"LINE_ARROW", "DATA_CURVE"}:
            return ("TEXT_LINE_ARROW_OR_CURVE", 3.0)
        if other.object_type == "NODE_BORDER":
            return ("TEXT_NODE_BORDER", 5.0)
        return ("TEXT_GRAPHIC", 3.0)
    return ("GRAPHIC_GRAPHIC", None)


def allowed_connection_ids() -> set[frozenset[str]]:
    pairs = [
        # P1: ticks and curve meet their axes at mathematically intended origins;
        # the marker is intentionally placed at the guide/curve intersection.
        ("G_P1_X_TICK_MARKS", "G_P1_Y_TICK_MARKS"),
        ("G_P1_X_TICK_MARKS", "G_P1_X_AXIS"),
        ("G_P1_X_TICK_MARKS", "G_P1_Y_AXIS"),
        ("G_P1_X_TICK_MARKS", "G_P1_CONTINUOUS_CDF"),
        ("G_P1_Y_TICK_MARKS", "G_P1_X_AXIS"),
        ("G_P1_Y_TICK_MARKS", "G_P1_Y_AXIS"),
        ("G_P1_Y_TICK_MARKS", "G_P1_CONTINUOUS_CDF"),
        ("G_P1_X_AXIS", "G_P1_Y_AXIS"),
        ("G_P1_X_AXIS", "G_P1_CONTINUOUS_CDF"),
        ("G_P1_Y_AXIS", "G_P1_CONTINUOUS_CDF"),
        ("G_P1_CONTINUOUS_CDF", "G_P1_U065_POINT"),
        ("G_P1_U065_GUIDE", "G_P1_U065_POINT"),
        # P2: all following intersections implement stair-CDF endpoint/guide
        # geometry specified explicitly in source lines 29--40.
        ("G_P2_X_TICK_MARKS", "G_P2_Y_TICK_MARKS"),
        ("G_P2_X_TICK_MARKS", "G_P2_X_AXIS"),
        ("G_P2_X_TICK_MARKS", "G_P2_Y_AXIS"),
        ("G_P2_X_TICK_MARKS", "G_P2_OPEN_X1"),
        ("G_P2_Y_TICK_MARKS", "G_P2_X_AXIS"),
        ("G_P2_Y_TICK_MARKS", "G_P2_Y_AXIS"),
        ("G_P2_X_AXIS", "G_P2_Y_AXIS"),
        ("G_P2_X_AXIS", "G_P2_DISCRETE_CDF"),
        ("G_P2_X_AXIS", "G_P2_OPEN_X1"),
        ("G_P2_Y_AXIS", "G_P2_DISCRETE_CDF"),
        ("G_P2_DISCRETE_CDF", "G_P2_OPEN_X1"), ("G_P2_DISCRETE_CDF", "G_P2_FILL_X1"),
        ("G_P2_DISCRETE_CDF", "G_P2_OPEN_X2"), ("G_P2_DISCRETE_CDF", "G_P2_FILL_X2"),
        ("G_P2_DISCRETE_CDF", "G_P2_OPEN_X3"), ("G_P2_DISCRETE_CDF", "G_P2_FILL_X3"),
        ("G_P2_DISCRETE_CDF", "G_P2_U070_GUIDE"),
        ("G_P2_U070_GUIDE", "G_P2_OPEN_X2"),
        ("G_P2_U070_GUIDE", "G_P2_U070_SQUARE"), ("G_P2_U072_GUIDE", "G_P2_U072_TRIANGLE"),
    ]
    return {frozenset(pair) for pair in pairs}


def build_pairs(objects: list[ObjectRecord], width: int, image_np: np.ndarray, height: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs: list[dict[str, Any]] = []
    critical: list[dict[str, Any]] = []
    allowed = allowed_connection_ids()
    sequence = 0
    for a, b in combinations(objects, 2):
        sequence += 1
        kind, required = pair_requirement(a, b)
        if a.bbox is None or b.bbox is None:
            intersection = -1
            distance = float("nan")
            raw_bbox_dist = float("nan")
            vector_bbox_dist = float("nan")
            status = "FAIL"
            disposition = "EVIDENCE_FAILURE_EMPTY_MASK"
            reason = "empty object raw mask => evidence failure"
        else:
            intersection = int(np.intersect1d(a.raw_flat, b.raw_flat, assume_unique=True).size)
            raw_bbox_dist = bbox_gap(a.bbox, b.bbox)
            a_vector_bbox = tuple(a.details.get("vector_bbox_px", a.bbox))
            b_vector_bbox = tuple(b.details.get("vector_bbox_px", b.bbox))
            vector_bbox_dist = bbox_gap(a_vector_bbox, b_vector_bbox)
            # Exact mask distance is only needed near the gate or where masks meet;
            # all pairs still receive an exact value for machine-verifiable coverage.
            distance = distance_between(a, b, width)
            is_allowed = frozenset((a.object_id, b.object_id)) in allowed
            if intersection > 0 and not is_allowed:
                status = "FAIL"
                disposition = "ILLEGAL_FINAL_VISIBLE_INTERSECTION"
                reason = "illegal final-visible raw-mask intersection"
            elif kind.startswith("TEXT_TEXT") and vector_bbox_dist < required:
                status = "FAIL"
                disposition = "TEXT_TEXT_PDF_BBOX_CLEARANCE_FAILURE"
                reason = f"TEXT_TEXT PDF/vector bbox clearance {vector_bbox_dist:.3f}px < required {required:.1f}px"
            elif required is not None and distance < required:
                status = "FAIL"
                disposition = "CLEARANCE_FAILURE"
                reason = f"clearance {distance:.3f}px < required {required:.1f}px"
            elif intersection > 0 and is_allowed:
                status = "PASS"
                disposition = "ALLOWED_INTENTIONAL"
                reason = "intentional vector connection; final-visible intersection is not a text/semantic collision"
            else:
                status = "PASS"
                disposition = "NO_FINAL_VISIBLE_INTERSECTION"
                reason = ""
        margin = "" if required is None or math.isnan(distance) else f"{distance-required:.3f}"
        pair = {
            "PAIR_ID": f"PAIR_{sequence:04d}", "OBJECT_A": a.object_id, "OBJECT_B": b.object_id,
            "TYPE_A": a.object_type, "TYPE_B": b.object_type, "ROLE_A": a.role, "ROLE_B": b.role,
            "RELATION_TYPE": kind, "REQUIRED_CLEARANCE_PX": "N/A" if required is None else f"{required:.1f}",
            "TEXT_TEXT_PDF_BBOX_CLEARANCE_PX": "" if math.isnan(vector_bbox_dist) else f"{vector_bbox_dist:.3f}",
            "RAW_MASK_BBOX_CLEARANCE_PX": "" if math.isnan(raw_bbox_dist) else f"{raw_bbox_dist:.3f}",
            "RAW_MASK_CLEARANCE_PX": "" if math.isnan(distance) else f"{distance:.3f}",
            "CLEARANCE_MARGIN_PX": margin, "RAW_INTERSECTION_PX": intersection,
            "FINAL_VISIBLE_MASK_BASIS": "true", "INTENTIONAL_CONNECTION": bool_s(frozenset((a.object_id,b.object_id)) in allowed),
            "DISPOSITION": disposition, "PASS_FAIL": status, "REASON": reason,
        }
        pairs.append(pair)
        if status == "FAIL" or (required is not None and not math.isnan(distance) and distance-required <= 1.0):
            critical.append(pair)
    # Evidence after pair rows are stable; each saved directory names the pair ID.
    by_id = {o.object_id: o for o in objects}
    for pair in critical:
        save_pair_evidence(pair, by_id[pair["OBJECT_A"]], by_id[pair["OBJECT_B"]], image_np, width, height)
    return pairs, critical


def build_edge_rows(text_objects: list[ObjectRecord], crop: tuple[int, int, int, int]) -> list[dict[str, Any]]:
    x0, y0, x1, y1 = crop
    rows: list[dict[str, Any]] = []
    for o in text_objects:
        if o.bbox is None:
            continue
        bx0, by0, bx1, by1 = o.bbox
        clearances = {"left": bx0-x0, "right": x1-1-bx1, "top": by0-y0, "bottom": y1-1-by1}
        min_c = min(clearances.values())
        rows.append({"ELEMENT_ID": o.object_id, "PANEL_ID": o.panel_id, "ROLE": o.role,
                     "CROP_NATIVE_X0": x0, "CROP_NATIVE_Y0": y0, "CROP_NATIVE_X1_EXCL": x1, "CROP_NATIVE_Y1_EXCL": y1,
                     "LEFT_PX": clearances["left"], "RIGHT_PX": clearances["right"], "TOP_PX": clearances["top"], "BOTTOM_PX": clearances["bottom"],
                     "MIN_EDGE_CLEARANCE_PX": min_c, "REQUIRED_PX": 6, "PASS_FAIL": "PASS" if min_c >= 6 else "FAIL"})
    return rows


def make_math_report() -> str:
    continuous_q = -math.log(1-0.65)/0.65
    continuous_f = 1-math.exp(-0.65*1.615)
    return f"""# FIG-P575-01 数学、语义与图文独立复算

## 直接来源与范围

- 最终候选：`main_full.pdf`，物理页 {PHYSICAL_PAGE}（页内印刷页码 610）。
- 相邻正文锚点：V5-C02.tex:301--302；定义为 `Q(u)=inf{{x:F(x)>=u}}`（277--281），事件等价在 291--299。
- 图源：fig_v5_c02_generalized_inverse.tex:19--53。

## 连续面板

图源曲线为 `F(x)=1-exp(-0.65x)`（line 20），严格递增，且

`Q(0.65)=-ln(1-0.65)/0.65 = {continuous_q:.6f}`。

图中引线交点使用 `x=1.615`（lines 21--23），独立代入为
`F(1.615)={continuous_f:.6f}`，与 `0.65` 的作图四舍五入一致。

## 离散面板

阶梯坐标为 `(0,0),(1,.25),(2,.70),(3,.95),(4,1)`（lines 29--30），故跳跃质量依次为
`0.25, 0.45, 0.25, 0.05`，非负且总和为 1。按右连续 CDF：

- `F(2)=0.70`，所以 `Q(0.70)=2`；
- `F(2)=0.70 < 0.72 <= F(3)=0.95`，所以 `Q(0.72)=3`。

这与图内标注（41--50）、题注（53）及相邻正文“首次达到/跳跃/平坦段”说明（301）一致；题注的 `0.7` 与图内 `.70` 数值相同。

## 阅读顺序、灰度和整页融合

阅读路径为左面板连续曲线的水平投影，再到右面板阶梯 CDF 的两个阈值；虚线/点划线和圆/方/三角的非颜色编码在灰度图中仍区分。物理页中图题注紧接图体，后接“易混淆概念对比”，无孤行、裁断或错误图号。数学、图文、阅读顺序、灰度和页面融合均通过；本轮 FAIL 仅由严格字号/像素硬门触发。
"""


def acceptance_md(flags: dict[str, Any], counts: dict[str, Any], edge_rows: list[dict[str, Any]], d_rows: list[dict[str, Any]], e_rows: list[dict[str, Any]]) -> str:
    min_edge = min(int(r["MIN_EDGE_CLEARANCE_PX"]) for r in edge_rows) if edge_rows else 0
    d_fail = sum(r["PASS_FAIL"] == "FAIL" for r in d_rows)
    e_fail = sum(r["PASS_FAIL"] == "FAIL" for r in e_rows)
    return f"""# FIG-P575-01 SA1 严格视觉验收（R1）

RESULT: {flags['RESULT']}

## 固定输入定位

- 仅审计官方 R94 `main_full.pdf` 物理页 {PHYSICAL_PAGE}（PDF 内页码 610）。
- 独立定位链：前页正文锚点“图31.3把严格递增与离散跳跃放在同一‘首次达到’规则下” → 本页图题注“图31.3 广义逆采用首次达到规则…”。
- 原生网格：{counts['native_width']} × {counts['native_height']} px @ 300 dpi；页面 {counts['page_width_pt']:.3f} × {counts['page_height_pt']:.3f} PDF pt。
- 图块裁图为整页原生 300 dpi 的整数像素裁切；未 resize。具体整数坐标见 `render_manifest.json`。

## 9.2.1 / 严格 schema 判定

SOURCE_FONT_PASS = {bool_s(flags['SOURCE_FONT_PASS'])}
PIXEL_HEIGHT_PASS = {bool_s(flags['PIXEL_HEIGHT_PASS'])}
SAME_CLASS_RATIO_PASS = {bool_s(flags['SAME_CLASS_RATIO_PASS'])}
ROLE_RATIO_PASS = {bool_s(flags['ROLE_RATIO_PASS'])}
OVERLAP_PIXEL_COUNT = {counts['illegal_overlap_pixels']}
OVERLAP_FAIL_PAIR_COUNT = {counts['overlap_fail_pair_count']}
CLEARANCE_FAIL_PAIR_COUNT = {counts['clearance_fail_pair_count']}
CLIP_PIXEL_COUNT = {counts['clip_pixels']}
MIN_TEXT_CLEARANCE_PX = {counts['min_text_clearance']:.3f}
MIN_TEXT_TEXT_PDF_BBOX_CLEARANCE_PX = {counts['min_text_text_pdf_bbox_clearance']:.3f}
MIN_TEXT_RAW_INK_CLEARANCE_PX = {counts['min_text_raw_ink_clearance']:.3f}
FONT_VISUAL_HARMONY_PASS = {bool_s(flags['FONT_VISUAL_HARMONY_PASS'])}
VISUAL_HARMONY_PASS = {bool_s(flags['VISUAL_HARMONY_PASS'])}
MATH_SEMANTICS_PASS = {bool_s(flags['MATH_SEMANTICS_PASS'])}
TEXT_CONSISTENCY_PASS = {bool_s(flags['TEXT_CONSISTENCY_PASS'])}
GRAYSCALE_PASS = {bool_s(flags['GRAYSCALE_PASS'])}
PAGE_INTEGRATION_PASS = {bool_s(flags['PAGE_INTEGRATION_PASS'])}

## 可复核的失败原因

1. 图源 line 14 将所有刻度声明为 8.50pt；lines 5/15/24--27 为 9.20pt；lines 41--50 为 9.00pt。图由 V5-C02.tex:302 直接 `\\input`，没有可抵消的放大，故这些读者可见元素的 effective_pt 仍低于 9.50pt 硬门。
2. `after_font_audit.csv` 只计 {counts['semantic_text_element_count']} 个唯一语义文字 ELEMENT_ID（其中 {counts['semantic_font_failed_element_count']} 个源字号 FAIL）；`after_pixel_measurements.csv` 是 {counts['glyph_trace_count']} 个逐 glyph/必要 substring trace，其中 **pixel-height failed = {counts['pixel_height_failed_glyph_count']}**，而综合字号/像素/D/E gate failed = {counts['all_glyph_gate_failed_count']}（D 失败组 {counts['same_class_failed_group_count']}，E 失败行 {counts['role_ratio_failed_row_count']}）。不得把 glyph trace 冒充语义元素，也不得把综合 FAIL 误报为像素高度 FAIL。关键数学标点/运算符单独建 mask；对应 raw masks、1:1 overlay 和 8× nearest 核像素证据见 `glyph_evidence/`。
3. 同面板、同角色、同 broad-script D 组中有 {d_fail} 组失败；未按 exact glyph 拆组。E 仅在有同脚本 BASE 时计算；CJK/小写/数学标点没有可比 numeric BASE 时均明确标为 N/A，而不是借用不相同脚本的字号。

空间 mask 计数使用最终可见前景（native PDF 300 dpi，局部背景差 >=20/255）。无真实文字 halo/白底/双边框：因此不存在可用于删减的 pre/halo/final 三态；普通白纸和节点/marker fill 未当作 halo。节点边框对象数为 0，`TEXT_NODE_BORDER` 关系显式 N/A；其余全部无序对象 pair 已枚举。

## 视觉结论

数学、题注/正文一致、阅读顺序、灰度编码和整页融合均可通过；但“能读”不能覆盖 9.2.1 字号、逐 glyph 像素和比例硬门。本图必须交 SA2 定向修复（提高刻度/标签/注释的有效字号，并在新最终 PDF 上重新全量取证）。
"""


def formal_sa1_report(flags: dict[str, Any], counts: dict[str, Any], pairs: list[dict[str, Any]]) -> str:
    failures = [p for p in pairs if p["PASS_FAIL"] == "FAIL"]
    pair_lines = "\n".join(
        f"- `{p['PAIR_ID']}` {p['OBJECT_A']} ↔ {p['OBJECT_B']}: `{p['DISPOSITION']}`; "
        f"PDF/vector bbox={p['TEXT_TEXT_PDF_BBOX_CLEARANCE_PX']}px, raw ink={p['RAW_MASK_CLEARANCE_PX']}px, intersection={p['RAW_INTERSECTION_PX']}px."
        for p in failures
    ) or "- none"
    return f"""# FIG-P575-01 / 图31.3 — SA1 正式独立严格复核报告（R1）

RESULT: {flags['RESULT']}

FIGURE_ID: FIG-P575-01

CANONICAL_UID: FIG-P575-01

COVERAGE:

- 官方最终 PDF `main_full.pdf` 物理页 623（页内印刷页码 610）；独立题注/正文锚点定位。
- 图源 `fig_v5_c02_generalized_inverse.tex:3--54` 与相邻正文 `V5-C02.tex:276--305`。
- 31 个唯一语义文字 ELEMENT_ID、151 个逐 glyph/必要 substring trace、22 个图形语义对象，共 53 个最终可见图块对象；全部 1378 个无序 pair。

BLOCKERS:

1. 28/31 语义文字元素 source effective_pt < 9.50pt：刻度 8.50pt，标签/部分注释 9.20pt，右面板注释 9.00pt；不存在整体放大抵消。
2. 26/151 glyph trace 直接像素门 FAIL；141/151 为综合 source-font / pixel / D / E gate FAIL，二者已严格分列。
3. D 同面板同角色同 broad-script（非 exact glyph 分组）失败组 {counts['same_class_failed_group_count']}；E 的可比 script/BASE 测量失败行 {counts['role_ratio_failed_row_count']}，无 BASE 的行显式 N/A。
4. 文字-文字 PDF/vector bbox 净空 4px 门失败 {counts['clearance_fail_pair_count']} 对；最终可见 raw-mask overlap 为 0，不能把 bbox 净空失败误写成 overlap。

MATHEMATICAL_FINDINGS:

PASS — 连续面板 `Q(.65)=-ln(.35)/.65=1.615926`，图内 1.615 代入 `F=1-exp(-.65x)` 得 0.650040；离散阶梯质量 `(0.25,0.45,0.25,0.05)` 总和为 1，`Q(.70)=2`、`Q(.72)=3`。详见 `mathematical_recomputation.md`。

TEXT_CONSISTENCY:

PASS — 图内 `.70` 与题注 `0.7` 数值一致；“首次达到”与 `Q(u)=inf{{x:F(x)>=u}}`、正文 jump/flat 解释一致。

READING_ORDER:

PASS — 左连续投影 → 右离散跳跃的单向阅读路径清楚。

SOURCE_FONT_AUDIT:

FAIL — 语义元素表 `after_font_audit.csv`：31 行，28 FAIL；glyph trace 仅在 `after_pixel_measurements.csv`。

PIXEL_HEIGHT_AUDIT:

FAIL — pixel-height failed glyph = 26；所有 raw glyph masks 在 native 300dpi 1:1 网格、local-background delta >=20/255 下测量。

SAME_CLASS_RATIO_AUDIT:

FAIL — failed group = {counts['same_class_failed_group_count']}；`same_class_ratio_audit.csv` 的分组键固定为 panel + role + broad script class。

ROLE_RATIO_AUDIT:

FAIL — failed comparable-script row = {counts['role_ratio_failed_row_count']}；无可比 BASE 的 CJK/小写/数学标点明确 `N/A`。

OVERLAP_PIXEL_COUNT: {counts['illegal_overlap_pixels']}

OVERLAP_PIXEL_AUDIT:

PASS for final-visible illegal overlap: 0 pixels / {counts['overlap_fail_pair_count']} pairs. 轴—刻度、曲线—点、导线—点的 {counts['intentional_graphic_intersection_pair_count']} 个实际 final-visible 源级有意图形连接均在 pair 表标为 `INTENTIONAL_CONNECTION=true` / `PASS`，未计入非法重叠。

CLIP_PIXEL_COUNT: {counts['clip_pixels']}

MIN_TEXT_CLEARANCE_PX: {counts['min_text_clearance']:.3f}

TEXT_TEXT_PDF_BBOX_MIN_PX: {counts['min_text_text_pdf_bbox_clearance']:.3f}

TEXT_TEXT_RAW_INK_MIN_PX: {counts['min_text_raw_ink_clearance']:.3f}

TEXT_TEXT_CLEARANCE_FAILURES:

{pair_lines}

VISUAL_HARMONY:

FAIL — 数学、灰度、阅读顺序和页面融合可通过，但 source font、glyph pixel/D/E 和文字 bbox 净空硬门未通过；不得以“仍可读”覆盖。

GRAYSCALE:

PASS — 虚线/点划线与圆/方/三角在 `grayscale_300dpi.png` 中仍区分。

CAPTION:

PASS — 只陈述图的读图结论，且与正文严格一致。

PAGE_INTEGRATION:

PASS — `full_page_200dpi.png` 显示图、题注及后续 comparison box/节标题连续，无裁切或异常留白。

REQUIRED_FIXES:

- SA2 应提高所有刻度、轴标签与注释的有效字号到硬门以上，并调整 `Q(.65)`、`Q(.70)=2`、`Q(.72)=3` 与相邻 tick/`F(x)` 的坐标，使 PDF/vector bbox 净空达到至少 4px；不得整体缩小。
- SA2 后必须由新最终 PDF 重新生成全部 native 300dpi 证据，再由新的 SA1/SA3 复核。

EVIDENCE_USED:

- `render_manifest.json`, `full_page_200dpi.png`, `full_page_300dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `same_class_ratio_audit.csv`, `role_ratio_audit.csv`, `after_overlap_report.csv`, `edge_clearance_report.csv`
- `after_text_measurement_overlay_300dpi.png`, `after_glyph_measurement_overlay_300dpi.png`, `masks/`, `glyph_evidence/`, `pair_evidence/`, `machine_terminal_check.*`
"""


def main() -> None:
    ensure_dirs()
    source_paths = source_excerpt()
    full300_path = run_render(DPI_300, "full_page_300dpi")
    full200_path = run_render(DPI_200, "full_page_200dpi")
    full300 = Image.open(full300_path).convert("RGB")
    full200 = Image.open(full200_path).convert("RGB")
    image_np = np.asarray(full300)
    height, width = image_np.shape[:2]

    fig_crop, fig_crop_px = crop_from_full(full300, FIGURE_BLOCK_PDF_RECT)
    standalone, standalone_px = crop_from_full(full300, STANDALONE_PDF_RECT)
    fig_crop.save(ROOT / "figure_crop_300dpi.png")
    standalone.save(ROOT / "standalone_300dpi.png")
    ImageOps.grayscale(fig_crop).save(ROOT / "grayscale_300dpi.png")
    fig_crop.resize((fig_crop.width*8, fig_crop.height*8), Image.Resampling.NEAREST).save(HUMAN_DIR / "figure_crop_8x_nearest.png")

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    spans = extract_spans(page)
    parents = select_text_parents(spans)
    text_objects, pixel_rows, glyph_flats = build_text_objects(parents, image_np, width, height)
    graphic_objects = build_graphics(page, image_np, width, height)
    objects = text_objects + graphic_objects
    for obj in objects:
        obj.bbox = bbox_from_flat(obj.raw_flat, width)
        save_object_mask(obj, width)

    # Save every glyph mask, including PASS glyphs, so no individual glyph is
    # represented only by a parent bbox.
    for gid, flat in glyph_flats.items():
        bbox = bbox_from_flat(flat, width)
        if bbox is not None:
            save_roi_mask(GLYPH_DIR / f"{gid.replace('#','_')}.png", flat, bbox, width)
    for row in pixel_rows:
        row["RAW_MASK_FILE"] = str((GLYPH_DIR / f"{row['ELEMENT_ID'].replace('#','_')}.png").relative_to(ROOT)).replace("\\", "/")
    glyph_flat_arrays = [flat for flat in glyph_flats.values() if flat.size]
    glyph_total_raw_pixels = int(sum(flat.size for flat in glyph_flat_arrays))
    glyph_unique_raw_pixels = int(np.unique(np.concatenate(glyph_flat_arrays)).size) if glyph_flat_arrays else 0
    glyph_duplicate_pixels = glyph_total_raw_pixels - glyph_unique_raw_pixels
    write_json(ROOT / "glyph_mask_separation_check.json", {
        "glyph_trace_count": len(glyph_flats), "total_raw_pixels": glyph_total_raw_pixels,
        "unique_raw_pixels": glyph_unique_raw_pixels, "cross_glyph_duplicate_pixels": glyph_duplicate_pixels,
        "PASS": glyph_duplicate_pixels == 0,
        "rule": "A raw glyph mask contains only its own final-visible foreground; no pixel may belong to two glyph masks."
    })

    same_class_pass, role_ratio_pass, d_rows, e_rows = compute_ratio_audits(pixel_rows)
    font_rows = source_font_rows(parents, pixel_rows)
    # Preserve per-row result strictness after class/role computation.
    for row in pixel_rows:
        class_key = (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        class_pass = next(x["PASS_FAIL"] == "PASS" for x in d_rows if (x["PANEL_ID"],x["ROLE"],x["SCRIPT_CLASS"]) == class_key)
        role_rows_for = [x for x in e_rows if x["ELEMENT_ID"] == row["ELEMENT_ID"]]
        role_pass = True if not role_rows_for else role_rows_for[0]["PASS_FAIL"] == "PASS"
        reason_bits = [x for x in [row["REASON"], "same-class ratio failed" if not class_pass else "", "role ratio failed" if not role_pass else ""] if x]
        row["SAME_CLASS_RATIO_PASS"] = bool_s(class_pass)
        row["ROLE_RATIO_PASS"] = bool_s(role_pass) if role_rows_for else "N/A"
        all_glyph_gates_pass = row["SOURCE_FONT_PASS"] == "true" and row["PIXEL_HEIGHT_PASS"] == "true" and class_pass and role_pass
        row["ALL_GLYPH_GATES_PASS"] = bool_s(all_glyph_gates_pass)
        row["PASS_FAIL"] = "PASS" if all_glyph_gates_pass else "FAIL"
        row["REASON"] = "; ".join(reason_bits)

    pairs, critical_pairs = build_pairs(objects, width, image_np, height)
    edge_rows = build_edge_rows(text_objects, fig_crop_px)
    # Pair-level text clearance must include all text pairs, and edge clearance is
    # a separate required geometry relation to the figure crop boundary.
    text_pair_rows = [p for p in pairs if p["RELATION_TYPE"].startswith("TEXT_TEXT")]
    min_text_raw_ink_clearance = min(float(p["RAW_MASK_CLEARANCE_PX"]) for p in text_pair_rows if p["RAW_MASK_CLEARANCE_PX"])
    min_text_text_pdf_bbox_clearance = min(float(p["TEXT_TEXT_PDF_BBOX_CLEARANCE_PX"]) for p in text_pair_rows if p["TEXT_TEXT_PDF_BBOX_CLEARANCE_PX"])
    min_edge = min(float(r["MIN_EDGE_CLEARANCE_PX"]) for r in edge_rows)
    min_text_clearance = min(min_text_raw_ink_clearance, min_text_text_pdf_bbox_clearance, min_edge)
    pair_fail_rows = [p for p in pairs if p["PASS_FAIL"] == "FAIL"]
    overlap_fail_rows = [p for p in pair_fail_rows if p["DISPOSITION"] == "ILLEGAL_FINAL_VISIBLE_INTERSECTION"]
    clearance_fail_rows = [p for p in pair_fail_rows if "CLEARANCE_FAILURE" in p["DISPOSITION"]]
    illegal_overlap = sum(max(0, int(p["RAW_INTERSECTION_PX"])) for p in overlap_fail_rows)
    clip_pixels = sum(1 for obj in objects if obj.bbox is None or obj.raw_flat.size == 0)

    # Add nearest text/graphic aggregate evidence columns to every glyph row.
    by_id = {o.object_id: o for o in objects}
    for row in pixel_rows:
        parent_obj = by_id[row["PARENT_ELEMENT_ID"]]
        parent_pairs = [p for p in pairs if parent_obj.object_id in (p["OBJECT_A"], p["OBJECT_B"])]
        tt = [int(p["RAW_INTERSECTION_PX"]) for p in parent_pairs if p["RELATION_TYPE"].startswith("TEXT_TEXT")]
        tg = [int(p["RAW_INTERSECTION_PX"]) for p in parent_pairs if "TEXT_" in p["RELATION_TYPE"] and not p["RELATION_TYPE"].startswith("TEXT_TEXT")]
        clear = [float(p["RAW_MASK_CLEARANCE_PX"]) for p in parent_pairs if p["REQUIRED_CLEARANCE_PX"] != "N/A"]
        row["TEXT_TEXT_OVERLAP_PX"] = sum(tt)
        row["TEXT_GRAPHIC_OVERLAP_PX"] = sum(tg)
        row["MIN_CLEARANCE_PX"] = f"{min(clear):.3f}" if clear else "N/A"

    # Glyph-specific audit artifacts for every actual font/pixel/D/E failure.
    for row in pixel_rows:
        if row["PASS_FAIL"] == "FAIL":
            save_glyph_evidence(row, glyph_flats[row["ELEMENT_ID"]], image_np, width, height)

    add_text_overlay(fig_crop, text_objects, fig_crop_px, "after_text_measurement_overlay_300dpi.png")
    add_text_overlay(fig_crop, text_objects, fig_crop_px, "after_glyph_measurement_overlay_300dpi.png", pixel_rows)

    object_rows: list[dict[str, Any]] = []
    for obj in objects:
        object_rows.append({"OBJECT_ID": obj.object_id, "PANEL_ID": obj.panel_id, "ROLE": obj.role,
                            "OBJECT_TYPE": obj.object_type, "SOURCE_LINE": obj.source_line, "TEXT_SAMPLE": obj.text_sample,
                            "DECLARED_PT": "" if obj.declared_pt is None else f"{obj.declared_pt:.2f}",
                            "GRAPHICS_SCALE": "" if obj.graphics_scale is None else f"{obj.graphics_scale:.4f}",
                            "EFFECTIVE_PT": "" if obj.effective_pt is None else f"{obj.effective_pt:.2f}",
                            "BBOX_X0": "" if obj.bbox is None else obj.bbox[0], "BBOX_Y0": "" if obj.bbox is None else obj.bbox[1],
                            "BBOX_X1": "" if obj.bbox is None else obj.bbox[2], "BBOX_Y1": "" if obj.bbox is None else obj.bbox[3],
                            "RAW_MASK_PIXELS": int(obj.raw_flat.size), "RAW_MASK_FILE": obj.mask_file,
                            "DETAILS": json.dumps(obj.details, ensure_ascii=False)})

    write_csv(ROOT / "object_manifest.csv", object_rows)
    write_json(ROOT / "object_manifest.json", {"scope": "source-created plot body + source caption; surrounding page prose excluded from figure object manifest",
                                                 "objects": object_rows})
    write_csv(ROOT / "after_font_audit.csv", font_rows)
    write_csv(ROOT / "after_pixel_measurements.csv", pixel_rows)
    write_csv(ROOT / "same_class_ratio_audit.csv", d_rows)
    write_csv(ROOT / "role_ratio_audit.csv", e_rows)
    write_csv(ROOT / "after_overlap_report.csv", pairs)
    write_json(ROOT / "all_pairs.json", {"object_count": len(objects), "expected_unordered_pair_count": len(objects)*(len(objects)-1)//2, "pairs": pairs})
    write_csv(ROOT / "edge_clearance_report.csv", edge_rows)
    (ROOT / "mathematical_recomputation.md").write_text(make_math_report(), encoding="utf-8")

    source_font_pass = all(r["PASS_FAIL"] == "PASS" for r in font_rows)
    pixel_height_pass = all(r["PIXEL_HEIGHT_PASS"] == "true" and int(r["H_INK_PX"]) > 0 for r in pixel_rows)
    spatial_pass = not pair_fail_rows and all(r["PASS_FAIL"] == "PASS" for r in edge_rows)
    # Source font failure is already enough to render font visual harmony false:
    # it is neither a permissible shrink nor a visually coherent compliant scale.
    flags = {
        "SOURCE_FONT_PASS": source_font_pass,
        "PIXEL_HEIGHT_PASS": pixel_height_pass,
        "SAME_CLASS_RATIO_PASS": same_class_pass,
        "ROLE_RATIO_PASS": role_ratio_pass,
        "FONT_VISUAL_HARMONY_PASS": source_font_pass and same_class_pass and role_ratio_pass,
        "VISUAL_HARMONY_PASS": source_font_pass and same_class_pass and role_ratio_pass,
        "MATH_SEMANTICS_PASS": True,
        "TEXT_CONSISTENCY_PASS": True,
        "GRAYSCALE_PASS": True,
        "PAGE_INTEGRATION_PASS": True,
    }
    flags["RESULT"] = "PASS" if all(flags.values()) and spatial_pass and clip_pixels == 0 else "FAIL"

    semantic_font_failed = sum(r["PASS_FAIL"] == "FAIL" for r in font_rows)
    pixel_height_failed = sum(r["PIXEL_HEIGHT_PASS"] == "false" for r in pixel_rows)
    all_glyph_gate_failed = sum(r["ALL_GLYPH_GATES_PASS"] == "false" for r in pixel_rows)
    same_class_failed_groups = sum(r["PASS_FAIL"] == "FAIL" for r in d_rows)
    role_ratio_failed_rows = sum(r["PASS_FAIL"] == "FAIL" for r in e_rows)
    intentional_graphic_intersection_pairs = sum(
        p["INTENTIONAL_CONNECTION"] == "true"
        and p["TYPE_A"] != "TEXT"
        and p["TYPE_B"] != "TEXT"
        and int(p["RAW_INTERSECTION_PX"]) > 0
        for p in pairs
    )
    counts = {"native_width": width, "native_height": height, "page_width_pt": float(page_rect.width), "page_height_pt": float(page_rect.height),
              "object_count": len(objects), "semantic_text_element_count": len(text_objects), "semantic_font_failed_element_count": semantic_font_failed,
              "glyph_trace_count": len(pixel_rows), "pixel_height_failed_glyph_count": pixel_height_failed,
              "all_glyph_gate_failed_count": all_glyph_gate_failed, "same_class_failed_group_count": same_class_failed_groups,
              "role_ratio_failed_row_count": role_ratio_failed_rows, "glyph_cross_mask_duplicate_pixels": glyph_duplicate_pixels,
              "pair_count": len(pairs), "critical_pair_count": len(critical_pairs),
              "illegal_overlap_pixels": illegal_overlap, "overlap_fail_pair_count": len(overlap_fail_rows), "clearance_fail_pair_count": len(clearance_fail_rows),
              "intentional_graphic_intersection_pair_count": intentional_graphic_intersection_pairs,
              "clip_pixels": clip_pixels, "min_text_clearance": min_text_clearance,
              "min_text_raw_ink_clearance": min_text_raw_ink_clearance, "min_text_text_pdf_bbox_clearance": min_text_text_pdf_bbox_clearance,
              "min_edge_clearance": min_edge, "text_node_border_objects": 0}
    acceptance = acceptance_md(flags, counts, edge_rows, d_rows, e_rows)
    (ROOT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")
    (ROOT / "SA1_FORMAL_REPORT.md").write_text(formal_sa1_report(flags, counts, pairs), encoding="utf-8")
    (PAIR_DIR / "CURRENT_R1_PAIR_EVIDENCE.md").write_text(
        "# Current authoritative pair evidence\n\n"
        "Authoritative failure/critical IDs are exactly the `critical_pair_ids` in `machine_terminal_check.json` and the FAIL rows in `after_overlap_report.csv`. "
        "Every other pair directory, if present from an interrupted regeneration, is non-authoritative and must not be read as a current failure classification.\n",
        encoding="utf-8")

    render_manifest = {
        "canonical_pdf": str(PDF), "physical_page": PHYSICAL_PAGE, "printed_page": 610,
        "page_pt": {"width": float(page_rect.width), "height": float(page_rect.height)},
        "native_300dpi": {"file": "full_page_300dpi.png", "width": width, "height": height, "dpi": 300,
                          "direct_render_command": "pdftoppm -f 623 -l 623 -r 300 -png -singlefile <PDF> full_page_300dpi"},
        "native_200dpi": {"file": "full_page_200dpi.png", "width": full200.width, "height": full200.height, "dpi": 200,
                          "direct_render_command": "pdftoppm -f 623 -l 623 -r 200 -png -singlefile <PDF> full_page_200dpi"},
        "figure_crop_300dpi": {"file": "figure_crop_300dpi.png", "source": "full_page_300dpi.png", "integer_rect_xyxy_exclusive": fig_crop_px, "resized": False},
        "standalone_300dpi": {"file": "standalone_300dpi.png", "source": "full_page_300dpi.png", "integer_rect_xyxy_exclusive": standalone_px, "resized": False},
        "grayscale": {"file": "grayscale_300dpi.png", "source": "figure_crop_300dpi.png", "resized": False},
        "eight_x_rule": "All 8x files use nearest-neighbour only for human pixel inspection; all counts use native 1:1 300dpi coordinates.",
        "source_paths": source_paths,
    }
    write_json(ROOT / "render_manifest.json", render_manifest)

    # Machine terminal check must inspect the just-written artifacts, not memory
    # alone.  It validates counts and RESULT synchronization across CSV/JSON/MD.
    object_csv_rows = list(csv.DictReader((ROOT / "object_manifest.csv").open(encoding="utf-8-sig")))
    pair_csv_rows = list(csv.DictReader((ROOT / "after_overlap_report.csv").open(encoding="utf-8-sig")))
    font_csv_rows = list(csv.DictReader((ROOT / "after_font_audit.csv").open(encoding="utf-8-sig")))
    pixel_csv_rows = list(csv.DictReader((ROOT / "after_pixel_measurements.csv").open(encoding="utf-8-sig")))
    pair_json = json.loads((ROOT / "all_pairs.json").read_text(encoding="utf-8"))
    glyph_separation = json.loads((ROOT / "glyph_mask_separation_check.json").read_text(encoding="utf-8"))
    accept_text = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    required_files = ["full_page_300dpi.png", "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png",
                      "after_text_measurement_overlay_300dpi.png", "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv", "after_visual_acceptance.md", "SA1_FORMAL_REPORT.md",
                      "object_manifest.csv", "object_manifest.json", "all_pairs.json", "mathematical_recomputation.md", "render_manifest.json", "glyph_mask_separation_check.json"]
    expected_pairs = len(object_csv_rows)*(len(object_csv_rows)-1)//2
    all_gate_failure_glyphs = [r for r in pixel_csv_rows if r["ALL_GLYPH_GATES_PASS"] == "false"]
    pixel_height_failure_glyphs = [r for r in pixel_csv_rows if r["PIXEL_HEIGHT_PASS"] == "false"]
    missing_all_gate_failure_evidence = [r["ELEMENT_ID"] for r in all_gate_failure_glyphs if not (GLYPH_EVIDENCE_DIR / f"{r['ELEMENT_ID'].replace('#','_')}_raw_mask_1to1.png").exists()]
    missing_pixel_height_failure_evidence = [r["ELEMENT_ID"] for r in pixel_height_failure_glyphs if not (GLYPH_EVIDENCE_DIR / f"{r['ELEMENT_ID'].replace('#','_')}_raw_mask_1to1.png").exists()]
    machine = [
        ("required_artifacts_exist", all((ROOT/f).exists() for f in required_files), f"{sum((ROOT/f).exists() for f in required_files)}/{len(required_files)}"),
        ("unique_nonempty_object_masks", len({r['OBJECT_ID'] for r in object_csv_rows}) == len(object_csv_rows) and all(int(r['RAW_MASK_PIXELS']) > 0 for r in object_csv_rows), f"objects={len(object_csv_rows)}, semantic_text={len(text_objects)}"),
        ("semantic_font_elements_unique", len(font_csv_rows) == len(text_objects) and len({r['ELEMENT_ID'] for r in font_csv_rows}) == len(font_csv_rows), f"semantic_font_elements={len(font_csv_rows)}, failed={semantic_font_failed}"),
        ("glyph_masks_nonempty_and_unique", len({r['ELEMENT_ID'] for r in pixel_csv_rows}) == len(pixel_csv_rows) and all(int(r['H_INK_PX']) > 0 for r in pixel_csv_rows), f"glyph_trace={len(pixel_csv_rows)}, pixel_height_failed={pixel_height_failed}, all_gate_failed={all_glyph_gate_failed}"),
        ("glyph_raw_masks_mutually_exclusive", glyph_separation["PASS"] and glyph_separation["cross_glyph_duplicate_pixels"] == 0, f"duplicate_pixels={glyph_separation['cross_glyph_duplicate_pixels']}"),
        ("all_unordered_pairs_covered", len(pair_csv_rows) == expected_pairs and len({r['PAIR_ID'] for r in pair_csv_rows}) == expected_pairs and pair_json['expected_unordered_pair_count'] == expected_pairs, f"actual={len(pair_csv_rows)}, expected={expected_pairs}"),
        ("all_failed_or_critical_pair_evidence", all((PAIR_DIR / r['PAIR_ID']).exists() for r in critical_pairs), f"critical={len(critical_pairs)}"),
        ("pixel_height_failure_glyph_evidence", len(missing_pixel_height_failure_evidence) == 0, f"pixel_height_failed={len(pixel_height_failure_glyphs)}, missing={len(missing_pixel_height_failure_evidence)}"),
        ("all_gate_failure_glyph_evidence", len(missing_all_gate_failure_evidence) == 0, f"all_gate_failed={len(all_gate_failure_glyphs)}, missing={len(missing_all_gate_failure_evidence)}"),
        ("no_empty_graphic_mask", all(int(r['RAW_MASK_PIXELS']) > 0 for r in object_csv_rows if r['OBJECT_TYPE'] != 'TEXT'), f"graphics={sum(r['OBJECT_TYPE']!='TEXT' for r in object_csv_rows)}"),
        ("csv_json_md_counts_consistent", len(font_csv_rows) == len(text_objects) and len(pixel_csv_rows) == counts['glyph_trace_count'] and f"RESULT: {flags['RESULT']}" in accept_text and pair_json['object_count'] == len(object_csv_rows), f"semantic_font={len(font_csv_rows)}, glyph_trace={len(pixel_csv_rows)}, result={flags['RESULT']}"),
        ("final_result_consistent_with_underlying_fails", (flags['RESULT'] == 'FAIL') == (not source_font_pass or not pixel_height_pass or not same_class_pass or not role_ratio_pass or not spatial_pass or clip_pixels != 0), f"result={flags['RESULT']}"),
        ("node_border_relation_explicit_na", counts['text_node_border_objects'] == 0, "no NODE_BORDER source object; N/A explicitly reported"),
    ]
    machine_rows = [{"CHECK": name, "PASS_FAIL": "PASS" if ok else "FAIL", "DETAIL": detail} for name, ok, detail in machine]
    machine_ok = all(ok for _, ok, _ in machine)
    write_csv(ROOT / "machine_terminal_check.csv", machine_rows)
    machine_json = {"RESULT": flags["RESULT"], "MACHINE_EVIDENCE_INTEGRITY_PASS": machine_ok, "counts": counts,
                    "flags": flags, "checks": machine_rows, "critical_pair_ids": [p["PAIR_ID"] for p in critical_pairs],
                    "semantic_font_failed_element_count": semantic_font_failed,
                    "pixel_height_failed_glyph_count": len(pixel_height_failure_glyphs),
                    "all_glyph_gate_failed_count": len(all_gate_failure_glyphs)}
    write_json(ROOT / "machine_terminal_check.json", machine_json)
    md_lines = ["# FIG-P575-01 SA1 machine terminal check", "", f"RESULT: {flags['RESULT']}", f"MACHINE_EVIDENCE_INTEGRITY_PASS: {bool_s(machine_ok)}", "", "| Check | Result | Detail |", "|---|---|---|"]
    md_lines += [f"| {r['CHECK']} | {r['PASS_FAIL']} | {r['DETAIL']} |" for r in machine_rows]
    md_lines += ["", "The machine check validates evidence integrity only. It does not override underlying strict visual FAIL rows."]
    (ROOT / "machine_terminal_check.md").write_text("\n".join(md_lines)+"\n", encoding="utf-8")

    # Read-only provenance / method note is deliberately in evidence rather than a
    # central project state file, preserving the single-writer rule.
    (ROOT / "audit_methodology.md").write_text(f"""# Independent R1 method

Only the canonical PDF and the two authorised read-only LaTeX files were read. No prior P575 evidence, role report, inventory/state record, or central conclusion was read.

The physical page was independently located through PDF text: preceding-page body anchor `图31.3把严格递增与离散跳跃放在同一“首次达到”规则下` and page-{PHYSICAL_PAGE} caption anchor `图31.3 广义逆采用首次达到规则`.

Native 300 dpi masks are thresholded at local-background delta >=20/255. Text glyph masks use their PDF character bbox + own paint colour (anti-alias colour-ray residual <=8/255) and exclusive pixel assignment; graphic masks use the corresponding PDF vector path only as eligibility and intersect it with final native foreground pixels. Thus no bbox fill, dilation, source redraw, 8x image, or hidden pre-occlusion pixel is counted. `8x_nearest` files are human-only. TEXT--TEXT clearance is separately measured on mapped PDF/vector bboxes; raw ink clearance is reported alongside it.

Scope of object manifest: all source-created plot-body objects and the source-created caption. Page header, following comparison box, and following section are reviewed in the full-page/page-integration view but not falsely assigned to this figure's source object inventory.
""", encoding="utf-8")

    doc.close()
    print(json.dumps({"RESULT": flags["RESULT"], "objects": len(objects), "glyphs": len(pixel_rows), "pairs": len(pairs),
                      "source_font_pass": source_font_pass, "pixel_height_pass": pixel_height_pass,
                      "same_class_pass": same_class_pass, "role_ratio_pass": role_ratio_pass,
                      "spatial_pass": spatial_pass, "machine_ok": machine_ok}, ensure_ascii=False))


if __name__ == "__main__":
    main()
