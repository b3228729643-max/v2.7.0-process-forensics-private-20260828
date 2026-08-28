from __future__ import annotations

import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label as cc_label
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa1_r110_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex")
PAGE_INDEX = 690
SCALE = 300 / 72.0
FIGURE_CROP_PX = (295, 2304, 2138, 3042)
FIGURE_CROP_PT = (71.0, 553.0, 513.0, 730.0)
PAGE_PNG = ROOT / "full_page_native300dpi.png"

GLYPH_MASK_DIR = ROOT / "masks" / "glyph"
GRAPHIC_MASK_DIR = ROOT / "masks" / "graphic"
CONTACT_DIR = ROOT / "contact_sheets"
CRITICAL_DIR = ROOT / "critical_rois"

DRAWING_SPECS = {
    13: ("G_NODE_FA_BORDER", "NODE_BORDER", "NODE_FA"),
    14: ("G_NODE_ALPHA_BORDER", "NODE_BORDER", "NODE_ALPHA"),
    15: ("G_NODE_FT_BORDER", "NODE_BORDER", "NODE_FT"),
    16: ("G_NODE_THETA_BORDER", "NODE_BORDER", "NODE_THETA"),
    17: ("G_NODE_FZY_BORDER", "NODE_BORDER", "NODE_FZY"),
    18: ("G_NODE_Z_BORDER", "NODE_BORDER", "NODE_Z"),
    19: ("G_NODE_Y_BORDER", "NODE_BORDER", "NODE_Y"),
    20: ("G_EDGE_FA_ALPHA", "LINE_ARROW", "EDGE_FA_ALPHA"),
    21: ("G_EDGE_ACTIVE_CHAIN", "LINE_ARROW", "EDGE_ACTIVE_CHAIN"),
    22: ("G_EDGE_FZY_Y", "LINE_ARROW", "EDGE_FZY_Y"),
    23: ("G_BLANKET_ALPHA_DASH", "PANEL_BORDER", "BLANKET_ALPHA"),
    24: ("G_BLANKET_Z_DASH", "PANEL_BORDER", "BLANKET_Z"),
    25: ("G_BLANKET_Y_DASH", "PANEL_BORDER", "BLANKET_Y"),
    26: ("G_ANN_ARROW_SHAFT", "LINE_ARROW", "ANN_IRRELEVANT_ARROW"),
    27: ("G_ANN_ARROWHEAD", "ARROWHEAD", "ANN_IRRELEVANT_ARROW"),
}

SEQ_PARENT = {
    33: ("NODE_FA", "NODE_LABEL", 24, 9.5),
    36: ("NODE_ALPHA", "NODE_LABEL", 25, 9.5),
    39: ("NODE_FT", "NODE_LABEL", 26, 9.5),
    42: ("NODE_THETA", "NODE_LABEL", 27, 9.5),
    45: ("NODE_FZY", "NODE_LABEL", 28, 9.5),
    48: ("NODE_Z", "NODE_LABEL", 29, 9.5),
    51: ("NODE_Y", "NODE_LABEL", 30, 9.5),
    58: ("ANN_BLANKET", "ANNOTATION", 40, 9.2),
    59: ("FORMULA_CONDITIONAL", "FORMULA_BLOCK", 42, 9.5),
    60: ("ANN_IRRELEVANT", "ANNOTATION", 45, 9.5),
    64: ("CAPTION_TEXT", "CAPTION", 50, 10.0),
}


def rgb255(color) -> np.ndarray:
    if isinstance(color, int):
        return np.array([(color >> 16) & 255, (color >> 8) & 255, color & 255], dtype=float)
    return np.array([round(float(x) * 255) for x in color], dtype=float)


def script_class(ch: str) -> str:
    cp = ord(ch)
    cat = unicodedata.category(ch)
    if ch in {",", "，", "、", ".", "。", ":", "：", ";", "；", "…"}:
        return "LOW_PROFILE_PUNCTUATION"
    if ch in {"∣", "|", "∝", "+", "−", "=", "×", "÷"}:
        return "BASELINE_MATH_OPERATOR"
    if ch in {"(", ")", "[", "]", "{", "}"}:
        return "MATH_DELIMITER"
    if "0" <= ch <= "9":
        return "LATIN_UPPER_OR_DIGIT"
    name = unicodedata.name(ch, "")
    if "MATHEMATICAL" in name and "SMALL" in name:
        return "LATIN_OR_GREEK_LOWER"
    if "GREEK" in name and "SMALL" in name:
        return "LATIN_OR_GREEK_LOWER"
    if "LATIN" in name and ch.islower():
        return "LATIN_OR_GREEK_LOWER"
    if "LATIN" in name and ch.isupper():
        return "LATIN_UPPER_OR_DIGIT"
    if cat.startswith("L") and (0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF):
        return "CJK_FULL_HEIGHT"
    if cat.startswith("P"):
        return "PUNCTUATION_OTHER"
    return "CJK_FULL_HEIGHT" if cp > 0x2FFF else "MATH_OR_SYMBOL"


def class_floor(kind: str) -> int | None:
    return {
        "CJK_FULL_HEIGHT": 30,
        "LATIN_UPPER_OR_DIGIT": 24,
        "LATIN_OR_GREEK_LOWER": 17,
        "BASELINE_MATH_OPERATOR": 22,
        "MATH_DELIMITER": 22,
        "MATH_OR_SYMBOL": 22,
    }.get(kind)


def px_rect(rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect[0] * SCALE),
        math.floor(rect[1] * SCALE),
        math.ceil(rect[2] * SCALE),
        math.ceil(rect[3] * SCALE),
    )


def rect_gap(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def color_select(pixels: np.ndarray, foreground: np.ndarray, background: np.ndarray) -> np.ndarray:
    delta = foreground - background
    norm2 = float(np.dot(delta, delta))
    if norm2 < 1:
        return np.linalg.norm(pixels.astype(float) - foreground, axis=2) <= 12
    rel = pixels.astype(float) - background
    alpha = np.tensordot(rel, delta, axes=([2], [0])) / norm2
    projected = background + alpha[..., None] * delta
    residual = np.linalg.norm(pixels.astype(float) - projected, axis=2)
    contrast = np.linalg.norm(pixels.astype(float) - background, axis=2)
    return (alpha >= (20 / 255)) & (alpha <= 1.25) & (residual <= 30) & (contrast >= 20)


def estimate_background(page_arr: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    x0p, y0p = max(0, x0 - 3), max(0, y0 - 3)
    x1p, y1p = min(page_arr.shape[1], x1 + 3), min(page_arr.shape[0], y1 + 3)
    patch = page_arr[y0p:y1p, x0p:x1p]
    ring = np.concatenate(
        [patch[0].reshape(-1, 3), patch[-1].reshape(-1, 3), patch[:, 0].reshape(-1, 3), patch[:, -1].reshape(-1, 3)], axis=0
    )
    quant = (ring // 4) * 4
    values, counts = np.unique(quant, axis=0, return_counts=True)
    return values[int(np.argmax(counts))].astype(float)


def ink_bbox(mask: np.ndarray, origin_x: int, origin_y: int):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min() + origin_x), int(ys.min() + origin_y), int(xs.max() + origin_x + 1), int(ys.max() + origin_y + 1)]


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def remove_boundary_bleed(mask: np.ndarray, glyph_class: str) -> np.ndarray:
    if glyph_class in {"LOW_PROFILE_PUNCTUATION", "PUNCTUATION_OTHER"}:
        return mask
    labels, count = cc_label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    if count <= 1:
        return mask
    areas = np.bincount(labels.ravel())[1:]
    total = int(mask.sum())
    result = mask.copy()
    for component, area in enumerate(areas, 1):
        ys, xs = np.nonzero(labels == component)
        touches_side = xs.min() <= 0 or xs.max() >= mask.shape[1] - 1
        tiny = area <= max(12, math.floor(total * 0.06))
        if touches_side and tiny:
            result[labels == component] = False
    return result


def cubic(p0, p1, p2, p3, n=48):
    result = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
        result.append((x * SCALE, y * SCALE))
    return result


def drawing_subpaths(drawing):
    paths = []
    current = []
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            p0, p1 = item[1], item[2]
            segment = [(p0.x * SCALE, p0.y * SCALE), (p1.x * SCALE, p1.y * SCALE)]
        elif kind == "c":
            segment = cubic(item[1], item[2], item[3], item[4])
        elif kind == "re":
            r = item[1]
            segment = [(r.x0 * SCALE, r.y0 * SCALE), (r.x1 * SCALE, r.y0 * SCALE), (r.x1 * SCALE, r.y1 * SCALE), (r.x0 * SCALE, r.y1 * SCALE), (r.x0 * SCALE, r.y0 * SCALE)]
        else:
            raise RuntimeError(f"unsupported drawing item {kind}")
        if current and math.dist(current[-1], segment[0]) < 0.1:
            current.extend(segment[1:])
        else:
            if current:
                paths.append(current)
            current = segment
    if current:
        paths.append(current)
    return paths


def draw_dashed(draw: ImageDraw.ImageDraw, points, fill, width, dash_pt):
    values = [float(x) for x in re.findall(r"[0-9]+(?:\.[0-9]+)?", str(dash_pt))]
    # PyMuPDF represents a solid dash as "[] 0". The trailing phase is not a
    # dash length and must never enter the stepping loop.
    if not values or str(dash_pt).lstrip().startswith("[]"):
        draw.line(points, fill=fill, width=width, joint="curve")
        return
    pattern = [x * SCALE for x in values[:-1]] if "]" in str(dash_pt) and len(values) > 1 else [x * SCALE for x in values]
    if not pattern or any(x <= 0 for x in pattern):
        draw.line(points, fill=fill, width=width, joint="curve")
        return
    pattern_index = 0
    remain = pattern[0]
    on = True
    for a, b in zip(points, points[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        pos = 0.0
        while pos < length:
            step = min(remain, length - pos)
            if on:
                p0 = (a[0] + dx * pos / length, a[1] + dy * pos / length)
                p1 = (a[0] + dx * (pos + step) / length, a[1] + dy * (pos + step) / length)
                draw.line([p0, p1], fill=fill, width=width)
            pos += step
            remain -= step
            if remain <= 1e-7:
                pattern_index = (pattern_index + 1) % len(pattern)
                remain = pattern[pattern_index]
                on = pattern_index % 2 == 0


def graphic_candidate_mask(drawing, image_size, include_fill: bool):
    mask_img = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(mask_img)
    paths = drawing_subpaths(drawing)
    width = max(1, math.ceil(float(drawing.get("width") or 0) * SCALE) + 4)
    for points in paths:
        if include_fill:
            draw.polygon(points, fill=255)
        draw_dashed(draw, points, 255, width, drawing.get("dashes") or "")
    return np.array(mask_img) > 0


def text_parent(seqno: int, bbox_pt) -> tuple[str, str, int, float]:
    parent, role, line, declared = SEQ_PARENT[seqno]
    if seqno == 64 and bbox_pt[0] < 110 and bbox_pt[1] < 713:
        return "CAPTION_LABEL", "CAPTION_LABEL", 50, 10.0
    return parent, role, line, declared


def make_glyph_contact_sheets(page_img: Image.Image, glyphs: list[dict]):
    sheets = []
    per_sheet = 10
    for sheet_index in range(math.ceil(len(glyphs) / per_sheet)):
        chunk = glyphs[sheet_index * per_sheet : (sheet_index + 1) * per_sheet]
        canvas = Image.new("RGB", (2200, 1900), "white")
        draw = ImageDraw.Draw(canvas)
        for cell_index, glyph in enumerate(chunk):
            col = cell_index % 2
            row = cell_index // 2
            ox, oy = col * 1100, row * 380
            draw.text((ox + 10, oy + 8), f"{glyph['element_id']} {glyph['codepoint']} H={glyph['h_ink_px']} A={glyph['ink_area_px']}", fill="black")
            x0, y0, x1, y1 = glyph["mask_bbox_full_px"]
            pad = 3
            rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
            rx1, ry1 = min(page_img.width, x1 + pad), min(page_img.height, y1 + pad)
            original = page_img.crop((rx0, ry0, rx1, ry1))
            local_mask = Image.open(GLYPH_MASK_DIR / glyph["safe_filename"]).convert("L")
            mask_canvas = Image.new("L", original.size, 255)
            mask_canvas.paste(local_mask, (x0 - rx0, y0 - ry0))
            overlay = original.copy()
            overlay_arr = np.array(overlay)
            mask_arr = np.array(mask_canvas) == 0
            overlay_arr[mask_arr] = [255, 0, 0]
            overlay = Image.fromarray(overlay_arr)
            mask_rgb = Image.merge("RGB", (mask_canvas, mask_canvas, mask_canvas))
            views = [("ORIGINAL 8x", original), ("TARGET OVERLAY 8x", overlay), ("MASK ONLY 8x", mask_rgb)]
            for view_index, (label, view) in enumerate(views):
                enlarged = view.resize((view.width * 8, view.height * 8), Image.Resampling.NEAREST)
                max_w, max_h = 340, 300
                crop_x = max(0, (enlarged.width - max_w) // 2)
                crop_y = max(0, (enlarged.height - max_h) // 2)
                shown = enlarged.crop((crop_x, crop_y, min(enlarged.width, crop_x + max_w), min(enlarged.height, crop_y + max_h)))
                vx = ox + 10 + view_index * 360
                vy = oy + 55
                canvas.paste(shown, (vx, vy))
                draw.text((vx, oy + 335), label, fill="black")
            glyph["contact_sheet"] = f"glyph_contact_sheet_{sheet_index + 1:02d}.png"
            glyph["contact_cell"] = cell_index + 1
        out = CONTACT_DIR / f"glyph_contact_sheet_{sheet_index + 1:02d}.png"
        canvas.save(out)
        sheets.append(out.name)
    return sheets


def make_graphic_contact_sheet(page_img: Image.Image, graphics: list[dict]):
    canvas = Image.new("RGB", (2200, 2400), "white")
    draw = ImageDraw.Draw(canvas)
    for i, graphic in enumerate(graphics):
        col, row = i % 3, i // 3
        ox, oy = col * 730, row * 480
        draw.text((ox + 8, oy + 8), f"{graphic['element_id']} seq={graphic['seqno']} px={graphic['mask_pixel_count']}", fill="black")
        x0, y0, x1, y1 = graphic["mask_bbox_full_px"]
        pad = 8
        rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
        rx1, ry1 = min(page_img.width, x1 + pad), min(page_img.height, y1 + pad)
        original = page_img.crop((rx0, ry0, rx1, ry1))
        local_mask = Image.open(GRAPHIC_MASK_DIR / graphic["safe_filename"]).convert("L")
        mask_canvas = Image.new("L", original.size, 255)
        mask_canvas.paste(local_mask, (x0 - rx0, y0 - ry0))
        overlay = np.array(original)
        overlay[np.array(mask_canvas) == 0] = [255, 0, 0]
        overlay = Image.fromarray(overlay)
        for vi, (label, view) in enumerate((("ORIGINAL native", original), ("TARGET OVERLAY", overlay), ("MASK ONLY", Image.merge("RGB", (mask_canvas, mask_canvas, mask_canvas))))):
            thumb = view.copy()
            thumb.thumbnail((220, 360), Image.Resampling.NEAREST)
            vx = ox + 5 + vi * 240
            canvas.paste(thumb, (vx, oy + 55))
            draw.text((vx, oy + 430), label, fill="black")
        graphic["contact_sheet"] = "graphic_contact_sheet_01.png"
        graphic["contact_cell"] = i + 1
    out = CONTACT_DIR / "graphic_contact_sheet_01.png"
    canvas.save(out)
    return out.name


def load_local_mask(obj):
    directory = GLYPH_MASK_DIR if obj["kind"] == "TEXT_GLYPH" else GRAPHIC_MASK_DIR
    return np.array(Image.open(directory / obj["safe_filename"]).convert("L")) == 0


def global_indices(obj, page_width):
    local = load_local_mask(obj)
    ys, xs = np.nonzero(local)
    x0, y0, _, _ = obj["mask_bbox_full_px"]
    gx, gy = xs + x0, ys + y0
    return set((gy * page_width + gx).tolist()), np.column_stack((gx, gy))


def design_relation(a, b):
    ids = {a["element_id"], b["element_id"]}
    if a["parent_id"] == b["parent_id"] and a["kind"] == b["kind"] == "TEXT_GLYPH":
        return "SAME_TEXT_PARENT_INTERNAL_TYPOGRAPHY"
    intentional = [
        ({"G_NODE_FA_BORDER", "G_EDGE_FA_ALPHA"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_ALPHA_BORDER", "G_EDGE_FA_ALPHA"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_ALPHA_BORDER", "G_EDGE_ACTIVE_CHAIN"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_FT_BORDER", "G_EDGE_ACTIVE_CHAIN"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_THETA_BORDER", "G_EDGE_ACTIVE_CHAIN"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_FZY_BORDER", "G_EDGE_ACTIVE_CHAIN"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_Z_BORDER", "G_EDGE_ACTIVE_CHAIN"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_FZY_BORDER", "G_EDGE_FZY_Y"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_NODE_Y_BORDER", "G_EDGE_FZY_Y"}, "EDGE_ENDPOINT_TO_NODE_BORDER"),
        ({"G_ANN_ARROW_SHAFT", "G_ANN_ARROWHEAD"}, "ARROW_SHAFT_HEAD_COMPOSITION"),
    ]
    for pair, tag in intentional:
        if ids == pair:
            return tag
    return "NONE"


def relation_class(a, b):
    roles = {a["role"], b["role"]}
    kinds = {a["kind"], b["kind"]}
    if kinds == {"TEXT_GLYPH"}:
        return "TEXT-TEXT"
    if "TEXT_GLYPH" in kinds:
        other = b if a["kind"] == "TEXT_GLYPH" else a
        return f"TEXT/FORMULA-{other['role']}"
    return f"GRAPHIC-{a['role']}__{b['role']}"


def main():
    for directory in (GLYPH_MASK_DIR, GRAPHIC_MASK_DIR, CONTACT_DIR, CRITICAL_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    page_img = Image.open(PAGE_PNG).convert("RGB")
    page_arr = np.array(page_img)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]

    glyphs = []
    ordinal = 0
    for span in page.get_texttrace():
        seqno = span["seqno"]
        if seqno not in SEQ_PARENT:
            continue
        foreground = rgb255(span["color"])
        for codepoint, glyph_id, origin, bbox in span["chars"]:
            ch = chr(codepoint)
            if ch.isspace():
                continue
            if not (bbox[0] >= FIGURE_CROP_PT[0] and bbox[2] <= FIGURE_CROP_PT[2] and bbox[1] >= FIGURE_CROP_PT[1] and bbox[3] <= FIGURE_CROP_PT[3]):
                continue
            ordinal += 1
            element_id = f"TXT_{ordinal:04d}_U{codepoint:04X}"
            safe_filename = f"txt_{ordinal:04d}_u{codepoint:04x}.png"
            box = px_rect(bbox)
            x0, y0, x1, y1 = box
            patch = page_arr[y0:y1, x0:x1]
            background = estimate_background(page_arr, box)
            mask = color_select(patch, foreground, background)
            # floor/ceil raster mapping can include one boundary column/row whose
            # pixel centre lies outside the PDF glyph bbox. Keep only pixel
            # centres owned by this exact PDF glyph bbox to prevent neighbour
            # antialias pixels from entering the target mask.
            x_centres_pt = (np.arange(x0, x1) + 0.5) / SCALE
            y_centres_pt = (np.arange(y0, y1) + 0.5) / SCALE
            ownership = (
                (x_centres_pt[None, :] >= bbox[0])
                & (x_centres_pt[None, :] < bbox[2])
                & (y_centres_pt[:, None] >= bbox[1])
                & (y_centres_pt[:, None] < bbox[3])
            )
            mask &= ownership
            if not mask.any():
                raise RuntimeError(f"empty glyph mask {element_id} {ch!r} box={box} fg={foreground} bg={background}")
            ibox = ink_bbox(mask, x0, y0)
            h_ink = ibox[3] - ibox[1]
            parent, role, source_line, declared_pt = text_parent(seqno, bbox)
            kind = script_class(ch)
            mask = remove_boundary_bleed(mask, kind)
            if not mask.any():
                raise RuntimeError(f"glyph mask emptied after boundary-bleed filtering {element_id}")
            ibox = ink_bbox(mask, x0, y0)
            h_ink = ibox[3] - ibox[1]
            save_mask(mask, GLYPH_MASK_DIR / safe_filename)
            glyphs.append(
                {
                    "element_id": element_id,
                    "safe_filename": safe_filename,
                    "kind": "TEXT_GLYPH",
                    "role": role,
                    "parent_id": parent,
                    "panel_id": "P1",
                    "char": ch,
                    "codepoint": f"U+{codepoint:04X}",
                    "pdf_glyph_id": glyph_id,
                    "pdf_seqno": seqno,
                    "font": span["font"],
                    "pdf_size_bp": round(float(span["size"]), 6),
                    "source_declared_pt": declared_pt,
                    "graphics_scale_for_text": 1.0,
                    "source_effective_pt": declared_pt,
                    "source_line": source_line,
                    "script_class": kind,
                    "nominal_class_floor_px": class_floor(kind),
                    "bbox_pt": [round(float(v), 6) for v in bbox],
                    "bbox_full_px": list(box),
                    "mask_bbox_full_px": list(box),
                    "ink_bbox_full_px": ibox,
                    "h_ink_px": h_ink,
                    "ink_area_px": int(mask.sum()),
                    "foreground_rgb": foreground.astype(int).tolist(),
                    "estimated_background_rgb": background.astype(int).tolist(),
                    "mask_source": "native300dpi current full-page raster; raw pixels within PDF glyph bbox selected by >=20/255 local-background contrast and foreground-color projection",
                }
            )

    drawings = page.get_drawings(extended=True)
    graphics = []
    for draw_index, (element_id, role, parent) in DRAWING_SPECS.items():
        drawing = drawings[draw_index]
        include_fill = role == "ARROWHEAD"
        candidate = graphic_candidate_mask(drawing, page_img.size, include_fill=include_fill)
        foreground = rgb255(drawing["color"])
        background = np.array([255, 255, 255], dtype=float)
        rect = drawing["rect"]
        nominal = px_rect(rect)
        cx0 = max(0, nominal[0] - 8); cy0 = max(0, nominal[1] - 8)
        cx1 = min(page_img.width, nominal[2] + 8); cy1 = min(page_img.height, nominal[3] + 8)
        candidate_local = candidate[cy0:cy1, cx0:cx1]
        selected_local = candidate_local & color_select(page_arr[cy0:cy1, cx0:cx1], foreground, background)
        ys, xs = np.nonzero(selected_local)
        if len(xs) == 0:
            raise RuntimeError(f"empty graphic mask {element_id}")
        box = [int(xs.min() + cx0), int(ys.min() + cy0), int(xs.max() + cx0 + 1), int(ys.max() + cy0 + 1)]
        local = selected_local[int(ys.min()) : int(ys.max() + 1), int(xs.min()) : int(xs.max() + 1)]
        safe_filename = element_id.lower() + ".png"
        save_mask(local, GRAPHIC_MASK_DIR / safe_filename)
        graphics.append(
            {
                "element_id": element_id,
                "safe_filename": safe_filename,
                "kind": "GRAPHIC",
                "role": role,
                "parent_id": parent,
                "panel_id": "P1",
                "draw_index": draw_index,
                "seqno": drawing["seqno"],
                "drawing_type": drawing["type"],
                "bbox_pt": [round(rect.x0, 6), round(rect.y0, 6), round(rect.x1, 6), round(rect.y1, 6)],
                "bbox_full_px": list(nominal),
                "mask_bbox_full_px": box,
                "ink_bbox_full_px": box,
                "mask_pixel_count": int(local.sum()),
                "foreground_rgb": foreground.astype(int).tolist(),
                "stroke_width_pt": round(float(drawing.get("width") or 0), 6),
                "dashes": drawing.get("dashes") or "",
                "fill_excluded_as_background": drawing["type"] in {"f", "fs"} and role != "ARROWHEAD",
                "mask_source": "native300dpi current full-page raster pixels selected inside vector-path candidate support; node fill excluded, arrowhead fill included",
            }
        )

    glyph_sheets = make_glyph_contact_sheets(page_img, glyphs)
    graphic_sheet = make_graphic_contact_sheet(page_img, graphics)

    objects = glyphs + graphics
    index_sets = {}
    coords = {}
    for obj in objects:
        index_sets[obj["element_id"]], coords[obj["element_id"]] = global_indices(obj, page_img.width)
    trees = {element_id: cKDTree(points) for element_id, points in coords.items()}

    pairs = []
    critical = []
    for i, a in enumerate(objects):
        for b in objects[i + 1 :]:
            aid, bid = a["element_id"], b["element_id"]
            overlap = len(index_sets[aid].intersection(index_sets[bid]))
            ac, bc = coords[aid], coords[bid]
            if overlap:
                raw_distance = 0.0
            else:
                small_id, large_id = (aid, bid) if len(ac) <= len(bc) else (bid, aid)
                raw_distance = float(trees[large_id].query(coords[small_id], k=1)[0].min())
            bbox_clearance = rect_gap(a["bbox_full_px"], b["bbox_full_px"])
            design = design_relation(a, b)
            relation = relation_class(a, b)
            priority = "ROUTINE"
            if overlap or raw_distance < 15 or (a["kind"] == "TEXT_GLYPH" and b["kind"] == "TEXT_GLYPH" and a["parent_id"] != b["parent_id"] and bbox_clearance < 20):
                priority = "CRITICAL_REVIEW"
            row = {
                "pair_id": f"PAIR_{len(pairs) + 1:05d}",
                "a_id": aid,
                "b_id": bid,
                "a_kind": a["kind"],
                "b_kind": b["kind"],
                "a_role": a["role"],
                "b_role": b["role"],
                "relation_class": relation,
                "same_semantic_parent": a["parent_id"] == b["parent_id"],
                "design_relation_tag": design,
                "bbox_clearance_px": round(bbox_clearance, 4),
                "raw_mask_intersection_px": overlap,
                "raw_mask_min_distance_px": round(raw_distance, 4),
                "review_priority": priority,
            }
            pairs.append(row)
            if priority == "CRITICAL_REVIEW":
                critical.append(row)

    with (ROOT / "visible_objects.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        fields = ["element_id", "safe_filename", "kind", "role", "parent_id", "panel_id", "char", "codepoint", "font", "pdf_size_bp", "source_declared_pt", "graphics_scale_for_text", "source_effective_pt", "source_line", "script_class", "nominal_class_floor_px", "bbox_pt", "bbox_full_px", "mask_bbox_full_px", "ink_bbox_full_px", "h_ink_px", "ink_area_px", "draw_index", "seqno", "drawing_type", "mask_pixel_count", "stroke_width_pt", "dashes", "fill_excluded_as_background", "mask_source", "contact_sheet", "contact_cell"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for obj in objects:
            row = dict(obj)
            for key in ("bbox_pt", "bbox_full_px", "mask_bbox_full_px", "ink_bbox_full_px"):
                if key in row:
                    row[key] = json.dumps(row[key], ensure_ascii=False)
            writer.writerow(row)

    with (ROOT / "safe_filename_map.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["element_id", "safe_filename", "kind"])
        writer.writeheader()
        writer.writerows({k: obj[k] for k in ("element_id", "safe_filename", "kind")} for obj in objects)

    with (ROOT / "machine_glyph_measurements.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        fields = ["element_id", "parent_id", "role", "char", "codepoint", "font", "source_line", "source_declared_pt", "graphics_scale_for_text", "source_effective_pt", "pdf_size_bp", "script_class", "nominal_class_floor_px", "bbox_full_px", "ink_bbox_full_px", "h_ink_px", "ink_area_px", "safe_filename", "contact_sheet", "contact_cell"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for glyph in glyphs:
            row = dict(glyph)
            row["bbox_full_px"] = json.dumps(row["bbox_full_px"])
            row["ink_bbox_full_px"] = json.dumps(row["ink_bbox_full_px"])
            writer.writerow(row)

    pair_fields = list(pairs[0])
    with (ROOT / "all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=pair_fields)
        writer.writeheader()
        writer.writerows(pairs)
    with (ROOT / "critical_relations.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=pair_fields)
        writer.writeheader()
        writer.writerows(critical)

    # One overlay for all glyph bboxes and one for semantic parents / graphics.
    crop = page_img.crop(FIGURE_CROP_PX)
    glyph_overlay = crop.copy()
    gdraw = ImageDraw.Draw(glyph_overlay)
    for glyph in glyphs:
        x0, y0, x1, y1 = glyph["bbox_full_px"]
        x0 -= FIGURE_CROP_PX[0]; x1 -= FIGURE_CROP_PX[0]
        y0 -= FIGURE_CROP_PX[1]; y1 -= FIGURE_CROP_PX[1]
        gdraw.rectangle((x0, y0, x1, y1), outline=(255, 0, 0), width=1)
        gdraw.text((x0, max(0, y0 - 9)), glyph["element_id"].split("_")[1], fill=(180, 0, 0))
    glyph_overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    semantic = crop.copy()
    sdraw = ImageDraw.Draw(semantic)
    parent_boxes = defaultdict(list)
    for obj in objects:
        parent_boxes[obj["parent_id"]].append(obj["bbox_full_px"])
    for parent_index, (parent, boxes) in enumerate(sorted(parent_boxes.items())):
        x0 = min(b[0] for b in boxes) - FIGURE_CROP_PX[0]
        y0 = min(b[1] for b in boxes) - FIGURE_CROP_PX[1]
        x1 = max(b[2] for b in boxes) - FIGURE_CROP_PX[0]
        y1 = max(b[3] for b in boxes) - FIGURE_CROP_PX[1]
        color = ((37 * parent_index) % 220, (83 * parent_index + 40) % 220, (131 * parent_index + 80) % 220)
        sdraw.rectangle((x0, y0, x1, y1), outline=color, width=3)
        sdraw.text((x0, max(0, y0 - 13)), parent, fill=color)
    semantic.save(ROOT / "semantic_object_overlay_300dpi.png")

    font_rows = [
        ("NODE_LABELS", "NODE_LABEL", "9,10,12,14,16", 9.5, 1.0, 9.5, "TikZ scale=1.100 changes coordinates; no transform shape, so node text scale remains 1.0"),
        ("ANN_BLANKET", "ANNOTATION", "40-41", 9.2, 1.0, 9.2, "R168 advisory candidate; must be judged from current native evidence, not threshold alone"),
        ("FORMULA_CONDITIONAL", "FORMULA_BLOCK", "42-44", 9.5, 1.0, 9.5, "explicit node font"),
        ("ANN_IRRELEVANT", "ANNOTATION", "45-46", 9.5, 1.0, 9.5, "explicit node font"),
        ("CAPTION", "CAPTION", "49-50", 10.0, 1.0, 10.0, "document caption text; PDF text trace 9.9626bp corresponds to 10pt TeX"),
    ]
    with (ROOT / "machine_source_font_inventory.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source_element", "role", "source_lines", "declared_pt", "graphics_scale_for_text", "effective_pt", "machine_note"])
        writer.writerows(font_rows)

    low_profile_groups = defaultdict(list)
    for glyph in glyphs:
        if glyph["script_class"] == "LOW_PROFILE_PUNCTUATION":
            key = (glyph["char"], glyph["font"], glyph["source_effective_pt"], tuple(glyph["foreground_rgb"]))
            low_profile_groups[key].append(glyph)
    with (ROOT / "low_profile_calibration_inventory.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["calibration_group", "char", "codepoint", "font", "effective_pt", "color_rgb", "member_count", "element_ids", "h_ink_values", "area_values", "median_h", "median_area"])
        for group_index, (key, members) in enumerate(sorted(low_profile_groups.items(), key=lambda item: (ord(item[0][0]), item[0][1], item[0][2])), 1):
            char, font, effective_pt, color = key
            hs = [m["h_ink_px"] for m in members]
            areas = [m["ink_area_px"] for m in members]
            writer.writerow([f"CAL_{group_index:03d}", char, f"U+{ord(char):04X}", font, effective_pt, json.dumps(color), len(members), ";".join(m["element_id"] for m in members), ";".join(map(str, hs)), ";".join(map(str, areas)), float(np.median(hs)), float(np.median(areas))])

    drawing_coverage = []
    for graphic in graphics:
        drawing_coverage.append({"draw_index": graphic["draw_index"], "seqno": graphic["seqno"], "element_id": graphic["element_id"], "role": graphic["role"], "mask_file": f"masks/graphic/{graphic['safe_filename']}", "mask_pixel_count": graphic["mask_pixel_count"]})
    with (ROOT / "drawing_bidir_coverage.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(drawing_coverage[0]))
        writer.writeheader(); writer.writerows(drawing_coverage)

    freeze = {
        "handoff_id": "C-FIG-P641-01-R110-SA1-FRESH-ISOLATED-V1",
        "uid": "FIG-P641-01",
        "physical_page_1_based": 691,
        "printed_page": 678,
        "page_pt": [595.276, 841.89],
        "native300dpi_grid_px": [2480, 3508],
        "figure_crop_px_in_full_page": list(FIGURE_CROP_PX),
        "standalone_crop_px_in_full_page": [487, 2304, 1959, 2900],
        "visible_text_glyph_count": len(glyphs),
        "visible_graphic_foreground_count": len(graphics),
        "visible_object_denominator": len(objects),
        "unordered_pair_denominator": len(pairs),
        "expected_pair_denominator_formula": len(objects) * (len(objects) - 1) // 2,
        "critical_relation_count": len(critical),
        "text_parent_ids": sorted({g["parent_id"] for g in glyphs}),
        "graphic_ids": [g["element_id"] for g in graphics],
        "math_rule_object_count": 0,
        "math_rule_reason": "Current figure formulas contain no overline/underline, radical bar, fraction rule, cancel stroke, hat/vector path, or other formula rule; all visible math symbols are PDF text glyphs.",
        "glyph_contact_sheets": glyph_sheets,
        "graphic_contact_sheets": [graphic_sheet],
        "manual_decisions_generated_by_machine": False,
        "hard_gate_specification": {
            "R168": "Raster/font-outline/taxonomy or explicit 9.2pt threshold differences alone are advisory. Hard failure requires current-PDF missing/tofu/wrong glyph or math meaning, actual unreadability or visibly severe imbalance, true clipping, illegal overlap, or semantic/geometric error.",
            "overlap": "independent semantic foreground illegal intersection >=1 native px",
            "clip": "true final-visible foreground clipping >=1 native px",
            "required_views": ["full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png"],
        },
    }
    (ROOT / "denominator_freeze.json").write_text(json.dumps(freeze, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "machine_objects.json").write_text(json.dumps({"glyphs": glyphs, "graphics": graphics}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"glyphs": len(glyphs), "graphics": len(graphics), "objects": len(objects), "pairs": len(pairs), "critical": len(critical), "glyph_sheets": len(glyph_sheets)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
