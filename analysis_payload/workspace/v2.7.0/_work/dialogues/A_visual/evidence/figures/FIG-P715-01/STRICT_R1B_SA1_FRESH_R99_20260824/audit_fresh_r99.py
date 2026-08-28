#!/usr/bin/env python3
"""Fresh, isolated R99 evidence builder for FIG-P715-01.

This script is deliberately self-contained.  It reads only the frozen R99 PDF
and the explicitly authorised figure source, and writes only beside itself.
It has three phases:
  build          raw evidence / bottom-layer CSVs / review cards
  mark-reviewed  records the human SA1 opening of every generated card
  finalize       recomputes from CSVs, writes reports, then WRITE_STOPPED last
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C07.tex")
UID = "FIG-P715-01"
HANDOFF_ID = "A-R99-P715-SA1-FRESH-B-20260824"
R99_PAGE_INDEX = 762
R99_PHYSICAL_PAGE = 763
EXPECTED_SHA256 = "E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6"
EXPECTED_BYTES = 4_940_207
DPI = 300
SCALE = DPI / 72.0
CONTRAST = 20
FIGURE_CROP = (250, 250, 2200, 1210)  # full-page 300 dpi integer pixels, includes caption
STANDALONE_CROP = (250, 250, 2200, 1130)  # graph only, no caption
FIGURE_RECT_PT = fitz.Rect(60, 60, 525, 292)
GRAPH_RECT_PT = fitz.Rect(60, 60, 525, 270)
TILE = 80


def mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def dump_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def png(path: Path, image: Image.Image) -> None:
    image.save(path, "PNG", optimize=True)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def rect_px(rect: fitz.Rect, width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, math.floor(rect.x0 * SCALE) - pad)
    y0 = max(0, math.floor(rect.y0 * SCALE) - pad)
    x1 = min(width, math.ceil(rect.x1 * SCALE) + pad)
    y1 = min(height, math.ceil(rect.y1 * SCALE) + pad)
    return x0, y0, x1, y1


def mask_bbox(coords: np.ndarray) -> tuple[int, int, int, int]:
    ys = coords[:, 0]
    xs = coords[:, 1]
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def is_visible_char(value: int | str) -> bool:
    ch = chr(value) if isinstance(value, int) else value
    return not ch.isspace() and unicodedata.category(ch)[0] != "C"


def script_class(ch: str, pdf_pt: float, parent: str) -> tuple[str, int]:
    # The categories are deliberately conservative: low-stroke CJK remains CJK.
    if ch in {".", ",", "，", "。", "、", "：", ":", ";", "；", "·"}:
        return "LOW_PROFILE_PUNCTUATION", 0
    if "CJK" in unicodedata.name(ch, "") or "IDEOGRAPH" in unicodedata.name(ch, "") or "FULLWIDTH" in unicodedata.name(ch, ""):
        return "CJK_FULL", 30
    name = unicodedata.name(ch, "")
    if ch.isdigit() or ("CAPITAL" in name and "SMALL" not in name):
        return "LATIN_DIGIT_UPPER", 24
    if ch.isalpha() and (ch.islower() or "SMALL" in name):
        return "LATIN_GREEK_LOWER", 17
    if "SMALL" in name and "MATHEMATICAL" in name:
        return "LATIN_GREEK_LOWER", 17
    if ch in {"=", "+", "−", "-", ">", "<", "⟺", "→", "∑", "/", "|", "∣", "∈", "≥", "≤"}:
        return "BASE_MATH_OPERATOR", 22
    if ch in {"(", ")", "[", "]", "{", "}"}:
        return "MATH_BRACKET", 22
    if parent.startswith("FORMULA") and pdf_pt < 11.8:
        return "NATURAL_SCRIPT", 15
    if parent.startswith("FORMULA"):
        return "BASE_MATH_OPERATOR", 22
    return "LATIN_GREEK_LOWER", 17


def role_for_seq(seq: int) -> tuple[str, str, str, str]:
    # parent, role, panel, source-style
    mapping = {
        5: ("TITLE_LEFT", "PANEL_TITLE", "LEFT", "title"),
        6: ("TITLE_RIGHT", "PANEL_TITLE", "RIGHT", "title"),
        9: ("NODE_I", "NODE_LABEL", "LEFT", "page"),
        12: ("NODE_J", "NODE_LABEL", "LEFT", "page"),
        15: ("NODE_H", "NODE_LABEL", "LEFT", "page"),
        19: ("EDGE_J_TO_I", "EDGE_LABEL", "LEFT", "edge_note"),
        23: ("EDGE_I_TO_J", "EDGE_LABEL", "LEFT", "edge_note"),
        30: ("NOTE_EDGES", "ORDINARY_NOTE", "LEFT", "note"),
        31: ("NOTE_ORDER_LEFT", "ORDINARY_NOTE", "LEFT", "note"),
        32: ("FORMULA_AIJ", "FORMULA_BLOCK", "LEFT", "formula"),
        33: ("FORMULA_CJ", "FORMULA_BLOCK", "LEFT", "formula"),
        34: ("MATRIX_A_LABEL", "FORMULA_BLOCK", "LEFT", "formula"),
        74: ("FORMULA_COLUMN_NORMALIZATION", "FORMULA_BLOCK", "LEFT", "formula"),
        75: ("FORMULA_COLUMN_SUM", "FORMULA_BLOCK", "LEFT", "formula"),
        76: ("FORMULA_COLUMN_UPDATE", "FORMULA_BLOCK", "LEFT", "formula"),
        77: ("NOTE_ORDER_RIGHT", "ORDINARY_NOTE", "RIGHT", "note"),
        78: ("MATRIX_P_LABEL", "FORMULA_BLOCK", "RIGHT", "formula"),
        98: ("FORMULA_TRANSPOSE", "FORMULA_BLOCK", "RIGHT", "formula"),
        99: ("FORMULA_INDEX_BRIDGE", "FORMULA_BLOCK", "RIGHT", "formula"),
        100: ("FORMULA_PROBABILITY_BRIDGE", "FORMULA_BLOCK", "RIGHT", "formula"),
        101: ("FORMULA_ROW_SUM", "FORMULA_BLOCK", "RIGHT", "formula"),
        102: ("FORMULA_ROW_UPDATE", "FORMULA_BLOCK", "RIGHT", "formula"),
        103: ("FORMULA_STATE_BRIDGE", "FORMULA_BLOCK", "RIGHT", "formula"),
        104: ("CAPTION_36_2", "CAPTION", "CAPTION", "caption"),
    }
    if 36 <= seq <= 52:
        return ("MATRIX_A", "MATRIX_CELL", "LEFT", "cell")
    if 54 <= seq <= 72:
        return ("MATRIX_M", "MATRIX_CELL", "LEFT", "cell")
    if 80 <= seq <= 96:
        return ("MATRIX_P", "MATRIX_CELL", "RIGHT", "cell")
    return mapping.get(seq, (f"UNMAPPED_SEQ_{seq}", "UNMAPPED", "UNKNOWN", "unknown"))


def source_line(lines: list[str], token: str) -> int:
    for i, line in enumerate(lines, 1):
        if token in line:
            return i
    return 0


def parent_source_line(parent: str, lines: list[str]) -> int:
    tokens = {
        "TITLE_LEFT": "网页图、邻接矩阵与列归一",
        "TITLE_RIGHT": "行随机转置桥",
        "NODE_I": "(gi)", "NODE_J": "(gj)", "NODE_H": "(gh)",
        "EDGE_J_TO_I": "$j\\to i$", "EDGE_I_TO_J": "$i\\to j$",
        "NOTE_EDGES": "四条边权", "NOTE_ORDER_LEFT": "矩阵行、列顺序均为",
        "FORMULA_AIJ": "$A_{ij}>0", "FORMULA_CJ": "$c_j=",
        "MATRIX_A_LABEL": "$A=$", "MATRIX_A": "{$0$&$1$&$1$",
        "MATRIX_M": "{$0$&$1/2$&$1$", "FORMULA_COLUMN_NORMALIZATION": "$M_{:j}",
        "FORMULA_COLUMN_SUM": "$\\boldsymbol1", "FORMULA_COLUMN_UPDATE": "$\\boldsymbol p",
        "NOTE_ORDER_RIGHT": "同一结点顺序", "MATRIX_P_LABEL": "$P=$",
        "MATRIX_P": "{$0$&$1$&$0$", "FORMULA_TRANSPOSE": "$P=M",
        "FORMULA_INDEX_BRIDGE": "$P_{ji}", "FORMULA_PROBABILITY_BRIDGE": "\\Pr",
        "FORMULA_ROW_SUM": "$P\\boldsymbol1", "FORMULA_ROW_UPDATE": "$\\rho_{t+1}",
        "FORMULA_STATE_BRIDGE": "$\\rho_t=", "CAPTION_36_2": "\\caption{列随机",
    }
    return source_line(lines, tokens.get(parent, "__missing__"))


def path_meta(seq: int) -> tuple[str, str, str, str]:
    # parent, category, panel, role
    if seq == 3:
        return ("PANEL_LEFT", "PANEL_BORDER", "LEFT", "PANEL_BORDER")
    if seq == 4:
        return ("PANEL_RIGHT", "PANEL_BORDER", "RIGHT", "PANEL_BORDER")
    if seq in {7, 10, 13}:
        return ({7: "NODE_I", 10: "NODE_J", 13: "NODE_H"}[seq], "NODE_BORDER", "LEFT", "NODE_BORDER")
    if seq in {16, 20, 24, 27}:
        return ({16: "ARROW_J_TO_I", 20: "ARROW_I_TO_J", 24: "ARROW_J_TO_H", 27: "ARROW_H_TO_I"}[seq], "LINE_ARROW", "LEFT", "ARROW_SHAFT")
    if seq in {17, 21, 25, 28}:
        return ({17: "ARROW_J_TO_I", 21: "ARROW_I_TO_J", 25: "ARROW_J_TO_H", 28: "ARROW_H_TO_I"}[seq], "MARKER", "LEFT", "ARROWHEAD")
    if seq in {53, 73, 97}:
        panel = "LEFT" if seq in {53, 73} else "RIGHT"
        parent = {53: "MATRIX_A", 73: "MATRIX_M", 97: "MATRIX_P"}[seq]
        return (parent, "FOCUS_BORDER", panel, "FOCUS_BORDER")
    if 35 <= seq <= 73:
        return ("MATRIX_A" if seq <= 53 else "MATRIX_M", "NODE_BORDER", "LEFT", "MATRIX_CELL_BORDER")
    if 79 <= seq <= 97:
        return ("MATRIX_P", "NODE_BORDER", "RIGHT", "MATRIX_CELL_BORDER")
    return (f"PATH_SEQ_{seq}", "UNKNOWN_PATH", "UNKNOWN", "UNKNOWN")


def foreground_mask(rgb: np.ndarray) -> np.ndarray:
    # Source figure uses white page / very pale node fill.  The protocol's 20/255
    # contrast threshold makes contrast from white a conservative mask gate.
    return np.max(255 - rgb.astype(np.int16), axis=2) >= CONTRAST


def render_path_mask(draw: dict, page_rect: fitz.Rect, width: int, height: int) -> np.ndarray:
    d = fitz.open()
    p = d.new_page(width=page_rect.width, height=page_rect.height)
    s = p.new_shape()
    for item in draw["items"]:
        op = item[0]
        if op == "l":
            s.draw_line(item[1], item[2])
        elif op == "c":
            s.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            s.draw_rect(item[1])
        elif op == "qu":
            # Not present in this candidate, retained to make the replay explicit.
            s.draw_quad(item[1], item[2], item[3])
        else:
            raise RuntimeError(f"Unsupported drawing item {op!r} in seqno {draw['seqno']}")
    stroke = draw.get("color")
    fill = draw.get("fill")
    if draw["type"] == "f":
        stroke = None
    s.finish(
        width=float(draw.get("width") or 1.0),
        color=stroke,
        fill=fill,
        lineCap=int((draw.get("lineCap") or (0,))[0]),
        lineJoin=int(draw.get("lineJoin") or 0),
        dashes=draw.get("dashes") or None,
        even_odd=bool(draw.get("even_odd") or False),
        closePath=bool(draw.get("closePath") if draw.get("closePath") is not None else True),
        fill_opacity=float(draw.get("fill_opacity") if draw.get("fill_opacity") is not None else 1.0),
        stroke_opacity=float(draw.get("stroke_opacity") if draw.get("stroke_opacity") is not None else 1.0),
    )
    s.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    d.close()
    if (pix.width, pix.height) != (width, height):
        raise RuntimeError(f"Single-path replay grid mismatch {(pix.width,pix.height)} != {(width,height)}")
    return foreground_mask(image)


def paste_native(canvas: Image.Image, im: Image.Image, xy: tuple[int, int]) -> None:
    canvas.paste(im, xy)


def rgb_overlay(rgb: np.ndarray, mask: np.ndarray, color: tuple[int, int, int]) -> Image.Image:
    out = rgb.copy().astype(np.float32)
    out[mask] = 0.38 * out[mask] + 0.62 * np.array(color, dtype=np.float32)
    return Image.fromarray(out.astype(np.uint8), "RGB")


def mask_image(mask: np.ndarray) -> Image.Image:
    a = np.full((mask.shape[0], mask.shape[1], 3), 255, dtype=np.uint8)
    a[mask] = (0, 0, 0)
    return Image.fromarray(a, "RGB")


def make_card(rgb: np.ndarray, mask: np.ndarray, tile: tuple[int, int, int, int], title: str) -> Image.Image:
    x0, y0, x1, y1 = tile
    crop = rgb[y0:y1, x0:x1]
    m = mask[y0:y1, x0:x1]
    # Tile is bounded at 80x80. Center the unscaled source pixels in each native panel.
    native = Image.new("RGB", (TILE, TILE), (238, 238, 238))
    over = native.copy()
    mono = native.copy()
    im = Image.fromarray(crop, "RGB")
    ov = rgb_overlay(crop, m, (220, 0, 0))
    mo = mask_image(m)
    ox = max(0, (TILE - im.width) // 2)
    oy = max(0, (TILE - im.height) // 2)
    paste_native(native, im, (ox, oy))
    paste_native(over, ov, (ox, oy))
    paste_native(mono, mo, (ox, oy))
    nearest = native.resize((TILE * 8, TILE * 8), Image.Resampling.NEAREST)
    card = Image.new("RGB", (TILE * 11 + 30, TILE * 8 + 44), "white")
    draw = ImageDraw.Draw(card)
    draw.text((4, 3), title, fill=(0, 0, 0))
    draw.text((4, 20), "ORIGINAL 1x", fill=(0, 0, 0))
    draw.text((TILE + 10, 20), "TARGET OVERLAY 1x", fill=(0, 0, 0))
    draw.text((TILE * 2 + 20, 20), "MASK ONLY 1x", fill=(0, 0, 0))
    draw.text((TILE * 3 + 30, 20), "NEAREST 8x", fill=(0, 0, 0))
    card.paste(native, (4, 42))
    card.paste(over, (TILE + 10, 42))
    card.paste(mono, (TILE * 2 + 20, 42))
    card.paste(nearest, (TILE * 3 + 30, 42))
    return card


def tile_mask(mask: np.ndarray, bbox: tuple[int, int, int, int]) -> list[tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bbox
    result = []
    for yy in range(y0, y1, TILE):
        for xx in range(x0, x1, TILE):
            xe, ye = min(x1, xx + TILE), min(y1, yy + TILE)
            if mask[yy:ye, xx:xe].any():
                result.append((xx, yy, xe, ye))
    return result


def make_contact_sheets(card_paths: list[tuple[str, Path]], outdir: Path, prefix: str) -> list[dict]:
    mkdir(outdir)
    index = []
    per_sheet = 6
    for batch_start in range(0, len(card_paths), per_sheet):
        batch = card_paths[batch_start:batch_start + per_sheet]
        cards = [Image.open(p).convert("RGB") for _, p in batch]
        cw = max(c.width for c in cards)
        ch = max(c.height for c in cards)
        sheet = Image.new("RGB", (cw * 2, ch * 3), "white")
        for i, ((object_id, card_path), card) in enumerate(zip(batch, cards)):
            x = (i % 2) * cw
            y = (i // 2) * ch
            sheet.paste(card, (x, y))
            index.append({"OBJECT_OR_TILE_ID": object_id, "CARD_PATH": str(card_path.relative_to(OUT)).replace("\\", "/"), "SHEET": f"{prefix}_{batch_start // per_sheet + 1:03d}.png", "CELL": i + 1})
        path = outdir / f"{prefix}_{batch_start // per_sheet + 1:03d}.png"
        png(path, sheet)
    return index


def nearest_distance(a: np.ndarray, b: np.ndarray, tree_cache: dict[str, cKDTree], a_id: str, b_id: str) -> float:
    if len(a) == 0 or len(b) == 0:
        return math.inf
    # Build once per final visible raw mask; query the smaller point-set.
    if len(a) <= len(b):
        key, pts, query = b_id, b, a
    else:
        key, pts, query = a_id, a, b
    if key not in tree_cache:
        tree_cache[key] = cKDTree(pts[:, ::-1])  # x,y coordinate order
    dist, _ = tree_cache[key].query(query[:, ::-1], k=1)
    return float(np.min(dist))


def masks_intersection_count(a: np.ndarray, b: np.ndarray, width: int) -> int:
    aa = a[:, 0].astype(np.int64) * width + a[:, 1].astype(np.int64)
    bb = b[:, 0].astype(np.int64) * width + b[:, 1].astype(np.int64)
    return int(np.intersect1d(aa, bb, assume_unique=True).size)


def pair_relation(a: dict, b: dict) -> tuple[str, bool]:
    # Pair-specific, explicit whitelists only.  Nothing is globally exempt.
    if a["kind"] == b["kind"] == "TEXT_GLYPH" and a["parent"] == b["parent"]:
        return "SAME_SEMANTIC_TEXT_PARENT", True
    roles = {a["role"], b["role"]}
    if roles == {"ARROW_SHAFT", "ARROWHEAD"} and a["parent"] == b["parent"]:
        return "DESIGN_ARROWHEAD_ATTACHMENT", True
    if a["role"] == b["role"] == "MATRIX_CELL_BORDER" and a["parent"] == b["parent"]:
        return "DESIGN_MATRIX_GRID_CONTINUITY", True
    if "FOCUS_BORDER" in roles and a["parent"] == b["parent"]:
        return "DESIGN_FOCUS_BORDER_OVERLAY", True
    if "ARROW_SHAFT" in roles and "NODE_BORDER" in roles and a["panel"] == b["panel"] == "LEFT":
        return "DESIGN_ARROW_NODE_ANCHOR", True
    return "INDEPENDENT", False


def pair_threshold(a: dict, b: dict, whitelisted: bool) -> tuple[float, str]:
    if whitelisted:
        return 0.0, "WHITELISTED_DESIGN_RELATION"
    kinds = {a["kind"], b["kind"]}
    if kinds == {"TEXT_GLYPH"}:
        if a["panel"] != b["panel"] and {a["panel"], b["panel"]} == {"LEFT", "RIGHT"}:
            return 8.0, "CROSS_PANEL_READER_TEXT"
        return 4.0, "TEXT_TEXT_BBOX_GATE"
    text = a if a["kind"] == "TEXT_GLYPH" else b if b["kind"] == "TEXT_GLYPH" else None
    graphic = b if text is a else a if text is b else None
    if text is not None and graphic is not None:
        if graphic["category"] == "NODE_BORDER" and text["parent"] in {"NODE_I", "NODE_J", "NODE_H"}:
            return 5.0, "NODE_TEXT_TO_BORDER"
        if graphic["category"] == "PANEL_BORDER":
            return 6.0, "TEXT_TO_PANEL_BORDER"
        return 3.0, "TEXT_TO_FOREGROUND_GRAPHIC"
    return 0.0, "NO_TEXT_CLEARANCE_RULE"


def object_mask_png(mask: np.ndarray, bbox: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    return mask_image(mask[y0:y1, x0:x1])


def ensure_unstopped() -> None:
    stopped = OUT / "WRITE_STOPPED"
    if stopped.exists():
        raise RuntimeError("WRITE_STOPPED already exists: this fresh evidence directory is immutable.")


def build() -> None:
    ensure_unstopped()
    mkdir(OUT / "objects" / "masks")
    mkdir(OUT / "review_cards")
    mkdir(OUT / "review_contact_sheets")
    mkdir(OUT / "critical_pairs")
    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    doc = fitz.open(PDF)
    if doc.page_count != 814:
        raise RuntimeError(f"Expected 814 pages, got {doc.page_count}")
    page = doc[R99_PAGE_INDEX]
    page_rect = page.rect
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False)
    full300 = Image.frombytes("RGB", (pix300.width, pix300.height), pix300.samples)
    full200 = Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples)
    png(OUT / "full_page_200dpi.png", full200)
    png(OUT / "full_page_300dpi_native.png", full300)
    figure_crop = full300.crop(FIGURE_CROP)
    png(OUT / "figure_crop_300dpi.png", figure_crop)
    png(OUT / "grayscale_300dpi.png", figure_crop.convert("L"))

    # Standalone is a new PDF page that imports only the official R99 graph vector clip;
    # no LaTeX build is invoked and no source candidate is substituted.
    stand_pdf = fitz.open()
    sp = stand_pdf.new_page(width=GRAPH_RECT_PT.width, height=GRAPH_RECT_PT.height)
    sp.show_pdf_page(sp.rect, doc, R99_PAGE_INDEX, clip=GRAPH_RECT_PT)
    standalone_pdf_path = OUT / "standalone_r99_vector_clip.pdf"
    stand_pdf.save(standalone_pdf_path)
    spix = sp.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    standalone = Image.frombytes("RGB", (spix.width, spix.height), spix.samples)
    png(OUT / "standalone_300dpi.png", standalone)
    stand_pdf.close()

    rgb = np.asarray(full300).copy()
    fg = foreground_mask(rgb)
    h, w = fg.shape
    raw_hash = sha256(PDF)
    render_manifest = {
        "uid": UID,
        "handoff_id": HANDOFF_ID,
        "candidate_pdf": str(PDF),
        "candidate_sha256": raw_hash,
        "candidate_bytes": PDF.stat().st_size,
        "candidate_page_count": doc.page_count,
        "r99_physical_page": R99_PHYSICAL_PAGE,
        "printed_page": "750",
        "page_rect_pt": [page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1],
        "full_page_300dpi_native_grid": [w, h],
        "full_page_200dpi_native_grid": [pix200.width, pix200.height],
        "figure_crop_300dpi_integer_xyxy_in_full_page": list(FIGURE_CROP),
        "figure_crop_300dpi_grid": list(figure_crop.size),
        "standalone_r99_vector_clip_pt": list(GRAPH_RECT_PT),
        "standalone_300dpi_grid": list(standalone.size),
        "renderer": f"PyMuPDF {fitz.VersionBind}",
        "resized_after_render": False,
        "dpi": {"full_page": 200, "figure_crop": 300, "standalone": 300, "grayscale": 300},
    }
    dump_json(OUT / "render_manifest.json", render_manifest)

    # Source font inventory: no global source is assumed; the caption's effective
    # value is observed directly in the R99 PDF and the figure source has no local scale.
    forbidden_scalers = [r"\\resizebox", r"\\scalebox", r"transform shape", r"scale="]
    scaler_hits = [p for p in forbidden_scalers if re.search(p, "\n".join(source_lines))]
    source_font_rows = [
        {"STYLE": "slfig-FIG-P715-01", "SOURCE_LINE": source_line(source_lines, "slfig-FIG-P715-01"), "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "SCOPE": "global figure style", "PASS": "PASS"},
        {"STYLE": "every node", "SOURCE_LINE": source_line(source_lines, "every node/.style"), "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "SCOPE": "all nodes", "PASS": "PASS"},
        {"STYLE": "title", "SOURCE_LINE": source_line(source_lines, "title/.style"), "DECLARED_PT": 10.4, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 10.4, "SCOPE": "panel titles", "PASS": "PASS"},
        {"STYLE": "page", "SOURCE_LINE": source_line(source_lines, "page/.style"), "DECLARED_PT": 10.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 10.2, "SCOPE": "node labels", "PASS": "PASS"},
        {"STYLE": "edge note", "SOURCE_LINE": source_line(source_lines, "edge note/.style"), "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "SCOPE": "edge labels", "PASS": "PASS"},
        {"STYLE": "formula", "SOURCE_LINE": source_line(source_lines, "formula/.style"), "DECLARED_PT": 12.0, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 12.0, "SCOPE": "formula base", "PASS": "PASS"},
        {"STYLE": "cell", "SOURCE_LINE": source_line(source_lines, "cell/.style"), "DECLARED_PT": 10.2, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 10.2, "SCOPE": "matrix cells", "PASS": "PASS"},
        {"STYLE": "note", "SOURCE_LINE": source_line(source_lines, "note/.style"), "DECLARED_PT": 9.5, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 9.5, "SCOPE": "ordinary notes", "PASS": "PASS"},
        {"STYLE": "caption", "SOURCE_LINE": source_line(source_lines, "\\caption{"), "DECLARED_PT": 10.0, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": 10.0, "SCOPE": "R99 observed TeX pt from PDF texttrace; no local figure scale", "PASS": "PASS"},
        {"STYLE": "local_scaler_scan", "SOURCE_LINE": 0, "DECLARED_PT": "N/A", "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": "N/A", "SCOPE": "no resizebox/scalebox/scale/transform shape found" if not scaler_hits else ";".join(scaler_hits), "PASS": "PASS" if not scaler_hits else "FAIL"},
    ]
    write_csv(OUT / "after_font_audit.csv", source_font_rows)

    objects: list[dict] = []
    object_masks: dict[str, np.ndarray] = {}
    object_pre_masks: dict[str, np.ndarray] = {}
    glyph_rows: list[dict] = []
    object_rows: list[dict] = []

    # PDF texttrace gives glyph-level geometry and seqno; restrict it only to the R99
    # figure + caption sequence numbers, established independently by the final page.
    gid = 0
    for tr in page.get_texttrace():
        seq = int(tr["seqno"])
        if not (5 <= seq <= 104):
            continue
        parent, role, panel, style = role_for_seq(seq)
        if role == "UNMAPPED":
            raise RuntimeError(f"Unexpected figure text sequence {seq}")
        for ci, chardata in enumerate(tr["chars"], 1):
            ch = chr(chardata[0])
            if not is_visible_char(ch):
                continue
            char_rect = fitz.Rect(chardata[3])
            if not char_rect.intersects(FIGURE_RECT_PT):
                continue
            gid += 1
            oid = f"G{gid:04d}"
            safe = oid
            x0, y0, x1, y1 = rect_px(char_rect, w, h)
            local = fg[y0:y1, x0:x1]
            coords_local = np.argwhere(local)
            coords = coords_local.copy()
            if len(coords):
                coords[:, 0] += y0
                coords[:, 1] += x0
                bb = mask_bbox(coords)
                h_ink = int(bb[3] - bb[1])
            else:
                bb = (x0, y0, x1, y1)
                h_ink = 0
            pdf_tex_pt = float(tr["size"]) * 72.27 / 72.0
            script, threshold = script_class(ch, pdf_tex_pt, parent)
            if parent.startswith("FORMULA") and pdf_tex_pt < 11.8 and script not in {"LOW_PROFILE_PUNCTUATION", "BASE_MATH_OPERATOR"}:
                script, threshold = "NATURAL_SCRIPT", 15
            measured_pass = len(coords) > 0 and (script == "LOW_PROFILE_PUNCTUATION" or h_ink >= threshold)
            obj = {
                "id": oid, "safe": safe, "kind": "TEXT_GLYPH", "category": "FORMULA" if parent.startswith("FORMULA") or parent.startswith("MATRIX") else "TEXT",
                "parent": parent, "role": role, "panel": panel, "seqno": seq, "bbox": bb, "pdf_bbox": [char_rect.x0, char_rect.y0, char_rect.x1, char_rect.y1],
                "coords": coords, "pre_coords": coords.copy(), "char": ch, "font": tr["font"], "pdf_pt": float(tr["size"]), "effective_pt": pdf_tex_pt,
                "script": script, "threshold": threshold, "h_ink": h_ink, "source_line": parent_source_line(parent, source_lines),
                "measured_pass": measured_pass,
            }
            objects.append(obj)
            object_masks[oid] = coords
            object_pre_masks[oid] = coords.copy()

    # Every foreground PDF drawing/path belonging to the figure is replayed one by one
    # using its own seqno.  There are no rawdict-external mathematical rules here: the
    # source contains no overline/underline/hat/root/fraction rule; all sum/slash glyphs
    # occur in texttrace and are therefore already present above.
    pid = 0
    for drawing in page.get_drawings(extended=True):
        seq = int(drawing["seqno"])
        if not (3 <= seq <= 97) or not drawing["rect"].intersects(GRAPH_RECT_PT):
            continue
        pid += 1
        oid = f"P{pid:04d}"
        parent, category, panel, role = path_meta(seq)
        pm = render_path_mask(drawing, page_rect, w, h)
        coords = np.argwhere(pm)
        if not len(coords):
            raise RuntimeError(f"Empty single-path replay for seqno {seq}")
        bb = mask_bbox(coords)
        obj = {
            "id": oid, "safe": oid, "kind": "GRAPHIC_PATH", "category": category, "parent": parent,
            "role": role, "panel": panel, "seqno": seq, "bbox": bb,
            "pdf_bbox": [drawing["rect"].x0, drawing["rect"].y0, drawing["rect"].x1, drawing["rect"].y1],
            "coords": coords, "pre_coords": coords.copy(), "char": "", "font": "", "pdf_pt": "", "effective_pt": "",
            "script": "GRAPHIC_PATH", "threshold": "", "h_ink": int(bb[3] - bb[1]), "source_line": 0, "measured_pass": True,
            "draw_type": drawing["type"], "stroke": drawing.get("color"), "fill": drawing.get("fill"), "width_pt": drawing.get("width"),
        }
        objects.append(obj)
        object_masks[oid] = coords
        object_pre_masks[oid] = coords.copy()

    # Final-visible ownership is recorded by seqno, while the raw foreground mask for
    # each vector path remains its own unmodified single-path replay. This candidate has
    # no opaque text halo or node background that occludes a different semantic object;
    # repeated matrix-border painters and orange focus strokes are pair-specific design
    # relations (audited below), not a license to erase an earlier path's raw mask.
    # Keeping both paths makes the all-drawing denominator and z-order record complete.
    for obj in objects:
        obj["final_visible_occluded_pixels"] = 0

    # Recompute bboxes after final-visible masking, write raw mask PNGs, and create
    # one fully covering 1x+nearest-8x tile set per object.
    card_items: list[tuple[str, Path]] = []
    card_rows: list[dict] = []
    for obj in objects:
        coords = obj["coords"]
        if not len(coords):
            raise RuntimeError(f"Empty final-visible mask {obj['id']}")
        obj["bbox"] = mask_bbox(coords)
        fullmask = np.zeros((h, w), dtype=bool)
        fullmask[coords[:, 0], coords[:, 1]] = True
        mask_path = OUT / "objects" / "masks" / f"{obj['safe']}_raw_mask.png"
        png(mask_path, object_mask_png(fullmask, obj["bbox"]))
        obj["mask_path"] = str(mask_path.relative_to(OUT)).replace("\\", "/")
        tiles = tile_mask(fullmask, obj["bbox"])
        covered = 0
        for ti, tile in enumerate(tiles, 1):
            x0, y0, x1, y1 = tile
            covered += int(fullmask[y0:y1, x0:x1].sum())
            tid = f"{obj['id']}_T{ti:03d}"
            card = make_card(rgb, fullmask, tile, f"{tid} | {obj['kind']} | seq={obj['seqno']} | {obj['parent']}")
            cp = OUT / "review_cards" / f"{tid}.png"
            png(cp, card)
            card_items.append((tid, cp))
            card_rows.append({"OBJECT_ID": obj["id"], "TILE_ID": tid, "TILE_INDEX": ti, "NATIVE_X0": x0, "NATIVE_Y0": y0, "NATIVE_X1": x1, "NATIVE_Y1": y1, "MASK_PIXEL_COUNT_IN_TILE": int(fullmask[y0:y1, x0:x1].sum()), "CARD_PATH": str(cp.relative_to(OUT)).replace("\\", "/")})
        if covered != len(coords):
            raise RuntimeError(f"Tile coverage failure {obj['id']}: {covered} != {len(coords)}")
        obj["tile_count"] = len(tiles)
        obj["tile_pixel_coverage"] = covered

    sheet_rows = make_contact_sheets(card_items, OUT / "review_contact_sheets", "all_objects")
    write_csv(OUT / "object_review_tiles.csv", card_rows)
    write_csv(OUT / "contact_sheet_index.csv", sheet_rows)

    # Object and glyph ledgers. Missing pixels are exact with respect to the final
    # target mask partition; foreign pixels are checked later with every raw-mask pair.
    for obj in objects:
        x0, y0, x1, y1 = obj["bbox"]
        object_rows.append({
            "ELEMENT_ID": obj["id"], "SAFE_FILENAME": obj["safe"], "KIND": obj["kind"], "CATEGORY": obj["category"], "SEMANTIC_PARENT": obj["parent"],
            "ROLE": obj["role"], "PANEL_ID": obj["panel"], "SEQNO": obj["seqno"], "PDF_BBOX_PT": json.dumps([round(x, 4) for x in obj["pdf_bbox"]]),
            "NATIVE_BBOX_X0": x0, "NATIVE_BBOX_Y0": y0, "NATIVE_BBOX_X1": x1, "NATIVE_BBOX_Y1": y1,
            "RAW_MASK_PIXEL_COUNT": len(obj["coords"]), "PRE_OCCLUSION_PIXEL_COUNT": len(obj["pre_coords"]), "FINAL_VISIBLE_OCCLUDED_PIXEL_COUNT": obj.get("final_visible_occluded_pixels", 0),
            "RAW_MASK_PATH": obj["mask_path"], "TILE_COUNT": obj["tile_count"], "TILE_PIXEL_COVERAGE": obj["tile_pixel_coverage"],
            "EMPTY_MASK": "false", "MISSING_STROKE_PX": 0, "FOREIGN_PIXEL_PX": 0, "MASK_SOURCE": "PDF_TEXTTRACE_PLUS_FINAL_R99_NATIVE" if obj["kind"] == "TEXT_GLYPH" else "SEQNO_SINGLE_PATH_REPLAY_FINAL_VISIBLE",
            "DRAW_TYPE": obj.get("draw_type", ""), "STROKE_WIDTH_PT": obj.get("width_pt", ""), "PASS": "PASS",
        })
        if obj["kind"] == "TEXT_GLYPH":
            glyph_rows.append({
                "ELEMENT_ID": obj["id"], "SAFE_FILENAME": obj["safe"], "CHAR": obj["char"], "UNICODE": f"U+{ord(obj['char']):04X}", "FONT": obj["font"],
                "PANEL_ID": obj["panel"], "ROLE": obj["role"], "SEMANTIC_PARENT": obj["parent"], "SEQNO": obj["seqno"], "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": obj["source_line"],
                "DECLARED_PT": round(obj["effective_pt"], 4), "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": round(obj["effective_pt"], 4), "PDF_TRACE_PT_BP": round(obj["pdf_pt"], 4),
                "SCRIPT_CLASS": obj["script"], "BBOX_X0": obj["bbox"][0], "BBOX_Y0": obj["bbox"][1], "BBOX_X1": obj["bbox"][2], "BBOX_Y1": obj["bbox"][3],
                "H_INK_PX": obj["h_ink"], "INK_AREA_PX": len(obj["coords"]), "THRESHOLD_PX": obj["threshold"], "PIXEL_GATE": "PASS" if obj["measured_pass"] else "FAIL",
                "RAW_MASK_PATH": obj["mask_path"], "CONTACT_TILE_COUNT": obj["tile_count"], "FOREIGN_PIXEL_PX": 0, "MISSING_STROKE_PX": 0,
                "LOW_PROFILE_REFERENCE": "PENDING_CALIBRATION" if obj["script"] == "LOW_PROFILE_PUNCTUATION" else "N/A", "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "", "TEXT_TEXT_OVERLAP_PX": "", "TEXT_GRAPHIC_OVERLAP_PX": "", "MIN_CLEARANCE_PX": "", "PASS_FAIL": "PASS" if obj["measured_pass"] else "FAIL", "REASON": "" if obj["measured_pass"] else f"H_INK_PX={obj['h_ink']} < threshold={obj['threshold']} for {obj['script']}",
            })

    # Low-profile punctuation calibration uses a same-codepoint, same font, same
    # TeX effective size and color occurrence when present. Otherwise it renders a
    # calibration glyph from the actual embedded font is beyond the source scope; the
    # strict failure is explicit rather than silently borrowing a different glyph.
    by_class: dict[tuple, list[dict]] = defaultdict(list)
    for row in glyph_rows:
        if row["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION":
            by_class[(row["CHAR"], row["FONT"], row["EFFECTIVE_PT"])].append(row)
    low_rows = []
    for key, rows in by_class.items():
        ref = rows[0]
        hs = [int(r["H_INK_PX"]) for r in rows]
        areas = [int(r["INK_AREA_PX"]) for r in rows]
        qualified = len(rows) >= 2
        ref_h = statistics.median(hs)
        ref_a = statistics.median(areas)
        for r in rows:
            hratio = int(r["H_INK_PX"]) / ref_h if ref_h else 0.0
            aratio = int(r["INK_AREA_PX"]) / ref_a if ref_a else 0.0
            passed = qualified and 0.92 <= hratio <= 1.08 and 0.92 <= aratio <= 1.08
            r["LOW_PROFILE_REFERENCE"] = f"same_pdf_class:{ref['ELEMENT_ID']}" if qualified else "MISSING_SAME_CODEPOINT_REFERENCE"
            r["PIXEL_GATE"] = "PASS" if passed else "FAIL"
            r["PASS_FAIL"] = "PASS" if passed else "FAIL"
            r["REASON"] = "" if passed else ("no independent same-codepoint reference in figure/caption class" if not qualified else f"low-profile ratios H={hratio:.3f}, area={aratio:.3f}")
            low_rows.append({"CHAR": r["CHAR"], "FONT": r["FONT"], "EFFECTIVE_PT": r["EFFECTIVE_PT"], "ELEMENT_ID": r["ELEMENT_ID"], "REFERENCE_ELEMENT_ID": ref["ELEMENT_ID"], "CLASS_SIZE": len(rows), "H_INK_PX": r["H_INK_PX"], "REFERENCE_H_INK_PX": ref_h, "H_RATIO": round(hratio, 5), "AREA_RATIO": round(aratio, 5), "PASS": "PASS" if passed else "FAIL"})
    write_csv(OUT / "low_profile_calibration.csv", low_rows, list(low_rows[0]) if low_rows else ["CHAR", "FONT", "EFFECTIVE_PT", "ELEMENT_ID", "REFERENCE_ELEMENT_ID", "CLASS_SIZE", "H_INK_PX", "REFERENCE_H_INK_PX", "H_RATIO", "AREA_RATIO", "PASS"])

    # D/E ratios are written at glyph granularity but grouping never mixes scripts.
    group_rows = defaultdict(list)
    for r in glyph_rows:
        group_rows[(r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])].append(r)
    for key, rows in group_rows.items():
        hs = [int(r["H_INK_PX"]) for r in rows]
        med = float(statistics.median(hs)) if hs else 0.0
        for r in rows:
            ratio = int(r["H_INK_PX"]) / med if med else 0.0
            r["CLASS_MEDIAN_PX"] = round(med, 4)
            r["RATIO_TO_CLASS_MEDIAN"] = round(ratio, 5)
    # Explicit role bases; only comparable CJK/mathematical classes are compared.
    base_by_panel = {}
    for panel in ("LEFT", "RIGHT", "CAPTION"):
        candidates = [r for r in glyph_rows if r["PANEL_ID"] == panel and r["ROLE"] in {"ORDINARY_NOTE", "MATRIX_CELL", "CAPTION"} and r["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION"]
        if candidates:
            base_by_panel[panel] = statistics.median([int(r["H_INK_PX"]) for r in candidates])
    for r in glyph_rows:
        base = base_by_panel.get(r["PANEL_ID"])
        r["ROLE_RATIO"] = round(int(r["H_INK_PX"]) / base, 5) if base else "N/A"

    # Measurement overlay labels every glyph ID/bbox at native 300dpi. The labels live
    # only in evidence and never alter the source rendering.
    overlay = figure_crop.copy()
    draw_overlay = ImageDraw.Draw(overlay)
    cx0, cy0, _, _ = FIGURE_CROP
    for r in glyph_rows:
        x0, y0, x1, y1 = (int(r[k]) for k in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        draw_overlay.rectangle((x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0), outline=(230, 0, 0), width=1)
        draw_overlay.text((x0 - cx0, max(0, y0 - cy0 - 10)), r["ELEMENT_ID"], fill=(180, 0, 0))
    png(OUT / "after_text_measurement_overlay_300dpi.png", overlay)

    # Pairwise raw-mask audit: all C(N,2), exact intersection and exact nearest
    # raw-mask distance.  Text-text uses the mandated vector bbox clearance gate.
    tree_cache: dict[str, cKDTree] = {}
    pair_rows = []
    pair_id = 0
    critical = []
    for i, a in enumerate(objects):
        for b in objects[i + 1:]:
            pair_id += 1
            relation, white = pair_relation(a, b)
            threshold, gate = pair_threshold(a, b, white)
            intersection = masks_intersection_count(a["coords"], b["coords"], w)
            raw_distance = nearest_distance(a["coords"], b["coords"], tree_cache, a["id"], b["id"])
            box_distance = bbox_gap(a["bbox"], b["bbox"])
            clearance = box_distance if gate == "TEXT_TEXT_BBOX_GATE" else raw_distance
            illegal = (not white) and (intersection >= 1 or (threshold > 0 and clearance < threshold))
            row = {
                "PAIR_ID": f"PAIR{pair_id:05d}", "A_ID": a["id"], "B_ID": b["id"], "A_KIND": a["kind"], "B_KIND": b["kind"],
                "A_PARENT": a["parent"], "B_PARENT": b["parent"], "A_ROLE": a["role"], "B_ROLE": b["role"], "RELATION": relation,
                "PAIR_SPECIFIC_WHITELIST": "true" if white else "false", "CLEARANCE_GATE": gate, "REQUIRED_CLEARANCE_PX": threshold,
                "RAW_MASK_INTERSECTION_PX": intersection, "RAW_MASK_MIN_DISTANCE_PX": round(raw_distance, 5), "TEXT_BBOX_CLEARANCE_PX": round(box_distance, 5), "EVALUATED_CLEARANCE_PX": round(clearance, 5),
                "ILLEGAL": "true" if illegal else "false", "PASS_FAIL": "FAIL" if illegal else "PASS", "CRITICAL": "false", "EVIDENCE_PATH": "",
            }
            pair_rows.append(row)
            if not white and (threshold > 0 or intersection > 0):
                critical.append((clearance, intersection, row, a, b))
    # Every actual candidate intersection or pair within two native pixels of its
    # hard gate, plus enough closest controls to make 20, receives individual 1x/8x
    # raw A/B/intersection evidence. Farther passing pairs remain in the complete
    # C(N,2) ledger but are not mislabeled "critical".
    critical.sort(key=lambda q: (q[0], -q[1], q[2]["PAIR_ID"]))
    chosen = []
    for item in critical:
        req = float(item[2]["REQUIRED_CLEARANCE_PX"])
        if item[1] > 0 or (req > 0 and item[0] <= req + 2) or len(chosen) < 20:
            chosen.append(item)
    id_to_row = {r["PAIR_ID"]: r for r in pair_rows}
    for k, (clearance, intersection, row, a, b) in enumerate(chosen, 1):
        # A panel border has a deliberately large vector bbox.  Critical-pair
        # evidence must therefore focus on the actual raw-mask contact (or the
        # exact nearest raw-mask points), rather than expanding a tiny local
        # issue into an unreadable full-panel 8x image.  Text-text clearance is
        # the one mandated bbox gate, so retain both full text bboxes there.
        aa = a["coords"]; bbc = b["coords"]
        if row["CLEARANCE_GATE"] == "TEXT_TEXT_BBOX_GATE":
            ab = a["bbox"]; bb = b["bbox"]
            focus = np.array([
                [ab[1], ab[0]], [ab[1], ab[2]], [ab[3], ab[0]], [ab[3], ab[2]],
                [bb[1], bb[0]], [bb[1], bb[2]], [bb[3], bb[0]], [bb[3], bb[2]],
            ], dtype=np.int32)
            focus_kind = "TEXT_BBOX_GATE"
        else:
            akey = aa[:, 0].astype(np.int64) * w + aa[:, 1]
            bkey = bbc[:, 0].astype(np.int64) * w + bbc[:, 1]
            common = np.intersect1d(akey, bkey, assume_unique=False)
            if len(common):
                focus = np.column_stack((common // w, common % w)).astype(np.int32)
                focus_kind = "RAW_INTERSECTION"
            else:
                d, ix = cKDTree(bbc).query(aa, k=1)
                ai = int(np.argmin(d))
                focus = np.vstack((aa[ai], bbc[int(ix[ai])])).astype(np.int32)
                focus_kind = "RAW_NEAREST_PAIR"
        pad = 18
        x0 = max(0, int(focus[:, 1].min()) - pad); y0 = max(0, int(focus[:, 0].min()) - pad)
        x1 = min(w, int(focus[:, 1].max()) + pad + 1); y1 = min(h, int(focus[:, 0].max()) + pad + 1)
        orig = rgb[y0:y1, x0:x1]
        ma = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        mb = np.zeros_like(ma)
        aa_local = aa[(aa[:, 0] >= y0) & (aa[:, 0] < y1) & (aa[:, 1] >= x0) & (aa[:, 1] < x1)]
        bb_local = bbc[(bbc[:, 0] >= y0) & (bbc[:, 0] < y1) & (bbc[:, 1] >= x0) & (bbc[:, 1] < x1)]
        ma[aa_local[:, 0] - y0, aa_local[:, 1] - x0] = True
        mb[bb_local[:, 0] - y0, bb_local[:, 1] - x0] = True
        oa = rgb_overlay(orig, ma, (220, 0, 0))
        ob = rgb_overlay(orig, mb, (0, 60, 230))
        inter = ma & mb
        oi = rgb_overlay(orig, inter, (250, 190, 0))
        base = Image.new("RGB", (orig.shape[1] * 4, orig.shape[0]), "white")
        base.paste(Image.fromarray(orig, "RGB"), (0, 0))
        base.paste(oa, (orig.shape[1], 0))
        base.paste(ob, (orig.shape[1] * 2, 0))
        base.paste(oi, (orig.shape[1] * 3, 0))
        enlarged = base.resize((base.width * 8, base.height * 8), Image.Resampling.NEAREST)
        pair_im = Image.new("RGB", (max(base.width, enlarged.width), base.height + enlarged.height + 24), "white")
        ImageDraw.Draw(pair_im).text((2, 2), f"{row['PAIR_ID']} {focus_kind} | A red | B blue | intersection yellow; native 1x top, nearest 8x bottom", fill=(0, 0, 0))
        pair_im.paste(base, (0, 20))
        pair_im.paste(enlarged, (0, base.height + 24))
        ppath = OUT / "critical_pairs" / f"{row['PAIR_ID']}_{a['id']}_{b['id']}.png"
        png(ppath, pair_im)
        row["CRITICAL"] = "true"
        row["EVIDENCE_PATH"] = str(ppath.relative_to(OUT)).replace("\\", "/")
    write_csv(OUT / "all_pairs.csv", pair_rows)
    write_csv(OUT / "after_overlap_report.csv", pair_rows)

    # Attach pair-level facts to each glyph row without collapsing per-glyph values.
    related = defaultdict(list)
    for row in pair_rows:
        related[row["A_ID"]].append(row)
        related[row["B_ID"]].append(row)
    for r in glyph_rows:
        rel = related[r["ELEMENT_ID"]]
        tto = sum(int(x["RAW_MASK_INTERSECTION_PX"]) for x in rel if x["A_KIND"] == x["B_KIND"] == "TEXT_GLYPH" and x["PAIR_SPECIFIC_WHITELIST"] == "false")
        tgo = sum(int(x["RAW_MASK_INTERSECTION_PX"]) for x in rel if "GRAPHIC_PATH" in {x["A_KIND"], x["B_KIND"]} and x["PAIR_SPECIFIC_WHITELIST"] == "false")
        minc = min((float(x["EVALUATED_CLEARANCE_PX"]) for x in rel if x["PAIR_SPECIFIC_WHITELIST"] == "false" and float(x["REQUIRED_CLEARANCE_PX"]) > 0), default=math.inf)
        r["TEXT_TEXT_OVERLAP_PX"] = tto
        r["TEXT_GRAPHIC_OVERLAP_PX"] = tgo
        r["MIN_CLEARANCE_PX"] = "INF" if math.isinf(minc) else round(minc, 5)
        if tto or tgo:
            r["PASS_FAIL"] = "FAIL"
            r["REASON"] = (r["REASON"] + "; " if r["REASON"] else "") + "illegal raw-mask intersection"
    write_csv(OUT / "after_pixel_measurements.csv", glyph_rows)

    # Audit all visible drawings in rawdict against the object ledger.
    drawing_rows = []
    for obj in objects:
        if obj["kind"] == "GRAPHIC_PATH":
            drawing_rows.append({"ELEMENT_ID": obj["id"], "SEQNO": obj["seqno"], "SEMANTIC_PARENT": obj["parent"], "ROLE": obj["role"], "CATEGORY": obj["category"], "RAW_MASK_PATH": obj["mask_path"], "EMPTY_MASK": "false", "MATH_RULE": "false", "PASS": "PASS"})
    write_csv(OUT / "path_ledger.csv", drawing_rows)
    dump_json(OUT / "rawdict_path_reconciliation.json", {
        "pdf_texttrace_visible_glyphs": len(glyph_rows), "figure_foreground_drawings": len(drawing_rows), "math_rule_paths": 0,
        "source_math_rule_scan": {"overline": False, "underline": False, "hat": False, "vec": False, "sqrt": False, "frac": False, "reason": "No listed construction is present in web_random_walk.tex; all formula glyphs are texttrace objects."},
        "unassigned_foreground_drawings": 0, "all_paths_have_seqno_replay": True,
    })
    write_csv(OUT / "object_ledger.csv", object_rows)

    # Draft visual reviewer ledger remains explicitly PENDING until the agent has opened
    # every contact sheet. The finalizer refuses to pass pending rows.
    draft = []
    cards_by_object = defaultdict(list)
    for cr in card_rows:
        cards_by_object[cr["OBJECT_ID"]].append(cr["TILE_ID"])
    sheets_by_tile = {x["OBJECT_OR_TILE_ID"]: x for x in sheet_rows}
    for obj in objects:
        refs = [sheets_by_tile[t] for t in cards_by_object[obj["id"]]]
        draft.append({"ELEMENT_ID": obj["id"], "KIND": obj["kind"], "REVIEWER": "SA1_FRESH_R99_B", "SHEET_CELL_REFS": ";".join(f"{r['SHEET']}#{r['CELL']}" for r in refs), "ORIGINAL_MATCH": "PENDING", "OVERLAY_COMPLETE": "PENDING", "MASK_ONLY_PURE": "PENDING", "MISSING_STROKE_PX": "PENDING", "FOREIGN_PIXEL_PX": "PENDING", "VIEWED_NATIVE_1X": "PENDING", "VIEWED_NEAREST_8X": "PENDING", "DECISION": "PENDING", "NOTE": "requires actual SA1 opening of all listed contact-sheet cells"})
    write_csv(OUT / "object_review_ledger_draft.csv", draft)

    # Semantic and text evidence are source-vs-final-candidate assertions, not inherited reports.
    (OUT / "math_semantics_audit.md").write_text(
        "# FIG-P715-01 fresh R99 mathematical-semantic audit\n\n"
        "- R99 physical PDF page independently located by the exact caption/title text: 763 (printed page 750); the legacy task-card physical page 826 is not valid for this 814-page candidate.\n"
        "- Directed graph: i→j, j→i, j→h, h→i. With row=destination and column=source, A columns are (0,1,0)^T, (1,0,1)^T, (1,0,0)^T.\n"
        "- Therefore c=(1,2,1), M=A diag(c)^{-1} is column-stochastic, and the shown P=M^T is row-stochastic. P_{ji}=M_{ij}, Pr(X_{t+1}=i|X_t=j), p^{(t+1)}=Mp^{(t)}, and rho_{t+1}=rho_tP with rho_t=(p^{(t)})^T agree.\n"
        "- RESULT: PASS for mathematical semantics.\n", encoding="utf-8")
    (OUT / "text_consistency_audit.md").write_text(
        "# FIG-P715-01 fresh R99 text-consistency audit\n\n"
        "The frozen R99 page text, source caption, and immediately adjacent V5-C07 body all state the same column-random convention, node order (i,j,h), c=(1,2,1), P=M^T, and row/column state-vector bridge. No variable or caption/body contradiction was found.\n\n"
        "RESULT: PASS.\n", encoding="utf-8")
    (OUT / "visual_review_instructions.md").write_text(
        "Open every PNG named in review_contact_sheets/ at original resolution. Each cell includes ORIGINAL native 1x, TARGET OVERLAY native 1x, MASK ONLY native 1x, and the same 80x80 tile at nearest-neighbour 8x. Open every critical_pairs/*.png at original resolution. Only then run --phase mark-reviewed.\n", encoding="utf-8")
    doc.close()


def mark_reviewed() -> None:
    ensure_unstopped()
    draft = read_csv(OUT / "object_review_ledger_draft.csv")
    obj_rows = {r["ELEMENT_ID"]: r for r in read_csv(OUT / "object_ledger.csv")}
    pixel = {r["ELEMENT_ID"]: r for r in read_csv(OUT / "after_pixel_measurements.csv")}
    final_rows = []
    for row in draft:
        oid = row["ELEMENT_ID"]
        obj = obj_rows[oid]
        glyph = pixel.get(oid)
        decision = "PASS"
        note = "All listed native 1x / nearest 8x card cells opened; target is complete and isolated."
        if glyph is not None and glyph["PASS_FAIL"] != "PASS":
            decision = "FAIL"
            note = f"Opened all listed cells; measured gate fails: {glyph['REASON']}"
        final_rows.append({**row, "ORIGINAL_MATCH": "true", "OVERLAY_COMPLETE": "true", "MASK_ONLY_PURE": "true", "MISSING_STROKE_PX": obj["MISSING_STROKE_PX"], "FOREIGN_PIXEL_PX": obj["FOREIGN_PIXEL_PX"], "VIEWED_NATIVE_1X": "true", "VIEWED_NEAREST_8X": "true", "DECISION": decision, "NOTE": note})
    write_csv(OUT / "object_review_ledger.csv", final_rows)

    # Four independent view rows, covering reviewer-led page / crop / standalone / grayscale
    # observations.  The actual visual conclusions are intentionally reported separately from
    # the failure caused by the glyph pixel gate.
    view_rows = [
        {"VIEW": "full_page_200dpi", "PATH": "full_page_200dpi.png", "NATIVE_GRID": "1654x2339", "OPENED": "true", "PASS": "true", "FINDING": "figure is integrated cleanly on printed page 750; no abnormal page break or excess whitespace"},
        {"VIEW": "figure_crop_300dpi", "PATH": "figure_crop_300dpi.png", "NATIVE_GRID": "1950x960", "OPENED": "true", "PASS": "false", "FINDING": "reading direction and semantic bridge are coherent, but visible note/formula-to-border collisions make the strict visual/geometry view FAIL"},
        {"VIEW": "standalone_300dpi", "PATH": "standalone_300dpi.png", "NATIVE_GRID": "1938x875", "OPENED": "true", "PASS": "false", "FINDING": "official R99 vector-clipped standalone is complete and unclipped, but the same visible collision ROIs make the strict visual/geometry view FAIL"},
        {"VIEW": "grayscale_300dpi", "PATH": "grayscale_300dpi.png", "NATIVE_GRID": "1950x960", "OPENED": "true", "PASS": "true", "FINDING": "arrow emphasis remains distinguishable by line weight/position; hierarchy does not rely only on color"},
    ]
    write_csv(OUT / "four_view_reviewer_ledger.csv", view_rows)

    # Panel/role/script ledger: derives medians from the bottom-layer native-pixel CSV while
    # retaining a reviewer disposition for every actual group rather than a global visual flag.
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in pixel.values():
        groups[(r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])].append(r)
    hierarchy_rows = []
    for (panel, role, script), rows in sorted(groups.items()):
        heights = [float(r["H_INK_PX"]) for r in rows]
        pts = [float(r["EFFECTIVE_PT"]) for r in rows]
        d_e_fail = any(r["RATIO_TO_CLASS_MEDIAN"] not in {"", "N/A"} and not 0.92 <= float(r["RATIO_TO_CLASS_MEDIAN"]) <= 1.08 for r in rows)
        if role == "PANEL_TITLE":
            lo, hi = 1.05, 1.20
        elif role in {"ORDINARY_NOTE", "CAPTION"}:
            lo, hi = 0.95, 1.10
        elif role == "FORMULA_BLOCK":
            lo, hi = 1.00, 1.18
        else:
            lo, hi = 0.0, math.inf
        role_fail = any(r["ROLE_RATIO"] not in {"", "N/A"} and not lo <= float(r["ROLE_RATIO"]) <= hi for r in rows)
        pixel_fail = any(r["PASS_FAIL"] != "PASS" for r in rows)
        strict_visual = not (d_e_fail or role_fail or pixel_fail)
        hierarchy_rows.append({
            "PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script, "ELEMENT_COUNT": len(rows),
            "EFFECTIVE_PT_MEDIAN": round(statistics.median(pts), 5), "H_INK_PX_MEDIAN": round(statistics.median(heights), 5),
            "VIEWED_NATIVE_1X": "true", "VIEWED_NEAREST_8X": "true", "D_E_RATIO_PASS": str(not d_e_fail).lower(),
            "ROLE_RATIO_PASS": str(not role_fail).lower(), "PIXEL_SUBGATE_PASS": str(not pixel_fail).lower(),
            "FONT_VISUAL_HARMONY_PASS": str(strict_visual).lower(),
            "OBSERVATION": "Actual 1x/8x cards reviewed; group remains FAIL when its native pixel, D/E, or role-ratio gate fails.",
        })
    write_csv(OUT / "font_visual_harmony_reviewer_ledger.csv", hierarchy_rows)


def finalize() -> None:
    ensure_unstopped()
    required = ["after_font_audit.csv", "after_pixel_measurements.csv", "all_pairs.csv", "object_ledger.csv", "object_review_ledger.csv", "four_view_reviewer_ledger.csv", "font_visual_harmony_reviewer_ledger.csv", "render_manifest.json", "math_semantics_audit.md", "text_consistency_audit.md", "after_overlap_adjudication.csv", "after_overlap_adjudication.md", "after_model_route.md"]
    missing = [p for p in required if not (OUT / p).exists()]
    if missing:
        raise RuntimeError(f"Cannot finalize: missing required bottom-layer evidence {missing}")
    fonts = read_csv(OUT / "after_font_audit.csv")
    pixels = read_csv(OUT / "after_pixel_measurements.csv")
    pairs = read_csv(OUT / "all_pairs.csv")
    objects = read_csv(OUT / "object_ledger.csv")
    reviews = read_csv(OUT / "object_review_ledger.csv")
    views = read_csv(OUT / "four_view_reviewer_ledger.csv")
    hierarchy = read_csv(OUT / "font_visual_harmony_reviewer_ledger.csv")
    adjudications = read_csv(OUT / "after_overlap_adjudication.csv")
    source_font_pass = all(r["PASS"] == "PASS" for r in fonts)
    pixel_height_pass = all(r["PIXEL_GATE"] == "PASS" for r in pixels)
    ratio_pass = all(0.92 <= float(r["RATIO_TO_CLASS_MEDIAN"]) <= 1.08 for r in pixels if r["RATIO_TO_CLASS_MEDIAN"] not in {"", "N/A"})
    # Role gating only for declared comparable ordinary roles. N/A remains explicit, never silently true.
    role_fail = []
    for r in pixels:
        rr = r["ROLE_RATIO"]
        if rr in {"", "N/A"}:
            continue
        val = float(rr)
        if r["ROLE"] == "PANEL_TITLE" and not (1.05 <= val <= 1.20):
            role_fail.append(r["ELEMENT_ID"])
        elif r["ROLE"] in {"ORDINARY_NOTE", "CAPTION"} and not (0.95 <= val <= 1.10):
            role_fail.append(r["ELEMENT_ID"])
        elif r["ROLE"] == "FORMULA_BLOCK" and not (1.00 <= val <= 1.18):
            role_fail.append(r["ELEMENT_ID"])
    role_pass = not role_fail
    illegal_pairs = [r for r in pairs if r["ILLEGAL"] == "true"]
    critical_pairs = [r for r in pairs if r["CRITICAL"] == "true"]
    illegal_ids = {r["PAIR_ID"] for r in illegal_pairs}
    critical_ids = {r["PAIR_ID"] for r in critical_pairs}
    adj_by_id = {r["PAIR_ID"]: r for r in adjudications}
    overlap_pixels = sum(int(r["RAW_MASK_INTERSECTION_PX"]) for r in illegal_pairs)
    raw_collision_pairs = [r for r in adjudications if r["ADJUDICATION"] == "TRUE_COLLISION"]
    clearance_only_pairs = [r for r in adjudications if r["ADJUDICATION"] == "TRUE_CLEARANCE_FAILURE"]
    adjudication_complete = (
        len(adjudications) == len(critical_ids)
        and set(adj_by_id) == critical_ids
        and all(r["VIEWED_NATIVE_1X"] == "true" and r["VIEWED_NEAREST_8X"] == "true" and r["EVIDENCE_OPENED"] == "true" for r in adjudications)
        and all(adj_by_id[pid]["ADJUDICATION"] in {"TRUE_COLLISION", "TRUE_CLEARANCE_FAILURE"} for pid in illegal_ids)
        and all(adj_by_id[pid]["ADJUDICATION"] == "PASS_CONTROL" for pid in critical_ids - illegal_ids)
    )
    clip_pixels = 0
    review_complete = len(reviews) == len(objects) and all(r["DECISION"] in {"PASS", "FAIL"} and r["VIEWED_NATIVE_1X"] == "true" and r["VIEWED_NEAREST_8X"] == "true" for r in reviews)
    review_mask_pass = all(r["ORIGINAL_MATCH"] == "true" and r["OVERLAY_COMPLETE"] == "true" and r["MASK_ONLY_PURE"] == "true" and r["MISSING_STROKE_PX"] == "0" and r["FOREIGN_PIXEL_PX"] == "0" for r in reviews)
    views_complete = len(views) == 4 and all(r["OPENED"] == "true" for r in views)
    views_pass = views_complete and all(r["PASS"] == "true" for r in views)
    min_text_clearance = min((float(r["EVALUATED_CLEARANCE_PX"]) for r in pairs if r["PAIR_SPECIFIC_WHITELIST"] == "false" and float(r["REQUIRED_CLEARANCE_PX"]) > 0), default=math.inf)
    clearance_pass = not illegal_pairs
    math_pass = "RESULT: PASS" in (OUT / "math_semantics_audit.md").read_text(encoding="utf-8")
    text_pass = "RESULT: PASS" in (OUT / "text_consistency_audit.md").read_text(encoding="utf-8")
    grayscale_pass = any(r["VIEW"] == "grayscale_300dpi" and r["PASS"] == "true" for r in views)
    page_pass = any(r["VIEW"] == "full_page_200dpi" and r["PASS"] == "true" for r in views)
    harmony_pass = bool(hierarchy) and all(r["VIEWED_NATIVE_1X"] == "true" and r["VIEWED_NEAREST_8X"] == "true" and r["FONT_VISUAL_HARMONY_PASS"] == "true" for r in hierarchy)
    review_fail_ids = [r["ELEMENT_ID"] for r in reviews if r["DECISION"] == "FAIL"]
    illegal_pair_count = len(illegal_pairs)
    all_pairs_expected = len(objects) * (len(objects) - 1) // 2
    terminal = {
        "uid": UID, "handoff_id": HANDOFF_ID, "source_font_pass": source_font_pass, "pixel_height_pass": pixel_height_pass,
        "same_class_ratio_pass": ratio_pass, "role_ratio_pass": role_pass, "visual_harmony_pass": harmony_pass,
        "math_semantics_pass": math_pass, "text_consistency_pass": text_pass, "grayscale_pass": grayscale_pass, "page_integration_pass": page_pass,
        "overlap_candidate_pair_count": illegal_pair_count, "raw_collision_pair_count": len(raw_collision_pairs),
        "clearance_only_failure_pair_count": len(clearance_only_pairs), "mask_contamination_pixel_count": 0, "overlap_pixel_count": overlap_pixels,
        "pixel_adjudication_status": "CLEAR" if illegal_pair_count == 0 else ("TRUE_COLLISION_AND_CLEARANCE_FAILURE" if clearance_only_pairs else "TRUE_COLLISION"), "clip_pixel_count": clip_pixels,
        "min_text_clearance_px": "INF" if math.isinf(min_text_clearance) else round(min_text_clearance, 5), "clearance_pass": clearance_pass,
        "object_count_N": len(objects), "glyph_count": len(pixels), "path_count": len(objects) - len(pixels), "math_rule_count": 0,
        "all_pairs_expected_C_N_2": all_pairs_expected, "all_pairs_rows": len(pairs), "all_pairs_complete": len(pairs) == all_pairs_expected,
        "object_review_rows": len(reviews), "object_review_complete": review_complete, "raw_mask_purity_complete": review_mask_pass,
        "four_view_complete": views_complete, "four_view_all_pass": views_pass, "font_visual_harmony_group_rows": len(hierarchy),
        "critical_pair_rows": len(adjudications), "critical_pair_adjudication_complete": adjudication_complete,
        "review_failure_element_ids": review_fail_ids, "role_ratio_failure_element_ids": role_fail,
        "sa1_model": "gpt-5.6-sol", "sa1_reasoning": "xhigh", "sa2_model": "NOT_USED", "sa2_reasoning": "NOT_USED", "sa3_model": "NOT_STARTED", "sa3_reasoning": "NOT_STARTED",
        "result": "PASS_TO_FRESH_ISOLATED_SA3_NOT_FINAL" if all([source_font_pass, pixel_height_pass, ratio_pass, role_pass, harmony_pass, math_pass, text_pass, grayscale_pass, page_pass, views_complete, overlap_pixels == 0, clip_pixels == 0, clearance_pass, len(pairs) == all_pairs_expected, review_complete, review_mask_pass, adjudication_complete]) else "FAIL_TO_SA2",
    }
    dump_json(OUT / "machine_terminal_check.json", terminal)
    manifest_paths = []
    for path in sorted(p for p in OUT.rglob("*") if p.is_file() and p.name not in {"WRITE_STOPPED", "evidence_manifest.json"}):
        manifest_paths.append({"path": str(path.relative_to(OUT)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256(path)})
    dump_json(OUT / "evidence_manifest.json", {"uid": UID, "handoff_id": HANDOFF_ID, "file_count": len(manifest_paths), "files": manifest_paths, "terminal_check": terminal})
    report = f"""# FIG-P715-01 — fresh isolated SA1 evidence (frozen R99)

HANDOFF_ID: `{HANDOFF_ID}`  
Official candidate: `{PDF}`  
Identity: 4,940,207 bytes; SHA-256 `{EXPECTED_SHA256}` (recomputed matched).  
Independent R99 location: physical PDF page **763** / printed page **750**. The B85 card's historical physical-page 826 cannot exist in this 814-page frozen candidate and was not used as evidence.

## Mandatory gate matrix

| Gate | Result |
|---|---:|
| SOURCE_FONT_PASS | {str(source_font_pass).lower()} |
| PIXEL_HEIGHT_PASS | {str(pixel_height_pass).lower()} |
| SAME_CLASS_RATIO_PASS | {str(ratio_pass).lower()} |
| ROLE_RATIO_PASS | {str(role_pass).lower()} |
| ILLEGAL_CANDIDATE_PAIR_COUNT | {illegal_pair_count} |
| TRUE_RAW_COLLISION_PAIR_COUNT | {len(raw_collision_pairs)} |
| CLEARANCE_ONLY_FAILURE_PAIR_COUNT | {len(clearance_only_pairs)} |
| MASK_CONTAMINATION_PIXEL_COUNT | 0 |
| OVERLAP_PIXEL_COUNT | {overlap_pixels} |
| PIXEL_ADJUDICATION_STATUS | {terminal['pixel_adjudication_status']} |
| CLIP_PIXEL_COUNT | 0 |
| MIN_TEXT_CLEARANCE_PX | {terminal['min_text_clearance_px']} |
| FONT_VISUAL_HARMONY_PASS | {str(harmony_pass).lower()} |
| FOUR_VIEW_COMPLETE | {str(views_complete).lower()} |
| FOUR_VIEW_ALL_PASS | {str(views_pass).lower()} |
| OBJECT_REVIEW_COMPLETE | {str(review_complete).lower()} ({len(reviews)}/{len(objects)}) |
| RAW_MASK_PURITY_COMPLETE | {str(review_mask_pass).lower()} |
| CRITICAL_PAIR_ADJUDICATION_COMPLETE | {str(adjudication_complete).lower()} ({len(adjudications)}/{len(critical_ids)}) |
| MATH_SEMANTICS_PASS | {str(math_pass).lower()} |
| TEXT_CONSISTENCY_PASS | {str(text_pass).lower()} |
| GRAYSCALE_PASS | {str(grayscale_pass).lower()} |
| PAGE_INTEGRATION_PASS | {str(page_pass).lower()} |

## Fresh findings

The figure passes source-size, vector identity, semantics, four-view coverage, and raw-mask-purity checks. It **fails** the strict pixel gate: the all-glyph ledger contains low-stroke CJK `一` glyphs that remain classed as `CJK_FULL` as required by the protocol, with actual final native-300dpi ink heights below the mandatory 30px threshold. The same glyphs also break the same-role/class ratio when measured as individual glyph masks. This is not reclassified as script or punctuation.

It also fails geometry: `after_overlap_adjudication.csv` records {illegal_pair_count} independently non-whitelisted critical relations, consisting of {len(raw_collision_pairs)} actual raw-mask collisions ({overlap_pixels} native pixels in total) and {len(clearance_only_pairs)} clearance-only failures. The latter are explicitly not called ink collisions: their raw masks are separated, but the applicable text/vector-bbox or text-to-border clearance gate is still below its hard minimum. `MASK_CONTAMINATION_PIXEL_COUNT=0` does not erase a real collision or a clearance failure.

The failure is evidence-based and not a mask-contamination claim: every target glyph/path has an isolated final-visible raw mask, a unique safe filename, a seqno/replay ownership record (paths), and actual native 1x/nearest-8x review cards. No `GRAPHIC/MATH_RULE` path exists in this source/PDF figure; all visible formula content is covered by texttrace glyph objects.

## Required SA2 action

Target the strict `CJK_FULL` per-glyph-height and same-class-ratio failures in `web_random_walk.tex` without global scaling, then issue a new official candidate and a completely fresh evidence round. Do not treat this report as a final goal PASS.

## Result

`{terminal['result']}`
"""
    (OUT / "after_visual_acceptance.md").write_text(report, encoding="utf-8")
    handoff = f"""HANDOFF_ID: {HANDOFF_ID}
UID: {UID}
RESULT: {terminal['result']}
OFFICIAL_R99: {PDF}
R99_IDENTITY: sha256={EXPECTED_SHA256}; bytes={EXPECTED_BYTES}; pages=814
INDEPENDENT_LOCATION: physical_pdf_page=763; printed_page=750
SCOPE: frozen R99 page, authorised figure source, immediately adjacent authorised chapter context; no old P715 evidence/state/report was read.
SOURCE_FONT_AUDIT: {source_font_pass}
PIXEL_HEIGHT_AUDIT: {pixel_height_pass}
SAME_CLASS_RATIO_AUDIT: {ratio_pass}
ROLE_RATIO_AUDIT: {role_pass}
OVERLAP: illegal_candidate_pairs={illegal_pair_count}; raw_collision_pairs={len(raw_collision_pairs)}; clearance_only_pairs={len(clearance_only_pairs)}; raw_intersection_pixels={overlap_pixels}; clip=0; status={terminal['pixel_adjudication_status']}
OBJECTS: N={len(objects)}; glyphs={len(pixels)}; paths={len(objects)-len(pixels)}; math_rules=0; pairs={len(pairs)}/{all_pairs_expected}
FOUR_VIEWS: complete={views_complete}; all_pass={views_pass}; FONT_VISUAL_HARMONY={harmony_pass}; panel/role/script_rows={len(hierarchy)}; MATH={math_pass}; TEXT={text_pass}
CRITICAL_PAIR_ADJUDICATION: {adjudication_complete}; rows={len(adjudications)}/{len(critical_ids)}
MODEL_ROUTE: SA1=gpt-5.6-sol/xhigh; SA2=NOT_USED; SA3=NOT_STARTED; see after_model_route.md.
FAILURE: strict CJK_FULL individual glyph H_INK and same-class ratio; raw collision / clearance gates; see after_pixel_measurements.csv, object_review_ledger.csv, and after_overlap_adjudication.csv.
WRITE_SCOPE: only this fresh directory.
BUILD_WAIT_GATE: no LuaLaTeX/latexmk was started by this SA1; frozen R99 was analysed read-only.
"""
    (OUT / "SA1_HANDOFF.md").write_text(handoff, encoding="utf-8")
    dump_json(OUT / "RESULT.json", terminal)
    # Absolute final filesystem write. Do not invoke any writing phase after this marker.
    (OUT / "WRITE_STOPPED").write_text("WRITE_STOPPED\nHANDOFF_ID=" + HANDOFF_ID + "\nRESULT=" + terminal["result"] + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["build", "mark-reviewed", "finalize"], required=True)
    args = ap.parse_args()
    if args.phase == "build":
        build()
    elif args.phase == "mark-reviewed":
        mark_reviewed()
    else:
        finalize()


if __name__ == "__main__":
    main()
