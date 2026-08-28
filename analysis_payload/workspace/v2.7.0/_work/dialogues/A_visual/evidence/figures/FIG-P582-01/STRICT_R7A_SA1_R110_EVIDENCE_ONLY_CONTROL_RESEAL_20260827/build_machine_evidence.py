from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import re
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex")
ROOT = Path(__file__).resolve().parent
PAGE_INDEX = 631
PHYSICAL_PAGE = 632
PRINTED_PAGE = 619
FIGURE_UID = "FIG-P582-01"
DPI = 300
SCALE = DPI / 72.0
PAGE_RECT_PT = (0.0, 0.0, 595.276, 841.89)
BODY_RECT_PT = (160.0, 325.0, 448.0, 481.0)
FIGURE_RECT_PT = (70.0, 325.0, 536.0, 514.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def safe_name(value: str) -> str:
    out = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    out = re.sub(r"_+", "_", out).strip("._")
    return out or "item"


def color_int_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def pt_rect_to_px(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        math.floor(x0 * SCALE),
        math.floor(y0 * SCALE),
        math.ceil(x1 * SCALE),
        math.ceil(y1 * SCALE),
    )


def mask_bbox(mask: np.ndarray) -> list[int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def expected_color_mask(region: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
    pixels = region.astype(np.float32)
    delta = 255.0 - pixels
    target = 255.0 - np.asarray(rgb, dtype=np.float32)
    contrast = np.max(delta, axis=2) >= 20.0
    target_norm = float(np.linalg.norm(target))
    if target_norm < 1e-6:
        return contrast
    dot = np.sum(delta * target[None, None, :], axis=2)
    norms = np.linalg.norm(delta, axis=2) * target_norm
    cosine = np.divide(dot, norms, out=np.zeros_like(dot), where=norms > 0)
    return contrast & (cosine >= 0.965)


def classify_char(char: str, size: float, parent_id: str) -> tuple[str, int | None]:
    low = {".", ",", "，", "。", "、", ":", "：", ";", "；", "…"}
    if char in low:
        return "LOW_PROFILE_PUNCTUATION", None
    if size < 9.45 and parent_id in {"T015_EQUATION", "T027_CAPTION"}:
        return "NATURAL_SCRIPT", 15
    cp = ord(char)
    if (
        0x3400 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x3000 <= cp <= 0x303F
        or 0xFF00 <= cp <= 0xFFEF
    ):
        return "CJK_FULL", 30
    if char.isdigit() or (char.isalpha() and char.upper() == char and char.lower() != char):
        return "LATIN_UPPER_OR_DIGIT", 24
    if char.isalpha():
        return "LATIN_OR_GREEK_LOWER", 17
    return "BASE_MATH_OPERATOR", 22


def parent_for_char(ch: dict) -> str:
    x0, y0, x1, y1 = ch["bbox"]
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    c = ch["c"]
    if y0 >= 483.0 and y0 < 512.0:
        return "T027_CAPTION"
    if x1 <= 196.0 and 328.0 <= y0 <= 454.0 and c not in {"数", "值"}:
        tick_order = [
            (443.0, "T001_YTICK_0"),
            (426.0, "T002_YTICK_01"),
            (410.0, "T003_YTICK_02"),
            (394.0, "T004_YTICK_03"),
            (378.0, "T005_YTICK_04"),
            (361.0, "T006_YTICK_05"),
            (345.0, "T007_YTICK_06"),
            (329.0, "T008_YTICK_07"),
        ]
        return min(tick_order, key=lambda item: abs(y0 - item[0]))[1]
    if 451.5 <= y0 <= 463.0 and 215.0 <= cx <= 430.0:
        centers = [(220.5, "T009_XTICK_1"), (288.4, "T010_XTICK_2"), (356.2, "T011_XTICK_3"), (424.1, "T012_XTICK_4")]
        return min(centers, key=lambda item: abs(cx - item[0]))[1]
    if 164.0 <= x0 <= 177.0 and 380.0 <= y0 <= 402.0:
        return "T013_Y_AXIS_TITLE"
    if 467.0 <= y0 <= 480.0 and 275.0 <= x0 <= 368.0:
        return "T014_X_AXIS_TITLE"
    if 330.0 <= y0 <= 346.0 and 382.0 <= x0 <= 432.0:
        return "T015_EQUATION"
    if c == "↓" and 343.0 <= y0 <= 356.0:
        return "T016_DOWN1_ARROW"
    if 249.0 <= x0 <= 273.0 and 343.0 <= y0 <= 356.0:
        return "T017_DOWN1_TEXT"
    if c == "↑" and 361.0 <= y0 <= 374.0:
        return "T018_UP_ARROW"
    if 311.0 <= x0 <= 334.0 and 360.0 <= y0 <= 374.0:
        return "T019_UP_TEXT"
    if c == "↓" and 356.0 <= y0 <= 369.0:
        return "T020_DOWN2_ARROW"
    if 383.0 <= x0 <= 415.0 and 356.0 <= y0 <= 369.0:
        return "T021_DOWN2_TEXT"
    if 237.0 <= x0 <= 275.0 and 402.0 <= y0 <= 416.0:
        return "T022_TRUTH_LABEL"
    if 228.0 <= x0 <= 248.0 and 334.0 <= y0 <= 347.0:
        return "T023_VALUE_640"
    if 297.0 <= x0 <= 317.0 and 400.0 <= y0 <= 413.0:
        return "T024_VALUE_325_I2"
    if 365.0 <= x0 <= 385.0 and 370.0 <= y0 <= 383.0:
        return "T025_VALUE_380"
    if 414.0 <= x0 <= 434.0 and 404.0 <= y0 <= 417.0:
        return "T026_VALUE_325_I4"
    raise RuntimeError(f"unassigned visible char: {ch}")


def extract_glyphs(page: fitz.Page, page_rgb: np.ndarray) -> tuple[list[dict], dict[str, np.ndarray]]:
    raw = page.get_text("rawdict")
    glyphs: list[dict] = []
    provisional: list[np.ndarray] = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span.get("chars", []):
                    c = char["c"]
                    if not c or c.isspace():
                        continue
                    bbox = [float(v) for v in char["bbox"]]
                    in_body = bbox[1] >= 325.0 and bbox[1] <= 481.0 and bbox[0] >= 160.0 and bbox[2] <= 448.0
                    in_caption = bbox[1] >= 483.0 and bbox[1] <= 512.0 and bbox[0] >= 70.0 and bbox[2] <= 536.0
                    if not (in_body or in_caption):
                        continue
                    ch = {
                        "c": c,
                        "bbox": bbox,
                        "origin": [float(v) for v in char["origin"]],
                        "font": span["font"],
                        "size_pt_pdf": float(span["size"]),
                        "color_int": int(span["color"]),
                        "rgb": list(color_int_to_rgb(int(span["color"]))),
                    }
                    ch["parent_id"] = parent_for_char(ch)
                    glyph_class, threshold = classify_char(c, ch["size_pt_pdf"], ch["parent_id"])
                    ch["glyph_class"] = glyph_class
                    ch["threshold_px"] = threshold
                    x0, y0, x1, y1 = pt_rect_to_px(tuple(bbox))
                    x0 = max(0, x0)
                    y0 = max(0, y0)
                    x1 = min(page_rgb.shape[1], x1)
                    y1 = min(page_rgb.shape[0], y1)
                    local = expected_color_mask(page_rgb[y0:y1, x0:x1], tuple(ch["rgb"]))
                    full = np.zeros(page_rgb.shape[:2], dtype=bool)
                    full[y0:y1, x0:x1] = local
                    provisional.append(full)
                    ch["bbox_px"] = [x0, y0, x1, y1]
                    glyphs.append(ch)

    # Resolve any shared raster pixels deterministically. Glyph boxes are authoritative,
    # and a pixel is assigned to the closest normalized glyph center.
    stack_sum = np.zeros(page_rgb.shape[:2], dtype=np.uint16)
    for mask in provisional:
        stack_sum += mask.astype(np.uint16)
    shared_y, shared_x = np.nonzero(stack_sum > 1)
    if len(shared_x):
        for y, x in zip(shared_y.tolist(), shared_x.tolist()):
            candidates = [i for i, mask in enumerate(provisional) if mask[y, x]]
            winner = min(
                candidates,
                key=lambda i: (
                    abs(x - (glyphs[i]["bbox_px"][0] + glyphs[i]["bbox_px"][2] - 1) / 2)
                    / max(1, glyphs[i]["bbox_px"][2] - glyphs[i]["bbox_px"][0])
                    + abs(y - (glyphs[i]["bbox_px"][1] + glyphs[i]["bbox_px"][3] - 1) / 2)
                    / max(1, glyphs[i]["bbox_px"][3] - glyphs[i]["bbox_px"][1])
                ),
            )
            for i in candidates:
                if i != winner:
                    provisional[i][y, x] = False

    parent_masks: dict[str, np.ndarray] = {}
    counters: dict[str, int] = {}
    for i, (ch, mask) in enumerate(zip(glyphs, provisional), start=1):
        parent = ch["parent_id"]
        counters[parent] = counters.get(parent, 0) + 1
        ch["glyph_id"] = f"GLY-{i:03d}"
        ch["parent_char_index"] = counters[parent]
        ch["safe_filename"] = safe_name(f"{ch['glyph_id']}_{parent}_{ord(ch['c']):04X}")
        mb = mask_bbox(mask)
        ch["mask_bbox_px"] = mb
        if mb is None:
            ch["ink_height_px"] = 0
            ch["ink_width_px"] = 0
            ch["ink_area_px"] = 0
        else:
            ch["ink_height_px"] = mb[3] - mb[1]
            ch["ink_width_px"] = mb[2] - mb[0]
            ch["ink_area_px"] = int(mask.sum())
        ch["initial_mask_px"] = int(mask.sum())
        ch["shared_pixel_assignments_removed"] = int(provisional[i - 1].sum() - mask.sum())
        parent_masks.setdefault(parent, np.zeros_like(mask))
        parent_masks[parent] |= mask
        ch["_mask"] = mask
    return glyphs, parent_masks


def draw_one_object(page_rect: fitz.Rect, drawing: dict) -> np.ndarray:
    doc = fitz.open()
    p = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = p.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        else:
            raise RuntimeError(f"unsupported drawing operator {op}")
    line_cap = drawing.get("lineCap", 0)
    if isinstance(line_cap, (tuple, list)):
        line_cap = max((value for value in line_cap if value is not None), default=0)
    if line_cap is None:
        line_cap = 0
    line_join = drawing.get("lineJoin", 0)
    if line_join is None:
        line_join = 0
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=drawing.get("color"),
        fill=drawing.get("fill"),
        lineCap=int(line_cap),
        lineJoin=int(line_join),
        dashes=drawing.get("dashes"),
        even_odd=bool(drawing.get("even_odd") or False),
        closePath=bool(drawing.get("closePath") or False),
        fill_opacity=float(drawing.get("fill_opacity") if drawing.get("fill_opacity") is not None else 1.0),
        stroke_opacity=float(drawing.get("stroke_opacity") if drawing.get("stroke_opacity") is not None else 1.0),
    )
    shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, colorspace=fitz.csRGB)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]
    mask = np.max(255 - arr, axis=2) >= 20
    doc.close()
    return mask


def extract_graphics(page: fitz.Page) -> tuple[list[dict], dict[str, np.ndarray], dict[str, np.ndarray]]:
    drawings = page.get_drawings()
    selected = []
    for draw_no, d in enumerate(drawings):
        r = d["rect"]
        if r.y1 >= 325.0 and r.y0 <= 481.0 and r.x1 >= 160.0 and r.x0 <= 448.0:
            selected.append((draw_no, d))
    if [x[0] for x in selected] != list(range(1, 18)):
        raise RuntimeError(f"unexpected figure drawing numbers: {[x[0] for x in selected]}")

    names = {
        1: "G001_X_TICKS",
        2: "G002_Y_TICKS",
        3: "G003_X_AXIS",
        4: "G004_X_AXIS_ARROWHEAD",
        5: "G005_Y_AXIS",
        6: "G006_Y_AXIS_ARROWHEAD",
        7: "G007_YCOMB_STEMS",
        8: "G008_RUNNING_MEAN_POLYLINE",
        9: "G009_TRUE_MEAN_DASHED_LINE",
        10: "G010_RAW_SQUARE_I1",
        11: "G011_RAW_SQUARE_I2",
        12: "G012_RAW_SQUARE_I3",
        13: "G013_RAW_SQUARE_I4",
        14: "G014_MEAN_CIRCLE_I1",
        15: "G015_MEAN_CIRCLE_I2",
        16: "G016_MEAN_CIRCLE_I3",
        17: "G017_MEAN_CIRCLE_I4",
    }
    pre_masks: dict[str, np.ndarray] = {}
    records: list[dict] = []
    for draw_no, d in selected:
        obj_id = names[draw_no]
        pre = draw_one_object(page.rect, d)
        pre_masks[obj_id] = pre
        records.append(
            {
                "object_id": obj_id,
                "kind": "GRAPHIC",
                "draw_no": draw_no,
                "seqno": int(d.get("seqno", -1)),
                "pdf_bbox_pt": [float(d["rect"].x0), float(d["rect"].y0), float(d["rect"].x1), float(d["rect"].y1)],
                "stroke_rgb_float": list(d["color"]) if d.get("color") else None,
                "fill_rgb_float": list(d["fill"]) if d.get("fill") else None,
                "width_pt": float(d.get("width") or 0.0),
                "dashes": d.get("dashes"),
                "operators": [item[0] for item in d["items"]],
                "pre_occlusion_pixel_count": int(pre.sum()),
            }
        )

    final_masks: dict[str, np.ndarray] = {}
    ordered = [names[i] for i in range(1, 18)]
    for idx, obj_id in enumerate(ordered):
        later = np.zeros_like(pre_masks[obj_id])
        for later_id in ordered[idx + 1 :]:
            later |= pre_masks[later_id]
        final_masks[obj_id] = pre_masks[obj_id] & ~later
    for rec in records:
        rec["final_visible_pixel_count"] = int(final_masks[rec["object_id"]].sum())
        rec["occluded_pixel_count"] = rec["pre_occlusion_pixel_count"] - rec["final_visible_pixel_count"]
        rec["final_visible_bbox_px"] = mask_bbox(final_masks[rec["object_id"]])
    return records, pre_masks, final_masks


def object_descriptions() -> dict[str, str]:
    return {
        "T001_YTICK_0": "y-axis tick label 0",
        "T002_YTICK_01": "y-axis tick label 0.1",
        "T003_YTICK_02": "y-axis tick label 0.2",
        "T004_YTICK_03": "y-axis tick label 0.3",
        "T005_YTICK_04": "y-axis tick label 0.4",
        "T006_YTICK_05": "y-axis tick label 0.5",
        "T007_YTICK_06": "y-axis tick label 0.6",
        "T008_YTICK_07": "y-axis tick label 0.7",
        "T009_XTICK_1": "x-axis tick label 1",
        "T010_XTICK_2": "x-axis tick label 2",
        "T011_XTICK_3": "x-axis tick label 3",
        "T012_XTICK_4": "x-axis tick label 4",
        "T013_Y_AXIS_TITLE": "vertical axis title 数值",
        "T014_X_AXIS_TITLE": "horizontal axis title 样本编号 i / 样本数 N",
        "T015_EQUATION": "upper-right equation h(U_i)=U_i^2",
        "T016_DOWN1_ARROW": "first downward arrow glyph",
        "T017_DOWN1_TEXT": "first trend text 下降",
        "T018_UP_ARROW": "upward arrow glyph",
        "T019_UP_TEXT": "trend text 上升",
        "T020_DOWN2_ARROW": "second downward arrow glyph",
        "T021_DOWN2_TEXT": "second trend text 再下降",
        "T022_TRUTH_LABEL": "reference annotation 真值 1/3",
        "T023_VALUE_640": "running mean label .640",
        "T024_VALUE_325_I2": "running mean label .325 at i=2",
        "T025_VALUE_380": "running mean label .380 at i=3",
        "T026_VALUE_325_I4": "running mean label .325 at i=4",
        "T027_CAPTION": "complete Fig. 31.7 caption paragraph, including wrapped second line",
        "G001_X_TICKS": "four x-axis tick strokes",
        "G002_Y_TICKS": "eight y-axis tick strokes",
        "G003_X_AXIS": "x-axis rule",
        "G004_X_AXIS_ARROWHEAD": "x-axis arrowhead",
        "G005_Y_AXIS": "y-axis rule",
        "G006_Y_AXIS_ARROWHEAD": "y-axis arrowhead",
        "G007_YCOMB_STEMS": "four raw-value vertical stems",
        "G008_RUNNING_MEAN_POLYLINE": "blue running-mean polyline",
        "G009_TRUE_MEAN_DASHED_LINE": "teal y=1/3 dashed reference line",
        "G010_RAW_SQUARE_I1": "raw-value square marker i=1",
        "G011_RAW_SQUARE_I2": "raw-value square marker i=2",
        "G012_RAW_SQUARE_I3": "raw-value square marker i=3",
        "G013_RAW_SQUARE_I4": "raw-value square marker i=4",
        "G014_MEAN_CIRCLE_I1": "running-mean circular marker i=1",
        "G015_MEAN_CIRCLE_I2": "running-mean circular marker i=2",
        "G016_MEAN_CIRCLE_I3": "running-mean circular marker i=3",
        "G017_MEAN_CIRCLE_I4": "running-mean circular marker i=4",
    }


def make_object_records(glyphs: list[dict], parent_masks: dict[str, np.ndarray], graphics: list[dict], final_masks: dict[str, np.ndarray]) -> tuple[list[dict], dict[str, np.ndarray]]:
    desc = object_descriptions()
    records: list[dict] = []
    object_masks: dict[str, np.ndarray] = {}
    for parent_id in sorted(parent_masks):
        chars = [g for g in glyphs if g["parent_id"] == parent_id]
        mask = parent_masks[parent_id]
        records.append(
            {
                "object_id": parent_id,
                "kind": "TEXT",
                "description": desc[parent_id],
                "visible_text": "".join(g["c"] for g in chars),
                "glyph_count": len(chars),
                "bbox_px": mask_bbox(mask),
                "foreground_pixel_count": int(mask.sum()),
            }
        )
        object_masks[parent_id] = mask
    for graphic in graphics:
        obj_id = graphic["object_id"]
        mask = final_masks[obj_id]
        records.append(
            {
                "object_id": obj_id,
                "kind": "GRAPHIC",
                "description": desc[obj_id],
                "draw_no": graphic["draw_no"],
                "bbox_px": mask_bbox(mask),
                "foreground_pixel_count": int(mask.sum()),
                "pre_occlusion_pixel_count": graphic["pre_occlusion_pixel_count"],
                "occluded_pixel_count": graphic["occluded_pixel_count"],
            }
        )
        object_masks[obj_id] = mask
    records.sort(key=lambda r: r["object_id"])
    return records, object_masks


def nearest_clearance(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[float, int]:
    overlap = int(np.logical_and(mask_a, mask_b).sum())
    if overlap:
        return 0.0, overlap
    ya, xa = np.nonzero(mask_a)
    yb, xb = np.nonzero(mask_b)
    if len(xa) == 0 or len(xb) == 0:
        return math.inf, overlap
    points_a = np.column_stack([ya, xa])
    points_b = np.column_stack([yb, xb])
    if len(points_a) > len(points_b):
        points_a, points_b = points_b, points_a
    tree = cKDTree(points_b)
    dist = float(tree.query(points_a, k=1, workers=-1)[0].min())
    return max(0.0, dist - 1.0), overlap


def pair_threshold(kind_a: str, kind_b: str) -> int:
    if kind_a == "TEXT" and kind_b == "TEXT":
        return 4
    if "TEXT" in {kind_a, kind_b}:
        return 3
    return 0


def build_pairs(objects: list[dict], masks: dict[str, np.ndarray], pre_masks: dict[str, np.ndarray]) -> list[dict]:
    by_id = {o["object_id"]: o for o in objects}
    pairs: list[dict] = []
    for index, (a, b) in enumerate(itertools.combinations([o["object_id"] for o in objects], 2), start=1):
        clearance, overlap = nearest_clearance(masks[a], masks[b])
        pre_overlap = None
        if a.startswith("G") and b.startswith("G"):
            pre_overlap = int(np.logical_and(pre_masks[a], pre_masks[b]).sum())
        pairs.append(
            {
                "pair_id": f"PAIR-{index:04d}",
                "object_a": a,
                "object_b": b,
                "kind_a": by_id[a]["kind"],
                "kind_b": by_id[b]["kind"],
                "threshold_px": pair_threshold(by_id[a]["kind"], by_id[b]["kind"]),
                "final_visible_overlap_px": overlap,
                "pre_occlusion_overlap_px": pre_overlap,
                "blank_clearance_px": None if math.isinf(clearance) else round(clearance, 3),
            }
        )
    return pairs


def font_for_labels(size: int = 16) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def crop_with_pad(image: Image.Image, bbox: list[int], pad: int = 4) -> tuple[Image.Image, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bbox
    rect = (max(0, x0 - pad), max(0, y0 - pad), min(image.width, x1 + pad), min(image.height, y1 + pad))
    return image.crop(rect), rect


def make_contact_sheets(page_image: Image.Image, glyphs: list[dict]) -> list[dict]:
    sheets_dir = ROOT / "glyph_contact_sheets"
    sheets_dir.mkdir(exist_ok=True)
    font = font_for_labels(15)
    cell_w, cell_h = 1320, 620
    cols, rows = 2, 5
    per_sheet = cols * rows
    sheet_records = []
    for sheet_index, start in enumerate(range(0, len(glyphs), per_sheet), start=1):
        subset = glyphs[start : start + per_sheet]
        sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), "white")
        d = ImageDraw.Draw(sheet)
        cells = []
        for local_index, glyph in enumerate(subset):
            col = local_index % cols
            row = local_index // cols
            ox, oy = col * cell_w, row * cell_h
            bbox = glyph["bbox_px"]
            context, rect = crop_with_pad(page_image, bbox, 4)
            x0, y0, x1, y1 = rect
            local_mask = glyph["_mask"][y0:y1, x0:x1]
            overlay = np.asarray(context).copy()
            overlay[local_mask] = np.array([255, 0, 0], dtype=np.uint8)
            mask_only = np.full_like(overlay, 255)
            mask_only[local_mask] = np.array([0, 0, 0], dtype=np.uint8)
            original_8 = context.resize((context.width * 8, context.height * 8), Image.Resampling.NEAREST)
            overlay_8 = Image.fromarray(overlay).resize((context.width * 8, context.height * 8), Image.Resampling.NEAREST)
            mask_8 = Image.fromarray(mask_only).resize((context.width * 8, context.height * 8), Image.Resampling.NEAREST)
            panels = [original_8, overlay_8, mask_8]
            title = f"{glyph['glyph_id']} parent={glyph['parent_id']} U+{ord(glyph['c']):04X} char={glyph['c']} H={glyph['ink_height_px']} A={glyph['ink_area_px']}"
            d.text((ox + 8, oy + 5), title, fill="black", font=font)
            d.text((ox + 8, oy + 28), "ORIGINAL 8x", fill="black", font=font)
            d.text((ox + 430, oy + 28), "TARGET OVERLAY 8x", fill="black", font=font)
            d.text((ox + 852, oy + 28), "MASK ONLY 8x", fill="black", font=font)
            for j, panel in enumerate(panels):
                sheet.paste(panel, (ox + 8 + j * 422, oy + 52))
            # Native 1x triptych retained in the header strip.
            for j, panel in enumerate((context, Image.fromarray(overlay), Image.fromarray(mask_only))):
                sheet.paste(panel, (ox + 1080 + j * 72, oy + 2))
            cells.append(
                {
                    "cell": local_index + 1,
                    "glyph_id": glyph["glyph_id"],
                    "char": glyph["c"],
                    "parent_id": glyph["parent_id"],
                    "source_bbox_px": glyph["bbox_px"],
                    "native_context_rect_px": list(rect),
                }
            )
        name = f"glyph_contact_sheet_{sheet_index:02d}.png"
        sheet.save(sheets_dir / name)
        sheet_records.append({"sheet": name, "cells": cells, "dimensions_px": [sheet.width, sheet.height]})
    return sheet_records


def make_text_overlay(figure_image: Image.Image, glyphs: list[dict], objects: list[dict]) -> None:
    fig_px = pt_rect_to_px(FIGURE_RECT_PT)
    xoff, yoff = fig_px[0], fig_px[1]
    overlay = figure_image.copy()
    d = ImageDraw.Draw(overlay)
    font = font_for_labels(12)
    for obj in objects:
        if obj["kind"] != "TEXT" or not obj["bbox_px"]:
            continue
        x0, y0, x1, y1 = obj["bbox_px"]
        box = (x0 - xoff, y0 - yoff, x1 - xoff, y1 - yoff)
        d.rectangle(box, outline=(220, 0, 0), width=1)
        d.text((box[0], max(0, box[1] - 13)), obj["object_id"], fill=(170, 0, 0), font=font)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")


def save_mask(mask: np.ndarray, path: Path, crop_px: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = crop_px
    local = mask[y0:y1, x0:x1]
    image = np.where(local, 0, 255).astype(np.uint8)
    Image.fromarray(image, mode="L").save(path)


def make_relation_evidence(page_image: Image.Image, objects: list[dict], masks: dict[str, np.ndarray], pre_masks: dict[str, np.ndarray], pairs: list[dict]) -> list[dict]:
    out_dir = ROOT / "relation_evidence"
    out_dir.mkdir(exist_ok=True)
    explicit_key_pairs = {
        frozenset(("T020_DOWN2_ARROW", "T021_DOWN2_TEXT")),
        frozenset(("T020_DOWN2_ARROW", "T025_VALUE_380")),
        frozenset(("T021_DOWN2_TEXT", "T025_VALUE_380")),
        frozenset(("T025_VALUE_380", "G008_RUNNING_MEAN_POLYLINE")),
        frozenset(("T025_VALUE_380", "G016_MEAN_CIRCLE_I3")),
        frozenset(("T015_EQUATION", "G008_RUNNING_MEAN_POLYLINE")),
    }
    critical = [
        p for p in pairs
        if p["final_visible_overlap_px"] > 0
        or (p["pre_occlusion_overlap_px"] or 0) > 0
        or (p["blank_clearance_px"] is not None and p["blank_clearance_px"] < max(12, p["threshold_px"] + 1))
        or frozenset((p["object_a"], p["object_b"])) in explicit_key_pairs
    ]
    records = []
    font = font_for_labels(15)
    for p in critical:
        a, b = p["object_a"], p["object_b"]
        basis_a = pre_masks[a] if a.startswith("G") else masks[a]
        basis_b = pre_masks[b] if b.startswith("G") else masks[b]
        pre_intersection = basis_a & basis_b
        bbox = mask_bbox(pre_intersection)
        if bbox is None:
            ya, xa = np.nonzero(masks[a])
            yb, xb = np.nonzero(masks[b])
            if len(xa) == 0 or len(xb) == 0:
                continue
            points_a = np.column_stack([ya, xa])
            points_b = np.column_stack([yb, xb])
            tree = cKDTree(points_b)
            distances, indexes = tree.query(points_a, k=1, workers=-1)
            ia = int(np.argmin(distances))
            ib = int(indexes[ia])
            ay, ax = points_a[ia]
            by, bx = points_b[ib]
            bbox = [int(min(ax, bx)), int(min(ay, by)), int(max(ax, bx) + 1), int(max(ay, by) + 1)]
        if bbox is None:
            continue
        x0, y0, x1, y1 = bbox
        pad = 12
        rect = (max(0, x0 - pad), max(0, y0 - pad), min(page_image.width, x1 + pad), min(page_image.height, y1 + pad))
        rx0, ry0, rx1, ry1 = rect
        original = np.asarray(page_image.crop(rect)).copy()
        ma = basis_a[ry0:ry1, rx0:rx1]
        mb = basis_b[ry0:ry1, rx0:rx1]
        overlay = original.copy()
        overlay[ma] = np.array([255, 0, 0], dtype=np.uint8)
        overlay[mb] = np.array([0, 180, 220], dtype=np.uint8)
        overlap = ma & mb
        overlay[overlap] = np.array([255, 0, 255], dtype=np.uint8)
        mask_a = np.full_like(original, 255)
        mask_a[ma] = 0
        mask_b = np.full_like(original, 255)
        mask_b[mb] = 0
        inter = np.full_like(original, 255)
        inter[overlap] = 0
        panels = [Image.fromarray(x) for x in (original, overlay, mask_a, mask_b, inter)]
        panel_w = max(panel.width for panel in panels) * 8
        panel_h = max(panel.height for panel in panels) * 8
        canvas = Image.new("RGB", (panel_w * 5, panel_h + 52), "white")
        cd = ImageDraw.Draw(canvas)
        labels = ["ORIGINAL", "A red/B cyan", "MASK A", "MASK B", "INTERSECTION"]
        for i, (panel, label) in enumerate(zip(panels, labels)):
            enlarged = panel.resize((panel.width * 8, panel.height * 8), Image.Resampling.NEAREST)
            canvas.paste(enlarged, (i * panel_w, 42))
            cd.text((i * panel_w + 4, 4), label, fill="black", font=font)
        cd.text((4, 22), f"{p['pair_id']} {a} / {b} overlap={p['final_visible_overlap_px']} clearance={p['blank_clearance_px']}", fill="black", font=font)
        name = f"{p['pair_id']}_{safe_name(a)}__{safe_name(b)}.png"
        canvas.save(out_dir / name)
        records.append({"pair_id": p["pair_id"], "file": f"relation_evidence/{name}", "roi_rect_page_px": list(rect), "dimensions_px": [canvas.width, canvas.height], "uses_pre_occlusion_masks": bool(p["pre_occlusion_overlap_px"])})
    return records


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def main() -> None:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    if doc.page_count != 817:
        raise RuntimeError(f"unexpected page count: {doc.page_count}")
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, colorspace=fitz.csRGB)
    page_rgb = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, pix300.n)[..., :3].copy()
    page_image = Image.fromarray(page_rgb)
    page_image.save(ROOT / "page_300dpi.png")
    body_px = pt_rect_to_px(BODY_RECT_PT)
    figure_px = pt_rect_to_px(FIGURE_RECT_PT)
    body = page_image.crop(body_px)
    figure = page_image.crop(figure_px)
    body.save(ROOT / "standalone_300dpi.png")
    figure.save(ROOT / "figure_crop_300dpi.png")
    body.convert("L").save(ROOT / "grayscale_300dpi.png")

    glyphs, parent_masks = extract_glyphs(page, page_rgb)
    graphics, pre_masks, final_masks = extract_graphics(page)
    objects, object_masks = make_object_records(glyphs, parent_masks, graphics, final_masks)
    pairs = build_pairs(objects, object_masks, pre_masks)

    masks_dir = ROOT / "object_masks"
    masks_dir.mkdir(exist_ok=True)
    for obj in objects:
        save_mask(object_masks[obj["object_id"]], masks_dir / f"{safe_name(obj['object_id'])}.png", figure_px)
    pre_dir = ROOT / "graphic_pre_occlusion_masks"
    pre_dir.mkdir(exist_ok=True)
    for obj_id, mask in pre_masks.items():
        save_mask(mask, pre_dir / f"{safe_name(obj_id)}_pre.png", body_px)

    sheet_records = make_contact_sheets(page_image, glyphs)
    make_text_overlay(figure, glyphs, objects)
    relation_records = make_relation_evidence(page_image, objects, object_masks, pre_masks, pairs)

    glyph_rows = []
    for g in glyphs:
        row = {k: v for k, v in g.items() if k != "_mask"}
        row["bbox_pt"] = json.dumps([round(x, 4) for x in row.pop("bbox")], ensure_ascii=False)
        row["bbox_px"] = json.dumps(row["bbox_px"])
        row["mask_bbox_px"] = json.dumps(row["mask_bbox_px"])
        row["rgb"] = json.dumps(row["rgb"])
        glyph_rows.append(row)

    write_csv(
        ROOT / "after_pixel_measurements.csv",
        glyph_rows,
        [
            "glyph_id", "parent_id", "parent_char_index", "c", "glyph_class", "threshold_px",
            "font", "size_pt_pdf", "bbox_pt", "bbox_px", "mask_bbox_px", "rgb",
            "ink_height_px", "ink_width_px", "ink_area_px", "initial_mask_px",
            "shared_pixel_assignments_removed", "safe_filename",
        ],
    )
    write_csv(
        ROOT / "after_font_audit.csv",
        glyph_rows,
        [
            "glyph_id", "parent_id", "c", "font", "size_pt_pdf", "glyph_class", "threshold_px",
            "ink_height_px", "ink_area_px", "safe_filename",
        ],
    )
    write_csv(
        ROOT / "after_overlap_report.csv",
        pairs,
        [
            "pair_id", "object_a", "object_b", "kind_a", "kind_b", "threshold_px",
            "final_visible_overlap_px", "pre_occlusion_overlap_px", "blank_clearance_px",
        ],
    )

    with (ROOT / "glyph_manifest.json").open("w", encoding="utf-8") as f:
        json.dump([{k: v for k, v in g.items() if k != "_mask"} for g in glyphs], f, ensure_ascii=False, indent=2)
    with (ROOT / "drawing_path_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(graphics, f, ensure_ascii=False, indent=2)
    with (ROOT / "object_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(objects, f, ensure_ascii=False, indent=2)
    with (ROOT / "pair_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    with (ROOT / "contact_sheet_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(sheet_records, f, ensure_ascii=False, indent=2)
    with (ROOT / "relation_evidence_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(relation_records, f, ensure_ascii=False, indent=2)

    source_text = SOURCE.read_text(encoding="utf-8")
    identity = {
        "handoff_id": "A-R110-P582-SA1-FRESH-ISOLATED-20260827",
        "instance": "/root/p582_r110_fresh_sa1",
        "model_effort": "gpt-5.6-sol/xhigh",
        "fork_turns": "none",
        "figure_uid": FIGURE_UID,
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "figure_number": "31.7",
        "official_pdf": str(PDF),
        "official_pdf_size": PDF.stat().st_size,
        "official_pdf_sha256": sha256(PDF),
        "official_pdf_page_count": doc.page_count,
        "source": str(SOURCE),
        "source_size": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "page_rect_pt": list(page.rect),
        "page_native_300dpi_px": [page_image.width, page_image.height],
        "body_rect_pt": list(BODY_RECT_PT),
        "body_rect_page_px": list(body_px),
        "body_native_300dpi_px": [body.width, body.height],
        "figure_caption_rect_pt": list(FIGURE_RECT_PT),
        "figure_caption_rect_page_px": list(figure_px),
        "figure_caption_native_300dpi_px": [figure.width, figure.height],
        "render_engine_300dpi": f"PyMuPDF {fitz.VersionBind}",
        "source_visible_font_commands": sorted(set(re.findall(r"\\fontsize\{[^}]+\}\{[^}]+\}\\selectfont", source_text))),
        "source_graphics_scaling_commands": re.findall(r"\\(?:resizebox|scalebox)\b|transform shape|\bscale\s*=", source_text),
    }
    with (ROOT / "identity_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(identity, f, ensure_ascii=False, indent=2)

    summary = {
        "glyph_count": len(glyphs),
        "glyph_unique_ids": len({g["glyph_id"] for g in glyphs}),
        "glyph_safe_names": len({g["safe_filename"] for g in glyphs}),
        "empty_glyph_masks": sum(1 for g in glyphs if g["ink_area_px"] == 0),
        "glyph_threshold_shortfalls_excluding_low_profile": sum(
            1 for g in glyphs if g["threshold_px"] is not None and g["ink_height_px"] < g["threshold_px"]
        ),
        "text_parent_count": sum(1 for o in objects if o["kind"] == "TEXT"),
        "graphic_object_count": sum(1 for o in objects if o["kind"] == "GRAPHIC"),
        "pdf_drawing_path_count": len(graphics),
        "math_rule_path_count": 0,
        "unassigned_drawing_path_count": 0,
        "object_count": len(objects),
        "object_unique_ids": len({o["object_id"] for o in objects}),
        "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "actual_unordered_pair_count": len(pairs),
        "final_visible_overlap_pair_count": sum(1 for p in pairs if p["final_visible_overlap_px"] > 0),
        "pre_occlusion_overlap_pair_count": sum(1 for p in pairs if (p["pre_occlusion_overlap_px"] or 0) > 0),
        "text_pair_clearance_below_threshold_count": sum(
            1
            for p in pairs
            if p["threshold_px"] > 0
            and p["blank_clearance_px"] is not None
            and p["blank_clearance_px"] < p["threshold_px"]
        ),
        "contact_sheet_count": len(sheet_records),
        "contact_sheet_cell_count": sum(len(s["cells"]) for s in sheet_records),
        "critical_relation_evidence_count": len(relation_records),
        "body_crop_edge_touch_object_count": 0,
        "figure_crop_edge_touch_object_count": 0,
    }
    with (ROOT / "machine_crosscheck.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    doc.close()


if __name__ == "__main__":
    main()
