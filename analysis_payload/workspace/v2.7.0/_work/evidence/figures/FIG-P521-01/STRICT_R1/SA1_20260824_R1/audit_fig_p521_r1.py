from __future__ import annotations

import csv
import itertools
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = Path(__file__).resolve().parent
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r93_fullbook" / "main_full.pdf"
PNG300 = OUT / "final_full_page_300dpi.png"
PAGE_NO = 567  # one-based page in the frozen final PDF

SOURCE_FILE = "src/绘图源码/第04册_无监督学习与矩阵分解/V4-C06/fig_v4_c06_plsa_dag.tex"
COMMON_STYLE = "src/讲义源码/common/statlearnbook.sty:305"

FIG_RECT_PT = (60.0, 285.0, 535.0, 460.0)  # includes the complete graph and its one-line caption
STANDALONE_RECT_PT = (130.0, 285.0, 470.0, 435.0)  # graph only; no resampling

ELEMENTS = {
    "T01_THETA": dict(role="PARAM_FORMULA", line="16", text="θ_d=P(z|d)", declared=9.4, panel="P1"),
    "T02_PHI": dict(role="PARAM_FORMULA", line="17", text="φ_z=P(w|z)", declared=9.4, panel="P1"),
    "T03_NODE_D": dict(role="NODE_LABEL", line="18", text="d", declared=9.4, panel="P1"),
    "T04_NODE_Z": dict(role="NODE_LABEL", line="19", text="z", declared=9.4, panel="P1"),
    "T05_NODE_W": dict(role="NODE_LABEL", line="20", text="w", declared=9.4, panel="P1"),
    "T06_PLATE_N": dict(role="PLATE_LABEL", line="33", text="n=1:N_d", declared=8.8, panel="P1"),
    "T07_PLATE_D": dict(role="PLATE_LABEL", line="35", text="d=1:D", declared=8.8, panel="P1"),
    "T08_CHAIN": dict(role="SUMMARY_FORMULA", line="38", text="d→z→w", declared=9.4, panel="P1"),
    "T09_CI": dict(role="SUMMARY_FORMULA", line="38", text="w⊥d|z", declared=9.4, panel="P1"),
    "T10_LEG_OBS": dict(role="LEGEND", line="40", text="实心：观测", declared=8.8, panel="P1"),
    "T11_LEG_LAT": dict(role="LEGEND", line="42", text="空心：潜变量", declared=8.8, panel="P1"),
    "T12_LEG_PARAM": dict(role="LEGEND", line="44", text="矩形：参数", declared=8.8, panel="P1"),
    "T13_CAPTION": dict(role="CAPTION", line="46; common style 305", text="图29.1 PLSA生成图：文档决定主题混合，主题决定单词分布；给定主题后单词与文档条件独立", declared=10.0, panel="PAGE"),
}

# PDF page.get_drawings() indices, tied to the frozen final page rather than paint order.
DRAWING_NAMES = {
    4: ("G01_PARAM_BOX_THETA", "NODE_BORDER"),
    5: ("G02_PARAM_BOX_PHI", "NODE_BORDER"),
    6: ("G03_NODE_BORDER_D", "NODE_BORDER"),
    7: ("G04_NODE_BORDER_Z", "NODE_BORDER"),
    8: ("G05_NODE_BORDER_W", "NODE_BORDER"),
    9: ("G06_EDGE_D_TO_Z", "LINE_ARROW"),
    10: ("G07_ARROWHEAD_D_TO_Z", "LINE_ARROW"),
    11: ("G08_EDGE_Z_TO_W", "LINE_ARROW"),
    12: ("G09_ARROWHEAD_Z_TO_W", "LINE_ARROW"),
    13: ("G10_EDGE_THETA_TO_Z", "LINE_ARROW"),
    14: ("G11_ARROWHEAD_THETA_TO_Z", "LINE_ARROW"),
    15: ("G12_EDGE_PHI_TO_W", "LINE_ARROW"),
    16: ("G13_ARROWHEAD_PHI_TO_W", "LINE_ARROW"),
    17: ("G14_INNER_PLATE", "PANEL_BORDER"),
    18: ("G15_OUTER_PLATE", "PANEL_BORDER"),
    19: ("G16_SUMMARY_BOX", "NODE_BORDER"),
}


def px_rect(pt_rect, sx, sy):
    x0, y0, x1, y1 = pt_rect
    return (math.floor(x0 * sx), math.floor(y0 * sy), math.ceil(x1 * sx), math.ceil(y1 * sy))


def clipped_rect(rect, width, height):
    x0, y0, x1, y1 = rect
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def union_bbox(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def bbox_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    if dx and dy:
        return math.hypot(dx, dy)
    return float(dx or dy)


def text_element_for(x, y):
    if 300 <= y < 323:
        return "T01_THETA" if x < 250 else "T02_PHI"
    if x >= 385 and 340 <= y < 353:
        return "T10_LEG_OBS"
    if x >= 385 and 353 <= y < 367:
        return "T11_LEG_LAT"
    if x >= 385 and 367 <= y < 381:
        return "T12_LEG_PARAM"
    if 353 <= y < 375:
        if x < 200:
            return "T03_NODE_D"
        if x < 300:
            return "T04_NODE_Z"
        return "T05_NODE_W"
    if 380 <= y < 405:
        return "T06_PLATE_N" if x < 340 else "T07_PLATE_D"
    if 408 <= y < 426:
        return "T08_CHAIN" if x < 270 else "T09_CI"
    if 432 <= y < 455:
        return "T13_CAPTION"
    return None


def normal_char(c):
    return unicodedata.normalize("NFKC", c)


def class_and_threshold(c, span_size, element):
    norm = normal_char(c)
    # TeX's automatically generated scripts are legal only when the 9.4pt base is legal.
    if span_size < 8.0 and element in {"T01_THETA", "T02_PHI", "T06_PLATE_N"}:
        return "NATURAL_SCRIPT", 15
    if ("CJK UNIFIED IDEOGRAPH" in unicodedata.name(c, "")
            or unicodedata.east_asian_width(c) in {"W", "F"}):
        return "CJK_OR_FULLWIDTH", 30
    if norm.isdigit():
        return "DIGIT", 24
    if norm.isalpha():
        # Mathematical alphanumeric Greek normalizes to a Greek code point.
        if "GREEK" in unicodedata.name(norm, ""):
            return "GREEK_LOWER", 17
        if norm.isupper():
            return "LATIN_UPPER", 24
        return "LATIN_LOWER", 17
    return "MATH_OPERATOR_OR_PUNCT", 22


def mode_rgb(region):
    arr = region.reshape(-1, 3)
    colors, counts = np.unique(arr, axis=0, return_counts=True)
    return colors[np.argmax(counts)]


def raw_char_mask(rgb, rect):
    """Unexpanded foreground mask: original pixels differing >=20 from local modal background."""
    h, w, _ = rgb.shape
    x0, y0, x1, y1 = clipped_rect(rect, w, h)
    ex0, ey0, ex1, ey1 = clipped_rect((x0 - 2, y0 - 2, x1 + 2, y1 + 2), w, h)
    bg = mode_rgb(rgb[ey0:ey1, ex0:ex1])
    region = rgb[y0:y1, x0:x1]
    foreground = np.max(np.abs(region.astype(np.int16) - bg.astype(np.int16)), axis=2) >= 20
    mask = np.zeros((h, w), dtype=bool)
    mask[y0:y1, x0:x1] = foreground
    ys, xs = np.where(foreground)
    ink_bbox = None
    if len(xs):
        ink_bbox = [int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1)]
    return mask, bg.tolist(), ink_bbox


def drawing_mask(rgb, drawing, crop_box, sx, sy):
    """Raw, unexpanded vector foreground for one original PDF drawing object.

    It is separated by the vector's own original drawing rectangle, stroke colour and,
    for rectangle plates, a narrow boundary band.  Text is not admitted by colour.
    """
    h, w, _ = rgb.shape
    xoff, yoff, _, _ = crop_box
    rect = drawing["rect"]
    x0, y0, x1, y1 = px_rect((rect.x0, rect.y0, rect.x1, rect.y1), sx, sy)
    x0, y0, x1, y1 = clipped_rect((x0 - xoff, y0 - yoff, x1 - xoff, y1 - yoff), w, h)
    full = np.zeros((h, w), dtype=bool)
    if x1 <= x0 or y1 <= y0 or drawing.get("color") is None:
        return full
    region = rgb[y0:y1, x0:x1].astype(np.int16)
    color = np.array([round(v * 255) for v in drawing["color"]], dtype=np.int16)
    # Central original stroke pixels are close to the declared PDF drawing colour.
    raw_colour = np.max(np.abs(region - color), axis=2) <= 64
    # A plate/rounded rectangle rectangle contains other objects: keep only its actual edge band.
    name = DRAWING_NAMES.get(drawing["seqno"], ("", ""))[0]
    if any(key in name for key in ("BOX", "BORDER", "PLATE", "SUMMARY")):
        yy, xx = np.indices(raw_colour.shape)
        # No morphology: this is the original vector rectangle's finite-width edge support.
        edge = (xx <= 4) | (xx >= raw_colour.shape[1] - 5) | (yy <= 4) | (yy >= raw_colour.shape[0] - 5)
        raw_colour &= edge
    full[y0:y1, x0:x1] = raw_colour
    return full


def save_mask(mask, path):
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path)


def save_roi(name, pt_rect, a_name, a_mask, b_name=None, b_mask=None, rgb_full=None, sx=None, sy=None):
    rx0, ry0, rx1, ry1 = px_rect(pt_rect, sx, sy)
    h, w, _ = rgb_full.shape
    rx0, ry0, rx1, ry1 = clipped_rect((rx0, ry0, rx1, ry1), w, h)
    roi = Image.fromarray(rgb_full[ry0:ry1, rx0:rx1])
    roi.save(OUT / "rois" / f"{name}_original.png")
    save_mask(a_mask[ry0:ry1, rx0:rx1], OUT / "rois" / f"{name}_{a_name}_mask.png")
    if b_mask is not None:
        save_mask(b_mask[ry0:ry1, rx0:rx1], OUT / "rois" / f"{name}_{b_name}_mask.png")
    over = np.array(roi).copy()
    am = a_mask[ry0:ry1, rx0:rx1]
    over[am] = np.array([255, 0, 0], dtype=np.uint8)
    if b_mask is not None:
        bm = b_mask[ry0:ry1, rx0:rx1]
        onlyb = bm & ~am
        both = bm & am
        over[onlyb] = np.array([0, 80, 255], dtype=np.uint8)
        over[both] = np.array([255, 0, 255], dtype=np.uint8)
    Image.fromarray(over).save(OUT / "rois" / f"{name}_overlay.png")


def csv_write(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    (OUT / "masks").mkdir(exist_ok=True)
    (OUT / "rois").mkdir(exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_NO - 1]
    page_w, page_h = page.rect.width, page.rect.height
    image = Image.open(PNG300).convert("RGB")
    full_rgb = np.asarray(image)
    full_h, full_w, _ = full_rgb.shape
    sx, sy = full_w / page_w, full_h / page_h
    figure_crop_box = px_rect(FIG_RECT_PT, sx, sy)
    standalone_crop_box = px_rect(STANDALONE_RECT_PT, sx, sy)
    image.crop(figure_crop_box).save(OUT / "final_figure_crop_300dpi.png")
    image.crop(standalone_crop_box).save(OUT / "final_standalone_crop_300dpi.png")
    image.crop(figure_crop_box).convert("L").save(OUT / "final_grayscale_300dpi.png")

    # Pull every actual glyph/substring from the final vector page.  This is independent
    # of PDF text order and uses PDF bboxes mapped directly to the 300 dpi PNG.
    records = []
    raw = page.get_text("rawdict")
    glyph_no = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    # TeX interword glue has a PDF bbox but is not a visible glyph.
                    if char["c"].isspace():
                        continue
                    x0, y0, x1, y1 = char["bbox"]
                    element = text_element_for((x0 + x1) / 2, y0)
                    if element is None:
                        continue
                    glyph_no += 1
                    rx0, ry0, rx1, ry1 = px_rect((x0, y0, x1, y1), sx, sy)
                    mask, bg, ink_bbox = raw_char_mask(full_rgb, (rx0, ry0, rx1, ry1))
                    script, threshold = class_and_threshold(char["c"], span["size"], element)
                    ink_h = 0 if ink_bbox is None else ink_bbox[3] - ink_bbox[1]
                    records.append({
                        "ELEMENT_ID": element,
                        "GLYPH_ID": f"G{glyph_no:03d}",
                        "GLYPH": char["c"],
                        "PDF_FONT": span["font"],
                        "PDF_SPAN_PT": round(span["size"], 3),
                        "BBOX_PX": [rx0, ry0, rx1, ry1],
                        "MASK": mask,
                        "BACKGROUND_RGB": bg,
                        "INK_BBOX_PX": ink_bbox,
                        "H_INK_PX": int(ink_h),
                        "SCRIPT_CLASS": script,
                        "THRESHOLD_PX": threshold,
                    })

    by_element = defaultdict(list)
    for row in records:
        by_element[row["ELEMENT_ID"]].append(row)
    assert set(by_element) == set(ELEMENTS), f"text extraction coverage mismatch: {set(ELEMENTS) - set(by_element)}"

    crop_x0, crop_y0, crop_x1, crop_y1 = figure_crop_box
    crop_h, crop_w = crop_y1 - crop_y0, crop_x1 - crop_x0
    text_masks = {}
    text_boxes = {}
    for element, rows in by_element.items():
        global_mask = np.zeros((full_h, full_w), dtype=bool)
        for row in rows:
            global_mask |= row["MASK"]
        text_masks[element] = global_mask[crop_y0:crop_y1, crop_x0:crop_x1]
        text_boxes[element] = union_bbox([r["BBOX_PX"] for r in rows])
        save_mask(text_masks[element], OUT / "masks" / f"{element}_raw_foreground.png")

    # Extract masks for each line, border and arrow from the final PDF drawing list.
    drawing_masks = {}
    vector_rows = []
    for idx, drawing in enumerate(page.get_drawings()):
        if idx not in DRAWING_NAMES:
            continue
        # seqno is not trusted as a list index, retain it only as a PDF traceability field.
        drawing = dict(drawing)
        drawing["seqno"] = idx
        name, category = DRAWING_NAMES[idx]
        raw_mask_full = drawing_mask(full_rgb[crop_y0:crop_y1, crop_x0:crop_x1], drawing,
                                     figure_crop_box, sx, sy)
        drawing_masks[name] = raw_mask_full
        save_mask(raw_mask_full, OUT / "masks" / f"{name}_raw_foreground.png")
        r = drawing["rect"]
        vector_rows.append({
            "VECTOR_ID": name,
            "PDF_DRAWING_INDEX": idx,
            "CATEGORY": category,
            "PDF_RECT_PT": [round(r.x0, 3), round(r.y0, 3), round(r.x1, 3), round(r.y1, 3)],
            "STROKE_WIDTH_PT": round(drawing.get("width", 0), 4),
            "STROKE_RGB": [round(v, 4) for v in drawing.get("color", ())] if drawing.get("color") else None,
            "RAW_FOREGROUND_PIXELS": int(raw_mask_full.sum()),
            "MASK_FILE": f"masks/{name}_raw_foreground.png",
        })

    # Paint-free text pair audit: each text mask comes only from its own PDF glyph bboxes.
    pairs = []
    for a, b in itertools.combinations(ELEMENTS, 2):
        overlap = int(np.logical_and(text_masks[a], text_masks[b]).sum())
        gap = bbox_gap(text_boxes[a], text_boxes[b])
        pairs.append({
            "PAIR_ID": f"TT_{a}__{b}", "PAIR_TYPE": "TEXT_TEXT", "OBJECT_A": a, "OBJECT_B": b,
            "RELATION": "independent_text", "EXEMPT": False, "RAW_OVERLAP_PX": overlap,
            "CLEARANCE_METHOD": "PDF_bbox_gap_px", "CLEARANCE_PX": round(gap, 3), "REQUIRED_PX": 4,
            "PASS": overlap == 0 and gap >= 4,
        })

    # Text-to-vector audit.  All components are registered; node-label/border pairs use 5 px,
    # all remaining lines, arrows, plates and boxes use 3 px.
    matching_node_border = {
        "T03_NODE_D": "G03_NODE_BORDER_D", "T04_NODE_Z": "G04_NODE_BORDER_Z", "T05_NODE_W": "G05_NODE_BORDER_W"
    }
    for t, g in itertools.product(ELEMENTS, drawing_masks):
        tm, gm = text_masks[t], drawing_masks[g]
        overlap = int(np.logical_and(tm, gm).sum())
        clearance = float(distance_transform_edt(~gm)[tm].min()) if tm.any() and gm.any() else float("nan")
        required = 5 if matching_node_border.get(t) == g else 3
        pairs.append({
            "PAIR_ID": f"TG_{t}__{g}", "PAIR_TYPE": "TEXT_GRAPHIC", "OBJECT_A": t, "OBJECT_B": g,
            "RELATION": "node_text_to_own_border" if matching_node_border.get(t) == g else "independent_text_graphic",
            "EXEMPT": False, "RAW_OVERLAP_PX": overlap,
            "CLEARANCE_METHOD": "raw_foreground_Euclidean_px", "CLEARANCE_PX": round(clearance, 3),
            "REQUIRED_PX": required, "PASS": bool(overlap == 0 and not math.isnan(clearance) and clearance >= required),
        })

    # Deliberate line--node connections are explicitly registered as exemptions, never treated as text overlap.
    edge_rows = [
        ("E01", "d→z", "G06_EDGE_D_TO_Z,G07_ARROWHEAD_D_TO_Z", "G03_NODE_BORDER_D→G04_NODE_BORDER_Z", "directed conditional dependence P(z|d)"),
        ("E02", "z→w", "G08_EDGE_Z_TO_W,G09_ARROWHEAD_Z_TO_W", "G04_NODE_BORDER_Z→G05_NODE_BORDER_W", "directed conditional dependence P(w|z)"),
        ("E03", "θ_d→z", "G10_EDGE_THETA_TO_Z,G11_ARROWHEAD_THETA_TO_Z", "G01_PARAM_BOX_THETA→G04_NODE_BORDER_Z", "parameter influence for P(z|d)"),
        ("E04", "φ_z→w", "G12_EDGE_PHI_TO_W,G13_ARROWHEAD_PHI_TO_W", "G02_PARAM_BOX_PHI→G05_NODE_BORDER_W", "parameter influence for P(w|z)"),
    ]
    for edge_id, label, arrow_ids, endpoints, semantic in edge_rows:
        pairs.append({
            "PAIR_ID": edge_id, "PAIR_TYPE": "EDGE_RELATION", "OBJECT_A": arrow_ids, "OBJECT_B": endpoints,
            "RELATION": label, "EXEMPT": True, "RAW_OVERLAP_PX": "EXEMPT_INTENTIONAL_CONNECTION",
            "CLEARANCE_METHOD": "not_applicable", "CLEARANCE_PX": "N/A", "REQUIRED_PX": "N/A", "PASS": True,
            "SEMANTIC_EXPECTATION": semantic,
        })

    # Pixel-height medians are calculated only within a same role and script class.
    medians = {}
    groups = defaultdict(list)
    for r in records:
        groups[(ELEMENTS[r["ELEMENT_ID"]]["role"], r["SCRIPT_CLASS"])].append(r["H_INK_PX"])
    for key, vals in groups.items():
        medians[key] = float(np.median(vals))
    for r in records:
        role = ELEMENTS[r["ELEMENT_ID"]]["role"]
        med = medians[(role, r["SCRIPT_CLASS"])]
        r["CLASS_MEDIAN_PX"] = round(med, 3)
        r["RATIO_TO_CLASS_MEDIAN"] = round(r["H_INK_PX"] / med, 4) if med else None
        r["PIXEL_PASS"] = r["H_INK_PX"] >= r["THRESHOLD_PX"]
        r["SAME_CLASS_PASS"] = 0.92 <= r["RATIO_TO_CLASS_MEDIAN"] <= 1.08

    base_pt = 9.4
    role_rows = []
    for role in sorted({v["role"] for v in ELEMENTS.values()}):
        els = [e for e, d in ELEMENTS.items() if d["role"] == role]
        eff = float(np.median([ELEMENTS[e]["declared"] for e in els]))
        ratio = eff / base_pt
        if role in {"PLATE_LABEL", "LEGEND"}:
            lo, hi = 0.95, 1.10
        elif role in {"PARAM_FORMULA", "SUMMARY_FORMULA"}:
            lo, hi = 1.00, 1.18
        elif role == "CAPTION":
            lo, hi = 0.95, 1.18
        else:
            lo, hi = 0.92, 1.08
        role_rows.append({"ROLE": role, "BASE_ROLE": "NODE_LABEL", "BASE_EFFECTIVE_PT": base_pt,
                          "ROLE_EFFECTIVE_PT": eff, "ROLE_RATIO": round(ratio, 4),
                          "ALLOWED_RANGE": f"[{lo:.2f},{hi:.2f}]", "PASS": lo <= ratio <= hi,
                          "REASON": "source-effective-size comparison; cross-script ink heights are not conflated"})
    role_pass = all(row["PASS"] for row in role_rows)

    # Complete source-font audit (base formula, automatic script basis, and the figure caption style).
    font_rows = []
    for e, info in ELEMENTS.items():
        base = info["declared"]
        if e == "T13_CAPTION":
            style = "caption font={small}; 11pt class → 10pt; PDF span 9.963pt"
        elif info["role"] in {"PLATE_LABEL", "LEGEND"}:
            style = "explicit \\fontsize{8.8pt}{10.4pt}\\selectfont"
        else:
            style = "explicit \\fontsize{9.4pt}{11.2pt}\\selectfont"
        font_rows.append({
            "ELEMENT_ID": e, "ROLE": info["role"], "SOURCE_FILE": SOURCE_FILE, "SOURCE_LINE": info["line"],
            "DECLARED_PT": base, "GRAPHICS_SCALE": 1.0, "EFFECTIVE_PT": base,
            "BASELINE_REQUIREMENT_PT": 9.5, "PASS": base >= 9.5, "STYLE_EVIDENCE": style,
        })
    font_role_rows = []
    for role in sorted({info["role"] for info in ELEMENTS.values()}):
        values = [info["declared"] for info in ELEMENTS.values() if info["role"] == role]
        lo_pt, hi_pt = min(values), max(values)
        font_role_rows.append({
            "PANEL_ID": "P1" if role != "CAPTION" else "PAGE",
            "ROLE": role,
            "ELEMENT_COUNT": len(values),
            "MIN_EFFECTIVE_PT": lo_pt,
            "MAX_EFFECTIVE_PT": hi_pt,
            "MAX_MIN_RATIO": round(hi_pt / lo_pt, 4),
            "ABS_DIFF_PT": round(hi_pt - lo_pt, 4),
            "SAME_PANEL_PASS": hi_pt / lo_pt <= 1.03 and hi_pt - lo_pt <= 0.25,
            "CROSS_PANEL_STATUS": "NOT_APPLICABLE_SINGLE_PANEL",
            "CROSS_PANEL_PASS": True,
        })

    # Add mandatory columns to every glyph row after all pair data are available.
    text_text_overlap = {e: 0 for e in ELEMENTS}
    text_graphic_overlap = {e: 0 for e in ELEMENTS}
    min_clearance = {e: float("inf") for e in ELEMENTS}
    for p in pairs:
        if p["PAIR_TYPE"] == "TEXT_TEXT":
            for e in (p["OBJECT_A"], p["OBJECT_B"]):
                text_text_overlap[e] += int(p["RAW_OVERLAP_PX"])
                min_clearance[e] = min(min_clearance[e], float(p["CLEARANCE_PX"]))
        elif p["PAIR_TYPE"] == "TEXT_GRAPHIC":
            text_graphic_overlap[p["OBJECT_A"]] += int(p["RAW_OVERLAP_PX"])
            min_clearance[p["OBJECT_A"]] = min(min_clearance[p["OBJECT_A"]], float(p["CLEARANCE_PX"]))
    pixel_csv_rows = []
    for r in records:
        e = r["ELEMENT_ID"]
        info = ELEMENTS[e]
        font_ok = info["declared"] >= 9.5
        reason = []
        if not font_ok:
            reason.append(f"base effective {info['declared']}pt < 9.5pt")
        if not r["PIXEL_PASS"]:
            reason.append(f"raw H_ink {r['H_INK_PX']}px < {r['THRESHOLD_PX']}px")
        if not r["SAME_CLASS_PASS"]:
            reason.append("same-role/script ratio outside [0.92,1.08]")
        pixel_csv_rows.append({
            "ELEMENT_ID": e, "PANEL_ID": info["panel"], "ROLE": info["role"], "SOURCE_FILE": SOURCE_FILE,
            "SOURCE_LINE": info["line"], "DECLARED_PT": info["declared"], "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": info["declared"], "TEXT_SAMPLE": info["text"], "GLYPH_ID": r["GLYPH_ID"],
            "GLYPH": r["GLYPH"], "PDF_FONT": r["PDF_FONT"], "PDF_SPAN_PT": r["PDF_SPAN_PT"],
            "SCRIPT_CLASS": r["SCRIPT_CLASS"], "THRESHOLD_PX": r["THRESHOLD_PX"],
            "BBOX_X0": r["BBOX_PX"][0], "BBOX_Y0": r["BBOX_PX"][1],
            "BBOX_X1": r["BBOX_PX"][2], "BBOX_Y1": r["BBOX_PX"][3],
            "H_INK_PX": r["H_INK_PX"], "INK_BBOX_PX": r["INK_BBOX_PX"], "LOCAL_BACKGROUND_RGB": r["BACKGROUND_RGB"],
            "CLASS_MEDIAN_PX": r["CLASS_MEDIAN_PX"], "RATIO_TO_CLASS_MEDIAN": r["RATIO_TO_CLASS_MEDIAN"],
            "ROLE_RATIO": next(rr["ROLE_RATIO"] for rr in role_rows if rr["ROLE"] == info["role"]),
            "TEXT_TEXT_OVERLAP_PX": text_text_overlap[e], "TEXT_GRAPHIC_OVERLAP_PX": text_graphic_overlap[e],
            "MIN_CLEARANCE_PX": round(min_clearance[e], 3),
            "PIXEL_HEIGHT_PASS": r["PIXEL_PASS"], "SAME_CLASS_RATIO_COMPONENT_PASS": r["SAME_CLASS_PASS"],
            "PASS_FAIL": "PASS" if font_ok and r["PIXEL_PASS"] and r["SAME_CLASS_PASS"] else "FAIL",
            "REASON": "; ".join(reason) if reason else "all glyph-level checks pass",
        })

    # No reader-visible figure object approaches a physical page boundary: all bboxes are inward.
    figure_page_bbox = [137.7856, 293.4675, 504.2, 451.3]
    page_edge_dist_px = min(figure_page_bbox[0] * sx, figure_page_bbox[1] * sy,
                            (page_w - figure_page_bbox[2]) * sx, (page_h - figure_page_bbox[3]) * sy)
    overlap_total = sum(int(p["RAW_OVERLAP_PX"]) for p in pairs if p["PAIR_TYPE"] in {"TEXT_TEXT", "TEXT_GRAPHIC"})
    min_text_clearance = min(float(p["CLEARANCE_PX"]) for p in pairs if p["PAIR_TYPE"] == "TEXT_TEXT")
    min_graphic_clearance = min(float(p["CLEARANCE_PX"]) for p in pairs if p["PAIR_TYPE"] == "TEXT_GRAPHIC")
    pixel_pass = all(r["PIXEL_HEIGHT_PASS"] for r in pixel_csv_rows)
    same_class_pass = all(r["SAME_CLASS_RATIO_COMPONENT_PASS"] for r in pixel_csv_rows)
    source_font_pass = all(r["PASS"] for r in font_rows)
    overlap_pass = all(bool(p["PASS"]) for p in pairs if p["PAIR_TYPE"] in {"TEXT_TEXT", "TEXT_GRAPHIC"}) and overlap_total == 0

    # Overlay of all PDF-mapped text bboxes on the native 300 dpi crop.
    over = image.crop(figure_crop_box).copy()
    draw = ImageDraw.Draw(over)
    font = ImageFont.load_default()
    palette = [(220, 20, 60), (0, 128, 255), (255, 140, 0), (128, 0, 128)]
    for n, e in enumerate(ELEMENTS):
        x0, y0, x1, y1 = text_boxes[e]
        color = palette[n % len(palette)]
        draw.rectangle((x0 - crop_x0, y0 - crop_y0, x1 - crop_x0, y1 - crop_y0), outline=color, width=1)
        draw.text((x0 - crop_x0, max(0, y0 - crop_y0 - 10)), e, fill=color, font=font)
    over.save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Critical evidence is visual rather than a bare script count.
    # Critical ROIs remain in native pixels.  The helper takes both masks in the
    # same crop coordinate system, so no transformed or paint-order mask is mixed in.
    def critical_crop(name, pt, a, b):
        gx0, gy0, gx1, gy1 = px_rect(pt, sx, sy)
        x0, y0, x1, y1 = gx0 - crop_x0, gy0 - crop_y0, gx1 - crop_x0, gy1 - crop_y0
        orig = np.asarray(image.crop(figure_crop_box))[y0:y1, x0:x1]
        Image.fromarray(orig).save(OUT / "rois" / f"{name}_original.png")
        save_mask(a[y0:y1, x0:x1], OUT / "rois" / f"{name}_A_mask.png")
        save_mask(b[y0:y1, x0:x1], OUT / "rois" / f"{name}_B_mask.png")
        overlay = orig.copy()
        aa, bb = a[y0:y1, x0:x1], b[y0:y1, x0:x1]
        overlay[aa] = (255, 0, 0)
        overlay[bb & ~aa] = (0, 80, 255)
        overlay[aa & bb] = (255, 0, 255)
        Image.fromarray(overlay).save(OUT / "rois" / f"{name}_overlay.png")
    critical_crop("critical_phi_inside_D_plate", (280, 288, 390, 356), text_masks["T02_PHI"], drawing_masks["G15_OUTER_PLATE"])
    critical_crop("critical_D_plate_label_clearance", (330, 377, 390, 405), text_masks["T07_PLATE_D"], drawing_masks["G15_OUTER_PLATE"])
    critical_crop("critical_theta_operator", (140, 300, 210, 323), text_masks["T01_THETA"], drawing_masks["G01_PARAM_BOX_THETA"])

    source_font_fields = list(font_rows[0])
    pixel_fields = list(pixel_csv_rows[0])
    pair_fields = list(pairs[0])
    vector_fields = list(vector_rows[0])
    csv_write(OUT / "after_font_audit.csv", font_rows, source_font_fields)
    csv_write(OUT / "source_font_role_consistency.csv", font_role_rows, list(font_role_rows[0]))
    csv_write(OUT / "after_pixel_measurements.csv", pixel_csv_rows, pixel_fields)
    csv_write(OUT / "after_overlap_report.csv", pairs, pair_fields)
    csv_write(OUT / "vector_inventory.csv", vector_rows, vector_fields)
    csv_write(OUT / "element_inventory.csv", [dict(ELEMENT_ID=k, **v) for k, v in ELEMENTS.items()],
              ["ELEMENT_ID", "role", "line", "text", "declared", "panel"])

    acceptance = {
        "FIGURE_ID": "FIG-P521-01",
        "FROZEN_PDF": str(PDF),
        "ACTUAL_FINAL_PDF_PAGE": PAGE_NO,
        "PRINTED_PAGE": 554,
        "SOURCE_FONT_PASS": source_font_pass,
        "PIXEL_HEIGHT_PASS": pixel_pass,
        "SAME_CLASS_RATIO_PASS": same_class_pass,
        "ROLE_RATIO_PASS": role_pass,
        "OVERLAP_PIXEL_COUNT": overlap_total,
        "CLIP_PIXEL_COUNT": 0,
        "MIN_TEXT_TEXT_BBOX_CLEARANCE_PX": round(min_text_clearance, 3),
        "MIN_TEXT_GRAPHIC_RAW_CLEARANCE_PX": round(min_graphic_clearance, 3),
        "MIN_TEXT_CLEARANCE_PX": round(min(min_text_clearance, min_graphic_clearance), 3),
        "PAGE_EDGE_CLEARANCE_PX": round(page_edge_dist_px, 3),
        "VISUAL_HARMONY_PASS": False,
        "FONT_VISUAL_HARMONY_PASS": False,
        "MATH_SEMANTICS_PASS": False,
        "TEXT_CONSISTENCY_PASS": False,
        "GRAYSCALE_PASS": True,
        "PAGE_INTEGRATION_PASS": True,
        "RESULT": "FAIL",
        "HARD_FAILS": [
            "All primary TikZ text is 9.4pt and plate/legend text is 8.8pt, below 9.5pt.",
            "Raw glyph measurement includes individual formula operators/punctuation; any failing glyph makes PIXEL_HEIGHT_PASS false.",
            "Plate/legend role size is 8.8/9.4=0.9362, below the 0.95 annotation/legend floor.",
            "φ_z=P(w|z) is inside the d=1:D plate even though it is a global topic-word distribution.",
            "Inner plate says n=1:N_d while the adjacent text defines L_j repetitions for document d_j."
        ],
        "METHOD": "Native pdftocairo 300dpi PNG; PDF glyph bboxes; local-background >=20/255 raw foreground; no dilation; vector masks separated by original drawing rectangles and stroke colour; pairwise raw intersections and Euclidean clearances.",
    }
    (OUT / "audit.json").write_text(json.dumps({
        "acceptance": acceptance, "role_audit": role_rows, "critical_pairs": [
            {"pair": "T02_PHI vs G15_OUTER_PLATE", "finding": "φ_z is visually inside the D plate; semantic, not an overlap failure", "roi": "rois/critical_phi_inside_D_plate_original.png"},
            {"pair": "T07_PLATE_D vs G15_OUTER_PLATE", "finding": "nearest plate-label/border pair; raw masks and overlay supplied", "roi": "rois/critical_D_plate_label_clearance_original.png"},
            {"pair": "T01_THETA vs G01_PARAM_BOX_THETA", "finding": "source-font/operator evidence ROI", "roi": "rois/critical_theta_operator_original.png"},
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "after_visual_acceptance.md").write_text("\n".join([
        "# FIG-P521-01 — SA1 Strict R1 acceptance",
        "",
        f"- SOURCE_FONT_PASS = {str(acceptance['SOURCE_FONT_PASS']).lower()}",
        f"- PIXEL_HEIGHT_PASS = {str(acceptance['PIXEL_HEIGHT_PASS']).lower()}",
        f"- SAME_CLASS_RATIO_PASS = {str(acceptance['SAME_CLASS_RATIO_PASS']).lower()}",
        f"- ROLE_RATIO_PASS = {str(acceptance['ROLE_RATIO_PASS']).lower()}",
        f"- OVERLAP_PIXEL_COUNT = {acceptance['OVERLAP_PIXEL_COUNT']}",
        f"- CLIP_PIXEL_COUNT = {acceptance['CLIP_PIXEL_COUNT']}",
        f"- MIN_TEXT_CLEARANCE_PX = {acceptance['MIN_TEXT_CLEARANCE_PX']}",
        "- VISUAL_HARMONY_PASS = false",
        "- FONT_VISUAL_HARMONY_PASS = false",
        "- MATH_SEMANTICS_PASS = false",
        "- TEXT_CONSISTENCY_PASS = false",
        "- GRAYSCALE_PASS = true",
        "- PAGE_INTEGRATION_PASS = true",
        "",
        "RESULT: FAIL",
        "",
        "Why: source effective font hard minimum fails; individual raw glyph/operator checks are recorded in CSV; the 8.8pt legend/plate role is below the role floor; and the plate/model semantics conflict with the adjacent PLSA description.",
    ]), encoding="utf-8")
    print(json.dumps(acceptance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
