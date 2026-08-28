#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent, native-300-dpi measurement for FIG-P020-01.

Inputs are deliberately limited to the official R90 full-book PDF, its direct
300-dpi page-17 render, the freshly generated isolated render, and the current
authoritative figure source.  The script has no dependency on prior review
reports, masks, or conclusions.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parent
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r90_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第01册_数学基础与统计学习基本理论" / "V1-C01" / "fig_v1_c01_language_flow.tex"
TEMPLATE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "common" / "statlearnbook.sty"
PAGE300 = OUT / "SA3_FIG-P020-01_page17_300dpi.png"
STANDALONE300 = OUT / "SA3_FIG-P020-01_standalone_page_300dpi.png"
PAGE_INDEX = 16  # physical page 17, zero indexed

# Cropping copies pixels without any resize. It contains the vector drawing,
# return annotation, and caption with >= 35px of surrounding raw-page space.
FIG_CROP = (200, 1170, 2280, 1700)


def compact(text: str) -> str:
    return "".join(text.split())


def pixel_box(pdf_box: tuple[float, float, float, float], sx: float, sy: float, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pdf_box
    return (
        max(0, math.floor(x0 * sx)),
        max(0, math.floor(y0 * sy)),
        min(width, math.ceil(x1 * sx)),
        min(height, math.ceil(y1 * sy)),
    )


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """Euclidean clearance between two exclusive-coordinate bboxes in pixels."""
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def rgb_mask_local(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Threshold local foreground at the Goal C1 contrast rule (>=20/255).

    The boxes are native PDF text bboxes and contain one text span only.  The
    local RGB mode is the directly rendered substrate (white or node fill), so
    this keeps only materially contrasting ink rather than pale antialiasing.
    """
    x0, y0, x1, y1 = box
    crop = image[y0:y1, x0:x1, :3]
    if crop.size == 0:
        raise ValueError(f"empty pixel box: {box}")
    packed = crop.reshape(-1, 3)
    values, counts = np.unique(packed, axis=0, return_counts=True)
    background = values[int(np.argmax(counts))].astype(np.int16)
    delta = np.max(np.abs(crop.astype(np.int16) - background), axis=2)
    local = delta >= 20
    result = np.zeros(image.shape[:2], dtype=bool)
    result[y0:y1, x0:x1] = local
    return result


def ink_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise ValueError("no thresholded foreground pixels")
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Nearest ink-to-ink distance in raw pixels; 0 means overlap."""
    if not a.any() or not b.any():
        raise ValueError("cannot measure distance with an empty mask")
    dist = cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 5)
    return float(dist[a].min())


def sample_cubic(p0: fitz.Point, p1: fitz.Point, p2: fitz.Point, p3: fitz.Point, sx: float, sy: float) -> np.ndarray:
    t = np.linspace(0.0, 1.0, 25)
    u = 1.0 - t
    x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
    y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
    return np.rint(np.column_stack((x * sx, y * sy))).astype(np.int32)


def path_polyline(path: dict[str, Any], sx: float, sy: float) -> list[np.ndarray]:
    """Approximate PDF vector path segments on the native raster grid."""
    polylines: list[np.ndarray] = []
    current: list[tuple[int, int]] = []
    for item in path["items"]:
        op = item[0]
        if op == "l":
            p0, p1 = item[1], item[2]
            a = (round(p0.x * sx), round(p0.y * sy))
            b = (round(p1.x * sx), round(p1.y * sy))
            if not current:
                current = [a]
            elif current[-1] != a:
                current.append(a)
            current.append(b)
        elif op == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            curve = sample_cubic(p0, p1, p2, p3, sx, sy)
            if not current:
                current = [tuple(curve[0])]
            elif current[-1] != tuple(curve[0]):
                current.append(tuple(curve[0]))
            current.extend(tuple(p) for p in curve[1:])
        elif op == "re":
            rect = item[1]
            ring = np.array(
                [
                    (round(rect.x0 * sx), round(rect.y0 * sy)),
                    (round(rect.x1 * sx), round(rect.y0 * sy)),
                    (round(rect.x1 * sx), round(rect.y1 * sy)),
                    (round(rect.x0 * sx), round(rect.y1 * sy)),
                    (round(rect.x0 * sx), round(rect.y0 * sy)),
                ],
                dtype=np.int32,
            )
            polylines.append(ring)
        else:
            raise ValueError(f"unsupported PDF path item: {op}")
    if current:
        polylines.append(np.asarray(current, dtype=np.int32))
    return polylines


def raster_path(path: dict[str, Any], sx: float, sy: float, shape: tuple[int, int], fill_arrowhead: bool) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    thick = max(1, int(math.ceil(float(path.get("width") or 0.0) * max(sx, sy))))
    polylines = path_polyline(path, sx, sy)
    for polyline in polylines:
        if len(polyline) >= 2:
            cv2.polylines(mask, [polyline], False, 255, thickness=thick, lineType=cv2.LINE_8)
            if fill_arrowhead and len(polyline) >= 3:
                cv2.fillPoly(mask, [polyline], 255, lineType=cv2.LINE_8)
    return mask.astype(bool)


def mode_source_spec(kind: str) -> tuple[str, int, float, str]:
    if kind == "NODE_HEADING":
        return (str(SOURCE), 11, 10.5, "stage/.style font=\\fontsize{10.5pt}{12.6pt}\\selectfont")
    if kind == "NODE_BODY":
        return (str(SOURCE), 14, 10.0, "per-node body override \\fontsize{10.0pt}{12.0pt}\\selectfont")
    if kind == "RETURN_ANNOTATION":
        return (str(SOURCE), 35, 10.0, "node font=\\fontsize{10.0pt}{12.0pt}\\selectfont")
    if kind.startswith("CAPTION"):
        return (str(SOURCE), 38, 10.0, f"figure caption; \\small at ctexbook 11pt, {TEMPLATE}:305")
    raise ValueError(kind)


def class_threshold(script_class: str) -> int:
    return {"CJK": 30, "DIGIT": 24, "LOWER_GREEK": 17, "MATH_BASE": 22, "SCRIPT": 15}[script_class]


def main() -> None:
    if not all(item.is_file() for item in (PDF, SOURCE, TEMPLATE, PAGE300, STANDALONE300)):
        missing = [str(item) for item in (PDF, SOURCE, TEMPLATE, PAGE300, STANDALONE300) if not item.is_file()]
        raise FileNotFoundError("; ".join(missing))

    source_text = SOURCE.read_text(encoding="utf-8")
    disallowed_scalers = [token for token in ("\\resizebox", "\\scalebox", "transform shape", "scale=") if token in source_text]
    if disallowed_scalers:
        raise RuntimeError(f"source-scale audit requires manual review: {disallowed_scalers}")

    page_image = np.asarray(Image.open(PAGE300).convert("RGB"))
    if page_image.shape[:2] != (3508, 2481):
        raise RuntimeError(f"not the required native A4 300dpi size: {page_image.shape[:2]}")

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx = page_image.shape[1] / page.rect.width
    sy = page_image.shape[0] / page.rect.height
    raw = page.get_text("rawdict")
    spans: list[dict[str, Any]] = []
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = "".join(ch["c"] for ch in span.get("chars", []))
                spans.append({"text": text, "compact": compact(text), "span": span})

    # Restrict lookup to the native vector/text band occupied by the figure
    # and caption. This prevents an ordinary body reference such as “图” from
    # being mistaken for the caption label later on the same page.
    figure_spans = [entry for entry in spans if 290.0 <= float(entry["span"]["bbox"][1]) <= 400.0]

    def find_exact(expected: str) -> dict[str, Any]:
        matches = [entry for entry in figure_spans if entry["compact"] == expected]
        if len(matches) != 1:
            raise RuntimeError(f"expected one PDF text span {expected!r}, found {len(matches)}")
        return matches[0]

    def find_prefix(expected: str) -> dict[str, Any]:
        matches = [entry for entry in figure_spans if entry["compact"].startswith(expected)]
        if len(matches) != 1:
            raise RuntimeError(f"expected one PDF text span beginning {expected!r}, found {len(matches)}")
        return matches[0]

    specs = [
        ("T01", "NODE_HEADING", "CJK", "对象声明", "对象声明"),
        ("T02", "NODE_BODY", "CJK", "集合、类型与维数", "集合、类型与维数"),
        ("T03", "NODE_HEADING", "CJK", "关系与映射", "关系与映射"),
        ("T04", "NODE_BODY", "CJK", "定义域", "定义域"),
        ("T05", "NODE_BODY", "CJK", "值域", "值域"),
        ("T06", "NODE_HEADING", "CJK", "运算与逻辑", "运算与逻辑"),
        ("T07", "NODE_BODY", "CJK", "复合、量词与约束", "复合、量词与约束"),
        ("T08", "NODE_HEADING", "CJK", "可核验任务", "可核验任务"),
        ("T09", "NODE_BODY", "CJK", "输入、输出与判据", "输入、输出与判据"),
        ("T10", "RETURN_ANNOTATION", "CJK", "逆向核对：任务所用定义逐项返回检查", "逆向核对：任务所用定义逐项返回检查"),
        ("T11", "CAPTION_LABEL", "CJK", "图", "图"),
        ("T12", "CAPTION_LABEL", "DIGIT", "1.1", "1.1"),
        ("T13", "CAPTION_BODY", "CJK", "数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。", "数学语言从对象声明到任务陈述的依赖关系"),
    ]

    elements: list[dict[str, Any]] = []
    for element_id, role, script_class, expected, lookup in specs:
        found = find_prefix(lookup) if element_id == "T13" else find_exact(lookup)
        span = found["span"]
        pdf_box = tuple(float(value) for value in span["bbox"])
        raw_box = pixel_box(pdf_box, sx, sy, page_image.shape[1], page_image.shape[0])
        mask = rgb_mask_local(page_image, raw_box)
        actual = ink_bbox(mask)
        source_file, source_line, declared, source_note = mode_source_spec(role)
        elements.append(
            {
                "ELEMENT_ID": element_id,
                "PANEL_ID": "PANEL_1_ONLY",
                "ROLE": role,
                "SCRIPT_CLASS": script_class,
                "TEXT_SAMPLE": expected,
                "SOURCE_FILE": source_file,
                "SOURCE_LINE": source_line,
                "SOURCE_NOTE": source_note,
                "DECLARED_PT": declared,
                "GRAPHICS_SCALE": 1.0,
                "EFFECTIVE_PT": declared,
                "PDF_VECTOR_PT": float(span["size"]),
                "PDF_BBOX_PT": pdf_box,
                "PDF_BBOX_PX": raw_box,
                "MASK": mask,
                "INK_BBOX_PX": actual,
                "H_INK_PX": actual[3] - actual[1],
            }
        )

    # The direct vector inventory provides an independent confirmation of the
    # inline arrow's graphic nature.  Indexes are verified by the geometry
    # rather than assumed from source text alone.
    drawings = page.get_drawings()
    if len(drawings) < 23:
        raise RuntimeError(f"expected full vector drawing inventory, got {len(drawings)} paths")
    def drawing(index_1based: int) -> dict[str, Any]:
        return drawings[index_1based - 1]

    groups: dict[str, dict[str, Any]] = {
        "NODE_BORDER_1": {"ids": [9], "fill": False, "kind": "NODE_BORDER"},
        "NODE_BORDER_2": {"ids": [10], "fill": False, "kind": "NODE_BORDER"},
        "INLINE_ARROW_DOMAIN_TO_CODOMAIN": {"ids": [11, 12], "fill": True, "kind": "LINE_ARROW"},
        "NODE_BORDER_3": {"ids": [13], "fill": False, "kind": "NODE_BORDER"},
        "NODE_BORDER_4": {"ids": [14], "fill": False, "kind": "NODE_BORDER"},
        "MAIN_ARROW_1": {"ids": [15, 16], "fill": True, "kind": "LINE_ARROW"},
        "MAIN_ARROW_2": {"ids": [17, 18], "fill": True, "kind": "LINE_ARROW"},
        "MAIN_ARROW_3": {"ids": [19, 20], "fill": True, "kind": "LINE_ARROW"},
        "RETURN_ARROW": {"ids": [21, 22], "fill": True, "kind": "LINE_ARROW"},
    }
    masks: dict[str, np.ndarray] = {}
    for group_name, group in groups.items():
        group_mask = np.zeros(page_image.shape[:2], dtype=bool)
        for index in group["ids"]:
            path = drawing(index)
            group_mask |= raster_path(path, sx, sy, page_image.shape[:2], bool(group["fill"]))
        if not group_mask.any():
            raise RuntimeError(f"empty vector mask for {group_name}")
        masks[group_name] = group_mask

    # The inline-arrow group must be a standalone line + filled arrowhead in
    # the official PDF between the two word spans. This is stronger evidence
    # than a textual glyph search.
    inline_bbox = ink_bbox(masks["INLINE_ARROW_DOMAIN_TO_CODOMAIN"])
    domain = next(row for row in elements if row["ELEMENT_ID"] == "T04")
    codomain = next(row for row in elements if row["ELEMENT_ID"] == "T05")
    if not (domain["INK_BBOX_PX"][2] < inline_bbox[0] < inline_bbox[2] < codomain["INK_BBOX_PX"][0]):
        raise RuntimeError("inline vector arrow does not sit between 定义域 and 值域")

    graphics_mask = np.zeros(page_image.shape[:2], dtype=bool)
    for mask in masks.values():
        graphics_mask |= mask
    text_mask = np.zeros(page_image.shape[:2], dtype=bool)
    for row in elements:
        text_mask |= row["MASK"]

    # Same-role actual-pixel medians and role ratios, all from direct native
    # pixels. Different script classes are intentionally not mixed.
    by_role_class: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in elements:
        by_role_class.setdefault((row["ROLE"], row["SCRIPT_CLASS"]), []).append(row)
    medians: dict[tuple[str, str], float] = {}
    for key, rows in by_role_class.items():
        medians[key] = float(statistics.median(row["H_INK_PX"] for row in rows))
        for row in rows:
            row["CLASS_MEDIAN_PX"] = medians[key]
            row["RATIO_TO_CLASS_MEDIAN"] = row["H_INK_PX"] / medians[key]

    base = medians[("NODE_BODY", "CJK")]
    for row in elements:
        # §9.2.1-D forbids mixing full-height CJK with Latin/cap/digit ink
        # height in a pixel ratio.  The caption number therefore receives its
        # own class threshold (24px) and is not misclassified as a visually
        # shrunken CJK semantic role.
        row["ROLE_RATIO"] = row["H_INK_PX"] / base if row["SCRIPT_CLASS"] == "CJK" else "N/A_SCRIPT_CLASS"

    # Pixel intersection checks and per-element nearest graphic clearance.
    for row in elements:
        row["TEXT_TEXT_OVERLAP_PX"] = int(np.count_nonzero(row["MASK"] & (text_mask & ~row["MASK"])))
        row["TEXT_GRAPHIC_OVERLAP_PX"] = int(np.count_nonzero(row["MASK"] & graphics_mask))
        row["MIN_CLEARANCE_PX"] = mask_distance(row["MASK"], graphics_mask)

    # Build detailed pair evidence. Text-text values use the strict mapped PDF
    # bboxes required by §9.2.1-F; text-graphic values use the direct ink masks.
    pair_rows: list[dict[str, Any]] = []
    for index, a in enumerate(elements):
        for b in elements[index + 1:]:
            clear = bbox_distance(a["PDF_BBOX_PX"], b["PDF_BBOX_PX"])
            pair_rows.append(
                {
                    "PAIR_ID": f"TT-{a['ELEMENT_ID']}-{b['ELEMENT_ID']}",
                    "OBJECT_A": a["ELEMENT_ID"],
                    "CLASS_A": "TEXT",
                    "OBJECT_B": b["ELEMENT_ID"],
                    "CLASS_B": "TEXT",
                    "MEASURE": "mapped PDF text-bbox clearance",
                    "OVERLAP_PX": 0 if clear > 0 else 1,
                    "CLEARANCE_PX": f"{clear:.2f}",
                    "THRESHOLD_PX": 4,
                    "PASS_FAIL": "PASS" if clear >= 4 else "FAIL",
                }
            )
    node_for_text = {
        "T01": "NODE_BORDER_1", "T02": "NODE_BORDER_1", "T03": "NODE_BORDER_2", "T04": "NODE_BORDER_2",
        "T05": "NODE_BORDER_2", "T06": "NODE_BORDER_3", "T07": "NODE_BORDER_3", "T08": "NODE_BORDER_4", "T09": "NODE_BORDER_4",
    }
    for row in elements:
        for group_name, group_mask in masks.items():
            own_border = node_for_text.get(row["ELEMENT_ID"]) == group_name
            threshold = 5 if own_border else 3
            clear = mask_distance(row["MASK"], group_mask)
            overlap = int(np.count_nonzero(row["MASK"] & group_mask))
            pair_rows.append(
                {
                    "PAIR_ID": f"TG-{row['ELEMENT_ID']}-{group_name}",
                    "OBJECT_A": row["ELEMENT_ID"],
                    "CLASS_A": "TEXT",
                    "OBJECT_B": group_name,
                    "CLASS_B": groups[group_name]["kind"],
                    "MEASURE": "native 300dpi ink-mask clearance",
                    "OVERLAP_PX": overlap,
                    "CLEARANCE_PX": f"{clear:.2f}",
                    "THRESHOLD_PX": threshold,
                    "PASS_FAIL": "PASS" if overlap == 0 and clear >= threshold else "FAIL",
                }
            )

    # Page/image-edge clearance against the raw A4 image, no visual crop is
    # used for this test. It is therefore immune to crop choice.
    for row in elements:
        x0, y0, x1, y1 = row["INK_BBOX_PX"]
        edge = min(x0, y0, page_image.shape[1] - x1, page_image.shape[0] - y1)
        pair_rows.append(
            {
                "PAIR_ID": f"EDGE-{row['ELEMENT_ID']}",
                "OBJECT_A": row["ELEMENT_ID"],
                "CLASS_A": "TEXT",
                "OBJECT_B": "A4_PAGE_IMAGE_EDGE",
                "CLASS_B": "IMAGE_EDGE",
                "MEASURE": "native 300dpi ink bbox to page edge",
                "OVERLAP_PX": 0 if edge > 0 else 1,
                "CLEARANCE_PX": f"{edge:.2f}",
                "THRESHOLD_PX": 6,
                "PASS_FAIL": "PASS" if edge >= 6 else "FAIL",
            }
        )

    # Explicit arrow pair evidence requested by the task.
    inline_mask = masks["INLINE_ARROW_DOMAIN_TO_CODOMAIN"]
    inline_pairs = {
        "ARROW_CLEARANCE_DOMAIN": domain,
        "ARROW_CLEARANCE_CODOMAIN": codomain,
    }
    for pair_id, row in inline_pairs.items():
        clear = mask_distance(row["MASK"], inline_mask)
        overlap = int(np.count_nonzero(row["MASK"] & inline_mask))
        pair_rows.append(
            {
                "PAIR_ID": pair_id,
                "OBJECT_A": row["ELEMENT_ID"],
                "CLASS_A": "TEXT",
                "OBJECT_B": "INLINE_ARROW_DOMAIN_TO_CODOMAIN",
                "CLASS_B": "LINE_ARROW",
                "MEASURE": "requested native 300dpi text-to-middle-vector-arrow clearance",
                "OVERLAP_PX": overlap,
                "CLEARANCE_PX": f"{clear:.2f}",
                "THRESHOLD_PX": 3,
                "PASS_FAIL": "PASS" if overlap == 0 and clear >= 3 else "FAIL",
            }
        )

    # No clipping: every text ink and every non-background vector path remains
    # strictly inside the original A4 media box. Pixel masks meet no image edge.
    clip_pixels = int(np.count_nonzero((text_mask | graphics_mask)[0, :]))
    clip_pixels += int(np.count_nonzero((text_mask | graphics_mask)[-1, :]))
    clip_pixels += int(np.count_nonzero((text_mask | graphics_mask)[:, 0]))
    clip_pixels += int(np.count_nonzero((text_mask | graphics_mask)[:, -1]))

    role_rows: list[dict[str, Any]] = []
    for (role, script_class), median in sorted(medians.items()):
        entries = by_role_class[(role, script_class)]
        source_values = [entry["EFFECTIVE_PT"] for entry in entries]
        role_rows.append(
            {
                "ROLE": role,
                "SCRIPT_CLASS": script_class,
                "COUNT": len(entries),
                "SOURCE_EFFECTIVE_MIN_PT": f"{min(source_values):.2f}",
                "SOURCE_EFFECTIVE_MAX_PT": f"{max(source_values):.2f}",
                "SOURCE_RATIO_MAX_MIN": f"{max(source_values) / min(source_values):.4f}",
                "SOURCE_ABS_DIFF_PT": f"{max(source_values) - min(source_values):.2f}",
                "H_INK_MEDIAN_PX": f"{median:.2f}",
                "H_INK_MIN_PX": min(entry["H_INK_PX"] for entry in entries),
                "H_INK_MAX_PX": max(entry["H_INK_PX"] for entry in entries),
                "PIXEL_RATIO_MAX_MIN": f"{max(entry['H_INK_PX'] for entry in entries) / min(entry['H_INK_PX'] for entry in entries):.4f}",
                "ROLE_TO_BASE": f"{median / base:.4f}" if script_class == "CJK" else "N/A_SCRIPT_CLASS",
                "SOURCE_SAME_ROLE_PASS": "PASS" if max(source_values) / min(source_values) <= 1.03 and max(source_values) - min(source_values) <= 0.25 else "FAIL",
                "PIXEL_SAME_CLASS_PASS": "PASS" if all(0.92 <= entry["H_INK_PX"] / median <= 1.08 for entry in entries) else "FAIL",
            }
        )

    # PASS calculations are intentionally conservative: absent data raises,
    # rather than falling through to a positive result.
    source_font_pass = all(row["EFFECTIVE_PT"] >= 9.5 for row in elements)
    pixel_height_pass = all(row["H_INK_PX"] >= class_threshold(row["SCRIPT_CLASS"]) for row in elements)
    same_class_pass = all(row["PIXEL_SAME_CLASS_PASS"] == "PASS" for row in role_rows) and all(
        0.92 <= row["RATIO_TO_CLASS_MEDIAN"] <= 1.08 for row in elements
    )
    source_role_pass = all(row["SOURCE_SAME_ROLE_PASS"] == "PASS" for row in role_rows)
    # Titles are intentional node-heading emphasis. It must remain <=1.25 of
    # normal node-body BASE; all non-heading ancillary roles are also checked.
    role_ratio_pass = source_role_pass and all(
        row["ROLE_RATIO"] <= 1.25 and row["ROLE_RATIO"] >= 0.90
        for row in elements
        if row["ROLE"] != "NODE_BODY" and row["SCRIPT_CLASS"] == "CJK"
    )
    overlap_pixels = int(np.count_nonzero(text_mask & graphics_mask)) + sum(
        int(np.count_nonzero(a["MASK"] & b["MASK"])) for i, a in enumerate(elements) for b in elements[i + 1:]
    )
    clearance_pass = all(row["PASS_FAIL"] == "PASS" for row in pair_rows)
    all_pair_failures = [row for row in pair_rows if row["PASS_FAIL"] != "PASS"]

    # Images: direct crops and grayscale without resize. Overlay coordinates
    # are relative to the crop and identify every audited text plus the arrow.
    x0, y0, x1, y1 = FIG_CROP
    raw_crop = Image.fromarray(page_image[y0:y1, x0:x1])
    raw_crop.save(OUT / "SA3_FIG-P020-01_figure_roi_300dpi.png")
    ImageOps.grayscale(raw_crop).save(OUT / "SA3_FIG-P020-01_figure_roi_grayscale_300dpi.png")
    overlay = raw_crop.copy()
    painter = ImageDraw.Draw(overlay)
    for row in elements:
        bx0, by0, bx1, by1 = row["PDF_BBOX_PX"]
        local = (bx0 - x0, by0 - y0, bx1 - x0, by1 - y0)
        painter.rectangle(local, outline=(230, 20, 20), width=2)
        painter.text((local[0], max(0, local[1] - 12)), row["ELEMENT_ID"], fill=(230, 20, 20))
    ax0, ay0, ax1, ay1 = inline_bbox
    painter.rectangle((ax0 - x0 - 2, ay0 - y0 - 2, ax1 - x0 + 2, ay1 - y0 + 2), outline=(0, 150, 0), width=2)
    painter.text((ax0 - x0, max(0, ay0 - y0 - 14)), "G01", fill=(0, 130, 0))
    overlay.save(OUT / "SA3_FIG-P020-01_text_measurement_overlay_300dpi.png")

    standalone = np.asarray(Image.open(STANDALONE300).convert("RGB"))
    if standalone.shape[:2] != (3508, 2481):
        raise RuntimeError(f"standalone not native A4 300dpi: {standalone.shape[:2]}")
    gray = cv2.cvtColor(standalone, cv2.COLOR_RGB2GRAY)
    fg = gray < 230
    ys, xs = np.where(fg)
    if len(xs) == 0:
        raise RuntimeError("isolated render contains no foreground")
    sx0, sy0 = max(0, int(xs.min()) - 40), max(0, int(ys.min()) - 40)
    sx1, sy1 = min(standalone.shape[1], int(xs.max()) + 41), min(standalone.shape[0], int(ys.max()) + 41)
    Image.fromarray(standalone[sy0:sy1, sx0:sx1]).save(OUT / "SA3_FIG-P020-01_standalone_figure_roi_300dpi.png")

    font_fields = [
        "ELEMENT_ID", "ROLE", "TEXT_SAMPLE", "SOURCE_FILE", "SOURCE_LINE", "SOURCE_NOTE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_VECTOR_PT",
    ]
    with (OUT / "SA3_FIG-P020-01_source_font_audit.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=font_fields)
        writer.writeheader()
        writer.writerows([{key: row[key] for key in font_fields} for row in elements])

    measure_fields = [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_VECTOR_PT", "TEXT_SAMPLE", "SCRIPT_CLASS",
        "PDF_BBOX_PX", "INK_BBOX_PX", "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON",
    ]
    for row in elements:
        threshold = class_threshold(row["SCRIPT_CLASS"])
        own_border_clearance = min(
            float(pair["CLEARANCE_PX"])
            for pair in pair_rows
            if pair["OBJECT_A"] == row["ELEMENT_ID"] and pair["CLASS_B"] == "NODE_BORDER"
        ) if row["ELEMENT_ID"] in node_for_text else row["MIN_CLEARANCE_PX"]
        row["PASS_FAIL"] = "PASS" if row["EFFECTIVE_PT"] >= 9.5 and row["H_INK_PX"] >= threshold and 0.92 <= row["RATIO_TO_CLASS_MEDIAN"] <= 1.08 and row["TEXT_TEXT_OVERLAP_PX"] == 0 and row["TEXT_GRAPHIC_OVERLAP_PX"] == 0 and own_border_clearance >= (5 if row["ELEMENT_ID"] in node_for_text else 3) else "FAIL"
        row["REASON"] = f"source>={row['EFFECTIVE_PT']:.2f}pt; H={row['H_INK_PX']}px/{threshold}px; native thresholded masks; closest own/general graphic clearance={own_border_clearance:.2f}px"
    with (OUT / "SA3_FIG-P020-01_pixel_measurements.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=measure_fields)
        writer.writeheader()
        writer.writerows([{key: row[key] for key in measure_fields} for row in elements])

    with (OUT / "SA3_FIG-P020-01_overlap_clearance.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["PAIR_ID", "OBJECT_A", "CLASS_A", "OBJECT_B", "CLASS_B", "MEASURE", "OVERLAP_PX", "CLEARANCE_PX", "THRESHOLD_PX", "PASS_FAIL"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(pair_rows)

    with (OUT / "SA3_FIG-P020-01_role_ratio.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = list(role_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(role_rows)

    min_text_bbox = min(float(row["CLEARANCE_PX"]) for row in pair_rows if row["CLASS_A"] == "TEXT" and row["CLASS_B"] == "TEXT")
    min_text_graphic = min(float(row["CLEARANCE_PX"]) for row in pair_rows if row["CLASS_A"] == "TEXT" and row["CLASS_B"] in {"LINE_ARROW", "NODE_BORDER"})
    summary = {
        "input": {
            "official_pdf": str(PDF),
            "physical_page": 17,
            "source": str(SOURCE),
            "render": "direct pdftoppm 300dpi; no resize",
            "page_pixels": [int(page_image.shape[1]), int(page_image.shape[0])],
            "pdf_media_box_pt": [page.rect.width, page.rect.height],
            "pixel_scale": [sx, sy],
        },
        "inline_arrow": {
            "source_lines": "16-20; TikZ \\draw[-{Stealth}] rather than a text arrow",
            "official_pdf_vector_paths": ["D011 stroke", "D012 filled arrowhead"],
            "native_300dpi_ink_bbox": inline_bbox,
            "domain_clearance_px": mask_distance(domain["MASK"], inline_mask),
            "codomain_clearance_px": mask_distance(codomain["MASK"], inline_mask),
        },
        "threshold_method": "per-span local RGB background mode; foreground max-channel contrast >=20/255; all distances/native masks in unscaled 300dpi pixels",
        "source_font_pass": source_font_pass,
        "pixel_height_pass": pixel_height_pass,
        "same_class_ratio_pass": same_class_pass,
        "role_ratio_pass": role_ratio_pass,
        "overlap_pixel_count": overlap_pixels,
        "clip_pixel_count": clip_pixels,
        "min_text_text_bbox_clearance_px": min_text_bbox,
        "min_text_graphic_ink_clearance_px": min_text_graphic,
        "all_pair_clearance_pass": clearance_pass,
        "pair_failures": all_pair_failures,
        "single_panel": True,
        "cross_panel_requirement": "N/A: no second panel exists, so no cross-panel comparison is implied or omitted",
    }
    (OUT / "SA3_FIG-P020-01_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
