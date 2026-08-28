from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


HANDOFF_ID = "A-R110-P049-SA1-FRESH-ISOLATED-20260827"
UID = "FIG-P049-01"
ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C03\fig_v1_c03_gradient_contour.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C03.tex")
EXPECTED_PDF_SHA256 = "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3"
EXPECTED_SOURCE_SHA256 = "F9D4040ABB708F8043C619FB8C59B9CCCFDB2938E1BBD54B03B1E5D940F2999C"
CAPTION_NEEDLE = "梯度与等值线"
SCALE_300 = 300.0 / 72.0


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def union_rect(rects: list[fitz.Rect]) -> fitz.Rect:
    if not rects:
        raise ValueError("empty rectangle set")
    r = fitz.Rect(rects[0])
    for q in rects[1:]:
        r |= q
    return r


def render_clip(page: fitz.Page, clip: fitz.Rect, zoom: float, target: Path, grayscale: bool = False) -> Image.Image:
    cs = fitz.csGRAY if grayscale else fitz.csRGB
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, colorspace=cs, alpha=False)
    mode = "L" if grayscale else "RGB"
    im = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    im.save(target, dpi=(round(72 * zoom), round(72 * zoom)))
    return im


def rect_to_px(r: fitz.Rect, clip: fitz.Rect, scale: float, width: int, height: int) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor((r.x0 - clip.x0) * scale)) - 1)
    y0 = max(0, int(math.floor((r.y0 - clip.y0) * scale)) - 1)
    x1 = min(width, int(math.ceil((r.x1 - clip.x0) * scale)) + 1)
    y1 = min(height, int(math.ceil((r.y1 - clip.y0) * scale)) + 1)
    return x0, y0, x1, y1


def color_int_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def target_visible_mask(rgb: np.ndarray, vector_mask: np.ndarray, target_rgb: tuple[int, int, int]) -> np.ndarray:
    target = np.asarray(target_rgb, dtype=np.float32)
    v = 255.0 - target
    vv = float(np.dot(v, v))
    if vv < 100.0:
        return np.zeros(vector_mask.shape, dtype=bool)
    p = rgb.astype(np.float32)
    d = 255.0 - p
    alpha = np.sum(d * v, axis=2) / vv
    recon = 255.0 - alpha[..., None] * v
    residual = np.sqrt(np.sum((p - recon) ** 2, axis=2))
    contrast = np.max(d, axis=2)
    return vector_mask & (contrast >= 20.0) & (alpha >= 0.07) & (alpha <= 1.35) & (residual <= 34.0)


def bezier_points(p0, p1, p2, p3, steps=32):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u**3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t**3 * p3.y
        pts.append((x, y))
    return pts


def pxy(point, clip: fitz.Rect, scale: float) -> tuple[int, int]:
    return (int(round((point.x - clip.x0) * scale)), int(round((point.y - clip.y0) * scale)))


def drawing_vector_mask(drawing: dict, clip: fitz.Rect, scale: float, shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    width = max(1, int(math.ceil(float(drawing.get("width") or 0.6) * scale)))
    for item in drawing.get("items", []):
        kind = item[0]
        if kind == "l":
            cv2.line(mask, pxy(item[1], clip, scale), pxy(item[2], clip, scale), 255, width, cv2.LINE_AA)
        elif kind == "c":
            pts = bezier_points(item[1], item[2], item[3], item[4])
            arr = np.asarray([pxy(fitz.Point(x, y), clip, scale) for x, y in pts], dtype=np.int32)
            cv2.polylines(mask, [arr], False, 255, width, cv2.LINE_AA)
        elif kind == "re":
            r = item[1]
            a = pxy(fitz.Point(r.x0, r.y0), clip, scale)
            b = pxy(fitz.Point(r.x1, r.y1), clip, scale)
            if drawing.get("fill") is not None:
                cv2.rectangle(mask, a, b, 255, -1, cv2.LINE_AA)
            if drawing.get("color") is not None:
                cv2.rectangle(mask, a, b, 255, width, cv2.LINE_AA)
        elif kind == "qu":
            q = item[1]
            arr = np.asarray([pxy(q.ul, clip, scale), pxy(q.ur, clip, scale), pxy(q.lr, clip, scale), pxy(q.ll, clip, scale)], dtype=np.int32)
            if drawing.get("fill") is not None:
                cv2.fillPoly(mask, [arr], 255, cv2.LINE_AA)
            if drawing.get("color") is not None:
                cv2.polylines(mask, [arr], True, 255, width, cv2.LINE_AA)
    return mask > 32


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    if np.any(a & b):
        return 0.0
    if not np.any(a) or not np.any(b):
        return float("inf")
    inv = (~a).astype(np.uint8)
    dist = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    return float(dist[b].min())


def classify_span(text: str, font: str, size: float, max_size: float) -> tuple[str, int]:
    if not text.strip():
        return "WHITESPACE_NONINK", 0
    if size <= max_size * 0.76:
        return "SCRIPT_DERIVED", 15
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "CJK_FULL", 30
    named_letters = [unicodedata.name(ch, "") for ch in text if ch.isalpha()]
    if named_letters and all("SMALL" in name for name in named_letters):
        return "LATIN_OR_GREEK_XHEIGHT", 17
    if "Math" in font or any(ch in text for ch in "∇=<>≤≥/()²³⁴𝑃𝑓𝑥𝑐𝑣"):
        return "MATH_BASE", 22
    letters = [ch for ch in text if ch.isalpha()]
    if letters and all(ch.isupper() for ch in letters):
        return "LATIN_CAP_OR_DIGIT", 24
    return "LATIN_XHEIGHT", 17


def pt_dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(p, a, b) -> float:
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    den = vx * vx + vy * vy
    if den == 0:
        return pt_dist(p, a)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / den))
    q = (a[0] + t * vx, a[1] + t * vy)
    return pt_dist(p, q)


def main() -> None:
    started = now_iso()
    masks_dir = ROOT / "masks"
    rois_dir = ROOT / "rois"
    masks_dir.mkdir(exist_ok=False)
    rois_dir.mkdir(exist_ok=False)

    pdf_sha = sha256(PDF)
    source_sha = sha256(SOURCE)
    doc = fitz.open(PDF)
    hits = [i for i, p in enumerate(doc) if CAPTION_NEEDLE in p.get_text()]
    if len(hits) != 1:
        raise RuntimeError(f"caption locator expected one hit, got {hits}")
    page_index = hits[0]
    page = doc[page_index]
    drawings = page.get_drawings()
    figure_drawing_indices = [i for i, q in enumerate(drawings) if q["rect"].y1 >= 55 and q["rect"].y0 <= 229 and q["rect"].x1 >= 100 and q["rect"].x0 <= 490]
    visible_drawing_indices = [i for i in figure_drawing_indices if not (drawings[i].get("fill") == (1.0, 1.0, 1.0) and drawings[i].get("color") is None)]
    graphic_union = union_rect([drawings[i]["rect"] for i in figure_drawing_indices])
    graphic_clip = fitz.Rect(graphic_union.x0 - 8, graphic_union.y0 - 8, graphic_union.x1 + 8, graphic_union.y1 + 2)

    text_dict = page.get_text("dict")
    spans = []
    for block in text_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for s in line.get("spans", []):
                q = dict(s)
                q["bbox_rect"] = fitz.Rect(s["bbox"])
                spans.append(q)
    caption_spans = [s for s in spans if s["bbox_rect"].y0 >= 230 and s["bbox_rect"].y1 <= 249 and s["bbox_rect"].x0 >= 120 and s["bbox_rect"].x1 <= 490]
    caption_rect = union_rect([s["bbox_rect"] for s in caption_spans])
    associated_clip = fitz.Rect(min(graphic_clip.x0, caption_rect.x0 - 8), graphic_clip.y0, max(graphic_clip.x1, caption_rect.x1 + 8), caption_rect.y1 + 4)

    full300 = render_clip(page, page.rect, SCALE_300, ROOT / "01_full_page_native_300dpi.png")
    graphic300 = render_clip(page, graphic_clip, SCALE_300, ROOT / "02_graphic_native_300dpi.png")
    render_clip(page, graphic_clip, 1.0, ROOT / "03_graphic_native_1x.png")
    render_clip(page, graphic_clip, 8.0, ROOT / "04_graphic_native_8x.png")
    render_clip(page, graphic_clip, SCALE_300, ROOT / "05_graphic_grayscale_native_300dpi.png", grayscale=True)
    assoc300 = render_clip(page, associated_clip, SCALE_300, ROOT / "06_associated_crop_native_300dpi.png")
    assoc_rgb = np.asarray(assoc300.convert("RGB"))
    ah, aw = assoc_rgb.shape[:2]

    text_specs = {
        "T_AXIS_X1": dict(role="AXIS_LABEL", source_line=29, source_text="$x_1$", declared_pt=9.4, select=lambda x, y: 408 <= x <= 430 and 145 <= y <= 163),
        "T_AXIS_X2": dict(role="AXIS_LABEL", source_line=29, source_text="$x_2$", declared_pt=9.4, select=lambda x, y: 250 <= x <= 276 and 64 <= y <= 86),
        "T_CONTOUR_C1": dict(role="CONTOUR_LABEL", source_line=41, source_text="$c_1$", declared_pt=9.4, select=lambda x, y: 205 <= x <= 221 and 132 <= y <= 153),
        "T_CONTOUR_C2": dict(role="CONTOUR_LABEL", source_line=43, source_text="$c_2$", declared_pt=9.4, select=lambda x, y: 179 <= x <= 197 and 130 <= y <= 151),
        "T_CONTOUR_C3": dict(role="CONTOUR_LABEL", source_line=45, source_text="$c_3$", declared_pt=9.4, select=lambda x, y: 154 <= x <= 173 and 135 <= y <= 153),
        "T_CONTOUR_ORDER": dict(role="CONTOUR_ORDER", source_line=47, source_text="$c_1<c_2<c_3$", declared_pt=9.2, select=lambda x, y: 155 <= x <= 218 and 212 <= y <= 230),
        "T_POINT_P": dict(role="POINT_LABEL", source_line=55, source_text="$P=(2.4,1.08)$", declared_pt=9.4, select=lambda x, y: 255 <= x <= 322 and 132 <= y <= 153),
        "T_GRADIENT": dict(role="VECTOR_LABEL", source_line=57, source_text="$\\nabla f(P)$", declared_pt=9.4, select=lambda x, y: 310 <= x <= 341 and 91 <= y <= 107),
        "T_TANGENT": dict(role="VECTOR_LABEL", source_line=60, source_text="$\\boldsymbol v_{\\rm tan}$", declared_pt=9.4, select=lambda x, y: 292 <= x <= 312 and 96 <= y <= 113),
        "T_INCREASE": dict(role="DIRECTION_LABEL", source_line=65, source_text="$f$ 增大", declared_pt=9.2, select=lambda x, y: 334 <= x <= 369 and 172 <= y <= 190),
        "T_NOTE_1": dict(role="GUIDE_NOTE", source_line=68, source_text="1. 定位 $P$ 所在等值线", declared_pt=9.2, select=lambda x, y: 370 <= x <= 462 and 76 <= y <= 92),
        "T_NOTE_2": dict(role="GUIDE_NOTE", source_line=70, source_text="2. 梯度指向函数增大", declared_pt=9.2, select=lambda x, y: 370 <= x <= 462 and 94 <= y <= 112),
        "T_NOTE_3": dict(role="GUIDE_NOTE", source_line=72, source_text="3. $\\nabla f(P)^{\\mathsf T}\\boldsymbol v_{\\rm tan}=0$", declared_pt=9.2, select=lambda x, y: 370 <= x <= 452 and 112 <= y <= 132),
        "T_FUNCTION": dict(role="FORMULA_BLOCK", source_line=78, source_text="$f(x_1,x_2)=x_1^2/9+x_2^2/3.24$", declared_pt=9.2, select=lambda x, y: 228 <= x <= 348 and 212 <= y <= 231),
        "T_CAPTION": dict(role="CAPTION", source_line=81, source_text="图3.1 梯度与等值线。箭头在该点垂直于局部切线，并指向函数值增加的方向。", declared_pt=None, select=lambda x, y: 120 <= x <= 490 and 230 <= y <= 249),
    }

    text_members: dict[str, list[dict]] = {}
    assigned_span_ids: set[int] = set()
    for oid, spec in text_specs.items():
        chosen = []
        for s in spans:
            r = s["bbox_rect"]
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            if spec["select"](cx, cy):
                chosen.append(s)
                assigned_span_ids.add(id(s))
        if not chosen:
            raise RuntimeError(f"no PDF spans assigned to {oid}")
        text_members[oid] = chosen

    graphic_specs = {
        "G_AXIS_X": dict(role="AXIS", source_line=26, drawings=[1, 2]),
        "G_AXIS_Y": dict(role="AXIS", source_line=26, drawings=[3, 4]),
        "G_CONTOUR_C1": dict(role="DATA_CURVE", source_line=32, drawings=[5]),
        "G_CONTOUR_C2": dict(role="DATA_CURVE", source_line=35, drawings=[6]),
        "G_CONTOUR_C3": dict(role="DATA_CURVE", source_line=38, drawings=[7]),
        "G_POINT_P": dict(role="MARKER", source_line=53, drawings=[11]),
        "G_GRADIENT": dict(role="LINE_ARROW", source_line=56, drawings=[13, 14]),
        "G_TANGENT": dict(role="LINE", source_line=58, drawings=[16]),
        "G_RIGHT_ANGLE": dict(role="RIGHT_ANGLE_MARKER", source_line=61, drawings=[18]),
        "G_INCREASE": dict(role="LINE_ARROW", source_line=62, drawings=[19, 20]),
        "G_GUIDE_1": dict(role="GUIDE_LINE", source_line=73, drawings=[25]),
        "G_GUIDE_2": dict(role="GUIDE_LINE", source_line=74, drawings=[26]),
        "G_GUIDE_3": dict(role="GUIDE_LINE", source_line=75, drawings=[27]),
    }
    all_needed_drawing_indices = sorted({i for s in graphic_specs.values() for i in s["drawings"]})
    if not all(i in visible_drawing_indices for i in all_needed_drawing_indices):
        raise RuntimeError("expected figure drawing indices missing")

    object_rows = []
    object_masks: dict[str, np.ndarray] = {}
    span_rows = []
    text_measure_rows = []
    extracted_logic = {}

    for oid, spec in text_specs.items():
        members = text_members[oid]
        bbox = union_rect([s["bbox_rect"] for s in members])
        max_size = max(float(s["size"]) for s in members)
        omask = np.zeros((ah, aw), dtype=bool)
        heights = []
        thresholds = []
        for j, s in enumerate(members, 1):
            r = s["bbox_rect"]
            x0, y0, x1, y1 = rect_to_px(r, associated_clip, SCALE_300, aw, ah)
            region = assoc_rgb[y0:y1, x0:x1]
            target = color_int_to_rgb(int(s.get("color", 0)))
            base = np.ones((y1 - y0, x1 - x0), dtype=bool)
            ink = target_visible_mask(region, base, target) if s["text"].strip() else np.zeros(base.shape, dtype=bool)
            omask[y0:y1, x0:x1] |= ink
            ys, xs = np.nonzero(ink)
            h_ink = int(ys.max() - ys.min() + 1) if len(ys) else 0
            script_class, threshold = classify_span(s["text"], s["font"], float(s["size"]), max_size)
            if threshold:
                heights.append(h_ink)
                thresholds.append(threshold)
            span_rows.append({
                "ELEMENT_ID": oid,
                "SUBSPAN_ID": f"{oid}-S{j:02d}",
                "TEXT": s["text"],
                "FONT": s["font"],
                "PDF_FONT_SIZE_PT": f"{float(s['size']):.6f}",
                "SCRIPT_CLASS": script_class,
                "H_INK_PX_300": h_ink,
                "THRESHOLD_PX": threshold,
                "LEGACY_PIXEL_THRESHOLD_PASS": str(threshold == 0 or h_ink >= threshold).lower(),
                "PDF_BBOX": ";".join(f"{v:.6f}" for v in r),
                "OBSERVED_AT": now_iso(),
            })
        object_masks[oid] = omask
        Image.fromarray((omask.astype(np.uint8) * 255)).save(masks_dir / f"{oid}.png")
        mb = mask_bbox(omask)
        effective = max_size
        declared = spec["declared_pt"] if spec["declared_pt"] is not None else effective
        r168_font = "PASS" if effective >= 9.5 else "ADVISORY_8.8_TO_9.4_PT_NOT_HARD_FAILURE"
        text_measure_rows.append({
            "ELEMENT_ID": oid,
            "PANEL_ID": "FIGURE" if oid != "T_CAPTION" else "PAGE_CAPTION",
            "ROLE": spec["role"],
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": spec["source_line"],
            "DECLARED_PT": f"{declared:.6f}",
            "GRAPHICS_SCALE": "1.000000",
            "EFFECTIVE_PT_FINAL_PDF": f"{effective:.6f}",
            "TEXT_SAMPLE": spec["source_text"],
            "SCRIPT_CLASS": "MIXED" if len({r["SCRIPT_CLASS"] for r in span_rows if r["ELEMENT_ID"] == oid}) > 1 else next(r["SCRIPT_CLASS"] for r in span_rows if r["ELEMENT_ID"] == oid),
            "BBOX_X0": mb[0] if mb else "",
            "BBOX_Y0": mb[1] if mb else "",
            "BBOX_X1": mb[2] if mb else "",
            "BBOX_Y1": mb[3] if mb else "",
            "H_INK_PX": int(mask_bbox(omask)[3] - mask_bbox(omask)[1]) if mb else 0,
            "MIN_SUBSPAN_H_INK_PX": min(heights),
            "MIN_SUBSPAN_THRESHOLD_PX": min(thresholds),
            "PIXEL_HEIGHT_PASS": str(all(r["LEGACY_PIXEL_THRESHOLD_PASS"] == "true" for r in span_rows if r["ELEMENT_ID"] == oid)).lower(),
            "R168_FONT_STATUS": r168_font,
            "PASS_FAIL": "PASS" if np.any(omask) else "FAIL",
            "REASON": "Direct 300-dpi ink measurement; R168 makes 8.8-9.4 pt differences advisory when glyphs are correct and readable.",
        })
        extracted_logic[oid] = "".join(s["text"] for s in members)
        object_rows.append({
            "OBJECT_ID": oid,
            "CATEGORY": "TEXT" if oid != "T_CAPTION" else "CAPTION_TEXT",
            "ROLE": spec["role"],
            "PANEL_ID": "FIGURE" if oid != "T_CAPTION" else "PAGE_CAPTION",
            "PDF_X0": f"{bbox.x0:.6f}", "PDF_Y0": f"{bbox.y0:.6f}", "PDF_X1": f"{bbox.x1:.6f}", "PDF_Y1": f"{bbox.y1:.6f}",
            "SOURCE_LINE": spec["source_line"],
            "SOURCE_TEXT_OR_GEOMETRY": spec["source_text"],
            "PDF_EXTRACTED_TEXT": extracted_logic[oid],
            "MASK_FILE": f"masks/{oid}.png",
            "DENOMINATOR_STATUS": "FROZEN_INCLUDED",
        })

    for oid, spec in graphic_specs.items():
        omask = np.zeros((ah, aw), dtype=bool)
        rects = []
        for idx in spec["drawings"]:
            q = drawings[idx]
            rects.append(q["rect"])
            vec = drawing_vector_mask(q, associated_clip, SCALE_300, (ah, aw))
            colors = []
            if q.get("color") is not None:
                colors.append(tuple(int(round(v * 255)) for v in q["color"]))
            if q.get("fill") is not None and tuple(q["fill"]) != (1.0, 1.0, 1.0):
                colors.append(tuple(int(round(v * 255)) for v in q["fill"]))
            visible = np.zeros((ah, aw), dtype=bool)
            for c in colors:
                visible |= target_visible_mask(assoc_rgb, vec, c)
            # Later opaque white label backgrounds occlude earlier curves and
            # axes in the final PDF.  Remove those areas before pair tests;
            # otherwise text ink can be mistaken for a hidden vector path.
            for later_idx in figure_drawing_indices:
                if later_idx <= idx:
                    continue
                later = drawings[later_idx]
                fill = later.get("fill")
                if fill is None or not all(float(v) >= 0.99 for v in fill):
                    continue
                if later.get("type") not in ("f", "fs"):
                    continue
                visible &= ~drawing_vector_mask(later, associated_clip, SCALE_300, (ah, aw))
            omask |= visible
        bbox = union_rect(rects)
        object_masks[oid] = omask
        Image.fromarray((omask.astype(np.uint8) * 255)).save(masks_dir / f"{oid}.png")
        object_rows.append({
            "OBJECT_ID": oid,
            "CATEGORY": "GRAPHIC",
            "ROLE": spec["role"],
            "PANEL_ID": "FIGURE",
            "PDF_X0": f"{bbox.x0:.6f}", "PDF_Y0": f"{bbox.y0:.6f}", "PDF_X1": f"{bbox.x1:.6f}", "PDF_Y1": f"{bbox.y1:.6f}",
            "SOURCE_LINE": spec["source_line"],
            "SOURCE_TEXT_OR_GEOMETRY": oid,
            "PDF_EXTRACTED_TEXT": "",
            "MASK_FILE": f"masks/{oid}.png",
            "DENOMINATOR_STATUS": "FROZEN_INCLUDED",
        })

    object_rows.sort(key=lambda r: r["OBJECT_ID"])
    object_ids = [r["OBJECT_ID"] for r in object_rows]
    if len(object_ids) != len(set(object_ids)):
        raise RuntimeError("duplicate visible object id")

    intentional = {
        frozenset(("G_AXIS_X", "G_AXIS_Y")),
        frozenset(("G_AXIS_X", "G_CONTOUR_C1")), frozenset(("G_AXIS_X", "G_CONTOUR_C2")), frozenset(("G_AXIS_X", "G_CONTOUR_C3")),
        frozenset(("G_AXIS_Y", "G_CONTOUR_C1")), frozenset(("G_AXIS_Y", "G_CONTOUR_C2")), frozenset(("G_AXIS_Y", "G_CONTOUR_C3")),
        frozenset(("G_CONTOUR_C3", "G_POINT_P")),
        frozenset(("G_POINT_P", "G_GRADIENT")), frozenset(("G_POINT_P", "G_TANGENT")),
        frozenset(("G_GRADIENT", "G_RIGHT_ANGLE")), frozenset(("G_TANGENT", "G_RIGHT_ANGLE")),
        frozenset(("G_GUIDE_2", "G_GRADIENT")), frozenset(("G_GUIDE_3", "G_RIGHT_ANGLE")),
    }
    category = {r["OBJECT_ID"]: r["CATEGORY"] for r in object_rows}
    pair_rows = []
    illegal_total = 0
    candidate_total = 0
    for i, a in enumerate(object_ids):
        for b in object_ids[i + 1:]:
            ma, mb = object_masks[a], object_masks[b]
            overlap = int(np.count_nonzero(ma & mb))
            dist = mask_distance(ma, mb)
            text_involved = category[a] != "GRAPHIC" or category[b] != "GRAPHIC"
            if text_involved:
                policy = "ZERO_ILLEGAL_OVERLAP"
                threshold = 4 if category[a] != "GRAPHIC" and category[b] != "GRAPHIC" else 3
                illegal = overlap
                classification = "TRUE_COLLISION" if illegal else "SEPARATE_CLEAR"
            elif frozenset((a, b)) in intentional:
                policy = "ALLOWED_INTENTIONAL_GEOMETRY_CONTACT"
                threshold = 0
                illegal = 0
                classification = "INTENTIONAL_CONTACT_OR_PROXIMITY" if overlap or dist <= 3 else "SEMANTICALLY_RELATED_CLEAR"
            else:
                policy = "GEOMETRY_PAIR_REVIEWED"
                threshold = 0
                illegal = 0
                classification = "GEOMETRY_CONTACT_REVIEW" if overlap else "SEPARATE_CLEAR"
            candidate_total += overlap
            illegal_total += illegal
            protocol_clear = (dist >= threshold) if threshold else True
            pair_rows.append({
                "PAIR_ID": f"PAIR-{len(pair_rows)+1:04d}",
                "OBJECT_A": a, "OBJECT_B": b,
                "CATEGORY_A": category[a], "CATEGORY_B": category[b],
                "POLICY": policy,
                "RAW_SHARED_VISIBLE_PIXEL_COUNT": overlap,
                "CANONICAL_ILLEGAL_OVERLAP_PIXEL_COUNT": illegal,
                "MIN_FOREGROUND_CLEARANCE_PX": "INF" if math.isinf(dist) else f"{dist:.3f}",
                "PROTOCOL_CLEARANCE_THRESHOLD_PX": threshold,
                "PROTOCOL_CLEARANCE_PASS": str(protocol_clear).lower(),
                "R168_HARD_OVERLAP_PASS": str(illegal == 0).lower(),
                "CLASSIFICATION": classification,
            })

    expected_pairs = len(object_ids) * (len(object_ids) - 1) // 2
    if len(pair_rows) != expected_pairs:
        raise RuntimeError("unordered pair denominator mismatch")

    # Geometry and mathematical semantics recomputed from the source coordinates.
    P = (2.4, 1.08)
    G = (3.12, 1.98)
    T = (3.34, 0.33)
    Tm = (1.46, 1.83)
    grad = (2 * P[0] / 9.0, 2 * P[1] / 3.24)
    grad_arrow = (G[0] - P[0], G[1] - P[1])
    tangent = (T[0] - Tm[0], T[1] - Tm[1])
    p_to_t = (T[0] - P[0], T[1] - P[1])
    dot = grad[0] * tangent[0] + grad[1] * tangent[1]
    cosang = dot / (math.hypot(*grad) * math.hypot(*tangent))
    right_dot = grad_arrow[0] * p_to_t[0] + grad_arrow[1] * p_to_t[1]
    right_cos = right_dot / (math.hypot(*grad_arrow) * math.hypot(*p_to_t))
    right_angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, right_cos))))
    scale_factor = grad_arrow[0] / grad[0]
    contour_params = [("c1", 1.5, 0.9), ("c2", 2.4, 1.44), ("c3", 3.0, 1.8)]
    contour_values = [{"label": n, "a": a, "b": b, "f_constant_x": a * a / 9.0, "f_constant_y": b * b / 3.24} for n, a, b in contour_params]
    axis_pt_per_unit = (drawings[7]["rect"].x1 - drawings[7]["rect"].x0) / 6.0
    px_per_axis_unit_300 = axis_pt_per_unit * SCALE_300
    guide1_end = (2.75, 1.36)
    guide2_end = G
    guide3_end = (2.67, 1.23)
    guide_semantics = {
        "guide_1": {
            "note": "定位 P 所在等值线",
            "endpoint": guide1_end,
            "distance_to_P_axis_units": pt_dist(guide1_end, P),
            "distance_to_P_px_300": pt_dist(guide1_end, P) * px_per_axis_unit_300,
            "contour_c3_residual_abs": abs(guide1_end[0] ** 2 / 9.0 + guide1_end[1] ** 2 / 3.24 - 1.0),
            "distance_to_gradient_segment_axis_units": point_segment_distance(guide1_end, P, G),
            "distance_to_gradient_segment_px_300": point_segment_distance(guide1_end, P, G) * px_per_axis_unit_300,
            "exact_target_gate": False,
            "reason": "Endpoint is neither P nor the c3 contour and is materially nearer the gradient segment than the stated contour target.",
        },
        "guide_2": {
            "note": "梯度指向函数增大",
            "endpoint": guide2_end,
            "target_G": G,
            "distance_to_target_axis_units": pt_dist(guide2_end, G),
            "exact_target_gate": True,
        },
        "guide_3": {
            "note": "gradient-transpose times tangent equals zero",
            "endpoint": guide3_end,
            "distance_to_P_axis_units": pt_dist(guide3_end, P),
            "distance_to_P_px_300": pt_dist(guide3_end, P) * px_per_axis_unit_300,
            "distance_to_right_angle_visible_mask_px_300": mask_distance(object_masks["G_GUIDE_3"], object_masks["G_RIGHT_ANGLE"]),
            "exact_target_gate": mask_distance(object_masks["G_GUIDE_3"], object_masks["G_RIGHT_ANGLE"]) <= 3.0,
        },
    }
    geometry = {
        "observed_at": now_iso(),
        "function": "f(x1,x2)=x1^2/9+x2^2/3.24",
        "contours": contour_values,
        "contour_order_strict": contour_values[0]["f_constant_x"] < contour_values[1]["f_constant_x"] < contour_values[2]["f_constant_x"],
        "P": P,
        "f_P": P[0] ** 2 / 9.0 + P[1] ** 2 / 3.24,
        "gradient_at_P": grad,
        "gradient_arrow_vector": grad_arrow,
        "gradient_arrow_positive_scale_factor": scale_factor,
        "gradient_direction_exact_gate": scale_factor > 0 and abs(grad_arrow[1] / grad[1] - scale_factor) < 1e-12,
        "tangent_vector_T_minus_Tm": tangent,
        "gradient_dot_tangent": dot,
        "normalized_orthogonality_residual": abs(cosang),
        "orthogonality_angle_deg": math.degrees(math.acos(max(-1.0, min(1.0, abs(cosang))))),
        "P_is_tangent_segment_midpoint": [round((Tm[0] + T[0]) / 2, 12), round((Tm[1] + T[1]) / 2, 12)] == [P[0], P[1]],
        "right_angle_marker_source_triplet": "T--P--G",
        "right_angle_dot": right_dot,
        "right_angle_deg": right_angle_deg,
        "right_angle_gate": abs(90.0 - right_angle_deg) <= 0.2,
        "guide_line_semantics": guide_semantics,
    }

    all_extracted = "".join(extracted_logic.values())
    missing_or_tofu = ("\ufffd" in all_extracted) or ("□" in all_extracted)
    min_text_edge = float("inf")
    for oid in text_specs:
        if oid == "T_CAPTION":
            continue
        mb = mask_bbox(object_masks[oid])
        if mb:
            min_text_edge = min(min_text_edge, mb[0], mb[1], aw - mb[2], ah - mb[3])
    protocol_pixel_pass = all(r["LEGACY_PIXEL_THRESHOLD_PASS"] == "true" for r in span_rows)
    legacy_source_font_pass = all(float(r["EFFECTIVE_PT_FINAL_PDF"]) >= 9.5 for r in text_measure_rows if r["ELEMENT_ID"] != "T_CAPTION")
    hard_gates = {
        "PDF_IDENTITY": pdf_sha == EXPECTED_PDF_SHA256 and PDF.stat().st_size == 4967063 and len(doc) == 817,
        "SOURCE_IDENTITY": source_sha == EXPECTED_SOURCE_SHA256 and SOURCE.stat().st_size == 4189,
        "UNIQUE_R110_LOCATOR": hits == [47],
        "VISIBLE_OBJECT_DENOMINATOR_28": len(object_ids) == 28,
        "ALL_UNORDERED_PAIRS_378": len(pair_rows) == 378,
        "ALL_OBJECT_MASKS_NONEMPTY": all(np.any(m) for m in object_masks.values()),
        "NO_MISSING_TOFU_OR_REPLACEMENT_CODEPOINT": not missing_or_tofu,
        "DIRECT_300DPI_PIXEL_HEIGHT_LEGACY_THRESHOLDS": protocol_pixel_pass,
        "ZERO_ILLEGAL_TEXT_INVOLVING_OVERLAP": illegal_total == 0,
        "ZERO_CLIP_PIXELS": min_text_edge >= 6,
        "CONTOUR_ORDER_AND_P_MEMBERSHIP": geometry["contour_order_strict"] and abs(geometry["f_P"] - 1.0) < 1e-12,
        "GRADIENT_DIRECTION": geometry["gradient_direction_exact_gate"],
        "TANGENT_ORTHOGONALITY": geometry["normalized_orthogonality_residual"] < 0.002,
        "RIGHT_ANGLE_MARKER": geometry["right_angle_gate"],
        "GUIDE_1_TARGET_SEMANTICS": guide_semantics["guide_1"]["exact_target_gate"],
        "GUIDE_2_TARGET_SEMANTICS": guide_semantics["guide_2"]["exact_target_gate"],
        "GUIDE_3_TARGET_SEMANTICS": guide_semantics["guide_3"]["exact_target_gate"],
    }
    machine_summary = {
        "HANDOFF_ID": HANDOFF_ID,
        "UID": UID,
        "started_at": started,
        "completed_at": now_iso(),
        "R168": "8.8-9.4 pt and minor font/pixel contour differences are advisory; hard failure is reserved for missing/tofu/wrong codepoint/math meaning, unreadability/obvious imbalance, clipping/illegal overlap, or geometry/semantic errors.",
        "legacy_source_font_9_5_pass": legacy_source_font_pass,
        "legacy_source_font_status_under_R168": "ADVISORY_ONLY" if not legacy_source_font_pass else "PASS",
        "hard_gates": hard_gates,
        "hard_gate_pass": all(hard_gates.values()),
        "failed_hard_gates": [k for k, v in hard_gates.items() if not v],
        "visible_object_count": len(object_ids),
        "unordered_pair_count": len(pair_rows),
        "raw_shared_visible_pixels_all_pairs_sum_nonunique": candidate_total,
        "canonical_illegal_overlap_pixels": illegal_total,
        "clip_pixel_count": 0 if min_text_edge >= 6 else 1,
        "min_text_to_associated_crop_edge_px": min_text_edge,
        "pixel_adjudication_status": "CLEAR" if illegal_total == 0 else "TRUE_COLLISION",
    }

    identity = {
        "HANDOFF_ID": HANDOFF_ID,
        "UID": UID,
        "observed_at": now_iso(),
        "pdf": {"path": str(PDF), "size": PDF.stat().st_size, "sha256": pdf_sha, "pages": len(doc)},
        "source": {"path": str(SOURCE), "size": SOURCE.stat().st_size, "sha256": source_sha},
        "chapter_context": {"path": str(CHAPTER), "lines": "131-147"},
        "models": {"SA1_MODEL": "gpt-5.6-sol", "SA1_REASONING": "xhigh"},
        "isolation": "Fresh isolated; no old P049 evidence, roles, state, handoffs, reports, inventory, chat, Git history, or other UID conclusions were read.",
    }
    locator = {
        "observed_at": now_iso(),
        "caption_needle": CAPTION_NEEDLE,
        "hit_page_indices_zero_based": hits,
        "physical_page_one_based": page_index + 1,
        "printed_page_from_header": 35,
        "page_rect_pdf_points": list(page.rect),
        "graphic_clip_pdf_points": list(graphic_clip),
        "associated_clip_pdf_points": list(associated_clip),
        "figure_drawing_indices": figure_drawing_indices,
        "visible_drawing_indices": visible_drawing_indices,
    }
    write_json(ROOT / "identity.json", identity)
    write_json(ROOT / "locator.json", locator)
    write_json(ROOT / "geometry_semantics.json", geometry)
    write_json(ROOT / "machine_gate_summary.json", machine_summary)

    object_fields = ["OBJECT_ID", "CATEGORY", "ROLE", "PANEL_ID", "PDF_X0", "PDF_Y0", "PDF_X1", "PDF_Y1", "SOURCE_LINE", "SOURCE_TEXT_OR_GEOMETRY", "PDF_EXTRACTED_TEXT", "MASK_FILE", "DENOMINATOR_STATUS"]
    pair_fields = ["PAIR_ID", "OBJECT_A", "OBJECT_B", "CATEGORY_A", "CATEGORY_B", "POLICY", "RAW_SHARED_VISIBLE_PIXEL_COUNT", "CANONICAL_ILLEGAL_OVERLAP_PIXEL_COUNT", "MIN_FOREGROUND_CLEARANCE_PX", "PROTOCOL_CLEARANCE_THRESHOLD_PX", "PROTOCOL_CLEARANCE_PASS", "R168_HARD_OVERLAP_PASS", "CLASSIFICATION"]
    text_fields = ["ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT_FINAL_PDF", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "MIN_SUBSPAN_H_INK_PX", "MIN_SUBSPAN_THRESHOLD_PX", "PIXEL_HEIGHT_PASS", "R168_FONT_STATUS", "PASS_FAIL", "REASON"]
    span_fields = ["ELEMENT_ID", "SUBSPAN_ID", "TEXT", "FONT", "PDF_FONT_SIZE_PT", "SCRIPT_CLASS", "H_INK_PX_300", "THRESHOLD_PX", "LEGACY_PIXEL_THRESHOLD_PASS", "PDF_BBOX", "OBSERVED_AT"]
    write_csv(ROOT / "visible_object_denominator.csv", object_rows, object_fields)
    write_csv(ROOT / "all_unordered_pairs.csv", pair_rows, pair_fields)
    write_csv(ROOT / "text_element_measurements_300dpi.csv", text_measure_rows, text_fields)
    write_csv(ROOT / "text_subspan_measurements_300dpi.csv", span_rows, span_fields)

    # Overlays are view artifacts only; measurements above remain on the direct native 300-dpi raster.
    overlay = assoc300.convert("RGB")
    draw = ImageDraw.Draw(overlay)
    palette = {"TEXT": (220, 40, 40), "CAPTION_TEXT": (180, 40, 180), "GRAPHIC": (20, 130, 220)}
    font = ImageFont.load_default()
    for row in object_rows:
        oid = row["OBJECT_ID"]
        mb = mask_bbox(object_masks[oid])
        if not mb:
            continue
        color = palette[row["CATEGORY"]]
        draw.rectangle(mb, outline=color, width=2)
        draw.rectangle((mb[0], max(0, mb[1] - 11), mb[0] + 6 * len(oid) + 3, mb[1]), fill=(255, 255, 255))
        draw.text((mb[0] + 1, max(0, mb[1] - 11)), oid, fill=color, font=font)
    overlay.save(ROOT / "07_visible_object_overlay_300dpi.png", dpi=(300, 300))

    text_overlay = assoc300.convert("RGB")
    td = ImageDraw.Draw(text_overlay)
    for row in object_rows:
        if row["CATEGORY"] == "GRAPHIC":
            continue
        oid = row["OBJECT_ID"]
        mb = mask_bbox(object_masks[oid])
        if mb:
            td.rectangle(mb, outline=(220, 35, 35), width=2)
            td.text((mb[0] + 1, max(0, mb[1] - 11)), oid, fill=(220, 35, 35), font=font)
    text_overlay.save(ROOT / "08_text_measurement_overlay_300dpi.png", dpi=(300, 300))

    roi_specs = {
        "09_gradient_tangent_right_angle_roi_native_8x.png": fitz.Rect(286, 88, 354, 158),
        "10_guide_lines_and_notes_roi_native_8x.png": fitz.Rect(325, 72, 464, 138),
        "11_contours_labels_formula_roi_native_8x.png": fitz.Rect(150, 106, 350, 230),
    }
    for name, clip in roi_specs.items():
        render_clip(page, clip, 8.0, rois_dir / name)

    # Compact review sheet; labelled as a display-only composition, never used for measurements.
    panels = [
        (Image.open(ROOT / "02_graphic_native_300dpi.png").convert("RGB"), "A  Native graphic 300 dpi"),
        (Image.open(ROOT / "05_graphic_grayscale_native_300dpi.png").convert("RGB"), "B  Grayscale 300 dpi"),
        (Image.open(ROOT / "07_visible_object_overlay_300dpi.png").convert("RGB"), "C  Frozen 28-object overlay"),
        (Image.open(rois_dir / "09_gradient_tangent_right_angle_roi_native_8x.png").convert("RGB"), "D  Native 8x geometry ROI"),
        (Image.open(rois_dir / "10_guide_lines_and_notes_roi_native_8x.png").convert("RGB"), "E  Native 8x guide ROI"),
        (Image.open(ROOT / "01_full_page_native_300dpi.png").convert("RGB"), "F  Full page 300 dpi"),
    ]
    thumb_w, thumb_h = 950, 620
    sheet = Image.new("RGB", (thumb_w * 2 + 60, thumb_h * 3 + 120), "white")
    sd = ImageDraw.Draw(sheet)
    for idx, (im, label) in enumerate(panels):
        col, row = idx % 2, idx // 2
        x, y = 20 + col * (thumb_w + 20), 20 + row * (thumb_h + 30)
        fit = im.copy()
        fit.thumbnail((thumb_w, thumb_h - 28), Image.Resampling.LANCZOS)
        sheet.paste(fit, (x + (thumb_w - fit.width) // 2, y + 24))
        sd.text((x, y), label, fill=(0, 0, 0), font=font)
    sd.text((20, sheet.height - 26), "DISPLAY-ONLY CONTACT SHEET. Machine measurements use direct native 300-dpi rasters; ROIs are direct native 8x renders.", fill=(0, 0, 0), font=font)
    sheet.save(ROOT / "12_final_review_contact_sheet.png")

    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    chapter_lines = CHAPTER.read_text(encoding="utf-8").splitlines()
    (ROOT / "source_excerpt_current.txt").write_text("\n".join(f"{i+1}: {line}" for i, line in enumerate(source_lines)) + "\n", encoding="utf-8")
    (ROOT / "neighbor_context_current.txt").write_text("\n".join(f"{i+1}: {chapter_lines[i]}" for i in range(130, 147)) + "\n", encoding="utf-8")

    manifest_rows = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "build_sa1_evidence.py"):
        manifest_rows.append({"relative_path": path.relative_to(ROOT).as_posix(), "size": path.stat().st_size, "generated_or_observed_at": now_iso()})
    write_csv(ROOT / "pre_manual_manifest.csv", manifest_rows, ["relative_path", "size", "generated_or_observed_at"])


if __name__ == "__main__":
    main()
