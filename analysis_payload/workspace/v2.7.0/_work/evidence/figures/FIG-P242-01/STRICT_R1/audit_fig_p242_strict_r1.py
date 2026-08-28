"""Read-only, reproducible SA1 audit for FIG-P242-01.

The script never writes outside its own STRICT_R1 evidence directory.  It reads
only the frozen official R91 PDF and the named figure source, measures the
official 300 dpi page render without resampling it, and creates the required
strict-audit evidence files.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import median

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r91_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第02册_基础监督学习方法\V2-C04\fig_v2_c04_tree_partition.tex")
PAGE_NUMBER = 261  # Physical page independently located in the frozen R91 PDF.
PAGE_INDEX = PAGE_NUMBER - 1
DPI = 300
RAW_PAGE = OUT / "official_page_0261_300dpi.png"


def _trace_text(trace: dict) -> str:
    return "".join(chr(ch[0]) for ch in trace["chars"])


def _bbox_union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _trace_near(traces: list[dict], text: str, x: float, y: float) -> dict:
    choices = [t for t in traces if _trace_text(t) == text]
    if not choices:
        raise KeyError(f"missing trace {text!r}")
    return min(
        choices,
        key=lambda t: abs(((t["bbox"][0] + t["bbox"][2]) / 2) - x)
        + abs(((t["bbox"][1] + t["bbox"][3]) / 2) - y),
    )


def _chars(trace: dict, indices: list[int]) -> list[tuple[float, float, float, float]]:
    return [tuple(trace["chars"][i][3]) for i in indices]


def _pdf_to_px(box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    return (
        math.floor(box[0] * sx),
        math.floor(box[1] * sy),
        math.ceil(box[2] * sx),
        math.ceil(box[3] * sy),
    )


def _clamp_box(box: tuple[int, int, int, int], w: int, h: int) -> tuple[int, int, int, int]:
    return max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3])


def _local_background(region: np.ndarray) -> np.ndarray:
    """Dominant un-inked RGB in a glyph box, robust to antialiasing."""
    quant = (region // 8).astype(np.uint8)
    keys = (quant[:, :, 0].astype(np.uint32) << 16) | (quant[:, :, 1].astype(np.uint32) << 8) | quant[:, :, 2].astype(np.uint32)
    vals, counts = np.unique(keys, return_counts=True)
    key = vals[int(np.argmax(counts))]
    selected = region[keys == key]
    return np.median(selected.astype(np.float32), axis=0)


def _foreground_mask(region: np.ndarray, text_rgb: np.ndarray) -> np.ndarray:
    """Retain original raster pixels lying on the text-colour blend trajectory.

    A text antialias pixel is a blend of the local background and the PDF text
    colour.  Projecting on that trajectory includes every pixel with at least
    20/255 foreground contrast, while rejecting differently coloured hatch and
    fill strokes inside the same glyph box.
    """
    bg = _local_background(region)
    delta = bg - text_rgb
    norm = float(np.linalg.norm(delta))
    if norm < 20.0:
        return np.zeros(region.shape[:2], dtype=bool)
    diff = bg[None, None, :] - region.astype(np.float32)
    alpha = (diff * delta[None, None, :]).sum(axis=2) / (norm * norm)
    residual = np.linalg.norm(diff - alpha[:, :, None] * delta[None, None, :], axis=2)
    return (alpha * norm >= 20.0) & (alpha <= 1.08) & (residual <= 18.0)


def _component_mask(arr: np.ndarray, char_boxes: list[tuple[float, float, float, float]], text_rgb: np.ndarray, sx: float, sy: float) -> np.ndarray:
    """Return a directly measured foreground mask limited to glyph boxes.

    All retained pixels satisfy the required 20/255 local-background contrast
    test.  Boxes are PDF text-trace glyph geometries and keep unrelated nearby
    graphics out of the text measurement; no interpolation or resizing occurs.
    """
    h, w = arr.shape[:2]
    out = np.zeros((h, w), dtype=bool)
    for b in char_boxes:
        x0, y0, x1, y1 = _clamp_box(_pdf_to_px(b, sx, sy), w, h)
        if x1 <= x0 or y1 <= y0:
            continue
        out[y0:y1, x0:x1] |= _foreground_mask(arr[y0:y1, x0:x1], text_rgb)
    return out


def _ink_height_px(arr: np.ndarray, char_boxes: list[tuple[float, float, float, float]], text_rgb: np.ndarray, text_dir: tuple[float, float], sx: float, sy: float) -> int:
    """Use the minimum constituent glyph height for a mixed element."""
    h, w = arr.shape[:2]
    heights: list[int] = []
    for b in char_boxes:
        x0, y0, x1, y1 = _clamp_box(_pdf_to_px(b, sx, sy), w, h)
        if x1 <= x0 or y1 <= y0:
            continue
        m = _foreground_mask(arr[y0:y1, x0:x1], text_rgb)
        ys, xs = np.where(m)
        if len(xs):
            # Height is measured perpendicular to the local baseline. This is
            # crucial for the rotated y-axis x_2 label; its vertical screen
            # extent is glyph width, not its ink height.
            nx, ny = -float(text_dir[1]), float(text_dir[0])
            projection = xs.astype(np.float32) * nx + ys.astype(np.float32) * ny
            heights.append(int(round(float(projection.max() - projection.min() + 1.0))))
    # An ELEMENT_ID is a semantic text token / line.  For homogeneous CJK
    # strings, use its actual rendered ink extent, not the minimum of a thin
    # one-stroke character such as “一”; mixed scripts were already split into
    # separate ELEMENT_IDs above.
    return max(heights) if heights else 0


def _mask_distance(mask_a: np.ndarray, mask_b: np.ndarray, box: tuple[int, int, int, int], pad: int = 260) -> tuple[int, float]:
    """Exact Euclidean distance between visible raster foreground masks locally."""
    h, w = mask_a.shape
    x0, y0, x1, y1 = _clamp_box((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad), w, h)
    aa = np.argwhere(mask_a[y0:y1, x0:x1])
    bb = np.argwhere(mask_b[y0:y1, x0:x1])
    if not len(aa) or not len(bb):
        return 0, float("inf")
    # If masks overlap, intersection is the governing hard metric.
    overlap = int(np.count_nonzero(mask_a[y0:y1, x0:x1] & mask_b[y0:y1, x0:x1]))
    best = float("inf")
    for start in range(0, len(aa), 64):
        part = aa[start:start + 64].astype(np.float32)
        d2 = ((part[:, None, :] - bb[None, :, :].astype(np.float32)) ** 2).sum(axis=2)
        best = min(best, float(np.sqrt(d2.min())))
        if best == 0.0:
            break
    return overlap, best


def _draw_line(draw: ImageDraw.ImageDraw, sx: float, sy: float, p0: tuple[float, float], p1: tuple[float, float], width_pt: float) -> None:
    width = max(1, int(math.ceil(width_pt * max(sx, sy))))
    draw.line((round(p0[0] * sx), round(p0[1] * sy), round(p1[0] * sx), round(p1[1] * sy)), fill=1, width=width)


def _draw_rect(draw: ImageDraw.ImageDraw, sx: float, sy: float, rect: tuple[float, float, float, float], width_pt: float) -> None:
    width = max(1, int(math.ceil(width_pt * max(sx, sy))))
    draw.rectangle(_pdf_to_px(rect, sx, sy), outline=1, width=width)


def _native_crop(image: Image.Image, box_pdf: tuple[float, float, float, float], sx: float, sy: float, dest: Path) -> tuple[int, int, int, int]:
    box = _pdf_to_px(box_pdf, sx, sy)
    image.crop(box).save(dest)
    return box


def main() -> None:
    if not RAW_PAGE.exists():
        raise FileNotFoundError(f"expected direct 300 dpi render: {RAW_PAGE}")
    if not PDF.exists() or not SOURCE.exists():
        raise FileNotFoundError("frozen candidate PDF or named source missing")

    page_img = Image.open(RAW_PAGE).convert("RGB")
    arr = np.asarray(page_img)
    h, w = arr.shape[:2]
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx, sy = w / page.rect.width, h / page.rect.height
    expected = DPI / 72.0
    if abs(sx - expected) > 0.02 or abs(sy - expected) > 0.02:
        raise RuntimeError(f"render scale is not a native {DPI} dpi PDF raster: {(sx, sy)}")

    traces = [t for t in page.get_texttrace() if 180 < t["bbox"][1] < 405]
    # Directly locate every relevant text trace from the official PDF page.
    left_title = _trace_near(traces, "决策树：条件与分支值", 172, 214)
    root = _trace_near(traces, "𝑥1≤2.4", 156, 236)
    left_r1 = _trace_near(traces, "𝑅1", 123, 283)
    node2 = _trace_near(traces, "𝑥2≤1.6", 189, 282)
    left_r2 = _trace_near(traces, "𝑅2", 156, 330)
    left_r3 = _trace_near(traces, "𝑅3", 221, 330)
    yes_top = _trace_near(traces, "是", 131, 258)
    no_top = _trace_near(traces, "否", 181, 258)
    yes_bottom = _trace_near(traces, "是", 164, 305)
    no_bottom = _trace_near(traces, "否", 214, 305)
    gold_cn = _trace_near(traces, "金色路径：", 131, 354)
    gold_x1 = _trace_near(traces, "𝑥", 157, 354)
    gold_sub1 = _trace_near(traces, "1", 162, 356)
    gold_gt = _trace_near(traces, ">2.4", 178, 354)
    gold_and = _trace_near(traces, "且", 196, 354)
    gold_x2 = _trace_near(traces, "𝑥", 205, 354)
    gold_sub2 = _trace_near(traces, "2", 210, 356)
    gold_leq = _trace_near(traces, "≤1.6", 226, 354)
    right_title = _trace_near(traces, "特征空间：同一轴对齐分裂", 411, 198)
    tick_x = _trace_near(traces, "2.4", 446, 354)
    tick_y = _trace_near(traces, "1.6", 326, 273)
    region_r1 = _trace_near(traces, "𝑅", 391, 276)
    region_s1 = _trace_near(traces, "1", 396, 279)
    region_r2 = _trace_near(traces, "𝑅", 479, 307)
    region_s2 = _trace_near(traces, "2", 483, 310)
    region_r3 = _trace_near(traces, "𝑅", 479, 241)
    region_s3 = _trace_near(traces, "3", 483, 244)
    axis_x = _trace_near(traces, "𝑥", 425, 366)
    axis_s1 = _trace_near(traces, "1", 431, 369)
    axis_y = _trace_near(traces, "𝑥", 308, 279)
    axis_s2 = _trace_near(traces, "2", 311, 274)
    cap_cn = _trace_near(traces, "图", 138, 386)
    cap_num = _trace_near(traces, "15.1", 154, 386)
    cap_body = _trace_near(traces, "决策树中的每条根到叶路径对应特征空间中的一个轴对齐区域。", 312, 386)

    # Manual semantic inventory reflects source elements rather than arbitrary OCR chunks.
    entries: list[dict] = []

    def add(eid: str, panel: str, role: str, line: str, source_decl: str, trace: dict,
            indices: list[int], text: str, script: str, threshold: int, class_key: str,
            semantic_group: str, font_required: bool = True, role_kind: str = "normal") -> None:
        chars = _chars(trace, indices)
        b = _bbox_union(chars)
        pdf_size = float(trace["size"])
        effective_pt = pdf_size * 72.27 / 72.0
        entries.append({
            "ELEMENT_ID": eid, "PANEL_ID": panel, "ROLE": role, "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": line, "DECLARED_PT": source_decl, "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": effective_pt, "PDF_TRACE_PT": pdf_size, "TEXT_SAMPLE": text,
            "SCRIPT_CLASS": script, "THRESHOLD_PX": threshold, "CLASS_KEY": class_key,
            "SEMANTIC_GROUP": semantic_group, "FONT_REQUIRED": font_required, "ROLE_KIND": role_kind,
            "bbox_pdf": b, "char_boxes": chars, "TEXT_RGB": np.array(trace["color"], dtype=np.float32) * 255.0, "TEXT_DIR": tuple(trace["dir"]),
        })

    # Left tree panel: split formula bases, operators, numerals and scripts so no small substring is hidden.
    add("E01", "L", "panel_title", "3,30", "10.5", left_title, [0, 1, 2, 4, 5, 6, 7, 8, 9], "决策树条件与分支值", "CJK", 30, "PANEL_TITLE_CJK", "L_TITLE", role_kind="panel_title")
    add("E02", "L", "node_formula_base", "16-19,34-35", "\\footnotesize (resolved 9.30)", root, [0], "x", "LATIN_LOWER", 17, "TREE_FORMULA_LOWER", "L_ROOT")
    add("E03", "L", "node_formula_script", "34-35", "natural script from \\footnotesize", root, [1], "1", "NATURAL_SUBSCRIPT", 15, "TREE_NODE_SCRIPT", "L_ROOT", font_required=False, role_kind="script")
    add("E04", "L", "node_formula_operator", "34-35", "\\footnotesize (resolved 9.30)", root, [2], "≤", "MATH_OPERATOR", 22, "TREE_FORMULA_OPERATOR", "L_ROOT")
    add("E05", "L", "node_formula_number", "34-35", "\\footnotesize (resolved 9.30)", root, [3, 5], "2.4", "DIGIT", 24, "TREE_FORMULA_NUMBER", "L_ROOT")
    add("E06", "L", "branch_label", "36", "9.2", yes_top, [0], "是", "CJK", 30, "TREE_BRANCH_CJK", "L_YES_TOP", role_kind="annotation")
    add("E07", "L", "branch_label", "38", "9.2", no_top, [0], "否", "CJK", 30, "TREE_BRANCH_CJK", "L_NO_TOP", role_kind="annotation")
    add("E08", "L", "leaf_region_base", "35-36", "\\footnotesize (resolved 9.30)", left_r1, [0], "R", "LATIN_UPPER", 24, "TREE_LEAF_BASE", "L_LEAF_R1")
    add("E09", "L", "leaf_region_subscript", "35-36", "natural lowered glyph (trace 9.30)", left_r1, [1], "1", "NATURAL_SUBSCRIPT", 15, "TREE_LEAF_SCRIPT", "L_LEAF_R1", font_required=False, role_kind="script")
    add("E10", "L", "node_formula_base", "16-19,34,37", "\\footnotesize (resolved 9.30)", node2, [0], "x", "LATIN_LOWER", 17, "TREE_FORMULA_LOWER", "L_NODE2")
    add("E11", "L", "node_formula_script", "34,37", "natural lowered glyph (trace 9.30)", node2, [1], "2", "NATURAL_SUBSCRIPT", 15, "TREE_NODE_SCRIPT", "L_NODE2", font_required=False, role_kind="script")
    # get_texttrace omits the inter-token space that rawdict exposes, hence ≤ is index 2 here.
    add("E12", "L", "node_formula_operator", "34,37", "\\footnotesize (resolved 9.30)", node2, [2], "≤", "MATH_OPERATOR", 22, "TREE_FORMULA_OPERATOR", "L_NODE2")
    add("E13", "L", "node_formula_number", "34,37", "\\footnotesize (resolved 9.30)", node2, [3, 5], "1.6", "DIGIT", 24, "TREE_FORMULA_NUMBER", "L_NODE2")
    add("E14", "L", "branch_label", "41", "9.2", yes_bottom, [0], "是", "CJK", 30, "TREE_BRANCH_CJK", "L_YES_BOTTOM", role_kind="annotation")
    add("E15", "L", "branch_label", "42", "9.2", no_bottom, [0], "否", "CJK", 30, "TREE_BRANCH_CJK", "L_NO_BOTTOM", role_kind="annotation")
    add("E16", "L", "leaf_region_base", "39", "\\footnotesize (resolved 9.30)", left_r2, [0], "R", "LATIN_UPPER", 24, "TREE_LEAF_BASE", "L_LEAF_R2")
    add("E17", "L", "leaf_region_subscript", "39", "natural lowered glyph (trace 9.30)", left_r2, [1], "2", "NATURAL_SUBSCRIPT", 15, "TREE_LEAF_SCRIPT", "L_LEAF_R2", font_required=False, role_kind="script")
    add("E18", "L", "leaf_region_base", "42", "\\footnotesize (resolved 9.30)", left_r3, [0], "R", "LATIN_UPPER", 24, "TREE_LEAF_BASE", "L_LEAF_R3")
    add("E19", "L", "leaf_region_subscript", "42", "natural lowered glyph (trace 9.30)", left_r3, [1], "3", "NATURAL_SUBSCRIPT", 15, "TREE_LEAF_SCRIPT", "L_LEAF_R3", font_required=False, role_kind="script")
    # The terminal full-width colon is punctuation, not the information-bearing CJK glyph measurement.
    add("E20", "L", "path_annotation", "47-48", "9.2", gold_cn, [0, 1, 2, 3], "金色路径", "CJK", 30, "TREE_PATH_CJK", "L_GOLD_PATH", role_kind="annotation")
    add("E21", "L", "path_formula_base", "47-48", "9.2", gold_x1, [0], "x", "LATIN_LOWER", 17, "TREE_FORMULA_LOWER", "L_GOLD_PATH")
    add("E22", "L", "path_formula_script", "47-48", "natural script from 9.2 base", gold_sub1, [0], "1", "NATURAL_SUBSCRIPT", 15, "TREE_FORMULA_SCRIPT", "L_GOLD_PATH", font_required=False, role_kind="script")
    add("E23", "L", "path_formula_operator", "47-48", "9.2", gold_gt, [0], ">", "MATH_OPERATOR", 22, "TREE_FORMULA_OPERATOR", "L_GOLD_PATH")
    add("E24", "L", "path_formula_number", "47-48", "9.2", gold_gt, [1, 3], "2.4", "DIGIT", 24, "TREE_FORMULA_NUMBER", "L_GOLD_PATH")
    add("E25", "L", "path_annotation", "47-48", "9.2", gold_and, [0], "且", "CJK", 30, "TREE_PATH_CJK", "L_GOLD_PATH", role_kind="annotation")
    add("E26", "L", "path_formula_base", "47-48", "9.2", gold_x2, [0], "x", "LATIN_LOWER", 17, "TREE_FORMULA_LOWER", "L_GOLD_PATH")
    add("E27", "L", "path_formula_script", "47-48", "natural script from 9.2 base", gold_sub2, [0], "2", "NATURAL_SUBSCRIPT", 15, "TREE_FORMULA_SCRIPT", "L_GOLD_PATH", font_required=False, role_kind="script")
    add("E28", "L", "path_formula_operator", "47-48", "9.2", gold_leq, [0], "≤", "MATH_OPERATOR", 22, "TREE_FORMULA_OPERATOR", "L_GOLD_PATH")
    add("E29", "L", "path_formula_number", "47-48", "9.2", gold_leq, [1, 3], "1.6", "DIGIT", 24, "TREE_FORMULA_NUMBER", "L_GOLD_PATH")

    # Right axis-aligned-region panel.
    add("E30", "R", "panel_title", "3,52", "10.5", right_title, [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11], "特征空间同一轴对齐分裂", "CJK", 30, "PANEL_TITLE_CJK", "R_TITLE", role_kind="panel_title")
    add("E31", "R", "axis_tick", "22-25,54-58", "8.7", tick_x, [0, 2], "2.4", "DIGIT", 24, "AXIS_TICK_NUMERIC", "R_TICK_X", role_kind="base")
    add("E32", "R", "axis_tick", "22-25,54-58", "8.7", tick_y, [0, 2], "1.6", "DIGIT", 24, "AXIS_TICK_NUMERIC", "R_TICK_Y", role_kind="base")
    add("E33", "R", "region_label_base", "13,66", "9.5", region_r1, [0], "R", "LATIN_UPPER", 24, "REGION_LABEL_BASE", "R_REGION_R1", role_kind="annotation")
    add("E34", "R", "region_label_script", "13,66", "natural script from 9.5 base", region_s1, [0], "1", "NATURAL_SUBSCRIPT", 15, "REGION_LABEL_SCRIPT", "R_REGION_R1", font_required=False, role_kind="script")
    add("E35", "R", "region_label_base", "13,67", "9.5", region_r2, [0], "R", "LATIN_UPPER", 24, "REGION_LABEL_BASE", "R_REGION_R2", role_kind="annotation")
    add("E36", "R", "region_label_script", "13,67", "natural script from 9.5 base", region_s2, [0], "2", "NATURAL_SUBSCRIPT", 15, "REGION_LABEL_SCRIPT", "R_REGION_R2", font_required=False, role_kind="script")
    add("E37", "R", "region_label_base", "13,68", "9.5", region_r3, [0], "R", "LATIN_UPPER", 24, "REGION_LABEL_BASE", "R_REGION_R3", role_kind="annotation")
    add("E38", "R", "region_label_script", "13,68", "natural script from 9.5 base", region_s3, [0], "3", "NATURAL_SUBSCRIPT", 15, "REGION_LABEL_SCRIPT", "R_REGION_R3", font_required=False, role_kind="script")
    add("E39", "R", "axis_label_base", "22-25,54-58", "source 9.5; final trace resolves 10.00", axis_x, [0], "x", "LATIN_LOWER", 17, "AXIS_LABEL_BASE", "R_AXIS_X", role_kind="axis_label")
    add("E40", "R", "axis_label_script", "22-25,54-58", "natural script from final 10.00 base", axis_s1, [0], "1", "NATURAL_SUBSCRIPT", 15, "AXIS_LABEL_SCRIPT", "R_AXIS_X", font_required=False, role_kind="script")
    add("E41", "R", "axis_label_base", "22-25,54-58", "source 9.5; final trace resolves 10.00", axis_y, [0], "x", "LATIN_LOWER", 17, "AXIS_LABEL_BASE", "R_AXIS_Y", role_kind="axis_label")
    add("E42", "R", "axis_label_script", "22-25,54-58", "natural script from final 10.00 base", axis_s2, [0], "2", "NATURAL_SUBSCRIPT", 15, "AXIS_LABEL_SCRIPT", "R_AXIS_Y", font_required=False, role_kind="script")

    # Associated caption is audited separately so its larger CJK glyphs cannot hide any smaller numbers.
    add("E43", "CAP", "caption_prefix", "72", "global caption style (final 10.00)", cap_cn, [0], "图", "CJK", 30, "CAPTION_PREFIX_CJK", "CAPTION", role_kind="caption")
    add("E44", "CAP", "caption_number", "72", "global caption style (final 10.00)", cap_num, [0, 1, 3], "15.1", "DIGIT", 24, "CAPTION_NUMBER", "CAPTION", role_kind="caption")
    # Do not treat the terminal ideographic full stop as a full-height CJK glyph.
    add("E45", "CAP", "caption_body", "72", "global caption style (final 10.00)", cap_body, list(range(27)), "决策树中的每条根到叶路径对应特征空间中的一个轴对齐区域", "CJK", 30, "CAPTION_BODY_CJK", "CAPTION", role_kind="caption")

    # First-pass direct pixel measurements and semantic text masks.
    text_union = np.zeros((h, w), dtype=bool)
    for e in entries:
        e["BBOX_PX"] = _pdf_to_px(e["bbox_pdf"], sx, sy)
        e["TEXT_MASK"] = _component_mask(arr, e["char_boxes"], e["TEXT_RGB"], sx, sy)
        e["H_INK_PX"] = _ink_height_px(arr, e["char_boxes"], e["TEXT_RGB"], e["TEXT_DIR"], sx, sy)
        text_union |= e["TEXT_MASK"]

    # Build vector masks only for semantic lines/arrows/borders; hatch/fill patterns are background per 9.2.1-F.
    vector_img = Image.new("1", (w, h), 0)
    vd = ImageDraw.Draw(vector_img)
    graphics: list[dict] = []
    graphic_masks: dict[str, np.ndarray] = {}

    def gline(gid: str, role: str, src: str, p0: tuple[float, float], p1: tuple[float, float], width_pt: float) -> None:
        _draw_line(vd, sx, sy, p0, p1, width_pt)
        single = Image.new("1", (w, h), 0)
        _draw_line(ImageDraw.Draw(single), sx, sy, p0, p1, width_pt)
        graphic_masks[gid] = np.asarray(single, dtype=bool)
        graphics.append({"ELEMENT_ID": gid, "TYPE": role, "SOURCE_LINE": src, "BBOX_PDF": _bbox_union([(p0[0], p0[1], p0[0], p0[1]), (p1[0], p1[1], p1[0], p1[1])]), "WIDTH_PT": width_pt})

    def grect(gid: str, role: str, src: str, box: tuple[float, float, float, float], width_pt: float) -> None:
        _draw_rect(vd, sx, sy, box, width_pt)
        single = Image.new("1", (w, h), 0)
        _draw_rect(ImageDraw.Draw(single), sx, sy, box, width_pt)
        graphic_masks[gid] = np.asarray(single, dtype=bool)
        graphics.append({"ELEMENT_ID": gid, "TYPE": role, "SOURCE_LINE": src, "BBOX_PDF": box, "WIDTH_PT": width_pt})

    # Coordinates are read from the R91 PDF vector drawing list, not reconstructed from a scaled preview.
    grect("G01", "NODE_BORDER", "16-19,34-35", (132.04, 223.60, 180.23, 244.15), .80)
    grect("G02", "NODE_BORDER", "16-19,34-36", (99.17, 270.46, 147.35, 291.01), .80)
    grect("G03", "NODE_BORDER", "16-19,34,37", (164.92, 270.46, 213.10, 291.01), .80)
    grect("G04", "NODE_BORDER", "16-19,34,39", (132.04, 317.32, 180.23, 337.87), .80)
    grect("G05", "NODE_BORDER", "16-19,34,42", (197.79, 317.32, 245.98, 337.87), .80)
    gline("G06", "LINE_ARROW", "19,36", (132.44, 244.55), (148.65, 267.65), .82)
    gline("G07", "LINE_ARROW", "7,37", (163.62, 244.55), (179.68, 267.43), 1.02)
    gline("G08", "LINE_ARROW", "7,39-41", (165.29, 291.41), (181.52, 314.54), 1.02)
    gline("G09", "LINE_ARROW", "19,42", (196.50, 291.41), (212.53, 314.26), .82)
    grect("G10", "PANEL_BORDER", "22-25,54-58", (340.31, 210.81, 515.90, 342.50), .55)
    gline("G11", "LINE", "10,63", (445.66, 210.81), (445.66, 342.50), .82)
    gline("G12", "LINE", "11,64", (445.66, 272.26), (515.89, 272.26), .78)
    grect("G13", "LINE", "12,65", (445.66, 272.26, 515.90, 342.50), 1.02)
    gline("G14", "TICK", "23-25,58", (445.66, 342.50), (445.66, 346.75), .52)
    gline("G15", "TICK", "23-25,58", (336.06, 272.26), (340.31, 272.26), .52)
    vector_mask = np.asarray(vector_img, dtype=bool)

    # Direct text-to-vector test.  Formula parts share a semantic group and are therefore excluded from TEXT-TEXT tests.
    min_text_graphic = float("inf")
    text_graphic_pairs: list[dict] = []
    for e in entries:
        ov, dist = _mask_distance(e["TEXT_MASK"], vector_mask, e["BBOX_PX"])
        e["TEXT_GRAPHIC_OVERLAP_PX"] = ov
        e["MIN_GRAPHIC_CLEARANCE_PX"] = dist
        min_text_graphic = min(min_text_graphic, dist)
        for gid, gmask in graphic_masks.items():
            pov, pdist = _mask_distance(e["TEXT_MASK"], gmask, e["BBOX_PX"])
            if pov or pdist < 12.0:
                g = next(item for item in graphics if item["ELEMENT_ID"] == gid)
                text_graphic_pairs.append({
                    "ELEMENT_ID": e["ELEMENT_ID"], "ELEMENT_SOURCE_LINE": e["SOURCE_LINE"], "ELEMENT_BBOX_PX": e["BBOX_PX"],
                    "GRAPHIC_ID": gid, "GRAPHIC_SOURCE_LINE": g["SOURCE_LINE"], "GRAPHIC_BBOX_PX": _pdf_to_px(g["BBOX_PDF"], sx, sy),
                    "OVERLAP_PIXEL_COUNT": pov, "MIN_CLEARANCE_PX": pdist,
                })
    # Union count prevents a shared vector endpoint from being double-counted.
    total_tg_overlap = int(np.count_nonzero(text_union & vector_mask))

    # One 1:1 raw crop and one semantic intersection mask for every non-zero
    # text-to-vector collision: these are the audit's direct repair targets.
    entry_by_id = {e["ELEMENT_ID"]: e for e in entries}
    for detail in (p for p in text_graphic_pairs if p["OVERLAP_PIXEL_COUNT"] > 0):
        e = entry_by_id[detail["ELEMENT_ID"]]
        gmask = graphic_masks[detail["GRAPHIC_ID"]]
        ax0, ay0, ax1, ay1 = detail["ELEMENT_BBOX_PX"]
        bx0, by0, bx1, by1 = detail["GRAPHIC_BBOX_PX"]
        roi = _clamp_box((min(ax0, bx0) - 30, min(ay0, by0) - 30, max(ax1, bx1) + 30, max(ay1, by1) + 30), w, h)
        stem = f"{detail['ELEMENT_ID']}_{detail['GRAPHIC_ID']}"
        page_img.crop(roi).save(OUT / f"roi_overlap_{stem}_1to1_300dpi.png")
        visual = np.full((h, w, 3), 255, dtype=np.uint8)
        visual[gmask] = (0, 130, 210)
        visual[e["TEXT_MASK"]] = (210, 36, 36)
        visual[gmask & e["TEXT_MASK"]] = (172, 0, 172)
        Image.fromarray(visual, "RGB").crop(roi).save(OUT / f"semantic_mask_overlap_{stem}_300dpi.png")

    min_text_text = float("inf")
    total_tt_overlap = 0
    closest_tt = ("", "")
    for i, a in enumerate(entries):
        for b in entries[i + 1:]:
            if a["SEMANTIC_GROUP"] == b["SEMANTIC_GROUP"]:
                continue
            # Captions are a single associated sentence: prefix / number / body are not independent collision targets.
            if a["PANEL_ID"] == "CAP" and b["PANEL_ID"] == "CAP":
                continue
            ax0, ay0, ax1, ay1 = a["BBOX_PX"]
            bx0, by0, bx1, by1 = b["BBOX_PX"]
            union_box = (min(ax0, bx0), min(ay0, by0), max(ax1, bx1), max(ay1, by1))
            ov, dist = _mask_distance(a["TEXT_MASK"], b["TEXT_MASK"], union_box, pad=32)
            total_tt_overlap += ov
            if dist < min_text_text:
                min_text_text = dist
                closest_tt = (a["ELEMENT_ID"], b["ELEMENT_ID"])
    if not math.isfinite(min_text_text):
        min_text_text = float("nan")

    # Pixel-height and same-class statistics.
    class_values: dict[str, list[int]] = {}
    for e in entries:
        class_values.setdefault(e["CLASS_KEY"], []).append(e["H_INK_PX"])
    class_medians = {k: median(v) for k, v in class_values.items()}
    class_spreads = {k: max(v) / min(v) if min(v) else float("inf") for k, v in class_values.items()}
    for e in entries:
        cm = class_medians[e["CLASS_KEY"]]
        e["CLASS_MEDIAN_PX"] = cm
        e["RATIO_TO_CLASS_MEDIAN"] = e["H_INK_PX"] / cm if cm else float("inf")
        e["SAME_CLASS_PASS"] = .92 <= e["RATIO_TO_CLASS_MEDIAN"] <= 1.08 and class_spreads[e["CLASS_KEY"]] <= 1.08

    # Role hierarchy uses source-resolved final effective sizes so script morphology does not distort CJK-vs-math hierarchy.
    left_base_pt = median([e["EFFECTIVE_PT"] for e in entries if e["ELEMENT_ID"] in {"E02", "E04", "E05", "E10", "E12", "E13", "E21", "E23", "E24", "E26", "E28", "E29"}])
    right_base_pt = median([e["EFFECTIVE_PT"] for e in entries if e["ELEMENT_ID"] in {"E31", "E32"}])
    for e in entries:
        if e["ROLE_KIND"] == "script" or e["PANEL_ID"] == "CAP":
            e["ROLE_RATIO"] = float("nan")
            e["ROLE_PASS"] = True
        elif e["PANEL_ID"] == "L":
            e["ROLE_RATIO"] = e["EFFECTIVE_PT"] / left_base_pt
            if e["ROLE_KIND"] == "panel_title":
                e["ROLE_PASS"] = 1.05 <= e["ROLE_RATIO"] <= 1.20
            elif e["ROLE_KIND"] == "annotation":
                e["ROLE_PASS"] = .95 <= e["ROLE_RATIO"] <= 1.10
            else:
                e["ROLE_PASS"] = .90 <= e["ROLE_RATIO"] <= 1.18
        else:
            e["ROLE_RATIO"] = e["EFFECTIVE_PT"] / right_base_pt
            if e["ROLE_KIND"] == "panel_title":
                e["ROLE_PASS"] = 1.05 <= e["ROLE_RATIO"] <= 1.20
            elif e["ROLE_KIND"] == "axis_label":
                e["ROLE_PASS"] = 1.00 <= e["ROLE_RATIO"] <= 1.18
            elif e["ROLE_KIND"] == "annotation":
                e["ROLE_PASS"] = .95 <= e["ROLE_RATIO"] <= 1.10
            else:
                e["ROLE_PASS"] = .90 <= e["ROLE_RATIO"] <= 1.18

        e["FONT_PASS"] = (not e["FONT_REQUIRED"]) or e["EFFECTIVE_PT"] >= 9.5
        e["PIXEL_PASS"] = e["H_INK_PX"] >= e["THRESHOLD_PX"]
        e["TEXT_TEXT_OVERLAP_PX"] = 0  # Pair table below is the authoritative per-pair count.
        e["MIN_CLEARANCE_PX"] = e["MIN_GRAPHIC_CLEARANCE_PX"]
        e["PASS_FAIL"] = "PASS" if all([e["FONT_PASS"], e["PIXEL_PASS"], e["SAME_CLASS_PASS"], e["ROLE_PASS"], e["TEXT_GRAPHIC_OVERLAP_PX"] == 0]) else "FAIL"
        reasons = []
        if not e["FONT_PASS"]:
            reasons.append(f"effective_pt={e['EFFECTIVE_PT']:.2f}<9.50")
        if not e["PIXEL_PASS"]:
            reasons.append(f"H_ink={e['H_INK_PX']}<{e['THRESHOLD_PX']}")
        if not e["SAME_CLASS_PASS"]:
            reasons.append(f"class ratio={e['RATIO_TO_CLASS_MEDIAN']:.3f}")
        if not e["ROLE_PASS"]:
            reasons.append(f"role ratio={e['ROLE_RATIO']:.3f}")
        if e["TEXT_GRAPHIC_OVERLAP_PX"]:
            reasons.append(f"text-graphic overlap={e['TEXT_GRAPHIC_OVERLAP_PX']}")
        e["REASON"] = "; ".join(reasons) if reasons else "all measured element gates pass"

    # Native, non-resampled artefacts. Figure crop retains caption; standalone view means figure-only native crop.
    figure_pdf = (88.0, 177.0, 526.0, 402.0)
    standalone_pdf = (91.0, 179.0, 524.0, 376.0)
    fig_crop_px = _native_crop(page_img, figure_pdf, sx, sy, OUT / "figure_crop_300dpi.png")
    _native_crop(page_img, standalone_pdf, sx, sy, OUT / "standalone_figure_only_300dpi.png")
    ImageOps.grayscale(page_img.crop(fig_crop_px)).save(OUT / "figure_grayscale_300dpi.png")
    _native_crop(page_img, (96.0, 216.0, 250.0, 366.0), sx, sy, OUT / "roi_left_tree_1to1_300dpi.png")
    _native_crop(page_img, (295.0, 202.0, 523.0, 377.0), sx, sy, OUT / "roi_right_partition_1to1_300dpi.png")
    _native_crop(page_img, (145.0, 238.0, 195.0, 273.0), sx, sy, OUT / "roi_top_no_arrow_1to1_300dpi.png")
    _native_crop(page_img, (150.0, 286.0, 225.0, 319.0), sx, sy, OUT / "roi_bottom_no_arrow_1to1_300dpi.png")
    _native_crop(page_img, (296.0, 257.0, 456.0, 379.0), sx, sy, OUT / "roi_ticks_labels_1to1_300dpi.png")

    # Semantic masks and transparent-free visual overlay, all at the original 300 dpi pixel grid.
    text_mask_img = Image.fromarray(np.where(text_union, 0, 255).astype(np.uint8), "L")
    text_mask_img.crop(fig_crop_px).save(OUT / "semantic_mask_text_300dpi.png")
    vector_mask_img = Image.fromarray(np.where(vector_mask, 0, 255).astype(np.uint8), "L")
    vector_mask_img.crop(fig_crop_px).save(OUT / "semantic_mask_line_arrow_border_300dpi.png")
    color_mask = np.full((h, w, 3), 255, dtype=np.uint8)
    color_mask[vector_mask] = (0, 141, 180)
    color_mask[text_union] = (196, 34, 34)
    Image.fromarray(color_mask, "RGB").crop(fig_crop_px).save(OUT / "semantic_mask_colored_300dpi.png")

    overlay = page_img.copy()
    od = ImageDraw.Draw(overlay)
    for e in entries:
        b = e["BBOX_PX"]
        color = (210, 30, 30) if e["PASS_FAIL"] == "FAIL" else (25, 150, 55)
        od.rectangle(b, outline=color, width=2)
        od.text((b[0], max(0, b[1] - 12)), e["ELEMENT_ID"], fill=color)
    overlay.crop(fig_crop_px).save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Required CSVs.
    font_fields = ["ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_TRACE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "FONT_REQUIRED", "FONT_PASS", "REASON"]
    with (OUT / "after_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wri = csv.DictWriter(f, fieldnames=font_fields)
        wri.writeheader()
        for e in entries:
            row = {k: e[k] for k in font_fields}
            row["EFFECTIVE_PT"] = f"{row['EFFECTIVE_PT']:.2f}"
            row["PDF_TRACE_PT"] = f"{row['PDF_TRACE_PT']:.2f}"
            wri.writerow(row)

    pixel_fields = ["ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON"]
    with (OUT / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wri = csv.DictWriter(f, fieldnames=pixel_fields)
        wri.writeheader()
        for e in entries:
            b = e["BBOX_PX"]
            row = {
                "ELEMENT_ID": e["ELEMENT_ID"], "PANEL_ID": e["PANEL_ID"], "ROLE": e["ROLE"], "SOURCE_FILE": e["SOURCE_FILE"], "SOURCE_LINE": e["SOURCE_LINE"], "DECLARED_PT": e["DECLARED_PT"], "GRAPHICS_SCALE": "1.00", "EFFECTIVE_PT": f"{e['EFFECTIVE_PT']:.2f}", "TEXT_SAMPLE": e["TEXT_SAMPLE"], "SCRIPT_CLASS": e["SCRIPT_CLASS"], "BBOX_X0": b[0], "BBOX_Y0": b[1], "BBOX_X1": b[2], "BBOX_Y1": b[3], "H_INK_PX": e["H_INK_PX"], "THRESHOLD_PX": e["THRESHOLD_PX"], "CLASS_MEDIAN_PX": f"{e['CLASS_MEDIAN_PX']:.2f}", "RATIO_TO_CLASS_MEDIAN": f"{e['RATIO_TO_CLASS_MEDIAN']:.3f}", "ROLE_RATIO": "N/A" if not math.isfinite(e["ROLE_RATIO"]) else f"{e['ROLE_RATIO']:.3f}", "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": e["TEXT_GRAPHIC_OVERLAP_PX"], "MIN_CLEARANCE_PX": "N/A" if not math.isfinite(e["MIN_CLEARANCE_PX"]) else f"{e['MIN_CLEARANCE_PX']:.2f}", "PASS_FAIL": e["PASS_FAIL"], "REASON": e["REASON"],
            }
            wri.writerow(row)

    # Object inventory preserves all non-text semantic elements required for a true element-level review.
    with (OUT / "after_element_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["ELEMENT_ID", "CATEGORY", "DESCRIPTION", "SOURCE_LINE", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "WIDTH_PT", "STATUS"]
        wri = csv.DictWriter(f, fieldnames=fields)
        wri.writeheader()
        for e in entries:
            b = e["BBOX_PX"]
            wri.writerow({"ELEMENT_ID": e["ELEMENT_ID"], "CATEGORY": "TEXT_OR_FORMULA", "DESCRIPTION": e["TEXT_SAMPLE"], "SOURCE_LINE": e["SOURCE_LINE"], "BBOX_X0": b[0], "BBOX_Y0": b[1], "BBOX_X1": b[2], "BBOX_Y1": b[3], "WIDTH_PT": "", "STATUS": e["PASS_FAIL"]})
        for g in graphics:
            b = _pdf_to_px(g["BBOX_PDF"], sx, sy)
            wri.writerow({"ELEMENT_ID": g["ELEMENT_ID"], "CATEGORY": g["TYPE"], "DESCRIPTION": g["TYPE"], "SOURCE_LINE": g["SOURCE_LINE"], "BBOX_X0": b[0], "BBOX_Y0": b[1], "BBOX_X1": b[2], "BBOX_Y1": b[3], "WIDTH_PT": g["WIDTH_PT"], "STATUS": "MEASURED"})

    # Per-pair report explicitly records all hard zero-overlap categories and their tightest observed clearances.
    node_text = [e for e in entries if e["PANEL_ID"] == "L" and ("node" in e["ROLE"] or "leaf" in e["ROLE"])]
    node_border_mask = np.zeros((h, w), dtype=bool)
    for gid in ("G01", "G02", "G03", "G04", "G05"):
        node_border_mask |= graphic_masks[gid]
    node_border_min = min((_mask_distance(e["TEXT_MASK"], node_border_mask, e["BBOX_PX"])[1] for e in node_text), default=float("inf"))
    # Raw figure boxes are generous; page-edge clipping is tested against the original full page, not crop edges.
    all_boxes = [e["BBOX_PX"] for e in entries] + [_pdf_to_px(g["BBOX_PDF"], sx, sy) for g in graphics]
    edge_min = min(min(b[0], b[1], w - b[2], h - b[3]) for b in all_boxes)
    left_boxes = [e["BBOX_PX"] for e in entries if e["PANEL_ID"] == "L"]
    right_boxes = [e["BBOX_PX"] for e in entries if e["PANEL_ID"] == "R"]
    cross_panel = min(b[0] - a[2] for a in left_boxes for b in right_boxes if b[0] >= a[2])
    pair_rows = [
        {"CHECK_ID": "O01", "CATEGORY": "TEXT_TEXT", "OBJECT_A": closest_tt[0], "OBJECT_B": closest_tt[1], "OBJECT_A_SOURCE_LINE": "see after_pixel_measurements.csv", "OBJECT_B_SOURCE_LINE": "see after_pixel_measurements.csv", "OBJECT_A_BBOX_PX": "see after_pixel_measurements.csv", "OBJECT_B_BBOX_PX": "see after_pixel_measurements.csv", "OVERLAP_PIXEL_COUNT": total_tt_overlap, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": min_text_text, "THRESHOLD_PX": 4, "METHOD": "all distinct semantic text groups"},
        {"CHECK_ID": "O02", "CATEGORY": "TEXT_LINE_ARROW_MARKER", "OBJECT_A": "all_text", "OBJECT_B": "G06-G15", "OBJECT_A_SOURCE_LINE": "multiple", "OBJECT_B_SOURCE_LINE": "7-12,19,22-25,36-42,54-65", "OBJECT_A_BBOX_PX": "see per-pair rows", "OBJECT_B_BBOX_PX": "see per-pair rows", "OVERLAP_PIXEL_COUNT": total_tg_overlap, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": min_text_graphic, "THRESHOLD_PX": 3, "METHOD": "visible text masks vs vector line/arrow/border semantic masks"},
        {"CHECK_ID": "O03", "CATEGORY": "NODE_TEXT_BORDER", "OBJECT_A": "tree node/leaf text", "OBJECT_B": "G01-G05", "OBJECT_A_SOURCE_LINE": "34-42", "OBJECT_B_SOURCE_LINE": "16-19,34-42", "OBJECT_A_BBOX_PX": "see after_pixel_measurements.csv", "OBJECT_B_BBOX_PX": "see after_element_inventory.csv", "OVERLAP_PIXEL_COUNT": 0, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": node_border_min, "THRESHOLD_PX": 5, "METHOD": "node-border semantic mask only"},
        {"CHECK_ID": "O04", "CATEGORY": "TEXT_PAGE_EDGE", "OBJECT_A": "all_text", "OBJECT_B": "official_page_edge", "OBJECT_A_SOURCE_LINE": "multiple", "OBJECT_B_SOURCE_LINE": "N/A", "OBJECT_A_BBOX_PX": "see after_pixel_measurements.csv", "OBJECT_B_BBOX_PX": f"0,0,{w},{h}", "OVERLAP_PIXEL_COUNT": 0, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": float(edge_min), "THRESHOLD_PX": 6, "METHOD": "original official page edge, not an evidence-crop edge"},
        {"CHECK_ID": "O05", "CATEGORY": "CROSS_PANEL_TEXT", "OBJECT_A": "left_panel_text", "OBJECT_B": "right_panel_text", "OBJECT_A_SOURCE_LINE": "30-48", "OBJECT_B_SOURCE_LINE": "52-68", "OBJECT_A_BBOX_PX": "see after_pixel_measurements.csv", "OBJECT_B_BBOX_PX": "see after_pixel_measurements.csv", "OVERLAP_PIXEL_COUNT": 0, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": float(cross_panel), "THRESHOLD_PX": 8, "METHOD": "left/right independent reader elements"},
        {"CHECK_ID": "O06", "CATEGORY": "CLIP", "OBJECT_A": "all_semantic_objects", "OBJECT_B": "official_page_bounds", "OBJECT_A_SOURCE_LINE": "multiple", "OBJECT_B_SOURCE_LINE": "N/A", "OBJECT_A_BBOX_PX": "see inventories", "OBJECT_B_BBOX_PX": f"0,0,{w},{h}", "OVERLAP_PIXEL_COUNT": 0, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": float(edge_min), "THRESHOLD_PX": 0, "METHOD": "no object reaches the official PDF page edge"},
    ]
    for n, detail in enumerate((p for p in text_graphic_pairs if p["OVERLAP_PIXEL_COUNT"] > 0), start=7):
        pair_rows.append({
            "CHECK_ID": f"O{n:02d}", "CATEGORY": "TEXT_LINE_ARROW_MARKER", "OBJECT_A": detail["ELEMENT_ID"], "OBJECT_B": detail["GRAPHIC_ID"],
            "OBJECT_A_SOURCE_LINE": detail["ELEMENT_SOURCE_LINE"], "OBJECT_B_SOURCE_LINE": detail["GRAPHIC_SOURCE_LINE"],
            "OBJECT_A_BBOX_PX": ",".join(map(str, detail["ELEMENT_BBOX_PX"])), "OBJECT_B_BBOX_PX": ",".join(map(str, detail["GRAPHIC_BBOX_PX"])),
            "OVERLAP_PIXEL_COUNT": detail["OVERLAP_PIXEL_COUNT"], "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": detail["MIN_CLEARANCE_PX"], "THRESHOLD_PX": 3,
            "METHOD": "native 300dpi glyph-colour semantic mask vs individual vector semantic mask; inspect paired 1:1 ROI",
        })
    with (OUT / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["CHECK_ID", "CATEGORY", "OBJECT_A", "OBJECT_B", "OBJECT_A_SOURCE_LINE", "OBJECT_B_SOURCE_LINE", "OBJECT_A_BBOX_PX", "OBJECT_B_BBOX_PX", "OVERLAP_PIXEL_COUNT", "CLIP_PIXEL_COUNT", "MIN_CLEARANCE_PX", "THRESHOLD_PX", "PASS_FAIL", "METHOD"]
        wri = csv.DictWriter(f, fieldnames=fields)
        wri.writeheader()
        for row in pair_rows:
            dist = row["MIN_CLEARANCE_PX"]
            thresh = row["THRESHOLD_PX"]
            row["PASS_FAIL"] = "PASS" if row["OVERLAP_PIXEL_COUNT"] == 0 and row["CLIP_PIXEL_COUNT"] == 0 and (thresh == 0 or dist >= thresh) else "FAIL"
            row["MIN_CLEARANCE_PX"] = "N/A" if not math.isfinite(dist) else f"{dist:.2f}"
            wri.writerow(row)

    # A fail-centric ledger gives SA2 a precise, non-ambiguous repair queue.
    fail_rows: list[dict] = []
    for e in entries:
        bbox = ",".join(map(str, e["BBOX_PX"]))
        if not e["FONT_PASS"]:
            direction = "Raise the named local font to >=9.5pt effective size (do not use global scaling); then reflow the panel."
            if e["ELEMENT_ID"] in {"E31", "E32"}:
                direction = "Set pgfplots tick label style to >=9.5pt effective size; recheck the title-to-tick hierarchy."
            fail_rows.append({"FAIL_TYPE": "SOURCE_FONT", "ELEMENT_ID": e["ELEMENT_ID"], "COUNTERPART": "", "SOURCE_LINE": e["SOURCE_LINE"], "NATIVE_BBOX_PX": bbox, "THRESHOLD": "effective_pt >= 9.50", "OBSERVED": f"{e['EFFECTIVE_PT']:.2f}pt", "MINIMAL_FIX_DIRECTION": direction})
        if not e["SAME_CLASS_PASS"]:
            cls = e["CLASS_KEY"]
            direction = "Normalize the same-role rendered glyph treatment (prefer a consistent label background/halo where pattern interference is present) and rerun the raw 300dpi ratio audit."
            if cls == "TREE_FORMULA_OPERATOR":
                direction = "Either predeclare > and <= as distinct semantic operator roles with a rationale, or choose a comparator treatment whose rendered ink heights meet the 0.92-1.08 same-class range."
            fail_rows.append({"FAIL_TYPE": "SAME_CLASS_RATIO", "ELEMENT_ID": e["ELEMENT_ID"], "COUNTERPART": cls, "SOURCE_LINE": e["SOURCE_LINE"], "NATIVE_BBOX_PX": bbox, "THRESHOLD": "per-element 0.92-1.08; class max/min <=1.08", "OBSERVED": f"ratio={e['RATIO_TO_CLASS_MEDIAN']:.3f}; class_spread={class_spreads[cls]:.3f}", "MINIMAL_FIX_DIRECTION": direction})
        if not e["ROLE_PASS"]:
            fail_rows.append({"FAIL_TYPE": "ROLE_RATIO", "ELEMENT_ID": e["ELEMENT_ID"], "COUNTERPART": "right_panel_tick_base (E31,E32)", "SOURCE_LINE": e["SOURCE_LINE"], "NATIVE_BBOX_PX": bbox, "THRESHOLD": "panel title / BASE in [1.05,1.20]", "OBSERVED": f"ratio={e['ROLE_RATIO']:.3f}", "MINIMAL_FIX_DIRECTION": "Raise tick labels to >=9.5pt and retain the current title size; this returns 10.5/9.5=1.105 without shrinking information."})
    for detail in (p for p in text_graphic_pairs if p["OVERLAP_PIXEL_COUNT"] > 0):
        direction = "Move the branch label away from the arrow path (or move the arrow) until the native 300dpi mask has 0 overlap and >=3px clearance; do not rely on draw order."
        fail_rows.append({"FAIL_TYPE": "TEXT_GRAPHIC_OVERLAP", "ELEMENT_ID": detail["ELEMENT_ID"], "COUNTERPART": detail["GRAPHIC_ID"], "SOURCE_LINE": f"text {detail['ELEMENT_SOURCE_LINE']}; graphic {detail['GRAPHIC_SOURCE_LINE']}", "NATIVE_BBOX_PX": f"text={','.join(map(str, detail['ELEMENT_BBOX_PX']))}; graphic={','.join(map(str, detail['GRAPHIC_BBOX_PX']))}", "THRESHOLD": "overlap=0; clearance >=3px", "OBSERVED": f"overlap={detail['OVERLAP_PIXEL_COUNT']}; clearance={detail['MIN_CLEARANCE_PX']:.2f}px", "MINIMAL_FIX_DIRECTION": direction})
    with (OUT / "failure_ledger.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["FAIL_TYPE", "ELEMENT_ID", "COUNTERPART", "SOURCE_LINE", "NATIVE_BBOX_PX", "THRESHOLD", "OBSERVED", "MINIMAL_FIX_DIRECTION"]
        wri = csv.DictWriter(f, fieldnames=fields)
        wri.writeheader()
        wri.writerows(fail_rows)

    summary = {
        "figure_id": "FIG-P242-01",
        "official_pdf": str(PDF),
        "physical_page": PAGE_NUMBER,
        "render": {"dpi": DPI, "file": RAW_PAGE.name, "width_px": w, "height_px": h, "sx": sx, "sy": sy, "resampled": False},
        "font_fail_ids": [e["ELEMENT_ID"] for e in entries if not e["FONT_PASS"]],
        "pixel_fail_ids": [e["ELEMENT_ID"] for e in entries if not e["PIXEL_PASS"]],
        "same_class_fail_ids": [e["ELEMENT_ID"] for e in entries if not e["SAME_CLASS_PASS"]],
        "role_fail_ids": [e["ELEMENT_ID"] for e in entries if not e["ROLE_PASS"]],
        "overlap_pixel_count": int(total_tt_overlap + total_tg_overlap),
        "clip_pixel_count": 0,
        "min_text_text_clearance_px": min_text_text,
        "min_text_graphic_clearance_px": min_text_graphic,
        "node_text_border_clearance_px": node_border_min,
        "edge_clearance_px": edge_min,
        "cross_panel_clearance_px": cross_panel,
        "class_spreads": class_spreads,
    }
    with (OUT / "measurement_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, allow_nan=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
