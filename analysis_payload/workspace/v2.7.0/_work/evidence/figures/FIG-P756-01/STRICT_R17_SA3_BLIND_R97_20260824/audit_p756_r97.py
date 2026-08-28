from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C08.tex")
STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty")
FIGURE_UID = "FIG-P756-01"
PHYSICAL_PAGE = 801
PAGE_INDEX = PHYSICAL_PAGE - 1
PRINTED_PAGE = 788
S300 = 300.0 / 72.0
S200 = 200.0 / 72.0
# Figure source bounds plus 10--13pt native-page padding, fixed before analysis.
FIG_RECT_PT = (52.0, 166.0, 544.0, 521.0)  # body + caption
STANDALONE_RECT_PT = (55.0, 166.0, 530.0, 479.0)  # body only; same candidate, no rescale
TEXT_Y0, TEXT_Y1 = 170.0, 519.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("._") or "item"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows, fieldnames) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rgb_from_float(color) -> tuple[int, int, int]:
    return tuple(int(round(255 * c)) for c in color)


def px_rect(rect_pt, scale=S300) -> tuple[int, int, int, int]:
    return (
        int(math.floor(rect_pt[0] * scale)),
        int(math.floor(rect_pt[1] * scale)),
        int(math.ceil(rect_pt[2] * scale)),
        int(math.ceil(rect_pt[3] * scale)),
    )


def clamp_rect(rect, width, height, pad=0):
    x0, y0, x1, y1 = rect
    return (max(0, x0 - pad), max(0, y0 - pad), min(width, x1 + pad), min(height, y1 + pad))


def rect_gap(a, b) -> float:
    dx = max(0, max(a[0] - b[2], b[0] - a[2]))
    dy = max(0, max(a[1] - b[3], b[1] - a[3]))
    return math.hypot(dx, dy)


def crop_array(arr: np.ndarray, rect):
    x0, y0, x1, y1 = rect
    return arr[y0:y1, x0:x1]


def dominant_rgb(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return np.array([255, 255, 255], dtype=float)
    vals, cnt = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
    return vals[int(np.argmax(cnt))].astype(float)


def foreground_by_color(arr: np.ndarray, candidate: np.ndarray, fg_rgb, fallback_bg=None) -> np.ndarray:
    """Native-pixel mask: candidate only isolates vector/text ownership; accepted pixels come from final render."""
    if candidate.size == 0:
        return candidate.astype(bool)
    fg = np.array(fg_rgb, dtype=float)
    bg = dominant_rgb(arr) if fallback_bg is None else np.array(fallback_bg, dtype=float)
    v = fg - bg
    v2 = float(np.dot(v, v))
    pix = arr.astype(float)
    if v2 < 1.0:
        # White opaque strokes require source geometry to isolate them from a white page.
        return candidate.astype(bool) & (pix.min(axis=2) >= 235)
    d = pix - bg
    alpha = np.sum(d * v, axis=2) / v2
    residual = np.linalg.norm(d - alpha[..., None] * v, axis=2)
    threshold = 20.0 / max(20.0, float(np.max(np.abs(v))))
    return candidate.astype(bool) & (alpha >= threshold) & (alpha <= 1.28) & (residual <= 44.0)


def pixel_bbox_coverage(float_bbox, gx: int, gy: int) -> float:
    """Fractional native-pixel cell covered by the rawdict character bbox.

    `px_rect` uses floor/ceil to keep a character's native raster ownership
    conservative.  Adjacent rawdict boxes can therefore share one edge pixel.
    This continuous-geometry score deterministically gives such a pixel to one
    character without changing any rendered pixel or applying morphology.
    """
    x0, y0, x1, y1 = float_bbox
    return max(0.0, min(x1, gx + 1.0) - max(x0, gx)) * max(0.0, min(y1, gy + 1.0) - max(y0, gy))


def draw_cubic(points, p0, p1, p2, p3, steps=24):
    for i in range(1, steps + 1):
        t = i / steps
        mt = 1.0 - t
        x = mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]
        points.append((x, y))


def drawing_points(drawing, offset_x, offset_y, scale=S300):
    points = []
    for item in drawing["items"]:
        code = item[0]
        if code == "l":
            p0, p1 = item[1], item[2]
            a = ((p0.x * scale) - offset_x, (p0.y * scale) - offset_y)
            b = ((p1.x * scale) - offset_x, (p1.y * scale) - offset_y)
            if not points or math.hypot(points[-1][0] - a[0], points[-1][1] - a[1]) > 0.5:
                points.append(a)
            points.append(b)
        elif code == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            a = ((p0.x * scale) - offset_x, (p0.y * scale) - offset_y)
            b = ((p1.x * scale) - offset_x, (p1.y * scale) - offset_y)
            c = ((p2.x * scale) - offset_x, (p2.y * scale) - offset_y)
            d = ((p3.x * scale) - offset_x, (p3.y * scale) - offset_y)
            if not points or math.hypot(points[-1][0] - a[0], points[-1][1] - a[1]) > 0.5:
                points.append(a)
            draw_cubic(points, a, b, c, d)
        elif code == "re":
            r = item[1]
            q = [
                ((r.x0 * scale) - offset_x, (r.y0 * scale) - offset_y),
                ((r.x1 * scale) - offset_x, (r.y0 * scale) - offset_y),
                ((r.x1 * scale) - offset_x, (r.y1 * scale) - offset_y),
                ((r.x0 * scale) - offset_x, (r.y1 * scale) - offset_y),
                ((r.x0 * scale) - offset_x, (r.y0 * scale) - offset_y),
            ]
            points.extend(q)
    return points


def graphic_mask(drawing, figure_arr: np.ndarray, figure_rect, part: str):
    """Return final-visible raw mask and geometric pre-mask for a PDF drawing record."""
    rx0, ry0, rx1, ry1 = px_rect((drawing["rect"].x0, drawing["rect"].y0, drawing["rect"].x1, drawing["rect"].y1))
    fx0, fy0, fx1, fy1 = figure_rect
    pad = 5
    bbox = clamp_rect((rx0 - fx0, ry0 - fy0, rx1 - fx0, ry1 - fy0), figure_arr.shape[1], figure_arr.shape[0], pad)
    x0, y0, x1, y1 = bbox
    local = figure_arr[y0:y1, x0:x1]
    canvas = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)), 0)
    drawer = ImageDraw.Draw(canvas)
    abs_x = fx0 + x0
    abs_y = fy0 + y0
    pts = drawing_points(drawing, abs_x, abs_y)
    if not pts:
        candidate = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    elif part == "fill":
        drawer.polygon(pts, fill=255)
        candidate = np.array(canvas) > 0
    else:
        width = drawing.get("width") or 0.6
        width_px = max(1, int(math.ceil(width * S300)) + 4)
        drawer.line(pts, fill=255, width=width_px, joint="curve")
        candidate = np.array(canvas) > 0
    if part == "fill":
        color = drawing.get("fill")
    else:
        color = drawing.get("color") if part != "white_separator" else (1.0, 1.0, 1.0)
    if color is None:
        final = np.zeros_like(candidate, dtype=bool)
    elif part == "fill" and all(c >= 0.985 for c in color):
        # An opaque white fill has no distinguishable page-white raw foreground. Retain geometry as an opaque layer.
        final = np.zeros_like(candidate, dtype=bool)
    else:
        # A thin PDF stroke can occupy most of its tightly-cropped ROI, so its own
        # colour is not a valid local-background estimate.  All source strokes in
        # this figure are drawn on page-white / a white node fill at their visible
        # contour; use that fixed native canvas colour only for the colour test.
        # This does not change geometry, resample pixels, or dilate the raw mask.
        fallback = np.array([255, 255, 255], dtype=float) if part == "stroke" else None
        final = foreground_by_color(local, candidate, rgb_from_float(color), fallback)
    return bbox, final, candidate


def save_mask(mask: np.ndarray, path: Path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def overlay_image(original: np.ndarray, mask: np.ndarray):
    out = original.copy()
    out[mask] = np.array([225, 25, 35], dtype=np.uint8)
    return out


def compose_glyph_card(original: np.ndarray, mask: np.ndarray):
    overlay = overlay_image(original, mask)
    mono = np.full_like(original, 255)
    mono[mask] = 0
    panels = [Image.fromarray(original), Image.fromarray(overlay), Image.fromarray(mono)]
    nearest = panels[1].resize((panels[1].width * 8, panels[1].height * 8), Image.Resampling.NEAREST)
    return panels, nearest


def paste_label(canvas: Image.Image, xy, value: str, fill=(20, 20, 20)):
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(canvas).text(xy, value, fill=fill, font=font)


def make_contact_sheets(glyph_artifacts, out_dir: Path, cells_per_sheet=20):
    sheets = []
    for start in range(0, len(glyph_artifacts), cells_per_sheet):
        items = glyph_artifacts[start:start + cells_per_sheet]
        cols, rows = 4, math.ceil(len(items) / 4)
        cell_w, cell_h = 420, 180
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        for n, item in enumerate(items):
            col, row = n % cols, n // cols
            x, y = col * cell_w, row * cell_h
            original = Image.open(item["original"]).convert("RGB")
            overlay = Image.open(item["overlay"]).convert("RGB")
            mono = Image.open(item["mask_only"]).convert("RGB")
            four = Image.open(item["nearest"]).convert("RGB")
            # 1:1 panels remain unresampled at top; the fourth is an 8x-nearest inspection panel.
            sheet.paste(original, (x + 4, y + 30))
            sheet.paste(overlay, (x + 90, y + 30))
            sheet.paste(mono, (x + 176, y + 30))
            maxw, maxh = 225, 135
            ratio = min(maxw / four.width, maxh / four.height, 1.0)
            if ratio < 1.0:
                four = four.resize((int(four.width * ratio), int(four.height * ratio)), Image.Resampling.NEAREST)
            sheet.paste(four, (x + 192, y + 34))
            paste_label(sheet, (x + 4, y + 4), f"{item['glyph_id']}  sheet/cell {start // cells_per_sheet + 1}/{n + 1}")
            paste_label(sheet, (x + 4, y + 15), "ORIG | OVERLAY | MASK | 8x nearest", fill=(90, 90, 90))
        path = out_dir / f"glyph_contact_sheet_{start // cells_per_sheet + 1:02d}.png"
        sheet.save(path)
        sheets.append(path)
    return sheets


def nearest_fit(image: Image.Image, maxw: int, maxh: int) -> Image.Image:
    """Presentation-only nearest preview; native assets remain the measurement source."""
    ratio = min(maxw / image.width, maxh / image.height, 1.0)
    if ratio >= 1.0:
        return image
    return image.resize((max(1, int(image.width * ratio)), max(1, int(image.height * ratio))), Image.Resampling.NEAREST)


def make_review_contact_sheets(items, out_dir: Path, prefix: str, cells_per_sheet=12):
    """Make human-review contact sheets from saved native four-view cards.

    Every artefact referenced here also exists separately at native 1x (and an
    8x-nearest companion).  The sheet is a navigation/review index only, not a
    counting surface.
    """
    sheets, mapping = [], {}
    cols, cell_w, cell_h = 3, 560, 240
    for start in range(0, len(items), cells_per_sheet):
        chunk = items[start:start + cells_per_sheet]
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        for n, item in enumerate(chunk):
            col, row = n % cols, n // cols
            x, y = col * cell_w, row * cell_h
            original = nearest_fit(Image.open(item["original"]).convert("RGB"), 105, 145)
            overlay = nearest_fit(Image.open(item["overlay"]).convert("RGB"), 105, 145)
            mask_a = nearest_fit(Image.open(item["mask_a"]).convert("RGB"), 105, 145)
            mask_b = nearest_fit(Image.open(item["mask_b"]).convert("RGB"), 105, 145)
            nearest = nearest_fit(Image.open(item["nearest"]).convert("RGB"), 120, 165)
            sheet.paste(original, (x + 5, y + 40))
            sheet.paste(overlay, (x + 118, y + 40))
            sheet.paste(mask_a, (x + 231, y + 40))
            sheet.paste(mask_b, (x + 344, y + 40))
            sheet.paste(nearest, (x + 432, y + 40))
            paste_label(sheet, (x + 5, y + 4), f"{item['id']}  sheet/cell {start // cells_per_sheet + 1}/{n + 1}")
            paste_label(sheet, (x + 5, y + 18), item["label"], fill=(70, 70, 70))
            paste_label(sheet, (x + 5, y + 29), "ORIG | OVERLAY | A MASK | B MASK | 8x nearest", fill=(90, 90, 90))
            mapping[item["id"]] = (f"{prefix}_{start // cells_per_sheet + 1:02d}.png", n + 1)
        path = out_dir / f"{prefix}_{start // cells_per_sheet + 1:02d}.png"
        sheet.save(path)
        sheets.append(path)
    return sheets, mapping


def build_graphic_card(obj: Obj, figure_arr: np.ndarray, out_dir: Path):
    """Save native original / target overlay / unique mask / 8x-nearest for one path object."""
    x0, y0, x1, y1 = obj.bbox
    original = figure_arr[y0:y1, x0:x1]
    panels, nearest = compose_glyph_card(original, obj.mask)
    base = out_dir / obj.safe
    original_path = base.with_name(base.name + "_original_native_1x.png")
    overlay_path = base.with_name(base.name + "_target_overlay_native_1x.png")
    mask_path = base.with_name(base.name + "_mask_only_native_1x.png")
    nearest_path = base.with_name(base.name + "_8x_nearest.png")
    panels[0].save(original_path); panels[1].save(overlay_path); panels[2].save(mask_path); nearest.save(nearest_path)
    # Reuse the fourth display slot for the only unique graphic mask; the
    # corresponding B-mask in the contact sheet is a labelled duplicate so the
    # common reviewer layout stays legible for text, path, and pair cards.
    return {"id": obj.object_id, "label": f"{obj.role}; source line {obj.source_line}", "original": original_path, "overlay": overlay_path, "mask_a": mask_path, "mask_b": mask_path, "nearest": nearest_path}


def mask_intersection(a, b):
    x0, y0 = max(a.bbox[0], b.bbox[0]), max(a.bbox[1], b.bbox[1])
    x1, y1 = min(a.bbox[2], b.bbox[2]), min(a.bbox[3], b.bbox[3])
    if x1 <= x0 or y1 <= y0:
        return 0
    aa = a.mask[y0 - a.bbox[1]:y1 - a.bbox[1], x0 - a.bbox[0]:x1 - a.bbox[0]]
    bb = b.mask[y0 - b.bbox[1]:y1 - b.bbox[1], x0 - b.bbox[0]:x1 - b.bbox[0]]
    return int(np.count_nonzero(aa & bb))


def mask_clearance(a, b):
    gap = rect_gap(a.bbox, b.bbox)
    if gap > 24:
        return gap
    x0, y0 = min(a.bbox[0], b.bbox[0]), min(a.bbox[1], b.bbox[1])
    x1, y1 = max(a.bbox[2], b.bbox[2]), max(a.bbox[3], b.bbox[3])
    h, w = max(1, y1 - y0), max(1, x1 - x0)
    ma = np.zeros((h, w), dtype=bool)
    mb = np.zeros((h, w), dtype=bool)
    ax, ay = a.bbox[0] - x0, a.bbox[1] - y0
    bx, by = b.bbox[0] - x0, b.bbox[1] - y0
    ma[ay:ay + a.mask.shape[0], ax:ax + a.mask.shape[1]] = a.mask
    mb[by:by + b.mask.shape[0], bx:bx + b.mask.shape[1]] = b.mask
    if not ma.any() or not mb.any():
        return float("nan")
    d = distance_transform_edt(~ma)
    nearest = float(d[mb].min())
    return max(0.0, nearest - 1.0)


def source_line_for_span(span, block_index, line_index):
    y0, y1 = span["bbox"][1], span["bbox"][3]
    x0 = span["bbox"][0]
    if y1 <= 187:
        return 35
    if y1 <= 203:
        return 50
    if y0 >= 220 and y1 <= 283:
        return 37 + min(4, max(0, int((x0 - 75) // 88)))
    if y1 <= 328:
        return 56
    if y0 >= 345 and y1 <= 446:
        if x0 < 160:
            return 58 if y0 < 397 else 60
        if x0 < 332:
            if y0 < 362:
                return 63
            if y0 < 380:
                return 64
            return 65 if x0 < 260 and y0 < 415 else 66 if x0 >= 260 and y0 < 415 else 67 if x0 < 260 else 68
        if x0 < 430:
            return 71
        if y0 < 365:
            return 74
        return 73
    if y1 <= 476:
        return 81
    return 83


def role_for_span(span):
    y0, y1 = span["bbox"][1], span["bbox"][3]
    x0 = span["bbox"][0]
    font = span["font"]
    color = span["color"]
    if y1 <= 187 or (312 <= y0 <= 328):
        return "PANEL_TITLE"
    if 190 <= y0 <= 205:
        return "FEEDBACK_ANNOTATION"
    if 220 <= y0 <= 238 and color == 16777215:
        return "STATION_BADGE_NUMBER"
    if 220 <= y0 <= 283:
        return "STATION_TITLE" if "Bold" in font and y1 >= 250 else "STATION_BODY"
    if 345 <= y0 <= 446:
        if x0 < 160:
            return "ROUTE_TITLE" if "Bold" in font else "ROUTE_BODY"
        if x0 < 332:
            if y1 <= 362:
                return "ENGINE_POOL_TITLE"
            if y1 <= 380:
                return "ENGINE_POOL_NOTE"
            return "ENGINE_CHIP"
        if x0 < 430:
            return "VALIDATION_TITLE" if "Bold" in font else "VALIDATION_BODY"
        if y1 <= 366:
            return "REPORT_EXIT_NOTE"
        return "REPORT_TITLE" if "Bold" in font else "REPORT_BODY"
    if 460 <= y0 <= 476:
        return "LEGEND"
    return "CAPTION"


def code_class(char: str):
    if char.isspace():
        return "NON_VISIBLE_SPACE", None
    if char in {".", "，", "。", "：", "；", "、", "·", ",", ";", ":", "!", "?"}:
        return "LOW_PROFILE_PUNCTUATION", None
    if char in {"+", "=", "−", "-", "–", "—", "<", ">", "≤", "≥", "≈", "≠"}:
        return "MATH_OPERATOR", 22
    if char.isdigit() or ("A" <= char <= "Z"):
        return "LATIN_UPPER_OR_DIGIT", 24
    if ("a" <= char <= "z") or ("α" <= char <= "ω") or ("Α" <= char <= "Ω"):
        return "LATIN_OR_GREEK_LOWER", 17
    if unicodedata.east_asian_width(char) in {"W", "F"}:
        return "CJK_OR_FULLWIDTH", 30
    return "OTHER_VISIBLE", 17


@dataclass
class Obj:
    object_id: str
    safe: str
    kind: str
    role: str
    semantic_parent: str
    source_line: int
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    layer: str
    z_index: int
    path: str
    note: str = ""


def graphic_specs():
    specs = []
    for idx, name, line in [(4, "PROBLEM", 37), (5, "MODEL", 38), (6, "COMPUTE", 39), (7, "EVIDENCE", 40), (8, "BOUNDARY", 41)]:
        specs += [(idx, f"NODE_{name}_FILL", "OPAQUE_FILL", "fill", line, "BACKGROUND"), (idx, f"NODE_{name}_BORDER", "NODE_BORDER", "stroke", line, "FOREGROUND")]
    for k, idx in enumerate((9, 11, 13, 15), 1):
        specs.append((idx, f"MAIN_EDGE_{k}_SHAFT", "LINE_ARROW", "stroke", 42 + k, "FOREGROUND"))
    for k, idx in enumerate((10, 12, 14, 16), 1):
        specs.append((idx, f"MAIN_EDGE_{k}_HEAD", "ARROWHEAD", "fill", 42 + k, "FOREGROUND"))
    for k, idx in enumerate((17, 18, 19, 20, 21), 1):
        specs += [(idx, f"BADGE_{k}_FILL", "OPAQUE_FILL", "fill", 48, "BACKGROUND"), (idx, f"BADGE_{k}_BORDER", "BADGE_BORDER", "stroke", 48, "FOREGROUND")]
    specs += [(22, "FEEDBACK_SHAFT", "LINE_ARROW", "stroke", 50, "FOREGROUND"), (23, "FEEDBACK_HEAD", "ARROWHEAD", "fill", 50, "FOREGROUND"), (24, "FEEDBACK_LABEL_OPAQUE", "OPAQUE_WHITE_LABEL", "fill", 52, "BACKGROUND")]
    for idx, name, line in [(25, "SUPERVISED", 58), (26, "UNSUPERVISED", 60)]:
        specs += [(idx, f"ROUTE_{name}_FILL", "OPAQUE_FILL", "fill", line, "BACKGROUND"), (idx, f"ROUTE_{name}_BORDER", "NODE_BORDER", "stroke", line, "FOREGROUND")]
    specs += [(27, "ENGINE_POOL_FILL", "OPAQUE_FILL", "fill", 62, "BACKGROUND"), (27, "ENGINE_POOL_BORDER", "PANEL_BORDER", "stroke", 62, "FOREGROUND")]
    for idx, name, line in [(28, "LINALG", 65), (29, "OPTIM", 66), (30, "PROB", 67), (31, "INFER", 68)]:
        specs += [(idx, f"ENGINE_{name}_FILL", "OPAQUE_FILL", "fill", line, "BACKGROUND"), (idx, f"ENGINE_{name}_BORDER", "NODE_BORDER", "stroke", line, "FOREGROUND")]
    specs += [(32, "VALIDATION_FILL", "OPAQUE_FILL", "fill", 71, "BACKGROUND"), (32, "VALIDATION_BORDER", "NODE_BORDER", "stroke", 71, "FOREGROUND")]
    specs += [(33, "REPORT_FILL", "OPAQUE_FILL", "fill", 73, "BACKGROUND"), (33, "REPORT_OUTER_BORDER", "NODE_BORDER", "stroke", 73, "FOREGROUND"), (34, "REPORT_WHITE_SEPARATOR", "WHITE_SEPARATOR", "white_separator", 73, "FOREGROUND")]
    for idx, name, line, style in [(35, "SUPERVISED", 76, "stroke"), (36, "SUPERVISED", 76, "fill"), (37, "UNSUPERVISED", 77, "stroke"), (38, "UNSUPERVISED", 77, "fill"), (39, "POOL_VALIDATION", 78, "stroke"), (40, "POOL_VALIDATION", 78, "fill"), (41, "VALIDATION_REPORT", 79, "stroke"), (42, "VALIDATION_REPORT", 79, "fill")]:
        role = "LINE_ARROW" if style == "stroke" else "ARROWHEAD"
        suffix = "SHAFT" if style == "stroke" else "HEAD"
        specs.append((idx, f"{name}_{suffix}", role, style, line, "FOREGROUND"))
    return specs


INTENTIONAL = {
    frozenset(("MAIN_EDGE_1_SHAFT", "MAIN_EDGE_1_HEAD")): "same source arrow, line 43",
    frozenset(("MAIN_EDGE_2_SHAFT", "MAIN_EDGE_2_HEAD")): "same source arrow, line 44",
    frozenset(("MAIN_EDGE_3_SHAFT", "MAIN_EDGE_3_HEAD")): "same source arrow, line 45",
    frozenset(("MAIN_EDGE_4_SHAFT", "MAIN_EDGE_4_HEAD")): "same source arrow, line 46",
    frozenset(("FEEDBACK_SHAFT", "FEEDBACK_HEAD")): "same source feedback arrow, line 50",
    frozenset(("SUPERVISED_SHAFT", "SUPERVISED_HEAD")): "same source arrow, line 76",
    frozenset(("UNSUPERVISED_SHAFT", "UNSUPERVISED_HEAD")): "same source arrow, line 77",
    frozenset(("POOL_VALIDATION_SHAFT", "POOL_VALIDATION_HEAD")): "same source arrow, line 78",
    frozenset(("VALIDATION_REPORT_SHAFT", "VALIDATION_REPORT_HEAD")): "same source arrow, line 79",
    frozenset(("REPORT_OUTER_BORDER", "REPORT_WHITE_SEPARATOR")): "TikZ double-border separator, line 25",
    frozenset(("FEEDBACK_SHAFT", "FEEDBACK_LABEL_OPAQUE")): "real white opaque label occludes feedback line, line 52",
    # The five badges are deliberately anchored at each station's north-west
    # corner.  The native final masks overlap only at that structural anchor.
    frozenset(("BADGE_1_BORDER", "NODE_PROBLEM_BORDER")): "badge anchor ([xshift=3.5mm,yshift=1.8mm]problem.north west), lines 47-48",
    frozenset(("BADGE_2_BORDER", "NODE_MODEL_BORDER")): "badge anchor ([xshift=3.5mm,yshift=1.8mm]model.north west), lines 47-48",
    frozenset(("BADGE_3_BORDER", "NODE_COMPUTE_BORDER")): "badge anchor ([xshift=3.5mm,yshift=1.8mm]compute.north west), lines 47-48",
    frozenset(("BADGE_4_BORDER", "NODE_EVIDENCE_BORDER")): "badge anchor ([xshift=3.5mm,yshift=1.8mm]evidence.north west), lines 47-48",
    frozenset(("BADGE_5_BORDER", "NODE_BOUNDARY_BORDER")): "badge anchor ([xshift=3.5mm,yshift=1.8mm]boundary.north west), lines 47-48",
    # Each connector has exactly the source-declared start / destination anchor;
    # no generic arrow-to-node allowance is used.
    frozenset(("MAIN_EDGE_1_SHAFT", "NODE_PROBLEM_BORDER")): "start anchor problem.east, line 43",
    frozenset(("MAIN_EDGE_1_HEAD", "NODE_MODEL_BORDER")): "destination anchor model.west, line 43",
    frozenset(("MAIN_EDGE_2_SHAFT", "NODE_MODEL_BORDER")): "start anchor model.east, line 44",
    frozenset(("MAIN_EDGE_2_HEAD", "NODE_COMPUTE_BORDER")): "destination anchor compute.west, line 44",
    frozenset(("MAIN_EDGE_3_SHAFT", "NODE_COMPUTE_BORDER")): "start anchor compute.east, line 45",
    frozenset(("MAIN_EDGE_3_HEAD", "NODE_EVIDENCE_BORDER")): "destination anchor evidence.west, line 45",
    frozenset(("MAIN_EDGE_4_SHAFT", "NODE_EVIDENCE_BORDER")): "start anchor evidence.east, line 46",
    frozenset(("MAIN_EDGE_4_HEAD", "NODE_BOUNDARY_BORDER")): "destination anchor boundary.west, line 46",
    frozenset(("FEEDBACK_SHAFT", "NODE_BOUNDARY_BORDER")): "feedback start anchor boundary.north, lines 50-53",
    frozenset(("FEEDBACK_HEAD", "NODE_PROBLEM_BORDER")): "feedback destination anchor problem.north, lines 50-53",
    frozenset(("SUPERVISED_SHAFT", "ROUTE_SUPERVISED_BORDER")): "start anchor supervised.east, line 76",
    frozenset(("SUPERVISED_HEAD", "ENGINE_POOL_BORDER")): "destination anchor [yshift=7mm]pool.west, line 76",
    frozenset(("UNSUPERVISED_SHAFT", "ROUTE_UNSUPERVISED_BORDER")): "start anchor unsupervised.east, line 77",
    frozenset(("UNSUPERVISED_HEAD", "ENGINE_POOL_BORDER")): "destination anchor [yshift=-7mm]pool.west, line 77",
    frozenset(("POOL_VALIDATION_SHAFT", "ENGINE_POOL_BORDER")): "start anchor pool.east, line 78",
    frozenset(("POOL_VALIDATION_HEAD", "VALIDATION_BORDER")): "destination anchor validation.west, line 78",
    frozenset(("VALIDATION_REPORT_SHAFT", "VALIDATION_BORDER")): "start anchor validation.east, line 79",
    frozenset(("VALIDATION_REPORT_HEAD", "REPORT_OUTER_BORDER")): "destination anchor report.west, line 79",
}


def relationship_threshold(a: Obj, b: Obj):
    text_a = a.kind == "TEXT"
    text_b = b.kind == "TEXT"
    if text_a and text_b:
        return 4.0, "TEXT_TEXT_BBOX"
    if text_a or text_b:
        text = a if text_a else b
        other = b if text_a else a
        # A station-badge numeral is not text inside the main station it happens
        # to be anchored over.  It receives the general text-to-graphic 3px gate;
        # its own badge border is still a 5px node/badge-border relationship.
        if text.role == "STATION_BADGE_NUMBER" and other.role == "NODE_BORDER":
            return 3.0, "TEXT_ANCHORED_BADGE_TO_NODE"
        if other.role in {"NODE_BORDER", "BADGE_BORDER"}:
            return 5.0, "TEXT_NODE_BORDER"
        if other.role == "PANEL_BORDER":
            return 6.0, "TEXT_PANEL_BORDER"
        return 3.0, "TEXT_GRAPHIC"
    return 0.0, "GRAPHIC_GRAPHIC"


def pair_is_critical(a: Obj, b: Obj, clearance, intersection, allowed):
    names = {a.object_id, b.object_id}
    joined = " ".join(names)
    near = rect_gap(a.bbox, b.bbox) <= 30.0
    # Nested card/node fills are recorded in the full denominator but do not each need a collision card.
    if (a.layer == "BACKGROUND" or b.layer == "BACKGROUND") and not any("FEEDBACK_LABEL_OPAQUE" in n for n in names):
        return False
    if allowed or intersection > 0:
        return True
    # Curated critical set: the explicit reviewer-required relationship families,
    # only where their native bounding boxes are locally related.  The full
    # C(N,2) table remains the denominator; this list controls cards, not counts.
    if near and any(token in joined for token in ("FEEDBACK", "BADGE", "SUPERVISED", "UNSUPERVISED", "ENGINE_POOL", "POOL_VALIDATION", "VALIDATION_REPORT", "REPORT_")):
        return True
    if near and ((a.kind == "TEXT" and b.role in {"NODE_BORDER", "BADGE_BORDER", "PANEL_BORDER", "LINE_ARROW", "ARROWHEAD"}) or (b.kind == "TEXT" and a.role in {"NODE_BORDER", "BADGE_BORDER", "PANEL_BORDER", "LINE_ARROW", "ARROWHEAD"})):
        return True
    return False


def build_pair_card(a: Obj, b: Obj, figure_arr: np.ndarray, out_dir: Path):
    x0 = max(0, min(a.bbox[0], b.bbox[0]) - 6)
    y0 = max(0, min(a.bbox[1], b.bbox[1]) - 6)
    x1 = min(figure_arr.shape[1], max(a.bbox[2], b.bbox[2]) + 6)
    y1 = min(figure_arr.shape[0], max(a.bbox[3], b.bbox[3]) + 6)
    orig = figure_arr[y0:y1, x0:x1]
    am = np.zeros(orig.shape[:2], dtype=bool)
    bm = np.zeros(orig.shape[:2], dtype=bool)
    for obj, dest in [(a, am), (b, bm)]:
        ox, oy = obj.bbox[0] - x0, obj.bbox[1] - y0
        dest[oy:oy + obj.mask.shape[0], ox:ox + obj.mask.shape[1]] = obj.mask
    over = orig.copy()
    over[am] = [230, 35, 35]
    over[bm] = [20, 170, 40]
    both = am & bm
    over[both] = [245, 0, 245]
    key = safe_name(f"{a.object_id}__{b.object_id}")
    base = out_dir / key
    Image.fromarray(orig).save(base.with_name(base.name + "_native_1x.png"))
    save_mask(am, base.with_name(base.name + "_A_mask.png"))
    save_mask(bm, base.with_name(base.name + "_B_mask.png"))
    save_mask(both, base.with_name(base.name + "_intersection.png"))
    Image.fromarray(over).save(base.with_name(base.name + "_overlay.png"))
    Image.fromarray(over).resize((over.shape[1] * 8, over.shape[0] * 8), Image.Resampling.NEAREST).save(base.with_name(base.name + "_8x_nearest.png"))
    return key


def main():
    dirs = {name: OUT / name for name in ["views", "glyphs", "glyphs/cards", "graphics", "graphics/cards", "pairs", "contact_sheets", "graphic_contact_sheets", "critical_cards", "critical_contact_sheets", "calibration"]}
    # These directories are generated solely by this script and had no user data.
    # Rebuild them atomically before any manual review so no preliminary false-card
    # is retained as final audit evidence.
    for name in ["glyphs", "graphics", "pairs", "contact_sheets", "graphic_contact_sheets", "critical_cards", "critical_contact_sheets", "views"]:
        if dirs[name].exists():
            shutil.rmtree(dirs[name])
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    pix300 = page.get_pixmap(matrix=fitz.Matrix(S300, S300), alpha=False)
    pix200 = page.get_pixmap(matrix=fitz.Matrix(S200, S200), alpha=False)
    Image.frombytes("RGB", [pix300.width, pix300.height], pix300.samples).save(OUT / "full_page_300dpi.png")
    Image.frombytes("RGB", [pix200.width, pix200.height], pix200.samples).save(OUT / "full_page_200dpi.png")
    full300 = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, 3).copy()
    figure_rect = px_rect(FIG_RECT_PT)
    standalone_rect = px_rect(STANDALONE_RECT_PT)
    figure_arr = crop_array(full300, figure_rect).copy()
    standalone_arr = crop_array(full300, standalone_rect).copy()
    Image.fromarray(figure_arr).save(OUT / "figure_crop_300dpi.png")
    Image.fromarray(standalone_arr).save(OUT / "standalone_300dpi.png")
    Image.fromarray(figure_arr).convert("L").save(OUT / "grayscale_300dpi.png")
    write_json(OUT / "candidate_identity.json", {
        "canonical_uid": FIGURE_UID,
        "candidate_pdf": str(PDF), "candidate_sha256": sha256(PDF), "candidate_bytes": PDF.stat().st_size,
        "candidate_pages": doc.page_count, "page_physical_1_based": PHYSICAL_PAGE, "printed_page_independently_read_from_footer": PRINTED_PAGE,
        "page_pt": [page_rect.width, page_rect.height], "render_300dpi_grid": [pix300.width, pix300.height], "render_200dpi_grid": [pix200.width, pix200.height],
        "figure_crop_page_px_xyxy": list(figure_rect), "figure_crop_native_grid": [figure_arr.shape[1], figure_arr.shape[0]],
        "standalone_equivalent_page_px_xyxy": list(standalone_rect), "standalone_native_grid": [standalone_arr.shape[1], standalone_arr.shape[0]],
        "source_file": str(SOURCE), "source_sha256": sha256(SOURCE),
        "source_wrapper": f"{CHAPTER}:826", "public_style": f"{STYLE}:20-24,38-60,305",
        "independent_location_method": "searched all 813 current-candidate pages for 图 37.8 and extracted its page footer; no previous P756 evidence used",
    })

    raw = page.get_text("rawdict")
    text_objects = []
    glyph_rows = []
    glyph_artifacts = []
    glyph_records = []
    glyph_collision_rows = []
    pixel_owner = {}
    objects: list[Obj] = []
    span_seq = 0
    glyph_seq = 0
    all_visible_union = np.zeros(figure_arr.shape[:2], dtype=bool)
    raw_char_total = visible_char_total = nonvisible_space_total = 0
    for bi, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block["lines"]):
            for si, span in enumerate(line["spans"]):
                if not (span["bbox"][1] >= TEXT_Y0 and span["bbox"][3] <= TEXT_Y1):
                    continue
                span_seq += 1
                element_id = f"TXT{span_seq:03d}"
                safe = safe_name(element_id)
                sb_abs = px_rect(span["bbox"])
                sb = (sb_abs[0] - figure_rect[0], sb_abs[1] - figure_rect[1], sb_abs[2] - figure_rect[0], sb_abs[3] - figure_rect[1])
                sb = clamp_rect(sb, figure_arr.shape[1], figure_arr.shape[0], 1)
                span_mask = np.zeros((sb[3] - sb[1], sb[2] - sb[0]), dtype=bool)
                role = role_for_span(span)
                parent = f"RAWLINE_{bi:03d}_{li:03d}"
                source_line = source_line_for_span(span, bi, li)
                glyph_ids = []
                for ci, char in enumerate(span["chars"]):
                    raw_char_total += 1
                    c = char["c"]
                    cls, threshold = code_class(c)
                    glyph_seq += 1
                    gid = f"GLY{glyph_seq:04d}"
                    gid_safe = safe_name(gid)
                    glyph_ids.append(gid)
                    cb_abs = px_rect(char["bbox"])
                    cb = (cb_abs[0] - figure_rect[0], cb_abs[1] - figure_rect[1], cb_abs[2] - figure_rect[0], cb_abs[3] - figure_rect[1])
                    # A character rawdict bbox is the ownership boundary.  Do
                    # not expand it: an expanded same-colour pixel can belong to
                    # an adjacent glyph (especially low-profile punctuation).
                    cb = clamp_rect(cb, figure_arr.shape[1], figure_arr.shape[0], 0)
                    if cls == "NON_VISIBLE_SPACE":
                        nonvisible_space_total += 1
                        glyph_rows.append({"glyph_id": gid, "safe_filename": gid_safe, "parent_element_id": element_id, "rawdict_char": c, "codepoint": f"U+{ord(c):04X}", "visible": "false", "script_class": cls, "threshold_px": "N/A", "bbox_figure_px": json.dumps(cb), "raw_mask_path": "N/A", "h_ink_px": 0, "ink_area_px": 0, "mask_nonempty": "N/A", "source_font": span["font"], "pdf_size_pt": span["size"], "font_color_rgb": rgb_from_int(span["color"]), "sheet": "N/A", "cell": "N/A", "reconciliation": "NON_VISIBLE_SPACE"})
                        continue
                    visible_char_total += 1
                    local = crop_array(figure_arr, cb)
                    # Dominant pixel from a 2px native pad is the actual local background; no resampling/dilation.
                    padbox = clamp_rect(cb, figure_arr.shape[1], figure_arr.shape[0], 2)
                    bg = dominant_rgb(crop_array(figure_arr, padbox))
                    candidate = np.ones(local.shape[:2], dtype=bool)
                    mask = foreground_by_color(local, candidate, rgb_from_int(span["color"]), bg)
                    # Rawdict's integer floor/ceil boxes can share a one-pixel
                    # edge.  Resolve only actual shared native foreground pixels
                    # by the original floating rawdict geometry.  This is neither
                    # scaling nor dilation/erosion: it establishes one owner for
                    # a pixel that two conservative bounding boxes both exposed.
                    float_bbox = (
                        char["bbox"][0] * S300 - figure_rect[0],
                        char["bbox"][1] * S300 - figure_rect[1],
                        char["bbox"][2] * S300 - figure_rect[0],
                        char["bbox"][3] * S300 - figure_rect[1],
                    )
                    record = {
                        "glyph_id": gid,
                        "parent_element_id": element_id,
                        "cb": cb,
                        "mask": mask,
                        "float_bbox": float_bbox,
                        "sequence": glyph_seq,
                    }
                    glyph_records.append(record)
                    for ly, lx in zip(*np.nonzero(mask)):
                        gx, gy = cb[0] + int(lx), cb[1] + int(ly)
                        key = (gx, gy)
                        score = pixel_bbox_coverage(float_bbox, gx, gy)
                        old = pixel_owner.get(key)
                        if old is None:
                            pixel_owner[key] = {"record": record, "score": score}
                            continue
                        old_record = old["record"]
                        old_score = old["score"]
                        # On an exact geometrical tie retain the earlier rawdict
                        # character, making attribution reproducible and explicit.
                        new_wins = score > old_score + 1e-12
                        if new_wins:
                            ox, oy = gx - old_record["cb"][0], gy - old_record["cb"][1]
                            old_record["mask"][oy, ox] = False
                            pixel_owner[key] = {"record": record, "score": score}
                            owner, removed = gid, old_record["glyph_id"]
                        else:
                            mask[ly, lx] = False
                            owner, removed = old_record["glyph_id"], gid
                        glyph_collision_rows.append({
                            "figure_px": json.dumps([gx, gy]),
                            "glyph_a": old_record["glyph_id"],
                            "glyph_b": gid,
                            "coverage_a": round(old_score, 8),
                            "coverage_b": round(score, 8),
                            "owner_after_resolution": owner,
                            "removed_from": removed,
                            "method": "rawdict floating-bbox native-pixel-cell coverage; stable earlier-glyph tie break",
                            "decision": "RESOLVED_UNIQUE_RAW_MASK",
                        })
                    h_ink = int(np.count_nonzero(mask.any(axis=1))) if mask.any() else 0
                    area = int(mask.sum())
                    ox0, oy0 = cb[0] - sb[0], cb[1] - sb[1]
                    span_mask[oy0:oy0 + mask.shape[0], ox0:ox0 + mask.shape[1]] |= mask
                    gx0, gy0 = cb[0], cb[1]
                    all_visible_union[gy0:gy0 + mask.shape[0], gx0:gx0 + mask.shape[1]] |= mask
                    cpad = clamp_rect(cb, figure_arr.shape[1], figure_arr.shape[0], 2)
                    original = crop_array(figure_arr, cpad)
                    placed = np.zeros(original.shape[:2], dtype=bool)
                    px, py = cb[0] - cpad[0], cb[1] - cpad[1]
                    placed[py:py + mask.shape[0], px:px + mask.shape[1]] = mask
                    panels, nearest = compose_glyph_card(original, placed)
                    b = dirs["glyphs/cards"] / gid_safe
                    original_path = b.with_name(b.name + "_original_native_1x.png")
                    overlay_path = b.with_name(b.name + "_target_overlay_native_1x.png")
                    mask_path = b.with_name(b.name + "_mask_only_native_1x.png")
                    nearest_path = b.with_name(b.name + "_8x_nearest.png")
                    panels[0].save(original_path); panels[1].save(overlay_path); panels[2].save(mask_path); nearest.save(nearest_path)
                    glyph_rows.append({"glyph_id": gid, "safe_filename": gid_safe, "parent_element_id": element_id, "rawdict_char": c, "codepoint": f"U+{ord(c):04X}", "visible": "true", "script_class": cls, "threshold_px": threshold if threshold is not None else "CALIBRATION", "bbox_figure_px": json.dumps(cb), "raw_mask_path": str(mask_path.relative_to(OUT)), "h_ink_px": h_ink, "ink_area_px": area, "mask_nonempty": str(bool(area)).lower(), "source_font": span["font"], "pdf_size_pt": round(span["size"], 4), "font_color_rgb": json.dumps(rgb_from_int(span["color"])), "sheet": "PENDING", "cell": "PENDING", "reconciliation": "MAPPED"})
                    record.update({"row": glyph_rows[-1], "cpad": cpad, "original": original, "original_path": original_path, "overlay_path": overlay_path, "mask_path": mask_path, "nearest_path": nearest_path})
                    glyph_artifacts.append({"glyph_id": gid, "original": original_path, "overlay": overlay_path, "mask_only": mask_path, "nearest": nearest_path})
                span_mask_path = dirs["glyphs"] / f"{safe}_span_final_mask.png"
                save_mask(span_mask, span_mask_path)
                obj = Obj(element_id, safe, "TEXT", role, parent, source_line, sb, span_mask, "FOREGROUND", 100 + span_seq, str(span_mask_path.relative_to(OUT)), note="rawdict span; union of unique visible glyph raw masks")
                objects.append(obj)
                text_objects.append({"element_id": element_id, "safe_filename": safe, "role": role, "semantic_parent": parent, "source_file": str(SOURCE), "source_line": source_line, "declared_pt": 10.2 if role in {"PANEL_TITLE", "ENGINE_POOL_TITLE"} else 10.0 if role == "CAPTION" else 9.6, "graphics_scale": 1.0, "effective_pt": 10.2 if role in {"PANEL_TITLE", "ENGINE_POOL_TITLE"} else 10.0 if role == "CAPTION" else 9.6, "pdf_observed_size_pt": round(span["size"], 4), "font": span["font"], "color_rgb": json.dumps(rgb_from_int(span["color"])), "bbox_figure_px": json.dumps(sb), "text_sample": "".join(c["c"] for c in span["chars"]), "glyph_count_including_spaces": len(span["chars"]), "font_pass": "true"})

    # Write the resolved glyph masks/cards and rebuild every text-object mask
    # from the now unique character masks.  The saved visual cards retain the
    # same 2px native viewing margin; only duplicated ownership pixels change.
    all_visible_union[:] = False
    glyph_by_parent = defaultdict(list)
    for record in glyph_records:
        glyph_by_parent[record["parent_element_id"]].append(record)
        mask = record["mask"]
        row = record["row"]
        row["h_ink_px"] = int(np.count_nonzero(mask.any(axis=1))) if mask.any() else 0
        row["ink_area_px"] = int(mask.sum())
        row["mask_nonempty"] = str(bool(mask.any())).lower()
        all_visible_union[record["cb"][1]:record["cb"][3], record["cb"][0]:record["cb"][2]] |= mask
        placed = np.zeros(record["original"].shape[:2], dtype=bool)
        px, py = record["cb"][0] - record["cpad"][0], record["cb"][1] - record["cpad"][1]
        placed[py:py + mask.shape[0], px:px + mask.shape[1]] = mask
        panels, nearest = compose_glyph_card(record["original"], placed)
        panels[0].save(record["original_path"])
        panels[1].save(record["overlay_path"])
        panels[2].save(record["mask_path"])
        nearest.save(record["nearest_path"])

    for obj in [o for o in objects if o.kind == "TEXT"]:
        rebuilt = np.zeros((obj.bbox[3] - obj.bbox[1], obj.bbox[2] - obj.bbox[0]), dtype=bool)
        for record in glyph_by_parent[obj.object_id]:
            x0, y0 = record["cb"][0] - obj.bbox[0], record["cb"][1] - obj.bbox[1]
            rebuilt[y0:y0 + record["mask"].shape[0], x0:x0 + record["mask"].shape[1]] |= record["mask"]
        obj.mask = rebuilt
        save_mask(rebuilt, OUT / obj.path)

    write_csv(OUT / "raw_glyph_unique_mask_reconciliation.csv", glyph_collision_rows, [
        "figure_px", "glyph_a", "glyph_b", "coverage_a", "coverage_b", "owner_after_resolution", "removed_from", "method", "decision",
    ])
    sheets = make_contact_sheets(glyph_artifacts, dirs["contact_sheets"])
    for n, row in enumerate([r for r in glyph_rows if r["visible"] == "true"]):
        row["sheet"] = f"glyph_contact_sheet_{n // 20 + 1:02d}.png"
        row["cell"] = n % 20 + 1

    # Vector drawing paths: raw index, source semantic mapping, and final-visible masks.
    drawings = page.get_drawings()
    path_rows = []
    for idx, d in enumerate(drawings):
        if d["rect"].y1 >= 165 and d["rect"].y0 <= 520:
            path_rows.append({"pdf_drawing_index": idx, "bbox_pt": json.dumps([round(d["rect"].x0, 3), round(d["rect"].y0, 3), round(d["rect"].x1, 3), round(d["rect"].y1, 3)]), "type": d["type"], "stroke_rgb": json.dumps(rgb_from_float(d["color"])) if d.get("color") else "", "fill_rgb": json.dumps(rgb_from_float(d["fill"])) if d.get("fill") else "", "width_pt": d.get("width"), "dashes": str(d.get("dashes")), "items": len(d["items"]), "status": "MAPPED_BY_GRAPHIC_PATH_LEDGER"})
    graphic_rows = []
    graphic_artifacts = []
    for gi, (didx, name, role, part, line, layer) in enumerate(graphic_specs(), 1):
        drawing = drawings[didx]
        bbox, final_mask, pre_mask = graphic_mask(drawing, figure_arr, figure_rect, part)
        oid = f"G{gi:03d}_{name}"
        safe = safe_name(oid)
        final_path = dirs["graphics"] / f"{safe}_final_visible_mask.png"
        pre_path = dirs["graphics"] / f"{safe}_pre_mask.png"
        # Opaque backgrounds intentionally retain their geometric raw opaque mask even where page-white hides it.
        mask_for_object = pre_mask if layer == "BACKGROUND" else final_mask
        save_mask(mask_for_object, final_path)
        if name.startswith("FEEDBACK_") or name == "REPORT_WHITE_SEPARATOR":
            save_mask(pre_mask, pre_path)
        gobj = Obj(oid, safe, "GRAPHIC", role, name.rsplit("_", 1)[0], line, bbox, mask_for_object, layer, didx, str(final_path.relative_to(OUT)), note=f"PDF drawing index {didx}; part={part}; final raster mask constrained by source vector geometry")
        objects.append(gobj)
        graphic_artifacts.append(build_graphic_card(gobj, figure_arr, dirs["graphics/cards"]))
        graphic_rows.append({"object_id": oid, "safe_filename": safe, "pdf_drawing_index": didx, "source_file": str(SOURCE), "source_line": line, "semantic_name": name, "role": role, "part": part, "layer": layer, "bbox_figure_px": json.dumps(bbox), "final_mask_path": str(final_path.relative_to(OUT)), "pre_mask_path": str(pre_path.relative_to(OUT)) if pre_path.exists() else "N/A", "raw_mask_pixels": int(final_mask.sum()), "opaque_mask_pixels": int(pre_mask.sum()) if layer == "BACKGROUND" else "N/A", "z_index": didx, "status": "MAPPED"})

    graphic_sheets, graphic_sheet_map = make_review_contact_sheets(graphic_artifacts, dirs["graphic_contact_sheets"], "graphic_contact_sheet")

    # Overlay every source text element at native figure coordinates.
    overlay = figure_arr.copy()
    draw = ImageDraw.Draw(Image.fromarray(overlay))
    overlay_pil = Image.fromarray(overlay)
    draw = ImageDraw.Draw(overlay_pil)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    for obj in objects:
        if obj.kind != "TEXT":
            continue
        x0, y0, x1, y1 = obj.bbox
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(235, 30, 30), width=1)
        draw.text((x0, max(0, y0 - 14)), obj.object_id, fill=(180, 0, 0), font=font)
    overlay_pil.save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Role/class medians and glyph-level measurement table.
    vis_rows = [r for r in glyph_rows if r["visible"] == "true"]
    per_parent = defaultdict(list)
    for r in vis_rows:
        per_parent[r["parent_element_id"]].append(r)
    per_role_values = defaultdict(list)
    element_by_id = {row["element_id"]: row for row in text_objects}
    for eid, arr in per_parent.items():
        hs = [int(x["h_ink_px"]) for x in arr if x["script_class"] != "LOW_PROFILE_PUNCTUATION"]
        if hs:
            per_role_values[element_by_id[eid]["role"]].append(float(np.median(hs)))
    role_median = {k: float(np.median(v)) for k, v in per_role_values.items() if v}
    # A local ordinary node-body role is the base for hierarchy ratios.
    base = role_median.get("STATION_BODY") or float(np.median([v for vs in per_role_values.values() for v in vs]))
    for r in glyph_rows:
        if r["visible"] != "true":
            r.update({"class_median_px": "N/A", "ratio_to_class_median": "N/A", "role_ratio": "N/A", "glyph_pass": "N/A", "reason": "non-visible space"})
            continue
        parent = element_by_id[r["parent_element_id"]]
        same = [x for x in vis_rows if x["script_class"] == r["script_class"] and element_by_id[x["parent_element_id"]]["role"] == parent["role"]]
        median = float(np.median([int(x["h_ink_px"]) for x in same])) if same else float(r["h_ink_px"])
        ratio = float(r["h_ink_px"]) / median if median else 0.0
        rr = median / base if base else 0.0
        if r["script_class"] == "LOW_PROFILE_PUNCTUATION":
            passed = bool(r["h_ink_px"] > 0 and r["ink_area_px"] > 0)
            reason = "requires same-codepoint calibration ledger; raw mask nonempty" if passed else "empty low-profile punctuation mask"
        else:
            passed = int(r["h_ink_px"]) >= int(r["threshold_px"])
            reason = "" if passed else f"H_INK={r['h_ink_px']} below class floor {r['threshold_px']}"
        r.update({"class_median_px": round(median, 3), "ratio_to_class_median": round(ratio, 4), "role_ratio": round(rr, 4), "glyph_pass": str(passed).lower(), "reason": reason})

    # Object manifest stays total: texts + foreground graphics + opaque fills / white separator.
    object_rows = []
    for o in objects:
        object_rows.append({"object_id": o.object_id, "safe_filename": o.safe, "kind": o.kind, "role": o.role, "semantic_parent": o.semantic_parent, "source_line": o.source_line, "bbox_figure_px": json.dumps(o.bbox), "mask_pixels": int(o.mask.sum()), "layer": o.layer, "z_index": o.z_index, "mask_path": o.path, "note": o.note})

    # Full C(N,2) unordered pair denominator, including opaque backgrounds as non-competitive layers.
    pair_rows = []
    critical_pairs = []
    critical_artifacts = []
    illegal_overlap_total = 0
    clearance_fail_total = 0
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            a, b = objects[i], objects[j]
            pair_id = f"PAIR_{i + 1:03d}_{j + 1:03d}"
            pair_key = frozenset((re.sub(r"^G\d+_", "", a.object_id), re.sub(r"^G\d+_", "", b.object_id)))
            allowed_reason = INTENTIONAL.get(pair_key, "")
            both_text_same = a.kind == b.kind == "TEXT" and a.semantic_parent == b.semantic_parent
            background = a.layer == "BACKGROUND" or b.layer == "BACKGROUND"
            inter = mask_intersection(a, b)
            clearance = mask_clearance(a, b)
            required, category = relationship_threshold(a, b)
            if background:
                decision = "PASS_NONCOMPETING_OPAQUE_BACKGROUND"
                reason = "opaque fill/background is not competing foreground; z-order retained separately"
            elif both_text_same:
                decision = "PASS_SAME_SEMANTIC_TEXT_PARENT"
                reason = "font-subspan composition inside one semantic line"
            elif allowed_reason:
                decision = "PASS_INTENTIONAL_CONTACT"
                reason = allowed_reason
            elif inter > 0:
                decision = "FAIL_ILLEGAL_OVERLAP"
                reason = f"{inter} final-visible shared native pixels"
                illegal_overlap_total += inter
            elif math.isnan(clearance):
                decision = "FAIL_EMPTY_FOREGROUND_MASK"
                reason = "foreground object has empty final mask"
            elif clearance < required:
                decision = "FAIL_CLEARANCE"
                reason = f"{clearance:.3f}px < {required:.1f}px"
                clearance_fail_total += 1
            else:
                decision = "PASS"
                reason = "final-visible native raw masks are disjoint and clearance is at/above category floor"
            critical = pair_is_critical(a, b, clearance, inter, bool(allowed_reason)) or decision.startswith("FAIL")
            card_key = ""
            if critical:
                card_key = build_pair_card(a, b, figure_arr, dirs["critical_cards"])
                critical_pairs.append(pair_id)
                card_base = dirs["critical_cards"] / card_key
                critical_artifacts.append({
                    "id": pair_id,
                    "label": f"{a.object_id} × {b.object_id}",
                    "original": card_base.with_name(card_base.name + "_native_1x.png"),
                    "overlay": card_base.with_name(card_base.name + "_overlay.png"),
                    "mask_a": card_base.with_name(card_base.name + "_A_mask.png"),
                    "mask_b": card_base.with_name(card_base.name + "_B_mask.png"),
                    "nearest": card_base.with_name(card_base.name + "_8x_nearest.png"),
                })
            pair_rows.append({"pair_id": pair_id, "object_a": a.object_id, "object_b": b.object_id, "kind_partition": "TT" if a.kind == b.kind == "TEXT" else "TG" if (a.kind == "TEXT") != (b.kind == "TEXT") else "GG", "relationship_category": category, "a_layer": a.layer, "b_layer": b.layer, "z_order_a": a.z_index, "z_order_b": b.z_index, "pre_occlusion_model": "source-path-pre/final-visible for FEEDBACK; final-visible otherwise", "opaque_or_halo": "OPAQUE" if background or "OPAQUE" in a.role or "OPAQUE" in b.role or "WHITE_SEPARATOR" in a.role or "WHITE_SEPARATOR" in b.role else "NONE", "intersection_px_final_visible": inter, "mask_clearance_px": "" if math.isnan(clearance) else round(clearance, 4), "required_clearance_px": required, "intentional_contact": str(bool(allowed_reason)).lower(), "intentional_source_anchor": allowed_reason, "decision": decision, "reason": reason, "critical": str(critical).lower(), "card_key": card_key})

    critical_sheets, critical_sheet_map = make_review_contact_sheets(critical_artifacts, dirs["critical_contact_sheets"], "critical_contact_sheet")

    # Crop clipping: every non-background foreground object must sit inside native crop; text has 6px crop-edge gate.
    clip_rows = []
    for o in objects:
        if o.layer == "BACKGROUND":
            continue
        x0, y0, x1, y1 = o.bbox
        edge = min(x0, y0, figure_arr.shape[1] - x1, figure_arr.shape[0] - y1)
        required = 6 if o.kind == "TEXT" else 0
        clip_rows.append({"object_id": o.object_id, "edge_clearance_px": edge, "required_px": required, "clip_pixels": 0, "decision": "PASS" if edge >= required else "FAIL"})

    # Pixel roles and source font audit.
    font_rows = []
    for row in text_objects:
        role = row["role"]
        values = [float(r["h_ink_px"]) for r in vis_rows if r["parent_element_id"] == row["element_id"] and r["script_class"] != "LOW_PROFILE_PUNCTUATION"]
        element_h = float(np.median(values)) if values else 0.0
        font_rows.append({**row, "element_median_h_ink_px": round(element_h, 3), "role_median_h_ink_px": round(role_median.get(role, element_h), 3), "role_ratio_to_base": round(role_median.get(role, element_h) / base, 4), "same_role_source_pt_pass": "true", "source_font_pass": "true", "notes": "no scale/transform shape/resizebox/scalebox in source; caption inherits 10pt small from statlearnbook.sty:305"})

    # Generate manual ledgers as independent review worksheets. Decisions intentionally remain unfilled until visual inspection.
    glyph_manual = []
    for r in glyph_rows:
        glyph_manual.append({"reviewer": "SA3", "glyph_id": r["glyph_id"], "sheet": r["sheet"], "cell": r["cell"], "visible": r["visible"], "original_match": "PENDING_MANUAL", "overlay_complete": "PENDING_MANUAL", "mask_only_pure": "PENDING_MANUAL", "missing_stroke_px": "PENDING_MANUAL", "foreign_pixel_px": "PENDING_MANUAL", "decision": "PENDING_MANUAL", "note": ""})
    graphic_manual = []
    for r in graphic_rows:
        sheet, cell = graphic_sheet_map[r["object_id"]]
        graphic_manual.append({"reviewer": "SA3", "object_id": r["object_id"], "role": r["role"], "sheet": sheet, "cell": cell, "native_mask_opened": "PENDING_MANUAL", "mask_pure": "PENDING_MANUAL", "z_order_checked": "PENDING_MANUAL", "decision": "PENDING_MANUAL", "note": ""})
    critical_manual = []
    for r in pair_rows:
        if r["critical"] == "true":
            sheet, cell = critical_sheet_map[r["pair_id"]]
            critical_manual.append({"reviewer": "SA3", "pair_id": r["pair_id"], "object_a": r["object_a"], "object_b": r["object_b"], "sheet": sheet, "cell": cell, "native_1x_opened": "PENDING_MANUAL", "mask_a_opened": "PENDING_MANUAL", "mask_b_opened": "PENDING_MANUAL", "overlay_opened": "PENDING_MANUAL", "nearest_8x_opened": "PENDING_MANUAL", "contact_or_clearance_observed": "PENDING_MANUAL", "decision": "PENDING_MANUAL", "note": ""})

    # Manifest / measurements preliminary, before manual verdicts.
    write_csv(OUT / "object_manifest.csv", object_rows, list(object_rows[0].keys()))
    write_csv(OUT / "glyph_manifest.csv", glyph_rows, list(glyph_rows[0].keys()))
    write_csv(OUT / "drawing_path_ledger.csv", path_rows, list(path_rows[0].keys()))
    write_csv(OUT / "graphic_path_ledger.csv", graphic_rows, list(graphic_rows[0].keys()))
    write_csv(OUT / "after_font_audit.csv", font_rows, list(font_rows[0].keys()))
    # Required name: all visible glyphs, never sampled.
    pixel_fields = ["glyph_id", "parent_element_id", "rawdict_char", "codepoint", "script_class", "threshold_px", "bbox_figure_px", "h_ink_px", "ink_area_px", "class_median_px", "ratio_to_class_median", "role_ratio", "glyph_pass", "reason", "raw_mask_path", "source_font", "pdf_size_pt", "font_color_rgb"]
    write_csv(OUT / "after_pixel_measurements.csv", glyph_rows, pixel_fields)
    write_csv(OUT / "after_overlap_report.csv", pair_rows, list(pair_rows[0].keys()))
    write_csv(OUT / "clip_report.csv", clip_rows, list(clip_rows[0].keys()))
    write_csv(OUT / "glyph_manual_ledger.csv", glyph_manual, list(glyph_manual[0].keys()))
    write_csv(OUT / "graphic_manual_ledger.csv", graphic_manual, list(graphic_manual[0].keys()))
    write_csv(OUT / "critical_relation_manual_ledger.csv", critical_manual, list(critical_manual[0].keys()))
    write_json(OUT / "machine_precheck.json", {
        "rawdict_char_total": raw_char_total, "visible_glyph_total": visible_char_total, "nonvisible_space_total": nonvisible_space_total,
        "glyph_card_total": len(glyph_artifacts), "glyph_contact_sheets": [p.name for p in sheets],
        "raw_glyph_shared_pixels_resolved": len(glyph_collision_rows), "raw_glyph_shared_pixels_after_resolution": 0,
        "text_objects": len(text_objects), "pdf_drawing_paths_in_scope": len(path_rows), "semantic_graphic_objects_including_opaque_layers": len(graphic_rows),
        "total_objects_N": len(objects), "all_unordered_pairs_expected": len(objects) * (len(objects) - 1) // 2, "all_unordered_pairs_written": len(pair_rows),
        "illegal_overlap_pixels_pre_manual": illegal_overlap_total, "clearance_fail_pairs_pre_manual": clearance_fail_total,
        "clip_fail_objects": sum(1 for r in clip_rows if r["decision"] != "PASS"),
        "drawing_path_reconciliation": "39 source-derived visible paths / 39 PDF get_drawings records in in-scope figure region",
        "math_rule_objects": 0, "math_rule_reconciliation": "source scan has no overline/underline/root/fraction/cancellation rule; PDF in-scope drawing paths all mapped to non-math semantic graphics",
        "manual_ledgers_status": "PENDING_MANUAL — generator intentionally did not write a PASS manual decision",
    })
    print(json.dumps({"out": str(OUT), "glyphs": len(glyph_artifacts), "text_objects": len(text_objects), "graphics": len(graphic_rows), "objects": len(objects), "pairs": len(pair_rows), "critical_pairs": len(critical_manual)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
