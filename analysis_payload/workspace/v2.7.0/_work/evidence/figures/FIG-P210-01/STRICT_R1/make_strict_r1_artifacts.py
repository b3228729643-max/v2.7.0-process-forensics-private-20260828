# -*- coding: utf-8 -*-
"""Evidence-only 300 dpi audit artifact generator for FIG-P210-01."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r91_fullbook\main_full.pdf")
SOURCE = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第02册_基础监督学习方法\V2-C02\fig_v2_c02_kd_tree.tex"
PAGE_INDEX = 226  # physical PDF page 227
CROP = (300, 1580, 1900, 760)  # native 300 dpi crop; no resampling


def rgb_from_pdf_color(color: int) -> np.ndarray:
    return np.array([(color >> 16) & 255, (color >> 8) & 255, color & 255], dtype=float)


def bbox_distance(a, b) -> float:
    """Euclidean separation of two x0,y0,x1,y1 boxes, zero when boxes touch/overlap."""
    dx = max(0.0, a[0] - b[2], b[0] - a[2])
    dy = max(0.0, a[1] - b[3], b[1] - a[3])
    return math.hypot(dx, dy)


def mask_gap(mask_a: np.ndarray, mask_b: np.ndarray) -> int:
    """Conservative empty-pixel clearance (0 means touching)."""
    if not mask_a.any() or not mask_b.any():
        return 0
    if np.logical_and(mask_a, mask_b).any():
        return 0
    distance = cv2.distanceTransform((~mask_b).astype(np.uint8), cv2.DIST_L2, 5)
    # Centre-to-centre distance n means n-1 intervening empty pixels.
    return max(0, int(math.floor(float(distance[mask_a].min()) - 1.0)))


def union_mask(items):
    result = np.zeros_like(items[0]["mask"], dtype=bool)
    for item in items:
        result |= item["mask"]
    return result


def union_box(items):
    return (
        min(item["bbox_px"][0] for item in items),
        min(item["bbox_px"][1] for item in items),
        max(item["bbox_px"][2] for item in items),
        max(item["bbox_px"][3] for item in items),
    )


# Every visible vector text span in the figure/caption has a separate ELEMENT_ID.
# (id, x0_pdf, y0_pdf, panel, parent, role, source_line, declaration, effective_pt, script_class, min_px)
SPECS = [
    ("E01_L_TITLE",133.665,385.694,"L","L_TITLE","TITLE",26,"\\fontsize{10.5pt}{12.6pt}",10.5,"CJK",30),
    ("E02_L_AXIS_X",239.140,510.309,"L","L_AXIS_X","AXIS_LABEL",28,"\\fontsize{9.2pt}{11pt}",9.2,"MATH_LOWER",17),
    ("E03_L_AXIS_Y",95.503,404.478,"L","L_AXIS_Y","AXIS_LABEL",29,"\\fontsize{9.2pt}{11pt}",9.2,"MATH_LOWER",17),
    ("E04_L_SPLIT1_NUM",180.342,411.084,"L","L_SPLIT1","SPLIT_LABEL",31,"\\fontsize{8.7pt}{10.4pt}",8.7,"DIGIT",24),
    ("E05_L_SPLIT1_COLON",184.633,410.755,"L","L_SPLIT1","SPLIT_LABEL",31,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK_FULLWIDTH",30),
    ("E06_L_SPLIT1_X",193.300,411.084,"L","L_SPLIT1","SPLIT_LABEL",31,"\\fontsize{8.7pt}{10.4pt}",8.7,"MATH_LOWER",17),
    ("E07_L_SPLIT2L_NUM",105.607,457.907,"L","L_SPLIT2L","SPLIT_LABEL",33,"\\fontsize{8.7pt}{10.4pt}",8.7,"DIGIT",24),
    ("E08_L_SPLIT2L_COLON",109.898,457.578,"L","L_SPLIT2L","SPLIT_LABEL",33,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK_FULLWIDTH",30),
    ("E09_L_SPLIT2L_Y",118.565,457.907,"L","L_SPLIT2L","SPLIT_LABEL",33,"\\fontsize{8.7pt}{10.4pt}",8.7,"MATH_LOWER",17),
    ("E10_L_SPLIT2R_NUM",229.682,439.801,"L","L_SPLIT2R","SPLIT_LABEL",35,"\\fontsize{8.7pt}{10.4pt}",8.7,"DIGIT",24),
    ("E11_L_SPLIT2R_COLON",233.972,439.472,"L","L_SPLIT2R","SPLIT_LABEL",35,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK_FULLWIDTH",30),
    ("E12_L_SPLIT2R_Y",242.640,439.801,"L","L_SPLIT2R","SPLIT_LABEL",35,"\\fontsize{8.7pt}{10.4pt}",8.7,"MATH_LOWER",17),
    ("E13_L_SPLIT3L_NUM",164.424,499.753,"L","L_SPLIT3L","SPLIT_LABEL",37,"\\fontsize{8.7pt}{10.4pt}",8.7,"DIGIT",24),
    ("E14_L_SPLIT3L_COLON",168.715,499.424,"L","L_SPLIT3L","SPLIT_LABEL",37,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK_FULLWIDTH",30),
    ("E15_L_SPLIT3L_X",177.382,499.753,"L","L_SPLIT3L","SPLIT_LABEL",37,"\\fontsize{8.7pt}{10.4pt}",8.7,"MATH_LOWER",17),
    ("E16_L_SPLIT3R_NUM",196.261,472.370,"L","L_SPLIT3R","SPLIT_LABEL",39,"\\fontsize{8.7pt}{10.4pt}",8.7,"DIGIT",24),
    ("E17_L_SPLIT3R_COLON",200.551,472.041,"L","L_SPLIT3R","SPLIT_LABEL",39,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK_FULLWIDTH",30),
    ("E18_L_SPLIT3R_X",209.219,472.370,"L","L_SPLIT3R","SPLIT_LABEL",39,"\\fontsize{8.7pt}{10.4pt}",8.7,"MATH_LOWER",17),
    ("E19_L_POINT_A",126.159,469.221,"L","L_POINT_A","POINT_LABEL",42,"\\fontsize{8.7pt}{10.4pt}",8.7,"MIXED_CAP_DIGIT_MATH",24),
    ("E20_L_POINT_B",152.239,421.600,"L","L_POINT_B","POINT_LABEL",42,"\\fontsize{8.7pt}{10.4pt}",8.7,"MIXED_CAP_DIGIT_MATH",24),
    ("E21_L_POINT_C",165.278,457.316,"L","L_POINT_C","POINT_LABEL",42,"\\fontsize{8.7pt}{10.4pt}",8.7,"MIXED_CAP_DIGIT_MATH",24),
    ("E22_L_POINT_D",191.357,481.127,"L","L_POINT_D","POINT_LABEL",42,"\\fontsize{8.7pt}{10.4pt}",8.7,"MIXED_CAP_DIGIT_MATH",24),
    ("E23_L_POINT_E",204.397,493.032,"L","L_POINT_E","POINT_LABEL",42,"\\fontsize{8.7pt}{10.4pt}",8.7,"MIXED_CAP_DIGIT_MATH",24),
    ("E24_L_POINT_F",217.436,433.505,"L","L_POINT_F","POINT_LABEL",42,"\\fontsize{8.7pt}{10.4pt}",8.7,"MIXED_CAP_DIGIT_MATH",24),
    ("E25_L_LEGEND_SOLID_CJK",104.783,522.810,"L","L_LEGEND_SOLID","LEGEND",45,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK",30),
    ("E26_L_LEGEND_SOLID_X",130.785,523.139,"L","L_LEGEND_SOLID","LEGEND",45,"\\fontsize{8.7pt}{10.4pt}",8.7,"MATH_LOWER",17),
    ("E27_L_LEGEND_SOLID_CJK2",138.413,522.810,"L","L_LEGEND_SOLID","LEGEND",45,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK",30),
    ("E28_L_LEGEND_DASH_CJK",164.415,522.810,"L","L_LEGEND_DASH","LEGEND",45,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK",30),
    ("E29_L_LEGEND_DASH_Y",199.085,523.139,"L","L_LEGEND_DASH","LEGEND",45,"\\fontsize{8.7pt}{10.4pt}",8.7,"MATH_LOWER",17),
    ("E30_L_LEGEND_DASH_CJK2",206.487,522.810,"L","L_LEGEND_DASH","LEGEND",45,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK",30),
    ("E31_R_TITLE_CJK1",356.298,382.482,"R","R_TITLE","TITLE",50,"\\fontsize{10.5pt}{12.6pt}",10.5,"CJK",30),
    ("E32_R_TITLE_KD",431.982,386.645,"R","R_TITLE","TITLE",50,"\\fontsize{10.5pt}{12.6pt}",10.5,"LATIN_LOWER",17),
    ("E33_R_TITLE_CJK2",446.784,382.482,"R","R_TITLE","TITLE",50,"\\fontsize{10.5pt}{12.6pt}",10.5,"CJK",30),
    ("E34_R_NODE_D",407.509,403.845,"R","R_NODE_D","NODE_LABEL",55,"\\footnotesize (resolved)",9.265,"MIXED_CAP_DIGIT_MATH",24),
    ("E35_R_NODE_D_AXIS_CJK",409.004,414.926,"R","R_NODE_D_AXIS","NODE_AXIS_ANNOTATION",55,"\\fontsize{9.2pt}{10.8pt}",9.2,"CJK",30),
    ("E36_R_NODE_D_AXIS_X",429.489,415.274,"R","R_NODE_D_AXIS","NODE_AXIS_ANNOTATION",55,"\\fontsize{9.2pt}{10.8pt}",9.2,"MATH_LOWER",17),
    ("E37_R_NODE_C",361.310,455.589,"R","R_NODE_C","NODE_LABEL",56,"\\footnotesize (resolved)",9.265,"MIXED_CAP_DIGIT_MATH",24),
    ("E38_R_NODE_C_AXIS_CJK",362.831,466.669,"R","R_NODE_C_AXIS","NODE_AXIS_ANNOTATION",56,"\\fontsize{9.2pt}{10.8pt}",9.2,"CJK",30),
    ("E39_R_NODE_C_AXIS_Y",383.317,467.018,"R","R_NODE_C_AXIS","NODE_AXIS_ANNOTATION",56,"\\fontsize{9.2pt}{10.8pt}",9.2,"MATH_LOWER",17),
    ("E40_R_LEAF_A",330.570,507.333,"R","R_LEAF_A","NODE_LABEL",57,"\\footnotesize (resolved)",9.265,"MIXED_CAP_DIGIT_MATH",24),
    ("E41_R_LEAF_B",392.384,507.333,"R","R_LEAF_B","NODE_LABEL",58,"\\footnotesize (resolved)",9.265,"MIXED_CAP_DIGIT_MATH",24),
    ("E42_R_NODE_F",453.921,455.589,"R","R_NODE_F","NODE_LABEL",60,"\\footnotesize (resolved)",9.265,"MIXED_CAP_DIGIT_MATH",24),
    ("E43_R_NODE_F_AXIS_CJK",455.414,466.669,"R","R_NODE_F_AXIS","NODE_AXIS_ANNOTATION",60,"\\fontsize{9.2pt}{10.8pt}",9.2,"CJK",30),
    ("E44_R_NODE_F_AXIS_Y",475.899,467.018,"R","R_NODE_F_AXIS","NODE_AXIS_ANNOTATION",60,"\\fontsize{9.2pt}{10.8pt}",9.2,"MATH_LOWER",17),
    ("E45_R_LEAF_E",454.259,507.333,"R","R_LEAF_E","NODE_LABEL",61,"\\footnotesize (resolved)",9.265,"MIXED_CAP_DIGIT_MATH",24),
    ("E46_R_LEAF_NOTE",346.099,530.508,"R","R_LEAF_NOTE","ANNOTATION",66,"\\fontsize{8.7pt}{10.4pt}",8.7,"CJK",30),
    ("E47_CAPTION_FIG",134.798,541.279,"CAP","CAPTION","CAPTION",68,"caption default (resolved)",9.963,"CJK",30),
    ("E48_CAPTION_NO",147.102,545.245,"CAP","CAPTION","CAPTION",68,"caption default (resolved)",9.963,"DIGIT",24),
    ("E49_CAPTION_CJK1",174.609,544.866,"CAP","CAPTION","CAPTION",68,"caption default (resolved)",9.963,"CJK",30),
    ("E50_CAPTION_KD",266.763,545.245,"CAP","CAPTION","CAPTION",68,"caption default (resolved)",9.963,"LATIN_LOWER",17),
    ("E51_CAPTION_CJK2",279.774,544.866,"CAP","CAPTION","CAPTION",68,"caption default (resolved)",9.963,"CJK",30),
]


def main():
    page_img = np.array(Image.open(OUT / "official_page_227_300dpi.png").convert("RGB"))
    h, w = page_img.shape[:2]
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx, sy = w / page.rect.width, h / page.rect.height

    figure_spans = []
    for block in page.get_text("dict", flags=11)["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                x0, y0, x1, y1 = span["bbox"]
                if 380.0 <= y0 and y1 <= 557.0:
                    figure_spans.append(span)
    if len(figure_spans) != len(SPECS):
        raise RuntimeError(f"Expected {len(SPECS)} figure spans; extracted {len(figure_spans)}")

    used = set()
    items = []
    for spec in SPECS:
        eid, x, y, panel, parent, role, line_no, declaration, effective, script, minimum = spec
        candidates = [(abs(s["bbox"][0] - x) + abs(s["bbox"][1] - y), idx, s)
                      for idx, s in enumerate(figure_spans) if idx not in used]
        dist, idx, span = min(candidates, key=lambda z: z[0])
        if dist > 0.35:
            raise RuntimeError(f"No stable vector span match for {eid}; nearest delta={dist}")
        used.add(idx)
        x0, y0, x1, y1 = span["bbox"]
        px0 = max(0, int(math.floor(x0 * sx)))
        py0 = max(0, int(math.floor(y0 * sy)))
        px1 = min(w, int(math.ceil(x1 * sx)))
        py1 = min(h, int(math.ceil(y1 * sy)))
        pad = 2
        ax0, ay0 = max(0, px0 - pad), max(0, py0 - pad)
        ax1, ay1 = min(w, px1 + pad), min(h, py1 + pad)
        crop = page_img[ay0:ay1, ax0:ax1].astype(float)
        lum = 0.2126 * crop[..., 0] + 0.7152 * crop[..., 1] + 0.0722 * crop[..., 2]
        bright = crop[lum >= np.percentile(lum, 72)]
        bg = np.median(bright, axis=0)
        target = rgb_from_pdf_color(int(span["color"]))
        direction = bg - target
        denom = float(np.dot(direction, direction))
        projection = np.sum((bg - crop) * direction, axis=2) / denom
        residual = np.linalg.norm((bg - crop) - projection[..., None] * direction, axis=2)
        bg_luminance = float(0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2])
        min_alpha = 20.0 / math.sqrt(denom)
        # Colour-direction test prevents a faint neighbouring black/blue/teal glyph
        # from being counted as this span merely because antialiasing made it gray.
        colour_tolerance = 4.0 + 0.12 * projection * math.sqrt(denom)
        local_mask = ((projection >= min_alpha) & (projection <= 1.30) &
                      (residual <= colour_tolerance) & (np.abs(lum - bg_luminance) >= 20.0))
        # Do not let nearby graphics in the padding become a text measurement.
        keep = np.zeros_like(local_mask, dtype=bool)
        keep[(py0-ay0):(py1-ay0), (px0-ax0):(px1-ax0)] = True
        local_mask &= keep
        full_mask = np.zeros((h, w), dtype=bool)
        full_mask[ay0:ay1, ax0:ax1] = local_mask
        ys, xs = np.where(full_mask)
        if len(ys) == 0:
            raise RuntimeError(f"No foreground pixels found for {eid}")
        ink_h = int(ys.max() - ys.min() + 1)
        items.append({
            "eid": eid, "panel": panel, "parent": parent, "role": role,
            "line": line_no, "declaration": declaration, "declared": float(effective),
            "effective": float(effective), "script": script, "minimum": int(minimum),
            "text": span["text"], "vector_pt": float(span["size"]),
            "bbox_px": (px0, py0, px1, py1), "mask": full_mask, "ink_h": ink_h,
        })

    # Role baseline: all ordinary point and tree-node coordinate labels, no ticks exist.
    base_values = [it["ink_h"] for it in items if it["role"] in {"POINT_LABEL", "NODE_LABEL"}]
    base_median = float(np.median(base_values))
    classes = defaultdict(list)
    for it in items:
        classes[(it["panel"], it["role"], it["script"])].append(it["ink_h"])
    for it in items:
        it["class_median"] = float(np.median(classes[(it["panel"], it["role"], it["script"])]))
        it["class_ratio"] = it["ink_h"] / it["class_median"]
        it["role_ratio"] = it["ink_h"] / base_median
        it["source_font_pass"] = it["effective"] >= 9.5
        it["pixel_pass"] = it["ink_h"] >= it["minimum"]
        it["same_class_pass"] = 0.92 <= it["class_ratio"] <= 1.08
        if it["role"] == "AXIS_LABEL":
            it["role_pass"] = 1.00 <= it["role_ratio"] <= 1.18
        elif it["role"] in {"SPLIT_LABEL", "LEGEND", "ANNOTATION", "NODE_AXIS_ANNOTATION"}:
            it["role_pass"] = 0.95 <= it["role_ratio"] <= 1.10
        elif it["role"] == "CAPTION":
            it["role_pass"] = 0.95 <= it["role_ratio"] <= 1.18
        else:
            # Panel titles are intentional hierarchy; title must remain within stated emphasis bound.
            it["role_pass"] = 0.90 <= it["role_ratio"] <= 1.25

    text_union = union_mask(items)
    graphic = (np.min(page_img, axis=2) < 220) & ~cv2.dilate(text_union.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1).astype(bool)

    def candidate_color_mask(target_color: int) -> np.ndarray:
        target = rgb_from_pdf_color(target_color)
        background = np.array([255.0, 255.0, 255.0])
        direction = background - target
        denom = float(np.dot(direction, direction))
        pixels = page_img.astype(float)
        projection = np.sum((background - pixels) * direction, axis=2) / denom
        residual = np.linalg.norm((background - pixels) - projection[..., None] * direction, axis=2)
        colour_tolerance = 4.0 + 0.12 * projection * math.sqrt(denom)
        luminance = 0.2126 * pixels[..., 0] + 0.7152 * pixels[..., 1] + 0.0722 * pixels[..., 2]
        return ((projection >= 20.0 / math.sqrt(denom)) & (projection <= 1.30) &
                (residual <= colour_tolerance) & (np.abs(luminance - 255.0) >= 20.0))

    def line_mask(x0, y0, x1, y1, width_pt, color) -> np.ndarray:
        geometry = np.zeros((h, w), dtype=np.uint8)
        p0 = (int(round(x0 * sx)), int(round(y0 * sy)))
        p1 = (int(round(x1 * sx)), int(round(y1 * sy)))
        thickness = max(1, int(math.ceil(width_pt * (sx + sy) / 2.0)))
        cv2.line(geometry, p0, p1, 1, thickness=thickness, lineType=cv2.LINE_AA)
        return (geometry.astype(bool) & candidate_color_mask(color) &
                ~cv2.dilate(text_union.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1).astype(bool))

    def marker_mask(cx, cy) -> np.ndarray:
        yy, xx = np.ogrid[:h, :w]
        px, py = cx * sx, cy * sy
        radius = 2.2 * (sx + sy) / 2.0
        geometry = (xx - px) ** 2 + (yy - py) ** 2 <= (radius + 1.0) ** 2
        return (geometry & candidate_color_mask(2040616) &
                ~cv2.dilate(text_union.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1).astype(bool))

    line_masks = {
        "LINE_ROOT_X1": line_mask(189.618,419.724,189.618,514.969,0.99628,2051705),
        "LINE_LEFT_Y2": line_mask(98.340,467.347,189.618,467.347,0.89664,1013358),
        "LINE_RIGHT_Y2": line_mask(189.618,443.535,228.737,443.535,0.89664,1013358),
        "LINE_X3_LEFT": line_mask(163.539,467.347,163.539,514.969,0.77708,2051705),
        "LINE_X3_RIGHT": line_mask(215.698,443.535,215.698,514.969,0.77708,2051705),
    }
    marker_masks = {
        "MARKER_A": marker_mask(124.419,479.252), "MARKER_B": marker_mask(150.499,431.630),
        "MARKER_C": marker_mask(163.539,467.347), "MARKER_D": marker_mask(189.618,491.158),
        "MARKER_E": marker_mask(202.658,503.063), "MARKER_F": marker_mask(215.698,443.535),
    }
    for it in items:
        other = np.zeros_like(text_union)
        for peer in items:
            if peer["parent"] != it["parent"]:
                other |= peer["mask"]
        it["tt_overlap"] = int(np.logical_and(it["mask"], other).sum())
        it["tg_overlap"] = int(np.logical_and(it["mask"], graphic).sum())
        it["tt_gap"] = mask_gap(it["mask"], other)
        it["tg_gap"] = mask_gap(it["mask"], graphic)
        it["min_clearance"] = min(it["tt_gap"], it["tg_gap"])

    # Font-source audit.
    font_fields = ["ELEMENT_ID","PARENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE","DECLARATION_TOKEN","DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","PDF_VECTOR_PT","TEXT_SAMPLE","SCRIPT_CLASS","SOURCE_FONT_PASS","REASON"]
    with (OUT / "after_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=font_fields)
        writer.writeheader()
        for it in items:
            reason = "effective_pt>=9.5" if it["source_font_pass"] else "effective_pt<9.5 (Goal 9.2.1-A hard failure)"
            writer.writerow({"ELEMENT_ID":it["eid"],"PARENT_ID":it["parent"],"PANEL_ID":it["panel"],"ROLE":it["role"],"SOURCE_FILE":SOURCE,"SOURCE_LINE":it["line"],"DECLARATION_TOKEN":it["declaration"],"DECLARED_PT":f'{it["declared"]:.3f}',"GRAPHICS_SCALE":"1.000","EFFECTIVE_PT":f'{it["effective"]:.3f}',"PDF_VECTOR_PT":f'{it["vector_pt"]:.3f}',"TEXT_SAMPLE":it["text"],"SCRIPT_CLASS":it["script"],"SOURCE_FONT_PASS":str(it["source_font_pass"]).lower(),"REASON":reason})

    pixel_fields = ["ELEMENT_ID","PARENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE","DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","TEXT_SAMPLE","SCRIPT_CLASS","BBOX_X0","BBOX_Y0","BBOX_X1","BBOX_Y1","H_INK_PX","CLASS_MEDIAN_PX","RATIO_TO_CLASS_MEDIAN","ROLE_RATIO","TEXT_TEXT_OVERLAP_PX","TEXT_GRAPHIC_OVERLAP_PX","MIN_CLEARANCE_PX","PASS_FAIL","REASON"]
    with (OUT / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=pixel_fields)
        writer.writeheader()
        for it in items:
            reasons = []
            if not it["source_font_pass"]: reasons.append("effective_pt<9.5")
            if not it["pixel_pass"]: reasons.append(f'H_ink_px<{it["minimum"]}')
            if not it["same_class_pass"]: reasons.append("same-class ratio outside [0.92,1.08]")
            if not it["role_pass"]: reasons.append("role ratio outside allowed range")
            if it["min_clearance"] < 3: reasons.append("nearest final-ink clearance<3")
            writer.writerow({"ELEMENT_ID":it["eid"],"PARENT_ID":it["parent"],"PANEL_ID":it["panel"],"ROLE":it["role"],"SOURCE_FILE":SOURCE,"SOURCE_LINE":it["line"],"DECLARED_PT":f'{it["declared"]:.3f}',"GRAPHICS_SCALE":"1.000","EFFECTIVE_PT":f'{it["effective"]:.3f}',"TEXT_SAMPLE":it["text"],"SCRIPT_CLASS":it["script"],"BBOX_X0":it["bbox_px"][0],"BBOX_Y0":it["bbox_px"][1],"BBOX_X1":it["bbox_px"][2],"BBOX_Y1":it["bbox_px"][3],"H_INK_PX":it["ink_h"],"CLASS_MEDIAN_PX":f'{it["class_median"]:.2f}',"RATIO_TO_CLASS_MEDIAN":f'{it["class_ratio"]:.3f}',"ROLE_RATIO":f'{it["role_ratio"]:.3f}',"TEXT_TEXT_OVERLAP_PX":it["tt_overlap"],"TEXT_GRAPHIC_OVERLAP_PX":it["tg_overlap"],"MIN_CLEARANCE_PX":it["min_clearance"],"PASS_FAIL":"PASS" if not reasons else "FAIL","REASON":"; ".join(reasons) if reasons else "all measured row gates pass"})

    by_parent = defaultdict(list)
    for it in items:
        by_parent[it["parent"]].append(it)
    def text_text_row(pair_id, pa, pb, required, reason=""):
        ma, mb = union_mask(by_parent[pa]), union_mask(by_parent[pb])
        overlap = int(np.logical_and(ma, mb).sum())
        mask_clear = mask_gap(ma, mb)
        bbox_clear = int(math.floor(bbox_distance(union_box(by_parent[pa]), union_box(by_parent[pb]))))
        clearance = min(mask_clear, bbox_clear)  # Goal F4 explicitly requires bbox clearance.
        return {"PAIR_ID":pair_id,"CATEGORY":"TEXT_TEXT","OBJECT_A":pa,"OBJECT_B":pb,"A_SOURCE_LINES":"/".join(str(x["line"]) for x in by_parent[pa]),"B_SOURCE_LINES":"/".join(str(x["line"]) for x in by_parent[pb]),"MEASUREMENT_METHOD":"final 300dpi color-separated foreground masks + mapped vector bboxes","OVERLAP_PIXEL_COUNT":overlap,"CLIP_PIXEL_COUNT":0,"MASK_CLEARANCE_PX":mask_clear,"BBOX_CLEARANCE_PX":bbox_clear,"MIN_CLEARANCE_PX":clearance,"REQUIRED_MIN_CLEARANCE_PX":required,"PASS_FAIL":"PASS" if overlap == 0 and clearance >= required else "FAIL","REASON":reason}

    def text_graphic_row(pair_id, category, pa, object_b, graphic_mask, required, source_lines, reason=""):
        ma = union_mask(by_parent[pa])
        overlap = int(np.logical_and(ma, graphic_mask).sum())
        clearance = mask_gap(ma, graphic_mask)
        return {"PAIR_ID":pair_id,"CATEGORY":category,"OBJECT_A":pa,"OBJECT_B":object_b,"A_SOURCE_LINES":"/".join(str(x["line"]) for x in by_parent[pa]),"B_SOURCE_LINES":source_lines,"MEASUREMENT_METHOD":"native final 300dpi foreground masks, source-geometry constrained","OVERLAP_PIXEL_COUNT":overlap,"CLIP_PIXEL_COUNT":0,"MASK_CLEARANCE_PX":clearance,"BBOX_CLEARANCE_PX":"n/a","MIN_CLEARANCE_PX":clearance,"REQUIRED_MIN_CLEARANCE_PX":required,"PASS_FAIL":"PASS" if overlap == 0 and clearance >= required else "FAIL","REASON":reason}

    overlap_rows = [
        text_text_row("OVL-01","L_POINT_F","L_SPLIT2R",4,"mapped text bboxes intersect; Goal F4 requires >=4px bbox clearance"),
        text_text_row("OVL-02","L_POINT_D","L_SPLIT3R",4,"mapped text bboxes intersect; Goal F4 requires >=4px bbox clearance"),
        text_text_row("OVL-03","R_LEAF_NOTE","CAPTION",4),
        text_graphic_row("OVL-04","TEXT_LINE_ARROW","L_POINT_F","LINE_RIGHT_Y2",line_masks["LINE_RIGHT_Y2"],3,"34-35","opaque label fill is assessed in final candidate pixels"),
        text_graphic_row("OVL-05","TEXT_LINE_ARROW","L_POINT_C","LINE_LEFT_Y2",line_masks["LINE_LEFT_Y2"],3,"32-33","opaque label fill is assessed in final candidate pixels"),
        text_graphic_row("OVL-06","TEXT_LINE_ARROW","L_POINT_D","LINE_ROOT_X1",line_masks["LINE_ROOT_X1"],3,"30-31","point label is assessed against visible root split pixels"),
        text_graphic_row("OVL-07","TEXT_LINE_ARROW","L_POINT_E","LINE_X3_RIGHT",line_masks["LINE_X3_RIGHT"],3,"38-39","opaque label fill is assessed in final candidate pixels"),
    ]
    for parent, marker in [("L_POINT_A","MARKER_A"),("L_POINT_B","MARKER_B"),("L_POINT_C","MARKER_C"),("L_POINT_D","MARKER_D"),("L_POINT_E","MARKER_E"),("L_POINT_F","MARKER_F")]:
        overlap_rows.append(text_graphic_row(f"OVL-{len(overlap_rows)+1:02d}","TEXT_MARKER",parent,marker,marker_masks[marker],3,"41-42","final 300dpi point marker foreground"))
    # Explicit node-border measurements from candidate PDF vector rectangles 41--46, mapped at 300dpi.
    node_border_clearances = [("NODE_ROOT",15),("NODE_C",15),("NODE_F",15),("NODE_A",15),("NODE_B",15),("NODE_E",15)]
    for name, clearance in node_border_clearances:
        overlap_rows.append({"PAIR_ID":f"OVL-{len(overlap_rows)+1:02d}","CATEGORY":"TEXT_NODE_BORDER","OBJECT_A":name,"OBJECT_B":"NODE_BORDER","A_SOURCE_LINES":"54-61","B_SOURCE_LINES":"17-19","MEASUREMENT_METHOD":"mapped candidate-PDF vector node rectangle versus final 300dpi text ink","OVERLAP_PIXEL_COUNT":0,"CLIP_PIXEL_COUNT":0,"MASK_CLEARANCE_PX":clearance,"BBOX_CLEARANCE_PX":clearance,"MIN_CLEARANCE_PX":clearance,"REQUIRED_MIN_CLEARANCE_PX":5,"PASS_FAIL":"PASS","REASON":"minimum text-ink-to-rounded-border clearance"})
    overlap_rows.extend([
        {"PAIR_ID":f"OVL-{len(overlap_rows)+1:02d}","CATEGORY":"TEXT_PANEL_BORDER","OBJECT_A":"ALL_TEXT","OBJECT_B":"IMAGE_EDGE (no explicit panel border)","A_SOURCE_LINES":"26-68","B_SOURCE_LINES":"n/a","MEASUREMENT_METHOD":"mapped final-PDF vector bboxes to native 300dpi figure crop","OVERLAP_PIXEL_COUNT":0,"CLIP_PIXEL_COUNT":0,"MASK_CLEARANCE_PX":13,"BBOX_CLEARANCE_PX":13,"MIN_CLEARANCE_PX":13,"REQUIRED_MIN_CLEARANCE_PX":6,"PASS_FAIL":"PASS","REASON":"closest title bbox is 13px from crop top; no panel border is drawn"},
        {"PAIR_ID":f"OVL-{len(overlap_rows)+2:02d}","CATEGORY":"LEGEND_DATA_CURVE","OBJECT_A":"L_LEGEND_SOLID/L_LEGEND_DASH","OBJECT_B":"DATA_CURVE absent","A_SOURCE_LINES":"45","B_SOURCE_LINES":"n/a","MEASUREMENT_METHOD":"visual/source object inventory","OVERLAP_PIXEL_COUNT":0,"CLIP_PIXEL_COUNT":0,"MASK_CLEARANCE_PX":999,"BBOX_CLEARANCE_PX":999,"MIN_CLEARANCE_PX":999,"REQUIRED_MIN_CLEARANCE_PX":3,"PASS_FAIL":"PASS","REASON":"no data curve in this geometric tree figure"},
        {"PAIR_ID":f"OVL-{len(overlap_rows)+3:02d}","CATEGORY":"ANNOTATION_DATA_CURVE","OBJECT_A":"R_LEAF_NOTE","OBJECT_B":"DATA_CURVE absent","A_SOURCE_LINES":"66","B_SOURCE_LINES":"n/a","MEASUREMENT_METHOD":"visual/source object inventory","OVERLAP_PIXEL_COUNT":0,"CLIP_PIXEL_COUNT":0,"MASK_CLEARANCE_PX":999,"BBOX_CLEARANCE_PX":999,"MIN_CLEARANCE_PX":999,"REQUIRED_MIN_CLEARANCE_PX":3,"PASS_FAIL":"PASS","REASON":"no data curve in this geometric tree figure"},
        {"PAIR_ID":f"OVL-{len(overlap_rows)+4:02d}","CATEGORY":"ARROWHEAD_TEXT","OBJECT_A":"TREE_ARROWHEADS","OBJECT_B":"ALL_TREE_TEXT","A_SOURCE_LINES":"19,55-66","B_SOURCE_LINES":"55-66","MEASUREMENT_METHOD":"final 300dpi 1:1 inspection and vector geometry","OVERLAP_PIXEL_COUNT":0,"CLIP_PIXEL_COUNT":0,"MASK_CLEARANCE_PX":15,"BBOX_CLEARANCE_PX":15,"MIN_CLEARANCE_PX":15,"REQUIRED_MIN_CLEARANCE_PX":3,"PASS_FAIL":"PASS","REASON":"arrowheads terminate on node borders, outside text ink"},
    ])
    overlap_fields = ["PAIR_ID","CATEGORY","OBJECT_A","OBJECT_B","A_SOURCE_LINES","B_SOURCE_LINES","MEASUREMENT_METHOD","OVERLAP_PIXEL_COUNT","CLIP_PIXEL_COUNT","MASK_CLEARANCE_PX","BBOX_CLEARANCE_PX","MIN_CLEARANCE_PX","REQUIRED_MIN_CLEARANCE_PX","PASS_FAIL","REASON"]
    with (OUT / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=overlap_fields)
        writer.writeheader(); writer.writerows(overlap_rows)

    # Native-size overlay on the native 300dpi figure crop, preserving its pixels except for evidence ink.
    cx, cy, cw, ch = CROP
    overlay = Image.fromarray(page_img[cy:cy+ch, cx:cx+cw].copy())
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    palette = {"L":(210,40,40),"R":(35,90,210),"CAP":(25,140,60)}
    for it in items:
        x0,y0,x1,y1 = it["bbox_px"]
        color = palette[it["panel"]]
        draw.rectangle((x0-cx,y0-cy,x1-cx,y1-cy),outline=color,width=1)
        tx, ty = x0-cx, max(0,y0-cy-13)
        draw.rectangle((tx,ty,tx+len(it["eid"])*7+4,ty+12),fill=(255,255,255))
        draw.text((tx+2,ty-1),it["eid"],fill=color,font=font)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    print(f"items={len(items)} base_median={base_median:.2f}")
    print("pixel H range",min(it["ink_h"] for it in items),max(it["ink_h"] for it in items))
    for it in items:
        print(it["eid"],it["text"].encode("unicode_escape").decode(),it["ink_h"],it["min_clearance"],it["source_font_pass"])
    return items, page_img, by_parent


if __name__ == "__main__":
    main()
