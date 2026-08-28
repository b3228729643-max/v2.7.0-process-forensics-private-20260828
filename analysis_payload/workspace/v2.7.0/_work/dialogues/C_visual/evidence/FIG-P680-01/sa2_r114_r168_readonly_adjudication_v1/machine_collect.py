from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa2_r114_r168_readonly_adjudication_v1")
PAGE_INDEX = 728
PAGE_PHYSICAL = 729
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
FIG_RECT = fitz.Rect(62.0, 134.0, 522.0, 302.5)
FIGCAP_RECT = fitz.Rect(62.0, 134.0, 522.0, 336.0)


TEXT_SPECS = [
    ("T01", "shared_heading", (238, 145, 393, 158), "node_text", 16, "9.4"),
    ("T02", "shared_subtitle", (247, 157, 384, 170), "node_text", 16, "9.4"),
    ("T03", "row_model", (104, 190, 150, 211), "row_label", 17, "9.8"),
    ("T04", "full_bayes", (188, 189, 267, 203), "node_text", 18, "9.4"),
    ("T05", "full_random", (188, 202, 267, 215), "math_node_text", 18, "9.4"),
    ("T06", "point_variant", (365, 189, 442, 203), "node_text", 19, "9.4"),
    ("T07", "point_parameter", (368, 202, 439, 215), "math_node_text", 19, "9.4"),
    ("T08", "row_inference", (104, 235, 150, 256), "row_label", 20, "9.8"),
    ("T09", "collapsed_gibbs", (194, 235, 260, 249), "node_text", 21, "9.4"),
    ("T10", "integrate_theta_phi", (197, 247, 258, 261), "math_node_text", 21, "9.4"),
    ("T11", "mean_field_vem", (368, 235, 440, 249), "node_text", 22, "9.4"),
    ("T12", "elbo_ascent", (368, 247, 439, 261), "node_text", 22, "9.4"),
    ("T13", "posterior_warning", (216, 282, 415, 297), "warning_text", 29, "9.2"),
    ("T14", "caption_label", (73, 302, 108, 320), "caption_label", 32, "not_explicit"),
    ("T15", "caption_body", (112, 304, 512, 334), "caption_body", 32, "not_explicit"),
]

GRAPHIC_SPECS = [
    ("G01", "shared_container", (232.326, 139.645, 399.174, 173.661), "node_container", (3,)),
    ("G02", "full_container", (162.677, 185.000, 293.072, 219.016), "node_container", (4,)),
    ("G03", "point_container", (338.428, 185.000, 468.823, 219.016), "node_container", (5,)),
    ("G04", "gibbs_container", (162.677, 230.354, 293.072, 264.370), "node_container", (6,)),
    ("G05", "vem_container", (338.428, 230.354, 468.823, 264.370), "node_container", (7,)),
    ("G06", "arrow_shared_full", (229.152, 172.566, 295.907, 184.135), "line_arrow", (8, 9)),
    ("G07", "arrow_shared_point", (335.593, 172.566, 402.348, 184.135), "line_arrow", (10, 11)),
    ("G08", "arrow_full_gibbs", (226.782, 219.394, 228.968, 228.823), "line_arrow", (12, 13)),
    ("G09", "arrow_point_vem", (402.532, 219.394, 404.718, 228.823), "line_arrow", (14, 15)),
    ("G10", "warning_container", (151.338, 275.709, 480.162, 301.221), "node_container", (16,)),
]

ROIS = [
    ("ROI01_shared_left_branch", (218, 165, 307, 190)),
    ("ROI02_shared_right_branch", (325, 165, 414, 190)),
    ("ROI03_left_route", (156, 179, 300, 269)),
    ("ROI04_right_route", (332, 179, 475, 269)),
    ("ROI05_warning", (145, 271, 486, 304)),
    ("ROI06_caption", (70, 301, 515, 336)),
]


def rect_union(rects):
    xs0 = [r[0] for r in rects]
    ys0 = [r[1] for r in rects]
    xs1 = [r[2] for r in rects]
    ys1 = [r[3] for r in rects]
    return (min(xs0), min(ys0), max(xs1), max(ys1))


def in_window(bbox, window):
    cx = (bbox[0] + bbox[2]) / 2.0
    cy = (bbox[1] + bbox[3]) / 2.0
    return window[0] <= cx <= window[2] and window[1] <= cy <= window[3]


def pdf_to_px(rect):
    return tuple(int(round(v * SCALE_300)) for v in rect)


def local_ink_height(rgb, bbox_px):
    x0, y0, x1, y1 = bbox_px
    pad = 3
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(rgb.shape[1], x1 + pad)
    y1 = min(rgb.shape[0], y1 + pad)
    tile = rgb[y0:y1, x0:x1].astype(np.int16)
    if tile.size == 0:
        return 0, [0, 0, 0], 0
    edge = np.concatenate((tile[0], tile[-1], tile[:, 0], tile[:, -1]), axis=0)
    bg = np.median(edge, axis=0)
    delta = np.max(np.abs(tile - bg), axis=2)
    mask = delta >= 20
    row_counts = mask.sum(axis=1)
    cols = mask.sum(axis=0)
    valid_rows = np.where(row_counts >= 2)[0]
    valid_cols = np.where(cols >= 1)[0]
    if len(valid_rows) == 0 or len(valid_cols) == 0:
        return 0, [int(x) for x in bg], int(mask.sum())
    return int(valid_rows[-1] - valid_rows[0] + 1), [int(x) for x in bg], int(mask.sum())


def bbox_metrics(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = ix * iy
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    distance = math.hypot(dx, dy)
    contains_ab = a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3]
    contains_ba = b[0] <= a[0] and b[1] <= a[1] and b[2] >= a[2] and b[3] >= a[3]
    relation = "a_contains_b" if contains_ab else "b_contains_a" if contains_ba else "none"
    return intersection, distance, relation


def draw_label(draw, xy, label, color):
    x, y = xy
    draw.rectangle((x, y, x + 49, y + 16), fill=(255, 255, 255), outline=color, width=1)
    draw.text((x + 2, y + 1), label, fill=color)


def main():
    (OUT / "views").mkdir(exist_ok=False)
    (OUT / "overlays").mkdir(exist_ok=False)
    (OUT / "rois").mkdir(exist_ok=False)
    (OUT / "machine").mkdir(exist_ok=False)

    doc = fitz.open(PDF)
    if doc.page_count != 817:
        raise RuntimeError(f"unexpected page count: {doc.page_count}")
    page = doc[PAGE_INDEX]
    text = page.get_text("text")
    if "模型与后验不同" not in text or "图35.1" not in text.replace(" ", ""):
        raise RuntimeError("target caption anchors absent on physical page 729")

    pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE_200, SCALE_200), alpha=False)
    pix200.save(OUT / "views" / "full_page_200dpi.png")
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False)
    pix300.save(OUT / "views" / "native_page_300dpi.png")
    page300 = Image.open(OUT / "views" / "native_page_300dpi.png").convert("RGB")
    page_rgb = np.asarray(page300)

    fig_box = pdf_to_px(FIG_RECT)
    figcap_box = pdf_to_px(FIGCAP_RECT)
    fig = page300.crop(fig_box)
    figcap = page300.crop(figcap_box)
    fig.save(OUT / "views" / "figure_only_300dpi.png")
    figcap.save(OUT / "views" / "figure_caption_300dpi.png")
    figcap.convert("L").save(OUT / "views" / "figure_caption_grayscale_300dpi.png")

    raw = page.get_text("rawdict")
    chars = []
    spans = []
    span_seq = 0
    char_seq = 0
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_seq += 1
                span_chars = span.get("chars", [])
                span_text = "".join(ch["c"] for ch in span_chars)
                spans.append({
                    "span_seq": span_seq,
                    "text": span_text,
                    "bbox": [round(v, 6) for v in span["bbox"]],
                    "size_pt": round(span["size"], 6),
                    "font": span["font"],
                })
                for ch in span_chars:
                    char_seq += 1
                    chars.append({
                        "char_seq": char_seq,
                        "char": ch["c"],
                        "codepoint": f"U+{ord(ch['c']):04X}",
                        "bbox": tuple(ch["bbox"]),
                        "size_pt": float(span["size"]),
                        "font": span["font"],
                        "span_seq": span_seq,
                    })

    object_rows = []
    glyph_rows = []
    object_bboxes = {}
    for oid, name, window, role, source_line, declared_pt in TEXT_SPECS:
        selected = [ch for ch in chars if in_window(ch["bbox"], window)]
        if not selected:
            raise RuntimeError(f"no characters collected for {oid}")
        selected.sort(key=lambda ch: (round(ch["bbox"][1], 1), ch["bbox"][0]))
        bbox = rect_union([ch["bbox"] for ch in selected])
        object_bboxes[oid] = bbox
        height, bg, ink_pixels = local_ink_height(page_rgb, pdf_to_px(bbox))
        font_sizes = [ch["size_pt"] for ch in selected]
        text_sample = "".join(ch["char"] for ch in selected)
        object_rows.append({
            "object_id": oid,
            "object_name": name,
            "object_type": "text",
            "semantic_role": role,
            "source_line": source_line,
            "declared_pt": declared_pt,
            "graphics_scale": "1.0",
            "pdf_span_pt_min": f"{min(font_sizes):.6f}",
            "pdf_span_pt_max": f"{max(font_sizes):.6f}",
            "text_sample": text_sample,
            "bbox_pdf": json.dumps([round(v, 6) for v in bbox]),
            "bbox_300px": json.dumps(pdf_to_px(bbox)),
            "group_ink_height_px": height,
            "local_background_rgb": json.dumps(bg),
            "thresholded_foreground_px": ink_pixels,
        })
        for ch in selected:
            ch_height, ch_bg, ch_ink = local_ink_height(page_rgb, pdf_to_px(ch["bbox"]))
            glyph_rows.append({
                "object_id": oid,
                "char_seq": ch["char_seq"],
                "char": ch["char"],
                "codepoint": ch["codepoint"],
                "font": ch["font"],
                "size_pt": f"{ch['size_pt']:.6f}",
                "bbox_pdf": json.dumps([round(v, 6) for v in ch["bbox"]]),
                "bbox_300px": json.dumps(pdf_to_px(ch["bbox"])),
                "ink_height_px": ch_height,
                "local_background_rgb": json.dumps(ch_bg),
                "thresholded_foreground_px": ch_ink,
            })

    for oid, name, bbox, role, drawing_indexes in GRAPHIC_SPECS:
        object_bboxes[oid] = bbox
        object_rows.append({
            "object_id": oid,
            "object_name": name,
            "object_type": "graphic",
            "semantic_role": role,
            "source_line": "23-29" if role == "line_arrow" else "10-14,16-22,29",
            "declared_pt": "not_applicable",
            "graphics_scale": "1.0",
            "pdf_span_pt_min": "not_applicable",
            "pdf_span_pt_max": "not_applicable",
            "text_sample": "",
            "bbox_pdf": json.dumps([round(v, 6) for v in bbox]),
            "bbox_300px": json.dumps(pdf_to_px(bbox)),
            "group_ink_height_px": "not_applicable",
            "local_background_rgb": "not_applicable",
            "thresholded_foreground_px": "not_applicable",
            "drawing_indexes": json.dumps(drawing_indexes),
        })

    pair_rows = []
    ids = [row["object_id"] for row in object_rows]
    for pair_seq, (a_id, b_id) in enumerate(itertools.combinations(ids, 2), start=1):
        a = object_bboxes[a_id]
        b = object_bboxes[b_id]
        intersection, distance, containment = bbox_metrics(a, b)
        pair_rows.append({
            "pair_seq": pair_seq,
            "object_a": a_id,
            "object_b": b_id,
            "bbox_intersection_pdf_pt2": f"{intersection:.6f}",
            "bbox_intersection_300px2": f"{intersection * SCALE_300 * SCALE_300:.6f}",
            "bbox_edge_distance_pdf_pt": f"{distance:.6f}",
            "bbox_edge_distance_300px": f"{distance * SCALE_300:.6f}",
            "containment_relation": containment,
        })

    with (OUT / "machine" / "object_geometry.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = sorted({key for row in object_rows for key in row})
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(object_rows)
    with (OUT / "machine" / "glyph_observations.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(glyph_rows[0]))
        w.writeheader()
        w.writerows(glyph_rows)
    with (OUT / "machine" / "all_unordered_pairs_geometry.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pair_rows[0]))
        w.writeheader()
        w.writerows(pair_rows)

    drawings = page.get_drawings()
    drawing_rows = []
    for idx, drawing in enumerate(drawings):
        rect = drawing["rect"]
        if rect.intersects(FIG_RECT):
            drawing_rows.append({
                "drawing_index": idx,
                "rect_pdf": [round(v, 6) for v in rect],
                "drawing_type": drawing.get("type"),
                "stroke_rgb": drawing.get("color"),
                "fill_rgb": drawing.get("fill"),
                "line_width_pt": drawing.get("width"),
            })
    machine_summary = {
        "physical_page": PAGE_PHYSICAL,
        "page_index_zero_based": PAGE_INDEX,
        "printed_page_text": "716",
        "figure_number_text": "35.1",
        "page_points": [page.rect.width, page.rect.height],
        "render_scale_300": SCALE_300,
        "render_scale_200": SCALE_200,
        "figure_rect_pdf": list(FIG_RECT),
        "figure_caption_rect_pdf": list(FIGCAP_RECT),
        "reader_visible_object_count": len(object_rows),
        "text_object_count": len(TEXT_SPECS),
        "graphic_object_count": len(GRAPHIC_SPECS),
        "unordered_pair_count": len(pair_rows),
        "expected_unordered_pair_count": len(object_rows) * (len(object_rows) - 1) // 2,
        "target_page_anchor_occurrences": {
            "模型与后验不同": text.count("模型与后验不同"),
            "图35.1": text.replace(" ", "").count("图35.1"),
        },
        "figure_drawings": drawing_rows,
    }
    (OUT / "machine" / "machine_summary.json").write_text(
        json.dumps(machine_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "machine" / "target_page_text.txt").write_text(text, encoding="utf-8")

    overlay = page300.crop(figcap_box).copy()
    odraw = ImageDraw.Draw(overlay)
    colors = {"text": (8, 88, 180), "graphic": (196, 42, 42)}
    for row in object_rows:
        bbox = json.loads(row["bbox_pdf"])
        pb = pdf_to_px(bbox)
        local = (pb[0] - figcap_box[0], pb[1] - figcap_box[1], pb[2] - figcap_box[0], pb[3] - figcap_box[1])
        color = colors[row["object_type"]]
        odraw.rectangle(local, outline=color, width=2)
        draw_label(odraw, (local[0], max(0, local[1] - 16)), row["object_id"], color)
    overlay.save(OUT / "overlays" / "object_overlay_300dpi.png")

    semantic = page300.crop(figcap_box).copy()
    sdraw = ImageDraw.Draw(semantic)
    for oid, name, bbox, role, _ in GRAPHIC_SPECS:
        pb = pdf_to_px(bbox)
        local = (pb[0] - figcap_box[0], pb[1] - figcap_box[1], pb[2] - figcap_box[0], pb[3] - figcap_box[1])
        color = (0, 116, 90) if role == "node_container" else (196, 108, 0)
        sdraw.rectangle(local, outline=color, width=3)
        draw_label(sdraw, (local[0], max(0, local[1] - 16)), oid, color)
    semantic.save(OUT / "overlays" / "semantic_overlay_300dpi.png")

    for roi_name, roi_pdf in ROIS:
        roi_px = pdf_to_px(roi_pdf)
        roi = page300.crop(roi_px)
        roi.save(OUT / "rois" / f"{roi_name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), resample=Image.Resampling.NEAREST).save(
            OUT / "rois" / f"{roi_name}_nearest8x.png"
        )


if __name__ == "__main__":
    main()
