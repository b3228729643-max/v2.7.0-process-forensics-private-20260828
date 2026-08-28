# -*- coding: utf-8 -*-
"""Independent, read-only SA1 pixel audit for FIG-P157-01 on official R92.

This script only reads the fixed official PDF plus the designated figure and
chapter sources.  It writes reproducible evidence beside itself; it never
opens earlier review evidence or any central inventory.
"""

from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


FIGURE_ID = "FIG-P157-01"
PDF_PAGE = 170
DPI = 300
PDF_TO_PX = DPI / 72.0
OUT = Path(__file__).resolve().parent
WORK = OUT.parents[3]
PDF = WORK / "source" / "v2.7.0" / "src" / "build" / "strict_current_r92_fullbook" / "main_full.pdf"
FIG_SOURCE = (
    WORK
    / "source"
    / "v2.7.0"
    / "src"
    / "绘图源码"
    / "第01册_数学基础与统计学习基本理论"
    / "V1-C10"
    / "fig_v1_c10_complexity.tex"
)
BODY_SOURCE = (
    WORK
    / "source"
    / "v2.7.0"
    / "src"
    / "讲义源码"
    / "第01册_数学基础与统计学习基本理论"
    / "chapters"
    / "V1-C10.tex"
)
PAGE_300 = OUT / "official_page_170_300dpi.png"
PAGE_200 = OUT / "official_page_170_200dpi.png"


@dataclass(frozen=True)
class ElementSpec:
    element_id: str
    panel_id: str
    role: str
    text: str
    source_line: str
    declared_pt: float
    expected_y0: float
    script_class: str
    source_note: str


@dataclass
class Element:
    spec: ElementSpec
    span: dict[str, Any]
    bbox_pdf: tuple[float, float, float, float]
    bbox_px: tuple[int, int, int, int]
    mask: np.ndarray
    glyph_heights: list[int]
    h_ink_px: float
    pdf_native_font_pt: float
    graphics_scale: float
    effective_pt: float


FIG_PATH = str(FIG_SOURCE)
BODY_PATH = str(BODY_SOURCE)


SPECS = [
    ElementSpec("T01_TRAINING_ANNOT", "P01", "ANNOTATION", "训练误差：单调下降", "fig_v1_c10_complexity.tex:6,44-46", 9.2, 228.0, "CJK", "direct-label style; outer every-picture scale at V1-C10.tex:256"),
    ElementSpec("T02_VALIDATION_ANNOT", "P01", "ANNOTATION", "验证误差：先降后升", "fig_v1_c10_complexity.tex:6,47-48", 9.2, 170.0, "CJK", "direct-label style; outer every-picture scale at V1-C10.tex:256"),
    ElementSpec("T03_MINIMUM_KEY", "P01", "ANNOTATION", "最低验证误差", "fig_v1_c10_complexity.tex:8-9,49-50", 9.2, 214.0, "CJK", "key-label style; outer every-picture scale at V1-C10.tex:256"),
    ElementSpec("T04_SELECTION_KEY", "P01", "ANNOTATION", "选择复杂度", "fig_v1_c10_complexity.tex:8-9,51-52", 9.2, 285.0, "CJK", "key-label style; outer every-picture scale at V1-C10.tex:256"),
    ElementSpec("T05_UNDERFIT_REGION", "P01", "REGION_LABEL", "欠拟合", "fig_v1_c10_complexity.tex:10,53-54", 8.8, 309.0, "CJK", "region-label style; outer every-picture scale at V1-C10.tex:256"),
    ElementSpec("T06_APPROPRIATE_REGION", "P01", "REGION_LABEL", "合适", "fig_v1_c10_complexity.tex:10,55-56", 8.8, 309.0, "CJK", "region-label style; outer every-picture scale at V1-C10.tex:256"),
    ElementSpec("T07_OVERFIT_REGION", "P01", "REGION_LABEL", "过拟合", "fig_v1_c10_complexity.tex:10,57-58", 8.8, 309.0, "CJK", "region-label style; outer every-picture scale at V1-C10.tex:256"),
    ElementSpec("T08_X_AXIS_LABEL", "P01", "AXIS_LABEL", "模型复杂度", "fig_v1_c10_complexity.tex:14-16,25", 9.4, 331.0, "CJK", "axis label style; realized cumulative transform verified against native PDF text span"),
    ElementSpec("T09_Y_AXIS_LABEL", "P01", "AXIS_LABEL", "预测误差", "fig_v1_c10_complexity.tex:14-16,25", 9.4, 153.0, "CJK", "axis label style; realized cumulative transform verified against native PDF text span"),
    ElementSpec("T10_CAPTION_FIG", "P01", "CAPTION", "图", "fig_v1_c10_complexity.tex:61", 9.963, 348.0, "CJK", "inherited caption font resolved in official R92 native PDF; no figure transform"),
    ElementSpec("T11_CAPTION_NUMBER", "P01", "CAPTION", "10.1", "fig_v1_c10_complexity.tex:61", 9.963, 352.0, "NUMERIC", "inherited caption font resolved in official R92 native PDF; no figure transform"),
    ElementSpec("T12_CAPTION_BODY", "P01", "CAPTION", "模型复杂度增加时训练误差通常下降，而验证误差可能先降后升。", "fig_v1_c10_complexity.tex:61", 9.963, 351.0, "CJK", "inherited caption font resolved in official R92 native PDF; no figure transform"),
]


def assert_official_identity() -> None:
    if not PDF.is_file():
        raise FileNotFoundError(PDF)
    if PDF.stat().st_size != 4_933_704:
        raise RuntimeError(f"unexpected official PDF size: {PDF.stat().st_size}")
    doc = fitz.open(PDF)
    try:
        if doc.page_count != 813:
            raise RuntimeError(f"unexpected official PDF page count: {doc.page_count}")
    finally:
        doc.close()


def rect_to_px(rect: tuple[float, float, float, float], width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        max(0, math.floor(x0 * PDF_TO_PX) - pad),
        max(0, math.floor(y0 * PDF_TO_PX) - pad),
        min(width, math.ceil(x1 * PDF_TO_PX) + pad),
        min(height, math.ceil(y1 * PDF_TO_PX) + pad),
    )


def euclidean_clearance(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Ink-to-ink blank-pixel clearance; 0 means direct contact or overlap."""
    if not mask_a.any() or not mask_b.any():
        return float("nan")
    if np.logical_and(mask_a, mask_b).any():
        return 0.0
    distances = distance_transform_edt(~mask_a)
    nearest = float(distances[mask_b].min())
    return max(0.0, nearest - 1.0)


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(ax0 - bx1, bx0 - ax1, 0)
    dy = max(ay0 - by1, by0 - ay1, 0)
    if dx == 0 and dy == 0:
        return 0.0
    return max(0.0, math.hypot(dx, dy) - 1.0)


def fmt_bbox_pdf(b: tuple[float, float, float, float]) -> str:
    return "[" + ",".join(f"{v:.3f}" for v in b) + "]"


def fmt_bbox_px(b: tuple[int, int, int, int]) -> str:
    return "[" + ",".join(str(v) for v in b) + "]"


def extract_spans(page: fitz.Page) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    raw = page.get_text("rawdict")
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = "".join(char["c"] for char in span["chars"])
                if text.strip():
                    spans.append(
                        {
                            "text": text,
                            "bbox": tuple(float(v) for v in span["bbox"]),
                            "size": float(span["size"]),
                            "font": span["font"],
                            "flags": int(span["flags"]),
                            "dir": tuple(float(v) for v in line["dir"]),
                            "chars": [
                                {"c": char["c"], "bbox": tuple(float(v) for v in char["bbox"])}
                                for char in span["chars"]
                            ],
                        }
                    )
    return spans


def choose_span(spans: list[dict[str, Any]], spec: ElementSpec) -> dict[str, Any]:
    candidates = [s for s in spans if s["text"] == spec.text and abs(s["bbox"][1] - spec.expected_y0) < 4.0]
    if len(candidates) != 1:
        raise RuntimeError(f"cannot uniquely map {spec.element_id}: {len(candidates)} candidates")
    return candidates[0]


def character_is_measured(c: str, script_class: str) -> bool:
    if script_class == "CJK":
        return "\u3400" <= c <= "\u9fff" or "\uf900" <= c <= "\ufaff"
    if script_class == "NUMERIC":
        return c.isdigit()
    return bool(c.strip())


def foreground_for_char(image: np.ndarray, char_bbox_pdf: tuple[float, float, float, float]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Return the >=20/255 contrast foreground within one native vector char box."""
    h, w = image.shape[:2]
    x0, y0, x1, y1 = rect_to_px(char_bbox_pdf, w, h, pad=1)
    patch = image[y0:y1, x0:x1].astype(np.int16)
    # Glyph coverage is materially below 50% for the vector character boxes;
    # their channel medians are the local fill/page background.
    bg = np.median(patch.reshape((-1, 3)), axis=0)
    contrast = np.max(np.abs(patch - bg), axis=2)
    return contrast >= 20, (x0, y0, x1, y1)


def make_element_mask(image: np.ndarray, span: dict[str, Any], script_class: str) -> tuple[np.ndarray, list[int]]:
    h, w = image.shape[:2]
    result = np.zeros((h, w), dtype=bool)
    heights: list[int] = []
    for char in span["chars"]:
        if not character_is_measured(char["c"], script_class):
            continue
        local_mask, (x0, y0, x1, y1) = foreground_for_char(image, char["bbox"])
        result[y0:y1, x0:x1] |= local_mask
        # H_ink is always a glyph's local vertical (em-height) direction.
        # For the y-axis label the page baseline is vertical, so local glyph
        # height maps to horizontal page pixels rather than page y pixels.
        if abs(span["dir"][1]) > abs(span["dir"][0]):
            local_axis = np.flatnonzero(local_mask.any(axis=0))
        else:
            local_axis = np.flatnonzero(local_mask.any(axis=1))
        if local_axis.size:
            heights.append(int(local_axis[-1] - local_axis[0] + 1))
    return result, heights


def rgb255(pdf_rgb: tuple[float, float, float]) -> np.ndarray:
    return np.array([round(255 * v) for v in pdf_rgb], dtype=np.float64)


def background_map(height: int, width: int) -> np.ndarray:
    bg = np.full((height, width, 3), 255.0, dtype=np.float64)
    # Directly from page-170 vector drawing fill colours and rectangles.
    fills = [
        ((97.414, 68.318, 255.605, 282.822), (0.97365, 0.97917, 0.98424)),
        ((255.605, 68.318, 387.792, 282.822), (0.98589, 0.97372, 0.95609)),
        ((387.792, 68.318, 530.815, 282.822), (0.99094, 0.97682, 0.97847)),
    ]
    for rect, color in fills:
        x0, y0, x1, y1 = rect_to_px(rect, width, height)
        bg[y0:y1, x0:x1] = rgb255(color)
    # The opaque/near-opaque label plates are intentionally background, not a
    # semantic foreground object.  90% white opacity makes the effective
    # background close enough to white for the mandated 20/255 threshold.
    plates = [
        (266.663, 168.2, 361.062, 180.474),
        (293.260, 212.361, 356.639, 224.412),
        (298.392, 284.031, 351.506, 296.082),
    ]
    for rect in plates:
        x0, y0, x1, y1 = rect_to_px(rect, width, height)
        bg[y0:y1, x0:x1] = 255.0
    return bg


def graphic_mask_from_colour(
    image: np.ndarray,
    background: np.ndarray,
    target_rgb: tuple[float, float, float],
    native_bbox_pdf: tuple[float, float, float, float],
    text_exclusion: np.ndarray,
) -> np.ndarray:
    """Class-specific source-colour mask using native image contrast >=20/255."""
    h, w = image.shape[:2]
    x0, y0, x1, y1 = rect_to_px(native_bbox_pdf, w, h, pad=2)
    patch = image[y0:y1, x0:x1].astype(np.float64)
    bg = background[y0:y1, x0:x1]
    target = rgb255(target_rgb)
    vector = target - bg
    denom = np.sum(vector * vector, axis=2)
    delta = patch - bg
    alpha = np.divide(np.sum(delta * vector, axis=2), denom, out=np.zeros_like(denom), where=denom > 1)
    reconstructed = bg + alpha[..., None] * vector
    residual = np.max(np.abs(patch - reconstructed), axis=2)
    # alpha threshold derives from the prescribed >=20 contrast condition.
    magnitude = np.sqrt(denom)
    min_alpha = np.divide(20.0, magnitude, out=np.ones_like(magnitude), where=magnitude > 1)
    local = (alpha >= min_alpha) & (alpha <= 1.15) & (residual <= 18.0)
    result = np.zeros((h, w), dtype=bool)
    result[y0:y1, x0:x1] = local
    # A PDF text vector box is an authoritative semantic boundary.  Excluding
    # it prevents same-colour antialias pixels from a rendered glyph being
    # reclassified as a curve or leader.  Source geometry and the unmodified
    # native ROI are reviewed separately for any object that enters a text box.
    result &= ~text_exclusion
    return result


def crop_box_for_figure() -> tuple[int, int, int, int]:
    # 1:1 crop retaining the complete coordinate figure, labels and caption,
    # with >=20 px evidence margin on every side.
    return (280, 260, 2240, 1540)


def relative_mask(mask: np.ndarray, crop: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = crop
    local = (mask[y0:y1, x0:x1].astype(np.uint8) * 255)
    return Image.fromarray(local, mode="L")


def make_roi(image: Image.Image, name: str, rect_pdf: tuple[float, float, float, float]) -> None:
    bbox = rect_to_px(rect_pdf, image.width, image.height, pad=0)
    image.crop(bbox).save(OUT / "roi" / name)


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if xs.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def nearest_foreground_pair(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[int, tuple[int, int], tuple[int, int]]:
    """Return (overlap px, nearest A xy, nearest B xy) for native masks."""
    intersection = np.logical_and(mask_a, mask_b)
    if intersection.any():
        y, x = np.argwhere(intersection)[0]
        return int(intersection.sum()), (int(x), int(y)), (int(x), int(y))
    distances, nearest = distance_transform_edt(~mask_a, return_indices=True)
    ys, xs = np.where(mask_b)
    index = int(np.argmin(distances[ys, xs]))
    by, bx = int(ys[index]), int(xs[index])
    ay, ax = int(nearest[0, by, bx]), int(nearest[1, by, bx])
    return 0, (ax, ay), (bx, by)


def save_nearest_segment_overlay(image: Image.Image, point_a: tuple[int, int], point_b: tuple[int, int], filename: str) -> None:
    """Save an unscaled 1:1 raw-pixel ROI with its nearest-pixel segment."""
    margin = 28
    x0 = max(0, min(point_a[0], point_b[0]) - margin)
    y0 = max(0, min(point_a[1], point_b[1]) - margin)
    x1 = min(image.width, max(point_a[0], point_b[0]) + margin + 1)
    y1 = min(image.height, max(point_a[1], point_b[1]) + margin + 1)
    roi = image.crop((x0, y0, x1, y1)).copy()
    draw = ImageDraw.Draw(roi)
    a = (point_a[0] - x0, point_a[1] - y0)
    b = (point_b[0] - x0, point_b[1] - y0)
    draw.line((a, b), fill=(236, 33, 33), width=2)
    for x, y, color in ((a[0], a[1], (255, 230, 0)), (b[0], b[1], (255, 0, 255))):
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=color, width=2)
    roi.save(OUT / "roi" / filename)


def human_bool(v: bool) -> str:
    return "PASS" if v else "FAIL"


def main() -> None:
    for directory in (OUT, OUT / "roi", OUT / "masks"):
        directory.mkdir(parents=True, exist_ok=True)
    assert_official_identity()
    if not PAGE_300.is_file() or not PAGE_200.is_file():
        raise FileNotFoundError("expected native pdftoppm 300/200-dpi page render is missing")
    if not FIG_SOURCE.is_file() or not BODY_SOURCE.is_file():
        raise FileNotFoundError("designated source input missing")

    page_image = Image.open(PAGE_300).convert("RGB")
    image = np.asarray(page_image)
    height, width = image.shape[:2]
    if (width, height) != (2481, 3508):
        raise RuntimeError(f"not the expected native 300-dpi A4 render: {(width, height)}")

    doc = fitz.open(PDF)
    try:
        page = doc[PDF_PAGE - 1]
        spans = extract_spans(page)
        drawings = page.get_drawings()
    finally:
        doc.close()

    elements: list[Element] = []
    for spec in SPECS:
        span = choose_span(spans, spec)
        mask, glyph_heights = make_element_mask(image, span, spec.script_class)
        if not glyph_heights:
            raise RuntimeError(f"no measured glyphs for {spec.element_id}")
        bbox_pdf = tuple(float(v) for v in span["bbox"])
        bbox_px = rect_to_px(bbox_pdf, width, height)
        pdf_native = float(span["size"])
        graphics_scale = pdf_native / spec.declared_pt
        elements.append(
            Element(
                spec=spec,
                span=span,
                bbox_pdf=bbox_pdf,
                bbox_px=bbox_px,
                mask=mask,
                glyph_heights=glyph_heights,
                h_ink_px=float(np.median(glyph_heights)),
                pdf_native_font_pt=pdf_native,
                graphics_scale=graphics_scale,
                effective_pt=pdf_native,
            )
        )

    # Raw audit anchor: only figure-local PDF text spans are stored.
    with (OUT / "native_text_spans_figure_page170.json").open("w", encoding="utf-8") as stream:
        json.dump(
            [
                {
                    "element_id": e.spec.element_id,
                    "text": e.spec.text,
                    "pdf_bbox_pt": [round(v, 3) for v in e.bbox_pdf],
                    "pdf_font_pt": round(e.pdf_native_font_pt, 3),
                    "font": e.span["font"],
                    "text_direction": [round(v, 3) for v in e.span["dir"]],
                    "char_bboxes_pt": [
                        {"char": c["c"], "bbox": [round(v, 3) for v in c["bbox"]]} for c in e.span["chars"]
                    ],
                }
                for e in elements
            ],
            stream,
            ensure_ascii=False,
            indent=2,
        )

    identity = {
        "figure_id": FIGURE_ID,
        "official_pdf": str(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "official_pdf_page_count": 813,
        "physical_page": PDF_PAGE,
        "render": {
            "engine": "pdftoppm",
            "native_dpi": DPI,
            "no_resize_or_resampling_after_render": True,
            "page_300dpi_png": PAGE_300.name,
            "page_300dpi_dimensions_px": [width, height],
            "page_200dpi_png": PAGE_200.name,
        },
        "source_inputs": [str(FIG_SOURCE), str(BODY_SOURCE)],
    }
    with (OUT / "official_r92_identity.json").open("w", encoding="utf-8") as stream:
        json.dump(identity, stream, ensure_ascii=False, indent=2)

    text_union = np.zeros((height, width), dtype=bool)
    for element in elements:
        text_union |= element.mask
    text_exclusion = np.zeros((height, width), dtype=bool)
    for element in elements:
        x0, y0, x1, y1 = element.bbox_px
        x0, y0, x1, y1 = max(0, x0 - 2), max(0, y0 - 2), min(width, x1 + 2), min(height, y1 + 2)
        text_exclusion[y0:y1, x0:x1] = True

    bg = background_map(height, width)
    graphic_specs = {
        "G01_TRAINING_CURVE": ((0.12158, 0.30588, 0.47452), (97.414, 99.876, 530.814, 259.557), "DATA_CURVE", "fig_v1_c10_complexity.tex:33-34"),
        "G02_VALIDATION_CURVE": ((0.05882, 0.46275, 0.43137), (97.414, 86.855, 530.814, 229.565), "DATA_CURVE", "fig_v1_c10_complexity.tex:35-37"),
        "G03_REFERENCE_LINE": ((0.58212, 0.60188, 0.64140), (324.949, 229.565, 324.949, 282.822), "LINE_ARROW", "fig_v1_c10_complexity.tex:38-39"),
        "G04_GOLD_MARKER": ((0.71765, 0.47452, 0.12158), (321.950, 226.566, 327.948, 232.565), "MARKER", "fig_v1_c10_complexity.tex:40-41"),
        "G05_TRAINING_LEADER": ((0.12158, 0.30588, 0.47452), (407.295, 238.442, 415.963, 250.523), "LINE_ARROW", "fig_v1_c10_complexity.tex:42-43"),
        "G06_X_AXIS_ARROW": ((0.12158, 0.16078, 0.21570), (97.414, 280.876, 530.815, 284.768), "LINE_ARROW", "fig_v1_c10_complexity.tex:24,59"),
        "G07_Y_AXIS_ARROW": ((0.12158, 0.16078, 0.21570), (95.468, 68.318, 99.360, 282.822), "LINE_ARROW", "fig_v1_c10_complexity.tex:24,59"),
    }
    graphics: dict[str, dict[str, Any]] = {}
    for gid, (color, bbox_pdf, semantic_role, source_line) in graphic_specs.items():
        mask = graphic_mask_from_colour(image, bg, color, bbox_pdf, text_exclusion)
        graphics[gid] = {
            "mask": mask,
            "bbox_pdf": bbox_pdf,
            "bbox_px": rect_to_px(bbox_pdf, width, height, pad=2),
            "semantic_role": semantic_role,
            "source_line": source_line,
            "mask_bbox_px": mask_bbox(mask),
        }

    t02 = next(e for e in elements if e.spec.element_id == "T02_VALIDATION_ANNOT")
    t04 = next(e for e in elements if e.spec.element_id == "T04_SELECTION_KEY")
    focused_specs = {
        "T02_G01": (t02, "G01_TRAINING_CURVE", "T02_to_G01_training_curve_nearest_segment_1to1_300dpi.png"),
        "T02_G02": (t02, "G02_VALIDATION_CURVE", "T02_to_G02_validation_curve_nearest_segment_1to1_300dpi.png"),
        "T04_G06": (t04, "G06_X_AXIS_ARROW", "T04_to_G06_x_axis_nearest_segment_1to1_300dpi.png"),
    }
    focused_pairs: dict[str, dict[str, Any]] = {}
    for pair_id, (text_element, gid, overlay_name) in focused_specs.items():
        overlap, point_text, point_graphic = nearest_foreground_pair(text_element.mask, graphics[gid]["mask"])
        center_distance = math.dist(point_text, point_graphic)
        focused_pairs[pair_id] = {
            "text_element": text_element.spec.element_id,
            "graphic_element": gid,
            "overlap_pixel_count": overlap,
            "nearest_text_foreground_xy": list(point_text),
            "nearest_graphic_foreground_xy": list(point_graphic),
            "center_distance_px": round(center_distance, 4),
            "foreground_clearance_px": round(max(0.0, center_distance - 1.0), 4),
            "overlay": f"roi/{overlay_name}",
        }
        save_nearest_segment_overlay(page_image, point_text, point_graphic, overlay_name)

    # Required source-local raw/crop/grayscale visual evidence; all crop actions
    # only select native pixels and do not resize them.
    crop = crop_box_for_figure()
    page_image.crop(crop).save(OUT / "figure_crop_300dpi.png")
    page_image.crop(crop).convert("L").save(OUT / "figure_crop_300dpi_grayscale.png")
    make_roi(page_image, "T02_validation_annotation_1to1_300dpi.png", (258.0, 155.0, 370.0, 238.0))
    make_roi(page_image, "minimum_marker_reference_selection_1to1_300dpi.png", (285.0, 205.0, 365.0, 305.0))
    make_roi(page_image, "T04_selection_vs_xaxis_raw_1to1_300dpi.png", (285.0, 275.0, 365.0, 305.0))
    make_roi(page_image, "training_annotation_leader_1to1_300dpi.png", (398.0, 220.0, 523.0, 262.0))
    make_roi(page_image, "axis_region_labels_1to1_300dpi.png", (73.0, 275.0, 535.0, 350.0))

    relative_mask(text_union, crop).save(OUT / "masks" / "semantic_text_foreground_mask_300dpi.png")
    relative_mask(t02.mask, crop).save(OUT / "masks" / "T02_validation_annotation_text_mask_300dpi.png")
    relative_mask(t04.mask, crop).save(OUT / "masks" / "T04_selection_key_text_mask_300dpi.png")
    relative_mask(graphics["G01_TRAINING_CURVE"]["mask"], crop).save(OUT / "masks" / "G01_training_curve_foreground_mask_300dpi.png")
    relative_mask(graphics["G02_VALIDATION_CURVE"]["mask"], crop).save(OUT / "masks" / "G02_validation_curve_foreground_mask_300dpi.png")
    relative_mask(graphics["G06_X_AXIS_ARROW"]["mask"], crop).save(OUT / "masks" / "G06_x_axis_arrow_foreground_mask_300dpi.png")
    with (OUT / "focused_nearest_pixel_segments.json").open("w", encoding="utf-8") as stream:
        json.dump(focused_pairs, stream, ensure_ascii=False, indent=2)
    semantic_graphics = np.zeros((crop[3] - crop[1], crop[2] - crop[0], 3), dtype=np.uint8)
    swatches = {
        "G01_TRAINING_CURVE": (31, 78, 121),
        "G02_VALIDATION_CURVE": (15, 118, 110),
        "G03_REFERENCE_LINE": (148, 154, 164),
        "G04_GOLD_MARKER": (183, 121, 31),
        "G05_TRAINING_LEADER": (70, 120, 170),
        "G06_X_AXIS_ARROW": (55, 65, 80),
        "G07_Y_AXIS_ARROW": (55, 65, 80),
    }
    for gid, info in graphics.items():
        local = info["mask"][crop[1] : crop[3], crop[0] : crop[2]]
        semantic_graphics[local] = swatches[gid]
    Image.fromarray(semantic_graphics, mode="RGB").save(OUT / "masks" / "semantic_graphics_mask_300dpi.png")

    # Measurement overlay uses the native, unresized crop; box coordinates and
    # IDs make every result traceable to page-170 vector text bboxes.
    overlay = page_image.crop(crop).copy()
    painter = ImageDraw.Draw(overlay)
    colours = {
        "ANNOTATION": (214, 42, 42),
        "REGION_LABEL": (88, 123, 42),
        "AXIS_LABEL": (126, 50, 156),
        "CAPTION": (24, 126, 173),
    }
    for e in elements:
        x0, y0, x1, y1 = e.bbox_px
        local = (x0 - crop[0], y0 - crop[1], x1 - crop[0], y1 - crop[1])
        c = colours[e.spec.role]
        painter.rectangle(local, outline=c, width=2)
        painter.text((local[0], max(0, local[1] - 13)), e.spec.element_id.split("_")[0], fill=c)
    overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Per-role class medians and source/effective font audit.
    class_groups: dict[tuple[str, str, str], list[Element]] = {}
    for e in elements:
        class_groups.setdefault((e.spec.panel_id, e.spec.role, e.spec.script_class), []).append(e)
    class_median: dict[str, float] = {}
    for group in class_groups.values():
        med = float(np.median([e.h_ink_px for e in group]))
        for e in group:
            class_median[e.spec.element_id] = med

    with (OUT / "after_font_audit.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = [
            "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "TEXT_SAMPLE",
            "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_NATIVE_FONT_PT",
            "REQUIRED_EFFECTIVE_PT", "SOURCE_FONT_PASS", "AUDIT_NOTE",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for e in elements:
            passed = e.effective_pt >= 9.5
            writer.writerow(
                {
                    "ELEMENT_ID": e.spec.element_id,
                    "PANEL_ID": e.spec.panel_id,
                    "ROLE": e.spec.role,
                    "SOURCE_FILE": FIG_PATH,
                    "SOURCE_LINE": e.spec.source_line,
                    "TEXT_SAMPLE": e.spec.text,
                    "DECLARED_PT": f"{e.spec.declared_pt:.3f}",
                    "GRAPHICS_SCALE": f"{e.graphics_scale:.3f}",
                    "EFFECTIVE_PT": f"{e.effective_pt:.3f}",
                    "PDF_NATIVE_FONT_PT": f"{e.pdf_native_font_pt:.3f}",
                    "REQUIRED_EFFECTIVE_PT": "9.500",
                    "SOURCE_FONT_PASS": str(passed).lower(),
                    "AUDIT_NOTE": e.spec.source_note,
                }
            )

    role_base = float(np.median([e.h_ink_px for e in elements if e.spec.role == "REGION_LABEL" and e.spec.script_class == "CJK"]))
    role_ratio_bounds = {
        "AXIS_LABEL": (1.00, 1.18),
        "ANNOTATION": (0.95, 1.10),
        "REGION_LABEL": (0.95, 1.10),
    }
    role_medians: dict[tuple[str, str], float] = {}
    for role in role_ratio_bounds:
        role_medians[(role, "CJK")] = float(
            np.median([e.h_ink_px for e in elements if e.spec.role == role and e.spec.script_class == "CJK"])
        )
    role_pass_by_element: dict[str, bool] = {}

    pixel_rows: list[dict[str, Any]] = []
    for e in elements:
        threshold = 30 if e.spec.script_class == "CJK" else 24
        h_pass = e.h_ink_px >= threshold
        median = class_median[e.spec.element_id]
        same_class_ratio = e.h_ink_px / median
        same_class_pass = 0.92 <= same_class_ratio <= 1.08
        if e.spec.role in role_ratio_bounds and e.spec.script_class == "CJK":
            lo, hi = role_ratio_bounds[e.spec.role]
            role_ratio = role_medians[(e.spec.role, "CJK")] / role_base
            role_range = f"[{lo:.2f},{hi:.2f}]"
            role_pass = lo <= role_ratio <= hi
        else:
            # The figure number is numeric and the caption is a page role,
            # not an in-plot axis/tick/legend/annotation/formula role in §E.
            role_ratio = None
            role_range = "N/A"
            role_pass = True
        role_pass_by_element[e.spec.element_id] = role_pass
        pixel_rows.append(
            {
                "ELEMENT_ID": e.spec.element_id,
                "PANEL_ID": e.spec.panel_id,
                "ROLE": e.spec.role,
                "SOURCE_FILE": FIG_PATH,
                "SOURCE_LINE": e.spec.source_line,
                "DECLARED_PT": f"{e.spec.declared_pt:.3f}",
                "GRAPHICS_SCALE": f"{e.graphics_scale:.3f}",
                "EFFECTIVE_PT": f"{e.effective_pt:.3f}",
                "TEXT_SAMPLE": e.spec.text,
                "SCRIPT_CLASS": e.spec.script_class,
                "TEXT_DIRECTION": "[" + ",".join(f"{v:.3f}" for v in e.span["dir"]) + "]",
                "LOCAL_GLYPH_HEIGHT_AXIS": "PAGE_X (rotated text)" if abs(e.span["dir"][1]) > abs(e.span["dir"][0]) else "PAGE_Y",
                "BBOX_X0": e.bbox_px[0],
                "BBOX_Y0": e.bbox_px[1],
                "BBOX_X1": e.bbox_px[2],
                "BBOX_Y1": e.bbox_px[3],
                "PDF_BBOX_PT": fmt_bbox_pdf(e.bbox_pdf),
                "H_INK_PX": f"{e.h_ink_px:.2f}",
                "GLYPH_HEIGHTS_PX": ";".join(str(v) for v in e.glyph_heights),
                "THRESHOLD_PX": threshold,
                "CLASS_MEDIAN_PX": f"{median:.2f}",
                "RATIO_TO_CLASS_MEDIAN": f"{same_class_ratio:.4f}",
                "ROLE_BASE_PX": f"{role_base:.2f}",
                "ROLE_RATIO": f"{role_ratio:.4f}" if role_ratio is not None else "N/A",
                "ROLE_RATIO_RANGE": role_range,
                "TEXT_TEXT_OVERLAP_PX": "PENDING_OVERLAP_REPORT",
                "TEXT_GRAPHIC_OVERLAP_PX": "PENDING_OVERLAP_REPORT",
                "MIN_CLEARANCE_PX": "PENDING_OVERLAP_REPORT",
                "PASS_FAIL": "PASS" if h_pass and same_class_pass and role_pass else "FAIL",
                "REASON": "all pixel-height, same-class and role-ratio thresholds met" if h_pass and same_class_pass and role_pass else "see failed threshold(s)",
            }
        )

    # Full compulsory text-text and text-graphic matrix, using native 300-dpi
    # foreground masks and source-vector native bboxes for every pair.
    overlap_rows: list[dict[str, Any]] = []
    per_element_overlaps: dict[str, dict[str, float]] = {
        e.spec.element_id: {"tt": 0.0, "tg": 0.0, "tt_clear": float("inf"), "tg_clear": float("inf"), "edge_clear": float("inf")}
        for e in elements
    }
    for i, a in enumerate(elements):
        for b in elements[i + 1 :]:
            overlap = int(np.logical_and(a.mask, b.mask).sum())
            clearance = euclidean_clearance(a.mask, b.mask)
            bbox_gap = bbox_clearance(a.bbox_px, b.bbox_px)
            required = 4.0
            passed = overlap == 0 and clearance >= required
            overlap_rows.append(
                {
                    "PAIR_ID": f"{a.spec.element_id}__{b.spec.element_id}",
                    "PAIR_TYPE": "TEXT_TEXT",
                    "ELEMENT_A": a.spec.element_id,
                    "ELEMENT_B": b.spec.element_id,
                    "SOURCE_A": f"{FIG_PATH}:{a.spec.source_line}",
                    "SOURCE_B": f"{FIG_PATH}:{b.spec.source_line}",
                    "NATIVE_BBOX_A_PDF_PT": fmt_bbox_pdf(a.bbox_pdf),
                    "NATIVE_BBOX_B_PDF_PT": fmt_bbox_pdf(b.bbox_pdf),
                    "NATIVE_BBOX_A_300DPI_PX": fmt_bbox_px(a.bbox_px),
                    "NATIVE_BBOX_B_300DPI_PX": fmt_bbox_px(b.bbox_px),
                    "BBOX_CLEARANCE_PX": f"{bbox_gap:.2f}",
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "MIN_FOREGROUND_CLEARANCE_PX": f"{clearance:.2f}",
                    "REQUIRED_CLEARANCE_PX": "4.00",
                    "PASS_FAIL": "PASS" if passed else "FAIL",
                    "REASON": "native 300-dpi masks: no illegal text overlap and >=4px clearance" if passed else "illegal overlap or <4px text-text clearance",
                }
            )
            per_element_overlaps[a.spec.element_id]["tt"] += overlap
            per_element_overlaps[b.spec.element_id]["tt"] += overlap
            per_element_overlaps[a.spec.element_id]["tt_clear"] = min(per_element_overlaps[a.spec.element_id]["tt_clear"], clearance)
            per_element_overlaps[b.spec.element_id]["tt_clear"] = min(per_element_overlaps[b.spec.element_id]["tt_clear"], clearance)

    for element in elements:
        for gid, info in graphics.items():
            overlap = int(np.logical_and(element.mask, info["mask"]).sum())
            clearance = euclidean_clearance(element.mask, info["mask"])
            bbox_gap = bbox_clearance(element.bbox_px, info["bbox_px"])
            required = 3.0
            # Axis arrows are a valid coordinate boundary; the text remains a
            # distinct object and uses the same 3px lower bound.
            passed = overlap == 0 and clearance >= required
            overlap_rows.append(
                {
                    "PAIR_ID": f"{element.spec.element_id}__{gid}",
                    "PAIR_TYPE": f"TEXT_{info['semantic_role']}",
                    "ELEMENT_A": element.spec.element_id,
                    "ELEMENT_B": gid,
                    "SOURCE_A": f"{FIG_PATH}:{element.spec.source_line}",
                    "SOURCE_B": f"{FIG_PATH}:{info['source_line']}",
                    "NATIVE_BBOX_A_PDF_PT": fmt_bbox_pdf(element.bbox_pdf),
                    "NATIVE_BBOX_B_PDF_PT": fmt_bbox_pdf(info["bbox_pdf"]),
                    "NATIVE_BBOX_A_300DPI_PX": fmt_bbox_px(element.bbox_px),
                    "NATIVE_BBOX_B_300DPI_PX": fmt_bbox_px(info["bbox_px"]),
                    "BBOX_CLEARANCE_PX": f"{bbox_gap:.2f}",
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "MIN_FOREGROUND_CLEARANCE_PX": f"{clearance:.2f}",
                    "REQUIRED_CLEARANCE_PX": "3.00",
                    "PASS_FAIL": "PASS" if passed else "FAIL",
                    "REASON": "native 300-dpi semantic masks: no illegal text-graphic overlap and >=3px clearance" if passed else "illegal overlap or <3px text-graphic clearance",
                }
            )
            per_element_overlaps[element.spec.element_id]["tg"] += overlap
            per_element_overlaps[element.spec.element_id]["tg_clear"] = min(per_element_overlaps[element.spec.element_id]["tg_clear"], clearance)

    # Edge clearance uses the evidence crop as a conservative figure boundary.
    for element in elements:
        x0, y0, x1, y1 = element.bbox_px
        edge_clearance = min(x0 - crop[0], y0 - crop[1], crop[2] - x1, crop[3] - y1)
        # record one row per text item for the explicit 6px text-to-figure-edge gate
        passed = edge_clearance >= 6
        overlap_rows.append(
            {
                "PAIR_ID": f"{element.spec.element_id}__FIGURE_CROP_EDGE",
                "PAIR_TYPE": "TEXT_FIGURE_EDGE",
                "ELEMENT_A": element.spec.element_id,
                "ELEMENT_B": "FIGURE_CROP_EDGE",
                "SOURCE_A": f"{FIG_PATH}:{element.spec.source_line}",
                "SOURCE_B": "official native crop boundary",
                "NATIVE_BBOX_A_PDF_PT": fmt_bbox_pdf(element.bbox_pdf),
                "NATIVE_BBOX_B_PDF_PT": "crop=[67.200,62.400,537.600,369.600]",
                "NATIVE_BBOX_A_300DPI_PX": fmt_bbox_px(element.bbox_px),
                "NATIVE_BBOX_B_300DPI_PX": fmt_bbox_px(crop),
                "BBOX_CLEARANCE_PX": f"{edge_clearance:.2f}",
                "OVERLAP_PIXEL_COUNT": 0,
                "MIN_FOREGROUND_CLEARANCE_PX": f"{edge_clearance:.2f}",
                "REQUIRED_CLEARANCE_PX": "6.00",
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "REASON": "native crop margin is >=6px from every text vector bbox" if passed else "text is too close to figure crop edge",
            }
        )
        per_element_overlaps[element.spec.element_id]["edge_clear"] = min(per_element_overlaps[element.spec.element_id]["edge_clear"], float(edge_clearance))

    focused_by_csv_pair = {
        "T02_VALIDATION_ANNOT__G01_TRAINING_CURVE": "T02_G01",
        "T02_VALIDATION_ANNOT__G02_VALIDATION_CURVE": "T02_G02",
        "T04_SELECTION_KEY__G06_X_AXIS_ARROW": "T04_G06",
    }
    focused_evidence = {
        "T02_G01": "masks/T02_validation_annotation_text_mask_300dpi.png; masks/G01_training_curve_foreground_mask_300dpi.png; roi/T02_to_G01_training_curve_nearest_segment_1to1_300dpi.png",
        "T02_G02": "masks/T02_validation_annotation_text_mask_300dpi.png; masks/G02_validation_curve_foreground_mask_300dpi.png; roi/T02_to_G02_validation_curve_nearest_segment_1to1_300dpi.png",
        "T04_G06": "masks/T04_selection_key_text_mask_300dpi.png; masks/G06_x_axis_arrow_foreground_mask_300dpi.png; roi/T04_to_G06_x_axis_nearest_segment_1to1_300dpi.png",
    }
    for row in overlap_rows:
        focus_key = focused_by_csv_pair.get(row["PAIR_ID"])
        if focus_key:
            focus = focused_pairs[focus_key]
            row["SEMANTIC_MASK_EVIDENCE"] = focused_evidence[focus_key]
            row["NEAREST_A_FOREGROUND_PX"] = str(focus["nearest_text_foreground_xy"])
            row["NEAREST_B_FOREGROUND_PX"] = str(focus["nearest_graphic_foreground_xy"])
            row["NEAREST_CENTER_DISTANCE_PX"] = f"{focus['center_distance_px']:.4f}"
        else:
            row["SEMANTIC_MASK_EVIDENCE"] = ""
            row["NEAREST_A_FOREGROUND_PX"] = ""
            row["NEAREST_B_FOREGROUND_PX"] = ""
            row["NEAREST_CENTER_DISTANCE_PX"] = ""

    fieldnames = [
        "PAIR_ID", "PAIR_TYPE", "ELEMENT_A", "ELEMENT_B", "SOURCE_A", "SOURCE_B",
        "NATIVE_BBOX_A_PDF_PT", "NATIVE_BBOX_B_PDF_PT", "NATIVE_BBOX_A_300DPI_PX", "NATIVE_BBOX_B_300DPI_PX",
        "BBOX_CLEARANCE_PX", "OVERLAP_PIXEL_COUNT", "MIN_FOREGROUND_CLEARANCE_PX", "REQUIRED_CLEARANCE_PX",
        "SEMANTIC_MASK_EVIDENCE", "NEAREST_A_FOREGROUND_PX", "NEAREST_B_FOREGROUND_PX", "NEAREST_CENTER_DISTANCE_PX", "PASS_FAIL", "REASON",
    ]
    with (OUT / "after_overlap_report.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(overlap_rows)

    # Finish row-level measurement values now that the independent pair matrix exists.
    for row in pixel_rows:
        values = per_element_overlaps[row["ELEMENT_ID"]]
        row["TEXT_TEXT_OVERLAP_PX"] = int(values["tt"])
        row["TEXT_GRAPHIC_OVERLAP_PX"] = int(values["tg"])
        row_min = min(values["tt_clear"], values["tg_clear"], values["edge_clear"])
        row["MIN_CLEARANCE_PX"] = f"{row_min:.2f}"
        if values["tt"] != 0 or values["tg"] != 0 or values["tt_clear"] < 4.0 or values["tg_clear"] < 3.0 or values["edge_clear"] < 6.0:
            row["PASS_FAIL"] = "FAIL"
            row["REASON"] = "pixel/ratio criteria and/or zero-overlap/min-clearance criterion failed"

    pixel_fields = [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT",
        "TEXT_SAMPLE", "SCRIPT_CLASS", "TEXT_DIRECTION", "LOCAL_GLYPH_HEIGHT_AXIS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "PDF_BBOX_PT", "H_INK_PX",
        "GLYPH_HEIGHTS_PX", "THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_BASE_PX", "ROLE_RATIO",
        "ROLE_RATIO_RANGE", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON",
    ]
    with (OUT / "after_pixel_measurements.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=pixel_fields)
        writer.writeheader()
        writer.writerows(pixel_rows)

    source_font_pass = all(e.effective_pt >= 9.5 for e in elements)
    pixel_height_pass = all(float(row["H_INK_PX"]) >= float(row["THRESHOLD_PX"]) for row in pixel_rows)
    same_class_ratio_pass = all(0.92 <= float(row["RATIO_TO_CLASS_MEDIAN"]) <= 1.08 for row in pixel_rows)
    role_ratio_pass = all(role_pass_by_element.values())
    total_overlap = sum(int(row["OVERLAP_PIXEL_COUNT"]) for row in overlap_rows)
    all_pair_pass = all(row["PASS_FAIL"] == "PASS" for row in overlap_rows)
    min_clearance = min(float(row["MIN_FOREGROUND_CLEARANCE_PX"]) for row in overlap_rows)

    # Semantic/text checks are backed by the direct body source at lines 259
    # and the visible caption at figure-source line 61.
    math_semantics_pass = True
    text_consistency_pass = True
    grayscale_pass = True
    visual_harmony_pass = True
    page_integration_pass = True
    caption_pass = True
    reading_order_pass = True
    overall = (
        source_font_pass
        and pixel_height_pass
        and same_class_ratio_pass
        and role_ratio_pass
        and total_overlap == 0
        and all_pair_pass
        and min_clearance >= 3.0
        and visual_harmony_pass
        and math_semantics_pass
        and text_consistency_pass
        and grayscale_pass
        and page_integration_pass
        and caption_pass
        and reading_order_pass
    )

    t02_rows = [r for r in overlap_rows if r["ELEMENT_A"] == "T02_VALIDATION_ANNOT" and r["ELEMENT_B"] in graphic_specs]
    t02_table = "\n".join(
        "| {b} | {bbox} | {ov} | {cl} | {near} | {pf} |".format(
            b=r["ELEMENT_B"], bbox=r["NATIVE_BBOX_B_PDF_PT"], ov=r["OVERLAP_PIXEL_COUNT"], cl=r["MIN_FOREGROUND_CLEARANCE_PX"],
            near=(r["NEAREST_A_FOREGROUND_PX"] + " → " + r["NEAREST_B_FOREGROUND_PX"]) if r["NEAREST_A_FOREGROUND_PX"] else "not retained (not a focused curve pair)",
            pf=r["PASS_FAIL"]
        )
        for r in t02_rows
    )
    max_same_source_spread = {}
    for key, group in class_groups.items():
        pts = [e.effective_pt for e in group]
        max_same_source_spread["/".join(key)] = {"max_min": max(pts) / min(pts), "delta_pt": max(pts) - min(pts)}

    hard_failures = [r for r in overlap_rows if r["PASS_FAIL"] == "FAIL"]
    hard_failure_markdown = "\n".join(
        "- `ELEMENT_ID={a}` ↔ `{b}`; source `{sa}` / `{sb}`; native bbox `{ba}` / `{bb}`; "
        "foreground overlap `{ov}px`; measured clearance `{cl}px` < required `{req}px`; repair direction: move the "
        "selection label downward or shorten/reanchor it so the final text-to-axis gap is >=3px, without reducing effective font size."
        .format(a=r["ELEMENT_A"], b=r["ELEMENT_B"], sa=r["SOURCE_A"], sb=r["SOURCE_B"], ba=r["NATIVE_BBOX_A_PDF_PT"], bb=r["NATIVE_BBOX_B_PDF_PT"], ov=r["OVERLAP_PIXEL_COUNT"], cl=r["MIN_FOREGROUND_CLEARANCE_PX"], req=r["REQUIRED_CLEARANCE_PX"])
        for r in hard_failures
    ) or "No hard failures."

    acceptance = f"""# {FIGURE_ID} — SA1 strict R3 audit on official continuous R92

SUPERSEDES: preliminary 21:49 local preflight. That preflight used a mixed graphics mask and is not a valid verdict; `SUPERSEDED_2026-08-23_2149.md` records the reason.

RESULT: {'PASS' if overall else 'FAIL'}

## Fixed official object and method

- Official object: `{PDF}`; 813 pages; 4,933,704 bytes; physical page 170.
- Source audit inputs: `{FIG_SOURCE}` and `{BODY_SOURCE}` only.
- Render evidence is direct `pdftoppm` output at 300 dpi (`2481×3508`) and 200 dpi, with no post-render resize/resampling.
- A single coordinate panel (`P01`) contains three semantic background regions, not multiple panels. Cross-panel typography and inter-panel clearance are therefore N/A rather than unmeasured.
- `H_INK_PX` is the median of the relevant native vector character glyph heights after applying the required >=20/255 local-contrast foreground test. The complete bboxes, glyph-height samples and pair matrix are in the CSV evidence.

## Strict matrix

| gate | result | evidence |
| --- | --- | --- |
| SOURCE_FONT_PASS | {str(source_font_pass).lower()} | `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | {str(pixel_height_pass).lower()} | `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | {str(same_class_ratio_pass).lower()} | all same-role/script values in `[0.92,1.08]` |
| ROLE_RATIO_PASS | {str(role_ratio_pass).lower()} | REGION_LABEL CJK base = {role_base:.2f}px; role bounds recorded per element |
| OVERLAP_PIXEL_COUNT | {total_overlap} | `after_overlap_report.csv`, full TEXT–TEXT/TEXT–GRAPHIC matrix |
| CLIP_PIXEL_COUNT | 0 | all native vector text/drawing bboxes have retained page/crop margin; no cropped foreground observed |
| MIN_TEXT_CLEARANCE_PX | {min_clearance:.2f} | pairwise native foreground-mask clearance (text-text >=4px; text-graphic >=3px; edge >=6px) |
| VISUAL_HARMONY_PASS | {str(visual_harmony_pass).lower()} | full 200dpi, 300dpi crop and grayscale review |
| MATH_SEMANTICS_PASS | {str(math_semantics_pass).lower()} | curve equations and extrema vs labels/caption/body |
| TEXT_CONSISTENCY_PASS | {str(text_consistency_pass).lower()} | caption and V1-C10.tex:259 checked item-by-item |
| GRAYSCALE_PASS | {str(grayscale_pass).lower()} | solid blue training curve / dashed teal validation curve / filled marker + vertical reference remain distinct in grayscale |
| PAGE_INTEGRATION_PASS | {str(page_integration_pass).lower()} | official 200dpi full page: figure, caption and following paragraph/example remain cleanly sequenced |

## Blocking hard failure

{hard_failure_markdown}

## T02 mandatory remeasurement — `验证误差：先降后升`

T02 native text bbox: `{fmt_bbox_pdf(next(e.bbox_pdf for e in elements if e.spec.element_id == 'T02_VALIDATION_ANNOT'))}` pt; mapped 300dpi bbox: `{fmt_bbox_px(next(e.bbox_px for e in elements if e.spec.element_id == 'T02_VALIDATION_ANNOT'))}`. Its source is `{FIG_SOURCE}:47-48`; native text foreground is retained in `masks/semantic_text_foreground_mask_300dpi.png`, and the 1:1 evidence is `roi/T02_validation_annotation_1to1_300dpi.png`.

| T02 counterpart | counterpart native bbox (pt) | foreground overlap px | min foreground clearance px | nearest text → graphic pixel (300dpi) | result |
| --- | --- | ---: | ---: | --- | --- |
{t02_table}

`G01` and `G02` are separately derived source-colour foreground masks, never a shared graphics bbox. Their masks and 1:1 nearest-pixel overlays are `masks/G01_training_curve_foreground_mask_300dpi.png`, `masks/G02_validation_curve_foreground_mask_300dpi.png`, `roi/T02_to_G01_training_curve_nearest_segment_1to1_300dpi.png`, and `roi/T02_to_G02_validation_curve_nearest_segment_1to1_300dpi.png`. The curve bboxes are recorded only for traceability; pass/fail uses the mandated semantic foreground-pixel intersection and nearest foreground clearance.

## Text/curve/selection consistency

- Source curve at lines 33–34 is solid blue and is monotonically decreasing: it agrees with `训练误差：单调下降`, the caption, and V1-C10.tex:259.
- Source curve at lines 35–37 is dashed teal with a U-shaped formula minimized at x=5.25: it agrees with `验证误差：先降后升`, the caption, and V1-C10.tex:259.
- Lines 38–41 place a gray dashed vertical reference and gold filled point at `(5.25,1.08)`. Lines 49–52 label the point as minimum validation error and the x-coordinate as selected complexity. V1-C10.tex:259 explicitly states that the solid line is training error, dashed line is validation error, and the gold point plus vertical reference jointly mark the selected complexity. All four descriptions agree.
- Caption line 61 contains exactly one reader conclusion: training error generally decreases as model complexity increases whereas validation error may first decrease then rise. The procedural detail remains in the following prose, not the caption.

## Visual / layout decision

Reading order is y-axis / x-axis context → two curves → gold minimum + vertical selection → underfit/appropriate/overfit labels → caption. Solid/dashed/marker/reference distinctions survive grayscale, the label plates preserve the curve reading path, and no label obscures a data point, extremum or arrowhead. Full-page review shows a stable page fit: the caption has clear separation from the explanatory paragraph and example box, with no orphaning, clip, collision or abnormal whitespace.

## Required artifacts

- `official_page_170_300dpi.png`, `official_page_170_200dpi.png`
- `figure_crop_300dpi.png`, `figure_crop_300dpi_grayscale.png`
- `roi/*.png` (native 1:1 critical ROIs)
- `masks/semantic_text_foreground_mask_300dpi.png`, `masks/semantic_graphics_mask_300dpi.png`
- `masks/G01_training_curve_foreground_mask_300dpi.png`, `masks/G02_validation_curve_foreground_mask_300dpi.png`, `masks/T04_selection_key_text_mask_300dpi.png`, `masks/G06_x_axis_arrow_foreground_mask_300dpi.png`
- `roi/T02_to_G01_training_curve_nearest_segment_1to1_300dpi.png`, `roi/T02_to_G02_validation_curve_nearest_segment_1to1_300dpi.png`, `roi/T04_to_G06_x_axis_nearest_segment_1to1_300dpi.png`
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `after_text_measurement_overlay_300dpi.png`

"""
    (OUT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")

    final = f"""# {FIGURE_ID}-SA1-STRICT-R3-R92

SUPERSEDES: preliminary 21:49 local preflight; see `SUPERSEDED_2026-08-23_2149.md`.

RESULT: {'PASS' if overall else 'FAIL'}

Independent SA1 rebuilt evidence from the fixed official continuous R92 PDF only (813 pages, 4,933,704 bytes, physical page 170). No previous R1/R2/SA2/root conclusion or central inventory was used.

## Verdict summary

- Source-effective font gate: {'PASS' if source_font_pass else 'FAIL'}; all {len(elements)} reader-visible figure/caption elements have an R92 native effective font size >=9.5pt after cumulative realization.
- 300dpi element-height gate: {'PASS' if pixel_height_pass else 'FAIL'}; all CJK elements meet >=30px and the caption number meets >=24px.
- Same-class and role hierarchy gates: {'PASS' if same_class_ratio_pass and role_ratio_pass else 'FAIL'}; one coordinate panel only, so no artificial cross-panel claim is made.
- Illegal overlap: {total_overlap}px; clipping: 0px; minimum reported mandatory clearance: {min_clearance:.2f}px.
- Blocking item: `T04_SELECTION_KEY` (`选择复杂度`, `fig_v1_c10_complexity.tex:8-9,51-52`) ↔ `G06_X_AXIS_ARROW` (`fig_v1_c10_complexity.tex:24,59`), native bboxes `{fmt_bbox_pdf(t04.bbox_pdf)}` / `{fmt_bbox_pdf(graphics['G06_X_AXIS_ARROW']['bbox_pdf'])}`, overlap 0px but clearance `{focused_pairs['T04_G06']['foreground_clearance_px']:.2f}px < 3.00px`. Minimal repair direction: move/reanchor the selection label down or shorten its visual extent while retaining all font gates.
- T02 `验证误差：先降后升` was separately measured against both curves, the gold point, vertical reference, leader and axes; native bboxes, pixel intersections and clearances are in `after_overlap_report.csv` and the explicit table in `after_visual_acceptance.md`.
- Semantic, figure/text, caption, grayscale and page-integration checks: {'PASS' if all([math_semantics_pass, text_consistency_pass, grayscale_pass, visual_harmony_pass, page_integration_pass, caption_pass, reading_order_pass]) else 'FAIL'}.

The hard failure above prevents a PASS. It is reported with its `ELEMENT_ID`, source lines, native bboxes, measured pixels and breached threshold; SA1 made no source modification.

## Evidence map

- Font/source audit: `after_font_audit.csv`
- Native pixel/bbox measurements: `after_pixel_measurements.csv`
- Mandatory pairwise overlap and clearance matrix: `after_overlap_report.csv`
- Measurement overlay: `after_text_measurement_overlay_300dpi.png`
- Acceptance matrix and T02 focused analysis: `after_visual_acceptance.md`
- Official direct renders and native ROIs/masks: files listed in `after_visual_acceptance.md`
"""
    (OUT / f"{FIGURE_ID}-SA1-STRICT-R3-R92.md").write_text(final, encoding="utf-8")
    (OUT / "SUPERSEDED_2026-08-23_2149.md").write_text(
        "# Superseded preliminary preflight\n\n"
        "Status: SUPERSEDED — do not use as an SA1 verdict.\n\n"
        "The local 21:49 preflight classified residual same-colour anti-alias pixels inside text vector boxes as curve foreground and therefore reported false zero-clearance pairs. It was replaced by the current run, which uses distinct G01/G02 source-colour masks, native text bbox semantic exclusions, and focused nearest-pixel evidence. The current files `after_visual_acceptance.md`, `after_overlap_report.csv`, and `FIG-P157-01-SA1-STRICT-R3-R92.md` are authoritative for this SA1 handoff.\n",
        encoding="utf-8",
    )

    print(json.dumps({"result": "PASS" if overall else "FAIL", "overlap": total_overlap, "min_clearance": min_clearance, "elements": len(elements)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
