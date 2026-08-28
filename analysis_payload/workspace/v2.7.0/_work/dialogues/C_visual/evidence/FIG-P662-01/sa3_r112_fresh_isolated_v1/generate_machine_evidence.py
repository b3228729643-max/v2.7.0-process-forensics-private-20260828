from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FULL = ROOT / "full_page_300dpi.png"
SCALE = 300.0 / 72.0

# All rectangles use PDF page coordinates in points: x0, y0, x1, y1.
# The denominator follows the authored node/path granularity in the frozen source.
OBJECTS = [
    ("O01", "BADGE", "step badge 1", (127.46, 260.80, 143.34, 276.67)),
    ("O02", "NODE", "Y1 Gamma input node", (88.16, 283.05, 182.64, 307.14)),
    ("O03", "NODE", "Y2 Gamma input node", (88.17, 311.40, 182.63, 335.49)),
    ("O04", "TEXT_NODE", "vertical ellipsis", (132.30, 335.86, 138.50, 347.82)),
    ("O05", "NODE", "YK Gamma input node", (85.73, 351.93, 185.07, 376.03)),
    ("O06", "NOTE_NODE", "independent/common-rate note", (89.40, 383.04, 181.40, 392.17)),
    ("O07", "BADGE", "step badge 2", (226.67, 285.18, 242.55, 301.05)),
    ("O08", "NODE", "total S node", (197.76, 310.59, 271.46, 341.96)),
    ("O09", "NODE", "division by S node", (296.97, 312.10, 325.32, 340.45)),
    ("O10", "BADGE", "step badge 3", (303.21, 285.18, 319.09, 301.05)),
    ("O11", "NODE", "ratio Theta_k node", (336.94, 310.69, 419.15, 341.87)),
    ("O12", "NODE", "Dirichlet result node", (431.62, 310.69, 516.66, 341.87)),
    ("O13", "GEOMETRY", "simplex triangle", (461.39, 280.64, 486.90, 302.75)),
    ("O14", "MARKER", "simplex point", (472.35, 292.74, 475.94, 296.32)),
    ("O15", "NOTE_NODE", "simplex-point label", (486.12, 288.14, 519.99, 297.21)),
    ("O16", "NODE", "S independent Theta result node", (261.54, 363.98, 400.44, 392.33)),
    ("O17", "NODE", "K=2 Beta special-case node", (413.20, 363.98, 520.91, 392.33)),
    ("O18", "LINE_ARROW", "Y1 to total arrow", (182.96, 295.10, 196.76, 316.75)),
    ("O19", "LINE_ARROW", "Y2 to total arrow", (182.95, 323.44, 196.22, 326.59)),
    ("O20", "LINE_ARROW", "YK to total arrow", (185.40, 335.91, 196.95, 363.98)),
    ("O21", "LINE_ARROW", "total to divide arrow", (271.81, 325.06, 295.41, 327.50)),
    ("O22", "LINE_ARROW", "divide to ratio arrow", (325.67, 325.06, 335.38, 327.50)),
    ("O23", "LINE_ARROW", "ratio to Dirichlet arrow", (419.50, 325.06, 430.06, 327.50)),
    ("O24", "AUX_LINE", "total to independence auxiliary path", (234.61, 342.31, 291.31, 363.98)),
    ("O25", "AUX_LINE", "ratio to independence auxiliary path", (370.68, 342.22, 378.05, 363.98)),
    ("O26", "CAPTION", "Figure 34.5 caption, two lines", (87.48, 395.42, 519.13, 423.07)),
]

TEXT = [
    ("T01", "BADGE", "1", 8.47, (133.30, 264.99, 137.50, 273.46)),
    ("T02", "FORMULA", "Y_1~Gamma(alpha_1,lambda)", 9.17, (94.68, 290.76, 176.12, 301.19)),
    ("T03", "SCRIPT", "subscripts 1,1", 6.42, (101.41, 294.78, 162.34, 301.19)),
    ("T04", "FORMULA", "Y_2~Gamma(alpha_2,lambda)", 9.17, (94.69, 319.10, 176.10, 329.54)),
    ("T05", "SCRIPT", "subscripts 2,2", 6.42, (101.42, 323.12, 162.33, 329.54)),
    ("T06", "SYMBOL", "vertical ellipsis", 11.96, (132.30, 335.86, 138.50, 347.82)),
    ("T07", "FORMULA", "Y_K~Gamma(alpha_K,lambda)", 9.17, (92.25, 359.64, 178.55, 370.07)),
    ("T08", "SCRIPT", "subscripts K,K", 6.42, (98.97, 363.66, 164.29, 370.07)),
    ("T09", "NOTE", "mutually independent, common rate parameter", 8.47, (89.40, 383.10, 174.08, 392.17)),
    ("T10", "FORMULA", "lambda in common-rate note", 8.97, (176.07, 383.04, 181.40, 392.01)),
    ("T11", "BADGE", "2", 8.47, (232.52, 289.41, 236.71, 297.88)),
    ("T12", "NODE_LABEL", "total", 9.17, (225.45, 314.73, 243.78, 324.54)),
    ("T13", "FORMULA", "S=sum Y_k", 9.17, (207.73, 323.96, 261.13, 340.64)),
    ("T14", "SCRIPT", "upper K", 6.42, (234.89, 323.96, 240.44, 330.37)),
    ("T15", "SCRIPT", "lower k=1 and Y subscript k", 6.42, (234.89, 331.27, 261.13, 339.99)),
    ("T16", "FORMULA", "divide S", 9.17, (304.98, 322.50, 317.04, 331.66)),
    ("T17", "BADGE", "3", 8.47, (309.05, 289.36, 313.24, 297.83)),
    ("T18", "NODE_LABEL", "ratio", 9.17, (368.88, 316.49, 387.21, 326.30)),
    ("T19", "FORMULA", "Theta_k=Y_k/S", 9.17, (355.13, 327.79, 400.68, 338.23)),
    ("T20", "SCRIPT", "Theta and Y subscripts k", 6.42, (362.83, 331.81, 390.97, 338.23)),
    ("T21", "FORMULA", "Theta~Dir(alpha)", 9.17, (450.81, 315.25, 497.47, 324.42)),
    ("T22", "FORMULA", "sum_k Theta_k=1", 9.17, (451.67, 326.21, 496.60, 338.95)),
    ("T23", "SCRIPT", "summation and Theta subscripts k", 6.42, (460.94, 330.23, 479.41, 338.95)),
    ("T24", "NOTE", "simplex point", 8.47, (486.12, 288.14, 519.99, 297.21)),
    ("T25", "FORMULA", "S independent Theta; S~Gamma(alpha_0,lambda)", 9.17, (272.49, 373.76, 389.49, 384.20)),
    ("T26", "SCRIPT", "alpha subscript 0", 6.42, (371.82, 377.78, 375.71, 384.20)),
    ("T27", "NOTE_FORMULA", "K=2 special case", 9.17, (430.32, 368.41, 484.84, 378.23)),
    ("T28", "FORMULA", "Theta_1~Beta(alpha_1,alpha_2)", 9.17, (430.32, 379.72, 503.78, 390.81)),
    ("T29", "SCRIPT", "Beta-case subscripts 1,1,2", 6.42, (438.02, 383.74, 499.60, 390.15)),
    ("T30", "CAPTION", "Figure 34.5 caption line 1", 9.96, (87.48, 395.42, 519.13, 409.85)),
    ("T31", "CAPTION", "Figure 34.5 caption line 2", 9.96, (87.48, 412.40, 492.38, 423.07)),
]

CROP_PT = (82.0, 255.0, 525.0, 394.0)
WITH_CAPTION_PT = (82.0, 255.0, 525.0, 426.0)
INTEGRATION_PT = (68.0, 220.0, 530.0, 460.0)


def pt_to_px(v: float) -> int:
    return int(round(v * SCALE))


def rect_to_full_px(rect):
    return tuple(pt_to_px(v) for v in rect)


def crop_by_pt(im: Image.Image, rect):
    return im.crop(rect_to_full_px(rect))


def load_font(size=18):
    for p in [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
    ]:
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def rel_rect(rect, origin_pt):
    ox, oy = origin_pt[:2]
    return tuple(pt_to_px(v - (ox if i % 2 == 0 else oy)) for i, v in enumerate(rect))


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy) * SCALE


def bbox_intersection_px(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0
    return int(round((x1 - x0) * SCALE)) * int(round((y1 - y0) * SCALE))


def dominant_background(arr):
    if arr.size == 0:
        return np.array([255, 255, 255], dtype=np.int16)
    q = (arr.reshape(-1, 3) // 8) * 8
    colors, counts = np.unique(q, axis=0, return_counts=True)
    return colors[counts.argmax()].astype(np.int16)


def ink_height(full_arr, rect):
    x0, y0, x1, y1 = rect_to_full_px(rect)
    roi = full_arr[max(0, y0):min(full_arr.shape[0], y1 + 1), max(0, x0):min(full_arr.shape[1], x1 + 1)]
    if roi.size == 0:
        return 0, 0, 0
    bg = dominant_background(roi)
    delta = np.max(np.abs(roi.astype(np.int16) - bg), axis=2)
    mask = delta >= 20
    ys, xs = np.where(mask)
    if not len(ys):
        return 0, 0, 0
    return int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1), int(mask.sum())


def make_masks(full_arr):
    masks = {}
    h, w = full_arr.shape[:2]
    dark = np.min(full_arr, axis=2) < 205
    for oid, _, _, rect in OBJECTS:
        m = np.zeros((h, w), dtype=np.uint8)
        x0, y0, x1, y1 = rect_to_full_px(rect)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, x1 + 1), min(h, y1 + 1)
        m[y0:y1, x0:x1] = dark[y0:y1, x0:x1]
        masks[oid] = m
    return masks


def main():
    full = Image.open(FULL).convert("RGB")
    full_arr = np.array(full)
    crop = crop_by_pt(full, CROP_PT)
    with_caption = crop_by_pt(full, WITH_CAPTION_PT)
    integration = crop_by_pt(full, INTEGRATION_PT)
    crop.save(ROOT / "figure_crop_300dpi.png", dpi=(300, 300))
    with_caption.save(ROOT / "figure_with_caption_300dpi.png", dpi=(300, 300))
    integration.save(ROOT / "page_integration_300dpi.png", dpi=(300, 300))
    crop.convert("L").save(ROOT / "grayscale_300dpi.png", dpi=(300, 300))

    font = load_font(18)
    obj_overlay = with_caption.copy()
    d = ImageDraw.Draw(obj_overlay)
    colors = {
        "BADGE": "#d62728", "NODE": "#0066cc", "TEXT_NODE": "#8c564b",
        "NOTE_NODE": "#9467bd", "GEOMETRY": "#2ca02c", "MARKER": "#ff7f0e",
        "LINE_ARROW": "#17becf", "AUX_LINE": "#bcbd22", "CAPTION": "#e377c2",
    }
    for oid, kind, _, rect in OBJECTS:
        rr = rel_rect(rect, WITH_CAPTION_PT)
        c = colors[kind]
        d.rectangle(rr, outline=c, width=3)
        d.text((rr[0] + 2, rr[1] + 2), oid, fill=c, font=font, stroke_width=2, stroke_fill="white")
    obj_overlay.save(ROOT / "semantic_object_overlay_300dpi.png", dpi=(300, 300))

    text_overlay = with_caption.copy()
    d = ImageDraw.Draw(text_overlay)
    tcolors = {"SCRIPT": "#d62728", "CAPTION": "#e377c2", "BADGE": "#ff7f0e"}
    for tid, role, _, _, rect in TEXT:
        rr = rel_rect(rect, WITH_CAPTION_PT)
        c = tcolors.get(role, "#0057b8")
        d.rectangle(rr, outline=c, width=2)
        d.text((rr[0] + 1, rr[1] - 18), tid, fill=c, font=font, stroke_width=2, stroke_fill="white")
    text_overlay.save(ROOT / "text_glyph_overlay_300dpi.png", dpi=(300, 300))

    masks = make_masks(full_arr)
    with (ROOT / "machine_objects.csv").open("w", encoding="utf-8-sig", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["OBJECT_ID", "CATEGORY", "DESCRIPTION", "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT"])
        for oid, kind, desc, rect in OBJECTS:
            wr.writerow([oid, kind, desc, *[f"{v:.2f}" for v in rect]])

    with (ROOT / "machine_pairs.csv").open("w", encoding="utf-8-sig", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B", "BBOX_GAP_PX", "BBOX_INTERSECTION_AREA_PX", "RASTER_MASK_INTERSECTION_PX"])
        for idx, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
            aid, bid = a[0], b[0]
            wr.writerow([
                f"P{idx:03d}", aid, bid, f"{bbox_gap(a[3], b[3]):.2f}",
                bbox_intersection_px(a[3], b[3]), int(np.count_nonzero(masks[aid] & masks[bid])),
            ])

    with (ROOT / "machine_text_measurements.csv").open("w", encoding="utf-8-sig", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["TEXT_ID", "ROLE", "TEXT_SAMPLE", "PDF_SPAN_SIZE_PT", "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT", "H_INK_PX", "W_INK_PX", "INK_PIXELS"])
        for tid, role, sample, size, rect in TEXT:
            h, w, n = ink_height(full_arr, rect)
            wr.writerow([tid, role, sample, f"{size:.2f}", *[f"{v:.2f}" for v in rect], h, w, n])

    rois = {
        "risk_roi_fanin_native1x.png": (178.0, 282.0, 203.0, 378.0),
        "risk_roi_aux_native1x.png": (225.0, 337.0, 405.0, 395.0),
        "risk_roi_simplex_native1x.png": (450.0, 274.0, 523.0, 306.0),
        "risk_roi_sumtext_native1x.png": (196.0, 307.0, 273.0, 344.0),
        "risk_roi_resulttext_native1x.png": (334.0, 307.0, 521.0, 344.0),
        "risk_roi_bottomtext_native1x.png": (258.0, 360.0, 523.0, 395.0),
    }
    for name, rect in rois.items():
        roi = crop_by_pt(full, rect)
        roi.save(ROOT / name, dpi=(300, 300))
        zoom = roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST)
        zoom.save(ROOT / name.replace("native1x", "nearest8x"))


if __name__ == "__main__":
    main()
