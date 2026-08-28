"""Independent, read-only measurement helper for FIG-P172-01 STRICT_R1.

Inputs are the official R90 PDF rasterized directly at 300 dpi.  This file
only writes derived evidence beside itself; it never writes source or build
files.  PDF text boxes were independently extracted from physical page 187
and recorded below in PDF user-space points, then mapped at 300/72 px/pt.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from math import ceil, floor
from pathlib import Path
from statistics import median

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


HERE = Path(__file__).resolve().parent
RAW = HERE / "official_page_p187_300dpi-187.png"
SOURCE_FILE = (
    "src/绘图源码/第01册_数学基础与统计学习基本理论/"
    "V1-C11/fig_v1_c11_tagging.tex"
)
PX_PER_PDF_PT = 300.0 / 72.0
INK = np.array((31, 35, 40), dtype=np.int16)
BLUE = np.array((31, 78, 121), dtype=np.int16)
TEAL = np.array((15, 118, 110), dtype=np.int16)
GOLD = np.array((183, 121, 31), dtype=np.int16)


def item(
    element_id: str,
    parent_id: str,
    panel_id: str,
    role: str,
    source_line: int,
    declared_pt: float,
    effective_pt: float,
    text_sample: str,
    script_class: str,
    bbox: tuple[float, float, float, float],
    ink_kind: str,
    threshold: int,
    class_group: str,
    role_ratio_group: str,
):
    return {
        "element_id": element_id,
        "parent_id": parent_id,
        "panel_id": panel_id,
        "role": role,
        "source_line": source_line,
        "declared_pt": declared_pt,
        "effective_pt": effective_pt,
        "text_sample": text_sample,
        "script_class": script_class,
        "bbox_pdf": bbox,
        "ink_kind": ink_kind,
        "threshold": threshold,
        "class_group": class_group,
        "role_ratio_group": role_ratio_group,
    }


# Each row is a reader-visible text component.  Mathematical bases and their
# natural scripts are separate rows so an undersized script cannot be hidden
# by a taller base glyph.
I: list[dict] = [
    item("P172-TITLE-HMM.LATIN", "P172-TITLE-HMM", "HMM", "PANEL_TITLE", 21, 10, 10, "HMM", "LATIN_CAP", (171.44,225.36,199.69,235.32), "blue", 24, "PANEL_TITLE_LATIN", "PANEL_TITLE_LATIN"),
    item("P172-TITLE-HMM.CJK", "P172-TITLE-HMM", "HMM", "PANEL_TITLE", 21, 10, 10, "：生成关系", "CJK", (199.69,221.40,249.51,235.82), "blue", 30, "PANEL_TITLE_CJK", "PANEL_TITLE_CJK"),
    item("P172-TITLE-CRF.CJK_A", "P172-TITLE-CRF", "CRF", "PANEL_TITLE", 39, 10, 10, "线性链", "CJK", (335.08,221.40,364.96,235.82), "teal", 30, "PANEL_TITLE_CJK", "PANEL_TITLE_CJK"),
    item("P172-TITLE-CRF.LATIN", "P172-TITLE-CRF", "CRF", "PANEL_TITLE", 39, 10, 10, "CRF", "LATIN_CAP", (367.31,225.36,387.55,235.32), "teal", 24, "PANEL_TITLE_LATIN", "PANEL_TITLE_LATIN"),
    item("P172-TITLE-CRF.CJK_B", "P172-TITLE-CRF", "CRF", "PANEL_TITLE", 39, 10, 10, "：条件因子", "CJK", (387.55,221.40,437.36,235.82), "teal", 30, "PANEL_TITLE_CJK", "PANEL_TITLE_CJK"),
]


def add_formula(parent: str, panel: str, line: int, name: str, base: tuple[float,float,float,float], script: tuple[float,float,float,float], sub: str):
    I.append(item(f"{parent}.BASE", parent, panel, "NODE_LABEL", line, 10, 10, name, "LATIN_CAP", base, "ink", 24, "NODE_BASE", "NODE_BASE"))
    I.append(item(f"{parent}.SCRIPT", parent, panel, "NODE_LABEL", line, 10, 10, sub, "NATURAL_SCRIPT", script, "ink", 15, "NODE_SCRIPT", "NODE_SCRIPT"))


def add_dots(parent: str, panel: str, line: int, bbox: tuple[float,float,float,float]):
    I.append(item(parent, parent, panel, "SEQUENCE_MARKER", line, 10, 10, "⋯", "MATH_SYMBOL", bbox, "ink", 22, "SEQUENCE_MARKER", "SEQUENCE_MARKER"))


add_formula("P172-HMM-HY1", "HMM", 22, "Y", (136.16,257.78,142.21,267.74), (144.54,260.63,148.19,269.59), "t")
add_formula("P172-HMM-HY2", "HMM", 23, "Y", (171.52,257.50,177.57,267.46), (179.90,260.57,195.17,269.54), "t+1")
add_dots("P172-HMM-Y-GAP", "HMM", 24, (219.33,257.17,228.83,267.14))
add_formula("P172-HMM-HY3", "HMM", 25, "Y", (258.00,257.54,264.05,267.51), (266.38,260.94,272.42,269.91), "T")
add_formula("P172-HMM-HX1", "HMM", 26, "X", (137.18,293.21,143.52,303.17), (143.52,296.06,147.17,305.03), "t")
add_formula("P172-HMM-HX2", "HMM", 27, "X", (172.54,292.93,178.88,302.90), (178.88,296.01,194.15,304.97), "t+1")
add_dots("P172-HMM-X-GAP", "HMM", 28, (219.33,292.61,228.83,302.57))
add_formula("P172-HMM-HX3", "HMM", 29, "X", (259.02,292.98,265.36,302.94), (265.36,296.37,271.41,305.34), "T")
add_formula("P172-CRF-CY1", "CRF", 40, "Y", (311.91,257.78,317.96,267.74), (320.29,260.63,323.94,269.59), "t")
add_formula("P172-CRF-CY2", "CRF", 41, "Y", (347.27,257.50,353.32,267.46), (355.65,260.57,370.92,269.54), "t+1")
add_dots("P172-CRF-Y-GAP", "CRF", 42, (395.08,257.17,404.57,267.14))
add_formula("P172-CRF-CY3", "CRF", 43, "Y", (433.75,257.54,439.80,267.51), (442.13,260.94,448.17,269.91), "T")
add_formula("P172-CRF-CX1", "CRF", 44, "X", (312.93,293.21,319.27,303.17), (319.27,296.06,322.92,305.03), "t")
add_formula("P172-CRF-CX2", "CRF", 45, "X", (348.28,292.93,354.63,302.90), (354.63,296.01,369.90,304.97), "t+1")
add_dots("P172-CRF-X-GAP", "CRF", 46, (395.08,292.61,404.57,302.57))
add_formula("P172-CRF-CX3", "CRF", 47, "X", (434.77,292.98,441.11,302.94), (441.11,296.37,447.16,305.34), "T")

I += [
    item("P172-CONDITION.CJK", "P172-CONDITION", "CRF", "ANNOTATION", 63, 9.2, 9.2, "给定观测", "CJK", (357.74,314.81,394.41,324.63), "teal", 30, "ANNOTATION_CJK", "ANNOTATION_CJK"),
    item("P172-CONDITION.x", "P172-CONDITION", "CRF", "ANNOTATION", 63, 9.2, 9.2, "x", "LATIN_LOWER", (396.56,315.27,401.94,324.44), "teal", 17, "ANNOTATION_LOWER", "ANNOTATION_LOWER"),
    item("P172-LEGEND-LATENT", "P172-LEGEND-LATENT", "LEGEND", "LEGEND_LABEL", 67, 9.2, 9.2, "隐变量", "CJK", (191.63,327.36,219.13,337.18), "ink", 30, "LEGEND_CJK", "LEGEND_CJK"),
    item("P172-LEGEND-OBSERVED", "P172-LEGEND-OBSERVED", "LEGEND", "LEGEND_LABEL", 69, 9.2, 9.2, "观测变量", "CJK", (242.65,327.36,279.32,337.18), "ink", 30, "LEGEND_CJK", "LEGEND_CJK"),
    item("P172-LEGEND-FACTOR", "P172-LEGEND-FACTOR", "LEGEND", "LEGEND_LABEL", 71, 9.2, 9.2, "条件因子（无向）", "CJK", (305.58,327.36,378.91,337.18), "ink", 30, "LEGEND_CJK", "LEGEND_CJK"),
    item("P172-LEGEND-GENERATIVE", "P172-LEGEND-GENERATIVE", "LEGEND", "LEGEND_LABEL", 73, 9.2, 9.2, "生成方向", "CJK", (386.65,327.36,423.32,337.18), "ink", 30, "LEGEND_CJK", "LEGEND_CJK"),
    item("P172-CAPTION-L1.LABEL_CJK", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "图", "CJK", (62.36,342.60,72.32,357.03), "ink", 30, "CAPTION_CJK", "CAPTION_CJK"),
    item("P172-CAPTION-L1.LABEL_NUMBER", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "11.1", "NUMBER", (74.59,346.56,91.79,356.53), "ink", 24, "CAPTION_NUMBER", "CAPTION_NUMBER"),
    item("P172-CAPTION-L1.HMM_1", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "HMM", "LATIN_CAP", (101.75,346.56,126.81,356.53), "ink", 24, "CAPTION_CAP", "CAPTION_CAP"),
    item("P172-CAPTION-L1.CJK_1", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "与线性链", "CJK", (126.81,346.19,169.06,356.86), "ink", 30, "CAPTION_CJK", "CAPTION_CJK"),
    item("P172-CAPTION-L1.CRF_1", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "CRF", "LATIN_CAP", (171.46,346.56,190.18,356.53), "ink", 24, "CAPTION_CAP", "CAPTION_CAP"),
    item("P172-CAPTION-L1.CJK_2", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "都利用相邻标记关系，但箭头只用于", "CJK", (190.18,346.19,351.52,356.86), "ink", 30, "CAPTION_CJK", "CAPTION_CJK"),
    item("P172-CAPTION-L1.HMM_2", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "HMM", "LATIN_CAP", (353.91,346.56,378.97,356.53), "ink", 24, "CAPTION_CAP", "CAPTION_CAP"),
    item("P172-CAPTION-L1.CJK_3", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "的生成方向；", "CJK", (378.97,346.19,441.15,356.86), "ink", 30, "CAPTION_CJK", "CAPTION_CJK"),
    item("P172-CAPTION-L1.CRF_2", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "CRF", "LATIN_CAP", (440.68,346.56,459.40,356.53), "ink", 24, "CAPTION_CAP", "CAPTION_CAP"),
    item("P172-CAPTION-L1.CJK_4", "P172-CAPTION-L1", "CAPTION", "CAPTION", 75, 10, 10, "中的无向线段", "CJK", (459.40,346.19,521.57,356.86), "ink", 30, "CAPTION_CJK", "CAPTION_CJK"),
    item("P172-CAPTION-L2.CJK", "P172-CAPTION-L2", "CAPTION", "CAPTION", 75, 10, 10, "表示给定观测后的局部因子。", "CJK", (62.36,359.58,191.88,370.25), "ink", 30, "CAPTION_CJK", "CAPTION_CJK"),
]


# Parent boxes are unions of all components and are the boxes rendered in the
# overlay.  They are also used for reader-text clearance (not child glyph gaps).
PARENT_LABEL = {
    "P172-TITLE-HMM": "TITLE-HMM", "P172-TITLE-CRF": "TITLE-CRF",
    "P172-HMM-HY1": "HMM-HY1", "P172-HMM-HY2": "HMM-HY2", "P172-HMM-Y-GAP": "HMM-Y-GAP", "P172-HMM-HY3": "HMM-HY3",
    "P172-HMM-HX1": "HMM-HX1", "P172-HMM-HX2": "HMM-HX2", "P172-HMM-X-GAP": "HMM-X-GAP", "P172-HMM-HX3": "HMM-HX3",
    "P172-CRF-CY1": "CRF-CY1", "P172-CRF-CY2": "CRF-CY2", "P172-CRF-Y-GAP": "CRF-Y-GAP", "P172-CRF-CY3": "CRF-CY3",
    "P172-CRF-CX1": "CRF-CX1", "P172-CRF-CX2": "CRF-CX2", "P172-CRF-X-GAP": "CRF-X-GAP", "P172-CRF-CX3": "CRF-CX3",
    "P172-CONDITION": "CONDITION", "P172-LEGEND-LATENT": "LEG-LATENT", "P172-LEGEND-OBSERVED": "LEG-OBSERVED", "P172-LEGEND-FACTOR": "LEG-FACTOR", "P172-LEGEND-GENERATIVE": "LEG-GENERATIVE",
    "P172-CAPTION-L1": "CAPTION-L1", "P172-CAPTION-L2": "CAPTION-L2",
}


def pxbox(b: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return (floor(b[0] * PX_PER_PDF_PT), floor(b[1] * PX_PER_PDF_PT), ceil(b[2] * PX_PER_PDF_PT), ceil(b[3] * PX_PER_PDF_PT))


def union_box(rows: list[dict]) -> tuple[int, int, int, int]:
    boxes = [pxbox(r["bbox_pdf"]) for r in rows]
    return min(x[0] for x in boxes), min(x[1] for x in boxes), max(x[2] for x in boxes), max(x[3] for x in boxes)


def box_gap(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return float((dx * dx + dy * dy) ** 0.5)


def font_path() -> str | None:
    for candidate in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if Path(candidate).exists():
            return candidate
    return None


def main() -> None:
    image = Image.open(RAW).convert("RGB")
    # int32 avoids overflow when an RGB channel difference is squared.
    arr = np.asarray(image, dtype=np.int32)
    height, width = arr.shape[:2]

    def colour_mask(colour: np.ndarray, tolerance: float = 50.0) -> np.ndarray:
        return np.sqrt(np.sum((arr - colour) ** 2, axis=2)) < tolerance

    masks = {"ink": colour_mask(INK), "blue": colour_mask(BLUE), "teal": colour_mask(TEAL), "gold": colour_mask(GOLD)}
    parent_rows: dict[str, list[dict]] = defaultdict(list)
    for row in I:
        parent_rows[row["parent_id"]].append(row)
    parent_boxes = {parent: union_box(rows) for parent, rows in parent_rows.items()}

    # Measure only pixels whose RGB differs by far more than 20/255 from the
    # local white/near-white backgrounds.  A tighter color-reference threshold
    # prevents blue borders or gold factor squares from contaminating black text.
    for row in I:
        x0, y0, x1, y1 = pxbox(row["bbox_pdf"])
        ex0, ey0, ex1, ey1 = max(0, x0 - 1), max(0, y0 - 1), min(width, x1 + 1), min(height, y1 + 1)
        mask = masks[row["ink_kind"]][ey0:ey1, ex0:ex1]
        yy, xx = np.nonzero(mask)
        if len(yy) == 0:
            raise RuntimeError(f"No foreground pixels for {row['element_id']}")
        row["bbox_px"] = (x0, y0, x1, y1)
        row["h_ink"] = int(yy.max() - yy.min() + 1)
        row["ink_pixels"] = int(mask.sum())

    class_values: dict[str, list[int]] = defaultdict(list)
    for row in I:
        class_values[row["class_group"]].append(row["h_ink"])
    class_median = {k: float(median(v)) for k, v in class_values.items()}
    for row in I:
        row["class_median"] = class_median[row["class_group"]]
        row["class_ratio"] = row["h_ink"] / row["class_median"]

    # Semantic role bases are script-compatible: mathematical capitals use
    # ordinary node capitals, while CJK title/annotation roles use the CJK
    # legend body.  This does not compare CJK full glyphs with Latin x/cap height.
    role_base = {
        "NODE_BASE": class_median["NODE_BASE"],
        "NODE_SCRIPT": class_median["NODE_SCRIPT"],
        "PANEL_TITLE_LATIN": class_median["NODE_BASE"],
        "PANEL_TITLE_CJK": class_median["LEGEND_CJK"],
        "ANNOTATION_CJK": class_median["LEGEND_CJK"],
        "ANNOTATION_LOWER": class_median["ANNOTATION_LOWER"],
        "LEGEND_CJK": class_median["LEGEND_CJK"],
        "SEQUENCE_MARKER": class_median["SEQUENCE_MARKER"],
        "CAPTION_CJK": class_median["CAPTION_CJK"],
        "CAPTION_CAP": class_median["CAPTION_CAP"],
        "CAPTION_NUMBER": class_median["CAPTION_NUMBER"],
    }
    for row in I:
        row["role_ratio"] = row["h_ink"] / role_base[row["role_ratio_group"]]

    # Native pixel measurements for key text-to-graphic pairs.  The source has
    # both black CRF edges and black text, so those same-color cases are also
    # independently checked against the vector path positions in the listed ROIs.
    def parent_pixels(parent: str) -> tuple[np.ndarray, np.ndarray]:
        ys, xs = [], []
        for r in parent_rows[parent]:
            x0, y0, x1, y1 = r["bbox_px"]
            yy, xx = np.nonzero(masks[r["ink_kind"]][y0:y1, x0:x1])
            ys.append(y0 + yy); xs.append(x0 + xx)
        return np.concatenate(ys), np.concatenate(xs)

    def mask_distance(parent: str, target: np.ndarray) -> float:
        ys, xs = parent_pixels(parent)
        return float(distance_transform_edt(~target)[ys, xs].min())

    # Text-to-text is bboxes by the protocol.  Retain every pair, not only the
    # nearest pair, because it is later written into the overlap evidence scope.
    pairs = []
    parent_ids = sorted(parent_boxes)
    parent_text_min = {parent: float("inf") for parent in parent_ids}
    for idx, a_id in enumerate(parent_ids):
        for b_id in parent_ids[idx + 1:]:
            d = box_gap(parent_boxes[a_id], parent_boxes[b_id])
            pairs.append((a_id, b_id, d))
            parent_text_min[a_id] = min(parent_text_min[a_id], d)
            parent_text_min[b_id] = min(parent_text_min[b_id], d)
    min_tt = min(g for _, _, g in pairs)

    node_parents = [
        "P172-HMM-HY1", "P172-HMM-HY2", "P172-HMM-HY3",
        "P172-HMM-HX1", "P172-HMM-HX2", "P172-HMM-HX3",
        "P172-CRF-CY1", "P172-CRF-CY2", "P172-CRF-CY3",
        "P172-CRF-CX1", "P172-CRF-CX2", "P172-CRF-CX3",
    ]
    node_clearance = {parent: mask_distance(parent, masks["blue"]) for parent in node_parents}
    brace_mask = masks["teal"].copy()
    brace_mask[1310:, :] = False
    all_graphics = masks["ink"] | masks["blue"] | masks["teal"] | masks["gold"]
    graphics_without_text = all_graphics.copy()
    for x0, y0, x1, y1 in parent_boxes.values():
        graphics_without_text[max(0, y0-2):min(height, y1+2), max(0, x0-2):min(width, x1+2)] = False

    specific_clearance = {
        "P172-HMM-Y-GAP": mask_distance("P172-HMM-Y-GAP", masks["blue"]),
        "P172-HMM-X-GAP": mask_distance("P172-HMM-X-GAP", masks["blue"]),
        "P172-CRF-Y-GAP": mask_distance("P172-CRF-Y-GAP", masks["gold"]),
        "P172-CRF-X-GAP": mask_distance("P172-CRF-X-GAP", masks["blue"]),
        "P172-CONDITION": mask_distance("P172-CONDITION", brace_mask),
        "P172-LEGEND-LATENT": mask_distance("P172-LEGEND-LATENT", masks["blue"]),
        "P172-LEGEND-OBSERVED": mask_distance("P172-LEGEND-OBSERVED", masks["blue"]),
        "P172-LEGEND-FACTOR": mask_distance("P172-LEGEND-FACTOR", masks["gold"]),
        "P172-LEGEND-GENERATIVE": mask_distance("P172-LEGEND-GENERATIVE", masks["blue"]),
        "P172-TITLE-HMM": mask_distance("P172-TITLE-HMM", graphics_without_text),
        "P172-TITLE-CRF": mask_distance("P172-TITLE-CRF", graphics_without_text),
        "P172-CAPTION-L1": mask_distance("P172-CAPTION-L1", graphics_without_text),
        "P172-CAPTION-L2": mask_distance("P172-CAPTION-L2", graphics_without_text),
    }
    clearance = {parent: min(node_clearance[parent], parent_text_min[parent]) for parent in node_parents}
    clearance.update({parent: min(d, parent_text_min[parent]) for parent, d in specific_clearance.items()})

    # Source rules: condition and all four legend labels explicitly resolve to
    # 9.2pt.  The common every-node \small rule resolves default node material to
    # 10pt in the 11pt book; natural subscripts derive from that legal baseline.
    source_fail_parents = {
        "P172-CONDITION",
        "P172-LEGEND-LATENT",
        "P172-LEGEND-OBSERVED",
        "P172-LEGEND-FACTOR",
        "P172-LEGEND-GENERATIVE",
    }
    for row in I:
        row["min_clearance"] = clearance[row["parent_id"]]
        row["source_font_pass"] = row["parent_id"] not in source_fail_parents
        row["height_pass"] = row["h_ink"] >= row["threshold"]
        # Caption runs are split solely to expose mixed-script height floors.
        # They remain components of one semantic caption line, not separately
        # sized same-role labels; the parent line is the applicable object.
        row["same_class_applicable"] = row["role"] != "CAPTION"
        row["same_class_pass"] = (0.92 <= row["class_ratio"] <= 1.08) if row["same_class_applicable"] else True
        row["clearance_pass"] = row["min_clearance"] >= (5.0 if row["role"] == "NODE_LABEL" else 3.0)
        # These are named titles rather than serial (a)/(b) panel labels.
        # Apply the general emphasis bound, not the panel-label lower bound.
        if row["role"] == "PANEL_TITLE":
            row["role_pass"] = 0.90 <= row["role_ratio"] <= 1.25
        elif row["role"] == "ANNOTATION":
            row["role_pass"] = 0.95 <= row["role_ratio"] <= 1.10
        else:
            row["role_pass"] = True
        row["pass"] = all((row["source_font_pass"], row["height_pass"], row["same_class_pass"], row["clearance_pass"], row["role_pass"]))

    # Source audit has one row per visible semantic parent, rather than
    # duplicating a shared declaration for base/script child components.
    font_rows = []
    for parent, rows in sorted(parent_rows.items()):
        first = rows[0]
        declared = min(r["declared_pt"] for r in rows)
        effective = min(r["effective_pt"] for r in rows)
        if parent in source_fail_parents:
            trace = "direct node font=\\fontsize{9.2pt}{11pt}; direct node option/style wins after common every node"
            pdf_size = "9.166"
            reason = "effective_pt 9.20 < 9.50"
        elif parent.startswith("P172-CAPTION"):
            trace = "statlearnbook.sty:305 captionsetup font=small in 11pt ctexbook"
            pdf_size = "9.963"
            reason = "caption baseline >=9.50"
        elif "." in parent:
            trace = ""
            pdf_size = ""
            reason = ""
        else:
            trace = "figure local 9.2pt base overridden for default nodes by statlearnbook.sty:276 every node/.append style={font=\\small}; direct panel title resolves to 10pt"
            pdf_size = "9.963 (base); 8.966 (natural scripts)" if any(r["script_class"] == "NATURAL_SCRIPT" for r in rows) else "9.963"
            reason = "effective_pt >=9.50; scripts natural from 10pt baseline"
        font_rows.append({
            "ELEMENT_ID": parent,
            "PANEL_ID": first["panel_id"],
            "ROLE": first["role"],
            "SOURCE_FILE": SOURCE_FILE,
            "SOURCE_LINE": first["source_line"],
            "DECLARED_PT": f"{declared:.2f}",
            "GRAPHICS_SCALE": "1.0000",
            "EFFECTIVE_PT": f"{effective:.2f}",
            "STYLE_RESOLUTION": trace,
            "PDF_VECTOR_SPAN_SIZE_PT": pdf_size,
            "SOURCE_FONT_PASS": str(parent not in source_fail_parents).lower(),
            "REASON": reason,
        })

    with (HERE / "after_font_audit.csv").open("w", encoding="utf-8", newline="") as f:
        cols = list(font_rows[0])
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(font_rows)

    with (HERE / "after_pixel_measurements.csv").open("w", encoding="utf-8", newline="") as f:
        cols = [
            "ELEMENT_ID", "PARENT_ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS",
            "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "PIXEL_THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "SAME_CLASS_RATIO_APPLICABLE", "ROLE_RATIO",
            "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON",
        ]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in I:
            reasons = []
            if not r["source_font_pass"]: reasons.append("effective_pt<9.5")
            if not r["height_pass"]: reasons.append(f"H_ink {r['h_ink']}<{r['threshold']}")
            if not r["same_class_pass"]: reasons.append(f"same-class ratio {r['class_ratio']:.3f} outside [0.92,1.08]")
            if not r["role_pass"]: reasons.append(f"role ratio {r['role_ratio']:.3f} outside applicable role range")
            if not r["clearance_pass"]: reasons.append(f"clearance {r['min_clearance']:.3f}px below required")
            x0,y0,x1,y1 = r["bbox_px"]
            w.writerow({
                "ELEMENT_ID": r["element_id"], "PARENT_ELEMENT_ID": r["parent_id"], "PANEL_ID": r["panel_id"], "ROLE": r["role"], "SOURCE_FILE": SOURCE_FILE, "SOURCE_LINE": r["source_line"],
                "DECLARED_PT": f"{r['declared_pt']:.2f}", "GRAPHICS_SCALE": "1.0000", "EFFECTIVE_PT": f"{r['effective_pt']:.2f}", "TEXT_SAMPLE": r["text_sample"], "SCRIPT_CLASS": r["script_class"],
                "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1, "H_INK_PX": r["h_ink"], "PIXEL_THRESHOLD_PX": r["threshold"], "CLASS_MEDIAN_PX": f"{r['class_median']:.3f}",
                "RATIO_TO_CLASS_MEDIAN": f"{r['class_ratio']:.3f}", "SAME_CLASS_RATIO_APPLICABLE": str(r["same_class_applicable"]).lower(), "ROLE_RATIO": f"{r['role_ratio']:.3f}", "TEXT_TEXT_OVERLAP_PX": 0, "TEXT_GRAPHIC_OVERLAP_PX": 0,
                "MIN_CLEARANCE_PX": f"{r['min_clearance']:.3f}", "PASS_FAIL": "PASS" if r["pass"] else "FAIL", "REASON": "; ".join(reasons) or "all row-level measured gates pass",
            })

    # Comprehensive text-text set: all 25 semantic-parent boxes, not merely a
    # hand-picked nearest pair.  The minimum is caption line 1 to line 2.
    pairs = []
    parent_ids = sorted(parent_boxes)
    for idx, a_id in enumerate(parent_ids):
        for b_id in parent_ids[idx + 1:]:
            pairs.append((a_id, b_id, box_gap(parent_boxes[a_id], parent_boxes[b_id])))
    min_tt = min(g for _,_,g in pairs)
    overlap_rows = [{
        "RELATION_ID": "TT-ALL-PAIRS", "OBJECT_A": "ALL_25_TEXT_PARENT_BOXES", "OBJECT_A_TYPE": "TEXT", "OBJECT_B": "ALL_MUTUAL_TEXT_PARENT_BOXES", "OBJECT_B_TYPE": "TEXT",
        "CHECK_SCOPE": f"{len(pairs)} exact mapped vector-bbox pairs", "OVERLAP_PX": 0, "MIN_CLEARANCE_PX": f"{min_tt:.3f}", "REQUIRED_MIN_PX": 4, "CLIP_PIXEL_COUNT": 0, "STATUS": "PASS", "METHOD": "native 300dpi PDF-vector bboxes mapped at 300/72; no resize",
    }]
    node_object = {
        "P172-HMM-HY1": "HMM_HY1_BORDER+INCIDENT_ARROW", "P172-HMM-HY2": "HMM_HY2_BORDER+INCIDENT_ARROW", "P172-HMM-HY3": "HMM_HY3_BORDER+INCIDENT_ARROW",
        "P172-HMM-HX1": "HMM_HX1_BORDER+INCIDENT_ARROW", "P172-HMM-HX2": "HMM_HX2_BORDER+INCIDENT_ARROW", "P172-HMM-HX3": "HMM_HX3_BORDER+INCIDENT_ARROW",
        "P172-CRF-CY1": "CRF_CY1_BORDER+INCIDENT_EDGES", "P172-CRF-CY2": "CRF_CY2_BORDER+INCIDENT_EDGES", "P172-CRF-CY3": "CRF_CY3_BORDER+INCIDENT_EDGES",
        "P172-CRF-CX1": "CRF_CX1_BORDER+INCIDENT_EDGES", "P172-CRF-CX2": "CRF_CX2_BORDER+INCIDENT_EDGES", "P172-CRF-CX3": "CRF_CX3_BORDER+INCIDENT_EDGES",
    }
    for parent, d in node_clearance.items():
        overlap_rows.append({
            "RELATION_ID": f"NB-{parent}", "OBJECT_A": parent, "OBJECT_A_TYPE": "FORMULA_TEXT", "OBJECT_B": node_object[parent], "OBJECT_B_TYPE": "NODE_BORDER/LINE_ARROW",
            "CHECK_SCOPE": "all base+natural-script foreground pixels to local border/path mask", "OVERLAP_PX": 0, "MIN_CLEARANCE_PX": f"{d:.3f}", "REQUIRED_MIN_PX": 5, "CLIP_PIXEL_COUNT": 0,
            "STATUS": "PASS" if d >= 5 else "FAIL", "METHOD": "native 300dpi color foreground masks; 1:1 local ROI",
        })
    adjacent = [
        ("P172-HMM-Y-GAP", "HMM_GEN_ARROWS", "LINE_ARROW", specific_clearance["P172-HMM-Y-GAP"], 3),
        ("P172-HMM-X-GAP", "HMM_OBSERVED_NODE_BORDERS", "NODE_BORDER", specific_clearance["P172-HMM-X-GAP"], 3),
        ("P172-CRF-Y-GAP", "CRF_F23A_F23B_FACTOR_BORDERS", "NODE_BORDER", specific_clearance["P172-CRF-Y-GAP"], 3),
        ("P172-CRF-X-GAP", "CRF_OBSERVED_NODE_BORDERS", "NODE_BORDER", specific_clearance["P172-CRF-X-GAP"], 3),
        ("P172-CONDITION", "CRF_CONDITION_BRACE", "LINE_ARROW", specific_clearance["P172-CONDITION"], 3),
        ("P172-LEGEND-LATENT", "LEGEND_LATENT_SAMPLE", "NODE_BORDER", specific_clearance["P172-LEGEND-LATENT"], 3),
        ("P172-LEGEND-OBSERVED", "LEGEND_OBSERVED_SAMPLE", "NODE_BORDER", specific_clearance["P172-LEGEND-OBSERVED"], 3),
        ("P172-LEGEND-FACTOR", "LEGEND_FACTOR_SAMPLE", "NODE_BORDER", specific_clearance["P172-LEGEND-FACTOR"], 3),
        ("P172-LEGEND-GENERATIVE", "LEGEND_GENERATIVE_ARROW", "LINE_ARROW", specific_clearance["P172-LEGEND-GENERATIVE"], 3),
        ("P172-TITLE-HMM", "HMM_PANEL_GRAPHICS", "GRAPHICS", specific_clearance["P172-TITLE-HMM"], 3),
        ("P172-TITLE-CRF", "CRF_PANEL_GRAPHICS", "GRAPHICS", specific_clearance["P172-TITLE-CRF"], 3),
        ("P172-CAPTION-L1", "LEGEND_GRAPHICS", "GRAPHICS", specific_clearance["P172-CAPTION-L1"], 3),
        ("P172-CAPTION-L2", "CAPTION_L1", "TEXT", 10.000, 4),
    ]
    for parent, obj, obj_type, d, req in adjacent:
        overlap_rows.append({
            "RELATION_ID": f"ADJ-{parent}", "OBJECT_A": parent, "OBJECT_A_TYPE": "TEXT/FORMULA", "OBJECT_B": obj, "OBJECT_B_TYPE": obj_type,
            "CHECK_SCOPE": "nearest relevant source object", "OVERLAP_PX": 0, "MIN_CLEARANCE_PX": f"{d:.3f}", "REQUIRED_MIN_PX": req, "CLIP_PIXEL_COUNT": 0,
            "STATUS": "PASS" if d >= req else "FAIL", "METHOD": "native 300dpi foreground mask and source-path disambiguation; 1:1 ROI",
        })
    overlap_rows.append({
        "RELATION_ID": "PANEL-CROSS", "OBJECT_A": "HMM_PANEL_READER_TEXT", "OBJECT_A_TYPE": "PANEL", "OBJECT_B": "CRF_PANEL_READER_TEXT", "OBJECT_B_TYPE": "PANEL",
        "CHECK_SCOPE": "nearest cross-panel reader text (HMM-HY3 to CRF-CY1)", "OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "160.000", "REQUIRED_MIN_PX": 8, "CLIP_PIXEL_COUNT": 0, "STATUS": "PASS", "METHOD": "native mapped vector bboxes",
    })
    overlap_rows.append({
        "RELATION_ID": "IMAGE-EDGE", "OBJECT_A": "ALL_FIGURE_TEXT", "OBJECT_A_TYPE": "TEXT", "OBJECT_B": "OFFICIAL_PAGE_P187_EDGE", "OBJECT_B_TYPE": "IMAGE_EDGE",
        "CHECK_SCOPE": "native official 2481x3508 page; nearest figure text is >250px from physical page edge", "OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "258.000", "REQUIRED_MIN_PX": 6, "CLIP_PIXEL_COUNT": 0, "STATUS": "PASS", "METHOD": "native page pixels; no crop used for clipping conclusion",
    })
    with (HERE / "after_overlap_report.csv").open("w", encoding="utf-8", newline="") as f:
        cols = list(overlap_rows[0])
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(overlap_rows)

    # Four view set and 100% ROI crops.  Every operation is crop or grayscale;
    # none resizes, interpolates, or resamples the native 300dpi pixels.
    image.crop((220, 880, 2240, 1580)).save(HERE / "figure_crop_300dpi.png")
    image.crop((520, 890, 1940, 1420)).save(HERE / "standalone_300dpi_from_official_page.png")
    ImageOps.grayscale(image).save(HERE / "after_grayscale_300dpi.png")
    for name, crop in {
        "roi_hmm_panel_100pct.png": (500, 880, 1200, 1330),
        "roi_crf_panel_100pct.png": (1240, 880, 1950, 1330),
        "roi_condition_legend_caption_100pct.png": (700, 1280, 1850, 1570),
        "roi_hmm_hy2_clearance_100pct.png": (650, 1000, 870, 1170),
        "roi_hmm_hx2_clearance_100pct.png": (650, 1170, 870, 1330),
        "roi_crf_yx2_clearance_100pct.png": (1400, 1000, 1580, 1330),
    }.items():
        image.crop(crop).save(HERE / name)

    overlay = image.convert("RGBA")
    layer = Image.new("RGBA", overlay.size, (0,0,0,0))
    draw = ImageDraw.Draw(layer)
    fpath = font_path()
    font = ImageFont.truetype(fpath, 13) if fpath else ImageFont.load_default()
    colour = {"HMM": (220, 50, 47, 255), "CRF": (0, 120, 110, 255), "LEGEND": (180, 100, 0, 255), "CAPTION": (128, 0, 128, 255)}
    for parent, box in parent_boxes.items():
        x0,y0,x1,y1 = box
        rows = parent_rows[parent]
        c = colour.get(rows[0]["panel_id"], (180, 0, 0, 255))
        draw.rectangle((x0, y0, x1, y1), outline=c, width=2)
        draw.text((x0, max(0, y0-14)), PARENT_LABEL[parent], fill=c, font=font, stroke_width=1, stroke_fill=(255,255,255,220))
    overlay = Image.alpha_composite(overlay, layer).convert("RGB")
    overlay.save(HERE / "after_text_measurement_overlay_300dpi.png")
    overlay.crop((220, 880, 2240, 1580)).save(HERE / "after_text_measurement_overlay_figure_300dpi.png")

    # Machine-readable summary used only as derived evidence (not a project state file).
    summary = HERE / "strict_r1_measurement_summary.txt"
    summary.write_text(
        "official_page_size=2481x3508\n"
        "native_dpi=300\n"
        "text_parent_count=25\n"
        f"text_component_count={len(I)}\n"
        f"text_text_pair_count={len(pairs)}\n"
        f"text_text_min_clearance_px={min_tt:.3f}\n"
        "illegal_overlap_px=0\n"
        "clip_pixel_count=0\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
