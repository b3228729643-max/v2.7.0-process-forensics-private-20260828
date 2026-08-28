from __future__ import annotations

import csv
import itertools
import json
import math
import os
import unicodedata
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf")
PHYSICAL_PAGE = 69
PAGE_INDEX = PHYSICAL_PAGE - 1
SCALE = 300.0 / 72.0

# These integer coordinates were frozen after opening the 300 dpi page render.
# They contain the complete two-panel figure and caption with generous white margin.
FIGURE_CROP = (420, 260, 2020, 930)
BODY_CROP = (420, 260, 2020, 835)
FIGURE_PT = (100.8, 62.4, 484.8, 223.2)
BODY_PT = (100.8, 62.4, 484.8, 200.4)

MANUAL_RESERVED = {
    "manual_glyph_review.csv",
    "manual_relationship_review.md",
    "manual_view_review.md",
    "after_visual_acceptance.md",
    "RESULT.txt",
}


def ensure_dirs() -> None:
    for name in (
        "glyph_contacts",
        "glyph_masks",
        "contact_sheets",
        "drawing_masks",
        "critical_pairs",
        "critical_rois",
    ):
        (ROOT / name).mkdir(exist_ok=True)


def write_json(name: str, payload: object) -> None:
    if name in MANUAL_RESERVED:
        raise RuntimeError(f"machine writer may not touch manual file: {name}")
    (ROOT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_csv(name: str, rows: list[dict], fieldnames: list[str]) -> None:
    if name in MANUAL_RESERVED:
        raise RuntimeError(f"machine writer may not touch manual file: {name}")
    with (ROOT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def px_bbox(pt_bbox: list[float] | tuple[float, ...], pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pt_bbox
    return (
        max(0, math.floor(x0 * SCALE) - pad),
        max(0, math.floor(y0 * SCALE) - pad),
        min(PAGE_W, math.ceil(x1 * SCALE) + pad),
        min(PAGE_H, math.ceil(y1 * SCALE) + pad),
    )


def text_color(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def ink_mask(rgb: np.ndarray) -> np.ndarray:
    return (255 - rgb.astype(np.int16)).max(axis=2) >= 20


def target_color_mask(rgb: np.ndarray, colors: list[tuple[int, int, int]]) -> np.ndarray:
    if not colors:
        return ink_mask(rgb)
    pix = rgb.astype(np.float32)
    best = np.zeros(rgb.shape[:2], dtype=bool)
    for color in colors:
        target = np.array(color, dtype=np.float32)
        delta = 255.0 - target
        useful = delta > 10.0
        if not np.any(useful):
            continue
        alpha_components = (255.0 - pix[..., useful]) / delta[useful]
        alpha = np.median(alpha_components, axis=2)
        predicted = 255.0 - alpha[..., None] * delta[None, None, :]
        residual = np.max(np.abs(predicted - pix), axis=2)
        candidate = (alpha >= (20.0 / max(float(delta.max()), 1.0))) & (alpha <= 1.12) & (residual <= 14.0)
        # Colored plot strokes must retain the source hue. Without this guard,
        # pale antialiased gray text inside a long drawing bbox can look like a
        # very low-alpha sample of the target color and contaminate the mask.
        if float(np.ptp(target)) >= 24.0:
            observed_chroma = np.ptp(pix, axis=2)
            observed_ink = np.maximum((255.0 - pix).max(axis=2), 1.0)
            target_chroma_ratio = float(np.ptp(target)) / max(float(delta.max()), 1.0)
            candidate &= (observed_chroma / observed_ink) >= max(0.12, target_chroma_ratio * 0.55)
        best |= candidate
    return best & ink_mask(rgb)


def tight_bbox(mask: np.ndarray, origin: tuple[int, int]) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    ox, oy = origin
    return (ox + int(xs.min()), oy + int(ys.min()), ox + int(xs.max()) + 1, oy + int(ys.max()) + 1)


def point_px(point: fitz.Point, origin: tuple[int, int]) -> tuple[int, int]:
    return (int(round(point.x * SCALE)) - origin[0], int(round(point.y * SCALE)) - origin[1])


def geometric_support_mask(drawing: dict, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    support = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    width_px = max(1, int(math.ceil(float(drawing.get("width") or 0.6) * SCALE)))
    stroke_thickness = width_px + 3
    subpaths: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []
    for item in drawing.get("items", []):
        kind = item[0]
        if kind == "l":
            p0, p1 = point_px(item[1], (x0, y0)), point_px(item[2], (x0, y0))
            cv2.line(support, p0, p1, 255, thickness=stroke_thickness, lineType=cv2.LINE_AA)
            if not current:
                current.append(p0)
            current.append(p1)
        elif kind == "c":
            p0 = np.array(point_px(item[1], (x0, y0)), dtype=np.float64)
            p1 = np.array(point_px(item[2], (x0, y0)), dtype=np.float64)
            p2 = np.array(point_px(item[3], (x0, y0)), dtype=np.float64)
            p3 = np.array(point_px(item[4], (x0, y0)), dtype=np.float64)
            points = []
            for t in np.linspace(0.0, 1.0, 41):
                q = ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * (t**2) * p2 + (t**3) * p3
                points.append((int(round(q[0])), int(round(q[1]))))
            cv2.polylines(support, [np.array(points, dtype=np.int32)], False, 255, thickness=stroke_thickness, lineType=cv2.LINE_AA)
            if not current:
                current.append(points[0])
            current.extend(points[1:])
        else:
            raise RuntimeError(f"unexpected drawing item {kind!r} in seqno {drawing.get('seqno')}")
    if current:
        subpaths.append(current)
    if drawing.get("fill") is not None and subpaths:
        for points in subpaths:
            if len(points) >= 3:
                cv2.fillPoly(support, [np.array(points, dtype=np.int32)], 255, lineType=cv2.LINE_AA)
    return support > 0


def category_for(ch: str, span_size: float) -> tuple[str, int]:
    code = ord(ch)
    low_punct = set(".,:;，。；：、…·")
    if ch in low_punct:
        return "LOW_PROFILE_PUNCTUATION", 1
    if span_size < 8.0 and (ch.isdigit() or ch.isalpha() or code >= 0x1D400):
        return "NATURAL_TEX_SCRIPT", 15
    if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
        return "CJK_FULL", 30
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_CAP_OR_DIGIT", 24
    if ch.islower() or code >= 0x1D400:
        return "LATIN_GREEK_LOWER", 17
    return "BASE_MATH_OR_OPERATOR", 22


def safe_text(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")


def mask_png(mask: np.ndarray) -> Image.Image:
    arr = np.where(mask, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="L")


def overlay_image(original: Image.Image, mask: np.ndarray, color=(255, 0, 0), alpha=0.62) -> Image.Image:
    base = np.array(original.convert("RGB"), dtype=np.float32)
    tint = np.array(color, dtype=np.float32)
    base[mask] = base[mask] * (1.0 - alpha) + tint * alpha
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), mode="RGB")


def make_glyph_contact(
    gid: str,
    ch: str,
    category: str,
    h_ink: int,
    threshold: int,
    bbox_global: tuple[int, int, int, int],
    local_rgb: np.ndarray,
    mask: np.ndarray,
) -> Image.Image:
    pad = 8
    original = Image.fromarray(local_rgb, mode="RGB")
    overlay = overlay_image(original, mask)
    mono = mask_png(mask).convert("RGB")
    views = [original, overlay, mono]
    labels = ["ORIGINAL 1x", "TARGET OVERLAY 1x", "MASK ONLY 1x"]
    zooms = [v.resize((v.width * 8, v.height * 8), Image.Resampling.NEAREST) for v in views]
    max_native_h = max(v.height for v in views)
    max_zoom_h = max(v.height for v in zooms)
    width = max(900, sum(v.width for v in zooms) + 4 * pad)
    height = 66 + max_native_h + 24 + max_zoom_h + 3 * pad
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    char_label = ch if ch.isprintable() else f"U+{ord(ch):04X}"
    header = (
        f"{gid} char={char_label!r} U+{ord(ch):04X} category={category} "
        f"H_INK={h_ink}px threshold={threshold}px bbox={bbox_global}"
    )
    draw.text((pad, pad), header, fill="black", font=font)
    x = pad
    y = 34
    for label, view in zip(labels, views):
        draw.text((x, y), label, fill="black", font=font)
        canvas.paste(view, (x, y + 16))
        x += view.width + 3 * pad
    x = pad
    y2 = 34 + max_native_h + 28
    for label, view in zip(labels, zooms):
        draw.text((x, y2), label.replace("1x", "8x NN"), fill="black", font=font)
        canvas.paste(view, (x, y2 + 16))
        x += view.width + pad
    return canvas


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def pair_metrics(a: dict, b: dict) -> tuple[int, float]:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    ux0, uy0 = min(ax0, bx0), min(ay0, by0)
    ux1, uy1 = max(ax1, bx1), max(ay1, by1)
    if ux1 <= ux0 or uy1 <= uy0:
        return 0, float("inf")
    # Distant pairs use the conservative bounding-box gap and need no raster allocation.
    gap = bbox_gap(a["bbox_px"], b["bbox_px"])
    if gap > 24:
        return 0, gap
    h, w = uy1 - uy0, ux1 - ux0
    ma = np.zeros((h, w), dtype=np.uint8)
    mb = np.zeros((h, w), dtype=np.uint8)
    ma[ay0 - uy0 : ay1 - uy0, ax0 - ux0 : ax1 - ux0] = a["mask"].astype(np.uint8)
    mb[by0 - uy0 : by1 - uy0, bx0 - ux0 : bx1 - ux0] = b["mask"].astype(np.uint8)
    overlap = int(np.count_nonzero(ma & mb))
    if overlap:
        return overlap, 0.0
    if not ma.any() or not mb.any():
        return 0, float("inf")
    dist_to_a = cv2.distanceTransform((1 - ma).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    return 0, float(dist_to_a[mb.astype(bool)].min())


def save_pair_evidence(pair_id: str, a: dict, b: dict) -> dict[str, str]:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    pad = 8
    x0, y0 = max(0, min(ax0, bx0) - pad), max(0, min(ay0, by0) - pad)
    x1, y1 = min(PAGE_W, max(ax1, bx1) + pad), min(PAGE_H, max(ay1, by1) + pad)
    original = PAGE_IMG.crop((x0, y0, x1, y1)).convert("RGB")
    h, w = y1 - y0, x1 - x0
    ma = np.zeros((h, w), dtype=bool)
    mb = np.zeros((h, w), dtype=bool)
    ma[ay0 - y0 : ay1 - y0, ax0 - x0 : ax1 - x0] = a["mask"]
    mb[by0 - y0 : by1 - y0, bx0 - x0 : bx1 - x0] = b["mask"]
    overlay = np.array(original, dtype=np.float32)
    overlay[ma] = overlay[ma] * 0.35 + np.array([255, 0, 0]) * 0.65
    overlay[mb] = overlay[mb] * 0.35 + np.array([0, 70, 255]) * 0.65
    both = ma & mb
    overlay[both] = np.array([255, 0, 255])
    overlay_img = Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8), mode="RGB")
    base = ROOT / "critical_pairs" / pair_id
    original_path = base.with_name(base.name + "_original_1x.png")
    overlay_path = base.with_name(base.name + "_overlay_1x.png")
    mask_a_path = base.with_name(base.name + "_mask_a.png")
    mask_b_path = base.with_name(base.name + "_mask_b.png")
    inter_path = base.with_name(base.name + "_intersection.png")
    zoom_path = base.with_name(base.name + "_overlay_8x_nearest.png")
    original.save(original_path)
    overlay_img.save(overlay_path)
    mask_png(ma).save(mask_a_path)
    mask_png(mb).save(mask_b_path)
    mask_png(both).save(inter_path)
    overlay_img.resize((overlay_img.width * 8, overlay_img.height * 8), Image.Resampling.NEAREST).save(zoom_path)
    return {
        "original_1x": original_path.name,
        "overlay_1x": overlay_path.name,
        "mask_a": mask_a_path.name,
        "mask_b": mask_b_path.name,
        "intersection": inter_path.name,
        "overlay_8x_nearest": zoom_path.name,
        "roi_global_px": f"[{x0},{y0},{x1-x0},{y1-y0}]",
    }


def drawing_role(seqno: int) -> str:
    roles = {
        3: "CDF_TICKS_X_GROUP",
        4: "CDF_TICKS_Y_GROUP",
        5: "CDF_AXIS_X",
        6: "CDF_AXIS_X_ARROWHEAD",
        7: "CDF_AXIS_Y",
        8: "CDF_AXIS_Y_ARROWHEAD",
        13: "CDF_STEP_CURVE",
        14: "CDF_LIMIT_LINE_Y1",
        15: "CDF_GUIDE_X1",
        16: "CDF_GUIDE_X2",
        17: "CDF_GUIDE_X3",
        18: "CDF_GUIDE_X4",
        28: "CDF_FILLED_MARKER_X1",
        30: "CDF_FILLED_MARKER_X2",
        32: "CDF_FILLED_MARKER_X3",
        34: "CDF_FILLED_MARKER_X4",
        36: "CDF_OPEN_MARKER_X1",
        37: "CDF_OPEN_MARKER_X2",
        38: "CDF_OPEN_MARKER_X3",
        39: "CDF_OPEN_MARKER_X4",
        41: "PMF_TICKS_X_GROUP",
        42: "PMF_TICKS_Y_GROUP",
        43: "PMF_AXIS_X",
        44: "PMF_AXIS_X_ARROWHEAD",
        45: "PMF_AXIS_Y",
        46: "PMF_AXIS_Y_ARROWHEAD",
        54: "PMF_STEM_GROUP",
        56: "PMF_GUIDE_X1",
        57: "PMF_GUIDE_X2",
        58: "PMF_GUIDE_X3",
        59: "PMF_GUIDE_X4",
        62: "PMF_MARKER_X1",
        64: "PMF_MARKER_X2",
        66: "PMF_MARKER_X3",
        68: "PMF_MARKER_X4",
    }
    return roles.get(seqno, f"UNCLASSIFIED_FOREGROUND_SEQ_{seqno}")


def intended_drawing_connection(a: dict, b: dict) -> bool:
    if a["kind"] != "DRAWING" or b["kind"] != "DRAWING":
        return False
    ra, rb = a["role"], b["role"]
    pair = {ra, rb}
    if pair in (
        {"CDF_AXIS_X", "CDF_AXIS_X_ARROWHEAD"},
        {"CDF_AXIS_Y", "CDF_AXIS_Y_ARROWHEAD"},
        {"PMF_AXIS_X", "PMF_AXIS_X_ARROWHEAD"},
        {"PMF_AXIS_Y", "PMF_AXIS_Y_ARROWHEAD"},
    ):
        return True
    if "CDF_STEP_CURVE" in pair and any("CDF_FILLED_MARKER" in r or "CDF_OPEN_MARKER" in r for r in pair):
        return True
    if "PMF_STEM_GROUP" in pair and any("PMF_MARKER" in r for r in pair):
        return True
    if any("GUIDE" in r for r in pair) and any(
        token in other
        for token in ("CURVE", "STEM", "MARKER", "AXIS", "TICKS")
        for other in pair
    ):
        return True
    if any("TICKS" in r for r in pair) and any("AXIS" in other for other in pair):
        return True
    return False


ensure_dirs()
for reserved in MANUAL_RESERVED:
    if (ROOT / reserved).exists():
        raise RuntimeError(f"refusing to run after manual review exists: {reserved}")

PAGE_IMG = Image.open(ROOT / "page_300dpi.png").convert("RGB")
PAGE_GRAY = Image.open(ROOT / "page_gray_300dpi.png").convert("L")
PAGE_W, PAGE_H = PAGE_IMG.size
if (PAGE_W, PAGE_H) != (2481, 3508):
    raise RuntimeError(f"unexpected native page dimensions {(PAGE_W, PAGE_H)}")

figure = PAGE_IMG.crop(FIGURE_CROP)
standalone = PAGE_IMG.crop(BODY_CROP)
gray_figure = PAGE_GRAY.crop(FIGURE_CROP)
figure.save(ROOT / "figure_crop_300dpi.png")
standalone.save(ROOT / "standalone_300dpi.png")
gray_figure.save(ROOT / "grayscale_300dpi.png")
figure.resize((figure.width * 8, figure.height * 8), Image.Resampling.NEAREST).save(
    ROOT / "figure_crop_300dpi_8x_nearest.png"
)

doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
raw = page.get_text("rawdict")

line_texts: dict[str, str] = {}
for bi, block in enumerate(raw["blocks"]):
    if block.get("type") != 0:
        continue
    for li, line in enumerate(block.get("lines", [])):
        key = f"B{bi:03d}-L{li:02d}"
        line_texts[key] = "".join(
            char.get("c", "")
            for span in line.get("spans", [])
            for char in span.get("chars", [])
        )

glyph_raw: list[dict] = []
for bi, block in enumerate(raw["blocks"]):
    if block.get("type") != 0:
        continue
    for li, line in enumerate(block.get("lines", [])):
        parent = f"B{bi:03d}-L{li:02d}"
        for si, span in enumerate(line.get("spans", [])):
            for ci, char in enumerate(span.get("chars", [])):
                ch = char.get("c", "")
                if not ch or ch.isspace():
                    continue
                bbox = tuple(float(v) for v in char["bbox"])
                cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
                if not (FIGURE_PT[0] <= cx <= FIGURE_PT[2] and FIGURE_PT[1] <= cy <= FIGURE_PT[3]):
                    continue
                glyph_raw.append(
                    {
                        "sort": (bbox[1], bbox[0], bi, li, si, ci),
                        "char": ch,
                        "bbox_pt": bbox,
                        "origin_pt": tuple(float(v) for v in char.get("origin", (0, 0))),
                        "span_size_pt": float(span.get("size", 0)),
                        "font": span.get("font", ""),
                        "color": int(span.get("color", 0)),
                        "flags": int(span.get("flags", 0)),
                        "parent": parent,
                        "parent_text": line_texts[parent],
                        "source_index": f"{bi}:{li}:{si}:{ci}",
                    }
                )

glyph_raw.sort(key=lambda row: row["sort"])
glyph_rows: list[dict] = []
font_rows: list[dict] = []
objects: list[dict] = []
contact_images: list[Image.Image] = []
overlay = figure.copy()
overlay_draw = ImageDraw.Draw(overlay)
overlay_font = ImageFont.load_default()

for index, row in enumerate(glyph_raw, 1):
    gid = f"G{index:03d}"
    bbox = px_bbox(row["bbox_pt"], pad=1)
    x0, y0, x1, y1 = bbox
    local_rgb = np.asarray(PAGE_IMG.crop(bbox).convert("RGB"))
    mask = target_color_mask(local_rgb, [text_color(row["color"])])
    tb = tight_bbox(mask, (x0, y0))
    h_ink = 0 if tb is None else tb[3] - tb[1]
    w_ink = 0 if tb is None else tb[2] - tb[0]
    category, threshold = category_for(row["char"], row["span_size_pt"])
    strict_machine_pass = bool(mask.any() and (category == "LOW_PROFILE_PUNCTUATION" or h_ink >= threshold))
    mask_path = ROOT / "glyph_masks" / f"{gid}.png"
    mask_png(mask).save(mask_path)
    contact = make_glyph_contact(
        gid, row["char"], category, h_ink, threshold, bbox, local_rgb, mask
    )
    contact_path = ROOT / "glyph_contacts" / f"{gid}.png"
    contact.save(contact_path)
    contact_images.append(contact)
    crop_x0, crop_y0 = FIGURE_CROP[0], FIGURE_CROP[1]
    overlay_draw.rectangle((x0 - crop_x0, y0 - crop_y0, x1 - crop_x0, y1 - crop_y0), outline=(255, 0, 0), width=1)
    overlay_draw.text((x0 - crop_x0, max(0, y0 - crop_y0 - 10)), gid, fill=(200, 0, 0), font=overlay_font)
    glyph_rows.append(
        {
            "element_id": gid,
            "char": row["char"],
            "unicode": f"U+{ord(row['char']):04X}",
            "unicode_name": unicodedata.name(row["char"], "UNNAMED"),
            "parent_id": row["parent"],
            "parent_text": safe_text(row["parent_text"]),
            "source_index": row["source_index"],
            "font": row["font"],
            "pdf_span_size_pt": f"{row['span_size_pt']:.3f}",
            "font_rgb": str(text_color(row["color"])),
            "bbox_pt": str(tuple(round(v, 3) for v in row["bbox_pt"])),
            "bbox_px_global": str(bbox),
            "tight_ink_bbox_px_global": "" if tb is None else str(tb),
            "mask_pixels": int(mask.sum()),
            "h_ink_px": h_ink,
            "w_ink_px": w_ink,
            "taxonomy": category,
            "strict_reference_threshold_px": threshold,
            "strict_reference_machine_pass": strict_machine_pass,
            "mask_path": str(mask_path.relative_to(ROOT)),
            "contact_path": str(contact_path.relative_to(ROOT)),
        }
    )
    font_rows.append(
        {
            "element_id": gid,
            "char": row["char"],
            "parent_id": row["parent"],
            "font": row["font"],
            "pdf_span_size_pt": f"{row['span_size_pt']:.3f}",
            "taxonomy": category,
            "h_ink_px": h_ink,
            "strict_reference_threshold_px": threshold,
            "strict_reference_machine_pass": strict_machine_pass,
            "r168_hard_gate_scope": "missing/tofu/wrong-codepoint/actual-unreadability-only",
        }
    )
    objects.append(
        {
            "id": gid,
            "kind": "GLYPH",
            "role": category,
            "parent": row["parent"],
            "char": row["char"],
            "bbox_px": bbox,
            "mask": mask,
            "mask_pixels": int(mask.sum()),
        }
    )

overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

# Six reviewer-sized contact cells per sheet. No reviewer fields are authored here.
sheet_index = []
for sheet_no, start in enumerate(range(0, len(contact_images), 6), 1):
    cells = contact_images[start : start + 6]
    width = max(cell.width for cell in cells)
    heights = [cell.height for cell in cells]
    canvas = Image.new("RGB", (width, sum(heights) + 28), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 8), f"FIG-P067-01 glyph contact sheet {sheet_no:02d}", fill="black", font=overlay_font)
    y = 28
    for offset, cell in enumerate(cells):
        canvas.paste(cell, (0, y))
        sheet_index.append(
            {
                "element_id": f"G{start + offset + 1:03d}",
                "sheet": f"contact_sheets/glyph_sheet_{sheet_no:02d}.png",
                "cell": offset + 1,
            }
        )
        y += cell.height
    canvas.save(ROOT / "contact_sheets" / f"glyph_sheet_{sheet_no:02d}.png")

write_csv(
    "machine_glyph_inventory.csv",
    glyph_rows,
    list(glyph_rows[0].keys()),
)
write_csv(
    "after_pixel_measurements.csv",
    glyph_rows,
    list(glyph_rows[0].keys()),
)
write_csv("after_font_audit.csv", font_rows, list(font_rows[0].keys()))
write_csv("machine_contact_sheet_index.csv", sheet_index, list(sheet_index[0].keys()))

drawing_rows: list[dict] = []
halo_rows: list[dict] = []
drawing_overlay = figure.copy()
drawing_overlay_draw = ImageDraw.Draw(drawing_overlay)
draw_counter = 0
all_drawings = page.get_drawings()
body_drawings = []
halo_drawings = []
for drawing in all_drawings:
    rect = drawing["rect"]
    cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
    if not (BODY_PT[0] <= cx <= BODY_PT[2] and BODY_PT[1] <= cy <= BODY_PT[3]):
        continue
    fill = drawing.get("fill")
    stroke = drawing.get("color")
    is_white_fill_only = (
        fill is not None
        and min(fill) >= 0.98
        and (stroke is None or drawing.get("type") == "f")
    )
    seqno = int(drawing.get("seqno", -1))
    if is_white_fill_only:
        halo_drawings.append(drawing)
        halo_rows.append(
            {
                "seqno": seqno,
                "role": "REAL_OPAQUE_TEXT_BACKGROUND",
                "bbox_pt": str(tuple(round(v, 3) for v in rect)),
                "draw_type": drawing.get("type"),
                "item_count": len(drawing.get("items", [])),
                "semantic_effect": "final-visible occlusion of underlying guide/curve behind text",
            }
        )
        continue
    if stroke is None and fill is None:
        continue
    body_drawings.append(drawing)

for drawing in body_drawings:
    rect = drawing["rect"]
    fill = drawing.get("fill")
    stroke = drawing.get("color")
    seqno = int(drawing.get("seqno", -1))
    draw_counter += 1
    did = f"D{draw_counter:03d}"
    bbox = px_bbox(tuple(rect), pad=3)
    x0, y0, x1, y1 = bbox
    local_rgb = np.asarray(PAGE_IMG.crop(bbox).convert("RGB"))
    colors: list[tuple[int, int, int]] = []
    for value in (stroke, fill):
        if value is not None and min(value) < 0.98:
            colors.append(tuple(int(round(255 * channel)) for channel in value))
    mask = target_color_mask(local_rgb, colors)
    mask &= geometric_support_mask(drawing, bbox)
    # Preserve real paint order: later opaque white text backgrounds remove the
    # underlying guide/curve from the final-visible foreground denominator.
    for halo in halo_drawings:
        if int(halo.get("seqno", -1)) <= seqno:
            continue
        hx0, hy0, hx1, hy1 = px_bbox(tuple(halo["rect"]), pad=0)
        ix0, iy0 = max(x0, hx0), max(y0, hy0)
        ix1, iy1 = min(x1, hx1), min(y1, hy1)
        if ix1 > ix0 and iy1 > iy0:
            mask[iy0 - y0 : iy1 - y0, ix0 - x0 : ix1 - x0] = False
    role = drawing_role(seqno)
    tb = tight_bbox(mask, (x0, y0))
    mask_path = ROOT / "drawing_masks" / f"{did}.png"
    mask_png(mask).save(mask_path)
    drawing_rows.append(
        {
            "element_id": did,
            "seqno": seqno,
            "role": role,
            "draw_type": drawing.get("type"),
            "item_count": len(drawing.get("items", [])),
            "stroke_rgb": "" if stroke is None else str(tuple(round(255 * c) for c in stroke)),
            "fill_rgb": "" if fill is None else str(tuple(round(255 * c) for c in fill)),
            "line_width_pt": drawing.get("width"),
            "bbox_pt": str(tuple(round(v, 3) for v in rect)),
            "bbox_px_global": str(bbox),
            "tight_ink_bbox_px_global": "" if tb is None else str(tb),
            "mask_pixels": int(mask.sum()),
            "mask_nonempty": bool(mask.any()),
            "mask_path": str(mask_path.relative_to(ROOT)),
        }
    )
    drawing_overlay_draw.rectangle(
        (x0 - FIGURE_CROP[0], y0 - FIGURE_CROP[1], x1 - FIGURE_CROP[0], y1 - FIGURE_CROP[1]),
        outline=(0, 120, 255),
        width=1,
    )
    drawing_overlay_draw.text(
        (x0 - FIGURE_CROP[0], max(0, y0 - FIGURE_CROP[1] - 10)),
        did,
        fill=(0, 80, 200),
        font=overlay_font,
    )
    objects.append(
        {
            "id": did,
            "kind": "DRAWING",
            "role": role,
            "parent": role.split("_")[0],
            "char": "",
            "seqno": seqno,
            "bbox_px": bbox,
            "mask": mask,
            "mask_pixels": int(mask.sum()),
        }
    )

drawing_overlay.save(ROOT / "machine_drawing_overlay_300dpi.png")
write_csv("machine_drawing_inventory.csv", drawing_rows, list(drawing_rows[0].keys()))
write_csv("machine_occlusion_background_inventory.csv", halo_rows, list(halo_rows[0].keys()))

pair_rows: list[dict] = []
critical_rows: list[dict] = []
for number, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
    pair_id = f"R{number:05d}"
    bbox_distance = bbox_gap(a["bbox_px"], b["bbox_px"])
    overlap, clearance = pair_metrics(a, b)
    same_parent = bool(a["kind"] == "GLYPH" and b["kind"] == "GLYPH" and a["parent"] == b["parent"])
    design_connection = intended_drawing_connection(a, b)
    if same_parent:
        relation_class = "SAME_SEMANTIC_LINE_OR_FORMULA_INTERNAL"
        threshold = 0
    elif design_connection:
        relation_class = "INTENDED_GEOMETRIC_CONNECTION"
        threshold = 0
    elif a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        relation_class = "INDEPENDENT_TEXT_TEXT"
        threshold = 4
    elif a["kind"] == "GLYPH" or b["kind"] == "GLYPH":
        relation_class = "TEXT_OR_FORMULA_TO_GRAPHIC"
        threshold = 3
    else:
        relation_class = "GRAPHIC_GRAPHIC"
        threshold = 0
    review_required = bool(
        (not same_parent)
        and (not design_connection)
        and (
            overlap > 0
            or clearance < max(threshold + 9, 12)
            or bbox_distance < max(threshold + 9, 12)
        )
    )
    evidence = {}
    if review_required:
        evidence = save_pair_evidence(pair_id, a, b)
    row = {
        "pair_id": pair_id,
        "a_id": a["id"],
        "b_id": b["id"],
        "a_kind": a["kind"],
        "b_kind": b["kind"],
        "a_role": a["role"],
        "b_role": b["role"],
        "relation_class": relation_class,
        "same_semantic_parent": same_parent,
        "intended_geometric_connection": design_connection,
        "bbox_gap_px": round(bbox_distance, 3),
        "raw_mask_intersection_px": overlap,
        "raw_mask_clearance_px": "INF" if math.isinf(clearance) else round(clearance, 3),
        "reference_threshold_px": threshold,
        "manual_review_required": review_required,
        "evidence_original_1x": evidence.get("original_1x", ""),
        "evidence_overlay_1x": evidence.get("overlay_1x", ""),
        "evidence_mask_a": evidence.get("mask_a", ""),
        "evidence_mask_b": evidence.get("mask_b", ""),
        "evidence_intersection": evidence.get("intersection", ""),
        "evidence_overlay_8x_nearest": evidence.get("overlay_8x_nearest", ""),
        "evidence_roi_global_px": evidence.get("roi_global_px", ""),
    }
    pair_rows.append(row)
    if review_required:
        critical_rows.append(row)

write_csv("after_overlap_report.csv", pair_rows, list(pair_rows[0].keys()))
write_csv("machine_critical_pair_index.csv", critical_rows, list(pair_rows[0].keys()))

# Four figure-scale critical ROIs, frozen at native 300 dpi and 8x nearest-neighbour.
roi_specs = {
    "cdf_left_right_continuity": (430, 280, 1180, 550),
    "cdf_jump_endpoints_and_labels": (760, 285, 1900, 540),
    "pmf_stems_ticks_and_note": (430, 535, 2000, 800),
    "caption_integration": (520, 820, 1900, 925),
}
for name, box in roi_specs.items():
    roi = PAGE_IMG.crop(box)
    roi.save(ROOT / "critical_rois" / f"{name}_native_300dpi_1x.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "critical_rois" / f"{name}_native_300dpi_8x_nearest.png"
    )

text_trace = page.get_texttrace()
visible_trace = [
    t
    for t in text_trace
    if fitz.Rect(t["bbox"]).intersects(fitz.Rect(*FIGURE_PT))
]
replacement_count = sum(row["char"] == "\ufffd" for row in glyph_raw)
tofu_suspects = [
    row["element_id"]
    for row in glyph_rows
    if row["char"] in {"□", "▯", "�"}
]
object_count = len(objects)
pair_count = len(pair_rows)
expected_pairs = object_count * (object_count - 1) // 2
machine_summary = {
    "uid": "FIG-P067-01",
    "official_pdf": str(PDF),
    "physical_page": PHYSICAL_PAGE,
    "printed_page": 56,
    "page_pt": [round(page.rect.width, 3), round(page.rect.height, 3)],
    "page_300dpi_px": [PAGE_W, PAGE_H],
    "figure_crop_global_px_xywh": [
        FIGURE_CROP[0],
        FIGURE_CROP[1],
        FIGURE_CROP[2] - FIGURE_CROP[0],
        FIGURE_CROP[3] - FIGURE_CROP[1],
    ],
    "standalone_crop_global_px_xywh": [
        BODY_CROP[0],
        BODY_CROP[1],
        BODY_CROP[2] - BODY_CROP[0],
        BODY_CROP[3] - BODY_CROP[1],
    ],
    "figure_crop_native_px": list(figure.size),
    "standalone_native_px": list(standalone.size),
    "grayscale_native_px": list(gray_figure.size),
    "glyph_count": len(glyph_rows),
    "glyph_mask_nonempty_count": sum(int(row["mask_pixels"]) > 0 for row in glyph_rows),
    "glyph_strict_reference_pixel_pass_count": sum(bool(row["strict_reference_machine_pass"]) for row in glyph_rows),
    "drawing_foreground_count": len(drawing_rows),
    "drawing_mask_nonempty_count": sum(bool(row["mask_nonempty"]) for row in drawing_rows),
    "opaque_text_background_count": len(halo_rows),
    "visible_text_trace_span_count": len(visible_trace),
    "math_rule_path_count": 0,
    "math_rule_reason": "No overline/underline/fraction/radical/accent rule occurs in the visible figure; subscripts are PDF text glyphs.",
    "replacement_character_count": replacement_count,
    "tofu_suspect_ids": tofu_suspects,
    "visible_object_denominator": object_count,
    "unordered_pair_expected": expected_pairs,
    "unordered_pair_enumerated": pair_count,
    "critical_pair_evidence_count": len(critical_rows),
    "empty_mask_count": sum(obj["mask_pixels"] == 0 for obj in objects),
    "machine_files_write_manual_fields": False,
}
if pair_count != expected_pairs:
    raise RuntimeError("unordered-pair denominator mismatch")
write_json("machine_summary.json", machine_summary)
write_json(
    "native_render_manifest.json",
    {
        "pdf": str(PDF),
        "physical_page": PHYSICAL_PAGE,
        "printed_page": 56,
        "renderer": "Poppler pdftoppm native page render; Pillow integer crop only",
        "page_pt": machine_summary["page_pt"],
        "page_300dpi_px": machine_summary["page_300dpi_px"],
        "figure_crop_global_px_xywh": machine_summary["figure_crop_global_px_xywh"],
        "standalone_crop_global_px_xywh": machine_summary["standalone_crop_global_px_xywh"],
        "no_resize_for_measurement_views": True,
        "nearest_neighbour_8x_is_visual_only": True,
        "views": {
            "full_page_200dpi": "full_page_200dpi.png",
            "page_300dpi_master": "page_300dpi.png",
            "figure_crop_300dpi": "figure_crop_300dpi.png",
            "standalone_300dpi": "standalone_300dpi.png",
            "grayscale_300dpi": "grayscale_300dpi.png",
            "figure_crop_8x_nearest": "figure_crop_300dpi_8x_nearest.png",
        },
    },
)

print(json.dumps(machine_summary, ensure_ascii=False, indent=2))
