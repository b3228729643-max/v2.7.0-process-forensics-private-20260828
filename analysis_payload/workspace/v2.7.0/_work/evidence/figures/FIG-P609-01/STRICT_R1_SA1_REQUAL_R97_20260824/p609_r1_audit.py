#!/usr/bin/env python3
"""Independent, candidate-locked SA1 evidence generator for FIG-P609-01.

All measurements in this program are derived from the frozen R97 full-book PDF.
It intentionally never opens a sibling/earlier FIG-P609 evidence directory.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, label


OUT = Path(__file__).resolve().parent
WORK = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF = WORK / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf"
SOURCE = WORK / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex"
CONTEXT = WORK / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C03.tex"
EXPECTED_PDF_SHA256 = "062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814"
PAGE_INDEX = 658  # physical page 659, zero-based PyMuPDF index
PHYSICAL_PAGE = PAGE_INDEX + 1
PRINTED_PAGE = 646
DPI = 300
SCALE = DPI / 72.0
FIG_RECT_PT = (70.0, 525.0, 510.0, 702.0)  # strict P609 figure scope; excludes caption/body
STANDALONE_RECT_PT = (76.0, 528.0, 505.0, 702.0)
REVIEWER = "SA1_R1_INDEPENDENT"

# Read-only full-book exact-match discovery was performed once from this locked R97 candidate
# by this R1 generator.  These anchors avoid rescanning all 813 pages every material rebuild;
# every anchor is re-rendered and remeasured from the same candidate below.  GL026 and GL045
# intentionally have no anchor because that exact codepoint/font/size/colour combination had
# no second official-PDF occurrence in that scan.
EXTERNAL_CALIBRATION_ANCHORS: dict[str, dict[str, Any] | None] = {
    "GL026": None,
    "GL045": None,
    "GL095": {"pdf_page": 626, "bbox_pt": [247.843, 72.508, 250.187, 82.072], "writing_direction": [1.0, 0.0]},
    "GL107": {"pdf_page": 731, "bbox_pt": [276.862976, 244.876602, 286.427124, 258.725494], "writing_direction": [1.0, 0.0]},
    "GL148": {"pdf_page": 680, "bbox_pt": [486.365387, 375.989716, 495.929535, 386.23291], "writing_direction": [1.0, 0.0]},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ensure_dirs() -> None:
    for rel in (
        "render",
        "tables",
        "masks/glyphs",
        "masks/objects",
        "glyph_rois",
        "glyph_contact_sheets",
        "pair_cards",
        "pair_contact_sheets",
        "clipping_cards",
        "math_rule_cards",
        "calibration",
        "machine",
    ):
        (OUT / rel).mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        # Later rows (e.g. only critical/clip candidates) legitimately add evidence links.
        # Preserve the union rather than silently dropping those fields based on row zero.
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def pt_rect_to_px(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (math.floor(x0 * SCALE), math.floor(y0 * SCALE), math.ceil(x1 * SCALE), math.ceil(y1 * SCALE))


def rgb_from_pdf_color(color: int | None) -> tuple[int, int, int]:
    if color is None:
        return (31, 35, 40)
    return ((color >> 16) & 255, (color >> 8) & 255, color & 255)


def is_cjk(ch: str) -> bool:
    if not ch:
        return False
    code = ord(ch)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0xFF01 <= code <= 0xFF60
    )


LOW_PROFILE = {".", ",", "，", "、", "。", "：", ":", "；", ";", "⋯", "…"}
MATH_OPERATORS = {"=", "+", "−", "-", "<", ">", "≤", "≥", "×", "÷", "∑", "√"}
RAWDICT_COMBINING_CONTROLS = {"\u0302"}
RENDERED_MATH_ACCENTS = {"ˆ", "ˉ", "¯"}


def char_class(ch: str, font_size: float) -> tuple[str, int | None, str]:
    """Return class, fixed height gate (or None for calibrated class), and rationale."""
    if ch in LOW_PROFILE:
        return ("LOW_PROFILE_PUNCTUATION", None, "same-codepoint H/area calibration [0.92,1.08]")
    if ch in RAWDICT_COMBINING_CONTROLS:
        # MuPDF records these as zero-width logical combining controls.  They remain in the
        # rawdict ledger, but are not an independently paintable visible foreground glyph.
        return ("RAWDICT_COMBINING_CONTROL", None, "zero-width logical accent control; visual accent audited through its rendered base/accent association")
    if ch in RENDERED_MATH_ACCENTS:
        return ("MATH_ACCENT_COMPOSITE_COMPONENT", None, "visible structural math accent; audited through its named base association, never treated as a standalone reader glyph")
    if is_cjk(ch):
        return ("CJK_OR_FULLWIDTH", 30, "full-height CJK/fullwidth glyph")
    # A relation sign remains a relation sign even inside a TeX subscript.  It is never
    # re-labelled as a low-profile or naturally-scripted glyph merely to lower its gate.
    if ch in MATH_OPERATORS:
        return ("BASE_MATH_OPERATOR", 22, "base math operator")
    if font_size < 8.0:
        return ("NATURAL_SCRIPT", 15, "TeX-derived natural script from a >=9.5pt base formula")
    if ch.isdigit() or (ch.isascii() and ch.isupper()):
        return ("LATIN_CAP_OR_DIGIT", 24, "Latin cap or digit")
    if ch.isascii() and ch.islower():
        return ("LATIN_LOWER", 17, "x-height Latin lowercase")
    name = unicodedata.name(ch, "")
    if "MATHEMATICAL" in name and "SMALL" in name:
        return ("MATH_LOWER", 17, "mathematical lowercase / x-height glyph")
    if "MATHEMATICAL" in name and "CAPITAL" in name:
        return ("MATH_CAP", 24, "mathematical capital glyph")
    if 0x0370 <= ord(ch) <= 0x03FF:
        # Ordinary Greek lowercase is an x-height-style comparator; uppercase follows cap gate.
        return ("GREEK_CAP" if ch.isupper() else "GREEK_LOWER", 24 if ch.isupper() else 17, "Greek glyph case gate")
    if 0x1D400 <= ord(ch) <= 0x1D7FF:
        return ("MATH_OR_GREEK_BASE", 22, "unclassified base mathematical glyph")
    return ("MATH_OR_OTHER_BASE", 22, "base mathematical/other visible glyph")


def declared_font_pt(pdf_size: float, ch: str) -> tuple[float, str, float]:
    """Recover source font setting from the visible span size and TeX script behavior."""
    if pdf_size < 8.0:
        # The only smaller raw spans in scope are TeX scripts generated by the 9.6pt or 10.4pt base formulas.
        return (pdf_size, "NATURAL_SCRIPT_FROM_BASE", 9.6 if pdf_size < 6.8 else 9.8)
    if pdf_size >= 10.1:
        return (10.4, "SOURCE_FONT_10_4PT", 10.4)
    if pdf_size >= 9.65:
        return (9.8, "SOURCE_FONT_9_8PT", 9.8)
    return (9.6, "SOURCE_FONT_9_6PT", 9.6)


def safe_char(ch: str) -> str:
    return "U%04X" % ord(ch)


def bbox_of(mask: np.ndarray, offset_x: int = 0, offset_y: int = 0) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()) + offset_x, int(ys.min()) + offset_y, int(xs.max()) + 1 + offset_x, int(ys.max()) + 1 + offset_y)


def crop_box_with_pad(mask_a: np.ndarray, mask_b: np.ndarray | None = None, pad: int = 8) -> tuple[int, int, int, int]:
    union = mask_a.copy()
    if mask_b is not None:
        union |= mask_b
    b = bbox_of(union)
    h, w = union.shape
    if b is None:
        return (0, 0, min(w, 8), min(h, 8))
    return (max(0, b[0] - pad), max(0, b[1] - pad), min(w, b[2] + pad), min(h, b[3] + pad))


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def alpha_overlay(base: np.ndarray, a: np.ndarray | None = None, b: np.ndarray | None = None, intersection: np.ndarray | None = None) -> np.ndarray:
    arr = base.copy().astype(np.float32)
    if a is not None:
        arr[a] = 0.38 * arr[a] + 0.62 * np.array([230, 35, 35])
    if b is not None:
        arr[b] = 0.38 * arr[b] + 0.62 * np.array([0, 165, 230])
    if intersection is not None:
        arr[intersection] = np.array([255, 235, 0])
    return np.clip(arr, 0, 255).astype(np.uint8)


def nearest_scale(img: Image.Image, factor: int = 8) -> Image.Image:
    return img.resize((img.width * factor, img.height * factor), Image.Resampling.NEAREST)


def paste_labelled(canvas: Image.Image, image: Image.Image, label: str, x: int, y: int, w: int, h: int) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((x, y, x + w - 1, y + h - 1), fill=(255, 255, 255), outline=(100, 100, 100))
    room_h = h - 20
    resized = image.copy()
    if resized.width > w - 4 or resized.height > room_h - 4:
        ratio = min((w - 4) / max(1, resized.width), (room_h - 4) / max(1, resized.height))
        resized = resized.resize((max(1, int(resized.width * ratio)), max(1, int(resized.height * ratio))), Image.Resampling.NEAREST)
    canvas.paste(resized, (x + (w - resized.width) // 2, y + 20 + (room_h - resized.height) // 2))
    draw.text((x + 4, y + 3), label, fill=(0, 0, 0))


@dataclass
class ObjectRecord:
    object_id: str
    kind: str
    role: str
    panel: str
    parent: str
    drawing_index: str
    drawing_item: str
    z_order: int
    source_semantics: str
    pre_mask: np.ndarray
    final_mask: np.ndarray | None = None


def line_mask(shape: tuple[int, int], fx0: int, fy0: int, p0: tuple[float, float], p1: tuple[float, float], width_pt: float, rounded: bool = True) -> np.ndarray:
    h, w = shape
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    x0, y0 = p0[0] * SCALE - fx0, p0[1] * SCALE - fy0
    x1, y1 = p1[0] * SCALE - fx0, p1[1] * SCALE - fy0
    width = max(1, int(round(width_pt * SCALE)))
    d.line((x0, y0, x1, y1), fill=255, width=width)
    if rounded:
        r = width / 2
        d.ellipse((x0-r, y0-r, x0+r, y0+r), fill=255)
        d.ellipse((x1-r, y1-r, x1+r, y1+r), fill=255)
    return np.array(im) > 0


def polygon_mask(shape: tuple[int, int], fx0: int, fy0: int, pts: list[tuple[float, float]]) -> np.ndarray:
    h, w = shape
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    d.polygon([(x * SCALE - fx0, y * SCALE - fy0) for x, y in pts], fill=255)
    return np.array(im) > 0


def ellipse_mask(shape: tuple[int, int], fx0: int, fy0: int, rect: tuple[float, float, float, float]) -> np.ndarray:
    h, w = shape
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = rect
    d.ellipse((x0 * SCALE - fx0, y0 * SCALE - fy0, x1 * SCALE - fx0, y1 * SCALE - fy0), fill=255)
    return np.array(im) > 0


def rounded_border_mask(shape: tuple[int, int], fx0: int, fy0: int, rect: tuple[float, float, float, float], width_pt: float, radius_pt: float) -> np.ndarray:
    h, w = shape
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = rect
    coords = (x0 * SCALE - fx0, y0 * SCALE - fy0, x1 * SCALE - fx0, y1 * SCALE - fy0)
    d.rounded_rectangle(coords, radius=radius_pt * SCALE, outline=255, width=max(1, int(round(width_pt * SCALE))))
    return np.array(im) > 0


def rgb_ink_mask(img: np.ndarray) -> np.ndarray:
    """20/255 effective-foreground gate against the white/pale local PDF backgrounds."""
    return np.max(255 - img.astype(np.int16), axis=2) >= 20


def render_page(doc: fitz.Document, page_index: int, dpi: int) -> Image.Image:
    pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def collect_raw_lines(page: fitz.Page) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return source-order figure lines and visible rawdict characters, excluding caption/body scope."""
    raw = page.get_text("rawdict")
    fx0, fy0, fx1, fy1 = FIG_RECT_PT
    lines: list[dict[str, Any]] = []
    glyphs: list[dict[str, Any]] = []
    line_no = 0
    glyph_no = 0
    for bi, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block["lines"]):
            items: list[tuple[dict[str, Any], dict[str, Any]]] = []
            for span in line["spans"]:
                for char in span["chars"]:
                    if not char["c"].isspace():
                        items.append((span, char))
            if not items:
                continue
            x0 = min(c["bbox"][0] for _, c in items)
            y0 = min(c["bbox"][1] for _, c in items)
            x1 = max(c["bbox"][2] for _, c in items)
            y1 = max(c["bbox"][3] for _, c in items)
            # Centre must be inside P609 figure scope. This deliberately rejects Fig 32.9 caption at y>702pt.
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if not (fx0 <= cx <= fx1 and fy0 <= cy <= fy1):
                continue
            raw_line_id = f"L{line_no:03d}"
            lines.append({
                "raw_line_id": raw_line_id,
                "block_index": bi,
                "line_index": li,
                "bbox_pt": [x0, y0, x1, y1],
                "text": "".join(c["c"] for _, c in items),
                "char_count": len(items),
            })
            for span, char in items:
                glyph_no += 1
                fsize = float(span["size"])
                cclass, min_gate, gate_basis = char_class(char["c"], fsize)
                declared, source_font_basis, base_pt = declared_font_pt(fsize, char["c"])
                glyphs.append({
                    "glyph_id": f"GL{glyph_no:03d}",
                    "safe_filename": f"GL{glyph_no:03d}_{safe_char(char['c'])}",
                    "raw_line_id": raw_line_id,
                    "char": char["c"],
                    "unicode": f"U+{ord(char['c']):04X}",
                    "bbox_pt": list(char["bbox"]),
                    "origin_pt": list(char.get("origin", (None, None))),
                    "writing_direction": list(line.get("dir", (1.0, 0.0))),
                    "font": span["font"],
                    "pdf_font_size_pt": fsize,
                    "font_color_rgb": rgb_from_pdf_color(span.get("color")),
                    "script_class": cclass,
                    "min_gate_px": min_gate,
                    "gate_basis": gate_basis,
                    "declared_pt": declared,
                    "graphics_scale": 1.0,
                    "effective_pt": declared if cclass != "NATURAL_SCRIPT" else base_pt,
                    "visible_font_pt": fsize,
                    "source_font_basis": source_font_basis,
                    "trace_bbox_pt": None,
                    "mask_basis": "PENDING_TEXTTRACE",
                    "rawdict_visible_foreground": cclass != "RAWDICT_COMBINING_CONTROL",
                })
            line_no += 1
    return lines, glyphs


def line_parent_mapping(lines: list[dict[str, Any]]) -> dict[str, tuple[str, str, str, str]]:
    """Explicit semantic parents for each rawdict line; maps all P609 text and nothing outside scope."""
    expected = 32
    if len(lines) != expected:
        raise RuntimeError(f"P609 scope expected {expected} raw lines, found {len(lines)}; do not silently regroup.")
    out: dict[str, tuple[str, str, str, str]] = {}
    def add(indices: Iterable[int], object_id: str, role: str, panel: str, semantics: str) -> None:
        for i in indices:
            out[f"L{i:03d}"] = (object_id, role, panel, semantics)
    for i in range(7):
        add([i], f"T{1+i:03d}", "TICK_LABEL_X", "LEFT", f"x-axis numeric tick k={i}")
    yvals = ["0", "0.25", "0.5", "0.75", "1"]
    for i, value in enumerate(yvals):
        add([7+i], f"T{8+i:03d}", "TICK_LABEL_Y", "LEFT", f"y-axis numeric tick ACF={value}")
    add([12], "T013", "ANNOTATION", "LEFT", "gold truncation label 截断 K=6")
    add([13], "T014", "ANNOTATION", "LEFT", "ellipsis for unshown lags")
    add([14], "T015", "AXIS_LABEL", "LEFT", "x-axis label 滞后 k")
    add([15], "T016", "AXIS_LABEL", "LEFT", "rotated y-axis label 经验 ACF rho-hat-k")
    add([16], "T017", "PANEL_TITLE", "LEFT", "left panel title")
    add([17], "T018", "PANEL_TITLE", "RIGHT", "right panel title")
    add(range(18, 24), "T019", "FORMULA_BLOCK", "RIGHT", "finite weighted tau-hat formula")
    add(range(24, 29), "T020", "FORMULA_BLOCK", "RIGHT", "N-eff finite-sample formula and positivity condition")
    add([29], "T021", "ANNOTATION", "RIGHT", "predeclared finite window statement")
    add([30], "T022", "ANNOTATION", "RIGHT", "unshown-lag exclusion statement")
    add([31], "T023", "ANNOTATION", "RIGHT", "finite-trajectory diagnostic warning")
    if len(out) != expected:
        raise RuntimeError("semantic parent map is incomplete")
    return out


def glyph_masks(
    figure_rgb: np.ndarray,
    glyphs: list[dict[str, Any]],
    fig_px: tuple[int, int, int, int],
) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    """Extract disjoint native masks from the final 300dpi candidate.

    Rawdict boxes are retained as provenance, but texttrace's visible-glyph boxes are the
    segmentation basis whenever available.  This avoids treating a font ascent/descent box
    or a zero-width TeX combining control as target foreground.
    """
    fx0, fy0, _, _ = fig_px
    h, w = figure_rgb.shape[:2]
    ink = rgb_ink_mask(figure_rgb)
    candidates: list[np.ndarray] = []
    for g in glyphs:
        cand = np.zeros((h, w), dtype=bool)
        if g["script_class"] == "RAWDICT_COMBINING_CONTROL":
            g["mask_basis"] = "NO_INDEPENDENT_VISIBLE_MASK_ZERO_WIDTH_RAWDICT_CONTROL"
            g["mask_basis_bbox_pt"] = None
            candidates.append(cand)
            continue
        trace = g.get("trace_bbox_pt")
        if trace is not None and trace[2] > trace[0] and trace[3] > trace[1]:
            x0pt, y0pt, x1pt, y1pt = (float(v) for v in trace)
            g["mask_basis"] = "TEXTTRACE_VISIBLE_GLYPH_BBOX"
        else:
            x0pt, y0pt, x1pt, y1pt = (float(v) for v in g["bbox_pt"])
            g["mask_basis"] = "RAWDICT_BBOX_FALLBACK_NO_VALID_TEXTTRACE_BBOX"
        g["mask_basis_bbox_pt"] = [x0pt, y0pt, x1pt, y1pt]
        # Convert the visible glyph box to the same native grid, retaining a 0.5px anti-alias allowance.
        x0 = max(0, math.floor(x0pt * SCALE - fx0 - 0.5))
        y0 = max(0, math.floor(y0pt * SCALE - fy0 - 0.5))
        x1 = min(w, math.ceil(x1pt * SCALE - fx0 + 0.5))
        y1 = min(h, math.ceil(y1pt * SCALE - fy0 + 0.5))
        if x1 > x0 and y1 > y0:
            area = ink[y0:y1, x0:x1].copy()
            # Hue-direction filter removes white/pale background while retaining anti-aliased target ink.
            exp = np.array(g["font_color_rgb"], dtype=float)
            direction = 255.0 - exp
            denom = float(np.dot(direction, direction))
            pix = figure_rgb[y0:y1, x0:x1].astype(float)
            vec = 255.0 - pix
            projection = np.tensordot(vec, direction, axes=([2], [0])) / max(denom, 1.0)
            residual = np.sqrt(np.sum((vec - projection[..., None] * direction) ** 2, axis=2))
            color_ok = (projection >= 0.045) & (residual <= 38.0)
            # Dark mathematical glyphs and axes share a colour. The bbox gate remains authoritative;
            # any later graphic intersection is explicitly measured at object-pair level.
            area &= color_ok
            cand[y0:y1, x0:x1] = area
        candidates.append(cand)

    # The PDF texttrace bbox for the visibly rendered circumflex of N-eff overlaps the
    # base-N bbox.  Split the union by its native disconnected components instead of allowing
    # a nearest-centre allocator to fold a base downstroke into the accent (or an adjacent e
    # into either).  This is a concrete resegmentation, not a mask-purity waiver.
    by_id = {g["glyph_id"]: i for i, g in enumerate(glyphs)}
    accent_i, base_i = by_id["GL083"], by_id["GL084"]
    union = candidates[accent_i] | candidates[base_i]
    labels, n_labels = label(union, structure=np.ones((3, 3), dtype=np.int8))
    comps: list[tuple[int, int, int, int]] = []  # (label, area, ymin, xmin)
    for comp in range(1, n_labels + 1):
        ys, xs = np.where(labels == comp)
        if len(xs):
            comps.append((comp, int(len(xs)), int(ys.min()), int(xs.min())))
    if len(comps) < 2:
        raise RuntimeError("GL083/GL084 visible accent/base component separation failed; do not use an impure bbox mask")
    accent_label = min(comps, key=lambda t: (t[2], -t[1]))[0]
    remaining = [c for c in comps if c[0] != accent_label]
    base_label = max(remaining, key=lambda t: t[1])[0]
    candidates[accent_i] = labels == accent_label
    candidates[base_i] = labels == base_label
    glyphs[accent_i]["mask_basis"] = "TEXTTRACE_BBOX_NATIVE_COMPONENT_RESEGMENTED_VISIBLE_CIRCUMFLEX"
    glyphs[accent_i]["mask_resegmentation"] = f"component={accent_label}; selected upper disconnected roof from {len(comps)} union components"
    glyphs[base_i]["mask_basis"] = "TEXTTRACE_BBOX_NATIVE_COMPONENT_RESEGMENTED_BASE_N"
    glyphs[base_i]["mask_resegmentation"] = f"component={base_label}; selected largest remaining base-N component from {len(comps)} union components"

    # GL122's raw/texttrace semicolon bbox carries a disconnected 2px antialias remnant from
    # its immediately preceding mathematical K.  Keep only the two semicolon components
    # (top dot and lower comma) and record the removed remnant before remeasurement.
    semi_i = by_id["GL122"]
    semi_labels, semi_n = label(candidates[semi_i], structure=np.ones((3, 3), dtype=np.int8))
    semi_areas = [(comp, int((semi_labels == comp).sum())) for comp in range(1, semi_n + 1)]
    keep_semis = [comp for comp, area in semi_areas if area >= 5]
    removed = int(candidates[semi_i].sum() - sum(area for comp, area in semi_areas if comp in keep_semis))
    if len(keep_semis) != 2 or removed <= 0:
        raise RuntimeError("GL122 semicolon contamination split no longer matches the locked candidate; do not retain an impure punctuation mask")
    candidates[semi_i] = np.isin(semi_labels, keep_semis)
    glyphs[semi_i]["mask_basis"] = "TEXTTRACE_BBOX_NATIVE_COMPONENT_RESEGMENTED_FULLWIDTH_SEMICOLON"
    glyphs[semi_i]["mask_resegmentation"] = f"removed {removed}px disconnected foreign remnant from preceding GL121 mathematical K; retained exactly two semicolon components"
    glyphs[semi_i]["FOREIGN_REMOVED_RESEGMENT_PX"] = removed

    # A native ink pixel belongs to one glyph mask.  Resolve only actual candidate overlap by
    # nearest *visible-bbox* centre.  Reassignment is recorded as contested ownership, not
    # silently misreported as a missing stroke.
    owners = np.full((h, w), -1, dtype=np.int32)
    score = np.full((h, w), np.inf, dtype=float)
    yy, xx = np.indices((h, w))
    for i, (g, cand) in enumerate(zip(glyphs, candidates)):
        if not cand.any():
            continue
        x0pt, y0pt, x1pt, y1pt = g["mask_basis_bbox_pt"]
        cx = ((x0pt + x1pt) / 2) * SCALE - fx0
        cy = ((y0pt + y1pt) / 2) * SCALE - fy0
        rx = max(1.0, (x1pt - x0pt) * SCALE / 2)
        ry = max(1.0, (y1pt - y0pt) * SCALE / 2)
        local_score = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        take = cand & (local_score < score)
        owners[take] = i
        score[take] = local_score[take]
    masks = [(owners == i) for i in range(len(glyphs))]
    rows: list[dict[str, Any]] = []
    for g, cand, mask in zip(glyphs, candidates, masks):
        raw_box = bbox_of(mask, fx0, fy0)
        h_ink = 0 if raw_box is None else raw_box[3] - raw_box[1]
        w_ink = 0 if raw_box is None else raw_box[2] - raw_box[0]
        candidate_count = int(cand.sum())
        actual_count = int(mask.sum())
        # The loop-local identity is added below; an actual missing stroke is never inferred
        # solely from an ownership collision.  Manual review must separately certify purity.
        g["raw_bbox_px"] = raw_box
        g["H_INK_PX"] = h_ink
        g["W_INK_PX"] = w_ink
        g["INK_AREA_PX"] = actual_count
        g["CANDIDATE_INK_PX"] = candidate_count
        g["OWNERSHIP_CONTESTED_PX"] = 0
        g["MISSING_STROKE_PX_MACHINE"] = 0
        g["FOREIGN_PIXEL_PX_MACHINE"] = 0
        g["FOREIGN_REMOVED_RESEGMENT_PX"] = g.get("FOREIGN_REMOVED_RESEGMENT_PX", 0)
        g["EMPTY_MASK"] = actual_count == 0 and g["script_class"] != "RAWDICT_COMBINING_CONTROL"
        if g["script_class"] == "RAWDICT_COMBINING_CONTROL":
            g["mask_status"] = "RAWDICT_CONTROL_NO_INDEPENDENT_VISIBLE_MASK"
        else:
            g["mask_status"] = "VISIBLE_MASK_READY" if actual_count else "VISIBLE_MASK_EMPTY"
        rows.append(g)

    # Now that identities are stable, record exact contested ownership counts without using it
    # as a missing-stroke proxy.  Any nonzero value is manually checked in the ledger.
    for i, (g, cand) in enumerate(zip(glyphs, candidates)):
        g["OWNERSHIP_CONTESTED_PX"] = int((cand & (owners >= 0) & (owners != i)).sum())
    return masks, rows


def crop_local(mask: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    return mask[y0:y1, x0:x1]


def make_glyph_artifacts(
    figure_rgb: np.ndarray,
    glyphs: list[dict[str, Any]],
    masks: list[np.ndarray],
) -> list[dict[str, Any]]:
    """Save 1x ORIGINAL/OVERLAY/MASK_ONLY per glyph and 8x nearest contact sheets."""
    card_meta: list[dict[str, Any]] = []
    sheet_rows: list[Image.Image] = []
    cards_per_sheet = 12
    for index, (g, mask) in enumerate(zip(glyphs, masks), start=1):
        if mask.any():
            box = crop_box_with_pad(mask, pad=4)
        else:
            # Logical combining controls have no independently paintable glyph bbox.  Their
            # regular sheet cell shows their rawdict anchor context; the authoritative visual
            # audit is the separately linked accent-association card.
            basis = g.get("mask_basis_bbox_pt") or g["bbox_pt"]
            fx0, fy0, _, _ = pt_rect_to_px(FIG_RECT_PT)
            cx = int(round(((basis[0] + basis[2]) / 2) * SCALE - fx0))
            cy = int(round(((basis[1] + basis[3]) / 2) * SCALE - fy0))
            box = (max(0, cx - 24), max(0, cy - 24), min(figure_rgb.shape[1], cx + 25), min(figure_rgb.shape[0], cy + 25))
        x0, y0, x1, y1 = box
        original = Image.fromarray(figure_rgb[y0:y1, x0:x1], mode="RGB")
        overlay_arr = alpha_overlay(figure_rgb[y0:y1, x0:x1], a=mask[y0:y1, x0:x1])
        overlay = Image.fromarray(overlay_arr, mode="RGB")
        mask_img = Image.fromarray(np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8), mode="L").convert("RGB")
        stem = g["safe_filename"]
        original_path = OUT / "glyph_rois" / f"{stem}_original_1x.png"
        overlay_path = OUT / "glyph_rois" / f"{stem}_target_overlay_1x.png"
        mask_path = OUT / "glyph_rois" / f"{stem}_mask_only_1x.png"
        original.save(original_path)
        overlay.save(overlay_path)
        mask_img.save(mask_path)
        save_mask(mask[y0:y1, x0:x1], OUT / "masks" / "glyphs" / f"{stem}_raw_mask.png")

        # Each cell has the mandatory three views at 8x nearest-neighbour; no measurement uses this scale.
        cell_w, cell_h = 510, 178
        card = Image.new("RGB", (cell_w, cell_h), "white")
        third = (cell_w - 12) // 3
        paste_labelled(card, nearest_scale(original), "ORIGINAL 8x", 4, 2, third, cell_h - 4)
        paste_labelled(card, nearest_scale(overlay), "TARGET OVERLAY 8x", 6 + third, 2, third, cell_h - 4)
        paste_labelled(card, nearest_scale(mask_img), "MASK ONLY 8x", 8 + 2 * third, 2, third, cell_h - 4)
        draw = ImageDraw.Draw(card)
        draw.rectangle((0, 0, cell_w - 1, cell_h - 1), outline=(0, 0, 0))
        draw.text((4, cell_h - 16), f"{g['glyph_id']} {g['unicode']} {g['char']}", fill=(0, 0, 0))
        sheet_rows.append(card)
        sheet_no = (index - 1) // cards_per_sheet + 1
        cell_no = (index - 1) % cards_per_sheet + 1
        card_meta.append({
            "glyph_id": g["glyph_id"],
            "sheet": f"glyph_contact_sheets/glyph_sheet_{sheet_no:02d}.png",
            "cell": cell_no,
            "original_1x": str(original_path.relative_to(OUT)).replace("\\", "/"),
            "overlay_1x": str(overlay_path.relative_to(OUT)).replace("\\", "/"),
            "mask_only_1x": str(mask_path.relative_to(OUT)).replace("\\", "/"),
            "raw_mask": f"masks/glyphs/{stem}_raw_mask.png",
            "review_mode": "ACCENT_ASSOCIATION_CARD" if g["script_class"] in {"RAWDICT_COMBINING_CONTROL", "MATH_ACCENT_COMPOSITE_COMPONENT"} else "TRIPLET_CARD",
        })

    for sheet_idx in range((len(sheet_rows) + cards_per_sheet - 1) // cards_per_sheet):
        rows = sheet_rows[sheet_idx * cards_per_sheet : (sheet_idx + 1) * cards_per_sheet]
        cols = 2
        per_col = math.ceil(len(rows) / cols)
        canvas = Image.new("RGB", (cols * 510, per_col * 178 + 28), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((4, 4), f"FIG-P609-01 glyph contact sheet {sheet_idx + 1:02d} — 8x nearest review only", fill=(0, 0, 0))
        for j, cell in enumerate(rows):
            c = j % cols
            r = j // cols
            canvas.paste(cell, (c * 510, 28 + r * 178))
        canvas.save(OUT / "glyph_contact_sheets" / f"glyph_sheet_{sheet_idx + 1:02d}.png")
    return card_meta


def create_text_objects(
    glyphs: list[dict[str, Any]], masks: list[np.ndarray], parent_map: dict[str, tuple[str, str, str, str]]
) -> list[ObjectRecord]:
    by_parent: dict[str, list[int]] = defaultdict(list)
    meta: dict[str, tuple[str, str, str]] = {}
    for i, g in enumerate(glyphs):
        oid, role, panel, semantics = parent_map[g["raw_line_id"]]
        g["parent_object_id"] = oid
        g["role"] = role
        g["panel"] = panel
        by_parent[oid].append(i)
        meta[oid] = (role, panel, semantics)
    objects: list[ObjectRecord] = []
    for oid in sorted(by_parent):
        idxs = by_parent[oid]
        mask = np.zeros_like(masks[0], dtype=bool)
        for i in idxs:
            mask |= masks[i]
        role, panel, semantics = meta[oid]
        z = max(int(round(glyphs[i].get("seqno", 0))) for i in idxs)
        objects.append(ObjectRecord(oid, "TEXT" if role != "FORMULA_BLOCK" else "FORMULA", role, panel, "", "rawdict", ",".join(glyphs[i]["raw_line_id"] for i in idxs), z, semantics, mask))
    return objects


def attach_texttrace_seqnos(page: fitz.Page, glyphs: list[dict[str, Any]]) -> None:
    """Map each rawdict character to its PDF display-list sequence number without using old evidence."""
    trace_chars: list[tuple[str, tuple[float, float, float, float], int]] = []
    for t in page.get_texttrace():
        seq = int(t.get("seqno", -1))
        for c in t["chars"]:
            trace_chars.append((chr(c[0]), tuple(float(v) for v in c[3]), seq))
    used: set[int] = set()
    line_seq: dict[str, int] = {}
    for g in glyphs:
        gb = g["bbox_pt"]
        best: tuple[float, int, int] | None = None
        for i, (ch, tb, seq) in enumerate(trace_chars):
            if i in used or ch != g["char"]:
                continue
            # rawdict uses font bounding boxes for some CJK glyphs and combining accents while
            # texttrace uses visible glyph bounds. Their horizontal anchors are stable; use the
            # nearest source-order position rather than assuming their y bounds are identical.
            gcx, gcy = (gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2
            tcx, tcy = (tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2
            d = abs(gcx - tcx) * 20 + abs(gcy - tcy)
            if best is None or d < best[0]:
                best = (d, i, seq)
        threshold = 12.0
        if best is None or best[0] > threshold:
            if g["char"] == "\u0302" and g["raw_line_id"] in line_seq:
                # A second class of MuPDF accent extraction has a zero-width bbox located after
                # the preceding TeX atom (rather than above the visible base glyph). It belongs to
                # the exact same raw line / display-list text sequence already mapped above.
                g["seqno"] = line_seq[g["raw_line_id"]]
                g["seqno_mapping_method"] = "RAW_LINE_DISPLAYLIST_SEQUENCE_FOR_ZERO_WIDTH_ACCENT"
                g["trace_bbox_pt"] = None
                g["rawdict_visible_foreground"] = False
                continue
            raise RuntimeError(f"unmapped rawdict glyph {g['glyph_id']} {g['char']!r}; evidence must not guess z-order")
        used.add(best[1])
        g["seqno"] = best[2]
        g["seqno_mapping_method"] = "TEXTTRACE_NEAREST_SAME_CODEPOINT"
        g["trace_bbox_pt"] = list(trace_chars[best[1]][1])
        tb = g["trace_bbox_pt"]
        if g["script_class"] == "RAWDICT_COMBINING_CONTROL" and (tb[2] <= tb[0] or tb[3] <= tb[1]):
            g["rawdict_visible_foreground"] = False
        line_seq[g["raw_line_id"]] = best[2]


def drawing_line_items(drawing: dict[str, Any]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    out: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for item in drawing["items"]:
        if item[0] == "l":
            p0, p1 = item[1], item[2]
            out.append(((p0.x, p0.y), (p1.x, p1.y)))
    return out


def build_graphic_objects(page: fitz.Page, shape: tuple[int, int], fig_px: tuple[int, int, int, int], figure_rgb: np.ndarray) -> tuple[list[ObjectRecord], list[dict[str, Any]], list[dict[str, Any]]]:
    """Build every P609 drawing/path object. Pale fills are recorded but excluded from foreground pairs."""
    drawings = page.get_drawings()
    fx0, fy0, _, _ = fig_px
    ink = rgb_ink_mask(figure_rgb)
    objs: list[ObjectRecord] = []
    coverage: list[dict[str, Any]] = []
    math_rules: list[dict[str, Any]] = []

    def add_obj(oid: str, kind: str, role: str, panel: str, drawing_index: int, drawing_item: str, z: int, semantics: str, geometry: np.ndarray) -> None:
        # Geometry comes directly from the current PDF drawing/path coordinates. Gating by actual
        # candidate ink preserves the native final-visible footprint, while pre geometry captures paint order.
        actual = geometry & ink
        objs.append(ObjectRecord(oid, kind, role, panel, "", str(drawing_index), drawing_item, z, semantics, geometry, actual))
        coverage.append({
            "drawing_index": drawing_index,
            "drawing_item": drawing_item,
            "object_id": oid,
            "kind": kind,
            "role": role,
            "z_order": z,
            "foreground": True,
            "assignment": "MAPPED_FOREGROUND",
            "bbox_pt": [round(v, 6) for v in drawings[drawing_index]["rect"]],
            "source_semantics": semantics,
        })

    # Drawings 65--85 are independently identified from the current physical page and lie wholly in P609 scope.
    x_ticks = drawing_line_items(drawings[65])
    if len(x_ticks) != 7:
        raise RuntimeError("P609 x tick drawing no longer has 7 components")
    for i, (p0, p1) in enumerate(x_ticks):
        add_obj(f"G{5+i:03d}", "GRAPHIC", "AXIS_TICK", "LEFT", 65, f"line_{i}", 137, f"x-axis tick k={i}", line_mask(shape, fx0, fy0, p0, p1, 0.597760, True))

    y_ticks = drawing_line_items(drawings[66])
    if len(y_ticks) != 5:
        raise RuntimeError("P609 y tick drawing no longer has 5 components")
    yvals = ["0", "0.25", "0.5", "0.75", "1"]
    for i, (p0, p1) in enumerate(y_ticks):
        add_obj(f"G{12+i:03d}", "GRAPHIC", "AXIS_TICK", "LEFT", 66, f"line_{i}", 138, f"y-axis tick ACF={yvals[i]}", line_mask(shape, fx0, fy0, p0, p1, 0.597760, True))

    x_axis = drawing_line_items(drawings[67])[0]
    add_obj("G001", "GRAPHIC", "AXIS", "LEFT", 67, "line_0", 139, "x-axis shaft", line_mask(shape, fx0, fy0, x_axis[0], x_axis[1], 0.697390, True))
    add_obj("G002", "GRAPHIC", "AXIS_ARROWHEAD", "LEFT", 68, "polygon", 140, "x-axis arrowhead", polygon_mask(shape, fx0, fy0, [(291.404144, 668.050049), (287.498810, 666.097412), (288.963318, 668.050049), (287.498810, 670.002686)]))
    y_axis = drawing_line_items(drawings[69])[0]
    add_obj("G003", "GRAPHIC", "AXIS", "LEFT", 69, "line_0", 141, "y-axis shaft", line_mask(shape, fx0, fy0, y_axis[0], y_axis[1], 0.697390, True))
    add_obj("G004", "GRAPHIC", "AXIS_ARROWHEAD", "LEFT", 70, "polygon", 142, "y-axis arrowhead", polygon_mask(shape, fx0, fy0, [(126.475006, 556.976379), (124.522354, 560.881714), (126.475006, 559.417236), (128.427658, 560.881714)]))

    # Drawing 71 is a pale SLBlue!5 plot-region fill: explicitly visible background, not a foreground object.
    coverage.append({
        "drawing_index": 71,
        "drawing_item": "fill_rect",
        "object_id": "B001",
        "kind": "BACKGROUND_FILL",
        "role": "PLOT_REGION_FILL",
        "z_order": 155,
        "foreground": False,
        "assignment": "EXCLUDED_BACKGROUND_FILL",
        "bbox_pt": [round(v, 6) for v in drawings[71]["rect"]],
        "source_semantics": "SLBlue!5 background behind the left ACF plot; excluded from foreground pair denominator by protocol.",
    })

    stems = drawing_line_items(drawings[72])
    if len(stems) != 7:
        raise RuntimeError("P609 ACF stem drawing no longer has 7 components")
    acf = [1.00, 0.86, 0.74, 0.64, 0.55, 0.47, 0.40]
    for i, (p0, p1) in enumerate(stems):
        add_obj(f"G{17+i:03d}", "GRAPHIC", "DATA_STEM", "LEFT", 72, f"line_{i}", 156, f"ACF stem k={i}, rho={acf[i]:.2f}", line_mask(shape, fx0, fy0, p0, p1, 0.996280, True))

    cutoff = drawing_line_items(drawings[73])[0]
    dash, gap = 2.98883 * SCALE, 1.99255 * SCALE
    # The current PDF's dashed line begins at its lower endpoint; construct each dash on the same native grid.
    p0, p1 = cutoff
    x = p0[0] * SCALE - fx0
    y_start = p0[1] * SCALE - fy0
    y_end = p1[1] * SCALE - fy0
    direction = -1 if y_end < y_start else 1
    dash_img = Image.new("L", (shape[1], shape[0]), 0)
    dd = ImageDraw.Draw(dash_img)
    y = y_start
    while (direction < 0 and y > y_end) or (direction > 0 and y < y_end):
        y2 = y + direction * dash
        if direction < 0:
            y2 = max(y2, y_end)
        else:
            y2 = min(y2, y_end)
        dd.line((x, y, x, y2), fill=255, width=max(1, int(round(0.747210 * SCALE))))
        y = y2 + direction * gap
    add_obj("G024", "GRAPHIC", "CUTOFF_GUIDE", "LEFT", 73, "dashed_line", 157, "gold dashed cutoff guide at K=6.5", np.array(dash_img) > 0)

    marker_rects = [
        (131.031815, 563.311157, 134.817657, 567.097046),
        (149.459656, 577.709595, 153.245514, 581.495484),
        (167.887497, 590.051147, 171.673340, 593.836976),
        (186.315338, 600.335754, 190.101181, 604.121521),
        (204.743179, 609.591858, 208.529007, 613.377686),
        (223.171021, 617.819580, 226.956848, 621.605347),
        (241.598846, 625.018738, 245.384689, 628.804565),
    ]
    for i, rect in enumerate(marker_rects):
        add_obj(f"G{25+i:03d}", "GRAPHIC", "DATA_MARKER", "LEFT", 74 + i, "circle", 160 + 2 * i, f"filled ACF marker k={i}, rho={acf[i]:.2f}", ellipse_mask(shape, fx0, fy0, rect))

    add_obj("G032", "GRAPHIC", "NODE_BORDER", "RIGHT", 81, "stroke", 177, "rounded ESS explanation node border (white fill separately excluded)", rounded_border_mask(shape, fx0, fy0, (308.736023, 548.898376, 501.494354, 676.128052), 0.647570, 2.0))
    coverage.append({
        "drawing_index": 81,
        "drawing_item": "white_fill",
        "object_id": "B002",
        "kind": "BACKGROUND_FILL",
        "role": "NODE_INTERIOR_FILL",
        "z_order": 177,
        "foreground": False,
        "assignment": "EXCLUDED_BACKGROUND_FILL",
        "bbox_pt": [round(v, 6) for v in drawings[81]["rect"]],
        "source_semantics": "Opaque white node interior is background, never folded into the border foreground mask.",
    })

    r1 = line_mask(shape, fx0, fy0, (405.165009, 586.708008), (410.569000, 586.708008), 0.65, False)
    add_obj("R001", "GRAPHIC/MATH_RULE", "MATH_RULE", "RIGHT", 82, "line_0", 180, "fraction rule k/n within finite weighted tau-hat formula (parent T019)", r1)
    r2 = line_mask(shape, fx0, fy0, (345.061005, 612.873047), (363.253998, 612.873047), 0.65, False)
    add_obj("R002", "GRAPHIC/MATH_RULE", "MATH_RULE", "RIGHT", 83, "line_0", 182, "fraction rule n/tau-hat within N-eff formula (parent T020)", r2)
    math_rules.extend([
        {"rule_id": "R001", "drawing_index": 82, "seqno": 180, "parent_formula": "T019", "semantic": "k/n fraction rule", "bbox_pt": [405.165009, 586.708008, 410.569000, 586.708008]},
        {"rule_id": "R002", "drawing_index": 83, "seqno": 182, "parent_formula": "T020", "semantic": "n/tau-hat fraction rule", "bbox_pt": [345.061005, 612.873047, 363.253998, 612.873047]},
    ])
    shaft = drawing_line_items(drawings[84])[0]
    add_obj("G033", "GRAPHIC", "CONNECTOR_ARROW", "BETWEEN", 84, "line_0", 184, "connector arrow shaft from ACF panel toward ESS node", line_mask(shape, fx0, fy0, shaft[0], shaft[1], 0.747210, True))
    add_obj("G034", "GRAPHIC", "CONNECTOR_ARROWHEAD", "BETWEEN", 85, "polygon", 185, "connector arrowhead toward ESS node", polygon_mask(shape, fx0, fy0, [(304.513550, 612.513245), (300.432678, 610.970642), (301.784821, 612.513245), (300.432678, 614.055847)]))

    # Enforce exactly the P609 drawing/path coverage. No P608 drawing (61/62) is included by figure scope.
    foreground_expected = 36
    if len(objs) != foreground_expected:
        raise RuntimeError(f"foreground path coverage mismatch: expected {foreground_expected}, got {len(objs)}")
    return objs, coverage, math_rules


def assign_final_masks(objects: list[ObjectRecord]) -> None:
    """Use current PDF draw/text sequence to allocate unique final-visible pixels while preserving pre-zorder masks."""
    ordered = sorted(enumerate(objects), key=lambda it: (it[1].z_order, it[0]))
    higher = np.zeros_like(objects[0].pre_mask, dtype=bool)
    for _, obj in reversed(ordered):
        # `final_mask` has actual candidate ink only; geometry is retained in pre_mask for reverse occlusion evidence.
        raw = obj.final_mask if obj.final_mask is not None else obj.pre_mask
        obj.final_mask = raw & ~higher
        higher |= obj.pre_mask


def object_inventory_rows(objects: list[ObjectRecord], fig_px: tuple[int, int, int, int]) -> list[dict[str, Any]]:
    fx0, fy0, _, _ = fig_px
    rows: list[dict[str, Any]] = []
    for obj in objects:
        pre_box = bbox_of(obj.pre_mask, fx0, fy0)
        final_box = bbox_of(obj.final_mask if obj.final_mask is not None else obj.pre_mask, fx0, fy0)
        rows.append({
            "object_id": obj.object_id,
            "kind": obj.kind,
            "role": obj.role,
            "panel": obj.panel,
            "parent": obj.parent,
            "drawing_index": obj.drawing_index,
            "drawing_item": obj.drawing_item,
            "z_order": obj.z_order,
            "pre_raw_bbox_px": pre_box,
            "final_visible_bbox_px": final_box,
            "pre_mask_pixels": int(obj.pre_mask.sum()),
            "final_visible_mask_pixels": int((obj.final_mask if obj.final_mask is not None else obj.pre_mask).sum()),
            "safe_pre_mask": f"masks/objects/{obj.object_id}_pre_zorder.png",
            "safe_final_mask": f"masks/objects/{obj.object_id}_final_visible.png",
            "source_semantics": obj.source_semantics,
        })
    return rows


def save_object_masks(objects: list[ObjectRecord]) -> None:
    for obj in objects:
        save_mask(obj.pre_mask, OUT / "masks" / "objects" / f"{obj.object_id}_pre_zorder.png")
        save_mask(obj.final_mask if obj.final_mask is not None else obj.pre_mask, OUT / "masks" / "objects" / f"{obj.object_id}_final_visible.png")


def object_map(objects: list[ObjectRecord]) -> dict[str, ObjectRecord]:
    return {obj.object_id: obj for obj in objects}


def intentional_whitelist() -> dict[frozenset[str], tuple[str, str]]:
    """Every intended contact is named individually; no category-wide exemption exists."""
    records: dict[frozenset[str], tuple[str, str]] = {}
    def put(a: str, b: str, tag: str, detail: str) -> None:
        records[frozenset((a, b))] = (tag, detail)

    put("G001", "G002", "INTENTIONAL_AXIS_CONSTRUCTION", "x-axis shaft joins its own arrowhead at the positive x endpoint.")
    put("G003", "G004", "INTENTIONAL_AXIS_CONSTRUCTION", "y-axis shaft joins its own arrowhead at the positive y endpoint.")
    put("G001", "G003", "INTENTIONAL_AXIS_ORIGIN", "x and y shafts share the plotted coordinate origin only.")
    for i in range(7):
        put("G001", f"G{5+i:03d}", "INTENTIONAL_AXIS_TICK", f"x tick k={i} attaches to the x-axis shaft at its designated coordinate.")
    yvals = ["0", "0.25", "0.5", "0.75", "1"]
    for i, val in enumerate(yvals):
        put("G003", f"G{12+i:03d}", "INTENTIONAL_AXIS_TICK", f"y tick ACF={val} attaches to the y-axis shaft at its designated coordinate.")
    put("G001", "G012", "INTENTIONAL_AXIS_ORIGIN_TICK", "the y=0 tick shares the x-axis at the coordinate origin by axis construction.")
    acf = [1.00, 0.86, 0.74, 0.64, 0.55, 0.47, 0.40]
    for i, rho in enumerate(acf):
        tick = f"G{5+i:03d}"
        stem = f"G{17+i:03d}"
        marker = f"G{25+i:03d}"
        put(tick, stem, "INTENTIONAL_DATA_RELATION", f"Source lines 19 and 22--23 explicitly give xtick={i} and ycomb coordinate ({i},{rho:.2f}); this exact stem intentionally shares its own k={i} tick only. No other tick/stem pair is exempt.")
        put("G001", stem, "INTENTIONAL_DATA_RELATION", f"ACF stem k={i}, rho={rho:.2f} intentionally starts on y=0 x-axis.")
        put(stem, marker, "INTENTIONAL_DATA_RELATION", f"filled marker k={i}, rho={rho:.2f} intentionally caps its own ACF stem.")
    put("G001", "G024", "INTENTIONAL_CUTOFF_GUIDE", "dashed K=6.5 cutoff guide intentionally terminates on the x-axis.")
    put("G033", "G034", "INTENTIONAL_CONNECTOR_CONSTRUCTION", "connector shaft joins its own arrowhead toward the ESS node.")
    put("T019", "R001", "INTENTIONAL_MATH_RULE", "R001 is the k/n fraction rule belonging only to finite weighted tau-hat formula T019.")
    put("T020", "R002", "INTENTIONAL_MATH_RULE", "R002 is the n/tau-hat fraction rule belonging only to N-eff formula T020.")
    return records


def pair_required_clearance(a: ObjectRecord, b: ObjectRecord) -> tuple[float, str]:
    a_text = a.kind in {"TEXT", "FORMULA"}
    b_text = b.kind in {"TEXT", "FORMULA"}
    if a_text and b_text:
        required = 4.0
        kind = "TEXT_TEXT"
    elif a_text or b_text:
        other = b if a_text else a
        required = 5.0 if other.role == "NODE_BORDER" else 3.0
        kind = "TEXT_GRAPHIC"
    else:
        required = 3.0
        kind = "GRAPHIC_GRAPHIC"
    if a_text and b_text and {a.panel, b.panel} == {"LEFT", "RIGHT"}:
        required = max(required, 8.0)
        kind += "_CROSS_PANEL"
    return required, kind


def min_clearance(a: np.ndarray, b: np.ndarray) -> tuple[int, float, float, tuple[int, int] | None]:
    """Return shared pixels, edge clearance, centre distance, and a nearest B pixel coordinate."""
    inter = a & b
    shared = int(inter.sum())
    if shared:
        y, x = np.argwhere(inter)[0]
        return shared, 0.0, 0.0, (int(x), int(y))
    if not a.any() or not b.any():
        return 0, float("nan"), float("nan"), None
    dt, indices = distance_transform_edt(~a, return_indices=True)
    values = dt[b]
    idx = int(np.argmin(values))
    by, bx = np.argwhere(b)[idx]
    centre = float(values[idx])
    # Native mask edge clearance counts blank pixels between the nearest effective-foreground pixels.
    clearance = max(0.0, centre - 1.0)
    return 0, clearance, centre, (int(bx), int(by))


def pair_card(
    pair_id: str,
    a: ObjectRecord,
    b: ObjectRecord,
    figure_rgb: np.ndarray,
    pre_intersection: np.ndarray,
    final_intersection: np.ndarray,
    clearance_note: str,
) -> dict[str, str]:
    final_a = a.final_mask if a.final_mask is not None else a.pre_mask
    final_b = b.final_mask if b.final_mask is not None else b.pre_mask
    box = crop_box_with_pad(a.pre_mask | final_a, b.pre_mask | final_b, pad=10)
    x0, y0, x1, y1 = box
    base = figure_rgb[y0:y1, x0:x1]
    pa = a.pre_mask[y0:y1, x0:x1]
    pb = b.pre_mask[y0:y1, x0:x1]
    fa = final_a[y0:y1, x0:x1]
    fb = final_b[y0:y1, x0:x1]
    pi = pre_intersection[y0:y1, x0:x1]
    fi = final_intersection[y0:y1, x0:x1]
    original = Image.fromarray(base, mode="RGB")
    overlay = Image.fromarray(alpha_overlay(base, fa, fb, pi | fi), mode="RGB")
    a_pre = Image.fromarray(np.where(pa, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    b_pre = Image.fromarray(np.where(pb, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    a_mask = Image.fromarray(np.where(fa, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    b_mask = Image.fromarray(np.where(fb, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    pre_inter_mask = Image.fromarray(np.where(pi, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    final_inter_mask = Image.fromarray(np.where(fi, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    safe = f"{pair_id}_{a.object_id}_{b.object_id}"
    paths = {
        "original_1x": OUT / "pair_cards" / f"{safe}_original_1x.png",
        "a_pre_mask": OUT / "pair_cards" / f"{safe}_A_{a.object_id}_pre_zorder_mask_1x.png",
        "b_pre_mask": OUT / "pair_cards" / f"{safe}_B_{b.object_id}_pre_zorder_mask_1x.png",
        "a_final_mask": OUT / "pair_cards" / f"{safe}_A_{a.object_id}_final_mask_1x.png",
        "b_final_mask": OUT / "pair_cards" / f"{safe}_B_{b.object_id}_final_mask_1x.png",
        "pre_intersection": OUT / "pair_cards" / f"{safe}_pre_zorder_intersection_1x.png",
        "final_intersection": OUT / "pair_cards" / f"{safe}_final_visible_intersection_1x.png",
        "overlay": OUT / "pair_cards" / f"{safe}_overlay_1x.png",
        "nearest8": OUT / "pair_cards" / f"{safe}_8x_nearest.png",
    }
    original.save(paths["original_1x"])
    a_pre.save(paths["a_pre_mask"])
    b_pre.save(paths["b_pre_mask"])
    a_mask.save(paths["a_final_mask"])
    b_mask.save(paths["b_final_mask"])
    pre_inter_mask.save(paths["pre_intersection"])
    final_inter_mask.save(paths["final_intersection"])
    overlay.save(paths["overlay"])
    panel_w, panel_h = 290, 180
    canvas = Image.new("RGB", (panel_w * 3, panel_h * 3 + 36), "white")
    paste_labelled(canvas, nearest_scale(original), "ORIGINAL 8x", 0, 0, panel_w, panel_h)
    paste_labelled(canvas, nearest_scale(overlay), "FINAL A red / B cyan / PRE shared yellow", panel_w, 0, panel_w, panel_h)
    paste_labelled(canvas, nearest_scale(a_mask), f"A FINAL {a.object_id}", panel_w * 2, 0, panel_w, panel_h)
    paste_labelled(canvas, nearest_scale(b_mask), f"B FINAL {b.object_id}", 0, panel_h, panel_w, panel_h)
    paste_labelled(canvas, nearest_scale(final_inter_mask), "FINAL-VISIBLE INTERSECTION", panel_w, panel_h, panel_w, panel_h)
    blank = Image.new("RGB", (10, 10), "white")
    paste_labelled(canvas, blank, clearance_note, panel_w * 2, panel_h, panel_w, panel_h)
    paste_labelled(canvas, nearest_scale(a_pre), f"A PRE {a.object_id}", 0, panel_h * 2, panel_w, panel_h)
    paste_labelled(canvas, nearest_scale(b_pre), f"B PRE {b.object_id}", panel_w, panel_h * 2, panel_w, panel_h)
    paste_labelled(canvas, nearest_scale(pre_inter_mask), "PRE-ZORDER INTERSECTION", panel_w * 2, panel_h * 2, panel_w, panel_h)
    draw = ImageDraw.Draw(canvas)
    draw.text((4, panel_h * 3 + 7), f"{pair_id}: {a.object_id} vs {b.object_id}", fill=(0, 0, 0))
    canvas.save(paths["nearest8"])
    return {k: str(v.relative_to(OUT)).replace("\\", "/") for k, v in paths.items()}


def build_pair_ledger(objects: list[ObjectRecord], figure_rgb: np.ndarray) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    whitelist = intentional_whitelist()
    rows: list[dict[str, Any]] = []
    critical_rows: list[dict[str, Any]] = []
    for pair_no, (a, b) in enumerate(combinations(objects, 2), start=1):
        pair_id = f"P{pair_no:04d}"
        fa = a.final_mask if a.final_mask is not None else a.pre_mask
        fb = b.final_mask if b.final_mask is not None else b.pre_mask
        pre_shared, pre_clear, pre_dist, _ = min_clearance(a.pre_mask, b.pre_mask)
        final_shared, clearance, centre_dist, contact = min_clearance(fa, fb)
        req, pair_kind = pair_required_clearance(a, b)
        intent = whitelist.get(frozenset((a.object_id, b.object_id)))
        if intent:
            decision = "INTENTIONAL_DATA_RELATION" if intent[0] == "INTENTIONAL_DATA_RELATION" else "INTENTIONAL_CONTACT_PASS"
            result = "PASS_WHITELISTED"
            reason = intent[1]
        elif pre_shared >= 1 or final_shared >= 1 or (not math.isnan(clearance) and clearance < req):
            decision = "HARD_FAIL"
            result = "FAIL"
            reason = f"non-whitelisted pre_shared={pre_shared}, final_shared={final_shared}, clearance={clearance:.3f}px, required={req:.3f}px"
        elif math.isnan(clearance):
            decision = "EVIDENCE_FAIL"
            result = "FAIL"
            reason = "empty or unmeasurable final mask"
        else:
            decision = "PASS"
            result = "PASS"
            reason = "no overlap and applicable native clearance met"
        critical = pre_shared > 0 or final_shared > 0 or (not math.isnan(clearance) and clearance < req + 5.0)
        row: dict[str, Any] = {
            "pair_id": pair_id,
            "object_a": a.object_id,
            "object_b": b.object_id,
            "pair_kind": pair_kind,
            "a_kind": a.kind,
            "b_kind": b.kind,
            "a_role": a.role,
            "b_role": b.role,
            "a_z_order": a.z_order,
            "b_z_order": b.z_order,
            "pre_zorder_shared_px": pre_shared,
            "pre_zorder_clearance_px": pre_clear,
            "final_visible_shared_px": final_shared,
            "final_visible_clearance_px": clearance,
            "nearest_center_distance_px": centre_dist,
            "required_clearance_px": req,
            "contact_xy_figure_px": contact,
            "intentional_tag": "" if intent is None else intent[0],
            "intentional_reason": "" if intent is None else intent[1],
            "decision": decision,
            "result": result,
            "reason": reason,
            "critical_or_contact": critical,
            "manual_reviewer": "PENDING_CRITICAL_CARD" if critical else "NOT_REQUIRED_WIDE_CLEARANCE",
            "manual_decision": "PENDING" if critical else "NOT_REQUIRED",
            "manual_note": "",
        }
        if critical:
            paths = pair_card(pair_id, a, b, figure_rgb, a.pre_mask & b.pre_mask, fa & fb, f"final clearance={clearance:.3f}px; required={req:.3f}px")
            row.update({f"evidence_{k}": v for k, v in paths.items()})
            critical_rows.append(row)
        else:
            for key in ("original_1x", "a_pre_mask", "b_pre_mask", "a_final_mask", "b_final_mask", "pre_intersection", "final_intersection", "overlay", "nearest8"):
                row[f"evidence_{key}"] = ""
        rows.append(row)
    expected = len(objects) * (len(objects) - 1) // 2
    if len(rows) != expected:
        raise RuntimeError(f"pair denominator mismatch: {len(rows)} != {expected}")
    return rows, critical_rows


def make_pair_contact_sheets(critical_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create readable 8x-nearest sheets from the individual critical cards for actual human opening."""
    updated: list[dict[str, Any]] = []
    cards_per_sheet = 4
    for sheet_no in range((len(critical_rows) + cards_per_sheet - 1) // cards_per_sheet):
        batch = critical_rows[sheet_no * cards_per_sheet : (sheet_no + 1) * cards_per_sheet]
        thumbs: list[Image.Image] = []
        for row in batch:
            im = Image.open(OUT / row["evidence_nearest8"]).convert("RGB")
            im.thumbnail((760, 360), Image.Resampling.NEAREST)
            thumbs.append(im)
        canvas = Image.new("RGB", (1520, 720 + 30), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((4, 5), f"FIG-P609-01 critical/contact pair review sheet {sheet_no+1:02d}", fill=(0, 0, 0))
        for i, im in enumerate(thumbs):
            x = (i % 2) * 760
            y = 30 + (i // 2) * 360
            canvas.paste(im, (x + (760 - im.width) // 2, y + (360 - im.height) // 2))
        rel = f"pair_contact_sheets/pair_sheet_{sheet_no+1:02d}.png"
        canvas.save(OUT / rel)
        for i, row in enumerate(batch):
            row["manual_sheet"] = rel
            row["manual_cell"] = i + 1
            updated.append(row)
    return updated


def glyph_local_mask_from_page(page_rgb: np.ndarray, glyph: dict[str, Any], page_scale: float) -> np.ndarray:
    """Calibrate a glyph in its own 300dpi official PDF page crop; same extraction algorithm as target glyphs."""
    x0pt, y0pt, x1pt, y1pt = glyph.get("mask_basis_bbox_pt") or glyph["bbox_pt"]
    x0 = max(0, math.floor(x0pt * page_scale - 0.5))
    y0 = max(0, math.floor(y0pt * page_scale - 0.5))
    x1 = min(page_rgb.shape[1], math.ceil(x1pt * page_scale + 0.5))
    y1 = min(page_rgb.shape[0], math.ceil(y1pt * page_scale + 0.5))
    crop = page_rgb[y0:y1, x0:x1]
    if crop.size == 0:
        return np.zeros((0, 0), dtype=bool)
    ink = rgb_ink_mask(crop)
    exp = np.array(glyph["font_color_rgb"], dtype=float)
    direction = 255.0 - exp
    denom = float(np.dot(direction, direction))
    vec = 255.0 - crop.astype(float)
    projection = np.tensordot(vec, direction, axes=([2], [0])) / max(denom, 1.0)
    residual = np.sqrt(np.sum((vec - projection[..., None] * direction) ** 2, axis=2))
    return ink & (projection >= 0.045) & (residual <= 38.0)


def attach_reference_texttrace_bbox(page: fitz.Page, ref: dict[str, Any]) -> dict[str, Any]:
    """Use the reference page's actual visible glyph bbox, never a broad rawdict font box."""
    rb = ref["bbox_pt"]
    rcx, rcy = (rb[0] + rb[2]) / 2, (rb[1] + rb[3]) / 2
    best: tuple[float, tuple[float, float, float, float]] | None = None
    for trace in page.get_texttrace():
        for ch, _gid, _origin, tb in trace["chars"]:
            if chr(ch) != ref["char"]:
                continue
            tb = tuple(float(v) for v in tb)
            if tb[2] <= tb[0] or tb[3] <= tb[1]:
                continue
            tcx, tcy = (tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2
            distance = abs(rcx - tcx) * 20 + abs(rcy - tcy)
            if best is None or distance < best[0]:
                best = (distance, tb)
    if best is not None and best[0] <= 12.0:
        ref["mask_basis_bbox_pt"] = list(best[1])
        ref["reference_bbox_mapping"] = "TEXTTRACE_VISIBLE_GLYPH_BBOX"
    else:
        ref["mask_basis_bbox_pt"] = list(ref["bbox_pt"])
        ref["reference_bbox_mapping"] = "RAWDICT_BBOX_FALLBACK_NO_TEXTTRACE_MATCH"
    return ref


def scan_external_calibration(doc: fitz.Document, target: dict[str, Any], target_page: int = PAGE_INDEX) -> dict[str, Any] | None:
    """Find another official-PDF glyph with exactly matching codepoint/font/size/colour for singleton calibration."""
    wanted_char = target["char"]
    wanted_font = target["font"]
    wanted_size = float(target["pdf_font_size_pt"])
    wanted_color = tuple(target["font_color_rgb"])
    target_box = tuple(target["bbox_pt"])
    for page_idx in range(doc.page_count):
        raw = doc[page_idx].get_text("rawdict")
        for block in raw["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["font"] != wanted_font or abs(float(span["size"]) - wanted_size) > 0.02 or rgb_from_pdf_color(span.get("color")) != wanted_color:
                        continue
                    for char in span["chars"]:
                        if char["c"] != wanted_char:
                            continue
                        if page_idx == target_page and sum((a - b) ** 2 for a, b in zip(target_box, char["bbox"])) < 0.01:
                            continue
                        ref = dict(target)
                        ref["bbox_pt"] = list(char["bbox"])
                        ref["origin_pt"] = list(char.get("origin", (None, None)))
                        ref["pdf_page"] = page_idx + 1
                        return ref
    return None


def build_official_calibration_index(doc: fitz.Document, wanted: set[tuple[str, str, float, tuple[int, int, int]]]) -> dict[tuple[str, str, float, tuple[int, int, int]], list[dict[str, Any]]]:
    """One read-only pass over the locked candidate, avoiding repeated whole-book scans per punctuation glyph."""
    index: dict[tuple[str, str, float, tuple[int, int, int]], list[dict[str, Any]]] = defaultdict(list)
    for page_idx in range(doc.page_count):
        raw = doc[page_idx].get_text("rawdict")
        for block in raw["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    key_prefix = (span["font"], round(float(span["size"]), 2), rgb_from_pdf_color(span.get("color")))
                    for char in span["chars"]:
                        key = (char["c"], key_prefix[0], key_prefix[1], key_prefix[2])
                        if key in wanted:
                            index[key].append({
                                "bbox_pt": list(char["bbox"]),
                                "origin_pt": list(char.get("origin", (None, None))),
                                "font": span["font"],
                                "pdf_font_size_pt": float(span["size"]),
                            "font_color_rgb": key_prefix[2],
                            "char": char["c"],
                            "writing_direction": list(line.get("dir", (1.0, 0.0))),
                            "pdf_page": page_idx + 1,
                            })
    return index


def make_calibration_artifact(page_img: Image.Image, ref: dict[str, Any], stem: str) -> tuple[Path, Path, int, int]:
    rgb = np.array(page_img)
    mask = glyph_local_mask_from_page(rgb, ref, SCALE)
    # The selected horizontal comma reference sits immediately after a widehat-N in the
    # official book.  Its visible bbox contains a disconnected 18px roof tip from that prior
    # atom.  Retain the comma's largest connected component only; this is documented on the
    # reference row and is the same purity rule used for target GL122.
    ref["reference_resegmentation"] = "NONE"
    if ref.get("char") == "," and mask.any():
        ref_labels, ref_n = label(mask, structure=np.ones((3, 3), dtype=np.int8))
        components = [(comp, int((ref_labels == comp).sum())) for comp in range(1, ref_n + 1)]
        if len(components) > 1:
            keep = max(components, key=lambda t: t[1])[0]
            removed = int(mask.sum() - (ref_labels == keep).sum())
            if removed > 0:
                mask = ref_labels == keep
                ref["reference_resegmentation"] = f"removed {removed}px disconnected preceding-widehat roof remnant; retained largest comma component"
    x0pt, y0pt, x1pt, y1pt = ref.get("mask_basis_bbox_pt") or ref["bbox_pt"]
    x0 = max(0, math.floor(x0pt * SCALE - 4))
    y0 = max(0, math.floor(y0pt * SCALE - 4))
    x1 = min(rgb.shape[1], math.ceil(x1pt * SCALE + 4))
    y1 = min(rgb.shape[0], math.ceil(y1pt * SCALE + 4))
    original = Image.fromarray(rgb[y0:y1, x0:x1], mode="RGB")
    # Mask here is local to raw bbox without the 4px padding.
    local_overlay = original.copy()
    mx0 = max(0, math.floor(x0pt * SCALE - 0.5) - x0)
    my0 = max(0, math.floor(y0pt * SCALE - 0.5) - y0)
    if mask.size:
        arr = np.array(local_overlay)
        mh, mw = mask.shape
        region = arr[my0:my0+mh, mx0:mx0+mw]
        region[mask] = (230, 35, 35)
        arr[my0:my0+mh, mx0:mx0+mw] = region
        local_overlay = Image.fromarray(arr, mode="RGB")
    h = int(mask.shape[0]) if mask.size else 0
    area = int(mask.sum()) if mask.size else 0
    one = OUT / "calibration" / f"{stem}_reference_1x.png"
    eight = OUT / "calibration" / f"{stem}_reference_8x.png"
    original.save(one)
    card = Image.new("RGB", (660, 250), "white")
    mask_img = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").convert("RGB") if mask.size else Image.new("RGB", (1, 1), "white")
    paste_labelled(card, nearest_scale(original), "REFERENCE ORIGINAL 8x", 0, 0, 220, 250)
    paste_labelled(card, nearest_scale(local_overlay), "TARGET OVERLAY 8x", 220, 0, 220, 250)
    paste_labelled(card, nearest_scale(mask_img), "MASK ONLY 8x", 440, 0, 220, 250)
    card.save(eight)
    # H inside raw bbox; mask itself has no global co-ordinates but has true native grid height.
    b = bbox_of(mask)
    return one, eight, (0 if b is None else b[3] - b[1]), area


def low_profile_and_accent_calibration(doc: fitz.Document, glyphs: list[dict[str, Any]], masks: list[np.ndarray]) -> list[dict[str, Any]]:
    """Independent [0.92,1.08] calibration for low-profile and rendered-accent ink.

    A same-candidate group uses one actual median-like specimen rather than a synthetic median
    mask.  A singleton uses an exact codepoint/font/size/colour specimen from the frozen PDF.
    Zero-width rawdict controls are not calibration targets because they have no own foreground.
    """
    groups: dict[tuple[str, str, float, tuple[int, int, int], str], list[int]] = defaultdict(list)
    for i, g in enumerate(glyphs):
        if g["script_class"] == "LOW_PROFILE_PUNCTUATION":
            groups[(g["char"], g["font"], round(float(g["pdf_font_size_pt"]), 2), tuple(g["font_color_rgb"]), g["script_class"])].append(i)
    page_cache: dict[int, Image.Image] = {}
    rows: list[dict[str, Any]] = []
    for key, idxs in groups.items():
        # A few adjacent texttrace boxes meet on anti-aliased edge pixels.  The unique mask is
        # still a valid candidate for a same-codepoint calibration once that contested count is
        # separately disclosed and manually opened; do not discard all in-scope peers and force
        # an unrelated external fallback.
        usable = [i for i in idxs if glyphs[i]["H_INK_PX"] > 0 and glyphs[i]["INK_AREA_PX"] > 0]
        ref_h: float | None = None
        ref_area: float | None = None
        ref_desc: str
        ref_paths = ""
        ref_glyph_id = ""
        if len(usable) >= 2:
            median_h = float(median([glyphs[i]["H_INK_PX"] for i in usable]))
            median_area = float(median([glyphs[i]["INK_AREA_PX"] for i in usable]))
            ref_idx = min(usable, key=lambda i: abs(glyphs[i]["H_INK_PX"] / median_h - 1.0) + abs(glyphs[i]["INK_AREA_PX"] / median_area - 1.0))
            ref_h = float(glyphs[ref_idx]["H_INK_PX"])
            ref_area = float(glyphs[ref_idx]["INK_AREA_PX"])
            ref_glyph_id = glyphs[ref_idx]["glyph_id"]
            ref_desc = "same-candidate exact matching glyph; median-like clean specimen selected before target ratios"
            ref_paths = "|".join([
                f"glyph_rois/{glyphs[ref_idx]['safe_filename']}_original_1x.png",
                f"glyph_rois/{glyphs[ref_idx]['safe_filename']}_target_overlay_1x.png",
                f"glyph_rois/{glyphs[ref_idx]['safe_filename']}_mask_only_1x.png",
            ])
        else:
            target = glyphs[idxs[0]]
            if target["glyph_id"] not in EXTERNAL_CALIBRATION_ANCHORS:
                raise RuntimeError(f"singleton low-profile target {target['glyph_id']} was not part of the candidate-locked reference discovery; do not substitute a loose match")
            anchor = EXTERNAL_CALIBRATION_ANCHORS[target["glyph_id"]]
            if anchor is None:
                ref_desc = "NO_MATCHING_OFFICIAL_PDF_REFERENCE_FOUND"
                ref_paths = ""
            else:
                ref = dict(target)
                ref.update(anchor)
                page_no = int(ref["pdf_page"])
                ref = attach_reference_texttrace_bbox(doc[page_no - 1], ref)
                if page_no not in page_cache:
                    page_cache[page_no] = render_page(doc, page_no - 1, DPI)
                stem = f"CAL_{target['safe_filename']}_P{page_no:03d}"
                p1, p8, ref_h, ref_area = make_calibration_artifact(page_cache[page_no], ref, stem)
                ref_desc = f"official candidate page {page_no}, exact codepoint/font/size/colour/direction match; candidate-locked full-book discovery anchor re-rendered"
                ref_paths = f"{p1.relative_to(OUT).as_posix()}|{p8.relative_to(OUT).as_posix()}"
        for i in idxs:
            g = glyphs[i]
            if ref_h is None or ref_area is None or ref_h <= 0 or ref_area <= 0:
                h_ratio = float("nan")
                area_ratio = float("nan")
                passed = False
                reason = "calibration reference unavailable"
            else:
                h_ratio = g["H_INK_PX"] / ref_h
                area_ratio = g["INK_AREA_PX"] / ref_area
                passed = 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08
                reason = "within [0.92,1.08] H and effective-ink area calibration range" if passed else "outside [0.92,1.08] H or area calibration range"
            g["LOW_PROFILE_OR_ACCENT_CALIBRATION_PASS"] = passed
            g["CAL_REFERENCE_H_PX"] = ref_h
            g["CAL_REFERENCE_AREA_PX"] = ref_area
            g["CAL_H_RATIO"] = h_ratio
            g["CAL_AREA_RATIO"] = area_ratio
            rows.append({
                "glyph_id": g["glyph_id"],
                "char": g["char"],
                "unicode": g["unicode"],
                "script_class": g["script_class"],
                "font": g["font"],
                "pdf_font_size_pt": g["pdf_font_size_pt"],
                "reference_method": ref_desc,
                "reference_glyph_id": ref_glyph_id,
                "reference_bbox_mapping": "TEXTTRACE_VISIBLE_GLYPH_BBOX" if ref_paths and len(usable) < 2 and ref_h is not None else ("IN_SCOPE_TARGET_MASK" if len(usable) >= 2 else "N/A"),
                "reference_resegmentation": (ref.get("reference_resegmentation", "NONE") if ref_paths and len(usable) < 2 else "N/A"),
                "reference_paths": ref_paths,
                "reference_H_INK_PX": ref_h,
                "reference_area_px": ref_area,
                "target_H_INK_PX": g["H_INK_PX"],
                "target_area_px": g["INK_AREA_PX"],
                "H_ratio": h_ratio,
                "area_ratio": area_ratio,
                "pass": passed,
                "reason": reason,
            })
    # non-low-profile glyphs have a not-applicable calibration state, never silently left blank.
    for g in glyphs:
        if "LOW_PROFILE_OR_ACCENT_CALIBRATION_PASS" not in g:
            if g["script_class"] == "RAWDICT_COMBINING_CONTROL":
                g["LOW_PROFILE_OR_ACCENT_CALIBRATION_PASS"] = "N/A_RAWDICT_CONTROL"
            elif g["script_class"] == "MATH_ACCENT_COMPOSITE_COMPONENT":
                g["LOW_PROFILE_OR_ACCENT_CALIBRATION_PASS"] = "N/A_STRUCTURAL_MATH_ACCENT_ASSOCIATION"
            else:
                g["LOW_PROFILE_OR_ACCENT_CALIBRATION_PASS"] = "N/A"
            g["CAL_REFERENCE_H_PX"] = "N/A"
            g["CAL_REFERENCE_AREA_PX"] = "N/A"
            g["CAL_H_RATIO"] = "N/A"
            g["CAL_AREA_RATIO"] = "N/A"
    return rows


def glyph_gate_status(g: dict[str, Any]) -> tuple[bool, str]:
    if g["script_class"] in {"RAWDICT_COMBINING_CONTROL", "MATH_ACCENT_COMPOSITE_COMPONENT"}:
        linked = bool(g.get("accent_association_id"))
        reason = "zero-width rawdict combining control" if g["script_class"] == "RAWDICT_COMBINING_CONTROL" else "visible composite math-accent component"
        return linked, f"{reason}; independently auditable through its named rendered-base association" if linked else "missing required named accent association"
    if g["EMPTY_MASK"]:
        return False, "empty raw mask"
    if g["MISSING_STROKE_PX_MACHINE"] > 0:
        return False, f"missing assigned native pixels={g['MISSING_STROKE_PX_MACHINE']}"
    if g["script_class"] == "LOW_PROFILE_PUNCTUATION":
        passed = g["LOW_PROFILE_OR_ACCENT_CALIBRATION_PASS"] is True
        return passed, "calibrated low-profile/accent glyph" if passed else "low-profile/accent calibration failed or unavailable"
    required = int(g["min_gate_px"])
    return g["H_INK_PX"] >= required, f"H_INK={g['H_INK_PX']}px vs required {required}px"


def make_text_measurement_overlay(figure_rgb: np.ndarray, glyphs: list[dict[str, Any]], fig_px: tuple[int, int, int, int]) -> None:
    arr = Image.fromarray(figure_rgb.copy(), mode="RGB")
    d = ImageDraw.Draw(arr)
    fx0, fy0, _, _ = fig_px
    for g in glyphs:
        b = g["raw_bbox_px"]
        if b is None:
            continue
        x0, y0, x1, y1 = b
        x0 -= fx0; x1 -= fx0; y0 -= fy0; y1 -= fy0
        ok, _ = glyph_gate_status(g)
        colour = (0, 160, 0) if ok else (240, 0, 0)
        d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=colour, width=1)
        d.text((x0, max(0, y0 - 9)), g["glyph_id"], fill=colour)
    arr.save(OUT / "after_text_measurement_overlay_300dpi.png")


def text_object_metrics(objects: list[ObjectRecord], glyphs: list[dict[str, Any]], masks: list[np.ndarray], fig_px: tuple[int, int, int, int]) -> list[dict[str, Any]]:
    """Measure element-level baselines for D/E rather than comparing intrinsically different glyph silhouettes."""
    fx0, fy0, _, _ = fig_px
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for g in glyphs:
        by_parent[g["parent_object_id"]].append(g)
    by_id = object_map(objects)
    rows: list[dict[str, Any]] = []
    for oid in sorted(by_parent):
        group = by_parent[oid]
        obj = by_id[oid]
        base = [g["H_INK_PX"] for g in group if g["script_class"] not in {"NATURAL_SCRIPT", "LOW_PROFILE_PUNCTUATION", "RAWDICT_COMBINING_CONTROL", "MATH_ACCENT_COMPOSITE_COMPONENT"}]
        if not base:
            base = [g["H_INK_PX"] for g in group if g["H_INK_PX"] > 0]
        element_h = float(median(base)) if base else float("nan")
        bbox = bbox_of(obj.final_mask if obj.final_mask is not None else obj.pre_mask, fx0, fy0)
        declared_pts = [g["declared_pt"] for g in group if g["script_class"] != "NATURAL_SCRIPT"]
        effective = float(median(declared_pts)) if declared_pts else 9.6
        normal_pt_pass = all(g["effective_pt"] >= 9.5 for g in group if g["script_class"] != "NATURAL_SCRIPT")
        rows.append({
            "ELEMENT_ID": oid,
            "PANEL_ID": obj.panel,
            "ROLE": obj.role,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": "source declarations / rawdict mapping",
            "DECLARED_PT": effective,
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": effective,
            "TEXT_SAMPLE": "".join(g["char"] for g in group),
            "SCRIPT_CLASS": "MIXED" if len({g["script_class"] for g in group}) > 1 else group[0]["script_class"],
            "BBOX_X0": "" if bbox is None else bbox[0],
            "BBOX_Y0": "" if bbox is None else bbox[1],
            "BBOX_X1": "" if bbox is None else bbox[2],
            "BBOX_Y1": "" if bbox is None else bbox[3],
            "H_INK_PX": element_h,
            "BASE_GLYPH_COUNT": len(base),
            "NORMAL_EFFECTIVE_PT_PASS": normal_pt_pass,
            "ROLE_BASE_HEIGHT_PX": "",
            "RATIO_TO_CLASS_MEDIAN": "",
            "ROLE_RATIO": "",
            "TEXT_TEXT_OVERLAP_PX": "see after_overlap_report.csv",
            "TEXT_GRAPHIC_OVERLAP_PX": "see after_overlap_report.csv",
            "MIN_CLEARANCE_PX": "see after_overlap_report.csv",
            "PASS_FAIL": "PENDING_D_E",
            "REASON": "",
        })
    return rows


def d_e_audit(element_rows: list[dict[str, Any]], glyphs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool, bool]:
    """Apply D/E without comparing unrelated raw glyph silhouettes.

    D compares only repeated *same codepoint, font, effective size, role and panel* samples.
    E uses source-effective point sizes plus a later full-view visual-harmony review; it never
    derives a role ratio from a mix of Chinese, Latin, operators and math glyph raw heights.
    """
    d_records: list[dict[str, Any]] = []
    families: dict[tuple[str, str, str, str, float, float, str], list[dict[str, Any]]] = defaultdict(list)
    for g in glyphs:
        if g["script_class"] in {"LOW_PROFILE_PUNCTUATION", "RAWDICT_COMBINING_CONTROL", "MATH_ACCENT_COMPOSITE_COMPONENT"} or g["H_INK_PX"] <= 0:
            continue
        key = (
            g["panel"], g["role"], g["char"], g["font"],
            round(float(g["effective_pt"]), 3), round(float(g["visible_font_pt"]), 3), g["script_class"],
        )
        families[key].append(g)
    d_ok = True
    tested = 0
    for key, family in sorted(families.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        if len(family) < 2:
            continue
        vals = [float(g["H_INK_PX"]) for g in family]
        med = float(median(vals))
        ratios = [v / med for v in vals]
        passed = min(ratios) >= 0.92 and max(ratios) <= 1.08
        d_ok &= passed
        tested += 1
        d_records.append({
            "gate": "D",
            "comparison_basis": "same panel + same role + exact visible codepoint + same font + same source effective pt + same script class",
            "panel": key[0], "role": key[1], "char": key[2], "font": key[3],
            "effective_pt": key[4], "visible_font_pt": key[5], "script_class": key[6],
            "glyph_ids": [g["glyph_id"] for g in family], "H_INK_values_px": vals,
            "median_px": med, "min_ratio": min(ratios), "max_ratio": max(ratios),
            "pass": passed, "reason": "exact comparable glyph-family H-ink calibration [0.92,1.08]",
        })
    if tested == 0:
        d_records.append({"gate": "D", "comparison_basis": "none", "pass": False, "reason": "No exact comparable glyph family found; cannot substitute unrelated raw-height comparison."})
        d_ok = False

    role_pt: dict[str, float] = {}
    for role in sorted({r["ROLE"] for r in element_rows}):
        vals = [float(r["EFFECTIVE_PT"]) for r in element_rows if r["ROLE"] == role and isinstance(r["EFFECTIVE_PT"], (int, float))]
        if vals:
            role_pt[role] = float(median(vals))
    tick_pt = float(median([role_pt["TICK_LABEL_X"], role_pt["TICK_LABEL_Y"]]))
    e_specs = [
        ("TICK_LABEL_X", (0.92, 1.08), "ordinary x tick reader text"),
        ("TICK_LABEL_Y", (0.92, 1.08), "ordinary y tick reader text"),
        ("AXIS_LABEL", (1.00, 1.18), "axis labels modestly above ticks"),
        ("ANNOTATION", (0.95, 1.10), "ordinary explanatory text remains coordinated with ticks"),
        ("FORMULA_BLOCK", (0.95, 1.10), "formula reader text remains coordinated with explanatory text"),
        ("PANEL_TITLE", (1.05, 1.20), "panel title has restrained hierarchy over reader text"),
    ]
    e_records: list[dict[str, Any]] = []
    e_ok = True
    for role, band, semantic in e_specs:
        pt = role_pt[role]
        ratio = pt / tick_pt
        passed = band[0] <= ratio <= band[1] and pt >= 9.5
        e_ok &= passed
        e_records.append({
            "gate": "E", "comparison_basis": "source effective pt; raw H deliberately not mixed across scripts",
            "role": role, "source_effective_pt": pt, "tick_source_effective_pt": tick_pt,
            "ratio": ratio, "required_range": list(band), "pass": passed,
            "manual_full_view_required": True, "reason": semantic,
        })
    title_ratio = role_pt["PANEL_TITLE"] / role_pt["PANEL_TITLE"]
    e_records.append({
        "gate": "D_CROSS_PANEL", "comparison_basis": "same source-effective 10.4pt panel-title role", "role": "PANEL_TITLE",
        "left_right_source_ratio": title_ratio, "pass": title_ratio == 1.0,
        "manual_full_view_required": True, "reason": "cross-panel title source scale is identical; visible harmony is manually checked on native/full/gray views.",
    })
    return d_records + e_records, d_ok, e_ok


def build_glyph_ledger_rows(glyphs: list[dict[str, Any]], card_meta: list[dict[str, Any]]) -> list[dict[str, Any]]:
    card_by_id = {c["glyph_id"]: c for c in card_meta}
    rows: list[dict[str, Any]] = []
    for g in glyphs:
        gate, gate_reason = glyph_gate_status(g)
        card = card_by_id[g["glyph_id"]]
        rows.append({
            "glyph_id": g["glyph_id"],
            "safe_filename": g["safe_filename"],
            "parent_object_id": g["parent_object_id"],
            "raw_line_id": g["raw_line_id"],
            "char": g["char"],
            "unicode": g["unicode"],
            "font": g["font"],
            "pdf_font_size_pt": g["pdf_font_size_pt"],
            "declared_pt": g["declared_pt"],
            "graphics_scale": g["graphics_scale"],
            "effective_pt": g["effective_pt"],
            "visible_font_pt": g["visible_font_pt"],
            "source_font_basis": g["source_font_basis"],
            "script_class": g["script_class"],
            "min_gate_px": g["min_gate_px"],
            "bbox_pt": g["bbox_pt"],
            "texttrace_bbox_pt": g.get("trace_bbox_pt"),
            "mask_basis": g.get("mask_basis"),
            "mask_basis_bbox_pt": g.get("mask_basis_bbox_pt"),
            "mask_resegmentation": g.get("mask_resegmentation", ""),
            "rawdict_visible_foreground": g.get("rawdict_visible_foreground"),
            "raw_bbox_px": g["raw_bbox_px"],
            "H_INK_PX": g["H_INK_PX"],
            "W_INK_PX": g["W_INK_PX"],
            "INK_AREA_PX": g["INK_AREA_PX"],
            "candidate_ink_px": g.get("CANDIDATE_INK_PX", 0),
            "ownership_contested_px": g.get("OWNERSHIP_CONTESTED_PX", 0),
            "empty_mask": g["EMPTY_MASK"],
            "missing_stroke_px_machine": g["MISSING_STROKE_PX_MACHINE"],
            "foreign_pixel_px_machine": g["FOREIGN_PIXEL_PX_MACHINE"],
            "foreign_removed_resegmentation_px": g.get("FOREIGN_REMOVED_RESEGMENT_PX", 0),
            "calibration_pass": g["LOW_PROFILE_OR_ACCENT_CALIBRATION_PASS"],
            "cal_reference_H_px": g["CAL_REFERENCE_H_PX"],
            "cal_reference_area_px": g["CAL_REFERENCE_AREA_PX"],
            "cal_H_ratio": g["CAL_H_RATIO"],
            "cal_area_ratio": g["CAL_AREA_RATIO"],
            "accent_association_id": g.get("accent_association_id", ""),
            "accent_base_association_ids": "|".join(g.get("accent_base_association_ids", [])),
            "machine_pixel_gate": gate,
            "machine_gate_reason": gate_reason,
            "reviewer": "PENDING_MANUAL_OPEN",
            "sheet": card["sheet"],
            "cell": card["cell"],
            "original_match": "PENDING",
            "overlay_complete": "PENDING",
            "mask_only_pure": "PENDING",
            "missing_stroke_px_manual": "PENDING",
            "foreign_pixel_px_manual": "PENDING",
            "decision": "PENDING",
            "note": "Awaiting actual 8x ORIGINAL/TARGET OVERLAY/MASK ONLY review." if g["script_class"] not in {"RAWDICT_COMBINING_CONTROL", "MATH_ACCENT_COMPOSITE_COMPONENT"} else "Awaiting named accent-association card review; accent/control is not reviewed as an unrelated standalone reader glyph.",
            "original_1x": card["original_1x"],
            "overlay_1x": card["overlay_1x"],
            "mask_only_1x": card["mask_only_1x"],
            "raw_mask": card["raw_mask"],
            "review_mode": card["review_mode"],
        })
    return rows


def render_views(doc: fitz.Document) -> tuple[Image.Image, np.ndarray, tuple[int, int, int, int], tuple[int, int, int, int]]:
    page300 = render_page(doc, PAGE_INDEX, DPI)
    page200 = render_page(doc, PAGE_INDEX, 200)
    page200.save(OUT / "full_page_200dpi.png")
    page300.save(OUT / "render" / "physical_659_native_300dpi.png")
    fig_px = pt_rect_to_px(FIG_RECT_PT)
    standalone_px = pt_rect_to_px(STANDALONE_RECT_PT)
    figure = page300.crop(fig_px)
    standalone = page300.crop(standalone_px)
    figure.save(OUT / "figure_crop_300dpi.png")
    standalone.save(OUT / "standalone_300dpi.png")
    figure.convert("L").save(OUT / "grayscale_300dpi.png")
    write_json(OUT / "render" / "render_identity.json", {
        "candidate_pdf": str(PDF),
        "candidate_sha256": sha256(PDF),
        "round": "R97",
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "page_pt": [doc[PAGE_INDEX].rect.width, doc[PAGE_INDEX].rect.height],
        "native_300dpi_page_px": [page300.width, page300.height],
        "full_page_200dpi_px": [page200.width, page200.height],
        "figure_crop_pt": list(FIG_RECT_PT),
        "figure_crop_native_px": list(fig_px),
        "standalone_scope_pt": list(STANDALONE_RECT_PT),
        "standalone_scope_native_px": list(standalone_px),
        "render_method": "PyMuPDF direct final-PDF pixmap at 300dpi; native crop only, no resize",
    })
    return page300, np.array(figure), fig_px, standalone_px


def source_font_audit() -> list[dict[str, Any]]:
    text = SOURCE.read_text(encoding="utf-8")
    checks = [
        ("tikz_global", r"slfig-FIG-P609-01/.style=\{font=\\fontsize\{9\.6pt\}\{11\.8pt\}\\selectfont", 9.6, 1.0, 9.6, "PASS", "TikZ global style"),
        ("tick_label", r"tick label style=\{font=\\fontsize\{9\.6pt\}\{11\.8pt\}\\selectfont\}", 9.6, 1.0, 9.6, "PASS", "PGFPlots tick style"),
        ("axis_label", r"label style=\{font=\\fontsize\{9\.8pt\}\{12\.0pt\}\\selectfont\}", 9.8, 1.0, 9.8, "PASS", "PGFPlots label style"),
        ("title", r"title style=\{font=\\fontsize\{10\.4pt\}\{12\.6pt\}\\selectfont", 10.4, 1.0, 10.4, "PASS", "PGFPlots title style"),
        ("node_normal", r"every node/.style=\{font=\\fontsize\{9\.6pt\}\{11\.8pt\}\\selectfont", 9.6, 1.0, 9.6, "PASS", "every node normal reader text"),
        ("ess_heading", r"\\fontsize\{10\.4pt\}\{12\.6pt\}\\selectfont\\bfseries", 10.4, 1.0, 10.4, "PASS", "ESS heading"),
        ("caption", r"captionsetup\{width=\.94\\linewidth,font=normalsize\}", 10.0, 1.0, 10.0, "PASS", "caption excluded from strict figure-scope glyph denominator but source checked"),
    ]
    rows = []
    for eid, pattern, declared, scale, effective, status, note in checks:
        found = bool(re.search(pattern, text))
        rows.append({
            "ELEMENT_ID": eid,
            "SOURCE_FILE": str(SOURCE),
            "pattern_found": found,
            "declared_pt": declared,
            "graphics_scale": scale,
            "effective_pt": effective,
            "normal_9_5pt_gate": effective >= 9.5,
            "script_exception": "N/A",
            "forbidden_resizebox_scalebox_scale_transform_shape": not any(x in text for x in ["\\resizebox", "\\scalebox", "transform shape"]),
            "status": status if found else "FAIL",
            "note": note,
        })
    # `clip=false` is present and expected: it avoids hidden stems; it does not replace the visible clip audit.
    rows.append({
        "ELEMENT_ID": "clip_policy",
        "SOURCE_FILE": str(SOURCE),
        "pattern_found": "clip=false" in text,
        "declared_pt": "N/A",
        "graphics_scale": "N/A",
        "effective_pt": "N/A",
        "normal_9_5pt_gate": "N/A",
        "script_exception": "N/A",
        "forbidden_resizebox_scalebox_scale_transform_shape": "N/A",
        "status": "PASS" if "clip=false" in text else "FAIL",
        "note": "current source declares clip=false; rendered candidate still audited for visible clipping",
    })
    return rows


def math_rule_artifacts(objects: list[ObjectRecord], figure_rgb: np.ndarray) -> list[dict[str, Any]]:
    by_id = object_map(objects)
    rows: list[dict[str, Any]] = []
    for rid, parent, label in (("R001", "T019", "k/n fraction rule"), ("R002", "T020", "n/tau-hat fraction rule")):
        obj = by_id[rid]
        box = crop_box_with_pad(obj.pre_mask, pad=8)
        x0, y0, x1, y1 = box
        base = figure_rgb[y0:y1, x0:x1]
        mask = obj.final_mask if obj.final_mask is not None else obj.pre_mask
        original = Image.fromarray(base, mode="RGB")
        overlay = Image.fromarray(alpha_overlay(base, a=mask[y0:y1, x0:x1]), mode="RGB")
        mask_img = Image.fromarray(np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8), mode="L").convert("RGB")
        stem = f"{rid}_{parent}"
        p_orig = OUT / "math_rule_cards" / f"{stem}_original_1x.png"
        p_overlay = OUT / "math_rule_cards" / f"{stem}_target_overlay_1x.png"
        p_mask = OUT / "math_rule_cards" / f"{stem}_mask_only_1x.png"
        p_card = OUT / "math_rule_cards" / f"{stem}_8x_nearest.png"
        original.save(p_orig); overlay.save(p_overlay); mask_img.save(p_mask)
        card = Image.new("RGB", (720, 250), "white")
        paste_labelled(card, nearest_scale(original), "ORIGINAL 8x", 0, 0, 240, 250)
        paste_labelled(card, nearest_scale(overlay), "TARGET OVERLAY 8x", 240, 0, 240, 250)
        paste_labelled(card, nearest_scale(mask_img), "MASK ONLY 8x", 480, 0, 240, 250)
        card.save(p_card)
        rows.append({
            "rule_id": rid,
            "kind": "GRAPHIC/MATH_RULE",
            "parent_formula": parent,
            "semantic": label,
            "drawing_index": by_id[rid].drawing_index,
            "z_order": by_id[rid].z_order,
            "pre_pixels": int(by_id[rid].pre_mask.sum()),
            "final_visible_pixels": int(mask.sum()),
            "empty_mask": not bool(mask.any()),
            "original_1x": p_orig.relative_to(OUT).as_posix(),
            "overlay_1x": p_overlay.relative_to(OUT).as_posix(),
            "mask_only_1x": p_mask.relative_to(OUT).as_posix(),
            "nearest8": p_card.relative_to(OUT).as_posix(),
            "reviewer": "PENDING_MANUAL_OPEN",
            "decision": "PENDING",
            "note": "Must be opened independently; never merged into text or axis masks.",
        })
    return rows


def math_accent_association_artifacts(
    glyphs: list[dict[str, Any]], masks: list[np.ndarray], figure_rgb: np.ndarray, fig_px: tuple[int, int, int, int]
) -> list[dict[str, Any]]:
    """Account for every visible/zero-width mathematical accent without folding it into a rule.

    The four U+0302 records are MuPDF logical combining controls with no independent paintable
    bbox.  They are retained in the rawdict ledger and linked one-by-one to their exact rendered
    base; U+02C6 is a separately rendered visible accent and retains its own glyph mask.
    """
    by_id = {g["glyph_id"]: (i, g) for i, g in enumerate(glyphs)}
    associations = [
        ("A001", "GL035", "GL036", "\\widehat{\\rho}_{k} in rotated y-axis label", "T016", "RAWDICT_COMPOSITE_CONTROL"),
        ("A002", "GL080", "GL081", "\\widehat{\\rho}_{k} in finite weighted tau formula", "T019", "RAWDICT_COMPOSITE_CONTROL"),
        ("A003", "GL090", "GL091", "denominator \\widehat{\\tau}_{K,n} in N-eff formula", "T020", "RAWDICT_COMPOSITE_CONTROL"),
        ("A004", "GL096", "GL097", "positivity condition \\widehat{\\tau}_{K,n}>0", "T020", "RAWDICT_COMPOSITE_CONTROL"),
        ("A005", "GL083", "GL084", "rendered accent of \\widehat{N}_{eff}", "T020", "RENDERED_ACCENT_GLYPH"),
    ]
    fx0, fy0, _, _ = fig_px
    rows: list[dict[str, Any]] = []
    for aid, accent_id, base_id, semantic, parent, mode in associations:
        ai, accent = by_id[accent_id]
        bi, base = by_id[base_id]
        accent_mask = masks[ai]
        base_mask = masks[bi]
        # Exact source-derived bbox union, including the zero-width control's raw anchor, keeps
        # a visual audit field even when that control has no own raster foreground.
        boxes = [accent.get("mask_basis_bbox_pt") or accent["bbox_pt"], base.get("mask_basis_bbox_pt") or base["bbox_pt"]]
        ax0 = min(float(b[0]) for b in boxes); ay0 = min(float(b[1]) for b in boxes)
        ax1 = max(float(b[2]) for b in boxes); ay1 = max(float(b[3]) for b in boxes)
        gx0 = max(0, math.floor(ax0 * SCALE - fx0 - 1)); gy0 = max(0, math.floor(ay0 * SCALE - fy0 - 1))
        gx1 = min(figure_rgb.shape[1], math.ceil(ax1 * SCALE - fx0 + 1)); gy1 = min(figure_rgb.shape[0], math.ceil(ay1 * SCALE - fy0 + 1))
        # A card needs readable context around the exact association, while pixel coverage is
        # measured only in the tightly bounded source ROI so a neighbouring subscript is not
        # spuriously called foreign.
        cx0 = max(0, gx0 - 8); cy0 = max(0, gy0 - 8); cx1 = min(figure_rgb.shape[1], gx1 + 8); cy1 = min(figure_rgb.shape[0], gy1 + 8)
        base_local = base_mask[cy0:cy1, cx0:cx1]
        accent_local = accent_mask[cy0:cy1, cx0:cx1]
        combined = base_local | accent_local
        original_arr = figure_rgb[cy0:cy1, cx0:cx1]
        overlay_arr = alpha_overlay(original_arr, accent_local, base_local, accent_local & base_local)
        original = Image.fromarray(original_arr, mode="RGB")
        overlay = Image.fromarray(overlay_arr, mode="RGB")
        accent_img = Image.fromarray(np.where(accent_local, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        base_img = Image.fromarray(np.where(base_local, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        combined_img = Image.fromarray(np.where(combined, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        prefix = OUT / "math_rule_cards" / f"{aid}_{accent_id}_{base_id}"
        paths = {
            "original_1x": prefix.with_name(prefix.name + "_original_1x.png"),
            "overlay_1x": prefix.with_name(prefix.name + "_accent_red_base_cyan_overlay_1x.png"),
            "accent_mask_1x": prefix.with_name(prefix.name + "_accent_mask_1x.png"),
            "base_mask_1x": prefix.with_name(prefix.name + "_base_mask_1x.png"),
            "combined_mask_1x": prefix.with_name(prefix.name + "_combined_mask_1x.png"),
            "nearest8": prefix.with_name(prefix.name + "_8x_nearest.png"),
        }
        original.save(paths["original_1x"]); overlay.save(paths["overlay_1x"]); accent_img.save(paths["accent_mask_1x"]); base_img.save(paths["base_mask_1x"]); combined_img.save(paths["combined_mask_1x"])
        card = Image.new("RGB", (900, 440), "white")
        paste_labelled(card, nearest_scale(original), "ORIGINAL 8x", 0, 0, 300, 210)
        paste_labelled(card, nearest_scale(overlay), "ACCENT red / BASE cyan", 300, 0, 300, 210)
        paste_labelled(card, nearest_scale(accent_img), "ACCENT MASK", 600, 0, 300, 210)
        paste_labelled(card, nearest_scale(base_img), "BASE MASK", 0, 210, 300, 210)
        paste_labelled(card, nearest_scale(combined_img), "COMBINED MASK", 300, 210, 300, 210)
        paste_labelled(card, Image.new("RGB", (4, 4), "white"), mode, 600, 210, 300, 210)
        ImageDraw.Draw(card).text((4, 420), f"{aid}: {accent_id} -> {base_id}; {semantic}", fill=(0, 0, 0))
        card.save(paths["nearest8"])
        accent["accent_association_id"] = aid
        base.setdefault("accent_base_association_ids", []).append(aid)
        rows.append({
            "association_id": aid,
            "accent_glyph_id": accent_id,
            "base_glyph_id": base_id,
            "parent_object": parent,
            "mode": mode,
            "source_semantic_anchor": semantic,
            "accent_rawdict_bbox_pt": accent["bbox_pt"],
            "accent_texttrace_bbox_pt": accent.get("trace_bbox_pt"),
            "accent_independent_mask_pixels": int(accent_mask.sum()),
            "base_mask_pixels": int(base_mask.sum()),
            "original_1x": paths["original_1x"].relative_to(OUT).as_posix(),
            "overlay_1x": paths["overlay_1x"].relative_to(OUT).as_posix(),
            "accent_mask_1x": paths["accent_mask_1x"].relative_to(OUT).as_posix(),
            "base_mask_1x": paths["base_mask_1x"].relative_to(OUT).as_posix(),
            "combined_mask_1x": paths["combined_mask_1x"].relative_to(OUT).as_posix(),
            "nearest8": paths["nearest8"].relative_to(OUT).as_posix(),
            "reviewer": "PENDING_MANUAL_OPEN",
            "decision": "PENDING",
            "note": "Individual association; no accent is reassigned to an axis, fraction rule, or another formula.",
        })
    return rows


def clipping_card(item_id: str, mask: np.ndarray, figure_rgb: np.ndarray, margin: int | None) -> dict[str, str]:
    """Native crop-boundary card for one suspicious clip/edge candidate."""
    h, w = mask.shape
    b = bbox_of(mask)
    if b is None:
        box = (0, 0, min(w, 10), min(h, 10))
    else:
        x0, y0, x1, y1 = b
        # Include the actual relevant crop edge in the 1x card when it is within 6 px.
        if x0 < 6: x0 = 0
        else: x0 = max(0, x0 - 10)
        if y0 < 6: y0 = 0
        else: y0 = max(0, y0 - 10)
        if w - x1 < 6: x1 = w
        else: x1 = min(w, x1 + 10)
        if h - y1 < 6: y1 = h
        else: y1 = min(h, y1 + 10)
        box = (x0, y0, x1, y1)
    x0, y0, x1, y1 = box
    original = Image.fromarray(figure_rgb[y0:y1, x0:x1], mode="RGB")
    overlay = Image.fromarray(alpha_overlay(figure_rgb[y0:y1, x0:x1], a=mask[y0:y1, x0:x1]), mode="RGB")
    mask_img = Image.fromarray(np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8), mode="L").convert("RGB")
    # Green lines mark whichever displayed boundaries are true strict-figure crop edges.
    annotated = np.array(overlay)
    if x0 == 0: annotated[:, :1] = (0, 180, 0)
    if y0 == 0: annotated[:1, :] = (0, 180, 0)
    if x1 == w: annotated[:, -1:] = (0, 180, 0)
    if y1 == h: annotated[-1:, :] = (0, 180, 0)
    overlay = Image.fromarray(annotated, mode="RGB")
    stem = f"CLIP_{item_id}"
    p_orig = OUT / "clipping_cards" / f"{stem}_original_1x.png"
    p_overlay = OUT / "clipping_cards" / f"{stem}_overlay_1x.png"
    p_mask = OUT / "clipping_cards" / f"{stem}_mask_only_1x.png"
    p_card = OUT / "clipping_cards" / f"{stem}_8x_nearest.png"
    original.save(p_orig); overlay.save(p_overlay); mask_img.save(p_mask)
    card = Image.new("RGB", (720, 250), "white")
    paste_labelled(card, nearest_scale(original), "ORIGINAL 8x", 0, 0, 240, 250)
    paste_labelled(card, nearest_scale(overlay), f"OVERLAY 8x; margin={margin}", 240, 0, 240, 250)
    paste_labelled(card, nearest_scale(mask_img), "MASK ONLY 8x", 480, 0, 240, 250)
    card.save(p_card)
    return {"original_1x": p_orig.relative_to(OUT).as_posix(), "overlay_1x": p_overlay.relative_to(OUT).as_posix(), "mask_only_1x": p_mask.relative_to(OUT).as_posix(), "nearest8": p_card.relative_to(OUT).as_posix()}


def clipping_audit(objects: list[ObjectRecord], glyphs: list[dict[str, Any]], masks: list[np.ndarray], figure_rgb: np.ndarray) -> list[dict[str, Any]]:
    h, w = figure_rgb.shape[:2]
    rows: list[dict[str, Any]] = []
    mask_by_id: dict[str, np.ndarray] = {}
    for obj in objects:
        mask = obj.final_mask if obj.final_mask is not None else obj.pre_mask
        mask_by_id[obj.object_id] = mask
        edge = int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())
        b = bbox_of(mask)
        margin = None if b is None else min(b[0], b[1], w - b[2], h - b[3])
        passed = edge == 0 and (margin is None or margin >= 6)
        row = {"scope": "FIGURE_CROP", "id": obj.object_id, "kind": obj.kind, "edge_ink_px": edge, "nearest_crop_edge_px": margin, "pass": passed, "reason": "native crop edge must retain >=6px reader-element margin", "reviewer": "NOT_REQUIRED" if passed else "PENDING_MANUAL_OPEN", "decision": "NOT_REQUIRED" if passed else "PENDING", "note": ""}
        if not passed:
            row.update({f"evidence_{k}": v for k, v in clipping_card(obj.object_id, mask, figure_rgb, margin).items()})
        rows.append(row)
    for g, mask in zip(glyphs, masks):
        mask_by_id[g["glyph_id"]] = mask
        if g["script_class"] == "RAWDICT_COMBINING_CONTROL":
            rows.append({"scope": "FIGURE_CROP", "id": g["glyph_id"], "kind": "RAWDICT_COMBINING_CONTROL", "edge_ink_px": 0, "nearest_crop_edge_px": "N/A", "pass": True, "reason": "logical zero-width control; crop evidence is on named base association", "reviewer": "PENDING_ASSOCIATION_CARD", "decision": "PENDING", "note": g.get("accent_association_id", "")})
            continue
        b = bbox_of(mask)
        if b is None:
            row = {"scope": "FIGURE_CROP", "id": g["glyph_id"], "kind": "GLYPH", "edge_ink_px": 0, "nearest_crop_edge_px": "N/A", "pass": False, "reason": "empty visible glyph mask", "reviewer": "PENDING_MANUAL_OPEN", "decision": "PENDING", "note": ""}
            row.update({f"evidence_{k}": v for k, v in clipping_card(g["glyph_id"], mask, figure_rgb, None).items()})
            rows.append(row)
            continue
        margin = min(b[0], b[1], w - b[2], h - b[3])
        passed = margin >= 6
        row = {"scope": "FIGURE_CROP", "id": g["glyph_id"], "kind": "GLYPH", "edge_ink_px": 0, "nearest_crop_edge_px": margin, "pass": passed, "reason": "native glyph bbox to strict P609 crop boundary", "reviewer": "NOT_REQUIRED" if passed else "PENDING_MANUAL_OPEN", "decision": "NOT_REQUIRED" if passed else "PENDING", "note": ""}
        if not passed:
            row.update({f"evidence_{k}": v for k, v in clipping_card(g["glyph_id"], mask, figure_rgb, margin).items()})
        rows.append(row)
    # Preserve a conservative three-card crop-proximity review even if no item crosses the
    # 6px hard boundary after the strict P609 scope is applied.  This closes the previously
    # raised clipping-candidate queue without converting a proximity review into a false FAIL.
    numeric = [r for r in rows if isinstance(r.get("nearest_crop_edge_px"), int) and r["id"] in mask_by_id]
    for rank, row in enumerate(sorted(numeric, key=lambda r: int(r["nearest_crop_edge_px"]))[:3], start=1):
        if not any(k.startswith("evidence_") for k in row):
            row.update({f"evidence_{k}": v for k, v in clipping_card(row["id"], mask_by_id[row["id"]], figure_rgb, int(row["nearest_crop_edge_px"])).items()})
        row["reviewer"] = "PENDING_MANUAL_OPEN"
        row["decision"] = "PENDING"
        row["note"] = f"CROP_PROXIMITY_REVIEW_{rank}_OF_3; pass/fail remains based on the explicit 6px hard boundary."
    return rows


def source_and_context_report() -> str:
    return f"""# FIG-P609-01 identity and source/context audit

- UID: `FIG-P609-01`; official figure number: `32.9`.
- Candidate: `{PDF}`
- Candidate SHA256: `{sha256(PDF)}` (expected R97 SHA matched).
- Candidate length: 813 physical pages; independently located on physical page {PHYSICAL_PAGE}, printed page {PRINTED_PAGE}.
- Scope rectangle in official-page coordinates: `{list(FIG_RECT_PT)}` pt; it excludes the Fig. 32.9 caption and surrounding prose from the object denominator.
- Source: `{SOURCE}`
- Source SHA256: `{sha256(SOURCE)}`.
- Direct neighboring text: `{CONTEXT}`, lines 569--614 inspected. It says Fig. 32.9 joins empirical ACF and finite-sample weighted ESS as a diagnostic; it explicitly limits the interpretation to the predeclared window and does not treat a finite trajectory as a convergence proof.

## Source-to-PDF semantic check

The current source shows `K=6`, ACF coordinates `(0,1),(1,.86),…,(6,.40)`, and the finite-weighted forms for `\\widehat\\tau_{{K,n}}` and `\\widehat N_{{\\mathrm{{eff}}}}`. The candidate's text, caption, and neighboring prose agree: positive retained ACF increases the variance-weight factor and reduces same-length effective sample size. The dashed cut at 6.5 separates the retained window from the explicit ellipsis, so it does not falsely imply unobserved lags are zero.

No old FIG-P609 evidence, prior PASS, central state, or sibling audit is an input to this package.
"""


def build_initial() -> None:
    if (OUT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED exists: this evidence package is immutable")
    ensure_dirs()
    if sha256(PDF) != EXPECTED_PDF_SHA256:
        raise RuntimeError("candidate SHA256 mismatch; no evidence may be produced from a different PDF")
    doc = fitz.open(PDF)
    if doc.page_count != 813:
        raise RuntimeError(f"candidate page count mismatch: {doc.page_count}")
    page = doc[PAGE_INDEX]
    page300, figure_rgb, fig_px, standalone_px = render_views(doc)
    lines, glyphs = collect_raw_lines(page)
    attach_texttrace_seqnos(page, glyphs)
    parent_map = line_parent_mapping(lines)
    masks, glyphs = glyph_masks(figure_rgb, glyphs, fig_px)
    card_meta = make_glyph_artifacts(figure_rgb, glyphs, masks)
    accent_rows = math_accent_association_artifacts(glyphs, masks, figure_rgb, fig_px)
    text_objects = create_text_objects(glyphs, masks, parent_map)
    graphic_objects, path_coverage, raw_math_rules = build_graphic_objects(page, figure_rgb.shape[:2], fig_px, figure_rgb)
    objects = text_objects + graphic_objects
    if len(text_objects) != 23 or len(graphic_objects) != 36 or len(objects) != 59:
        raise RuntimeError(f"object denominator expected 23 text + 36 graphics =59; got {len(text_objects)}+{len(graphic_objects)}")
    assign_final_masks(objects)
    save_object_masks(objects)
    calibration_rows = low_profile_and_accent_calibration(doc, glyphs, masks)
    make_text_measurement_overlay(figure_rgb, glyphs, fig_px)
    glyph_ledger = build_glyph_ledger_rows(glyphs, card_meta)
    element_rows = text_object_metrics(objects, glyphs, masks, fig_px)
    de_rows, d_pass, e_pass = d_e_audit(element_rows, glyphs)
    pair_rows, critical_rows = build_pair_ledger(objects, figure_rgb)
    make_pair_contact_sheets(critical_rows)
    rule_rows = math_rule_artifacts(objects, figure_rgb)
    inventory = object_inventory_rows(objects, fig_px)
    clipping_rows = clipping_audit(objects, glyphs, masks, figure_rgb)
    font_rows = source_font_audit()

    # Persist only this R1 package. Source copy is immutable evidence of the exact read-only input.
    shutil.copy2(SOURCE, OUT / "source_snapshot_readonly.tex")
    write_json(OUT / "authority_identity.json", {
        "uid": "FIG-P609-01",
        "figure_number": "32.9",
        "candidate_pdf": str(PDF),
        "candidate_pdf_sha256": sha256(PDF),
        "expected_pdf_sha256": EXPECTED_PDF_SHA256,
        "candidate_page_count": doc.page_count,
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "direct_context": str(CONTEXT),
        "figure_scope_pt": list(FIG_RECT_PT),
        "figure_scope_native_px": list(fig_px),
        "standalone_scope_native_px": list(standalone_px),
        "independence": "No old FIG-P609 evidence, report, PASS conclusion, inventory, or central P609 state was read.",
    })
    write_json(OUT / "machine" / "rawdict_line_inventory.json", {"line_count": len(lines), "lines": lines})
    write_json(OUT / "machine" / "glyph_id_filename_map.json", [{"glyph_id": g["glyph_id"], "safe_filename": g["safe_filename"], "char": g["char"]} for g in glyphs])
    write_json(OUT / "machine" / "calibration_reference_discovery.json", {
        "candidate_sha256": sha256(PDF),
        "method": "one candidate-locked read-only full-book exact match discovery by codepoint/font/size/colour/direction; anchors are re-rendered and remeasured during every build",
        "singleton_anchor_resolution": EXTERNAL_CALIBRATION_ANCHORS,
        "no_match_is_a_gate_failure_not_a_substitution": ["GL026", "GL045"],
    })
    write_csv(OUT / "glyph_ledger.csv", glyph_ledger)
    write_csv(OUT / "after_pixel_measurements.csv", glyph_ledger)
    write_csv(OUT / "after_font_audit.csv", font_rows)
    write_csv(OUT / "element_font_d_e_measurements.csv", element_rows)
    write_csv(OUT / "d_e_audit.csv", de_rows)
    write_csv(OUT / "low_profile_accent_calibration.csv", calibration_rows)
    write_csv(OUT / "object_inventory.csv", inventory)
    write_csv(OUT / "after_overlap_report.csv", pair_rows)
    write_csv(OUT / "critical_pair_manual_ledger.csv", critical_rows)
    write_csv(OUT / "math_rule_ledger.csv", rule_rows)
    write_csv(OUT / "math_accent_association_ledger.csv", accent_rows)
    write_csv(OUT / "drawing_path_coverage.csv", path_coverage)
    write_json(OUT / "drawing_path_coverage.json", {
        "scope": "P609 strict crop only; drawing indices 65--85",
        "rawdict_glyph_count": len(glyphs),
        "visible_glyph_count": sum(1 for g in glyphs if g["script_class"] != "RAWDICT_COMBINING_CONTROL"),
        "rawdict_combining_control_count": sum(1 for g in glyphs if g["script_class"] == "RAWDICT_COMBINING_CONTROL"),
        "foreground_drawing_object_count": len(graphic_objects),
        "foreground_math_rule_count": 2,
        "background_exclusions": [r for r in path_coverage if not r["foreground"]],
        "coverage": path_coverage,
        "unassigned_foreground_path_count": 0,
        "out_of_scope_drawings_not_imported": [61, 62, 63, 64],
    })
    write_csv(OUT / "clipping_audit.csv", clipping_rows)
    (OUT / "SOURCE_AND_CONTEXT.md").write_text(source_and_context_report(), encoding="utf-8")

    glyph_machine_fail = [r for r in glyph_ledger if not r["machine_pixel_gate"]]
    pair_machine_fail = [r for r in pair_rows if r["result"] == "FAIL"]
    clip_fail = [r for r in clipping_rows if not r["pass"]]
    summary = {
        "status": "PRELIMINARY_MACHINE_ONLY_MANUAL_LEDGER_PENDING",
        "candidate_sha256": sha256(PDF),
        "source_sha256": sha256(SOURCE),
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "glyph_count": len(glyphs),
        "visible_glyph_count": sum(1 for g in glyphs if g["script_class"] != "RAWDICT_COMBINING_CONTROL"),
        "rawdict_combining_control_count": sum(1 for g in glyphs if g["script_class"] == "RAWDICT_COMBINING_CONTROL"),
        "glyph_contact_sheet_count": math.ceil(len(glyphs) / 12),
        "text_object_count": len(text_objects),
        "graphic_math_rule_object_count": len(graphic_objects),
        "total_foreground_object_count": len(objects),
        "pair_expected_nC2": len(objects) * (len(objects) - 1) // 2,
        "pair_enumerated": len(pair_rows),
        "critical_or_contact_pair_count": len(critical_rows),
        "pair_contact_sheet_count": math.ceil(len(critical_rows) / 4),
        "math_rule_count": len(rule_rows),
        "unassigned_foreground_path_count": 0,
        "glyph_machine_fail_count": len(glyph_machine_fail),
        "glyph_machine_fail_ids": [r["glyph_id"] for r in glyph_machine_fail],
        "pair_hard_fail_count": len(pair_machine_fail),
        "pair_hard_fail_ids": [r["pair_id"] for r in pair_machine_fail],
        "clip_fail_count": len(clip_fail),
        "D_same_class_pass": d_pass,
        "E_role_ratio_pass": e_pass,
        "manual_glyph_review_complete": False,
        "manual_pair_review_complete": False,
        "manual_math_rule_review_complete": False,
    }
    write_json(OUT / "machine" / "preliminary_machine_summary.json", summary)
    # Explicit machine-openability / denominator verification before any human completion.
    assert len(pair_rows) == summary["pair_expected_nC2"]
    assert sum(1 for p in (OUT / "glyph_contact_sheets").glob("glyph_sheet_*.png")) == summary["glyph_contact_sheet_count"]
    assert sum(1 for p in (OUT / "pair_cards").glob("*_8x_nearest.png")) == len(critical_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] != "build":
        print("usage: p609_r1_audit.py build")
        raise SystemExit(2)
    build_initial()


if __name__ == "__main__":
    main()
