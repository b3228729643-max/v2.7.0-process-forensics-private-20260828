"""Generate isolated R1 evidence for FIG-P222-01 from official R91 assets.

All outputs are derived in-place from the official 300 dpi page render.  The
script never writes to the LaTeX source tree.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "official_page_240_300dpi.png"
STANDALONE_PAGE = ROOT / "standalone_page_300dpi_raw.png"
SCALE = 300.0 / 72.0  # PDF point -> raster px for Poppler's 300 dpi render
CROP = (550, 1400, 2000, 2150)  # x0, y0, x1, y1; crop only, never resize
SOURCE_FIG = "src/绘图源码/第02册_基础监督学习方法/V2-C03/fig_v2_c03_star.tex"
SOURCE_STYLE = "src/讲义源码/common/statlearnbook.sty"


def px_box(pt_box):
    x0, y0, x1, y1 = pt_box
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


# Word-/glyph-level PDF vector bboxes are from official_page_240_text_bboxes.html.
# Split natural scripts from their base formulas so small semantic subparts are not
# hidden by a taller adjacent glyph.
E = [
    dict(id="T01_CATEGORY", panel="P1", role="ANNOTATION", source_line="8", declared=9.20, effective=9.20, text="类别变量", cls="CJK", bbox=(284.976,343.956496,321.638520,353.772886), threshold=30, parent="L01_CATEGORY"),
    dict(id="T02_Y_NODE", panel="P1", role="NODE_LABEL", source_line="17", declared=9.20, effective=9.20, text="Y", cls="MATH_BASE", bbox=(299.735,368.692468,305.782322,378.655108), threshold=22, parent="L02_Y_NODE"),
    dict(id="T03_X1_BASE", panel="P1", role="NODE_LABEL", source_line="19", declared=9.20, effective=9.20, text="X", cls="MATH_BASE", bbox=(198.440,431.314468,204.786202,441.277108), threshold=22, parent="L03_X1"),
    dict(id="T04_X1_SUB", panel="P1", role="NATURAL_SUBSCRIPT", source_line="19", declared=9.20, effective=6.67, text="1", cls="NATURAL_SCRIPT", bbox=(204.786,434.388618,209.349887,443.354998), threshold=15, parent="L03_X1"),
    dict(id="T05_X2_BASE", panel="P1", role="NODE_LABEL", source_line="20", declared=9.20, effective=9.20, text="X", cls="MATH_BASE", bbox=(247.979,431.297468,254.325202,441.260108), threshold=22, parent="L04_X2"),
    dict(id="T06_X2_SUB", panel="P1", role="NATURAL_SUBSCRIPT", source_line="20", declared=9.20, effective=6.67, text="2", cls="NATURAL_SCRIPT", bbox=(254.325,434.406618,259.023383,443.372998), threshold=15, parent="L04_X2"),
    dict(id="T07_ELLIPSIS", panel="P1", role="MATH_OPERATOR", source_line="21", declared=9.20, effective=9.20, text="⋯", cls="MATH_BASE", bbox=(298.560,430.783468,308.054396,440.746108), threshold=22, parent="L05_ELLIPSIS"),
    dict(id="T08_XDM1_BASE", panel="P1", role="NODE_LABEL", source_line="22", declared=9.20, effective=9.20, text="X", cls="MATH_BASE", bbox=(340.983,430.898468,347.329202,440.861108), threshold=22, parent="L06_XD_MINUS_1"),
    dict(id="T09_XDM1_SUB", panel="P1", role="NATURAL_SUBSCRIPT", source_line="22", declared=9.20, effective=6.67, text="d−1", cls="NATURAL_SCRIPT", bbox=(347.329,434.679618,364.445819,443.645998), threshold=15, parent="L06_XD_MINUS_1"),
    dict(id="T10_XD_BASE", panel="P1", role="NODE_LABEL", source_line="23", declared=9.20, effective=9.20, text="X", cls="MATH_BASE", bbox=(396.332,430.898468,402.678202,440.861108), threshold=22, parent="L07_XD"),
    dict(id="T11_XD_SUB", panel="P1", role="NATURAL_SUBSCRIPT", source_line="23", declared=9.20, effective=6.67, text="d", cls="NATURAL_SCRIPT", bbox=(402.678,434.679618,408.129559,443.645998), threshold=15, parent="L07_XD"),
    dict(id="T12_REGION_CJK", panel="P1", role="ANNOTATION", source_line="32", declared=9.20, effective=9.20, text="给定…后相互独立", cls="CJK", bbox=(265.206,449.382496,341.408150,459.198886), threshold=30, parent="L08_REGION_LABEL"),
    dict(id="T13_REGION_Y", panel="P1", role="ANNOTATION", source_line="32", declared=9.20, effective=9.20, text="Y", cls="MATH_BASE", bbox=(285.691,449.730790,292.418572,458.896420), threshold=22, parent="L08_REGION_LABEL"),
    dict(id="T14_FORMULA_XI", panel="P1", role="FORMULA_BASE", source_line="34", declared=9.20, effective=9.20, text="X", cls="MATH_BASE", bbox=(260.925,478.137790,268.028363,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T15_FORMULA_I", panel="P1", role="NATURAL_SUBSCRIPT", source_line="34", declared=9.20, effective=6.67, text="i", cls="NATURAL_SCRIPT", bbox=(268.028,482.158084,270.363388,488.573984), threshold=15, parent="L09_FORMULA"),
    dict(id="T16_FORMULA_PERP", panel="P1", role="FORMULA_OPERATOR", source_line="34", declared=9.20, effective=9.20, text="⊥", cls="MATH_BASE", bbox=(273.468,478.137790,279.966432,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T17_FORMULA_XJ", panel="P1", role="FORMULA_BASE", source_line="34", declared=9.20, effective=9.20, text="X", cls="MATH_BASE", bbox=(282.505311,478.137790,289.608674,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T18_FORMULA_J", panel="P1", role="NATURAL_SUBSCRIPT", source_line="34", declared=9.20, effective=6.67, text="j", cls="NATURAL_SCRIPT", bbox=(289.616,482.158084,292.830366,488.573984), threshold=15, parent="L09_FORMULA"),
    dict(id="T19_FORMULA_MID", panel="P1", role="FORMULA_OPERATOR", source_line="34", declared=9.20, effective=9.20, text="∣", cls="MATH_BASE", bbox=(296.064,478.137790,298.557051,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T20_FORMULA_Y", panel="P1", role="FORMULA_BASE", source_line="34", declared=9.20, effective=9.20, text="Y", cls="MATH_BASE", bbox=(301.095931,478.137790,307.823503,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T21_FORMULA_I_PAREN", panel="P1", role="FORMULA_BASE", source_line="34", declared=9.20, effective=9.20, text="(i", cls="MATH_BASE", bbox=(317.997353,478.137790,324.807416,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T22_FORMULA_NEQ", panel="P1", role="FORMULA_OPERATOR", source_line="34", declared=9.20, effective=9.20, text="≠", cls="MATH_BASE", bbox=(327.538773,478.137790,334.614640,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T23_FORMULA_J_PAREN", panel="P1", role="FORMULA_BASE", source_line="34", declared=9.20, effective=9.20, text="j)", cls="MATH_BASE", bbox=(337.162685,478.137790,345.686721,487.303420), threshold=22, parent="L09_FORMULA"),
    dict(id="T24_CAPTION_LABEL", panel="CAPTION", role="CAPTION_LABEL", source_line="36; statlearnbook.sty:305", declared=10.00, effective=10.00, text="图", cls="CJK", bbox=(147.825,496.173338,157.787640,510.599240), threshold=30, parent="L10_CAPTION"),
    dict(id="T25_CAPTION_NUMBER", panel="CAPTION", role="CAPTION_LABEL", source_line="36; statlearnbook.sty:305", declared=10.00, effective=10.00, text="14.1", cls="UPPER_OR_DIGIT", bbox=(160.129,500.138468,177.673209,510.101108), threshold=24, parent="L10_CAPTION"),
    dict(id="T26_CAPTION_CJK_L", panel="CAPTION", role="CAPTION_TEXT", source_line="36; statlearnbook.sty:305", declared=10.00, effective=10.00, text="朴素贝叶斯的条件依赖结构：给定", cls="CJK", bbox=(187.636,499.759888,337.075600,510.429875), threshold=30, parent="L10_CAPTION"),
    dict(id="T27_CAPTION_Y", panel="CAPTION", role="CAPTION_TEXT", source_line="36; statlearnbook.sty:305", declared=10.00, effective=10.00, text="Y", cls="MATH_BASE", bbox=(339.566,500.138468,345.613322,510.101108), threshold=22, parent="L10_CAPTION"),
    dict(id="T28_CAPTION_CJK_R", panel="CAPTION", role="CAPTION_TEXT", source_line="36; statlearnbook.sty:305", declared=10.00, effective=10.00, text="后，各特征节点相互独立", cls="CJK", bbox=(349.200,499.759888,458.789040,510.429875), threshold=30, parent="L10_CAPTION"),
]


def dominant_bg(rgb):
    colors, counts = np.unique(rgb.reshape(-1, 3), axis=0, return_counts=True)
    return colors[np.argmax(counts)]


def mask_in_box(arr, box, ink_kind, bg_override=None):
    x0, y0, x1, y1 = box
    patch = arr[y0:y1, x0:x1]
    bg = np.array(bg_override, dtype=np.uint8) if bg_override is not None else dominant_bg(patch)
    diff = np.abs(patch.astype(np.int16) - bg.astype(np.int16))
    delta = np.max(diff, axis=2)
    r = patch[:, :, 0].astype(np.int16)
    g = patch[:, :, 1].astype(np.int16)
    b = patch[:, :, 2].astype(np.int16)
    # The published PDF uses exact black, blue and teal ink.  Restricting each
    # element to its expected hue prevents a node/panel border from inflating a
    # nearby text bbox while still retaining antialiased text pixels above C1.
    if ink_kind == "blue":
        hue_ok = (b - g >= 15) & (b - r >= 30)
    elif ink_kind == "teal":
        hue_ok = (g - r >= 25) & (np.abs(b - g) <= 45)
    else:  # black mathematical/caption ink
        # Black antialiasing changes all channels by almost the same amount;
        # the blue node outline changes them very unevenly.  This retains only
        # C1-valid neutral/dark foreground and excludes the nearby blue ring.
        hue_ok = np.min(diff, axis=2) >= 0.78 * np.maximum(delta, 1)
    return (delta >= 20) & hue_ok, tuple(int(v) for v in bg)


def near_color(arr, color, tolerance=24):
    delta = arr.astype(np.int32) - np.array(color, dtype=np.int32)
    d = np.sqrt(np.sum(delta * delta, axis=2))
    return d <= tolerance


def segment_band(mask, p0, p1, half_width):
    yy, xx = np.indices(mask.shape)
    x0, y0 = p0
    x1, y1 = p1
    vx, vy = x1 - x0, y1 - y0
    denom = vx * vx + vy * vy
    t = np.clip(((xx - x0) * vx + (yy - y0) * vy) / denom, 0.0, 1.0)
    dx = xx - (x0 + t * vx)
    dy = yy - (y0 + t * vy)
    return np.hypot(dx, dy) <= half_width


def rect_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def mask_distance(a, b):
    if not a.any() or not b.any():
        return None
    overlap = int(np.logical_and(a, b).sum())
    if overlap:
        return overlap, 0.0
    d = ndimage.distance_transform_edt(~b)
    return 0, float(d[a].min())


def union_bbox(boxes):
    return (
        min(b[0] for b in boxes), min(b[1] for b in boxes),
        max(b[2] for b in boxes), max(b[3] for b in boxes),
    )


def bbox_of_mask(mask):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return "N/A"
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def save_mask(mask, path):
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def main():
    arr = np.array(Image.open(PAGE).convert("RGB"))
    h, w = arr.shape[:2]
    assert (w, h) == (2481, 3508), (w, h)

    # Original-pixel crops: PIL crop does not resample.
    x0, y0, x1, y1 = CROP
    page_img = Image.fromarray(arr)
    page_img.crop(CROP).save(ROOT / "after_figure_crop_300dpi.png")
    page_img.crop(CROP).convert("L").save(ROOT / "after_grayscale_300dpi.png")
    page_img.crop((1120, 1385, 1400, 1650)).save(ROOT / "roi_top_node_1to1_300dpi.png")
    page_img.crop((760, 1650, 1775, 1965)).save(ROOT / "roi_feature_nodes_1to1_300dpi.png")
    page_img.crop((1000, 1840, 1510, 2150)).save(ROOT / "roi_region_formula_caption_1to1_300dpi.png")

    # Standalone source compiled without editing source, then cropped without resize.
    standalone = Image.open(STANDALONE_PAGE).convert("RGB")
    # content extent found from non-white pixels after rendering at the same 300 dpi.
    sa = np.array(standalone)
    nonwhite = np.any(sa < 250, axis=2)
    ys, xs = np.where(nonwhite)
    sa_box = (int(xs.min()) - 16, int(ys.min()) - 16, int(xs.max()) + 17, int(ys.max()) + 17)
    standalone.crop(sa_box).save(ROOT / "after_standalone_300dpi.png")

    # Element foreground masks measured in the final official PDF page only.
    text_mask = np.zeros((h, w), dtype=bool)
    by_parent = defaultdict(list)
    for item in E:
        box = px_box(item["bbox"])
        ink_kind = "blue" if item["id"] == "T01_CATEGORY" else ("teal" if item["id"] in ("T12_REGION_CJK", "T13_REGION_Y") else "black")
        bg_override = (242, 246, 250) if item["id"] in {"T02_Y_NODE", "T03_X1_BASE", "T04_X1_SUB", "T05_X2_BASE", "T06_X2_SUB", "T08_XDM1_BASE", "T09_XDM1_SUB", "T10_XD_BASE", "T11_XD_SUB"} else ((241, 248, 246) if ink_kind == "teal" else None)
        mask, bg = mask_in_box(arr, box, ink_kind, bg_override)
        full = np.zeros((h, w), dtype=bool)
        bx0, by0, bx1, by1 = box
        full[by0:by1, bx0:bx1] = mask
        rows = np.where(mask.any(axis=1))[0]
        if len(rows):
            ink = int(rows.max() - rows.min() + 1)
        else:
            ink = 0
        item["box_px"] = box
        item["mask"] = full
        item["background"] = bg
        item["ink"] = ink
        text_mask |= full
        by_parent[item["parent"]].append(item)

    # Semantic graphic masks. Exact source colors make these semantic separations
    # reproducible from the raw Poppler raster without thresholding page screenshots.
    blue = near_color(arr, (31, 78, 121), tolerance=28)
    teal = near_color(arr, (15, 118, 110), tolerance=30)
    light_border = near_color(arr, (203, 213, 225), tolerance=20)
    centers = [(1262,1557), (850,1819), (1058,1819), (1472,1819), (1680,1819)]
    yy, xx = np.indices((h, w))
    node_border = np.zeros((h, w), dtype=bool)
    node_parts = []
    for cx, cy in centers:
        r = np.hypot(xx-cx, yy-cy)
        part = blue & (r >= 38) & (r <= 51)
        node_parts.append(part)
        node_border |= part
    arrow_parts = []
    for endpoint in centers[1:]:
        arrow_parts.append(blue & segment_band(blue, centers[0], endpoint, 13) & ~node_border & ~text_mask)
    arrow = np.zeros((h, w), dtype=bool)
    for part in arrow_parts:
        arrow |= part
    node_border &= ~text_mask
    node_parts = [part & ~text_mask for part in node_parts]
    lab, nlab = ndimage.label(teal & ~text_mask)
    panel_border = np.zeros((h, w), dtype=bool)
    if nlab:
        counts = np.bincount(lab.ravel())
        for idx in np.argsort(counts)[::-1]:
            if idx and counts[idx] > 250:
                panel_border |= lab == idx
                break
    formula_zone = np.zeros((h, w), dtype=bool)
    formula_zone[1940:2080, 1000:1540] = True
    formula_border = light_border & formula_zone & ~text_mask

    # Keep semantic masks in figure-crop coordinates; no scaling occurs.
    save_mask(text_mask[y0:y1, x0:x1], ROOT / "mask_text_formula_300dpi.png")
    save_mask(arrow[y0:y1, x0:x1], ROOT / "mask_line_arrow_300dpi.png")
    save_mask(node_border[y0:y1, x0:x1], ROOT / "mask_node_border_300dpi.png")
    save_mask(panel_border[y0:y1, x0:x1], ROOT / "mask_panel_border_300dpi.png")
    save_mask(formula_border[y0:y1, x0:x1], ROOT / "mask_formula_box_border_300dpi.png")
    save_mask(np.zeros((y1-y0, x1-x0), dtype=bool), ROOT / "mask_marker_none_300dpi.png")
    save_mask(np.zeros((y1-y0, x1-x0), dtype=bool), ROOT / "mask_data_curve_none_300dpi.png")

    # Complete semantic object inventory, including genuinely absent object types.
    inventory = []
    for item in E:
        obj_class = "FORMULA" if item["role"].startswith("FORMULA") or item["role"] == "MATH_OPERATOR" else "TEXT"
        inventory.append({"OBJECT_ID": item["id"], "PANEL_ID": item["panel"], "CLASS": obj_class, "DESCRIPTION": item["text"], "SOURCE_FILE": SOURCE_FIG if "statlearnbook" not in item["source_line"] else SOURCE_FIG + "; " + SOURCE_STYLE, "SOURCE_LINE": item["source_line"], "NATIVE_BBOX_PX": str(item["box_px"]), "MASK_FILE": "mask_text_formula_300dpi.png", "STATUS": "PRESENT"})
    arrow_desc = ["Y→X_1", "Y→X_2", "Y→X_{d-1}", "Y→X_d"]
    for idx, (desc, part) in enumerate(zip(arrow_desc, arrow_parts), 1):
        inventory.append({"OBJECT_ID": f"AR{idx:02d}", "PANEL_ID": "P1", "CLASS": "LINE_ARROW", "DESCRIPTION": desc, "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": str(23 + idx), "NATIVE_BBOX_PX": str(bbox_of_mask(part)), "MASK_FILE": "mask_line_arrow_300dpi.png", "STATUS": "PRESENT"})
    node_desc = ["Y class node border", "X_1 node border", "X_2 node border", "X_{d-1} node border", "X_d node border"]
    node_lines = ["5--6,17", "5,19", "5,20", "5,22", "5,23"]
    for idx, (desc, line, part) in enumerate(zip(node_desc, node_lines, node_parts), 1):
        inventory.append({"OBJECT_ID": f"NB{idx:02d}", "PANEL_ID": "P1", "CLASS": "NODE_BORDER", "DESCRIPTION": desc, "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": line, "NATIVE_BBOX_PX": str(bbox_of_mask(part)), "MASK_FILE": "mask_node_border_300dpi.png", "STATUS": "PRESENT"})
    inventory.extend([
        {"OBJECT_ID": "PB01", "PANEL_ID": "P1", "CLASS": "PANEL_BORDER", "DESCRIPTION": "feature conditional-independence region", "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": "29--30", "NATIVE_BBOX_PX": str(bbox_of_mask(panel_border)), "MASK_FILE": "mask_panel_border_300dpi.png", "STATUS": "PRESENT"},
        {"OBJECT_ID": "FB01", "PANEL_ID": "P1", "CLASS": "FORMULA_BOX_BORDER", "DESCRIPTION": "conditional-independence formula box", "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": "11--12,33--34", "NATIVE_BBOX_PX": str(bbox_of_mask(formula_border)), "MASK_FILE": "mask_formula_box_border_300dpi.png", "STATUS": "PRESENT"},
        {"OBJECT_ID": "MARKER_NONE", "PANEL_ID": "P1", "CLASS": "MARKER", "DESCRIPTION": "no point/marker object", "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": "17--35", "NATIVE_BBOX_PX": "N/A", "MASK_FILE": "mask_marker_none_300dpi.png", "STATUS": "ABSENT_NOT_UNKNOWN"},
        {"OBJECT_ID": "CURVE_NONE", "PANEL_ID": "P1", "CLASS": "DATA_CURVE", "DESCRIPTION": "no data curve", "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": "17--35", "NATIVE_BBOX_PX": "N/A", "MASK_FILE": "mask_data_curve_none_300dpi.png", "STATUS": "ABSENT_NOT_UNKNOWN"},
        {"OBJECT_ID": "TICK_NONE", "PANEL_ID": "P1", "CLASS": "TICK", "DESCRIPTION": "no axes/ticks", "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": "17--35", "NATIVE_BBOX_PX": "N/A", "MASK_FILE": "N/A", "STATUS": "ABSENT_NOT_UNKNOWN"},
        {"OBJECT_ID": "LEGEND_NONE", "PANEL_ID": "P1", "CLASS": "LEGEND", "DESCRIPTION": "no legend", "SOURCE_FILE": SOURCE_FIG, "SOURCE_LINE": "17--35", "NATIVE_BBOX_PX": "N/A", "MASK_FILE": "N/A", "STATUS": "ABSENT_NOT_UNKNOWN"},
    ])
    with (ROOT / "after_semantic_object_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["OBJECT_ID","PANEL_ID","CLASS","DESCRIPTION","SOURCE_FILE","SOURCE_LINE","NATIVE_BBOX_PX","MASK_FILE","STATUS"]
        wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(inventory)

    # Build parent/layout objects (natural scripts remain one layout object).
    layout = {}
    for parent, members in by_parent.items():
        mask = np.zeros((h, w), dtype=bool)
        for m in members:
            mask |= m["mask"]
        layout[parent] = {
            "mask": mask,
            "bbox": union_bbox([m["box_px"] for m in members]),
            "members": members,
        }

    # Pixel audit metrics and same-class ratios.
    # Ratio groups only contain repeated, directly comparable semantic glyphs.
    # Do not compare an index `i` with a descender-bearing `j`, or an operator
    # with a variable: their different ink anatomy is not a font-scale drift.
    same_group = {
        "T01_CATEGORY": "ANNOTATION_CJK", "T12_REGION_CJK": "ANNOTATION_CJK",
        "T02_Y_NODE": "NODE_LABEL_MATH", "T03_X1_BASE": "NODE_LABEL_MATH",
        "T05_X2_BASE": "NODE_LABEL_MATH", "T08_XDM1_BASE": "NODE_LABEL_MATH", "T10_XD_BASE": "NODE_LABEL_MATH",
        "T04_X1_SUB": "NODE_INDEX_DIGIT", "T06_X2_SUB": "NODE_INDEX_DIGIT",
        "T09_XDM1_SUB": "NODE_INDEX_COMPOSITE", "T11_XD_SUB": "NODE_INDEX_LATIN",
        "T14_FORMULA_XI": "FORMULA_VARIABLE_UPPER", "T17_FORMULA_XJ": "FORMULA_VARIABLE_UPPER", "T20_FORMULA_Y": "FORMULA_VARIABLE_UPPER",
        "T15_FORMULA_I": "FORMULA_INDEX_I", "T18_FORMULA_J": "FORMULA_INDEX_J",
        "T16_FORMULA_PERP": "FORMULA_OPERATOR_PERP", "T19_FORMULA_MID": "FORMULA_OPERATOR_MID", "T22_FORMULA_NEQ": "FORMULA_OPERATOR_NEQ",
        "T21_FORMULA_I_PAREN": "FORMULA_PAREN_I", "T23_FORMULA_J_PAREN": "FORMULA_PAREN_J",
        "T07_ELLIPSIS": "ELLIPSIS", "T13_REGION_Y": "REGION_Y",
        "T24_CAPTION_LABEL": "CAPTION_LABEL", "T25_CAPTION_NUMBER": "CAPTION_NUMBER", "T27_CAPTION_Y": "CAPTION_Y",
        "T26_CAPTION_CJK_L": "CAPTION_CJK_TEXT", "T28_CAPTION_CJK_R": "CAPTION_CJK_TEXT",
    }
    comparable_groups = defaultdict(list)
    for item in E:
        group = same_group[item["id"]]
        item["group"] = group
        comparable_groups[group].append(item)
    for group, items in comparable_groups.items():
        median = float(np.median([i["ink"] for i in items]))
        for item in items:
            item["class_median"] = median
            item["ratio_to_median"] = item["ink"] / median if median else 0.0

    # Role ratio: node-label math is the declared local BASE (no tick role exists).
    base_items = [i for i in E if i["role"] == "NODE_LABEL"]
    base_median = float(np.median([i["ink"] for i in base_items]))
    for item in E:
        item["role_ratio"] = item["ink"] / base_median if base_median else 0.0

    # 9.2.1-E role hierarchy; no tick role exists, so ordinary node math is BASE.
    role_rows = []
    def add_role_check(check_id, element_ids, role, lower, upper):
        members = [next(i for i in E if i["id"] == eid) for eid in element_ids]
        h_med = float(np.median([m["ink"] for m in members]))
        ratio = h_med / base_median
        ok = lower <= ratio <= upper
        role_rows.append({"CHECK_ID": check_id, "ELEMENT_IDS": ";".join(element_ids), "ROLE": role, "BASE_ROLE": "NODE_LABEL_MATH", "BASE_MEDIAN_PX": f"{base_median:.2f}", "ROLE_MEDIAN_PX": f"{h_med:.2f}", "ROLE_RATIO": f"{ratio:.4f}", "ALLOWED_RANGE": f"[{lower:.2f},{upper:.2f}]", "PASS_FAIL": "PASS" if ok else "FAIL", "REASON": "within 9.2.1-E range" if ok else "outside 9.2.1-E range"})
    add_role_check("ROLE_ANNOTATION_CJK", ["T01_CATEGORY", "T12_REGION_CJK"], "ordinary annotation", 0.95, 1.10)
    add_role_check("ROLE_FORMULA_BASE", ["T14_FORMULA_XI", "T17_FORMULA_XJ", "T20_FORMULA_Y"], "formula block baseline", 1.00, 1.18)
    for absent_role in ("axis title/unit", "legend", "panel label"):
        role_rows.append({"CHECK_ID": "ROLE_ABSENT_" + absent_role.replace(" ", "_").replace("/", "_"), "ELEMENT_IDS": "N/A", "ROLE": absent_role, "BASE_ROLE": "NODE_LABEL_MATH", "BASE_MEDIAN_PX": f"{base_median:.2f}", "ROLE_MEDIAN_PX": "N/A", "ROLE_RATIO": "N/A", "ALLOWED_RANGE": "N/A", "PASS_FAIL": "PASS", "REASON": "not present in this figure; not an unknown"})
    with (ROOT / "after_role_ratio_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["CHECK_ID","ELEMENT_IDS","ROLE","BASE_ROLE","BASE_MEDIAN_PX","ROLE_MEDIAN_PX","ROLE_RATIO","ALLOWED_RANGE","PASS_FAIL","REASON"]
        wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(role_rows)

    # Formally fail all direct 9.2pt styles; scripts are only admissible if their
    # parent baseline meets 9.5pt, which it does not in this candidate.
    for item in E:
        if item["role"] == "NATURAL_SUBSCRIPT":
            item["font_pass"] = False
            item["font_reason"] = "natural script is derived from a 9.20pt parent baseline (<9.50pt)"
        else:
            item["font_pass"] = item["effective"] >= 9.5
            item["font_reason"] = "effective_pt >= 9.50" if item["font_pass"] else "effective_pt < 9.50"
        item["pixel_pass"] = item["ink"] >= item["threshold"]

    # Component-level graphic clearances; formula/node label masks are retained.
    graphic_masks = {
        "LINE_ARROW": arrow,
        "NODE_BORDER": node_border,
        "PANEL_BORDER": panel_border,
        "FORMULA_BOX_BORDER": formula_border,
    }
    graphic_distance = {name: ndimage.distance_transform_edt(~mask) for name, mask in graphic_masks.items()}

    # Dedicated native-pixel evidence for the only failed node-label clearance.
    # These files are crops, never rescaled.  The two masks share exactly the
    # same coordinate frame as the raw ROI, so the 4.47 px result is directly
    # reproducible from the official 300 dpi page render.
    xd_roi = (1380, 1740, 1550, 1890)
    xd_text = layout["L06_XD_MINUS_1"]["mask"]
    xd_border = node_parts[3]
    page_img.crop(xd_roi).save(ROOT / "roi_xdminus1_node_border_1to1_300dpi.png")
    save_mask(xd_text[xd_roi[1]:xd_roi[3], xd_roi[0]:xd_roi[2]], ROOT / "mask_xdminus1_text_300dpi.png")
    save_mask(xd_border[xd_roi[1]:xd_roi[3], xd_roi[0]:xd_roi[2]], ROOT / "mask_xdminus1_node_border_300dpi.png")
    xd_dist, xd_nearest = ndimage.distance_transform_edt(~xd_border, return_indices=True)
    xd_points = np.argwhere(xd_text)
    xd_text_point = xd_points[int(np.argmin(xd_dist[xd_text]))]
    xd_border_point = np.array([
        xd_nearest[0][tuple(xd_text_point)],
        xd_nearest[1][tuple(xd_text_point)],
    ])
    xd_clearance = float(xd_dist[tuple(xd_text_point)])
    xd_overlay = np.array(page_img.crop(xd_roi).convert("RGB")).copy()
    local_text = xd_text[xd_roi[1]:xd_roi[3], xd_roi[0]:xd_roi[2]]
    local_border = xd_border[xd_roi[1]:xd_roi[3], xd_roi[0]:xd_roi[2]]
    xd_overlay[local_text] = (235, 45, 45)
    xd_overlay[local_border] = (35, 95, 235)
    xd_overlay_img = Image.fromarray(xd_overlay)
    xd_draw = ImageDraw.Draw(xd_overlay_img)
    p_text = (int(xd_text_point[1] - xd_roi[0]), int(xd_text_point[0] - xd_roi[1]))
    p_border = (int(xd_border_point[1] - xd_roi[0]), int(xd_border_point[0] - xd_roi[1]))
    xd_draw.line([p_text, p_border], fill=(255, 135, 0), width=1)
    xd_draw.ellipse((p_text[0]-2, p_text[1]-2, p_text[0]+2, p_text[1]+2), outline=(255, 135, 0), width=1)
    xd_draw.ellipse((p_border[0]-2, p_border[1]-2, p_border[0]+2, p_border[1]+2), outline=(255, 135, 0), width=1)
    xd_overlay_img.save(ROOT / "overlay_xdminus1_node_border_clearance_300dpi.png")
    (ROOT / "xdminus1_node_border_clearance_native.json").write_text(json.dumps({
        "official_page_render": "official_page_240_300dpi.png",
        "dpi": 300,
        "roi_native_bbox_px": list(xd_roi),
        "text_layout_id": "L06_XD_MINUS_1",
        "source_line": "22",
        "text_native_bbox_px": list(layout["L06_XD_MINUS_1"]["bbox"]),
        "border_object_id": "NB04",
        "minimum_clearance_px": round(xd_clearance, 6),
        "threshold_px": 5,
        "nearest_text_yx_px": [int(xd_text_point[0]), int(xd_text_point[1])],
        "nearest_border_yx_px": [int(xd_border_point[0]), int(xd_border_point[1])],
        "overlap_pixel_count": int(np.logical_and(xd_text, xd_border).sum()),
        "result": "FAIL" if xd_clearance < 5 else "PASS",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    per_item_clearance = {}
    for item in E:
        checks = []
        for gname, gmask in graphic_masks.items():
            overlap = int(np.logical_and(item["mask"], gmask).sum())
            dist = 0.0 if overlap else float(graphic_distance[gname][item["mask"]].min())
            checks.append((gname, overlap, dist))
        per_item_clearance[item["id"]] = min((x[2] for x in checks), default=float("inf"))
        item["text_graphic_overlap"] = sum(x[1] for x in checks)
        item["min_clearance"] = per_item_clearance[item["id"]]

    # Generate native-coordinate overlay after measurements.
    overlay = page_img.crop(CROP).convert("RGB")
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    colors = {"CJK": (210, 40, 40), "MATH_BASE": (40, 90, 220), "NATURAL_SCRIPT": (170, 0, 170), "UPPER_OR_DIGIT": (230, 120, 0)}
    for item in E:
        bx0, by0, bx1, by1 = item["box_px"]
        c = colors[item["cls"]]
        box = (bx0-x0, by0-y0, bx1-x0, by1-y0)
        draw.rectangle(box, outline=c, width=2)
        draw.text((box[0], max(0, box[1]-13)), f"{item['id']} h={item['ink']}", fill=c, font=font)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # Raw crop coordinate and mask provenance record.
    metadata = {
        "official_pdf": "v2.7.0/_work/source/v2.7.0/src/build/strict_current_r91_fullbook/main_full.pdf",
        "official_pdf_physical_page": 240,
        "printed_page": 227,
        "render": {"tool": "pdftoppm", "dpi": 300, "resize_after_render": False, "image_px": [w, h]},
        "figure_crop_px": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
        "coordinate_map": "x_px=floor_or_ceil(x_pdf_pt*300/72); y_px=floor_or_ceil(y_pdf_pt*300/72)",
        "masks": {
            "TEXT_FORMULA": "per-element local-background foreground; abs(channel-background)>=20",
            "LINE_ARROW": "source blue near RGB(31,78,121), segment bands, text and node-border removed",
            "NODE_BORDER": "source blue near RGB(31,78,121), five known node annuli, text removed",
            "PANEL_BORDER": "largest connected teal foreground component after region-label removal",
            "FORMULA_BOX_BORDER": "near RGB(203,213,225) in formula box zone, text removed",
            "MARKER": "none in source",
            "DATA_CURVE": "none in source",
        },
    }
    (ROOT / "native_coordinates_and_mask_method.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    # Font audit CSV.
    font_fields = ["ELEMENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE","DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","TEXT_SAMPLE","SCRIPT_CLASS","PDF_VECTOR_BBOX_PT","NATIVE_BBOX_PX","SOURCE_FONT_THRESHOLD_PT","SOURCE_FONT_PASS","REASON"]
    with (ROOT / "after_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=font_fields)
        wr.writeheader()
        for item in E:
            src = SOURCE_FIG if "statlearnbook" not in item["source_line"] else SOURCE_FIG + "; " + SOURCE_STYLE
            wr.writerow({
                "ELEMENT_ID": item["id"], "PANEL_ID": item["panel"], "ROLE": item["role"],
                "SOURCE_FILE": src, "SOURCE_LINE": item["source_line"],
                "DECLARED_PT": f"{item['declared']:.2f}", "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{item['effective']:.2f}", "TEXT_SAMPLE": item["text"],
                "SCRIPT_CLASS": item["cls"], "PDF_VECTOR_BBOX_PT": "[%.3f,%.3f,%.3f,%.3f]" % item["bbox"],
                "NATIVE_BBOX_PX": str(item["box_px"]), "SOURCE_FONT_THRESHOLD_PT": "9.50 baseline; natural script allowed only from >=9.50 baseline",
                "SOURCE_FONT_PASS": str(item["font_pass"]).lower(), "REASON": item["font_reason"],
            })

    # Pixel audit CSV.
    pix_fields = ["ELEMENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE","DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","TEXT_SAMPLE","SCRIPT_CLASS","BBOX_X0","BBOX_Y0","BBOX_X1","BBOX_Y1","H_INK_PX","CLASS_MEDIAN_PX","RATIO_TO_CLASS_MEDIAN","ROLE_RATIO","TEXT_TEXT_OVERLAP_PX","TEXT_GRAPHIC_OVERLAP_PX","MIN_CLEARANCE_PX","PASS_FAIL","REASON"]
    with (ROOT / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=pix_fields)
        wr.writeheader()
        for item in E:
            bx0, by0, bx1, by1 = item["box_px"]
            p = item["pixel_pass"]
            reason = "H_ink_px >= class threshold" if p else f"H_ink_px={item['ink']} < threshold={item['threshold']}"
            wr.writerow({
                "ELEMENT_ID": item["id"], "PANEL_ID": item["panel"], "ROLE": item["role"],
                "SOURCE_FILE": SOURCE_FIG + ("; " + SOURCE_STYLE if "statlearnbook" in item["source_line"] else ""),
                "SOURCE_LINE": item["source_line"], "DECLARED_PT": f"{item['declared']:.2f}", "GRAPHICS_SCALE": "1.0000", "EFFECTIVE_PT": f"{item['effective']:.2f}",
                "TEXT_SAMPLE": item["text"], "SCRIPT_CLASS": item["cls"],
                "BBOX_X0": bx0, "BBOX_Y0": by0, "BBOX_X1": bx1, "BBOX_Y1": by1,
                "H_INK_PX": item["ink"], "CLASS_MEDIAN_PX": f"{item['class_median']:.2f}",
                "RATIO_TO_CLASS_MEDIAN": f"{item['ratio_to_median']:.4f}", "ROLE_RATIO": f"{item['role_ratio']:.4f}",
                "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": item["text_graphic_overlap"],
                "MIN_CLEARANCE_PX": "inf" if math.isinf(item["min_clearance"]) else f"{item['min_clearance']:.2f}",
                "PASS_FAIL": "PASS" if p else "FAIL", "REASON": reason,
            })

    # Exhaustive layout-object text/text checks plus text/graphic checks.
    overlap_fields = ["CHECK_ID","OBJECT_A","CLASS_A","OBJECT_B","CLASS_B","NATIVE_BBOX_A_PX","NATIVE_BBOX_B_PX","OVERLAP_PIXEL_COUNT","MIN_CLEARANCE_PX","THRESHOLD_PX","PASS_FAIL","METHOD","NOTES"]
    rows = []
    litems = list(layout.items())
    for i, (name_a, a) in enumerate(litems):
        for name_b, b in litems[i+1:]:
            ov = int(np.logical_and(a["mask"], b["mask"]).sum())
            gap = rect_gap(a["bbox"], b["bbox"])
            ok = ov == 0 and gap >= 4
            rows.append(dict(CHECK_ID=f"TT_{name_a}_{name_b}",OBJECT_A=name_a,CLASS_A="TEXT_FORMULA",OBJECT_B=name_b,CLASS_B="TEXT_FORMULA",NATIVE_BBOX_A_PX=str(a["bbox"]),NATIVE_BBOX_B_PX=str(b["bbox"]),OVERLAP_PIXEL_COUNT=ov,MIN_CLEARANCE_PX=f"{gap:.2f}",THRESHOLD_PX="4",PASS_FAIL="PASS" if ok else "FAIL",METHOD="semantic foreground intersection; independent-layout bbox gap",NOTES="natural script components are grouped with their parent formula/label"))
    # Required text-to-arrow/marker/border categories, restricted to relevant closest relations.
    relevant = {
        "L02_Y_NODE": ["NODE_BORDER","LINE_ARROW"],
        "L03_X1": ["NODE_BORDER","LINE_ARROW"], "L04_X2": ["NODE_BORDER","LINE_ARROW"],
        "L06_XD_MINUS_1": ["NODE_BORDER","LINE_ARROW"], "L07_XD": ["NODE_BORDER","LINE_ARROW"],
        "L08_REGION_LABEL": ["PANEL_BORDER"], "L09_FORMULA": ["FORMULA_BOX_BORDER"],
    }
    for name_a, classes in relevant.items():
        a = layout[name_a]
        for cls in classes:
            gmask = graphic_masks[cls]
            ov = int(np.logical_and(a["mask"], gmask).sum())
            dist = 0.0 if ov else float(graphic_distance[cls][a["mask"]].min())
            threshold = 5 if cls == "NODE_BORDER" else 3
            if cls == "PANEL_BORDER": threshold = 6
            ok = ov == 0 and dist >= threshold
            rows.append(dict(CHECK_ID=f"TG_{name_a}_{cls}",OBJECT_A=name_a,CLASS_A="TEXT_FORMULA",OBJECT_B=cls,CLASS_B=cls,NATIVE_BBOX_A_PX=str(a["bbox"]),NATIVE_BBOX_B_PX="semantic-mask",OVERLAP_PIXEL_COUNT=ov,MIN_CLEARANCE_PX=f"{dist:.2f}",THRESHOLD_PX=str(threshold),PASS_FAIL="PASS" if ok else "FAIL",METHOD="raw 300dpi semantic foreground-mask Euclidean distance",NOTES="node=5px; line/arrow=3px; panel crop/edge=6px"))
    # Page boundary and figure crop edge checks, based on the real 300dpi official page.
    for name_a, a in litems:
        bx0, by0, bx1, by1 = a["bbox"]
        page_gap = min(bx0, by0, w-bx1, h-by1)
        crop_gap = min(bx0-x0, by0-y0, x1-bx1, y1-by1)
        rows.append(dict(CHECK_ID=f"EDGE_PAGE_{name_a}",OBJECT_A=name_a,CLASS_A="TEXT_FORMULA",OBJECT_B="OFFICIAL_PAGE_EDGE",CLASS_B="PAGE_EDGE",NATIVE_BBOX_A_PX=str(a["bbox"]),NATIVE_BBOX_B_PX="[0,0,2481,3508]",OVERLAP_PIXEL_COUNT=0,MIN_CLEARANCE_PX=f"{page_gap:.2f}",THRESHOLD_PX="6",PASS_FAIL="PASS" if page_gap>=6 else "FAIL",METHOD="native bbox vs original 300dpi official page boundary",NOTES="official page clip check"))
        rows.append(dict(CHECK_ID=f"EDGE_CROP_{name_a}",OBJECT_A=name_a,CLASS_A="TEXT_FORMULA",OBJECT_B="FIGURE_CROP_EDGE",CLASS_B="FIGURE_EDGE",NATIVE_BBOX_A_PX=str(a["bbox"]),NATIVE_BBOX_B_PX=str(CROP),OVERLAP_PIXEL_COUNT=0,MIN_CLEARANCE_PX=f"{crop_gap:.2f}",THRESHOLD_PX="6",PASS_FAIL="PASS" if crop_gap>=6 else "FAIL",METHOD="native bbox vs no-resize figure crop boundary",NOTES="crop has documented raw margin"))
    for absent in ("MARKER", "DATA_CURVE", "TICK", "LEGEND"):
        rows.append(dict(CHECK_ID=f"ABSENT_{absent}",OBJECT_A=absent,CLASS_A=absent,OBJECT_B="N/A",CLASS_B="N/A",NATIVE_BBOX_A_PX="N/A",NATIVE_BBOX_B_PX="N/A",OVERLAP_PIXEL_COUNT=0,MIN_CLEARANCE_PX="N/A",THRESHOLD_PX="N/A",PASS_FAIL="PASS",METHOD="source enumeration lines 17--35",NOTES="not present; not an unknown"))
    with (ROOT / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=overlap_fields)
        wr.writeheader(); wr.writerows(rows)

    # Summaries consumed when writing the human acceptance report.
    summary = {
        "native_page_px": [w, h],
        "figure_crop_px": list(CROP),
        "base_median_px": base_median,
        "source_font_fail_ids": [i["id"] for i in E if not i["font_pass"]],
        "pixel_fail_ids": [i["id"] for i in E if not i["pixel_pass"]],
        "same_class_ratio_fail_ids": [i["id"] for i in E if not (0.92 <= i["ratio_to_median"] <= 1.08)],
        "role_ratio_fail_checks": [r["CHECK_ID"] for r in role_rows if r["PASS_FAIL"] == "FAIL"],
        "text_graphic_overlap_total": int(sum(i["text_graphic_overlap"] for i in E)),
        "overlap_report_fail_count": sum(r["PASS_FAIL"] == "FAIL" for r in rows),
        "minimum_reported_clearance_px": min(float(r["MIN_CLEARANCE_PX"]) for r in rows if r["MIN_CLEARANCE_PX"] not in ("N/A", "inf")),
        "semantic_mask_px": {"TEXT_FORMULA": int(text_mask.sum()), "LINE_ARROW": int(arrow.sum()), "NODE_BORDER": int(node_border.sum()), "PANEL_BORDER": int(panel_border.sum()), "FORMULA_BOX_BORDER": int(formula_border.sum())},
    }
    (ROOT / "strict_r1_measurement_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
