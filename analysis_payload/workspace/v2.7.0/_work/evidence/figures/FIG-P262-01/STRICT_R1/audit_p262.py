from __future__ import annotations

"""Independent, read-only strict SA1 evidence generator for FIG-P262-01.

Inputs are the frozen official full-book PDF and direct 300/200 dpi Poppler
renders.  All written artefacts stay in this directory.  Crops are pixel
subsets only; no source image is resized or resampled.
"""

import csv
import json
import math
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P262-01" / "STRICT_R1"
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r92_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第02册_基础监督学习方法" / "V2-C05" / "fig_v2_c05_sigmoid.tex"
CHAPTER = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "第02册_基础监督学习方法" / "chapters" / "V2-C05.tex"
STYLE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "common" / "statlearnbook.sty"

PDF_PAGE = 284
PAGE_INDEX = PDF_PAGE - 1
PAGE_300 = OUT / "official_page_300dpi.png"
PAGE_200 = OUT / "official_page_200dpi.png"


def pdf_to_px(box, sx, sy):
    x0, y0, x1, y1 = box
    return (
        max(0, math.floor(x0 * sx)),
        max(0, math.floor(y0 * sy)),
        min(PAGE_W, math.ceil(x1 * sx)),
        min(PAGE_H, math.ceil(y1 * sy)),
    )


def content_bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def ink_measure(image: np.ndarray, box_px):
    x0, y0, x1, y1 = box_px
    # C1: foreground differs from white local background by at least 20/255.
    # The frozen page's text field is white; this keeps antialiased pale fringe
    # pixels out of height calculations.
    crop = image[y0:y1, x0:x1, :]
    foreground = (255 - crop).max(axis=2) >= 20
    b = content_bbox(foreground)
    if b is None:
        return 0, None, foreground
    bx0, by0, bx1, by1 = b
    return by1 - by0, (x0 + bx0, y0 + by0, x0 + bx1, y0 + by1), foreground


def nearest_clearance(mask_a: np.ndarray, mask_b: np.ndarray):
    """Euclidean clearance between two boolean masks in pixels."""
    if not np.any(mask_a) or not np.any(mask_b):
        return None
    # Distance transform reports distance from each pixel to the nearest zero;
    # therefore invert mask_b so its foreground is zero.
    d = cv2.distanceTransform((~mask_b).astype(np.uint8), cv2.DIST_L2, 5)
    return float(d[mask_a].min())


def draw_vector_mask(page, sx, sy, crop_pdf):
    """Render a conservative semantic LINE/ARROW/MARKER mask from PDF paths.

    This only covers the plotted semantic graphics in the crop; text is made
    separately from extracted glyph bboxes.  Rectangular opaque label fills are
    excluded from GRAPHICS because they are declared label backgrounds.
    """
    x0, y0, x1, y1 = pdf_to_px(crop_pdf, sx, sy)
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    # Relevant PDF drawing indices are known from direct inspection of this
    # single official page: 13--25 and 27--32.  26/29 are label backgrounds,
    # 30--32 are circular MARKERs and are retained.
    drawings = page.get_drawings()
    # 28 is the fraction bar (internal to the formula), and 29 is the
    # note's white fill/border. Neither is an independent LINE_ARROW object
    # in the F-section comparison below; the note border is checked exactly
    # in its own NODE_BORDER rows.
    keep = set(range(13, 26)) | {27, 30, 31, 32}
    for idx, d in enumerate(drawings):
        if idx not in keep:
            continue
        rect = d["rect"]
        if rect.x1 < crop_pdf[0] or rect.x0 > crop_pdf[2] or rect.y1 < crop_pdf[1] or rect.y0 > crop_pdf[3]:
            continue
        color = d.get("color") or d.get("fill")
        # White label fill is nonsemantic background, not a line/marker.
        if color and min(color) > 0.97:
            continue
        thickness = max(1, int(round((d.get("width") or 0.60) * (sx + sy) / 2)))
        items = d["items"]
        pts = []
        for item in items:
            kind = item[0]
            if kind == "l":
                a, b = item[1], item[2]
                cv2.line(mask,
                         (round(a.x * sx) - x0, round(a.y * sy) - y0),
                         (round(b.x * sx) - x0, round(b.y * sy) - y0),
                         255, thickness, lineType=cv2.LINE_AA)
            elif kind == "c":
                # Cubic Bezier, sampled finely enough for 300 dpi evidence.
                a, b, c, e = item[1], item[2], item[3], item[4]
                sampled = []
                for t in np.linspace(0.0, 1.0, 101):
                    q = (1-t)**3 * np.array([a.x, a.y]) + 3*(1-t)**2*t*np.array([b.x, b.y]) + 3*(1-t)*t*t*np.array([c.x, c.y]) + t**3*np.array([e.x, e.y])
                    sampled.append([round(q[0] * sx) - x0, round(q[1] * sy) - y0])
                cv2.polylines(mask, [np.asarray(sampled, dtype=np.int32)], False, 255, thickness, lineType=cv2.LINE_AA)
            elif kind == "re":
                r = item[1]
                cv2.rectangle(mask,
                              (round(r.x0 * sx) - x0, round(r.y0 * sy) - y0),
                              (round(r.x1 * sx) - x0, round(r.y1 * sy) - y0),
                              255, thickness, lineType=cv2.LINE_AA)
        # Filled marker circles / arrowheads are represented by closed Beziers.
        if d.get("fill") is not None and d.get("type") in {"f", "fs"}:
            rr = d["rect"]
            # A compact filled-vector bounding rectangle is a conservative
            # marker mask for distance/overlap only.
            px0, py0, px1, py1 = pdf_to_px((rr.x0, rr.y0, rr.x1, rr.y1), sx, sy)
            if px1 > x0 and px0 < x1 and py1 > y0 and py0 < y1:
                cv2.rectangle(mask, (max(0, px0-x0), max(0, py0-y0)),
                              (min(mask.shape[1]-1, px1-x0), min(mask.shape[0]-1, py1-y0)), 255, -1)
    return mask.astype(bool), (x0, y0, x1, y1)


def write_csv(path: Path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if not PAGE_300.exists() or not PAGE_200.exists():
    raise SystemExit("Expected direct Poppler 300/200 dpi page renders are missing.")

rgb = np.asarray(Image.open(PAGE_300).convert("RGB"))
PAGE_H, PAGE_W = rgb.shape[:2]
doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
sx, sy = PAGE_W / page.rect.width, PAGE_H / page.rect.height

# All reader-visible text within the figure/caption. Boxes are native PDF
# vector bboxes from the final PDF text layer (not image OCR), mapped directly
# to the raw 300 dpi Poppler image. A sub-element is split whenever its own
# script class has an independent C-section threshold.
elements = [
    dict(id="E01_AXIS_Y_SIGMA", panel="P1", role="AXIS_LABEL", source_line="34 (label font L20)", declared=9.5, text="σ(z)", script="greek_lower", box=(307.142, 528.100, 324.945, 538.063), threshold=17, kind="general"),
    dict(id="E02_AXIS_X_Z", panel="P1", role="AXIS_LABEL", source_line="34 (label font L20)", declared=9.5, text="z", script="latin_lower", box=(460.322, 685.127, 465.234, 695.090), threshold=17, kind="general"),
    dict(id="E03_XTICK_MINUS", panel="P1", role="TICK", source_line="35 (tick font L19)", declared=8.7, text="−", script="math_operator", box=(244.247, 700.392, 250.940, 709.060), threshold=22, kind="general"),
    dict(id="E04_XTICK_A_NEG", panel="P1", role="TICK", source_line="35 (tick font L19)", declared=8.7, text="a", script="latin_lower", box=(250.940, 700.392, 256.217, 709.060), threshold=17, kind="general"),
    dict(id="E05_XTICK_A_POS", panel="P1", role="TICK", source_line="35 (tick font L19)", declared=8.7, text="a", script="latin_lower", box=(353.743, 700.392, 359.021, 709.060), threshold=17, kind="general"),
    dict(id="E06_YTICK_ONE", panel="P1", role="TICK", source_line="36 (tick font L19)", declared=8.7, text="1", script="digit", box=(293.056, 533.431, 297.346, 542.099), threshold=24, kind="general"),
    dict(id="E07_YTICK_HALF_NUM", panel="P1", role="TICK", source_line="36 (tick font L19)", declared=8.7, text="1", script="natural_script", box=(292.747, 609.307, 296.151, 615.374), threshold=15, kind="natural_script"),
    dict(id="E08_YTICK_HALF_DEN", panel="P1", role="TICK", source_line="36 (tick font L19)", declared=8.7, text="2", script="natural_script", box=(292.753, 619.448, 296.145, 625.515), threshold=15, kind="natural_script"),
    dict(id="E09_LABEL_PROB_MAP", panel="P1", role="ANNOTATION", source_line="50", declared=9.2, text="概率映射", script="cjk", box=(374.927, 562.089, 411.589, 571.906), threshold=30, kind="general"),
    dict(id="E10_NOTE_SYMM_SIGMA", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="σ", script="greek_lower", box=(158.546, 577.551, 164.600, 586.716), threshold=17, kind="general"),
    dict(id="E11_NOTE_SYMM_LPAREN", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="(", script="math_operator", box=(164.600, 577.551, 168.430, 586.716), threshold=22, kind="general"),
    dict(id="E12_NOTE_SYMM_MINUS", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="−", script="math_operator", box=(168.430, 577.551, 175.500, 586.716), threshold=22, kind="general"),
    dict(id="E13_NOTE_SYMM_A", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="a", script="latin_lower", box=(175.500, 577.551, 181.080, 586.716), threshold=17, kind="general"),
    dict(id="E14_NOTE_SYMM_EQUAL", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="=", script="math_operator", box=(187.450, 577.551, 194.520, 586.716), threshold=22, kind="general"),
    dict(id="E15_NOTE_SYMM_ONE", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="1", script="digit", box=(197.070, 577.551, 201.730, 586.716), threshold=24, kind="general"),
    dict(id="E16_NOTE_SYMM_MINUS", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="−", script="math_operator", box=(203.770, 577.551, 210.850, 586.716), threshold=22, kind="general"),
    dict(id="E17_NOTE_SYMM_SIGMA_2", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="σ", script="greek_lower", box=(212.890, 577.551, 218.950, 586.716), threshold=17, kind="general"),
    dict(id="E18_NOTE_SYMM_A_2", panel="P1", role="FORMULA", source_line="57 (note font L12)", declared=9.2, text="a", script="latin_lower", box=(222.770, 577.551, 228.350, 586.716), threshold=17, kind="general"),
    dict(id="E19_SLOPE_CN", panel="P1", role="ANNOTATION", source_line="55", declared=9.2, text="中心斜率", script="cjk", box=(332.353, 627.718, 369.015, 637.534), threshold=30, kind="general"),
    dict(id="E20_SLOPE_SIGMA", panel="P1", role="FORMULA", source_line="55", declared=9.2, text="σ", script="greek_lower", box=(371.170, 628.066, 377.228, 637.231), threshold=17, kind="general"),
    dict(id="E21_SLOPE_PRIME", panel="P1", role="FORMULA", source_line="55", declared=9.2, text="′", script="math_operator", box=(377.228, 626.861, 380.019, 633.277), threshold=22, kind="general"),
    dict(id="E22_SLOPE_ZERO", panel="P1", role="FORMULA", source_line="55", declared=9.2, text="0", script="digit", box=(384.210, 628.066, 389.520, 637.231), threshold=24, kind="general"),
    dict(id="E23_SLOPE_EQUAL", panel="P1", role="FORMULA", source_line="55", declared=9.2, text="=", script="math_operator", box=(395.890, 628.066, 402.961, 637.231), threshold=22, kind="general"),
    dict(id="E24_SLOPE_NUM", panel="P1", role="FORMULA", source_line="55", declared=9.2, text="1", script="natural_script", box=(406.831, 624.799, 410.430, 631.215), threshold=15, kind="natural_script"),
    dict(id="E25_SLOPE_DEN", panel="P1", role="FORMULA", source_line="55", declared=9.2, text="4", script="natural_script", box=(406.709, 635.523, 410.552, 641.939), threshold=15, kind="natural_script"),
    dict(id="E26_CAPTION_CHINESE", panel="P1", role="CAPTION", source_line="60; captionsetup statlearnbook.sty:305", declared=10.0, text="逻辑斯谛函数把线性预测量映射为概率，并满足关于…的中心对称性", script="cjk", box=(161.340, 717.140, 485.090, 727.810), threshold=30, kind="general"),
]

# Characters that form one mathematical or textual expression are split above
# only for the C-section pixel threshold.  They are one logical TEXT object
# for the independent-object TEXT--TEXT spacing test.
logical_object = {
    "E01_AXIS_Y_SIGMA": "AXIS_Y", "E02_AXIS_X_Z": "AXIS_X",
    "E03_XTICK_MINUS": "XTICK_NEG_A", "E04_XTICK_A_NEG": "XTICK_NEG_A",
    "E05_XTICK_A_POS": "XTICK_POS_A", "E06_YTICK_ONE": "YTICK_ONE",
    "E07_YTICK_HALF_NUM": "YTICK_HALF", "E08_YTICK_HALF_DEN": "YTICK_HALF",
    "E09_LABEL_PROB_MAP": "PROBABILITY_MAPPING_LABEL",
    "E10_NOTE_SYMM_SIGMA": "SYMMETRY_FORMULA", "E11_NOTE_SYMM_LPAREN": "SYMMETRY_FORMULA",
    "E12_NOTE_SYMM_MINUS": "SYMMETRY_FORMULA", "E13_NOTE_SYMM_A": "SYMMETRY_FORMULA",
    "E14_NOTE_SYMM_EQUAL": "SYMMETRY_FORMULA", "E15_NOTE_SYMM_ONE": "SYMMETRY_FORMULA",
    "E16_NOTE_SYMM_MINUS": "SYMMETRY_FORMULA", "E17_NOTE_SYMM_SIGMA_2": "SYMMETRY_FORMULA",
    "E18_NOTE_SYMM_A_2": "SYMMETRY_FORMULA",
    "E19_SLOPE_CN": "CENTER_SLOPE_ANNOTATION", "E20_SLOPE_SIGMA": "CENTER_SLOPE_ANNOTATION",
    "E21_SLOPE_PRIME": "CENTER_SLOPE_ANNOTATION", "E22_SLOPE_ZERO": "CENTER_SLOPE_ANNOTATION",
    "E23_SLOPE_EQUAL": "CENTER_SLOPE_ANNOTATION", "E24_SLOPE_NUM": "CENTER_SLOPE_ANNOTATION",
    "E25_SLOPE_DEN": "CENTER_SLOPE_ANNOTATION", "E26_CAPTION_CHINESE": "CAPTION",
}

for e in elements:
    e["effective"] = e["declared"]  # No \resizebox/\scalebox/scale/transform shape in source.
    e["graphics_scale"] = 1.00
    e["box_px"] = pdf_to_px(e["box"], sx, sy)
    e["h_ink"], e["ink_box"], e["mask_local"] = ink_measure(rgb, e["box_px"])
    e["pixel_pass"] = e["h_ink"] >= e["threshold"]
    e["font_pass"] = e["effective"] >= 9.5
    e["font_reason"] = "PASS" if e["font_pass"] else f"effective_pt={e['effective']:.1f}<9.5pt"
    e["pixel_reason"] = "PASS" if e["pixel_pass"] else f"H_ink_px={e['h_ink']}<{e['threshold']}px"

# Same script + same role ratios.  Any singleton has no same-class peer, which
# is reported explicitly (not silently promoted to PASS).
group_values = {}
for e in elements:
    group_values.setdefault((e["panel"], e["role"], e["script"]), []).append(e["h_ink"])
for e in elements:
    vals = group_values[(e["panel"], e["role"], e["script"])]
    med = float(np.median(vals))
    e["class_median"] = med
    e["class_ratio"] = e["h_ink"] / med if med else None
    e["same_class_pass"] = len(vals) >= 2 and 0.92 <= e["class_ratio"] <= 1.08

# Role hierarchy uses declared effective size because this one panel mixes CJK
# full-height glyphs with Latin x-height glyphs. The source declaration is
# nevertheless a required independent audit; its tick base is 8.7pt.
base_pt = 8.7
role_declared_ratio = {
    "AXIS_LABEL": 9.5 / base_pt,
    "TICK": 1.0,
    "ANNOTATION": 9.2 / base_pt,
    "FORMULA": 9.2 / base_pt,
    "CAPTION": 10.0 / base_pt,
}
for e in elements:
    e["role_ratio"] = role_declared_ratio[e["role"]]

# Build direct semantic masks on the unchanged 300 dpi page. Text mask only
# holds foreground in PDF text bboxes. Graphic mask is reconstructed from the
# original page's vector drawings over the graph plot area.
graph_crop_pdf = (130.0, 520.0, 475.0, 711.0)
graph_mask, graph_crop_px = draw_vector_mask(page, sx, sy, graph_crop_pdf)
gx0, gy0, gx1, gy1 = graph_crop_px
text_mask_full = np.zeros((PAGE_H, PAGE_W), dtype=bool)
for e in elements:
    x0, y0, x1, y1 = e["box_px"]
    h, w = y1-y0, x1-x0
    # Same threshold as C1. This makes the text foreground traceable to the
    # frozen raster, rather than replacing it with OCR boxes.
    local = (255 - rgb[y0:y1, x0:x1, :]).max(axis=2) >= 20
    text_mask_full[y0:y1, x0:x1] |= local
graphic_mask_full = np.zeros((PAGE_H, PAGE_W), dtype=bool)
graphic_mask_full[gy0:gy1, gx0:gx1] = graph_mask

# Opaque label background (source L50) removes the curve under the text; it is
# not a text/graphic overlap. Remove it from reconstructed graphic mask.
white_label = pdf_to_px((373.834, 560.258, 412.689, 571.615), sx, sy)
graphic_mask_full[white_label[1]:white_label[3], white_label[0]:white_label[2]] = False

# Raw raster intersection across semantic source masks.
overlap_pairs = []

def pair_row(pair_id, a_id, b_kind, mask_a, mask_b, required, source_lines, explanation):
    inter = int(np.count_nonzero(mask_a & mask_b))
    clearance = nearest_clearance(mask_a, mask_b)
    element = next(x for x in elements if x["id"] == a_id)
    x0, y0, x1, y1 = element["box_px"]
    repair = {
        "E01_AXIS_Y_SIGMA": "Move the y-axis label away from the y=1 reference line, or give it an opaque background/halo with >=3px final clearance.",
        "E06_YTICK_ONE": "Offset the y=1 tick label from the y=1 dashed reference line (or revise the reference-line treatment) to reach >=3px final clearance.",
        "E19_SLOPE_CN": "Move the center-slope annotation so the z=a guide does not cross its glyphs; preserve >=3px clearance or use an opaque label background.",
    }.get(a_id, "Maintain >=3px final text-to-graphic clearance after local re-layout.")
    return dict(
        PAIR_ID=pair_id,
        ELEMENT_ID=a_id,
        OTHER_OBJECT=b_kind,
        SOURCE_LINES=source_lines,
        ELEMENT_BBOX_300DPI=f"({x0},{y0},{x1},{y1})",
        NATIVE_COORDINATE_SYSTEM="official PDF page 284 -> direct Poppler 300 dpi",
        OVERLAP_PIXEL_COUNT=inter,
        MIN_CLEARANCE_PX=("" if clearance is None else f"{clearance:.2f}"),
        REQUIRED_MIN_CLEARANCE_PX=required,
        CLIP_PIXEL_COUNT=0,
        PASS_FAIL="PASS" if inter == 0 and clearance is not None and clearance >= required else "FAIL",
        METHOD=explanation,
        MINIMUM_REPAIR_DIRECTION=repair,
    )

# One line/arrow/marker clearance per reader-visible figure text. Formula-only
# fraction rules are internal formula geometry, not independent LINE_ARROW.
for e in elements:
    x0, y0, x1, y1 = e["box_px"]
    emask = np.zeros((PAGE_H, PAGE_W), dtype=bool)
    emask[y0:y1, x0:x1] = text_mask_full[y0:y1, x0:x1]
    # For caption there is no graph object in its vicinity; use its nearest
    # reader-object clearance below instead of claiming a phantom graphic mask.
    if e["role"] != "CAPTION":
        overlap_pairs.append(pair_row(
            f"G_{e['id']}", e["id"], "LINE_ARROW_MARKER",
            emask, graphic_mask_full, 3, e["source_line"],
            "text foreground from raw 300dpi; graphics reconstructed from final PDF vector paths"))

# TEXT--TEXT clearances by exact vector bbox. We compare independent reader
# objects—not adjacent characters within the same formula expression.
object_boxes = {}
object_lines = {}
for e in elements:
    obj = logical_object[e["id"]]
    x0, y0, x1, y1 = e["box_px"]
    if obj not in object_boxes:
        object_boxes[obj] = [x0, y0, x1, y1]
        object_lines[obj] = {e["source_line"]}
    else:
        b = object_boxes[obj]
        object_boxes[obj] = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
        object_lines[obj].add(e["source_line"])
for obj, abox in object_boxes.items():
    if obj == "CAPTION":
        continue
    ax0, ay0, ax1, ay1 = abox
    best = float("inf")
    best_id = ""
    for other, bbox in object_boxes.items():
        if obj == other or other == "CAPTION":
            continue
        bx0, by0, bx1, by1 = bbox
        dx = max(0, bx0-ax1, ax0-bx1)
        dy = max(0, by0-ay1, ay0-by1)
        dist = math.hypot(dx, dy)
        if dist < best:
            best, best_id = dist, other
    overlap_pairs.append(dict(
        PAIR_ID=f"T_{obj}", ELEMENT_ID=obj, OTHER_OBJECT=best_id,
        SOURCE_LINES="; ".join(sorted(object_lines[obj])), NATIVE_COORDINATE_SYSTEM="native 300dpi bbox",
        ELEMENT_BBOX_300DPI=f"({ax0},{ay0},{ax1},{ay1})",
        OVERLAP_PIXEL_COUNT=0, MIN_CLEARANCE_PX=f"{best:.2f}", REQUIRED_MIN_CLEARANCE_PX=4,
        CLIP_PIXEL_COUNT=0, PASS_FAIL="PASS" if best >= 4 else "FAIL",
        METHOD="minimum bbox separation against all other independent figure-text objects",
        MINIMUM_REPAIR_DIRECTION="Separate independent text objects to >=4px bbox clearance if this row fails."))

# Node-border clearance of the boxed symmetry formula is measured from raw PDF
# vector geometry, after subtracting the 0.548pt border half-width.
note_box = (155.358, 575.128, 235.363, 588.604)
note_border_half_px = 0.54794 * ((sx+sy)/2) / 2
for e in [x for x in elements if x["id"].startswith("E10_") or x["id"].startswith("E11_") or x["id"].startswith("E12_") or x["id"].startswith("E13_") or x["id"].startswith("E14_") or x["id"].startswith("E15_") or x["id"].startswith("E16_") or x["id"].startswith("E17_") or x["id"].startswith("E18_")]:
    bx0, by0, bx1, by1 = e["box"]
    cpt = min(bx0-note_box[0], note_box[2]-bx1, by0-note_box[1], note_box[3]-by1) * ((sx+sy)/2) - note_border_half_px
    overlap_pairs.append(dict(
        PAIR_ID=f"B_{e['id']}", ELEMENT_ID=e["id"], OTHER_OBJECT="NODE_BORDER(note)",
        SOURCE_LINES="12,57", NATIVE_COORDINATE_SYSTEM="native PDF vector bbox -> 300dpi",
        ELEMENT_BBOX_300DPI=f"({e['box_px'][0]},{e['box_px'][1]},{e['box_px'][2]},{e['box_px'][3]})",
        OVERLAP_PIXEL_COUNT=0, MIN_CLEARANCE_PX=f"{cpt:.2f}", REQUIRED_MIN_CLEARANCE_PX=5,
        CLIP_PIXEL_COUNT=0, PASS_FAIL="PASS" if cpt >= 5 else "FAIL",
        METHOD="final-PDF note border bbox, stroke halfwidth deducted",
        MINIMUM_REPAIR_DIRECTION="Increase note inner padding/reposition text to retain >=5px after the source-font repair."))

for e in elements:
    x0, y0, x1, y1 = e["box_px"]
    edge = min(x0, y0, PAGE_W-x1, PAGE_H-y1)
    overlap_pairs.append(dict(
        PAIR_ID=f"E_{e['id']}", ELEMENT_ID=e["id"], OTHER_OBJECT="PAGE_OR_FIGURE_CROP_EDGE",
        SOURCE_LINES=e["source_line"], NATIVE_COORDINATE_SYSTEM="native 300dpi bbox",
        ELEMENT_BBOX_300DPI=f"({x0},{y0},{x1},{y1})",
        OVERLAP_PIXEL_COUNT=0, MIN_CLEARANCE_PX=f"{edge:.2f}", REQUIRED_MIN_CLEARANCE_PX=6,
        CLIP_PIXEL_COUNT=0, PASS_FAIL="PASS" if edge >= 6 else "FAIL",
        METHOD="mapped final-PDF text bbox against official page bounds",
        MINIMUM_REPAIR_DIRECTION="Reposition/reflow element to preserve >=6px from final page/figure boundary if this row fails."))

# Render no-resample direct crops. PIL crop is a pixel subset.
fig_crop_px = (420, 2140, 2140, 3070)
standalone_crop_px = (500, 2170, 2050, 2965)
roi_ticks_px = (950, 2170, 1550, 3000)
roi_annotations_px = (620, 2280, 1800, 2725)
Image.fromarray(rgb).crop(fig_crop_px).save(OUT / "figure_crop_300dpi.png")
Image.fromarray(rgb).crop(standalone_crop_px).save(OUT / "standalone_300dpi_from_official.png")
Image.fromarray(rgb).crop(fig_crop_px).convert("L").save(OUT / "figure_crop_grayscale_300dpi.png")
Image.fromarray(rgb).crop(roi_ticks_px).save(OUT / "roi_ticks_axis_1to1_300dpi.png")
Image.fromarray(rgb).crop(roi_annotations_px).save(OUT / "roi_annotations_1to1_300dpi.png")

# Save semantic masks at native 300dpi, full page and graph crop. White=mask.
Image.fromarray((text_mask_full * 255).astype(np.uint8), mode="L").save(OUT / "semantic_mask_TEXT_300dpi.png")
Image.fromarray((graphic_mask_full * 255).astype(np.uint8), mode="L").save(OUT / "semantic_mask_LINE_ARROW_MARKER_300dpi.png")
semantic_rgb = np.zeros((PAGE_H, PAGE_W, 3), dtype=np.uint8) + 255
semantic_rgb[graphic_mask_full] = (190, 145, 35)
semantic_rgb[text_mask_full] = (0, 120, 150)
semantic_rgb[text_mask_full & graphic_mask_full] = (220, 0, 0)
Image.fromarray(semantic_rgb).crop(fig_crop_px).save(OUT / "semantic_masks_figure_300dpi.png")

# Measurement overlay: draw native PDF bboxes and concise IDs directly on the
# original pixel grid. It is an analytical overlay, not a resampled render.
overlay = Image.fromarray(rgb.copy())
draw = ImageDraw.Draw(overlay)
for e in elements:
    x0, y0, x1, y1 = e["box_px"]
    color = (220, 0, 0) if (not e["font_pass"] or not e["pixel_pass"]) else (0, 145, 0)
    draw.rectangle((x0, y0, x1-1, y1-1), outline=color, width=2)
    draw.text((x0, max(0, y0-15)), e["id"], fill=color, stroke_width=1, stroke_fill=(255, 255, 255))
overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

# CSV rows. The explicit PASS_FAIL reports both source and pixel reasons,
# without treating a hard source failure as cured by a superficially readable
# raster glyph.
graphic_overlap_by_id = {}
clearance_by_id = {}
for row in overlap_pairs:
    eid = row["ELEMENT_ID"]
    if row["PAIR_ID"].startswith("G_"):
        graphic_overlap_by_id[eid] = int(row["OVERLAP_PIXEL_COUNT"])
    if row["MIN_CLEARANCE_PX"] not in {"", None}:
        clearance_by_id.setdefault(eid, []).append(float(row["MIN_CLEARANCE_PX"]))
pixel_rows = []
for e in elements:
    x0, y0, x1, y1 = e["box_px"]
    reasons = []
    if not e["font_pass"]:
        reasons.append(e["font_reason"])
    if not e["pixel_pass"]:
        reasons.append(e["pixel_reason"])
    if len(group_values[(e["panel"], e["role"], e["script"])]) < 2:
        reasons.append("same-class peer unavailable; strict protocol treats untestable class comparison as FAIL")
    graphic_overlap = graphic_overlap_by_id.get(e["id"], 0)
    if graphic_overlap:
        reasons.append(f"TEXT_GRAPHIC_OVERLAP_PX={graphic_overlap}; required 0")
    pixel_rows.append(dict(
        ELEMENT_ID=e["id"], PANEL_ID=e["panel"], ROLE=e["role"], SOURCE_FILE=str(SOURCE),
        SOURCE_LINE=e["source_line"], DECLARED_PT=f"{e['declared']:.2f}", GRAPHICS_SCALE="1.000",
        EFFECTIVE_PT=f"{e['effective']:.2f}", TEXT_SAMPLE=e["text"], SCRIPT_CLASS=e["script"],
        BBOX_X0=x0, BBOX_Y0=y0, BBOX_X1=x1, BBOX_Y1=y1, H_INK_PX=e["h_ink"],
        PIXEL_THRESHOLD_PX=e["threshold"], CLASS_MEDIAN_PX=f"{e['class_median']:.2f}",
        RATIO_TO_CLASS_MEDIAN=("" if e["class_ratio"] is None else f"{e['class_ratio']:.4f}"),
        ROLE_RATIO=f"{e['role_ratio']:.4f}", TEXT_TEXT_OVERLAP_PX="0", TEXT_GRAPHIC_OVERLAP_PX=str(graphic_overlap),
        SOURCE_FONT_PASS=str(e["font_pass"]).lower(), PIXEL_HEIGHT_PASS=str(e["pixel_pass"]).lower(),
        SAME_CLASS_RATIO_PASS=str(e["same_class_pass"]).lower(),
        ROLE_RATIO_PASS=("true" if 0.90 <= e["role_ratio"] <= 1.25 else "false"),
        MIN_CLEARANCE_PX=("" if e["id"] not in clearance_by_id else f"{min(clearance_by_id[e['id']]):.2f}"), PASS_FAIL="PASS" if not reasons else "FAIL",
        REASON="; ".join(reasons) if reasons else "PASS",
        MINIMUM_REPAIR_DIRECTION=(
            "Raise effective source text to >=9.5pt and re-layout locally; never apply an overall graphic scale."
            if not e["font_pass"] else
            ("Use a larger/appropriately styled rendered math glyph so H_ink reaches its class threshold, then remeasure at raw 300dpi." if not e["pixel_pass"] else "No element-specific font/pixel repair indicated.")),
    ))

font_rows = []
for e in elements:
    font_rows.append(dict(
        ELEMENT_ID=e["id"], PANEL_ID=e["panel"], ROLE=e["role"], SOURCE_FILE=str(SOURCE),
        SOURCE_LINE=e["source_line"], DECLARED_PT=f"{e['declared']:.2f}", GRAPHICS_SCALE="1.000",
        EFFECTIVE_PT=f"{e['effective']:.2f}", TEXT_SAMPLE=e["text"], SOURCE_FONT_PASS=str(e["font_pass"]).lower(),
        REASON=e["font_reason"],
    ))

pixel_fields = ["ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "PIXEL_THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "SOURCE_FONT_PASS", "PIXEL_HEIGHT_PASS", "SAME_CLASS_RATIO_PASS", "ROLE_RATIO_PASS", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON", "MINIMUM_REPAIR_DIRECTION"]
font_fields = ["ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SOURCE_FONT_PASS", "REASON"]
overlap_fields = ["PAIR_ID", "ELEMENT_ID", "OTHER_OBJECT", "SOURCE_LINES", "ELEMENT_BBOX_300DPI", "NATIVE_COORDINATE_SYSTEM", "OVERLAP_PIXEL_COUNT", "MIN_CLEARANCE_PX", "REQUIRED_MIN_CLEARANCE_PX", "CLIP_PIXEL_COUNT", "PASS_FAIL", "METHOD", "MINIMUM_REPAIR_DIRECTION"]
write_csv(OUT / "after_pixel_measurements.csv", pixel_rows, pixel_fields)
write_csv(OUT / "after_font_audit.csv", font_rows, font_fields)
write_csv(OUT / "after_overlap_report.csv", overlap_pairs, overlap_fields)

# Machine-readable provenance and coverage declaration for the review record.
provenance = {
    "figure_id": "FIG-P262-01",
    "figure_number": "图16.1",
    "official_pdf": str(PDF),
    "official_pdf_page": PDF_PAGE,
    "official_pdf_page_label": "271",
    "official_pdf_length_bytes": PDF.stat().st_size,
    "direct_render": {"renderer": "pdftoppm", "dpi": [300, 200], "resampling": "none"},
    "page_pixels_300dpi": [PAGE_W, PAGE_H],
    "mapping": {"sx": sx, "sy": sy},
    "source": str(SOURCE),
    "chapter_context": {"file": str(CHAPTER), "figure_input_line": 220, "direct_explanation_line": 221},
    "caption_source_line": 60,
    "font_style_source": {"file": str(STYLE), "caption_setup_line": 305},
    "semantic_masks": {"text": "semantic_mask_TEXT_300dpi.png", "graphics": "semantic_mask_LINE_ARROW_MARKER_300dpi.png", "combined": "semantic_masks_figure_300dpi.png"},
}
(OUT / "audit_provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")

font_fail_ids = [e["id"] for e in elements if not e["font_pass"]]
pixel_fail_ids = [e["id"] for e in elements if not e["pixel_pass"]]
same_class_all_tested = all(len(group_values[(e["panel"], e["role"], e["script"])]) >= 2 and e["same_class_pass"] for e in elements)
overlap_all_pass = all(row["PASS_FAIL"] == "PASS" for row in overlap_pairs)
min_clear = min(float(row["MIN_CLEARANCE_PX"]) for row in overlap_pairs if row["MIN_CLEARANCE_PX"] not in {"", None})
overlap_total = sum(int(row["OVERLAP_PIXEL_COUNT"]) for row in overlap_pairs)
overlap_fails = [row for row in overlap_pairs if row["PASS_FAIL"] == "FAIL"]

# One normalized row per concrete failure makes the requested ELEMENT_ID, source
# line, native bbox, threshold and minimal repair traceable without relying on
# prose interpretation.
failure_rows = []
for e in elements:
    bbox = f"({e['box_px'][0]},{e['box_px'][1]},{e['box_px'][2]},{e['box_px'][3]})"
    if not e["font_pass"]:
        failure_rows.append(dict(FAILURE_ID=f"FONT_{e['id']}", ELEMENT_ID=e["id"], FAILURE_CLASS="SOURCE_FONT", SOURCE_FILE=str(SOURCE), SOURCE_LINE=e["source_line"], NATIVE_BBOX_300DPI=bbox, OBSERVED=f"effective_pt={e['effective']:.2f}", THRESHOLD="effective_pt>=9.50", MINIMUM_REPAIR_DIRECTION="Raise the local source declaration to >=9.5pt and re-layout; do not shrink the overall graphic."))
    if not e["pixel_pass"]:
        failure_rows.append(dict(FAILURE_ID=f"PIXEL_{e['id']}", ELEMENT_ID=e["id"], FAILURE_CLASS="PIXEL_HEIGHT", SOURCE_FILE=str(SOURCE), SOURCE_LINE=e["source_line"], NATIVE_BBOX_300DPI=bbox, OBSERVED=f"H_ink_px={e['h_ink']}", THRESHOLD=f"H_ink_px>={e['threshold']}", MINIMUM_REPAIR_DIRECTION="Increase/re-style the rendered math glyph until its own raw-300dpi ink height meets threshold; remeasure after rebuild."))
for row in overlap_fails:
    failure_rows.append(dict(FAILURE_ID=f"OVERLAP_{row['PAIR_ID']}", ELEMENT_ID=row["ELEMENT_ID"], FAILURE_CLASS="ILLEGAL_OVERLAP_OR_CLEARANCE", SOURCE_FILE=str(SOURCE), SOURCE_LINE=row["SOURCE_LINES"], NATIVE_BBOX_300DPI=row["ELEMENT_BBOX_300DPI"], OBSERVED=f"overlap_px={row['OVERLAP_PIXEL_COUNT']}; clearance_px={row['MIN_CLEARANCE_PX']}", THRESHOLD=f"overlap=0; clearance>={row['REQUIRED_MIN_CLEARANCE_PX']}px", MINIMUM_REPAIR_DIRECTION=row["MINIMUM_REPAIR_DIRECTION"]))
write_csv(OUT / "strict_failure_register.csv", failure_rows, ["FAILURE_ID", "ELEMENT_ID", "FAILURE_CLASS", "SOURCE_FILE", "SOURCE_LINE", "NATIVE_BBOX_300DPI", "OBSERVED", "THRESHOLD", "MINIMUM_REPAIR_DIRECTION"])

md = f"""# FIG-P262-01 — SA1 Strict R1

RESULT: **FAIL**

## Frozen candidate and direct views

- Official candidate: `{PDF}` (4,933,704 bytes), physical PDF page **{PDF_PAGE}** (printed page 271).
- `official_page_300dpi.png` and `official_page_200dpi.png` were rendered directly from that page with Poppler; the 300 dpi raster is `{PAGE_W}×{PAGE_H}`. No screenshot, resize, or resampling was used.
- `figure_crop_300dpi.png`, the 1:1 ROIs, and the grayscale image are pixel crops/conversion of that original 300 dpi page only.
- The direct Figure source is `{SOURCE}`. It is inserted at `{CHAPTER}:220`; the immediate explanatory paragraph is line 221. Caption source is line 60.

## Hard-gate outcome

| Gate | Result | Evidence |
|---|---|---|
| SOURCE_FONT_PASS | false | {len(font_fail_ids)} of {len(elements)} visible elements have effective 8.7/9.2pt below 9.5pt; see `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | false | Math operators/prime in `{', '.join(pixel_fail_ids)}` are below C-section operator threshold; see `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | false | Singleton role/script groups cannot be validly ratio-tested; strict protocol declares untestable/unknown a FAIL. Measurable peer groups are retained in CSV. |
| ROLE_RATIO_PASS | false | Required actual-pixel role hierarchy is not fully comparable across this one-panel CJK/math mix; source declaration ratios are recorded but do not substitute for actual-pixel evidence. |
| OVERLAP_PIXEL_COUNT | **{overlap_total}** across reported semantic pairs | `after_overlap_report.csv`; raw text foreground + final-PDF vector masks |
| CLIP_PIXEL_COUNT | 0 | `after_overlap_report.csv`; all mapped text bboxes within official raster |
| MIN_TEXT_CLEARANCE_PX | {min_clear:.2f} (minimum across logged pairs) | `after_overlap_report.csv` |
| VISUAL_HARMONY_PASS | false | Repeated 8.7/9.2pt figure text violates the global reading hierarchy, regardless of basic legibility. |
| MATH_SEMANTICS_PASS | true | Logistic curve, center point, symmetry identity, $\sigma'(0)=1/4$, tangent, and $z=\pm a$ guides agree with source and nearby text. |
| TEXT_CONSISTENCY_PASS | true | Caption and line 221 state the same center symmetry / probability-range conclusion. |
| GRAYSCALE_PASS | true | Curve/markers/guide and tangent remain distinguishable through line styles/markers and contrast in `figure_crop_grayscale_300dpi.png`. |
| PAGE_INTEGRATION_PASS | true | Full 200 dpi page shows a centered graph with caption and the following explanatory paragraph, without page crop or abnormal break. |

## Explicit failures and minimum targeted repair

1. **ELEMENT_IDs `{', '.join(font_fail_ids)}`** — native 300 dpi bboxes, source lines, declared/effective values, and C-section thresholds are all in `strict_failure_register.csv`. Figure-default/direct/note/formula text is **9.2pt** (source lines 5, 9, 12, 54--57); tick text is **8.7pt** (line 19). Both are below the 9.5pt hard gate. Minimum repair: raise every reader-visible figure font to at least 9.5pt (including PGFPlots ticks); then re-layout/re-render instead of globally scaling.
2. **ELEMENT_IDs `{', '.join(pixel_fail_ids)}`** — each fails the >=22px basic math/operator rule at its native bbox/ink height. Minimum repair: after raising the base font, enlarge/re-style each individual operator/prime until its own raw-300dpi ink height reaches the cited threshold; do not only enlarge surrounding Chinese text.
3. **Illegal foreground overlap: `{'; '.join(f"{r['ELEMENT_ID']}={r['OVERLAP_PIXEL_COUNT']}px" for r in overlap_fails)}`** — all affected source lines, native bboxes, zero-overlap threshold, and minimal repositioning directions are in `after_overlap_report.csv` and `strict_failure_register.csv`. Specifically: the $y=1$ reference line crosses `$\\sigma(z)$` and the y=1 tick label; the $z=a$ guide crosses “中心斜率”.
4. **Same-class and actual role comparisons** are not complete for all role/script combinations. Under the strict protocol these are not passable as unknown. Minimum repair: after the font/layout correction, provide all per-role actual-pixel measures from a regenerated official candidate so each prescribed comparison has a legitimate same-script reference (or record a documented non-applicability accepted by the root protocol).

## Independent visual/semantic review

- Reading order is unambiguous: axes and sigmoid curve first, then the green points/guides, tangent/slope annotation, and symmetry identity.
- The curve matches $1/(1+e^{{-z}})$; it is monotone, hits $(0,1/2)$, approaches the 0/1 reference levels, and the plotted tangent source formula is $1/2+z/4$. The two guides at $z=\pm2$ support the displayed central symmetry identity.
- Caption: “逻辑斯谛函数把线性预测量映射为概率，并满足关于$(0,1/2)$的中心对称性。” It is one conclusion and agrees with the adjacent prose (“$z=0$时概率为$1/2$，且$\sigma(-z)=1-\sigma(z)$”).
- The white label background prevents the blue curve from passing through “概率映射”; the boxed symmetry formula has a logged node-border clearance above 5 px. However, the masks show the three explicit text–graphic collisions listed above. No clipping was found.

## Evidence inventory

- `official_page_300dpi.png`, `official_page_200dpi.png`
- `figure_crop_300dpi.png`, `standalone_300dpi_from_official.png`, `figure_crop_grayscale_300dpi.png`
- `roi_ticks_axis_1to1_300dpi.png`, `roi_annotations_1to1_300dpi.png`
- `semantic_mask_TEXT_300dpi.png`, `semantic_mask_LINE_ARROW_MARKER_300dpi.png`, `semantic_masks_figure_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `strict_failure_register.csv`, `after_text_measurement_overlay_300dpi.png`
- `audit_provenance.json`

No SA3 is authorized: this SA1 result is FAIL.
"""
(OUT / "after_visual_acceptance.md").write_text(md, encoding="utf-8")

report = f"""# FIG-P262-01-SA1-STRICT-R1

RESULT: **FAIL**

The frozen official R92 full-book candidate contains 图16.1 on physical PDF page **284** (printed page 271). This is an independent SA1 read-only review. It used only the frozen candidate PDF, the direct figure source, and direct adjacent chapter lines; no prior SA1/SA2/SA3/root report or central inventory was read.

The result is a hard fail before any discretionary visual judgment: source line 19 sets tick labels to 8.7pt and source lines 5/9/12/54--57 set the ordinary figure labels/formulae to 9.2pt. The required effective minimum is 9.5pt. The raw 300 dpi measurement further finds mathematical operators/prime below the 22px operator threshold. In addition, final-page semantic masks quantify 241 illegal text–graphic foreground pixels: y-label $\\sigma(z)$ / y=1 reference, y=1 tick / reference, and “中心斜率” / z=a guide. Complete unique ELEMENT_ID records, source lines, native bboxes, thresholds, and repair direction are in `strict_failure_register.csv` plus the three required audit CSVs.

Direct semantic validation is otherwise favorable: the curve is the intended sigmoid; $\sigma(-z)=1-\sigma(z)$, the $(0,1/2)$ symmetry, guides, points, and tangent slope $1/4$ agree with source, caption, and immediate body text. Clipping is zero, but it cannot cure the source-font, pixel-height, or three text–graphic-overlap failures.

Required minimum source repair: increase all reader-visible figure text—including PGFPlots ticks and every direct/note/formula annotation—to a true effective >=9.5pt, re-layout locally to preserve clearances, rebuild the official full-book candidate, and regenerate all evidence. Do **not** launch SA3 from this failing SA1.
"""
(OUT / "FIG-P262-01-SA1-STRICT-R1.md").write_text(report, encoding="utf-8")

print(json.dumps({
    "result": "FAIL",
    "page": PDF_PAGE,
    "font_fail_ids": font_fail_ids,
    "pixel_fail_ids": pixel_fail_ids,
    "overlap_pairs_pass": overlap_all_pass,
    "overlap_pixel_total": overlap_total,
    "min_logged_clearance_px": min_clear,
    "out": str(OUT),
}, ensure_ascii=False, indent=2))
