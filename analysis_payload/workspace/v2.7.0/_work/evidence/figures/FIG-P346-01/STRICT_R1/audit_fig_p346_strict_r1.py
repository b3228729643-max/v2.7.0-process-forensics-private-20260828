from __future__ import annotations

import csv
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
EVIDENCE = ROOT / r"v2.7.0\_work\evidence\figures\FIG-P346-01\STRICT_R1"
PDF = ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf"
SOURCE = ROOT / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第03册_优化模型与序列模型\V3-C04\fig_v3_c04_bound.tex"
PAGE_INDEX = 374
PHYSICAL_PAGE = 375
SCALE = 300.0 / 72.0
SS = 4


@dataclass
class Element:
    element_id: str
    parent_id: str
    role: str
    source_line: int
    declared_pt: float
    effective_pt: float
    token: str
    script_class: str
    min_px: int | None
    bbox_pt: tuple[float, float, float, float]
    pdf_font_size: float


def bbox_union(boxes: Iterable[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    b = list(boxes)
    return (min(x[0] for x in b), min(x[1] for x in b), max(x[2] for x in b), max(x[3] for x in b))


def px_box(box: tuple[float, float, float, float], pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (
        max(0, int(math.ceil(x0 * SCALE - 0.5)) - pad),
        max(0, int(math.ceil(y0 * SCALE - 0.5)) - pad),
        min(W, int(math.ceil(x1 * SCALE - 0.5)) + pad),
        min(H, int(math.ceil(y1 * SCALE - 0.5)) + pad),
    )


def actual_foreground_in_box(box: tuple[float, float, float, float]) -> np.ndarray:
    x0, y0, x1, y1 = px_box(box, pad=0)
    out = np.zeros((H, W), np.uint8)
    crop = text_layer_rgb[y0:y1, x0:x1].astype(np.int16)
    # Goal 9.2.1-C: local-background contrast of at least 20/255.
    # All text boxes here are on white or on a <= 5.5% pale fill whose
    # maximum channel difference remains below 20.
    fg = np.max(255 - crop, axis=2) >= 20
    out[y0:y1, x0:x1][fg] = 255
    return out


def ink_height(mask: np.ndarray) -> int:
    yy, _ = np.where(mask > 0)
    return 0 if len(yy) == 0 else int(yy.max() - yy.min() + 1)


def ink_width(mask: np.ndarray) -> int:
    _, xx = np.where(mask > 0)
    return 0 if len(xx) == 0 else int(xx.max() - xx.min() + 1)


def ink_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    yy, xx = np.where(mask > 0)
    if len(xx) == 0:
        return (0, 0, 0, 0)
    return (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)


def cubic_points(p0, p1, p2, p3, n=30):
    t = np.linspace(0.0, 1.0, n)
    u = 1.0 - t
    return np.column_stack(
        (
            u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x,
            u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y,
        )
    )


def drawing_points(d: dict) -> list[np.ndarray]:
    paths: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []
    for item in d["items"]:
        kind = item[0]
        if kind == "l":
            a, b = item[1], item[2]
            if not cur or abs(cur[-1][0] - a.x) > 1e-4 or abs(cur[-1][1] - a.y) > 1e-4:
                if cur:
                    paths.append(cur)
                cur = [(a.x, a.y)]
            cur.append((b.x, b.y))
        elif kind == "c":
            p0, p1, p2, p3 = item[1:5]
            pts = cubic_points(p0, p1, p2, p3)
            if not cur or abs(cur[-1][0] - p0.x) > 1e-4 or abs(cur[-1][1] - p0.y) > 1e-4:
                if cur:
                    paths.append(cur)
                cur = [(p0.x, p0.y)]
            cur.extend((float(x), float(y)) for x, y in pts[1:])
        elif kind == "re":
            r = item[1]
            if cur:
                paths.append(cur)
                cur = []
            paths.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
        elif kind == "qu":
            q = item[1]
            if cur:
                paths.append(cur)
                cur = []
            paths.append([(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y), (q.ul.x, q.ul.y)])
    if cur:
        paths.append(cur)
    return [np.asarray(p, dtype=np.float64) for p in paths]


def parse_dashes(text: str | None) -> tuple[list[float], float]:
    if not text or text.startswith("[]"):
        return ([], 0.0)
    nums = [float(x) for x in re.findall(r"[-+]?\d+(?:\.\d+)?", text)]
    if len(nums) < 2:
        return ([], 0.0)
    return (nums[:-1], nums[-1])


def draw_dashed_path(canvas: np.ndarray, pts: np.ndarray, width: int, pattern: list[float], phase: float):
    pts = pts * (SCALE * SS)
    pat = [max(0.01, x * SCALE * SS) for x in pattern]
    phase *= SCALE * SS
    state = 0
    while phase >= pat[state]:
        phase -= pat[state]
        state = (state + 1) % len(pat)
    remaining = pat[state] - phase
    draw_on = state % 2 == 0
    for a, b in zip(pts[:-1], pts[1:]):
        vec = b - a
        seglen = float(np.hypot(vec[0], vec[1]))
        if seglen <= 1e-9:
            continue
        unit = vec / seglen
        pos = 0.0
        while pos < seglen - 1e-9:
            step = min(remaining, seglen - pos)
            q0 = a + unit * pos
            q1 = a + unit * (pos + step)
            if draw_on:
                cv2.line(canvas, tuple(np.rint(q0).astype(int)), tuple(np.rint(q1).astype(int)), 255, width, cv2.LINE_AA)
            pos += step
            remaining -= step
            if remaining <= 1e-9:
                state = (state + 1) % len(pat)
                draw_on = state % 2 == 0
                remaining = pat[state]


def render_drawing_mask(d: dict, object_color: tuple[float, float, float] | None, fill_shape: bool = False) -> np.ndarray:
    hi = np.zeros((H * SS, W * SS), np.uint8)
    paths = drawing_points(d)
    width_pt = d.get("width") or 0.0
    width_hi = max(1, int(round(width_pt * SCALE * SS)))
    pattern, phase = parse_dashes(d.get("dashes"))
    if fill_shape:
        for path in paths:
            p = np.rint(path * (SCALE * SS)).astype(np.int32)
            cv2.fillPoly(hi, [p], 255, cv2.LINE_AA)
    if "s" in (d.get("type") or ""):
        for path in paths:
            if pattern:
                draw_dashed_path(hi, path, width_hi, pattern, phase)
            else:
                p = np.rint(path * (SCALE * SS)).astype(np.int32)
                cv2.polylines(hi, [p], False, 255, width_hi, cv2.LINE_AA)
                # line cap = round in the frozen candidate
                radius = max(1, width_hi // 2)
                cv2.circle(hi, tuple(p[0]), radius, 255, -1, cv2.LINE_AA)
                cv2.circle(hi, tuple(p[-1]), radius, 255, -1, cv2.LINE_AA)
    low = cv2.resize(hi, (W, H), interpolation=cv2.INTER_AREA)
    if object_color is None:
        max_diff = 255
    else:
        rgb = np.asarray(object_color) * 255.0
        max_diff = max(1.0, float(np.max(255.0 - rgb)))
    alpha_threshold = int(math.ceil(255.0 * 20.0 / max_diff))
    return np.where(low >= alpha_threshold, 255, 0).astype(np.uint8)


_point_cache: dict[int, tuple[np.ndarray, cKDTree]] = {}


def points_and_tree(mask: np.ndarray):
    key = id(mask)
    if key not in _point_cache:
        yy, xx = np.where(mask > 0)
        pts = np.column_stack((xx, yy)).astype(np.float64)
        _point_cache[key] = (pts, cKDTree(pts))
    return _point_cache[key]


def distance_and_points(mask_a: np.ndarray, mask_b: np.ndarray):
    overlap = int(np.count_nonzero((mask_a > 0) & (mask_b > 0)))
    ap, atree = points_and_tree(mask_a)
    bp, btree = points_and_tree(mask_b)
    if len(ap) == 0 or len(bp) == 0:
        return overlap, math.inf, (-1, -1), (-1, -1)
    if len(ap) <= len(bp):
        d, idx = btree.query(ap, k=1)
        k = int(np.argmin(d))
        pa = ap[k]; pb = bp[int(idx[k])]
        return overlap, float(d[k]), (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1]))
    d, idx = atree.query(bp, k=1)
    k = int(np.argmin(d))
    pb = bp[k]; pa = ap[int(idx[k])]
    return overlap, float(d[k]), (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1]))


def bbox_distance(a: tuple[float, float, float, float], b: tuple[float, float, float, float]):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    intersects = (min(ax1, bx1) > max(ax0, bx0)) and (min(ay1, by1) > max(ay0, by0))
    return float(math.hypot(dx, dy)), intersects


def save_roi(name: str, boxes: list[tuple[int, int, int, int]], pad=30, overlay=None):
    x0 = max(0, min(b[0] for b in boxes) - pad)
    y0 = max(0, min(b[1] for b in boxes) - pad)
    x1 = min(W, max(b[2] for b in boxes) + pad)
    y1 = min(H, max(b[3] for b in boxes) + pad)
    arr = page_rgb[y0:y1, x0:x1].copy()
    if overlay:
        for (x, y), color in overlay:
            cv2.drawMarker(arr, (x - x0, y - y0), color, cv2.MARKER_CROSS, 13, 2, cv2.LINE_AA)
    Image.fromarray(arr).save(EVIDENCE / name)


EVIDENCE.mkdir(parents=True, exist_ok=True)
mask_dir = EVIDENCE / "masks"
roi_dir = EVIDENCE / "roi"
mask_dir.mkdir(exist_ok=True)
roi_dir.mkdir(exist_ok=True)

page_path = EVIDENCE / "full_page_300dpi.png"
page_rgb = np.asarray(Image.open(page_path).convert("RGB"))
H, W = page_rgb.shape[:2]
assert (W, H) == (2481, 3508), (W, H)

# Lossless native-300-dpi crops; never resize after the official render.
figure_box_px = (450, 650, 2000, 1712)
figure_crop = Image.fromarray(page_rgb[figure_box_px[1]:figure_box_px[3], figure_box_px[0]:figure_box_px[2]])
figure_crop.save(EVIDENCE / "figure_crop_300dpi.png")
figure_crop.save(EVIDENCE / "standalone_300dpi.png")
gray = cv2.cvtColor(np.asarray(figure_crop), cv2.COLOR_RGB2GRAY)
Image.fromarray(gray).save(EVIDENCE / "grayscale_300dpi.png")

# If the independently compiled source-only page is present, use its native
# 300dpi non-white content crop as the true standalone view (no resizing).
standalone_full = EVIDENCE / "standalone_source_full_page_300dpi.png"
if standalone_full.exists():
    sa = np.asarray(Image.open(standalone_full).convert("RGB"))
    fg = np.max(255 - sa.astype(np.int16), axis=2) >= 10
    sy, sx = np.where(fg)
    if len(sx):
        pad = 40
        sx0 = max(0, int(sx.min()) - pad); sx1 = min(sa.shape[1], int(sx.max()) + 1 + pad)
        sy0 = max(0, int(sy.min()) - pad); sy1 = min(sa.shape[0], int(sy.max()) + 1 + pad)
        Image.fromarray(sa[sy0:sy1, sx0:sx1]).save(EVIDENCE / "standalone_300dpi.png")

doc = fitz.open(PDF)


def filtered_content(data: bytes, keep_text: bool) -> bytes:
    out = []
    in_text = False
    path_ops = {b"m", b"l", b"c", b"v", b"y", b"h", b"re", b"S", b"s", b"f", b"F", b"f*",
                b"B", b"B*", b"b", b"b*", b"n", b"W", b"W*", b"Do", b"sh"}
    for line in data.splitlines(keepends=True):
        stripped = line.strip()
        if stripped == b"BT":
            in_text = True
            if keep_text:
                out.append(line)
            continue
        if stripped == b"ET":
            if keep_text:
                out.append(line)
            in_text = False
            continue
        if in_text:
            if keep_text:
                out.append(line)
            continue
        if not keep_text:
            out.append(line)
            continue
        if stripped:
            op = stripped.split()[-1]
            if op in path_ops:
                continue
        out.append(line)
    return b"".join(out)


def make_layer_pdf(path: Path, keep_text: bool):
    layer = fitz.open()
    layer.insert_pdf(doc, from_page=PAGE_INDEX, to_page=PAGE_INDEX)
    p = layer[0]
    data = filtered_content(p.read_contents(), keep_text=keep_text)
    xref = layer.get_new_xref()
    layer.update_object(xref, "<<>>")
    layer.update_stream(xref, data)
    p.set_contents(xref)
    layer.save(path, garbage=4, deflate=True)
    layer.close()


text_pdf = EVIDENCE / "page375_text_only_independent.pdf"
graphics_pdf = EVIDENCE / "page375_graphics_only_independent.pdf"
make_layer_pdf(text_pdf, keep_text=True)
make_layer_pdf(graphics_pdf, keep_text=False)
subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(text_pdf), str(EVIDENCE / "page375_text_only_300dpi")], check=True)
subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(graphics_pdf), str(EVIDENCE / "page375_graphics_only_300dpi")], check=True)
text_layer_rgb = np.asarray(Image.open(EVIDENCE / "page375_text_only_300dpi.png").convert("RGB"))
assert text_layer_rgb.shape == page_rgb.shape
graphics_layer_rgb = np.asarray(Image.open(EVIDENCE / "page375_graphics_only_300dpi.png").convert("RGB"))
fx0, fy0, fx1, fy1 = figure_box_px
Image.fromarray(text_layer_rgb[fy0:fy1, fx0:fx1]).save(EVIDENCE / "text_layer_figure_crop_300dpi.png")
Image.fromarray(graphics_layer_rgb[fy0:fy1, fx0:fx1]).save(EVIDENCE / "graphics_layer_figure_crop_300dpi.png")

page = doc[PAGE_INDEX]
raw = page.get_text("rawdict")
spans = []
for block in raw["blocks"]:
    for line in block.get("lines", []):
        for span in line["spans"]:
            text = "".join(ch["c"] for ch in span["chars"])
            if span["bbox"][1] < 410 and span["bbox"][3] > 150:
                spans.append({"text": text, "span": span, "line": line})


def find_span(text: str, y_min: float, y_max: float):
    hits = [s for s in spans if s["text"] == text and y_min <= s["span"]["bbox"][1] <= y_max]
    if len(hits) != 1:
        raise RuntimeError(f"span {text!r} in {y_min}:{y_max}: {len(hits)} hits")
    return hits[0]


def char_info(spanrec, index: int):
    ch = spanrec["span"]["chars"][index]
    return ch["c"], tuple(ch["bbox"]), float(spanrec["span"]["size"])


elements: list[Element] = []


def add_char(eid, parent, role, line, declared, token, cls, min_px, spanrec, idx, effective=None):
    c, box, pdfsize = char_info(spanrec, idx)
    if c != token:
        raise RuntimeError(f"{eid}: expected {token!r}, got {c!r}")
    elements.append(Element(eid, parent, role, line, declared, declared if effective is None else effective,
                            token, cls, min_px, box, pdfsize))


tick = find_span("2", 355, 365)
ell = find_span("ℓ(𝜃)", 165, 180)
bound = find_span("𝐵(𝜃, 2)", 238, 250)
bound_cjk = find_span("：下界", 238, 250)
tangent_note = find_span("相切点；共享切线", 195, 210)
axis_theta = find_span("𝜃", 370, 380)
y_axis = find_span("目标值", 240, 255)
formula = find_span("ℓ(𝜃) −𝐵(𝜃, 2) = 0.16(𝜃−2)", 388, 398)
formula_exp = find_span("2", 385, 395)
formula_ge = find_span("≥0", 388, 398)

add_char("T01_X_TICK_2", "L01_X_TICK", "TICK", 15, 8.5, "2", "DIGIT", 24, tick, 0)
add_char("T02_X_AXIS_THETA", "L02_X_AXIS_LABEL", "AXIS_TITLE", 14, 9.5, "𝜃", "GREEK_LOWER", 17, axis_theta, 0)
for i, ch in enumerate("目标值"):
    add_char(f"T03{chr(65+i)}_Y_AXIS_{ch}", "L03_Y_AXIS_TITLE", "AXIS_TITLE", 14, 9.5, ch, "CJK", 30, y_axis, i)

for i, (suffix, ch, cls, mn) in enumerate([
    ("L", "ℓ", "LATIN_LOWER", 17), ("OPEN", "(", "MATH_OPERATOR", 22),
    ("THETA", "𝜃", "GREEK_LOWER", 17), ("CLOSE", ")", "MATH_OPERATOR", 22),
]):
    add_char(f"T04{chr(65+i)}_ELL_{suffix}", "L04_ELL_LABEL", "DIRECT_LABEL", 31, 9.2, ch, cls, mn, ell, i)

for i, (suffix, ch, cls, mn) in enumerate([
    ("B", "𝐵", "LATIN_CAP", 24), ("OPEN", "(", "MATH_OPERATOR", 22),
    ("THETA", "𝜃", "GREEK_LOWER", 17), ("COMMA", ",", "PUNCTUATION", None),
    ("SPACE", " ", "SPACE", None), ("TWO", "2", "DIGIT", 24), ("CLOSE", ")", "MATH_OPERATOR", 22),
]):
    if cls != "SPACE":
        add_char(f"T05{chr(65+i)}_BOUND_{suffix}", "L05_BOUND_LABEL", "DIRECT_LABEL", 35, 9.2, ch, cls, mn, bound, i)
for i, (ch, cls, mn) in enumerate([("：", "FULLWIDTH_SYMBOL", 30), ("下", "CJK", 30), ("界", "CJK", 30)]):
    add_char(f"T05H{i+1}_BOUND_CJK_{i+1}", "L05_BOUND_LABEL", "DIRECT_LABEL", 35, 9.2, ch, cls, mn, bound_cjk, i)

for i, ch in enumerate("相切点；共享切线"):
    cls = "FULLWIDTH_SYMBOL" if ch == "；" else "CJK"
    add_char(f"T06{chr(65+i)}_TANGENCY_{i+1}", "L06_TANGENCY_NOTE", "ANNOTATION", 39, 9.0, ch, cls, 30, tangent_note, i)

formula_chars = [
    ("L", "ℓ", "LATIN_LOWER", 17, 0), ("OPEN1", "(", "MATH_OPERATOR", 22, 1),
    ("THETA1", "𝜃", "GREEK_LOWER", 17, 2), ("CLOSE1", ")", "MATH_OPERATOR", 22, 3),
    ("MINUS1", "−", "MATH_OPERATOR", 22, 5), ("B", "𝐵", "LATIN_CAP", 24, 6),
    ("OPEN2", "(", "MATH_OPERATOR", 22, 7), ("THETA2", "𝜃", "GREEK_LOWER", 17, 8),
    ("COMMA", ",", "PUNCTUATION", None, 9), ("TWO_ARG", "2", "DIGIT", 24, 11),
    ("CLOSE2", ")", "MATH_OPERATOR", 22, 12), ("EQUALS", "=", "MATH_OPERATOR", 22, 14),
    ("ZERO1", "0", "DIGIT", 24, 16), ("DOT", ".", "PUNCTUATION", None, 17),
    ("ONE", "1", "DIGIT", 24, 18), ("SIX", "6", "DIGIT", 24, 19),
    ("OPEN3", "(", "MATH_OPERATOR", 22, 20), ("THETA3", "𝜃", "GREEK_LOWER", 17, 21),
    ("MINUS2", "−", "MATH_OPERATOR", 22, 22), ("TWO_BASE", "2", "DIGIT", 24, 23),
    ("CLOSE3", ")", "MATH_OPERATOR", 22, 24),
]
for i, (suffix, ch, cls, mn, idx) in enumerate(formula_chars):
    add_char(f"T07{chr(65+i)}_FORMULA_{suffix}", "L07_FORMULA_NOTE", "FORMULA_BLOCK", 44, 9.0, ch, cls, mn, formula, idx)
add_char("T07V_FORMULA_EXP2", "L07_FORMULA_NOTE", "FORMULA_BLOCK", 44, 9.0, "2", "NATURAL_SCRIPT", 15, formula_exp, 0)
add_char("T07W_FORMULA_GE", "L07_FORMULA_NOTE", "FORMULA_BLOCK", 44, 9.0, "≥", "MATH_OPERATOR", 22, formula_ge, 0)
add_char("T07X_FORMULA_ZERO2", "L07_FORMULA_NOTE", "FORMULA_BLOCK", 44, 9.0, "0", "DIGIT", 24, formula_ge, 1)

# Independent actual raster masks for every reader-visible token.
element_masks: dict[str, np.ndarray] = {}
for el in elements:
    m = actual_foreground_in_box(el.bbox_pt)
    element_masks[el.element_id] = m
    Image.fromarray(m).save(mask_dir / f"{el.element_id}_TEXT_MASK.png")

parent_masks: dict[str, np.ndarray] = {}
for el in elements:
    parent_masks.setdefault(el.parent_id, np.zeros((H, W), np.uint8))
    parent_masks[el.parent_id] = cv2.bitwise_or(parent_masks[el.parent_id], element_masks[el.element_id])
for pid, m in parent_masks.items():
    Image.fromarray(m).save(mask_dir / f"{pid}_TEXT_OBJECT_MASK.png")

drawings = page.get_drawings()
graphic_specs = [
    ("G01_X_TICK_LINE", "LINE_ARROW", 4, False),
    ("G02_X_AXIS_LINE", "LINE_ARROW", 5, False),
    ("G03_X_AXIS_ARROWHEAD", "LINE_ARROW", 6, True),
    ("G04_Y_AXIS_LINE", "LINE_ARROW", 7, False),
    ("G05_Y_AXIS_ARROWHEAD", "LINE_ARROW", 8, True),
    ("G06_ELL_CURVE", "DATA_CURVE", 10, False),
    ("G07_BOUND_CURVE", "DATA_CURVE", 11, False),
    ("G08_VERTICAL_GUIDE", "LINE_ARROW", 12, False),
    ("G09_TANGENT_LINE", "DATA_CURVE", 13, False),
    ("G10_ELL_LEADER", "LINE_ARROW", 14, False),
    ("G11_BOUND_LEADER", "LINE_ARROW", 15, False),
    ("G12_TANGENCY_LEADER", "LINE_ARROW", 16, False),
    ("G13_TANGENCY_MARKER", "MARKER", 17, True),
    ("G14_FORMULA_NOTE_BORDER", "NODE_BORDER", 18, False),
]
graphic_masks: dict[str, np.ndarray] = {}
graphic_classes: dict[str, str] = {}
for gid, cls, idx, filled in graphic_specs:
    d = drawings[idx]
    color = d.get("fill") if filled and d.get("fill") is not None else d.get("color")
    gm = render_drawing_mask(d, color, fill_shape=filled)
    graphic_masks[gid] = gm
    graphic_classes[gid] = cls
    Image.fromarray(gm).save(mask_dir / f"{gid}_{cls}_MASK.png")

# Pixel metrics and within-role class ratios.  The y-axis title is rotated;
# normalize it back to reading orientation, so H_ink is rotation-invariant.
heights = {
    el.element_id: (ink_width(element_masks[el.element_id]) if el.parent_id == "L03_Y_AXIS_TITLE" else ink_height(element_masks[el.element_id]))
    for el in elements
}
class_groups: dict[tuple[str, str], list[int]] = {}
for el in elements:
    if el.script_class not in {"SPACE", "PUNCTUATION"}:
        class_groups.setdefault((el.role, el.script_class), []).append(heights[el.element_id])
class_median = {k: float(np.median(v)) for k, v in class_groups.items()}

base_height = float(heights["T01_X_TICK_2"])
role_medians: dict[str, float] = {}
for role in sorted({e.role for e in elements}):
    vals = [heights[e.element_id] for e in elements if e.role == role and e.script_class not in {"SPACE", "PUNCTUATION", "FULLWIDTH_SYMBOL", "MATH_OPERATOR"}]
    role_medians[role] = float(np.median(vals)) if vals else math.nan

role_bands = {
    "TICK": (1.00, 1.00),
    "AXIS_TITLE": (1.00, 1.18),
    "DIRECT_LABEL": (0.95, 1.10),
    "ANNOTATION": (0.95, 1.10),
    "FORMULA_BLOCK": (1.00, 1.18),
}
role_rows = []
for role, med in role_medians.items():
    ratio = med / base_height if base_height and not math.isnan(med) else math.nan
    lo, hi = role_bands[role]
    role_rows.append({
        "PANEL_ID": "P1", "ROLE": role, "BASE_ROLE": "TICK", "BASE_MEDIAN_PX": f"{base_height:.2f}",
        "ROLE_MEDIAN_PX": f"{med:.2f}", "ROLE_RATIO": f"{ratio:.4f}", "ALLOWED_BAND": f"[{lo:.2f},{hi:.2f}]",
        "PASS_FAIL": "PASS" if lo <= ratio <= hi else "FAIL",
        "METHOD": "native 300dpi principal-glyph ink median; rotated y-axis CJK orientation-normalized",
    })
with (EVIDENCE / "role_ratio_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
    wri = csv.DictWriter(f, fieldnames=list(role_rows[0])); wri.writeheader(); wri.writerows(role_rows)

font_rows = []
pixel_rows = []
for el in elements:
    h = heights[el.element_id]
    # Natural scripts are exempt only when derived from a >=9.5pt base.
    # Here the whole formula base is 9.0pt, so its exponent is not exempt.
    source_pass = el.effective_pt >= 9.5
    key = (el.role, el.script_class)
    med = class_median.get(key, math.nan)
    ratio = h / med if med and not math.isnan(med) else math.nan
    role_ratio = role_medians[el.role] / base_height if base_height and not math.isnan(role_medians[el.role]) else math.nan
    pixel_pass = el.min_px is None or h >= el.min_px
    ratio_pass = math.isnan(ratio) or 0.92 <= ratio <= 1.08
    reasons = []
    if not source_pass:
        reasons.append(f"effective_pt {el.effective_pt:.2f}<9.50")
    if not pixel_pass:
        reasons.append(f"H_ink {h}px<{el.min_px}px")
    if not ratio_pass:
        reasons.append(f"same-role/class ratio {ratio:.4f} outside [0.92,1.08]")
    x0, y0, x1, y1 = ink_bbox(element_masks[el.element_id])
    font_rows.append({
        "ELEMENT_ID": el.element_id, "PARENT_OBJECT_ID": el.parent_id, "PANEL_ID": "P1",
        "ROLE": el.role, "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": el.source_line,
        "TEXT_SAMPLE": el.token, "DECLARED_PT": f"{el.declared_pt:.2f}", "GRAPHICS_SCALE": "1.0000",
        "EFFECTIVE_PT": f"{el.effective_pt:.2f}", "PDF_SPAN_SIZE_PT": f"{el.pdf_font_size:.4f}",
        "PASS_FAIL": "PASS" if source_pass else "FAIL",
        "REASON": "source effective size passes" if source_pass else reasons[0],
    })
    pixel_rows.append({
        "ELEMENT_ID": el.element_id, "PARENT_OBJECT_ID": el.parent_id, "PANEL_ID": "P1", "ROLE": el.role,
        "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": el.source_line,
        "DECLARED_PT": f"{el.declared_pt:.2f}", "GRAPHICS_SCALE": "1.0000", "EFFECTIVE_PT": f"{el.effective_pt:.2f}",
        "TEXT_SAMPLE": el.token, "SCRIPT_CLASS": el.script_class,
        "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1,
        "H_INK_PX": h, "REQUIRED_MIN_PX": "" if el.min_px is None else el.min_px,
        "CLASS_MEDIAN_PX": "" if math.isnan(med) else f"{med:.2f}",
        "RATIO_TO_CLASS_MEDIAN": "" if math.isnan(ratio) else f"{ratio:.4f}",
        "ROLE_RATIO": "" if math.isnan(role_ratio) else f"{role_ratio:.4f}",
        "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0,
        "MIN_CLEARANCE_PX": "see after_overlap_report.csv",
        "PASS_FAIL": "PASS" if source_pass and pixel_pass and ratio_pass else "FAIL",
        "REASON": "; ".join(reasons) if reasons else "meets measured source/pixel/class gates",
    })

# Independent object overlap and clearance matrix.
overlap_rows = []
parent_ids = sorted(parent_masks)
parent_boxes_px = {}
for pid in parent_ids:
    boxes = [e.bbox_pt for e in elements if e.parent_id == pid]
    b = bbox_union(boxes)
    parent_boxes_px[pid] = tuple(v * SCALE for v in b)
graphic_boxes_px = {}
for gid, cls, idx, filled in graphic_specs:
    r = drawings[idx]["rect"]
    half = ((drawings[idx].get("width") or 0.0) * SCALE / 2.0)
    graphic_boxes_px[gid] = (r.x0 * SCALE - half, r.y0 * SCALE - half, r.x1 * SCALE + half, r.y1 * SCALE + half)
for i, a in enumerate(parent_ids):
    for b in parent_ids[i + 1:]:
        ov, dist, pa, pb = distance_and_points(parent_masks[a], parent_masks[b])
        bdist, binter = bbox_distance(parent_boxes_px[a], parent_boxes_px[b])
        overlap_rows.append({
            "OBJECT_A": a, "CLASS_A": "TEXT", "OBJECT_B": b, "CLASS_B": "TEXT",
            "OVERLAP_PIXEL_COUNT": ov, "MIN_CLEARANCE_PX": f"{dist:.4f}", "REQUIRED_CLEARANCE_PX": 4,
            "BBOX_CLEARANCE_PX": f"{bdist:.4f}", "BBOX_INTERSECT": str(binter).lower(),
            "A_NEAREST_XY": f"{pa[0]},{pa[1]}", "B_NEAREST_XY": f"{pb[0]},{pb[1]}",
            "MASK_METHOD": "native 300dpi actual-text foreground, contrast>=20; no dilation",
            "PASS_FAIL": "PASS" if ov == 0 and bdist >= 4 else "FAIL",
        })
for pid, tm in parent_masks.items():
    for gid, gm in graphic_masks.items():
        required = 5 if pid == "L07_FORMULA_NOTE" and gid == "G14_FORMULA_NOTE_BORDER" else 3
        ov, dist, pa, pb = distance_and_points(tm, gm)
        bdist, binter = bbox_distance(parent_boxes_px[pid], graphic_boxes_px[gid])
        overlap_rows.append({
            "OBJECT_A": pid, "CLASS_A": "TEXT", "OBJECT_B": gid, "CLASS_B": graphic_classes[gid],
            "OVERLAP_PIXEL_COUNT": ov, "MIN_CLEARANCE_PX": f"{dist:.4f}", "REQUIRED_CLEARANCE_PX": required,
            "BBOX_CLEARANCE_PX": f"{bdist:.4f}", "BBOX_INTERSECT": str(binter).lower(),
            "A_NEAREST_XY": f"{pa[0]},{pa[1]}", "B_NEAREST_XY": f"{pb[0]},{pb[1]}",
            "MASK_METHOD": "native text raster + independent PDF-vector reconstruction at 4x SS; threshold mapped to contrast>=20; no dilation",
            "PASS_FAIL": "PASS" if ov == 0 and dist >= required else "FAIL",
        })
with (EVIDENCE / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
    wri = csv.DictWriter(f, fieldnames=list(overlap_rows[0]))
    wri.writeheader(); wri.writerows(overlap_rows)

# Add matrix minima back to the pixel table, without changing source measurements.
text_to_text = [r for r in overlap_rows if r["CLASS_B"] == "TEXT"]
text_to_graphic = [r for r in overlap_rows if r["CLASS_B"] != "TEXT"]
max_overlap = max(int(r["OVERLAP_PIXEL_COUNT"]) for r in overlap_rows)
total_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in overlap_rows)
min_tt = min(float(r["MIN_CLEARANCE_PX"]) for r in text_to_text)
min_tg = min(float(r["MIN_CLEARANCE_PX"]) for r in text_to_graphic)
min_tt_bbox = min(float(r["BBOX_CLEARANCE_PX"]) for r in text_to_text)

for row in pixel_rows:
    pid = row["PARENT_OBJECT_ID"]
    rel = [r for r in overlap_rows if r["OBJECT_A"] == pid]
    row["TEXT_TEXT_OVERLAP_PX"] = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in rel if r["CLASS_B"] == "TEXT")
    row["TEXT_GRAPHIC_OVERLAP_PX"] = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in rel if r["CLASS_B"] != "TEXT")
    row["MIN_CLEARANCE_PX"] = f"{min(float(r['MIN_CLEARANCE_PX']) for r in rel):.4f}"
with (EVIDENCE / "after_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
    wri = csv.DictWriter(f, fieldnames=list(font_rows[0]))
    wri.writeheader(); wri.writerows(font_rows)
with (EVIDENCE / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
    wri = csv.DictWriter(f, fieldnames=list(pixel_rows[0]))
    wri.writeheader(); wri.writerows(pixel_rows)

# Traceable page-edge / clipping and single-panel applicability evidence.
edge_rows = []
for oid, cls, box in [(k, "TEXT", v) for k, v in parent_boxes_px.items()] + [(k, graphic_classes[k], v) for k, v in graphic_boxes_px.items()]:
    x0, y0, x1, y1 = box
    edge = min(x0, y0, W - x1, H - y1)
    clipped = int(x0 < 0 or y0 < 0 or x1 > W or y1 > H)
    edge_rows.append({"OBJECT_ID": oid, "CLASS": cls, "PAGE_X0": f"{x0:.4f}", "PAGE_Y0": f"{y0:.4f}",
                      "PAGE_X1": f"{x1:.4f}", "PAGE_Y1": f"{y1:.4f}", "MIN_PAGE_EDGE_CLEARANCE_PX": f"{edge:.4f}",
                      "REQUIRED_PX": 6, "CLIP_PIXEL_COUNT": clipped,
                      "PANEL_ID": "P1", "PANEL_BORDER_STATUS": "NOT_PRESENT_SINGLE_PANEL",
                      "CROSS_PANEL_CHECK": "NOT_APPLICABLE_ONE_PANEL",
                      "PASS_FAIL": "PASS" if clipped == 0 and edge >= 6 else "FAIL"})
with (EVIDENCE / "edge_clip_panel_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
    wri = csv.DictWriter(f, fieldnames=list(edge_rows[0])); wri.writeheader(); wri.writerows(edge_rows)

# Traceable measurement overlay.  The frozen native crop is pasted 1:1 on a
# larger white sheet; no figure pixel is resized.  Numbered bboxes map to a
# two-column table containing every full ELEMENT_ID and H_ink value.
fx0, fy0, fx1, fy1 = figure_box_px
crop_arr = page_rgb[fy0:fy1, fx0:fx1]
sheet = Image.new("RGB", (3450, 1160), "white")
sheet.paste(Image.fromarray(crop_arr), (30, 50))
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
    badge_font = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 15)
except OSError:
    font = ImageFont.load_default(); badge_font = font
palette = [(220, 38, 38), (37, 99, 235), (5, 150, 105), (217, 119, 6)]
for idx, el in enumerate(elements):
    x0, y0, x1, y1 = ink_bbox(element_masks[el.element_id])
    color = palette[idx % len(palette)]
    rx0, ry0, rx1, ry1 = x0 - fx0 + 30, y0 - fy0 + 50, x1 - fx0 + 30, y1 - fy0 + 50
    draw.rectangle((rx0, ry0, rx1, ry1), outline=color, width=2)
    draw.rectangle((rx0, max(0, ry0 - 18), rx0 + 27, ry0), fill="white", outline=color, width=1)
    draw.text((rx0 + 2, max(0, ry0 - 18)), f"{idx+1:02d}", fill=color, font=badge_font)
    col = idx // 25
    row = idx % 25
    tx = 1610 + col * 900
    ty = 55 + row * 42
    draw.text((tx, ty), f"{idx+1:02d}  {el.element_id}  H={heights[el.element_id]}px", fill=color, font=font)
sheet.save(EVIDENCE / "after_text_measurement_overlay_300dpi.png")

# Critical native 1:1 raw ROIs and nearest-point overlay.
formula_box = ink_bbox(parent_masks["L07_FORMULA_NOTE"])
tick_box = ink_bbox(parent_masks["L01_X_TICK"])
tangent_box = ink_bbox(parent_masks["L06_TANGENCY_NOTE"])
theta_box = ink_bbox(parent_masks["L02_X_AXIS_LABEL"])
border_box = ink_bbox(graphic_masks["G14_FORMULA_NOTE_BORDER"])
save_roi("roi/roi_formula_operators_raw_1to1_300dpi.png", [formula_box], pad=35)
save_roi("roi/roi_tick_2_raw_1to1_300dpi.png", [tick_box], pad=35)
save_roi("roi/roi_tangency_note_raw_1to1_300dpi.png", [tangent_box], pad=35)
save_roi("roi/roi_axis_theta_to_note_border_raw_1to1_300dpi.png", [theta_box, border_box], pad=20)
critical = next(r for r in overlap_rows if r["OBJECT_A"] == "L02_X_AXIS_LABEL" and r["OBJECT_B"] == "G14_FORMULA_NOTE_BORDER")
pa = tuple(map(int, critical["A_NEAREST_XY"].split(",")))
pb = tuple(map(int, critical["B_NEAREST_XY"].split(",")))
save_roi("roi/roi_axis_theta_to_note_border_nearest_points_1to1_300dpi.png", [theta_box, border_box], pad=20,
         overlay=[(pa, (255, 0, 0)), (pb, (0, 0, 255))])
Image.fromarray(parent_masks["L02_X_AXIS_LABEL"]).save(roi_dir / "roi_axis_theta_TEXT_MASK.png")
Image.fromarray(graphic_masks["G14_FORMULA_NOTE_BORDER"]).save(roi_dir / "roi_formula_border_NODE_BORDER_MASK.png")

bound_row = next(r for r in overlap_rows if r["OBJECT_A"] == "L05_BOUND_LABEL" and r["OBJECT_B"] == "G07_BOUND_CURVE")
bound_box = ink_bbox(parent_masks["L05_BOUND_LABEL"])
bx0 = max(0, bound_box[0] - 45); by0 = max(0, bound_box[1] - 45)
bx1 = min(W, bound_box[2] + 45); by1 = min(H, bound_box[3] + 45)
Image.fromarray(page_rgb[by0:by1, bx0:bx1]).save(roi_dir / "roi_bound_label_vs_curve_raw_1to1_300dpi.png")
Image.fromarray(parent_masks["L05_BOUND_LABEL"][by0:by1, bx0:bx1]).save(roi_dir / "roi_bound_label_TEXT_MASK_1to1.png")
Image.fromarray(graphic_masks["G07_BOUND_CURVE"][by0:by1, bx0:bx1]).save(roi_dir / "roi_bound_curve_DATA_CURVE_MASK_1to1.png")
ovmask = ((parent_masks["L05_BOUND_LABEL"] > 0) & (graphic_masks["G07_BOUND_CURVE"] > 0)).astype(np.uint8) * 255
Image.fromarray(ovmask[by0:by1, bx0:bx1]).save(roi_dir / "roi_bound_label_curve_OVERLAP_MASK_1to1.png")
ov = page_rgb[by0:by1, bx0:bx1].copy()
tlocal = parent_masks["L05_BOUND_LABEL"][by0:by1, bx0:bx1] > 0
glocal = graphic_masks["G07_BOUND_CURVE"][by0:by1, bx0:bx1] > 0
ov[tlocal] = (0.55 * ov[tlocal] + 0.45 * np.array([0, 180, 255])).astype(np.uint8)
ov[glocal] = (0.55 * ov[glocal] + 0.45 * np.array([255, 210, 0])).astype(np.uint8)
ov[tlocal & glocal] = np.array([255, 0, 255], dtype=np.uint8)
Image.fromarray(ov).save(roi_dir / "roi_bound_label_curve_overlap_overlay_1to1_300dpi.png")

summary = {
    "element_count": len(elements),
    "source_fail_count": sum(r["PASS_FAIL"] == "FAIL" for r in font_rows),
    "pixel_or_ratio_fail_count": sum(r["PASS_FAIL"] == "FAIL" for r in pixel_rows),
    "pixel_height_fail_count": sum((e.min_px is not None and heights[e.element_id] < e.min_px) for e in elements),
    "same_class_ratio_fail_count": sum((r["RATIO_TO_CLASS_MEDIAN"] not in {"", None} and not 0.92 <= float(r["RATIO_TO_CLASS_MEDIAN"]) <= 1.08) for r in pixel_rows),
    "role_ratio_fail_count": sum(r["PASS_FAIL"] == "FAIL" for r in role_rows),
    "overlap_pair_count": sum(int(r["OVERLAP_PIXEL_COUNT"]) > 0 for r in overlap_rows),
    "overlap_pixel_sum": total_overlap,
    "max_pair_overlap": max_overlap,
    "min_text_text_clearance": min_tt,
    "min_text_text_bbox_clearance": min_tt_bbox,
    "min_text_graphic_clearance": min_tg,
    "axis_theta_to_border_clearance": float(critical["MIN_CLEARANCE_PX"]),
    "axis_theta_to_border_bbox_clearance": float(critical["BBOX_CLEARANCE_PX"]),
    "clip_pixel_count": sum(int(r["CLIP_PIXEL_COUNT"]) for r in edge_rows),
}
with (EVIDENCE / "measurement_summary.txt").open("w", encoding="utf-8") as f:
    for k, v in summary.items():
        f.write(f"{k}={v}\n")
print(summary)
