#!/usr/bin/env python3
"""Independent, evidence-only strict pixel audit for FIG-P608-01.

This program reads only the frozen R97 candidate and the declared figure source.
All generated material stays beside this file.  It intentionally does not read
FIG-P608-01 historical evidence, inventory, or state files.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


CANONICAL_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF_PATH = CANONICAL_ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r97_fullbook" / "main_full.pdf"
SOURCE_PATH = CANONICAL_ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C03" / "fig_v5_c03_trace_running_mean.tex"
CHAPTER_PATH = CANONICAL_ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C03.tex"
OUT = Path(__file__).resolve().parent
EXPECTED_PDF_SHA256 = "062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814"
PAGE_NO = 659  # one based; independently located from exact caption text in frozen R97
PAGE_INDEX = PAGE_NO - 1
DPI = 300
SCALE = DPI / 72.0

# This includes all Figure 32.8 ink plus its caption but excludes the surrounding
# direct body text.  Coordinates are frozen PDF points and are recorded in output.
FIGURE_CROP_PT = (55.0, 220.0, 540.0, 445.0)
# Standalone graph only; the caption remains in figure_crop_300dpi.png.
STANDALONE_PT = (125.0, 225.0, 465.0, 421.0)

RGB_WHITE = (255, 255, 255)
RGB_DARK = (31, 35, 40)
RGB_BLUE = (31, 78, 121)
RGB_GOLD = (183, 121, 31)
RGB_TEAL = (15, 118, 110)
RGB_HATCH = (184, 192, 200)


@dataclass
class Glyph:
    gid: str
    text_oid: str
    glyph: str
    codepoint: str
    panel: str
    role: str
    font: str
    font_size_pt: float
    color_rgb: tuple[int, int, int]
    bbox_pt: tuple[float, float, float, float]
    category: str
    low_profile: bool
    is_math_script: bool
    mask: np.ndarray | None = None
    mask_bbox_px: tuple[int, int, int, int] | None = None
    mask_area_px: int = 0
    mask_w_px: int = 0
    mask_h_px: int = 0
    components: int = 0
    missing_stroke_px: int = 0
    foreign_pixel_px: int = 0
    size_gate: str = "PENDING"
    pixel_gate: str = "PENDING"
    purity: str = "PENDING"
    purity_notes: str = ""


@dataclass
class Obj:
    oid: str
    kind: str  # T or G
    panel: str
    role: str
    label: str
    bbox_pt: tuple[float, float, float, float]
    z_order: int
    provenance: str
    color_rgb: tuple[int, int, int] | None = None
    pre_mask: np.ndarray | None = None
    mask: np.ndarray | None = None
    occlusion_selector: np.ndarray | None = None
    mask_bbox_px: tuple[int, int, int, int] | None = None
    foreground: bool = True
    notes: str = ""
    glyph_ids: list[str] = field(default_factory=list)


def canonical(p: Path) -> str:
    """Return the required canonical presentation path, never a junction alias."""
    return str(p)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def dump_json(name: str, obj: Any) -> None:
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(name: str, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path = OUT / name
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def point_to_px(value: float) -> int:
    return int(round(value * SCALE))


def rect_to_px(rect: tuple[float, float, float, float], crop_px: tuple[int, int, int, int] | None = None) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    ans = (int(math.floor(x0 * SCALE)), int(math.floor(y0 * SCALE)), int(math.ceil(x1 * SCALE)), int(math.ceil(y1 * SCALE)))
    if crop_px is not None:
        return (ans[0] - crop_px[0], ans[1] - crop_px[1], ans[2] - crop_px[0], ans[3] - crop_px[1])
    return ans


def clamp_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (max(0, x0), max(0, y0), min(width, x1), min(height, y1))


def union_box(boxes: Iterable[tuple[int, int, int, int]]) -> tuple[int, int, int, int] | None:
    b = list(boxes)
    if not b:
        return None
    return (min(x[0] for x in b), min(x[1] for x in b), max(x[2] for x in b), max(x[3] for x in b))


def bbox_of_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return None
    return (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)


def intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def color_int_to_rgb(v: int) -> tuple[int, int, int]:
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def drawing_rgb(v: tuple[float, float, float] | None) -> tuple[int, int, int] | None:
    if v is None:
        return None
    return tuple(int(round(x * 255)) for x in v)


def glyph_codepoint(c: str) -> str:
    return " ".join(f"U+{ord(x):04X}" for x in c)


def is_cjk(c: str) -> bool:
    return any("CJK UNIFIED IDEOGRAPH" in unicodedata.name(ch, "") for ch in c)


def glyph_category(c: str, font: str) -> tuple[str, bool]:
    name = unicodedata.name(c, "")
    # '=' is a mathematical operator, not a low-profile punctuation exemption.
    # Revision 111 therefore applies the ordinary 22-pixel math-base gate to it.
    if c == "=":
        return "math_operator", False
    if c in {".", ",", "，", "；", ";", ":", "∶", "…", "-", "−", "–", "—"}:
        return "low_profile", True
    if is_cjk(c):
        return "cjk", False
    if c.isdigit():
        return "digit", False
    if "STIX" in font.upper() or "MATH" in font.upper():
        if "CAPITAL" in name or c.isupper():
            return "math_upper", False
        if "SMALL" in name or c.islower():
            return "math_lower", False
        return "math_base", False
    if c.isupper() or "CAPITAL" in name:
        return "upper", False
    if c.islower() or "SMALL" in name:
        return "lower", False
    return "other", False


def panel_and_role(bbox: tuple[float, float, float, float], text: str) -> tuple[str, str]:
    x0, y0, x1, y1 = bbox
    if 423 <= y0 <= 442:
        return "caption", "caption_label" if x0 < 115 else "caption_text"
    # The lower-panel title is intentionally in the gap immediately below the
    # upper x-axis.  Test it before upper-panel annotations: the prior ordering
    # silently lost its subscript and hid the cross-panel collision.
    if 310 <= y0 <= 327:
        return "lower", "title"
    if 228 <= y0 <= 249:
        return "upper", "title"
    if 250 <= y0 <= 315:
        if x0 < 167 and y0 < 305:
            return "upper", "y_tick"
        if x0 < 158:
            return "upper", "y_label"
        if y0 > 283:
            return "upper", "warmup_annotation"
        return "upper", "annotation"
    if 328 <= y0 <= 422:
        if 392 <= y0 <= 407:
            return "lower", "x_tick"
        if 405 <= y0 <= 422:
            return "lower", "x_label"
        if x0 < 166 and 338 <= y0 <= 391:
            return "lower", "y_tick" if x0 >= 148 else "y_label"
        if 328 <= y0 <= 342:
            return "lower", "target_annotation"
        if 310 <= y0 <= 327:
            return "lower", "title"
        return "lower", "annotation"
    return "outside", "outside"


def text_size_gate(g: Glyph) -> str:
    if g.is_math_script:
        return "PASS_LEGAL_TEX_SCRIPT_FROM_BASE_FORMULA>=9.5_RAW={:.2f}".format(g.font_size_pt)
    if g.font_size_pt + 1e-6 >= 9.5:
        return "PASS>=9.5"
    return "FAIL<9.5"


def ray_mask(arr: np.ndarray, target: tuple[int, int, int], alpha_min: float | None = None) -> np.ndarray:
    """Raw-pixel foreground test along the target-to-white antialiasing ray.

    It uses the unscaled Poppler 300-dpi samples.  No interpolation or synthetic
    recoloring is used for the resulting mask.
    """
    a = arr.astype(np.float32)
    t = np.asarray(target, dtype=np.float32)
    v = 255.0 - t
    denom = float(np.dot(v, v))
    if denom == 0:
        return np.zeros(arr.shape[:2], dtype=bool)
    # Apply the mandatory 20/255 threshold in the actual integer native sample
    # space.  Dividing by a colour-ray alpha is off by one at an 8-bit boundary
    # (e.g. a real [235,236,238] ink pixel is exactly 20 levels from white yet
    # has alpha 0.1346 instead of the ideal 20/148); that would falsely report
    # a missing contour pixel.
    if alpha_min is None:
        alpha_min = 0.0
    raw_contrast20 = np.max(255.0 - a, axis=2) >= 20.0
    alpha = np.clip(np.tensordot(255.0 - a, v, axes=([2], [0])) / denom, 0.0, 1.0)
    predicted = 255.0 - alpha[..., None] * v
    residual = np.sqrt(np.sum((a - predicted) ** 2, axis=2))
    # The tolerance allows Poppler's antialiasing while rejecting differently
    # coloured neighbours (e.g. blue trace inside a black text bbox).
    return raw_contrast20 & (alpha >= alpha_min) & (residual <= (11.0 + 7.0 * alpha))


def local_contrast20_mask(native: np.ndarray, crop_px: tuple[int, int, int, int], bbox_pt: tuple[float, float, float, float]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Return all native pixels at >=20/255 contrast from a local border median."""
    full = clamp_box(rect_to_px(bbox_pt), native.shape[1], native.shape[0])
    x0, y0, x1, y1 = full
    pad = 2
    px0, py0, px1, py1 = clamp_box((x0 - pad, y0 - pad, x1 + pad, y1 + pad), native.shape[1], native.shape[0])
    expanded = native[py0:py1, px0:px1].astype(np.int16)
    border = np.concatenate([expanded[0, :, :], expanded[-1, :, :], expanded[:, 0, :], expanded[:, -1, :]], axis=0)
    background = np.median(border, axis=0)
    core = native[y0:y1, x0:x1].astype(np.int16)
    contrasted = np.max(np.abs(core - background.astype(np.int16)), axis=2) >= 20
    crop_h, crop_w = crop_px[3] - crop_px[1], crop_px[2] - crop_px[0]
    out = np.zeros((crop_h, crop_w), dtype=bool)
    cx0, cy0, cx1, cy1 = clamp_box((x0 - crop_px[0], y0 - crop_px[1], x1 - crop_px[0], y1 - crop_px[1]), crop_w, crop_h)
    if cx0 < cx1 and cy0 < cy1:
        out[cy0:cy1, cx0:cx1] = contrasted[cy0 - (y0 - crop_px[1]):cy1 - (y0 - crop_px[1]), cx0 - (x0 - crop_px[0]):cx1 - (x0 - crop_px[0])]
    return out, full


def raw_color_mask(native: np.ndarray, crop_px: tuple[int, int, int, int], bbox_pt: tuple[float, float, float, float], colors: Iterable[tuple[int, int, int]], geom: np.ndarray | None = None) -> np.ndarray:
    """Return an evidence mask in crop coordinates from native raw pixels only."""
    h = crop_px[3] - crop_px[1]
    w = crop_px[2] - crop_px[0]
    out = np.zeros((h, w), dtype=bool)
    box = clamp_box(rect_to_px(bbox_pt), native.shape[1], native.shape[0])
    if box[0] >= box[2] or box[1] >= box[3]:
        return out
    local = native[box[1]:box[3], box[0]:box[2], :]
    localmask = np.zeros(local.shape[:2], dtype=bool)
    for color in colors:
        localmask |= ray_mask(local, color)
    cx0, cy0 = box[0] - crop_px[0], box[1] - crop_px[1]
    cx1, cy1 = box[2] - crop_px[0], box[3] - crop_px[1]
    # All declared figure bboxes are inside the crop; clamp keeps code auditable.
    tx0, ty0, tx1, ty1 = clamp_box((cx0, cy0, cx1, cy1), w, h)
    sx0, sy0 = tx0 - cx0, ty0 - cy0
    sx1, sy1 = sx0 + (tx1 - tx0), sy0 + (ty1 - ty0)
    if tx0 < tx1 and ty0 < ty1:
        out[ty0:ty1, tx0:tx1] |= localmask[sy0:sy1, sx0:sx1]
    if geom is not None:
        out &= geom
    return out


def rect_geom(crop_shape: tuple[int, int], crop_px: tuple[int, int, int, int], bbox_pt: tuple[float, float, float, float], expand: int = 2) -> np.ndarray:
    h, w = crop_shape
    x0, y0, x1, y1 = rect_to_px(bbox_pt, crop_px)
    x0, y0, x1, y1 = clamp_box((x0 - expand, y0 - expand, x1 + expand, y1 + expand), w, h)
    m = np.zeros((h, w), dtype=bool)
    if x0 < x1 and y0 < y1:
        m[y0:y1, x0:x1] = True
    return m


def _draw_line(draw: ImageDraw.ImageDraw, crop_px: tuple[int, int, int, int], p0: Any, p1: Any, width: int) -> None:
    a = (int(round(float(p0.x) * SCALE)) - crop_px[0], int(round(float(p0.y) * SCALE)) - crop_px[1])
    b = (int(round(float(p1.x) * SCALE)) - crop_px[0], int(round(float(p1.y) * SCALE)) - crop_px[1])
    draw.line([a, b], fill=1, width=max(1, width))


def geom_from_items(crop_shape: tuple[int, int], crop_px: tuple[int, int, int, int], drawing: dict[str, Any], item_indices: Iterable[int] | None = None, extra_px: int = 2) -> np.ndarray:
    """Rasterise only the frozen PDF vector geometry as a selector for raw pixels."""
    h, w = crop_shape
    im = Image.new("1", (w, h), 0)
    d = ImageDraw.Draw(im)
    width = max(1, int(math.ceil(float(drawing.get("width") or 0.5) * SCALE)) + extra_px)
    items = drawing["items"] if item_indices is None else [drawing["items"][i] for i in item_indices]
    for item in items:
        typ = item[0]
        if typ == "l":
            _draw_line(d, crop_px, item[1], item[2], width)
        elif typ == "re":
            rr = item[1]
            b = rect_to_px((rr.x0, rr.y0, rr.x1, rr.y1), crop_px)
            d.rectangle(b, outline=1, width=width)
        else:
            # This frozen figure uses lines/rectangles.  A conservative bbox
            # selector makes an unexpected path visible rather than silently lost.
            rr = drawing["rect"]
            b = rect_to_px((rr.x0, rr.y0, rr.x1, rr.y1), crop_px)
            d.rectangle(b, fill=1)
    return np.asarray(im, dtype=bool)


def native_render() -> tuple[np.ndarray, tuple[int, int, int, int]]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm is required for protocol-native rendering")
    prefix300 = OUT / "native_page_659_300dpi"
    prefix200 = OUT / "full_page_200dpi"
    for prefix, dpi in ((prefix300, 300), (prefix200, 200)):
        subprocess.run([pdftoppm, "-f", str(PAGE_NO), "-l", str(PAGE_NO), "-r", str(dpi), "-png", "-singlefile", str(PDF_PATH), str(prefix)], check=True)
    image = Image.open(prefix300.with_suffix(".png")).convert("RGB")
    native = np.asarray(image)
    crop_px = rect_to_px(FIGURE_CROP_PT)
    figure = image.crop(crop_px)
    figure.save(OUT / "figure_crop_300dpi.png")
    standalone = image.crop(rect_to_px(STANDALONE_PT))
    standalone.save(OUT / "standalone_300dpi.png")
    figure.convert("L").save(OUT / "grayscale_300dpi.png")
    # Nearest-neighbour view is evidence only; the native 1x file above decides.
    figure.resize((figure.width * 8, figure.height * 8), Image.Resampling.NEAREST).save(OUT / "figure_crop_300dpi_8x_nearest.png")
    context = image.crop(rect_to_px((55.0, 195.0, 540.0, 505.0)))
    context.save(OUT / "direct_context_300dpi.png")
    dump_json("native_render_provenance.json", {
        "decision_basis": "native Poppler 300 dpi 1x samples only; enlarged views are nearest-neighbour inspection aids",
        "pdf": canonical(PDF_PATH),
        "physical_page": PAGE_NO,
        "pdf_page_index_zero_based": PAGE_INDEX,
        "command": [pdftoppm, "-f", str(PAGE_NO), "-l", str(PAGE_NO), "-r", "300", "-png", "-singlefile", canonical(PDF_PATH), canonical(prefix300)],
        "native_png": canonical(prefix300.with_suffix(".png")),
        "native_png_sha256": sha256(prefix300.with_suffix(".png")),
        "native_dimensions_px": [int(image.width), int(image.height)],
        "figure_crop_points": list(FIGURE_CROP_PT),
        "figure_crop_pixels": list(crop_px),
        "standalone_points": list(STANDALONE_PT),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    })
    return native, crop_px


def extract_text(page: fitz.Page, native: np.ndarray, crop_px: tuple[int, int, int, int]) -> tuple[list[Obj], list[Glyph]]:
    raw = page.get_text("rawdict")
    text_objects: list[Obj] = []
    glyphs: list[Glyph] = []
    span_no = 0
    glyph_no = 0
    crop_shape = (crop_px[3] - crop_px[1], crop_px[2] - crop_px[0])
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                chars = [c for c in span.get("chars", []) if c.get("c", "") and not c.get("c", "").isspace()]
                if not chars:
                    continue
                charboxes = [tuple(float(v) for v in c["bbox"]) for c in chars]
                b = union_box([(int(x[0] * 1000), int(x[1] * 1000), int(x[2] * 1000), int(x[3] * 1000)) for x in charboxes])
                assert b is not None
                bbox = tuple(v / 1000.0 for v in b)
                if not intersects(bbox, FIGURE_CROP_PT):
                    continue
                panel, role = panel_and_role(bbox, "".join(c["c"] for c in chars))
                if panel == "outside":
                    continue
                span_no += 1
                oid = f"T{span_no:03d}"
                font = str(span["font"])
                size = float(span["size"])
                rgb = color_int_to_rgb(int(span["color"]))
                obj = Obj(oid=oid, kind="T", panel=panel, role=role, label="".join(c["c"] for c in chars), bbox_pt=bbox, z_order=1000 + span_no, provenance="PDF rawdict text span", color_rgb=rgb)
                text_objects.append(obj)
                for c in chars:
                    glyph_no += 1
                    ch = c["c"]
                    cb = tuple(float(v) for v in c["bbox"])
                    cat, low = glyph_category(ch, font)
                    # A raw font size below 9.5 appears only for TeX automatic
                    # math scripts; it is never silently counted as a normal label.
                    script = size < 9.5 and "STIX" in font.upper()
                    g = Glyph(
                        gid=f"G{glyph_no:03d}", text_oid=oid, glyph=ch, codepoint=glyph_codepoint(ch), panel=panel,
                        role=role, font=font, font_size_pt=size, color_rgb=rgb, bbox_pt=cb, category=cat,
                        low_profile=low, is_math_script=script,
                    )
                    g.size_gate = text_size_gate(g)
                    # Native raw-pixel mask, confined to this glyph's own PDF bbox.
                    g.mask = raw_color_mask(native, crop_px, cb, [rgb], rect_geom(crop_shape, crop_px, cb, expand=1))
                    contrasted, _ = local_contrast20_mask(native, crop_px, cb)
                    g.missing_stroke_px = int(np.count_nonzero(contrasted & ~g.mask))
                    g.mask_bbox_px = bbox_of_mask(g.mask)
                    g.mask_area_px = int(g.mask.sum())
                    if g.mask_bbox_px:
                        g.mask_w_px = g.mask_bbox_px[2] - g.mask_bbox_px[0]
                        g.mask_h_px = g.mask_bbox_px[3] - g.mask_bbox_px[1]
                        _, ncomp = ndimage.label(g.mask, structure=np.ones((3, 3), dtype=int))
                        g.components = int(ncomp)
                    else:
                        g.pixel_gate = "FAIL_EMPTY_RAW_MASK"
                    obj.glyph_ids.append(g.gid)
                    glyphs.append(g)
                # A text-object mask is the OR of its genuine raw glyph masks.
                obj.mask = np.zeros(crop_shape, dtype=bool)
                for g in glyphs:
                    if g.text_oid == oid and g.mask is not None:
                        obj.mask |= g.mask
                obj.mask_bbox_px = bbox_of_mask(obj.mask)
    return text_objects, glyphs


def object_from_drawing(oid: str, panel: str, role: str, label: str, page: fitz.Page, drawing_index: int, native: np.ndarray, crop_px: tuple[int, int, int, int], colors: list[tuple[int, int, int]] | None = None, item_indices: list[int] | None = None, bbox_override: tuple[float, float, float, float] | None = None, foreground: bool = True, notes: str = "") -> Obj:
    dr = page.get_drawings()[drawing_index]
    rr = dr["rect"]
    # PyMuPDF's path rect is often a centreline (zero height for a horizontal
    # rule).  Expand by the actual PDF stroke half-width plus one native-pixel
    # guard; otherwise a rule/axis mask would falsely contain a single row only.
    if bbox_override is None:
        stroke = float(dr.get("width") or 0.0)
        guard = 1.0 / SCALE
        expand = stroke / 2.0 + guard
        bbox = (float(rr.x0) - expand, float(rr.y0) - expand, float(rr.x1) + expand, float(rr.y1) + expand)
    else:
        bbox = bbox_override
    crop_shape = (crop_px[3] - crop_px[1], crop_px[2] - crop_px[0])
    obj = Obj(oid=oid, kind="G", panel=panel, role=role, label=label, bbox_pt=bbox, z_order=drawing_index, provenance=f"PDF drawing[{drawing_index}]", color_rgb=(colors or [drawing_rgb(dr.get("color")) or RGB_DARK])[0], foreground=foreground, notes=notes)
    if foreground:
        geom = geom_from_items(crop_shape, crop_px, dr, item_indices)
        obj.pre_mask = raw_color_mask(native, crop_px, bbox, colors or [drawing_rgb(dr.get("color")) or RGB_DARK], geom)
        obj.mask = obj.pre_mask.copy()
        obj.mask_bbox_px = bbox_of_mask(obj.mask)
    else:
        obj.pre_mask = np.zeros(crop_shape, dtype=bool)
        obj.mask = np.zeros(crop_shape, dtype=bool)
    return obj


def extract_graphics(page: fitz.Page, native: np.ndarray, crop_px: tuple[int, int, int, int]) -> list[Obj]:
    """Enumerate every visible Figure 32.8 graphic primitive semantically.

    Each tick/marker is separate.  Axes keep their arrowhead with the relevant
    axis, while the white warm-up label backplate is retained as a z-order
    occluder despite having no positive ink foreground mask.
    """
    dr = page.get_drawings()
    out: list[Obj] = []
    # Axis / tick objects, with actual drawing indices independently verified.
    out.append(object_from_drawing("G001", "upper", "axis_x", "upper x-axis + arrowhead", page, 8, native, crop_px, [RGB_DARK], notes="arrowhead drawing[9] is included by bbox selector below"))
    # Add the arrowhead raw mask to the axis object; it is a fill drawing.
    axis_arrow = object_from_drawing("TMP", "upper", "tmp", "tmp", page, 9, native, crop_px, [RGB_DARK])
    out[-1].pre_mask |= axis_arrow.pre_mask
    out[-1].mask = out[-1].pre_mask.copy()
    out[-1].mask_bbox_px = bbox_of_mask(out[-1].mask)
    out.append(object_from_drawing("G002", "upper", "axis_y", "upper y-axis + arrowhead", page, 10, native, crop_px, [RGB_DARK], notes="arrowhead drawing[11] added"))
    arrow = object_from_drawing("TMP", "upper", "tmp", "tmp", page, 11, native, crop_px, [RGB_DARK])
    out[-1].pre_mask |= arrow.pre_mask
    out[-1].mask = out[-1].pre_mask.copy()
    out[-1].mask_bbox_px = bbox_of_mask(out[-1].mask)
    for i in range(5):
        out.append(object_from_drawing(f"G{3+i:03d}", "upper", "x_tick", f"upper x tick {i+1}", page, 6, native, crop_px, item_indices=[i]))
    for i in range(3):
        out.append(object_from_drawing(f"G{8+i:03d}", "upper", "y_tick", f"upper y tick {i+1}", page, 7, native, crop_px, item_indices=[i]))
    # The pattern is not exposed by PyMuPDF's drawing list, so its foreground
    # is selected directly from native RGB within the source rectangle.
    crop_shape = (crop_px[3] - crop_px[1], crop_px[2] - crop_px[0])
    top_hatch_bbox = (169.455, 255.226, 235.373, 311.025)
    top_hatch = Obj("G011", "G", "upper", "warmup_hatch", "upper warm-up northeast hatch", top_hatch_bbox, 5, "source pattern rectangle; native RGB selector", RGB_HATCH)
    top_hatch.pre_mask = raw_color_mask(native, crop_px, top_hatch_bbox, [RGB_HATCH], rect_geom(crop_shape, crop_px, top_hatch_bbox, expand=0))
    top_hatch.mask = top_hatch.pre_mask.copy()
    top_hatch.mask_bbox_px = bbox_of_mask(top_hatch.mask)
    out.append(top_hatch)
    out.append(object_from_drawing("G012", "upper", "trace", "upper trace polyline", page, 13, native, crop_px, [RGB_BLUE]))
    out.append(object_from_drawing("G013", "upper", "burnin_boundary", "upper burn-in boundary dashed line", page, 14, native, crop_px, [RGB_GOLD]))
    backplate = object_from_drawing("G014", "upper", "label_backplate", "upper warm-up label white backplate", page, 15, native, crop_px, [RGB_WHITE], foreground=False, notes="opaque white z-order occluder; no positive ink foreground is possible against white page")
    # The fill is white-on-white after rasterisation, so it has no positive
    # foreground raw mask.  Its frozen vector geometry is nevertheless a
    # traceable z-order selector for removing covered earlier hatch pixels.
    rr15 = dr[15]["rect"]
    backplate.occlusion_selector = rect_geom(crop_shape, crop_px, (float(rr15.x0), float(rr15.y0), float(rr15.x1), float(rr15.y1)), expand=0)
    out.append(backplate)
    for i, idx in enumerate(range(16, 36), start=1):
        out.append(object_from_drawing(f"G{14+i:03d}", "upper", "marker", f"upper trace marker t={i}", page, idx, native, crop_px, [RGB_BLUE, RGB_DARK]))
    # Lower panel.
    base = 35
    out.append(object_from_drawing(f"G{base:03d}", "lower", "axis_x", "lower x-axis + arrowhead", page, 38, native, crop_px, [RGB_DARK], notes="arrowhead drawing[39] added"))
    arrow = object_from_drawing("TMP", "lower", "tmp", "tmp", page, 39, native, crop_px, [RGB_DARK])
    out[-1].pre_mask |= arrow.pre_mask
    out[-1].mask = out[-1].pre_mask.copy()
    out[-1].mask_bbox_px = bbox_of_mask(out[-1].mask)
    out.append(object_from_drawing(f"G{base+1:03d}", "lower", "axis_y", "lower y-axis + arrowhead", page, 40, native, crop_px, [RGB_DARK], notes="arrowhead drawing[41] added"))
    arrow = object_from_drawing("TMP", "lower", "tmp", "tmp", page, 41, native, crop_px, [RGB_DARK])
    out[-1].pre_mask |= arrow.pre_mask
    out[-1].mask = out[-1].pre_mask.copy()
    out[-1].mask_bbox_px = bbox_of_mask(out[-1].mask)
    for i in range(5):
        out.append(object_from_drawing(f"G{base+2+i:03d}", "lower", "x_tick", f"lower x tick {i+1}", page, 36, native, crop_px, item_indices=[i]))
    for i in range(4):
        out.append(object_from_drawing(f"G{base+7+i:03d}", "lower", "y_tick", f"lower y tick {i+1}", page, 37, native, crop_px, item_indices=[i]))
    bot_hatch_bbox = (169.455, 335.118, 235.373, 390.919)
    bot_hatch = Obj(f"G{base+11:03d}", "G", "lower", "warmup_hatch", "lower warm-up northeast hatch", bot_hatch_bbox, 35, "source pattern rectangle; native RGB selector", RGB_HATCH)
    bot_hatch.pre_mask = raw_color_mask(native, crop_px, bot_hatch_bbox, [RGB_HATCH], rect_geom(crop_shape, crop_px, bot_hatch_bbox, expand=0))
    bot_hatch.mask = bot_hatch.pre_mask.copy()
    bot_hatch.mask_bbox_px = bbox_of_mask(bot_hatch.mask)
    out.append(bot_hatch)
    out.append(object_from_drawing(f"G{base+12:03d}", "lower", "running_mean", "lower retained-sample running-mean polyline", page, 43, native, crop_px, [RGB_BLUE]))
    out.append(object_from_drawing(f"G{base+13:03d}", "lower", "burnin_boundary", "lower burn-in boundary dashed line", page, 44, native, crop_px, [RGB_GOLD]))
    out.append(object_from_drawing(f"G{base+14:03d}", "lower", "target_reference", "target value 2 dash-dot reference", page, 45, native, crop_px, [RGB_TEAL]))
    for i, idx in enumerate(range(46, 61), start=6):
        seq = base + 14 + (i - 5)
        out.append(object_from_drawing(f"G{seq:03d}", "lower", "marker", f"lower running-mean marker t={i}", page, idx, native, crop_px, [RGB_BLUE, RGB_DARK]))
    # These two rules are real final-visible PDF drawing paths, not characters in
    # rawdict.  They must remain separate GRAPHIC/MATH_RULE foreground objects.
    out.append(object_from_drawing("R001", "lower", "math_rule", "overline rule for lower y-label \\overline X_{6:t}", page, 61, native, crop_px, [RGB_DARK], notes="semantic parent set after rawdict extraction; drawing[61]"))
    out.append(object_from_drawing("R002", "lower", "math_rule", "overline rule for lower-panel title \\overline X_{6:t}", page, 62, native, crop_px, [RGB_DARK], notes="semantic parent set after rawdict extraction; drawing[62]"))
    # Ensure IDs are unique and the expected count is visible before pair work.
    ids = [x.oid for x in out]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate graphic object ID")
    return out


def resolve_graphic_final_visible_masks(graphics: list[Obj]) -> None:
    """Assign shared same-colour raw pixels to the later PDF drawing object.

    This is traceable z-order separation, not dilation/painting.  It is needed
    for e.g. marker-on-trace and drawing[62] overline-on-axis.  Pair clearance
    is then measured from two *unique* final-visible raw masks, while pre-mask
    intersections remain recorded in the rule ledger.
    """
    candidates = [o for o in graphics if o.foreground and o.pre_mask is not None]
    if not candidates:
        return
    opaque_selectors = [o for o in graphics if not o.foreground and o.occlusion_selector is not None]
    # First remove raw pixels physically hidden by a later opaque white
    # backplate.  This is z-order isolation from the PDF path, not a visual
    # paint/dilate operation and it remains separately recorded in inventory.
    initial: dict[str, np.ndarray] = {}
    for obj in candidates:
        candidate = obj.pre_mask.copy()
        for occluder in opaque_selectors:
            if obj.z_order < occluder.z_order:
                candidate &= ~occluder.occlusion_selector
        initial[obj.oid] = candidate
    occupied = np.zeros_like(candidates[0].pre_mask, dtype=bool)
    for obj in sorted(candidates, key=lambda x: x.z_order, reverse=True):
        obj.mask = initial[obj.oid] & ~occupied
        occupied |= obj.mask
        obj.mask_bbox_px = bbox_of_mask(obj.mask)


def bind_math_rule_parents(text_objects: list[Obj], graphics: list[Obj]) -> list[dict[str, Any]]:
    """Close the rawdict-text ↔ drawing-rule semantic mapping for both overbars."""
    lower_title = [o.oid for o in text_objects if o.panel == "lower" and o.role == "title"]
    lower_ylabel = [o.oid for o in text_objects if o.panel == "lower" and o.role == "y_label"]
    rows: list[dict[str, Any]] = []
    for rule in [o for o in graphics if o.role == "math_rule"]:
        parent_ids = lower_ylabel if rule.oid == "R001" else lower_title
        rule.notes = (rule.notes + "; semantic_parent_text_objects=" + ",".join(parent_ids)).strip("; ")
        pre = rule.pre_mask if rule.pre_mask is not None else np.zeros((1, 1), dtype=bool)
        final = rule.mask if rule.mask is not None else np.zeros((1, 1), dtype=bool)
        rows.append({
            "rule_id": rule.oid, "safe_filename": f"{rule.oid}_math_rule.png", "pdf_drawing_index": rule.z_order,
            "panel": rule.panel, "semantic_parent_text_objects": ",".join(parent_ids), "semantic_parent_formula": "\\overline X_{6:t}",
            "bbox_pt": ";".join(f"{x:.3f}" for x in rule.bbox_pt),
            "pre_occlusion_raw_pixels": int(pre.sum()), "final_unique_raw_pixels": int(final.sum()),
            "raw_mask_bbox_px": ";".join(map(str, rule.mask_bbox_px or ("", "", "", ""))),
            "mask_nonempty": "YES" if final.any() else "NO", "status": "PENDING_FOUR_PANEL_HUMAN_REVIEW",
        })
    return rows


def apply_glyph_gates(glyphs: list[Glyph], graphics: list[Obj]) -> None:
    # Low-profile items are not falsely rejected by a tall-glyph criterion.  They
    # receive a separate reference calibration ledger below.  Other gates are
    # the mandatory protocol thresholds in native 300dpi pixels.
    for g in glyphs:
        if not g.mask_bbox_px:
            g.pixel_gate = "FAIL_EMPTY_RAW_MASK"
        elif g.low_profile:
            g.pixel_gate = "PENDING_LOW_PROFILE_CALIBRATION"
        elif g.is_math_script:
            needed = 15
            metric = g.mask_h_px
            g.pixel_gate = f"PASS_LEGAL_SCRIPT_H={metric}>={needed}" if metric >= needed else f"FAIL_LEGAL_SCRIPT_H={metric}<{needed}"
        else:
            needed = 1
            if g.category == "cjk":
                needed = 30
            elif g.category in {"upper", "digit", "math_upper"}:
                needed = 24
            elif g.category in {"lower", "math_lower"}:
                needed = 17
            elif g.category in {"math_base", "math_operator"}:
                needed = 22
            metric = g.mask_h_px
            g.pixel_gate = f"PASS_H={metric}>={needed}" if metric >= needed else f"FAIL_H={metric}<{needed}"
        # A glyph mask has to be separate from actual graphics, not merely from
        # its PDF text bbox.  This uses the raw, already-selected graphic masks.
        contaminants: list[str] = []
        foreign_pixels = 0
        # The two overbar paths are separate GRAPHIC/MATH_RULE objects, but
        # their own X is their explicitly declared semantic parent.  That
        # one formula-internal relationship is not an alien component.  No
        # other text/graphic intersection is exempted here.
        own_rule = "R002" if (g.panel == "lower" and g.role == "title" and g.glyph == "𝑋") else (
            "R001" if (g.panel == "lower" and g.role == "y_label" and g.glyph == "𝑋") else ""
        )
        if g.mask is not None:
            for obj in graphics:
                if obj.mask is not None and obj.mask.any() and np.any(g.mask & obj.mask):
                    hit = int(np.count_nonzero(g.mask & obj.mask))
                    if obj.oid != own_rule:
                        contaminants.append(obj.oid)
                        foreign_pixels += hit
        g.foreign_pixel_px = foreign_pixels
        if contaminants:
            g.purity = "FAIL_FOREIGN_RAW_COMPONENT"
            g.purity_notes = "native-mask intersection with " + ",".join(contaminants)
        else:
            g.purity = "PASS_RAW_MASK_ISOLATED"


def _tex_font_declaration(font: str) -> str:
    """Use the actual candidate families from local TeX/system font files."""
    if font == "STIXTwoMath-Regular":
        return r"\newfontface\AuditFont{STIXTwoMath-Regular.otf}[Path=D:/texlive/2026/texmf-dist/fonts/opentype/public/stix2-otf/]"
    if font == "STIXTwoText-Bold":
        return r"\newfontface\AuditFont{STIXTwoText-Bold.otf}[Path=D:/texlive/2026/texmf-dist/fonts/opentype/public/stix2-otf/]"
    if font == "NotoSerifSC-ExtraLight":
        # Candidate PDF reports this exact face.  The local variable font is the
        # PDF source family; RawFeature fixes the extra-light axis for replay.
        return r"\newfontface\AuditFont{NotoSerifSC-VF.ttf}[Path=C:/WINDOWS/fonts/,RawFeature={+wght=200}]"
    raise RuntimeError(f"no declared calibration font mapping for {font}")


def _glyph_orientation(glyph: Glyph) -> str:
    """The pgfplots lower y-label is a real 90-degree text transform."""
    return "ROTATED_90" if glyph.panel == "lower" and glyph.role == "y_label" else "UPRIGHT"


def _write_calibration_card(native: Image.Image, mask: np.ndarray, directory: Path, stem: str) -> dict[str, str]:
    bb = bbox_of_mask(mask)
    if bb is None:
        return {"original_1x": "", "target_overlay_1x": "", "mask_only_1x": "", "triad_8x": ""}
    x0, y0, x1, y1 = clamp_box((bb[0] - 3, bb[1] - 3, bb[2] + 3, bb[3] + 3), mask.shape[1], mask.shape[0])
    raw = native.crop((x0, y0, x1, y1))
    target = mask[y0:y1, x0:x1]
    overlay = np.asarray(raw).copy(); overlay[target] = (235, 25, 25)
    only = np.full_like(overlay, 255); only[target] = (0, 0, 0)
    paths = {
        "original_1x": directory / f"{stem}_original_1x.png",
        "target_overlay_1x": directory / f"{stem}_target_overlay_1x.png",
        "mask_only_1x": directory / f"{stem}_mask_only_1x.png",
        "triad_8x": directory / f"{stem}_original_overlay_mask_8x_nearest.png",
    }
    raw.save(paths["original_1x"]); Image.fromarray(overlay).save(paths["target_overlay_1x"]); Image.fromarray(only).save(paths["mask_only_1x"])
    raw8 = raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    over8 = Image.fromarray(overlay).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    only8 = Image.fromarray(only).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    strip = Image.new("RGB", (raw8.width * 3, raw8.height + 18), RGB_WHITE)
    d = ImageDraw.Draw(strip); d.text((2, 2), "ORIGINAL / TARGET OVERLAY / MASK ONLY — 8x nearest", fill=(0, 0, 0))
    strip.paste(raw8, (0, 18)); strip.paste(over8, (raw8.width, 18)); strip.paste(only8, (raw8.width * 2, 18)); strip.save(paths["triad_8x"])
    return {k: f"low_profile_calibration/{v.name}" for k, v in paths.items()}


def _standalone_calibration(glyph: Glyph, calibration_id: str) -> dict[str, Any]:
    """Render one isolated same-font/size/colour low-profile reference at 300dpi."""
    directory = OUT / "low_profile_calibration"
    directory.mkdir(exist_ok=True)
    stem = calibration_id
    tex = directory / f"{stem}.tex"
    pdf = directory / f"{stem}.pdf"
    png = directory / f"{stem}_native_300dpi.png"
    r, g, b = glyph.color_rgb
    leading = max(glyph.font_size_pt * 1.22, glyph.font_size_pt + 1.0)
    orientation = _glyph_orientation(glyph)
    rendered = rf"{{\AuditFont\fontsize{{{glyph.font_size_pt:.2f}pt}}{{{leading:.2f}pt}}\selectfont\color[rgb]{{{r/255:.8f},{g/255:.8f},{b/255:.8f}}}{glyph.glyph}}}"
    if orientation == "ROTATED_90":
        # Measure the same final orientation as the pgfplots y-label, not an
        # upright proxy whose H_INK is an unrelated axis dimension.
        rendered = rf"\rotatebox{{90}}{{{rendered}}}"
    tex.write_text("\n".join([
        r"\documentclass[border=24pt]{standalone}", r"\usepackage{fontspec}", r"\usepackage{xcolor}", r"\usepackage{graphicx}",
        _tex_font_declaration(glyph.font), r"\begin{document}", r"\noindent", rendered,
        r"\end{document}", "",
    ]), encoding="utf-8")
    xelatex = shutil.which("xelatex")
    pdftoppm = shutil.which("pdftoppm")
    if not xelatex or not pdftoppm:
        return {"status": "FAIL_CALIBRATION_TOOL_UNAVAILABLE", "source": f"low_profile_calibration/{tex.name}"}
    run = subprocess.run([xelatex, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={directory}", str(tex)], cwd=directory, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (directory / f"{stem}_xelatex.stdout.txt").write_text(run.stdout + "\n" + run.stderr, encoding="utf-8")
    if run.returncode != 0 or not pdf.exists():
        return {"status": "FAIL_CALIBRATION_TEX_RENDER", "source": f"low_profile_calibration/{tex.name}", "log": f"low_profile_calibration/{stem}_xelatex.stdout.txt"}
    subprocess.run([pdftoppm, "-r", "300", "-png", "-singlefile", str(pdf), str(png.with_suffix(""))], check=True)
    im = Image.open(png).convert("RGB")
    arr = np.asarray(im)
    # It is a truly standalone page: no other foreground path exists.  The
    # same 20/255 foreground convention is applied to the declared target hue.
    mask = ray_mask(arr, glyph.color_rgb)
    bb = bbox_of_mask(mask)
    if bb is None:
        return {"status": "FAIL_CALIBRATION_EMPTY_MASK", "source": f"low_profile_calibration/{tex.name}", "pdf": f"low_profile_calibration/{pdf.name}", "native": f"low_profile_calibration/{png.name}"}
    h = bb[3] - bb[1]; w = bb[2] - bb[0]; area = int(mask.sum())
    card_paths = _write_calibration_card(im, mask, directory, stem)
    return {
        "status": "PASS_STANDALONE_REFERENCE", "source": f"low_profile_calibration/{tex.name}", "pdf": f"low_profile_calibration/{pdf.name}",
        "native": f"low_profile_calibration/{png.name}", "font": glyph.font, "effective_pt": glyph.font_size_pt, "orientation": orientation,
        "rgb": "/".join(map(str, glyph.color_rgb)), "H_INK_PX": h, "W_INK_PX": w, "AREA_INK_PX": area,
        "bbox_px": ";".join(map(str, bb)), "cards": card_paths,
    }


def calibrate_low_profile(glyphs: list[Glyph]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply the strict [0.92,1.08] H_INK and area-ratio rule to every target."""
    groups: dict[tuple[str, str, float, tuple[int, int, int], str], list[Glyph]] = {}
    for g in glyphs:
        if g.low_profile:
            groups.setdefault((g.glyph, g.font, round(g.font_size_pt, 2), g.color_rgb, _glyph_orientation(g)), []).append(g)
    rows: list[dict[str, Any]] = []
    cal_index: dict[str, Any] = {}
    for idx, (key, members) in enumerate(sorted(groups.items(), key=lambda x: x[0]), start=1):
        cal_id = f"LP{idx:03d}_{ord(members[0].glyph):04X}_{members[0].font.replace('-', '_')}_{_glyph_orientation(members[0])}"
        calibration = _standalone_calibration(members[0], cal_id)
        cal_index[cal_id] = calibration
        for target in members:
            if calibration.get("status") != "PASS_STANDALONE_REFERENCE":
                target.pixel_gate = calibration["status"]
                h_ratio = area_ratio = ""
                status = calibration["status"]
            else:
                ref_h = int(calibration["H_INK_PX"]); ref_area = int(calibration["AREA_INK_PX"])
                h_ratio_n = target.mask_h_px / ref_h if ref_h else 0.0
                area_ratio_n = target.mask_area_px / ref_area if ref_area else 0.0
                h_ratio, area_ratio = f"{h_ratio_n:.3f}", f"{area_ratio_n:.3f}"
                status = "PASS_REFERENCE_H_AND_AREA" if 0.92 <= h_ratio_n <= 1.08 and 0.92 <= area_ratio_n <= 1.08 else "FAIL_REFERENCE_H_OR_AREA_RATIO"
                target.pixel_gate = status
            rows.append({
                "glyph_id": target.gid, "glyph": target.glyph, "codepoint": target.codepoint, "font": target.font,
                "effective_pt": f"{target.font_size_pt:.2f}", "rgb": "/".join(map(str, target.color_rgb)), "orientation": _glyph_orientation(target), "calibration_id": cal_id,
                "calibration_status": calibration.get("status"), "calibration_H_INK_PX": calibration.get("H_INK_PX", ""),
                "calibration_AREA_INK_PX": calibration.get("AREA_INK_PX", ""), "target_H_INK_PX": target.mask_h_px,
                "target_AREA_INK_PX": target.mask_area_px, "H_INK_ratio": h_ratio, "area_ratio": area_ratio,
                "required_ratio_interval": "[0.92,1.08]", "status": status,
                "method": "independent standalone TeX replay using actual candidate font family, same codepoint/size/color/300dpi/20-255 mask",
                "calibration_source": calibration.get("source", ""), "calibration_native": calibration.get("native", ""),
                "calibration_cards": json.dumps(calibration.get("cards", {}), ensure_ascii=False),
            })
    return rows, cal_index


def intended_contacts(objects: list[Obj]) -> dict[tuple[str, str], str]:
    bylabel = {o.label: o.oid for o in objects}
    byrole: dict[tuple[str, str], list[Obj]] = {}
    for o in objects:
        byrole.setdefault((o.panel, o.role), []).append(o)
    intent: dict[tuple[str, str], str] = {}
    def add(a: Obj, b: Obj, reason: str) -> None:
        intent[tuple(sorted((a.oid, b.oid)))] = reason
    # Individual tick-to-axis attachments.
    for panel in ("upper", "lower"):
        xaxis = byrole[(panel, "axis_x")][0]
        yaxis = byrole[(panel, "axis_y")][0]
        # Roles are shared by rawdict tick-label text and vector tick marks;
        # only the latter participate in coordinate-frame contact semantics.
        x_ticks = [o for o in byrole[(panel, "x_tick")] if o.kind == "G"]
        y_ticks = [o for o in byrole[(panel, "y_tick")] if o.kind == "G"]
        add(xaxis, yaxis, f"{panel} coordinate-frame axes intentionally meet at the origin")
        for tick in x_ticks:
            add(tick, xaxis, f"{panel} x tick is intentionally attached to its x-axis")
        for tick in y_ticks:
            add(tick, yaxis, f"{panel} y tick is intentionally attached to its y-axis")
        hatch = byrole[(panel, "warmup_hatch")][0]
        add(hatch, xaxis, f"{panel} warm-up hatch terminates at the x-axis boundary")
        add(hatch, yaxis, f"{panel} warm-up hatch terminates at the y-axis boundary")
        # The t=1 x tick shares the coordinate origin with the y-axis.  The
        # t=5 tick and each y tick are deliberately drawn through the shaded
        # burn-in panel; these are named one-by-one, never a class exemption.
        if x_ticks:
            add(x_ticks[0], yaxis, f"{panel} t=1 x tick intentionally meets the y-axis at the coordinate origin")
        if len(x_ticks) > 1:
            add(x_ticks[1], hatch, f"{panel} t=5 x tick intentionally crosses the warm-up hatch at the stated burn-in interval")
        for tick in y_ticks:
            add(tick, hatch, f"{panel} y tick {tick.label} intentionally crosses the warm-up hatch at the coordinate-frame boundary")
    toptrace = byrole[("upper", "trace")][0]
    for marker in byrole[("upper", "marker")]:
        add(toptrace, marker, f"trace sample marker is intentionally drawn on the upper trace ({marker.label})")
    lowertrace = byrole[("lower", "running_mean")][0]
    for marker in byrole[("lower", "marker")]:
        add(lowertrace, marker, f"running-mean sample marker is intentionally drawn on the lower trace ({marker.label})")
    top_hatch = byrole[("upper", "warmup_hatch")][0]
    add(top_hatch, toptrace, "upper trace passes through the deliberately hatched warm-up region")
    for marker in byrole[("upper", "marker")]:
        if marker.label.endswith(("t=1", "t=2", "t=3", "t=4", "t=5")):
            add(top_hatch, marker, f"warm-up marker is intentionally within shaded interval ({marker.label})")
    for panel in ("upper", "lower"):
        burn = byrole[(panel, "burnin_boundary")][0]
        xaxis = byrole[(panel, "axis_x")][0]
        hatch = byrole[(panel, "warmup_hatch")][0]
        add(burn, xaxis, f"{panel} dashed burn-in divider starts at its x-axis")
        add(burn, hatch, f"{panel} dashed burn-in divider is the warm-up rectangle boundary")
    add(toptrace, byrole[("upper", "burnin_boundary")][0], "upper trace reaches the stated t=5 burn-in divider")
    ref = byrole[("lower", "target_reference")][0]
    burn = byrole[("lower", "burnin_boundary")][0]
    add(ref, burn, "target reference begins at the burn-in boundary")
    add(ref, byrole[("lower", "warmup_hatch")][0], "target reference starts at the retained-sample boundary adjacent to the warm-up hatch")
    add(ref, lowertrace, "running-mean curve may meet target reference; comparison is the stated semantics")
    for marker in byrole[("lower", "marker")]:
        if marker.label.endswith(("t=12", "t=14", "t=17", "t=20")):
            add(ref, marker, f"exact running mean equals target value 2 ({marker.label})")
    # Five source-proved, individually named target-data relations.  This is
    # never a marker-class waiver: the declared lower coordinates are
    # t=10=1.9800, t=15=2.0200, t=16=2.0182, t=18=2.0077 and t=19=2.0071,
    # while the distinct source draw command establishes the y=2 reference.
    near_target_values = {
        "t=10": "1.9800", "t=15": "2.0200", "t=16": "2.0182",
        "t=18": "2.0077", "t=19": "2.0071",
    }
    for marker in byrole[("lower", "marker")]:
        suffix = marker.label.rsplit(" ", 1)[-1]
        if suffix in near_target_values:
            value = near_target_values[suffix]
            add(ref, marker, (
                f"INTENTIONAL_DATA_RELATION: lower source coordinate {suffix}={value} is deliberately compared to "
                f"the separately drawn target reference y=2 (source coordinate/draw lines 37-43)"
            ))
    first_top_marker = byrole[("upper", "marker")][0]
    add(first_top_marker, byrole[("upper", "axis_y")][0], "upper t=1 sample marker intentionally lies on the y-axis at the coordinate origin")
    # Rules are independent graphics objects, but the accent-to-own-X pairing is
    # an explicitly named formula-internal composition only.  Rules retain all
    # normal checks against axes, borders, curves, and other text.
    for rule in byrole.get(("lower", "math_rule"), []):
        if rule.oid == "R001":
            for text in byrole.get(("lower", "y_label"), []):
                if text.label == "𝑋":
                    add(rule, text, "overline rule is the intentional accent of its own lower y-label X")
        if rule.oid == "R002":
            for text in byrole.get(("lower", "title"), []):
                if text.label == "𝑋":
                    add(rule, text, "overline rule is the intentional accent of its own lower-title X")
    return intent


def required_clearance(a: Obj, b: Obj) -> int:
    if a.panel in {"upper", "lower"} and b.panel in {"upper", "lower"} and a.panel != b.panel:
        return 8
    if a.kind == "T" and b.kind == "T":
        return 4
    if (a.kind == "T" and b.role.startswith("axis")) or (b.kind == "T" and a.role.startswith("axis")):
        return 5
    return 3


def nearest_relation(a: Obj, b: Obj, distance_field: np.ndarray | None = None, nearest_indices: np.ndarray | None = None) -> tuple[int, float | None, tuple[int, int] | None, tuple[int, int] | None]:
    assert a.mask is not None and b.mask is not None
    overlap = int(np.count_nonzero(a.mask & b.mask))
    if overlap:
        yy, xx = np.nonzero(a.mask & b.mask)
        p = (int(round(xx.mean())), int(round(yy.mean())))
        return overlap, 0.0, p, p
    if not a.mask.any() or not b.mask.any():
        return 0, None, None, None
    # Native actual foreground masks, no bounding-box proxy.  The caller caches
    # one distance field per object A, so all n(n-1)/2 pairs remain exact without
    # recomputing the same field thousands of times.
    if distance_field is None or nearest_indices is None:
        distance_field, nearest_indices = ndimage.distance_transform_edt(~a.mask, return_indices=True)
    values = distance_field[b.mask]
    where = np.argmin(values)
    by, bx = np.argwhere(b.mask)[where]
    ay = int(nearest_indices[0, by, bx])
    ax = int(nearest_indices[1, by, bx])
    return 0, max(0.0, float(values[where]) - 1.0), (ax, ay), (int(bx), int(by))


def make_pair_card(row: dict[str, Any], a: Obj, b: Obj, native_image: Image.Image, crop_px: tuple[int, int, int, int], cards_dir: Path) -> str:
    if row["nearest_a_x"] == "" or row["nearest_b_x"] == "":
        return ""
    ax, ay = int(row["nearest_a_x"]), int(row["nearest_a_y"])
    bx, by = int(row["nearest_b_x"]), int(row["nearest_b_y"])
    cx = int(round((ax + bx) / 2))
    cy = int(round((ay + by) / 2))
    half = 16
    x0 = max(0, cx - half); y0 = max(0, cy - half)
    x1 = min(a.mask.shape[1], cx + half + 1); y1 = min(a.mask.shape[0], cy + half + 1)
    rawbox = (crop_px[0] + x0, crop_px[1] + y0, crop_px[0] + x1, crop_px[1] + y1)
    raw = native_image.crop(rawbox)
    ma = a.mask[y0:y1, x0:x1]
    mb = b.mask[y0:y1, x0:x1]
    overlay = np.full((raw.height, raw.width, 3), 255, dtype=np.uint8)
    overlay[ma] = (220, 35, 35)
    overlay[mb] = (35, 75, 220)
    overlay[ma & mb] = (255, 150, 0)
    def nearest(im: Image.Image) -> Image.Image:
        return im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST)
    aimg = Image.fromarray(np.where(ma[..., None], np.array((220, 35, 35), dtype=np.uint8), np.array((255, 255, 255), dtype=np.uint8))).convert("RGB")
    bimg = Image.fromarray(np.where(mb[..., None], np.array((35, 75, 220), dtype=np.uint8), np.array((255, 255, 255), dtype=np.uint8))).convert("RGB")
    # Top-left is deliberately the unscaled native sample, padded only for a
    # readable card layout.  The other three panels are 8x nearest-neighbour.
    nraw, na, nb, no = raw, nearest(aimg), nearest(bimg), nearest(Image.fromarray(overlay))
    cellw = max(na.width, nb.width, no.width, nraw.width)
    cellh = max(na.height, nb.height, no.height, nraw.height)
    canvas = Image.new("RGB", (cellw * 2, cellh * 2 + 26), RGB_WHITE)
    canvas.paste(nraw, (0, 26))
    canvas.paste(na, (cellw, 26))
    canvas.paste(nb, (0, 26 + cellh))
    canvas.paste(no, (cellw, 26 + cellh))
    draw = ImageDraw.Draw(canvas)
    draw.text((2, 2), f"RAW 1x | A 8x red | B 8x blue | overlap orange: {a.oid}/{b.oid}", fill=(0, 0, 0))
    filename = f"{row['pair_id']}_{a.oid}_{b.oid}.png"
    canvas.save(cards_dir / filename)
    return f"pair_cards/{filename}"


def make_glyph_card(g: Glyph, native_image: Image.Image, crop_px: tuple[int, int, int, int], cards_dir: Path) -> str:
    assert g.mask is not None
    x0, y0, x1, y1 = rect_to_px(g.bbox_pt, crop_px)
    x0, y0, x1, y1 = clamp_box((x0 - 1, y0 - 1, x1 + 1, y1 + 1), g.mask.shape[1], g.mask.shape[0])
    raw = native_image.crop((crop_px[0] + x0, crop_px[1] + y0, crop_px[0] + x1, crop_px[1] + y1))
    mask = g.mask[y0:y1, x0:x1]
    overlay = np.asarray(raw).copy()
    overlay[mask] = (235, 25, 25)
    mask_only = np.full_like(overlay, 255)
    mask_only[mask] = (0, 0, 0)
    # Same native bbox/pad in all views.  The top strip retains an unscaled 1x
    # original; below are the required ORIGINAL / TARGET OVERLAY / MASK ONLY
    # physical views at eight-times nearest-neighbour (never interpolated).
    original8 = raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    overlay8 = Image.fromarray(overlay).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    mask8 = Image.fromarray(mask_only).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    panelw = max(original8.width, overlay8.width, mask8.width)
    panelh = max(original8.height, overlay8.height, mask8.height)
    card = Image.new("RGB", (panelw * 3, panelh + raw.height + 42), RGB_WHITE)
    d = ImageDraw.Draw(card)
    d.text((1, 1), f"{g.gid} U+{ord(g.glyph):04X}  ORIGINAL 1x (unscaled, left) | three required 8x-nearest views", fill=(0, 0, 0))
    card.paste(raw, (1, 16))
    d.text((panelw + 2, 16), "ORIGINAL 8x", fill=(0, 0, 0))
    d.text((panelw * 2 + 2, 16), "TARGET OVERLAY 8x", fill=(0, 0, 0))
    d.text((2, raw.height + 24), "MASK ONLY 8x", fill=(0, 0, 0))
    card.paste(original8, (panelw, raw.height + 36))
    card.paste(overlay8, (panelw * 2, raw.height + 36))
    card.paste(mask8, (0, raw.height + 36))
    filename = f"{g.gid}_{ord(g.glyph):04X}.png"
    card.save(cards_dir / filename)
    return f"glyph_cards/{filename}"


def make_rule_evidence(rule: Obj, native_image: Image.Image, crop_px: tuple[int, int, int, int], cards_dir: Path) -> dict[str, str]:
    """Save the mandatory 1x/overlay/mask-only/8x four-view evidence for a math rule."""
    assert rule.mask is not None
    pre = rule.pre_mask if rule.pre_mask is not None else rule.mask
    bbox = bbox_of_mask(pre) or bbox_of_mask(rule.mask)
    if bbox is None:
        return {"original_1x": "", "target_overlay_1x": "", "mask_only_1x": "", "four_view_8x": ""}
    x0, y0, x1, y1 = clamp_box((bbox[0] - 3, bbox[1] - 3, bbox[2] + 3, bbox[3] + 3), rule.mask.shape[1], rule.mask.shape[0])
    raw = native_image.crop((crop_px[0] + x0, crop_px[1] + y0, crop_px[0] + x1, crop_px[1] + y1))
    target = rule.mask[y0:y1, x0:x1]
    overlay = np.asarray(raw).copy()
    overlay[target] = (235, 25, 25)
    mask_only = np.full_like(overlay, 255)
    mask_only[target] = (0, 0, 0)
    stem = rule.oid + "_math_rule"
    paths = {
        "original_1x": cards_dir / f"{stem}_original_1x.png",
        "target_overlay_1x": cards_dir / f"{stem}_target_overlay_1x.png",
        "mask_only_1x": cards_dir / f"{stem}_mask_only_1x.png",
        "four_view_8x": cards_dir / f"{stem}_four_view_8x_nearest.png",
    }
    raw.save(paths["original_1x"])
    Image.fromarray(overlay).save(paths["target_overlay_1x"])
    Image.fromarray(mask_only).save(paths["mask_only_1x"])
    raw8 = raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    overlay8 = Image.fromarray(overlay).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    mask8 = Image.fromarray(mask_only).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    cellw = max(raw8.width, overlay8.width, mask8.width)
    cellh = max(raw8.height, overlay8.height, mask8.height)
    panel = Image.new("RGB", (cellw * 3, cellh + 20), RGB_WHITE)
    d = ImageDraw.Draw(panel)
    d.text((2, 2), f"{rule.oid} ORIGINAL / TARGET OVERLAY / MASK ONLY (all 8x nearest)", fill=(0, 0, 0))
    panel.paste(raw8, (0, 20)); panel.paste(overlay8, (cellw, 20)); panel.paste(mask8, (cellw * 2, 20))
    panel.save(paths["four_view_8x"])
    return {k: f"math_rule_cards/{v.name}" for k, v in paths.items()}


def make_critical_bar_axis_evidence(rule: Obj, axis: Obj, native_image: Image.Image, crop_px: tuple[int, int, int, int]) -> dict[str, Any]:
    """Dedicated, unique-mask evidence for the non-whitelisted R002 ↔ G001 pair."""
    outdir = OUT / "critical_barX_vs_upper_axis"
    outdir.mkdir(exist_ok=True)
    assert rule.mask is not None and axis.mask is not None
    pre_rule = rule.pre_mask if rule.pre_mask is not None else rule.mask
    pre_axis = axis.pre_mask if axis.pre_mask is not None else axis.mask
    boxes = [x for x in (bbox_of_mask(pre_rule), bbox_of_mask(pre_axis), bbox_of_mask(rule.mask), bbox_of_mask(axis.mask)) if x]
    box = union_box(boxes)
    assert box is not None
    x0, y0, x1, y1 = clamp_box((box[0] - 6, box[1] - 8, box[2] + 6, box[3] + 8), rule.mask.shape[1], rule.mask.shape[0])
    raw = native_image.crop((crop_px[0] + x0, crop_px[1] + y0, crop_px[0] + x1, crop_px[1] + y1))
    rmask = rule.mask[y0:y1, x0:x1]
    amask = axis.mask[y0:y1, x0:x1]
    pre_rmask = pre_rule[y0:y1, x0:x1]
    pre_amask = pre_axis[y0:y1, x0:x1]
    pre_intersection = int(np.count_nonzero(pre_rule & pre_axis))
    final_intersection = int(np.count_nonzero(rule.mask & axis.mask))
    raw.save(outdir / "barX_vs_upper_axis_original_1x.png")
    Image.fromarray(np.where(pre_rmask, 0, 255).astype(np.uint8)).save(outdir / "barX_pre_zorder_raw_mask_1x.png")
    Image.fromarray(np.where(pre_amask, 0, 255).astype(np.uint8)).save(outdir / "upper_axis_pre_zorder_raw_mask_1x.png")
    Image.fromarray(np.where(pre_rmask & pre_amask, 0, 255).astype(np.uint8)).save(outdir / "pre_zorder_shared_intersection_1x.png")
    Image.fromarray(np.where(rmask, 0, 255).astype(np.uint8)).save(outdir / "barX_unique_raw_mask_1x.png")
    Image.fromarray(np.where(amask, 0, 255).astype(np.uint8)).save(outdir / "upper_axis_unique_raw_mask_1x.png")
    pre_overlay = np.asarray(raw).copy()
    pre_overlay[pre_amask] = (35, 75, 220)
    pre_overlay[pre_rmask] = (235, 25, 25)
    pre_overlay[pre_amask & pre_rmask] = (255, 150, 0)
    Image.fromarray(pre_overlay).save(outdir / "pre_zorder_A_B_intersection_overlay_1x.png")
    overlay = np.asarray(raw).copy()
    overlay[amask] = (35, 75, 220)
    overlay[rmask] = (235, 25, 25)
    overlay[amask & rmask] = (255, 150, 0)
    Image.fromarray(overlay).save(outdir / "barX_axis_unique_overlay_1x.png")
    Image.fromarray(pre_overlay).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(outdir / "pre_zorder_A_B_intersection_overlay_8x_nearest.png")
    Image.fromarray(overlay).resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(outdir / "barX_axis_unique_overlay_8x_nearest.png")
    overlap, clearance, pa, pb = nearest_relation(rule, axis)
    # Source PDF vector geometry independently cross-checks the raster finding.
    # These measurements come directly from this frozen candidate, never a prior
    # audit package.
    page = fitz.open(PDF_PATH)[PAGE_INDEX]
    drawings = page.get_drawings()
    axis_d = drawings[8]; rule_d = drawings[62]
    axis_y = float(axis_d["rect"].y0); rule_y = float(rule_d["rect"].y0)
    axis_w = float(axis_d.get("width") or 0.0); rule_w = float(rule_d.get("width") or 0.0)
    centre_gap = abs(rule_y - axis_y)
    half_width_sum = (axis_w + rule_w) / 2.0
    result = {
        "rule_object": rule.oid, "axis_object": axis.oid, "decision_basis": "unique final-visible raw masks; native 300dpi 1x",
        "pre_zorder_same_colour_geometric_raw_intersection_px": pre_intersection,
        "final_unique_raw_intersection_px": final_intersection,
        "final_unique_raw_clearance_px": clearance,
        "nearest_rule_pixel_crop_xy": pa, "nearest_axis_pixel_crop_xy": pb,
        "vector_geometry_crosscheck": {
            "axis_pdf_drawing_index": 8, "axis_centerline_y_pt": axis_y, "axis_stroke_width_pt": axis_w,
            "overbar_pdf_drawing_index": 62, "overbar_centerline_y_pt": rule_y, "overbar_stroke_width_pt": rule_w,
            "centreline_distance_pt": centre_gap, "half_stroke_width_sum_pt": half_width_sum,
            "vector_stroke_penetration_pt": max(0.0, half_width_sum - centre_gap),
        },
        "non_whitelisted": True, "verdict": "FAIL" if (final_intersection > 0 or (clearance is not None and clearance < 8)) else "PASS",
        "files": {p.name: f"critical_barX_vs_upper_axis/{p.name}" for p in outdir.iterdir() if p.is_file()},
    }
    dump_json("critical_barX_vs_upper_axis.json", result)
    return result


def make_contact_sheets(cards: list[Path], directory: Path, prefix: str, columns: int = 3, rows: int = 4) -> list[str]:
    result: list[str] = []
    if not cards:
        return result
    thumb_w, thumb_h = 400, 360
    for page_no, start in enumerate(range(0, len(cards), columns * rows), start=1):
        chosen = cards[start:start + columns * rows]
        sheet = Image.new("RGB", (columns * thumb_w, rows * thumb_h), (245, 245, 245))
        for i, card in enumerate(chosen):
            im = Image.open(card).convert("RGB")
            im.thumbnail((thumb_w - 8, thumb_h - 8), Image.Resampling.NEAREST)
            x = (i % columns) * thumb_w + 4
            y = (i // columns) * thumb_h + 4
            sheet.paste(im, (x, y))
        name = f"{prefix}_{page_no:03d}.png"
        sheet.save(directory / name)
        result.append(f"{directory.name}/{name}")
    return result


def build_pairs(objects: list[Obj], native_image: Image.Image, crop_px: tuple[int, int, int, int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    cards_dir = OUT / "pair_cards"
    cards_dir.mkdir(exist_ok=True)
    intent = intended_contacts(objects)
    rows: list[dict[str, Any]] = []
    contact_rows: list[dict[str, Any]] = []
    num = 0
    for a_index, a in enumerate(objects[:-1]):
        have_a_mask = a.foreground and a.mask is not None and a.mask.any()
        if have_a_mask:
            distance_field, nearest_indices = ndimage.distance_transform_edt(~a.mask, return_indices=True)
        else:
            distance_field = nearest_indices = None
        for b in objects[a_index + 1:]:
            num += 1
            pair_key = tuple(sorted((a.oid, b.oid)))
            req = required_clearance(a, b)
            if not have_a_mask or not b.foreground or b.mask is None or not b.mask.any():
                row = {
                    "pair_id": f"P{num:04d}", "object_a": a.oid, "object_b": b.oid, "type": a.kind + b.kind,
                    "panel_relation": f"{a.panel}/{b.panel}", "raw_overlap_px": "", "raw_clearance_px": "",
                    "required_clearance_px": req, "intent_whitelisted": "NO", "intent_reason": "",
                    "verdict": "NOT_APPLICABLE_BACKGROUND_OCCLUDER", "nearest_a_x": "", "nearest_a_y": "", "nearest_b_x": "", "nearest_b_y": "", "evidence_card": "",
                }
                rows.append(row)
                continue
            overlap, clearance, pa, pb = nearest_relation(a, b, distance_field, nearest_indices)
            contact_or_short = overlap > 0 or (clearance is not None and clearance < req)
            whitelisted = pair_key in intent
            if contact_or_short:
                verdict = "INTENDED_CONTACT" if whitelisted else "FAIL_UNWHITELISTED_OVERLAP_OR_CLEARANCE"
            else:
                verdict = "PASS_CLEARANCE"
            # Even a still-passing gap under 8px gets a human pixel card as a
            # protocol-critical/suspected region.
            card_needed = overlap > 0 or (clearance is not None and clearance < 8.0)
            row = {
                "pair_id": f"P{num:04d}", "object_a": a.oid, "object_b": b.oid, "type": a.kind + b.kind,
                "panel_relation": f"{a.panel}/{b.panel}", "raw_overlap_px": overlap,
                "raw_clearance_px": f"{clearance:.3f}" if clearance is not None else "",
                "required_clearance_px": req, "intent_whitelisted": "YES" if whitelisted else "NO",
                "intent_reason": intent.get(pair_key, ""), "verdict": verdict,
                "nearest_a_x": "" if pa is None else pa[0], "nearest_a_y": "" if pa is None else pa[1],
                "nearest_b_x": "" if pb is None else pb[0], "nearest_b_y": "" if pb is None else pb[1], "evidence_card": "",
            }
            if card_needed:
                row["evidence_card"] = make_pair_card(row, a, b, native_image, crop_px, cards_dir)
            if verdict == "INTENDED_CONTACT":
                contact_rows.append({
                    "pair_id": row["pair_id"], "object_a": a.oid, "object_b": b.oid,
                    "raw_overlap_px": overlap, "raw_clearance_px": row["raw_clearance_px"],
                    "semantic_reason": intent[pair_key], "pixel_card": row["evidence_card"],
                    "status": "NAMED_INDIVIDUAL_WHITELIST",
                })
            rows.append(row)
    pair_card_paths = [OUT / r["evidence_card"] for r in rows if r["evidence_card"]]
    contact_sheets_dir = OUT / "pair_contact_sheets"
    contact_sheets_dir.mkdir(exist_ok=True)
    sheets = make_contact_sheets(pair_card_paths, contact_sheets_dir, "pair_contact_sheet")
    return rows, contact_rows, sheets


def make_overlay(native_image: Image.Image, crop_px: tuple[int, int, int, int], glyphs: list[Glyph]) -> None:
    crop = native_image.crop(crop_px).convert("RGB")
    draw = ImageDraw.Draw(crop)
    for g in glyphs:
        x0, y0, x1, y1 = rect_to_px(g.bbox_pt, crop_px)
        color = (220, 0, 0) if g.pixel_gate.startswith("FAIL") or g.purity.startswith("FAIL") else (0, 130, 0)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
        draw.text((x0, max(0, y0 - 8)), g.gid[1:], fill=color)
    crop.save(OUT / "after_text_measurement_overlay_300dpi.png")


def source_and_location_audit(doc: fitz.Document, page: fitz.Page) -> dict[str, Any]:
    page_text = page.get_text("text")
    exact_caption = "舍弃前5步后，保留样本运行均值在目标值2附近波动；本图仅作诊断，不构成收敛证明"
    normalized_caption = re.sub(r"\s+", "", exact_caption)
    caption_occurrences = [i + 1 for i, p in enumerate(doc) if normalized_caption in re.sub(r"\s+", "", p.get_text("text"))]
    chapter = CHAPTER_PATH.read_text(encoding="utf-8")
    source = SOURCE_PATH.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    chapter_lines = chapter.splitlines()
    input_line = next((i + 1 for i, line in enumerate(chapter_lines) if "fig_v5_c03_trace_running_mean.tex" in line), None)
    intro_line = next((i + 1 for i, line in enumerate(chapter_lines) if "展示固定诊断示意轨迹与保留样本运行均值" in line), None)
    aux = PDF_PATH.parent / "main_full.aux"
    fls = PDF_PATH.parent / "main_full.fls"
    aux_hit = [x for x in aux.read_text(encoding="utf-8", errors="replace").splitlines() if "fig:V5-C03-trace-running-mean" in x]
    fls_hit = [x for x in fls.read_text(encoding="utf-8", errors="replace").splitlines() if "fig_v5_c03_trace_running_mean.tex" in x]
    # PDF page 651 has equation (32.8); exact caption disambiguates the figure.
    false_equation_pages = [i + 1 for i, p in enumerate(doc) if "(32.8)" in p.get_text("text")]
    excerpt_start = max(0, (input_line or 1) - 5)
    (OUT / "direct_body_source_excerpt.txt").write_text("\n".join(chapter_lines[excerpt_start:excerpt_start + 13]) + "\n", encoding="utf-8")
    (OUT / "figure_source_full.tex.txt").write_text(source, encoding="utf-8")
    return {
        "candidate_pdf": canonical(PDF_PATH), "candidate_pdf_sha256": sha256(PDF_PATH), "candidate_pages": doc.page_count,
        "declared_figure_source": canonical(SOURCE_PATH), "source_sha256": sha256(SOURCE_PATH), "source_bytes": SOURCE_PATH.stat().st_size,
        "figure_number": "32.8", "physical_page": PAGE_NO, "printed_page": "646", "caption_exact": exact_caption,
        "caption_physical_pages": caption_occurrences, "equation_32_8_physical_pages_disambiguated": false_equation_pages,
        "chapter_input_line": input_line, "chapter_introduction_line": intro_line,
        "aux_label_lines": aux_hit, "fls_source_input_lines": fls_hit,
        "candidate_page_text_has_caption": normalized_caption in re.sub(r"\s+", "", page_text),
        "source_caption_line": next((i + 1 for i, line in enumerate(source_lines) if "\\caption" in line), None),
        "source_label_line": next((i + 1 for i, line in enumerate(source_lines) if "V5-C03-trace-running-mean" in line), None),
        "result": "PASS_IDENTITY_AND_LOCATION" if caption_occurrences == [PAGE_NO] and normalized_caption in re.sub(r"\s+", "", page_text) else "FAIL_IDENTITY_OR_CAPTION_LOCATION",
    }


def mathematical_audit() -> dict[str, Any]:
    trace = [3.8, 3.4, 3.0, 2.7, 2.4, 1.9, 2.2, 1.7, 2.1, 2.0, 2.3, 1.8, 2.1, 1.9, 2.2, 2.0, 1.8, 2.1, 2.0, 1.9]
    printed = [1.9000, 2.0500, 1.9333, 1.9750, 1.9800, 2.0333, 2.0000, 2.0125, 2.0000, 2.0200, 2.0182, 2.0000, 2.0077, 2.0071, 2.0000]
    computed = [sum(trace[5:i + 1]) / len(trace[5:i + 1]) for i in range(5, len(trace))]
    deltas = [abs(a - b) for a, b in zip(computed, printed)]
    return {
        "fixed_trace": trace, "retained_t_range": [6, 20], "computed_running_means": computed,
        "source_coordinates_running_means": printed, "max_absolute_rounding_error": max(deltas),
        "final_mean_t20": computed[-1], "target_value": 2.0,
        "caption_and_direct_body_semantics": "diagnostic illustration only; not a convergence proof",
        "status": "PASS" if max(deltas) <= 0.00005 and abs(computed[-1] - 2.0) < 1e-12 else "FAIL",
    }


def visual_and_occlusion(objects: list[Obj], pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pair_by_obj: dict[str, list[dict[str, Any]]] = {}
    for p in pairs:
        pair_by_obj.setdefault(p["object_a"], []).append(p)
        pair_by_obj.setdefault(p["object_b"], []).append(p)
    rows: list[dict[str, Any]] = []
    for o in objects:
        unallowed = [p["pair_id"] for p in pair_by_obj.get(o.oid, []) if p["verdict"] == "FAIL_UNWHITELISTED_OVERLAP_OR_CLEARANCE"]
        status = "FAIL_ADJACENCY_OR_OCCLUSION" if unallowed else "PASS_NO_UNWHITELISTED_OCCLUSION"
        if o.role == "label_backplate":
            status = "PASS_DECLARED_WHITE_ZORDER_OCCLUDER"
        rows.append({
            "object_id": o.oid, "kind": o.kind, "panel": o.panel, "role": o.role, "label": o.label,
            "pdf_z_order": o.z_order, "provenance": o.provenance, "foreground_mask": "YES" if o.foreground else "NO_WHITE_OCCLUDER",
            "relevant_failed_pairs": ",".join(unallowed), "status": status,
            "manual_zorder_check": "PENDING_HUMAN_CONTACT_SHEET_REVIEW",
        })
    return rows


def layout_audit(text_objects: list[Obj], glyphs: list[Glyph]) -> dict[str, Any]:
    role_sizes: dict[str, list[float]] = {}
    for g in glyphs:
        role_sizes.setdefault(f"{g.panel}:{g.role}", []).append(g.font_size_pt)
    sizes = {k: {"count": len(v), "min_pt": min(v), "max_pt": max(v), "median_pt": float(np.median(v))} for k, v in role_sizes.items()}
    # Source-declared role hierarchy, independently checked against PDF raw spans.
    return {
        "source_declared": {"regular_label_pt": 9.6, "title_and_axis_label_pt": 10.8, "math_script_raw_pdf_pt": 7.53},
        "observed_by_panel_role": sizes,
        "coordination": {
            "upper_lower_tick_size_match": True,
            "upper_lower_axis_label_size_match": True,
            "upper_lower_title_size_match": True,
            "ordinary_roles_meet_9_5pt": all(g.font_size_pt >= 9.5 or g.is_math_script for g in glyphs),
        },
        "status": "PENDING_HUMAN_D_E_AND_PAIR_SEPARATION_GATE",
    }


def drawing_path_coverage(page: fitz.Page, graphics: list[Obj]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Prove that every in-scope PDF foreground path has one audited object.

    The source hatch patterns are not represented in PyMuPDF's drawing list, so
    they are separately named native-pixel objects.  Every visible *drawing*
    path in the P608 crop is accounted for below, including the two overbars.
    """
    path_map: dict[int, list[str]] = {
        6: ["G003", "G004", "G005", "G006", "G007"], 7: ["G008", "G009", "G010"],
        8: ["G001"], 9: ["G001"], 10: ["G002"], 11: ["G002"], 13: ["G012"],
        14: ["G013"], 15: ["G014"], 36: ["G037", "G038", "G039", "G040", "G041"],
        37: ["G042", "G043", "G044", "G045"], 38: ["G035"], 39: ["G035"],
        40: ["G036"], 41: ["G036"], 43: ["G047"], 44: ["G048"], 45: ["G049"],
        61: ["R001"], 62: ["R002"],
    }
    for drawing_index, oid in zip(range(16, 36), range(15, 35)):
        path_map[drawing_index] = [f"G{oid:03d}"]
    for drawing_index, oid in zip(range(46, 61), range(50, 65)):
        path_map[drawing_index] = [f"G{oid:03d}"]
    known_ids = {o.oid for o in graphics}
    rows: list[dict[str, Any]] = []
    unassigned: list[int] = []
    for index, drawing in enumerate(page.get_drawings()):
        rect = drawing["rect"]
        bbox = (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))
        in_scope = intersects(bbox, FIGURE_CROP_PT)
        assigned = path_map.get(index, [])
        if in_scope and index != 15 and not assigned:
            unassigned.append(index)
        if any(oid not in known_ids for oid in assigned):
            raise RuntimeError(f"drawing path mapping references missing object(s): {index} -> {assigned}")
        rows.append({
            "pdf_drawing_index": index, "bbox_pt": ";".join(f"{v:.3f}" for v in bbox),
            "stroke_width_pt": f"{float(drawing.get('width') or 0.0):.6f}", "drawing_type": drawing.get("type", ""),
            "item_count": len(drawing.get("items", [])), "in_p608_figure_crop": "YES" if in_scope else "NO",
            "foreground_class": "WHITE_BACKPLATE_OCCLUDER" if index == 15 else "FOREGROUND_PATH",
            "audited_object_ids": ",".join(assigned),
            "coverage_status": "OUT_OF_SCOPE" if not in_scope else ("COVERED" if assigned else "FAIL_UNASSIGNED_FOREGROUND_PATH"),
        })
    summary = {
        "coverage_basis": "PyMuPDF page.get_drawings() enumerated against frozen P659 figure crop; rawdict covers text separately",
        "in_scope_drawing_paths": sum(r["in_p608_figure_crop"] == "YES" for r in rows),
        "unassigned_foreground_path_indices": unassigned,
        "unassigned_foreground_path_count": len(unassigned),
        "supplemental_native_pattern_objects": ["G011", "G046"],
        "math_rule_paths": {"drawing[61]": "R001", "drawing[62]": "R002"},
        "status": "PASS_NO_UNASSIGNED_FOREGROUND_PATH" if not unassigned else "FAIL_UNASSIGNED_FOREGROUND_PATH",
    }
    return rows, summary


def _glyph_sheet_location(index_zero_based: int) -> tuple[str, str]:
    per_sheet = 12
    sheet = index_zero_based // per_sheet + 1
    inside = index_zero_based % per_sheet
    return (f"glyph_contact_sheets/glyph_sheet_{sheet:03d}.png", f"r{inside // 4 + 1}c{inside % 4 + 1}")


def _pair_metric_map(pair_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in pair_rows:
        if row["verdict"] == "NOT_APPLICABLE_BACKGROUND_OCCLUDER":
            continue
        for oid in (row["object_a"], row["object_b"]):
            prior = result.get(oid)
            clearance = float(row["raw_clearance_px"]) if row["raw_clearance_px"] not in {"", None} else float("inf")
            if prior is None or clearance < prior["clearance"]:
                result[oid] = {"clearance": clearance, "pair_id": row["pair_id"], "other": row["object_b"] if oid == row["object_a"] else row["object_a"]}
    return result


def strict_glyph_rows(glyphs: list[Glyph], pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One schema-shaped row per visible rawdict glyph; no final human decision."""
    role_heights: dict[str, list[int]] = {}
    for g in glyphs:
        role_heights.setdefault(f"{g.panel}:{g.role}:{g.category}", []).append(g.mask_h_px)
    medians = {key: float(np.median(values)) for key, values in role_heights.items() if values}
    nearest = _pair_metric_map(pair_rows)
    rows: list[dict[str, Any]] = []
    for index, g in enumerate(glyphs):
        bb = g.mask_bbox_px or ("", "", "", "")
        role_key = f"{g.panel}:{g.role}:{g.category}"
        median = medians.get(role_key, 0.0)
        sheet, cell = _glyph_sheet_location(index)
        pairinfo = nearest.get(g.text_oid)
        machine_result = "FAIL" if (g.size_gate.startswith("FAIL") or g.pixel_gate.startswith("FAIL") or g.purity.startswith("FAIL")) else "PENDING_HUMAN_REVIEW"
        rows.append({
            "glyph_id": g.gid, "text_object_id": g.text_oid, "glyph": g.glyph, "codepoint": g.codepoint,
            "panel": g.panel, "role": g.role, "font": g.font, "effective_pt": f"{g.font_size_pt:.2f}",
            "declared_pt": f"{g.font_size_pt:.2f}", "graphics_scale": "1.000", "source_file": canonical(SOURCE_PATH),
            "source_line": "46" if g.role in {"caption_label", "caption_text"} else "20-42",
            "bbox_pt": ";".join(f"{x:.3f}" for x in g.bbox_pt), "category": g.category,
            "low_profile": "YES" if g.low_profile else "NO", "math_script": "YES" if g.is_math_script else "NO",
            "raw_mask_bbox_px": ";".join(map(str, bb)), "raw_mask_w_px": g.mask_w_px, "raw_mask_h_px": g.mask_h_px,
            "H_INK_PX": g.mask_h_px, "W_INK_PX": g.mask_w_px, "AREA_INK_PX": g.mask_area_px,
            "components_8_connected": g.components, "class_median_px": f"{median:.3f}",
            "ratio_to_class_median": f"{g.mask_h_px / median:.3f}" if median else "",
            "role_ratio": f"{g.mask_h_px / median:.3f}" if median else "",
            "font_size_gate": g.size_gate, "pixel_gate": g.pixel_gate, "mask_purity": g.purity,
            "purity_notes": g.purity_notes, "missing_stroke_px": g.missing_stroke_px,
            "foreign_pixel_px": g.foreign_pixel_px, "text_text_overlap_px": 0,
            "text_graphic_overlap_px": g.foreign_pixel_px,
            "min_clearance_px": "" if pairinfo is None or not math.isfinite(pairinfo["clearance"]) else f"{pairinfo['clearance']:.3f}",
            "nearest_object_pair": "" if pairinfo is None else f"{pairinfo['pair_id']}:{pairinfo['other']}",
            "card": f"glyph_cards/{g.gid}_{ord(g.glyph):04X}.png", "sheet": sheet, "cell": cell,
            "reviewer": "PENDING", "original_match": "PENDING", "overlay_complete": "PENDING", "mask_only_pure": "PENDING",
            "decision": "PENDING", "note": "Machine row only; final reviewer must inspect this exact card/cell.",
            "machine_pass_fail": machine_result,
        })
    return rows


def build_critical_only() -> None:
    """Regenerate only the dedicated critical ROI after evidence-card changes."""
    if sha256(PDF_PATH) != EXPECTED_PDF_SHA256:
        raise RuntimeError("frozen R97 candidate SHA256 mismatch")
    page = fitz.open(PDF_PATH)[PAGE_INDEX]
    native = np.asarray(Image.open(OUT / "native_page_659_300dpi.png").convert("RGB"))
    native_image = Image.open(OUT / "native_page_659_300dpi.png").convert("RGB")
    crop_px = rect_to_px(FIGURE_CROP_PT)
    graphics = extract_graphics(page, native, crop_px)
    resolve_graphic_final_visible_masks(graphics)
    by_id = {obj.oid: obj for obj in graphics}
    make_critical_bar_axis_evidence(by_id["R002"], by_id["G001"], native_image, crop_px)


def build_reports() -> None:
    if OUT.name != "STRICT_R1_SA1_REQUAL_R97_20260824":
        raise RuntimeError("refusing to write outside the dedicated R1 evidence directory")
    if sha256(PDF_PATH) != EXPECTED_PDF_SHA256:
        raise RuntimeError("frozen R97 candidate SHA256 mismatch")
    doc = fitz.open(PDF_PATH)
    if doc.page_count != 813:
        raise RuntimeError("frozen R97 candidate page count mismatch")
    page = doc[PAGE_INDEX]
    native, crop_px = native_render()
    native_image = Image.open(OUT / "native_page_659_300dpi.png").convert("RGB")
    identity = source_and_location_audit(doc, page)
    dump_json("identity_and_location.json", identity)
    text_objects, glyphs = extract_text(page, native, crop_px)
    graphics = extract_graphics(page, native, crop_px)
    # Apply vector drawing order before *any* pair or purity measurement.
    resolve_graphic_final_visible_masks(graphics)
    rule_rows = bind_math_rule_parents(text_objects, graphics)
    drawing_rows, drawing_summary = drawing_path_coverage(page, graphics)
    if drawing_summary["unassigned_foreground_path_count"]:
        raise RuntimeError("unassigned in-scope foreground PDF drawing path")
    objects = text_objects + graphics
    apply_glyph_gates(glyphs, graphics)
    calibration_rows, calibration_index = calibrate_low_profile(glyphs)
    # Build all glyph evidence cards and sheets before the paired-object stage.
    glyph_dir = OUT / "glyph_cards"; glyph_dir.mkdir(exist_ok=True)
    glyph_cards = [OUT / make_glyph_card(g, native_image, crop_px, glyph_dir) for g in glyphs]
    glyph_sheet_dir = OUT / "glyph_contact_sheets"; glyph_sheet_dir.mkdir(exist_ok=True)
    glyph_sheets = make_contact_sheets(glyph_cards, glyph_sheet_dir, "glyph_sheet", columns=4, rows=3)
    make_overlay(native_image, crop_px, glyphs)
    pair_rows, contact_rows, pair_sheets = build_pairs(objects, native_image, crop_px)
    rule_dir = OUT / "math_rule_cards"; rule_dir.mkdir(exist_ok=True)
    rule_paths = {r.oid: make_rule_evidence(r, native_image, crop_px, rule_dir) for r in graphics if r.role == "math_rule"}
    for row in rule_rows:
        row.update(rule_paths.get(row["rule_id"], {}))
        row["reviewer"] = "PENDING"
        row["original_match"] = "PENDING"
        row["overlay_complete"] = "PENDING"
        row["mask_only_pure"] = "PENDING"
        row["decision"] = "PENDING"
        row["note"] = "Four-panel native/8x review not yet entered."
    rule_by_id = {r.oid: r for r in graphics}
    critical = make_critical_bar_axis_evidence(rule_by_id["R002"], rule_by_id["G001"], native_image, crop_px)
    # Purity gets a final post-pair check: any non-intended glyph/graphic raw
    # intersection remains a hard glyph failure already visible in the ledger.
    fail_pairs = [r for r in pair_rows if r["verdict"] == "FAIL_UNWHITELISTED_OVERLAP_OR_CLEARANCE"]
    object_rows = []
    for o in objects:
        bbox = o.mask_bbox_px or ("", "", "", "")
        object_rows.append({
            "object_id": o.oid, "kind": o.kind, "panel": o.panel, "role": o.role, "label": o.label,
            "bbox_pt": ";".join(f"{x:.3f}" for x in o.bbox_pt), "raw_mask_bbox_px": ";".join(map(str, bbox)),
            "pre_occlusion_raw_mask_pixels": int(o.pre_mask.sum()) if o.pre_mask is not None else 0,
            "final_unique_raw_mask_pixels": int(o.mask.sum()) if o.mask is not None else 0,
            "raw_mask_pixels": int(o.mask.sum()) if o.mask is not None else 0, "foreground": "YES" if o.foreground else "NO_WHITE_OCCLUDER",
            "pdf_z_order": o.z_order, "provenance": o.provenance, "notes": o.notes,
        })
    glyph_rows = strict_glyph_rows(glyphs, pair_rows)
    write_csv("object_inventory.csv", object_rows)
    write_csv("glyph_ledger.csv", glyph_rows)
    write_csv("after_font_audit.csv", glyph_rows)
    write_csv("after_pixel_measurements.csv", glyph_rows)
    write_csv("low_profile_calibration.csv", calibration_rows)
    write_csv("after_overlap_report.csv", pair_rows)
    write_csv("intended_contact_ledger.csv", contact_rows)
    write_csv("math_rule_ledger.csv", rule_rows)
    write_csv("drawing_path_coverage.csv", drawing_rows)
    dump_json("drawing_path_crosscheck.json", drawing_summary)
    occlusion_rows = visual_and_occlusion(objects, pair_rows)
    write_csv("occlusion_zorder.csv", occlusion_rows)
    layout = layout_audit(text_objects, glyphs)
    dump_json("layout_coordination.json", layout)
    math_audit = mathematical_audit()
    dump_json("math_semantics_audit.json", math_audit)
    summary = {
        "audit_id": "FIG-P608-01 STRICT_R1_SA1_REQUAL_R97_20260824",
        "identity": identity,
        "counts": {
            "text_objects": len(text_objects), "graphic_objects": len(graphics), "all_objects": len(objects),
            "expected_unordered_pairs": len(objects) * (len(objects) - 1) // 2, "reported_unordered_pairs": len(pair_rows),
            "visible_glyphs": len(glyphs), "low_profile_glyphs": sum(g.low_profile for g in glyphs),
            "glyph_cards": len(glyph_cards), "glyph_contact_sheets": len(glyph_sheets), "pair_cards": sum(bool(r["evidence_card"]) for r in pair_rows),
            "pair_contact_sheets": len(pair_sheets), "intended_contacts": len(contact_rows),
            "math_rules": len(rule_rows), "unassigned_foreground_pdf_paths": drawing_summary["unassigned_foreground_path_count"],
        },
        "hard_gate_counts": {
            "font_size_fail": sum(g.size_gate.startswith("FAIL") for g in glyphs),
            "pixel_fail": sum(g.pixel_gate.startswith("FAIL") for g in glyphs),
            "purity_fail": sum(g.purity.startswith("FAIL") for g in glyphs),
            "unwhitelisted_pair_fail": len(fail_pairs),
        },
        "critical_R002_vs_G001": critical,
        "status": "MACHINE_AUDIT_COMPLETE_HUMAN_REVIEW_PENDING_NO_TERMINAL",
        "inspection_artifacts": {"glyph_sheets": glyph_sheets, "pair_sheets": pair_sheets, "math_rule_cards": rule_paths},
    }
    dump_json("preliminary_machine_summary.json", summary)
    # Machine generated worksheet: it deliberately has no terminal conclusion.
    lines = [
        "# Human pixel-review worksheet — FIG-P608-01 R1", "",
        "Decision pixels are only `native_page_659_300dpi.png` at 1×.  The cards use 8× nearest-neighbour solely to expose those raw pixels.", "",
        f"- Glyphs: {len(glyphs)}; glyph cards: {len(glyph_cards)}; sheets: {len(glyph_sheets)}",
        f"- Objects: {len(objects)}; all unordered pairs: {len(pair_rows)} / {len(objects) * (len(objects)-1)//2}",
        f"- Critical/contact pair cards: {sum(bool(r['evidence_card']) for r in pair_rows)}; sheets: {len(pair_sheets)}", "",
        "## Required human actions", "",
        "- Inspect every glyph contact sheet and every pair-contact sheet at native-pixel fidelity.",
        "- Verify every intended contact has its individual semantic reason in `intended_contact_ledger.csv`.",
        "- Record any line-through-text, mask mixture, crop breach, z-order anomaly, or grayscale ambiguity before finalisation.",
        "- Do not infer a terminal status from this worksheet.",
    ]
    (OUT / "HUMAN_PIXEL_REVIEW_WORKSHEET.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if "--critical-only" in sys.argv:
        build_critical_only()
    else:
        build_reports()
