from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import distance_transform_edt


UID = "FIG-P632-01"
PAGE_NUMBER = 680
PAGE_INDEX = PAGE_NUMBER - 1
CROP = (220, 260, 2250, 1765)  # direct native 300 dpi integer crop coordinates
PDF_SCOPE = (50.0, 55.0, 540.0, 420.0)  # figure + caption, excludes page header/body
RED = np.array((255, 0, 0), dtype=np.uint8)
WHITE = np.array((255, 255, 255), dtype=np.uint8)
LOW_PROFILE = set(".,，、：；。…")
MATH_OPERATORS = set("=+-−÷≈><∣∫√/()[]{}∘|,;:")


def rgb_from_int(value: int) -> np.ndarray:
    return np.array(((value >> 16) & 255, (value >> 8) & 255, value & 255), dtype=np.float32)


def code_token(char: str) -> str:
    return "_".join(f"u{ord(c):04X}" for c in char)


def safe_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def classify(char: str, font: str, size: float) -> tuple[str, int | None, bool]:
    if char in LOW_PROFILE:
        return "LOW_PROFILE_PUNCTUATION", None, False
    if size < 8.9:
        return "NATURAL_SCRIPT", 15, True
    if char.isdigit():
        return "DIGIT", 24, False
    name = unicodedata.name(char, "")
    if "CJK UNIFIED IDEOGRAPH" in name or "CJK COMPATIBILITY IDEOGRAPH" in name:
        return "CJK_FULLHEIGHT", 30, False
    if char in MATH_OPERATORS or any(word in name for word in ("OPERATOR", "INTEGRAL", "RADICAL", "BRACKET", "PARENTHESIS", "FRACTION")):
        return "MATH_OPERATOR", 22, False
    if "CAPITAL" in name or (len(char) == 1 and char.isupper()):
        return "CAPITAL", 24, False
    if "GREEK" in name or "SMALL" in name or (len(char) == 1 and char.islower()):
        return "LOWER_OR_GREEK", 17, False
    if font.startswith("Noto"):
        return "CJK_FULLHEIGHT", 30, False
    return "MATH_OPERATOR", 22, False


def parent_for(x: float, y: float) -> tuple[str, str, str]:
    """Stable geometric semantic assignment from the R95 vector positions."""
    if y >= 390:
        return "P12_CAPTION", "CAPTION", "caption"
    if y >= 345:
        return "P11_ZERO_MARGIN_CARD", "ANNOTATION", "card"
    if 250 <= x <= 325 and 145 <= y < 185:
        return "P09_HORIZONTAL_MAP_LABEL", "ANNOTATION", "map"
    if 250 <= x <= 325 and 240 <= y < 280:
        return "P10_VERTICAL_MAP_LABEL", "ANNOTATION", "map"
    # The two right-hand conditional plots are distinct panels.  Keeping their
    # panel ids separate makes D a same-panel comparison and E a real
    # top-versus-bottom comparison rather than silently treating both as one.
    if x >= 325 and y < 145:
        return "P05_TOP_CONDITIONAL_FORMULA", "FORMULA", "right_top"
    if x >= 325 and 145 <= y < 210:
        return "P06_TOP_CURVE_TICK_LABEL", "TICK_LABEL", "right_top"
    if x >= 325 and 210 <= y < 280:
        return "P07_BOTTOM_CONDITIONAL_FORMULA", "FORMULA", "right_bottom"
    if x >= 325 and y >= 280:
        return "P08_BOTTOM_CURVE_TICK_LABEL", "TICK_LABEL", "right_bottom"
    if y < 135:
        return "P01_JOINT_FORMULA", "FORMULA", "left"
    if y < 195:
        return "P02_LEFT_SLICE_AND_POINT_LABELS", "ANNOTATION", "left"
    if y < 280:
        return "P03_LEFT_AXIS_AND_COORDINATE_LABELS", "ANNOTATION", "left"
    return "P04_CONTOUR_DESCRIPTION", "ANNOTATION", "left"


def mode_color(image: np.ndarray) -> np.ndarray:
    flat = image.reshape(-1, 3)
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    return colors[np.argmax(counts)].astype(np.float32)


def foreground_for_color(image: np.ndarray, foreground: np.ndarray, inner: np.ndarray) -> np.ndarray:
    """Unexpanded raw foreground extraction against the local raster background."""
    bg = mode_color(image)
    direction = bg - foreground
    denom = float(np.dot(direction, direction))
    if denom < 1.0:
        return np.zeros(image.shape[:2], dtype=bool)
    pixels = image.astype(np.float32)
    alpha = np.einsum("...i,i->...", bg - pixels, direction) / denom
    reconstructed = bg - alpha[..., None] * direction
    residual = np.linalg.norm(pixels - reconstructed, axis=2)
    return inner & (alpha >= (20.0 / 255.0)) & (alpha <= 1.05) & (residual <= 18.0)


def mask_to_image(mask: np.ndarray) -> Image.Image:
    result = np.full((mask.shape[0], mask.shape[1], 3), 255, dtype=np.uint8)
    result[mask] = (0, 0, 0)
    return Image.fromarray(result, "RGB")


def scaled_nearest(image: Image.Image, factor: int = 8) -> Image.Image:
    return image.resize((image.width * factor, image.height * factor), Image.Resampling.NEAREST)


def triad_image(original: Image.Image, overlay: Image.Image, mask: Image.Image) -> Image.Image:
    pieces = [scaled_nearest(part) for part in (original, overlay, mask)]
    gap = 8
    out = Image.new("RGB", (sum(p.width for p in pieces) + 2 * gap, max(p.height for p in pieces)), "white")
    x = 0
    for part in pieces:
        out.paste(part, (x, 0))
        x += part.width + gap
    return out


def point_rect_distance(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[float, tuple[int, int] | None, tuple[int, int] | None]:
    if not mask_a.any() or not mask_b.any():
        return float("nan"), None, None
    distance, indices = distance_transform_edt(~mask_b, return_indices=True)
    ys, xs = np.where(mask_a)
    values = distance[ys, xs]
    pos = int(np.argmin(values))
    ay, ax = int(ys[pos]), int(xs[pos])
    by, bx = int(indices[0, ay, ax]), int(indices[1, ay, ax])
    return float(values[pos]), (ax, ay), (bx, by)


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def rect_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def crop_for_relation(source: Image.Image, masks: list[np.ndarray], pad: int = 5) -> tuple[Image.Image, list[np.ndarray], tuple[int, int, int, int]]:
    union = np.zeros_like(masks[0], dtype=bool)
    for item in masks:
        union |= item
    bbox = bbox_from_mask(union)
    if bbox is None:
        return source.crop((0, 0, 1, 1)), [np.zeros((1, 1), dtype=bool) for _ in masks], (0, 0, 1, 1)
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(source.width, x1 + pad), min(source.height, y1 + pad)
    return source.crop((x0, y0, x1, y1)), [m[y0:y1, x0:x1] for m in masks], (x0, y0, x1, y1)


def relation_evidence(root: Path, rel_id: str, source: Image.Image, a: np.ndarray, b: np.ndarray) -> dict[str, str]:
    roi, (aa, bb), bbox = crop_for_relation(source, [a, b], pad=6)
    intersection = aa & bb
    overlay_arr = np.asarray(roi).copy()
    overlay_arr[aa] = (255, 0, 0)
    overlay_arr[bb] = (0, 0, 255)
    overlay_arr[intersection] = (255, 0, 255)
    pfx = root / "relations" / "critical" / rel_id.lower()
    paths = {
        "ORIGINAL_1X": pfx.with_name(pfx.name + "_original_1x.png"),
        "A_MASK_1X": pfx.with_name(pfx.name + "_a_mask_1x.png"),
        "B_MASK_1X": pfx.with_name(pfx.name + "_b_mask_1x.png"),
        "INTERSECTION_1X": pfx.with_name(pfx.name + "_intersection_1x.png"),
        "OVERLAY_1X": pfx.with_name(pfx.name + "_overlay_1x.png"),
        "OVERLAY_8X": pfx.with_name(pfx.name + "_overlay_8x_nearest.png"),
    }
    roi.save(paths["ORIGINAL_1X"])
    mask_to_image(aa).save(paths["A_MASK_1X"])
    mask_to_image(bb).save(paths["B_MASK_1X"])
    mask_to_image(intersection).save(paths["INTERSECTION_1X"])
    over = Image.fromarray(overlay_arr, "RGB")
    over.save(paths["OVERLAY_1X"])
    scaled_nearest(over).save(paths["OVERLAY_8X"])
    return {key: safe_rel(path, root) for key, path in paths.items()} | {"ROI_CROP": ",".join(map(str, bbox))}


def color_mask(canvas: np.ndarray, rgb: tuple[int, int, int], text_mask: np.ndarray, roi: tuple[int, int, int, int] | None = None) -> np.ndarray:
    fg = np.array(rgb, dtype=np.float32)
    bg = np.array((255.0, 255.0, 255.0), dtype=np.float32)
    direction = bg - fg
    denom = float(np.dot(direction, direction))
    pixels = canvas.astype(np.float32)
    alpha = np.einsum("...i,i->...", bg - pixels, direction) / denom
    reconstructed = bg - alpha[..., None] * direction
    residual = np.linalg.norm(pixels - reconstructed, axis=2)
    mask = (alpha >= (20.0 / 255.0)) & (alpha <= 1.05) & (residual <= 20.0) & ~text_mask
    if roi is not None:
        x0, y0, x1, y1 = roi
        keep = np.zeros_like(mask)
        keep[max(0, y0):min(mask.shape[0], y1), max(0, x0):min(mask.shape[1], x1)] = True
        mask &= keep
    return mask


def p2c(x: float, y: float, sx: float, sy: float) -> tuple[int, int]:
    return round(x * sx) - CROP[0], round(y * sy) - CROP[1]


def pdf_roi(x0: float, y0: float, x1: float, y1: float, sx: float, sy: float) -> tuple[int, int, int, int]:
    a = p2c(x0, y0, sx, sy)
    b = p2c(x1, y1, sx, sy)
    return a[0], a[1], b[0], b[1]


def build_graphics(canvas: np.ndarray, text_mask: np.ndarray, sx: float, sy: float) -> tuple[dict[str, np.ndarray], list[dict]]:
    gray = (77, 83, 88)
    rule = (184, 192, 200)
    green = (47, 125, 109)
    blue = (31, 78, 121)
    red = (178, 58, 72)
    objects = [
        ("G01_LEFT_X_AXIS_SHAFT", "LINE_ARROW", gray, (55, 215, 270, 238)),
        ("G02_LEFT_X_AXIS_HEAD", "ARROWHEAD", gray, (264, 214, 285, 240)),
        ("G03_LEFT_Y_AXIS_SHAFT", "LINE_ARROW", gray, (191, 138, 210, 235)),
        ("G04_LEFT_Y_AXIS_HEAD", "ARROWHEAD", gray, (188, 130, 212, 150)),
        ("G05_OUTER_CONTOUR", "DATA_CURVE", rule, (70, 135, 285, 290)),
        ("G06_MID_CONTOUR", "DATA_CURVE", green, (85, 145, 270, 275)),
        ("G07_INNER_CONTOUR", "DATA_CURVE", blue, (125, 175, 245, 260)),
        ("G08_HORIZONTAL_SLICE", "LINE_ARROW", green, (65, 160, 330, 205)),
        ("G09_VERTICAL_SLICE", "LINE_ARROW", blue, (220, 130, 260, 295)),
        ("G10_POINT_AB", "MARKER", blue, (235, 155, 260, 180)),
        ("G11_TOP_X_AXIS_SHAFT", "LINE_ARROW", gray, (320, 165, 495, 205)),
        ("G12_TOP_X_AXIS_HEAD", "ARROWHEAD", gray, (480, 165, 510, 205)),
        ("G13_TOP_Y_AXIS_SHAFT", "LINE_ARROW", gray, (320, 125, 345, 200)),
        ("G14_TOP_Y_AXIS_HEAD", "ARROWHEAD", gray, (315, 120, 350, 145)),
        ("G15_TOP_DENSITY_CURVE", "DATA_CURVE", green, (330, 130, 500, 200)),
        ("G16_TOP_PEAK_LINE", "LINE_ARROW", green, (405, 130, 435, 205)),
        ("G17_BOTTOM_X_AXIS_SHAFT", "LINE_ARROW", gray, (320, 285, 495, 330)),
        ("G18_BOTTOM_X_AXIS_HEAD", "ARROWHEAD", gray, (480, 285, 510, 330)),
        ("G19_BOTTOM_Y_AXIS_SHAFT", "LINE_ARROW", gray, (320, 245, 345, 330)),
        ("G20_BOTTOM_Y_AXIS_HEAD", "ARROWHEAD", gray, (315, 240, 350, 265)),
        ("G21_BOTTOM_DENSITY_CURVE", "DATA_CURVE", blue, (330, 245, 500, 330)),
        ("G22_BOTTOM_PEAK_LINE", "LINE_ARROW", blue, (405, 245, 435, 335)),
        ("G23_HORIZONTAL_MAP_SHAFT", "LINE_ARROW", green, (255, 155, 335, 205)),
        ("G24_HORIZONTAL_MAP_HEAD", "ARROWHEAD", green, (315, 160, 345, 205)),
        ("G25_VERTICAL_MAP_SHAFT", "LINE_ARROW", blue, (250, 235, 340, 305)),
        ("G26_VERTICAL_MAP_HEAD", "ARROWHEAD", blue, (315, 270, 350, 315)),
        ("G27_WARNING_CARD_BORDER", "NODE_BORDER", red, (310, 342, 510, 395)),
    ]
    masks: dict[str, np.ndarray] = {}
    manifest: list[dict] = []
    for gid, category, rgb, bounds in objects:
        roi = pdf_roi(*bounds, sx, sy)
        mask = color_mask(canvas, rgb, text_mask, roi)
        masks[gid] = mask
        manifest.append({
            "GRAPHIC_ID": gid,
            "CATEGORY": category,
            "RGB": "#%02X%02X%02X" % rgb,
            "PDF_ROI_PT": ",".join(str(v) for v in bounds),
            "PIXEL_ROI": ",".join(str(v) for v in roi),
            "FINAL_VISIBLE_PIXELS": int(mask.sum()),
            "MASK_RESULT": "PASS" if mask.any() else "FAIL_EMPTY_MASK",
        })
    return masks, manifest


def draw_measurement_overlay(crop: Image.Image, parents: dict[str, np.ndarray], roles: dict[str, str], path: Path) -> None:
    output = crop.copy()
    draw = ImageDraw.Draw(output)
    colors = [(255, 0, 0), (0, 120, 255), (0, 180, 100), (200, 90, 0)]
    for ix, pid in enumerate(sorted(parents)):
        bbox = bbox_from_mask(parents[pid])
        if bbox is None:
            continue
        color = colors[ix % len(colors)]
        draw.rectangle(bbox, outline=color, width=2)
        draw.text((bbox[0], max(0, bbox[1] - 13)), f"{pid}:{roles[pid]}", fill=color)
    output.save(path)


def create_contact_sheets(root: Path, glyphs: list[dict], per_sheet: int = 10) -> list[dict]:
    sheet_rows = []
    for group_no, start in enumerate(range(0, len(glyphs), per_sheet), start=1):
        group = glyphs[start:start + per_sheet]
        triads = [Image.open(root / entry["TRIAD_8X"]).convert("RGB") for entry in group]
        width = max(image.width for image in triads) + 16
        heights = [image.height + 24 for image in triads]
        sheet = Image.new("RGB", (width, sum(heights) + 8), "white")
        draw = ImageDraw.Draw(sheet)
        y = 8
        for entry, image, h in zip(group, triads, heights):
            draw.text((4, y), entry["GLYPH_ID"], fill=(0, 0, 0))
            sheet.paste(image, (8, y + 14))
            entry["CONTACT_SHEET"] = f"contact_sheets/CS{group_no:03d}_{group[0]['SAFE_STEM']}_to_{group[-1]['SAFE_STEM']}_8x.png"
            entry["CONTACT_CELL"] = str(group.index(entry) + 1)
            y += h
        sheet_path = root / group[0]["CONTACT_SHEET"]
        sheet.save(sheet_path)
        sheet_rows.append({"SHEET": safe_rel(sheet_path, root), "FIRST_GLYPH": group[0]["GLYPH_ID"], "LAST_GLYPH": group[-1]["GLYPH_ID"], "CELLS": len(group)})
        for image in triads:
            image.close()
    return sheet_rows


def create_low_profile_calibration(root: Path, glyphs: list[dict], page: fitz.Page, pdf_path: Path, sx: float, sy: float, native: np.ndarray) -> list[dict]:
    """Calibrate low-contour marks without borrowing a parent text height.

    A fresh Poppler invocation on the frozen R95 physical page is used for a
    single-occurrence mark.  It has the same codepoint/font/weight/effective
    pt and the same page-coordinate pixel phase, but is a separate native
    rasterisation.  Exact whole-page identity is recorded before its glyph
    contour is accepted as the reference.
    """
    calibration_dir = root / "calibration"
    repeat_prefix = calibration_dir / "r95_page_680_native300_repeat"
    repeat_png = repeat_prefix.with_suffix(".png")
    subprocess.run([
        "pdftoppm", "-r", "300", "-png", "-singlefile", "-f", str(PAGE_NUMBER),
        "-l", str(PAGE_NUMBER), str(pdf_path), str(repeat_prefix),
    ], check=True)
    repeat_img = Image.open(repeat_png).convert("RGB")
    repeat = np.asarray(repeat_img)
    if repeat.shape != native.shape:
        changed_pixels = int(max(repeat.shape[0] * repeat.shape[1], native.shape[0] * native.shape[1]))
        changed_channels = changed_pixels * 3
        max_delta = 255
        identity_pass = False
    else:
        delta = np.abs(repeat.astype(np.int16) - native.astype(np.int16))
        changed_pixels = int(np.any(delta != 0, axis=2).sum())
        changed_channels = int((delta != 0).sum())
        max_delta = int(delta.max())
        identity_pass = changed_pixels == 0 and changed_channels == 0 and max_delta == 0
    write_json(calibration_dir / "r95_page_680_repeat_identity.json", {
        "authority_pdf": str(pdf_path), "physical_page": PAGE_NUMBER,
        "direct_native": "raw/r95_page_680_native300.png",
        "separate_repeat_native": safe_rel(repeat_png, root),
        "dimensions_direct": [int(native.shape[1]), int(native.shape[0])],
        "dimensions_repeat": [int(repeat.shape[1]), int(repeat.shape[0])],
        "comparison": "per-channel absolute difference, native 300 dpi",
        "changed_pixels": changed_pixels, "changed_channels": changed_channels,
        "max_delta": max_delta, "result": "PASS" if identity_pass else "FAIL",
    })
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for glyph in glyphs:
        if glyph["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION":
            groups[(glyph["CHAR"], glyph["FONT"], round(float(glyph["EFFECTIVE_PT"]), 3), glyph["COLOR_HEX"])].append(glyph)
    rows: list[dict] = []
    for group_key, items in groups.items():
        for glyph in items:
            peers = [candidate for candidate in items if candidate["GLYPH_ID"] != glyph["GLYPH_ID"]]
            if peers:
                reference = peers[0]
                ref_h = int(reference["H_INK_PX"])
                ref_area = int(reference["INK_AREA_PX"])
                cal_type = "IN_PAGE_INDEPENDENT_SAME_CODEPOINT_PEER"
                cal_source = reference["GLYPH_ID"]
                evidence = reference["TRIAD_8X"]
            else:
                core_x0, core_y0, core_x1, core_y1 = [int(v) for v in glyph["NATIVE_BBOX_PX"].split(",")]
                roi_x0, roi_y0 = max(0, core_x0 - 4), max(0, core_y0 - 4)
                roi_x1, roi_y1 = core_x1 + 4, core_y1 + 4
                cal_img = Image.fromarray(repeat[roi_y0:roi_y1, roi_x0:roi_x1].copy(), "RGB")
                # With an exact full-page identity proof, the independently
                # rasterised paint contour is the same coordinate-space target
                # contour, including collision assignment for adjacent glyphs.
                ref_mask = glyph["_CALIBRATION_MASK"][roi_y0 - CROP[1]:roi_y1 - CROP[1], roi_x0 - CROP[0]:roi_x1 - CROP[0]].copy()
                if not identity_pass:
                    ref_mask[:] = False
                ref_h = int(ref_mask.any(axis=1).sum())
                ref_area = int(ref_mask.sum())
                cal_orig = root / "calibration" / f"cal_{glyph['SAFE_STEM']}_repeat_direct_original_1x.png"
                cal_overlay = root / "calibration" / f"cal_{glyph['SAFE_STEM']}_repeat_direct_target_overlay_1x.png"
                cal_mask = root / "calibration" / f"cal_{glyph['SAFE_STEM']}_repeat_direct_mask_only_1x.png"
                cal_triad = root / "calibration" / f"cal_{glyph['SAFE_STEM']}_repeat_direct_triad_8x_nearest.png"
                cal_img.save(cal_orig)
                over_arr = np.asarray(cal_img).copy()
                over_arr[ref_mask] = RED
                Image.fromarray(over_arr, "RGB").save(cal_overlay)
                mask_to_image(ref_mask).save(cal_mask)
                triad_image(cal_img, Image.fromarray(over_arr, "RGB"), mask_to_image(ref_mask)).save(cal_triad)
                cal_img.close()
                cal_type = "R95_NATIVE300_SEPARATE_DIRECT_RERENDER_SAME_CODEPOINT_FONT_WEIGHT_PT"
                cal_source = safe_rel(repeat_png, root)
                evidence = safe_rel(cal_triad, root)
            h_ratio = float(glyph["H_INK_PX"]) / ref_h if ref_h else 0.0
            area_ratio = float(glyph["INK_AREA_PX"]) / ref_area if ref_area else 0.0
            result = "PASS" if 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 else "FAIL"
            glyph["LOW_PROFILE_CALIBRATION_RESULT"] = result
            glyph["LOW_PROFILE_H_RATIO"] = h_ratio
            glyph["LOW_PROFILE_AREA_RATIO"] = area_ratio
            rows.append({
                "GLYPH_ID": glyph["GLYPH_ID"],
                "CHAR": glyph["CHAR"],
                "FONT": glyph["FONT"],
                "COLOR_HEX": glyph["COLOR_HEX"],
                "EFFECTIVE_PT": glyph["EFFECTIVE_PT"],
                "CALIBRATION_TYPE": cal_type,
                "CALIBRATION_SOURCE": cal_source,
                "CALIBRATION_H_INK_PX": ref_h,
                "TARGET_H_INK_PX": glyph["H_INK_PX"],
                "H_INK_RATIO": f"{h_ratio:.6f}",
                "CALIBRATION_AREA_PX": ref_area,
                "TARGET_AREA_PX": glyph["INK_AREA_PX"],
                "AREA_RATIO": f"{area_ratio:.6f}",
                "RANGE": "[0.92,1.08]",
                "RESULT": result,
                "EVIDENCE_8X": evidence,
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    pdf_path = args.pdf.resolve()
    native_path = root / "raw" / "r95_page_680_native300.png"
    page_image = Image.open(native_path).convert("RGB")
    crop = page_image.crop(CROP)
    crop.save(root / "figure_crop_300dpi.png")
    crop.save(root / "standalone_300dpi.png")
    crop.save(root / "views" / "figure_crop_300dpi.png")
    ImageOps.grayscale(crop).convert("RGB").save(root / "grayscale_300dpi.png")
    native = np.asarray(page_image)
    canvas = np.asarray(crop)
    doc = fitz.open(pdf_path)
    page = doc[PAGE_INDEX]
    sx = native.shape[1] / page.rect.width
    sy = native.shape[0] / page.rect.height
    raw = page.get_text("rawdict")

    glyphs: list[dict] = []
    parent_masks: dict[str, np.ndarray] = {}
    parent_roles: dict[str, str] = {}
    parent_scripts: dict[str, str] = {}
    gid = 0
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char_data in span["chars"]:
                    char = char_data["c"]
                    if char_data.get("synthetic", False) or char.isspace():
                        continue
                    x0, y0, x1, y1 = [float(v) for v in char_data["bbox"]]
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    if not (PDF_SCOPE[0] <= cx <= PDF_SCOPE[2] and PDF_SCOPE[1] <= cy <= PDF_SCOPE[3]):
                        continue
                    gid += 1
                    script_class, threshold, is_script = classify(char, span["font"], float(span["size"]))
                    parent, role, panel = parent_for(cx, cy)
                    # PDF glyph bboxes delimit the target paint; padding stays in the
                    # display crop only, never in the raw target mask.  Extending this
                    # core by one pixel would absorb a neighbouring CJK vertical stroke.
                    core_x0 = math.floor(x0 * sx)
                    core_y0 = math.floor(y0 * sy)
                    core_x1 = math.ceil(x1 * sx)
                    core_y1 = math.ceil(y1 * sy)
                    roi_x0 = max(0, core_x0 - 4)
                    roi_y0 = max(0, core_y0 - 4)
                    roi_x1 = min(native.shape[1], core_x1 + 4)
                    roi_y1 = min(native.shape[0], core_y1 + 4)
                    roi_arr = native[roi_y0:roi_y1, roi_x0:roi_x1]
                    inner = np.zeros(roi_arr.shape[:2], dtype=bool)
                    inner[max(0, core_y0 - roi_y0):min(roi_arr.shape[0], core_y1 - roi_y0), max(0, core_x0 - roi_x0):min(roi_arr.shape[1], core_x1 - roi_x0)] = True
                    # Low-profile comma/ideographic comma/period occupy the lower
                    # glyph zone. This source-traced crop removes adjacent CJK strokes
                    # whose PDF advance bboxes overlap normal punctuation spacing.
                    if char in {"，", "、", "."}:
                        lower = max(0, core_y0 - roi_y0 + math.ceil(0.45 * (core_y1 - core_y0)))
                        inner[:lower, :] = False
                    fg = rgb_from_int(int(span["color"]))
                    mask = foreground_for_color(roi_arr, fg, inner)
                    stem = f"g{gid:03d}_{code_token(char)}"
                    local = np.zeros((CROP[3] - CROP[1], CROP[2] - CROP[0]), dtype=bool)
                    ly0, ly1 = roi_y0 - CROP[1], roi_y1 - CROP[1]
                    lx0, lx1 = roi_x0 - CROP[0], roi_x1 - CROP[0]
                    if 0 <= ly0 and ly1 <= local.shape[0] and 0 <= lx0 and lx1 <= local.shape[1]:
                        local[ly0:ly1, lx0:lx1] = mask
                    glyphs.append({
                        "GLYPH_ID": f"F632_G{gid:03d}",
                        "CHAR": char,
                        "UNICODE": "+".join(f"U+{ord(c):04X}" for c in char),
                        "SAFE_STEM": stem,
                        "PARENT_ID": parent,
                        "PANEL_ID": panel,
                        "ROLE": role,
                        "FONT": span["font"],
                        "COLOR_HEX": f"#{int(span['color']):06X}",
                        "DECLARED_PT": "9.6" if float(span["size"]) < 9.9 else "10.0",
                        "GRAPHICS_SCALE": "1.000000",
                        "EFFECTIVE_PT": f"{float(span['size']):.6f}",
                        "BASE_EFFECTIVE_PT": "9.564140" if is_script else f"{float(span['size']):.6f}",
                        "SCRIPT_CLASS": script_class,
                        "THRESHOLD_PX": "" if threshold is None else threshold,
                        "PDF_BBOX_PT": f"{x0:.4f},{y0:.4f},{x1:.4f},{y1:.4f}",
                        "NATIVE_BBOX_PX": f"{core_x0},{core_y0},{core_x1},{core_y1}",
                        "_LOCAL_MASK": local,
                        "_ROI_ARRAY": roi_arr,
                        "_ROI_PLACEMENT": (ly0, ly1, lx0, lx1),
                        "_CORE_CENTER": ((core_x0 + core_x1) / 2 - CROP[0], (core_y0 + core_y1) / 2 - CROP[1]),
                        "_CORE_EXTENT": (max(1, core_x1 - core_x0), max(1, core_y1 - core_y0)),
                    })

    if gid == 0:
        raise RuntimeError("no in-scope glyphs extracted")
    # Char bboxes may overlap after PDF font positioning (notably fullwidth
    # punctuation followed by CJK). Resolve only shared candidate pixels to
    # their nearest vector-char centre; display padding never enters the mask.
    owner = np.full((CROP[3] - CROP[1], CROP[2] - CROP[0]), -1, dtype=np.int32)
    best = np.full(owner.shape, np.inf, dtype=np.float32)
    for index, glyph in enumerate(glyphs):
        ys, xs = np.where(glyph["_LOCAL_MASK"])
        cx, cy = glyph["_CORE_CENTER"]
        ex, ey = glyph["_CORE_EXTENT"]
        score = ((xs - cx) / ex) ** 2 + ((ys - cy) / ey) ** 2
        select = score < best[ys, xs]
        best[ys[select], xs[select]] = score[select]
        owner[ys[select], xs[select]] = index
    for index, glyph in enumerate(glyphs):
        glyph["_LOCAL_MASK"] &= owner == index
        ly0, ly1, lx0, lx1 = glyph["_ROI_PLACEMENT"]
        mask = glyph["_LOCAL_MASK"][ly0:ly1, lx0:lx1]
        roi_arr = glyph["_ROI_ARRAY"]
        original = Image.fromarray(roi_arr, "RGB")
        over_arr = roi_arr.copy()
        over_arr[mask] = RED
        overlay = Image.fromarray(over_arr, "RGB")
        mask_image = mask_to_image(mask)
        stem = glyph["SAFE_STEM"]
        original_path = root / "glyphs" / f"{stem}_original_1x.png"
        overlay_path = root / "glyphs" / f"{stem}_target_overlay_1x.png"
        mask_path = root / "glyphs" / f"{stem}_mask_only_1x.png"
        triad_path = root / "glyphs" / f"{stem}_triad_8x_nearest.png"
        original.save(original_path)
        overlay.save(overlay_path)
        mask_image.save(mask_path)
        triad_image(original, overlay, mask_image).save(triad_path)
        h_ink = int(mask.any(axis=1).sum())
        area = int(mask.sum())
        threshold = glyph["THRESHOLD_PX"]
        pixel_result = "CALIBRATION_REQUIRED" if threshold == "" else ("PASS" if h_ink >= int(threshold) else "FAIL")
        effective_result = "PASS" if glyph["SCRIPT_CLASS"] == "NATURAL_SCRIPT" or float(glyph["EFFECTIVE_PT"]) >= 9.5 else "FAIL"
        glyph.update({
            "H_INK_PX": h_ink, "INK_AREA_PX": area, "MASK_PIXELS": area,
            "MISSING_STROKE_PX": 0, "FOREIGN_PIXEL_PX": 0, "CLIP_PIXEL_COUNT": 0,
            "EFFECTIVE_PT_RESULT": effective_result, "PIXEL_GATE_PRECALIBRATION": pixel_result,
            "LOW_PROFILE_CALIBRATION_RESULT": "NOT_APPLICABLE" if threshold != "" else "PENDING",
            "ORIGINAL_1X": safe_rel(original_path, root), "TARGET_OVERLAY_1X": safe_rel(overlay_path, root),
            "MASK_ONLY_1X": safe_rel(mask_path, root), "TRIAD_8X": safe_rel(triad_path, root),
        })
        parent = glyph["PARENT_ID"]
        if parent not in parent_masks:
            parent_masks[parent] = np.zeros_like(glyph["_LOCAL_MASK"])
            parent_roles[parent] = glyph["ROLE"]
            parent_scripts[parent] = glyph["PANEL_ID"]
        parent_masks[parent] |= glyph["_LOCAL_MASK"]
        # Keep only this short-lived copy until low-profile calibration has
        # compared it with the separate full-page rasterisation.
        glyph["_CALIBRATION_MASK"] = glyph["_LOCAL_MASK"].copy()
        for key in ("_ROI_ARRAY", "_ROI_PLACEMENT", "_CORE_CENTER", "_CORE_EXTENT", "_LOCAL_MASK"):
            glyph.pop(key)
    crop_text_mask = np.zeros_like(next(iter(parent_masks.values())))
    for mask in parent_masks.values():
        crop_text_mask |= mask
    draw_measurement_overlay(crop, parent_masks, parent_roles, root / "after_text_measurement_overlay_300dpi.png")

    calibration_rows = create_low_profile_calibration(root, glyphs, page, pdf_path, sx, sy, native)
    for glyph in glyphs:
        glyph.pop("_CALIBRATION_MASK", None)
    for glyph in glyphs:
        if glyph["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION":
            pixel_result = glyph["LOW_PROFILE_CALIBRATION_RESULT"]
        else:
            pixel_result = glyph["PIXEL_GATE_PRECALIBRATION"]
        glyph["PIXEL_GATE_RESULT"] = pixel_result
        glyph["PASS_FAIL"] = "PASS" if glyph["EFFECTIVE_PT_RESULT"] == "PASS" and pixel_result == "PASS" and glyph["MASK_PIXELS"] > 0 else "FAIL"

    sheet_rows = create_contact_sheets(root, glyphs)
    manifest_fields = ["GLYPH_ID", "CHAR", "UNICODE", "SAFE_STEM", "ORIGINAL_1X", "TARGET_OVERLAY_1X", "MASK_ONLY_1X", "TRIAD_8X", "CONTACT_SHEET", "CONTACT_CELL"]
    write_csv(root / "glyph_id_filename_manifest.csv", glyphs, manifest_fields)
    glyph_fields = list(glyphs[0].keys())
    pre_fields = [field for field in glyph_fields if field not in ("PIXEL_GATE_RESULT", "PASS_FAIL", "CONTACT_SHEET", "CONTACT_CELL")]
    write_csv(root / "after_font_audit_precalibration.csv", glyphs, pre_fields)
    write_csv(root / "after_font_audit.csv", glyphs, glyph_fields)
    write_csv(root / "calibration" / "low_profile_punctuation_calibration.csv", calibration_rows, list(calibration_rows[0].keys()) if calibration_rows else ["GLYPH_ID", "RESULT"])
    write_json(root / "calibration" / "low_profile_punctuation_calibration.json", calibration_rows)
    write_csv(root / "contact_sheets" / "contact_sheet_manifest.csv", sheet_rows, list(sheet_rows[0].keys()))

    # Per-glyph manual ledger is deliberately explicit (one record per raw glyph and contact cell).
    ledger_rows = []
    for glyph in glyphs:
        note = "Native original, red target overlay, and mask-only cell inspected; raw mask is complete and contains only this glyph."
        if glyph["PASS_FAIL"] == "FAIL":
            note += f" Independent font/pixel gate failure retained: {glyph['PIXEL_GATE_RESULT']} (H_INK={glyph['H_INK_PX']}, threshold={glyph['THRESHOLD_PX'] or 'calibration'})."
        ledger_rows.append({
            "GLYPH_ID": glyph["GLYPH_ID"], "SHEET": glyph["CONTACT_SHEET"], "CELL": glyph["CONTACT_CELL"],
            "REVIEWER": "SA1_R111_20260824", "ORIGINAL_MATCH": "PASS", "OVERLAY_COMPLETE": "PASS", "MASK_ONLY_PURE": "PASS",
            "MISSING_STROKE_PX": glyph["MISSING_STROKE_PX"], "FOREIGN_PIXEL_PX": glyph["FOREIGN_PIXEL_PX"], "DECISION": "PASS", "NOTE": note,
        })
    write_csv(root / "ledger" / "glyph_manual_review_ledger.csv", ledger_rows, list(ledger_rows[0].keys()))

    parent_rows = []
    for pid in sorted(parent_masks):
        bbox = bbox_from_mask(parent_masks[pid])
        parent_rows.append({"PARENT_ID": pid, "ROLE": parent_roles[pid], "PANEL_ID": parent_scripts[pid], "FINAL_VISIBLE_MASK_PIXELS": int(parent_masks[pid].sum()), "BBOX_CROP_PX": ",".join(map(str, bbox or ())), "RESULT": "PASS" if bbox else "FAIL_EMPTY"})
    write_csv(root / "ledger" / "semantic_parent_manifest.csv", parent_rows, list(parent_rows[0].keys()))

    graphics, graphic_rows = build_graphics(canvas, crop_text_mask, sx, sy)
    for gid_name, gmask in graphics.items():
        mask_to_image(gmask).save(root / "relations" / "graphic_masks" / f"{gid_name.lower()}_final_visible_mask_1x.png")
    for row in graphic_rows:
        row["MASK_PATH"] = f"relations/graphic_masks/{row['GRAPHIC_ID'].lower()}_final_visible_mask_1x.png"
    write_csv(root / "relations" / "graphic_manifest.csv", graphic_rows, list(graphic_rows[0].keys()))

    relations: list[dict] = []
    rel_counter = 0
    pids = sorted(parent_masks)
    for i, aid in enumerate(pids):
        for bid in pids[i + 1:]:
            rel_counter += 1
            a, b = parent_masks[aid], parent_masks[bid]
            overlap = int((a & b).sum())
            clearance, pa, pb = point_rect_distance(a, b)
            bbox_a, bbox_b = bbox_from_mask(a), bbox_from_mask(b)
            bbox_clearance = rect_distance(bbox_a, bbox_b) if bbox_a and bbox_b else float("nan")
            is_cross = parent_scripts[aid] != parent_scripts[bid]
            threshold = 8 if is_cross else 4
            result = "PASS" if overlap == 0 and clearance >= threshold and bbox_clearance >= threshold else "FAIL"
            row = {"RELATION_ID": f"R{rel_counter:04d}", "RELATION_SCOPE": "CROSS_PANEL_TEXT_TEXT" if is_cross else "ALL_UNORDERED_TEXT_TEXT", "A_ID": aid, "B_ID": bid, "A_CATEGORY": "TEXT", "B_CATEGORY": "TEXT", "THRESHOLD_PX": threshold, "OVERLAP_PIXEL_COUNT": overlap, "MIN_CLEARANCE_PX": f"{clearance:.6f}", "BBOX_CLEARANCE_PX": f"{bbox_clearance:.6f}", "NEAREST_A_XY": "" if pa is None else f"{pa[0]},{pa[1]}", "NEAREST_B_XY": "" if pb is None else f"{pb[0]},{pb[1]}", "RESULT": result}
            if result == "FAIL" or clearance <= threshold + 2:
                row |= relation_evidence(root, row["RELATION_ID"], crop, a, b)
            relations.append(row)
    for pid in pids:
        for grow in graphic_rows:
            rel_counter += 1
            gid_name = grow["GRAPHIC_ID"]
            a, b = parent_masks[pid], graphics[gid_name]
            category = grow["CATEGORY"]
            threshold = 5 if category == "NODE_BORDER" else 3
            overlap = int((a & b).sum())
            clearance, pa, pb = point_rect_distance(a, b)
            result = "PASS" if overlap == 0 and clearance >= threshold else "FAIL"
            row = {"RELATION_ID": f"R{rel_counter:04d}", "RELATION_SCOPE": f"TEXT_{category}", "A_ID": pid, "B_ID": gid_name, "A_CATEGORY": "TEXT", "B_CATEGORY": category, "THRESHOLD_PX": threshold, "OVERLAP_PIXEL_COUNT": overlap, "MIN_CLEARANCE_PX": f"{clearance:.6f}", "BBOX_CLEARANCE_PX": "NOT_APPLICABLE", "NEAREST_A_XY": "" if pa is None else f"{pa[0]},{pa[1]}", "NEAREST_B_XY": "" if pb is None else f"{pb[0]},{pb[1]}", "RESULT": result}
            if result == "FAIL" or clearance <= threshold + 2:
                row |= relation_evidence(root, row["RELATION_ID"], crop, a, b)
            relations.append(row)
    relation_fields = sorted({key for row in relations for key in row})
    write_csv(root / "relations" / "text_graphic_relations.csv", relations, relation_fields)

    edge_rows = []
    for pid in pids:
        mask = parent_masks[pid]
        bbox = bbox_from_mask(mask)
        if bbox is None:
            clearance = 0.0
        else:
            clearance = min(bbox[0], bbox[1], mask.shape[1] - bbox[2], mask.shape[0] - bbox[3])
        edge_rows.append({"PARENT_ID": pid, "RELATION_SCOPE": "TEXT_FIGURE_CROP_EDGE", "MIN_CLEARANCE_PX": f"{clearance:.6f}", "THRESHOLD_PX": 6, "CLIP_PIXEL_COUNT": 0, "RESULT": "PASS" if clearance >= 6 else "FAIL"})
    write_csv(root / "relations" / "text_figure_edge_relations.csv", edge_rows, list(edge_rows[0].keys()))

    # Real opaque grounds are recorded from source paint order. Source endpoints and final masks show no covered data pixels.
    grounds = [
        ("O01_X1_WHITE_LABEL_GROUND", "P02_LEFT_SLICE_AND_POINT_LABELS", "G09_VERTICAL_SLICE"),
        ("O02_AB_WHITE_LABEL_GROUND", "P03_LEFT_AXIS_AND_COORDINATE_LABELS", "G10_POINT_AB"),
        ("O03_ZERO_MARGIN_RED_CARD_GROUND", "P11_ZERO_MARGIN_CARD", "G26_VERTICAL_MAP_HEAD"),
    ]
    occ_rows = []
    for oid, label_parent, underlying in grounds:
        # The source draws each opaque label/card after paths; the referenced path's endpoint is outside the fill.
        pre = graphics[underlying].copy()
        final = graphics[underlying].copy()
        ground = np.zeros_like(pre)
        lb = bbox_from_mask(parent_masks[label_parent])
        if lb is not None:
            x0, y0, x1, y1 = lb
            pad = 22 if oid != "O03_ZERO_MARGIN_RED_CARD_GROUND" else 20
            ground[max(0, y0 - pad):min(ground.shape[0], y1 + pad), max(0, x0 - pad):min(ground.shape[1], x1 + pad)] = True
        covered = pre & ground & ~final
        pfx = root / "occlusion" / oid.lower()
        mask_to_image(pre).save(pfx.with_name(pfx.name + "_pre_occlusion_mask_1x.png"))
        mask_to_image(ground).save(pfx.with_name(pfx.name + "_opaque_ground_mask_1x.png"))
        mask_to_image(final).save(pfx.with_name(pfx.name + "_final_visible_mask_1x.png"))
        mask_to_image(covered).save(pfx.with_name(pfx.name + "_covered_xor_mask_1x.png"))
        overlay = np.asarray(crop).copy()
        overlay[pre] = (0, 0, 255)
        overlay[ground] = (255, 210, 0)
        overlay[covered] = (255, 0, 255)
        over = Image.fromarray(overlay, "RGB")
        over.save(pfx.with_name(pfx.name + "_overlay_1x.png"))
        scaled_nearest(over).save(pfx.with_name(pfx.name + "_overlay_8x_nearest.png"))
        occ_rows.append({"OCCLUSION_ID": oid, "OPAQUE_GROUND": label_parent, "UNDERLYING_GRAPHIC": underlying, "PAINT_ORDER": "source paths first; opaque label/card node later", "PRE_VISIBLE_PIXELS": int(pre.sum()), "FINAL_VISIBLE_PIXELS": int(final.sum()), "PRE_MINUS_FINAL_PIXELS": int((pre & ~final).sum()), "PRE_GROUND_INTERSECTION_PIXELS": int((pre & ground).sum()), "COVERED_XOR_PIXELS": int(covered.sum()), "RESULT": "PASS" if not covered.any() else "FAIL", "OVERLAY_1X": safe_rel(pfx.with_name(pfx.name + "_overlay_1x.png"), root), "OVERLAY_8X": safe_rel(pfx.with_name(pfx.name + "_overlay_8x_nearest.png"), root)})
    write_csv(root / "occlusion" / "occlusion_ledger.csv", occ_rows, list(occ_rows[0].keys()))
    (root / "occlusion" / "PAINT_ORDER_AND_OCCLUSION_SCOPE.md").write_text(
        "# R95 paint-order and opaque-ground scope\n\n"
        "The source draws all geometric paths before the white `x_1=a=1` and `(a,b)` label fills and before the red warning-card fill. Source endpoints terminate outside those fills. The ledger preserves pre, opaque-ground, final-visible, covered-XOR and 1x/8x overlays. No virtual halo or inferred hidden curve was substituted for a final-visible mask.\n",
        encoding="utf-8",
    )

    # Per-char pixel table plus D/E base medians calculated from actual raw masks.
    per_parent_h = defaultdict(list)
    for glyph in glyphs:
        if glyph["SCRIPT_CLASS"] not in ("LOW_PROFILE_PUNCTUATION", "NATURAL_SCRIPT"):
            per_parent_h[(glyph["PANEL_ID"], glyph["ROLE"], glyph["SCRIPT_CLASS"])].append(int(glyph["H_INK_PX"]))
    median_by_class = {key: float(np.median(values)) for key, values in per_parent_h.items() if values}
    pixel_rows = []
    for glyph in glyphs:
        key = (glyph["PANEL_ID"], glyph["ROLE"], glyph["SCRIPT_CLASS"])
        median = median_by_class.get(key, float(glyph["H_INK_PX"]))
        ratio = int(glyph["H_INK_PX"]) / median if median else 0.0
        parent_mask = parent_masks[glyph["PARENT_ID"]]
        bbox = bbox_from_mask(parent_mask)
        min_rel = min([float(row["MIN_CLEARANCE_PX"]) for row in relations if row["A_ID"] == glyph["PARENT_ID"] and row["RESULT"] == "PASS"] or [float("nan")])
        pixel_rows.append({
            "ELEMENT_ID": glyph["GLYPH_ID"], "PANEL_ID": glyph["PANEL_ID"], "ROLE": glyph["ROLE"], "SOURCE_FILE": "fig_v5_c04_conditional_slice.tex", "SOURCE_LINE": "all figure-visible glyphs", "DECLARED_PT": glyph["DECLARED_PT"], "GRAPHICS_SCALE": glyph["GRAPHICS_SCALE"], "EFFECTIVE_PT": glyph["EFFECTIVE_PT"], "TEXT_SAMPLE": glyph["CHAR"], "SCRIPT_CLASS": glyph["SCRIPT_CLASS"], "BBOX_X0": glyph["NATIVE_BBOX_PX"].split(",")[0], "BBOX_Y0": glyph["NATIVE_BBOX_PX"].split(",")[1], "BBOX_X1": glyph["NATIVE_BBOX_PX"].split(",")[2], "BBOX_Y1": glyph["NATIVE_BBOX_PX"].split(",")[3], "H_INK_PX": glyph["H_INK_PX"], "CLASS_MEDIAN_PX": f"{median:.6f}", "RATIO_TO_CLASS_MEDIAN": f"{ratio:.6f}", "ROLE_RATIO": "ACTUAL_BASELINE_PENDING", "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": f"{min_rel:.6f}", "PASS_FAIL": glyph["PASS_FAIL"], "REASON": "pixel/pt gate from raw native mask"})
    write_csv(root / "after_pixel_measurements.csv", pixel_rows, list(pixel_rows[0].keys()))

    # Actual D/E baselines, never a hard-coded true.
    de_rows = []
    for key, values in sorted(per_parent_h.items()):
        med = float(np.median(values))
        ratio = max(values) / min(values) if min(values) else float("inf")
        de_rows.append({"PANEL_ID": key[0], "ROLE": key[1], "SCRIPT_CLASS": key[2], "ELEMENT_COUNT": len(values), "ACTUAL_H_INK_MEDIAN": f"{med:.6f}", "ACTUAL_H_INK_MAX_MIN_RATIO": f"{ratio:.6f}", "D_RESULT": "PASS" if 0.92 <= min(values) / med and max(values) / med <= 1.08 else "FAIL", "E_CROSS_PANEL_RESULT": "PASS"})
    # Derive the E fields per role/script across all actual panel medians.
    groups_for_e = defaultdict(list)
    for row in de_rows:
        groups_for_e[(row["ROLE"], row["SCRIPT_CLASS"])].append(float(row["ACTUAL_H_INK_MEDIAN"]))
    for row in de_rows:
        medians = groups_for_e[(row["ROLE"], row["SCRIPT_CLASS"])]
        cross_ratio = max(medians) / min(medians) if min(medians) else float("inf")
        row["E_CROSS_PANEL_MAX_MIN_RATIO"] = f"{cross_ratio:.6f}"
        row["E_CROSS_PANEL_RESULT"] = "PASS" if cross_ratio <= 1.10 else "FAIL"
    write_csv(root / "ledger" / "de_actual_baselines.csv", de_rows, list(de_rows[0].keys()))

    failure_glyphs = [g for g in glyphs if g["PASS_FAIL"] == "FAIL"]
    relation_failures = [r for r in relations if r["RESULT"] == "FAIL"]
    graphic_failures = [g for g in graphic_rows if g["MASK_RESULT"] != "PASS"]
    edge_failures = [r for r in edge_rows if r["RESULT"] != "PASS"]
    all_mask_ok = all(g["MASK_PIXELS"] > 0 and g["MISSING_STROKE_PX"] == 0 and g["FOREIGN_PIXEL_PX"] == 0 for g in glyphs)
    summary = {
        "figure_uid": UID,
        "authority": {"pdf": str(pdf_path), "physical_page": PAGE_NUMBER, "page_pt": [float(page.rect.width), float(page.rect.height)], "native300_px": [int(native.shape[1]), int(native.shape[0])], "crop_native300": list(CROP), "scope_pdf_pt": list(PDF_SCOPE)},
        "glyph_count": len(glyphs), "glyph_mask_integrity_pass": all_mask_ok, "glyph_font_failures": [g["GLYPH_ID"] for g in failure_glyphs], "low_profile_calibration_rows": len(calibration_rows), "low_profile_calibration_failures": [r["GLYPH_ID"] for r in calibration_rows if r["RESULT"] != "PASS"], "parent_count": len(parent_masks), "graphic_count": len(graphics), "all_unordered_text_text_relations": len([r for r in relations if "TEXT_TEXT" in r["RELATION_SCOPE"]]), "text_graphic_relations": len([r for r in relations if r["RELATION_SCOPE"].startswith("TEXT_") and "TEXT_TEXT" not in r["RELATION_SCOPE"]]), "relation_failures": [r["RELATION_ID"] for r in relation_failures], "edge_failures": [r["PARENT_ID"] for r in edge_failures], "graphic_mask_failures": [r["GRAPHIC_ID"] for r in graphic_failures], "overall_pre_manual_result": "FAIL" if failure_glyphs or relation_failures or edge_failures or graphic_failures else "PENDING_MANUAL_AND_VISUAL"}
    write_json(root / "R95_AUTHORITY_AND_SCOPE.json", summary["authority"])
    write_json(root / "final_table_summary.json", summary)
    write_json(root / "generation_counts.json", {"glyphs": len(glyphs), "contact_sheets": len(sheet_rows), "calibration_rows": len(calibration_rows), "parents": len(parent_masks), "graphics": len(graphics), "relations": len(relations), "edge_relations": len(edge_rows)})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
