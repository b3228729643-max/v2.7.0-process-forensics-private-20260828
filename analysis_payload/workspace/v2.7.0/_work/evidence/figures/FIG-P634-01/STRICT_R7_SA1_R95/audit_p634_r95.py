"""Independent SA1 audit for FIG-P634-01 against the official R95 PDF.

This script is deliberately self-contained in the newly created evidence
directory.  It never reads a prior FIG-P634-01 evidence directory.  Pixel
measurements always originate in full_page_300dpi.png, which was rendered
directly from official R95 physical page 682 with pdftocairo at 300 dpi.
"""
from __future__ import annotations

import csv
from io import BytesIO
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt

import pdf_glyph_replay_support as pdf_replay


BASE_ROOT = Path(__file__).resolve().parent
# The first candidate outputs at BASE_ROOT are deliberately retained with a
# SUPERSEDED marker because their bbox-delta masks were contaminated.  The
# R3 remains preserved but explicitly superseded because it contains replay
# method probes.  R4 was interrupted before a machine stage and R5 used the
# wrong naked-alpha closure; R6 predated final integer-lattice quantisation;
# all are preserved with nonterminal markers. R7 is the clean, from-scratch
# candidate using official PDF content-stream replay, CID-specific full-page
# knockout authority on the final 8-bit lattice, and portable safe evidence
# filenames.  R8 replaces the transparent-replay support as the raw-mask
# authority: the replay remains a source-path diagnostic only.
ROOT = BASE_ROOT / "PATH_ISOLATED_R8_CID_KNOCKOUT_AUTHORITY_SAFE"
ROOT.mkdir(parents=True, exist_ok=True)
OFFICIAL_PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf"
)
PAGE_NUMBER_PHYSICAL = 682
PAGE_INDEX = PAGE_NUMBER_PHYSICAL - 1
PRINTED_PAGE = 669
DPI = 300
SCALE = DPI / 72.0
# The isolated SVG path is conservatively sampled on this subpixel grid, then
# reduced by exact vector-cell coverage (any covered subcell -> covered native
# cell).  It is a path-trace support construction, never a dilation of the
# official-page mask.  Final H/overlap measurements still use only 300dpi.
PATH_SUPPORT_SUPERSAMPLE = 8
FULL_300 = BASE_ROOT / "full_page_300dpi.png"
FULL_200 = BASE_ROOT / "full_page_200dpi.png"
PAGE_SVG = BASE_ROOT / "page_682_native.svg"

# The page-local figure scope deliberately includes the title, diagram and
# its two-line caption, but excludes the following prose paragraph.  It is
# expressed in PDF pt and only converted to integer native-pixel coordinates.
FIG_RECT_PT = fitz.Rect(70.0, 408.0, 530.0, 612.0)
# Integer crop taken from the native full-page PNG; no resampling is allowed.
CROP_BOX_PX = (280, 1680, 2210, 2580)

RGB_WHITE = np.array((255, 255, 255), dtype=np.float32)
RGB_SL_BLUE = np.array((31, 78, 121), dtype=np.float32)
RGB_SL_GOLD = np.array((183, 121, 31), dtype=np.float32)
RGB_SL_RULE = np.array((184, 192, 200), dtype=np.float32)
RGB_SL_GRAY = np.array((107, 114, 128), dtype=np.float32)
RGB_SL_TEXT = np.array((77, 83, 88), dtype=np.float32)
RGB_SL_INK = np.array((31, 35, 40), dtype=np.float32)
RGB_GOLD_BG = np.array((249, 243, 235), dtype=np.float32)
RGB_BLUE_BG = np.array((246, 248, 250), dtype=np.float32)

# Per-glyph human review is a separately signed evidence stage.  There is no
# global completion switch: every one of the 193 contact cells must receive a
# distinct ledger row tied to the R4 mask/contact identity.
MANUAL_LEDGER_SCHEMA_VERSION = "R8_PER_GLYPH_8X_V1"

WINDOWS_RESERVED_BASENAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def safe_file_stem(value: str) -> str:
    """Return a portable ordinary filename stem, never an NTFS ADS path."""
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).rstrip(". ")
    if not stem:
        stem = "unnamed"
    if stem.upper() in WINDOWS_RESERVED_BASENAMES:
        stem = f"_{stem}"
    if ":" in stem or any(ch in stem for ch in '<>"/\\|?*'):
        abort(f"unsafe Windows filename stem after sanitisation: {value!r} -> {stem!r}")
    return stem


def safe_png_filename(value: str) -> str:
    return safe_file_stem(value) + ".png"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class Mask:
    """A sparse native 1:1 binary mask with an integer page-coordinate bbox."""

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
    def pixels(self) -> int:
        return int(self.data.sum())

    def nonempty_bbox(self) -> tuple[int, int, int, int] | None:
        ys, xs = np.nonzero(self.data)
        if not len(xs):
            return None
        return (
            self.x0 + int(xs.min()),
            self.y0 + int(ys.min()),
            self.x0 + int(xs.max()) + 1,
            self.y0 + int(ys.max()) + 1,
        )


def abort(message: str) -> None:
    print(f"AUDIT_ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def px(value_pt: float) -> float:
    return value_pt * SCALE


def rect_to_px(rect: fitz.Rect, pad: int = 0) -> tuple[int, int, int, int]:
    return (
        max(0, math.floor(px(rect.x0)) - pad),
        max(0, math.floor(px(rect.y0)) - pad),
        math.ceil(px(rect.x1)) + pad,
        math.ceil(px(rect.y1)) + pad,
    )


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def rect_intersection(
    a: tuple[int, int, int, int], b: tuple[int, int, int, int]
) -> tuple[int, int, int, int] | None:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1, y1)


def pair_intersection_pixels(a: Mask, b: Mask) -> int:
    overlap = rect_intersection(a.bbox, b.bbox)
    if overlap is None:
        return 0
    x0, y0, x1, y1 = overlap
    sa = a.data[y0 - a.y0 : y1 - a.y0, x0 - a.x0 : x1 - a.x0]
    sb = b.data[y0 - b.y0 : y1 - b.y0, x0 - b.x0 : x1 - b.x0]
    return int(np.logical_and(sa, sb).sum())


def pair_intersection_mask(a: Mask, b: Mask) -> Mask:
    overlap = rect_intersection(a.bbox, b.bbox)
    if overlap is None:
        return Mask(0, 0, np.zeros((1, 1), dtype=bool))
    x0, y0, x1, y1 = overlap
    sa = a.data[y0 - a.y0 : y1 - a.y0, x0 - a.x0 : x1 - a.x0]
    sb = b.data[y0 - b.y0 : y1 - b.y0, x0 - b.x0 : x1 - b.x0]
    return Mask(x0, y0, np.logical_and(sa, sb))


def pair_min_distance(a: Mask, b: Mask) -> float:
    """Native-pixel centre-to-centre distance; 0 means shared visible pixel."""
    if not a.pixels or not b.pixels:
        return math.inf
    if pair_intersection_pixels(a, b):
        return 0.0
    # A cheap exact lower bound avoids allocating a huge canvas for distant pairs.
    bbd = bbox_distance(a.bbox, b.bbox)
    if bbd > 120.0:
        return bbd
    x0 = min(a.x0, b.x0)
    y0 = min(a.y0, b.y0)
    x1 = max(a.x1, b.x1)
    y1 = max(a.y1, b.y1)
    canvas_b = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    canvas_a = np.zeros_like(canvas_b)
    canvas_a[a.y0 - y0 : a.y1 - y0, a.x0 - x0 : a.x1 - x0] = a.data
    canvas_b[b.y0 - y0 : b.y1 - y0, b.x0 - x0 : b.x1 - x0] = b.data
    d = distance_transform_edt(~canvas_b)
    return float(d[canvas_a].min())


def union_masks(masks: list[Mask]) -> Mask:
    if not masks:
        return Mask(0, 0, np.zeros((1, 1), dtype=bool))
    x0 = min(m.x0 for m in masks)
    y0 = min(m.y0 for m in masks)
    x1 = max(m.x1 for m in masks)
    y1 = max(m.y1 for m in masks)
    data = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    for m in masks:
        data[m.y0 - y0 : m.y1 - y0, m.x0 - x0 : m.x1 - x0] |= m.data
    return Mask(x0, y0, data)


def geometry_rect_mask(box: tuple[int, int, int, int]) -> Mask:
    x0, y0, x1, y1 = box
    return Mask(x0, y0, np.ones((max(1, y1 - y0), max(1, x1 - x0)), dtype=bool))


def subtract_mask(a: Mask, b: Mask) -> Mask:
    data = a.data.copy()
    overlap = rect_intersection(a.bbox, b.bbox)
    if overlap is not None:
        x0, y0, x1, y1 = overlap
        data[y0 - a.y0 : y1 - a.y0, x0 - a.x0 : x1 - a.x0] &= ~b.data[
            y0 - b.y0 : y1 - b.y0, x0 - b.x0 : x1 - b.x0
        ]
    return Mask(a.x0, a.y0, data)


def write_mask_png(mask: Mask, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.where(mask.data, 0, 255).astype(np.uint8), mode="L").save(path)


def make_native_roi(
    page: Image.Image, box: tuple[int, int, int, int], out_1x: Path, out_8x: Path
) -> None:
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(page.width, x1), min(page.height, y1)
    roi = page.crop((x0, y0, x1, y1))
    roi.save(out_1x)
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(out_8x)


def mask_from_char(*_args: Any, **_kwargs: Any) -> Mask:
    """DEPRECATED AND PROHIBITED: modal-bbox text masking is never admissible.

    R4 uses official-PDF CID replay plus direct official-page knockout
    difference.  This guard remains solely to make accidental reuse of
    the disallowed tight-bbox modal-background method fail loudly in review.
    """
    abort("DEPRECATED mask_from_char modal-background method must not be used")


def ray_colour_mask(
    img: np.ndarray,
    box: tuple[int, int, int, int],
    target: np.ndarray,
    backgrounds: tuple[np.ndarray, ...],
    residual_limit: float = 18.0,
    candidate: np.ndarray | None = None,
) -> Mask:
    """Extract a vector-colour foreground from the final native raster.

    A pixel must lie on an antialiasing blend ray from an actual local
    background to the known PDF vector colour.  No geometric dilation is used.
    """
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
    crop = img[y0:y1, x0:x1].astype(np.float32)
    allowed = np.zeros(crop.shape[:2], dtype=bool)
    for bg in backgrounds:
        direction = target - bg
        denom = float(np.dot(direction, direction))
        if denom == 0:
            continue
        delta = crop - bg
        alpha = np.clip(np.sum(delta * direction, axis=2) / denom, 0.0, 1.0)
        predicted = bg + alpha[..., None] * direction
        residual = np.linalg.norm(crop - predicted, axis=2)
        contrast = np.max(np.abs(crop - bg), axis=2)
        allowed |= (alpha >= 0.06) & (contrast >= 20.0) & (residual <= residual_limit)
    if candidate is not None:
        if candidate.shape != allowed.shape:
            abort(f"vector candidate shape {candidate.shape} does not match raster crop {allowed.shape}")
        allowed &= candidate
    return Mask(x0, y0, allowed)


def vector_rectangle_stroke_candidate(
    rect: fitz.Rect, width_pt: float | None, image_shape: tuple[int, ...]
) -> tuple[tuple[int, int, int, int], np.ndarray]:
    """Native sampling support for a declared PDF rectangle stroke.

    The candidate is derived directly from the centreline rectangle and its
    declared stroke width.  The extra half-pixel diagonal is solely the
    raster-cell coverage bound needed to retain true antialiasing support; the
    final mask still consists only of matching pixels present in the R95 PNG.
    It is not a morphology operation and cannot reach card-interior text.
    """
    half_pt = float(width_pt or 0.0) / 2.0
    raster_cover_pt = math.sqrt(0.5) / SCALE
    support_pt = half_pt + raster_cover_pt
    pad = math.ceil(support_pt * SCALE) + 1
    x0, y0, x1, y1 = rect_to_px(rect, pad=pad)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(image_shape[1], x1), min(image_shape[0], y1)
    xs_pt = (np.arange(x0, x1, dtype=np.float64) + 0.5) / SCALE
    ys_pt = (np.arange(y0, y1, dtype=np.float64) + 0.5) / SCALE
    distance_to_edge = np.minimum(
        np.minimum(
            np.abs(xs_pt[None, :] - rect.x0),
            np.abs(xs_pt[None, :] - rect.x1),
        ),
        np.minimum(
            np.abs(ys_pt[:, None] - rect.y0),
            np.abs(ys_pt[:, None] - rect.y1),
        ),
    )
    return (x0, y0, x1, y1), distance_to_edge <= support_pt


def resolve_same_semantic_text_glyph_ownership(
    glyphs: list[dict[str, Any]], glyph_masks: dict[str, Mask]
) -> list[dict[str, Any]]:
    """Allocate a shared raster pixel to the later actual SVG glyph paint.

    Pixel-centre ownership removes normal adjacent-bbox duplication.  If an
    antialiased pixel nevertheless appears in two glyph candidates of the same
    semantic text element (including one complete formula/caption parent), SVG <use> order is the only valid final-visible
    owner: the later source paint is visible at that exact output pixel.  This
    operation is intentionally limited to a single semantic element; pixels
    across different text elements remain untouched and are audited as a real
    relationship.  It is recorded per glyph for manual review.
    """
    rows: list[dict[str, Any]] = []
    compound_parents = {"P_FORMULA_J", "P_FORMULA_D", "P_FORMULA_T", "P_CAPTION"}
    by_element: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        owner_id = glyph["parent_id"] if glyph["parent_id"] in compound_parents else glyph["element_id"]
        by_element[owner_id].append(glyph)
    for element_id, members in by_element.items():
        # Later SVG paint has final visibility precedence.
        accepted: list[dict[str, Any]] = []
        for glyph in sorted(members, key=lambda g: int(g["svg_use_index"]), reverse=True):
            mask = glyph_masks[glyph["glyph_id"]]
            before = mask.pixels
            removed = 0
            for later in accepted:
                other = glyph_masks[later["glyph_id"]]
                overlap = rect_intersection(mask.bbox, other.bbox)
                if overlap is None:
                    continue
                x0, y0, x1, y1 = overlap
                own = mask.data[y0 - mask.y0 : y1 - mask.y0, x0 - mask.x0 : x1 - mask.x0]
                later_data = other.data[y0 - other.y0 : y1 - other.y0, x0 - other.x0 : x1 - other.x0]
                n = int(np.logical_and(own, later_data).sum())
                if n:
                    own &= ~later_data
                    removed += n
            rows.append(
                {
                    "GLYPH_ID": glyph["glyph_id"],
                    "SEMANTIC_OWNER_ID": element_id,
                    "SVG_USE_INDEX": glyph["svg_use_index"],
                    "RAW_PIXELS_BEFORE_FINAL_PAINT_OWNERSHIP": before,
                    "PIXELS_REMOVED_TO_LATER_SVG_USE": removed,
                    "RAW_PIXELS_FINAL_VISIBLE": mask.pixels,
                    "OWNERSHIP_STATUS": "PASS" if mask.pixels else "FAIL_EMPTY_AFTER_FINAL_PAINT_OWNERSHIP",
                    "RULE": "pixel-centre char bbox; any residual same-element shared pixel belongs to later actual SVG <use> paint",
                }
            )
            accepted.append(glyph)
    return sorted(rows, key=lambda r: r["GLYPH_ID"])


def element_meta(span: dict[str, Any], ordinal: int) -> dict[str, Any]:
    text = "".join(c["c"] for c in span["chars"])
    x0, y0, x1, y1 = span["bbox"]
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    source_line: int
    declared: float
    role: str
    panel = "MAIN"
    parent = f"P_SPAN_{ordinal:03d}"
    if cy < 435:
        source_line, declared, role, parent = 17, 10.6, "PANEL_TITLE", "P_TITLE"
    elif cy < 452:
        source_line, declared, role = (18, 9.6, "SEQUENCE_INDEX") if text in {"1", "2"} else (20, 9.6, "SEQUENCE_LABEL")
        parent = "P_SEQUENCE"
    elif cy < 466:
        source_line, declared, role, parent = 27, 9.6, "ARROW_LABEL", "P_SEQUENCE"
    elif cy < 501:
        source_line, declared = (32, 9.6)
        role = "NODE_INDEX" if text in {"1", "2"} else "NODE_LABEL"
        card = min(8, max(1, int((cx - 119.5) / 42.52) + 1))
        parent = f"P_NODE_{card:02d}"
    elif cy < 516:
        source_line, declared, role = 40, 9.6, "STATE_GROUP_LABEL"
        parent = "P_STATE_GROUPS"
    elif cy < 532:
        source_line, declared = 45, 10.0
        if any(ch in "𝑥x" for ch in text):
            role, parent = "FORMULA_BASE", "P_FORMULA_J"
        elif text.strip() in {"[𝑗]", "[j]"}:
            role, parent = "FORMULA_SCRIPT", "P_FORMULA_J"
        else:
            role, parent = "STATE_LABEL", "P_STATE_J"
    elif cy < 545:
        source_line, declared, role, parent = 46, 9.8, "STATE_EXPLANATION", "P_STATE_J"
    elif cy < 562:
        source_line, declared, role, parent = 56, 9.6, "STATE_CONNECTION_LABEL", "P_END_STATE"
    elif cy < 580:
        if any(ch in "𝑥x" for ch in text):
            source_line, declared, role = 52, 10.0, "FORMULA_BASE"
            parent = "P_FORMULA_D" if cx < 250 else "P_FORMULA_T"
        elif any(ch in "[]()𝑑𝑡dt" for ch in text) and not any("轮" <= ch <= "轮" for ch in text):
            source_line, declared, role = 52, 9.0, "FORMULA_SCRIPT"
            parent = "P_FORMULA_D" if "[" in text or "]" in text else "P_FORMULA_T"
        else:
            source_line, declared, role, parent = 54, 9.8, "END_SAMPLE_LABEL", "P_END_STATE"
    else:
        panel = "CAPTION"
        parent = "P_CAPTION"
        if text == "图":
            source_line, declared, role = 61, 10.0, "CAPTION_LABEL"
        elif any(ch.isdigit() for ch in text):
            source_line, declared, role = 61, 10.0, "CAPTION_NUMBER"
        else:
            source_line, declared, role = 61, 10.0, "CAPTION_TEXT"
    return {
        "element_id": f"T{ordinal:03d}",
        "parent_id": parent,
        "panel_id": panel,
        "role": role,
        "source_line": source_line,
        "declared_pt": declared,
        "effective_pt": declared,
        "text": text,
        "span_bbox_pt": tuple(float(v) for v in span["bbox"]),
        "pdf_extracted_pt": float(span["size"]),
        "font": span["font"],
        "chars": span["chars"],
    }


def classify_glyph(char: str, parent_role: str) -> tuple[str, int, str]:
    if parent_role == "FORMULA_SCRIPT":
        return "NATURAL_TEX_SCRIPT", 15, "natural script from a >=9.5pt base formula"
    if parent_role == "FORMULA_BASE" or char in {"𝑥", "x"}:
        return "BASE_MATH", 22, "base mathematical glyph"
    if char.isdigit() or ("A" <= char <= "Z"):
        return "UPPERCASE_DIGIT", 24, "uppercase/digit floor"
    if char.isalpha() and ord(char) < 128:
        return "LOWERCASE_GREEK", 17, "x-height Latin/Greek floor"
    if unicodedata.east_asian_width(char) in {"W", "F"} or "CJK" in unicodedata.name(char, ""):
        return "CJK_FULLWIDTH", 30, "CJK/full-width floor; low-stroke characters have no exception"
    if char in {"−", "+", "=", ".", ",", "，", "。", "；", ";", "…", "、", "[", "]", "(", ")"}:
        # Full-width punctuation has already been captured above.  All other
        # semantic punctuation is still independently measured.
        return "SEMANTIC_PUNCTUATION", 22, "independent semantic punctuation/operator floor"
    return "SYMBOL", 22, "visible symbol floor"


def parse_svg_glyph_uses() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, str]]:
    ns = {
        "svg": "http://www.w3.org/2000/svg",
        "xlink": "http://www.w3.org/1999/xlink",
    }
    root = ET.parse(PAGE_SVG).getroot()
    symbols: dict[str, dict[str, Any]] = {}
    symbol_xml: dict[str, str] = {}
    parents = {child: parent for parent in root.iter() for child in parent}
    for sym in root.iter("{http://www.w3.org/2000/svg}symbol"):
        ident = sym.attrib.get("id", "")
        paths = [p.attrib.get("d", "") for p in sym.iter("{http://www.w3.org/2000/svg}path")]
        symbols[ident] = {
            "shape_path_count": len(paths),
            "shape_path_char_count": sum(len(p) for p in paths),
            "shape_nonempty": bool(paths) and all(bool(p.strip()) for p in paths),
        }
        symbol_xml[ident] = ET.tostring(sym, encoding="unicode")
    uses: list[dict[str, Any]] = []
    for num, use in enumerate(root.iter("{http://www.w3.org/2000/svg}use")):
        href = use.attrib.get("{http://www.w3.org/1999/xlink}href", "")
        if not href.startswith("#glyph"):
            continue
        try:
            x = float(use.attrib["x"])
            y = float(use.attrib["y"])
        except (KeyError, ValueError):
            continue
        if FIG_RECT_PT.x0 <= x <= FIG_RECT_PT.x1 and FIG_RECT_PT.y0 <= y <= FIG_RECT_PT.y1:
            parent = parents.get(use)
            uses.append(
                {
                    "svg_use_index": num,
                    "x": x,
                    "y": y,
                    "href": href,
                    "shape_id": href[1:],
                    "parent_tag": (parent.tag.rsplit("}", 1)[-1] if parent is not None else "UNKNOWN"),
                    "parent_style": (parent.attrib.get("style", "") if parent is not None else "UNKNOWN"),
                    "parent_transform": (parent.attrib.get("transform", "") if parent is not None else "UNKNOWN"),
                    "use_transform": use.attrib.get("transform", ""),
                }
            )
    return uses, symbols, symbol_xml


def map_glyphs_to_svg(elements: list[dict[str, Any]], uses: list[dict[str, Any]], symbols: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    available = set(range(len(uses)))
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    glyph_no = 0
    for element in elements:
        for char_no, char_data in enumerate(element["chars"], start=1):
            char = char_data["c"]
            if char.isspace():
                continue
            glyph_no += 1
            ox, oy = char_data["origin"]
            candidates = [
                i
                for i in available
                if abs(uses[i]["x"] - ox) <= 1.30 and abs(uses[i]["y"] - oy) <= 1.30
            ]
            candidates.sort(key=lambda i: (abs(uses[i]["x"] - ox) + abs(uses[i]["y"] - oy), uses[i]["svg_use_index"]))
            status = "PASS"
            if len(candidates) != 1:
                status = "FAIL"
                errors.append(
                    f"glyph {element['element_id']}:{char_no} {char!r} has {len(candidates)} SVG-use candidates"
                )
                chosen = candidates[0] if candidates else None
            else:
                chosen = candidates[0]
            if chosen is not None:
                available.remove(chosen)
                svg = uses[chosen]
                shape = symbols.get(svg["shape_id"], {})
            else:
                svg = {
                    "svg_use_index": "", "x": "", "y": "", "href": "", "shape_id": "",
                    "parent_tag": "", "parent_style": "", "parent_transform": "", "use_transform": "",
                }
                shape = {"shape_path_count": 0, "shape_path_char_count": 0, "shape_nonempty": False}
            script_class, threshold, threshold_rule = classify_glyph(char, element["role"])
            rows.append(
                {
                    "glyph_id": f"{element['element_id']}:G{char_no:02d}",
                    "element_id": element["element_id"],
                    "parent_id": element["parent_id"],
                    "panel_id": element["panel_id"],
                    "role": element["role"],
                    "expected_char": char,
                    "unicode": f"U+{ord(char):04X}",
                    "char_bbox_pt": tuple(float(v) for v in char_data["bbox"]),
                    "origin_pt": (float(ox), float(oy)),
                    "svg_use_index": svg["svg_use_index"],
                    "svg_x_pt": svg["x"],
                    "svg_y_pt": svg["y"],
                    "svg_shape_id": svg["shape_id"],
                    "svg_shape_path_count": shape["shape_path_count"],
                    "svg_shape_path_char_count": shape["shape_path_char_count"],
                    "svg_shape_nonempty": shape["shape_nonempty"],
                    "svg_parent_tag": svg["parent_tag"],
                    "svg_parent_style": svg["parent_style"],
                    "svg_parent_transform": svg["parent_transform"],
                    "svg_use_transform": svg["use_transform"],
                    "script_class": script_class,
                    "threshold_px": threshold,
                    "threshold_rule": threshold_rule,
                    "mapping_status": status,
                }
            )
    if available:
        errors.append(f"{len(available)} unclaimed SVG glyph-use objects in figure scope")
    # A PDF font glyph path must not silently serve two different Unicode chars.
    by_shape: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["svg_shape_id"]:
            by_shape[row["svg_shape_id"]].add(row["expected_char"])
    for shape_id, chars in by_shape.items():
        if len(chars) != 1:
            errors.append(f"SVG shape {shape_id} maps to multiple chars: {sorted(chars)!r}")
    for row in rows:
        if not row["svg_shape_nonempty"]:
            errors.append(f"{row['glyph_id']} resolves to empty/nonexistent SVG shape")
    return rows, errors


def glyph_shape_mask_from_svg(
    glyph: dict[str, Any],
    symbol_xml: dict[str, str],
    image_shape: tuple[int, ...],
    page_rect: fitz.Rect,
) -> Mask:
    """DEPRECATED R4 diagnostic only; never called by an R4 terminal audit.

    Rasterize exactly one mapped SVG glyph path onto its native page grid.

    This is traceable *shape isolation*, not a replacement measurement image:
    the generated alpha support merely identifies the one glyph path.  The
    actual raw foreground values and all H/overlap measurements still come
    exclusively from the direct official-R95 `full_page_300dpi.png` pixels.
    """
    shape_id = glyph["svg_shape_id"]
    if shape_id not in symbol_xml:
        return Mask(0, 0, np.zeros((1, 1), dtype=bool))
    x0, y0, x1, y1 = glyph["char_bbox_px"]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(image_shape[1], x1), min(image_shape[0], y1)
    if x1 <= x0 or y1 <= y0:
        return Mask(x0, y0, np.zeros((1, 1), dtype=bool))
    width, height = x1 - x0, y1 - y0
    parent_style = glyph.get("svg_parent_style", "")
    parent_transform = glyph.get("svg_parent_transform", "")
    use_transform = glyph.get("svg_use_transform", "")
    # The SVG text colour is immaterial to alpha support, but retaining the
    # actual parent style/transform makes the CHAR -> <use> -> parent -> path
    # chain explicit and correct for opacity/transformed use cases.
    parent_attrs = f' style="{parent_style}"' if parent_style else ""
    if parent_transform:
        parent_attrs += f' transform="{parent_transform}"'
    use_attrs = f' transform="{use_transform}"' if use_transform else ""
    # Preserve the official A4 origin and page size.  A mini-SVG made from the
    # character bbox would have a different Cairo pixel phase than the direct
    # 300dpi official page.  This full-page one-glyph SVG is converted to PDF
    # then rasterised with the *same pdftocairo engine* used for the official
    # native page, cropped at the same integer pixel coordinates.
    isolated_svg = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{page_rect.width:.12f}pt" height="{page_rect.height:.12f}pt" '
        f'viewBox="0 0 {page_rect.width:.12f} {page_rect.height:.12f}">'
        f'<defs>{symbol_xml[shape_id]}</defs>'
        f'<g{parent_attrs}><use xlink:href="#{shape_id}" x="{glyph["svg_x_pt"]}" y="{glyph["svg_y_pt"]}"{use_attrs}/></g>'
        '</svg>'
    )
    try:
        svg_doc = fitz.open("svg", isolated_svg.encode("utf-8"))
        glyph_pdf_bytes = svg_doc.convert_to_pdf()
        # pdftocairo is the direct official-R95 rasteriser.  The temporary
        # files are isolated scratch data, not evidence outputs; only the
        # resulting binary support is diagnostic only and is not persisted by R4.
        with tempfile.TemporaryDirectory(prefix="fig_p634_glyph_") as tmp:
            tmp_dir = Path(tmp)
            pdf_path = tmp_dir / "isolated_glyph.pdf"
            out_base = tmp_dir / "isolated_glyph"
            pdf_path.write_bytes(glyph_pdf_bytes)
            completed = subprocess.run(
                [
                    "pdftocairo", "-png", "-singlefile", "-transp",
                    "-r", str(DPI * PATH_SUPPORT_SUPERSAMPLE),
                    "-x", str(x0 * PATH_SUPPORT_SUPERSAMPLE),
                    "-y", str(y0 * PATH_SUPPORT_SUPERSAMPLE),
                    "-W", str(width * PATH_SUPPORT_SUPERSAMPLE),
                    "-H", str(height * PATH_SUPPORT_SUPERSAMPLE),
                    str(pdf_path), str(out_base),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"pdftocairo isolation exited {completed.returncode}: {completed.stderr.strip()}"
                )
            out_png = out_base.with_suffix(".png")
            if not out_png.exists():
                raise RuntimeError("pdftocairo isolation produced no PNG")
            with Image.open(out_png) as isolated_image:
                rgba = np.asarray(isolated_image.convert("RGBA"))
        expected_width = width * PATH_SUPPORT_SUPERSAMPLE
        expected_height = height * PATH_SUPPORT_SUPERSAMPLE
        if rgba.shape[1] != expected_width or rgba.shape[0] != expected_height:
            raise RuntimeError(
                f"isolated glyph raster grid {rgba.shape[1]}x{rgba.shape[0]}, expected {expected_width}x{expected_height}"
            )
        alpha_hi = rgba[:, :, 3]
        # This reduction records only which original vector path intersects a
        # native raster cell.  It does not add neighbours to a mask; it avoids
        # a renderer-specific antialias threshold discarding a true final
        # visible pixel at a glyph edge.
        alpha = alpha_hi.reshape(
            height, PATH_SUPPORT_SUPERSAMPLE, width, PATH_SUPPORT_SUPERSAMPLE
        ).any(axis=(1, 3))
        if not alpha.any():
            raise RuntimeError("isolated Cairo glyph alpha support is empty")
    except Exception as exc:  # noqa: BLE001 -- an isolation failure is evidence failure, not fallback.
        print(f"GLYPH_SVG_ISOLATION_ERROR {glyph['glyph_id']}: {exc}", file=sys.stderr)
        return Mask(x0, y0, np.zeros((height, width), dtype=bool))
    return Mask(x0, y0, alpha > 0)


def parse_svg_fill(style: str) -> tuple[np.ndarray | None, float | None]:
    """Recover the actual SVG parent fill and opacity for a mapped glyph."""
    rgb_match = re.search(
        r"(?:^|;)\s*fill\s*:\s*rgb\(\s*([0-9.]+)(%)?\s*,\s*([0-9.]+)(%)?\s*,\s*([0-9.]+)(%)?\s*\)",
        style,
    )
    if not rgb_match:
        return None, None
    values: list[float] = []
    groups = rgb_match.groups()
    for value, percent in ((groups[0], groups[1]), (groups[2], groups[3]), (groups[4], groups[5])):
        v = float(value)
        # Do not guess channel units from a magnitude: `rgb(31,35,40)` and
        # `rgb(31%,35%,40%)` are materially different parent paint colours.
        values.append(v * 2.55 if percent else v)
    if any(v < 0.0 or v > 255.0 for v in values):
        return None, None
    opacity_match = re.search(r"(?:^|;)\s*fill-opacity\s*:\s*([0-9.]+)", style)
    opacity = float(opacity_match.group(1)) if opacity_match else 1.0
    if not (0.0 <= opacity <= 1.0):
        return None, None
    return np.array(values, dtype=np.float32), opacity


def glyph_known_background(glyph: dict[str, Any]) -> tuple[np.ndarray, str]:
    """Return the source/paint-order-provable background beneath this glyph."""
    parent = glyph["parent_id"]
    if parent in {"P_NODE_01", "P_NODE_02", "P_NODE_03", "P_NODE_04"}:
        return RGB_WHITE, "true opaque sl634-halo fill=white drawn after done-card pattern"
    if parent == "P_NODE_05":
        return RGB_GOLD_BG, "sl634-now final node fill=SLGoldBg"
    if parent in {"P_NODE_06", "P_NODE_07", "P_NODE_08"}:
        return RGB_WHITE, "sl634-old final node fill=white"
    return RGB_WHITE, "white page or final white state-card background (source / final vector paint order)"


def known_background_colour_ray_mask(
    img: np.ndarray,
    rect: fitz.Rect,
    fill: np.ndarray,
    opacity: float,
    background: np.ndarray,
    residual_limit: float = 14.0,
) -> Mask:
    """Select actual 300dpi effective text ink from known fill/background.

    Unlike a tight-bbox modal colour, this uses the mapped SVG glyph's actual
    paint colour plus a source/paint-order-proven underlay.  Thus high-coverage
    CJK characters cannot invert the background estimate and a hatch/border of
    another colour cannot become text ink.  The output remains on the official
    R95 native pixel grid and applies the required >=20/255 contrast floor.
    """
    x0, y0, x1, y1 = rect_to_px(rect, pad=0)
    x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
    if x1 <= x0 or y1 <= y0:
        return Mask(x0, y0, np.zeros((1, 1), dtype=bool))
    crop = img[y0:y1, x0:x1].astype(np.float32)
    target = opacity * fill + (1.0 - opacity) * background
    direction = target - background
    denom = float(np.dot(direction, direction))
    if denom <= 0.0:
        return Mask(x0, y0, np.zeros(crop.shape[:2], dtype=bool))
    delta = crop - background
    alpha = np.sum(delta * direction, axis=2) / denom
    predicted = background + np.clip(alpha, 0.0, 1.0)[..., None] * direction
    residual = np.linalg.norm(crop - predicted, axis=2)
    contrast = np.max(np.abs(crop - background), axis=2)
    xs_pt = (np.arange(x0, x1, dtype=np.float64) + 0.5) / SCALE
    ys_pt = (np.arange(y0, y1, dtype=np.float64) + 0.5) / SCALE
    owned = (
        (xs_pt[None, :] >= rect.x0)
        & (xs_pt[None, :] < rect.x1)
        & (ys_pt[:, None] >= rect.y0)
        & (ys_pt[:, None] < rect.y1)
    )
    allowed = (
        (alpha >= 0.0)
        & (alpha <= 1.05)
        & (contrast >= 20.0)
        & (residual <= residual_limit)
        & owned
    )
    return Mask(x0, y0, allowed)


def translate_binary_mask(data: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """Translate only existing native pixels; no wrapping or morphology."""
    result = np.zeros_like(data)
    src_x0, src_x1 = max(0, -dx), min(data.shape[1], data.shape[1] - dx)
    src_y0, src_y1 = max(0, -dy), min(data.shape[0], data.shape[0] - dy)
    if src_x1 <= src_x0 or src_y1 <= src_y0:
        return result
    dst_x0, dst_x1 = src_x0 + dx, src_x1 + dx
    dst_y0, dst_y1 = src_y0 + dy, src_y1 + dy
    result[dst_y0:dst_y1, dst_x0:dst_x1] = data[src_y0:src_y1, src_x0:src_x1]
    return result


def register_svg_path_to_native_text(
    glyph: dict[str, Any], unregistered: Mask, colour_ray: Mask
) -> tuple[Mask, dict[str, Any]]:
    """DEPRECATED R4 diagnostic only; never called by an R4 terminal audit.

    Register auxiliary SVG support to the final R95 pixel lattice.

    The SVG renderer is used only to trace the glyph path and has a documented
    sub-pixel origin phase different from Poppler's direct PDF raster.  For
    each already-mapped CHAR/use, a bounded +/-4 native-pixel translation is
    selected against the *known-fill colour-ray* of the same official page.
    It changes neither the path geometry nor the final-page pixels, and every
    registration/coverage value is written for independent review.
    """
    if unregistered.bbox != colour_ray.bbox or not colour_ray.pixels or not unregistered.pixels:
        return Mask(unregistered.x0, unregistered.y0, np.zeros_like(unregistered.data)), {
            "dx": "", "dy": "", "intersection": 0, "colour_coverage": 0.0,
            "shape_coverage": 0.0, "status": "FAIL_EMPTY_OR_BBOX_MISMATCH",
        }
    candidates: list[tuple[int, int, int, int, float, float]] = []
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            shifted = translate_binary_mask(unregistered.data, dx, dy)
            support = int(shifted.sum())
            inter = int(np.logical_and(shifted, colour_ray.data).sum())
            colour_cov = inter / colour_ray.pixels if colour_ray.pixels else 0.0
            shape_cov = inter / support if support else 0.0
            candidates.append((inter, -abs(dx) - abs(dy), dx, dy, colour_cov, shape_cov))
    # Highest intersection, then smallest displacement; all ties remain
    # explicit below rather than being silently treated as one mapping.
    candidates.sort(reverse=True)
    best_inter, _, dx, dy, colour_cov, shape_cov = candidates[0]
    tie_count = sum(1 for row in candidates if row[0] == best_inter and row[1] == candidates[0][1])
    registered = Mask(
        unregistered.x0, unregistered.y0, translate_binary_mask(unregistered.data, dx, dy)
    )
    # Each known-fill, >=20/255 final-visible stroke pixel for this mapped
    # CHAR must be explained by its registered actual SVG path.  A percentage
    # tolerance would hide a missing CJK stroke, so exact integer equality is
    # required.  The corresponding missing mask is persisted by the caller.
    status = "PASS" if best_inter == colour_ray.pixels and tie_count == 1 else "FAIL_INCOMPLETE_OR_AMBIGUOUS"
    return registered, {
        "dx": dx,
        "dy": dy,
        "intersection": best_inter,
        "colour_coverage": colour_cov,
        "shape_coverage": shape_cov,
        "status": status,
    }


def drawing_label(idx: int) -> tuple[str, str, np.ndarray | None, tuple[np.ndarray, ...], bool]:
    """ID, category, stroke colour, valid local backgrounds, foreground flag."""
    if idx == 0:
        return "G_ARROW_SEQUENCE_LINE", "LINE_ARROW", RGB_SL_GRAY, (RGB_WHITE,), True
    if idx == 1:
        return "G_ARROW_SEQUENCE_HEAD", "ARROWHEAD", RGB_SL_GRAY, (RGB_WHITE,), True
    if 2 <= idx <= 5:
        return f"G_NODE_DONE_{idx - 1}_BORDER", "NODE_BORDER", RGB_SL_BLUE, (RGB_WHITE, RGB_BLUE_BG), True
    if 6 <= idx <= 9:
        return f"B_NODE_DONE_{idx - 5}_HALO", "OPAQUE_HALO_BACKGROUND", None, (), False
    if idx == 10:
        return "G_NODE_CURRENT_BORDER", "NODE_BORDER", RGB_SL_GOLD, (RGB_WHITE, RGB_GOLD_BG), True
    if 11 <= idx <= 13:
        return f"G_NODE_OLD_{idx - 10}_BORDER", "NODE_BORDER", RGB_SL_RULE, (RGB_WHITE,), True
    if idx == 14:
        return "G_STATE_CARD_J_BORDER", "PANEL_BORDER", RGB_SL_RULE, (RGB_WHITE,), True
    if idx == 15:
        return "G_STATE_CARD_END_BORDER", "PANEL_BORDER", RGB_SL_RULE, (RGB_WHITE,), True
    if idx == 16:
        return "G_ARROW_SAME_LINE", "LINE_ARROW", RGB_SL_GRAY, (RGB_WHITE,), True
    if idx == 17:
        return "G_ARROW_SAME_LEFT_HEAD", "ARROWHEAD", RGB_SL_GRAY, (RGB_WHITE,), True
    if idx == 18:
        return "G_ARROW_SAME_RIGHT_HEAD", "ARROWHEAD", RGB_SL_GRAY, (RGB_WHITE,), True
    if idx == 19:
        return "G_ARROW_RECORD_LINE", "LINE_ARROW", RGB_SL_GRAY, (RGB_WHITE,), True
    if idx == 20:
        return "G_ARROW_RECORD_HEAD", "ARROWHEAD", RGB_SL_GRAY, (RGB_WHITE,), True
    return f"G_UNEXPECTED_{idx:02d}", "UNKNOWN", None, (), False


def build_graphics(page: fitz.Page, img: np.ndarray) -> tuple[list[dict[str, Any]], list[str]]:
    drawings = [
        d
        for d in page.get_drawings()
        if (FIG_RECT_PT.y0 <= d["rect"].y0 <= FIG_RECT_PT.y1)
        or (FIG_RECT_PT.y0 <= d["rect"].y1 <= FIG_RECT_PT.y1)
    ]
    errors: list[str] = []
    if len(drawings) != 21:
        errors.append(f"expected 21 final-PDF vector drawings in figure scope, found {len(drawings)}")
    graphics: list[dict[str, Any]] = []
    for idx, drawing in enumerate(drawings):
        ident, category, target, bgs, foreground = drawing_label(idx)
        raw_rect = drawing["rect"]
        box = rect_to_px(raw_rect, pad=3)
        if category == "OPAQUE_HALO_BACKGROUND":
            mask = geometry_rect_mask(rect_to_px(raw_rect, pad=0))
        elif target is not None:
            if category in {"NODE_BORDER", "PANEL_BORDER"}:
                box, stroke_candidate = vector_rectangle_stroke_candidate(
                    raw_rect, drawing.get("width"), img.shape
                )
                mask = ray_colour_mask(img, box, target, bgs, candidate=stroke_candidate)
            else:
                mask = ray_colour_mask(img, box, target, bgs)
        else:
            mask = Mask(0, 0, np.zeros((1, 1), dtype=bool))
        graphics.append(
            {
                "id": ident,
                "category": category,
                "role": category,
                "panel_id": "MAIN",
                "drawing_index": idx,
                "display_seqno": drawing.get("seqno", "UNKNOWN"),
                "bbox_pt": tuple(float(v) for v in raw_rect),
                "bbox_px": box,
                "mask": mask,
                "foreground": foreground,
                "paint_order": idx,
                "stroke_rgb": tuple(int(round(255 * v)) for v in drawing.get("color") or ()) or None,
                "fill_rgb": tuple(int(round(255 * v)) for v in drawing.get("fill") or ()) or None,
                "width_pt": drawing.get("width"),
                "dashes": drawing.get("dashes"),
            }
        )
    # The four patterned done cards are final-visible texture foregrounds. Their
    # only legal occluders are the four source-declared white halo backgrounds.
    done_borders = [g for g in graphics if g["id"].startswith("G_NODE_DONE_")]
    halos = [g for g in graphics if g["category"] == "OPAQUE_HALO_BACKGROUND"]
    for n, border in enumerate(done_borders, start=1):
        pre = geometry_rect_mask(rect_to_px(fitz.Rect(border["bbox_pt"]), pad=0))
        halo = halos[n - 1]["mask"] if n <= len(halos) else Mask(0, 0, np.zeros((1, 1), dtype=bool))
        final_bg = subtract_mask(pre, halo)
        # Exclude the border band and retain only visible pattern pixels in the
        # pre-minus-halo region.  It comes from the final native page, not an
        # invented dilation or a white-box erasure.
        pattern_candidate = ray_colour_mask(
            img,
            pre.bbox,
            RGB_SL_RULE,
            (RGB_WHITE, RGB_BLUE_BG),
            residual_limit=24.0,
        )
        # Keep the actual textured inner card region first, before any halo
        # classification.  This is a real final-page colour mask, not the
        # rectangle geometry; it lets the text audit attribute a colour-ray
        # false candidate to texture even where it lies spatially in a halo.
        pre_local = np.zeros_like(pattern_candidate.data)
        pre_overlap = rect_intersection(pattern_candidate.bbox, pre.bbox)
        if pre_overlap is not None:
            x0, y0, x1, y1 = pre_overlap
            pre_local[y0 - pattern_candidate.y0 : y1 - pattern_candidate.y0, x0 - pattern_candidate.x0 : x1 - pattern_candidate.x0] = pre.data[
                y0 - pre.y0 : y1 - pre.y0, x0 - pre.x0 : x1 - pre.x0
            ]
        # Keep only the actual post-halo inner card region.  Remove the outer
        # border with direct rectangle geometry; this is a classification step,
        # not a mask expansion used for measurement.
        final_local = np.zeros_like(pattern_candidate.data)
        overlap = rect_intersection(pattern_candidate.bbox, final_bg.bbox)
        if overlap is not None:
            x0, y0, x1, y1 = overlap
            final_local[y0 - pattern_candidate.y0 : y1 - pattern_candidate.y0, x0 - pattern_candidate.x0 : x1 - pattern_candidate.x0] = final_bg.data[
                y0 - final_bg.y0 : y1 - final_bg.y0, x0 - final_bg.x0 : x1 - final_bg.x0
            ]
        # Four native pixels is enough to remove the known 0.95pt outline
        # support without dilating any foreground mask.
        if pre_local.shape[0] > 8 and pre_local.shape[1] > 8:
            pre_local[:4, :] = False
            pre_local[-4:, :] = False
            pre_local[:, :4] = False
            pre_local[:, -4:] = False
            final_local[:4, :] = False
            final_local[-4:, :] = False
            final_local[:, :4] = False
            final_local[:, -4:] = False
        pre_pattern = Mask(pattern_candidate.x0, pattern_candidate.y0, pattern_candidate.data & pre_local)
        pattern = Mask(pattern_candidate.x0, pattern_candidate.y0, pattern_candidate.data & final_local)
        graphics.append(
            {
                "id": f"G_NODE_DONE_{n}_PATTERN_FINAL_VISIBLE",
                "category": "BACKGROUND_TEXTURE",
                "role": "BACKGROUND_TEXTURE",
                "panel_id": "MAIN",
                "drawing_index": f"pattern-{n}",
                # MuPDF's display list records the tiling-pattern operation
                # immediately before each border as the preceding sequence
                # number.  Its bbox is clipped / unreliable, so retain both
                # the exact display sequence and the card-border path anchor.
                "display_seqno": int(border["display_seqno"]) - 1 if isinstance(border.get("display_seqno"), int) else "UNKNOWN",
                "owner_path_anchor": f"DRAWING_INDEX={border['drawing_index']};DISPLAY_SEQNO={border['display_seqno']}",
                "bbox_pt": border["bbox_pt"],
                "bbox_px": pre.bbox,
                "mask": pattern,
                "foreground": True,
                "paint_order": 5.5 + n / 10.0,
                "stroke_rgb": (184, 192, 200),
                "fill_rgb": None,
                "width_pt": None,
                "dashes": None,
                "pre_mask": pre,
                "pre_pattern_mask": pre_pattern,
                "halo_mask": halo,
                "final_background_mask": final_bg,
            }
        )
    return graphics, errors


def bind_glyphs_to_texttrace_seqno(page: fitz.Page, glyphs: list[dict[str, Any]]) -> list[str]:
    """Attach every mapped PDF CHAR to a real display-list text sequence.

    Texttrace glyph codes can be font-encoded rather than Unicode, therefore
    the binding uses the official PDF CHAR rectangle and requires a unique
    maximum overlap with a texttrace run.  The resulting seqno is used only
    for paint-order evidence, never for a bitmap-derived mask.
    """
    errors: list[str] = []
    traces = [trace for trace in page.get_texttrace() if trace.get("type") == 0]
    for glyph in glyphs:
        target = fitz.Rect(glyph["char_bbox_pt"])
        candidates: list[tuple[float, float, dict[str, Any]]] = []
        for trace in traces:
            trace_rect = fitz.Rect(trace["bbox"])
            overlap = target & trace_rect
            if overlap.is_empty:
                continue
            area = float(overlap.get_area())
            if area <= 0:
                continue
            candidates.append((area, -float(trace_rect.get_area()), trace))
        candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
        if not candidates:
            glyph["pdf_texttrace_seqno"] = "UNKNOWN"
            glyph["pdf_texttrace_mapping_pass"] = False
            errors.append(f"{glyph['glyph_id']} has no texttrace display-sequence overlap")
            continue
        best_area, _inverse_area, best = candidates[0]
        ties = sum(1 for area, _, _ in candidates if abs(area - best_area) < 1e-6)
        seqno = best.get("seqno")
        passed = isinstance(seqno, int) and ties == 1
        glyph["pdf_texttrace_seqno"] = seqno if passed else "UNKNOWN"
        glyph["pdf_texttrace_bbox_pt"] = tuple(float(value) for value in best["bbox"])
        glyph["pdf_texttrace_overlap_pt2"] = best_area
        glyph["pdf_texttrace_mapping_pass"] = passed
        if not passed:
            errors.append(f"{glyph['glyph_id']} ambiguous/unknown texttrace seqno candidates={len(candidates)} ties={ties}")
    return errors


def build_relation_text_objects(text_objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create the text objects used in mandatory external relations.

    PDF extraction emits a formula base and its natural script as separate
    spans.  They are children of one complete semantic formula and must not be
    measured against one another as independent TEXT_TEXT objects.  Likewise,
    the two caption lines and their label/number fragments are one caption
    paragraph under the explicit natural-wrap exception.  Their raw child
    masks remain separately inventoried and audited; only the relation object
    is the complete semantic parent.
    """
    compound = {
        "P_FORMULA_J": ("FORMULA", "FORMULA_COMPLETE"),
        "P_FORMULA_D": ("FORMULA", "FORMULA_COMPLETE"),
        "P_FORMULA_T": ("FORMULA", "FORMULA_COMPLETE"),
        "P_CAPTION": ("TEXT", "CAPTION_PARAGRAPH"),
    }
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obj in text_objects:
        by_parent[obj["parent_id"]].append(obj)
    result: list[dict[str, Any]] = []
    emitted: set[str] = set()
    for obj in text_objects:
        parent = obj["parent_id"]
        if parent not in compound:
            clone = dict(obj)
            clone["relation_members"] = obj["id"]
            clone["relation_object_kind"] = "SINGLE_SEMANTIC_TEXT_ELEMENT"
            result.append(clone)
            continue
        if parent in emitted:
            continue
        members = by_parent[parent]
        category, role = compound[parent]
        result.append(
            {
                "id": parent,
                "category": category,
                "role": role,
                "panel_id": members[0]["panel_id"],
                "parent_id": parent,
                "mask": union_masks([m["mask"] for m in members]),
                "bbox_px": union_masks([m["mask"] for m in members]).bbox,
                "foreground": True,
                "element": None,
                "relation_members": ";".join(m["id"] for m in members),
                "relation_object_kind": "COMPLETE_SEMANTIC_PARENT",
            }
        )
        emitted.add(parent)
    return result


def mask_crop(mask: Mask, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    result = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    overlap = rect_intersection(mask.bbox, box)
    if overlap is None:
        return result
    ox0, oy0, ox1, oy1 = overlap
    result[oy0 - y0 : oy1 - y0, ox0 - x0 : ox1 - x0] = mask.data[
        oy0 - mask.y0 : oy1 - mask.y0, ox0 - mask.x0 : ox1 - mask.x0
    ]
    return result


def attribute_nonpath_colour_candidates(
    glyph: dict[str, Any], nonpath: Mask, graphics: list[dict[str, Any]], img: np.ndarray, alpha: np.ndarray
) -> tuple[list[dict[str, Any]], Mask]:
    """Resolve *each* rejected colour-ray pixel to a PDF paint owner.

    The colour ray is diagnostic only.  A pixel that it proposed but the
    official target-CID replay rejects is preserved in this ledger, with its
    global native coordinate, actual RGB, target alpha, actual graphic mask,
    display-list sequence and pre/post-target ordering.  This prevents a
    striped card texture from being waved away as a generic "grey candidate".
    Pixels with no concrete owner stay in the returned UNKNOWN mask.
    """
    evidence: list[dict[str, Any]] = []
    for graphic in graphics:
        evidence.append(
            {
                "evidence_id": graphic["id"],
                "mask": graphic["mask"],
                "owner_phase": "FINAL_VISIBLE_GRAPHIC",
                "graphic": graphic,
            }
        )
        if "pre_pattern_mask" in graphic:
            evidence.append(
                {
                    "evidence_id": f"{graphic['id']}:PRE_HALO_TEXTURE",
                    "mask": graphic["pre_pattern_mask"],
                    "owner_phase": "PRE_HALO_TEXTURE_ON_FINAL_PAGE",
                    "graphic": graphic,
                }
            )
    local_evidence = [(item, mask_crop(item["mask"], nonpath.bbox)) for item in evidence]
    covered = np.zeros_like(nonpath.data)
    rows: list[dict[str, Any]] = []
    target_seqno = glyph.get("pdf_texttrace_seqno")
    for local_y, local_x in zip(*np.nonzero(nonpath.data)):
        candidates = [(item, local[local_y, local_x]) for item, local in local_evidence if local[local_y, local_x]]
        global_x = nonpath.x0 + int(local_x)
        global_y = nonpath.y0 + int(local_y)
        if not candidates:
            rows.append(
                {
                    "GLYPH_ID": glyph["glyph_id"],
                    "EXPECTED_CHAR": glyph["expected_char"],
                    "X_NATIVE": global_x,
                    "Y_NATIVE": global_y,
                    "PAGE_RGB": ",".join(str(int(value)) for value in img[global_y, global_x, :3]),
                    "TARGET_REPLAY_ALPHA": int(alpha[local_y, local_x]),
                    "TARGET_ALPHA_GE20": bool(alpha[local_y, local_x] >= 20),
                    "EVIDENCE_ID": "UNKNOWN",
                    "OWNER_DRAWING_INDEX": "UNKNOWN",
                    "OWNER_DISPLAY_SEQNO": "UNKNOWN",
                    "OWNER_PATH_ANCHOR": "UNKNOWN",
                    "OWNER_PHASE": "UNKNOWN",
                    "TARGET_TEXTTRACE_SEQNO": target_seqno,
                    "PAINT_ORDER_PROOF": "FAIL_NO_OWNER",
                    "DISPOSITION": "FAIL_UNEXPLAINED_COLOUR_RAY_NONPATH_PIXEL",
                }
            )
            continue
        # Prefer the most specific pre-halo texture mask, then an actual
        # final-visible graphic.  This order is deterministic and is disclosed
        # rather than relying on an arbitrary overlapping colour mask.
        candidates.sort(key=lambda pair: 0 if pair[0]["owner_phase"].startswith("PRE_HALO") else 1)
        item = candidates[0][0]
        graphic = item["graphic"]
        owner_seqno = graphic.get("display_seqno", "UNKNOWN")
        if isinstance(owner_seqno, int) and isinstance(target_seqno, int):
            paint_order = (
                "OWNER_BEFORE_TARGET_TEXT" if owner_seqno < target_seqno
                else "OWNER_AFTER_TARGET_TEXT_TRUE_OCCLUSION_OR_NON_TARGET"
            )
        else:
            paint_order = "UNKNOWN_SEQUENCE"
        rows.append(
            {
                "GLYPH_ID": glyph["glyph_id"],
                "EXPECTED_CHAR": glyph["expected_char"],
                "X_NATIVE": global_x,
                "Y_NATIVE": global_y,
                "PAGE_RGB": ",".join(str(int(value)) for value in img[global_y, global_x, :3]),
                "TARGET_REPLAY_ALPHA": int(alpha[local_y, local_x]),
                "TARGET_ALPHA_GE20": bool(alpha[local_y, local_x] >= 20),
                "EVIDENCE_ID": item["evidence_id"],
                "OWNER_DRAWING_INDEX": graphic.get("drawing_index", "UNKNOWN"),
                "OWNER_DISPLAY_SEQNO": owner_seqno,
                "OWNER_PATH_ANCHOR": graphic.get("owner_path_anchor", f"DRAWING_INDEX={graphic.get('drawing_index', 'UNKNOWN')}"),
                "OWNER_PHASE": item["owner_phase"],
                "TARGET_TEXTTRACE_SEQNO": target_seqno,
                "PAINT_ORDER_PROOF": paint_order,
                "DISPOSITION": "ATTRIBUTED_NON_TARGET_PIXEL",
            }
        )
        covered[local_y, local_x] = True
    remaining = Mask(nonpath.x0, nonpath.y0, nonpath.data & ~covered)
    return rows, remaining


def save_relation_package(
    page: Image.Image,
    relation: dict[str, Any],
    a: Mask,
    b: Mask,
    rel_dir: Path,
) -> None:
    pad = 8
    box = (
        max(0, min(a.x0, b.x0) - pad),
        max(0, min(a.y0, b.y0) - pad),
        min(page.width, max(a.x1, b.x1) + pad),
        min(page.height, max(a.y1, b.y1) + pad),
    )
    stem = safe_file_stem(relation["relation_id"])
    make_native_roi(page, box, rel_dir / f"{stem}_native_1x.png", rel_dir / f"{stem}_8x_nearest.png")
    aa = mask_crop(a, box)
    bb = mask_crop(b, box)
    both = aa & bb
    # A=cyan, B=magenta, intersection=red; the masks retain native pixel grid.
    overlay = np.full((aa.shape[0], aa.shape[1], 3), 255, dtype=np.uint8)
    overlay[aa] = (0, 190, 220)
    overlay[bb] = (210, 0, 190)
    overlay[both] = (230, 0, 0)
    Image.fromarray(overlay).save(rel_dir / f"{stem}_A_B_intersection.png")
    write_mask_png(Mask(box[0], box[1], aa), rel_dir / f"{stem}_A_raw.png")
    write_mask_png(Mask(box[0], box[1], bb), rel_dir / f"{stem}_B_raw.png")
    write_mask_png(Mask(box[0], box[1], both), rel_dir / f"{stem}_intersection_raw.png")


def pick_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\DejaVuSans.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def create_glyph_contact_sheets(
    page: Image.Image,
    glyphs: list[dict[str, Any]],
    glyph_masks: dict[str, Mask],
    raw_mask_sha_by_glyph: dict[str, str],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Make 8x-nearest proof sheets for every CHAR -> raw-mask binding.

    Every cell contains (1) original native context, (2) the exact final raw
    glyph mask painted red over that context, and (3) mask-only.  No contact
    sheet is used for a measurement; it is a human verification artifact for
    the mapped shape and contamination-free mask.
    """
    out_dir = ROOT / "glyph_contact_sheets"
    out_dir.mkdir(exist_ok=True)
    font = pick_font(16)
    sheet_names: list[str] = []
    coverage: list[dict[str, Any]] = []
    per_sheet, cols = 14, 2
    cell_w, cell_h = 1400, 660
    for start in range(0, len(glyphs), per_sheet):
        batch = glyphs[start : start + per_sheet]
        rows = math.ceil(len(batch) / cols)
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for ix, glyph in enumerate(batch):
            col, row = ix % cols, ix // cols
            ox, oy = col * cell_w, row * cell_h
            rect = glyph["char_bbox_px"]
            # Context adds only three canonical native pixels around the exact
            # char bbox.  Enlargement is integer 8x nearest-neighbour.
            box = (max(0, rect[0] - 3), max(0, rect[1] - 3), min(page.width, rect[2] + 3), min(page.height, rect[3] + 3))
            crop = page.crop(box)
            raw = mask_crop(glyph_masks[glyph["glyph_id"]], box)
            original_8x = crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST)
            overlay_arr = np.asarray(crop).copy()
            overlay_arr[raw] = (255, 0, 0)
            overlay_8x = Image.fromarray(overlay_arr).resize(
                (crop.width * 8, crop.height * 8), Image.Resampling.NEAREST
            )
            mask_only = Image.fromarray(np.where(raw, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            mask_only_8x = mask_only.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST)
            panel_w = original_8x.width
            if panel_w * 3 + 50 > cell_w or original_8x.height + 60 > cell_h:
                abort(f"contact-sheet cell too small for exact 8x glyph {glyph['glyph_id']}")
            px0 = ox + 20
            py0 = oy + 42
            sheet.paste(original_8x, (px0, py0))
            sheet.paste(overlay_8x, (px0 + panel_w + 15, py0))
            sheet.paste(mask_only_8x, (px0 + 2 * (panel_w + 15), py0))
            draw.text(
                (ox + 5, oy + 4),
                f"{glyph['glyph_id']} {glyph['unicode']}  CHAR={glyph['expected_char']}  SHAPE={glyph['svg_shape_id']}  PARENT={glyph['parent_id']}",
                fill=(0, 0, 0), font=font,
            )
            draw.text((px0, oy + 24), "ORIGINAL 8x", fill=(0, 0, 0), font=font)
            draw.text((px0 + panel_w + 15, oy + 24), "TARGET RAW MASK (RED) 8x", fill=(150, 0, 0), font=font)
            draw.text((px0 + 2 * (panel_w + 15), oy + 24), "MASK ONLY 8x", fill=(0, 0, 0), font=font)
            draw.rectangle((ox, oy, ox + cell_w - 1, oy + cell_h - 1), outline=(150, 150, 150), width=1)
            coverage.append(
                {
                    "GLYPH_ID": glyph["glyph_id"],
                    "EXPECTED_CHAR": glyph["expected_char"],
                    "UNICODE": glyph["unicode"],
                    "SVG_SHAPE_ID": glyph["svg_shape_id"],
                    "SHEET": f"glyph_mapping_{start // per_sheet + 1:02d}_8x_nearest.png",
                    "CELL_INDEX": ix + 1,
                    "ORIGINAL_CONTEXT": "present",
                    "TARGET_MASK_RED_OVERLAY": "present",
                    "MASK_ONLY": "present",
                    "RAW_MASK_SHA256": raw_mask_sha_by_glyph[glyph["glyph_id"]],
                    "MANUAL_8X_REVIEW": "PENDING_PER_GLYPH_LEDGER",
                    "MANUAL_NOTE": "requires SA1 per-glyph 8x inspection before terminal decision",
                }
            )
        name = f"glyph_mapping_{start // per_sheet + 1:02d}_8x_nearest.png"
        sheet.save(out_dir / name)
        sheet_names.append(str((Path("glyph_contact_sheets") / name).as_posix()))
    return sheet_names, coverage


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else ["EMPTY"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_glyph_file_manifest(
    glyphs: list[dict[str, Any]],
    masks_by_kind: dict[str, dict[str, Mask]],
    filename_key_by_kind: dict[str, str],
    relative_dir_by_kind: dict[str, Path],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Verify portable ordinary PNG evidence for every glyph and mask kind."""
    rows: list[dict[str, Any]] = []
    safe_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    expected_count = len(glyphs)
    for kind, masks in masks_by_kind.items():
        key = filename_key_by_kind[kind]
        rel_dir = relative_dir_by_kind[kind]
        directory = ROOT / rel_dir
        enumerated = [path for path in directory.iterdir() if path.is_file()] if directory.exists() else []
        ordinary_names = [path.name for path in enumerated]
        if len(ordinary_names) != expected_count:
            errors.append(f"{kind} ordinary PNG enumeration {len(ordinary_names)} != glyph count {expected_count}")
        if len(set(ordinary_names)) != len(ordinary_names):
            errors.append(f"{kind} has duplicate ordinary filenames")
        for glyph in glyphs:
            glyph_id = glyph["glyph_id"]
            filename = glyph[key]
            path = directory / filename
            mask = masks[glyph_id]
            expected_size = (mask.data.shape[1], mask.data.shape[0])
            safe_name = safe_png_filename(glyph_id)
            safe_filename_pass = (
                filename == safe_name
                and Path(filename).name == filename
                and ":" not in filename
                and not any(ch in filename for ch in '<>"/\\|?*')
                and filename.lower().endswith(".png")
            )
            enumerated_once = ordinary_names.count(filename) == 1
            png_open_pass = False
            actual_size: tuple[int, int] | str = "UNKNOWN"
            sha = "UNKNOWN"
            try:
                with Image.open(path) as image:
                    image.load()
                    actual_size = image.size
                    png_open_pass = image.format == "PNG" and image.size == expected_size
                sha = sha256_file(path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{kind}:{glyph_id} unreadable ordinary PNG: {exc}")
            passed = bool(safe_filename_pass and enumerated_once and png_open_pass)
            if not passed:
                errors.append(f"{kind}:{glyph_id} portable PNG manifest failure")
            rows.append(
                {
                    "GLYPH_ID": glyph_id,
                    "MASK_KIND": kind,
                    "SAFE_FILENAME": filename,
                    "RELATIVE_PATH": str((rel_dir / filename).as_posix()),
                    "SAFE_FILENAME_PASS": safe_filename_pass,
                    "COLON_OR_ADS_RISK_PASS": ":" not in filename,
                    "ORDINARY_ENUMERATED_EXACTLY_ONCE": enumerated_once,
                    "EXISTS": path.exists(),
                    "PNG_OPEN_AND_SIZE_PASS": png_open_pass,
                    "EXPECTED_PNG_SIZE": f"{expected_size[0]}x{expected_size[1]}",
                    "ACTUAL_PNG_SIZE": actual_size if isinstance(actual_size, str) else f"{actual_size[0]}x{actual_size[1]}",
                    "MASK_BBOX_PX": fmt_box(mask.bbox),
                    "MASK_PIXELS": mask.pixels,
                    "SHA256": sha,
                    "PASS": passed,
                }
            )
            if kind == "RAW_GLYPH":
                safe_rows.append(
                    {
                        "GLYPH_ID": glyph_id,
                        "SAFE_FILENAME": filename,
                        "RAW_MASK_RELATIVE_PATH": str((rel_dir / filename).as_posix()),
                        "SHAPE_SUPPORT_SAFE_FILENAME": glyph["shape_support_mask_filename"],
                        "SHAPE_SUPPORT_RELATIVE_PATH": str((relative_dir_by_kind["PDF_REPLAY_SHAPE_SUPPORT"] / glyph["shape_support_mask_filename"]).as_posix()),
                        "WINDOWS_PORTABLE_PASS": safe_filename_pass,
                    }
                )
    return rows, safe_rows, errors


def build_manual_review_template(
    coverage: list[dict[str, Any]], evidence_identity: str
) -> list[dict[str, Any]]:
    """Create one non-preapproved manual record for every contact-sheet cell."""
    return [
        {
            "LEDGER_SCHEMA": MANUAL_LEDGER_SCHEMA_VERSION,
            "EVIDENCE_IDENTITY_SHA256": evidence_identity,
            "GLYPH_ID": row["GLYPH_ID"],
            "REVIEWER": "",
            "SHEET": row["SHEET"],
            "CELL": row["CELL_INDEX"],
            "ORIGINAL_MATCH": "PENDING",
            "OVERLAY_COMPLETE": "PENDING",
            "MASK_ONLY_PURE": "PENDING",
            "MISSING_STROKE_PX": "",
            "FOREIGN_PIXEL_PX": "",
            "DECISION": "PENDING",
            "NOTE": "Inspect ORIGINAL 8x, target-red overlay, and MASK ONLY 8x for this exact glyph; do not bulk-approve.",
            "RAW_MASK_SHA256": row["RAW_MASK_SHA256"],
        }
        for row in coverage
    ]


def build_manual_visual_harmony_template(
    elements: list[dict[str, Any]],
    element_measurements: list[dict[str, Any]],
    evidence_identity: str,
) -> list[dict[str, Any]]:
    """Emit reviewer-owned visual rows for every view × panel/role/script.

    A global assertion cannot establish font harmony.  Each reviewer row names
    the evidence view actually opened, its semantic panel/role/script scope,
    source/effective type size, native H median and automated D/E context;
    all visual judgements deliberately begin PENDING.
    """
    views = [
        ("FULL_PAGE_200DPI", "full_page_200dpi.png"),
        ("FIGURE_CROP_300DPI", "figure_crop_300dpi.png"),
        ("STANDALONE_300DPI", "standalone_300dpi.png"),
        ("GRAYSCALE_300DPI", "grayscale_300dpi.png"),
    ]
    element_by_id = {element["element_id"]: element for element in elements}
    rows: list[dict[str, Any]] = []
    for measurement in element_measurements:
        element = element_by_id[measurement["element_id"]]
        for view_id, evidence_file in views:
            rows.append(
                {
        "LEDGER_SCHEMA": "R8_PER_VIEW_PANEL_ROLE_SCRIPT_V1",
                    "EVIDENCE_IDENTITY_SHA256": evidence_identity,
                    "VIEW_ID": view_id,
                    "EVIDENCE_FILE": evidence_file,
                    "PANEL_ID": measurement["panel_id"],
                    "ROLE": measurement["role"],
                    "SCRIPT_CLASS": measurement["script_class"],
                    "ELEMENT_ID": measurement["element_id"],
                    "PARENT_ID": measurement["parent_id"],
                    "TEXT_SAMPLE": measurement["text_sample"],
                    "EFFECTIVE_PT": f"{element['effective_pt']:.2f}",
                    "NATIVE_H_MEDIAN_PX": f"{measurement['h_ink_px']:.3f}",
                    "D_STATUS": "N/A" if measurement["d_pass"] is None else ("PASS" if measurement["d_pass"] else "FAIL"),
                    "E_STATUS": "N/A" if measurement["e_pass"] is None else ("PASS" if measurement["e_pass"] else "FAIL"),
                    "REVIEWER": "",
                    "VIEW_OPENED": "PENDING",
                    "FONT_SIZE_HARMONY": "PENDING",
                    "WEIGHT_FAMILY_HARMONY": "PENDING",
                    "BASELINE_ALIGNMENT": "PENDING",
                    "GRAY_HIERARCHY": "PENDING",
                    "PAGE_INTEGRATION": "PENDING",
                    "CROWDING_OR_INTRUSION": "PENDING",
                    "CROSS_PANEL_CONSISTENCY": "PENDING",
                    "DECISION": "PENDING",
                    "NOTE": "Reviewer must open the named evidence file and record this exact panel/role/script judgement; no global approval is allowed.",
                }
            )
    return rows


def fmt_box(box: tuple[int, int, int, int]) -> str:
    return ",".join(str(v) for v in box)


def main() -> None:
    if not OFFICIAL_PDF.exists() or not FULL_300.exists() or not FULL_200.exists() or not PAGE_SVG.exists():
        abort("missing official PDF or required direct-R95 render inputs")
    # Preserve identity-locked copies inside the path-isolated evidence run.
    # These bytes originated from the direct official-R95 commands recorded in
    # the base run; copying does not rasterize, resize or otherwise transform
    # the native evidence.
    shutil.copyfile(FULL_300, ROOT / "full_page_300dpi.png")
    shutil.copyfile(FULL_200, ROOT / "full_page_200dpi.png")
    shutil.copyfile(PAGE_SVG, ROOT / "page_682_native.svg")
    page_image = Image.open(FULL_300).convert("RGB")
    if page_image.size != (2481, 3508):
        abort(f"native render grid is {page_image.size}, expected official-A4 300dpi 2481x3508")
    img = np.asarray(page_image)
    doc = fitz.open(OFFICIAL_PDF)
    if doc.page_count != 813:
        abort(f"official PDF has {doc.page_count} pages, expected 813")
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    if not (abs(page_rect.width - 595.276) < 0.05 and abs(page_rect.height - 841.89) < 0.05):
        abort(f"unexpected official page size {page_rect}")

    # 1) Gather every visible span within the declared figure+caption scope.
    raw = page.get_text("rawdict")
    source_spans: list[dict[str, Any]] = []
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                rect = fitz.Rect(span["bbox"])
                text = "".join(c["c"] for c in span["chars"])
                if text.strip() and FIG_RECT_PT.contains(rect):
                    source_spans.append(span)
    elements = [element_meta(span, i + 1) for i, span in enumerate(source_spans)]
    if not elements:
        abort("no semantic text elements recovered from final PDF figure scope")

    # 2) Bind every visible PDF char to one actual SVG <use>/<symbol> shape.
    # The SVG chain establishes CHAR -> parent -> actual vector shape.  A
    # second, independent official-PDF content chain below supplies the exact
    # glyph CID/font/CTM replay used for native alpha isolation.
    uses, symbols, _symbol_xml = parse_svg_glyph_uses()
    glyphs, map_errors = map_glyphs_to_svg(elements, uses, symbols)
    if not glyphs:
        abort("no glyph-level text mapping rows")
    glyph_by_element: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        glyph_by_element[glyph["element_id"]].append(glyph)

    for glyph in glyphs:
        glyph["char_bbox_px"] = rect_to_px(fitz.Rect(glyph["char_bbox_pt"]), pad=0)

    # Recover all final visible graphics/backgrounds before classifying text
    # candidates, so an independently isolated glyph can attribute a rejected
    # colour-ray pixel to a real texture/line rather than silently discard it.
    graphics, graphic_errors = build_graphics(page, img)
    foreground_graphics = [g for g in graphics if g["foreground"]]
    texttrace_errors = bind_glyphs_to_texttrace_seqno(page, glyphs)

    # 3) Replay one original official-PDF glyph per page.  The replay PDF
    # clones R95 page resources and records font/CID/CTM/text matrix/fill, then
    # pdftocairo produces native 300dpi alpha supports.  It is the sole raw
    # glyph-isolation authority; the page PNG remains the sole measurement
    # image.
    replay_reader, replay_page, replay_stream, replay_records, replay_extract_errors = (
        pdf_replay.extract_official_text_records(OFFICIAL_PDF, PAGE_INDEX)
    )
    replay_bind_errors = pdf_replay.bind_glyphs_to_official_replay(
        elements,
        glyphs,
        replay_records,
        float(replay_page.mediabox.height),
        (FIG_RECT_PT.x0, FIG_RECT_PT.y0, FIG_RECT_PT.x1, FIG_RECT_PT.y1),
    )
    replay_alpha_values, replay_manifest_rows, replay_render_errors = (
        pdf_replay.render_official_glyph_replays(
            glyphs,
            replay_reader,
            replay_page,
            replay_stream,
            ROOT / "official_pdf_glyph_replays.pdf",
            SCALE,
        )
    )
    final_visibility_data_by_glyph, final_visibility_manifest_rows, final_visibility_errors = (
        pdf_replay.render_official_glyph_final_visibility(
            glyphs,
            replay_reader,
            replay_page,
            replay_stream,
            img[:, :, :3],
            replay_alpha_values,
            ROOT / "official_pdf_glyph_final_visibility_knockouts.pdf",
            SCALE,
        )
    )
    pdf_replay_errors = [
        *replay_extract_errors,
        *replay_bind_errors,
        *replay_render_errors,
        *final_visibility_errors,
    ]

    # 4) Derive final native raw masks (no dilation) for each glyph and span.
    glyph_masks: dict[str, Mask] = {}
    glyph_shape_masks: dict[str, Mask] = {}
    glyph_final_visible_masks: dict[str, Mask] = {}
    glyph_colour_ray_masks: dict[str, Mask] = {}
    glyph_nonpath_masks: dict[str, Mask] = {}
    glyph_missing_masks: dict[str, Mask] = {}
    glyph_foreign_masks: dict[str, Mask] = {}
    glyph_occluded_masks: dict[str, Mask] = {}
    glyph_background_ledger: list[dict[str, Any]] = []
    glyph_nonpath_rows: list[dict[str, Any]] = []
    glyph_subthreshold_drift_rows: list[dict[str, Any]] = []
    glyph_quantization_boundary_rows: list[dict[str, Any]] = []
    quantization_boundary_errors: list[str] = []
    final_visibility_by_glyph = {row["GLYPH_ID"]: row for row in final_visibility_manifest_rows}
    for glyph in glyphs:
        rect = fitz.Rect(glyph["char_bbox_pt"])
        x0, y0, x1, y1 = glyph["char_bbox_px"]
        expected_shape = (y1 - y0, x1 - x0)
        fill, opacity = parse_svg_fill(glyph["svg_parent_style"])
        background, background_rule = glyph_known_background(glyph)
        if fill is None or opacity is None:
            glyph["fill_mapping_pass"] = False
            glyph["svg_fill_rgb"] = "UNKNOWN"
            glyph["svg_fill_opacity"] = "UNKNOWN"
            colour_ray = Mask(x0, y0, np.zeros(expected_shape, dtype=bool))
        else:
            glyph["fill_mapping_pass"] = True
            glyph["svg_fill_rgb"] = ",".join(str(int(round(v))) for v in fill)
            glyph["svg_fill_opacity"] = f"{opacity:.6f}"
            colour_ray = known_background_colour_ray_mask(img, rect, fill, opacity, background)
        alpha_values = replay_alpha_values.get(glyph["glyph_id"])
        final_visibility_data = final_visibility_data_by_glyph.get(glyph["glyph_id"])
        final_row = final_visibility_by_glyph.get(glyph["glyph_id"], {})
        if alpha_values is None or alpha_values.shape != expected_shape:
            alpha_values = np.zeros(expected_shape, dtype=np.uint8)
            glyph["pdf_replay_grid_pass"] = False
        else:
            glyph["pdf_replay_grid_pass"] = True
        if final_visibility_data is None or final_visibility_data["direct_effective"].shape != expected_shape:
            final_visibility_data = {
                "baseline_effective": np.zeros(expected_shape, dtype=bool),
                "direct_effective": np.zeros(expected_shape, dtype=bool),
                "replay_effective": np.zeros(expected_shape, dtype=bool),
                "replay_effective_float": np.zeros(expected_shape, dtype=bool),
                "replay_quantization_boundary": np.zeros(expected_shape, dtype=bool),
                "raw_outside_isolated_alpha": np.ones(expected_shape, dtype=bool),
                "baseline_outside_isolated_alpha": np.ones(expected_shape, dtype=bool),
                "transparent_alpha_overpredict": np.ones(expected_shape, dtype=bool),
                "transparent_alpha_underpredict": np.ones(expected_shape, dtype=bool),
                "raw_delta": np.zeros(expected_shape, dtype=bool),
                "safe_subthreshold_drift": np.zeros(expected_shape, dtype=bool),
                "unsafe_drift": np.ones(expected_shape, dtype=bool),
                "baseline_native_diff": np.ones(expected_shape, dtype=bool),
                "baseline_contrast": np.zeros(expected_shape, dtype=np.int16),
                "direct_contrast": np.zeros(expected_shape, dtype=np.int16),
                "replay_contrast": np.zeros(expected_shape, dtype=np.int16),
                "replay_contrast_float": np.zeros(expected_shape, dtype=np.float64),
                "knockout_rgb": np.zeros((expected_shape[0], expected_shape[1], 3), dtype=np.uint8),
                "baseline_rgb": np.zeros((expected_shape[0], expected_shape[1], 3), dtype=np.uint8),
            }
            glyph["final_visibility_grid_pass"] = False
        else:
            glyph["final_visibility_grid_pass"] = True
        alpha_nonzero = alpha_values > 0
        alpha_ge20 = alpha_values >= 20
        # The isolated official CID alpha proves the unique path support.  It
        # is deliberately not a >=20 raw-foreground mask: transparent replay
        # compositing can quantize differently on a coloured knockout layer.
        shape_mask = Mask(x0, y0, alpha_nonzero)
        # B is the official full-page baseline with the untouched CID; D is
        # the direct native final page.  Both use the exact same knockout K
        # (only this CID changed to Tr 3) and must agree coordinate by
        # coordinate. D is the final-visible raw audit mask.
        final_visible_mask = Mask(x0, y0, final_visibility_data["direct_effective"])
        mask = final_visible_mask
        missing = Mask(x0, y0, final_visibility_data["direct_effective"] & ~alpha_nonzero)
        foreign = Mask(x0, y0, mask.data & ~alpha_nonzero)
        # Any B pixel absent from D would be a true later-paint occlusion.
        # This is distinct from a transparent replay compositing diagnostic.
        occluded = Mask(x0, y0, final_visibility_data["baseline_effective"] & ~final_visibility_data["direct_effective"])
        # A colour-ray pixel not present in this independently replayed target
        # CID is not text.  It remains individually ledgered as a concrete
        # vector/pattern owner with display-list paint order, or UNKNOWN/FAIL.
        nonpath = Mask(x0, y0, colour_ray.data & ~alpha_nonzero)
        attributions, unexplained = attribute_nonpath_colour_candidates(
            glyph, nonpath, graphics, img, alpha_values
        )
        glyph_masks[glyph["glyph_id"]] = mask
        glyph_shape_masks[glyph["glyph_id"]] = shape_mask
        glyph_final_visible_masks[glyph["glyph_id"]] = final_visible_mask
        glyph_colour_ray_masks[glyph["glyph_id"]] = colour_ray
        glyph_nonpath_masks[glyph["glyph_id"]] = nonpath
        glyph_missing_masks[glyph["glyph_id"]] = missing
        glyph_foreign_masks[glyph["glyph_id"]] = foreign
        glyph_occluded_masks[glyph["glyph_id"]] = occluded
        glyph["known_background_rgb"] = ",".join(map(str, (int(v) for v in background)))
        glyph["known_background_rule"] = background_rule
        glyph["pdf_replay_support_pixels"] = shape_mask.pixels
        glyph["pdf_replay_alpha_nonzero_pixels"] = int(alpha_nonzero.sum())
        glyph["pdf_replay_alpha_ge20_pixels"] = int(alpha_ge20.sum())
        glyph["replay_effective_foreground_ge20_pixels"] = shape_mask.pixels
        glyph["baseline_effective_foreground_ge20_pixels"] = int(final_visibility_data["baseline_effective"].sum())
        glyph["direct_effective_foreground_ge20_pixels"] = mask.pixels
        glyph["official_final_visible_pixels"] = final_visible_mask.pixels
        glyph["official_final_visible_ge20_pixels"] = mask.pixels
        glyph["raw_effective_to_isolated_cid_alpha_missing_pixels"] = missing.pixels
        glyph["official_target_mask_foreign_pixels"] = foreign.pixels
        glyph["real_later_paint_occluded_raw_effective_pixels"] = occluded.pixels
        glyph["final_visible_delta_outside_target_alpha_pixels"] = int(final_row.get("FINAL_VISIBLE_DELTA_OUTSIDE_TARGET_ALPHA_PIXELS", -1))
        glyph["baseline_direct_mismatch_pixels"] = int(final_row.get("BASELINE_VS_DIRECT_NATIVE_MISMATCH_PIXELS", -1))
        glyph["baseline_direct_safe_subthreshold_drift_pixels"] = int(final_row.get("BASELINE_DIRECT_SUBTHRESHOLD_AA_DRIFT_PIXELS", -1))
        glyph["baseline_direct_unsafe_mismatch_pixels"] = int(final_row.get("BASELINE_DIRECT_UNSAFE_MISMATCH_PIXELS", -1))
        glyph["baseline_direct_effective_xor_pixels"] = int(final_row.get("BASELINE_DIRECT_EFFECTIVE_XOR_PIXELS", -1))
        glyph["baseline_replay_effective_xor_pixels"] = int(final_row.get("BASELINE_REPLAY_EFFECTIVE_XOR_PIXELS", -1))
        glyph["direct_replay_effective_xor_pixels"] = int(final_row.get("DIRECT_REPLAY_EFFECTIVE_XOR_PIXELS", -1))
        glyph["raw_effective_outside_isolated_alpha_pixels"] = int(final_row.get("RAW_EFFECTIVE_OUTSIDE_ISOLATED_ALPHA_PIXELS", -1))
        glyph["baseline_effective_outside_isolated_alpha_pixels"] = int(final_row.get("BASELINE_EFFECTIVE_OUTSIDE_ISOLATED_ALPHA_PIXELS", -1))
        glyph["transparent_alpha_effective_overpredict_pixels"] = int(final_row.get("TRANSPARENT_ALPHA_EFFECTIVE_OVERPREDICT_PIXELS", -1))
        glyph["transparent_alpha_effective_underpredict_pixels"] = int(final_row.get("TRANSPARENT_ALPHA_EFFECTIVE_UNDERPREDICT_PIXELS", -1))
        glyph["colour_ray_pixels"] = colour_ray.pixels
        glyph["path_colour_intersection_pixels"] = int((colour_ray.data & alpha_nonzero).sum())
        glyph["colour_ray_nonpath_pixels"] = nonpath.pixels
        glyph["unexplained_colour_candidate_pixels"] = unexplained.pixels
        glyph["nonpath_attribution_ids"] = ";".join(sorted({str(row["EVIDENCE_ID"]) for row in attributions if row["EVIDENCE_ID"] != "UNKNOWN"})) or "N/A"
        for local_y, local_x in zip(*np.nonzero(final_visibility_data["baseline_native_diff"])):
            gx, gy = x0 + int(local_x), y0 + int(local_y)
            safe = bool(final_visibility_data["safe_subthreshold_drift"][local_y, local_x])
            glyph_subthreshold_drift_rows.append(
                {
                    "GLYPH_ID": glyph["glyph_id"],
                    "EXPECTED_CHAR": glyph["expected_char"],
                    "X_NATIVE": gx,
                    "Y_NATIVE": gy,
                    "DIRECT_OFFICIAL_RGB": ",".join(str(int(value)) for value in img[gy, gx, :3]),
                    "OFFICIAL_KNOCKOUT_LOCAL_BACKGROUND_RGB": ",".join(
                        str(int(value)) for value in final_visibility_data["knockout_rgb"][local_y, local_x, :3]
                    ),
                    "CROP_BASELINE_RGB": ",".join(
                        str(int(value)) for value in final_visibility_data["baseline_rgb"][local_y, local_x, :3]
                    ),
                    "DIRECT_EFFECTIVE_CONTRAST_MAX_RGB": int(final_visibility_data["direct_contrast"][local_y, local_x]),
                    "BASELINE_EFFECTIVE_CONTRAST_MAX_RGB": int(final_visibility_data["baseline_contrast"][local_y, local_x]),
                    "REPLAY_ALPHA_0_255": int(alpha_values[local_y, local_x]),
                    "DIRECT_EFFECTIVE_GE20": bool(final_visibility_data["direct_effective"][local_y, local_x]),
                    "BASELINE_EFFECTIVE_GE20": bool(final_visibility_data["baseline_effective"][local_y, local_x]),
                    "REPLAY_EFFECTIVE_GE20": bool(final_visibility_data["replay_effective"][local_y, local_x]),
                    "EFFECTIVE_SUPPORT_XOR_DIRECT_BASELINE": bool(
                        final_visibility_data["direct_effective"][local_y, local_x]
                        != final_visibility_data["baseline_effective"][local_y, local_x]
                    ),
                    "EFFECTIVE_SUPPORT_XOR_BASELINE_REPLAY": bool(
                        final_visibility_data["baseline_effective"][local_y, local_x]
                        != final_visibility_data["replay_effective"][local_y, local_x]
                    ),
                    "EFFECTIVE_SUPPORT_XOR_DIRECT_REPLAY": bool(
                        final_visibility_data["direct_effective"][local_y, local_x]
                        != final_visibility_data["replay_effective"][local_y, local_x]
                    ),
                    "DISPOSITION": "SAFE_SUBTHRESHOLD_AA_DRIFT_NON_GATING" if safe else "FAIL_UNSAFE_BASELINE_DRIFT",
                }
            )
        record = glyph.get("pdf_replay_record")
        record_fill = record.get("fill_rgb") if record else None
        record_opacity = record.get("fill_opacity") if record else None
        glyph["replay_float_vs_integer_effective_xor_pixels"] = int(
            final_visibility_data["replay_quantization_boundary"].sum()
        )
        glyph["quantization_boundary_explanation_pass"] = True
        for local_y, local_x in zip(*np.nonzero(final_visibility_data["replay_quantization_boundary"])):
            gx, gy = x0 + int(local_x), y0 + int(local_y)
            integer_lattice_true_boundary = bool(
                not final_visibility_data["replay_effective_float"][local_y, local_x]
                and final_visibility_data["replay_effective"][local_y, local_x]
                and final_visibility_data["baseline_effective"][local_y, local_x]
                and final_visibility_data["direct_effective"][local_y, local_x]
            )
            transparent_alpha_overpredict = bool(
                not final_visibility_data["replay_effective_float"][local_y, local_x]
                and final_visibility_data["replay_effective"][local_y, local_x]
                and not final_visibility_data["baseline_effective"][local_y, local_x]
                and not final_visibility_data["direct_effective"][local_y, local_x]
            )
            expected_boundary = integer_lattice_true_boundary or transparent_alpha_overpredict
            explanation = (
                "OFFICIAL_INTEGER_LATTICE_TRUE_EFFECTIVE_BOUNDARY"
                if integer_lattice_true_boundary
                else (
                    "TRANSPARENT_ALPHA_OVERPREDICT_NON_GATING: official B/D both below 20; full-page CID knockout authority retained"
                    if transparent_alpha_overpredict
                    else "FAIL_UNEXPECTED_FLOAT_INTEGER_SUPPORT_TRANSITION"
                )
            )
            glyph_quantization_boundary_rows.append(
                {
                    "GLYPH_ID": glyph["glyph_id"],
                    "EXPECTED_CHAR": glyph["expected_char"],
                    "X_NATIVE": gx,
                    "Y_NATIVE": gy,
                    "PDF_FILL_RGB_0_1": "UNKNOWN" if record_fill is None else ",".join(f"{value:.6f}" for value in record_fill),
                    "OFFICIAL_KNOCKOUT_LOCAL_BACKGROUND_RGB": ",".join(
                        str(int(value)) for value in final_visibility_data["knockout_rgb"][local_y, local_x, :3]
                    ),
                    "REPLAY_ALPHA_0_255": int(alpha_values[local_y, local_x]),
                    "REPLAY_FLOAT_EFFECTIVE_CONTRAST_MAX_RGB": f"{final_visibility_data['replay_contrast_float'][local_y, local_x]:.9f}",
                    "REPLAY_INTEGER_LATTICE_EFFECTIVE_CONTRAST_MAX_RGB": int(final_visibility_data["replay_contrast"][local_y, local_x]),
                    "REPLAY_FLOAT_EFFECTIVE_GE20": bool(final_visibility_data["replay_effective_float"][local_y, local_x]),
                    "REPLAY_INTEGER_EFFECTIVE_GE20": bool(final_visibility_data["replay_effective"][local_y, local_x]),
                    "BASELINE_EFFECTIVE_GE20": bool(final_visibility_data["baseline_effective"][local_y, local_x]),
                    "DIRECT_EFFECTIVE_GE20": bool(final_visibility_data["direct_effective"][local_y, local_x]),
                    "ISOLATED_CID_ALPHA_SUPPORT_GT0": bool(alpha_nonzero[local_y, local_x]),
                    "DIAGNOSTIC_CLASS": (
                        "INTEGER_LATTICE_TRUE_BOUNDARY" if integer_lattice_true_boundary
                        else "TRANSPARENT_ALPHA_OVERPREDICT" if transparent_alpha_overpredict
                        else "UNEXPLAINED"
                    ),
                    "EXPLANATION_PASS": expected_boundary,
                    "EXPLANATION": explanation,
                }
            )
            if not expected_boundary:
                glyph["quantization_boundary_explanation_pass"] = False
                quantization_boundary_errors.append(
                    f"{glyph['glyph_id']} ({gx},{gy}) unexpected float/integer effective-support transition"
                )
        fill_crosscheck = (
            fill is not None
            and opacity is not None
            and record_fill is not None
            and record_opacity is not None
            and float(np.max(np.abs(fill / 255.0 - np.array(record_fill)))) <= 0.004
            and abs(float(opacity) - float(record_opacity)) <= 1e-6
        )
        glyph["pdf_svg_fill_crosscheck_pass"] = bool(fill_crosscheck)
        glyph["final_visible_closure_pass"] = (
            glyph["final_visibility_grid_pass"]
            and glyph["baseline_direct_unsafe_mismatch_pixels"] == 0
            and glyph["baseline_direct_effective_xor_pixels"] == 0
            and glyph["raw_effective_outside_isolated_alpha_pixels"] == 0
            and glyph["baseline_effective_outside_isolated_alpha_pixels"] == 0
            and missing.pixels == 0
            and foreign.pixels == 0
            and occluded.pixels == 0
        )
        glyph["shape_isolation_pass"] = (
            glyph["fill_mapping_pass"]
            and shape_mask.pixels > 0
            and mask.pixels > 0
            and glyph.get("pdf_replay_mapping_pass", False)
            and glyph["pdf_replay_grid_pass"]
            and glyph.get("pdf_texttrace_mapping_pass", False)
            and glyph["pdf_svg_fill_crosscheck_pass"]
            and glyph["final_visible_closure_pass"]
            and glyph["quantization_boundary_explanation_pass"]
            and unexplained.pixels == 0
        )
        glyph_background_ledger.append(
            {
                "GLYPH_ID": glyph["glyph_id"],
                "EXPECTED_CHAR": glyph["expected_char"],
                "PARENT_ID": glyph["parent_id"],
                "SVG_PARENT_FILL_RGB": glyph["svg_fill_rgb"],
                "SVG_FILL_OPACITY": glyph["svg_fill_opacity"],
                "KNOWN_UNDERLAY_RGB": glyph["known_background_rgb"],
                "UNDERLAY_PROOF": background_rule,
                "COLOUR_RAY_CANDIDATE_PIXELS": glyph["colour_ray_pixels"],
                "PDF_REPLAY_ALPHA_NONZERO_PIXELS": glyph["pdf_replay_alpha_nonzero_pixels"],
                "PDF_REPLAY_ALPHA_GE20_PIXELS": glyph["pdf_replay_alpha_ge20_pixels"],
                "REPLAY_EFFECTIVE_FOREGROUND_GE20_PIXELS": glyph["replay_effective_foreground_ge20_pixels"],
                "BASELINE_EFFECTIVE_FOREGROUND_GE20_PIXELS": glyph["baseline_effective_foreground_ge20_pixels"],
                "DIRECT_EFFECTIVE_FOREGROUND_GE20_PIXELS": glyph["direct_effective_foreground_ge20_pixels"],
                "OFFICIAL_FINAL_VISIBLE_TARGET_PIXELS": glyph["official_final_visible_pixels"],
                "OFFICIAL_FINAL_VISIBLE_TARGET_GE20_PIXELS": glyph["official_final_visible_ge20_pixels"],
                "RAW_EFFECTIVE_TO_ISOLATED_CID_ALPHA_MISSING_PIXELS": glyph["raw_effective_to_isolated_cid_alpha_missing_pixels"],
                "OFFICIAL_TARGET_MASK_FOREIGN_PIXELS": glyph["official_target_mask_foreign_pixels"],
                "REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE_PIXELS": glyph["real_later_paint_occluded_raw_effective_pixels"],
                "BASELINE_DIRECT_NATIVE_MISMATCH_PIXELS": glyph["baseline_direct_mismatch_pixels"],
                "BASELINE_DIRECT_SAFE_SUBTHRESHOLD_AA_DRIFT_PIXELS": glyph["baseline_direct_safe_subthreshold_drift_pixels"],
                "BASELINE_DIRECT_UNSAFE_MISMATCH_PIXELS": glyph["baseline_direct_unsafe_mismatch_pixels"],
                "BASELINE_DIRECT_EFFECTIVE_XOR_PIXELS": glyph["baseline_direct_effective_xor_pixels"],
                "BASELINE_REPLAY_EFFECTIVE_XOR_PIXELS": glyph["baseline_replay_effective_xor_pixels"],
                "DIRECT_REPLAY_EFFECTIVE_XOR_PIXELS": glyph["direct_replay_effective_xor_pixels"],
                "RAW_EFFECTIVE_OUTSIDE_ISOLATED_CID_ALPHA_PIXELS": glyph["raw_effective_outside_isolated_alpha_pixels"],
                "BASELINE_EFFECTIVE_OUTSIDE_ISOLATED_CID_ALPHA_PIXELS": glyph["baseline_effective_outside_isolated_alpha_pixels"],
                "TRANSPARENT_ALPHA_EFFECTIVE_OVERPREDICT_PIXELS_DIAGNOSTIC": glyph["transparent_alpha_effective_overpredict_pixels"],
                "TRANSPARENT_ALPHA_EFFECTIVE_UNDERPREDICT_PIXELS_DIAGNOSTIC": glyph["transparent_alpha_effective_underpredict_pixels"],
                "REPLAY_FLOAT_VS_INTEGER_EFFECTIVE_XOR_PIXELS": glyph["replay_float_vs_integer_effective_xor_pixels"],
                "QUANTIZATION_BOUNDARY_EXPLANATION_PASS": glyph["quantization_boundary_explanation_pass"],
                "FINAL_VISIBLE_DELTA_OUTSIDE_TARGET_ALPHA_PIXELS": glyph["final_visible_delta_outside_target_alpha_pixels"],
                "TEXT_ONLY_INTERSECTION_PIXELS": glyph["path_colour_intersection_pixels"],
                "COLOUR_RAY_NONPATH_PIXELS": glyph["colour_ray_nonpath_pixels"],
                "NONPATH_ATTRIBUTION_IDS": glyph["nonpath_attribution_ids"],
                "UNEXPLAINED_COLOUR_RAY_NONPATH_PIXELS": glyph["unexplained_colour_candidate_pixels"],
                "PDF_SVG_FILL_OPACITY_CROSSCHECK": glyph["pdf_svg_fill_crosscheck_pass"],
                "COMPLETENESS_STATUS": "PASS" if glyph["shape_isolation_pass"] else "FAIL",
            }
        )
        glyph_nonpath_rows.extend(attributions)
    glyph_ownership_rows = resolve_same_semantic_text_glyph_ownership(glyphs, glyph_masks)
    for glyph in glyphs:
        mask = glyph_masks[glyph["glyph_id"]]
        glyph["raw_mask_pixels"] = mask.pixels
        glyph["raw_mask_bbox_px"] = fmt_box(mask.nonempty_bbox() or mask.bbox)
        glyph["h_ink_px"] = int(np.any(mask.data, axis=1).sum()) if mask.pixels else 0
        glyph["pixel_pass"] = glyph["h_ink_px"] >= glyph["threshold_px"] and mask.pixels > 0
        glyph["pixel_reason"] = "PASS" if glyph["pixel_pass"] else f"H_INK={glyph['h_ink_px']} < {glyph['threshold_px']} or raw mask empty"

    text_objects: list[dict[str, Any]] = []
    for element in elements:
        own = glyph_by_element[element["element_id"]]
        mask = union_masks([glyph_masks[g["glyph_id"]] for g in own])
        element["mask"] = mask
        element["bbox_px"] = mask.bbox
        element["nonempty"] = mask.pixels > 0
        element["glyph_count"] = len(own)
        element["raw_mask_pixels"] = mask.pixels
        # Goal 9.2.1(A): a natural TeX scriptstyle child may be below 9.5pt
        # only where its formula base is itself >=9.5pt; the child is still
        # governed by the independent >=15px glyph gate.
        element["effective_font_pass"] = (
            element["effective_pt"] >= 9.5
            or (element["role"] == "FORMULA_SCRIPT" and element["parent_id"] in {"P_FORMULA_J", "P_FORMULA_D", "P_FORMULA_T"})
        )
        text_objects.append(
            {
                "id": element["element_id"],
                "category": "TEXT" if not element["role"].startswith("FORMULA") else "FORMULA",
                "role": element["role"],
                "panel_id": element["panel_id"],
                "parent_id": element["parent_id"],
                "mask": mask,
                "bbox_px": mask.bbox,
                "foreground": True,
                "element": element,
            }
        )

    # Persist every raw glyph, semantic text and final-visible graphic mask.
    for glyph in glyphs:
        glyph["raw_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        glyph["shape_support_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        glyph["final_visible_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        glyph["colour_ray_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        glyph["nonpath_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        glyph["missing_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        glyph["foreign_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        glyph["occluded_mask_filename"] = safe_png_filename(glyph["glyph_id"])
        write_mask_png(glyph_masks[glyph["glyph_id"]], ROOT / "masks" / "glyphs" / glyph["raw_mask_filename"])
        write_mask_png(
            glyph_shape_masks[glyph["glyph_id"]],
            ROOT / "masks" / "glyph_shape_support" / glyph["shape_support_mask_filename"],
        )
        write_mask_png(
            glyph_final_visible_masks[glyph["glyph_id"]],
            ROOT / "masks" / "glyph_final_visible_target" / glyph["final_visible_mask_filename"],
        )
        write_mask_png(
            glyph_colour_ray_masks[glyph["glyph_id"]],
            ROOT / "masks" / "glyph_colour_ray_candidates" / glyph["colour_ray_mask_filename"],
        )
        write_mask_png(
            glyph_nonpath_masks[glyph["glyph_id"]],
            ROOT / "masks" / "glyph_colour_ray_nonpath" / glyph["nonpath_mask_filename"],
        )
        write_mask_png(
            glyph_missing_masks[glyph["glyph_id"]],
            ROOT / "masks" / "glyph_completeness_missing" / glyph["missing_mask_filename"],
        )
        write_mask_png(
            glyph_foreign_masks[glyph["glyph_id"]],
            ROOT / "masks" / "glyph_foreign_pixels" / glyph["foreign_mask_filename"],
        )
        write_mask_png(
            glyph_occluded_masks[glyph["glyph_id"]],
            ROOT / "masks" / "glyph_real_later_paint_occluded" / glyph["occluded_mask_filename"],
        )
    write_csv(ROOT / "glyph_mask_ownership.csv", glyph_ownership_rows)
    for obj in text_objects:
        write_mask_png(obj["mask"], ROOT / "masks" / "text" / safe_png_filename(obj["id"]))
    for graphic in graphics:
        write_mask_png(graphic["mask"], ROOT / "masks" / "graphics" / safe_png_filename(graphic["id"]))
        if "pre_mask" in graphic:
            write_mask_png(graphic["pre_mask"], ROOT / "masks" / "paint_order" / safe_png_filename(f"{graphic['id']}_pre_occlusion"))
            write_mask_png(graphic["pre_pattern_mask"], ROOT / "masks" / "paint_order" / safe_png_filename(f"{graphic['id']}_pre_halo_texture"))
            write_mask_png(graphic["halo_mask"], ROOT / "masks" / "paint_order" / safe_png_filename(f"{graphic['id']}_true_opaque_halo"))
            write_mask_png(graphic["final_background_mask"], ROOT / "masks" / "paint_order" / safe_png_filename(f"{graphic['id']}_final_visible_background"))

    glyph_file_rows, safe_filename_rows, glyph_file_errors = build_glyph_file_manifest(
        glyphs,
        {
            "RAW_GLYPH": glyph_masks,
            "PDF_REPLAY_SHAPE_SUPPORT": glyph_shape_masks,
            "OFFICIAL_FINAL_VISIBLE_TARGET": glyph_final_visible_masks,
            "COLOUR_RAY_CANDIDATE": glyph_colour_ray_masks,
            "COLOUR_RAY_NONPATH": glyph_nonpath_masks,
            "COMPLETENESS_MISSING": glyph_missing_masks,
            "FOREIGN_PIXEL": glyph_foreign_masks,
            "REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE": glyph_occluded_masks,
        },
        {
            "RAW_GLYPH": "raw_mask_filename",
            "PDF_REPLAY_SHAPE_SUPPORT": "shape_support_mask_filename",
            "OFFICIAL_FINAL_VISIBLE_TARGET": "final_visible_mask_filename",
            "COLOUR_RAY_CANDIDATE": "colour_ray_mask_filename",
            "COLOUR_RAY_NONPATH": "nonpath_mask_filename",
            "COMPLETENESS_MISSING": "missing_mask_filename",
            "FOREIGN_PIXEL": "foreign_mask_filename",
            "REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE": "occluded_mask_filename",
        },
        {
            "RAW_GLYPH": Path("masks") / "glyphs",
            "PDF_REPLAY_SHAPE_SUPPORT": Path("masks") / "glyph_shape_support",
            "OFFICIAL_FINAL_VISIBLE_TARGET": Path("masks") / "glyph_final_visible_target",
            "COLOUR_RAY_CANDIDATE": Path("masks") / "glyph_colour_ray_candidates",
            "COLOUR_RAY_NONPATH": Path("masks") / "glyph_colour_ray_nonpath",
            "COMPLETENESS_MISSING": Path("masks") / "glyph_completeness_missing",
            "FOREIGN_PIXEL": Path("masks") / "glyph_foreign_pixels",
            "REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE": Path("masks") / "glyph_real_later_paint_occluded",
        },
    )
    raw_mask_sha_by_glyph = {
        row["GLYPH_ID"]: row["SHA256"]
        for row in glyph_file_rows
        if row["MASK_KIND"] == "RAW_GLYPH"
    }
    evidence_identity_payload = [
        {
            "glyph_id": glyph["glyph_id"],
            "raw_mask_sha256": raw_mask_sha_by_glyph.get(glyph["glyph_id"], "UNKNOWN"),
            "shape_support_sha256": next(
                (
                    row["SHA256"]
                    for row in glyph_file_rows
                    if row["GLYPH_ID"] == glyph["glyph_id"] and row["MASK_KIND"] == "PDF_REPLAY_SHAPE_SUPPORT"
                ),
                "UNKNOWN",
            ),
            "final_visible_sha256": next(
                (
                    row["SHA256"]
                    for row in glyph_file_rows
                    if row["GLYPH_ID"] == glyph["glyph_id"] and row["MASK_KIND"] == "OFFICIAL_FINAL_VISIBLE_TARGET"
                ),
                "UNKNOWN",
            ),
            "char": glyph["expected_char"],
            "shape": glyph["svg_shape_id"],
            "bbox": glyph["char_bbox_px"],
        }
        for glyph in sorted(glyphs, key=lambda item: item["glyph_id"])
    ]
    manual_evidence_identity = hashlib.sha256(
        json.dumps(evidence_identity_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    # 5) Compute source-font table and element-level H-ink/D/E measurements.
    font_rows: list[dict[str, Any]] = []
    for element in elements:
        script_groups = sorted({g["script_class"] for g in glyph_by_element[element["element_id"]]})
        font_rows.append(
            {
                "ELEMENT_ID": element["element_id"],
                "PARENT_ID": element["parent_id"],
                "PANEL_ID": element["panel_id"],
                "ROLE": element["role"],
                "SOURCE_FILE": "fig_v5_c04_coordinate_sweep.tex / common/statlearnbook.sty",
                "SOURCE_LINE": element["source_line"],
                "TEXT_SAMPLE": element["text"],
                "FONT": element["font"],
                "DECLARED_PT": f"{element['declared_pt']:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{element['effective_pt']:.2f}",
                "PDF_EXTRACTED_PT": f"{element['pdf_extracted_pt']:.4f}",
                "SCRIPT_CLASSES": ";".join(script_groups),
                "FONT_PASS": element["effective_font_pass"],
                "REASON": (
                    "PASS: legal natural TeX scriptstyle from the associated 10.0pt base; child pixels audited at >=15px"
                    if element["role"] == "FORMULA_SCRIPT"
                    else "PASS"
                ),
            }
        )

    # Parent/span representative is the median of raw child glyph heights of a
    # single script class.  Mixed formula spans are already separated by PDF
    # spans, so no CJK glyph can mask a small mathematical child.
    element_measurements: list[dict[str, Any]] = []
    for element in elements:
        children = glyph_by_element[element["element_id"]]
        by_script: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for g in children:
            by_script[g["script_class"]].append(g)
        for script_class, values in by_script.items():
            hs = [g["h_ink_px"] for g in values]
            threshold = max(g["threshold_px"] for g in values)
            # One low-stroke character must fail independently even when a
            # same-span median is healthy.
            child_pass = all(g["pixel_pass"] for g in values)
            rep = float(np.median(hs))
            element_measurements.append(
                {
                    "measurement_id": f"{element['element_id']}:{script_class}",
                    "element_id": element["element_id"],
                    "parent_id": element["parent_id"],
                    "panel_id": element["panel_id"],
                    "role": element["role"],
                    "script_class": script_class,
                    "text_sample": element["text"],
                    "bbox_px": element["bbox_px"],
                    "h_ink_px": rep,
                    "threshold_px": threshold,
                    "all_child_glyphs_pass": child_pass,
                    "glyph_count": len(values),
                }
            )
    by_d_group: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in element_measurements:
        by_d_group[(row["panel_id"], row["role"], row["script_class"])].append(row)
    for key, rows in by_d_group.items():
        median = float(np.median([r["h_ink_px"] for r in rows]))
        role_median_ratio = max(r["h_ink_px"] for r in rows) / min(r["h_ink_px"] for r in rows) if rows and min(r["h_ink_px"] for r in rows) else math.inf
        for row in rows:
            row["class_median_px"] = median
            row["ratio_to_class_median"] = row["h_ink_px"] / median if median else math.inf
            row["same_class_group_size"] = len(rows)
            row["same_class_group_extreme_ratio"] = role_median_ratio
            row["d_applicable"] = len(rows) > 1
            row["d_pass"] = (
                (0.92 <= row["ratio_to_class_median"] <= 1.08 and role_median_ratio <= 1.08)
                if len(rows) > 1
                else None
            )

    # E: only visually comparable CJK roles are compared to the ordinary node
    # body base.  Formula, digit and script classes are explicitly N/A rather
    # than silently cross-compared with full-height CJK glyphs.
    base_rows = [
        r
        for r in element_measurements
        if r["panel_id"] == "MAIN" and r["role"] == "NODE_LABEL" and r["script_class"] == "CJK_FULLWIDTH"
    ]
    base_median = float(np.median([r["h_ink_px"] for r in base_rows])) if base_rows else math.nan
    role_band = {
        "PANEL_TITLE": (1.05, 1.20),
        "SEQUENCE_LABEL": (0.95, 1.10),
        "ARROW_LABEL": (0.95, 1.10),
        "STATE_GROUP_LABEL": (0.95, 1.10),
        "STATE_LABEL": (0.95, 1.10),
        "STATE_EXPLANATION": (0.95, 1.10),
        "STATE_CONNECTION_LABEL": (0.95, 1.10),
        "END_SAMPLE_LABEL": (0.95, 1.10),
    }
    for row in element_measurements:
        if row["panel_id"] != "MAIN" or row["script_class"] != "CJK_FULLWIDTH":
            row["role_ratio"] = "N/A_CROSS_SCRIPT_OR_CAPTION"
            row["e_pass"] = None
            row["e_reason"] = "N/A: only same-script CJK roles are comparable to the CJK BASE"
        elif row["role"] == "NODE_LABEL":
            row["role_ratio"] = row["h_ink_px"] / base_median
            row["e_pass"] = True
            row["e_reason"] = "BASE: ordinary node-body CJK"
        elif row["role"] in role_band:
            low, high = role_band[row["role"]]
            ratio = row["h_ink_px"] / base_median
            row["role_ratio"] = ratio
            row["e_pass"] = low <= ratio <= high
            row["e_reason"] = f"CJK comparable role band [{low:.2f},{high:.2f}]"
        else:
            row["role_ratio"] = "N/A_NO_9.2.1_ROLE_BAND"
            row["e_pass"] = None
            row["e_reason"] = "N/A: no prescribed same-script role band"

    # 6) All unordered foreground pairs plus a required-relation subset.
    # Formula base/script and caption fragments are represented externally only
    # by their complete semantic parents; their individual raw masks remain in
    # the glyph/text inventories and are never silently discarded.
    relation_text_objects = build_relation_text_objects(text_objects)
    foreground = relation_text_objects + [
        {
            "id": g["id"],
            "category": g["category"],
            "role": g["role"],
            "panel_id": g["panel_id"],
            "parent_id": g["id"],
            "mask": g["mask"],
            "bbox_px": g["mask"].bbox,
            "foreground": True,
            "element": None,
        }
        for g in foreground_graphics
    ]
    object_by_id = {obj["id"]: obj for obj in foreground}
    all_pairs: list[dict[str, Any]] = []
    required_relations: list[dict[str, Any]] = []
    for counter, (a, b) in enumerate(combinations(foreground, 2), start=1):
        ac, bc = a["category"], b["category"]
        overlap = pair_intersection_pixels(a["mask"], b["mask"])
        min_distance = pair_min_distance(a["mask"], b["mask"])
        text_a, text_b = ac in {"TEXT", "FORMULA"}, bc in {"TEXT", "FORMULA"}
        relevant = False
        relation_type = "FOREGROUND_PAIR_NA"
        threshold = None
        clearance_metric = "N/A"
        waived = False
        if text_a and text_b:
            relation_type = "TEXT_TEXT"
            clearance_metric = "PDF_VECTOR_BBOX"
            min_distance = bbox_distance(a["bbox_px"], b["bbox_px"])
            # Caption fragments and natural formula scripts have already been
            # folded into a single semantic relation object above.  Thus every
            # remaining TEXT_TEXT pair is an external pair and receives the
            # full 4px PDF/vector-bbox gate.
            threshold = 4.0
            relevant = True
        elif text_a or text_b:
            text, graphic = (a, b) if text_a else (b, a)
            if graphic["category"] == "NODE_BORDER":
                relation_type, threshold, clearance_metric, relevant = "TEXT_NODE_BORDER", 5.0, "RAW_MASK", True
            elif graphic["category"] == "PANEL_BORDER":
                relation_type, threshold, clearance_metric, relevant = "TEXT_PANEL_BORDER", 5.0, "RAW_MASK", True
            elif graphic["category"] == "LINE_ARROW":
                relation_type, threshold, clearance_metric, relevant = "TEXT_LINE_ARROW", 3.0, "RAW_MASK", True
            elif graphic["category"] == "ARROWHEAD":
                relation_type, threshold, clearance_metric, relevant = "ARROWHEAD_TEXT", 3.0, "RAW_MASK", True
            elif graphic["category"] == "BACKGROUND_TEXTURE":
                relation_type, threshold, clearance_metric, relevant = "TEXT_BACKGROUND_TEXTURE", 3.0, "RAW_MASK", True
        status = "PASS"
        reason = "non-mandatory graphic/graphic pair"
        if relevant:
            if overlap != 0:
                status, reason = "FAIL", f"illegal final-visible overlap={overlap}px"
            elif threshold is not None and min_distance < threshold:
                status, reason = "FAIL", f"clearance={min_distance:.3f}px < {threshold:.3f}px"
            else:
                reason = "PASS"
        row = {
            "relation_id": f"R{counter:04d}",
            "object_a": a["id"],
            "object_b": b["id"],
            "category_a": ac,
            "category_b": bc,
            "semantic_members_a": a.get("relation_members", a["id"]),
            "semantic_members_b": b.get("relation_members", b["id"]),
            "relation_type": relation_type,
            "mandatory": relevant,
            "waived_natural_caption_wrap": False,
            "overlap_pixel_count": overlap,
            "clearance_px": f"{min_distance:.6f}" if math.isfinite(min_distance) else "INF",
            "clearance_metric": clearance_metric,
            "threshold_px": "N/A" if threshold is None else f"{threshold:.1f}",
            "status": status,
            "reason": reason,
        }
        all_pairs.append(row)
        if relevant:
            required_relations.append(row)

    # All text foreground is checked against every other foreground object.
    # A per-glyph crosscheck catches accidental contamination before parent masks
    # are used in any relationship calculation.
    glyph_graphic_cross = []
    glyph_contamination_rows: list[dict[str, Any]] = []
    for glyph in glyphs:
        for graphic in foreground_graphics:
            n = pair_intersection_pixels(glyph_masks[glyph["glyph_id"]], graphic["mask"])
            glyph_contamination_rows.append(
                {
                    "GLYPH_ID": glyph["glyph_id"],
                    "EXPECTED_CHAR": glyph["expected_char"],
                    "SVG_SHAPE_ID": glyph["svg_shape_id"],
                    "GRAPHIC_ID": graphic["id"],
                    "GRAPHIC_CATEGORY": graphic["category"],
                    "FINAL_VISIBLE_RAW_MASK_INTERSECTION_PX": n,
                    "CONTAMINATION_PASS": n == 0,
                    "RULE": "glyph SVG-path isolated final R95 raw mask must contain no final-visible graphic pixel",
                }
            )
            if n:
                glyph_graphic_cross.append((glyph["glyph_id"], graphic["id"], n))
    glyph_pair_overlap = 0
    for a, b in combinations(glyphs, 2):
        # A formula/caption semantic parent may span several PDF text spans;
        # no pair of its child glyph masks may retain a duplicated raw pixel.
        same_semantic_owner = (
            a["element_id"] == b["element_id"]
            or (
                a["parent_id"] == b["parent_id"]
                and a["parent_id"] in {"P_FORMULA_J", "P_FORMULA_D", "P_FORMULA_T", "P_CAPTION"}
            )
        )
        if same_semantic_owner:
            glyph_pair_overlap += pair_intersection_pixels(glyph_masks[a["glyph_id"]], glyph_masks[b["glyph_id"]])

    # Page clipping: a raw foreground pixel or vector bbox on a page boundary
    # would be a clip failure.  All final-visible components are inspected.
    clip_count = 0
    page_w, page_h = page_image.size
    for obj in foreground:
        mask = obj["mask"]
        nbb = mask.nonempty_bbox()
        if nbb and (nbb[0] <= 0 or nbb[1] <= 0 or nbb[2] >= page_w or nbb[3] >= page_h):
            clip_count += 1

    # 7) Native crop, grayscale and text overlay.
    crop = page_image.crop(CROP_BOX_PX)
    crop.save(ROOT / "figure_crop_300dpi.png")
    # No independent source is accepted for this SA1. The standalone view is
    # therefore the same unscaled native pixel crop, explicitly documented.
    shutil.copyfile(ROOT / "figure_crop_300dpi.png", ROOT / "standalone_300dpi.png")
    ImageOps.grayscale(crop).save(ROOT / "grayscale_300dpi.png")

    overlay = crop.copy()
    draw = ImageDraw.Draw(overlay)
    small_font = pick_font(11)
    for idx, obj in enumerate(text_objects):
        x0, y0, x1, y1 = obj["bbox_px"]
        x0 -= CROP_BOX_PX[0]
        x1 -= CROP_BOX_PX[0]
        y0 -= CROP_BOX_PX[1]
        y1 -= CROP_BOX_PX[1]
        colour = ((37 * idx + 80) % 220, (79 * idx + 50) % 220, (131 * idx + 30) % 220)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=colour, width=1)
        label = f"{obj['id']} {obj['role']}"
        draw.rectangle((x0, max(0, y0 - 12), min(overlay.width - 1, x0 + 130), y0), fill=(255, 255, 255))
        draw.text((x0 + 1, max(0, y0 - 12)), label, fill=colour, font=small_font)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # 8) Critical and failure packages.  The 1:1 native ROIs are canonical;
    # each paired 8x image is nearest-neighbour visual-only evidence.
    roi_dir = ROOT / "ROIs"
    roi_dir.mkdir(exist_ok=True)
    critical_relations = [
        r
        for r in required_relations
        if r["status"] == "FAIL"
        or (
            r["threshold_px"] != "N/A"
            and r["clearance_px"] != "INF"
            and float(r["clearance_px"]) <= float(r["threshold_px"]) + 2.0
        )
    ]
    for relation in critical_relations:
        save_relation_package(page_image, relation, object_by_id[relation["object_a"]]["mask"], object_by_id[relation["object_b"]]["mask"], roi_dir)
    critical_glyphs = [
        g
        for g in glyphs
        if (
            not g["pixel_pass"]
            or not g["shape_isolation_pass"]
            or g["h_ink_px"] <= g["threshold_px"] + 1
            or g["colour_ray_nonpath_pixels"] > 0
            or g["real_later_paint_occluded_raw_effective_pixels"] > 0
        )
    ]
    for glyph in critical_glyphs:
        box = glyph["char_bbox_px"]
        make_native_roi(
            page_image,
            (max(0, box[0] - 3), max(0, box[1] - 3), min(page_w, box[2] + 3), min(page_h, box[3] + 3)),
            roi_dir / safe_png_filename(f"{glyph['glyph_id']}_native_1x"),
            roi_dir / safe_png_filename(f"{glyph['glyph_id']}_8x_nearest"),
        )
    contact_sheets, glyph_contact_coverage = create_glyph_contact_sheets(
        page_image, glyphs, glyph_masks, raw_mask_sha_by_glyph
    )
    glyph_manual_review_rows = build_manual_review_template(glyph_contact_coverage, manual_evidence_identity)
    visual_harmony_review_rows = build_manual_visual_harmony_template(
        elements, element_measurements, manual_evidence_identity
    )

    # 9) Flat audit CSV rows: semantic representative rows plus mandatory child
    # glyph rows.  This makes every child threshold independently auditable.
    p_rows: list[dict[str, Any]] = []
    element_measurement_index = {(r["element_id"], r["script_class"]): r for r in element_measurements}
    for row in element_measurements:
        e = next(e for e in elements if e["element_id"] == row["element_id"])
        p_rows.append(
            {
                "AUDIT_LEVEL": "SEMANTIC_ELEMENT",
                "ELEMENT_ID": row["measurement_id"],
                "PARENT_ID": row["parent_id"],
                "PANEL_ID": row["panel_id"],
                "ROLE": row["role"],
                "SOURCE_FILE": "fig_v5_c04_coordinate_sweep.tex",
                "SOURCE_LINE": e["source_line"],
                "DECLARED_PT": f"{e['declared_pt']:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{e['effective_pt']:.2f}",
                "TEXT_SAMPLE": e["text"],
                "SCRIPT_CLASS": row["script_class"],
                "BBOX_X0": row["bbox_px"][0],
                "BBOX_Y0": row["bbox_px"][1],
                "BBOX_X1": row["bbox_px"][2],
                "BBOX_Y1": row["bbox_px"][3],
                "H_INK_PX": f"{row['h_ink_px']:.3f}",
                "PIXEL_THRESHOLD_PX": row["threshold_px"],
                "CLASS_MEDIAN_PX": f"{row['class_median_px']:.3f}",
                "RATIO_TO_CLASS_MEDIAN": f"{row['ratio_to_class_median']:.5f}",
                "SAME_CLASS_GROUP": f"{row['panel_id']}|{row['role']}|{row['script_class']}",
                "SAME_CLASS_GROUP_SIZE": row["same_class_group_size"],
                "SAME_CLASS_EXTREME_RATIO": f"{row['same_class_group_extreme_ratio']:.5f}",
                "D_APPLICABLE": row["d_applicable"],
                "D_PASS": "N/A" if row["d_pass"] is None else row["d_pass"],
                "ROLE_RATIO": row["role_ratio"],
                "E_PASS": "N/A" if row["e_pass"] is None else row["e_pass"],
                "E_REASON": row["e_reason"],
                "TEXT_TEXT_OVERLAP_PX": "see after_overlap_report.csv",
                "TEXT_GRAPHIC_OVERLAP_PX": "see after_overlap_report.csv",
                "MIN_CLEARANCE_PX": "see after_overlap_report.csv",
                "PASS_FAIL": "PASS" if row["all_child_glyphs_pass"] and (row["d_pass"] is not False) and (row["e_pass"] is not False) else "FAIL",
                "REASON": "semantic representative; child glyph rows below enforce every character",
            }
        )
    for glyph in glyphs:
        e = next(e for e in elements if e["element_id"] == glyph["element_id"])
        p_rows.append(
            {
                "AUDIT_LEVEL": "GLYPH_OR_KEY_SUBSTRING",
                "ELEMENT_ID": glyph["glyph_id"],
                "PARENT_ID": glyph["parent_id"],
                "PANEL_ID": glyph["panel_id"],
                "ROLE": glyph["role"],
                "SOURCE_FILE": "fig_v5_c04_coordinate_sweep.tex",
                "SOURCE_LINE": e["source_line"],
                "DECLARED_PT": f"{e['declared_pt']:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{e['effective_pt']:.2f}",
                "TEXT_SAMPLE": glyph["expected_char"],
                "SCRIPT_CLASS": glyph["script_class"],
                "BBOX_X0": glyph["char_bbox_px"][0],
                "BBOX_Y0": glyph["char_bbox_px"][1],
                "BBOX_X1": glyph["char_bbox_px"][2],
                "BBOX_Y1": glyph["char_bbox_px"][3],
                "H_INK_PX": glyph["h_ink_px"],
                "PIXEL_THRESHOLD_PX": glyph["threshold_px"],
                "CLASS_MEDIAN_PX": "N/A_CHILD_GLYPH",
                "RATIO_TO_CLASS_MEDIAN": "N/A_CHILD_GLYPH",
                "SAME_CLASS_GROUP": "N/A_CHILD_GLYPH",
                "SAME_CLASS_GROUP_SIZE": "N/A",
                "SAME_CLASS_EXTREME_RATIO": "N/A",
                "D_APPLICABLE": "N/A_CHILD_GLYPH",
                "D_PASS": "N/A_CHILD_GLYPH",
                "ROLE_RATIO": "N/A_CHILD_GLYPH",
                "E_PASS": "N/A_CHILD_GLYPH",
                "E_REASON": glyph["threshold_rule"],
                "TEXT_TEXT_OVERLAP_PX": "see after_overlap_report.csv",
                "TEXT_GRAPHIC_OVERLAP_PX": "see after_overlap_report.csv",
                "MIN_CLEARANCE_PX": "see after_overlap_report.csv",
                "PASS_FAIL": "PASS" if glyph["pixel_pass"] and glyph["mapping_status"] == "PASS" and glyph["shape_isolation_pass"] else "FAIL",
                "REASON": (
                    glyph["pixel_reason"]
                    + "; SVG character-shape mapping=" + glyph["mapping_status"]
                    + "; official-CID/final-visible closure=" + ("PASS" if glyph["shape_isolation_pass"] else "FAIL")
                ),
            }
        )

    # 10) inventories and machine-integrity accounting.
    # The semantic inventory is the relationship object universe.  A separate
    # PDF-span inventory preserves every extraction fragment and its child
    # glyph evidence, so formula/caption grouping cannot conceal a span.
    semantic_text_inventory = []
    for obj in relation_text_objects:
        semantic_text_inventory.append(
            {
                "SEMANTIC_ELEMENT_ID": obj["id"],
                "CATEGORY": obj["category"],
                "ROLE": obj["role"],
                "PANEL_ID": obj["panel_id"],
                "PARENT_ID": obj["parent_id"],
                "MEMBER_PDF_SPAN_IDS": obj.get("relation_members", obj["id"]),
                "RELATION_OBJECT_KIND": obj.get("relation_object_kind", "SINGLE_SEMANTIC_TEXT_ELEMENT"),
                "NATIVE_RAW_MASK_BBOX_PX": fmt_box(obj["mask"].bbox),
                "NATIVE_RAW_MASK_PIXELS": obj["mask"].pixels,
                "NONEMPTY": obj["mask"].pixels > 0,
            }
        )
    text_inventory = []
    relation_id_for_span = {
        member: obj["id"]
        for obj in relation_text_objects
        for member in obj.get("relation_members", obj["id"]).split(";")
    }
    for e in elements:
        text_inventory.append(
            {
                "PDF_SPAN_ID": e["element_id"],
                "SEMANTIC_RELATION_OBJECT_ID": relation_id_for_span[e["element_id"]],
                "PARENT_ID": e["parent_id"],
                "PANEL_ID": e["panel_id"],
                "ROLE": e["role"],
                "TEXT": e["text"],
                "SOURCE_LINE": e["source_line"],
                "PDF_BBOX_PT": ",".join(f"{v:.4f}" for v in e["span_bbox_pt"]),
                "NATIVE_BBOX_PX": fmt_box(e["bbox_px"]),
                "GLYPH_COUNT": e["glyph_count"],
                "RAW_MASK_PIXELS": e["raw_mask_pixels"],
                "NONEMPTY": e["nonempty"],
            }
        )
    graphics_inventory = []
    for g in graphics:
        graphics_inventory.append(
            {
                "GRAPHIC_ID": g["id"],
                "CATEGORY": g["category"],
                "DRAWING_INDEX": g["drawing_index"],
                "PAINT_ORDER": g["paint_order"],
                "PDF_DISPLAY_SEQNO": g.get("display_seqno", "UNKNOWN"),
                "OWNER_PATH_ANCHOR": g.get("owner_path_anchor", f"DRAWING_INDEX={g['drawing_index']}"),
                "PDF_BBOX_PT": ",".join(f"{v:.4f}" for v in g["bbox_pt"]),
                "NATIVE_MASK_BBOX_PX": fmt_box(g["mask"].bbox),
                "RAW_MASK_PIXELS": g["mask"].pixels,
                "FOREGROUND": g["foreground"],
                "STROKE_RGB": g["stroke_rgb"],
                "FILL_RGB": g["fill_rgb"],
                "DASHES": g["dashes"],
                "PRE_HALO_FINAL_EVIDENCE": "yes" if "pre_mask" in g else "not-applicable",
                "PRE_HALO_TEXTURE_RAW_PIXELS": g["pre_pattern_mask"].pixels if "pre_pattern_mask" in g else "N/A",
                "PRE_HALO_TEXTURE_MASK": (
                    safe_png_filename(f"{g['id']}_pre_halo_texture") if "pre_pattern_mask" in g else "N/A"
                ),
            }
        )
    map_rows = []
    for g in glyphs:
        map_rows.append(
            {
                "GLYPH_ID": g["glyph_id"],
                "ELEMENT_ID": g["element_id"],
                "PARENT_ID": g["parent_id"],
                "EXPECTED_CHAR": g["expected_char"],
                "UNICODE": g["unicode"],
                "PDF_CHAR_BBOX_PT": ",".join(f"{v:.4f}" for v in g["char_bbox_pt"]),
                "NATIVE_CHAR_BBOX_PX": fmt_box(g["char_bbox_px"]),
                "SVG_USE_INDEX": g["svg_use_index"],
                "SVG_USE_X_PT": g["svg_x_pt"],
                "SVG_USE_Y_PT": g["svg_y_pt"],
                "SVG_SHAPE_ID": g["svg_shape_id"],
                "SVG_SHAPE_PATH_COUNT": g["svg_shape_path_count"],
                "SVG_SHAPE_PATH_CHAR_COUNT": g["svg_shape_path_char_count"],
                "SVG_SHAPE_NONEMPTY": g["svg_shape_nonempty"],
                "SVG_PARENT_TAG": g["svg_parent_tag"],
                "SVG_PARENT_STYLE": g["svg_parent_style"],
                "SVG_PARENT_TRANSFORM": g["svg_parent_transform"],
                "SVG_USE_TRANSFORM": g["svg_use_transform"],
                "SVG_FILL_RGB": g["svg_fill_rgb"],
                "SVG_FILL_OPACITY": g["svg_fill_opacity"],
                "KNOWN_UNDERLAY_RGB": g["known_background_rgb"],
                "KNOWN_UNDERLAY_PROOF": g["known_background_rule"],
                "PDF_REPLAY_MAPPING_PASS": g.get("pdf_replay_mapping_pass", False),
                "PDF_CONTENT_OP_INDEX": g.get("pdf_replay_record", {}).get("op_index", "UNKNOWN"),
                "PDF_CID_HEX": g.get("pdf_replay_cid_hex", "UNKNOWN"),
                "PDF_TEXTTRACE_SEQNO": g.get("pdf_texttrace_seqno", "UNKNOWN"),
                "PDF_TEXTTRACE_MAPPING_PASS": g.get("pdf_texttrace_mapping_pass", False),
                "PDF_REPLAY_ALPHA_NONZERO_PIXELS": g["pdf_replay_alpha_nonzero_pixels"],
                "PDF_REPLAY_ALPHA_GE20_PIXELS": g["pdf_replay_alpha_ge20_pixels"],
                "REPLAY_EFFECTIVE_FOREGROUND_GE20_PIXELS": g["replay_effective_foreground_ge20_pixels"],
                "DIRECT_EFFECTIVE_FOREGROUND_GE20_PIXELS": g["direct_effective_foreground_ge20_pixels"],
                "PDF_REPLAY_GRID_PASS": g["pdf_replay_grid_pass"],
                "PDF_SVG_FILL_OPACITY_CROSSCHECK": g["pdf_svg_fill_crosscheck_pass"],
                "OFFICIAL_FINAL_VISIBLE_GRID_PASS": g["final_visibility_grid_pass"],
                "OFFICIAL_FINAL_VISIBLE_PIXELS": g["official_final_visible_pixels"],
                "OFFICIAL_FINAL_VISIBLE_GE20_PIXELS": g["official_final_visible_ge20_pixels"],
                "RAW_EFFECTIVE_TO_ISOLATED_CID_ALPHA_MISSING_PIXELS": g["raw_effective_to_isolated_cid_alpha_missing_pixels"],
                "OFFICIAL_TARGET_MASK_FOREIGN_PIXELS": g["official_target_mask_foreign_pixels"],
                "REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE_PIXELS": g["real_later_paint_occluded_raw_effective_pixels"],
                "BASELINE_DIRECT_NATIVE_MISMATCH_PIXELS": g["baseline_direct_mismatch_pixels"],
                "BASELINE_DIRECT_SAFE_SUBTHRESHOLD_AA_DRIFT_PIXELS": g["baseline_direct_safe_subthreshold_drift_pixels"],
                "BASELINE_DIRECT_UNSAFE_MISMATCH_PIXELS": g["baseline_direct_unsafe_mismatch_pixels"],
                "BASELINE_DIRECT_EFFECTIVE_XOR_PIXELS": g["baseline_direct_effective_xor_pixels"],
                "BASELINE_REPLAY_EFFECTIVE_XOR_PIXELS": g["baseline_replay_effective_xor_pixels"],
                "DIRECT_REPLAY_EFFECTIVE_XOR_PIXELS": g["direct_replay_effective_xor_pixels"],
                "RAW_EFFECTIVE_OUTSIDE_ISOLATED_CID_ALPHA_PIXELS": g["raw_effective_outside_isolated_alpha_pixels"],
                "BASELINE_EFFECTIVE_OUTSIDE_ISOLATED_CID_ALPHA_PIXELS": g["baseline_effective_outside_isolated_alpha_pixels"],
                "TRANSPARENT_ALPHA_EFFECTIVE_OVERPREDICT_PIXELS_DIAGNOSTIC": g["transparent_alpha_effective_overpredict_pixels"],
                "TRANSPARENT_ALPHA_EFFECTIVE_UNDERPREDICT_PIXELS_DIAGNOSTIC": g["transparent_alpha_effective_underpredict_pixels"],
                "REPLAY_FLOAT_VS_INTEGER_EFFECTIVE_XOR_PIXELS": g["replay_float_vs_integer_effective_xor_pixels"],
                "QUANTIZATION_BOUNDARY_EXPLANATION_PASS": g["quantization_boundary_explanation_pass"],
                "FINAL_VISIBLE_DELTA_OUTSIDE_TARGET_ALPHA_PIXELS": g["final_visible_delta_outside_target_alpha_pixels"],
                "PDF_REPLAY_ISOLATION_PASS": g["shape_isolation_pass"],
                "COLOUR_RAY_CANDIDATE_PIXELS": g["colour_ray_pixels"],
                "PATH_TO_COLOUR_RAY_INTERSECTION_PIXELS": g["path_colour_intersection_pixels"],
                "COLOUR_RAY_NONPATH_PIXELS": g["colour_ray_nonpath_pixels"],
                "NONPATH_ATTRIBUTION_IDS": g["nonpath_attribution_ids"],
                "UNEXPLAINED_COLOUR_RAY_NONPATH_PIXELS": g["unexplained_colour_candidate_pixels"],
                "NATIVE_ACTUAL_INK_BBOX_PX": g["raw_mask_bbox_px"],
                "NATIVE_RAW_MASK_PIXELS": g["raw_mask_pixels"],
                "RAW_MASK_FILENAME": g["raw_mask_filename"],
                "PDF_REPLAY_SUPPORT_FILENAME": g["shape_support_mask_filename"],
                "OFFICIAL_FINAL_VISIBLE_FILENAME": g["final_visible_mask_filename"],
                "COLOUR_RAY_CANDIDATE_FILENAME": g["colour_ray_mask_filename"],
                "COLOUR_RAY_NONPATH_FILENAME": g["nonpath_mask_filename"],
                "COMPLETENESS_MISSING_FILENAME": g["missing_mask_filename"],
                "FOREIGN_PIXEL_FILENAME": g["foreign_mask_filename"],
                "REAL_LATER_PAINT_OCCLUDED_FILENAME": g["occluded_mask_filename"],
                "MAPPING_STATUS": g["mapping_status"],
                "MANUAL_CONTACT_SHEET": "glyph_contact_sheets/ (all glyphs, 8x-nearest source crops)",
            }
        )
    write_csv(ROOT / "after_font_audit.csv", font_rows)
    write_csv(ROOT / "after_pixel_measurements.csv", p_rows)
    write_csv(ROOT / "after_overlap_report.csv", required_relations)
    write_csv(ROOT / "semantic_text_inventory.csv", semantic_text_inventory)
    write_csv(ROOT / "pdf_text_span_inventory.csv", text_inventory)
    write_csv(ROOT / "final_visible_graphics_inventory.csv", graphics_inventory)
    write_csv(ROOT / "all_foreground_pairs.csv", all_pairs)
    write_csv(ROOT / "required_relations.csv", required_relations)
    write_csv(ROOT / "glyph_shape_mapping.csv", map_rows)
    write_csv(ROOT / "glyph_pdf_content_replay_manifest.csv", replay_manifest_rows)
    write_csv(ROOT / "glyph_final_visibility_knockout_manifest.csv", final_visibility_manifest_rows)
    write_csv(ROOT / "glyph_contact_sheet_coverage.csv", glyph_contact_coverage)
    write_csv(ROOT / "glyph_manual_review.csv", glyph_manual_review_rows)
    write_csv(ROOT / "manual_visual_harmony_ledger.csv", visual_harmony_review_rows)
    write_csv(ROOT / "glyph_mask_contamination_report.csv", glyph_contamination_rows)
    write_csv(ROOT / "glyph_background_and_completeness_ledger.csv", glyph_background_ledger)
    write_csv(ROOT / "glyph_colour_ray_nonpath_attribution.csv", glyph_nonpath_rows)
    write_csv(
        ROOT / "glyph_subthreshold_aa_drift_ledger.csv",
        glyph_subthreshold_drift_rows,
        fieldnames=[
            "GLYPH_ID", "EXPECTED_CHAR", "X_NATIVE", "Y_NATIVE", "DIRECT_OFFICIAL_RGB",
            "OFFICIAL_KNOCKOUT_LOCAL_BACKGROUND_RGB", "CROP_BASELINE_RGB",
            "DIRECT_EFFECTIVE_CONTRAST_MAX_RGB", "BASELINE_EFFECTIVE_CONTRAST_MAX_RGB",
            "REPLAY_ALPHA_0_255", "DIRECT_EFFECTIVE_GE20", "BASELINE_EFFECTIVE_GE20",
            "REPLAY_EFFECTIVE_GE20", "EFFECTIVE_SUPPORT_XOR_DIRECT_BASELINE",
            "EFFECTIVE_SUPPORT_XOR_BASELINE_REPLAY", "EFFECTIVE_SUPPORT_XOR_DIRECT_REPLAY", "DISPOSITION",
        ],
    )
    write_csv(
        ROOT / "glyph_replay_integer_lattice_quantization_ledger.csv",
        glyph_quantization_boundary_rows,
        fieldnames=[
            "GLYPH_ID", "EXPECTED_CHAR", "X_NATIVE", "Y_NATIVE", "PDF_FILL_RGB_0_1",
            "OFFICIAL_KNOCKOUT_LOCAL_BACKGROUND_RGB", "REPLAY_ALPHA_0_255",
            "REPLAY_FLOAT_EFFECTIVE_CONTRAST_MAX_RGB", "REPLAY_INTEGER_LATTICE_EFFECTIVE_CONTRAST_MAX_RGB",
            "REPLAY_FLOAT_EFFECTIVE_GE20", "REPLAY_INTEGER_EFFECTIVE_GE20",
            "BASELINE_EFFECTIVE_GE20", "DIRECT_EFFECTIVE_GE20", "ISOLATED_CID_ALPHA_SUPPORT_GT0",
            "DIAGNOSTIC_CLASS", "EXPLANATION_PASS", "EXPLANATION",
        ],
    )
    write_csv(ROOT / "glyph_file_manifest.csv", glyph_file_rows)
    write_csv(ROOT / "glyph_safe_filename_map.csv", safe_filename_rows)
    (ROOT / "glyph_manual_review_identity.json").write_text(
        json.dumps(
            {
                "schema": MANUAL_LEDGER_SCHEMA_VERSION,
                "evidence_identity_sha256": manual_evidence_identity,
                "glyph_count": len(glyphs),
                "visual_harmony_row_count": len(visual_harmony_review_rows),
                "identity_payload": evidence_identity_payload,
                "status": "PENDING_INDIVIDUAL_SA1_8X_REVIEW",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    d_fail = [r for r in element_measurements if r["d_pass"] is False]
    e_fail = [r for r in element_measurements if r["e_pass"] is False]
    font_fail = [r for r in font_rows if r["FONT_PASS"] is False]
    pixel_fail = [g for g in glyphs if not g["pixel_pass"]]
    shape_isolation_fail = [g for g in glyphs if not g["shape_isolation_pass"]]
    # This construction pass emits a deliberately PENDING per-glyph ledger.
    # A separate post-inspection verifier may turn it into a terminal result
    # only after exactly 193 individual reviewer rows are populated and match
    # the immutable R8 identity; no bulk flag can alter this status.
    manual_glyph_review_pass = False
    overlap_fail = [r for r in required_relations if int(r["overlap_pixel_count"]) != 0]
    clearance_fail = [r for r in required_relations if r["status"] == "FAIL" and int(r["overlap_pixel_count"]) == 0]
    empty_masks = [
        name
        for name, mask in [(g["glyph_id"], glyph_masks[g["glyph_id"]]) for g in glyphs]
        + [(o["id"], o["mask"]) for o in text_objects]
        + [(g["id"], g["mask"]) for g in graphics]
        if not mask.pixels
    ]
    source_font_pass = not font_fail
    pixel_height_pass = not pixel_fail
    same_class_pass = not d_fail
    role_ratio_pass = not e_fail
    relation_pass = not overlap_fail and not clearance_fail
    mapping_pass = (
        not map_errors
        and not texttrace_errors
        and not graphic_errors
        and not pdf_replay_errors
        and not glyph_file_errors
        and not quantization_boundary_errors
        and not shape_isolation_fail
        and not glyph_graphic_cross
        and glyph_pair_overlap == 0
    )
    mask_integrity_pass = not empty_masks
    clip_pass = clip_count == 0

    # Final visual/mathematical statements are deliberately conservative: the
    # automated result is not allowed to claim PASS while a mapping or raw mask
    # invariant is unknown.  Manual findings are completed by the reviewer
    # after examining generated canonical/8x views.
    machine_integrity = {
        "result_at_machine_stage": "PASS" if all([source_font_pass, pixel_height_pass, same_class_pass, role_ratio_pass, relation_pass, mapping_pass, mask_integrity_pass, clip_pass, manual_glyph_review_pass]) else "FAIL",
        "official_pdf": str(OFFICIAL_PDF),
        "physical_page": PAGE_NUMBER_PHYSICAL,
        "printed_page": PRINTED_PAGE,
        "native_grid": {"width": page_w, "height": page_h, "dpi": DPI, "scale_px_per_pdf_pt": SCALE},
        "figure_crop_px": {"x0": CROP_BOX_PX[0], "y0": CROP_BOX_PX[1], "x1": CROP_BOX_PX[2], "y1": CROP_BOX_PX[3]},
        "pdf_text_span_count": len(elements),
        "semantic_text_element_count": len(relation_text_objects),
        "glyph_count": len(glyphs),
        "svg_glyph_use_count": len(uses),
        "final_visible_graphics_and_background_count": len(graphics),
        "foreground_object_count": len(foreground),
        "all_unordered_foreground_pair_count": len(all_pairs),
        "required_relation_count": len(required_relations),
        "critical_relation_count": len(critical_relations),
        "critical_glyph_count": len(critical_glyphs),
        "empty_mask_count": len(empty_masks),
        "glyph_to_graphic_intersection_count": len(glyph_graphic_cross),
        "same_parent_glyph_mask_overlap_px": glyph_pair_overlap,
        "glyph_final_paint_ownership_removal_px": sum(int(r["PIXELS_REMOVED_TO_LATER_SVG_USE"]) for r in glyph_ownership_rows),
        "glyph_path_isolation_fail_count": len(shape_isolation_fail),
        "pdf_replay_error_count": len(pdf_replay_errors),
        "texttrace_mapping_error_count": len(texttrace_errors),
        "graphic_inventory_error_count": len(graphic_errors),
        "glyph_file_manifest_error_count": len(glyph_file_errors),
        "glyph_file_manifest_row_count": len(glyph_file_rows),
        "safe_filename_map_row_count": len(safe_filename_rows),
        "official_final_visible_raw_effective_outside_isolated_cid_alpha_pixel_total": sum(g["raw_effective_to_isolated_cid_alpha_missing_pixels"] for g in glyphs),
        "official_target_mask_foreign_pixel_total": sum(g["official_target_mask_foreign_pixels"] for g in glyphs),
        "real_later_paint_occluded_raw_effective_pixel_total": sum(g["real_later_paint_occluded_raw_effective_pixels"] for g in glyphs),
        "baseline_direct_native_mismatch_pixel_total": sum(g["baseline_direct_mismatch_pixels"] for g in glyphs),
        "baseline_direct_safe_subthreshold_aa_drift_pixel_total": sum(g["baseline_direct_safe_subthreshold_drift_pixels"] for g in glyphs),
        "baseline_direct_unsafe_mismatch_pixel_total": sum(g["baseline_direct_unsafe_mismatch_pixels"] for g in glyphs),
        "baseline_direct_effective_support_xor_pixel_total": sum(g["baseline_direct_effective_xor_pixels"] for g in glyphs),
        "transparent_alpha_vs_baseline_effective_support_xor_pixel_total_diagnostic": sum(g["baseline_replay_effective_xor_pixels"] for g in glyphs),
        "transparent_alpha_vs_direct_effective_support_xor_pixel_total_diagnostic": sum(g["direct_replay_effective_xor_pixels"] for g in glyphs),
        "raw_effective_outside_isolated_cid_alpha_pixel_total": sum(g["raw_effective_outside_isolated_alpha_pixels"] for g in glyphs),
        "baseline_effective_outside_isolated_cid_alpha_pixel_total": sum(g["baseline_effective_outside_isolated_alpha_pixels"] for g in glyphs),
        "transparent_alpha_effective_overpredict_pixel_total_diagnostic": sum(g["transparent_alpha_effective_overpredict_pixels"] for g in glyphs),
        "transparent_alpha_effective_underpredict_pixel_total_diagnostic": sum(g["transparent_alpha_effective_underpredict_pixels"] for g in glyphs),
        "subthreshold_aa_drift_ledger_row_count": len(glyph_subthreshold_drift_rows),
        "replay_float_to_integer_quantization_boundary_row_count": len(glyph_quantization_boundary_rows),
        "replay_quantization_boundary_explanation_error_count": len(quantization_boundary_errors),
        "final_visible_delta_outside_target_alpha_pixel_total": sum(g["final_visible_delta_outside_target_alpha_pixels"] for g in glyphs),
        "colour_ray_nonpath_pixel_total": sum(g["colour_ray_nonpath_pixels"] for g in glyphs),
        "unexplained_colour_ray_nonpath_pixel_total": sum(g["unexplained_colour_candidate_pixels"] for g in glyphs),
        "colour_ray_nonpath_owner_ledger_row_count": len(glyph_nonpath_rows),
        "glyph_contact_sheet_coverage_count": len(glyph_contact_coverage),
        "glyph_manual_review_template_row_count": len(glyph_manual_review_rows),
        "manual_visual_harmony_template_row_count": len(visual_harmony_review_rows),
        "glyph_manual_review_identity_sha256": manual_evidence_identity,
        "glyph_manual_8x_review_pass": manual_glyph_review_pass,
        "font_fail_count": len(font_fail),
        "pixel_fail_count": len(pixel_fail),
        "d_fail_count": len(d_fail),
        "e_fail_count": len(e_fail),
        "overlap_fail_count": len(overlap_fail),
        "clearance_fail_count": len(clearance_fail),
        "clip_count": clip_count,
        "mapping_error_count": len(map_errors),
        "failure_ids": [
            *[g["glyph_id"] for g in pixel_fail],
            *[r["measurement_id"] for r in d_fail],
            *[r["measurement_id"] for r in e_fail],
            *[r["relation_id"] for r in overlap_fail + clearance_fail],
            *[f"MAP:{e}" for e in map_errors],
            *[f"TEXTTRACE:{e}" for e in texttrace_errors],
            *[f"GRAPHIC:{e}" for e in graphic_errors],
            *[f"PDF_REPLAY:{e}" for e in pdf_replay_errors],
            *[f"FILE:{e}" for e in glyph_file_errors],
            *[f"QUANT:{e}" for e in quantization_boundary_errors],
            *[f"SHAPE:{g['glyph_id']}" for g in shape_isolation_fail],
            *(["MANUAL_GLYPH_8X_REVIEW_PENDING"] if not manual_glyph_review_pass else []),
            *[f"EMPTY:{e}" for e in empty_masks],
        ],
        "required_files": {
            "full_page_200dpi": FULL_200.name,
            "full_page_300dpi": FULL_300.name,
            "figure_crop_300dpi": "figure_crop_300dpi.png",
            "standalone_300dpi": "standalone_300dpi.png",
            "grayscale_300dpi": "grayscale_300dpi.png",
            "font_audit": "after_font_audit.csv",
            "pixel_measurements": "after_pixel_measurements.csv",
            "overlap_report": "after_overlap_report.csv",
            "text_overlay": "after_text_measurement_overlay_300dpi.png",
            "pdf_content_replay_manifest": "glyph_pdf_content_replay_manifest.csv",
            "final_visibility_knockout_manifest": "glyph_final_visibility_knockout_manifest.csv",
            "glyph_file_manifest": "glyph_file_manifest.csv",
            "safe_filename_map": "glyph_safe_filename_map.csv",
            "manual_review_ledger": "glyph_manual_review.csv",
            "manual_review_identity": "glyph_manual_review_identity.json",
            "manual_visual_harmony_ledger": "manual_visual_harmony_ledger.csv",
            "subthreshold_aa_drift_ledger": "glyph_subthreshold_aa_drift_ledger.csv",
            "replay_integer_lattice_quantization_ledger": "glyph_replay_integer_lattice_quantization_ledger.csv",
            "effective_foreground_quantization_protocol": "effective_foreground_quantization_protocol.md",
        },
        "contact_sheets": contact_sheets,
    }
    (ROOT / "machine_integrity.json").write_text(json.dumps(machine_integrity, ensure_ascii=False, indent=2), encoding="utf-8")

    render_manifest = {
        "official_pdf_only_input": str(OFFICIAL_PDF),
        "figure_uid": "FIG-P634-01",
        "figure_number": "图 33.3",
        "physical_page": PAGE_NUMBER_PHYSICAL,
        "printed_page": PRINTED_PAGE,
        "page_size_pt": [float(page_rect.width), float(page_rect.height)],
        "native_300dpi_grid": [page_w, page_h],
        "render_method": "pdftocairo -png -singlefile -r 300 -f 682 -l 682 main_full.pdf full_page_300dpi",
        "crop_method": "Pillow integer pixel crop from full_page_300dpi.png; no resize",
        "crop_box_native_px": list(CROP_BOX_PX),
        "count_coordinate_system": "full_page_300dpi native 1:1 pixels",
        "eight_x_policy": "nearest-neighbour visual confirmation only; no thresholding or measurements use 8x images",
    }
    (ROOT / "render_manifest.json").write_text(json.dumps(render_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Audit reports that make required N/A states explicit rather than silently
    # treating cross-script values as comparable.
    (ROOT / "paint_order_and_halo_evidence.md").write_text(
        "# FIG-P634-01 paint order and real halo evidence\n\n"
        "Source lines 28--35 draw four patterned completed cards first, then draw four `sl634-halo` nodes with `fill=white, draw=none` over their text areas. "
        "The final PDF drawing order is recovered as drawings 2--9. For each completed card, `masks/paint_order/` retains three native-coordinate masks: pre-occlusion card support, the true opaque halo rectangle, and pre minus halo (final-visible background support). "
        "The quality relations use only the separate final-visible border/pattern raw masks in `masks/graphics/`; no dilation, white page box, or fabricated halo is used to erase a collision.\n",
        encoding="utf-8",
    )
    (ROOT / "four_views.md").write_text(
        "# Four-view inspection basis\n\n"
        "- `full_page_200dpi.png`: direct R95 page render, page integration.\n"
        "- `figure_crop_300dpi.png`: integer crop from direct native 300dpi full page; canonical pixel-measurement context.\n"
        "- `standalone_300dpi.png`: identical unscaled native crop because the official R95 final PDF is the sole allowed input; no independent source render is substituted.\n"
        "- `grayscale_300dpi.png`: native crop converted only for visual grayscale hierarchy inspection; never used for measurement.\n"
        "- `glyph_contact_sheets/`: all glyphs as native source crops enlarged with nearest-neighbour solely for manual char↔shape checking.\n",
        encoding="utf-8",
    )
    (ROOT / "after_visual_acceptance.md").write_text(
        "# FIG-P634-01 visual acceptance — nonterminal R8 construction\n\n"
        "- STATUS: PENDING_INDIVIDUAL_193_GLYPH_8X_REVIEW\n"
        "- COLOR_VIEW: PENDING\n"
        "- GRAYSCALE_VIEW: PENDING\n"
        "- FULL_PAGE_INTEGRATION: PENDING\n"
        "- LOCAL_300DPI_VIEW: PENDING\n"
        "- MATH_SEMANTIC_REVIEW: PENDING_HUMAN_CONFIRMATION\n"
        "- FONT_VISUAL_HARMONY_PASS: PENDING\n\n"
        "This file cannot be treated as an acceptance decision.  The R8 glyph ledger is intentionally emitted with 193 individual PENDING rows tied to `glyph_manual_review_identity.json`; `manual_visual_harmony_ledger.csv` separately contains every view × panel/role/script PENDING reviewer row.\n",
        encoding="utf-8",
    )
    (ROOT / "math_semantic_review.md").write_text(
        "# Mathematical and textual consistency review\n\n"
        "The diagram and adjacent paragraph agree on the system-scan invariant: at substep `j`, the left segment of `x^{[j]}` contains same-round updates, the right segment retains prior-round values, and only `x^{[d]} = x^{(t)}` is a completed-round sample. "
        "The source diagram, caption, reading-order paragraph, and V5-C04 surrounding text all preserve this distinction; arrows are directional update-order aids rather than a claim of parallel update. "
        "The visual review must still use the native/8x packages for final human confirmation of formula, state-card, arrow, border and texture separations.\n",
        encoding="utf-8",
    )
    (ROOT / "effective_foreground_quantization_protocol.md").write_text(
        "# Effective-foreground closure on the official 8-bit lattice\n\n"
        "For each official CID and each native coordinate, the local background is the same-coordinate official knockout RGB `K` (the official page with only that CID changed to `Tr 3`).  The official supports are:\n\n"
        "- `B = max_abs(crop-baseline RGB − K) >= 20`;\n"
        "- `D = max_abs(direct full-page native RGB − K) >= 20`;\n"
        "- `R = max_abs(round_8bit(alpha/255 × official_fill_RGB + (1−alpha/255) × K) − K) >= 20` (diagnostic only).\n\n"
        "`B` and `D` are rendered by the same official PDF renderer and must have coordinate-wise `B XOR D = 0`; `D` is the final-visible raw mask.  Every `D` pixel must be inside exactly the isolated official CID alpha support, and the raw mask must have zero foreign pixels.  `B & ~D` is the only later-paint occlusion test and must be zero.  The transparent CID replay proves actual path/source identity but is not a raw-mask authority: the 8-bit `R` diagnostic can overpredict a coloured-background threshold coordinate.  Every such coordinate is enumerated and classified in `glyph_replay_integer_lattice_quantization_ledger.csv`; none may be UNKNOWN.\n\n"
        f"R8 transparency/integer diagnostic rows: {len(glyph_quantization_boundary_rows)}; unexplained rows: {len(quantization_boundary_errors)}.  The four `T020` alpha=23 overpredict coordinates retain B/D, background, float and integer values in that ledger.\n",
        encoding="utf-8",
    )
    print(json.dumps(machine_integrity, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
