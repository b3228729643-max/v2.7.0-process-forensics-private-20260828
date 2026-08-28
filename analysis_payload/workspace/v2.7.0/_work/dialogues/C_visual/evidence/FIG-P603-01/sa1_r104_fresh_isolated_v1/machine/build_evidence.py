from __future__ import annotations

import csv
import json
import math
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_acceptance_function.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P603-01\sa1_r104_fresh_isolated_v1")
PAGE_INDEX = 654
DPI = 300
PT_SCALE = DPI / 72.0

RENDER = ROOT / "render"
MACHINE = ROOT / "machine"
GLYPH_MASK_DIR = ROOT / "masks" / "glyph"
OBJECT_MASK_DIR = ROOT / "masks" / "object"
CONTACT = ROOT / "contact"
PAIR_DIR = ROOT / "pairs"

for d in (RENDER, MACHINE, GLYPH_MASK_DIR, OBJECT_MASK_DIR, CONTACT / "glyph_cards", CONTACT / "glyph_sheets", CONTACT / "math_rules", PAIR_DIR):
    d.mkdir(parents=True, exist_ok=True)

PAGE_PNG = RENDER / "full_page_300dpi.png"
if not PAGE_PNG.exists():
    raise SystemExit(f"missing Poppler native render: {PAGE_PNG}")

page_image = Image.open(PAGE_PNG).convert("RGB")
page_np = np.asarray(page_image)
doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_w_pt = float(page.rect.width)
page_h_pt = float(page.rect.height)
page_w_px, page_h_px = page_image.size
sx = page_w_px / page_w_pt
sy = page_h_px / page_h_pt


def pt_rect_to_px(rect):
    x0, y0, x1, y1 = [float(v) for v in rect]
    return (
        max(0, int(math.floor(x0 * sx))),
        max(0, int(math.floor(y0 * sy))),
        min(page_w_px, int(math.ceil(x1 * sx))),
        min(page_h_px, int(math.ceil(y1 * sy))),
    )


def rgb_from_int(color: int):
    return np.array([(color >> 16) & 255, (color >> 8) & 255, color & 255], dtype=np.float64)


def safe_name(value: str):
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return s.strip("._") or "item"


STANDALONE_PT = (108.0, 507.0, 479.0, 657.0)
FIGURE_CROP_PT = (57.0, 507.0, 527.0, 691.0)
standalone_px = pt_rect_to_px(STANDALONE_PT)
figure_crop_px = pt_rect_to_px(FIGURE_CROP_PT)

standalone = page_image.crop(standalone_px)
figure_crop = page_image.crop(figure_crop_px)
standalone.save(RENDER / "standalone_300dpi.png")
figure_crop.save(RENDER / "figure_crop_300dpi.png")
standalone.convert("L").save(RENDER / "grayscale_300dpi.png")


def text_object_for(block_no: int, char_bbox):
    x0, y0, x1, y1 = char_bbox
    if block_no == 19:
        return "T01_X_TICK_LABELS" if y0 >= 630 else "T02_Y_TICK_LABELS"
    return {
        20: "T02_Y_TICK_LABELS",
        21: "T02_Y_TICK_LABELS",
        22: "T03_LEFT_ANNOTATION",
        23: "T03_LEFT_ANNOTATION",
        24: "T04_RIGHT_ANNOTATION",
        25: "T05_FOLDPOINT_LABEL",
        26: "T06_X_AXIS_LABEL",
        27: "T07_Y_AXIS_LABEL",
        28: "T08_GENERAL_RATIO_FORMULA",
        29: "T08_GENERAL_RATIO_FORMULA",
        30: "T09_INDEPENDENT_RATIO_ANNOTATION",
        31: "T09_INDEPENDENT_RATIO_ANNOTATION",
        32: "T10_CAPTION_LABEL" if (x1 <= 94.0 and y0 < 675.0) else "T11_CAPTION_BODY",
    }.get(block_no)


TEXT_OBJECT_META = {
    "T01_X_TICK_LABELS": ("tick_label", "math", "0 1 2 3", 8.5),
    "T02_Y_TICK_LABELS": ("tick_label", "math", "0 0.5 1", 8.5),
    "T03_LEFT_ANNOTATION": ("annotation", "mixed", "r<1：按比例接受", 9.2),
    "T04_RIGHT_ANNOTATION": ("annotation", "mixed", "r≥1：必然接受", 9.2),
    "T05_FOLDPOINT_LABEL": ("annotation", "cjk", "折点", 9.2),
    "T06_X_AXIS_LABEL": ("axis_label", "math", "r", 9.2),
    "T07_Y_AXIS_LABEL": ("axis_label", "math", "α(x,y)", 9.2),
    "T08_GENERAL_RATIO_FORMULA": ("formula", "math", "r=π(y)q(y,x)/π(x)q(x,y)", 9.2),
    "T09_INDEPENDENT_RATIO_ANNOTATION": ("formula_annotation", "mixed", "独立提议：r=w(y)/w(x)", 9.2),
    "T10_CAPTION_LABEL": ("caption_label", "mixed", "图32.6", None),
    "T11_CAPTION_BODY": ("caption", "mixed", "MH接受概率是比值r的截断函数α=min{1,r}，其中r=π(y)q(y,x)/[π(x)q(x,y)]；独立提议时可写为r=w(y)/w(x)", None),
}


def is_cjk(ch):
    cp = ord(ch)
    return (
        0x3400 <= cp <= 0x4DBF
        or 0x4E00 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x3000 <= cp <= 0x303F
        or 0xFF00 <= cp <= 0xFFEF
    )


LOW_PUNCT = set(".,，。；：、·…")


def glyph_class(ch):
    if ch in "+-=<>/−≥≤":
        return "BASE_MATH_OR_OPERATOR", 22
    if ch in LOW_PUNCT:
        return "LOW_PROFILE_PUNCTUATION", None
    cat = unicodedata.category(ch)
    if is_cjk(ch):
        return "CJK_FULL", 30
    if ch.isdigit() or (ch.isascii() and ch.isupper()):
        return "LATIN_UPPER_OR_DIGIT", 24
    name = unicodedata.name(ch, "")
    if (ch.isascii() and ch.islower()) or "SMALL" in name or "GREEK" in name:
        return "LOWER_OR_GREEK", 17
    if cat.startswith("P") and ch not in "()[]{}":
        return "LOW_PROFILE_PUNCTUATION", None
    return "BASE_MATH_OR_OPERATOR", 22


def estimate_bg(px_rect):
    x0, y0, x1, y1 = px_rect
    pad = 3
    crop = page_np[max(0, y0-pad):min(page_h_px, y1+pad), max(0, x0-pad):min(page_w_px, x1+pad)]
    flat = crop.reshape(-1, 3)
    quant = (flat // 8).astype(np.int16)
    keys = quant[:, 0] * 1024 + quant[:, 1] * 32 + quant[:, 2]
    mode_key = Counter(keys.tolist()).most_common(1)[0][0]
    selected = flat[keys == mode_key]
    return np.median(selected, axis=0).astype(np.float64)


def glyph_mask_for(px_rect, fg):
    x0, y0, x1, y1 = px_rect
    crop = page_np[y0:y1, x0:x1].astype(np.float64)
    bg = estimate_bg(px_rect)
    v = fg - bg
    denom = float(np.dot(v, v))
    if denom < 1:
        return np.zeros((y1-y0, x1-x0), dtype=bool), bg
    delta = crop - bg
    alpha = np.tensordot(delta, v, axes=([2], [0])) / denom
    recon = bg + np.clip(alpha, 0, 1.2)[..., None] * v
    residual = np.linalg.norm(crop - recon, axis=2)
    contrast = np.max(np.abs(delta), axis=2)
    mask = (contrast >= 20.0) & (alpha >= 0.045) & (alpha <= 1.25) & (residual <= 42.0)
    return mask, bg


glyph_rows = []
object_full_masks = {k: np.zeros((page_h_px, page_w_px), dtype=bool) for k in TEXT_OBJECT_META}
space_exclusions = []
glyph_counter = 0
raw = page.get_text("rawdict")
for block in raw["blocks"]:
    bno = block.get("number", -1)
    if bno < 19 or bno > 32:
        continue
    for line_idx, line in enumerate(block.get("lines", [])):
        for span_idx, span in enumerate(line.get("spans", [])):
            fg = rgb_from_int(span.get("color", 0))
            for char_idx, char in enumerate(span.get("chars", [])):
                ch = char.get("c", "")
                bbox = tuple(float(v) for v in char["bbox"])
                obj = text_object_for(bno, bbox)
                if obj is None:
                    continue
                if ch.isspace() or unicodedata.category(ch) == "Zs":
                    space_exclusions.append({"block": bno, "line": line_idx, "span": span_idx, "char": char_idx, "bbox_pt": bbox, "reason": "non-visible spacing glyph"})
                    continue
                glyph_counter += 1
                gid = f"C{glyph_counter:03d}"
                safe = f"{gid}_{safe_name(obj)}_U{ord(ch):04X}"
                px_rect = pt_rect_to_px(bbox)
                local_mask, bg = glyph_mask_for(px_rect, fg)
                x0, y0, x1, y1 = px_rect
                object_full_masks[obj][y0:y1, x0:x1] |= local_mask
                mask_img = Image.fromarray((local_mask.astype(np.uint8) * 255), mode="L")
                mask_path = GLYPH_MASK_DIR / f"{safe}.png"
                mask_img.save(mask_path)
                ys, xs = np.where(local_mask)
                page_ink_h = int(ys.max() - ys.min() + 1) if len(ys) else 0
                ink_w = int(xs.max() - xs.min() + 1) if len(xs) else 0
                line_dir = tuple(float(v) for v in line.get("dir", (1.0, 0.0)))
                rotated_quarter_turn = abs(line_dir[0]) < 0.1 and abs(line_dir[1]) > 0.9
                ink_h = ink_w if rotated_quarter_turn else page_ink_h
                area = int(local_mask.sum())
                gclass, threshold = glyph_class(ch)
                machine_threshold = "NA_LOW_PUNCT" if threshold is None else ("MEETS" if ink_h >= threshold else "BELOW")
                glyph_rows.append({
                    "glyph_id": gid,
                    "safe_filename": safe,
                    "element_id": obj,
                    "char": ch,
                    "unicode": f"U+{ord(ch):04X}",
                    "unicode_name": unicodedata.name(ch, "UNNAMED"),
                    "block": bno,
                    "line_index": line_idx,
                    "span_index": span_idx,
                    "char_index": char_idx,
                    "font": span.get("font"),
                    "pdf_size_pt": round(float(span.get("size", 0)), 4),
                    "source_declared_pt": TEXT_OBJECT_META[obj][3],
                    "bbox_pt": [round(v, 4) for v in bbox],
                    "bbox_px": list(px_rect),
                    "line_direction": [round(v, 4) for v in line_dir],
                    "orientation": "ROTATED_90" if rotated_quarter_turn else "HORIZONTAL",
                    "fg_rgb": [int(v) for v in fg],
                    "bg_rgb_estimate": [int(round(v)) for v in bg],
                    "page_vertical_ink_span_px": page_ink_h,
                    "ink_height_px": ink_h,
                    "ink_width_px": ink_w,
                    "ink_area_px": area,
                    "glyph_class": gclass,
                    "threshold_px": threshold,
                    "machine_threshold_status": machine_threshold,
                    "mask_path": str(mask_path.resolve()),
                    "mask_nonempty": bool(area),
                })


GRAPHIC_META = {
    # Every foreground drawing is mapped to its exact PyMuPDF drawing index on
    # physical page 655.  The pale filled acceptance region (drawing 14) is a
    # background field and is separately excluded from the foreground-pair
    # universe in the machine inventory.
    "G01_X_TICKS": ("tick_lines", 8, (128, 128, 128), 70),
    "G02_Y_TICKS": ("tick_lines", 9, (128, 128, 128), 70),
    "G03_X_AXIS_LINE": ("axis_line", 10, (31, 35, 40), 90),
    "G04_X_AXIS_ARROWHEAD": ("arrowhead", 11, (31, 35, 40), 90),
    "G05_Y_AXIS_LINE": ("axis_line", 12, (31, 35, 40), 90),
    "G06_Y_AXIS_ARROWHEAD": ("arrowhead", 13, (31, 35, 40), 90),
    "G07_CURVE_R_LT_1": ("data_curve", 15, (31, 78, 121), 95),
    "G08_CURVE_R_GE_1": ("data_curve", 16, (31, 78, 121), 95),
    "G09_THRESHOLD_GUIDE_DASHED": ("guide_line", 17, (107, 114, 128), 85),
    "G10_FOLD_MARKER": ("marker", 18, (183, 121, 31), 105),
    "G11_FORMULA_FRAME_BORDER": ("node_border", 19, (184, 192, 200), 70),
    "G12_GENERAL_FRACTION_RULE": ("math_rule", 20, (31, 35, 40), 90),
    "G13_INDEPENDENT_FRACTION_RULE": ("math_rule", 21, (31, 35, 40), 90),
}


def pxy(point):
    return (int(round(float(point.x) * sx)), int(round(float(point.y) * sy)))


def geometric_mask_for_drawing(drawing, role):
    geom = Image.new("L", (page_w_px, page_h_px), 0)
    gd = ImageDraw.Draw(geom)
    width = max(1, int(math.ceil(float(drawing.get("width") or 0.8) * max(sx, sy))) + 3)
    rect = drawing["rect"]
    rpx = pt_rect_to_px(rect)
    if role == "marker":
        gd.ellipse((rpx[0]-2, rpx[1]-2, rpx[2]+2, rpx[3]+2), fill=255)
        return np.asarray(geom) > 0
    if role == "node_border":
        radius = max(3, int(round(2.0 * sx)))
        gd.rounded_rectangle((rpx[0]-2, rpx[1]-2, rpx[2]+2, rpx[3]+2), radius=radius, outline=255, width=width)
        return np.asarray(geom) > 0
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            gd.line([pxy(item[1]), pxy(item[2])], fill=255, width=width)
        elif op == "c":
            # Dense cubic sampling keeps the native-raster selection confined
            # to the actual Bezier path while the original Poppler pixels,
            # not this helper geometry, remain the final raw mask.
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            pts = []
            for j in range(41):
                t = j / 40.0
                u = 1.0 - t
                x = u**3*p0.x + 3*u*u*t*p1.x + 3*u*t*t*p2.x + t**3*p3.x
                y = u**3*p0.y + 3*u*u*t*p1.y + 3*u*t*t*p2.y + t**3*p3.y
                pts.append((int(round(x*sx)), int(round(y*sy))))
            gd.line(pts, fill=255, width=width)
    if drawing["type"] in ("f", "fs") and role == "arrowhead":
        pts = []
        for item in drawing["items"]:
            if item[0] == "l":
                pts.extend([pxy(item[1]), pxy(item[2])])
        if pts:
            gd.polygon(pts, fill=255)
    return np.asarray(geom) > 0


graphic_rows = []
page_drawings = page.get_drawings()
for gid, (role, drawing_index, color, tolerance) in GRAPHIC_META.items():
    drawing = page_drawings[drawing_index]
    geom = geometric_mask_for_drawing(drawing, role)
    target = np.array(color, dtype=np.float64)
    pixels = page_np.astype(np.float64)
    dist = np.linalg.norm(pixels - target, axis=2)
    contrast = np.max(255.0 - pixels, axis=2)
    full = geom & (dist <= tolerance) & (contrast >= 20)
    object_full_masks[gid] = full
    ys, xs = np.where(full)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)] if len(xs) else [0, 0, 0, 0]
    local = full[bbox[1]:bbox[3], bbox[0]:bbox[2]] if len(xs) else np.zeros((1, 1), dtype=bool)
    path = OBJECT_MASK_DIR / f"{gid}.png"
    Image.fromarray(local.astype(np.uint8)*255, mode="L").save(path)
    graphic_rows.append({
        "graphic_id": gid,
        "safe_filename": gid,
        "role": role,
        "source_drawing_mapping": {"page_drawing_index": drawing_index, "drawing_rect_pt": [round(float(v), 4) for v in drawing["rect"]], "drawing_item_count": len(drawing["items"])},
        "bbox_px": bbox,
        "mask_area_px": int(full.sum()),
        "mask_nonempty": bool(full.any()),
        "target_rgb": color,
        "color_tolerance": tolerance,
        "mask_path": str(path.resolve()),
    })

# Save text object masks after glyph accumulation.
object_rows = []
for oid, (role, script, content, declared) in TEXT_OBJECT_META.items():
    full = object_full_masks[oid]
    ys, xs = np.where(full)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)] if len(xs) else [0, 0, 0, 0]
    local = full[bbox[1]:bbox[3], bbox[0]:bbox[2]] if len(xs) else np.zeros((1, 1), dtype=bool)
    path = OBJECT_MASK_DIR / f"{oid}.png"
    Image.fromarray(local.astype(np.uint8)*255, mode="L").save(path)
    object_rows.append({
        "object_id": oid,
        "kind": "TEXT",
        "role": role,
        "script": script,
        "content": content,
        "source_declared_pt": declared,
        "graphics_scale": 1.0,
        "effective_pt": declared,
        "bbox_px": bbox,
        "mask_area_px": int(full.sum()),
        "mask_nonempty": bool(full.any()),
        "mask_path": str(path.resolve()),
    })
for row in graphic_rows:
    object_rows.append({
        "object_id": row["graphic_id"],
        "kind": "GRAPHIC",
        "role": row["role"],
        "script": "NA",
        "content": row["graphic_id"],
        "source_declared_pt": None,
        "graphics_scale": None,
        "effective_pt": None,
        "bbox_px": row["bbox_px"],
        "mask_area_px": row["mask_area_px"],
        "mask_nonempty": row["mask_nonempty"],
        "mask_path": row["mask_path"],
    })


def write_csv(path, rows):
    if not rows:
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            out = {k: (json.dumps(v, ensure_ascii=False, separators=(",", ":")) if isinstance(v, (list, dict, tuple)) else v) for k, v in row.items()}
            w.writerow(out)


write_csv(MACHINE / "glyph_inventory_machine.csv", glyph_rows)
write_csv(MACHINE / "graphic_inventory_machine.csv", graphic_rows)
write_csv(MACHINE / "object_inventory_machine.csv", object_rows)
(MACHINE / "glyph_inventory_machine.json").write_text(json.dumps(glyph_rows, ensure_ascii=False, indent=2), encoding="utf-8")
(MACHINE / "graphic_inventory_machine.json").write_text(json.dumps(graphic_rows, ensure_ascii=False, indent=2), encoding="utf-8")
(MACHINE / "object_inventory_machine.json").write_text(json.dumps(object_rows, ensure_ascii=False, indent=2), encoding="utf-8")
(MACHINE / "space_exclusions.json").write_text(json.dumps(space_exclusions, ensure_ascii=False, indent=2), encoding="utf-8")


# Object overlay using native page pixels; drawing annotations are machine labels only.
overlay = page_image.copy()
draw = ImageDraw.Draw(overlay)
colors = [(220,20,60),(0,128,255),(0,160,80),(255,128,0),(128,0,200)]
for idx, row in enumerate(object_rows):
    x0, y0, x1, y1 = row["bbox_px"]
    c = colors[idx % len(colors)]
    draw.rectangle((x0, y0, max(x0, x1-1), max(y0, y1-1)), outline=c, width=2)
    draw.text((x0+2, max(0, y0-14)), row["object_id"], fill=c)
overlay.crop(figure_crop_px).save(RENDER / "text_and_object_overlay_300dpi.png")


def mask_bbox(mask):
    ys, xs = np.where(mask)
    return (int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)) if len(xs) else (0, 0, 0, 0)


def pair_required_clearance(a, b):
    ka, kb = a["kind"], b["kind"]
    ra, rb = a["role"], b["role"]
    if ka == kb == "TEXT":
        return 4, "TEXT-TEXT"
    if "TEXT" in (ka, kb):
        gr = rb if ka == "TEXT" else ra
        if gr == "node_border":
            return 5, "TEXT-NODE_BORDER"
        if gr in ("axis_line", "arrowhead", "tick_lines", "data_curve", "guide_line", "marker", "math_rule"):
            return 3, "TEXT-LINE_ARROW_MARKER"
    return 0, "GRAPHIC-GRAPHIC_OR_NA"


pair_rows = []
critical_ids = []
for ia, a in enumerate(object_rows):
    ma = object_full_masks[a["object_id"]]
    for ib in range(ia+1, len(object_rows)):
        b = object_rows[ib]
        mb = object_full_masks[b["object_id"]]
        pid = f"P{len(pair_rows)+1:03d}"
        inter = ma & mb
        overlap = int(inter.sum())
        union_bbox = (
            min(a["bbox_px"][0], b["bbox_px"][0]),
            min(a["bbox_px"][1], b["bbox_px"][1]),
            max(a["bbox_px"][2], b["bbox_px"][2]),
            max(a["bbox_px"][3], b["bbox_px"][3]),
        )
        if overlap:
            center_distance = 0.0
            clearance = 0.0
        else:
            x0, y0, x1, y1 = union_bbox
            pad = 4
            x0 = max(0, x0-pad); y0 = max(0, y0-pad); x1 = min(page_w_px, x1+pad); y1 = min(page_h_px, y1+pad)
            suba = ma[y0:y1, x0:x1]
            subb = mb[y0:y1, x0:x1]
            if suba.any() and subb.any():
                dist = distance_transform_edt(~suba)
                center_distance = float(dist[subb].min())
                clearance = max(0.0, center_distance - 1.0)
            else:
                center_distance = float("inf")
                clearance = float("inf")
        req, category = pair_required_clearance(a, b)
        machine_gate = "OVERLAP_PRESENT" if overlap else ("BELOW_REQUIRED_CLEARANCE" if clearance < req else "MEETS_NUMERIC_CLEARANCE")
        critical = bool(overlap or clearance <= 12.0)
        evidence_dir = ""
        if critical:
            critical_ids.append(pid)
            ed = PAIR_DIR / pid
            ed.mkdir(exist_ok=True)
            x0, y0, x1, y1 = union_bbox
            pad = 12
            x0=max(0,x0-pad); y0=max(0,y0-pad); x1=min(page_w_px,x1+pad); y1=min(page_h_px,y1+pad)
            raw_roi = page_image.crop((x0,y0,x1,y1))
            aa = ma[y0:y1,x0:x1]
            bb = mb[y0:y1,x0:x1]
            ii = aa & bb
            Image.fromarray(aa.astype(np.uint8)*255, "L").save(ed / "mask_A.png")
            Image.fromarray(bb.astype(np.uint8)*255, "L").save(ed / "mask_B.png")
            Image.fromarray(ii.astype(np.uint8)*255, "L").save(ed / "intersection.png")
            ov = np.array(raw_roi).copy()
            ov[aa] = (255,0,0); ov[bb] = (0,120,255); ov[ii] = (255,0,255)
            Image.fromarray(ov).save(ed / "overlay.png")
            raw_roi.save(ed / "roi_1x.png")
            raw_roi.resize((raw_roi.width*8, raw_roi.height*8), Image.Resampling.NEAREST).save(ed / "roi_8x_nearest.png")
            if ii.any():
                tys, txs = np.where(ii)
                qx0, qy0, qx1, qy1 = int(txs.min()), int(tys.min()), int(txs.max()+1), int(tys.max()+1)
            else:
                da, inds = distance_transform_edt(~aa, return_indices=True)
                bys, bxs = np.where(bb)
                vals = da[bys, bxs]
                k = int(np.argmin(vals))
                bx, by = int(bxs[k]), int(bys[k])
                ay, ax = int(inds[0, by, bx]), int(inds[1, by, bx])
                qx0, qy0, qx1, qy1 = min(ax,bx), min(ay,by), max(ax,bx)+1, max(ay,by)+1
            qpad = 16
            qx0=max(0,qx0-qpad); qy0=max(0,qy0-qpad); qx1=min(raw_roi.width,qx1+qpad); qy1=min(raw_roi.height,qy1+qpad)
            tight_raw = raw_roi.crop((qx0,qy0,qx1,qy1))
            tight_ov = Image.fromarray(ov).crop((qx0,qy0,qx1,qy1))
            tight_raw.save(ed / "critical_tight_1x.png")
            tight_ov.save(ed / "critical_tight_overlay_1x.png")
            tight_raw.resize((tight_raw.width*8,tight_raw.height*8),Image.Resampling.NEAREST).save(ed / "critical_tight_8x_nearest.png")
            tight_ov.resize((tight_ov.width*8,tight_ov.height*8),Image.Resampling.NEAREST).save(ed / "critical_tight_overlay_8x_nearest.png")
            evidence_dir = str(ed.resolve())
        pair_rows.append({
            "pair_id": pid,
            "object_a": a["object_id"],
            "object_b": b["object_id"],
            "category": category,
            "required_clearance_px": req,
            "overlap_pixel_count": overlap,
            "center_distance_px": None if math.isinf(center_distance) else round(center_distance, 4),
            "edge_clearance_px": None if math.isinf(clearance) else round(clearance, 4),
            "machine_gate": machine_gate,
            "critical_le_12px": critical,
            "union_bbox_px": list(union_bbox),
            "evidence_dir": evidence_dir,
        })

write_csv(MACHINE / "pair_inventory_machine.csv", pair_rows)
(MACHINE / "pair_inventory_machine.json").write_text(json.dumps(pair_rows, ensure_ascii=False, indent=2), encoding="utf-8")


# Critical-pair contact sheets: machine render only, no reviewer fields.
critical_cards = []
pair_by_id = {r["pair_id"]: r for r in pair_rows}
for pid in critical_ids:
    row = pair_by_id[pid]
    ed = Path(row["evidence_dir"])
    a = Image.open(ed / "critical_tight_8x_nearest.png").convert("RGB")
    b = Image.open(ed / "critical_tight_overlay_8x_nearest.png").convert("RGB")
    max_part_w = 900
    cw = min(max_part_w, max(a.width,b.width))
    # Preserve the 8x raster without resampling: crop only if a very long
    # composed geometry would otherwise make the contact sheet unusable.
    a = a.crop((0,0,cw,a.height)); b = b.crop((0,0,cw,b.height))
    card = Image.new("RGB",(cw*2+30,max(a.height,b.height)+70),"white")
    cd = ImageDraw.Draw(card)
    cd.text((10,8),f"{pid}: {row['object_a']} vs {row['object_b']}  overlap={row['overlap_pixel_count']}  clearance={row['edge_clearance_px']}",fill="black")
    cd.text((10,30),"RAW TIGHT 8x nearest",fill="black"); cd.text((cw+20,30),"A=red B=blue intersection=magenta, 8x nearest",fill="black")
    card.paste(a,(10,55)); card.paste(b,(cw+20,55))
    cp = PAIR_DIR / f"{pid}_critical_card.png"
    card.save(cp); critical_cards.append(cp)
for start in range(0,len(critical_cards),5):
    cards=[Image.open(p).convert("RGB") for p in critical_cards[start:start+5]]
    sw=max(c.width for c in cards); sh=sum(c.height for c in cards)+20*(len(cards)-1)
    sheet=Image.new("RGB",(sw,sh),"white"); yy=0
    for c in cards: sheet.paste(c,(0,yy)); yy+=c.height+20
    sheet.save(PAIR_DIR / f"critical_pair_contact_sheet_{start//5+1:02d}.png")


# Per-object clip/image-edge inventory.
clip_rows = []
for row in object_rows:
    oid = row["object_id"]
    x0,y0,x1,y1 = row["bbox_px"]
    crop = figure_crop_px if oid in ("T10_CAPTION_LABEL", "T11_CAPTION_BODY") else standalone_px
    cx0,cy0,cx1,cy1 = crop
    inside = x0>=cx0 and y0>=cy0 and x1<=cx1 and y1<=cy1
    clearance = min(x0-cx0, y0-cy0, cx1-x1, cy1-y1) if inside else -1
    clip_rows.append({
        "object_id": oid,
        "relevant_crop": "figure_crop_300dpi" if oid in ("T10_CAPTION_LABEL", "T11_CAPTION_BODY") else "standalone_300dpi",
        "object_bbox_px": row["bbox_px"],
        "crop_bbox_page_px": list(crop),
        "inside_crop": inside,
        "minimum_crop_edge_clearance_px": int(clearance),
        "clip_pixel_count": 0 if inside else int(object_full_masks[oid].sum()),
    })
write_csv(MACHINE / "clip_inventory_machine.csv", clip_rows)


# Machine-only role and punctuation-peer inventories.
role_stats = []
for oid in TEXT_OBJECT_META:
    subset = [r for r in glyph_rows if r["element_id"] == oid and r["glyph_class"] != "LOW_PROFILE_PUNCTUATION"]
    by_class = defaultdict(list)
    for r in subset:
        by_class[r["glyph_class"]].append(r["ink_height_px"])
    for gclass, vals in sorted(by_class.items()):
        role_stats.append({
            "element_id": oid,
            "role": TEXT_OBJECT_META[oid][0],
            "glyph_class": gclass,
            "count": len(vals),
            "median_ink_height_px": float(np.median(vals)),
            "min_ink_height_px": int(min(vals)),
            "max_ink_height_px": int(max(vals)),
            "max_min_ratio": round(max(vals)/min(vals),4) if min(vals) else None,
        })
write_csv(MACHINE / "role_stats_machine.csv", role_stats)

peer_rows = []
for r in glyph_rows:
    if r["glyph_class"] != "LOW_PROFILE_PUNCTUATION":
        continue
    peers = [q for q in glyph_rows if q["glyph_id"] != r["glyph_id"] and q["char"] == r["char"] and q["font"] == r["font"] and abs(float(q["pdf_size_pt"])-float(r["pdf_size_pt"])) <= 0.25]
    peer_rows.append({
        "glyph_id": r["glyph_id"],
        "char": r["char"],
        "font": r["font"],
        "pdf_size_pt": r["pdf_size_pt"],
        "ink_height_px": r["ink_height_px"],
        "ink_area_px": r["ink_area_px"],
        "peer_ids": [q["glyph_id"] for q in peers],
        "peer_count": len(peers),
        "height_ratios": [round(r["ink_height_px"]/q["ink_height_px"],4) if q["ink_height_px"] else None for q in peers],
        "area_ratios": [round(r["ink_area_px"]/q["ink_area_px"],4) if q["ink_area_px"] else None for q in peers],
    })
write_csv(MACHINE / "punctuation_peer_inventory_machine.csv", peer_rows)

source_text = SOURCE.read_text(encoding="utf-8")
source_machine = {
    "source": str(SOURCE.resolve()),
    "global_tikz_font_declarations": re.findall(r"font=\\fontsize\{([^}]+)\}\{([^}]+)\}\\selectfont", source_text),
    "tick_label_font_declarations": re.findall(r"tick label style=\{font=\\fontsize\{([^}]+)\}\{([^}]+)\}\\selectfont\}", source_text),
    "scale_tokens": re.findall(r"\\(?:resizebox|scalebox)|transform shape|(?<!line )scale\s*=", source_text),
    "clip_tokens": re.findall(r"clip\s*=\s*(?:true|false)", source_text),
    "figure_uid_tokens": re.findall(r"FIG-P603-01", source_text),
    "caption_text_present": "MH接受概率是比值" in source_text,
    "label_present": "fig:V5-C03-acceptance-function" in source_text,
}
(MACHINE / "source_font_inventory_machine.json").write_text(json.dumps(source_machine, ensure_ascii=False, indent=2), encoding="utf-8")

drawing_coverage = {
    "page_drawing_count": len(page_drawings),
    "figure_foreground_mappings": {gid: data[1] for gid,data in GRAPHIC_META.items()},
    "explicit_exclusions": [
        {"drawing_index": i, "reason": "outside FIG-P603-01 page region; preceding page content"} for i in range(0,8)
    ] + [
        {"drawing_index": 14, "reason": "pale acceptance-region fill is a background field, not reader foreground; retained in all color/grayscale renders"}
    ],
    "covered_or_excluded_indices": list(range(0,22)),
    "uncovered_indices": [],
    "text_block_scope": {"included_blocks": list(range(19,33)), "explicitly_excluded_blocks": [18,33,34,35], "reason": "adjacent guide paragraph, following body, display equation, and footer remain page-fusion context but are outside the figure/caption object universe"},
}
(MACHINE / "drawing_coverage_machine.json").write_text(json.dumps(drawing_coverage, ensure_ascii=False, indent=2), encoding="utf-8")


# Glyph cards and contact sheets. This stage contains no human decisions.
def get_font(size=15):
    candidates = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf"]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


font = get_font(15)
small_font = get_font(12)
card_paths = []
for row in glyph_rows:
    x0,y0,x1,y1 = row["bbox_px"]
    pad = 4
    rx0=max(0,x0-pad); ry0=max(0,y0-pad); rx1=min(page_w_px,x1+pad); ry1=min(page_h_px,y1+pad)
    original = page_image.crop((rx0,ry0,rx1,ry1))
    mask_local = np.zeros((ry1-ry0,rx1-rx0),dtype=bool)
    m = np.asarray(Image.open(row["mask_path"]).convert("L"))>0
    mask_local[y0-ry0:y1-ry0,x0-rx0:x1-rx0] = m
    over = np.asarray(original).copy()
    over[mask_local] = (255,0,0)
    mask_rgb = np.full((ry1-ry0,rx1-rx0,3),255,dtype=np.uint8)
    mask_rgb[mask_local] = (0,0,0)
    imgs = [original, Image.fromarray(over), Image.fromarray(mask_rgb)]
    zooms = [im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST) for im in imgs]
    card_w = max(1050, sum(im.width for im in zooms)+40)
    card_h = 90 + max(im.height for im in zooms) + 50
    card = Image.new("RGB",(card_w,card_h),"white")
    cd=ImageDraw.Draw(card)
    cd.text((10,8),f"{row['glyph_id']}  {row['element_id']}  {row['unicode']}  char={row['char']!r}",fill="black",font=font)
    cd.text((10,30),f"bbox_px={row['bbox_px']} ink={row['ink_width_px']}x{row['ink_height_px']} area={row['ink_area_px']} class={row['glyph_class']}",fill="black",font=small_font)
    labels=["ORIGINAL 8x nearest","TARGET OVERLAY 8x nearest","MASK ONLY 8x nearest"]
    xx=10
    for lab,im in zip(labels,zooms):
        cd.text((xx,55),lab,fill="black",font=small_font)
        card.paste(im,(xx,80)); xx += im.width+10
    path=CONTACT/"glyph_cards"/f"{row['safe_filename']}.png"
    card.save(path)
    row["contact_card_path"] = str(path.resolve())
    card_paths.append(path)

for start in range(0,len(card_paths),10):
    batch=card_paths[start:start+10]
    cards=[Image.open(p).convert("RGB") for p in batch]
    sw=max(im.width for im in cards)
    sh=sum(im.height for im in cards)+20*(len(cards)-1)
    sheet=Image.new("RGB",(sw,sh),"white")
    yy=0
    for im in cards:
        sheet.paste(im,(0,yy)); yy += im.height+20
    sheet_no=start//10+1
    sheet.save(CONTACT/"glyph_sheets"/f"glyph_contact_sheet_{sheet_no:02d}.png")
    for cell,row in enumerate(glyph_rows[start:start+10],1):
        row["contact_sheet"] = f"glyph_contact_sheet_{sheet_no:02d}.png"
        row["contact_cell"] = cell

write_csv(MACHINE / "glyph_inventory_machine.csv", glyph_rows)
(MACHINE / "glyph_inventory_machine.json").write_text(json.dumps(glyph_rows, ensure_ascii=False, indent=2), encoding="utf-8")


# Math-rule four-view evidence.
for oid in ("G12_GENERAL_FRACTION_RULE", "G13_INDEPENDENT_FRACTION_RULE"):
    full=object_full_masks[oid]
    x0,y0,x1,y1=mask_bbox(full)
    pad=6; rx0=max(0,x0-pad); ry0=max(0,y0-pad); rx1=min(page_w_px,x1+pad); ry1=min(page_h_px,y1+pad)
    original=page_image.crop((rx0,ry0,rx1,ry1))
    local=full[ry0:ry1,rx0:rx1]
    ov=np.asarray(original).copy(); ov[local]=(255,0,0)
    mask_rgb=np.full_like(ov,255); mask_rgb[local]=(0,0,0)
    parts=[original,Image.fromarray(ov),Image.fromarray(mask_rgb)]
    zoom=[im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST) for im in parts]
    canvas=Image.new("RGB",(sum(im.width for im in zoom)+40,max(im.height for im in zoom)+60),"white")
    dr=ImageDraw.Draw(canvas); dr.text((10,8),f"{oid} ORIGINAL / TARGET OVERLAY / MASK ONLY at 8x nearest",fill="black",font=font)
    xx=10
    for im in zoom: canvas.paste(im,(xx,40)); xx+=im.width+10
    canvas.save(CONTACT/"math_rules"/f"{oid}_four_view_8x.png")


summary = {
    "pdf": str(PDF.resolve()),
    "page_index_zero_based": PAGE_INDEX,
    "physical_page": PAGE_INDEX + 1,
    "printed_page": 642,
    "figure_number": "图32.6",
    "page_pt": [page_w_pt, page_h_pt],
    "native_300dpi_grid_px": [page_w_px, page_h_px],
    "standalone_crop_pt": list(STANDALONE_PT),
    "standalone_crop_px": list(standalone_px),
    "figure_crop_pt": list(FIGURE_CROP_PT),
    "figure_crop_px": list(figure_crop_px),
    "glyph_count": len(glyph_rows),
    "space_exclusion_count": len(space_exclusions),
    "text_object_count": len(TEXT_OBJECT_META),
    "graphic_object_count": len(GRAPHIC_META),
    "foreground_object_count": len(object_rows),
    "pair_count": len(pair_rows),
    "expected_pair_count": len(object_rows) * (len(object_rows)-1) // 2,
    "critical_pair_count_le_12px_or_overlap": len(critical_ids),
    "critical_pair_ids": critical_ids,
    "empty_glyph_masks": sum(not r["mask_nonempty"] for r in glyph_rows),
    "empty_graphic_masks": sum(not r["mask_nonempty"] for r in graphic_rows),
    "machine_glyph_threshold_below_count": sum(r["machine_threshold_status"] == "BELOW" for r in glyph_rows),
    "machine_pair_overlap_present_count": sum(r["overlap_pixel_count"] > 0 for r in pair_rows),
    "machine_pair_below_clearance_count": sum(r["machine_gate"] == "BELOW_REQUIRED_CLEARANCE" for r in pair_rows),
    "clip_pixel_count": sum(r["clip_pixel_count"] for r in clip_rows),
    "render_engine": "Poppler pdftoppm direct page render; crops are integer-coordinate non-resized extracts",
    "script_scope": "machine inventories, masks, pairs, renders, and contact sheets only; no reviewer booleans, decisions, or notes",
}
(MACHINE / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
