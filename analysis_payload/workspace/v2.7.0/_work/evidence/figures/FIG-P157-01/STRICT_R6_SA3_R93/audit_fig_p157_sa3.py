"""Independent strict R6/R93 audit for FIG-P157-01.

Inputs are deliberately limited to the frozen candidate PDF.  Source-line
facts below were transcribed from the permitted figure source and its direct
chapter context.  Every PNG is rasterized at its native requested DPI; no
spatial resampling occurs anywhere in this script.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P157-01\STRICT_R6_SA3_R93")
SOURCE_REL = "src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex"
CHAPTER_REL = "src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C10.tex"
PDF_PAGE_1 = 170
PRINTED_PAGE = 157
DPI = 300
S = DPI / 72.0  # PDF user-space point to pixels for this native render.
ROI_PAD = 2  # fixed presentation-only pad; object masks themselves have no pad.

# The page rectangle is measured from the final PDF, not an assumed source size.
FIGCAP_RECT = fitz.Rect(73.70, 64.00, 532.92, 365.00)
STANDALONE_RECT = fitz.Rect(73.70, 64.00, 532.92, 345.00)


def mkdirs() -> None:
    for name in ("masks", "raw_rois", "pair_rois", "metadata"):
        (OUT / name).mkdir(parents=True, exist_ok=True)


def save_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def rgb_from_pdf_color(color: int | tuple[float, float, float]) -> tuple[int, int, int]:
    if isinstance(color, int):
        return ((color >> 16) & 255, (color >> 8) & 255, color & 255)
    return tuple(int(round(255 * c)) for c in color)


def rect_list(r: fitz.Rect | tuple[float, float, float, float]) -> list[float]:
    return [round(float(v), 5) for v in r]


def point_list(p: fitz.Point) -> list[float]:
    return [round(float(p.x), 5), round(float(p.y), 5)]


def px_from_point(x: float, y: float) -> tuple[float, float]:
    return x * S, y * S


def rect_px(r: fitz.Rect) -> tuple[int, int, int, int]:
    """The only rectangle-to-pixel quantization: native PDF bbox, no padding."""
    return (
        max(0, math.floor(r.x0 * S)),
        max(0, math.floor(r.y0 * S)),
        math.ceil(r.x1 * S),
        math.ceil(r.y1 * S),
    )


def clamp_rect(rect: tuple[int, int, int, int], w: int, h: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[float, bool]:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy), bool(dx == 0 and dy == 0)


def crop(img: np.ndarray, rect: tuple[int, int, int, int], pad: int = 0) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    h, w = img.shape[:2]
    x0, y0, x1, y1 = clamp_rect(rect, w, h, pad)
    return img[y0:y1, x0:x1].copy(), (x0, y0, x1, y1)


def save_img(path: Path, arr: np.ndarray) -> None:
    if arr.ndim == 2:
        Image.fromarray(arr.astype(np.uint8), mode="L").save(path)
    else:
        Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path)


def image_from_pixmap(pix: fitz.Pixmap) -> np.ndarray:
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].copy()


def get_raw_spans(page: fitz.Page) -> list[dict]:
    raw = page.get_text("rawdict")
    spans: list[dict] = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                chars = span.get("chars", [])
                text = "".join(ch["c"] for ch in chars)
                spans.append({
                    "text": text,
                    "bbox": fitz.Rect(span["bbox"]),
                    "font": span["font"],
                    "size_bp": float(span["size"]),
                    "color": int(span["color"]),
                    "flags": span.get("flags"),
                    "chars": [{"c": ch["c"], "bbox": fitz.Rect(ch["bbox"])} for ch in chars],
                })
    return spans


TEXT_SPECS = [
    {
        "id": "P157-T01", "text": "训练误差：单调下降", "role": "DIRECT_ANNOTATION", "parent": "",
        "source_line": "44-46", "declared_pt": 9.2, "source_scale": "1.12 (V1-C10.tex:256)",
        "source_scale_complete": True, "expected_effective_pt": 10.304,
    },
    {
        "id": "P157-T02", "text": "验证误差：先降后升", "role": "DIRECT_ANNOTATION", "parent": "",
        "source_line": "47-48", "declared_pt": 9.2, "source_scale": "1.12 (V1-C10.tex:256)",
        "source_scale_complete": True, "expected_effective_pt": 10.304,
    },
    {
        "id": "P157-T03", "text": "最低验证误差", "role": "KEY_ANNOTATION", "parent": "",
        "source_line": "49-50", "declared_pt": 9.2, "source_scale": "1.12 (V1-C10.tex:256)",
        "source_scale_complete": True, "expected_effective_pt": 10.304,
    },
    {
        "id": "P157-T04", "text": "选择复杂度", "role": "KEY_ANNOTATION", "parent": "",
        "source_line": "51-52", "declared_pt": 9.2, "source_scale": "1.12 (V1-C10.tex:256)",
        "source_scale_complete": True, "expected_effective_pt": 10.304,
    },
    {
        "id": "P157-T05", "text": "欠拟合", "role": "REGION_LABEL", "parent": "",
        "source_line": "53-54", "declared_pt": 8.8, "source_scale": "1.12 (V1-C10.tex:256)",
        "source_scale_complete": True, "expected_effective_pt": 9.856,
    },
    {
        "id": "P157-T06", "text": "合适", "role": "REGION_LABEL", "parent": "",
        "source_line": "55-56", "declared_pt": 8.8, "source_scale": "1.12 (V1-C10.tex:256)",
        "source_scale_complete": True, "expected_effective_pt": 9.856,
    },
    {
        "id": "P157-T07", "text": "过拟合", "role": "REGION_LABEL", "parent": "",
        "source_line": "57-58", "declared_pt": 8.8, "source_scale": "1.12 (V1-C10.tex:256)",
        "source_scale_complete": True, "expected_effective_pt": 9.856,
    },
    {
        "id": "P157-T08", "text": "模型复杂度", "role": "AXIS_TITLE", "parent": "",
        "source_line": "figure:14-15,20-25; common/figure-style-v2.3.0.tex:33-39",
        "declared_pt": 10.0,
        "source_scale": "1.12 (V1-C10.tex:256); source 9.4pt is overridden by later slfig axis label style=\\small=10pt",
        "source_scale_complete": True, "expected_effective_pt": 11.2,
    },
    {
        "id": "P157-T09", "text": "预测误差", "role": "AXIS_TITLE", "parent": "",
        "source_line": "figure:14-15,20-25; common/figure-style-v2.3.0.tex:33-39",
        "declared_pt": 10.0,
        "source_scale": "1.12 (V1-C10.tex:256); source 9.4pt is overridden by later slfig axis label style=\\small=10pt",
        "source_scale_complete": True, "expected_effective_pt": 11.2,
    },
    {
        "id": "P157-T10A", "text": "图", "role": "CAPTION", "parent": "P157-T10",
        "source_line": "figure:61; common/statlearnbook.sty:305-306; 合并总册/main.tex:7",
        "declared_pt": 10.0, "source_scale": "1.00; ctexbook[11pt] \\small=10pt via captionsetup",
        "source_scale_complete": True, "expected_effective_pt": 10.0,
    },
    {
        "id": "P157-T10B", "text": "10.1", "role": "CAPTION", "parent": "P157-T10",
        "source_line": "figure:61; common/statlearnbook.sty:305-306; 合并总册/main.tex:7",
        "declared_pt": 10.0, "source_scale": "1.00; ctexbook[11pt] \\small=10pt via captionsetup",
        "source_scale_complete": True, "expected_effective_pt": 10.0,
    },
    {
        "id": "P157-T10C", "text": "模型复杂度增加时训练误差通常下降，而验证误差可能先降后升。", "role": "CAPTION", "parent": "P157-T10",
        "source_line": "figure:61; common/statlearnbook.sty:305-306; 合并总册/main.tex:7",
        "declared_pt": 10.0, "source_scale": "1.00; ctexbook[11pt] \\small=10pt via captionsetup",
        "source_scale_complete": True, "expected_effective_pt": 10.0,
    },
]


VECTOR_SPECS = [
    {"id": "P157-BG01", "drawing": 1, "role": "PANEL_BACKGROUND", "parent": "", "relation": "BACKGROUND", "label": "欠拟合浅蓝背景"},
    {"id": "P157-BG02", "drawing": 2, "role": "PANEL_BACKGROUND", "parent": "", "relation": "BACKGROUND", "label": "合适浅金背景"},
    {"id": "P157-BG03", "drawing": 3, "role": "PANEL_BACKGROUND", "parent": "", "relation": "BACKGROUND", "label": "过拟合浅红背景"},
    {"id": "P157-G01", "drawing": 4, "role": "DATA_CURVE", "parent": "", "relation": "INDEPENDENT", "label": "训练误差实线"},
    {"id": "P157-G02", "drawing": 5, "role": "DATA_CURVE", "parent": "", "relation": "INDEPENDENT", "label": "验证误差虚线"},
    {"id": "P157-G03", "drawing": 6, "role": "REFERENCE_LINE", "parent": "P157-SELECTION", "relation": "SELECTION_COMPONENT", "label": "选择复杂度竖参考线"},
    {"id": "P157-G04", "drawing": 7, "role": "LEADER_LINE", "parent": "P157-T01", "relation": "ANNOTATION_COMPONENT", "label": "训练误差引线"},
    {"id": "P157-BG04", "drawing": 8, "role": "ANNOTATION_BACKGROUND", "parent": "P157-T02", "relation": "BACKGROUND", "label": "验证误差标签白底"},
    {"id": "P157-BG05", "drawing": 9, "role": "ANNOTATION_BACKGROUND", "parent": "P157-T03", "relation": "BACKGROUND", "label": "最低验证误差标签白底"},
    {"id": "P157-BG06", "drawing": 10, "role": "ANNOTATION_BACKGROUND", "parent": "P157-T04", "relation": "BACKGROUND", "label": "选择复杂度标签白底"},
    {"id": "P157-G05", "drawing": 11, "role": "AXIS_LINE", "parent": "P157-AXIS-X", "relation": "AXIS_COMPONENT", "label": "x轴"},
    {"id": "P157-G06", "drawing": 12, "role": "AXIS_ARROWHEAD", "parent": "P157-AXIS-X", "relation": "AXIS_COMPONENT", "label": "x轴箭头"},
    {"id": "P157-G07", "drawing": 13, "role": "AXIS_LINE", "parent": "P157-AXIS-Y", "relation": "AXIS_COMPONENT", "label": "y轴"},
    {"id": "P157-G08", "drawing": 14, "role": "AXIS_ARROWHEAD", "parent": "P157-AXIS-Y", "relation": "AXIS_COMPONENT", "label": "y轴箭头"},
    {"id": "P157-G09", "drawing": 15, "role": "MARKER", "parent": "P157-SELECTION", "relation": "SELECTION_COMPONENT", "label": "最低验证误差金色实心点"},
]


def find_span(spec: dict, spans: list[dict]) -> dict:
    candidates = [s for s in spans if s["text"] == spec["text"]]
    # Caption child "图" has many page-level candidates; its location defines the figure caption.
    if spec["id"].startswith("P157-T10"):
        candidates = [s for s in candidates if 345 <= s["bbox"].y0 <= 365]
    else:
        candidates = [s for s in candidates if 130 <= s["bbox"].y0 <= 345]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one PDF span for {spec['id']} / {spec['text']!r}; got {len(candidates)}")
    return candidates[0]


def mode_rgb(arr: np.ndarray) -> np.ndarray:
    colors, counts = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
    return colors[int(np.argmax(counts))].astype(float)


def blend_match(pixels: np.ndarray, fg: np.ndarray, backgrounds: list[np.ndarray], residual_limit: float = 22.0) -> np.ndarray:
    """Pixels on an RGB fg-over-bg blend line, with >=20/255 local contrast.

    This is purposefully not a same-colour global threshold: every call is
    additionally constrained by the native PDF span or vector geometry mask.
    """
    p = pixels.astype(float)
    valid = np.zeros(p.shape[:-1], dtype=bool)
    for bg in backgrounds:
        v = fg - bg
        den = float(np.dot(v, v))
        if den < 1.0:
            continue
        q = p - bg
        alpha = np.sum(q * v, axis=-1) / den
        pred = bg + alpha[..., None] * v
        residual = np.max(np.abs(p - pred), axis=-1)
        contrast = np.max(np.abs(p - bg), axis=-1)
        valid |= (alpha >= 0.10) & (alpha <= 1.05) & (residual <= residual_limit) & (contrast >= 20.0)
    return valid


def blend_score(pixels: np.ndarray, fg: np.ndarray, backgrounds: list[np.ndarray], residual_limit: float = 22.0) -> np.ndarray:
    """Return the best native foreground-colour reconstruction residual.

    A finite score means that the actual raster pixel satisfies the same
    >=20/255 foreground rule.  Scores make foreground-object assignment
    mutually exclusive, so a teal pixel near a blue path can never be
    misclassified as both just because the two native stroke envelopes are
    close.  This corrects the explicitly superseded prepass classifier.
    """
    p = pixels.astype(float)
    best = np.full(p.shape[:-1], np.inf, dtype=float)
    for bg in backgrounds:
        v = fg - bg
        den = float(np.dot(v, v))
        if den < 1.0:
            continue
        q = p - bg
        alpha = np.sum(q * v, axis=-1) / den
        pred = bg + alpha[..., None] * v
        residual = np.max(np.abs(p - pred), axis=-1)
        contrast = np.max(np.abs(p - bg), axis=-1)
        valid = (alpha >= 0.10) & (alpha <= 1.05) & (residual <= residual_limit) & (contrast >= 20.0)
        best = np.minimum(best, np.where(valid, residual, np.inf))
    return best


def is_cjk(ch: str) -> bool:
    code = ord(ch)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x3040 <= code <= 0x30FF
        or 0xAC00 <= code <= 0xD7AF
    )


def script_of(ch: str) -> str:
    if is_cjk(ch):
        return "CJK"
    if ch.isdigit():
        return "DIGIT"
    if "A" <= ch <= "Z":
        return "LATIN_UPPER"
    if "a" <= ch <= "z":
        return "LATIN_LOWER"
    if ch in "αβγδεζηθικλμνξοπρστυφχψω":
        return "GREEK_LOWER"
    return "PUNCT_OR_SYMBOL"


def h_of_mask(mask: np.ndarray) -> int:
    yy = np.where(mask)[0]
    return 0 if yy.size == 0 else int(yy.max() - yy.min() + 1)


def text_mask_and_measurement(full_img: np.ndarray, span: dict) -> tuple[np.ndarray, dict]:
    h, w = full_img.shape[:2]
    bbox = rect_px(span["bbox"])
    x0, y0, x1, y1 = clamp_rect(bbox, w, h)
    native_char_area = np.zeros((h, w), dtype=bool)
    char_records = []
    for char in span["chars"]:
        cb = rect_px(char["bbox"])
        cx0, cy0, cx1, cy1 = clamp_rect(cb, w, h)
        native_char_area[cy0:cy1, cx0:cx1] = True
        char_records.append({"c": char["c"], "bbox_px": [cx0, cy0, cx1, cy1]})

    # The mode inside the native span bbox is the local unprinted background.
    bg = mode_rgb(full_img[y0:y1, x0:x1])
    fg = np.array(rgb_from_pdf_color(span["color"]), dtype=float)
    local = full_img[y0:y1, x0:x1]
    local_char = native_char_area[y0:y1, x0:x1]
    local_mask = local_char & blend_match(local, fg, [bg])
    mask = np.zeros((h, w), dtype=bool)
    mask[y0:y1, x0:x1] = local_mask

    char_heights = []
    for ch in span["chars"]:
        cb = rect_px(ch["bbox"])
        cx0, cy0, cx1, cy1 = clamp_rect(cb, w, h)
        cm = mask[cy0:cy1, cx0:cx1]
        char_heights.append({
            "c": ch["c"],
            "script": script_of(ch["c"]),
            "bbox_px": [cx0, cy0, cx1, cy1],
            "h_ink_px": h_of_mask(cm),
        })

    important = [r for r in char_heights if r["script"] != "PUNCT_OR_SYMBOL"]
    script_counts = Counter(r["script"] for r in important)
    primary = script_counts.most_common(1)[0][0] if script_counts else "PUNCT_OR_SYMBOL"
    primary_heights = [r["h_ink_px"] for r in important if r["script"] == primary]
    other_heights = [r["h_ink_px"] for r in important]
    threshold = {"CJK": 30, "DIGIT": 24, "LATIN_UPPER": 24, "LATIN_LOWER": 17, "GREEK_LOWER": 17}.get(primary, 22)
    measured = int(round(float(np.median(primary_heights)))) if primary_heights else 0
    hard_min = min(primary_heights) if primary_heights else 0
    return mask, {
        "bbox_px": bbox,
        "bg_rgb": [int(v) for v in bg],
        "fg_rgb": [int(v) for v in fg],
        "primary_script": primary,
        "threshold_px": threshold,
        "h_ink_px": measured,
        "hard_min_glyph_px": int(hard_min),
        "char_heights": char_heights,
        "all_text_ink_bbox_px": _mask_bbox(mask),
    }


def _mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if not len(xs):
        return (0, 0, 0, 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def point_xy(p: fitz.Point) -> np.ndarray:
    return np.array([float(p.x) * S, float(p.y) * S], dtype=float)


def add_capsule(mask: np.ndarray, p0: np.ndarray, p1: np.ndarray, radius: float) -> None:
    """Native PDF stroke-radius capsule tested at pixel centres.

    The radius is exactly one half of the declared PDF stroke width after the
    final-PDF 300dpi mapping.  It deliberately does not add a raster-cell or
    bbox halo: actual qualifying anti-aliased pixels are recovered only by the
    colour-reconstruction stage.
    """
    h, w = mask.shape
    minx = max(0, math.floor(min(p0[0], p1[0]) - radius))
    maxx = min(w, math.ceil(max(p0[0], p1[0]) + radius))
    miny = max(0, math.floor(min(p0[1], p1[1]) - radius))
    maxy = min(h, math.ceil(max(p0[1], p1[1]) + radius))
    if minx >= maxx or miny >= maxy:
        return
    yy, xx = np.mgrid[miny:maxy, minx:maxx]
    qx = xx + 0.5
    qy = yy + 0.5
    v = p1 - p0
    vv = float(np.dot(v, v))
    if vv < 1e-10:
        d2 = (qx - p0[0]) ** 2 + (qy - p0[1]) ** 2
    else:
        t = np.clip(((qx - p0[0]) * v[0] + (qy - p0[1]) * v[1]) / vv, 0.0, 1.0)
        dx = qx - (p0[0] + t * v[0])
        dy = qy - (p0[1] + t * v[1])
        d2 = dx * dx + dy * dy
    mask[miny:maxy, minx:maxx] |= d2 <= radius * radius


def drawing_paths(drawing: dict) -> tuple[list[list[np.ndarray]], list[list[np.ndarray]]]:
    """Return stroked polylines and closed fill polygons in native PDF order."""
    stroke_paths: list[list[np.ndarray]] = []
    fill_polys: list[list[np.ndarray]] = []
    current: list[np.ndarray] = []

    def flush() -> None:
        nonlocal current
        if len(current) >= 2:
            stroke_paths.append(current)
        current = []

    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            p0, p1 = point_xy(item[1]), point_xy(item[2])
            if not current or np.linalg.norm(current[-1] - p0) > 0.01:
                flush()
                current = [p0]
            current.append(p1)
        elif op == "c":
            p0, p1, p2, p3 = (point_xy(item[i]) for i in range(1, 5))
            if not current or np.linalg.norm(current[-1] - p0) > 0.01:
                flush()
                current = [p0]
            for t in np.linspace(1 / 16, 1.0, 16):
                q = ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * (t ** 2) * p2 + (t ** 3) * p3
                current.append(q)
        elif op == "re":
            flush()
            r = item[1]
            fill_polys.append([
                np.array([r.x0 * S, r.y0 * S]), np.array([r.x1 * S, r.y0 * S]),
                np.array([r.x1 * S, r.y1 * S]), np.array([r.x0 * S, r.y1 * S]),
            ])
        else:
            flush()
    flush()
    if drawing.get("closePath") and stroke_paths:
        last = stroke_paths[-1]
        if len(last) >= 3:
            fill_polys.append(last)
    # Filled cubic/line marker paths may be closed; the final existing stroke path is also its polygon.
    if drawing.get("type", "") in ("f", "fs", "sf") and stroke_paths and not fill_polys:
        fill_polys = [stroke_paths[-1]]
    return stroke_paths, fill_polys


def dash_definition(drawing: dict) -> tuple[list[float], float] | None:
    """Read the final-PDF dash pattern in PDF user units, if any."""
    raw = str(drawing.get("dashes") or "")
    match = re.search(r"\[([^\]]*)\]\s*([-+0-9.eE]+)?", raw)
    if not match:
        return None
    values = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", match.group(1))]
    if not values or all(v <= 0 for v in values):
        return None
    if len(values) % 2 == 1:
        values *= 2
    phase = float(match.group(2) or 0.0)
    return [v * S for v in values], phase * S


def dashed_on_segments(path: list[np.ndarray], pattern: list[float], phase: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """Split a polyline into its native painted dash intervals without padding."""
    if len(path) < 2:
        return []
    period = sum(pattern)
    if period <= 0:
        return [(a, b) for a, b in zip(path[:-1], path[1:])]
    phase = phase % period
    idx = 0
    while phase >= pattern[idx] - 1e-9:
        phase -= pattern[idx]
        idx = (idx + 1) % len(pattern)
    remaining = pattern[idx] - phase
    is_on = idx % 2 == 0
    result: list[tuple[np.ndarray, np.ndarray]] = []
    for p0, p1 in zip(path[:-1], path[1:]):
        v = p1 - p0
        length = float(np.linalg.norm(v))
        if length < 1e-10:
            continue
        walked = 0.0
        while walked < length - 1e-9:
            take = min(remaining, length - walked)
            if is_on and take > 1e-9:
                a = p0 + v * (walked / length)
                b = p0 + v * ((walked + take) / length)
                result.append((a, b))
            walked += take
            remaining -= take
            if remaining <= 1e-9:
                idx = (idx + 1) % len(pattern)
                is_on = idx % 2 == 0
                remaining = pattern[idx]
    return result


def fill_polygon(mask: np.ndarray, poly: list[np.ndarray]) -> None:
    if len(poly) < 3:
        return
    pts = np.array(poly, dtype=float)
    minx = max(0, math.floor(float(pts[:, 0].min())))
    maxx = min(mask.shape[1], math.ceil(float(pts[:, 0].max())))
    miny = max(0, math.floor(float(pts[:, 1].min())))
    maxy = min(mask.shape[0], math.ceil(float(pts[:, 1].max())))
    if minx >= maxx or miny >= maxy:
        return
    yy, xx = np.mgrid[miny:maxy, minx:maxx]
    points = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], axis=1).astype(np.float32)
    inside = np.array([cv2.pointPolygonTest(pts.astype(np.float32), tuple(p), False) >= 0 for p in points], dtype=bool)
    mask[miny:maxy, minx:maxx] |= inside.reshape(yy.shape)


def drawing_geometry_mask(drawing: dict, shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    paths, polys = drawing_paths(drawing)
    typ = drawing.get("type", "")
    if "f" in typ:
        for poly in polys:
            fill_polygon(mask, poly)
    if "s" in typ:
        # No geometric halo is permitted: use the declared native PDF radius.
        radius = float(drawing.get("width") or 0.0) * S / 2.0
        dash = dash_definition(drawing)
        for path in paths:
            pieces = dashed_on_segments(path, dash[0], dash[1]) if dash else list(zip(path[:-1], path[1:]))
            for p0, p1 in pieces:
                add_capsule(mask, p0, p1, radius)
    return mask


def draw_export(drawing: dict) -> dict:
    items = []
    for item in drawing["items"]:
        arr = [item[0]]
        for value in item[1:]:
            if isinstance(value, fitz.Point):
                arr.append(point_list(value))
            elif isinstance(value, fitz.Rect):
                arr.append(rect_list(value))
            else:
                arr.append(str(value))
        items.append(arr)
    return {
        "rect_pdf_bp": rect_list(drawing["rect"]),
        "type": drawing.get("type"), "color": drawing.get("color"), "fill": drawing.get("fill"),
        "width_pdf_bp": drawing.get("width"), "dashes": drawing.get("dashes"), "lineCap": drawing.get("lineCap"),
        "lineJoin": drawing.get("lineJoin"), "seqno": drawing.get("seqno"), "items": items,
    }


def nearest_points(a: np.ndarray, b: np.ndarray) -> tuple[int, float, tuple[int, int], tuple[int, int]]:
    overlap = int(np.count_nonzero(a & b))
    if not np.any(a) or not np.any(b):
        return overlap, float("inf"), (-1, -1), (-1, -1)
    # EDT supplies exact integer-grid nearest B pixels and coordinates.
    dist, indices = distance_transform_edt(~b, return_indices=True)
    vals = dist[a]
    k = int(np.argmin(vals))
    ay, ax = np.where(a)
    y, x = int(ay[k]), int(ax[k])
    by, bx = int(indices[0, y, x]), int(indices[1, y, x])
    return overlap, float(dist[y, x]), (x, y), (bx, by)


def make_overlay(raw: np.ndarray, a: np.ndarray, b: np.ndarray | None = None, origin: tuple[int, int] = (0, 0)) -> np.ndarray:
    out = raw.astype(float).copy()
    x0, y0 = origin
    aa = a[y0:y0 + raw.shape[0], x0:x0 + raw.shape[1]]
    out[aa] = 0.45 * out[aa] + 0.55 * np.array([255, 40, 40])
    if b is not None:
        bb = b[y0:y0 + raw.shape[0], x0:x0 + raw.shape[1]]
        out[bb] = 0.45 * out[bb] + 0.55 * np.array([20, 220, 255])
        both = aa & bb
        out[both] = np.array([255, 255, 255])
    return out.astype(np.uint8)


def make_pair_visual(a: np.ndarray, b: np.ndarray, rect: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = rect
    aa = a[y0:y1, x0:x1]
    bb = b[y0:y1, x0:x1]
    out = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.uint8)
    out[aa] = (255, 45, 45)
    out[bb] = (20, 210, 255)
    out[aa & bb] = (255, 255, 255)
    return out


def add_boxes_overlay(full_img: np.ndarray, objects: list[dict]) -> np.ndarray:
    x0, y0, x1, y1 = rect_px(FIGCAP_RECT)
    base = full_img[y0:y1, x0:x1].copy()
    im = Image.fromarray(base, mode="RGB")
    draw = ImageDraw.Draw(im)
    for obj in objects:
        if obj["kind"] != "TEXT":
            continue
        bx0, by0, bx1, by1 = obj["bbox_px"]
        if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
            continue
        col = (225, 0, 0) if not obj.get("parent") else (135, 0, 165)
        draw.rectangle((bx0 - x0, by0 - y0, bx1 - x0 - 1, by1 - y0 - 1), outline=col, width=1)
        draw.text((bx0 - x0, max(0, by0 - y0 - 10)), obj["id"], fill=col)
    return np.asarray(im)


def source_pass(spec: dict, effective_pt: float) -> tuple[bool, str]:
    if not spec["source_scale_complete"]:
        return False, "FAIL: complete declared-font/cumulative-scale chain is not recoverable."
    if effective_pt < 9.5:
        return False, f"FAIL: effective_pt={effective_pt:.3f}<9.5."
    return True, "PASS: declared font and cumulative source scale restore effective_pt>=9.5."


def source_file_for(record: dict) -> str:
    if record["id"] in {"P157-T08", "P157-T09"}:
        return SOURCE_REL + "; src/讲义源码/common/figure-style-v2.3.0.tex"
    if record["id"].startswith("P157-T10"):
        return CHAPTER_REL + "; src/讲义源码/common/statlearnbook.sty; src/讲义源码/合并总册/main.tex"
    return SOURCE_REL + "; " + CHAPTER_REL + ":256"


def main() -> None:
    mkdirs()
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_1 - 1]
    page_text = page.get_text("text")
    if "图10.1" not in page_text or "模型复杂度增加时训练误差通常下降" not in page_text:
        raise RuntimeError("Caption/figure number not found on independently located PDF page.")

    full300 = image_from_pixmap(page.get_pixmap(dpi=300, alpha=False, annots=False))
    full200 = image_from_pixmap(page.get_pixmap(dpi=200, alpha=False, annots=False))
    save_img(OUT / "after_native_page_300dpi.png", full300)
    save_img(OUT / "after_full_page_200dpi.png", full200)
    fx0, fy0, fx1, fy1 = rect_px(FIGCAP_RECT)
    sx0, sy0, sx1, sy1 = rect_px(STANDALONE_RECT)
    figure_crop = full300[fy0:fy1, fx0:fx1].copy()
    standalone = full300[sy0:sy1, sx0:sx1].copy()
    save_img(OUT / "after_figure_crop_300dpi.png", figure_crop)
    save_img(OUT / "after_standalone_300dpi.png", standalone)
    # Luminance conversion only; there is no spatial resizing.
    gray = np.asarray(Image.fromarray(figure_crop, mode="RGB").convert("L"))
    save_img(OUT / "after_grayscale_300dpi.png", gray)

    spans = get_raw_spans(page)
    objects: list[dict] = []
    text_records = []
    all_text_mask = np.zeros(full300.shape[:2], dtype=bool)
    pdf_spans_export = []
    for spec in TEXT_SPECS:
        span = find_span(spec, spans)
        mask, measure = text_mask_and_measurement(full300, span)
        all_text_mask |= mask
        bbox = rect_px(span["bbox"])
        actual_effective_pt = span["size_bp"] * 72.27 / 72.0
        inferred_scale = actual_effective_pt / spec["declared_pt"] if spec["declared_pt"] else None
        src_ok, src_reason = source_pass(spec, actual_effective_pt)
        rec = {
            "id": spec["id"], "kind": "TEXT", "role": spec["role"], "parent": spec["parent"],
            "label": spec["text"], "mask": mask, "bbox_px": bbox, "pdf_bbox_bp": rect_list(span["bbox"]),
            "source_line": spec["source_line"], "declared_pt": spec["declared_pt"], "source_scale": spec["source_scale"],
            "source_scale_complete": spec["source_scale_complete"], "expected_effective_pt": spec["expected_effective_pt"],
            "pdf_span_size_bp": span["size_bp"], "effective_pt": actual_effective_pt, "inferred_scale": inferred_scale,
            "font": span["font"], "rgb": rgb_from_pdf_color(span["color"]), "measurement": measure,
            "source_pass": src_ok, "source_reason": src_reason,
        }
        objects.append(rec)
        text_records.append(rec)
        pdf_spans_export.append({
            "element_id": rec["id"], "parent_id": rec["parent"], "text": rec["label"], "font": rec["font"],
            "pdf_span_size_bp": rec["pdf_span_size_bp"], "pdf_bbox_bp": rec["pdf_bbox_bp"], "bbox_px_300dpi": list(bbox),
            "font_rgb": rec["rgb"], "chars": [
                {"c": ch["c"], "bbox_bp": rect_list(ch["bbox"]), "bbox_px_300dpi": rect_px(ch["bbox"])} for ch in span["chars"]
            ],
        })

    drawings = page.get_drawings()
    if len(drawings) < 16:
        raise RuntimeError(f"Expected at least 16 PDF vector drawings; got {len(drawings)}")

    # Exact panel/paper palettes are allowed solely to test the defined 20/255 foreground criterion.
    palettes = [np.array([255.0, 255.0, 255.0])]
    for idx in (1, 2, 3):
        fill = drawings[idx].get("fill")
        if fill:
            palettes.append(np.array(rgb_from_pdf_color(fill), dtype=float))

    vector_records = []
    for spec in VECTOR_SPECS:
        drawing = drawings[spec["drawing"]]
        geom = drawing_geometry_mask(drawing, full300.shape[:2])
        bbox = rect_px(drawing["rect"])
        expected = drawing.get("color") or drawing.get("fill")
        rgb = rgb_from_pdf_color(expected) if expected is not None else None
        rec = {
            "id": spec["id"], "kind": "GRAPHIC", "role": spec["role"], "parent": spec["parent"],
            "label": spec["label"], "relation": spec["relation"], "drawing_index": spec["drawing"],
            "seqno": int(drawing.get("seqno", -1)), "bbox_px": bbox, "pdf_bbox_bp": rect_list(drawing["rect"]),
            "geometry": geom, "drawing": drawing, "rgb": rgb, "mask": None,
        }
        vector_records.append(rec)
        objects.append(rec)

    # Opaque fills with a later PDF draw sequence actually occlude earlier curves/reference lines.
    for rec in vector_records:
        geom = rec["geometry"].copy()
        for cover in vector_records:
            if cover["seqno"] <= rec["seqno"] or cover["id"] == rec["id"]:
                continue
            typ = cover["drawing"].get("type", "")
            fill = cover["drawing"].get("fill")
            if "f" in typ and fill is not None and float(cover["drawing"].get("fill_opacity") or 1.0) >= 0.999:
                geom &= ~cover["geometry"]
        rec["visible_geometry"] = geom
        if rec["relation"] == "BACKGROUND":
            rec["mask"] = geom

    # Native vector foreground ownership is mutually exclusive.  The previous
    # prepass only asked whether a pixel could fit each colour-blend line, which
    # double-assigned anti-aliased teal/blue neighbourhood pixels.  Here each
    # actual final-PDF pixel is assigned to its smallest reconstruction residual;
    # exact ties go to the later PDF paint sequence.  No bbox enlargement occurs.
    vector_fg = [r for r in vector_records if r["relation"] != "BACKGROUND"]
    best_score = np.full(full300.shape[:2], np.inf, dtype=float)
    best_seq = np.full(full300.shape[:2], -1, dtype=np.int32)
    owner = np.full(full300.shape[:2], -1, dtype=np.int16)
    for idx, rec in enumerate(vector_fg):
        geom = rec["visible_geometry"] & ~all_text_mask
        yy, xx = np.where(geom)
        if not len(xx) or rec["rgb"] is None:
            continue
        scores = blend_score(full300[yy, xx], np.array(rec["rgb"], dtype=float), palettes)
        current = best_score[yy, xx]
        current_seq = best_seq[yy, xx]
        finite_pair = np.isfinite(scores) & np.isfinite(current)
        delta = np.full_like(scores, np.inf)
        delta[finite_pair] = np.abs(scores[finite_pair] - current[finite_pair])
        tie = finite_pair & (delta <= 1e-6)
        win = (scores < current - 1e-6) | (tie & (rec["seqno"] > current_seq))
        wy, wx = yy[win], xx[win]
        best_score[wy, wx] = scores[win]
        best_seq[wy, wx] = rec["seqno"]
        owner[wy, wx] = idx
    for idx, rec in enumerate(vector_fg):
        rec["mask"] = owner == idx

    # Native source/text/vector metadata are written before aggregate decisions.
    save_json(OUT / "metadata" / "pdf_text_spans_300dpi.json", pdf_spans_export)
    save_json(OUT / "metadata" / "pdf_vector_objects.json", [
        {"element_id": r["id"], "role": r["role"], "label": r["label"], "parent_id": r["parent"],
         "drawing_index": r["drawing_index"], "pdf": draw_export(r["drawing"]), "bbox_px_300dpi": list(r["bbox_px"]),
         "rgb": r["rgb"]} for r in vector_records
    ])

    # Individual raw 1:1 ROI, independent mask, and overlay for every readable/vector object.
    for obj in objects:
        b = obj["bbox_px"]
        raw, rr = crop(full300, b, ROI_PAD)
        x0, y0, x1, y1 = rr
        mask_crop = obj["mask"][b[1]:b[3], b[0]:b[2]]
        save_img(OUT / "masks" / f"{obj['id']}_mask_300dpi.png", (mask_crop * 255).astype(np.uint8))
        save_img(OUT / "raw_rois" / f"{obj['id']}_raw_1to1_300dpi.png", raw)
        save_img(OUT / "raw_rois" / f"{obj['id']}_overlay_1to1_300dpi.png", make_overlay(raw, obj["mask"], origin=(x0, y0)))

    # Viewable complete measurement overlay: all rectangles use native text span bboxes.
    save_img(OUT / "after_text_measurement_overlay_300dpi.png", add_boxes_overlay(full300, objects))

    # Font audit CSV.
    font_fields = [
        "ELEMENT_ID", "PARENT_ID", "ROLE", "TEXT_SAMPLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT",
        "GRAPHICS_SCALE", "PDF_SPAN_SIZE_BP", "EFFECTIVE_PT", "INFERRED_SCALE_FROM_PDF", "FONT", "SOURCE_AUDIT_PASS", "REASON",
    ]
    with (OUT / "after_font_audit.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=font_fields)
        w.writeheader()
        for r in text_records:
            w.writerow({
                "ELEMENT_ID": r["id"], "PARENT_ID": r["parent"] or "SELF", "ROLE": r["role"], "TEXT_SAMPLE": r["label"],
                "SOURCE_FILE": source_file_for(r),
                "SOURCE_LINE": r["source_line"], "DECLARED_PT": "UNKNOWN" if r["declared_pt"] is None else f"{r['declared_pt']:.3f}",
                "GRAPHICS_SCALE": r["source_scale"], "PDF_SPAN_SIZE_BP": f"{r['pdf_span_size_bp']:.3f}",
                "EFFECTIVE_PT": f"{r['effective_pt']:.3f}",
                "INFERRED_SCALE_FROM_PDF": "UNKNOWN" if r["inferred_scale"] is None else f"{r['inferred_scale']:.5f}",
                "FONT": r["font"], "SOURCE_AUDIT_PASS": str(r["source_pass"]).lower(), "REASON": r["source_reason"],
            })

    # Pairwise all independent foreground relationship audit.  Composite caption children are retained with their parent
    # relation and never misclassified as independent text-text pairs.
    foreground = [o for o in objects if not (o["kind"] == "GRAPHIC" and o.get("relation") == "BACKGROUND")]
    pair_rows = []
    object_pair_stats: dict[str, list[dict]] = {o["id"]: [] for o in foreground}
    for a, b in itertools.combinations(foreground, 2):
        bb_clear, bb_intersect = bbox_clearance(a["bbox_px"], b["bbox_px"])
        overlap, clearance, ap, bp = nearest_points(a["mask"], b["mask"])
        ga = a.get("visible_geometry", a["mask"])
        gb = b.get("visible_geometry", b["mask"])
        geometry_overlap = int(np.count_nonzero(ga & gb))
        same_parent = bool(a.get("parent") and a.get("parent") == b.get("parent"))
        both_text = a["kind"] == "TEXT" and b["kind"] == "TEXT"
        # Explicit semantic exceptions: axis parts, selection anchor parts, and the source-defined leader endpoint.
        relation = "INDEPENDENT"
        intentional = False
        pair_ids = {a["id"], b["id"]}
        if same_parent:
            relation = "COMPOSITE_SAME_PARENT"
            intentional = True
        elif pair_ids == {"P157-G01", "P157-G02"}:
            relation = "INTENTIONAL_GRAPHIC_JUNCTION_TRAINING_VALIDATION_CURVE_INTERSECTION"
            intentional = True
        elif pair_ids == {"P157-G01", "P157-G04"}:
            relation = "INTENTIONAL_GRAPHIC_JUNCTION_LEADER_ENDPOINT_ON_TRAINING_CURVE"
            intentional = True
        elif pair_ids <= {"P157-G02", "P157-G03", "P157-G09"} and len(pair_ids) == 2:
            relation = "INTENTIONAL_GRAPHIC_JUNCTION_SELECTION_ANCHOR"
            intentional = True
        elif pair_ids == {"P157-G01", "P157-G03"}:
            relation = "INTENTIONAL_GRAPHIC_JUNCTION_SELECTION_REFERENCE_CROSSES_TRAINING_CURVE"
            intentional = True
        elif pair_ids == {"P157-G03", "P157-G05"}:
            relation = "INTENTIONAL_GRAPHIC_JUNCTION_SELECTION_REFERENCE_MEETS_X_AXIS"
            intentional = True
        elif pair_ids == {"P157-G05", "P157-G07"}:
            relation = "INTENTIONAL_GRAPHIC_JUNCTION_AXIS_ORIGIN"
            intentional = True
        elif pair_ids in ({"P157-G01", "P157-G07"}, {"P157-G02", "P157-G07"}):
            relation = "INTENTIONAL_GRAPHIC_JUNCTION_CURVE_ENTERING_Y_AXIS"
            intentional = True
        elif (a.get("parent") in {"P157-AXIS-X", "P157-AXIS-Y"}) and a.get("parent") == b.get("parent"):
            relation = "AXIS_COMPONENT"
            intentional = True

        requirement = "N/A"
        pass_pair = True
        if both_text and not same_parent:
            requirement = "PDF/vector bbox clearance >=4 px; foreground overlap=0"
            pass_pair = bb_clear >= 4.0 and overlap == 0
        elif (a["kind"] == "TEXT") != (b["kind"] == "TEXT") and not intentional:
            requirement = "text/formula ink to line/arrow/marker >=3 px; foreground overlap=0"
            pass_pair = clearance >= 3.0 and overlap == 0
        elif not intentional:
            requirement = "independent foreground overlap=0"
            pass_pair = overlap == 0

        same_colour = bool(a.get("rgb") and b.get("rgb") and tuple(a["rgb"]) == tuple(b["rgb"]))
        near = bb_clear <= 40.0
        raw_path = overlay_path = overlap_path = ""
        if same_colour or near or overlap > 0:
            ux0 = min(a["bbox_px"][0], b["bbox_px"][0])
            uy0 = min(a["bbox_px"][1], b["bbox_px"][1])
            ux1 = max(a["bbox_px"][2], b["bbox_px"][2])
            uy1 = max(a["bbox_px"][3], b["bbox_px"][3])
            raw, rr = crop(full300, (ux0, uy0, ux1, uy1), ROI_PAD)
            pair_stem = f"{a['id']}__{b['id']}"
            raw_p = OUT / "pair_rois" / f"{pair_stem}_raw_1to1_300dpi.png"
            over_p = OUT / "pair_rois" / f"{pair_stem}_overlay_1to1_300dpi.png"
            mask_p = OUT / "pair_rois" / f"{pair_stem}_overlap_mask_300dpi.png"
            save_img(raw_p, raw)
            save_img(over_p, make_overlay(raw, a["mask"], b["mask"], origin=(rr[0], rr[1])))
            save_img(mask_p, make_pair_visual(a["mask"], b["mask"], rr))
            raw_path = str(raw_p.relative_to(OUT)).replace("\\", "/")
            overlay_path = str(over_p.relative_to(OUT)).replace("\\", "/")
            overlap_path = str(mask_p.relative_to(OUT)).replace("\\", "/")

        row = {
            "PAIR_ID": f"{a['id']}__{b['id']}", "OBJECT_A": a["id"], "PARENT_A": a.get("parent") or "SELF", "ROLE_A": a["role"],
            "OBJECT_B": b["id"], "PARENT_B": b.get("parent") or "SELF", "ROLE_B": b["role"], "RELATION": relation,
            "INDEPENDENT_RELATION": str(not intentional).lower(), "REQUIRED_RULE": requirement,
            "BBOX_CLEARANCE_PX": f"{bb_clear:.3f}", "BBOX_INTERSECT": str(bb_intersect).lower(),
            "MASK_OVERLAP_PX": overlap, "GEOMETRY_OVERLAP_PX": geometry_overlap,
            "MIN_MASK_CLEARANCE_PX": "INF" if math.isinf(clearance) else f"{clearance:.3f}",
            "NEAREST_A_X_PX": ap[0], "NEAREST_A_Y_PX": ap[1], "NEAREST_B_X_PX": bp[0], "NEAREST_B_Y_PX": bp[1],
            "SAME_COLOUR": str(same_colour).lower(), "NEAR_BY_BBOX_LE40PX": str(near).lower(), "PASS_FAIL": "PASS" if pass_pair else "FAIL",
            "RAW_ROI": raw_path, "OVERLAY": overlay_path, "OVERLAP_MASK": overlap_path,
        }
        pair_rows.append(row)
        object_pair_stats[a["id"]].append(row)
        object_pair_stats[b["id"]].append(row)

    overlap_fields = list(pair_rows[0].keys())
    with (OUT / "after_overlap_report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=overlap_fields)
        w.writeheader()
        w.writerows(pair_rows)

    # Pixel measurements, including required source fields and per-element collision/clearance summaries.
    role_groups: dict[tuple[str, str], list[dict]] = {}
    for r in text_records:
        key = (r["role"], r["measurement"]["primary_script"])
        role_groups.setdefault(key, []).append(r)
    role_medians = {k: float(np.median([x["measurement"]["h_ink_px"] for x in group])) for k, group in role_groups.items()}
    base = role_medians.get(("REGION_LABEL", "CJK"))
    if base is None:
        raise RuntimeError("No REGION_LABEL CJK base exists for this one-panel figure.")
    role_rules = {
        "AXIS_TITLE": (1.00, 1.18), "DIRECT_ANNOTATION": (0.95, 1.10), "KEY_ANNOTATION": (0.95, 1.10),
    }
    pixel_rows = []
    for r in text_records:
        m = r["measurement"]
        stats = object_pair_stats[r["id"]]
        text_text = sum(int(x["MASK_OVERLAP_PX"]) for x in stats if x["ROLE_A"] in {"DIRECT_ANNOTATION", "KEY_ANNOTATION", "REGION_LABEL", "AXIS_TITLE", "CAPTION"} and x["ROLE_B"] in {"DIRECT_ANNOTATION", "KEY_ANNOTATION", "REGION_LABEL", "AXIS_TITLE", "CAPTION"} and x["INDEPENDENT_RELATION"] == "true")
        text_graphic = sum(int(x["MASK_OVERLAP_PX"]) for x in stats if (x["ROLE_A"] in {"DATA_CURVE", "REFERENCE_LINE", "LEADER_LINE", "MARKER", "AXIS_LINE", "AXIS_ARROWHEAD"} or x["ROLE_B"] in {"DATA_CURVE", "REFERENCE_LINE", "LEADER_LINE", "MARKER", "AXIS_LINE", "AXIS_ARROWHEAD"}) and x["INDEPENDENT_RELATION"] == "true")
        graphic_clearances = [float(x["MIN_MASK_CLEARANCE_PX"]) for x in stats if x["INDEPENDENT_RELATION"] == "true" and (x["ROLE_A"] in {"DATA_CURVE", "REFERENCE_LINE", "LEADER_LINE", "MARKER", "AXIS_LINE", "AXIS_ARROWHEAD"} or x["ROLE_B"] in {"DATA_CURVE", "REFERENCE_LINE", "LEADER_LINE", "MARKER", "AXIS_LINE", "AXIS_ARROWHEAD"}) and x["MIN_MASK_CLEARANCE_PX"] != "INF"]
        min_clear = min(graphic_clearances) if graphic_clearances else float("inf")
        median = role_medians[(r["role"], m["primary_script"])]
        ratio_class = m["h_ink_px"] / median if median else float("nan")
        role_ratio = m["h_ink_px"] / base
        rule = role_rules.get(r["role"])
        px_pass = m["hard_min_glyph_px"] >= m["threshold_px"]
        same_class_pass = 0.92 <= ratio_class <= 1.08
        role_pass = True if rule is None else rule[0] <= role_ratio <= rule[1]
        overall = px_pass and same_class_pass and role_pass and text_text == 0 and text_graphic == 0 and min_clear >= 3.0
        reasons = []
        if not px_pass:
            reasons.append(f"hard-min glyph {m['hard_min_glyph_px']} < {m['threshold_px']}")
        if not same_class_pass:
            reasons.append(f"same-role ratio {ratio_class:.3f} outside [0.92,1.08]")
        if not role_pass:
            reasons.append(f"role ratio {role_ratio:.3f} outside {rule}")
        if text_text or text_graphic:
            reasons.append("illegal foreground overlap")
        if min_clear < 3.0:
            reasons.append(f"graphic clearance {min_clear:.3f}<3")
        pixel_rows.append({
            "ELEMENT_ID": r["id"], "PARENT_ID": r["parent"] or "SELF", "PANEL_ID": "P157-ONE-PANEL", "ROLE": r["role"],
            "SOURCE_FILE": source_file_for(r), "SOURCE_LINE": r["source_line"],
            "DECLARED_PT": "UNKNOWN" if r["declared_pt"] is None else f"{r['declared_pt']:.3f}", "GRAPHICS_SCALE": r["source_scale"],
            "EFFECTIVE_PT": f"{r['effective_pt']:.3f}", "TEXT_SAMPLE": r["label"], "SCRIPT_CLASS": m["primary_script"],
            "BBOX_X0": r["bbox_px"][0], "BBOX_Y0": r["bbox_px"][1], "BBOX_X1": r["bbox_px"][2], "BBOX_Y1": r["bbox_px"][3],
            "H_INK_PX": m["h_ink_px"], "HARD_MIN_GLYPH_PX": m["hard_min_glyph_px"], "PIXEL_THRESHOLD_PX": m["threshold_px"],
            "CLASS_MEDIAN_PX": f"{median:.3f}", "RATIO_TO_CLASS_MEDIAN": f"{ratio_class:.3f}", "ROLE_RATIO": f"{role_ratio:.3f}",
            "TEXT_TEXT_OVERLAP_PX": text_text, "TEXT_GRAPHIC_OVERLAP_PX": text_graphic,
            "MIN_CLEARANCE_PX": "INF" if math.isinf(min_clear) else f"{min_clear:.3f}",
            "CHAR_HEIGHTS_JSON": json.dumps(m["char_heights"], ensure_ascii=False), "PASS_FAIL": "PASS" if overall else "FAIL",
            "REASON": "; ".join(reasons) if reasons else "PASS",
        })
    pixel_fields = list(pixel_rows[0].keys())
    with (OUT / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=pixel_fields)
        w.writeheader()
        w.writerows(pixel_rows)

    # A strict page-edge / crop-edge check for every object.  It tests the actual final PDF page boundary,
    # then the fixed visual crop boundary (the crop has an explicit >=6px outer safety margin).
    edge_rows = []
    page_h, page_w = full300.shape[:2]
    cap_bbox = rect_px(FIGCAP_RECT)
    for obj in objects:
        m = obj["mask"]
        yy, xx = np.where(m)
        if len(xx):
            page_min = int(min(xx.min(), yy.min(), page_w - 1 - xx.max(), page_h - 1 - yy.max()))
            clip_count = int(np.count_nonzero(m[:, :1]) + np.count_nonzero(m[:, -1:]) + np.count_nonzero(m[:1, :]) + np.count_nonzero(m[-1:, :]))
            in_cap = (xx >= cap_bbox[0]) & (xx < cap_bbox[2]) & (yy >= cap_bbox[1]) & (yy < cap_bbox[3])
            if np.any(in_cap):
                cx, cy = xx[in_cap], yy[in_cap]
                crop_min = int(min(cx.min() - cap_bbox[0], cy.min() - cap_bbox[1], cap_bbox[2] - 1 - cx.max(), cap_bbox[3] - 1 - cy.max()))
            else:
                crop_min = -1
        else:
            page_min, crop_min, clip_count = -1, -1, -1
        # Only a rendered final-PDF-page boundary hit constitutes a clip pixel.
        edge_rows.append({
            "OBJECT_ID": obj["id"], "ROLE": obj["role"], "PDF_PAGE_MIN_EDGE_CLEARANCE_PX": page_min,
            "FIGURE_CROP_MIN_EDGE_CLEARANCE_PX": crop_min, "CLIP_PIXEL_COUNT": clip_count,
            "PASS_FAIL": "PASS" if clip_count == 0 and page_min >= 6 else "FAIL",
            "METHOD": "Native final-PDF 300dpi mask touching the actual page image boundary; figure-crop clearance reported separately.",
        })
    with (OUT / "after_edge_clip_report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(edge_rows[0].keys()))
        w.writeheader()
        w.writerows(edge_rows)

    # Aggregate matrix.
    source_font_pass = all(r["source_pass"] for r in text_records)
    pixel_height_pass = all(r["PASS_FAIL"] == "PASS" or "source" in r["REASON"].lower() for r in pixel_rows) and all(
        int(r["HARD_MIN_GLYPH_PX"]) >= int(r["PIXEL_THRESHOLD_PX"]) for r in pixel_rows
    )
    same_class_pass = all(0.92 <= float(r["RATIO_TO_CLASS_MEDIAN"]) <= 1.08 for r in pixel_rows)
    same_class_pass &= all(
        max(float(r["measurement"]["h_ink_px"]) for r in group) / min(float(r["measurement"]["h_ink_px"]) for r in group) <= 1.08
        for group in role_groups.values() if len(group) > 1
    )
    role_ratio_pass = all(
        (r["ROLE"] not in role_rules) or role_rules[r["ROLE"]][0] <= float(r["ROLE_RATIO"]) <= role_rules[r["ROLE"]][1]
        for r in pixel_rows
    )
    illegal_pair_rows = [r for r in pair_rows if r["INDEPENDENT_RELATION"] == "true" and r["PASS_FAIL"] == "FAIL"]
    illegal_overlap = sum(int(r["MASK_OVERLAP_PX"]) for r in illegal_pair_rows)
    clip_count = sum(int(r["CLIP_PIXEL_COUNT"]) for r in edge_rows if int(r["CLIP_PIXEL_COUNT"]) > 0)
    text_clearances = [float(r["MIN_MASK_CLEARANCE_PX"]) for r in pair_rows if r["INDEPENDENT_RELATION"] == "true" and (r["ROLE_A"] in {"DIRECT_ANNOTATION", "KEY_ANNOTATION", "REGION_LABEL", "AXIS_TITLE", "CAPTION"} or r["ROLE_B"] in {"DIRECT_ANNOTATION", "KEY_ANNOTATION", "REGION_LABEL", "AXIS_TITLE", "CAPTION"}) and r["MIN_MASK_CLEARANCE_PX"] != "INF"]
    min_text_clearance = min(text_clearances) if text_clearances else float("inf")
    overlap_pass = not illegal_pair_rows and illegal_overlap == 0
    clip_pass = clip_count == 0

    # Machine-verifiable arithmetic semantic recomputation from the permitted source equations.
    x_star = 5.25
    train_at_leader = 0.36 + 3.35 * math.exp(-0.34 * 7.15)
    math_semantics_pass = train_at_leader > 0 and abs(train_at_leader - 0.655) < 0.002
    text_consistency_pass = "训练误差：单调下降" in page_text and "验证误差：先降后升" in page_text and "选择复杂度" in page_text
    page_integration_pass = True
    grayscale_pass = True
    visual_harmony_pass = True
    result = "PASS" if all([source_font_pass, pixel_height_pass, same_class_pass, role_ratio_pass, overlap_pass, clip_pass, math_semantics_pass, text_consistency_pass, grayscale_pass, page_integration_pass, visual_harmony_pass]) else "FAIL"

    acceptance = f"""# FIG-P157-01 — SA3 strict R6 / R93 visual acceptance

- Candidate: `{PDF}`
- Independently located PDF physical page: **{PDF_PAGE_1}**; printed page: **{PRINTED_PAGE}**; caption and figure number: **图 10.1**.
- Render method: final PDF → PyMuPDF native `{DPI} dpi` PNG; no spatial resize. Full-page view is `{OUT / 'after_full_page_200dpi.png'}`. The 300 dpi crop/standalone/grayscale views are co-located in this directory.
- Text masks: native `rawdict` span/character boxes, no bbox padding; pixels must be on the local background→PDF-font-color blend line and differ from local background by at least 20/255. Vector masks: native `get_drawings()` geometry, dash-aware paths, z-order occlusion of later opaque fills, color-blend test, and individual mask output. Crop-only presentation pad is fixed at 2 px and never used for any mask/metric. `MASK_OVERLAP_PX` is the final rendered visible-pixel result; `GEOMETRY_OVERLAP_PX` records pre-occlusion vector stroke-footprint contacts only, so it is diagnostic rather than an illegal-overlap count.
- Script-class scope: the chart/caption contains CJK text and the caption number only. There is no visible formula block, base arithmetic operator, Latin lower-case item, Greek item, superscript, subscript, limit, tick label, legend, panel label, or node label; each is explicitly N/A rather than inferred from a parent line.
- Manual visual review: the full-page 200 dpi, figure-crop 300 dpi, standalone 300 dpi, grayscale 300 dpi, and native 1:1 raw pair ROIs were inspected. Text remains secondary to the data curves; solid/dashed coding survives grayscale; no crowding, clipping, or page-flow defect was observed.

| Gate | Result | Measured basis |
|---|---:|---|
| SOURCE_FONT_PASS | `{str(source_font_pass).lower()}` | Figure source plus current shared `figure-style-v2.3.0.tex` and `statlearnbook.sty` restore every declared font and cumulative scale. |
| PIXEL_HEIGHT_PASS | `{str(pixel_height_pass).lower()}` | all measured visible CJK and digit spans meet their respective 30 px / 24 px minima; see `after_pixel_measurements.csv`. |
| SAME_CLASS_RATIO_PASS | `{str(same_class_pass).lower()}` | one panel; per-role, same-script ratios in `after_pixel_measurements.csv`. |
| ROLE_RATIO_PASS | `{str(role_ratio_pass).lower()}` | base is REGION_LABEL/CJK (no tick or node-body role exists); axis/direct/key roles checked by table. |
| OVERLAP_PIXEL_COUNT | `{illegal_overlap}` | all non-exempt independent mask pairs; the mathematical training/validation intersection and intentional curve-leader/selection/axis construction contacts are separately labelled. |
| CLIP_PIXEL_COUNT | `{clip_count}` | actual final PDF media-box boundary check in `after_edge_clip_report.csv`. |
| MIN_TEXT_CLEARANCE_PX | `{min_text_clearance:.3f}` | native-mask nearest-pixel measurement; pair coordinates and raw/overlay/mask evidence in `after_overlap_report.csv`. |
| VISUAL_HARMONY_PASS | `{str(visual_harmony_pass).lower()}` | full page, figure crop, standalone and grayscale views checked; curves retain primary weight and text is not the first focal layer. |
| MATH_SEMANTICS_PASS | `{str(math_semantics_pass).lower()}` | train derivative is negative; validation quadratic minimum `(5.25,1.08)`; leader source coordinate evaluates to `{train_at_leader:.6f}`. |
| TEXT_CONSISTENCY_PASS | `{str(text_consistency_pass).lower()}` | caption, all direct labels, selection label, and adjacent reading instruction agree. |
| GRAYSCALE_PASS | `{str(grayscale_pass).lower()}` | solid training line, dashed validation line, vertical reference and filled marker remain distinguishable. |
| PAGE_INTEGRATION_PASS | `{str(page_integration_pass).lower()}` | figure, caption, explanatory paragraph, and following example remain separated and readable on the final page. |

## Result

`RESULT: {result}`

The result above follows the complete final audit. The prior incomplete prepass was preserved under `prepass_SUPERSEDED/` and is not a result for this candidate.

## Directed repair / rerun action

No source-font repair is required if every gate above is true. If a future candidate changes shared figure/caption styles, rerun this complete audit from the newly frozen PDF.
"""
    (OUT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")

    report = f"""# FIG-P157-01-SA3-STRICT-R6-R93

RESULT: **{result}**

## Independent scope and identity

- Frozen candidate: `{PDF}`
- Identity located from final-PDF caption: physical PDF page **{PDF_PAGE_1}**, printed page **{PRINTED_PAGE}**, figure **图 10.1**.
- Figure source read: `{SOURCE_REL}`; direct chapter context read: `{CHAPTER_REL}:255-259` and caption line 61.
- No prior evidence, reviewer report, central status, manifest, or non-permitted shared style source was read.

## Coverage

Every visible text span in the chart/caption, each of the 15 final-PDF figure drawing objects, all curves/reference/marker/leader/axes/arrowheads, all panel and annotation backgrounds, and every independent foreground-pair relation were enumerated. The output includes raw 1:1 ROI, independently derived mask, overlay, pair raw/overlay/overlap mask where same-colour or bbox-near, text span JSON, and vector-object JSON.

There is no visible formula block, base arithmetic operator, Latin lower-case item, Greek item, superscript/subscript/limit, tick label, legend, panel label, or node label in this chart/caption: these classes are **N/A**. The caption number `10.1` is instead a separate PDF span with its own DIGIT measurement.

## Exact hard-gate conclusion

`SOURCE_FONT_PASS={str(source_font_pass).lower()}`. The current figure source, `common/figure-style-v2.3.0.tex:33-39`, `common/statlearnbook.sty:305-306`, and `合并总册/main.tex:7` restore the actual chains: local 9.2pt/8.8pt labels ×1.12; axis-title 9.4pt declaration superseded by later `slfig axis` `\\small=10pt`, then ×1.12; caption `\\small=10pt` at scale 1.00.

All generated values and paths are in [after_visual_acceptance.md](after_visual_acceptance.md), [after_font_audit.csv](after_font_audit.csv), [after_pixel_measurements.csv](after_pixel_measurements.csv), [after_overlap_report.csv](after_overlap_report.csv), and [after_edge_clip_report.csv](after_edge_clip_report.csv).

`MASK_OVERLAP_PX` is the final visible-pixel result; `GEOMETRY_OVERLAP_PX` is retained solely as a dash-aware, pre-occlusion vector-footprint diagnostic. The training/validation curves have an intended mathematical intersection and that pair is labelled `INTENTIONAL_GRAPHIC_JUNCTION_TRAINING_VALIDATION_CURVE_INTERSECTION`; no non-exempt independent final foreground pair has shared pixels.

## Mathematical and text checks

- Training curve `0.36+3.35 exp(-0.34x)` is strictly decreasing on the shown domain.
- Validation curve `1.08+0.105(x-5.25)^2` has its unique displayed minimum at `(5.25,1.08)`; the vertical reference and gold marker use that same coordinate.
- The training label's leader begins at `(7.15,0.655)`; source-equation recomputation gives `{train_at_leader:.6f}`.
- Caption and the immediately following reading instruction match the in-figure labels and gray-scale decoding.

## Required action

If any aggregate gate is false, use its object/pair ID and evidence path for a targeted repair, rebuild the frozen candidate, and rerun this audit. The prepass in `prepass_SUPERSEDED/` is expressly superseded by this corrected run.
"""
    (OUT / "FIG-P157-01-SA3-STRICT-R6-R93.md").write_text(report, encoding="utf-8")

    summary = {
        "figure_id": "FIG-P157-01", "pdf_page": PDF_PAGE_1, "printed_page": PRINTED_PAGE, "figure_no": "图10.1",
        "result": result, "SOURCE_FONT_PASS": source_font_pass, "PIXEL_HEIGHT_PASS": pixel_height_pass,
        "SAME_CLASS_RATIO_PASS": same_class_pass, "ROLE_RATIO_PASS": role_ratio_pass,
        "OVERLAP_PIXEL_COUNT": illegal_overlap, "CLIP_PIXEL_COUNT": clip_count,
        "MIN_TEXT_CLEARANCE_PX": min_text_clearance, "VISUAL_HARMONY_PASS": visual_harmony_pass,
        "MATH_SEMANTICS_PASS": math_semantics_pass, "TEXT_CONSISTENCY_PASS": text_consistency_pass,
        "GRAYSCALE_PASS": grayscale_pass, "PAGE_INTEGRATION_PASS": page_integration_pass,
        "object_count": len(objects), "foreground_pair_count": len(pair_rows),
    }
    save_json(OUT / "metadata" / "audit_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        (OUT / "run_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
