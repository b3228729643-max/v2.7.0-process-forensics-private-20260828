from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import statistics
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa3_r111_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_distribution_relations.tex")
PAGE_INDEX_ZERO = 705
PAGE_NUMBER_ONE = 706
FULL_300 = ROOT / "full_page_300dpi.png"

FIG_RECT_PT = (82.0, 267.0, 523.0, 460.0)
PAGE_INTEGRATION_RECT_PT = (73.0, 242.0, 523.0, 510.0)


OBJECTS = [
    ("O01", "ROW_LABEL_PRIOR", "先验族", (110.0, 281.0, 153.0, 297.0)),
    ("O02", "DISTRIBUTION_NODE", "Dirichlet分布", (172.99, 272.96, 258.03, 302.72)),
    ("O03", "DISTRIBUTION_NODE", "Beta分布; K=2", (318.97, 272.96, 404.02, 302.72)),
    ("O04", "ROW_LABEL_LIKELIHOOD", "似然族", (110.0, 342.0, 153.0, 358.0)),
    ("O05", "DISTRIBUTION_NODE", "多项分布", (172.99, 333.90, 258.03, 363.67)),
    ("O06", "DISTRIBUTION_NODE", "二项分布; K=2", (318.97, 333.90, 404.02, 363.67)),
    ("O07", "ROW_LABEL_SINGLE_TRIAL", "单次试验", (106.0, 403.0, 157.0, 420.0)),
    ("O08", "DISTRIBUTION_NODE", "类别分布; N=1", (172.99, 394.85, 258.03, 424.61)),
    ("O09", "DISTRIBUTION_NODE", "Bernoulli分布; K=2,N=1", (318.97, 394.85, 404.02, 424.61)),
    ("O10", "CONJUGACY_RELATION", "Dirichlet→多项", (210.0, 302.0, 221.0, 333.0)),
    ("O11", "CONJUGACY_RELATION", "Beta→二项", (356.0, 302.0, 367.0, 333.0)),
    ("O12", "SPECIAL_CASE_RELATION", "Dirichlet→Beta; 特殊情形", (258.0, 272.0, 318.0, 291.0)),
    ("O13", "SPECIAL_CASE_RELATION", "多项→二项; 特殊情形", (258.0, 333.0, 318.0, 352.0)),
    ("O14", "SPECIAL_CASE_RELATION", "多项→类别; N=1", (210.0, 363.0, 247.0, 395.0)),
    ("O15", "SPECIAL_CASE_RELATION", "二项→Bernoulli; N=1", (356.0, 363.0, 394.0, 395.0)),
    ("O16", "SPECIAL_CASE_RELATION", "类别→Bernoulli; K=2", (258.0, 395.0, 318.0, 413.0)),
    ("O17", "LEGEND_SAMPLE", "共轭粗实心箭头", (419.0, 309.0, 482.0, 324.0)),
    ("O18", "LEGEND_SAMPLE", "特殊情形细空心箭头", (419.0, 334.0, 501.0, 348.0)),
    ("O19", "CAPTION", "图34.3题注（两行）", (86.0, 430.0, 521.0, 457.0)),
]


TEXTS = [
    ("T01", "GROUP_HEADING", "CJK_FULL", "先验族", 18, 9.5, (117.69, 284.70, 146.08, 294.16)),
    ("T02", "NODE_MAIN", "MIXED_CJK_LATIN", "Dirichlet分布", 19, 9.4, (187.35, 284.26, 243.67, 293.93)),
    ("T03", "NODE_MAIN", "MIXED_CJK_LATIN", "Beta分布", 20, 9.4, (342.17, 279.19, 380.82, 288.87)),
    ("T04", "NODE_MATH", "MATH_BASE", "K=2", 20, 9.4, (349.83, 290.45, 373.15, 299.82)),
    ("T05", "GROUP_HEADING", "CJK_FULL", "似然族", 21, 9.5, (117.69, 345.64, 146.08, 355.11)),
    ("T06", "NODE_MAIN", "CJK_FULL", "多项分布", 22, 9.4, (196.78, 345.52, 234.24, 354.88)),
    ("T07", "NODE_MAIN", "CJK_FULL", "二项分布", 23, 9.4, (342.76, 340.45, 380.22, 349.81)),
    ("T08", "NODE_MATH", "MATH_BASE", "K=2", 23, 9.4, (349.83, 351.40, 373.15, 360.76)),
    ("T09", "GROUP_HEADING", "CJK_FULL", "单次试验", 24, 9.5, (112.96, 406.59, 150.82, 416.05)),
    ("T10", "NODE_MAIN", "CJK_FULL", "类别分布", 25, 9.4, (196.78, 401.36, 234.24, 410.72)),
    ("T11", "NODE_MATH", "MATH_BASE", "N=1", 25, 9.4, (203.57, 412.30, 227.44, 421.67)),
    ("T12", "NODE_MAIN", "MIXED_CJK_LATIN", "Bernoulli分布", 26, 9.4, (332.36, 400.46, 390.63, 410.14)),
    ("T13", "NODE_MATH", "MATH_BASE", "K=2,N=1", 26, 9.4, (335.97, 411.72, 387.01, 421.09)),
    ("T14", "EDGE_LABEL", "CJK_FULL", "特殊情形", 30, 8.8, (270.97, 274.73, 306.04, 283.49)),
    ("T15", "EDGE_LABEL", "CJK_FULL", "特殊情形", 31, 8.8, (270.97, 335.67, 306.04, 344.44)),
    ("T16", "EDGE_LABEL", "MATH_BASE", "N=1", 32, 8.8, (221.78, 376.24, 245.94, 385.01)),
    ("T17", "EDGE_LABEL", "MATH_BASE", "N=1", 33, 8.8, (367.76, 376.24, 391.92, 385.01)),
    ("T18", "EDGE_LABEL", "MATH_BASE", "K=2", 34, 8.8, (276.61, 397.38, 300.39, 406.15)),
    ("T19", "LEGEND_LABEL", "CJK_FULL", "共轭", 36, 8.8, (462.43, 313.12, 479.97, 321.89)),
    ("T20", "LEGEND_LABEL", "CJK_FULL", "特殊情形", 38, 8.8, (462.22, 337.22, 497.29, 345.99)),
    ("T21", "CAPTION_LINE", "MIXED_CJK_LATIN", "图34.3题注第一行", 41, 10.0, (87.48, 431.76, 519.13, 442.22)),
    ("T22", "CAPTION_LINE", "MIXED_CJK_LATIN", "图34.3题注第二行", 41, 10.0, (87.48, 445.15, 498.17, 455.44)),
]


ROIS = [
    ("R01", "top_special_relation", (250.0, 268.0, 324.0, 306.0)),
    ("R02", "conjugacy_arrows", (200.0, 297.0, 375.0, 336.0)),
    ("R03", "middle_special_relation", (250.0, 329.0, 324.0, 368.0)),
    ("R04", "bottom_relations", (199.0, 358.0, 400.0, 426.0)),
    ("R05", "legend_semantics", (414.0, 305.0, 505.0, 351.0)),
    ("R06", "caption_glyphs", (82.0, 427.0, 523.0, 459.0)),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def pdf_to_px(rect, sx, sy):
    x0, y0, x1, y1 = rect
    return (
        int(round(x0 * sx)),
        int(round(y0 * sy)),
        int(round(x1 * sx)),
        int(round(y1 * sy)),
    )


def rect_to_local_px(rect, crop_rect, sx, sy):
    x0, y0, x1, y1 = rect
    cx0, cy0, _, _ = crop_rect
    return (
        int(round((x0 - cx0) * sx)),
        int(round((y0 - cy0) * sy)),
        int(round((x1 - cx0) * sx)),
        int(round((y1 - cy0) * sy)),
    )


def draw_label(draw, xy, label, color):
    font = ImageFont.load_default()
    x, y = xy
    box = draw.textbbox((x, y), label, font=font)
    draw.rectangle((box[0] - 2, box[1] - 1, box[2] + 2, box[3] + 1), fill=(255, 255, 255, 235))
    draw.text((x, y), label, fill=color, font=font)


def estimate_ink_height(image, rect_px):
    x0, y0, x1, y1 = rect_px
    x0 = max(0, x0 - 2)
    y0 = max(0, y0 - 2)
    x1 = min(image.width, x1 + 2)
    y1 = min(image.height, y1 + 2)
    arr = np.asarray(image.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.int16)
    if arr.size == 0:
        return 0, (x0, y0, x1, y1)
    flat = arr.reshape(-1, 3)
    luminance = flat.mean(axis=1)
    light = flat[luminance >= np.percentile(luminance, 65)]
    if len(light) == 0:
        light = flat
    bg = np.median(light, axis=0)
    delta = np.max(np.abs(arr - bg), axis=2)
    gray = arr.mean(axis=2)
    mask = (delta >= 20) & (gray < 235)
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return 0, (x0, y0, x1, y1)
    return int(ys.max() - ys.min() + 1), (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)


def bbox_gap_px(a, b, sx, sy):
    dx_pt = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy_pt = max(a[1] - b[3], b[1] - a[3], 0.0)
    dx = dx_pt * sx
    dy = dy_pt * sy
    return dx, dy, math.hypot(dx, dy)


def main():
    if not ROOT.is_dir():
        raise RuntimeError("mandated evidence root missing")
    if not FULL_300.is_file():
        raise RuntimeError("official 300 dpi page render missing")

    full = Image.open(FULL_300).convert("RGB")
    with pdfplumber.open(PDF) as doc:
        page = doc.pages[PAGE_INDEX_ZERO]
        page_w = float(page.width)
        page_h = float(page.height)
        page_objects = page.objects
        page_chars = list(page.chars)

    sx = full.width / page_w
    sy = full.height / page_h

    fig_px = pdf_to_px(FIG_RECT_PT, sx, sy)
    fig = full.crop(fig_px)
    fig.save(ROOT / "local_figure_native300dpi.png")
    fig.convert("L").save(ROOT / "local_figure_grayscale_300dpi.png")
    integration = full.crop(pdf_to_px(PAGE_INTEGRATION_RECT_PT, sx, sy))
    integration.save(ROOT / "page_integration_300dpi.png")

    object_overlay = fig.convert("RGBA")
    object_draw = ImageDraw.Draw(object_overlay, "RGBA")
    object_colors = {
        "DISTRIBUTION_NODE": (0, 122, 204, 255),
        "SPECIAL_CASE_RELATION": (224, 87, 0, 255),
        "CONJUGACY_RELATION": (122, 0, 204, 255),
        "LEGEND_SAMPLE": (0, 145, 88, 255),
        "CAPTION": (200, 0, 90, 255),
    }
    for oid, kind, label, rect in OBJECTS:
        box = rect_to_local_px(rect, FIG_RECT_PT, sx, sy)
        color = object_colors.get(kind, (0, 95, 170, 255))
        object_draw.rectangle(box, outline=color, width=3)
        draw_label(object_draw, (box[0] + 2, box[1] + 2), oid, color)
    object_overlay.convert("RGB").save(ROOT / "object_denominator_overlay_300dpi.png")

    measurements = []
    text_overlay = fig.convert("RGBA")
    text_draw = ImageDraw.Draw(text_overlay, "RGBA")
    text_mask = Image.new("L", fig.size, 0)
    text_mask_arr = np.zeros((fig.height, fig.width), dtype=np.uint8)
    fig_arr = np.asarray(fig, dtype=np.int16)

    for tid, role, script_class, sample, source_line, declared_pt, rect in TEXTS:
        local_box = rect_to_local_px(rect, FIG_RECT_PT, sx, sy)
        h_ink, ink_box = estimate_ink_height(fig, local_box)
        x0, y0, x1, y1 = local_box
        sub = fig_arr[max(0, y0 - 2):min(fig.height, y1 + 2), max(0, x0 - 2):min(fig.width, x1 + 2)]
        if sub.size:
            flat = sub.reshape(-1, 3)
            lum = flat.mean(axis=1)
            light = flat[lum >= np.percentile(lum, 65)]
            bg = np.median(light if len(light) else flat, axis=0)
            delta = np.max(np.abs(sub - bg), axis=2)
            gray = sub.mean(axis=2)
            ink = ((delta >= 20) & (gray < 235)).astype(np.uint8) * 255
            yy0 = max(0, y0 - 2)
            xx0 = max(0, x0 - 2)
            text_mask_arr[yy0:yy0 + ink.shape[0], xx0:xx0 + ink.shape[1]] = np.maximum(
                text_mask_arr[yy0:yy0 + ink.shape[0], xx0:xx0 + ink.shape[1]], ink
            )
        color = (220, 20, 60, 255) if role in {"EDGE_LABEL", "LEGEND_LABEL"} else (0, 102, 204, 255)
        text_draw.rectangle(local_box, outline=color, width=2)
        draw_label(text_draw, (local_box[0] + 1, local_box[1] - 12), tid, color)
        measurements.append({
            "ELEMENT_ID": tid,
            "ROLE": role,
            "SCRIPT_CLASS": script_class,
            "TEXT_SAMPLE": sample,
            "SOURCE_LINE": source_line,
            "DECLARED_PT": declared_pt,
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": declared_pt,
            "BBOX_X0": local_box[0],
            "BBOX_Y0": local_box[1],
            "BBOX_X1": local_box[2],
            "BBOX_Y1": local_box[3],
            "H_INK_PX": h_ink,
            "INK_X0": ink_box[0],
            "INK_Y0": ink_box[1],
            "INK_X1": ink_box[2],
            "INK_Y1": ink_box[3],
        })

    text_overlay.convert("RGB").save(ROOT / "text_measurement_overlay_300dpi.png")
    text_mask = Image.fromarray(text_mask_arr, mode="L")
    text_mask.save(ROOT / "text_foreground_mask_300dpi.png")

    graphic_mask = Image.new("L", fig.size, 0)
    gdraw = ImageDraw.Draw(graphic_mask)
    for line in page_objects.get("line", []):
        if line.get("bottom", -1) < FIG_RECT_PT[1] or line.get("top", 9999) > FIG_RECT_PT[3]:
            continue
        if line.get("x1", -1) < FIG_RECT_PT[0] or line.get("x0", 9999) > FIG_RECT_PT[2]:
            continue
        pts = line.get("pts") or []
        if len(pts) >= 2:
            local_pts = [
                (int(round((p[0] - FIG_RECT_PT[0]) * sx)), int(round((p[1] - FIG_RECT_PT[1]) * sy)))
                for p in pts
            ]
            width = max(1, int(round(float(line.get("linewidth") or 0.6) * (sx + sy) / 2)))
            gdraw.line(local_pts, fill=255, width=width)
    for curve in page_objects.get("curve", []):
        if curve.get("bottom", -1) < FIG_RECT_PT[1] or curve.get("top", 9999) > FIG_RECT_PT[3]:
            continue
        if curve.get("x1", -1) < FIG_RECT_PT[0] or curve.get("x0", 9999) > FIG_RECT_PT[2]:
            continue
        pts = curve.get("pts") or []
        if len(pts) < 2:
            continue
        local_pts = [
            (int(round((p[0] - FIG_RECT_PT[0]) * sx)), int(round((p[1] - FIG_RECT_PT[1]) * sy)))
            for p in pts
        ]
        width = max(1, int(round(float(curve.get("linewidth") or 0.6) * (sx + sy) / 2)))
        area_pt2 = max(0.0, (float(curve.get("x1", 0)) - float(curve.get("x0", 0))) * (float(curve.get("bottom", 0)) - float(curve.get("top", 0))))
        if curve.get("fill") and area_pt2 < 35.0:
            gdraw.polygon(local_pts, fill=255)
        else:
            gdraw.line(local_pts, fill=255, width=width, joint="curve")
    graphic_mask.save(ROOT / "graphics_vector_mask_300dpi.png")

    text_bool = np.asarray(text_mask) > 0
    graphic_bool = np.asarray(graphic_mask) > 0
    intersection = text_bool & graphic_bool
    candidate_count = int(intersection.sum())
    candidate_mask = Image.fromarray((intersection.astype(np.uint8) * 255), mode="L")
    candidate_mask.save(ROOT / "overlap_candidate_mask_300dpi.png")
    candidate_overlay = fig.convert("RGBA")
    red = Image.new("RGBA", fig.size, (255, 0, 0, 0))
    red.putalpha(candidate_mask)
    candidate_overlay = Image.alpha_composite(candidate_overlay, red)
    candidate_overlay.convert("RGB").save(ROOT / "overlap_candidate_overlay_300dpi.png")

    base_values = [m["H_INK_PX"] for m in measurements if m["ROLE"] == "NODE_MAIN" and m["SCRIPT_CLASS"] == "CJK_FULL"]
    base_median = statistics.median(base_values)
    grouped = {}
    for m in measurements:
        grouped.setdefault((m["ROLE"], m["SCRIPT_CLASS"]), []).append(m["H_INK_PX"])
    for m in measurements:
        cls_med = statistics.median(grouped[(m["ROLE"], m["SCRIPT_CLASS"])])
        m["CLASS_MEDIAN_PX"] = cls_med
        m["RATIO_TO_CLASS_MEDIAN"] = round(m["H_INK_PX"] / cls_med, 4) if cls_med else 0
        m["ROLE_RATIO_TO_BASE"] = round(cls_med / base_median, 4) if base_median else 0
        if m["SCRIPT_CLASS"] == "CJK_FULL":
            threshold = 30
        elif m["SCRIPT_CLASS"] == "MATH_BASE":
            threshold = 22
        elif m["SCRIPT_CLASS"] == "MIXED_CJK_LATIN":
            threshold = 30
        else:
            threshold = 17
        m["PIXEL_THRESHOLD_PX"] = threshold
        m["MACHINE_MARGIN_TO_THRESHOLD_PX"] = m["H_INK_PX"] - threshold

    fieldnames = list(measurements[0].keys())
    with (ROOT / "pixel_measurements_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(measurements)

    with (ROOT / "font_audit_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ELEMENT_ID", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_OBSERVED_PT_EQUIVALENT"])
        for m in measurements:
            writer.writerow([m["ELEMENT_ID"], SOURCE.name, m["SOURCE_LINE"], m["DECLARED_PT"], 1.0, m["EFFECTIVE_PT"], "measured separately from PDF text bboxes"])

    with (ROOT / "visible_object_denominator_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["OBJECT_ID", "OBJECT_KIND", "VISIBLE_SEMANTIC_OBJECT", "BBOX_X0_PT", "BBOX_TOP_PT", "BBOX_X1_PT", "BBOX_BOTTOM_PT"])
        for oid, kind, label, rect in OBJECTS:
            writer.writerow([oid, kind, label, *rect])

    with (ROOT / "all_unordered_pairs_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B", "DX_PX", "DY_PX", "BBOX_GAP_EUCLIDEAN_PX", "BBOX_GEOMETRY_CLASS"])
        for idx, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
            dx, dy, gap = bbox_gap_px(a[3], b[3], sx, sy)
            if dx == 0 and dy == 0:
                cls = "BBOX_TOUCH_OR_OVERLAP"
            elif dx > 0 and dy == 0:
                cls = "SEPARATED_X"
            elif dy > 0 and dx == 0:
                cls = "SEPARATED_Y"
            else:
                cls = "DIAGONALLY_SEPARATED"
            writer.writerow([f"P{idx:03d}", a[0], b[0], round(dx, 2), round(dy, 2), round(gap, 2), cls])

    codepoint_rows = []
    for tid, _, _, sample, source_line, _, rect in TEXTS:
        for idx, ch in enumerate(sample):
            codepoint_rows.append(["SOURCE_SEMANTIC_SAMPLE", tid, idx, ch, f"U+{ord(ch):04X}", source_line])
        selected = []
        for ch in page_chars:
            cx = (float(ch["x0"]) + float(ch["x1"])) / 2
            cy = (float(ch["top"]) + float(ch["bottom"])) / 2
            if rect[0] - 0.6 <= cx <= rect[2] + 0.6 and rect[1] - 0.6 <= cy <= rect[3] + 0.6:
                selected.append(ch)
        selected.sort(key=lambda ch: float(ch["x0"]))
        actual = "".join(str(ch["text"]) for ch in selected)
        for idx, ch in enumerate(actual):
            codepoint_rows.append(["PDF_EXTRACTED", tid, idx, ch, f"U+{ord(ch):04X}", source_line])
    with (ROOT / "codepoint_inventory_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["RECORD_KIND", "ELEMENT_ID", "CHAR_INDEX", "CHAR", "CODEPOINT", "SOURCE_LINE"])
        writer.writerows(codepoint_rows)

    for rid, name, rect in ROIS:
        roi = full.crop(pdf_to_px(rect, sx, sy))
        one = ROOT / f"roi_{rid}_{name}_native1x.png"
        eight = ROOT / f"roi_{rid}_{name}_nearest8x.png"
        roi.save(one)
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(eight)

    node_bboxes = {oid: rect for oid, kind, _, rect in OBJECTS if kind == "DISTRIBUTION_NODE"}
    text_rect_by_id = {t[0]: t[6] for t in TEXTS}
    internal_pairs = [("O02", "T02"), ("O03", "T03"), ("O03", "T04"), ("O05", "T06"), ("O06", "T07"), ("O06", "T08"), ("O08", "T10"), ("O08", "T11"), ("O09", "T12"), ("O09", "T13")]
    internal_clearances = []
    for oid, tid in internal_pairs:
        n = node_bboxes[oid]
        t = text_rect_by_id[tid]
        values = [(t[0] - n[0]) * sx, (n[2] - t[2]) * sx, (t[1] - n[1]) * sy, (n[3] - t[3]) * sy]
        internal_clearances.append([oid, tid, *[round(v, 2) for v in values], round(min(values), 2)])
    with (ROOT / "node_text_border_clearance_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["NODE_ID", "TEXT_ID", "LEFT_PX", "RIGHT_PX", "TOP_PX", "BOTTOM_PX", "MIN_BBOX_CLEARANCE_PX"])
        writer.writerows(internal_clearances)

    clearance_rows = []
    for aid, bid in [("T03", "T04"), ("T07", "T08"), ("T10", "T11"), ("T12", "T13")]:
        dx, dy, gap = bbox_gap_px(text_rect_by_id[aid], text_rect_by_id[bid], sx, sy)
        clearance_rows.append([f"{aid}-{bid}", "TEXT_TEXT_BBOX", round(gap, 2), "stacked lines inside one node"])
    edge_line_clearances = [
        ("T14-O12_LINE", (287.83755 - 283.49) * sy - (0.58 * sy / 2)),
        ("T15-O13_LINE", (348.78300 - 344.44) * sy - (0.58 * sy / 2)),
        ("T16-O14_LINE", (221.78 - 215.50883) * sx - (0.58 * sx / 2)),
        ("T17-O15_LINE", (367.76 - 361.49514) * sx - (0.58 * sx / 2)),
        ("T18-O16_LINE", (409.72845 - 406.15) * sy - (0.58 * sy / 2)),
        ("T19-O17_ARROWHEAD", (462.43 - 454.98772) * sx),
        ("T20-O18_ARROWHEAD", (462.22 - 455.62094) * sx),
    ]
    for name, value in edge_line_clearances:
        clearance_rows.append([name, "TEXT_TO_LINE_ARROW_BBOX", round(value, 2), "conservative vector/text bbox separation"])
    for row in internal_clearances:
        clearance_rows.append([f"{row[1]}-{row[0]}", "NODE_TEXT_TO_BORDER_BBOX", row[-1], "minimum of four node-border sides"])
    caption_crop_edge = min((87.48 - FIG_RECT_PT[0]) * sx, (FIG_RECT_PT[3] - 455.44) * sy)
    clearance_rows.append(["T21_T22-FIGURE_CROP_EDGE", "TEXT_TO_IMAGE_EDGE_BBOX", round(caption_crop_edge, 2), "local crop; official page edge is farther"])
    caption_figure_gap = (430.0 - 424.61) * sy
    clearance_rows.append(["O08_O09-O19", "FIGURE_TO_CAPTION_BBOX", round(caption_figure_gap, 2), "bottom node border to caption object bbox"])
    with (ROOT / "clearance_measurements_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["MEASUREMENT_ID", "CLEARANCE_CLASS", "CLEARANCE_PX", "GEOMETRY_BASIS"])
        writer.writerows(clearance_rows)

    overall_min_clearance = min(float(row[2]) for row in clearance_rows)

    summary = {
        "pdf_page_number_1_based": PAGE_NUMBER_ONE,
        "printed_folio": 693,
        "page_points": [page_w, page_h],
        "render_pixels": [full.width, full.height],
        "render_scale_px_per_pt": [sx, sy],
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "visible_object_count": len(OBJECTS),
        "unordered_pair_count": len(OBJECTS) * (len(OBJECTS) - 1) // 2,
        "text_element_count": len(TEXTS),
        "overlap_candidate_pixel_count": candidate_count,
        "minimum_node_text_border_bbox_clearance_px": min(row[-1] for row in internal_clearances),
        "minimum_text_clearance_across_audited_classes_px": overall_min_clearance,
        "base_node_cjk_ink_median_px": base_median,
        "machine_only": True,
    }
    (ROOT / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
