from __future__ import annotations

import csv
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_rejection_sampling_comparison.tex")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P610-01\sa3_r104_fresh_isolated_v1")
MASK_DIR = OUT / "masks"
PAGE_INDEX = 661  # zero based; physical PDF page 662
DPI = 300


TEXT_GROUPS = [
    {"id": "TXT_L_TITLE", "panel": "L", "role": "PANEL_TITLE", "bbox_pt": (160, 497, 245, 520), "declared_pt": 10.2, "line": 18},
    {"id": "TXT_R_TITLE", "panel": "R", "role": "PANEL_TITLE", "bbox_pt": (338, 497, 466, 520), "declared_pt": 10.2, "line": 19},
    {"id": "TXT_L_PROP_Y1", "panel": "L", "role": "NODE_LABEL", "bbox_pt": (140, 525, 166, 552), "declared_pt": 9.2, "line": 20},
    {"id": "TXT_L_PROP_Y2", "panel": "L", "role": "NODE_LABEL", "bbox_pt": (191, 525, 217, 552), "declared_pt": 9.2, "line": 20},
    {"id": "TXT_L_PROP_Y3", "panel": "L", "role": "NODE_LABEL", "bbox_pt": (242, 525, 268, 552), "declared_pt": 9.2, "line": 20},
    {"id": "TXT_R_PROP_Y1", "panel": "R", "role": "NODE_LABEL", "bbox_pt": (338, 525, 365, 552), "declared_pt": 9.2, "line": 22},
    {"id": "TXT_R_PROP_Y2", "panel": "R", "role": "NODE_LABEL", "bbox_pt": (389, 525, 416, 552), "declared_pt": 9.2, "line": 22},
    {"id": "TXT_R_PROP_Y3", "panel": "R", "role": "NODE_LABEL", "bbox_pt": (440, 525, 467, 552), "declared_pt": 9.2, "line": 22},
    {"id": "TXT_L_REJECT", "panel": "L", "role": "REJECTION_MARK", "bbox_pt": (195, 550, 213, 570), "declared_pt": 14.0, "line": 26},
    {"id": "TXT_R_REJECT", "panel": "R", "role": "REJECTION_MARK", "bbox_pt": (393, 550, 412, 570), "declared_pt": 14.0, "line": 34},
    {"id": "TXT_L_OUT_Y1", "panel": "L", "role": "NODE_LABEL", "bbox_pt": (140, 568, 167, 596), "declared_pt": 9.2, "line": 24},
    {"id": "TXT_L_OUT_Y3", "panel": "L", "role": "NODE_LABEL", "bbox_pt": (242, 568, 269, 596), "declared_pt": 9.2, "line": 25},
    {"id": "TXT_R_OUT_Y1A", "panel": "R", "role": "NODE_LABEL", "bbox_pt": (338, 568, 365, 596), "declared_pt": 9.2, "line": 31},
    {"id": "TXT_R_OUT_Y1B", "panel": "R", "role": "NODE_LABEL", "bbox_pt": (389, 568, 416, 596), "declared_pt": 9.2, "line": 32},
    {"id": "TXT_R_OUT_Y3", "panel": "R", "role": "NODE_LABEL", "bbox_pt": (440, 568, 467, 596), "declared_pt": 9.2, "line": 33},
    {"id": "TXT_L_NOTE", "panel": "L", "role": "ANNOTATION", "bbox_pt": (145, 598, 271, 617), "declared_pt": 8.5, "line": 29},
    {"id": "TXT_R_NOTE", "panel": "R", "role": "ANNOTATION", "bbox_pt": (327, 598, 476, 617), "declared_pt": 8.5, "line": 41},
]


GRAPHIC_GROUPS = [
    {"id": "G_L_PANEL_BORDER", "panel": "L", "class": "PANEL_BORDER", "drawings": [4], "line": 16},
    {"id": "G_R_PANEL_BORDER", "panel": "R", "class": "PANEL_BORDER", "drawings": [5], "line": 17},
    {"id": "G_L_PROP_NODE_1", "panel": "L", "class": "NODE_BORDER", "drawings": [6], "line": 21},
    {"id": "G_L_PROP_NODE_2", "panel": "L", "class": "NODE_BORDER", "drawings": [7], "line": 21},
    {"id": "G_L_PROP_NODE_3", "panel": "L", "class": "NODE_BORDER", "drawings": [8], "line": 21},
    {"id": "G_R_PROP_NODE_1", "panel": "R", "class": "NODE_BORDER", "drawings": [9], "line": 23},
    {"id": "G_R_PROP_NODE_2", "panel": "R", "class": "NODE_BORDER", "drawings": [10], "line": 23},
    {"id": "G_R_PROP_NODE_3", "panel": "R", "class": "NODE_BORDER", "drawings": [11], "line": 23},
    {"id": "G_L_OUT_NODE_1", "panel": "L", "class": "NODE_BORDER", "drawings": [12], "line": 24},
    {"id": "G_L_OUT_NODE_3", "panel": "L", "class": "NODE_BORDER", "drawings": [13], "line": 25},
    {"id": "G_L_PROPOSAL_CONNECTOR_1", "panel": "L", "class": "LINE_ARROW", "drawings": [14], "line": 27},
    {"id": "G_L_PROPOSAL_CONNECTOR_3", "panel": "L", "class": "LINE_ARROW", "drawings": [15], "line": 28},
    {"id": "G_R_OUT_NODE_1", "panel": "R", "class": "NODE_BORDER", "drawings": [16], "line": 31},
    {"id": "G_R_OUT_NODE_2_DOUBLE", "panel": "R", "class": "NODE_BORDER", "drawings": [17, 18], "line": 32},
    {"id": "G_R_OUT_NODE_3", "panel": "R", "class": "NODE_BORDER", "drawings": [19], "line": 33},
    {"id": "G_R_PROPOSAL_CONNECTOR_1", "panel": "R", "class": "LINE_ARROW", "drawings": [20], "line": 35},
    {"id": "G_R_PROPOSAL_CONNECTOR_2", "panel": "R", "class": "LINE_ARROW", "drawings": [21], "line": 36},
    {"id": "G_R_PROPOSAL_CONNECTOR_3", "panel": "R", "class": "LINE_ARROW", "drawings": [22], "line": 38},
    {"id": "G_R_STATE_ARROW_1", "panel": "R", "class": "LINE_ARROW", "drawings": [23, 24], "line": 39},
    {"id": "G_R_STATE_ARROW_2", "panel": "R", "class": "LINE_ARROW", "drawings": [25, 26], "line": 40},
    {"id": "G_CENTER_DIVIDER", "panel": "BETWEEN", "class": "PANEL_BORDER", "drawings": [27], "line": 42},
]


def px_box(rect_pt, sx, sy, pad=0):
    x0, y0, x1, y1 = rect_pt
    return (
        max(0, math.floor(x0 * sx) - pad),
        max(0, math.floor(y0 * sy) - pad),
        math.ceil(x1 * sx) + pad,
        math.ceil(y1 * sy) + pad,
    )


def mask_record(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {"bbox": (0, 0, 0, 0), "crop": np.zeros((0, 0), dtype=np.uint8), "coords": np.zeros((0, 2), dtype=np.float32)}
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = mask[y0:y1, x0:x1].copy()
    coords = np.column_stack((ys, xs)).astype(np.float32)
    return {"bbox": (x0, y0, x1, y1), "crop": crop, "coords": coords}


def save_mask(mask: np.ndarray, path: Path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path, dpi=(DPI, DPI))


def script_class(ch: str):
    if not ch:
        return "EMPTY"
    cp = ord(ch[0])
    name = unicodedata.name(ch[0], "")
    cat = unicodedata.category(ch[0])
    if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
        return "CJK_FULL"
    if "MATHEMATICAL" in name and ("SMALL" in name or "ITALIC SMALL" in name):
        return "MATH_LOWER"
    if ch[0].isdigit():
        return "DIGIT"
    if ch[0].isupper() or "CAPITAL" in name:
        return "LATIN_UPPER"
    if ch[0].islower() or "SMALL" in name:
        return "LATIN_LOWER"
    if cat.startswith("P") or cat.startswith("S"):
        return "SYMBOL"
    return "OTHER"


def find_group(bbox):
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    for g in TEXT_GROUPS:
        x0, y0, x1, y1 = g["bbox_pt"]
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            return g
    return None


def add_path_item(shape, item):
    op = item[0]
    if op == "l":
        shape.draw_line(item[1], item[2])
    elif op == "c":
        shape.draw_bezier(item[1], item[2], item[3], item[4])
    elif op == "re":
        shape.draw_rect(item[1])
    elif op == "qu":
        shape.draw_quad(item[1])
    else:
        raise RuntimeError(f"Unsupported drawing operator: {op!r}")


def render_drawing_group(page_rect, drawings, indices):
    tmp = fitz.open()
    pg = tmp.new_page(width=page_rect.width, height=page_rect.height)
    for idx in indices:
        d = drawings[idx]
        sh = pg.new_shape()
        for item in d["items"]:
            add_path_item(sh, item)
        fill = d.get("fill") if idx in (24, 26) else None
        sh.finish(
            width=d.get("width", 1),
            color=d.get("color"),
            fill=fill,
            dashes=d.get("dashes"),
            lineCap=max(d.get("lineCap", (0, 0, 0))),
            lineJoin=d.get("lineJoin", 0),
            closePath=d.get("closePath", False),
            stroke_opacity=d.get("stroke_opacity") if d.get("stroke_opacity") is not None else 1,
            fill_opacity=d.get("fill_opacity") if d.get("fill_opacity") is not None else 1,
        )
        sh.commit(overlay=True)
    pix = pg.get_pixmap(dpi=DPI, alpha=False, colorspace=fitz.csRGB)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    tmp.close()
    delta = np.max(np.abs(arr.astype(np.int16) - 255), axis=2)
    return delta >= 20


def crop_and_save(img, rect_pt, sx, sy, filename, grayscale=False):
    box = px_box(rect_pt, sx, sy)
    crop = img.crop(box)
    if grayscale:
        crop = crop.convert("L")
    crop.save(OUT / filename, dpi=(DPI, DPI))
    return box, crop.size


def pair_overlap(a, b):
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    x0, y0 = max(ax0, bx0), max(ay0, by0)
    x1, y1 = min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    ac = a["crop"][y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
    bc = b["crop"][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
    return int(np.count_nonzero(ac & bc))


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def nearest_distance(a, b):
    if len(a["coords"]) == 0 or len(b["coords"]) == 0:
        return math.nan
    small, large = (a["coords"], b["coords"]) if len(a["coords"]) <= len(b["coords"]) else (b["coords"], a["coords"])
    tree = cKDTree(large)
    d, _ = tree.query(small, k=1, workers=-1)
    return float(np.min(d))


def pair_family(a_class, b_class):
    s = {a_class, b_class}
    if s == {"TEXT"} or s == {"FORMULA"} or s == {"TEXT", "FORMULA"}:
        return "TEXT_TEXT"
    if ("TEXT" in s or "FORMULA" in s) and "LINE_ARROW" in s:
        return "TEXT_FORMULA__LINE_ARROW"
    if ("TEXT" in s or "FORMULA" in s) and "MARKER" in s:
        return "TEXT_FORMULA__MARKER"
    if ("TEXT" in s or "FORMULA" in s) and "NODE_BORDER" in s:
        return "TEXT_FORMULA__NODE_BORDER"
    if ("TEXT" in s or "FORMULA" in s) and "PANEL_BORDER" in s:
        return "TEXT_FORMULA__PANEL_BORDER"
    return "OTHER"


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    pix = page.get_pixmap(dpi=DPI, alpha=False, colorspace=fitz.csRGB)
    page_rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].copy()
    fitz_img = Image.fromarray(page_rgb, mode="RGB")
    fitz_img.save(OUT / "full_page_fitz_reference_300dpi.png", dpi=(DPI, DPI))
    sx = pix.width / page_rect.width
    sy = pix.height / page_rect.height

    crop_specs = [
        ("figure_crop_with_caption_native_300dpi.png", (70.0, 492.0, 535.0, 657.0), False),
        ("standalone_equivalent_native_300dpi.png", (110.0, 493.0, 496.0, 627.0), False),
        ("standalone_equivalent_grayscale_300dpi.png", (110.0, 493.0, 496.0, 627.0), True),
    ]
    crop_rows = []
    for name, rect, gray in crop_specs:
        box, size = crop_and_save(fitz_img, rect, sx, sy, name, gray)
        crop_rows.append({"file": name, "pdf_rect_pt": str(rect), "pixel_box_full_page": str(box), "pixel_size": str(size), "dpi": DPI, "post_render_resize": "none"})
    full_gray = fitz_img.convert("L")
    full_gray.save(OUT / "full_page_grayscale_300dpi.png", dpi=(DPI, DPI))
    standalone = Image.open(OUT / "standalone_equivalent_native_300dpi.png")
    standalone.save(OUT / "standalone_1x_native_300dpi.png", dpi=(DPI, DPI))
    standalone.resize((standalone.width * 8, standalone.height * 8), Image.Resampling.NEAREST).save(OUT / "standalone_8x_nearest_inspection.png")

    # Raw character inventory and text masks, using the direct 300 dpi page raster.
    raw = page.get_text("rawdict")
    chars_by_group = defaultdict(list)
    glyph_rows = []
    glyph_masks_by_group = defaultdict(list)
    glyph_seq = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                color = fitz.sRGB_to_rgb(span.get("color", 0))
                for ch in span.get("chars", []):
                    text = ch.get("c", "")
                    if not text or text.isspace():
                        continue
                    bbox = tuple(ch["bbox"])
                    group = find_group(bbox)
                    if group is None:
                        continue
                    glyph_seq += 1
                    x0, y0, x1, y1 = px_box(bbox, sx, sy, pad=1)
                    reg = page_rgb[y0:y1, x0:x1].astype(np.float32)
                    border = np.concatenate((reg[0, :, :], reg[-1, :, :], reg[:, 0, :], reg[:, -1, :]), axis=0)
                    bg = np.median(border, axis=0)
                    target = np.array(color, dtype=np.float32)
                    vec = target - bg
                    norm2 = float(np.dot(vec, vec)) or 1.0
                    alpha = np.tensordot(reg - bg, vec, axes=([2], [0])) / norm2
                    proj = bg + alpha[:, :, None] * vec
                    residual = np.linalg.norm(reg - proj, axis=2)
                    contrast = np.max(np.abs(reg - bg), axis=2)
                    local = (contrast >= 20.0) & (alpha > 0.0) & (alpha <= 1.25) & (residual <= 18.0)
                    if float(target.max() - target.min()) > 30.0:
                        chroma = np.max(reg, axis=2) - np.min(reg, axis=2)
                        local &= chroma >= 10.0
                        local &= np.argmax(reg, axis=2) == int(np.argmax(target))
                        local &= np.argmin(reg, axis=2) == int(np.argmin(target))
                    mask = np.zeros((pix.height, pix.width), dtype=bool)
                    mask[y0:y1, x0:x1] = local
                    rec = mask_record(mask)
                    h_ink = rec["bbox"][3] - rec["bbox"][1] if len(rec["coords"]) else 0
                    w_ink = rec["bbox"][2] - rec["bbox"][0] if len(rec["coords"]) else 0
                    glyph_id = f"GLY_{glyph_seq:03d}"
                    glyph_rows.append({
                        "glyph_id": glyph_id,
                        "element_id": group["id"],
                        "panel_id": group["panel"],
                        "role": group["role"],
                        "unicode_text": text,
                        "codepoints": " ".join(f"U+{ord(c):04X}" for c in text),
                        "unicode_names": " | ".join(unicodedata.name(c, "UNNAMED") for c in text),
                        "script_class": script_class(text),
                        "font": span.get("font"),
                        "pdf_span_size_pt": f"{span.get('size', 0):.6f}",
                        "declared_base_pt": group["declared_pt"],
                        "graphics_scale": "1.0",
                        "pdf_bbox_pt": " ".join(f"{v:.6f}" for v in bbox),
                        "raster_bbox_px": f"{x0} {y0} {x1} {y1}",
                        "ink_bbox_px": " ".join(str(v) for v in rec["bbox"]),
                        "h_ink_px": h_ink,
                        "w_ink_px": w_ink,
                        "foreground_pixel_count": len(rec["coords"]),
                        "source_line": group["line"],
                        "source_color_rgb": str(color),
                        "local_background_rgb": " ".join(str(int(round(v))) for v in bg),
                        "threshold_contrast_255": 20,
                    })
                    chars_by_group[group["id"]].append((text, span, bbox, glyph_id, h_ink, rec))
                    glyph_masks_by_group[group["id"]].append(mask)

    masks = {}
    object_meta = {}
    text_rows = []
    for g in TEXT_GROUPS:
        items = chars_by_group[g["id"]]
        mask = np.zeros((pix.height, pix.width), dtype=bool)
        for m in glyph_masks_by_group[g["id"]]:
            mask |= m
        rec = mask_record(mask)
        masks[g["id"]] = rec
        save_mask(mask, MASK_DIR / f"{g['id']}.png")
        text = "".join(x[0] for x in items)
        sizes = [float(x[1].get("size", 0)) for x in items]
        heights = [int(x[4]) for x in items if int(x[4]) > 0]
        scripts = sorted({script_class(x[0]) for x in items})
        h = rec["bbox"][3] - rec["bbox"][1] if len(rec["coords"]) else 0
        text_rows.append({
            "element_id": g["id"],
            "panel_id": g["panel"],
            "role": g["role"],
            "object_class": "FORMULA" if g["role"] == "NODE_LABEL" else "TEXT",
            "source_file": str(SOURCE.resolve()),
            "source_line": g["line"],
            "declared_pt": g["declared_pt"],
            "graphics_scale": "1.0",
            "pdf_span_size_min_pt": f"{min(sizes):.6f}" if sizes else "",
            "pdf_span_size_max_pt": f"{max(sizes):.6f}" if sizes else "",
            "text_extracted": text,
            "script_classes": "|".join(scripts),
            "glyph_count": len(items),
            "ink_bbox_px": " ".join(str(v) for v in rec["bbox"]),
            "h_ink_px": h,
            "median_glyph_h_ink_px": f"{float(np.median(heights)):.3f}" if heights else "",
            "foreground_pixel_count": len(rec["coords"]),
        })
        object_meta[g["id"]] = {"panel": g["panel"], "role": g["role"], "class": "FORMULA" if g["role"] == "NODE_LABEL" else "TEXT", "source_line": g["line"]}

    drawings = page.get_drawings()
    graphic_rows = []
    for g in GRAPHIC_GROUPS:
        mask = render_drawing_group(page_rect, drawings, g["drawings"])
        rec = mask_record(mask)
        masks[g["id"]] = rec
        save_mask(mask, MASK_DIR / f"{g['id']}.png")
        draw_rects = [drawings[i]["rect"] for i in g["drawings"]]
        union = fitz.Rect(draw_rects[0])
        for r in draw_rects[1:]:
            union |= r
        graphic_rows.append({
            "object_id": g["id"],
            "panel_id": g["panel"],
            "object_class": g["class"],
            "drawing_indices": "|".join(map(str, g["drawings"])),
            "source_file": str(SOURCE.resolve()),
            "source_line": g["line"],
            "vector_bbox_pt": " ".join(f"{v:.6f}" for v in union),
            "ink_bbox_px": " ".join(str(v) for v in rec["bbox"]),
            "foreground_pixel_count": len(rec["coords"]),
        })
        object_meta[g["id"]] = {"panel": g["panel"], "role": g["class"], "class": g["class"], "source_line": g["line"]}

    object_rows = []
    for oid in [g["id"] for g in TEXT_GROUPS] + [g["id"] for g in GRAPHIC_GROUPS]:
        rec = masks[oid]
        meta = object_meta[oid]
        object_rows.append({
            "object_id": oid,
            "panel_id": meta["panel"],
            "role": meta["role"],
            "object_class": meta["class"],
            "source_line": meta["source_line"],
            "ink_bbox_px": " ".join(str(v) for v in rec["bbox"]),
            "foreground_pixel_count": len(rec["coords"]),
            "mask_file": f"masks/{oid}.png",
        })

    object_ids = [r["object_id"] for r in object_rows]
    pair_rows = []
    critical_rows = []
    mandatory_families = {
        "TEXT_TEXT",
        "TEXT_FORMULA__LINE_ARROW",
        "TEXT_FORMULA__MARKER",
        "TEXT_FORMULA__NODE_BORDER",
        "TEXT_FORMULA__PANEL_BORDER",
    }
    for i, aid in enumerate(object_ids):
        for bid in object_ids[i + 1:]:
            a, b = masks[aid], masks[bid]
            overlap = pair_overlap(a, b)
            nearest = nearest_distance(a, b)
            clearance = max(0.0, nearest - 1.0) if math.isfinite(nearest) else math.nan
            ac, bc = object_meta[aid]["class"], object_meta[bid]["class"]
            family = pair_family(ac, bc)
            row = {
                "pair_id": f"{aid}__{bid}",
                "object_a": aid,
                "class_a": ac,
                "panel_a": object_meta[aid]["panel"],
                "object_b": bid,
                "class_b": bc,
                "panel_b": object_meta[bid]["panel"],
                "pair_family": family,
                "bbox_gap_px": f"{bbox_gap(a, b):.6f}",
                "nearest_ink_center_distance_px": f"{nearest:.6f}",
                "blank_pixel_clearance_px": f"{clearance:.6f}",
                "mask_overlap_pixel_count": overlap,
                "measurement_raster": "full_page_fitz_reference_300dpi.png",
                "mask_threshold_contrast_255": 20,
            }
            pair_rows.append(row)
            if family in mandatory_families or overlap > 0 or clearance <= 12.0:
                critical_rows.append(row)

    # Role and peer medians are raw aggregates, not acceptance decisions.
    peer_rows = []
    by_role_panel = defaultdict(list)
    for row in text_rows:
        by_role_panel[(row["role"], row["panel_id"])].append(int(row["h_ink_px"]))
    for (role, panel), vals in sorted(by_role_panel.items()):
        peer_rows.append({
            "role": role,
            "panel_id": panel,
            "element_count": len(vals),
            "median_element_h_ink_px": f"{float(np.median(vals)):.6f}",
            "min_element_h_ink_px": min(vals),
            "max_element_h_ink_px": max(vals),
            "max_to_min_ratio": f"{max(vals)/min(vals):.6f}" if min(vals) else "",
        })

    # Raw clip and boundary clearances, restricted to reader elements.
    panel_borders = {"L": masks["G_L_PANEL_BORDER"], "R": masks["G_R_PANEL_BORDER"]}
    clip_rows = []
    for g in TEXT_GROUPS:
        rec = masks[g["id"]]
        x0, y0, x1, y1 = rec["bbox"]
        page_edge = min(x0, y0, pix.width - x1, pix.height - y1)
        panel_dist = nearest_distance(rec, panel_borders[g["panel"]]) if g["panel"] in panel_borders else math.nan
        panel_clearance = max(0.0, panel_dist - 1.0) if math.isfinite(panel_dist) else math.nan
        clip_rows.append({
            "object_id": g["id"],
            "panel_id": g["panel"],
            "ink_bbox_px": " ".join(str(v) for v in rec["bbox"]),
            "page_edge_bbox_clearance_px": page_edge,
            "nearest_panel_border_ink_center_distance_px": f"{panel_dist:.6f}",
            "blank_pixel_clearance_to_panel_border_px": f"{panel_clearance:.6f}",
            "ink_pixels_on_physical_page_edge": int(np.count_nonzero(rec["crop"][0, :]) + np.count_nonzero(rec["crop"][-1, :]) + np.count_nonzero(rec["crop"][:, 0]) + np.count_nonzero(rec["crop"][:, -1])) if (x0 == 0 or y0 == 0 or x1 == pix.width or y1 == pix.height) else 0,
        })

    # Measurement overlays.
    overlay = fitz_img.copy()
    draw = ImageDraw.Draw(overlay)
    try:
        label_font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17)
    except OSError:
        label_font = ImageFont.load_default()
    for oid in object_ids:
        x0, y0, x1, y1 = masks[oid]["bbox"]
        color = (245, 128, 24) if object_meta[oid]["class"] in ("TEXT", "FORMULA") else (0, 155, 205)
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        draw.text((x0, max(0, y0 - 18)), oid, fill=color, font=label_font)
    overlay.crop(px_box((108, 490, 498, 629), sx, sy)).save(OUT / "object_measurement_overlay_native_300dpi.png", dpi=(DPI, DPI))

    glyph_overlay = fitz_img.copy()
    gd = ImageDraw.Draw(glyph_overlay)
    for row in glyph_rows:
        x0, y0, x1, y1 = map(int, row["ink_bbox_px"].split())
        gd.rectangle((x0, y0, x1, y1), outline=(212, 72, 117), width=1)
        gd.text((x0, max(0, y0 - 12)), row["glyph_id"], fill=(212, 72, 117), font=label_font)
    glyph_overlay.crop(px_box((108, 490, 498, 629), sx, sy)).save(OUT / "glyph_measurement_overlay_native_300dpi.png", dpi=(DPI, DPI))

    # Combined foreground masks.
    text_union = np.zeros((pix.height, pix.width), dtype=bool)
    graphic_union = np.zeros_like(text_union)
    for oid in object_ids:
        rec = masks[oid]
        x0, y0, x1, y1 = rec["bbox"]
        target = text_union if object_meta[oid]["class"] in ("TEXT", "FORMULA") else graphic_union
        if x1 > x0 and y1 > y0:
            target[y0:y1, x0:x1] |= rec["crop"]
    save_mask(text_union, OUT / "text_semantic_union_mask_300dpi.png")
    save_mask(graphic_union, OUT / "graphic_semantic_union_mask_300dpi.png")

    write_csv(OUT / "glyph_inventory_raw.csv", glyph_rows, list(glyph_rows[0].keys()))
    write_csv(OUT / "text_element_measurements_raw.csv", text_rows, list(text_rows[0].keys()))
    write_csv(OUT / "graphic_object_inventory_raw.csv", graphic_rows, list(graphic_rows[0].keys()))
    write_csv(OUT / "actual_object_inventory_raw.csv", object_rows, list(object_rows[0].keys()))
    write_csv(OUT / "all_unordered_object_pairs_raw.csv", pair_rows, list(pair_rows[0].keys()))
    write_csv(OUT / "critical_and_required_pairs_raw.csv", critical_rows, list(pair_rows[0].keys()))
    write_csv(OUT / "peer_role_aggregates_raw.csv", peer_rows, list(peer_rows[0].keys()))
    write_csv(OUT / "clip_and_boundary_measurements_raw.csv", clip_rows, list(clip_rows[0].keys()))
    write_csv(OUT / "render_crop_inventory_raw.csv", crop_rows, list(crop_rows[0].keys()))

    metadata = {
        "pdf_resolved_path": str(PDF.resolve()),
        "source_resolved_path": str(SOURCE.resolve()),
        "physical_page": 662,
        "zero_based_page_index": PAGE_INDEX,
        "printed_page_header": 649,
        "figure_number": "32.10",
        "source_label": "fig:V5-C03-rejection-vs-mh",
        "page_size_pt": [page_rect.width, page_rect.height],
        "fitz_raster_size_px": [pix.width, pix.height],
        "dpi": DPI,
        "scale_x_px_per_pdf_pt": sx,
        "scale_y_px_per_pdf_pt": sy,
        "text_element_count": len(TEXT_GROUPS),
        "glyph_count_non_whitespace": len(glyph_rows),
        "graphic_semantic_object_count": len(GRAPHIC_GROUPS),
        "actual_semantic_object_count": len(object_ids),
        "all_unordered_pair_count": len(pair_rows),
        "expected_unordered_pair_count_n_choose_2": len(object_ids) * (len(object_ids) - 1) // 2,
        "fitz_version": fitz.VersionBind,
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "measurement_note": "Raw mechanical measurements only; no reviewer result, boolean acceptance, decision, or semantic adjudication is generated by this program.",
    }
    (OUT / "mechanical_measurement_metadata_raw.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    doc.close()


if __name__ == "__main__":
    main()
