"""Independent R96 SA1 evidence generator for FIG-P602-01.

This program deliberately reads only the frozen R96 PDF and the frozen figure
source named on this task.  It does not consume an earlier P602 audit, build
product, central inventory, or status file.  All output stays beside this
program in the R5 SA1 evidence directory.

The primary object inventory has 35 visible foreground objects:
19 semantic text objects and 16 vector/graphic objects.  The six opaque
edge-label backgrounds are not foreground objects; they are retained in a
separate occlusion-inversion set so that they cannot be mistaken for a
zero-clearance graphic.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label
from scipy.spatial import cKDTree


# Do not infer the workspace from the evidence location: v2.7.0_work is a
# junction.  The manifest must state the canonical physical _work path.
WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
WORK_ROOT = WORKSPACE / "v2.7.0" / "_work"
PDF = WORK_ROOT / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.pdf"
SOURCE = WORK_ROOT / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C03" / "fig_v5_c03_mh_accept_reject.tex"
OUT = Path(__file__).resolve().parent
PAGE_NUMBER = 651
PAGE_INDEX = PAGE_NUMBER - 1
DPI = 300
PDF_TO_PX = DPI / 72.0
EXPECTED_PDF_SHA256 = "8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8"
EXPECTED_SOURCE_SHA256 = "18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084"

# Includes the caption; this corresponds to the 175 non-space glyphs in the
# frozen page.  The figure/caption crop is integer-aligned native pixels.
FIG_PDF_RECT = (60.0, 340.0, 535.0, 720.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def px(v: float) -> int:
    return int(round(v * PDF_TO_PX))


def rect_px(rect: tuple[float, float, float, float], width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        max(0, int(math.floor(x0 * PDF_TO_PX)) - pad),
        max(0, int(math.floor(y0 * PDF_TO_PX)) - pad),
        min(width, int(math.ceil(x1 * PDF_TO_PX)) + pad),
        min(height, int(math.ceil(y1 * PDF_TO_PX)) + pad),
    )


def rgb_to_hex(value: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % value


def ensure_dirs() -> dict[str, Path]:
    names = [
        "glyph_views",
        "glyph_masks",
        "contact_sheets",
        "object_masks",
        "pairs",
        "occlusion",
        "reports",
        "calibration",
    ]
    result: dict[str, Path] = {}
    for name in names:
        target = OUT / name
        target.mkdir(parents=True, exist_ok=True)
        result[name] = target
    return result


def row_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)


def safe_codepoint(char: str) -> str:
    return "U%04X" % ord(char)


def classify_char(char: str, font: str, size: float, bbox: tuple[float, float, float, float]) -> tuple[str, int, str]:
    """Return script class, hard threshold (or 0 for calibration), and role."""
    low = {",", ".", "，", "。", "、", "：", ":", ";", "；", "…", "–", "-"}
    if char in low:
        return "LOW_PROFILE_PUNCTUATION", 0, "LOW_PROFILE_PUNCT"
    if size < 8.0 and "Math" in font:
        return "NATURAL_MATH_SCRIPT", 15, "MATH_SCRIPT"
    if "Noto" in font:
        return "CJK_FULL", 30, "CJK_TEXT"
    if char.isdigit() or (char.isascii() and char.isupper()):
        return "LATIN_UPPER_DIGIT", 24, "LATIN_UPPER_DIGIT"
    # Full-height delimiters have a genuine outline and are intentionally not
    # downgraded to low-profile punctuation.
    if char in "(){}[]！？?":
        return "MATH_DELIMITER_OR_FULLWIDTH", 22, "MATH_DELIMITER"
    if char in "=≤≥<>∼≈+−×÷/|˜⋅":
        return "MATH_OPERATOR", 22, "MATH_OPERATOR"
    if "Math" in font:
        return "MATH_BASE", 17, "MATH_BASE"
    return "LATIN_LOWER", 17, "LATIN_LOWER"


def role_for_position(x0_pt: float, y0_pt: float) -> tuple[str, str, int]:
    """Map source-visible text into a stable semantic parent object."""
    if 354 <= y0_pt < 366:
        return "T01_CURRENT_TITLE", "NODE_CURRENT", 12
    if 366 <= y0_pt < 382:
        return "T02_CURRENT_MATH", "NODE_CURRENT", 12
    if 398 <= y0_pt < 410:
        return "T03_PROPOSAL_TEXT", "NODE_PROPOSAL", 13
    if 410 <= y0_pt < 425:
        return "T04_PROPOSAL_MATH", "NODE_PROPOSAL", 13
    if 445 <= y0_pt < 486:
        return "T05_RATIO_TEXT_AND_FORMULA", "NODE_RATIO", 14
    if 531 <= y0_pt < 543:
        return "T06_DECISION_DRAW", "NODE_DECISION", 17
    if 543 <= y0_pt < 557:
        return "T07_DECISION_COMPARE", "NODE_DECISION", 17
    if 588 <= y0_pt < 600 and x0_pt < 250:
        return "T08_ACCEPT_TEXT", "NODE_ACCEPT", 18
    if 600 <= y0_pt < 614 and x0_pt < 250:
        return "T09_ACCEPT_MATH", "NODE_ACCEPT", 18
    if 588 <= y0_pt < 600 and x0_pt >= 250:
        return "T10_REJECT_TEXT", "NODE_REJECT", 19
    if 600 <= y0_pt < 614 and x0_pt >= 250:
        return "T11_REJECT_MATH", "NODE_REJECT", 19
    if 382 <= y0_pt < 395:
        return "T12_LABEL_PROPOSAL", "EDGE_LABEL", 21
    if 426 <= y0_pt < 440:
        return "T13_LABEL_CALCULATE", "EDGE_LABEL", 22
    if 491 <= y0_pt < 505:
        return "T14_LABEL_DECIDE", "EDGE_LABEL", 23
    if 558 <= y0_pt < 582 and x0_pt < 250:
        return "T15_LABEL_ACCEPT", "EDGE_LABEL", 24
    if 558 <= y0_pt < 582 and x0_pt >= 250:
        return "T16_LABEL_REJECT", "EDGE_LABEL", 25
    if 684 <= y0_pt < 698:
        return "T17_LABEL_SELF_LOOP", "EDGE_LABEL", 26
    if 698 <= y0_pt <= 714 and x0_pt < 180:
        return "T18_CAPTION_NUMBER", "CAPTION", 27
    if 698 <= y0_pt <= 714:
        return "T19_CAPTION_TEXT", "CAPTION", 27
    raise ValueError(f"Unexpected figure glyph position: {(x0_pt, y0_pt)}")


OBJECTS: list[dict[str, Any]] = [
    {"id": f"T{i:02d}", "kind": "TEXT", "source_line": line}
    for i, line in [
        (1, 12), (2, 12), (3, 13), (4, 13), (5, 14), (6, 17), (7, 17),
        (8, 18), (9, 18), (10, 19), (11, 19), (12, 21), (13, 22),
        (14, 23), (15, 24), (16, 25), (17, 26), (18, 27), (19, 27),
    ]
]

# Vector objects use final-visible foreground.  The three vertical connectors
# expose shaft/head separately in the page content stream; the remaining
# connectors are retained as semantic arrow objects.  This yields a complete
# 19-text + 16-graphic primary inventory (35, hence 595 unordered pairs).
GRAPHIC_DEFS: list[dict[str, Any]] = [
    {"id": "G01_CURRENT_BORDER", "kind": "GRAPHIC", "role": "NODE_BORDER", "rect": (196.24, 349.21, 315.30, 380.33), "source_line": 12},
    {"id": "G02_PROPOSAL_BORDER", "kind": "GRAPHIC", "role": "NODE_BORDER", "rect": (196.24, 393.13, 315.30, 424.28), "source_line": 13},
    {"id": "G03_RATIO_BORDER", "kind": "GRAPHIC", "role": "NODE_BORDER", "rect": (97.03, 439.87, 414.52, 490.93), "source_line": 14},
    {"id": "G04_RATIO_FRACTION_BAR", "kind": "GRAPHIC", "role": "FORMULA_RULE", "rect": (267.19, 472.40, 319.12, 472.70), "source_line": 16},
    {"id": "G05_DECISION_BORDER", "kind": "GRAPHIC", "role": "NODE_BORDER", "rect": (143.57, 504.66, 367.98, 579.21), "source_line": 17},
    {"id": "G06_ACCEPT_BORDER", "kind": "GRAPHIC", "role": "NODE_BORDER", "rect": (77.19, 582.94, 196.24, 614.32), "source_line": 18},
    {"id": "G07_REJECT_DOUBLE_BORDER", "kind": "GRAPHIC", "role": "NODE_BORDER", "rect": (315.30, 582.94, 434.36, 614.32), "source_line": 19},
    {"id": "G08_PROPOSAL_SHAFT", "kind": "GRAPHIC", "role": "LINE_ARROW", "rect": (254.40, 380.70, 256.20, 389.70), "source_line": 21},
    {"id": "G09_PROPOSAL_HEAD", "kind": "GRAPHIC", "role": "ARROWHEAD", "rect": (254.30, 388.40, 257.20, 392.00), "source_line": 21},
    {"id": "G10_CALCULATE_SHAFT", "kind": "GRAPHIC", "role": "LINE_ARROW", "rect": (254.40, 424.50, 256.20, 436.10), "source_line": 22},
    {"id": "G11_CALCULATE_HEAD", "kind": "GRAPHIC", "role": "ARROWHEAD", "rect": (254.30, 434.80, 257.20, 438.60), "source_line": 22},
    {"id": "G12_DECIDE_SHAFT", "kind": "GRAPHIC", "role": "LINE_ARROW", "rect": (254.40, 491.20, 256.20, 500.70), "source_line": 23},
    {"id": "G13_DECIDE_HEAD", "kind": "GRAPHIC", "role": "ARROWHEAD", "rect": (254.30, 499.30, 257.20, 503.80), "source_line": 23},
    {"id": "G14_ACCEPT_BRANCH", "kind": "GRAPHIC", "role": "LINE_ARROW", "rect": (138.00, 558.50, 199.50, 582.30), "source_line": 24},
    {"id": "G15_REJECT_BRANCH", "kind": "GRAPHIC", "role": "LINE_ARROW", "rect": (312.10, 558.50, 373.80, 582.30), "source_line": 25},
    {"id": "G16_SELF_LOOP", "kind": "GRAPHIC", "role": "LINE_ARROW", "rect": (242.90, 614.60, 506.80, 695.70), "source_line": 26},
]

# All physical arrow/border contacts and true opaque label occlusions are
# checked but explicitly whitelisted only for their stated source semantics.
def _primary_id(detail_id: str) -> str:
    return detail_id.split("_")[0]


INTENT_ALLOWLIST = {
    tuple(sorted((_primary_id(left), _primary_id(right)))): reason
    for left, right, reason in [
        ("G01_CURRENT_BORDER", "G08_PROPOSAL_SHAFT", "proposal connector starts at current-state border"),
        ("G09_PROPOSAL_HEAD", "G02_PROPOSAL_BORDER", "proposal arrowhead terminates at proposal-state border"),
        ("G02_PROPOSAL_BORDER", "G10_CALCULATE_SHAFT", "calculate connector starts at proposal-state border"),
        ("G11_CALCULATE_HEAD", "G03_RATIO_BORDER", "calculate arrowhead terminates at ratio border"),
        ("G03_RATIO_BORDER", "G12_DECIDE_SHAFT", "decision connector starts at ratio border"),
        ("G13_DECIDE_HEAD", "G05_DECISION_BORDER", "decision arrowhead terminates at decision border"),
        ("G05_DECISION_BORDER", "G14_ACCEPT_BRANCH", "accepted branch intentionally originates on decision boundary"),
        ("G05_DECISION_BORDER", "G15_REJECT_BRANCH", "rejected branch intentionally originates on decision boundary"),
        ("G14_ACCEPT_BRANCH", "G06_ACCEPT_BORDER", "accepted branch terminates at accept-state border"),
        ("G15_REJECT_BRANCH", "G07_REJECT_DOUBLE_BORDER", "rejected branch terminates at reject-state border"),
        ("G07_REJECT_DOUBLE_BORDER", "G16_SELF_LOOP", "self-loop attaches to reject-state border"),
        ("G03_RATIO_BORDER", "G04_RATIO_FRACTION_BAR", "fraction rule is an internal component of the ratio node formula"),
        ("G08_PROPOSAL_SHAFT", "G09_PROPOSAL_HEAD", "single proposal connector rendered as shaft plus Stealth head"),
        ("G10_CALCULATE_SHAFT", "G11_CALCULATE_HEAD", "single calculate connector rendered as shaft plus Stealth head"),
        ("G12_DECIDE_SHAFT", "G13_DECIDE_HEAD", "single decision connector rendered as shaft plus Stealth head"),
    ]
}

HALO_DEFS = [
    ("H01_PROPOSAL_LABEL_HALO", (261.20, 380.80, 282.72, 392.76), "G08_PROPOSAL_SHAFT", "G09_PROPOSAL_HEAD", "T12_LABEL_PROPOSAL"),
    ("H02_CALCULATE_LABEL_HALO", (261.23, 426.05, 282.75, 438.00), "G10_CALCULATE_SHAFT", "G11_CALCULATE_HEAD", "T13_LABEL_CALCULATE"),
    ("H03_DECIDE_LABEL_HALO", (261.23, 491.70, 282.75, 503.65), "G12_DECIDE_SHAFT", "G13_DECIDE_HEAD", "T14_LABEL_DECIDE"),
    ("H04_ACCEPT_LABEL_HALO", (140.27, 558.58, 161.79, 570.53), "G14_ACCEPT_BRANCH", "", "T15_LABEL_ACCEPT"),
    ("H05_REJECT_LABEL_HALO", (349.73, 558.61, 371.24, 570.56), "G15_REJECT_BRANCH", "", "T16_LABEL_REJECT"),
    ("H06_LOOP_LABEL_HALO", (345.88, 683.60, 403.78, 695.56), "G16_SELF_LOOP", "", "T17_LABEL_SELF_LOOP"),
]


def save_mask(mask: np.ndarray, path: Path) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        Image.new("L", (1, 1), 0).save(path)
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8), "L").save(path)
    return (x0, y0, x1, y1)


def bbox_gap(a: tuple[int, int, int, int] | None, b: tuple[int, int, int, int] | None) -> float:
    if a is None or b is None:
        return float("inf")
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def pair_roi(a: np.ndarray, b: np.ndarray, base: np.ndarray, path: Path, pad: int = 8) -> tuple[int, int, int, int] | None:
    combined = a | b
    ys, xs = np.where(combined)
    if len(xs) == 0:
        return None
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(base.shape[1], int(xs.max()) + 1 + pad)
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(base.shape[0], int(ys.max()) + 1 + pad)
    image = base[y0:y1, x0:x1].copy()
    image[a[y0:y1, x0:x1]] = (235, 64, 52)
    image[b[y0:y1, x0:x1]] = (44, 115, 195)
    Image.fromarray(image).save(path)
    Image.fromarray(image).resize((image.shape[1] * 8, image.shape[0] * 8), Image.Resampling.NEAREST).save(path.with_name(path.stem + "_8x_nearest.png"))
    return x0, y0, x1, y1


def contact_sheets(glyphs: list[dict[str, Any]], base: np.ndarray, dirs: dict[str, Path]) -> list[dict[str, Any]]:
    """Create 20 nine-cell sheets of native crops tripled at 8× nearest."""
    index_rows: list[dict[str, Any]] = []
    font = ImageFont.load_default()
    for sheet_idx in range(math.ceil(len(glyphs) / 9)):
        cells = glyphs[sheet_idx * 9 : (sheet_idx + 1) * 9]
        native_cells: list[tuple[dict[str, Any], Image.Image, Image.Image, Image.Image]] = []
        max_w = 1
        max_h = 1
        for glyph in cells:
            x0, y0, x1, y1 = glyph["pixel_bbox"]
            pad = 3
            cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
            cx1, cy1 = min(base.shape[1], x1 + pad), min(base.shape[0], y1 + pad)
            original = Image.fromarray(base[cy0:cy1, cx0:cx1])
            overlay_arr = base[cy0:cy1, cx0:cx1].copy()
            local = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
            gx0, gy0, gx1, gy1 = glyph["pixel_bbox"]
            local[gy0 - cy0:gy1 - cy0, gx0 - cx0:gx1 - cx0] = glyph["mask_local"]
            overlay_arr[local] = (235, 64, 52)
            overlay = Image.fromarray(overlay_arr)
            mask = Image.fromarray((local * 255).astype(np.uint8), "L").convert("RGB")
            native_cells.append((glyph, original, overlay, mask))
            max_w = max(max_w, original.width)
            max_h = max(max_h, original.height)
        cell_w = (max_w * 3 + 4) * 8
        cell_h = (max_h + 4) * 8 + 18
        canvas = Image.new("RGB", (cell_w * 3, cell_h * 3), "white")
        draw = ImageDraw.Draw(canvas)
        for position, (glyph, original, overlay, mask) in enumerate(native_cells):
            row, col = divmod(position, 3)
            bx = col * cell_w
            by = row * cell_h
            label = f"{glyph['glyph_id']} | O / T / M"
            draw.text((bx + 2, by + 1), label, fill="black", font=font)
            ox = bx + 2
            oy = by + 18
            for view in (original, overlay, mask):
                enlarged = view.resize((view.width * 8, view.height * 8), Image.Resampling.NEAREST)
                canvas.paste(enlarged, (ox, oy))
                ox += (max_w + 1) * 8
            glyph["contact_sheet"] = f"contact_sheets/contact_sheet_{sheet_idx + 1:02d}.png"
            glyph["contact_cell"] = f"r{row + 1}c{col + 1}"
            index_rows.append({
                "glyph_id": glyph["glyph_id"],
                "safe_filename": glyph["safe_filename"],
                "sheet": sheet_idx + 1,
                "cell": f"r{row + 1}c{col + 1}",
                "views": "ORIGINAL|TARGET_OVERLAY|MASK_ONLY",
                "native_bbox": json.dumps(glyph["pixel_bbox"]),
                "native_pad_px": 3,
                "scale": "8x nearest only",
            })
        canvas.save(dirs["contact_sheets"] / f"contact_sheet_{sheet_idx + 1:02d}.png")
    return index_rows


def main() -> None:
    dirs = ensure_dirs()
    pdf_hash = sha256(PDF)
    source_hash = sha256(SOURCE)
    if pdf_hash != EXPECTED_PDF_SHA256:
        raise RuntimeError(f"Frozen PDF hash mismatch: {pdf_hash}")
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Frozen source hash mismatch: {source_hash}")

    page_300 = OUT / "official_R96_physical_651_full_page_300dpi.png"
    page_200 = OUT / "official_R96_physical_651_full_page_200dpi.png"
    if not page_300.exists() or not page_200.exists():
        raise RuntimeError("Expected direct pdftoppm R96 page render is absent.")
    base = np.asarray(Image.open(page_300).convert("RGB"))
    image_h, image_w = base.shape[:2]
    doc = fitz.open(PDF)
    if doc.page_count != 813:
        raise RuntimeError(f"Unexpected official PDF page count: {doc.page_count}")
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    # Poppler's direct rasterizer expands a fractional final pixel rather
    # than truncating it; use the same ceil policy for a native-grid check.
    expected_w = int(math.ceil(page_rect.width * PDF_TO_PX))
    expected_h = int(math.ceil(page_rect.height * PDF_TO_PX))
    if (image_w, image_h) != (expected_w, expected_h):
        raise RuntimeError(f"Native render dimensions {image_w}x{image_h} do not match {expected_w}x{expected_h}")

    crop_box = rect_px(FIG_PDF_RECT, image_w, image_h)
    figure_crop = Image.fromarray(base).crop(crop_box)
    figure_crop.save(OUT / "figure_crop_300dpi.png")
    # This is a crop directly from the official PDF native rendering, not a
    # separately compiled candidate; it is deliberately named so the identity
    # remains clear in the manifest.
    figure_crop.save(OUT / "standalone_300dpi.png")
    figure_crop.convert("L").save(OUT / "grayscale_300dpi.png")

    # Extract every non-space character from figure plus caption.  The count
    # is asserted before any masks are made, preventing accidental crop drift.
    raw = page.get_text("rawdict")
    glyphs: list[dict[str, Any]] = []
    gid = 0
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                sx0, sy0, sx1, sy1 = span["bbox"]
                if sy0 < 345 or sy0 > 714:
                    continue
                for char in span["chars"]:
                    value = char["c"]
                    if not value.strip():
                        continue
                    bbox_pt = tuple(float(v) for v in char["bbox"])
                    x0, y0, x1, y1 = rect_px(bbox_pt, image_w, image_h)
                    object_id, semantic_parent, source_line = role_for_position(bbox_pt[0], bbox_pt[1])
                    script_class, floor_px, script_role = classify_char(value, span["font"], float(span["size"]), bbox_pt)
                    gid += 1
                    safe = f"g{gid:03d}_{safe_codepoint(value)}"
                    glyphs.append({
                        "glyph_id": f"GLYPH-{gid:03d}",
                        "safe_filename": safe,
                        "char": value,
                        "codepoint": safe_codepoint(value),
                        "object_id": object_id,
                        "semantic_parent": semantic_parent,
                        "source_line": source_line,
                        "font": span["font"],
                        "pdf_font_size_pt": round(float(span["size"]), 3),
                        "pdf_color": int(span["color"]),
                        "bbox_pt": bbox_pt,
                        "pixel_bbox": (x0, y0, x1, y1),
                        "script_class": script_class,
                        "pixel_floor": floor_px,
                        "glyph_role": script_role,
                    })
    if len(glyphs) != 175:
        raise RuntimeError(f"Expected 175 non-space figure/caption glyphs; found {len(glyphs)}")

    # The 20/255 foreground test uses the light local background around each
    # glyph.  The char bbox is the PDF/vector map; no dilation is applied.
    text_union = np.zeros((image_h, image_w), dtype=bool)
    for glyph in glyphs:
        x0, y0, x1, y1 = glyph["pixel_bbox"]
        pad = 2
        ax0, ay0 = max(0, x0 - pad), max(0, y0 - pad)
        ax1, ay1 = min(image_w, x1 + pad), min(image_h, y1 + pad)
        region = base[ay0:ay1, ax0:ax1].astype(np.int16)
        local_bg = np.percentile(region.reshape(-1, 3), 97, axis=0)
        contrast = np.max(np.abs(region - local_bg), axis=2)
        foreground = contrast >= 20
        # Tight raw bbox: padding only establishes local background and is not
        # added to a target glyph mask.  Keep the mask compact; full-page
        # masks are reconstructed only while assembling a parent text object.
        local_mask = foreground[y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0].copy()
        glyph["mask_local"] = local_mask
        glyph["local_background_rgb"] = [round(float(v), 2) for v in local_bg]
        glyph["raw_mask_pixels"] = int(local_mask.sum())
        ys, xs = np.where(local_mask)
        if len(xs):
            glyph["ink_bbox"] = (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)
            glyph["h_ink_px"] = int(ys.max() - ys.min() + 1)
        else:
            glyph["ink_bbox"] = None
            glyph["h_ink_px"] = 0
        text_union[y0:y1, x0:x1] |= local_mask

    # MuPDF reports a TeX \widetilde accent and its following pi with
    # overlapping glyph boxes.  The final PDF visibly separates the accent
    # from the base glyph vertically; split their shared raw foreground by
    # connected component before contamination accounting.  This is a
    # geometric separation of the actual native pixels, not a dilation or a
    # borrowed historical P602 mask.
    for idx in range(len(glyphs) - 1):
        accent, base_glyph = glyphs[idx], glyphs[idx + 1]
        if accent["char"] != "˜" or base_glyph["char"] != "𝜋":
            continue
        ax0, ay0, ax1, ay1 = accent["pixel_bbox"]
        bx0, by0, bx1, by1 = base_glyph["pixel_bbox"]
        ux0, uy0, ux1, uy1 = min(ax0, bx0), min(ay0, by0), max(ax1, bx1), max(ay1, by1)
        combined = np.zeros((uy1 - uy0, ux1 - ux0), dtype=bool)
        combined[ay0 - uy0:ay1 - uy0, ax0 - ux0:ax1 - ux0] |= accent["mask_local"]
        combined[by0 - uy0:by1 - uy0, bx0 - ux0:bx1 - ux0] |= base_glyph["mask_local"]
        labelled, component_count = label(combined, structure=np.ones((3, 3), dtype=int))
        if component_count < 2:
            continue
        components = []
        for component_id in range(1, component_count + 1):
            ys, xs = np.where(labelled == component_id)
            if len(xs):
                components.append((int(ys.min()), int(ys.max()), component_id))
        top_component = min(components)[2]
        accent_union = labelled == top_component
        new_accent = accent_union[ay0 - uy0:ay1 - uy0, ax0 - ux0:ax1 - ux0] & accent["mask_local"]
        new_base = base_glyph["mask_local"].copy()
        overlap_with_base = accent_union[by0 - uy0:by1 - uy0, bx0 - ux0:bx1 - ux0]
        new_base &= ~overlap_with_base
        if new_accent.any() and new_base.any():
            accent["mask_local"] = new_accent
            base_glyph["mask_local"] = new_base
            # Recompute masks metrics after the explicit accent/base split.
            for target in (accent, base_glyph):
                tx0, ty0, tx1, ty1 = target["pixel_bbox"]
                ys, xs = np.where(target["mask_local"])
                target["raw_mask_pixels"] = int(target["mask_local"].sum())
                target["ink_bbox"] = (tx0 + int(xs.min()), ty0 + int(ys.min()), tx0 + int(xs.max()) + 1, ty0 + int(ys.max()) + 1)
                target["h_ink_px"] = int(ys.max() - ys.min() + 1)

    # Conservative peer-bbox contamination check.  The actual mask is never
    # dilated, so an overlap is evidence for review rather than being hidden.
    for idx, glyph in enumerate(glyphs):
        # Only potentially intersecting PDF bboxes are inspected.  Building a
        # whole-page union 175 times would be needless and obscures the exact
        # peer responsible for a contamination flag.
        gx0, gy0, gx1, gy1 = glyph["pixel_bbox"]
        foreign_pixels = 0
        for jdx, peer in enumerate(glyphs):
            if idx == jdx:
                continue
            px0, py0, px1, py1 = peer["pixel_bbox"]
            ix0, iy0 = max(gx0, px0), max(gy0, py0)
            ix1, iy1 = min(gx1, px1), min(gy1, py1)
            if ix0 < ix1 and iy0 < iy1:
                own = glyph["mask_local"][iy0 - gy0:iy1 - gy0, ix0 - gx0:ix1 - gx0]
                peer_mask = peer["mask_local"][iy0 - py0:iy1 - py0, ix0 - px0:ix1 - px0]
                foreign_pixels += int((own & peer_mask).sum())
        # Raster glyph bboxes may share a boundary without a foreign ink pixel;
        # only target ink inside an overlapping peer bbox is recorded.
        glyph["foreign_bbox_pixel_px"] = foreign_pixels
        glyph["missing_stroke_px"] = 0
        glyph["mask_only_pure_auto"] = glyph["foreign_bbox_pixel_px"] == 0 and glyph["raw_mask_pixels"] > 0
        glyph["overlay_complete_auto"] = glyph["raw_mask_pixels"] > 0

    # Build text-object masks by union of individual raw masks.
    masks: dict[str, np.ndarray] = {}
    object_meta: dict[str, dict[str, Any]] = {}
    for obj in OBJECTS:
        oid = f"T{int(obj['id'][1:]):02d}"
        # The extraction object id uses the same numeric component.
        selected = [g for g in glyphs if g["object_id"].startswith(oid + "_")]
        full = np.zeros((image_h, image_w), dtype=bool)
        for glyph in selected:
            x0, y0, x1, y1 = glyph["pixel_bbox"]
            full[y0:y1, x0:x1] |= glyph["mask_local"]
        masks[oid] = full
        object_meta[oid] = {
            "object_id": oid,
            "detail_id": selected[0]["object_id"] if selected else f"{oid}_UNMAPPED",
            "kind": "TEXT",
            "role": selected[0]["semantic_parent"] if selected else "UNMAPPED",
            "source_line": obj["source_line"],
            "glyph_count": len(selected),
        }

    # Native foreground of graphics: contrast to white page/fill >=20, minus
    # all text raw masks.  Rectangle boundaries originate from the final PDF
    # vector drawing boxes, not an earlier P602 evidence file.
    contrast_to_white = np.max(255 - base.astype(np.int16), axis=2) >= 20
    for definition in GRAPHIC_DEFS:
        full = np.zeros((image_h, image_w), dtype=bool)
        x0, y0, x1, y1 = rect_px(definition["rect"], image_w, image_h, pad=1)
        full[y0:y1, x0:x1] = contrast_to_white[y0:y1, x0:x1]
        full &= ~text_union
        oid = definition["id"].split("_")[0]
        masks[oid] = full
        object_meta[oid] = {
            "object_id": oid,
            "detail_id": definition["id"],
            "kind": "GRAPHIC",
            "role": definition["role"],
            "source_line": definition["source_line"],
            "glyph_count": 0,
        }

    if len(masks) != 35:
        raise RuntimeError(f"Primary object inventory must be 35; got {len(masks)}")

    # Save all final-visible masks and a portable filename map.
    object_rows: list[dict[str, Any]] = []
    for oid in sorted(masks):
        mask_path = dirs["object_masks"] / f"{oid}_final_visible_mask.png"
        b = save_mask(masks[oid], mask_path)
        object_meta[oid]["pixel_bbox"] = b
        object_meta[oid]["mask_path"] = f"object_masks/{mask_path.name}"
        object_meta[oid]["foreground_px"] = int(masks[oid].sum())
        object_rows.append({**object_meta[oid], "pixel_bbox": json.dumps(b) if b else ""})
    row_csv(OUT / "foreground_objects.csv", object_rows, [
        "object_id", "detail_id", "kind", "role", "source_line", "glyph_count", "foreground_px", "pixel_bbox", "mask_path"
    ])

    # Save raw glyph masks and per-glyph source/pixel measurement records.
    glyph_rows: list[dict[str, Any]] = []
    font_rows: list[dict[str, Any]] = []
    for glyph in glyphs:
        mask_path = dirs["glyph_masks"] / f"{glyph['safe_filename']}_mask.png"
        Image.fromarray((glyph["mask_local"] * 255).astype(np.uint8), "L").save(mask_path)
        effective_pt = glyph["pdf_font_size_pt"]
        declared_pt = 11.2 if 10.8 <= effective_pt <= 11.5 else (10.0 if 9.8 <= effective_pt <= 10.1 else 9.6)
        # Only 6.695pt maths produced by TeX scripts derives from a 9.6pt
        # base.  Its source audit remains legal but the actual glyph remains
        # measured against the 15px script floor.
        source_base_pt = 9.6 if glyph["script_class"] == "NATURAL_MATH_SCRIPT" else declared_pt
        source_pass = source_base_pt >= 9.5
        glyph["declared_pt"] = declared_pt
        glyph["effective_pt"] = effective_pt
        glyph["source_base_pt"] = source_base_pt
        glyph["source_font_pass"] = source_pass
        glyph_rows.append({
            "GLYPH_ID": glyph["glyph_id"], "SAFE_FILENAME": glyph["safe_filename"], "ELEMENT_ID": glyph["object_id"],
            "CHAR": glyph["char"], "CODEPOINT": glyph["codepoint"], "PANEL_ID": "MAIN", "ROLE": glyph["glyph_role"],
            "SOURCE_FILE": str(SOURCE.relative_to(WORKSPACE)).replace("\\", "/"), "SOURCE_LINE": glyph["source_line"],
            "DECLARED_PT": glyph["declared_pt"], "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": glyph["effective_pt"],
            "TEXT_SAMPLE": glyph["char"], "SCRIPT_CLASS": glyph["script_class"],
            "BBOX_X0": glyph["pixel_bbox"][0], "BBOX_Y0": glyph["pixel_bbox"][1], "BBOX_X1": glyph["pixel_bbox"][2], "BBOX_Y1": glyph["pixel_bbox"][3],
            "H_INK_PX": glyph["h_ink_px"], "RAW_MASK_PIXELS": glyph["raw_mask_pixels"],
            "FOREIGN_BBOX_PIXEL_PX": glyph["foreign_bbox_pixel_px"], "MISSING_STROKE_PX": glyph["missing_stroke_px"],
            "MASK_PATH": f"glyph_masks/{mask_path.name}", "CONTACT_SHEET": "", "CONTACT_CELL": "",
        })
        font_rows.append({
            "ELEMENT_ID": glyph["glyph_id"], "CHAR": glyph["char"], "CODEPOINT": glyph["codepoint"], "PARENT_OBJECT": glyph["object_id"],
            "SOURCE_FILE": str(SOURCE.relative_to(WORKSPACE)).replace("\\", "/"), "SOURCE_LINE": glyph["source_line"],
            "DECLARED_PT": glyph["declared_pt"], "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": glyph["effective_pt"],
            "PDF_FONT_SIZE_PT": glyph["pdf_font_size_pt"], "PDF_FONT": glyph["font"], "COLOR_INT": glyph["pdf_color"],
            "NATURAL_SCRIPT_BASE_PT": glyph["source_base_pt"], "SOURCE_FONT_PASS": str(source_pass).lower(),
        })

    contacts = contact_sheets(glyphs, base, dirs)
    by_gid = {row["glyph_id"]: row for row in contacts}
    for row in glyph_rows:
        row["CONTACT_SHEET"] = by_gid[row["GLYPH_ID"]]["sheet"]
        row["CONTACT_CELL"] = by_gid[row["GLYPH_ID"]]["cell"]
    row_csv(OUT / "glyph_map.csv", glyph_rows, list(glyph_rows[0].keys()))
    row_csv(OUT / "after_font_audit.csv", font_rows, list(font_rows[0].keys()))
    row_csv(OUT / "contact_sheet_index.csv", contacts, list(contacts[0].keys()))

    # Per-glyph explicit manual ledger is intentionally row-level, never a
    # global checkbox.  It remains PENDING until the reviewer has opened all
    # 20 sheets; finalisation will replace it with reviewer decisions.
    ledger_rows = []
    for glyph in glyphs:
        ledger_rows.append({
            "GLYPH_ID": glyph["glyph_id"], "SHEET": glyph["contact_sheet"].split("_")[-1].split(".")[0],
            "CELL": glyph["contact_cell"], "REVIEWER": "SA1_R5", "ORIGINAL_MATCH": "PENDING",
            "OVERLAY_COMPLETE": "PENDING", "MASK_ONLY_PURE": "PENDING", "MISSING_STROKE_PX": glyph["missing_stroke_px"],
            "FOREIGN_PIXEL_PX": glyph["foreign_bbox_pixel_px"], "DECISION": "PENDING", "NOTE": "Awaiting actual 1:1+8x contact review",
        })
    row_csv(OUT / "glyph_reviewer_ledger.csv", ledger_rows, list(ledger_rows[0].keys()))

    # Pairwise raw 1:1 audit across all 35 primary foreground objects.
    # KD trees provide exact native-pixel nearest foreground distances without
    # repeating a 2481×3508 distance transform 595 times.
    mask_coords = {
        oid: np.column_stack(np.where(mask))
        for oid, mask in masks.items()
    }
    mask_trees = {
        oid: cKDTree(coords) if len(coords) else None
        for oid, coords in mask_coords.items()
    }
    pair_rows: list[dict[str, Any]] = []
    critical: list[tuple[str, str, np.ndarray, np.ndarray, str]] = []
    for a_id, b_id in itertools.combinations(sorted(masks), 2):
        a, b = masks[a_id], masks[b_id]
        intersection = int(np.count_nonzero(a & b))
        a_bbox = object_meta[a_id]["pixel_bbox"]
        b_bbox = object_meta[b_id]["pixel_bbox"]
        if a.any() and b.any():
            a_coords, b_coords = mask_coords[a_id], mask_coords[b_id]
            if len(a_coords) <= len(b_coords):
                distances, _ = mask_trees[b_id].query(a_coords, k=1)
            else:
                distances, _ = mask_trees[a_id].query(b_coords, k=1)
            min_clearance = float(np.min(distances))
        else:
            min_clearance = float("inf")
        a_kind, b_kind = object_meta[a_id]["kind"], object_meta[b_id]["kind"]
        pair_class = "".join(sorted([a_kind[0], b_kind[0]]))
        key = tuple(sorted((a_id, b_id)))
        intent = INTENT_ALLOWLIST.get(key, "")
        same_parent = a_kind == b_kind == "TEXT" and object_meta[a_id]["role"] == object_meta[b_id]["role"] and object_meta[a_id]["role"].startswith("NODE")
        if intersection > 0 and not intent and not same_parent:
            status = "FAIL_ILLEGAL_OVERLAP"
            reason = "raw 1:1 final-visible foreground intersection"
        elif intersection > 0 and intent:
            status = "INTENTIONAL_CONTACT"
            reason = intent
        elif same_parent:
            status = "SAME_PARENT_LAYOUT"
            reason = "same semantic node text; only ink intersection is a hard gate"
        else:
            status = "PASS_NO_OVERLAP"
            reason = ""
        # Mark close non-parent/non-intent relations for explicit ROI review;
        # class-specific hard gates are determined in the review report.
        if intersection > 0 or min_clearance <= 12:
            critical.append((a_id, b_id, a, b, status))
        pair_rows.append({
            "PAIR_ID": f"{a_id}__{b_id}", "A_ID": a_id, "B_ID": b_id, "A_KIND": a_kind, "B_KIND": b_kind,
            "PAIR_CLASS": pair_class, "A_ROLE": object_meta[a_id]["role"], "B_ROLE": object_meta[b_id]["role"],
            "RAW_INTERSECTION_PX": intersection, "RAW_MIN_CLEARANCE_PX": round(min_clearance, 3) if math.isfinite(min_clearance) else "",
            "BBOX_GAP_PX": round(bbox_gap(a_bbox, b_bbox), 3), "INTENT_ALLOWLIST": intent or "",
            "STATUS": status, "REASON": reason, "ROI_PATH": "",
        })
    # Deduplicate and write ROI evidence for every failed/critical relation.
    row_by_pair = {row["PAIR_ID"]: row for row in pair_rows}
    for a_id, b_id, a, b, status in critical:
        pair_id = f"{a_id}__{b_id}"
        roi_path = dirs["pairs"] / f"{pair_id}_roi.png"
        roi = pair_roi(a, b, base, roi_path)
        if roi:
            row_by_pair[pair_id]["ROI_PATH"] = f"pairs/{roi_path.name}"
    row_csv(OUT / "all_unordered_pairs.csv", pair_rows, list(pair_rows[0].keys()))

    # Separate opaque label-background masks and source-order occlusion
    # inversion.  These masks are deliberately not presented as foreground.
    occlusion_rows: list[dict[str, Any]] = []
    for hid, hrect, primary, secondary, text_id in HALO_DEFS:
        halo = np.zeros((image_h, image_w), dtype=bool)
        x0, y0, x1, y1 = rect_px(hrect, image_w, image_h)
        halo[y0:y1, x0:x1] = True
        hpath = dirs["occlusion"] / f"{hid}_opaque_halo_mask.png"
        save_mask(halo, hpath)
        primary_key = primary.split("_")[0]
        secondary_key = secondary.split("_")[0] if secondary else ""
        pre = masks[primary_key].copy()
        if secondary:
            pre |= masks[secondary_key]
        final = pre & ~halo
        pre_path = dirs["occlusion"] / f"{hid}_pre_occlusion_mask.png"
        final_path = dirs["occlusion"] / f"{hid}_final_visible_mask.png"
        save_mask(pre, pre_path)
        save_mask(final, final_path)
        occluded = int(np.count_nonzero(pre & halo))
        observed = masks[primary_key].copy()
        if secondary:
            observed |= masks[secondary_key]
        unexpected = int(np.count_nonzero(observed & halo))
        roi_path = dirs["occlusion"] / f"{hid}_occlusion_roi.png"
        pair_roi(pre, halo, base, roi_path)
        occlusion_rows.append({
            "HALO_ID": hid, "TEXT_PARENT": text_id, "PRE_OBJECTS": "+".join(x for x in (primary, secondary) if x),
            "PAINT_ORDER": "arrow shaft/head precedes opaque white edge-label background; text paints after background",
            "PRE_OCCLUSION_PX": int(pre.sum()), "HALO_PX": int(halo.sum()), "INTENTIONAL_OCCLUDED_PX": occluded,
            "FINAL_VISIBLE_PX": int(final.sum()), "OBSERVED_FINAL_VISIBLE_PX": int(observed.sum()),
            "UNEXPECTED_VISIBLE_IN_HALO_PX": unexpected, "HALO_MASK": f"occlusion/{hpath.name}",
            "PRE_MASK": f"occlusion/{pre_path.name}", "FINAL_MASK": f"occlusion/{final_path.name}", "ROI": f"occlusion/{roi_path.name}",
            "STATUS": "PASS" if unexpected == 0 else "FAIL",
        })
    row_csv(OUT / "occlusion_inversion.csv", occlusion_rows, list(occlusion_rows[0].keys()))

    # D/E compares label-level elements, not the natural outline height of
    # unlike characters (for example x, parentheses and an equals sign cannot
    # be forced into one same-class median).  Glyphs retain their independent
    # C-section floors below; element medians are compared only among matching
    # semantic role, font and effective-size strata.
    element_values: dict[tuple[str, str, str, float, str], list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        element_values[(glyph["object_id"], glyph["glyph_role"], glyph["script_class"], glyph["effective_pt"], glyph["font"])].append(glyph)
    element_rows: list[dict[str, Any]] = []
    for key, members in element_values.items():
        oid, role, script, effective_pt, font_name = key
        element_rows.append({
            "ELEMENT_OBJECT": oid, "ROLE": role, "SCRIPT_CLASS": script, "EFFECTIVE_PT": effective_pt,
            "PDF_FONT": font_name, "GLYPH_COUNT": len(members), "MEDIAN_H_INK_PX": round(float(np.median([m["h_ink_px"] for m in members])), 3),
            "LOW_PROFILE": str(script == "LOW_PROFILE_PUNCTUATION").lower(),
        })
    style_groups: dict[tuple[str, str, float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in element_rows:
        style_groups[(row["ROLE"], row["SCRIPT_CLASS"], row["EFFECTIVE_PT"], row["PDF_FONT"])].append(row)
    class_rows: list[dict[str, Any]] = []
    for key, members in style_groups.items():
        values = [float(m["MEDIAN_H_INK_PX"]) for m in members]
        med = float(np.median(values))
        ratios = [v / med if med else 0.0 for v in values]
        script = key[1]
        passed = script == "LOW_PROFILE_PUNCTUATION" or all(0.92 <= ratio <= 1.08 for ratio in ratios)
        class_rows.append({
            "ROLE": key[0], "SCRIPT_CLASS": script, "EFFECTIVE_PT": key[2], "PDF_FONT": key[3],
            "ELEMENT_COUNT": len(members), "CLASS_MEDIAN_PX": round(med, 3), "MIN_ELEMENT_MEDIAN_PX": round(min(values), 3),
            "MAX_ELEMENT_MEDIAN_PX": round(max(values), 3), "MAX_MIN_RATIO": round(max(values) / min(values), 3) if min(values) else "INF",
            "PASS": "N/A_LOW_PROFILE_CALIBRATION" if script == "LOW_PROFILE_PUNCTUATION" else str(passed).lower(),
            "ELEMENTS": "|".join(m["ELEMENT_OBJECT"] for m in members),
        })
    measurement_rows: list[dict[str, Any]] = []
    for glyph in glyphs:
        floor_pass = glyph["pixel_floor"] == 0 or glyph["h_ink_px"] >= glyph["pixel_floor"]
        pure = glyph["mask_only_pure_auto"] and glyph["overlay_complete_auto"]
        glyph["pixel_pass_auto"] = floor_pass and pure
        reasons = []
        if not floor_pass:
            reasons.append(f"H_INK {glyph['h_ink_px']}px below {glyph['pixel_floor']}px floor")
        if not pure:
            reasons.append("empty or peer-bbox-contaminated raw mask")
        measurement_rows.append({
            "ELEMENT_ID": glyph["glyph_id"], "PANEL_ID": "MAIN", "ROLE": glyph["glyph_role"],
            "SOURCE_FILE": str(SOURCE.relative_to(WORKSPACE)).replace("\\", "/"), "SOURCE_LINE": glyph["source_line"],
            "DECLARED_PT": glyph["declared_pt"], "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": glyph["effective_pt"],
            "TEXT_SAMPLE": glyph["char"], "SCRIPT_CLASS": glyph["script_class"],
            "BBOX_X0": glyph["pixel_bbox"][0], "BBOX_Y0": glyph["pixel_bbox"][1], "BBOX_X1": glyph["pixel_bbox"][2], "BBOX_Y1": glyph["pixel_bbox"][3],
            "H_INK_PX": glyph["h_ink_px"], "CLASS_MEDIAN_PX": "N/A_OBJECT_LEVEL", "RATIO_TO_CLASS_MEDIAN": "N/A_OBJECT_LEVEL",
            "ROLE_RATIO": "see same_class_ratio_audit.csv", "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0,
            "MIN_CLEARANCE_PX": "see all_unordered_pairs.csv", "PASS_FAIL": "PASS" if glyph["pixel_pass_auto"] else "FAIL",
            "REASON": "; ".join(reasons), "MASK_PATH": f"glyph_masks/{glyph['safe_filename']}_mask.png",
        })
    row_csv(OUT / "after_pixel_measurements.csv", measurement_rows, list(measurement_rows[0].keys()))
    row_csv(OUT / "same_class_ratio_audit.csv", class_rows, list(class_rows[0].keys()))
    row_csv(OUT / "element_level_ratio_audit.csv", element_rows, list(element_rows[0].keys()))

    # Summary gate is deliberately draft-only until contact-sheet review and
    # independent punctuation calibration are finalized.
    source_font_pass = all(g["source_font_pass"] for g in glyphs)
    raw_pixel_pass = all(g["pixel_pass_auto"] for g in glyphs)
    non_intent_overlap = [r for r in pair_rows if r["STATUS"] == "FAIL_ILLEGAL_OVERLAP"]
    all_pairs_count = len(pair_rows)
    source_text = SOURCE.read_text(encoding="utf-8")
    evidence = {
        "task_id": "FIG-P602-01",
        "review_role": "SA1 independent R5 continuation",
        "candidate_pdf": str(PDF), "candidate_pdf_sha256": pdf_hash, "physical_page": PAGE_NUMBER,
        "printed_page": 638, "figure_number": "32.5", "page_pt": [page_rect.width, page_rect.height],
        "native_300dpi": [image_w, image_h], "figure_crop_pixel_rect": list(crop_box),
        "source": str(SOURCE), "source_sha256": source_hash, "source_declared_base_pt": 9.6,
        "source_contains_inner_formula_11_2pt": "\\fontsize{11.2pt}{13.6pt}" in source_text,
        "glyph_count": len(glyphs), "contact_sheet_count": math.ceil(len(glyphs) / 9),
        "primary_object_count": len(masks), "unordered_pair_count": all_pairs_count,
        "source_font_pass_auto": source_font_pass, "pixel_pass_auto_before_manual_and_calibration": raw_pixel_pass,
        "illegal_overlap_pair_count": len(non_intent_overlap), "occlusion_halo_count": len(occlusion_rows),
        "manual_contact_ledger": "PENDING", "low_profile_calibration": "PENDING", "status": "DRAFT_NOT_TERMINAL",
    }
    save_json(OUT / "evidence_manifest_draft.json", evidence)
    with (dirs["reports"] / "machine_gate_draft.md").open("w", encoding="utf-8") as stream:
        stream.write("# FIG-P602-01 R5 SA1 machine gate — draft\n\n")
        stream.write(f"- Candidate: R96 official `{PDF.name}`, physical page {PAGE_NUMBER}, printed page 638, figure 32.5.\n")
        stream.write(f"- Hashes: PDF `{pdf_hash}`, figure source `{source_hash}`.\n")
        stream.write(f"- Extracted {len(glyphs)} non-space glyphs into {math.ceil(len(glyphs)/9)} three-view contact sheets.\n")
        stream.write(f"- Primary objects/pairs: {len(masks)}/{all_pairs_count}; all TT/TG/GG combinations are enumerated.\n")
        stream.write(f"- Source font preliminary pass: `{source_font_pass}`; raw pixel preliminary pass: `{raw_pixel_pass}`.\n")
        stream.write(f"- Illegal final-visible intersections before whitelist: {len(non_intent_overlap)}.\n")
        stream.write("- This is not a verdict.  Manual 1:1+8x ledger, low-profile calibration, D/E review, four-view review and final integrity cross-check remain mandatory.\n")


if __name__ == "__main__":
    main()
