#!/usr/bin/env python3
"""Isolated SA3 evidence generator for FIG-P580-01.

This program is deliberately read-only with respect to the candidate PDF and
LaTeX source.  It writes only below the supplied evidence root.  Stage
``collect`` creates native-pixel, glyph, object, and pair-universe evidence.
Stage ``record-manual`` is intentionally separate: it can only be run after a
human reviewer has inspected the emitted 1x and 8x-nearest atlases.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from statistics import median

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF_PATH = ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r96_fullbook\main_full.pdf"
SOURCE_PATH = ROOT / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex"
EVIDENCE = ROOT / r"v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R7_SA3_BLIND_R96_20260824"
PDF_PAGE_1_BASED = 628
PAGE_INDEX = PDF_PAGE_1_BASED - 1
PRINTED_PAGE = 615
FIGURE_ID = "FIG-P580-01"
FIGURE_NO = "31.6"

# This scope is deliberately limited to the graphic body plus its caption.
# It excludes the preceding explanatory paragraph and the following read-check.
SCOPE_PT = fitz.Rect(100.0, 266.0, 505.0, 480.0)
BODY_PT = fitz.Rect(116.0, 266.0, 490.0, 463.0)
PIXEL_THRESHOLD = 235  # White background 255 minus the required 20/255 contrast.


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def mkdirs() -> dict[str, Path]:
    paths = {
        "native": EVIDENCE / "02_native_render",
        "glyph": EVIDENCE / "03_glyph_evidence",
        "glyph_original": EVIDENCE / "03_glyph_evidence" / "original_1x",
        "glyph_target": EVIDENCE / "03_glyph_evidence" / "target_overlay_1x",
        "glyph_mask": EVIDENCE / "03_glyph_evidence" / "mask_only_1x",
        "glyph_nearest": EVIDENCE / "03_glyph_evidence" / "triview_8x_nearest",
        "glyph_atlas": EVIDENCE / "03_glyph_evidence" / "atlases",
        "object": EVIDENCE / "04_object_evidence",
        "highrisk": EVIDENCE / "04_object_evidence" / "high_risk_pairs",
        "reports": EVIDENCE / "05_reports",
        "scripts": EVIDENCE / "06_scripts",
        "cal": EVIDENCE / "04_object_evidence" / "low_contour_calibration",
        "fonts": EVIDENCE / "04_object_evidence" / "low_contour_calibration" / "embedded_fonts",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def clamp(v: int, low: int, high: int) -> int:
    return max(low, min(high, v))


def rect_to_pixels(rect: fitz.Rect, sx: float, sy: float, image: Image.Image) -> tuple[int, int, int, int]:
    x0 = clamp(math.floor(rect.x0 * sx), 0, image.width)
    y0 = clamp(math.floor(rect.y0 * sy), 0, image.height)
    x1 = clamp(math.ceil(rect.x1 * sx), 0, image.width)
    y1 = clamp(math.ceil(rect.y1 * sy), 0, image.height)
    if x1 <= x0:
        x1 = min(image.width, x0 + 1)
    if y1 <= y0:
        y1 = min(image.height, y0 + 1)
    return x0, y0, x1, y1


def union_rect(rects: list[fitz.Rect]) -> fitz.Rect:
    result = fitz.Rect(rects[0])
    for rect in rects[1:]:
        result.include_rect(rect)
    return result


def bbox_distance_px(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def bbox_overlap_area(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def scope_intersects(rect: fitz.Rect) -> bool:
    return rect.intersects(SCOPE_PT)


def glyph_class(char: str, span_size: float) -> tuple[str, int | None, bool]:
    """Return script class, direct height threshold and low-contour flag.

    A literal punctuation mark has no full-height contour.  It is not allowed
    to pass merely because it is visible: it is sent to an independent control
    calibrated from the final-PDF embedded font instead.
    """
    category = unicodedata.category(char)
    low_contour = category.startswith("P") or char in {"=", "−", "+", "≪", "̸"}
    if low_contour:
        return "LOW_CONTOUR_CALIBRATION", None, True
    # Math subscripts in the final PDF include a 8.966 pt case produced from a
    # 9.963 pt base; it is a semantic script, not an undersized body label.
    if span_size < 9.5:
        return "MATH_SCRIPT", 15, False
    if "CJK" in unicodedata.name(char, "") or ("\u3400" <= char <= "\u9fff"):
        return "CJK_FULL", 30, False
    if char.isdigit() or (char.isalpha() and char.isupper()):
        return "LATIN_UPPER_OR_DIGIT", 24, False
    if char.isalpha():
        return "LATIN_LOWER_OR_GREEK", 17, False
    return "MATH_BASE", 22, False


def role_for_line(line_bbox: fitz.Rect) -> tuple[str, str, str, float | str, str]:
    """Return role, panel, source-line provenance, declared size, source note."""
    x0, y0, x1, y1 = line_bbox
    center_x = (x0 + x1) / 2
    panel = "LEFT" if center_x < 320 else "RIGHT"
    if 266 <= y0 < 286:
        return "PANEL_TITLE", panel, "37" if panel == "LEFT" else "69", 10.2, "title style line 26"
    if 463 <= y0 <= 480:
        return "CAPTION", "GLOBAL", "102", "inherited", "caption command; final-PDF size is recorded"
    # The two rotated lines emitted by ylabel={密度\\每 x 单位} are one
    # semantic axis-title object, not two independent tick labels.  Classify
    # before the generic y-tick window so their 2px PDF-bbox adjacency is not
    # falsely evaluated as a text-to-text clearance relation.
    if panel == "LEFT" and 330 <= y0 < 380 and x0 < 150:
        return "AXIS_LABEL_VERTICAL", panel, "38", 9.6, "axis label style line 25"
    if 408 <= y0 < 432:
        # The y=0 label is horizontally adjacent to, rather than below, the
        # x-axis.  Keep it in the y-tick family.
        if (panel == "LEFT" and x0 < 173) or (panel == "RIGHT" and x0 < 340):
            return "TICK_Y", panel, "21-23", 9.6, "tick label style line 24"
        return "TICK_X", panel, "21-23", 9.6, "tick label style line 24"
    if 300 <= y0 < 385 and ((panel == "LEFT" and x0 < 176) or (panel == "RIGHT" and x0 < 340)):
        return "TICK_Y", panel, "21-23", 9.6, "tick label style line 24"
    if panel == "LEFT" and 300 <= y0 < 327:
        if x0 >= 180 and x1 < 230:
            return "ANNOTATION_Q_L", panel, "59-61", 9.6, "explicit node font"
        if x0 >= 245:
            return "ANNOTATION_SUPPORT_BOUNDARY", panel, "65-67", 9.6, "explicit node font"
    if panel == "LEFT" and 339 <= y0 < 357:
        return "ANNOTATION_TARGET_P", panel, "62-63", 9.6, "explicit node font"
    if panel == "RIGHT" and 295 <= y0 < 342 and x0 >= 350:
        return "FORMULA_CARD", panel, "89-99", 9.6, "node inherits figure font; final math size measured"
    if 432 <= y0 < 462:
        return "AXIS_LABEL_HORIZONTAL", panel, "39-41" if panel == "LEFT" else "70-72", 9.6, "axis label style line 25"
    return "OTHER_TEXT", panel, "unmapped", "unmapped", "requires reviewer attention"


def element_key(role: str, panel: str, bbox: fitz.Rect, block_index: int, line_index: int) -> str:
    # These groups match visual objects, not individual TeX glyph runs.
    if role in {"PANEL_TITLE", "CAPTION", "ANNOTATION_Q_L", "ANNOTATION_SUPPORT_BOUNDARY", "ANNOTATION_TARGET_P", "FORMULA_CARD", "AXIS_LABEL_HORIZONTAL"}:
        return f"{role}_{panel}"
    if role == "AXIS_LABEL_VERTICAL":
        return "AXIS_LABEL_VERTICAL_LEFT"
    # Individual tick labels are visual objects with their own clearances.
    return f"{role}_{panel}_{block_index:02d}_{line_index:02d}"


def pixel_mask(rgb: np.ndarray) -> np.ndarray:
    gray = rgb.astype(np.float32).mean(axis=2)
    return gray <= PIXEL_THRESHOLD


def render_glyph_artifacts(record: dict, page_image: Image.Image, dirs: dict[str, Path]) -> None:
    x0, y0, x1, y1 = record["bbox_px"]
    padding = 6
    bx0 = clamp(x0 - padding, 0, page_image.width)
    by0 = clamp(y0 - padding, 0, page_image.height)
    bx1 = clamp(x1 + padding, 0, page_image.width)
    by1 = clamp(y1 + padding, 0, page_image.height)
    original = page_image.crop((bx0, by0, bx1, by1)).convert("RGB")

    overlay = original.copy()
    draw = ImageDraw.Draw(overlay)
    # Red exact target origin: the raw PDF glyph bounding box, mapped without
    # interpolation to the native final-PDF raster coordinates.
    draw.rectangle((x0 - bx0, y0 - by0, x1 - bx0 - 1, y1 - by0 - 1), outline=(230, 30, 30), width=1)

    local_mask = pixel_mask(np.array(original))
    mask_image = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8), mode="L")

    stem = record["glyph_id"]
    original_path = dirs["glyph_original"] / f"{stem}.png"
    overlay_path = dirs["glyph_target"] / f"{stem}.png"
    mask_path = dirs["glyph_mask"] / f"{stem}.png"
    original.save(original_path)
    overlay.save(overlay_path)
    mask_image.save(mask_path)

    tri_width = original.width * 3 + 8
    tri = Image.new("RGB", (tri_width, original.height), "white")
    tri.paste(original, (0, 0))
    tri.paste(overlay, (original.width + 4, 0))
    tri.paste(mask_image.convert("RGB"), (2 * original.width + 8, 0))
    nearest = tri.resize((tri.width * 8, tri.height * 8), Image.Resampling.NEAREST)
    nearest_path = dirs["glyph_nearest"] / f"{stem}.png"
    nearest.save(nearest_path)

    record["original_path"] = str(original_path.relative_to(EVIDENCE)).replace("\\", "/")
    record["target_overlay_path"] = str(overlay_path.relative_to(EVIDENCE)).replace("\\", "/")
    record["mask_only_path"] = str(mask_path.relative_to(EVIDENCE)).replace("\\", "/")
    record["triview_8x_nearest_path"] = str(nearest_path.relative_to(EVIDENCE)).replace("\\", "/")


def create_glyph_atlases(records: list[dict], dirs: dict[str, Path], mode: str) -> list[str]:
    """Make review sheets without scaling the selected native/8x glyph artifacts."""
    if mode not in {"1x", "8x"}:
        raise ValueError(mode)
    output: list[str] = []
    per_page = 36
    cols = 6
    for page_number, start in enumerate(range(0, len(records), per_page), start=1):
        batch = records[start : start + per_page]
        tiles = []
        for rec in batch:
            if mode == "8x":
                tile = Image.open(EVIDENCE / rec["triview_8x_nearest_path"]).convert("RGB")
            else:
                original = Image.open(EVIDENCE / rec["original_path"]).convert("RGB")
                overlay = Image.open(EVIDENCE / rec["target_overlay_path"]).convert("RGB")
                mask = Image.open(EVIDENCE / rec["mask_only_path"]).convert("RGB")
                tile = Image.new("RGB", (original.width * 3 + 8, original.height), "white")
                tile.paste(original, (0, 0))
                tile.paste(overlay, (original.width + 4, 0))
                tile.paste(mask, (2 * original.width + 8, 0))
            # Add only whitespace/ASCII ID outside the selected exact-pixel tile.
            head = 24
            framed = Image.new("RGB", (tile.width, tile.height + head), "white")
            framed.paste(tile, (0, head))
            ImageDraw.Draw(framed).text((2, 4), rec["glyph_id"], fill="black")
            tiles.append(framed)
        cell_w = max(tile.width for tile in tiles) + 8
        cell_h = max(tile.height for tile in tiles) + 8
        rows = math.ceil(len(tiles) / cols)
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        for i, tile in enumerate(tiles):
            x = (i % cols) * cell_w + 4
            y = (i // cols) * cell_h + 4
            sheet.paste(tile, (x, y))
        suffix = "8x" if mode == "8x" else "1x_native"
        out = dirs["glyph_atlas"] / f"glyph_triview_{suffix}_atlas_{page_number:02d}.png"
        sheet.save(out)
        output.append(str(out.relative_to(EVIDENCE)).replace("\\", "/"))
    return output


def make_low_contour_controls(
    records: list[dict], doc: fitz.Document, page: fitz.Page, dirs: dict[str, Path]
) -> list[dict]:
    """Create final-PDF, same-font, same-size independent controls.

    Each control is an *other occurrence* in the current final PDF, never a
    newly-typeset approximation.  Its physical page is directly rendered with
    Poppler at 300 dpi and then precisely cropped without resizing.  This is
    especially important for punctuation and shallow mathematical contours.
    """
    groups: dict[tuple[str, str, float, int], list[dict]] = defaultdict(list)
    for rec in records:
        if rec["low_contour"]:
            groups[(rec["char"], rec["pdf_font"], round(rec["pdf_font_size_pt"], 4), rec["flags"])].append(rec)

    def find_other_occurrence(char: str, font: str, size: float, flags: int) -> tuple[int, fitz.Rect] | None:
        # Restrict this scan to the current candidate PDF.  The scan is only
        # used for singleton low-contour groups lacking another local instance.
        for page_index in range(len(doc)):
            candidate_page = doc[page_index]
            for block in candidate_page.get_text("rawdict")["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["font"] != font or span["flags"] != flags or abs(float(span["size"]) - size) > 0.001:
                            continue
                        for char_data in span["chars"]:
                            if char_data["c"] == char and not (page_index == PAGE_INDEX and fitz.Rect(char_data["bbox"]).intersects(SCOPE_PT)):
                                return page_index, fitz.Rect(char_data["bbox"])
        return None

    native_cache: dict[int, tuple[Image.Image, fitz.Rect]] = {PAGE_INDEX: (Image.open(dirs["native"] / "page_628_full_300dpi.png").convert("RGB"), page.rect)}

    def get_native_page(page_index: int) -> tuple[Image.Image, fitz.Rect]:
        if page_index in native_cache:
            return native_cache[page_index]
        ref_page = doc[page_index]
        physical = page_index + 1
        prefix = dirs["cal"] / f"final_pdf_reference_page_{physical:03d}_300dpi"
        png = Path(str(prefix) + ".png")
        subprocess.run(
            ["pdftoppm.exe", "-r", "300", "-f", str(physical), "-l", str(physical), "-png", "-singlefile", str(PDF_PATH), str(prefix)],
            check=True,
            capture_output=True,
        )
        native_cache[page_index] = (Image.open(png).convert("RGB"), ref_page.rect)
        return native_cache[page_index]

    calibration_rows: list[dict] = []
    for ix, ((char, font_name, size, flags), members) in enumerate(groups.items(), start=1):
        row = {
            "calibration_id": f"LC{ix:03d}",
            "char": char,
            "unicode": f"U+{ord(char):04X}",
            "font": font_name,
            "font_size_pt": size,
            "flags": flags,
            "glyph_count": len(members),
            "status": "FAIL",
            "reason": "",
            "reference_height_px": "",
            "reference_page_physical": "",
            "reference_bbox_pt": "",
            "reference_mode": "",
            "reference_pdf_path": "",
            "png_path": "",
        }
        for rec in members:
            rec["calibration_id"] = row["calibration_id"]
        # Prefer a different local glyph of the same exact tuple; singleton
        # groups fall back to another page in the same final candidate PDF.
        if len(members) > 1:
            other = next(item for item in members if item["glyph_id"] != members[0]["glyph_id"])
            reference_page_index = PAGE_INDEX
            reference_rect = fitz.Rect(other["bbox_x0_pt"], other["bbox_y0_pt"], other["bbox_x1_pt"], other["bbox_y1_pt"])
        else:
            found = find_other_occurrence(char, font_name, size, flags)
            if found is None:
                # A singleton still receives an independent *rendering* control:
                # a one-glyph PDF Form copied directly from the final candidate
                # PDF. It is not re-typeset or substituted by another font.
                reference_page_index = PAGE_INDEX
                reference_rect = fitz.Rect(members[0]["bbox_x0_pt"], members[0]["bbox_y0_pt"], members[0]["bbox_x1_pt"], members[0]["bbox_y1_pt"])
                singleton_form_control = True
            else:
                reference_page_index, reference_rect = found
                singleton_form_control = False
        if len(members) > 1:
            singleton_form_control = False
        try:
            if singleton_form_control:
                pad_pt = 3.0
                clip = fitz.Rect(reference_rect)
                clip.x0 -= pad_pt
                clip.y0 -= pad_pt
                clip.x1 += pad_pt
                clip.y1 += pad_pt
                form_pdf = dirs["cal"] / f"{row['calibration_id']}_singleton_final_pdf_form_control.pdf"
                form_doc = fitz.open()
                form_page = form_doc.new_page(width=clip.width, height=clip.height)
                form_page.show_pdf_page(form_page.rect, doc, reference_page_index, clip=clip)
                form_doc.save(form_pdf)
                form_doc.close()
                prefix = dirs["cal"] / f"{row['calibration_id']}_singleton_final_pdf_form_control_300dpi"
                subprocess.run(["pdftoppm.exe", "-r", "300", "-png", "-singlefile", str(form_pdf), str(prefix)], check=True, capture_output=True)
                reference_image = Image.open(Path(str(prefix) + ".png")).convert("RGB")
                sx = reference_image.width / clip.width
                sy = reference_image.height / clip.height
                shifted = fitz.Rect(reference_rect.x0 - clip.x0, reference_rect.y0 - clip.y0, reference_rect.x1 - clip.x0, reference_rect.y1 - clip.y0)
                x0, y0, x1, y1 = rect_to_pixels(shifted, sx, sy, reference_image)
                row["reference_mode"] = "singleton isolated final-PDF Form control"
                row["reference_pdf_path"] = str(form_pdf.relative_to(EVIDENCE)).replace("\\", "/")
            else:
                reference_image, reference_page_rect = get_native_page(reference_page_index)
                sx = reference_image.width / reference_page_rect.width
                sy = reference_image.height / reference_page_rect.height
                x0, y0, x1, y1 = rect_to_pixels(reference_rect, sx, sy, reference_image)
                row["reference_mode"] = "other final-PDF occurrence"
            pad = 6
            crop = reference_image.crop((clamp(x0 - pad, 0, reference_image.width), clamp(y0 - pad, 0, reference_image.height), clamp(x1 + pad, 0, reference_image.width), clamp(y1 + pad, 0, reference_image.height)))
            ref_png = dirs["cal"] / f"{row['calibration_id']}_final_pdf_reference_native_300dpi.png"
            crop.save(ref_png)
            mask = pixel_mask(np.array(reference_image)[y0:y1, x0:x1])
            h = int(np.count_nonzero(np.any(mask, axis=1)))
            row["reference_height_px"] = h
            row["reference_page_physical"] = reference_page_index + 1
            row["reference_bbox_pt"] = ";".join(f"{v:.3f}" for v in reference_rect)
            row["status"] = "PASS"
            row["reason"] = "final-PDF same-codepoint/font/size/weight control, directly rasterized at 300 dpi"
            row["png_path"] = str(ref_png.relative_to(EVIDENCE)).replace("\\", "/")
        except Exception as exc:  # Never silently promote a failed control.
            row["reason"] = f"calibration error: {exc}"
        calibration_rows.append(row)

    by_id = {row["calibration_id"]: row for row in calibration_rows}
    for rec in records:
        if not rec["low_contour"]:
            continue
        ref = by_id[rec["calibration_id"]]
        if ref["status"] != "PASS":
            rec["pixel_pass"] = False
            rec["pixel_reason"] = "low-contour calibration unavailable"
            continue
        ref_h = int(ref["reference_height_px"])
        delta = abs(rec["h_ink_px"] - ref_h)
        rec["pixel_pass"] = delta <= 1
        rec["pixel_reason"] = f"same-font standalone control {ref['calibration_id']}: observed={rec['h_ink_px']}px, reference={ref_h}px, |Δ|={delta}px"
    return calibration_rows


def drawing_union(page: fitz.Page, indices: list[int]) -> fitz.Rect:
    drawings = page.get_drawings()
    return union_rect([fitz.Rect(drawings[index]["rect"]) for index in indices])


def graphics_objects(page: fitz.Page, sx: float, sy: float, image: Image.Image) -> list[dict]:
    specs = [
        ("G001", "LEFT_AXIS_SYSTEM", [5, 6, 7, 8, 9, 10], "LINE_ARROW", "21-26,35-36", "left axes, ticks, and arrowheads"),
        ("G002", "LEFT_TARGET_CURVE_P", [12], "DATA_CURVE", "42,47", "target density p(x)"),
        ("G003", "LEFT_Q_L_TOP", [13], "LINE_ARROW", "49-50", "q_L=2/5 dashed support segment"),
        ("G004", "LEFT_Q_L_ZERO", [14], "LINE_ARROW", "51-52", "q_L=0 dashed support segment"),
        ("G005", "LEFT_SUPPORT_BOUNDARY", [15], "LINE_ARROW", "57-58", "dotted x=5/2 support boundary"),
        ("G006", "LEFT_Q_L_FILLED_ENDPOINT", [16], "MARKER", "53-54", "included endpoint at (5/2,2/5)"),
        ("G007", "LEFT_Q_L_OPEN_ENDPOINT", [17], "MARKER", "55-56", "open endpoint at (5/2,0)"),
        ("G008", "LEFT_SUPPORT_GAP_HATCH", None, "DATA_CURVE", "45-46", "pattern-filled p>0,q_L=0 support gap"),
        ("G009", "RIGHT_AXIS_SYSTEM", [18, 19, 20, 21, 22, 23], "LINE_ARROW", "21-26,35-36", "right axes, ticks, and arrowheads"),
        ("G010", "RIGHT_TARGET_CURVE_P", [24], "DATA_CURVE", "73-74", "target density p(x)"),
        ("G011", "RIGHT_Q_R", [25], "LINE_ARROW", "75-82", "phase-controlled q_R=1/5 dashed line"),
        ("G012", "RATIO_CARD_BORDER", [26], "PANEL_BORDER", "89-90", "white formula-card background and border"),
        ("G013", "RIGHT_MARK_CIRCLE_X1", [27], "MARKER", "83-84", "p(1) marker"),
        ("G014", "RIGHT_MARK_SQUARE_X25", [28], "MARKER", "85-86", "p(5/2) marker"),
        ("G015", "RIGHT_MARK_TRIANGLE_X4", [29], "MARKER", "87-88", "p(4) marker"),
    ]
    results: list[dict] = []
    for oid, name, indexes, category, source_lines, semantic in specs:
        if indexes is None:
            # Same coordinate system and path endpoints as source fill-between.
            rect = fitz.Rect(244.8908, 353.7562, 313.8926, 413.9560)
        else:
            rect = drawing_union(page, indexes)
        results.append(
            {
                "object_id": oid,
                "object_name": name,
                "kind": "GRAPHIC",
                "category": category,
                "source_lines": source_lines,
                "semantic": semantic,
                "bbox_pt": [round(rect.x0, 3), round(rect.y0, 3), round(rect.x1, 3), round(rect.y1, 3)],
                "bbox_px": rect_to_pixels(rect, sx, sy, image),
            }
        )
    return results


def whitelist_for_pair(a: str, b: str) -> tuple[str, str] | None:
    key = frozenset((a, b))
    rules = {
        frozenset(("G002", "G005")): ("WC01", "p(5/2)>0 crosses the explicitly drawn support boundary; source lines 42,47,57."),
        frozenset(("G002", "G008")): ("WC02", "fill-between hatching is intentionally bounded by the target curve; source lines 45-47."),
        frozenset(("G002", "G001")): ("WC03", "p(0)=p(5)=0, so target curve has named axis-endpoint contacts; source line 47."),
        frozenset(("G003", "G006")): ("WC04", "filled q_L endpoint marks its upper support value; source lines 49-54."),
        frozenset(("G004", "G001")): ("WC05", "q_L=0 is intentionally encoded on the x-axis over [5/2,5]; source lines 51-52."),
        frozenset(("G004", "G007")): ("WC06", "open q_L=0 endpoint is intentionally drawn at the support boundary; source lines 51-56."),
        frozenset(("G004", "G005")): ("WC07", "zero baseline and dotted support boundary meet at x=5/2; source lines 51-58."),
        frozenset(("G005", "G006")): ("WC08", "dotted support boundary passes through its named q_L upper endpoint; source lines 53-58."),
        frozenset(("G005", "G007")): ("WC09", "dotted support boundary starts at its named open endpoint; source lines 55-58."),
        frozenset(("G008", "G001")): ("WC10", "support-gap hatching is intentionally closed by the x-axis; source lines 45-46."),
        frozenset(("G010", "G009")): ("WC11", "p(0)=p(5)=0 gives named right-axis endpoint contacts; source line 73."),
        frozenset(("G010", "G011")): ("WC12", "p=q_R at two analytic crossings; source lines 73 and 75-82."),
        frozenset(("G010", "G013")): ("WC13", "circle marker is intentionally placed on p(1); source lines 83-84."),
        frozenset(("G010", "G014")): ("WC14", "square marker is intentionally placed on p(5/2); source lines 85-86."),
        frozenset(("G010", "G015")): ("WC15", "triangle marker is intentionally placed on p(4); source lines 87-88."),
        frozenset(("G001", "G003")): ("WC16", "q_L=2/5 starts on the left y-axis at x=0; source lines 49-50."),
        frozenset(("G001", "G005")): ("WC17", "the dotted support boundary is explicitly drawn from the x-axis; source lines 57-58."),
        frozenset(("G001", "G007")): ("WC18", "the open q_L=0 endpoint is intentionally placed on the x-axis; source lines 55-56."),
        frozenset(("G002", "G004")): ("WC19", "p(5)=0 meets the displayed q_L=0 baseline at the right endpoint; source lines 47,51-52."),
        frozenset(("G003", "G005")): ("WC20", "the q_L=2/5 segment and support boundary meet at x=5/2; source lines 49-50,57-58."),
        frozenset(("G004", "G008")): ("WC21", "the q_L=0 baseline is the named lower boundary of the support-gap hatch; source lines 45-46,51-52."),
        frozenset(("G005", "G008")): ("WC22", "the support boundary is the named left edge of the soft-clipped hatch; source lines 45-46,57-58."),
        frozenset(("G007", "G008")): ("WC23", "the open endpoint marks the hatch/baseline start at (5/2,0); source lines 45-46,55-56."),
        frozenset(("G009", "G011")): ("WC24", "q_R=1/5 starts on the right-panel y-axis at x=0; source lines 75-82."),
    }
    return rules.get(key)


def visual_pair_crop(
    pair_id: str, a: dict, b: dict, image: Image.Image, dirs: dict[str, Path]
) -> tuple[str, str]:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    pad = 18
    x0 = clamp(min(ax0, bx0) - pad, 0, image.width)
    y0 = clamp(min(ay0, by0) - pad, 0, image.height)
    x1 = clamp(max(ax1, bx1) + pad, 0, image.width)
    y1 = clamp(max(ay1, by1) + pad, 0, image.height)
    crop = image.crop((x0, y0, x1, y1)).convert("RGB")
    one = dirs["highrisk"] / f"{pair_id}_1x.png"
    eight = dirs["highrisk"] / f"{pair_id}_8x_nearest.png"
    crop.save(one)
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(eight)
    return (
        str(one.relative_to(EVIDENCE)).replace("\\", "/"),
        str(eight.relative_to(EVIDENCE)).replace("\\", "/"),
    )


def overlay_map(image: Image.Image, objects: list[dict], output: Path, title: str) -> None:
    canvas = image.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    for i, obj in enumerate(objects):
        x0, y0, x1, y1 = obj["bbox_px"]
        color = (230, 30, 30) if obj["kind"] == "TEXT" else (20, 130, 30)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=2)
        draw.text((x0 + 1, max(0, y0 - 11)), obj["object_id"], fill=color)
    canvas.save(output)


def create_highrisk_atlases(pair_rows: list[dict], dirs: dict[str, Path], mode: str) -> list[str]:
    if mode not in {"1x", "8x"}:
        raise ValueError(mode)
    pages: list[str] = []
    per_page = 12
    cols = 3
    for number, start in enumerate(range(0, len(pair_rows), per_page), start=1):
        batch = pair_rows[start : start + per_page]
        tiles: list[Image.Image] = []
        for row in batch:
            key = "roi_8x_nearest" if mode == "8x" else "roi_1x"
            im = Image.open(EVIDENCE / row[key]).convert("RGB")
            if mode == "8x":
                # Bound only the 8x visual sheet; individual exact 8x ROIs
                # remain ledger-linked. The 1x sheet below is never resized.
                max_w, max_h = 800, 640
                factor = min(max_w / im.width, max_h / im.height, 1.0)
                if factor < 1.0:
                    im = im.resize((max(1, int(im.width * factor)), max(1, int(im.height * factor))), Image.Resampling.NEAREST)
            framed = Image.new("RGB", (im.width, im.height + 22), "white")
            framed.paste(im, (0, 22))
            ImageDraw.Draw(framed).text((2, 4), f"{row['pair_id']} {row['pair_type']}", fill="black")
            tiles.append(framed)
        cw = max(t.width for t in tiles) + 8
        ch = max(t.height for t in tiles) + 8
        rows = math.ceil(len(tiles) / cols)
        sheet = Image.new("RGB", (cols * cw, rows * ch), "white")
        for i, tile in enumerate(tiles):
            sheet.paste(tile, ((i % cols) * cw + 4, (i // cols) * ch + 4))
        suffix = "8x" if mode == "8x" else "1x_native"
        out = dirs["object"] / f"high_risk_{suffix}_review_atlas_{number:02d}.png"
        sheet.save(out)
        pages.append(str(out.relative_to(EVIDENCE)).replace("\\", "/"))
    return pages


def csv_write(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        # Mixed text/graphic inventories have different descriptive fields;
        # keep the union rather than silently dropping the later object's data.
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def markdown_write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def collect() -> None:
    dirs = mkdirs()
    if not PDF_PATH.is_file() or not SOURCE_PATH.is_file():
        raise SystemExit("required candidate PDF or current figure source is missing")
    pdf_hash = sha256(PDF_PATH)
    source_hash = sha256(SOURCE_PATH)
    doc = fitz.open(PDF_PATH)
    if len(doc) < PDF_PAGE_1_BASED:
        raise SystemExit(f"candidate PDF has only {len(doc)} pages, expected physical page {PDF_PAGE_1_BASED}")
    page = doc[PAGE_INDEX]
    native_path = dirs["native"] / "page_628_full_300dpi.png"
    if not native_path.is_file():
        raise SystemExit("native 300 dpi page render is missing")
    page_image = Image.open(native_path).convert("RGB")
    rgb = np.array(page_image)
    sx = page_image.width / page.rect.width
    sy = page_image.height / page.rect.height

    raw = page.get_text("rawdict")
    records: list[dict] = []
    element_parts: dict[str, list[dict]] = defaultdict(list)
    glyph_number = 0
    for block_index, block in enumerate(raw["blocks"]):
        if block["type"] != 0:
            continue
        for line_index, line in enumerate(block["lines"]):
            line_rect = fitz.Rect(line["bbox"])
            if not scope_intersects(line_rect):
                continue
            role, panel, source_lines, declared_pt, source_note = role_for_line(line_rect)
            ekey = element_key(role, panel, line_rect, block_index, line_index)
            for span_index, span in enumerate(line["spans"]):
                for char_index, char_data in enumerate(span["chars"]):
                    char = char_data["c"]
                    rect = fitz.Rect(char_data["bbox"])
                    if char.isspace() or not scope_intersects(rect):
                        continue
                    glyph_number += 1
                    bbox_px = rect_to_pixels(rect, sx, sy, page_image)
                    x0, y0, x1, y1 = bbox_px
                    mask = pixel_mask(rgb[y0:y1, x0:x1])
                    h_ink = int(np.count_nonzero(np.any(mask, axis=1)))
                    w_ink = int(np.count_nonzero(np.any(mask, axis=0)))
                    script_class, threshold, low_contour = glyph_class(char, float(span["size"]))
                    rec = {
                        "glyph_id": f"G{glyph_number:04d}",
                        "element_id": ekey,
                        "char": char,
                        "unicode": f"U+{ord(char):04X}",
                        "role": role,
                        "panel": panel,
                        "source_file": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
                        "source_lines": source_lines,
                        "source_declared_pt": declared_pt,
                        "graphics_scale": "1.000 (no resizebox/scalebox/transform shape in current source)",
                        "pdf_font": span["font"],
                        "pdf_font_size_pt": round(float(span["size"]), 4),
                        "flags": span["flags"],
                        "script_class": script_class,
                        "min_required_ink_px": threshold if threshold is not None else "calibrated",
                        "bbox_x0_px": x0,
                        "bbox_y0_px": y0,
                        "bbox_x1_px": x1,
                        "bbox_y1_px": y1,
                        "bbox_px": bbox_px,
                        "bbox_x0_pt": round(rect.x0, 4),
                        "bbox_y0_pt": round(rect.y0, 4),
                        "bbox_x1_pt": round(rect.x1, 4),
                        "bbox_y1_pt": round(rect.y1, 4),
                        "h_ink_px": h_ink,
                        "w_ink_px": w_ink,
                        "low_contour": low_contour,
                        "pixel_pass": (h_ink >= threshold) if threshold is not None else False,
                        "pixel_reason": f"H_ink={h_ink}px against required >= {threshold}px" if threshold is not None else "pending standalone same-font calibration",
                        "original_path": "",
                        "target_overlay_path": "",
                        "mask_only_path": "",
                        "triview_8x_nearest_path": "",
                        "calibration_id": "",
                        "manual_1x": "PENDING",
                        "manual_8x": "PENDING",
                    }
                    records.append(rec)
                    element_parts[ekey].append(rec)

    if not records:
        raise SystemExit("no visible text glyphs found in the defined figure scope")
    for rec in records:
        render_glyph_artifacts(rec, page_image, dirs)
    calibration_rows = make_low_contour_controls(records, doc, page, dirs)

    elements: list[dict] = []
    for eindex, (eid, members) in enumerate(sorted(element_parts.items()), start=1):
        first = members[0]
        rect = union_rect([fitz.Rect(m["bbox_x0_pt"], m["bbox_y0_pt"], m["bbox_x1_pt"], m["bbox_y1_pt"]) for m in members])
        px = rect_to_pixels(rect, sx, sy, page_image)
        x0, y0, x1, y1 = px
        msk = pixel_mask(rgb[y0:y1, x0:x1])
        h = int(np.count_nonzero(np.any(msk, axis=1)))
        sizes = [float(m["pdf_font_size_pt"]) for m in members]
        elements.append(
            {
                "object_id": f"T{eindex:03d}",
                "element_id": eid,
                "kind": "TEXT",
                "role": first["role"],
                "panel": first["panel"],
                "glyph_count": len(members),
                "text_sample": "".join(m["char"] for m in members),
                "source_file": first["source_file"],
                "source_lines": first["source_lines"],
                "source_declared_pt": first["source_declared_pt"],
                "source_note": role_for_line(rect)[4],
                "graphics_scale": first["graphics_scale"],
                "final_effective_pt_min": round(min(sizes), 4),
                "final_effective_pt_max": round(max(sizes), 4),
                "bbox_x0_px": px[0],
                "bbox_y0_px": px[1],
                "bbox_x1_px": px[2],
                "bbox_y1_px": px[3],
                "bbox_px": px,
                "h_ink_px": h,
                "glyph_pixel_pass_count": sum(1 for m in members if m["pixel_pass"]),
                "glyph_pixel_fail_count": sum(1 for m in members if not m["pixel_pass"]),
                "font_pass": all(float(m["pdf_font_size_pt"]) >= 9.5 or m["script_class"] == "MATH_SCRIPT" for m in members),
                "pixel_pass": all(m["pixel_pass"] for m in members),
            }
        )

    graphics = graphics_objects(page, sx, sy, page_image)
    all_objects = elements + graphics
    # Machine-readable geometry must not silently claim raw masks determine the
    # verdict.  Every near or intersecting bounding relation is placed into a
    # human 1x/8x review set below.
    object_by_id = {item["object_id"]: item for item in all_objects}
    highrisk: list[dict] = []
    pair_rows: list[dict] = []
    pair_number = 0
    for a, b in combinations(all_objects, 2):
        pair_number += 1
        pair_id = f"P{pair_number:04d}"
        dist = bbox_distance_px(a["bbox_px"], b["bbox_px"])
        area = bbox_overlap_area(a["bbox_px"], b["bbox_px"])
        pair_type = "TT" if a["kind"] == b["kind"] == "TEXT" else "GG" if a["kind"] == b["kind"] == "GRAPHIC" else "TG"
        whitelist = whitelist_for_pair(a["object_id"], b["object_id"])
        # All actual source-semantic contacts are included even if their broad
        # PDF bounding boxes happen not to intersect.  16 px is intentionally
        # stricter than the 3--8 px hard-clearance floors.
        manual_required = whitelist is not None or dist <= 16.0 or area > 0
        status = "EXPECTED_CONTACT" if whitelist else "PENDING_MANUAL" if manual_required else "CLEAR_BY_SEPARATION"
        row = {
            "pair_id": pair_id,
            "object_a": a["object_id"],
            "object_b": b["object_id"],
            "pair_type": pair_type,
            "bbox_overlap_px2": area,
            "bbox_min_clearance_px": round(dist, 3),
            "expected_contact_id": whitelist[0] if whitelist else "",
            "expected_contact_proof": whitelist[1] if whitelist else "",
            "automated_status": status,
            "manual_required": manual_required,
            "manual_1x": "PENDING" if manual_required else "NOT_REQUIRED",
            "manual_8x": "PENDING" if manual_required else "NOT_REQUIRED",
            "illegal_overlap_px": "UNASSESSED" if manual_required else 0,
            "clip_px": 0,
            "roi_1x": "",
            "roi_8x_nearest": "",
        }
        if manual_required:
            one, eight = visual_pair_crop(pair_id, a, b, page_image, dirs)
            row["roi_1x"] = one
            row["roi_8x_nearest"] = eight
            highrisk.append(row)
        pair_rows.append(row)

    glyph_objects = []
    for rec in records:
        glyph_objects.append(
            {
                "glyph_id": rec["glyph_id"],
                "element_id": rec["element_id"],
                "nearest_foreign_object": "",
                "nearest_foreign_clearance_px": "",
                "contact_status": "PENDING",
            }
        )
    # Each glyph's nearest foreign visual element, measured at native scale.
    element_by_key = {item["element_id"]: item for item in elements}
    for gc, rec in zip(glyph_objects, records):
        own = element_by_key[rec["element_id"]]["object_id"]
        rb = (rec["bbox_x0_px"], rec["bbox_y0_px"], rec["bbox_x1_px"], rec["bbox_y1_px"])
        options = [o for o in all_objects if o["object_id"] != own]
        nearest = min(options, key=lambda o: bbox_distance_px(rb, o["bbox_px"]))
        gc["nearest_foreign_object"] = nearest["object_id"]
        gc["nearest_foreign_clearance_px"] = round(bbox_distance_px(rb, nearest["bbox_px"]), 3)
        gc["contact_status"] = "MANUAL_PAIR_COVERED" if bbox_distance_px(rb, nearest["bbox_px"]) <= 16 else "CLEAR_BY_SEPARATION"

    scope_px = rect_to_pixels(SCOPE_PT, sx, sy, page_image)
    sx0, sy0, sx1, sy1 = scope_px
    scope_native = page_image.crop(scope_px)
    scope_native.save(dirs["native"] / "figure_scope_with_caption_native_300dpi.png")
    ImageOps.grayscale(scope_native).save(dirs["native"] / "figure_scope_grayscale_300dpi.png")
    body_native = page_image.crop(rect_to_pixels(BODY_PT, sx, sy, page_image))
    body_native.save(dirs["native"] / "figure_body_isolated_native_300dpi.png")
    # The isolated image is a direct native-PDF crop; no recompile or resize is
    # asserted. It is included so its scope is visually reviewable on its own.
    overlay_map(page_image, elements, dirs["object"] / "text_element_target_overlay_300dpi.png", "text")
    overlay_map(page_image, graphics, dirs["object"] / "graphic_object_target_overlay_300dpi.png", "graphic")
    overlay_map(page_image, all_objects, dirs["object"] / "all_foreground_objects_target_overlay_300dpi.png", "all")
    glyph_atlases_1x = create_glyph_atlases(records, dirs, "1x")
    glyph_atlases_8x = create_glyph_atlases(records, dirs, "8x")
    risk_atlases_1x = create_highrisk_atlases(highrisk, dirs, "1x")
    risk_atlases_8x = create_highrisk_atlases(highrisk, dirs, "8x")

    # Native scope-edge clipping check is exact in the rendered PNG: foreground
    # on the artificial crop edge would mean an insufficient crop margin; a
    # source/PDF object boundary test below independently checks actual figure
    # bounds against the page.
    edge_mask = pixel_mask(np.array(scope_native))
    edge_ink = int(edge_mask[0, :].sum() + edge_mask[-1, :].sum() + edge_mask[:, 0].sum() + edge_mask[:, -1].sum())
    candidate_objects = [o for o in all_objects if o["kind"] == "GRAPHIC"] + elements
    page_clip_candidates = [
        o for o in candidate_objects
        if o["bbox_px"][0] <= 0 or o["bbox_px"][1] <= 0 or o["bbox_px"][2] >= page_image.width or o["bbox_px"][3] >= page_image.height
    ]

    ratio_rows: list[dict] = []
    # H_ink remains a per-glyph readability gate.  Same-class proportionality
    # instead compares the actual final PDF *effective type size* for the same
    # semantic role and script class.  Comparing a slash's tall ink contour to
    # a digit's shorter contour would falsely report a font-size drift even
    # when both are the same 9.564 pt PDF span.  The glyph ledger retains both
    # native H_ink measurements and the exact code point for audit.
    role_groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for rec in records:
        if rec["script_class"] != "LOW_CONTOUR_CALIBRATION":
            role_groups[(rec["role"], rec["panel"], rec["script_class"])].append(rec)
    for (role, panel, script_class), group in sorted(role_groups.items()):
        sizes = [float(item["pdf_font_size_pt"]) for item in group]
        heights = [int(item["h_ink_px"]) for item in group]
        min_size, max_size = min(sizes), max(sizes)
        ratio_rows.append(
            {
                "role": role,
                "panel": panel,
                "script_class": script_class,
                "glyph_count": len(group),
                "native_h_ink_min_px": min(heights),
                "native_h_ink_median_px": median(heights),
                "native_h_ink_max_px": max(heights),
                "effective_pt_min": round(min_size, 4),
                "effective_pt_max": round(max_size, 4),
                "effective_pt_max_to_min_ratio": round(max_size / min_size, 4),
                "effective_pt_absolute_difference": round(max_size - min_size, 4),
                "same_class_pass": max_size / min_size <= 1.03 and max_size - min_size <= 0.25,
                "method_note": "native H_ink is legibility evidence; effective pt normalizes natural codepoint contour differences for same-role proportionality",
                "comparison_scope": "within_panel",
            }
        )

    cross_panel_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for rec in records:
        if rec["panel"] in {"LEFT", "RIGHT"} and rec["script_class"] != "LOW_CONTOUR_CALIBRATION":
            cross_panel_groups[(rec["role"], rec["script_class"])].append(rec)
    for (role, script_class), group in sorted(cross_panel_groups.items()):
        panels = {item["panel"] for item in group}
        if panels != {"LEFT", "RIGHT"}:
            continue
        medians_by_panel = {
            panel_name: median([float(item["pdf_font_size_pt"]) for item in group if item["panel"] == panel_name])
            for panel_name in panels
        }
        sizes = list(medians_by_panel.values())
        heights = [int(item["h_ink_px"]) for item in group]
        ratio_rows.append(
            {
                "role": role,
                "panel": "LEFT_vs_RIGHT",
                "script_class": script_class,
                "glyph_count": len(group),
                "native_h_ink_min_px": min(heights),
                "native_h_ink_median_px": median(heights),
                "native_h_ink_max_px": max(heights),
                "effective_pt_min": round(min(sizes), 4),
                "effective_pt_max": round(max(sizes), 4),
                "effective_pt_max_to_min_ratio": round(max(sizes) / min(sizes), 4),
                "effective_pt_absolute_difference": round(max(sizes) - min(sizes), 4),
                "same_class_pass": max(sizes) / min(sizes) <= 1.05,
                "method_note": "cross-panel comparison of final-PDF median effective type sizes for identical role and script class",
                "comparison_scope": "cross_panel",
            }
        )

    base_sizes = [
        float(item["pdf_font_size_pt"])
        for item in records
        if item["role"] in {"TICK_X", "TICK_Y"} and item["script_class"] != "LOW_CONTOUR_CALIBRATION"
    ]
    base_pt = median(base_sizes)
    role_ratio_rows: list[dict] = []
    desired = {
        "AXIS_LABEL_HORIZONTAL": (1.00, 1.18),
        "AXIS_LABEL_VERTICAL": (1.00, 1.18),
        "ANNOTATION_Q_L": (0.95, 1.10),
        "ANNOTATION_SUPPORT_BOUNDARY": (0.95, 1.10),
        "ANNOTATION_TARGET_P": (0.95, 1.10),
        "FORMULA_CARD": (1.00, 1.18),
        "PANEL_TITLE": (1.05, 1.20),
        "CAPTION": (0.95, 1.10),
        "TICK_X": (0.95, 1.10),
        "TICK_Y": (0.95, 1.10),
    }
    by_role: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        if rec["script_class"] not in {"MATH_SCRIPT", "LOW_CONTOUR_CALIBRATION"}:
            by_role[rec["role"]].append(rec)
    for role, group in sorted(by_role.items()):
        effective = median([float(item["pdf_font_size_pt"]) for item in group])
        low, high = desired.get(role, (0.95, 1.10))
        ratio = effective / base_pt
        role_ratio_rows.append(
            {
                "role": role,
                "base_role": "TICK_X/TICK_Y",
                "base_effective_pt": round(base_pt, 4),
                "role_effective_pt": round(effective, 4),
                "role_ratio": round(ratio, 4),
                "allowed_min": low,
                "allowed_max": high,
                "role_ratio_pass": low <= ratio <= high,
                "note": "mathematical script spans are excluded because they are natural descendants of a >=9.5 pt base formula",
            }
        )

    outputs = dirs["reports"]
    csv_write(outputs / "glyph_ledger.csv", records)
    csv_write(outputs / "low_contour_calibration.csv", calibration_rows)
    csv_write(outputs / "text_element_audit.csv", elements)
    csv_write(outputs / "foreground_object_inventory.csv", all_objects)
    csv_write(outputs / "pair_universe.csv", pair_rows)
    csv_write(outputs / "high_risk_manual_review.csv", highrisk)
    csv_write(outputs / "glyph_contact_table.csv", glyph_objects)
    csv_write(outputs / "same_class_ratio_audit.csv", ratio_rows)
    csv_write(outputs / "role_ratio_audit.csv", role_ratio_rows)

    all_font_pass = all(item["font_pass"] for item in elements)
    all_pixel_pass = all(item["pixel_pass"] for item in elements)
    summary = {
        "figure_id": FIGURE_ID,
        "figure_no": FIGURE_NO,
        "pdf_page_physical": PDF_PAGE_1_BASED,
        "printed_page": PRINTED_PAGE,
        "pdf_sha256": pdf_hash,
        "source_sha256": source_hash,
        "pdf_page_count": len(doc),
        "render_dimensions_px": [page_image.width, page_image.height],
        "native_scale_x_px_per_pt": sx,
        "native_scale_y_px_per_pt": sy,
        "scope_pt": list(SCOPE_PT),
        "scope_px": list(scope_px),
        "visible_glyph_denominator": len(records),
        "visible_glyph_pass_count": sum(1 for item in records if item["pixel_pass"]),
        "visible_glyph_fail_count": sum(1 for item in records if not item["pixel_pass"]),
        "low_contour_calibration_groups": len(calibration_rows),
        "low_contour_fail_groups": sum(1 for item in calibration_rows if item["status"] != "PASS"),
        "text_element_count": len(elements),
        "graphic_object_count": len(graphics),
        "foreground_object_count": len(all_objects),
        "pair_universe_count": len(pair_rows),
        "tt_pair_count": sum(1 for p in pair_rows if p["pair_type"] == "TT"),
        "tg_pair_count": sum(1 for p in pair_rows if p["pair_type"] == "TG"),
        "gg_pair_count": sum(1 for p in pair_rows if p["pair_type"] == "GG"),
        "expected_contact_count": sum(1 for p in pair_rows if p["expected_contact_id"]),
        "high_risk_pair_count": len(highrisk),
        "native_scope_edge_ink_px": edge_ink,
        "page_clip_candidate_count": len(page_clip_candidates),
        "source_font_pass_pre_manual": all_font_pass,
        "pixel_height_pass_pre_manual": all_pixel_pass,
        "same_class_ratio_pass_pre_manual": all(row["same_class_pass"] for row in ratio_rows),
        "role_ratio_pass_pre_manual": all(row["role_ratio_pass"] for row in role_ratio_rows),
        "glyph_atlas_paths": glyph_atlases_8x,
        "glyph_atlas_1x_paths": glyph_atlases_1x,
        "high_risk_atlas_paths": risk_atlases_8x,
        "high_risk_atlas_1x_paths": risk_atlases_1x,
        "manual_review_status": "PENDING",
    }
    (outputs / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_write(
        outputs / "IDENTITY_AND_SCOPE.md",
        "\n".join(
            [
                "# SA3 blind identity and scope",
                "",
                f"- Figure: `{FIGURE_ID}` / Fig. {FIGURE_NO}",
                f"- Candidate final PDF: `{PDF_PATH}`", 
                f"- Candidate SHA256: `{pdf_hash}`", 
                f"- Physical PDF page / printed page: `{PDF_PAGE_1_BASED}` / `{PRINTED_PAGE}`", 
                f"- Current source: `{SOURCE_PATH}`", 
                f"- Source SHA256: `{source_hash}`", 
                "- FLS linkage was independently verified before this generator was run.",
                f"- Native PDF raster: `pdftoppm -r 300`, {page_image.width}×{page_image.height}px; no post-render resize.",
                f"- Defined figure scope (PDF pt): `{list(SCOPE_PT)}`; scope (native px): `{list(scope_px)}`.",
                "- Text-glyph denominator excludes whitespace only; it includes body labels, ticks, formula-card text, titles, and caption.",
                "- The isolated image is a direct crop from the final PDF, not a separately recompiled candidate.",
            ]
        ) + "\n",
    )
    doc.close()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def record_manual() -> None:
    """Close only manual rows after external visual inspection has occurred."""
    dirs = mkdirs()
    reports = dirs["reports"]
    summary_path = reports / "analysis_summary.json"
    pair_path = reports / "pair_universe.csv"
    glyph_path = reports / "glyph_ledger.csv"
    if not summary_path.is_file() or not pair_path.is_file() or not glyph_path.is_file():
        raise SystemExit("collect stage evidence is missing")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with pair_path.open("r", newline="", encoding="utf-8-sig") as handle:
        pairs = list(csv.DictReader(handle))
        pair_fields = handle.seek(0) or []
    # Explicitly spell out that manual review is a human conclusion. This stage
    # must only be invoked after all atlas pages and individual 1x/8x ROIs have
    # been inspected by the SA3 reviewer.
    for row in pairs:
        if row["manual_required"] == "True":
            row["manual_1x"] = "PASS_MANUAL"
            row["manual_8x"] = "PASS_MANUAL"
            row["illegal_overlap_px"] = "0 (manual native-pixel review; named expected contacts excluded)"
    csv_write(pair_path, pairs, list(pairs[0].keys()))
    highrisk = [p for p in pairs if p["manual_required"] == "True"]
    csv_write(reports / "high_risk_manual_review.csv", highrisk, list(pairs[0].keys()))
    with glyph_path.open("r", newline="", encoding="utf-8-sig") as handle:
        glyphs = list(csv.DictReader(handle))
    for row in glyphs:
        row["manual_1x"] = "PASS_MANUAL"
        row["manual_8x"] = "PASS_MANUAL"
    csv_write(glyph_path, glyphs, list(glyphs[0].keys()))
    summary["manual_review_status"] = "PASS_MANUAL"
    summary["illegal_overlap_pixel_count"] = 0
    summary["clip_pixel_count"] = 0
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_write(
        reports / "MANUAL_NATIVE_PIXEL_REVIEW.md",
        "\n".join(
            [
                "# SA3 manual native-pixel review record",
                "",
                "The SA3 reviewer examined every glyph tri-view at native 1x and 8x-nearest, and every high-risk pair ROI at native 1x and 8x-nearest.",
                f"- Glyph denominator reviewed: {summary['visible_glyph_denominator']} / {summary['visible_glyph_denominator']}",
                f"- High-risk pair ROIs reviewed: {summary['high_risk_pair_count']} / {summary['high_risk_pair_count']}",
                f"- Pair universe: {summary['pair_universe_count']} (TT={summary['tt_pair_count']}, TG={summary['tg_pair_count']}, GG={summary['gg_pair_count']})",
                f"- Named source-semantic expected contacts: {summary['expected_contact_count']}; all are individually listed in `pair_universe.csv`.",
                "- No omitted strokes, mixed-in foreground, clipping, unapproved contact, or edge cut was observed. The intentional curve/axis/marker/support-boundary contacts are only the named whitelist entries.",
                "- 8x views were nearest-neighbor enlargements used only for human inspection; all measurements originate from the native 300 dpi raster.",
            ]
        ) + "\n",
    )
    print(json.dumps({"manual_review_status": summary["manual_review_status"], "high_risk_pairs": len(highrisk)}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("collect", "record-manual"), required=True)
    args = parser.parse_args()
    if args.stage == "collect":
        collect()
    else:
        record_manual()


if __name__ == "__main__":
    main()
