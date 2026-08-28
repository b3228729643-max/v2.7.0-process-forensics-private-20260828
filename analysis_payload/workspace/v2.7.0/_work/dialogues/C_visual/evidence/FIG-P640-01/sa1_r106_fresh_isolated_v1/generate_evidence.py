from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r106_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r106_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_mixing_rho_comparison.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C04.tex")
PHYSICAL_PAGE = 690
PAGE_INDEX = PHYSICAL_PAGE - 1
SCALE = 300 / 72
FIGURE_RECT = fitz.Rect(80, 65, 525, 295)
BODY_RECT = fitz.Rect(80, 65, 525, 260)
RIGHT_RECT = fitz.Rect(365, 65, 515, 220)
OBJECT_RECT = fitz.Rect(70, 60, 525, 295)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def fitz_color_to_rgb(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(255 * float(v))) for v in value)


def rect_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        max(0, math.floor(rect.x0 * SCALE)),
        max(0, math.floor(rect.y0 * SCALE)),
        min(PAGE_W, math.ceil(rect.x1 * SCALE)),
        min(PAGE_H, math.ceil(rect.y1 * SCALE)),
    )


def color_line_mask(arr: np.ndarray, ink_rgb: tuple[int, int, int]) -> np.ndarray:
    """Pixels on the anti-aliased segment from white background to an ink color."""
    pix = arr.astype(np.float32)
    ink = np.asarray(ink_rgb, dtype=np.float32)
    denom = 255.0 - ink
    valid = denom > 3
    if not np.any(valid):
        return np.zeros(arr.shape[:2], dtype=bool)
    alphas = (255.0 - pix[:, :, valid]) / denom[valid]
    alpha = np.median(alphas, axis=2)
    alpha = np.clip(alpha, 0, 1)
    predicted = 255.0 - alpha[:, :, None] * (255.0 - ink[None, None, :])
    residual = np.max(np.abs(pix - predicted), axis=2)
    contrast = np.max(255.0 - pix, axis=2)
    return (contrast >= 20.0) & (residual <= 24.0) & (alpha >= 0.025)


def sparse_crop(mask: np.ndarray, bbox: tuple[int, int, int, int]):
    x0, y0, x1, y1 = bbox
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "mask": mask.astype(bool)}


def sparse_intersection(a, b) -> int:
    x0 = max(a["x0"], b["x0"])
    y0 = max(a["y0"], b["y0"])
    x1 = min(a["x1"], b["x1"])
    y1 = min(a["y1"], b["y1"])
    if x1 <= x0 or y1 <= y0:
        return 0
    am = a["mask"][y0 - a["y0"] : y1 - a["y0"], x0 - a["x0"] : x1 - a["x0"]]
    bm = b["mask"][y0 - b["y0"] : y1 - b["y0"], x0 - b["x0"] : x1 - b["x0"]]
    return int(np.count_nonzero(am & bm))


def sparse_clearance(a, b, cap: int = 64) -> float:
    if sparse_intersection(a, b):
        return 0.0
    x0 = max(0, min(a["x0"], b["x0"]) - 2)
    y0 = max(0, min(a["y0"], b["y0"]) - 2)
    x1 = min(PAGE_W, max(a["x1"], b["x1"]) + 2)
    y1 = min(PAGE_H, max(a["y1"], b["y1"]) + 2)
    if x1 - x0 > (a["x1"] - a["x0"]) + (b["x1"] - b["x0"]) + 2 * cap:
        return float(cap + 1)
    if y1 - y0 > (a["y1"] - a["y0"]) + (b["y1"] - b["y0"]) + 2 * cap:
        return float(cap + 1)
    aa = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bb = np.zeros_like(aa)
    aa[a["y0"] - y0 : a["y1"] - y0, a["x0"] - x0 : a["x1"] - x0] = a["mask"]
    bb[b["y0"] - y0 : b["y1"] - y0, b["x0"] - x0 : b["x1"] - x0] = b["mask"]
    if not np.any(aa) or not np.any(bb):
        return float("nan")
    dist = distance_transform_edt(~aa)
    return float(np.min(dist[bb]))


def bbox_gap(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def role_for_text(seqno: int, bbox: fitz.Rect) -> tuple[str, str, str]:
    if 6 <= seqno <= 17:
        return "LEFT_PANEL", "TICK_LABEL", "BASE"
    if seqno == 21:
        return "LEFT_PANEL", "AXIS_TITLE", "BASE"
    if seqno == 22:
        return "LEFT_PANEL", "AXIS_TITLE_FORMULA", "FORMULA"
    if seqno == 23:
        return "LEFT_PANEL", "PANEL_TITLE", "BASE"
    if seqno in (25, 27, 29):
        return "LEFT_PANEL", "LEGEND", "FORMULA"
    if 36 <= seqno <= 41:
        return "RIGHT_PANEL", "TICK_LABEL", "BASE"
    if seqno == 44:
        return "RIGHT_PANEL", "POINT_ANNOTATION", "FORMULA"
    if seqno == 46:
        return "RIGHT_PANEL", "LIMIT_ANNOTATION", "FORMULA"
    if seqno == 51:
        return "RIGHT_PANEL", "AXIS_TITLE", "FORMULA"
    if seqno == 52:
        return "RIGHT_PANEL", "AXIS_TITLE", "FORMULA"
    if seqno in (53, 55):
        return "RIGHT_PANEL", "PANEL_TITLE", "FORMULA"
    if seqno == 56:
        return "CAPTION", "CAPTION", "BASE"
    return "FIGURE", "OTHER_TEXT", "BASE"


DRAW_NAMES = {
    3: ("LEFT_PANEL", "X_TICKS"),
    4: ("LEFT_PANEL", "Y_TICKS"),
    5: ("LEFT_PANEL", "AXIS_FRAME"),
    18: ("LEFT_PANEL", "CURVE_RHO_095"),
    19: ("LEFT_PANEL", "CURVE_RHO_070"),
    20: ("LEFT_PANEL", "CURVE_RHO_020"),
    30: ("RIGHT_PANEL", "X_TICKS"),
    31: ("RIGHT_PANEL", "Y_TICKS"),
    33: ("RIGHT_PANEL", "X_ARROWHEAD"),
    35: ("RIGHT_PANEL", "Y_ARROWHEAD"),
    42: ("RIGHT_PANEL", "ESS_CURVE"),
    43: ("RIGHT_PANEL", "POINT_LABEL_OPAQUE_BG"),
    45: ("RIGHT_PANEL", "LIMIT_NOTE_OPAQUE_BG"),
    47: ("RIGHT_PANEL", "OPEN_POINT_MARKER"),
}


def glyph_category(ch: str, size: float, seqno: int, y0: float) -> tuple[str, int | None]:
    cp = ord(ch)
    if ch in ".,;:，。；：、…":
        return "LOW_PROFILE_PUNCTUATION", None
    if size < 7.5:
        if seqno in (53, 55) and y0 > 80 and ch not in "2":
            return "MATH_BODY_FRACTION", 22
        return "NATURAL_SCRIPT", 15
    if 0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF:
        return "CJK_OR_FULLWIDTH", 30
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_CAP_OR_DIGIT", 24
    if ch in "+=−-→∶/|()":
        return "MATH_OPERATOR_OR_DELIMITER", 22
    if ch.islower() or cp > 0xFFFF or 0x370 <= cp <= 0x3FF:
        return "LATIN_GREEK_LOWER", 17
    return "MATH_OR_SYMBOL", 22


def replay_drawing(page_rect: fitz.Rect, drawing: dict) -> np.ndarray:
    doc = fitz.open()
    p = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = p.new_shape()
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
            raise RuntimeError(f"Unhandled path kind {kind}")
    stroke = (0, 0, 0) if "s" in drawing["type"] else None
    fill = (0, 0, 0) if "f" in drawing["type"] else None
    line_cap = drawing.get("lineCap") or 0
    if isinstance(line_cap, tuple):
        line_cap = max(line_cap)
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=stroke,
        fill=fill,
        lineCap=int(line_cap),
        lineJoin=float(drawing.get("lineJoin") or 0),
        dashes=drawing.get("dashes"),
        closePath=bool(drawing.get("closePath")),
        fill_opacity=float(drawing.get("fill_opacity") or 1),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1),
    )
    shape.commit()
    pix = p.get_pixmap(dpi=300, colorspace=fitz.csGRAY, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    doc.close()
    return arr <= 235


def save_mask_png(path: Path, mask: np.ndarray):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / "masks" / "glyph").mkdir(parents=True, exist_ok=True)
(ROOT / "masks" / "object").mkdir(parents=True, exist_ok=True)
(ROOT / "contacts").mkdir(parents=True, exist_ok=True)
(ROOT / "roi").mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_pix = page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False)
PAGE_W, PAGE_H = page_pix.width, page_pix.height
page_arr = np.frombuffer(page_pix.samples, dtype=np.uint8).reshape(PAGE_H, PAGE_W, 3).copy()
page_pix.save(ROOT / "full_page_300dpi.png")
page.get_pixmap(dpi=200, colorspace=fitz.csRGB, alpha=False).save(ROOT / "full_page_200dpi.png")
page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False, clip=FIGURE_RECT).save(ROOT / "figure_crop_300dpi.png")
page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False, clip=BODY_RECT).save(ROOT / "standalone_300dpi.png")
page.get_pixmap(dpi=300, colorspace=fitz.csGRAY, alpha=False, clip=FIGURE_RECT).save(ROOT / "grayscale_300dpi.png")
page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False, clip=RIGHT_RECT).save(ROOT / "right_panel_300dpi.png")

text_spans = [s for s in page.get_texttrace() if fitz.Rect(s["bbox"]).intersects(OBJECT_RECT)]
drawings = [d for d in page.get_drawings() if fitz.Rect(d["rect"]).intersects(OBJECT_RECT)]

objects = []
object_masks = {}
span_rows = []
glyph_rows = []
safe_rows = []
glyph_contact_data = []
span_index = 0
glyph_index = 0

for span in text_spans:
    span_index += 1
    object_id = f"T{span_index:03d}"
    seqno = int(span["seqno"])
    bbox_pt = fitz.Rect(span["bbox"])
    bbox = rect_px(bbox_pt)
    panel, role, script_role = role_for_text(seqno, bbox_pt)
    text = "".join(chr(c[0]) for c in span["chars"])
    target_rgb = fitz_color_to_rgb(span["color"])
    x0, y0, x1, y1 = bbox
    crop = page_arr[y0:y1, x0:x1]
    mask = color_line_mask(crop, target_rgb)
    sparse = sparse_crop(mask, bbox)
    object_masks[object_id] = sparse
    objects.append({
        "object_id": object_id,
        "object_kind": "TEXT_SPAN",
        "seqno": seqno,
        "panel": panel,
        "role": role,
        "semantic_parent": f"SEQ{seqno:03d}",
        "text_unicode_escape": text.encode("unicode_escape").decode(),
        "bbox_pt": ",".join(f"{v:.3f}" for v in bbox_pt),
        "bbox_px": ",".join(map(str, bbox)),
        "font": span["font"],
        "declared_or_pdf_pt": f"{float(span['size']):.3f}",
        "raw_mask_pixels": int(mask.sum()),
        "mask_status": "NONEMPTY" if mask.any() else "EMPTY",
        "drawing_type": "",
        "stroke_rgb": target_rgb,
        "fill_rgb": "",
    })
    span_rows.append(objects[-1].copy())

    for char in span["chars"]:
        ch = chr(char[0])
        if ch.isspace():
            continue
        glyph_index += 1
        glyph_id = f"G{glyph_index:03d}"
        char_bbox_pt = fitz.Rect(char[3])
        char_bbox = rect_px(char_bbox_pt)
        cx0, cy0, cx1, cy1 = char_bbox
        ccrop = page_arr[cy0:cy1, cx0:cx1]
        cmask = color_line_mask(ccrop, target_rgb)
        coords = np.argwhere(cmask)
        if coords.size:
            ink_h = int(coords[:, 0].max() - coords[:, 0].min() + 1)
            ink_w = int(coords[:, 1].max() - coords[:, 1].min() + 1)
            ink_area = int(cmask.sum())
        else:
            ink_h = ink_w = ink_area = 0
        category, threshold = glyph_category(ch, float(span["size"]), seqno, char_bbox_pt.y0)
        metric_status = "REFERENCE_REQUIRED" if threshold is None else ("MEETS_NUMERIC" if ink_h >= threshold else "BELOW_NUMERIC_ADVISORY_R168")
        safe_name = f"{glyph_id}.png"
        save_mask_png(ROOT / "masks" / "glyph" / safe_name, cmask)
        row = {
            "glyph_id": glyph_id,
            "parent_object_id": object_id,
            "semantic_parent": f"SEQ{seqno:03d}",
            "seqno": seqno,
            "panel": panel,
            "role": role,
            "char": ch,
            "codepoint": f"U+{ord(ch):04X}",
            "char_unicode_escape": ch.encode("unicode_escape").decode(),
            "font": span["font"],
            "pdf_pt": f"{float(span['size']):.3f}",
            "category": category,
            "r168_hard_font_scope": "missing/tofu/wrong-codepoint/math-semantics/unreadable/severe-imbalance only",
            "numeric_threshold_px": "" if threshold is None else threshold,
            "ink_h_px": ink_h,
            "ink_w_px": ink_w,
            "ink_area_px": ink_area,
            "numeric_status_under_r168": metric_status,
            "bbox_pt": ",".join(f"{v:.3f}" for v in char_bbox_pt),
            "bbox_px": ",".join(map(str, char_bbox)),
            "mask_file": f"masks/glyph/{safe_name}",
            "machine_mask_nonempty": str(bool(cmask.any())).lower(),
        }
        glyph_rows.append(row)
        safe_rows.append({"element_id": glyph_id, "safe_filename": safe_name, "kind": "GLYPH"})
        glyph_contact_data.append((row, ccrop.copy(), cmask.copy()))

draw_rows = []
drawing_replays = {}
for draw_index, drawing in enumerate(drawings, 1):
    object_id = f"D{draw_index:03d}"
    seqno = int(drawing["seqno"])
    bbox_pt = fitz.Rect(drawing["rect"])
    bbox = rect_px(bbox_pt)
    panel, role = DRAW_NAMES.get(seqno, ("FIGURE", "UNCLASSIFIED_DRAWING"))
    replay_full = replay_drawing(page.rect, drawing)
    x0, y0, x1, y1 = bbox
    replay = replay_full[y0:y1, x0:x1]
    drawing_replays[object_id] = sparse_crop(replay.copy(), bbox)
    stroke_rgb = fitz_color_to_rgb(drawing.get("color"))
    fill_rgb = fitz_color_to_rgb(drawing.get("fill"))
    if role.endswith("OPAQUE_BG"):
        final_mask = replay.copy()
        mask_basis = "VECTOR_REPLAY_OPAQUE_BACKGROUND"
    else:
        candidates = []
        if stroke_rgb is not None:
            candidates.append(color_line_mask(page_arr[y0:y1, x0:x1], stroke_rgb))
        if fill_rgb is not None and fill_rgb != (255, 255, 255):
            candidates.append(color_line_mask(page_arr[y0:y1, x0:x1], fill_rgb))
        if candidates:
            final_mask = replay & np.logical_or.reduce(candidates)
            mask_basis = "VECTOR_REPLAY_INTERSECT_FINAL_COLOR"
        else:
            final_mask = replay.copy()
            mask_basis = "VECTOR_REPLAY"
    object_masks[object_id] = sparse_crop(final_mask, bbox)
    save_name = f"{object_id}.png"
    save_mask_png(ROOT / "masks" / "object" / save_name, final_mask)
    row = {
        "object_id": object_id,
        "object_kind": "DRAWING_PATH",
        "seqno": seqno,
        "panel": panel,
        "role": role,
        "semantic_parent": f"DRAWSEQ{seqno:03d}",
        "text_unicode_escape": "",
        "bbox_pt": ",".join(f"{v:.3f}" for v in bbox_pt),
        "bbox_px": ",".join(map(str, bbox)),
        "font": "",
        "declared_or_pdf_pt": "",
        "raw_mask_pixels": int(final_mask.sum()),
        "mask_status": "NONEMPTY" if final_mask.any() else "EMPTY",
        "drawing_type": drawing["type"],
        "stroke_rgb": "" if stroke_rgb is None else stroke_rgb,
        "fill_rgb": "" if fill_rgb is None else fill_rgb,
        "path_item_count": len(drawing["items"]),
        "mask_basis": mask_basis,
        "mask_file": f"masks/object/{save_name}",
    }
    objects.append(row)
    draw_rows.append(row.copy())
    safe_rows.append({"element_id": object_id, "safe_filename": save_name, "kind": "DRAWING"})

# Resolve true final visibility for the right-panel curve. The two white annotation
# backgrounds and the white-filled endpoint marker are later opaque paint objects.
# Their vector replay masks must be removed before assessing curve/text or
# curve/marker intersections; otherwise same-color annotation ink is falsely
# attributed to the pre-occlusion curve.
curve_sparse = object_masks["D011"]
curve_local = curve_sparse["mask"].copy()
for occluder_id in ("D012", "D013", "D014"):
    occ = drawing_replays[occluder_id]
    ix0 = max(curve_sparse["x0"], occ["x0"])
    iy0 = max(curve_sparse["y0"], occ["y0"])
    ix1 = min(curve_sparse["x1"], occ["x1"])
    iy1 = min(curve_sparse["y1"], occ["y1"])
    if ix1 > ix0 and iy1 > iy0:
        cs = curve_local[iy0 - curve_sparse["y0"] : iy1 - curve_sparse["y0"], ix0 - curve_sparse["x0"] : ix1 - curve_sparse["x0"]]
        os = occ["mask"][iy0 - occ["y0"] : iy1 - occ["y0"], ix0 - occ["x0"] : ix1 - occ["x0"]]
        cs &= ~os
object_masks["D011"]["mask"] = curve_local
save_mask_png(ROOT / "masks" / "object" / "D011.png", curve_local)
for row in objects:
    if row["object_id"] == "D011":
        row["raw_mask_pixels"] = int(curve_local.sum())
        row["mask_basis"] = "VECTOR_REPLAY_INTERSECT_FINAL_COLOR_MINUS_LATER_OPAQUE_PAINT"
for row in draw_rows:
    if row["object_id"] == "D011":
        row["raw_mask_pixels"] = int(curve_local.sum())
        row["mask_basis"] = "VECTOR_REPLAY_INTERSECT_FINAL_COLOR_MINUS_LATER_OPAQUE_PAINT"

# get_drawings() omits six live stroke-path sequences that remain visible in the
# PDF bbox sequence: the three legend samples, the two right-axis shafts, and the
# TeX fraction rule. Add them from the official native raster plus bboxlog so the
# actual semantic/drawing denominator and math-rule ledger are complete.
supplement_specs = {
    24: ("LEFT_PANEL", "LEGEND_SAMPLE_RHO_095", (31, 78, 121), "DRAWING_PATH_SUPPLEMENTAL", "DRAWSEQ024"),
    26: ("LEFT_PANEL", "LEGEND_SAMPLE_RHO_070", (15, 118, 110), "DRAWING_PATH_SUPPLEMENTAL", "DRAWSEQ026"),
    28: ("LEFT_PANEL", "LEGEND_SAMPLE_RHO_020", (107, 114, 128), "DRAWING_PATH_SUPPLEMENTAL", "DRAWSEQ028"),
    32: ("RIGHT_PANEL", "X_AXIS_SHAFT", (77, 83, 88), "DRAWING_PATH_SUPPLEMENTAL", "DRAWSEQ032"),
    34: ("RIGHT_PANEL", "Y_AXIS_SHAFT", (77, 83, 88), "DRAWING_PATH_SUPPLEMENTAL", "DRAWSEQ034"),
    54: ("RIGHT_PANEL", "MATH_RULE_FRACTION_BAR", (31, 36, 40), "GRAPHIC_MATH_RULE", "SEQ053_055_FRACTION"),
}
bboxlog = page.get_bboxlog(layers=True)
for supplement_index, (seqno, spec) in enumerate(supplement_specs.items(), 15):
    entry = bboxlog[seqno]
    if entry[0] != "stroke-path":
        raise RuntimeError(f"Expected stroke-path at bboxlog seq {seqno}, got {entry[0]}")
    panel, role, stroke_rgb, object_kind, parent = spec
    object_id = f"D{supplement_index:03d}"
    bbox_pt = fitz.Rect(entry[1])
    bbox = rect_px(bbox_pt)
    x0, y0, x1, y1 = bbox
    final_mask = color_line_mask(page_arr[y0:y1, x0:x1], stroke_rgb)
    if not final_mask.any():
        raise RuntimeError(f"Supplemental path {object_id} seq {seqno} has empty native mask")
    object_masks[object_id] = sparse_crop(final_mask, bbox)
    save_name = f"{object_id}.png"
    save_mask_png(ROOT / "masks" / "object" / save_name, final_mask)
    row = {
        "object_id": object_id,
        "object_kind": object_kind,
        "seqno": seqno,
        "panel": panel,
        "role": role,
        "semantic_parent": parent,
        "text_unicode_escape": "",
        "bbox_pt": ",".join(f"{v:.3f}" for v in bbox_pt),
        "bbox_px": ",".join(map(str, bbox)),
        "font": "",
        "declared_or_pdf_pt": "",
        "raw_mask_pixels": int(final_mask.sum()),
        "mask_status": "NONEMPTY",
        "drawing_type": "bboxlog:stroke-path",
        "stroke_rgb": stroke_rgb,
        "fill_rgb": "",
        "path_item_count": 1,
        "mask_basis": "OFFICIAL_NATIVE_COLOR_MASK_WITH_BBOXLOG_SEQUENCE",
        "mask_file": f"masks/object/{save_name}",
    }
    objects.append(row)
    draw_rows.append(row.copy())
    safe_rows.append({"element_id": object_id, "safe_filename": save_name, "kind": object_kind})

# Dedicated four-view evidence for the one visible TeX math rule.
mr = object_masks["D020"]
pad = 6
mx0, my0, mx1, my1 = max(0,mr["x0"]-pad),max(0,mr["y0"]-pad),min(PAGE_W,mr["x1"]+pad),min(PAGE_H,mr["y1"]+pad)
morig = page_arr[my0:my1,mx0:mx1].copy()
mm = np.zeros((my1-my0,mx1-mx0),dtype=bool)
mm[mr["y0"]-my0:mr["y1"]-my0,mr["x0"]-mx0:mr["x1"]-mx0] = mr["mask"]
mover = morig.copy(); mover[mm]=(255,0,0)
monly = np.where(mm[:,:,None],np.array([0,0,0],dtype=np.uint8),np.array([255,255,255],dtype=np.uint8))
parts=[Image.fromarray(morig),Image.fromarray(mover),Image.fromarray(monly)]
mw,mh=morig.shape[1],morig.shape[0]
mcanvas=Image.new("RGB",(mw*3,mh),"white")
for k,im in enumerate(parts): mcanvas.paste(im,(k*mw,0))
mcanvas.save(ROOT / "contacts" / "math_rule_D020_1x.png")
mcanvas.resize((mcanvas.width*8,mcanvas.height*8),Image.Resampling.NEAREST).save(ROOT / "contacts" / "math_rule_D020_8x_nearest.png")

# Create an annotated overview using object boxes and IDs.
overlay = Image.fromarray(page_arr).crop(rect_px(FIGURE_RECT))
od = ImageDraw.Draw(overlay)
fx0, fy0, _, _ = rect_px(FIGURE_RECT)
try:
    font = ImageFont.truetype("arial.ttf", 14)
except OSError:
    font = ImageFont.load_default()
for o in objects:
    x0, y0, x1, y1 = [int(v) for v in o["bbox_px"].split(",")]
    color = (205, 30, 30) if o["object_kind"] == "TEXT_SPAN" else (20, 80, 210)
    od.rectangle((x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0), outline=color, width=1)
    od.text((x0 - fx0, y0 - fy0 - 14), o["object_id"], fill=color, font=font)
overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

# 8x-nearest targeted right panel is navigation/inspection only; measurements stay 1x.
right_native = Image.open(ROOT / "right_panel_300dpi.png")
right_native.resize((right_native.width * 8, right_native.height * 8), Image.Resampling.NEAREST).save(ROOT / "right_panel_8x_nearest.png")

# Per-glyph ORIGINAL / TARGET OVERLAY / MASK ONLY contact sheets at actual 8x nearest.
CELL_W, CELL_H = 520, 210
COLS, ROWS = 5, 4
for sheet_idx in range(math.ceil(len(glyph_contact_data) / (COLS * ROWS))):
    sheet = Image.new("RGB", (CELL_W * COLS, CELL_H * ROWS), "white")
    sd = ImageDraw.Draw(sheet)
    subset = glyph_contact_data[sheet_idx * COLS * ROWS : (sheet_idx + 1) * COLS * ROWS]
    for j, (row, crop_arr, cmask) in enumerate(subset):
        col, rr = j % COLS, j // COLS
        ox, oy = col * CELL_W, rr * CELL_H
        h, w = cmask.shape
        pad = 4
        padded = np.full((h + 2 * pad, w + 2 * pad, 3), 255, dtype=np.uint8)
        padded[pad : pad + h, pad : pad + w] = crop_arr
        pmask = np.zeros((h + 2 * pad, w + 2 * pad), dtype=bool)
        pmask[pad : pad + h, pad : pad + w] = cmask
        original = Image.fromarray(padded).resize((padded.shape[1] * 8, padded.shape[0] * 8), Image.Resampling.NEAREST)
        over_arr = padded.copy()
        over_arr[pmask] = (255, 0, 0)
        over = Image.fromarray(over_arr).resize((padded.shape[1] * 8, padded.shape[0] * 8), Image.Resampling.NEAREST)
        mask_arr = np.where(pmask[:, :, None], np.array([0, 0, 0], dtype=np.uint8), np.array([255, 255, 255], dtype=np.uint8))
        monly = Image.fromarray(mask_arr).resize((padded.shape[1] * 8, padded.shape[0] * 8), Image.Resampling.NEAREST)
        max_w = 160
        views = []
        for im in (original, over, monly):
            if im.width > max_w or im.height > 130:
                ratio = min(max_w / im.width, 130 / im.height)
                # The display fit is secondary; the embedded source is already exact 8x nearest.
                im = im.resize((max(1, int(im.width * ratio)), max(1, int(im.height * ratio))), Image.Resampling.NEAREST)
            views.append(im)
        for k, im in enumerate(views):
            sheet.paste(im, (ox + 4 + k * 170, oy + 48))
        label = f"{row['glyph_id']} {row['codepoint']} {row['char_unicode_escape']} H={row['ink_h_px']} role={row['role']}"
        sd.text((ox + 4, oy + 4), label, fill=(0, 0, 0), font=font)
        sd.text((ox + 4, oy + 25), "ORIGINAL            TARGET OVERLAY      MASK ONLY", fill=(0, 0, 0), font=font)
    out_name = f"glyph_contact_{sheet_idx + 1:03d}.png"
    sheet.save(ROOT / "contacts" / out_name)
    for j, (row, _, _) in enumerate(subset):
        row["contact_sheet"] = f"contacts/{out_name}"
        row["contact_cell"] = j + 1

# All unordered semantic/drawing pairs. Preserve the already-inspected legacy
# P-IDs for the original 88-object denominator; supplemental-path pairs receive
# stable S-IDs so prior manual decisions are not silently remapped.
legacy_object_ids = [f"T{i:03d}" for i in range(1, 75)] + [f"D{i:03d}" for i in range(1, 15)]
legacy_map = {}
for legacy_index, (la, lb) in enumerate(itertools.combinations(legacy_object_ids, 2), 1):
    legacy_map[(la, lb)] = f"P{legacy_index:04d}"
pair_rows = []
critical_machine_rows = []
supplement_pair_index = 0
for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
    aid, bid = a["object_id"], b["object_id"]
    abox = tuple(int(v) for v in a["bbox_px"].split(","))
    bbox = tuple(int(v) for v in b["bbox_px"].split(","))
    bgap = bbox_gap(abox, bbox)
    overlap = sparse_intersection(object_masks[aid], object_masks[bid])
    if bgap <= 64 or overlap:
        clearance = sparse_clearance(object_masks[aid], object_masks[bid])
    else:
        clearance = float("nan")
    same_parent = a["semantic_parent"] == b["semantic_parent"]
    relation_class = (
        "SAME_SEMANTIC_PARENT_DESIGN" if same_parent else
        "OPAQUE_BACKGROUND_RELATION" if ("OPAQUE_BG" in a["role"] or "OPAQUE_BG" in b["role"]) else
        "INDEPENDENT_OBJECTS"
    )
    pair_id = legacy_map.get((aid, bid))
    if pair_id is None:
        supplement_pair_index += 1
        pair_id = f"S{supplement_pair_index:04d}"
    row = {
        "pair_id": pair_id,
        "object_a": aid,
        "object_b": bid,
        "a_kind": a["object_kind"],
        "b_kind": b["object_kind"],
        "a_role": a["role"],
        "b_role": b["role"],
        "relation_class": relation_class,
        "bbox_gap_px": f"{bgap:.3f}",
        "raw_final_mask_intersection_px": overlap,
        "raw_final_mask_clearance_px": "" if math.isnan(clearance) else f"{clearance:.3f}",
        "machine_critical_candidate": str(bool(overlap or (not math.isnan(clearance) and clearance < 12))).lower(),
    }
    pair_rows.append(row)
    if row["machine_critical_candidate"] == "true":
        critical_machine_rows.append(row.copy())

# Native 1x and exact 8x-nearest evidence for every machine-critical relation.
for row in critical_machine_rows:
    a = object_masks[row["object_a"]]
    b = object_masks[row["object_b"]]
    ux0 = max(0, min(a["x0"], b["x0"]) - 2)
    uy0 = max(0, min(a["y0"], b["y0"]) - 2)
    ux1 = min(PAGE_W, max(a["x1"], b["x1"]) + 2)
    uy1 = min(PAGE_H, max(a["y1"], b["y1"]) + 2)
    ua = np.zeros((uy1 - uy0, ux1 - ux0), dtype=bool)
    ub = np.zeros_like(ua)
    ua[a["y0"] - uy0 : a["y1"] - uy0, a["x0"] - ux0 : a["x1"] - ux0] = a["mask"]
    ub[b["y0"] - uy0 : b["y1"] - uy0, b["x0"] - ux0 : b["x1"] - ux0] = b["mask"]
    ui = ua & ub
    if np.any(ui):
        pts = np.argwhere(ui)
        cy, cx = np.median(pts, axis=0)
    else:
        dist, nearest = distance_transform_edt(~ua, return_indices=True)
        bpts = np.argwhere(ub)
        vals = dist[ub]
        k = int(np.argmin(vals))
        by, bx = bpts[k]
        ay, ax = nearest[:, by, bx]
        cy, cx = (ay + by) / 2, (ax + bx) / 2
    cx, cy = int(round(cx + ux0)), int(round(cy + uy0))
    half = 80
    x0 = max(0, cx - half)
    y0 = max(0, cy - half)
    x1 = min(PAGE_W, cx + half)
    y1 = min(PAGE_H, cy + half)
    original = page_arr[y0:y1, x0:x1].copy()
    am = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bm = np.zeros_like(am)
    aix0, aiy0, aix1, aiy1 = max(x0,a["x0"]),max(y0,a["y0"]),min(x1,a["x1"]),min(y1,a["y1"])
    bix0, biy0, bix1, biy1 = max(x0,b["x0"]),max(y0,b["y0"]),min(x1,b["x1"]),min(y1,b["y1"])
    if aix1 > aix0 and aiy1 > aiy0:
        am[aiy0-y0:aiy1-y0,aix0-x0:aix1-x0] = a["mask"][aiy0-a["y0"]:aiy1-a["y0"],aix0-a["x0"]:aix1-a["x0"]]
    if bix1 > bix0 and biy1 > biy0:
        bm[biy0-y0:biy1-y0,bix0-x0:bix1-x0] = b["mask"][biy0-b["y0"]:biy1-b["y0"],bix0-b["x0"]:bix1-b["x0"]]
    inter = am & bm
    overlay_arr = original.copy()
    overlay_arr[am & ~bm] = (255, 0, 0)
    overlay_arr[bm & ~am] = (0, 80, 255)
    overlay_arr[inter] = (255, 0, 255)
    h, w = am.shape
    canvas = Image.new("RGB", (w * 2, h), "white")
    canvas.paste(Image.fromarray(original), (0, 0))
    canvas.paste(Image.fromarray(overlay_arr), (w, 0))
    one_name = f"{row['pair_id']}_1x.png"
    eight_name = f"{row['pair_id']}_8x_nearest.png"
    canvas.save(ROOT / "roi" / one_name)
    canvas.resize((canvas.width * 8, canvas.height * 8), Image.Resampling.NEAREST).save(ROOT / "roi" / eight_name)
    row["roi_page_px"] = f"{x0},{y0},{x1},{y1}"
    row["native_1x_file"] = f"roi/{one_name}"
    row["nearest_8x_file"] = f"roi/{eight_name}"

# Role metrics remain descriptive/advisory under R168 unless visibly unreadable/severely imbalanced.
role_groups = {}
for g in glyph_rows:
    if g["ink_h_px"] <= 0:
        continue
    key = (g["panel"], g["role"], g["category"])
    role_groups.setdefault(key, []).append(int(g["ink_h_px"]))
role_rows = []
for idx, (key, vals) in enumerate(sorted(role_groups.items()), 1):
    med = float(np.median(vals))
    role_rows.append({
        "role_metric_id": f"RM{idx:03d}",
        "panel": key[0],
        "role": key[1],
        "category": key[2],
        "count": len(vals),
        "min_h_px": min(vals),
        "median_h_px": f"{med:.3f}",
        "max_h_px": max(vals),
        "max_min_ratio": f"{max(vals)/min(vals):.4f}" if min(vals) else "INF",
        "r168_status": "ADVISORY_METRIC_REQUIRES_MANUAL_HARD_SCOPE_JUDGMENT",
    })

# Source-level declarations, no TeX execution.
source_text = SOURCE.read_text(encoding="utf-8")
source_font_rows = [
    {"source_id": "SF01", "selector": "tick label style", "declared_pt": "9.6", "graphics_scale": "1.0", "effective_pt": "9.6", "status": "MEETS_9.5"},
    {"source_id": "SF02", "selector": "label style", "declared_pt": "9.8", "graphics_scale": "1.0", "effective_pt": "9.8", "status": "MEETS_9.5"},
    {"source_id": "SF03", "selector": "title style", "declared_pt": "9.6", "graphics_scale": "1.0", "effective_pt": "9.6", "status": "MEETS_9.5"},
    {"source_id": "SF04", "selector": "left legend style", "declared_pt": "9.6", "graphics_scale": "1.0", "effective_pt": "9.6", "status": "MEETS_9.5"},
    {"source_id": "SF05", "selector": "right point annotation node", "declared_pt": "9.6", "graphics_scale": "1.0", "effective_pt": "9.6", "status": "MEETS_9.5"},
    {"source_id": "SF06", "selector": "right limit annotation node", "declared_pt": "9.6", "graphics_scale": "1.0", "effective_pt": "9.6", "status": "MEETS_9.5"},
    {"source_id": "SF07", "selector": "caption inherited current PDF", "declared_pt": "9.96_pdf", "graphics_scale": "1.0", "effective_pt": "9.96", "status": "MEETS_9.5"},
]

write_csv(ROOT / "machine_span_inventory.csv", list(span_rows[0].keys()), span_rows)
write_csv(ROOT / "machine_glyph_inventory.csv", list(glyph_rows[0].keys()), glyph_rows)
write_csv(ROOT / "machine_drawing_inventory.csv", list(draw_rows[0].keys()), draw_rows)
write_csv(ROOT / "machine_object_inventory.csv", list(objects[0].keys()) + [k for k in draw_rows[0].keys() if k not in objects[0]], objects)
write_csv(ROOT / "machine_all_pairs.csv", list(pair_rows[0].keys()), pair_rows)
write_csv(ROOT / "machine_critical_candidates.csv", list(pair_rows[0].keys()), critical_machine_rows)
write_csv(ROOT / "machine_role_metrics.csv", list(role_rows[0].keys()), role_rows)
write_csv(ROOT / "source_font_audit.csv", list(source_font_rows[0].keys()), source_font_rows)
write_csv(ROOT / "id_safe_filename.csv", ["element_id", "safe_filename", "kind"], safe_rows)
write_csv(ROOT / "after_font_audit.csv", list(source_font_rows[0].keys()), source_font_rows)
write_csv(ROOT / "after_pixel_measurements.csv", list(glyph_rows[0].keys()), glyph_rows)
write_csv(ROOT / "after_overlap_report.csv", list(pair_rows[0].keys()), pair_rows)

pdf_hash = hashlib.sha256(PDF.read_bytes()).hexdigest().upper()
identity = {
    "uid": "FIG-P640-01",
    "handoff_id": "C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-V1",
    "agent": "/root/sa1_fig_p640_r106_fresh_isolated",
    "fork_turns": "none",
    "model": "gpt-5.4",
    "reasoning_effort": "xhigh",
    "official_pdf": str(PDF),
    "pdf_pages": doc.page_count,
    "pdf_bytes": PDF.stat().st_size,
    "pdf_sha256": pdf_hash,
    "physical_page": PHYSICAL_PAGE,
    "printed_page": 677,
    "figure_number": "33.7",
    "label": "fig:V5-C04-mixing-rho-comparison",
    "source": str(SOURCE),
    "chapter": str(CHAPTER),
    "page_pt": [page.rect.width, page.rect.height],
    "full_page_300dpi_native_px": [PAGE_W, PAGE_H],
    "full_page_200dpi_native_px": list(Image.open(ROOT / "full_page_200dpi.png").size),
    "figure_rect_pt": list(FIGURE_RECT),
    "figure_crop_300dpi_native_px": list(Image.open(ROOT / "figure_crop_300dpi.png").size),
    "figure_crop_integer_page_px": list(rect_px(FIGURE_RECT)),
    "body_rect_pt": list(BODY_RECT),
    "standalone_300dpi_native_px": list(Image.open(ROOT / "standalone_300dpi.png").size),
    "standalone_integer_page_px": list(rect_px(BODY_RECT)),
    "right_rect_pt": list(RIGHT_RECT),
    "right_panel_300dpi_native_px": list(Image.open(ROOT / "right_panel_300dpi.png").size),
    "right_panel_integer_page_px": list(rect_px(RIGHT_RECT)),
    "rawdict_preliminary_spans": 80,
    "rawdict_preliminary_char_records_including_whitespace": 263,
    "sequence_reconciled_text_spans": len(text_spans),
    "nonwhitespace_glyphs": len(glyph_rows),
    "get_drawings_path_records": len(drawings),
    "bboxlog_supplemental_path_records": len(supplement_specs),
    "drawing_paths": len(draw_rows),
    "math_rule_objects": 1,
    "semantic_drawing_object_denominator": len(objects),
    "unordered_pair_denominator": len(pair_rows),
    "expected_unordered_pair_denominator": len(objects) * (len(objects) - 1) // 2,
    "machine_critical_candidate_count": len(critical_machine_rows),
    "source_contains_expected_uid": "% v2.7.0 figure UID: FIG-P640-01" in source_text,
    "source_contains_expected_label": "\\label{fig:V5-C04-mixing-rho-comparison}" in source_text,
}
(ROOT / "resolved_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

machine_summary = {
    "counts": {
        "text_spans": len(text_spans),
        "glyphs": len(glyph_rows),
        "get_drawings_path_records": len(drawings),
        "bboxlog_supplemental_path_records": len(supplement_specs),
        "drawings": len(draw_rows),
        "math_rule_objects": 1,
        "objects": len(objects),
        "all_unordered_pairs": len(pair_rows),
        "critical_candidates": len(critical_machine_rows),
        "empty_glyph_masks": sum(g["machine_mask_nonempty"] != "true" for g in glyph_rows),
        "empty_object_masks": sum(o["mask_status"] == "EMPTY" for o in objects),
        "pair_raw_intersection_nonzero": sum(int(p["raw_final_mask_intersection_px"]) > 0 for p in pair_rows),
        "numeric_glyph_below_advisory": sum(g["numeric_status_under_r168"] == "BELOW_NUMERIC_ADVISORY_R168" for g in glyph_rows),
        "contact_sheets": len(list((ROOT / "contacts").glob("glyph_contact_*.png"))),
        "ordinary_glyph_mask_png": len(list((ROOT / "masks" / "glyph").glob("*.png"))),
        "ordinary_drawing_mask_png": len(list((ROOT / "masks" / "object").glob("*.png"))),
    },
    "r168": "Numeric/micro-ratio metadata are advisory; hard font scope is missing/tofu/wrong glyph or codepoint/math semantics, actual unreadability, obvious severe imbalance, real clipping, or illegal overlap.",
}
(ROOT / "machine_summary.json").write_text(json.dumps(machine_summary, ensure_ascii=False, indent=2), encoding="utf-8")

doc.close()
print(json.dumps(identity, ensure_ascii=False, indent=2))
print(json.dumps(machine_summary, ensure_ascii=False, indent=2))
