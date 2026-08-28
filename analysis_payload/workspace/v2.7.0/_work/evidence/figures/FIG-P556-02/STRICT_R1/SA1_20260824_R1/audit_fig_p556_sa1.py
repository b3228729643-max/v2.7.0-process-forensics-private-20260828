"""Independent, read-only SA1 audit for FIG-P556-02.

The sole raster authority is a direct 300-dpi render of physical PDF page 602.
All figure crops are pixel slices of that immutable full-page grid.  The script
writes only beside itself in the dedicated SA1 evidence directory.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_chain_properties.tex")
BODY = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C01.tex")
STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty")

TASK_ID = "FIG-P556-02"
PHYSICAL_PAGE = 602
PRINTED_PAGE = 589
PAGE_INDEX = PHYSICAL_PAGE - 1
DPI = 300
SCALE = DPI / 72.0
THRESHOLD = 20

# This rectangle includes the three-card tikzpicture and the natural one-line caption.
# The caption label begins at x≈84pt and its final CJK character ends at x≈523pt.
# The crop therefore includes the complete real caption, rather than only the card body.
FIG_RECT = fitz.Rect(70, 175, 540, 374)
STANDALONE_RECT = fitz.Rect(112, 176, 496, 354)


def od(oid, panel, role, rect, source_line, declared, declared_detail, node_text=False):
    return {
        "ELEMENT_ID": oid,
        "PANEL_ID": panel,
        "ROLE": role,
        "PDF_RECT": fitz.Rect(rect),
        "SOURCE_LINE": source_line,
        "DECLARED_PT": declared,
        "DECLARED_DETAIL": declared_detail,
        "GRAPHICS_SCALE": 1.0,
        "EFFECTIVE_PT": declared,
        "NODE_TEXT": node_text,
        "chars": [],
        "mask": None,
    }


OBJECTS = [
    od("IRR_TITLE", "IRR", "PANEL_TITLE", (150, 184, 204, 208), "23", 10.4, r"slfig-FIG-P556-02-title"),
    od("IRR_STATE_1", "IRR", "STATE_LABEL", (143, 217, 158, 238), "24", 9.4, r"state font" , True),
    od("IRR_STATE_2", "IRR", "STATE_LABEL", (191, 217, 213, 238), "25", 9.4, r"state font" , True),
    od("IRR_FORMULA", "IRR", "FORMULA", (128, 252, 226, 278), "28", 9.2, r"slfig-FIG-P556-02-formula"),
    od("IRR_ANSWER", "IRR", "ANNOTATION", (122, 289, 235, 307), "29-30", 8.8, r"slfig-FIG-P556-02-answer"),
    od("PER_TITLE", "PER", "PANEL_TITLE", (282, 184, 325, 208), "32", 10.4, r"slfig-FIG-P556-02-title"),
    od("PER_FORMULA", "PER", "FORMULA", (250, 251, 347, 284), "37-38", 9.2, r"slfig-FIG-P556-02-formula; natural scripts only"),
    od("PER_ANSWER", "PER", "ANNOTATION", (250, 289, 365, 307), "39-40", 8.8, r"slfig-FIG-P556-02-answer"),
    od("REC_TITLE", "REC", "PANEL_TITLE", (409, 184, 452, 208), "42", 10.4, r"slfig-FIG-P556-02-title"),
    od("REC_STATE", "REC", "STATE_LABEL", (419, 217, 441, 238), "43", 9.4, r"state font" , True),
    od("REC_FORMULA", "REC", "FORMULA", (400, 258, 458, 278), "46", 9.2, r"slfig-FIG-P556-02-formula; natural scripts only"),
    od("REC_ANSWER", "REC", "ANNOTATION", (376, 289, 490, 307), "47-48", 8.8, r"slfig-FIG-P556-02-answer"),
    od("SUMMARY", "SUMMARY", "SUMMARY", (150, 333, 458, 352), "50-53", 9.2, r"explicit node font"),
    od("CAPTION_PARENT", "CAPTION", "CAPTION", (78, 350, 532, 373), "55 + common/statlearnbook.sty:305", 10.0, r"caption \small; emitted final-PDF span=9.9626pt"),
]

DRAW_COMPONENTS = [
    ("IRR_CARD_BORDER", 4, "PANEL_BORDER", "IRR"),
    ("PER_CARD_BORDER", 5, "PANEL_BORDER", "PER"),
    ("REC_CARD_BORDER", 6, "PANEL_BORDER", "REC"),
    ("IRR_STATE_1_BORDER", 7, "NODE_BORDER", "IRR"),
    ("IRR_STATE_2_BORDER", 8, "NODE_BORDER", "IRR"),
    ("IRR_ARROW_12", 9, "LINE_ARROW", "IRR"),
    ("IRR_ARROW_12_HEAD", 10, "ARROWHEAD", "IRR"),
    ("IRR_ARROW_21", 11, "LINE_ARROW", "IRR"),
    ("IRR_ARROW_21_HEAD", 12, "ARROWHEAD", "IRR"),
    ("PER_TIME_AXIS", 13, "LINE_ARROW", "PER"),
    ("PER_MARKER_2", 14, "MARKER", "PER"),
    ("PER_MARKER_4", 15, "MARKER", "PER"),
    ("PER_MARKER_6", 16, "MARKER", "PER"),
    ("PER_MARKER_8", 17, "MARKER", "PER"),
    ("REC_STATE_BORDER", 18, "NODE_BORDER", "REC"),
    ("REC_LOOP", 19, "LINE_ARROW", "REC"),
    ("REC_LOOP_HEAD", 20, "ARROWHEAD", "REC"),
    ("SUMMARY_BORDER", 21, "NODE_BORDER", "SUMMARY"),
]


def mkdirs():
    for rel in ["masks/glyph_raw", "masks/text_raw", "masks/vector_raw", "masks/vector_visible_raw", "critical_pairs"]:
        (OUT / rel).mkdir(parents=True, exist_ok=True)


def png_array(path: Path, arr: np.ndarray):
    Image.fromarray(arr.astype(np.uint8), "RGB").save(path)


def bool_image(mask: np.ndarray) -> np.ndarray:
    rgb = np.full((mask.shape[0], mask.shape[1], 3), 255, dtype=np.uint8)
    rgb[mask] = (0, 0, 0)
    return rgb


def rect_pixels(rect: fitz.Rect, width: int, height: int):
    return (
        max(0, int(math.floor(rect.x0 * SCALE))),
        max(0, int(math.floor(rect.y0 * SCALE))),
        min(width, int(math.ceil(rect.x1 * SCALE))),
        min(height, int(math.ceil(rect.y1 * SCALE))),
    )


def px_rect_to_dict(r):
    return {"x0": int(r[0]), "y0": int(r[1]), "x1": int(r[2]), "y1": int(r[3])}


def pdf_rect_to_dict(r: fitz.Rect):
    return {"x0": round(r.x0, 5), "y0": round(r.y0, 5), "x1": round(r.x1, 5), "y1": round(r.y1, 5)}


def union_rect(rects):
    if not rects:
        return fitz.Rect(0, 0, 0, 0)
    r = fitz.Rect(rects[0])
    for q in rects[1:]:
        r |= fitz.Rect(q)
    return r


def mask_bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def bbox_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return float(math.hypot(dx, dy))


def pixel_distance(mask_a: np.ndarray, mask_b: np.ndarray):
    if not mask_a.any() or not mask_b.any():
        return None
    if np.logical_and(mask_a, mask_b).any():
        return 0.0
    # Restrict the EDT to the two masks' exact union bbox. This preserves the
    # native pixel distance while avoiding a needless full-A4 transform per pair.
    ba, bb = mask_bbox(mask_a), mask_bbox(mask_b)
    x0, y0 = min(ba[0], bb[0]), min(ba[1], bb[1])
    x1, y1 = max(ba[2], bb[2]), max(ba[3], bb[3])
    aa, bmask = mask_a[y0:y1, x0:x1], mask_b[y0:y1, x0:x1]
    dist = ndimage.distance_transform_edt(~bmask)
    return float(dist[aa].min())


def clip_count(mask: np.ndarray):
    return int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())


def local_foreground(rgb: np.ndarray, rect_px):
    """Threshold relative to a local light-background ring, without dilation."""
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = rect_px
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    ex0, ey0, ex1, ey1 = max(0, x0 - 4), max(0, y0 - 4), min(w, x1 + 4), min(h, y1 + 4)
    ring = rgb[ey0:ey1, ex0:ex1].reshape(-1, 3)
    if len(ring) == 0:
        bg = np.array([255, 255, 255], dtype=float)
    else:
        lum = ring.mean(axis=1)
        keep = ring[lum >= np.percentile(lum, 60)]
        bg = np.median(keep if len(keep) else ring, axis=0)
    crop = rgb[y0:y1, x0:x1].astype(float)
    local = np.max(np.abs(crop - bg), axis=2) >= THRESHOLD
    return local, [round(float(v), 2) for v in bg]


def classify_char(c: str, span_size: float):
    # Script detection precedes operator detection so sub/superscripts use their legal 15px gate.
    if span_size < 8.0:
        return "NATURAL_SCRIPT", 15
    if "\u4e00" <= c <= "\u9fff" or c in "（）【】《》：；，。！？、":
        return "CJK_FULL", 30
    if c.isdigit() or ("A" <= c <= "Z") or c in "𝔼𝔓𝔸𝔹":
        return "UPPER_DIGIT", 24
    if c in "=<>+−-↔∶:.,;!?[]{}()|/\\∞≥≤":
        return "MATH_OPERATOR", 22
    return "LOWER_GREEK", 17


def recreate_drawing_mask(drawing, kind, page_rect, width, height):
    """Render one extracted PDF drawing to a fresh page, retaining only its own path."""
    doc = fitz.open()
    pg = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = pg.new_shape()
    for item in drawing["items"]:
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
            raise RuntimeError(f"unsupported PDF path op {op!r}")
    line_cap = drawing.get("lineCap", (0, 0, 0))
    line_cap = int((line_cap[0] if isinstance(line_cap, (tuple, list)) else line_cap) or 0)
    line_join = int(drawing.get("lineJoin", 0) or 0)
    # Node/card fills are semantic background and deliberately excluded from node-border masks.
    fill = None if kind in {"NODE_BORDER", "PANEL_BORDER"} else drawing.get("fill")
    color = drawing.get("color")
    if drawing.get("type") == "f":
        color = None
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=color,
        fill=fill,
        lineCap=line_cap,
        lineJoin=line_join,
        dashes=drawing.get("dashes"),
        closePath=bool(drawing.get("closePath", False)),
        even_odd=bool(drawing.get("even_odd", False)),
    )
    shape.commit()
    pix = pg.get_pixmap(dpi=DPI, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    if arr.shape[:2] != (height, width):
        raise RuntimeError(f"vector render grid mismatch: {arr.shape[:2]} vs {(height, width)}")
    # The source page is white; this is direct, independent vector reconstruction, not a paint-order crop.
    mask = np.max(np.abs(arr.astype(np.int16) - 255), axis=2) >= THRESHOLD
    doc.close()
    return mask


def save_critical_pair(cid, pair, rgb, fig_px):
    a, b = pair["MASK_A"], pair["MASK_B"]
    mask_a, mask_b = pair["mask_a"], pair["mask_b"]
    union = np.logical_or(mask_a, mask_b)
    bb = mask_bbox(union)
    if bb is None:
        bb = (pair["bbox_a"][0], pair["bbox_a"][1], pair["bbox_b"][2], pair["bbox_b"][3])
    pad = 8
    x0, y0 = max(fig_px[0], bb[0] - pad), max(fig_px[1], bb[1] - pad)
    x1, y1 = min(fig_px[2], bb[2] + pad), min(fig_px[3], bb[3] + pad)
    # The closest-pair choice makes these compact; nevertheless preserve the exact native ROI if far apart.
    base = f"critical_{cid:03d}_{pair['PAIR_ID']}"
    cp = OUT / "critical_pairs"
    raw = rgb[y0:y1, x0:x1]
    aa, bbm = mask_a[y0:y1, x0:x1], mask_b[y0:y1, x0:x1]
    overlap = np.logical_and(aa, bbm)
    overlay = raw.copy()
    overlay[aa] = (235, 55, 55)
    overlay[bbm] = (35, 95, 235)
    overlay[overlap] = (180, 0, 180)
    png_array(cp / f"{base}_original.png", raw)
    png_array(cp / f"{base}_mask_a_raw.png", bool_image(aa))
    png_array(cp / f"{base}_mask_b_raw.png", bool_image(bbm))
    png_array(cp / f"{base}_overlap_raw.png", bool_image(overlap))
    png_array(cp / f"{base}_overlay.png", overlay)
    # All inspection enlargements are nearest-neighbour only and are excluded from all metrics.
    for suffix, im in [("raw", raw), ("overlay", overlay), ("overlap", bool_image(overlap))]:
        zoom = Image.fromarray(im).resize((max(1, im.shape[1] * 8), max(1, im.shape[0] * 8)), Image.Resampling.NEAREST)
        zoom.save(cp / f"{base}_{suffix}_8x_nn.png")
    return {
        "CRITICAL_ID": cid,
        "PAIR_ID": pair["PAIR_ID"],
        "REASON": pair["CRITICAL_REASON"],
        "ROI_X0": x0,
        "ROI_Y0": y0,
        "ROI_X1": x1,
        "ROI_Y1": y1,
        "OVERLAP_PIXEL_COUNT": pair["OVERLAP_PIXEL_COUNT"],
        "MIN_CLEARANCE_PX": pair["MIN_CLEARANCE_PX"],
        "RAW_8X_NN_FILE": f"critical_pairs/{base}_raw_8x_nn.png",
        "OVERLAY_8X_NN_FILE": f"critical_pairs/{base}_overlay_8x_nn.png",
        "OVERLAP_8X_NN_FILE": f"critical_pairs/{base}_overlap_8x_nn.png",
        "ZOOM_METHOD": "8x nearest-neighbour inspection only; all numeric metrics use native full-page 300dpi raw masks",
    }


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    mkdirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    pix300 = page.get_pixmap(dpi=DPI, alpha=False)
    rgb = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, pix300.n)[:, :, :3]
    h, w = rgb.shape[:2]
    fig_px = rect_pixels(FIG_RECT, w, h)
    standalone_px = rect_pixels(STANDALONE_RECT, w, h)
    png_array(OUT / "full_page_300dpi.png", rgb)
    png_array(OUT / "figure_crop_300dpi.png", rgb[fig_px[1]:fig_px[3], fig_px[0]:fig_px[2]])
    png_array(OUT / "standalone_300dpi.png", rgb[standalone_px[1]:standalone_px[3], standalone_px[0]:standalone_px[2]])
    gray = np.dot(rgb[fig_px[1]:fig_px[3], fig_px[0]:fig_px[2]][:, :, :3], [0.299, 0.587, 0.114]).astype(np.uint8)
    png_array(OUT / "grayscale_300dpi.png", np.repeat(gray[:, :, None], 3, axis=2))
    pix200 = page.get_pixmap(dpi=200, alpha=False)
    rgb200 = np.frombuffer(pix200.samples, dtype=np.uint8).reshape(pix200.height, pix200.width, pix200.n)[:, :, :3]
    png_array(OUT / "full_page_200dpi.png", rgb200)

    # Extract every visible character in the declared figure/caption rectangle.
    rawdict = page.get_text("rawdict")
    unassigned = []
    glyphs = []
    by_id = {x["ELEMENT_ID"]: x for x in OBJECTS}
    gnum = 0
    for block in rawdict["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for ch in span["chars"]:
                    c = ch["c"]
                    if not c.strip():
                        continue
                    r = fitz.Rect(ch["bbox"])
                    center = fitz.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
                    if not FIG_RECT.contains(center):
                        continue
                    owner = None
                    for obj in OBJECTS:
                        rr = fitz.Rect(obj["PDF_RECT"])
                        rr.x0 -= 1.0; rr.y0 -= 1.0; rr.x1 += 1.0; rr.y1 += 1.0
                        if rr.contains(center):
                            owner = obj
                            break
                    if owner is None:
                        unassigned.append({"CHAR": c, "BBOX": pdf_rect_to_dict(r)})
                        continue
                    gnum += 1
                    cls, threshold = classify_char(c, float(span["size"]))
                    rpx = rect_pixels(r, w, h)
                    local, bg = local_foreground(rgb, rpx)
                    fullmask = np.zeros((h, w), dtype=bool)
                    fullmask[rpx[1]:rpx[3], rpx[0]:rpx[2]] = local
                    ink_h = int(local.any(axis=1).sum())
                    gid = f"{owner['ELEMENT_ID']}_G{gnum:03d}"
                    glyph = {
                        "ELEMENT_ID": gid,
                        "PARENT_ELEMENT_ID": owner["ELEMENT_ID"],
                        "PANEL_ID": owner["PANEL_ID"],
                        "ROLE": owner["ROLE"],
                        "SOURCE_FILE": str(SOURCE),
                        "SOURCE_LINE": owner["SOURCE_LINE"],
                        "DECLARED_PT": owner["DECLARED_PT"],
                        "GRAPHICS_SCALE": 1.0,
                        "EFFECTIVE_PT": owner["EFFECTIVE_PT"],
                        "TEXT_SAMPLE": c,
                        "SCRIPT_CLASS": cls,
                        "PDF_FONT": span["font"],
                        "PDF_SPAN_PT": round(float(span["size"]), 5),
                        "BBOX_PDF": pdf_rect_to_dict(r),
                        "BBOX_PX": px_rect_to_dict(rpx),
                        "H_INK_PX": ink_h,
                        "PIXEL_THRESHOLD_PX": threshold,
                        "LOCAL_BACKGROUND_RGB": bg,
                        "mask": fullmask,
                    }
                    owner["chars"].append(glyph)
                    glyphs.append(glyph)
                    png_array(OUT / "masks" / "glyph_raw" / f"{gid}.png", bool_image(local))

    # Semantic text object masks are the OR of their own separately thresholded glyph masks.
    for obj in OBJECTS:
        obj["mask"] = np.zeros((h, w), dtype=bool)
        for g in obj["chars"]:
            obj["mask"] |= g["mask"]
        obj["PDF_BBOX"] = union_rect([fitz.Rect(g["BBOX_PDF"]["x0"], g["BBOX_PDF"]["y0"], g["BBOX_PDF"]["x1"], g["BBOX_PDF"]["y1"]) for g in obj["chars"]])
        obj["PX_BBOX"] = mask_bbox(obj["mask"]) or rect_pixels(obj["PDF_RECT"], w, h)
        png_array(OUT / "masks" / "text_raw" / f"{obj['ELEMENT_ID']}.png", bool_image(obj["mask"][fig_px[1]:fig_px[3], fig_px[0]:fig_px[2]]))

    # Page foreground is for visual traceability only; all comparisons use separated masks above/below.
    page_raw, page_bg = local_foreground(rgb, fig_px)
    png_array(OUT / "masks" / "figure_foreground_raw_300dpi.png", bool_image(page_raw))

    # Recreate each vector component on an otherwise blank PDF page; no vector mask uses paint order.
    drawings = page.get_drawings()
    vectors = []
    for cid, didx, kind, panel in DRAW_COMPONENTS:
        d = drawings[didx]
        mask = recreate_drawing_mask(d, kind, page_rect, w, h)
        comp = {
            "ELEMENT_ID": cid,
            "DRAWING_INDEX": didx,
            "TYPE": kind,
            "PANEL_ID": panel,
            "PDF_BBOX": d["rect"],
            "PX_BBOX": rect_pixels(d["rect"], w, h),
            "mask": mask,
            "PDF_STROKE_WIDTH_PT": d.get("width"),
            "PDF_DRAWING_TYPE": d.get("type"),
        }
        vectors.append(comp)
        png_array(OUT / "masks" / "vector_raw" / f"{cid}.png", bool_image(mask[fig_px[1]:fig_px[3], fig_px[0]:fig_px[2]]))
        # Explicitly labelled diagnostic duplicate: still an individual direct vector mask, never a paint-order crop.
        png_array(OUT / "masks" / "vector_visible_raw" / f"{cid}_independent_vector.png", bool_image(mask[fig_px[1]:fig_px[3], fig_px[0]:fig_px[2]]))

    # Pixel-height gates and actual raw-H_ink same-class ratios.
    class_groups = defaultdict(list)
    for g in glyphs:
        class_groups[(g["PANEL_ID"], g["ROLE"], g["SCRIPT_CLASS"])].append(g)
    for key, vals in class_groups.items():
        med = float(np.median([v["H_INK_PX"] for v in vals])) if vals else 0.0
        for g in vals:
            g["CLASS_GROUP"] = "|".join(key)
            g["CLASS_MEDIAN_PX"] = round(med, 5)
            g["RATIO_TO_CLASS_MEDIAN"] = round(g["H_INK_PX"] / med, 5) if med else None
            g["PIXEL_PASS"] = bool(g["H_INK_PX"] >= g["PIXEL_THRESHOLD_PX"])
            g["SAME_CLASS_PASS"] = bool(g["RATIO_TO_CLASS_MEDIAN"] is not None and 0.92 <= g["RATIO_TO_CLASS_MEDIAN"] <= 1.08)

    cross_groups = defaultdict(lambda: defaultdict(list))
    for g in glyphs:
        cross_groups[(g["ROLE"], g["SCRIPT_CLASS"])][g["PANEL_ID"]].append(g["H_INK_PX"])
    cross_rows = []
    cross_pass = True
    for (role, script), panels in sorted(cross_groups.items()):
        if len(panels) < 2:
            continue
        medians = {panel: float(np.median(values)) for panel, values in panels.items()}
        ratio = max(medians.values()) / min(medians.values()) if min(medians.values()) else float("inf")
        passed = ratio <= 1.10
        cross_pass &= passed
        cross_rows.append({
            "AUDIT_KIND": "CROSS_PANEL_SAME_ROLE_RAW_H_INK",
            "ROLE": role,
            "SCRIPT_CLASS": script,
            "PANEL_MEDIANS_PX": json.dumps({k: round(v, 5) for k, v in medians.items()}, ensure_ascii=False),
            "RATIO_MAX_MIN": round(ratio, 5),
            "THRESHOLD": "<=1.10",
            "PASS_FAIL": "PASS" if passed else "FAIL",
            "METRIC_ORIGIN": "actual_non_dilated_raw_H_ink_px",
        })

    # Source-level role font consistency is independent from the >=9.5pt gate.
    font_groups = defaultdict(list)
    for obj in OBJECTS:
        font_groups[obj["ROLE"]].append(obj)
    for obj in OBJECTS:
        vals = [x["EFFECTIVE_PT"] for x in font_groups[obj["ROLE"]]]
        r = max(vals) / min(vals)
        delta = max(vals) - min(vals)
        obj["SOURCE_ROLE_MAX_MIN"] = r
        obj["SOURCE_ROLE_ABS_DIFF_PT"] = delta
        obj["SOURCE_ROLE_RATIO_PASS"] = r <= 1.03 and delta <= 0.25
        obj["SOURCE_FONT_PASS"] = obj["EFFECTIVE_PT"] >= 9.5 and obj["SOURCE_ROLE_RATIO_PASS"]

    # Role hierarchy uses actual raw H_ink and never declared/PDF font-size proxies.
    def median_for(role, script):
        values = [g["H_INK_PX"] for g in glyphs if g["ROLE"] == role and g["SCRIPT_CLASS"] == script]
        return float(np.median(values)) if values else None

    # E is deliberately script-comparable: it never divides a CJK height by a
    # Latin/Greek/digit/operator height.  The formula role supplies a separate
    # same-script math BASE where available; otherwise the row is explicit N/A.
    cjk_base = median_for("ANNOTATION", "CJK_FULL")
    math_base_by_script = {
        script: median_for("FORMULA", script)
        for script in ("LOWER_GREEK", "UPPER_DIGIT", "MATH_OPERATOR")
    }
    role_rows = []
    role_specs = [
        ("PANEL_TITLE", "CJK_FULL", cjk_base, 1.05, 1.20, "CJK annotation BASE"),
        ("ANNOTATION", "CJK_FULL", cjk_base, 0.95, 1.10, "CJK annotation BASE"),
        ("SUMMARY", "CJK_FULL", cjk_base, 0.95, 1.10, "ordinary annotation against CJK BASE"),
        ("CAPTION", "CJK_FULL", cjk_base, 0.95, 1.10, "caption against CJK BASE"),
        ("FORMULA", "CJK_FULL", cjk_base, 1.00, 1.18, "formula block against CJK BASE"),
        ("FORMULA", "LOWER_GREEK", math_base_by_script["LOWER_GREEK"], 1.00, 1.18, "same-script LOWER_GREEK formula BASE"),
        ("FORMULA", "UPPER_DIGIT", math_base_by_script["UPPER_DIGIT"], 1.00, 1.18, "same-script UPPER_DIGIT formula BASE"),
        ("FORMULA", "MATH_OPERATOR", math_base_by_script["MATH_OPERATOR"], 1.00, 1.18, "same-script MATH_OPERATOR formula BASE"),
        ("STATE_LABEL", "UPPER_DIGIT", math_base_by_script["UPPER_DIGIT"], 0.95, 1.10, "same-script formula BASE"),
        ("STATE_LABEL", "LOWER_GREEK", math_base_by_script["LOWER_GREEK"], 0.95, 1.10, "same-script formula BASE"),
    ]
    covered_role_scripts = set()
    for role, script, base, lo, hi, rationale in role_specs:
        value = median_for(role, script)
        if value is None:
            continue
        covered_role_scripts.add((role, script))
        ratio = value / base if base else None
        passed = bool(ratio is not None and lo <= ratio <= hi)
        role_rows.append({
            "AUDIT_KIND": "ROLE_HIERARCHY_RAW_H_INK",
            "ROLE": role,
            "SCRIPT_CLASS": script,
            "ROLE_MEDIAN_RAW_H_INK_PX": round(value, 5),
            "BASE_MEDIAN_RAW_H_INK_PX": round(base, 5) if base else None,
            "ROLE_RATIO": round(ratio, 5) if ratio is not None else None,
            "EXPECTED_RANGE": f"[{lo:.2f},{hi:.2f}]",
            "BASE_RATIONALE": rationale,
            "APPLICABILITY": "APPLICABLE_SAME_SCRIPT",
            "PASS_FAIL": "PASS" if passed else "FAIL",
            "METRIC_ORIGIN": "actual_non_dilated_raw_H_ink_px",
        })
    # Natural scripts and any role/script lacking a comparable same-script BASE
    # are N/A for E, rather than fabricated cross-script ratio failures.  Their
    # own C gate and their parent source baseline remain separately audited.
    for role, script in sorted({(g["ROLE"], g["SCRIPT_CLASS"]) for g in glyphs} - covered_role_scripts):
        values = [g["H_INK_PX"] for g in glyphs if g["ROLE"] == role and g["SCRIPT_CLASS"] == script]
        role_rows.append({
            "AUDIT_KIND": "ROLE_HIERARCHY_NA_NO_COMPARABLE_SCRIPT_BASE",
            "ROLE": role,
            "SCRIPT_CLASS": script,
            "ROLE_MEDIAN_RAW_H_INK_PX": round(float(np.median(values)), 5),
            "BASE_MEDIAN_RAW_H_INK_PX": None,
            "ROLE_RATIO": None,
            "EXPECTED_RANGE": "N/A — no same-script role BASE in this figure",
            "BASE_RATIONALE": "No cross-script comparison is permitted; source/pixel gates remain independent.",
            "APPLICABILITY": "N/A_NO_COMPARABLE_SCRIPT_BASE",
            "PASS_FAIL": "N/A",
            "METRIC_ORIGIN": "actual_non_dilated_raw_H_ink_px",
        })

    # Exhaustive unique pairs: all semantic TEXT x TEXT and TEXT x every independent vector component.
    pairs = []
    for ia, a in enumerate(OBJECTS):
        for b in OBJECTS[ia + 1:]:
            cross = a["PANEL_ID"] in {"IRR", "PER", "REC"} and b["PANEL_ID"] in {"IRR", "PER", "REC"} and a["PANEL_ID"] != b["PANEL_ID"]
            kind = "CROSS_PANEL_TEXT_TEXT" if cross else "TEXT_TEXT"
            threshold = 8 if cross else 4
            overlap = int(np.logical_and(a["mask"], b["mask"]).sum())
            rawclear = pixel_distance(a["mask"], b["mask"])
            bboxclear = bbox_gap(a["PX_BBOX"], b["PX_BBOX"])
            passed = overlap == 0 and bboxclear >= threshold
            pairs.append({
                "PAIR_ID": f"{a['ELEMENT_ID']}__{b['ELEMENT_ID']}", "PAIR_KIND": kind,
                "A_ID": a["ELEMENT_ID"], "A_TYPE": "TEXT", "B_ID": b["ELEMENT_ID"], "B_TYPE": "TEXT",
                "THRESHOLD_PX": threshold, "OVERLAP_PIXEL_COUNT": overlap, "RAW_CLEARANCE_PX": rawclear,
                "PDF_VECTOR_BBOX_CLEARANCE_PX": bboxclear, "MIN_CLEARANCE_PX": bboxclear,
                "PASS_FAIL": "PASS" if passed else "FAIL", "MASK_A": f"masks/text_raw/{a['ELEMENT_ID']}.png", "MASK_B": f"masks/text_raw/{b['ELEMENT_ID']}.png",
                "mask_a": a["mask"], "mask_b": b["mask"], "bbox_a": a["PX_BBOX"], "bbox_b": b["PX_BBOX"],
            })
    for a in OBJECTS:
        for b in vectors:
            if b["TYPE"] == "NODE_BORDER":
                kind, threshold = "TEXT_NODE_BORDER", 5
            elif b["TYPE"] == "PANEL_BORDER":
                kind, threshold = "TEXT_PANEL_BORDER", 6
            elif b["TYPE"] == "MARKER":
                kind, threshold = "TEXT_MARKER", 3
            elif b["TYPE"] == "ARROWHEAD":
                kind, threshold = "TEXT_ARROWHEAD", 3
            else:
                kind, threshold = "TEXT_LINE_ARROW", 3
            overlap = int(np.logical_and(a["mask"], b["mask"]).sum())
            rawclear = pixel_distance(a["mask"], b["mask"])
            bboxclear = bbox_gap(a["PX_BBOX"], b["PX_BBOX"])
            passed = overlap == 0 and rawclear is not None and rawclear >= threshold
            pairs.append({
                "PAIR_ID": f"{a['ELEMENT_ID']}__{b['ELEMENT_ID']}", "PAIR_KIND": kind,
                "A_ID": a["ELEMENT_ID"], "A_TYPE": "TEXT", "B_ID": b["ELEMENT_ID"], "B_TYPE": b["TYPE"],
                "THRESHOLD_PX": threshold, "OVERLAP_PIXEL_COUNT": overlap, "RAW_CLEARANCE_PX": rawclear,
                "PDF_VECTOR_BBOX_CLEARANCE_PX": bboxclear, "MIN_CLEARANCE_PX": rawclear,
                "PASS_FAIL": "PASS" if passed else "FAIL", "MASK_A": f"masks/text_raw/{a['ELEMENT_ID']}.png", "MASK_B": f"masks/vector_raw/{b['ELEMENT_ID']}.png",
                "mask_a": a["mask"], "mask_b": b["mask"], "bbox_a": a["PX_BBOX"], "bbox_b": b["PX_BBOX"],
            })
    for p in pairs:
        p["CRITICAL_REASON"] = "failure" if p["PASS_FAIL"] == "FAIL" else "nearest_pass_pair"
        val = p["MIN_CLEARANCE_PX"]
        p["critical_sort"] = -1.0 if p["PASS_FAIL"] == "FAIL" else (val if val is not None else 1e9)
    fail_pairs = [p for p in pairs if p["PASS_FAIL"] == "FAIL"]
    nearest = sorted([p for p in pairs if p["PASS_FAIL"] == "PASS"], key=lambda x: x["critical_sort"])[:12]
    critical = fail_pairs + nearest
    # Pair ids are unique by construction; keep no duplicates if a failure had entered the nearest set.
    seen, critical_unique = set(), []
    for p in critical:
        if p["PAIR_ID"] not in seen:
            seen.add(p["PAIR_ID"]); critical_unique.append(p)
    critical_rows = [save_critical_pair(i + 1, pair, rgb, fig_px) for i, pair in enumerate(critical_unique)]

    # Per-object pair maxima feed the mandated glyph table columns.
    pair_by_obj = defaultdict(list)
    for p in pairs:
        pair_by_obj[p["A_ID"]].append(p)
        pair_by_obj[p["B_ID"]].append(p)
    for g in glyphs:
        objpairs = pair_by_obj[g["PARENT_ELEMENT_ID"]]
        g["TEXT_TEXT_OVERLAP_PX"] = max((p["OVERLAP_PIXEL_COUNT"] for p in objpairs if p["PAIR_KIND"] in {"TEXT_TEXT", "CROSS_PANEL_TEXT_TEXT"}), default=0)
        g["TEXT_GRAPHIC_OVERLAP_PX"] = max((p["OVERLAP_PIXEL_COUNT"] for p in objpairs if p["PAIR_KIND"] not in {"TEXT_TEXT", "CROSS_PANEL_TEXT_TEXT"}), default=0)
        g["MIN_CLEARANCE_PX"] = min((p["MIN_CLEARANCE_PX"] for p in objpairs if p["MIN_CLEARANCE_PX"] is not None), default=None)
        g["ROLE_RATIO"] = None
        # This CSV's PASS_FAIL is strictly the C-section glyph-height gate.
        # Same-class D results remain in their own explicit columns/table, so
        # its 17-pixel-failure count cannot be confused with ratio failures.
        g["PASS_FAIL"] = "PASS" if g["PIXEL_PASS"] else "FAIL"
        g["REASON"] = f"H_ink={g['H_INK_PX']}<{g['PIXEL_THRESHOLD_PX']}" if not g["PIXEL_PASS"] else "own glyph H_ink threshold passed; see SAME_CLASS_PASS separately"

    # Edge and clipping audit over every semantic object and vector component.
    edge_rows = []
    all_edge = []
    for x in OBJECTS:
        all_edge.append((x["ELEMENT_ID"], "TEXT", x["PDF_BBOX"], x["PX_BBOX"], x["mask"]))
    for x in vectors:
        all_edge.append((x["ELEMENT_ID"], x["TYPE"], x["PDF_BBOX"], x["PX_BBOX"], x["mask"]))
    min_edge = float("inf")
    clip_total = 0
    figure_bounds = fig_px
    for eid, typ, pbox, pxb, mask in all_edge:
        edge = min(pxb[0] - figure_bounds[0], pxb[1] - figure_bounds[1], figure_bounds[2] - pxb[2], figure_bounds[3] - pxb[3])
        clips = clip_count(mask)
        min_edge = min(min_edge, edge)
        clip_total += clips
        edge_rows.append({"ELEMENT_ID": eid, "TYPE": typ, "PDF_BBOX": json.dumps(pdf_rect_to_dict(pbox), ensure_ascii=False), "BBOX_PX": json.dumps(px_rect_to_dict(pxb)), "FIGURE_EDGE_CLEARANCE_PX": edge, "PAGE_EDGE_CLIP_PIXEL_COUNT": clips, "PASS_FAIL": "PASS" if edge >= 6 and clips == 0 else "FAIL"})

    # All-text measurement overlay: parent object bbox/role labels plus thin glyph rectangles.
    overlay = Image.fromarray(rgb[fig_px[1]:fig_px[3], fig_px[0]:fig_px[2]].copy())
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    colors = {"PANEL_TITLE": (220, 20, 60), "STATE_LABEL": (20, 70, 220), "FORMULA": (130, 20, 170), "ANNOTATION": (0, 120, 90), "CAPTION": (180, 80, 0)}
    for obj in OBJECTS:
        x0, y0, x1, y1 = obj["PX_BBOX"]
        x0 -= fig_px[0]; x1 -= fig_px[0]; y0 -= fig_px[1]; y1 -= fig_px[1]
        col = colors.get(obj["ROLE"], (0, 0, 0))
        draw.rectangle((x0, y0, x1, y1), outline=col, width=2)
        draw.text((x0, max(0, y0 - 10)), f"{obj['ELEMENT_ID']} | {obj['ROLE']}", fill=col, font=font)
        for g in obj["chars"]:
            rr = g["BBOX_PX"]
            draw.rectangle((rr["x0"] - fig_px[0], rr["y0"] - fig_px[1], rr["x1"] - fig_px[0], rr["y1"] - fig_px[1]), outline=(255, 0, 0), width=1)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Audit data files.
    font_rows = []
    for obj in OBJECTS:
        font_rows.append({
            "ELEMENT_ID": obj["ELEMENT_ID"], "PANEL_ID": obj["PANEL_ID"], "ROLE": obj["ROLE"], "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": obj["SOURCE_LINE"],
            "DECLARED_PT": obj["DECLARED_PT"], "DECLARED_DETAIL": obj["DECLARED_DETAIL"], "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": obj["EFFECTIVE_PT"],
            "SOURCE_ROLE_MAX_MIN": round(obj["SOURCE_ROLE_MAX_MIN"], 5), "SOURCE_ROLE_ABS_DIFF_PT": round(obj["SOURCE_ROLE_ABS_DIFF_PT"], 5),
            "SOURCE_ROLE_RATIO_PASS": obj["SOURCE_ROLE_RATIO_PASS"], "SOURCE_FONT_PASS": obj["SOURCE_FONT_PASS"],
            "REASON": "effective_pt<9.5" if obj["EFFECTIVE_PT"] < 9.5 else "effective_pt>=9.5",
        })
    write_csv(OUT / "after_font_audit.csv", font_rows, list(font_rows[0].keys()))
    pixel_rows = []
    for g in glyphs:
        bb = g["BBOX_PX"]
        pixel_rows.append({
            "ELEMENT_ID": g["ELEMENT_ID"], "PARENT_ELEMENT_ID": g["PARENT_ELEMENT_ID"], "PANEL_ID": g["PANEL_ID"], "ROLE": g["ROLE"], "SOURCE_FILE": g["SOURCE_FILE"], "SOURCE_LINE": g["SOURCE_LINE"],
            "DECLARED_PT": g["DECLARED_PT"], "GRAPHICS_SCALE": g["GRAPHICS_SCALE"], "EFFECTIVE_PT": g["EFFECTIVE_PT"], "TEXT_SAMPLE": g["TEXT_SAMPLE"], "SCRIPT_CLASS": g["SCRIPT_CLASS"], "PDF_FONT": g["PDF_FONT"], "PDF_SPAN_PT": g["PDF_SPAN_PT"],
            "BBOX_X0": bb["x0"], "BBOX_Y0": bb["y0"], "BBOX_X1": bb["x1"], "BBOX_Y1": bb["y1"], "H_INK_PX": g["H_INK_PX"], "PIXEL_THRESHOLD_PX": g["PIXEL_THRESHOLD_PX"],
            "CLASS_GROUP": g["CLASS_GROUP"], "CLASS_MEDIAN_PX": g["CLASS_MEDIAN_PX"], "RATIO_TO_CLASS_MEDIAN": g["RATIO_TO_CLASS_MEDIAN"], "ROLE_RATIO": g["ROLE_RATIO"],
            "TEXT_TEXT_OVERLAP_PX": g["TEXT_TEXT_OVERLAP_PX"], "TEXT_GRAPHIC_OVERLAP_PX": g["TEXT_GRAPHIC_OVERLAP_PX"], "MIN_CLEARANCE_PX": g["MIN_CLEARANCE_PX"], "LOCAL_BACKGROUND_RGB": json.dumps(g["LOCAL_BACKGROUND_RGB"]), "PIXEL_PASS": g["PIXEL_PASS"], "SAME_CLASS_PASS": g["SAME_CLASS_PASS"],
            "PASS_FAIL": g["PASS_FAIL"], "REASON": g["REASON"], "RAW_MASK_FILE": f"masks/glyph_raw/{g['ELEMENT_ID']}.png",
        })
    write_csv(OUT / "after_pixel_measurements.csv", pixel_rows, list(pixel_rows[0].keys()))
    ratio_rows = []
    for g in glyphs:
        ratio_rows.append({"ELEMENT_ID": g["ELEMENT_ID"], "PARENT_ELEMENT_ID": g["PARENT_ELEMENT_ID"], "PANEL_ID": g["PANEL_ID"], "ROLE": g["ROLE"], "SCRIPT_CLASS": g["SCRIPT_CLASS"], "H_INK_PX": g["H_INK_PX"], "CLASS_MEDIAN_PX": g["CLASS_MEDIAN_PX"], "RATIO_TO_CLASS_MEDIAN": g["RATIO_TO_CLASS_MEDIAN"], "THRESHOLD": "[0.92,1.08]", "PASS_FAIL": "PASS" if g["SAME_CLASS_PASS"] else "FAIL", "METRIC_ORIGIN": "actual_non_dilated_raw_H_ink_px"})
    ratio_rows.extend(cross_rows)
    write_csv(OUT / "same_class_ratio_audit.csv", ratio_rows, ["ELEMENT_ID", "PARENT_ELEMENT_ID", "PANEL_ID", "ROLE", "SCRIPT_CLASS", "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "THRESHOLD", "PASS_FAIL", "METRIC_ORIGIN", "AUDIT_KIND", "PANEL_MEDIANS_PX", "RATIO_MAX_MIN"])
    write_csv(OUT / "role_ratio_audit.csv", role_rows, list(role_rows[0].keys()) if role_rows else ["AUDIT_KIND"])
    vector_rows = []
    for v in vectors:
        vector_rows.append({"ELEMENT_ID": v["ELEMENT_ID"], "DRAWING_INDEX": v["DRAWING_INDEX"], "TYPE": v["TYPE"], "PANEL_ID": v["PANEL_ID"], "PDF_BBOX": json.dumps(pdf_rect_to_dict(v["PDF_BBOX"])), "BBOX_PX": json.dumps(px_rect_to_dict(v["PX_BBOX"])), "PDF_STROKE_WIDTH_PT": v["PDF_STROKE_WIDTH_PT"], "PDF_DRAWING_TYPE": v["PDF_DRAWING_TYPE"], "RAW_MASK_FILE": f"masks/vector_raw/{v['ELEMENT_ID']}.png", "MASK_METHOD": "independent PDF path recreation on the canonical full-page 300dpi grid; no dilation; no paint-order crop"})
    write_csv(OUT / "vector_component_inventory.csv", vector_rows, list(vector_rows[0].keys()))
    pair_rows = []
    for p in pairs:
        pair_rows.append({
            **{k: p[k] for k in ["PAIR_ID", "PAIR_KIND", "A_ID", "A_TYPE", "B_ID", "B_TYPE", "THRESHOLD_PX", "OVERLAP_PIXEL_COUNT", "RAW_CLEARANCE_PX", "PDF_VECTOR_BBOX_CLEARANCE_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "MASK_A", "MASK_B"]},
            "STRUCTURAL_UNDERLAY_OVERLAP_PX": p["OVERLAP_PIXEL_COUNT"],
            "STRUCTURAL_UNDERLAY_CLEARANCE_PX": p["RAW_CLEARANCE_PX"],
            "PAINT_ORDER_SHIELDED": False,
            "METRIC_METHOD": "separated non-dilated native-300dpi raw masks; independent PDF vector path; no paint-order layer",
        })
    write_csv(OUT / "after_overlap_report.csv", pair_rows, list(pair_rows[0].keys()))
    write_csv(OUT / "after_edge_clip_report.csv", edge_rows, list(edge_rows[0].keys()))
    write_csv(OUT / "critical_pair_index.csv", critical_rows, list(critical_rows[0].keys()) if critical_rows else ["CRITICAL_ID"])
    manifest = ["# FIG-P556-02｜SA1 critical-pair manifest", "", "All masks below are separated, non-dilated native-300dpi masks.  8x files use nearest-neighbour only and are inspection evidence, never a measurement source.", ""]
    for r in critical_rows:
        manifest.append(f"- {r['CRITICAL_ID']:03d} `{r['PAIR_ID']}` — {r['REASON']}; raw={r['RAW_8X_NN_FILE']}; overlay={r['OVERLAY_8X_NN_FILE']}; overlap={r['OVERLAP_8X_NN_FILE']}")
    (OUT / "critical_pair_manifest.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")

    element_map = {
        "TASK_ID": TASK_ID, "PHYSICAL_PAGE": PHYSICAL_PAGE, "PRINTED_PAGE": PRINTED_PAGE, "DPI": DPI, "PIXEL_GRID": "full physical page rasterized directly from frozen main_full.pdf; all crops are pixel slices",
        "FIGURE_RECT_PDF": pdf_rect_to_dict(FIG_RECT), "FIGURE_RECT_PX": px_rect_to_dict(fig_px), "UNASSIGNED_FIGURE_VISIBLE_CHARS": unassigned,
        "TEXT_ELEMENTS": [{"ELEMENT_ID": o["ELEMENT_ID"], "PANEL_ID": o["PANEL_ID"], "ROLE": o["ROLE"], "PDF_BBOX": pdf_rect_to_dict(o["PDF_BBOX"]), "PIXEL_BBOX": px_rect_to_dict(o["PX_BBOX"]), "RAW_MASK": f"masks/text_raw/{o['ELEMENT_ID']}.png", "GLYPH_IDS": [g["ELEMENT_ID"] for g in o["chars"]]} for o in OBJECTS],
        "VECTOR_ELEMENTS": [{"ELEMENT_ID": v["ELEMENT_ID"], "TYPE": v["TYPE"], "PANEL_ID": v["PANEL_ID"], "PDF_BBOX": pdf_rect_to_dict(v["PDF_BBOX"]), "PIXEL_BBOX": px_rect_to_dict(v["PX_BBOX"]), "RAW_MASK": f"masks/vector_raw/{v['ELEMENT_ID']}.png"} for v in vectors],
    }
    (OUT / "element_bbox_map.json").write_text(json.dumps(element_map, ensure_ascii=False, indent=2), encoding="utf-8")

    source_fail_count = sum(not o["SOURCE_FONT_PASS"] for o in OBJECTS)
    glyph_fail_count = sum(not g["PIXEL_PASS"] for g in glyphs)
    same_fail_count = sum(not g["SAME_CLASS_PASS"] for g in glyphs) + sum(r["PASS_FAIL"] == "FAIL" for r in cross_rows)
    role_fail_count = sum(r["PASS_FAIL"] == "FAIL" for r in role_rows if r.get("APPLICABILITY") == "APPLICABLE_SAME_SCRIPT")
    overlap_pixels = sum(p["OVERLAP_PIXEL_COUNT"] for p in fail_pairs)
    min_positive = min((p["MIN_CLEARANCE_PX"] for p in pairs if p["MIN_CLEARANCE_PX"] is not None and p["MIN_CLEARANCE_PX"] > 0), default=None)
    source_role_ratio_pass = all(o["SOURCE_ROLE_RATIO_PASS"] for o in OBJECTS)
    pixel_height_pass = glyph_fail_count == 0
    same_class_pass = same_fail_count == 0
    role_ratio_pass = role_fail_count == 0
    overlap_pass = len(fail_pairs) == 0 and overlap_pixels == 0
    edge_pass = clip_total == 0 and all(r["PASS_FAIL"] == "PASS" for r in edge_rows)
    coverage_pass = len(unassigned) == 0 and all(o["chars"] for o in OBJECTS)
    # Formulae are correct.  The nearby body/caption, however, does not faithfully describe the current three-panel source/PDF.
    math_semantics_pass = True
    caption_pass = False
    text_consistency_pass = False
    reading_order_pass = True
    grayscale_pass = True
    page_integration_pass = True
    visual_harmony_pass = False
    font_harmony_pass = False
    result = all([coverage_pass, source_fail_count == 0, source_role_ratio_pass, pixel_height_pass, same_class_pass, role_ratio_pass, overlap_pass, edge_pass, math_semantics_pass, caption_pass, text_consistency_pass, reading_order_pass, grayscale_pass, page_integration_pass, visual_harmony_pass, font_harmony_pass])
    metrics = {
        "TASK_ID": TASK_ID, "RESULT": "PASS" if result else "FAIL", "NEXT_ROLE": "SA3" if result else "SA2", "PHYSICAL_PAGE": PHYSICAL_PAGE, "PRINTED_PAGE": PRINTED_PAGE, "FIGURE_LABEL": "图30.5",
        "VISIBLE_GLYPH_COUNT": len(glyphs), "SEMANTIC_TEXT_OBJECT_COUNT": len(OBJECTS), "GRAPHIC_COMPONENT_COUNT": len(vectors), "PAIR_COUNT": len(pairs), "CRITICAL_PAIR_COUNT": len(critical_rows),
        "COVERAGE_PASS": coverage_pass, "UNASSIGNED_FIGURE_VISIBLE_CHAR_COUNT": len(unassigned), "SOURCE_FONT_PASS": source_fail_count == 0, "SOURCE_FONT_FAILURE_COUNT": source_fail_count, "SOURCE_ROLE_RATIO_PASS": source_role_ratio_pass,
        "PIXEL_HEIGHT_PASS": pixel_height_pass, "PIXEL_GLYPH_FAILURE_COUNT": glyph_fail_count, "SAME_CLASS_RATIO_PASS": same_class_pass, "SAME_CLASS_RATIO_FAILURE_COUNT": same_fail_count, "ROLE_RATIO_PASS": role_ratio_pass, "ROLE_RATIO_FAILURE_COUNT": role_fail_count,
        "OVERLAP_PIXEL_COUNT": overlap_pixels, "OVERLAP_FAIL_PAIR_COUNT": len(fail_pairs), "PAIR_CLEARANCE_FAILURE_COUNT": len(fail_pairs), "MIN_TEXT_CLEARANCE_PX": min((p["MIN_CLEARANCE_PX"] for p in pairs if p["MIN_CLEARANCE_PX"] is not None), default=None), "MIN_POSITIVE_CLEARANCE_PX": min_positive,
        "CLIP_PIXEL_COUNT": clip_total, "MIN_FIGURE_EDGE_CLEARANCE_PX": min_edge, "EDGE_CLIP_PASS": edge_pass,
        "FONT_VISUAL_HARMONY_PASS": font_harmony_pass, "VISUAL_HARMONY_PASS": visual_harmony_pass, "MATH_SEMANTICS_PASS": math_semantics_pass, "CAPTION_PASS": caption_pass, "TEXT_CONSISTENCY_PASS": text_consistency_pass,
        "READING_ORDER_PASS": reading_order_pass, "GRAYSCALE_PASS": grayscale_pass, "PAGE_INTEGRATION_PASS": page_integration_pass,
    }
    (OUT / "audit_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    semantic = {
        "FIGURE_MATH_SEMANTICS_PASS": True,
        "IRREDUCIBILITY": {"SOURCE_PDF": "two directed arrows 1↔2 plus i↔j (support-graph connectivity)", "BODY": "V5-C01.tex:379 defines mutual reachability/communication; all states communicating means irreducible", "RESULT": "PASS"},
        "PERIODICITY": {"SOURCE_PDF": "d(i)=gcd{n≥1:P_ii^(n)>0}; 2,4,6,8 time markers illustrate return-length set with gcd 2", "BODY": "V5-C01.tex:382-394 defines T_i and d(i)=gcd T_i", "RESULT": "PASS"},
        "POSITIVE_RECURRENCE": {"SOURCE_PDF": "E_i[tau_i^+]<∞ and a return loop", "BODY": "V5-C01.tex:408-428 defines normal recurrence by finite expected first positive return time", "RESULT": "PASS"},
        "SEPARATION": {"SOURCE_PDF": "bottom summary says connectivity, return rhythm and expected return time must be checked separately", "RESULT": "PASS"},
        "CAPTION": {"SOURCE_PDF": "caption says three structures but explicitly explains only irreducibility and periodicity", "MISSING": "normal recurrence / finite E_i[tau_i^+]", "RESULT": "FAIL"},
        "DIRECT_ADJACENT_BODY": {"BODY_LINE_639": "calls this figure three state graphs: reducible aperiodic, irreducible periodic, irreducible aperiodic", "CURRENT_SOURCE_PDF": "is instead a three-card property explainer (irreducibility, periodicity, positive recurrence)", "RESULT": "FAIL"},
        "INDEX_WARNING_HANDLING": "Did not copy the mismatched old-card reading conclusion. Source mathematics -> frozen final PDF -> direct body governed this audit.",
    }
    (OUT / "math_text_semantics_audit.json").write_text(json.dumps(semantic, ensure_ascii=False, indent=2), encoding="utf-8")
    consistency = {
        "CANONICAL_RENDER_METHOD": "Frozen final-PDF full physical page direct 300dpi rasterization; figure and standalone are exact pixel slices; no resize.",
        "NONCANONICAL_DIRECT_CLIP_STATUS": "NOT USED",
        "MASK_METHOD": "separated text char-bbox raw masks and separately recreated PDF vector-path masks; foreground threshold local-background delta>=20/255; no dilation; no paint-order mask used for metrics",
        "UNIQUE_PAIR_COUNTING_RULE": "each unordered semantic TEXT-TEXT or TEXT-VECTOR pair occurs once in after_overlap_report.csv",
        "PAIR_COUNT": len(pairs), "FAIL_PAIR_COUNT": len(fail_pairs), "OVERLAP_PIXEL_COUNT": overlap_pixels, "CLIP_PIXEL_COUNT": clip_total,
        "CRITICAL_PAIR_COUNT": len(critical_rows), "CRITICAL_PAIR_EVIDENCE": "every critical/fail pair has original ROI, separated A/B raw masks, raw intersection, overlay, plus raw/overlay/overlap 8x nearest-neighbour files",
    }
    (OUT / "measurement_consistency.json").write_text(json.dumps(consistency, ensure_ascii=False, indent=2), encoding="utf-8")

    # Human-facing formal reports.
    def fnum(x):
        return "N/A" if x is None else f"{x:.3f}"
    report = f"""# FIG-P556-02（图30.5）｜独立 SA1 严格视觉、文字与数学首审

## 1. 身份、冻结输入与独立定位

- 任务：`{TASK_ID}`；角色：独立只读 SA1；轮次：`STRICT_R1/SA1_20260824_R1`。
- 冻结候选：`{PDF}`。
- 真实定位：物理 PDF 第 **{PHYSICAL_PAGE}** 页、印刷第 **{PRINTED_PAGE}** 页、**图30.5**。这由冻结 PDF 的图号和实际题注定位；未采用旧索引的页码字段。
- 图源：`{SOURCE}`；直接相邻正文：`{BODY}:628,639-640`；公共样式：`{STYLE}:275-276,305`。
- 覆盖：{len(OBJECTS)} 个语义文字对象、{len(glyphs)} 个可见字形/运算符/标点、{len(vectors)} 个独立 PDF 矢量组件、{len(pairs)} 个唯一成对关系。题注自然行流为一个 `CAPTION_PARENT`，未拆成伪文字对象。

## 2. 四视图、固定像素网格与分离 raw mask

`full_page_200dpi.png`、`full_page_300dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png` 与 `grayscale_300dpi.png` 都来自冻结 PDF。唯一测量网格是整张物理页直接 rasterize 的原生 300 dpi 网格；图裁和 standalone 都是该网格的像素切片，绝不 resize。

每个字形以 PDF char bbox 在局部背景差 `>=20/255` 的前景建立未膨胀 raw mask，位于 `masks/glyph_raw/`；文字父对象位于 `masks/text_raw/`。每条边、箭头、箭头头、刻线、marker、节点边框与卡片边框由 PDF path 独立重建到同一网格，位于 `masks/vector_raw/`。节点/卡片填充被排除为背景；数值不使用 paint-order 可见层。本轮没有碰撞失败 pair；仍为 {len(critical_rows)} 个最近临界 pair 保留原图 ROI、双方 raw mask、交集、overlay 与三个最近邻 `8x` 检查图，见 `critical_pair_index.csv` 与 `critical_pair_manifest.md`。

## 3. 源级有效字号

`SOURCE_FONT_PASS: {str(source_fail_count == 0).lower()}`；**{source_fail_count}/{len(OBJECTS)}** 语义对象低于 9.5 pt。面板标题为 10.4 pt、题注 `\\small` 为 10.0 pt（通过）；状态标签 9.4 pt、公式与底部摘要 9.2 pt、三条回答注记 8.8 pt（失败）。同角色 source max/min 和绝对差自身一致（`SOURCE_ROLE_RATIO_PASS: {str(source_role_ratio_pass).lower()}`），但不能抵消最低字号硬失败。完整 declared/effective/font-source 行在 `after_font_audit.csv`；无 graphics scale，`GRAPHICS_SCALE=1.0`。

## 4. 300 dpi 逐字形门

`PIXEL_HEIGHT_PASS: {str(pixel_height_pass).lower()}`；**{glyph_fail_count}/{len(glyphs)}** 字形未达自身阈值。`after_pixel_measurements.csv` 将每个中文/全角字符、大写/数字、小写/希腊、基准数学运算符/标点和自然脚本各自列出 PDF bbox、raw `H_ink_px`、阈值、局部背景、字体及 raw mask；父公式/整行没有替代任何子串。

## 5. 同类、角色比例与 FONT_VISUAL_HARMONY

`SAME_CLASS_RATIO_PASS: {str(same_class_pass).lower()}`；actual raw `H_ink_px` 的同面板、同角色、同脚本审计有 **{same_fail_count}** 个失败行（34 个元素/类比与 2 个跨面板同角色同脚本中位数比），绝未用 declared pt、PDF span-size proxy 或 exact-glyph 分组判门。`ROLE_RATIO_PASS: {str(role_ratio_pass).lower()}`，失败行 **{role_fail_count}**；CJK BASE 是三张卡重复的普通回答注记，而 LOWER_GREEK、UPPER_DIGIT 与 MATH_OPERATOR 分别使用各自同脚本的公式 BASE。没有可比脚本的角色/脚本组合明确写为 `N/A`，不构成跨脚本伪失败；所有数值均在 `role_ratio_audit.csv`。

`FONT_VISUAL_HARMONY_PASS: false`，`VISUAL_HARMONY_PASS: false`。理由是 8.8--9.4 pt 的可见信息角色低于硬下限，并且 raw-H 角色层级存在失败；“适当缩小”不适用，因为它会进一步违反字号、像素、比例和整体阅读门。

## 6. 零重叠、净空、边缘和裁切

`OVERLAP_PIXEL_COUNT: {overlap_pixels}`，`OVERLAP_FAIL_PAIR_COUNT: {len(fail_pairs)}`，`CLIP_PIXEL_COUNT: {clip_total}`。全部文字--文字、跨面板文字--文字、文字--线/箭头/marker、文字--节点边框和文字--卡片边框都登记在 `after_overlap_report.csv`；该表每一无序 pair 仅计一次。最小 raw/bbox 净空为 **{fnum(metrics['MIN_TEXT_CLEARANCE_PX'])} px**，其余最小正净空为 **{fnum(min_positive)} px**；图证据裁边最小 bbox 净空为 **{fnum(min_edge)} px**。边缘/裁切逐项见 `after_edge_clip_report.csv`。

本节的 `OVERLAP/CLIP` 结论只来自双方分离的 native-300dpi raw mask。若本次存在失败或临界对，其交集和 `8x` 证据可由 `critical_pair_manifest.md` 精确追溯。

## 7. 数学、正文、题注、阅读顺序、灰度与页面整合

`MATH_SEMANTICS_PASS: true`：双向 1/2 支撑图与 `i↔j` 正确对应通信/不可约性；`d(i)=gcd{{n≥1:P_ii^(n)>0}}` 与 2,4,6,8 返回时长示意正确表达周期的 gcd；`E_i[tau_i^+]<∞` 正确给出正常返。三者分别回答连通性、回返节律和平均正回返时间，未相互替代。

`CAPTION_PASS: false`，`TEXT_CONSISTENCY_PASS: false`：图注宣称“三类”却只明说不可约性和周期性，遗漏正常返；更直接地，紧邻 `V5-C01.tex:639` 称本图为三类状态图（可约非周期、不可约周期、不可约非周期），而当前源/PDF 是三卡属性解释图。这是独立从 source → frozen PDF → direct body 得出的结论，不沿用错位索引读图结论。详见 `math_text_semantics_audit.json`。

`READING_ORDER_PASS: true`（从左到右：不可约性、周期性、正常返，再读底部总结）；`GRAYSCALE_PASS: true`（文字、边框与箭头在灰度仍可区分）；`PAGE_INTEGRATION_PASS: true`（图、题注及随后图30.6的页内连接无裁切/异常断行）。这些通过项不覆盖字号、像素、比例和文字一致性硬失败。

## 8. 最终矩阵与移交

```text
RESULT: {'PASS' if result else 'FAIL'}
TASK_ID: {TASK_ID}
PHYSICAL_PAGE: {PHYSICAL_PAGE}
PRINTED_PAGE: {PRINTED_PAGE}
COVERAGE_PASS: {str(coverage_pass).lower()}
SOURCE_FONT_PASS: {str(source_fail_count == 0).lower()} ({source_fail_count} failures)
SOURCE_ROLE_RATIO_PASS: {str(source_role_ratio_pass).lower()}
PIXEL_HEIGHT_PASS: {str(pixel_height_pass).lower()} ({glyph_fail_count}/{len(glyphs)} glyph failures)
SAME_CLASS_RATIO_PASS: {str(same_class_pass).lower()} ({same_fail_count} failures; actual raw H_ink)
ROLE_RATIO_PASS: {str(role_ratio_pass).lower()} ({role_fail_count} failures; actual raw H_ink)
OVERLAP_PIXEL_COUNT: {overlap_pixels} ({len(fail_pairs)} failing pairs)
CLIP_PIXEL_COUNT: {clip_total}
MIN_TEXT_CLEARANCE_PX: {fnum(metrics['MIN_TEXT_CLEARANCE_PX'])}
FONT_VISUAL_HARMONY_PASS: false
VISUAL_HARMONY_PASS: false
MATH_SEMANTICS_PASS: true
CAPTION_PASS: false
TEXT_CONSISTENCY_PASS: false
READING_ORDER_PASS: true
GRAYSCALE_PASS: true
PAGE_INTEGRATION_PASS: true
NEXT_ROLE: {'SA3' if result else 'SA2'}
```

SA2 应只修改该图和允许的直接相邻正文：先把答案、公式、状态和摘要提升到有效至少 9.5 pt，再重新排布卡片/间距以保持所有 raw-H 和净空门；补齐图注对正常返的说明，并使正文的图30.5描述与三卡图一致。不得整体缩放规避失败；新候选必须以新 PDF 重新全量 SA1。
"""
    (OUT / "SA1_STRICT_R1_REPORT.md").write_text(report, encoding="utf-8")
    acceptance = f"""# FIG-P556-02｜SA1 visual acceptance

冻结输入 `main_full.pdf` 的真实图位是物理第 {PHYSICAL_PAGE} 页、印刷第 {PRINTED_PAGE} 页、图30.5。300 dpi 的唯一有效口径为整页直出固定网格后切片；不使用 resize 或 direct clip。

| Gate | Result | Evidence |
|---|---|---|
| SOURCE_FONT_PASS | FAIL ({source_fail_count}/{len(OBJECTS)} source objects) | `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | FAIL ({glyph_fail_count}/{len(glyphs)} glyphs) | `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | {'PASS' if same_class_pass else 'FAIL'} ({same_fail_count} actual raw-H rows) | `same_class_ratio_audit.csv` |
| ROLE_RATIO_PASS | {'PASS' if role_ratio_pass else 'FAIL'} ({role_fail_count} actual raw-H rows) | `role_ratio_audit.csv` |
| OVERLAP_PIXEL_COUNT | {'PASS' if overlap_pixels == 0 else 'FAIL'} ({overlap_pixels}, {len(fail_pairs)} pairs) | `after_overlap_report.csv` |
| CLIP_PIXEL_COUNT | {'PASS' if clip_total == 0 else 'FAIL'} ({clip_total}) | `after_edge_clip_report.csv` |
| FONT_VISUAL_HARMONY_PASS | FAIL | four-view inspection + source/raw-H audit |
| MATH_SEMANTICS_PASS | PASS | `math_text_semantics_audit.json` |
| CAPTION/TEXT CONSISTENCY | FAIL | `math_text_semantics_audit.json` |

There are {len(fail_pairs)} collision-failure pairs; the {len(critical_rows)} nearest critical pairs nevertheless have separate raw masks, overlap, overlay and nearest-neighbour 8x ROI. The result is **FAIL → SA2**.
"""
    (OUT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")

    # Machine-readable final artifact completeness check.
    required = [
        "full_page_200dpi.png", "full_page_300dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png", "after_text_measurement_overlay_300dpi.png",
        "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv", "after_edge_clip_report.csv", "same_class_ratio_audit.csv", "role_ratio_audit.csv",
        "vector_component_inventory.csv", "element_bbox_map.json", "measurement_consistency.json", "math_text_semantics_audit.json", "SA1_STRICT_R1_REPORT.md", "after_visual_acceptance.md", "critical_pair_index.csv", "critical_pair_manifest.md", "audit_metrics.json",
    ]
    missing = [x for x in required if not (OUT / x).is_file()]
    missing_8x = []
    for r in critical_rows:
        for col in ["RAW_8X_NN_FILE", "OVERLAY_8X_NN_FILE", "OVERLAP_8X_NN_FILE"]:
            if not (OUT / r[col]).is_file():
                missing_8x.append(f"{r['PAIR_ID']}:{col}")
    check_pass = not missing and not missing_8x and len(pair_rows) == len(pairs) and len(critical_rows) == len(critical_unique)
    final_check = {
        "CHECK_ID": "FIG-P556-02_STRICT_R1_SA1_FINAL_CONSISTENCY", "CHECK_STATUS": "PASS" if check_pass else "FAIL", "FIGURE_RESULT": "PASS" if result else "FAIL",
        "REQUIRED_ARTIFACT_COUNT": len(required), "REQUIRED_ARTIFACT_MISSING": missing, "PAIR_ROWS": len(pair_rows), "PAIR_EXPECTED": len(pairs), "CRITICAL_PAIR_ROWS": len(critical_rows), "CRITICAL_8X_MISSING": missing_8x,
        "METRICS_CROSSCHECK": {"OVERLAP_PIXEL_COUNT": overlap_pixels, "OVERLAP_FAIL_PAIR_COUNT": len(fail_pairs), "CLIP_PIXEL_COUNT": clip_total, "SAME_CLASS_RATIO_PASS": same_class_pass, "ROLE_RATIO_PASS": role_ratio_pass},
        "CANONICAL_GRID": "full-page direct 300dpi; crop slices only; no resize",
    }
    (OUT / "final_consistency_check.json").write_text(json.dumps(final_check, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "final_consistency_check.md").write_text(
        f"# FIG-P556-02｜SA1 machine consistency check\n\n`CHECK_STATUS: {'PASS' if check_pass else 'FAIL'}` verifies {len(required)-len(missing)}/{len(required)} required artifacts, {len(pair_rows)}/{len(pairs)} all-pair rows and {len(critical_rows)} critical 8x sets. It does not override `FIGURE_RESULT: {'PASS' if result else 'FAIL'}`.\n\nCanonical grid: full physical PDF page direct 300dpi, then pixel-slice crop/standalone; no resize. Missing required artifacts: `{missing}`. Missing 8x paths: `{missing_8x}`.\n", encoding="utf-8")
    print(json.dumps({"RESULT": metrics["RESULT"], "NEXT_ROLE": metrics["NEXT_ROLE"], "PHYSICAL_PAGE": PHYSICAL_PAGE, "GLYPHS": len(glyphs), "PAIRS": len(pairs), "OVERLAP": overlap_pixels, "FAIL_PAIRS": len(fail_pairs), "SOURCE_FAIL": source_fail_count, "PIXEL_FAIL": glyph_fail_count, "SAME_FAIL": same_fail_count, "ROLE_FAIL": role_fail_count, "FINAL_MACHINE_CHECK": "PASS" if check_pass else "FAIL"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
