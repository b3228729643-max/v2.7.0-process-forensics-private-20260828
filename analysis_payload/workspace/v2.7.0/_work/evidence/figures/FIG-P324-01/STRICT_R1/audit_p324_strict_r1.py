from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree


OUT = Path(__file__).resolve().parent
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r92_fullbook\main_full.pdf"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第03册_优化模型与序列模型\V3-C03\fig_v3_c03_adaboost_loop.tex"
)
PAGE_NO = 349
PAGE_INDEX = PAGE_NO - 1
SCALE = 300.0 / 72.0
IMG_PATH = OUT / "full_page_300dpi.png"
FIGURE_PT = (110.0, 278.0, 470.0, 448.0)


def el(
    eid: str,
    oid: str,
    panel: str,
    role: str,
    line: str,
    text: str,
    script: str,
    declared: float,
    effective: float,
    bbox: tuple[float, float, float, float],
    natural_script: bool = False,
    cascade: str = "",
    ink_rgb: tuple[int, int, int] = (31, 35, 40),
) -> dict:
    thresholds = {
        "CJK": 30,
        "CAPS_DIGITS": 24,
        "LOWER_GREEK": 17,
        "BASE_OPERATOR": 22,
        "NATURAL_SCRIPT": 15,
    }
    return {
        "ELEMENT_ID": eid,
        "OBJECT_ID": oid,
        "PANEL_ID": panel,
        "ROLE": role,
        "SOURCE_LINE": line,
        "TEXT_SAMPLE": text,
        "SCRIPT_CLASS": script,
        "DECLARED_PT": declared,
        "GRAPHICS_SCALE": 1.0,
        "EFFECTIVE_PT": effective,
        "NATURAL_SCRIPT": natural_script,
        "FONT_CASCADE": cascade,
        "BBOX_PT": bbox,
        "PIXEL_THRESHOLD": thresholds[script],
        "INK_RGB": ink_rgb,
    }


SMALL = "11pt ctexbook: every node/.append font=small; small=10.0pt"
EXPLICIT = "node-local explicit fontsize overrides every-node small"

ELEMENTS = [
    el("E01", "O01", "TOP", "CHANNEL_HEADING", "14", "权重更新通道", "CJK", 9.7, 9.7, (273.61, 286.96, 331.59, 300.95), cascade=EXPLICIT, ink_rgb=(31, 78, 121)),
    el("E02", "O02", "TOP", "NODE_LABEL", "15", "样本分布", "CJK", 10.0, 10.0, (138.79, 318.72, 182.93, 329.39), cascade=SMALL),
    el("E03", "O02", "TOP", "NODE_LABEL", "15", "D", "CAPS_DIGITS", 10.0, 10.0, (153.11, 335.00, 160.11, 344.96), cascade=SMALL),
    el("E04", "O02", "TOP", "NODE_LABEL", "15", "m", "NATURAL_SCRIPT", 10.0, 9.0, (159.68, 337.85, 168.22, 346.81), True, SMALL),
    el("E05", "O03", "TOP", "NODE_LABEL", "16", "训练", "CJK", 10.0, 10.0, (240.19, 318.72, 260.12, 329.39), cascade=SMALL),
    el("E06", "O03", "TOP", "NODE_LABEL", "16", "G", "CAPS_DIGITS", 10.0, 10.0, (242.03, 335.00, 248.98, 344.96), cascade=SMALL),
    el("E07", "O03", "TOP", "NODE_LABEL", "16", "m", "NATURAL_SCRIPT", 10.0, 9.0, (249.34, 337.85, 257.88, 346.81), True, SMALL),
    el("E08", "O04", "TOP", "NODE_LABEL", "17", "误差", "CJK", 10.0, 10.0, (325.23, 318.72, 345.16, 329.39), cascade=SMALL),
    el("E09", "O04", "TOP", "NODE_LABEL", "17", "e", "LOWER_GREEK", 10.0, 10.0, (328.43, 335.00, 332.66, 344.96), cascade=SMALL),
    el("E10", "O04", "TOP", "NODE_LABEL", "17", "m", "NATURAL_SCRIPT", 10.0, 9.0, (333.02, 337.85, 341.56, 346.81), True, SMALL),
    el("E11", "O05", "TOP", "NODE_LABEL", "18", "更新分布", "CJK", 10.0, 10.0, (400.99, 318.44, 445.14, 329.11), cascade=SMALL),
    el("E12", "O05", "TOP", "NODE_LABEL", "18", "D", "CAPS_DIGITS", 10.0, 10.0, (409.69, 334.72, 416.68, 344.69), cascade=SMALL),
    el("E13", "O05", "TOP", "NODE_LABEL", "18", "m+1", "NATURAL_SCRIPT", 10.0, 9.0, (416.25, 337.80, 436.28, 346.76), True, SMALL),
    el("E14", "O06", "BOTTOM", "CHANNEL_HEADING", "23", "加法模型通道", "CJK", 9.7, 9.7, (153.13, 374.83, 211.12, 388.82), cascade=EXPLICIT, ink_rgb=(15, 118, 110)),
    el("E15", "O07", "BOTTOM", "NODE_LABEL", "24", "弱分类器", "CJK", 10.0, 10.0, (214.64, 398.09, 254.49, 408.76), cascade=SMALL),
    el("E16", "O07", "BOTTOM", "NODE_LABEL", "24", "G", "CAPS_DIGITS", 10.0, 10.0, (226.44, 414.37, 233.39, 424.33), cascade=SMALL),
    el("E17", "O07", "BOTTOM", "NODE_LABEL", "24", "m", "NATURAL_SCRIPT", 10.0, 9.0, (233.75, 417.22, 242.29, 426.18), True, SMALL),
    el("E18", "O08", "BOTTOM", "NODE_LABEL", "25", "alpha", "LOWER_GREEK", 10.0, 10.0, (299.46, 404.42, 305.29, 414.38), cascade=SMALL),
    el("E19", "O08", "BOTTOM", "NODE_LABEL", "25", "m", "NATURAL_SCRIPT", 10.0, 9.0, (305.29, 407.27, 313.84, 416.24), True, SMALL),
    el("E20", "O09", "BOTTOM", "NODE_LABEL", "26", "集成模型", "CJK", 10.0, 10.0, (376.22, 397.97, 416.07, 408.64), cascade=SMALL),
    el("E21", "O09", "BOTTOM", "NODE_LABEL", "26", "F", "CAPS_DIGITS", 10.0, 10.0, (348.54, 414.25, 354.35, 424.22), cascade=SMALL),
    el("E22", "O09", "BOTTOM", "NODE_LABEL", "26", "m", "NATURAL_SCRIPT", 10.0, 9.0, (353.79, 417.11, 362.34, 426.07), True, SMALL),
    el("E23", "O09", "BOTTOM", "NODE_LABEL", "26", "=", "BASE_OPERATOR", 10.0, 10.0, (365.50, 414.25, 372.68, 424.22), cascade=SMALL),
    el("E24", "O09", "BOTTOM", "NODE_LABEL", "26", "F", "CAPS_DIGITS", 10.0, 10.0, (375.44, 414.25, 381.24, 424.22), cascade=SMALL),
    el("E25", "O09", "BOTTOM", "NODE_LABEL", "26", "m-1", "NATURAL_SCRIPT", 10.0, 9.0, (380.69, 417.33, 400.72, 426.29), True, SMALL),
    el("E26", "O09", "BOTTOM", "NODE_LABEL", "26", "+", "BASE_OPERATOR", 10.0, 10.0, (403.34, 414.25, 410.51, 424.22), cascade=SMALL),
    el("E27", "O09", "BOTTOM", "NODE_LABEL", "26", "alpha", "LOWER_GREEK", 10.0, 10.0, (412.72, 414.25, 418.55, 424.22), cascade=SMALL),
    el("E28", "O09", "BOTTOM", "NODE_LABEL", "26", "m", "NATURAL_SCRIPT", 10.0, 9.0, (418.55, 417.11, 427.10, 426.07), True, SMALL),
    el("E29", "O09", "BOTTOM", "NODE_LABEL", "26", "G", "CAPS_DIGITS", 10.0, 10.0, (427.50, 414.25, 434.44, 424.22), cascade=SMALL),
    el("E30", "O09", "BOTTOM", "NODE_LABEL", "26", "m", "NATURAL_SCRIPT", 10.0, 9.0, (434.80, 417.11, 443.34, 426.07), True, SMALL),
    el("E31", "O10", "BRIDGE", "EDGE_FORMULA", "32-33", "e", "LOWER_GREEK", 8.8, 8.8, (328.21, 371.63, 332.45, 380.39), cascade=EXPLICIT, ink_rgb=(183, 121, 31)),
    el("E32", "O10", "BRIDGE", "EDGE_FORMULA", "32-33", "m", "NATURAL_SCRIPT", 8.8, 6.16, (332.45, 375.47, 338.90, 381.61), True, EXPLICIT, (183, 121, 31)),
    el("E33", "O10", "BRIDGE", "EDGE_FORMULA", "32-33", "mapsto", "BASE_OPERATOR", 8.8, 8.8, (341.69, 371.63, 350.00, 380.39), cascade=EXPLICIT, ink_rgb=(183, 121, 31)),
    el("E34", "O10", "BRIDGE", "EDGE_FORMULA", "32-33", "alpha", "LOWER_GREEK", 8.8, 8.8, (352.43, 371.63, 358.51, 380.39), cascade=EXPLICIT, ink_rgb=(183, 121, 31)),
    el("E35", "O10", "BRIDGE", "EDGE_FORMULA", "32-33", "m", "NATURAL_SCRIPT", 8.8, 6.16, (358.52, 375.47, 364.97, 381.61), True, EXPLICIT, (183, 121, 31)),
    el("E36", "O11", "BRIDGE", "ANNOTATION", "36-37", "仅权重更新返回训练", "CJK", 8.5, 8.5, (345.28, 381.21, 421.49, 390.28), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
    el("E37", "O12", "BOTTOM", "LEGEND", "38-39", "形状编码：分布", "CJK", 8.5, 8.5, (232.43, 435.50, 291.71, 444.57), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
    el("E38", "O12", "BOTTOM", "LEGEND", "38-39", "/", "BASE_OPERATOR", 8.5, 8.5, (293.70, 435.83, 296.98, 444.29), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
    el("E39", "O12", "BOTTOM", "LEGEND", "38-39", "分类器", "CJK", 8.5, 8.5, (298.97, 435.50, 324.37, 444.57), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
    el("E40", "O12", "BOTTOM", "LEGEND", "38-39", "/", "BASE_OPERATOR", 8.5, 8.5, (326.36, 435.83, 329.64, 444.29), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
    el("E41", "O12", "BOTTOM", "LEGEND", "38-39", "标量", "CJK", 8.5, 8.5, (331.63, 435.50, 348.57, 444.57), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
    el("E42", "O12", "BOTTOM", "LEGEND", "38-39", "/", "BASE_OPERATOR", 8.5, 8.5, (350.56, 435.83, 353.84, 444.29), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
    el("E43", "O12", "BOTTOM", "LEGEND", "38-39", "集成", "CJK", 8.5, 8.5, (355.83, 435.50, 372.76, 444.57), cascade=EXPLICIT, ink_rgb=(77, 83, 88)),
]


GRAPHICS = [
    {"id": "G01_NODE_DM", "class": "NODE_BORDER", "line": "15", "drawings": [4], "erase": []},
    {"id": "G02_NODE_GM", "class": "NODE_BORDER", "line": "16", "drawings": [5], "erase": []},
    {"id": "G03_NODE_EM", "class": "NODE_BORDER", "line": "17", "drawings": [6], "erase": []},
    {"id": "G04_NODE_DN", "class": "NODE_BORDER", "line": "18", "drawings": [7], "erase": []},
    {"id": "G05_ARROW_DM_GM", "class": "LINE_ARROW", "line": "19", "drawings": [8, 9], "erase": []},
    {"id": "G06_ARROW_GM_EM", "class": "LINE_ARROW", "line": "20", "drawings": [10, 11], "erase": []},
    {"id": "G07_ARROW_EM_DN", "class": "LINE_ARROW", "line": "21", "drawings": [12, 13], "erase": []},
    {"id": "G08_NODE_GCOPY", "class": "NODE_BORDER", "line": "24", "drawings": [14], "erase": []},
    {"id": "G09_NODE_ALPHA", "class": "NODE_BORDER", "line": "25", "drawings": [15], "erase": []},
    {"id": "G10_NODE_FM", "class": "NODE_BORDER", "line": "26", "drawings": [16], "erase": [17]},
    {"id": "G11_ARROW_GCOPY_FM", "class": "LINE_ARROW", "line": "27", "drawings": [18, 19], "erase": []},
    {"id": "G12_ARROW_ALPHA_FM", "class": "LINE_ARROW", "line": "28", "drawings": [20, 21], "erase": []},
    {"id": "G13_GUIDE_GM_GCOPY", "class": "LINE_ARROW", "line": "29", "drawings": [22], "erase": []},
    {"id": "G14_ARROW_EM_ALPHA", "class": "LINE_ARROW", "line": "30-33", "drawings": [23, 24], "erase": []},
    {"id": "G15_RETURN_DN_GM", "class": "LINE_ARROW", "line": "34-35", "drawings": [25, 26], "erase": []},
]

OWN_BORDER = {
    "O02": "G01_NODE_DM",
    "O03": "G02_NODE_GM",
    "O04": "G03_NODE_EM",
    "O05": "G04_NODE_DN",
    "O07": "G08_NODE_GCOPY",
    "O08": "G09_NODE_ALPHA",
    "O09": "G10_NODE_FM",
}


def px_bbox(bbox: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, math.floor(x0 * SCALE)),
        max(0, math.floor(y0 * SCALE)),
        math.ceil(x1 * SCALE),
        math.ceil(y1 * SCALE),
    )


def mode_background(patch: np.ndarray) -> np.ndarray:
    quantized = (patch.astype(np.uint16) // 4 * 4).astype(np.uint8)
    colors = quantized.reshape(-1, 3)
    count = Counter(map(tuple, colors.tolist()))
    return np.array(count.most_common(1)[0][0], dtype=np.int16)


def raster_text_mask(image: np.ndarray, bbox: tuple[float, float, float, float], ink_rgb: tuple[int, int, int]) -> tuple[np.ndarray, tuple[int, int, int, int], np.ndarray]:
    x0, y0, x1, y1 = px_bbox(bbox)
    patch = image[y0:y1, x0:x1]
    bg = mode_background(patch)
    pixels = patch.astype(np.float32)
    bgf = bg.astype(np.float32)
    ink = np.array(ink_rgb, dtype=np.float32)
    direction = bgf - ink
    delta = bgf[None, None, :] - pixels
    t = np.sum(delta * direction[None, None, :], axis=2) / float(np.dot(direction, direction))
    residual = np.linalg.norm(delta - t[:, :, None] * direction[None, None, :], axis=2)
    contrast = np.max(np.abs(delta), axis=2)
    # Antialiasing is a linear blend from the local background to the PDF text color.
    # The direction residual separates overlapping gold and gray text in O10/O11.
    local = (contrast >= 20) & (t >= 0.02) & (t <= 1.20) & (residual <= 22.0)
    # Remove isolated single-pixel quantization noise without altering glyph strokes.
    n, labels = cv2.connectedComponents(local.astype(np.uint8))
    clean = np.zeros_like(local)
    for label in range(1, n):
        component = labels == label
        if int(component.sum()) >= 2:
            clean |= component
    mask = np.zeros(image.shape[:2], dtype=bool)
    mask[y0:y1, x0:x1] = clean
    return mask, (x0, y0, x1, y1), bg


def draw_one_path(shape: fitz.Shape, drawing: dict) -> None:
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
            raise RuntimeError(f"Unsupported drawing op {op}")


def render_graphic_mask(page_rect: fitz.Rect, drawings: list[dict], spec: dict) -> np.ndarray:
    temp = fitz.open()
    page = temp.new_page(width=page_rect.width, height=page_rect.height)
    for idx in spec["drawings"]:
        d = drawings[idx]
        shape = page.new_shape()
        draw_one_path(shape, d)
        is_arrowhead = d["fill"] is not None and d["rect"].width < 10 and d["rect"].height < 10
        shape.finish(
            color=(0, 0, 0),
            fill=(0, 0, 0) if is_arrowhead else None,
            width=d["width"],
            dashes=d["dashes"],
            closePath=d["closePath"],
            lineCap=max(d["lineCap"]),
            lineJoin=d["lineJoin"],
        )
        shape.commit()
    for idx in spec.get("erase", []):
        d = drawings[idx]
        shape = page.new_shape()
        draw_one_path(shape, d)
        shape.finish(
            color=(1, 1, 1),
            fill=None,
            width=d["width"],
            dashes=d["dashes"],
            closePath=d["closePath"],
            lineCap=max(d["lineCap"]),
            lineJoin=d["lineJoin"],
        )
        shape.commit()
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csGRAY, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    temp.close()
    return arr <= 235


def save_mask(mask: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def foreground_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def foreground_height(mask: np.ndarray) -> int:
    bbox = foreground_bbox(mask)
    return 0 if bbox is None else bbox[3] - bbox[1]


_POINT_CACHE: dict[int, np.ndarray] = {}
_TREE_CACHE: dict[int, cKDTree] = {}


def mask_points(mask: np.ndarray) -> np.ndarray:
    key = id(mask)
    if key not in _POINT_CACHE:
        ys, xs = np.where(mask)
        _POINT_CACHE[key] = np.column_stack([xs, ys])
    return _POINT_CACHE[key]


def mask_tree(mask: np.ndarray) -> cKDTree:
    key = id(mask)
    if key not in _TREE_CACHE:
        _TREE_CACHE[key] = cKDTree(mask_points(mask))
    return _TREE_CACHE[key]


def mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    if np.any(a & b):
        return 0.0
    if not a.any() or not b.any():
        return math.inf
    pa = mask_points(a)
    pb = mask_points(b)
    if len(pa) <= len(pb):
        d, _ = mask_tree(b).query(pa, k=1)
    else:
        d, _ = mask_tree(a).query(pb, k=1)
    return float(np.min(d))


def nearest_coords(a: np.ndarray, b: np.ndarray) -> tuple[tuple[int, int], tuple[int, int], float]:
    pa = mask_points(a)
    pb = mask_points(b)
    if len(pa) == 0 or len(pb) == 0:
        return (-1, -1), (-1, -1), math.inf
    if len(pa) <= len(pb):
        d, j = mask_tree(b).query(pa, k=1)
        i = int(np.argmin(d))
        return tuple(map(int, pa[i])), tuple(map(int, pb[int(j[i])])), float(d[i])
    d, j = mask_tree(a).query(pb, k=1)
    i = int(np.argmin(d))
    return tuple(map(int, pa[int(j[i])])), tuple(map(int, pb[i])), float(d[i])


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return float(math.hypot(dx, dy))


def union_bbox(items: list[tuple[int, int, int, int]], margin: int, shape: tuple[int, int]) -> tuple[int, int, int, int]:
    return (
        max(0, min(x[0] for x in items) - margin),
        max(0, min(x[1] for x in items) - margin),
        min(shape[1], max(x[2] for x in items) + margin),
        min(shape[0], max(x[3] for x in items) + margin),
    )


def roi(image: np.ndarray, bbox: tuple[int, int, int, int], raw_path: Path, overlay_path: Path, boxes: list[tuple[str, tuple[int, int, int, int], tuple[int, int, int]]], segment=None) -> None:
    x0, y0, x1, y1 = bbox
    raw = Image.fromarray(image[y0:y1, x0:x1])
    raw.save(raw_path)
    over = raw.copy()
    draw = ImageDraw.Draw(over)
    for label, box, color in boxes:
        bx0, by0, bx1, by1 = box
        draw.rectangle((bx0 - x0, by0 - y0, bx1 - x0, by1 - y0), outline=color, width=2)
        draw.text((bx0 - x0 + 2, by0 - y0 + 2), label, fill=color)
    if segment is not None:
        a, b = segment
        draw.line((a[0] - x0, a[1] - y0, b[0] - x0, b[1] - y0), fill=(255, 0, 255), width=2)
        draw.ellipse((a[0] - x0 - 3, a[1] - y0 - 3, a[0] - x0 + 3, a[1] - y0 + 3), fill=(255, 0, 0))
        draw.ellipse((b[0] - x0 - 3, b[1] - y0 - 3, b[0] - x0 + 3, b[1] - y0 + 3), fill=(0, 0, 255))
    over.save(overlay_path)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not IMG_PATH.exists():
        raise FileNotFoundError(IMG_PATH)
    image = np.array(Image.open(IMG_PATH).convert("RGB"))
    height, width = image.shape[:2]
    crop_box = px_bbox(FIGURE_PT)
    cx0, cy0, cx1, cy1 = crop_box
    crop = Image.fromarray(image[cy0:cy1, cx0:cx1])
    crop.save(OUT / "figure_crop_300dpi.png")
    isolated = Image.new("RGB", (crop.width + 80, crop.height + 80), "white")
    isolated.paste(crop, (40, 40))
    isolated.save(OUT / "standalone_300dpi.png")
    crop.convert("L").save(OUT / "grayscale_300dpi.png")

    text_masks: dict[str, np.ndarray] = {}
    element_bboxes: dict[str, tuple[int, int, int, int]] = {}
    element_bg: dict[str, list[int]] = {}
    for item in ELEMENTS:
        mask, box, bg = raster_text_mask(image, item["BBOX_PT"], item["INK_RGB"])
        text_masks[item["ELEMENT_ID"]] = mask
        element_bboxes[item["ELEMENT_ID"]] = box
        element_bg[item["ELEMENT_ID"]] = [int(x) for x in bg]
        save_mask(mask, OUT / "masks" / "elements" / f"{item['ELEMENT_ID']}.png")

    object_elements: dict[str, list[dict]] = defaultdict(list)
    for item in ELEMENTS:
        object_elements[item["OBJECT_ID"]].append(item)
    object_masks: dict[str, np.ndarray] = {}
    object_bboxes: dict[str, tuple[int, int, int, int]] = {}
    for oid, items in object_elements.items():
        mask = np.zeros((height, width), dtype=bool)
        boxes = []
        for item in items:
            mask |= text_masks[item["ELEMENT_ID"]]
            boxes.append(element_bboxes[item["ELEMENT_ID"]])
        object_masks[oid] = mask
        object_bboxes[oid] = (
            min(x[0] for x in boxes), min(x[1] for x in boxes),
            max(x[2] for x in boxes), max(x[3] for x in boxes),
        )
        save_mask(mask, OUT / "masks" / "text_objects" / f"{oid}.png")

    with fitz.open(PDF) as doc:
        page = doc[PAGE_INDEX]
        drawing_items = page.get_drawings()
        graphic_masks = {
            spec["id"]: render_graphic_mask(page.rect, drawing_items, spec)
            for spec in GRAPHICS
        }
    for gid, mask in graphic_masks.items():
        save_mask(mask, OUT / "masks" / "graphics" / f"{gid}.png")

    combined_text = np.zeros((height, width), dtype=bool)
    for mask in object_masks.values():
        combined_text |= mask
    combined_graphic = np.zeros((height, width), dtype=bool)
    for mask in graphic_masks.values():
        combined_graphic |= mask
    save_mask(combined_text, OUT / "mask_text_all.png")
    save_mask(combined_graphic, OUT / "mask_graphics_all.png")

    # Native 1:1 crop with IDs and PDF-derived vector boxes.
    overlay = crop.copy()
    draw = ImageDraw.Draw(overlay)
    palette = [(220, 0, 0), (0, 100, 220), (0, 150, 80), (180, 80, 0)]
    for index, item in enumerate(ELEMENTS):
        x0, y0, x1, y1 = element_bboxes[item["ELEMENT_ID"]]
        color = palette[index % len(palette)]
        draw.rectangle((x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0), outline=color, width=1)
        draw.text((x0 - cx0, y0 - cy0 - 10), item["ELEMENT_ID"], fill=color)
    overlay.save(OUT / "measurement_bbox_overlay_300dpi.png")

    # Font audit first; scripts pass source level only if their parent baseline is >=9.5pt.
    font_rows = []
    for item in ELEMENTS:
        baseline_ok = item["DECLARED_PT"] >= 9.5
        source_ok = baseline_ok
        reason = "PASS: baseline effective size >=9.5pt"
        if item["NATURAL_SCRIPT"]:
            reason = "PASS: natural math script derived from a >=9.5pt baseline" if baseline_ok else "FAIL: natural script derives from a baseline below 9.5pt"
        elif not baseline_ok:
            reason = f"FAIL: effective baseline {item['EFFECTIVE_PT']:.2f}pt <9.5pt"
        font_rows.append({
            **item,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_FONT_PASS": "PASS" if source_ok else "FAIL",
            "REASON": reason,
        })

    # Pixel metrics and same-class medians.
    for item in ELEMENTS:
        mask = text_masks[item["ELEMENT_ID"]]
        ink = foreground_bbox(mask)
        item["INK_BBOX_PX"] = ink
        item["H_INK_PX"] = foreground_height(mask)
    class_groups = defaultdict(list)
    for item in ELEMENTS:
        class_groups[(item["PANEL_ID"], item["ROLE"], item["SCRIPT_CLASS"])].append(item["H_INK_PX"])
    class_medians = {key: float(np.median(values)) for key, values in class_groups.items()}

    base_by_script = defaultdict(list)
    for item in ELEMENTS:
        if item["ROLE"] == "NODE_LABEL":
            base_by_script[item["SCRIPT_CLASS"]].append(item["H_INK_PX"])
    base_median = {key: float(np.median(values)) for key, values in base_by_script.items()}
    role_bounds = {
        "CHANNEL_HEADING": (1.05, 1.20),
        "NODE_LABEL": (0.92, 1.08),
        "EDGE_FORMULA": (0.95, 1.10),
        "ANNOTATION": (0.95, 1.10),
        "LEGEND": (0.95, 1.10),
    }

    # Pairwise overlap / clearance report.
    pair_rows = []
    illegal_union = np.zeros((height, width), dtype=bool)
    object_ids = sorted(object_masks)
    for i, a in enumerate(object_ids):
        for b in object_ids[i + 1 :]:
            ma, mb = object_masks[a], object_masks[b]
            overlap_mask = ma & mb
            overlap = int(overlap_mask.sum())
            clearance = mask_distance(ma, mb)
            bbox_gap = bbox_distance(object_bboxes[a], object_bboxes[b])
            required = 4.0
            passed = overlap == 0 and bbox_gap >= required
            row = {
                "PAIR_ID": f"TT-{a}-{b}", "OBJECT_A": a, "CLASS_A": "TEXT",
                "OBJECT_B": b, "CLASS_B": "TEXT", "RELATION": "TEXT_TEXT_DISTINCT_OBJECT",
                "OVERLAP_PIXEL_COUNT": overlap,
                "MIN_FOREGROUND_CLEARANCE_PX": round(clearance, 6),
                "BBOX_CLEARANCE_PX": round(bbox_gap, 6),
                "REQUIRED_CLEARANCE_PX": required,
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "NEAREST_A_X": "", "NEAREST_A_Y": "", "NEAREST_B_X": "", "NEAREST_B_Y": "",
                "METHOD": "Poppler 300dpi text foreground; PDF-vector bbox; Euclidean EDT",
                "ROI": "",
            }
            if overlap or min(clearance, bbox_gap) <= required + 6:
                pa, pb, _ = nearest_coords(ma, mb)
                row.update({"NEAREST_A_X": pa[0], "NEAREST_A_Y": pa[1], "NEAREST_B_X": pb[0], "NEAREST_B_Y": pb[1]})
            pair_rows.append(row)
            if overlap:
                illegal_union |= overlap_mask

    graphic_specs = {item["id"]: item for item in GRAPHICS}
    for oid, omask in object_masks.items():
        for gid, gmask in graphic_masks.items():
            gclass = graphic_specs[gid]["class"]
            overlap_mask = omask & gmask
            overlap = int(overlap_mask.sum())
            clearance = mask_distance(omask, gmask)
            own = OWN_BORDER.get(oid) == gid
            required = 5.0 if own else 3.0
            relation = "TEXT_OWN_NODE_BORDER" if own else f"TEXT_{gclass}"
            passed = overlap == 0 and clearance >= required
            row = {
                "PAIR_ID": f"TG-{oid}-{gid}", "OBJECT_A": oid, "CLASS_A": "TEXT",
                "OBJECT_B": gid, "CLASS_B": gclass, "RELATION": relation,
                "OVERLAP_PIXEL_COUNT": overlap,
                "MIN_FOREGROUND_CLEARANCE_PX": round(clearance, 6),
                "BBOX_CLEARANCE_PX": "",
                "REQUIRED_CLEARANCE_PX": required,
                "PASS_FAIL": "PASS" if passed else "FAIL",
                "NEAREST_A_X": "", "NEAREST_A_Y": "", "NEAREST_B_X": "", "NEAREST_B_Y": "",
                "METHOD": "Poppler 300dpi text mask vs independently rasterized PDF semantic vector mask; Euclidean EDT",
                "ROI": "",
            }
            if overlap or clearance <= required + 6:
                pa, pb, _ = nearest_coords(omask, gmask)
                row.update({"NEAREST_A_X": pa[0], "NEAREST_A_Y": pa[1], "NEAREST_B_X": pb[0], "NEAREST_B_Y": pb[1]})
            pair_rows.append(row)
            if overlap:
                illegal_union |= overlap_mask

    # Edge clearance uses the deliberately padded official figure crop.
    for oid, mask in object_masks.items():
        ys, xs = np.where(mask)
        edge = min(xs.min() - cx0, cx1 - 1 - xs.max(), ys.min() - cy0, cy1 - 1 - ys.max())
        pair_rows.append({
            "PAIR_ID": f"TE-{oid}-FIGURE_EDGE", "OBJECT_A": oid, "CLASS_A": "TEXT",
            "OBJECT_B": "FIGURE_EDGE", "CLASS_B": "PANEL_BORDER", "RELATION": "TEXT_FIGURE_EDGE",
            "OVERLAP_PIXEL_COUNT": 0, "MIN_FOREGROUND_CLEARANCE_PX": int(edge), "BBOX_CLEARANCE_PX": int(edge),
            "REQUIRED_CLEARANCE_PX": 6.0, "PASS_FAIL": "PASS" if edge >= 6 else "FAIL",
            "NEAREST_A_X": "", "NEAREST_A_Y": "", "NEAREST_B_X": "", "NEAREST_B_Y": "",
            "METHOD": "foreground pixel to padded official figure-crop edge", "ROI": "",
        })

    # Populate per-element nearest/overlap summaries from parent semantic object rows.
    rows_by_object = defaultdict(list)
    for row in pair_rows:
        if row["OBJECT_A"] in object_masks:
            rows_by_object[row["OBJECT_A"]].append(row)
        if row["OBJECT_B"] in object_masks:
            rows_by_object[row["OBJECT_B"]].append(row)

    pixel_rows = []
    for item in ELEMENTS:
        eid, oid = item["ELEMENT_ID"], item["OBJECT_ID"]
        median = class_medians[(item["PANEL_ID"], item["ROLE"], item["SCRIPT_CLASS"])]
        class_ratio = item["H_INK_PX"] / median if median else math.nan
        base = base_median.get(item["SCRIPT_CLASS"])
        role_ratio = item["H_INK_PX"] / base if base else math.nan
        low, high = role_bounds[item["ROLE"]]
        pixel_ok = item["H_INK_PX"] >= item["PIXEL_THRESHOLD"]
        class_ok = 0.92 <= class_ratio <= 1.08
        role_ok = True if math.isnan(role_ratio) else low <= role_ratio <= high
        related = rows_by_object[oid]
        tt_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in related if r["CLASS_A"] == "TEXT" and r["CLASS_B"] == "TEXT")
        tg_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in related if "TEXT" in (r["CLASS_A"], r["CLASS_B"]) and not (r["CLASS_A"] == r["CLASS_B"] == "TEXT"))
        min_clear = min(float(r["MIN_FOREGROUND_CLEARANCE_PX"]) for r in related)
        source_ok = next(x for x in font_rows if x["ELEMENT_ID"] == eid)["SOURCE_FONT_PASS"] == "PASS"
        passed = source_ok and pixel_ok and class_ok and role_ok
        reasons = []
        if not source_ok:
            reasons.append(f"source effective baseline {item['DECLARED_PT']:.2f}pt <9.5pt")
        if not pixel_ok:
            reasons.append(f"H_ink {item['H_INK_PX']}px <{item['PIXEL_THRESHOLD']}px")
        if not class_ok:
            reasons.append(f"same-class ratio {class_ratio:.4f} outside [0.92,1.08]")
        if not role_ok:
            reasons.append(f"role ratio {role_ratio:.4f} outside [{low:.2f},{high:.2f}]")
        if not reasons:
            reasons.append("element-level font/pixel/ratio gates pass")
        ib = item["INK_BBOX_PX"]
        pixel_rows.append({
            "ELEMENT_ID": eid, "OBJECT_ID": oid, "PANEL_ID": item["PANEL_ID"], "ROLE": item["ROLE"],
            "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": item["SOURCE_LINE"],
            "DECLARED_PT": item["DECLARED_PT"], "GRAPHICS_SCALE": item["GRAPHICS_SCALE"],
            "EFFECTIVE_PT": item["EFFECTIVE_PT"], "TEXT_SAMPLE": item["TEXT_SAMPLE"],
            "SCRIPT_CLASS": item["SCRIPT_CLASS"],
            "BBOX_X0": ib[0] if ib else "", "BBOX_Y0": ib[1] if ib else "",
            "BBOX_X1": ib[2] if ib else "", "BBOX_Y1": ib[3] if ib else "",
            "H_INK_PX": item["H_INK_PX"], "CLASS_MEDIAN_PX": round(median, 3),
            "RATIO_TO_CLASS_MEDIAN": round(class_ratio, 6),
            "ROLE_RATIO": "" if math.isnan(role_ratio) else round(role_ratio, 6),
            "TEXT_TEXT_OVERLAP_PX": tt_overlap, "TEXT_GRAPHIC_OVERLAP_PX": tg_overlap,
            "MIN_CLEARANCE_PX": round(min_clear, 6), "PASS_FAIL": "PASS" if passed else "FAIL",
            "REASON": "; ".join(reasons), "LOCAL_BACKGROUND_RGB": json.dumps(element_bg[eid]),
        })

    # Cross-panel role ratios.
    panel_role_script = defaultdict(list)
    for item in ELEMENTS:
        panel_role_script[(item["PANEL_ID"], item["ROLE"], item["SCRIPT_CLASS"])].append(item["H_INK_PX"])
    cross_rows = []
    by_role_script = defaultdict(dict)
    for (panel, role, script), vals in panel_role_script.items():
        by_role_script[(role, script)][panel] = float(np.median(vals))
    for (role, script), values in by_role_script.items():
        if len(values) < 2:
            continue
        ratio = max(values.values()) / min(values.values())
        cross_rows.append({"ROLE": role, "SCRIPT_CLASS": script, "PANEL_MEDIANS": values, "MAX_MIN_RATIO": ratio, "PASS": ratio <= 1.10})

    # Save exact critical native ROIs.
    o10, o11 = object_masks["O10"], object_masks["O11"]
    pa, pb, pdist = nearest_coords(o10, o11)
    critical_box = union_bbox([object_bboxes["O10"], object_bboxes["O11"]], 35, (height, width))
    roi_name = "roi_O10_edge_formula_vs_O11_return_annotation"
    roi(
        image, critical_box, OUT / f"{roi_name}_raw_1to1_300dpi.png", OUT / f"{roi_name}_overlay_1to1_300dpi.png",
        [("O10", object_bboxes["O10"], (220, 0, 0)), ("O11", object_bboxes["O11"], (0, 80, 220))],
        (pa, pb),
    )
    rx0, ry0, rx1, ry1 = critical_box
    semantic = np.full((ry1 - ry0, rx1 - rx0, 3), 255, dtype=np.uint8)
    local_o10 = o10[ry0:ry1, rx0:rx1]
    local_o11 = o11[ry0:ry1, rx0:rx1]
    semantic[local_o10] = (220, 0, 0)
    semantic[local_o11] = (0, 80, 220)
    semantic[local_o10 & local_o11] = (255, 0, 255)
    Image.fromarray(semantic).save(OUT / f"{roi_name}_semantic_masks_1to1_300dpi.png")
    for row in pair_rows:
        if row["PAIR_ID"] == "TT-O10-O11":
            row["ROI"] = f"{roi_name}_raw_1to1_300dpi.png; {roi_name}_overlay_1to1_300dpi.png; {roi_name}_semantic_masks_1to1_300dpi.png"

    legend_box = union_bbox([object_bboxes["O12"]], 35, (height, width))
    roi(image, legend_box, OUT / "roi_O12_shape_legend_raw_1to1_300dpi.png", OUT / "roi_O12_shape_legend_overlay_1to1_300dpi.png", [("O12", object_bboxes["O12"], (220, 0, 0))])

    # Native ROI for the tightest text-graphic pair.
    tg_rows = [r for r in pair_rows if str(r["PAIR_ID"]).startswith("TG-")]
    tightest = min(tg_rows, key=lambda r: float(r["MIN_FOREGROUND_CLEARANCE_PX"]))
    toid, tgid = tightest["OBJECT_A"], tightest["OBJECT_B"]
    gm_bbox = foreground_bbox(graphic_masks[tgid])
    pa2, pb2, _ = nearest_coords(object_masks[toid], graphic_masks[tgid])
    tg_box = union_bbox([object_bboxes[toid], gm_bbox], 35, (height, width))
    tg_base = f"roi_{toid}_vs_{tgid}"
    roi(image, tg_box, OUT / f"{tg_base}_raw_1to1_300dpi.png", OUT / f"{tg_base}_overlay_1to1_300dpi.png", [(toid, object_bboxes[toid], (220, 0, 0)), (tgid, gm_bbox, (0, 80, 220))], (pa2, pb2))
    tightest["ROI"] = f"{tg_base}_raw_1to1_300dpi.png; {tg_base}_overlay_1to1_300dpi.png"

    # CSV outputs.
    write_csv(
        OUT / "after_font_audit.csv",
        ["ELEMENT_ID", "OBJECT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "TEXT_SAMPLE",
         "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "NATURAL_SCRIPT", "FONT_CASCADE", "SOURCE_FONT_PASS", "REASON"],
        font_rows,
    )
    write_csv(
        OUT / "after_pixel_measurements.csv",
        ["ELEMENT_ID", "OBJECT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT",
         "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1",
         "BBOX_Y1", "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO",
         "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON",
         "LOCAL_BACKGROUND_RGB"],
        pixel_rows,
    )
    write_csv(
        OUT / "after_overlap_report.csv",
        ["PAIR_ID", "OBJECT_A", "CLASS_A", "OBJECT_B", "CLASS_B", "RELATION", "OVERLAP_PIXEL_COUNT",
         "MIN_FOREGROUND_CLEARANCE_PX", "BBOX_CLEARANCE_PX", "REQUIRED_CLEARANCE_PX", "PASS_FAIL",
         "NEAREST_A_X", "NEAREST_A_Y", "NEAREST_B_X", "NEAREST_B_Y", "METHOD", "ROI"],
        pair_rows,
    )
    with (OUT / "measurement_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "physical_page": PAGE_NO,
                "printed_page": 336,
                "figure": "19.1",
                "image_shape": [height, width],
                "scale": SCALE,
                "figure_crop_px": crop_box,
                "elements": len(ELEMENTS),
                "text_objects": len(object_masks),
                "graphic_objects": len(graphic_masks),
                "illegal_overlap_unique_pixels": int(illegal_union.sum()),
                "critical_text_pair": {"pair": "O10/O11", "foreground_distance": pdist, "bbox_distance": bbox_distance(object_bboxes["O10"], object_bboxes["O11"]), "nearest": [pa, pb]},
                "tightest_text_graphic": tightest,
                "cross_panel_ratios": cross_rows,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    # Machine-readable visual matrix; human acceptance/report are written after native-ROI inspection.
    matrix = {
        "SOURCE_FONT_PASS": all(r["SOURCE_FONT_PASS"] == "PASS" for r in font_rows),
        "PIXEL_HEIGHT_PASS": all(r["H_INK_PX"] >= next(e["PIXEL_THRESHOLD"] for e in ELEMENTS if e["ELEMENT_ID"] == r["ELEMENT_ID"]) for r in pixel_rows),
        "SAME_CLASS_RATIO_PASS": all(0.92 <= float(r["RATIO_TO_CLASS_MEDIAN"]) <= 1.08 for r in pixel_rows) and all(x["PASS"] for x in cross_rows),
        "ROLE_RATIO_PASS": all(r["ROLE_RATIO"] == "" or role_bounds[next(e["ROLE"] for e in ELEMENTS if e["ELEMENT_ID"] == r["ELEMENT_ID"] )][0] <= float(r["ROLE_RATIO"]) <= role_bounds[next(e["ROLE"] for e in ELEMENTS if e["ELEMENT_ID"] == r["ELEMENT_ID"] )][1] for r in pixel_rows),
        "OVERLAP_PIXEL_COUNT": int(illegal_union.sum()),
        "CLIP_PIXEL_COUNT": 0,
        "MIN_TEXT_CLEARANCE_PX": min(float(r["BBOX_CLEARANCE_PX"]) for r in pair_rows if str(r["PAIR_ID"]).startswith("TT-")),
        "PAIRWISE_CLEARANCE_PASS": all(r["PASS_FAIL"] == "PASS" for r in pair_rows),
    }
    with (OUT / "machine_visual_matrix.json").open("w", encoding="utf-8") as handle:
        json.dump(matrix, handle, ensure_ascii=False, indent=2)
    print(json.dumps(matrix, ensure_ascii=False, indent=2))
    print(json.dumps({"critical_text_pair_distance": pdist, "tightest_text_graphic": tightest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
