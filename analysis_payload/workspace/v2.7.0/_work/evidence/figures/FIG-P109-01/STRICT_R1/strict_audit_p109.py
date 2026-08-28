from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


EVIDENCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P109-01\STRICT_R1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r90_fullbook\main_full.pdf")
PNG = EVIDENCE / "full_page_300dpi.png"
STANDALONE_PNG = EVIDENCE / "standalone_300dpi.png"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C07\fig_v1_c07_convex_set.tex")
COMMON_STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty")

PAGE_INDEX = 115
SCALE = 300.0 / 72.0
FIGURE_CROP = (620, 1200, 1905, 2055)
STANDALONE_CROP = (620, 200, 1905, 1055)


def px_bbox(pdf_bbox, pad=0):
    x0, y0, x1, y1 = pdf_bbox
    return (
        math.floor(x0 * SCALE) - pad,
        math.floor(y0 * SCALE) - pad,
        math.ceil(x1 * SCALE) + pad,
        math.ceil(y1 * SCALE) + pad,
    )


def text_of(span):
    return "".join(c["c"] for c in span["chars"])


def color_mode(crop: np.ndarray):
    flat = crop.reshape(-1, 3)
    # Quantize by two bits to make anti-aliased near-background pixels coalesce.
    q = (flat // 4) * 4
    key, _ = Counter(map(tuple, q.tolist())).most_common(1)[0]
    return np.array(key, dtype=np.int16)


def ink_mask_for_bbox(rgb: np.ndarray, bbox):
    x0, y0, x1, y1 = bbox
    crop = rgb[y0:y1, x0:x1, :3]
    bg = color_mode(crop)
    delta = np.max(np.abs(crop.astype(np.int16) - bg[None, None, :]), axis=2)
    mask = delta >= 20
    # All text in this figure is neutral SLInk/gray.  Exclude visibly blue or
    # teal geometry from a text bbox; the vector masks below independently
    # recover those paths, including portions hidden behind later text.
    px = crop.astype(np.int16)
    colored_geometry = ((px[:, :, 2] - px[:, :, 0] >= 35) & (px[:, :, 1] - px[:, :, 0] >= 8))
    mask &= ~colored_geometry
    return mask, tuple(int(v) for v in bg)


def mask_geometry(mask: np.ndarray, bbox):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None, 0, 0
    x0, y0, _, _ = bbox
    ink_bbox = (int(xs.min() + x0), int(ys.min() + y0), int(xs.max() + x0 + 1), int(ys.max() + y0 + 1))
    return ink_bbox, int(ys.max() - ys.min() + 1), int(mask.sum())


def cubic(p0, p1, p2, p3, n=32):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t**3 * p3.y
        out.append((round(x * SCALE), round(y * SCALE)))
    return out


def drawing_stroke_mask(size, drawing):
    image = Image.new("1", size, 0)
    draw = ImageDraw.Draw(image)
    width = max(1, math.ceil(float(drawing.get("width") or 0.5) * SCALE))
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            p0, p1 = item[1], item[2]
            draw.line([(round(p0.x * SCALE), round(p0.y * SCALE)), (round(p1.x * SCALE), round(p1.y * SCALE))], fill=1, width=width)
        elif kind == "c":
            pts = cubic(item[1], item[2], item[3], item[4])
            draw.line(pts, fill=1, width=width)
        elif kind == "re":
            r = item[1]
            draw.rectangle(px_bbox(tuple(r)), outline=1, width=width)
    return np.array(image, dtype=bool)


def drawing_fill_mask(size, drawing):
    image = Image.new("1", size, 0)
    draw = ImageDraw.Draw(image)
    r = drawing["rect"]
    draw.ellipse(px_bbox(tuple(r)), fill=1)
    return np.array(image, dtype=bool)


def globalize(local_mask, bbox, shape):
    result = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = bbox
    result[y0:y1, x0:x1] = local_mask
    return result


def clearance_and_overlap(mask_a, mask_b):
    overlap = int(np.count_nonzero(mask_a & mask_b))
    if overlap:
        ys, xs = np.nonzero(mask_a & mask_b)
        overlap_bbox = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
        return overlap, 0.0, overlap_bbox, None, None
    if not mask_a.any() or not mask_b.any():
        return overlap, None, None, None, None
    dist, nearest = distance_transform_edt(~mask_b, return_indices=True)
    ys, xs = np.nonzero(mask_a)
    values = dist[ys, xs]
    which = int(np.argmin(values))
    ay, ax = int(ys[which]), int(xs[which])
    by, bx = int(nearest[0, ay, ax]), int(nearest[1, ay, ax])
    return overlap, float(values[which]), None, (ax, ay), (bx, by)


def char_class(ch):
    if "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf":
        return "CJK", 30
    if ch.isdigit() or ch in {"𝐶", "C"}:
        return "LATIN_CAP_OR_DIGIT", 24
    if ch in {"𝑥", "𝑦", "𝑧", "𝜆", "x", "y", "z", "λ"}:
        return "LATIN_LOWER_OR_GREEK", 17
    if ch in {"=", "+", "−", "-", "∈", "⟹", "[", "]", "(", ")"}:
        return "BASE_MATH_OPERATOR", 22
    return "PUNCTUATION_SOURCE_CONTROLLED", 0


def main():
    image = Image.open(PNG).convert("RGB")
    assert image.size == (2481, 3508), image.size
    rgb = np.asarray(image)
    h, w = rgb.shape[:2]

    image.crop(FIGURE_CROP).save(EVIDENCE / "figure_crop_300dpi.png")
    ImageOps.grayscale(image.crop(FIGURE_CROP)).save(EVIDENCE / "grayscale_300dpi.png")
    standalone = Image.open(STANDALONE_PNG).convert("RGB")
    assert standalone.size == (2481, 3508), standalone.size
    standalone.crop(STANDALONE_CROP).save(EVIDENCE / "standalone_figure_crop_300dpi.png")

    roi_boxes = {
        "roi_endpoint_x_300dpi_1to1.png": (760, 1590, 980, 1815),
        "roi_endpoint_y_region_300dpi_1to1.png": (1510, 1230, 1810, 1485),
        "roi_formula_segment_300dpi_1to1.png": (900, 1400, 1380, 1650),
        "roi_note_300dpi_1to1.png": (820, 1840, 1710, 2010),
        "roi_figure_caption_clearance_300dpi_1to1.png": (800, 1880, 1740, 2070),
    }
    for name, box in roi_boxes.items():
        image.crop(box).save(EVIDENCE / name)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    spans = []
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                y0 = span["bbox"][1]
                if 300 <= y0 <= 500:
                    spans.append(span)

    def pick(text, ylo, yhi):
        matches = [s for s in spans if text_of(s) == text and ylo <= s["bbox"][1] <= yhi]
        if len(matches) != 1:
            raise RuntimeError((text, ylo, yhi, [(text_of(s), s["bbox"]) for s in matches]))
        return matches[0]

    sx = pick("𝑥", 400, 430)
    sy = pick("𝑦", 315, 340)
    sz = pick("𝑧= 𝜆𝑥+ (1 −𝜆)𝑦", 345, 370)
    sregion = pick("凸可行域", 305, 330)
    sregion_c = pick("𝐶", 305, 330)
    note_spans = [s for s in spans if 450 <= s["bbox"][1] <= 470 and text_of(s).strip()]
    cap_label = pick("图", 470, 490)
    cap_number = pick("7.1", 470, 490)
    cap_text = pick("凸集中任意两点的线段仍位于可行域内", 470, 495)

    rows = []
    semantic_masks = {}

    def add_semantic(element_id, span_list, role, source_line, declared_pt, effective_pt, sample, script_class, ratio_group):
        x0 = min(s["bbox"][0] for s in span_list)
        y0 = min(s["bbox"][1] for s in span_list)
        x1 = max(s["bbox"][2] for s in span_list)
        y1 = max(s["bbox"][3] for s in span_list)
        bbox = px_bbox((x0, y0, x1, y1), pad=1)
        local, bg = ink_mask_for_bbox(rgb, bbox)
        ink_bbox, height, pixels = mask_geometry(local, bbox)
        global_mask = globalize(local, bbox, (h, w))
        semantic_masks[element_id] = global_mask
        rows.append({
            "ELEMENT_ID": element_id,
            "PANEL_ID": "P109_MAIN",
            "ROLE": role,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": source_line,
            "DECLARED_PT": declared_pt,
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": effective_pt,
            "PDF_FONT_SIZE_BP": round(span_list[0]["size"], 4),
            "TEXT_SAMPLE": sample,
            "SCRIPT_CLASS": script_class,
            "RATIO_GROUP": ratio_group,
            "BBOX_X0": bbox[0], "BBOX_Y0": bbox[1], "BBOX_X1": bbox[2], "BBOX_Y1": bbox[3],
            "INK_BBOX": ink_bbox,
            "H_INK_PX": height,
            "INK_PIXEL_COUNT": pixels,
            "BACKGROUND_RGB_Q4": bg,
            "PIXEL_THRESHOLD": "mixed; class-specific children below",
            "PIXEL_PASS": "SEE_CHILDREN",
            "SOURCE_FONT_PASS": effective_pt >= 9.5,
        })

    add_semantic("T_ENDPOINT_X", [sx], "POINT_LABEL", 24, 10.0, 10.0, "x", "LATIN_LOWER_OR_GREEK", "POINT_LABEL")
    add_semantic("T_ENDPOINT_Y", [sy], "POINT_LABEL", 25, 10.0, 10.0, "y", "LATIN_LOWER_OR_GREEK", "POINT_LABEL")
    add_semantic("T_FORMULA_Z", [sz], "FORMULA_BLOCK", 28, 9.2, 9.2, "z=lambda*x+(1-lambda)*y", "MIXED_MATH", "FORMULA_LINE")
    add_semantic("T_REGION_CJK", [sregion], "ORDINARY_ANNOTATION", 30, 9.2, 9.2, "凸可行域", "CJK", "REGION_LABEL")
    add_semantic("T_REGION_C", [sregion_c], "ORDINARY_ANNOTATION", 30, 9.2, 9.2, "C", "LATIN_CAP_OR_DIGIT", "REGION_LABEL")
    add_semantic("T_FORMULA_CONCLUSION", note_spans, "FORMULA_BLOCK", "32-33", 9.2, 9.2, "x,y in C, lambda in [0,1] => lambda*x+(1-lambda)*y in C", "MIXED_MATH", "FORMULA_LINE")
    add_semantic("T_CAPTION_LABEL", [cap_label, cap_number], "CAPTION_LABEL", "35; common style 305", 10.0, 10.0, "图 7.1", "MIXED_CJK_DIGIT", "CAPTION_LABEL")
    add_semantic("T_CAPTION_TEXT", [cap_text], "CAPTION_TEXT", "35; common style 305", 10.0, 10.0, "凸集中任意两点的线段仍位于可行域内", "CJK", "CAPTION_TEXT")

    char_parent_specs = [
        ("X", [sx], "POINT_LABEL", 24, 10.0),
        ("Y", [sy], "POINT_LABEL", 25, 10.0),
        ("Z", [sz], "FORMULA_BLOCK", 28, 9.2),
        ("REG", [sregion, sregion_c], "ORDINARY_ANNOTATION", 30, 9.2),
        ("CONC", note_spans, "FORMULA_BLOCK", "32-33", 9.2),
        ("CAPLBL", [cap_label, cap_number], "CAPTION_LABEL", "35; common style 305", 10.0),
        ("CAPTXT", [cap_text], "CAPTION_TEXT", "35; common style 305", 10.0),
    ]
    char_counter = Counter()
    char_rows = []
    for prefix, span_list, role, source_line, effective_pt in char_parent_specs:
        for span in span_list:
            for char in span["chars"]:
                ch = char["c"]
                if ch.isspace():
                    continue
                char_counter[(prefix, ch)] += 1
                n = char_counter[(prefix, ch)]
                element_id = f"G_{prefix}_{ord(ch):04X}_{n:02d}"
                bbox = px_bbox(char["bbox"], pad=1)
                local, bg = ink_mask_for_bbox(rgb, bbox)
                ink_bbox, height, pixels = mask_geometry(local, bbox)
                cls, threshold = char_class(ch)
                if threshold:
                    pixel_pass = height >= threshold
                else:
                    pixel_pass = "SOURCE_CONTROLLED"
                char_rows.append({
                    "ELEMENT_ID": element_id,
                    "PARENT": prefix,
                    "ROLE": role,
                    "SOURCE_LINE": source_line,
                    "EFFECTIVE_PT": effective_pt,
                    "CHAR": ch,
                    "SCRIPT_CLASS": cls,
                    "BBOX_X0": bbox[0], "BBOX_Y0": bbox[1], "BBOX_X1": bbox[2], "BBOX_Y1": bbox[3],
                    "INK_BBOX": ink_bbox,
                    "H_INK_PX": height,
                    "THRESHOLD_PX": threshold or "SOURCE_CONTROLLED",
                    "PASS_FAIL": "PASS" if pixel_pass is True or pixel_pass == "SOURCE_CONTROLLED" else "FAIL",
                    "INK_PIXEL_COUNT": pixels,
                    "BACKGROUND_RGB_Q4": bg,
                })

    # Same-role measurements use semantic line/label masks, not unlike glyph shapes.
    group_members = {
        "POINT_LABEL": ["T_ENDPOINT_X", "T_ENDPOINT_Y"],
        "FORMULA_LINE": ["T_FORMULA_Z", "T_FORMULA_CONCLUSION"],
    }
    semantic_by_id = {r["ELEMENT_ID"]: r for r in rows}
    ratio_rows = []
    for group, ids in group_members.items():
        vals = [semantic_by_id[i]["H_INK_PX"] for i in ids]
        median = float(np.median(vals))
        for i, value in zip(ids, vals):
            ratio = value / median
            ratio_rows.append({
                "RATIO_GROUP": group,
                "ELEMENT_ID": i,
                "H_INK_PX": value,
                "CLASS_MEDIAN_PX": median,
                "RATIO_TO_CLASS_MEDIAN": round(ratio, 6),
                "PASS_FAIL": "PASS" if 0.92 <= ratio <= 1.08 else "FAIL",
            })

    drawings = page.get_drawings()
    boundary = drawing_stroke_mask((w, h), drawings[7])
    segment = drawing_stroke_mask((w, h), drawings[8])
    marker_x = drawing_fill_mask((w, h), drawings[9])
    marker_y = drawing_fill_mask((w, h), drawings[10])
    marker_25 = drawing_fill_mask((w, h), drawings[11])
    marker_50 = drawing_fill_mask((w, h), drawings[12])
    marker_75 = drawing_fill_mask((w, h), drawings[13])
    note_border = drawing_stroke_mask((w, h), drawings[15])

    graphics = {
        "G_BOUNDARY": boundary,
        "G_SEGMENT": segment,
        "M_ENDPOINT_X": marker_x,
        "M_ENDPOINT_Y": marker_y,
        "M_INTERIOR_25": marker_25,
        "M_INTERIOR_50": marker_50,
        "M_INTERIOR_75": marker_75,
        "N_NOTE_BORDER": note_border,
    }
    risk_pairs = [
        ("T_ENDPOINT_X", "M_ENDPOINT_X", "TEXT-MARKER", 3),
        ("T_ENDPOINT_X", "G_BOUNDARY", "TEXT-DATA_CURVE", 3),
        ("T_ENDPOINT_Y", "M_ENDPOINT_Y", "TEXT-MARKER", 3),
        ("T_ENDPOINT_Y", "G_BOUNDARY", "TEXT-DATA_CURVE", 3),
        ("T_FORMULA_Z", "G_SEGMENT", "FORMULA-LINE", 3),
        ("T_FORMULA_Z", "M_INTERIOR_50", "FORMULA-MARKER", 3),
        ("T_REGION_CJK", "G_BOUNDARY", "TEXT-DATA_CURVE", 3),
        ("T_REGION_C", "G_BOUNDARY", "TEXT-DATA_CURVE", 3),
        ("T_FORMULA_CONCLUSION", "N_NOTE_BORDER", "FORMULA-NODE_BORDER", 5),
        ("T_FORMULA_CONCLUSION", "G_BOUNDARY", "FORMULA-DATA_CURVE", 3),
        ("T_CAPTION_LABEL", "N_NOTE_BORDER", "TEXT-NODE_BORDER", 3),
        ("T_CAPTION_TEXT", "N_NOTE_BORDER", "TEXT-NODE_BORDER", 3),
    ]
    overlap_rows = []
    for a, b, kind, required in risk_pairs:
        overlap, clearance, overlap_bbox, nearest_a, nearest_b = clearance_and_overlap(semantic_masks[a], graphics[b])
        overlap_rows.append({
            "OBJECT_A": a, "OBJECT_B": b, "PAIR_CLASS": kind,
            "OVERLAP_PIXEL_COUNT": overlap,
            "OVERLAP_BBOX": overlap_bbox,
            "MIN_CLEARANCE_PX": None if clearance is None else round(clearance, 6),
            "NEAREST_A_XY": nearest_a,
            "NEAREST_B_XY": nearest_b,
            "REQUIRED_CLEARANCE_PX": required,
            "PASS_FAIL": "PASS" if overlap == 0 and clearance is not None and clearance >= required else "FAIL",
        })

    text_pairs = [
        ("T_ENDPOINT_Y", "T_REGION_C", "TEXT-TEXT", 4),
        ("T_REGION_CJK", "T_REGION_C", "TEXT-TEXT", 4),
        ("T_FORMULA_CONCLUSION", "T_CAPTION_LABEL", "TEXT-TEXT", 4),
        ("T_FORMULA_CONCLUSION", "T_CAPTION_TEXT", "TEXT-TEXT", 4),
    ]
    for a, b, kind, required in text_pairs:
        overlap, clearance, overlap_bbox, nearest_a, nearest_b = clearance_and_overlap(semantic_masks[a], semantic_masks[b])
        overlap_rows.append({
            "OBJECT_A": a, "OBJECT_B": b, "PAIR_CLASS": kind,
            "OVERLAP_PIXEL_COUNT": overlap,
            "OVERLAP_BBOX": overlap_bbox,
            "MIN_CLEARANCE_PX": None if clearance is None else round(clearance, 6),
            "NEAREST_A_XY": nearest_a,
            "NEAREST_B_XY": nearest_b,
            "REQUIRED_CLEARANCE_PX": required,
            "PASS_FAIL": "PASS" if overlap == 0 and clearance is not None and clearance >= required else "FAIL",
        })

    edge_rows = []
    fx0, fy0, fx1, fy1 = FIGURE_CROP
    for element_id, mask in semantic_masks.items():
        ys, xs = np.nonzero(mask)
        outside = int(np.count_nonzero((xs < fx0) | (xs >= fx1) | (ys < fy0) | (ys >= fy1)))
        edge_clearance = int(min(xs.min() - fx0, fx1 - 1 - xs.max(), ys.min() - fy0, fy1 - 1 - ys.max()))
        edge_rows.append({
            "ELEMENT_ID": element_id,
            "CLIP_PIXEL_COUNT": outside,
            "MIN_FIGURE_CROP_EDGE_CLEARANCE_PX": edge_clearance,
            "REQUIRED_EDGE_CLEARANCE_PX": 6,
            "PASS_FAIL": "PASS" if outside == 0 and edge_clearance >= 6 else "FAIL",
        })

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    colors = ["#d62728", "#9467bd", "#ff7f0e", "#17becf", "#2ca02c", "#8c564b", "#e377c2", "#bcbd22"]
    for idx, row in enumerate(rows):
        box = (row["BBOX_X0"], row["BBOX_Y0"], row["BBOX_X1"], row["BBOX_Y1"])
        color = colors[idx % len(colors)]
        draw.rectangle(box, outline=color, width=2)
        draw.text((box[0], max(0, box[1] - 13)), row["ELEMENT_ID"], fill=color)
    overlay.crop(FIGURE_CROP).save(EVIDENCE / "text_measurement_overlay_300dpi.png")

    fail_overlay = image.copy()
    fail_rgb = np.asarray(fail_overlay).copy()
    overlap_region = semantic_masks["T_REGION_C"] & boundary
    fail_rgb[overlap_region] = np.array([255, 0, 0], dtype=np.uint8)
    # Mark the one-pixel CJK-to-boundary clearance pair in magenta/cyan.
    cjk_pair = next(r for r in overlap_rows if r["OBJECT_A"] == "T_REGION_CJK" and r["OBJECT_B"] == "G_BOUNDARY")
    if cjk_pair["NEAREST_A_XY"] and cjk_pair["NEAREST_B_XY"]:
        ax, ay = cjk_pair["NEAREST_A_XY"]
        bx, by = cjk_pair["NEAREST_B_XY"]
        fail_rgb[max(0, ay - 2):ay + 3, max(0, ax - 2):ax + 3] = np.array([255, 0, 255], dtype=np.uint8)
        fail_rgb[max(0, by - 2):by + 3, max(0, bx - 2):bx + 3] = np.array([0, 255, 255], dtype=np.uint8)
    Image.fromarray(fail_rgb).crop(roi_boxes["roi_endpoint_y_region_300dpi_1to1.png"]).save(
        EVIDENCE / "roi_region_boundary_overlap_overlay_300dpi_1to1.png"
    )

    with (EVIDENCE / "after_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with (EVIDENCE / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(char_rows[0].keys()))
        writer.writeheader()
        writer.writerows(char_rows)
    with (EVIDENCE / "after_same_class_ratios.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(ratio_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ratio_rows)
    with (EVIDENCE / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(overlap_rows[0].keys()))
        writer.writeheader()
        writer.writerows(overlap_rows)
    with (EVIDENCE / "clip_and_edge_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(edge_rows[0].keys()))
        writer.writeheader()
        writer.writerows(edge_rows)

    drawing_manifest = []
    for idx in range(7, 16):
        d = drawings[idx]
        drawing_manifest.append({
            "DRAWING_INDEX": idx,
            "TYPE": d["type"],
            "PDF_BBOX": [round(v, 6) for v in tuple(d["rect"])],
            "PIXEL_BBOX": list(px_bbox(tuple(d["rect"]))),
            "STROKE_RGB_0_1": d["color"],
            "FILL_RGB_0_1": d["fill"],
            "WIDTH_PT": d["width"],
        })
    summary = {
        "PDF": str(PDF),
        "PHYSICAL_PAGE_1_BASED": 116,
        "PAGE_COUNT": doc.page_count,
        "PAGE_SIZE_PT": [page.rect.width, page.rect.height],
        "FULL_PAGE_300DPI_SIZE": list(image.size),
        "FIGURE_CROP": list(FIGURE_CROP),
        "STANDALONE_CROP": list(STANDALONE_CROP),
        "PIXEL_HEIGHT_FAIL_IDS": [r["ELEMENT_ID"] for r in char_rows if r["PASS_FAIL"] == "FAIL"],
        "SOURCE_FONT_FAIL_IDS": [r["ELEMENT_ID"] for r in rows if not r["SOURCE_FONT_PASS"]],
        "RATIO_FAIL_IDS": [r["ELEMENT_ID"] for r in ratio_rows if r["PASS_FAIL"] == "FAIL"],
        "OVERLAP_FAIL_PAIRS": [f"{r['OBJECT_A']}::{r['OBJECT_B']}" for r in overlap_rows if r["PASS_FAIL"] == "FAIL"],
        "MAX_OVERLAP_PIXEL_COUNT": max(r["OVERLAP_PIXEL_COUNT"] for r in overlap_rows),
        "MIN_MEASURED_CLEARANCE_PX": min(r["MIN_CLEARANCE_PX"] for r in overlap_rows if r["MIN_CLEARANCE_PX"] is not None),
        "CLIP_PIXEL_COUNT": sum(r["CLIP_PIXEL_COUNT"] for r in edge_rows),
        "MIN_FIGURE_CROP_EDGE_CLEARANCE_PX": min(r["MIN_FIGURE_CROP_EDGE_CLEARANCE_PX"] for r in edge_rows),
        "DRAWINGS": drawing_manifest,
        "ROI_BOXES": roi_boxes,
    }
    (EVIDENCE / "audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
