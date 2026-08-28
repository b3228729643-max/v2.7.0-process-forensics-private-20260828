from __future__ import annotations

import csv
import itertools
import json
import math
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P656-01\sa1_r108_fresh_isolated_replacement_v2")
PAGE_INDEX = 704
SCALE = 300.0 / 72.0


def pdf_rect_to_px(rect):
    x0, y0, x1, y1 = rect
    return tuple(int(round(v * SCALE)) for v in (x0, y0, x1, y1))


def union_rect(rects):
    return (
        min(r[0] for r in rects),
        min(r[1] for r in rects),
        max(r[2] for r in rects),
        max(r[3] for r in rects),
    )


def color_int_to_rgb(value):
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def bbox_distance(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def dominant_background(arr):
    flat = arr.reshape(-1, 3)
    q = (flat // 8) * 8
    key, _ = Counter(map(tuple, q.tolist())).most_common(1)[0]
    return np.array(key, dtype=np.int16) + 4


def text_ink_mask(page_rgb, rect_px, title=False):
    x0, y0, x1, y1 = rect_px
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(page_rgb.shape[1], x1)
    y1 = min(page_rgb.shape[0], y1)
    roi = page_rgb[y0:y1, x0:x1].astype(np.int16)
    bg = dominant_background(roi)
    contrast = np.max(np.abs(roi - bg), axis=2)
    spread = roi.max(axis=2) - roi.min(axis=2)
    if title:
        mask = (contrast >= 20) & (roi[:, :, 2] - roi[:, :, 0] >= 28) & (roi.mean(axis=2) < 210)
    else:
        # Body text is neutral dark gray/black. The strict chroma bound excludes
        # anti-aliased remnants of the teal hatch behind category-2 token labels.
        mask = (contrast >= 20) & (spread <= 18) & (roi.mean(axis=2) < 226)
    full = np.zeros(page_rgb.shape[:2], dtype=bool)
    full[y0:y1, x0:x1] = mask
    return full, tuple(int(v) for v in bg)


def ink_height(mask, rect_px):
    x0, y0, x1, y1 = rect_px
    yy, xx = np.nonzero(mask[y0:y1, x0:x1])
    return 0 if yy.size == 0 else int(yy.max() - yy.min() + 1)


def annulus_mask(shape, rect_px, thickness=4):
    out = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = rect_px
    yy, xx = np.ogrid[y0:y1, x0:x1]
    cx = (x0 + x1 - 1) / 2
    cy = (y0 + y1 - 1) / 2
    rx = (x1 - x0 - 1) / 2
    ry = (y1 - y0 - 1) / 2
    outer = ((xx - cx) / max(rx, 1)) ** 2 + ((yy - cy) / max(ry, 1)) ** 2 <= 1
    inner = ((xx - cx) / max(rx - thickness, 1)) ** 2 + ((yy - cy) / max(ry - thickness, 1)) ** 2 < 1
    out[y0:y1, x0:x1] = outer & ~inner
    return out


def rounded_rect_border_mask(shape, rect_px, thickness=4):
    out = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = rect_px
    out[y0:y0 + thickness, x0:x1] = True
    out[y1 - thickness:y1, x0:x1] = True
    out[y0:y1, x0:x0 + thickness] = True
    out[y0:y1, x1 - thickness:x1] = True
    return out


def line_arrow_mask(shape, shaft_rect_px, head_rect_px, thickness=5):
    out = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = shaft_rect_px
    y = int(round((y0 + y1) / 2))
    out[max(0, y - thickness // 2):min(shape[0], y + thickness // 2 + 1), x0:x1] = True
    hx0, hy0, hx1, hy1 = head_rect_px
    for x in range(hx0, hx1):
        frac = (x - hx0 + 1) / max(hx1 - hx0, 1)
        half = max(1, int(round(frac * (hy1 - hy0) / 2)))
        cy = (hy0 + hy1) // 2
        out[max(0, cy - half):min(shape[0], cy + half + 1), x] = True
    return out


def save_crop(img, name, rect_pdf, grayscale=False):
    crop = img.crop(pdf_rect_to_px(rect_pdf))
    if grayscale:
        crop = crop.convert("L")
    crop.save(ROOT / "render" / name)
    return crop


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
raw = page.get_text("rawdict")
spans = [
    s
    for block in raw["blocks"]
    for line in block.get("lines", [])
    for s in line.get("spans", [])
    if s["bbox"][1] >= 560 and s["bbox"][3] <= 682
]

page_png = ROOT / "render" / "r108_p705_full_300dpi.png"
page_img = Image.open(page_png).convert("RGB")
page_rgb = np.asarray(page_img)

figure_rect = (75.0, 562.0, 505.0, 681.0)
figure_caption_rect = (70.0, 562.0, 515.0, 712.0)
standalone = save_crop(page_img, "r108_p705_standalone_300dpi.png", figure_rect)
save_crop(page_img, "r108_p705_figure_with_caption_300dpi.png", figure_caption_rect)
save_crop(page_img, "r108_p705_grayscale_300dpi.png", figure_rect, grayscale=True)

risk_rects = {
    "roi_text_text_coefficient": (388.0, 594.0, 500.0, 637.5),
    "roi_warning_bottom_clearance": (254.0, 660.0, 379.0, 681.5),
    "roi_arrow1_label_and_countbox": (212.0, 596.0, 261.0, 624.0),
    "roi_arrow2_and_coefficientbox": (372.0, 607.0, 397.0, 626.0),
}
for stem, rect in risk_rects.items():
    roi = page_img.crop(pdf_rect_to_px(rect))
    roi.save(ROOT / "render" / f"{stem}_native300dpi_1x.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "render" / f"{stem}_native300dpi_8x_nearest.png"
    )

# Span and glyph extraction is fully mechanical. Source TeX-point interpretation is adjudicated separately.
span_rows = []
glyph_rows = []
span_index = {id(s): i for i, s in enumerate(spans)}
for i, span in enumerate(spans, 1):
    text = "".join(c["c"] for c in span["chars"])
    span_rows.append(
        {
            "SPAN_ID": f"S{i:02d}",
            "TEXT": text,
            "FONT": span["font"],
            "SIZE_BP": f"{span['size']:.5f}",
            "COLOR_RGB": color_int_to_rgb(span["color"]),
            "BBOX_PDF": tuple(round(v, 3) for v in span["bbox"]),
            "CHAR_COUNT": len(span["chars"]),
        }
    )
    for char_i, char in enumerate(span["chars"], 1):
        c = char["c"]
        if c.isspace():
            continue
        rect_px = pdf_rect_to_px(char["bbox"])
        mask, bg = text_ink_mask(page_rgb, rect_px, title=(i == 1))
        h = ink_height(mask, rect_px)
        glyph_rows.append(
            {
                "GLYPH_ID": f"G{len(glyph_rows)+1:03d}",
                "SPAN_ID": f"S{i:02d}",
                "CHAR_IN_SPAN": char_i,
                "CHAR": c,
                "FONT": span["font"],
                "SIZE_BP": f"{span['size']:.5f}",
                "BBOX_PDF": tuple(round(v, 3) for v in char["bbox"]),
                "BBOX_PX": rect_px,
                "INK_HEIGHT_PX": h,
                "LOCAL_BG_RGB": bg,
            }
        )

with (ROOT / "analysis" / "pdf_font_spans.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=span_rows[0].keys())
    w.writeheader()
    w.writerows(span_rows)
with (ROOT / "analysis" / "glyph_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=glyph_rows[0].keys())
    w.writeheader()
    w.writerows(glyph_rows)

# 25 text objects: one title, 18 token labels, arrow label, three formula/text blocks,
# and the two coefficient blocks. Their bounding boxes come directly from PDF text spans.
text_groups = [
    ("T_TITLE", "TEXT", [0]),
    *[(f"T_TOKEN_R{r}C{c}", "TEXT", [1 + (r - 1) * 6 + (c - 1)]) for r in range(1, 4) for c in range(1, 7)],
    ("T_COUNT_FORMULA", "FORMULA", list(range(19, 27))),
    ("T_ARROW_LABEL", "TEXT", [27]),
    ("T_CONSTRAINT", "FORMULA", list(range(28, 38))),
    ("T_WARNING", "TEXT", [38]),
    ("T_COEF_HEADER", "TEXT", [39]),
    ("T_COEF_FORMULA", "FORMULA", list(range(40, 45))),
]

objects = []
object_masks = {}
for object_id, cls, idxs in text_groups:
    rect = union_rect([spans[i]["bbox"] for i in idxs])
    rect_px = pdf_rect_to_px(rect)
    mask = np.zeros(page_rgb.shape[:2], dtype=bool)
    for idx in idxs:
        for char in spans[idx]["chars"]:
            if char["c"].isspace():
                continue
            cmask, _ = text_ink_mask(page_rgb, pdf_rect_to_px(char["bbox"]), title=(object_id == "T_TITLE"))
            mask |= cmask
    object_masks[object_id] = mask
    objects.append({"OBJECT_ID": object_id, "CLASS": cls, "BBOX_PDF": rect, "BBOX_PX": rect_px})

drawings = page.get_drawings()
circle_draw_indices = [5, 6, 7, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23, 24, 25]
for pos, drawing_idx in enumerate(circle_draw_indices):
    r = pos // 6 + 1
    c = pos % 6 + 1
    object_id = f"G_TOKEN_BODY_R{r}C{c}"
    rect = tuple(drawings[drawing_idx]["rect"])
    rect_px = pdf_rect_to_px(rect)
    object_masks[object_id] = annulus_mask(page_rgb.shape[:2], rect_px, thickness=4)
    objects.append({"OBJECT_ID": object_id, "CLASS": "NODE_BORDER", "BBOX_PDF": rect, "BBOX_PX": rect_px})

box_specs = [
    ("G_COUNT_BOX", 26),
    ("G_WARNING_BOX", 29),
    ("G_COEFFICIENT_BOX", 30),
]
for object_id, drawing_idx in box_specs:
    rect = tuple(drawings[drawing_idx]["rect"])
    rect_px = pdf_rect_to_px(rect)
    object_masks[object_id] = rounded_rect_border_mask(page_rgb.shape[:2], rect_px, thickness=4)
    objects.append({"OBJECT_ID": object_id, "CLASS": "NODE_BORDER", "BBOX_PDF": rect, "BBOX_PX": rect_px})

arrow_specs = [
    ("G_ARROW_SEQUENCES_TO_COUNT", 27, 28),
    ("G_ARROW_COUNT_TO_COEFFICIENT", 31, 32),
]
for object_id, shaft_idx, head_idx in arrow_specs:
    shaft = tuple(drawings[shaft_idx]["rect"])
    head = tuple(drawings[head_idx]["rect"])
    rect = union_rect([shaft, head])
    object_masks[object_id] = line_arrow_mask(
        page_rgb.shape[:2], pdf_rect_to_px(shaft), pdf_rect_to_px(head), thickness=5
    )
    objects.append({"OBJECT_ID": object_id, "CLASS": "LINE_ARROW", "BBOX_PDF": rect, "BBOX_PX": pdf_rect_to_px(rect)})

assert len(objects) == 48, len(objects)
objects.sort(key=lambda x: x["OBJECT_ID"])

with (ROOT / "analysis" / "visible_objects.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = ["OBJECT_ID", "CLASS", "BBOX_PDF", "BBOX_PX", "MASK_PIXEL_COUNT", "INK_HEIGHT_PX"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for obj in objects:
        row = dict(obj)
        row["MASK_PIXEL_COUNT"] = int(object_masks[obj["OBJECT_ID"]].sum())
        row["INK_HEIGHT_PX"] = (
            ink_height(object_masks[obj["OBJECT_ID"]], obj["BBOX_PX"])
            if obj["CLASS"] in ("TEXT", "FORMULA")
            else ""
        )
        w.writerow(row)

pair_rows = []
containment_pairs = {
    *(tuple(sorted((f"G_TOKEN_BODY_R{r}C{c}", f"T_TOKEN_R{r}C{c}"))) for r in range(1, 4) for c in range(1, 7)),
    tuple(sorted(("G_COUNT_BOX", "T_COUNT_FORMULA"))),
    tuple(sorted(("G_WARNING_BOX", "T_WARNING"))),
    tuple(sorted(("G_COEFFICIENT_BOX", "T_COEF_HEADER"))),
    tuple(sorted(("G_COEFFICIENT_BOX", "T_COEF_FORMULA"))),
}
arrow_attachment_pairs = {
    tuple(sorted(("G_ARROW_SEQUENCES_TO_COUNT", "G_COUNT_BOX"))),
    tuple(sorted(("G_ARROW_COUNT_TO_COEFFICIENT", "G_COUNT_BOX"))),
    tuple(sorted(("G_ARROW_COUNT_TO_COEFFICIENT", "G_COEFFICIENT_BOX"))),
}
for a, b in itertools.combinations(objects, 2):
    aid, bid = a["OBJECT_ID"], b["OBJECT_ID"]
    overlap = int(np.logical_and(object_masks[aid], object_masks[bid]).sum())
    key = tuple(sorted((aid, bid)))
    if key in containment_pairs:
        family = "INTENDED_TEXT_IN_NODE_CONTAINMENT"
    elif key in arrow_attachment_pairs:
        family = "INTENDED_ARROW_NODE_ATTACHMENT"
    else:
        family = "POSITIVE_BBOX_SEPARATION"
    pair_rows.append(
        {
            "PAIR_ID": f"P{len(pair_rows)+1:04d}",
            "OBJECT_A": aid,
            "CLASS_A": a["CLASS"],
            "OBJECT_B": bid,
            "CLASS_B": b["CLASS"],
            "GEOMETRY_FAMILY": family,
            "MASK_INTERSECTION_PX": overlap,
            "BBOX_GAP_PX": f"{bbox_distance(a['BBOX_PX'], b['BBOX_PX']):.3f}",
        }
    )
assert len(pair_rows) == 1128, len(pair_rows)
with (ROOT / "analysis" / "all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=pair_rows[0].keys())
    w.writeheader()
    w.writerows(pair_rows)

# Save a tight, independent monochrome mask for every object, plus class composites.
(ROOT / "masks").mkdir(exist_ok=True)
figure_px = pdf_rect_to_px(figure_rect)
fx0, fy0, fx1, fy1 = figure_px
text_composite = np.zeros((fy1 - fy0, fx1 - fx0), dtype=np.uint8)
graphic_composite = np.zeros_like(text_composite)
for obj in objects:
    oid = obj["OBJECT_ID"]
    mask = object_masks[oid]
    x0, y0, x1, y1 = obj["BBOX_PX"]
    pad = 4
    x0p, y0p = max(0, x0 - pad), max(0, y0 - pad)
    x1p, y1p = min(mask.shape[1], x1 + pad), min(mask.shape[0], y1 + pad)
    Image.fromarray((mask[y0p:y1p, x0p:x1p] * 255).astype(np.uint8), mode="L").save(
        ROOT / "masks" / f"{oid}.png"
    )
    local = mask[fy0:fy1, fx0:fx1]
    if obj["CLASS"] in ("TEXT", "FORMULA"):
        text_composite[local] = 255
    else:
        graphic_composite[local] = 255
Image.fromarray(text_composite, mode="L").save(ROOT / "render" / "independent_text_masks_300dpi.png")
Image.fromarray(graphic_composite, mode="L").save(ROOT / "render" / "independent_graphic_masks_300dpi.png")
mask_rgb = np.full((text_composite.shape[0], text_composite.shape[1], 3), 255, dtype=np.uint8)
mask_rgb[graphic_composite > 0] = (30, 90, 210)
mask_rgb[text_composite > 0] = (215, 35, 65)
Image.fromarray(mask_rgb, mode="RGB").save(ROOT / "render" / "independent_mask_composite_300dpi.png")

# Exact mechanical clearances for the protocol's required relation classes.
obj_by_id = {o["OBJECT_ID"]: o for o in objects}
clearance_rows = []
for aid, bid in sorted(containment_pairs):
    text_id = aid if obj_by_id[aid]["CLASS"] in ("TEXT", "FORMULA") else bid
    border_id = bid if text_id == aid else aid
    dist = distance_transform_edt(~object_masks[border_id])
    values = dist[object_masks[text_id]]
    clearance_rows.append(
        {
            "RELATION": "NODE_INTERNAL_TEXT_TO_BORDER",
            "OBJECT_A": text_id,
            "OBJECT_B": border_id,
            "CLEARANCE_PX": f"{float(values.min()):.3f}",
            "MEASURE": "independent_mask_euclidean",
        }
    )
text_objects = [o for o in objects if o["CLASS"] in ("TEXT", "FORMULA")]
for a, b in itertools.combinations(text_objects, 2):
    clearance_rows.append(
        {
            "RELATION": "TEXT_TEXT_BBOX",
            "OBJECT_A": a["OBJECT_ID"],
            "OBJECT_B": b["OBJECT_ID"],
            "CLEARANCE_PX": f"{bbox_distance(a['BBOX_PX'], b['BBOX_PX']):.3f}",
            "MEASURE": "pdf_bbox_mapped_to_native300dpi",
        }
    )
arrow_objects = [o for o in objects if o["CLASS"] == "LINE_ARROW"]
for text_obj in text_objects:
    for arrow_obj in arrow_objects:
        dist = distance_transform_edt(~object_masks[arrow_obj["OBJECT_ID"]])
        values = dist[object_masks[text_obj["OBJECT_ID"]]]
        clearance_rows.append(
            {
                "RELATION": "TEXT_FORMULA_TO_LINE_ARROW",
                "OBJECT_A": text_obj["OBJECT_ID"],
                "OBJECT_B": arrow_obj["OBJECT_ID"],
                "CLEARANCE_PX": f"{float(values.min()):.3f}",
                "MEASURE": "independent_mask_euclidean",
            }
        )
for text_obj in text_objects:
    x0, y0, x1, y1 = text_obj["BBOX_PX"]
    edge_clearance = min(x0 - fx0, y0 - fy0, fx1 - x1, fy1 - y1)
    clearance_rows.append(
        {
            "RELATION": "TEXT_TO_FIGURE_CROP_EDGE",
            "OBJECT_A": text_obj["OBJECT_ID"],
            "OBJECT_B": "FIGURE_CROP_EDGE",
            "CLEARANCE_PX": f"{float(edge_clearance):.3f}",
            "MEASURE": "pdf_bbox_mapped_to_native300dpi",
        }
    )
with (ROOT / "analysis" / "clearance_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=clearance_rows[0].keys())
    w.writeheader()
    w.writerows(clearance_rows)

# Measurement overlay for traceability. Every object gets its own labeled PDF-derived box.
overlay = page_img.crop(pdf_rect_to_px(figure_rect)).copy()
draw = ImageDraw.Draw(overlay)
ox0, oy0, _, _ = pdf_rect_to_px(figure_rect)
for obj in objects:
    x0, y0, x1, y1 = obj["BBOX_PX"]
    x0 -= ox0
    x1 -= ox0
    y0 -= oy0
    y1 -= oy0
    color = (210, 40, 60) if obj["CLASS"] in ("TEXT", "FORMULA") else (40, 100, 210)
    draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
    draw.text((x0 + 2, max(0, y0 - 12)), obj["OBJECT_ID"], fill=color)
overlay.save(ROOT / "render" / "r108_p705_object_overlay_300dpi.png")

nonvisible_artifacts = []
for idx in (8, 15, 21):
    d = drawings[idx]
    nonvisible_artifacts.append(
        {
            "DRAWING_INDEX": idx,
            "SEQNO": d.get("seqno"),
            "EXTRACTED_RECT": tuple(d["rect"]),
            "TYPE": d.get("type"),
            "ITEM_COUNT": len(d.get("items", [])),
        }
    )
with (ROOT / "analysis" / "nonvisible_pdf_artifacts.json").open("w", encoding="utf-8") as f:
    json.dump(nonvisible_artifacts, f, ensure_ascii=False, indent=2)

summary = {
    "page_physical": 705,
    "page_printed": 692,
    "page_size_bp": [page.rect.width, page.rect.height],
    "render_scale_px_per_bp": SCALE,
    "visible_object_denominator": len(objects),
    "text_object_count": sum(o["CLASS"] in ("TEXT", "FORMULA") for o in objects),
    "graphic_object_count": sum(o["CLASS"] not in ("TEXT", "FORMULA") for o in objects),
    "unordered_pair_denominator": len(pair_rows),
    "extracted_char_count_including_spaces": sum(len(s["chars"]) for s in spans),
    "visible_glyph_denominator_excluding_spaces": len(glyph_rows),
    "mechanical_mask_intersection_total_px": sum(int(r["MASK_INTERSECTION_PX"]) for r in pair_rows),
    "mechanical_mask_pairs_with_intersection": sum(int(r["MASK_INTERSECTION_PX"]) > 0 for r in pair_rows),
    "pair_geometry_families": dict(Counter(r["GEOMETRY_FAMILY"] for r in pair_rows)),
    "glyph_ink_height_min_px": min(r["INK_HEIGHT_PX"] for r in glyph_rows),
    "glyph_ink_height_max_px": max(r["INK_HEIGHT_PX"] for r in glyph_rows),
    "text_object_ink_height_min_px": min(
        ink_height(object_masks[o["OBJECT_ID"]], o["BBOX_PX"])
        for o in objects
        if o["CLASS"] in ("TEXT", "FORMULA")
    ),
    "text_object_ink_height_max_px": max(
        ink_height(object_masks[o["OBJECT_ID"]], o["BBOX_PX"])
        for o in objects
        if o["CLASS"] in ("TEXT", "FORMULA")
    ),
    "clearance_min_by_relation_px": {
        relation: min(float(r["CLEARANCE_PX"]) for r in clearance_rows if r["RELATION"] == relation)
        for relation in sorted({r["RELATION"] for r in clearance_rows})
    },
    "object_mask_pixels_outside_figure_crop": int(
        sum(
            mask.sum()
            - mask[fy0:fy1, fx0:fx1].sum()
            for mask in object_masks.values()
        )
    ),
    "objects_bbox_intersect_page_boundary": sum(
        int(
            o["BBOX_PX"][0] <= 0
            or o["BBOX_PX"][1] <= 0
            or o["BBOX_PX"][2] >= page_rgb.shape[1]
            or o["BBOX_PX"][3] >= page_rgb.shape[0]
        )
        for o in objects
    ),
    "nonvisible_pdf_artifact_count": len(nonvisible_artifacts),
    "risk_rois": risk_rects,
}
with (ROOT / "analysis" / "mechanical_summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
