from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R23_SA3_FRESH_ISOLATED_R103_20260825")
PAGE_INDEX = 703
PAGE_NUMBER = 704
SCALE = 300.0 / 72.0
BODY_PT = fitz.Rect(65, 55, 530, 220)
FIGURE_PT = fitz.Rect(65, 55, 530, 246)
FULL_IMAGE = ROOT / "01_native_views" / "full_page_300dpi.png"

DIRS = {
    "identity": ROOT / "00_identity",
    "views": ROOT / "01_native_views",
    "machine": ROOT / "02_machine",
    "objects": ROOT / "03_objects",
    "glyphs": ROOT / "04_glyphs",
    "pairs": ROOT / "05_pairs",
    "relations": ROOT / "06_relations",
    "contacts": ROOT / "07_contact_sheets",
    "critical": ROOT / "08_critical_rois",
    "manual": ROOT / "09_manual",
    "validation": ROOT / "10_validation",
    "manifests": ROOT / "11_manifests",
}

NODE_RECTS = {
    "trial": fitz.Rect(77.312, 68.454, 164.654, 102.470),
    "gamma": fitz.Rect(77.312, 133.652, 164.654, 167.668),
    "families": fitz.Rect(175.647, 99.636, 271.493, 136.486),
    "posterior": fitz.Rect(282.377, 92.549, 393.238, 143.573),
    "predictive": fitz.Rect(401.434, 75.541, 529.303, 160.581),
    "simplex": fitz.Rect(201.095, 161.148, 272.691, 195.164),
    "mom": fitz.Rect(297.757, 161.148, 369.354, 195.164),
    "lda": fitz.Rect(421.066, 179.007, 492.663, 213.023),
}

GRAPHICS = {
    1: ("GRAPHIC-NODE-TRIAL-BORDER", "NODE_BORDER", "trial", "border"),
    2: ("GRAPHIC-NODE-GAMMA-BORDER", "NODE_BORDER", "gamma", "border"),
    3: ("GRAPHIC-NODE-FAMILIES-BORDER", "NODE_BORDER", "families", "border"),
    4: ("GRAPHIC-NODE-POSTERIOR-BORDER", "NODE_BORDER", "posterior", "border"),
    5: ("GRAPHIC-NODE-PREDICTIVE-BORDER", "NODE_BORDER", "predictive", "border"),
    6: ("GRAPHIC-MATH-RULE-PREDICTIVE-FRACTION", "MATH_RULE", "predictive_formula", "line"),
    7: ("GRAPHIC-NODE-SIMPLEX-BORDER", "NODE_BORDER", "simplex", "border"),
    8: ("GRAPHIC-NODE-MOM-BORDER", "NODE_BORDER", "mom", "border"),
    9: ("GRAPHIC-NODE-LDA-BORDER", "NODE_BORDER", "lda", "border"),
    10: ("GRAPHIC-EDGE-R1-LINE", "LINE_ARROW", "R1", "line"),
    11: ("GRAPHIC-EDGE-R1-ARROWHEAD", "ARROWHEAD", "R1", "arrowhead"),
    12: ("GRAPHIC-EDGE-R2-LINE", "LINE_ARROW", "R2", "line"),
    13: ("GRAPHIC-EDGE-R2-ARROWHEAD", "ARROWHEAD", "R2", "arrowhead"),
    14: ("GRAPHIC-EDGE-R3-LINE", "LINE_ARROW", "R3", "line"),
    15: ("GRAPHIC-EDGE-R3-ARROWHEAD", "ARROWHEAD", "R3", "arrowhead"),
    16: ("GRAPHIC-EDGE-R4-LINE", "LINE_ARROW", "R4", "line"),
    17: ("GRAPHIC-EDGE-R4-ARROWHEAD", "ARROWHEAD", "R4", "arrowhead"),
    18: ("GRAPHIC-EDGE-R5-LINE", "LINE_ARROW", "R5", "line"),
    19: ("GRAPHIC-EDGE-R6-LINE", "LINE_ARROW", "R6", "line"),
    20: ("GRAPHIC-EDGE-R7-LINE", "LINE_ARROW", "R7", "line"),
    21: ("GRAPHIC-EDGE-R7-ARROWHEAD", "ARROWHEAD", "R7", "arrowhead"),
}

RELATIONS = [
    ("R1", "trial", "families", "directed_solid", [10, 11]),
    ("R2", "gamma", "families", "directed_solid", [12, 13]),
    ("R3", "families", "posterior", "directed_solid", [14, 15]),
    ("R4", "posterior", "predictive", "directed_solid", [16, 17]),
    ("R5", "families", "simplex", "undirected_thin", [18]),
    ("R6", "posterior", "mom", "undirected_thin", [19]),
    ("R7", "predictive", "lda", "directed_dashed", [20, 21]),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def pt_to_px_rect(rect: fitz.Rect, pad: int = 0) -> tuple[int, int, int, int]:
    return (
        max(0, math.floor(rect.x0 * SCALE) - pad),
        max(0, math.floor(rect.y0 * SCALE) - pad),
        min(page_w, math.ceil(rect.x1 * SCALE) + pad),
        min(page_h, math.ceil(rect.y1 * SCALE) + pad),
    )


def rect_contains_point(rect: fitz.Rect, x: float, y: float, margin: float = 0.2) -> bool:
    return rect.x0 - margin <= x <= rect.x1 + margin and rect.y0 - margin <= y <= rect.y1 + margin


def local_mode_rgb(arr: np.ndarray) -> np.ndarray:
    flat = arr.reshape(-1, 3)
    counts = Counter(map(tuple, flat.tolist()))
    return np.asarray(counts.most_common(1)[0][0], dtype=np.float32)


def segment_color_mixture(arr: np.ndarray, fg: tuple[int, int, int], backgrounds: list[tuple[int, int, int] | np.ndarray]) -> np.ndarray:
    pix = arr.astype(np.float32)
    fg_v = np.asarray(fg, dtype=np.float32)
    keep = np.zeros(arr.shape[:2], dtype=bool)
    for bg in backgrounds:
        bg_v = np.asarray(bg, dtype=np.float32)
        vec = fg_v - bg_v
        denom = float(np.dot(vec, vec))
        if denom < 1:
            continue
        alpha = np.sum((pix - bg_v) * vec, axis=2) / denom
        alpha_c = np.clip(alpha, 0.0, 1.0)
        recon = bg_v + alpha_c[..., None] * vec
        residual = np.linalg.norm(pix - recon, axis=2)
        contrast = np.max(np.abs(pix - bg_v), axis=2)
        keep |= (alpha > 0.02) & (alpha < 1.08) & (residual <= 16.0) & (contrast >= 20.0)
    return keep


def safe_char_name(char: str) -> str:
    return f"U{ord(char):04X}"


def classify_glyph(char: str, font: str, size: float) -> tuple[str, int]:
    cp = ord(char)
    if size < 9.0:
        return "LEGAL_NATURAL_SCRIPT", 15
    if (
        0x3400 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x3000 <= cp <= 0x303F
    ):
        return "CJK_FULL", 30
    if "Math" in font or "Mezenets" in font or cp >= 0x1D400 or char in "+-=<>/−":
        return "MATH_BASE", 22
    if char.isupper() or char.isdigit():
        return "LATIN_UPPER_OR_DIGIT", 24
    return "LATIN_OR_GREEK_LOWER", 17


def find_parent(rect: fitz.Rect) -> str:
    cx = (rect.x0 + rect.x1) / 2
    cy = (rect.y0 + rect.y1) / 2
    for name, node_rect in NODE_RECTS.items():
        if rect_contains_point(node_rect, cx, cy):
            return name
    if 445 <= cx <= 485 and 160 <= cy <= 180:
        return "R7_application_label"
    return "UNASSIGNED"


def bezier(p0, p1, p2, p3, steps=32):
    out = []
    for t in np.linspace(0, 1, steps):
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t**2
        d = t**3
        out.append((a * p0.x + b * p1.x + c * p2.x + d * p3.x, a * p0.y + b * p1.y + c * p2.y + d * p3.y))
    return out


def pxy(point) -> tuple[int, int]:
    return (round(point.x * SCALE), round(point.y * SCALE))


def drawing_support(drawing: dict, kind: str) -> np.ndarray:
    support = Image.new("1", (page_w, page_h), 0)
    draw = ImageDraw.Draw(support)
    stroke_px = math.ceil(float(drawing.get("width") or 0.7) * SCALE)
    width_px = max(2, stroke_px + (3 if kind == "border" else 1))
    if kind == "arrowhead":
        pts = []
        for item in drawing.get("items", []):
            if item[0] == "l":
                if not pts:
                    pts.append(pxy(item[1]))
                pts.append(pxy(item[2]))
        if pts:
            draw.polygon(pts, fill=1)
            draw.line(pts + [pts[0]], fill=1, width=width_px)
        return np.asarray(support, dtype=bool)

    for item in drawing.get("items", []):
        op = item[0]
        if op == "l":
            draw.line([pxy(item[1]), pxy(item[2])], fill=1, width=width_px)
        elif op == "c":
            pts = bezier(item[1], item[2], item[3], item[4])
            draw.line([(round(x * SCALE), round(y * SCALE)) for x, y in pts], fill=1, width=width_px)
        elif op == "re":
            r = item[1]
            draw.rectangle(pt_to_px_rect(r), outline=1, width=width_px)
        elif op == "qu":
            q = item[1]
            pts = [pxy(q.ul), pxy(q.ur), pxy(q.lr), pxy(q.ll), pxy(q.ul)]
            draw.line(pts, fill=1, width=width_px)
    return np.asarray(support, dtype=bool)


def object_pack(original: np.ndarray, mask: np.ndarray, title: str) -> Image.Image:
    if original.size == 0:
        original = np.full((1, 1, 3), 255, dtype=np.uint8)
        mask = np.zeros((1, 1), dtype=bool)
    overlay = original.copy()
    overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
    mono = np.full_like(original, 255)
    mono[mask] = 0
    panels = [Image.fromarray(original), Image.fromarray(overlay), Image.fromarray(mono)]
    w, h = panels[0].size
    label_h = 24
    canvas = Image.new("RGB", (max(3 * w, 3 * w * 8), label_h + h + 8 * h), "white")
    d = ImageDraw.Draw(canvas)
    d.text((3, 3), title, fill="black")
    for i, panel in enumerate(panels):
        canvas.paste(panel, (i * w, label_h))
        up = panel.resize((w * 8, h * 8), resample=Image.Resampling.NEAREST)
        canvas.paste(up, (i * w * 8, label_h + h))
    return canvas


def save_contact_sheets(items: list[dict], prefix: str, per_sheet: int = 15) -> list[str]:
    outputs = []
    for sheet_index in range(0, len(items), per_sheet):
        subset = items[sheet_index : sheet_index + per_sheet]
        cols = 3
        rows = math.ceil(len(subset) / cols)
        cell_w, cell_h = 500, 220
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        d = ImageDraw.Draw(sheet)
        for j, obj in enumerate(subset):
            x0 = (j % cols) * cell_w
            y0 = (j // cols) * cell_h
            crop = obj["crop"]
            mask = obj["local_mask"]
            overlay = crop.copy()
            overlay[mask] = [255, 0, 0]
            mono = np.full_like(crop, 255)
            mono[mask] = 0
            h, w = crop.shape[:2]
            scale = min(8.0, 145.0 / max(1, h), 145.0 / max(1, w))
            target_h = max(1, round(h * scale))
            target_w = max(1, round(w * scale))
            views = [crop, overlay, mono]
            d.text((x0 + 5, y0 + 4), obj["contact_label"], fill="black")
            for k, view in enumerate(views):
                resample = Image.Resampling.NEAREST if scale >= 1.0 else Image.Resampling.LANCZOS
                im = Image.fromarray(view).resize((target_w, target_h), resample)
                sheet.paste(im, (x0 + 5 + k * 160, y0 + 40))
            d.rectangle((x0, y0, x0 + cell_w - 1, y0 + cell_h - 1), outline=(180, 180, 180))
        n = sheet_index // per_sheet + 1
        path = DIRS["contacts"] / f"{prefix}_{n:02d}.png"
        sheet.save(path, dpi=(300, 300))
        outputs.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return outputs


for directory in DIRS.values():
    directory.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_rgb = np.asarray(Image.open(FULL_IMAGE).convert("RGB"))
page_h, page_w = page_rgb.shape[:2]
if (page_w, page_h) != (2481, 3508):
    raise RuntimeError(f"Unexpected native grid: {(page_w, page_h)}")

all_drawings = page.get_drawings()
# Build the unique vector fraction-rule mask before glyph extraction so the
# same-color rule can be subtracted from text bboxes without inventing pixels.
rule_drawing = all_drawings[6]
rule_rect = fitz.Rect(rule_drawing["rect"])
rule_x0, rule_y0, rule_x1, rule_y1 = pt_to_px_rect(rule_rect, pad=5)
rule_crop = page_rgb[rule_y0:rule_y1, rule_x0:rule_x1]
rule_support_global = drawing_support(rule_drawing, "line")
rule_fg = tuple(round(float(v) * 255) for v in rule_drawing["color"])
rule_local = segment_color_mixture(rule_crop, rule_fg, [local_mode_rgb(rule_crop), (255, 255, 255)]) & rule_support_global[rule_y0:rule_y1, rule_x0:rule_x1]
math_rule_mask_global = np.zeros((page_h, page_w), dtype=bool)
math_rule_mask_global[rule_y0:rule_y1, rule_x0:rule_x1] = rule_local

raw = page.get_text("rawdict")
glyph_objs: list[dict] = []
visible_chars = []
for block in raw.get("blocks", []):
    if block.get("type") != 0:
        continue
    for line_index, line in enumerate(block.get("lines", []), 1):
        for span_index, span in enumerate(line.get("spans", []), 1):
            for char_index, char in enumerate(span.get("chars", []), 1):
                c = char.get("c", "")
                rect = fitz.Rect(char["bbox"])
                cx = (rect.x0 + rect.x1) / 2
                cy = (rect.y0 + rect.y1) / 2
                if c == " " or not rect_contains_point(BODY_PT, cx, cy):
                    continue
                visible_chars.append((char, span, line_index, span_index, char_index))

for ordinal, (char, span, line_index, span_index, char_index) in enumerate(visible_chars, 1):
    c = char["c"]
    rect = fitz.Rect(char["bbox"])
    x0, y0, x1, y1 = pt_to_px_rect(rect, pad=1)
    crop = page_rgb[y0:y1, x0:x1].copy()
    bg = local_mode_rgb(crop)
    fg = rgb_from_int(int(span.get("color", 0)))
    mask = segment_color_mixture(crop, fg, [bg, (255, 255, 255)])
    # Restrict to the extracted glyph bbox plus one native pixel.
    core_x0 = max(0, math.floor(rect.x0 * SCALE) - x0)
    core_y0 = max(0, math.floor(rect.y0 * SCALE) - y0)
    core_x1 = min(crop.shape[1], math.ceil(rect.x1 * SCALE) - x0)
    core_y1 = min(crop.shape[0], math.ceil(rect.y1 * SCALE) - y0)
    core = np.zeros_like(mask)
    core[max(0, core_y0 - 1) : min(crop.shape[0], core_y1 + 1), max(0, core_x0 - 1) : min(crop.shape[1], core_x1 + 1)] = True
    mask &= core
    # The TeX fraction rule is a separately inventoried graphic object and
    # must not contaminate same-colour numerator/denominator glyph masks.
    mask &= ~math_rule_mask_global[y0:y1, x0:x1]
    yy, xx = np.where(mask)
    object_id = f"GLYPH-{ordinal:03d}"
    safe = f"GLYPH_{ordinal:03d}_{safe_char_name(c)}"
    category, threshold = classify_glyph(c, str(span.get("font", "")), float(span.get("size", 0)))
    h_ink = int(yy.max() - yy.min() + 1) if len(yy) else 0
    w_ink = int(xx.max() - xx.min() + 1) if len(xx) else 0
    area = int(mask.sum())
    global_coords = np.column_stack((yy + y0, xx + x0)).astype(np.int32)
    parent = find_parent(rect)
    cy = (rect.y0 + rect.y1) / 2
    font_name = str(span.get("font", ""))
    if parent == "trial" and ("Math" in font_name or ord(c) >= 0x1D400):
        parent = "trial_formula"
    elif parent == "posterior" and cy >= 118:
        parent = "posterior_formula"
    elif parent == "predictive" and cy >= 114:
        parent = "predictive_formula"
    pack_path = DIRS["glyphs"] / f"{safe}_1x_8x.png"
    object_pack(crop, mask, f"{object_id} {safe_char_name(c)}").save(pack_path, dpi=(300, 300))
    glyph_objs.append({
        "object_id": object_id,
        "safe_filename": safe,
        "object_type": "GLYPH",
        "char": c,
        "codepoint": f"U+{ord(c):04X}",
        "unicode_name": unicodedata.name(c, "UNKNOWN"),
        "font": str(span.get("font", "")),
        "source_extracted_size_pt": round(float(span.get("size", 0)), 4),
        "category": category,
        "threshold_px": threshold,
        "h_ink_px": h_ink,
        "w_ink_px": w_ink,
        "ink_area_px": area,
        "threshold_eval": "MEETS" if h_ink >= threshold else "BELOW_NUMERIC_THRESHOLD",
        "bbox_pt": [round(v, 4) for v in rect],
        "bbox_px": [x0, y0, x1, y1],
        "parent": parent,
        "line_index": line_index,
        "span_index": span_index,
        "char_index": char_index,
        "mask_pixel_count": area,
        "empty_mask_count": int(area == 0),
        "pack_path": str(pack_path.relative_to(ROOT)).replace("\\", "/"),
        "crop": crop,
        "local_mask": mask,
        "coords": global_coords,
        "contact_label": f"{object_id} {safe_char_name(c)} {parent} H={h_ink}/{threshold} {('OK' if h_ink >= threshold else 'LOW')}",
    })

# PDF character bboxes can overlap vertically across tightly typeset lines.
# Partition any same-colour pixel claimed by multiple glyph bboxes to the
# nearest normalized bbox centre, then regenerate each unique raw mask pack.
pixel_claims: dict[tuple[int, int], list[int]] = defaultdict(list)
for glyph_index, obj in enumerate(glyph_objs):
    for coord in obj["coords"]:
        pixel_claims[(int(coord[0]), int(coord[1]))].append(glyph_index)
for (py, px), claimants in pixel_claims.items():
    if len(claimants) <= 1:
        continue
    def score(glyph_index: int) -> float:
        gx0, gy0, gx1, gy1 = glyph_objs[glyph_index]["bbox_px"]
        cx = (gx0 + gx1) / 2
        cy = (gy0 + gy1) / 2
        return ((px - cx) / max(1.0, (gx1 - gx0) / 2)) ** 2 + ((py - cy) / max(1.0, (gy1 - gy0) / 2)) ** 2
    winner = min(claimants, key=score)
    for loser in claimants:
        if loser == winner:
            continue
        obj = glyph_objs[loser]
        lx0, ly0, _, _ = obj["bbox_px"]
        ly, lx = py - ly0, px - lx0
        if 0 <= ly < obj["local_mask"].shape[0] and 0 <= lx < obj["local_mask"].shape[1]:
            obj["local_mask"][ly, lx] = False

for obj in glyph_objs:
    mask = obj["local_mask"]
    yy, xx = np.where(mask)
    x0, y0, _, _ = obj["bbox_px"]
    area = int(mask.sum())
    obj["h_ink_px"] = int(yy.max() - yy.min() + 1) if len(yy) else 0
    obj["w_ink_px"] = int(xx.max() - xx.min() + 1) if len(xx) else 0
    obj["ink_area_px"] = area
    obj["mask_pixel_count"] = area
    obj["empty_mask_count"] = int(area == 0)
    obj["threshold_eval"] = "MEETS" if obj["h_ink_px"] >= obj["threshold_px"] else "BELOW_NUMERIC_THRESHOLD"
    obj["coords"] = np.column_stack((yy + y0, xx + x0)).astype(np.int32)
    obj["contact_label"] = f"{obj['object_id']} {obj['safe_filename'].split('_')[-1]} {obj['parent']} H={obj['h_ink_px']}/{obj['threshold_px']} {('OK' if obj['h_ink_px'] >= obj['threshold_px'] else 'LOW')}"
    pack_path = ROOT / obj["pack_path"]
    object_pack(obj["crop"], mask, f"{obj['object_id']} {obj['codepoint'].replace('+', '')}").save(pack_path, dpi=(300, 300))

graphic_objs: list[dict] = []
for drawing_index, (object_id, object_type, parent, kind) in GRAPHICS.items():
    drawing = all_drawings[drawing_index]
    rect = fitz.Rect(drawing["rect"])
    x0, y0, x1, y1 = pt_to_px_rect(rect, pad=5)
    crop = page_rgb[y0:y1, x0:x1].copy()
    support_global = drawing_support(drawing, kind)
    support = support_global[y0:y1, x0:x1]
    color_float = drawing.get("fill") if kind == "arrowhead" and drawing.get("fill") else drawing.get("color")
    fg = tuple(round(float(v) * 255) for v in color_float)
    bgs: list[tuple[int, int, int] | np.ndarray] = [local_mode_rgb(crop), (255, 255, 255)]
    if drawing.get("fill") and kind == "border":
        bgs.append(tuple(round(float(v) * 255) for v in drawing["fill"]))
    mask = segment_color_mixture(crop, fg, bgs) & support
    if drawing_index == 6:
        mask = math_rule_mask_global[y0:y1, x0:x1].copy()
    yy, xx = np.where(mask)
    area = int(mask.sum())
    global_coords = np.column_stack((yy + y0, xx + x0)).astype(np.int32)
    safe = object_id.replace("-", "_")
    pack_path = DIRS["objects"] / f"{safe}_1x_8x.png"
    object_pack(crop, mask, object_id).save(pack_path, dpi=(300, 300))
    graphic_objs.append({
        "object_id": object_id,
        "safe_filename": safe,
        "object_type": object_type,
        "char": "",
        "codepoint": "",
        "unicode_name": "",
        "font": "",
        "source_extracted_size_pt": "",
        "category": object_type,
        "threshold_px": "",
        "h_ink_px": int(yy.max() - yy.min() + 1) if len(yy) else 0,
        "w_ink_px": int(xx.max() - xx.min() + 1) if len(xx) else 0,
        "ink_area_px": area,
        "threshold_eval": "NONEMPTY" if area else "EMPTY",
        "bbox_pt": [round(v, 4) for v in rect],
        "bbox_px": [x0, y0, x1, y1],
        "parent": parent,
        "drawing_index": drawing_index,
        "drawing_kind": kind,
        "drawing_type": drawing.get("type"),
        "drawing_item_count": len(drawing.get("items", [])),
        "stroke_width_pt": round(float(drawing.get("width") or 0), 5),
        "mask_pixel_count": area,
        "empty_mask_count": int(area == 0),
        "pack_path": str(pack_path.relative_to(ROOT)).replace("\\", "/"),
        "crop": crop,
        "local_mask": mask,
        "coords": global_coords,
        "contact_label": f"{object_id} idx={drawing_index} px={area} {('OK' if area else 'EMPTY')}",
    })

# Arrowheads are painted after their shafts in the source PDF.  Remove the
# opaque arrowhead pixels from each corresponding shaft so both ledgers carry
# unique final-visible masks while preserving the designed zero-clearance join.
graphic_by_index = {o["drawing_index"]: o for o in graphic_objs}
for _, _, _, _, drawing_indices in RELATIONS:
    if len(drawing_indices) != 2:
        continue
    line_obj = graphic_by_index[drawing_indices[0]]
    arrow_obj = graphic_by_index[drawing_indices[1]]
    arrow_pixels = {tuple(v) for v in arrow_obj["coords"].tolist()}
    if not arrow_pixels:
        continue
    kept = np.asarray([v for v in line_obj["coords"].tolist() if tuple(v) not in arrow_pixels], dtype=np.int32)
    if kept.size == 0:
        kept = np.empty((0, 2), dtype=np.int32)
    line_obj["coords"] = kept
    lx0, ly0, _, _ = line_obj["bbox_px"]
    local = np.zeros_like(line_obj["local_mask"])
    if len(kept):
        yy = kept[:, 0] - ly0
        xx = kept[:, 1] - lx0
        local[yy, xx] = True
    line_obj["local_mask"] = local
    yy, xx = np.where(local)
    area = int(local.sum())
    line_obj["mask_pixel_count"] = area
    line_obj["ink_area_px"] = area
    line_obj["empty_mask_count"] = int(area == 0)
    line_obj["h_ink_px"] = int(yy.max() - yy.min() + 1) if len(yy) else 0
    line_obj["w_ink_px"] = int(xx.max() - xx.min() + 1) if len(xx) else 0
    line_obj["threshold_eval"] = "NONEMPTY" if area else "EMPTY"
    line_obj["contact_label"] = f"{line_obj['object_id']} idx={line_obj['drawing_index']} px={area} {('OK' if area else 'EMPTY')}"
    object_pack(line_obj["crop"], local, line_obj["object_id"]).save(ROOT / line_obj["pack_path"], dpi=(300, 300))

objects = glyph_objs + graphic_objs
object_by_id = {o["object_id"]: o for o in objects}
if len(object_by_id) != len(objects):
    raise RuntimeError("Duplicate object IDs")

def bbox_gap(a: dict, b: dict) -> float:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


trees = {o["object_id"]: cKDTree(o["coords"]) if len(o["coords"]) else None for o in objects}

def exact_clearance(a: dict, b: dict) -> tuple[int, float]:
    ca, cb = a["coords"], b["coords"]
    if len(ca) == 0 or len(cb) == 0:
        return 0, math.inf
    sa = {tuple(v) for v in ca.tolist()}
    sb = {tuple(v) for v in cb.tolist()}
    overlap = len(sa & sb)
    if overlap:
        return overlap, 0.0
    if len(ca) <= len(cb):
        distances, _ = trees[b["object_id"]].query(ca, k=1, workers=1)
    else:
        distances, _ = trees[a["object_id"]].query(cb, k=1, workers=1)
    # Pixel-edge clearance: centre distance minus one pixel, floored at zero.
    return 0, max(0.0, float(np.min(distances)) - 1.0)


def semantic_pair_class(a: dict, b: dict) -> str:
    if a["parent"] == b["parent"] and a["parent"] != "UNASSIGNED":
        if a["parent"].startswith("R") or a["parent"] == "predictive_formula":
            return "DESIGN_COMPOSITION"
        if a["object_type"] == "GLYPH" and b["object_type"] == "GLYPH":
            return "SAME_TEXT_PARENT"
    base_a = a["parent"].replace("_formula", "")
    base_b = b["parent"].replace("_formula", "")
    if a["object_type"] == "GLYPH" and b["object_type"] == "GLYPH" and base_a == base_b and base_a != "UNASSIGNED":
        return "SAME_TEXT_PARENT"
    parents = {a["parent"], b["parent"]}
    for rid, source, target, _, _ in RELATIONS:
        types = {a["object_type"], b["object_type"]}
        if rid in parents and (source in parents or target in parents) and "NODE_BORDER" in types and ("LINE_ARROW" in types or "ARROWHEAD" in types):
            return "INTENTIONAL_EDGE_NODE_CONNECTION"
    return "INDEPENDENT"


def hard_clearance_threshold(a: dict, b: dict, pair_class: str) -> int:
    if pair_class != "INDEPENDENT":
        return 0
    types = {a["object_type"], b["object_type"]}
    if types == {"GLYPH"}:
        return 4
    if "GLYPH" in types and "NODE_BORDER" in types:
        return 5
    if "GLYPH" in types and ("LINE_ARROW" in types or "ARROWHEAD" in types):
        return 3
    return 0


pair_rows = []
critical_pairs = []
illegal_pairs = []
clearance_failure_pairs = []
for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
    overlap, clearance = exact_clearance(a, b)
    pair_class = semantic_pair_class(a, b)
    hard_relevant = pair_class == "INDEPENDENT"
    illegal = hard_relevant and overlap > 0
    hard_threshold = hard_clearance_threshold(a, b, pair_class)
    clearance_failure = hard_threshold > 0 and clearance < hard_threshold
    if illegal:
        illegal_pairs.append((a, b, overlap, clearance, pair_class))
    if clearance_failure:
        clearance_failure_pairs.append((a, b, overlap, clearance, pair_class, hard_threshold))
    critical = hard_relevant and clearance < 12.0
    if critical or pair_class in {"INTENTIONAL_EDGE_NODE_CONNECTION", "DESIGN_COMPOSITION"} and clearance < 3.0:
        critical_pairs.append((a, b, overlap, clearance, pair_class))
    pair_rows.append({
        "pair_id": f"PAIR-{pair_index:05d}",
        "object_a": a["object_id"],
        "object_b": b["object_id"],
        "type_a": a["object_type"],
        "type_b": b["object_type"],
        "parent_a": a["parent"],
        "parent_b": b["parent"],
        "semantic_pair_class": pair_class,
        "bbox_lower_bound_px": round(bbox_gap(a, b), 3),
        "overlap_pixel_count": overlap,
        "min_clearance_px": round(clearance, 3) if math.isfinite(clearance) else "INF",
        "hard_clearance_threshold_px": hard_threshold,
        "clearance_hard_eval": "FAIL" if clearance_failure else ("PASS" if hard_threshold else "N/A"),
        "machine_relation": "ILLEGAL_OVERLAP" if illegal else ("CLEARANCE_HARD_FAIL" if clearance_failure else ("ADVISORY_UNDER_12" if critical else "NO_MACHINE_HARD_FAILURE")),
    })

expected_pairs = len(objects) * (len(objects) - 1) // 2
if len(pair_rows) != expected_pairs:
    raise RuntimeError("Pair denominator mismatch")

def strip_runtime_fields(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in {"crop", "local_mask", "coords", "contact_label"}}


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    for row in rows[1:]:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


object_rows = [strip_runtime_fields(o) for o in objects]
glyph_rows = [strip_runtime_fields(o) for o in glyph_objs]
graphic_rows = [strip_runtime_fields(o) for o in graphic_objs]
write_csv(DIRS["machine"] / "object_ledger.csv", object_rows)
write_csv(DIRS["machine"] / "glyph_ledger.csv", glyph_rows)
write_csv(DIRS["machine"] / "graphic_ledger.csv", graphic_rows)
write_csv(DIRS["pairs"] / "all_unordered_pairs.csv", pair_rows)

clearance_groups: dict[str, list[dict]] = defaultdict(list)
for row in pair_rows:
    if row["semantic_pair_class"] != "INDEPENDENT":
        continue
    key = "|".join(sorted([row["type_a"], row["type_b"]]))
    clearance_groups[key].append(row)
clearance_rows = []
for key, rows in sorted(clearance_groups.items()):
    nearest = min(rows, key=lambda r: float(r["min_clearance_px"]) if r["min_clearance_px"] != "INF" else math.inf)
    clearance_rows.append({
        "pair_type": key,
        "pair_count": len(rows),
        "minimum_clearance_px": nearest["min_clearance_px"],
        "minimum_pair_id": nearest["pair_id"],
        "minimum_object_a": nearest["object_a"],
        "minimum_object_b": nearest["object_b"],
        "hard_threshold_px": nearest["hard_clearance_threshold_px"],
        "minimum_hard_eval": nearest["clearance_hard_eval"],
    })
write_csv(DIRS["pairs"] / "clearance_category_summary.csv", clearance_rows)

id_map = [{"object_id": o["object_id"], "safe_filename": o["safe_filename"], "pack_path": o["pack_path"]} for o in objects]
write_csv(DIRS["machine"] / "id_safe_filename_map.csv", id_map)

glyph_contact_paths = save_contact_sheets(glyph_objs, "glyph_contact_sheet", per_sheet=15)
graphic_contact_paths = save_contact_sheets(graphic_objs, "graphic_contact_sheet", per_sheet=9)

# Figure object overlay with compact numeric labels.
overlay = page_rgb.copy()
od = ImageDraw.Draw(Image.fromarray(overlay))
overlay_image = Image.fromarray(overlay)
od = ImageDraw.Draw(overlay_image)
for idx, obj in enumerate(objects, 1):
    x0, y0, x1, y1 = obj["bbox_px"]
    color = (220, 30, 30) if obj["object_type"] == "GLYPH" else (20, 80, 220)
    od.rectangle((x0, y0, x1, y1), outline=color, width=1)
    if obj["object_type"] != "GLYPH":
        od.text((x0, max(0, y0 - 12)), obj["object_id"].replace("GRAPHIC-", "G-"), fill=color)
body_x0, body_y0, body_x1, body_y1 = pt_to_px_rect(BODY_PT)
overlay_image.crop((body_x0, body_y0, body_x1, body_y1)).save(DIRS["machine"] / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))

# Pair matrix: machine relationship classes only.
n = len(objects)
matrix = np.full((n, n, 3), 245, dtype=np.uint8)
np.fill_diagonal(matrix[:, :, 0], 40)
np.fill_diagonal(matrix[:, :, 1], 40)
np.fill_diagonal(matrix[:, :, 2], 40)
index_by_id = {o["object_id"]: i for i, o in enumerate(objects)}
for row in pair_rows:
    i, j = index_by_id[row["object_a"]], index_by_id[row["object_b"]]
    if row["machine_relation"] == "ILLEGAL_OVERLAP":
        color = (230, 30, 30)
    elif row["machine_relation"] in {"CLEARANCE_HARD_FAIL", "ADVISORY_UNDER_12"}:
        color = (245, 150, 30)
    elif row["semantic_pair_class"] in {"DESIGN_COMPOSITION", "INTENTIONAL_EDGE_NODE_CONNECTION", "SAME_TEXT_PARENT"}:
        color = (75, 180, 90)
    else:
        color = (210, 220, 235)
    matrix[i, j] = matrix[j, i] = color
Image.fromarray(matrix).save(DIRS["pairs"] / "pair_matrix_1x.png")
Image.fromarray(matrix).resize((n * 8, n * 8), Image.Resampling.NEAREST).save(DIRS["pairs"] / "pair_matrix_8x_nearest.png")

# Critical ROI contact sheets. These are machine-selected candidates; final interpretation is external/manual.
critical_rows = []
for idx, (a, b, overlap, clearance, pair_class) in enumerate(critical_pairs, 1):
    ca, cb = a["coords"], b["coords"]
    if overlap:
        shared = list({tuple(v) for v in ca.tolist()} & {tuple(v) for v in cb.tolist()})
        pa = pb = np.asarray(shared[0], dtype=np.int32)
    elif len(ca) <= len(cb):
        distances, nearest_index = trees[b["object_id"]].query(ca, k=1, workers=1)
        k = int(np.argmin(distances))
        pa, pb = ca[k], cb[int(nearest_index[k])]
    else:
        distances, nearest_index = trees[a["object_id"]].query(cb, k=1, workers=1)
        k = int(np.argmin(distances))
        pb, pa = cb[k], ca[int(nearest_index[k])]
    y0 = max(0, int(min(pa[0], pb[0])) - 28)
    x0 = max(0, int(min(pa[1], pb[1])) - 28)
    y1 = min(page_h, int(max(pa[0], pb[0])) + 29)
    x1 = min(page_w, int(max(pa[1], pb[1])) + 29)
    raw_roi = page_rgb[y0:y1, x0:x1].copy()
    a_mask = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    b_mask = np.zeros_like(a_mask)
    for coords, target in ((a["coords"], a_mask), (b["coords"], b_mask)):
        if len(coords):
            yy = coords[:, 0] - y0
            xx = coords[:, 1] - x0
            valid = (yy >= 0) & (yy < target.shape[0]) & (xx >= 0) & (xx < target.shape[1])
            target[yy[valid], xx[valid]] = True
    over = raw_roi.copy()
    over[a_mask] = [255, 0, 0]
    over[b_mask] = [0, 80, 255]
    both = a_mask & b_mask
    over[both] = [255, 0, 255]
    mask_panel = np.full_like(raw_roi, 255)
    mask_panel[a_mask] = [255, 0, 0]
    mask_panel[b_mask] = [0, 80, 255]
    mask_panel[both] = [255, 0, 255]
    views = [Image.fromarray(raw_roi), Image.fromarray(over), Image.fromarray(mask_panel)]
    w, h = views[0].size
    canvas = Image.new("RGB", (w * 3 * 8, 28 + h + h * 8), "white")
    dd = ImageDraw.Draw(canvas)
    dd.text((3, 3), f"{a['object_id']} :: {b['object_id']} overlap={overlap} clearance={clearance:.3f} class={pair_class}", fill="black")
    for k, im in enumerate(views):
        canvas.paste(im, (k * w, 28))
        canvas.paste(im.resize((w * 8, h * 8), Image.Resampling.NEAREST), (k * w * 8, 28 + h))
    path = DIRS["critical"] / f"CRITICAL_{idx:04d}.png"
    canvas.save(path, dpi=(300, 300))
    critical_rows.append({
        "critical_id": f"CRITICAL-{idx:04d}",
        "object_a": a["object_id"],
        "object_b": b["object_id"],
        "semantic_pair_class": pair_class,
        "overlap_pixel_count": overlap,
        "min_clearance_px": round(clearance, 3),
        "roi_xywh_px": [x0, y0, x1 - x0, y1 - y0],
        "evidence_path": str(path.relative_to(ROOT)).replace("\\", "/"),
    })
write_csv(DIRS["critical"] / "critical_machine_index.csv", critical_rows)

# Seven source relations and visual overlay.
relation_rows = []
relation_image = Image.fromarray(page_rgb.copy())
rd = ImageDraw.Draw(relation_image)
palette = [(220, 20, 60), (255, 130, 0), (20, 140, 80), (30, 110, 220), (150, 60, 200), (20, 170, 180), (210, 80, 150)]
for color, (rid, source, target, edge_type, drawing_indices) in zip(palette, RELATIONS):
    coords_for_relation = []
    for drawing_index in drawing_indices:
        obj = object_by_id[GRAPHICS[drawing_index][0]]
        coords_for_relation.extend(obj["coords"].tolist())
    for py, px in coords_for_relation:
        rd.point((px, py), fill=color)
    if coords_for_relation:
        arr = np.asarray(coords_for_relation)
        mid = (int(np.median(arr[:, 1])), int(np.median(arr[:, 0])))
        rd.text((mid[0] + 6, mid[1] - 14), rid, fill=color)
    nonempty = sum(1 for i in drawing_indices if object_by_id[GRAPHICS[i][0]]["mask_pixel_count"] > 0)
    relation_rows.append({
        "relation_id": rid,
        "source": source,
        "target": target,
        "edge_type": edge_type,
        "drawing_indices": ";".join(map(str, drawing_indices)),
        "graphic_object_ids": ";".join(GRAPHICS[i][0] for i in drawing_indices),
        "expected_graphic_count": len(drawing_indices),
        "nonempty_graphic_count": nonempty,
        "machine_structure_status": "COMPLETE" if nonempty == len(drawing_indices) else "INCOMPLETE",
    })
write_csv(DIRS["relations"] / "seven_relations.csv", relation_rows)
relation_image.crop((body_x0, body_y0, body_x1, body_y1)).save(DIRS["relations"] / "seven_relations_overlay_300dpi.png", dpi=(300, 300))

# Source-level font inventory, derived only from the current whitelisted TeX.
source_rows = [
    {"source_role": "global_slfig_style", "declared_pt": 10.1, "graphics_scale": 1.0, "effective_pt": 10.1, "scope": "tikz global"},
    {"source_role": "every_node", "declared_pt": 10.1, "graphics_scale": 1.0, "effective_pt": 10.1, "scope": "all ordinary node labels"},
    {"source_role": "trial_count_formula", "declared_pt": 11.6, "graphics_scale": 1.0, "effective_pt": 11.6, "scope": "n"},
    {"source_role": "posterior_formula", "declared_pt": 11.6, "graphics_scale": 1.0, "effective_pt": 11.6, "scope": "parameters alpha+n"},
    {"source_role": "predictive_fraction", "declared_pt": 11.6, "graphics_scale": 1.0, "effective_pt": 11.6, "scope": "(alpha_i+n_i)/(alpha_0+N)"},
    {"source_role": "application_edge_label", "declared_pt": 10.1, "graphics_scale": 1.0, "effective_pt": 10.1, "scope": "application"},
]
write_csv(DIRS["machine"] / "source_font_audit.csv", source_rows)

# R168 records D/E micro-ratios as advisory only.  These tables are numeric;
# no script-authored visual harmony or reviewer decision fields are emitted.
for obj in glyph_objs:
    if obj["parent"].endswith("_formula") or obj["parent"] == "trial_formula":
        obj["role"] = "FORMULA"
    elif obj["parent"] == "R7_application_label":
        obj["role"] = "ANNOTATION"
    else:
        obj["role"] = "BASE"
    if obj["category"] == "CJK_FULL":
        obj["script_group"] = "CJK"
    elif obj["category"] == "LEGAL_NATURAL_SCRIPT":
        obj["script_group"] = "NATURAL_SCRIPT"
    elif obj["category"] == "MATH_BASE":
        obj["script_group"] = "MATH"
    else:
        obj["script_group"] = "LATIN"
role_groups = defaultdict(list)
for obj in glyph_objs:
    role_groups[(obj["role"], obj["script_group"])].append(obj["h_ink_px"])
role_medians = {k: float(np.median(v)) for k, v in role_groups.items()}
de_rows = []
for obj in glyph_objs:
    med = role_medians[(obj["role"], obj["script_group"])]
    base = role_medians.get(("BASE", obj["script_group"]))
    d_ratio = obj["h_ink_px"] / med if med else math.nan
    e_ratio = med / base if base else None
    de_rows.append({
        "object_id": obj["object_id"],
        "role": obj["role"],
        "script_group": obj["script_group"],
        "h_ink_px": obj["h_ink_px"],
        "role_script_median_px": round(med, 3),
        "D_element_over_role_median": round(d_ratio, 4),
        "D_R168_advisory_band": "WITHIN_0.92_1.08" if 0.92 <= d_ratio <= 1.08 else "OUTSIDE_ADVISORY_BAND",
        "E_role_over_base_median": round(e_ratio, 4) if e_ratio is not None else "N/A",
        "R168_disposition": "ADVISORY_ONLY",
    })
write_csv(DIRS["machine"] / "font_de_advisory.csv", de_rows)
font_role_rows = []
for (role, script), values in sorted(role_groups.items()):
    base = role_medians.get(("BASE", script))
    font_role_rows.append({
        "role": role,
        "script_group": script,
        "glyph_count": len(values),
        "minimum_h_ink_px": min(values),
        "median_h_ink_px": round(float(np.median(values)), 3),
        "maximum_h_ink_px": max(values),
        "median_over_base": round(role_medians[(role, script)] / base, 4) if base else "N/A",
        "R168_disposition": "ADVISORY_ONLY",
    })
write_csv(DIRS["machine"] / "font_role_summary.csv", font_role_rows)

source_text = SOURCE.read_text(encoding="utf-8")
source_checks = {
    "source_path": str(SOURCE),
    "source_sha256": sha256(SOURCE),
    "has_every_node_10_1pt": "every node/.style={font=\\fontsize{10.1pt}{12.2pt}\\selectfont" in source_text,
    "has_formula_11_6pt": source_text.count("\\fontsize{11.6pt}{13.8pt}\\selectfont") == 3,
    "has_graphics_scale_override": any(tok in source_text for tok in ["\\resizebox", "\\scalebox", "transform shape"]),
    "has_tiny_or_scriptstyle_override": any(tok in source_text for tok in ["\\tiny", "\\scriptsize", "\\scriptstyle"]),
    "declared_node_count": source_text.count("\\node[") + source_text.count("--node["),
    "declared_draw_edge_count": source_text.count("\\draw["),
}
(DIRS["machine"] / "source_checks.json").write_text(json.dumps(source_checks, ensure_ascii=False, indent=2), encoding="utf-8")

height_counts = Counter(o["threshold_eval"] for o in glyph_objs)
parent_counts = Counter(o["parent"] for o in glyph_objs)
type_counts = Counter(o["object_type"] for o in objects)
machine_summary = {
    "handoff_id": "A-R103-P654-SA3-FRESH-ISOLATED-20260825",
    "uid": "FIG-P654-01",
    "official_pdf": str(PDF),
    "physical_page": PAGE_NUMBER,
    "page_count": doc.page_count,
    "page_size_pt": [round(page.rect.width, 3), round(page.rect.height, 3)],
    "native_300dpi_grid_px": [page_w, page_h],
    "body_crop_pt": [float(v) for v in BODY_PT],
    "body_crop_px": [body_x0, body_y0, body_x1 - body_x0, body_y1 - body_y0],
    "figure_crop_pt": [float(v) for v in FIGURE_PT],
    "figure_crop_px": [*pt_to_px_rect(FIGURE_PT)[:2], pt_to_px_rect(FIGURE_PT)[2] - pt_to_px_rect(FIGURE_PT)[0], pt_to_px_rect(FIGURE_PT)[3] - pt_to_px_rect(FIGURE_PT)[1]],
    "pdf_size_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "glyph_count": len(glyph_objs),
    "graphic_count": len(graphic_objs),
    "math_rule_count": sum(o["object_type"] == "MATH_RULE" for o in graphic_objs),
    "total_object_count": len(objects),
    "object_type_counts": dict(type_counts),
    "glyph_parent_counts": dict(parent_counts),
    "pair_expected_count": expected_pairs,
    "pair_actual_count": len(pair_rows),
    "seven_relation_count": len(relation_rows),
    "empty_mask_count": sum(o["empty_mask_count"] for o in objects),
    "glyph_numeric_height_counts": dict(height_counts),
    "illegal_overlap_pair_count": len(illegal_pairs),
    "clearance_hard_failure_pair_count": len(clearance_failure_pairs),
    "machine_critical_pair_count": len(critical_pairs),
    "critical_roi_file_count": len(critical_rows),
    "clip_pixel_count": sum(int(np.count_nonzero((o["coords"][:, 0] <= body_y0) | (o["coords"][:, 0] >= body_y1 - 1) | (o["coords"][:, 1] <= body_x0) | (o["coords"][:, 1] >= body_x1 - 1))) for o in objects if len(o["coords"])),
    "glyph_contact_sheets": glyph_contact_paths,
    "graphic_contact_sheets": graphic_contact_paths,
    "minimum_text_to_body_edge_clearance_px": min(min(int(c[:, 0].min() - body_y0), int(body_y1 - 1 - c[:, 0].max()), int(c[:, 1].min() - body_x0), int(body_x1 - 1 - c[:, 1].max())) for c in [o["coords"] for o in glyph_objs if len(o["coords"])]),
    "machine_hard_gate_status": "PASS" if not illegal_pairs and not clearance_failure_pairs and all(o["mask_pixel_count"] > 0 for o in objects) and len(pair_rows) == expected_pairs and all(r["machine_structure_status"] == "COMPLETE" for r in relation_rows) else "FAIL",
    "manual_fields_generated_by_script": 0,
}
(DIRS["machine"] / "machine_summary.json").write_text(json.dumps(machine_summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(machine_summary, ensure_ascii=False, indent=2))
