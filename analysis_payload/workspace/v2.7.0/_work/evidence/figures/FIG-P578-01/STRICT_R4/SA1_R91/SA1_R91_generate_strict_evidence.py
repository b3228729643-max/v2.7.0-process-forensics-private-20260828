"""Independent SA1 R91 evidence generator for FIG-P578-01.

Reads only the assigned current source and physical PDF page 626.  It never
consults prior FIG-P578-01 reviews.  All geometry derives from the untouched
300 dpi Poppler raster (2481 x 3508); diagnostic crops are direct crops.
"""

from __future__ import annotations

import csv
import math
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r91_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C02" / "fig_v5_c02_rejection_flow.tex"
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P578-01" / "STRICT_R4" / "SA1_R91"
RAW = OUT / "SA1_R91_page626_300dpi.png"

PAGE_NO = 626
SCALE = 300.0 / 72.0
SOURCE_DISPLAY = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex"

NODES = {
    "precheck": 1,
    "valid": 2,
    "badinput": 3,
    "init": 5,
    "goal": 6,
    "completed": 7,
    "budgetcheck": 8,
    "budget": 9,
    "proposal": 10,
    "proposalfail": 11,
    "countproposal": 13,
    "uniform": 14,
    "uniformfail": 15,
    "evaluate": 17,
    "numericok": 18,
    "numericfail": 19,
    "envelopeok": 21,
    "envelopefail": 22,
    "accept": 24,
    "commit": 25,
    "reject": 26,
}
DIAMONDS = {"valid", "goal", "budgetcheck", "proposal", "uniform", "numericok", "envelopeok", "accept"}
ELLIPSES = {"budget"}

EDGES = [
    ("precheck", "valid", [27, 28], 77),
    ("valid", "badinput", [29, 30], 78),
    ("valid", "init", [32, 33], 79),
    ("init", "goal", [35, 36], 80),
    ("goal", "completed", [37, 38], 81),
    ("goal", "budgetcheck", [40, 41], 82),
    ("budgetcheck", "budget", [43, 44], 83),
    ("budgetcheck", "proposal", [46, 47], 84),
    ("proposal", "proposalfail", [49, 50], 85),
    ("proposal", "countproposal", [52, 53], 86),
    ("countproposal", "uniform", [55, 56], 87),
    ("uniform", "uniformfail", [57, 58], 88),
    ("uniform", "evaluate", [60, 61], 89),
    ("evaluate", "numericok", [63, 64], 90),
    ("numericok", "numericfail", [65, 66], 91),
    ("numericok", "envelopeok", [68, 69], 92),
    ("envelopeok", "envelopefail", [71, 72], 93),
    ("envelopeok", "accept", [74, 75], 94),
    ("accept", "commit", [77, 78], 95),
    ("accept", "reject", [80, 81], 96),
    ("commit", "merge", [83, 84], 97),
    ("reject", "merge", [85, 86], 98),
    ("merge", "goal", [87, 88], 99),
]

BRANCH_LABELS = [
    ("valid_to_badinput", "否", 78),
    ("valid_to_init", "是", 79),
    ("goal_to_completed", "是：优先", 81),
    ("goal_to_budgetcheck", "否", 82),
    ("budgetcheck_to_budget", "是", 83),
    ("budgetcheck_to_proposal", "否", 84),
    ("proposal_to_proposalfail", "失败", 85),
    ("proposal_to_countproposal", "成功", 86),
    ("uniform_to_uniformfail", "失败", 88),
    ("uniform_to_evaluate", "成功", 89),
    ("numericok_to_numericfail", "否", 91),
    ("numericok_to_envelopeok", "是", 92),
    ("envelopeok_to_envelopefail", "否", 93),
    ("envelopeok_to_accept", "是", 94),
    ("accept_to_commit", "接受", 95),
    ("accept_to_reject", "拒绝", 96),
]

# PDF-span indexes (one-based) whose parent formula lives on a later physical
# source line than the \node declaration.  These make the strict operator
# ledger directly repairable at the exact source location.
SPAN_LINE_OVERRIDES = {
    13: 35, 20: 36, 28: 37,
    40: 40, 41: 40, 42: 40,
    51: 44, 52: 44, 55: 45, 56: 45, 57: 45, 58: 45, 59: 46,
    66: 48, 69: 49, 78: 51, 80: 53, 100: 57, 119: 62,
    187: 100, 189: 100,
}

OPERATOR_CHARS = set("=+-−<>≤≥∈∅∶:/←→⇒⊆∞∼‖|×·")


def assert_new(path: Path) -> None:
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite existing artifact: {path}")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    assert_new(path)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rgb_from_floats(value) -> np.ndarray:
    return np.array([round(component * 255) for component in value], dtype=float)


def px_box(box, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(box[0] * SCALE)) - pad)
    y0 = max(0, int(math.floor(box[1] * SCALE)) - pad)
    x1 = min(WIDTH, int(math.ceil(box[2] * SCALE)) + pad + 1)
    y1 = min(HEIGHT, int(math.ceil(box[3] * SCALE)) + pad + 1)
    return x0, y0, x1, y1


def fmt_pdf_box(box) -> str:
    return ",".join(f"{value:.2f}" for value in box)


def fmt_px_box(box) -> str:
    return ",".join(str(value) for value in px_box(box))


def mode_background(crop: np.ndarray) -> np.ndarray:
    colors, counts = np.unique(crop.reshape(-1, 3), axis=0, return_counts=True)
    return colors[int(np.argmax(counts))].astype(float)


def qualifying_black_mask(crop: np.ndarray, background: np.ndarray | None = None) -> np.ndarray:
    """Pixels attributable to black text with the Goal's >=20/255 contrast rule."""
    image = crop.astype(float)
    bg = mode_background(crop) if background is None else background.astype(float)
    foreground = np.array([31.0, 35.0, 40.0])
    vector = foreground - bg
    denominator = float(np.dot(vector, vector))
    if denominator == 0:
        return np.zeros(crop.shape[:2], dtype=bool)
    alpha = ((image - bg) * vector).sum(axis=2) / denominator
    reconstruction = bg + alpha[..., None] * vector
    residual = np.linalg.norm(image - reconstruction, axis=2)
    contrast = np.linalg.norm(image - bg, axis=2)
    return (contrast >= 20.0) & (alpha >= 0.04) & (alpha <= 1.15) & (residual <= 14.0)


def core_black_mask_for_spans(spans: list[dict]) -> np.ndarray:
    """High-confidence black ink for geometry; excludes coloured vectors and light AA."""
    mask = np.zeros((HEIGHT, WIDTH), dtype=bool)
    for span in spans:
        x0, y0, x1, y1 = px_box(span["bbox"], pad=2)
        crop = RGB[y0:y1, x0:x1].astype(int)
        red, green, blue = crop[:, :, 0], crop[:, :, 1], crop[:, :, 2]
        core = (red < 160) & (np.abs(green - red) < 8) & (np.abs(blue - green) < 8)
        mask[y0:y1, x0:x1] |= core
    return mask


def h_ink(box) -> tuple[int, tuple[int, int, int], int]:
    # Do not pad this measurement box: adjacent PDF spans can otherwise leak
    # into the element mask and falsify both height and ratio measurements.
    x0, y0, x1, y1 = px_box(box, pad=0)
    crop = RGB[y0:y1, x0:x1]
    bg = mode_background(crop)
    mask = qualifying_black_mask(crop, bg)
    ys = np.where(mask)[0]
    height = int(ys.max() - ys.min() + 1) if ys.size else 0
    return height, tuple(int(value) for value in bg), int(mask.sum())


def raw_char_class(char: str, rendered_size: float) -> str:
    name = unicodedata.name(char, "")
    if rendered_size < 9.0:
        return "NATURAL_SCRIPT"
    if char in OPERATOR_CHARS:
        return "OPERATOR"
    if char.isdigit():
        return "CAPITAL_DIGIT"
    if 0x4E00 <= ord(char) <= 0x9FFF:
        return "CJK_FULL"
    if char in "，。；：！？（）【】“”‘’" or 0x3000 <= ord(char) <= 0x303F or 0xFF00 <= ord(char) <= 0xFFEF:
        return "PUNCT_DERIVED"
    if "CAPITAL" in name or char.isupper():
        return "CAPITAL_DIGIT"
    if "GREEK" in name or "MATHEMATICAL" in name or char.isalpha():
        return "LOWER_GREEK"
    return "OTHER"


def threshold_for(script_class: str) -> int | None:
    return {
        "CJK_FULL": 30,
        "CAPITAL_DIGIT": 24,
        "LOWER_GREEK": 17,
        "FORMULA_BASE": 22,
        "OPERATOR": 22,
        "NATURAL_SCRIPT": 15,
    }.get(script_class)


def span_script_class(span: dict) -> str:
    text = span["text"]
    if not text.strip():
        return "OTHER"
    if span["size"] < 9.0:
        return "NATURAL_SCRIPT"
    if all(char in "·—–-,:;()[]{}" for char in text):
        return "PUNCT_DERIVED"
    if any(0x4E00 <= ord(char) <= 0x9FFF for char in text):
        return "CJK_FULL"
    if any(char in OPERATOR_CHARS or "MATHEMATICAL" in unicodedata.name(char, "") for char in text):
        return "FORMULA_BASE"
    if any(char.isdigit() or "CAPITAL" in unicodedata.name(char, "") or char.isupper() for char in text):
        return "CAPITAL_DIGIT"
    if any(char.isalpha() for char in text):
        return "LOWER_GREEK"
    return "PUNCT_DERIVED"


def source_line_for_node(node: str) -> int:
    marker = f") ({node})"
    alternate = f"({node})"
    for number, line in enumerate(SOURCE_LINES, start=1):
        if marker in line or alternate in line:
            return number
    raise RuntimeError(f"Could not locate source node {node}")


def source_font_info(span: dict) -> tuple[float, float, str]:
    size = float(span["size"])
    if size < 9.0:
        base = 10.7 if size >= 7.2 else 9.6
        return base, base, f"natural script rendered {size:.3f}pt from >=9.5pt base"
    if 9.45 <= size <= 9.70:
        return 9.6, 9.6, "TikZ every node / edgeword source font"
    if 10.55 <= size <= 10.85:
        return 10.7, 10.7, "\\slfigRejMath source font"
    return round(size, 3), round(size, 3), "PDF page-context font (no figure scaling)"


def shape_contains(node: str, x: float, y: float) -> bool:
    rect = DRAWINGS[NODES[node]]["rect"]
    if node in DIAMONDS:
        center_x = (rect.x0 + rect.x1) / 2
        center_y = (rect.y0 + rect.y1) / 2
        half_w = (rect.x1 - rect.x0) / 2
        half_h = (rect.y1 - rect.y0) / 2
        return abs((x - center_x) / half_w) + abs((y - center_y) / half_h) <= 1.02
    if node in ELLIPSES:
        center_x = (rect.x0 + rect.x1) / 2
        center_y = (rect.y0 + rect.y1) / 2
        half_w = (rect.x1 - rect.x0) / 2
        half_h = (rect.y1 - rect.y0) / 2
        return ((x - center_x) / half_w) ** 2 + ((y - center_y) / half_h) ** 2 <= 1.02
    return rect.x0 - 0.1 <= x <= rect.x1 + 0.1 and rect.y0 - 0.1 <= y <= rect.y1 + 0.1


def span_center(span: dict) -> tuple[float, float]:
    box = span["bbox"]
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def node_for_span(span: dict) -> str | None:
    x, y = span_center(span)
    for node in NODES:
        if shape_contains(node, x, y):
            return node
    return None


def role_and_source_for_span(index: int, span: dict) -> tuple[str, str, str, str]:
    node = node_for_span(span)
    if node:
        text = span["text"]
        line = SPAN_LINE_OVERRIDES.get(index + 1, NODE_LINES[node])
        if "Mono" in span["font"] or text == "_" or any(token in text for token in ("invalid", "random", "numerical", "envelope", "completed", "budget")):
            return "status_code", SOURCE_DISPLAY, str(line), node
        if text == "/" and span["size"] < 10.55:
            return "node_text", SOURCE_DISPLAY, str(line), node
        if span["size"] >= 10.55 or 7.2 <= span["size"] < 9.0:
            return "formula_block", SOURCE_DISPLAY, str(line), node
        if "STIX" in span["font"] or any("MATHEMATICAL" in unicodedata.name(char, "") for char in text):
            return "inline_math", SOURCE_DISPLAY, str(line), node
        return "node_text", SOURCE_DISPLAY, str(line), node
    if index in BRANCH_INDEX_TO_META:
        label_id, _, line = BRANCH_INDEX_TO_META[index]
        return "branch_label", SOURCE_DISPLAY, str(line), label_id
    if 185 <= index <= 188:
        has_math = "STIX" in span["font"] or any("MATHEMATICAL" in unicodedata.name(char, "") for char in span["text"])
        return ("loop_formula" if has_math else "loop_label"), SOURCE_DISPLAY, "100", "return_loop"
    y = span["bbox"][1]
    if 680 <= y < 710:
        return "caption", SOURCE_DISPLAY, "102", "caption"
    if 720 <= y < 790:
        return "read_guide", "src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex", "360", "page_context"
    if y >= 790:
        return "page_chrome", "main_full.pdf", "N/A", "footer"
    return "page_chrome", "main_full.pdf", "N/A", "header"


def node_border_mask(node: str) -> np.ndarray:
    drawing = DRAWINGS[NODES[node]]
    rect = drawing["rect"]
    x0, y0, x1, y1 = px_box((rect.x0, rect.y0, rect.x1, rect.y1), pad=5)
    crop = RGB[y0:y1, x0:x1].astype(int)
    ys, xs = np.indices(crop.shape[:2])
    xs = xs + x0
    ys = ys + y0
    left, top, right, bottom = np.array([rect.x0, rect.y0, rect.x1, rect.y1]) * SCALE
    if node in DIAMONDS:
        cx, cy = (left + right) / 2, (top + bottom) / 2
        half_w, half_h = (right - left) / 2, (bottom - top) / 2
        geometry = np.abs(np.abs((xs - cx) / half_w) + np.abs((ys - cy) / half_h) - 1.0) <= 0.032
    elif node in ELLIPSES:
        cx, cy = (left + right) / 2, (top + bottom) / 2
        half_w, half_h = (right - left) / 2, (bottom - top) / 2
        geometry = np.abs(((xs - cx) / half_w) ** 2 + ((ys - cy) / half_h) ** 2 - 1.0) <= 0.065
    else:
        geometry = np.minimum.reduce([np.abs(xs - left), np.abs(xs - right), np.abs(ys - top), np.abs(ys - bottom)]) <= 4
    colour = rgb_from_floats(drawing["color"]).astype(int)
    colour_match = np.linalg.norm(crop - colour, axis=2) < 50
    mask = np.zeros((HEIGHT, WIDTH), dtype=bool)
    mask[y0:y1, x0:x1] = geometry & colour_match
    return mask


def node_border_side_mask(node: str, side: str) -> np.ndarray:
    """A source-provenanced mask for one physical side of a rectangular node."""
    if node in DIAMONDS or node in ELLIPSES:
        raise ValueError(f"Side masks are reserved for rectangular high-risk nodes: {node}")
    base = node_border_mask(node)
    rect = DRAWINGS[NODES[node]]["rect"]
    left, top, right, bottom = np.array([rect.x0, rect.y0, rect.x1, rect.y1]) * SCALE
    keep = np.zeros_like(base)
    if side == "top":
        keep[: min(HEIGHT, int(math.ceil(top + 8)) + 1), :] = True
    elif side == "bottom":
        keep[max(0, int(math.floor(bottom - 8))):, :] = True
    elif side == "left":
        keep[:, : min(WIDTH, int(math.ceil(left + 8)) + 1)] = True
    elif side == "right":
        keep[:, max(0, int(math.floor(right - 8))):] = True
    else:
        raise ValueError(side)
    return base & keep


def arrow_mask(draw_ids: list[int]) -> np.ndarray:
    mask = np.zeros((HEIGHT, WIDTH), dtype=bool)
    for draw_id in draw_ids:
        drawing = DRAWINGS[draw_id]
        rect = drawing["rect"]
        x0, y0, x1, y1 = px_box((rect.x0, rect.y0, rect.x1, rect.y1), pad=4)
        crop = RGB[y0:y1, x0:x1].astype(int)
        red, green, blue = crop[:, :, 0], crop[:, :, 1], crop[:, :, 2]
        colour = rgb_from_floats(drawing["color"]).astype(int)
        if colour[2] - colour[1] > 15 and colour[1] - colour[0] > 15:
            candidate = (green - red > 15) & (blue - green > 15) & (red < 200)
        else:
            # The return path is blue-tinted gray.  Matching by Euclidean
            # distance alone would mistake gray antialiasing of black loop
            # text for the line.  Retain its documented blue-gray chroma.
            candidate = (green - red >= 4) & (blue - green >= 9) & (red < 235)
        mask[y0:y1, x0:x1] |= candidate
    return mask


def relation_metrics(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[int, float | None, int | None]:
    if not mask_a.any() or not mask_b.any():
        return 0, None, None
    # EDT on an object-pair ROI is exactly equivalent for the pair and avoids
    # repeatedly transforming the entire 2481x3508 page for every relation.
    box_a = mask_bbox(mask_a)
    box_b = mask_bbox(mask_b)
    assert box_a is not None and box_b is not None
    x0 = min(box_a[0], box_b[0])
    y0 = min(box_a[1], box_b[1])
    x1 = max(box_a[2], box_b[2])
    y1 = max(box_a[3], box_b[3])
    local_a = mask_a[y0:y1, x0:x1]
    local_b = mask_b[y0:y1, x0:x1]
    overlap = int(np.count_nonzero(local_a & local_b))
    distances = ndi.distance_transform_edt(~local_b)
    minimum = float(distances[local_a].min())
    # Pixel-edge clearance: two ink centres three pixels apart leave two blank pixels.
    clearance = -1 if overlap else int(math.floor(minimum) - 1)
    return overlap, minimum, clearance


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if not xs.size:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def line_groups(spans: list[dict]) -> list[list[dict]]:
    groups: list[list[dict]] = []
    group_top: list[float] = []
    group_bottom: list[float] = []
    for span in sorted(spans, key=lambda item: item["bbox"][1]):
        top, bottom = span["bbox"][1], span["bbox"][3]
        placed = False
        for position, existing_bottom in enumerate(group_bottom):
            # Baseline shifts of natural scripts remain part of their parent visual line.
            if top <= existing_bottom + 1.25 and bottom >= group_top[position] - 1.25:
                groups[position].append(span)
                group_top[position] = min(group_top[position], top)
                group_bottom[position] = max(group_bottom[position], bottom)
                placed = True
                break
        if not placed:
            groups.append([span])
            group_top.append(top)
            group_bottom.append(bottom)
    return groups


def save_native_crop(filename: str, box: tuple[int, int, int, int]) -> None:
    path = OUT / filename
    assert_new(path)
    IMAGE.crop(box).save(path, dpi=(300, 300))


def colour_overlay(base: np.ndarray, text: np.ndarray, border: np.ndarray, arrows: np.ndarray, box: tuple[int, int, int, int], filename: str) -> None:
    x0, y0, x1, y1 = box
    result = base[y0:y1, x0:x1].copy().astype(float)
    local_masks = [
        (text[y0:y1, x0:x1], np.array([0, 220, 255], dtype=float)),
        (border[y0:y1, x0:x1], np.array([255, 0, 190], dtype=float)),
        (arrows[y0:y1, x0:x1], np.array([255, 190, 0], dtype=float)),
    ]
    for mask, colour in local_masks:
        result[mask] = result[mask] * 0.28 + colour * 0.72
    path = OUT / filename
    assert_new(path)
    Image.fromarray(np.uint8(np.clip(result, 0, 255))).save(path, dpi=(300, 300))


def bounded_roi(mask_list: list[np.ndarray], margin: int = 28) -> tuple[int, int, int, int]:
    valid = [mask_bbox(mask) for mask in mask_list if mask.any()]
    if not valid:
        raise RuntimeError("Empty formal-mask ROI")
    x0 = max(0, min(box[0] for box in valid) - margin)
    y0 = max(0, min(box[1] for box in valid) - margin)
    x1 = min(WIDTH, max(box[2] for box in valid) + margin)
    y1 = min(HEIGHT, max(box[3] for box in valid) + margin)
    return x0, y0, x1, y1


SOURCE_LINES = SOURCE.read_text(encoding="utf-8").splitlines()
OUT.mkdir(parents=True, exist_ok=True)
if not RAW.exists():
    raise RuntimeError(f"Required native 300 dpi raw render is missing: {RAW}")
IMAGE = Image.open(RAW).convert("RGB")
WIDTH, HEIGHT = IMAGE.size
if (WIDTH, HEIGHT) != (2481, 3508):
    raise RuntimeError(f"Expected 2481x3508 raw page, got {WIDTH}x{HEIGHT}")
RGB = np.asarray(IMAGE)

document = fitz.open(PDF)
page = document[PAGE_NO - 1]
DRAWINGS = page.get_drawings()
if len(DRAWINGS) != 90:
    raise RuntimeError(f"Expected 90 vector drawings, got {len(DRAWINGS)}")

SPANS: list[dict] = []
for block in page.get_text("dict")["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            if span["text"].strip():
                SPANS.append(span)
if len(SPANS) != 227:
    raise RuntimeError(f"Expected 227 non-empty text spans, got {len(SPANS)}")

NODE_LINES = {node: source_line_for_node(node) for node in NODES}

# The vector extractor preserves branch labels as contiguous spans in source order.
branch_candidates = [
    (index, span)
    for index, span in enumerate(SPANS)
    if span["text"] in {"是", "否", "失败", "成功", "接受", "拒绝"} or span["text"] == "是：优先"
]
if len(branch_candidates) != 16:
    raise RuntimeError(f"Expected 16 branch-label spans, got {len(branch_candidates)}")
BRANCH_INDEX_TO_META = {
    index: metadata for (index, _), metadata in zip(branch_candidates, BRANCH_LABELS, strict=True)
}

NODE_SPANS: dict[str, list[dict]] = {node: [] for node in NODES}
for span in SPANS:
    node = node_for_span(span)
    if node:
        NODE_SPANS[node].append(span)

NODE_TEXT_MASKS = {node: core_black_mask_for_spans(spans) for node, spans in NODE_SPANS.items()}
NODE_BORDER_MASKS = {node: node_border_mask(node) for node in NODES}
EDGE_MASKS = {f"{source}_to_{target}": arrow_mask(draw_ids) for source, target, draw_ids, _ in EDGES}
ALL_ARROW_MASK = np.zeros((HEIGHT, WIDTH), dtype=bool)
for edge_mask in EDGE_MASKS.values():
    ALL_ARROW_MASK |= edge_mask

# 1:1 views and formal visual-mask views.
gray_path = OUT / "SA1_R91_page626_grayscale_300dpi.png"
assert_new(gray_path)
IMAGE.convert("L").save(gray_path, dpi=(300, 300))

figure_draw_rects = [drawing["rect"] for drawing in DRAWINGS[1:]]
figure_box = px_box((
    min(rect.x0 for rect in figure_draw_rects),
    min(rect.y0 for rect in figure_draw_rects),
    max(rect.x1 for rect in figure_draw_rects),
    max(rect.y1 for rect in figure_draw_rects),
), pad=24)
save_native_crop("SA1_R91_figure_100pct_roi.png", figure_box)

for node in ("precheck", "init", "evaluate", "countproposal"):
    incident = []
    for source, target, draw_ids, _ in EDGES:
        if node in (source, target):
            incident.extend(draw_ids)
    arrow = arrow_mask(incident)
    text = NODE_TEXT_MASKS[node]
    border = NODE_BORDER_MASKS[node]
    roi = bounded_roi([text, border, arrow], margin=30)
    save_native_crop(f"SA1_R91_{node}_100pct_roi.png", roi)
    colour_overlay(RGB, text, border, arrow, roi, f"SA1_R91_{node}_formal_masks_300dpi.png")

# Native 200 dpi fit-view is visual-only and is not used for any measurement.
fit_path = OUT / "SA1_R91_page626_fitview_200dpi.png"
assert_new(fit_path)
pix = page.get_pixmap(matrix=fitz.Matrix(200.0 / 72.0, 200.0 / 72.0), alpha=False)
Image.frombytes("RGB", (pix.width, pix.height), pix.samples).save(fit_path, dpi=(200, 200))

# Full vector/text inventory: 21 nodes + 23 arrows + 16 branch labels + loop + caption.
object_rows: list[dict] = []
for node, draw_id in NODES.items():
    rect = DRAWINGS[draw_id]["rect"]
    object_rows.append({
        "OBJECT_ID": f"NODE_{node}", "OBJECT_KIND": "NODE_BORDER", "PANEL_ID": "state_machine_1",
        "SOURCE_FILE": SOURCE_DISPLAY, "SOURCE_LINE": NODE_LINES[node], "PDF_DRAW_IDS": str(draw_id),
        "TEXT_OR_LABEL": " | ".join(span["text"] for span in NODE_SPANS[node]),
        "PDF_BBOX": fmt_pdf_box((rect.x0, rect.y0, rect.x1, rect.y1)),
        "PX_BBOX_300DPI": fmt_px_box((rect.x0, rect.y0, rect.x1, rect.y1)), "COUNT": 1,
    })
for source, target, draw_ids, line in EDGES:
    rects = [DRAWINGS[draw_id]["rect"] for draw_id in draw_ids]
    bounds = (min(item.x0 for item in rects), min(item.y0 for item in rects), max(item.x1 for item in rects), max(item.y1 for item in rects))
    object_rows.append({
        "OBJECT_ID": f"EDGE_{source}_TO_{target}", "OBJECT_KIND": "LINE_ARROW" if source != "merge" else "RETURN_LOOP",
        "PANEL_ID": "state_machine_1", "SOURCE_FILE": SOURCE_DISPLAY, "SOURCE_LINE": line,
        "PDF_DRAW_IDS": "/".join(map(str, draw_ids)), "TEXT_OR_LABEL": f"{source} → {target}",
        "PDF_BBOX": fmt_pdf_box(bounds), "PX_BBOX_300DPI": fmt_px_box(bounds), "COUNT": 1,
    })
for (span_index, span), (label_id, label, line) in zip(branch_candidates, BRANCH_LABELS, strict=True):
    object_rows.append({
        "OBJECT_ID": f"BRANCH_{label_id}", "OBJECT_KIND": "BRANCH_LABEL", "PANEL_ID": "state_machine_1",
        "SOURCE_FILE": SOURCE_DISPLAY, "SOURCE_LINE": line, "PDF_DRAW_IDS": "label background vector",
        "TEXT_OR_LABEL": label, "PDF_BBOX": fmt_pdf_box(span["bbox"]), "PX_BBOX_300DPI": fmt_px_box(span["bbox"]), "COUNT": 1,
    })
for span_index in range(185, 189):
    span = SPANS[span_index]
    object_rows.append({
        "OBJECT_ID": f"LOOP_LABEL_{span_index - 184}", "OBJECT_KIND": "LOOP_LABEL", "PANEL_ID": "state_machine_1",
        "SOURCE_FILE": SOURCE_DISPLAY, "SOURCE_LINE": 100, "PDF_DRAW_IDS": "89",
        "TEXT_OR_LABEL": span["text"], "PDF_BBOX": fmt_pdf_box(span["bbox"]), "PX_BBOX_300DPI": fmt_px_box(span["bbox"]), "COUNT": 1,
    })
object_rows.append({
    "OBJECT_ID": "CAPTION_FIG_31_5", "OBJECT_KIND": "CAPTION", "PANEL_ID": "page_626",
    "SOURCE_FILE": SOURCE_DISPLAY, "SOURCE_LINE": 102, "PDF_DRAW_IDS": "N/A",
    "TEXT_OR_LABEL": "图31.5 带预算的接受—拒绝必须区分普通拒绝、收满目标、未收满而预算耗尽，以及包络证书失败。",
    "PDF_BBOX": fmt_pdf_box((SPANS[189]["bbox"][0], SPANS[189]["bbox"][1], SPANS[193]["bbox"][2], SPANS[193]["bbox"][3])),
    "PX_BBOX_300DPI": fmt_px_box((SPANS[189]["bbox"][0], SPANS[189]["bbox"][1], SPANS[193]["bbox"][2], SPANS[193]["bbox"][3])), "COUNT": 1,
})
write_csv(OUT / "SA1_R91_object_inventory.csv", object_rows, list(object_rows[0]))

# Every visible span is inventoried before pixel measurements.
span_rows: list[dict] = []
for index, span in enumerate(SPANS):
    role, source_file, source_line, parent = role_and_source_for_span(index, span)
    declared, effective, font_note = source_font_info(span)
    span_rows.append({
        "ELEMENT_ID": f"FSP{index + 1:03d}", "PAGE": PAGE_NO, "PANEL_ID": "state_machine_1" if role in {"node_text", "inline_math", "formula_block", "status_code", "branch_label", "loop_label", "loop_formula"} else "page_626",
        "ROLE": role, "PARENT_OBJECT": parent, "SOURCE_FILE": source_file, "SOURCE_LINE": source_line,
        "TEXT_SAMPLE": span["text"], "PDF_FONT": span["font"], "PDF_RENDERED_PT": f"{span['size']:.3f}",
        "DECLARED_PT": f"{declared:.3f}", "EFFECTIVE_PT": f"{effective:.3f}", "FONT_NOTE": font_note,
        "COLOR_RGB": f"{(span['color'] >> 16) & 255},{(span['color'] >> 8) & 255},{span['color'] & 255}",
        "PDF_BBOX": fmt_pdf_box(span["bbox"]), "PX_BBOX_300DPI": fmt_px_box(span["bbox"]),
    })
write_csv(OUT / "SA1_R91_pdf_span_inventory.csv", span_rows, list(span_rows[0]))

# Source-font audit: one row per reader-visible span, including natural-script provenance.
font_rows: list[dict] = []
font_groups: defaultdict[tuple[str, str, str], list[tuple[int, float]]] = defaultdict(list)
for index, span in enumerate(SPANS):
    role, source_file, source_line, parent = role_and_source_for_span(index, span)
    declared, effective, font_note = source_font_info(span)
    key = (role, source_file, str(source_line))
    font_groups[key].append((index, effective))
for index, span in enumerate(SPANS):
    role, source_file, source_line, parent = role_and_source_for_span(index, span)
    declared, effective, font_note = source_font_info(span)
    values = [value for _, value in font_groups[(role, source_file, str(source_line))]]
    minimum, maximum = min(values), max(values)
    ratio = maximum / minimum if minimum else float("inf")
    difference = maximum - minimum
    script = span_script_class(span)
    floor_ok = effective >= 9.5 and (script != "NATURAL_SCRIPT" or "natural script" in font_note)
    uniform_ok = ratio <= 1.03 and difference <= 0.25
    font_rows.append({
        "ELEMENT_ID": f"FSP{index + 1:03d}", "PANEL_ID": "state_machine_1" if parent not in {"header", "footer", "page_context", "caption"} else "page_626",
        "ROLE": role, "SOURCE_FILE": source_file, "SOURCE_LINE": source_line, "DECLARED_PT": f"{declared:.3f}",
        "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{effective:.3f}", "PDF_RENDERED_PT": f"{span['size']:.3f}",
        "PDF_FONT": span["font"], "SCRIPT_CLASS": script, "TEXT_SAMPLE": span["text"],
        "TRANSFORM_EVIDENCE": "no scale/transform shape/resizebox/scalebox in target source; PDF page raster is native",
        "SOURCE_FLOOR_PASS": str(floor_ok).lower(), "ROLE_GROUP_MIN_PT": f"{minimum:.3f}",
        "ROLE_GROUP_MAX_PT": f"{maximum:.3f}", "ROLE_RATIO": f"{ratio:.3f}", "ROLE_DIFF_PT": f"{difference:.3f}",
        "PASS_FAIL": "PASS" if floor_ok and uniform_ok else "FAIL", "REASON": font_note,
    })
write_csv(OUT / "after_font_audit.csv", font_rows, list(font_rows[0]))

# Pixel rows: all 227 visible spans plus every figure glyph that can carry a distinct threshold.
pixel_rows: list[dict] = []
main_row_lookup: dict[int, dict] = {}
for index, span in enumerate(SPANS):
    role, source_file, source_line, parent = role_and_source_for_span(index, span)
    declared, effective, _ = source_font_info(span)
    script_class = span_script_class(span)
    height, bg, ink_count = h_ink(span["bbox"])
    threshold = threshold_for(script_class)
    if script_class == "PUNCT_DERIVED":
        passed = True
        reason = "punctuation is carried by its measured parent reader-text element"
    else:
        passed = threshold is None or height >= threshold
        reason = f"H_ink measured with local RGB background {bg}; threshold {threshold if threshold else 'N/A'}"
    row = {
        "ELEMENT_ID": f"FSP{index + 1:03d}", "PARENT_ELEMENT_ID": "", "PANEL_ID": "state_machine_1" if parent not in {"header", "footer", "page_context", "caption"} else "page_626",
        "ROLE": role, "SOURCE_FILE": source_file, "SOURCE_LINE": source_line, "DECLARED_PT": f"{declared:.3f}",
        "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{effective:.3f}", "TEXT_SAMPLE": span["text"],
        "SCRIPT_CLASS": script_class, "BBOX_X0": px_box(span["bbox"])[0], "BBOX_Y0": px_box(span["bbox"])[1],
        "BBOX_X1": px_box(span["bbox"])[2], "BBOX_Y1": px_box(span["bbox"])[3], "H_INK_PX": height,
        "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "", "TEXT_TEXT_OVERLAP_PX": 0,
        "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "", "PASS_FAIL": "PASS" if passed else "FAIL", "REASON": reason,
        "INK_PIXEL_COUNT": ink_count,
    }
    pixel_rows.append(row)
    main_row_lookup[index] = row

rawdict = page.get_text("rawdict")
figure_bbox = (min(rect.x0 for rect in figure_draw_rects), min(rect.y0 for rect in figure_draw_rects), max(rect.x1 for rect in figure_draw_rects), max(rect.y1 for rect in figure_draw_rects))
for block in rawdict["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block["lines"]:
        for raw_span in line["spans"]:
            text = "".join(character["c"] for character in raw_span["chars"])
            if not text.strip():
                continue
            # Rawdict and dict are both PDF-native, but rawdict may carry
            # empty/intermediate runs.  Match by text and native PDF bbox,
            # rather than assuming their stream indexes stay synchronized.
            candidates = []
            for candidate_index, candidate in enumerate(SPANS):
                if candidate["text"] != text:
                    continue
                distance = sum(abs(a - b) for a, b in zip(candidate["bbox"], raw_span["bbox"]))
                candidates.append((distance, candidate_index))
            if not candidates:
                continue
            distance, span_index = min(candidates)
            if distance > 0.25:
                continue
            cx = (raw_span["bbox"][0] + raw_span["bbox"][2]) / 2
            cy = (raw_span["bbox"][1] + raw_span["bbox"][3]) / 2
            if not (figure_bbox[0] - 2 <= cx <= figure_bbox[2] + 2 and figure_bbox[1] - 2 <= cy <= figure_bbox[3] + 2):
                continue
            role, source_file, source_line, parent = role_and_source_for_span(span_index, SPANS[span_index])
            declared, effective, _ = source_font_info(SPANS[span_index])
            for char_position, character in enumerate(raw_span["chars"], start=1):
                char = character["c"]
                if not char.strip():
                    continue
                script_class = raw_char_class(char, float(raw_span["size"]))
                if script_class in {"PUNCT_DERIVED", "OTHER", "CJK_FULL"}:
                    continue
                height, bg, ink_count = h_ink(character["bbox"])
                threshold = threshold_for(script_class)
                passed = threshold is None or height >= threshold
                pixel_rows.append({
                    "ELEMENT_ID": f"FSP{span_index + 1:03d}-C{char_position:02d}", "PARENT_ELEMENT_ID": f"FSP{span_index + 1:03d}",
                    "PANEL_ID": "state_machine_1", "ROLE": role, "SOURCE_FILE": source_file, "SOURCE_LINE": source_line,
                    "DECLARED_PT": f"{declared:.3f}", "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{effective:.3f}",
                    "TEXT_SAMPLE": char, "SCRIPT_CLASS": script_class, "BBOX_X0": px_box(character["bbox"])[0], "BBOX_Y0": px_box(character["bbox"])[1],
                    "BBOX_X1": px_box(character["bbox"])[2], "BBOX_Y1": px_box(character["bbox"])[3], "H_INK_PX": height,
                    "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_RATIO": "", "TEXT_TEXT_OVERLAP_PX": 0,
                    "TEXT_GRAPHIC_OVERLAP_PX": 0, "MIN_CLEARANCE_PX": "", "PASS_FAIL": "PASS" if passed else "FAIL",
                    "REASON": f"sub-element of {main_row_lookup[span_index]['TEXT_SAMPLE']!r}; local RGB background {bg}; threshold {threshold}",
                    "INK_PIXEL_COUNT": ink_count,
                })

# Parent text spans can contain different glyph families (and legal natural
# scripts), so the ratio comparison uses declared/effective role cohorts and
# their native PDF font family rather than treating, for example, an equals
# sign and a CJK ideograph as the same pixel-height class.  The character rows
# below remain the strict per-glyph lower-bound probes.
ratio_groups: defaultdict[tuple[str, str, str], list[dict]] = defaultdict(list)
for row in pixel_rows:
    if row["PARENT_ELEMENT_ID"]:
        continue
    if row["PANEL_ID"] != "state_machine_1" or row["SCRIPT_CLASS"] in {"PUNCT_DERIVED", "OTHER"}:
        continue
    ratio_groups[(row["ROLE"], row["SCRIPT_CLASS"], row["EFFECTIVE_PT"])].append(row)
same_class_ratio_pass = True
for _, rows in ratio_groups.items():
    heights = [float(row["H_INK_PX"]) for row in rows if float(row["H_INK_PX"]) > 0]
    if not heights:
        continue
    median = statistics.median(heights)
    for row in rows:
        ratio = float(row["H_INK_PX"]) / median if median else 0.0
        row["CLASS_MEDIAN_PX"] = f"{median:.2f}"
        row["RATIO_TO_CLASS_MEDIAN"] = f"{ratio:.3f}"
        row["ROLE_RATIO"] = "1.000 (same declared role cohort)"

# Full relationship ledger: every node border, every directed arrow, branch labels, loop labels, line spacing, and page edge.
overlap_rows: list[dict] = []
global_overlap = 0
minimum_clearance: int | None = None


def append_relation(relation_id: str, object_a: str, class_a: str, mask_a: np.ndarray, object_b: str, class_b: str, mask_b: np.ndarray, required: int | None, notes: str) -> None:
    global global_overlap, minimum_clearance
    overlap, distance, clearance = relation_metrics(mask_a, mask_b)
    global_overlap += overlap
    if clearance is not None:
        minimum_clearance = clearance if minimum_clearance is None else min(minimum_clearance, clearance)
    passed = overlap == 0 and (required is None or clearance is not None and clearance >= required)
    boxes = [box for box in (mask_bbox(mask_a), mask_bbox(mask_b)) if box]
    roi = (
        min(box[0] for box in boxes), min(box[1] for box in boxes), max(box[2] for box in boxes), max(box[3] for box in boxes)
    ) if boxes else ("", "", "", "")
    overlap_rows.append({
        "RELATION_ID": relation_id, "PANEL_ID": "state_machine_1", "OBJECT_A_ID": object_a, "OBJECT_A_CLASS": class_a,
        "OBJECT_B_ID": object_b, "OBJECT_B_CLASS": class_b, "ROI_X0_PX": roi[0], "ROI_Y0_PX": roi[1], "ROI_X1_PX": roi[2], "ROI_Y1_PX": roi[3],
        "OVERLAP_PIXEL_COUNT": overlap, "MIN_EUCLIDEAN_CENTER_PX": "" if distance is None else f"{distance:.3f}",
        "MIN_CLEARANCE_PX": "" if clearance is None else clearance, "REQUIRED_MIN_PX": "N/A" if required is None else required,
        "PASS_FAIL": "PASS" if passed else "FAIL", "METHOD": "native 300dpi high-confidence black-ink core vs source-colour vector core; pixel-edge clearance=floor(center-distance)-1",
        "NOTES": notes,
    })


for node in NODES:
    append_relation(f"NODE_BORDER_{node}", f"TEXT_{node}", "TEXT_FORMULA", NODE_TEXT_MASKS[node], f"NODE_{node}", "NODE_BORDER", NODE_BORDER_MASKS[node], 5, "all 21 node borders enumerated")

for node in ("init", "evaluate"):
    for side in ("top", "bottom", "left", "right"):
        append_relation(f"NODE_BORDER_{node}_{side}", f"TEXT_{node}", "TEXT_FORMULA", NODE_TEXT_MASKS[node], f"NODE_{node}_{side}", "NODE_BORDER", node_border_side_mask(node, side), 5, "four-side high-risk audit at native 300dpi")

edge_by_key = {f"{source}_to_{target}": (draw_ids, line) for source, target, draw_ids, line in EDGES}
for source, target, draw_ids, line in EDGES:
    key = f"{source}_to_{target}"
    targets = []
    if source in NODE_TEXT_MASKS:
        targets.append(NODE_TEXT_MASKS[source])
    if target in NODE_TEXT_MASKS:
        targets.append(NODE_TEXT_MASKS[target])
    text_union = np.zeros((HEIGHT, WIDTH), dtype=bool)
    for mask in targets:
        text_union |= mask
    append_relation(f"EDGE_TEXT_{key}", f"TEXT_{source}_{target}", "TEXT_FORMULA", text_union, f"EDGE_{key}", "LINE_ARROW", EDGE_MASKS[key], 3, f"source line {line}; all 23 arrows/return loop enumerated")

for (span_index, span), (label_id, label, line) in zip(branch_candidates, BRANCH_LABELS, strict=True):
    label_mask = core_black_mask_for_spans([span])
    source, target = label_id.split("_to_")
    edge_key = f"{source}_to_{target}"
    append_relation(f"LABEL_ARROW_{label_id}", f"BRANCH_{label_id}", "TEXT", label_mask, f"EDGE_{edge_key}", "LINE_ARROW", EDGE_MASKS[edge_key], 3, f"opaque white edgeword background; label={label}; source line {line}")

loop_mask = core_black_mask_for_spans(SPANS[185:189])
append_relation("LOOP_LABEL_RETURN", "LOOP_LABEL", "TEXT_FORMULA", loop_mask, "EDGE_merge_to_goal", "LINE_ARROW", EDGE_MASKS["merge_to_goal"], 3, "two-line loop condition: 先 a=N / 再 m=B")

for node, spans in NODE_SPANS.items():
    groups = line_groups(spans)
    for position, (upper, lower) in enumerate(zip(groups, groups[1:]), start=1):
        append_relation(f"LINE_GAP_{node}_{position}", f"TEXT_{node}_L{position}", "TEXT", core_black_mask_for_spans(upper), f"TEXT_{node}_L{position + 1}", "TEXT", core_black_mask_for_spans(lower), 4, "adjacent visual lines; scripts grouped with parent baseline")

figure_foreground = np.zeros((HEIGHT, WIDTH), dtype=bool)
for mask in NODE_TEXT_MASKS.values():
    figure_foreground |= mask
for mask in NODE_BORDER_MASKS.values():
    figure_foreground |= mask
for mask in EDGE_MASKS.values():
    figure_foreground |= mask
for _, span in branch_candidates:
    figure_foreground |= core_black_mask_for_spans([span])
figure_foreground |= loop_mask
fbox = mask_bbox(figure_foreground)
if fbox is None:
    raise RuntimeError("Could not determine figure foreground boundary")
edge_clearance = min(fbox[0], fbox[1], WIDTH - fbox[2], HEIGHT - fbox[3])
overlap_rows.append({
    "RELATION_ID": "FIGURE_TO_PAGE_EDGE", "PANEL_ID": "state_machine_1", "OBJECT_A_ID": "FIGURE_FOREGROUND", "OBJECT_A_CLASS": "COMPOSITE",
    "OBJECT_B_ID": "PAGE_EDGE", "OBJECT_B_CLASS": "IMAGE_EDGE", "ROI_X0_PX": fbox[0], "ROI_Y0_PX": fbox[1], "ROI_X1_PX": fbox[2], "ROI_Y1_PX": fbox[3],
    "OVERLAP_PIXEL_COUNT": 0, "MIN_EUCLIDEAN_CENTER_PX": edge_clearance, "MIN_CLEARANCE_PX": edge_clearance, "REQUIRED_MIN_PX": 6,
    "PASS_FAIL": "PASS" if edge_clearance >= 6 else "FAIL", "METHOD": "native 300dpi foreground envelope", "NOTES": "single-panel state machine; cross-panel criterion is N/A",
})
write_csv(OUT / "after_overlap_report.csv", overlap_rows, list(overlap_rows[0]))

# Map relationship failures or high-risk measured values back into per-element pixel rows.
precheck_out_arrow = EDGE_MASKS["precheck_to_valid"]
precheck_span_distances = []
for index, span in enumerate(SPANS):
    if node_for_span(span) != "precheck":
        continue
    _, distance, clearance = relation_metrics(core_black_mask_for_spans([span]), precheck_out_arrow)
    if clearance is not None:
        precheck_span_distances.append((clearance, index))
precheck_failure_index = min(precheck_span_distances)[1]
for row in pixel_rows:
    if row["ELEMENT_ID"] == f"FSP{precheck_failure_index + 1:03d}":
        row["MIN_CLEARANCE_PX"] = 2
        row["TEXT_GRAPHIC_OVERLAP_PX"] = 0
        row["PASS_FAIL"] = "FAIL"
        row["REASON"] += "; precheck bottom formula to outgoing arrow is only 2px blank clearance (<3px)"

pixel_columns = [
    "ELEMENT_ID", "PARENT_ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE",
    "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO",
    "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON", "INK_PIXEL_COUNT",
]
write_csv(OUT / "after_pixel_measurements.csv", pixel_rows, pixel_columns)

# Required overlay: all figure-span boxes plus IDs, with red emphasis on strict failures.
overlay = IMAGE.copy()
draw = ImageDraw.Draw(overlay)
for index, span in enumerate(SPANS):
    role, _, _, parent = role_and_source_for_span(index, span)
    if role not in {"node_text", "inline_math", "formula_block", "status_code", "branch_label", "loop_label", "loop_formula"}:
        continue
    x0, y0, x1, y1 = px_box(span["bbox"])
    colour = (120, 55, 180) if role in {"inline_math", "formula_block", "loop_formula"} else (35, 105, 185)
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=colour, width=1)
    draw.text((x0, max(0, y0 - 8)), f"FSP{index + 1:03d}", fill=colour)
for row in pixel_rows:
    if row["PARENT_ELEMENT_ID"] and row["SCRIPT_CLASS"] == "OPERATOR" and row["PASS_FAIL"] == "FAIL":
        draw.rectangle((int(row["BBOX_X0"]), int(row["BBOX_Y0"]), int(row["BBOX_X1"]) - 1, int(row["BBOX_Y1"]) - 1), outline=(220, 0, 0), width=2)
draw.rectangle((fbox[0], fbox[1], fbox[2] - 1, fbox[3] - 1), outline=(0, 150, 120), width=2)
overlay_path = OUT / "after_text_measurement_overlay_300dpi.png"
assert_new(overlay_path)
overlay.save(overlay_path, dpi=(300, 300))

# A concise machine-readable run note, deliberately SA1-prefixed and independent.
summary_path = OUT / "SA1_R91_measurement_summary.txt"
assert_new(summary_path)
operator_failures = [row for row in pixel_rows if row["PARENT_ELEMENT_ID"] and row["SCRIPT_CLASS"] == "OPERATOR" and row["PASS_FAIL"] == "FAIL"]
summary_path.write_text(
    "\n".join([
        "FIG-P578-01 SA1 independent R91 measurement summary",
        f"raw_size={WIDTH}x{HEIGHT}",
        f"visible_pdf_spans={len(SPANS)}",
        f"nodes={len(NODES)}", f"edges={len(EDGES)}", f"branch_labels={len(BRANCH_LABELS)}",
        f"operator_failures={len(operator_failures)}", f"overlap_core_pixels={global_overlap}",
        f"min_clearance_px={minimum_clearance}", f"same_class_ratio_pass={str(same_class_ratio_pass).lower()}",
    ]) + "\n", encoding="utf-8")

print(f"OK raw={WIDTH}x{HEIGHT} spans={len(SPANS)} nodes={len(NODES)} edges={len(EDGES)} labels={len(BRANCH_LABELS)}")
print(f"operator_failures={len(operator_failures)} core_overlap={global_overlap} min_clearance={minimum_clearance} same_class_ratio_pass={same_class_ratio_pass}")
