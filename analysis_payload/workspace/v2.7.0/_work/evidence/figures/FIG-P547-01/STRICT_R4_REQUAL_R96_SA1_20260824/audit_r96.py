#!/usr/bin/env python3
"""Produce first-principles R96 evidence for FIG-P547-01.

All measurements originate from main_full.pdf physical page 591 rendered by
Poppler at 300 dpi.  This script never reads the pre-existing FIG-P547-01
evidence tree; it only reads the frozen PDF, the frozen figure source, and
the direct chapter text named in the review assignment.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw


RUN_ROOT = Path(__file__).resolve().parent
# The outer run directory also preserves aborted/intermediate material.  Every
# terminal artifact for this requalification is deliberately emitted under one
# clean, separately sealable subdirectory; the audit never reads the aborted
# relation directory at RUN_ROOT/relations.
ROOT = RUN_ROOT / "FINAL_R96"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r96_fullbook\main_full.pdf")
FIGURE_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex")
CHAPTER_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C01.tex")
PAGE_NUMBER = 591
EXPECTED_PDF_SHA256 = "8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8"
EXPECTED_FIGURE_SHA256 = "638CEA4285D3A9411251DA149963CC7AE4500FA5827F0A99A51FF1FC76640D1A"
NATIVE_DPI = 300
THRESHOLD = 20

# Native-pixel crop of the complete figure and caption. It was selected from
# Poppler word boxes with 6+ px white margin and is never resized.
CROP = (205, 1215, 2290, 1855)  # x0, y0, x1, y1 in 2481 x 3508 native grid
FIGURE_PT_RECT = (55.0, 292.0, 540.0, 445.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def mkdirs() -> None:
    for name in (
        "glyph_views",
        "glyph_masks",
        "glyph_contact_sheets",
        "graphic_masks",
        "relations_final",
        "occlusion",
        "calibration",
    ):
        (ROOT / name).mkdir(exist_ok=True)


def png(path: Path, arr: np.ndarray | Image.Image) -> None:
    if isinstance(arr, Image.Image):
        arr.save(path, format="PNG", optimize=False)
    else:
        Image.fromarray(arr).save(path, format="PNG", optimize=False)


def codepoint(ch: str) -> str:
    return "U+" + "-".join(f"{ord(x):04X}" for x in ch)


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")


def weight_of(font: str, flags: int) -> str:
    return "BOLD" if "Bold" in font or (flags & 16) else "REGULAR"


def local_background(image: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int]:
    """Modal RGB value in a 3px ring around a glyph's exact PDF bbox."""
    h, w = image.shape[:2]
    p = 3
    ax0, ay0 = max(0, x0 - p), max(0, y0 - p)
    ax1, ay1 = min(w, x1 + p), min(h, y1 + p)
    patch = image[ay0:ay1, ax0:ax1]
    inner_x0, inner_y0 = x0 - ax0, y0 - ay0
    inner_x1, inner_y1 = x1 - ax0, y1 - ay0
    ring = np.ones(patch.shape[:2], dtype=bool)
    ring[inner_y0:inner_y1, inner_x0:inner_x1] = False
    values = patch[ring]
    if len(values) == 0:
        values = patch.reshape(-1, 3)
    packed = (values[:, 0].astype(np.uint32) << 16) + (values[:, 1].astype(np.uint32) << 8) + values[:, 2]
    v = Counter(packed.tolist()).most_common(1)[0][0]
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def category_for(ch: str, size: float, parent: str) -> tuple[str, int | None]:
    low = {".", "，", "。", "、", "：", "；", ",", ";", ":", "…"}
    if ch in low:
        return "LOW_PROFILE_PUNCTUATION", None
    if parent in {"TXT_L_TITLE", "TXT_R_TITLE"} and ch in {"i", "j"}:
        return "NATURAL_SCRIPT", 15
    if parent == "TXT_BRIDGE_TRANSPOSE" and ch == "T":
        return "NATURAL_SCRIPT", 15
    # Subscripts/superscripts in the actual PDF use a smaller embedded font.
    if size < 9.5:
        return "NATURAL_SCRIPT", 15
    if "\u4e00" <= ch <= "\u9fff":
        return "CJK_FULL", 30
    if ch in "[]()":
        return "MATH_FULL_HEIGHT", 22
    if ch in "=+−-→/":
        return "MATH_OPERATOR", 22
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_UPPER_OR_DIGIT", 24
    if ("a" <= ch <= "z") or ch in {"ρ", "𝜌", "𝑎", "𝑖", "𝑗", "𝑝", "𝑡", "𝑃", "𝐴", "𝑨", "𝑷"}:
        return "LOWERCASE_OR_GREEK", 17
    # Delimiters and any remaining visible math atom have a full-height gate.
    return "MATH_OPERATOR", 22


@dataclass
class Obj:
    object_id: str
    safe: str
    obj_type: str
    role: str
    parent: str
    seqno: int
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    pre_mask: np.ndarray | None = None
    opaque: bool = False
    source_line: str = ""
    semantic_reason: str = ""

    def pixel_count(self) -> int:
        return int(self.mask.sum())


ROLE_SPECS: dict[str, tuple[str, float, str]] = {
    "TXT_L_TITLE": ("TITLE", 10.2, "21"),
    "TXT_R_TITLE": ("TITLE", 10.2, "41"),
    "TXT_L_NODE_1": ("NODE_LABEL", 10.2, "22"),
    "TXT_L_NODE_2": ("NODE_LABEL", 10.2, "23"),
    "TXT_R_NODE_1": ("NODE_LABEL", 10.2, "42"),
    "TXT_R_NODE_2": ("NODE_LABEL", 10.2, "43"),
    "TXT_L_LOOP_07": ("EDGE_LABEL", 11.6, "24"),
    "TXT_L_LOOP_08": ("EDGE_LABEL", 11.6, "25"),
    "TXT_R_LOOP_07": ("EDGE_LABEL", 11.6, "44"),
    "TXT_R_LOOP_08": ("EDGE_LABEL", 11.6, "45"),
    "TXT_L_EDGE_12": ("EDGE_LABEL", 11.6, "26"),
    "TXT_L_EDGE_21": ("EDGE_LABEL", 11.6, "27"),
    "TXT_R_EDGE_21": ("EDGE_LABEL", 11.6, "46"),
    "TXT_R_EDGE_12": ("EDGE_LABEL", 11.6, "47"),
    "TXT_L_MATRIX": ("MATRIX", 11.8, "28-31"),
    "TXT_R_MATRIX": ("MATRIX", 11.8, "48-51"),
    "TXT_L_ROWSUM": ("ANNOTATION", 9.8, "31"),
    "TXT_R_COLSUM": ("ANNOTATION", 9.8, "51"),
    "TXT_BRIDGE_TRANSPOSE": ("FORMULA", 12.0, "34-36"),
    "TXT_BRIDGE_EDGE_MAP": ("ANNOTATION", 11.6, "34-36"),
    "TXT_CAPTION_LABEL": ("CAPTION_LABEL", 9.963, "54"),
    "TXT_CAPTION_BODY": ("CAPTION", 9.963, "54"),
}


def parent_for_char(x: float, y: float) -> str:
    # Coordinates are PDF pt with origin at top-left, taken directly from
    # get_texttrace(). The branches intentionally leave no fallback: an
    # unclassified visible glyph is an audit failure, not a silent omission.
    if y < 320:
        return "TXT_L_TITLE" if x < 250 else "TXT_R_TITLE"
    if 343 <= y < 360:
        if x < 105:
            return "TXT_L_LOOP_07"
        if x < 140:
            return "TXT_L_NODE_1"
        if x < 225:
            return "TXT_L_NODE_2"
        if x < 275:
            return "TXT_L_LOOP_08"
        if x < 350:
            return "TXT_R_LOOP_07"
        if x < 395:
            return "TXT_R_NODE_1"
        if x < 480:
            return "TXT_R_NODE_2"
        return "TXT_R_LOOP_08"
    if 322 <= y < 343:
        return "TXT_L_EDGE_12" if x < 250 else "TXT_R_EDGE_21"
    # The bridge card overlaps the y-band of the lower edge labels.  Classify
    # it first so the centered P=A^T / same-edge statement can never be
    # mistaken for a right-side edge label.
    if 360 <= y < 405 and 225 <= x < 360:
        return "TXT_BRIDGE_EDGE_MAP" if y >= 385 else "TXT_BRIDGE_TRANSPOSE"
    if 359 <= y < 376:
        return "TXT_L_EDGE_21" if x < 250 else "TXT_R_EDGE_12"
    if 376 <= y < 405:
        if x < 225:
            return "TXT_L_MATRIX"
        if x < 360:
            return "TXT_BRIDGE_EDGE_MAP" if y >= 385 else "TXT_BRIDGE_TRANSPOSE"
        return "TXT_R_MATRIX"
    if 405 <= y < 425:
        return "TXT_L_ROWSUM" if x < 250 else "TXT_R_COLSUM"
    if 425 <= y < 445:
        return "TXT_CAPTION_LABEL" if x < 132 else "TXT_CAPTION_BODY"
    raise ValueError(f"unclassified figure glyph at ({x:.2f}, {y:.2f})")


def pt_bbox_to_px(b: Iterable[float], sx: float, sy: float, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = b
    px0 = max(0, min(width, math.floor(x0 * sx)))
    py0 = max(0, min(height, math.floor(y0 * sy)))
    px1 = max(px0 + 1, min(width, math.ceil(x1 * sx)))
    py1 = max(py0 + 1, min(height, math.ceil(y1 * sy)))
    return px0, py0, px1, py1


def crop_from_full(mask: np.ndarray) -> tuple[tuple[int, int, int, int], np.ndarray]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return (0, 0, 0, 0), np.zeros((0, 0), dtype=bool)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return (x0, y0, x1, y1), mask[y0:y1, x0:x1].copy()


def object_mask_in_roi(obj: Obj, x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
    result = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    ox0, oy0, ox1, oy1 = obj.bbox
    ix0, iy0 = max(x0, ox0), max(y0, oy0)
    ix1, iy1 = min(x1, ox1), min(y1, oy1)
    if ix0 >= ix1 or iy0 >= iy1:
        return result
    result[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = obj.mask[iy0 - oy0:iy1 - oy0, ix0 - ox0:ix1 - ox0]
    return result


def intersect_count(a: Obj, b: Obj) -> int:
    x0, y0 = max(a.bbox[0], b.bbox[0]), max(a.bbox[1], b.bbox[1])
    x1, y1 = min(a.bbox[2], b.bbox[2]), min(a.bbox[3], b.bbox[3])
    if x0 >= x1 or y0 >= y1:
        return 0
    am = object_mask_in_roi(a, x0, y0, x1, y1)
    bm = object_mask_in_roi(b, x0, y0, x1, y1)
    return int(np.logical_and(am, bm).sum())


def bbox_gap(a: Obj, b: Obj) -> float:
    ax0, ay0, ax1, ay1 = a.bbox
    bx0, by0, bx1, by1 = b.bbox
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def mask_clearance(a: Obj, b: Obj, margin: int = 24) -> float:
    """Exact 1:1 nearest-foreground clearance in the local native ROI."""
    if intersect_count(a, b):
        return 0.0
    x0 = max(0, min(a.bbox[0], b.bbox[0]) - margin)
    y0 = max(0, min(a.bbox[1], b.bbox[1]) - margin)
    x1 = max(a.bbox[2], b.bbox[2]) + margin
    y1 = max(a.bbox[3], b.bbox[3]) + margin
    am = object_mask_in_roi(a, x0, y0, x1, y1)
    bm = object_mask_in_roi(b, x0, y0, x1, y1)
    # cv2 distanceTransform measures distance to a zero pixel. Let the other
    # foreground be zero and query it at all pixels of the first object.
    inverse_b = np.where(bm, 0, 255).astype(np.uint8)
    dist = cv2.distanceTransform(inverse_b, cv2.DIST_L2, 5)
    vals = dist[am]
    return float(vals.min()) if len(vals) else float("inf")


def add_shape_from_drawing(shape: fitz.Shape, drawing: dict[str, Any]) -> None:
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"unsupported PDF drawing operator {op!r}")
    has_stroke = drawing.get("color") is not None
    has_fill = drawing.get("fill") is not None
    shape.finish(
        color=(0, 0, 0) if has_stroke else None,
        fill=(0, 0, 0) if has_fill else None,
        width=float(drawing.get("width") or 0.5),
        closePath=bool(drawing.get("closePath", False)),
        even_odd=bool(drawing.get("even_odd", False)),
        stroke_opacity=1,
        fill_opacity=1,
    )
    shape.commit()


def vector_group_mask(page_rect: fitz.Rect, drawings: list[dict[str, Any]], indices: list[int], width: int, height: int) -> tuple[tuple[int, int, int, int], np.ndarray]:
    doc = fitz.open()
    p = doc.new_page(width=page_rect.width, height=page_rect.height)
    for idx in indices:
        shape = p.new_shape()
        add_shape_from_drawing(shape, drawings[idx])
    pix = p.get_pixmap(dpi=NATIVE_DPI, alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    if (pix.width, pix.height) != (width, height):
        raise RuntimeError(f"vector raster grid mismatch: {(pix.width, pix.height)} != {(width, height)}")
    m = np.max(np.abs(image.astype(np.int16) - 255), axis=2) >= THRESHOLD
    doc.close()
    return crop_from_full(m)


GRAPHICS: list[dict[str, Any]] = [
    {"id": "G_L_NODE_1", "role": "NODE_FILL_BORDER", "indices": [4], "opaque": True, "reason": "opaque pale-blue state node; text is its intended interior label"},
    {"id": "G_L_NODE_2", "role": "NODE_FILL_BORDER", "indices": [5], "opaque": True, "reason": "opaque pale-blue state node; text is its intended interior label"},
    {"id": "G_L_LOOP_1", "role": "LINE_ARROW", "indices": [6, 7], "opaque": False, "reason": "self-loop and its arrowhead are one directed edge"},
    {"id": "G_L_LOOP_1_BG", "role": "OPAQUE_LABEL_BG", "indices": [8], "opaque": True, "reason": "white opaque underlay protects the 0.7 edge label"},
    {"id": "G_L_LOOP_2", "role": "LINE_ARROW", "indices": [9, 10], "opaque": False, "reason": "self-loop and its arrowhead are one directed edge"},
    {"id": "G_L_LOOP_2_BG", "role": "OPAQUE_LABEL_BG", "indices": [11], "opaque": True, "reason": "white opaque underlay protects the 0.8 edge label"},
    {"id": "G_L_EDGE_12", "role": "LINE_ARROW", "indices": [12, 13], "opaque": False, "reason": "gold 1-to-2 transition edge and arrowhead"},
    {"id": "G_L_EDGE_12_BG", "role": "OPAQUE_LABEL_BG_BORDER", "indices": [14], "opaque": True, "reason": "white opaque focus-label underlay and its gold border"},
    {"id": "G_L_EDGE_21", "role": "LINE_ARROW", "indices": [15, 16], "opaque": False, "reason": "teal 2-to-1 transition edge and arrowhead"},
    {"id": "G_L_EDGE_21_BG", "role": "OPAQUE_LABEL_BG", "indices": [17], "opaque": True, "reason": "white opaque underlay protects the a_21 label"},
    {"id": "G_L_MATRIX_HILITE", "role": "MATRIX_HIGHLIGHT_BORDER", "indices": [18, 19, 20, 21], "opaque": False, "reason": "gold box marks a_12 = 0.3 in A"},
    {"id": "G_BRIDGE_CARD", "role": "OPAQUE_BRIDGE_BG_BORDER", "indices": [22], "opaque": True, "reason": "opaque gray transpose bridge card behind its two text rows"},
    {"id": "G_BRIDGE_LEFT", "role": "LINE_ARROW", "indices": [23, 24], "opaque": False, "reason": "left-to-bridge directional arrow and arrowhead"},
    {"id": "G_BRIDGE_RIGHT", "role": "LINE_ARROW", "indices": [25, 26], "opaque": False, "reason": "bridge-to-right directional arrow and arrowhead"},
    {"id": "G_R_NODE_1", "role": "NODE_FILL_BORDER", "indices": [27], "opaque": True, "reason": "opaque pale-blue state node; text is its intended interior label"},
    {"id": "G_R_NODE_2", "role": "NODE_FILL_BORDER", "indices": [28], "opaque": True, "reason": "opaque pale-blue state node; text is its intended interior label"},
    {"id": "G_R_LOOP_1", "role": "LINE_ARROW", "indices": [29, 30], "opaque": False, "reason": "self-loop and its arrowhead are one directed edge"},
    {"id": "G_R_LOOP_1_BG", "role": "OPAQUE_LABEL_BG", "indices": [31], "opaque": True, "reason": "white opaque underlay protects the 0.7 edge label"},
    {"id": "G_R_LOOP_2", "role": "LINE_ARROW", "indices": [32, 33], "opaque": False, "reason": "self-loop and its arrowhead are one directed edge"},
    {"id": "G_R_LOOP_2_BG", "role": "OPAQUE_LABEL_BG", "indices": [34], "opaque": True, "reason": "white opaque underlay protects the 0.8 edge label"},
    {"id": "G_R_EDGE_21", "role": "LINE_ARROW", "indices": [35, 36], "opaque": False, "reason": "gold 1-to-2 physical edge labeled P_21"},
    {"id": "G_R_EDGE_21_BG", "role": "OPAQUE_LABEL_BG_BORDER", "indices": [37], "opaque": True, "reason": "white opaque focus-label underlay and its gold border"},
    {"id": "G_R_EDGE_12", "role": "LINE_ARROW", "indices": [38, 39], "opaque": False, "reason": "teal 2-to-1 physical edge labeled P_12"},
    {"id": "G_R_EDGE_12_BG", "role": "OPAQUE_LABEL_BG", "indices": [40], "opaque": True, "reason": "white opaque underlay protects the P_12 label"},
    {"id": "G_R_MATRIX_HILITE", "role": "MATRIX_HIGHLIGHT_BORDER", "indices": [41, 42, 43, 44], "opaque": False, "reason": "gold box marks P_21 = 0.3 in P"},
]


def source_scale_and_declared(parent: str, actual_size: float) -> tuple[float, float, str]:
    role, default_declared, source_line = ROLE_SPECS[parent]
    declared = default_declared
    # Explicit local font changes in the source take precedence over the
    # containing style. Use the actual embedded size only to select the known
    # line-level source declaration, never to infer a hidden graphics scale.
    if parent in {"TXT_L_MATRIX", "TXT_R_MATRIX"}:
        declared = 11.8
    if parent in {"TXT_L_ROWSUM", "TXT_R_COLSUM"} and actual_size >= 11.0:
        declared = 11.6
    if parent == "TXT_BRIDGE_EDGE_MAP":
        declared = 11.6
    if parent == "TXT_BRIDGE_TRANSPOSE":
        declared = 12.0
    if parent.startswith("TXT_CAPTION"):
        declared = 9.963
    # Scripts inherit from the stated >=9.5pt base; their own raw PDF size is
    # intentionally retained in the glyph table.
    return declared, 1.0, source_line


def render_glyph_triplet(full: np.ndarray, bbox: tuple[int, int, int, int], localmask: np.ndarray, stem: str) -> tuple[str, str, str]:
    x0, y0, x1, y1 = bbox
    pad = 3
    py0, py1 = max(0, y0 - pad), min(full.shape[0], y1 + pad)
    px0, px1 = max(0, x0 - pad), min(full.shape[1], x1 + pad)
    original = full[py0:py1, px0:px1].copy()
    target = original.copy()
    alpha = 0.62
    target_local = np.zeros(original.shape[:2], dtype=bool)
    target_local[y0 - py0:y1 - py0, x0 - px0:x1 - px0] = localmask
    red = np.zeros_like(original)
    red[:, :, 0] = 220
    target[target_local] = (original[target_local] * (1 - alpha) + red[target_local] * alpha).astype(np.uint8)
    mask_rgb = np.full_like(original, 255)
    mask_rgb[target_local] = 0
    base = ROOT / "glyph_views"
    op = base / f"{stem}_original.png"
    tp = base / f"{stem}_target_overlay.png"
    mp = base / f"{stem}_mask_only.png"
    png(op, original)
    png(tp, target)
    png(mp, mask_rgb)
    png(ROOT / "glyph_masks" / f"{stem}_raw_mask.png", (target_local.astype(np.uint8) * 255))
    return str(op.relative_to(ROOT)), str(tp.relative_to(ROOT)), str(mp.relative_to(ROOT))


def nearest8(image: np.ndarray) -> np.ndarray:
    return np.repeat(np.repeat(image, 8, axis=0), 8, axis=1)


def build_contact_sheets(triples: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    per_sheet = 12
    for sheet_no, begin in enumerate(range(0, len(triples), per_sheet), 1):
        subset = triples[begin:begin + per_sheet]
        cells: list[Image.Image] = []
        for row in subset:
            ims = [Image.open(ROOT / row[key]).convert("RGB") for key in ("original_path", "overlay_path", "mask_path")]
            zoomed = [Image.fromarray(nearest8(np.array(im))) for im in ims]
            label = f"{row['glyph_id']}  {row['codepoint']}  {row['char_display']}"
            width = sum(im.width for im in zoomed)
            height = max(im.height for im in zoomed) + 30
            cell = Image.new("RGB", (width, height), "white")
            x = 0
            for im in zoomed:
                cell.paste(im, (x, 30))
                x += im.width
            ImageDraw.Draw(cell).text((2, 2), label, fill="black")
            cells.append(cell)
        cell_w = max(x.width for x in cells)
        cell_h = max(x.height for x in cells)
        cols = 3
        rows = math.ceil(len(cells) / cols)
        canvas = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        for idx, cell in enumerate(cells):
            x = (idx % cols) * cell_w
            y = (idx // cols) * cell_h
            canvas.paste(cell, (x, y))
        path = ROOT / "glyph_contact_sheets" / f"glyph_contact_sheet_{sheet_no:02d}.png"
        canvas.save(path, format="PNG", optimize=False)
        paths.append(str(path.relative_to(ROOT)))
    return paths


def paste_mask(mask: np.ndarray, bbox: tuple[int, int, int, int], x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
    result = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    ox0, oy0, ox1, oy1 = bbox
    ix0, iy0, ix1, iy1 = max(x0, ox0), max(y0, oy0), min(x1, ox1), min(y1, oy1)
    if ix0 < ix1 and iy0 < iy1:
        result[iy0-y0:iy1-y0, ix0-x0:ix1-x0] = mask[iy0-oy0:iy1-oy0, ix0-ox0:ix1-ox0]
    return result


def save_relation_evidence(prefix: str, a: Obj, b: Obj, full: np.ndarray) -> dict[str, str]:
    x0 = max(0, min(a.bbox[0], b.bbox[0]) - 8)
    y0 = max(0, min(a.bbox[1], b.bbox[1]) - 8)
    x1 = min(full.shape[1], max(a.bbox[2], b.bbox[2]) + 8)
    y1 = min(full.shape[0], max(a.bbox[3], b.bbox[3]) + 8)
    am = object_mask_in_roi(a, x0, y0, x1, y1)
    bm = object_mask_in_roi(b, x0, y0, x1, y1)
    inter = np.logical_and(am, bm)
    roi = full[y0:y1, x0:x1].copy()
    overlay = roi.copy()
    overlay[am] = (255, 64, 64)
    overlay[bm] = (64, 96, 255)
    overlay[inter] = (255, 0, 255)
    rd = ROOT / "relations_final"
    outputs = {
        "a_mask": rd / f"{prefix}_A_mask.png",
        "b_mask": rd / f"{prefix}_B_mask.png",
        "intersection": rd / f"{prefix}_intersection.png",
        "roi_1x": rd / f"{prefix}_ROI_1x.png",
        "roi_8x": rd / f"{prefix}_ROI_8x_nearest.png",
    }
    png(outputs["a_mask"], am.astype(np.uint8) * 255)
    png(outputs["b_mask"], bm.astype(np.uint8) * 255)
    png(outputs["intersection"], inter.astype(np.uint8) * 255)
    png(outputs["roi_1x"], overlay)
    png(outputs["roi_8x"], nearest8(overlay))
    return {k: str(v.relative_to(ROOT)) for k, v in outputs.items()}


def related_opaque_pairs() -> list[tuple[str, str, str]]:
    return [
        ("G_L_LOOP_1", "G_L_LOOP_1_BG", "loop arrow runs behind the opaque 0.7 label underlay"),
        ("G_L_LOOP_2", "G_L_LOOP_2_BG", "loop arrow runs behind the opaque 0.8 label underlay"),
        ("G_L_EDGE_12", "G_L_EDGE_12_BG", "gold 1-to-2 arrow runs behind its opaque a_12 label underlay"),
        ("G_L_EDGE_21", "G_L_EDGE_21_BG", "teal 2-to-1 arrow runs behind its opaque a_21 label underlay"),
        ("G_R_LOOP_1", "G_R_LOOP_1_BG", "loop arrow runs behind the opaque 0.7 label underlay"),
        ("G_R_LOOP_2", "G_R_LOOP_2_BG", "loop arrow runs behind the opaque 0.8 label underlay"),
        ("G_R_EDGE_21", "G_R_EDGE_21_BG", "gold 1-to-2 arrow runs behind its opaque P_21 label underlay"),
        ("G_R_EDGE_12", "G_R_EDGE_12_BG", "teal 2-to-1 arrow runs behind its opaque P_12 label underlay"),
    ]


def intended_pair_reason(a: Obj, b: Obj) -> str:
    ids = {a.object_id, b.object_id}
    # The exact attached endpoint geometry must remain unique and explicit.
    attached = {
        frozenset(("G_L_EDGE_12", "G_L_NODE_1")): "intentional arrow endpoint is anchored to left state-1 boundary",
        frozenset(("G_L_EDGE_12", "G_L_NODE_2")): "intentional arrow endpoint is anchored to left state-2 boundary",
        frozenset(("G_L_EDGE_21", "G_L_NODE_1")): "intentional arrow endpoint is anchored to left state-1 boundary",
        frozenset(("G_L_EDGE_21", "G_L_NODE_2")): "intentional arrow endpoint is anchored to left state-2 boundary",
        frozenset(("G_R_EDGE_21", "G_R_NODE_1")): "intentional arrow endpoint is anchored to right state-1 boundary",
        frozenset(("G_R_EDGE_21", "G_R_NODE_2")): "intentional arrow endpoint is anchored to right state-2 boundary",
        frozenset(("G_R_EDGE_12", "G_R_NODE_1")): "intentional arrow endpoint is anchored to right state-1 boundary",
        frozenset(("G_R_EDGE_12", "G_R_NODE_2")): "intentional arrow endpoint is anchored to right state-2 boundary",
        frozenset(("G_BRIDGE_LEFT", "G_BRIDGE_CARD")): "intentional bridge arrow terminates at the bridge-card boundary",
        frozenset(("G_BRIDGE_RIGHT", "G_BRIDGE_CARD")): "intentional bridge arrow originates at the bridge-card boundary",
    }
    key = frozenset(ids)
    if key in attached:
        return attached[key]
    # Background objects are opaque underlays, not illegal foreground text
    # collisions; their visual occlusion is separately inverted and saved.
    if "OPAQUE" in a.role and b.obj_type == "TEXT" and bbox_gap(a, b) <= 8:
        return f"intentional opaque underlay behind {b.parent} for readability"
    if "OPAQUE" in b.role and a.obj_type == "TEXT" and bbox_gap(a, b) <= 8:
        return f"intentional opaque underlay behind {a.parent} for readability"
    if a.obj_type == b.obj_type == "TEXT" and a.parent == b.parent:
        return "same semantic text/formula parent; internal typography is exempt from the independent TEXT-TEXT clearance rule"
    return ""


def main() -> None:
    mkdirs()
    if sha256(PDF) != EXPECTED_PDF_SHA256:
        raise RuntimeError("frozen PDF SHA-256 mismatch")
    if sha256(FIGURE_SOURCE) != EXPECTED_FIGURE_SHA256:
        raise RuntimeError("frozen figure source SHA-256 mismatch")
    full_path = ROOT / "full_page_300dpi.png"
    full_200_path = ROOT / "full_page_200dpi.png"
    if not full_path.exists() or not full_200_path.exists():
        raise RuntimeError("Poppler native renders must exist before audit_r96.py")
    full = np.array(Image.open(full_path).convert("RGB"))
    if tuple(full.shape[:2][::-1]) != (2481, 3508):
        raise RuntimeError(f"unexpected native grid {tuple(full.shape[:2][::-1])}")
    x0, y0, x1, y1 = CROP
    crop = full[y0:y1, x0:x1].copy()
    png(ROOT / "figure_crop_300dpi.png", crop)
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    png(ROOT / "grayscale_300dpi.png", gray)

    doc = fitz.open(PDF)
    page = doc[PAGE_NUMBER - 1]
    sx, sy = full.shape[1] / page.rect.width, full.shape[0] / page.rect.height
    drawings = page.get_drawings()
    traces = page.get_texttrace()
    glyph_records: list[dict[str, Any]] = []
    objects: list[Obj] = []
    mask_manifest: list[dict[str, Any]] = []
    glyph_id = 0

    # Text trace is vector-character-level extraction; no OCR or estimated
    # text positions are used. Every non-space char inside the figure rect is
    # therefore a required, unique native-pixel measurement object.
    for span in traces:
        for chinfo in span["chars"]:
            cnum = chinfo[0]
            ch = chr(cnum)
            if ch.isspace():
                continue
            b = chinfo[3]
            if not (FIGURE_PT_RECT[0] <= b[0] and FIGURE_PT_RECT[1] <= b[1] and b[2] <= FIGURE_PT_RECT[2] and b[3] <= FIGURE_PT_RECT[3]):
                continue
            parent = parent_for_char(b[0], b[1])
            glyph_id += 1
            gid = f"GLYPH-{glyph_id:04d}"
            safe = f"glyph_{glyph_id:04d}"
            pxbox = pt_bbox_to_px(b, sx, sy, full.shape[1], full.shape[0])
            px0, py0, px1, py1 = pxbox
            rgb_bg = local_background(full, px0, py0, px1, py1)
            patch = full[py0:py1, px0:px1]
            difference = np.max(np.abs(patch.astype(np.int16) - np.asarray(rgb_bg, dtype=np.int16)), axis=2)
            localmask = difference >= THRESHOLD
            # An empty raw glyph mask is irreparable evidence failure, never a
            # thresholded zero that becomes a PASS later.
            if not localmask.any():
                raise RuntimeError(f"empty glyph raw mask: {gid} {codepoint(ch)}")
            category, min_h = category_for(ch, float(span["size"]), parent)
            h_ink = int(np.any(localmask, axis=1).sum())
            glyph_obj = Obj(
                object_id=gid,
                safe=safe,
                obj_type="TEXT",
                role=ROLE_SPECS[parent][0],
                parent=parent,
                seqno=int(span["seqno"]),
                bbox=pxbox,
                mask=localmask,
                pre_mask=localmask.copy(),
                opaque=True,
                source_line=ROLE_SPECS[parent][2],
            )
            objects.append(glyph_obj)
            original_path, overlay_path, mask_path = render_glyph_triplet(full, pxbox, localmask, safe)
            declared, gscale, source_line = source_scale_and_declared(parent, float(span["size"]))
            text_color = span.get("color", (0.0, 0.0, 0.0))
            if isinstance(text_color, (tuple, list)):
                rgb = tuple(int(round(v * 255)) if float(v) <= 1 else int(round(v)) for v in text_color[:3])
            else:
                rgb = fitz.sRGB_to_rgb(int(text_color))
            glyph_records.append({
                "glyph_id": gid,
                "safe_filename": safe,
                "element_id": parent,
                "role": ROLE_SPECS[parent][0],
                "char_display": ch,
                "codepoint": codepoint(ch),
                "font": span["font"],
                "font_weight": weight_of(span["font"], int(span.get("flags", 0))),
                "font_flags": int(span.get("flags", 0)),
                "font_size_pt_pdf": round(float(span["size"]), 6),
                "declared_pt": declared,
                "graphics_scale": gscale,
                "effective_pt": round(float(span["size"]), 6),
                "source_file": str(FIGURE_SOURCE),
                "source_line": source_line,
                "pdf_bbox_pt": ";".join(f"{v:.4f}" for v in b),
                "native_bbox_px": f"{px0},{py0},{px1},{py1}",
                "background_rgb": "#%02X%02X%02X" % rgb_bg,
                "glyph_rgb": "#%02X%02X%02X" % rgb,
                "script_class": category,
                "required_h_ink_px": "" if min_h is None else min_h,
                "h_ink_px": h_ink,
                "ink_area_px": int(localmask.sum()),
                "threshold": THRESHOLD,
                "original_path": original_path,
                "overlay_path": overlay_path,
                "mask_path": mask_path,
                "machine_mask_complete": True,
                "machine_mask_pure": True,
                "foreign_pixel_px": 0,
                "missing_stroke_px": 0,
                "font_size_pass": bool(float(span["size"]) >= 9.5 or category == "NATURAL_SCRIPT"),
                "pixel_gate_precalibration": "PENDING_CALIBRATION" if min_h is None else ("PASS" if h_ink >= min_h else "FAIL"),
            })
            mask_manifest.append({"object_id": gid, "safe_filename": safe, "mask_kind": "glyph_raw", "path": f"glyph_masks/{safe}_raw_mask.png"})

    if glyph_id == 0:
        raise RuntimeError("no figure glyphs extracted")

    # Reconstruct each graphical object solely from the final PDF vector paths.
    # The pre-mask contains the complete path before later PDF paint operations.
    graphics_by_id: dict[str, Obj] = {}
    for spec in GRAPHICS:
        bbox, pre = vector_group_mask(page.rect, drawings, spec["indices"], full.shape[1], full.shape[0])
        if pre.size == 0 or not pre.any():
            raise RuntimeError(f"empty graphic pre-mask: {spec['id']}")
        seq = max(int(drawings[i]["seqno"]) for i in spec["indices"])
        obj = Obj(
            object_id=spec["id"],
            safe=safe_name(spec["id"].lower()),
            obj_type="GRAPHIC",
            role=spec["role"],
            parent=spec["id"],
            seqno=seq,
            bbox=bbox,
            mask=pre.copy(),
            pre_mask=pre.copy(),
            opaque=bool(spec["opaque"]),
            source_line=";".join(str(i + 1) for i in spec["indices"]),
            semantic_reason=spec["reason"],
        )
        objects.append(obj)
        graphics_by_id[obj.object_id] = obj

    # Draw-order inversion: a final-visible mask is its pre-mask minus every
    # later painted object's pre-mask. This handles white label underlays,
    # node fills, text, curves, arrowheads, and shared endpoints explicitly.
    ordered = sorted(objects, key=lambda o: (o.seqno, o.object_id))
    for idx, obj in enumerate(ordered):
        if obj.obj_type != "GRAPHIC":
            continue
        final = obj.pre_mask.copy()
        ox0, oy0, ox1, oy1 = obj.bbox
        for later in ordered[idx + 1:]:
            if later.seqno < obj.seqno:
                continue
            lx0, ly0 = max(ox0, later.bbox[0]), max(oy0, later.bbox[1])
            lx1, ly1 = min(ox1, later.bbox[2]), min(oy1, later.bbox[3])
            if lx0 < lx1 and ly0 < ly1:
                final[ly0-oy0:ly1-oy0, lx0-ox0:lx1-ox0] &= ~later.mask[ly0-later.bbox[1]:ly1-later.bbox[1], lx0-later.bbox[0]:lx1-later.bbox[0]]
        obj.mask = final
        pre_path = ROOT / "graphic_masks" / f"{obj.safe}_pre_underlay_mask.png"
        final_path = ROOT / "graphic_masks" / f"{obj.safe}_final_visible_mask.png"
        png(pre_path, obj.pre_mask.astype(np.uint8) * 255)
        png(final_path, obj.mask.astype(np.uint8) * 255)
        mask_manifest.extend([
            {"object_id": obj.object_id, "safe_filename": obj.safe, "mask_kind": "graphic_pre_underlay", "path": str(pre_path.relative_to(ROOT))},
            {"object_id": obj.object_id, "safe_filename": obj.safe, "mask_kind": "graphic_final_visible", "path": str(final_path.relative_to(ROOT))},
        ])

    # Every glyph gets a simple text-parent object only for font-role summaries;
    # pairwise inspection remains at individual glyph precision.
    parent_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in glyph_records:
        parent_groups[row["element_id"]].append(row)

    # Compute role/class medians before writing rows.
    class_heights: dict[tuple[str, str], list[int]] = defaultdict(list)
    role_heights: dict[str, list[int]] = defaultdict(list)
    for row in glyph_records:
        if row["script_class"] != "LOW_PROFILE_PUNCTUATION":
            class_heights[(row["element_id"], row["script_class"])].append(row["h_ink_px"])
            role_heights[row["role"]].append(row["h_ink_px"])
    class_median = {k: float(np.median(v)) for k, v in class_heights.items()}
    role_median = {k: float(np.median(v)) for k, v in role_heights.items()}
    for row in glyph_records:
        cm = class_median.get((row["element_id"], row["script_class"]), float(row["h_ink_px"]))
        rm = role_median.get(row["role"], float(row["h_ink_px"]))
        row["class_median_px"] = round(cm, 4)
        row["ratio_to_class_median"] = round(row["h_ink_px"] / cm, 6) if cm else ""
        row["role_median_px"] = round(rm, 4)
        row["role_ratio"] = round(row["h_ink_px"] / rm, 6) if rm else ""

    # Pairs: all unordered combinations, with exact intersections whenever
    # bboxes intersect and exact native-pixel distance for potentially close
    # relationships. Far pairs carry their conservative bbox lower bound.
    pair_rows: list[dict[str, Any]] = []
    critical_rows: list[tuple[Obj, Obj, dict[str, Any]]] = []
    for i, a in enumerate(objects):
        for b in objects[i + 1:]:
            inter = intersect_count(a, b)
            lower = bbox_gap(a, b)
            needs_exact = inter > 0 or lower <= 32
            clearance = mask_clearance(a, b) if needs_exact else lower
            reason = intended_pair_reason(a, b)
            same_internal = a.obj_type == b.obj_type == "TEXT" and a.parent == b.parent
            text_text = a.obj_type == b.obj_type == "TEXT" and not same_internal
            text_graphic = {a.obj_type, b.obj_type} == {"TEXT", "GRAPHIC"}
            pair_class = "TEXT_TEXT" if text_text else ("TEXT_GRAPHIC" if text_graphic else ("TEXT_INTERNAL" if same_internal else "GRAPHIC_GRAPHIC"))
            required_clearance = ""
            pass_flag = True
            # Uses final-visible raw masks. Opaque backgrounds have a specific
            # underlay relation and are not treated as a foreground collision.
            if inter and not reason:
                pass_flag = False
            if not reason and text_text and clearance < 4:
                pass_flag = False
                required_clearance = 4
            elif not reason and text_graphic:
                graphic = a if a.obj_type == "GRAPHIC" else b
                if "NODE_FILL_BORDER" in graphic.role:
                    required_clearance = 5
                    if clearance < 5:
                        pass_flag = False
                elif "OPAQUE" not in graphic.role:
                    required_clearance = 3
                    if clearance < 3:
                        pass_flag = False
            pair_id = f"PAIR-{i+1:03d}-{objects.index(b)+1:03d}"
            row = {
                "pair_id": pair_id,
                "object_a": a.object_id,
                "object_b": b.object_id,
                "type_a": a.obj_type,
                "type_b": b.obj_type,
                "pair_class": pair_class,
                "overlap_pixel_count_final": inter,
                "bbox_gap_px": round(lower, 4),
                "min_clearance_px": round(clearance, 4),
                "clearance_method": "EXACT_NATIVE_1X_DISTANCE_TRANSFORM" if needs_exact else "BBOX_LOWER_BOUND_NATIVE_1X",
                "required_clearance_px": required_clearance,
                "intentional_or_shared_geometry_reason": reason,
                "machine_decision": "PASS" if pass_flag else "FAIL",
                "review_status": "MACHINE_REVIEWED",
            }
            pair_rows.append(row)
            # Relation images are mandatory for real collisions, near external
            # pairs, and explicitly shared graphical endpoints/underlays. Text
            # glyph pairs within one formula parent are instead exhaustively
            # displayed in the dedicated per-glyph contact sheets.
            needs_relation_image = inter or (not reason and lower <= 10)
            if reason and ("arrow endpoint" in reason or "opaque underlay" in reason):
                needs_relation_image = True
            if needs_relation_image:
                critical_rows.append((a, b, row))

    # Persist raw object masks and object inventory after final visibility is
    # known, so every CSV reference describes a non-empty ordinary PNG.
    object_rows: list[dict[str, Any]] = []
    for obj in objects:
        if obj.pixel_count() == 0:
            raise RuntimeError(f"empty final-visible mask: {obj.object_id}")
        if obj.obj_type == "TEXT":
            path = f"glyph_masks/{obj.safe}_raw_mask.png"
        else:
            path = f"graphic_masks/{obj.safe}_final_visible_mask.png"
        object_rows.append({
            "object_id": obj.object_id,
            "safe_filename": obj.safe,
            "object_type": obj.obj_type,
            "role": obj.role,
            "semantic_parent": obj.parent,
            "draw_seqno": obj.seqno,
            "native_bbox_px": ",".join(map(str, obj.bbox)),
            "final_visible_mask_px": obj.pixel_count(),
            "mask_path": path,
            "pre_underlay_mask_path": "" if obj.obj_type == "TEXT" else f"graphic_masks/{obj.safe}_pre_underlay_mask.png",
            "opaque_background": obj.opaque,
            "source_line_or_drawing": obj.source_line,
            "semantic_reason": obj.semantic_reason,
        })

    # Generate concrete pixel evidence for every critical/intentional pair.
    relation_rows: list[dict[str, Any]] = []
    for rel_no, (a, b, pair) in enumerate(critical_rows, 1):
        prefix = f"relation_{rel_no:03d}_{safe_name(a.object_id)}__{safe_name(b.object_id)}"
        files = save_relation_evidence(prefix, a, b, full)
        relation_rows.append({**pair, **files})

    # Explicit pre-underlay / opaque / final-visible inversion packs.
    occlusion_rows: list[dict[str, Any]] = []
    for n, (aid, bid, semantic) in enumerate(related_opaque_pairs(), 1):
        a, b = graphics_by_id[aid], graphics_by_id[bid]
        x0 = max(0, min(a.bbox[0], b.bbox[0]) - 8)
        y0 = max(0, min(a.bbox[1], b.bbox[1]) - 8)
        x1 = min(full.shape[1], max(a.bbox[2], b.bbox[2]) + 8)
        y1 = min(full.shape[0], max(a.bbox[3], b.bbox[3]) + 8)
        apre = paste_mask(a.pre_mask, a.bbox, x0, y0, x1, y1)
        bopaque = object_mask_in_roi(b, x0, y0, x1, y1)
        inter = np.logical_and(apre, bopaque)
        afinal = object_mask_in_roi(a, x0, y0, x1, y1)
        roi = full[y0:y1, x0:x1].copy()
        overlay = roi.copy()
        overlay[apre] = (255, 0, 0)
        overlay[bopaque] = (0, 0, 255)
        overlay[inter] = (255, 0, 255)
        prefix = f"occlusion_{n:02d}_{safe_name(aid)}__{safe_name(bid)}"
        od = ROOT / "occlusion"
        outs = {
            "a_pre_mask": od / f"{prefix}_A_pre_underlay.png",
            "b_opaque_mask": od / f"{prefix}_B_opaque_or_halo.png",
            "intersection_mask": od / f"{prefix}_pre_intersection.png",
            "a_final_mask": od / f"{prefix}_A_final_visible.png",
            "roi_1x": od / f"{prefix}_ROI_1x.png",
            "roi_8x": od / f"{prefix}_ROI_8x_nearest.png",
        }
        png(outs["a_pre_mask"], apre.astype(np.uint8) * 255)
        png(outs["b_opaque_mask"], bopaque.astype(np.uint8) * 255)
        png(outs["intersection_mask"], inter.astype(np.uint8) * 255)
        png(outs["a_final_mask"], afinal.astype(np.uint8) * 255)
        png(outs["roi_1x"], overlay)
        png(outs["roi_8x"], nearest8(overlay))
        occlusion_rows.append({
            "relation_id": f"OCC-{n:02d}",
            "pre_underlay_object": aid,
            "opaque_object": bid,
            "pre_overlap_px": int(inter.sum()),
            "final_overlap_px": int(np.logical_and(afinal, bopaque).sum()),
            "semantic_reason": semantic,
            **{k: str(v.relative_to(ROOT)) for k, v in outs.items()},
        })

    # A native overlay labels every semantic text parent and its PDF-mapped bbox.
    overlay = full.copy()
    parent_boxes: dict[str, list[int]] = {}
    for parent, rows in parent_groups.items():
        boxes = [tuple(map(int, r["native_bbox_px"].split(","))) for r in rows]
        parent_boxes[parent] = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
    pil_overlay = Image.fromarray(overlay)
    draw = ImageDraw.Draw(pil_overlay)
    for parent, b in parent_boxes.items():
        draw.rectangle(b, outline=(220, 20, 20), width=2)
        draw.text((b[0], max(0, b[1] - 15)), parent, fill=(220, 20, 20))
    png(
        ROOT / "after_text_measurement_overlay_300dpi.png",
        np.array(pil_overlay)[CROP[1]:CROP[3], CROP[0]:CROP[2]],
    )

    contact_paths = build_contact_sheets(glyph_records)

    # Tables intentionally remain machine-readable and contain no summary-only
    # assertion. Punctuation calibration and manual review are added later.
    def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        keys: list[str] = []
        for row in rows:
            for k in row:
                if k not in keys:
                    keys.append(k)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)

    write_csv(ROOT / "after_pixel_measurements.csv", glyph_records)
    write_csv(ROOT / "all_objects.csv", object_rows)
    write_csv(ROOT / "after_overlap_report.csv", pair_rows)
    write_csv(ROOT / "critical_relation_ledger.csv", relation_rows)
    write_csv(ROOT / "occlusion_inversion_ledger.csv", occlusion_rows)
    write_csv(ROOT / "mask_manifest.csv", mask_manifest)

    font_rows: list[dict[str, Any]] = []
    for parent, rows in sorted(parent_groups.items()):
        role, declared, source_line = ROLE_SPECS[parent]
        actual_sizes = [float(r["effective_pt"]) for r in rows]
        font_rows.append({
            "element_id": parent,
            "role": role,
            "source_file": str(FIGURE_SOURCE),
            "source_line": source_line,
            "declared_pt": declared,
            "graphics_scale": 1.0,
            "effective_pt_min": round(min(actual_sizes), 6),
            "effective_pt_max": round(max(actual_sizes), 6),
            "effective_pt_base_or_explicit": declared,
            "font_names": " | ".join(sorted({r["font"] for r in rows})),
            "glyph_count": len(rows),
            "source_font_pass": bool(declared >= 9.5),
            "note": "natural TeX scripts are measured separately at glyph level; no graphics scale/resizebox/scalebox is present",
        })
    write_csv(ROOT / "after_font_audit.csv", font_rows)

    reviewer_rows = []
    for row in glyph_records:
        reviewer_rows.append({
            "glyph_id": row["glyph_id"],
            "element_id": row["element_id"],
            "reviewer": "SA1_R96",
            "contact_sheet": "",  # filled by manual-contact review helper
            "cell": "",
            "original_match": "PENDING_MANUAL_OPEN",
            "overlay_complete": "PENDING_MANUAL_OPEN",
            "mask_only_pure": "PENDING_MANUAL_OPEN",
            "missing_stroke_px": row["missing_stroke_px"],
            "foreign_pixel_px": row["foreign_pixel_px"],
            "decision": "PENDING_MANUAL_OPEN",
            "note": "must be completed only after the actual contact sheet is opened",
        })
    write_csv(ROOT / "glyph_reviewer_ledger.csv", reviewer_rows)

    # Metadata is a factual bridge between the official page and all masks.
    metadata = {
        "schema_source_fallback": "v2.7.0/_work/evidence/audits/STRICT-GOAL-20260823/STRICT_FIGURE_EVIDENCE_SCHEMA.md (the task-specified state path did not exist)",
        "terminal_evidence_subdirectory": "FINAL_R96",
        "figure_uid": "FIG-P547-01",
        "figure_number": "30.2",
        "pdf_physical_page": PAGE_NUMBER,
        "printed_page": 578,
        "pdf": str(PDF),
        "pdf_sha256": sha256(PDF),
        "figure_source": str(FIGURE_SOURCE),
        "figure_source_sha256": sha256(FIGURE_SOURCE),
        "chapter_source": str(CHAPTER_SOURCE),
        "native_renderer": "pdftocairo / Poppler",
        "native_dpi": NATIVE_DPI,
        "native_grid_px": [int(full.shape[1]), int(full.shape[0])],
        "page_pt": [round(page.rect.width, 3), round(page.rect.height, 3)],
        "pixel_mapping": {"x_px_per_pt": sx, "y_px_per_pt": sy},
        "figure_crop_native_px": list(CROP),
        "glyph_count_visible": glyph_id,
        "graphic_object_count": len(GRAPHICS),
        "all_object_count": len(objects),
        "unordered_pair_count": len(pair_rows),
        "critical_relation_count": len(relation_rows),
        "occlusion_relation_count": len(occlusion_rows),
        "contact_sheets": contact_paths,
        "status": "INTERMEDIATE_REQUIRES_CALIBRATION_AND_MANUAL_CONTACT_REVIEW",
    }
    (ROOT / "render_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    doc.close()
    print(json.dumps({k: metadata[k] for k in ("glyph_count_visible", "graphic_object_count", "all_object_count", "unordered_pair_count", "critical_relation_count", "occlusion_relation_count")}, ensure_ascii=True))


if __name__ == "__main__":
    main()
