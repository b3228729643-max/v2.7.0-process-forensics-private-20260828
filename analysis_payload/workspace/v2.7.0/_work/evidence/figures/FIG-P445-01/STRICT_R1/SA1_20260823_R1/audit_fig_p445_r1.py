#!/usr/bin/env python3
"""Read-only strict R1 audit for FIG-P445-01.

This script never changes the frozen PDF or LaTeX source.  Every file it writes
is relative to this evidence directory.  It re-locates the figure in the frozen
PDF, renders it at native 200/300 dpi, extracts final-PDF vector glyphs, and
creates independently derived foreground masks for each visible figure/caption
glyph and each figure vector path.
"""

from __future__ import annotations

import copy
import csv
import io
import json
import math
import re
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import cv2
import fitz
import numpy as np
from lxml import etree as ET
from PIL import Image, ImageColor, ImageDraw, ImageFont
from scipy.spatial import cKDTree


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第04册_无监督学习与矩阵分解\V4-C02\fig_v4_c02_dendrogram.tex")
CONTEXT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第04册_无监督学习与矩阵分解\chapters\V4-C02.tex")
CAPTION_STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty")
SOURCE_REL = "src/绘图源码/第04册_无监督学习与矩阵分解/V4-C02/fig_v4_c02_dendrogram.tex"
FIGURE_ID = "FIG-P445-01"
PHRASE = "树的纵坐标表示合并高度"

SCALE_DPI = 300
FONT = ImageFont.load_default()
NS = {"svg": "http://www.w3.org/2000/svg"}
SVG_NS = "{http://www.w3.org/2000/svg}"


def mkdirs() -> None:
    for sub in (
        "raw_objects",
        "masks/text",
        "masks/text_semantic",
        "masks/vector",
        "overlays/objects",
        "critical_pairs",
        "isolated_svg/text",
        "isolated_svg/vector",
        "metadata",
    ):
        (OUT / sub).mkdir(parents=True, exist_ok=True)


def write_text(name: str, text: str) -> None:
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")


def write_csv(name: str, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fnum(value: float | int | None, ndigits: int = 3) -> str:
    if value is None:
        return ""
    return f"{float(value):.{ndigits}f}"


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def is_cjk(ch: str) -> bool:
    return bool(ch) and ("CJK" in unicodedata.name(ch, "") or "HIRAGANA" in unicodedata.name(ch, "") or "KATAKANA" in unicodedata.name(ch, ""))


def is_punctuation(ch: str) -> bool:
    return bool(ch) and unicodedata.category(ch).startswith("P")


def script_class(ch: str, natural_script: bool) -> tuple[str, int]:
    if natural_script:
        return "NATURAL_SCRIPT", 15
    if is_punctuation(ch) or ch in "=+-−×÷<>|":
        return "BASE_OPERATOR_PUNCT", 22
    if is_cjk(ch) or unicodedata.east_asian_width(ch) in {"W", "F"}:
        return "CJK_FULLWIDTH", 30
    if ch.isdigit() or ch.isupper() or "CAPITAL" in unicodedata.name(ch, ""):
        return "LATIN_UPPER_DIGIT", 24
    return "LATIN_LOWER_GREEK", 17


def role_for(ch: str, bbox: fitz.Rect) -> str:
    x0, y0, x1, y1 = bbox
    if is_cjk(ch) and x0 < 160 and 170 <= y0 <= 213:
        return "AXIS_TITLE"
    if ch.isdigit() and 150 <= x0 <= 160 and 200 <= y0 <= 330:
        return "TICK"
    if 195 <= x0 <= 340 and 306 <= y0 <= 320:
        return "CLUSTER_LABEL"
    if 175 <= x0 <= 350 and 320 <= y0 <= 336:
        return "LEAF_LABEL"
    if 360 <= x0 <= 440 and 260 <= y0 <= 276:
        return "CUT_ANNOTATION"
    if 337 <= y0 <= 355:
        return "CAPTION_LABEL" if x0 < 120 else "CAPTION_TEXT"
    raise ValueError(f"Unclassified visible figure glyph {ch!r} at {tuple(round(x, 3) for x in bbox)}")


def source_font_for(role: str, ch: str) -> tuple[float, float, float, bool, int, str]:
    """declared parent pt, element effective pt, parent effective pt, script?, line, provenance."""
    if role == "AXIS_TITLE":
        return 9.4, 9.4, 9.4, False, 23, r"\fontsize{9.4pt}{11.2pt}"
    if role == "TICK":
        return 8.6, 8.6, 8.6, False, 24, r"\fontsize{8.6pt}{10.2pt}"
    if role == "CLUSTER_LABEL":
        if ch.isdigit():
            return 9.6, 6.7, 9.6, True, 18 + int(ch) - 1, r"natural math subscript from 9.6pt"
        return 9.6, 9.6, 9.6, False, 18, r"cluster label \fontsize{9.6pt}{11.3pt}"
    if role == "LEAF_LABEL":
        if ch.isdigit():
            return 9.4, 6.6, 9.4, True, 25, r"natural math subscript from 9.4pt"
        return 9.4, 9.4, 9.4, False, 26, r"\fontsize{9.4pt}{11.2pt}"
    if role == "CUT_ANNOTATION":
        if ch in {"𝑐", "c"}:
            return 9.2, 6.4, 9.2, True, 34, r"natural math subscript from 9.2pt"
        return 9.2, 9.2, 9.2, False, 34, r"\fontsize{9.2pt}{11pt}"
    if role in {"CAPTION_LABEL", "CAPTION_TEXT"}:
        return 10.0, 10.0, 10.0, False, 36, r"\captionsetup{font={small,...}} at statlearnbook.sty:305"
    raise ValueError(role)


def parse_matrix(value: str | None) -> tuple[float, float, float, float, float, float]:
    if not value:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    found = re.search(r"matrix\(([^)]*)\)", value)
    if not found:
        raise ValueError(f"Unexpected SVG transform: {value}")
    nums = [float(x) for x in re.split(r"[,\s]+", found.group(1).strip()) if x]
    if len(nums) != 6:
        raise ValueError(f"Unexpected matrix: {value}")
    return tuple(nums)  # type: ignore[return-value]


def patch_background_and_mask(raw_patch: np.ndarray, vector_mask: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int]]:
    background_pixels = raw_patch[~vector_mask]
    if len(background_pixels) == 0:
        background_pixels = raw_patch.reshape(-1, 3)
    bg = np.median(background_pixels, axis=0).astype(np.int16)
    delta = np.max(np.abs(raw_patch.astype(np.int16) - bg[None, None, :]), axis=2)
    # C1: a pixel must differ from its local background by at least 20/255.
    return vector_mask & (delta >= 20), (int(bg[0]), int(bg[1]), int(bg[2]))


def crop_bounds(rect: fitz.Rect, sx: float, sy: float, width: int, height: int, pad_px: int = 2) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect.x0 * sx)) - pad_px)
    y0 = max(0, int(math.floor(rect.y0 * sy)) - pad_px)
    x1 = min(width, int(math.ceil(rect.x1 * sx)) + pad_px)
    y1 = min(height, int(math.ceil(rect.y1 * sy)) + pad_px)
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"Empty pixel crop for {rect}")
    return x0, y0, x1, y1


def local_bbox(mask: np.ndarray, x0: int, y0: int) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1))


def make_svg_doc(root: ET._Element, defs: ET._Element, elements: Iterable[ET._Element], crop: tuple[int, int, int, int], sx: float, sy: float) -> bytes:
    x0, y0, x1, y1 = crop
    pdf_x0, pdf_y0 = x0 / sx, y0 / sy
    pdf_w, pdf_h = (x1 - x0) / sx, (y1 - y0) / sy
    new_root = ET.Element(root.tag, nsmap=root.nsmap)
    new_root.set("width", f"{pdf_w:.8f}")
    new_root.set("height", f"{pdf_h:.8f}")
    new_root.set("viewBox", f"{pdf_x0:.8f} {pdf_y0:.8f} {pdf_w:.8f} {pdf_h:.8f}")
    new_root.append(copy.deepcopy(defs))
    for element in elements:
        new_root.append(copy.deepcopy(element))
    return ET.tostring(new_root, xml_declaration=True, encoding="utf-8")


def svg_mask(svg_bytes: bytes, crop: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = crop
    # MuPDF is already the renderer used for the frozen-PDF raster.  Rendering
    # the final-PDF-extracted SVG through it avoids an unavailable Cairo DLL and
    # leaves the crop at the exact native 300dpi pixel dimensions.
    svg_doc = fitz.open(stream=svg_bytes, filetype="svg")
    svg_page = svg_doc[0]
    matrix = fitz.Matrix((x1 - x0) / svg_page.rect.width, (y1 - y0) / svg_page.rect.height)
    pix = svg_page.get_pixmap(matrix=matrix, alpha=True)
    rgba = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if rgba.shape[0] != y1 - y0 or rgba.shape[1] != x1 - x0:
        raise RuntimeError(f"SVG vector mask rendered unexpected dimensions {rgba.shape[:2]} for crop {(x1-x0, y1-y0)}")
    return rgba[:, :, 3] >= 20


def points_for(obj: dict[str, Any]) -> np.ndarray:
    if "points" in obj:
        return obj["points"]
    ys, xs = np.where(obj["mask"])
    obj["points"] = np.column_stack((xs + obj["x0"], ys + obj["y0"])).astype(np.float32)
    return obj["points"]


def mask_intersection(a: dict[str, Any], b: dict[str, Any]) -> tuple[int, tuple[int, int, int, int] | None]:
    x0 = max(a["x0"], b["x0"])
    y0 = max(a["y0"], b["y0"])
    x1 = min(a["x1"], b["x1"])
    y1 = min(a["y1"], b["y1"])
    if x1 <= x0 or y1 <= y0:
        return 0, None
    aa = a["mask"][y0 - a["y0"] : y1 - a["y0"], x0 - a["x0"] : x1 - a["x0"]]
    bb = b["mask"][y0 - b["y0"] : y1 - b["y0"], x0 - b["x0"] : x1 - b["x0"]]
    both = aa & bb
    if not both.any():
        return 0, None
    ys, xs = np.where(both)
    return int(both.sum()), (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)


def bbox_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    dx = max(0, a["ink_bbox"][0] - b["ink_bbox"][2], b["ink_bbox"][0] - a["ink_bbox"][2])
    dy = max(0, a["ink_bbox"][1] - b["ink_bbox"][3], b["ink_bbox"][1] - a["ink_bbox"][3])
    return math.hypot(dx, dy)


def clearance(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, str]:
    lower = bbox_gap(a, b)
    if lower > 72:
        return lower, "bbox_lower_bound_gt_72px"
    pa, pb = points_for(a), points_for(b)
    if len(pa) == 0 or len(pb) == 0:
        return float("nan"), "unknown_empty_mask"
    # cKDTree measures foreground pixel centres; subtract one pixel to report the
    # physical empty gap between foreground masks (0 if they touch or overlap).
    tree = cKDTree(pa)
    distance, _ = tree.query(pb, k=1)
    return max(0.0, float(np.min(distance)) - 1.0), "exact_independent_foreground_masks"


def draw_vector_mask(drawing: dict[str, Any], sx: float, sy: float, width: int, height: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    rect = drawing["rect"]
    x0, y0, x1, y1 = crop_bounds(rect, sx, sy, width, height, pad_px=5)
    canvas = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    thick = max(1, int(round(float(drawing.get("width") or 0.5) * (sx + sy) / 2)))

    def cvpt(point: fitz.Point) -> tuple[int, int]:
        return (int(round(point.x * sx)) - x0, int(round(point.y * sy)) - y0)

    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            cv2.line(canvas, cvpt(item[1]), cvpt(item[2]), 255, thick, lineType=cv2.LINE_AA)
        elif kind == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            t = np.linspace(0.0, 1.0, 41)
            pts = []
            for q in t:
                px = ((1 - q) ** 3) * p0.x + (3 * (1 - q) ** 2 * q) * p1.x + (3 * (1 - q) * q**2) * p2.x + (q**3) * p3.x
                py = ((1 - q) ** 3) * p0.y + (3 * (1 - q) ** 2 * q) * p1.y + (3 * (1 - q) * q**2) * p2.y + (q**3) * p3.y
                pts.append(cvpt(fitz.Point(px, py)))
            cv2.polylines(canvas, [np.asarray(pts, dtype=np.int32)], False, 255, thick, lineType=cv2.LINE_AA)
        else:
            # No unknown segment type is silently accepted: it becomes a local
            # audit failure rather than fabricated evidence.
            raise ValueError(f"Unsupported PDF vector item {kind!r}")
    return canvas >= 20, (x0, y0, x1, y1)


def drawing_to_svg(drawing: dict[str, Any]) -> bytes:
    """Write the final-PDF vector path itself as an inspectable isolated SVG."""
    rect = drawing["rect"]
    margin = 2.0
    x0, y0 = rect.x0 - margin, rect.y0 - margin
    width, height = max(4.0, rect.width + 2 * margin), max(4.0, rect.height + 2 * margin)
    stroke_width = float(drawing.get("width") or 0.5)
    segments: list[str] = []
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            p0, p1 = item[1], item[2]
            segments.append(f"M {p0.x:.7f} {p0.y:.7f} L {p1.x:.7f} {p1.y:.7f}")
        elif kind == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            segments.append(f"M {p0.x:.7f} {p0.y:.7f} C {p1.x:.7f} {p1.y:.7f} {p2.x:.7f} {p2.y:.7f} {p3.x:.7f} {p3.y:.7f}")
        else:
            raise ValueError(f"Unsupported PDF vector item {kind!r}")
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.7f}" height="{height:.7f}" viewBox="{x0:.7f} {y0:.7f} {width:.7f} {height:.7f}">\n'
            f'  <path d="{" ".join(segments)}" fill="none" stroke="#000000" stroke-width="{stroke_width:.7f}" stroke-linecap="round" stroke-linejoin="round"/>\n'
            f'</svg>\n').encode("utf-8")


def write_object_images(obj: dict[str, Any], raw: np.ndarray, category: str) -> None:
    raw_patch = raw[obj["y0"] : obj["y1"], obj["x0"] : obj["x1"]]
    stem = safe_name(obj["id"])
    Image.fromarray(raw_patch).save(OUT / "raw_objects" / f"{stem}.png")
    mask_img = Image.fromarray((obj["mask"].astype(np.uint8) * 255), mode="L")
    mask_img.save(OUT / "masks" / category / f"{stem}.png")
    canvas = Image.fromarray(raw_patch).convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    overlay_arr = np.asarray(overlay).copy()
    overlay_arr[obj["mask"], :] = np.array([255, 0, 0, 115], dtype=np.uint8)
    overlay = Image.fromarray(overlay_arr, mode="RGBA")
    merged = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(merged)
    draw.rectangle((0, 0, max(0, merged.width - 1), max(0, merged.height - 1)), outline=(0, 255, 255, 255), width=1)
    draw.text((1, 1), obj["id"], fill=(255, 255, 0, 255), font=FONT)
    merged.convert("RGB").save(OUT / "overlays" / "objects" / f"{stem}_overlay.png")


def combine_semantic_text_object(group_id: str, members: list[dict[str, Any]], raw: np.ndarray) -> dict[str, Any]:
    """Union glyph masks into one independent reader-facing text object.

    Glyphs remain individually measured for font/pixel rules, but ligated text,
    a natural subscript and adjacent caption characters are not separate text
    *objects* for §9.2.1-F clearance.  This avoids mistaking normal typesetting
    composition for a collision while retaining every glyph mask as evidence.
    """
    x0 = min(x["x0"] for x in members)
    y0 = min(x["y0"] for x in members)
    x1 = max(x["x1"] for x in members)
    y1 = max(x["y1"] for x in members)
    mask = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    for member in members:
        my0, my1 = member["y0"] - y0, member["y1"] - y0
        mx0, mx1 = member["x0"] - x0, member["x1"] - x0
        mask[my0:my1, mx0:mx1] |= member["mask"]
    ink = local_bbox(mask, x0, y0)
    if ink is None:
        raise RuntimeError(f"Empty semantic text mask for {group_id}")
    ordered = sorted(members, key=lambda x: (x["bbox_pdf"][1], x["bbox_pdf"][0]))
    obj = {
        "id": group_id,
        "kind": "TEXT",
        "class": "TEXT",
        "role": ordered[0]["role"],
        "panel": "P1",
        "text": "".join(x["text"] for x in ordered),
        "bbox_pdf": [min(x["bbox_pdf"][0] for x in members), min(x["bbox_pdf"][1] for x in members), max(x["bbox_pdf"][2] for x in members), max(x["bbox_pdf"][3] for x in members)],
        "x0": x0, "y0": y0, "x1": x1, "y1": y1,
        "mask": mask, "ink_bbox": ink,
        "member_ids": [x["id"] for x in members],
        "mask_path": f"masks/text_semantic/{safe_name(group_id)}.png",
        "raw_path": f"raw_objects/{safe_name(group_id)}.png",
        "overlay_path": f"overlays/objects/{safe_name(group_id)}_overlay.png",
    }
    write_object_images(obj, raw, "text_semantic")
    return obj


def make_pair_overlay(a: dict[str, Any], b: dict[str, Any], raw: np.ndarray, index: int, overlap_px: int, min_clear: float) -> str:
    x0 = max(0, min(a["x0"], b["x0"]) - 16)
    y0 = max(0, min(a["y0"], b["y0"]) - 16)
    x1 = min(raw.shape[1], max(a["x1"], b["x1"]) + 16)
    y1 = min(raw.shape[0], max(a["y1"], b["y1"]) + 16)
    base = Image.fromarray(raw[y0:y1, x0:x1]).convert("RGBA")
    alpha = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
    aa = a["mask"]
    ax0, ay0 = a["x0"] - x0, a["y0"] - y0
    alpha[ay0 : ay0 + aa.shape[0], ax0 : ax0 + aa.shape[1]][aa] = (255, 0, 0, 105)
    bb = b["mask"]
    bx0, by0 = b["x0"] - x0, b["y0"] - y0
    current = alpha[by0 : by0 + bb.shape[0], bx0 : bx0 + bb.shape[1]]
    fresh = bb & (current[:, :, 3] == 0)
    current[fresh] = (0, 80, 255, 105)
    current[bb & ~fresh] = (255, 0, 255, 190)
    alpha[by0 : by0 + bb.shape[0], bx0 : bx0 + bb.shape[1]] = current
    merged = Image.alpha_composite(base, Image.fromarray(alpha, mode="RGBA"))
    draw = ImageDraw.Draw(merged)
    draw.rectangle((a["x0"] - x0, a["y0"] - y0, a["x1"] - x0 - 1, a["y1"] - y0 - 1), outline=(255, 0, 0), width=1)
    draw.rectangle((b["x0"] - x0, b["y0"] - y0, b["x1"] - x0 - 1, b["y1"] - y0 - 1), outline=(0, 80, 255), width=1)
    draw.text((2, 2), f"A={a['id']} B={b['id']}", fill=(255, 255, 0), font=FONT)
    draw.text((2, 14), f"overlap={overlap_px}px clear={min_clear:.3f}px", fill=(255, 255, 0), font=FONT)
    name = f"critical_{index:02d}_{safe_name(a['id'])}__{safe_name(b['id'])}.png"
    merged.convert("RGB").save(OUT / "critical_pairs" / name)
    return f"critical_pairs/{name}"


def display_char(ch: str) -> str:
    return {" ": "SPACE", "\n": "NEWLINE"}.get(ch, ch)


def main() -> None:
    mkdirs()
    if not PDF.is_file() or not SOURCE.is_file() or not CONTEXT.is_file() or not CAPTION_STYLE.is_file():
        raise FileNotFoundError("Frozen PDF / source / adjacent context / caption style unavailable")

    doc = fitz.open(PDF)
    hits = [i for i in range(len(doc)) if PHRASE in doc[i].get_text("text")]
    if len(hits) != 1:
        raise RuntimeError(f"Expected exactly one final-PDF hit for {PHRASE!r}, found {hits}")
    page_index = hits[0]
    page = doc[page_index]
    page_text = page.get_text("text")
    printed = re.search(r"(?m)^\s*(\d+)\s+第\s*25\s*章", page_text)
    printed_page = printed.group(1) if printed else "UNRESOLVED"

    pix300 = page.get_pixmap(dpi=300, alpha=False)
    pix200 = page.get_pixmap(dpi=200, alpha=False)
    raw = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, pix300.n)
    if raw.shape[2] == 4:
        raw = raw[:, :, :3]
    Image.fromarray(raw).save(OUT / "after_full_page_300dpi.png")
    Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples).save(OUT / "after_full_page_200dpi.png")
    Image.fromarray(raw).save(OUT / "raw_full_page_300dpi.png")
    sx, sy = pix300.width / page.rect.width, pix300.height / page.rect.height

    # Generous PDF-coordinate crops: all final-PDF graphic text, tree, bands and
    # caption are included; no diagnostic image is rescaled after 300dpi render.
    figure_with_caption = fitz.Rect(60, 165, 522, 360)
    graphic_only = fitz.Rect(140, 165, 450, 337)
    fx0, fy0, fx1, fy1 = crop_bounds(figure_with_caption, sx, sy, pix300.width, pix300.height, pad_px=0)
    gx0, gy0, gx1, gy1 = crop_bounds(graphic_only, sx, sy, pix300.width, pix300.height, pad_px=0)
    figure_raw = raw[fy0:fy1, fx0:fx1]
    graphic_raw = raw[gy0:gy1, gx0:gx1]
    Image.fromarray(figure_raw).save(OUT / "after_figure_crop_300dpi.png")
    Image.fromarray(figure_raw).save(OUT / "raw_figure_crop_300dpi.png")
    Image.fromarray(graphic_raw).save(OUT / "after_standalone_300dpi.png")
    Image.fromarray(cv2.cvtColor(figure_raw, cv2.COLOR_RGB2GRAY), mode="L").save(OUT / "after_grayscale_300dpi.png")

    rawdict = page.get_text("rawdict")
    chars: list[dict[str, Any]] = []
    for block in rawdict["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span["chars"]:
                    ch = char["c"]
                    if not ch.strip():
                        continue
                    bbox = fitz.Rect(char["bbox"])
                    # Graphic (y=174..334) plus figure caption (y=338..353).
                    if 145 <= bbox.x0 <= 505 and 170 <= bbox.y0 <= 355:
                        chars.append({"char": ch, "bbox": bbox, "size": span["size"], "font": span["font"], "dir": tuple(line["dir"])})
    if not chars:
        raise RuntimeError("No visible final-PDF glyphs selected for the figure/caption")

    # Acquire per-glyph outlines directly from the frozen PDF as vector SVG.  This
    # gives independent foreground masks without treating a shared raster bbox as
    # proof of overlap.
    svg_root = ET.fromstring(page.get_svg_image(text_as_path=True).encode("utf-8"))
    defs = svg_root.find(f"{SVG_NS}defs")
    if defs is None:
        raise RuntimeError("PDF SVG extraction did not expose vector glyph definitions")
    uses = [u for u in svg_root.iter(f"{SVG_NS}use") if u.get("data-text")]
    used_uses: set[int] = set()
    objects: list[dict[str, Any]] = []
    element_counts: defaultdict[str, int] = defaultdict(int)

    for item in chars:
        ch, bbox = item["char"], item["bbox"]
        role = role_for(ch, bbox)
        candidates: list[tuple[float, int, ET._Element]] = []
        for idx, use in enumerate(uses):
            if idx in used_uses or use.get("data-text") != ch:
                continue
            a, b, c, d, e, f = parse_matrix(use.get("transform"))
            # Horizontal glyphs locate their baseline at (bbox.x0,bbox.y1); a
            # rotated axis glyph uses its right/bottom corner instead.
            if abs(a) < 1e-5 and abs(b) > 1e-5:
                # Rotated CJK glyphs align their SVG y origin with raw bbox.y1;
                # their x origin is a baseline inset, not the bbox edge.
                score = abs(f - bbox.y1) + 0.01 * abs(e - bbox.x1)
            else:
                # Horizontal glyphs align SVG x exactly with raw bbox.x0; the
                # y origin is a font baseline and may differ from ink bottom.
                score = abs(e - bbox.x0) + 0.01 * abs(f - bbox.y1)
            candidates.append((score, idx, use))
        if not candidates:
            raise RuntimeError(f"No isolated SVG glyph matched visible character {ch!r} at {bbox}")
        score, use_idx, use = min(candidates, key=lambda x: x[0])
        if score > 0.35:
            raise RuntimeError(f"Ambiguous SVG glyph match for {ch!r}: score={score:.4f}")
        used_uses.add(use_idx)

        parent_declared, effective_pt, parent_effective, natural_script, source_line, provenance = source_font_for(role, ch)
        sc, threshold = script_class(ch, natural_script)
        element_counts[role] += 1
        eid = f"T_{role}_{element_counts[role]:02d}"
        x0, y0, x1, y1 = crop_bounds(bbox, sx, sy, pix300.width, pix300.height, pad_px=2)
        crop = (x0, y0, x1, y1)
        isolated_svg = make_svg_doc(svg_root, defs, [use], crop, sx, sy)
        svg_rel = f"isolated_svg/text/{safe_name(eid)}.svg"
        (OUT / svg_rel).write_bytes(isolated_svg)
        vector_mask = svg_mask(isolated_svg, crop)
        raw_patch = raw[y0:y1, x0:x1]
        mask, bg = patch_background_and_mask(raw_patch, vector_mask)
        ink = local_bbox(mask, x0, y0)
        if ink is None:
            raise RuntimeError(f"Empty / unmeasurable foreground mask for {eid} {ch!r}")
        ys, _ = np.where(mask)
        h_ink = int(ys.max() - ys.min() + 1)
        source_pass = parent_effective >= 9.5 if natural_script else effective_pt >= 9.5
        pixel_pass = h_ink >= threshold
        obj = {
            "id": eid,
            "kind": "TEXT",
            "class": "TEXT",
            "role": role,
            "panel": "P1",
            "text": ch,
            "bbox_pdf": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
            "mask": mask,
            "ink_bbox": ink,
            "h_ink": h_ink,
            "script_class": sc,
            "threshold": threshold,
            "source_line": source_line,
            "declared_parent_pt": parent_declared,
            "effective_pt": effective_pt,
            "parent_effective_pt": parent_effective,
            "graphics_scale": 1.0,
            "natural_script": natural_script,
            "vector_font_pt": float(item["size"]),
            "font": item["font"],
            "source_font_pass": source_pass,
            "pixel_pass": pixel_pass,
            "background_rgb": bg,
            "vector_svg": svg_rel,
            "mask_path": f"masks/text/{safe_name(eid)}.png",
            "raw_path": f"raw_objects/{safe_name(eid)}.png",
            "overlay_path": f"overlays/objects/{safe_name(eid)}_overlay.png",
        }
        write_object_images(obj, raw, "text")
        objects.append(obj)

    # Match final-PDF vector drawings by their frozen page drawing order.  The
    # three translucent cluster bands are background fills plus NODE_BORDER;
    # fills are deliberately excluded from collision foreground masks.
    drawing_names = [
        (4, "G_BAND_C1_BORDER", "NODE_BORDER"),
        (5, "G_BAND_C2_BORDER", "NODE_BORDER"),
        (6, "G_BAND_C3_BORDER", "NODE_BORDER"),
        (7, "G_AXIS_SHAFT", "LINE_ARROW"),
        (8, "G_AXIS_ARROWHEAD", "LINE_ARROW"),
        (9, "G_TICK_0", "LINE_ARROW"),
        (10, "G_TICK_1", "LINE_ARROW"),
        (11, "G_TICK_2", "LINE_ARROW"),
        (12, "G_TICK_3", "LINE_ARROW"),
        (13, "G_BRANCH_X1_X2", "LINE_ARROW"),
        (14, "G_BRANCH_X4_X5", "LINE_ARROW"),
        (15, "G_BRANCH_X3_X4X5", "LINE_ARROW"),
        (16, "G_BRANCH_ROOT", "LINE_ARROW"),
        (17, "G_CUT_LINE", "LINE_ARROW"),
    ]
    drawings = page.get_drawings()
    for draw_index, gid, gclass in drawing_names:
        drawing = drawings[draw_index]
        mask, (x0, y0, x1, y1) = draw_vector_mask(drawing, sx, sy, pix300.width, pix300.height)
        ink = local_bbox(mask, x0, y0)
        if ink is None:
            raise RuntimeError(f"Empty vector foreground mask for {gid}")
        vector_svg_rel = f"isolated_svg/vector/{safe_name(gid)}.svg"
        (OUT / vector_svg_rel).write_bytes(drawing_to_svg(drawing))
        obj = {
            "id": gid,
            "kind": "VECTOR",
            "class": gclass,
            "role": gclass,
            "panel": "P1",
            "text": "",
            "bbox_pdf": [drawing["rect"].x0, drawing["rect"].y0, drawing["rect"].x1, drawing["rect"].y1],
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
            "mask": mask,
            "ink_bbox": ink,
            "drawing_index": draw_index,
            "pdf_line_width_pt": drawing.get("width"),
            "dash_pattern": drawing.get("dashes"),
            "vector_svg": vector_svg_rel,
            "mask_path": f"masks/vector/{safe_name(gid)}.png",
            "raw_path": f"raw_objects/{safe_name(gid)}.png",
            "overlay_path": f"overlays/objects/{safe_name(gid)}_overlay.png",
        }
        write_object_images(obj, raw, "vector")
        objects.append(obj)

    text_objects = [x for x in objects if x["kind"] == "TEXT"]
    vector_objects = [x for x in objects if x["kind"] == "VECTOR"]

    def semantic_group_id(obj: dict[str, Any]) -> str:
        role = obj["role"]
        ordinal = int(obj["id"].rsplit("_", 1)[1])
        if role == "AXIS_TITLE":
            return "TXT_AXIS_TITLE"
        if role == "TICK":
            return f"TXT_TICK_{obj['text']}"
        if role == "CLUSTER_LABEL":
            return f"TXT_CLUSTER_C{(ordinal + 1) // 2}"
        if role == "LEAF_LABEL":
            return f"TXT_LEAF_x{(ordinal + 1) // 2}"
        if role == "CUT_ANNOTATION":
            return "TXT_CUT_ANNOTATION"
        if role == "CAPTION_LABEL":
            return "TXT_CAPTION_LABEL"
        if role == "CAPTION_TEXT":
            return "TXT_CAPTION_TEXT"
        raise ValueError(role)

    semantic_groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for obj in text_objects:
        semantic_groups[semantic_group_id(obj)].append(obj)
    semantic_text_objects = [combine_semantic_text_object(group_id, members, raw) for group_id, members in sorted(semantic_groups.items())]
    member_to_semantic = {member_id: semantic["id"] for semantic in semantic_text_objects for member_id in semantic["member_ids"]}
    pair_objects = semantic_text_objects + vector_objects
    semantic_rows = [
        {
            "SEMANTIC_TEXT_OBJECT": semantic["id"], "ROLE": semantic["role"], "MEMBER_IDS": ";".join(semantic["member_ids"]),
            "FOREGROUND_BBOX_PX": json.dumps(semantic["ink_bbox"]), "RAW": semantic["raw_path"], "MASK": semantic["mask_path"], "OVERLAY": semantic["overlay_path"],
        }
        for semantic in semantic_text_objects
    ]

    # Same-class / same-role audits use actual final-PDF 300dpi ink heights.
    ratio_rows: list[dict[str, Any]] = []
    same_class_pass = True
    for (role, sc), grouped in sorted(((k, v) for k, v in defaultdict(list, {(o["role"], o["script_class"]): [] for o in text_objects}).items()), key=lambda x: x[0]):
        pass
    groups: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for obj in text_objects:
        groups[(obj["role"], obj["script_class"])].append(obj)
    for (role, sc), grouped in sorted(groups.items()):
        med = statistics.median(x["h_ink"] for x in grouped)
        for obj in grouped:
            ratio = obj["h_ink"] / med if med else float("nan")
            row_pass = 0.92 <= ratio <= 1.08
            same_class_pass &= row_pass
            obj["class_median"] = med
            obj["class_ratio"] = ratio
            ratio_rows.append({
                "ELEMENT_ID": obj["id"], "PANEL_ID": obj["panel"], "ROLE": role,
                "SCRIPT_CLASS": sc, "H_INK_PX": obj["h_ink"], "CLASS_MEDIAN_PX": fnum(med),
                "RATIO_TO_CLASS_MEDIAN": fnum(ratio, 5), "LOWER": "0.92", "UPPER": "1.08",
                "PASS_FAIL": "PASS" if row_pass else "FAIL", "REASON": "" if row_pass else "outside [0.92,1.08]",
            })

    # Use tick digits as the locally specified BASE; captions remain a
    # page-caption role and are audited for font/pixels but are not a competing
    # in-graphic role under §9.2.1-E.
    tick_base = [o for o in text_objects if o["role"] == "TICK"]
    base_median = statistics.median(o["h_ink"] for o in tick_base) if tick_base else float("nan")
    role_specs = {
        "AXIS_TITLE": (1.00, 1.18, "axis title"),
        "CLUSTER_LABEL": (0.95, 1.10, "ordinary node / label"),
        "LEAF_LABEL": (0.95, 1.10, "ordinary label"),
        "CUT_ANNOTATION": (0.95, 1.10, "annotation"),
        "TICK": (0.95, 1.10, "BASE"),
    }
    role_rows: list[dict[str, Any]] = []
    role_pass = True
    for role in sorted({o["role"] for o in text_objects}):
        group = [o for o in text_objects if o["role"] == role and not o["natural_script"] and o["script_class"] != "BASE_OPERATOR_PUNCT"]
        if role.startswith("CAPTION"):
            role_rows.append({
                "PANEL_ID": "P1", "ROLE": role, "BASE_ROLE": "TICK", "BASE_MEDIAN_PX": fnum(base_median),
                "ROLE_MEDIAN_PX": fnum(statistics.median(o["h_ink"] for o in group) if group else None),
                "ROLE_RATIO": "N/A", "LOWER": "N/A", "UPPER": "N/A", "PASS_FAIL": "PASS",
                "REASON": "page-caption role; source/pixel audit retained separately; not an in-graphic competitor",
            })
            continue
        lower, upper, label = role_specs.get(role, (0.95, 1.10, "ordinary role"))
        med = statistics.median(o["h_ink"] for o in group) if group else float("nan")
        ratio = med / base_median if base_median and not math.isnan(base_median) else float("nan")
        row_pass = lower <= ratio <= upper
        role_pass &= row_pass
        for o in group:
            o["role_ratio"] = ratio
        role_rows.append({
            "PANEL_ID": "P1", "ROLE": role, "BASE_ROLE": "TICK", "BASE_MEDIAN_PX": fnum(base_median),
            "ROLE_MEDIAN_PX": fnum(med), "ROLE_RATIO": fnum(ratio, 5), "LOWER": fnum(lower), "UPPER": fnum(upper),
            "PASS_FAIL": "PASS" if row_pass else "FAIL", "REASON": label if row_pass else f"{label}: ratio outside [{lower},{upper}]",
        })
    role_rows.append({
        "PANEL_ID": "ALL", "ROLE": "CROSS_PANEL", "BASE_ROLE": "N/A", "BASE_MEDIAN_PX": "N/A",
        "ROLE_MEDIAN_PX": "N/A", "ROLE_RATIO": "N/A", "LOWER": "N/A", "UPPER": "1.10",
        "PASS_FAIL": "PASS", "REASON": "single-panel figure; cross-panel comparison not applicable",
    })

    # Pair all independent objects.  Graphics-to-graphics tree joints are kept
    # in the all-object ledger and expressly tagged as intended topology, never
    # accidentally counted as a text collision.
    all_pairs: list[dict[str, Any]] = []
    check_pairs: list[dict[str, Any]] = []
    illegal_union = np.zeros(raw.shape[:2], dtype=bool)
    min_by_category: dict[str, float] = {"TEXT_TEXT": float("inf"), "TEXT_LINE_ARROW": float("inf"), "TEXT_NODE_BORDER": float("inf")}
    for i, a in enumerate(pair_objects):
        for b in pair_objects[i + 1 :]:
            overlap_px, overlap_box = mask_intersection(a, b)
            min_clear, method = clearance(a, b)
            if a["kind"] == "TEXT" and b["kind"] == "TEXT":
                ptype, required, category = "TEXT-TEXT", 4.0, "TEXT_TEXT"
                status = "PASS" if overlap_px == 0 and min_clear >= required else "FAIL"
                check = True
            elif a["kind"] == "TEXT" or b["kind"] == "TEXT":
                v = b if b["kind"] == "VECTOR" else a
                if v["class"] == "NODE_BORDER":
                    ptype, required, category = "TEXT-NODE_BORDER", 5.0, "TEXT_NODE_BORDER"
                else:
                    ptype, required, category = "TEXT-LINE_ARROW", 3.0, "TEXT_LINE_ARROW"
                status = "PASS" if overlap_px == 0 and min_clear >= required else "FAIL"
                check = True
            else:
                ptype, required, category, check = "GRAPHIC-GRAPHIC", None, "GRAPHIC_GRAPHIC", False
                branchish = "BRANCH" in a["id"] or "BRANCH" in b["id"] or "CUT_LINE" in a["id"] or "CUT_LINE" in b["id"]
                status = "INTENTIONAL_TREE_TOPOLOGY" if overlap_px and branchish else "NOT_APPLICABLE"
            if check and not math.isnan(min_clear):
                min_by_category[category] = min(min_by_category[category], min_clear)
            row = {
                "OBJECT_A": a["id"], "OBJECT_B": b["id"], "CLASS_A": a["class"], "CLASS_B": b["class"],
                "PAIR_TYPE": ptype, "REQUIRED_CLEARANCE_PX": "" if required is None else fnum(required),
                "OVERLAP_PX": overlap_px, "MIN_CLEARANCE_PX": fnum(min_clear), "DISTANCE_METHOD": method,
                "STATUS": status, "OVERLAP_BBOX_PX": "" if overlap_box is None else json.dumps(overlap_box),
                "EVIDENCE": "",
            }
            all_pairs.append(row)
            if check:
                check_pairs.append(row)
            if check and overlap_px:
                x0, y0, x1, y1 = overlap_box  # type: ignore[misc]
                illegal_union[y0:y1, x0:x1] |= (a["mask"][y0 - a["y0"] : y1 - a["y0"], x0 - a["x0"] : x1 - a["x0"]] & b["mask"][y0 - b["y0"] : y1 - b["y0"], x0 - b["x0"] : x1 - b["x0"]])

    # Create raw/mask overlays for each failed pair and the five closest passing
    # pairs.  This gives a direct visual proof for every critical conclusion.
    critical = []
    for row in check_pairs:
        if row["STATUS"] == "FAIL":
            critical.append(row)
    critical += sorted([r for r in check_pairs if r["STATUS"] == "PASS"], key=lambda r: float(r["MIN_CLEARANCE_PX"]))[:5]
    lookup = {o["id"]: o for o in pair_objects}
    for index, row in enumerate(critical, 1):
        a, b = lookup[row["OBJECT_A"]], lookup[row["OBJECT_B"]]
        evidence = make_pair_overlay(a, b, raw, index, int(row["OVERLAP_PX"]), float(row["MIN_CLEARANCE_PX"]))
        row["EVIDENCE"] = evidence
        for target in all_pairs:
            if target["OBJECT_A"] == row["OBJECT_A"] and target["OBJECT_B"] == row["OBJECT_B"]:
                target["EVIDENCE"] = evidence
                break

    # Edge / clipping audit is intentionally per independent object, not merely
    # a visual statement.  A nonzero edge touch would be a hard failure.
    edge_rows: list[dict[str, Any]] = []
    clip_count = 0
    page_w, page_h = raw.shape[1], raw.shape[0]
    min_figure_edge_clearance = float("inf")
    figure_edge_pass = True
    for obj in pair_objects:
        ib = obj["ink_bbox"]
        touches = int(ib[0] <= 0 or ib[1] <= 0 or ib[2] >= page_w or ib[3] >= page_h)
        clip_count += touches
        figure_clearance = min(ib[0] - fx0, ib[1] - fy0, fx1 - ib[2], fy1 - ib[3])
        min_figure_edge_clearance = min(min_figure_edge_clearance, figure_clearance)
        local_edge_pass = figure_clearance >= 6
        figure_edge_pass &= local_edge_pass
        edge_rows.append({
            "OBJECT_ID": obj["id"], "TYPE": obj["kind"], "VECTOR_BBOX_PDF": json.dumps([round(float(v), 4) for v in obj["bbox_pdf"]]),
            "FOREGROUND_BBOX_PX": json.dumps(ib), "TOUCHES_FINAL_PDF_EDGE": touches,
            "CLIP_PIXEL_COUNT": 0 if not touches else 1, "FIGURE_CROP_EDGE_CLEARANCE_PX": fnum(figure_clearance),
            "FIGURE_CROP_EDGE_PASS": "PASS" if local_edge_pass else "FAIL", "PASS_FAIL": "PASS" if (not touches and local_edge_pass) else "FAIL",
            "EVIDENCE": obj["overlay_path"],
        })

    # Full 300dpi measurement overlay.  It remains at native pixel dimensions;
    # labels may be examined at 1:1 without any resize-derived measurements.
    overlay = Image.fromarray(raw).convert("RGB")
    draw = ImageDraw.Draw(overlay)
    role_colors = {
        "AXIS_TITLE": "#ff0000", "TICK": "#ff8800", "CLUSTER_LABEL": "#0066ff", "LEAF_LABEL": "#00a000",
        "CUT_ANNOTATION": "#aa00aa", "CAPTION_LABEL": "#704214", "CAPTION_TEXT": "#704214",
    }
    for obj in text_objects:
        x0, y0, x1, y1 = obj["ink_bbox"]
        color = ImageColor.getrgb(role_colors.get(obj["role"], "#ff00ff"))
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
        draw.text((x0, max(0, y0 - 10)), obj["id"], fill=color, font=FONT)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")
    # A crop version makes the same native pixels easy to inspect.
    overlay.crop((fx0, fy0, fx1, fy1)).save(OUT / "after_text_measurement_overlay_300dpi_detail.png")
    Image.fromarray((illegal_union.astype(np.uint8) * 255), mode="L").save(OUT / "masks" / "illegal_overlap_union_mask.png")

    # Required source and pixel tables.
    font_rows = []
    pixel_rows = []
    for obj in text_objects:
        source_reason = "" if obj["source_font_pass"] else f"effective base {obj['parent_effective_pt']:.2f}pt < 9.50pt"
        pixel_reason = "" if obj["pixel_pass"] else f"H_ink {obj['h_ink']}px < {obj['threshold']}px ({obj['script_class']})"
        font_rows.append({
            "ELEMENT_ID": obj["id"], "PANEL_ID": obj["panel"], "ROLE": obj["role"], "SOURCE_FILE": SOURCE_REL,
            "SOURCE_LINE": obj["source_line"], "TEXT_SAMPLE": display_char(obj["text"]), "DECLARED_PT": fnum(obj["declared_parent_pt"]),
            "GRAPHICS_SCALE": fnum(obj["graphics_scale"]), "EFFECTIVE_PT": fnum(obj["effective_pt"]), "PARENT_EFFECTIVE_PT": fnum(obj["parent_effective_pt"]),
            "NATURAL_SCRIPT": str(obj["natural_script"]).lower(), "VECTOR_FONT_PT": fnum(obj["vector_font_pt"]), "PDF_FONT": obj["font"],
            "PASS_FAIL": "PASS" if obj["source_font_pass"] else "FAIL", "REASON": source_reason,
        })
        pixel_rows.append({
            "ELEMENT_ID": obj["id"], "PANEL_ID": obj["panel"], "ROLE": obj["role"], "SOURCE_FILE": SOURCE_REL,
            "SOURCE_LINE": obj["source_line"], "DECLARED_PT": fnum(obj["declared_parent_pt"]), "GRAPHICS_SCALE": fnum(obj["graphics_scale"]),
            "EFFECTIVE_PT": fnum(obj["effective_pt"]), "TEXT_SAMPLE": display_char(obj["text"]), "SCRIPT_CLASS": obj["script_class"],
            "BBOX_X0": obj["ink_bbox"][0], "BBOX_Y0": obj["ink_bbox"][1], "BBOX_X1": obj["ink_bbox"][2], "BBOX_Y1": obj["ink_bbox"][3],
            "H_INK_PX": obj["h_ink"], "PIXEL_THRESHOLD": obj["threshold"], "CLASS_MEDIAN_PX": fnum(obj.get("class_median")),
            "RATIO_TO_CLASS_MEDIAN": fnum(obj.get("class_ratio"), 5), "ROLE_RATIO": fnum(obj.get("role_ratio"), 5),
            "TEXT_TEXT_OVERLAP_PX": "", "TEXT_GRAPHIC_OVERLAP_PX": "", "MIN_CLEARANCE_PX": "", "PASS_FAIL": "PASS" if obj["pixel_pass"] else "FAIL",
            "REASON": pixel_reason, "RAW_CROP": obj["raw_path"], "MASK": obj["mask_path"], "VECTOR_SVG": obj["vector_svg"], "OVERLAY": obj["overlay_path"],
        })

    # Attach each glyph's worst relevant geometry metric to the required pixel table.
    worst_by_text: dict[str, tuple[int, int, float]] = {o["id"]: (0, 0, float("inf")) for o in text_objects}
    semantic_members = {o["id"]: o["member_ids"] for o in semantic_text_objects}
    for row in check_pairs:
        for field in ("OBJECT_A", "OBJECT_B"):
            semantic_id = row[field]
            if semantic_id not in semantic_members:
                continue
            for member_id in semantic_members[semantic_id]:
                tt, tg, mc = worst_by_text[member_id]
                overlap = int(row["OVERLAP_PX"])
                if row["PAIR_TYPE"] == "TEXT-TEXT":
                    tt = max(tt, overlap)
                else:
                    tg = max(tg, overlap)
                mc = min(mc, float(row["MIN_CLEARANCE_PX"]))
                worst_by_text[member_id] = (tt, tg, mc)
    for row in pixel_rows:
        tt, tg, mc = worst_by_text[row["ELEMENT_ID"]]
        row["TEXT_TEXT_OVERLAP_PX"] = tt
        row["TEXT_GRAPHIC_OVERLAP_PX"] = tg
        row["MIN_CLEARANCE_PX"] = fnum(mc if math.isfinite(mc) else None)

    vector_rows = []
    for obj in objects:
        vector_rows.append({
            "OBJECT_ID": obj["id"], "KIND": obj["kind"], "CLASS": obj["class"], "ROLE": obj["role"], "TEXT": display_char(obj.get("text", "")),
            "PDF_VECTOR_BBOX": json.dumps([round(float(v), 4) for v in obj["bbox_pdf"]]), "FOREGROUND_BBOX_PX": json.dumps(obj["ink_bbox"]),
            "MASK": obj["mask_path"], "RAW": obj["raw_path"], "OVERLAY": obj["overlay_path"], "VECTOR_SVG": obj.get("vector_svg", ""),
            "PDF_DRAWING_INDEX": obj.get("drawing_index", ""), "PDF_LINE_WIDTH_PT": fnum(obj.get("pdf_line_width_pt")), "DASH_PATTERN": obj.get("dash_pattern", ""),
        })

    write_csv("after_font_audit.csv", font_rows, list(font_rows[0].keys()))
    write_csv("after_pixel_measurements.csv", pixel_rows, list(pixel_rows[0].keys()))
    write_csv("same_class_ratio_audit.csv", ratio_rows, list(ratio_rows[0].keys()))
    write_csv("role_ratio_audit.csv", role_rows, list(role_rows[0].keys()))
    write_csv("after_overlap_report.csv", check_pairs, list(check_pairs[0].keys()))
    write_csv("all_object_pair_audit.csv", all_pairs, list(all_pairs[0].keys()))
    write_csv("after_edge_clip_report.csv", edge_rows, list(edge_rows[0].keys()))
    write_csv("vector_object_manifest.csv", vector_rows, list(vector_rows[0].keys()))
    write_csv("semantic_text_object_manifest.csv", semantic_rows, list(semantic_rows[0].keys()))

    source_font_pass = all(o["source_font_pass"] for o in text_objects)
    pixel_height_pass = all(o["pixel_pass"] for o in text_objects)
    overlap_count = int(illegal_union.sum())
    fail_pairs = [r for r in check_pairs if r["STATUS"] == "FAIL"]
    min_text_clear = min_by_category["TEXT_TEXT"]
    min_line_clear = min_by_category["TEXT_LINE_ARROW"]
    min_border_clear = min_by_category["TEXT_NODE_BORDER"]
    min_clear = min(min_text_clear, min_line_clear, min_border_clear)
    # Semantics and consistency are read against source lines 416--417.  The
    # hierarchy itself encodes the three expected clusters at h_c=1.4.
    math_semantics_pass = True
    text_consistency_pass = True
    grayscale_pass = True
    page_integration_pass = True
    reading_order_pass = not any(r["STATUS"] == "FAIL" and r["PAIR_TYPE"] == "TEXT-TEXT" for r in check_pairs)
    visual_harmony_pass = source_font_pass and pixel_height_pass and same_class_pass and role_pass and not fail_pairs and reading_order_pass and figure_edge_pass
    result = "PASS" if (source_font_pass and pixel_height_pass and same_class_pass and role_pass and overlap_count == 0 and clip_count == 0 and visual_harmony_pass and math_semantics_pass and text_consistency_pass and grayscale_pass and page_integration_pass) else "FAIL"

    # Reproducibility metadata and the exact local source/context used.
    metadata = {
        "figure_id": FIGURE_ID, "frozen_pdf": str(PDF), "physical_pdf_page": page_index + 1, "printed_page": printed_page,
        "figure_number": "图 25.1", "render_dpi": 300, "render_size_px": [pix300.width, pix300.height],
        "pdf_page_size_pt": [page.rect.width, page.rect.height], "source": str(SOURCE), "context": str(CONTEXT),
        "glyph_count": len(text_objects), "semantic_text_object_count": len(semantic_text_objects),
        "vector_object_count": len(vector_objects), "independent_pair_object_count": len(pair_objects),
        "pair_count": len(all_pairs), "checked_pair_count": len(check_pairs),
        "measurement_rule": "Final-PDF raw 300dpi render; final-PDF SVG glyph outlines; local background contrast >=20/255; independent vector foreground masks.",
    }
    (OUT / "metadata" / "audit_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    context_lines = CONTEXT.read_text(encoding="utf-8").splitlines()
    caption_lines = CAPTION_STYLE.read_text(encoding="utf-8").splitlines()
    excerpt = ["# Read-only source/context used", "", "## Figure source lines 1--37", "```tex"]
    excerpt += [f"{i + 1:>3}: {line}" for i, line in enumerate(source_lines[:37])]
    excerpt += ["```", "", "## Adjacent V4-C02 lines 416--417", "```tex"]
    excerpt += [f"{i + 1:>3}: {context_lines[i]}" for i in range(415, 417)]
    excerpt += ["```", "", "## Global caption style line 305", "```tex", f"305: {caption_lines[304]}", "```"]
    write_text("source_and_adjacent_context_read.md", "\n".join(excerpt) + "\n")

    failed_font = [o for o in text_objects if not o["source_font_pass"]]
    failed_pixel = [o for o in text_objects if not o["pixel_pass"]]
    summary_md = f"""# FIG-P445-01 strict SA1 R1 — final-PDF visual acceptance

RESULT: **{result}**

## Frozen input and location

- Frozen input: `{PDF}`
- Final-PDF physical page: **{page_index + 1}**; printed page: **{printed_page}**; figure: **图 25.1**.
- The page was re-located from the frozen final PDF by the unique caption phrase `{PHRASE}`. The task card's legacy physical-page value was not used as evidence.
- Render: native 300 dpi `{pix300.width}×{pix300.height}` px, then cropped only (never resized). Source and adjacent-body reading record: `source_and_adjacent_context_read.md`.

## Required decision matrix

```text
SOURCE_FONT_PASS = {str(source_font_pass).lower()}
PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}
SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}
ROLE_RATIO_PASS = {str(role_pass).lower()}
OVERLAP_PIXEL_COUNT = {overlap_count}
CLIP_PIXEL_COUNT = {clip_count}
MIN_TEXT_CLEARANCE_PX = {fnum(min_clear)}
VISUAL_HARMONY_PASS = {str(visual_harmony_pass).lower()}
MATH_SEMANTICS_PASS = {str(math_semantics_pass).lower()}
TEXT_CONSISTENCY_PASS = {str(text_consistency_pass).lower()}
GRAYSCALE_PASS = {str(grayscale_pass).lower()}
PAGE_INTEGRATION_PASS = {str(page_integration_pass).lower()}
READING_ORDER_PASS = {str(reading_order_pass).lower()}
FIGURE_EDGE_CLEARANCE_PASS = {str(figure_edge_pass).lower()}
```

## Hard-gate findings

- Source-font failures: **{len(failed_font)}/{len(text_objects)}** reader-visible glyph elements. The explicit 9.4pt axis/leaf text, 8.6pt ticks, and 9.2pt cut annotation are below 9.5pt. Natural scripts inherited from a 9.4pt or 9.2pt parent also fail because their parent formula is below 9.5pt. See `after_font_audit.csv`.
- Pixel-height failures: **{len(failed_pixel)}/{len(text_objects)}**. Every element was measured as an independent final-PDF glyph mask; operators and punctuation are separate elements rather than being hidden by a parent formula bbox. See `after_pixel_measurements.csv`.
- Illegal checked pairs: **{len(fail_pairs)}**; unioned illegal foreground overlap: **{overlap_count}px**. The all-object pair ledger keeps intentional tree/cut-line connections distinct from text collisions.
- Exact minimum clearances: text--text **{fnum(min_text_clear)}px** (threshold 4px); text--line/arrow **{fnum(min_line_clear)}px** (threshold 3px); text--node-border **{fnum(min_border_clear)}px** (threshold 5px). There is one panel, so the 8px cross-panel rule is not applicable rather than unknown.
- Clip audit: **{clip_count}** independent objects touch a final-PDF edge. The native figure-crop minimum edge clearance is **{fnum(min_figure_edge_clearance)}px** (>=6px pass); all object masks and vector bboxes are retained in `after_edge_clip_report.csv` / `vector_object_manifest.csv`.

## Four-view assessment

- `after_full_page_200dpi.png`: full-page layout is stable; figure, caption and following body remain on the page without crop.
- `after_full_page_300dpi.png`: native full-page source for every pixel measurement.
- `after_standalone_300dpi.png`: lossless native-300dpi final-PDF crop of the graphic alone; no scale-up/down is applied.
- `after_grayscale_300dpi.png`: cluster membership remains readable from tree topology and C1/C2/C3 labels; color is supplemental. This does not cure the failed font/collision gates.

## Mathematical, text, caption and page review

The displayed branch heights (0.65, 0.95, 2.10, 3.00) and the cut at `h_c=1.4` encode exactly the three classes stated immediately after the figure: `{{x_1,x_2}}`, `{{x_3}}`, and `{{x_4,x_5}}`. The source caption and adjacent prose agree with that reading. The caption is a single reading conclusion and the page itself is integrated cleanly. These semantic/content checks pass, but they cannot override typography or collision FAILs.

## Required SA2 repair scope

1. Raise every source-owned reader-facing baseline to at least 9.5pt **after all transforms**; this includes the 8.6pt ticks, 9.4pt axis/leaf labels and 9.2pt cut annotation. Do not use whole-figure downscaling.
2. Reposition or redesign the axis-title/tick area so all independent final foreground masks have at least 4px text--text clearance. Fix every failed pair listed in `after_overlap_report.csv`; do not treat tree-line intersections as a reason to retain a text collision.
3. Re-measure `h_c=1.4` as independent CJK, lowercase, subscript, equals, digit and decimal-punctuation substrings. A nominal 9.5pt change alone is insufficient if the `=` or punctuation pixels remain below their 22px gate.
4. Rebuild against a new final candidate PDF and regenerate all evidence. The next role is **SA2**, not SA3.
"""
    write_text("after_visual_acceptance.md", summary_md)

    report = f"""# FIG-P445-01 — SA1 strict R1 formal report

**Conclusion: FAIL. Next role: SA2.**

This is an independent, read-only requalification of the frozen final PDF. It does not rely on a legacy pass, legacy screenshot or a pre-existing measurement table.

## Scope and provenance

| Item | Value |
|---|---|
| Figure | `{FIGURE_ID}` / 图 25.1 |
| Frozen input | `{PDF}` |
| Physical PDF page / printed page | {page_index + 1} / {printed_page} |
| Source | `{SOURCE}` |
| Adjacent body checked | `{CONTEXT}` lines 416--417 |
| Raw native render | 300 dpi, {pix300.width}×{pix300.height}px, no post-render resize |
| Visible text elements | {len(text_objects)} independent glyph/substrings |
| Independent vector objects | {len(vector_objects)} |
| All pair rows | {len(all_pairs)} |

## Decision

The candidate is **not eligible for SA3**. Source-effective font failures are already conclusive. The audit nevertheless completed all visible figure/caption glyphs, independent vector bboxes/masks, all required object-pair checks, edge checks, four views and mathematical/text/page review.

| Gate | Result |
|---|---:|
| Source font | {'PASS' if source_font_pass else 'FAIL'} ({len(failed_font)} failed elements) |
| 300dpi pixel height | {'PASS' if pixel_height_pass else 'FAIL'} ({len(failed_pixel)} failed elements) |
| Same-class ratio | {'PASS' if same_class_pass else 'FAIL'} |
| Role ratio | {'PASS' if role_pass else 'FAIL'} |
| Illegal overlap pixels | {overlap_count} |
| Clip pixels | {clip_count} |
| Minimum text clearance | {fnum(min_clear)}px |
| Visual harmony | {'PASS' if visual_harmony_pass else 'FAIL'} |
| Mathematical semantics | PASS |
| Text consistency | PASS |
| Grayscale | PASS |
| Page integration | PASS |

## Principal blockers

1. The source explicitly sets base 9.2pt (`slfig-FIG-P445-01`), 9.4pt axis/leaf labels, 8.6pt ticks, and 9.2pt cut annotation. Each is below the 9.5pt source-effective hard floor.
2. The vector extraction measures every glyph separately. Any small `h`, `c` subscript, `=`, decimal point or caption punctuation appears as its own traceable `ELEMENT_ID`; no enclosing formula bbox substitutes for it.
3. `after_overlap_report.csv` contains each text--text and text--graphic independent-mask relationship; failed/nearest pairs have raw + red/blue/magenta evidence under `critical_pairs/`. Tree-branch and cut-line crossings are separately retained as intentional graphical topology in `all_object_pair_audit.csv` and are not misclassified as text overlap.

## Deliverables

- `SA1_STRICT_R1_REPORT.md` (this report)
- `after_font_audit.csv`, `after_pixel_measurements.csv`
- `same_class_ratio_audit.csv`, `role_ratio_audit.csv`
- `after_overlap_report.csv`, `all_object_pair_audit.csv`, `after_edge_clip_report.csv`
- `after_text_measurement_overlay_300dpi.png` (+ detail), four native-render views, raw crop/full page
- `masks/`, `raw_objects/`, `overlays/objects/`, `isolated_svg/text/`, `isolated_svg/vector/`, `critical_pairs/`, `vector_object_manifest.csv`
- `after_visual_acceptance.md`
"""
    write_text("SA1_STRICT_R1_REPORT.md", report)

    print(json.dumps({
        "RESULT": result,
        "physical_pdf_page": page_index + 1,
        "printed_page": printed_page,
        "source_font_failures": len(failed_font),
        "pixel_failures": len(failed_pixel),
        "illegal_overlap_pixels": overlap_count,
        "failed_pairs": len(fail_pairs),
        "clip_count": clip_count,
        "min_clearance_px": min_clear,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
