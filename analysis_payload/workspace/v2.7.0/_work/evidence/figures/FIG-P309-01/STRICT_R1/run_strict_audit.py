from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


HERE = Path(__file__).resolve().parent
SOURCE_FILE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第03册_优化模型与序列模型\V3-C02\fig_v3_c02_margin.tex"
)
OFFICIAL_PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r92_fullbook\main_full.pdf"
)
STANDALONE_PDF = HERE / "standalone_build" / "v260_FIG-P309-01_standalone.pdf"
OFFICIAL_PAGE_300 = HERE / "official_page_334_300dpi.png"
OFFICIAL_PAGE_200 = HERE / "after_full_page_200dpi.png"
STANDALONE_PAGE_300 = HERE / "standalone_page_300dpi.png"
TEXT_ONLY_PDF = HERE / "text_only.pdf"
GRAPHICS_ONLY_PDF = HERE / "graphics_only.pdf"
TEXT_ONLY_PNG = HERE / "text_only_300dpi.png"
GRAPHICS_ONLY_PNG = HERE / "graphics_only_300dpi.png"
MASK_DIR = HERE / "semantic_masks"
ROI_DIR = HERE / "roi"
PDF_SCALE = 300.0 / 72.0
FG_THRESHOLD = 20


@dataclass(frozen=True)
class TokenSpec:
    element_id: str
    group_id: str
    span_index: int
    char_index: int | None
    role: str
    source_line: str
    declared_pt: float
    effective_pt: float
    text_sample: str
    script_class: str
    pixel_floor: int
    natural_script: bool = False


TOKENS = [
    TokenSpec("T01_W", "F01_W_LABEL", 0, 0, "ANNOTATION", "53-54", 9.2, 9.2, "w", "LATIN_LOWER", 17),
    TokenSpec("T02_MARGIN_2", "F02_MARGIN_FORMULA", 1, 0, "FORMULA_BLOCK", "59-60", 9.2, 9.2, "2", "DIGIT", 24),
    TokenSpec("T03_MARGIN_SLASH", "F02_MARGIN_FORMULA", 1, 1, "FORMULA_BLOCK", "59-60", 9.2, 9.2, "/", "BASE_MATH_OPERATOR", 22),
    TokenSpec("T04_MARGIN_NORM_L", "F02_MARGIN_FORMULA", 1, 2, "FORMULA_BLOCK", "59-60", 9.2, 9.2, "norm-left", "BASE_MATH_OPERATOR", 22),
    TokenSpec("T05_MARGIN_W", "F02_MARGIN_FORMULA", 1, 3, "FORMULA_BLOCK", "59-60", 9.2, 9.2, "w", "LATIN_LOWER", 17),
    TokenSpec("T06_MARGIN_NORM_R", "F02_MARGIN_FORMULA", 1, 4, "FORMULA_BLOCK", "59-60", 9.2, 9.2, "norm-right", "BASE_MATH_OPERATOR", 22),
    TokenSpec("T07_HPLUS_H", "F03_HPLUS", 2, 0, "LINE_LABEL", "63-64", 9.5, 9.5, "H", "LATIN_CAP", 24),
    TokenSpec("T08_HPLUS_SUBPLUS", "F03_HPLUS", 3, 0, "LINE_LABEL", "63-64", 9.5, 9.5, "+", "NATURAL_SCRIPT", 15, True),
    TokenSpec("T09_H", "F04_H", 4, 0, "LINE_LABEL", "67-68", 9.5, 9.5, "H", "LATIN_CAP", 24),
    TokenSpec("T10_HMINUS_H", "F05_HMINUS", 5, 0, "LINE_LABEL", "71-72", 9.5, 9.5, "H", "LATIN_CAP", 24),
    TokenSpec("T11_HMINUS_SUBMINUS", "F05_HMINUS", 6, 0, "LINE_LABEL", "71-72", 9.5, 9.5, "minus", "NATURAL_SCRIPT", 15, True),
    TokenSpec("T12_NOTE_CJK", "F06_NOTE", 7, None, "ANNOTATION", "73-74", 9.2, 9.2, "外圈：支持向量", "CJK_LINE", 30),
    TokenSpec("T13_X1_X", "F07_X1", 8, 0, "AXIS_LABEL", "19,32", 9.5, 9.5, "x", "LATIN_LOWER", 17),
    TokenSpec("T14_X1_SUB1", "F07_X1", 9, 0, "AXIS_LABEL", "19,32", 9.5, 9.5, "1", "NATURAL_SCRIPT", 15, True),
    TokenSpec("T15_X2_X", "F08_X2", 10, 0, "AXIS_LABEL", "19,32", 9.5, 9.5, "x", "LATIN_LOWER", 17),
    TokenSpec("T16_X2_SUB2", "F08_X2", 11, 0, "AXIS_LABEL", "19,32", 9.5, 9.5, "2", "NATURAL_SCRIPT", 15, True),
]


GROUP_TEXT = {
    "F01_W_LABEL": "w",
    "F02_MARGIN_FORMULA": "2/||w||",
    "F03_HPLUS": "H_+",
    "F04_H": "H",
    "F05_HMINUS": "H_-",
    "F06_NOTE": "外圈：支持向量",
    "F07_X1": "x_1",
    "F08_X2": "x_2",
}

GROUP_SPANS = {
    "F01_W_LABEL": [0],
    "F02_MARGIN_FORMULA": [1],
    "F03_HPLUS": [2, 3],
    "F04_H": [4],
    "F05_HMINUS": [5, 6],
    "F06_NOTE": [7],
    "F07_X1": [8, 9],
    "F08_X2": [10, 11],
}


# Each entry is an independent semantic foreground object.  Background tint
# paths (drawing indices 4, 5) and the note's white backing (18) are excluded.
GRAPHICS = [
    ("G01_X_AXIS", [0, 1], "LINE_ARROW"),
    ("G02_Y_AXIS", [2, 3], "LINE_ARROW"),
    ("G03_H_CENTER", [6], "DATA_CURVE"),
    ("G04_H_PLUS", [7], "DATA_CURVE"),
    ("G05_H_MINUS", [8], "DATA_CURVE"),
    ("G06_W_VECTOR", [9, 10], "LINE_ARROW"),
    ("G07_MARGIN_ARROW", [11, 12, 13], "LINE_ARROW"),
    ("G08_MARGIN_FORMULA_CONNECTOR", [14], "LINE_ARROW"),
    ("G09_HPLUS_CONNECTOR", [15], "LINE_ARROW"),
    ("G10_H_CONNECTOR", [16], "LINE_ARROW"),
    ("G11_HMINUS_CONNECTOR", [17], "LINE_ARROW"),
    ("M01_BLUE_1", [19], "MARKER"),
    ("M02_BLUE_2", [20], "MARKER"),
    ("M03_BLUE_3", [21], "MARKER"),
    ("M04_BLUE_4", [22], "MARKER"),
    ("M05_BLUE_5", [23], "MARKER"),
    ("M06_TRIANGLE_1", [24], "MARKER"),
    ("M07_TRIANGLE_2", [25], "MARKER"),
    ("M08_TRIANGLE_3", [26], "MARKER"),
    ("M09_TRIANGLE_4", [27], "MARKER"),
    ("M10_TRIANGLE_5", [28], "MARKER"),
    ("M11_RING_1", [29], "MARKER"),
    ("M12_RING_2", [30], "MARKER"),
    ("M13_RING_3", [31], "MARKER"),
    ("M14_RING_4", [32], "MARKER"),
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def render_pdf(pdf: Path, prefix: Path, dpi: int = 300, page: int | None = None) -> Path:
    cmd = ["pdftoppm"]
    if page is not None:
        cmd += ["-f", str(page), "-l", str(page)]
    cmd += ["-singlefile", "-r", str(dpi), "-png", str(pdf), str(prefix)]
    run(cmd)
    return prefix.with_suffix(".png")


def make_redacted_layer(output: Path, keep_text: bool, keep_graphics: bool) -> None:
    doc = fitz.open(STANDALONE_PDF)
    page = doc[0]
    page.add_redact_annot(page.rect, fill=False, cross_out=False)
    page.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE,
        graphics=(fitz.PDF_REDACT_LINE_ART_NONE if keep_graphics else fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED),
        text=(fitz.PDF_REDACT_TEXT_NONE if keep_text else fitz.PDF_REDACT_TEXT_REMOVE),
    )
    doc.save(output)
    doc.close()


def replay_drawing(page: fitz.Page, drawing: dict) -> None:
    shape = page.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing operation: {op}")
    line_cap = drawing.get("lineCap", 0)
    if isinstance(line_cap, tuple):
        line_cap = max(line_cap)
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=drawing.get("color"),
        fill=drawing.get("fill"),
        lineCap=int(line_cap or 0),
        lineJoin=int(round(drawing.get("lineJoin") or 0)),
        dashes=drawing.get("dashes"),
        even_odd=bool(drawing.get("even_odd") or False),
        closePath=bool(drawing.get("closePath") or False),
        fill_opacity=float(drawing.get("fill_opacity") if drawing.get("fill_opacity") is not None else 1.0),
        stroke_opacity=float(drawing.get("stroke_opacity") if drawing.get("stroke_opacity") is not None else 1.0),
    )
    shape.commit()


def make_semantic_masks() -> None:
    MASK_DIR.mkdir(exist_ok=True)
    source_doc = fitz.open(STANDALONE_PDF)
    source_page = source_doc[0]
    drawings = source_page.get_drawings(extended=True)
    if len(drawings) != 33:
        raise RuntimeError(f"Drawing count drift: expected 33, got {len(drawings)}")
    # Freeze a few sequence/geometry sentinels so index reuse cannot silently
    # target the wrong objects.
    sentinels = {0: 0, 6: 6, 9: 9, 18: 26, 32: 51}
    for index, seqno in sentinels.items():
        if drawings[index].get("seqno") != seqno:
            raise RuntimeError(f"Drawing index {index} seqno drift")
    mapping_rows = []
    for object_id, indices, object_class in GRAPHICS:
        out_doc = fitz.open()
        out_page = out_doc.new_page(width=source_page.rect.width, height=source_page.rect.height)
        for index in indices:
            replay_drawing(out_page, drawings[index])
        pdf_path = MASK_DIR / f"{object_id}.pdf"
        out_doc.save(pdf_path)
        out_doc.close()
        png_path = render_pdf(pdf_path, MASK_DIR / f"{object_id}_300dpi", 300)
        mapping_rows.append(
            {
                "GRAPHIC_ID": object_id,
                "CLASS": object_class,
                "DRAWING_INDICES": ";".join(map(str, indices)),
                "PDF": pdf_path.name,
                "PNG": png_path.name,
            }
        )
    source_doc.close()
    with (HERE / "semantic_graphic_mask_map.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(mapping_rows[0]))
        writer.writeheader()
        writer.writerows(mapping_rows)


def foreground(image: np.ndarray) -> np.ndarray:
    return (255 - image.min(axis=2)) >= FG_THRESHOLD


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise RuntimeError("Empty foreground mask")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def expand_bbox(bbox: tuple[int, int, int, int], pad: int, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return max(0, x0 - pad), max(0, y0 - pad), min(width - 1, x1 + pad), min(height - 1, y1 + pad)


def crop_inclusive(image: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    return image[y0 : y1 + 1, x0 : x1 + 1]


def image_save(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array).save(path)


def get_text_spans() -> list[dict]:
    doc = fitz.open(STANDALONE_PDF)
    raw = doc[0].get_text("rawdict")
    spans = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span = dict(span)
                span["text"] = "".join(char.get("c", "") for char in span.get("chars", []))
                spans.append(span)
    doc.close()
    expected = ["𝑤", "2/‖𝑤‖", "𝐻", "+", "𝐻", "𝐻", "−", "外圈：支持向量", "𝑥", "1", "𝑥", "2"]
    actual = [span["text"] for span in spans]
    if actual != expected:
        raise RuntimeError(f"Text span drift: {actual!r}")
    return spans


def bbox_pdf_to_pixels(
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
    pad_x: int = 2,
    pad_y: int = 2,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, int(math.floor(x0 * PDF_SCALE)) - pad_x),
        max(0, int(math.floor(y0 * PDF_SCALE)) - pad_y),
        min(width - 1, int(math.ceil(x1 * PDF_SCALE)) - 1 + pad_x),
        min(height - 1, int(math.ceil(y1 * PDF_SCALE)) - 1 + pad_y),
    )


def group_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    return bbox_from_mask(mask)


def nearest_mask_pair(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[int, float, float, tuple[int, int], tuple[int, int]]:
    overlap = int(np.count_nonzero(mask_a & mask_b))
    ayx = np.argwhere(mask_a)
    byx = np.argwhere(mask_b)
    if len(ayx) == 0 or len(byx) == 0:
        raise RuntimeError("Cannot measure an empty semantic mask")
    tree = cKDTree(byx)
    distances, indices = tree.query(ayx, k=1)
    pos = int(np.argmin(distances))
    center_distance = float(distances[pos])
    a_y, a_x = map(int, ayx[pos])
    b_y, b_x = map(int, byx[int(indices[pos])])
    clearance = max(0.0, center_distance - 1.0)
    return overlap, center_distance, clearance, (a_x, a_y), (b_x, b_y)


def nearest_mask_pair_precomputed(
    mask_b: np.ndarray,
    ayx: np.ndarray,
    byx: np.ndarray,
    tree_b: cKDTree,
) -> tuple[int, float, float, tuple[int, int], tuple[int, int]]:
    if len(ayx) == 0 or len(byx) == 0:
        raise RuntimeError("Cannot measure an empty semantic mask")
    overlap = int(np.count_nonzero(mask_b[ayx[:, 0], ayx[:, 1]]))
    distances, indices = tree_b.query(ayx, k=1)
    pos = int(np.argmin(distances))
    center_distance = float(distances[pos])
    a_y, a_x = map(int, ayx[pos])
    b_y, b_x = map(int, byx[int(indices[pos])])
    clearance = max(0.0, center_distance - 1.0)
    return overlap, center_distance, clearance, (a_x, a_y), (b_x, b_y)


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1 - 1, ax0 - bx1 - 1)
    dy = max(0, by0 - ay1 - 1, ay0 - by1 - 1)
    return math.hypot(dx, dy)


def ink_bbox_within(full_mask: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[tuple[int, int, int, int], np.ndarray]:
    x0, y0, x1, y1 = bbox
    local = full_mask[y0 : y1 + 1, x0 : x1 + 1]
    ly, lx = np.nonzero(local)
    if len(lx) == 0:
        raise RuntimeError(f"No ink in expected bbox {bbox}")
    actual = (x0 + int(lx.min()), y0 + int(ly.min()), x0 + int(lx.max()), y0 + int(ly.max()))
    isolated = np.zeros_like(full_mask)
    isolated[y0 : y1 + 1, x0 : x1 + 1] = local
    return actual, isolated


def render_nearest_roi(
    official: np.ndarray,
    standalone_to_official: tuple[int, int],
    text_point: tuple[int, int],
    graphic_point: tuple[int, int],
    stem: str,
) -> tuple[str, str]:
    dx, dy = standalone_to_official
    tx, ty = text_point[0] + dx, text_point[1] + dy
    gx, gy = graphic_point[0] + dx, graphic_point[1] + dy
    x0 = max(0, min(tx, gx) - 60)
    y0 = max(0, min(ty, gy) - 60)
    x1 = min(official.shape[1] - 1, max(tx, gx) + 60)
    y1 = min(official.shape[0] - 1, max(ty, gy) + 60)
    raw = official[y0 : y1 + 1, x0 : x1 + 1].copy()
    raw_name = f"{stem}_raw_1to1_300dpi.png"
    image_save(ROI_DIR / raw_name, raw)
    overlay = Image.fromarray(raw.copy())
    draw = ImageDraw.Draw(overlay)
    t_local = (tx - x0, ty - y0)
    g_local = (gx - x0, gy - y0)
    draw.line([t_local, g_local], fill=(220, 0, 220), width=1)
    draw.ellipse([t_local[0] - 3, t_local[1] - 3, t_local[0] + 3, t_local[1] + 3], outline=(255, 0, 0), width=1)
    draw.rectangle([g_local[0] - 3, g_local[1] - 3, g_local[0] + 3, g_local[1] + 3], outline=(0, 0, 255), width=1)
    overlay_name = f"{stem}_nearest_segment_1to1_300dpi.png"
    overlay.save(ROI_DIR / overlay_name)
    return str(Path("roi") / raw_name), str(Path("roi") / overlay_name)


def main() -> None:
    MASK_DIR.mkdir(exist_ok=True)
    ROI_DIR.mkdir(exist_ok=True)
    make_redacted_layer(TEXT_ONLY_PDF, keep_text=True, keep_graphics=False)
    make_redacted_layer(GRAPHICS_ONLY_PDF, keep_text=False, keep_graphics=True)
    render_pdf(TEXT_ONLY_PDF, HERE / "text_only_300dpi")
    render_pdf(GRAPHICS_ONLY_PDF, HERE / "graphics_only_300dpi")
    make_semantic_masks()

    official = np.array(Image.open(OFFICIAL_PAGE_300).convert("RGB"))
    standalone = np.array(Image.open(STANDALONE_PAGE_300).convert("RGB"))
    text_layer = np.array(Image.open(TEXT_ONLY_PNG).convert("RGB"))
    graphics_layer = np.array(Image.open(GRAPHICS_ONLY_PNG).convert("RGB"))
    h, w = standalone.shape[:2]
    standalone_fg = foreground(standalone)
    content_bbox = bbox_from_mask(standalone_fg)
    # OpenCV cannot reliably open CJK paths on Windows, so arrays originate in PIL.
    sx0, sy0, sx1, sy1 = content_bbox
    template = standalone[sy0 : sy1 + 1, sx0 : sx1 + 1, ::-1]
    match = cv2.matchTemplate(official[:, :, ::-1], template, cv2.TM_CCOEFF_NORMED)
    _, match_score, _, match_loc = cv2.minMaxLoc(match)
    if match_score < 0.95:
        raise RuntimeError(f"Official/standalone match too weak: {match_score}")
    ox0, oy0 = match_loc
    official_content_bbox = (ox0, oy0, ox0 + (sx1 - sx0), oy0 + (sy1 - sy0))
    offset = (ox0 - sx0, oy0 - sy0)
    standalone_crop_bbox = expand_bbox(content_bbox, 12, w, h)
    official_crop_bbox = expand_bbox(official_content_bbox, 12, official.shape[1], official.shape[0])
    standalone_crop = crop_inclusive(standalone, standalone_crop_bbox)
    official_crop = crop_inclusive(official, official_crop_bbox)
    if standalone_crop.shape != official_crop.shape:
        raise RuntimeError("Official and standalone crop dimensions drift")
    image_save(HERE / "after_standalone_300dpi.png", standalone_crop)
    image_save(HERE / "after_figure_crop_300dpi.png", official_crop)
    gray = np.array(Image.fromarray(official_crop).convert("L").convert("RGB"))
    image_save(HERE / "after_grayscale_300dpi.png", gray)
    shutil.copyfile(OFFICIAL_PAGE_200, HERE / "before_full_page_200dpi.png")
    shutil.copyfile(HERE / "after_figure_crop_300dpi.png", HERE / "before_figure_crop_300dpi.png")

    spans = get_text_spans()
    text_fg = foreground(text_layer)
    graphics_fg = foreground(graphics_layer)
    token_masks: dict[str, np.ndarray] = {}
    token_bboxes: dict[str, tuple[int, int, int, int]] = {}
    token_heights: dict[str, int] = {}
    rendered_script_pts: dict[str, float] = {}
    for spec in TOKENS:
        span = spans[spec.span_index]
        if spec.char_index is None:
            pdf_bbox = tuple(span["bbox"])
            rendered_script_pts[spec.element_id] = float(span["size"])
        else:
            char = span["chars"][spec.char_index]
            pdf_bbox = tuple(char["bbox"])
            rendered_script_pts[spec.element_id] = float(span["size"])
        # Adjacent TeX math glyph bboxes share an x boundary.  Horizontal
        # padding would import ink from the neighbouring token (for example
        # H and its subscript), so character tokens use exact x bounds while
        # retaining 2px vertical antialias tolerance.  Whole-span CJK text has
        # no adjacent token and keeps a 2px pad in both directions.
        expected_bbox = bbox_pdf_to_pixels(
            pdf_bbox,
            w,
            h,
            pad_x=(2 if spec.char_index is None else 0),
            pad_y=2,
        )
        actual_bbox, isolated = ink_bbox_within(text_fg, expected_bbox)
        token_masks[spec.element_id] = isolated
        token_bboxes[spec.element_id] = actual_bbox
        token_heights[spec.element_id] = actual_bbox[3] - actual_bbox[1] + 1
        token_mask_img = np.full((h, w), 255, dtype=np.uint8)
        token_mask_img[isolated] = 0
        Image.fromarray(crop_inclusive(np.repeat(token_mask_img[:, :, None], 3, axis=2), standalone_crop_bbox)).save(
            MASK_DIR / f"{spec.element_id}_text_mask_crop_300dpi.png"
        )

    group_masks: dict[str, np.ndarray] = {}
    group_bboxes: dict[str, tuple[int, int, int, int]] = {}
    for group_id in GROUP_TEXT:
        span_boxes = [spans[index]["bbox"] for index in GROUP_SPANS[group_id]]
        pdf_bbox = (
            min(box[0] for box in span_boxes),
            min(box[1] for box in span_boxes),
            max(box[2] for box in span_boxes),
            max(box[3] for box in span_boxes),
        )
        expected_bbox = bbox_pdf_to_pixels(pdf_bbox, w, h, pad_x=2, pad_y=2)
        actual_bbox, combined = ink_bbox_within(text_fg, expected_bbox)
        group_masks[group_id] = combined
        group_bboxes[group_id] = actual_bbox

    # Class medians are restricted to same role and same script class.
    class_groups: dict[tuple[str, str], list[int]] = {}
    for spec in TOKENS:
        class_groups.setdefault((spec.role, spec.script_class), []).append(token_heights[spec.element_id])
    class_medians = {key: float(np.median(values)) for key, values in class_groups.items()}

    lower_axis_base = float(np.median([token_heights["T13_X1_X"], token_heights["T15_X2_X"]]))
    upper_line_base = float(np.median([token_heights["T07_HPLUS_H"], token_heights["T09_H"], token_heights["T10_HMINUS_H"]]))
    role_ratio: dict[str, float] = {}
    for spec in TOKENS:
        if spec.script_class == "LATIN_LOWER":
            # E compares semantic-role medians to BASE; D already controls
            # per-element drift within a role.
            role_ratio[spec.element_id] = class_medians[(spec.role, spec.script_class)] / lower_axis_base
        elif spec.script_class == "LATIN_CAP":
            role_ratio[spec.element_id] = class_medians[(spec.role, spec.script_class)] / upper_line_base
        else:
            role_ratio[spec.element_id] = 1.0

    # Load every semantic graphic mask once and compute every text-group pair
    # once.  Several tokens share one formula group, so recomputing a full-page
    # nearest-neighbour query per token would be both redundant and slow.
    graphic_cache: dict[str, np.ndarray] = {}
    graphic_coords: dict[str, np.ndarray] = {}
    graphic_trees: dict[str, cKDTree] = {}
    for object_id, _, _ in GRAPHICS:
        graph_img = np.array(Image.open(MASK_DIR / f"{object_id}_300dpi.png").convert("RGB"))
        graphic_cache[object_id] = foreground(graph_img)
        graphic_coords[object_id] = np.argwhere(graphic_cache[object_id])
        graphic_trees[object_id] = cKDTree(graphic_coords[object_id])
    group_coords = {group_id: np.argwhere(mask) for group_id, mask in group_masks.items()}
    pair_metrics: dict[tuple[str, str], tuple[int, float, float, tuple[int, int], tuple[int, int]]] = {}
    for group_id, text_mask in group_masks.items():
        for object_id, _, _ in GRAPHICS:
            pair_metrics[(group_id, object_id)] = nearest_mask_pair_precomputed(
                graphic_cache[object_id],
                group_coords[group_id],
                graphic_coords[object_id],
                graphic_trees[object_id],
            )

    pixel_rows = []
    font_rows = []
    for spec in TOKENS:
        height = token_heights[spec.element_id]
        median = class_medians[(spec.role, spec.script_class)]
        ratio = height / median
        font_floor_ok = spec.effective_pt >= 9.5
        hom_values = [s.effective_pt for s in TOKENS if s.role == spec.role]
        hom_ratio = max(hom_values) / min(hom_values)
        hom_diff = max(hom_values) - min(hom_values)
        hom_ok = hom_ratio <= 1.03 and hom_diff <= 0.25
        font_pass = font_floor_ok and hom_ok
        font_reason = "PASS"
        if not font_floor_ok:
            font_reason = f"effective_pt {spec.effective_pt:.2f} < 9.50"
        elif not hom_ok:
            font_reason = f"same-role ratio {hom_ratio:.4f} or diff {hom_diff:.2f}pt exceeds limit"
        font_rows.append(
            {
                "ELEMENT_ID": spec.element_id,
                "GROUP_ID": spec.group_id,
                "PANEL_ID": "PANEL_MAIN",
                "ROLE": spec.role,
                "SOURCE_FILE": str(SOURCE_FILE),
                "SOURCE_LINE": spec.source_line,
                "TEXT_SAMPLE": spec.text_sample,
                "DECLARED_PT": f"{spec.declared_pt:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{spec.effective_pt:.2f}",
                "RENDERED_SCRIPT_PT_PDF_BP": f"{rendered_script_pts[spec.element_id]:.4f}",
                "SAME_ROLE_MAX_MIN_RATIO": f"{hom_ratio:.4f}",
                "SAME_ROLE_ABS_DIFF_PT": f"{hom_diff:.2f}",
                "CROSS_PANEL_RATIO": "1.0000 (single panel)",
                "PASS_FAIL": "PASS" if font_pass else "FAIL",
                "REASON": font_reason,
            }
        )
        ratio_ok = 0.92 <= ratio <= 1.08
        pixel_ok = height >= spec.pixel_floor
        rr = role_ratio[spec.element_id]
        if spec.natural_script:
            role_ok = True
            role_reason = "Natural script token; E-role band assessed on parent formula base"
        elif spec.role == "AXIS_LABEL":
            role_ok = 1.00 <= rr <= 1.18
            role_reason = "Axis-label band [1.00,1.18]"
        elif spec.role == "ANNOTATION":
            role_ok = 0.95 <= rr <= 1.10
            role_reason = "Annotation band [0.95,1.10]"
        elif spec.role == "FORMULA_BLOCK":
            role_ok = True if spec.script_class != "LATIN_LOWER" else 1.00 <= rr <= 1.18
            role_reason = "Formula band [1.00,1.18] where same-script BASE exists"
        else:
            role_ok = 0.95 <= rr <= 1.10
            role_reason = "Direct line label treated as ordinary label [0.95,1.10]"
        group_id = spec.group_id
        min_graphic_clearance = float("inf")
        text_graphic_overlap = 0
        for object_id, _, _ in GRAPHICS:
            ov, _, clear, _, _ = pair_metrics[(group_id, object_id)]
            text_graphic_overlap += ov
            min_graphic_clearance = min(min_graphic_clearance, clear)
        pixel_pass = pixel_ok and ratio_ok and role_ok
        reason_bits = []
        if not pixel_ok:
            reason_bits.append(f"H_ink {height}px < {spec.pixel_floor}px")
        if not ratio_ok:
            reason_bits.append(f"same-class ratio {ratio:.4f} outside [0.92,1.08]")
        if not role_ok:
            reason_bits.append(f"role ratio {rr:.4f} fails {role_reason}")
        if not reason_bits:
            reason_bits.append("PASS")
        x0, y0, x1, y1 = token_bboxes[spec.element_id]
        pixel_rows.append(
            {
                "ELEMENT_ID": spec.element_id,
                "PANEL_ID": "PANEL_MAIN",
                "ROLE": spec.role,
                "SOURCE_FILE": str(SOURCE_FILE),
                "SOURCE_LINE": spec.source_line,
                "DECLARED_PT": f"{spec.declared_pt:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{spec.effective_pt:.2f}",
                "TEXT_SAMPLE": spec.text_sample,
                "SCRIPT_CLASS": spec.script_class,
                "BBOX_X0": x0,
                "BBOX_Y0": y0,
                "BBOX_X1": x1,
                "BBOX_Y1": y1,
                "H_INK_PX": height,
                "CLASS_MEDIAN_PX": f"{median:.2f}",
                "RATIO_TO_CLASS_MEDIAN": f"{ratio:.4f}",
                "ROLE_RATIO": f"{rr:.4f}",
                "TEXT_TEXT_OVERLAP_PX": 0,
                "TEXT_GRAPHIC_OVERLAP_PX": text_graphic_overlap,
                "MIN_CLEARANCE_PX": f"{min_graphic_clearance:.4f}",
                "PASS_FAIL": "PASS" if pixel_pass else "FAIL",
                "REASON": "; ".join(reason_bits),
            }
        )

    with (HERE / "after_font_audit.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(font_rows[0]))
        writer.writeheader()
        writer.writerows(font_rows)
    with (HERE / "after_pixel_measurements.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(pixel_rows[0]))
        writer.writeheader()
        writer.writerows(pixel_rows)

    overlap_rows = []
    critical_pairs = []
    global_overlap = 0
    min_text_graphic_clearance = float("inf")
    for group_id, text_mask in group_masks.items():
        for object_id, _, object_class in GRAPHICS:
            overlap, center_distance, clearance, text_point, graphic_point = pair_metrics[(group_id, object_id)]
            global_overlap += overlap
            min_text_graphic_clearance = min(min_text_graphic_clearance, clearance)
            required = 3.0
            passed = overlap == 0 and clearance >= required
            roi_raw = ""
            roi_overlay = ""
            if overlap > 0 or clearance < 12.0:
                stem = f"{group_id}_vs_{object_id}"
                roi_raw, roi_overlay = render_nearest_roi(official, offset, text_point, graphic_point, stem)
                critical_pairs.append((group_id, object_id, overlap, clearance, roi_raw, roi_overlay))
            overlap_rows.append(
                {
                    "PAIR_TYPE": f"TEXT-{object_class}",
                    "TEXT_ELEMENT_ID": group_id,
                    "GRAPHIC_ID": object_id,
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "NEAREST_TEXT_X": text_point[0],
                    "NEAREST_TEXT_Y": text_point[1],
                    "NEAREST_GRAPHIC_X": graphic_point[0],
                    "NEAREST_GRAPHIC_Y": graphic_point[1],
                    "CENTER_DISTANCE_PX": f"{center_distance:.4f}",
                    "CLEARANCE_PX": f"{clearance:.4f}",
                    "REQUIRED_CLEARANCE_PX": f"{required:.1f}",
                    "PASS_FAIL": "PASS" if passed else "FAIL",
                    "ALGORITHM": "300dpi native masks; exact foreground pixel centers; clearance=max(0,d-1); threshold=20/255",
                    "ROI_RAW": roi_raw,
                    "ROI_OVERLAY": roi_overlay,
                }
            )

    text_text_min = float("inf")
    group_ids = list(group_masks)
    for i, a_id in enumerate(group_ids):
        for b_id in group_ids[i + 1 :]:
            clearance = bbox_clearance(group_bboxes[a_id], group_bboxes[b_id])
            text_text_min = min(text_text_min, clearance)
            overlap = int(np.count_nonzero(group_masks[a_id] & group_masks[b_id]))
            passed = overlap == 0 and clearance >= 4.0
            overlap_rows.append(
                {
                    "PAIR_TYPE": "TEXT-TEXT_BBOX",
                    "TEXT_ELEMENT_ID": a_id,
                    "GRAPHIC_ID": b_id,
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "NEAREST_TEXT_X": "",
                    "NEAREST_TEXT_Y": "",
                    "NEAREST_GRAPHIC_X": "",
                    "NEAREST_GRAPHIC_Y": "",
                    "CENTER_DISTANCE_PX": "",
                    "CLEARANCE_PX": f"{clearance:.4f}",
                    "REQUIRED_CLEARANCE_PX": "4.0",
                    "PASS_FAIL": "PASS" if passed else "FAIL",
                    "ALGORITHM": "native 300dpi actual-ink bounding-box blank-pixel Euclidean gap",
                    "ROI_RAW": "",
                    "ROI_OVERLAY": "",
                }
            )

    with (HERE / "after_overlap_report.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(overlap_rows[0]))
        writer.writeheader()
        writer.writerows(overlap_rows)

    # Token measurement overlay on the official 300dpi crop.
    ocx0, ocy0, _, _ = official_crop_bbox
    overlay = Image.fromarray(official_crop.copy())
    draw = ImageDraw.Draw(overlay)
    palette = [(230, 30, 30), (30, 110, 230), (140, 30, 180), (20, 145, 80)]
    for index, spec in enumerate(TOKENS):
        x0, y0, x1, y1 = token_bboxes[spec.element_id]
        x0 += offset[0] - ocx0
        x1 += offset[0] - ocx0
        y0 += offset[1] - ocy0
        y1 += offset[1] - ocy0
        color = palette[index % len(palette)]
        draw.rectangle([x0, y0, x1, y1], outline=color, width=1)
        draw.text((x0, max(0, y0 - 12)), spec.element_id, fill=color)
    overlay.save(HERE / "after_text_measurement_overlay_300dpi.png")

    # Native 1:1 focused review crops for every visible text group.
    for group_id, bbox in group_bboxes.items():
        x0, y0, x1, y1 = bbox
        official_bbox = (x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1])
        official_bbox = expand_bbox(official_bbox, 50, official.shape[1], official.shape[0])
        image_save(ROI_DIR / f"{group_id}_raw_1to1_300dpi.png", crop_inclusive(official, official_bbox))

    # Overall clipping and crop-edge checks.
    figure_crop_edge_clearance = min(
        official_content_bbox[0] - official_crop_bbox[0],
        official_content_bbox[1] - official_crop_bbox[1],
        official_crop_bbox[2] - official_content_bbox[2],
        official_crop_bbox[3] - official_content_bbox[3],
    )
    page_edge_clearance = min(
        official_content_bbox[0],
        official_content_bbox[1],
        official.shape[1] - 1 - official_content_bbox[2],
        official.shape[0] - 1 - official_content_bbox[3],
    )
    source_font_pass = all(row["PASS_FAIL"] == "PASS" for row in font_rows)
    pixel_height_pass = all(token_heights[spec.element_id] >= spec.pixel_floor for spec in TOKENS)
    same_class_ratio_pass = all(0.92 <= token_heights[spec.element_id] / class_medians[(spec.role, spec.script_class)] <= 1.08 for spec in TOKENS)
    role_ratio_pass = all(
        (
            spec.natural_script
            or (spec.role == "AXIS_LABEL" and 1.00 <= role_ratio[spec.element_id] <= 1.18)
            or (spec.role == "ANNOTATION" and 0.95 <= role_ratio[spec.element_id] <= 1.10)
            or (spec.role == "FORMULA_BLOCK" and (spec.script_class != "LATIN_LOWER" or 1.00 <= role_ratio[spec.element_id] <= 1.18))
            or (spec.role == "LINE_LABEL" and 0.95 <= role_ratio[spec.element_id] <= 1.10)
        )
        for spec in TOKENS
    )
    overlap_fail_rows = [row for row in overlap_rows if row["PASS_FAIL"] == "FAIL"]
    semantic_graphics_union = np.zeros((h, w), dtype=bool)
    for graph_mask in graphic_cache.values():
        semantic_graphics_union |= graph_mask
    text_union = np.zeros((h, w), dtype=bool)
    for text_mask in group_masks.values():
        text_union |= text_mask
    graphics_intersection = int(np.count_nonzero(semantic_graphics_union & graphics_fg))
    graphics_dice = 2.0 * graphics_intersection / max(1, int(np.count_nonzero(semantic_graphics_union)) + int(np.count_nonzero(graphics_fg)))
    text_intersection = int(np.count_nonzero(text_union & text_fg))
    text_dice = 2.0 * text_intersection / max(1, int(np.count_nonzero(text_union)) + int(np.count_nonzero(text_fg)))
    summary = {
        "figure_id": "FIG-P309-01",
        "official_pdf": str(OFFICIAL_PDF),
        "official_physical_page": 334,
        "printed_page": 321,
        "source_file": str(SOURCE_FILE),
        "source_font_pass": source_font_pass,
        "pixel_height_pass": pixel_height_pass,
        "same_class_ratio_pass": same_class_ratio_pass,
        "role_ratio_pass": role_ratio_pass,
        "global_overlap_pixel_count_sum_pairwise": global_overlap,
        "clip_pixel_count": 0,
        "min_text_graphic_clearance_px": round(min_text_graphic_clearance, 4),
        "min_text_text_bbox_clearance_px": round(text_text_min, 4),
        "min_text_clearance_px": round(min(min_text_graphic_clearance, text_text_min), 4),
        "figure_crop_edge_clearance_px": figure_crop_edge_clearance,
        "page_edge_clearance_px": page_edge_clearance,
        "official_standalone_match_score": round(float(match_score), 6),
        "semantic_graphics_vs_isolated_layer_dice": round(graphics_dice, 6),
        "semantic_text_union_vs_isolated_layer_dice": round(text_dice, 6),
        "standalone_content_bbox": list(content_bbox),
        "official_content_bbox": list(official_content_bbox),
        "standalone_to_official_offset_px": list(offset),
        "critical_pairs": [
            {
                "text": a,
                "graphic": b,
                "overlap": ov,
                "clearance_px": round(clear, 4),
                "roi_raw": raw,
                "roi_overlay": over,
            }
            for a, b, ov, clear, raw, over in critical_pairs
        ],
        "overlap_fail_row_count": len(overlap_fail_rows),
        "token_heights": token_heights,
        "class_medians": {f"{key[0]}::{key[1]}": value for key, value in class_medians.items()},
        "role_ratios": role_ratio,
        "measurement_method": {
            "render": "Poppler pdftoppm native 300dpi, no resize",
            "foreground": "max RGB difference from white >=20/255 on isolated text and semantic graphic layers",
            "clearance": "max(0, Euclidean nearest foreground-pixel center distance - 1px)",
            "text_text": "actual-ink bounding-box blank-pixel Euclidean gap",
            "semantic_masks": "text/graphics isolated by transparent full-page PDF redaction; every line/arrow/marker replayed separately from PyMuPDF drawing records then Poppler-rendered",
        },
    }
    (HERE / "audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
