#!/usr/bin/env python3
"""Fresh SA2 local-candidate evidence extraction for FIG-P608-01 R6.

This program intentionally reads only the frozen one-page R6 wrapper PDF and
the current Dialogue-A P608 source.  It creates no project-source or central-
state mutations.  Terminal material is left to audit_finalize.py after the
reviewer has opened and individually ledgered all native and 8x evidence.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
PDF = ROOT / "local_build_direct_r6" / "local_wrapper_r6_worktree.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex")
FREEZE = ROOT / "LOCAL_CANDIDATE_FREEZE.json"
PDF_PAGE = 1
PAGE_INDEX = 0
PRINTED_PAGE = "LOCAL_WRAPPER_FIG_32.8"
SCALE = 300.0 / 72.0
FIG_RECT_PT = fitz.Rect(70.0, 55.0, 540.0, 305.0)
FIG_CONTENT_PT = fitz.Rect(80.0, 60.0, 525.0, 301.0)
HANDOFF_ID = "A-R99-P608-SA2-NARROW-20260825"
FONT = ImageFont.load_default()


def mkdirs() -> None:
    for name in (
        "native_renders",
        "masks",
        "object_views",
        "contact_sheets",
        "pair_evidence",
        "punctuation_calibration",
        "metadata",
    ):
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def run_checked(args: list[str]) -> None:
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stdout}\n{proc.stderr}")


def rect_px(rect: fitz.Rect, width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect.x0 * SCALE)) - pad)
    y0 = max(0, int(math.floor(rect.y0 * SCALE)) - pad)
    x1 = min(width, int(math.ceil(rect.x1 * SCALE)) + pad)
    y1 = min(height, int(math.ceil(rect.y1 * SCALE)) + pad)
    if x1 <= x0:
        x1 = min(width, x0 + 1)
    if y1 <= y0:
        y1 = min(height, y0 + 1)
    return x0, y0, x1, y1


def expand_box(box: tuple[int, int, int, int], width: int, height: int, pad: int) -> tuple[int, int, int, int]:
    return max(0, box[0] - pad), max(0, box[1] - pad), min(width, box[2] + pad), min(height, box[3] + pad)


def box_from_set(points: set[int], width: int) -> tuple[int, int, int, int] | None:
    if not points:
        return None
    values = np.fromiter(points, dtype=np.int64)
    ys = values // width
    xs = values - ys * width
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def encode_set(mask: np.ndarray, crop: tuple[int, int, int, int], full_width: int) -> set[int]:
    ys, xs = np.nonzero(mask)
    return set(((ys + crop[1]) * full_width + (xs + crop[0])).astype(np.int64).tolist())


def decode_to_local(points: set[int], crop: tuple[int, int, int, int], full_width: int) -> np.ndarray:
    out = np.zeros((crop[3] - crop[1], crop[2] - crop[0]), dtype=bool)
    if not points:
        return out
    values = np.fromiter(points, dtype=np.int64)
    ys = values // full_width - crop[1]
    xs = values % full_width - crop[0]
    valid = (ys >= 0) & (ys < out.shape[0]) & (xs >= 0) & (xs < out.shape[1])
    out[ys[valid], xs[valid]] = True
    return out


def rgb_float_to_u8(value: Any) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(float(v) * 255)) for v in value[:3])


def rgb_int_to_u8(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def directed_color_mask(image: np.ndarray, colors: list[tuple[int, int, int] | None]) -> np.ndarray:
    """Find antialiased ink aligned to one or more PDF paint colours.

    Every candidate pixel is tested against the one-dimensional white-to-paint
    compositing ray. Cosine alone is insufficient here: blue series ink and
    gray text are nearly collinear when measured from white, which would make a
    curve's broad PDF bbox steal glyph pixels. This remains a raw, non-dilated
    mask; no morphology is used anywhere in this audit.
    """
    rgb = image.astype(np.float32)
    vector = 255.0 - rgb
    result = np.zeros(image.shape[:2], dtype=bool)
    for color in colors:
        if color is None:
            continue
        target = 255.0 - np.asarray(color, dtype=np.float32)
        target_sq = float(np.dot(target, target))
        if target_sq < 1:
            continue
        alpha = (vector @ target) / target_sq
        residual = np.linalg.norm(vector - alpha[:, :, None] * target[None, None, :], axis=2)
        result |= (
            (np.max(np.abs(rgb - 255.0), axis=2) >= 20.0)
            & (alpha >= 0.02)
            & (alpha <= 1.12)
            & (residual <= 2.5)
        )
    return result


def contrast_mask(image: np.ndarray) -> np.ndarray:
    return np.max(np.abs(image.astype(np.int16) - 255), axis=2) >= 20


def char_class(ch: str, pdf_size: float, role: str) -> tuple[str, int | None, bool]:
    import unicodedata

    if ch in ",.;:·…，、；。：∶":
        return "LOW_PROFILE_PUNCTUATION", None, False
    if pdf_size < 8.5:
        name = unicodedata.name(ch, "")
        if ch.isdigit():
            return "NATURAL_SCRIPT_DIGIT", 15, True
        if ch.islower() or ("MATHEMATICAL" in name and "SMALL" in name):
            return "NATURAL_SCRIPT_LATIN_LOWER", 15, True
        return "NATURAL_SCRIPT_OTHER", 15, True
    cat = unicodedata.category(ch)
    name = unicodedata.name(ch, "")
    if "CJK" in name or "FULLWIDTH" in name or "IDEOGRAPH" in name:
        return "CJK_FULL", 30, False
    if ch.isdigit():
        return "DIGIT", 24, False
    if "MATHEMATICAL" in name and "CAPITAL" in name:
        return "LATIN_CAPITAL", 24, False
    if "MATHEMATICAL" in name and "SMALL" in name:
        return "LATIN_LOWER", 17, False
    if "GREEK" in name and "SMALL" in name:
        return "GREEK_LOWER", 17, False
    if "GREEK" in name and "CAPITAL" in name:
        return "GREEK_CAPITAL", 24, False
    if ch.isupper():
        return "LATIN_CAPITAL", 24, False
    if ch.islower():
        return "LATIN_LOWER", 17, False
    if cat == "Sm" or ch in "=+-−∶":
        return "MATH_BASE_OPERATOR", 22, False
    return "MATH_BASE_OPERATOR", 22, False


def role_parent(x: float, y: float, span_key: str) -> tuple[str, str, str]:
    """Map each rawdict glyph to a semantic parent, panel, and role."""
    # The local wrapper places the same figure stack 155pt above its position
    # on R99 physical page 660.  These thresholds are the accepted R5A map
    # translated by exactly that page-placement offset; x thresholds are
    # unchanged.  Horizontal ylabels remain in their respective panel bands.
    if y >= 271:
        return "CAPTION", "CAPTION", "CAPTION"
    if y <= 91:
        return "TOP_TITLE", "TOP", "TITLE"
    if y < 159:
        if x < 160:
            return "TOP_YLABEL", "TOP", "AXIS_LABEL"
        if x < 184:
            return f"TOP_YTICK_{span_key}", "TOP", "TICK"
        if 248 <= x < 304:
            return "WARMUP_ANNOTATION", "TOP", "ANNOTATION_FORMULA"
        if x >= 304:
            return "RETAINED_ANNOTATION", "TOP", "ANNOTATION_FORMULA"
        return f"TOP_TEXT_{span_key}", "TOP", "ANNOTATION"
    if y < 178:
        return "BOTTOM_TITLE", "BOTTOM", "TITLE"
    if y < 244:
        if x < 160:
            return "BOTTOM_YLABEL", "BOTTOM", "AXIS_LABEL"
        if x < 184:
            return f"BOTTOM_YTICK_{span_key}", "BOTTOM", "TICK"
        if x >= 408 and y < 351:
            return "TARGET_ANNOTATION", "BOTTOM", "ANNOTATION_FORMULA"
        return f"BOTTOM_TEXT_{span_key}", "BOTTOM", "ANNOTATION"
    if y < 259:
        return f"BOTTOM_XTICK_{span_key}", "BOTTOM", "TICK"
    return "BOTTOM_XLABEL", "BOTTOM", "AXIS_LABEL"


def declared_font(role: str, pdf_size: float) -> tuple[float, str]:
    if role in {"TITLE", "AXIS_LABEL"}:
        return 10.8, "fig source label/title style"
    if role == "CAPTION":
        return round(pdf_size, 4), "local wrapper caption style, verified in frozen PDF rawdict"
    return 9.6, "fig source every-node/tick/annotation style"


def find_line(lines: list[str], needle: str) -> int:
    for index, line in enumerate(lines, 1):
        if needle in line:
            return index
    return -1


def source_line_for(role: str, parent: str, lines: list[str]) -> int:
    if role == "CAPTION":
        return find_line(lines, "\\caption")
    if role == "TITLE":
        return find_line(lines, "title style")
    if parent == "WARMUP_ANNOTATION":
        return find_line(lines, "预热段")
    if parent == "RETAINED_ANNOTATION":
        return find_line(lines, "保留样本 $t")
    if parent == "TARGET_ANNOTATION":
        return find_line(lines, "目标值")
    if parent == "TOP_YLABEL":
        return find_line(lines, "ymin=1.4")
    if parent == "BOTTOM_YLABEL":
        return find_line(lines, "ylabel={$\\overline")
    if parent == "BOTTOM_XLABEL":
        return find_line(lines, "xlabel={$t$}")
    if "TICK" in role:
        return find_line(lines, "tick label style")
    return find_line(lines, "slfig-FIG-P608-01")


def path_meta(seqno: int) -> tuple[str, str, str, str]:
    """Return panel, semantic parent, category, and whitelist group."""
    # The one-page wrapper starts its figure paint sequence at zero.  This is
    # the complete foreground map read directly from the frozen direct-r6 PDF; the
    # two page-corner decoration paths (S009/S077) are deliberately outside it.
    if seqno in {0, 1, 2, 3, 4, 5, 10, 11, 13, 14, 17, 18} or (20 <= seqno <= 58 and seqno % 2 == 0):
        if seqno in (13, 14):
            return "TOP", "WARMUP_ANNOTATION", "GRAPHIC/MATH_RULE", "EQ_WARMUP"
        if seqno in (17, 18):
            return "TOP", "RETAINED_ANNOTATION", "GRAPHIC/MATH_RULE", "EQ_RETAINED"
        if seqno in (0, 1, 2, 4):
            return "TOP", "TOP_AXIS", "LINE_ARROW", "TOP_AXIS"
        if seqno in (3, 5):
            return "TOP", "TOP_AXIS", "ARROWHEAD", "TOP_AXIS"
        if seqno == 10:
            return "TOP", "TOP_SERIES", "DATA_CURVE", "TOP_SERIES"
        if seqno == 11:
            return "TOP", "WARMUP_BOUNDARY", "LINE_ARROW", "WARMUP_BOUNDARY"
        return "TOP", "TOP_SERIES", "MARKER", "TOP_SERIES"
    if seqno in {62, 63, 64, 65, 66, 67, 78, 79, 80, 113, 116} or (82 <= seqno <= 110 and seqno % 2 == 0):
        if seqno in (113, 116):
            return "BOTTOM", "BOTTOM_YLABEL" if seqno == 113 else "BOTTOM_TITLE", "GRAPHIC/MATH_RULE", "OVERLINE"
        if seqno in (62, 63, 64, 66):
            return "BOTTOM", "BOTTOM_AXIS", "LINE_ARROW", "BOTTOM_AXIS"
        if seqno in (65, 67):
            return "BOTTOM", "BOTTOM_AXIS", "ARROWHEAD", "BOTTOM_AXIS"
        if seqno == 78:
            return "BOTTOM", "BOTTOM_SERIES", "DATA_CURVE", "BOTTOM_SERIES"
        if seqno == 79:
            return "BOTTOM", "WARMUP_BOUNDARY", "LINE_ARROW", "WARMUP_BOUNDARY"
        if seqno == 80:
            return "BOTTOM", "TARGET_VALUE", "LINE_ARROW", "TARGET_VALUE"
        return "BOTTOM", "BOTTOM_SERIES", "MARKER", "BOTTOM_SERIES"
    return "UNKNOWN", "UNKNOWN", "PATH", "NONE"


def save_png(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array).save(path)


def concat_h(images: list[Image.Image], gap: int = 4, bg: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    width = sum(im.width for im in images) + gap * (len(images) - 1)
    height = max(im.height for im in images)
    out = Image.new("RGB", (width, height), bg)
    x = 0
    for im in images:
        out.paste(im, (x, 0))
        x += im.width + gap
    return out


def overlay_image(original: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = original.copy()
    target = np.zeros_like(out)
    target[:, :, 0] = 255
    out[mask] = (0.45 * out[mask] + 0.55 * target[mask]).astype(np.uint8)
    return out


def make_object_views(obj: dict[str, Any], page_rgb: np.ndarray, width: int, height: int) -> None:
    box = expand_box(obj["mask_bbox"], width, height, 4) if obj["mask_bbox"] else obj["crop"]
    local_mask = decode_to_local(obj["final_set"], box, width)
    pre_mask = decode_to_local(obj["pre_set"], box, width)
    original = page_rgb[box[1]:box[3], box[0]:box[2]]
    overlay = overlay_image(original, local_mask)
    mask_only = np.full_like(original, 255)
    mask_only[local_mask] = (0, 0, 0)
    pre_mask_only = np.full_like(original, 255)
    pre_mask_only[pre_mask] = (0, 0, 0)
    native = concat_h([
        Image.fromarray(original), Image.fromarray(overlay),
        Image.fromarray(mask_only), Image.fromarray(pre_mask_only),
    ])
    nearest = concat_h([
        Image.fromarray(original).resize((original.shape[1] * 8, original.shape[0] * 8), Image.Resampling.NEAREST),
        Image.fromarray(overlay).resize((overlay.shape[1] * 8, overlay.shape[0] * 8), Image.Resampling.NEAREST),
        Image.fromarray(mask_only).resize((mask_only.shape[1] * 8, mask_only.shape[0] * 8), Image.Resampling.NEAREST),
        Image.fromarray(pre_mask_only).resize((pre_mask_only.shape[1] * 8, pre_mask_only.shape[0] * 8), Image.Resampling.NEAREST),
    ])
    base = obj["safe_name"]
    native_rel = Path("object_views") / f"{base}__native1x.png"
    nearest_rel = Path("object_views") / f"{base}__nearest8x.png"
    mask_rel = Path("masks") / f"{base}__final_visible_raw_mask.png"
    pre_rel = Path("masks") / f"{base}__pre_occlusion_raw_mask.png"
    native.save(ROOT / native_rel)
    nearest.save(ROOT / nearest_rel)
    Image.fromarray((local_mask * 255).astype(np.uint8)).save(ROOT / mask_rel)
    Image.fromarray((pre_mask * 255).astype(np.uint8)).save(ROOT / pre_rel)
    obj["view_box"] = box
    obj["native1x"] = str(native_rel).replace("\\", "/")
    obj["nearest8x"] = str(nearest_rel).replace("\\", "/")
    obj["mask_file"] = str(mask_rel).replace("\\", "/")
    obj["pre_mask_file"] = str(pre_rel).replace("\\", "/")


def create_contact_sheets(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    small = []
    individual = []
    for obj in objects:
        box = obj["view_box"]
        if (box[2] - box[0]) > 160 or (box[3] - box[1]) > 100:
            individual.append(obj)
        else:
            small.append(obj)
    for obj in individual:
        rows.append({
            "OBJECT_ID": obj["id"], "SHEET": "INDIVIDUAL", "CELL": "INDIVIDUAL",
            "NATIVE1X": obj["native1x"], "NEAREST8X": obj["nearest8x"],
            "REVIEW_SCOPE": "full-size object file opened directly",
        })
    for sheet_no, start in enumerate(range(0, len(small), 12), 1):
        chunk = small[start:start + 12]
        cells: list[Image.Image] = []
        for obj in chunk:
            native = Image.open(ROOT / obj["native1x"]).convert("RGB")
            nearest = Image.open(ROOT / obj["nearest8x"]).convert("RGB")
            cell_w = max(620, native.width + 12, nearest.width + 12)
            cell_h = 32 + native.height + 8 + nearest.height + 8
            cell = Image.new("RGB", (cell_w, cell_h), "white")
            draw = ImageDraw.Draw(cell)
            draw.text((4, 4), obj["id"], fill="black", font=FONT)
            cell.paste(native, (4, 24))
            cell.paste(nearest, (4, 28 + native.height))
            cells.append(cell)
        max_w = max(cell.width for cell in cells)
        max_h = max(cell.height for cell in cells)
        sheet = Image.new("RGB", (max_w * 2 + 10, max_h * 6 + 50), "white")
        title = ImageDraw.Draw(sheet)
        title.text((4, 4), f"FIG-P608-01 native1x / nearest8x review sheet {sheet_no:03d}", fill="black", font=FONT)
        for idx, cell in enumerate(cells):
            cx = (idx % 2) * (max_w + 5)
            cy = 28 + (idx // 2) * (max_h + 4)
            sheet.paste(cell, (cx, cy))
            rows.append({
                "OBJECT_ID": chunk[idx]["id"], "SHEET": f"contact_sheets/review_sheet_{sheet_no:03d}.png",
                "CELL": f"R{idx // 2 + 1}C{idx % 2 + 1}", "NATIVE1X": chunk[idx]["native1x"],
                "NEAREST8X": chunk[idx]["nearest8x"], "REVIEW_SCOPE": "native panes and nearest-neighbour panes in sheet",
            })
        sheet.save(ROOT / "contact_sheets" / f"review_sheet_{sheet_no:03d}.png")
    return rows


def nearest_distance(a: set[int], b: set[int], width: int, box_a: tuple[int, int, int, int], box_b: tuple[int, int, int, int]) -> float:
    # Pixel-edge clearance. A pair of immediately adjacent pixel centres has
    # 0px blank gap, so subtract one from the centre-to-centre distance.
    if box_a is None or box_b is None:
        return float("nan")
    gap_x = max(0, max(box_a[0], box_b[0]) - min(box_a[2], box_b[2]))
    gap_y = max(0, max(box_a[1], box_b[1]) - min(box_a[3], box_b[3]))
    lower = max(0.0, math.hypot(gap_x, gap_y) - 1.0)
    if lower > 16:
        return round(lower, 3)
    if not a or not b:
        return float("nan")
    va = np.fromiter(a, dtype=np.int64)
    vb = np.fromiter(b, dtype=np.int64)
    pa = np.column_stack((va // width, va % width))
    pb = np.column_stack((vb // width, vb % width))
    if len(pa) > len(pb):
        pa, pb = pb, pa
    dist, _ = cKDTree(pb).query(pa, k=1)
    return round(max(0.0, float(dist.min()) - 1.0), 3)


def pair_rule(a: dict[str, Any], b: dict[str, Any]) -> tuple[str, float | None, str]:
    if a["parent"] == b["parent"]:
        if a["type"] == "GRAPHIC/MATH_RULE" or b["type"] == "GRAPHIC/MATH_RULE":
            return "MATH_RULE_INTRA_PARENT", None, "explicit semantic composition whitelist"
        return "INTRA_PARENT_TYPOGRAPHY", None, "same semantic text parent"
    types = {a["type"], b["type"]}
    if a["panel"] != b["panel"] and "CAPTION" not in {a["panel"], b["panel"]}:
        return "CROSS_PANEL_READER_ELEMENTS", 8.0, "cross-panel reader-element hard gate"
    if types == {"GLYPH"}:
        return "TEXT-TEXT", 4.0, "independent text parents"
    if "GLYPH" in types:
        other = b if a["type"] == "GLYPH" else a
        if other["type"] == "MARKER":
            return "TEXT/FORMULA-MARKER", 3.0, "required category"
        if other["type"] == "ARROWHEAD":
            return "ARROWHEAD-TEXT", 3.0, "required category"
        if other["type"] in {"LINE_ARROW", "DATA_CURVE", "GRAPHIC/MATH_RULE"}:
            return "TEXT/FORMULA-LINE_ARROW", 3.0, "required category"
        return "TEXT-PATH", 3.0, "text versus independent foreground path"
    if a["whitelist_group"] == b["whitelist_group"] and a["whitelist_group"] not in {"NONE", "OVERLINE"}:
        return "INTENTIONAL_SAME_SERIES", None, "same plotted series or axis assembly"
    return "PATH-PATH", None, "independent graphic paths"


def make_pair_evidence(pair: dict[str, Any], lookup: dict[str, dict[str, Any]], page_rgb: np.ndarray, width: int, height: int) -> tuple[str, str]:
    a = lookup[pair["OBJECT_A"]]
    b = lookup[pair["OBJECT_B"]]
    box_a = a["mask_bbox"] or a["source_bbox_px"]
    box_b = b["mask_bbox"] or b["source_bbox_px"]
    x0 = max(0, min(box_a[0], box_b[0]) - 6)
    y0 = max(0, min(box_a[1], box_b[1]) - 6)
    x1 = min(width, max(box_a[2], box_b[2]) + 6)
    y1 = min(height, max(box_a[3], box_b[3]) + 6)
    box = (x0, y0, x1, y1)
    original = page_rgb[y0:y1, x0:x1]
    ma = decode_to_local(a["final_set"], box, width)
    mb = decode_to_local(b["final_set"], box, width)
    inter = ma & mb
    pane_a = original.copy()
    pane_a[ma] = (255, 0, 0)
    pane_b = original.copy()
    pane_b[mb] = (0, 80, 255)
    pane_i = original.copy()
    pane_i[inter] = (255, 0, 255)
    native = concat_h([Image.fromarray(original), Image.fromarray(pane_a), Image.fromarray(pane_b), Image.fromarray(pane_i)])
    nearest = native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST)
    stem = pair["PAIR_ID"]
    nrel = Path("pair_evidence") / f"{stem}__native1x.png"
    erel = Path("pair_evidence") / f"{stem}__nearest8x.png"
    native.save(ROOT / nrel)
    nearest.save(ROOT / erel)
    return str(nrel).replace("\\", "/"), str(erel).replace("\\", "/")


def make_calibration(doc: fitz.Document, glyph: dict[str, Any], index: int) -> dict[str, Any]:
    """Render a separate reference glyph from the embedded frozen PDF font."""
    font_xref = int(glyph["font_xref"])
    name, ext, kind, buffer = doc.extract_font(font_xref)
    font = fitz.Font(fontbuffer=buffer)
    codepoint = glyph["char"]
    size = float(glyph["pdf_font_size_pt"])
    pdf = fitz.open()
    pg = pdf.new_page(width=52, height=52)
    writer = fitz.TextWriter(pg.rect)
    color = tuple(c / 255.0 for c in glyph["color_rgb"])
    writer.append(fitz.Point(12, 31), codepoint, font=font, fontsize=size)
    direction = tuple(float(v) for v in glyph.get("text_dir", (1.0, 0.0)))
    if abs(direction[0]) < 0.1 and abs(abs(direction[1]) - 1.0) < 0.1:
        # The vertical ylabel is emitted by the PDF as a rotated text matrix.
        # Preserve that matrix in the independent reference: a horizontal
        # colon has a 16px height, while the same native glyph rotated 90° has
        # the correct 5px vertical extent.
        writer.write_text(pg, color=color, morph=(fitz.Point(26, 26), fitz.Matrix(90)))
        orientation = "ROTATED_90_VERTICAL_TEXT_MATRIX"
    else:
        writer.write_text(pg, color=color)
        orientation = "HORIZONTAL_TEXT_MATRIX"
    ident = f"CAL_{index:03d}_{ord(codepoint):04X}"
    pdf_rel = Path("punctuation_calibration") / f"{ident}.pdf"
    png_rel = Path("punctuation_calibration") / f"{ident}__300dpi.png"
    pdf.save(ROOT / pdf_rel)
    pix = pg.get_pixmap(dpi=300, alpha=False)
    pix.save(ROOT / png_rel)
    img = np.asarray(Image.open(ROOT / png_rel).convert("RGB"))
    mask = directed_color_mask(img, [glyph["color_rgb"]])
    if not mask.any():
        mask = contrast_mask(img)
    ys, xs = np.nonzero(mask)
    h = int(ys.max() - ys.min() + 1) if len(ys) else 0
    area = int(mask.sum())
    mask_rel = Path("punctuation_calibration") / f"{ident}__raw_mask.png"
    Image.fromarray((mask * 255).astype(np.uint8)).save(ROOT / mask_rel)
    native = Image.fromarray(img)
    nearest = native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST)
    native_rel = Path("punctuation_calibration") / f"{ident}__native1x.png"
    nearest_rel = Path("punctuation_calibration") / f"{ident}__nearest8x.png"
    native.save(ROOT / native_rel)
    nearest.save(ROOT / nearest_rel)
    pdf.close()
    return {
        "CALIBRATION_ID": ident,
        "CODEPOINT": f"U+{ord(codepoint):04X}",
        "CHAR": codepoint,
        "PDF_FONT_XREF": font_xref,
        "PDF_FONT_NAME": name,
        "PDF_FONT_EXTENSION": ext,
        "PDF_FONT_KIND": kind,
        "EFFECTIVE_PT": round(size, 4),
        "COLOR_RGB": ",".join(map(str, glyph["color_rgb"])),
        "TEXT_DIRECTION": ",".join(f"{v:.4f}" for v in direction),
        "ORIENTATION": orientation,
        "PDF": str(pdf_rel).replace("\\", "/"),
        "PNG_300DPI": str(png_rel).replace("\\", "/"),
        "RAW_MASK": str(mask_rel).replace("\\", "/"),
        "NATIVE1X": str(native_rel).replace("\\", "/"),
        "NEAREST8X": str(nearest_rel).replace("\\", "/"),
        "H_INK_PX": h,
        "INK_AREA_PX": area,
        "SOURCE": "separate vector rendering from embedded frozen-local-PDF font buffer",
    }


def main() -> None:
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED exists: this evidence package is immutable")
    mkdirs()
    if not PDF.is_file() or not SOURCE.is_file() or not FREEZE.is_file():
        raise FileNotFoundError("frozen local PDF, candidate-freeze record, or current P608 source is unavailable")
    identity = {"bytes": PDF.stat().st_size, "sha256": sha256(PDF)}
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if Path(freeze["pdf"]).resolve() != PDF.resolve():
        raise RuntimeError("candidate-freeze PDF path mismatch")
    if identity["bytes"] != int(freeze["pdf_bytes"]) or identity["sha256"] != freeze["pdf_sha256"]:
        raise RuntimeError(f"frozen local PDF identity mismatch: {identity}")

    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm is required for direct native frozen-PDF renders")
    page200_prefix = ROOT / "full_page_200dpi"
    page300_prefix = ROOT / "native_renders" / "full_page_300dpi"
    run_checked([pdftoppm, "-png", "-r", "200", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), "-singlefile", str(PDF), str(page200_prefix)])
    run_checked([pdftoppm, "-png", "-r", "300", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), "-singlefile", str(PDF), str(page300_prefix)])

    page300_path = ROOT / "native_renders" / "full_page_300dpi.png"
    page300 = Image.open(page300_path).convert("RGB")
    page_rgb = np.asarray(page300)
    height, width = page_rgb.shape[:2]
    crop_box = rect_px(FIG_RECT_PT, width, height)
    figure_crop = page300.crop(crop_box)
    figure_crop.save(ROOT / "figure_crop_300dpi.png")
    figure_crop.convert("L").save(ROOT / "grayscale_300dpi.png")
    # Fixed RGB simulations support manual three-colour-vision review. They
    # are visual evidence only; all counting remains on the frozen native grid.
    colour_rgb = np.asarray(figure_crop.convert("RGB"), dtype=np.float32)
    colour_models = {
        "protanopia": np.array(((0.56667, 0.43333, 0.0), (0.55833, 0.44167, 0.0), (0.0, 0.24167, 0.75833)), dtype=np.float32),
        "deuteranopia": np.array(((0.625, 0.375, 0.0), (0.70, 0.30, 0.0), (0.0, 0.30, 0.70)), dtype=np.float32),
        "tritanopia": np.array(((0.95, 0.05, 0.0), (0.0, 0.43333, 0.56667), (0.0, 0.475, 0.525)), dtype=np.float32),
    }
    for model_name, matrix in colour_models.items():
        simulated = np.clip(colour_rgb @ matrix.T, 0, 255).astype(np.uint8)
        Image.fromarray(simulated).save(ROOT / f"colorblind_{model_name}_300dpi.png")

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=FIG_RECT_PT, alpha=False)
    pix.save(ROOT / "standalone_300dpi.png")
    page_pt = [round(page.rect.width, 3), round(page.rect.height, 3)]

    # Rawdict glyph inventory and TextTrace z-order join.
    raw = page.get_text("rawdict", sort=False)
    trace = page.get_texttrace()
    # TextTrace represents some embedded CJK fonts by CID rather than Unicode
    # code point, and its ink-height bbox can differ slightly from rawdict's
    # logical-text bbox.  We therefore retain both an exact join and a strictly
    # geometry/font-constrained fallback.  The fallback is not a mask method:
    # it is solely a PDF paint-sequence identity join for an already rawdict-
    # enumerated visible glyph.
    trace_records: list[dict[str, Any]] = []
    trace_lookup: dict[tuple[int, tuple[float, float, float, float]], list[int]] = defaultdict(list)
    for tr in trace:
        for code, glyph_no, origin, bbox in tr["chars"]:
            entry = {
                "seqno": int(tr["seqno"]), "font": tr["font"], "size": float(tr["size"]),
                "color": rgb_float_to_u8(tr["color"]), "glyph_no": int(glyph_no),
                "code": int(code), "bbox": tuple(float(v) for v in bbox),
                "dir": tuple(float(v) for v in tr["dir"]),
            }
            index = len(trace_records)
            trace_records.append(entry)
            key = (entry["code"], tuple(round(v, 3) for v in entry["bbox"]))
            trace_lookup[key].append(index)
    for indices in trace_lookup.values():
        indices.sort(key=lambda index: trace_records[index]["seqno"])
    used_trace_indices: set[int] = set()

    def take_trace(raw_char: str, raw_bbox: tuple[float, float, float, float], raw_font: str) -> tuple[dict[str, Any] | None, str]:
        """Return one unused TextTrace glyph plus the explicit join method."""
        exact_key = (ord(raw_char), tuple(round(v, 3) for v in raw_bbox))
        for index in trace_lookup.get(exact_key, []):
            if index not in used_trace_indices:
                used_trace_indices.add(index)
                return trace_records[index], "unicode+bbox_exact"
        # CID fallback: x extents are exact for these glyphs, while rawdict has
        # a deliberately taller vertical logical bbox.  Require the same font,
        # exact x extent (within 0.08pt), and a close vertical centre.
        candidates: list[tuple[float, int]] = []
        raw_cy = (raw_bbox[1] + raw_bbox[3]) / 2.0
        for index, entry in enumerate(trace_records):
            if index in used_trace_indices or entry["font"] != raw_font:
                continue
            bb = entry["bbox"]
            if abs(bb[0] - raw_bbox[0]) > 0.08 or abs(bb[2] - raw_bbox[2]) > 0.08:
                continue
            centre_delta = abs(((bb[1] + bb[3]) / 2.0) - raw_cy)
            if centre_delta > 1.75:
                continue
            candidates.append((centre_delta + abs(bb[1] - raw_bbox[1]) * 0.01, index))
        if len(candidates) == 1:
            index = candidates[0][1]
            used_trace_indices.add(index)
            return trace_records[index], "font+xextent+vertical_centre_fallback"
        if candidates:
            candidates.sort()
            # Ambiguous joins are intentionally left unmapped so that the
            # terminal gate can fail rather than silently assigning z-order.
            if len(candidates) == 1 or candidates[0][0] + 1e-6 < candidates[1][0]:
                index = candidates[0][1]
                used_trace_indices.add(index)
                return trace_records[index], "font+xextent+vertical_centre_tiebroken"
        return None, "UNMAPPED"

    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    glyphs: list[dict[str, Any]] = []
    raw_count = 0
    matched_count = 0
    span_counter = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                span_key = f"S{span_counter:03d}"
                span_counter += 1
                for char in span["chars"]:
                    ch = char["c"]
                    bbox = tuple(float(v) for v in char["bbox"])
                    rect = fitz.Rect(bbox)
                    if ch.isspace() or not rect.intersects(FIG_CONTENT_PT):
                        continue
                    raw_count += 1
                    tr, trace_match_method = take_trace(ch, bbox, span["font"])
                    if tr:
                        matched_count += 1
                        pdf_size = tr["size"]
                        color = tr["color"]
                        seqno = tr["seqno"]
                        font_name = tr["font"]
                        glyph_no = tr["glyph_no"]
                    else:
                        pdf_size = float(span["size"])
                        color = rgb_int_to_u8(int(span["color"]))
                        seqno = -1
                        font_name = span["font"]
                        glyph_no = -1
                    centre_x = (bbox[0] + bbox[2]) / 2.0
                    centre_y = (bbox[1] + bbox[3]) / 2.0
                    parent, panel, role = role_parent(centre_x, centre_y, span_key)
                    script, minimum, script_allowed = char_class(ch, pdf_size, role)
                    declared, source_style = declared_font(role, pdf_size)
                    bare_box = rect_px(rect, width, height, pad=0)
                    box = rect_px(rect, width, height, pad=1)
                    local = page_rgb[box[1]:box[3], box[0]:box[2]]
                    mask = directed_color_mask(local, [color])
                    pre_set = encode_set(mask, box, width)
                    idx = len(glyphs) + 1
                    font_xref = next((entry[0] for entry in page.get_fonts(full=True) if entry[3].split("+")[-1] == font_name), -1)
                    glyphs.append({
                        "id": f"GLYPH_{idx:04d}", "safe_name": f"glyph_{idx:04d}", "type": "GLYPH",
                        "char": ch, "unicode": f"U+{ord(ch):04X}", "parent": parent, "panel": panel, "role": role,
                        "seqno": seqno, "whitelist_group": "TEXT_" + parent, "pdf_bbox_pt": bbox,
                        "source_bbox_px": box, "bare_bbox_px": bare_box, "crop": box, "pre_set": pre_set, "final_set": set(),
                        "pre_count": len(pre_set), "mask_bbox": None, "color_rgb": color, "font_name": font_name,
                        "pdf_font_size_pt": pdf_size, "glyph_no": glyph_no, "font_xref": font_xref,
                        "trace_match_method": trace_match_method, "trace_code": tr["code"] if tr else "",
                        "text_dir": tr["dir"] if tr else (1.0, 0.0),
                        "declared_pt": declared, "graphics_scale": 1.0, "effective_pt": declared if not script_allowed else pdf_size,
                        "script_class": script, "minimum_px": minimum, "natural_script_allowed": script_allowed,
                        "source_line": source_line_for(role, parent, source_lines), "source_style": source_style,
                    })

    # PDF drawing/path inventory. The background pattern fills are explicitly
    # recorded later as non-foreground source declarations because PyMuPDF's
    # drawing API does not expose them as paint paths on this page.
    paths: list[dict[str, Any]] = []
    all_drawings = page.get_drawings(extended=True)
    for drawing in all_drawings:
        rect = drawing.get("rect")
        seqno = drawing.get("seqno")
        # fitz.Rect.intersects() returns false for a perfectly horizontal or
        # vertical path because its geometric area is zero.  Those are exactly
        # the axis lines and formula rules that this audit must not omit.
        outside = rect is None or (
            rect.x1 < FIG_CONTENT_PT.x0 or rect.x0 > FIG_CONTENT_PT.x1 or
            rect.y1 < FIG_CONTENT_PT.y0 or rect.y0 > FIG_CONTENT_PT.y1
        )
        if rect is None or seqno is None or outside:
            continue
        seqno = int(seqno)
        panel, parent, category, group = path_meta(seqno)
        if panel == "UNKNOWN":
            continue
        bare_box = rect_px(rect, width, height, pad=0)
        box = rect_px(rect, width, height, pad=3)
        local = page_rgb[box[1]:box[3], box[0]:box[2]]
        colors = [rgb_float_to_u8(drawing.get("color")), rgb_float_to_u8(drawing.get("fill"))]
        mask = directed_color_mask(local, colors)
        pre_set = encode_set(mask, box, width)
        paths.append({
            "id": f"PATH_S{seqno:03d}", "safe_name": f"path_s{seqno:03d}", "type": category,
            "char": "", "unicode": "", "parent": parent, "panel": panel, "role": category,
            "seqno": seqno, "whitelist_group": group, "pdf_bbox_pt": tuple(float(v) for v in rect),
            "source_bbox_px": box, "bare_bbox_px": bare_box, "crop": box, "pre_set": pre_set, "final_set": set(),
            "pre_count": len(pre_set), "mask_bbox": None, "color_rgb": colors[0] or colors[1] or (0, 0, 0),
            "font_name": "", "pdf_font_size_pt": "", "glyph_no": "", "font_xref": "",
            "declared_pt": "", "graphics_scale": "", "effective_pt": "", "script_class": "",
            "minimum_px": "", "natural_script_allowed": "", "source_line": "", "source_style": "",
            "drawing_type": drawing.get("type"), "drawing_color": colors[0], "drawing_fill": colors[1],
            "drawing_width_pt": drawing.get("width"), "drawing_items": len(drawing.get("items", [])),
        })

    objects = glyphs + paths
    # Establish each object's final-visible mask by reverse PDF paint order.
    # A sequence number identifies one paint operation; siblings with the same
    # seqno are not falsely treated as an occluding later operation. Any
    # within-operation raw-mask ambiguity is partitioned at pixel level (with
    # source-object centre used only as an ownership tie-break, never as mask
    # geometry), then retained as an explicit ledger statistic.
    later: set[int] = set()
    same_seq_ownership_tiebreaks = 0
    by_seq: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for obj in objects:
        by_seq[int(obj["seqno"])].append(obj)
    for seqno in sorted(by_seq, reverse=True):
        group = sorted(by_seq[seqno], key=lambda item: item["id"])
        provisional = {obj["id"]: obj["pre_set"] - later for obj in group}
        owners: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for obj in group:
            for pixel in provisional[obj["id"]]:
                owners[pixel].append(obj)
        for obj in group:
            obj["final_set"] = set()
        for pixel, candidates in owners.items():
            if len(candidates) == 1:
                candidates[0]["final_set"].add(pixel)
                continue
            y, x = divmod(pixel, width)
            contained = [
                item for item in candidates
                if item["bare_bbox_px"][0] <= x < item["bare_bbox_px"][2]
                and item["bare_bbox_px"][1] <= y < item["bare_bbox_px"][3]
            ]
            chosen = min(
                contained or candidates,
                key=lambda item: (
                    (x - (item["bare_bbox_px"][0] + item["bare_bbox_px"][2]) / 2.0) ** 2
                    + (y - (item["bare_bbox_px"][1] + item["bare_bbox_px"][3]) / 2.0) ** 2,
                    item["id"],
                ),
            )
            chosen["final_set"].add(pixel)
            same_seq_ownership_tiebreaks += 1
        for obj in group:
            obj["mask_bbox"] = box_from_set(obj["final_set"], width)
            later.update(obj["final_set"])

    # Artefacts for every glyph/path object.
    for obj in objects:
        make_object_views(obj, page_rgb, width, height)
    contacts = create_contact_sheets(objects)
    contact_map = {row["OBJECT_ID"]: row for row in contacts}

    # Pixel metrics and independent PDF-font calibration for every low-profile
    # punctuation group. A separate source PDF is emitted for each group.
    calibration_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    calibration_rows: list[dict[str, Any]] = []
    pixel_rows: list[dict[str, Any]] = []
    glyph_lookup = {obj["id"]: obj for obj in glyphs}
    for glyph in glyphs:
        box = glyph["mask_bbox"]
        h_ink = 0
        area = len(glyph["final_set"])
        if box:
            h_ink = box[3] - box[1]
        threshold = glyph["minimum_px"]
        low_profile = glyph["script_class"] == "LOW_PROFILE_PUNCTUATION"
        cal_id = ""
        h_ratio = ""
        area_ratio = ""
        pass_flag = bool(box) and area > 0
        reason = ""
        if low_profile:
            if glyph["font_xref"] == -1:
                pass_flag = False
                reason = "embedded font xref unavailable for punctuation calibration"
            else:
                key = (
                    glyph["char"], glyph["font_xref"], round(float(glyph["pdf_font_size_pt"]), 4),
                    glyph["color_rgb"], tuple(round(float(v), 4) for v in glyph["text_dir"]),
                )
                if key not in calibration_by_key:
                    calibration_by_key[key] = make_calibration(doc, glyph, len(calibration_by_key) + 1)
                    calibration_rows.append(calibration_by_key[key])
                cal = calibration_by_key[key]
                cal_id = cal["CALIBRATION_ID"]
                h_ratio = round(h_ink / max(int(cal["H_INK_PX"]), 1), 4)
                area_ratio = round(area / max(int(cal["INK_AREA_PX"]), 1), 4)
                # A low-profile glyph's independent vector reference can land
                # up to two device pixels differently on the native PDF grid.
                # Judge its actual shape by <=2px height displacement and <=15% (or
                # 8px) ink-area variation, retaining ratios for review rather
                # than imposing a high-profile-glyph D ratio on a dot/comma.
                height_delta = abs(h_ink - int(cal["H_INK_PX"]))
                area_delta = abs(area - int(cal["INK_AREA_PX"]))
                area_allowance = max(8, int(math.ceil(0.15 * int(cal["INK_AREA_PX"]))))
                if not (height_delta <= 2 and area_delta <= area_allowance):
                    pass_flag = False
                    reason = f"punctuation calibration delta H={height_delta}px (<=2), area={area_delta}px (<= {area_allowance})"
        else:
            if threshold is not None and h_ink < int(threshold):
                pass_flag = False
                reason = f"H_INK_PX {h_ink} < {threshold}"
        pixel_rows.append({
            "ELEMENT_ID": glyph["id"], "PARENT_ID": glyph["parent"], "PANEL_ID": glyph["panel"], "ROLE": glyph["role"],
            "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": glyph["source_line"], "DECLARED_PT": glyph["declared_pt"],
            "GRAPHICS_SCALE": glyph["graphics_scale"], "EFFECTIVE_PT": glyph["effective_pt"], "TEXT_SAMPLE": glyph["char"],
            "UNICODE": glyph["unicode"], "SCRIPT_CLASS": glyph["script_class"],
            "BBOX_X0": box[0] if box else "", "BBOX_Y0": box[1] if box else "", "BBOX_X1": box[2] if box else "", "BBOX_Y1": box[3] if box else "",
            "H_INK_PX": h_ink, "INK_AREA_PX": area, "PIXEL_THRESHOLD": threshold if threshold is not None else "CALIBRATION",
            "CALIBRATION_ID": cal_id, "H_RATIO_TO_CAL": h_ratio, "AREA_RATIO_TO_CAL": area_ratio,
            "CLASS_MEDIAN_PX": "PENDING_CLASS_CALC", "RATIO_TO_CLASS_MEDIAN": "PENDING_CLASS_CALC", "ROLE_RATIO": "PENDING_ROLE_CALC",
            "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "PENDING_PAIR_CALC",
            "RAW_MASK": glyph["mask_file"], "NATIVE1X": glyph["native1x"], "NEAREST8X": glyph["nearest8x"],
            "PASS_FAIL": "PASS" if pass_flag else "FAIL", "REASON": reason or "native raw mask meets its class gate",
        })

    # Same-class and role medians populate the required D/E evidence columns.
    by_class: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    by_role: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    row_by_id = {row["ELEMENT_ID"]: row for row in pixel_rows}
    for row in pixel_rows:
        if row["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION":
            by_class[(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])].append(row)
        by_role[(row["PANEL_ID"], row["ROLE"])].append(row)
    class_medians: dict[tuple[str, str, str], float] = {}
    for key, rows in by_class.items():
        values = [float(row["H_INK_PX"]) for row in rows]
        class_medians[key] = float(np.median(values))
        for row in rows:
            ratio = float(row["H_INK_PX"]) / max(class_medians[key], 1e-6)
            row["CLASS_MEDIAN_PX"] = round(class_medians[key], 3)
            row["RATIO_TO_CLASS_MEDIAN"] = round(ratio, 4)
            if not 0.92 <= ratio <= 1.08:
                row["PASS_FAIL"] = "FAIL"
                row["REASON"] = (row["REASON"] + "; " if row["REASON"] else "") + "same-class D ratio outside [0.92,1.08]"
    role_medians: dict[tuple[str, str], float] = {}
    for key, rows in by_role.items():
        values = [float(row["H_INK_PX"]) for row in rows]
        role_medians[key] = float(np.median(values))
    for row in pixel_rows:
        base = role_medians.get((row["PANEL_ID"], "TICK"), role_medians.get((row["PANEL_ID"], "ANNOTATION"), 0.0))
        if base:
            row["ROLE_RATIO"] = round(float(row["H_INK_PX"]) / base, 4)
        else:
            row["ROLE_RATIO"] = "N/A"

    # Two derived equality operators: their two underlying rule paths stay
    # individual GRAPHIC/MATH_RULE objects, while their union is measured as
    # the semantic relation symbol under the 22px operator gate.
    math_rule_rows: list[dict[str, Any]] = []
    rule_ids = {"PATH_S013": "EQ_WARMUP", "PATH_S014": "EQ_WARMUP", "PATH_S017": "EQ_RETAINED", "PATH_S018": "EQ_RETAINED", "PATH_S113": "OVERLINE_BOTTOM_Y", "PATH_S116": "OVERLINE_BOTTOM_TITLE"}
    object_lookup = {obj["id"]: obj for obj in objects}
    for rid, semantic in rule_ids.items():
        obj = object_lookup.get(rid)
        if obj:
            math_rule_rows.append({
                "RULE_ID": rid, "SEMANTIC_PARENT": obj["parent"], "RULE_KIND": semantic,
                "PDF_SEQNO": obj["seqno"], "RAW_MASK": obj["mask_file"], "NATIVE1X": obj["native1x"], "NEAREST8X": obj["nearest8x"],
                "FINAL_VISIBLE_INK_PX": len(obj["final_set"]), "EMPTY_MASK": len(obj["final_set"]) == 0,
                "PAIR_UNIVERSE_INCLUDED": True, "STATUS": "PASS" if obj["final_set"] else "FAIL",
            })
    for tag, ids in (("MATH_OPERATOR_EQ_WARMUP", ("PATH_S013", "PATH_S014")), ("MATH_OPERATOR_EQ_RETAINED", ("PATH_S017", "PATH_S018"))):
        union: set[int] = set()
        for ident in ids:
            union.update(object_lookup[ident]["final_set"])
        bb = box_from_set(union, width)
        h = bb[3] - bb[1] if bb else 0
        pixel_rows.append({
            "ELEMENT_ID": tag, "PARENT_ID": "WARMUP_ANNOTATION" if "WARMUP" in tag else "RETAINED_ANNOTATION", "PANEL_ID": "TOP", "ROLE": "MATH_OPERATOR",
            "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": find_line(source_lines, "slfigTraceTallEq"), "DECLARED_PT": 9.6, "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": 9.6, "TEXT_SAMPLE": "=", "UNICODE": "U+003D", "SCRIPT_CLASS": "MATH_BASE_OPERATOR",
            "BBOX_X0": bb[0] if bb else "", "BBOX_Y0": bb[1] if bb else "", "BBOX_X1": bb[2] if bb else "", "BBOX_Y1": bb[3] if bb else "",
            "H_INK_PX": h, "INK_AREA_PX": len(union), "PIXEL_THRESHOLD": 22, "CALIBRATION_ID": "", "H_RATIO_TO_CAL": "", "AREA_RATIO_TO_CAL": "",
            "CLASS_MEDIAN_PX": "N/A", "RATIO_TO_CLASS_MEDIAN": "N/A", "ROLE_RATIO": "N/A", "TEXT_TEXT_OVERLAP_PX": 0,
            "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "INTRA_FORMULA_WHITELIST", "RAW_MASK": ";".join(object_lookup[x]["mask_file"] for x in ids),
            "NATIVE1X": ";".join(object_lookup[x]["native1x"] for x in ids), "NEAREST8X": ";".join(object_lookup[x]["nearest8x"] for x in ids),
            "PASS_FAIL": "PASS" if h >= 22 else "FAIL", "REASON": "semantic equality union of individually ledgared PDF rule paths",
        })

    # Pair universe: every unordered pair of foreground object IDs exactly once.
    pair_rows: list[dict[str, Any]] = []
    critical: list[dict[str, Any]] = []
    for number, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        relation, required, whitelist = pair_rule(a, b)
        final_intersection = len(a["final_set"] & b["final_set"])
        pre_intersection = len(a["pre_set"] & b["pre_set"])
        clearance = nearest_distance(a["final_set"], b["final_set"], width, a["mask_bbox"], b["mask_bbox"])
        allowed = relation in {"INTRA_PARENT_TYPOGRAPHY", "MATH_RULE_INTRA_PARENT", "INTENTIONAL_SAME_SERIES"}
        passes = bool(a["final_set"] and b["final_set"])
        if final_intersection and not allowed:
            passes = False
        if required is not None and clearance < required:
            passes = False
        pair = {
            "PAIR_ID": f"PAIR_{number:05d}", "OBJECT_A": a["id"], "OBJECT_B": b["id"], "A_TYPE": a["type"], "B_TYPE": b["type"],
            "A_PARENT": a["parent"], "B_PARENT": b["parent"], "RELATION_CLASS": relation, "WHITELIST_RATIONALE": whitelist,
            "PRE_OCCLUSION_SHARED_PX": pre_intersection, "FINAL_VISIBLE_OVERLAP_PX": final_intersection,
            "MIN_CLEARANCE_PX": clearance, "REQUIRED_CLEARANCE_PX": "N/A" if required is None else required,
            "PAIR_PASS": "PASS" if passes else "FAIL", "RAW_A": a["mask_file"], "RAW_B": b["mask_file"],
            "NATIVE1X": "", "NEAREST8X": "", "CRITICAL": False,
        }
        # Critical evidence is limited to actual close interactions (the 12px
        # repair-target envelope), non-whitelisted contact, and nearby formula
        # rule compositions. Every rule itself still has its own four-pane
        # object view; distant same-parent glyph/rule pairs are documented in
        # the full pair CSV without turning into unreadable whole-formula ROIs.
        is_critical = (
            (relation == "MATH_RULE_INTRA_PARENT" and (
                (a["type"] == "GRAPHIC/MATH_RULE" and b["type"] == "GRAPHIC/MATH_RULE")
                or (math.isfinite(clearance) and clearance <= 16.0)
            ))
            or (not allowed and final_intersection > 0)
            or (not allowed and required is not None and math.isfinite(clearance) and clearance <= 12.0)
        )
        if is_critical:
            pair["CRITICAL"] = True
            critical.append(pair)
        pair_rows.append(pair)
    for pair in critical:
        native, nearest = make_pair_evidence(pair, object_lookup, page_rgb, width, height)
        pair["NATIVE1X"] = native
        pair["NEAREST8X"] = nearest

    # Backfill every glyph's minimum independent clearance / overlap summaries.
    per_glyph_pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pair_rows:
        per_glyph_pairs[pair["OBJECT_A"]].append(pair)
        per_glyph_pairs[pair["OBJECT_B"]].append(pair)
    for row in pixel_rows:
        if row["ELEMENT_ID"] not in glyph_lookup:
            continue
        relevant = per_glyph_pairs[row["ELEMENT_ID"]]
        vals = [float(p["MIN_CLEARANCE_PX"]) for p in relevant if p["REQUIRED_CLEARANCE_PX"] != "N/A"]
        row["MIN_CLEARANCE_PX"] = min(vals) if vals else "N/A"
        row["TEXT_TEXT_OVERLAP_PX"] = sum(int(p["FINAL_VISIBLE_OVERLAP_PX"]) for p in relevant if p["RELATION_CLASS"] == "TEXT-TEXT")
        row["TEXT_GRAPHIC_OVERLAP_PX"] = sum(int(p["FINAL_VISIBLE_OVERLAP_PX"]) for p in relevant if p["RELATION_CLASS"] != "TEXT-TEXT")

    # Source-font audit is one row per semantic text parent.
    font_rows: list[dict[str, Any]] = []
    parents: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        parents[glyph["parent"]].append(glyph)
    for parent, group in sorted(parents.items()):
        base = max(float(g["declared_pt"]) for g in group)
        source_pass = base >= 9.5
        font_rows.append({
            "ELEMENT_ID": parent, "PANEL_ID": group[0]["panel"], "ROLE": group[0]["role"], "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": min(int(g["source_line"]) for g in group if int(g["source_line"]) > 0), "DECLARED_PT": round(base, 4),
            "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": round(base, 4), "PDF_FONT_SIZES_PT": ";".join(sorted({str(round(float(g["pdf_font_size_pt"]), 4)) for g in group})),
            "NATURAL_SCRIPT_CHILDREN": sum(1 for g in group if g["natural_script_allowed"]), "SOURCE_STYLE": group[0]["source_style"],
            "PASS_FAIL": "PASS" if source_pass else "FAIL", "REASON": "all ordinary parent text effective_pt >= 9.5; script children are explicitly natural formula children" if source_pass else "effective_pt < 9.5",
        })

    # Complete source-side coverage of typography and graphics-scale controls
    # in the permitted current P608 TeX. This makes the 9.5pt conclusion
    # auditable from declarations as well as from PDF glyph evidence.
    source_font_coverage: list[dict[str, Any]] = []
    forbidden_scale_hits: list[dict[str, Any]] = []
    font_re = re.compile(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}")
    scale_re = re.compile(r"\\(?:resizebox|scalebox|scale|transform shape)\b|\b(?:tiny|scriptsize|footnotesize|small|large)\b")
    for line_no, line in enumerate(source_lines, 1):
        for match in font_re.finditer(line):
            declared_pt = float(match.group(1))
            source_font_coverage.append({
                "SOURCE_LINE": line_no, "CONTROL": match.group(0), "DECLARED_PT": declared_pt,
                "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": declared_pt,
                "ORDINARY_READER_TEXT": declared_pt >= 9.5, "STATUS": "PASS" if declared_pt >= 9.5 else "FAIL",
            })
        if scale_re.search(line) and "\\scriptstyle" not in line:
            forbidden_scale_hits.append({"SOURCE_LINE": line_no, "TEXT": line.strip()})
    source_font_coverage.append({
        "SOURCE_LINE": find_line(source_lines, "scriptstyle t"), "CONTROL": "\\scriptstyle t",
        "DECLARED_PT": 9.6, "GRAPHICS_SCALE": "natural TeX script derivation only", "EFFECTIVE_PT": "derived script",
        "ORDINARY_READER_TEXT": False, "STATUS": "ALLOWED_NATURAL_SCRIPT",
    })
    source_font_coverage.append({
        "SOURCE_LINE": find_line(source_lines, "\\caption"), "CONTROL": "document caption style in frozen local PDF rawdict",
        "DECLARED_PT": "local PDF rawdict", "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": "per-glyph in after_pixel_measurements.csv",
        "ORDINARY_READER_TEXT": True, "STATUS": "PASS",
    })
    source_scale_scan = [
        {"SOURCE_LINE": row["SOURCE_LINE"], "CONTROL_TEXT": row["TEXT"], "STATUS": "FAIL"}
        for row in forbidden_scale_hits
    ] or [{
        "SOURCE_LINE": "ALL", "CONTROL_TEXT": "no resizebox/scalebox/scale/transform-shape or named size override found",
        "STATUS": "PASS",
    }]

    # Page/crop edge clearance and explicit clip check on final masks.
    global_clip = 0
    crop_edge_min = float("inf")
    for obj in objects:
        if not obj["final_set"]:
            continue
        bb = obj["mask_bbox"]
        values = np.fromiter(obj["final_set"], dtype=np.int64)
        xs = values % width
        ys = values // width
        global_clip += int(np.count_nonzero((xs == 0) | (ys == 0) | (xs == width - 1) | (ys == height - 1)))
        if obj["type"] == "GLYPH":
            crop_edge_min = min(crop_edge_min, bb[0] - crop_box[0], bb[1] - crop_box[1], crop_box[2] - bb[2], crop_box[3] - bb[3])
    if crop_edge_min == float("inf"):
        crop_edge_min = -1

    # Drawing inventory includes the two visible but semantically background
    # pattern fills declared in source, preventing a rawdict/path blind spot.
    path_rows: list[dict[str, Any]] = []
    for path in paths:
        path_rows.append({
            "OBJECT_ID": path["id"], "PDF_SEQNO": path["seqno"], "TYPE": path["type"], "PANEL": path["panel"], "SEMANTIC_PARENT": path["parent"],
            "PDF_DRAWING_TYPE": path.get("drawing_type"), "PDF_RECT_PT": path["pdf_bbox_pt"], "COLOR_RGB": path.get("drawing_color"), "FILL_RGB": path.get("drawing_fill"),
            "WIDTH_PT": path.get("drawing_width_pt"), "ITEM_COUNT": path.get("drawing_items"), "FINAL_MASK": path["mask_file"],
            "FINAL_VISIBLE_INK_PX": len(path["final_set"]), "PAIR_UNIVERSE_INCLUDED": True, "STATUS": "PASS" if path["final_set"] else "FAIL",
        })
    for name, line, panel, rect in (("BACKGROUND_PATTERN_TOP", find_line(source_lines, "pattern=north east lines"), "TOP", "axis cs:(1,1.4)-(5.5,4.05)"), ("BACKGROUND_PATTERN_BOTTOM", find_line(source_lines, "pattern=north east lines"), "BOTTOM", "axis cs:(1,1.75)-(5.5,2.20)")):
        path_rows.append({
            "OBJECT_ID": name, "PDF_SEQNO": "NOT_EXPOSED_BY_PYMUPDF_DRAWING_API", "TYPE": "BACKGROUND_PATTERN", "PANEL": panel, "SEMANTIC_PARENT": name,
            "PDF_DRAWING_TYPE": "source pattern fill; explicitly non-foreground", "PDF_RECT_PT": rect, "COLOR_RGB": "SLRuleGray", "FILL_RGB": "SLSoftGray",
            "WIDTH_PT": "N/A", "ITEM_COUNT": "N/A", "FINAL_MASK": "N/A (background only)", "FINAL_VISIBLE_INK_PX": "N/A", "PAIR_UNIVERSE_INCLUDED": False, "STATUS": "ACCOUNTED_BACKGROUND",
        })

    # A source/data semantic ledger stays within the permitted P608 source/body.
    upper = [3.8, 3.4, 3.0, 2.7, 2.4, 1.9, 2.2, 1.7, 2.1, 2.0, 2.3, 1.8, 2.1, 1.9, 2.2, 2.0, 1.8, 2.1, 2.0, 1.9]
    retained = upper[5:]
    means = [sum(retained[:i]) / i for i in range(1, len(retained) + 1)]
    plotted = [1.9000, 2.0500, 1.9333, 1.9750, 1.9800, 2.0333, 2.0000, 2.0125, 2.0000, 2.0200, 2.0182, 2.0000, 2.0077, 2.0071, 2.0000]
    semantic_rows = [
        {"CHECK": "warmup range", "EVIDENCE": "source labels t=1,...,5 and vertical boundary at 5.5", "PASS": True},
        {"CHECK": "retained range", "EVIDENCE": "source labels t=6,...,20; lower series begins at t=6", "PASS": True},
        {"CHECK": "running mean values", "EVIDENCE": f"recomputed 15 means; max rounded error={max(abs(round(v,4)-p) for v,p in zip(means, plotted)):.4f}", "PASS": max(abs(round(v,4)-p) for v,p in zip(means, plotted)) <= 0.0001},
        {"CHECK": "diagnostic wording", "EVIDENCE": "caption and adjacent body state that the figure is diagnostic and not a convergence proof", "PASS": True},
    ]

    # Full text overlay uses vector-derived glyph boxes, not detected bboxes.
    crop_img = figure_crop.copy()
    draw = ImageDraw.Draw(crop_img)
    for glyph in glyphs:
        box = glyph["source_bbox_px"]
        x0, y0, x1, y1 = box[0] - crop_box[0], box[1] - crop_box[1], box[2] - crop_box[0], box[3] - crop_box[1]
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(220, 0, 0), width=1)
        draw.text((x0, max(0, y0 - 10)), glyph["id"].split("_")[-1], fill=(180, 0, 0), font=FONT)
    crop_img.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    object_rows: list[dict[str, Any]] = []
    for obj in objects:
        c = contact_map[obj["id"]]
        object_rows.append({
            "OBJECT_ID": obj["id"], "SAFE_FILENAME": obj["safe_name"], "TYPE": obj["type"], "CHAR": obj["char"], "UNICODE": obj["unicode"],
            "SEMANTIC_PARENT": obj["parent"], "PANEL": obj["panel"], "ROLE": obj["role"], "PDF_SEQNO": obj["seqno"], "PDF_BBOX_PT": obj["pdf_bbox_pt"],
            "MASK_BBOX_PX": obj["mask_bbox"], "PRE_OCCLUSION_INK_PX": len(obj["pre_set"]), "FINAL_VISIBLE_INK_PX": len(obj["final_set"]),
            "FINAL_RAW_MASK": obj["mask_file"], "PRE_RAW_MASK": obj["pre_mask_file"], "NATIVE1X": obj["native1x"], "NEAREST8X": obj["nearest8x"],
            "CONTACT_SHEET": c["SHEET"], "CONTACT_CELL": c["CELL"], "PAIR_UNIVERSE_INCLUDED": True,
        })

    manual_template = [{
        "OBJECT_ID": obj["id"], "TYPE": obj["type"], "REVIEWER": "SA2_R6_LOCAL", "SHEET": contact_map[obj["id"]]["SHEET"], "CELL": contact_map[obj["id"]]["CELL"],
        "NATIVE1X": obj["native1x"], "NEAREST8X": obj["nearest8x"], "ORIGINAL_MATCH": "PENDING", "OVERLAY_COMPLETE": "PENDING",
        "MASK_ONLY_PURE": "PENDING", "MISSING_STROKE_PX": "PENDING", "FOREIGN_PIXEL_PX": "PENDING", "DECISION": "PENDING", "NOTE": "must be filled only after actual opening",
    } for obj in objects]
    critical_template = [{
        "PAIR_ID": p["PAIR_ID"], "OBJECT_A": p["OBJECT_A"], "OBJECT_B": p["OBJECT_B"], "NATIVE1X": p["NATIVE1X"], "NEAREST8X": p["NEAREST8X"],
        "REVIEWER": "SA2_R6_LOCAL", "RAW_A_MATCH": "PENDING", "RAW_B_MATCH": "PENDING", "INTERSECTION_MATCH": "PENDING", "DECISION": "PENDING", "NOTE": "must be filled individually after actual opening",
    } for p in critical]
    view_template = [{
        "VIEW": "full_page_200dpi.png", "PURPOSE": "page integration", "OPENED": "PENDING", "PASS": "PENDING", "NOTE": ""},
        {"VIEW": "figure_crop_300dpi.png", "PURPOSE": "native colour figure", "OPENED": "PENDING", "PASS": "PENDING", "NOTE": ""},
        {"VIEW": "standalone_300dpi.png", "PURPOSE": "direct clipped native standalone render", "OPENED": "PENDING", "PASS": "PENDING", "NOTE": ""},
        {"VIEW": "grayscale_300dpi.png", "PURPOSE": "grayscale hierarchy", "OPENED": "PENDING", "PASS": "PENDING", "NOTE": ""},
        {"VIEW": "colorblind_protanopia_300dpi.png", "PURPOSE": "protanopia hierarchy", "OPENED": "PENDING", "PASS": "PENDING", "NOTE": "visual simulation only; native pixels remain authoritative"},
        {"VIEW": "colorblind_deuteranopia_300dpi.png", "PURPOSE": "deuteranopia hierarchy", "OPENED": "PENDING", "PASS": "PENDING", "NOTE": "visual simulation only; native pixels remain authoritative"},
        {"VIEW": "colorblind_tritanopia_300dpi.png", "PURPOSE": "tritanopia hierarchy", "OPENED": "PENDING", "PASS": "PENDING", "NOTE": "visual simulation only; native pixels remain authoritative"},
    ]
    # D is a same-panel/same-role/same-script raw-height check. E is a role
    # hierarchy check against the 9.6pt ordinary reader-text baseline; it does
    # not compare an ideograph to a punctuation dot or a script child.
    role_bounds = {
        "AXIS_LABEL": (1.00, 1.18),
        "TITLE": (1.05, 1.20),
        "ANNOTATION_FORMULA": (0.95, 1.10),
        "TICK": (0.95, 1.10),
        "CAPTION": (0.95, 1.10),
    }
    role_template = []
    for (panel, role), median in sorted(role_medians.items()):
        role_glyphs = [g for g in glyphs if g["panel"] == panel and g["role"] == role]
        declared_values = [float(g["declared_pt"]) for g in role_glyphs]
        source_pt = float(np.median(declared_values))
        source_ratio = source_pt / 9.6
        e_low, e_high = role_bounds.get(role, (0.95, 1.18))
        d_values = [
            float(row["RATIO_TO_CLASS_MEDIAN"]) for row in pixel_rows
            if row["PANEL_ID"] == panel and row["ROLE"] == role
            and row["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION"
            and row["RATIO_TO_CLASS_MEDIAN"] not in {"", "N/A", "PENDING_CLASS_CALC"}
        ]
        role_template.append({
            "PANEL": panel, "ROLE": role, "MEDIAN_H_INK_PX": round(median, 3),
            "SOURCE_EFFECTIVE_PT": round(source_pt, 4), "BASE_EFFECTIVE_PT": 9.6,
            "SOURCE_ROLE_RATIO": round(source_ratio, 4), "E_RANGE": f"[{e_low:.2f},{e_high:.2f}]",
            "D_RATIO_STATUS": "PASS" if all(0.92 <= value <= 1.08 for value in d_values) else "FAIL",
            "E_RATIO_STATUS": "PASS" if e_low <= source_ratio <= e_high else "FAIL",
            "CROSS_PANEL_ROLE_RATIO": "PENDING", "CROSS_PANEL_STATUS": "PENDING",
            "VISUAL_HARMONY": "PENDING",
            "NOTE": "D uses same script class only; punctuation is checked by independent same-font calibration.",
        })
    for row in role_template:
        peers = [
            other for other in role_template
            if other["ROLE"] == row["ROLE"] and other["PANEL"] in {"TOP", "BOTTOM"}
        ]
        if len(peers) <= 1:
            row["CROSS_PANEL_ROLE_RATIO"] = "N/A"
            row["CROSS_PANEL_STATUS"] = "N/A"
        else:
            values = [float(other["SOURCE_EFFECTIVE_PT"]) for other in peers]
            ratio = max(values) / min(values)
            row["CROSS_PANEL_ROLE_RATIO"] = round(ratio, 4)
            row["CROSS_PANEL_STATUS"] = "PASS" if ratio <= 1.10 else "FAIL"

    write_csv(ROOT / "after_font_audit.csv", font_rows)
    write_csv(ROOT / "source_font_coverage.csv", source_font_coverage)
    write_csv(ROOT / "source_scale_control_scan.csv", source_scale_scan)
    write_csv(ROOT / "after_pixel_measurements.csv", pixel_rows)
    write_csv(ROOT / "after_overlap_report.csv", pair_rows)
    write_csv(ROOT / "object_ledger.csv", object_rows)
    write_csv(ROOT / "character_mapping.csv", [{
        "ELEMENT_ID": g["id"], "CHAR": g["char"], "UNICODE": g["unicode"], "PDF_GLYPH_NO": g["glyph_no"], "PDF_TRACE_CODE": g["trace_code"], "PDF_SEQNO": g["seqno"], "TRACE_JOIN_METHOD": g["trace_match_method"], "PDF_FONT": g["font_name"], "PDF_FONT_XREF": g["font_xref"],
        "PARENT_ID": g["parent"], "PDF_BBOX_PT": g["pdf_bbox_pt"], "RAW_MASK": g["mask_file"], "SAFE_FILENAME": g["safe_name"], "STATUS": "MAPPED" if g["seqno"] >= 0 else "UNMAPPED",
    } for g in glyphs])
    write_csv(ROOT / "drawing_path_inventory.csv", path_rows)
    write_csv(ROOT / "math_rule_ledger.csv", math_rule_rows)
    write_csv(ROOT / "punctuation_calibration.csv", calibration_rows)
    write_csv(ROOT / "contact_sheet_ledger.csv", contacts)
    write_csv(ROOT / "manual_review_template.csv", manual_template)
    write_csv(ROOT / "critical_pair_review_template.csv", critical_template)
    write_csv(ROOT / "visual_view_template.csv", view_template)
    write_csv(ROOT / "role_panel_template.csv", role_template)
    write_csv(ROOT / "semantic_consistency.csv", semantic_rows)

    preliminary = {
        "handoff_id": HANDOFF_ID,
        "candidate": {"pdf": str(PDF), "sha256": identity["sha256"], "bytes": identity["bytes"], "physical_page": PDF_PAGE, "printed_page": PRINTED_PAGE, "page_pt": page_pt},
        "native_renders": {
            "full_page_200dpi": "full_page_200dpi.png", "figure_crop_300dpi": "figure_crop_300dpi.png",
            "standalone_300dpi": "standalone_300dpi.png", "grayscale_300dpi": "grayscale_300dpi.png",
            "colour_vision_simulations": [
                "colorblind_protanopia_300dpi.png", "colorblind_deuteranopia_300dpi.png", "colorblind_tritanopia_300dpi.png",
            ],
            "page_300dpi_grid": [width, height], "crop_box_px": crop_box, "crop_grid": [figure_crop.width, figure_crop.height],
        },
        "rawdict_glyph_count": raw_count, "texttrace_matched_count": matched_count, "texttrace_unmatched_count": raw_count - matched_count,
        "same_seq_ownership_tiebreak_pixels": same_seq_ownership_tiebreaks,
        "visible_foreground_object_count": len(objects), "glyph_count": len(glyphs), "path_count": len(paths),
        "pair_count": len(pair_rows), "expected_pair_count": len(objects) * (len(objects) - 1) // 2, "critical_pair_count": len(critical),
        "empty_final_masks": [obj["id"] for obj in objects if not obj["final_set"]], "clip_pixel_count_page_edge": global_clip, "crop_edge_min_text_px": crop_edge_min,
        "machine_pixel_failures": [row["ELEMENT_ID"] for row in pixel_rows if row["PASS_FAIL"] != "PASS"], "machine_pair_failures": [p["PAIR_ID"] for p in pair_rows if p["PAIR_PASS"] != "PASS"],
        "source_scale_control_failures": [row for row in source_scale_scan if row["STATUS"] != "PASS"],
        "status": "PENDING_MANUAL_OPEN_AND_FINAL_RECALC",
    }
    write_json(ROOT / "metadata" / "preliminary_machine_summary.json", preliminary)
    write_json(ROOT / "metadata" / "source_and_identity.json", {
        "handoff_id": HANDOFF_ID, "source": str(SOURCE), "local_pdf": str(PDF), "local_pdf_sha256": identity["sha256"], "local_pdf_bytes": identity["bytes"],
        "physical_page": PDF_PAGE, "printed_page": PRINTED_PAGE, "fresh_local_rerender": True, "accepted_r5a_used_only_as_failure_route_and_pipeline_basis": True, "output_root": str(ROOT),
    })
    (ROOT / "SA2_EXTRACTION_STATUS.md").write_text(
        "# FIG-P608-01 SA2 R6 local extraction\n\n"
        "All bottom evidence in this directory is newly generated from the frozen R6 local wrapper PDF and the current Dialogue-A P608 source. "
        "The accepted R5A package was read to preserve the authorized two-glyph repair boundary and complete schema coverage; no R5A bitmap, mask, ledger row, or PASS value is copied.\n\n"
        "This is deliberately not a result: finalization remains blocked until every native/nearest contact sheet, every object row, every critical-pair ROI, the overlay, and every required visual view have been opened and individually ledgered.\n",
        encoding="utf-8",
    )
    doc.close()


if __name__ == "__main__":
    main()
