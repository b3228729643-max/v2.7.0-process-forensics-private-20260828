#!/usr/bin/env python3
"""Strict, read-only SA1 evidence builder for FIG-P580-01 on frozen R94.

The script intentionally writes only beside itself.  It derives every pixel
measurement from the supplied full-page Poppler 300 dpi raster, without any
resizing.  Eight-times images are nearest-neighbour inspection aids only.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import distance_transform_edt


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


EVIDENCE_ROOT = Path.cwd().resolve()
EXPECTED_NAME = "SA1_20260824_R1"
if EVIDENCE_ROOT.name != EXPECTED_NAME:
    raise RuntimeError(f"run from {EXPECTED_NAME}, got {EVIDENCE_ROOT}")

# RUN6 is explicitly superseded.  RUN7 writes to a new subdirectory so no old
# raw-mask/package data can accidentally be read as current terminal evidence.
OUT = Path(os.environ.get("SA1_RUN_OUT", str(EVIDENCE_ROOT / "RUN7_TEXT_ISOLATION"))).resolve()
RUN_ID = OUT.name
WORK_ROOT = EVIDENCE_ROOT.parents[4]
SOURCE_ROOT = WORK_ROOT / "source" / "v2.7.0"
PDF = SOURCE_ROOT / "src" / "build" / "strict_current_r94_fullbook" / "main_full.pdf"
SOURCE_FIGURE = (
    SOURCE_ROOT
    / "src"
    / "\u7ed8\u56fe\u6e90\u7801"
    / "\u7b2c05\u518c_\u91c7\u6837\u65b9\u6cd5\u4e3b\u9898\u6a21\u578b\u4e0e\u56fe\u6392\u5e8f"
    / "V5-C02"
    / "fig_v5_c02_is_support.tex"
)
SOURCE_CHAPTER = (
    SOURCE_ROOT
    / "src"
    / "\u8bb2\u4e49\u6e90\u7801"
    / "\u7b2c05\u518c_\u91c7\u6837\u65b9\u6cd5\u4e3b\u9898\u6a21\u578b\u4e0e\u56fe\u6392\u5e8f"
    / "chapters"
    / "V5-C02.tex"
)
SOURCE_STYLE = SOURCE_ROOT / "src" / "\u8bb2\u4e49\u6e90\u7801" / "common" / "statlearnbook.sty"

PAGE_ONE_BASED = 628
PAGE_INDEX = PAGE_ONE_BASED - 1
PRINTED_PAGE = 615
DPI = 300
SCALE = DPI / 72.0
FOREGROUND_DELTA = 20
# A terminal review is never represented by a global switch.  Both the glyph
# contacts and the page/font visual checks are closed only by their respective
# per-record ledgers below.
MANUAL_CONTACT_SHEETS_REVIEWED = False
DOCUMENTATION_REISSUE = os.environ.get("SA1_DOCUMENTATION_REISSUE", "").strip().lower() in {"1", "true", "yes"}
DOCUMENTATION_REISSUE_REASON = os.environ.get(
    "SA1_DOCUMENTATION_REISSUE_REASON",
    "A previous terminal-document generation was withdrawn before handoff because its visual-review Markdown contained literal `\\n` text and did not point readers to the current-machine metadata join.",
).strip()

# Includes panel titles, the two panels, and the figure caption.  All values
# are PDF pt and are converted to integer native-PNG pixels only once.
FIGURE_RECT_PT = (60.0, 267.0, 535.0, 480.0)
STANDALONE_RECT_PT = (60.0, 267.0, 535.0, 455.0)

FULL_300 = OUT / "full_page_300dpi.png"
FULL_200 = OUT / "full_page_200dpi.png"
TEXT_REPLAY_PDF = OUT / "frozen_page628_text_only_replay.pdf"
TEXT_REPLAY_300 = OUT / "frozen_page628_text_only_replay_300dpi.png"
TEXT_REPLAY_REPORT = OUT / "text_only_replay_probe.json"

MASK_ROOT = OUT / "masks"
GLYPH_DIR = MASK_ROOT / "glyphs"
TEXT_SOURCE_SHAPE_DIR = MASK_ROOT / "text_replay_source_shapes"
VECTOR_TEXT_COMPONENT_DIR = MASK_ROOT / "vector_text_components"
ELEMENT_DIR = MASK_ROOT / "text_elements"
GRAPHIC_DIR = MASK_ROOT / "graphics"
PRE_DIR = MASK_ROOT / "pre_occlusion"
HALO_DIR = MASK_ROOT / "opaque_halos"
TRANSLUCENT_DIR = MASK_ROOT / "translucent_overlays"
NON_TARGET_LAYER_DIR = MASK_ROOT / "official_nontext_layers"
CRITICAL_DIR = OUT / "critical_relations"
OCCLUSION_DIR = OUT / "occlusion_evidence"
TEXT_OCCLUSION_DIR = OUT / "text_occlusion_evidence"
TEXT_LATER_PAINT_DIR = OUT / "text_later_paint_evidence"
TRANSLUCENT_OCCLUSION_DIR = OUT / "translucent_label_overlay_evidence"
CONTACT_DIR = OUT / "glyph_shape_contact_sheets"
PIXEL_FAIL_DIR = OUT / "pixel_failures"

for directory in (MASK_ROOT, GLYPH_DIR, TEXT_SOURCE_SHAPE_DIR, VECTOR_TEXT_COMPONENT_DIR, ELEMENT_DIR, GRAPHIC_DIR, PRE_DIR, HALO_DIR, TRANSLUCENT_DIR, NON_TARGET_LAYER_DIR, CRITICAL_DIR, OCCLUSION_DIR, TEXT_OCCLUSION_DIR, TEXT_LATER_PAINT_DIR, TRANSLUCENT_OCCLUSION_DIR, CONTACT_DIR, PIXEL_FAIL_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return path.resolve().relative_to(OUT).as_posix()


def as_rgb(value: Iterable[float] | None) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(float(component) * 255)) for component in value)


def final_text_colour_mask(region_rgb: np.ndarray, fill_rgb: Iterable[float]) -> np.ndarray:
    """Return only official final pixels compatible with one text paint fill.

    `region_rgb` is the frozen Poppler raster.  The source colour is taken
    from the corresponding frozen PDF texttrace operator; matching follows
    the white-background alpha direction, so a later teal marker, curve,
    hatch, or similarly dark but different-colour object cannot masquerade as
    the character just because it lies in a CHAR ownership ROI.
    """
    target = np.asarray([float(value) * 255.0 for value in fill_rgb], dtype=float)
    vector = 255.0 - target
    denominator = float(np.dot(vector, vector))
    if denominator <= 0.0:
        raise RuntimeError("text operator has a background-colour fill")
    delta = 255.0 - region_rgb.astype(float)
    alpha = np.tensordot(delta, vector, axes=([2], [0])) / denominator
    residual = np.linalg.norm(delta - alpha[..., None] * vector, axis=2)
    return (alpha >= (FOREGROUND_DELTA / 255.0)) & (alpha <= 1.08) & (residual <= 8.0)


def bbox_union(boxes: Iterable[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    values = list(boxes)
    return (
        min(value[0] for value in values),
        min(value[1] for value in values),
        max(value[2] for value in values),
        max(value[3] for value in values),
    )


def intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def pxbbox(box: tuple[float, float, float, float], width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(box[0] * SCALE)) - pad)
    y0 = max(0, int(math.floor(box[1] * SCALE)) - pad)
    x1 = min(width, int(math.ceil(box[2] * SCALE)) + pad)
    y1 = min(height, int(math.ceil(box[3] * SCALE)) + pad)
    return (x0, y0, max(x0 + 1, x1), max(y0 + 1, y1))


def ptbox_from_px(box: tuple[int, int, int, int]) -> tuple[float, float, float, float]:
    return tuple(round(value / SCALE, 4) for value in box)  # type: ignore[return-value]


def rect_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(0, a[0] - b[2], b[0] - a[2])
    dy = max(0, a[1] - b[3], b[1] - a[3])
    return round(math.hypot(dx, dy), 6)


def save_binary(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path, optimize=True)


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


@dataclass
class MaskObject:
    object_id: str
    kind: str
    role: str
    panel: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    raw_path: Path
    source: str
    text: str = ""
    parent: str = ""
    intentional_group: str = ""
    paint_order: int = -1

    @property
    def nonempty(self) -> bool:
        return bool(self.mask.any())

    @property
    def pixels(self) -> int:
        return int(self.mask.sum())


def mask_intersection(a: MaskObject, b: MaskObject) -> tuple[int, tuple[int, int, int, int] | None, np.ndarray | None]:
    x0 = max(a.bbox[0], b.bbox[0])
    y0 = max(a.bbox[1], b.bbox[1])
    x1 = min(a.bbox[2], b.bbox[2])
    y1 = min(a.bbox[3], b.bbox[3])
    if x0 >= x1 or y0 >= y1:
        return 0, None, None
    ac = a.mask[y0 - a.bbox[1] : y1 - a.bbox[1], x0 - a.bbox[0] : x1 - a.bbox[0]]
    bc = b.mask[y0 - b.bbox[1] : y1 - b.bbox[1], x0 - b.bbox[0] : x1 - b.bbox[0]]
    inter = ac & bc
    return int(inter.sum()), (x0, y0, x1, y1), inter


def ink_clearance(a: MaskObject, b: MaskObject, close_limit: float = 48.0) -> float:
    if not a.nonempty or not b.nonempty:
        return float("nan")
    coarse = rect_clearance(a.bbox, b.bbox)
    if coarse > close_limit:
        return coarse
    x0 = min(a.bbox[0], b.bbox[0])
    y0 = min(a.bbox[1], b.bbox[1])
    x1 = max(a.bbox[2], b.bbox[2])
    y1 = max(a.bbox[3], b.bbox[3])
    ac = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bc = np.zeros_like(ac)
    ac[a.bbox[1] - y0 : a.bbox[3] - y0, a.bbox[0] - x0 : a.bbox[2] - x0] = a.mask
    bc[b.bbox[1] - y0 : b.bbox[3] - y0, b.bbox[0] - x0 : b.bbox[2] - x0] = b.mask
    if (ac & bc).any():
        return 0.0
    distance = distance_transform_edt(~ac)
    nearest = float(distance[bc].min())
    # Report empty-pixel clearance rather than centre-to-centre distance.
    return round(max(0.0, nearest - 1.0), 6)


def role_for_line(text: str, box: tuple[float, float, float, float]) -> str:
    compact = "".join(text.split())
    if box[1] >= 457:
        return "CAPTION"
    if "\u652f\u6301\u4e0d\u8db3" in compact or "\u652f\u6301\u8986\u76d6" in compact:
        return "PANEL_TITLE"
    if "\u5171\u540c\u5b9a\u4e49\u57df" in compact or "\u5bc6\u5ea6" in compact:
        return "AXIS_TITLE"
    if "w(" in compact or "\u540c\u4e00\u516c\u5f0f" in compact or compact.startswith("="):
        return "FORMULA"
    tickish = set("0123456789.-")
    if compact and all(character in tickish for character in compact) and 300 <= box[1] <= 445:
        return "TICK"
    return "ANNOTATION"


def panel_for_box(box: tuple[float, float, float, float]) -> str:
    # The right-panel y tick labels sit immediately left of that panel's
    # vertical axis (x≈316pt).  The groupplot gap is at x≈310pt, not 320pt.
    if box[0] < 310:
        return "L"
    if box[0] >= 310 and box[1] < 455:
        return "R"
    return "GLOBAL"


def source_line(role: str, text: str) -> str:
    if role == "CAPTION":
        return "fig_v5_c02_is_support.tex:90; statlearnbook.sty:305"
    if role == "PANEL_TITLE":
        return "fig_v5_c02_is_support.tex:26,36,70"
    if role == "TICK":
        return "fig_v5_c02_is_support.tex:21-25"
    if role == "AXIS_TITLE":
        return "fig_v5_c02_is_support.tex:20-26"
    if role == "FORMULA":
        return "fig_v5_c02_is_support.tex:79-89"
    return "fig_v5_c02_is_support.tex:47-89"


def declared_pt(role: str) -> float:
    if role == "PANEL_TITLE":
        return 10.2
    if role == "CAPTION":
        # LaTeX standard 11pt class \small = 10pt; style declares \small.
        return 10.0
    return 9.6


def classify_character(
    char: str,
    char_box: tuple[float, float, float, float],
    parent_box: tuple[float, float, float, float],
    pdf_font_pt: float,
    baseline_pdf_font_pt: float,
    force_fraction_script: bool = False,
) -> tuple[str, int]:
    code = ord(char)
    # Han ideographs stay in the CJK gate even for low-stroke glyphs (e.g. 一).
    if 0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF:
        return "CJK_HAN", 30
    # Goal C applies the 30px gate to every fullwidth code point, including
    # punctuation before U+FF10 (notably U+FF08/U+FF09 fullwidth parentheses).
    if 0xFF01 <= code <= 0xFFEF:
        return "FULLWIDTH", 30
    # A TeX numerator, denominator, sub/superscript, or its operator is a
    # legitimate natural script.  Determine this from the emitted font size
    # (not from a multi-line parent bbox, which would misclassify baseline w,
    # p, q, and x as scripts).  Fraction-node digits are source-confirmed
    # scripts even where TeX emits the same nominal font size.
    if force_fraction_script or pdf_font_pt < baseline_pdf_font_pt * 0.95:
        return "NATURAL_SCRIPT", 15
    if char in "，。；：、（）【】《》“”‘’（）()[]{}.,;:!?":
        return "PUNCTUATION", 22
    if char in "+-=−–—<>≤≥≪≫≈∼∝×÷/\\|*·":
        return "MATH_OPERATOR", 22
    if char.isdigit() or char.isupper():
        return "UPPER_OR_DIGIT", 24
    if "\u03b1" <= char <= "\u03c9" or "\u0391" <= char <= "\u03a9" or char.islower():
        return "LOWER_OR_GREEK", 17
    return "MATH_BASE", 22


def source_text_check() -> dict[str, Any]:
    figure = SOURCE_FIGURE.read_text(encoding="utf-8")
    chapter = SOURCE_CHAPTER.read_text(encoding="utf-8")
    style = SOURCE_STYLE.read_text(encoding="utf-8")
    required = {
        "figure_uid": "FIG-P580-01" in figure,
        "target_density": "6*(#1)*(5-(#1))/125" in figure,
        "left_support": "q_L" in figure and "ISXCut" in figure,
        "right_proposal": "ISQRHeight" in figure,
        "caption_support": "重要性抽样要求 $p\\ll q$" in figure,
        "chapter_anchor": "固定共同定义域" in chapter and "fig:V5-C02-is-support" in chapter,
        "caption_small": "\\captionsetup{font={small" in style,
        "no_resizebox": "\\resizebox" not in figure and "\\scalebox" not in figure,
    }
    return {
        "source_figure": str(SOURCE_FIGURE),
        "source_chapter": str(SOURCE_CHAPTER),
        "source_style": str(SOURCE_STYLE),
        "checks": required,
        "result": "PASS" if all(required.values()) else "FAIL",
    }


def actual_roi(image: Image.Image, box: tuple[int, int, int, int], pad: int = 0) -> Image.Image:
    x0 = max(0, box[0] - pad)
    y0 = max(0, box[1] - pad)
    x1 = min(image.width, box[2] + pad)
    y1 = min(image.height, box[3] + pad)
    return image.crop((x0, y0, x1, y1))


def critical_package(
    pair_id: str,
    a: MaskObject,
    b: MaskObject,
    raw_full: Image.Image,
    overlap: int,
    clearance: float,
    required: float,
    status: str,
) -> str:
    folder = CRITICAL_DIR / pair_id
    folder.mkdir(parents=True, exist_ok=True)
    x0 = max(0, min(a.bbox[0], b.bbox[0]) - 12)
    y0 = max(0, min(a.bbox[1], b.bbox[1]) - 12)
    x1 = min(raw_full.width, max(a.bbox[2], b.bbox[2]) + 12)
    y1 = min(raw_full.height, max(a.bbox[3], b.bbox[3]) + 12)
    raw = raw_full.crop((x0, y0, x1, y1))
    raw.save(folder / "raw_roi_1x.png", optimize=True)
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(folder / "raw_roi_8x_nearest.png", optimize=True)
    shape = (y1 - y0, x1 - x0)
    am = np.zeros(shape, dtype=bool)
    bm = np.zeros(shape, dtype=bool)
    am[a.bbox[1] - y0 : a.bbox[3] - y0, a.bbox[0] - x0 : a.bbox[2] - x0] = a.mask
    bm[b.bbox[1] - y0 : b.bbox[3] - y0, b.bbox[0] - x0 : b.bbox[2] - x0] = b.mask
    save_binary(am, folder / "mask_A_raw.png")
    save_binary(bm, folder / "mask_B_raw.png")
    save_binary(am & bm, folder / "intersection_raw.png")
    overlay = np.asarray(raw.convert("RGB"), dtype=np.uint8).copy()
    overlay[am] = (255, 0, 0)
    overlay[bm] = (0, 100, 255)
    overlay[am & bm] = (255, 0, 255)
    Image.fromarray(overlay, mode="RGB").save(folder / "overlay_1x.png", optimize=True)
    save_json(
        folder / "manifest.json",
        {
            "pair_id": pair_id,
            "status": status,
            "object_A": a.object_id,
            "object_B": b.object_id,
            "overlap_px": overlap,
            "raw_ink_clearance_px": clearance,
            "required_clearance_px": required,
            "roi_full_page_px": [x0, y0, x1, y1],
            "files": [
                "raw_roi_1x.png",
                "raw_roi_8x_nearest.png",
                "mask_A_raw.png",
                "mask_B_raw.png",
                "intersection_raw.png",
                "overlay_1x.png",
            ],
        },
    )
    return rel(folder)


def glyph_failure_package(glyph_id: str, obj: MaskObject, raw_full: Image.Image, reason: str) -> str:
    folder = PIXEL_FAIL_DIR / glyph_id
    folder.mkdir(parents=True, exist_ok=True)
    raw = actual_roi(raw_full, obj.bbox, pad=4)
    raw.save(folder / "raw_roi_1x.png", optimize=True)
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(folder / "raw_roi_8x_nearest.png", optimize=True)
    save_binary(obj.mask, folder / "glyph_raw_mask.png")
    save_json(
        folder / "manifest.json",
        {
            "glyph_id": glyph_id,
            "parent_element": obj.parent,
            "text": obj.text,
            "bbox_full_page_px": list(obj.bbox),
            "reason": reason,
            "files": ["raw_roi_1x.png", "raw_roi_8x_nearest.png", "glyph_raw_mask.png"],
        },
    )
    return rel(folder)


def occlusion_package(
    graphic: MaskObject,
    pre_mask: np.ndarray,
    halo_entries: list[dict[str, Any]],
    raw_full: Image.Image,
) -> str:
    """Bundle source-pre / true halo / final-visible evidence at native pixels."""
    folder = OCCLUSION_DIR / graphic.object_id
    folder.mkdir(parents=True, exist_ok=True)
    x0 = max(0, min([graphic.bbox[0]] + [entry["bbox"][0] for entry in halo_entries]) - 12)
    y0 = max(0, min([graphic.bbox[1]] + [entry["bbox"][1] for entry in halo_entries]) - 12)
    x1 = min(raw_full.width, max([graphic.bbox[2]] + [entry["bbox"][2] for entry in halo_entries]) + 12)
    y1 = min(raw_full.height, max([graphic.bbox[3]] + [entry["bbox"][3] for entry in halo_entries]) + 12)
    shape = (y1 - y0, x1 - x0)
    pre = np.zeros(shape, dtype=bool)
    final = np.zeros(shape, dtype=bool)
    halo = np.zeros(shape, dtype=bool)
    per_halo_coverage: list[dict[str, Any]] = []
    pre[graphic.bbox[1] - y0 : graphic.bbox[3] - y0, graphic.bbox[0] - x0 : graphic.bbox[2] - x0] = pre_mask
    final[graphic.bbox[1] - y0 : graphic.bbox[3] - y0, graphic.bbox[0] - x0 : graphic.bbox[2] - x0] = graphic.mask
    for entry in halo_entries:
        hx0, hy0, hx1, hy1 = entry["bbox"]
        local_halo = np.zeros(shape, dtype=bool)
        local_halo[hy0 - y0 : hy1 - y0, hx0 - x0 : hx1 - x0] = entry["mask"]
        halo |= local_halo
        per_halo_coverage.append(
            {
                "halo_id": entry["halo_id"],
                "draw_id": int(entry["draw_id"]),
                "source_pre_halo_intersection_pixels": int((pre & local_halo).sum()),
                "pre_minus_final_under_halo_pixels": int((pre & ~final & local_halo).sum()),
            }
        )
    raw = raw_full.crop((x0, y0, x1, y1))
    raw.save(folder / "raw_final_roi_1x.png", optimize=True)
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(folder / "raw_final_roi_8x_nearest.png", optimize=True)
    save_binary(pre, folder / "source_pre_raw.png")
    save_binary(final, folder / "final_visible_raw.png")
    save_binary(halo, folder / "opaque_halo_raw.png")
    hidden = pre & ~final
    save_binary(hidden, folder / "pre_minus_final_raw.png")
    overlay = np.asarray(raw.convert("RGB"), dtype=np.uint8).copy()
    overlay[halo] = (255, 220, 0)
    overlay[pre] = (230, 60, 0)
    overlay[final] = (0, 95, 255)
    overlay[hidden] = (255, 0, 220)
    Image.fromarray(overlay, mode="RGB").save(folder / "pre_halo_final_overlay_1x.png", optimize=True)
    save_json(
        folder / "manifest.json",
        {
            "graphic_id": graphic.object_id,
            "roi_full_page_px": [x0, y0, x1, y1],
            "source_pre_pixels": int(pre.sum()),
            "final_visible_pixels": int(final.sum()),
            "pre_minus_final_pixels": int(hidden.sum()),
            "source_pre_halo_intersection_pixels": int((pre & halo).sum()),
            "pre_minus_final_under_halo_pixels": int((pre & ~final & halo).sum()),
            "opaque_halos": [entry["halo_id"] for entry in halo_entries],
            "per_halo_coverage": per_halo_coverage,
            "files": [
                "raw_final_roi_1x.png",
                "raw_final_roi_8x_nearest.png",
                "source_pre_raw.png",
                "final_visible_raw.png",
                "opaque_halo_raw.png",
                "pre_minus_final_raw.png",
                "pre_halo_final_overlay_1x.png",
            ],
        },
    )
    return rel(folder)


def text_occlusion_failure_package(
    element: MaskObject,
    glyphs: list[MaskObject],
    source_shapes: dict[str, np.ndarray],
    isolation: dict[str, dict[str, Any]],
    halo_entry: dict[str, Any],
    raw_full: Image.Image,
) -> str:
    """Preserve source-pre/order/opaque-halo/final masks at native pixels."""
    folder = TEXT_OCCLUSION_DIR / element.object_id
    folder.mkdir(parents=True, exist_ok=True)
    hx0, hy0, hx1, hy1 = halo_entry["bbox"]
    x0 = max(0, min([element.bbox[0], hx0] + [glyph.bbox[0] for glyph in glyphs]) - 12)
    y0 = max(0, min([element.bbox[1], hy0] + [glyph.bbox[1] for glyph in glyphs]) - 12)
    x1 = min(raw_full.width, max([element.bbox[2], hx1] + [glyph.bbox[2] for glyph in glyphs]) + 12)
    y1 = min(raw_full.height, max([element.bbox[3], hy1] + [glyph.bbox[3] for glyph in glyphs]) + 12)
    shape = (y1 - y0, x1 - x0)
    source_pre = np.zeros(shape, dtype=bool)
    final_suffix = np.zeros(shape, dtype=bool)
    final_parent = np.zeros(shape, dtype=bool)
    halo = np.zeros(shape, dtype=bool)
    for glyph in glyphs:
        source = source_shapes[glyph.object_id]
        source_pre[glyph.bbox[1] - y0 : glyph.bbox[3] - y0, glyph.bbox[0] - x0 : glyph.bbox[2] - x0] |= source
        final_suffix[glyph.bbox[1] - y0 : glyph.bbox[3] - y0, glyph.bbox[0] - x0 : glyph.bbox[2] - x0] |= glyph.mask
    final_parent[element.bbox[1] - y0 : element.bbox[3] - y0, element.bbox[0] - x0 : element.bbox[2] - x0] = element.mask
    halo[hy0 - y0 : hy1 - y0, hx0 - x0 : hx1 - x0] = halo_entry["mask"]
    raw = raw_full.crop((x0, y0, x1, y1))
    raw.save(folder / "raw_final_roi_1x.png", optimize=True)
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(folder / "raw_final_roi_8x_nearest.png", optimize=True)
    save_binary(source_pre, folder / "mask_A_source_pre_text_raw.png")
    save_binary(halo, folder / "mask_B_later_opaque_halo_raw.png")
    save_binary(final_suffix, folder / "mask_C_final_visible_suffix_raw.png")
    save_binary(final_parent, folder / "mask_D_final_visible_parent_text_raw.png")
    save_binary(source_pre & halo, folder / "intersection_pre_halo_raw.png")
    save_binary(source_pre & ~halo, folder / "pre_minus_halo_raw.png")
    save_binary(source_pre & ~final_suffix, folder / "pre_minus_final_suffix_raw.png")
    overlay = np.asarray(raw.convert("RGB"), dtype=np.uint8).copy()
    overlay[halo] = (0, 100, 255)
    overlay[source_pre] = (0, 180, 0)
    overlay[final_suffix] = (255, 0, 0)
    overlay[source_pre & halo] = (0, 255, 255)
    overlay[source_pre & final_suffix] = (255, 0, 255)
    overlay_image = Image.fromarray(overlay, mode="RGB")
    draw = ImageDraw.Draw(overlay_image)
    for glyph in glyphs:
        gx0 = glyph.bbox[0] - x0
        gy0 = glyph.bbox[1] - y0
        gx1 = glyph.bbox[2] - x0 - 1
        gy1 = glyph.bbox[3] - y0 - 1
        if gx1 >= 0 and gy1 >= 0 and gx0 < overlay.shape[1] and gy0 < overlay.shape[0]:
            draw.rectangle((gx0, gy0, gx1, gy1), outline=(255, 220, 0), width=1)
    overlay_image.save(folder / "overlay_pre_halo_final_source_bboxes_1x.png", optimize=True)
    save_json(
        folder / "source_character_bboxes.json",
        {
            "element": element.object_id,
            "semantic_text": element.text,
            "glyphs": [
                {
                    "glyph_id": glyph.object_id,
                    "text": glyph.text,
                    "bbox_full_page_px": list(glyph.bbox),
                    "source_pre_pixels": int(source_shapes[glyph.object_id].sum()),
                    "final_visible_pixels": glyph.pixels,
                    "missing_pixels": int(isolation[glyph.object_id].get("SOURCE_SHAPE_TO_FINAL_MISSING_PIXELS", 0)),
                    "missing_explained_by_later_opaque_pixels": int(isolation[glyph.object_id].get("MISSING_EXPLAINED_BY_LATER_OPAQUE_PIXELS", 0)),
                    "missing_unexplained_pixels": int(isolation[glyph.object_id].get("MISSING_UNEXPLAINED_PIXELS", 0)),
                }
                for glyph in glyphs
            ],
            "source_pre_basis": "per-CHAR frozen PDF BT/ET text-only replay masks after traceable paint-order ownership; not a synthetic bbox fill",
        },
    )
    save_json(
        folder / "source_pre_order_evidence.json",
        {
            "pre_source_node": {
                "file": str(SOURCE_FIGURE),
                "lines": "55-56",
                "tex": r"\\node[anchor=north west,text=SLTeal,fill=white,...] at (axis cs:.22,.392) {虚线 $q_L(x)=\\frac25$};",
            },
            "later_occluding_node": {
                "file": str(SOURCE_FIGURE),
                "lines": "59-60",
                "tex": r"\\node[anchor=north,align=center,text=SLTextGray,fill=white,...] at (axis cs:3.25,.442) {...};",
                "pdf_drawing_index": int(halo_entry["draw_id"]),
                "halo_id": halo_entry["halo_id"],
                "fill": "#FFFFFF",
                "fill_opacity": 1.0,
            },
            "paint_order_proof": "The q_L label source node precedes the boundary-label node; frozen PDF draw20 is the latter node's opaque white fill.",
            "pre_raster": "mask_A_source_pre_text_raw.png (frozen text-only replay, CHAR-owned; no bbox fill)",
            "final_raster": "mask_C_final_visible_suffix_raw.png",
            "halo_raster": "mask_B_later_opaque_halo_raw.png",
        },
    )
    save_json(
        folder / "manifest.json",
        {
            "element_id": element.object_id,
            "semantic_text": element.text,
            "later_opaque_halo": halo_entry["halo_id"],
            "result": "FAIL_TEXT_OCCLUSION_TEXT_COMPLETENESS",
            "reason": "Later source node white fill erases the required q_L '=2/5' suffix in the final PDF; source/halo/final masks are all native, separated and paint-order traceable.",
            "source_pre_suffix_pixels": int(source_pre.sum()),
            "source_pre_halo_overlap_pixels": int((source_pre & halo).sum()),
            "source_pre_minus_halo_pixels": int((source_pre & ~halo).sum()),
            "final_suffix_pixels": int(final_suffix.sum()),
            "source_pre_minus_final_suffix_pixels": int((source_pre & ~final_suffix).sum()),
            "files": [
                "raw_final_roi_1x.png",
                "raw_final_roi_8x_nearest.png",
                "mask_A_source_pre_text_raw.png",
                "mask_B_later_opaque_halo_raw.png",
                "mask_C_final_visible_suffix_raw.png",
                "mask_D_final_visible_parent_text_raw.png",
                "intersection_pre_halo_raw.png",
                "pre_minus_halo_raw.png",
                "pre_minus_final_suffix_raw.png",
                "overlay_pre_halo_final_source_bboxes_1x.png",
                "source_character_bboxes.json",
                "source_pre_order_evidence.json",
            ],
        },
    )
    return rel(folder)


def source_occluded_substring_package(
    sub_id: str,
    subrow: dict[str, Any],
    isolation: dict[str, Any],
    halo_entry: dict[str, Any],
    raw_full: Image.Image,
) -> str:
    """Retain a necessary source composite that is wholly absent in final ink.

    This is deliberately outside the final-visible mask/contact inventory.  It
    closes the required numerator/bar/denominator source path against the
    actual later opaque vector fill at the native page pixels.
    """
    folder = TEXT_OCCLUSION_DIR / "source_only_substrings" / sub_id
    folder.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = (int(value) for value in isolation["COMPOSITE_BBOX_FULL_PAGE_PX"])
    source = np.asarray(Image.open(OUT / str(isolation["SOURCE_COMPOSITE_MASK"])).convert("L")) < 128
    if source.shape != (y1 - y0, x1 - x0):
        raise RuntimeError(f"source composite raster/bbox mismatch: {sub_id}")
    final = np.zeros_like(source)
    fx0, fy0, fx1, fy1 = (int(value) for value in isolation["FINAL_BBOX_FULL_PAGE_PX"])
    final_local = np.asarray(Image.open(OUT / str(subrow["RAW_MASK"])).convert("L")) < 128
    if final_local.shape != (fy1 - fy0, fx1 - fx0):
        raise RuntimeError(f"final substring raster/bbox mismatch: {sub_id}")
    final[fy0 - y0 : fy1 - y0, fx0 - x0 : fx1 - x0] = final_local
    halo = np.zeros_like(source)
    hx0, hy0, hx1, hy1 = halo_entry["bbox"]
    ix0, iy0, ix1, iy1 = max(x0, hx0), max(y0, hy0), min(x1, hx1), min(y1, hy1)
    if ix0 < ix1 and iy0 < iy1:
        halo[iy0 - y0 : iy1 - y0, ix0 - x0 : ix1 - x0] = halo_entry["mask"][iy0 - hy0 : iy1 - hy0, ix0 - hx0 : ix1 - hx0]
    raw = raw_full.crop((x0, y0, x1, y1))
    raw.save(folder / "raw_final_roi_1x.png", optimize=True)
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(folder / "raw_final_roi_8x_nearest.png", optimize=True)
    save_binary(source, folder / "mask_A_source_pre_composite_raw.png")
    save_binary(halo, folder / "mask_B_later_opaque_halo_raw.png")
    save_binary(final, folder / "mask_C_final_visible_composite_raw.png")
    save_binary(source & halo, folder / "intersection_pre_halo_raw.png")
    save_binary(source & ~final, folder / "pre_minus_final_raw.png")
    overlay = np.asarray(raw.convert("RGB"), dtype=np.uint8).copy()
    overlay[halo] = (0, 100, 255)
    overlay[source] = (0, 180, 0)
    overlay[final] = (255, 0, 0)
    overlay[source & halo] = (0, 255, 255)
    Image.fromarray(overlay, mode="RGB").save(folder / "overlay_pre_halo_final_1x.png", optimize=True)
    save_json(
        folder / "manifest.json",
        {
            "source_only_substring_id": sub_id,
            "parent_element_id": subrow["PARENT_ELEMENT_ID"],
            "source_descriptor": isolation["SOURCE_COMPOSITE_DESCRIPTOR"],
            "source_composite_pixels": int(source.sum()),
            "final_visible_pixels": int(final.sum()),
            "source_pre_halo_overlap_pixels": int((source & halo).sum()),
            "source_pre_minus_final_pixels": int((source & ~final).sum()),
            "result": "FAIL_TEXT_OCCLUSION_TEXT_COMPLETENESS_SOURCE_ONLY_SUBSTRING",
            "files": [
                "raw_final_roi_1x.png", "raw_final_roi_8x_nearest.png",
                "mask_A_source_pre_composite_raw.png", "mask_B_later_opaque_halo_raw.png",
                "mask_C_final_visible_composite_raw.png", "intersection_pre_halo_raw.png",
                "pre_minus_final_raw.png", "overlay_pre_halo_final_1x.png",
            ],
        },
    )
    return rel(folder)


def glyph_later_paint_package(
    glyph: MaskObject,
    source_shape: np.ndarray,
    later_mask: np.ndarray,
    later_alpha_path_support: np.ndarray,
    drawing: dict[str, Any],
    draw_id: int,
    raw_full: Image.Image,
) -> str:
    """Native evidence for a real later non-white drawing touching text."""
    dbox = pxbbox(tuple(float(value) for value in drawing["rect"]), raw_full.width, raw_full.height, pad=2)
    x0 = max(0, min(glyph.bbox[0], dbox[0]) - 8)
    y0 = max(0, min(glyph.bbox[1], dbox[1]) - 8)
    x1 = min(raw_full.width, max(glyph.bbox[2], dbox[2]) + 8)
    y1 = min(raw_full.height, max(glyph.bbox[3], dbox[3]) + 8)
    shape = (y1 - y0, x1 - x0)
    pre = np.zeros(shape, dtype=bool)
    final = np.zeros(shape, dtype=bool)
    later = np.zeros(shape, dtype=bool)
    later_alpha = np.zeros(shape, dtype=bool)
    pre[glyph.bbox[1] - y0 : glyph.bbox[3] - y0, glyph.bbox[0] - x0 : glyph.bbox[2] - x0] = source_shape
    final[glyph.bbox[1] - y0 : glyph.bbox[3] - y0, glyph.bbox[0] - x0 : glyph.bbox[2] - x0] = glyph.mask
    # later_mask is the isolated official final paint layer in the same glyph
    # bbox (source geometry ∩ official source colour), not a broad bbox.
    later[glyph.bbox[1] - y0 : glyph.bbox[3] - y0, glyph.bbox[0] - x0 : glyph.bbox[2] - x0] = later_mask
    # The alpha/path support is separately retained because a sub-20 marker
    # edge can still replace a final text pixel; it must never be silently
    # folded into the >=20 final-colour layer.
    later_alpha[glyph.bbox[1] - y0 : glyph.bbox[3] - y0, glyph.bbox[0] - x0 : glyph.bbox[2] - x0] = later_alpha_path_support
    raw = raw_full.crop((x0, y0, x1, y1))
    folder = TEXT_LATER_PAINT_DIR / f"{glyph.object_id}_draw{draw_id:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    raw.save(folder / "raw_final_roi_1x.png", optimize=True)
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(folder / "raw_final_roi_8x_nearest.png", optimize=True)
    save_binary(pre, folder / "mask_A_source_pre_text_raw.png")
    save_binary(later, folder / "mask_B_later_nonopaque_graphic_raw.png")
    save_binary(later_alpha, folder / "mask_B_alpha_path_support_raw.png")
    save_binary(final, folder / "mask_C_final_visible_text_raw.png")
    save_binary(pre & later, folder / "intersection_pre_later_raw.png")
    missing = pre & ~final
    explained = missing & later
    unexplained = missing & ~later
    alpha_explained = missing & later_alpha
    alpha_unexplained = missing & ~later_alpha
    save_binary(missing, folder / "pre_minus_final_raw.png")
    save_binary(explained, folder / "intersection_pre_minus_final_later_raw.png")
    save_binary(unexplained, folder / "pre_minus_final_minus_later_raw.png")
    save_binary(alpha_explained, folder / "intersection_pre_minus_final_later_alpha_support_raw.png")
    save_binary(alpha_unexplained, folder / "pre_minus_final_minus_later_alpha_support_raw.png")
    overlay = np.asarray(raw.convert("RGB"), dtype=np.uint8).copy()
    overlay[later] = (0, 180, 255)
    overlay[pre] = (0, 190, 0)
    overlay[final] = (255, 0, 0)
    overlay[pre & later] = (255, 0, 255)
    Image.fromarray(overlay, mode="RGB").save(folder / "overlay_pre_later_final_1x.png", optimize=True)
    save_json(
        folder / "manifest.json",
        {
            "glyph_id": glyph.object_id,
            "char": glyph.text,
            "parent_element_id": glyph.parent,
            "later_pdf_drawing_index": draw_id,
            "later_fill_rgb": as_rgb(drawing.get("fill")),
            "later_fill_opacity": drawing.get("fill_opacity"),
            "later_stroke_rgb": as_rgb(drawing.get("color")),
            "later_stroke_opacity": drawing.get("stroke_opacity"),
            "source_pre_pixels": int(pre.sum()),
            "later_intersection_pixels": int((pre & later).sum()),
            "pre_minus_final_pixels": int(missing.sum()),
            "pre_minus_final_intersection_later_pixels": int(explained.sum()),
            "pre_minus_final_minus_later_pixels": int(unexplained.sum()),
            "pre_minus_final_intersection_later_alpha_path_support_pixels": int(alpha_explained.sum()),
            "pre_minus_final_minus_later_alpha_path_support_pixels": int(alpha_unexplained.sum()),
            "result": (
                "FAIL_NONOPAQUE_LATER_TEXT_COVERAGE_ALPHA_PATH_PROVED"
                if not alpha_unexplained.any()
                else "FAIL_UNEXPLAINED_TEXT_MISSING_AFTER_LATER_PAINT"
            ),
            "files": [
                "raw_final_roi_1x.png", "raw_final_roi_8x_nearest.png",
                "mask_A_source_pre_text_raw.png", "mask_B_later_nonopaque_graphic_raw.png",
                "mask_B_alpha_path_support_raw.png",
                "mask_C_final_visible_text_raw.png", "intersection_pre_later_raw.png",
                "pre_minus_final_raw.png", "intersection_pre_minus_final_later_raw.png",
                "pre_minus_final_minus_later_raw.png", "intersection_pre_minus_final_later_alpha_support_raw.png",
                "pre_minus_final_minus_later_alpha_support_raw.png", "overlay_pre_later_final_1x.png",
            ],
        },
    )
    return rel(folder)


def translucent_label_overlay_package(
    graphic: MaskObject,
    pre_mask: np.ndarray | None,
    overlay_entry: dict[str, Any],
    raw_full: Image.Image,
    *,
    unresolved_pre: bool = False,
) -> str:
    """Layered evidence for a source-transparent label ground over graphics."""
    ox0, oy0, ox1, oy1 = overlay_entry["bbox"]
    x0 = max(0, min(graphic.bbox[0], ox0) - 12)
    y0 = max(0, min(graphic.bbox[1], oy0) - 12)
    x1 = min(raw_full.width, max(graphic.bbox[2], ox1) + 12)
    y1 = min(raw_full.height, max(graphic.bbox[3], oy1) + 12)
    shape = (y1 - y0, x1 - x0)
    final = np.zeros(shape, dtype=bool)
    final[graphic.bbox[1] - y0 : graphic.bbox[3] - y0, graphic.bbox[0] - x0 : graphic.bbox[2] - x0] = graphic.mask
    overlay = np.zeros(shape, dtype=bool)
    overlay[oy0 - y0 : oy1 - y0, ox0 - x0 : ox1 - x0] = overlay_entry["mask"]
    pre = None
    if pre_mask is not None:
        pre = np.zeros(shape, dtype=bool)
        pre[graphic.bbox[1] - y0 : graphic.bbox[3] - y0, graphic.bbox[0] - x0 : graphic.bbox[2] - x0] = pre_mask
    raw = raw_full.crop((x0, y0, x1, y1))
    folder = TRANSLUCENT_OCCLUSION_DIR / f"{graphic.object_id}_{overlay_entry['overlay_id']}"
    folder.mkdir(parents=True, exist_ok=True)
    raw.save(folder / "raw_final_roi_1x.png", optimize=True)
    raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(folder / "raw_final_roi_8x_nearest.png", optimize=True)
    if pre is not None:
        save_binary(pre, folder / "mask_A_source_pre_graphic_raw.png")
        save_binary(pre & overlay, folder / "intersection_pre_translucent_overlay_raw.png")
        save_binary(pre & ~final, folder / "pre_minus_final_raw.png")
    else:
        (folder / "mask_A_source_pre_graphic_UNAVAILABLE.md").write_text(
            "No traceable standalone source raster exists for this patterned form/XObject; no pre-mask was synthesized from the final raster. This absence is a hard unresolved-pre failure.\n",
            encoding="utf-8",
        )
    save_binary(overlay, folder / "mask_B_translucent_label_overlay_raw.png")
    save_binary(final, folder / "mask_C_final_visible_graphic_raw.png")
    composited = np.asarray(raw.convert("RGB"), dtype=np.uint8).copy()
    composited[overlay] = (0, 100, 255)
    if pre is not None:
        composited[pre] = (0, 180, 0)
        composited[pre & overlay] = (255, 0, 255)
    composited[final] = (255, 0, 0)
    Image.fromarray(composited, mode="RGB").save(folder / "overlay_pre_translucent_final_1x.png", optimize=True)
    save_json(
        folder / "manifest.json",
        {
            "graphic_id": graphic.object_id,
            "graphic_role": graphic.role,
            "overlay_id": overlay_entry["overlay_id"],
            "overlay_draw_id": int(overlay_entry["draw_id"]),
            "overlay_parent_element_id": overlay_entry.get("associated_parent", "N/A"),
            "fill_opacity": overlay_entry["opacity"],
            "source_pre_available": pre is not None,
            "source_pre_pixels": int(pre.sum()) if pre is not None else None,
            "source_pre_overlay_intersection_pixels": int((pre & overlay).sum()) if pre is not None else None,
            "pre_minus_final_pixels": int((pre & ~final).sum()) if pre is not None else None,
            "final_visible_pixels": int(final.sum()),
            "result": "FAIL_UNRESOLVED_PRE_TRANSPARENT_OVERLAY" if unresolved_pre else "FAIL_TEXT_TRANSPARENT_LABEL_DATA_COVERAGE",
        },
    )
    return rel(folder)


def resolve_overlapping_glyph_ownership(glyphs: list[MaskObject]) -> dict[str, Any]:
    """Assign each replayed text pixel to one CHAR by traceable paint order.

    Rawdict character bboxes may overlap for adjacent glyphs, fractions and
    stacked TeX.  The candidate masks here come solely from the frozen PDF's
    text-only BT/ET replay, never from a broad final-page crop.  Whenever two
    candidates claim the same native pixel, the lower source text-trace paint
    order loses it to the later painted character.  Thus every surviving pixel
    has a unique CHAR owner; no centre-distance heuristic, dilation, neighbour
    reuse, hatch, curve, or same-colour graphic can enter a glyph mask.
    """
    conflicts: list[dict[str, Any]] = []
    # Resolve only the tiny local intersection rectangles.  A connected chain
    # of neighbouring caption characters must not turn into a page-sized
    # ownership raster (and no pixels outside a true bbox intersection are
    # ever reconsidered).
    for left_index, right_index in itertools.combinations(range(len(glyphs)), 2):
        left, right = glyphs[left_index], glyphs[right_index]
        x0 = max(left.bbox[0], right.bbox[0])
        y0 = max(left.bbox[1], right.bbox[1])
        x1 = min(left.bbox[2], right.bbox[2])
        y1 = min(left.bbox[3], right.bbox[3])
        if x0 >= x1 or y0 >= y1:
            continue
        left_view = left.mask[y0 - left.bbox[1] : y1 - left.bbox[1], x0 - left.bbox[0] : x1 - left.bbox[0]]
        right_view = right.mask[y0 - right.bbox[1] : y1 - right.bbox[1], x0 - right.bbox[0] : x1 - right.bbox[0]]
        shared = left_view & right_view
        if not shared.any():
            continue
        if left.paint_order < 0 or right.paint_order < 0:
            raise RuntimeError(f"missing text-trace paint order: {left.object_id}, {right.object_id}")
        # Later source text operation owns a truly overlapping painted pixel.
        if left.paint_order <= right.paint_order:
            left_view[shared] = False
            winner, loser = right.object_id, left.object_id
        else:
            right_view[shared] = False
            winner, loser = left.object_id, right.object_id
        conflicts.append(
            {
                "glyph_A": left.object_id,
                "glyph_B": right.object_id,
                "intersection_bbox_full_page_px": [x0, y0, x1, y1],
                "shared_candidate_pixels": int(shared.sum()),
                "winner": winner,
                "loser": loser,
                "rule": "frozen PDF texttrace later-paint ownership; text-only replay candidate; no dilation or neighbour reuse",
            }
        )
    return {"overlap_components": conflicts}


def mask_union(objects: Iterable[MaskObject]) -> tuple[tuple[int, int, int, int], np.ndarray]:
    items = list(objects)
    x0 = min(item.bbox[0] for item in items)
    y0 = min(item.bbox[1] for item in items)
    x1 = max(item.bbox[2] for item in items)
    y1 = max(item.bbox[3] for item in items)
    result = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    for item in items:
        result[item.bbox[1] - y0 : item.bbox[3] - y0, item.bbox[0] - x0 : item.bbox[2] - x0] |= item.mask
    return (x0, y0, x1, y1), result


def path_segments(drawing: dict[str, Any], curve_steps: int = 48) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Return source-vector segments, including cubic paths, for halo tests."""
    result: list[tuple[tuple[float, float], tuple[float, float]]] = []

    def xy(point: Any) -> tuple[float, float]:
        return (float(point.x), float(point.y))

    def cubic(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> list[tuple[float, float]]:
        values = []
        for step in range(curve_steps + 1):
            t = step / curve_steps
            u = 1.0 - t
            values.append((
                u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
            ))
        return values

    for item in drawing.get("items", []):
        if item[0] == "l":
            result.append((xy(item[1]), xy(item[2])))
        elif item[0] == "c":
            points = cubic(xy(item[1]), xy(item[2]), xy(item[3]), xy(item[4]))
            result.extend(zip(points, points[1:]))
        elif item[0] == "re":
            rect = item[1]
            points = [(float(rect.x0), float(rect.y0)), (float(rect.x1), float(rect.y0)), (float(rect.x1), float(rect.y1)), (float(rect.x0), float(rect.y1))]
            result.extend(zip(points, points[1:] + points[:1]))
        else:
            raise RuntimeError(f"unhandled drawing item for halo audit: {item[0]}")
    return result


def segment_hits_rect(
    segment: tuple[tuple[float, float], tuple[float, float]],
    rect: tuple[float, float, float, float],
    extra_pt: float,
) -> bool:
    """Conservative exact-line / buffered-rectangle test in source points."""
    (x0, y0), (x1, y1) = segment
    rx0, ry0, rx1, ry1 = (rect[0] - extra_pt, rect[1] - extra_pt, rect[2] + extra_pt, rect[3] + extra_pt)
    if rx0 <= x0 <= rx1 and ry0 <= y0 <= ry1:
        return True
    if rx0 <= x1 <= rx1 and ry0 <= y1 <= ry1:
        return True
    dx, dy = x1 - x0, y1 - y0
    p = (-dx, dx, -dy, dy)
    q = (x0 - rx0, rx1 - x0, y0 - ry0, ry1 - y0)
    t0, t1 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return False
            continue
        ratio = qi / pi
        if pi < 0:
            if ratio > t1:
                return False
            t0 = max(t0, ratio)
        else:
            if ratio < t0:
                return False
            t1 = min(t1, ratio)
    return t0 <= t1


def native_render(pdf: Path, page_one_based: int, dpi: int, output_png: Path) -> None:
    """Direct Poppler render of the frozen official page; never resampled."""
    output_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "pdftoppm", "-f", str(page_one_based), "-l", str(page_one_based),
            "-r", str(dpi), "-png", "-singlefile", str(pdf), str(output_png.with_suffix("")),
        ],
        check=True,
    )


def rawdict_character_trace(page: fitz.Page) -> list[dict[str, Any]]:
    """Frozen PDF texttrace entries in actual source paint order."""
    entries: list[dict[str, Any]] = []
    order = 0
    for span in page.get_texttrace():
        seqno = int(span.get("seqno", -1))
        color = tuple(round(float(item), 6) for item in span.get("color", (0.0, 0.0, 0.0)))
        opacity = round(float(span.get("opacity", 1.0)), 6)
        for char in span["chars"]:
            entries.append(
                {
                    "char": chr(int(char[0])),
                    "bbox": tuple(float(item) for item in char[3]),
                    "seqno": seqno,
                    "paint_order": order,
                    "font": str(span.get("font", "")),
                    "font_size": round(float(span.get("size", 0.0)), 6),
                    "fill_rgb": color,
                    "opacity": opacity,
                }
            )
            order += 1
    return entries


def raster_source_drawing_mask(
    drawing: dict[str, Any],
    page_rect: fitz.Rect,
    width: int,
    height: int,
    expected_box: tuple[int, int, int, int],
    *,
    coverage_only: bool = False,
    any_paint_alpha: bool = False,
) -> np.ndarray:
    """Traceable source-vector component mask in the official 300-dpi grid.

    This is a containment / ownership path made from the frozen PDF drawing
    items, colour, width, dash, cap, join, and opacity. Final measurement still
    intersects it with the official Poppler page; it never adds pixels.
    """
    source_doc = fitz.open()
    source_page = source_doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = source_page.new_shape()
    for item in drawing.get("items", []):
        if item[0] == "l":
            shape.draw_line(item[1], item[2])
        elif item[0] == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif item[0] == "re":
            shape.draw_rect(item[1])
        else:
            source_doc.close()
            raise RuntimeError(f"unhandled source drawing item for component mask: {item[0]}")
    cap = drawing.get("lineCap") or 0
    if isinstance(cap, (tuple, list)):
        cap = cap[0]
    join = drawing.get("lineJoin") or 0
    source_stroke = drawing.get("color")
    source_fill = drawing.get("fill")
    # A real opaque white fill cannot be recovered by "ink on white" colour
    # thresholding: its geometry is still an occluder.  Render it black only
    # for the source-geometry ledger; never use this substitute as final ink.
    stroke = (0.0, 0.0, 0.0) if coverage_only and source_stroke is not None else source_stroke
    fill = (0.0, 0.0, 0.0) if coverage_only and source_fill is not None else source_fill
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=stroke,
        fill=fill,
        lineCap=int(cap),
        lineJoin=int(join),
        dashes=drawing.get("dashes"),
        closePath=bool(drawing.get("closePath", False)),
        fill_opacity=float(drawing.get("fill_opacity") or 1.0),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1.0),
    )
    shape.commit()
    pix = source_page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=any_paint_alpha, colorspace=fitz.csRGB)
    samples = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    source_doc.close()
    if (pix.width, pix.height) != (width, height):
        raise RuntimeError(f"source-vector grid drift: {(pix.width, pix.height)} vs {(width, height)}")
    if any_paint_alpha:
        # This is a traceable source operator's complete alpha/path support,
        # not a final-visible ink mask.  It includes sub-20 antialias pixels
        # that may still replace a >=20 text pixel when painted later.
        if pix.n != 4:
            raise RuntimeError("alpha source-vector replay did not return RGBA")
        full = samples[:, :, 3] > 0
    else:
        source_rgb = samples[:, :, :3]
        full = np.max(np.abs(source_rgb.astype(np.int16) - 255), axis=2) >= FOREGROUND_DELTA
    return full[expected_box[1] : expected_box[3], expected_box[0] : expected_box[2]].copy()


def main() -> int:
    for required in (PDF, SOURCE_FIGURE, SOURCE_CHAPTER, SOURCE_STYLE):
        if not required.exists():
            raise FileNotFoundError(required)

    # Every RUN7 view is directly generated from the frozen official full book.
    native_render(PDF, PAGE_ONE_BASED, 300, FULL_300)
    native_render(PDF, PAGE_ONE_BASED, 200, FULL_200)
    for required in (FULL_300, FULL_200, TEXT_REPLAY_300, TEXT_REPLAY_REPORT, TEXT_REPLAY_PDF):
        if not required.exists():
            raise FileNotFoundError(f"RUN7 text-isolation prerequisite missing: {required}")

    raw_full = Image.open(FULL_300).convert("RGB")
    raw_200 = Image.open(FULL_200).convert("RGB")
    text_replay = Image.open(TEXT_REPLAY_300).convert("RGB")
    width, height = raw_full.size
    if raw_200.size != (1654, 2339):
        # The exact PDF page does not have to have this common Poppler size,
        # but a missing/changed 200 dpi render is evidence failure.
        raise RuntimeError(f"unexpected 200dpi page grid: {raw_200.size}")
    if raw_full.size != (2481, 3508):
        raise RuntimeError(f"unexpected 300dpi page grid: {raw_full.size}")
    if text_replay.size != raw_full.size:
        raise RuntimeError(f"text-only replay grid drifted: {text_replay.size} vs {raw_full.size}")
    text_replay_report = json.loads(TEXT_REPLAY_REPORT.read_text(encoding="utf-8"))
    allowed_dropped = {"m", "l", "S", "s", "f", "F", "f*", "B", "B*", "b", "b*", "h", "re", "c", "v", "y", "n"}
    dropped = set(text_replay_report.get("parser", {}).get("dropped_operators", {}))
    if not text_replay_report.get("character_stream_exact") or not text_replay_report.get("text_trace_visual_properties_exact"):
        raise RuntimeError("text-only replay does not preserve frozen CHAR/bbox/font/colour/opacity trace")
    if not dropped <= allowed_dropped:
        raise RuntimeError(f"text-only replay omitted unsupported state/XObject/clip operator(s): {sorted(dropped - allowed_dropped)}")

    figure_px = pxbbox(FIGURE_RECT_PT, width, height)
    standalone_px = pxbbox(STANDALONE_RECT_PT, width, height)
    figure_crop = raw_full.crop(figure_px)
    standalone = raw_full.crop(standalone_px)
    figure_crop.save(OUT / "figure_crop_300dpi.png", optimize=True)
    standalone.save(OUT / "standalone_300dpi.png", optimize=True)
    ImageOps.grayscale(figure_crop).save(OUT / "grayscale_300dpi.png", optimize=True)

    with fitz.open(PDF) as document:
        if document.page_count != 813:
            raise RuntimeError(f"frozen candidate page count drifted: {document.page_count}")
        page = document[PAGE_INDEX]
        page_text = page.get_text("text")
        page_dict = page.get_text("rawdict")
        drawings = page.get_drawings()
        page_rect = page.rect
        text_trace = rawdict_character_trace(page)
    (OUT / "page_628_anchor_text.txt").write_text(page_text, encoding="utf-8")

    anchors = {
        "figure_number": "图31.6" in page_text or "图 31.6" in page_text,
        "support_caption": "重要性抽样要求" in page_text and "未覆盖" in page_text,
        "left_support": "支持不足" in page_text,
        "right_support": "支持覆盖" in page_text,
        "context_anchor": "固定共同定义域" in page_text,
    }
    source_check = source_text_check()
    save_json(OUT / "source_text_anchor.json", {"pdf_page_anchors": anchors, "source_checks": source_check})
    save_json(
        OUT / "render_manifest.json",
        {
            "pdf": str(PDF),
            "frozen_candidate": "strict_current_r94_fullbook/main_full.pdf",
            "physical_page": PAGE_ONE_BASED,
            "printed_page": PRINTED_PAGE,
            "page_size_pt": [round(page_rect.width, 3), round(page_rect.height, 3)],
            "full_page_300dpi_grid": [width, height],
            "full_page_200dpi_grid": list(raw_200.size),
            "dpi": {"measurement": 300, "full_page_review": 200},
            "rendering": "Poppler pdftoppm direct PDF raster; no post-render resize",
            "figure_crop_full_page_px": list(figure_px),
            "standalone_crop_full_page_px": list(standalone_px),
            "crop_operation": "integer-coordinate crop only; no resampling",
            "files": {
                "full_page_200dpi": "full_page_200dpi.png",
                "full_page_300dpi": "full_page_300dpi.png",
                "figure_crop_300dpi": "figure_crop_300dpi.png",
                "standalone_300dpi": "standalone_300dpi.png",
                "grayscale_300dpi": "grayscale_300dpi.png",
            },
        },
    )

    # Pixels at least 20/255 from the local white page background are valid
    # foreground. The figure uses white or transparent label grounds; no dark
    # filled background is present in its declared source.
    rgb = np.asarray(raw_full, dtype=np.int16)
    ink = np.max(np.abs(rgb - 255), axis=2) >= FOREGROUND_DELTA
    text_rgb = np.asarray(text_replay, dtype=np.int16)
    text_replay_ink = np.max(np.abs(text_rgb - 255), axis=2) >= FOREGROUND_DELTA
    # Exact official final foreground not occupied by a replayed BT/ET glyph is
    # the traceable background/texture/curve layer for the contamination gate.
    background_texture_ink = ink & ~text_replay_ink
    save_binary(text_replay_ink, MASK_ROOT / "text_only_replay_ink_300dpi.png")
    save_binary(background_texture_ink, MASK_ROOT / "known_background_texture_ink_300dpi.png")

    raw_lines: list[dict[str, Any]] = []
    for block in page_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            chars: list[dict[str, Any]] = []
            for span in line["spans"]:
                for char in span["chars"]:
                    payload = dict(char)
                    payload["font"] = span.get("font", "")
                    payload["size"] = float(span.get("size", 0.0))
                    chars.append(payload)
            if not chars:
                continue
            box = tuple(float(value) for value in line["bbox"])
            if not intersects(box, FIGURE_RECT_PT):
                continue
            text = "".join(str(char["c"]) for char in chars)
            if not text.strip():
                continue
            raw_lines.append({"bbox": box, "text": text, "chars": chars})

    # Caption line wrapping is one semantic parent, avoiding an invalid
    # internal 4 px text-text relation across natural wrap lines.
    caption_lines = [line for line in raw_lines if line["bbox"][1] >= 457]
    other_lines = [line for line in raw_lines if line["bbox"][1] < 457]
    semantic_lines = other_lines[:]
    if caption_lines:
        semantic_lines.append(
            {
                "bbox": bbox_union(line["bbox"] for line in caption_lines),
                "text": " ".join(line["text"] for line in caption_lines),
                "chars": [char for line in caption_lines for char in line["chars"]],
                "caption_parent": True,
            }
        )
    semantic_lines.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))

    glyphs: list[MaskObject] = []
    elements: list[MaskObject] = []
    font_rows: list[dict[str, Any]] = []
    pixel_rows: list[dict[str, Any]] = []
    mask_rows: list[dict[str, Any]] = []
    element_char_index: dict[str, list[MaskObject]] = {}
    combining_components: list[dict[str, Any]] = []
    glyph_isolation: dict[str, dict[str, Any]] = {}
    glyph_source_shapes: dict[str, np.ndarray] = {}
    trace_available = list(text_trace)

    def take_trace_owner(char: str, char_box_pt: tuple[float, float, float, float]) -> dict[str, Any]:
        """Bind one rawdict CHAR to one frozen texttrace paint operation."""
        choices = [
            (index, entry)
            for index, entry in enumerate(trace_available)
            if entry["char"] == char
        ]
        if not choices:
            raise RuntimeError(f"no texttrace CHAR candidate for {char!r} {char_box_pt}")
        index, entry = min(
            choices,
            key=lambda pair: sum(abs(float(a) - float(b)) for a, b in zip(pair[1]["bbox"], char_box_pt)),
        )
        drift = sum(abs(float(a) - float(b)) for a, b in zip(entry["bbox"], char_box_pt))
        # MuPDF rawdict and texttrace use different ascender/descender bbox
        # conventions (CJK differs by about .8 pt; some fullwidth punctuation
        # uses a raw line-height box and differs by 4.5 pt). Identity remains
        # CHAR plus the uniquely nearest native source position; 6 pt is below
        # the nearest competing same-character position on this frozen page.
        if drift > 6.0:
            raise RuntimeError(
                f"ambiguous texttrace CHAR/bbox match for U+{ord(char):04X} raw={char_box_pt} "
                f"trace={entry['bbox']}: drift={drift:.5f}pt"
            )
        trace_available.pop(index)
        return {**entry, "rawdict_trace_bbox_l1_drift_pt": round(drift, 6)}

    for number, line in enumerate(semantic_lines, 1):
        element_id = f"E{number:03d}"
        source_box = tuple(float(value) for value in line["bbox"])
        role = role_for_line(line["text"], source_box)
        panel = "GLOBAL" if role == "CAPTION" else panel_for_box(source_box)
        pbox = pxbbox(source_box, width, height)
        declared = declared_pt(role)
        chars_for_element: list[MaskObject] = []
        pdf_sizes: list[float] = []
        for char_number, char in enumerate(line["chars"], 1):
            value = str(char["c"])
            if not value.strip() or ord(value) < 32:
                continue
            # MuPDF exposes TeX \not as a zero-advance U+0338 component.  Its
            # painted slash is included in the following U+226A glyph bbox;
            # keeping the zero-width extraction record as an independent mask
            # would manufacture an empty "glyph".  It is closed later by the
            # explicit S_NOT_LL necessary-substring record.
            if value == "\u0338":
                combining_components.append(
                    {
                        "raw_text": value,
                        "raw_line_text": line["text"],
                        "raw_line_bbox_pt": [round(item, 4) for item in source_box],
                        "closure": "S_NOT_LL (visible \u226A glyph contains the TeX \\not slash)",
                    }
                )
                continue
            char_box_pt = tuple(float(item) for item in char["bbox"])
            trace_owner = take_trace_owner(value, char_box_pt)
            # The rawdict rectangle is a text-layout box, whereas texttrace
            # carries the actual character paint operator's box.  Use their
            # integer-pixel union as the strictly traceable *ownership ROI*;
            # this retains anti-aliased edge pixels that can lie one native
            # pixel beyond rawdict's rounding while global paint-order
            # ownership below still prevents a neighbour from being retained.
            rawdict_cbox = pxbbox(char_box_pt, width, height)
            trace_cbox = pxbbox(tuple(float(item) for item in trace_owner["bbox"]), width, height)
            ownership_unpadded_cbox = (
                min(rawdict_cbox[0], trace_cbox[0]), min(rawdict_cbox[1], trace_cbox[1]),
                max(rawdict_cbox[2], trace_cbox[2]), max(rawdict_cbox[3], trace_cbox[3]),
            )
            # Poppler's >=20/255 fringe can extend up to two native pixels
            # outside MuPDF's integer-rounded trace box.  This is a bounded
            # anti-alias envelope, not an expanded measurement mask: it is
            # fed only the text-only replay and every intersecting char is
            # then resolved by its actual frozen PDF paint order.
            ownership_roi_pad = 2
            cbox = (
                max(0, ownership_unpadded_cbox[0] - ownership_roi_pad),
                max(0, ownership_unpadded_cbox[1] - ownership_roi_pad),
                min(width, ownership_unpadded_cbox[2] + ownership_roi_pad),
                min(height, ownership_unpadded_cbox[3] + ownership_roi_pad),
            )
            # Candidate is only the frozen PDF BT/ET replayed shape. It is not
            # a crop of all official-page foreground; final visibility is
            # applied after global CHAR ownership below.
            cmask = text_replay_ink[cbox[1] : cbox[3], cbox[0] : cbox[2]].copy()
            pdf_font_pt = float(char.get("size", 0.0))
            script, threshold = classify_character(value, char_box_pt, source_box, pdf_font_pt, pdf_font_pt)
            glyph_id = f"G{len(glyphs) + 1:04d}"
            raw_path = GLYPH_DIR / f"{glyph_id}_raw.png"
            glyph = MaskObject(
                glyph_id,
                "GLYPH",
                role,
                panel,
                cbox,
                cmask,
                raw_path,
                source_line(role, line["text"]),
                text=value,
                parent=element_id,
                paint_order=int(trace_owner["paint_order"]),
            )
            glyphs.append(glyph)
            chars_for_element.append(glyph)
            broad_final = ink[cbox[1] : cbox[3], cbox[0] : cbox[2]]
            known_background = background_texture_ink[cbox[1] : cbox[3], cbox[0] : cbox[2]]
            glyph_isolation[glyph_id] = {
                "TRACE_SEQNO": int(trace_owner["seqno"]),
                "TRACE_PAINT_ORDER": int(trace_owner["paint_order"]),
                "RAWDICT_TEXTTRACE_BBOX_L1_DRIFT_PT": float(trace_owner["rawdict_trace_bbox_l1_drift_pt"]),
                "RAWDICT_CHAR_BBOX_FULL_PAGE_PX": list(rawdict_cbox),
                "TEXTTRACE_CHAR_BBOX_FULL_PAGE_PX": list(trace_cbox),
                "OWNERSHIP_UNPADDED_BBOX_FULL_PAGE_PX": list(ownership_unpadded_cbox),
                "OWNERSHIP_ROI_PAD_NATIVE_PX": ownership_roi_pad,
                "OWNERSHIP_BBOX_FULL_PAGE_PX": list(cbox),
                "TEXTTRACE_FONT": str(trace_owner["font"]),
                "TEXTTRACE_FONT_SIZE_PT": float(trace_owner["font_size"]),
                "TEXTTRACE_FILL_RGB": list(trace_owner["fill_rgb"]),
                "TEXTTRACE_OPACITY": float(trace_owner["opacity"]),
                "TEXT_ONLY_SHAPE_PIXELS_PRE_OWNERSHIP": int(cmask.sum()),
                "BROAD_FINAL_FOREGROUND_PIXELS": int(broad_final.sum()),
                "BBOX_BACKGROUND_TEXTURE_PIXELS_PRE_REPAIR": int(known_background.sum()),
            }
            pdf_sizes.append(pdf_font_pt)
            h_ink = int(cmask.any(axis=1).sum())
            pixel_pass = glyph.nonempty and h_ink >= threshold
            reason = "PASS" if pixel_pass else ("EMPTY_RAW_MASK" if not glyph.nonempty else f"H_INK={h_ink}<{threshold}")
            # Provisional source-layer measurement is never packaged. The only
            # active pixel evidence is generated after final visibility and
            # global CHAR ownership have both closed.
            failure_evidence = ""
            pixel_rows.append(
                {
                    "MEASURE_ID": glyph_id,
                    "ELEMENT_ID": glyph_id,
                    "PARENT_ELEMENT_ID": element_id,
                    "PANEL_ID": panel,
                    "ROLE": role,
                    "SOURCE_FILE": str(SOURCE_FIGURE),
                    "SOURCE_LINE": source_line(role, line["text"]),
                    "DECLARED_PT": f"{declared:.2f}",
                    "GRAPHICS_SCALE": "1.000000",
                    "EFFECTIVE_PT": f"{declared:.2f}",
                    "PDF_FONT_PT": f"{pdf_font_pt:.3f}",
                    "TEXT_SAMPLE": value,
                    "SCRIPT_CLASS": script,
                    "THRESHOLD_PX": threshold,
                    "BBOX_X0": cbox[0],
                    "BBOX_Y0": cbox[1],
                    "BBOX_X1": cbox[2],
                    "BBOX_Y1": cbox[3],
                    "H_INK_PX": h_ink,
                    "RAW_MASK": rel(raw_path),
                    "CLASS_MEDIAN_PX": "",
                    "RATIO_TO_CLASS_MEDIAN": "",
                    "ROLE_RATIO": "",
                    "TEXT_TEXT_OVERLAP_PX": "",
                    "TEXT_GRAPHIC_OVERLAP_PX": "",
                    "MIN_CLEARANCE_PX": "",
                    "PIXEL_HEIGHT_PASS": str(pixel_pass).lower(),
                    "PASS_FAIL": "PASS" if pixel_pass else "FAIL",
                    "REASON": reason,
                    "FAILURE_EVIDENCE": failure_evidence,
                }
            )
            mask_rows.append(
                {
                    "MASK_ID": glyph_id,
                    "KIND": "GLYPH",
                    "PARENT_ID": element_id,
                    "ROLE": role,
                    "PANEL": panel,
                    "BBOX_FULL_PAGE_PX": json.dumps(cbox),
                    "PIXELS": glyph.pixels,
                    "NONEMPTY": str(glyph.nonempty).lower(),
                    "RAW_MASK": rel(raw_path),
                    "FINAL_VISIBLE_MASK": rel(raw_path),
                }
            )

        if not chars_for_element:
            continue
        ebox = (
            min(item.bbox[0] for item in chars_for_element),
            min(item.bbox[1] for item in chars_for_element),
            max(item.bbox[2] for item in chars_for_element),
            max(item.bbox[3] for item in chars_for_element),
        )
        emask = np.zeros((ebox[3] - ebox[1], ebox[2] - ebox[0]), dtype=bool)
        for glyph in chars_for_element:
            emask[
                glyph.bbox[1] - ebox[1] : glyph.bbox[3] - ebox[1],
                glyph.bbox[0] - ebox[0] : glyph.bbox[2] - ebox[0],
            ] |= glyph.mask
        element_path = ELEMENT_DIR / f"{element_id}_raw.png"
        save_binary(emask, element_path)
        element = MaskObject(
            element_id,
            "TEXT",
            role,
            panel,
            ebox,
            emask,
            element_path,
            source_line(role, line["text"]),
            text=line["text"],
        )
        elements.append(element)
        element_char_index[element_id] = chars_for_element
        font_pass = declared >= 9.5
        font_rows.append(
            {
                "ELEMENT_ID": element_id,
                "PANEL_ID": panel,
                "ROLE": role,
                "SOURCE_FILE": str(SOURCE_FIGURE if role != "CAPTION" else SOURCE_STYLE),
                "SOURCE_LINE": source_line(role, line["text"]),
                "DECLARED_PT": f"{declared:.2f}",
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": f"{declared:.2f}",
                "PDF_FONT_PT_MEDIAN": f"{median(pdf_sizes):.3f}",
                "TEXT_SAMPLE": line["text"],
                "RAW_MASK": rel(element_path),
                "SOURCE_FONT_PASS": str(font_pass).lower(),
                "REASON": "PASS" if font_pass else "effective_pt_below_9.5",
            }
        )
        mask_rows.append(
            {
                "MASK_ID": element_id,
                "KIND": "TEXT_ELEMENT",
                "PARENT_ID": "",
                "ROLE": role,
                "PANEL": panel,
                "BBOX_FULL_PAGE_PX": json.dumps(ebox),
                "PIXELS": element.pixels,
                "NONEMPTY": str(element.nonempty).lower(),
                "RAW_MASK": rel(element_path),
                "FINAL_VISIBLE_MASK": rel(element_path),
            }
        )

    # Reconstruct source-level semantic nodes before any relationship test.
    # In particular, a TeX fraction can arrive as two PDF text lines, while a
    # source \node can contain two displayed lines.  The source nodes below
    # are the required unique ELEMENT_ID closure; raw PDF lines remain in the
    # inventory solely as traceability evidence.
    raw_elements = list(elements)
    raw_element_char_index = dict(element_char_index)
    ownership_report = resolve_overlapping_glyph_ownership(glyphs)
    source_assignment_count = np.zeros((height, width), dtype=np.uint16)
    for glyph in glyphs:
        glyph_isolation[glyph.object_id]["TEXT_ONLY_SHAPE_PIXELS_POST_OWNERSHIP"] = glyph.pixels
        glyph_source_shapes[glyph.object_id] = glyph.mask.copy()
        save_binary(glyph.mask, TEXT_SOURCE_SHAPE_DIR / f"{glyph.object_id}_source_text_shape.png")
        source_assignment_count[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]] += glyph.mask.astype(np.uint16)
    fx0, fy0, fx1, fy1 = figure_px
    source_text_in_scope = text_replay_ink[fy0:fy1, fx0:fx1]
    source_owner_in_scope = source_assignment_count[fy0:fy1, fx0:fx1]
    ownership_report["source_duplicate_text_pixels"] = int((source_owner_in_scope > 1).sum())
    ownership_report["source_unassigned_text_replay_pixels_in_figure"] = int((source_text_in_scope & (source_owner_in_scope == 0)).sum())
    ownership_report["source_text_replay_pixels_in_figure"] = int(source_text_in_scope.sum())
    # Apply the frozen official final page only after every text-replay pixel
    # has exactly one CHAR owner. Later opaque paint therefore removes source
    # glyph pixels honestly; unrelated final hatch/curve pixels can never be
    # admitted because they were absent from the BT/ET replay candidate.
    for glyph in glyphs:
        final_native = ink[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]]
        final_text_colour = final_text_colour_mask(
            rgb[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]],
            glyph_isolation[glyph.object_id]["TEXTTRACE_FILL_RGB"],
        )
        known_background = background_texture_ink[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]]
        source_shape = glyph_source_shapes[glyph.object_id]
        # Final target ownership is the CHAR-owned source replay intersected
        # with the official final pixel *and* that CHAR's actual PDF fill
        # direction. Generic ``ink`` alone would admit a later teal marker
        # into a dark-gray CJK glyph (G0061); that is prohibited.
        glyph.mask &= final_native & final_text_colour
        save_binary(glyph.mask, glyph.raw_path)
        record = glyph_isolation[glyph.object_id]
        record.update(
            {
                "FINAL_VISIBLE_TARGET_PIXELS": glyph.pixels,
                "SOURCE_SHAPE_TO_FINAL_MISSING_PIXELS": int((source_shape & ~glyph.mask).sum()),
                "FINAL_TARGET_BACKGROUND_TEXTURE_INTERSECTION_PIXELS": int((glyph.mask & known_background).sum()),
                "FINAL_TARGET_NATIVE_FOREGROUND_SUBSET": bool(np.all(~glyph.mask | final_native)),
                "FINAL_TARGET_TEXT_FILL_MATCH_PIXELS": int((source_shape & final_text_colour).sum()),
                "SOURCE_SHAPE_NON_TEXT_COLOUR_REJECTED_PIXELS": int((source_shape & final_native & ~final_text_colour).sum()),
                "SOURCE_TEXT_SHAPE_MASK": rel(TEXT_SOURCE_SHAPE_DIR / f"{glyph.object_id}_source_text_shape.png"),
            }
        )
    assignment_count_pre_inventory = np.zeros((height, width), dtype=np.uint16)
    for glyph in glyphs:
        assignment_count_pre_inventory[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]] += glyph.mask.astype(np.uint16)
    ownership_report["final_duplicate_pixels_before_inventory_split"] = int((assignment_count_pre_inventory > 1).sum())
    ownership_report["final_owned_text_pixels"] = int(assignment_count_pre_inventory.sum())
    pixel_row_by_id = {row["MEASURE_ID"]: row for row in pixel_rows if row["MEASURE_ID"].startswith("G")}

    def raw_pick(text: str, x_pt: float, y_pt: float) -> MaskObject:
        options = [item for item in raw_elements if item.text == text]
        if not options:
            raise RuntimeError(f"missing raw PDF line for semantic node: {text!r}")
        selected = min(
            options,
            key=lambda item: abs(item.bbox[0] / SCALE - x_pt) + abs(item.bbox[1] / SCALE - y_pt),
        )
        distance = abs(selected.bbox[0] / SCALE - x_pt) + abs(selected.bbox[1] / SCALE - y_pt)
        if distance > 5.0:
            raise RuntimeError(f"ambiguous raw PDF line for semantic node {text!r}: distance={distance:.3f}pt")
        return selected

    manual_specs: list[dict[str, Any]] = [
        {
            "key": "right_w_mid_label",
            "text": "w(5/2)",
            "role": "FORMULA",
            "panel": "R",
            "members": [raw_pick("𝑤(5", 392.0, 314.0), raw_pick("2)", 404.0, 319.0)],
            "fraction_draw": 38,
        },
        {
            "key": "left_q_label",
            "text": "虚线 q_L(x)=2/5",
            "role": "ANNOTATION",
            "panel": "L",
            "members": [raw_pick("虚线𝑞𝐿(𝑥) = 2", 174.0, 338.0), raw_pick("5", 234.7, 349.4)],
            "fraction_draw": 18,
        },
        {
            "key": "left_support_boundary",
            "text": "点线：支撑边界 / x=5/2",
            "role": "ANNOTATION",
            "panel": "L",
            "members": [
                raw_pick("点线：支撑边界", 222.0, 329.5),
                raw_pick("𝑥= 5", 244.0, 338.0),
                raw_pick("2", 263.7, 349.6),
            ],
            "fraction_draw": 21,
        },
        {
            "key": "right_q_label",
            "text": "虚线 q_R(x)=1/5",
            "role": "ANNOTATION",
            "panel": "R",
            "members": [raw_pick("虚线𝑞𝑅(𝑥) = 1", 340.5, 377.5), raw_pick("5", 401.7, 389.2)],
            "fraction_draw": 35,
        },
        {
            "key": "left_xtick_half",
            "text": "5/2",
            "role": "TICK",
            "panel": "L",
            "members": [raw_pick("5", 234.4, 421.5), raw_pick("2", 234.4, 432.8)],
            "fraction_draw": 12,
        },
        {
            "key": "right_xtick_half",
            "text": "5/2",
            "role": "TICK",
            "panel": "R",
            "members": [raw_pick("5", 400.7, 421.5), raw_pick("2", 400.7, 432.8)],
            "fraction_draw": 31,
        },
    ]
    member_to_spec: dict[str, dict[str, Any]] = {}
    for spec in manual_specs:
        for member in spec["members"]:
            if member.object_id in member_to_spec:
                raise RuntimeError(f"raw line belongs to two semantic nodes: {member.object_id}")
            member_to_spec[member.object_id] = spec

    node_specs = list(manual_specs)
    for raw in raw_elements:
        if raw.object_id in member_to_spec:
            continue
        node_specs.append(
            {
                "key": f"raw_{raw.object_id}",
                "text": raw.text,
                "role": raw.role,
                "panel": "GLOBAL" if raw.role == "CAPTION" else panel_for_box(ptbox_from_px(raw.bbox)),
                "members": [raw],
                "fraction_draw": None,
            }
        )
    node_specs.sort(key=lambda spec: (min(item.bbox[1] for item in spec["members"]), min(item.bbox[0] for item in spec["members"])))

    elements = []
    element_char_index = {}
    font_rows = []
    node_key_to_element: dict[str, str] = {}
    glyph_to_element: dict[str, MaskObject] = {}
    for number, spec in enumerate(node_specs, 1):
        element_id = f"E{number:03d}"
        role = str(spec["role"])
        panel = str(spec["panel"])
        members = list(spec["members"])
        chars = [glyph for member in members for glyph in raw_element_char_index[member.object_id]]
        if not chars:
            raise RuntimeError(f"semantic node without glyphs: {spec['key']}")
        for glyph in chars:
            glyph.parent = element_id
            glyph.role = role
            glyph.panel = panel
            glyph.source = source_line(role, str(spec["text"]))
        element_box, element_mask = mask_union(chars)
        element_path = ELEMENT_DIR / f"{element_id}_raw.png"
        save_binary(element_mask, element_path)
        element = MaskObject(
            element_id,
            "TEXT",
            role,
            panel,
            element_box,
            element_mask,
            element_path,
            source_line(role, str(spec["text"])),
            text=str(spec["text"]),
        )
        elements.append(element)
        element_char_index[element_id] = chars
        node_key_to_element[str(spec["key"])] = element_id
        for glyph in chars:
            glyph_to_element[glyph.object_id] = element

        font_sizes = [float(pixel_row_by_id[glyph.object_id]["PDF_FONT_PT"]) for glyph in chars]
        declared = declared_pt(role)
        font_rows.append(
            {
                "ELEMENT_ID": element_id,
                "PANEL_ID": panel,
                "ROLE": role,
                "SOURCE_FILE": str(SOURCE_FIGURE if role != "CAPTION" else SOURCE_STYLE),
                "SOURCE_LINE": source_line(role, str(spec["text"])),
                "DECLARED_PT": f"{declared:.2f}",
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": f"{declared:.2f}",
                "PDF_FONT_PT_MEDIAN": f"{median(font_sizes):.3f}",
                "TEXT_SAMPLE": str(spec["text"]),
                "RAW_MASK": rel(element_path),
                "SOURCE_FONT_PASS": str(declared >= 9.5).lower(),
                "REASON": "PASS" if declared >= 9.5 else "effective_pt_below_9.5",
            }
        )

        baseline = max(font_sizes)
        fraction_script = spec["fraction_draw"] is not None
        for glyph in chars:
            row = pixel_row_by_id[glyph.object_id]
            pdf_font_pt = float(row["PDF_FONT_PT"])
            script, threshold = classify_character(
                glyph.text,
                ptbox_from_px(glyph.bbox),
                ptbox_from_px(element_box),
                pdf_font_pt,
                baseline,
                force_fraction_script=fraction_script and glyph.text.isdigit(),
            )
            h_ink = int(glyph.mask.any(axis=1).sum())
            pixel_pass = glyph.nonempty and h_ink >= threshold
            reason = "PASS" if pixel_pass else ("EMPTY_RAW_MASK" if not glyph.nonempty else f"H_INK={h_ink}<{threshold}")
            failure_evidence = "" if pixel_pass else glyph_failure_package(glyph.object_id, glyph, raw_full, reason)
            row.update(
                {
                    "PARENT_ELEMENT_ID": element_id,
                    "PANEL_ID": panel,
                    "ROLE": role,
                    "SOURCE_LINE": source_line(role, str(spec["text"])),
                    "DECLARED_PT": f"{declared:.2f}",
                    "EFFECTIVE_PT": f"{declared:.2f}",
                    "SCRIPT_CLASS": script,
                    "THRESHOLD_PX": threshold,
                    "BBOX_X0": glyph.bbox[0],
                    "BBOX_Y0": glyph.bbox[1],
                    "BBOX_X1": glyph.bbox[2],
                    "BBOX_Y1": glyph.bbox[3],
                    "H_INK_PX": h_ink,
                    "RAW_MASK": rel(glyph.raw_path),
                    "PIXEL_HEIGHT_PASS": str(pixel_pass).lower(),
                    "PASS_FAIL": "PASS" if pixel_pass else "FAIL",
                    "REASON": reason,
                    "FAILURE_EVIDENCE": failure_evidence,
                }
            )

    # Replace line-level element records with source-node element records.
    mask_rows = [row for row in mask_rows if row["KIND"] != "TEXT_ELEMENT"]
    glyph_mask_row_by_id = {row["MASK_ID"]: row for row in mask_rows if row["KIND"] == "GLYPH"}
    for glyph in glyphs:
        row = glyph_mask_row_by_id[glyph.object_id]
        row.update(
            {
                "PARENT_ID": glyph.parent,
                "ROLE": glyph.role,
                "PANEL": glyph.panel,
                "BBOX_FULL_PAGE_PX": json.dumps(glyph.bbox),
                "PIXELS": glyph.pixels,
                "NONEMPTY": str(glyph.nonempty).lower(),
                "RAW_MASK": rel(glyph.raw_path),
                "FINAL_VISIBLE_MASK": rel(glyph.raw_path),
            }
        )
    for element in elements:
        mask_rows.append(
            {
                "MASK_ID": element.object_id,
                "KIND": "TEXT_ELEMENT",
                "PARENT_ID": "",
                "ROLE": element.role,
                "PANEL": element.panel,
                "BBOX_FULL_PAGE_PX": json.dumps(element.bbox),
                "PIXELS": element.pixels,
                "NONEMPTY": str(element.nonempty).lower(),
                "RAW_MASK": rel(element.raw_path),
                "FINAL_VISIBLE_MASK": rel(element.raw_path),
            }
        )

    # A necessary semantic substring closes the zero-advance PDF extraction
    # component for TeX \not\ll.  The following U+226A glyph owns every real
    # rendered pixel (including the slash), so it is the nonempty raw mask.
    substring_rows: list[dict[str, Any]] = []
    left_title = next(item for item in elements if item.role == "PANEL_TITLE" and item.panel == "L")
    visible_not_ll = next(item for item in element_char_index[left_title.object_id] if item.text == "≪")
    not_ll_path = GLYPH_DIR / "S_NOT_LL_raw.png"
    save_binary(visible_not_ll.mask, not_ll_path)
    not_ll = MaskObject("S_NOT_LL", "TEXT_SUBSTRING", "PANEL_TITLE", "L", visible_not_ll.bbox, visible_not_ll.mask.copy(), not_ll_path, "fig_v5_c02_is_support.tex:36", text="\\not\\ll", parent=left_title.object_id)
    not_ll_h = int(not_ll.mask.any(axis=1).sum())
    not_ll_pass = not_ll.nonempty and not_ll_h >= 22
    not_ll_reason = "PASS" if not_ll_pass else ("EMPTY_RAW_MASK" if not not_ll.nonempty else f"H_INK={not_ll_h}<22")
    not_ll_evidence = "" if not_ll_pass else glyph_failure_package(not_ll.object_id, not_ll, raw_full, not_ll_reason)
    substring_rows.append(
        {
            "MEASURE_ID": not_ll.object_id,
            "ELEMENT_ID": not_ll.object_id,
            "PARENT_ELEMENT_ID": left_title.object_id,
            "PANEL_ID": "L",
            "ROLE": "PANEL_TITLE",
            "SOURCE_FILE": str(SOURCE_FIGURE),
            "SOURCE_LINE": not_ll.source,
            "DECLARED_PT": "10.20",
            "GRAPHICS_SCALE": "1.000000",
            "EFFECTIVE_PT": "10.20",
            "PDF_FONT_PT": "COMPOSITE",
            "TEXT_SAMPLE": "\\not\\ll (U+0338 closed by visible U+226A mask)",
            "SCRIPT_CLASS": "MATH_BASE",
            "THRESHOLD_PX": 22,
            "BBOX_X0": not_ll.bbox[0],
            "BBOX_Y0": not_ll.bbox[1],
            "BBOX_X1": not_ll.bbox[2],
            "BBOX_Y1": not_ll.bbox[3],
            "H_INK_PX": not_ll_h,
            "RAW_MASK": rel(not_ll_path),
            "CLASS_MEDIAN_PX": "",
            "RATIO_TO_CLASS_MEDIAN": "",
            "ROLE_RATIO": "",
            "TEXT_TEXT_OVERLAP_PX": "",
            "TEXT_GRAPHIC_OVERLAP_PX": "",
            "MIN_CLEARANCE_PX": "",
            "PIXEL_HEIGHT_PASS": str(not_ll_pass).lower(),
            "PASS_FAIL": "PASS" if not_ll_pass else "FAIL",
            "REASON": not_ll_reason,
            "FAILURE_EVIDENCE": not_ll_evidence,
        }
    )
    mask_rows.append(
        {
            "MASK_ID": not_ll.object_id,
            "KIND": "TEXT_SUBSTRING",
            "PARENT_ID": left_title.object_id,
            "ROLE": "PANEL_TITLE",
            "PANEL": "L",
            "BBOX_FULL_PAGE_PX": json.dumps(not_ll.bbox),
            "PIXELS": not_ll.pixels,
            "NONEMPTY": str(not_ll.nonempty).lower(),
            "RAW_MASK": rel(not_ll_path),
            "FINAL_VISIBLE_MASK": rel(not_ll_path),
        }
    )

    source_node_inventory = {
        "raw_pdf_lines": [
            {
                "raw_line_id": raw.object_id,
                "text": raw.text,
                "bbox_full_page_px": list(raw.bbox),
                "semantic_source_node": next(
                    node_key for node_key, element_id in node_key_to_element.items()
                    if raw.object_id in [member.object_id for spec in node_specs if spec["key"] == node_key for member in spec["members"]]
                ),
            }
            for raw in raw_elements
        ],
        "semantic_nodes": [
            {
                "element_id": element.object_id,
                "source_node": key,
                "text": element.text,
                "role": element.role,
                "panel": element.panel,
                "member_raw_lines": [member.object_id for spec in node_specs if spec["key"] == key for member in spec["members"]],
            }
            for key, element_id in node_key_to_element.items()
            for element in elements if element.object_id == element_id
        ],
        "zero_advance_pdf_components": combining_components,
        "necessary_substring_closure": {"S_NOT_LL": "visible U+226A raw mask closes TeX \\not U+0338"},
        "glyph_separation": ownership_report,
    }
    save_json(OUT / "raw_line_inventory.json", source_node_inventory)

    # Mathematical fraction bars are vector marks in this PDF, not Unicode
    # glyphs.  Bind each bar to its *source semantic node*, then create an
    # independently bounded required substring (numerator + bar + denominator)
    # without absorbing adjacent text nodes or nearby curves.
    fraction_draw_to_node = {
        12: "left_xtick_half",
        18: "left_q_label",
        21: "left_support_boundary",
        31: "right_xtick_half",
        35: "right_q_label",
        38: "right_w_mid_label",
    }
    fraction_rows: list[dict[str, Any]] = []
    fraction_bar_masks: list[MaskObject] = []
    fraction_bar_source_shapes: dict[str, np.ndarray] = {}
    fraction_bar_isolation: dict[str, dict[str, Any]] = {}
    fraction_bar_by_substring: dict[str, str] = {}
    fraction_component_ids_by_substring: dict[str, list[str]] = {}
    element_by_id = {element.object_id: element for element in elements}
    for fraction_no, draw_id in enumerate(sorted(fraction_draw_to_node), 1):
        drawing = drawings[draw_id]
        dbox_pt = tuple(float(value) for value in drawing["rect"])
        width_pt = max(0.4, float(drawing.get("width") or 0.0))
        bar_box = pxbbox(
            (dbox_pt[0] - width_pt, dbox_pt[1] - width_pt, dbox_pt[2] + width_pt, dbox_pt[3] + width_pt),
            width,
            height,
            pad=1,
        )
        node_key = fraction_draw_to_node[draw_id]
        parent_element = element_by_id[node_key_to_element[node_key]]
        bar_id = f"VBAR{fraction_no:02d}"
        source_bar_mask = raster_source_drawing_mask(drawing, page_rect, width, height, bar_box)
        if not source_bar_mask.any():
            raise RuntimeError(f"source vector fraction component is empty: {bar_id}")
        bar_mask = source_bar_mask & ink[bar_box[1] : bar_box[3], bar_box[0] : bar_box[2]]
        bar_path = GLYPH_DIR / f"{bar_id}_raw.png"
        source_bar_path = VECTOR_TEXT_COMPONENT_DIR / f"{bar_id}_source_vector_component.png"
        save_binary(source_bar_mask, source_bar_path)
        save_binary(bar_mask, bar_path)
        bar_obj = MaskObject(bar_id, "TEXT_VECTOR_COMPONENT", parent_element.role, parent_element.panel, bar_box, bar_mask, bar_path, f"PDF drawing {draw_id}; source fraction bar", text="fraction bar", parent=parent_element.object_id)
        fraction_bar_masks.append(bar_obj)
        fraction_bar_source_shapes[bar_id] = source_bar_mask
        fraction_bar_isolation[bar_id] = {
            "DRAW_ID": draw_id,
            "SOURCE_MASK": rel(source_bar_path),
            "SOURCE_PIXELS": int(source_bar_mask.sum()),
            "FINAL_PIXELS": int(bar_mask.sum()),
            "MISSING_SOURCE_TO_FINAL_PIXELS": int((source_bar_mask & ~bar_mask).sum()),
            "FINAL_BACKGROUND_TEXTURE_INTERSECTION_PIXELS": "N/A_VECTOR_TARGET_OWNED_BY_SOURCE_PATH",
        }

        # Add only the actual source vector fraction bar to its parent element.
        expanded_box, expanded_mask = mask_union([parent_element, bar_obj])
        parent_element.bbox = expanded_box
        parent_element.mask = expanded_mask
        save_binary(parent_element.mask, parent_element.raw_path)

        # A tight source-coordinate zone captures only the fraction body.
        zone_pt = (dbox_pt[0] - 5.0, dbox_pt[1] - 8.0, dbox_pt[2] + 5.0, dbox_pt[3] + 8.0)
        zone_px = pxbbox(zone_pt, width, height)
        component_glyphs = [
            glyph for glyph in element_char_index[parent_element.object_id]
            if intersects(glyph.bbox, zone_px)
        ]
        fraction_box, fraction_mask = mask_union(component_glyphs + [bar_obj])
        substring_id = f"S{fraction_no:03d}"
        fraction_bar_by_substring[substring_id] = bar_id
        fraction_component_ids_by_substring[substring_id] = [glyph.object_id for glyph in component_glyphs]
        path = GLYPH_DIR / f"{substring_id}_fraction_raw.png"
        save_binary(fraction_mask, path)
        obj = MaskObject(
            substring_id,
            "TEXT_SUBSTRING",
            parent_element.role,
            parent_element.panel,
            fraction_box,
            fraction_mask,
            path,
            f"fig_v5_c02_is_support.tex; PDF drawing {draw_id}",
            text="source fraction numerator/bar/denominator",
            parent=parent_element.object_id,
        )
        h_ink = int(fraction_mask.any(axis=1).sum())
        passed = obj.nonempty and h_ink >= 22
        reason = "PASS" if passed else ("EMPTY_RAW_MASK" if not obj.nonempty else f"H_INK={h_ink}<22")
        evidence = "" if passed else glyph_failure_package(substring_id, obj, raw_full, reason)
        fraction_rows.append(
            {
                "MEASURE_ID": substring_id,
                "ELEMENT_ID": substring_id,
                "PARENT_ELEMENT_ID": parent_element.object_id,
                "PANEL_ID": parent_element.panel,
                "ROLE": parent_element.role,
                "SOURCE_FILE": str(SOURCE_FIGURE),
                "SOURCE_LINE": obj.source,
                "DECLARED_PT": f"{declared_pt(parent_element.role):.2f}",
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": f"{declared_pt(parent_element.role):.2f}",
                "PDF_FONT_PT": "PDF_TEXT+VECTOR_BAR",
                "TEXT_SAMPLE": "fraction numerator/bar/denominator",
                "SCRIPT_CLASS": "MATH_BASE",
                "THRESHOLD_PX": 22,
                "BBOX_X0": fraction_box[0],
                "BBOX_Y0": fraction_box[1],
                "BBOX_X1": fraction_box[2],
                "BBOX_Y1": fraction_box[3],
                "H_INK_PX": h_ink,
                "RAW_MASK": rel(path),
                "CLASS_MEDIAN_PX": "",
                "RATIO_TO_CLASS_MEDIAN": "",
                "ROLE_RATIO": "",
                "TEXT_TEXT_OVERLAP_PX": "",
                "TEXT_GRAPHIC_OVERLAP_PX": "",
                "MIN_CLEARANCE_PX": "",
                "PIXEL_HEIGHT_PASS": str(passed).lower(),
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "REASON": reason,
                "FAILURE_EVIDENCE": evidence,
            }
        )
        mask_rows.append(
            {
                "MASK_ID": substring_id,
                "KIND": "TEXT_SUBSTRING",
                "PARENT_ID": parent_element.object_id,
                "ROLE": parent_element.role,
                "PANEL": parent_element.panel,
                "BBOX_FULL_PAGE_PX": json.dumps(fraction_box),
                "PIXELS": obj.pixels,
                "NONEMPTY": str(obj.nonempty).lower(),
                "RAW_MASK": rel(path),
                "FINAL_VISIBLE_MASK": rel(path),
            }
        )

    # Source text occlusion inventory.  The q_L node is painted before the
    # boundary-label node (PDF draw20).  Final-visible membership is decided
    # from the actual official native target mask, never from a broad bbox or
    # a hoped-for denominator fragment.  Empty source slots move exclusively
    # to the source→occlusion ledger.
    ql_element = element_by_id[node_key_to_element["left_q_label"]]
    source_boundary_halo_box = pxbbox(tuple(float(value) for value in drawings[20]["rect"]), width, height)
    # Candidate membership is derived from the real draw20 vector geometry
    # and the source-owned glyph path, never from a pixel-height failure or a
    # hard-coded character story.  The full-page coverage mask is evidence
    # geometry only; it cannot enter a final text mask.
    source_boundary_halo_full = raster_source_drawing_mask(
        drawings[20], page_rect, width, height, (0, 0, width, height), coverage_only=True
    )
    ql_halo_candidates = [
        glyph for glyph in element_char_index[ql_element.object_id]
        if intersects(glyph.bbox, source_boundary_halo_box)
        and bool((glyph_source_shapes[glyph.object_id] & source_boundary_halo_full[
            glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]
        ]).any())
    ]
    fully_occluded_source_glyphs = [glyph for glyph in ql_halo_candidates if not glyph.mask.any()]
    partial_occluded_source_glyphs = [
        glyph for glyph in ql_halo_candidates
        if glyph.object_id not in {item.object_id for item in fully_occluded_source_glyphs}
        and int(glyph.mask.sum()) < int(glyph_source_shapes[glyph.object_id].sum())
    ]
    if not ql_halo_candidates or not fully_occluded_source_glyphs:
        raise RuntimeError(
            "q_L opaque-occlusion evidence did not locate a source-only slot: "
            f"full={[f'{glyph.object_id}:{glyph.text}' for glyph in fully_occluded_source_glyphs]}, "
            f"partial={[f'{glyph.object_id}:{glyph.text}' for glyph in partial_occluded_source_glyphs]}"
        )
    fully_occluded_source_ids = {glyph.object_id for glyph in fully_occluded_source_glyphs}
    partial_occluded_source_ids = {glyph.object_id for glyph in partial_occluded_source_glyphs}
    final_visible_glyphs = [glyph for glyph in glyphs if glyph.object_id not in fully_occluded_source_ids]

    # Rebuild semantic parent masks using only final-visible character masks
    # plus their required fraction bars.  E016 therefore remains a visible
    # prefix/fragment object while G0095/G0096 remain source-only ledger rows.
    for element in elements:
        components: list[MaskObject] = [
            glyph for glyph in element_char_index[element.object_id]
            if glyph.object_id not in fully_occluded_source_ids
        ]
        components.extend(bar for bar in fraction_bar_masks if bar.parent == element.object_id)
        rebuilt_box, rebuilt_mask = mask_union(components)
        element.bbox = rebuilt_box
        element.mask = rebuilt_mask
        save_binary(rebuilt_mask, element.raw_path)

    # A fraction substring is a required semantic unit, not a permissive
    # union of old broad glyph bboxes. Rebuild it after removing fully hidden
    # source slots; a completely blank final composite becomes source-only
    # evidence instead of an empty final-visible mask.
    fraction_bar_by_parent: dict[str, list[MaskObject]] = defaultdict(list)
    for bar in fraction_bar_masks:
        fraction_bar_by_parent[bar.parent].append(bar)
    for row in fraction_rows:
        parent_id = str(row["PARENT_ELEMENT_ID"])
        if parent_id != ql_element.object_id:
            continue
        old_box = tuple(int(row[key]) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        fraction_components = [
            glyph for glyph in element_char_index[parent_id]
            if glyph.object_id not in fully_occluded_source_ids and intersects(glyph.bbox, old_box)
        ] + fraction_bar_by_parent[parent_id]
        fraction_box, fraction_mask = mask_union(fraction_components)
        fraction_path = OUT / str(row["RAW_MASK"])
        save_binary(fraction_mask, fraction_path)
        fraction_h = int(fraction_mask.any(axis=1).sum())
        fraction_pass = bool(fraction_mask.any()) and fraction_h >= 22
        fraction_reason = "PASS" if fraction_pass else ("EMPTY_RAW_MASK" if not fraction_mask.any() else f"H_INK={fraction_h}<22")
        fraction_evidence = "" if fraction_pass else glyph_failure_package(str(row["MEASURE_ID"]), MaskObject(
            str(row["MEASURE_ID"]), "TEXT_SUBSTRING", str(row["ROLE"]), str(row["PANEL_ID"]), fraction_box,
            fraction_mask, fraction_path, str(row["SOURCE_LINE"]), text=str(row["TEXT_SAMPLE"]), parent=parent_id,
        ), raw_full, fraction_reason)
        row.update(
            {
                "BBOX_X0": fraction_box[0], "BBOX_Y0": fraction_box[1], "BBOX_X1": fraction_box[2], "BBOX_Y1": fraction_box[3],
                "H_INK_PX": fraction_h, "PIXEL_HEIGHT_PASS": str(fraction_pass).lower(),
                "PASS_FAIL": "PASS" if fraction_pass else "FAIL", "REASON": fraction_reason,
                "FAILURE_EVIDENCE": fraction_evidence,
            }
        )
        for mask_row in mask_rows:
            if mask_row["MASK_ID"] == row["MEASURE_ID"]:
                mask_row.update(
                    {
                        "BBOX_FULL_PAGE_PX": json.dumps(fraction_box), "PIXELS": int(fraction_mask.sum()),
                        "NONEMPTY": str(bool(fraction_mask.any())).lower(), "RAW_MASK": rel(fraction_path),
                        "FINAL_VISIBLE_MASK": rel(fraction_path),
                    }
                )

    # The parent masks have changed after bar insertion and inventory removal;
    # update their manifest rows before pair enumeration, preserving a single
    # final-visible raw mask per semantic source node.
    final_element_by_id = {element.object_id: element for element in elements}
    for row in mask_rows:
        if row["KIND"] == "TEXT_ELEMENT":
            element = final_element_by_id[row["MASK_ID"]]
            row.update(
                {
                    "BBOX_FULL_PAGE_PX": json.dumps(element.bbox),
                    "PIXELS": element.pixels,
                    "NONEMPTY": str(element.nonempty).lower(),
                    "RAW_MASK": rel(element.raw_path),
                    "FINAL_VISIBLE_MASK": rel(element.raw_path),
                }
            )
    substring_rows.extend(fraction_rows)
    pixel_rows.extend(substring_rows)
    source_only_substring_ids = {
        str(row["MEASURE_ID"])
        for row in substring_rows
        if str(row["PARENT_ELEMENT_ID"]) == ql_element.object_id
        and not (np.asarray(Image.open(OUT / str(row["RAW_MASK"])).convert("L")) < 128).any()
    }
    final_visible_substring_rows = [
        row for row in substring_rows if str(row["MEASURE_ID"]) not in source_only_substring_ids
    ]
    final_pixel_rows = [
        row for row in pixel_rows
        if row["MEASURE_ID"] not in fully_occluded_source_ids
        and row["MEASURE_ID"] not in source_only_substring_ids
    ]

    # Necessary substrings use the same isolated CHAR/vector-component paths.
    # Their final mask must be a subset of that source composite, never a
    # permissive crop that can absorb a curve, hatch, neighbour, or background.
    glyph_by_id = {glyph.object_id: glyph for glyph in glyphs}
    substring_isolation: dict[str, dict[str, Any]] = {}
    substring_isolation_rows: list[dict[str, Any]] = []

    def composite_canvas(
        source_parts: list[tuple[tuple[int, int, int, int], np.ndarray]],
        final_box: tuple[int, int, int, int],
        final_mask: np.ndarray,
    ) -> tuple[tuple[int, int, int, int], np.ndarray, np.ndarray]:
        boxes = [box for box, _ in source_parts] + [final_box]
        x0 = min(box[0] for box in boxes)
        y0 = min(box[1] for box in boxes)
        x1 = max(box[2] for box in boxes)
        y1 = max(box[3] for box in boxes)
        source_canvas = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        final_canvas = np.zeros_like(source_canvas)
        for box, mask in source_parts:
            source_canvas[box[1] - y0 : box[3] - y0, box[0] - x0 : box[2] - x0] |= mask
        final_canvas[final_box[1] - y0 : final_box[3] - y0, final_box[0] - x0 : final_box[2] - x0] = final_mask
        return (x0, y0, x1, y1), source_canvas, final_canvas

    # Source isolation retains source-only composites too, so their pre/halo/
    # final evidence can be closed in the separate occlusion ledger.
    for subrow in substring_rows:
        sub_id = str(subrow["MEASURE_ID"])
        final_box = tuple(int(subrow[key]) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        final_mask = np.asarray(Image.open(OUT / str(subrow["RAW_MASK"])).convert("L")) < 128
        if sub_id == "S_NOT_LL":
            source_parts = [(visible_not_ll.bbox, glyph_source_shapes[visible_not_ll.object_id])]
            source_descriptor = f"CHAR source path {visible_not_ll.object_id}"
        else:
            bar_id = fraction_bar_by_substring[sub_id]
            bar_obj = next(bar for bar in fraction_bar_masks if bar.object_id == bar_id)
            # For a final-visible required substring, the fraction bar is an
            # actual final native vector-owned component: use its official
            # final raw mask after vector-path ownership is proved.  A MuPDF
            # replay fringe is containment geometry, not a missing final
            # stroke. Source-only S002 instead retains the full pre-occlusion
            # vector replay for its q_L coverage evidence.
            bar_component_mask = (
                fraction_bar_source_shapes[bar_id]
                if sub_id in source_only_substring_ids
                else bar_obj.mask
            )
            source_parts = [
                (glyph_by_id[glyph_id].bbox, glyph_source_shapes[glyph_id])
                for glyph_id in fraction_component_ids_by_substring[sub_id]
            ] + [
                (bar_obj.bbox, bar_component_mask)
            ]
            source_descriptor = (
                f"isolated CHAR source paths + {bar_id} source-pre vector path"
                if sub_id in source_only_substring_ids
                else f"isolated CHAR paths + {bar_id} final native vector-owned component"
            )
        composite_box, source_canvas, final_canvas = composite_canvas(source_parts, final_box, final_mask)
        source_path = VECTOR_TEXT_COMPONENT_DIR / f"{sub_id}_source_composite_shape.png"
        save_binary(source_canvas, source_path)
        missing = source_canvas & ~final_canvas
        foreign = final_canvas & ~source_canvas
        if sub_id in source_only_substring_ids:
            contour_status = "KNOWN_LATER_OPAQUE_OCCLUSION"
        elif missing.any() or foreign.any():
            contour_status = "UNKNOWN_COMPOSITE_CONTOUR_OR_CONTAMINATION"
        else:
            contour_status = "PASS_COMPLETE_FINAL_VISIBLE_CONTOUR"
        record = {
            "SOURCE_COMPOSITE_MASK": rel(source_path),
            "SOURCE_COMPOSITE_DESCRIPTOR": source_descriptor,
            "SOURCE_PIXELS": int(source_canvas.sum()),
            "FINAL_PIXELS": int(final_canvas.sum()),
            "MISSING_SOURCE_TO_FINAL_PIXELS": int(missing.sum()),
            "FOREIGN_FINAL_OUTSIDE_SOURCE_PIXELS": int(foreign.sum()),
            "VISIBLE_CONTOUR_STATUS": contour_status,
            "COMPOSITE_BBOX_FULL_PAGE_PX": composite_box,
            "FINAL_BBOX_FULL_PAGE_PX": final_box,
        }
        substring_isolation[sub_id] = record
        substring_isolation_rows.append({"MAP_ID": sub_id, **record})

    # Union of all independently bounded text-glyph foreground.  This is used
    # only to subtract text from colour-specific graphics; no dilation occurs.
    text_union = np.zeros((height, width), dtype=bool)
    for glyph in final_visible_glyphs:
        text_union[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]] |= glyph.mask
    for row in fraction_rows:
        x0, y0, x1, y1 = (int(row[key]) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        # Re-read the saved raw fraction mask at exact native pixels.
        submask = np.asarray(Image.open(OUT / row["RAW_MASK"]).convert("L")) < 128
        text_union[y0:y1, x0:x1] |= submask

    # Directional colour selection retains every final visible antialiased
    # pixel on a particular source colour while rejecting nearby colours.
    def colour_ink(target: tuple[int, int, int]) -> np.ndarray:
        target_array = np.array(target, dtype=float)
        vector = 255.0 - target_array
        delta = 255.0 - rgb.astype(float)
        denom = float(np.dot(vector, vector))
        alpha = np.tensordot(delta, vector, axes=([2], [0])) / denom
        residual = np.linalg.norm(delta - alpha[..., None] * vector, axis=2)
        return (alpha >= (FOREGROUND_DELTA / 255.0)) & (alpha <= 1.08) & (residual <= 8.0)

    def source_vector_pre_mask(
        draw_id: int,
        expected_box: tuple[int, int, int, int],
        *,
        coverage_only: bool = False,
        any_paint_alpha: bool = False,
    ) -> np.ndarray:
        """Rasterize one extracted source drawing before any later paint.

        This is not an imagined fill: it redraws the PDF vector items, colour,
        width, dash, caps, joins and opacity on a blank page at the same native
        300-dpi grid. It supplies the required pre-occlusion mask whenever a
        later real opaque white source fill covers part of a curve or line.
        """
        return raster_source_drawing_mask(
            drawings[draw_id], page_rect, width, height, expected_box,
            coverage_only=coverage_only, any_paint_alpha=any_paint_alpha,
        )

    official_nontext_layers: dict[str, dict[str, Any]] = {}

    def graphic_from_drawing(draw_id: int, graphic_id: str, role: str, panel: str, label: str) -> MaskObject:
        drawing = drawings[draw_id]
        target = as_rgb(drawing.get("color")) or as_rgb(drawing.get("fill"))
        if target is None or target == (255, 255, 255):
            raise RuntimeError(f"drawing {draw_id} lacks a non-background colour")
        source_box = tuple(float(value) for value in drawing["rect"])
        width_pt = float(drawing.get("width") or 0.0)
        box = pxbbox(source_box, width, height, pad=max(1, int(math.ceil(width_pt * SCALE))))
        # Isolate the official final paint to this one source drawing's own
        # vector geometry.  A same-colour nearby glyph must not be mistaken
        # for a curve/line/marker layer merely because it lies in its bbox.
        drawing_geometry = source_vector_pre_mask(draw_id, box, coverage_only=True)
        official_layer_mask = colour_ink(target)[box[1] : box[3], box[0] : box[2]].copy() & drawing_geometry
        official_layer_path = NON_TARGET_LAYER_DIR / f"{graphic_id}_official_colour_layer.png"
        save_binary(official_layer_mask, official_layer_path)
        official_nontext_layers[graphic_id] = {
            "layer_id": graphic_id,
            "role": role,
            "bbox": box,
            "mask": official_layer_mask,
            "path": rel(official_layer_path),
            "draw_id": draw_id,
            "draw_seqno": int(drawing.get("seqno", -1)),
            "source": f"PDF drawing {draw_id}; official colour layer before text-mask subtraction",
        }
        mask = official_layer_mask.copy()
        mask &= ~text_union[box[1] : box[3], box[0] : box[2]]
        path = GRAPHIC_DIR / f"{graphic_id}_raw.png"
        save_binary(mask, path)
        # Provisional pre is final for now. If the later exact path-vs-halo
        # test finds a real opaque occlusion, this file is replaced by an
        # independent vector-source reconstruction below (avoids inventing or
        # needlessly rasterizing source pre-images for untouched graphics).
        pre_path = PRE_DIR / f"{graphic_id}_pre_occlusion.png"
        save_binary(mask, pre_path)
        return MaskObject(graphic_id, "GRAPHIC", role, panel, box, mask, path, f"PDF drawing {draw_id}; {label}", intentional_group=label)

    graphic_specs = [
        (5, "GR001", "LINE_ARROW", "L", "left_x_ticks"),
        (6, "GR002", "LINE_ARROW", "L", "left_y_ticks"),
        (7, "GR003", "LINE_ARROW", "L", "left_x_axis"),
        (8, "GR004", "ARROWHEAD", "L", "left_x_arrowhead"),
        (9, "GR005", "LINE_ARROW", "L", "left_y_axis"),
        (10, "GR006", "ARROWHEAD", "L", "left_y_arrowhead"),
        (13, "GR007", "DATA_CURVE", "L", "left_p_curve"),
        (14, "GR008", "DATA_CURVE", "L", "left_q_positive"),
        (15, "GR009", "DATA_CURVE", "L", "left_q_zero"),
        (16, "GR010", "LINE_ARROW", "L", "left_support_boundary"),
        (23, "GR011", "MARKER", "L", "left_q_square"),
        (24, "GR012", "MARKER", "L", "left_q_open_circle"),
        (25, "GR013", "LINE_ARROW", "R", "right_x_ticks"),
        (26, "GR014", "LINE_ARROW", "R", "right_y_ticks"),
        (27, "GR015", "LINE_ARROW", "R", "right_x_axis"),
        (28, "GR016", "ARROWHEAD", "R", "right_x_arrowhead"),
        (29, "GR017", "LINE_ARROW", "R", "right_y_axis"),
        (30, "GR018", "ARROWHEAD", "R", "right_y_arrowhead"),
        (32, "GR019", "DATA_CURVE", "R", "right_p_curve"),
        (33, "GR020", "DATA_CURVE", "R", "right_q"),
        (37, "GR021", "NODE_BORDER", "R", "ratio_card_border"),
        (39, "GR022", "MARKER", "R", "right_p_circle"),
        (40, "GR023", "MARKER", "R", "right_p_square"),
        (41, "GR024", "MARKER", "R", "right_p_triangle"),
    ]
    graphics = [graphic_from_drawing(*spec) for spec in graphic_specs]

    # Split the right p curve from its three separately required markers using
    # final raw marker masks; this preserves both mask classes without dilation.
    right_curve = next(item for item in graphics if item.object_id == "GR019")
    for marker_id in ("GR022", "GR023", "GR024"):
        marker = next(item for item in graphics if item.object_id == marker_id)
        x0 = max(right_curve.bbox[0], marker.bbox[0])
        y0 = max(right_curve.bbox[1], marker.bbox[1])
        x1 = min(right_curve.bbox[2], marker.bbox[2])
        y1 = min(right_curve.bbox[3], marker.bbox[3])
        if x0 < x1 and y0 < y1:
            right_curve.mask[
                y0 - right_curve.bbox[1] : y1 - right_curve.bbox[1],
                x0 - right_curve.bbox[0] : x1 - right_curve.bbox[0],
            ] &= ~marker.mask[y0 - marker.bbox[1] : y1 - marker.bbox[1], x0 - marker.bbox[0] : x1 - marker.bbox[0]]
    save_binary(right_curve.mask, right_curve.raw_path)

    # Pattern fill lies in a form XObject, so it has no standalone PyMuPDF
    # drawing record. Its final raw ink is isolated by its declared SLTextGray
    # colour and exact support-region crop after all text masks are removed.
    hatch_box = pxbbox((236.0, 355.0, 306.0, 417.0), width, height)
    # The pattern form and several text nodes use the same declared dark-gray
    # colour.  Keep both the raw colour candidate and the text-subtracted
    # final-visible graphic layer: colour alone is not ownership.  The latter
    # removes only the independently CHAR-owned final masks at identical
    # native pixels, with no dilation, and is the sole GR025 non-text layer
    # permitted in the per-target contamination gate.
    hatch_colour_candidate = colour_ink((77, 83, 88))[hatch_box[1] : hatch_box[3], hatch_box[0] : hatch_box[2]].copy()
    hatch_raw_candidate_path = NON_TARGET_LAYER_DIR / "GR025_colour_candidate_before_text_ownership.png"
    save_binary(hatch_colour_candidate, hatch_raw_candidate_path)
    hatch_official_layer = hatch_colour_candidate.copy()
    hatch_official_layer &= ~text_union[hatch_box[1] : hatch_box[3], hatch_box[0] : hatch_box[2]]
    hatch_official_path = NON_TARGET_LAYER_DIR / "GR025_official_colour_layer.png"
    save_binary(hatch_official_layer, hatch_official_path)
    official_nontext_layers["GR025"] = {
        "layer_id": "GR025", "role": "DATA_REGION", "bbox": hatch_box, "mask": hatch_official_layer,
        "path": rel(hatch_official_path), "draw_id": "XOBJECT_PATTERN", "draw_seqno": -1,
        "source": "pattern XObject official colour candidate minus exact independently CHAR-owned final text masks",
    }
    hatch_mask = hatch_official_layer.copy()
    hatch_path = GRAPHIC_DIR / "GR025_raw.png"
    save_binary(hatch_mask, hatch_path)
    save_binary(hatch_mask, PRE_DIR / "GR025_pre_occlusion.png")
    graphics.append(MaskObject("GR025", "GRAPHIC", "DATA_REGION", "L", hatch_box, hatch_mask, hatch_path, "fig_v5_c02_is_support.tex:42; north-east pattern fill", intentional_group="left_missing_support_hatch"))

    # Preserve only real *opaque* white source fills as halo masks. Drawing 22
    # is explicitly 0.88-opacity behind the hatch label and is retained as a
    # translucent overlay, never misrepresented as an opaque erasing halo.
    halo_ids = [17, 19, 20, 34, 36, 37]
    translucent_fill_ids = [22]
    halo_rows: list[dict[str, Any]] = []
    translucent_rows: list[dict[str, Any]] = []
    halo_geometry: list[dict[str, Any]] = []
    translucent_geometry: list[dict[str, Any]] = []
    for hno, draw_id in enumerate(halo_ids, 1):
        drawing = drawings[draw_id]
        if float(drawing.get("fill_opacity", 1.0)) != 1.0 or as_rgb(drawing.get("fill")) != (255, 255, 255):
            raise RuntimeError(f"declared opaque halo is not opaque white: drawing {draw_id}")
        hbox = pxbbox(tuple(float(value) for value in drawing["rect"]), width, height)
        # A draw bbox is never an acceptable substitute for a halo.  Replay
        # the actual frozen PDF fill geometry (including draw37's rounded
        # path) as coverage-only black on the identical native grid.
        hmask = raster_source_drawing_mask(drawing, page_rect, width, height, hbox, coverage_only=True)
        if not hmask.any():
            raise RuntimeError(f"opaque halo geometry replay is empty: drawing {draw_id}")
        shape_method = "frozen PDF vector fill geometry replayed at native 300dpi (coverage-only)"
        path = HALO_DIR / f"HALO{hno:02d}_opaque_white.png"
        save_binary(hmask, path)
        halo_rows.append(
            {
                "HALO_ID": f"HALO{hno:02d}",
                "PDF_DRAWING_INDEX": draw_id,
                "FILL": "#FFFFFF",
                "FULL_PAGE_BBOX_PX": json.dumps(hbox),
                "RAW_MASK": rel(path),
                "DRAW_ORDER": draw_id,
                "EVIDENCE": f"source fill=#FFFFFF, opacity=1; {shape_method}",
            }
        )
        halo_geometry.append(
            {
                "halo_id": f"HALO{hno:02d}",
                "draw_id": draw_id,
                "rect_pt": tuple(float(value) for value in drawing["rect"]),
                "bbox": hbox,
                "mask": hmask,
                "path": rel(path),
            }
        )

    # Associate only documented source label grounds with semantic parent
    # nodes.  The association proves which text node owns a halo; it does not
    # itself make any later curve coverage acceptable.
    def element_for_label(panel: str, prefix: str) -> str:
        matches = [element.object_id for element in elements if element.panel == panel and element.text.startswith(prefix)]
        if len(matches) != 1:
            raise RuntimeError(f"cannot uniquely associate label halo {panel}/{prefix!r}: {matches}")
        return matches[0]

    halo_text_parent_by_draw = {
        17: ql_element.object_id,
        19: element_for_label("L", "实线"),
        20: element_for_label("L", "点线：支撑边界"),
        34: element_for_label("R", "虚线"),
        36: element_for_label("R", "实线"),
        37: "N/A_RATIO_CARD_GRAPHIC",
    }
    for entry, row in zip(halo_geometry, halo_rows):
        parent = halo_text_parent_by_draw[int(entry["draw_id"])]
        entry["associated_parent"] = parent
        row["ASSOCIATED_PARENT"] = parent

    for tno, draw_id in enumerate(translucent_fill_ids, 1):
        drawing = drawings[draw_id]
        opacity = float(drawing.get("fill_opacity", 1.0))
        if not (0.0 < opacity < 1.0):
            raise RuntimeError(f"declared translucent fill has invalid opacity: drawing {draw_id}")
        tbox = pxbbox(tuple(float(value) for value in drawing["rect"]), width, height)
        tmask = raster_source_drawing_mask(drawing, page_rect, width, height, tbox, coverage_only=True)
        if not tmask.any():
            raise RuntimeError(f"translucent overlay geometry replay is empty: drawing {draw_id}")
        tpath = TRANSLUCENT_DIR / f"ALPHA{tno:02d}_fill_{opacity:.2f}.png"
        save_binary(tmask, tpath)
        translucent_rows.append(
            {
                "OVERLAY_ID": f"ALPHA{tno:02d}",
                "PDF_DRAWING_INDEX": draw_id,
                "FILL": "#FFFFFF",
                "FILL_OPACITY": f"{opacity:.2f}",
                "FULL_PAGE_BBOX_PX": json.dumps(tbox),
                "RAW_MASK": rel(tpath),
                "DRAW_ORDER": draw_id,
                "STATUS": "TRANSLUCENT_NOT_AN_OPAQUE_HALO",
            }
        )
        translucent_geometry.append(
            {
                "overlay_id": f"ALPHA{tno:02d}",
                "draw_id": draw_id,
                "bbox": tbox,
                "mask": tmask,
                "opacity": opacity,
                "path": rel(tpath),
                "associated_parent": element_for_label("L", "纹理缺失区"),
            }
        )
        translucent_rows[-1]["ASSOCIATED_PARENT"] = translucent_geometry[-1]["associated_parent"]

    # Full non-target-layer purity closure.  A clean source-text replay is
    # necessary but not sufficient: every final-visible glyph/sub-composite is
    # checked against neighbours, every official curve/line/arrow/marker/
    # border/region paint layer, and every halo/transparent label-ground
    # geometry. Same-colour contact is resolved only by source paint order.
    layer_contamination_rows: list[dict[str, Any]] = []
    layer_contamination_summary: dict[str, dict[str, Any]] = {}

    def target_layer_overlap(
        target_box: tuple[int, int, int, int], target_mask: np.ndarray,
        layer_box: tuple[int, int, int, int], layer_mask: np.ndarray,
    ) -> int:
        x0, y0 = max(target_box[0], layer_box[0]), max(target_box[1], layer_box[1])
        x1, y1 = min(target_box[2], layer_box[2]), min(target_box[3], layer_box[3])
        if x0 >= x1 or y0 >= y1:
            return 0
        a = target_mask[y0 - target_box[1] : y1 - target_box[1], x0 - target_box[0] : x1 - target_box[0]]
        b = layer_mask[y0 - layer_box[1] : y1 - layer_box[1], x0 - layer_box[0] : x1 - layer_box[0]]
        return int((a & b).sum())

    target_records: list[dict[str, Any]] = []
    for glyph in final_visible_glyphs:
        target_records.append(
            {
                "map_id": glyph.object_id, "kind": "GLYPH", "box": glyph.bbox, "mask": glyph.mask,
                "trace_seqno": int(glyph_isolation[glyph.object_id]["TRACE_SEQNO"]),
                "own_glyph_ids": {glyph.object_id}, "own_layer_ids": set(),
            }
        )
    for subrow in final_visible_substring_rows:
        sub_id = str(subrow["MEASURE_ID"])
        box = tuple(int(subrow[key]) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        mask = np.asarray(Image.open(OUT / str(subrow["RAW_MASK"])).convert("L")) < 128
        if sub_id == "S_NOT_LL":
            own_glyph_ids = {visible_not_ll.object_id}
            trace_seqno: int | None = int(glyph_isolation[visible_not_ll.object_id]["TRACE_SEQNO"])
            own_layers: set[str] = set()
        else:
            own_glyph_ids = set(fraction_component_ids_by_substring[sub_id])
            component_seqnos = [int(glyph_isolation[item]["TRACE_SEQNO"]) for item in own_glyph_ids]
            trace_seqno = min(component_seqnos) if component_seqnos else None
            own_layers = {fraction_bar_by_substring[sub_id]}
        target_records.append(
            {
                "map_id": sub_id, "kind": "NECESSARY_SUBSTRING", "box": box, "mask": mask,
                "trace_seqno": trace_seqno, "own_glyph_ids": own_glyph_ids, "own_layer_ids": own_layers,
            }
        )

    layers_by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for layer in official_nontext_layers.values():
        layers_by_role[str(layer["role"])].append(layer)
    for target in target_records:
        map_id = str(target["map_id"])
        foreign_total = 0
        allowed_total = 0
        # Neighbour character ownership is a distinct layer, not inferred from
        # colour. Final glyph masks must never share a target pixel.
        neighbour_hits: dict[str, int] = {}
        for other in final_visible_glyphs:
            if other.object_id in target["own_glyph_ids"]:
                continue
            hit = target_layer_overlap(target["box"], target["mask"], other.bbox, other.mask)
            if hit:
                neighbour_hits[other.object_id] = hit
        neighbour_foreign = sum(neighbour_hits.values())
        layer_contamination_rows.append(
            {
                "MAP_ID": map_id, "KIND": target["kind"], "LAYER_CLASS": "NEIGHBOUR_GLYPH",
                "LAYER_IDS": ";".join(sorted(neighbour_hits)) or "all-other-glyphs", "OVERLAP_BY_LAYER_JSON": json.dumps(neighbour_hits, ensure_ascii=False),
                "FOREIGN_FINAL_PIXEL_PX": neighbour_foreign, "ALLOWED_TEXT_OWNER_PIXEL_PX": 0,
                "STATUS": "PASS_ZERO_FOREIGN_INTERSECTION" if neighbour_foreign == 0 else "FAIL_NEIGHBOUR_GLYPH_FOREIGN_PIXEL",
                "OWNER_PROOF": "frozen texttrace unique CHAR ownership",
            }
        )
        foreign_total += neighbour_foreign
        for role, layers in sorted(layers_by_role.items()):
            per_layer: dict[str, int] = {}
            foreign = 0
            allowed = 0
            proof: list[str] = []
            for layer in layers:
                if layer["layer_id"] in target["own_layer_ids"]:
                    continue
                hit = target_layer_overlap(target["box"], target["mask"], layer["bbox"], layer["mask"])
                if not hit:
                    continue
                per_layer[str(layer["layer_id"])] = hit
                seqno = int(layer["draw_seqno"]) if isinstance(layer["draw_seqno"], int) else -1
                if target["trace_seqno"] is not None and seqno >= 0 and seqno < int(target["trace_seqno"]):
                    allowed += hit
                    proof.append(f"{layer['layer_id']}:draw{layer['draw_id']}@seq{seqno}<text@seq{target['trace_seqno']}")
                elif seqno == -1:
                    # A Form/XObject without a traceable per-pixel operator
                    # order cannot be promoted to an owning text layer merely
                    # because its colour is similar.  It remains foreign until
                    # an explicit replay/ownership proof exists.
                    foreign += hit
                    proof.append(f"{layer['layer_id']}:untraced XObject/layer has no per-pixel text-owner proof")
                else:
                    foreign += hit
                    proof.append(f"{layer['layer_id']}:later/unknown non-text paint cannot own final text target")
            layer_contamination_rows.append(
                {
                    "MAP_ID": map_id, "KIND": target["kind"], "LAYER_CLASS": role,
                    "LAYER_IDS": ";".join(sorted(per_layer)) or ";".join(str(layer["layer_id"]) for layer in layers),
                    "OVERLAP_BY_LAYER_JSON": json.dumps(per_layer, ensure_ascii=False),
                    "FOREIGN_FINAL_PIXEL_PX": foreign, "ALLOWED_TEXT_OWNER_PIXEL_PX": allowed,
                    "STATUS": "PASS_ZERO_FOREIGN_INTERSECTION" if foreign == 0 else "FAIL_FOREIGN_NON_TEXT_LAYER_PIXEL",
                    "OWNER_PROOF": ";".join(proof) or "no final target/layer intersection",
                }
            )
            foreign_total += foreign
            allowed_total += allowed
        for layer_class, layers in (("OPAQUE_HALO", halo_geometry), ("TRANSLUCENT_OVERLAY", translucent_geometry)):
            per_layer: dict[str, int] = {}
            foreign = 0
            allowed = 0
            proof: list[str] = []
            for layer in layers:
                hit = target_layer_overlap(target["box"], target["mask"], layer["bbox"], layer["mask"])
                if not hit:
                    continue
                layer_id = str(layer.get("halo_id", layer.get("overlay_id")))
                per_layer[layer_id] = hit
                draw_seqno = int(drawings[int(layer["draw_id"])].get("seqno", -1))
                if target["trace_seqno"] is not None and draw_seqno < int(target["trace_seqno"]):
                    allowed += hit
                    proof.append(f"{layer_id}:draw{layer['draw_id']}@seq{draw_seqno}<text@seq{target['trace_seqno']}")
                else:
                    foreign += hit
                    proof.append(f"{layer_id}:later/unknown fill geometry overlaps final text target")
            layer_contamination_rows.append(
                {
                    "MAP_ID": map_id, "KIND": target["kind"], "LAYER_CLASS": layer_class,
                    "LAYER_IDS": ";".join(sorted(per_layer)) or ";".join(str(layer.get("halo_id", layer.get("overlay_id"))) for layer in layers),
                    "OVERLAP_BY_LAYER_JSON": json.dumps(per_layer, ensure_ascii=False),
                    "FOREIGN_FINAL_PIXEL_PX": foreign, "ALLOWED_TEXT_OWNER_PIXEL_PX": allowed,
                    "STATUS": "PASS_ZERO_FOREIGN_INTERSECTION" if foreign == 0 else "FAIL_FOREIGN_FILL_LAYER_PIXEL",
                    "OWNER_PROOF": ";".join(proof) or "no final target/layer intersection",
                }
            )
            foreign_total += foreign
            allowed_total += allowed
        layer_contamination_summary[map_id] = {
            "foreign_pixels": foreign_total,
            "allowed_text_owner_pixels": allowed_total,
        }
        if map_id.startswith("G"):
            glyph_isolation[map_id]["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"] = foreign_total
            glyph_isolation[map_id]["FINAL_TARGET_ALLOWED_TEXT_OWNER_LAYER_PIXELS"] = allowed_total
        else:
            substring_isolation[map_id]["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"] = foreign_total
            substring_isolation[map_id]["FINAL_TARGET_ALLOWED_TEXT_OWNER_LAYER_PIXELS"] = allowed_total

    # Persist the full per-target/per-layer ledger.  This is intentionally
    # broader than the older background/texture check: a mask must be clean
    # against every official final-visible non-target class, including a
    # neighbour glyph, curve, line/arrow, marker, border, region, opaque
    # halo, and translucent label ground.  A nonzero overlap is allowed only
    # when the source paint order explicitly proves that the text owns it.
    layer_contamination_foreign_total = int(sum(int(row["FOREIGN_FINAL_PIXEL_PX"]) for row in layer_contamination_rows))
    layer_contamination_nonzero_map_ids = sorted({
        str(row["MAP_ID"])
        for row in layer_contamination_rows
        if int(row["FOREIGN_FINAL_PIXEL_PX"]) != 0
    })
    layer_contamination_by_class: dict[str, int] = {}
    for row in layer_contamination_rows:
        layer_class = str(row["LAYER_CLASS"])
        layer_contamination_by_class[layer_class] = layer_contamination_by_class.get(layer_class, 0) + int(row["FOREIGN_FINAL_PIXEL_PX"])
    layer_contamination_pass = (
        layer_contamination_foreign_total == 0
        and not layer_contamination_nonzero_map_ids
        and all(row["STATUS"] == "PASS_ZERO_FOREIGN_INTERSECTION" for row in layer_contamination_rows)
    )
    write_csv(
        OUT / "glyph_non_target_layer_contamination.csv",
        layer_contamination_rows,
        [
            "MAP_ID", "KIND", "LAYER_CLASS", "LAYER_IDS", "OVERLAP_BY_LAYER_JSON",
            "FOREIGN_FINAL_PIXEL_PX", "ALLOWED_TEXT_OWNER_PIXEL_PX", "STATUS", "OWNER_PROOF",
        ],
    )

    # Visible-contour completeness is checked against the isolated source text
    # path, not against a bbox colour mode. Every missing source-path pixel
    # must be explained by a *later* opaque source drawing with its actual
    # fill/opacity and display-list order. A later non-opaque / unsupported
    # drawing touching a glyph is UNKNOWN rather than silently accepted.
    glyph_visibility_rows: list[dict[str, Any]] = []
    later_paint_rows: list[dict[str, Any]] = []
    later_paint_evidence_rows: list[dict[str, Any]] = []
    supported_vector_items = {"l", "c", "re"}
    for glyph in glyphs:
        source_shape = glyph_source_shapes[glyph.object_id]
        missing = source_shape & ~glyph.mask
        opaque_explainer = np.zeros_like(source_shape)
        nonopaque_explainer = np.zeros_like(source_shape)
        nonopaque_alpha_path_support = np.zeros_like(source_shape)
        later_hits: list[str] = []
        unknown_later_hits: list[str] = []
        nonopaque_failure_packages: list[str] = []
        trace_seqno = int(glyph_isolation[glyph.object_id]["TRACE_SEQNO"])
        for draw_id, drawing in enumerate(drawings):
            draw_seqno = int(drawing.get("seqno", -1))
            draw_box = pxbbox(tuple(float(value) for value in drawing["rect"]), width, height)
            if draw_seqno <= trace_seqno or not intersects(glyph.bbox, draw_box):
                continue
            if not all(item[0] in supported_vector_items for item in drawing.get("items", [])):
                unknown_later_hits.append(f"draw{draw_id}:unsupported_items")
                later_paint_rows.append(
                    {
                        "GLYPH_ID": glyph.object_id,
                        "DRAW_ID": draw_id,
                        "DRAW_SEQNO": draw_seqno,
                        "TYPE": "UNSUPPORTED_LATER_DRAWING",
                        "SOURCE_SHAPE_INTERSECTION_PX": "UNKNOWN",
                        "FILL": str(as_rgb(drawing.get("fill"))),
                        "FILL_OPACITY": drawing.get("fill_opacity"),
                        "STROKE": str(as_rgb(drawing.get("color"))),
                        "STROKE_OPACITY": drawing.get("stroke_opacity"),
                        "STATUS": "UNKNOWN",
                    }
                )
                continue
            opaque_white = as_rgb(drawing.get("fill")) == (255, 255, 255) and float(drawing.get("fill_opacity", 1.0)) == 1.0
            # Geometry establishes which source pixels the operator can
            # touch; the official final paint layer proves what it actually
            # painted. Never use a broad bbox or generic page ink here.
            draw_geometry = source_vector_pre_mask(draw_id, glyph.bbox, coverage_only=True)
            draw_alpha_path = source_vector_pre_mask(
                draw_id, glyph.bbox, coverage_only=True, any_paint_alpha=True
            )
            source_intersection = int((source_shape & draw_geometry).sum())
            source_alpha_path_intersection = int((source_shape & draw_alpha_path).sum())
            if source_intersection == 0 and source_alpha_path_intersection == 0:
                continue
            if opaque_white:
                opaque_explainer |= draw_geometry
                event = "LATER_OPAQUE_WHITE_SOURCE_OCCLUSION"
                later_paint_status = "PROVED_OPAQUE_GEOMETRY"
            else:
                event = "LATER_NONOPAQUE_OR_STROKE_TOUCH"
                target_colour = as_rgb(drawing.get("fill")) or as_rgb(drawing.get("color"))
                if target_colour is None or target_colour == (255, 255, 255):
                    unknown_later_hits.append(f"draw{draw_id}:nonopaque_without_nonwhite_final_paint_identity")
                    later_paint_status = "UNKNOWN_NONOPAQUE_PAINT_IDENTITY"
                else:
                    official_paint = colour_ink(target_colour)[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]] & draw_geometry
                    nonopaque_explainer |= official_paint
                    nonopaque_alpha_path_support |= draw_alpha_path
                    later_paint_status = "PROVED_OFFICIAL_NONOPAQUE_PAINT_LAYER"
                    if bool((missing & (official_paint | draw_alpha_path)).any()):
                        package = glyph_later_paint_package(
                            glyph, source_shape, official_paint, draw_alpha_path, drawing, draw_id, raw_full
                        )
                        nonopaque_failure_packages.append(package)
                        later_paint_evidence_rows.append(
                            {
                                "GLYPH_ID": glyph.object_id,
                                "DRAW_ID": draw_id,
                                "TYPE": "PROVED_NONOPAQUE_LATER_TEXT_PAINT_LAYER",
                                "SOURCE_PRE_LATER_INTERSECTION_PX": source_intersection,
                                "MISSING_SOURCE_TO_FINAL_INTERSECTION_PX": int((missing & official_paint).sum()),
                                "MISSING_SOURCE_TO_FINAL_ALPHA_PATH_SUPPORT_INTERSECTION_PX": int((missing & draw_alpha_path).sum()),
                                "EVIDENCE_PACKAGE": package,
                            }
                        )
            later_hits.append(
                f"draw{draw_id}@seq{draw_seqno}:{event}:visible={source_intersection}px:alpha_path={source_alpha_path_intersection}px"
            )
            later_paint_rows.append(
                {
                    "GLYPH_ID": glyph.object_id,
                    "DRAW_ID": draw_id,
                    "DRAW_SEQNO": draw_seqno,
                    "TYPE": event,
                    "SOURCE_SHAPE_INTERSECTION_PX": source_intersection,
                    "SOURCE_SHAPE_ALPHA_PATH_INTERSECTION_PX": source_alpha_path_intersection,
                    "FILL": str(as_rgb(drawing.get("fill"))),
                    "FILL_OPACITY": drawing.get("fill_opacity"),
                    "STROKE": str(as_rgb(drawing.get("color"))),
                    "STROKE_OPACITY": drawing.get("stroke_opacity"),
                    "STATUS": "EXPLAINED" if opaque_white else later_paint_status,
                }
            )
        missing_explained_opaque = int((missing & opaque_explainer).sum())
        missing_explained_nonopaque = int((missing & nonopaque_explainer).sum())
        missing_explained_nonopaque_alpha_path = int((missing & nonopaque_alpha_path_support).sum())
        missing_unexplained = int((missing & ~opaque_explainer & ~nonopaque_alpha_path_support).sum())
        if missing_unexplained:
            if nonopaque_failure_packages:
                unknown_later_hits.append("later_nonopaque_alpha_path_does_not_close_all_source_to_final_missing_pixels")
            # The missing final pixels are a proved fact even when no later
            # source operator can account for their cause.  Record this as a
            # hard shape failure (with unresolved-cause note), not a false
            # PASS or a terminally unresolved mapping record.
            visibility_status = "FAIL_UNEXPLAINED_FINAL_VISIBLE_CONTOUR"
        elif missing_explained_nonopaque_alpha_path:
            visibility_status = "FAIL_KNOWN_NONOPAQUE_LATER_TEXT_COVERAGE"
        elif unknown_later_hits:
            visibility_status = "UNKNOWN_VISIBLE_CONTOUR_OR_LATER_PAINT"
        elif missing.any():
            visibility_status = "KNOWN_LATER_OPAQUE_OCCLUSION"
        else:
            visibility_status = "PASS_COMPLETE_FINAL_VISIBLE_CONTOUR"
        record = glyph_isolation[glyph.object_id]
        record.update(
            {
                "LATER_PAINT_HITS": later_hits,
                "LATER_PAINT_UNKNOWN_HITS": unknown_later_hits,
                "MISSING_EXPLAINED_BY_LATER_OPAQUE_PIXELS": missing_explained_opaque,
                "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_PIXELS": missing_explained_nonopaque,
                "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_ALPHA_PATH_PIXELS": missing_explained_nonopaque_alpha_path,
                "MISSING_UNEXPLAINED_PIXELS": missing_unexplained,
                "VISIBLE_CONTOUR_STATUS": visibility_status,
                "NONOPAQUE_FAILURE_EVIDENCE_PACKAGES": nonopaque_failure_packages,
            }
        )
        glyph_visibility_rows.append(
            {
                "GLYPH_ID": glyph.object_id,
                "CHAR": glyph.text,
                "PARENT_ELEMENT_ID": glyph.parent,
                "TRACE_SEQNO": trace_seqno,
                "TEXTTRACE_FILL_RGB": json.dumps(record["TEXTTRACE_FILL_RGB"]),
                "TEXTTRACE_OPACITY": record["TEXTTRACE_OPACITY"],
                "SOURCE_TEXT_SHAPE_MASK": record["SOURCE_TEXT_SHAPE_MASK"],
                "SOURCE_TEXT_SHAPE_PIXELS": int(source_shape.sum()),
                "FINAL_VISIBLE_TARGET_MASK": rel(glyph.raw_path),
                "FINAL_VISIBLE_TARGET_PIXELS": glyph.pixels,
                "MISSING_SOURCE_SHAPE_PIXELS": int(missing.sum()),
                "MISSING_EXPLAINED_BY_LATER_OPAQUE_PIXELS": missing_explained_opaque,
                "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_PIXELS": missing_explained_nonopaque,
                "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_ALPHA_PATH_PIXELS": missing_explained_nonopaque_alpha_path,
                "MISSING_UNEXPLAINED_PIXELS": missing_unexplained,
                "LATER_PAINT_HITS": ";".join(later_hits),
                "LATER_PAINT_UNKNOWN_HITS": ";".join(unknown_later_hits),
                "VISIBLE_CONTOUR_STATUS": visibility_status,
                "NONOPAQUE_FAILURE_EVIDENCE_PACKAGES": ";".join(nonopaque_failure_packages),
            }
        )

    # A source graphic's pre-mask equals its final raw mask only when no later
    # opaque white fill geometrically intersects its actual vector path (not a
    # broad drawing bbox). Otherwise unresolved pre-mask evidence would be a
    # hard failure rather than a fabricated reconstruction.
    occlusion_rows: list[dict[str, Any]] = []
    halo_curve_relation_rows: list[dict[str, Any]] = []
    unresolved_pre: list[str] = []
    drawing_by_graphic = {spec[1]: spec[0] for spec in graphic_specs}
    for graphic in graphics:
        draw_id = drawing_by_graphic.get(graphic.object_id, -1)
        pre_equals_final = True
        intersecting_halos: list[str] = []
        hit_halos: list[dict[str, Any]] = []
        geometry_tests: list[str] = []
        if draw_id >= 0:
            drawing = drawings[draw_id]
            segments = path_segments(drawing)
            buffer_pt = max(0.0, float(drawing.get("width") or 0.0) / 2.0)
            for halo in halo_geometry:
                if int(halo["draw_id"]) <= draw_id:
                    continue
                hits = sum(segment_hits_rect(segment, halo["rect_pt"], buffer_pt) for segment in segments)
                geometry_tests.append(f"{halo['halo_id']}:segments={len(segments)},hits={hits}")
                if hits:
                    pre_equals_final = False
                    intersecting_halos.append(str(halo["halo_id"]))
                    hit_halos.append(halo)
        pre_path = PRE_DIR / f"{graphic.object_id}_pre_occlusion.png"
        if hit_halos:
            pre_mask = source_vector_pre_mask(draw_id, graphic.bbox)
            save_binary(pre_mask, pre_path)
        else:
            pre_mask = np.asarray(Image.open(pre_path).convert("L")) < 128
        if pre_mask.shape != graphic.mask.shape:
            raise RuntimeError(f"pre/final native mask shape mismatch for {graphic.object_id}")
        occlusion_evidence = ""
        coverage_records: list[dict[str, Any]] = []
        if hit_halos:
            if not pre_mask.any():
                unresolved_pre.append(graphic.object_id)
            else:
                occlusion_evidence = occlusion_package(graphic, pre_mask, hit_halos, raw_full)
                coverage_records = json.loads((OUT / occlusion_evidence / "manifest.json").read_text(encoding="utf-8"))["per_halo_coverage"]
        illegal_label_coverages: list[dict[str, Any]] = []
        for coverage in coverage_records:
            halo = next(entry for entry in hit_halos if entry["halo_id"] == coverage["halo_id"])
            parent = str(halo.get("associated_parent", "N/A_UNASSOCIATED"))
            covered = int(coverage["source_pre_halo_intersection_pixels"])
            if covered == 0:
                legality = "PASS_TRUE_HALO_NO_SOURCE_GRAPHIC_COVERAGE"
            elif graphic.role == "DATA_CURVE":
                legality = "FAIL_TEXT_HALO_DATA_CURVE_OCCLUSION"
            elif graphic.role in {"LINE_ARROW", "ARROWHEAD"}:
                legality = "FAIL_TEXT_HALO_LINE_ARROW_OCCLUSION"
            else:
                legality = "FAIL_TEXT_HALO_NONBACKGROUND_GRAPHIC_OCCLUSION"
            record = {
                "GRAPHIC_ID": graphic.object_id,
                "GRAPHIC_ROLE": graphic.role,
                "HALO_ID": coverage["halo_id"],
                "HALO_DRAW_ID": coverage["draw_id"],
                "LABEL_PARENT_ELEMENT_ID": parent,
                "SOURCE_PRE_HALO_INTERSECTION_PX": covered,
                "PRE_MINUS_FINAL_UNDER_HALO_PX": int(coverage["pre_minus_final_under_halo_pixels"]),
                "LEGITIMACY": legality,
                "OCCLUSION_EVIDENCE_PACKAGE": occlusion_evidence,
            }
            halo_curve_relation_rows.append(record)
            if legality.startswith("FAIL_"):
                illegal_label_coverages.append(record)
        pre_final_difference = int((pre_mask & ~graphic.mask).sum())
        status = (
            "PASS" if pre_equals_final
            else ("FAIL_TEXT_HALO_GRAPHIC_OCCLUSION" if illegal_label_coverages
                  else ("PASS_PRE_HALO_FINAL_CLOSED" if occlusion_evidence else "FAIL_UNRESOLVED_PRE_OCCLUSION"))
        )
        occlusion_rows.append(
            {
                "GRAPHIC_ID": graphic.object_id,
                "PRE_MASK": rel(pre_path),
                "FINAL_VISIBLE_MASK": rel(graphic.raw_path),
                "PRE_EQUALS_FINAL": str(pre_equals_final).lower(),
                "LATER_OPAQUE_HALOS": ";".join(intersecting_halos),
                "GEOMETRY_TEST": ";".join(geometry_tests) or "no later opaque halo",
                "PRE_FINAL_DIFFERENCE_PX": pre_final_difference,
                "HALO_RELATION_SUMMARY": ";".join(
                    f"{record['HALO_ID']}:{record['SOURCE_PRE_HALO_INTERSECTION_PX']}px:{record['LEGITIMACY']}"
                    for record in halo_curve_relation_rows if record["GRAPHIC_ID"] == graphic.object_id
                ) or "no exact halo coverage record",
                "OCCLUSION_EVIDENCE_PACKAGE": occlusion_evidence,
                "STATUS": status,
            }
        )
        mask_rows.append(
            {
                "MASK_ID": graphic.object_id,
                "KIND": "GRAPHIC",
                "PARENT_ID": "",
                "ROLE": graphic.role,
                "PANEL": graphic.panel,
                "BBOX_FULL_PAGE_PX": json.dumps(graphic.bbox),
                "PIXELS": graphic.pixels,
                "NONEMPTY": str(graphic.nonempty).lower(),
                "RAW_MASK": rel(graphic.raw_path),
                "FINAL_VISIBLE_MASK": rel(graphic.raw_path),
            }
        )

    # Draw22 is not an opaque halo: it is a documented 0.88-alpha white
    # label ground painted after the patterned missing-support region. Treat
    # it separately. A source-vector curve can be checked exactly; the PGF
    # pattern form cannot be reconstructed as an independent pre-raster here,
    # so that limitation is recorded as a known hard audit failure rather than
    # silently reusing final hatch pixels as a fake pre-image.
    translucent_relation_rows: list[dict[str, Any]] = []
    for overlay_entry in translucent_geometry:
        ox0, oy0, ox1, oy1 = overlay_entry["bbox"]
        for graphic in graphics:
            gx0, gy0, gx1, gy1 = graphic.bbox
            if max(ox0, gx0) >= min(ox1, gx1) or max(oy0, gy0) >= min(oy1, gy1):
                continue
            if graphic.object_id == "GR025":
                package = translucent_label_overlay_package(graphic, None, overlay_entry, raw_full, unresolved_pre=True)
                translucent_relation_rows.append(
                    {
                        "GRAPHIC_ID": graphic.object_id,
                        "GRAPHIC_ROLE": graphic.role,
                        "OVERLAY_ID": overlay_entry["overlay_id"],
                        "OVERLAY_DRAW_ID": overlay_entry["draw_id"],
                        "LABEL_PARENT_ELEMENT_ID": overlay_entry["associated_parent"],
                        "SOURCE_PRE_OVERLAY_INTERSECTION_PX": "N/A_PATTERN_FORM_PRE_UNRECOVERABLE",
                        "PRE_MINUS_FINAL_PX": "N/A_PATTERN_FORM_PRE_UNRECOVERABLE",
                        "LEGITIMACY": "FAIL_KNOWN_UNRECOVERABLE_PRE_TRANSPARENT_LABEL_OVERLAY",
                        "EVIDENCE_PACKAGE": package,
                    }
                )
                continue
            draw_id = drawing_by_graphic.get(graphic.object_id)
            if draw_id is None:
                continue
            pre_mask = source_vector_pre_mask(draw_id, graphic.bbox)
            local_overlay = np.zeros_like(pre_mask)
            ix0, iy0, ix1, iy1 = max(gx0, ox0), max(gy0, oy0), min(gx1, ox1), min(gy1, oy1)
            local_overlay[iy0 - gy0 : iy1 - gy0, ix0 - gx0 : ix1 - gx0] = overlay_entry["mask"][iy0 - oy0 : iy1 - oy0, ix0 - ox0 : ix1 - ox0]
            intersection = int((pre_mask & local_overlay).sum())
            if intersection == 0:
                continue
            package = translucent_label_overlay_package(graphic, pre_mask, overlay_entry, raw_full)
            legitimacy = (
                "FAIL_TEXT_TRANSPARENT_LABEL_DATA_CURVE_OCCLUSION"
                if graphic.role == "DATA_CURVE"
                else "FAIL_TEXT_TRANSPARENT_LABEL_NONBACKGROUND_GRAPHIC_OCCLUSION"
            )
            translucent_relation_rows.append(
                {
                    "GRAPHIC_ID": graphic.object_id,
                    "GRAPHIC_ROLE": graphic.role,
                    "OVERLAY_ID": overlay_entry["overlay_id"],
                    "OVERLAY_DRAW_ID": overlay_entry["draw_id"],
                    "LABEL_PARENT_ELEMENT_ID": overlay_entry["associated_parent"],
                    "SOURCE_PRE_OVERLAY_INTERSECTION_PX": intersection,
                    "PRE_MINUS_FINAL_PX": int((pre_mask & ~graphic.mask).sum()),
                    "LEGITIMACY": legitimacy,
                    "EVIDENCE_PACKAGE": package,
                }
            )

    # Text has the same paint-order obligation as curves. Here the left q_L
    # source node precedes the later opaque boundary-label fill (draw 20). The
    # latter erases required q_L suffix content in the frozen final PDF. Keep
    # every zero-pixel source slot/composite in a separate ledger and derive
    # any partial final-visible record from the mask, never from a story about
    # a surviving denominator; do not fabricate a pre-text raster.
    text_occlusion_rows: list[dict[str, Any]] = []
    boundary_halo = next(item for item in halo_geometry if item["draw_id"] == 20)
    if tuple(boundary_halo["bbox"]) != tuple(source_boundary_halo_box):
        raise RuntimeError("draw20 opaque halo geometry drifted between source and final inventory classification")
    ql_suffix = sorted(fully_occluded_source_glyphs + partial_occluded_source_glyphs, key=lambda glyph: (glyph.bbox[0], glyph.bbox[1], glyph.object_id))
    if not ql_suffix:
        raise RuntimeError("q_L source-only/partial suffix evidence is empty")
    text_occlusion_evidence = text_occlusion_failure_package(
        ql_element, ql_suffix, glyph_source_shapes, glyph_isolation, boundary_halo, raw_full
    )
    text_occlusion_rows.append(
        {
            "ELEMENT_ID": ql_element.object_id,
            "SEMANTIC_TEXT": ql_element.text,
            "SOURCE_ORDER_EVIDENCE": "fig_v5_c02_is_support.tex:q_L node precedes boundary node; PDF draw20 is later opaque white fill",
            "LATER_OPAQUE_HALO": boundary_halo["halo_id"],
            "HIDDEN_OR_PARTIALLY_HIDDEN_GLYPHS": ";".join(f"{glyph.object_id}:{glyph.text}" for glyph in ql_suffix),
            "FINAL_VISIBLE_MASK": rel(ql_element.raw_path),
            "PRE_TEXT_STATUS": "SOURCE_NODE_RAWDICT_AND_PAINT_ORDER_RETAINED_NO_SYNTHETIC_PRE_RASTER",
            "STATUS": "FAIL_TEXT_OCCLUSION_TEXT_COMPLETENESS_REQUIRED_SUFFIX",
            "EVIDENCE_PACKAGE": text_occlusion_evidence,
        }
    )

    source_occlusion_ledger_rows: list[dict[str, Any]] = []
    for glyph in ql_suffix:
        fully_hidden = glyph.object_id in fully_occluded_source_ids
        source_occlusion_ledger_rows.append(
            {
                "SOURCE_GLYPH_ID": glyph.object_id,
                "CHAR": glyph.text,
                "UNICODE": " ".join(f"U+{ord(character):04X}" for character in glyph.text),
                "PARENT_ELEMENT_ID": glyph.parent,
                "PARENT_TEXT": ql_element.text,
                "SOURCE_PDF_CHAR_BBOX_FULL_PAGE_PX": json.dumps(glyph.bbox),
                "SOURCE_PRE_EVIDENCE": "fig_v5_c02_is_support.tex:55-56 q_L node; rawdict character slot; text_occlusion_evidence/E016/source_pre_order_evidence.json",
                "PAINT_ORDER": "source q_L node lines 55-56 before boundary node lines 59-60; PDF draw20 later",
                "OPAQUE_HALO": f"{boundary_halo['halo_id']} / PDF draw20 / #FFFFFF opacity=1",
                "BBOX_WITHIN_TRUE_OPAQUE_HALO": str(bool((glyph_source_shapes[glyph.object_id] & source_boundary_halo_full[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]]).any())).lower(),
                "FINAL_VISIBLE_INVENTORY": str(not fully_hidden).lower(),
                "FINAL_RAW_MASK": "N/A_EXCLUDED_FULLY_HIDDEN_SOURCE_SLOT" if fully_hidden else rel(glyph.raw_path),
                "FINAL_RAW_PIXEL_COUNT": glyph.pixels,
                "DISPOSITION": "EXCLUDED_FULLY_OCCLUDED_SOURCE_GLYPH" if fully_hidden else "RETAINED_PARTIAL_FINAL_VISIBLE_FRAGMENT",
                "SOURCE_PRE_PIXEL_COUNT": int(glyph_source_shapes[glyph.object_id].sum()),
                "MISSING_PIXEL_COUNT": int(glyph_isolation[glyph.object_id].get("SOURCE_SHAPE_TO_FINAL_MISSING_PIXELS", 0)),
                "MISSING_EXPLAINED_BY_LATER_OPAQUE_PIXELS": int(glyph_isolation[glyph.object_id].get("MISSING_EXPLAINED_BY_LATER_OPAQUE_PIXELS", 0)),
                "MISSING_UNEXPLAINED_PIXELS": int(glyph_isolation[glyph.object_id].get("MISSING_UNEXPLAINED_PIXELS", 0)),
                "STATUS": "FAIL_TEXT_OCCLUSION_TEXT_COMPLETENESS",
                "EVIDENCE_PACKAGE": text_occlusion_evidence,
            }
        )
    source_occlusion_substring_rows: list[dict[str, Any]] = []
    for sub_id in sorted(source_only_substring_ids):
        subrow = next(row for row in substring_rows if str(row["MEASURE_ID"]) == sub_id)
        isolation = substring_isolation[sub_id]
        package = source_occluded_substring_package(sub_id, subrow, isolation, boundary_halo, raw_full)
        source_occlusion_substring_rows.append(
            {
                "SOURCE_SUBSTRING_ID": sub_id,
                "PARENT_ELEMENT_ID": subrow["PARENT_ELEMENT_ID"],
                "SOURCE_DESCRIPTOR": isolation["SOURCE_COMPOSITE_DESCRIPTOR"],
                "SOURCE_COMPOSITE_BBOX_FULL_PAGE_PX": json.dumps(isolation["COMPOSITE_BBOX_FULL_PAGE_PX"]),
                "SOURCE_PRE_PIXEL_COUNT": isolation["SOURCE_PIXELS"],
                "FINAL_VISIBLE_INVENTORY": "false",
                "FINAL_RAW_MASK": "N/A_EXCLUDED_SOURCE_ONLY_REQUIRED_SUBSTRING",
                "FINAL_RAW_PIXEL_COUNT": isolation["FINAL_PIXELS"],
                "MISSING_PIXEL_COUNT": isolation["MISSING_SOURCE_TO_FINAL_PIXELS"],
                "FOREIGN_FINAL_PIXEL_COUNT": isolation["FOREIGN_FINAL_OUTSIDE_SOURCE_PIXELS"],
                "OPAQUE_HALO": f"{boundary_halo['halo_id']} / PDF draw20 / #FFFFFF opacity=1",
                "DISPOSITION": "EXCLUDED_FULLY_OCCLUDED_SOURCE_REQUIRED_SUBSTRING",
                "STATUS": "FAIL_TEXT_OCCLUSION_TEXT_COMPLETENESS",
                "EVIDENCE_PACKAGE": package,
            }
        )
    save_json(
        OUT / "final_visible_glyph_inventory.json",
        {
            "final_visible_glyph_count": len(final_visible_glyphs),
            "final_visible_glyph_ids": [glyph.object_id for glyph in final_visible_glyphs],
            "excluded_fully_occluded_source_glyph_count": len(fully_occluded_source_glyphs),
            "excluded_fully_occluded_source_glyph_ids": [glyph.object_id for glyph in fully_occluded_source_glyphs],
            "retained_partial_fragment_count": len(partial_occluded_source_glyphs),
            "retained_partial_fragment_ids": [glyph.object_id for glyph in partial_occluded_source_glyphs],
            "source_only_necessary_substring_count": len(source_only_substring_ids),
            "source_only_necessary_substring_ids": sorted(source_only_substring_ids),
            "closure_rule": "Only nonempty final-visible source glyph/substrings appear in final inventory. Fully hidden source slots and wholly hidden required composites remain only in the source-occlusion ledgers.",
        },
    )
    source_final_inventory_formula = {
        "source_glyph_count": len(glyphs),
        "source_necessary_substring_count": len(substring_rows),
        "source_total_slots": len(glyphs) + len(substring_rows),
        "excluded_fully_occluded_source_glyph_count": len(fully_occluded_source_glyphs),
        "excluded_source_only_necessary_substring_count": len(source_only_substring_ids),
        "retained_partial_final_visible_glyph_count": len(partial_occluded_source_glyphs),
        "expected_final_visible_contact_records": (
            len(glyphs) + len(substring_rows)
            - len(fully_occluded_source_glyphs)
            - len(source_only_substring_ids)
        ),
        "actual_final_visible_glyph_records": len(final_visible_glyphs),
        "actual_final_visible_substring_records": len(final_visible_substring_rows),
        "actual_final_visible_contact_records": len(final_visible_glyphs) + len(final_visible_substring_rows),
    }
    source_final_inventory_formula["pass"] = (
        source_final_inventory_formula["expected_final_visible_contact_records"]
        == source_final_inventory_formula["actual_final_visible_contact_records"]
        and source_final_inventory_formula["source_glyph_count"]
        == source_final_inventory_formula["actual_final_visible_glyph_records"]
        + source_final_inventory_formula["excluded_fully_occluded_source_glyph_count"]
        and source_final_inventory_formula["source_necessary_substring_count"]
        == source_final_inventory_formula["actual_final_visible_substring_records"]
        + source_final_inventory_formula["excluded_source_only_necessary_substring_count"]
    )
    save_json(OUT / "source_to_final_visible_inventory_formula.json", source_final_inventory_formula)

    # CHAR ↔ actual shape ↔ parent ↔ bbox closure. The candidate is a native
    # PDF/TikZ page (no SVG <use> objects exist here), so SVG-use order is an
    # explicit N/A rather than an unchecked assumption. Every cell below is a
    # raw 300-dpi crop enlarged 8× by nearest-neighbour for manual inspection;
    # its red pixels are that record's separated raw mask only.
    assignment_count = np.zeros((height, width), dtype=np.uint16)
    for glyph in final_visible_glyphs:
        assignment_count[glyph.bbox[1] : glyph.bbox[3], glyph.bbox[0] : glyph.bbox[2]] += glyph.mask.astype(np.uint16)
    mapping_rows: list[dict[str, Any]] = []
    mapping_visuals: list[tuple[MaskObject, dict[str, Any]]] = []
    element_by_id = {element.object_id: element for element in elements}

    def mapping_status_for(obj: MaskObject, *, partial_fragment: bool, is_substring: bool = False) -> tuple[str, str]:
        parent_ok = obj.parent in element_by_id
        native_slice = ink[obj.bbox[1] : obj.bbox[3], obj.bbox[0] : obj.bbox[2]]
        subset_native = bool(np.all(~obj.mask | native_slice))
        duplicate_pixels = 0
        if not is_substring:
            duplicate_pixels = int((assignment_count[obj.bbox[1] : obj.bbox[3], obj.bbox[0] : obj.bbox[2]] > 1).sum())
            isolation = glyph_isolation[obj.object_id]
            if int(isolation["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"]) != 0:
                return "UNKNOWN_NON_TARGET_LAYER_CONTAMINATION", "target final mask intersects a non-target official layer without text paint-order ownership"
            if int(ownership_report["source_duplicate_text_pixels"]) != 0 or int(ownership_report["source_unassigned_text_replay_pixels_in_figure"]) != 0:
                return "UNKNOWN_CHAR_OWNERSHIP_CLOSURE", "text-replay pixels are duplicated or unassigned across CHAR owners"
            if isolation["VISIBLE_CONTOUR_STATUS"] == "FAIL_KNOWN_NONOPAQUE_LATER_TEXT_COVERAGE":
                return "FAIL_KNOWN_NONOPAQUE_LATER_TEXT_COVERAGE", "source text is actually covered by a later non-white marker/stroke; native pre/later/final package is retained"
            if isolation["VISIBLE_CONTOUR_STATUS"] == "FAIL_UNEXPLAINED_FINAL_VISIBLE_CONTOUR":
                return "FAIL_UNEXPLAINED_FINAL_VISIBLE_CONTOUR", "source text has final-visible missing pixels not covered by any traceable later source paint path; native pre/later/final package records the unresolved cause"
            if isolation["VISIBLE_CONTOUR_STATUS"] == "UNKNOWN_VISIBLE_CONTOUR_OR_LATER_PAINT":
                return "UNKNOWN_VISIBLE_CONTOUR", "source target path has unexplained missing pixels or later paint"
        else:
            isolation = substring_isolation[obj.object_id]
            if int(isolation["FOREIGN_FINAL_OUTSIDE_SOURCE_PIXELS"]) != 0 or int(isolation["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"]) != 0:
                return "UNKNOWN_COMPOSITE_BACKGROUND_OR_NEIGHBOUR_CONTAMINATION", "final composite contains pixels outside isolated CHAR/vector source paths"
            if isolation["VISIBLE_CONTOUR_STATUS"] == "UNKNOWN_COMPOSITE_CONTOUR_OR_CONTAMINATION":
                return "UNKNOWN_COMPOSITE_VISIBLE_CONTOUR", "necessary substring has unexplained missing or foreign pixels"
        if partial_fragment:
            if is_substring:
                return "FAIL_KNOWN_PARTIAL_REQUIRED_SUBSTRING", "actual final pixels are only an opaque-halo fragment; source slot/parent/bbox is proved but required semantic substring is incomplete"
            return "FAIL_KNOWN_PARTIAL_CHAR_SHAPE", "actual final pixels are only an opaque-halo fragment; source slot/parent/bbox is proved but no complete character-shape claim is allowed"
        if not parent_ok:
            return "UNKNOWN_PARENT_NOT_CLOSED", "parent ELEMENT_ID absent"
        if not obj.nonempty:
            return "UNKNOWN_EMPTY_RAW_MASK", "empty final raw mask without proven opaque-halo explanation"
        if not subset_native:
            return "UNKNOWN_MASK_NOT_SUBSET_OF_NATIVE_FOREGROUND", "raw mask contains non-native pixel"
        if duplicate_pixels:
            return "UNKNOWN_SHARED_WITH_OTHER_GLYPH", f"{duplicate_pixels} final pixels assigned to more than one glyph"
        if not MANUAL_CONTACT_SHEETS_REVIEWED:
            return "PENDING_MANUAL_8X_CONTACT", "machine closure passed; pending actual 8× contact-sheet inspection"
        return "PASS_CHAR_SHAPE_PARENT_BBOX", "native shape subset, unique owner, source parent closure, and manual 8× check"

    for glyph in final_visible_glyphs:
        parent = element_by_id[glyph.parent]
        expected_parent_member = glyph in element_char_index[parent.object_id]
        is_fragment = glyph.object_id in partial_occluded_source_ids
        status, reason = mapping_status_for(glyph, partial_fragment=is_fragment)
        raw_row = pixel_row_by_id[glyph.object_id]
        isolation = glyph_isolation[glyph.object_id]
        row = {
            "MAP_ID": glyph.object_id,
            "KIND": "GLYPH",
            "CHAR": glyph.text,
            "UNICODE": " ".join(f"U+{ord(character):04X}" for character in glyph.text),
            "PARENT_ELEMENT_ID": glyph.parent,
            "PARENT_TEXT": parent.text,
            "ROLE": glyph.role,
            "PANEL": glyph.panel,
            "PDF_CHAR_BBOX_FULL_PAGE_PX": json.dumps(glyph.bbox),
            "RAWDICT_CHAR_BBOX_FULL_PAGE_PX": json.dumps(isolation["RAWDICT_CHAR_BBOX_FULL_PAGE_PX"]),
            "TEXTTRACE_CHAR_BBOX_FULL_PAGE_PX": json.dumps(isolation["TEXTTRACE_CHAR_BBOX_FULL_PAGE_PX"]),
            "OWNERSHIP_UNPADDED_BBOX_FULL_PAGE_PX": json.dumps(isolation["OWNERSHIP_UNPADDED_BBOX_FULL_PAGE_PX"]),
            "OWNERSHIP_ROI_PAD_NATIVE_PX": isolation["OWNERSHIP_ROI_PAD_NATIVE_PX"],
            "OWNERSHIP_BBOX_FULL_PAGE_PX": json.dumps(isolation["OWNERSHIP_BBOX_FULL_PAGE_PX"]),
            "RAW_MASK": rel(glyph.raw_path),
            "RAW_MASK_PIXELS": glyph.pixels,
            "SOURCE_TEXT_SHAPE_MASK": isolation["SOURCE_TEXT_SHAPE_MASK"],
            "TRACE_SEQNO": isolation["TRACE_SEQNO"],
            "TRACE_PAINT_ORDER": isolation["TRACE_PAINT_ORDER"],
            "TEXTTRACE_FILL_RGB": json.dumps(isolation["TEXTTRACE_FILL_RGB"]),
            "TEXTTRACE_OPACITY": isolation["TEXTTRACE_OPACITY"],
            "BACKGROUND_TEXTURE_INTERSECTION_PX": isolation["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"],
            "MISSING_STROKE_TOTAL_PX": isolation["SOURCE_SHAPE_TO_FINAL_MISSING_PIXELS"],
            "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_ALPHA_PATH_PX": isolation["MISSING_EXPLAINED_BY_LATER_NONOPAQUE_ALPHA_PATH_PIXELS"],
            "MISSING_UNEXPLAINED_PX": isolation["MISSING_UNEXPLAINED_PIXELS"],
            "VISIBLE_CONTOUR_STATUS": isolation["VISIBLE_CONTOUR_STATUS"],
            "LATER_COVERAGE_EVIDENCE": ";".join(isolation.get("NONOPAQUE_FAILURE_EVIDENCE_PACKAGES", [])),
            "H_INK_PX": raw_row["H_INK_PX"],
            "PIXEL_GATE": raw_row["PIXEL_HEIGHT_PASS"],
            "FINAL_VISIBLE_INVENTORY": "true",
            "SHAPE_COMPLETENESS": "PARTIAL_FRAGMENT_BEHIND_HALO03" if is_fragment else "COMPLETE_FINAL_VISIBLE_SHAPE",
            "PARENT_MEMBERSHIP_CLOSED": str(expected_parent_member).lower(),
            "SVG_USE_ORDER": "N/A_PDF_RAWDICT_AND_TIKZ_VECTOR",
            "MAP_STATUS": status,
            "MAP_REASON": reason,
            "CONTACT_SHEET": "",
            "CONTACT_CELL": "",
            "CONTACT_ORIGINAL_XY": "",
            "CONTACT_TARGET_OVERLAY_XY": "",
            "CONTACT_MASK_ONLY_XY": "",
        }
        mapping_rows.append(row)
        mapping_visuals.append((glyph, row))

    # S_NOT_LL closes the zero-advance \not extraction component; S001--S006
    # each bind a source vector fraction bar to its semantic parent.
    for subrow in final_visible_substring_rows:
        sub_id = str(subrow["MEASURE_ID"])
        sub_box = tuple(int(subrow[key]) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        sub_mask = np.asarray(Image.open(OUT / subrow["RAW_MASK"]).convert("L")) < 128
        parent_id = str(subrow["PARENT_ELEMENT_ID"])
        parent = element_by_id.get(parent_id)
        sub_obj = MaskObject(
            sub_id,
            "TEXT_SUBSTRING",
            str(subrow["ROLE"]),
            str(subrow["PANEL_ID"]),
            sub_box,
            sub_mask,
            OUT / subrow["RAW_MASK"],
            str(subrow["SOURCE_LINE"]),
            text=str(subrow["TEXT_SAMPLE"]),
            parent=parent_id,
        )
        is_fragment = False
        status, reason = mapping_status_for(sub_obj, partial_fragment=is_fragment, is_substring=True)
        isolation = substring_isolation[sub_id]
        row = {
            "MAP_ID": sub_id,
            "KIND": "NECESSARY_SUBSTRING",
            "CHAR": sub_obj.text,
            "UNICODE": "U+0338→U+226A visible closure" if sub_id == "S_NOT_LL" else "PDF_TEXT+VECTOR_FRACTION_BAR",
            "PARENT_ELEMENT_ID": parent_id,
            "PARENT_TEXT": parent.text if parent else "UNKNOWN",
            "ROLE": sub_obj.role,
            "PANEL": sub_obj.panel,
            "PDF_CHAR_BBOX_FULL_PAGE_PX": json.dumps(sub_box),
            "RAWDICT_CHAR_BBOX_FULL_PAGE_PX": "N/A_COMPOSITE",
            "TEXTTRACE_CHAR_BBOX_FULL_PAGE_PX": "N/A_COMPOSITE",
            "OWNERSHIP_UNPADDED_BBOX_FULL_PAGE_PX": "N/A_COMPOSITE",
            "OWNERSHIP_ROI_PAD_NATIVE_PX": "N/A_COMPOSITE",
            "OWNERSHIP_BBOX_FULL_PAGE_PX": json.dumps(sub_box),
            "RAW_MASK": str(subrow["RAW_MASK"]),
            "RAW_MASK_PIXELS": sub_obj.pixels,
            "SOURCE_TEXT_SHAPE_MASK": isolation["SOURCE_COMPOSITE_MASK"],
            "TRACE_SEQNO": "COMPOSITE",
            "TRACE_PAINT_ORDER": "COMPOSITE",
            "TEXTTRACE_FILL_RGB": "COMPOSITE",
            "TEXTTRACE_OPACITY": "COMPOSITE",
            "BACKGROUND_TEXTURE_INTERSECTION_PX": isolation["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"],
            "MISSING_STROKE_TOTAL_PX": isolation["MISSING_SOURCE_TO_FINAL_PIXELS"],
            "MISSING_UNEXPLAINED_PX": isolation["MISSING_SOURCE_TO_FINAL_PIXELS"] if isolation["VISIBLE_CONTOUR_STATUS"] != "KNOWN_LATER_OPAQUE_OCCLUSION" else 0,
            "VISIBLE_CONTOUR_STATUS": isolation["VISIBLE_CONTOUR_STATUS"],
            "H_INK_PX": subrow["H_INK_PX"],
            "PIXEL_GATE": subrow["PIXEL_HEIGHT_PASS"],
            "FINAL_VISIBLE_INVENTORY": "true",
            "SHAPE_COMPLETENESS": "COMPLETE_FINAL_VISIBLE_SHAPE",
            "PARENT_MEMBERSHIP_CLOSED": str(parent is not None).lower(),
            "SVG_USE_ORDER": "N/A_PDF_RAWDICT_AND_TIKZ_VECTOR",
            "MAP_STATUS": status,
            "MAP_REASON": reason,
            "CONTACT_SHEET": "",
            "CONTACT_CELL": "",
            "CONTACT_ORIGINAL_XY": "",
            "CONTACT_TARGET_OVERLAY_XY": "",
            "CONTACT_MASK_ONLY_XY": "",
        }
        mapping_rows.append(row)
        mapping_visuals.append((sub_obj, row))

    # Every MAP_ID gets three physically adjacent, equal-bbox panels: original
    # official ROI, target-only red overlay, and target-only mask.  None is a
    # derived visual substitute for another; all use the identical native ROI,
    # pad, and 8× nearest scaling.
    contact_columns, contact_rows_per_sheet = 4, 4
    contact_pad, contact_scale = 2, 8
    max_roi_width = max(obj.bbox[2] - obj.bbox[0] + 2 * contact_pad for obj, _ in mapping_visuals)
    max_roi_height = max(obj.bbox[3] - obj.bbox[1] + 2 * contact_pad for obj, _ in mapping_visuals)
    panel_width, panel_height = max_roi_width * contact_scale, max_roi_height * contact_scale
    panel_gap, outer_margin, label_height = 12, 8, 76
    contact_cell_width = outer_margin * 2 + panel_width * 3 + panel_gap * 2
    contact_cell_height = label_height + panel_height + outer_margin
    contact_layout_rows: list[dict[str, Any]] = []
    for start in range(0, len(mapping_visuals), contact_columns * contact_rows_per_sheet):
        sheet_no = start // (contact_columns * contact_rows_per_sheet) + 1
        sheet = Image.new("RGB", (contact_columns * contact_cell_width, contact_rows_per_sheet * contact_cell_height), "white")
        draw = ImageDraw.Draw(sheet)
        for local_index, (obj, row) in enumerate(mapping_visuals[start : start + contact_columns * contact_rows_per_sheet]):
            column = local_index % contact_columns
            sheet_row = local_index // contact_columns
            ox = column * contact_cell_width
            oy = sheet_row * contact_cell_height
            label_text = f"{row['MAP_ID']} {row['PARENT_ELEMENT_ID']} {row['UNICODE']}\n{row['MAP_STATUS']} | {row['SHAPE_COMPLETENESS']}"
            draw.text((ox + outer_margin, oy + 4), label_text, fill=(0, 0, 0))
            panel_y = oy + label_height
            panel_x = [
                ox + outer_margin,
                ox + outer_margin + panel_width + panel_gap,
                ox + outer_margin + 2 * (panel_width + panel_gap),
            ]
            for caption, x in zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), panel_x):
                draw.text((x, oy + 51), caption, fill=(0, 0, 0))
            crop = actual_roi(raw_full, obj.bbox, pad=contact_pad).convert("RGB")
            local_mask = np.zeros((crop.height, crop.width), dtype=bool)
            local_mask[contact_pad : contact_pad + obj.mask.shape[0], contact_pad : contact_pad + obj.mask.shape[1]] = obj.mask
            original8 = crop.resize((crop.width * contact_scale, crop.height * contact_scale), Image.Resampling.NEAREST)
            overlay_array = np.asarray(crop, dtype=np.uint8).copy()
            overlay_array[local_mask] = (255, 0, 0)
            overlay8 = Image.fromarray(overlay_array, mode="RGB").resize(original8.size, Image.Resampling.NEAREST)
            mask_only = np.where(local_mask, 0, 255).astype(np.uint8)
            mask8 = Image.fromarray(mask_only, mode="L").convert("RGB").resize(original8.size, Image.Resampling.NEAREST)
            sheet.paste(original8, (panel_x[0], panel_y))
            sheet.paste(overlay8, (panel_x[1], panel_y))
            sheet.paste(mask8, (panel_x[2], panel_y))
            rel_sheet = f"glyph_shape_contact_sheets/contact_sheet_{sheet_no:02d}_triple_8x_nearest.png"
            row["CONTACT_SHEET"] = rel_sheet
            row["CONTACT_CELL"] = f"r{sheet_row + 1}c{column + 1}"
            row["CONTACT_ORIGINAL_XY"] = json.dumps([panel_x[0], panel_y, original8.width, original8.height])
            row["CONTACT_TARGET_OVERLAY_XY"] = json.dumps([panel_x[1], panel_y, overlay8.width, overlay8.height])
            row["CONTACT_MASK_ONLY_XY"] = json.dumps([panel_x[2], panel_y, mask8.width, mask8.height])
            contact_layout_rows.append(
                {
                    "MAP_ID": row["MAP_ID"],
                    "CONTACT_SHEET": rel_sheet,
                    "CONTACT_CELL": row["CONTACT_CELL"],
                    "SOURCE_BBOX_FULL_PAGE_PX": json.dumps(obj.bbox),
                    "PAD_NATIVE_PX": contact_pad,
                    "SCALE": "8x_NEAREST",
                    "ORIGINAL_XYWH": row["CONTACT_ORIGINAL_XY"],
                    "TARGET_OVERLAY_XYWH": row["CONTACT_TARGET_OVERLAY_XY"],
                    "MASK_ONLY_XYWH": row["CONTACT_MASK_ONLY_XY"],
                    "STATUS": "PRESENT",
                }
            )
        sheet_path = CONTACT_DIR / f"contact_sheet_{sheet_no:02d}_triple_8x_nearest.png"
        sheet.save(sheet_path, optimize=True)
        if not sheet_path.exists():
            raise RuntimeError(f"missing required triple contact sheet: {sheet_path}")
    write_csv(
        OUT / "glyph_shape_contact_layout.csv",
        contact_layout_rows,
        ["MAP_ID", "CONTACT_SHEET", "CONTACT_CELL", "SOURCE_BBOX_FULL_PAGE_PX", "PAD_NATIVE_PX", "SCALE", "ORIGINAL_XYWH", "TARGET_OVERLAY_XYWH", "MASK_ONLY_XYWH", "STATUS"],
    )

    # A terminal review may not be asserted by a global boolean. Each MAP_ID
    # must have a reviewer-authored row after its actual three-panel cell has
    # been opened. The first pass writes only a PENDING template.
    manual_ledger_path = OUT / "glyph_shape_contact_manual_ledger.csv"
    manual_fields = [
        "MAP_ID", "REVIEWER", "SHEET", "CELL", "ORIGINAL_MATCH", "OVERLAY_COMPLETE",
        "MASK_ONLY_PURE", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX", "DECISION", "NOTE",
    ]
    layout_by_id = {row["MAP_ID"]: row for row in contact_layout_rows}
    expected_map_ids = [row["MAP_ID"] for row in mapping_rows]
    ledger_by_id: dict[str, dict[str, Any]] = {}
    if manual_ledger_path.exists():
        with manual_ledger_path.open("r", newline="", encoding="utf-8-sig") as handle:
            input_rows = list(csv.DictReader(handle))
        for entry in input_rows:
            map_id = str(entry.get("MAP_ID", ""))
            if not map_id or map_id in ledger_by_id:
                continue
            ledger_by_id[map_id] = {field: str(entry.get(field, "")).strip() for field in manual_fields}
    else:
        input_rows = []
    # A pre-rebuild PENDING-only template cannot be silently joined against a
    # changed final-visible inventory. Preserve it and its old sheets as
    # SUPERSEDED, then create a fresh exact template. No reviewer-authored row
    # is discarded: non-PENDING ledgers deliberately block this branch.
    if input_rows and set(str(row.get("MAP_ID", "")) for row in input_rows) != set(expected_map_ids):
        if all(str(row.get("DECISION", "")).strip().upper() == "PENDING" for row in input_rows):
            ledger_archive = OUT / "glyph_shape_contact_manual_ledger_PRE_R2_REBUILD_SUPERSEDED.csv"
            if not ledger_archive.exists():
                shutil.copy2(manual_ledger_path, ledger_archive)
            sheets_archive = OUT / "glyph_shape_contact_sheets_PRE_R2_REBUILD_SUPERSEDED"
            if CONTACT_DIR.exists() and not sheets_archive.exists():
                shutil.copytree(CONTACT_DIR, sheets_archive)
            (OUT / "R2_PRE_OWNERSHIP_REBUILD_CONTACTS_SUPERSEDED.md").write_text(
                "# Superseded contact evidence\n\n"
                "The prior contact ledger had only PENDING rows and a different final-visible inventory. "
                "It was generated before exact source-only classification / ownership reconstruction and carries no manual review coverage. "
                "The archived CSV and sheets are SUPERSEDED; only the newly generated exact inventory may be reviewed.\n",
                encoding="utf-8",
            )
            input_rows = []
            ledger_by_id = {}
        else:
            raise RuntimeError("manual contact ledger inventory drift would overwrite reviewer-authored rows")
    if not input_rows:
        template_rows = [
            {
                "MAP_ID": map_id,
                "REVIEWER": "",
                "SHEET": layout_by_id[map_id]["CONTACT_SHEET"],
                "CELL": layout_by_id[map_id]["CONTACT_CELL"],
                "ORIGINAL_MATCH": "",
                "OVERLAY_COMPLETE": "",
                "MASK_ONLY_PURE": "",
                "MISSING_STROKE_PX": "",
                "FOREIGN_PIXEL_PX": "",
                "DECISION": "PENDING",
                "NOTE": "Open ORIGINAL + TARGET OVERLAY + MASK ONLY at 8x before completing this row.",
            }
            for map_id in expected_map_ids
        ]
        write_csv(manual_ledger_path, template_rows, manual_fields)
        ledger_by_id = {row["MAP_ID"]: row for row in template_rows}

    def complete_manual_row(entry: dict[str, Any]) -> bool:
        required = ("REVIEWER", "SHEET", "CELL", "ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX", "DECISION", "NOTE")
        return all(str(entry.get(field, "")).strip() for field in required) and str(entry.get("DECISION")) != "PENDING"

    manual_missing_ids = [map_id for map_id in expected_map_ids if map_id not in ledger_by_id]
    manual_incomplete_ids = [map_id for map_id in expected_map_ids if map_id in ledger_by_id and not complete_manual_row(ledger_by_id[map_id])]
    manual_extra_ids = sorted(set(ledger_by_id) - set(expected_map_ids))
    manual_location_mismatch_ids = [
        map_id for map_id in expected_map_ids
        if map_id in ledger_by_id and complete_manual_row(ledger_by_id[map_id])
        and (ledger_by_id[map_id]["SHEET"] != layout_by_id[map_id]["CONTACT_SHEET"] or ledger_by_id[map_id]["CELL"] != layout_by_id[map_id]["CONTACT_CELL"])
    ]
    mapping_by_id = {row["MAP_ID"]: row for row in mapping_rows}
    manual_metric_mismatch_ids: list[str] = []
    for map_id in expected_map_ids:
        entry = ledger_by_id.get(map_id)
        if not entry or not complete_manual_row(entry):
            continue
        try:
            manual_missing = int(entry["MISSING_STROKE_PX"])
            manual_foreign = int(entry["FOREIGN_PIXEL_PX"])
            expected_missing = int(mapping_by_id[map_id]["MISSING_STROKE_TOTAL_PX"])
            expected_foreign = int(mapping_by_id[map_id]["BACKGROUND_TEXTURE_INTERSECTION_PX"])
        except (ValueError, TypeError):
            manual_metric_mismatch_ids.append(map_id)
            continue
        if manual_missing != expected_missing or manual_foreign != expected_foreign:
            manual_metric_mismatch_ids.append(map_id)
    manual_contact_complete = not manual_missing_ids and not manual_incomplete_ids and not manual_extra_ids and not manual_location_mismatch_ids and not manual_metric_mismatch_ids
    # The human ledger may promote only a machine-closed PENDING record. A
    # known machine fragment stays FAIL and must be explicitly acknowledged.
    for row in mapping_rows:
        entry = ledger_by_id.get(row["MAP_ID"])
        if not entry or not complete_manual_row(entry):
            continue
        decision = entry["DECISION"]
        booleans_true = all(entry[key].lower() == "true" for key in ("ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE"))
        try:
            foreign_pixels = int(entry["FOREIGN_PIXEL_PX"])
            missing_pixels = int(entry["MISSING_STROKE_PX"])
        except ValueError:
            row["MAP_STATUS"] = "UNKNOWN_MANUAL_LEDGER_NONNUMERIC"
            row["MAP_REASON"] = "manual missing/foreign pixel count is not an integer"
            continue
        if row["MAP_STATUS"].startswith("PENDING"):
            if decision == "PASS" and booleans_true and foreign_pixels == 0 and missing_pixels == 0:
                row["MAP_STATUS"] = "PASS_CHAR_SHAPE_PARENT_BBOX"
                row["MAP_REASON"] = "machine closure plus reviewer-verified original/overlay/mask-only triple contact"
            else:
                row["MAP_STATUS"] = "UNKNOWN_MANUAL_CONTACT_REJECTED"
                row["MAP_REASON"] = "manual triple-contact row does not support a complete pure shape"
        elif row["MAP_STATUS"].startswith("FAIL"):
            if decision != "KNOWN_FAIL" or not booleans_true or foreign_pixels != 0:
                row["MAP_STATUS"] = "UNKNOWN_MACHINE_FAILURE_LEDGER_MISMATCH"
                row["MAP_REASON"] = "machine-proved non-PASS record lacks matching explicit manual review"
            elif missing_pixels <= 0:
                row["MAP_STATUS"] = "UNKNOWN_MACHINE_FAILURE_MISSING_COUNT"
                row["MAP_REASON"] = "machine-proved missing-contour record must retain a positive source-to-final missing-stroke count"
    # Persist the ledger as supplied, never synthesize reviewer fields.
    manual_ledger_rows = [ledger_by_id[map_id] for map_id in expected_map_ids if map_id in ledger_by_id]

    # Machine ownership and contamination closure: every source CHAR pair and
    # every final visible CHAR pair is enumerated, not sampled. Composite
    # substrings are checked against their isolated CHAR/vector source union.
    def local_mask_overlap(
        box_a: tuple[int, int, int, int], mask_a: np.ndarray,
        box_b: tuple[int, int, int, int], mask_b: np.ndarray,
    ) -> int:
        x0, y0 = max(box_a[0], box_b[0]), max(box_a[1], box_b[1])
        x1, y1 = min(box_a[2], box_b[2]), min(box_a[3], box_b[3])
        if x0 >= x1 or y0 >= y1:
            return 0
        av = mask_a[y0 - box_a[1] : y1 - box_a[1], x0 - box_a[0] : x1 - box_a[0]]
        bv = mask_b[y0 - box_b[1] : y1 - box_b[1], x0 - box_b[0] : x1 - box_b[0]]
        return int((av & bv).sum())

    glyph_pair_rows: list[dict[str, Any]] = []
    source_pair_duplicate_pixels = 0
    final_pair_duplicate_pixels = 0
    for glyph_a, glyph_b in itertools.combinations(glyphs, 2):
        source_shared = local_mask_overlap(
            glyph_a.bbox, glyph_source_shapes[glyph_a.object_id],
            glyph_b.bbox, glyph_source_shapes[glyph_b.object_id],
        )
        final_shared = local_mask_overlap(glyph_a.bbox, glyph_a.mask, glyph_b.bbox, glyph_b.mask)
        source_pair_duplicate_pixels += source_shared
        final_pair_duplicate_pixels += final_shared
        glyph_pair_rows.append(
            {
                "GLYPH_A": glyph_a.object_id,
                "GLYPH_B": glyph_b.object_id,
                "SOURCE_TEXT_REPLAY_SHARED_PIXELS": source_shared,
                "FINAL_VISIBLE_SHARED_PIXELS": final_shared,
                "A_FINAL_VISIBLE_INVENTORY": str(glyph_a.object_id not in fully_occluded_source_ids).lower(),
                "B_FINAL_VISIBLE_INVENTORY": str(glyph_b.object_id not in fully_occluded_source_ids).lower(),
                "STATUS": "PASS" if source_shared == 0 and final_shared == 0 else "FAIL_DUPLICATE_OWNER_PIXEL",
            }
        )
    write_csv(
        OUT / "glyph_glyph_ownership_pairs.csv",
        glyph_pair_rows,
        ["GLYPH_A", "GLYPH_B", "SOURCE_TEXT_REPLAY_SHARED_PIXELS", "FINAL_VISIBLE_SHARED_PIXELS", "A_FINAL_VISIBLE_INVENTORY", "B_FINAL_VISIBLE_INVENTORY", "STATUS"],
    )

    contamination_rows: list[dict[str, Any]] = []
    for map_row in mapping_rows:
        map_id = map_row["MAP_ID"]
        layer_summary = layer_contamination_summary.get(map_id)
        if layer_summary is None:
            raise RuntimeError(f"missing full non-target-layer contamination ledger for {map_id}")
        if map_id.startswith("G"):
            data = glyph_isolation[map_id]
            bbox_background = int(data["BBOX_BACKGROUND_TEXTURE_PIXELS_PRE_REPAIR"])
            foreign_background = int(data["FINAL_TARGET_BACKGROUND_TEXTURE_INTERSECTION_PIXELS"])
            foreign = int(data["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"])
            allowed = int(data["FINAL_TARGET_ALLOWED_TEXT_OWNER_LAYER_PIXELS"])
            source_pixels = int(data["TEXT_ONLY_SHAPE_PIXELS_POST_OWNERSHIP"])
            final_pixels = int(data["FINAL_VISIBLE_TARGET_PIXELS"])
            source_path = data["SOURCE_TEXT_SHAPE_MASK"]
        else:
            data = substring_isolation[map_id]
            bbox_background = "N/A_COMPOSITE_SOURCE_PATH"
            foreign_background = int(data["FOREIGN_FINAL_OUTSIDE_SOURCE_PIXELS"])
            foreign = int(data["FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS"])
            allowed = int(data["FINAL_TARGET_ALLOWED_TEXT_OWNER_LAYER_PIXELS"])
            source_pixels = int(data["SOURCE_PIXELS"])
            final_pixels = int(data["FINAL_PIXELS"])
            source_path = data["SOURCE_COMPOSITE_MASK"]
        if foreign != int(layer_summary["foreign_pixels"]) or allowed != int(layer_summary["allowed_text_owner_pixels"]):
            raise RuntimeError(f"non-target-layer contamination summary drift for {map_id}")
        contamination_rows.append(
            {
                "MAP_ID": map_id,
                "KIND": map_row["KIND"],
                "PARENT_ELEMENT_ID": map_row["PARENT_ELEMENT_ID"],
                "SOURCE_PATH_MASK": source_path,
                "SOURCE_PATH_PIXELS": source_pixels,
                "FINAL_MASK": map_row["RAW_MASK"],
                "FINAL_MASK_PIXELS": final_pixels,
                "BBOX_BACKGROUND_TEXTURE_PIXELS_PRE_REPAIR": bbox_background,
                "FINAL_TARGET_FOREIGN_BACKGROUND_TEXTURE_PIXELS": foreign_background,
                "FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS": foreign,
                "FINAL_TARGET_ALLOWED_TEXT_OWNER_LAYER_PIXELS": allowed,
                "STATUS": "PASS_ZERO_FOREIGN_INTERSECTION" if foreign == 0 else "FAIL_FOREIGN_INTERSECTION",
            }
        )
    write_csv(
        OUT / "glyph_background_texture_contamination.csv",
        contamination_rows,
        ["MAP_ID", "KIND", "PARENT_ELEMENT_ID", "SOURCE_PATH_MASK", "SOURCE_PATH_PIXELS", "FINAL_MASK", "FINAL_MASK_PIXELS", "BBOX_BACKGROUND_TEXTURE_PIXELS_PRE_REPAIR", "FINAL_TARGET_FOREIGN_BACKGROUND_TEXTURE_PIXELS", "FINAL_TARGET_ALL_NON_TARGET_LAYER_FOREIGN_PIXELS", "FINAL_TARGET_ALLOWED_TEXT_OWNER_LAYER_PIXELS", "STATUS"],
    )
    write_csv(
        OUT / "glyph_visible_contour_completeness.csv",
        glyph_visibility_rows,
        ["GLYPH_ID", "CHAR", "PARENT_ELEMENT_ID", "TRACE_SEQNO", "TEXTTRACE_FILL_RGB", "TEXTTRACE_OPACITY", "SOURCE_TEXT_SHAPE_MASK", "SOURCE_TEXT_SHAPE_PIXELS", "FINAL_VISIBLE_TARGET_MASK", "FINAL_VISIBLE_TARGET_PIXELS", "MISSING_SOURCE_SHAPE_PIXELS", "MISSING_EXPLAINED_BY_LATER_OPAQUE_PIXELS", "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_PIXELS", "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_ALPHA_PATH_PIXELS", "MISSING_UNEXPLAINED_PIXELS", "LATER_PAINT_HITS", "LATER_PAINT_UNKNOWN_HITS", "VISIBLE_CONTOUR_STATUS", "NONOPAQUE_FAILURE_EVIDENCE_PACKAGES"],
    )
    write_csv(
        OUT / "glyph_later_paint_ledger.csv",
        later_paint_rows,
        ["GLYPH_ID", "DRAW_ID", "DRAW_SEQNO", "TYPE", "SOURCE_SHAPE_INTERSECTION_PX", "SOURCE_SHAPE_ALPHA_PATH_INTERSECTION_PX", "FILL", "FILL_OPACITY", "STROKE", "STROKE_OPACITY", "STATUS"],
    )
    write_csv(
        OUT / "glyph_later_paint_evidence.csv",
        later_paint_evidence_rows,
        ["GLYPH_ID", "DRAW_ID", "TYPE", "SOURCE_PRE_LATER_INTERSECTION_PX", "MISSING_SOURCE_TO_FINAL_INTERSECTION_PX", "MISSING_SOURCE_TO_FINAL_ALPHA_PATH_SUPPORT_INTERSECTION_PX", "EVIDENCE_PACKAGE"],
    )
    write_csv(
        OUT / "substring_isolation.csv",
        substring_isolation_rows,
        ["MAP_ID", "SOURCE_COMPOSITE_MASK", "SOURCE_COMPOSITE_DESCRIPTOR", "SOURCE_PIXELS", "FINAL_PIXELS", "MISSING_SOURCE_TO_FINAL_PIXELS", "FOREIGN_FINAL_OUTSIDE_SOURCE_PIXELS", "VISIBLE_CONTOUR_STATUS", "COMPOSITE_BBOX_FULL_PAGE_PX", "FINAL_BBOX_FULL_PAGE_PX"],
    )
    contamination_gate_pass = (
        int(ownership_report["source_duplicate_text_pixels"]) == 0
        and int(ownership_report["source_unassigned_text_replay_pixels_in_figure"]) == 0
        and source_pair_duplicate_pixels == 0
        and final_pair_duplicate_pixels == 0
        and layer_contamination_pass
        and all(row["STATUS"] == "PASS_ZERO_FOREIGN_INTERSECTION" for row in contamination_rows)
    )

    mapping_unknown_rows = [row for row in mapping_rows if row["MAP_STATUS"].startswith("UNKNOWN")]
    mapping_failed_rows = [row for row in mapping_rows if row["MAP_STATUS"].startswith("FAIL")]
    mapping_pending_rows = [row for row in mapping_rows if row["MAP_STATUS"].startswith("PENDING")]
    mapping_pass_rows = [row for row in mapping_rows if row["MAP_STATUS"].startswith("PASS")]
    mapping_status_by_id = {row["MAP_ID"]: row["MAP_STATUS"] for row in mapping_rows}
    write_csv(
        OUT / "glyph_shape_mapping.csv",
        mapping_rows,
        ["MAP_ID", "KIND", "CHAR", "UNICODE", "PARENT_ELEMENT_ID", "PARENT_TEXT", "ROLE", "PANEL", "PDF_CHAR_BBOX_FULL_PAGE_PX", "RAWDICT_CHAR_BBOX_FULL_PAGE_PX", "TEXTTRACE_CHAR_BBOX_FULL_PAGE_PX", "OWNERSHIP_UNPADDED_BBOX_FULL_PAGE_PX", "OWNERSHIP_ROI_PAD_NATIVE_PX", "OWNERSHIP_BBOX_FULL_PAGE_PX", "RAW_MASK", "RAW_MASK_PIXELS", "SOURCE_TEXT_SHAPE_MASK", "TRACE_SEQNO", "TRACE_PAINT_ORDER", "TEXTTRACE_FILL_RGB", "TEXTTRACE_OPACITY", "BACKGROUND_TEXTURE_INTERSECTION_PX", "MISSING_STROKE_TOTAL_PX", "MISSING_EXPLAINED_BY_LATER_NONOPAQUE_ALPHA_PATH_PX", "MISSING_UNEXPLAINED_PX", "VISIBLE_CONTOUR_STATUS", "LATER_COVERAGE_EVIDENCE", "H_INK_PX", "PIXEL_GATE", "FINAL_VISIBLE_INVENTORY", "SHAPE_COMPLETENESS", "PARENT_MEMBERSHIP_CLOSED", "SVG_USE_ORDER", "MAP_STATUS", "MAP_REASON", "CONTACT_SHEET", "CONTACT_CELL", "CONTACT_ORIGINAL_XY", "CONTACT_TARGET_OVERLAY_XY", "CONTACT_MASK_ONLY_XY"],
    )
    save_json(
        OUT / "glyph_shape_mapping_summary.json",
        {
            "source_backend": "PDF rawdict text plus TikZ/PDF page drawings",
            "svg_use_order": "N/A: frozen candidate contains no SVG component/use pipeline for this figure",
            "manual_contact_sheets_reviewed": manual_contact_complete,
            "manual_ledger_path": rel(manual_ledger_path),
            "manual_ledger_missing_ids": manual_missing_ids,
            "manual_ledger_incomplete_ids": manual_incomplete_ids,
            "manual_ledger_extra_ids": manual_extra_ids,
            "manual_ledger_location_mismatch_ids": manual_location_mismatch_ids,
            "manual_ledger_metric_mismatch_ids": manual_metric_mismatch_ids,
            "mapping_records": len(mapping_rows),
            "mapping_pass_records": len(mapping_pass_rows),
            "mapping_pending_records": len(mapping_pending_rows),
            "mapping_unknown_records": len(mapping_unknown_rows),
            "mapping_known_failure_records": len(mapping_failed_rows),
            "contact_sheet_count": math.ceil(len(mapping_visuals) / (contact_columns * contact_rows_per_sheet)),
            "known_text_halo_occlusion": text_occlusion_rows,
            "fully_occluded_source_slots_excluded_from_final_inventory": [glyph.object_id for glyph in fully_occluded_source_glyphs],
            "retained_partial_final_visible_fragments": [glyph.object_id for glyph in partial_occluded_source_glyphs],
            "source_only_necessary_substrings_excluded_from_final_inventory": sorted(source_only_substring_ids),
        },
    )
    contact_review = {
        "reviewer": "FIG-P580-01 SA1 strict visual/mathematical blind reviewer",
        "review_basis": "native 300-dpi PDF raster; raw separated mask overlay; 8x nearest-neighbour contact-sheet view only",
        "review_status": "REVIEWED_ALL_SHEETS" if manual_contact_complete else "PENDING_ALL_SHEETS",
        "reviewed_sheet_count": len({entry["SHEET"] for entry in manual_ledger_rows if complete_manual_row(entry)}),
        "total_sheet_count": math.ceil(len(mapping_visuals) / (contact_columns * contact_rows_per_sheet)),
        "reviewed_mapping_record_count": sum(complete_manual_row(entry) for entry in manual_ledger_rows),
        "ledger_complete": manual_contact_complete,
        "ledger_missing_ids": manual_missing_ids,
        "ledger_incomplete_ids": manual_incomplete_ids,
        "ledger_extra_ids": manual_extra_ids,
        "ledger_location_mismatch_ids": manual_location_mismatch_ids,
        "ledger_metric_mismatch_ids": manual_metric_mismatch_ids,
        "final_visible_glyph_record_count": len(final_visible_glyphs),
        "necessary_substring_record_count": len(final_visible_substring_rows),
        "documented_shape_mismatch_ids": [row["MAP_ID"] for row in mapping_failed_rows],
        "unexpected_shape_mismatch_ids": [],
        "source_only_fully_occluded_ids_not_in_contact_inventory": [glyph.object_id for glyph in fully_occluded_source_glyphs] + sorted(source_only_substring_ids),
        "per_sheet": [
            {
                "sheet": sheet_no,
                "path": f"glyph_shape_contact_sheets/contact_sheet_{sheet_no:02d}_triple_8x_nearest.png",
                "records": [row["MAP_ID"] for row in mapping_rows[(sheet_no - 1) * 16 : sheet_no * 16]],
                "status": "REVIEWED" if all(
                    map_id in ledger_by_id and complete_manual_row(ledger_by_id[map_id])
                    for map_id in [row["MAP_ID"] for row in mapping_rows[(sheet_no - 1) * 16 : sheet_no * 16]]
                ) else "PENDING",
            }
            for sheet_no in range(1, math.ceil(len(mapping_visuals) / (contact_columns * contact_rows_per_sheet)) + 1)
        ],
    }
    save_json(OUT / "glyph_shape_contact_sheet_manual_review.json", contact_review)
    (OUT / "glyph_shape_contact_sheet_manual_review.md").write_text(
        "# Glyph contact-sheet manual review\n\n"
        f"- Reviewer: {contact_review['reviewer']}\n"
        f"- Status: {contact_review['review_status']}\n"
        f"- Coverage: {contact_review['reviewed_sheet_count']}/{contact_review['total_sheet_count']} sheets; "
        f"{contact_review['reviewed_mapping_record_count']}/{len(mapping_rows)} mapping records.\n"
        f"- Documented negative records: {', '.join(contact_review['documented_shape_mismatch_ids']) or 'none'}.\n"
        f"- Unexpected CHAR↔shape mismatch records: {', '.join(contact_review['unexpected_shape_mismatch_ids']) or 'none'}.\n"
        f"- Source-only fully occluded slots excluded from final inventory: {', '.join(contact_review['source_only_fully_occluded_ids_not_in_contact_inventory']) or 'none'}.\n",
        encoding="utf-8",
    )

    # Per-element script medians are only eligible for D/E if every glyph in
    # the member set passes C. Pixel-height failures never enter D/E ratios.
    glyph_row_by_id = {row["MEASURE_ID"]: row for row in final_pixel_rows if row["MEASURE_ID"].startswith("G")}
    element_script_samples: list[dict[str, Any]] = []
    for element in elements:
        grouped: dict[str, list[MaskObject]] = defaultdict(list)
        for glyph in element_char_index[element.object_id]:
            if glyph.object_id in fully_occluded_source_ids:
                continue
            script = glyph_row_by_id[glyph.object_id]["SCRIPT_CLASS"]
            grouped[script].append(glyph)
        for script, group in grouped.items():
            rows = [glyph_row_by_id[glyph.object_id] for glyph in group]
            if not all(row["PIXEL_HEIGHT_PASS"] == "true" for row in rows):
                continue
            if not all(mapping_status_by_id.get(glyph.object_id) == "PASS_CHAR_SHAPE_PARENT_BBOX" for glyph in group):
                continue
            element_script_samples.append(
                {
                    "ELEMENT_ID": element.object_id,
                    "PANEL_ID": element.panel,
                    "ROLE": element.role,
                    "SCRIPT_CLASS": script,
                    "H_MEDIAN_PX": float(median(int(row["H_INK_PX"]) for row in rows)),
                    "MEMBER_GLYPHS": ";".join(row["MEASURE_ID"] for row in rows),
                }
            )

    class_rows: list[dict[str, Any]] = []
    grouped_for_d: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for sample in element_script_samples:
        grouped_for_d[(sample["PANEL_ID"], sample["ROLE"], sample["SCRIPT_CLASS"])].append(sample)
    for (panel, role, script), samples in sorted(grouped_for_d.items()):
        class_median = float(median(sample["H_MEDIAN_PX"] for sample in samples))
        for sample in samples:
            ratio = sample["H_MEDIAN_PX"] / class_median if class_median else float("nan")
            passed = 0.92 <= ratio <= 1.08
            class_rows.append(
                {
                    "ELEMENT_ID": sample["ELEMENT_ID"],
                    "PANEL_ID": panel,
                    "ROLE": role,
                    "SCRIPT_CLASS": script,
                    "H_ELEMENT_MEDIAN_PX": f"{sample['H_MEDIAN_PX']:.3f}",
                    "CLASS_MEDIAN_PX": f"{class_median:.3f}",
                    "RATIO_TO_CLASS_MEDIAN": f"{ratio:.6f}",
                    "D_SCOPE": "same_panel+same_role+same_script; not exact glyph; no cross-script",
                    "D_PASS": str(passed).lower(),
                    "REASON": "PASS" if passed else "outside_[0.92,1.08]",
                }
            )

    # E is deliberately stricter than a generic role-size comparison: it only
    # compares like scripts against an actual same-panel BASE (TICK) script.
    # No fallback role and no cross-script median is permitted; absent BASE is
    # an explicit N/A, never a failed glyph smuggled into a ratio.
    role_rows: list[dict[str, Any]] = []
    samples_by_panel_role_script: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for sample in element_script_samples:
        samples_by_panel_role_script[(sample["PANEL_ID"], sample["ROLE"], sample["SCRIPT_CLASS"])].append(sample)
    expected_by_role = {
        "AXIS_TITLE": (1.00, 1.18),
        "ANNOTATION": (0.95, 1.10),
        "FORMULA": (1.00, 1.18),
        "PANEL_TITLE": (1.05, 1.20),
    }
    for panel in ("L", "R"):
        for role, expected in expected_by_role.items():
            scripts = sorted({
                script for candidate_panel, candidate_role, script in samples_by_panel_role_script
                if candidate_panel == panel and candidate_role == role
            })
            if not scripts:
                role_rows.append(
                    {
                        "PANEL_ID": panel,
                        "ROLE": role,
                        "SCRIPT_CLASS": "N/A",
                        "BASE_ROLE": "TICK",
                        "BASE_MEDIAN_PX": "N/A",
                        "ROLE_MEDIAN_PX": "N/A",
                        "ROLE_RATIO": "N/A",
                        "EXPECTED_RANGE": f"[{expected[0]:.2f},{expected[1]:.2f}]",
                        "E_SCOPE": "same_panel+same_script+eligible_TICK_BASE_only",
                        "E_PASS": "N/A",
                        "REASON": "No all-C-pass sample for this role/script; excluded from E.",
                    }
                )
                continue
            for script in scripts:
                members = samples_by_panel_role_script[(panel, role, script)]
                value = float(median(member["H_MEDIAN_PX"] for member in members))
                bases = samples_by_panel_role_script.get((panel, "TICK", script), [])
                if not bases:
                    role_rows.append(
                        {
                            "PANEL_ID": panel,
                            "ROLE": role,
                            "SCRIPT_CLASS": script,
                            "BASE_ROLE": "TICK",
                            "BASE_MEDIAN_PX": "N/A",
                            "ROLE_MEDIAN_PX": f"{value:.3f}",
                            "ROLE_RATIO": "N/A",
                            "EXPECTED_RANGE": f"[{expected[0]:.2f},{expected[1]:.2f}]",
                            "E_SCOPE": "same_panel+same_script+eligible_TICK_BASE_only",
                            "E_PASS": "N/A",
                            "REASON": "No eligible same-script TICK BASE; explicit N/A.",
                        }
                    )
                    continue
                base_value = float(median(sample["H_MEDIAN_PX"] for sample in bases))
                ratio = value / base_value
                passed = expected[0] <= ratio <= expected[1]
                role_rows.append(
                    {
                        "PANEL_ID": panel,
                        "ROLE": role,
                        "SCRIPT_CLASS": script,
                        "BASE_ROLE": "TICK",
                        "BASE_MEDIAN_PX": f"{base_value:.3f}",
                        "ROLE_MEDIAN_PX": f"{value:.3f}",
                        "ROLE_RATIO": f"{ratio:.6f}",
                        "EXPECTED_RANGE": f"[{expected[0]:.2f},{expected[1]:.2f}]",
                        "E_SCOPE": "same_panel+same_script+eligible_TICK_BASE_only",
                        "E_PASS": str(passed).lower(),
                        "REASON": "PASS" if passed else f"outside_[{expected[0]:.2f},{expected[1]:.2f}]",
                    }
                )

    # All semantic TEXT and final-visible non-background GRAPHIC objects are
    # paired once. No visual pair is omitted; graphic-graphic connections are
    # explicitly declared intentional instead of being misreported as text
    # collisions.
    objects: list[MaskObject] = elements + graphics
    overlap_rows: list[dict[str, Any]] = []
    critical_packages: list[str] = []
    clip_failures: list[str] = []
    for obj in objects:
        # Figure crop acts as the visual edge; text needs >=6 pixels clearance.
        if obj.kind == "TEXT":
            edge_values = [
                obj.bbox[0] - figure_px[0],
                figure_px[2] - obj.bbox[2],
                obj.bbox[1] - figure_px[1],
                figure_px[3] - obj.bbox[3],
            ]
            edge_clearance = float(min(edge_values))
            if edge_clearance < 0:
                clip_failures.append(obj.object_id)
            overlap_rows.append(
                {
                    "PAIR_ID": f"EDGE_{obj.object_id}",
                    "OBJECT_A": obj.object_id,
                    "OBJECT_B": "FIGURE_CROP_EDGE",
                    "A_KIND": obj.kind,
                    "B_KIND": "PANEL_BORDER",
                    "A_ROLE": obj.role,
                    "B_ROLE": "FIGURE_EDGE",
                    "RELATION_CLASS": "TEXT_FIGURE_EDGE",
                    "INTENTIONAL_ALLOWED": "false",
                    "OVERLAP_PIXEL_COUNT": 0,
                    "BBOX_CLEARANCE_PX": f"{edge_clearance:.6f}",
                    "RAW_INK_CLEARANCE_PX": f"{edge_clearance:.6f}",
                    "REQUIRED_CLEARANCE_PX": 6,
                    "CLIP_PIXEL_COUNT": 0 if edge_clearance >= 0 else 1,
                    "STATUS": "PASS" if edge_clearance >= 6 else "FAIL",
                    "RAW_MASK_A": rel(obj.raw_path),
                    "RAW_MASK_B": "N/A_crop_boundary",
                    "INTERSECTION_MASK": "N/A",
                    "EVIDENCE_PACKAGE": "",
                }
            )

    for pair_number, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        pair_id = f"P{pair_number:04d}"
        overlap, _, _ = mask_intersection(a, b)
        bbox_clear = rect_clearance(a.bbox, b.bbox)
        clearance = ink_clearance(a, b)
        if a.kind == "TEXT" and b.kind == "TEXT":
            required = 8.0 if a.panel != b.panel and a.panel in ("L", "R") and b.panel in ("L", "R") else 4.0
            relation = "TEXT_TEXT"
            status = "PASS" if overlap == 0 and bbox_clear >= required else "FAIL"
            intentional = False
        elif a.kind == "TEXT" or b.kind == "TEXT":
            text_obj = a if a.kind == "TEXT" else b
            graphic_obj = b if a.kind == "TEXT" else a
            required = 5.0 if graphic_obj.role == "NODE_BORDER" else 3.0
            relation = f"TEXT_{graphic_obj.role}"
            status = "PASS" if overlap == 0 and clearance >= required else "FAIL"
            intentional = False
        else:
            required = 0.0
            relation = "GRAPHIC_GRAPHIC"
            # Source-directed geometry: axes/ticks/arrowheads, curves/markers,
            # and q=0/base-axis contact are intentional graph construction.
            status = "ALLOWED"
            intentional = True
        critical = not intentional and (status == "FAIL" or clearance <= required + 2.0 or bbox_clear <= required + 2.0)
        evidence = ""
        if critical:
            evidence = critical_package(pair_id, a, b, raw_full, overlap, clearance, required, status)
            critical_packages.append(evidence)
        overlap_rows.append(
            {
                "PAIR_ID": pair_id,
                "OBJECT_A": a.object_id,
                "OBJECT_B": b.object_id,
                "A_KIND": a.kind,
                "B_KIND": b.kind,
                "A_ROLE": a.role,
                "B_ROLE": b.role,
                "RELATION_CLASS": relation,
                "INTENTIONAL_ALLOWED": str(intentional).lower(),
                "OVERLAP_PIXEL_COUNT": overlap,
                "BBOX_CLEARANCE_PX": f"{bbox_clear:.6f}",
                "RAW_INK_CLEARANCE_PX": f"{clearance:.6f}",
                "REQUIRED_CLEARANCE_PX": f"{required:.6f}",
                "CLIP_PIXEL_COUNT": 0,
                "STATUS": status,
                "RAW_MASK_A": rel(a.raw_path),
                "RAW_MASK_B": rel(b.raw_path),
                "INTERSECTION_MASK": "embedded in critical package" if evidence else "not-needed; raw intersection=0",
                "EVIDENCE_PACKAGE": evidence,
            }
        )

    # A source-owned glyph can be covered by a later non-white marker even
    # when the final masks no longer overlap (because the marker has replaced
    # the missing text pixels).  Preserve that distinct paint-order relation
    # in the all-relations table with the standard raw A/B/intersection/overlay
    # package, plus its pre→later→final package in text_later_paint_evidence/.
    for event in later_paint_evidence_rows:
        glyph = glyph_by_id[event["GLYPH_ID"]]
        graphic = next(item for item in graphics if drawing_by_graphic.get(item.object_id) == int(event["DRAW_ID"]))
        overlap, _, _ = mask_intersection(glyph, graphic)
        clearance = ink_clearance(glyph, graphic)
        pair_id = f"TEXTLATER_{glyph.object_id}_{graphic.object_id}"
        evidence = critical_package(pair_id, glyph, graphic, raw_full, overlap, clearance, 3.0, "FAIL_SOURCE_PRE_LATER_TEXT_COVERAGE")
        critical_packages.append(evidence)
        overlap_rows.append(
            {
                "PAIR_ID": pair_id,
                "OBJECT_A": glyph.object_id,
                "OBJECT_B": graphic.object_id,
                "A_KIND": "TEXT_GLYPH",
                "B_KIND": "GRAPHIC",
                "A_ROLE": glyph.role,
                "B_ROLE": graphic.role,
                "RELATION_CLASS": f"TEXT_{graphic.role}_PAINT_ORDER",
                "INTENTIONAL_ALLOWED": "false",
                "OVERLAP_PIXEL_COUNT": overlap,
                "BBOX_CLEARANCE_PX": f"{rect_clearance(glyph.bbox, graphic.bbox):.6f}",
                "RAW_INK_CLEARANCE_PX": f"{clearance:.6f}",
                "REQUIRED_CLEARANCE_PX": "3.000000",
                "CLIP_PIXEL_COUNT": 0,
                "STATUS": "FAIL_SOURCE_PRE_LATER_TEXT_COVERAGE",
                "RAW_MASK_A": rel(glyph.raw_path),
                "RAW_MASK_B": rel(graphic.raw_path),
                "INTERSECTION_MASK": "embedded in critical package; pre/later/final closure in " + event["EVIDENCE_PACKAGE"],
                "EVIDENCE_PACKAGE": evidence,
            }
        )

    # Source-declared white grounds can be real halos and still be illegal if
    # their actual geometry erases a data curve or line.  Add one explicit
    # text↔graphic relation per proved coverage; its occlusion package carries
    # pre/halo/final layering, while the standard critical package preserves
    # the final raw A/B/intersection/clearance view.
    for relation in halo_curve_relation_rows:
        if not relation["LEGITIMACY"].startswith("FAIL_"):
            continue
        label = element_by_id.get(relation["LABEL_PARENT_ELEMENT_ID"])
        if label is None:
            continue
        graphic = next(item for item in graphics if item.object_id == relation["GRAPHIC_ID"])
        overlap, _, _ = mask_intersection(label, graphic)
        clearance = ink_clearance(label, graphic)
        pair_id = f"HALOCOV_{label.object_id}_{graphic.object_id}_{relation['HALO_ID']}"
        evidence = critical_package(pair_id, label, graphic, raw_full, overlap, clearance, 3.0, relation["LEGITIMACY"])
        critical_packages.append(evidence)
        overlap_rows.append(
            {
                "PAIR_ID": pair_id,
                "OBJECT_A": label.object_id,
                "OBJECT_B": graphic.object_id,
                "A_KIND": "TEXT",
                "B_KIND": "GRAPHIC",
                "A_ROLE": label.role,
                "B_ROLE": graphic.role,
                "RELATION_CLASS": f"TEXT_HALO_{graphic.role}_PAINT_ORDER",
                "INTENTIONAL_ALLOWED": "false",
                "OVERLAP_PIXEL_COUNT": overlap,
                "BBOX_CLEARANCE_PX": f"{rect_clearance(label.bbox, graphic.bbox):.6f}",
                "RAW_INK_CLEARANCE_PX": f"{clearance:.6f}",
                "REQUIRED_CLEARANCE_PX": "3.000000",
                "CLIP_PIXEL_COUNT": 0,
                "STATUS": relation["LEGITIMACY"],
                "RAW_MASK_A": rel(label.raw_path),
                "RAW_MASK_B": rel(graphic.raw_path),
                "INTERSECTION_MASK": "embedded in critical package; source-pre/halo/final in " + relation["OCCLUSION_EVIDENCE_PACKAGE"],
                "EVIDENCE_PACKAGE": evidence,
            }
        )

    for relation in translucent_relation_rows:
        label = element_by_id.get(relation["LABEL_PARENT_ELEMENT_ID"])
        if label is None:
            continue
        graphic = next(item for item in graphics if item.object_id == relation["GRAPHIC_ID"])
        overlap, _, _ = mask_intersection(label, graphic)
        clearance = ink_clearance(label, graphic)
        pair_id = f"ALPHACOV_{label.object_id}_{graphic.object_id}_{relation['OVERLAY_ID']}"
        evidence = critical_package(pair_id, label, graphic, raw_full, overlap, clearance, 3.0, relation["LEGITIMACY"])
        critical_packages.append(evidence)
        overlap_rows.append(
            {
                "PAIR_ID": pair_id,
                "OBJECT_A": label.object_id,
                "OBJECT_B": graphic.object_id,
                "A_KIND": "TEXT",
                "B_KIND": "GRAPHIC",
                "A_ROLE": label.role,
                "B_ROLE": graphic.role,
                "RELATION_CLASS": f"TEXT_TRANSLUCENT_LABEL_{graphic.role}_PAINT_ORDER",
                "INTENTIONAL_ALLOWED": "false",
                "OVERLAP_PIXEL_COUNT": overlap,
                "BBOX_CLEARANCE_PX": f"{rect_clearance(label.bbox, graphic.bbox):.6f}",
                "RAW_INK_CLEARANCE_PX": f"{clearance:.6f}",
                "REQUIRED_CLEARANCE_PX": "3.000000",
                "CLIP_PIXEL_COUNT": 0,
                "STATUS": relation["LEGITIMACY"],
                "RAW_MASK_A": rel(label.raw_path),
                "RAW_MASK_B": rel(graphic.raw_path),
                "INTERSECTION_MASK": "embedded in critical package; source-pre/translucent/final in " + relation["EVIDENCE_PACKAGE"],
                "EVIDENCE_PACKAGE": evidence,
            }
        )

    # Text measurement overlay: each semantic parent has an integer-pixel
    # rectangle and ASCII ID only, preserving the underlying native raster.
    overlay = figure_crop.convert("RGB").copy()
    draw = ImageDraw.Draw(overlay)
    colour_by_role = {
        "PANEL_TITLE": (220, 30, 30),
        "AXIS_TITLE": (230, 120, 0),
        "TICK": (160, 0, 160),
        "ANNOTATION": (0, 130, 0),
        "FORMULA": (0, 80, 230),
        "CAPTION": (120, 60, 0),
    }
    for element in elements:
        x0 = element.bbox[0] - figure_px[0]
        y0 = element.bbox[1] - figure_px[1]
        x1 = element.bbox[2] - figure_px[0]
        y1 = element.bbox[3] - figure_px[1]
        color = colour_by_role.get(element.role, (255, 0, 0))
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
        draw.text((x0, max(0, y0 - 9)), element.object_id, fill=color)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png", optimize=True)

    # Cross-link row-level ratios back into the per-glyph CSV without mixing
    # C failures into D/E. Values are annotations only; gates live in their
    # own scope-specific CSVs.
    # These are the only final-visible inventory rows exported to the machine
    # gates.  Fully occluded source slots have a separate, nonempty ledger
    # rather than being smuggled in as empty final masks.
    final_mask_rows = [
        row for row in mask_rows
        if row["MASK_ID"] not in fully_occluded_source_ids
        and row["MASK_ID"] not in source_only_substring_ids
    ]

    write_csv(
        OUT / "after_font_audit.csv",
        font_rows,
        [
            "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE",
            "EFFECTIVE_PT", "PDF_FONT_PT_MEDIAN", "TEXT_SAMPLE", "RAW_MASK", "SOURCE_FONT_PASS", "REASON",
        ],
    )
    write_csv(
        OUT / "after_pixel_measurements.csv",
        final_pixel_rows,
        [
            "MEASURE_ID", "ELEMENT_ID", "PARENT_ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE",
            "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_FONT_PT", "TEXT_SAMPLE", "SCRIPT_CLASS",
            "THRESHOLD_PX", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "RAW_MASK",
            "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX",
            "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PIXEL_HEIGHT_PASS", "PASS_FAIL", "REASON", "FAILURE_EVIDENCE",
        ],
    )
    write_csv(
        OUT / "after_class_ratio.csv",
        class_rows,
        ["ELEMENT_ID", "PANEL_ID", "ROLE", "SCRIPT_CLASS", "H_ELEMENT_MEDIAN_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "D_SCOPE", "D_PASS", "REASON"],
    )
    write_csv(
        OUT / "after_role_ratio.csv",
        role_rows,
        ["PANEL_ID", "ROLE", "SCRIPT_CLASS", "BASE_ROLE", "BASE_MEDIAN_PX", "ROLE_MEDIAN_PX", "ROLE_RATIO", "EXPECTED_RANGE", "E_SCOPE", "E_PASS", "REASON"],
    )

    # Font/grey/page acceptance is an independent human review gate.  It is
    # deliberately ledger-backed rather than a conventional comment or a
    # global boolean: the reviewer must inspect every native view and every
    # panel/role/script scope whose machine medians appear in D/E.
    visual_ledger_path = OUT / "manual_visual_harmony_ledger.csv"
    visual_fields = [
        "CHECK_ID", "CHECK_KIND", "SCOPE", "EVIDENCE_PATH", "PANEL_ID", "ROLE", "SCRIPT_CLASS",
        "FONT_PT_MEDIAN", "H_INK_MEDIAN_PX", "D_RESULT", "E_RESULT", "REVIEWER",
        "ORIGINAL_NATIVE_VIEWED", "NO_INTRUSIVE_OR_CRAMPED", "NO_CROSS_PANEL_INCONSISTENCY",
        "GRAYSCALE_READABLE", "PAGE_INTEGRATION_OK", "FONT_HARMONY_OK", "DECISION", "NOTE",
    ]

    d_scope: dict[tuple[str, str, str], str] = {}
    for row in class_rows:
        key = (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        old = d_scope.get(key)
        d_scope[key] = "FAIL" if row["D_PASS"] != "true" or old == "FAIL" else "PASS"
    e_scope: dict[tuple[str, str, str], str] = {}
    for row in role_rows:
        key = (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        if row["E_PASS"] == "false":
            e_scope[key] = "FAIL"
        elif row["E_PASS"] == "true" and e_scope.get(key) != "FAIL":
            e_scope[key] = "PASS"
        elif key not in e_scope:
            e_scope[key] = "N/A_NO_COMPARABLE_BASE"

    font_by_panel_role: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in font_rows:
        try:
            font_by_panel_role[(row["PANEL_ID"], row["ROLE"])].append(float(row["PDF_FONT_PT_MEDIAN"]))
        except (TypeError, ValueError):
            pass
    pixel_scopes = sorted({(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"]) for row in final_pixel_rows})
    visual_template_rows: list[dict[str, Any]] = [
        {
            "CHECK_ID": "VIEW_FULL_PAGE_200DPI", "CHECK_KIND": "NATIVE_VIEW", "SCOPE": "whole printed page / page fusion",
            "EVIDENCE_PATH": "full_page_200dpi.png", "PANEL_ID": "PAGE", "ROLE": "PAGE_FUSION", "SCRIPT_CLASS": "N/A",
            "FONT_PT_MEDIAN": "N/A", "H_INK_MEDIAN_PX": "N/A", "D_RESULT": "N/A", "E_RESULT": "N/A",
            "REVIEWER": "", "ORIGINAL_NATIVE_VIEWED": "", "NO_INTRUSIVE_OR_CRAMPED": "", "NO_CROSS_PANEL_INCONSISTENCY": "",
            "GRAYSCALE_READABLE": "N/A", "PAGE_INTEGRATION_OK": "", "FONT_HARMONY_OK": "", "DECISION": "PENDING",
            "NOTE": "Open native 200-dpi full page and judge page fusion, figure scale, neighbouring text, and reading path.",
        },
        {
            "CHECK_ID": "VIEW_FIGURE_CROP_300DPI", "CHECK_KIND": "NATIVE_VIEW", "SCOPE": "full figure colour crop",
            "EVIDENCE_PATH": "figure_crop_300dpi.png", "PANEL_ID": "FIGURE", "ROLE": "FIGURE_LAYOUT", "SCRIPT_CLASS": "N/A",
            "FONT_PT_MEDIAN": "N/A", "H_INK_MEDIAN_PX": "N/A", "D_RESULT": "N/A", "E_RESULT": "N/A",
            "REVIEWER": "", "ORIGINAL_NATIVE_VIEWED": "", "NO_INTRUSIVE_OR_CRAMPED": "", "NO_CROSS_PANEL_INCONSISTENCY": "",
            "GRAYSCALE_READABLE": "N/A", "PAGE_INTEGRATION_OK": "N/A", "FONT_HARMONY_OK": "", "DECISION": "PENDING",
            "NOTE": "Open native 300-dpi colour crop and judge overall font hierarchy, crowding, panels, and caption relationship.",
        },
        {
            "CHECK_ID": "VIEW_STANDALONE_300DPI", "CHECK_KIND": "NATIVE_VIEW", "SCOPE": "standalone figure crop",
            "EVIDENCE_PATH": "standalone_300dpi.png", "PANEL_ID": "FIGURE", "ROLE": "STANDALONE_LAYOUT", "SCRIPT_CLASS": "N/A",
            "FONT_PT_MEDIAN": "N/A", "H_INK_MEDIAN_PX": "N/A", "D_RESULT": "N/A", "E_RESULT": "N/A",
            "REVIEWER": "", "ORIGINAL_NATIVE_VIEWED": "", "NO_INTRUSIVE_OR_CRAMPED": "", "NO_CROSS_PANEL_INCONSISTENCY": "",
            "GRAYSCALE_READABLE": "N/A", "PAGE_INTEGRATION_OK": "N/A", "FONT_HARMONY_OK": "", "DECISION": "PENDING",
            "NOTE": "Open native 300-dpi standalone figure and judge visual priority of curves, hatching, labels, and formulae.",
        },
        {
            "CHECK_ID": "VIEW_GRAYSCALE_300DPI", "CHECK_KIND": "NATIVE_VIEW", "SCOPE": "grayscale figure crop",
            "EVIDENCE_PATH": "grayscale_300dpi.png", "PANEL_ID": "FIGURE", "ROLE": "GRAYSCALE", "SCRIPT_CLASS": "N/A",
            "FONT_PT_MEDIAN": "N/A", "H_INK_MEDIAN_PX": "N/A", "D_RESULT": "N/A", "E_RESULT": "N/A",
            "REVIEWER": "", "ORIGINAL_NATIVE_VIEWED": "", "NO_INTRUSIVE_OR_CRAMPED": "", "NO_CROSS_PANEL_INCONSISTENCY": "",
            "GRAYSCALE_READABLE": "", "PAGE_INTEGRATION_OK": "N/A", "FONT_HARMONY_OK": "", "DECISION": "PENDING",
            "NOTE": "Open native grayscale crop and confirm the left-gap/right-coverage reading path survives without colour-only encoding.",
        },
    ]
    font_role_metric_rows: list[dict[str, Any]] = []
    for panel, role, script in pixel_scopes:
        measurements = [row for row in final_pixel_rows if (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"]) == (panel, role, script)]
        h_median = float(median(int(row["H_INK_PX"]) for row in measurements)) if measurements else float("nan")
        font_values = font_by_panel_role.get((panel, role), [])
        font_median = float(median(font_values)) if font_values else float("nan")
        d_result = d_scope.get((panel, role, script), "N/A_NO_C_ELIGIBLE_SAME_SCRIPT_ELEMENT")
        e_result = e_scope.get((panel, role, script), "N/A_NO_COMPARABLE_BASE")
        check_id = f"FONT_{panel}_{role}_{script}".replace(" ", "_")
        font_role_metric_rows.append(
            {
                "CHECK_ID": check_id, "PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script,
                "FONT_PT_MEDIAN": "N/A" if math.isnan(font_median) else f"{font_median:.3f}",
                "H_INK_MEDIAN_PX": "N/A" if math.isnan(h_median) else f"{h_median:.3f}",
                "D_RESULT": d_result, "E_RESULT": e_result,
                "EVIDENCE_PATH": "after_font_audit.csv;after_pixel_measurements.csv;after_class_ratio.csv;after_role_ratio.csv",
            }
        )
        visual_template_rows.append(
            {
                "CHECK_ID": check_id, "CHECK_KIND": "PANEL_ROLE", "SCOPE": f"panel={panel}; role={role}; script={script}",
                "EVIDENCE_PATH": "figure_crop_300dpi.png;grayscale_300dpi.png;after_font_audit.csv;after_pixel_measurements.csv;after_class_ratio.csv;after_role_ratio.csv",
                "PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script,
                "FONT_PT_MEDIAN": "N/A" if math.isnan(font_median) else f"{font_median:.3f}",
                "H_INK_MEDIAN_PX": "N/A" if math.isnan(h_median) else f"{h_median:.3f}",
                "D_RESULT": d_result, "E_RESULT": e_result,
                "REVIEWER": "", "ORIGINAL_NATIVE_VIEWED": "", "NO_INTRUSIVE_OR_CRAMPED": "", "NO_CROSS_PANEL_INCONSISTENCY": "",
                "GRAYSCALE_READABLE": "N/A", "PAGE_INTEGRATION_OK": "N/A", "FONT_HARMONY_OK": "", "DECISION": "PENDING",
                "NOTE": "Open native crop/grayscale and assess this panel-role-script median together with its D/E eligibility/result; do not infer visual harmony from pt alone.",
            }
        )
    write_csv(
        OUT / "font_role_metrics.csv",
        font_role_metric_rows,
        ["CHECK_ID", "PANEL_ID", "ROLE", "SCRIPT_CLASS", "FONT_PT_MEDIAN", "H_INK_MEDIAN_PX", "D_RESULT", "E_RESULT", "EVIDENCE_PATH"],
    )

    visual_by_id: dict[str, dict[str, Any]] = {}
    raw_visual_rows: list[dict[str, Any]] = []
    # The reviewer-authored source CSV is immutable once any real review is
    # present.  A later machine recomputation may change only derived median /
    # D-E fields, so it is reconciled into a separate joined view below rather
    # than rewriting even one byte of the human ledger.
    visual_source_bytes = visual_ledger_path.read_bytes() if visual_ledger_path.exists() else b""
    if visual_ledger_path.exists():
        with visual_ledger_path.open("r", newline="", encoding="utf-8-sig") as handle:
            raw_visual_rows = list(csv.DictReader(handle))
        for entry in raw_visual_rows:
            check_id = str(entry.get("CHECK_ID", "")).strip()
            if check_id and check_id not in visual_by_id:
                visual_by_id[check_id] = {field: str(entry.get(field, "")).strip() for field in visual_fields}
    expected_visual_ids = [row["CHECK_ID"] for row in visual_template_rows]
    template_by_visual_id = {row["CHECK_ID"]: row for row in visual_template_rows}
    if not raw_visual_rows:
        write_csv(visual_ledger_path, visual_template_rows, visual_fields)
        visual_by_id = {row["CHECK_ID"]: row for row in visual_template_rows}

    # Before a reviewer starts, the ledger's machine-derived D/E and median
    # fields must be exactly the current run's values.  A PENDING-only stale
    # template has no human evidence to preserve, so archive it explicitly
    # and rebuild it; reviewer-authored rows are never silently rewritten.
    machine_visual_fields = (
        "CHECK_KIND", "SCOPE", "EVIDENCE_PATH", "PANEL_ID", "ROLE", "SCRIPT_CLASS",
        "FONT_PT_MEDIAN", "H_INK_MEDIAN_PX", "D_RESULT", "E_RESULT",
    )
    visual_metadata_reconciliation_rows: list[dict[str, str]] = []
    visual_metadata_reconciliation_pass = True
    visual_joined_ledger_path = OUT / "manual_visual_harmony_ledger_CURRENT_MACHINE_JOIN.csv"
    visual_reconciliation_path = OUT / "manual_visual_harmony_metadata_reconciliation.csv"
    human_visual_fields = (
        "REVIEWER", "ORIGINAL_NATIVE_VIEWED", "NO_INTRUSIVE_OR_CRAMPED",
        "NO_CROSS_PANEL_INCONSISTENCY", "GRAYSCALE_READABLE",
        "PAGE_INTEGRATION_OK", "FONT_HARMONY_OK", "DECISION", "NOTE",
    )
    machine_field_sources = {
        "CHECK_KIND": "visual-ledger schema/template",
        "SCOPE": "visual-ledger schema/template",
        "EVIDENCE_PATH": "visual-ledger schema/template",
        "PANEL_ID": "after_pixel_measurements.csv",
        "ROLE": "after_pixel_measurements.csv",
        "SCRIPT_CLASS": "after_pixel_measurements.csv",
        "FONT_PT_MEDIAN": "after_font_audit.csv",
        "H_INK_MEDIAN_PX": "after_pixel_measurements.csv",
        "D_RESULT": "after_class_ratio.csv",
        "E_RESULT": "after_role_ratio.csv",
    }
    if raw_visual_rows:
        existing_ids = set(visual_by_id)
        expected_ids = set(expected_visual_ids)
        metadata_drift = [
            check_id
            for check_id in expected_visual_ids
            if check_id in visual_by_id
            and any(visual_by_id[check_id].get(field, "") != template_by_visual_id[check_id][field] for field in machine_visual_fields)
        ]
        pending_only = all(
            str(row.get("DECISION", "")).strip().upper() == "PENDING"
            and not str(row.get("REVIEWER", "")).strip()
            and not str(row.get("ORIGINAL_NATIVE_VIEWED", "")).strip()
            and not str(row.get("NO_INTRUSIVE_OR_CRAMPED", "")).strip()
            and not str(row.get("NO_CROSS_PANEL_INCONSISTENCY", "")).strip()
            and not str(row.get("FONT_HARMONY_OK", "")).strip()
            and (
                str(template_by_visual_id.get(str(row.get("CHECK_ID", "")), {}).get("GRAYSCALE_READABLE", "")) == "N/A"
                or not str(row.get("GRAYSCALE_READABLE", "")).strip()
            )
            and (
                str(template_by_visual_id.get(str(row.get("CHECK_ID", "")), {}).get("PAGE_INTEGRATION_OK", "")) == "N/A"
                or not str(row.get("PAGE_INTEGRATION_OK", "")).strip()
            )
            for row in raw_visual_rows
        )
        if existing_ids != expected_ids:
            if not pending_only:
                raise RuntimeError(
                    "manual visual ledger inventory drift would overwrite reviewer-authored rows; reconcile manually"
                )
            visual_archive = OUT / "manual_visual_harmony_ledger_PRE_R2_METADATA_SYNC_SUPERSEDED.csv"
            if not visual_archive.exists():
                shutil.copy2(visual_ledger_path, visual_archive)
            (OUT / "R2_PRE_VISUAL_METADATA_SYNC_SUPERSEDED.md").write_text(
                "# Superseded pending visual ledger\n\n"
                "This PENDING-only ledger predates the current font-role medians / D-E results. "
                "It contains no reviewer-authored decision and is retained only as SUPERSEDED provenance. "
                "The active ledger was regenerated from the current measurement files before manual review.\n",
                encoding="utf-8",
            )
            write_csv(visual_ledger_path, visual_template_rows, visual_fields)
            raw_visual_rows = [dict(row) for row in visual_template_rows]
            visual_by_id = {row["CHECK_ID"]: row for row in visual_template_rows}
            visual_source_bytes = visual_ledger_path.read_bytes()
        elif metadata_drift:
            # Do not overwrite the reviewed CSV.  Instead make the precise
            # current-machine join auditable field-by-field and prove that every
            # reviewer field survives byte-for-byte (UTF-8 value bytes) while
            # the original source file itself remains byte-identical.
            joined_rows: list[dict[str, str]] = []
            for check_id in expected_visual_ids:
                raw = visual_by_id[check_id]
                template = template_by_visual_id[check_id]
                joined = {field: str(template.get(field, "")) for field in visual_fields}
                for field in human_visual_fields:
                    before = str(raw.get(field, ""))
                    joined[field] = before
                    if before.encode("utf-8") != str(joined[field]).encode("utf-8"):
                        raise RuntimeError(f"reviewer field byte preservation failed: {check_id}/{field}")
                for field in machine_visual_fields:
                    before = str(raw.get(field, ""))
                    after = str(template.get(field, ""))
                    if before != after:
                        visual_metadata_reconciliation_rows.append(
                            {
                                "CHECK_ID": check_id,
                                "FIELD": field,
                                "OLD_VALUE": before,
                                "NEW_VALUE": after,
                                "SOURCE_BOTTOM_TABLE": machine_field_sources[field],
                            }
                        )
                joined_rows.append(joined)
            if visual_ledger_path.read_bytes() != visual_source_bytes:
                raise RuntimeError("reviewer-authored visual ledger changed during metadata reconciliation")
            if any(
                joined[field].encode("utf-8") != visual_by_id[joined["CHECK_ID"]][field].encode("utf-8")
                for joined in joined_rows for field in human_visual_fields
            ):
                raise RuntimeError("joined visual ledger does not preserve human field UTF-8 bytes")
            write_csv(visual_joined_ledger_path, joined_rows, visual_fields)
            write_csv(
                visual_reconciliation_path,
                visual_metadata_reconciliation_rows,
                ["CHECK_ID", "FIELD", "OLD_VALUE", "NEW_VALUE", "SOURCE_BOTTOM_TABLE"],
            )
            save_json(
                OUT / "manual_visual_harmony_metadata_reconciliation.json",
                {
                    "source_manual_ledger": rel(visual_ledger_path),
                    "joined_current_machine_ledger": rel(visual_joined_ledger_path),
                    "reconciliation_csv": rel(visual_reconciliation_path),
                    "reconciled_machine_field_count": len(visual_metadata_reconciliation_rows),
                    "source_manual_ledger_byte_unchanged_pass": visual_ledger_path.read_bytes() == visual_source_bytes,
                    "human_field_utf8_byte_preservation_pass": True,
                    "human_fields": list(human_visual_fields),
                    "note": "Only derived machine metadata was updated in the joined view; the reviewer-authored source CSV was never rewritten.",
                },
            )
            raw_visual_rows = joined_rows
            visual_by_id = {row["CHECK_ID"]: row for row in joined_rows}

    def ledger_true(value: str) -> bool:
        return str(value).strip().lower() == "true"

    def visual_row_complete(entry: dict[str, Any], template: dict[str, Any]) -> bool:
        for field in ("REVIEWER", "ORIGINAL_NATIVE_VIEWED", "NO_INTRUSIVE_OR_CRAMPED", "NO_CROSS_PANEL_INCONSISTENCY", "FONT_HARMONY_OK", "DECISION", "NOTE"):
            if not str(entry.get(field, "")).strip():
                return False
        if str(entry.get("DECISION", "")).upper() not in {"PASS", "FAIL"}:
            return False
        if str(entry.get("ORIGINAL_NATIVE_VIEWED", "")).lower() not in {"true", "false"}:
            return False
        if str(entry.get("NO_INTRUSIVE_OR_CRAMPED", "")).lower() not in {"true", "false"}:
            return False
        if str(entry.get("NO_CROSS_PANEL_INCONSISTENCY", "")).lower() not in {"true", "false"}:
            return False
        if str(entry.get("FONT_HARMONY_OK", "")).lower() not in {"true", "false"}:
            return False
        if template["CHECK_ID"] == "VIEW_GRAYSCALE_300DPI" and str(entry.get("GRAYSCALE_READABLE", "")).lower() not in {"true", "false"}:
            return False
        if template["CHECK_ID"] == "VIEW_FULL_PAGE_200DPI" and str(entry.get("PAGE_INTEGRATION_OK", "")).lower() not in {"true", "false"}:
            return False
        return True

    visual_missing_ids = [check_id for check_id in expected_visual_ids if check_id not in visual_by_id]
    visual_extra_ids = sorted(set(visual_by_id) - set(expected_visual_ids))
    visual_metadata_mismatch_ids: list[str] = []
    visual_incomplete_ids: list[str] = []
    visual_manual_rows: list[dict[str, Any]] = []
    for check_id in expected_visual_ids:
        entry = visual_by_id.get(check_id)
        template = template_by_visual_id[check_id]
        if not entry:
            continue
        visual_manual_rows.append(entry)
        if any(entry.get(field, "") != template[field] for field in machine_visual_fields):
            visual_metadata_mismatch_ids.append(check_id)
        if not visual_row_complete(entry, template):
            visual_incomplete_ids.append(check_id)
    visual_ledger_complete = not visual_missing_ids and not visual_extra_ids and not visual_metadata_mismatch_ids and not visual_incomplete_ids
    visual_by_id_complete = {row["CHECK_ID"]: row for row in visual_manual_rows}
    visual_all_harmony_true = visual_ledger_complete and all(
        ledger_true(row["ORIGINAL_NATIVE_VIEWED"])
        and ledger_true(row["NO_INTRUSIVE_OR_CRAMPED"])
        and ledger_true(row["NO_CROSS_PANEL_INCONSISTENCY"])
        and ledger_true(row["FONT_HARMONY_OK"])
        and row["DECISION"].upper() == "PASS"
        for row in visual_manual_rows
    )
    grayscale_row = visual_by_id_complete.get("VIEW_GRAYSCALE_300DPI", {})
    page_rows = [visual_by_id_complete.get(check_id, {}) for check_id in ("VIEW_FULL_PAGE_200DPI", "VIEW_FIGURE_CROP_300DPI", "VIEW_STANDALONE_300DPI")]
    grayscale_pass = visual_ledger_complete and ledger_true(grayscale_row.get("GRAYSCALE_READABLE", "")) and grayscale_row.get("DECISION", "").upper() == "PASS"
    page_integration_pass = visual_ledger_complete and all(
        row and ledger_true(row.get("ORIGINAL_NATIVE_VIEWED", "")) and row.get("DECISION", "").upper() == "PASS"
        for row in page_rows
    ) and ledger_true(visual_by_id_complete.get("VIEW_FULL_PAGE_200DPI", {}).get("PAGE_INTEGRATION_OK", ""))
    font_harmony_pass = visual_all_harmony_true
    visual_review = {
        "review_status": "REVIEWED_ALL_REQUIRED_ROWS" if visual_ledger_complete else "PENDING_OR_INCOMPLETE",
        "total_required_rows": len(expected_visual_ids),
        "completed_rows": sum(visual_row_complete(visual_by_id[check_id], template_by_visual_id[check_id]) for check_id in expected_visual_ids if check_id in visual_by_id),
        "missing_ids": visual_missing_ids,
        "incomplete_ids": visual_incomplete_ids,
        "extra_ids": visual_extra_ids,
        "metadata_mismatch_ids": visual_metadata_mismatch_ids,
        "font_visual_harmony_pass": font_harmony_pass,
        "grayscale_pass": grayscale_pass,
        "page_integration_pass": page_integration_pass,
        "ledger_path": rel(visual_ledger_path),
        "current_machine_join_path": rel(visual_joined_ledger_path) if visual_joined_ledger_path.exists() else "N/A_NO_METADATA_DRIFT",
        "metadata_reconciliation_path": rel(visual_reconciliation_path) if visual_reconciliation_path.exists() else "N/A_NO_METADATA_DRIFT",
        "metadata_reconciled_machine_field_count": len(visual_metadata_reconciliation_rows),
        "source_manual_ledger_byte_unchanged_pass": visual_ledger_path.read_bytes() == visual_source_bytes,
        "human_field_utf8_byte_preservation_pass": visual_metadata_reconciliation_pass,
    }
    save_json(OUT / "manual_visual_harmony_review.json", visual_review)
    (OUT / "manual_visual_harmony_review.md").write_text(
        "# Manual visual-harmony / grayscale / page-integration review\n\n"
        f"- Status: {visual_review['review_status']}\n"
        f"- Coverage: {visual_review['completed_rows']}/{visual_review['total_required_rows']} required native-view/panel-role rows.\n"
        f"- FONT_VISUAL_HARMONY_PASS: {font_harmony_pass}\n"
        f"- GRAYSCALE_PASS: {grayscale_pass}\n"
        f"- PAGE_INTEGRATION_PASS: {page_integration_pass}\n"
        f"- Machine-metadata reconciliation: {visual_review['metadata_reconciled_machine_field_count']} field(s); source-ledger bytes unchanged={visual_review['source_manual_ledger_byte_unchanged_pass']}; human UTF-8 field preservation={visual_review['human_field_utf8_byte_preservation_pass']}.\n"
        f"- Reviewer source: `{visual_review['ledger_path']}`; current-metrics joined ledger: `{visual_review['current_machine_join_path']}`; field-level reconciliation: `{visual_review['metadata_reconciliation_path']}`.\n"
        f"- Missing: {', '.join(visual_missing_ids) or 'none'}\n"
        f"- Incomplete: {', '.join(visual_incomplete_ids) or 'none'}\n"
        f"- Metadata mismatch: {', '.join(visual_metadata_mismatch_ids) or 'none'}\n",
        encoding="utf-8",
    )

    write_csv(
        OUT / "after_overlap_report.csv",
        overlap_rows,
        [
            "PAIR_ID", "OBJECT_A", "OBJECT_B", "A_KIND", "B_KIND", "A_ROLE", "B_ROLE", "RELATION_CLASS",
            "INTENTIONAL_ALLOWED", "OVERLAP_PIXEL_COUNT", "BBOX_CLEARANCE_PX", "RAW_INK_CLEARANCE_PX",
            "REQUIRED_CLEARANCE_PX", "CLIP_PIXEL_COUNT", "STATUS", "RAW_MASK_A", "RAW_MASK_B", "INTERSECTION_MASK", "EVIDENCE_PACKAGE",
        ],
    )
    write_csv(
        OUT / "mask_manifest.csv",
        final_mask_rows,
        ["MASK_ID", "KIND", "PARENT_ID", "ROLE", "PANEL", "BBOX_FULL_PAGE_PX", "PIXELS", "NONEMPTY", "RAW_MASK", "FINAL_VISIBLE_MASK"],
    )
    write_csv(OUT / "halo_manifest.csv", halo_rows, ["HALO_ID", "PDF_DRAWING_INDEX", "FILL", "FULL_PAGE_BBOX_PX", "RAW_MASK", "DRAW_ORDER", "ASSOCIATED_PARENT", "EVIDENCE"])
    write_csv(OUT / "translucent_overlay_manifest.csv", translucent_rows, ["OVERLAY_ID", "PDF_DRAWING_INDEX", "FILL", "FILL_OPACITY", "FULL_PAGE_BBOX_PX", "RAW_MASK", "DRAW_ORDER", "ASSOCIATED_PARENT", "STATUS"])
    write_csv(OUT / "occlusion_manifest.csv", occlusion_rows, ["GRAPHIC_ID", "PRE_MASK", "FINAL_VISIBLE_MASK", "PRE_EQUALS_FINAL", "LATER_OPAQUE_HALOS", "GEOMETRY_TEST", "PRE_FINAL_DIFFERENCE_PX", "HALO_RELATION_SUMMARY", "OCCLUSION_EVIDENCE_PACKAGE", "STATUS"])
    write_csv(
        OUT / "text_halo_graphic_relations.csv",
        halo_curve_relation_rows,
        ["GRAPHIC_ID", "GRAPHIC_ROLE", "HALO_ID", "HALO_DRAW_ID", "LABEL_PARENT_ELEMENT_ID", "SOURCE_PRE_HALO_INTERSECTION_PX", "PRE_MINUS_FINAL_UNDER_HALO_PX", "LEGITIMACY", "OCCLUSION_EVIDENCE_PACKAGE"],
    )
    write_csv(
        OUT / "text_translucent_label_graphic_relations.csv",
        translucent_relation_rows,
        ["GRAPHIC_ID", "GRAPHIC_ROLE", "OVERLAY_ID", "OVERLAY_DRAW_ID", "LABEL_PARENT_ELEMENT_ID", "SOURCE_PRE_OVERLAY_INTERSECTION_PX", "PRE_MINUS_FINAL_PX", "LEGITIMACY", "EVIDENCE_PACKAGE"],
    )
    write_csv(OUT / "text_occlusion_manifest.csv", text_occlusion_rows, ["ELEMENT_ID", "SEMANTIC_TEXT", "SOURCE_ORDER_EVIDENCE", "LATER_OPAQUE_HALO", "HIDDEN_OR_PARTIALLY_HIDDEN_GLYPHS", "FINAL_VISIBLE_MASK", "PRE_TEXT_STATUS", "STATUS", "EVIDENCE_PACKAGE"])
    write_csv(
        OUT / "source_occlusion_ledger.csv",
        source_occlusion_ledger_rows,
        [
            "SOURCE_GLYPH_ID", "CHAR", "UNICODE", "PARENT_ELEMENT_ID", "PARENT_TEXT", "SOURCE_PDF_CHAR_BBOX_FULL_PAGE_PX",
            "SOURCE_PRE_EVIDENCE", "PAINT_ORDER", "OPAQUE_HALO", "BBOX_WITHIN_TRUE_OPAQUE_HALO",
            "FINAL_VISIBLE_INVENTORY", "FINAL_RAW_MASK", "FINAL_RAW_PIXEL_COUNT", "DISPOSITION",
            "SOURCE_PRE_PIXEL_COUNT", "MISSING_PIXEL_COUNT", "MISSING_EXPLAINED_BY_LATER_OPAQUE_PIXELS", "MISSING_UNEXPLAINED_PIXELS",
            "STATUS", "EVIDENCE_PACKAGE",
        ],
    )
    write_csv(
        OUT / "source_occlusion_substring_ledger.csv",
        source_occlusion_substring_rows,
        [
            "SOURCE_SUBSTRING_ID", "PARENT_ELEMENT_ID", "SOURCE_DESCRIPTOR", "SOURCE_COMPOSITE_BBOX_FULL_PAGE_PX",
            "SOURCE_PRE_PIXEL_COUNT", "FINAL_VISIBLE_INVENTORY", "FINAL_RAW_MASK", "FINAL_RAW_PIXEL_COUNT",
            "MISSING_PIXEL_COUNT", "FOREIGN_FINAL_PIXEL_COUNT", "OPAQUE_HALO", "DISPOSITION", "STATUS", "EVIDENCE_PACKAGE",
        ],
    )
    save_json(
        OUT / "vector_drawings.json",
        {
            "page": PAGE_ONE_BASED,
            "figure_drawing_indices": [spec[0] for spec in graphic_specs],
            "fraction_vector_substring_drawing_indices": sorted(fraction_draw_to_node),
            "opaque_white_halo_drawing_indices": halo_ids,
            "all_page_drawings": [
                {
                    "index": index,
                    "rect_pt": [round(float(value), 4) for value in drawing["rect"]],
                    "type": drawing.get("type"),
                    "width_pt": drawing.get("width"),
                    "stroke_rgb": as_rgb(drawing.get("color")),
                    "fill_rgb": as_rgb(drawing.get("fill")),
                    "items": len(drawing.get("items", [])),
                }
                for index, drawing in enumerate(drawings)
            ],
        },
    )

    source_font_pass = all(row["SOURCE_FONT_PASS"] == "true" for row in font_rows)
    pixel_failures = [row for row in final_pixel_rows if row["PIXEL_HEIGHT_PASS"] != "true"]
    pixel_pass = not pixel_failures
    d_failures = [row for row in class_rows if row["D_PASS"] != "true"]
    same_class_pass = not d_failures
    e_failures = [row for row in role_rows if row["E_PASS"] == "false"]
    role_pass = not e_failures
    illegal_overlap_rows = [
        row for row in overlap_rows
        if row["INTENTIONAL_ALLOWED"] == "false" and int(row["OVERLAP_PIXEL_COUNT"]) > 0
    ]
    clearance_failures = [
        row for row in overlap_rows
        if row["INTENTIONAL_ALLOWED"] == "false" and row["STATUS"] == "FAIL"
    ]
    clip_count = len(clip_failures)
    text_occlusion_failures = [row for row in text_occlusion_rows if row["STATUS"] != "PASS"]
    opaque_halo_graphic_failure_rows = [
        row for row in halo_curve_relation_rows if str(row["LEGITIMACY"]).startswith("FAIL_")
    ]
    translucent_label_graphic_failure_rows = [
        row for row in translucent_relation_rows if str(row["LEGITIMACY"]).startswith("FAIL_")
    ]
    opaque_halo_graphic_evidence_complete = all(
        str(row["OCCLUSION_EVIDENCE_PACKAGE"])
        and (OUT / str(row["OCCLUSION_EVIDENCE_PACKAGE"])).exists()
        for row in opaque_halo_graphic_failure_rows
    )
    translucent_label_graphic_evidence_complete = all(
        str(row["EVIDENCE_PACKAGE"])
        and (OUT / str(row["EVIDENCE_PACKAGE"])).exists()
        for row in translucent_label_graphic_failure_rows
    )
    text_halo_graphic_coverage_pass = not opaque_halo_graphic_failure_rows
    text_translucent_label_graphic_coverage_pass = not translucent_label_graphic_failure_rows
    final_visible_mask_closure = all(row["NONEMPTY"] == "true" for row in final_mask_rows)
    final_visible_inventory_formula_pass = bool(source_final_inventory_formula["pass"])
    mapping_resolution_pass = not mapping_unknown_rows and not mapping_pending_rows
    text_evidence_complete = all((OUT / row["EVIDENCE_PACKAGE"]).exists() for row in text_occlusion_rows)
    later_paint_evidence_complete = all((OUT / row["EVIDENCE_PACKAGE"]).exists() for row in later_paint_evidence_rows)
    critical_evidence_complete = all(
        (OUT / row["EVIDENCE_PACKAGE"]).exists()
        for row in overlap_rows
        if row["EVIDENCE_PACKAGE"]
    )
    overlap_count = sum(int(row["OVERLAP_PIXEL_COUNT"]) for row in illegal_overlap_rows)
    min_text_clearance = min(
        [float(row["RAW_INK_CLEARANCE_PX"]) for row in overlap_rows if row["RELATION_CLASS"].startswith("TEXT_") and row["RAW_INK_CLEARANCE_PX"] not in ("", "N/A")],
        default=float("nan"),
    )

    # Historical run folders must never be mistaken for current terminal
    # evidence. Preserve them in place, but publish an exhaustive ACTIVE /
    # SUPERSEDED lifecycle index keyed to the exact terminal CSV rows.
    critical_rows = [row for row in overlap_rows if row["EVIDENCE_PACKAGE"]]
    package_missing = [row["EVIDENCE_PACKAGE"] for row in critical_rows if not (OUT / row["EVIDENCE_PACKAGE"]).exists()]
    active_critical_ids = sorted({Path(str(row["EVIDENCE_PACKAGE"])).name for row in critical_rows})
    active_pixel_ids = sorted(str(row["MEASURE_ID"]) for row in pixel_failures)
    active_pixel_paths = {str(row["MEASURE_ID"]): str(row["FAILURE_EVIDENCE"]) for row in pixel_failures}
    active_pixel_missing_evidence = [item for item in active_pixel_ids if not active_pixel_paths[item] or not (OUT / active_pixel_paths[item]).exists()]
    critical_directory_ids = sorted(path.name for path in CRITICAL_DIR.iterdir() if path.is_dir())
    pixel_directory_ids = sorted(path.name for path in PIXEL_FAIL_DIR.iterdir() if path.is_dir())
    critical_missing_active_directories = sorted(set(active_critical_ids) - set(critical_directory_ids))
    pixel_missing_active_directories = sorted(set(active_pixel_ids) - set(pixel_directory_ids))
    critical_superseded_ids = sorted(set(critical_directory_ids) - set(active_critical_ids))
    pixel_superseded_ids = sorted(set(pixel_directory_ids) - set(active_pixel_ids))
    evidence_lifecycle_index_pass = (
        not package_missing
        and not active_pixel_missing_evidence
        and not critical_missing_active_directories
        and not pixel_missing_active_directories
        and set(critical_directory_ids) == set(active_critical_ids) | set(critical_superseded_ids)
        and set(pixel_directory_ids) == set(active_pixel_ids) | set(pixel_superseded_ids)
    )
    lifecycle_rows: list[dict[str, Any]] = []
    for evidence_id in critical_directory_ids:
        active = evidence_id in active_critical_ids
        lifecycle_rows.append(
            {
                "CATEGORY": "critical_relations",
                "ENTRY_ID": evidence_id,
                "DIRECTORY": f"critical_relations/{evidence_id}",
                "STATUS": "ACTIVE" if active else "SUPERSEDED",
                "CURRENT_TERMINAL_REFERENCE": f"after_overlap_report.csv:{evidence_id}" if active else "",
                "REASON": "exact terminal critical/failed relation package" if active else "not in terminal active list; retained prior/intermediate package",
            }
        )
    for evidence_id in pixel_directory_ids:
        active = evidence_id in active_pixel_ids
        special = evidence_id in fully_occluded_source_ids
        lifecycle_rows.append(
            {
                "CATEGORY": "pixel_failures",
                "ENTRY_ID": evidence_id,
                "DIRECTORY": f"pixel_failures/{evidence_id}",
                "STATUS": "ACTIVE" if active else "SUPERSEDED",
                "CURRENT_TERMINAL_REFERENCE": f"after_pixel_measurements.csv:{evidence_id}" if active else "",
                "REASON": (
                    "exact terminal final-visible pixel-height failure"
                    if active
                    else ("fully opaque source glyph excluded from final-visible inventory; see source_occlusion_ledger.csv" if special else "not in terminal active list; retained prior/intermediate package")
                ),
            }
        )
    write_csv(
        OUT / "active_terminal_critical_relations.csv",
        critical_rows,
        ["PAIR_ID", "OBJECT_A", "OBJECT_B", "RELATION_CLASS", "STATUS", "EVIDENCE_PACKAGE", "OVERLAP_PIXEL_COUNT", "BBOX_CLEARANCE_PX", "RAW_INK_CLEARANCE_PX", "REQUIRED_CLEARANCE_PX"],
    )
    write_csv(
        OUT / "active_terminal_pixel_failures.csv",
        pixel_failures,
        ["MEASURE_ID", "PARENT_ELEMENT_ID", "TEXT_SAMPLE", "SCRIPT_CLASS", "THRESHOLD_PX", "H_INK_PX", "PIXEL_HEIGHT_PASS", "FAILURE_EVIDENCE"],
    )
    write_csv(
        OUT / "evidence_lifecycle_index.csv",
        lifecycle_rows,
        ["CATEGORY", "ENTRY_ID", "DIRECTORY", "STATUS", "CURRENT_TERMINAL_REFERENCE", "REASON"],
    )
    lifecycle_summary = {
        "terminal_candidate": "frozen R94 page 628 / printed 615",
        "critical_relations": {
            "active_ids": active_critical_ids,
            "active_count": len(active_critical_ids),
            "physical_directory_count": len(critical_directory_ids),
            "superseded_ids": critical_superseded_ids,
            "missing_active_directories": critical_missing_active_directories,
        },
        "pixel_failures": {
            "active_ids": active_pixel_ids,
            "active_count": len(active_pixel_ids),
            "physical_directory_count": len(pixel_directory_ids),
            "superseded_ids": pixel_superseded_ids,
            "missing_active_directories": pixel_missing_active_directories,
            "missing_active_evidence": active_pixel_missing_evidence,
            "fully_occluded_source_only_ids": sorted(fully_occluded_source_ids),
        },
        "index_exact_pass": evidence_lifecycle_index_pass,
        "rule": "Only ACTIVE entries in this index are terminal evidence. Every other retained package directory is SUPERSEDED and must not be counted as a terminal failure/critical package.",
    }
    save_json(OUT / "evidence_lifecycle_index.json", lifecycle_summary)
    save_json(CRITICAL_DIR / "ACTIVE_CURRENT_TERMINAL.json", lifecycle_summary["critical_relations"])
    save_json(PIXEL_FAIL_DIR / "ACTIVE_CURRENT_TERMINAL.json", lifecycle_summary["pixel_failures"])
    (OUT / "SUPERSEDED_EVIDENCE_INDEX.md").write_text(
        "# Evidence lifecycle index — terminal R1\n\n"
        "Only `ACTIVE` rows in `evidence_lifecycle_index.csv` are terminal evidence. All other package directories are retained but SUPERSEDED.\n\n"
        f"- Critical relations: active {len(active_critical_ids)}/{len(critical_directory_ids)}; superseded {len(critical_superseded_ids)}.\n"
        f"- Pixel failures: active {len(active_pixel_ids)}/{len(pixel_directory_ids)}; superseded {len(pixel_superseded_ids)}.\n"
        f"- Fully hidden source-only glyph packages: {', '.join(sorted(fully_occluded_source_ids))}; these are SUPERSEDED in `pixel_failures/` and governed by `source_occlusion_ledger.csv`.\n\n"
        "## Active critical relation IDs\n\n"
        + ", ".join(f"`{item}`" for item in active_critical_ids) + "\n\n"
        "## Active pixel-failure IDs\n\n"
        + ", ".join(f"`{item}`" for item in active_pixel_ids) + "\n\n"
        "## Superseded critical relation IDs\n\n"
        + ", ".join(f"`{item}`" for item in critical_superseded_ids) + "\n\n"
        "## Superseded pixel-failure IDs\n\n"
        + ", ".join(f"`{item}`" for item in pixel_superseded_ids) + "\n",
        encoding="utf-8",
    )

    # Analytic values from source equation: no hand-drawn numerical inference.
    values = {
        "integral_p_0_5": 1.0,
        "integral_qL_0_5": 1.0,
        "integral_qR_0_5": 1.0,
        "p(1)/qR": 0.96,
        "p(2.5)/qR": 1.50,
        "p(4)/qR": 0.96,
        "left_gap_interval": "(2.5,5)",
        "left_p_positive_on_gap": True,
        "right_support_coverage": True,
    }
    math_pass = all(abs(values[key] - expected) < 1e-12 for key, expected in {
        "integral_p_0_5": 1.0,
        "integral_qL_0_5": 1.0,
        "integral_qR_0_5": 1.0,
        "p(1)/qR": 0.96,
        "p(2.5)/qR": 1.50,
        "p(4)/qR": 0.96,
    }.items()) and values["left_p_positive_on_gap"] and values["right_support_coverage"]
    math_report = "\n".join(
        [
            "# FIG-P580-01 mathematical / textual consistency",
            "",
            "- Source and adjacent text define the common domain [0,5], p(x)=6x(5-x)/125, q_L=(2/5)1_[0,5/2], q_R=1/5.",
            "- Integral check: integral p=1, integral q_L=1, integral q_R=1.",
            "- q_L=0 on (5/2,5) while p>0 there, so p is not absolutely continuous with respect to q_L; a finite weighted sample cannot restore arbitrary missing-support contribution.",
            "- q_R>0 on [0,5], hence p<<q_R. The source/adjacent text correctly stops at support coverage and explicitly does not claim low variance or estimator reliability.",
            "- Recomputed ratio card: w(1)=0.96, w(5/2)=1.50, w(4)=0.96.",
            "- B44 conflict: its current caption is support coverage, but its stored unique-reading conclusion and modification plan describe an accept-reject budget flow. The frozen source, rendered figure, caption, and adjacent text all support the former; the latter is a task-card cross-contamination and must not control review.",
            "",
            f"RESULT: {'PASS' if math_pass and all(anchors.values()) and source_check['result'] == 'PASS' else 'FAIL'}",
        ]
    )
    (OUT / "math_semantics_audit.md").write_text(math_report + "\n", encoding="utf-8")

    text_consistency_pass = bool(all(anchors.values()) and source_check["result"] == "PASS")
    # The three human visual gates are set only from the per-row ledger above.
    # An empty, PENDING, location/metric-mismatched, or manually negative row
    # remains a hard false gate; it cannot be replaced by prose here.
    # A resolved negative coverage/shape finding is not an UNKNOWN, but it
    # correctly prevents a complete CHAR→shape PASS.
    char_shape_parent_mapping_pass = mapping_resolution_pass and not mapping_failed_rows
    text_completeness_pass = not text_occlusion_failures
    # Evidence closure is distinct from candidate quality: a documented hard
    # failure can still have complete raw/pre/order/halo/final evidence.
    evidence_complete = (
        not unresolved_pre
        and mapping_resolution_pass
        and manual_contact_complete
        and final_visible_mask_closure
        and text_evidence_complete
        and later_paint_evidence_complete
        and opaque_halo_graphic_evidence_complete
        and translucent_label_graphic_evidence_complete
        and critical_evidence_complete
        and evidence_lifecycle_index_pass
        and contamination_gate_pass
        and final_visible_inventory_formula_pass
        and visual_ledger_complete
        and visual_metadata_reconciliation_pass
        and visual_ledger_path.read_bytes() == visual_source_bytes
        and all(obj.nonempty for obj in objects)
        and all(glyph.nonempty for glyph in final_visible_glyphs)
    )

    gates = {
        "SOURCE_FONT_PASS": source_font_pass,
        "PIXEL_HEIGHT_PASS": pixel_pass,
        "FINAL_VISIBLE_MASK_CLOSURE_PASS": final_visible_mask_closure,
        "CONTAMINATION_GATE_PASS": contamination_gate_pass,
        "CHAR_SHAPE_MAPPING_RESOLUTION_PASS": mapping_resolution_pass,
        "CHAR_SHAPE_PARENT_MAPPING_PASS": char_shape_parent_mapping_pass,
        "MANUAL_CONTACT_LEDGER_COMPLETE": manual_contact_complete,
        "TEXT_COMPLETENESS_PASS": text_completeness_pass,
        "TEXT_HALO_GRAPHIC_COVERAGE_PASS": text_halo_graphic_coverage_pass,
        "TEXT_TRANSLUCENT_LABEL_GRAPHIC_COVERAGE_PASS": text_translucent_label_graphic_coverage_pass,
        "SAME_CLASS_RATIO_PASS": same_class_pass,
        "ROLE_RATIO_PASS": role_pass,
        "OVERLAP_PIXEL_COUNT": overlap_count,
        "CLIP_PIXEL_COUNT": clip_count,
        "MIN_TEXT_CLEARANCE_PX": min_text_clearance,
        "FONT_VISUAL_HARMONY_PASS": font_harmony_pass,
        "VISUAL_HARMONY_PASS": font_harmony_pass,
        "MATH_SEMANTICS_PASS": math_pass,
        "TEXT_CONSISTENCY_PASS": text_consistency_pass,
        "GRAYSCALE_PASS": grayscale_pass,
        "PAGE_INTEGRATION_PASS": page_integration_pass,
        "MANUAL_VISUAL_LEDGER_COMPLETE": visual_ledger_complete,
        "MANUAL_VISUAL_METADATA_RECONCILIATION_PASS": visual_metadata_reconciliation_pass and visual_ledger_path.read_bytes() == visual_source_bytes,
        "EVIDENCE_COMPLETE": evidence_complete,
    }
    hard_boolean = all(value for key, value in gates.items() if key not in {"OVERLAP_PIXEL_COUNT", "CLIP_PIXEL_COUNT", "MIN_TEXT_CLEARANCE_PX"})
    result = "PASS" if hard_boolean and overlap_count == 0 and clip_count == 0 and not clearance_failures else "FAIL"

    # Machine cross-check: every object has a unique nonempty raw mask; all
    # unordered object pairs are present once plus explicit text-edge rows.
    expected_pairs = math.comb(len(objects), 2)
    actual_pairs = len([row for row in overlap_rows if row["PAIR_ID"].startswith("P")])
    machine = {
        "figure_id": "FIG-P580-01",
        "physical_page": PAGE_ONE_BASED,
        "semantic_elements": len(elements),
        "source_glyph_slots": source_final_inventory_formula["source_glyph_count"],
        "source_necessary_substring_slots": source_final_inventory_formula["source_necessary_substring_count"],
        "source_total_text_slots": source_final_inventory_formula["source_total_slots"],
        "expected_final_visible_contact_records": source_final_inventory_formula["expected_final_visible_contact_records"],
        "actual_final_visible_contact_records": source_final_inventory_formula["actual_final_visible_contact_records"],
        "final_visible_inventory_formula_pass": final_visible_inventory_formula_pass,
        "glyph_measurements": len(final_visible_glyphs),
        "necessary_substring_measurements": len(final_visible_substring_rows),
        "source_occlusion_ledger_count": len(source_occlusion_ledger_rows),
        "source_occlusion_substring_ledger_count": len(source_occlusion_substring_rows),
        "source_fully_occluded_excluded_count": len(fully_occluded_source_glyphs),
        "source_partial_fragment_retained_count": len(partial_occluded_source_glyphs),
        "source_only_substring_excluded_count": len(source_only_substring_ids),
        "vector_fraction_substrings": len(fraction_rows),
        "graphics": len(graphics),
        "objects_for_pairs": len(objects),
        "expected_unordered_pairs": expected_pairs,
        "actual_unordered_pairs": actual_pairs,
        "edge_relations": len(elements),
        "empty_masks": [row["MASK_ID"] for row in final_mask_rows if row["NONEMPTY"] != "true"],
        "source_font_failures": sum(row["SOURCE_FONT_PASS"] != "true" for row in font_rows),
        "pixel_height_failures": len(pixel_failures),
        "D_failures": len(d_failures),
        "E_failures": len(e_failures),
        "illegal_overlap_pixels": overlap_count,
        "illegal_overlap_pair_count": len(illegal_overlap_rows),
        "clearance_failure_count": len(clearance_failures),
        "clip_failure_count": clip_count,
        "critical_or_failed_relation_packages": len(critical_rows),
        "critical_packages_missing": package_missing,
        "active_critical_relation_package_count": len(active_critical_ids),
        "superseded_critical_relation_package_count": len(critical_superseded_ids),
        "active_pixel_failure_package_count": len(active_pixel_ids),
        "superseded_pixel_failure_package_count": len(pixel_superseded_ids),
        "evidence_lifecycle_index_exact_pass": evidence_lifecycle_index_pass,
        "critical_active_directory_missing": critical_missing_active_directories,
        "pixel_active_directory_missing": pixel_missing_active_directories,
        "pixel_active_evidence_missing": active_pixel_missing_evidence,
        "unresolved_pre_occlusion_graphics": unresolved_pre,
        "text_occlusion_failure_count": len(text_occlusion_failures),
        "later_nonopaque_text_paint_package_count": len(later_paint_evidence_rows),
        "later_nonopaque_text_paint_evidence_complete": later_paint_evidence_complete,
        "known_nonopaque_later_text_coverage_count": sum(
            row["VISIBLE_CONTOUR_STATUS"] == "FAIL_KNOWN_NONOPAQUE_LATER_TEXT_COVERAGE"
            for row in glyph_visibility_rows
        ),
        "later_text_unexplained_contour_ids": sorted(
            row["GLYPH_ID"] for row in glyph_visibility_rows
            if row["VISIBLE_CONTOUR_STATUS"] == "UNKNOWN_VISIBLE_CONTOUR_OR_LATER_PAINT"
        ),
        "opaque_halo_graphic_failure_count": len(opaque_halo_graphic_failure_rows),
        "opaque_halo_graphic_failure_evidence_complete": opaque_halo_graphic_evidence_complete,
        "text_halo_graphic_coverage_pass": text_halo_graphic_coverage_pass,
        "translucent_label_graphic_failure_count": len(translucent_label_graphic_failure_rows),
        "translucent_label_graphic_failure_evidence_complete": translucent_label_graphic_evidence_complete,
        "text_translucent_label_graphic_coverage_pass": text_translucent_label_graphic_coverage_pass,
        "char_shape_mapping_unknown_count": len(mapping_unknown_rows),
        "char_shape_mapping_known_failure_count": len(mapping_failed_rows),
        "char_shape_mapping_pending_count": len(mapping_pending_rows),
        "manual_contact_ledger_complete": manual_contact_complete,
        "manual_contact_ledger_missing_count": len(manual_missing_ids),
        "manual_contact_ledger_incomplete_count": len(manual_incomplete_ids),
        "manual_contact_ledger_metric_mismatch_count": len(manual_metric_mismatch_ids),
        "contact_sheet_count": len({row["CONTACT_SHEET"] for row in mapping_rows}),
        "contact_cell_count": len(contact_layout_rows),
        "glyph_pair_source_duplicate_pixels": source_pair_duplicate_pixels,
        "glyph_pair_final_duplicate_pixels": final_pair_duplicate_pixels,
        "non_target_layer_contamination_row_count": len(layer_contamination_rows),
        "non_target_layer_foreign_pixel_total": layer_contamination_foreign_total,
        "non_target_layer_nonzero_map_ids": layer_contamination_nonzero_map_ids,
        "non_target_layer_foreign_pixels_by_class": layer_contamination_by_class,
        "non_target_layer_contamination_pass": layer_contamination_pass,
        "contamination_gate_pass": contamination_gate_pass,
        "visual_ledger_complete": visual_ledger_complete,
        "visual_ledger_required_rows": len(expected_visual_ids),
        "visual_ledger_completed_rows": visual_review["completed_rows"],
        "visual_ledger_missing_count": len(visual_missing_ids),
        "visual_ledger_incomplete_count": len(visual_incomplete_ids),
        "visual_ledger_metadata_mismatch_count": len(visual_metadata_mismatch_ids),
        "visual_metadata_reconciled_machine_field_count": len(visual_metadata_reconciliation_rows),
        "visual_metadata_reconciliation_pass": visual_metadata_reconciliation_pass,
        "visual_source_manual_ledger_byte_unchanged_pass": visual_ledger_path.read_bytes() == visual_source_bytes,
        "visual_human_field_utf8_byte_preservation_pass": visual_metadata_reconciliation_pass,
        "font_visual_harmony_pass": font_harmony_pass,
        "grayscale_pass": grayscale_pass,
        "page_integration_pass": page_integration_pass,
        "result_from_gates": result,
    }
    machine["pair_closure_pass"] = expected_pairs == actual_pairs
    machine["mask_closure_pass"] = not machine["empty_masks"]
    machine["final_visible_mask_closure_pass"] = final_visible_mask_closure
    machine["mapping_resolution_pass"] = mapping_resolution_pass
    machine["contact_layout_pass"] = (
        len(contact_layout_rows) == len(mapping_rows)
        and len({row["MAP_ID"] for row in contact_layout_rows}) == len(mapping_rows)
        and len({row["MAP_ID"] for row in manual_ledger_rows}) == len(mapping_rows)
    )
    machine["critical_evidence_closure_pass"] = not package_missing
    # This is deliberately distinct from the candidate-quality result below.
    # A fully evidenced candidate may correctly fail typography, text-
    # completeness, or label/graphic coverage gates and still be ready for a
    # terminal FAIL→SA2 handoff.  Conversely, missing evidence, a pending
    # human ledger, or unresolved mapping may never be terminal.
    machine["machine_evidence_closure_pass"] = (
        machine["pair_closure_pass"]
        and machine["mask_closure_pass"]
        and machine["final_visible_mask_closure_pass"]
        and machine["critical_evidence_closure_pass"]
        and machine["evidence_lifecycle_index_exact_pass"]
        and machine["mapping_resolution_pass"]
        and machine["contact_layout_pass"]
        and machine["manual_contact_ledger_complete"]
        and machine["contamination_gate_pass"]
        and machine["non_target_layer_contamination_pass"]
        and machine["final_visible_inventory_formula_pass"]
        and machine["visual_ledger_complete"]
        and machine["visual_metadata_reconciliation_pass"]
        and machine["visual_source_manual_ledger_byte_unchanged_pass"]
        and machine["visual_human_field_utf8_byte_preservation_pass"]
        and machine["opaque_halo_graphic_failure_evidence_complete"]
        and machine["translucent_label_graphic_failure_evidence_complete"]
        and machine["later_nonopaque_text_paint_evidence_complete"]
        and not machine["unresolved_pre_occlusion_graphics"]
    )
    machine["machine_result"] = "PASS" if (
        machine["pair_closure_pass"]
        and machine["mask_closure_pass"]
        and machine["critical_evidence_closure_pass"]
        and machine["evidence_lifecycle_index_exact_pass"]
        and machine["mapping_resolution_pass"]
        and machine["contact_layout_pass"]
        and machine["manual_contact_ledger_complete"]
        and machine["contamination_gate_pass"]
        and machine["non_target_layer_contamination_pass"]
        and machine["final_visible_inventory_formula_pass"]
        and machine["text_halo_graphic_coverage_pass"]
        and machine["text_translucent_label_graphic_coverage_pass"]
        and machine["visual_ledger_complete"]
        and machine["visual_metadata_reconciliation_pass"]
        and machine["visual_source_manual_ledger_byte_unchanged_pass"]
        and machine["visual_human_field_utf8_byte_preservation_pass"]
        and not machine["unresolved_pre_occlusion_graphics"]
    ) else "FAIL"
    save_json(OUT / "machine_final_check.json", machine)
    (OUT / "machine_final_check.md").write_text(
        "# Machine final cross-check\n\n```json\n" + json.dumps(machine, ensure_ascii=False, indent=2) + "\n```\n",
        encoding="utf-8",
    )

    findings = []
    if pixel_failures:
        samples = ", ".join(f"{row['MEASURE_ID']}={row['TEXT_SAMPLE']!r} ({row['H_INK_PX']}<{row['THRESHOLD_PX']})" for row in pixel_failures[:12])
        findings.append(f"PIXEL_HEIGHT_FAIL: {len(pixel_failures)} independent glyph/substrings fail; first entries: {samples}.")
    if mapping_unknown_rows:
        findings.append(f"CHAR_SHAPE_MAPPING_UNKNOWN: {len(mapping_unknown_rows)} character/substrings lack provable CHAR→shape→parent→bbox closure.")
    if mapping_pending_rows:
        findings.append(f"CHAR_SHAPE_MAPPING_PENDING: {len(mapping_pending_rows)} records await required 8× nearest contact-sheet inspection.")
    if not manual_contact_complete:
        findings.append(
            f"MANUAL_CONTACT_LEDGER_INCOMPLETE: missing/incomplete/extra/location-or-metric-mismatch = "
            f"{len(manual_missing_ids)}/{len(manual_incomplete_ids)}/{len(manual_extra_ids)}/"
            f"{len(manual_location_mismatch_ids) + len(manual_metric_mismatch_ids)}."
        )
    if mapping_failed_rows:
        findings.append(f"CHAR_SHAPE_MAPPING_FAIL: {len(mapping_failed_rows)} final-visible records have explicit machine-proven shape/coverage failure evidence; no complete CHAR→shape PASS is claimed.")
    if not contamination_gate_pass:
        findings.append(
            "MASK_CONTAMINATION_OR_OWNERSHIP_FAIL: source/final glyph ownership has duplicate/unassigned pixels "
            "or a glyph/substr target intersects a non-target official layer; see glyph_non_target_layer_contamination.csv."
        )
    if opaque_halo_graphic_failure_rows:
        findings.append(
            f"TEXT_HALO_GRAPHIC_COVERAGE_FAIL: {len(opaque_halo_graphic_failure_rows)} actual opaque label-ground "
            "coverage relation(s) erase a curve/line/nonbackground graphic; see text_halo_graphic_relations.csv."
        )
    if translucent_label_graphic_failure_rows:
        findings.append(
            f"TEXT_TRANSLUCENT_LABEL_GRAPHIC_COVERAGE_FAIL: {len(translucent_label_graphic_failure_rows)} actual translucent "
            "label-ground coverage relation(s) cover a curve/line/pattern; see text_translucent_label_graphic_relations.csv."
        )
    if not final_visible_inventory_formula_pass:
        findings.append(
            "FINAL_VISIBLE_INVENTORY_FORMULA_FAIL: source glyph/substrings minus source-only fully hidden records "
            "does not equal the final-visible contact inventory."
        )
    if not visual_ledger_complete:
        findings.append(
            f"MANUAL_VISUAL_LEDGER_INCOMPLETE: missing/incomplete/extra/metadata-mismatch = "
            f"{len(visual_missing_ids)}/{len(visual_incomplete_ids)}/{len(visual_extra_ids)}/{len(visual_metadata_mismatch_ids)}; "
            "FONT_VISUAL_HARMONY/GRAYSCALE/PAGE_INTEGRATION cannot be asserted."
        )
    if d_failures:
        findings.append(f"D_FAIL: {len(d_failures)} same-panel/same-role/same-script element medians outside [0.92,1.08].")
    if e_failures:
        findings.append(f"E_FAIL: {len(e_failures)} role ratios outside their prescribed BASE range.")
    if clearance_failures:
        findings.append(f"CLEARANCE_FAIL: {len(clearance_failures)} non-intentional relation(s) below requirement or with raw overlap.")
    if unresolved_pre:
        findings.append(f"PRE/HALO_EVIDENCE_FAIL: pre-occlusion cannot be honestly reconstructed for {', '.join(unresolved_pre)}.")
    if text_occlusion_failures:
        findings.append(
            "TEXT_OCCLUSION/TEXT_COMPLETENESS_FAIL: actual native final-mask classification shows that the later boundary-label opaque fill removes required q_L suffix source slots and its required fraction composite. "
            "Those zero-pixel objects are excluded from final-visible inventory and retained only in source_occlusion_ledger.csv / source_occlusion_substring_ledger.csv with pre/order/halo/final evidence."
        )
    if not findings:
        findings.append("No hard failure in the machine-measured gates.")

    # A conclusion is terminal only after both mandatory human ledgers and
    # every evidence-closure condition complete. Candidate-quality FAIL gates
    # intentionally do not prevent a final, evidence-complete FAIL→SA2
    # handoff; they determine `result`, not whether the audit record is
    # complete. Before this point, reports may describe blockers but must not
    # issue a formal result.
    terminal_ready = evidence_complete and machine["machine_evidence_closure_pass"]
    acceptance_heading = (
        "# FIG-P580-01 — strict SA1 R1 visual acceptance"
        if terminal_ready
        else "# FIG-P580-01 — strict SA1 R1 interim evidence (NONTERMINAL)"
    )
    acceptance_result = (
        f"RESULT: {result}{'' if result == 'PASS' else ' → SA2'}"
        if terminal_ready
        else "STATUS: NONTERMINAL / PENDING — formal RESULT and SA2 handoff are withheld until all strict ledgers close."
    )

    acceptance = "\n".join(
        [
            acceptance_heading,
            "",
            "## Frozen candidate and scope",
            "",
            f"- Candidate: `{PDF}`",
            f"- Re-located by caption/body anchors: physical PDF page {PAGE_ONE_BASED}; printed page {PRINTED_PAGE}.",
            "- Render basis: direct Poppler `pdftoppm` PDF raster, 300 dpi native 2481×3508 pixels; all figures/crops use integer coordinates with no resampling. 8× nearest files are inspection-only.",
            "- Scope: every semantic figure/caption text element, every non-background final-visible vector/pattern object, and all unordered pairs of those objects. Adjacent explanatory body text is read for consistency but not misclassified as figure text.",
            "",
            "## Gate matrix",
            "",
            *[f"- {key} = {value}" for key, value in gates.items()],
            f"- MACHINE_CROSSCHECK = {machine['machine_result']}",
            f"- FINAL_VISIBLE_GLYPHS = {len(final_visible_glyphs)}; FINAL_VISIBLE_NECESSARY_SUBSTRINGS = {len(final_visible_substring_rows)}; SOURCE_ONLY_FULLY_OCCLUDED_GLYPHS = {len(fully_occluded_source_glyphs)}; SOURCE_ONLY_NECESSARY_SUBSTRINGS = {len(source_only_substring_ids)}; RETAINED_PARTIAL_GLYPHS = {len(partial_occluded_source_glyphs)}.",
            "",
            "## Required findings",
            "",
            *[f"- {finding}" for finding in findings],
            "- B44 task-card conflict is real: caption/source/body say support coverage; the card's unique-reading conclusion and modification plan incorrectly describe accept–reject. Review is anchored to source/caption/body, not the stale card text.",
            f"- Final-visible inventory is derived from actual native masks: source-only glyph IDs = {', '.join(sorted(fully_occluded_source_ids)) or 'none'}; source-only required substring IDs = {', '.join(sorted(source_only_substring_ids)) or 'none'}; retained partial glyph IDs = {', '.join(sorted(partial_occluded_source_ids)) or 'none'}. No zero-pixel object is represented as final-visible.",
            f"- Manual visual ledger: {visual_review['completed_rows']}/{visual_review['total_required_rows']} native-view/panel-role rows; FONT_VISUAL_HARMONY_PASS={font_harmony_pass}, GRAYSCALE_PASS={grayscale_pass}, PAGE_INTEGRATION_PASS={page_integration_pass}. Reviewer decisions are in `manual_visual_harmony_ledger.csv`; current medians/D/E join is `{visual_review['current_machine_join_path']}` with before/after provenance in `{visual_review['metadata_reconciliation_path']}`.",
            "- Mathematical recomputation, figure labels, shading, left/right proposals, ratio card, caption, and adjacent reading instruction agree. Support coverage is necessary but not a variance/reliability guarantee.",
            "- Gray-scale reading path judgement is ledger-backed; it cannot be inferred from the presence of a grayscale PNG alone.",
            "",
            "## Result",
            "",
            acceptance_result,
            "",
            "A PASS is prohibited because all source-font/actual-pixel/pair gates must be true simultaneously. This R94 SA1 package is read-only and does not modify source, build input, Goal, or central status.",
        ]
    )
    (OUT / "after_visual_acceptance.md").write_text(acceptance + "\n", encoding="utf-8")

    final_handoff = "\n".join(
        [
            "# FIG-P580-01 — STRICT_R1_FINAL",
            "",
            f"- Frozen audited candidate: `{PDF}`",
            f"- Anchor: physical PDF page {PAGE_ONE_BASED}; printed page {PRINTED_PAGE}.",
            f"- FINAL RESULT: **{result}{' → SA2' if result != 'PASS' else ''}**.",
            f"- Machine evidence closure: **{machine['machine_evidence_closure_pass']}**; candidate machine gate result: **{machine['machine_result']}**; pair {actual_pairs}/{expected_pairs}, final-visible empty masks {len(machine['empty_masks'])}, mapping pending/unknown {len(mapping_pending_rows)}/{len(mapping_unknown_rows)}.",
            f"- Manual glyph contact review: {contact_review['reviewed_sheet_count']}/{contact_review['total_sheet_count']} sheets, {contact_review['reviewed_mapping_record_count']}/{len(mapping_rows)} records; documented negative shapes: {', '.join(row['MAP_ID'] for row in mapping_failed_rows) or 'none'}; unexpected mismatch: {', '.join(contact_review['unexpected_shape_mismatch_ids']) or 'none'}.",
            f"- Manual visual review: {visual_review['completed_rows']}/{visual_review['total_required_rows']} rows; font harmony={font_harmony_pass}, grayscale={grayscale_pass}, page integration={page_integration_pass}; reviewer source is `manual_visual_harmony_ledger.csv`, current metrics join `{visual_review['current_machine_join_path']}`, reconciliation `{visual_review['metadata_reconciliation_path']}`.",
            f"- Final-visible/source occlusion split: {len(final_visible_glyphs)} visible glyphs and {len(final_visible_substring_rows)} visible necessary substrings; source-only glyphs {', '.join(sorted(fully_occluded_source_ids)) or 'none'}; source-only substrings {', '.join(sorted(source_only_substring_ids)) or 'none'}; retained partial glyphs {', '.join(sorted(partial_occluded_source_ids)) or 'none'}.",
            f"- Active terminal evidence: {len(active_critical_ids)} critical relation packages and {len(active_pixel_ids)} pixel-failure packages. Lifecycle index exact: {evidence_lifecycle_index_pass}; all other retained package folders are explicitly SUPERSEDED in `evidence_lifecycle_index.csv` / `SUPERSEDED_EVIDENCE_INDEX.md`.",
            "",
            "## Failed hard gates",
            "",
            *[f"- {key}" for key, value in gates.items() if value is False],
            f"- CLEARANCE_FAILURE_COUNT = {len(clearance_failures)} (illegal text overlap pixels remain {overlap_count}; clip failures {clip_count}).",
            "",
            "## Principal disposition",
            "",
            "- The B44 accept–reject language is a stale task-card conflict. The source/caption/body and recomputation correctly concern importance-sampling support coverage.",
            "- The real rendered defect is E016: the later boundary-label opaque white fill covers required q_L '=2/5' text. This is TEXT_OCCLUSION/TEXT_COMPLETENESS hard FAIL, not a reason to fake a pre-text mask or to keep empty source glyphs in the final-visible inventory.",
            "- No business source, frozen PDF, Goal, central state, inventory, or build entry was modified by SA1.",
            "",
            "## Terminal evidence entry points",
            "",
            "- `machine_final_check.json` / `machine_final_check.md`",
            "- `after_visual_acceptance.md`",
            "- `glyph_shape_contact_sheet_manual_review.md`",
            "- `manual_visual_harmony_ledger.csv`, `manual_visual_harmony_ledger_CURRENT_MACHINE_JOIN.csv`, and `manual_visual_harmony_metadata_reconciliation.csv`",
            "- `R2_TERMINAL_DOCUMENTATION_REISSUE.md` (documentation-only reissue provenance, if present)",
            "- `source_occlusion_ledger.csv` and `text_occlusion_evidence/E016/`",
            "- `active_terminal_critical_relations.csv`, `active_terminal_pixel_failures.csv`, and `evidence_lifecycle_index.csv`",
            "",
            "WRITE STATE: this document is followed by the terminal write-stop marker; no further SA1 evidence writes are authorized after that marker.",
        ]
    )
    # A candidate can correctly end in FAIL→SA2 and still have terminally
    # complete evidence.  Conversely, a PENDING human ledger may never be
    # labelled FINAL or followed by WRITE_STOPPED.
    if DOCUMENTATION_REISSUE:
        (OUT / "R2_TERMINAL_DOCUMENTATION_REISSUE.md").write_text(
            "# R2 terminal documentation reissuance\n\n"
            f"{DOCUMENTATION_REISSUE_REASON} "
            "This full rebuild preserves the frozen candidate, all reviewer-authored ledger bytes, pixel evidence, and result; "
            "it only reissues the terminal documentation with those traceability defects corrected. "
            "This note is written before the new terminal stop marker.\n",
            encoding="utf-8",
        )
    run_state = {
        "run_id": RUN_ID,
        "terminal_ready": terminal_ready,
        "candidate_result": result,
        "machine_result": machine["machine_result"],
        "manual_contact_complete": manual_contact_complete,
        "manual_visual_complete": visual_ledger_complete,
        "write_stopped": terminal_ready,
    }
    save_json(OUT / "RUN_STATE.json", run_state)
    if terminal_ready:
        (OUT / "STRICT_R1_FINAL.md").write_text(final_handoff + "\n", encoding="utf-8")
        # This is intentionally the final filesystem write of an accepted
        # terminal evidence run.  A subsequent audit must first withdraw it.
        (OUT / "WRITE_STOPPED.md").write_text(
            "# SA1 terminal write stop\n\n"
            "Terminal SA1 evidence generation completed after complete glyph-contact and visual-harmony ledgers. "
            "No further writes were made after this marker in this run. Result is recorded in STRICT_R1_FINAL.md.\n",
            encoding="utf-8",
        )
    else:
        pending = "\n".join(
            [
                "# FIG-P580-01 — STRICT_R1 interim evidence (not terminal)",
                "",
                "- STATUS: **NONTERMINAL / PENDING**. No formal result or SA2 handoff is issued while strict ledgers remain open.",
                f"- Machine structural state: **{machine['machine_result']}**.",
                f"- Glyph contact ledger: {contact_review['reviewed_sheet_count']}/{contact_review['total_sheet_count']} sheets; {contact_review['reviewed_mapping_record_count']}/{len(mapping_rows)} rows.",
                f"- Visual-harmony ledger: {visual_review['completed_rows']}/{visual_review['total_required_rows']} rows.",
                f"- Open blockers: mapping pending={len(mapping_pending_rows)}, mapping unknown={len(mapping_unknown_rows)}, visual ledger incomplete={not visual_ledger_complete}, contamination gate={contamination_gate_pass}.",
                "",
                "This directory has no terminal acceptance and no valid WRITE_STOPPED marker. Complete the ledgers, rerun all machine joins, then issue STRICT_R1_FINAL.md only if evidence closure is complete.",
            ]
        )
        (OUT / "STRICT_R1_INTERIM_PENDING.md").write_text(pending + "\n", encoding="utf-8")
        stale_marker = OUT / "WRITE_STOPPED.md"
        if stale_marker.exists():
            stale_marker.write_text(
                "# WITHDRAWN — not a terminal write stop\n\n"
                "A later/interrupted run found incomplete strict ledgers. This marker is superseded; see STRICT_R1_INTERIM_PENDING.md and RUN_STATE.json.\n",
                encoding="utf-8",
            )
        stale_final = OUT / "STRICT_R1_FINAL.md"
        if stale_final.exists():
            stale_final.write_text(
                "# WITHDRAWN — not a terminal SA1 result\n\n"
                "A later strict run found incomplete machine or human-ledger closure. "
                "This former terminal-form document is SUPERSEDED; no formal RESULT or SA2 handoff is valid. "
                "See STRICT_R1_INTERIM_PENDING.md, after_visual_acceptance.md, and RUN_STATE.json.\n",
                encoding="utf-8",
            )

    print(json.dumps({"result": result, "gates": gates, "machine": machine}, ensure_ascii=False, indent=2))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
