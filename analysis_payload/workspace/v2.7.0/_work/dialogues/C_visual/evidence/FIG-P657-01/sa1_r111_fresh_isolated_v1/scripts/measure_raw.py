from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa1_r111_fresh_isolated_v1")
PAGE_PATH = ROOT / "raw" / "page706_native300dpi.png"
PAGE_W_PT = 595.276
PAGE_H_PT = 841.89
FIGURE_CROP = (330, 1100, 2210, 1925)

page = Image.open(PAGE_PATH).convert("RGB")
gray = np.asarray(page.convert("L"))
sx, sy = page.width / PAGE_W_PT, page.height / PAGE_H_PT


def pxbbox(box):
    x0, top, x1, bottom = box
    return (
        max(0, math.floor(x0 * sx)),
        max(0, math.floor(top * sy)),
        min(page.width, math.ceil(x1 * sx)),
        min(page.height, math.ceil(bottom * sy)),
    )


# Exact word/line boxes transcribed from pdfplumber extraction of official R111 physical page 706.
elements = [
    ("T01", "FIGURE", "ROW_HEADING", 18, 9.5, "先验族", "CJK_FULL", (117.69, 284.70, 146.08, 294.16)),
    ("T02", "FIGURE", "NODE_LABEL", 19, 9.4, "Dirichlet分布", "MIXED_CJK_LATIN", (187.35, 284.26, 243.67, 293.93)),
    ("T03", "FIGURE", "NODE_LABEL", 20, 9.4, "Beta分布", "MIXED_CJK_LATIN", (342.17, 279.19, 380.82, 288.87)),
    ("T04", "FIGURE", "NODE_MATH", 20, 9.4, "𝐾=2", "MATH_BASE", (349.83, 290.45, 373.15, 299.82)),
    ("T05", "FIGURE", "ROW_HEADING", 21, 9.5, "似然族", "CJK_FULL", (117.69, 345.64, 146.08, 355.11)),
    ("T06", "FIGURE", "NODE_LABEL", 22, 9.4, "多项分布", "CJK_FULL", (196.78, 345.52, 234.24, 354.88)),
    ("T07", "FIGURE", "NODE_LABEL", 23, 9.4, "二项分布", "CJK_FULL", (342.76, 340.45, 380.22, 349.81)),
    ("T08", "FIGURE", "NODE_MATH", 23, 9.4, "𝐾=2", "MATH_BASE", (349.83, 351.40, 373.15, 360.76)),
    ("T09", "FIGURE", "ROW_HEADING", 24, 9.5, "单次试验", "CJK_FULL", (112.96, 406.59, 150.82, 416.05)),
    ("T10", "FIGURE", "NODE_LABEL", 25, 9.4, "类别分布", "CJK_FULL", (196.78, 401.36, 234.24, 410.72)),
    ("T11", "FIGURE", "NODE_MATH", 25, 9.4, "𝑁=1", "MATH_BASE", (203.57, 412.30, 227.44, 421.67)),
    ("T12", "FIGURE", "NODE_LABEL", 26, 9.4, "Bernoulli分布", "MIXED_CJK_LATIN", (332.36, 400.46, 390.63, 410.14)),
    ("T13", "FIGURE", "NODE_MATH_LINE", 26, 9.4, "𝐾=2,𝑁=1", "MATH_BASE_WITH_COMMA", (335.97, 411.72, 387.01, 421.09)),
    ("T13A", "FIGURE", "NODE_MATH", 26, 9.4, "𝐾=2", "MATH_BASE", (335.97, 411.72, 359.29, 421.09)),
    ("T13B", "FIGURE", "NODE_MATH", 26, 9.4, "𝑁=1", "MATH_BASE", (363.14, 411.72, 387.01, 421.09)),
    ("T14", "FIGURE", "EDGE_LABEL", 30, 8.8, "特殊情形", "CJK_FULL", (270.97, 274.73, 306.04, 283.49)),
    ("T15", "FIGURE", "EDGE_LABEL", 31, 8.8, "特殊情形", "CJK_FULL", (270.97, 335.67, 306.04, 344.44)),
    ("T16", "FIGURE", "EDGE_LABEL", 32, 8.8, "𝑁=1", "MATH_BASE", (221.78, 376.24, 245.94, 385.01)),
    ("T17", "FIGURE", "EDGE_LABEL", 33, 8.8, "𝑁=1", "MATH_BASE", (367.76, 376.24, 391.92, 385.01)),
    ("T18", "FIGURE", "EDGE_LABEL", 34, 8.8, "𝐾=2", "MATH_BASE", (276.61, 397.38, 300.39, 406.15)),
    ("T19", "FIGURE", "LEGEND_LABEL", 36, 8.8, "共轭", "CJK_FULL", (462.43, 313.12, 479.97, 321.89)),
    ("T20", "FIGURE", "LEGEND_LABEL", 38, 8.8, "特殊情形", "CJK_FULL", (462.22, 337.22, 497.29, 345.99)),
    ("T21", "CAPTION", "CAPTION_LABEL", 41, 10.0, "图34.3", "MIXED_CJK_DIGIT", (87.48, 431.76, 117.72, 442.22)),
    ("T22", "CAPTION", "CAPTION_BODY", 41, 10.0, "六个常用分布之间同时存在特殊情形关系和共轭关系：Beta是二维Dirichlet，二项是二维", "MIXED_CJK_LATIN", (127.68, 431.76, 519.13, 442.05)),
    ("T23", "CAPTION", "CAPTION_BODY", 41, 10.0, "多项，类别分布是单次多项，Bernoulli同时是单次二项；粗箭头表示共轭先验而不是集合包含", "MIXED_CJK_LATIN", (87.48, 445.15, 498.17, 455.44)),
]

class_keys = {
    "ROW_HEADING": ["T01", "T05", "T09"],
    "NODE_LABEL": ["T02", "T03", "T06", "T07", "T10", "T12"],
    "NODE_MATH": ["T04", "T08", "T11", "T13A", "T13B"],
    "EDGE_CJK": ["T14", "T15", "T19", "T20"],
    "EDGE_MATH": ["T16", "T17", "T18"],
    "CAPTION_LABEL": ["T21"],
    "CAPTION_BODY": ["T22", "T23"],
}

records = []
text_mask = np.zeros(gray.shape, dtype=bool)
element_masks = {}
for eid, scope, role, source_line, declared_pt, sample, script_class, pdf_box in elements:
    x0, y0, x1, y1 = pxbbox(pdf_box)
    roi = gray[y0:y1, x0:x1]
    bg = float(np.percentile(roi, 90))
    ink = roi <= max(0.0, bg - 20.0)
    active_rows = np.flatnonzero(ink.sum(axis=1) >= 1)
    active_cols = np.flatnonzero(ink.sum(axis=0) >= 1)
    h_ink = int(active_rows[-1] - active_rows[0] + 1) if active_rows.size else 0
    w_ink = int(active_cols[-1] - active_cols[0] + 1) if active_cols.size else 0
    text_mask[y0:y1, x0:x1] |= ink
    element_mask = np.zeros(gray.shape, dtype=bool)
    element_mask[y0:y1, x0:x1] = ink
    element_masks[eid] = element_mask
    records.append({
        "element_id": eid,
        "scope": scope,
        "role": role,
        "source_line": source_line,
        "declared_pt": declared_pt,
        "graphics_scale": 1.0,
        "effective_pt": declared_pt,
        "text_sample": sample,
        "script_class": script_class,
        "pdf_x0": pdf_box[0],
        "pdf_top": pdf_box[1],
        "pdf_x1": pdf_box[2],
        "pdf_bottom": pdf_box[3],
        "bbox_x0": x0,
        "bbox_y0": y0,
        "bbox_x1": x1,
        "bbox_y1": y1,
        "h_ink_px": h_ink,
        "w_ink_px": w_ink,
        "local_background_gray_p90": round(bg, 2),
        "threshold_gray": round(max(0.0, bg - 20.0), 2),
    })

by_id = {r["element_id"]: r for r in records}
for class_name, ids in class_keys.items():
    median = float(np.median([by_id[i]["h_ink_px"] for i in ids]))
    for i in ids:
        by_id[i]["comparison_class"] = class_name
        by_id[i]["class_median_px"] = median
        by_id[i]["ratio_to_class_median"] = round(by_id[i]["h_ink_px"] / median, 4)

base_median = float(np.median([by_id[i]["h_ink_px"] for i in class_keys["NODE_LABEL"]]))
for r in records:
    r["role_ratio_to_node_label_base"] = round(r["h_ink_px"] / base_median, 4)

raw_csv = ROOT / "review" / "pixel_measurements_raw.csv"
with raw_csv.open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)

independent_text_ids = [r["element_id"] for r in records if r["element_id"] != "T13"]
max_text_pair_overlap = 0
with (ROOT / "review" / "text_pair_pixel_overlap_raw.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["element_a", "element_b", "actual_ink_overlap_px"])
    for a, b in itertools.combinations(independent_text_ids, 2):
        count = int((element_masks[a] & element_masks[b]).sum())
        max_text_pair_overlap = max(max_text_pair_overlap, count)
        writer.writerow([a, b, count])

with (ROOT / "review" / "glyph_codepoints_raw.tsv").open("w", encoding="utf-8", newline="") as fh:
    fh.write("element_id\ttext_sample\tunicode_codepoints\n")
    for r in records:
        cps = " ".join(f"U+{ord(ch):04X}" for ch in r["text_sample"])
        fh.write(f"{r['element_id']}\t{r['text_sample']}\t{cps}\n")


# Native-pixel text-box overlay, including caption integration elements.
fx0, fy0, fx1, fy1 = FIGURE_CROP
overlay = page.crop(FIGURE_CROP).copy()
draw = ImageDraw.Draw(overlay)
palette = [(214, 39, 40), (31, 119, 180), (44, 160, 44), (148, 103, 189)]
for idx, r in enumerate(records):
    color = palette[idx % len(palette)]
    box = (r["bbox_x0"] - fx0, r["bbox_y0"] - fy0, r["bbox_x1"] - fx0, r["bbox_y1"] - fy0)
    draw.rectangle(box, outline=color, width=2)
    draw.text((box[0], max(0, box[1] - 11)), r["element_id"], fill=color)
overlay.save(ROOT / "review" / "text_element_bbox_overlay_native300dpi.png")


# Graphics-only foreground mask sampled around exact vector paths from pdfplumber geometry.
graphics_mask = np.zeros(gray.shape, dtype=bool)

def add_graphic_region(pdf_box, threshold=230):
    x0, y0, x1, y1 = pxbbox(pdf_box)
    roi = gray[y0:y1, x0:x1]
    graphics_mask[y0:y1, x0:x1] |= roi <= threshold


# Rounded node borders: narrow bands around each exact vector bounding box.
node_boxes = [
    (172.99, 272.96, 258.03, 302.72), (318.97, 272.96, 404.02, 302.72),
    (172.99, 333.90, 258.03, 363.67), (318.97, 333.90, 404.02, 363.67),
    (172.99, 394.85, 258.03, 424.61), (318.97, 394.85, 404.02, 424.61),
]
for box in node_boxes:
    x0, y0, x1, y1 = pxbbox(box)
    pad = 7
    local = gray[max(0, y0-pad):min(page.height, y1+pad), max(0, x0-pad):min(page.width, x1+pad)] <= 230
    h, w = local.shape
    yy, xx = np.ogrid[:h, :w]
    border_band = (xx < 13) | (xx >= w-13) | (yy < 13) | (yy >= h-13)
    target = graphics_mask[max(0, y0-pad):min(page.height, y1+pad), max(0, x0-pad):min(page.width, x1+pad)]
    target |= local & border_band

# Straight line and arrowhead envelopes, all in PDF top-coordinate space.
graphic_regions = [
    (214.5, 302.7, 216.6, 332.1), (360.4, 302.7, 362.6, 332.1),
    (258.1, 286.2, 317.9, 289.5), (258.1, 347.1, 317.9, 350.5),
    (213.8, 363.7, 217.2, 393.9), (359.8, 363.7, 363.2, 393.9),
    (258.1, 408.1, 317.9, 411.4),
    (420.7, 314.7, 455.2, 317.6), (420.7, 338.6, 455.9, 341.9),
]
for box in graphic_regions:
    add_graphic_region(box)

text_graphic_overlap = text_mask & graphics_mask
text_img = Image.fromarray(np.where(text_mask, 0, 255).astype(np.uint8))
graphic_img = Image.fromarray(np.where(graphics_mask, 0, 255).astype(np.uint8))
overlap_img = np.full((*gray.shape, 3), 255, dtype=np.uint8)
overlap_img[text_mask] = (70, 130, 180)
overlap_img[graphics_mask] = (70, 70, 70)
overlap_img[text_graphic_overlap] = (220, 0, 0)
text_img.crop(FIGURE_CROP).save(ROOT / "masks" / "text_foreground_mask_native300dpi.png")
graphic_img.crop(FIGURE_CROP).save(ROOT / "masks" / "graphics_foreground_mask_native300dpi.png")
Image.fromarray(overlap_img).crop(FIGURE_CROP).save(ROOT / "masks" / "text_graphics_overlap_overlay_native300dpi.png")


# Frozen visible-object denominator: 18 internal semantic objects + 2 caption integration objects.
objects = [
    ("O01", "ROW_HEADING", "先验族", (115.0, 282.0, 149.0, 297.0)),
    ("O02", "NODE", "Dirichlet分布", (172.5, 272.5, 258.5, 303.2)),
    ("O03", "NODE", "Beta分布; K=2", (318.5, 272.5, 404.5, 303.2)),
    ("O04", "ROW_HEADING", "似然族", (115.0, 343.0, 149.0, 358.0)),
    ("O05", "NODE", "多项分布", (172.5, 333.4, 258.5, 364.2)),
    ("O06", "NODE", "二项分布; K=2", (318.5, 333.4, 404.5, 364.2)),
    ("O07", "ROW_HEADING", "单次试验", (110.0, 404.0, 153.5, 419.0)),
    ("O08", "NODE", "类别分布; N=1", (172.5, 394.3, 258.5, 425.1)),
    ("O09", "NODE", "Bernoulli分布; K=2,N=1", (318.5, 394.3, 404.5, 425.1)),
    ("O10", "SPECIAL_RELATION", "Dirichlet→Beta; 特殊情形", (258.0, 273.5, 318.2, 290.0)),
    ("O11", "SPECIAL_RELATION", "多项→二项; 特殊情形", (258.0, 334.5, 318.2, 351.0)),
    ("O12", "SPECIAL_RELATION", "多项→类别; N=1", (213.5, 363.5, 247.0, 394.0)),
    ("O13", "SPECIAL_RELATION", "二项→Bernoulli; N=1", (359.5, 363.5, 393.0, 394.0)),
    ("O14", "SPECIAL_RELATION", "类别→Bernoulli; K=2", (258.0, 396.8, 318.2, 412.0)),
    ("O15", "CONJUGACY_RELATION", "Dirichlet→多项; 共轭", (213.5, 302.3, 217.5, 333.0)),
    ("O16", "CONJUGACY_RELATION", "Beta→二项; 共轭", (359.5, 302.3, 363.5, 333.0)),
    ("O17", "LEGEND_SAMPLE", "粗实线闭箭头=共轭", (420.5, 312.0, 481.0, 323.0)),
    ("O18", "LEGEND_SAMPLE", "细实线开箭头=特殊情形", (420.5, 336.0, 498.5, 347.5)),
    ("O19", "CAPTION_LABEL", "图34.3", (87.48, 431.76, 117.72, 442.22)),
    ("O20", "CAPTION_BODY", "六个常用分布…不是集合包含", (87.48, 431.76, 519.13, 455.44)),
]

with (ROOT / "review" / "visible_object_denominator_raw.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["object_id", "object_type", "visible_content", "pdf_x0", "pdf_top", "pdf_x1", "pdf_bottom"])
    for oid, typ, content, box in objects:
        writer.writerow([oid, typ, content, *box])


def bbox_metrics(a, b):
    ax0, ay0, ax1, ay1 = pxbbox(a)
    bx0, by0, bx1, by1 = pxbbox(b)
    iw = max(0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0, min(ay1, by1) - max(ay0, by0))
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return iw * ih, round(math.hypot(dx, dy), 3)


with (ROOT / "review" / "object_pair_geometry_raw.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["pair_id", "object_a", "object_b", "bbox_intersection_area_px", "bbox_gap_px"])
    for idx, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
        area, gap = bbox_metrics(a[3], b[3])
        writer.writerow([f"P{idx:03d}", a[0], b[0], area, gap])


summary = {
    "page_pixel_size": [page.width, page.height],
    "scale_px_per_pdf_pt": [sx, sy],
    "text_element_count": len(records),
    "visible_object_count": len(objects),
    "unordered_pair_count": math.comb(len(objects), 2),
    "text_graphics_overlap_pixel_count": int(text_graphic_overlap.sum()),
    "maximum_independent_text_pair_overlap_pixel_count": max_text_pair_overlap,
    "node_label_base_median_px": base_median,
}
(ROOT / "review" / "automated_measurement_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
