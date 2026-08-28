from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R18_SA1_FRESH_ISOLATED_R107_20260826")
MACHINE = ROOT / "machine"
RENDERS = ROOT / "renders"
REVIEW = ROOT / "review"
GLYPH_MASKS = MACHINE / "masks" / "glyph"
GRAPHIC_MASKS = MACHINE / "masks" / "graphic"
PAIR_NATIVE = REVIEW / "critical_pairs" / "native1x"
PAIR_8X = REVIEW / "critical_pairs" / "8x_nearest"

PDF_EXPECTED_SHA256 = "8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3"
PDF_EXPECTED_BYTES = 4_967_249
PDF_EXPECTED_PAGES = 817
SOURCE_EXPECTED_SHA256 = "900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87"
PHYSICAL_PAGE = 765
PAGE_INDEX = PHYSICAL_PAGE - 1
PRINTED_PAGE = 752
FIGURE_NUMBER = "36.2"
HANDOFF_ID = "A-R107-P715-SA1-FRESH-ISOLATED-20260826"
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
FIGURE_BODY_PT = fitz.Rect(68.0, 69.0, 516.0, 268.0)
FIGURE_CROP_PT = fitz.Rect(65.0, 66.0, 520.0, 290.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def bbox_to_px(rect: fitz.Rect, scale: float, width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, math.floor(rect.x0 * scale) - pad)
    y0 = max(0, math.floor(rect.y0 * scale) - pad)
    x1 = min(width, math.ceil(rect.x1 * scale) + pad)
    y1 = min(height, math.ceil(rect.y1 * scale) + pad)
    return x0, y0, x1, y1


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def classify_char(ch: str, size: float, role: str) -> tuple[str, int]:
    cp = ord(ch)
    cat = unicodedata.category(ch)
    if size < 9.49 and role in {"FORMULA", "MATRIX_ENTRY"}:
        return "NATURAL_SCRIPT", 15
    if ch in {".", ",", "，", "、", ":", ";", "：", "；", "·", "…"}:
        return "LOW_PROFILE_PUNCTUATION", 0
    if (0x3400 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF) or ch in {"（", "）", "《", "》"}:
        return "CJK_FULL_HEIGHT", 30
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_UPPER_OR_DIGIT", 24
    if ("a" <= ch <= "z") or (0x370 <= cp <= 0x3FF) or (0x1D400 <= cp <= 0x1D7FF):
        return "LATIN_GREEK_LOWER_OR_MATH_ALPHA", 17
    if cat.startswith("S") or ch in {"=", "+", "-", "−", ">", "<", "⟺", "→", "∑", "∣", "/"}:
        return "MATH_OPERATOR_OR_BASELINE", 22
    return "GENERAL_VISIBLE", 17


def semantic_parent_and_role(line_text: str, ch_bbox: fitz.Rect, bi: int, li: int) -> tuple[str, str, str]:
    cx = (ch_bbox.x0 + ch_bbox.x1) / 2
    cy = (ch_bbox.y0 + ch_bbox.y1) / 2
    panel = "LEFT" if cx < 302 else "RIGHT"
    compact = "".join(line_text.split())
    if cy < 90:
        role = "TITLE"
    elif 92 <= cx <= 190 and 104 <= cy <= 172:
        if compact in {"𝑖", "𝑗", "ℎ"}:
            role = "NODE_LABEL"
        elif "→" in compact:
            role = "EDGE_NOTE"
        else:
            role = "GRAPH_ANNOTATION"
    elif any(token in compact for token in ("=", ">", "⟺", "∑", "Pr", "ρ", "𝑝", "𝑋", "𝐴", "𝑀", "𝑃")):
        role = "FORMULA"
    elif (175 <= cy <= 232) and ((108 <= cx <= 171) or (218 <= cx <= 282) or (382 <= cx <= 445)):
        role = "MATRIX_ENTRY"
    else:
        role = "NOTE"
    parent = f"{panel}_B{bi:02d}_L{li:02d}_{role}"
    return parent, role, panel


def disambiguate_text_masks(objects: list[dict]) -> None:
    """Partition only pixels claimed by two PDF character boxes.

    This is a machine isolation step, not a reviewer verdict. Different baselines
    use the nearer baseline; same-line adjacent characters use the midpoint of
    their source origins. It prevents neighboring line descenders or adjacent
    italic boxes from being duplicated into two raw masks.
    """
    text_objects = [o for o in objects if o["kind"] == "TEXT"]
    for a, b in itertools.combinations(text_objects, 2):
        ax0, ay0, ax1, ay1 = a["bbox_px"]
        bx0, by0, bx1, by1 = b["bbox_px"]
        x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
        if x0 >= x1 or y0 >= y1:
            continue
        av = a["mask"][y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
        bv = b["mask"][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
        overlap = av & bv
        if not np.any(overlap):
            continue
        yy, xx = np.nonzero(overlap)
        gx = xx + x0
        gy = yy + y0
        if a["source_line_key"] == b["source_line_key"]:
            boundary = (a["origin_px"][0] + b["origin_px"][0]) / 2.0
            if a["origin_px"][0] <= b["origin_px"][0]:
                a_wins = gx < boundary
            else:
                a_wins = gx >= boundary
        else:
            boundary = (a["origin_px"][1] + b["origin_px"][1]) / 2.0
            if a["origin_px"][1] <= b["origin_px"][1]:
                a_wins = gy < boundary
            else:
                a_wins = gy >= boundary
        for k, keep_a in enumerate(a_wins):
            ly, lx = int(yy[k]), int(xx[k])
            if keep_a:
                bv[ly, lx] = False
            else:
                av[ly, lx] = False
    for obj in text_objects:
        labels, component_count = ndimage.label(obj["mask"], structure=np.ones((3, 3), dtype=np.uint8))
        if component_count:
            sizes = np.bincount(labels.ravel())[1:]
            ch = obj["char"]
            if obj["pixel_class"] == "CJK_FULL_HEIGHT":
                largest = int(sizes.max())
                minimum = max(2, int(math.ceil(largest * 0.03)))
                keep_labels = {idx + 1 for idx, size in enumerate(sizes) if int(size) >= minimum}
            else:
                expected_components = 3 if ch == "…" else (2 if ch in {"i", "j", "𝑖", "𝑗", "=", ":", "：", ";", "；"} else 1)
                order = np.argsort(sizes)[::-1][:expected_components]
                keep_labels = {int(idx) + 1 for idx in order if int(sizes[int(idx)]) >= 2}
            obj["mask"] = np.isin(labels, list(keep_labels))
        x0, y0, _, _ = obj["bbox_px"]
        obj["mask_bbox_px"] = list(mask_bbox(obj["mask"], x0, y0))
        yy, xx = np.nonzero(obj["mask"])
        obj["mask_pixel_count"] = int(obj["mask"].sum())
        obj["ink_height_px"] = int(yy.max() - yy.min() + 1) if len(yy) else 0
        obj["ink_width_px"] = int(xx.max() - xx.min() + 1) if len(xx) else 0
        obj["empty_mask"] = bool(obj["mask_pixel_count"] == 0)
        legacy_threshold = obj["legacy_threshold_px"]
        obj["legacy_threshold_status"] = (
            "CALIBRATION_REQUIRED"
            if obj["pixel_class"] == "LOW_PROFILE_PUNCTUATION"
            else ("ABOVE" if obj["ink_height_px"] >= legacy_threshold else "BELOW")
        )
        Image.fromarray((obj["mask"].astype(np.uint8) * 255), mode="L").save(GLYPH_MASKS / obj["safe_filename"])


def estimate_char_mask(crop: np.ndarray, expected_rgb: tuple[int, int, int]) -> tuple[np.ndarray, dict]:
    if crop.size == 0:
        return np.zeros(crop.shape[:2], dtype=bool), {"background_rgb": [255, 255, 255]}
    rgb = crop[..., :3].astype(np.float32)
    border = np.concatenate((rgb[0, :, :], rgb[-1, :, :], rgb[:, 0, :], rgb[:, -1, :]), axis=0)
    means = np.mean(border, axis=1)
    bright = border[means >= np.percentile(means, 55)]
    if bright.size == 0:
        bright = border
    bg = np.median(bright, axis=0)
    ink = np.array(expected_rgb, dtype=np.float32)
    direction = bg - ink
    denom = float(np.dot(direction, direction))
    if denom < 25:
        bg = np.array([255.0, 255.0, 255.0])
        direction = bg - ink
        denom = float(np.dot(direction, direction))
    t = np.sum((bg - rgb) * direction, axis=2) / max(denom, 1.0)
    projected = bg[None, None, :] - np.clip(t, 0.0, 1.0)[..., None] * direction[None, None, :]
    residual = np.sqrt(np.sum((rgb - projected) ** 2, axis=2))
    contrast = np.max(np.abs(rgb - bg[None, None, :]), axis=2)
    mask = (t > 0.045) & (contrast >= 20.0) & (residual <= 44.0)
    return mask, {
        "background_rgb": [round(float(v), 2) for v in bg],
        "expected_ink_rgb": list(expected_rgb),
        "contrast_threshold": 20,
        "residual_limit": 44,
    }


def replay_drawing_mask(page_rect: fitz.Rect, drawing: dict, scale: float, full_size: tuple[int, int], stroke_only: bool) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    temp = fitz.open()
    pg = temp.new_page(width=page_rect.width, height=page_rect.height)
    shape = pg.new_shape()
    for item in drawing["items"]:
        cmd = item[0]
        if cmd == "l":
            shape.draw_line(item[1], item[2])
        elif cmd == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif cmd == "re":
            shape.draw_rect(item[1])
        elif cmd == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing command {cmd!r} at seqno {drawing['seqno']}")
    fill = None if stroke_only else drawing.get("fill")
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=drawing.get("color"),
        fill=fill,
        dashes=drawing.get("dashes"),
        lineCap=int((drawing.get("lineCap") or (0,))[0]),
        lineJoin=int(drawing.get("lineJoin") or 0),
        closePath=bool(drawing.get("closePath")),
        even_odd=bool(drawing.get("even_odd")),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1.0),
        fill_opacity=float(drawing.get("fill_opacity") or 1.0),
    )
    shape.commit()
    pix = pg.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    mask_full = arr[..., 3] >= 8
    full_w, full_h = full_size
    bbox = bbox_to_px(drawing["rect"], scale, full_w, full_h, pad=3)
    x0, y0, x1, y1 = bbox
    result = mask_full[y0:y1, x0:x1].copy()
    temp.close()
    return result, bbox


def drawing_semantics(seqno: int) -> tuple[str, str, str]:
    mapping = {
        3: ("PANEL_BORDER", "LEFT_PANEL", "LEFT"),
        4: ("PANEL_BORDER", "RIGHT_PANEL", "RIGHT"),
        7: ("NODE_BORDER", "GRAPH_NODE_I", "LEFT"),
        10: ("NODE_BORDER", "GRAPH_NODE_J", "LEFT"),
        13: ("NODE_BORDER", "GRAPH_NODE_H", "LEFT"),
        16: ("EDGE_SHAFT", "EDGE_J_TO_I", "LEFT"),
        17: ("ARROWHEAD", "EDGE_J_TO_I", "LEFT"),
        20: ("EDGE_SHAFT", "EDGE_I_TO_J", "LEFT"),
        21: ("ARROWHEAD", "EDGE_I_TO_J", "LEFT"),
        24: ("EDGE_SHAFT", "EDGE_J_TO_H", "LEFT"),
        25: ("ARROWHEAD", "EDGE_J_TO_H", "LEFT"),
        27: ("EDGE_SHAFT", "EDGE_H_TO_I", "LEFT"),
        28: ("ARROWHEAD", "EDGE_H_TO_I", "LEFT"),
        53: ("FOCUS_BORDER", "MATRIX_A_FOCUS", "LEFT"),
        73: ("FOCUS_BORDER", "MATRIX_M_FOCUS", "LEFT"),
        97: ("FOCUS_BORDER", "MATRIX_P_FOCUS", "RIGHT"),
    }
    if seqno in mapping:
        return mapping[seqno]
    if 35 <= seqno <= 51 and seqno % 2 == 1:
        return "CELL_BORDER", f"MATRIX_A_CELL_{(seqno - 35) // 2 + 1:02d}", "LEFT"
    if 55 <= seqno <= 71 and seqno % 2 == 1:
        return "CELL_BORDER", f"MATRIX_M_CELL_{(seqno - 55) // 2 + 1:02d}", "LEFT"
    if 79 <= seqno <= 95 and seqno % 2 == 1:
        return "CELL_BORDER", f"MATRIX_P_CELL_{(seqno - 79) // 2 + 1:02d}", "RIGHT"
    return "FOREGROUND_PATH", f"DRAWING_SEQ_{seqno}", "LEFT" if seqno < 75 else "RIGHT"


def mask_bbox(mask: np.ndarray, x0: int, y0: int) -> tuple[int, int, int, int]:
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return x0, y0, x0, y0
    return x0 + int(xx.min()), y0 + int(yy.min()), x0 + int(xx.max()) + 1, y0 + int(yy.max()) + 1


def object_intersection(a: dict, b: dict) -> int:
    ax0, ay0, ax1, ay1 = a["mask_bbox_px"]
    bx0, by0, bx1, by1 = b["mask_bbox_px"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    am = a["mask"][y0 - a["bbox_px"][1]:y1 - a["bbox_px"][1], x0 - a["bbox_px"][0]:x1 - a["bbox_px"][0]]
    bm = b["mask"][y0 - b["bbox_px"][1]:y1 - b["bbox_px"][1], x0 - b["bbox_px"][0]:x1 - b["bbox_px"][0]]
    return int(np.count_nonzero(am & bm))


def bbox_gap(a: dict, b: dict) -> float:
    ax0, ay0, ax1, ay1 = a["mask_bbox_px"]
    bx0, by0, bx1, by1 = b["mask_bbox_px"]
    dx = max(ax0 - bx1, bx0 - ax1, 0)
    dy = max(ay0 - by1, by0 - ay1, 0)
    return math.hypot(dx, dy)


def coords_for(obj: dict) -> np.ndarray:
    if "coords" not in obj:
        yy, xx = np.nonzero(obj["mask"])
        obj["coords"] = np.column_stack((yy + obj["bbox_px"][1], xx + obj["bbox_px"][0])).astype(np.int32)
    return obj["coords"]


def exact_clearance(a: dict, b: dict) -> tuple[float, tuple[int, int], tuple[int, int]]:
    ca = coords_for(a)
    cb = coords_for(b)
    if len(ca) == 0 or len(cb) == 0:
        return math.inf, (0, 0), (0, 0)
    if len(ca) <= len(cb):
        tree = b.setdefault("tree", cKDTree(cb))
        dist, idx = tree.query(ca, k=1)
        k = int(np.argmin(dist))
        pa = ca[k]
        pb = cb[int(idx[k])]
    else:
        tree = a.setdefault("tree", cKDTree(ca))
        dist, idx = tree.query(cb, k=1)
        k = int(np.argmin(dist))
        pb = cb[k]
        pa = ca[int(idx[k])]
    clearance = max(0.0, float(dist[k]) - 1.0)
    return clearance, (int(pa[1]), int(pa[0])), (int(pb[1]), int(pb[0]))


def relation_for(a: dict, b: dict) -> tuple[str, int, str]:
    if a["kind"] == "TEXT" and b["kind"] == "TEXT":
        if a["semantic_parent"] == b["semantic_parent"]:
            return "DESIGN_INTERNAL_TEXT", 0, "same semantic text/formula parent"
        if a["panel"] != b["panel"]:
            return "CROSS_PANEL_READER_ELEMENTS", 8, "adjacent-panel reader elements"
        return "TEXT_TEXT", 4, "independent semantic text objects"
    if a["kind"] == "GRAPHIC" and b["kind"] == "GRAPHIC":
        if a["semantic_parent"] == b["semantic_parent"]:
            return "DESIGN_INTERNAL_GRAPHIC", 0, "same graph edge or same semantic graphic"
        if a["graphic_type"] == "CELL_BORDER" and b["graphic_type"] == "CELL_BORDER":
            return "DESIGN_MATRIX_GRID", 0, "matrix cell borders intentionally share grid edges"
        if "FOCUS_BORDER" in {a["graphic_type"], b["graphic_type"]} and "CELL_BORDER" in {a["graphic_type"], b["graphic_type"]}:
            return "DESIGN_FOCUS_ON_CELL", 0, "focus rectangle intentionally coincides with target cell border"
        return "GRAPHIC_GRAPHIC", 0, "graphic geometry; inspected for semantic correctness"
    text = a if a["kind"] == "TEXT" else b
    graphic = b if a["kind"] == "TEXT" else a
    gt = graphic["graphic_type"]
    cx = (text["mask_bbox_px"][0] + text["mask_bbox_px"][2]) / 2
    cy = (text["mask_bbox_px"][1] + text["mask_bbox_px"][3]) / 2
    gx0, gy0, gx1, gy1 = graphic["bbox_px"]
    inside = gx0 <= cx <= gx1 and gy0 <= cy <= gy1
    if gt == "PANEL_BORDER":
        return "TEXT_FORMULA_PANEL_BORDER", 6, "reader text to panel border"
    if gt in {"EDGE_SHAFT", "ARROWHEAD"}:
        return "TEXT_FORMULA_LINE_ARROW", 3, "reader text/formula to graph edge or arrowhead"
    if gt == "NODE_BORDER" and inside:
        return "NODE_TEXT_TO_BORDER", 5, "node label to final-visible node border"
    if gt in {"CELL_BORDER", "FOCUS_BORDER"} and inside:
        return "MATRIX_TEXT_TO_CELL_BORDER", 5, "matrix entry to cell/focus border"
    return "TEXT_GRAPHIC_OTHER", 0, "non-protocol-distant or non-owning graphic"


def render_pair_evidence(full: np.ndarray, a: dict, b: dict, pair_id: str, pa: tuple[int, int], pb: tuple[int, int]) -> tuple[str, str, tuple[int, int, int, int]]:
    cx = int(round((pa[0] + pb[0]) / 2))
    cy = int(round((pa[1] + pb[1]) / 2))
    x0, y0 = max(0, cx - 30), max(0, cy - 30)
    x1, y1 = min(full.shape[1], cx + 31), min(full.shape[0], cy + 31)
    original = full[y0:y1, x0:x1, :3].copy()
    ma = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    mb = np.zeros_like(ma)
    for target, obj in ((ma, a), (mb, b)):
        ox0, oy0, ox1, oy1 = obj["bbox_px"]
        ix0, iy0, ix1, iy1 = max(x0, ox0), max(y0, oy0), min(x1, ox1), min(y1, oy1)
        if ix0 < ix1 and iy0 < iy1:
            target[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = obj["mask"][iy0 - oy0:iy1 - oy0, ix0 - ox0:ix1 - ox0]
    overlay = original.astype(np.float32)
    overlay[ma] = 0.35 * overlay[ma] + 0.65 * np.array([255, 0, 0])
    overlay[mb] = 0.35 * overlay[mb] + 0.65 * np.array([0, 90, 255])
    overlay[ma & mb] = np.array([255, 0, 255])
    canvas = Image.new("RGB", ((x1 - x0) * 2, y1 - y0), "white")
    canvas.paste(Image.fromarray(original.astype(np.uint8)), (0, 0))
    canvas.paste(Image.fromarray(overlay.astype(np.uint8)), (x1 - x0, 0))
    npath = PAIR_NATIVE / f"{pair_id}_native1x.png"
    epath = PAIR_8X / f"{pair_id}_8x_nearest.png"
    canvas.save(npath)
    canvas.resize((canvas.width * 8, canvas.height * 8), Image.Resampling.NEAREST).save(epath)
    return str(npath.relative_to(ROOT)).replace("\\", "/"), str(epath.relative_to(ROOT)).replace("\\", "/"), (x0, y0, x1, y1)


def make_glyph_contact_sheets(full: np.ndarray, objects: list[dict]) -> list[dict]:
    glyphs = [o for o in objects if o["kind"] == "TEXT"]
    font = ImageFont.load_default()
    sheets = []
    per_sheet = 12
    for sheet_idx in range(math.ceil(len(glyphs) / per_sheet)):
        chunk = glyphs[sheet_idx * per_sheet:(sheet_idx + 1) * per_sheet]
        cells = []
        for obj in chunk:
            x0, y0, x1, y1 = obj["bbox_px"]
            original = full[y0:y1, x0:x1, :3].copy()
            mask = obj["mask"]
            overlay = original.astype(np.float32)
            overlay[mask] = 0.30 * overlay[mask] + 0.70 * np.array([255, 0, 0])
            only = np.full_like(original, 255)
            only[mask] = np.array([0, 0, 0])
            trip = Image.new("RGB", ((x1 - x0) * 3, y1 - y0), "white")
            trip.paste(Image.fromarray(original.astype(np.uint8)), (0, 0))
            trip.paste(Image.fromarray(overlay.astype(np.uint8)), (x1 - x0, 0))
            trip.paste(Image.fromarray(only.astype(np.uint8)), ((x1 - x0) * 2, 0))
            trip = trip.resize((trip.width * 8, trip.height * 8), Image.Resampling.NEAREST)
            cells.append((obj, trip))
        col_width = max((im.width for _, im in cells), default=1) + 20
        row_height = max((im.height for _, im in cells), default=1) + 50
        sheet = Image.new("RGB", (col_width * 2, row_height * 6), "white")
        draw = ImageDraw.Draw(sheet)
        for pos, (obj, im) in enumerate(cells):
            col, row = pos % 2, pos // 2
            x, y = col * col_width + 10, row * row_height + 35
            draw.text((x, row * row_height + 5), f"{obj['id']}  U+{ord(obj['char']):04X}  {obj['char']!r}  ORIGINAL | OVERLAY | MASK", fill="black", font=font)
            sheet.paste(im, (x, y))
            obj["contact_sheet"] = f"review/glyph_contact_sheet_{sheet_idx + 1:03d}.png"
            obj["contact_cell"] = pos + 1
        path = REVIEW / f"glyph_contact_sheet_{sheet_idx + 1:03d}.png"
        sheet.save(path)
        sheets.append({"sheet": path.name, "glyph_count": len(chunk), "first_id": chunk[0]["id"], "last_id": chunk[-1]["id"], "native_dimensions": [sheet.width, sheet.height]})
    return sheets


def make_pair_sheets(pairs: list[dict]) -> list[dict]:
    font = ImageFont.load_default()
    sheets = []
    per_sheet = 8
    for si in range(math.ceil(len(pairs) / per_sheet)):
        chunk = pairs[si * per_sheet:(si + 1) * per_sheet]
        thumbs = []
        for p in chunk:
            im = Image.open(ROOT / p["evidence_8x"]).convert("RGB")
            thumbs.append((p, im))
        w = max((im.width for _, im in thumbs), default=1) + 20
        h = max((im.height for _, im in thumbs), default=1) + 55
        sheet = Image.new("RGB", (w * 2, h * 4), "white")
        draw = ImageDraw.Draw(sheet)
        for pos, (p, im) in enumerate(thumbs):
            col, row = pos % 2, pos // 2
            x, y = col * w + 10, row * h + 35
            draw.text((x, row * h + 5), f"{p['pair_id']} {p['relation']} clr={p['clearance_px']} ov={p['intersection_px']}", fill="black", font=font)
            sheet.paste(im, (x, y))
            p["pair_sheet"] = f"review/critical_pair_sheet_{si + 1:03d}.png"
            p["pair_sheet_cell"] = pos + 1
        path = REVIEW / f"critical_pair_sheet_{si + 1:03d}.png"
        sheet.save(path)
        sheets.append({"sheet": path.name, "pair_count": len(chunk), "first_pair": chunk[0]["pair_id"], "last_pair": chunk[-1]["pair_id"], "native_dimensions": [sheet.width, sheet.height]})
    return sheets


def serialize_obj(obj: dict) -> dict:
    fields = [
        "id", "safe_filename", "kind", "char", "unicode", "font", "font_size_pt", "font_color_rgb",
        "semantic_parent", "role", "panel", "graphic_type", "drawing_seqno", "drawing_items",
        "bbox_pt", "bbox_px", "mask_bbox_px", "mask_pixel_count", "ink_height_px", "ink_width_px",
        "pixel_class", "legacy_threshold_px", "legacy_threshold_status", "r168_hard_gate_status",
        "empty_mask", "tofu_or_decode_candidate", "clip_pixel_count", "mask_path", "contact_sheet", "contact_cell",
    ]
    return {k: obj.get(k, "") for k in fields}


def main() -> None:
    for directory in (MACHINE, RENDERS, REVIEW, GLYPH_MASKS, GRAPHIC_MASKS, PAIR_NATIVE, PAIR_8X):
        directory.mkdir(parents=True, exist_ok=True)

    start = datetime.now(timezone.utc)
    pdf_sha = sha256(PDF)
    source_sha = sha256(SOURCE)
    doc = fitz.open(PDF)
    if pdf_sha != PDF_EXPECTED_SHA256 or PDF.stat().st_size != PDF_EXPECTED_BYTES or doc.page_count != PDF_EXPECTED_PAGES:
        raise RuntimeError("Frozen R107 PDF identity mismatch")
    if source_sha != SOURCE_EXPECTED_SHA256:
        raise RuntimeError("Frozen P715 source identity mismatch")
    page = doc[PAGE_INDEX]

    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False, annots=True)
    full300 = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, pix300.n).copy()
    Image.fromarray(full300[..., :3]).save(RENDERS / "full_page_300dpi.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE_200, SCALE_200), alpha=False, annots=True)
    full200 = np.frombuffer(pix200.samples, dtype=np.uint8).reshape(pix200.height, pix200.width, pix200.n).copy()
    Image.fromarray(full200[..., :3]).save(RENDERS / "full_page_200dpi.png")

    crop_px = bbox_to_px(FIGURE_CROP_PT, SCALE_300, pix300.width, pix300.height)
    body_px = bbox_to_px(FIGURE_BODY_PT, SCALE_300, pix300.width, pix300.height)
    x0, y0, x1, y1 = crop_px
    bx0, by0, bx1, by1 = body_px
    figure_crop = Image.fromarray(full300[y0:y1, x0:x1, :3])
    figure_crop.save(RENDERS / "figure_crop_300dpi.png")
    figure_crop.convert("L").save(RENDERS / "grayscale_300dpi.png")
    Image.fromarray(full300[by0:by1, bx0:bx1, :3]).save(RENDERS / "standalone_300dpi.png")

    objects: list[dict] = []
    raw = page.get_text("rawdict")
    tid = 0
    for bi, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block.get("lines", [])):
            line_text = "".join(ch.get("c", "") for sp in line.get("spans", []) for ch in sp.get("chars", []))
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    ch = char.get("c", "")
                    rect = fitz.Rect(char["bbox"])
                    center = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
                    if not ch or ch.isspace() or not FIGURE_BODY_PT.contains(center):
                        continue
                    tid += 1
                    oid = f"T{tid:04d}"
                    safe = f"glyph_{tid:04d}_u{ord(ch):04X}.png"
                    bbox_px = bbox_to_px(rect, SCALE_300, pix300.width, pix300.height, pad=1)
                    gx0, gy0, gx1, gy1 = bbox_px
                    crop = full300[gy0:gy1, gx0:gx1, :3]
                    expected = rgb_from_int(int(span.get("color", 0)))
                    mask, mask_meta = estimate_char_mask(crop, expected)
                    mb = mask_bbox(mask, gx0, gy0)
                    yy, xx = np.nonzero(mask)
                    h_ink = int(yy.max() - yy.min() + 1) if len(yy) else 0
                    w_ink = int(xx.max() - xx.min() + 1) if len(xx) else 0
                    parent, role, panel = semantic_parent_and_role(line_text, rect, bi, li)
                    pixel_class, legacy_threshold = classify_char(ch, float(span.get("size", 0.0)), role)
                    legacy_status = "CALIBRATION_REQUIRED" if pixel_class == "LOW_PROFILE_PUNCTUATION" else ("ABOVE" if h_ink >= legacy_threshold else "BELOW")
                    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(GLYPH_MASKS / safe)
                    objects.append({
                        "id": oid, "safe_filename": safe, "kind": "TEXT", "char": ch, "unicode": f"U+{ord(ch):04X}",
                        "font": span.get("font", ""), "font_size_pt": round(float(span.get("size", 0.0)), 4),
                        "font_color_rgb": list(expected), "semantic_parent": parent, "role": role, "panel": panel,
                        "graphic_type": "", "drawing_seqno": "", "drawing_items": "",
                        "bbox_pt": [round(float(v), 4) for v in rect], "bbox_px": list(bbox_px), "mask_bbox_px": list(mb),
                        "mask_pixel_count": int(mask.sum()), "ink_height_px": h_ink, "ink_width_px": w_ink,
                        "pixel_class": pixel_class, "legacy_threshold_px": legacy_threshold,
                        "legacy_threshold_status": legacy_status,
                        "r168_hard_gate_status": "ADVISORY_ONLY_UNLESS_ACTUALLY_UNREADABLE_OR_WRONG",
                        "empty_mask": bool(mask.sum() == 0), "tofu_or_decode_candidate": ch == "\ufffd" or ord(ch) == 0,
                        "clip_pixel_count": 0 if FIGURE_CROP_PT.contains(center) else int(mask.sum()),
                        "mask_path": f"machine/masks/glyph/{safe}", "mask_meta": mask_meta, "mask": mask,
                        "source_line_key": f"B{bi:02d}_L{li:02d}",
                        "origin_px": [round(float(char["origin"][0]) * SCALE_300, 4), round(float(char["origin"][1]) * SCALE_300, 4)],
                    })

    disambiguate_text_masks(objects)

    drawings = [d for d in page.get_drawings() if d["rect"].intersects(FIGURE_BODY_PT)]
    for did, drawing in enumerate(drawings, start=1):
        seq = int(drawing["seqno"])
        graphic_type, parent, panel = drawing_semantics(seq)
        stroke_only = graphic_type in {"NODE_BORDER", "PANEL_BORDER", "CELL_BORDER", "FOCUS_BORDER"}
        mask, bbox_px = replay_drawing_mask(page.rect, drawing, SCALE_300, (pix300.width, pix300.height), stroke_only)
        oid = f"G{did:04d}"
        safe = f"graphic_{did:04d}_seq{seq:03d}.png"
        Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(GRAPHIC_MASKS / safe)
        mb = mask_bbox(mask, bbox_px[0], bbox_px[1])
        yy, xx = np.nonzero(mask)
        center = fitz.Point((drawing["rect"].x0 + drawing["rect"].x1) / 2, (drawing["rect"].y0 + drawing["rect"].y1) / 2)
        objects.append({
            "id": oid, "safe_filename": safe, "kind": "GRAPHIC", "char": "", "unicode": "", "font": "",
            "font_size_pt": "", "font_color_rgb": "", "semantic_parent": parent, "role": "GRAPHIC", "panel": panel,
            "graphic_type": graphic_type, "drawing_seqno": seq, "drawing_items": len(drawing.get("items", [])),
            "bbox_pt": [round(float(v), 4) for v in drawing["rect"]], "bbox_px": list(bbox_px), "mask_bbox_px": list(mb),
            "mask_pixel_count": int(mask.sum()), "ink_height_px": int(yy.max() - yy.min() + 1) if len(yy) else 0,
            "ink_width_px": int(xx.max() - xx.min() + 1) if len(xx) else 0, "pixel_class": "GRAPHIC_FOREGROUND",
            "legacy_threshold_px": "", "legacy_threshold_status": "N/A",
            "r168_hard_gate_status": "HARD_IF_WRONG_GEOMETRY_CLIPPED_OR_ILLEGAL_OVERLAP",
            "empty_mask": bool(mask.sum() == 0), "tofu_or_decode_candidate": False,
            "clip_pixel_count": 0 if FIGURE_CROP_PT.contains(center) else int(mask.sum()),
            "mask_path": f"machine/masks/graphic/{safe}", "mask": mask,
        })

    glyph_sheets = make_glyph_contact_sheets(full300, objects)
    serialized = [serialize_obj(o) for o in objects]
    write_csv(MACHINE / "object_ledger.csv", serialized)
    write_json(MACHINE / "object_ledger.json", serialized)
    write_csv(MACHINE / "id_safe_filename.csv", [{"element_id": o["id"], "safe_filename": o["safe_filename"], "ordinary_path": o["mask_path"]} for o in objects])
    write_csv(MACHINE / "after_pixel_measurements.csv", [serialize_obj(o) for o in objects if o["kind"] == "TEXT"])
    write_csv(MACHINE / "drawing_inventory.csv", [serialize_obj(o) for o in objects if o["kind"] == "GRAPHIC"])
    write_json(MACHINE / "glyph_contact_sheet_index.json", glyph_sheets)

    overlay = Image.fromarray(full300[by0:by1, bx0:bx1, :3].copy())
    odraw = ImageDraw.Draw(overlay)
    for o in objects:
        ox0, oy0, ox1, oy1 = o["mask_bbox_px"]
        box = (ox0 - bx0, oy0 - by0, ox1 - bx0, oy1 - by0)
        color = (220, 30, 30) if o["kind"] == "TEXT" else (30, 90, 220)
        odraw.rectangle(box, outline=color, width=1)
        odraw.text((box[0], max(0, box[1] - 8)), o["id"], fill=color)
    overlay.save(RENDERS / "after_text_measurement_overlay_300dpi.png")

    pairs: list[dict] = []
    critical: list[dict] = []
    for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
        pair_id = f"P{pair_index:05d}"
        relation, threshold, reason = relation_for(a, b)
        inter = object_intersection(a, b)
        gap = bbox_gap(a, b)
        exact = inter > 0 or gap <= 30 or (threshold > 0 and gap <= threshold + 12)
        if exact:
            clearance, pa, pb = exact_clearance(a, b)
            basis = "EXACT_NATIVE_MASK"
        else:
            clearance = max(0.0, gap - 1.0)
            pa = ((a["mask_bbox_px"][0] + a["mask_bbox_px"][2]) // 2, (a["mask_bbox_px"][1] + a["mask_bbox_px"][3]) // 2)
            pb = ((b["mask_bbox_px"][0] + b["mask_bbox_px"][2]) // 2, (b["mask_bbox_px"][1] + b["mask_bbox_px"][3]) // 2)
            basis = "CERTIFIED_BBOX_LOWER_BOUND"
        design = relation.startswith("DESIGN_")
        illegal_overlap_candidate = inter > 0 and not design and relation != "GRAPHIC_GRAPHIC"
        clearance_candidate = threshold > 0 and clearance < threshold
        row = {
            "pair_id": pair_id, "object_a": a["id"], "object_b": b["id"], "kind_a": a["kind"], "kind_b": b["kind"],
            "parent_a": a["semantic_parent"], "parent_b": b["semantic_parent"], "relation": relation,
            "relation_reason": reason, "protocol_threshold_px": threshold, "bbox_clearance_px": round(gap, 4),
            "clearance_px": round(clearance, 4) if math.isfinite(clearance) else "INF", "clearance_basis": basis,
            "intersection_px": inter, "design_relation": design, "illegal_overlap_candidate": illegal_overlap_candidate,
            "clearance_failure_candidate": clearance_candidate, "closest_a_xy": list(pa), "closest_b_xy": list(pb),
            "critical": bool((threshold > 0 and clearance <= threshold + 7) or illegal_overlap_candidate),
            "evidence_native1x": "", "evidence_8x": "", "roi_xyxy": "",
        }
        if row["critical"]:
            nrel, erel, roi = render_pair_evidence(full300, a, b, pair_id, pa, pb)
            row["evidence_native1x"] = nrel
            row["evidence_8x"] = erel
            row["roi_xyxy"] = list(roi)
            critical.append(row)
        pairs.append(row)

    pair_sheets = make_pair_sheets(critical)
    write_csv(MACHINE / "all_unordered_pairs.csv", pairs)
    write_json(MACHINE / "all_unordered_pairs_summary.json", {
        "object_count": len(objects), "expected_pair_count": len(objects) * (len(objects) - 1) // 2,
        "actual_pair_count": len(pairs), "critical_pair_count": len(critical),
        "relation_counts": dict(Counter(p["relation"] for p in pairs)),
        "clearance_basis_counts": dict(Counter(p["clearance_basis"] for p in pairs)),
        "intersection_pair_count": sum(1 for p in pairs if p["intersection_px"] > 0),
        "machine_illegal_overlap_candidate_count": sum(1 for p in pairs if p["illegal_overlap_candidate"]),
        "machine_clearance_failure_candidate_count": sum(1 for p in pairs if p["clearance_failure_candidate"]),
    })
    write_csv(MACHINE / "critical_pairs.csv", critical)
    write_json(MACHINE / "critical_pair_sheet_index.json", pair_sheets)

    source_rows = [
        {"source_role": "GLOBAL_EVERY_NODE", "declared_pt": 9.5, "effective_pt": 9.5, "scale": 1.0, "location": "tikzset/every node", "r168_interpretation": "advisory unless actually unreadable/severely imbalanced"},
        {"source_role": "TITLE", "declared_pt": 10.4, "effective_pt": 10.4, "scale": 1.0, "location": "title/.style", "r168_interpretation": "advisory unless actually unreadable/severely imbalanced"},
        {"source_role": "PAGE_NODE", "declared_pt": 10.2, "effective_pt": 10.2, "scale": 1.0, "location": "page/.style", "r168_interpretation": "advisory unless actually unreadable/severely imbalanced"},
        {"source_role": "EDGE_NOTE", "declared_pt": 9.5, "effective_pt": 9.5, "scale": 1.0, "location": "edge note/.style", "r168_interpretation": "advisory unless actually unreadable/severely imbalanced"},
        {"source_role": "FORMULA", "declared_pt": 12.0, "effective_pt": 12.0, "scale": 1.0, "location": "formula/.style", "r168_interpretation": "advisory unless actually unreadable/severely imbalanced"},
        {"source_role": "MATRIX_CELL", "declared_pt": 10.2, "effective_pt": 10.2, "scale": 1.0, "location": "cell/.style", "r168_interpretation": "advisory unless actually unreadable/severely imbalanced"},
        {"source_role": "NOTE", "declared_pt": 9.5, "effective_pt": 9.5, "scale": 1.0, "location": "note/.style", "r168_interpretation": "advisory unless actually unreadable/severely imbalanced"},
    ]
    write_csv(MACHINE / "after_font_audit.csv", source_rows)

    fonts = []
    for item in doc.get_page_fonts(PAGE_INDEX, full=True):
        fonts.append({"xref": item[0], "extension": item[1], "type": item[2], "basefont": item[3], "resource_name": item[4], "encoding": item[5], "referencer": item[6]})
    write_json(MACHINE / "font_metadata.json", {"page": PHYSICAL_PAGE, "fonts": fonts})

    render_metadata = {
        "official_pdf": str(PDF), "physical_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE,
        "figure_number": FIGURE_NUMBER, "page_size_pt": [round(page.rect.width, 4), round(page.rect.height, 4)],
        "full_page_300dpi_native_dimensions": [pix300.width, pix300.height],
        "full_page_200dpi_native_dimensions": [pix200.width, pix200.height],
        "figure_crop_pt": [float(v) for v in FIGURE_CROP_PT], "figure_crop_px_xyxy": list(crop_px),
        "figure_crop_native_dimensions": [x1 - x0, y1 - y0],
        "standalone_body_pt": [float(v) for v in FIGURE_BODY_PT], "standalone_body_px_xyxy": list(body_px),
        "standalone_native_dimensions": [bx1 - bx0, by1 - by0], "render_engine": f"PyMuPDF {fitz.VersionBind}",
        "render_rule": "direct from frozen PDF; no post-render resize; grayscale is mode conversion only",
    }
    write_json(MACHINE / "render_metadata.json", render_metadata)

    graphic_counts = Counter(o["graphic_type"] for o in objects if o["kind"] == "GRAPHIC")
    role_counts = Counter(o["role"] for o in objects if o["kind"] == "TEXT")
    machine_summary = {
        "handoff_id": HANDOFF_ID, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "pdf_identity": {"bytes": PDF.stat().st_size, "sha256": pdf_sha, "pages": doc.page_count, "match": True},
        "source_identity": {"bytes": SOURCE.stat().st_size, "sha256": source_sha, "match": True},
        "locator": {"physical_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE, "figure_number": FIGURE_NUMBER, "title_left": "网页图、邻接矩阵与列归一", "title_right": "行随机转置桥"},
        "text_glyph_count": sum(1 for o in objects if o["kind"] == "TEXT"),
        "foreground_drawing_path_count": sum(1 for o in objects if o["kind"] == "GRAPHIC"),
        "visible_object_denominator_N": len(objects), "all_unordered_pair_count_C_N_2": len(pairs),
        "graphic_type_counts": dict(graphic_counts), "text_role_counts": dict(role_counts),
        "graph_edge_parent_count": len({o["semantic_parent"] for o in objects if o.get("graphic_type") in {"EDGE_SHAFT", "ARROWHEAD"}}),
        "matrix_cell_border_count": graphic_counts.get("CELL_BORDER", 0), "math_rule_path_count": graphic_counts.get("MATH_RULE", 0),
        "empty_mask_ids": [o["id"] for o in objects if o["empty_mask"]],
        "tofu_or_decode_candidate_ids": [o["id"] for o in objects if o["tofu_or_decode_candidate"]],
        "hard_overlap_candidate_pair_ids": [p["pair_id"] for p in pairs if p["illegal_overlap_candidate"]],
        "clearance_failure_candidate_pair_ids": [p["pair_id"] for p in pairs if p["clearance_failure_candidate"]],
        "critical_pair_count": len(critical), "glyph_contact_sheet_count": len(glyph_sheets),
        "critical_pair_sheet_count": len(pair_sheets),
        "r168_policy": "font size, pixel ratios, [0.92,1.08], taxonomy/peer deltas, font metadata and 1-2px raster differences are advisory and cannot alone fail; hard failures require actual unreadability/tofu/wrong code or math, obvious severe imbalance, real clip/illegal overlap, or real geometry/relationship error",
        "machine_scope": "objective extraction only; no manual reviewer, boolean decision, note, or final SA1 verdict generated by this script",
        "build_elapsed_seconds": round((datetime.now(timezone.utc) - start).total_seconds(), 3),
    }
    write_json(MACHINE / "machine_summary.json", machine_summary)
    doc.close()
    print(json.dumps(machine_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
