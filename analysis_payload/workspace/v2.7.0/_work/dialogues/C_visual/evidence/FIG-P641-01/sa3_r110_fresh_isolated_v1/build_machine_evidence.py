from __future__ import annotations

import csv
import itertools
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa3_r110_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex")
PHYSICAL_PAGE = 691
PRINTED_PAGE = 678
PAGE_IMAGE = ROOT / "full_page_300dpi_native.png"

# Coordinates are in PDF points from the top-left.  Crops are mapped once to
# the native 300 dpi page raster and are never resized.
COMPLETE_CROP_PT = (60.0, 550.0, 530.0, 730.0)
BODY_CROP_PT = (115.0, 550.0, 470.0, 696.0)

TEXT_ELEMENTS = {
    "T01_BLANKET_LEGEND": {
        "role": "LEGEND_ANNOTATION",
        "source_lines": "40-41",
        "declared_pt": 9.2,
        "expected": "虚线圈：Markov毯变量𝛼,𝑧,𝑦",
    },
    "T02_NODE_Z": {"role": "NODE_LABEL", "source_lines": "29", "declared_pt": 9.5, "expected": "𝑧"},
    "T03_FACTOR_P_ALPHA": {"role": "FACTOR_LABEL", "source_lines": "24", "declared_pt": 9.5, "expected": "𝑝(𝛼)"},
    "T04_NODE_ALPHA": {"role": "NODE_LABEL", "source_lines": "25", "declared_pt": 9.5, "expected": "𝛼"},
    "T05_FACTOR_THETA_ALPHA": {"role": "FACTOR_LABEL", "source_lines": "26", "declared_pt": 9.5, "expected": "𝑝(𝜃∣𝛼)"},
    "T06_FOCUS_THETA": {"role": "FOCUS_NODE_LABEL", "source_lines": "27", "declared_pt": 9.5, "expected": "𝜃"},
    "T07_FACTOR_ZY_THETA": {"role": "FACTOR_LABEL", "source_lines": "28", "declared_pt": 9.5, "expected": "𝑝(𝑧,𝑦∣𝜃)"},
    "T08_NODE_Y": {"role": "NODE_LABEL", "source_lines": "30", "declared_pt": 9.5, "expected": "𝑦"},
    "T09_ELIMINATED_ANNOTATION": {
        "role": "ANNOTATION",
        "source_lines": "45-46",
        "declared_pt": 9.5,
        "expected": "𝑝(𝛼)与𝜃无关置于毯变量标记外并消去",
    },
    "T10_CONDITIONAL_FORMULA": {
        "role": "FORMULA_BLOCK",
        "source_lines": "42-44",
        "declared_pt": 9.5,
        "expected": "𝜋(𝜃∣𝛼,𝑧,𝑦)∝𝑝(𝜃∣𝛼)𝑝(𝑧,𝑦∣𝜃)",
    },
    "T11_CAPTION": {
        "role": "CAPTION",
        "source_lines": "49-50",
        "declared_pt": None,
        "expected": "图33.8因子图中更新𝜃只需读取与𝜃相连的两个因子𝑝(𝜃∣𝛼)和𝑝(𝑧,𝑦∣𝜃)；Markov毯变量为𝛼,𝑧,𝑦，而与𝜃无关的因子𝑝(𝛼)可从满条件核中消去",
    },
}

GRAPHICS = [
    {"id": "G01_BORDER_FACTOR_P_ALPHA", "collection": "rects", "index": 0, "kind": "NODE_BORDER", "source_lines": "13-14,24", "shape": "rect"},
    {"id": "G02_BORDER_FACTOR_THETA_ALPHA", "collection": "rects", "index": 1, "kind": "NODE_BORDER", "source_lines": "15-16,26", "shape": "rect"},
    {"id": "G03_BORDER_FACTOR_ZY_THETA", "collection": "rects", "index": 2, "kind": "NODE_BORDER", "source_lines": "15-16,28", "shape": "rect"},
    {"id": "G04_BORDER_NODE_ALPHA", "collection": "curves", "index": 2, "kind": "NODE_BORDER", "source_lines": "9-10,25", "shape": "ellipse"},
    {"id": "G05_BORDER_NODE_THETA", "collection": "curves", "index": 3, "kind": "NODE_BORDER", "source_lines": "11-12,27", "shape": "ellipse"},
    {"id": "G06_BORDER_NODE_Z", "collection": "curves", "index": 4, "kind": "NODE_BORDER", "source_lines": "9-10,29", "shape": "ellipse"},
    {"id": "G07_BORDER_NODE_Y", "collection": "curves", "index": 5, "kind": "NODE_BORDER", "source_lines": "9-10,30", "shape": "ellipse"},
    {"id": "G08_BLANKET_ALPHA", "collection": "curves", "index": 6, "kind": "GROUP_BORDER", "source_lines": "36-39", "shape": "rounded_rect"},
    {"id": "G09_BLANKET_Z", "collection": "curves", "index": 7, "kind": "GROUP_BORDER", "source_lines": "36-39", "shape": "rounded_rect"},
    {"id": "G10_BLANKET_Y", "collection": "curves", "index": 8, "kind": "GROUP_BORDER", "source_lines": "36-39", "shape": "rounded_rect"},
    {"id": "G11_EDGE_P_ALPHA_TO_ALPHA", "collection": "lines", "index": 11, "kind": "LINE_ARROW", "source_lines": "32", "shape": "line"},
    {"id": "G12_EDGE_ALPHA_TO_FACTOR", "collection": "lines", "index": 12, "kind": "LINE_ARROW", "source_lines": "33", "shape": "line"},
    {"id": "G13_EDGE_FACTOR_TO_THETA", "collection": "lines", "index": 13, "kind": "LINE_ARROW", "source_lines": "33", "shape": "line"},
    {"id": "G14_EDGE_THETA_TO_FACTOR", "collection": "lines", "index": 14, "kind": "LINE_ARROW", "source_lines": "33", "shape": "line"},
    {"id": "G15_EDGE_FACTOR_TO_Z", "collection": "lines", "index": 15, "kind": "LINE_ARROW", "source_lines": "33", "shape": "line"},
    {"id": "G16_EDGE_FACTOR_TO_Y", "collection": "lines", "index": 16, "kind": "LINE_ARROW", "source_lines": "34", "shape": "line"},
    {"id": "G17_ANNOTATION_ARROW_SHAFT", "collection": "lines", "index": 17, "kind": "LINE_ARROW", "source_lines": "47", "shape": "line"},
    {"id": "G18_ANNOTATION_ARROWHEAD", "collection": "curves", "index": 9, "kind": "ARROWHEAD", "source_lines": "47", "shape": "filled_bbox"},
]

OWN_BORDER = {
    "T02_NODE_Z": "G06_BORDER_NODE_Z",
    "T03_FACTOR_P_ALPHA": "G01_BORDER_FACTOR_P_ALPHA",
    "T04_NODE_ALPHA": "G04_BORDER_NODE_ALPHA",
    "T05_FACTOR_THETA_ALPHA": "G02_BORDER_FACTOR_THETA_ALPHA",
    "T06_FOCUS_THETA": "G05_BORDER_NODE_THETA",
    "T07_FACTOR_ZY_THETA": "G03_BORDER_FACTOR_ZY_THETA",
    "T08_NODE_Y": "G07_BORDER_NODE_Y",
}

DESIGN_CONNECTIONS = {
    frozenset(("G11_EDGE_P_ALPHA_TO_ALPHA", "G01_BORDER_FACTOR_P_ALPHA")),
    frozenset(("G11_EDGE_P_ALPHA_TO_ALPHA", "G04_BORDER_NODE_ALPHA")),
    frozenset(("G12_EDGE_ALPHA_TO_FACTOR", "G04_BORDER_NODE_ALPHA")),
    frozenset(("G12_EDGE_ALPHA_TO_FACTOR", "G02_BORDER_FACTOR_THETA_ALPHA")),
    frozenset(("G13_EDGE_FACTOR_TO_THETA", "G02_BORDER_FACTOR_THETA_ALPHA")),
    frozenset(("G13_EDGE_FACTOR_TO_THETA", "G05_BORDER_NODE_THETA")),
    frozenset(("G14_EDGE_THETA_TO_FACTOR", "G05_BORDER_NODE_THETA")),
    frozenset(("G14_EDGE_THETA_TO_FACTOR", "G03_BORDER_FACTOR_ZY_THETA")),
    frozenset(("G15_EDGE_FACTOR_TO_Z", "G03_BORDER_FACTOR_ZY_THETA")),
    frozenset(("G15_EDGE_FACTOR_TO_Z", "G06_BORDER_NODE_Z")),
    frozenset(("G16_EDGE_FACTOR_TO_Y", "G03_BORDER_FACTOR_ZY_THETA")),
    frozenset(("G16_EDGE_FACTOR_TO_Y", "G07_BORDER_NODE_Y")),
    frozenset(("G17_ANNOTATION_ARROW_SHAFT", "G18_ANNOTATION_ARROWHEAD")),
    frozenset(("G18_ANNOTATION_ARROWHEAD", "G01_BORDER_FACTOR_P_ALPHA")),
    frozenset(("G11_EDGE_P_ALPHA_TO_ALPHA", "G08_BLANKET_ALPHA")),
    frozenset(("G12_EDGE_ALPHA_TO_FACTOR", "G08_BLANKET_ALPHA")),
    frozenset(("G15_EDGE_FACTOR_TO_Z", "G09_BLANKET_Z")),
    frozenset(("G16_EDGE_FACTOR_TO_Y", "G10_BLANKET_Y")),
}


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rgb255(color) -> tuple[int, int, int]:
    if color is None:
        return (0, 0, 0)
    if isinstance(color, (int, float)):
        value = int(round(float(color) * 255))
        return (value, value, value)
    values = list(color)
    if len(values) == 1:
        value = int(round(float(values[0]) * 255))
        return (value, value, value)
    return tuple(int(round(float(value) * 255)) for value in values[:3])


def mode_rgb(array: np.ndarray) -> np.ndarray:
    pixels = array.reshape(-1, 3)
    colors, counts = np.unique(pixels, axis=0, return_counts=True)
    return colors[int(np.argmax(counts))].astype(np.float32)


def color_foreground(
    array: np.ndarray,
    target: tuple[int, int, int],
    background: np.ndarray,
    residual_limit: float = 34.0,
) -> np.ndarray:
    pixels = array.astype(np.float32)
    target_v = np.asarray(target, dtype=np.float32)
    delta = target_v - background
    denom = float(np.dot(delta, delta))
    contrast = np.max(np.abs(pixels - background), axis=2)
    if denom < 400:
        distance = np.linalg.norm(pixels - target_v, axis=2)
        return (distance <= 100.0) & (contrast >= 20.0)
    t = np.sum((pixels - background) * delta, axis=2) / denom
    projected = background + t[..., None] * delta
    residual = np.linalg.norm(pixels - projected, axis=2)
    return (t >= 0.06) & (t <= 1.35) & (residual <= residual_limit) & (contrast >= 20.0)


def keep_largest_components(mask: np.ndarray, count: int) -> np.ndarray:
    height, width = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    for y, x in np.argwhere(mask):
        y = int(y)
        x = int(x)
        if seen[y, x]:
            continue
        stack = [(x, y)]
        seen[y, x] = True
        component: list[tuple[int, int]] = []
        while stack:
            cx, cy = stack.pop()
            component.append((cx, cy))
            for ny in range(max(0, cy - 1), min(height, cy + 2)):
                for nx in range(max(0, cx - 1), min(width, cx + 2)):
                    if mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((nx, ny))
        components.append(component)
    components.sort(key=len, reverse=True)
    result = np.zeros(mask.shape, dtype=bool)
    for component in components[:count]:
        for x, y in component:
            result[y, x] = True
    return result


def pt_box_to_px(box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (math.floor(x0 * sx), math.floor(y0 * sy), math.ceil(x1 * sx), math.ceil(y1 * sy))


def clamp_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (max(0, x0), max(0, y0), min(width, x1), min(height, y1))


def safe_text(text: str) -> str:
    return " ".join(f"U+{ord(char):04X}" for char in text)


def script_class(text: str) -> tuple[str, int]:
    cp = ord(text[0])
    category = unicodedata.category(text[0])
    name = unicodedata.name(text[0], "")
    if text in {",", ".", ":", ";", "，", "。", "：", "；", "、"}:
        return "LOW_PROFILE_PUNCTUATION", 0
    if text in {"(", ")", "[", "]", "{", "}", "∣", "∝", "=", "+", "−", "-"}:
        return "BASE_MATH_OPERATOR", 22
    if "CJK" in name or 0x3400 <= cp <= 0x9FFF:
        return "CJK_FULL", 30
    if text.isdigit() or (text.isalpha() and text.upper() == text and text.lower() != text):
        return "LATIN_UPPER_OR_DIGIT", 24
    if "GREEK" in name or "MATHEMATICAL" in name or (text.isalpha() and text.lower() == text):
        return "LATIN_XHEIGHT_OR_GREEK", 17
    if category.startswith("P"):
        return "LOW_PROFILE_PUNCTUATION", 0
    return "FULL_SYMBOL", 22


def assign_parent(char: dict) -> str:
    top = float(char["top"])
    x0 = float(char["x0"])
    if top < 575:
        return "T01_BLANKET_LEGEND"
    if top < 600 and x0 > 420:
        return "T02_NODE_Z"
    if top < 635:
        if x0 < 190:
            return "T03_FACTOR_P_ALPHA"
        if x0 < 235:
            return "T04_NODE_ALPHA"
        if x0 < 290:
            return "T05_FACTOR_THETA_ALPHA"
        if x0 < 345:
            return "T06_FOCUS_THETA"
        return "T07_FACTOR_ZY_THETA"
    if top < 660 and x0 > 420:
        return "T08_NODE_Y"
    if top < 679 and x0 < 240:
        return "T09_ELIMINATED_ANNOTATION"
    if top < 697:
        return "T10_CONDITIONAL_FORMULA"
    return "T11_CAPTION"


def reading_line(char: dict) -> int:
    top = float(char["top"])
    x0 = float(char["x0"])
    if top < 575:
        return 1
    if top < 600:
        return 2
    if top < 635:
        return 3
    if top < 660 and x0 > 420:
        return 4
    if top < 666:
        return 5
    if top < 679:
        return 6
    if top < 697:
        return 7
    if top < 713:
        return 8
    return 9


def box_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def coords_from_mask(mask: np.ndarray, x0: int, y0: int) -> np.ndarray:
    yy, xx = np.nonzero(mask)
    return np.column_stack((xx + x0, yy + y0)).astype(np.int32)


def encoded_pixels(coords: np.ndarray, width: int) -> set[int]:
    if not len(coords):
        return set()
    return set((coords[:, 1].astype(np.int64) * width + coords[:, 0]).tolist())


def exact_clearance(a: np.ndarray, b: np.ndarray) -> float | None:
    if not len(a) or not len(b):
        return None
    best_sq = float("inf")
    smaller, larger = (a, b) if len(a) <= len(b) else (b, a)
    for start in range(0, len(smaller), 256):
        block = smaller[start : start + 256].astype(np.int32)
        delta = block[:, None, :] - larger[None, :, :].astype(np.int32)
        sq = np.sum(delta * delta, axis=2)
        best_sq = min(best_sq, float(np.min(sq)))
        if best_sq == 0:
            return 0.0
    return max(0.0, math.sqrt(best_sq) - 1.0)


def mask_bbox(coords: np.ndarray) -> tuple[int, int, int, int]:
    if not len(coords):
        return (0, 0, 0, 0)
    return (
        int(coords[:, 0].min()),
        int(coords[:, 1].min()),
        int(coords[:, 0].max()) + 1,
        int(coords[:, 1].max()) + 1,
    )


def crop_mask_image(coords: np.ndarray, bbox: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    out = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)), 0)
    if len(coords):
        arr = np.zeros((max(1, y1 - y0), max(1, x1 - x0)), dtype=np.uint8)
        arr[coords[:, 1] - y0, coords[:, 0] - x0] = 255
        out = Image.fromarray(arr, mode="L")
    return out


def font(size: int = 18) -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\consola.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


page_img = Image.open(PAGE_IMAGE).convert("RGB")
page_array = np.asarray(page_img)

with pdfplumber.open(PDF) as pdf:
    page = pdf.pages[PHYSICAL_PAGE - 1]
    page_width_pt = float(page.width)
    page_height_pt = float(page.height)
    sx = page_img.width / page_width_pt
    sy = page_img.height / page_height_pt

    complete_crop_px = clamp_box(pt_box_to_px(COMPLETE_CROP_PT, sx, sy), page_img.width, page_img.height)
    body_crop_px = clamp_box(pt_box_to_px(BODY_CROP_PT, sx, sy), page_img.width, page_img.height)
    page_img.crop(complete_crop_px).save(ROOT / "figure_crop_300dpi.png")
    page_img.crop(body_crop_px).save(ROOT / "standalone_300dpi.png")
    page_img.crop(complete_crop_px).convert("L").save(ROOT / "grayscale_300dpi.png")

    selected_chars = [
        char
        for char in page.chars
        if float(char["top"]) >= COMPLETE_CROP_PT[1]
        and float(char["bottom"]) <= COMPLETE_CROP_PT[3]
        and float(char["x0"]) >= COMPLETE_CROP_PT[0]
        and float(char["x1"]) <= COMPLETE_CROP_PT[2]
        and str(char.get("text", "")).strip()
    ]
    selected_chars.sort(key=lambda char: (reading_line(char), float(char["x0"]), float(char["top"])))

    glyph_candidates: list[dict] = []
    for number, char in enumerate(selected_chars, start=1):
        glyph_id = f"C{number:03d}"
        text_value = str(char["text"])
        parent_id = assign_parent(char)
        px_box = clamp_box(
            pt_box_to_px((float(char["x0"]), float(char["top"]), float(char["x1"]), float(char["bottom"])), sx, sy),
            page_img.width,
            page_img.height,
        )
        x0, y0, x1, y1 = px_box
        pad_box = clamp_box((x0 - 2, y0 - 2, x1 + 2, y1 + 2), page_img.width, page_img.height)
        px0, py0, px1, py1 = pad_box
        padded = page_array[py0:py1, px0:px1]
        background = mode_rgb(padded)
        target = rgb255(char.get("non_stroking_color"))
        local = page_array[y0:y1, x0:x1]
        candidate = color_foreground(local, target, background)
        unicode_name = unicodedata.name(text_value[0], "")
        is_cjk = "CJK" in unicode_name or 0x3400 <= ord(text_value[0]) <= 0x9FFF
        if len(text_value) == 1 and not is_cjk and (text_value.isalnum() or "MATHEMATICAL" in unicode_name):
            candidate = keep_largest_components(candidate, 1)
        if text_value in {"(", ")", ".", ",", "，", "。"}:
            candidate = keep_largest_components(candidate, 1)
        elif text_value in {":", ";", "：", "；"}:
            candidate = keep_largest_components(candidate, 2)
        coords = coords_from_mask(candidate, x0, y0)
        glyph_candidates.append(
            {
                "id": glyph_id,
                "safe_filename": f"{glyph_id}.png",
                "text": text_value,
                "codepoints": safe_text(text_value),
                "unicode_name": " | ".join(unicodedata.name(value, "UNNAMED") for value in text_value),
                "parent_id": parent_id,
                "role": TEXT_ELEMENTS[parent_id]["role"],
                "source_lines": TEXT_ELEMENTS[parent_id]["source_lines"],
                "declared_pt": TEXT_ELEMENTS[parent_id]["declared_pt"],
                "pdf_size_pt": float(char.get("size", 0.0)),
                "fontname": str(char.get("fontname", "")),
                "target_rgb": target,
                "background_rgb": tuple(int(value) for value in background),
                "bbox_pt": (float(char["x0"]), float(char["top"]), float(char["x1"]), float(char["bottom"])),
                "bbox_px": px_box,
                "coords": coords,
            }
        )

    # Resolve any raster pixel proposed for more than one PDF character by the
    # nearest PDF-character center.  The resulting raw glyph masks are disjoint.
    owners: dict[int, list[int]] = defaultdict(list)
    for idx, glyph in enumerate(glyph_candidates):
        for encoded in encoded_pixels(glyph["coords"], page_img.width):
            owners[encoded].append(idx)
    assigned: list[list[tuple[int, int]]] = [[] for _ in glyph_candidates]
    for encoded, candidates in owners.items():
        y, x = divmod(encoded, page_img.width)
        if len(candidates) == 1:
            chosen = candidates[0]
        else:
            def score(index: int) -> float:
                gx0, gy0, gx1, gy1 = glyph_candidates[index]["bbox_px"]
                return (x - (gx0 + gx1) / 2.0) ** 2 + (y - (gy0 + gy1) / 2.0) ** 2
            chosen = min(candidates, key=score)
        assigned[chosen].append((x, y))
    for glyph, points in zip(glyph_candidates, assigned):
        glyph["coords"] = np.asarray(points, dtype=np.int32).reshape((-1, 2))

    graphic_objects: list[dict] = []
    for spec in GRAPHICS:
        obj = getattr(page, spec["collection"])[spec["index"]]
        box_pt = (float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"]))
        raw_box = pt_box_to_px(box_pt, sx, sy)
        box_px = clamp_box((raw_box[0] - 3, raw_box[1] - 3, raw_box[2] + 3, raw_box[3] + 3), page_img.width, page_img.height)
        x0, y0, x1, y1 = box_px
        local = page_array[y0:y1, x0:x1]
        target = rgb255(obj.get("stroking_color"))
        # Infer the paint background from a wider context than the narrow
        # stroked-path bbox.  A thin line can otherwise occupy most of its
        # three-pixel-padded crop, making its own stroke color the modal
        # "background" and reducing the raw mask to a few antialias pixels.
        context_pad = 14
        context = page_array[
            max(0, y0 - context_pad):min(page_img.height, y1 + context_pad),
            max(0, x0 - context_pad):min(page_img.width, x1 + context_pad),
        ]
        background = mode_rgb(context)
        if np.linalg.norm(background - np.asarray(target, dtype=np.float32)) < 20.0:
            background = np.asarray((255, 255, 255), dtype=np.float32)
        # The blue/teal figure palette is intentionally close.  A tighter
        # residual prevents a node ring from leaking into its surrounding
        # dashed blanket mask while still retaining antialias pixels that lie
        # on the target-to-background mixture line.
        color_mask = color_foreground(local, target, background, residual_limit=16.0)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        linewidth_px = max(1.0, float(obj.get("linewidth", 0.8)) * (sx + sy) / 2.0)
        band = max(3.0, linewidth_px * 1.8)
        shape = spec["shape"]
        gx0, gy0, gx1, gy1 = pt_box_to_px(box_pt, sx, sy)
        if shape == "line":
            # bbox top/bottom loses the ordered endpoints for a rising
            # diagonal.  pdfplumber's pts retain those endpoints in the same
            # top-origin page coordinate used by the raster.
            if obj.get("pts") and len(obj["pts"]) >= 2:
                line_x0 = float(obj["pts"][0][0]) * sx
                line_y0 = float(obj["pts"][0][1]) * sy
                line_x1 = float(obj["pts"][1][0]) * sx
                line_y1 = float(obj["pts"][1][1]) * sy
            else:
                line_x0, line_y0, line_x1, line_y1 = gx0, gy0, gx1, gy1
            vx = line_x1 - line_x0
            vy = line_y1 - line_y0
            denom = float(vx * vx + vy * vy) or 1.0
            t = np.clip(((xx - line_x0) * vx + (yy - line_y0) * vy) / denom, 0.0, 1.0)
            distance = np.hypot(xx - (line_x0 + t * vx), yy - (line_y0 + t * vy))
            geometry = distance <= band
        elif shape == "rect":
            within = (xx >= gx0 - band) & (xx <= gx1 + band) & (yy >= gy0 - band) & (yy <= gy1 + band)
            distance = np.minimum.reduce((np.abs(xx - gx0), np.abs(xx - gx1), np.abs(yy - gy0), np.abs(yy - gy1)))
            geometry = within & (distance <= band)
        elif shape == "ellipse":
            cx = (gx0 + gx1) / 2.0
            cy = (gy0 + gy1) / 2.0
            rx = max(1.0, (gx1 - gx0) / 2.0)
            ry = max(1.0, (gy1 - gy0) / 2.0)
            radius = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
            geometry = np.abs(radius - 1.0) <= band / min(rx, ry)
        elif shape == "rounded_rect":
            # Source line 37 specifies rounded corners=7pt and the TikZ
            # geometry is scaled 1.1.  Use the exact rounded-rectangle signed
            # distance instead of a broad bbox ring, which can reach the
            # nested circular node and create false path overlap.
            cx = (gx0 + gx1) / 2.0
            cy = (gy0 + gy1) / 2.0
            half_w = (gx1 - gx0) / 2.0
            half_h = (gy1 - gy0) / 2.0
            corner_radius = min(7.0 * 1.1 * (sx + sy) / 2.0, half_w, half_h)
            qx = np.abs(xx - cx) - (half_w - corner_radius)
            qy = np.abs(yy - cy) - (half_h - corner_radius)
            outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
            inside = np.minimum(np.maximum(qx, qy), 0.0)
            signed_distance = outside + inside - corner_radius
            geometry = np.abs(signed_distance) <= max(3.0, band)
        else:
            geometry = np.ones(color_mask.shape, dtype=bool)
        mask = color_mask & geometry
        coords = coords_from_mask(mask, x0, y0)
        graphic_objects.append(
            {
                **spec,
                "bbox_pt": box_pt,
                "bbox_px": box_px,
                "linewidth_pt": float(obj.get("linewidth", 0.0)),
                "stroke_rgb": target,
                "coords": coords,
            }
        )

auto_drawing_intersections = []
with pdfplumber.open(PDF) as pdf:
    page = pdf.pages[PHYSICAL_PAGE - 1]
    for collection in ("lines", "rects", "curves"):
        for index, obj in enumerate(getattr(page, collection)):
            x0, top, x1, bottom = float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"])
            if x1 >= BODY_CROP_PT[0] and x0 <= BODY_CROP_PT[2] and bottom >= BODY_CROP_PT[1] and top <= BODY_CROP_PT[3]:
                auto_drawing_intersections.append((collection, index))

glyph_dir = ROOT / "masks" / "glyphs"
graphic_dir = ROOT / "masks" / "graphics"
semantic_dir = ROOT / "masks" / "semantic"
roi_dir = ROOT / "critical_rois"
contact_dir = ROOT / "glyph_contact_sheets"
for directory in (glyph_dir, graphic_dir, semantic_dir, roi_dir, contact_dir):
    directory.mkdir(parents=True, exist_ok=True)

glyph_rows: list[dict] = []
mask_objects: list[dict] = []
parent_coords: dict[str, list[np.ndarray]] = defaultdict(list)
for glyph in glyph_candidates:
    coords = glyph["coords"]
    bbox = glyph["bbox_px"]
    mask_path = glyph_dir / glyph["safe_filename"]
    crop_mask_image(coords, bbox).save(mask_path)
    parent_coords[glyph["parent_id"]].append(coords)
    if len(coords):
        height = int(coords[:, 1].max() - coords[:, 1].min() + 1)
        width = int(coords[:, 0].max() - coords[:, 0].min() + 1)
    else:
        height = 0
        width = 0
    cls, threshold = script_class(glyph["text"])
    glyph_rows.append(
        {
            "element_id": glyph["id"],
            "semantic_parent": glyph["parent_id"],
            "role": glyph["role"],
            "source_file": str(SOURCE),
            "source_lines": glyph["source_lines"],
            "declared_pt": "INHERITED_CAPTION_STYLE" if glyph["declared_pt"] is None else glyph["declared_pt"],
            "graphics_scale": "1.0_NODE_TEXT_NOT_TRANSFORMED",
            "effective_pt_basis": glyph["pdf_size_pt"] if glyph["declared_pt"] is None else glyph["declared_pt"],
            "pdf_vector_size_pt": round(glyph["pdf_size_pt"], 5),
            "text": glyph["text"],
            "codepoints": glyph["codepoints"],
            "unicode_name": glyph["unicode_name"],
            "script_class": cls,
            "numeric_reference_threshold_px": threshold,
            "bbox_pt": ",".join(f"{value:.5f}" for value in glyph["bbox_pt"]),
            "bbox_px": ",".join(str(value) for value in bbox),
            "h_ink_px": height,
            "w_ink_px": width,
            "ink_area_px": len(coords),
            "target_rgb": ",".join(map(str, glyph["target_rgb"])),
            "background_rgb": ",".join(map(str, glyph["background_rgb"])),
            "fontname": glyph["fontname"],
            "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
            "safe_filename": glyph["safe_filename"],
        }
    )
    mask_objects.append(
        {
            "id": glyph["id"],
            "object_class": "GLYPH",
            "role": glyph["role"],
            "parent": glyph["parent_id"],
            "bbox": bbox,
            "coords": coords,
            "encoded": encoded_pixels(coords, page_img.width),
        }
    )

graphic_rows: list[dict] = []
for graphic in graphic_objects:
    coords = graphic["coords"]
    bbox = graphic["bbox_px"]
    mask_path = graphic_dir / f'{graphic["id"]}.png'
    crop_mask_image(coords, bbox).save(mask_path)
    graphic_rows.append(
        {
            "object_id": graphic["id"],
            "object_class": graphic["kind"],
            "pdf_collection": graphic["collection"],
            "pdf_collection_index": graphic["index"],
            "source_file": str(SOURCE),
            "source_lines": graphic["source_lines"],
            "bbox_pt": ",".join(f"{value:.5f}" for value in graphic["bbox_pt"]),
            "bbox_px": ",".join(str(value) for value in bbox),
            "linewidth_pt": graphic["linewidth_pt"],
            "stroke_rgb": ",".join(map(str, graphic["stroke_rgb"])),
            "ink_area_px": len(coords),
            "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
        }
    )
    mask_objects.append(
        {
            "id": graphic["id"],
            "object_class": graphic["kind"],
            "role": graphic["kind"],
            "parent": graphic["id"],
            "bbox": bbox,
            "coords": coords,
            "encoded": encoded_pixels(coords, page_img.width),
        }
    )

semantic_objects: list[dict] = []
text_element_rows: list[dict] = []
for element_id, metadata in TEXT_ELEMENTS.items():
    arrays = [array for array in parent_coords[element_id] if len(array)]
    coords = np.vstack(arrays) if arrays else np.empty((0, 2), dtype=np.int32)
    bbox = mask_bbox(coords)
    mask_path = semantic_dir / f"{element_id}.png"
    crop_mask_image(coords, bbox).save(mask_path)
    glyphs = [glyph for glyph in glyph_candidates if glyph["parent_id"] == element_id]
    extracted = "".join(glyph["text"] for glyph in glyphs)
    vector_sizes = [glyph["pdf_size_pt"] for glyph in glyphs]
    text_element_rows.append(
        {
            "element_id": element_id,
            "role": metadata["role"],
            "source_lines": metadata["source_lines"],
            "declared_pt": "INHERITED_CAPTION_STYLE" if metadata["declared_pt"] is None else metadata["declared_pt"],
            "graphics_scale": "1.0_NODE_TEXT_NOT_TRANSFORMED",
            "expected_visible_text": metadata["expected"],
            "extracted_visible_text": extracted,
            "glyph_count": len(glyphs),
            "pdf_vector_size_min_pt": round(min(vector_sizes), 5) if vector_sizes else "",
            "pdf_vector_size_median_pt": round(float(np.median(vector_sizes)), 5) if vector_sizes else "",
            "pdf_vector_size_max_pt": round(max(vector_sizes), 5) if vector_sizes else "",
            "bbox_px": ",".join(map(str, bbox)),
            "ink_area_px": len(coords),
            "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
        }
    )
    semantic_objects.append(
        {
            "id": element_id,
            "object_class": "TEXT_ELEMENT",
            "role": metadata["role"],
            "bbox": bbox,
            "coords": coords,
            "encoded": encoded_pixels(coords, page_img.width),
        }
    )

for graphic in mask_objects[len(glyph_candidates) :]:
    semantic_objects.append(graphic)

write_csv(
    ROOT / "after_pixel_measurements.csv",
    glyph_rows,
    [
        "element_id", "semantic_parent", "role", "source_file", "source_lines", "declared_pt", "graphics_scale",
        "effective_pt_basis", "pdf_vector_size_pt", "text", "codepoints", "unicode_name", "script_class",
        "numeric_reference_threshold_px", "bbox_pt", "bbox_px", "h_ink_px", "w_ink_px", "ink_area_px",
        "target_rgb", "background_rgb", "fontname", "mask_path", "safe_filename",
    ],
)
write_csv(
    ROOT / "text_elements.csv",
    text_element_rows,
    [
        "element_id", "role", "source_lines", "declared_pt", "graphics_scale", "expected_visible_text",
        "extracted_visible_text", "glyph_count", "pdf_vector_size_min_pt", "pdf_vector_size_median_pt",
        "pdf_vector_size_max_pt", "bbox_px", "ink_area_px", "mask_path",
    ],
)
write_csv(
    ROOT / "graphics_inventory.csv",
    graphic_rows,
    [
        "object_id", "object_class", "pdf_collection", "pdf_collection_index", "source_file", "source_lines",
        "bbox_pt", "bbox_px", "linewidth_pt", "stroke_rgb", "ink_area_px", "mask_path",
    ],
)
write_csv(
    ROOT / "id_safe_filename_map.csv",
    [
        {"object_id": row["element_id"], "safe_filename": row["safe_filename"], "ordinary_relative_path": row["mask_path"]}
        for row in glyph_rows
    ]
    + [
        {"object_id": row["object_id"], "safe_filename": f'{row["object_id"]}.png', "ordinary_relative_path": row["mask_path"]}
        for row in graphic_rows
    ],
    ["object_id", "safe_filename", "ordinary_relative_path"],
)

pair_rows: list[dict] = []
for pair_number, (a, b) in enumerate(itertools.combinations(mask_objects, 2), start=1):
    overlap = len(a["encoded"] & b["encoded"])
    gap = box_gap(a["bbox"], b["bbox"])
    exact = None
    method = "BBOX_LOWER_BOUND"
    if overlap:
        exact = 0.0
        method = "RAW_MASK_INTERSECTION"
    elif gap <= 12 and not (a["object_class"] == "GLYPH" and b["object_class"] == "GLYPH" and a["parent"] == b["parent"]):
        exact = exact_clearance(a["coords"], b["coords"])
        method = "RAW_MASK_EUCLIDEAN"
    if a["object_class"] == "GLYPH" and b["object_class"] == "GLYPH":
        relation_class = "GLYPH_SAME_PARENT" if a["parent"] == b["parent"] else "TEXT_TEXT"
    elif a["object_class"] == "GLYPH" or b["object_class"] == "GLYPH":
        graphic = b if a["object_class"] == "GLYPH" else a
        relation_class = "TEXT_GRAPHIC_" + graphic["object_class"]
    else:
        relation_class = "GRAPHIC_GRAPHIC"
    pair_rows.append(
        {
            "pair_id": f"P{pair_number:05d}",
            "object_a": a["id"],
            "object_b": b["id"],
            "class_a": a["object_class"],
            "class_b": b["object_class"],
            "parent_a": a["parent"],
            "parent_b": b["parent"],
            "relation_class": relation_class,
            "bbox_gap_px": round(gap, 4),
            "raw_mask_overlap_px": overlap,
            "raw_mask_clearance_px": "" if exact is None else round(exact, 4),
            "clearance_method": method,
            "source_design_connection": "YES" if frozenset((a["id"], b["id"])) in DESIGN_CONNECTIONS else "NO",
        }
    )

write_csv(
    ROOT / "all_unordered_pairs.csv",
    pair_rows,
    [
        "pair_id", "object_a", "object_b", "class_a", "class_b", "parent_a", "parent_b", "relation_class",
        "bbox_gap_px", "raw_mask_overlap_px", "raw_mask_clearance_px", "clearance_method", "source_design_connection",
    ],
)

# Semantic critical candidates: every close independent text relation, every
# close text/graphic relation, every source-declared node-border containment,
# and every source-declared graphic connection.  This is a machine selection,
# not a reviewer decision.
critical_candidates: list[dict] = []
seen_critical: set[frozenset[str]] = set()
for a, b in itertools.combinations(semantic_objects, 2):
    pair_key = frozenset((a["id"], b["id"]))
    overlap = len(a["encoded"] & b["encoded"])
    gap = box_gap(a["bbox"], b["bbox"])
    reasons: list[str] = []
    if pair_key in DESIGN_CONNECTIONS:
        reasons.append("SOURCE_DESIGN_CONNECTION")
    if a["id"] in OWN_BORDER and OWN_BORDER[a["id"]] == b["id"]:
        reasons.append("OWN_NODE_TEXT_TO_BORDER")
    if b["id"] in OWN_BORDER and OWN_BORDER[b["id"]] == a["id"]:
        reasons.append("OWN_NODE_TEXT_TO_BORDER")
    if a["object_class"] == "TEXT_ELEMENT" and b["object_class"] == "TEXT_ELEMENT" and gap <= 24:
        reasons.append("INDEPENDENT_TEXT_PROXIMITY_LE_24PX")
    if (a["object_class"] == "TEXT_ELEMENT") != (b["object_class"] == "TEXT_ELEMENT") and gap <= 24:
        reasons.append("TEXT_GRAPHIC_PROXIMITY_LE_24PX")
    if a["object_class"] != "TEXT_ELEMENT" and b["object_class"] != "TEXT_ELEMENT" and (gap <= 8 or overlap):
        reasons.append("GRAPHIC_PROXIMITY_OR_INTERSECTION")
    if not reasons:
        continue
    seen_critical.add(pair_key)
    exact = 0.0 if overlap else exact_clearance(a["coords"], b["coords"])
    critical_candidates.append(
        {
            "a": a,
            "b": b,
            "selection_rule": "+".join(reasons),
            "bbox_gap_px": gap,
            "overlap_px": overlap,
            "clearance_px": exact,
        }
    )

# Always include figure/body-to-caption and legend-to-nearest blanket boundary,
# because they are required page/semantic layout checks even when not within the
# proximity trigger.
for a_id, b_id, reason in (
    ("T10_CONDITIONAL_FORMULA", "T11_CAPTION", "FIGURE_BODY_TO_CAPTION"),
    ("T01_BLANKET_LEGEND", "G09_BLANKET_Z", "LEGEND_TO_NEAREST_GROUP_BORDER"),
    ("T09_ELIMINATED_ANNOTATION", "T10_CONDITIONAL_FORMULA", "ANNOTATION_TO_FORMULA"),
):
    a = next(obj for obj in semantic_objects if obj["id"] == a_id)
    b = next(obj for obj in semantic_objects if obj["id"] == b_id)
    key = frozenset((a_id, b_id))
    if key not in seen_critical:
        overlap = len(a["encoded"] & b["encoded"])
        critical_candidates.append(
            {
                "a": a,
                "b": b,
                "selection_rule": reason,
                "bbox_gap_px": box_gap(a["bbox"], b["bbox"]),
                "overlap_px": overlap,
                "clearance_px": 0.0 if overlap else exact_clearance(a["coords"], b["coords"]),
            }
        )
        seen_critical.add(key)

critical_rows: list[dict] = []
critical_thumbnails: list[Image.Image] = []
for number, item in enumerate(critical_candidates, start=1):
    relation_id = f"R{number:03d}"
    a, b = item["a"], item["b"]
    ux0 = max(0, min(a["bbox"][0], b["bbox"][0]) - 12)
    uy0 = max(0, min(a["bbox"][1], b["bbox"][1]) - 12)
    ux1 = min(page_img.width, max(a["bbox"][2], b["bbox"][2]) + 12)
    uy1 = min(page_img.height, max(a["bbox"][3], b["bbox"][3]) + 12)
    roi = page_img.crop((ux0, uy0, ux1, uy1))
    overlay = roi.copy()
    draw = ImageDraw.Draw(overlay)
    for obj, color in ((a, (255, 0, 0)), (b, (0, 100, 255))):
        coords = obj["coords"]
        if len(coords):
            local = coords - np.array((ux0, uy0), dtype=np.int32)
            overlay_arr = np.asarray(overlay).copy()
            valid = (
                (local[:, 0] >= 0) & (local[:, 0] < overlay_arr.shape[1]) &
                (local[:, 1] >= 0) & (local[:, 1] < overlay_arr.shape[0])
            )
            local = local[valid]
            overlay_arr[local[:, 1], local[:, 0]] = color
            overlay = Image.fromarray(overlay_arr)
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, overlay.width - 1, overlay.height - 1), outline=(0, 0, 0), width=1)
    intersection = a["encoded"] & b["encoded"]
    inter_image = Image.new("L", roi.size, 0)
    if intersection:
        inter_arr = np.zeros((roi.height, roi.width), dtype=np.uint8)
        for encoded in intersection:
            y, x = divmod(encoded, page_img.width)
            if ux0 <= x < ux1 and uy0 <= y < uy1:
                inter_arr[y - uy0, x - ux0] = 255
        inter_image = Image.fromarray(inter_arr, mode="L")
    a_image = Image.new("L", roi.size, 0)
    b_image = Image.new("L", roi.size, 0)
    for obj, target_image in ((a, a_image), (b, b_image)):
        arr = np.zeros((roi.height, roi.width), dtype=np.uint8)
        coords = obj["coords"]
        valid = (
            (coords[:, 0] >= ux0) & (coords[:, 0] < ux1) &
            (coords[:, 1] >= uy0) & (coords[:, 1] < uy1)
        ) if len(coords) else np.zeros(0, dtype=bool)
        local = coords[valid] - np.array((ux0, uy0), dtype=np.int32) if len(coords) else np.empty((0, 2), dtype=np.int32)
        if len(local):
            arr[local[:, 1], local[:, 0]] = 255
        target_image.paste(Image.fromarray(arr, mode="L"))
    base = f"{relation_id}_{a['id']}__{b['id']}"
    roi.save(roi_dir / f"{base}_native1x.png")
    overlay.save(roi_dir / f"{base}_overlay_native1x.png")
    a_image.save(roi_dir / f"{base}_mask_a.png")
    b_image.save(roi_dir / f"{base}_mask_b.png")
    inter_image.save(roi_dir / f"{base}_intersection.png")
    overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(roi_dir / f"{base}_nearest8x.png")
    critical_rows.append(
        {
            "relation_id": relation_id,
            "object_a": a["id"],
            "object_b": b["id"],
            "selection_rule": item["selection_rule"],
            "roi_bbox_fullpage_px": f"{ux0},{uy0},{ux1},{uy1}",
            "raw_mask_overlap_px": item["overlap_px"],
            "raw_mask_clearance_px": "" if item["clearance_px"] is None else round(item["clearance_px"], 4),
            "native1x_path": f"critical_rois/{base}_native1x.png",
            "nearest8x_path": f"critical_rois/{base}_nearest8x.png",
            "mask_a_path": f"critical_rois/{base}_mask_a.png",
            "mask_b_path": f"critical_rois/{base}_mask_b.png",
            "intersection_path": f"critical_rois/{base}_intersection.png",
        }
    )
    thumb = Image.new("RGB", (760, 260), "white")
    td = ImageDraw.Draw(thumb)
    td.text((8, 6), f"{relation_id} {a['id']} / {b['id']}", fill="black", font=font(16))
    td.text((8, 28), f"overlap={item['overlap_px']} clearance={item['clearance_px']}", fill="black", font=font(15))
    preview = overlay.copy()
    scale = min(720 / max(1, preview.width), 210 / max(1, preview.height), 8.0)
    preview = preview.resize((max(1, int(preview.width * scale)), max(1, int(preview.height * scale))), Image.Resampling.NEAREST)
    thumb.paste(preview, (20, 48))
    critical_thumbnails.append(thumb)

write_csv(
    ROOT / "critical_relations_machine.csv",
    critical_rows,
    [
        "relation_id", "object_a", "object_b", "selection_rule", "roi_bbox_fullpage_px", "raw_mask_overlap_px",
        "raw_mask_clearance_px", "native1x_path", "nearest8x_path", "mask_a_path", "mask_b_path", "intersection_path",
    ],
)

for sheet_index in range(0, len(critical_thumbnails), 12):
    batch = critical_thumbnails[sheet_index : sheet_index + 12]
    sheet = Image.new("RGB", (1520, 260 * 6), "white")
    for idx, thumb in enumerate(batch):
        col = idx % 2
        row = idx // 2
        sheet.paste(thumb, (col * 760, row * 260))
    sheet.save(ROOT / f"critical_relations_contact_sheet_{sheet_index // 12 + 1:02d}.png")

# Glyph contact sheets.  Every cell uses the same native padded crop for the
# original, target-only overlay, and mask-only panels, each scaled exactly 8x
# with nearest-neighbour interpolation.
glyph_cells: list[Image.Image] = []
for idx, glyph in enumerate(glyph_candidates, start=1):
    x0, y0, x1, y1 = glyph["bbox_px"]
    box = clamp_box((x0 - 3, y0 - 3, x1 + 3, y1 + 3), page_img.width, page_img.height)
    bx0, by0, bx1, by1 = box
    original = page_img.crop(box)
    overlay = original.copy()
    overlay_arr = np.asarray(overlay).copy()
    coords = glyph["coords"]
    if len(coords):
        local = coords - np.array((bx0, by0), dtype=np.int32)
        valid = (
            (local[:, 0] >= 0) & (local[:, 0] < overlay_arr.shape[1]) &
            (local[:, 1] >= 0) & (local[:, 1] < overlay_arr.shape[0])
        )
        local = local[valid]
        overlay_arr[local[:, 1], local[:, 0]] = (255, 0, 0)
    overlay = Image.fromarray(overlay_arr)
    mask_arr = np.zeros((original.height, original.width), dtype=np.uint8)
    if len(coords):
        local = coords - np.array((bx0, by0), dtype=np.int32)
        valid = (
            (local[:, 0] >= 0) & (local[:, 0] < mask_arr.shape[1]) &
            (local[:, 1] >= 0) & (local[:, 1] < mask_arr.shape[0])
        )
        local = local[valid]
        mask_arr[local[:, 1], local[:, 0]] = 255
    mask_only = Image.fromarray(mask_arr, mode="L").convert("RGB")
    views = [
        image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)
        for image in (original, overlay, mask_only)
    ]
    cell = Image.new("RGB", (1260, 430), "white")
    draw = ImageDraw.Draw(cell)
    draw.text((8, 6), f"{glyph['id']} parent={glyph['parent_id']} char={glyph['codepoints']}", fill="black", font=font(18))
    draw.text((8, 30), "ORIGINAL", fill="black", font=font(15))
    draw.text((425, 30), "TARGET OVERLAY", fill="black", font=font(15))
    draw.text((842, 30), "MASK ONLY", fill="black", font=font(15))
    for panel, x in zip(views, (8, 425, 842)):
        panel.thumbnail((400, 380), Image.Resampling.NEAREST)
        cell.paste(panel, (x, 48))
    glyph_cells.append(cell)

glyph_sheet_map_rows: list[dict] = []
for sheet_start in range(0, len(glyph_cells), 8):
    batch = glyph_cells[sheet_start : sheet_start + 8]
    sheet_number = sheet_start // 8 + 1
    sheet = Image.new("RGB", (2520, 1720), "white")
    for local_index, cell in enumerate(batch):
        col = local_index % 2
        row = local_index // 2
        sheet.paste(cell, (col * 1260, row * 430))
        glyph = glyph_candidates[sheet_start + local_index]
        glyph_sheet_map_rows.append(
            {
                "glyph_id": glyph["id"],
                "sheet": f"glyph_contact_sheets/contact_sheet_{sheet_number:02d}.png",
                "cell": f"r{row + 1}c{col + 1}",
            }
        )
    sheet.save(contact_dir / f"contact_sheet_{sheet_number:02d}.png")

write_csv(ROOT / "glyph_contact_sheet_map.csv", glyph_sheet_map_rows, ["glyph_id", "sheet", "cell"])

# Object and text overlays on the complete native crop.
cx0, cy0, cx1, cy1 = complete_crop_px
semantic_overlay = page_img.crop(complete_crop_px).copy()
sd = ImageDraw.Draw(semantic_overlay)
palette = [(220, 30, 30), (0, 105, 210), (0, 145, 80), (180, 90, 0)]
for idx, obj in enumerate(semantic_objects):
    x0, y0, x1, y1 = obj["bbox"]
    box = (x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0)
    color = palette[idx % len(palette)]
    sd.rectangle(box, outline=color, width=2)
    sd.text((box[0] + 2, max(0, box[1] - 18)), obj["id"], fill=color, font=font(13))
semantic_overlay.save(ROOT / "semantic_object_overlay_300dpi.png")

glyph_overlay = page_img.crop(complete_crop_px).copy()
gd = ImageDraw.Draw(glyph_overlay)
for glyph in glyph_candidates:
    x0, y0, x1, y1 = glyph["bbox_px"]
    box = (x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0)
    gd.rectangle(box, outline=(255, 0, 0), width=1)
    gd.text((box[0], max(0, box[1] - 9)), glyph["id"][1:], fill=(160, 0, 0), font=font(8))
glyph_overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

# Summary is metrics-only: it intentionally contains no reviewer identity,
# manual decision, note, or PASS/FAIL field.
glyph_heights = [row["h_ink_px"] for row in glyph_rows]
low_profile_count = sum(row["script_class"] == "LOW_PROFILE_PUNCTUATION" for row in glyph_rows)
summary = {
    "handoff_id": "C-FIG-P641-01-R110-SA3-FRESH-ISOLATED-V1",
    "uid": "FIG-P641-01",
    "official_pdf": str(PDF),
    "physical_page": PHYSICAL_PAGE,
    "printed_page": PRINTED_PAGE,
    "page_pt": [page_width_pt, page_height_pt],
    "native_300dpi_page_px": [page_img.width, page_img.height],
    "native_scale_px_per_pt": [sx, sy],
    "complete_crop_pt": COMPLETE_CROP_PT,
    "complete_crop_px": complete_crop_px,
    "body_crop_pt": BODY_CROP_PT,
    "body_crop_px": body_crop_px,
    "visible_text_element_count": len(TEXT_ELEMENTS),
    "visible_glyph_count": len(glyph_candidates),
    "visible_foreground_graphic_count": len(graphic_objects),
    "complete_foreground_object_denominator": len(mask_objects),
    "all_unordered_pair_count": len(pair_rows),
    "pair_count_formula": f"{len(mask_objects)}*{len(mask_objects)-1}/2",
    "critical_relation_count": len(critical_rows),
    "glyph_mask_count": len(glyph_rows),
    "graphic_mask_count": len(graphic_rows),
    "empty_glyph_mask_count": sum(row["ink_area_px"] == 0 for row in glyph_rows),
    "empty_graphic_mask_count": sum(row["ink_area_px"] == 0 for row in graphic_rows),
    "low_profile_punctuation_count": low_profile_count,
    "glyph_height_px_min": min(glyph_heights),
    "glyph_height_px_median": float(np.median(glyph_heights)),
    "glyph_height_px_max": max(glyph_heights),
    "raw_pair_overlap_nonzero_count": sum(row["raw_mask_overlap_px"] > 0 for row in pair_rows),
    "raw_pair_overlap_pixel_sum": sum(row["raw_mask_overlap_px"] for row in pair_rows),
    "pdf_drawing_intersections_in_body": [f"{collection}:{index}" for collection, index in auto_drawing_intersections],
    "pdf_drawing_intersection_count_in_body": len(auto_drawing_intersections),
    "accounted_pdf_drawing_objects": [f'{row["pdf_collection"]}:{row["pdf_collection_index"]}' for row in graphic_rows],
    "math_rule_count": 0,
    "math_rule_reason": "No overline/underline/hat/vector-accent/root/fraction/cancel rule is present; every visible PDF line/rect/curve in the figure body is assigned to one of G01-G18.",
}
(ROOT / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
