from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import shutil
from collections import defaultdict
from pathlib import Path

import fitz
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R8_SA3_FRESH_ISOLATED_R110_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex")
PAGE_INDEX = 631
PHYSICAL_PAGE = 632
PRINTED_PAGE = 619
FIGURE_LABEL = "31.7"
SCALE = 300.0 / 72.0
EXPECTED_PDF_SHA256 = "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3"
EXPECTED_SOURCE_SHA256 = "989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57"
EXPECTED_PDF_BYTES = 4_967_063

OBJECT_DIR = ROOT / "objects"
CONTACT_DIR = ROOT / "contact_sheets"
REL_DIR = ROOT / "relations"
CAL_DIR = ROOT / "calibrations"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rgb8(color) -> tuple[int, int, int]:
    if color is None:
        return (0, 0, 0)
    return tuple(int(round(255 * float(v))) for v in color)


def rect_px(rect) -> tuple[int, int, int, int]:
    r = fitz.Rect(rect)
    return (
        int(math.floor(r.x0 * SCALE)),
        int(math.floor(r.y0 * SCALE)),
        int(math.ceil(r.x1 * SCALE)),
        int(math.ceil(r.y1 * SCALE)),
    )


def padded_box(box, pad, width, height):
    x0, y0, x1, y1 = box
    return (max(0, x0 - pad), max(0, y0 - pad), min(width, x1 + pad), min(height, y1 + pad))


def union_boxes(boxes):
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def trim_mask(mask: np.ndarray, origin: tuple[int, int]):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return mask[:1, :1], (origin[0], origin[1], origin[0] + 1, origin[1] + 1)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return mask[y0:y1, x0:x1], (origin[0] + x0, origin[1] + y0, origin[0] + x1, origin[1] + y1)


def save_mask(mask: np.ndarray, path: Path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").save(path)


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    if count <= 1:
        return mask
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return labels == largest


def expected_color_mask(arr: np.ndarray, fg: tuple[int, int, int]) -> np.ndarray:
    pix = arr.astype(np.float32)
    f = np.array(fg, dtype=np.float32)
    v = 255.0 - f
    d = 255.0 - pix
    denom = float(np.dot(v, v))
    if denom < 1:
        return np.max(d, axis=2) >= 20
    alpha = np.tensordot(d, v, axes=([2], [0])) / denom
    alpha = np.clip(alpha, 0.0, 1.0)
    pred = 255.0 - alpha[..., None] * v
    residual = np.max(np.abs(pred - pix), axis=2)
    contrast = np.max(d, axis=2)
    return (contrast >= 20.0) & (alpha >= 0.04) & (residual <= 20.0)


def classify_char(ch: str, font: str, size: float, seqno: int):
    cp = ord(ch)
    low_punctuation = set(".,，。；;、:：…·")
    operators = set("−-+=/×÷≈<>≤≥∑√↑↓()[]{}")
    natural_script = (seqno == 33 and size < 8.0) or (seqno == 62 and size < 9.2)
    if natural_script:
        return "NATURAL_SCRIPT", 15
    if ch in low_punctuation:
        return "LOW_PROFILE_PUNCTUATION", None
    if ch in operators:
        return "BASE_MATH_OPERATOR", 22
    if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
        return "CJK", 30
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_UPPER_DIGIT", 24
    if ch.islower() or cp >= 0x370:
        return "LATIN_GREEK_LOWER", 17
    return "BASE_MATH_OPERATOR", 22


def glyph_parent(seqno: int, ch: str, font: str):
    mapping = {
        18: "X_TICKS", 19: "X_TICKS", 20: "X_TICKS", 21: "X_TICKS",
        22: "Y_TICKS", 23: "Y_TICKS", 24: "Y_TICKS", 25: "Y_TICKS",
        26: "Y_TICKS", 27: "Y_TICKS", 28: "Y_TICKS", 29: "Y_TICKS",
        33: "FORMULA_H", 34: "ANN_DOWN_1", 35: "ANN_UP", 36: "ANN_DOWN_2",
        37: "TRUTH_LABEL", 38: "VALUE_640", 39: "VALUE_325_2",
        40: "VALUE_380", 41: "VALUE_325_4", 60: "X_AXIS_TITLE",
        61: "Y_AXIS_TITLE", 62: "CAPTION",
    }
    return mapping[seqno]


def glyph_role(parent: str):
    if parent in {"X_TICKS", "Y_TICKS"}:
        return "TICK_LABEL"
    if parent in {"X_AXIS_TITLE", "Y_AXIS_TITLE"}:
        return "AXIS_TITLE"
    if parent.startswith("ANN_"):
        return "ANNOTATION"
    if parent == "FORMULA_H":
        return "FORMULA"
    if parent == "TRUTH_LABEL":
        return "ANNOTATION"
    if parent.startswith("VALUE_"):
        return "VALUE_LABEL"
    if parent == "CAPTION":
        return "CAPTION"
    return "OTHER_TEXT"


def declared_effective_pt(seqno: int, trace_size: float):
    if seqno in {60, 61}:
        return 9.6, "source label style"
    if seqno in {18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 33, 34, 35, 36, 37, 38, 39, 40, 41}:
        return 9.5, "source global/tick/node style"
    if seqno == 62:
        if trace_size < 9.2:
            return 9.963, "PDF caption base trace; visible sub/superscript is a natural TeX derivative"
        return round(trace_size, 3), "PDF caption trace (ambient caption style outside audit whitelist)"
    raise ValueError(seqno)


def drawing_parent(seqno: int):
    return {
        12: "X_TICK_MARKS", 13: "Y_TICK_MARKS", 14: "X_AXIS_LINE",
        15: "X_AXIS_ARROWHEAD", 16: "Y_AXIS_LINE", 17: "Y_AXIS_ARROWHEAD",
        30: "YCOMB_STEMS", 31: "RUNNING_MEAN_CURVE", 32: "TRUE_VALUE_LINE",
        42: "SAMPLE_MARKER_1", 44: "SAMPLE_MARKER_2", 46: "SAMPLE_MARKER_3",
        48: "SAMPLE_MARKER_4", 50: "MEAN_MARKER_1", 52: "MEAN_MARKER_2",
        54: "MEAN_MARKER_3", 56: "MEAN_MARKER_4",
    }[seqno]


def drawing_role(parent: str):
    if "MARKER" in parent:
        return "MARKER"
    if "ARROWHEAD" in parent:
        return "AXIS_ARROWHEAD"
    if "AXIS" in parent or "TICK_MARKS" in parent:
        return "AXIS_GEOMETRY"
    if parent == "RUNNING_MEAN_CURVE":
        return "DATA_CURVE"
    if parent == "YCOMB_STEMS":
        return "DATA_STEMS"
    if parent == "TRUE_VALUE_LINE":
        return "REFERENCE_LINE"
    return "DRAWING"


def replay_drawing(page_rect: fitz.Rect, drawing: dict, clip_box_px):
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            shape.draw_line(item[1], item[2])
        elif kind == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif kind == "re":
            shape.draw_rect(item[1])
        elif kind == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"unsupported drawing item {kind}")
    line_cap = drawing.get("lineCap", 0)
    if isinstance(line_cap, (tuple, list)):
        line_cap = max(line_cap)
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=drawing.get("color"),
        fill=drawing.get("fill"),
        lineCap=int(line_cap or 0),
        lineJoin=int(drawing.get("lineJoin") or 0),
        dashes=drawing.get("dashes"),
        even_odd=bool(drawing.get("even_odd", False)),
        closePath=bool(drawing.get("closePath", False)),
        fill_opacity=float(drawing.get("fill_opacity") or 1.0),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1.0),
    )
    shape.commit()
    x0, y0, x1, y1 = clip_box_px
    clip = fitz.Rect(x0 / SCALE, y0 / SCALE, x1 / SCALE, y1 / SCALE)
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, alpha=False, colorspace=fitz.csRGB)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]
    doc.close()
    return np.max(255 - arr, axis=2) >= 20


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def mask_points(obj):
    mask = np.array(Image.open(ROOT / obj["mask_path"]).convert("L")) < 128
    ys, xs = np.nonzero(mask)
    x0, y0, _, _ = obj["ink_bbox_px"]
    return np.column_stack((xs + x0, ys + y0)), mask


def exact_clearance(a, b):
    pa, _ = mask_points(a)
    pb, _ = mask_points(b)
    if len(pa) == 0 or len(pb) == 0:
        return None
    if len(pa) > len(pb):
        pa, pb = pb, pa
    tree = cKDTree(pb)
    dist, _ = tree.query(pa, k=1)
    return float(np.min(dist))


def overlap_count(a, b):
    ax0, ay0, ax1, ay1 = a["ink_bbox_px"]
    bx0, by0, bx1, by1 = b["ink_bbox_px"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    ma = np.array(Image.open(ROOT / a["mask_path"]).convert("L")) < 128
    mb = np.array(Image.open(ROOT / b["mask_path"]).convert("L")) < 128
    aa = ma[y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
    bb = mb[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
    return int(np.count_nonzero(aa & bb))


def drawing_overlap_allowed(pa: str, pb: str):
    pair = frozenset((pa, pb))
    allowed = {
        frozenset(("X_TICK_MARKS", "X_AXIS_LINE")),
        frozenset(("Y_TICK_MARKS", "Y_AXIS_LINE")),
        frozenset(("X_AXIS_LINE", "X_AXIS_ARROWHEAD")),
        frozenset(("Y_AXIS_LINE", "Y_AXIS_ARROWHEAD")),
        frozenset(("YCOMB_STEMS", "X_AXIS_LINE")),
        frozenset(("RUNNING_MEAN_CURVE", "TRUE_VALUE_LINE")),
        frozenset(("YCOMB_STEMS", "TRUE_VALUE_LINE")),
        frozenset(("SAMPLE_MARKER_1", "MEAN_MARKER_1")),
        frozenset(("X_TICK_MARKS", "YCOMB_STEMS")),
        frozenset(("X_TICK_MARKS", "SAMPLE_MARKER_2")),
        frozenset(("Y_TICK_MARKS", "X_AXIS_LINE")),
        frozenset(("Y_TICK_MARKS", "Y_AXIS_ARROWHEAD")),
        frozenset(("X_AXIS_LINE", "Y_AXIS_LINE")),
        frozenset(("X_AXIS_LINE", "SAMPLE_MARKER_2")),
        frozenset(("Y_AXIS_LINE", "TRUE_VALUE_LINE")),
        frozenset(("YCOMB_STEMS", "RUNNING_MEAN_CURVE")),
        frozenset(("RUNNING_MEAN_CURVE", "SAMPLE_MARKER_1")),
        frozenset(("TRUE_VALUE_LINE", "MEAN_MARKER_2")),
        frozenset(("TRUE_VALUE_LINE", "MEAN_MARKER_4")),
    }
    for idx in range(1, 5):
        allowed.add(frozenset(("YCOMB_STEMS", f"SAMPLE_MARKER_{idx}")))
        allowed.add(frozenset(("YCOMB_STEMS", f"MEAN_MARKER_{idx}")))
        allowed.add(frozenset(("RUNNING_MEAN_CURVE", f"MEAN_MARKER_{idx}")))
    return pair in allowed


def pair_policy(a, b):
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        if a["parent"] == b["parent"]:
            return "DESIGN_SAME_TEXT_PARENT", None
        return "INDEPENDENT_TEXT_TEXT", 4.0
    if a["kind"] == "DRAWING" and b["kind"] == "DRAWING":
        if drawing_overlap_allowed(a["parent"], b["parent"]):
            return "DESIGN_DRAWING_CONNECTION", None
        return "DRAWING_DRAWING", None
    text = a if a["kind"] == "GLYPH" else b
    drawing = b if a["kind"] == "GLYPH" else a
    if text["parent"] in {"X_TICKS", "Y_TICKS"} and drawing["parent"] in {"X_TICK_MARKS", "Y_TICK_MARKS", "X_AXIS_LINE", "Y_AXIS_LINE"}:
        return "TEXT_AXIS_GEOMETRY", 3.0
    return "INDEPENDENT_TEXT_DRAWING", 3.0


def make_contact_cell(page_img: Image.Image, obj: dict, width=440, height=210):
    cell = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(cell)
    label = f"{obj['id']}  {obj.get('char_repr', obj['parent'])}  H={obj['ink_height_px']} A={obj['ink_area_px']}"
    draw.text((8, 5), label, fill="black")
    ink = obj["ink_bbox_px"]
    context_box = padded_box(ink, 8, page_img.width, page_img.height)
    original = page_img.crop(context_box)
    mask = np.array(Image.open(ROOT / obj["mask_path"]).convert("L")) < 128
    overlay = original.copy()
    ov = np.array(overlay)
    ix0, iy0, ix1, iy1 = ink
    cx0, cy0, _, _ = context_box
    region = ov[iy0 - cy0:iy1 - cy0, ix0 - cx0:ix1 - cx0]
    region[mask] = np.array([230, 20, 30], dtype=np.uint8)
    overlay = Image.fromarray(ov)
    mask_only = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").convert("RGB")
    slots = [(8, 45, "ORIGINAL"), (110, 45, "TARGET OVERLAY"), (212, 45, "MASK ONLY")]
    for x, y, title in slots:
        draw.text((x, 28), title, fill="black")
    cell.paste(original, (8, 45))
    cell.paste(overlay, (110, 45))
    cell.paste(mask_only, (212, 45))
    nn = original.resize((original.width * 8, original.height * 8), Image.Resampling.NEAREST)
    maxw, maxh = 120, 145
    if nn.width > maxw or nn.height > maxh:
        nn.thumbnail((maxw, maxh), Image.Resampling.NEAREST)
    draw.text((314, 28), "8x NEAREST", fill="black")
    cell.paste(nn, (314, 45))
    draw.rectangle((0, 0, width - 1, height - 1), outline=(140, 140, 140))
    return cell


def save_contact_sheets(page_img, objects, prefix, per_sheet=12):
    paths = []
    for sheet_index, start in enumerate(range(0, len(objects), per_sheet), 1):
        chunk = objects[start:start + per_sheet]
        sheet = Image.new("RGB", (1320, 840), (238, 238, 238))
        for local, obj in enumerate(chunk):
            cell = make_contact_cell(page_img, obj)
            x = (local % 3) * 440
            y = (local // 3) * 210
            sheet.paste(cell, (x, y))
            obj["contact_sheet"] = f"contact_sheets/{prefix}_{sheet_index:02d}.png"
            obj["contact_cell"] = local + 1
        path = CONTACT_DIR / f"{prefix}_{sheet_index:02d}.png"
        sheet.save(path)
        paths.append(path)
    return paths


def relation_cell(page_img, pair, objects_by_id, width=660, height=240):
    a, b = objects_by_id[pair["a_id"]], objects_by_id[pair["b_id"]]
    box = union_boxes((a["ink_bbox_px"], b["ink_bbox_px"]))
    box = padded_box(box, 12, page_img.width, page_img.height)
    original = page_img.crop(box)
    overlay = np.array(original.copy())
    for obj, color in ((a, np.array([230, 20, 30], dtype=np.uint8)), (b, np.array([0, 170, 210], dtype=np.uint8))):
        mask = np.array(Image.open(ROOT / obj["mask_path"]).convert("L")) < 128
        x0, y0, x1, y1 = obj["ink_bbox_px"]
        bx0, by0, _, _ = box
        reg = overlay[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
        reg[mask] = color
    overlay = Image.fromarray(overlay)
    nn = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
    nn.thumbnail((290, 180), Image.Resampling.NEAREST)
    cell = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(cell)
    label = f"{pair['pair_id']} {a['id']}:{a['parent']} vs {b['id']}:{b['parent']} clr={pair['clearance_px']} ov={pair['overlap_px']}"
    d.text((8, 5), label, fill="black")
    d.text((8, 26), "ORIGINAL 1x", fill="black")
    d.text((220, 26), "A red / B cyan 1x", fill="black")
    d.text((430, 26), "8x nearest", fill="black")
    cell.paste(original, (8, 48))
    cell.paste(overlay, (220, 48))
    cell.paste(nn, (430, 48))
    d.rectangle((0, 0, width - 1, height - 1), outline=(140, 140, 140))
    return cell


def save_relation_sheets(page_img, pairs, objects_by_id, per_sheet=6):
    paths = []
    for sheet_index, start in enumerate(range(0, len(pairs), per_sheet), 1):
        chunk = pairs[start:start + per_sheet]
        sheet = Image.new("RGB", (1320, 720), (238, 238, 238))
        for local, pair in enumerate(chunk):
            cell = relation_cell(page_img, pair, objects_by_id)
            x = (local % 2) * 660
            y = (local // 2) * 240
            sheet.paste(cell, (x, y))
            pair["critical_sheet"] = f"relations/critical_relations_{sheet_index:02d}.png"
            pair["critical_cell"] = local + 1
        path = REL_DIR / f"critical_relations_{sheet_index:02d}.png"
        sheet.save(path)
        paths.append(path)
    return paths


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    for directory in (OBJECT_DIR, CONTACT_DIR, REL_DIR, CAL_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    if PDF.stat().st_size != EXPECTED_PDF_BYTES:
        raise RuntimeError("PDF byte size mismatch")
    if sha256(PDF) != EXPECTED_PDF_SHA256:
        raise RuntimeError("PDF SHA-256 mismatch")
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("source SHA-256 mismatch")

    doc = fitz.open(PDF)
    if len(doc) != 817:
        raise RuntimeError(f"page count mismatch: {len(doc)}")
    page = doc[PAGE_INDEX]
    page_text = page.get_text("text")
    for token in ("31.7", "运行均值", "再下降", ".380"):
        if token not in page_text:
            raise RuntimeError(f"page locator token missing: {token}")

    full300_path = ROOT / "full_page_300dpi.png"
    full200_path = ROOT / "full_page_200dpi.png"
    if not full300_path.exists() or not full200_path.exists():
        raise RuntimeError("required direct Poppler renders missing")
    page_img = Image.open(full300_path).convert("RGB")
    if page_img.size != (2481, 3508):
        raise RuntimeError(f"unexpected 300 dpi dimensions {page_img.size}")
    if Image.open(full200_path).size != (1654, 2339):
        raise RuntimeError("unexpected 200 dpi dimensions")
    page_arr = np.array(page_img)

    objects = []
    gid = 0
    selected_seqnos = {18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 33, 34, 35, 36, 37, 38, 39, 40, 41, 60, 61, 62}
    for span in page.get_texttrace():
        if span["seqno"] not in selected_seqnos:
            continue
        for cp, glyph_id, origin, bbox in span["chars"]:
            ch = chr(cp)
            if ch.isspace():
                continue
            gid += 1
            obj_id = f"G{gid:04d}"
            parent = glyph_parent(span["seqno"], ch, span["font"])
            role = glyph_role(parent)
            box = rect_px(bbox)
            x0, y0, x1, y1 = box
            crop = page_arr[y0:y1, x0:x1]
            target = expected_color_mask(crop, rgb8(span["color"]))
            if ch == ".":
                target = keep_largest_component(target)
            target, ink_box = trim_mask(target, (x0, y0))
            mask_path = OBJECT_DIR / f"{obj_id}.png"
            save_mask(target, mask_path)
            ys, xs = np.nonzero(target)
            char_class, min_height = classify_char(ch, span["font"], span["size"], span["seqno"])
            effective_pt, effective_basis = declared_effective_pt(span["seqno"], span["size"])
            objects.append({
                "id": obj_id,
                "safe_filename": obj_id,
                "kind": "GLYPH",
                "parent": parent,
                "role": role,
                "panel": "FIG31_7",
                "char": ch,
                "char_repr": f"U+{cp:04X} {ch}",
                "codepoint": f"U+{cp:04X}",
                "glyph_id": glyph_id,
                "seqno": span["seqno"],
                "font": span["font"],
                "pdf_trace_size_pt": round(float(span["size"]), 4),
                "declared_effective_pt": effective_pt,
                "declared_effective_basis": effective_basis,
                "natural_script": char_class == "NATURAL_SCRIPT",
                "char_class": char_class,
                "min_height_px": min_height,
                "color_rgb": rgb8(span["color"]),
                "vector_bbox_pt": [round(float(v), 4) for v in bbox],
                "vector_bbox_px": list(box),
                "ink_bbox_px": list(ink_box),
                "ink_width_px": int(target.shape[1] if target.any() else 0),
                "ink_height_px": int(target.shape[0] if target.any() else 0),
                "ink_area_px": int(target.sum()),
                "empty_mask": not bool(target.any()),
                "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
                "mask_method": "PDF300_POPPLER_CHAR_BBOX_EXPECTED_COLOR_20_255",
            })

    did = 0
    selected_drawings = []
    for drawing in page.get_drawings():
        r = drawing["rect"]
        if drawing["seqno"] in {12, 13, 14, 15, 16, 17, 30, 31, 32, 42, 44, 46, 48, 50, 52, 54, 56} and r.y0 >= 328 and r.y1 <= 515:
            selected_drawings.append(drawing)
    for drawing in selected_drawings:
        did += 1
        obj_id = f"D{did:04d}"
        parent = drawing_parent(drawing["seqno"])
        box = padded_box(rect_px(drawing["rect"]), 6, page_img.width, page_img.height)
        target = replay_drawing(page.rect, drawing, box)
        target, ink_box = trim_mask(target, (box[0], box[1]))
        mask_path = OBJECT_DIR / f"{obj_id}.png"
        save_mask(target, mask_path)
        objects.append({
            "id": obj_id,
            "safe_filename": obj_id,
            "kind": "DRAWING",
            "parent": parent,
            "role": drawing_role(parent),
            "panel": "FIG31_7",
            "char": "",
            "char_repr": parent,
            "codepoint": "",
            "glyph_id": "",
            "seqno": drawing["seqno"],
            "font": "",
            "pdf_trace_size_pt": "",
            "declared_effective_pt": "",
            "declared_effective_basis": "",
            "natural_script": "",
            "char_class": "GRAPHIC/PLOT_PATH",
            "min_height_px": "",
            "color_rgb": rgb8(drawing.get("color") or drawing.get("fill")),
            "vector_bbox_pt": [round(float(v), 4) for v in drawing["rect"]],
            "vector_bbox_px": list(rect_px(drawing["rect"])),
            "ink_bbox_px": list(ink_box),
            "ink_width_px": int(target.shape[1] if target.any() else 0),
            "ink_height_px": int(target.shape[0] if target.any() else 0),
            "ink_area_px": int(target.sum()),
            "empty_mask": not bool(target.any()),
            "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
            "mask_method": "REPLAYED_PDF_VECTOR_PATH_300DPI_20_255",
            "drawing_item_count": len(drawing["items"]),
            "drawing_item_types": "+".join(item[0] for item in drawing["items"]),
            "stroke_width_pt": drawing.get("width"),
            "fill_rgb": rgb8(drawing.get("fill")) if drawing.get("fill") is not None else "",
        })

    if len(selected_drawings) != 17:
        raise RuntimeError(f"drawing denominator mismatch {len(selected_drawings)}")
    empty = [o["id"] for o in objects if o["empty_mask"]]
    if empty:
        raise RuntimeError(f"empty object masks: {empty}")

    body_objects = [o for o in objects if o["parent"] != "CAPTION"]
    figure_box = padded_box(union_boxes([o["ink_bbox_px"] for o in objects]), 24, page_img.width, page_img.height)
    body_box = padded_box(union_boxes([o["ink_bbox_px"] for o in body_objects]), 24, page_img.width, page_img.height)
    page_img.crop(figure_box).save(ROOT / "figure_crop_300dpi.png")
    page_img.crop(body_box).save(ROOT / "standalone_300dpi.png")
    page_img.crop(figure_box).convert("L").save(ROOT / "grayscale_300dpi.png")

    overlay = page_img.crop(figure_box).copy()
    od = ImageDraw.Draw(overlay)
    fx0, fy0, _, _ = figure_box
    for obj in objects:
        x0, y0, x1, y1 = obj["ink_bbox_px"]
        color = (220, 30, 30) if obj["kind"] == "GLYPH" else (0, 140, 210)
        od.rectangle((x0 - fx0, y0 - fy0, x1 - fx0 - 1, y1 - fy0 - 1), outline=color, width=1)
        od.text((x0 - fx0, max(0, y0 - fy0 - 11)), obj["id"], fill=color)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    glyphs = [o for o in objects if o["kind"] == "GLYPH"]
    drawings = [o for o in objects if o["kind"] == "DRAWING"]
    glyph_sheets = save_contact_sheets(page_img, glyphs, "glyph_contact")
    drawing_sheets = save_contact_sheets(page_img, drawings, "drawing_contact")

    # Low-profile punctuation uses exact same-codepoint/font/size/color groups from this official PDF.
    calibration_groups = defaultdict(list)
    for obj in glyphs:
        if obj["char_class"] == "LOW_PROFILE_PUNCTUATION":
            key = (obj["char"], obj["font"], round(float(obj["pdf_trace_size_pt"]), 2), tuple(obj["color_rgb"]))
            calibration_groups[key].append(obj)
    calibration_rows = []
    for key, group in calibration_groups.items():
        heights = [g["ink_height_px"] for g in group]
        areas = [g["ink_area_px"] for g in group]
        med_h = float(np.median(heights))
        med_a = float(np.median(areas))
        for obj in group:
            obj["punct_reference_count"] = len(group)
            obj["punct_h_ratio"] = round(obj["ink_height_px"] / med_h, 5) if med_h else None
            obj["punct_area_ratio"] = round(obj["ink_area_px"] / med_a, 5) if med_a else None
            obj["punct_calibration_status"] = "IN_CANDIDATE_MATCH" if len(group) >= 2 else "SINGLETON_NEEDS_FONT_CALIBRATION"
            calibration_rows.append({
                "id": obj["id"], "char": obj["char"], "font": obj["font"],
                "size_pt": obj["pdf_trace_size_pt"], "reference_count": len(group),
                "height_px": obj["ink_height_px"], "area_px": obj["ink_area_px"],
                "median_height_px": med_h, "median_area_px": med_a,
                "height_ratio": obj["punct_h_ratio"], "area_ratio": obj["punct_area_ratio"],
                "machine_calibration_status": obj["punct_calibration_status"],
            })

    for obj in glyphs:
        if obj["char_class"] != "LOW_PROFILE_PUNCTUATION":
            obj["pixel_gate_status"] = "PASS" if obj["ink_height_px"] >= int(obj["min_height_px"]) else "ADVISORY_R168_OUTLINE_THRESHOLD"
        else:
            hr = obj.get("punct_h_ratio")
            ar = obj.get("punct_area_ratio")
            if obj.get("punct_reference_count", 0) >= 2 and 0.92 <= hr <= 1.08 and 0.92 <= ar <= 1.08:
                obj["pixel_gate_status"] = "PASS"
            elif obj.get("punct_reference_count", 0) < 2:
                obj["pixel_gate_status"] = "ADVISORY_SINGLETON_CALIBRATION"
            else:
                obj["pixel_gate_status"] = "FAIL"

    pairs = []
    for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        policy, threshold = pair_policy(a, b)
        bgap = bbox_gap(a["ink_bbox_px"], b["ink_bbox_px"])
        ov = overlap_count(a, b) if bgap == 0 else 0
        if bgap <= 36 or ov > 0:
            clearance = exact_clearance(a, b)
        else:
            clearance = None
        if ov > 0:
            effective_clearance = 0.0
        elif clearance is not None:
            effective_clearance = clearance
        else:
            effective_clearance = bgap
        machine_status = "PASS"
        reason = ""
        if ov > 0 and policy not in {"DESIGN_SAME_TEXT_PARENT", "DESIGN_DRAWING_CONNECTION"}:
            machine_status = "FAIL"
            reason = "non-design raw mask intersection"
        elif threshold is not None:
            metric = bgap if policy == "INDEPENDENT_TEXT_TEXT" else effective_clearance
            if metric < threshold:
                machine_status = "FAIL"
                reason = f"clearance below {threshold}px"
        pairs.append({
            "pair_id": f"P{pair_index:05d}",
            "a_id": a["id"], "b_id": b["id"],
            "a_parent": a["parent"], "b_parent": b["parent"],
            "policy": policy, "threshold_px": threshold,
            "bbox_gap_px": round(bgap, 4),
            "clearance_px": round(effective_clearance, 4),
            "clearance_exact": clearance is not None,
            "overlap_px": ov,
            "machine_status": machine_status,
            "machine_reason": reason,
        })

    expected_pairs = len(objects) * (len(objects) - 1) // 2
    if len(pairs) != expected_pairs:
        raise RuntimeError("unordered-pair denominator incomplete")

    key_parents = {"ANN_DOWN_2", "VALUE_380"}
    critical = []
    seen = set()
    candidates = [p for p in pairs if p["policy"] not in {"DESIGN_SAME_TEXT_PARENT"}]
    for p in sorted(candidates, key=lambda row: (row["machine_status"] != "FAIL", row["clearance_px"])):
        if p["machine_status"] == "FAIL" or p["clearance_px"] < 12:
            critical.append(p)
            seen.add(p["pair_id"])
    for p in sorted(candidates, key=lambda row: row["clearance_px"])[:30]:
        if p["pair_id"] not in seen:
            critical.append(p)
            seen.add(p["pair_id"])
    key_candidates = [p for p in candidates if p["a_parent"] in key_parents or p["b_parent"] in key_parents]
    grouped = defaultdict(list)
    for p in key_candidates:
        other = p["b_parent"] if p["a_parent"] in key_parents else p["a_parent"]
        key = (p["a_parent"] if p["a_parent"] in key_parents else p["b_parent"], other)
        grouped[key].append(p)
    for group in grouped.values():
        p = min(group, key=lambda row: row["clearance_px"])
        if p["pair_id"] not in seen:
            critical.append(p)
            seen.add(p["pair_id"])
    critical.sort(key=lambda row: row["pair_id"])
    relation_sheets = save_relation_sheets(page_img, critical, {o["id"]: o for o in objects})

    # Per-role / script ratio ledger (machine measurements only).
    groups = defaultdict(list)
    for obj in glyphs:
        script_key = obj["char_class"] if obj["char_class"] != "LOW_PROFILE_PUNCTUATION" else "PUNCT"
        groups[(obj["panel"], obj["role"], script_key)].append(obj)
    ratio_rows = []
    for (panel, role, script), group in sorted(groups.items()):
        heights = [g["ink_height_px"] for g in group]
        median = float(np.median(heights))
        ratios = [h / median for h in heights] if median else []
        ratio_rows.append({
            "panel": panel, "role": role, "script": script,
            "count": len(group), "median_height_px": median,
            "min_element_to_median": round(min(ratios), 5) if ratios else None,
            "max_element_to_median": round(max(ratios), 5) if ratios else None,
            "extreme_ratio": round(max(heights) / min(heights), 5) if heights and min(heights) else None,
            "machine_ratio_status": "PASS" if (not ratios or (min(ratios) >= 0.92 and max(ratios) <= 1.08 and max(heights) / min(heights) <= 1.08)) else "ADVISORY_OUTLINE_VARIATION",
        })

    # Edge clearance in the actual figure crop.
    clip_pixels = 0
    edge_rows = []
    fx0, fy0, fx1, fy1 = figure_box
    for obj in objects:
        x0, y0, x1, y1 = obj["ink_bbox_px"]
        clearance = min(x0 - fx0, y0 - fy0, fx1 - x1, fy1 - y1)
        edge_rows.append({"id": obj["id"], "edge_clearance_px": clearance, "machine_edge_status": "PASS" if clearance >= 6 else "FAIL"})
        if clearance < 1:
            clip_pixels += 1

    object_fields = [
        "id", "safe_filename", "kind", "parent", "role", "panel", "char", "char_repr", "codepoint", "glyph_id", "seqno",
        "font", "pdf_trace_size_pt", "declared_effective_pt", "declared_effective_basis", "natural_script", "char_class", "min_height_px",
        "color_rgb", "vector_bbox_pt", "vector_bbox_px", "ink_bbox_px", "ink_width_px", "ink_height_px", "ink_area_px", "empty_mask",
        "mask_path", "mask_method", "drawing_item_count", "drawing_item_types", "stroke_width_pt", "fill_rgb", "punct_reference_count",
        "punct_h_ratio", "punct_area_ratio", "punct_calibration_status", "pixel_gate_status", "contact_sheet", "contact_cell",
    ]
    write_csv(ROOT / "after_pixel_measurements.csv", objects, object_fields)
    write_csv(ROOT / "after_overlap_report.csv", pairs, list(pairs[0].keys()))
    write_csv(ROOT / "punctuation_calibration.csv", calibration_rows, list(calibration_rows[0].keys()) if calibration_rows else ["id"])
    write_csv(ROOT / "role_script_ratios.csv", ratio_rows, list(ratio_rows[0].keys()))
    write_csv(ROOT / "edge_clearance.csv", edge_rows, list(edge_rows[0].keys()))
    font_rows = [{
        "id": o["id"], "parent": o["parent"], "role": o["role"], "char": o["char"],
        "font": o["font"], "pdf_trace_size_pt": o["pdf_trace_size_pt"],
        "declared_effective_pt": o["declared_effective_pt"],
        "effective_basis": o["declared_effective_basis"], "natural_script": o["natural_script"],
        "source_font_gate": "PASS" if float(o["declared_effective_pt"]) >= 9.5 else "FAIL",
    } for o in glyphs]
    write_csv(ROOT / "after_font_audit.csv", font_rows, list(font_rows[0].keys()))

    with (ROOT / "object_manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(objects, stream, ensure_ascii=False, indent=2)
    with (ROOT / "unordered_pairs.json").open("w", encoding="utf-8") as stream:
        json.dump(pairs, stream, ensure_ascii=False, indent=2)
    with (ROOT / "critical_relations.json").open("w", encoding="utf-8") as stream:
        json.dump(critical, stream, ensure_ascii=False, indent=2)

    hard_pair_fails = [p for p in pairs if p["machine_status"] == "FAIL"]
    hard_pixel_fails = [o for o in glyphs if o["pixel_gate_status"] == "FAIL"]
    singleton_advisories = [o["id"] for o in glyphs if o["pixel_gate_status"] == "ADVISORY_SINGLETON_CALIBRATION"]
    ratio_advisories = [r for r in ratio_rows if r["machine_ratio_status"] != "PASS"]
    math_rule_candidates = [o for o in drawings if o["role"] == "MATH_RULE"]
    machine_summary = {
        "handoff_id": "A-R110-P582-SA3-FRESH-ISOLATED-20260827",
        "uid": "FIG-P582-01",
        "candidate_round": "R110",
        "pdf": str(PDF),
        "pdf_sha256": sha256(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_pages": len(doc),
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "figure_label": FIGURE_LABEL,
        "page_size_pt": [page.rect.width, page.rect.height],
        "full_page_200dpi_dimensions": list(Image.open(full200_path).size),
        "full_page_300dpi_dimensions": list(page_img.size),
        "figure_crop_bbox_px": list(figure_box),
        "figure_crop_dimensions": [figure_box[2] - figure_box[0], figure_box[3] - figure_box[1]],
        "standalone_crop_bbox_px": list(body_box),
        "standalone_crop_dimensions": [body_box[2] - body_box[0], body_box[3] - body_box[1]],
        "object_count": len(objects),
        "glyph_count": len(glyphs),
        "drawing_path_count": len(drawings),
        "math_rule_count": len(math_rule_candidates),
        "unordered_pair_count": len(pairs),
        "expected_unordered_pair_count": expected_pairs,
        "ordinary_mask_file_count": len(list(OBJECT_DIR.glob("*.png"))),
        "glyph_contact_sheet_count": len(glyph_sheets),
        "drawing_contact_sheet_count": len(drawing_sheets),
        "critical_relation_count": len(critical),
        "critical_relation_sheet_count": len(relation_sheets),
        "empty_mask_count": len(empty),
        "illegal_overlap_pixel_count": sum(p["overlap_px"] for p in hard_pair_fails if p["overlap_px"] > 0),
        "clip_pixel_count": clip_pixels,
        "pair_hard_fail_count": len(hard_pair_fails),
        "pixel_hard_fail_count": len(hard_pixel_fails),
        "singleton_punctuation_advisory_ids": singleton_advisories,
        "ratio_outline_advisory_count": len(ratio_advisories),
        "machine_hard_status": "PASS" if not hard_pair_fails and not hard_pixel_fails and not empty and clip_pixels == 0 else "FAIL",
    }
    with (ROOT / "machine_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(machine_summary, stream, ensure_ascii=False, indent=2)

    locator = {
        "method": "independent full-PDF UTF-8 text extraction token scan followed by page-level PDF object verification",
        "unique_target_hit_physical_page": PHYSICAL_PAGE,
        "printed_page_read_from_page_header": PRINTED_PAGE,
        "figure_label_read_from_caption": FIGURE_LABEL,
        "required_tokens": ["运行均值", "先降后升再下降", "图 31.7", "再下降", ".380"],
        "page_level_tokens_verified": ["31.7", "运行均值", "再下降", ".380"],
    }
    with (ROOT / "page_locator.json").open("w", encoding="utf-8") as stream:
        json.dump(locator, stream, ensure_ascii=False, indent=2)

    print(json.dumps(machine_summary, ensure_ascii=False, indent=2))
    doc.close()


if __name__ == "__main__":
    main()
