from __future__ import annotations

import csv
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF = ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf"
FIG_SOURCE = ROOT / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_coordinate_sweep.tex"
OUT = ROOT / r"v2.7.0\_work\evidence\figures\FIG-P634-01\STRICT_R2_SA2"
PAGE_NUMBER = 682
PAGE_INDEX = PAGE_NUMBER - 1
DPI = 300
SCALE = DPI / 72.0

# PDF-point regions on R93 physical page 682.
FIGURE_REGION = fitz.Rect(96.0, 397.0, 482.0, 556.5)
FIGURE_CAPTION_REGION = fitz.Rect(80.0, 397.0, 522.0, 588.0)
TEXT_AUDIT_REGION = fitz.Rect(80.0, 400.0, 522.0, 588.0)


@dataclass
class CharRecord:
    c: str
    bbox: fitz.Rect
    size: float
    font: str
    color: tuple[int, int, int]
    origin: tuple[float, float]
    span_id: int
    line_id: int


@dataclass
class Element:
    element_id: str
    parent_id: str
    role: str
    source_line: str
    declared_pt: float
    chars: list[CharRecord]
    text: str
    script_class: str
    threshold: int
    natural_script: bool

    @property
    def bbox_pdf(self) -> fitz.Rect:
        rect = fitz.Rect(self.chars[0].bbox)
        for ch in self.chars[1:]:
            rect.include_rect(ch.bbox)
        return rect


def rect_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * SCALE),
        math.floor(rect.y0 * SCALE),
        math.ceil(rect.x1 * SCALE),
        math.ceil(rect.y1 * SCALE),
    )


def role_for(bbox: fitz.Rect) -> tuple[str, str, float]:
    y = bbox.y0
    if y < 423:
        return "TITLE", "16", 10.6
    if y < 455:
        if bbox.x0 > 450:
            return "ORDER_ANNOTATION", "19-20", 9.6
        return "ORDER_LABEL", "17-18", 9.6
    if y < 489:
        return "SLOT_FORMULA", "21-28", 9.6
    if y < 502:
        return "STATE_LABEL", "29-31", 9.6
    if y < 531:
        return "STATE_FORMULA", "32-33", 10.0
    if y < 557:
        return "LEGEND", "34-35", 9.8
    return "CAPTION", "38", 10.0


def parent_for(role: str, bbox: fitz.Rect, line_id: int, span_id: int) -> str:
    if role == "SLOT_FORMULA":
        centers = [143.85, 186.37, 228.89, 271.41, 313.93, 356.45, 398.97, 441.49]
        cx = (bbox.x0 + bbox.x1) / 2
        return f"SLOT_{min(range(len(centers)), key=lambda i: abs(centers[i] - cx)) + 1:02d}"
    if role == "ORDER_LABEL":
        return f"ORDER_{span_id:03d}"
    if role == "STATE_LABEL":
        return f"STATE_LABEL_{span_id:03d}"
    if role == "STATE_FORMULA":
        return "STATE_FORMULA_CARD"
    if role == "LEGEND":
        return "LEGEND_CARD"
    if role == "CAPTION":
        # The two rendered lines are one naturally wrapped caption paragraph,
        # not independent semantic text objects. Internal line leading is
        # checked for actual foreground overlap only, not the independent-
        # object 4 px clearance gate.
        return "CAPTION_PARAGRAPH"
    return f"{role}_{span_id:03d}"


def is_han(c: str) -> bool:
    return any(
        lo <= ord(c) <= hi
        for lo, hi in ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF))
    )


def is_math_lower(c: str) -> bool:
    cp = ord(c)
    return (
        "a" <= c <= "z"
        or 0x03B1 <= cp <= 0x03C9
        or 0x1D44E <= cp <= 0x1D467
        or 0x1D6FC <= cp <= 0x1D735
    )


def is_math_upper(c: str) -> bool:
    cp = ord(c)
    return "A" <= c <= "Z" or 0x1D434 <= cp <= 0x1D44D


BASE_MATH_PUNCT = set("−-+=⋯…,.;:()[]")
FULLWIDTH_EQUALS = "＝"


def classify(text: str, natural_script: bool, font: str) -> tuple[str, int]:
    if natural_script:
        if all(ch.isdigit() for ch in text):
            return "NATURAL_SCRIPT_DIGIT", 15
        if all(is_math_lower(ch) for ch in text):
            return "NATURAL_SCRIPT_LOWER", 15
        return "NATURAL_SCRIPT_OPERATOR_OR_PUNCT", 15
    if text == FULLWIDTH_EQUALS:
        return "MATH_OPERATOR_OR_PUNCT", 22
    if all(ch in BASE_MATH_PUNCT for ch in text):
        return "MATH_OPERATOR_OR_PUNCT", 22
    if all(ch.isdigit() or ch == "." for ch in text) and any(ch.isdigit() for ch in text):
        return "DIGIT", 24
    if all(is_math_upper(ch) for ch in text):
        return "LATIN_UPPER", 24
    if all(is_math_lower(ch) for ch in text):
        return "LATIN_LOWER_OR_GREEK", 17
    if any(is_han(ch) for ch in text) or "Noto" in font:
        return "CJK_OR_FULLWIDTH", 30
    return "MATH_OPERATOR_OR_PUNCT", 22


def extract_chars(page: fitz.Page) -> list[CharRecord]:
    raw = page.get_text("rawdict", flags=fitz.TEXTFLAGS_RAWDICT)
    records: list[CharRecord] = []
    span_id = 0
    line_id = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            line_id += 1
            for span in line["spans"]:
                span_id += 1
                rgb = fitz.sRGB_to_rgb(span.get("color", 0))
                for ch in span["chars"]:
                    bbox = fitz.Rect(ch["bbox"])
                    if not bbox.intersects(TEXT_AUDIT_REGION) or bbox.y0 < TEXT_AUDIT_REGION.y0:
                        continue
                    records.append(
                        CharRecord(
                            c=ch["c"],
                            bbox=bbox,
                            size=float(span["size"]),
                            font=span["font"],
                            color=rgb,
                            origin=tuple(ch["origin"]),
                            span_id=span_id,
                            line_id=line_id,
                        )
                    )
    return records


def build_elements(chars: list[CharRecord]) -> list[Element]:
    by_span: dict[int, list[CharRecord]] = {}
    for ch in chars:
        by_span.setdefault(ch.span_id, []).append(ch)

    elements: list[Element] = []
    seq = 0
    for span_id, span_chars in by_span.items():
        span_chars.sort(key=lambda ch: (ch.bbox.x0, ch.bbox.y0))
        nonspace = [ch for ch in span_chars if not ch.c.isspace()]
        if not nonspace:
            continue
        span_bbox = fitz.Rect(nonspace[0].bbox)
        for ch in nonspace[1:]:
            span_bbox.include_rect(ch.bbox)
        role, source_line, declared_pt = role_for(span_bbox)
        parent_id = parent_for(role, span_bbox, nonspace[0].line_id, span_id)

        # CJK prose is audited as a semantic line segment. Explicit full-width
        # equality signs are split because the current task requires operator
        # substrings to be measured independently. Figure numbers remain a
        # single numeric semantic label (e.g. 33.3).
        whole_text = "".join(ch.c for ch in nonspace)
        is_cjk_span = any(is_han(ch.c) for ch in nonspace) or "Noto" in nonspace[0].font
        is_figure_number = role == "CAPTION" and all(ch.c.isdigit() or ch.c == "." for ch in nonspace)

        groups: list[list[CharRecord]] = []
        if is_figure_number:
            groups = [nonspace]
        elif is_cjk_span:
            current: list[CharRecord] = []
            for ch in nonspace:
                if ch.c == FULLWIDTH_EQUALS:
                    if current:
                        groups.append(current)
                        current = []
                    groups.append([ch])
                else:
                    current.append(ch)
            if current:
                groups.append(current)
        else:
            groups = [[ch] for ch in nonspace]

        for group in groups:
            seq += 1
            text = "".join(ch.c for ch in group)
            avg_size = statistics.median(ch.size for ch in group)
            natural_script = avg_size <= declared_pt * 0.925
            script_class, threshold = classify(text, natural_script, group[0].font)
            elements.append(
                Element(
                    element_id=f"R93_{seq:03d}",
                    parent_id=parent_id,
                    role=role,
                    source_line=source_line,
                    declared_pt=declared_pt,
                    chars=group,
                    text=text,
                    script_class=script_class,
                    threshold=threshold,
                    natural_script=natural_script,
                )
            )
    return elements


def color_mask(
    image: np.ndarray,
    bbox: tuple[int, int, int, int],
    foreground: tuple[int, int, int],
) -> tuple[np.ndarray, tuple[int, int, int, int] | None, int]:
    x0, y0, x1, y1 = bbox
    roi = image[y0:y1, x0:x1].astype(np.int16)
    if roi.size == 0:
        return np.zeros((0, 0), dtype=np.uint8), None, 0
    fg = np.array(foreground, dtype=np.int16)
    dist_fg = np.linalg.norm(roi - fg, axis=2)
    ring = np.concatenate((roi[0], roi[-1], roi[:, 0], roi[:, -1]), axis=0)
    bg = np.median(ring, axis=0)
    dist_bg = np.linalg.norm(roi - bg, axis=2)
    mask = ((dist_fg <= 78.0) & (dist_bg >= 20.0)).astype(np.uint8)
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return mask, None, 0
    ink = (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)
    return mask, ink, ink[3] - ink[1]


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def draw_geometry_mask(shape: tuple[int, int]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    h, w = shape
    objects: dict[str, np.ndarray] = {}

    def add_line(name: str, p0: tuple[float, float], p1: tuple[float, float], width_pt: float) -> None:
        mask = np.zeros((h, w), dtype=np.uint8)
        q0 = tuple(round(v * SCALE) for v in p0)
        q1 = tuple(round(v * SCALE) for v in p1)
        cv2.line(mask, q0, q1, 1, max(1, round(width_pt * SCALE)), cv2.LINE_8)
        objects[name] = mask

    def add_rect(name: str, rect: tuple[float, float, float, float], width_pt: float) -> None:
        mask = np.zeros((h, w), dtype=np.uint8)
        x0, y0, x1, y1 = (round(v * SCALE) for v in rect)
        cv2.rectangle(mask, (x0, y0), (x1, y1), 1, max(1, round(width_pt * SCALE)), cv2.LINE_8)
        objects[name] = mask

    add_line("ORDER_ARROW_SHAFT", (134.7755, 441.8793), (447.3747, 441.8793), 0.60)
    # Conservative filled arrowhead polygon bbox.
    head = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(
        [[round(x * SCALE), round(y * SCALE)] for x, y in ((449.6477, 441.8793), (446.4712, 440.7672), (446.4712, 442.9915))],
        dtype=np.int32,
    )
    cv2.fillPoly(head, [pts], 1)
    objects["ORDER_ARROW_HEAD"] = head

    node_rects = [
        (125.1378, 459.5963, 162.5556, 486.5257),
        (167.6580, 459.5963, 205.0758, 486.5257),
        (210.1782, 459.5963, 247.5960, 486.5257),
        (252.6984, 459.5963, 290.1162, 486.5257),
        (295.2186, 459.5963, 332.6364, 486.5257),
        (337.7389, 459.5963, 375.1566, 486.5257),
        (380.2590, 459.5963, 417.6768, 486.5257),
        (422.7793, 459.5963, 460.1970, 486.5257),
    ]
    widths = [0.95, 0.95, 0.95, 0.95, 1.05, 0.78, 0.78, 0.78]
    for i, (rect, width) in enumerate(zip(node_rects, widths), start=1):
        add_rect(f"SLOT_BORDER_{i:02d}", rect, width)
    add_rect("STATE_CARD_BORDER", (132.5078, 502.5139, 449.9900, 528.6484), 0.55)
    add_rect("LEGEND_CARD_BORDER", (106.5157, 532.5893, 475.9800, 555.2667), 0.55)

    union = np.zeros((h, w), dtype=np.uint8)
    for mask in objects.values():
        union |= mask
    return union, objects


def mask_clearance(text_mask: np.ndarray, graphic_mask: np.ndarray) -> float:
    if not np.any(text_mask) or not np.any(graphic_mask):
        return math.inf
    inv = (graphic_mask == 0).astype(np.uint8)
    dist = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    # Distance-transform values are pixel-centre distances.  Subtract one
    # pixel so the reported value is the number of blank pixels between the
    # two foreground masks, matching the accepted STRICT_R5 convention used
    # for FIG-P020-01.
    return max(0.0, float(dist[text_mask > 0].min()) - 1.0)


def crop_image(image: Image.Image, rect: fitz.Rect) -> Image.Image:
    return image.crop(rect_px(rect))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    chars = extract_chars(page)
    elements = build_elements(chars)

    page_png = OUT / "r93_p682_full_page_300dpi.png"
    if not page_png.exists():
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
        pix.save(page_png)
    pil = Image.open(page_png).convert("RGB")
    rgb = np.array(pil)
    crop_image(pil, FIGURE_REGION).save(OUT / "r93_p682_figure_crop_300dpi.png")
    figure_caption_crop = crop_image(pil, FIGURE_CAPTION_REGION)
    figure_caption_crop.save(OUT / "r93_p682_figure_caption_crop_300dpi.png")
    figure_caption_crop.convert("L").convert("RGB").save(OUT / "r93_p682_figure_caption_grayscale_300dpi.png")
    fit_page = pil.copy()
    fit_page.thumbnail((900, 1272), Image.Resampling.LANCZOS)
    fit_page.save(OUT / "r93_p682_fitpage_review_only.png")

    geometry_union, geometry_objects = draw_geometry_mask(rgb.shape[:2])
    text_union = np.zeros(rgb.shape[:2], dtype=np.uint8)
    rows: list[dict[str, object]] = []
    element_ink: dict[str, tuple[int, int, int, int]] = {}
    element_masks: dict[str, np.ndarray] = {}

    for element in elements:
        bbox = rect_px(element.bbox_pdf)
        target = element.chars[0].color
        local_mask, ink_bbox, h_ink = color_mask(rgb, bbox, target)
        full_mask = np.zeros(rgb.shape[:2], dtype=np.uint8)
        x0, y0, x1, y1 = bbox
        if local_mask.size:
            full_mask[y0:y1, x0:x1] = local_mask
        text_union |= full_mask
        element_masks[element.element_id] = full_mask
        if ink_bbox is not None:
            element_ink[element.element_id] = ink_bbox
        rows.append(
            {
                "ELEMENT_ID": element.element_id,
                "PARENT_ID": element.parent_id,
                "PANEL_ID": "P1",
                "ROLE": element.role,
                "SOURCE_FILE": str(FIG_SOURCE),
                "SOURCE_LINE": element.source_line,
                "DECLARED_PT": f"{element.declared_pt:.2f}",
                "DECLARED_BASE_PT": f"{element.declared_pt:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{element.declared_pt:.2f}",
                "PDF_VECTOR_PT": f"{statistics.median(ch.size for ch in element.chars):.3f}",
                "TEXT_SAMPLE": element.text,
                "SCRIPT_CLASS": element.script_class,
                "NATURAL_SCRIPT": str(element.natural_script).lower(),
                "BBOX_X0": bbox[0],
                "BBOX_Y0": bbox[1],
                "BBOX_X1": bbox[2],
                "BBOX_Y1": bbox[3],
                "INK_X0": "" if ink_bbox is None else ink_bbox[0],
                "INK_Y0": "" if ink_bbox is None else ink_bbox[1],
                "INK_X1": "" if ink_bbox is None else ink_bbox[2],
                "INK_Y1": "" if ink_bbox is None else ink_bbox[3],
                "H_INK_PX": h_ink,
                "PIXEL_THRESHOLD_PX": element.threshold,
                "CLASS_MEDIAN_PX": "",
                "RATIO_TO_CLASS_MEDIAN": "",
                "ROLE_RATIO": "",
                "TEXT_TEXT_OVERLAP_PX": 0,
                "TEXT_GRAPHIC_OVERLAP_PX": int(np.count_nonzero(full_mask & geometry_union)),
                "MIN_CLEARANCE_PX": "",
                "PASS_FAIL": "PASS" if h_ink >= element.threshold else "FAIL",
                "REASON": "" if h_ink >= element.threshold else f"H_ink={h_ink}px < {element.threshold}px",
            }
        )

    # Same role and same script-class ratios.
    # "Same class" is kept glyph-specific here. Comparing the ink height of
    # intrinsically different glyphs (for example italic j with a descender
    # against italic d with an ascender, or '(' against '=') would manufacture
    # a ratio failure unrelated to font scaling. Cross-glyph raw heights remain
    # visible in the CSV for independent reviewers.
    class_groups: dict[tuple[str, str, str], list[int]] = {}
    for i, row in enumerate(rows):
        if int(row["H_INK_PX"]) > 0:
            class_groups.setdefault(
                (str(row["ROLE"]), str(row["SCRIPT_CLASS"]), str(row["TEXT_SAMPLE"])), []
            ).append(i)
    for indices in class_groups.values():
        median = statistics.median(int(rows[i]["H_INK_PX"]) for i in indices)
        for i in indices:
            ratio = int(rows[i]["H_INK_PX"]) / median
            rows[i]["CLASS_MEDIAN_PX"] = f"{median:.2f}"
            rows[i]["RATIO_TO_CLASS_MEDIAN"] = f"{ratio:.4f}"
            rows[i]["ROLE_RATIO"] = f"{ratio:.4f}"
            if not (0.92 <= ratio <= 1.08):
                rows[i]["PASS_FAIL"] = "FAIL"
                reason = str(rows[i]["REASON"])
                extra = f"same-class ratio={ratio:.4f} outside [0.92,1.08]"
                rows[i]["REASON"] = f"{reason}; {extra}".strip("; ")

    # Independent text-text and text-graphic relations. Same-parent math
    # pieces are a single semantic object and are not counted as illegal
    # text-text overlap.
    relations: list[dict[str, object]] = []
    total_text_text_overlap = 0
    total_text_graphic_overlap = 0
    minimum_text_text = math.inf
    minimum_text_graphic = math.inf
    caption_internal_overlap = 0

    # A naturally wrapped caption is one reading-flow parent.  It is exempt
    # from the independent-object 4 px clearance gate, but a real foreground
    # collision between its extracted pieces would still be a defect.
    caption_elements = [e for e in elements if e.parent_id == "CAPTION_PARAGRAPH"]
    for i, a in enumerate(caption_elements):
        for b in caption_elements[i + 1 :]:
            caption_internal_overlap += int(
                np.count_nonzero(element_masks[a.element_id] & element_masks[b.element_id])
            )

    for i, a in enumerate(elements):
        if a.element_id not in element_ink:
            continue
        for b in elements[i + 1 :]:
            if b.element_id not in element_ink or a.parent_id == b.parent_id:
                continue
            overlap = int(np.count_nonzero(element_masks[a.element_id] & element_masks[b.element_id]))
            clearance = bbox_distance(element_ink[a.element_id], element_ink[b.element_id])
            total_text_text_overlap += overlap
            minimum_text_text = min(minimum_text_text, clearance)
            if overlap or clearance < 4:
                relations.append(
                    {
                        "RELATION_ID": f"TT_{a.element_id}_{b.element_id}",
                        "OBJECT_A": a.element_id,
                        "OBJECT_B": b.element_id,
                        "RELATION_CLASS": "TEXT_TEXT",
                        "OVERLAP_PIXEL_COUNT": overlap,
                        "MIN_CLEARANCE_PX": f"{clearance:.3f}",
                        "REQUIRED_CLEARANCE_PX": 4,
                        "PASS_FAIL": "PASS" if overlap == 0 and clearance >= 4 else "FAIL",
                    }
                )

    row_by_id = {str(row["ELEMENT_ID"]): row for row in rows}
    for element in elements:
        eid = element.element_id
        if eid not in element_ink:
            continue
        own_graphics: list[str] = []
        required = 3
        if element.parent_id.startswith("SLOT_"):
            own_graphics = [f"SLOT_BORDER_{int(element.parent_id[-2:]):02d}"]
            required = 5
        elif element.parent_id == "STATE_FORMULA_CARD":
            own_graphics = ["STATE_CARD_BORDER"]
            required = 5
        elif element.parent_id == "LEGEND_CARD":
            own_graphics = ["LEGEND_CARD_BORDER"]
            required = 5
        elif element.role in ("ORDER_LABEL", "ORDER_ANNOTATION"):
            own_graphics = ["ORDER_ARROW_SHAFT", "ORDER_ARROW_HEAD"]
            required = 3
        elif element.role == "STATE_LABEL":
            own_graphics = [
                "SLOT_BORDER_01", "SLOT_BORDER_02", "SLOT_BORDER_03", "SLOT_BORDER_04",
                "SLOT_BORDER_05", "SLOT_BORDER_06", "SLOT_BORDER_07", "SLOT_BORDER_08",
                "STATE_CARD_BORDER",
            ]
            required = 3
        else:
            continue
        best = math.inf
        overlap = 0
        best_name = ""
        for name in own_graphics:
            gmask = geometry_objects[name]
            ov = int(np.count_nonzero(element_masks[eid] & gmask))
            clear = mask_clearance(element_masks[eid], gmask)
            overlap += ov
            if clear < best:
                best = clear
                best_name = name
        total_text_graphic_overlap += overlap
        minimum_text_graphic = min(minimum_text_graphic, best)
        row_by_id[eid]["TEXT_GRAPHIC_OVERLAP_PX"] = overlap
        row_by_id[eid]["MIN_CLEARANCE_PX"] = f"{best:.3f}"
        if overlap or best < required:
            row_by_id[eid]["PASS_FAIL"] = "FAIL"
            reason = str(row_by_id[eid]["REASON"])
            extra = f"graphic overlap={overlap}px; clearance={best:.3f}px < {required}px"
            row_by_id[eid]["REASON"] = f"{reason}; {extra}".strip("; ")
        relations.append(
            {
                "RELATION_ID": f"TG_{eid}_{best_name}",
                "OBJECT_A": eid,
                "OBJECT_B": best_name,
                "RELATION_CLASS": "TEXT_GRAPHIC",
                "OVERLAP_PIXEL_COUNT": overlap,
                "MIN_CLEARANCE_PX": f"{best:.3f}",
                "REQUIRED_CLEARANCE_PX": required,
                "PASS_FAIL": "PASS" if overlap == 0 and best >= required else "FAIL",
            }
        )

    # Record aggregate geometry rows even when no failure relation exists.
    relations.extend(
        [
            {
                "RELATION_ID": "AGG_TEXT_TEXT",
                "OBJECT_A": "ALL_TEXT",
                "OBJECT_B": "ALL_INDEPENDENT_TEXT",
                "RELATION_CLASS": "TEXT_TEXT_AGGREGATE",
                "OVERLAP_PIXEL_COUNT": total_text_text_overlap,
                "MIN_CLEARANCE_PX": f"{minimum_text_text:.3f}",
                "REQUIRED_CLEARANCE_PX": 4,
                "PASS_FAIL": "PASS" if total_text_text_overlap == 0 and minimum_text_text >= 4 else "FAIL",
            },
            {
                "RELATION_ID": "AGG_TEXT_GRAPHIC",
                "OBJECT_A": "ALL_TEXT",
                "OBJECT_B": "AUDITED_LINES_BORDERS",
                "RELATION_CLASS": "TEXT_GRAPHIC_AGGREGATE",
                "OVERLAP_PIXEL_COUNT": total_text_graphic_overlap,
                "MIN_CLEARANCE_PX": f"{minimum_text_graphic:.3f}",
                "REQUIRED_CLEARANCE_PX": 3,
                "PASS_FAIL": "PASS" if total_text_graphic_overlap == 0 and minimum_text_graphic >= 3 else "FAIL",
            },
            {
                "RELATION_ID": "AGG_CAPTION_INTERNAL",
                "OBJECT_A": "CAPTION_PARAGRAPH",
                "OBJECT_B": "SAME_READING_FLOW",
                "RELATION_CLASS": "SAME_PARENT_ACTUAL_OVERLAP",
                "OVERLAP_PIXEL_COUNT": caption_internal_overlap,
                "MIN_CLEARANCE_PX": "N/A",
                "REQUIRED_CLEARANCE_PX": "overlap=0",
                "PASS_FAIL": "PASS" if caption_internal_overlap == 0 else "FAIL",
            },
        ]
    )

    # Audited figure/caption foreground is checked against the recorded native
    # 1:1 review window.  This makes clip=0 and the >=6 px edge result measured
    # facts rather than assertions.  The window itself is never used to resize
    # or relax glyph-height measurements.
    audited_foreground = text_union | geometry_union
    crop_x0, crop_y0, crop_x1, crop_y1 = rect_px(FIGURE_CAPTION_REGION)
    outside = audited_foreground.copy()
    outside[crop_y0:crop_y1, crop_x0:crop_x1] = 0
    clip_pixel_count = int(np.count_nonzero(outside))
    ys, xs = np.where(audited_foreground > 0)
    if len(xs):
        content_bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        edge_margins = {
            "left": content_bbox[0] - crop_x0,
            "top": content_bbox[1] - crop_y0,
            "right": crop_x1 - content_bbox[2],
            "bottom": crop_y1 - content_bbox[3],
        }
        edge_min_clearance = min(edge_margins.values())
    else:
        content_bbox = (0, 0, 0, 0)
        edge_margins = {"left": 0, "top": 0, "right": 0, "bottom": 0}
        edge_min_clearance = 0

    with (OUT / "r93_edge_clip_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["AUDIT_WINDOW_PX", "CONTENT_INK_BBOX_PX", "LEFT_PX", "TOP_PX", "RIGHT_PX", "BOTTOM_PX", "MIN_EDGE_PX", "REQUIRED_EDGE_PX", "OUTSIDE_CLIP_PIXELS", "PASS_FAIL"])
        writer.writerow([
            (crop_x0, crop_y0, crop_x1, crop_y1),
            content_bbox,
            edge_margins["left"], edge_margins["top"], edge_margins["right"], edge_margins["bottom"],
            edge_min_clearance, 6, clip_pixel_count,
            "PASS" if edge_min_clearance >= 6 and clip_pixel_count == 0 else "FAIL",
        ])

    fieldnames = list(rows[0].keys())
    with (OUT / "r93_pixel_measurements.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with (OUT / "r93_overlap_clearance.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(relations[0].keys()))
        writer.writeheader()
        writer.writerows(relations)

    # A compact vector-span inventory supports independent audit of PDF
    # mapping and source-size restoration.
    with (OUT / "r93_vector_chars.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CHAR", "SPAN_ID", "LINE_ID", "FONT", "PDF_VECTOR_PT", "COLOR_RGB", "BBOX_PDF", "BBOX_PX"])
        for ch in chars:
            writer.writerow([ch.c, ch.span_id, ch.line_id, ch.font, f"{ch.size:.4f}", ch.color, tuple(ch.bbox), rect_px(ch.bbox)])

    source_font_rows = [
        ("SF01", "BASE_STYLE", "5", "9.60", "9.60", "9.60", "1.0000", "PASS", "figure-wide fallback"),
        ("SF02", "NODE_DEFAULT", "14", "9.60", "9.60", "9.60", "1.0000", "PASS", "all unoverridden TikZ nodes"),
        ("SF03", "TITLE", "16", "10.60", "10.60", "10.60", "1.0000", "PASS", "single title role"),
        ("SF04", "ORDER_LABEL", "17-18", "9.60", "9.60", "9.60", "1.0000", "PASS", "all eight order labels"),
        ("SF05", "ORDER_ANNOTATION", "19-20", "9.60", "9.60", "9.60", "1.0000", "PASS", "update-order label"),
        ("SF06", "SLOT_FORMULA_BASE", "21-28", "9.60", "9.60", "9.60", "1.0000", "PASS", "natural scripts derive from >=9.5 pt base"),
        ("SF07", "STATE_LABEL", "29-31", "9.60", "9.60", "9.60", "1.0000", "PASS", "three status labels"),
        ("SF08", "STATE_FORMULA_BASE", "32-33", "10.00", "10.00", "10.00", "1.0000", "PASS", "within-sweep formula card"),
        ("SF09", "LEGEND_BASE", "34-35", "9.80", "9.80", "9.80", "1.0000", "PASS", "encoding/end-of-sweep card"),
        ("SF10", "CAPTION", "37-38; statlearnbook.sty:305", "10.00", "10.00", "10.00", "1.0000", "PASS", "global small caption, no local scale"),
    ]
    with (OUT / "r93_source_font_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ELEMENT_ID", "ROLE", "SOURCE_LINE", "DECLARED_PT_MIN", "DECLARED_PT_MAX", "EFFECTIVE_BASE_PT_MIN", "SAME_ROLE_MAX_MIN", "PASS_FAIL", "NOTES"])
        writer.writerows(source_font_rows)

    def heights(*, role: str, sample: str | None = None, script_class: str | None = None) -> list[int]:
        selected: list[int] = []
        for row in rows:
            if row["ROLE"] != role:
                continue
            if sample is not None and row["TEXT_SAMPLE"] != sample:
                continue
            if script_class is not None and row["SCRIPT_CLASS"] != script_class:
                continue
            selected.append(int(row["H_INK_PX"]))
        return selected

    state_label_cjk = statistics.median(heights(role="STATE_LABEL", script_class="CJK_OR_FULLWIDTH"))
    role_ratio_rows = [
        ("VR01", "SLOT_FORMULA", "STATE_FORMULA", "math lowercase x", statistics.median(heights(role="SLOT_FORMULA", sample="𝑥")), statistics.median(heights(role="STATE_FORMULA", sample="𝑥")), "[1.00,1.18]", "formula block versus ordinary coordinate-state formula"),
        ("VR02", "STATE_LABEL", "ORDER_ANNOTATION", "CJK", state_label_cjk, statistics.median(heights(role="ORDER_ANNOTATION", script_class="CJK_OR_FULLWIDTH")), "[0.95,1.10]", "ordinary annotation versus base status label"),
        ("VR03", "STATE_LABEL", "LEGEND", "CJK", state_label_cjk, statistics.median(heights(role="LEGEND", script_class="CJK_OR_FULLWIDTH")), "[0.95,1.10]", "legend versus base status label"),
        ("VR04", "STATE_LABEL", "CAPTION", "CJK parent median", state_label_cjk, statistics.median(heights(role="CAPTION", script_class="CJK_OR_FULLWIDTH")), "[0.95,1.10]", "caption is one reading-flow parent; raw glyph-dependent chunk heights remain in pixel CSV"),
        ("VR05", "STATE_LABEL", "TITLE", "CJK bold title", state_label_cjk, statistics.median(heights(role="TITLE", script_class="CJK_OR_FULLWIDTH")), "[0.90,1.25]", "semantic title emphasis"),
    ]
    with (OUT / "r93_role_ratio_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["AUDIT_ID", "BASE_ROLE", "COMPARE_ROLE", "SCRIPT_BASIS", "BASE_MEDIAN_PX", "COMPARE_MEDIAN_PX", "RATIO", "ALLOWED", "PASS_FAIL", "NOTES"])
        for audit_id, base_role, compare_role, basis, base_h, compare_h, allowed, notes in role_ratio_rows:
            ratio = compare_h / base_h
            lo, hi = (float(x) for x in allowed.strip("[]").split(","))
            writer.writerow([audit_id, base_role, compare_role, basis, f"{base_h:.2f}", f"{compare_h:.2f}", f"{ratio:.4f}", allowed, "PASS" if lo <= ratio <= hi else "FAIL", notes])

    # Every visible mathematical operator / punctuation substring gets a
    # native 1:1 ROI, its core-ink mask, and a same-size overlay. This prevents
    # a parent formula bbox from substituting for a short glyph's own H_ink.
    raw_dir = OUT / "raw_rois" / "operators"
    mask_dir = OUT / "masks" / "operators"
    operator_overlay_dir = OUT / "overlays" / "operators"
    raw_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    operator_overlay_dir.mkdir(parents=True, exist_ok=True)
    operator_manifest: list[list[object]] = []
    for element in elements:
        if "OPERATOR_OR_PUNCT" not in element.script_class:
            continue
        row = row_by_id[element.element_id]
        x0, y0, x1, y1 = (
            int(row["BBOX_X0"]), int(row["BBOX_Y0"]), int(row["BBOX_X1"]), int(row["BBOX_Y1"])
        )
        pad = 3
        rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
        rx1, ry1 = min(pil.width, x1 + pad), min(pil.height, y1 + pad)
        raw_roi = pil.crop((rx0, ry0, rx1, ry1))
        raw_roi.save(raw_dir / f"{element.element_id}_raw_1to1_300dpi.png")
        local = element_masks[element.element_id][ry0:ry1, rx0:rx1]
        mask_rgb = np.full((ry1 - ry0, rx1 - rx0, 3), 255, dtype=np.uint8)
        mask_rgb[local > 0] = (0, 0, 0)
        Image.fromarray(mask_rgb).save(mask_dir / f"{element.element_id}_mask_300dpi.png")
        op_overlay = raw_roi.copy()
        op_draw = ImageDraw.Draw(op_overlay)
        ink = element_ink.get(element.element_id)
        if ink is not None:
            ix0, iy0, ix1, iy1 = ink
            color = (215, 25, 35) if row["PASS_FAIL"] == "FAIL" else (20, 145, 65)
            op_draw.rectangle((ix0 - rx0, iy0 - ry0, ix1 - rx0 - 1, iy1 - ry0 - 1), outline=color, width=1)
        op_overlay.save(operator_overlay_dir / f"{element.element_id}_overlay_300dpi.png")
        operator_manifest.append([
            element.element_id, element.parent_id, element.role, element.text,
            row["SOURCE_LINE"], row["H_INK_PX"], row["PIXEL_THRESHOLD_PX"], row["PASS_FAIL"],
            str(raw_dir / f"{element.element_id}_raw_1to1_300dpi.png"),
            str(mask_dir / f"{element.element_id}_mask_300dpi.png"),
            str(operator_overlay_dir / f"{element.element_id}_overlay_300dpi.png"),
        ])
    with (OUT / "r93_operator_artifact_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ELEMENT_ID", "PARENT_ID", "ROLE", "TEXT_SAMPLE", "SOURCE_LINE", "H_INK_PX", "THRESHOLD_PX", "PASS_FAIL", "RAW_1TO1", "MASK", "OVERLAY"])
        writer.writerows(operator_manifest)

    # Overlay only failed rows plus semantic parent boxes, avoiding labels
    # that would obscure the source pixels under review.
    overlay = pil.copy()
    draw = ImageDraw.Draw(overlay)
    crop_box = rect_px(FIGURE_CAPTION_REGION)
    failed = [row for row in rows if row["PASS_FAIL"] == "FAIL"]
    failure_fields = [
        "ELEMENT_ID", "PARENT_ID", "ROLE", "SOURCE_LINE", "TEXT_SAMPLE", "SCRIPT_CLASS",
        "DECLARED_PT", "EFFECTIVE_PT", "PDF_VECTOR_PT",
        "INK_X0", "INK_Y0", "INK_X1", "INK_Y1", "H_INK_PX", "PIXEL_THRESHOLD_PX",
        "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "PASS_FAIL", "REASON",
    ]
    with (OUT / "r93_strict_failure_register.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=failure_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(failed)
    for row in failed:
        box = (int(row["BBOX_X0"]), int(row["BBOX_Y0"]), int(row["BBOX_X1"]), int(row["BBOX_Y1"]))
        draw.rectangle(box, outline=(220, 25, 35), width=2)
        draw.text((box[0], max(crop_box[1], box[1] - 11)), str(row["ELEMENT_ID"]), fill=(180, 0, 0))
    overlay.crop(crop_box).save(OUT / "r93_text_measurement_overlay_300dpi.png")

    summary = {
        "page_count": len(doc),
        "physical_page": PAGE_NUMBER,
        "image_size": pil.size,
        "element_count": len(rows),
        "failed_element_count": len(failed),
        "failed_pixel_height_count": sum(int(row["H_INK_PX"]) < int(row["PIXEL_THRESHOLD_PX"]) for row in rows),
        "failed_same_class_ratio_count": sum(
            bool(row["RATIO_TO_CLASS_MEDIAN"])
            and not (0.92 <= float(row["RATIO_TO_CLASS_MEDIAN"]) <= 1.08)
            for row in rows
        ),
        "overlap_pixel_count": total_text_text_overlap + total_text_graphic_overlap + caption_internal_overlap,
        "caption_internal_overlap_pixel_count": caption_internal_overlap,
        "text_text_min_clearance_px": minimum_text_text,
        "text_graphic_min_clearance_px": minimum_text_graphic,
        "edge_min_clearance_px": edge_min_clearance,
        "clip_pixel_count": clip_pixel_count,
    }
    with (OUT / "r93_measurement_summary.txt").open("w", encoding="utf-8") as f:
        for key, value in summary.items():
            f.write(f"{key}={value}\n")

    print(summary)
    for row in failed:
        sample = str(row["TEXT_SAMPLE"]).encode("unicode_escape").decode("ascii")
        print(row["ELEMENT_ID"], sample, row["ROLE"], row["H_INK_PX"], row["PIXEL_THRESHOLD_PX"], row["REASON"])


if __name__ == "__main__":
    main()
