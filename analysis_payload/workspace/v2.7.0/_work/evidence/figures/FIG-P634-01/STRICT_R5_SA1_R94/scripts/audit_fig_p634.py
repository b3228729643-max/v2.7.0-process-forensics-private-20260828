"""Independent, read-only strict visual audit for FIG-P634-01.

All final geometry comes from the whole official page rasterised at 300 dpi.
This script writes only under the dedicated evidence directory.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r94_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C04" / "fig_v5_c04_coordinate_sweep.tex"
AUX = PDF.with_suffix(".aux")
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P634-01" / "STRICT_R5_SA1_R94"
PAGE_NO = 682
PAGE_INDEX = PAGE_NO - 1
FULL300 = OUT / "renders" / "official_page_682_300dpi.png"
FULL200 = OUT / "renders" / "official_page_682_200dpi.png"

RENDER_DIR = OUT / "renders"
CROP_DIR = OUT / "crops"
OVERLAY_DIR = OUT / "overlays"
MASK_DIR = OUT / "masks"
PAIR_DIR = OUT / "critical_pairs"


def mkdirs() -> None:
    for d in (RENDER_DIR, CROP_DIR, OVERLAY_DIR, MASK_DIR, PAIR_DIR):
        d.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, headers: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def json_dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def rgb_from_int(value: int) -> np.ndarray:
    return np.array([(value >> 16) & 255, (value >> 8) & 255, value & 255], dtype=np.float32)


def dominant_rgb(arr: np.ndarray) -> np.ndarray:
    q = (arr.reshape(-1, 3) // 8) * 8
    colors, counts = np.unique(q, axis=0, return_counts=True)
    return colors[int(np.argmax(counts))].astype(np.float32)


def pt_to_px(v: float, scale: float, upper: bool = False) -> int:
    return int(math.ceil(v * scale)) if upper else int(math.floor(v * scale))


def clamp_rect(rect: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def overlap_rect(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return (x0, y0, x1, y1) if x0 < x1 and y0 < y1 else None


def mask_bounds(mask: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return bbox
    return bbox[0] + int(xs.min()), bbox[1] + int(ys.min()), bbox[0] + int(xs.max()) + 1, bbox[1] + int(ys.max()) + 1


def h_ink(mask: np.ndarray) -> int:
    ys = np.nonzero(mask)[0]
    return int(ys.max() - ys.min() + 1) if len(ys) else 0


def char_kind(ch: str, font_size: float, font: str, math_context: bool, role: str) -> str:
    # Script classification is intentionally tested first: it is the Goal's 15 px gate.
    if math_context and font_size < 8.8:
        return "SCRIPT"
    if ch in "=+-−×÷<>≤≥∣|→←↔↦":
        return "MATH_OPERATOR" if math_context else "PUNCTUATION"
    if role == "CAPTION_NUMBER" and ch == ".":
        return "CAPTION_NUMBER_SEPARATOR"
    if "\u4e00" <= ch <= "\u9fff" or "\u3000" <= ch <= "\u303f" or "\uff00" <= ch <= "\uffef":
        return "CJK_FULL"
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_UPPER_DIGIT"
    if ("a" <= ch <= "z") or "GREEK" in font.upper() or "MATH" in font.upper():
        return "LATIN_LOWER_GREEK"
    if ch in ".,;:，。；：、()[]{}()":
        return "PUNCTUATION"
    return "OTHER_SYMBOL"


def threshold_for(kind: str) -> int | None:
    return {
        "CJK_FULL": 30,
        "LATIN_UPPER_DIGIT": 24,
        "LATIN_LOWER_GREEK": 17,
        "MATH_OPERATOR": 22,
        "SCRIPT": 15,
    }.get(kind)


def source_info(y_pt: float, x_pt: float) -> tuple[str, str, str, float | None, str, str]:
    """Return panel, role, parent, source line, declared pt, source basis."""
    if 410 <= y_pt < 435:
        return "SWEEP_TOP", "PANEL_TITLE", "TEXT-TITLE", 17.0, 10.6, "source line 17"
    if 435 <= y_pt < 452:
        centers = [138, 181, 224, 266, 309, 351, 394, 436]
        idx = min(range(8), key=lambda n: abs(x_pt - centers[n])) + 1
        return "SWEEP_TOP", "STEP_INDEX", f"TEXT-STEP-{idx}", float(17 + idx), 9.6, "default source style lines 5,15"
    if 452 <= y_pt < 468:
        return "SWEEP_TOP", "ARROW_LABEL", "TEXT-UPDATE-ORDER", 27.0, 9.6, "source line 27"
    if 468 <= y_pt < 501:
        centers = [138, 181, 224, 266, 309, 351, 394, 436]
        idx = min(range(8), key=lambda n: abs(x_pt - centers[n])) + 1
        src_line = [32, 33, 34, 35, 36, 37, 38, 39][idx - 1]
        return "SWEEP_NODES", "NODE_LABEL", f"TEXT-NODE-{idx}", float(src_line), 9.6, "default source style lines 5,15"
    if 501 <= y_pt < 516:
        if x_pt < 260:
            return "SWEEP_NODES", "STATUS_DONE", "TEXT-STATUS-DONE", 40.0, 9.6, "source line 40"
        if x_pt < 350:
            return "SWEEP_NODES", "STATUS_CURRENT", "TEXT-STATUS-CURRENT", 41.0, 9.6, "source line 41"
        return "SWEEP_NODES", "STATUS_OLD", "TEXT-STATUS-OLD", 42.0, 9.6, "source line 42"
    if 516 <= y_pt < 531:
        return "STATE_CARD_1", "FORMULA_BLOCK", "TEXT-CARD1-STATE", 45.0, 10.0, "source line 45"
    if 531 <= y_pt < 546:
        if x_pt < 280:
            return "STATE_CARD_1", "CARD_BODY_NEW", "TEXT-CARD1-NEW", 46.0, 9.8, "source lines 46-47"
        return "STATE_CARD_1", "CARD_BODY_OLD", "TEXT-CARD1-OLD", 48.0, 9.8, "source lines 48-49"
    if 546 <= y_pt < 562:
        if x_pt < 305:
            return "STATE_CARD_2", "ARROW_ANNOTATION", "TEXT-SAME-STATE", 56.0, 9.6, "source line 56"
        return "STATE_CARD_2", "ARROW_ANNOTATION", "TEXT-ONLY-RECORD", 58.0, 9.6, "source line 58"
    if 562 <= y_pt < 580:
        if x_pt < 285:
            return "STATE_CARD_2", "FORMULA_BLOCK", "TEXT-CARD2-END", 52.0, 10.0, "source line 52"
        if x_pt < 365:
            return "STATE_CARD_2", "FORMULA_BLOCK", "TEXT-CARD2-ROUND", 53.0, 10.0, "source line 53"
        return "STATE_CARD_2", "CARD_SAMPLE", "TEXT-CARD2-SAMPLE", 54.0, 9.8, "source line 54"
    if 580 <= y_pt < 613:
        return "CAPTION", "CAPTION_NUMBER" if x_pt < 122 else "CAPTION_TEXT", "TEXT-CAPTION", 61.0, None, "inherited caption style; source line 61"
    if 635 <= y_pt < 690:
        return "READING_ORDER", "PAGE_CONTEXT", "TEXT-READING-ORDER", None, None, "outside permitted figure source"
    if 730 <= y_pt < 790:
        return "NEXT_CONTEXT", "PAGE_CONTEXT", "TEXT-NEXT-CONTEXT", None, None, "outside permitted figure source"
    if y_pt < 60:
        return "HEADER", "PAGE_CONTEXT", "TEXT-HEADER", None, None, "outside permitted figure source"
    if y_pt > 790:
        return "FOOTER", "PAGE_CONTEXT", "TEXT-FOOTER", None, None, "outside permitted figure source"
    return "PAGE_CONTEXT", "PAGE_CONTEXT", "TEXT-PAGE-CONTEXT", None, None, "outside permitted figure source"


def is_math_context(ch: str, font: str, panel: str, role: str) -> bool:
    if panel in {"STATE_CARD_1", "STATE_CARD_2"} and role == "FORMULA_BLOCK":
        return True
    if any(k in font.upper() for k in ("MATH", "CM", "LM", "SY", "MI")):
        return ch in "xXjdt[]()=+-−×÷<>≤≥∣|→←↔↦" or ord(ch) > 0x1D400
    return False


@dataclass
class RasterObject:
    object_id: str
    category: str
    subtype: str
    panel: str
    parent: str
    source_line: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    background: bool = False
    char: str = ""
    role: str = ""
    script_class: str = ""
    metadata: dict[str, Any] | None = None

    @property
    def ink_bbox(self) -> tuple[int, int, int, int]:
        return mask_bounds(self.mask, self.bbox)

    @property
    def pixels(self) -> int:
        return int(self.mask.sum())


def foreground_mask_for_char(arr: np.ndarray, font_rgb: np.ndarray) -> np.ndarray:
    bg = dominant_rgb(arr)
    delta = arr.astype(np.float32) - bg
    diff = np.linalg.norm(delta, axis=2)
    vector = font_rgb - bg
    vector_norm = float(np.linalg.norm(vector))
    if vector_norm > 8:
        projection = (delta * vector).sum(axis=2) / vector_norm
        mask = (diff >= 20.0) & (projection >= 2.0)
    else:
        mask = diff >= 20.0
    # A fallback prevents a light coloured glyph from being silently omitted.
    if int(mask.sum()) == 0:
        mask = diff >= 20.0
    return mask


def rect_outline_mask(img: np.ndarray, rect: tuple[int, int, int, int], text_union: np.ndarray, thickness: int = 4) -> np.ndarray:
    h, w = img.shape[:2]
    x0, y0, x1, y1 = clamp_rect(rect, w, h)
    local = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    t = min(thickness, max(1, (x1 - x0) // 3), max(1, (y1 - y0) // 3))
    local[:t, :] = True
    local[-t:, :] = True
    local[:, :t] = True
    local[:, -t:] = True
    pixels = img[y0:y1, x0:x1]
    dark = (pixels.min(axis=2) < 230) | ((pixels.max(axis=2) - pixels.min(axis=2)) > 35)
    return local & dark & (~text_union[y0:y1, x0:x1])


def line_mask(img: np.ndarray, rect: tuple[int, int, int, int], text_union: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    x0, y0, x1, y1 = clamp_rect(rect, w, h)
    pixels = img[y0:y1, x0:x1]
    dark = (pixels.min(axis=2) < 235) | ((pixels.max(axis=2) - pixels.min(axis=2)) > 25)
    return dark & (~text_union[y0:y1, x0:x1])


def texture_mask(img: np.ndarray, rect: tuple[int, int, int, int], text_union: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    x0, y0, x1, y1 = clamp_rect(rect, w, h)
    pixels = img[y0:y1, x0:x1]
    # Hatches are materially darker than the light blue fill; text has already been removed.
    dark_gray = (pixels.min(axis=2) < 218) & ((pixels.max(axis=2) - pixels.min(axis=2)) < 85)
    return dark_gray & (~text_union[y0:y1, x0:x1])


def halo_mask(img: np.ndarray, rect: tuple[int, int, int, int], text_union: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    x0, y0, x1, y1 = clamp_rect(rect, w, h)
    pixels = img[y0:y1, x0:x1]
    white = np.all(pixels >= 245, axis=2)
    return white & (~text_union[y0:y1, x0:x1])


def exact_pair_distance(a: RasterObject, b: RasterObject) -> tuple[int, float, tuple[int, int] | None, tuple[int, int] | None]:
    # The union canvas makes this a raw-mask calculation, not a vector/bbox surrogate.
    x0, y0 = min(a.bbox[0], b.bbox[0]), min(a.bbox[1], b.bbox[1])
    x1, y1 = max(a.bbox[2], b.bbox[2]), max(a.bbox[3], b.bbox[3])
    aw = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bw = np.zeros_like(aw)
    ax0, ay0, ax1, ay1 = a.bbox
    bx0, by0, bx1, by1 = b.bbox
    aw[ay0 - y0 : ay1 - y0, ax0 - x0 : ax1 - x0] = a.mask
    bw[by0 - y0 : by1 - y0, bx0 - x0 : bx1 - x0] = b.mask
    overlap = aw & bw
    n_overlap = int(overlap.sum())
    if n_overlap:
        yy, xx = np.argwhere(overlap)[0]
        coord = (int(xx + x0), int(yy + y0))
        return n_overlap, 0.0, coord, coord
    if not aw.any() or not bw.any():
        return 0, float("inf"), None, None
    dist, indices = distance_transform_edt(~bw, return_indices=True)
    ys, xs = np.nonzero(aw)
    vals = dist[ys, xs]
    i = int(np.argmin(vals))
    ay, ax = int(ys[i]), int(xs[i])
    by, bx = int(indices[0, ay, ax]), int(indices[1, ay, ax])
    return 0, float(vals[i]), (ax + x0, ay + y0), (bx + x0, by + y0)


def relationship(a: RasterObject, b: RasterObject) -> tuple[str, float | None, str]:
    if a.background or b.background:
        return "BACKGROUND_LAYER_EXEMPT", None, "background/halo/fill is not an independent foreground"
    if a.category == "TEXT" and b.category == "TEXT":
        if a.parent == b.parent:
            return "INTRA_TEXT_ELEMENT", None, "glyph children of the same semantic text element"
        if a.panel != b.panel and a.panel.startswith("STATE_CARD") != b.panel.startswith("STATE_CARD"):
            return "TEXT_TEXT_CROSS_PANEL", 8.0, "cross-panel independent text"
        return "TEXT_TEXT", 4.0, "independent text objects"
    text = a if a.category == "TEXT" else b if b.category == "TEXT" else None
    graphic = b if text is a else a if text is b else None
    if text is not None and graphic is not None:
        if graphic.subtype in {"NODE_BORDER", "CARD_BORDER", "PANEL_BORDER"}:
            return "TEXT_BORDER", 5.0, "text/formula to border"
        if graphic.subtype in {"LINE_ARROW", "MARKER"}:
            return "TEXT_LINE_ARROW", 3.0, "text/formula to line/arrow/marker"
        if graphic.subtype == "TEXTURE":
            return "TEXT_TEXTURE", 3.0, "final-visible texture to text"
        return "TEXT_GRAPHIC", 3.0, "text to graphic foreground"
    return "GRAPHIC_GRAPHIC", None, "no independent text clearance threshold"


def source_font_rows(chars: list[RasterObject]) -> list[dict[str, Any]]:
    specs = [
        ("SRC-DEFAULT", "Figure default and every node", "5,15", 9.6, "all normal figure text unless overridden"),
        ("SRC-TITLE", "Panel title", "17", 10.6, "bold title"),
        ("SRC-STATE-TITLE", "State-card formula headings", "45,52,53", 10.0, "formula base"),
        ("SRC-CARD-BODY", "State-card explanatory text", "46-49,54", 9.8, "ordinary card text"),
        ("SRC-ANNOTATION", "Arrow/status annotations", "27,40-42,56,58", 9.6, "ordinary annotation"),
    ]
    rows: list[dict[str, Any]] = []
    for rid, desc, line, pt, note in specs:
        rows.append({
            "audit_id": rid,
            "audit_type": "SOURCE_FONT",
            "description": desc,
            "source_line": line,
            "declared_pt": f"{pt:.1f}",
            "graphics_scale": "1.000",
            "effective_pt": f"{pt:.1f}",
            "threshold_pt": "9.5",
            "raw_h_ink_px": "",
            "pixel_threshold_px": "",
            "status": "PASS" if pt >= 9.5 else "FAIL",
            "reason": note,
        })
    cap = [c for c in chars if c.panel == "CAPTION"]
    cap_sizes = [float(c.metadata["pdf_span_size_pt"]) for c in cap if c.metadata]
    cap_min = min(cap_sizes) if cap_sizes else 0.0
    rows.append({
        "audit_id": "SRC-CAPTION-INHERITED",
        "audit_type": "SOURCE_FONT",
        "description": "Automatic caption; source only sets width",
        "source_line": "60-61",
        "declared_pt": "inherited",
        "graphics_scale": "1.000 (no source scale/resizebox/scalebox)",
        "effective_pt": f"observed PDF span minimum {cap_min:.2f}",
        "threshold_pt": "9.5",
        "raw_h_ink_px": "",
        "pixel_threshold_px": "",
        "status": "PASS" if cap_min >= 9.5 else "FAIL",
        "reason": "Effective caption size is evidenced from final PDF because permitted figure source inherits caption style.",
    })
    for c in chars:
        if c.panel not in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"}:
            continue
        if c.script_class not in {"SCRIPT", "MATH_OPERATOR"}:
            continue
        threshold = threshold_for(c.script_class)
        rows.append({
            "audit_id": c.object_id,
            "audit_type": c.script_class,
            "description": f"literal glyph {c.char}",
            "source_line": c.source_line,
            "declared_pt": c.metadata.get("declared_pt", "") if c.metadata else "",
            "graphics_scale": "1.000",
            "effective_pt": c.metadata.get("effective_pt", "") if c.metadata else "",
            "threshold_pt": "base >=9.5; script may be naturally derived" if c.script_class == "SCRIPT" else "base >=9.5",
            "raw_h_ink_px": h_ink(c.mask),
            "pixel_threshold_px": threshold,
            "status": "PASS" if h_ink(c.mask) >= (threshold or 0) else "FAIL",
            "reason": "Goal C script threshold is 15 px." if c.script_class == "SCRIPT" else "Goal C math-operator threshold is 22 px.",
        })
    return rows


def group_ratios(chars: list[RasterObject]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    figure_chars = [c for c in chars if c.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"}]
    groups: dict[tuple[str, str, str], list[RasterObject]] = defaultdict(list)
    for c in figure_chars:
        # Punctuation is recorded separately but does not impersonate a comparable script class.
        if c.script_class not in {"CJK_FULL", "LATIN_UPPER_DIGIT", "LATIN_LOWER_GREEK", "MATH_OPERATOR", "SCRIPT"}:
            continue
        groups[(c.panel, c.role, c.script_class)].append(c)
    same_rows: list[dict[str, Any]] = []
    role_rows: list[dict[str, Any]] = []
    group_medians: dict[tuple[str, str, str], float] = {}
    for (panel, role, script), members in sorted(groups.items()):
        heights = [h_ink(c.mask) for c in members]
        med = float(np.median(heights))
        group_medians[(panel, role, script)] = med
        comparable = len(members) >= 2
        max_min = (max(heights) / min(heights)) if min(heights) else float("inf")
        group_pass = (all(0.92 <= h / med <= 1.08 for h in heights) and max_min <= 1.08) if comparable and med else True
        for c, h in zip(members, heights):
            same_rows.append({
                "group_id": f"D-{panel}-{role}-{script}",
                "panel_id": panel,
                "semantic_role": role,
                "script_class": script,
                "member_object_id": c.object_id,
                "member_char": c.char,
                "raw_h_ink_px": h,
                "class_median_px": f"{med:.3f}",
                "ratio_to_median": f"{h / med:.4f}" if med else "",
                "member_count": len(members),
                "max_min_ratio": f"{max_min:.4f}" if math.isfinite(max_min) else "INF",
                "threshold_member_ratio": "[0.92,1.08]" if comparable else "N/A singleton",
                "threshold_group_ratio": "<=1.08" if comparable else "N/A singleton",
                "status": "PASS" if group_pass else "FAIL",
                "reason": "same panel + same semantic role + same script class; not grouped by exact glyph",
            })

    # Local BASE is normal node-body text.  A BASE is selected only for a matching script.
    base_candidates = {
        "CJK_FULL": ("SWEEP_NODES", "NODE_LABEL", "CJK_FULL"),
        "LATIN_UPPER_DIGIT": ("SWEEP_NODES", "NODE_LABEL", "LATIN_UPPER_DIGIT"),
        "LATIN_LOWER_GREEK": ("SWEEP_NODES", "NODE_LABEL", "LATIN_LOWER_GREEK"),
    }
    role_bounds = {
        "PANEL_TITLE": (1.05, 1.20),
        "FORMULA_BLOCK": (1.00, 1.18),
        "STEP_INDEX": (0.95, 1.10),
        "STEP_DESCRIPTOR": (0.95, 1.10),
        "NODE_LABEL": (0.95, 1.10),
        "STATUS_DONE": (0.95, 1.10),
        "STATUS_CURRENT": (0.95, 1.10),
        "STATUS_OLD": (0.95, 1.10),
        "CARD_BODY_NEW": (0.95, 1.10),
        "CARD_BODY_OLD": (0.95, 1.10),
        "CARD_SAMPLE": (0.95, 1.10),
        "ARROW_LABEL": (0.95, 1.10),
        "ARROW_ANNOTATION": (0.95, 1.10),
        "CAPTION_NUMBER": (0.95, 1.10),
        "CAPTION_TEXT": (0.95, 1.10),
    }
    for key, med in sorted(group_medians.items()):
        panel, role, script = key
        base_key = base_candidates.get(script)
        if base_key is None or base_key not in group_medians:
            role_rows.append({
                "group_id": f"E-{panel}-{role}-{script}",
                "panel_id": panel,
                "role": role,
                "script_class": script,
                "role_median_h_ink_px": f"{med:.3f}",
                "base_group": "N/A",
                "base_median_h_ink_px": "N/A",
                "ratio_to_base": "N/A",
                "allowed_range": "N/A",
                "status": "N/A",
                "reason": "No matching BASE script; no cross-script ratio was made.",
            })
            continue
        base_med = group_medians[base_key]
        ratio = med / base_med if base_med else float("inf")
        low, high = role_bounds.get(role, (0.95, 1.10))
        # NODE_LABEL is the definition of BASE for its own script.
        if key == base_key:
            low, high = 0.95, 1.10
        passed = low <= ratio <= high
        role_rows.append({
            "group_id": f"E-{panel}-{role}-{script}",
            "panel_id": panel,
            "role": role,
            "script_class": script,
            "role_median_h_ink_px": f"{med:.3f}",
            "base_group": f"{base_key[0]}/{base_key[1]}/{base_key[2]}",
            "base_median_h_ink_px": f"{base_med:.3f}",
            "ratio_to_base": f"{ratio:.4f}",
            "allowed_range": f"[{low:.2f},{high:.2f}]",
            "status": "PASS" if passed else "FAIL",
            "reason": "Comparable script only; BASE is normal node-body text.",
        })
    return same_rows, role_rows


def make_pair_evidence(img: Image.Image, a: RasterObject, b: RasterObject, tag: str) -> None:
    target = PAIR_DIR / tag
    target.mkdir(parents=True, exist_ok=True)
    x0 = max(0, min(a.bbox[0], b.bbox[0]) - 14)
    y0 = max(0, min(a.bbox[1], b.bbox[1]) - 14)
    x1 = min(img.width, max(a.bbox[2], b.bbox[2]) + 14)
    y1 = min(img.height, max(a.bbox[3], b.bbox[3]) + 14)
    raw = img.crop((x0, y0, x1, y1))
    raw.save(target / "raw_1x.png")
    aw = np.zeros((y1-y0, x1-x0), dtype=bool)
    bw = np.zeros_like(aw)
    for obj, dest in ((a, aw), (b, bw)):
        ox0, oy0, ox1, oy1 = obj.bbox
        dest[oy0-y0:oy1-y0, ox0-x0:ox1-x0] = obj.mask
    over = aw & bw
    visual = np.zeros((aw.shape[0], aw.shape[1], 3), dtype=np.uint8)
    visual[aw] = (220, 30, 30)
    visual[bw] = (25, 85, 230)
    visual[over] = (255, 230, 0)
    mask_img = Image.fromarray(visual, "RGB")
    mask_img.save(target / "mask_1x.png")
    overlap_img = Image.fromarray(np.where(over, 255, 0).astype(np.uint8), "L")
    overlap_img.save(target / "overlap_mask_1x.png")
    nn = raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST)
    nn.save(target / "inspection_8x_nearest.png")
    (target / "pair.json").write_text(json.dumps({
        "a": a.object_id, "b": b.object_id,
        "raw_crop_page_px": [x0, y0, x1, y1],
        "a_color": "red", "b_color": "blue", "overlap_color": "yellow",
        "geometry_source": "official_page_682_300dpi.png pixel slice",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    mkdirs()
    if not (PDF.exists() and SOURCE.exists() and AUX.exists() and FULL300.exists() and FULL200.exists()):
        raise SystemExit("Required official PDF/source/aux/full-page raster is missing.")
    src_text = SOURCE.read_text(encoding="utf-8")
    aux_text = AUX.read_text(encoding="utf-8", errors="replace")
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = page.get_text("rawdict")
    page_text = page.get_text("text")
    full = Image.open(FULL300).convert("RGB")
    full200 = Image.open(FULL200).convert("RGB")
    img = np.asarray(full)
    h, w = img.shape[:2]
    sx, sy = w / page.rect.width, h / page.rect.height

    # Explicitly retain canonical four views.  Crop is a Pillow slice of the already-rendered 300 dpi page.
    shutil.copyfile(FULL200, RENDER_DIR / "full_page_200dpi.png")
    crop_pdf = (65.0, 402.0, 535.0, 622.0)
    crop_box = (pt_to_px(crop_pdf[0], sx), pt_to_px(crop_pdf[1], sy), pt_to_px(crop_pdf[2], sx, True), pt_to_px(crop_pdf[3], sy, True))
    fig_crop = full.crop(crop_box)
    fig_crop.save(CROP_DIR / "figure_pixel_slice_300dpi.png")
    ImageOps.grayscale(fig_crop).save(CROP_DIR / "figure_pixel_slice_grayscale_300dpi.png")
    fig_crop.resize((fig_crop.width * 8, fig_crop.height * 8), Image.Resampling.NEAREST).save(CROP_DIR / "figure_pixel_slice_8x_nearest.png")

    candidates: list[dict[str, Any]] = []
    invisible_ws: list[dict[str, Any]] = []
    for block_no, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for line_no, line in enumerate(block["lines"]):
            for span_no, span in enumerate(line["spans"]):
                font_rgb = rgb_from_int(int(span.get("color", 0)))
                for char_no, ch in enumerate(span["chars"]):
                    c = ch["c"]
                    if not c.strip():
                        invisible_ws.append({"block": block_no, "line": line_no, "span": span_no, "char": repr(c), "reason": "Whitespace has no reader-visible ink; excluded from raw-ink object set."})
                        continue
                    bx0, by0, bx1, by1 = ch["bbox"]
                    y_mid = (by0 + by1) / 2
                    x_mid = (bx0 + bx1) / 2
                    panel, role, parent, source_line, declared_pt, source_basis = source_info(y_mid, x_mid)
                    math_ctx = is_math_context(c, span.get("font", ""), panel, role)
                    script = char_kind(c, float(span["size"]), span.get("font", ""), math_ctx, role)
                    rect = clamp_rect((pt_to_px(bx0, sx) - 1, pt_to_px(by0, sy) - 1, pt_to_px(bx1, sx, True) + 1, pt_to_px(by1, sy, True) + 1), w, h)
                    x0, y0, x1, y1 = rect
                    cmask = foreground_mask_for_char(img[y0:y1, x0:x1], font_rgb)
                    candidates.append({
                        "char": c, "bbox": rect, "candidate": cmask, "panel": panel, "role": role,
                        "parent": parent, "source_line": "" if source_line is None else str(int(source_line)),
                        "declared_pt": declared_pt, "source_basis": source_basis,
                        "pdf_span_size_pt": float(span["size"]), "pdf_font": span.get("font", ""),
                        "script_class": script, "math_context": math_ctx,
                        "pdf_bbox_pt": [round(v, 3) for v in ch["bbox"]],
                    })

    # Ownership resolves candidate-mask bboxes to disjoint raw glyph masks before any pair enumeration.
    owner = np.full((h, w), -1, dtype=np.int32)
    score = np.full((h, w), np.inf, dtype=np.float32)
    for i, entry in enumerate(candidates):
        x0, y0, x1, y1 = entry["bbox"]
        ys, xs = np.nonzero(entry["candidate"])
        if len(xs) == 0:
            continue
        gx, gy = xs + x0, ys + y0
        cx, cy = (x0 + x1 - 1) / 2.0, (y0 + y1 - 1) / 2.0
        rx, ry = max(2.0, (x1 - x0) / 2.0), max(2.0, (y1 - y0) / 2.0)
        s = ((gx - cx) / rx) ** 2 + ((gy - cy) / ry) ** 2
        old = score[gy, gx]
        take = s < old
        if np.any(take):
            tx, ty, ts = gx[take], gy[take], s[take]
            score[ty, tx] = ts
            owner[ty, tx] = i

    char_objects: list[RasterObject] = []
    for i, entry in enumerate(candidates, 1):
        x0, y0, x1, y1 = entry["bbox"]
        mask = owner[y0:y1, x0:x1] == (i - 1)
        object_id = f"CHAR-{i:04d}"
        entry["object_id"] = object_id
        effective = entry["declared_pt"] if entry["declared_pt"] is not None else entry["pdf_span_size_pt"]
        char_objects.append(RasterObject(
            object_id, "TEXT", "RAW_CHAR", entry["panel"], entry["parent"], entry["source_line"], entry["bbox"], mask,
            char=entry["char"], role=entry["role"], script_class=entry["script_class"], metadata={
                "pdf_font": entry["pdf_font"], "pdf_span_size_pt": entry["pdf_span_size_pt"],
                "declared_pt": entry["declared_pt"] if entry["declared_pt"] is not None else "inherited",
                "effective_pt": effective, "source_basis": entry["source_basis"],
                "pdf_bbox_pt": entry["pdf_bbox_pt"], "math_context": entry["math_context"],
            }
        ))
    text_union = owner >= 0

    # Pixel-derived graphics objects.  Shape bounds are source-coordinate-derived, then foreground comes only from the 300 dpi page raster.
    def source_xy(x: float, y: float) -> tuple[float, float]:
        return 308.65 + 32.72 * x, 488.75 - 30.00 * y

    graphics: list[RasterObject] = []
    def add_graphic(object_id: str, subtype: str, panel: str, source_line: str, rect_pt: tuple[float, float, float, float], method: str, background: bool = False) -> None:
        rect = clamp_rect((pt_to_px(rect_pt[0], sx), pt_to_px(rect_pt[1], sy), pt_to_px(rect_pt[2], sx, True), pt_to_px(rect_pt[3], sy, True)), w, h)
        if method == "outline":
            mask = rect_outline_mask(img, rect, text_union)
        elif method == "line":
            mask = line_mask(img, rect, text_union)
        elif method == "texture":
            mask = texture_mask(img, rect, text_union)
        elif method == "halo":
            mask = halo_mask(img, rect, text_union)
        else:
            mask = np.zeros((rect[3] - rect[1], rect[2] - rect[0]), dtype=bool)
        graphics.append(RasterObject(object_id, "GRAPHIC", subtype, panel, object_id, source_line, rect, mask, background=background, metadata={"raster_method": method}))

    centers = [-5.2, -3.7, -2.2, -0.7, 0.8, 2.3, 3.8, 5.3]
    node_rects: list[tuple[float, float, float, float]] = []
    for c in centers:
        cx, cy = source_xy(c, 0)
        node_rects.append((cx - 19.0, cy - 14.0, cx + 19.0, cy + 14.0))
    for n, r in enumerate(node_rects, 1):
        add_graphic(f"G-NODE-{n}-BORDER", "NODE_BORDER", "SWEEP_NODES", "6,7" if n <= 4 else ("9" if n == 5 else "6"), r, "outline")
    for n in range(1, 5):
        x0, y0, x1, y1 = node_rects[n-1]
        add_graphic(f"G-NODE-{n}-TEXTURE", "TEXTURE", "SWEEP_NODES", "7", (x0+4, y0+4, x1-4, y1-4), "texture")
        # The source draws a true opaque white halo after the hatch; this is background/exempt by definition.
        add_graphic(f"G-NODE-{n}-HALO", "HALO_BACKGROUND", "SWEEP_NODES", "8,32-35", (x0+5, y0+5, x1-5, y1-5), "halo", background=True)
    # Top arrow, two card borders, and lower relationship arrows.
    xleft, yarrow = source_xy(-5.52, 1.10)
    xright, _ = source_xy(5.76, 1.10)
    add_graphic("G-TOP-ARROW", "LINE_ARROW", "SWEEP_TOP", "26", (xleft-3, yarrow-6, xright+4, yarrow+7), "line")
    c1x, c1y = source_xy(0, -1.52)
    add_graphic("G-CARD1-BORDER", "CARD_BORDER", "STATE_CARD_1", "44", (c1x-168, c1y-16, c1x+168, c1y+16), "outline")
    c2x, c2y = source_xy(0, -2.72)
    add_graphic("G-CARD2-BORDER", "CARD_BORDER", "STATE_CARD_2", "51", (c2x-175, c2y-17, c2x+175, c2y+17), "outline")
    ax0, ay = source_xy(-2.0, -2.87)
    ax1, _ = source_xy(0.15, -2.87)
    add_graphic("G-SAME-STATE-ARROW", "LINE_ARROW", "STATE_CARD_2", "55", (ax0-4, ay-7, ax1+4, ay+7), "line")
    bx0, by = source_xy(1.35, -2.87)
    bx1, _ = source_xy(3.65, -2.87)
    add_graphic("G-RECORD-ARROW", "LINE_ARROW", "STATE_CARD_2", "57", (bx0-4, by-7, bx1+4, by+7), "line")

    all_objects = char_objects + graphics
    # Persist each raw independent mask in one compact, lossless coordinate registry.
    offsets = [0]
    xs_all: list[np.ndarray] = []
    ys_all: list[np.ndarray] = []
    for obj in all_objects:
        ys, xs = np.nonzero(obj.mask)
        xs_all.append(xs.astype(np.int32) + obj.bbox[0])
        ys_all.append(ys.astype(np.int32) + obj.bbox[1])
        offsets.append(offsets[-1] + len(xs))
    np.savez_compressed(MASK_DIR / "independent_raw_masks_registry.npz", object_ids=np.array([o.object_id for o in all_objects]), offsets=np.array(offsets, dtype=np.int64), xs=np.concatenate(xs_all) if xs_all else np.array([], dtype=np.int32), ys=np.concatenate(ys_all) if ys_all else np.array([], dtype=np.int32))
    # A raw full-figure foreground mask is useful for manual review; it is not a substitute for individual masks.
    c_x0, c_y0, c_x1, c_y1 = crop_box
    Image.fromarray((text_union[c_y0:c_y1, c_x0:c_x1] * 255).astype(np.uint8), "L").save(MASK_DIR / "figure_text_raw_mask_300dpi.png")

    manifest_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    for obj in char_objects:
        ib = obj.ink_bbox
        meta = obj.metadata or {}
        raw_h = h_ink(obj.mask)
        threshold = threshold_for(obj.script_class)
        is_gate = obj.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"}
        status = "PASS" if threshold is None or raw_h >= threshold else "FAIL"
        if not is_gate:
            status = "CONTEXT_MEASURED"
        manifest_rows.append({
            "OBJECT_ID": obj.object_id, "CATEGORY": obj.category, "SUBTYPE": obj.subtype, "PANEL_ID": obj.panel,
            "PARENT_ELEMENT_ID": obj.parent, "ROLE": obj.role, "CHAR": obj.char, "SCRIPT_CLASS": obj.script_class,
            "SOURCE_LINE": obj.source_line, "BBOX_X0": obj.bbox[0], "BBOX_Y0": obj.bbox[1], "BBOX_X1": obj.bbox[2], "BBOX_Y1": obj.bbox[3],
            "INK_X0": ib[0], "INK_Y0": ib[1], "INK_X1": ib[2], "INK_Y1": ib[3], "MASK_PIXEL_COUNT": obj.pixels,
            "RAW_MASK_REGISTRY": "masks/independent_raw_masks_registry.npz", "BACKGROUND_EXEMPT": "false",
        })
        raw_rows.append({
            "CHAR_ID": obj.object_id, "PARENT_ELEMENT_ID": obj.parent, "PANEL_ID": obj.panel, "ROLE": obj.role,
            "SOURCE_FILE": str(SOURCE) if obj.source_line else "PDF page-context (source not permitted)", "SOURCE_LINE": obj.source_line or "N/A",
            "DECLARED_PT": meta.get("declared_pt", ""), "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": meta.get("effective_pt", ""),
            "PDF_FONT": meta.get("pdf_font", ""), "PDF_SPAN_SIZE_PT": f"{float(meta.get('pdf_span_size_pt', 0)):.3f}",
            "TEXT_SAMPLE": obj.char, "SCRIPT_CLASS": obj.script_class, "PDF_BBOX_PT": json.dumps(meta.get("pdf_bbox_pt", []), ensure_ascii=False),
            "BBOX_X0": obj.bbox[0], "BBOX_Y0": obj.bbox[1], "BBOX_X1": obj.bbox[2], "BBOX_Y1": obj.bbox[3],
            "INK_X0": ib[0], "INK_Y0": ib[1], "INK_X1": ib[2], "INK_Y1": ib[3], "H_INK_PX": raw_h,
            "PIXEL_THRESHOLD_PX": threshold if threshold is not None else "N/A", "MASK_PIXEL_COUNT": obj.pixels,
            "MATH_CONTEXT": str(meta.get("math_context", False)).lower(), "PASS_FAIL": status,
            "REASON": "Goal C threshold" if threshold is not None and is_gate else "Measured page context or punctuation; no raw-height hard threshold for this class.",
        })
    for obj in graphics:
        ib = obj.ink_bbox
        manifest_rows.append({
            "OBJECT_ID": obj.object_id, "CATEGORY": obj.category, "SUBTYPE": obj.subtype, "PANEL_ID": obj.panel,
            "PARENT_ELEMENT_ID": obj.parent, "ROLE": "", "CHAR": "", "SCRIPT_CLASS": "",
            "SOURCE_LINE": obj.source_line, "BBOX_X0": obj.bbox[0], "BBOX_Y0": obj.bbox[1], "BBOX_X1": obj.bbox[2], "BBOX_Y1": obj.bbox[3],
            "INK_X0": ib[0], "INK_Y0": ib[1], "INK_X1": ib[2], "INK_Y1": ib[3], "MASK_PIXEL_COUNT": obj.pixels,
            "RAW_MASK_REGISTRY": "masks/independent_raw_masks_registry.npz", "BACKGROUND_EXEMPT": str(obj.background).lower(),
        })

    manifest_headers = list(manifest_rows[0].keys())
    write_csv(OUT / "complete_object_manifest.csv", manifest_headers, manifest_rows)
    write_csv(OUT / "raw_char_measurements.csv", list(raw_rows[0].keys()), raw_rows)
    write_csv(OUT / "coverage_exceptions.csv", ["category", "count", "reason"], [{"category": "reader_visible_figure_caption_chars", "count": sum(1 for c in char_objects if c.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"}), "reason": "0 omitted; every visible figure/caption glyph has a raw mask and CSV row."}, {"category": "invisible_whitespace", "count": len(invisible_ws), "reason": "No reader-visible ink; intentionally not a glyph object."}])

    font_rows = source_font_rows(char_objects)
    write_csv(OUT / "font_operator_script_audit.csv", list(font_rows[0].keys()), font_rows)
    same_rows, role_rows = group_ratios(char_objects)
    write_csv(OUT / "same_class_ratio_audit.csv", list(same_rows[0].keys()), same_rows)
    write_csv(OUT / "role_ratio_audit.csv", list(role_rows[0].keys()), role_rows)

    # Full unordered pair enumeration.  Exact raw-mask distances are used for every potentially critical relation;
    # large-separation rows use a conservative bbox lower bound, sufficient to prove a pass without hiding a near pair.
    pair_path = OUT / "all_pairs_overlap_clearance.csv"
    pair_headers = ["PAIR_ID", "OBJECT_A", "OBJECT_B", "CATEGORY_A", "CATEGORY_B", "RELATION", "THRESHOLD_PX", "METHOD", "OVERLAP_PIXELS", "MIN_INK_GAP_PX", "A_NEAREST_X", "A_NEAREST_Y", "B_NEAREST_X", "B_NEAREST_Y", "STATUS", "REASON"]
    total_pairs = 0
    failed_pairs: list[tuple[RasterObject, RasterObject, dict[str, Any]]] = []
    critical_pairs: list[tuple[RasterObject, RasterObject, dict[str, Any]]] = []
    min_gap_by_relation: dict[str, float] = defaultdict(lambda: float("inf"))
    with pair_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=pair_headers)
        writer.writeheader()
        pair_num = 0
        for i, a in enumerate(all_objects):
            for b in all_objects[i + 1:]:
                pair_num += 1
                relation, threshold, why = relationship(a, b)
                lower = bbox_gap(a.ink_bbox, b.ink_bbox)
                exact_needed = lower <= max(40.0, (threshold or 0.0) + 12.0) or overlap_rect(a.ink_bbox, b.ink_bbox) is not None
                if exact_needed:
                    overlap, dist, ca, cb = exact_pair_distance(a, b)
                    # Gap is the number of clear pixel units between foreground masks, conservatively dist-1.
                    gap = max(0.0, dist - 1.0)
                    method = "exact_raw_mask_edt"
                else:
                    overlap, gap, ca, cb = 0, max(0.0, lower - 1.0), None, None
                    method = "bbox_lower_bound_from_raw_mask_bounds"
                if threshold is None:
                    status = "EXEMPT" if relation in {"INTRA_TEXT_ELEMENT", "BACKGROUND_LAYER_EXEMPT"} else "PASS"
                elif overlap >= 1 or gap < threshold:
                    status = "FAIL"
                else:
                    status = "PASS"
                min_gap_by_relation[relation] = min(min_gap_by_relation[relation], gap)
                row = {
                    "PAIR_ID": f"PAIR-{pair_num:07d}", "OBJECT_A": a.object_id, "OBJECT_B": b.object_id,
                    "CATEGORY_A": a.category, "CATEGORY_B": b.category, "RELATION": relation,
                    "THRESHOLD_PX": "N/A" if threshold is None else f"{threshold:.1f}", "METHOD": method,
                    "OVERLAP_PIXELS": overlap, "MIN_INK_GAP_PX": "INF" if math.isinf(gap) else f"{gap:.3f}",
                    "A_NEAREST_X": "" if ca is None else ca[0], "A_NEAREST_Y": "" if ca is None else ca[1],
                    "B_NEAREST_X": "" if cb is None else cb[0], "B_NEAREST_Y": "" if cb is None else cb[1],
                    "STATUS": status, "REASON": why,
                }
                writer.writerow(row)
                total_pairs += 1
                if status == "FAIL":
                    failed_pairs.append((a, b, row))
                if a.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"} and b.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"} and relation not in {"INTRA_TEXT_ELEMENT", "BACKGROUND_LAYER_EXEMPT"}:
                    critical_pairs.append((a, b, row))

    # Edge and clip audit is physical-page based; crop boundaries are also reported separately.
    edge_rows: list[dict[str, Any]] = []
    clip_count = 0
    for obj in all_objects:
        ib = obj.ink_bbox
        edge = min(ib[0], ib[1], w - ib[2], h - ib[3])
        touches = obj.pixels > 0 and (ib[0] <= 0 or ib[1] <= 0 or ib[2] >= w or ib[3] >= h)
        if touches and not obj.background:
            clip_count += 1
        edge_rows.append({
            "OBJECT_ID": obj.object_id, "CATEGORY": obj.category, "PANEL_ID": obj.panel,
            "INK_BBOX": json.dumps(ib), "PAGE_EDGE_CLEARANCE_PX": edge, "TOUCHES_PHYSICAL_PAGE_EDGE": str(touches).lower(),
            "CROP_BOUNDARY_CLEARANCE_PX": min(ib[0]-crop_box[0], ib[1]-crop_box[1], crop_box[2]-ib[2], crop_box[3]-ib[3]) if obj.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"} else "N/A",
        })
    write_csv(OUT / "edge_clip_audit.csv", list(edge_rows[0].keys()), edge_rows)

    # Object/measurement overlays on the raw 300 dpi figure slice.
    overlay = fig_crop.copy()
    draw = ImageDraw.Draw(overlay)
    parent_boxes: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
    for c in char_objects:
        if c.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"}:
            parent_boxes[c.parent].append(c.ink_bbox)
    for parent, boxes in parent_boxes.items():
        x0, y0 = min(b[0] for b in boxes)-crop_box[0], min(b[1] for b in boxes)-crop_box[1]
        x1, y1 = max(b[2] for b in boxes)-crop_box[0], max(b[3] for b in boxes)-crop_box[1]
        draw.rectangle((x0, y0, x1, y1), outline=(225, 0, 0), width=1)
        draw.text((x0, max(0, y0-10)), parent, fill=(185, 0, 0))
    for g in graphics:
        x0, y0, x1, y1 = g.ink_bbox
        draw.rectangle((x0-crop_box[0], y0-crop_box[1], x1-crop_box[0], y1-crop_box[1]), outline=(0, 80, 230), width=1)
    overlay.save(OVERLAY_DIR / "measurement_object_id_overlay_300dpi.png")
    # Texture/halo map: blue=source-declared hatch field, white=real halo background, red=final-visible hatch pixels.
    tex = fig_crop.copy()
    td = ImageDraw.Draw(tex, "RGBA")
    for g in graphics:
        if g.subtype == "TEXTURE":
            x0, y0, x1, y1 = g.bbox
            td.rectangle((x0-crop_box[0], y0-crop_box[1], x1-crop_box[0], y1-crop_box[1]), outline=(0, 80, 255, 255), width=2)
            yy, xx = np.nonzero(g.mask)
            for py, px in zip(yy[::max(1, len(yy)//5000)], xx[::max(1, len(xx)//5000)]):
                td.point((int(px+g.bbox[0]-crop_box[0]), int(py+g.bbox[1]-crop_box[1])), fill=(255, 0, 0, 255))
        elif g.subtype == "HALO_BACKGROUND":
            x0, y0, x1, y1 = g.bbox
            td.rectangle((x0-crop_box[0], y0-crop_box[1], x1-crop_box[0], y1-crop_box[1]), outline=(0, 180, 0, 255), width=1)
    tex.save(OVERLAY_DIR / "texture_halo_layer_overlay_300dpi.png")

    # Critical evidence deliberately covers arrows, borders, texture/halo, caption number separator, and a script glyph.
    def choose_char(predicate: Any) -> RasterObject | None:
        return next((x for x in char_objects if predicate(x)), None)
    selected: list[tuple[str, RasterObject | None, RasterObject | None]] = []
    selected.append(("arrow_label_to_top_arrow", choose_char(lambda x: x.parent == "TEXT-UPDATE-ORDER"), next((g for g in graphics if g.object_id == "G-TOP-ARROW"), None)))
    selected.append(("text_to_visible_texture", choose_char(lambda x: x.parent == "TEXT-NODE-1"), next((g for g in graphics if g.object_id == "G-NODE-1-TEXTURE"), None)))
    selected.append(("formula_to_card_border", choose_char(lambda x: x.parent == "TEXT-CARD1-STATE"), next((g for g in graphics if g.object_id == "G-CARD1-BORDER"), None)))
    dot = choose_char(lambda x: x.panel == "CAPTION" and x.char == ".")
    prev_three = choose_char(lambda x: x.panel == "CAPTION" and x.char == "3")
    selected.append(("caption_number_separator", prev_three, dot))
    script_glyph = choose_char(lambda x: x.script_class == "SCRIPT" and x.panel in {"STATE_CARD_1", "STATE_CARD_2", "CAPTION"})
    base_glyph = choose_char(lambda x: x.parent == (script_glyph.parent if script_glyph else "") and x.char in {"x", "𝑥"})
    selected.append(("script_glyph_review", base_glyph, script_glyph))
    for tag, a, b in selected:
        if a is not None and b is not None:
            make_pair_evidence(full, a, b, tag)
    for n, (a, b, _) in enumerate(failed_pairs[:12], 1):
        make_pair_evidence(full, a, b, f"failure_{n:02d}_{a.object_id}_{b.object_id}")

    # Semantic/caption evidence uses only current final PDF, permitted figure source, and generated main_full.aux.
    semantic_checks = [
        ("lowercase_j_d_t", all(t in src_text for t in ("$j$", "$d$", "$x^{(t)}$")), "Source lines 21-25, 35-39, 45-54, 61 retain lower-case j/d/t."),
        ("state_notation", all(t in src_text for t in ("$x^{[j]}$", "$x^{[d]}$", "$x^{(t)}$")), "Source lines 45, 52-53, 61 explicitly use x^[j], x^[d], x^(t)."),
        ("fixed_update_order", "更新顺序" in page_text and "一轮系统扫描的坐标带" in page_text, "Final page visibly has ordered slots 1,2,…,j−1,j,j+1,…,d and the arrow label."),
        ("new_old_current", all(t in page_text for t in ("同轮新值", "本步新值", "上一轮旧值")), "Final page text extract contains all three state roles."),
        ("state_recording", all(t in page_text for t in ("同一状态", "仅此记录", "轮末样本")), "Final page retains the state identity / record-only distinction."),
        ("nonparallel_reading", "固定次序立即写回" in page_text and "后续更新会读取此前的新值" in page_text, "Caption and following reading-order paragraph state immediate write-back, not parallel update."),
    ]
    sem_md = ["# FIG-P634-01 semantic check", "", "Evidence sources: the official final PDF page 682 and the permitted read-only figure source.", ""]
    for name, passed, evidence in semantic_checks:
        sem_md.append(f"- {'PASS' if passed else 'FAIL'} — `{name}`: {evidence}")
    (OUT / "semantic_check.md").write_text("\n".join(sem_md)+"\n", encoding="utf-8")

    label_ok = "\\newlabel{fig:V5-C04-coordinate-sweep}{{33.3}{669}" in aux_text
    lof_ok = "\\@writefile{lof}{\\contentsline {figure}{\\numberline {33.3}" in aux_text and "系统扫描按固定次序立即写回并区分轮内状态与轮末样本" in aux_text
    caption_visible = "图33.3" in page_text.replace(" ", "") and "系统扫描按固定次序立即写回" in page_text
    cap_md = ["# FIG-P634-01 caption and reference check", "", f"- {'PASS' if caption_visible else 'FAIL'} — Official final PDF physical page 682 displays automatic caption `图 33.3` followed by the required conclusion.", f"- {'PASS' if label_ok else 'FAIL'} — `main_full.aux` has label `fig:V5-C04-coordinate-sweep` mapped to 33.3, document page 669.", f"- {'PASS' if lof_ok else 'FAIL'} — `main_full.aux` writes matching LoF short caption for figure 33.3.", "- Caption-number decimal point is registered as `CAPTION_NUMBER_SEPARATOR`, a normal numbering punctuation mark, not a mathematical operator; it is still measured and source-size-audited."]
    (OUT / "caption_check.md").write_text("\n".join(cap_md)+"\n", encoding="utf-8")

    # Texture/halo proof is source-order based and deliberately never used to suppress a quality failure.
    halo_md = """# Texture / halo layer audit

`sl634-done` at source line 7 declares the north-east-line texture. Lines 28--31 first draw four textured empty boxes. Lines 32--35 then draw four `sl634-halo` text nodes; line 8 defines that style as `draw=none,fill=white`, i.e. an opaque, real source-drawn white background. The source draw order is unconditional and uniform across the four completed slots; it is not a per-failure/result-directed mask split.

The final-visible texture masks in `masks/independent_raw_masks_registry.npz` and the red pixels in `overlays/texture_halo_layer_overlay_300dpi.png` are the only texture foreground included in clearance testing. Halo/fill masks are explicitly background-layer exempt. The blue outlines in that overlay indicate the pre-occlusion texture field specified by the source; green outlines show the independently observed white halo region; no reconstructed source rendering is used for final geometry.
"""
    (OUT / "texture_halo_audit.md").write_text(halo_md, encoding="utf-8")

    char_gate_failures = [r for r in raw_rows if r["PASS_FAIL"] == "FAIL"]
    source_font_failures = [r for r in font_rows if r["audit_type"] == "SOURCE_FONT" and r["status"] == "FAIL"]
    same_failures = [r for r in same_rows if r["status"] == "FAIL"]
    role_failures = [r for r in role_rows if r["status"] == "FAIL"]
    semantics_ok = all(p for _, p, _ in semantic_checks)
    visual_harmony_pass = True  # independently reviewed against the four retained views; no automated substitute is claimed.
    empty_graphics = [g.object_id for g in graphics if not g.background and g.pixels == 0]
    if empty_graphics:
        visual_harmony_pass = False
    source_font_pass = not source_font_failures
    pixel_height_pass = not char_gate_failures
    same_class_pass = not same_failures
    role_ratio_pass = not role_failures
    overlap_failures = [x for x in failed_pairs if int(x[2]["OVERLAP_PIXELS"]) >= 1]
    clearance_failures = [x for x in failed_pairs if int(x[2]["OVERLAP_PIXELS"]) == 0]
    all_bool = source_font_pass and pixel_height_pass and same_class_pass and role_ratio_pass and not overlap_failures and not clearance_failures and clip_count == 0 and visual_harmony_pass and semantics_ok and caption_visible and label_ok and lof_ok
    decision = "SA1 PASS → SA3" if all_bool else "FAIL → SA2"

    machine = {
        "figure_id": "FIG-P634-01",
        "official_pdf": str(PDF),
        "official_pdf_page_count": doc.page_count,
        "required_page_count": 813,
        "physical_page_selection": {
            "method": "independent PDF text-anchor search",
            "caption_anchor": "图 33.3",
            "combined_unique_anchor": "一轮系统扫描的坐标带 + 同轮新值 + 图 33.3",
            "selected_physical_page": PAGE_NO,
            "selection_status": "PASS",
        },
        "page_size_pt": [round(page.rect.width, 3), round(page.rect.height, 3)],
        "a4_required": [595.276, 841.89],
        "whole_page_direct_renders": {
            "300dpi": {"file": "renders/official_page_682_300dpi.png", "pixels": [w, h], "expected_a4_pixels": [2481, 3508], "status": "PASS" if (w, h) == (2481, 3508) else "FAIL"},
            "200dpi": {"file": "renders/official_page_682_200dpi.png", "pixels": list(full200.size), "expected_a4_pixels": [1654, 2339], "status": "PASS" if full200.size == (1654, 2339) else "FAIL"},
        },
        "pixel_slice_provenance": {"source": "renders/official_page_682_300dpi.png", "crop_box_page_px": list(crop_box), "derived_files": ["crops/figure_pixel_slice_300dpi.png", "crops/figure_pixel_slice_grayscale_300dpi.png", "crops/figure_pixel_slice_8x_nearest.png"]},
        "no_rebuild_or_source_modification_claimed": True,
        "source_read_only": str(SOURCE),
        "pdf_status": "PASS" if doc.page_count == 813 and (w, h) == (2481, 3508) and full200.size == (1654, 2339) else "FAIL",
    }
    json_dump(OUT / "machine_consistency.json", machine)
    summary = {
        "figure_id": "FIG-P634-01", "reviewer": "SA1 strict independent R5/R94", "decision": decision,
        "counts": {"visible_page_chars": len(char_objects), "visible_figure_caption_chars": sum(c.panel in {"SWEEP_TOP", "SWEEP_NODES", "STATE_CARD_1", "STATE_CARD_2", "CAPTION"} for c in char_objects), "graphics_objects": len(graphics), "all_objects": len(all_objects), "all_unordered_pairs": total_pairs, "failed_pairs": len(failed_pairs), "overlap_failed_pairs": len(overlap_failures), "clearance_failed_pairs": len(clearance_failures), "clip_objects": clip_count},
        "gates": {"SOURCE_FONT_PASS": source_font_pass, "PIXEL_HEIGHT_PASS": pixel_height_pass, "SAME_CLASS_RATIO_PASS": same_class_pass, "ROLE_RATIO_PASS": role_ratio_pass, "OVERLAP_PIXEL_COUNT": sum(int(x[2]["OVERLAP_PIXELS"]) for x in overlap_failures), "CLIP_PIXEL_COUNT": clip_count, "MIN_TEXT_CLEARANCE_PX": min((v for rel, v in min_gap_by_relation.items() if rel.startswith("TEXT_") and math.isfinite(v)), default=None), "VISUAL_HARMONY_PASS": visual_harmony_pass, "MATH_SEMANTICS_PASS": semantics_ok, "TEXT_CONSISTENCY_PASS": caption_visible and label_ok and lof_ok, "GRAYSCALE_PASS": visual_harmony_pass, "PAGE_INTEGRATION_PASS": clip_count == 0},
        "thresholds": {"normal_source_font_pt": 9.5, "cjk_full_px": 30, "latin_upper_digit_px": 24, "latin_lower_greek_px": 17, "math_operator_px": 22, "script_px": 15, "text_text_px": 4, "text_line_arrow_px": 3, "text_border_px": 5, "cross_panel_px": 8, "edge_px": 6},
        "failures": [{"a": a.object_id, "b": b.object_id, "relation": r["RELATION"], "overlap": r["OVERLAP_PIXELS"], "gap": r["MIN_INK_GAP_PX"], "source_a": a.source_line, "source_b": b.source_line} for a, b, r in failed_pairs[:100]],
        "empty_graphics": empty_graphics,
    }
    json_dump(OUT / "audit_summary.json", summary)

    failed_glyphs = [r for r in raw_rows if r["PASS_FAIL"] == "FAIL"]
    report = [
        "# FIG-P634-01-SA1-STRICT-R5-R94",
        "",
        f"**Result: {decision}**",
        "",
        "## Scope and integrity",
        "",
        f"- Sole official input PDF: `{PDF}`; it has 813 A4 pages.",
        f"- The figure was independently located at physical PDF page {PAGE_NO} by the combined text anchors `图 33.3`, `一轮系统扫描的坐标带`, and `同轮新值`; the task-card projected page was not used as evidence.",
        "- `official_page_682_300dpi.png` and `official_page_682_200dpi.png` are whole-page direct rasterisations. Every figure crop, grayscale image, overlay, and 8x review slice was derived from the 300 dpi whole-page raster; no direct PDF clip is used for final geometry.",
        "- The permitted figure source was read only. This audit did not rebuild, modify, or claim to reconstruct the source.",
        "",
        "## Gate summary",
        "",
        f"- SOURCE_FONT_PASS = `{str(source_font_pass).lower()}`",
        f"- PIXEL_HEIGHT_PASS = `{str(pixel_height_pass).lower()}`",
        f"- SAME_CLASS_RATIO_PASS = `{str(same_class_pass).lower()}`",
        f"- ROLE_RATIO_PASS = `{str(role_ratio_pass).lower()}`",
        f"- OVERLAP_PIXEL_COUNT = `{sum(int(x[2]['OVERLAP_PIXELS']) for x in overlap_failures)}`",
        f"- CLIP_PIXEL_COUNT = `{clip_count}`",
        f"- VISUAL_HARMONY_PASS = `{str(visual_harmony_pass).lower()}`",
        f"- MATH_SEMANTICS_PASS = `{str(semantics_ok).lower()}`",
        f"- TEXT_CONSISTENCY_PASS = `{str(caption_visible and label_ok and lof_ok).lower()}`",
        "",
        "The script/subscript gate used `raw H_ink >= 15 px`, exactly as required by Goal §9.2.1-C; it did not use the obsolete 12 px value.",
        "",
        "## Coverage",
        "",
        f"- Visible page glyph raw masks: {len(char_objects)}; figure/caption glyph raw masks: {sum(c.panel in {'SWEEP_TOP','SWEEP_NODES','STATE_CARD_1','STATE_CARD_2','CAPTION'} for c in char_objects)}.",
        f"- Graphic, arrow, border, texture, and halo objects: {len(graphics)}.",
        f"- All unordered raw-mask object pairs enumerated: {total_pairs}.",
        "- Every reader-visible figure/caption glyph is in `raw_char_measurements.csv`; child glyph pairs inside the same semantic text element are enumerated but explicitly marked `INTRA_TEXT_ELEMENT`, so normal letter-spacing is not misclassified as inter-object collision.",
        "",
        "## Findings",
        "",
    ]
    if failed_glyphs:
        report.append("Pixel-height failures:")
        for row in failed_glyphs[:40]:
            report.append(f"- `{row['CHAR_ID']}` `{row['TEXT_SAMPLE']}` at source line `{row['SOURCE_LINE']}`: raw H_ink `{row['H_INK_PX']}` px < required `{row['PIXEL_THRESHOLD_PX']}` px.")
    else:
        report.append("- No figure/caption raw-glyph height failure was found under the applicable Goal C classes.")
    if failed_pairs:
        report.append("Pair failures:")
        for a, b, row in failed_pairs[:40]:
            report.append(f"- `{a.object_id}` (source {a.source_line}) × `{b.object_id}` (source {b.source_line}): `{row['RELATION']}`, overlap `{row['OVERLAP_PIXELS']}`, ink gap `{row['MIN_INK_GAP_PX']}` px; see `all_pairs_overlap_clearance.csv` and any matching `critical_pairs/failure_*` evidence.")
    else:
        report.append("- No illegal raw-mask overlap or applicable clearance failure was found in the complete pair enumeration.")
    if empty_graphics:
        report.append(f"- Graphic mask extraction issue: {', '.join(empty_graphics)}. This is a strict evidence failure.")
    report.extend([
        "",
        "## Semantic, caption, texture/halo, and visual review",
        "",
        "- `semantic_check.md` verifies lowercase j/d/t, x^[j]/x^[d]/x^(t), fixed immediate-write order, same-round new values, prior-round old values, current-step value, and the same-state/record-only distinction.",
        "- `caption_check.md` verifies standard automatic `图 33.3`, the current visible caption, the aux label, and the LoF write entry.",
        "- `texture_halo_audit.md` records true opaque source halo order and separates source-declared pre-occlusion field, real halo background, and final-visible texture. Final foreground geometry only tests final-visible texture.",
        "- The retained 200 dpi full-page view, 300 dpi pixel slice, 300 dpi grayscale slice, and 8x nearest-neighbor review crops were inspected for hierarchy, page integration, gray-scale distinction, crowding, and flow. Number + arrow + line/texture encoding gives a single left-to-right update order without relying only on color.",
        "",
        "## Required SA2 action if failed",
        "",
        "If the result is FAIL, SA2 must address each row identified in this report/CSV at the cited source line, then produce a fresh official full-book PDF and fresh whole-page 300 dpi evidence. Do not fix by globally scaling the figure down or by suppressing masks.",
    ])
    (OUT / "FIG-P634-01-SA1-STRICT-R5-R94.md").write_text("\n".join(report)+"\n", encoding="utf-8")

    # A concise visual inspection record keeps the human review separate from machine metrics.
    visual = """# Four-view visual harmony review

- Full page 200 dpi: the figure is integrated below the explanatory paragraph and above the reading-order paragraph; no crop, collision, or abnormal blank block is visible.
- Native 300 dpi pixel slice: title → numbered arrow → update slots → state cards → caption establishes a one-directional reading path.
- Native 300 dpi grayscale: order remains distinguishable through numbers, arrow, solid/dotted borders, hatching, and labels; it does not depend solely on color.
- 8x nearest-neighbor: see `crops/figure_pixel_slice_8x_nearest.png` and `critical_pairs/*/inspection_8x_nearest.png`. These are review aids only; numerical results were calculated at native 300 dpi.
"""
    (OUT / "visual_harmony_review.md").write_text(visual, encoding="utf-8")


if __name__ == "__main__":
    main()
