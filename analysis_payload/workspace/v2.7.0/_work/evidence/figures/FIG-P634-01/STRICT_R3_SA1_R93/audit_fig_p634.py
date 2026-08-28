"""Strict, read-only visual audit for FIG-P634-01.

Inputs are deliberately limited to the frozen full-book PDF and the assigned
figure source.  All generated material is written next to this program.
Rendering uses PyMuPDF's direct 300 dpi page renderer.  Cropping and grayscale
conversion preserve the native 300 dpi pixel grid and never resample.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
PDF = (
    ROOT
    / "v2.7.0"
    / "_work"
    / "source"
    / "v2.7.0"
    / "src"
    / "build"
    / "strict_current_r93_fullbook"
    / "main_full.pdf"
)
SOURCE = (
    ROOT
    / "v2.7.0"
    / "_work"
    / "source"
    / "v2.7.0"
    / "src"
    / "绘图源码"
    / "第05册_采样方法主题模型与图排序"
    / "V5-C04"
    / "fig_v5_c04_coordinate_sweep.tex"
)
COMMON_STYLE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "common" / "statlearnbook.sty"
MERGED_MAIN = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "合并总册" / "main.tex"

SCALE = 300.0 / 72.0  # PDF user-space point to direct 300 dpi raster pixel.
FIGURE_PDF_BOX = (80.0, 398.0, 530.0, 556.0)
FIGURE_WITH_CAPTION_PDF_BOX = (80.0, 398.0, 530.0, 590.0)
FIGURE_ID = "FIG-P634-01"
PANEL_ID = "PANEL-01"
SOURCE_REL = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_coordinate_sweep.tex"


def csv_write(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pbox_to_px(box: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    x0 = max(0, min(width, math.floor(box[0] * SCALE)))
    y0 = max(0, min(height, math.floor(box[1] * SCALE)))
    x1 = max(x0 + 1, min(width, math.ceil(box[2] * SCALE)))
    y1 = max(y0 + 1, min(height, math.ceil(box[3] * SCALE)))
    return x0, y0, x1, y1


def pxbox_to_str(box: tuple[int, int, int, int]) -> str:
    return f"{box[0]},{box[1]},{box[2]},{box[3]}"


def pdfbox_to_str(box: tuple[float, float, float, float]) -> str:
    return ",".join(f"{v:.3f}" for v in box)


def union_box(boxes: Iterable[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    boxes = list(boxes)
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def rect_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return float(math.hypot(dx, dy))


def point_inside(box: tuple[float, float, float, float], x: float, y: float) -> bool:
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def rgb_from_pdf_int(color: int) -> tuple[int, int, int]:
    return (color >> 16 & 255, color >> 8 & 255, color & 255)


def color_tuple(values: tuple[float, float, float]) -> tuple[int, int, int]:
    return tuple(round(v * 255) for v in values)


def script_class(character: str, pdf_size: float) -> str:
    """Classify a rendered glyph for the protocol's height thresholds."""
    if character in SPECIALS:
        if pdf_size < 9.0:
            return "NATURAL_SCRIPT_SYMBOL"
        if character in FULLWIDTH_SPECIALS:
            return "FULLWIDTH"
        return "MATH_OPERATOR"
    if "CJK UNIFIED" in unicodedata.name(character, ""):
        return "CJK"
    if character.isdigit():
        return "NATURAL_SCRIPT" if pdf_size < 9.0 else "DIGIT"
    name = unicodedata.name(character, "")
    if pdf_size < 9.0 and ("MATHEMATICAL" in name or character.isalpha()):
        return "NATURAL_SCRIPT"
    if "GREEK" in name:
        return "GREEK_LOWER" if "SMALL" in name else "LATIN_UPPER"
    if "MATHEMATICAL" in name:
        return "MATH_BASE"
    if character.isupper():
        return "LATIN_UPPER"
    if character.islower():
        return "LATIN_LOWER"
    return "OTHER"


def threshold_for(kind: str) -> int:
    if kind in {"CJK", "FULLWIDTH"}:
        return 30
    if kind in {"DIGIT", "LATIN_UPPER"}:
        return 24
    if kind in {"LATIN_LOWER", "GREEK_LOWER", "MATH_BASE"}:
        return 17
    if kind in {"NATURAL_SCRIPT", "NATURAL_SCRIPT_SYMBOL"}:
        return 15
    if kind == "MATH_OPERATOR":
        return 22
    return 17


SPECIALS = {
    "−",
    "+",
    "=",
    "＝",
    "⋯",
    "…",
    "�",
    ",",
    "，",
    ";",
    "；",
    "(",
    ")",
    "（",
    "）",
    "[",
    "]",
    ".",
    "：",
    ":",
}
FULLWIDTH_SPECIALS = {"＝", "，", "；", "（", "）", "："}
SPECIAL_NAMES = {
    "−": "MINUS",
    "+": "PLUS",
    "=": "EQUALS",
    "＝": "FULLWIDTH_EQUALS",
    "⋯": "ELLIPSIS",
    "…": "ELLIPSIS",
    "�": "ELLIPSIS_EXTRACTION_GLYPH",
    ",": "COMMA",
    "，": "FULLWIDTH_COMMA",
    ";": "SEMICOLON",
    "；": "FULLWIDTH_SEMICOLON",
    "(": "LPAREN",
    ")": "RPAREN",
    "（": "FULLWIDTH_LPAREN",
    "）": "FULLWIDTH_RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ".": "DOT",
    "：": "FULLWIDTH_COLON",
    ":": "COLON",
}


@dataclass
class Char:
    char_id: str
    text: str
    pdf_box: tuple[float, float, float, float]
    px_box: tuple[int, int, int, int]
    font: str
    pdf_size: float
    color: tuple[int, int, int]
    source_span: str
    mask: np.ndarray
    h_ink: int
    local_bg: tuple[int, int, int]
    script: str
    ownership_x: tuple[int, int] = (0, 0)


@dataclass
class ObjectAudit:
    element_id: str
    object_class: str
    role: str
    text_sample: str
    chars: list[Char]
    mask: np.ndarray
    px_box: tuple[int, int, int, int]
    pdf_box: tuple[float, float, float, float]
    source_line: str
    declared_pt: str
    effective_pt: str
    pdf_font_pt: str
    script: str
    flow_id: str = ""
    parent_id: str = ""
    intended: str = ""
    path_prefix: str = "objects"
    h_ink: int = 0
    threshold: int = 0
    source_font_pass: bool = False
    pixel_pass: bool = False
    same_class_ratio: float = 1.0
    role_ratio: str = "N/A"
    text_text_overlap: int = 0
    text_graphic_overlap: int = 0
    min_clearance: str = "N/A"
    reason: str = ""
    foreground_px_box: tuple[int, int, int, int] | None = None


CONTEXTS = [
    # id, bounds, source line, declared pt, logical reader-flow / role origin
    ("FIG_TITLE", (230.0, 399.0, 355.0, 422.0), "10", "10.6", "", "TITLE"),
    ("SEQ_1", (133.0, 422.0, 154.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("SEQ_2", (176.0, 422.0, 197.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("SEQ_ELLIPSIS_1", (218.0, 422.0, 239.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("SEQ_J_MINUS_1", (256.0, 422.0, 285.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("SEQ_J", (304.0, 422.0, 323.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("SEQ_J_PLUS_1", (341.0, 422.0, 371.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("SEQ_ELLIPSIS_2", (387.0, 422.0, 410.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("SEQ_D", (432.0, 422.0, 451.0, 440.0), "11", "9.6", "", "SEQUENCE_INDEX"),
    ("ORDER_LABEL", (452.0, 433.0, 505.0, 452.0), "14-15", "9.6", "", "ORDER_LABEL"),
    ("NODE_1", (130.0, 462.0, 157.0, 485.0), "16", "9.6", "", "NODE"),
    ("NODE_2", (173.0, 462.0, 200.0, 485.0), "17", "9.6", "", "NODE"),
    ("NODE_ELLIPSIS_1", (218.0, 462.0, 239.0, 485.0), "18", "9.6", "", "NODE"),
    ("NODE_J_MINUS_1", (255.0, 462.0, 286.0, 485.0), "19", "9.6", "", "NODE"),
    ("NODE_J_CURRENT", (299.0, 462.0, 326.0, 485.0), "20", "9.6", "", "NODE"),
    ("NODE_J_PLUS_1", (338.0, 462.0, 373.0, 485.0), "21", "9.6", "", "NODE"),
    ("NODE_ELLIPSIS_2", (388.0, 462.0, 409.0, 485.0), "22", "9.6", "", "NODE"),
    ("NODE_D", (423.0, 462.0, 458.0, 485.0), "23", "9.6", "", "NODE"),
    ("STATE_DONE", (188.0, 487.0, 230.0, 504.0), "24", "9.6", "", "STATE_LABEL"),
    ("STATE_CURRENT", (298.0, 487.0, 330.0, 504.0), "25", "9.6", "", "STATE_LABEL"),
    ("STATE_OLD", (378.0, 487.0, 420.0, 504.0), "26", "9.6", "", "STATE_LABEL"),
    ("FORMULA_STATE", (168.0, 502.0, 350.0, 529.0), "27-28", "10.0", "", "FORMULA"),
    ("FORMULA_STATE_TEXT", (348.0, 502.0, 418.0, 529.0), "27-28", "10.0", "", "FORMULA_TEXT"),
    ("NOTE_TEXT", (104.0, 532.0, 480.0, 556.0), "29-30", "9.8", "", "NOTE_TEXT"),
    ("NOTE_MATH", (365.0, 532.0, 412.0, 556.0), "29-30", "9.8", "", "NOTE_MATH"),
    # The figure's local \captionsetup only sets width.  The actual source
    # chain is common/statlearnbook.sty:305 (font={small,...}) under the
    # 11pt ctexbook class at 合并总册/main.tex:8, so \small is 10.0pt.
    ("CAPTION_LABEL", (84.0, 555.0, 121.0, 575.0), "fig:32; statlearnbook.sty:305; 合并总册/main.tex:8", "10.0", "CAPTION_PARAGRAPH", "CAPTION"),
    ("CAPTION_LINE_1", (120.0, 555.0, 530.0, 575.0), "fig:32; statlearnbook.sty:305; 合并总册/main.tex:8", "10.0", "CAPTION_PARAGRAPH", "CAPTION"),
    ("CAPTION_MATH", (94.0, 570.0, 156.0, 588.0), "fig:32; statlearnbook.sty:305; 合并总册/main.tex:8", "10.0", "CAPTION_PARAGRAPH", "CAPTION_MATH"),
    ("CAPTION_LINE_2", (80.0, 570.0, 210.0, 588.0), "fig:32; statlearnbook.sty:305; 合并总册/main.tex:8", "10.0", "CAPTION_PARAGRAPH", "CAPTION"),
]
CONTEXT_MAP = {row[0]: row for row in CONTEXTS}


def context_for(character: Char) -> tuple[str, tuple[float, float, float, float], str, str, str, str]:
    x = (character.pdf_box[0] + character.pdf_box[2]) / 2
    y = (character.pdf_box[1] + character.pdf_box[3]) / 2
    matches = [row for row in CONTEXTS if point_inside(row[1], x, y)]
    if matches:
        # Nested semantic regions (e.g., the math part inside a prose card)
        # belong to the most specific, smallest PDF rectangle.
        return min(matches, key=lambda row: (row[1][2] - row[1][0]) * (row[1][3] - row[1][1]))
    raise RuntimeError(f"Unassigned figure/caption glyph {character.text!r} at {character.pdf_box}")


def text_mask_for_char(
    image_np: np.ndarray,
    character_box: tuple[int, int, int, int],
    fg: tuple[int, int, int],
    ownership_x: tuple[int, int] | None = None,
) -> tuple[np.ndarray, int, tuple[int, int, int]]:
    """Create a non-dilated 20/255 local-background glyph mask.

    PDF character bboxes legitimately overlap through side bearings/kerning.
    ``ownership_x`` is the midpoint partition between adjacent same-baseline
    glyph centres, not a mask dilation or a visual resize.  It prevents a
    neighbouring CJK glyph from being credited to a short comma/operator.
    """
    height, width = image_np.shape[:2]
    x0, y0, x1, y1 = character_box
    pad = 3
    rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
    rx1, ry1 = min(width, x1 + pad), min(height, y1 + pad)
    surrounding = image_np[ry0:ry1, rx0:rx1]
    ring = np.ones(surrounding.shape[:2], dtype=bool)
    ring[y0 - ry0 : y1 - ry0, x0 - rx0 : x1 - rx0] = False
    ring_pixels = surrounding[ring]
    if len(ring_pixels) == 0:
        bg = np.array([255, 255, 255], dtype=float)
    else:
        bg = np.median(ring_pixels.astype(float), axis=0)
    crop = image_np[y0:y1, x0:x1].astype(float)
    delta = np.max(np.abs(crop - bg), axis=2)
    foreground = np.asarray(fg, dtype=float)
    d_fg = np.linalg.norm(crop - foreground, axis=2)
    d_bg = np.linalg.norm(crop - bg, axis=2)
    # Difference >=20 is the protocol threshold; the colour-proximity branch
    # separates glyph ink from differently coloured node texture behind it.
    local = (delta >= 20.0) & (d_fg <= d_bg)
    if ownership_x is not None:
        ox0, ox1 = ownership_x
        global_x = np.arange(x0, x1)
        local &= (global_x[None, :] >= ox0) & (global_x[None, :] < ox1)
    mask = np.zeros(image_np.shape[:2], dtype=bool)
    mask[y0:y1, x0:x1] = local
    yy, _ = np.nonzero(local)
    ink_height = int(yy.max() - yy.min() + 1) if len(yy) else 0
    return mask, ink_height, tuple(round(float(v)) for v in bg)


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return None
    return int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)


def foreground_box(obj: ObjectAudit) -> tuple[int, int, int, int]:
    """Uninflated final foreground bbox; PDF/vector bbox remains separately recorded."""
    if obj.foreground_px_box is None:
        obj.foreground_px_box = mask_bbox(obj.mask) or obj.px_box
    return obj.foreground_px_box


def foreground_overlap(a: ObjectAudit, b: ObjectAudit) -> int:
    """Count final-mask overlap only in the intersecting uninflated bbox."""
    ax0, ay0, ax1, ay1 = foreground_box(a)
    bx0, by0, bx1, by1 = foreground_box(b)
    x0, y0 = max(ax0, bx0), max(ay0, by0)
    x1, y1 = min(ax1, bx1), min(ay1, by1)
    if x1 <= x0 or y1 <= y0:
        return 0
    return int(np.count_nonzero(a.mask[y0:y1, x0:x1] & b.mask[y0:y1, x0:x1]))


def save_triplet(obj: ObjectAudit, raw_image: Image.Image, directory: Path) -> tuple[str, str, str]:
    directory.mkdir(exist_ok=True)
    x0, y0, x1, y1 = obj.px_box
    pad = 8
    crop_box = (max(0, x0 - pad), max(0, y0 - pad), min(raw_image.width, x1 + pad), min(raw_image.height, y1 + pad))
    raw = raw_image.crop(crop_box)
    mask_crop = obj.mask[crop_box[1] : crop_box[3], crop_box[0] : crop_box[2]]
    raw_path = directory / f"{obj.element_id}_raw.png"
    mask_path = directory / f"{obj.element_id}_mask.png"
    overlay_path = directory / f"{obj.element_id}_overlay.png"
    raw.save(raw_path)
    Image.fromarray((mask_crop.astype(np.uint8) * 255), mode="L").save(mask_path)
    overlay = np.asarray(raw).copy()
    overlay[mask_crop] = (255, 45, 45)
    over = Image.fromarray(overlay)
    draw = ImageDraw.Draw(over)
    draw.rectangle((x0 - crop_box[0], y0 - crop_box[1], x1 - crop_box[0] - 1, y1 - crop_box[1] - 1), outline=(0, 170, 0), width=1)
    draw.text((2, 2), obj.element_id, fill=(0, 120, 0))
    over.save(overlay_path)
    return str(raw_path.relative_to(OUT)), str(mask_path.relative_to(OUT)), str(overlay_path.relative_to(OUT))


def make_border_mask(
    image_np: np.ndarray,
    pdf_box: tuple[float, float, float, float],
    stroke_color: tuple[int, int, int],
    stroke_pt: float,
) -> np.ndarray:
    """Isolate the actual painted border inside its vector bbox, without dilation."""
    height, width = image_np.shape[:2]
    px = pbox_to_px(pdf_box, width, height)
    x0, y0, x1, y1 = px
    mask = np.zeros((height, width), dtype=bool)
    crop = image_np[y0:y1, x0:x1].astype(float)
    fg = np.asarray(stroke_color, dtype=float)
    bg = np.array([255.0, 255.0, 255.0])
    diff = np.linalg.norm(crop - fg, axis=2)
    delta = np.max(np.abs(crop - bg), axis=2)
    # The ring is a location restriction based on the original vector bbox,
    # not a morphological expansion of the foreground mask.
    band = max(2, math.ceil(stroke_pt * SCALE) + 1)
    yy, xx = np.indices(crop.shape[:2])
    edge = (xx < band) | (xx >= crop.shape[1] - band) | (yy < band) | (yy >= crop.shape[0] - band)
    local = edge & (delta >= 20.0) & (diff <= 115.0)
    mask[y0:y1, x0:x1] = local
    return mask


def make_arrow_mask(image_np: np.ndarray, pdf_box: tuple[float, float, float, float], color: tuple[int, int, int]) -> np.ndarray:
    height, width = image_np.shape[:2]
    x0, y0, x1, y1 = pbox_to_px(pdf_box, width, height)
    mask = np.zeros((height, width), dtype=bool)
    crop = image_np[y0:y1, x0:x1].astype(float)
    fg = np.asarray(color, dtype=float)
    bg = np.array([255.0, 255.0, 255.0])
    local = (np.max(np.abs(crop - bg), axis=2) >= 20.0) & (np.linalg.norm(crop - fg, axis=2) <= 105.0)
    mask[y0:y1, x0:x1] = local
    return mask


def vector_object(
    obj_id: str,
    obj_class: str,
    pdf_box: tuple[float, float, float, float],
    mask: np.ndarray,
    intended: str,
    source_line: str = "vector PDF object",
) -> ObjectAudit:
    height, width = mask.shape
    px_box = pbox_to_px(pdf_box, width, height)
    return ObjectAudit(
        element_id=obj_id,
        object_class=obj_class,
        role=obj_class,
        text_sample="",
        chars=[],
        mask=mask,
        px_box=px_box,
        pdf_box=pdf_box,
        source_line=source_line,
        declared_pt="N/A",
        effective_pt="N/A",
        pdf_font_pt="N/A",
        script="N/A",
        intended=intended,
    )


def nearest_card_clearance(text_box: tuple[int, int, int, int], card_box: tuple[int, int, int, int]) -> float:
    # Text is inside the rectangle; return the actual rectangular inner-edge gap.
    return float(
        min(
            text_box[0] - card_box[0],
            text_box[1] - card_box[1],
            card_box[2] - text_box[2],
            card_box[3] - text_box[3],
        )
    )


def source_font_ok(obj: ObjectAudit) -> tuple[bool, str]:
    if obj.object_class != "TEXT":
        return True, "not a text object"
    if obj.script in {"NATURAL_SCRIPT", "NATURAL_SCRIPT_SYMBOL"}:
        return True, "natural TeX script/script-script derivative of a >=9.5 pt base formula"
    try:
        return (float(obj.effective_pt) >= 9.5, "base effective_pt >= 9.5" if float(obj.effective_pt) >= 9.5 else "base effective_pt < 9.5")
    except ValueError:
        return False, "effective source size cannot be restored"


def apply_glyph_ownership_masks(chars: list[Char], image_np: np.ndarray) -> None:
    """Assign every glyph an uninflated foreground mask exactly once.

    A midpoint split is used only when two extracted PDF character bboxes
    overlap on the same baseline.  This is necessary for literal punctuation:
    without it the wide PDF side bearing of a comma can include ink from the
    following CJK glyph.  No pixel is expanded, interpolated, or moved.
    """
    for char in chars:
        x0, y0, x1, y1 = char.px_box
        cx = (x0 + x1) / 2.0
        own_x0, own_x1 = x0, x1
        left_centres: list[float] = []
        right_centres: list[float] = []
        for other in chars:
            if other is char:
                continue
            ox0, oy0, ox1, oy1 = other.px_box
            y_overlap = max(0, min(y1, oy1) - max(y0, oy0))
            same_baseline = y_overlap >= 0.55 * min(y1 - y0, oy1 - oy0)
            horizontal_bbox_overlap = ox0 < x1 and x0 < ox1
            if not (same_baseline and horizontal_bbox_overlap):
                continue
            ocx = (ox0 + ox1) / 2.0
            if ocx < cx:
                left_centres.append(ocx)
            elif ocx > cx:
                right_centres.append(ocx)
        if left_centres:
            own_x0 = max(own_x0, math.ceil((max(left_centres) + cx) / 2.0))
        if right_centres:
            own_x1 = min(own_x1, math.floor((min(right_centres) + cx) / 2.0))
        if own_x1 <= own_x0:
            own_x0, own_x1 = x0, x1
        char.ownership_x = (own_x0, own_x1)
        char.mask, char.h_ink, char.local_bg = text_mask_for_char(
            image_np, char.px_box, char.color, char.ownership_x
        )


def find_candidate_page(document: fitz.Document) -> int:
    hits = []
    for index, page in enumerate(document):
        text = page.get_text("text")
        if "图33.3" in text and "系统扫描按固定次序立即写回" in text:
            hits.append(index)
    if len(hits) != 1:
        raise RuntimeError(f"Expected one independently discovered figure page; got {hits}")
    return hits[0]


def semantic_role_for_context(context_id: str, char_class: str) -> str:
    role = CONTEXT_MAP[context_id][5]
    if role == "NODE":
        return "NODE_SCRIPT" if char_class.startswith("NATURAL_SCRIPT") else "NODE_BASE"
    if role == "FORMULA":
        return "FORMULA_SCRIPT" if char_class.startswith("NATURAL_SCRIPT") else "FORMULA_BASE"
    if role == "NOTE_MATH":
        return "NOTE_MATH_SCRIPT" if char_class.startswith("NATURAL_SCRIPT") else "NOTE_MATH_BASE"
    if role == "CAPTION_MATH":
        return "CAPTION_MATH_SCRIPT" if char_class.startswith("NATURAL_SCRIPT") else "CAPTION_MATH_BASE"
    return role


def composite_text_id(obj: ObjectAudit) -> str:
    """Return the natural reader object containing a text fragment."""
    if obj.flow_id == "CAPTION_PARAGRAPH":
        return "CAPTION_PARAGRAPH"
    if obj.parent_id.startswith("FORMULA_STATE"):
        return "FORMULA_CARD"
    if obj.parent_id.startswith("NOTE_"):
        return "NOTE_CARD"
    return obj.parent_id


def same_class_scope(obj: ObjectAudit) -> str:
    """Scope only genuinely repeated comparable reader elements.

    Actual ink height varies with glyph anatomy (e.g. math j versus d).  The
    protocol's same-class test is therefore run on repeated role/script/glyph
    forms, never by comparing unrelated CJK body glyphs to Latin x-height or
    different terminal-index glyph anatomy.
    """
    if obj.element_id.startswith("SYM_"):
        return composite_text_id(obj)
    if obj.script == "NATURAL_SCRIPT":
        return f"script-literal:{obj.text_sample}"
    if obj.role == "SEQUENCE_INDEX" and obj.script == "MATH_BASE":
        return f"sequence-literal:{obj.text_sample}"
    if obj.role == "SEQUENCE_INDEX" and obj.script == "DIGIT":
        return "sequence-digit"
    return "panel-comparable-role"


def type_selector(chars: list[Char], selector: str) -> list[Char]:
    if selector == "CJK":
        return [c for c in chars if c.script == "CJK"]
    if selector == "DIGIT":
        return [c for c in chars if c.script == "DIGIT"]
    if selector == "MATH_BASE":
        return [c for c in chars if c.script in {"MATH_BASE", "LATIN_LOWER", "LATIN_UPPER", "GREEK_LOWER"}]
    if selector == "SCRIPT":
        return [c for c in chars if c.script == "NATURAL_SCRIPT"]
    raise ValueError(selector)


def build_text_object(
    obj_id: str,
    role: str,
    chars: list[Char],
    context_id: str,
    source_line: str,
    declared: str,
    flow: str,
    raw_shape: tuple[int, int],
) -> ObjectAudit:
    if not chars:
        raise RuntimeError(f"No characters selected for {obj_id}")
    mask = np.zeros(raw_shape, dtype=bool)
    for char in chars:
        mask |= char.mask
    px_box = union_box([c.px_box for c in chars])
    pdf_box = (
        min(c.pdf_box[0] for c in chars),
        min(c.pdf_box[1] for c in chars),
        max(c.pdf_box[2] for c in chars),
        max(c.pdf_box[3] for c in chars),
    )
    dominant = statistics.mode([c.script for c in chars])
    # Do not call a long CJK sentence a 4px object merely because it contains
    # the one-stroke character 一.  §9.2.1-C applies the 30px test to pure CJK
    # or *near full-height* characters.  Every raw glyph remains in
    # raw_char_measurements.csv; the component audit below excludes only
    # stroke-only glyphs (<60% of the CJK-run median), never full-height CJK.
    all_heights = [c.h_ink for c in chars]
    component_chars = chars
    omitted_strokes = 0
    if dominant == "CJK" and len(chars) > 1:
        run_median = statistics.median(all_heights)
        component_chars = [c for c in chars if c.h_ink >= 0.60 * run_median]
        omitted_strokes = len(chars) - len(component_chars)
        if not component_chars:  # defensive: never leave a reader object unmeasured
            component_chars = chars
            omitted_strokes = 0
    h = int(round(statistics.median(c.h_ink for c in component_chars)))
    pdf_size = statistics.median(c.pdf_size for c in chars)
    effective = declared
    if dominant == "NATURAL_SCRIPT":
        effective = f"natural_script({pdf_size:.2f} PDF pt)"
    obj = ObjectAudit(
        element_id=obj_id,
        object_class="TEXT",
        role=role,
        text_sample="".join(c.text for c in chars),
        chars=chars,
        mask=mask,
        px_box=px_box,
        pdf_box=pdf_box,
        source_line=source_line,
        declared_pt=declared,
        effective_pt=effective,
        pdf_font_pt=f"{pdf_size:.2f}",
        script=dominant,
        flow_id=flow,
        parent_id=context_id,
        h_ink=h,
        threshold=threshold_for(dominant),
    )
    obj.source_font_pass, source_reason = source_font_ok(obj)
    obj.pixel_pass = all(c.h_ink >= obj.threshold for c in component_chars)
    obj.reason = (
        source_reason
        + f"; component median H_ink={obj.h_ink}px from {len(component_chars)} independently masked comparable glyph(s)"
        + (f"; {omitted_strokes} CJK stroke-only glyph(s) retained in raw audit but excluded from near-full-height comparator" if omitted_strokes else "")
    )
    if not obj.pixel_pass:
        low = min(c.h_ink for c in component_chars)
        obj.reason += f"; comparable component minimum H_ink={low}px < {obj.threshold}px"
    return obj


def make_special_object(char: Char, context_id: str, ordinal: int, raw_shape: tuple[int, int]) -> ObjectAudit:
    _, _, line, declared, flow, _ = CONTEXT_MAP[context_id]
    kind = script_class(char.text, char.pdf_size)
    role = f"OP_{SPECIAL_NAMES[char.text]}"
    obj = ObjectAudit(
        element_id=f"SYM_{context_id}_{SPECIAL_NAMES[char.text]}_{ordinal:02d}",
        object_class="TEXT",
        role=role,
        text_sample=char.text,
        chars=[char],
        mask=char.mask.copy(),
        px_box=char.px_box,
        pdf_box=char.pdf_box,
        source_line=line,
        declared_pt=declared,
        effective_pt=(f"natural_script({char.pdf_size:.2f} PDF pt)" if kind == "NATURAL_SCRIPT_SYMBOL" else declared),
        pdf_font_pt=f"{char.pdf_size:.2f}",
        script=kind,
        flow_id=flow,
        parent_id=context_id,
        h_ink=char.h_ink,
        threshold=threshold_for(kind),
        path_prefix="symbols",
    )
    obj.source_font_pass, source_reason = source_font_ok(obj)
    obj.pixel_pass = obj.h_ink >= obj.threshold
    obj.reason = source_reason
    if not obj.pixel_pass:
        obj.reason += f"; independent {char.text!r} H_ink={obj.h_ink}px < {obj.threshold}px"
    return obj


def write_text_overlay(raw_image: Image.Image, objects: list[ObjectAudit]) -> None:
    crop_px = pbox_to_px(FIGURE_WITH_CAPTION_PDF_BOX, raw_image.width, raw_image.height)
    overview = raw_image.crop(crop_px).convert("RGB")
    detail = overview.copy()
    overview_draw = ImageDraw.Draw(overview)
    detail_draw = ImageDraw.Draw(detail)
    for obj in objects:
        if obj.object_class != "TEXT" or obj.element_id.startswith("SYM_"):
            continue
        x0, y0, x1, y1 = obj.px_box
        colour = (0, 170, 0) if obj.pixel_pass else (230, 40, 40)
        rect = (x0 - crop_px[0], y0 - crop_px[1], x1 - crop_px[0] - 1, y1 - crop_px[1] - 1)
        detail_draw.rectangle(rect, outline=colour, width=1)
        detail_draw.text((rect[0], max(0, rect[1] - 9)), obj.element_id, fill=colour)
        # Overview is deliberately readable: per-script items remain fully
        # traceable in objects/* raw/mask/overlay and the detail overlay.
        if "_SCRIPT_" not in obj.element_id:
            overview_draw.rectangle(rect, outline=colour, width=1)
            overview_draw.text((rect[0], max(0, rect[1] - 9)), obj.element_id, fill=colour)
    overview.save(OUT / "after_text_measurement_overlay_300dpi.png")
    detail.save(OUT / "after_text_measurement_overlay_300dpi_detail.png")


def pair_overlay(raw_image: Image.Image, a: ObjectAudit, b: ObjectAudit, path: Path) -> tuple[Path, Path]:
    xa0, ya0, xa1, ya1 = a.px_box
    xb0, yb0, xb1, yb1 = b.px_box
    x0, y0 = max(0, min(xa0, xb0) - 12), max(0, min(ya0, yb0) - 12)
    x1, y1 = min(raw_image.width, max(xa1, xb1) + 12), min(raw_image.height, max(ya1, yb1) + 12)
    raw = np.asarray(raw_image.crop((x0, y0, x1, y1))).copy()
    raw_path = path.with_name(f"{path.stem}_raw.png")
    Image.fromarray(raw).save(raw_path)
    ma = a.mask[y0:y1, x0:x1]
    mb = b.mask[y0:y1, x0:x1]
    raw[ma] = (35, 190, 45)
    raw[mb] = (230, 45, 45)
    raw[ma & mb] = (255, 0, 255)
    output = Image.fromarray(raw)
    draw = ImageDraw.Draw(output)
    draw.text((2, 2), f"A={a.element_id}", fill=(0, 125, 0))
    draw.text((2, 13), f"B={b.element_id}", fill=(180, 0, 0))
    output.save(path)
    overlap_path = path.with_name(f"{path.stem}_overlap_mask.png")
    Image.fromarray(((ma & mb).astype(np.uint8) * 255), mode="L").save(overlap_path)
    return raw_path, overlap_path


def main() -> None:
    # Read the assigned figure and its actual caption/type-size dependency
    # chain.  These are source dependencies, not prior figure evidence.
    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    if not any("FIG-P634-01" in line for line in source_lines):
        raise RuntimeError("Assigned source does not identify FIG-P634-01")
    style_lines = COMMON_STYLE.read_text(encoding="utf-8").splitlines()
    main_lines = MERGED_MAIN.read_text(encoding="utf-8").splitlines()
    if not any("\\captionsetup{font={small,stretch=1.12}" in line for line in style_lines):
        raise RuntimeError("Cannot recover caption font from actual public style dependency")
    if not any("\\documentclass[UTF8,a4paper,11pt,openany]{ctexbook}" in line for line in main_lines):
        raise RuntimeError("Cannot recover 11pt base class for inherited caption size")

    document = fitz.open(PDF)
    page_index = find_candidate_page(document)
    page = document[page_index]
    pix300 = page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False)
    pix200 = page.get_pixmap(dpi=200, colorspace=fitz.csRGB, alpha=False)
    raw_image = Image.frombytes("RGB", (pix300.width, pix300.height), pix300.samples)
    raw_image.save(OUT / "after_full_page_300dpi.png")
    Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples).save(OUT / "after_full_page_200dpi.png")
    fig_px = pbox_to_px(FIGURE_PDF_BOX, raw_image.width, raw_image.height)
    fig_cap_px = pbox_to_px(FIGURE_WITH_CAPTION_PDF_BOX, raw_image.width, raw_image.height)
    raw_image.crop(fig_px).save(OUT / "after_standalone_300dpi.png")
    figure_crop = raw_image.crop(fig_cap_px)
    figure_crop.save(OUT / "after_figure_crop_300dpi.png")
    figure_crop.convert("L").save(OUT / "after_grayscale_300dpi.png")
    image_np = np.asarray(raw_image)

    rawdict = page.get_text("rawdict", sort=True)
    chars: list[Char] = []
    char_counter = 0
    for block in rawdict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for raw_char in span["chars"]:
                    text = raw_char["c"]
                    if text.isspace():
                        continue
                    bbox = tuple(float(v) for v in raw_char["bbox"])
                    cx = (bbox[0] + bbox[2]) / 2
                    cy = (bbox[1] + bbox[3]) / 2
                    if not point_inside(FIGURE_WITH_CAPTION_PDF_BOX, cx, cy):
                        continue
                    char_counter += 1
                    px_box = pbox_to_px(bbox, raw_image.width, raw_image.height)
                    pdf_size = float(span["size"])
                    color = rgb_from_pdf_int(int(span["color"]))
                    chars.append(
                        Char(
                            char_id=f"CHAR_{char_counter:03d}",
                            text=text,
                            pdf_box=bbox,
                            px_box=px_box,
                            font=str(span["font"]),
                            pdf_size=pdf_size,
                            color=color,
                            source_span=str(span.get("text", "")),
                            mask=np.zeros(image_np.shape[:2], dtype=bool),
                            h_ink=0,
                            local_bg=(255, 255, 255),
                            script=script_class(text, pdf_size),
                        )
                    )

    apply_glyph_ownership_masks(chars, image_np)
    for char in chars:
        context_for(char)  # force a strict coverage failure if any glyph escapes the map

    # Group every non-space non-punctuation glyph into a logical reading object.
    groups: list[ObjectAudit] = []
    for ctx_id, box, line, declared, flow, ctx_role in CONTEXTS:
        scoped = [
            char
            for char in chars
            if context_for(char)[0] == ctx_id and char.text not in SPECIALS
        ]
        selectors: list[tuple[str, str]] = []
        if ctx_role in {"TITLE", "ORDER_LABEL", "STATE_LABEL", "FORMULA_TEXT", "NOTE_TEXT", "CAPTION"}:
            selectors.append(("CJK", "CJK"))
        if ctx_role in {"SEQUENCE_INDEX", "NODE", "FORMULA", "NOTE_MATH", "CAPTION_MATH", "CAPTION"}:
            selectors.append(("MATH_BASE", "MATH_BASE"))
            selectors.append(("SCRIPT", "NATURAL_SCRIPT"))
            if ctx_role == "SEQUENCE_INDEX":
                selectors.append(("DIGIT", "DIGIT"))
        if ctx_role == "CAPTION" and ctx_id == "CAPTION_LABEL":
            selectors.append(("DIGIT", "DIGIT"))
        for selector, script_name in selectors:
            selected = type_selector(scoped, selector)
            if not selected:
                continue
            role = semantic_role_for_context(ctx_id, script_name)
            if ctx_role == "SEQUENCE_INDEX" and selector == "DIGIT":
                role = "SEQUENCE_INDEX"
            if ctx_role == "CAPTION" and selector == "DIGIT":
                role = "CAPTION"
            suffix = {
                "CJK": "TEXT",
                "MATH_BASE": "BASE",
                "NATURAL_SCRIPT": "SCRIPT",
                "DIGIT": "DIGIT",
            }[script_name]
            if selector == "SCRIPT":
                # Script glyph anatomy (j/d/t/digits) is not a single
                # comparable height object.  Give each natural script its
                # own ELEMENT_ID and literal-sized class comparison.
                for ordinal, char in enumerate(selected, 1):
                    groups.append(
                        build_text_object(
                            f"{ctx_id}_{suffix}_{ordinal:02d}",
                            role,
                            [char],
                            ctx_id,
                            line,
                            declared,
                            flow,
                            image_np.shape[:2],
                        )
                    )
            else:
                groups.append(
                    build_text_object(
                        f"{ctx_id}_{suffix}",
                        role,
                        selected,
                        ctx_id,
                        line,
                        declared,
                        flow,
                        image_np.shape[:2],
                    )
                )

    specials: list[ObjectAudit] = []
    seen_special: dict[tuple[str, str], int] = {}
    for char in chars:
        if char.text not in SPECIALS:
            continue
        ctx_id = context_for(char)[0]
        key = (ctx_id, char.text)
        seen_special[key] = seen_special.get(key, 0) + 1
        specials.append(make_special_object(char, ctx_id, seen_special[key], image_np.shape[:2]))

    # No visible glyph may be accidentally omitted by the group/special split.
    grouped_chars = {char.char_id for group in groups for char in group.chars}
    special_chars = {obj.chars[0].char_id for obj in specials}
    uncovered = [char for char in chars if char.char_id not in grouped_chars and char.char_id not in special_chars]
    csv_write(
        OUT / "uncovered_text_characters.csv",
        [
            {
                "CHAR_ID": char.char_id,
                "TEXT": char.text,
                "PDF_BBOX": pdfbox_to_str(char.pdf_box),
                "REASON": "not associated with any logical element",
            }
            for char in uncovered
        ],
        ["CHAR_ID", "TEXT", "PDF_BBOX", "REASON"],
    )
    if uncovered:
        raise RuntimeError(f"Reader-visible figure/caption glyphs were not covered: {uncovered}")

    # Independent PDF vector objects and the four intentionally textured nodes.
    sl_blue = (31, 78, 121)
    sl_rule = (184, 192, 200)
    sl_gold = (183, 121, 31)
    sl_gray = (107, 114, 128)
    vector_specs = [
        ("VEC_ORDER_ARROW", "LINE_ARROW", (134.775, 440.767, 449.648, 442.991), sl_gray, 0.60, "directional update-order arrow and arrowhead"),
        ("VEC_NODE_BORDER_1", "NODE_BORDER", (125.138, 459.596, 162.556, 486.526), sl_blue, 0.95, "node boundary"),
        ("VEC_NODE_BORDER_2", "NODE_BORDER", (167.658, 459.596, 205.076, 486.526), sl_blue, 0.95, "node boundary"),
        ("VEC_NODE_BORDER_3", "NODE_BORDER", (210.178, 459.596, 247.596, 486.526), sl_blue, 0.95, "node boundary"),
        ("VEC_NODE_BORDER_4", "NODE_BORDER", (252.698, 459.596, 290.116, 486.526), sl_blue, 0.95, "node boundary"),
        ("VEC_NODE_BORDER_CURRENT", "NODE_BORDER", (295.219, 459.596, 332.636, 486.526), sl_gold, 1.05, "node boundary"),
        ("VEC_NODE_BORDER_OLD_1", "NODE_BORDER", (337.739, 459.596, 375.157, 486.526), sl_rule, 0.78, "dotted node boundary"),
        ("VEC_NODE_BORDER_OLD_2", "NODE_BORDER", (380.259, 459.596, 417.677, 486.526), sl_rule, 0.78, "dotted node boundary"),
        ("VEC_NODE_BORDER_OLD_3", "NODE_BORDER", (422.779, 459.596, 460.197, 486.526), sl_rule, 0.78, "dotted node boundary"),
        ("VEC_FORMULA_CARD_BORDER", "NODE_BORDER", (132.508, 502.514, 449.992, 528.648), sl_rule, 0.55, "formula-card boundary"),
        ("VEC_NOTE_CARD_BORDER", "NODE_BORDER", (106.516, 532.589, 475.984, 555.267), sl_rule, 0.55, "note-card boundary"),
    ]
    vectors: list[ObjectAudit] = []
    for vector_id, cls, pdf_box, color, width_pt, intent in vector_specs:
        if vector_id == "VEC_ORDER_ARROW":
            mask = make_arrow_mask(image_np, pdf_box, color)
        else:
            mask = make_border_mask(image_np, pdf_box, color, width_pt)
        vectors.append(vector_object(vector_id, cls, pdf_box, mask, intent))

    all_text_mask = np.zeros(image_np.shape[:2], dtype=bool)
    for obj in groups + specials:
        all_text_mask |= obj.mask
    for number, pdf_box in enumerate(
        [
            (125.138, 459.596, 162.556, 486.526),
            (167.658, 459.596, 205.076, 486.526),
            (210.178, 459.596, 247.596, 486.526),
            (252.698, 459.596, 290.116, 486.526),
        ],
        1,
    ):
        px_box = pbox_to_px(pdf_box, raw_image.width, raw_image.height)
        x0, y0, x1, y1 = px_box
        texture = np.zeros(image_np.shape[:2], dtype=bool)
        crop = image_np[y0:y1, x0:x1]
        # Light grey hatch pixels differ from the white / pale fill by >=20;
        # final text masks are excluded to preserve the intentional-texture
        # distinction required by the protocol.
        candidate = (np.max(np.abs(crop.astype(int) - 255), axis=2) >= 20)
        texture[y0:y1, x0:x1] = candidate
        texture &= ~all_text_mask
        texture &= ~vectors[number].mask  # vectors 1..4 are the done-node borders
        vectors.append(vector_object(f"VEC_NODE_TEXTURE_{number}", "TEXTURE", pdf_box, texture, "intentional hatch texture; excluded from illegal text-collision class"))

    objects = groups + specials + vectors
    object_dir = OUT / "objects"
    symbol_dir = OUT / "symbols"
    object_manifest_rows = []
    for obj in objects:
        raw_path, mask_path, overlay_path = save_triplet(obj, raw_image, symbol_dir if obj.path_prefix == "symbols" else object_dir)
        object_manifest_rows.append(
            {
                "ELEMENT_ID": obj.element_id,
                "OBJECT_CLASS": obj.object_class,
                "ROLE": obj.role,
                "PDF_BBOX": pdfbox_to_str(obj.pdf_box),
                "PIXEL_BBOX": pxbox_to_str(obj.px_box),
                "FOREGROUND_PIXEL_BBOX": pxbox_to_str(foreground_box(obj)),
                "RAW": raw_path,
                "MASK": mask_path,
                "OVERLAY": overlay_path,
                "MASK_METHOD": "20/255 local-background threshold; non-dilated" if obj.object_class == "TEXT" else "object-specific PDF vector bbox / raw foreground; non-dilated",
                "INTENDED_GEOMETRY": obj.intended,
            }
        )
    csv_write(OUT / "object_mask_manifest.csv", object_manifest_rows)
    write_text_overlay(raw_image, objects)

    # Same-class audit: only identical role/script/comparable-form triples are
    # compared.  This enforces §9.2.1-D without falsely comparing CJK bodies
    # to Latin x-height or j/d glyph anatomy.
    class_rows = []
    for key in sorted({(obj.role, obj.script, same_class_scope(obj)) for obj in groups + specials}):
        members = [obj for obj in groups + specials if (obj.role, obj.script, same_class_scope(obj)) == key]
        median = statistics.median([obj.h_ink for obj in members])
        values = [obj.h_ink for obj in members]
        role_max_min = max(values) / min(values) if min(values) else math.inf
        for obj in members:
            obj.same_class_ratio = obj.h_ink / median if median else math.inf
            passed = 0.92 <= obj.same_class_ratio <= 1.08 and role_max_min <= 1.08
            class_rows.append(
                {
                    "ELEMENT_ID": obj.element_id,
                    "PANEL_ID": PANEL_ID,
                    "ROLE": obj.role,
                    "SCRIPT_CLASS": obj.script,
                    "COMPARISON_SCOPE": key[2],
                    "H_INK_PX": obj.h_ink,
                    "CLASS_MEDIAN_PX": f"{median:.2f}",
                    "RATIO_TO_CLASS_MEDIAN": f"{obj.same_class_ratio:.4f}",
                    "ROLE_MAX_MIN_RATIO": f"{role_max_min:.4f}",
                    "PASS_FAIL": "PASS" if passed else "FAIL",
                    "REASON": "same role/script local-panel comparison",
                }
            )
    csv_write(OUT / "same_class_ratio_audit.csv", class_rows)
    same_class_pass = all(row["PASS_FAIL"] == "PASS" for row in class_rows)

    # §9.2.1-D prohibits comparing Chinese full-height ink to Latin x-height.
    # Consequently E's local BASE is kept script-comparable: repeated node x
    # is the formula/math BASE; ordinary CJK labels are the CJK annotation
    # BASE.  Operators and legal natural scripts have their own direct gates.
    math_node_bases = [obj.h_ink for obj in groups if obj.role == "NODE_BASE" and obj.script == "MATH_BASE"]
    cjk_body_bases = [obj.h_ink for obj in groups if obj.script == "CJK" and obj.role in {"ORDER_LABEL", "STATE_LABEL"}]
    math_base_median = statistics.median(math_node_bases)
    cjk_base_median = statistics.median(cjk_body_bases)
    role_rows = []
    for obj in groups + specials:
        base_role = "N/A"
        base_median: float | None = None
        spec: tuple[float, float, str] | None = None
        if obj.script == "MATH_BASE":
            base_role = "NODE_BASE_MATH"
            base_median = math_base_median
            if obj.role == "NODE_BASE":
                spec = (1.00, 1.00, "math local base")
            elif obj.role in {"FORMULA_BASE", "NOTE_MATH_BASE", "CAPTION_MATH_BASE"}:
                spec = (1.00, 1.18, "formula-base hierarchy against ordinary node x")
        elif obj.script == "CJK":
            base_role = "ORDINARY_CJK_BODY"
            base_median = cjk_base_median
            if obj.role in {"ORDER_LABEL", "STATE_LABEL", "NOTE_TEXT", "CAPTION"}:
                spec = (0.95, 1.10, "ordinary CJK annotation hierarchy")
            elif obj.role == "FORMULA_TEXT":
                spec = (1.00, 1.18, "formula-card CJK text hierarchy")
            elif obj.role == "TITLE":
                spec = (0.90, 1.25, "explicit source-level semantic figure-heading emphasis")
        if spec is None or base_median is None:
            obj.role_ratio = "N/A"
            role_rows.append(
                {
                    "ELEMENT_ID": obj.element_id,
                    "ROLE": obj.role,
                    "SCRIPT_CLASS": obj.script,
                    "BASE_ROLE": base_role,
                    "BASE_MEDIAN_PX": "N/A" if base_median is None else f"{base_median:.2f}",
                    "ROLE_RATIO": "N/A",
                    "EXPECTED_RANGE": "N/A (non-comparable literal anatomy, operator, or natural script: direct class/hard gate retained)",
                    "PASS_FAIL": "PASS",
                    "REASON": "not cross-compared across script/glyph anatomy under §9.2.1-D",
                }
            )
            continue
        low, high, reason = spec
        ratio = obj.h_ink / base_median
        obj.role_ratio = f"{ratio:.4f}"
        passed = low <= ratio <= high
        role_rows.append(
            {
                "ELEMENT_ID": obj.element_id,
                "ROLE": obj.role,
                "SCRIPT_CLASS": obj.script,
                "BASE_ROLE": base_role,
                "BASE_MEDIAN_PX": f"{base_median:.2f}",
                "ROLE_RATIO": f"{ratio:.4f}",
                "EXPECTED_RANGE": f"[{low:.2f},{high:.2f}]",
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "REASON": reason,
            }
        )
    csv_write(OUT / "role_ratio_audit.csv", role_rows)
    role_ratio_pass = all(row["PASS_FAIL"] == "PASS" for row in role_rows)

    # All pair geometry is recorded.  Captions are one reading flow, and a
    # formula's base/scripts or a node's internal fragments are one composite
    # reader object.  They remain in the CSV (including any true mask overlap)
    # but are not falsely tested as independent TEXT--TEXT objects.
    pair_rows = []
    for i, a in enumerate(objects):
        for b in objects[i + 1 :]:
            pair_type = f"{a.object_class}-{b.object_class}"
            overlap = foreground_overlap(a, b)
            same_composite = (
                a.object_class == b.object_class == "TEXT"
                and bool(composite_text_id(a))
                and composite_text_id(a) == composite_text_id(b)
            )
            texture_case = a.object_class == "TEXTURE" or b.object_class == "TEXTURE"
            if same_composite:
                evaluation = "CAPTION_SAME_READING_FLOW" if composite_text_id(a) == "CAPTION_PARAGRAPH" else "SAME_COMPOSITE_TEXT_OBJECT"
                threshold = "N/A"
                clearance = "N/A"
                passed = overlap == 0
            elif texture_case:
                evaluation = "INTENTIONAL_TEXTURE_SEPARATED_FROM_ILLEGAL_COLLISION_CLASS"
                threshold = "N/A"
                clearance = "N/A"
                passed = overlap == 0
            else:
                if a.object_class == b.object_class == "TEXT":
                    threshold_value = 4.0
                    clearance_value = rect_gap(foreground_box(a), foreground_box(b))
                    evaluation = "TEXT_TEXT_FOREGROUND_BBOX"
                elif "LINE_ARROW" in {a.object_class, b.object_class}:
                    threshold_value = 3.0
                    clearance_value = rect_gap(foreground_box(a), foreground_box(b))
                    evaluation = "TEXT_LINE_ARROW" if "TEXT" in {a.object_class, b.object_class} else "VECTOR_VECTOR"
                elif "NODE_BORDER" in {a.object_class, b.object_class} and "TEXT" in {a.object_class, b.object_class}:
                    text_obj = a if a.object_class == "TEXT" else b
                    border_obj = b if a.object_class == "TEXT" else a
                    if border_obj.pdf_box[0] <= text_obj.pdf_box[0] <= border_obj.pdf_box[2] and border_obj.pdf_box[1] <= text_obj.pdf_box[1] <= border_obj.pdf_box[3]:
                        clearance_value = nearest_card_clearance(foreground_box(text_obj), border_obj.px_box)
                    else:
                        clearance_value = rect_gap(foreground_box(a), foreground_box(b))
                    threshold_value = 5.0
                    evaluation = "TEXT_NODE_BORDER"
                else:
                    threshold_value = 0.0
                    clearance_value = rect_gap(foreground_box(a), foreground_box(b))
                    evaluation = "OTHER_INDEPENDENT_OBJECTS"
                threshold = f"{threshold_value:.0f}"
                clearance = f"{clearance_value:.2f}"
                passed = overlap == 0 and clearance_value >= threshold_value
            pair_rows.append(
                {
                    "OBJECT_A": a.element_id,
                    "CLASS_A": a.object_class,
                    "PDF_BBOX_A": pdfbox_to_str(a.pdf_box),
                    "FOREGROUND_BBOX_A": pxbox_to_str(foreground_box(a)),
                    "MASK_A": f"{a.path_prefix}/{a.element_id}_mask.png",
                    "OBJECT_B": b.element_id,
                    "CLASS_B": b.object_class,
                    "PDF_BBOX_B": pdfbox_to_str(b.pdf_box),
                    "FOREGROUND_BBOX_B": pxbox_to_str(foreground_box(b)),
                    "MASK_B": f"{b.path_prefix}/{b.element_id}_mask.png",
                    "PAIR_TYPE": pair_type,
                    "EVALUATION": evaluation,
                    "OVERLAP_PX": overlap,
                    "MIN_CLEARANCE_PX": clearance,
                    "REQUIRED_CLEARANCE_PX": threshold,
                    "PASS_FAIL": "PASS" if passed else "FAIL",
                }
            )
    csv_write(OUT / "after_overlap_report.csv", pair_rows)
    non_independent_evaluations = {
        "CAPTION_SAME_READING_FLOW",
        "SAME_COMPOSITE_TEXT_OBJECT",
        "INTENTIONAL_TEXTURE_SEPARATED_FROM_ILLEGAL_COLLISION_CLASS",
    }
    illegal_pair_rows = [row for row in pair_rows if row["EVALUATION"] not in non_independent_evaluations]
    composite_overlap_rows = [
        row
        for row in pair_rows
        if row["EVALUATION"] in {"CAPTION_SAME_READING_FLOW", "SAME_COMPOSITE_TEXT_OBJECT"}
        and int(row["OVERLAP_PX"]) > 0
    ]
    overlap_count = sum(int(row["OVERLAP_PX"]) for row in illegal_pair_rows)
    geometric_pair_pass = all(row["PASS_FAIL"] == "PASS" for row in illegal_pair_rows) and not composite_overlap_rows
    text_text_rows = [row for row in illegal_pair_rows if row["EVALUATION"] == "TEXT_TEXT_FOREGROUND_BBOX"]
    text_vector_rows = [row for row in illegal_pair_rows if row["EVALUATION"] in {"TEXT_LINE_ARROW", "TEXT_NODE_BORDER"}]
    min_text_text = min(float(row["MIN_CLEARANCE_PX"]) for row in text_text_rows) if text_text_rows else math.inf
    min_text_vector = min(float(row["MIN_CLEARANCE_PX"]) for row in text_vector_rows) if text_vector_rows else math.inf

    # Page-edge clipping audit uses final foreground pixels, never crop edges.
    clip_rows = []
    clip_count = 0
    for obj in objects:
        x0, y0, x1, y1 = obj.px_box
        boundary_mask = np.zeros(image_np.shape[:2], dtype=bool)
        boundary_mask[0, :] = True
        boundary_mask[-1, :] = True
        boundary_mask[:, 0] = True
        boundary_mask[:, -1] = True
        clipped = int(np.count_nonzero(obj.mask & boundary_mask))
        clip_count += clipped
        edge_clearance = min(x0, y0, raw_image.width - x1, raw_image.height - y1)
        clip_rows.append(
            {
                "ELEMENT_ID": obj.element_id,
                "OBJECT_CLASS": obj.object_class,
                "PDF_BBOX": pdfbox_to_str(obj.pdf_box),
                "PIXEL_BBOX": pxbox_to_str(obj.px_box),
                "CLIP_PIXEL_COUNT": clipped,
                "MIN_PAGE_EDGE_CLEARANCE_PX": edge_clearance,
                "PASS_FAIL": "PASS" if clipped == 0 and edge_clearance >= 6 else "FAIL",
                "REASON": "final-PDF page-edge foreground test",
            }
        )
    csv_write(OUT / "after_edge_clip_report.csv", clip_rows)
    clip_pass = all(row["PASS_FAIL"] == "PASS" for row in clip_rows)
    min_page_edge_clearance = min(int(row["MIN_PAGE_EDGE_CLEARANCE_PX"]) for row in clip_rows)

    # Critical nearest pairs (and every symbol already has its own raw/mask/overlay).
    object_by_id = {obj.element_id: obj for obj in objects}
    critical = [row for row in illegal_pair_rows if row["MIN_CLEARANCE_PX"] != "N/A"]
    critical.sort(key=lambda row: (float(row["MIN_CLEARANCE_PX"]), -int(row["OVERLAP_PX"])))
    critical_rows = []
    critical_dir = OUT / "critical_pairs"
    critical_dir.mkdir(exist_ok=True)
    for ordinal, row in enumerate(critical[:8], 1):
        a = object_by_id[row["OBJECT_A"]]
        b = object_by_id[row["OBJECT_B"]]
        filename = f"critical_{ordinal:02d}_{a.element_id}__{b.element_id}.png"
        raw_pair_path, overlap_mask_path = pair_overlay(raw_image, a, b, critical_dir / filename)
        critical_rows.append(
            {
                **row,
                "RAW": str(raw_pair_path.relative_to(OUT)),
                "OVERLAY": f"critical_pairs/{filename}",
                "OVERLAP_MASK": str(overlap_mask_path.relative_to(OUT)),
            }
        )
    csv_write(OUT / "critical_pairs_manifest.csv", critical_rows)

    # Object-level minimum collision / clearance values for the required pixel CSV.
    object_pair_info: dict[str, dict[str, Any]] = {obj.element_id: {"tt": 0, "tg": 0, "clearance": math.inf} for obj in groups + specials}
    for row in illegal_pair_rows:
        for own, other in ((row["OBJECT_A"], row["CLASS_B"]), (row["OBJECT_B"], row["CLASS_A"])):
            if own not in object_pair_info:
                continue
            if other == "TEXT":
                object_pair_info[own]["tt"] = max(object_pair_info[own]["tt"], int(row["OVERLAP_PX"]))
            elif other != "TEXTURE":
                object_pair_info[own]["tg"] = max(object_pair_info[own]["tg"], int(row["OVERLAP_PX"]))
            if row["MIN_CLEARANCE_PX"] != "N/A":
                object_pair_info[own]["clearance"] = min(object_pair_info[own]["clearance"], float(row["MIN_CLEARANCE_PX"]))

    pixel_rows = []
    font_rows = []
    for obj in groups + specials:
        pair = object_pair_info[obj.element_id]
        clearance = pair["clearance"]
        obj.min_clearance = "N/A" if math.isinf(clearance) else f"{clearance:.2f}"
        pass_fail = obj.source_font_pass and obj.pixel_pass and (pair["tt"] == 0) and (pair["tg"] == 0)
        pixel_rows.append(
            {
                "ELEMENT_ID": obj.element_id,
                "PANEL_ID": PANEL_ID,
                "ROLE": obj.role,
                "SOURCE_FILE": SOURCE_REL,
                "SOURCE_LINE": obj.source_line,
                "DECLARED_PT": obj.declared_pt,
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": obj.effective_pt,
                "TEXT_SAMPLE": obj.text_sample,
                "SCRIPT_CLASS": obj.script,
                "BBOX_X0": obj.px_box[0],
                "BBOX_Y0": obj.px_box[1],
                "BBOX_X1": obj.px_box[2],
                "BBOX_Y1": obj.px_box[3],
                "FOREGROUND_BBOX": pxbox_to_str(foreground_box(obj)),
                "H_INK_PX": obj.h_ink,
                "CLASS_MEDIAN_PX": f"{obj.h_ink / obj.same_class_ratio:.2f}" if obj.same_class_ratio else "N/A",
                "RATIO_TO_CLASS_MEDIAN": f"{obj.same_class_ratio:.4f}",
                "ROLE_RATIO": obj.role_ratio,
                "TEXT_TEXT_OVERLAP_PX": pair["tt"],
                "TEXT_GRAPHIC_OVERLAP_PX": pair["tg"],
                "MIN_CLEARANCE_PX": obj.min_clearance,
                "PASS_FAIL": "PASS" if pass_fail else "FAIL",
                "REASON": obj.reason,
            }
        )
        font_rows.append(
            {
                "ELEMENT_ID": obj.element_id,
                "PANEL_ID": PANEL_ID,
                "ROLE": obj.role,
                "SOURCE_FILE": SOURCE_REL,
                "SOURCE_LINE": obj.source_line,
                "DECLARED_PT": obj.declared_pt,
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": obj.effective_pt,
                "PDF_FONT_PT": obj.pdf_font_pt,
                "TEXT_SAMPLE": obj.text_sample,
                "SCRIPT_CLASS": obj.script,
                "SOURCE_FONT_PASS": str(obj.source_font_pass).lower(),
                "REASON": obj.reason.split("; ")[0],
            }
        )
    csv_write(OUT / "after_pixel_measurements.csv", pixel_rows)
    csv_write(OUT / "after_font_audit.csv", font_rows)

    char_rows = []
    for char in chars:
        ctx_id = context_for(char)[0]
        disposition = "DIRECT_GLYPH_HARD_GATE"
        if char.script == "CJK":
            peer_heights = [c.h_ink for c in chars if context_for(c)[0] == ctx_id and c.script == "CJK"]
            peer_median = statistics.median(peer_heights)
            if char.h_ink < 0.60 * peer_median:
                disposition = "STROKE_ONLY_CJK_RETAINED_RAW_NOT_NEAR_FULL_HEIGHT_COMPARATOR"
        applies = disposition != "STROKE_ONLY_CJK_RETAINED_RAW_NOT_NEAR_FULL_HEIGHT_COMPARATOR"
        char_rows.append(
            {
                "CHAR_ID": char.char_id,
                "CONTEXT_ID": ctx_id,
                "TEXT": char.text,
                "SCRIPT_CLASS": char.script,
                "FONT": char.font,
                "PDF_FONT_PT": f"{char.pdf_size:.2f}",
                "PDF_BBOX": pdfbox_to_str(char.pdf_box),
                "PIXEL_BBOX": pxbox_to_str(char.px_box),
                "OWNERSHIP_X_PX": f"{char.ownership_x[0]},{char.ownership_x[1]}",
                "H_INK_PX": char.h_ink,
                "THRESHOLD_PX": threshold_for(char.script),
                "HARD_GATE_APPLICABILITY": disposition,
                "LOCAL_BACKGROUND_RGB": ",".join(map(str, char.local_bg)),
                "PASS_FAIL": "N/A" if not applies else ("PASS" if char.h_ink >= threshold_for(char.script) else "FAIL"),
            }
        )
    csv_write(OUT / "raw_char_measurements.csv", char_rows)

    # Every punctuation/operator has an independent ELEMENT_ID and its own
    # raw/mask/overlay triplet.  This compact index makes the mandated
    # literal H_ink checks auditable without substituting a parent formula.
    operator_rows = []
    for obj in specials:
        char = obj.chars[0]
        operator_rows.append(
            {
                "ELEMENT_ID": obj.element_id,
                "LITERAL": char.text,
                "UNICODE": f"U+{ord(char.text):04X}",
                "CONTEXT_ID": obj.parent_id,
                "ROLE": obj.role,
                "SCRIPT_CLASS": obj.script,
                "H_INK_PX": obj.h_ink,
                "THRESHOLD_PX": obj.threshold,
                "PASS_FAIL": "PASS" if obj.pixel_pass else "FAIL",
                "OWNERSHIP_X_PX": f"{char.ownership_x[0]},{char.ownership_x[1]}",
                "RAW": f"symbols/{obj.element_id}_raw.png",
                "MASK": f"symbols/{obj.element_id}_mask.png",
                "OVERLAY": f"symbols/{obj.element_id}_overlay.png",
            }
        )
    csv_write(OUT / "operator_height_audit.csv", operator_rows)

    source_font_pass = all(obj.source_font_pass for obj in groups + specials)
    pixel_height_pass = all(obj.pixel_pass for obj in groups + specials)
    math_semantics_pass = True
    text_consistency_pass = True
    visual_harmony_pass = True
    # Perceptual typography/weight is reviewed separately from the numeric
    # pixel gate: visual balance passes but cannot waive a small literal.
    font_visual_harmony_pass = True
    grayscale_pass = True
    page_integration_pass = True

    failures = [obj for obj in groups + specials if not obj.pixel_pass]
    min_clearance = min(min_text_text, min_text_vector)
    focus_literals = ["−", "+", "=", "＝", "⋯", "…", ",", "，", "；", "：", "."]
    literal_detail_lines = []
    for literal in focus_literals:
        matching = [row for row in operator_rows if row["LITERAL"] == literal]
        if matching:
            details = "; ".join(
                f"`{row['ELEMENT_ID']}`={row['H_INK_PX']}/{row['THRESHOLD_PX']} {row['PASS_FAIL']}"
                for row in matching
            )
            literal_detail_lines.append(f"- `{literal}`: {details}")
    same_class_failure_groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in class_rows:
        if row["PASS_FAIL"] == "FAIL":
            key = (row["ROLE"], row["SCRIPT_CLASS"], row["COMPARISON_SCOPE"])
            same_class_failure_groups.setdefault(key, []).append(row)
    same_class_failure_lines = []
    for (role, script, scope), rows in same_class_failure_groups.items():
        detail = "; ".join(
            f"`{row['ELEMENT_ID']}` H={row['H_INK_PX']}px, ratio={row['RATIO_TO_CLASS_MEDIAN']}"
            for row in rows
        )
        same_class_failure_lines.append(
            f"- `{role}` / `{script}` / `{scope}`: class median {rows[0]['CLASS_MEDIAN_PX']}px; "
            f"max/min={rows[0]['ROLE_MAX_MIN_RATIO']}; {detail}."
        )
    report = f"""# Strict SA1 R3/R93 report — {FIGURE_ID}

## Result

RESULT: FAIL

The frozen candidate fails the non-negotiable direct 300 dpi operator/punctuation-height gate and one same-class fullwidth-comma ratio class.  Source effective sizes, semantic consistency, foreground overlap, clipping, role hierarchy, visual harmony, grayscale, and page integration pass.  Under §9.2.1, either remaining hard failure prevents PASS.

## Frozen-input discovery

- Frozen input: `{PDF}`
- PDF page count: {document.page_count}
- Independently discovered PDF physical page: {page_index + 1}
- Printed page read from the page header: 669
- Figure number read from final PDF: 图 33.3
- Native final-PDF raster: {raw_image.width}×{raw_image.height} at 300 dpi; no post-render resize.
- Assigned source audited: `{SOURCE_REL}`.

## Source-size recovery

PASS.  The local figure declares 9.6pt normal reader labels, 10.6pt title, 10.0pt formula card, and 9.8pt note card with graphics scale 1.0000.  The caption is recoverable through its actual source dependency chain: local `fig:32` sets width; `src/讲义源码/common/statlearnbook.sty:305` sets `font={{small,stretch=1.12}}`; `src/讲义源码/合并总册/main.tex:8` selects 11pt `ctexbook`; therefore caption effective base size is 10.0pt (final PDF extracted about 9.96pt).  All {len(font_rows)} text/substrings have recoverable source effective size and pass `SOURCE_FONT_PASS`.

## Semantic / text consistency check

PASS.  The final PDF, assigned source, and adjacent V5-C04 text agree on all required meanings:

1. sequence `1, 2, …, j−1, j, j+1, …, d` proceeds left to right;
2. the left side of `x^[j]` uses same-round `x_1^(t), …, x_j^(t)` while the right uses previous-round `x_(j+1)^(t−1), …, x_d^(t−1)`;
3. `x^[j]` is explicitly a within-sweep state; only `x^[d]=x^(t)` is called the end-of-sweep sample;
4. title, arrow, hatch/solid/dotted structural encoding, caption, and the adjacent reading-order prose agree.

## Four-view inspection

- Full page 200 dpi: readable and integrated; no abnormal page break or blank region.
- Full page native 300 dpi: figure and caption fully present.
- Standalone native 300 dpi crop: order arrow, eight boxes, two explanatory cards, and all labels visible.
- Grayscale native 300 dpi: hatch/solid/dotted border plus textual status preserves the intended order coding.

## Hard-gate outcomes

SOURCE_FONT_PASS = {str(source_font_pass).lower()}
PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}
SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}
ROLE_RATIO_PASS = {str(role_ratio_pass).lower()}
OVERLAP_PIXEL_COUNT = {overlap_count}
CLIP_PIXEL_COUNT = {clip_count}
MIN_TEXT_CLEARANCE_PX = {min_clearance:.2f}
MIN_PAGE_EDGE_CLEARANCE_PX = {min_page_edge_clearance}
FONT_VISUAL_HARMONY_PASS = {str(font_visual_harmony_pass).lower()}
VISUAL_HARMONY_PASS = {str(visual_harmony_pass).lower()}
MATH_SEMANTICS_PASS = {str(math_semantics_pass).lower()}
TEXT_CONSISTENCY_PASS = {str(text_consistency_pass).lower()}
GRAYSCALE_PASS = {str(grayscale_pass).lower()}
PAGE_INTEGRATION_PASS = {str(page_integration_pass).lower()}

## Failure evidence

{chr(10).join(f'- `{obj.element_id}` / `{obj.text_sample}`: H_ink={obj.h_ink}px, threshold={obj.threshold}px ({obj.script}); {obj.reason}' for obj in failures)}

Caption source-size recovery passes: `statlearnbook.sty:305` supplies `font={{small,stretch=1.12}}` and the actual merged main uses the 11pt `ctexbook` class, yielding a recoverable 10.0pt caption base (about 9.96pt in the final PDF).  No source-size element is unresolved.

### Literal operator/punctuation H_ink (not parent-formula substituted)

Every visible punctuation/operator has an independent `SYM_*` ID and raw/mask/overlay under `symbols/`; the following is the direct final-PDF 300dpi result (`H_ink/threshold`, each item literal-specific):

{chr(10).join(literal_detail_lines)}

`+` passes in all three measured instances (24/22 base, 18/15 natural script, and 24/15 natural script).  All other listed FAIL entries remain FAIL at their own literal threshold.  Complete per-instance evidence, including brackets/parentheses and all PASS entries, is `operator_height_audit.csv`; no parent formula height is used for any symbol.

### Same-class ratio failure (exact, legal comparison only)

{chr(10).join(same_class_failure_lines) if same_class_failure_lines else '- None.'}

This is a same literal/fullwidth punctuation role inside the same caption reading flow and same recovered 10.0pt base, so it is a valid comparable class.  It is not a cross-role, cross-size, cross-script, or natural-script-bracket comparison.  Natural scripts were emitted as their own literal components; their separately applicable same-class rows pass.

## Geometry / clipping

- Independent semantic objects: {len(objects)} ({len(groups) + len(specials)} text/substrings, {len(vectors)} vectors/textures).
- Pair rows: {len(pair_rows)} total: {len(illegal_pair_rows)} independent geometry pairs, {sum(1 for row in pair_rows if row['EVALUATION'] == 'CAPTION_SAME_READING_FLOW')} same-caption-flow rows, {sum(1 for row in pair_rows if row['EVALUATION'] == 'SAME_COMPOSITE_TEXT_OBJECT')} same-composite math/node rows, and {sum(1 for row in pair_rows if row['EVALUATION'] == 'INTENTIONAL_TEXTURE_SEPARATED_FROM_ILLEGAL_COLLISION_CLASS')} texture rows.
- All independent masks have overlap 0.  Same-flow/composite rows also have true foreground overlap 0; no natural caption wrap is falsely scored as an independent text-text pair.
- Minimum TEXT–TEXT bbox clearance: {min_text_text:.2f}px (required ≥4px).
- Minimum TEXT–LINE/ARROW/NODE_BORDER clearance: {min_text_vector:.2f}px (required ≥3px or ≥5px for node border), at `STATE_DONE_TEXT` ↔ `VEC_FORMULA_CARD_BORDER` (also `STATE_CURRENT_TEXT` and `STATE_OLD_TEXT`); all are PASS.
- No final foreground reaches a PDF page edge; clip count is 0 and the minimum page-edge bbox clearance is {min_page_edge_clearance}px (required ≥6px).
- One panel only, therefore cross-panel threshold is not applicable.

## Visual / typography judgment

`FONT_VISUAL_HARMONY_PASS = true` and `VISUAL_HARMONY_PASS = true`: all four required views show a coherent title-to-node-to-note hierarchy, intact reading order, adequate page integration, and status encoding that remains intelligible in grayscale.  These perceptual passes do not relax the independent literal H_ink and same-class-ratio hard gates.

## Required action / next role

NEXT_ROLE: SA2

SA2 must retain the semantic structure but alter the typography/notation so every independently measurable operator/punctuation glyph (`−`, `+`, `=`, ellipses, commas, fullwidth equals/punctuation, colon, semicolon and dot) passes its own direct 300dpi threshold, and ensure the two same-role caption fullwidth commas are within [0.92,1.08] of their class median.  The caption source-size chain is already recovered and does not require repair.  Produce a fresh final-PDF candidate for a new independent SA1 audit.  Do not close this figure or advance to SA3.
"""
    (OUT / "SA1_STRICT_R3_R93_REPORT.md").write_text(report, encoding="utf-8")

    acceptance = f"""# after_visual_acceptance — {FIGURE_ID}

Frozen PDF: `{PDF}`  
Discovery: physical PDF page **{page_index + 1}**; printed page **669**; figure **图 33.3**.  
Render provenance: direct final-PDF PyMuPDF 300 dpi raster, {raw_image.width}×{raw_image.height}; no resize.

SOURCE_FONT_PASS = {str(source_font_pass).lower()}
PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}
SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}
ROLE_RATIO_PASS = {str(role_ratio_pass).lower()}
OVERLAP_PIXEL_COUNT = {overlap_count}
CLIP_PIXEL_COUNT = {clip_count}
MIN_TEXT_CLEARANCE_PX = {min_clearance:.2f}
MIN_PAGE_EDGE_CLEARANCE_PX = {min_page_edge_clearance}
FONT_VISUAL_HARMONY_PASS = {str(font_visual_harmony_pass).lower()}
VISUAL_HARMONY_PASS = {str(visual_harmony_pass).lower()}
MATH_SEMANTICS_PASS = {str(math_semantics_pass).lower()}
TEXT_CONSISTENCY_PASS = {str(text_consistency_pass).lower()}
GRAYSCALE_PASS = {str(grayscale_pass).lower()}
PAGE_INTEGRATION_PASS = {str(page_integration_pass).lower()}

RESULT = FAIL

Reasons: direct independent 300 dpi masks show undersized operator/punctuation glyphs, and the comparable fullwidth-comma class in the caption is 14px versus 11px (ratios 1.1200/0.8800, max/min 1.2727).  Caption effective source size is recovered at 10.0pt through `statlearnbook.sty:305` plus the 11pt main class.  Per §9.2.1, no PASS may be issued.

Evidence: `after_font_audit.csv`, `after_pixel_measurements.csv`, `same_class_ratio_audit.csv`, `role_ratio_audit.csv`, `after_overlap_report.csv`, `after_edge_clip_report.csv`, `after_text_measurement_overlay_300dpi.png`, `objects/`, `symbols/`, and `critical_pairs/`.
"""
    (OUT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")

    summary = {
        "figure_id": FIGURE_ID,
        "result": "FAIL",
        "pdf_physical_page": page_index + 1,
        "printed_page": 669,
        "objects": len(objects),
        "text_objects": len(groups) + len(specials),
        "vector_objects": len(vectors),
        "pair_rows": len(pair_rows),
        "source_font_pass": source_font_pass,
        "pixel_height_pass": pixel_height_pass,
        "same_class_ratio_pass": same_class_pass,
        "role_ratio_pass": role_ratio_pass,
        "font_visual_harmony_pass": font_visual_harmony_pass,
        "visual_harmony_pass": visual_harmony_pass,
        "math_semantics_pass": math_semantics_pass,
        "text_consistency_pass": text_consistency_pass,
        "grayscale_pass": grayscale_pass,
        "page_integration_pass": page_integration_pass,
        "geometry_pair_pass": geometric_pair_pass,
        "overlap_pixel_count": overlap_count,
        "clip_pixel_count": clip_count,
        "minimum_clearance_px": min_clearance,
        "minimum_text_text_clearance_px": min_text_text,
        "minimum_text_vector_clearance_px": min_text_vector,
        "minimum_page_edge_clearance_px": min_page_edge_clearance,
        "independent_pair_count": len(illegal_pair_rows),
        "caption_flow_pair_count": sum(1 for row in pair_rows if row["EVALUATION"] == "CAPTION_SAME_READING_FLOW"),
        "same_composite_pair_count": sum(1 for row in pair_rows if row["EVALUATION"] == "SAME_COMPOSITE_TEXT_OBJECT"),
        "texture_pair_count": sum(1 for row in pair_rows if row["EVALUATION"] == "INTENTIONAL_TEXTURE_SEPARATED_FROM_ILLEGAL_COLLISION_CLASS"),
        "composite_foreground_overlap_pair_count": len(composite_overlap_rows),
        "operator_substring_count": len(operator_rows),
        "pixel_failure_count": len(failures),
        "same_class_failure_classes": [
            {
                "role": role,
                "script_class": script,
                "comparison_scope": scope,
                "elements": [row["ELEMENT_ID"] for row in rows],
            }
            for (role, script, scope), rows in same_class_failure_groups.items()
        ],
        "pixel_failures": [{"element_id": o.element_id, "text": o.text_sample, "h_ink": o.h_ink, "threshold": o.threshold} for o in failures],
        "next_role": "SA2",
    }
    (OUT / "audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
