#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent strict SA1 audit for FIG-P558-01, frozen R93 only.

This script is evidence-producing only. It reads the frozen PDF/source/body and
writes solely to this SA1 evidence directory. Pixel measurements are made on a
single direct 300 dpi raster of the full physical PDF page; every crop below is
a no-resize pixel slice of that grid.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


FIGURE_ID = "FIG-P558-01"
REVIEW_ID = "SA1_20260824_R1"
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / FIGURE_ID / "STRICT_R1" / REVIEW_ID
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r93_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C01" / "fig_v5_c01_random_walk.tex"
BODY = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C01.tex"
STYLE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "common" / "statlearnbook.sty"

PDF_PAGE_INDEX = 604  # physical page 605 (0-indexed PyMuPDF)
PHYSICAL_PAGE = 605
PRINTED_PAGE = 592
DPI = 300
SCALE = DPI / 72.0
FIG_RECT = fitz.Rect(70, 50, 535, 282)          # source figure + caption, PDF points
STANDALONE_RECT = fitz.Rect(75, 54, 525, 260)   # source figure body, no caption


def mkdirs() -> None:
    for name in ("masks/glyph_raw", "masks/text_raw", "masks/vector_raw",
                 "masks/vector_visible_raw", "masks/halo_raw", "critical_pairs"):
        (OUT / name).mkdir(parents=True, exist_ok=True)


def clear_prior_generated_evidence() -> None:
    """Remove only this SA1 run's earlier generated output before a fresh run.

    This avoids leaving an ROI/mask from an intermediate threshold pass in the
    final evidence directory. The fixed target is this task's unique evidence
    directory; the audit script itself is retained.
    """
    if not OUT.exists():
        return
    keep = {Path(__file__).name}
    for item in OUT.iterdir():
        if item.name in keep:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def stable_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else ["EMPTY"]
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for part in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def rectpx(rect: fitz.Rect, width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect.x0 * SCALE)) - pad)
    y0 = max(0, int(math.floor(rect.y0 * SCALE)) - pad)
    x1 = min(width, int(math.ceil(rect.x1 * SCALE)) + pad)
    y1 = min(height, int(math.ceil(rect.y1 * SCALE)) + pad)
    return x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)


def pxrect_to_list(rect: tuple[int, int, int, int]) -> list[int]:
    return [int(v) for v in rect]


def rect_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return float(math.hypot(dx, dy))


@dataclass
class MaskRef:
    """A trimmed raw binary mask positioned on the fixed full-page grid."""
    x0: int
    y0: int
    data: np.ndarray

    @property
    def x1(self) -> int:
        return self.x0 + int(self.data.shape[1])

    @property
    def y1(self) -> int:
        return self.y0 + int(self.data.shape[0])

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return (self.x0, self.y0, self.x1, self.y1)

    @property
    def area(self) -> int:
        return int(self.data.sum())


def trim_mask(full: np.ndarray, x0: int = 0, y0: int = 0) -> MaskRef:
    ys, xs = np.where(full)
    if len(xs) == 0:
        return MaskRef(x0, y0, np.zeros((1, 1), dtype=bool))
    xa, xb = int(xs.min()), int(xs.max()) + 1
    ya, yb = int(ys.min()), int(ys.max()) + 1
    return MaskRef(x0 + xa, y0 + ya, full[ya:yb, xa:xb].astype(bool, copy=True))


def blank_like(ref: MaskRef) -> MaskRef:
    return MaskRef(ref.x0, ref.y0, np.zeros_like(ref.data, dtype=bool))


def paste_into(ref: MaskRef, x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
    canvas = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    xa, xb = ref.x0 - x0, ref.x1 - x0
    ya, yb = ref.y0 - y0, ref.y1 - y0
    canvas[ya:yb, xa:xb] = ref.data
    return canvas


def union_refs(refs: Iterable[MaskRef]) -> MaskRef:
    refs = [r for r in refs if r.area]
    if not refs:
        return MaskRef(0, 0, np.zeros((1, 1), dtype=bool))
    x0, y0 = min(r.x0 for r in refs), min(r.y0 for r in refs)
    x1, y1 = max(r.x1 for r in refs), max(r.y1 for r in refs)
    arr = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    for r in refs:
        arr[r.y0-y0:r.y1-y0, r.x0-x0:r.x1-x0] |= r.data
    return trim_mask(arr, x0, y0)


def subtract_refs(base: MaskRef, covers: Iterable[MaskRef]) -> MaskRef:
    arr = base.data.copy()
    for c in covers:
        x0, y0 = max(base.x0, c.x0), max(base.y0, c.y0)
        x1, y1 = min(base.x1, c.x1), min(base.y1, c.y1)
        if x1 > x0 and y1 > y0:
            arr[y0-base.y0:y1-base.y0, x0-base.x0:x1-base.x0] &= ~c.data[y0-c.y0:y1-c.y0, x0-c.x0:x1-c.x0]
    return trim_mask(arr, base.x0, base.y0)


def overlap_px(a: MaskRef, b: MaskRef) -> int:
    x0, y0 = max(a.x0, b.x0), max(a.y0, b.y0)
    x1, y1 = min(a.x1, b.x1), min(a.y1, b.y1)
    if x1 <= x0 or y1 <= y0:
        return 0
    aa = a.data[y0-a.y0:y1-a.y0, x0-a.x0:x1-a.x0]
    bb = b.data[y0-b.y0:y1-b.y0, x0-b.x0:x1-b.x0]
    return int(np.count_nonzero(aa & bb))


def pixel_distance(a: MaskRef, b: MaskRef, shortcut: float = 24.0) -> float:
    """Exact raw-pixel distance when close; bbox lower bound otherwise."""
    if not a.area or not b.area:
        return math.inf
    bb = rect_distance(a.bbox, b.bbox)
    if bb > shortcut:
        return bb
    x0, y0 = min(a.x0, b.x0), min(a.y0, b.y0)
    x1, y1 = max(a.x1, b.x1), max(a.y1, b.y1)
    aa = paste_into(a, x0, y0, x1, y1)
    bbmask = paste_into(b, x0, y0, x1, y1)
    if np.any(aa & bbmask):
        return 0.0
    return float(distance_transform_edt(~bbmask)[aa].min())


def save_mask(ref: MaskRef, path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((ref.data.astype(np.uint8) * 255), mode="L").save(path)
    return {"path": str(path.relative_to(OUT)).replace("\\", "/"), "bbox_px": pxrect_to_list(ref.bbox), "foreground_px": ref.area}


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def threshold_for(ch: str, pdf_span_pt: float) -> tuple[str, int]:
    cp = ord(ch)
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK", 30
    # Fullwidth Chinese punctuation retains the 30px *height* rule, but it is
    # not ratio-comparable to a full-height Han ideograph. D compares only the
    # same script class, so do not manufacture CJK-ratio failures from a colon.
    if 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF:
        return "FULLWIDTH_PUNCT", 30
    if ch.isdigit():
        return "DIGIT", 24
    if ch.isalpha() and ch.isupper():
        return "UPPER", 24
    if "GREEK" in unicodedata.name(ch, ""):
        return "GREEK", 17
    if ch.isalpha():
        if pdf_span_pt < 8.0:
            return "NATURAL_SCRIPT", 15
        return "LOWER", 17
    if ch in "−-+=*/()[]{}<>|,:;.，。；：、…/":
        return "MATH_OPERATOR_PUNCT", 22
    return "OTHER_PUNCT", 22


def source_rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src")).replace("\\", "/")
    except ValueError:
        return str(path)


def rect(x0: float, y0: float, x1: float, y1: float) -> fitz.Rect:
    return fitz.Rect(x0, y0, x1, y1)


def make_objects() -> list[dict[str, Any]]:
    # Rectangles come from current frozen-PDF rawdict spans, expanded only enough
    # to group a semantic object; glyph masks remain restricted to each glyph bbox.
    o: list[dict[str, Any]] = []
    def add(id: str, role: str, panel: str, r: tuple[float, float, float, float], text: str,
            pt: float, line: int, note: str = "") -> None:
        o.append({"id": id, "role": role, "panel": panel, "rect_pdf": rect(*r),
                  "text": text, "declared_pt": pt, "source_line": line, "note": note})
    add("SIMPLE_TITLE", "TITLE", "TOPOLOGY_SIMPLE", (173, 66, 220, 86), "简单游走", 10.4, 18)
    for n, x in ((1, 142), (2, 192), (3, 241)):
        add(f"SIMPLE_STATE_{n}", "STATE_LABEL", "TOPOLOGY_SIMPLE", (x, 115, x+10, 129), str(n), 9.4, 19+n-1)
    add("SIMPLE_P12", "EDGE_LABEL", "TOPOLOGY_SIMPLE", (168, 106, 175, 117), "1", 8.8, 22)
    add("SIMPLE_P21", "EDGE_LABEL", "TOPOLOGY_SIMPLE", (164, 128, 180, 139), "1/2", 8.8, 23)
    add("SIMPLE_P23", "EDGE_LABEL", "TOPOLOGY_SIMPLE", (214, 105, 229, 117), "1/2", 8.8, 24)
    add("SIMPLE_P32", "EDGE_LABEL", "TOPOLOGY_SIMPLE", (218, 127, 225, 139), "1", 8.8, 25)
    add("LAZY_TITLE", "TITLE", "TOPOLOGY_LAZY", (380, 66, 427, 86), "惰性游走", 10.4, 28)
    for n, x in ((1, 349), (2, 399), (3, 448)):
        add(f"LAZY_STATE_{n}", "STATE_LABEL", "TOPOLOGY_LAZY", (x, 115, x+10, 129), str(n), 9.4, 29+n-1)
    add("LAZY_P12", "EDGE_LABEL", "TOPOLOGY_LAZY", (371, 105, 387, 117), "1/2", 8.8, 32)
    add("LAZY_P21", "EDGE_LABEL", "TOPOLOGY_LAZY", (371, 128, 387, 139), "1/4", 8.8, 33)
    add("LAZY_P23", "EDGE_LABEL", "TOPOLOGY_LAZY", (420, 105, 437, 117), "1/4", 8.8, 34)
    add("LAZY_P32", "EDGE_LABEL", "TOPOLOGY_LAZY", (420, 127, 437, 139), "1/2", 8.8, 35)
    add("LAZY_LOOP_1", "EDGE_LABEL", "TOPOLOGY_LAZY", (308, 116, 324, 129), "1/2", 8.8, 36)
    add("LAZY_LOOP_2", "EDGE_LABEL", "TOPOLOGY_LAZY", (403, 90, 419, 102), "1/2", 8.8, 37)
    add("LAZY_LOOP_3", "EDGE_LABEL", "TOPOLOGY_LAZY", (483, 116, 499, 129), "1/2", 8.8, 38)
    # Plot panels: ticks stay independent semantic objects; the natural axis formula stays a parent.
    for panel, annotation, tickline, labelline, annline in (
        ("PLOT_SIMPLE", "奇偶振荡", 45, 46, 51),
        ("PLOT_LAZY", "阻尼收敛", 57, 58, 63),
    ):
        shift = 0 if panel == "PLOT_SIMPLE" else 207
        for val, x in zip(("0", "2", "4", "6", "8"), (125.5+shift, 150.7+shift, 175.5+shift, 200.5+shift, 225.5+shift)):
            add(f"{panel}_XTICK_{val}", "TICK_LABEL", panel, (x, 190, x+6, 201), val, 8.6, tickline)
        for val, x, y in (("0.25", 105.5+shift, 179.5), ("0.5", 110+shift, 173.2), ("0.75", 105.5+shift, 166.8)):
            add(f"{panel}_YTICK_{val.replace('.', '_')}", "TICK_LABEL", panel, (x, y, x+18, y+11), val, 8.6, tickline)
        add(f"{panel}_ANNOTATION", "ANNOTATION", panel, (159+shift, 157, 198+shift, 170), annotation, 8.8, annline)
        add(f"{panel}_X_TITLE", "AXIS_TITLE", panel, (174+shift, 202, 182+shift, 215), "t", 9.2, labelline)
        add(f"{panel}_Y_TITLE", "AXIS_TITLE", panel, (87+shift, 155, 103+shift, 201), "P(X_t=2)", 9.2, labelline, "base 9.2pt; t is legal natural TeX script")
    add("SUMMARY", "SUMMARY_FORMULA", "SUMMARY", (173, 242, 427, 257), "共享平稳分布 π=(1/4,1/2,1/4)；惰性自环把周期从2降为1", 9.2, 65)
    add("CAPTION", "CAPTION", "CAPTION", (105, 260, 479, 279), "图30.7 三节点路径的简单游走与惰性游走：加入自环保持平稳分布并消除周期振荡", 9.963, 70, "inherited \\small resolved in frozen PDF")
    return o


def identify_vector(idx: int, drawing: dict[str, Any]) -> tuple[str, str, str]:
    """Return category, id, owner. All current-figure vector drawings are enumerated."""
    node_map = {1: ("SIMPLE_NODE_1", "SIMPLE_STATE_1"), 2: ("SIMPLE_NODE_2", "SIMPLE_STATE_2"),
                3: ("SIMPLE_NODE_3", "SIMPLE_STATE_3"), 16: ("LAZY_NODE_1", "LAZY_STATE_1"),
                17: ("LAZY_NODE_2", "LAZY_STATE_2"), 18: ("LAZY_NODE_3", "LAZY_STATE_3")}
    halos = {6, 9, 12, 15, 21, 24, 27, 30, 33, 36, 39, 48, 66}
    arrows = {4, 7, 10, 13, 19, 22, 25, 28, 31, 34, 37}
    arrowheads = {5, 8, 11, 14, 20, 23, 26, 29, 32, 35, 38}
    if idx in node_map:
        ident, owner = node_map[idx]
        return "NODE_BORDER", ident, owner
    if idx in halos:
        return "HALO_BACKGROUND", f"HALO_{idx:02d}", ""
    if idx in arrows:
        return "LINE_ARROW", f"ARROW_{idx:02d}", ""
    if idx in arrowheads:
        return "ARROWHEAD", f"ARROWHEAD_{idx:02d}", ""
    if idx in (40, 41, 58, 59):
        return "AUX_LINE", f"AXIS_TICK_{idx:02d}", ""
    if idx in (42, 44, 60, 62):
        return "LINE_ARROW", f"AXIS_{idx:02d}", ""
    if idx in (43, 45, 61, 63):
        return "ARROWHEAD", f"AXIS_HEAD_{idx:02d}", ""
    if idx in (46, 47, 64, 65):
        return "DATA_CURVE", f"CURVE_{idx:02d}", ""
    if 49 <= idx <= 57 or 67 <= idx <= 75:
        return "MARKER", f"MARKER_{idx:02d}", ""
    if idx == 76:
        return "PANEL_BORDER", "SUMMARY_BORDER", "SUMMARY"
    return "UNKNOWN_VECTOR", f"DRAWING_{idx:02d}", ""


def draw_mask_from_pdf_drawing(page: fitz.Page, drawing: dict[str, Any], kind: str, width: int, height: int) -> MaskRef:
    """Re-render one extracted vector path on a blank page: independent raw mask."""
    doc = fitz.open()
    pg = doc.new_page(width=page.rect.width, height=page.rect.height)
    sh = pg.new_shape()
    for item in drawing["items"]:
        typ = item[0]
        if typ == "l":
            sh.draw_line(item[1], item[2])
        elif typ == "c":
            sh.draw_bezier(item[1], item[2], item[3], item[4])
        elif typ == "re":
            sh.draw_rect(item[1])
        else:
            raise RuntimeError(f"unhandled drawing item {typ}")
    original_fill = drawing.get("fill")
    original_color = drawing.get("color")
    if kind == "HALO_BACKGROUND":
        color, fill, stroke_width = None, (0.0, 0.0, 0.0), 1.0
    elif kind in ("NODE_BORDER", "PANEL_BORDER"):
        color, fill, stroke_width = original_color, None, float(drawing.get("width") or 1.0)
    else:
        color, fill, stroke_width = original_color, original_fill, float(drawing.get("width") or 1.0)
    cap = drawing.get("lineCap")
    if isinstance(cap, (tuple, list)):
        cap = cap[0]
    cap = int(cap or 0)
    join = int(drawing.get("lineJoin") or 0)
    sh.finish(width=stroke_width, color=color, fill=fill, lineCap=cap, lineJoin=join,
              dashes=drawing.get("dashes"), even_odd=bool(drawing.get("even_odd") or False),
              closePath=bool(drawing.get("closePath") or False),
              fill_opacity=float(drawing.get("fill_opacity") or 1.0),
              stroke_opacity=float(drawing.get("stroke_opacity") or 1.0))
    sh.commit()
    pix = pg.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    # blank rendering makes max colour delta an independent vector foreground test.
    mask = np.max(255 - arr, axis=2) >= 20
    doc.close()
    return trim_mask(mask)


def raw_text_mask(page_rgb: np.ndarray, char_rect: tuple[int, int, int, int], text_rgb: tuple[int, int, int]) -> MaskRef:
    """No-dilation glyph mask, colour-matched to its PDF text paint.

    The drawing has teal/blue arrows that can pass through a glyph's PDF bbox.
    A generic ``dark pixel`` selection would let that independent vector paint
    inflate the text mask.  PDF rawdict supplies each span's paint RGB, so we
    retain pixels along that exact alpha-blend ray from white to the text RGB;
    this preserves raw 300dpi ink while keeping text and vector masks separate.
    """
    x0, y0, x1, y1 = char_rect
    crop = page_rgb[y0:y1, x0:x1].astype(np.float32)
    delta = 255.0 - crop
    expected_delta = 255.0 - np.asarray(text_rgb, dtype=np.float32)
    denom = float(np.dot(expected_delta, expected_delta))
    alpha = np.sum(delta * expected_delta, axis=2) / denom
    predicted = alpha[..., None] * expected_delta
    residual = np.max(np.abs(delta - predicted), axis=2)
    # 20/255 is the mandatory foreground lower bound. Residual tolerance only
    # permits PDF raster rounding / anti-aliasing, not a different coloured path.
    mask = (np.max(delta, axis=2) >= 20.0) & (alpha > 0.0) & (residual <= 7.0)
    return trim_mask(mask, x0, y0)


def int_rgb_to_tuple(value: int) -> tuple[int, int, int]:
    return ((int(value) >> 16) & 255, (int(value) >> 8) & 255, int(value) & 255)


def h_ink(ref: MaskRef, vertical_writing: bool = False) -> int:
    """Ink height perpendicular to the glyph baseline.

    For normal horizontal writing this is the raster y-extent.  The two y-axis
    formulae are rotated PDF text (`line.dir=(0,-1)`), so their intrinsic glyph
    height is the raster x-extent; treating page-y as height would falsely turn
    ordinary rotated capitals/digits into tiny characters.
    """
    if not ref.area:
        return 0
    return int(ref.data.shape[1] if vertical_writing else ref.data.shape[0])


def render_pair_artifacts(pair: dict[str, Any], a: MaskRef, b: MaskRef, page_rgb: np.ndarray,
                          width: int, height: int) -> dict[str, str]:
    margin = 8
    x0 = max(0, min(a.x0, b.x0) - margin)
    y0 = max(0, min(a.y0, b.y0) - margin)
    x1 = min(width, max(a.x1, b.x1) + margin)
    y1 = min(height, max(a.y1, b.y1) + margin)
    aa = paste_into(a, x0, y0, x1, y1)
    bb = paste_into(b, x0, y0, x1, y1)
    inter = aa & bb
    key = safe_id(pair["pair_id"])
    raw_path = OUT / "critical_pairs" / f"{key}_raw.png"
    a_path = OUT / "critical_pairs" / f"{key}_a_rawmask.png"
    b_path = OUT / "critical_pairs" / f"{key}_b_rawmask.png"
    i_path = OUT / "critical_pairs" / f"{key}_intersection.png"
    o_path = OUT / "critical_pairs" / f"{key}_overlay.png"
    z_path = OUT / "critical_pairs" / f"{key}_8xNN.png"
    Image.fromarray(page_rgb[y0:y1, x0:x1], mode="RGB").save(raw_path)
    Image.fromarray((aa.astype(np.uint8) * 255), mode="L").save(a_path)
    Image.fromarray((bb.astype(np.uint8) * 255), mode="L").save(b_path)
    Image.fromarray((inter.astype(np.uint8) * 255), mode="L").save(i_path)
    over = page_rgb[y0:y1, x0:x1].copy()
    over[aa] = (255, 60, 60)
    over[bb] = (40, 220, 255)
    over[inter] = (255, 0, 255)
    ovimg = Image.fromarray(over, mode="RGB")
    ovimg.save(o_path)
    ovimg.resize((ovimg.width * 8, ovimg.height * 8), Image.Resampling.NEAREST).save(z_path)
    def rel(p: Path) -> str:
        return str(p.relative_to(OUT)).replace("\\", "/")
    return {"roi_bbox_px": json.dumps([x0, y0, x1, y1]), "raw_roi": rel(raw_path),
            "a_mask": rel(a_path), "b_mask": rel(b_path), "intersection": rel(i_path),
            "overlay": rel(o_path), "nn8x": rel(z_path)}


def add_overlay(crop: np.ndarray, objects: list[dict[str, Any]], crop_origin: tuple[int, int]) -> None:
    img = Image.fromarray(crop.copy(), mode="RGB")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    role_color = {"TITLE": (205, 35, 35), "STATE_LABEL": (20, 90, 220), "EDGE_LABEL": (170, 75, 0),
                  "TICK_LABEL": (80, 0, 180), "AXIS_TITLE": (0, 135, 100), "ANNOTATION": (190, 0, 120),
                  "SUMMARY_FORMULA": (0, 130, 180), "CAPTION": (70, 70, 70)}
    ox, oy = crop_origin
    for obj in objects:
        x0, y0, x1, y1 = obj["bbox_px"]
        x0, y0, x1, y1 = x0-ox, y0-oy, x1-ox, y1-oy
        col = role_color.get(obj["role"], (255, 0, 0))
        draw.rectangle((x0, y0, x1-1, y1-1), outline=col, width=1)
        draw.text((x0, max(0, y0-9)), obj["id"], fill=col, font=font)
    img.save(OUT / "after_text_measurement_overlay_300dpi.png")


def get_chardata(page: fitz.Page, objects: list[dict[str, Any]], page_w: int, page_h: int,
                 page_rgb: np.ndarray) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw = page.get_text("rawdict")
    chars: list[dict[str, Any]] = []
    unassigned: list[dict[str, Any]] = []
    fig = FIG_RECT
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            direction = tuple(line.get("dir", (1.0, 0.0)))
            vertical_writing = abs(direction[1]) > abs(direction[0])
            for span in line["spans"]:
                span_pt = float(span.get("size", 0.0))
                text_rgb = int_rgb_to_tuple(int(span.get("color", 0)))
                for character in span["chars"]:
                    # TeX-inserted spaces have no visible ink and are not reader-visible
                    # glyphs/semantic punctuation. They remain inside the parent formula.
                    if character["c"].isspace():
                        continue
                    cb = fitz.Rect(character["bbox"])
                    center = fitz.Point((cb.x0+cb.x1)/2, (cb.y0+cb.y1)/2)
                    if not fig.contains(center):
                        continue
                    matches = [o for o in objects if o["rect_pdf"].contains(center)]
                    if len(matches) != 1:
                        unassigned.append({"character": character["c"], "bbox_pdf": list(cb),
                                           "matching_objects": [m["id"] for m in matches]})
                        continue
                    obj = matches[0]
                    pxb = rectpx(cb, page_w, page_h, pad=0)
                    mask = raw_text_mask(page_rgb, pxb, text_rgb)
                    script, minimum = threshold_for(character["c"], span_pt)
                    glyph_no = len(obj.setdefault("glyphs", [])) + 1
                    gid = f"{obj['id']}__g{glyph_no:02d}"
                    mask_info = save_mask(mask, OUT / "masks" / "glyph_raw" / f"{safe_id(gid)}.png")
                    item = {"ELEMENT_ID": gid, "PARENT_ELEMENT_ID": obj["id"], "PANEL_ID": obj["panel"],
                            "ROLE": obj["role"], "SOURCE_FILE": source_rel(SOURCE), "SOURCE_LINE": obj["source_line"],
                            "DECLARED_PT": obj["declared_pt"], "GRAPHICS_SCALE": 1.0,
                            "EFFECTIVE_PT": obj["declared_pt"], "PDF_SPAN_PT": round(span_pt, 3),
                            "TEXT_SAMPLE": character["c"], "SCRIPT_CLASS": script,
                            "MIN_REQUIRED_PX": minimum, "BBOX_X0": pxb[0], "BBOX_Y0": pxb[1],
                            "BBOX_X1": pxb[2], "BBOX_Y1": pxb[3],
                            "TEXT_DIRECTION": json.dumps(direction),
                            "PDF_TEXT_RGB": json.dumps(text_rgb),
                            "H_INK_AXIS": "x_extent_for_rotated_text" if vertical_writing else "y_extent",
                            "H_INK_PX": h_ink(mask, vertical_writing),
                            "MASK_PATH": mask_info["path"], "MASK_FOREGROUND_PX": mask_info["foreground_px"],
                            "legal_script": script == "NATURAL_SCRIPT" and obj["id"].endswith("Y_TITLE"),
                            "raw_mask": mask}
                    chars.append(item)
                    obj["glyphs"].append(item)
    for obj in objects:
        glyphs = obj.get("glyphs", [])
        obj["mask"] = union_refs([g["raw_mask"] for g in glyphs])
        obj["bbox_px"] = obj["mask"].bbox if obj["mask"].area else rectpx(obj["rect_pdf"], page_w, page_h)
        obj["mask_info"] = save_mask(obj["mask"], OUT / "masks" / "text_raw" / f"{safe_id(obj['id'])}.png")
    return chars, unassigned


def classify_source_fonts(objects: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    global_role: dict[str, list[dict[str, Any]]] = {}
    for o in objects:
        groups.setdefault((o["panel"], o["role"]), []).append(o)
        global_role.setdefault(o["role"], []).append(o)
    per_group: dict[tuple[str, str], tuple[float, float, bool]] = {}
    for key, vals in groups.items():
        pts = [float(v["declared_pt"]) for v in vals]
        ratio = max(pts)/min(pts)
        diff = max(pts)-min(pts)
        per_group[key] = (ratio, diff, ratio <= 1.03 and diff <= 0.25)
    cross: dict[str, tuple[float, bool]] = {}
    for role, vals in global_role.items():
        pts = [float(v["declared_pt"]) for v in vals]
        ratio = max(pts)/min(pts)
        cross[role] = (ratio, ratio <= 1.05)
    for o in objects:
        sr, sd, sp = per_group[(o["panel"], o["role"])]
        cr, cp = cross[o["role"]]
        source_pass = float(o["declared_pt"]) >= 9.5 and sp and cp
        rows.append({"ELEMENT_ID": o["id"], "PANEL_ID": o["panel"], "ROLE": o["role"],
                     "SOURCE_FILE": source_rel(SOURCE), "SOURCE_LINE": o["source_line"],
                     "DECLARED_PT": o["declared_pt"], "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": o["declared_pt"],
                     "MIN_EFFECTIVE_PT": 9.5, "SAME_ROLE_PANEL_MAX_MIN": round(sr, 4),
                     "SAME_ROLE_PANEL_DIFF_PT": round(sd, 3), "SAME_ROLE_PANEL_PASS": sp,
                     "CROSS_PANEL_ROLE_MAX_MIN": round(cr, 4), "CROSS_PANEL_ROLE_PASS": cp,
                     "SCRIPT_EXCEPTION": o["note"] if "natural" in o["note"] else "",
                     "PASS_FAIL": "PASS" if source_pass else "FAIL",
                     "REASON": "" if source_pass else ("effective_pt<9.5" if o["declared_pt"] < 9.5 else "role_size_consistency")})
    stats: list[dict[str, Any]] = []
    for (panel, role), (ratio, diff, passed) in per_group.items():
        stats.append({"check_type": "SOURCE_SAME_PANEL_ROLE", "panel": panel, "role": role,
                      "script_class": "N/A_SOURCE_PT", "n": len(groups[(panel, role)]), "ratio": round(ratio, 4),
                      "threshold": "max/min<=1.03; diff<=0.25pt", "difference_pt": round(diff, 3),
                      "PASS_FAIL": "PASS" if passed else "FAIL", "basis": "actual effective_pt from current source"})
    for role, (ratio, passed) in cross.items():
        stats.append({"check_type": "SOURCE_CROSS_PANEL_ROLE", "panel": "CROSS_PANEL", "role": role,
                      "script_class": "N/A_SOURCE_PT", "n": len(global_role[role]), "ratio": round(ratio, 4),
                      "threshold": "max/min<=1.05", "difference_pt": "", "PASS_FAIL": "PASS" if passed else "FAIL",
                      "basis": "actual effective_pt from current source"})
    return rows, stats


def semantic_script_components(glyphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build ratio units as semantic parent object × script class.

    C still measures every glyph (including all literal punctuation).  D/E,
    however, compare semantic elements rather than splitting a natural title or
    caption into artificial one-character ratio objects. This is why the unit
    below is neither an exact glyph nor a cross-script aggregate.
    """
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for g in glyphs:
        grouped.setdefault((g["PARENT_ELEMENT_ID"], g["PANEL_ID"], g["ROLE"], g["SCRIPT_CLASS"]), []).append(g)
    result: list[dict[str, Any]] = []
    for (parent, panel, role, script), vals in sorted(grouped.items()):
        m = union_refs([g["raw_mask"] for g in vals])
        vertical = vals[0]["H_INK_AXIS"] == "x_extent_for_rotated_text"
        cid = f"{parent}::{script}"
        mi = save_mask(m, OUT / "masks" / "text_raw" / "script_components" / f"{safe_id(cid)}.png")
        result.append({"id": cid, "parent": parent, "panel": panel, "role": role, "script": script,
                       "glyphs": vals, "mask": m, "h": h_ink(m, vertical), "axis": vals[0]["H_INK_AXIS"],
                       "mask_path": mi["path"]})
    return result


def compute_class_ratios(glyphs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool, list[dict[str, Any]]]:
    components = semantic_script_components(glyphs)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for c in components:
        grouped.setdefault((c["panel"], c["role"], c["script"]), []).append(c)
    rows: list[dict[str, Any]] = []
    all_pass = True
    for key, vals in sorted(grouped.items()):
        hs = np.array([v["h"] for v in vals], dtype=float)
        med = float(np.median(hs))
        elrat = [float(v["h"] / med) if med else math.inf for v in vals]
        extrema = float(max(hs) / min(hs)) if min(hs) else math.inf
        group_pass = all(.92 <= x <= 1.08 for x in elrat) and extrema <= 1.08
        all_pass &= group_pass
        for v, ratio in zip(vals, elrat):
            passed = bool(.92 <= ratio <= 1.08 and extrema <= 1.08)
            for g in v["glyphs"]:
                g["CLASS_MEDIAN_PX"] = round(med, 3)
                g["RATIO_TO_CLASS_MEDIAN"] = round(ratio, 4)
                g["SAME_CLASS_PASS"] = passed
                g["RATIO_COMPONENT_ID"] = v["id"]
            rows.append({"check_type": "SAME_PANEL_ROLE_SCRIPT", "panel": key[0], "role": key[1],
                         "script_class": key[2], "ELEMENT_ID": v["id"], "PARENT_ELEMENT_ID": v["parent"],
                         "GLYPH_COUNT": len(v["glyphs"]), "H_INK_PX": v["h"], "H_INK_AXIS": v["axis"],
                         "RAW_MASK": v["mask_path"], "class_median_px": round(med, 3),
                         "ratio_to_median": round(ratio, 4), "group_extrema_ratio": round(extrema, 4),
                         "threshold": "each[0.92,1.08]; extrema<=1.08", "PASS_FAIL": "PASS" if passed else "FAIL",
                         "basis": "actual raw H_ink_px of semantic parent×script; same panel+role+script only"})
    return rows, all_pass, components


def compute_cross_panel_ratios(components: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    grp: dict[tuple[str, str], dict[str, list[float]]] = {}
    for c in components:
        grp.setdefault((c["role"], c["script"]), {}).setdefault(c["panel"], []).append(float(c["h"]))
    rows: list[dict[str, Any]] = []
    all_pass = True
    for (role, script), by_panel in sorted(grp.items()):
        medians = {panel: float(np.median(hs)) for panel, hs in by_panel.items()}
        if len(medians) < 2:
            rows.append({"check_type": "CROSS_PANEL_ROLE_SCRIPT", "panel": "N/A", "role": role,
                         "script_class": script, "n": sum(len(x) for x in by_panel.values()), "ratio": "N/A",
                         "threshold": "<=1.10", "difference_pt": "", "PASS_FAIL": "N/A",
                         "basis": "only one panel has this comparable role+script"})
            continue
        ratio = max(medians.values()) / min(medians.values()) if min(medians.values()) else math.inf
        passed = ratio <= 1.10
        all_pass &= passed
        rows.append({"check_type": "CROSS_PANEL_ROLE_SCRIPT", "panel": json.dumps(medians, ensure_ascii=False),
                     "role": role, "script_class": script, "n": sum(len(x) for x in by_panel.values()),
                     "ratio": round(ratio, 4), "threshold": "<=1.10", "difference_pt": "",
                     "PASS_FAIL": "PASS" if passed else "FAIL",
                     "basis": "actual raw H_ink_px semantic component medians; no cross-script comparison"})
    return rows, all_pass


def assign_role_ratios(components: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    """E uses same-script actual raw semantic-component H only."""
    group: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for c in components:
        group.setdefault((c["panel"], c["role"], c["script"]), []).append(c)
    med = {k: float(np.median([x["h"] for x in vals])) for k, vals in group.items()}
    panel_base = {"TOPOLOGY_SIMPLE": "STATE_LABEL", "TOPOLOGY_LAZY": "STATE_LABEL",
                  "PLOT_SIMPLE": "TICK_LABEL", "PLOT_LAZY": "TICK_LABEL"}
    expected = {"AXIS_TITLE": (1.00, 1.18), "ANNOTATION": (0.95, 1.10),
                "EDGE_LABEL": (1.00, 1.18)}
    rows: list[dict[str, Any]] = []
    all_pass = True
    for (panel, role, script), value in sorted(med.items()):
        base_role = panel_base.get(panel)
        base_key = (panel, base_role, script) if base_role else None
        if not base_key or base_key not in med:
            status, ratio, threshold, basis = "N/A", "N/A", "N/A", "no comparable script in local BASE; no cross-script proxy"
            per_glyph_role = "N/A"
        elif role == base_role:
            status, ratio, threshold, basis = "PASS", 1.0, "BASE=1.00", "actual raw H_ink_px"
            per_glyph_role = 1.0
        elif role not in expected:
            status, ratio, threshold, basis = "N/A", "N/A", "N/A", "role not governed by §9.2.1-E relative-to-BASE band"
            per_glyph_role = "N/A"
        else:
            lo, hi = expected[role]
            ratio = value / med[base_key] if med[base_key] else math.inf
            status = "PASS" if lo <= ratio <= hi else "FAIL"
            threshold = f"[{lo:.2f},{hi:.2f}]"
            basis = f"actual raw H_ink_px: {role} / {base_role}; script={script}"
            per_glyph_role = round(ratio, 4)
            all_pass &= status == "PASS"
        for c in group[(panel, role, script)]:
            for g in c["glyphs"]:
                g["ROLE_RATIO"] = per_glyph_role
        rows.append({"check_type": "ROLE_HIERARCHY", "panel": panel, "role": role,
                     "script_class": script, "n": len(group[(panel, role, script)]), "ratio": ratio,
                     "threshold": threshold, "difference_pt": "", "PASS_FAIL": status, "basis": basis})
    return rows, all_pass


def build_vector_components(page: fitz.Page, page_w: int, page_h: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    components: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    for idx, d in enumerate(page.get_drawings()):
        r = d["rect"]
        if idx == 0 or not (r.y1 > FIG_RECT.y0 and r.y0 < STANDALONE_RECT.y1 and r.x1 > FIG_RECT.x0 and r.x0 < FIG_RECT.x1):
            continue
        kind, cid, owner = identify_vector(idx, d)
        raw = draw_mask_from_pdf_drawing(page, d, kind, page_w, page_h)
        comp = {"id": cid, "drawing_index": idx, "kind": kind, "owner": owner, "seqno": int(d.get("seqno", -1)),
                "pdf_bbox": [round(float(v), 4) for v in d["rect"]], "raw": raw, "visible": raw,
                "fill": d.get("fill"), "stroke": d.get("color"), "width_pt": d.get("width"),
                "items": len(d.get("items", []))}
        if kind == "UNKNOWN_VECTOR":
            comp["unknown"] = True
        components.append(comp)
    halos = [c for c in components if c["kind"] == "HALO_BACKGROUND"]
    for comp in components:
        if comp["kind"] == "HALO_BACKGROUND":
            comp["raw_info"] = save_mask(comp["raw"], OUT / "masks" / "halo_raw" / f"{safe_id(comp['id'])}.png")
            comp["visible_info"] = comp["raw_info"]
        else:
            cover = [h["raw"] for h in halos if h["seqno"] > comp["seqno"]]
            comp["visible"] = subtract_refs(comp["raw"], cover)
            comp["raw_info"] = save_mask(comp["raw"], OUT / "masks" / "vector_raw" / f"{safe_id(comp['id'])}.png")
            comp["visible_info"] = save_mask(comp["visible"], OUT / "masks" / "vector_visible_raw" / f"{safe_id(comp['id'])}.png")
        inventory.append({"VECTOR_ID": comp["id"], "DRAWING_INDEX": comp["drawing_index"], "SEQNO": comp["seqno"],
                          "CATEGORY": comp["kind"], "OWNER": comp["owner"], "PDF_BBOX": json.dumps(comp["pdf_bbox"]),
                          "RAW_BBOX_PX": json.dumps(pxrect_to_list(comp["raw"].bbox)), "RAW_FOREGROUND_PX": comp["raw"].area,
                          "FINAL_VISIBLE_BBOX_PX": json.dumps(pxrect_to_list(comp["visible"].bbox)),
                          "FINAL_VISIBLE_FOREGROUND_PX": comp["visible"].area,
                          "FILL_RGB": json.dumps(comp["fill"]), "STROKE_RGB": json.dumps(comp["stroke"]),
                          "STROKE_WIDTH_PT": comp["width_pt"], "RAW_MASK": comp["raw_info"]["path"],
                          "FINAL_VISIBLE_MASK": comp["visible_info"]["path"],
                          "STATUS": "FAIL_UNKNOWN" if comp["kind"] == "UNKNOWN_VECTOR" else "PASS_ENUMERATED"})
    return components, inventory


def pair_audits(objects: list[dict[str, Any]], components: list[dict[str, Any]], page_rgb: np.ndarray,
                page_w: int, page_h: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, float]:
    rows: list[dict[str, Any]] = []
    refs: dict[str, MaskRef] = {o["id"]: o["mask"] for o in objects}
    critical: list[dict[str, Any]] = []
    # all independent semantic text-text combinations
    for i, a in enumerate(objects):
        for b in objects[i+1:]:
            overlap = overlap_px(a["mask"], b["mask"])
            clearance = rect_distance(a["bbox_px"], b["bbox_px"])
            cross = a["panel"] != b["panel"] and a["panel"] not in ("SUMMARY", "CAPTION") and b["panel"] not in ("SUMMARY", "CAPTION")
            threshold = 8 if cross else 4
            status = "FAIL_OVERLAP" if overlap else ("FAIL_CLEARANCE" if clearance < threshold else "PASS")
            p = {"pair_id": f"TT__{a['id']}__{b['id']}", "pair_type": "TEXT_TEXT", "A_ID": a["id"], "B_ID": b["id"],
                 "A_ROLE": a["role"], "B_CATEGORY": "TEXT", "OVERLAP_PIXEL_COUNT": overlap,
                 "PRE_OCCLUSION_OVERLAP_PX": 0, "CLEARANCE_PX": round(clearance, 3), "THRESHOLD_PX": threshold,
                 "CROSS_PANEL": cross, "HALO_STATUS": "NOT_APPLICABLE", "PASS_FAIL": status,
                 "METHOD": "separated raw text masks; bbox clearance; fixed full-page 300dpi"}
            refs[p["pair_id"]] = a["mask"]
            rows.append(p)
    # all text-to-final-visible vector components; halos retained separately as coverage evidence.
    graphics = [c for c in components if c["kind"] != "HALO_BACKGROUND"]
    for a in objects:
        for c in graphics:
            raw_overlap = overlap_px(a["mask"], c["raw"])
            final_overlap = overlap_px(a["mask"], c["visible"])
            clearance = pixel_distance(a["mask"], c["visible"])
            own_border = (c["kind"] in ("NODE_BORDER", "PANEL_BORDER") and c["owner"] == a["id"])
            threshold = 5 if own_border else 3
            if final_overlap:
                status = "FAIL_OVERLAP"
            elif clearance < threshold:
                status = "FAIL_CLEARANCE"
            elif raw_overlap:
                status = "PASS_HALO_COVERED"
            else:
                status = "PASS"
            ptype = "TEXT_NODE_BORDER" if c["kind"] == "NODE_BORDER" else ("TEXT_PANEL_BORDER" if c["kind"] == "PANEL_BORDER" else "TEXT_GRAPHIC")
            p = {"pair_id": f"TV__{a['id']}__{c['id']}", "pair_type": ptype, "A_ID": a["id"], "B_ID": c["id"],
                 "A_ROLE": a["role"], "B_CATEGORY": c["kind"], "OVERLAP_PIXEL_COUNT": final_overlap,
                 "PRE_OCCLUSION_OVERLAP_PX": raw_overlap, "CLEARANCE_PX": round(clearance, 3), "THRESHOLD_PX": threshold,
                 "CROSS_PANEL": False, "HALO_STATUS": "COVERED_BY_FINAL_HALO" if raw_overlap and not final_overlap else "NONE",
                 "PASS_FAIL": status, "METHOD": "separated vector raw/final-visible masks; final visibility subtracts later opaque PDF halo only"}
            rows.append(p)
            # Failure, near-threshold, or underlay-contact pairs need human-verifiable paired ROI/masks.
            if status != "PASS" or (math.isfinite(clearance) and clearance <= threshold + 2):
                critical.append({"pair": p, "a": a["mask"], "b": c["visible"], "raw_b": c["raw"]})
    # Text text criticals are added after all visual rows to preserve an exhaustive evidence index.
    objmap = {o["id"]: o for o in objects}
    for p in rows:
        if p["pair_type"] == "TEXT_TEXT" and (p["PASS_FAIL"] != "PASS" or p["CLEARANCE_PX"] <= p["THRESHOLD_PX"] + 2):
            critical.append({"pair": p, "a": objmap[p["A_ID"]]["mask"], "b": objmap[p["B_ID"]]["mask"], "raw_b": objmap[p["B_ID"]]["mask"]})
    # Produce one evidence bundle per unique critical pair. For halo contact, b is final visible and a separate raw-b mask is logged.
    critical_index: list[dict[str, Any]] = []
    for entry in critical:
        p = entry["pair"]
        paths = render_pair_artifacts(p, entry["a"], entry["b"], page_rgb, page_w, page_h)
        p.update(paths)
        if p["PRE_OCCLUSION_OVERLAP_PX"]:
            raw_path = OUT / "critical_pairs" / f"{safe_id(p['pair_id'])}_b_pre_occlusion_rawmask.png"
            save_mask(entry["raw_b"], raw_path)
            p["PRE_OCCLUSION_B_MASK"] = str(raw_path.relative_to(OUT)).replace("\\", "/")
        critical_index.append({"PAIR_ID": p["pair_id"], "STATUS": p["PASS_FAIL"], "OVERLAP_PIXEL_COUNT": p["OVERLAP_PIXEL_COUNT"],
                               "PRE_OCCLUSION_OVERLAP_PX": p["PRE_OCCLUSION_OVERLAP_PX"], "CLEARANCE_PX": p["CLEARANCE_PX"], **paths,
                               "PRE_OCCLUSION_B_MASK": p.get("PRE_OCCLUSION_B_MASK", "")})
    illegal_overlap = int(sum(p["OVERLAP_PIXEL_COUNT"] for p in rows))
    min_clear = min((float(p["CLEARANCE_PX"]) for p in rows if math.isfinite(float(p["CLEARANCE_PX"]))), default=math.inf)
    return rows, critical_index, illegal_overlap, min_clear


def trace_signature(rows: Iterable[dict[str, Any]], fields: tuple[str, ...]) -> str:
    text = "\n".join("|".join(str(row.get(field, "")) for field in fields) for row in sorted(rows, key=lambda r: str(r.get(fields[0], ""))))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_vector_inventory_and_pair_traceability(components: list[dict[str, Any]], inventory: list[dict[str, Any]],
                                                     objects: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Assert the emitted inventory fields and every pair's vector trace while components are still in memory."""
    errors: list[str] = []
    by_id = {c["id"]: c for c in components}
    if len(by_id) != len(components):
        errors.append("duplicate VECTOR_ID in in-memory components")
    if len(inventory) != len(components):
        errors.append(f"inventory rows {len(inventory)} != components {len(components)}")
    inventory_by_id = {str(r["VECTOR_ID"]): r for r in inventory}
    if len(inventory_by_id) != len(inventory):
        errors.append("duplicate VECTOR_ID in in-memory inventory")
    vector_records: list[dict[str, Any]] = []
    for cid, c in sorted(by_id.items()):
        row = inventory_by_id.get(cid)
        expected = {"VECTOR_ID": cid, "DRAWING_INDEX": c["drawing_index"], "CATEGORY": c["kind"], "OWNER": c["owner"],
                    "RAW_MASK": c["raw_info"]["path"], "FINAL_VISIBLE_MASK": c["visible_info"]["path"]}
        if row is None:
            errors.append(f"missing inventory row {cid}")
        else:
            for key, value in expected.items():
                if str(row.get(key)) != str(value):
                    errors.append(f"inventory mismatch {cid}.{key}: {row.get(key)!r}!={value!r}")
        vector_records.append({**expected, "IS_HALO_BACKGROUND": c["kind"] == "HALO_BACKGROUND"})
    unknown = [c["id"] for c in components if c["kind"] == "UNKNOWN_VECTOR"]
    halo = [c for c in components if c["kind"] == "HALO_BACKGROUND"]
    nonhalo = [c for c in components if c["kind"] != "HALO_BACKGROUND"]
    if len(halo) != 13:
        errors.append(f"HALO_BACKGROUND count {len(halo)} != 13")
    if len(nonhalo) != 63:
        errors.append(f"nonhalo final-visible count {len(nonhalo)} != 63")
    if unknown:
        errors.append("unknown vector(s): " + ",".join(unknown))
    obj_by_id = {o["id"]: o for o in objects}
    tt = 0
    tv = 0
    per_vector_pair_count = {c["id"]: 0 for c in nonhalo}
    for p in pair_rows:
        if p["pair_type"] == "TEXT_TEXT":
            tt += 1
            a, b = obj_by_id.get(p["A_ID"]), obj_by_id.get(p["B_ID"])
            if a is None or b is None:
                errors.append(f"text-text missing object {p['pair_id']}")
                continue
            cross = a["panel"] != b["panel"] and a["panel"] not in ("SUMMARY", "CAPTION") and b["panel"] not in ("SUMMARY", "CAPTION")
            expected_threshold = 8 if cross else 4
            if p["B_CATEGORY"] != "TEXT" or int(p["THRESHOLD_PX"]) != expected_threshold:
                errors.append(f"text-text trace mismatch {p['pair_id']}")
        else:
            tv += 1
            a, c = obj_by_id.get(p["A_ID"]), by_id.get(p["B_ID"])
            if a is None or c is None or c["kind"] == "HALO_BACKGROUND":
                errors.append(f"text-vector missing/halo B {p['pair_id']}")
                continue
            expected_threshold = 5 if c["kind"] in ("NODE_BORDER", "PANEL_BORDER") and c["owner"] == a["id"] else 3
            if p["B_CATEGORY"] != c["kind"] or int(p["THRESHOLD_PX"]) != expected_threshold:
                errors.append(f"text-vector trace mismatch {p['pair_id']}")
            per_vector_pair_count[c["id"]] += 1
    expected_tt = len(objects) * (len(objects) - 1) // 2
    expected_tv = len(objects) * len(nonhalo)
    if tt != expected_tt or tv != expected_tv or len(pair_rows) != expected_tt + expected_tv:
        errors.append(f"pair cardinality TT={tt}/{expected_tt}, TV={tv}/{expected_tv}, total={len(pair_rows)}")
    for cid, count in per_vector_pair_count.items():
        if count != len(objects):
            errors.append(f"vector {cid} has {count}/{len(objects)} text pairs")
    vector_fields = ("VECTOR_ID", "DRAWING_INDEX", "CATEGORY", "OWNER", "RAW_MASK", "FINAL_VISIBLE_MASK")
    pair_fields = ("pair_id", "pair_type", "A_ID", "B_ID", "B_CATEGORY", "THRESHOLD_PX")
    return {"pass": not errors, "errors": errors, "component_count": len(components), "inventory_row_count": len(inventory),
            "HALO_BACKGROUND_COUNT": len(halo), "NONHALO_FINAL_VISIBLE_COUNT": len(nonhalo), "UNKNOWN_VECTOR_COUNT": len(unknown),
            "TEXT_TEXT_PAIR_COUNT": tt, "TEXT_VECTOR_PAIR_COUNT": tv, "TOTAL_PAIR_COUNT": len(pair_rows),
            "EXPECTED_TOTAL_PAIR_COUNT": expected_tt + expected_tv, "vector_records": vector_records,
            "in_memory_inventory_signature": trace_signature(vector_records, vector_fields),
            "in_memory_pair_trace_signature": trace_signature(pair_rows, pair_fields)}


def edge_clip_audit(objects: list[dict[str, Any]], components: list[dict[str, Any]], page_w: int, page_h: int) -> tuple[list[dict[str, Any]], int]:
    fig_px = rectpx(FIG_RECT, page_w, page_h)
    rows: list[dict[str, Any]] = []
    everything: list[tuple[str, str, MaskRef]] = [(o["id"], "TEXT", o["mask"]) for o in objects]
    everything += [(c["id"], c["kind"], c["visible"]) for c in components if c["kind"] != "HALO_BACKGROUND"]
    clips = 0
    for eid, category, m in everything:
        bx = m.bbox
        page_dist = min(bx[0], bx[1], page_w-bx[2], page_h-bx[3])
        fig_dist = min(bx[0]-fig_px[0], bx[1]-fig_px[1], fig_px[2]-bx[2], fig_px[3]-bx[3])
        touch = int(m.area > 0 and (bx[0] == 0 or bx[1] == 0 or bx[2] == page_w or bx[3] == page_h))
        clip = touch
        clips += clip
        minimum = 6 if category == "TEXT" else 0
        rows.append({"ELEMENT_ID": eid, "CATEGORY": category, "BBOX_PX": json.dumps(pxrect_to_list(bx)),
                     "PAGE_EDGE_DISTANCE_PX": page_dist, "FIGURE_CROP_EDGE_DISTANCE_PX": fig_dist,
                     "MIN_REQUIRED_TEXT_EDGE_PX": minimum, "TOUCH_PAGE_BOUNDARY": touch,
                     "CLIP_PIXEL_COUNT": clip, "PASS_FAIL": "PASS" if not clip and (category != "TEXT" or fig_dist >= 6) else "FAIL"})
    return rows, clips


def fill_object_pair_metrics(glyphs: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> None:
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for p in pair_rows:
        by_parent.setdefault(p["A_ID"], []).append(p)
        if p["pair_type"] == "TEXT_TEXT":
            by_parent.setdefault(p["B_ID"], []).append(p)
    for g in glyphs:
        ps = by_parent.get(g["PARENT_ELEMENT_ID"], [])
        tt = sum(p["OVERLAP_PIXEL_COUNT"] for p in ps if p["pair_type"] == "TEXT_TEXT")
        tg = sum(p["OVERLAP_PIXEL_COUNT"] for p in ps if p["pair_type"] != "TEXT_TEXT")
        clear = min((float(p["CLEARANCE_PX"]) for p in ps if math.isfinite(float(p["CLEARANCE_PX"]))), default=math.inf)
        g["TEXT_TEXT_OVERLAP_PX"] = tt
        g["TEXT_GRAPHIC_OVERLAP_PX"] = tg
        g["MIN_CLEARANCE_PX"] = round(clear, 3) if math.isfinite(clear) else "INF"


def final_pixel_rows(glyphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for g in glyphs:
        height_ok = g["H_INK_PX"] >= g["MIN_REQUIRED_PX"]
        ratio_ok = bool(g.get("SAME_CLASS_PASS", False))
        role_value = g.get("ROLE_RATIO", "N/A")
        role_ok = role_value == "N/A" or isinstance(role_value, (int, float))
        no_overlap = g["TEXT_TEXT_OVERLAP_PX"] == 0 and g["TEXT_GRAPHIC_OVERLAP_PX"] == 0
        reasons = []
        if not height_ok:
            reasons.append(f"H_ink={g['H_INK_PX']}<{g['MIN_REQUIRED_PX']}({g['SCRIPT_CLASS']})")
        if not ratio_ok:
            reasons.append("same_panel_role_script_ratio")
        if not no_overlap:
            reasons.append("illegal_overlap")
        g["PIXEL_HEIGHT_PASS"] = height_ok
        g["PASS_FAIL"] = "PASS" if height_ok and ratio_ok and no_overlap else "FAIL"
        g["REASON"] = ";".join(reasons)
        out = {k: v for k, v in g.items() if k not in ("raw_mask",)}
        rows.append(out)
    return rows


def make_semantics() -> dict[str, Any]:
    simple = [[0.0, 1.0, 0.0], [0.5, 0.0, 0.5], [0.0, 1.0, 0.0]]
    lazy = [[0.5, 0.5, 0.0], [0.25, 0.5, 0.25], [0.0, 0.5, 0.5]]
    pi = [0.25, 0.5, 0.25]
    def mul(v: list[float], a: list[list[float]]) -> list[float]:
        return [sum(v[i] * a[i][j] for i in range(3)) for j in range(3)]
    return {
        "figure_id": FIGURE_ID,
        "inputs": {"source": source_rel(SOURCE), "body": source_rel(BODY), "pdf": str(PDF),
                   "physical_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE},
        "source_graph_transitions": {"simple": simple, "lazy": lazy},
        "claimed_stationary_distribution": pi,
        "stationary_check_simple": mul(pi, simple),
        "stationary_check_lazy": mul(pi, lazy),
        "stationary_distribution_preserved": True,
        "irreducible": True,
        "period_simple": 2,
        "period_lazy": 1,
        "body_consistency": {
            "body_lines": [694, 701, 725, 727, 728],
            "body_assertions": ["connected path is irreducible", "unlooped bipartite path has period 2",
                                "A_L=1/2(I+A) adds self-loops and preserves stationary distribution",
                                "figure should show stationary pi=(1/4,1/2,1/4) and removal of periodicity"],
            "graph_and_caption_consistent": True
        },
        "curve_check": {
            "simple_displayed_p2_t0_to8": [0.75, 0.25, 0.75, 0.25, 0.75, 0.25, 0.75, 0.25, 0.75],
            "lazy_displayed_p2_t0_to8": [0.75, 0.375, 0.5625, 0.46875, 0.5156, 0.4922, 0.5039, 0.4980, 0.5010],
            "lazy_graph_implication": "For every probability row vector mu, (mu A_L)_2 = 1/2*mu_1 + 1/2*mu_2 + 1/2*mu_3 = 1/2.",
            "required_lazy_p2_t_ge_1": 0.5,
            "first_contradictory_displayed_point": {"t": 1, "displayed": 0.375, "required": 0.5},
            "curve_matches_drawn_lazy_chain": False,
            "initial_distribution_declared_in_figure_or_body": False,
            "simple_curve_qualitative_alternation": True,
            "verdict": "FAIL: the right plot is not generated by the displayed lazy three-node path; the starting distribution is also unstated."
        },
        "MATH_SEMANTICS_PASS": False,
        "TEXT_CONSISTENCY_PASS": False
    }


def write_reports(metrics: dict[str, Any], objects: list[dict[str, Any]], critical: list[dict[str, Any]],
                  semantics: dict[str, Any]) -> None:
    b = lambda x: "true" if x else "false"
    critical_lines = "\n".join(f"- `{r['PAIR_ID']}` — {r['STATUS']}; final overlap={r['OVERLAP_PIXEL_COUNT']}; pre-occlusion={r['PRE_OCCLUSION_OVERLAP_PX']}; clearance={r['CLEARANCE_PX']} px; 8× `{r['nn8x']}`" for r in critical) or "- 无临界/失败 pair（仍已完成全对 CSV）。"
    report = f"""# {FIGURE_ID}｜独立 SA1 严格视觉与数学首审（{REVIEW_ID}）

## 1. 范围、冻结输入与定位

- 冻结输入：`{PDF}`；直接定位为 PDF 物理页 **{PHYSICAL_PAGE}**（PyMuPDF index {PDF_PAGE_INDEX}）、印刷页 **{PRINTED_PAGE}**，题注为“图30.7 三节点路径的简单游走与惰性游走：加入自环保持平稳分布并消除周期振荡”。
- 只读取当前图源 `{source_rel(SOURCE)}`、相邻正文 `{source_rel(BODY)}` 和公共样式 `{source_rel(STYLE)}`；未读取本图任何旧 SA/根结论、截图或测量。
- 300 dpi 测量来自一次性直接渲染整页 `{metrics['full_page_px'][0]}×{metrics['full_page_px'][1]}` 固定网格；所有局部图均为该网格的像素切片、未 resize。

## 2. 源级有效字号

- 源级对象 {metrics['object_count']} 个；`effective_pt<9.5` 的读者对象 **{metrics['source_font_fail_count']}** 个。具体为状态标签 9.4pt、边/自环概率 8.8pt、刻度 8.6pt、轴标题/公式基准 9.2pt、注释 8.8pt、摘要 9.2pt；详见 `after_font_audit.csv`。
- 同面板同角色源级字号一致性与跨面板同角色比均已记录；它们不能抵消 9.5pt 硬下限失败。
- `SOURCE_FONT_PASS = {b(metrics['SOURCE_FONT_PASS'])}`。

## 3. 原生 300dpi 逐字形测量

- 已枚举 {metrics['glyph_count']} 个 PDF 字形/字面运算符/标点；每一项有 PDF bbox、无膨胀 raw mask、H_ink 与类别阈值，见 `after_pixel_measurements.csv` 与 `masks/glyph_raw/`。
- `PIXEL_HEIGHT_PASS = {b(metrics['PIXEL_HEIGHT_PASS'])}`；逐字形高度失败 **{metrics['pixel_height_fail_count']}** 个。父公式或中文行高未替代任何数字、`/`、`=`、逗号/句点等子串。
- 图中文字测量框在 `after_text_measurement_overlay_300dpi.png`；自然题注作为单一父段 `CAPTION`，未人为拆行为文字—文字碰撞对象。

## 4. 同类比例、角色层级与字体协调

- 每个字形仍单独做 C 节 H_ink 门；D/E 的比例单位为“同一语义父对象 × 同一 script class”的实际 raw mask H_ink，因此不会把自然题注/标题拆成单字制造伪比例，也未按 exact glyph 分组或跨脚本混比。跨面板同角色同脚本的实际中位数另列，见 `same_class_ratio_audit.csv`/`role_ratio_audit.csv`。
- `SAME_CLASS_RATIO_PASS = {b(metrics['SAME_CLASS_RATIO_PASS'])}`；失败行 **{metrics['same_class_fail_count']}**。`ROLE_RATIO_PASS = {b(metrics['ROLE_RATIO_PASS'])}`；失败行 **{metrics['role_ratio_fail_count']}**。无可比 script 的角色层级明示 `N/A`，未伪造跨脚本比例。
- `FONT_VISUAL_HARMONY_PASS = {b(metrics['FONT_VISUAL_HARMONY_PASS'])}`：刻度、边标签与注释的 8.6–8.8pt 明显低于此图其他文本的教学阅读基准；本轮未以“可读”或缩小建议覆盖硬门。

## 5. 零重叠、净空、halo 与裁切

- 已枚举 **{metrics['vector_count']}** 条当前图非文字矢量路径，其中 **{metrics['halo_count']}** 条是明确白底 halo，另 **{metrics['visible_vector_count']}** 条为曲线、标记、节点边框、箭头、箭头头、轴或摘要框；全部独立 raw mask 与最终可见 mask 位于 `masks/vector_raw/`、`masks/vector_visible_raw/`、`masks/halo_raw/`。
- `VECTOR_PAIR_TRACEABILITY_PASS = {b(metrics['VECTOR_PAIR_TRACEABILITY_PASS'])}`：`vector_pair_traceability.json` 已逐行核对 `VECTOR_ID/DRAWING_INDEX/CATEGORY/OWNER/raw/final-visible mask` 与内存 components，并核对所有 pair 的 `B_CATEGORY/THRESHOLD_PX`；halo=13、非halo=63、unknown=0。
- 全对数 **{metrics['pair_count']}**；最终非法重叠为 **{metrics['overlap_fail_pair_count']} 对 / {metrics['OVERLAP_PIXEL_COUNT']} 像素**，`CLIP_PIXEL_COUNT = {metrics['CLIP_PIXEL_COUNT']}`；另有 **{metrics['clearance_fail_pair_count']} 对**虽经 halo 已无最终交集但仅 1px 净空。最小实测 pair 净空 **{metrics['MIN_CLEARANCE_PX']} px**。halo 前遮挡量单独列 `PRE_OCCLUSION_OVERLAP_PX`，不混入最终非法重叠。
- `OVERLAP_PASS = {b(metrics['OVERLAP_PASS'])}`；`CLIP_PASS = {b(metrics['CLIP_PASS'])}`；`CLEARANCE_PASS = {b(metrics['CLEARANCE_PASS'])}`。所有失败/临界或 halo 接触 pair 均有原图、双方 raw mask、交集、overlay 和 8× 最近邻版本（文件索引：`critical_pair_manifest.md`）：
{critical_lines}

## 6. 数学、图文与阅读语义

- 上部 simple 图的边概率是三节点路径随机游走；lazy 图等于 `A_L=1/2(I+A)`，两者的 `π=(1/4,1/2,1/4)` 均为平稳分布，simple 周期 2、lazy 周期 1，和相邻正文第30章相符。
- 但右下曲线与右上惰性链不相容：对任意分布 `mu`，`(mu A_L)_2 = 1/2`，故从 t=1 起 `P(X_t=2)` 必恒为 0.5；图中 t=1 标为 0.375，继而画出阻尼振荡。初始分布也未声明。该量化数据/图内命题错误详见 `math_text_semantics_audit.json`。
- `MATH_SEMANTICS_PASS = false`；`TEXT_CONSISTENCY_PASS = false`。阅读顺序（上：链；下：曲线；末：摘要/题注）本身清晰，但不能修复上述数学矛盾。

## 7. 四视图、灰度与页面融合

- 已核看 `full_page_200dpi.png`、`full_page_300dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`。上下结构和曲线/虚线/点型在灰度中仍可分辨；页面嵌入与题注自然。
- `GRAYSCALE_PASS = true`，`READING_ORDER_PASS = true`，`PAGE_INTEGRATION_PASS = true`。它们不覆盖字号与数学硬失败。

## 8. 结论与路由

```
RESULT: FAIL
FIGURE_ID: {FIGURE_ID}
SOURCE_FONT_PASS: {b(metrics['SOURCE_FONT_PASS'])}
PIXEL_HEIGHT_PASS: {b(metrics['PIXEL_HEIGHT_PASS'])}
SAME_CLASS_RATIO_PASS: {b(metrics['SAME_CLASS_RATIO_PASS'])}
ROLE_RATIO_PASS: {b(metrics['ROLE_RATIO_PASS'])}
FONT_VISUAL_HARMONY_PASS: {b(metrics['FONT_VISUAL_HARMONY_PASS'])}
OVERLAP_PIXEL_COUNT: {metrics['OVERLAP_PIXEL_COUNT']}
OVERLAP_FAIL_PAIR_COUNT: {metrics['overlap_fail_pair_count']}
CLIP_PIXEL_COUNT: {metrics['CLIP_PIXEL_COUNT']}
VECTOR_PAIR_TRACEABILITY_PASS: {b(metrics['VECTOR_PAIR_TRACEABILITY_PASS'])}
MATH_SEMANTICS_PASS: false
TEXT_CONSISTENCY_PASS: false
EVIDENCE_INTEGRITY_PASS: {b(metrics['EVIDENCE_INTEGRITY_PASS'])}
NEXT_ROLE: SA2
```

SA2 应先修正惰性链曲线（或改变所画链/明确初始条件使数据可由转移矩阵推得），再将所有普通可见文字提高至至少 9.5pt，同时重新安排以通过逐字形、比例和净空门；不得仅整体缩放。
"""
    (OUT / "SA1_STRICT_R1_REPORT.md").write_text(report, encoding="utf-8")
    visual = f"""# {FIGURE_ID} after visual acceptance — {REVIEW_ID}

Frozen PDF: physical page {PHYSICAL_PAGE}, printed page {PRINTED_PAGE}; all metrics use the direct 300dpi full-page fixed grid.

SOURCE_FONT_PASS = {b(metrics['SOURCE_FONT_PASS'])}
PIXEL_HEIGHT_PASS = {b(metrics['PIXEL_HEIGHT_PASS'])}
SAME_CLASS_RATIO_PASS = {b(metrics['SAME_CLASS_RATIO_PASS'])}
ROLE_RATIO_PASS = {b(metrics['ROLE_RATIO_PASS'])}
FONT_VISUAL_HARMONY_PASS = {b(metrics['FONT_VISUAL_HARMONY_PASS'])}
OVERLAP_PIXEL_COUNT = {metrics['OVERLAP_PIXEL_COUNT']}
OVERLAP_FAIL_PAIR_COUNT = {metrics['overlap_fail_pair_count']}
CLIP_PIXEL_COUNT = {metrics['CLIP_PIXEL_COUNT']}
VECTOR_PAIR_TRACEABILITY_PASS = {b(metrics['VECTOR_PAIR_TRACEABILITY_PASS'])}
MIN_TEXT_CLEARANCE_PX = {metrics['MIN_CLEARANCE_PX']}
OVERLAP_PASS = {b(metrics['OVERLAP_PASS'])}
CLIP_PASS = {b(metrics['CLIP_PASS'])}
CLEARANCE_PASS = {b(metrics['CLEARANCE_PASS'])}
MATH_SEMANTICS_PASS = false
TEXT_CONSISTENCY_PASS = false
GRAYSCALE_PASS = true
READING_ORDER_PASS = true
PAGE_INTEGRATION_PASS = true
EVIDENCE_INTEGRITY_PASS = {b(metrics['EVIDENCE_INTEGRITY_PASS'])}

FONT_VISUAL_HARMONY rationale: false. The only permission to reduce text would require >=9.5pt plus all pixel/ratio/clearance/page gates; this frozen candidate has 8.6–9.4pt reader text and therefore cannot claim that exception.

RESULT = FAIL
NEXT_ROLE = SA2
"""
    (OUT / "after_visual_acceptance.md").write_text(visual, encoding="utf-8")


def report_integrity(metrics: dict[str, Any]) -> dict[str, Any]:
    required = ["full_page_200dpi.png", "full_page_300dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png",
                "after_font_audit.csv", "after_pixel_measurements.csv", "same_class_ratio_audit.csv", "role_ratio_audit.csv",
                "after_overlap_report.csv", "after_edge_clip_report.csv", "after_text_measurement_overlay_300dpi.png",
                "after_visual_acceptance.md", "SA1_STRICT_R1_REPORT.md", "vector_component_inventory.csv", "math_text_semantics_audit.json",
                "measurement_consistency.json", "audit_metrics.json", "critical_pair_index.csv", "critical_pair_manifest.md",
                "vector_pair_traceability.json"]
    missing = [x for x in required if not (OUT / x).is_file()]
    required_dirs = ["masks/glyph_raw", "masks/text_raw", "masks/vector_raw", "masks/vector_visible_raw", "masks/halo_raw", "critical_pairs"]
    empty_dirs = [x for x in required_dirs if not any((OUT / x).iterdir())]
    def exists_rel(value: str) -> bool:
        return bool(value) and (OUT / value).is_file()
    pixel_rows = list(csv.DictReader((OUT / "after_pixel_measurements.csv").open(encoding="utf-8-sig")))
    font_rows = list(csv.DictReader((OUT / "after_font_audit.csv").open(encoding="utf-8-sig")))
    same_rows = list(csv.DictReader((OUT / "same_class_ratio_audit.csv").open(encoding="utf-8-sig")))
    role_rows = list(csv.DictReader((OUT / "role_ratio_audit.csv").open(encoding="utf-8-sig")))
    overlap_rows = list(csv.DictReader((OUT / "after_overlap_report.csv").open(encoding="utf-8-sig")))
    edge_rows = list(csv.DictReader((OUT / "after_edge_clip_report.csv").open(encoding="utf-8-sig")))
    vector_rows = list(csv.DictReader((OUT / "vector_component_inventory.csv").open(encoding="utf-8-sig")))
    critical_rows = list(csv.DictReader((OUT / "critical_pair_index.csv").open(encoding="utf-8-sig")))
    trace = json.loads((OUT / "vector_pair_traceability.json").read_text(encoding="utf-8"))
    glyph_masks_complete = bool(pixel_rows) and all(exists_rel(r["MASK_PATH"]) for r in pixel_rows)
    vector_masks_complete = bool(vector_rows) and all(exists_rel(r["RAW_MASK"]) and exists_rel(r["FINAL_VISIBLE_MASK"]) for r in vector_rows)
    critical_fields = ("raw_roi", "a_mask", "b_mask", "intersection", "overlay", "nn8x")
    critical_evidence_complete = bool(critical_rows) and all(all(exists_rel(r[k]) for k in critical_fields) for r in critical_rows)
    vector_fields = ("VECTOR_ID", "DRAWING_INDEX", "CATEGORY", "OWNER", "RAW_MASK", "FINAL_VISIBLE_MASK")
    pair_fields = ("pair_id", "pair_type", "A_ID", "B_ID", "B_CATEGORY", "THRESHOLD_PX")
    vector_csv_traceability = trace.get("in_memory_inventory_signature") == trace_signature(vector_rows, vector_fields)
    pair_csv_traceability = trace.get("in_memory_pair_trace_signature") == trace_signature(overlap_rows, pair_fields)
    vector_pair_memory_traceability = bool(trace.get("pass")) and trace.get("HALO_BACKGROUND_COUNT") == 13 and trace.get("NONHALO_FINAL_VISIBLE_COUNT") == 63 and trace.get("UNKNOWN_VECTOR_COUNT") == 0 and trace.get("TOTAL_PAIR_COUNT") == 3612
    metrics_csv_consistency = (
        len(pixel_rows) == metrics["glyph_count"] and
        sum(r["PASS_FAIL"] == "FAIL" for r in font_rows) == metrics["source_font_fail_count"] and
        sum(r["PIXEL_HEIGHT_PASS"] == "False" for r in pixel_rows) == metrics["pixel_height_fail_count"] and
        sum(r["PASS_FAIL"] == "FAIL" for r in same_rows) == metrics["same_class_fail_count"] and
        sum(r["PASS_FAIL"] == "FAIL" for r in role_rows) == metrics["role_ratio_fail_count"] and
        len(overlap_rows) == metrics["pair_count"] and
        sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in overlap_rows) == metrics["OVERLAP_PIXEL_COUNT"] and
        sum(r["PASS_FAIL"] == "FAIL_OVERLAP" for r in overlap_rows) == metrics["overlap_fail_pair_count"] and
        sum(r["PASS_FAIL"] == "FAIL_CLEARANCE" for r in overlap_rows) == metrics["clearance_fail_pair_count"] and
        sum(int(r["CLIP_PIXEL_COUNT"]) for r in edge_rows) == metrics["CLIP_PIXEL_COUNT"] and
        len(critical_rows) == metrics["critical_pair_count"] and len(vector_rows) == metrics["vector_count"]
    )
    report_text = (OUT / "SA1_STRICT_R1_REPORT.md").read_text(encoding="utf-8")
    visual_text = (OUT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    tokens = [f"OVERLAP_PIXEL_COUNT: {metrics['OVERLAP_PIXEL_COUNT']}",
              f"OVERLAP_FAIL_PAIR_COUNT: {metrics['overlap_fail_pair_count']}",
              f"CLIP_PIXEL_COUNT: {metrics['CLIP_PIXEL_COUNT']}",
              f"VECTOR_PAIR_TRACEABILITY_PASS: {str(metrics['VECTOR_PAIR_TRACEABILITY_PASS']).lower()}", "RESULT: FAIL", "NEXT_ROLE: SA2"]
    report_tokens = all(t in report_text for t in tokens)
    visual_tokens = all(t.replace(":", " =") if False else True for t in tokens)  # marker retained below for explicit checks
    visual_tokens = all(t in visual_text for t in [f"OVERLAP_PIXEL_COUNT = {metrics['OVERLAP_PIXEL_COUNT']}",
                                                    f"OVERLAP_FAIL_PAIR_COUNT = {metrics['overlap_fail_pair_count']}",
                                                    f"CLIP_PIXEL_COUNT = {metrics['CLIP_PIXEL_COUNT']}",
                                                    f"VECTOR_PAIR_TRACEABILITY_PASS = {str(metrics['VECTOR_PAIR_TRACEABILITY_PASS']).lower()}", "RESULT = FAIL", "NEXT_ROLE = SA2"])
    old_tokens = ["187", "189", "SUPERSEDED"]
    legacy_active = [t for t in old_tokens if t in report_text or t in visual_text]
    return {"figure_id": FIGURE_ID, "review_id": REVIEW_ID, "required_artifacts": required,
            "missing_artifacts": missing, "empty_required_dirs": empty_dirs,
            "glyph_masks_complete": glyph_masks_complete, "vector_masks_complete": vector_masks_complete,
            "critical_evidence_complete": critical_evidence_complete, "critical_pair_count": len(critical_rows),
            "metrics_csv_consistency": metrics_csv_consistency,
            "vector_pair_memory_traceability": vector_pair_memory_traceability,
            "vector_inventory_csv_traceability": vector_csv_traceability,
            "pair_csv_traceability": pair_csv_traceability,
            "halo_background_count": trace.get("HALO_BACKGROUND_COUNT"), "nonhalo_final_visible_count": trace.get("NONHALO_FINAL_VISIBLE_COUNT"),
            "unknown_vector_count": trace.get("UNKNOWN_VECTOR_COUNT"),
            "report_numeric_consistency": report_tokens, "visual_numeric_consistency": visual_tokens,
            "legacy_active_tokens": legacy_active, "source_pdf_sha256": sha256(PDF),
            "evidence_integrity_pass": not missing and not empty_dirs and glyph_masks_complete and vector_masks_complete and critical_evidence_complete and metrics_csv_consistency and vector_pair_memory_traceability and vector_csv_traceability and pair_csv_traceability and report_tokens and visual_tokens and not legacy_active}


def main() -> None:
    clear_prior_generated_evidence()
    mkdirs()
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_INDEX]
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    pix200 = page.get_pixmap(matrix=fitz.Matrix(200/72.0, 200/72.0), alpha=False)
    pix300.save(OUT / "full_page_300dpi.png")
    pix200.save(OUT / "full_page_200dpi.png")
    page_rgb = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, 3).copy()
    page_h, page_w = page_rgb.shape[:2]
    figpx = rectpx(FIG_RECT, page_w, page_h)
    bodypx = rectpx(STANDALONE_RECT, page_w, page_h)
    figcrop = page_rgb[figpx[1]:figpx[3], figpx[0]:figpx[2]]
    bodycrop = page_rgb[bodypx[1]:bodypx[3], bodypx[0]:bodypx[2]]
    Image.fromarray(figcrop, mode="RGB").save(OUT / "figure_crop_300dpi.png")
    Image.fromarray(bodycrop, mode="RGB").save(OUT / "standalone_300dpi.png")
    Image.fromarray(figcrop, mode="RGB").convert("L").save(OUT / "grayscale_300dpi.png")
    stable_json(OUT / "render_provenance.json", {
        "frozen_pdf": str(PDF), "pdf_sha256": sha256(PDF), "physical_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE,
        "direct_page_render_dpi": DPI, "rendered_page_px": [page_w, page_h], "scale": SCALE,
        "figure_crop_pdf_pt": list(FIG_RECT), "figure_crop_px": list(figpx), "standalone_crop_pdf_pt": list(STANDALONE_RECT),
        "standalone_crop_px": list(bodypx), "no_resize_after_direct_render": True,
        "method": "full page direct PDF raster at 300dpi; all 300dpi crops are pixel slices"})

    objects = make_objects()
    glyphs, unassigned = get_chardata(page, objects, page_w, page_h, page_rgb)
    add_overlay(figcrop, objects, (figpx[0], figpx[1]))
    source_rows, source_ratio_rows = classify_source_fonts(objects)
    same_rows, same_pass, ratio_components = compute_class_ratios(glyphs)
    cross_rows, cross_pass = compute_cross_panel_ratios(ratio_components)
    role_rows, role_pass = assign_role_ratios(ratio_components)
    components, vector_inventory = build_vector_components(page, page_w, page_h)
    pair_rows, critical_index, overlap_count, min_clear = pair_audits(objects, components, page_rgb, page_w, page_h)
    vector_pair_trace = validate_vector_inventory_and_pair_traceability(components, vector_inventory, objects, pair_rows)
    edge_rows, clip_count = edge_clip_audit(objects, components, page_w, page_h)
    fill_object_pair_metrics(glyphs, pair_rows)
    pixel_rows = final_pixel_rows(glyphs)
    semantics = make_semantics()

    write_csv(OUT / "after_font_audit.csv", source_rows)
    write_csv(OUT / "after_pixel_measurements.csv", pixel_rows)
    write_csv(OUT / "same_class_ratio_audit.csv", same_rows)
    write_csv(OUT / "role_ratio_audit.csv", source_ratio_rows + cross_rows + role_rows)
    write_csv(OUT / "after_overlap_report.csv", pair_rows)
    write_csv(OUT / "after_edge_clip_report.csv", edge_rows)
    write_csv(OUT / "vector_component_inventory.csv", vector_inventory)
    stable_json(OUT / "vector_pair_traceability.json", vector_pair_trace)
    write_csv(OUT / "critical_pair_index.csv", critical_index, fields=["PAIR_ID", "STATUS", "OVERLAP_PIXEL_COUNT", "PRE_OCCLUSION_OVERLAP_PX", "CLEARANCE_PX", "roi_bbox_px", "raw_roi", "a_mask", "b_mask", "intersection", "overlay", "nn8x", "PRE_OCCLUSION_B_MASK"])
    (OUT / "critical_pair_manifest.md").write_text(
        "# FIG-P558-01 critical / failed pair manifest\n\n"
        "All paths are final frozen-PDF 300dpi evidence. `8xNN` is only an inspection enlargement; metrics use the native grid.\n\n" +
        "\n".join(
            f"- `{r['PAIR_ID']}` | {r['STATUS']} | final={r['OVERLAP_PIXEL_COUNT']} px | pre-halo={r['PRE_OCCLUSION_OVERLAP_PX']} px | clearance={r['CLEARANCE_PX']} px\n"
            f"  - raw `{r['raw_roi']}`; A `{r['a_mask']}`; B `{r['b_mask']}`; intersection `{r['intersection']}`; overlay `{r['overlay']}`; 8xNN `{r['nn8x']}`"
            for r in critical_index) + "\n", encoding="utf-8")
    stable_json(OUT / "math_text_semantics_audit.json", semantics)
    stable_json(OUT / "element_bbox_map.json", {"objects": [{"id": o["id"], "role": o["role"], "panel": o["panel"],
        "pdf_bbox": list(o["rect_pdf"]), "pixel_bbox": list(o["bbox_px"]), "mask": o["mask_info"]} for o in objects],
        "coverage_unassigned": unassigned, "glyph_count": len(glyphs)})
    stable_json(OUT / "halo_coverage_manifest.json", {"rule": "final visible vector mask = independent vector raw mask minus only later opaque white halo paths; raw pre-occlusion is preserved",
        "halos": [{"id": c["id"], "drawing_index": c["drawing_index"], "seqno": c["seqno"], "mask": c["raw_info"]} for c in components if c["kind"] == "HALO_BACKGROUND"],
        "pre_occlusion_pair_count": sum(1 for p in pair_rows if p["PRE_OCCLUSION_OVERLAP_PX"] > 0),
        "pre_occlusion_pixel_pair_sum": sum(int(p["PRE_OCCLUSION_OVERLAP_PX"]) for p in pair_rows)})
    stable_json(OUT / "measurement_consistency.json", {"measurement_basis": "actual raw H_ink_px from final full-page native 300dpi grid; no pt/PDF proxy used for D/E",
        "threshold_delta_rgb": 20, "no_dilation": True, "glyph_count": len(glyphs), "unassigned_glyphs": unassigned,
        "source_font_rows": len(source_rows), "same_class_rows": len(same_rows), "ratio_component_count": len(ratio_components),
        "ratio_unit": "semantic parent object × script class, derived from actual raw glyph masks; not exact glyph / not cross-script",
        "role_ratio_rows": len(source_ratio_rows)+len(cross_rows)+len(role_rows),
        "overlap_rows": len(pair_rows), "vector_components": len(components), "critical_pairs": len(critical_index),
        "vector_pair_traceability": {k: vector_pair_trace[k] for k in ("pass", "HALO_BACKGROUND_COUNT", "NONHALO_FINAL_VISIBLE_COUNT", "UNKNOWN_VECTOR_COUNT", "TEXT_TEXT_PAIR_COUNT", "TEXT_VECTOR_PAIR_COUNT", "TOTAL_PAIR_COUNT")}})

    pixel_fail = sum(1 for r in pixel_rows if not r["PIXEL_HEIGHT_PASS"])
    same_fail = sum(1 for r in same_rows if r["PASS_FAIL"] == "FAIL")
    role_fail = sum(1 for r in role_rows if r["PASS_FAIL"] == "FAIL") + sum(1 for r in cross_rows if r["PASS_FAIL"] == "FAIL")
    source_fail = sum(1 for r in source_rows if r["PASS_FAIL"] == "FAIL")
    clearance_fail = sum(1 for p in pair_rows if p["PASS_FAIL"] == "FAIL_CLEARANCE")
    overlap_fail_pairs = sum(1 for p in pair_rows if p["PASS_FAIL"] == "FAIL_OVERLAP")
    metrics = {"figure_id": FIGURE_ID, "review_id": REVIEW_ID, "physical_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE,
               "full_page_px": [page_w, page_h], "object_count": len(objects), "glyph_count": len(glyphs), "vector_count": len(components),
               "halo_count": sum(1 for c in components if c["kind"] == "HALO_BACKGROUND"),
               "visible_vector_count": sum(1 for c in components if c["kind"] != "HALO_BACKGROUND"), "pair_count": len(pair_rows),
               "critical_pair_count": len(critical_index), "unassigned_glyph_count": len(unassigned), "source_font_fail_count": source_fail,
               "pixel_height_fail_count": pixel_fail, "same_class_fail_count": same_fail, "role_ratio_fail_count": role_fail,
               "clearance_fail_pair_count": clearance_fail, "overlap_fail_pair_count": overlap_fail_pairs,
               "SOURCE_FONT_PASS": source_fail == 0 and len(unassigned) == 0, "PIXEL_HEIGHT_PASS": pixel_fail == 0 and len(unassigned) == 0,
               "SAME_CLASS_RATIO_PASS": same_pass and cross_pass, "ROLE_RATIO_PASS": role_pass,
               "OVERLAP_PIXEL_COUNT": overlap_count, "CLIP_PIXEL_COUNT": clip_count,
               "MIN_CLEARANCE_PX": round(min_clear, 3) if math.isfinite(min_clear) else "INF",
               "OVERLAP_PASS": overlap_count == 0, "CLIP_PASS": clip_count == 0,
               "CLEARANCE_PASS": clearance_fail == 0 and overlap_count == 0, "FONT_VISUAL_HARMONY_PASS": False,
               "MATH_SEMANTICS_PASS": False, "TEXT_CONSISTENCY_PASS": False,
               "GRAYSCALE_PASS": True, "READING_ORDER_PASS": True, "PAGE_INTEGRATION_PASS": True,
               "VECTOR_PAIR_TRACEABILITY_PASS": bool(vector_pair_trace["pass"]), "ALL_HARD_GATES_PASS": False}
    # First write reports with a provisional evidence-integrity true; immediately replace with the machine result.
    metrics["EVIDENCE_INTEGRITY_PASS"] = True
    stable_json(OUT / "audit_metrics.json", metrics)
    write_reports(metrics, objects, critical_index, semantics)
    integrity = report_integrity(metrics)
    metrics["EVIDENCE_INTEGRITY_PASS"] = bool(integrity["evidence_integrity_pass"])
    stable_json(OUT / "audit_metrics.json", metrics)
    write_reports(metrics, objects, critical_index, semantics)
    integrity = report_integrity(metrics)
    stable_json(OUT / "final_consistency_check.json", integrity)
    (OUT / "final_consistency_check.md").write_text(
        f"# {FIGURE_ID} machine final consistency\n\n"
        f"- required artifacts present: `{not integrity['missing_artifacts']}`\n"
        f"- required mask directories nonempty: `{not integrity['empty_required_dirs']}`\n"
        f"- every glyph mask referenced and present: `{integrity['glyph_masks_complete']}`\n"
        f"- every vector raw/final-visible mask referenced and present: `{integrity['vector_masks_complete']}`\n"
        f"- all {integrity['critical_pair_count']} critical pairs include raw/A/B/intersection/overlay/8×NN: `{integrity['critical_evidence_complete']}`\n"
        f"- metrics ↔ CSV row/count/total consistency: `{integrity['metrics_csv_consistency']}`\n"
        f"- memory vector inventory / pair trace (halo={integrity['halo_background_count']}, nonhalo={integrity['nonhalo_final_visible_count']}, unknown={integrity['unknown_vector_count']}): `{integrity['vector_pair_memory_traceability']}`\n"
        f"- emitted inventory CSV mapping signature: `{integrity['vector_inventory_csv_traceability']}`\n"
        f"- emitted pair B_CATEGORY/threshold signature: `{integrity['pair_csv_traceability']}`\n"
        f"- report metrics tokens consistent: `{integrity['report_numeric_consistency']}`\n"
        f"- acceptance metrics tokens consistent: `{integrity['visual_numeric_consistency']}`\n"
        f"- legacy active tokens absent: `{not integrity['legacy_active_tokens']}`\n"
        f"- EVIDENCE_INTEGRITY_PASS: `{integrity['evidence_integrity_pass']}`\n", encoding="utf-8")
    doc.close()
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
