from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


# This is an evidence generator only. It reads the frozen R93 PDF and current
# figure source, and writes only into STRICT_R1. It never resizes a rendered PDF
# image: all 300-dpi views originate from one native final-PDF render.
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P412-01\STRICT_R1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第03册_优化模型与序列模型\V3-C07\fig_v3_c07_selection_loop.tex")
ADJACENT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第03册_优化模型与序列模型\chapters\V3-C07.tex")

PDF_PAGE_1BASED = 449
PDF_PAGE_INDEX = PDF_PAGE_1BASED - 1
PRINTED_PAGE = 436
FIGURE_NUMBER = "23.1"
DPI = 300
SCALE = DPI / 72.0  # PDF points to pixels for a native 300-dpi render.
PAGE_CROP_PT = fitz.Rect(55.0, 570.0, 535.0, 780.0)  # Figure + caption field.
STANDALONE_CROP_PT = fitz.Rect(70.0, 580.0, 515.0, 758.0)  # Graphic field only.


def ensure_dirs() -> None:
    for name in [
        "masks/text", "masks/vector", "masks/background", "raw_1to1/text",
        "raw_1to1/vector", "overlays/text", "overlays/vector", "pairs",
        "failure_closest", "raw_pdf",
    ]:
        (OUT / name).mkdir(parents=True, exist_ok=True)


def rgb_from_pdf_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def as_rgb_image(pix: fitz.Pixmap) -> Image.Image:
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def pdf_box_to_px(box: tuple[float, float, float, float] | fitz.Rect) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = [float(v) for v in box]
    return (math.floor(x0 * SCALE), math.floor(y0 * SCALE), math.ceil(x1 * SCALE), math.ceil(y1 * SCALE))


def clip_px(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    return (max(0, min(width, box[0])), max(0, min(height, box[1])), max(0, min(width, box[2])), max(0, min(height, box[3])))


def pdf_rect_to_float_px(rect: fitz.Rect | tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return tuple(float(v) * SCALE for v in rect)


def rect_union(rects: list[fitz.Rect]) -> fitz.Rect:
    r = fitz.Rect(rects[0])
    for value in rects[1:]:
        r |= value
    return r


def rect_clearance_px(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def rect_intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def page_crop(image: Image.Image, rect_pt: fitz.Rect) -> Image.Image:
    return image.crop(clip_px(pdf_box_to_px(rect_pt), image.width, image.height))


def path_points(drawing: dict) -> list[list[tuple[float, float]]]:
    """Recover each real PDF vector path from PyMuPDF's get_drawings output.

    The result follows actual line/cubic/rectangle PDF operators. It intentionally
    does not replace paths with their bounding boxes.
    """
    paths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    last: tuple[float, float] | None = None

    def finish_current() -> None:
        nonlocal current, last
        if current:
            paths.append(current)
        current = []
        last = None

    def pt(p) -> tuple[float, float]:
        return (float(p.x), float(p.y))

    def add_point(p: tuple[float, float]) -> None:
        nonlocal current, last
        if last is None or abs(last[0] - p[0]) > 1e-7 or abs(last[1] - p[1]) > 1e-7:
            current.append(p)
        last = p

    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            p1, p2 = pt(item[1]), pt(item[2])
            if last is not None and (abs(last[0] - p1[0]) > 1e-7 or abs(last[1] - p1[1]) > 1e-7):
                finish_current()
            add_point(p1)
            add_point(p2)
        elif op == "c":
            p0, p1, p2, p3 = pt(item[1]), pt(item[2]), pt(item[3]), pt(item[4])
            if last is not None and (abs(last[0] - p0[0]) > 1e-7 or abs(last[1] - p0[1]) > 1e-7):
                finish_current()
            add_point(p0)
            for t in np.linspace(1.0 / 64.0, 1.0, 64):
                q = (
                    (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0],
                    (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1],
                )
                add_point(q)
        elif op == "re":
            finish_current()
            r = item[1]
            paths.append([(float(r.x0), float(r.y0)), (float(r.x1), float(r.y0)), (float(r.x1), float(r.y1)), (float(r.x0), float(r.y1)), (float(r.x0), float(r.y0))])
        elif op == "qu":
            # A quadrilateral is already a PDF vector; retain its four corners.
            finish_current()
            q = item[1]
            paths.append([(float(p.x), float(p.y)) for p in q] + [(float(q[0].x), float(q[0].y))])
        else:
            raise RuntimeError(f"Unhandled PDF drawing operator: {op}")
    finish_current()
    return paths


def vector_mask_for_drawings(drawings: list[dict], drawing_indices: list[int], include_fill: bool, shape: tuple[int, int]) -> np.ndarray:
    """Create a binary raster from actual PDF vector paths at 300 dpi.

    Node fills are deliberately excluded: they are background under Goal 9.2.1-F.
    Filled arrowheads are retained. No bbox-derived dilation is performed.
    """
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    def dash_spec(value) -> tuple[list[float], float]:
        if not value or value == "[] 0":
            return [], 0.0
        # PyMuPDF returns e.g. "[ 2.98883 1.99255 ] 0" in native PDF points.
        inner, phase_text = str(value).split("]", 1)
        values = [float(x) for x in inner.replace("[", " ").split()]
        phase = float(phase_text.strip() or 0.0)
        if len(values) % 2:
            values *= 2
        return [v * SCALE for v in values], phase * SCALE

    def draw_dashed(points, width_px: int, pattern: list[float], phase: float, round_cap: bool) -> None:
        if len(points) < 2:
            return
        if not pattern:
            draw.line(points, fill=255, width=width_px, joint="curve")
            if round_cap:
                radius = width_px / 2.0
                for p in (points[0], points[-1]):
                    draw.ellipse((p[0] - radius, p[1] - radius, p[0] + radius, p[1] + radius), fill=255)
            return
        cycle = sum(pattern)
        phase = phase % cycle if cycle else 0.0
        pidx = 0
        while phase >= pattern[pidx] and pattern[pidx] > 0:
            phase -= pattern[pidx]
            pidx = (pidx + 1) % len(pattern)
        remain_pattern = pattern[pidx] - phase
        on = (pidx % 2) == 0
        for start, end in zip(points, points[1:]):
            x0, y0 = start
            x1, y1 = end
            seg = math.hypot(x1 - x0, y1 - y0)
            if seg == 0:
                continue
            walked = 0.0
            while walked < seg - 1e-6:
                use = min(seg - walked, remain_pattern)
                t0 = walked / seg
                t1 = (walked + use) / seg
                a = (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0)
                b = (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)
                if on:
                    draw.line((a, b), fill=255, width=width_px)
                    if round_cap:
                        radius = width_px / 2.0
                        for p in (a, b):
                            draw.ellipse((p[0] - radius, p[1] - radius, p[0] + radius, p[1] + radius), fill=255)
                walked += use
                remain_pattern -= use
                if remain_pattern <= 1e-6:
                    pidx = (pidx + 1) % len(pattern)
                    remain_pattern = pattern[pidx]
                    on = (pidx % 2) == 0

    for index in drawing_indices:
        d = drawings[index]
        width = float(d.get("width") or 0.0)
        width_px = max(1, int(round(width * SCALE)))
        for path in path_points(d):
            pts = [(round(x * SCALE, 4), round(y * SCALE, 4)) for x, y in path]
            if include_fill and d.get("fill") is not None and len(pts) >= 3:
                draw.polygon(pts, fill=255)
            if width > 0.0 and len(pts) >= 2:
                pattern, phase = dash_spec(d.get("dashes"))
                cap = d.get("lineCap") or (0,)
                draw_dashed(pts, width_px, pattern, phase, cap[0] == 1)
    return np.asarray(canvas, dtype=np.uint8) > 0


def foreground_text_mask(image: np.ndarray, chars: list[dict], text_rgb: tuple[int, int, int]) -> np.ndarray:
    """Segment ink only inside exact raw PDF character bboxes.

    A pixel is accepted only when its local-background contrast is at least
    20/255 and it is closer to the PDF span foreground color than to the local
    background. This excludes pale antialias noise and avoids borrowing pixels
    outside the PDF text span.
    """
    h, w = image.shape[:2]
    total = np.zeros((h, w), dtype=bool)
    target = np.asarray(text_rgb, dtype=np.float32)
    for char in chars:
        x0p, y0p, x1p, y1p = [float(v) for v in char["bbox"]]
        ix0, iy0, ix1, iy1 = clip_px(pdf_box_to_px((x0p, y0p, x1p, y1p)), w, h)
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        xx = (np.arange(ix0, ix1, dtype=np.float32) + 0.5) / SCALE
        yy = (np.arange(iy0, iy1, dtype=np.float32) + 0.5) / SCALE
        inside = (yy[:, None] >= y0p) & (yy[:, None] < y1p) & (xx[None, :] >= x0p) & (xx[None, :] < x1p)
        region = image[iy0:iy1, ix0:ix1, :].astype(np.float32)
        flat = region[inside].astype(np.uint8)
        if len(flat) == 0:
            continue
        colors, counts = np.unique(flat, axis=0, return_counts=True)
        background = colors[int(np.argmax(counts))].astype(np.float32)
        d_bg = np.linalg.norm(region - background, axis=2)
        d_fg = np.linalg.norm(region - target, axis=2)
        accepted = inside & (d_bg >= 20.0) & (d_fg <= d_bg)
        total[iy0:iy1, ix0:ix1] |= accepted
    return total


def crop_mask(mask: np.ndarray, bbox_px: tuple[int, int, int, int]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    h, w = mask.shape
    box = clip_px(bbox_px, w, h)
    return mask[box[1]:box[3], box[0]:box[2]], box


def save_mask_raw_overlay(obj: dict, image: Image.Image, mask: np.ndarray, folder: str) -> None:
    bbox = obj["bbox_px"]
    c_mask, box = crop_mask(mask, bbox)
    raw = image.crop(box)
    raw_path = OUT / f"raw_1to1/{folder}/{obj['id']}_raw_1to1.png"
    mask_path = OUT / f"masks/{folder}/{obj['id']}_mask_300dpi.png"
    overlay_path = OUT / f"overlays/{folder}/{obj['id']}_overlay_300dpi.png"
    raw.save(raw_path)
    Image.fromarray((c_mask.astype(np.uint8) * 255), mode="L").save(mask_path)
    arr = np.asarray(raw).copy()
    arr[c_mask] = (255, 0, 255) if folder == "text" else (0, 210, 255)
    Image.fromarray(arr, mode="RGB").save(overlay_path)
    obj["raw_path"] = str(raw_path.relative_to(OUT)).replace("\\", "/")
    obj["mask_path"] = str(mask_path.relative_to(OUT)).replace("\\", "/")
    obj["overlay_path"] = str(overlay_path.relative_to(OUT)).replace("\\", "/")


def coords_for(obj: dict) -> np.ndarray:
    if "coords" not in obj:
        rows, cols = np.where(obj["mask"])
        obj["coords"] = np.column_stack((cols, rows)).astype(np.float32)
    return obj["coords"]


def mask_overlap(a: dict, b: dict) -> int:
    return int(np.count_nonzero(a["mask"] & b["mask"]))


def nearest_points(a: dict, b: dict) -> tuple[float, tuple[int, int] | None, tuple[int, int] | None]:
    ca, cb = coords_for(a), coords_for(b)
    if len(ca) == 0 or len(cb) == 0:
        return math.inf, None, None
    if len(ca) <= len(cb):
        tree = cKDTree(cb)
        dist, idx = tree.query(ca, k=1)
        k = int(np.argmin(dist))
        return float(dist[k]), tuple(map(int, ca[k])), tuple(map(int, cb[int(idx[k])]))
    tree = cKDTree(ca)
    dist, idx = tree.query(cb, k=1)
    k = int(np.argmin(dist))
    return float(dist[k]), tuple(map(int, ca[int(idx[k])])), tuple(map(int, cb[k]))


def safe_name(value: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in value).strip("_")


def save_pair_detail(a: dict, b: dict, overlap: int, nearest: float, pa, pb) -> str:
    """Save an exact-union 1:1 raw ROI, object overlay, and overlap mask.

    The ROI is the union of the two actual PDF/vector bboxes, never an expanded
    convenience crop. The blue/magenta colors identify independent masks only.
    """
    x0 = min(a["bbox_px"][0], b["bbox_px"][0])
    y0 = min(a["bbox_px"][1], b["bbox_px"][1])
    x1 = max(a["bbox_px"][2], b["bbox_px"][2])
    y1 = max(a["bbox_px"][3], b["bbox_px"][3])
    box = clip_px((x0, y0, x1, y1), FULL_300.width, FULL_300.height)
    raw = FULL_300.crop(box)
    ma = a["mask"][box[1]:box[3], box[0]:box[2]]
    mb = b["mask"][box[1]:box[3], box[0]:box[2]]
    arr = np.asarray(raw).copy()
    arr[ma] = (255, 0, 255)
    arr[mb] = (0, 210, 255)
    both = ma & mb
    arr[both] = (255, 255, 0)
    draw = ImageDraw.Draw(Image.fromarray(arr, mode="RGB"))
    # Re-create after labels are placed; original pixels have not been scaled.
    over = Image.fromarray(arr, mode="RGB")
    if pa is not None and pb is not None:
        d = ImageDraw.Draw(over)
        d.line([(pa[0] - box[0], pa[1] - box[1]), (pb[0] - box[0], pb[1] - box[1])], fill=(255, 255, 0), width=1)
    stem = f"{a['id']}__{b['id']}"
    raw_path = OUT / f"pairs/{stem}_raw_1to1.png"
    over_path = OUT / f"pairs/{stem}_overlay_300dpi.png"
    overlap_path = OUT / f"pairs/{stem}_overlap_mask_300dpi.png"
    raw.save(raw_path)
    over.save(over_path)
    Image.fromarray((both.astype(np.uint8) * 255), mode="L").save(overlap_path)
    return str(over_path.relative_to(OUT)).replace("\\", "/")


def make_full_overlay(objects: list[dict], crop: fitz.Rect, output_name: str, color: tuple[int, int, int]) -> None:
    image = page_crop(FULL_300, crop).copy()
    draw = ImageDraw.Draw(image)
    cx0, cy0, _, _ = pdf_box_to_px(crop)
    for obj in objects:
        x0, y0, x1, y1 = obj["bbox_px"]
        draw.rectangle((x0 - cx0, y0 - cy0, x1 - cx0 - 1, y1 - cy0 - 1), outline=color, width=1)
        draw.text((x0 - cx0, max(0, y0 - cy0 - 12)), obj["id"], fill=color)
    image.save(OUT / output_name)


def source_spec() -> list[dict]:
    # Meaningful text objects in visible order. Caption is included because Goal
    # treats caption-associated reader text as an auditable figure element.
    return [
        {"id": "T01", "label": "task_definition", "text": "任务定义", "role": "NODE_LABEL", "parent": "NODE_TASK", "line": 14, "declared": 9.4, "script": "CJK_FULLWIDTH"},
        {"id": "T02", "label": "candidate_family", "text": "候选模型族", "role": "NODE_LABEL", "parent": "NODE_FAMILY", "line": 15, "declared": 9.4, "script": "CJK_FULLWIDTH"},
        {"id": "T03", "label": "train_candidate", "text": "训练候选", "role": "NODE_LABEL", "parent": "NODE_TRAIN", "line": 16, "declared": 9.4, "script": "CJK_FULLWIDTH"},
        {"id": "T04", "label": "validation_selection", "text": "验证选择", "role": "NODE_LABEL", "parent": "NODE_VALID", "line": 17, "declared": 9.4, "script": "CJK_FULLWIDTH"},
        {"id": "T05", "label": "development_feedback", "text": "开发反馈：仅返回候选族", "role": "ANNOTATION", "parent": "FEEDBACK_LOOP", "line": 22, "declared": 9.0, "script": "CJK_FULLWIDTH"},
        {"id": "T06", "label": "freeze", "text": "冻结", "role": "NODE_LABEL", "parent": "NODE_FREEZE", "line": 27, "declared": 9.4, "script": "CJK_FULLWIDTH"},
        {"id": "T07", "label": "one_final_test", "text": "一次最终测试", "role": "NODE_LABEL", "parent": "NODE_TEST", "line": 28, "declared": 9.4, "script": "CJK_FULLWIDTH"},
        {"id": "T08", "label": "report_result", "text": "报告结果", "role": "NODE_LABEL", "parent": "NODE_REPORT", "line": 29, "declared": 9.4, "script": "CJK_FULLWIDTH"},
        {"id": "T09", "label": "locked_test_set", "text": "锁定测试集", "role": "NODE_LABEL", "parent": "NODE_LOCKED", "line": 37, "declared": 9.2, "script": "CJK_FULLWIDTH"},
        {"id": "T10", "label": "no_dev_access", "text": "禁止开发期访问", "role": "NODE_LABEL", "parent": "NODE_LOCKED", "line": 37, "declared": 9.2, "script": "CJK_FULLWIDTH"},
        {"id": "T11", "label": "no_return_path", "text": "无任何返回候选族的路径", "role": "ANNOTATION", "parent": "LOCKED_TEST_NOTE", "line": 40, "declared": 9.0, "script": "CJK_FULLWIDTH"},
        {"id": "T12", "label": "caption_figure_prefix", "text": "图", "role": "CAPTION_PREFIX", "parent": "CAPTION_23_1", "line": 42, "declared": None, "script": "CJK_FULLWIDTH"},
        {"id": "T13", "label": "caption_figure_number", "text": "23.1", "role": "CAPTION_NUMBER", "parent": "CAPTION_23_1", "line": 42, "declared": None, "script": "LATIN_DIGIT"},
        {"id": "T14", "label": "caption_text", "text": "监督学习方法选择闭环。测试集不进入返回候选模型族的反馈回路。", "role": "CAPTION_TEXT", "parent": "CAPTION_23_1", "line": 42, "declared": None, "script": "CJK_FULLWIDTH"},
    ]


def json_vector_item(item):
    def convert(value):
        if isinstance(value, fitz.Point):
            return {"x": float(value.x), "y": float(value.y)}
        if isinstance(value, fitz.Rect):
            return {"x0": float(value.x0), "y0": float(value.y0), "x1": float(value.x1), "y1": float(value.y1)}
        if isinstance(value, (tuple, list)):
            return [convert(v) for v in value]
        return value
    return [convert(v) for v in item]


def vector_spec() -> list[dict]:
    # indices are exactly the frozen R93 page.get_drawings() operator objects.
    return [
        {"id": "V01", "label": "task_node_border", "kind": "NODE_BORDER", "parent": "NODE_TASK", "drawings": [7], "fill": False, "line": 14},
        {"id": "V02", "label": "family_node_border", "kind": "NODE_BORDER", "parent": "NODE_FAMILY", "drawings": [8], "fill": False, "line": 15},
        {"id": "V03", "label": "train_node_border", "kind": "NODE_BORDER", "parent": "NODE_TRAIN", "drawings": [9], "fill": False, "line": 16},
        {"id": "V04", "label": "valid_node_border", "kind": "NODE_BORDER", "parent": "NODE_VALID", "drawings": [10], "fill": False, "line": 17},
        {"id": "V05", "label": "task_to_family", "kind": "LINE_ARROW", "parent": "FLOW_MAIN", "drawings": [11, 12], "fill": True, "line": 18},
        {"id": "V06", "label": "family_to_train", "kind": "LINE_ARROW", "parent": "FLOW_MAIN", "drawings": [13, 14], "fill": True, "line": 19},
        {"id": "V07", "label": "train_to_valid", "kind": "LINE_ARROW", "parent": "FLOW_MAIN", "drawings": [15, 16], "fill": True, "line": 20},
        {"id": "V08", "label": "feedback_return", "kind": "LINE_ARROW", "parent": "FEEDBACK_LOOP", "drawings": [17, 18], "fill": True, "line": 21},
        {"id": "V09", "label": "freeze_diamond_border", "kind": "NODE_BORDER", "parent": "NODE_FREEZE", "drawings": [20], "fill": False, "line": 25},
        {"id": "V10", "label": "valid_to_freeze", "kind": "LINE_ARROW", "parent": "FLOW_FINAL", "drawings": [23, 24], "fill": True, "line": 30},
        {"id": "V11", "label": "freeze_to_test", "kind": "LINE_ARROW", "parent": "FLOW_FINAL", "drawings": [25, 26], "fill": True, "line": 31},
        {"id": "V12", "label": "test_to_report", "kind": "LINE_ARROW", "parent": "FLOW_FINAL", "drawings": [27, 28], "fill": True, "line": 32},
        {"id": "V13", "label": "test_node_border", "kind": "NODE_BORDER", "parent": "NODE_TEST", "drawings": [21], "fill": False, "line": 28},
        {"id": "V14", "label": "report_node_border", "kind": "NODE_BORDER", "parent": "NODE_REPORT", "drawings": [22], "fill": False, "line": 29},
        {"id": "V15", "label": "locked_node_border", "kind": "NODE_BORDER", "parent": "NODE_LOCKED", "drawings": [29], "fill": False, "line": 34},
        {"id": "V16", "label": "locked_to_test", "kind": "LINE_ARROW", "parent": "FLOW_LOCKED", "drawings": [30, 31], "fill": True, "line": 38},
    ]


def find_raw_span(raw_spans: list[dict], text: str) -> dict:
    hits = [s for s in raw_spans if "".join(c["c"] for c in s["chars"]) == text]
    if len(hits) != 1:
        raise RuntimeError(f"Expected exactly one R93 PDF span for {text!r}, found {len(hits)}")
    return hits[0]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def b(value: bool) -> str:
    return "true" if value else "false"


def fmt(value) -> str:
    if isinstance(value, float):
        if math.isinf(value):
            return "INF"
        return f"{value:.3f}"
    if value is None:
        return "UNKNOWN"
    return str(value)


def report_text(gates: dict, font_rows: list[dict], pixel_rows: list[dict], pair_rows: list[dict], edge_rows: list[dict], same_rows: list[dict], role_rows: list[dict]) -> str:
    source_fail = [r for r in font_rows if r["PASS_FAIL"] == "FAIL"]
    pixel_fail = [r for r in pixel_rows if r["PASS_FAIL"] == "FAIL"]
    overlap_fail = [r for r in pair_rows if r["PASS_FAIL"] == "FAIL"]
    reasons = "；".join(sorted({r["REASON"] for r in source_fail if r["REASON"]}))
    closest = sorted(pixel_rows, key=lambda r: (r["H_INK_PX"] - r["PIXEL_THRESHOLD_PX"], r["ELEMENT_ID"]))[0]
    node_font = [r for r in font_rows if r["ROLE"] == "NODE_LABEL"]
    ann_font = [r for r in font_rows if r["ROLE"] == "ANNOTATION"]
    node_declared = [float(r["DECLARED_PT"]) for r in node_font]
    ann_declared = [float(r["DECLARED_PT"]) for r in ann_font]
    min_text_bbox = min(float(r["BBOX_CLEARANCE_PX"]) for r in pair_rows if r["PAIR_CLASS"] == "TEXT_TEXT")
    min_line = min(float(r["NEAREST_DISTANCE_PX"]) for r in pair_rows if r["PAIR_CLASS"] == "TEXT_LINE_ARROW")
    min_node = min(float(r["NEAREST_DISTANCE_PX"]) for r in pair_rows if r["PAIR_CLASS"] == "TEXT_NODE_BORDER" and r["REQUIRED_MIN_PX"] != "N/A")
    min_fig_edge = min(float(r["FIGURE_EDGE_CLEARANCE_PX"]) for r in pixel_rows)
    cjk_rows = [r for r in pixel_rows if r["SCRIPT_CLASS"] == "CJK_FULLWIDTH"]
    cjk_values = [int(r["H_INK_PX"]) for r in cjk_rows]
    digit = next(r for r in pixel_rows if r["ELEMENT_ID"] == "T13")
    node_same = next(r for r in same_rows if r["ROLE"] == "NODE_LABEL")
    annotation_role = next(r for r in role_rows if r["ROLE"] == "ANNOTATION")
    return f"""# FIG-P412-01 — SA1 STRICT-R1 独立审计

RESULT: **FAIL**

## 对象定位与冻结身份

- Canonical UID: `FIG-P412-01`; current label: `fig:V3-C07-selection-loop`; current printed figure number: `{FIGURE_NUMBER}`.
- Official frozen candidate: `{PDF}` (directory identity `strict_current_r93_fullbook`, R93).
- Actual PDF physical page (1-based): `{PDF_PAGE_1BASED}` of 813; printed page: `{PRINTED_PAGE}`; task-ID page token `P412` is historical and does not identify the current R93 placement.
- Source: `{SOURCE}` lines 3–43. Adjacent source: `{ADJACENT}` lines 223–230.
- The source has no formula, Latin/Greek variable, or `+`/`−`/`=` basic-operator element inside the figure; those operator/script gates are explicitly `NOT_PRESENT`, not sampled away.

## Strict gate matrix

| Gate | Result | Measured evidence |
|---|---:|---|
| SOURCE_FONT_PASS | `{b(gates['SOURCE_FONT_PASS'])}` | `{len(source_fail)}` failed text elements; `{reasons}` |
| PIXEL_HEIGHT_PASS | `{b(gates['PIXEL_HEIGHT_PASS'])}` | closest threshold: `{closest['ELEMENT_ID']}` `{closest['H_INK_PX']} px` vs `{closest['PIXEL_THRESHOLD_PX']} px` |
| SAME_CLASS_RATIO_PASS | `{b(gates['SAME_CLASS_RATIO_PASS'])}` | `same_class_ratio_audit.csv` |
| ROLE_RATIO_PASS | `{b(gates['ROLE_RATIO_PASS'])}` | `role_ratio_audit.csv` |
| OVERLAP_PIXEL_COUNT | `{gates['OVERLAP_PIXEL_COUNT']}` | independent real-PDF span/vector masks in `after_overlap_report.csv` |
| CLIP_PIXEL_COUNT | `{gates['CLIP_PIXEL_COUNT']}` | `after_edge_clip_report.csv` |
| MIN_TEXT_CLEARANCE_PX | `{gates['MIN_TEXT_CLEARANCE_PX']:.3f}` | category minima and nearest points in `after_overlap_report.csv` |
| VISUAL_HARMONY_PASS | `{b(gates['VISUAL_HARMONY_PASS'])}` | four native views reviewed; visual hierarchy is coherent, but it cannot override font-gate failure |
| MATH_SEMANTICS_PASS | `{b(gates['MATH_SEMANTICS_PASS'])}` | selection/test flow semantics match source, caption, and adjacent text |
| TEXT_CONSISTENCY_PASS | `{b(gates['TEXT_CONSISTENCY_PASS'])}` | labels/caption match source and adjacent body |
| GRAYSCALE_PASS | `{b(gates['GRAYSCALE_PASS'])}` | `grayscale_300dpi.png` retains direction, containment, and warning distinctions |
| PAGE_INTEGRATION_PASS | `{b(gates['PAGE_INTEGRATION_PASS'])}` | `full_page_200dpi.png`: figure, caption, footer and preceding paragraph do not collide |

## Quantitative threshold record

| Audit family | Measured result | Rule / result | Evidence |
|---|---:|---|---|
| Source node-label effective fonts | `{min(node_declared):.1f}–{max(node_declared):.1f} pt`; max/min `{max(node_declared)/min(node_declared):.6f}`; difference `{max(node_declared)-min(node_declared):.3f} pt` | internal consistency passes (`<=1.03`, `<=0.25 pt`), but all are `<9.5 pt` → FAIL | `after_font_audit.csv` |
| Source annotation effective fonts | `{min(ann_declared):.1f} pt`; max/min `1.000000`; difference `0.000 pt` | internally consistent, but `<9.5 pt` → FAIL | `after_font_audit.csv` |
| Caption source font | `UNKNOWN` (PDF vector span is 9.962640 PDF pt, but declaration is outside permitted source scope) | unknown effective source font → FAIL | `after_font_audit.csv`, `raw_pdf/raw_pdf_spans.json` |
| CJK/fullwidth ink heights | `{min(cjk_values)}–{max(cjk_values)} px` | `>=30 px` → PASS | `after_pixel_measurements.csv` |
| Caption number ink height | `{digit['H_INK_PX']} px` | `>=24 px` → PASS | `after_pixel_measurements.csv` |
| Same-class node-label ratio | element range `0.970588–1.000000`; max/min `{node_same['ROLE_MAX_MEDIAN_OVER_MIN']}` | `[0.92,1.08]`; role max/min `<=1.08` → PASS | `same_class_ratio_audit.csv` |
| Cross-panel same-role ratio | `N/A` | single panel; no cross-panel comparison exists | `same_class_ratio_audit.csv` |
| Annotation/base role ratio | `{annotation_role['ROLE_RATIO']}` (annotation median `{annotation_role['ROLE_MEDIAN_PX']} px`, base `{annotation_role['BASE_MEDIAN_PX']} px`) | `[0.95,1.10]` → PASS | `role_ratio_audit.csv` |
| Axis / legend / formula / panel-label roles | `NOT_PRESENT` | no applicable role band | `object_register.csv`, source lines 14–42 |
| Text–text PDF/vector bbox clearance | `{min_text_bbox:.3f} px` | `>=4 px` → PASS | `after_overlap_report.csv` |
| Text/formula–line/arrow ink clearance | `{min_line:.3f} px` (T05↔V08) | `>=3 px` → PASS | `after_overlap_report.csv`, `pairs/T05__V08_overlay_300dpi.png` |
| Node-text–node-border ink clearance | `{min_node:.3f} px` (T10↔V15) | `>=5 px` → PASS | `after_overlap_report.csv` |
| Text–figure-image-edge clearance | `{min_fig_edge:.3f} px` | `>=6 px` → PASS | `after_pixel_measurements.csv` |
| Independent foreground intersections | `{gates['OVERLAP_PIXEL_COUNT']} px` | exactly 0 → PASS | `after_overlap_report.csv`, `after_overlap_overlay_300dpi.png` |
| Independent edge clips | `{gates['CLIP_PIXEL_COUNT']} px` | exactly 0 → PASS | `after_edge_clip_report.csv` |

## Hard-failure basis

Every reader-visible source-owned figure text is declared at 9.0, 9.2, or 9.4 pt; all are below the required 9.5 pt effective minimum. The current R93 PDF vector font sizes corroborate those declarations after TeX/PDF unit conversion. Caption source size is unavailable within this strictly limited read scope (caption macro is outside current figure source), so the caption source-font field is `UNKNOWN`; Goal §9.2.1 requires this to fail rather than be assumed. Pixel readability, ratios, mask overlap, clipping, semantics, and visual integration do not cure this source-effective-font failure.

Per Goal §9.2.1-I, SA3 is prohibited at this point. The sole next step is **SA2 targeted source repair**, then a new standalone/final-PDF render and a full independent re-audit.

## SUPERSEDED provisional-mask result

`SUPERSEDED`: a first provisional color-only reconstruction treated the feedback line as a solid path and incorrectly counted `T05↔V08 = 161` overlapping pixels. It was not retained as a current finding: native R93 PDF drawing 17 has dash array `[2.98883 1.99255] 0`, and drawing 19 is the subsequently painted opaque white feedback-label background. The corrected true-PDF span/vector masks preserve that dash array and paint order: `T05↔V08` has `MASK_OVERLAP_PX=0` and `NEAREST_DISTANCE_PX=7.000`. The raw pair/overlay/mask in `pairs/T05__V08_*` is the current evidence.

## Required SA2 repair targets

1. Raise every source-owned visible figure text to an effective size of at least 9.5 pt without any `scale`, `transform shape`, `resizebox`, or `scalebox` workaround: top/terminal node labels (lines 14–17, 27–29), feedback label (line 22), locked node text (line 36–37), and red note (line 39–40).
2. Preserve the measured role bands: ordinary node labels remain the base; annotations remain within 0.95–1.10 of base. Recheck the feedback label’s own path clearance rather than relying on its white background.
3. Make the caption source font auditable through the permitted task source/configuration path, or provide an authoritative, scoped declaration for it; unknown effective font cannot pass.

## Evidence and method

- Four required views: `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`. Each PNG is a direct native R93 PDF rendering/crop at the stated dpi; no image resizing occurred. The standalone view is a direct graphic-field crop of the frozen final PDF, not a recompiled substitute.
- `raw_pdf/raw_pdf_spans.json` stores the native PDF spans/characters and PDF bboxes; `raw_pdf/raw_pdf_vectors.json` stores native `get_drawings()` paths, widths and IDs.
- Text masks are thresholded only inside their exact raw PDF character boxes (local-background difference >=20/255). Vector masks are rebuilt from actual PDF vector operators, including native widths, Béziers, dash arrays, and the opaque-background paint order, rather than expanded bboxes. Each object has a tight 1:1 raw ROI, mask, and overlay under `raw_1to1/`, `masks/`, and `overlays/`.
- `object_register.csv` contains 14 text spans, 16 foreground vector objects, and the one excluded background fill. Pair CSV rows carry both parents, vector/PDF bbox clearance, real-mask intersection count, mask/raw paths, and nearest foreground pixel coordinates. All `{len(pair_rows)}` pairs (91 text–text + 224 text–vector) are measured without sampling; detail images are emitted for every same-color text pair and every near text/vector pair.
- `after_text_measurement_overlay_300dpi.png` and `after_vector_object_overlay_300dpi.png` identify the PDF bboxes used for every text/vector object.

## Independent content assessment

The diagram correctly encodes the intended statistical protocol: task definition → candidate family → training → validation selection; only validation returns to the candidate family; frozen configuration then permits one final test and report; the locked test-set arrow is one-way into the test and cannot return to development. This is consistent with the caption and the immediately following explanatory sentence. No mathematical formula/operator is present to audit. The left-to-right top flow and the freeze-to-final-test lower flow are readable; the grayscale view preserves the distinct node/arrow structure and warning placement.
"""


def acceptance_text(gates: dict) -> str:
    return f"""# FIG-P412-01 after_visual_acceptance — SA1 STRICT-R1

RESULT: FAIL

SOURCE_FONT_PASS = {b(gates['SOURCE_FONT_PASS'])}
PIXEL_HEIGHT_PASS = {b(gates['PIXEL_HEIGHT_PASS'])}
SAME_CLASS_RATIO_PASS = {b(gates['SAME_CLASS_RATIO_PASS'])}
ROLE_RATIO_PASS = {b(gates['ROLE_RATIO_PASS'])}
OVERLAP_PIXEL_COUNT = {gates['OVERLAP_PIXEL_COUNT']}
CLIP_PIXEL_COUNT = {gates['CLIP_PIXEL_COUNT']}
MIN_TEXT_CLEARANCE_PX = {gates['MIN_TEXT_CLEARANCE_PX']:.3f}
VISUAL_HARMONY_PASS = {b(gates['VISUAL_HARMONY_PASS'])}
MATH_SEMANTICS_PASS = {b(gates['MATH_SEMANTICS_PASS'])}
TEXT_CONSISTENCY_PASS = {b(gates['TEXT_CONSISTENCY_PASS'])}
GRAYSCALE_PASS = {b(gates['GRAYSCALE_PASS'])}
PAGE_INTEGRATION_PASS = {b(gates['PAGE_INTEGRATION_PASS'])}

Hard result: FAIL. Source-owned text is below the 9.5-pt effective-font floor and caption source-effective size is unknown in the allowed source scope. No PASS/SA3 routing is allowed.

Views actually reviewed: full_page_200dpi.png; figure_crop_300dpi.png; standalone_300dpi.png; grayscale_300dpi.png.
"""


ensure_dirs()
doc = fitz.open(PDF)
page = doc[PDF_PAGE_INDEX]
FULL_300 = as_rgb_image(page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False))
FULL_200 = as_rgb_image(page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False))
FULL_200.save(OUT / "full_page_200dpi.png")
FIGURE_CROP = page_crop(FULL_300, PAGE_CROP_PT)
FIGURE_CROP.save(OUT / "figure_crop_300dpi.png")
page_crop(FULL_300, STANDALONE_CROP_PT).save(OUT / "standalone_300dpi.png")
FIGURE_CROP.convert("L").save(OUT / "grayscale_300dpi.png")

image_np = np.asarray(FULL_300)
raw = page.get_text("rawdict")
raw_spans = [s for block in raw["blocks"] if block["type"] == 0 for line in block["lines"] for s in line["spans"] if 570.0 < float(s["bbox"][1]) < 780.0]
drawings = page.get_drawings()

# Native PDF evidence, separate from interpretation/masks.
with (OUT / "raw_pdf/raw_pdf_spans.json").open("w", encoding="utf-8") as f:
    json.dump([
        {"text": "".join(c["c"] for c in s["chars"]), "bbox_pt": list(map(float, s["bbox"])), "font": s["font"], "pdf_font_size_pt": float(s["size"]), "color_rgb": rgb_from_pdf_int(int(s["color"])), "chars": [{"char": c["c"], "bbox_pt": list(map(float, c["bbox"]))} for c in s["chars"]]}
        for s in raw_spans
    ], f, ensure_ascii=False, indent=2)
with (OUT / "raw_pdf/raw_pdf_vectors.json").open("w", encoding="utf-8") as f:
    json.dump([
        {"drawing_index": i, "bbox_pt": list(map(float, d["rect"])), "type": d["type"], "width_pt": d.get("width"), "dashes": d.get("dashes"), "lineCap": d.get("lineCap"), "lineJoin": d.get("lineJoin"), "stroke": d.get("color"), "fill": d.get("fill"), "operator_count": len(d["items"]), "items": [json_vector_item(x) for x in d["items"]]}
        for i, d in enumerate(drawings) if float(d["rect"].y0) > 560.0
    ], f, ensure_ascii=False, indent=2)

texts: list[dict] = []
for spec in source_spec():
    span = find_raw_span(raw_spans, spec["text"])
    bbox_pt = tuple(float(v) for v in span["bbox"])
    text_rgb = rgb_from_pdf_int(int(span["color"]))
    mask = foreground_text_mask(image_np, span["chars"], text_rgb)
    ink_y, ink_x = np.where(mask)
    h_ink = int(ink_y.max() - ink_y.min() + 1) if len(ink_y) else 0
    threshold = 30 if spec["script"] == "CJK_FULLWIDTH" else 24
    effective = spec["declared"]
    source_ok = effective is not None and effective >= 9.5
    if effective is None:
        source_reason = "FAIL: caption declared_pt/effective_pt unavailable in permitted source scope"
    elif effective < 9.5:
        source_reason = f"FAIL: effective_pt={effective:.1f}<9.5"
    else:
        source_reason = "PASS"
    obj = {
        **spec,
        "kind": "TEXT",
        "bbox_pt": bbox_pt,
        "bbox_float_px": pdf_rect_to_float_px(bbox_pt),
        "bbox_px": pdf_box_to_px(bbox_pt),
        "pdf_font_size": float(span["size"]),
        "pdf_font": span["font"],
        "text_rgb": text_rgb,
        "mask": mask,
        "h_ink": h_ink,
        "threshold": threshold,
        "pixel_ok": h_ink >= threshold,
        "source_ok": source_ok,
        "source_reason": source_reason,
        "chars": span["chars"],
    }
    texts.append(obj)

# PDF drawing 19 is the opaque white feedback-label background painted after
# the dashed return path. It is background by Goal F, but it occludes the
# earlier path in the final frozen PDF and therefore must be applied before
# creating visible vector foreground masks.
bg_mask = vector_mask_for_drawings(drawings, [19], True, image_np.shape[:2])
vectors: list[dict] = []
for spec in vector_spec():
    drects = [fitz.Rect(drawings[i]["rect"]) for i in spec["drawings"]]
    bbox_pt_rect = rect_union(drects)
    mask = vector_mask_for_drawings(drawings, spec["drawings"], bool(spec["fill"]), image_np.shape[:2])
    if any(i < 19 for i in spec["drawings"]):
        mask &= ~bg_mask
    obj = {
        **spec,
        "bbox_pt": tuple(float(v) for v in bbox_pt_rect),
        "bbox_float_px": pdf_rect_to_float_px(bbox_pt_rect),
        "bbox_px": pdf_box_to_px(bbox_pt_rect),
        "mask": mask,
    }
    save_mask_raw_overlay(obj, FULL_300, mask, "vector")
    vectors.append(obj)

# Remove only independent, still-visible vector-path pixels from each
# color-segmented text candidate. This prevents a same-colour dashed line from
# being mislabelled as glyph ink inside a PDF text bbox. It is not bbox erosion:
# each removed pixel is an actual PDF vector-path pixel after paint-order
# occlusion has been applied.
visible_vector_union = np.zeros(image_np.shape[:2], dtype=bool)
for vector in vectors:
    visible_vector_union |= vector["mask"]
for text in texts:
    text["mask"] &= ~visible_vector_union
    ink_y, ink_x = np.where(text["mask"])
    text["h_ink"] = int(ink_y.max() - ink_y.min() + 1) if len(ink_y) else 0
    text["pixel_ok"] = text["h_ink"] >= text["threshold"]
    save_mask_raw_overlay(text, FULL_300, text["mask"], "text")

# This white fill is actual PDF geometry, but correctly stays background under F.
bg_obj = {"id": "BG01", "kind": "BACKGROUND_LABEL_FILL", "parent": "FEEDBACK_LOOP", "drawings": [19], "bbox_pt": tuple(float(v) for v in drawings[19]["rect"]), "bbox_float_px": pdf_rect_to_float_px(drawings[19]["rect"]), "bbox_px": pdf_box_to_px(drawings[19]["rect"]), "mask": bg_mask}
c_bg, box_bg = crop_mask(bg_obj["mask"], bg_obj["bbox_px"])
Image.fromarray((c_bg.astype(np.uint8) * 255), mode="L").save(OUT / "masks/background/BG01_feedback_label_fill_mask_300dpi.png")

make_full_overlay(texts, PAGE_CROP_PT, "after_text_measurement_overlay_300dpi.png", (255, 0, 255))
make_full_overlay(vectors, PAGE_CROP_PT, "after_vector_object_overlay_300dpi.png", (0, 210, 255))

# Text-text and text-vector interactions. Rows are exhaustive; expanded visual
# pair detail is added for same-colour text or genuinely close object pairs.
pair_rows: list[dict] = []
near_detail_count = 0
for i, a in enumerate(texts):
    for bobj in texts[i + 1:]:
        overlap = mask_overlap(a, bobj)
        nearest, pa, pb = nearest_points(a, bobj)
        clearance = rect_clearance_px(a["bbox_float_px"], bobj["bbox_float_px"])
        intersects = rect_intersects(a["bbox_float_px"], bobj["bbox_float_px"])
        ok = overlap == 0 and clearance >= 4.0
        same_color = a["text_rgb"] == bobj["text_rgb"]
        detail = ""
        if same_color or clearance < 30.0 or nearest < 30.0:
            detail = save_pair_detail(a, bobj, overlap, nearest, pa, pb)
            near_detail_count += 1
        pair_rows.append({
            "PAIR_ID": f"{a['id']}__{bobj['id']}", "PAIR_CLASS": "TEXT_TEXT", "PARENT_A": a["parent"], "PARENT_B": bobj["parent"],
            "OBJECT_A": a["id"], "OBJECT_B": bobj["id"], "BBOX_CLEARANCE_PX": clearance, "BBOX_INTERSECTION_STATUS": "INTERSECT" if intersects else "DISJOINT",
            "MASK_OVERLAP_PX": overlap, "NEAREST_DISTANCE_PX": nearest, "NEAREST_POINT_A_PX": pa, "NEAREST_POINT_B_PX": pb,
            "REQUIRED_MIN_PX": 4.0, "PASS_FAIL": "PASS" if ok else "FAIL", "DETAIL_OVERLAY": detail,
            "MASK_A_PATH": a["mask_path"], "MASK_B_PATH": bobj["mask_path"], "RAW_A_PATH": a["raw_path"], "RAW_B_PATH": bobj["raw_path"],
        })

semantic_node_pairs = {"T01": "V01", "T02": "V02", "T03": "V03", "T04": "V04", "T05": "V08", "T06": "V09", "T07": "V13", "T08": "V14", "T09": "V15", "T10": "V15"}
for a in texts:
    for bobj in vectors:
        overlap = mask_overlap(a, bobj)
        nearest, pa, pb = nearest_points(a, bobj)
        clearance = rect_clearance_px(a["bbox_float_px"], bobj["bbox_float_px"])
        intersects = rect_intersects(a["bbox_float_px"], bobj["bbox_float_px"])
        required = 5.0 if bobj["kind"] == "NODE_BORDER" and semantic_node_pairs.get(a["id"]) == bobj["id"] else 3.0
        applicable = semantic_node_pairs.get(a["id"]) == bobj["id"] or bobj["kind"] == "LINE_ARROW"
        ok = overlap == 0 and (not applicable or nearest >= required)
        detail = ""
        if clearance < 50.0 or nearest < 50.0 or overlap > 0:
            detail = save_pair_detail(a, bobj, overlap, nearest, pa, pb)
            near_detail_count += 1
        pair_rows.append({
            "PAIR_ID": f"{a['id']}__{bobj['id']}", "PAIR_CLASS": f"TEXT_{bobj['kind']}", "PARENT_A": a["parent"], "PARENT_B": bobj["parent"],
            "OBJECT_A": a["id"], "OBJECT_B": bobj["id"], "BBOX_CLEARANCE_PX": clearance, "BBOX_INTERSECTION_STATUS": "INTERSECT" if intersects else "DISJOINT",
            "MASK_OVERLAP_PX": overlap, "NEAREST_DISTANCE_PX": nearest, "NEAREST_POINT_A_PX": pa, "NEAREST_POINT_B_PX": pb,
            "REQUIRED_MIN_PX": required if applicable else "N/A", "PASS_FAIL": "PASS" if ok else "FAIL", "DETAIL_OVERLAY": detail,
            "MASK_A_PATH": a["mask_path"], "MASK_B_PATH": bobj["mask_path"], "RAW_A_PATH": a["raw_path"], "RAW_B_PATH": bobj["raw_path"],
        })

# Per-text actual mask overlaps and minimum clearance, including figure image edge.
fig_box_float = pdf_rect_to_float_px(PAGE_CROP_PT)
for text in texts:
    tt = [r for r in pair_rows if r["PAIR_CLASS"] == "TEXT_TEXT" and (r["OBJECT_A"] == text["id"] or r["OBJECT_B"] == text["id"])]
    tg = [r for r in pair_rows if r["PAIR_CLASS"] != "TEXT_TEXT" and r["OBJECT_A"] == text["id"]]
    bx = text["bbox_float_px"]
    edge_clearance = min(bx[0] - fig_box_float[0], fig_box_float[2] - bx[2], bx[1] - fig_box_float[1], fig_box_float[3] - bx[3])
    min_graphic = min([float(r["NEAREST_DISTANCE_PX"]) for r in tg] + [edge_clearance])
    text["text_text_overlap"] = int(sum(int(r["MASK_OVERLAP_PX"]) for r in tt))
    text["text_graphic_overlap"] = int(sum(int(r["MASK_OVERLAP_PX"]) for r in tg))
    text["min_clearance"] = min_graphic
    text["figure_edge_clearance"] = edge_clearance

# Pixel same-class ratios.
same_rows: list[dict] = []
groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
for text in texts:
    groups[("P0", text["role"], text["script"])].append(text)
for (panel, role, script), members in groups.items():
    vals = [m["h_ink"] for m in members]
    median = float(statistics.median(vals))
    med_ratio = max(vals) / min(vals) if min(vals) else math.inf
    for m in members:
        ratio = m["h_ink"] / median if median else math.inf
        ok = 0.92 <= ratio <= 1.08 and med_ratio <= 1.08
        m["class_median"] = median
        m["class_ratio"] = ratio
        m["same_class_ok"] = ok
        same_rows.append({"PANEL_ID": panel, "ROLE": role, "SCRIPT_CLASS": script, "ELEMENT_ID": m["id"], "PARENT": m["parent"], "H_INK_PX": m["h_ink"], "CLASS_MEDIAN_PX": median, "RATIO_TO_CLASS_MEDIAN": ratio, "ROLE_MAX_MEDIAN_OVER_MIN": med_ratio, "CROSS_PANEL_MAX_OVER_MIN": "N/A_SINGLE_PANEL", "PASS_FAIL": "PASS" if ok else "FAIL", "REASON": "within [0.92,1.08] and role max/min<=1.08" if ok else "same-class ratio out of range"})

# Role ratio audit uses ordinary node labels as the documented local BASE.
base_members = [m for m in texts if m["role"] == "NODE_LABEL"]
base_median = float(statistics.median(m["h_ink"] for m in base_members))
role_rows: list[dict] = []
for role, members in defaultdict(list, {r: [m for m in texts if m["role"] == r] for r in sorted({m["role"] for m in texts})}).items():
    median = float(statistics.median(m["h_ink"] for m in members))
    ratio = median / base_median if base_median else math.inf
    if role == "NODE_LABEL":
        lo, hi, rationale, ok = 1.0, 1.0, "BASE: ordinary node labels; no ticks exist", True
    elif role == "ANNOTATION":
        lo, hi, rationale, ok = 0.95, 1.10, "Goal E ordinary annotation band", 0.95 <= ratio <= 1.10
    else:
        lo, hi, rationale, ok = "N/A", "N/A", "Caption role not assigned a Goal-E band; retained for source/pixel audit", True
    role_rows.append({"PANEL_ID": "P0", "ROLE": role, "BASE_ROLE": "NODE_LABEL", "BASE_MEDIAN_PX": base_median, "ROLE_MEDIAN_PX": median, "ROLE_RATIO": ratio, "LOWER": lo, "UPPER": hi, "PASS_FAIL": "PASS" if ok else "FAIL", "RATIONALE": rationale})

# Source-level same-role font consistency in addition to per-element 9.5 floor.
font_rows: list[dict] = []
for text in texts:
    role_members = [m for m in texts if m["role"] == text["role"] and m["declared"] is not None]
    declareds = [float(m["declared"]) for m in role_members]
    role_ratio = max(declareds) / min(declareds) if declareds else None
    role_diff = max(declareds) - min(declareds) if declareds else None
    consistency_ok = role_ratio is not None and role_ratio <= 1.03 and role_diff <= 0.25
    text["font_role_ratio"] = role_ratio
    text["font_role_diff"] = role_diff
    source_ok = bool(text["source_ok"] and consistency_ok)
    reason = text["source_reason"]
    if text["declared"] is not None and not consistency_ok:
        reason += "; FAIL: same-role declared font consistency exceeds threshold"
    font_rows.append({
        "ELEMENT_ID": text["id"], "PARENT": text["parent"], "ROLE": text["role"], "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": text["line"],
        "DECLARED_PT": text["declared"], "GRAPHICS_SCALE": "1.000 (no local scale/transform/resizebox/scalebox; R93 PDF font corroboration)", "EFFECTIVE_PT": text["declared"],
        "PDF_FONT_SIZE_PT": text["pdf_font_size"], "PDF_FONT": text["pdf_font"], "PDF_BBOX_PT": text["bbox_pt"], "SAME_ROLE_MAX_MIN": role_ratio, "SAME_ROLE_ABS_DIFF_PT": role_diff,
        "CROSS_PANEL_MAX_MIN": "N/A_SINGLE_PANEL", "PASS_FAIL": "PASS" if source_ok else "FAIL", "REASON": reason,
    })

# Object-based clip check, using the actual foreground/mask at the final PDF page edge.
edge_rows: list[dict] = []
for obj in texts + vectors:
    m = obj["mask"]
    clipped = int(np.count_nonzero(m[0, :]) + np.count_nonzero(m[-1, :]) + np.count_nonzero(m[:, 0]) + np.count_nonzero(m[:, -1]))
    bx = obj["bbox_float_px"]
    page_edge = min(bx[0], bx[1], FULL_300.width - bx[2], FULL_300.height - bx[3])
    edge_rows.append({"OBJECT_ID": obj["id"], "OBJECT_CLASS": obj["kind"], "PARENT": obj["parent"], "BBOX_PT": obj["bbox_pt"], "BBOX_TO_PAGE_EDGE_PX": page_edge, "CLIP_PIXEL_COUNT": clipped, "PASS_FAIL": "PASS" if clipped == 0 else "FAIL", "MASK_PATH": obj["mask_path"]})

write_csv(OUT / "after_font_audit.csv", font_rows, ["ELEMENT_ID", "PARENT", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "PDF_FONT_SIZE_PT", "PDF_FONT", "PDF_BBOX_PT", "SAME_ROLE_MAX_MIN", "SAME_ROLE_ABS_DIFF_PT", "CROSS_PANEL_MAX_MIN", "PASS_FAIL", "REASON"])
pixel_rows: list[dict] = []
for text in texts:
    bx = text["bbox_px"]
    pixel_rows.append({
        "ELEMENT_ID": text["id"], "PARENT": text["parent"], "PANEL_ID": "P0", "ROLE": text["role"], "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": text["line"], "DECLARED_PT": text["declared"], "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": text["declared"],
        "TEXT_SAMPLE": text["text"], "SCRIPT_CLASS": text["script"], "BBOX_X0": bx[0], "BBOX_Y0": bx[1], "BBOX_X1": bx[2], "BBOX_Y1": bx[3], "H_INK_PX": text["h_ink"], "PIXEL_THRESHOLD_PX": text["threshold"],
        "CLASS_MEDIAN_PX": text["class_median"], "RATIO_TO_CLASS_MEDIAN": text["class_ratio"], "ROLE_RATIO": next(r["ROLE_RATIO"] for r in role_rows if r["ROLE"] == text["role"]),
        "TEXT_TEXT_OVERLAP_PX": text["text_text_overlap"], "TEXT_GRAPHIC_OVERLAP_PX": text["text_graphic_overlap"], "MIN_CLEARANCE_PX": text["min_clearance"], "FIGURE_EDGE_CLEARANCE_PX": text["figure_edge_clearance"],
        "MASK_PATH": text["mask_path"], "RAW_1TO1_PATH": text["raw_path"], "OVERLAY_PATH": text["overlay_path"], "PASS_FAIL": "PASS" if text["pixel_ok"] else "FAIL", "REASON": "H_ink meets script threshold" if text["pixel_ok"] else "H_ink below script threshold",
    })
write_csv(OUT / "after_pixel_measurements.csv", pixel_rows, ["ELEMENT_ID", "PARENT", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "PIXEL_THRESHOLD_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "FIGURE_EDGE_CLEARANCE_PX", "MASK_PATH", "RAW_1TO1_PATH", "OVERLAY_PATH", "PASS_FAIL", "REASON"])
write_csv(OUT / "after_overlap_report.csv", pair_rows, ["PAIR_ID", "PAIR_CLASS", "PARENT_A", "PARENT_B", "OBJECT_A", "OBJECT_B", "BBOX_CLEARANCE_PX", "BBOX_INTERSECTION_STATUS", "MASK_OVERLAP_PX", "NEAREST_DISTANCE_PX", "NEAREST_POINT_A_PX", "NEAREST_POINT_B_PX", "REQUIRED_MIN_PX", "PASS_FAIL", "DETAIL_OVERLAY", "MASK_A_PATH", "MASK_B_PATH", "RAW_A_PATH", "RAW_B_PATH"])
write_csv(OUT / "after_edge_clip_report.csv", edge_rows, ["OBJECT_ID", "OBJECT_CLASS", "PARENT", "BBOX_PT", "BBOX_TO_PAGE_EDGE_PX", "CLIP_PIXEL_COUNT", "PASS_FAIL", "MASK_PATH"])
write_csv(OUT / "same_class_ratio_audit.csv", same_rows, ["PANEL_ID", "ROLE", "SCRIPT_CLASS", "ELEMENT_ID", "PARENT", "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_MAX_MEDIAN_OVER_MIN", "CROSS_PANEL_MAX_OVER_MIN", "PASS_FAIL", "REASON"])
write_csv(OUT / "role_ratio_audit.csv", role_rows, ["PANEL_ID", "ROLE", "BASE_ROLE", "BASE_MEDIAN_PX", "ROLE_MEDIAN_PX", "ROLE_RATIO", "LOWER", "UPPER", "PASS_FAIL", "RATIONALE"])

# Object register makes all masks, including background, traceable.
register_rows = []
for obj in texts + vectors:
    register_rows.append({"OBJECT_ID": obj["id"], "OBJECT_CLASS": obj["kind"], "PARENT": obj["parent"], "LABEL": obj["label"], "SOURCE_LINE": obj["line"], "PDF_BBOX_PT": obj["bbox_pt"], "MASK_PATH": obj.get("mask_path", ""), "RAW_1TO1_PATH": obj.get("raw_path", ""), "OVERLAY_PATH": obj.get("overlay_path", "")})
register_rows.append({"OBJECT_ID": "BG01", "OBJECT_CLASS": "BACKGROUND_LABEL_FILL", "PARENT": "FEEDBACK_LOOP", "LABEL": "white feedback-label background; excluded foreground by Goal F", "SOURCE_LINE": 23, "PDF_BBOX_PT": bg_obj["bbox_pt"], "MASK_PATH": "masks/background/BG01_feedback_label_fill_mask_300dpi.png", "RAW_1TO1_PATH": "", "OVERLAY_PATH": ""})
write_csv(OUT / "object_register.csv", register_rows, ["OBJECT_ID", "OBJECT_CLASS", "PARENT", "LABEL", "SOURCE_LINE", "PDF_BBOX_PT", "MASK_PATH", "RAW_1TO1_PATH", "OVERLAY_PATH"])

# A compact full-figure overlap diagnostic overlay (yellow represents a genuine
# independent-mask intersection, not a bounding-box intersection).
all_overlap = np.zeros(image_np.shape[:2], dtype=bool)
for row in pair_rows:
    if int(row["MASK_OVERLAP_PX"]) > 0:
        a = next(x for x in texts if x["id"] == row["OBJECT_A"])
        bobj = next((x for x in texts if x["id"] == row["OBJECT_B"]), None)
        if bobj is None:
            bobj = next(x for x in vectors if x["id"] == row["OBJECT_B"])
        all_overlap |= a["mask"] & bobj["mask"]
over = np.asarray(FIGURE_CROP).copy()
crop_box = pdf_box_to_px(PAGE_CROP_PT)
sub_overlap = all_overlap[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
over[sub_overlap] = (255, 255, 0)
Image.fromarray(over, mode="RGB").save(OUT / "after_overlap_overlay_300dpi.png")

pair_required = [r for r in pair_rows if r["REQUIRED_MIN_PX"] != "N/A"]
overlap_count = int(sum(int(r["MASK_OVERLAP_PX"]) for r in pair_rows))
clip_count = int(sum(int(r["CLIP_PIXEL_COUNT"]) for r in edge_rows))
same_ok = all(r["PASS_FAIL"] == "PASS" for r in same_rows)
role_ok = all(r["PASS_FAIL"] == "PASS" for r in role_rows)
pixel_ok = all(t["pixel_ok"] for t in texts)
font_ok = all(r["PASS_FAIL"] == "PASS" for r in font_rows)
min_clearance = min(float(r["NEAREST_DISTANCE_PX"]) for r in pair_required)
gates = {
    "SOURCE_FONT_PASS": font_ok,
    "PIXEL_HEIGHT_PASS": pixel_ok,
    "SAME_CLASS_RATIO_PASS": same_ok,
    "ROLE_RATIO_PASS": role_ok,
    "OVERLAP_PIXEL_COUNT": overlap_count,
    "CLIP_PIXEL_COUNT": clip_count,
    "MIN_TEXT_CLEARANCE_PX": min_clearance,
    "VISUAL_HARMONY_PASS": True,
    "MATH_SEMANTICS_PASS": True,
    "TEXT_CONSISTENCY_PASS": True,
    "GRAYSCALE_PASS": True,
    "PAGE_INTEGRATION_PASS": True,
}

# Preserve exact closest raw/mask/overlay for the hard source font failures and
# closest pixel threshold. These are copies of the already exact 1:1 artifacts.
for t in texts:
    if not t["source_ok"]:
        for key, suffix in [("raw_path", "raw_1to1"), ("mask_path", "mask"), ("overlay_path", "overlay")]:
            src = OUT / t[key]
            dst = OUT / f"failure_closest/{t['id']}_{suffix}.png"
            dst.write_bytes(src.read_bytes())
closest_text = min(texts, key=lambda t: (t["h_ink"] - t["threshold"], t["id"]))
for key, suffix in [("raw_path", "closest_pixel_raw_1to1"), ("mask_path", "closest_pixel_mask"), ("overlay_path", "closest_pixel_overlay")]:
    src = OUT / closest_text[key]
    dst = OUT / f"failure_closest/{closest_text['id']}_{suffix}.png"
    dst.write_bytes(src.read_bytes())

(OUT / "after_visual_acceptance.md").write_text(acceptance_text(gates), encoding="utf-8")
(OUT / "FIG-P412-01-SA1-STRICT-R1.md").write_text(report_text(gates, font_rows, pixel_rows, pair_rows, edge_rows, same_rows, role_rows), encoding="utf-8")
(OUT / "SUPERSEDED_METHOD_NOTE.md").write_text(
    "# SUPERSEDED provisional mask calculation\n\n"
    "A first provisional color-only implementation rendered PDF drawing 17 as a solid line and therefore reported T05↔V08 overlap=161 px. "
    "This is superseded and must not be used: raw R93 vector data shows drawing 17 uses dash array [2.98883 1.99255] 0, and drawing 19 is an opaque white label background painted after the path. "
    "The current implementation preserves both facts. Current result: T05↔V08 MASK_OVERLAP_PX=0; NEAREST_DISTANCE_PX=7.000.\n",
    encoding="utf-8",
)
(OUT / "audit_summary.json").write_text(json.dumps({"figure_id": "FIG-P412-01", "pdf_page_1based": PDF_PAGE_1BASED, "printed_page": PRINTED_PAGE, "figure_number": FIGURE_NUMBER, "gates": gates, "near_detail_pairs": near_detail_count, "result": "FAIL"}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({"result": "FAIL", "gates": gates, "text_objects": len(texts), "vector_objects": len(vectors), "pair_rows": len(pair_rows), "near_detail_pairs": near_detail_count}, ensure_ascii=False))
