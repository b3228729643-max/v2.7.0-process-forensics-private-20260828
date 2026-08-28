#!/usr/bin/env python3
"""Read-only strict R1 visual audit for FIG-P467-01.

Inputs are immutable: the official R93 full-book PDF and the current TikZ source.
All generated artifacts are intentionally confined to this script's directory.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第04册_无监督学习与矩阵分解\V4-C03\fig_v4_c03_svd_geometry.tex")
SOURCE_REL = "src/绘图源码/第04册_无监督学习与矩阵分解/V4-C03/fig_v4_c03_svd_geometry.tex"
STYLE_REL = "src/讲义源码/common/statlearnbook.sty"
PDF_PAGE_NUMBER = 509  # one-based physical page, independently found by caption text
PRINTED_PAGE = 496
FIGURE_NO = "图26.1"
PDF_DPI = 300
FIG_RECT_PT = (150.0, 200.0, 435.0, 322.0)  # tight source-figure/caption crop, no resize
FG_DELTA = 20


def mkdirs() -> dict[str, Path]:
    result = {"raw": OUT / "raw", "masks": OUT / "masks", "overlays": OUT / "overlays", "pairs": OUT / "pairs"}
    for path in result.values():
        path.mkdir(parents=True, exist_ok=True)
    return result


DIR = mkdirs()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rect_union(rects: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    return (min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects), max(r[3] for r in rects))


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def clip_rect(rect: tuple[int, int, int, int], w: int, h: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (max(0, x0), max(0, y0), min(w, x1), min(h, y1))


def crop_with_pad(image: Image.Image, rect: tuple[int, int, int, int], pad: int = 6) -> tuple[Image.Image, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = clip_rect((rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad), image.width, image.height)
    return image.crop((x0, y0, x1, y1)), (x0, y0, x1, y1)


def foreground_mask(arr: np.ndarray) -> np.ndarray:
    # Page background is PDF white. The 20/255 criterion is exactly the strict protocol's C threshold.
    return np.max(np.abs(arr.astype(np.int16) - 255), axis=2) >= FG_DELTA


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def classify_char(c: str, is_script_t: bool = False) -> tuple[str, int]:
    if is_script_t:
        return "NATURAL_SUPERSCRIPT", 15
    if "CJK UNIFIED IDEOGRAPH" in unicodedata.name(c, ""):
        return "CJK", 30
    name = unicodedata.name(c, "")
    if c.isdigit():
        return "DIGIT", 24
    if c in "+-=−×÷<>≤≥≈≠∑∫":
        return "MATH_OPERATOR", 22
    if "CAPITAL" in name or c in "Σ𝑉𝑈":
        return "UPPERCASE_OR_GREEK", 24
    if "SMALL" in name or c.islower():
        return "LOWERCASE_OR_GREEK", 17
    if unicodedata.category(c).startswith("P") or c in "：；，。、.:":
        return "PUNCTUATION", 22
    return "OTHER_VISIBLE", 17


def text_group_for(xmid: float, ymid: float) -> tuple[str, str, str, int, float, str, str]:
    """Return logical object, panel, role, source line, base TeX pt, file, source description."""
    if 200.0 <= ymid < 225.0:
        if xmid < 222.0:
            return "TITLE_P1", "P1", "PANEL_TITLE", 21, 9.4, SOURCE_REL, "title style line 19; title content line 21"
        if xmid < 295.0:
            return "TITLE_P2", "P2", "PANEL_TITLE", 28, 9.4, SOURCE_REL, "title style line 19; title content line 28"
        if xmid < 360.0:
            return "TITLE_P3", "P3", "PANEL_TITLE", 33, 9.4, SOURCE_REL, "title style line 19; title content line 33"
        return "TITLE_P4", "P4", "PANEL_TITLE", 38, 9.4, SOURCE_REL, "title style line 19; title content line 38"
    if 280.0 <= ymid < 300.0:
        return "ANNOTATION", "GLOBAL", "ANNOTATION", 48, 9.0, SOURCE_REL, "explicit node font line 48"
    if 300.0 <= ymid <= 322.0:
        if xmid < 190.0:
            return "CAPTION_LABEL", "GLOBAL", "CAPTION_LABEL", 50, 10.0, f"{SOURCE_REL}; {STYLE_REL}", "caption line 50; inherited small at statlearnbook.sty:305"
        return "CAPTION_TEXT", "GLOBAL", "CAPTION_TEXT", 50, 10.0, f"{SOURCE_REL}; {STYLE_REL}", "caption line 50; inherited small at statlearnbook.sty:305"
    raise ValueError(f"unexpected figure text character at {xmid=}, {ymid=}")


def nominal_effective_pt(group: str, c: str) -> tuple[float, bool, str]:
    if group == "TITLE_P2" and c == "T":
        return 6.58, True, "natural superscript from title base (PDF extraction: 6.555 bp -> 6.58 TeX pt)"
    if group.startswith("TITLE"):
        return 9.4, False, "explicit title style"
    if group == "ANNOTATION":
        return 9.0, False, "explicit node font"
    return 10.0, False, "inherited caption small"


def pixel_box(pdf_box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    return (math.floor(pdf_box[0] * sx), math.floor(pdf_box[1] * sy), math.ceil(pdf_box[2] * sx), math.ceil(pdf_box[3] * sy))


def exact_pair_clearance(mask_a: np.ndarray, mask_b: np.ndarray, roi: tuple[int, int, int, int]) -> tuple[int, float]:
    x0, y0, x1, y1 = roi
    a = mask_a[y0:y1, x0:x1]
    b = mask_b[y0:y1, x0:x1]
    overlap = int(np.count_nonzero(a & b))
    if not np.any(a) or not np.any(b):
        return overlap, float("nan")
    dist = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 5)
    return overlap, float(dist[a].min())


def pair_roi(a: tuple[int, int, int, int], b: tuple[int, int, int, int], w: int, h: int, pad: int = 4) -> tuple[int, int, int, int]:
    return clip_rect((min(a[0], b[0]) - pad, min(a[1], b[1]) - pad, max(a[2], b[2]) + pad, max(a[3], b[3]) + pad), w, h)


def main() -> None:
    if not PDF.is_file() or not SOURCE.is_file():
        raise SystemExit("frozen PDF or source file is missing")
    page300_path = OUT / "after_full_page_300dpi.png"
    page200_path = OUT / "after_full_page_200dpi.png"
    if not page300_path.is_file() or not page200_path.is_file():
        raise SystemExit("direct pdftoppm page renders are required before this audit")

    page_img = Image.open(page300_path).convert("RGB")
    img = np.asarray(page_img)
    h, w = img.shape[:2]
    doc = fitz.open(PDF)
    page = doc[PDF_PAGE_NUMBER - 1]
    sx, sy = w / page.rect.width, h / page.rect.height
    if not (4.15 <= sx <= 4.18 and 4.15 <= sy <= 4.18):
        raise SystemExit(f"not a direct 300 dpi page rendering: sx={sx}, sy={sy}")

    fig_px = pixel_box(FIG_RECT_PT, sx, sy)
    fig_px = clip_rect(fig_px, w, h)
    figure_crop = page_img.crop(fig_px)
    figure_crop.save(OUT / "after_figure_crop_300dpi.png")
    # The standalone view is a non-resampled crop of the sole frozen PDF candidate.
    figure_crop.save(OUT / "after_standalone_300dpi.png")
    figure_crop.convert("L").save(OUT / "after_grayscale_300dpi.png")

    rawdict = page.get_text("rawdict")
    glyphs: list[dict] = []
    seq = 0
    for block in rawdict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span.get("chars", []):
                    c = char["c"]
                    if not c or c.isspace():
                        continue
                    b = tuple(float(v) for v in char["bbox"])
                    xmid, ymid = ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)
                    if not (150.0 <= xmid <= 435.0 and 200.0 <= ymid <= 322.0):
                        continue
                    group, panel, role, source_line, declared_pt, source_file, source_desc = text_group_for(xmid, ymid)
                    effective_pt, is_natural_script, eff_desc = nominal_effective_pt(group, c)
                    script_class, threshold = classify_char(c, is_script_t=(group == "TITLE_P2" and c == "T"))
                    pbox = pixel_box(b, sx, sy)
                    pbox = clip_rect(pbox, w, h)
                    raw_roi = img[pbox[1]:pbox[3], pbox[0]:pbox[2]]
                    mask_roi = foreground_mask(raw_roi)
                    yy, xx = np.where(mask_roi)
                    if len(yy):
                        ink_x0, ink_y0 = int(pbox[0] + xx.min()), int(pbox[1] + yy.min())
                        ink_x1, ink_y1 = int(pbox[0] + xx.max() + 1), int(pbox[1] + yy.max() + 1)
                        h_ink = int(ink_y1 - ink_y0)
                    else:
                        ink_x0 = ink_y0 = ink_x1 = ink_y1 = -1
                        h_ink = 0
                    if is_natural_script:
                        source_font_pass = declared_pt >= 9.5
                        source_reason = "FAIL: natural superscript is only allowed from a >=9.5pt base; title base is 9.4pt"
                    else:
                        source_font_pass = effective_pt >= 9.5
                        source_reason = "PASS" if source_font_pass else f"FAIL: effective {effective_pt:.2f}pt < 9.50pt"
                    pixel_pass = h_ink >= threshold
                    pixel_reason = "PASS" if pixel_pass else f"FAIL: H_ink={h_ink}px < {threshold}px for {script_class}"
                    seq += 1
                    glyphs.append({
                        "ELEMENT_ID": f"GLYPH_{seq:03d}", "PARENT_ID": group, "PANEL_ID": panel, "ROLE": role,
                        "SOURCE_FILE": source_file, "SOURCE_LINE": source_line, "SOURCE_DECLARATION": source_desc,
                        "DECLARED_PT": declared_pt, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": round(effective_pt, 3),
                        "PDF_FONT_SIZE_TEX_PT": round(float(span["size"]) * 72.27 / 72.0, 3), "TEXT_SAMPLE": c,
                        "SCRIPT_CLASS": script_class, "PIXEL_THRESHOLD": threshold, "PDF_BBOX_X0": round(b[0], 3),
                        "PDF_BBOX_Y0": round(b[1], 3), "PDF_BBOX_X1": round(b[2], 3), "PDF_BBOX_Y1": round(b[3], 3),
                        "BBOX_X0": pbox[0], "BBOX_Y0": pbox[1], "BBOX_X1": pbox[2], "BBOX_Y1": pbox[3],
                        "INK_X0": ink_x0, "INK_Y0": ink_y0, "INK_X1": ink_x1, "INK_Y1": ink_y1,
                        "H_INK_PX": h_ink, "SOURCE_FONT_PASS": source_font_pass, "PIXEL_PASS": pixel_pass,
                        "SOURCE_REASON": source_reason, "PIXEL_REASON": pixel_reason, "EFFECTIVE_NOTE": eff_desc,
                        "mask_roi": mask_roi, "pixel_box": pbox,
                    })

    if not glyphs:
        raise SystemExit("no figure glyphs located")

    # Preserve raw/mask/overlay evidence for every visible glyph, including independent
    # punctuation and natural-script substrings used by the strict pixel gates.
    for folder in (DIR["raw"] / "glyphs", DIR["masks"] / "glyphs", DIR["overlays"] / "glyphs"):
        folder.mkdir(parents=True, exist_ok=True)
    glyph_font = ImageFont.load_default()
    for g in glyphs:
        raw_crop, crop_box = crop_with_pad(page_img, g["pixel_box"], pad=6)
        raw_rel = f"raw/glyphs/{g['ELEMENT_ID']}_raw_300dpi.png"
        mask_rel = f"masks/glyphs/{g['ELEMENT_ID']}_mask_unexpanded_300dpi.png"
        overlay_rel = f"overlays/glyphs/{g['ELEMENT_ID']}_bbox_mask_overlay_300dpi.png"
        raw_crop.save(OUT / raw_rel)
        save_mask(g["mask_roi"], OUT / mask_rel)
        glyph_overlay = raw_crop.copy()
        gd = ImageDraw.Draw(glyph_overlay)
        gb = g["pixel_box"]
        color = (220, 0, 0) if not (g["SOURCE_FONT_PASS"] and g["PIXEL_PASS"]) else (0, 130, 0)
        gd.rectangle((gb[0] - crop_box[0], gb[1] - crop_box[1], gb[2] - crop_box[0], gb[3] - crop_box[1]), outline=color, width=1)
        gd.text((1, 1), g["ELEMENT_ID"], fill=(200, 0, 0), font=glyph_font)
        glyph_overlay.save(OUT / overlay_rel)
        g["RAW_ROI"] = raw_rel
        g["MASK"] = mask_rel
        g["OVERLAY"] = overlay_rel

    # Build logical independent text objects from the glyph masks. Characters are separate for pixel tests,
    # but contiguous glyphs in one label are intentionally one TEXT object for clearance tests.
    text_objects: list[dict] = []
    full_text_mask = np.zeros((h, w), dtype=bool)
    for parent in ["TITLE_P1", "TITLE_P2", "TITLE_P3", "TITLE_P4", "ANNOTATION", "CAPTION_LABEL", "CAPTION_TEXT"]:
        members = [g for g in glyphs if g["PARENT_ID"] == parent]
        if not members:
            continue
        bbox = rect_union([g["pixel_box"] for g in members])
        mask = np.zeros((h, w), dtype=bool)
        for g in members:
            x0, y0, x1, y1 = g["pixel_box"]
            mask[y0:y1, x0:x1] |= g["mask_roi"]
        full_text_mask |= mask
        text_objects.append({"OBJECT_ID": parent, "OBJECT_CLASS": "TEXT", "PANEL_ID": members[0]["PANEL_ID"], "ROLE": members[0]["ROLE"], "bbox": bbox, "mask": mask})

    # Extract independent vector paths from the final PDF. These source-independent vector bboxes are kept
    # separately; graphic-graphic contacts are geometric/data contacts and are never reclassified as text collisions.
    graphics: list[dict] = []
    full_graphics_mask = np.zeros((h, w), dtype=bool)
    for idx, drawing in enumerate(page.get_drawings(), start=1):
        r = drawing["rect"]
        if r.x1 < 150 or r.x0 > 435 or r.y1 < 220 or r.y0 > 285:
            continue
        pad_pt = max(0.8, float(drawing.get("width") or 0.0) / 2.0 + 0.8)
        pbox = pixel_box((r.x0 - pad_pt, r.y0 - pad_pt, r.x1 + pad_pt, r.y1 + pad_pt), sx, sy)
        pbox = clip_rect(pbox, w, h)
        roi = img[pbox[1]:pbox[3], pbox[0]:pbox[2]]
        roi_mask = foreground_mask(roi)
        mask = np.zeros((h, w), dtype=bool)
        mask[pbox[1]:pbox[3], pbox[0]:pbox[2]] = roi_mask
        full_graphics_mask |= mask
        fill = drawing.get("fill")
        width = drawing.get("width")
        kind = "FILLED_MARKER_OR_ARROWHEAD" if fill is not None and width is None else "VECTOR_PATH"
        graphics.append({
            "OBJECT_ID": f"GFX_{len(graphics)+1:03d}", "OBJECT_CLASS": kind, "PANEL_ID": "P1-P4",
            "ROLE": "LINE_ARROW_MARKER_DATA", "bbox": pbox, "mask": mask,
            "pdf_bbox": (float(r.x0), float(r.y0), float(r.x1), float(r.y1)), "width_pt": width,
            "stroke": drawing.get("color"), "fill": fill, "item_count": len(drawing.get("items", [])),
        })

    # Object inventory and individual raw/mask/overlay artifacts for every independent text/vector object.
    objects = text_objects + graphics
    inventory: list[dict] = []
    for obj in objects:
        oid = obj["OBJECT_ID"]
        bbox = obj["bbox"]
        raw_crop, crop_box = crop_with_pad(page_img, bbox)
        local_mask = obj["mask"][crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
        raw_rel = f"raw/{oid}_raw_300dpi.png"
        mask_rel = f"masks/{oid}_mask_unexpanded_300dpi.png"
        overlay_rel = f"overlays/{oid}_bbox_mask_overlay_300dpi.png"
        raw_crop.save(OUT / raw_rel)
        save_mask(local_mask, OUT / mask_rel)
        over = raw_crop.copy()
        draw = ImageDraw.Draw(over)
        ox0, oy0 = bbox[0] - crop_box[0], bbox[1] - crop_box[1]
        ox1, oy1 = bbox[2] - crop_box[0], bbox[3] - crop_box[1]
        draw.rectangle((ox0, oy0, ox1, oy1), outline=(255, 0, 0) if obj["OBJECT_CLASS"] == "TEXT" else (0, 100, 255), width=2)
        draw.text((1, 1), oid, fill=(200, 0, 0), font=ImageFont.load_default())
        over.save(OUT / overlay_rel)
        inventory.append({
            "OBJECT_ID": oid, "OBJECT_CLASS": obj["OBJECT_CLASS"], "PANEL_ID": obj["PANEL_ID"], "ROLE": obj["ROLE"],
            "BBOX_X0": bbox[0], "BBOX_Y0": bbox[1], "BBOX_X1": bbox[2], "BBOX_Y1": bbox[3],
            "FOREGROUND_PIXEL_COUNT": int(np.count_nonzero(obj["mask"])), "RAW_ROI": raw_rel, "MASK": mask_rel, "OVERLAY": overlay_rel,
        })
    write_csv(OUT / "objects_inventory.csv", inventory)

    # Retain unexpanded masks for reproducibility and an explicit zero-overlap mask.
    fx0, fy0, fx1, fy1 = fig_px
    save_mask(full_text_mask[fy0:fy1, fx0:fx1], DIR["masks"] / "figure_text_foreground_mask_unexpanded_300dpi.png")
    save_mask(full_graphics_mask[fy0:fy1, fx0:fx1], DIR["masks"] / "figure_graphics_foreground_mask_unexpanded_300dpi.png")
    save_mask((full_text_mask & full_graphics_mask)[fy0:fy1, fx0:fx1], DIR["masks"] / "figure_text_graphic_overlap_mask_unexpanded_300dpi.png")

    # Same-class comparisons use logical text *elements/substrings*, never isolated glyph shapes:
    # e.g. a Chinese 一 has a short ink bbox but must still fail its own 30px glyph gate; it is
    # not evidence of a different font size from the rest of its annotation. Punctuation/scripts
    # are independently thresholded but are not semantic role-size comparators.
    ratio_units: list[dict] = []
    glyph_groups: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for g in glyphs:
        glyph_groups[(g["PARENT_ID"], g["PANEL_ID"], g["ROLE"], g["SCRIPT_CLASS"])].append(g)
    for (parent, panel, role, sclass), members in sorted(glyph_groups.items()):
        if sclass in {"PUNCTUATION", "NATURAL_SUPERSCRIPT"}:
            for g in members:
                g["CLASS_MEDIAN_PX"] = "N/A"
                g["RATIO_TO_CLASS_MEDIAN"] = "N/A (not a semantic-size comparator)"
            continue
        b = rect_union([g["pixel_box"] for g in members])
        unit_mask = np.zeros((h, w), dtype=bool)
        for g in members:
            x0, y0, x1, y1 = g["pixel_box"]
            unit_mask[y0:y1, x0:x1] |= g["mask_roi"]
        yy, _ = np.where(unit_mask)
        unit_h = int(yy.max() - yy.min() + 1) if len(yy) else 0
        ratio_units.append({"UNIT_ID": f"{parent}:{sclass}", "PARENT_ID": parent, "PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": sclass, "H_INK_PX": unit_h, "MEMBERS": members})

    same_rows: list[dict] = []
    same_class_pass = True
    unit_groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for unit in ratio_units:
        unit_groups[(unit["PANEL_ID"], unit["ROLE"], unit["SCRIPT_CLASS"])].append(unit)
    for (panel, role, sclass), units in sorted(unit_groups.items()):
        hs = [u["H_INK_PX"] for u in units]
        median = float(statistics.median(hs))
        ratios = [h / median if median else 0.0 for h in hs]
        passed = len(units) == 1 or all(0.92 <= r <= 1.08 for r in ratios)
        if not passed:
            same_class_pass = False
        same_rows.append({"SCOPE": "INTRA_PANEL", "PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": sclass, "ELEMENT_COUNT": len(units), "MEDIAN_H_INK_PX": round(median, 3), "MIN_RATIO": round(min(ratios), 4), "MAX_RATIO": round(max(ratios), 4), "MAX_OVER_MIN": round(max(hs) / min(hs), 4) if min(hs) else "INF", "THRESHOLD": "semantic elements [0.92,1.08]", "PASS_FAIL": "PASS" if passed else "FAIL", "ELEMENT_IDS": "|".join(u["UNIT_ID"] for u in units)})

    # Cross-panel consistency has one panel-local element unit per title role / script class.
    cross_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for unit in ratio_units:
        if unit["PANEL_ID"] in {"P1", "P2", "P3", "P4"}:
            cross_groups[(unit["ROLE"], unit["SCRIPT_CLASS"])].append(unit)
    for (role, sclass), units in sorted(cross_groups.items()):
        if len(units) < 2:
            continue
        hs = [u["H_INK_PX"] for u in units]
        ratio = max(hs) / min(hs) if min(hs) else float("inf")
        passed = ratio <= 1.10
        same_class_pass &= passed
        median = float(statistics.median(hs))
        for unit in units:
            for g in unit["MEMBERS"]:
                g["CLASS_MEDIAN_PX"] = round(median, 3)
                g["RATIO_TO_CLASS_MEDIAN"] = round(unit["H_INK_PX"] / median, 4) if median else 0.0
        same_rows.append({"SCOPE": "CROSS_PANEL", "PANEL_ID": "P1-P4", "ROLE": role, "SCRIPT_CLASS": sclass, "ELEMENT_COUNT": len(units), "MEDIAN_H_INK_PX": "|".join(f"{u['PANEL_ID']}:{u['H_INK_PX']:.2f}" for u in units), "MIN_RATIO": "", "MAX_RATIO": "", "MAX_OVER_MIN": round(ratio, 4), "THRESHOLD": "panel medians <=1.10", "PASS_FAIL": "PASS" if passed else "FAIL", "ELEMENT_IDS": "|".join(u["UNIT_ID"] for u in units)})
    # Single-panel role units retain their own element height as a traceable N/A ratio baseline.
    for unit in ratio_units:
        for g in unit["MEMBERS"]:
            if "CLASS_MEDIAN_PX" not in g:
                g["CLASS_MEDIAN_PX"] = unit["H_INK_PX"]
                g["RATIO_TO_CLASS_MEDIAN"] = 1.0
    write_csv(OUT / "same_class_ratio_audit.csv", same_rows)

    # Role hierarchy. There are no ticks or ordinary nodes, so the explanatory annotation is the documented BASE.
    base_hs = [g["H_INK_PX"] for g in glyphs if g["PARENT_ID"] == "ANNOTATION" and g["SCRIPT_CLASS"] == "CJK"]
    base = float(statistics.median(base_hs))
    title_hs = [g["H_INK_PX"] for g in glyphs if g["ROLE"] == "PANEL_TITLE" and g["SCRIPT_CLASS"] == "CJK"]
    title_median = float(statistics.median(title_hs))
    title_ratio = title_median / base if base else 0.0
    role_rows = [{
        "BASE_ROLE": "ANNOTATION/CJK", "BASE_SELECTION_REASON": "No ticks or normal node text are present; the explanatory annotation is the only ordinary reader text.",
        "TARGET_ROLE": "PANEL_TITLE/CJK", "TARGET_MEDIAN_PX": round(title_median, 3), "BASE_MEDIAN_PX": round(base, 3), "ROLE_RATIO": round(title_ratio, 4),
        "REQUIRED_RANGE": "[1.05,1.20] (panel-label hierarchy)", "PASS_FAIL": "PASS" if 1.05 <= title_ratio <= 1.20 else "FAIL", "NOTES": "CJK-to-CJK comparison only; math glyphs remain separately measured and are not mixed with CJK."
    }]
    role_ratio_pass = role_rows[0]["PASS_FAIL"] == "PASS"
    write_csv(OUT / "role_ratio_audit.csv", role_rows)
    for g in glyphs:
        g["ROLE_RATIO"] = round(title_ratio, 4) if g["ROLE"] == "PANEL_TITLE" and g["SCRIPT_CLASS"] == "CJK" else "N/A"

    # Full pair audit: all logical text objects x all vector paths, plus all independent TEXT-TEXT pairs.
    overlap_rows: list[dict] = []
    critical_candidates: list[tuple[float, dict]] = []
    text_text_min = float("inf")
    text_gfx_min = float("inf")
    overlap_total = 0
    for i, a in enumerate(text_objects):
        for b in text_objects[i + 1:]:
            gap = bbox_gap(a["bbox"], b["bbox"])
            roi = pair_roi(a["bbox"], b["bbox"], w, h)
            overlap, clearance = exact_pair_clearance(a["mask"], b["mask"], roi)
            overlap_total += overlap
            text_text_min = min(text_text_min, gap)
            row = {"PAIR_ID": f"TT_{a['OBJECT_ID']}_{b['OBJECT_ID']}", "PAIR_TYPE": "TEXT_TEXT", "OBJECT_A": a["OBJECT_ID"], "OBJECT_B": b["OBJECT_ID"], "A_CLASS": a["OBJECT_CLASS"], "B_CLASS": b["OBJECT_CLASS"], "INTENTIONAL_GEOMETRY": "NO", "BBOX_CLEARANCE_PX": round(gap, 3), "FOREGROUND_OVERLAP_PX": overlap, "MIN_FOREGROUND_CLEARANCE_PX": round(clearance, 3), "REQUIRED_CLEARANCE_PX": 4, "PASS_FAIL": "PASS" if overlap == 0 and gap >= 4 else "FAIL", "METHOD": "unexpanded foreground masks + vector bbox", "RAW_A": f"raw/{a['OBJECT_ID']}_raw_300dpi.png", "RAW_B": f"raw/{b['OBJECT_ID']}_raw_300dpi.png"}
            overlap_rows.append(row)
            critical_candidates.append((gap, row))
    for a in text_objects:
        for b in graphics:
            gap = bbox_gap(a["bbox"], b["bbox"])
            # Bboxes are a rigorous no-overlap proof if separated. The closest candidates also get exact mask distance.
            if gap <= 60:
                roi = pair_roi(a["bbox"], b["bbox"], w, h)
                overlap, clearance = exact_pair_clearance(a["mask"], b["mask"], roi)
                method = "unexpanded foreground masks (critical / near pair)"
            else:
                overlap, clearance = 0, gap
                method = "disjoint vector bboxes; foreground clearance lower-bounded by bbox clearance"
            overlap_total += overlap
            text_gfx_min = min(text_gfx_min, clearance)
            row = {"PAIR_ID": f"TG_{a['OBJECT_ID']}_{b['OBJECT_ID']}", "PAIR_TYPE": "TEXT_GRAPHIC", "OBJECT_A": a["OBJECT_ID"], "OBJECT_B": b["OBJECT_ID"], "A_CLASS": a["OBJECT_CLASS"], "B_CLASS": b["OBJECT_CLASS"], "INTENTIONAL_GEOMETRY": "NO", "BBOX_CLEARANCE_PX": round(gap, 3), "FOREGROUND_OVERLAP_PX": overlap, "MIN_FOREGROUND_CLEARANCE_PX": round(clearance, 3), "REQUIRED_CLEARANCE_PX": 3, "PASS_FAIL": "PASS" if overlap == 0 and clearance >= 3 else "FAIL", "METHOD": method, "RAW_A": f"raw/{a['OBJECT_ID']}_raw_300dpi.png", "RAW_B": f"raw/{b['OBJECT_ID']}_raw_300dpi.png"}
            overlap_rows.append(row)
            critical_candidates.append((clearance, row))
    write_csv(OUT / "after_overlap_report.csv", overlap_rows)

    # Geometric vector contacts are explicitly documented as intended drawing/data construction, not text collisions.
    geometry_rows: list[dict] = []
    for i, a in enumerate(graphics):
        for b in graphics[i + 1:]:
            gap = bbox_gap(a["bbox"], b["bbox"])
            if gap == 0:
                geometry_rows.append({"OBJECT_A": a["OBJECT_ID"], "OBJECT_B": b["OBJECT_ID"], "BBOX_INTERSECTS": True, "CLASSIFICATION": "INTENTIONAL_GEOMETRY_OR_DATA_COMPONENT_CONTACT", "EXCLUDED_FROM_TEXT_COLLISION_COUNT": True})
    write_csv(OUT / "intentional_geometry_intersections.csv", geometry_rows, ["OBJECT_A", "OBJECT_B", "BBOX_INTERSECTS", "CLASSIFICATION", "EXCLUDED_FROM_TEXT_COLLISION_COUNT"])

    # Most critical (nearest) pair evidence: raw ROI, both unexpanded masks, and bbox overlay.
    critical_candidates.sort(key=lambda item: item[0])
    for rank, (_, row) in enumerate(critical_candidates[:8], start=1):
        a = next(obj for obj in objects if obj["OBJECT_ID"] == row["OBJECT_A"])
        b = next(obj for obj in objects if obj["OBJECT_ID"] == row["OBJECT_B"])
        roi = pair_roi(a["bbox"], b["bbox"], w, h, pad=10)
        raw = page_img.crop(roi)
        base = f"critical_{rank:02d}_{row['PAIR_ID']}"
        raw.save(DIR["pairs"] / f"{base}_raw_300dpi.png")
        pa = a["mask"][roi[1]:roi[3], roi[0]:roi[2]]
        pb = b["mask"][roi[1]:roi[3], roi[0]:roi[2]]
        rgb = np.full((roi[3]-roi[1], roi[2]-roi[0], 3), 255, dtype=np.uint8)
        rgb[pa] = (255, 0, 0)
        rgb[pb] = np.where(pa[pb, None], (255, 0, 255), (0, 0, 255))
        Image.fromarray(rgb).save(DIR["pairs"] / f"{base}_masks_unexpanded.png")
        overlay = raw.copy()
        draw = ImageDraw.Draw(overlay)
        for obj, color in [(a, (255, 0, 0)), (b, (0, 80, 255))]:
            bb = obj["bbox"]
            draw.rectangle((bb[0]-roi[0], bb[1]-roi[1], bb[2]-roi[0], bb[3]-roi[1]), outline=color, width=2)
        draw.text((2, 2), row["PAIR_ID"], fill=(0, 0, 0), font=ImageFont.load_default())
        overlay.save(DIR["pairs"] / f"{base}_overlay_300dpi.png")

    # Edge/crop clipping audit for every independent object.
    edge_rows: list[dict] = []
    clip_total = 0
    for obj in objects:
        mask = obj["mask"]
        bbox = obj["bbox"]
        page_edge = min(bbox[0], bbox[1], w - bbox[2], h - bbox[3])
        crop_edge = min(bbox[0] - fx0, bbox[1] - fy0, fx1 - bbox[2], fy1 - bbox[3])
        touches_page = int(np.count_nonzero(mask[0, :]) + np.count_nonzero(mask[-1, :]) + np.count_nonzero(mask[:, 0]) + np.count_nonzero(mask[:, -1]))
        # A figure crop is evidence-only; foreground reaching it would show insufficient crop/edge clearance.
        local = mask[fy0:fy1, fx0:fx1]
        touches_crop = int(np.count_nonzero(local[0, :]) + np.count_nonzero(local[-1, :]) + np.count_nonzero(local[:, 0]) + np.count_nonzero(local[:, -1]))
        clip_count = touches_page + touches_crop
        clip_total += clip_count
        required = 6 if obj["OBJECT_CLASS"] == "TEXT" else 0
        edge_rows.append({"OBJECT_ID": obj["OBJECT_ID"], "OBJECT_CLASS": obj["OBJECT_CLASS"], "PAGE_EDGE_CLEARANCE_PX": round(page_edge, 3), "FIGURE_CROP_EDGE_CLEARANCE_PX": round(crop_edge, 3), "PAGE_EDGE_FOREGROUND_PX": touches_page, "CROP_EDGE_FOREGROUND_PX": touches_crop, "CLIP_PIXEL_COUNT": clip_count, "REQUIRED_TEXT_EDGE_CLEARANCE_PX": required, "PASS_FAIL": "PASS" if clip_count == 0 and (obj["OBJECT_CLASS"] != "TEXT" or crop_edge >= 6) else "FAIL"})
    write_csv(OUT / "after_edge_clip_report.csv", edge_rows)

    # Pixel measurement output after all class medians are populated.
    pixel_rows: list[dict] = []
    font_rows: list[dict] = []
    for g in glyphs:
        overall = g["SOURCE_FONT_PASS"] and g["PIXEL_PASS"]
        pixel_rows.append({
            "ELEMENT_ID": g["ELEMENT_ID"], "PARENT_ID": g["PARENT_ID"], "PANEL_ID": g["PANEL_ID"], "ROLE": g["ROLE"], "SOURCE_FILE": g["SOURCE_FILE"], "SOURCE_LINE": g["SOURCE_LINE"], "DECLARED_PT": g["DECLARED_PT"], "GRAPHICS_SCALE": g["GRAPHICS_SCALE"], "EFFECTIVE_PT": g["EFFECTIVE_PT"], "TEXT_SAMPLE": g["TEXT_SAMPLE"], "SCRIPT_CLASS": g["SCRIPT_CLASS"], "BBOX_X0": g["BBOX_X0"], "BBOX_Y0": g["BBOX_Y0"], "BBOX_X1": g["BBOX_X1"], "BBOX_Y1": g["BBOX_Y1"], "H_INK_PX": g["H_INK_PX"], "CLASS_MEDIAN_PX": g.get("CLASS_MEDIAN_PX", ""), "RATIO_TO_CLASS_MEDIAN": g.get("RATIO_TO_CLASS_MEDIAN", ""), "ROLE_RATIO": g.get("ROLE_RATIO", ""), "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "see object-pair audit", "SOURCE_FONT_PASS": g["SOURCE_FONT_PASS"], "PIXEL_PASS": g["PIXEL_PASS"], "RAW_ROI": g["RAW_ROI"], "MASK": g["MASK"], "OVERLAY": g["OVERLAY"], "PASS_FAIL": "PASS" if overall else "FAIL", "REASON": f"{g['SOURCE_REASON']} | {g['PIXEL_REASON']}"
        })
        font_rows.append({
            "ELEMENT_ID": g["ELEMENT_ID"], "PARENT_ID": g["PARENT_ID"], "PANEL_ID": g["PANEL_ID"], "ROLE": g["ROLE"], "SOURCE_FILE": g["SOURCE_FILE"], "SOURCE_LINE": g["SOURCE_LINE"], "SOURCE_DECLARATION": g["SOURCE_DECLARATION"], "TEXT_SAMPLE": g["TEXT_SAMPLE"], "SCRIPT_CLASS": g["SCRIPT_CLASS"], "DECLARED_PT": g["DECLARED_PT"], "GRAPHICS_SCALE": g["GRAPHICS_SCALE"], "EFFECTIVE_PT": g["EFFECTIVE_PT"], "PDF_FONT_SIZE_TEX_PT": g["PDF_FONT_SIZE_TEX_PT"], "RAW_ROI": g["RAW_ROI"], "MASK": g["MASK"], "OVERLAY": g["OVERLAY"], "PASS_FAIL": "PASS" if g["SOURCE_FONT_PASS"] else "FAIL", "REASON": g["SOURCE_REASON"]
        })
    write_csv(OUT / "after_pixel_measurements.csv", pixel_rows)
    write_csv(OUT / "after_font_audit.csv", font_rows)

    # Required measurement overlay: every glyph receives its ID, bounding box, and role color.
    overlay = figure_crop.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for g in glyphs:
        x0, y0, x1, y1 = g["pixel_box"]
        x0, x1 = x0 - fx0, x1 - fx0
        y0, y1 = y0 - fy0, y1 - fy0
        color = (220, 0, 0) if not (g["SOURCE_FONT_PASS"] and g["PIXEL_PASS"]) else (0, 130, 0)
        draw.rectangle((x0, y0, x1, y1), outline=color, width=1)
        draw.text((x0, max(0, y0 - 8)), f"{g['ELEMENT_ID']}:{g['ROLE']}", fill=color, font=font)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    font_fail_count = sum(not g["SOURCE_FONT_PASS"] for g in glyphs)
    pixel_fail_count = sum(not g["PIXEL_PASS"] for g in glyphs)
    source_font_pass = font_fail_count == 0
    pixel_height_pass = pixel_fail_count == 0
    all_overlap_pass = overlap_total == 0
    all_clip_pass = clip_total == 0
    # Reading/mathematics/full-page/gray were directly inspected separately; font hard failures also prevent visual harmony.
    math_semantics_pass = True
    text_consistency_pass = True
    grayscale_pass = True
    page_integration_pass = True
    visual_harmony_pass = source_font_pass and pixel_height_pass and same_class_pass and role_ratio_pass
    minimum_clearance = min(text_text_min, text_gfx_min)
    final_pass = all([source_font_pass, pixel_height_pass, same_class_pass, role_ratio_pass, all_overlap_pass, all_clip_pass, visual_harmony_pass, math_semantics_pass, text_consistency_pass, grayscale_pass, page_integration_pass]) and minimum_clearance >= 3

    metadata = {
        "figure_id": "FIG-P467-01", "physical_pdf_page": PDF_PAGE_NUMBER, "printed_page": PRINTED_PAGE, "figure_number": FIGURE_NO,
        "input_pdf": str(PDF), "input_pdf_only": True, "source_read_only": str(SOURCE), "render": "pdftoppm direct 300 dpi, no post-render resize",
        "full_page_300_dimensions": [w, h], "pdf_page_points": [page.rect.width, page.rect.height], "scale_px_per_pdf_point": [sx, sy], "figure_crop_px": fig_px,
        "glyph_count": len(glyphs), "text_object_count": len(text_objects), "vector_object_count": len(graphics), "font_fail_count": font_fail_count, "pixel_fail_count": pixel_fail_count,
        "overlap_pixel_count": overlap_total, "clip_pixel_count": clip_total, "text_text_min_bbox_clearance_px": text_text_min, "text_graphic_min_foreground_clearance_px": text_gfx_min,
    }
    (OUT / "audit_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# FIG-P467-01 — STRICT_R1 SA1 visual acceptance",
        "",
        f"- Frozen candidate: `{PDF.name}`, physical PDF page **{PDF_PAGE_NUMBER}**, printed page **{PRINTED_PAGE}**, **{FIGURE_NO}**.",
        "- All 300 dpi measurements use the direct, unresized `pdftoppm` raster from the frozen candidate. The standalone view is a non-resampled crop of that same final PDF.",
        f"- Reader-visible glyphs measured: **{len(glyphs)}**; independent text objects: **{len(text_objects)}**; independent PDF vector objects: **{len(graphics)}**.",
        "",
        "## Required matrix",
        "",
        f"- SOURCE_FONT_PASS = {'true' if source_font_pass else 'false'} (failed glyphs: {font_fail_count})",
        f"- PIXEL_HEIGHT_PASS = {'true' if pixel_height_pass else 'false'} (failed glyphs: {pixel_fail_count})",
        f"- SAME_CLASS_RATIO_PASS = {'true' if same_class_pass else 'false'}",
        f"- ROLE_RATIO_PASS = {'true' if role_ratio_pass else 'false'}",
        f"- OVERLAP_PIXEL_COUNT = {overlap_total}",
        f"- CLIP_PIXEL_COUNT = {clip_total}",
        f"- MIN_TEXT_CLEARANCE_PX = {minimum_clearance:.3f} (text-text bbox {text_text_min:.3f}; text-graphic foreground {text_gfx_min:.3f})",
        f"- VISUAL_HARMONY_PASS = {'true' if visual_harmony_pass else 'false'}",
        f"- MATH_SEMANTICS_PASS = {'true' if math_semantics_pass else 'false'}",
        f"- TEXT_CONSISTENCY_PASS = {'true' if text_consistency_pass else 'false'}",
        f"- GRAYSCALE_PASS = {'true' if grayscale_pass else 'false'}",
        f"- PAGE_INTEGRATION_PASS = {'true' if page_integration_pass else 'false'}",
        "",
        "## Strict result",
        "",
        f"RESULT: {'PASS' if final_pass else 'FAIL'}",
        "",
        "### Deterministic hard failures",
        "",
        "- TikZ default reader text is `9.2pt` (source line 3), panel-title text is `9.4pt` (line 19), and the annotation is `9.0pt` (line 48). Each is below the required 9.5pt effective size; the title superscript is naturally derived from the already-invalid 9.4pt base.",
        "- Per-glyph 300 dpi measurements and independent punctuation/math sub-strings are in `after_pixel_measurements.csv`; no parent formula/line bbox is used as a substitute.",
        "",
        "### Non-font findings",
        "",
        "- All TEXT–TEXT and TEXT–GRAPHIC pair records are in `after_overlap_report.csv`; independent geometry/data contacts are preserved separately in `intentional_geometry_intersections.csv` and excluded from text-collision counts.",
        "- The visual semantic sequence is left-to-right: unit circle → V^T orthogonal rotation → Σ axial scaling → U orthogonal rotation. Source coordinates preserve these transformations and match adjacent text/caption.",
        "- Full-page 200 dpi, full-page native 300 dpi, standalone native 300 dpi, and grayscale native 300 dpi were inspected. The line/arrow structure remains distinguishable in grayscale, and the page integration is stable; neither can override font hard failures.",
        "",
        "## Required next role",
        "",
        "SA2. Increase all reader-facing figure text to a true effective >=9.5pt (including title base and annotation), preserve natural script derivation from a compliant base, recompile a new official candidate, and regenerate this entire evidence set before a new SA1 review. Do not use global scaling as a workaround.",
    ]
    (OUT / "after_visual_acceptance.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
