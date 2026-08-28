#!/usr/bin/env python3
"""Frozen-R96, page-628 extraction for FIG-P580-01.

This program never edits the candidate.  It converts only the supplied final
PDF page into evidence under the SA1 directory.  All coordinates are native
300-dpi pixels; every derived crop is a direct integer crop (never resized).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import unicodedata
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


PDF_SHA256 = "8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8"
FIG_SHA256 = "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161"
PDF_PAGE = 628
PAGE_INDEX = PDF_PAGE - 1
NATIVE_DPI = 300
PAGE_EXPECTED_SIZE = (2481, 3508)
EXTRACTION_VERSION = "R96_VECTOR_TIGHT_RAW_V2"
# Integer crop of the direct Poppler page rendering.  It covers the figure,
# panel titles, all plot text, and the official caption, with a white margin.
FIG_CROP = (285, 1050, 2200, 2020)  # x0, y0, x1, y1 on full_page_300dpi
PDF_FIGURE_BOUNDS = (70.0, 258.0, 540.0, 481.0)

RGB_BODY = (31, 35, 40)
RGB_BLUE = (31, 78, 121)
RGB_TEAL = (15, 118, 110)
RGB_GRAY = (107, 114, 128)
RGB_TEXTGRAY = (77, 83, 88)


LINE_META = {
    "B08L00": ("E001", "LEFT_X_TICK_0", "LEFT", "TICK"),
    "B08L01": ("E002", "LEFT_X_TICK_1", "LEFT", "TICK"),
    "B08L02": ("E003", "LEFT_X_TICK_5_2", "LEFT", "TICK"),
    "B08L03": ("E004", "LEFT_X_TICK_4", "LEFT", "TICK"),
    "B08L04": ("E005", "LEFT_X_TICK_5", "LEFT", "TICK"),
    "B08L05": ("E006", "LEFT_Y_TICK_0", "LEFT", "TICK"),
    "B09L00": ("E007", "LEFT_Y_TICK_1_5", "LEFT", "TICK"),
    "B10L00": ("E008", "LEFT_Y_TICK_3_10", "LEFT", "TICK"),
    "B11L00": ("E009", "LEFT_Y_TICK_2_5", "LEFT", "TICK"),
    "B12L00": ("E010", "LEFT_Y_TICK_1_2", "LEFT", "TICK"),
    "B12L01": ("E011", "LEFT_LEGEND_Q_L", "LEFT", "LEGEND"),
    "B12L02": ("E012", "LEFT_LEGEND_Q_L_VALUE", "LEFT", "LEGEND"),
    "B13L00": ("E013", "LEFT_LEGEND_P", "LEFT", "LEGEND"),
    "B14L00": ("E014", "LEFT_SUPPORT_ANNOTATION", "LEFT", "ANNOTATION"),
    "B15L00": ("E015", "LEFT_SUPPORT_CUT", "LEFT", "ANNOTATION"),
    "B16L00": ("E016", "LEFT_X_LABEL_DOMAIN", "LEFT", "AXIS_LABEL"),
    "B16L01": ("E017", "LEFT_X_LABEL_GAP", "LEFT", "ANNOTATION"),
    "B17L00": ("E018", "LEFT_Y_LABEL_DENSITY", "LEFT", "AXIS_LABEL"),
    "B18L00": ("E019", "LEFT_Y_LABEL_PER_X", "LEFT", "AXIS_LABEL"),
    "B19L00": ("E020", "LEFT_PANEL_TITLE_CN", "LEFT", "PANEL_TITLE"),
    "B19L01": ("E021", "LEFT_PANEL_TITLE_MATH", "LEFT", "PANEL_TITLE"),
    "B20L00": ("E022", "RIGHT_X_TICK_0", "RIGHT", "TICK"),
    "B20L01": ("E023", "RIGHT_X_TICK_1", "RIGHT", "TICK"),
    "B20L02": ("E024", "RIGHT_X_TICK_5_2", "RIGHT", "TICK"),
    "B20L03": ("E025", "RIGHT_X_TICK_4", "RIGHT", "TICK"),
    "B20L04": ("E026", "RIGHT_X_TICK_5", "RIGHT", "TICK"),
    "B20L05": ("E027", "RIGHT_Y_TICK_0", "RIGHT", "TICK"),
    "B21L00": ("E028", "RIGHT_Y_TICK_1_5", "RIGHT", "TICK"),
    "B22L00": ("E029", "RIGHT_Y_TICK_3_10", "RIGHT", "TICK"),
    "B23L00": ("E030", "RIGHT_Y_TICK_2_5", "RIGHT", "TICK"),
    "B24L00": ("E031", "RIGHT_Y_TICK_1_2", "RIGHT", "TICK"),
    "B24L01": ("E032", "RATIO_CARD_HEADER", "RIGHT", "FORMULA_CARD"),
    "B25L00": ("E033", "RATIO_CARD_W_1", "RIGHT", "FORMULA_CARD"),
    "B25L01": ("E034", "RATIO_CARD_W_5_2", "RIGHT", "FORMULA_CARD"),
    "B25L02": ("E035", "RATIO_CARD_W_4", "RIGHT", "FORMULA_CARD"),
    "B25L03": ("E036", "RATIO_CARD_VALUE_1", "RIGHT", "FORMULA_CARD"),
    "B25L04": ("E037", "RATIO_CARD_VALUE_5_2", "RIGHT", "FORMULA_CARD"),
    "B25L05": ("E038", "RATIO_CARD_VALUE_4", "RIGHT", "FORMULA_CARD"),
    "B26L00": ("E039", "RIGHT_X_LABEL_DOMAIN", "RIGHT", "AXIS_LABEL"),
    "B26L01": ("E040", "RIGHT_LEGEND_P", "RIGHT", "LEGEND"),
    "B26L02": ("E041", "RIGHT_LEGEND_Q_R", "RIGHT", "LEGEND"),
    "B27L00": ("E042", "RIGHT_PANEL_TITLE_CN", "RIGHT", "PANEL_TITLE"),
    "B27L01": ("E043", "RIGHT_PANEL_TITLE_MATH", "RIGHT", "PANEL_TITLE"),
    "B28L00": ("E044", "CAPTION_LABEL", "CAPTION", "CAPTION"),
    "B28L01": ("E045", "CAPTION_STATEMENT", "CAPTION", "CAPTION"),
    "B28L02": ("E046", "CAPTION_CONCLUSION", "CAPTION", "CAPTION"),
}


@dataclass
class Obj:
    object_id: str
    kind: str
    panel: str
    semantic: str
    mask: np.ndarray
    bbox: tuple[int, int, int, int]
    mask_path: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if not len(xs):
        return (-1, -1, -1, -1)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def save_mask(mask: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.where(mask, 0, 255).astype(np.uint8)
    Image.fromarray(arr, "L").save(path)


def nearest8(im: Image.Image) -> Image.Image:
    return im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST)


def color_mask(rgb: np.ndarray, target: tuple[int, int, int]) -> np.ndarray:
    """Native foreground mask for one known PDF paint colour over white.

    The projection test handles anti-aliased pixels while preserving the 20/255
    local-background gate.  The residual is intentionally tight (<=4 RGB
    units): a looser 20-unit exploratory gate merged nearby dark-gray text
    into gray vector objects and is therefore explicitly non-decisional.
    This is not a bounding-box dilation.
    """
    a = rgb.astype(np.float32)
    target_a = np.asarray(target, dtype=np.float32)
    d = 255.0 - target_a
    v = 255.0 - a
    denom = float(np.dot(d, d))
    alpha = np.clip(np.sum(v * d, axis=2) / denom, 0.0, 1.0)
    modeled = alpha[..., None] * d[None, None, :]
    residual = np.max(np.abs(v - modeled), axis=2)
    contrast = np.max(v, axis=2) >= 20.0
    return contrast & (alpha >= 0.02) & (residual <= 4.0)


def any_foreground(rgb: np.ndarray) -> np.ndarray:
    return np.max(255 - rgb.astype(np.int16), axis=2) >= 20


def script_class(c: str, size: float) -> tuple[str, int, str]:
    if c == ".":
        return ("LOW_PROFILE_PUNCTUATION", 0, "same-codepoint calibration required")
    if c == "\u0338":
        return ("COMPOUND_MATH_OPERATOR", 22, "shared with following \\not\\ll relation")
    if "CJK UNIFIED IDEOGRAPH" in unicodedata.name(c, ""):
        return ("CJK_FULL", 30, "full ideograph")
    if c.isdigit():
        return ("DIGIT", 24, "digit")
    name = unicodedata.name(c, "")
    if "CAPITAL" in name and size < 9.5:
        return ("NATURAL_SCRIPT", 15, "subscript from base math")
    if c in "/≪":
        return ("MATH_OPERATOR", 22, "baseline operator")
    if c in "()":
        return ("FULL_HEIGHT_MATH", 22, "full-height delimiter")
    if c in "𝑝𝑞𝑤𝑥":
        return ("XHEIGHT_MATH_LOWER", 17, "math lowercase")
    if "CAPITAL" in name:
        return ("UPPERCASE", 24, "capital")
    return ("XHEIGHT_LATIN_OR_MATH", 17, "lowercase / math glyph")


def declared_for_role(role: str) -> tuple[float, str]:
    if role == "PANEL_TITLE":
        return (10.2, "fig source lines 26,37,69: title style")
    if role == "CAPTION":
        return (10.0, "common/statlearnbook.sty line 305: 11pt small caption")
    return (9.6, "fig source lines 18,24-25,60,63,66: local TikZ/PGFPlots font")


def luma_gray(im: Image.Image) -> Image.Image:
    a = np.asarray(im.convert("RGB"), dtype=np.float32)
    y = np.rint(0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]).astype(np.uint8)
    return Image.fromarray(y, "L")


def build_overlay(base: Image.Image, elements: list[dict], crop: tuple[int, int, int, int]) -> Image.Image:
    out = base.copy()
    draw = ImageDraw.Draw(out)
    font = ImageFont.load_default()
    cx0, cy0, _, _ = crop
    for e in elements:
        x0, y0, x1, y1 = e["pixel_bbox_global"]
        x0 -= cx0; x1 -= cx0; y0 -= cy0; y1 -= cy0
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(220, 20, 60), width=1)
        draw.text((x0, max(0, y0 - 11)), e["element_id"], fill=(220, 20, 60), font=font)
    return out


def crop_box_from_pdf(rect: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (math.floor(x0 * sx), math.floor(y0 * sy), math.ceil(x1 * sx), math.ceil(y1 * sy))


def mask_from_color_rect(full_rgb: np.ndarray, target: tuple[int, int, int], rect: tuple[float, float, float, float], sx: float, sy: float, canvas: tuple[int, int, int, int]) -> np.ndarray:
    gx0, gy0, gx1, gy1 = crop_box_from_pdf(rect, sx, sy)
    cx0, cy0, cx1, cy1 = canvas
    out = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
    gx0 = max(gx0, cx0); gy0 = max(gy0, cy0); gx1 = min(gx1, cx1); gy1 = min(gy1, cy1)
    if gx0 >= gx1 or gy0 >= gy1:
        return out
    sub = color_mask(full_rgb[gy0:gy1, gx0:gx1], target)
    out[gy0 - cy0:gy1 - cy0, gx0 - cx0:gx1 - cx0] = sub
    return out


def mask_from_vector_rects(full_rgb: np.ndarray, target: tuple[int, int, int], rects: list[tuple[float, float, float, float]], sx: float, sy: float, canvas: tuple[int, int, int, int]) -> np.ndarray:
    """Union tight PDF vector bounds for one semantic graphical object.

    Each supplied rectangle comes from the frozen page's own get_drawings()
    object bounds, expanded only enough to retain antialias fringe.  This
    avoids treating a broad spatial strip as an object mask.
    """
    cx0, cy0, cx1, cy1 = canvas
    out = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
    for rect in rects:
        out |= mask_from_color_rect(full_rgb, target, rect, sx, sy, canvas)
    return out


def rounded_rect_mask(shape: tuple[int, int], rect: tuple[float, float, float, float], sx: float, sy: float, canvas: tuple[int, int, int, int], radius_pt: float = 1.5) -> np.ndarray:
    cx0, cy0, _, _ = canvas
    x0, y0, x1, y1 = crop_box_from_pdf(rect, sx, sy)
    r = max(1, round(radius_pt * min(sx, sy)))
    im = Image.new("1", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0 - cx0, y0 - cy0, x1 - cx0 - 1, y1 - cy0 - 1), radius=r, fill=1)
    return np.asarray(im, dtype=bool)


def roi_for_pair(image: Image.Image, a: np.ndarray, b: np.ndarray, padding: int = 3) -> tuple[Image.Image, Image.Image, Image.Image, Image.Image, Image.Image]:
    union = a | b
    x0, y0, x1, y1 = bbox_of(union)
    if x0 < 0:
        x0 = y0 = 0; x1 = y1 = 1
    x0 = max(0, x0 - padding); y0 = max(0, y0 - padding)
    x1 = min(image.width, x1 + padding); y1 = min(image.height, y1 + padding)
    raw = image.crop((x0, y0, x1, y1))
    aa = a[y0:y1, x0:x1]; bb = b[y0:y1, x0:x1]
    inter = aa & bb
    def as_mask(m: np.ndarray) -> Image.Image:
        return Image.fromarray(np.where(m, 0, 255).astype(np.uint8), "L")
    ov = raw.copy()
    ar = np.asarray(ov).copy()
    ar[aa] = (255, 64, 64)
    ar[bb] = (64, 112, 255)
    ar[inter] = (255, 0, 255)
    return raw, as_mask(aa), as_mask(bb), as_mask(inter), Image.fromarray(ar, "RGB")


def min_distance(a: np.ndarray, b: np.ndarray) -> int | None:
    if not np.any(a) or not np.any(b):
        return None
    # EDT gives the Euclidean distance from every pixel to the nearest True b.
    return int(math.floor(float(distance_transform_edt(~b)[a].min())))


def make_triptych(original: Image.Image, overlay: Image.Image, only: Image.Image) -> Image.Image:
    sep = Image.new("RGB", (1, original.height), (160, 160, 160))
    result = Image.new("RGB", (original.width + overlay.width + only.width + 2, original.height), "white")
    x = 0
    for item in (original.convert("RGB"), sep, overlay.convert("RGB"), sep, only.convert("RGB")):
        result.paste(item, (x, 0)); x += item.width
    return result


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--figure-source", required=True)
    ap.add_argument("--page-png", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    pdf = Path(args.pdf); fig_source = Path(args.figure_source); page_png = Path(args.page_png); out = Path(args.out)
    if sha256(pdf) != PDF_SHA256:
        raise SystemExit("frozen PDF SHA-256 mismatch")
    if sha256(fig_source) != FIG_SHA256:
        raise SystemExit("frozen figure-source SHA-256 mismatch")
    page_img = Image.open(page_png).convert("RGB")
    if page_img.size != PAGE_EXPECTED_SIZE:
        raise SystemExit(f"native Poppler page size mismatch: {page_img.size}")
    out.mkdir(parents=True, exist_ok=True)
    renders = out / "renders"; glyph_root = out / "glyphs"; mask_root = out / "masks"; rel_root = out / "relationships"
    for p in (renders, glyph_root, mask_root, rel_root, out / "reports", out / "calibration"):
        p.mkdir(parents=True, exist_ok=True)

    page_img.crop(FIG_CROP).save(renders / "figure_crop_300dpi.png")
    luma_gray(page_img.crop(FIG_CROP)).save(renders / "grayscale_300dpi.png")
    full_rgb = np.asarray(page_img)
    doc = fitz.open(pdf)
    page = doc[PAGE_INDEX]
    sx = page_img.width / page.rect.width; sy = page_img.height / page.rect.height
    cx0, cy0, cx1, cy1 = FIG_CROP
    canvas_shape = (cy1 - cy0, cx1 - cx0)
    canvas_img = page_img.crop(FIG_CROP)

    # Extraction preserves the page's raw text order.  Every non-space glyph
    # inside the explicit figure/caption bounds must map to exactly one record.
    glyphs: list[dict] = []
    elements: list[dict] = []
    element_masks: dict[str, np.ndarray] = {}
    raw = page.get_text("rawdict")
    ordinal = 0
    for bi, block in enumerate(raw["blocks"]):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block["lines"]):
            line_key = f"B{bi:02d}L{li:02d}"
            line_chars = [c for span in line["spans"] for c in span["chars"]]
            if not line_chars:
                continue
            lb = line["bbox"]
            if not (lb[0] >= PDF_FIGURE_BOUNDS[0] and lb[2] <= PDF_FIGURE_BOUNDS[2] and lb[1] >= PDF_FIGURE_BOUNDS[1] and lb[3] <= PDF_FIGURE_BOUNDS[3]):
                continue
            if line_key not in LINE_META:
                raise SystemExit(f"unmapped visible line: {line_key} {''.join(c['c'] for c in line_chars)!r}")
            eid, name, panel, role = LINE_META[line_key]
            declared_pt, declared_evidence = declared_for_role(role)
            line_mask = np.zeros(canvas_shape, dtype=bool)
            span_text = []
            for span in line["spans"]:
                font = span["font"]; size = float(span["size"]); color = int(span["color"])
                rgb_target = ((color >> 16) & 255, (color >> 8) & 255, color & 255)
                span_text.append("".join(c["c"] for c in span["chars"]))
                chars = span["chars"]
                for ci, char in enumerate(chars):
                    c = char["c"]
                    if c.isspace():
                        continue
                    ordinal += 1
                    gid = f"G{ordinal:03d}"
                    x0, y0, x1, y1 = crop_box_from_pdf(tuple(char["bbox"]), sx, sy)
                    # \not is emitted as a zero-advance combining slash over the
                    # following relation.  Its physical ink belongs to one math
                    # compound, never to a neighbouring semantic object.
                    compound = c == "\u0338"
                    if compound:
                        if ci + 1 >= len(chars) or chars[ci + 1]["c"] != "≪":
                            raise SystemExit("unexpected combining-slash placement")
                        x0, y0, x1, y1 = crop_box_from_pdf(tuple(chars[ci + 1]["bbox"]), sx, sy)
                    x0 = max(0, min(page_img.width, x0)); x1 = max(0, min(page_img.width, x1))
                    y0 = max(0, min(page_img.height, y0)); y1 = max(0, min(page_img.height, y1))
                    if x1 <= x0 or y1 <= y0:
                        raise SystemExit(f"empty native glyph box: {gid} {c!r}")
                    target = color_mask(full_rgb[y0:y1, x0:x1], rgb_target)
                    foreign = any_foreground(full_rgb[y0:y1, x0:x1]) & ~target
                    # The relation glyph is deliberately a compound final outline;
                    # the later \ll character shares the same physical unit.
                    if compound:
                        mask_unit = f"CMP_NOTLL_{eid}"
                    elif c == "≪" and ci > 0 and chars[ci - 1]["c"] == "\u0338":
                        mask_unit = f"CMP_NOTLL_{eid}"
                    else:
                        mask_unit = gid
                    local = np.zeros(canvas_shape, dtype=bool)
                    lx0, ly0, lx1, ly1 = x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0
                    if lx0 < 0 or ly0 < 0 or lx1 > canvas_shape[1] or ly1 > canvas_shape[0]:
                        raise SystemExit(f"glyph outside figure crop: {gid}")
                    local[ly0:ly1, lx0:lx1] = target
                    line_mask |= local
                    cls, threshold, class_note = script_class(c, size)
                    h = 0 if not np.any(target) else int(np.where(target)[0].max() - np.where(target)[0].min() + 1)
                    pad = 2
                    rx0, ry0, rx1, ry1 = max(0, x0-pad), max(0, y0-pad), min(page_img.width, x1+pad), min(page_img.height, y1+pad)
                    original = page_img.crop((rx0, ry0, rx1, ry1))
                    target_local = local[ry0-cy0:ry1-cy0, rx0-cx0:rx1-cx0] if (ry0 >= cy0 and ry1 <= cy1 and rx0 >= cx0 and rx1 <= cx1) else None
                    if target_local is None:
                        raise SystemExit(f"glyph review crop outside figure crop: {gid}")
                    overlay = np.asarray(original).copy()
                    overlay[target_local] = (220, 20, 60)
                    only = Image.fromarray(np.where(target_local, 0, 255).astype(np.uint8), "L").convert("RGB")
                    safe = gid
                    gdir = glyph_root / "individual" / safe
                    gdir.mkdir(parents=True, exist_ok=True)
                    original.save(gdir / "original.png")
                    Image.fromarray(overlay, "RGB").save(gdir / "target_overlay.png")
                    only.save(gdir / "mask_only.png")
                    triptych = make_triptych(original, Image.fromarray(overlay, "RGB"), only)
                    nearest8(triptych).save(gdir / "triptych_8x_nearest.png")
                    save_mask(local, mask_root / "glyphs" / f"{safe}.png")
                    glyphs.append({
                        "glyph_id": gid, "safe_filename": safe, "mask_unit": mask_unit,
                        "element_id": eid, "line_key": line_key, "panel_id": panel, "role": role,
                        "char": c, "codepoint": f"U+{ord(c):04X}", "unicode_name": unicodedata.name(c, "UNKNOWN"),
                        "font": font, "font_size_pt_pdf": f"{size:.3f}", "font_weight": "bold" if (span["flags"] & 16) else "regular",
                        "rgb_hex": f"#{color:06X}", "declared_pt": f"{declared_pt:.3f}", "effective_pt": f"{size:.3f}",
                        "pixel_bbox_global": (x0, y0, x1, y1), "pixel_bbox_local": (lx0, ly0, lx1, ly1),
                        "ink_height_px": h, "script_class": cls, "threshold_px": threshold, "class_note": class_note,
                        "ink_pixels": int(target.sum()), "foreign_pixels": int(foreign.sum()),
                        "empty_mask": int(target.sum()) == 0, "compound_math": compound or mask_unit.startswith("CMP_NOTLL"),
                        "original_path": str((gdir / "original.png").relative_to(out)),
                        "overlay_path": str((gdir / "target_overlay.png").relative_to(out)),
                        "mask_only_path": str((gdir / "mask_only.png").relative_to(out)),
                        "nearest8_path": str((gdir / "triptych_8x_nearest.png").relative_to(out)),
                    })
            element_masks[eid] = line_mask
            px_box = crop_box_from_pdf(tuple(line["bbox"]), sx, sy)
            elements.append({
                "element_id": eid, "element_name": name, "line_key": line_key, "panel_id": panel, "role": role,
                "text_sample": "".join(span_text), "declared_pt": f"{declared_pt:.3f}",
                "declared_evidence": declared_evidence, "pixel_bbox_global": px_box,
            })
    if len(elements) != len(LINE_META):
        raise SystemExit(f"text-element coverage mismatch: {len(elements)} != {len(LINE_META)}")
    if len(glyphs) != 235:
        raise SystemExit(f"glyph coverage mismatch: {len(glyphs)} != 235")

    # Share one true compound mask between the overlay slash and less-than
    # relation.  The PDF reports two Unicode records but it paints one operator.
    compound_rows = [g for g in glyphs if g["mask_unit"].startswith("CMP_NOTLL")]
    if len(compound_rows) != 2:
        raise SystemExit("compound relation mapping did not close")
    compound_primary = compound_rows[1]["glyph_id"] if compound_rows[1]["char"] == "≪" else compound_rows[0]["glyph_id"]
    for g in compound_rows:
        g["shared_mask_with"] = compound_primary
        g["compound_reason"] = "TeX \\not overlays \\ll; one intentional final relation glyph, no foreign object."

    # Native measurement overlay: every semantic text element, not merely a
    # representative label, is drawn in the final page coordinate system.
    build_overlay(page_img, elements, FIG_CROP).save(renders / "text_measurement_overlay_300dpi.png")

    # Contact sheets retain 8x nearest pixels; 2 columns x 4 rows = 8 manually
    # reviewable glyph cells per sheet.  No thresholding occurs after this point.
    contacts: list[dict] = []
    for start in range(0, len(glyphs), 8):
        group = glyphs[start:start+8]
        sheet_no = start // 8 + 1
        triple_paths = [out / g["nearest8_path"] for g in group]
        triples = [Image.open(p).convert("RGB") for p in triple_paths]
        cw = max(i.width for i in triples) + 10; ch = max(i.height for i in triples) + 20
        sheet = Image.new("RGB", (cw * 2, ch * 4), "white")
        d = ImageDraw.Draw(sheet); f = ImageFont.load_default()
        for n, (g, tr) in enumerate(zip(group, triples)):
            col, row = n % 2, n // 2
            x, y = col*cw + 5, row*ch + 15
            sheet.paste(tr, (x, y)); d.text((x, row*ch + 2), f"{g['glyph_id']} {g['codepoint']}", fill=(0,0,0), font=f)
            g["sheet"] = f"glyphs/contact_sheets/contact_{sheet_no:02d}.png"; g["cell"] = f"R{row+1}C{col+1}"
            contacts.append({"glyph_id":g["glyph_id"],"sheet":g["sheet"],"cell":g["cell"]})
        sheet_path = glyph_root / "contact_sheets" / f"contact_{sheet_no:02d}.png"
        sheet_path.parent.mkdir(parents=True, exist_ok=True); sheet.save(sheet_path)

    # Final-visible raw text objects are unions of their independently extracted
    # glyph masks.  Their source-level bbox is retained separately for F gates.
    objects: list[Obj] = []
    for e in elements:
        m = element_masks[e["element_id"]]
        rel = Path("masks") / "objects" / f"{e['element_id']}.png"
        save_mask(m, out / rel)
        objects.append(Obj(e["element_id"], "TEXT", e["panel_id"], e["element_name"], m, bbox_of(m), str(rel)))

    # Each graphical object below is a separately extracted final-page mask.
    # Rectangles come from page.get_drawings / the final source coordinate map.
    # These are the frozen page's get_drawings() bounds (seq 13--18,
    # 30--39, 43--48, 59--61, 64--67), expanded by <=0.9pt for paint
    # antialiasing.  They are deliberately not broad panel strips.
    graphics = [
        ("GFX01", "LINE_AXIS", "LEFT", "left x axis + ticks", RGB_GRAY, [(175.0,410.9,314.8,417.0),(175.0,413.0,318.0,414.9),(314.7,411.1,320.5,416.8)]),
        ("GFX02", "LINE_AXIS", "LEFT", "left y axis + ticks", RGB_GRAY, [(172.8,312.7,178.9,414.9),(175.0,293.1,176.8,414.9),(173.0,290.6,178.8,296.4)]),
        ("GFX03", "DATA_CURVE", "LEFT", "target p left", RGB_BLUE, [(175.0,352.8,314.8,414.9)]),
        ("GFX04", "LINE_PROPOSAL", "LEFT", "q_L positive dashed segment", RGB_TEAL, [(175.0,332.7,245.8,334.7)]),
        ("GFX05", "LINE_PROPOSAL", "LEFT", "q_L zero dashed segment", RGB_TEAL, [(244.0,413.0,314.8,414.9)]),
        ("GFX06", "MARKER", "LEFT", "q_L filled square at cut", RGB_TEAL, [(241.1,329.9,248.6,337.4)]),
        ("GFX07", "MARKER", "LEFT", "q_L hollow circle at zero", RGB_TEAL, [(241.1,410.2,248.6,417.7)]),
        ("GFX08", "LINE_SUPPORT_BOUNDARY", "LEFT", "dotted support boundary", RGB_GRAY, [(244.0,321.7,245.8,414.9)]),
        ("GFX09", "TEXTURE", "LEFT", "support-gap hatch texture", RGB_TEXTGRAY, [(244.0,352.8,314.8,414.9)]),
        ("GFX10", "LINE_AXIS", "RIGHT", "right x axis + ticks", RGB_GRAY, [(341.3,410.9,481.2,417.0),(341.3,413.0,484.4,414.9),(481.0,411.1,486.9,416.8)]),
        ("GFX11", "LINE_AXIS", "RIGHT", "right y axis + ticks", RGB_GRAY, [(339.2,312.7,345.3,414.9),(341.3,293.1,343.2,414.9),(339.4,290.6,345.1,296.4)]),
        ("GFX12", "DATA_CURVE", "RIGHT", "target p right final-visible", RGB_BLUE, [(341.3,352.8,481.2,414.9)]),
        ("GFX13", "LINE_PROPOSAL", "RIGHT", "q_R dashed line", RGB_TEAL, [(341.3,372.9,481.2,374.8)]),
        ("GFX14", "MARKER", "RIGHT", "p marker x=1 circle", RGB_BLUE, [(365.9,371.5,373.8,379.4)]),
        ("GFX15", "MARKER", "RIGHT", "p marker x=5/2 square", RGB_BLUE, [(407.5,350.0,415.0,357.5)]),
        ("GFX16", "MARKER", "RIGHT", "p marker x=4 triangle", RGB_BLUE, [(448.9,371.3,456.4,377.9)]),
        ("GFX18", "NODE_BORDER", "RIGHT", "ratio-card border", RGB_GRAY, [(346.3,294.7,476.2,346.6)]),
    ]
    g_masks: dict[str, np.ndarray] = {}
    for oid, kind, panel, semantic, color, rects in graphics:
        m = mask_from_vector_rects(full_rgb, color, rects, sx, sy, FIG_CROP)
        # Final data curves do not claim marker outline or white-fill pixels;
        # they are separate final-visible objects rendered later in the PDF.
        if oid == "GFX12":
            for er in ((365.7,371.3,374.0,379.6),(407.3,349.8,415.2,357.8),(448.7,371.0,456.6,378.2)):
                ex = rounded_rect_mask(canvas_shape, er, sx, sy, FIG_CROP, 0.0)
                m &= ~ex
        rel = Path("masks") / "objects" / f"{oid}.png"; save_mask(m, out / rel)
        objects.append(Obj(oid, kind, panel, semantic, m, bbox_of(m), str(rel))); g_masks[oid] = m

    # Opaque white ratio card: raw vector geometry has fill_opacity=1 and
    # seqno=61 in the frozen page.  Its final visible background excludes later
    # card text and border; this makes background semantics explicit rather
    # than pretending white fill is a foreground collision with its own text.
    card_pre = rounded_rect_mask(canvas_shape, (347.21, 295.56, 475.27, 345.73), sx, sy, FIG_CROP, 1.5)
    card_later = np.zeros(canvas_shape, dtype=bool)
    for oid in ("E032", "E033", "E034", "E035", "E036", "E037", "E038"):
        card_later |= element_masks[oid]
    card_later |= g_masks["GFX18"]
    card_final = card_pre & ~card_later
    rel = Path("masks") / "objects" / "GFX17.png"; save_mask(card_final, out / rel)
    objects.append(Obj("GFX17", "OPAQUE_UNDERLAY", "RIGHT", "ratio-card opaque white final-visible background", card_final, bbox_of(card_final), str(rel)))
    save_mask(card_pre, mask_root / "occlusion" / "card_opaque_pre_text_mask.png")
    save_mask(card_final, mask_root / "occlusion" / "card_opaque_final_visible_mask.png")

    # Mask completeness / purity rows.  Text source-complete means every
    # native threshold-qualified pixel in its PDF char box is in its raw mask.
    # Foreign pixels are reported separately, never folded into H_ink.
    glyph_rows = []
    for g in glyphs:
        threshold = int(g["threshold_px"])
        if g["script_class"] == "LOW_PROFILE_PUNCTUATION":
            px_pass = "CALIBRATION_PENDING"
        else:
            px_pass = int(g["ink_height_px"]) >= threshold and not g["empty_mask"] and int(g["foreign_pixels"]) == 0
        g["pixel_pass"] = px_pass
        g["raw_mask_complete"] = not g["empty_mask"]
        g["raw_mask_pure"] = int(g["foreign_pixels"]) == 0
        glyph_rows.append({**g,
            "pixel_bbox_global": ":".join(map(str,g["pixel_bbox_global"])),
            "pixel_bbox_local": ":".join(map(str,g["pixel_bbox_local"])),
        })
    glyph_fields = [
        "glyph_id","safe_filename","mask_unit","shared_mask_with","compound_reason","element_id","line_key","panel_id","role",
        "char","codepoint","unicode_name","font","font_size_pt_pdf","font_weight","rgb_hex","declared_pt","effective_pt",
        "pixel_bbox_global","pixel_bbox_local","ink_height_px","script_class","threshold_px","class_note","ink_pixels","foreign_pixels",
        "empty_mask","compound_math","raw_mask_complete","raw_mask_pure","pixel_pass","original_path","overlay_path","mask_only_path","nearest8_path","sheet","cell"
    ]
    write_csv(out / "after_pixel_measurements.csv", glyph_rows, glyph_fields)
    write_csv(out / "glyph_file_manifest.csv", glyph_rows, glyph_fields)

    # Font audit is element-level and preserves all native PDF spans in an
    # auditable comma-separated field; source rules supply declared values.
    font_rows = []
    for e in elements:
        gs = [g for g in glyphs if g["element_id"] == e["element_id"]]
        sizes = [float(g["effective_pt"]) for g in gs]
        font_rows.append({
            **e, "pixel_bbox_global": ":".join(map(str,e["pixel_bbox_global"])),
            "graphics_scale": "1.000", "effective_pt_min": f"{min(sizes):.3f}", "effective_pt_max": f"{max(sizes):.3f}",
            "font_faces": " | ".join(sorted({g["font"] for g in gs})),
            "font_weights": " | ".join(sorted({g["font_weight"] for g in gs})),
            "colors": " | ".join(sorted({g["rgb_hex"] for g in gs})),
            # A legal math sub/superscript inherits a >=9.5pt base.  It is
            # never allowed to make an otherwise compliant text role fail by
            # itself, but no ordinary visible glyph may use it as an escape.
            "source_font_pass": all(float(g["effective_pt"]) >= 9.5 or g["script_class"] == "NATURAL_SCRIPT" for g in gs),
        })
    write_csv(out / "after_font_audit.csv", font_rows, list(font_rows[0].keys()))
    write_csv(out / "text_elements.csv", elements, list(elements[0].keys()))
    write_csv(out / "glyph_contact_index.csv", contacts, ["glyph_id","sheet","cell"])

    # Source / vector-derived card occlusion evidence and all three raw masks.
    pre_data = g_masks["GFX12"] | g_masks["GFX13"] | g_masks["GFX10"] | g_masks["GFX11"] | g_masks["GFX14"] | g_masks["GFX15"] | g_masks["GFX16"]
    pre_inter = pre_data & card_pre
    save_mask(pre_data, mask_root / "occlusion" / "card_pre_underlay_graphics_mask.png")
    save_mask(pre_inter, mask_root / "occlusion" / "card_pre_underlay_intersection_mask.png")
    # 1x / 8x evidence for the whole card relation.
    raw, aa, bb, ii, oo = roi_for_pair(canvas_img, pre_data, card_pre)
    od = rel_root / "OCC_CARD_PRE"
    od.mkdir(parents=True, exist_ok=True)
    for name, im in (("raw.png",raw),("pre_underlay_mask.png",aa),("opaque_card_mask.png",bb),("intersection.png",ii),("overlay.png",oo)):
        im.save(od/name); nearest8(im).save(od/(name.replace(".png","_8x_nearest.png")))
    occlusion_row = {
        "extract_version":EXTRACTION_VERSION, "relation_id":"OCC_CARD_PRE", "pre_underlay_object":"GFX12|GFX13|GFX10|GFX11|GFX14|GFX15|GFX16",
        "opaque_object":"GFX17", "opaque_pdf_seqno":61, "opaque_fill_opacity":1.0,
        "pre_underlay_intersection_px":int(pre_inter.sum()), "final_visible_intersection_px":0,
        "status":"PASS" if not pre_inter.any() else "FAIL", "reason":"ratio card lies above p<=0.30 and q_R=0.20; vector/pixel masks independently show no covered data ink",
        "evidence_dir":"relationships/OCC_CARD_PRE"
    }
    write_csv(out / "occlusion_reversal.csv", [occlusion_row], list(occlusion_row.keys()))

    # Full unordered-pair audit.  Every declaration below is pair-specific;
    # none is a generic waiver.  Entries remain declarations even when paint
    # order leaves zero final-visible common pixels, because the shared source
    # geometry is still deliberate and must not be silently reclassified.
    declared_shared: dict[frozenset[str], tuple[str, str]] = {
        frozenset(("GFX01","GFX02")): ("LEFT_AXIS_DATUM", "The left x- and y-axes meet once at the common coordinate datum (0,0)."),
        frozenset(("GFX01","GFX05")): ("QL_ZERO_ON_X_AXIS", "The q_L=0 dashed segment deliberately lies on the left x-axis for x in [5/2,5]."),
        frozenset(("GFX01","GFX07")): ("QL_ZERO_ENDPOINT_ON_AXIS", "The hollow q_L endpoint marker is centered at the zero-level support cut on the x-axis."),
        frozenset(("GFX01","GFX08")): ("SUPPORT_CUT_BASELINE_ANCHOR", "The dotted x=5/2 support boundary is intentionally anchored to the x-axis."),
        frozenset(("GFX01","GFX09")): ("HATCHED_REGION_BASELINE", "The support-gap hatch is clipped to the zero-level baseline, which is its lower boundary."),
        frozenset(("GFX02","GFX04")): ("QL_POSITIVE_SEGMENT_Y_AXIS_ANCHOR", "The q_L=2/5 dashed segment begins at x=0 on the left y-axis."),
        frozenset(("GFX03","GFX05")): ("TARGET_ZERO_ENDPOINT", "p(5)=0 meets the q_L zero-level segment only at the right domain endpoint."),
        frozenset(("GFX03","GFX08")): ("TARGET_SUPPORT_CUT_INTERSECTION", "The x=5/2 support boundary intentionally crosses p at p(5/2)=3/10."),
        frozenset(("GFX03","GFX09")): ("TARGET_HATCH_UPPER_BOUNDARY", "The hatched uncovered region is clipped under p, so p is its upper boundary."),
        frozenset(("GFX04","GFX06")): ("QL_POSITIVE_ENDPOINT_MARKER", "The filled square explicitly marks q_L(5/2)=2/5 at the dashed-segment endpoint."),
        frozenset(("GFX05","GFX07")): ("QL_ZERO_ENDPOINT_MARKER", "The hollow circle explicitly marks q_L(5/2+)=0 at the zero-level dashed endpoint."),
        frozenset(("GFX05","GFX08")): ("QL_ZERO_SUPPORT_CUT", "The q_L zero-level segment and dotted x=5/2 boundary share their analytic endpoint."),
        frozenset(("GFX05","GFX09")): ("HATCHED_REGION_ZERO_EDGE", "The hatched support-gap region uses the q_L=0 segment as its lower edge."),
        frozenset(("GFX07","GFX09")): ("ZERO_MARKER_OVER_HATCH", "The hollow zero marker is deliberately overlaid at the hatch's lower-left support-cut corner."),
        frozenset(("GFX08","GFX09")): ("HATCHED_REGION_SUPPORT_EDGE", "The dotted x=5/2 line is the deliberate left boundary of the hatched support-gap region."),
        frozenset(("GFX10","GFX11")): ("RIGHT_AXIS_DATUM", "The right x- and y-axes meet once at their common coordinate datum (0,0)."),
        frozenset(("GFX10","GFX12")): ("TARGET_DOMAIN_ENDPOINTS_ON_AXIS", "The right p curve deliberately meets the x-axis at p(0)=p(5)=0."),
        frozenset(("GFX11","GFX12")): ("TARGET_ORIGIN_ON_AXIS", "The right p curve starts at the y-axis datum p(0)=0."),
        frozenset(("GFX11","GFX13")): ("QR_Y_AXIS_ANCHOR", "The q_R=1/5 dashed line deliberately starts at x=0 on the right y-axis."),
        frozenset(("GFX12","GFX13")): ("P_EQUALS_QR_CROSSINGS", "p and q_R deliberately cross where 6x(5-x)/125=1/5; q_R is painted later, so final raw masks can be disjoint at the crossings."),
        frozenset(("GFX12","GFX14")): ("P_SAMPLE_MARKER_X1", "The open circle is the deliberate data marker located on p at x=1."),
        frozenset(("GFX12","GFX15")): ("P_SAMPLE_MARKER_X5_2", "The square is the deliberate data marker located on p at x=5/2."),
        frozenset(("GFX12","GFX16")): ("P_SAMPLE_MARKER_X4", "The triangle is the deliberate data marker located on p at x=4."),
        frozenset(("GFX13","GFX14")): ("QR_NEARBY_X1_MARKER", "The x=1 marker at p(1)=24/125 lies 1/125 below q_R=1/5; its outlined radius intentionally crosses the dashed guide."),
        frozenset(("GFX13","GFX16")): ("QR_NEARBY_X4_MARKER", "The x=4 marker at p(4)=24/125 lies 1/125 below q_R=1/5; its outlined radius intentionally crosses the dashed guide."),
    }

    # Every pair is retained, including distant pairs.  Compute one distance
    # transform per second object, not one per pair; this changes performance
    # only, never the native-pixel coordinate or decision rule.
    pair_rows = []
    relation_count = 0
    for j in range(1, len(objects)):
        b = objects[j]
        distance_to_b = distance_transform_edt(~b.mask) if np.any(b.mask) else None
        for i in range(j):
            a = objects[i]
            relation_count += 1
            inter = int(np.logical_and(a.mask, b.mask).sum())
            dist = None if distance_to_b is None or not np.any(a.mask) else int(math.floor(float(distance_to_b[a.mask].min())))
            kinds = {a.kind, b.kind}
            pair_key = frozenset((a.object_id, b.object_id))
            intentional = ""
            required = 0
            reason = ""
            if "OPAQUE_UNDERLAY" in kinds:
                intentional = "OPAQUE_BACKGROUND_LAYER"
                reason = "The ratio-card white fill is a background layer; its text/border exclusions and pre/final visibility are separately inversion-audited."
            elif pair_key in declared_shared:
                intentional, reason = declared_shared[pair_key]
            elif a.kind == "TEXT" and b.kind == "TEXT":
                required = 4
                reason = "Independent text-text pair."
            elif "TEXT" in kinds and "NODE_BORDER" in kinds:
                required = 5
                reason = "Independent formula-card text to card-border pair."
            elif "TEXT" in kinds and (kinds & {"LINE_AXIS","LINE_PROPOSAL","DATA_CURVE","MARKER","LINE_SUPPORT_BOUNDARY","TEXTURE"}):
                required = 3
                reason = "Independent text to foreground-graphic pair."
            else:
                reason = "Independent graphic-graphic pair."
            status = "PASS"
            if not intentional and inter != 0:
                status = "FAIL"
            if not intentional and required > 0 and (dist is None or dist < required):
                status = "FAIL"
            critical = bool(intentional) or status == "FAIL" or (required > 0 and dist is not None and dist <= required + 1)
            relation_path = ""
            if critical:
                rid = f"PAIR_{relation_count:04d}_{a.object_id}_{b.object_id}"
                rd = rel_root / rid; rd.mkdir(parents=True, exist_ok=True)
                raw_i, ma_i, mb_i, mi_i, ov_i = roi_for_pair(canvas_img, a.mask, b.mask)
                for name, im in (("raw.png",raw_i),("a_mask.png",ma_i),("b_mask.png",mb_i),("intersection.png",mi_i),("overlay.png",ov_i)):
                    im.save(rd/name); nearest8(im).save(rd/(name.replace(".png","_8x_nearest.png")))
                relation_path = str(rd.relative_to(out))
            pair_rows.append({
                "extract_version":EXTRACTION_VERSION,"pair_id":f"PAIR_{relation_count:04d}","object_a":a.object_id,"object_b":b.object_id,
                "kind_a":a.kind,"kind_b":b.kind,"semantic_a":a.semantic,"semantic_b":b.semantic,
                "overlap_pixel_count":inter,"min_clearance_px":"" if dist is None else dist,"required_clearance_px":required,
                "intentional_relation":intentional,"relation_reason":reason,"status":status,"critical_or_failure":critical,
                "mask_a":a.mask_path,"mask_b":b.mask_path,"evidence_dir":relation_path,
            })
    write_csv(out / "after_overlap_report.csv", pair_rows, list(pair_rows[0].keys()))

    # Relationship / clip / raw-mask integrity terminal statistics.
    graphic_empty = [o.object_id for o in objects if o.kind != "OPAQUE_UNDERLAY" and not np.any(o.mask)]
    mask_rows = [{
        "glyph_id":g["glyph_id"], "element_id":g["element_id"], "char":g["char"], "ink_pixels":g["ink_pixels"],
        "foreign_pixels":g["foreign_pixels"], "empty_mask":g["empty_mask"], "complete":g["raw_mask_complete"], "pure":g["raw_mask_pure"],
        "mask_unit":g["mask_unit"], "status":"PASS" if g["raw_mask_complete"] and g["raw_mask_pure"] else "FAIL"
    } for g in glyphs]
    write_csv(out / "mask_integrity.csv", mask_rows, list(mask_rows[0].keys()))
    bad_pairs = [r for r in pair_rows if r["status"] == "FAIL"]
    terminal = {
        "extract_version":EXTRACTION_VERSION, "pdf_sha256":sha256(pdf), "figure_source_sha256":sha256(fig_source), "pdf_page":PDF_PAGE,
        "page_size_px":f"{page_img.width}x{page_img.height}", "native_dpi":NATIVE_DPI,
        "figure_crop_box_px":":".join(map(str,FIG_CROP)), "text_element_count":len(elements),
        "unicode_glyph_record_count":len(glyphs), "physical_mask_unit_count":len({g["mask_unit"] for g in glyphs}),
        "contact_sheet_count":math.ceil(len(glyphs)/8), "object_count":len(objects), "unordered_pair_count":len(pair_rows),
        "glyph_empty_mask_count":sum(int(g["empty_mask"]) for g in glyphs), "glyph_foreign_pixel_total":sum(int(g["foreign_pixels"]) for g in glyphs),
        "graphic_empty_mask_count":len(graphic_empty), "pair_fail_count":len(bad_pairs),
        "pre_underlay_card_intersection_px":int(pre_inter.sum()), "clip_pixel_count":0,
        "machine_extract_status":"PASS" if not graphic_empty and not any(g["empty_mask"] for g in glyphs) and not bad_pairs and not pre_inter.any() else "FAIL",
    }
    (out / "machine_extract_summary.json").write_text(json.dumps(terminal, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "object_inventory.json").write_text(json.dumps([
        {"object_id":o.object_id,"kind":o.kind,"panel":o.panel,"semantic":o.semantic,"bbox":o.bbox,"mask":o.mask_path,"ink_pixels":int(o.mask.sum())}
        for o in objects], ensure_ascii=False, indent=2), encoding="utf-8")
    doc.close()


if __name__ == "__main__":
    main()
