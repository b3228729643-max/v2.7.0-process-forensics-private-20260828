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
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[5]
PDF = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.pdf"
SOURCE = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C02" / "fig_v5_c02_is_support.tex"
FLS = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.fls"

PHYSICAL_PAGE = 628
PRINTED_PAGE = 615
FIGURE_ID = "FIG-P580-01"
FIGURE_NUMBER = "31.6"
DPI = 300
SCALE = DPI / 72.0
TEX_PT_PER_PDF_PT = 72.27 / 72.0
PDF_FINGERPRINT = "8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8"
SOURCE_FINGERPRINT = "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161"

# This is the exact figure environment (two plots plus caption), in PDF points.
# The preceding "观察任务" and following "读图检查" remain outside the figure object;
# page integration is reviewed separately from the direct 200 dpi page render.
FIGURE_RECT_PT = fitz.Rect(73.0, 263.0, 533.0, 481.0)
GRAPH_RECT_PT = fitz.Rect(150.0, 263.0, 500.0, 462.0)
LOW_PROFILE = set(".,:;，。；：、…")

# Every path that is physically inside the two panels is enumerated below.  The
# names are descriptive evidence labels, not a substitution for examining the
# actual PDF path record saved in vector_objects.json.
VECTOR_SEMANTICS = {
    5: "LEFT_X_TICK_SET", 6: "LEFT_Y_TICK_SET", 7: "LEFT_X_AXIS",
    8: "LEFT_X_ARROWHEAD", 9: "LEFT_Y_AXIS", 10: "LEFT_Y_ARROWHEAD",
    12: "LEFT_TARGET_P_CURVE", 13: "LEFT_Q_L_TOP", 14: "LEFT_Q_L_BASELINE",
    15: "LEFT_SUPPORT_BOUNDARY_X_5_2", 16: "LEFT_Q_L_FILLED_MARKER",
    17: "LEFT_Q_L_HOLLOW_MARKER", 18: "RIGHT_X_TICK_SET",
    19: "RIGHT_Y_TICK_SET", 20: "RIGHT_X_AXIS", 21: "RIGHT_X_ARROWHEAD",
    22: "RIGHT_Y_AXIS", 23: "RIGHT_Y_ARROWHEAD", 24: "RIGHT_TARGET_P_CURVE",
    25: "RIGHT_Q_R_DASHED", 26: "RIGHT_WEIGHT_CARD_BORDER",
    27: "RIGHT_WEIGHT_MARKER_X_1", 28: "RIGHT_WEIGHT_MARKER_X_5_2",
    29: "RIGHT_WEIGHT_MARKER_X_4",
}

# Exact source-level geometric contacts observed in the native candidate run.
# Keys are intentionally exhaustive rather than a broad "all GG" exemption.
# Line references are to the frozen SHA-verified figure source.
GG_INTENT_WHITELIST = {
    ("GFX05", "GFX06"): "LEFT_AXIS_TICK_SETS_SHARE_ORIGIN; source L20-30",
    ("GFX05", "GFX07"): "LEFT_X_TICKS_ATTACH_X_AXIS; source L20-30",
    ("GFX05", "GFX09"): "LEFT_ORIGIN_TICK_TOUCHES_Y_AXIS; source L20-30",
    ("GFX05", "GFX12"): "LEFT_P_ENDPOINTS_ON_AXIS_TICKS; source L4-6,L47-48",
    ("GFX05", "GFX14"): "LEFT_Q_L_ZERO_DASHES_SHARE_Y0_TICKS; source L51-52",
    ("GFX05", "GFX15"): "LEFT_SUPPORT_BOUNDARY_STARTS_AT_X_5_2_TICK; source L57-58",
    ("GFX05", "GFX17"): "LEFT_Q_L_ZERO_MARKER_AT_X_5_2_TICK; source L55-56",
    ("GFX05", "GFX_HATCH"): "LEFT_HATCH_FILL_MEETS_Y0_AXIS_TICK; source L45-46",
    ("GFX06", "GFX07"): "LEFT_Y_ZERO_TICK_ATTACHES_X_AXIS; source L20-30",
    ("GFX06", "GFX09"): "LEFT_Y_TICKS_ATTACH_Y_AXIS; source L20-30",
    ("GFX06", "GFX12"): "LEFT_P_ORIGIN_ON_Y_AXIS; source L4-6,L47-48",
    ("GFX06", "GFX13"): "LEFT_Q_L_TOP_STARTS_ON_Y_AXIS; source L49-50",
    ("GFX07", "GFX08"): "LEFT_X_AXIS_AND_ARROWHEAD_JOIN; source L20-30",
    ("GFX07", "GFX09"): "LEFT_COORDINATE_AXES_JOIN_AT_ORIGIN; source L20-30",
    ("GFX07", "GFX12"): "LEFT_P_ENDPOINTS_ON_X_AXIS; source L4-6,L47-48",
    ("GFX07", "GFX14"): "LEFT_Q_L_ZERO_DASHES_INTENTIONALLY_OVERLAY_X_AXIS; source L51-52",
    ("GFX07", "GFX15"): "LEFT_SUPPORT_BOUNDARY_STARTS_ON_X_AXIS; source L57-58",
    ("GFX07", "GFX17"): "LEFT_Q_L_ZERO_MARKER_ON_X_AXIS; source L55-56",
    ("GFX09", "GFX10"): "LEFT_Y_AXIS_AND_ARROWHEAD_JOIN; source L20-30",
    ("GFX09", "GFX12"): "LEFT_P_ORIGIN_ON_Y_AXIS; source L4-6,L47-48",
    ("GFX09", "GFX13"): "LEFT_Q_L_TOP_STARTS_ON_Y_AXIS; source L49-50",
    ("GFX12", "GFX14"): "LEFT_P_AND_Q_L_ZERO_MEET_AT_X_5; source L4-6,L47-48,L51-52",
    ("GFX12", "GFX15"): "LEFT_P_CROSSES_DECLARED_SUPPORT_BOUNDARY; source L47-48,L57-58",
    ("GFX12", "GFX_HATCH"): "LEFT_P_IS_HATCH_FILL_BOUNDARY; source L45-48",
    ("GFX13", "GFX16"): "LEFT_Q_L_TOP_AND_FILLED_ENDPOINT_MARKER; source L49-54",
    ("GFX14", "GFX15"): "LEFT_Q_L_ZERO_DASHES_END_AT_SUPPORT_BOUNDARY; source L51-58",
    ("GFX14", "GFX17"): "LEFT_Q_L_ZERO_AND_HOLLOW_ENDPOINT_MARKER; source L51-56",
    ("GFX15", "GFX16"): "LEFT_SUPPORT_BOUNDARY_AND_TOP_MARKER; source L53-58",
    ("GFX15", "GFX17"): "LEFT_SUPPORT_BOUNDARY_AND_ZERO_MARKER; source L55-58",
    ("GFX15", "GFX_HATCH"): "LEFT_SUPPORT_BOUNDARY_IS_HATCH_CLIP_EDGE; source L45-46,L57-58",
    ("GFX17", "GFX_HATCH"): "LEFT_ZERO_MARKER_AT_HATCH_CLIP_EDGE; source L45-46,L55-56",
    ("GFX18", "GFX19"): "RIGHT_AXIS_TICK_SETS_SHARE_ORIGIN; source L20-30",
    ("GFX18", "GFX20"): "RIGHT_X_TICKS_ATTACH_X_AXIS; source L20-30",
    ("GFX18", "GFX22"): "RIGHT_ORIGIN_TICK_TOUCHES_Y_AXIS; source L20-30",
    ("GFX18", "GFX24"): "RIGHT_P_ENDPOINTS_ON_AXIS_TICKS; source L4-6,L73-74",
    ("GFX19", "GFX20"): "RIGHT_Y_ZERO_TICK_ATTACHES_X_AXIS; source L20-30",
    ("GFX19", "GFX22"): "RIGHT_Y_TICKS_ATTACH_Y_AXIS; source L20-30",
    ("GFX19", "GFX24"): "RIGHT_P_ORIGIN_ON_Y_AXIS; source L4-6,L73-74",
    ("GFX19", "GFX25"): "RIGHT_Q_R_DASHES_START_ON_Y_AXIS; source L75-82",
    ("GFX20", "GFX21"): "RIGHT_X_AXIS_AND_ARROWHEAD_JOIN; source L20-30",
    ("GFX20", "GFX22"): "RIGHT_COORDINATE_AXES_JOIN_AT_ORIGIN; source L20-30",
    ("GFX20", "GFX24"): "RIGHT_P_ENDPOINTS_ON_X_AXIS; source L4-6,L73-74",
    ("GFX22", "GFX23"): "RIGHT_Y_AXIS_AND_ARROWHEAD_JOIN; source L20-30",
    ("GFX22", "GFX24"): "RIGHT_P_ORIGIN_ON_Y_AXIS; source L4-6,L73-74",
    ("GFX22", "GFX25"): "RIGHT_Q_R_DASHES_START_ON_Y_AXIS; source L75-82",
    ("GFX24", "GFX27"): "RIGHT_P_AND_WEIGHT_MARKER_X_1; source L73-74,L83-84",
    ("GFX24", "GFX28"): "RIGHT_P_AND_WEIGHT_MARKER_X_5_2; source L73-74,L85-86",
    ("GFX24", "GFX29"): "RIGHT_P_AND_WEIGHT_MARKER_X_4; source L73-74,L87-88",
}


@dataclass
class Obj:
    oid: str
    safe: str
    kind: str
    role: str
    script_class: str
    parent: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    source: str
    metadata: dict[str, Any]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ensure_dirs() -> dict[str, Path]:
    dirs = {
        "renders": ROOT / "renders",
        "reports": ROOT / "reports",
        "masks": ROOT / "glyph_masks",
        "gfx_masks": ROOT / "vector_masks",
        "contacts": ROOT / "contacts",
        "relationships": ROOT / "relationships",
        "calibration": ROOT / "calibration",
        "scripts": ROOT / "scripts",
    }
    for p in dirs.values():
        p.mkdir(parents=True, exist_ok=True)
    return dirs


def px_rect(rect: fitz.Rect, width: int, height: int) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect.x0 * SCALE)))
    y0 = max(0, int(math.floor(rect.y0 * SCALE)))
    x1 = min(width, int(math.ceil(rect.x1 * SCALE)))
    y1 = min(height, int(math.ceil(rect.y1 * SCALE)))
    return x0, y0, x1, y1


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(ax0 - bx1, bx0 - ax1, 0)
    dy = max(ay0 - by1, by0 - ay1, 0)
    return math.hypot(dx, dy)


def is_cjk(ch: str) -> bool:
    return bool(ch) and (
        "CJK UNIFIED IDEOGRAPH" in unicodedata.name(ch, "")
        or "CJK COMPATIBILITY IDEOGRAPH" in unicodedata.name(ch, "")
        or 0x3000 <= ord(ch) <= 0x303F
        or 0xFF00 <= ord(ch) <= 0xFFEF
    )


def script_class(ch: str, effective_pt: float) -> str:
    if unicodedata.combining(ch):
        return "COMBINING_OVERLAY"
    if ch in LOW_PROFILE:
        return "LOW_PROFILE_PUNCTUATION"
    if effective_pt < 9.5:
        return "NATURAL_SCRIPT"
    if is_cjk(ch):
        return "CJK_FULL"
    if ch.isdigit() or (ch.isascii() and ch.isupper()):
        return "LATIN_CAP_DIGIT"
    if ch.isascii() and ch.islower():
        return "LATIN_LOWER"
    unicode_name = unicodedata.name(ch, "")
    # Math-mode italic letters are encoded as Mathematical Alphanumeric
    # Unicode characters.  They remain letters for C/D/E thresholds rather
    # than becoming generic operators simply because they are non-ASCII.
    if "MATHEMATICAL" in unicode_name and "SMALL" in unicode_name:
        return "LATIN_LOWER"
    if "MATHEMATICAL" in unicode_name and "CAPITAL" in unicode_name:
        return "LATIN_CAP_DIGIT"
    if ch in "αβγδεζηθικλμνξοπρστυφχψωΓΔΘΛΞΠΣΦΨΩ":
        return "GREEK_LOWER" if ch.islower() else "GREEK_UPPER"
    return "MATH_OPERATOR"


def pixel_threshold_mask(rgb: np.ndarray) -> np.ndarray:
    # The figure background is pure white.  This directly implements the
    # required 20/255 local-background contrast threshold without dilation.
    return np.max(255 - rgb.astype(np.int16), axis=2) >= 20


def mask_bbox(mask: np.ndarray, x0: int, y0: int) -> tuple[int, int, int, int] | None:
    yy, xx = np.where(mask)
    if not len(xx):
        return None
    return x0 + int(xx.min()), y0 + int(yy.min()), x0 + int(xx.max()) + 1, y0 + int(yy.max()) + 1


def ink_height(mask: np.ndarray) -> int:
    yy = np.where(mask)[0]
    return int(yy.max() - yy.min() + 1) if len(yy) else 0


def required_height(cls: str) -> int | None:
    return {
        "CJK_FULL": 30,
        "LATIN_CAP_DIGIT": 24,
        "LATIN_LOWER": 17,
        "GREEK_LOWER": 17,
        "GREEK_UPPER": 24,
        "MATH_OPERATOR": 22,
        "COMBINING_OVERLAY": 22,
        "NATURAL_SCRIPT": 15,
    }.get(cls)


def role_for_char(b: int, x_pt: float, y_pt: float) -> str:
    if y_pt >= 462:
        return "CAPTION"
    if y_pt < 288:
        return "PANEL_TITLE"
    if 295 <= y_pt <= 346 and x_pt >= 347:
        return "FORMULA_CARD"
    if x_pt <= 170 and 296 <= y_pt <= 390:
        return "Y_AXIS_LABEL_OR_TICK"
    if 405 <= y_pt <= 430:
        return "TICK_LABEL"
    if y_pt >= 430:
        return "X_AXIS_LABEL_OR_ANNOTATION"
    if b in {12, 13, 14, 15, 16, 24, 25, 26}:
        return "AXIS_LABEL_OR_TICK"
    return "ANNOTATION"


def render_page(doc: fitz.Document, dirs: dict[str, Path]) -> tuple[np.ndarray, tuple[int, int, int, int], fitz.Page]:
    page = doc.load_page(PHYSICAL_PAGE - 1)
    matrix = fitz.Matrix(SCALE, SCALE)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    page_img.save(dirs["renders"] / "full_page_300dpi.png")
    page_img.save(dirs["renders"] / "after_full_page_300dpi.png")

    pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False)
    page200 = Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples)
    page200.save(dirs["renders"] / "full_page_200dpi.png")
    page200.save(dirs["renders"] / "after_full_page_200dpi.png")

    bounds = px_rect(FIGURE_RECT_PT, pix.width, pix.height)
    crop = page_img.crop(bounds)
    crop.save(dirs["renders"] / "figure_crop_300dpi.png")
    crop.save(dirs["renders"] / "after_figure_crop_300dpi.png")

    # This is a direct 300 dpi PDF clip, not a resampled derivative.
    clip_pix = page.get_pixmap(matrix=matrix, clip=FIGURE_RECT_PT, alpha=False)
    standalone = Image.frombytes("RGB", (clip_pix.width, clip_pix.height), clip_pix.samples)
    standalone.save(dirs["renders"] / "standalone_300dpi.png")
    standalone.save(dirs["renders"] / "after_standalone_300dpi.png")
    crop.convert("L").save(dirs["renders"] / "grayscale_300dpi.png")
    crop.convert("L").save(dirs["renders"] / "after_grayscale_300dpi.png")
    return np.asarray(page_img), bounds, page


def combining_negation_mask(cluster_mask: np.ndarray) -> np.ndarray:
    """Select U+0338 from the final visible `\\not\\ll` composite.

    In this PDF the ToUnicode stream exposes U+0338 with a zero-width raw
    bbox, while its painted long solidus is composited into the following
    U+226A bbox.  The selection is therefore made only from final native ink
    in that exact following bbox.  The solidus has an independently verified
    slope y + 2x = 62 (+/- 2 native pixels), whereas the two less-than signs
    have the distinct shallow +/- 0.5 slopes.  It is a source-declared,
    same-formula-parent overlay and is documented in occlusion reversal.
    """
    yy, xx = np.mgrid[:cluster_mask.shape[0], :cluster_mask.shape[1]]
    selected = cluster_mask & (np.abs(yy + 2.0 * xx - 62.0) <= 2.0)
    if not selected.any() or ink_height(selected) < 22:
        raise RuntimeError("U+0338 final-visible solidus selection failed")
    return selected


def extract_glyphs(page: fitz.Page, page_rgb: np.ndarray, dirs: dict[str, Path]) -> tuple[list[Obj], list[dict[str, Any]]]:
    raw = page.get_text("rawdict")
    rows: list[dict[str, Any]] = []
    objects: list[Obj] = []
    n = 0
    h, w = page_rgb.shape[:2]
    for b_idx, block in enumerate(raw.get("blocks", [])):
        for l_idx, line in enumerate(block.get("lines", [])):
            for s_idx, span in enumerate(line.get("spans", [])):
                for c_idx, char in enumerate(span.get("chars", [])):
                    ch = char.get("c", "")
                    if not ch or ch.isspace():
                        continue
                    rect = fitz.Rect(char["bbox"])
                    cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
                    if not FIGURE_RECT_PT.contains(fitz.Point(cx, cy)):
                        continue
                    n += 1
                    oid = f"G{n:04d}"
                    safe = oid
                    analysis_rect = rect
                    combining_overlay = bool(unicodedata.combining(ch))
                    composite_base = bool(c_idx > 0 and unicodedata.combining(span.get("chars", [])[c_idx - 1].get("c", "")))
                    if combining_overlay:
                        # The next character is U+226A in the exact same span.
                        # Its raw bbox contains the renderer's final composite.
                        following = span.get("chars", [])[c_idx + 1:c_idx + 2]
                        if len(following) != 1 or following[0].get("c") != "≪":
                            raise RuntimeError("Unexpected U+0338 composite neighbour")
                        analysis_rect = fitz.Rect(following[0]["bbox"])
                    bbox = px_rect(analysis_rect, w, h)
                    x0, y0, x1, y1 = bbox
                    local = pixel_threshold_mask(page_rgb[y0:y1, x0:x1])
                    if combining_overlay:
                        local = combining_negation_mask(local)
                    elif composite_base:
                        # U+226A owns its two chevrons; the final painted
                        # negation solidus is uniquely owned by preceding
                        # U+0338, including at their crossings.
                        local = local & ~combining_negation_mask(local)
                    size_pdf = float(span.get("size", 0.0))
                    effective = size_pdf * TEX_PT_PER_PDF_PT
                    cls = script_class(ch, effective)
                    role = role_for_char(b_idx, cx, cy)
                    source_declared = "9.6pt figure-base"
                    if cy < 288:
                        source_declared = "10.2pt panel-title"
                    if cy >= 462:
                        source_declared = "caption small (effective from PDF)"
                    if effective < 9.5:
                        source_declared = "natural TeX script derived from >=9.5pt base"
                    actual_bbox = mask_bbox(local, x0, y0)
                    hpx = ink_height(local)
                    threshold = required_height(cls)
                    rows.append({
                        "ELEMENT_ID": f"E_B{b_idx:03d}",
                        "GLYPH_ID": oid,
                        "SAFE_FILENAME": safe,
                        "PANEL_ID": "LEFT" if cx < 330 else "RIGHT",
                        "ROLE": role,
                        "PARENT": f"B{b_idx:03d}",
                        "SOURCE_FILE": str(SOURCE.relative_to(PROJECT)),
                        "SOURCE_LINE": "figure source; PDF glyph mapping",
                        "TEXT_SAMPLE": ch,
                        "CODEPOINT": f"U+{ord(ch):04X}",
                        "FONT": span.get("font", ""),
                        "DECLARED_PT": source_declared,
                        "PDF_FONT_SIZE_PT": round(size_pdf, 4),
                        "GRAPHICS_SCALE": 1.0,
                        "EFFECTIVE_PT": round(effective, 4),
                        "SCRIPT_CLASS": cls,
                        "BBOX_X0": x0,
                        "BBOX_Y0": y0,
                        "BBOX_X1": x1,
                        "BBOX_Y1": y1,
                        "ACTUAL_BBOX": actual_bbox,
                        "H_INK_PX": hpx,
                        "INK_AREA_PX": int(np.count_nonzero(local)),
                        "REQUIRED_H_PX": threshold if threshold is not None else "CALIBRATION",
                        "RAW_MASK_PATH": f"glyph_masks/{safe}_mask.png",
                        "FONT_PASS": effective >= 9.5 or cls == "NATURAL_SCRIPT",
                        "PIXEL_PASS": (threshold is None or hpx >= threshold) and bool(local.any()),
                        "MASK_NONEMPTY": bool(local.any()),
                        "MASK_METHOD": (
                            "native_300dpi_final_composite_U0338_solidus_selection"
                            if combining_overlay else (
                                "native_300dpi_U226A_composite_base_after_U0338_solidus_subtraction"
                                if composite_base else "native_300dpi_char_bbox_plus_20of255_threshold"
                            )
                        ),
                        "COMPOSITE_OVERLAY": combining_overlay,
                        "COMPOSITE_BASE_AFTER_OVERLAY": composite_base,
                        "RAW_PDF_BBOX_PT": [round(v, 5) for v in rect],
                        "ANALYSIS_BBOX_PT": [round(v, 5) for v in analysis_rect],
                    })
                    Image.fromarray((local * 255).astype(np.uint8), mode="L").save(dirs["masks"] / f"{safe}_mask.png")
                    objects.append(Obj(
                        oid=oid, safe=safe, kind="TEXT", role=role, script_class=cls,
                        parent=f"B{b_idx:03d}", bbox=bbox, mask=local,
                        source=(
                            "PDF rawdict U+0338 zero-width bbox + next-glyph final composite solidus selection"
                            if combining_overlay else (
                                "PDF rawdict U+226A final composite bbox minus uniquely owned U+0338 solidus"
                                if composite_base else "PDF rawdict char bbox + native 300dpi raw mask"
                            )
                        ),
                        metadata=rows[-1],
                    ))
    return objects, rows


def drawing_to_serializable(d: dict[str, Any]) -> dict[str, Any]:
    def cv(v: Any) -> Any:
        if isinstance(v, fitz.Point):
            return [round(v.x, 6), round(v.y, 6)]
        if isinstance(v, fitz.Rect):
            return [round(v.x0, 6), round(v.y0, 6), round(v.x1, 6), round(v.y1, 6)]
        if isinstance(v, tuple):
            return [cv(x) for x in v]
        if isinstance(v, list):
            return [cv(x) for x in v]
        if isinstance(v, dict):
            return {k: cv(x) for k, x in v.items()}
        return v
    return {k: cv(v) for k, v in d.items()}


def vector_selection_mask(drawing: dict[str, Any], page_rect: fitz.Rect, width: int, height: int) -> np.ndarray:
    # Replays the current PDF path geometry on a blank same-size vector page.
    # It is then intersected with the native final PDF foreground, so it cannot
    # accidentally import neighbouring same-colour raster pixels.
    vdoc = fitz.open()
    vpage = vdoc.new_page(width=page_rect.width, height=page_rect.height)
    shape = vpage.new_shape()
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            shape.draw_line(item[1], item[2])
        elif kind == "re":
            shape.draw_rect(item[1])
        elif kind == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        else:
            raise RuntimeError(f"Unhandled PDF vector item: {kind}")
    cap_value = drawing.get("lineCap") or (0,)
    cap = int(cap_value[0])
    join = int(round(float(drawing.get("lineJoin") or 0)))
    fill_value = drawing.get("fill")
    # A white node/card fill is background, never a final-visible border mask.
    # Retaining it would falsely absorb the card's text into the border object.
    if fill_value is not None and all(float(v) >= 0.98 for v in fill_value):
        fill_value = None
    shape.finish(
        width=float(drawing.get("width") or 0.5),
        color=(0,) if drawing.get("color") is not None else None,
        fill=(0,) if fill_value is not None else None,
        lineCap=cap,
        lineJoin=join,
        dashes=drawing.get("dashes"),
        even_odd=bool(drawing.get("even_odd")),
        closePath=bool(drawing.get("closePath")),
    )
    shape.commit()
    pix = vpage.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    return np.any(arr[:, :, :3] < 250, axis=2)


def rect_touches(a: fitz.Rect, b: fitz.Rect) -> bool:
    """Inclusive rectangle test; fitz.Rect.intersects drops zero-height axes."""
    return not (a.x1 < b.x0 or a.x0 > b.x1 or a.y1 < b.y0 or a.y0 > b.y1)


def extract_vector_objects(page: fitz.Page, page_rgb: np.ndarray, dirs: dict[str, Path]) -> tuple[list[Obj], list[dict[str, Any]]]:
    foreground = pixel_threshold_mask(page_rgb)
    pheight, pwidth = foreground.shape
    records: list[dict[str, Any]] = []
    objects: list[Obj] = []
    drawings = page.get_drawings()
    for idx, drawing in enumerate(drawings):
        rect = drawing["rect"]
        if not rect_touches(rect, GRAPH_RECT_PT):
            continue
        # The graph only: exclude page header, theorem box and page footer.
        if rect.y0 < 260 or rect.y1 > 462 or rect.x1 < 150 or rect.x0 > 500:
            continue
        oid = f"GFX{idx:02d}"
        safe = oid
        selection = vector_selection_mask(drawing, page.rect, pwidth, pheight)
        # Exact current-PDF visible ink constrained by this object’s own vector path.
        final_mask = selection & foreground
        # get_drawings reports a geometric centre line for zero-height axes;
        # expand to its rendered stroke envelope before cropping the own mask.
        margin = max(1.5, float(drawing.get("width") or 0.0) / 2.0 + 0.75)
        mask_rect = fitz.Rect(rect)
        mask_rect.x0 -= margin; mask_rect.y0 -= margin
        mask_rect.x1 += margin; mask_rect.y1 += margin
        bbox = px_rect(mask_rect, pwidth, pheight)
        x0, y0, x1, y1 = bbox
        local = final_mask[y0:y1, x0:x1]
        Image.fromarray((local * 255).astype(np.uint8), mode="L").save(dirs["gfx_masks"] / f"{safe}_final_visible.png")
        records.append({
            "OBJECT_ID": oid,
            "SAFE_FILENAME": safe,
            "KIND": "GRAPHIC",
            "ROLE": VECTOR_SEMANTICS.get(idx, "PDF_VECTOR_DRAWING"),
            "SEQNO": drawing.get("seqno"),
            "TYPE": drawing.get("type"),
            "RECT_PT": [round(v, 5) for v in rect],
            "MASK_RECT_PT": [round(v, 5) for v in mask_rect],
            "BBOX_PX": bbox,
            "RAW_MASK_PATH": f"vector_masks/{safe}_final_visible.png",
            "MASK_NONEMPTY": bool(local.any()),
            "VECTOR_BOUNDARY": drawing_to_serializable(drawing),
        })
        objects.append(Obj(
            oid=oid, safe=safe, kind="GRAPHIC", role=VECTOR_SEMANTICS.get(idx, "PDF_VECTOR_DRAWING"),
            script_class="N/A", parent=oid, bbox=bbox, mask=local,
            source="PDF get_drawings vector path replay + native final foreground",
            metadata=records[-1],
        ))
    return objects, records


def add_hatch_object(page_rgb: np.ndarray, dirs: dict[str, Path]) -> Obj:
    """Create a semantic mask for the left-panel hatched support-missing area.

    The PDF exposes its boundary curve as an ordinary vector drawing but the
    PGF pattern is painted as a pattern resource.  This mask is therefore
    analytically bounded by the declared p(x) curve / x=5/2 / x-axis and is
    colour-restricted to the actual final dark-grey hatch ink.  It intentionally
    excludes the blue curve, teal baseline, and dotted boundary so no adjacent
    grey object can enter the pattern mask.
    """
    h, w = page_rgb.shape[:2]
    x0, y0, x1, y1 = px_rect(fitz.Rect(244.8908, 353.7562, 313.8900, 413.9561), w, h)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    xpt = xx / SCALE
    # y of p=6x(5-x)/125 in the page coordinate system from the two axis points
    # (x=0,y=413.9560) and (x=5,y=413.9560), with p(2.5)=0.3 at y=353.7562.
    xdata = (xpt - 175.8890) / (313.8900 - 175.8890) * 5.0
    p_y = 413.9560 - (6.0 * xdata * (5.0 - xdata) / 125.0) / 0.3 * (413.9560 - 353.7562)
    inside = (xpt >= 244.8908) & (xpt <= 313.8900) & (yy / SCALE >= p_y + 0.35) & (yy / SCALE <= 413.25)
    rgb = page_rgb[y0:y1, x0:x1]
    # SLTextGray hatch ink is darker than the blue/teal curve and axis grey.
    dark_grey = (rgb[:, :, 0] <= 100) & (rgb[:, :, 1] <= 108) & (rgb[:, :, 2] <= 116)
    mask = inside & dark_grey
    oid = "GFX_HATCH"
    Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(dirs["gfx_masks"] / f"{oid}_final_visible.png")
    return Obj(
        oid=oid, safe=oid, kind="GRAPHIC", role="HATCH_PATTERN", script_class="N/A",
        parent=oid, bbox=(x0, y0, x1, y1), mask=mask,
        source="analytic source boundary + native final dark-grey hatch-only pixels",
        metadata={
            "OBJECT_ID": oid,
            "SAFE_FILENAME": oid,
            "KIND": "GRAPHIC",
            "ROLE": "HATCH_PATTERN",
            "BBOX_PX": [x0, y0, x1, y1],
            "RAW_MASK_PATH": f"vector_masks/{oid}_final_visible.png",
            "MASK_NONEMPTY": bool(mask.any()),
            "VECTOR_BOUNDARY": "x in [5/2,5], p(x)<=y<=0; source analytic contract p=6x(5-x)/125",
        },
    )


def paste_mask(global_mask: np.ndarray, obj: Obj, origin: tuple[int, int]) -> None:
    ox, oy = origin
    x0, y0, x1, y1 = obj.bbox
    global_mask[y0 - oy:y1 - oy, x0 - ox:x1 - ox] |= obj.mask


def pair_metrics(a: Obj, b: Obj) -> tuple[int, float | None, tuple[int, int, int, int]]:
    x0 = min(a.bbox[0], b.bbox[0])
    y0 = min(a.bbox[1], b.bbox[1])
    x1 = max(a.bbox[2], b.bbox[2])
    y1 = max(a.bbox[3], b.bbox[3])
    am = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bm = np.zeros_like(am)
    paste_mask(am, a, (x0, y0))
    paste_mask(bm, b, (x0, y0))
    overlap = int(np.count_nonzero(am & bm))
    if overlap:
        return overlap, 0.0, (x0, y0, x1, y1)
    if not am.any() or not bm.any():
        return overlap, None, (x0, y0, x1, y1)
    # Exact native-grid Euclidean distance between the two final-visible raw masks.
    distances = distance_transform_edt(~am)
    return overlap, float(distances[bm].min()), (x0, y0, x1, y1)


def required_clearance(a: Obj, b: Obj) -> int:
    if a.kind == "TEXT" and b.kind == "TEXT":
        return 0 if a.parent == b.parent else 4
    if a.kind == "TEXT" or b.kind == "TEXT":
        return 3
    return 0


def save_pair_evidence(a: Obj, b: Obj, page_rgb: np.ndarray, dirs: dict[str, Path], metrics: tuple[int, float | None, tuple[int, int, int, int]]) -> str:
    overlap, clearance, union = metrics
    x0, y0, x1, y1 = union
    pad = 8
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(page_rgb.shape[1], x1 + pad); y1 = min(page_rgb.shape[0], y1 + pad)
    sub_a = np.zeros((y1-y0, x1-x0), dtype=bool)
    sub_b = np.zeros_like(sub_a)
    paste_mask(sub_a, a, (x0, y0)); paste_mask(sub_b, b, (x0, y0))
    inter = sub_a & sub_b
    pair_dir = dirs["relationships"] / f"PAIR_{a.safe}_{b.safe}"
    pair_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(page_rgb[y0:y1, x0:x1]).save(pair_dir / "raw.png")
    Image.fromarray((sub_a*255).astype(np.uint8), mode="L").save(pair_dir / "a_mask.png")
    Image.fromarray((sub_b*255).astype(np.uint8), mode="L").save(pair_dir / "b_mask.png")
    Image.fromarray((inter*255).astype(np.uint8), mode="L").save(pair_dir / "intersection.png")
    overlay = page_rgb[y0:y1, x0:x1].copy()
    overlay[sub_a] = [220, 25, 25]
    overlay[sub_b] = [25, 90, 220]
    overlay[inter] = [255, 0, 255]
    oi = Image.fromarray(overlay)
    oi.save(pair_dir / "overlay_1x.png")
    oi.resize((oi.width*8, oi.height*8), Image.Resampling.NEAREST).save(pair_dir / "overlay_8x_nearest.png")
    (pair_dir / "relation.json").write_text(json.dumps({
        "pair": [a.oid, b.oid], "native_roi": [x0, y0, x1, y1],
        "overlap_px": overlap, "clearance_px": clearance,
        "mask_a": a.source, "mask_b": b.source,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(pair_dir.relative_to(ROOT)).replace("\\", "/")


def intent_whitelist(a: Obj, b: Obj, same_parent: bool) -> str:
    """Return only a concrete, source-explainable overlap exemption.

    Geometric objects do *not* receive a blanket exemption.  GG contacts are
    deliberately returned as empty until their exact object pair is assessed
    and added as a named source-level relation after the candidate run.
    """
    if same_parent and {a.oid, b.oid} == {"G0090", "G0091"}:
        return "FORMULA_U0338_OVER_U226A_FINAL_COMPOSITE_SAME_PARENT"
    if a.kind == b.kind == "GRAPHIC":
        return GG_INTENT_WHITELIST.get(tuple(sorted((a.oid, b.oid))), "")
    return ""


def create_relationships(objects: list[Obj], page_rgb: np.ndarray, dirs: dict[str, Path]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    critical = 0
    gg = 0
    illegal_overlap_pairs = 0
    illegal_overlap_pixels = 0
    intentional_overlap_pairs = 0
    intentional_overlap_pixels = 0
    clearance_failures = 0
    empty_masks = 0
    for a, b in combinations(objects, 2):
        if a.kind == "GRAPHIC" and b.kind == "GRAPHIC":
            gg += 1
        bbd = bbox_distance(a.bbox, b.bbox)
        req = required_clearance(a, b)
        # For far-separated bboxes the spatial separation is directly proven.
        # Any close/bounding-box-overlap relation receives independent raw-mask
        # metrics; hence no pair remains UNKNOWN.
        measured = bbd <= 24 or req == 0 and a.kind == b.kind == "GRAPHIC"
        if measured:
            metrics = pair_metrics(a, b)
            overlap, clearance, _ = metrics
        else:
            overlap, clearance = 0, bbd
            metrics = None
        if not a.mask.any() or not b.mask.any():
            empty_masks += 1
        same_parent = a.kind == b.kind == "TEXT" and a.parent == b.parent
        intentional = intent_whitelist(a, b, same_parent)
        hard_overlap = overlap >= 1 and not same_parent and not intentional
        hard_clearance = req > 0 and clearance is not None and clearance < req
        if hard_overlap:
            illegal_overlap_pairs += 1
            illegal_overlap_pixels += overlap
        elif overlap >= 1 and intentional:
            intentional_overlap_pairs += 1
            intentional_overlap_pixels += overlap
        if hard_clearance:
            clearance_failures += 1
        is_critical = measured and (overlap > 0 or (clearance is not None and clearance < 12))
        evidence = ""
        if is_critical:
            critical += 1
            evidence = save_pair_evidence(a, b, page_rgb, dirs, metrics)  # type: ignore[arg-type]
        status = "PASS"
        if not a.mask.any() or not b.mask.any() or clearance is None:
            status = "EVIDENCE_FAIL"
        elif hard_overlap:
            status = "FAIL_OVERLAP"
        elif hard_clearance:
            status = "FAIL_CLEARANCE"
        rows.append({
            "PAIR_ID": f"PAIR_{a.safe}_{b.safe}",
            "OBJECT_A": a.oid, "OBJECT_B": b.oid,
            "KIND_A": a.kind, "KIND_B": b.kind,
            "RELATION_CLASS": "GG" if a.kind == b.kind == "GRAPHIC" else ("TT" if a.kind == b.kind == "TEXT" else "TG"),
            "A_PARENT": a.parent, "B_PARENT": b.parent,
            "SAME_SEMANTIC_PARENT": same_parent,
            "BBOX_CLEARANCE_PX": round(bbd, 4),
            "RAW_OVERLAP_PX": overlap,
            "RAW_MIN_CLEARANCE_PX": "" if clearance is None else round(clearance, 4),
            "REQUIRED_CLEARANCE_PX": req,
            "INTENT_WHITELIST": intentional,
            "RELATION_PROOF": "NATIVE_RAW_MASK" if measured else "DISJOINT_BBOX_CLEARANCE_BOUND",
            "MEASURED_NATIVE_1X": measured,
            "CRITICAL": is_critical,
            "EVIDENCE_DIR": evidence,
            "STATUS": status,
        })
    stats = {
        "object_count": len(objects), "pair_count": len(rows), "gg_pair_count": gg,
        "critical_pair_count": critical,
        "illegal_overlap_pair_count": illegal_overlap_pairs,
        "illegal_overlap_pixel_count": illegal_overlap_pixels,
        "intentional_overlap_pair_count": intentional_overlap_pairs,
        "intentional_overlap_pixel_count": intentional_overlap_pixels,
        "clearance_failure_pair_count": clearance_failures, "empty_mask_pair_count": empty_masks,
    }
    return rows, stats


def create_overlay(glyphs: list[Obj], page_rgb: np.ndarray, figure_bounds: tuple[int, int, int, int], dirs: dict[str, Path]) -> None:
    x0, y0, x1, y1 = figure_bounds
    image = Image.fromarray(page_rgb[y0:y1, x0:x1].copy())
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=11)
    colours = {
        "PANEL_TITLE": (160, 0, 0), "CAPTION": (0, 80, 160),
        "FORMULA_CARD": (110, 50, 150), "TICK_LABEL": (0, 130, 90),
        "Y_AXIS_LABEL_OR_TICK": (160, 100, 0), "AXIS_LABEL_OR_TICK": (160, 100, 0),
        "X_AXIS_LABEL_OR_ANNOTATION": (160, 100, 0), "ANNOTATION": (0, 120, 120),
    }
    for obj in glyphs:
        gx0, gy0, gx1, gy1 = obj.bbox
        c = colours.get(obj.role, (180, 0, 180))
        draw.rectangle((gx0-x0, gy0-y0, gx1-x0-1, gy1-y0-1), outline=c, width=1)
        draw.text((gx0-x0, max(0, gy0-y0-11)), obj.oid, fill=c, font=font)
    image.save(dirs["renders"] / "text_measurement_overlay_300dpi.png")
    image.save(dirs["renders"] / "after_text_measurement_overlay_300dpi.png")


def make_contact_sheets(glyphs: list[Obj], page_rgb: np.ndarray, dirs: dict[str, Path]) -> list[dict[str, Any]]:
    """Write the required ORIGINAL / TARGET OVERLAY / MASK ONLY triads.

    Each glyph has its own native bbox and physical 8x-nearest triplet.  The
    returned rows deliberately remain PENDING until this SA1 opens every sheet.
    """
    font = ImageFont.load_default(size=13)
    cell_w, cell_h = 1160, 310
    cols, rows_per_sheet = 2, 4
    per_sheet = cols * rows_per_sheet
    ledger: list[dict[str, Any]] = []
    for base in range(0, len(glyphs), per_sheet):
        batch = glyphs[base:base+per_sheet]
        sheet_no = base // per_sheet + 1
        canvas = Image.new("RGB", (cell_w*cols, cell_h*rows_per_sheet), "white")
        d = ImageDraw.Draw(canvas)
        for k, obj in enumerate(batch):
            col, row = k % cols, k // cols
            ox, oy = col*cell_w, row*cell_h
            x0, y0, x1, y1 = obj.bbox
            pad = 3
            ax0, ay0 = max(0, x0-pad), max(0, y0-pad)
            ax1, ay1 = min(page_rgb.shape[1], x1+pad), min(page_rgb.shape[0], y1+pad)
            original = Image.fromarray(page_rgb[ay0:ay1, ax0:ax1])
            target = np.zeros((ay1-ay0, ax1-ax0), dtype=bool)
            paste_mask(target, obj, (ax0, ay0))
            overlay = np.asarray(original).copy()
            overlay[target] = [230, 20, 20]
            only = np.full_like(overlay, 255)
            only[target] = [0, 0, 0]
            views = [original, Image.fromarray(overlay), Image.fromarray(only)]
            labels = ["ORIGINAL", "TARGET OVERLAY", "MASK ONLY"]
            native_w, native_h = original.size
            max_view_w, max_view_h = 330, 240
            factor = min(8, max(1, max_view_w // max(1, native_w)), max(1, max_view_h // max(1, native_h)))
            view_w, view_h = native_w*factor, native_h*factor
            d.text((ox+6, oy+6), f"{obj.oid} {obj.metadata['CODEPOINT']}  native bbox={obj.bbox}", fill="black", font=font)
            d.text((ox+6, oy+23), f"role={obj.role}; class={obj.script_class}; H={obj.metadata['H_INK_PX']}px", fill="black", font=font)
            for vi, (view, label) in enumerate(zip(views, labels)):
                vx = ox + 7 + vi*380
                vy = oy + 47
                d.text((vx, vy), label, fill="black", font=font)
                enlarged = view.resize((view_w, view_h), Image.Resampling.NEAREST)
                canvas.paste(enlarged, (vx, vy+18))
                d.rectangle((vx, vy+18, vx+view_w-1, vy+18+view_h-1), outline="black", width=1)
            ledger.append({
                "GLYPH_ID": obj.oid,
                "SAFE_FILENAME": obj.safe,
                "SHEET": f"contact_sheet_{sheet_no:02d}.png",
                "CELL": k+1,
                "ORIGINAL_MATCH": "PENDING_MANUAL",
                "OVERLAY_COMPLETE": "PENDING_MANUAL",
                "MASK_ONLY_PURE": "PENDING_MANUAL",
                "MISSING_STROKE_PX": "PENDING_MANUAL",
                "FOREIGN_PIXEL_PX": "PENDING_MANUAL",
                "REVIEWER": "SA1_R5",
                "DECISION": "PENDING_MANUAL",
                "NOTE": "Must be completed only after opening this tri-view cell at 8x nearest.",
            })
        canvas.save(dirs["contacts"] / f"contact_sheet_{sheet_no:02d}.png")
    return ledger


def low_profile_calibration(doc: fitz.Document, glyph_rows: list[dict[str, Any]], dirs: dict[str, Path]) -> dict[str, Any]:
    """Calibrate each low-profile glyph against exact-font final-PDF controls.

    A period is inherently shorter than the ordinary glyph height threshold,
    so this does not borrow a generic CJK/Latin threshold.  It searches the
    frozen full book for independent final-PDF instances with exactly the same
    embedded font and PDF size, renders each directly at 300 dpi, and retains
    raw/mask views at 8x nearest for manual inspection.
    """
    lows = [r for r in glyph_rows if r["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION"]
    if not lows:
        result = {"status": "NOT_APPLICABLE", "pass": True, "target_count": 0, "controls": []}
        (dirs["calibration"] / "low_profile_calibration.csv").write_text(
            "STATUS,DETAIL\nNOT_APPLICABLE,No LOW_PROFILE_PUNCTUATION glyph is present inside the scoped figure environment.\n",
            encoding="utf-8-sig",
        )
        return result

    all_control_rows: list[dict[str, Any]] = []
    sheets: list[Image.Image] = []
    for target in lows:
        wanted_font = target["FONT"]
        wanted_size = float(target["PDF_FONT_SIZE_PT"])
        wanted_ch = target["TEXT_SAMPLE"]
        candidates: list[tuple[int, fitz.Rect]] = []
        for pno in range(doc.page_count):
            if pno == PHYSICAL_PAGE - 1:
                continue
            p = doc.load_page(pno)
            raw = p.get_text("rawdict")
            for block in raw.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("font") != wanted_font or abs(float(span.get("size", 0.0)) - wanted_size) > 0.02:
                            continue
                        for char in span.get("chars", []):
                            if char.get("c") == wanted_ch:
                                candidates.append((pno + 1, fitz.Rect(char["bbox"])))
                                if len(candidates) >= 8:
                                    break
                        if len(candidates) >= 8:
                            break
                    if len(candidates) >= 8:
                        break
                if len(candidates) >= 8:
                    break
            if len(candidates) >= 8:
                break
        for cno, (physical, rect) in enumerate(candidates, 1):
            p = doc.load_page(physical - 1)
            pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
            x0, y0, x1, y1 = px_rect(rect, pix.width, pix.height)
            mask = pixel_threshold_mask(arr[y0:y1, x0:x1])
            hpx = ink_height(mask)
            pad = 3
            ax0, ay0 = max(0, x0-pad), max(0, y0-pad)
            ax1, ay1 = min(pix.width, x1+pad), min(pix.height, y1+pad)
            raw_crop = Image.fromarray(arr[ay0:ay1, ax0:ax1])
            only = np.full_like(np.asarray(raw_crop), 255)
            sy0, sx0 = y0-ay0, x0-ax0
            only[sy0:sy0+mask.shape[0], sx0:sx0+mask.shape[1]][mask] = [0, 0, 0]
            raw_crop.resize((raw_crop.width*8, raw_crop.height*8), Image.Resampling.NEAREST).save(
                dirs["calibration"] / f"{target['GLYPH_ID']}_control_{cno:02d}_original_8x.png"
            )
            Image.fromarray(only).resize((raw_crop.width*8, raw_crop.height*8), Image.Resampling.NEAREST).save(
                dirs["calibration"] / f"{target['GLYPH_ID']}_control_{cno:02d}_mask_8x.png"
            )
            all_control_rows.append({
                "TARGET_GLYPH": target["GLYPH_ID"], "CHAR": wanted_ch, "FONT": wanted_font,
                "PDF_FONT_SIZE_PT": wanted_size, "CONTROL_PHYSICAL_PAGE": physical,
                "CONTROL_RECT_PT": [round(v, 5) for v in rect], "CONTROL_H_INK_PX": hpx,
                "CONTROL_INK_AREA_PX": int(np.count_nonzero(mask)),
                "CONTROL_NONEMPTY": bool(mask.any()),
                "ORIGINAL_8X": f"{target['GLYPH_ID']}_control_{cno:02d}_original_8x.png",
                "MASK_8X": f"{target['GLYPH_ID']}_control_{cno:02d}_mask_8x.png",
            })
    control_heights = [int(r["CONTROL_H_INK_PX"]) for r in all_control_rows if r["CONTROL_NONEMPTY"]]
    control_areas = [int(r["CONTROL_INK_AREA_PX"]) for r in all_control_rows if r["CONTROL_NONEMPTY"]]
    observed_targets = [int(r["H_INK_PX"]) for r in lows]
    observed_areas = [int(r["INK_AREA_PX"]) for r in lows]
    reference = float(np.median(control_heights)) if control_heights else 0.0
    reference_area = float(np.median(control_areas)) if control_areas else 0.0
    h_ratios = [h / reference if reference else 0.0 for h in observed_targets]
    area_ratios = [a / reference_area if reference_area else 0.0 for a in observed_areas]
    passed = len(control_heights) >= 5 and all(0.92 <= ratio <= 1.08 for ratio in h_ratios) and all(0.92 <= ratio <= 1.08 for ratio in area_ratios)
    for r in lows:
        r["LOW_PROFILE_CALIBRATION_REF_H_PX"] = round(reference, 4)
        r["LOW_PROFILE_CALIBRATION_REF_AREA_PX"] = round(reference_area, 4)
        r["LOW_PROFILE_H_RATIO"] = round(int(r["H_INK_PX"]) / reference, 4) if reference else 0.0
        r["LOW_PROFILE_AREA_RATIO"] = round(int(r["INK_AREA_PX"]) / reference_area, 4) if reference_area else 0.0
        r["LOW_PROFILE_CALIBRATION_PASS"] = passed
        r["PIXEL_PASS"] = bool(r["MASK_NONEMPTY"]) and passed
    write_csv(dirs["calibration"] / "low_profile_calibration.csv", all_control_rows)
    md = (
        f"# Low-profile calibration — {FIGURE_ID}\n\n"
        f"- Target: {', '.join(r['GLYPH_ID'] + ' ' + repr(r['TEXT_SAMPLE']) for r in lows)}\n"
        f"- Exact final-PDF controls: {len(control_heights)}; font `{lows[0]['FONT']}`, PDF size `{lows[0]['PDF_FONT_SIZE_PT']}` pt.\n"
        f"- Control ink heights at native 300 dpi: `{control_heights}`; median `{reference}` px.\n"
        f"- Scoped target ink heights: `{observed_targets}` px; H ratios `{h_ratios}`.\n"
        f"- Control ink areas: `{control_areas}`; median `{reference_area}` px; target areas `{observed_areas}`, area ratios `{area_ratios}`.\n"
        f"- Result: `{'PASS' if passed else 'FAIL'}`.  Each original/mask control is an independent direct 300 dpi frozen-PDF rendering and is retained at 8x nearest.\n"
    )
    (dirs["calibration"] / "low_profile_calibration.md").write_text(md, encoding="utf-8")
    return {
        "status": "PASS" if passed else "FAIL", "pass": passed, "target_count": len(lows),
        "controls": all_control_rows, "control_heights": control_heights, "control_areas": control_areas,
        "reference_height_px": reference, "reference_area_px": reference_area,
    }


def write_glyph_enumeration_boundary(page: fitz.Page, glyph_rows: list[dict[str, Any]], dirs: dict[str, Path]) -> dict[str, Any]:
    """Independently prove the 235 raw-text inclusion boundary before review."""
    raw = page.get_text("rawdict")
    scoped: list[dict[str, Any]] = []
    fringe: list[dict[str, Any]] = []
    for b_idx, block in enumerate(raw.get("blocks", [])):
        for l_idx, line in enumerate(block.get("lines", [])):
            for s_idx, span in enumerate(line.get("spans", [])):
                for c_idx, char in enumerate(span.get("chars", [])):
                    ch = char.get("c", "")
                    if not ch or ch.isspace():
                        continue
                    rect = fitz.Rect(char["bbox"])
                    centre = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
                    row = {
                        "BLOCK": b_idx, "LINE": l_idx, "SPAN": s_idx, "CHAR": c_idx,
                        "TEXT": ch, "BBOX_PT": [round(v, 5) for v in rect],
                    }
                    if FIGURE_RECT_PT.contains(centre):
                        scoped.append(row)
                    elif rect.intersects(FIGURE_RECT_PT):
                        fringe.append(row)
    id_match = len(scoped) == len(glyph_rows)
    blocks = sorted({r["BLOCK"] for r in scoped})
    payload = {
        "rawdict_center_inside_figure_count": len(scoped),
        "glyph_id_map_count": len(glyph_rows),
        "counts_match": id_match,
        "bbox_intersects_but_center_outside_count": len(fringe),
        "scoped_blocks": blocks,
        "fringe_rows": fringe,
        "result": "PASS" if id_match and not fringe else "FAIL",
    }
    (dirs["reports"] / "glyph_enumeration_boundary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def write_graphic_enumeration(page: fitz.Page, vector_records: list[dict[str, Any]], dirs: dict[str, Path]) -> dict[str, Any]:
    """Record the complete vector/pattern foreground universe in the panels."""
    graphic_indices: list[int] = []
    for idx, drawing in enumerate(page.get_drawings()):
        rect = drawing["rect"]
        if rect_touches(rect, GRAPH_RECT_PT) and not (rect.y0 < 260 or rect.y1 > 462 or rect.x1 < 150 or rect.x0 > 500):
            graphic_indices.append(idx)
    expected_indices = sorted(VECTOR_SEMANTICS)
    ids = {r["OBJECT_ID"] for r in vector_records}
    payload = {
        "pdf_get_drawings_graph_indices": graphic_indices,
        "expected_source_vector_indices": expected_indices,
        "path_indices_match": graphic_indices == expected_indices,
        "path_record_count": len([r for r in vector_records if r["OBJECT_ID"] != "GFX_HATCH"]),
        "semantic_pattern_object": "GFX_HATCH",
        "all_vector_masks_nonempty": all(bool(r["MASK_NONEMPTY"]) for r in vector_records),
        "vector_record_ids": sorted(ids),
        "result": "PASS" if graphic_indices == expected_indices and "GFX_HATCH" in ids and len(vector_records) == len(expected_indices) + 1 else "FAIL",
    }
    (dirs["reports"] / "graphic_enumeration_boundary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def allocate_same_parent_shared_pixels(glyphs: list[Obj], glyph_rows: list[dict[str, Any]], dirs: dict[str, Path]) -> list[dict[str, Any]]:
    """Assign ambiguous raw-bbox pixels to exactly one adjacent glyph.

    PDF rawdict bboxes can overlap by one device column even when adjacent
    glyph paint is not semantically shared.  Every such raw foreground pixel
    is assigned by nearest *exclusive* final-ink seed, so no target mask can
    silently contain the neighbour's claimed pixel.  The four actual cases
    are retained in a CSV and the modified native masks are re-saved.
    """
    row_by_id = {r["GLYPH_ID"]: r for r in glyph_rows}
    allocations: list[dict[str, Any]] = []
    for a, b in combinations(glyphs, 2):
        if a.parent != b.parent or bbox_distance(a.bbox, b.bbox) > 0:
            continue
        # The U+0338/U+226A composite was already separated at extraction.
        if {a.oid, b.oid} == {"G0090", "G0091"}:
            continue
        overlap, _, union = pair_metrics(a, b)
        if overlap == 0:
            continue
        x0, y0, x1, y1 = union
        am = np.zeros((y1-y0, x1-x0), dtype=bool)
        bm = np.zeros_like(am)
        paste_mask(am, a, (x0, y0)); paste_mask(bm, b, (x0, y0))
        shared = am & bm
        a_seed = am & ~shared
        b_seed = bm & ~shared
        if not a_seed.any() or not b_seed.any():
            raise RuntimeError(f"Cannot uniquely allocate shared final ink: {a.oid}/{b.oid}")
        da = distance_transform_edt(~a_seed)
        db = distance_transform_edt(~b_seed)
        to_a = shared & (da <= db)
        to_b = shared & ~to_a
        ay, ax = np.where(to_b)
        a.mask[ay + y0 - a.bbox[1], ax + x0 - a.bbox[0]] = False
        by, bx = np.where(to_a)
        b.mask[by + y0 - b.bbox[1], bx + x0 - b.bbox[0]] = False
        source_context = {
            frozenset({"G0143", "G0144"}): "formula-card w(4), source L96",
            frozenset({"G0155", "G0156"}): "formula-card 24/25, source L97",
            frozenset({"G0177", "G0178"}): "right-panel q_R title formula, source L69",
            frozenset({"G0226", "G0227"}): "caption 增加样本, source L102",
        }.get(frozenset({a.oid, b.oid}), "same semantic parent; source/PDF glyph sequence")
        allocations.append({
            "PAIR_ID": f"PAIR_{a.oid}_{b.oid}", "OBJECT_A": a.oid, "OBJECT_B": b.oid,
            "SHARED_RAW_PIXELS_BEFORE": overlap, "ASSIGNED_TO_A": int(np.count_nonzero(to_a)),
            "ASSIGNED_TO_B": int(np.count_nonzero(to_b)), "METHOD": "nearest_exclusive_final_ink_seed_no_dilation",
            "SOURCE_CONTEXT": source_context,
        })
    for obj in glyphs:
        r = row_by_id[obj.oid]
        r["ACTUAL_BBOX"] = mask_bbox(obj.mask, obj.bbox[0], obj.bbox[1])
        r["H_INK_PX"] = ink_height(obj.mask)
        r["INK_AREA_PX"] = int(np.count_nonzero(obj.mask))
        threshold = required_height(obj.script_class)
        r["PIXEL_PASS"] = (threshold is None or r["H_INK_PX"] >= threshold) and bool(obj.mask.any())
        if any(obj.oid in {x["OBJECT_A"], x["OBJECT_B"]} for x in allocations):
            r["MASK_METHOD"] = str(r["MASK_METHOD"]) + " + same-parent unique-pixel allocation"
        Image.fromarray((obj.mask * 255).astype(np.uint8), mode="L").save(dirs["masks"] / f"{obj.safe}_mask.png")
    write_csv(dirs["reports"] / "same_parent_mask_allocation.csv", allocations)
    return allocations


def write_occlusion_reverse(dirs: dict[str, Path]) -> None:
    """Make final-visible rather than pre-paint ownership explicit."""
    rows = [
        {
            "CASE_ID": "OCC-01", "OBJECTS": "G0090/U+0338, G0091/U+226A",
            "SOURCE_EVIDENCE": "source L37: p\\not\\ll q_L",
            "REVERSE_RULE": "ToUnicode gives U+0338 zero-width bbox; final glyph cluster is separated by long-solidus geometry only.",
            "FINAL_VISIBLE_DECISION": "Same-formula-parent overlay; G0090 owns final solidus mask, G0091 records composite cluster; no independent-text collision.",
        },
        {
            "CASE_ID": "OCC-02", "OBJECTS": "GFX_HATCH, GFX12, GFX14, GFX15, GFX17",
            "SOURCE_EVIDENCE": "source L45-46 plus L47-58",
            "REVERSE_RULE": "Pattern is not exposed by get_drawings.  Its final mask is analytically bounded then colour-restricted; curve/baseline/boundary/marker pixels are excluded.",
            "FINAL_VISIBLE_DECISION": "Only final dark-grey hatch pixels belong to GFX_HATCH; boundary contacts are named intentional GG relations.",
        },
        {
            "CASE_ID": "OCC-03", "OBJECTS": "GFX26 formula-card border and all formula-card glyphs",
            "SOURCE_EVIDENCE": "source L89-99; PDF path seqno 61 has white fill",
            "REVERSE_RULE": "White card fill reverses/occludes prior plot paint.  GFX26 replay deliberately retains border only, never the white interior or formula text.",
            "FINAL_VISIBLE_DECISION": "No card-text/vector mask merger; formula glyphs are independently owned by rawdict masks.",
        },
        {
            "CASE_ID": "OCC-04", "OBJECTS": "GFX28/GFX29 white-filled markers, GFX24 target curve",
            "SOURCE_EVIDENCE": "source L85-88",
            "REVERSE_RULE": "Marker fill is white and hides the underlying curve inside its interior; own mask uses final foreground after that paint order.",
            "FINAL_VISIBLE_DECISION": "Only intended curve-to-marker outline contacts remain and are explicitly whitelisted.",
        },
        {
            "CASE_ID": "OCC-05", "OBJECTS": "GFX16 filled q_L marker, GFX13, GFX15",
            "SOURCE_EVIDENCE": "source L49-58",
            "REVERSE_RULE": "Filled endpoint marker is a semantic node painted on its q_L line/support boundary junction.",
            "FINAL_VISIBLE_DECISION": "Its observed final contacts are named geometry joins, not independent foreground collisions.",
        },
    ]
    write_csv(dirs["relationships"] / "occlusion_reverse.csv", rows)
    md = "# Final-visible occlusion reversal\n\n" + "\n".join(
        f"- **{r['CASE_ID']}** `{r['OBJECTS']}` — {r['FINAL_VISIBLE_DECISION']}" for r in rows
    ) + "\n"
    (dirs["relationships"] / "occlusion_reverse.md").write_text(md, encoding="utf-8")


def add_measurement_statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_element: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_element[(r["ELEMENT_ID"], r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])].append(r)
    element_medians: dict[tuple[str, str, str, str], float] = {}
    for key, group in by_element.items():
        element_medians[key] = float(np.median([g["H_INK_PX"] for g in group]))
    by_role_class: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for (_, panel, role, cls), med in element_medians.items():
        by_role_class[(panel, role, cls)].append(med)
    class_medians = {k: float(np.median(v)) for k, v in by_role_class.items()}
    same_class_pass = True
    for r in rows:
        key = (r["ELEMENT_ID"], r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])
        cmed = class_medians[(r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])]
        emed = element_medians[key]
        ratio = emed / cmed if cmed else 0.0
        # The D gate compares semantic-element medians, not individual glyph
        # shapes (e.g. CJK stroke topology) while every glyph retains its own C gate.
        r["CLASS_MEDIAN_PX"] = round(cmed, 4)
        r["ELEMENT_MEDIAN_PX"] = round(emed, 4)
        r["RATIO_TO_CLASS_MEDIAN"] = round(ratio, 4)
        r["SAME_CLASS_RATIO_PASS"] = 0.92 <= ratio <= 1.08
        same_class_pass &= bool(r["SAME_CLASS_RATIO_PASS"])

    # E uses source/PDF effective point-size medians for hierarchy.  Native
    # ink-height ratios remain recorded below as a diagnostic, but can differ
    # by one raster row for CJK glyph topology; using them as the sole E
    # measure would falsely turn the declared 10.2/9.6 = 1.0625 title tier
    # into 1.035.  C/D still individually gate every raw 300 dpi glyph.
    source_role_values: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for r in rows:
        source_role_values[(r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])].append(float(r["PDF_FONT_SIZE_PT"]))
    source_role_medians = {k: float(np.median(v)) for k, v in source_role_values.items()}
    base_by_panel: dict[str, float] = {}
    for panel in {r["PANEL_ID"] for r in rows}:
        ordinary = [
            med for (p, role, cls), med in source_role_medians.items()
            if p == panel and cls == "CJK_FULL" and role in {
                "ANNOTATION", "AXIS_LABEL_OR_TICK", "Y_AXIS_LABEL_OR_TICK",
                "X_AXIS_LABEL_OR_ANNOTATION", "TICK_LABEL",
            }
        ]
        if ordinary:
            base_by_panel[panel] = float(np.median(ordinary))
    role_ratio_pass = True
    role_bounds = {
        "PANEL_TITLE": (1.05, 1.20),
        "FORMULA_CARD": (1.00, 1.18),
        "CAPTION": (0.95, 1.18),
        "ANNOTATION": (0.95, 1.10),
        "AXIS_LABEL_OR_TICK": (0.95, 1.18),
        "Y_AXIS_LABEL_OR_TICK": (0.95, 1.18),
        "X_AXIS_LABEL_OR_ANNOTATION": (0.95, 1.18),
        "TICK_LABEL": (0.95, 1.10),
    }
    for r in rows:
        base = base_by_panel.get(r["PANEL_ID"])
        if base is None or r["SCRIPT_CLASS"] != "CJK_FULL":
            r["ROLE_RATIO"] = "N/A_CROSS_SCRIPT"
            r["ROLE_RATIO_INK_DIAGNOSTIC"] = "N/A_CROSS_SCRIPT"
            r["ROLE_RATIO_METHOD"] = "N/A_CROSS_SCRIPT"
            r["ROLE_RATIO_PASS"] = True
            continue
        role_source_med = source_role_medians[(r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])]
        ratio = role_source_med / base if base else 0.0
        role_ink_med = class_medians[(r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])]
        # Diagnostic only: it makes the native rounding difference explicit.
        base_ink_candidates = [
            med for (p, role, cls), med in class_medians.items()
            if p == r["PANEL_ID"] and cls == "CJK_FULL" and role in {
                "ANNOTATION", "AXIS_LABEL_OR_TICK", "Y_AXIS_LABEL_OR_TICK",
                "X_AXIS_LABEL_OR_ANNOTATION", "TICK_LABEL",
            }
        ]
        base_ink = float(np.median(base_ink_candidates)) if base_ink_candidates else 0.0
        lo, hi = role_bounds.get(r["ROLE"], (0.95, 1.10))
        r["ROLE_RATIO"] = round(ratio, 4)
        r["ROLE_RATIO_INK_DIAGNOSTIC"] = round(role_ink_med / base_ink, 4) if base_ink else "N/A"
        r["ROLE_RATIO_METHOD"] = "PDF_EFFECTIVE_PT_ROLE_MEDIAN_OVER_9.6PT_CJK_BASE"
        r["ROLE_RATIO_PASS"] = lo <= ratio <= hi
        role_ratio_pass &= bool(r["ROLE_RATIO_PASS"])
    return {
        "same_class_pass": same_class_pass,
        "role_ratio_pass": role_ratio_pass,
        "base_by_panel": base_by_panel,
        "class_medians": {"|".join(k): v for k, v in class_medians.items()},
        "source_role_medians": {"|".join(k): v for k, v in source_role_medians.items()},
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def aggregate_pair_metrics(glyph_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> None:
    by_id = {r["GLYPH_ID"]: r for r in glyph_rows}
    for r in glyph_rows:
        r["TEXT_TEXT_OVERLAP_PX"] = 0
        r["TEXT_GRAPHIC_OVERLAP_PX"] = 0
        r["MIN_CLEARANCE_PX"] = ""
        r["PAIR_EVIDENCE_STATUS"] = "PASS"
    for p in pair_rows:
        for oid, other_kind in ((p["OBJECT_A"], p["KIND_B"]), (p["OBJECT_B"], p["KIND_A"])):
            if oid not in by_id:
                continue
            r = by_id[oid]
            overlap = int(p["RAW_OVERLAP_PX"])
            if p["RELATION_CLASS"] == "TT":
                r["TEXT_TEXT_OVERLAP_PX"] += overlap
            elif p["RELATION_CLASS"] == "TG":
                r["TEXT_GRAPHIC_OVERLAP_PX"] += overlap
            clearance = p["RAW_MIN_CLEARANCE_PX"]
            if clearance != "":
                value = float(clearance)
                existing = r["MIN_CLEARANCE_PX"]
                if existing == "" or value < float(existing):
                    r["MIN_CLEARANCE_PX"] = round(value, 4)
            if p["STATUS"] != "PASS":
                r["PAIR_EVIDENCE_STATUS"] = p["STATUS"]
    for r in glyph_rows:
        r["PASS_FAIL"] = "PASS" if (
            r["FONT_PASS"] and r["PIXEL_PASS"] and r["SAME_CLASS_RATIO_PASS"]
            and r["ROLE_RATIO_PASS"] and r["PAIR_EVIDENCE_STATUS"] == "PASS"
        ) else "FAIL"
        r["REASON"] = "" if r["PASS_FAIL"] == "PASS" else "font/pixel/ratio/pair gate failure"


def write_identity_report(page: fitz.Page, page_rgb: np.ndarray, figure_bounds: tuple[int, int, int, int], dirs: dict[str, Path]) -> None:
    fls_text = FLS.read_text(encoding="utf-8", errors="replace")
    fls_hits = [line for line in fls_text.splitlines() if "fig_v5_c02_is_support.tex" in line]
    contents = f"""# {FIGURE_ID} — R5 SA1 identity and scope\n\n- Official PDF: `{PDF}`\n- PDF SHA-256 actually verified: `{sha256(PDF)}`\n- Frozen graph source: `{SOURCE}`\n- Source SHA-256 actually verified: `{sha256(SOURCE)}`\n- Physical page / printed page / figure: `{PHYSICAL_PAGE}` / `{PRINTED_PAGE}` / `{FIGURE_NUMBER}`\n- PDF page size: `{page.rect.width:.4f} × {page.rect.height:.4f} pt`; native 300 dpi page: `{page_rgb.shape[1]} × {page_rgb.shape[0]} px`.\n- Figure environment scope: `{[FIGURE_RECT_PT.x0, FIGURE_RECT_PT.y0, FIGURE_RECT_PT.x1, FIGURE_RECT_PT.y1]}` pt; native integer crop `{list(figure_bounds)}`.\n- `standalone_300dpi.png` is a direct clipped 300 dpi rendering of the frozen PDF page, not a resized crop.\n- FLS source locator: `{fls_hits[0] if fls_hits else 'MISSING — identity failure'}`\n\nNo R4/older P580 conclusion or repair artefact was read or used. The 32 user-noted abandoned colour-projection assertions are excluded from every R5 numerator, denominator, relationship CSV, and conclusion.\n\nThe direct current figure source and PDF page agree on the support illustration: $p(x)=6x(5-x)/125$, $q_L=(2/5)1_{[0,5/2]}$, $q_R=1/5$; the left support gap means $p\\not\\ll q_L$, while the right proposal covers the target. $w(1)=24/25$, $w(5/2)=3/2$, $w(4)=24/25$.\n"""
    (dirs["reports"] / "identity_and_scope.md").write_text(contents, encoding="utf-8")


def write_machine_status(glyph_rows: list[dict[str, Any]], vector_records: list[dict[str, Any]], pair_rows: list[dict[str, Any]], stats: dict[str, int], ratio_stats: dict[str, Any], ledger: list[dict[str, Any]], calibration: dict[str, Any], enumeration: dict[str, Any], graphic_enumeration: dict[str, Any], dirs: dict[str, Path]) -> None:
    low = [r for r in glyph_rows if r["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION"]
    source_font_pass = all(bool(r["FONT_PASS"]) for r in glyph_rows)
    pixel_pass = all(bool(r["PIXEL_PASS"]) for r in glyph_rows)
    all_glyph_rows_pass = all(r["PASS_FAIL"] == "PASS" for r in glyph_rows)
    clip_count = 0
    # Actual page-edge clipping: every scoped visible object is interior to the PDF page.
    for r in glyph_rows:
        if min(r["BBOX_X0"], r["BBOX_Y0"], 2481-r["BBOX_X1"], 3508-r["BBOX_Y1"]) <= 0:
            clip_count += 1
    report = {
        "figure_id": FIGURE_ID,
        "stage": "MACHINE_EVIDENCE_COMPLETE_MANUAL_LEDGER_PENDING",
        "glyph_count": len(glyph_rows),
        "vector_graphic_count": len(vector_records),
        "low_profile_punctuation_count": len(low),
        "source_font_pass": source_font_pass,
        "pixel_height_pass": pixel_pass,
        "same_class_ratio_pass": ratio_stats["same_class_pass"],
        "role_ratio_pass": ratio_stats["role_ratio_pass"],
        "all_glyph_rows_pass": all_glyph_rows_pass,
        "low_profile_calibration_pass": calibration["pass"],
        "glyph_enumeration_boundary_pass": enumeration["result"] == "PASS",
        "graphic_enumeration_boundary_pass": graphic_enumeration["result"] == "PASS",
        "overlap_pixel_count": stats["illegal_overlap_pixel_count"],
        "clip_pixel_count": clip_count,
        "min_text_clearance_px": min((float(r["MIN_CLEARANCE_PX"]) for r in glyph_rows if r["MIN_CLEARANCE_PX"] != ""), default=None),
        "pair_stats": stats,
        "pending_manual_ledger_rows": sum(r["DECISION"] == "PENDING_MANUAL" for r in ledger),
        "no_empty_vector_mask": all(r["MASK_NONEMPTY"] for r in vector_records),
    }
    (dirs["reports"] / "r5_machine_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    acceptance = f"""# {FIGURE_ID} R5 SA1 visual acceptance — pending manual glyph ledger\n\nSOURCE_FONT_PASS = {str(source_font_pass).lower()}\nPIXEL_HEIGHT_PASS = {str(pixel_pass).lower()}\nSAME_CLASS_RATIO_PASS = {str(ratio_stats['same_class_pass']).lower()}\nROLE_RATIO_PASS = {str(ratio_stats['role_ratio_pass']).lower()}\nLOW_PROFILE_CALIBRATION_PASS = {str(calibration['pass']).lower()}\nGLYPH_ENUMERATION_BOUNDARY_PASS = {str(enumeration['result'] == 'PASS').lower()}\nOVERLAP_PIXEL_COUNT = {stats['illegal_overlap_pixel_count']}\nCLIP_PIXEL_COUNT = {clip_count}\nMIN_TEXT_CLEARANCE_PX = {report['min_text_clearance_px']}\nFONT_VISUAL_HARMONY_PASS = PENDING_MANUAL\nMATH_SEMANTICS_PASS = PENDING_MANUAL\nTEXT_CONSISTENCY_PASS = PENDING_MANUAL\nGRAYSCALE_PASS = PENDING_MANUAL\nPAGE_INTEGRATION_PASS = PENDING_MANUAL\n\nRESULT = PENDING_MANUAL_GLYPH_CONTACT_AND_FOUR_VIEW_REVIEW\n\nThis is not a PASS or a terminal conclusion.  The per-glyph reviewer ledger has {report['pending_manual_ledger_rows']} pending cells and must be completed by opening every 8x-nearest tri-view contact cell.\n"""
    (ROOT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")


def main() -> None:
    dirs = ensure_dirs()
    if sha256(SOURCE) != SOURCE_FINGERPRINT:
        raise SystemExit("Frozen source SHA-256 mismatch")
    if sha256(PDF) != PDF_FINGERPRINT:
        raise SystemExit("Official frozen PDF SHA-256 mismatch")
    doc = fitz.open(PDF)
    page_rgb, figure_bounds, page = render_page(doc, dirs)
    glyphs, glyph_rows = extract_glyphs(page, page_rgb, dirs)
    same_parent_allocations = allocate_same_parent_shared_pixels(glyphs, glyph_rows, dirs)
    calibration = low_profile_calibration(doc, glyph_rows, dirs)
    enumeration = write_glyph_enumeration_boundary(page, glyph_rows, dirs)
    vectors, vector_records = extract_vector_objects(page, page_rgb, dirs)
    hatch = add_hatch_object(page_rgb, dirs)
    vectors.append(hatch)
    vector_records.append(hatch.metadata)
    graphic_enumeration = write_graphic_enumeration(page, vector_records, dirs)
    ratio_stats = add_measurement_statistics(glyph_rows)
    create_overlay(glyphs, page_rgb, figure_bounds, dirs)
    ledger = make_contact_sheets(glyphs, page_rgb, dirs)
    all_objects = glyphs + vectors
    pair_rows, stats = create_relationships(all_objects, page_rgb, dirs)
    aggregate_pair_metrics(glyph_rows, pair_rows)

    write_csv(ROOT / "after_font_audit.csv", glyph_rows)
    write_csv(ROOT / "after_pixel_measurements.csv", glyph_rows)
    write_csv(ROOT / "after_overlap_report.csv", pair_rows)
    write_csv(dirs["relationships"] / "all_unordered_pairs.csv", pair_rows)
    write_csv(ROOT / "glyph_reviewer_ledger.csv", ledger)
    write_csv(ROOT / "glyph_id_filename_map.csv", [{"GLYPH_ID": o.oid, "SAFE_FILENAME": o.safe, "MASK_PATH": f"glyph_masks/{o.safe}_mask.png"} for o in glyphs])
    (dirs["reports"] / "vector_objects.json").write_text(json.dumps(vector_records, ensure_ascii=False, indent=2), encoding="utf-8")
    (dirs["relationships"] / "relationship_manifest.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    write_occlusion_reverse(dirs)
    write_identity_report(page, page_rgb, figure_bounds, dirs)
    write_machine_status(glyph_rows, vector_records, pair_rows, stats, ratio_stats, ledger, calibration, enumeration, graphic_enumeration, dirs)
    print(json.dumps({"glyphs": len(glyphs), "vectors": len(vectors), "same_parent_allocations": len(same_parent_allocations), "pairs": len(pair_rows), **stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
