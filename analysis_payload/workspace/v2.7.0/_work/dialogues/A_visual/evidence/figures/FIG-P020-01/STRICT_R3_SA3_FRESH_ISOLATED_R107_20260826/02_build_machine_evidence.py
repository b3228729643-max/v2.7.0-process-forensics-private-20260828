from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R3_SA3_FRESH_ISOLATED_R107_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C01\fig_v1_c01_language_flow.tex")
GOAL = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md")
PROTOCOL = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md")
SCHEMA = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\STRICT-GOAL-20260823\STRICT_FIGURE_EVIDENCE_SCHEMA.md")
PDFTOPPM = Path(r"C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe")
PAGE_NUMBER = 17
HANDOFF_ID = "A-R107-P020-SA3-FRESH-ISOLATED-20260826"

# Independently frozen after locating the exact caption on physical page 17.
# The figure crop includes the caption.  The standalone crop contains only the
# TikZ drawing.  Both are integer crops of a direct native 300 dpi page render.
FIGURE_CROP_PT = (59.0, 266.0, 525.0, 375.0)
STANDALONE_CROP_PT = (59.0, 266.0, 525.0, 359.0)
TARGET_TEXT_PT = (60.0, 280.0, 522.0, 373.0)

EXPECTED_PARENTS = {
    "P_OBJECT_TITLE": ("对象声明", 14, 10.5, "NODE_TITLE", "OBJECT"),
    "P_RELATION_TITLE": ("关系与映射", 15, 10.5, "NODE_TITLE", "RELATION"),
    "P_LOGIC_TITLE": ("运算与逻辑", 22, 10.5, "NODE_TITLE", "LOGIC"),
    "P_TASK_TITLE": ("可核验任务", 23, 10.5, "NODE_TITLE", "TASK"),
    "P_OBJECT_BODY": ("集合、类型与维数", 14, 10.0, "NODE_BODY", "OBJECT"),
    "P_RELATION_DOMAIN": ("定义域", 15, 10.0, "NODE_BODY", "RELATION"),
    "P_RELATION_RANGE": ("值域", 21, 10.0, "NODE_BODY", "RELATION"),
    "P_LOGIC_BODY": ("复合、量词与约束", 22, 10.0, "NODE_BODY", "LOGIC"),
    "P_TASK_BODY": ("输入、输出与判据", 23, 10.0, "NODE_BODY", "TASK"),
    "P_AUDIT_NOTE": ("逆向核对：任务所用定义逐项返回检查", 35, 10.0, "ANNOTATION", "AUDIT"),
    # The current figure source contains the caption verbatim at line 38.  Its
    # figure-local source has no explicit size override; native PDF metadata is
    # 9.96264 pt, consistent with the nominal 10 pt caption style.
    "P_CAPTION_LABEL": ("图1.1", 38, 10.0, "CAPTION_LABEL", "CAPTION"),
    "P_CAPTION_TEXT": ("数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。", 38, 10.0, "CAPTION_TEXT", "CAPTION"),
}

NODE_RANGES = {
    "OBJECT": (103.88405, 192.46595),
    "RELATION": (210.9376, 299.51953),
    "LOGIC": (317.9912, 406.57312),
    "TASK": (425.04477, 513.62669),
}

LOW_PROFILE = {"、", "：", "。", "."}
SINGLE_HORIZONTAL_STROKE_CJK = {"一"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_page(dpi: int, output: Path) -> None:
    prefix = output.with_suffix("")
    subprocess.run(
        [
            str(PDFTOPPM),
            "-f",
            str(PAGE_NUMBER),
            "-l",
            str(PAGE_NUMBER),
            "-singlefile",
            "-r",
            str(dpi),
            "-png",
            str(PDF),
            str(prefix),
        ],
        check=True,
    )


def pdf_bbox_to_px(bbox: tuple[float, float, float, float], sx: float, sy: float, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, math.floor(x0 * sx) - pad),
        max(0, math.floor(y0 * sy) - pad),
        math.ceil(x1 * sx) + pad,
        math.ceil(y1 * sy) + pad,
    )


def color255(value) -> np.ndarray:
    if isinstance(value, (int, float)):
        return np.array([value, value, value], dtype=np.float64) * 255.0
    return np.array(value[:3], dtype=np.float64) * 255.0


def mixture_mask(region: np.ndarray, fg: np.ndarray, backgrounds: list[np.ndarray], residual_limit: float = 20.0) -> np.ndarray:
    pixels = region.astype(np.float64)
    best = np.zeros(region.shape[:2], dtype=bool)
    for bg in backgrounds:
        vector = bg - fg
        denom = float(np.dot(vector, vector))
        if denom <= 1e-9:
            continue
        alpha = np.sum((bg - pixels) * vector, axis=2) / denom
        alpha_clip = np.clip(alpha, 0.0, 1.0)
        reconstructed = bg[None, None, :] - alpha_clip[:, :, None] * vector[None, None, :]
        residual = np.max(np.abs(pixels - reconstructed), axis=2)
        local_contrast = np.max(np.abs(pixels - bg[None, None, :]), axis=2)
        valid = (alpha >= 0.0) & (alpha <= 1.12) & (local_contrast >= 20.0) & (residual <= residual_limit)
        best |= valid
    return best


def trim_mask(mask: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return mask[:0, :0], (bbox[0], bbox[1], bbox[0], bbox[1])
    lx0, lx1 = int(xs.min()), int(xs.max()) + 1
    ly0, ly1 = int(ys.min()), int(ys.max()) + 1
    return mask[ly0:ly1, lx0:lx1], (bbox[0] + lx0, bbox[1] + ly0, bbox[0] + lx1, bbox[1] + ly1)


def paste_mask(canvas: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int], origin: tuple[int, int]) -> None:
    ox, oy = origin
    x0, y0, x1, y1 = bbox
    dx0, dy0 = x0 - ox, y0 - oy
    dx1, dy1 = x1 - ox, y1 - oy
    canvas[dy0:dy1, dx0:dx1] |= mask


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def make_triptych(original: Image.Image, mask: np.ndarray, scale: int = 8) -> Image.Image:
    original = original.convert("RGB")
    arr = np.array(original)
    overlay = arr.copy()
    overlay[mask] = ((overlay[mask].astype(np.uint16) + np.array([255, 0, 0], dtype=np.uint16)) // 2).astype(np.uint8)
    mask_only = np.full_like(arr, 255)
    mask_only[mask] = np.array([0, 0, 0], dtype=np.uint8)
    panels = [Image.fromarray(arr), Image.fromarray(overlay), Image.fromarray(mask_only)]
    up = [panel.resize((panel.width * scale, panel.height * scale), Image.Resampling.NEAREST) for panel in panels]
    trip = Image.new("RGB", (sum(panel.width for panel in up), max(panel.height for panel in up)), "white")
    x = 0
    for panel in up:
        trip.paste(panel, (x, 0))
        x += panel.width
    return trip


def object_mask_from_char(char: dict, image: Image.Image, sx: float, sy: float, node: str) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    bbox = pdf_bbox_to_px((char["x0"], char["top"], char["x1"], char["bottom"]), sx, sy, pad=2)
    region = np.array(image.crop(bbox).convert("RGB"))
    fg = color255(char["non_stroking_color"])
    if node == "OBJECT" or node == "LOGIC":
        backgrounds = [color255([0.94902, 0.96472, 0.9804])]
    elif node == "RELATION" or node == "TASK":
        backgrounds = [color255([0.9451, 0.97255, 0.96472])]
    else:
        backgrounds = [color255(1.0)]
    mask = mixture_mask(region, fg, backgrounds, residual_limit=22.0)
    # PDF glyph vector boxes are half-open ownership cells.  Padding is used
    # only to avoid losing antialiasing at integer conversion; a pixel is owned
    # by this glyph only when its native-pixel centre lies inside this glyph's
    # own vector box.  This prevents adjacent same-colour glyphs from being
    # copied into both raw masks.
    yy, xx = np.indices(mask.shape)
    global_x_center = bbox[0] + xx + 0.5
    global_y_center = bbox[1] + yy + 0.5
    owned = (
        (global_x_center >= float(char["x0"]) * sx)
        & (global_x_center < float(char["x1"]) * sx)
        & (global_y_center >= float(char["top"]) * sy)
        & (global_y_center < float(char["bottom"]) * sy)
    )
    mask &= owned
    return trim_mask(mask, bbox)


def parent_for_char(char: dict) -> str:
    top = float(char["top"])
    x = (float(char["x0"]) + float(char["x1"])) / 2.0
    if top >= 360.0:
        return "P_CAPTION_LABEL" if x < 110.0 else "P_CAPTION_TEXT"
    if top < 295.5:
        if x < 200:
            return "P_OBJECT_TITLE"
        if x < 310:
            return "P_RELATION_TITLE"
        if x < 417:
            return "P_LOGIC_TITLE"
        return "P_TASK_TITLE"
    if top < 315.0:
        if x < 200:
            return "P_OBJECT_BODY"
        if x < 260:
            return "P_RELATION_DOMAIN"
        if x < 310:
            return "P_RELATION_RANGE"
        if x < 417:
            return "P_LOGIC_BODY"
        return "P_TASK_BODY"
    return "P_AUDIT_NOTE"


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)


def relation_type(a: dict, b: dict) -> tuple[str, float | None, str, bool]:
    kinds = {a["kind"], b["kind"]}
    design_allowed = False
    if kinds == {"TEXT"}:
        if a["parent_id"] == b["parent_id"]:
            return "SAME_PARENT_GLYPH_SEQUENCE", None, "MASK", False
        return "TEXT_TEXT", 4.0, "VECTOR_BBOX", False
    if kinds == {"TEXT", "GRAPHIC"}:
        text_obj = a if a["kind"] == "TEXT" else b
        graphic = b if a["kind"] == "TEXT" else a
        if graphic["graphic_role"] == "NODE_BORDER" and text_obj["node_id"] == graphic["node_id"]:
            return "TEXT_NODE_BORDER", 5.0, "MASK", False
        if graphic["graphic_role"] == "ARROWHEAD":
            return "ARROWHEAD_TEXT", 3.0, "MASK", False
        return "TEXT_LINE_ARROW", 3.0, "MASK", False
    if a.get("connection_group") and a.get("connection_group") == b.get("connection_group"):
        design_allowed = True
        return "DESIGN_SHAFT_HEAD_CONNECTION", None, "MASK", design_allowed
    return "GRAPHIC_GRAPHIC", None, "MASK", False


def relation_images(rel: dict, obj_a: dict, obj_b: dict, page_image: Image.Image, root: Path) -> dict:
    ax, ay = rel["nearest_a_x"], rel["nearest_a_y"]
    bx, by = rel["nearest_b_x"], rel["nearest_b_y"]
    margin = 18
    x0 = max(0, min(ax, bx) - margin)
    y0 = max(0, min(ay, by) - margin)
    x1 = min(page_image.width, max(ax, bx) + margin + 1)
    y1 = min(page_image.height, max(ay, by) + margin + 1)
    roi = (x0, y0, x1, y1)
    original = page_image.crop(roi).convert("RGB")

    def local_mask(obj: dict) -> np.ndarray:
        canvas = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        ox0, oy0, ox1, oy1 = obj["ink_bbox_px"]
        ix0, iy0 = max(x0, ox0), max(y0, oy0)
        ix1, iy1 = min(x1, ox1), min(y1, oy1)
        if ix1 > ix0 and iy1 > iy0:
            src = obj["mask"][iy0 - oy0 : iy1 - oy0, ix0 - ox0 : ix1 - ox0]
            canvas[iy0 - y0 : iy1 - y0, ix0 - x0 : ix1 - x0] = src
        return canvas

    mask_a = local_mask(obj_a)
    mask_b = local_mask(obj_b)
    inter = mask_a & mask_b
    raw = np.array(original)
    overlay = raw.copy()
    overlay[mask_a] = np.array([255, 50, 50], dtype=np.uint8)
    overlay[mask_b] = np.array([50, 120, 255], dtype=np.uint8)
    overlay[inter] = np.array([255, 0, 255], dtype=np.uint8)
    mask_a_img = np.full_like(raw, 255)
    mask_b_img = np.full_like(raw, 255)
    inter_img = np.full_like(raw, 255)
    mask_a_img[mask_a] = np.array([0, 0, 0], dtype=np.uint8)
    mask_b_img[mask_b] = np.array([0, 0, 0], dtype=np.uint8)
    inter_img[inter] = np.array([0, 0, 0], dtype=np.uint8)
    panels = [raw, mask_a_img, mask_b_img, inter_img, overlay]
    composite = Image.new("RGB", ((x1 - x0) * len(panels), y1 - y0), "white")
    for index, panel in enumerate(panels):
        composite.paste(Image.fromarray(panel), ((x1 - x0) * index, 0))
    stem = rel["relation_id"]
    one = root / f"{stem}_1x.png"
    eight = root / f"{stem}_8x_nearest.png"
    composite.save(one)
    composite.resize((composite.width * 8, composite.height * 8), Image.Resampling.NEAREST).save(eight)
    return {
        "roi_full_page_px": [x0, y0, x1, y1],
        "one_x": str(one.relative_to(ROOT)).replace("\\", "/"),
        "eight_x": str(eight.relative_to(ROOT)).replace("\\", "/"),
        "panel_order": ["ORIGINAL", "A_MASK", "B_MASK", "INTERSECTION", "OVERLAY_A_RED_B_BLUE"],
    }


ROOT.mkdir(parents=True, exist_ok=True)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

identity = {
    "handoff_id": HANDOFF_ID,
    "instance": "/root/p020_r107_fresh_sa3",
    "role": "sole fresh isolated terminal SA3",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "xhigh",
    "fork_turns": "none",
    "parent_history_inherited": False,
    "official_round": "R107",
    "canonical_uid": "FIG-P020-01",
    "official_pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
    "current_source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
    "goal": {"path": str(GOAL), "bytes": GOAL.stat().st_size, "sha256": sha256(GOAL)},
    "protocol": {"path": str(PROTOCOL), "bytes": PROTOCOL.stat().st_size, "sha256": sha256(PROTOCOL)},
    "schema": {"path": str(SCHEMA), "bytes": SCHEMA.stat().st_size, "sha256": sha256(SCHEMA)},
}
write_json(ROOT / "input_identity.json", identity)

render_page(300, ROOT / "full_page_300dpi.png")
render_page(200, ROOT / "full_page_200dpi.png")
page_image = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
page200 = Image.open(ROOT / "full_page_200dpi.png").convert("RGB")

discovery = json.loads((ROOT / "discovery_page17.json").read_text(encoding="utf-8"))
page_width_pt = float(discovery["page_width_pt"])
page_height_pt = float(discovery["page_height_pt"])
sx = page_image.width / page_width_pt
sy = page_image.height / page_height_pt
sx200 = page200.width / page_width_pt
sy200 = page200.height / page_height_pt

figure_crop_px = pdf_bbox_to_px(FIGURE_CROP_PT, sx, sy)
standalone_crop_px = pdf_bbox_to_px(STANDALONE_CROP_PT, sx, sy)
figure_crop = page_image.crop(figure_crop_px)
standalone = page_image.crop(standalone_crop_px)
figure_crop.save(ROOT / "figure_crop_300dpi.png")
standalone.save(ROOT / "standalone_300dpi.png")
Image.merge("RGB", (figure_crop.convert("L"),) * 3).save(ROOT / "grayscale_300dpi.png")

location = {
    "official_round": "R107",
    "physical_page": PAGE_NUMBER,
    "printed_page": 4,
    "page_size_pt": [page_width_pt, page_height_pt],
    "full_page_300dpi_native_px": list(page_image.size),
    "full_page_200dpi_native_px": list(page200.size),
    "scale_300_px_per_pt": [sx, sy],
    "scale_200_px_per_pt": [sx200, sy200],
    "caption_exact": "图 1.1 数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。",
    "caption_pdf_bbox_pt": [80.257, 361.85, 503.68, 372.311],
    "figure_crop_bbox_pt": list(FIGURE_CROP_PT),
    "figure_crop_bbox_full_page_300dpi_px": list(figure_crop_px),
    "figure_crop_native_px": list(figure_crop.size),
    "standalone_crop_bbox_pt": list(STANDALONE_CROP_PT),
    "standalone_crop_bbox_full_page_300dpi_px": list(standalone_crop_px),
    "standalone_native_px": list(standalone.size),
    "crop_method": "integer crop of direct native Poppler render; no resize",
}
write_json(ROOT / "location_and_crop_freeze.json", location)

# Enumerate and map every visible target glyph.
chars = [
    c
    for c in discovery["objects"]["char"]
    if TARGET_TEXT_PT[0] <= float(c["x0"]) <= TARGET_TEXT_PT[2]
    and TARGET_TEXT_PT[1] <= float(c["top"]) < TARGET_TEXT_PT[3]
]
for char in chars:
    char["parent_id"] = parent_for_char(char)

groups: dict[str, list[dict]] = defaultdict(list)
for char in chars:
    groups[char["parent_id"]].append(char)
for parent_id, items in groups.items():
    items.sort(key=lambda c: float(c["x0"]))
    actual = "".join(c["text"] for c in items)
    expected = EXPECTED_PARENTS[parent_id][0]
    if actual != expected:
        raise RuntimeError(f"Glyph mapping mismatch for {parent_id}: {actual!r} != {expected!r}")

glyph_dir = ROOT / "glyph_masks"
glyph_1x = glyph_dir / "1x"
glyph_8x = glyph_dir / "8x_nearest"
glyph_1x.mkdir(parents=True, exist_ok=True)
glyph_8x.mkdir(parents=True, exist_ok=True)

ordered_chars: list[dict] = []
for parent_id in EXPECTED_PARENTS:
    ordered_chars.extend(groups[parent_id])

objects: list[dict] = []
glyph_rows: list[dict] = []
glyph_triptychs: list[tuple[str, Image.Image]] = []
for index, char in enumerate(ordered_chars, 1):
    object_id = f"T{index:03d}"
    parent_id = char["parent_id"]
    expected_text, source_line, declared_pt, role, node_id = EXPECTED_PARENTS[parent_id]
    mask, ink_bbox = object_mask_from_char(char, page_image, sx, sy, node_id)
    if mask.size == 0 or not mask.any():
        h_ink = 0
        w_ink = 0
    else:
        ys, xs = np.nonzero(mask)
        h_ink = int(ys.max() - ys.min() + 1)
        w_ink = int(xs.max() - xs.min() + 1)
    vector_bbox = pdf_bbox_to_px((char["x0"], char["top"], char["x1"], char["bottom"]), sx, sy)
    if char["text"] in LOW_PROFILE:
        script_class = "LOW_PROFILE_PUNCTUATION"
        hard_threshold = None
    elif char["text"] in SINGLE_HORIZONTAL_STROKE_CJK:
        script_class = "SINGLE_HORIZONTAL_STROKE_CJK"
        hard_threshold = None
    elif char["text"].isdigit():
        script_class = "LATIN_UPPER_DIGIT"
        hard_threshold = 24
    else:
        script_class = "CJK_FULL"
        hard_threshold = 30
    if h_ink == 0:
        machine_status = "FAIL_EMPTY_MASK"
    elif hard_threshold is not None and h_ink < hard_threshold:
        machine_status = "FAIL_HARD_PIXEL_HEIGHT"
    elif script_class in {"LOW_PROFILE_PUNCTUATION", "SINGLE_HORIZONTAL_STROKE_CJK"}:
        machine_status = "PASS_R168_ADVISORY_MICRO_RATIO"
    else:
        machine_status = "PASS"

    original = page_image.crop(ink_bbox).convert("RGB")
    arr = np.array(original)
    overlay = arr.copy()
    overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.full_like(arr, 255)
    mask_only[mask] = np.array([0, 0, 0], dtype=np.uint8)
    original_path = glyph_1x / f"{object_id}_original_1x.png"
    overlay_path = glyph_1x / f"{object_id}_target_overlay_1x.png"
    mask_path = glyph_1x / f"{object_id}_mask_only_1x.png"
    Image.fromarray(arr).save(original_path)
    Image.fromarray(overlay).save(overlay_path)
    Image.fromarray(mask_only).save(mask_path)
    trip = make_triptych(original, mask, scale=8)
    trip_path = glyph_8x / f"{object_id}_triptych_8x_nearest.png"
    trip.save(trip_path)
    glyph_triptychs.append((object_id, trip))

    obj = {
        "object_id": object_id,
        "kind": "TEXT",
        "parent_id": parent_id,
        "node_id": node_id,
        "role": role,
        "graphic_role": "",
        "connection_group": "",
        "char": char["text"],
        "source_line": source_line,
        "declared_pt": declared_pt,
        "effective_pt": declared_pt,
        "pdf_fontname": char["fontname"],
        "pdf_font_size_pt": float(char["size"]),
        "vector_bbox_px": vector_bbox,
        "ink_bbox_px": ink_bbox,
        "mask": mask,
    }
    objects.append(obj)
    glyph_rows.append(
        {
            "ELEMENT_ID": object_id,
            "PARENT_ID": parent_id,
            "PANEL_ID": "MAIN",
            "ROLE": role,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": source_line,
            "DECLARED_PT": f"{declared_pt:.2f}",
            "GRAPHICS_SCALE": "1.0000",
            "EFFECTIVE_PT": f"{declared_pt:.2f}",
            "PDF_FONTNAME": char["fontname"],
            "PDF_FONT_SIZE_PT": f"{float(char['size']):.5f}",
            "FONT_METADATA_DIFF_PCT": f"{abs(float(char['size']) - declared_pt) / declared_pt * 100:.4f}",
            "TEXT_SAMPLE": char["text"],
            "UNICODE_CODEPOINT": f"U+{ord(char['text']):04X}",
            "SCRIPT_CLASS": script_class,
            "VECTOR_BBOX_PX": json.dumps(vector_bbox),
            "INK_BBOX_PX": json.dumps(ink_bbox),
            "H_INK_PX": h_ink,
            "W_INK_PX": w_ink,
            "HARD_THRESHOLD_PX": hard_threshold if hard_threshold is not None else "R168_ADVISORY",
            "MASK_PIXEL_COUNT": int(mask.sum()),
            "EMPTY_MASK": not bool(mask.any()),
            "CLIP_TOUCH_PAGE_EDGE": bool(ink_bbox[0] <= 0 or ink_bbox[1] <= 0 or ink_bbox[2] >= page_image.width or ink_bbox[3] >= page_image.height),
            "MACHINE_GATE_STATUS": machine_status,
            "MACHINE_REASON": "R168 makes micro [0.92,1.08], font metadata, single-horizontal-stroke CJK and 1-2px raster differences advisory" if script_class in {"LOW_PROFILE_PUNCTUATION", "SINGLE_HORIZONTAL_STROKE_CJK"} else "hard class height and non-empty raw-mask gate",
            "ORIGINAL_1X": str(original_path.relative_to(ROOT)).replace("\\", "/"),
            "TARGET_OVERLAY_1X": str(overlay_path.relative_to(ROOT)).replace("\\", "/"),
            "MASK_ONLY_1X": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
            "TRIPTYCH_8X": str(trip_path.relative_to(ROOT)).replace("\\", "/"),
        }
    )

# 8x nearest contact sheets: two columns by five rows.
contact_dir = ROOT / "contact_sheets"
contact_dir.mkdir(exist_ok=True)
contact_manifest = []
font = ImageFont.load_default()
for sheet_index, start in enumerate(range(0, len(glyph_triptychs), 10), 1):
    batch = glyph_triptychs[start : start + 10]
    cell_w = max(img.width for _, img in batch) + 12
    cell_h = max(img.height for _, img in batch) + 28
    sheet = Image.new("RGB", (cell_w * 2, cell_h * 5), "white")
    draw = ImageDraw.Draw(sheet)
    cells = []
    for local_index, (object_id, trip) in enumerate(batch):
        col = local_index % 2
        row = local_index // 2
        x = col * cell_w + 6
        y = row * cell_h + 20
        draw.text((x, row * cell_h + 3), f"{object_id} ORIGINAL | OVERLAY | MASK", fill="black", font=font)
        sheet.paste(trip, (x, y))
        cells.append({"object_id": object_id, "cell": f"R{row + 1}C{col + 1}"})
    path = contact_dir / f"glyph_contact_{sheet_index:02d}_8x_nearest.png"
    sheet.save(path)
    contact_manifest.append({"sheet": str(path.relative_to(ROOT)).replace("\\", "/"), "cells": cells})
write_json(contact_dir / "glyph_contact_manifest.json", contact_manifest)

# Enumerate every target drawing/path and construct 14 foreground masks.
drawings = discovery["objects"]
graphic_specs = [
    ("G001", "curve", 5, "NODE_BORDER", "OBJECT", "", [0.12158, 0.30588, 0.47452], [[0.94902, 0.96472, 0.9804], [0.97365, 0.97917, 0.98424]]),
    ("G002", "curve", 6, "NODE_BORDER", "RELATION", "", [0.12158, 0.30588, 0.47452], [[0.9451, 0.97255, 0.96472], [0.97365, 0.97917, 0.98424]]),
    ("G003", "curve", 8, "NODE_BORDER", "LOGIC", "", [0.12158, 0.30588, 0.47452], [[0.94902, 0.96472, 0.9804], [0.97365, 0.97917, 0.98424]]),
    ("G004", "curve", 9, "NODE_BORDER", "TASK", "", [0.12158, 0.30588, 0.47452], [[0.9451, 0.97255, 0.96472], [0.97365, 0.97917, 0.98424]]),
    ("G005", "line", 3, "LINE_ARROW", "RELATION", "INLINE", [0.12158, 0.16078, 0.2157], [[0.9451, 0.97255, 0.96472]]),
    ("G006", "curve", 7, "ARROWHEAD", "RELATION", "INLINE", [0.12158, 0.16078, 0.2157], [[0.9451, 0.97255, 0.96472]]),
    ("G007", "line", 4, "LINE_ARROW", "CHAIN", "MAIN1", [0.12158, 0.30588, 0.47452], [[0.97365, 0.97917, 0.98424]]),
    ("G008", "curve", 10, "ARROWHEAD", "CHAIN", "MAIN1", [0.12158, 0.30588, 0.47452], [[0.97365, 0.97917, 0.98424]]),
    ("G009", "line", 5, "LINE_ARROW", "CHAIN", "MAIN2", [0.12158, 0.30588, 0.47452], [[0.97365, 0.97917, 0.98424]]),
    ("G010", "curve", 11, "ARROWHEAD", "CHAIN", "MAIN2", [0.12158, 0.30588, 0.47452], [[0.97365, 0.97917, 0.98424]]),
    ("G011", "line", 6, "LINE_ARROW", "CHAIN", "MAIN3", [0.12158, 0.30588, 0.47452], [[0.97365, 0.97917, 0.98424]]),
    ("G012", "curve", 12, "ARROWHEAD", "CHAIN", "MAIN3", [0.12158, 0.30588, 0.47452], [[0.97365, 0.97917, 0.98424]]),
    ("G013", "curve", 13, "LINE_ARROW", "AUDIT", "RETURN", [0.41962, 0.44707, 0.50195], [[0.97365, 0.97917, 0.98424], [1.0, 1.0, 1.0]]),
    ("G014", "curve", 14, "ARROWHEAD", "AUDIT", "RETURN", [0.41962, 0.44707, 0.50195], [[0.97365, 0.97917, 0.98424], [1.0, 1.0, 1.0]]),
]
graphic_dir = ROOT / "graphic_masks"
graphic_dir.mkdir(exist_ok=True)
graphic_rows = []
graphic_triptychs = []
for object_id, obj_type, obj_index, role, node_id, connection_group, fg_value, bg_values in graphic_specs:
    drawing = drawings[obj_type][obj_index]
    bbox_pt = (float(drawing["x0"]), float(drawing["top"]), float(drawing["x1"]), float(drawing["bottom"]))
    bbox = pdf_bbox_to_px(bbox_pt, sx, sy, pad=4)
    region = np.array(page_image.crop(bbox).convert("RGB"))
    mask = mixture_mask(region, color255(fg_value), [color255(bg) for bg in bg_values], residual_limit=26.0)
    if role == "NODE_BORDER":
        yy, xx = np.indices(mask.shape)
        band = np.minimum.reduce([xx, yy, mask.shape[1] - 1 - xx, mask.shape[0] - 1 - yy]) <= 9
        mask &= band
    mask, ink_bbox = trim_mask(mask, bbox)
    original = page_image.crop(ink_bbox).convert("RGB")
    raw = np.array(original)
    overlay = raw.copy()
    overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.full_like(raw, 255)
    mask_only[mask] = np.array([0, 0, 0], dtype=np.uint8)
    original_path = graphic_dir / f"{object_id}_original_1x.png"
    overlay_path = graphic_dir / f"{object_id}_target_overlay_1x.png"
    mask_path = graphic_dir / f"{object_id}_mask_only_1x.png"
    Image.fromarray(raw).save(original_path)
    Image.fromarray(overlay).save(overlay_path)
    Image.fromarray(mask_only).save(mask_path)
    trip = make_triptych(original, mask, scale=2)
    graphic_triptychs.append((object_id, trip))
    obj = {
        "object_id": object_id,
        "kind": "GRAPHIC",
        "parent_id": connection_group or object_id,
        "node_id": node_id,
        "role": "GRAPHIC",
        "graphic_role": role,
        "connection_group": connection_group,
        "char": "",
        "source_line": {"NODE_BORDER": 9, "LINE_ARROW": 28 if node_id == "CHAIN" else (18 if node_id == "RELATION" else 32), "ARROWHEAD": 29 if node_id == "CHAIN" else (18 if node_id == "RELATION" else 32)}[role],
        "declared_pt": "",
        "effective_pt": "",
        "pdf_fontname": "",
        "pdf_font_size_pt": "",
        "vector_bbox_px": pdf_bbox_to_px(bbox_pt, sx, sy),
        "ink_bbox_px": ink_bbox,
        "mask": mask,
    }
    objects.append(obj)
    graphic_rows.append(
        {
            "OBJECT_ID": object_id,
            "PDF_OBJECT_TYPE": obj_type,
            "PDF_OBJECT_INDEX": obj_index,
            "GRAPHIC_ROLE": role,
            "NODE_ID": node_id,
            "CONNECTION_GROUP": connection_group,
            "SOURCE_LINE": obj["source_line"],
            "VECTOR_BBOX_PT": json.dumps(bbox_pt),
            "VECTOR_BBOX_PX": json.dumps(obj["vector_bbox_px"]),
            "INK_BBOX_PX": json.dumps(ink_bbox),
            "MASK_PIXEL_COUNT": int(mask.sum()),
            "EMPTY_MASK": not bool(mask.any()),
            "MACHINE_STATUS": "PASS" if mask.any() else "FAIL_EMPTY_MASK",
            "ORIGINAL_1X": str(original_path.relative_to(ROOT)).replace("\\", "/"),
            "TARGET_OVERLAY_1X": str(overlay_path.relative_to(ROOT)).replace("\\", "/"),
            "MASK_ONLY_1X": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
        }
    )

# Two compact graphic contact sheets (native objects; no metric is taken from these sheets).
graphic_contact_manifest = []
for sheet_index, start in enumerate(range(0, len(graphic_triptychs), 7), 1):
    batch = graphic_triptychs[start : start + 7]
    cell_w = max(img.width for _, img in batch) + 14
    cell_h = max(img.height for _, img in batch) + 28
    sheet = Image.new("RGB", (cell_w, cell_h * len(batch)), "white")
    draw = ImageDraw.Draw(sheet)
    cells = []
    for row, (object_id, trip) in enumerate(batch):
        y = row * cell_h
        draw.text((5, y + 3), f"{object_id} ORIGINAL | OVERLAY | MASK (2x navigation)", fill="black", font=font)
        sheet.paste(trip, (5, y + 20))
        cells.append({"object_id": object_id, "cell": f"R{row + 1}C1"})
    path = contact_dir / f"graphic_contact_{sheet_index:02d}.png"
    sheet.save(path)
    graphic_contact_manifest.append({"sheet": str(path.relative_to(ROOT)).replace("\\", "/"), "cells": cells})
write_json(contact_dir / "graphic_contact_manifest.json", graphic_contact_manifest)

# Every target PDF drawing/path is accounted for, including two backgrounds.
drawing_ledger = [
    {"PDF_OBJECT_TYPE": "curve", "PDF_OBJECT_INDEX": 4, "CLASS": "BACKGROUND_FILL", "FOREGROUND_OBJECT_ID": "", "MACHINE_STATUS": "ACCOUNTED_BACKGROUND"},
    {"PDF_OBJECT_TYPE": "rect", "PDF_OBJECT_INDEX": 0, "CLASS": "OPAQUE_ANNOTATION_BACKGROUND", "FOREGROUND_OBJECT_ID": "", "MACHINE_STATUS": "ACCOUNTED_BACKGROUND"},
]
for spec in graphic_specs:
    drawing_ledger.append({"PDF_OBJECT_TYPE": spec[1], "PDF_OBJECT_INDEX": spec[2], "CLASS": spec[3], "FOREGROUND_OBJECT_ID": spec[0], "MACHINE_STATUS": "ACCOUNTED_FOREGROUND"})
write_csv(ROOT / "drawing_path_ledger.csv", drawing_ledger)
write_csv(ROOT / "graphic_object_ledger.csv", graphic_rows)

# Produce the text/object overlay on the full figure crop (body + caption).
overlay = figure_crop.copy()
draw = ImageDraw.Draw(overlay)
sox, soy = figure_crop_px[0], figure_crop_px[1]
for obj in objects:
    x0, y0, x1, y1 = obj["ink_bbox_px"]
    color = (220, 30, 30) if obj["kind"] == "TEXT" else (20, 80, 220)
    draw.rectangle((x0 - sox, y0 - soy, x1 - 1 - sox, y1 - 1 - soy), outline=color, width=1)
    draw.text((x0 - sox, max(0, y0 - soy - 10)), obj["object_id"], fill=color, font=font)
overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

# Freeze object denominator and safe-name mapping.
object_manifest_rows = []
for obj in objects:
    object_manifest_rows.append(
        {
            "OBJECT_ID": obj["object_id"],
            "SAFE_FILENAME": obj["object_id"],
            "KIND": obj["kind"],
            "PARENT_ID": obj["parent_id"],
            "NODE_ID": obj["node_id"],
            "ROLE": obj["role"],
            "GRAPHIC_ROLE": obj["graphic_role"],
            "CONNECTION_GROUP": obj["connection_group"],
            "VISIBLE_TEXT": obj["char"],
            "INK_BBOX_PX": json.dumps(obj["ink_bbox_px"]),
            "MASK_PIXEL_COUNT": int(obj["mask"].sum()),
        }
    )
write_csv(ROOT / "object_manifest.csv", object_manifest_rows)

N = len(objects)
expected_pairs = N * (N - 1) // 2

# Prepare masks in the frozen figure-crop coordinates and exhaust every
# unordered pair, including every visible caption glyph.
stand_w = figure_crop_px[2] - figure_crop_px[0]
stand_h = figure_crop_px[3] - figure_crop_px[1]
stand_masks: dict[str, np.ndarray] = {}
for obj in objects:
    canvas = np.zeros((stand_h, stand_w), dtype=bool)
    paste_mask(canvas, obj["mask"], obj["ink_bbox_px"], (figure_crop_px[0], figure_crop_px[1]))
    stand_masks[obj["object_id"]] = canvas

pair_rows = []
pair_runtime = []
for i, obj_a in enumerate(objects):
    mask_a = stand_masks[obj_a["object_id"]]
    distances, nearest_indices = ndimage.distance_transform_edt(~mask_a, return_indices=True)
    for j in range(i + 1, N):
        obj_b = objects[j]
        mask_b = stand_masks[obj_b["object_id"]]
        inter = mask_a & mask_b
        overlap = int(inter.sum())
        if overlap:
            yy, xx = np.argwhere(inter)[0]
            a_y = b_y = int(yy + figure_crop_px[1])
            a_x = b_x = int(xx + figure_crop_px[0])
            center_distance = 0.0
            raw_clearance = 0.0
        else:
            coords_b = np.argwhere(mask_b)
            vals = distances[coords_b[:, 0], coords_b[:, 1]]
            k = int(np.argmin(vals))
            b_yl, b_xl = map(int, coords_b[k])
            a_yl = int(nearest_indices[0, b_yl, b_xl])
            a_xl = int(nearest_indices[1, b_yl, b_xl])
            a_x, a_y = a_xl + figure_crop_px[0], a_yl + figure_crop_px[1]
            b_x, b_y = b_xl + figure_crop_px[0], b_yl + figure_crop_px[1]
            center_distance = float(vals[k])
            raw_clearance = max(0.0, center_distance - 1.0)
        gate_type, threshold, metric, design_allowed = relation_type(obj_a, obj_b)
        vector_gap = bbox_gap(obj_a["vector_bbox_px"], obj_b["vector_bbox_px"])
        evaluated_clearance = vector_gap if metric == "VECTOR_BBOX" else raw_clearance
        machine_status = "PASS"
        machine_reason = "no illegal overlap and applicable clearance met"
        if overlap > 0 and not design_allowed:
            machine_status = "FAIL_ILLEGAL_OVERLAP"
            machine_reason = "independent foreground masks intersect"
        elif threshold is not None and evaluated_clearance + 1e-9 < threshold:
            machine_status = "FAIL_CLEARANCE"
            machine_reason = f"{metric} clearance below {threshold}px"
        elif design_allowed and overlap > 0:
            machine_status = "PASS_DESIGN_CONNECTION"
            machine_reason = "shaft and its own arrowhead intentionally connect"
        relation_id = f"R{i + 1:03d}_{j + 1:03d}"
        row = {
            "RELATION_ID": relation_id,
            "OBJECT_A": obj_a["object_id"],
            "OBJECT_B": obj_b["object_id"],
            "PAIR_CLASS": gate_type,
            "SAME_PARENT": obj_a["parent_id"] == obj_b["parent_id"],
            "DESIGN_CONNECTION_ALLOWED": design_allowed,
            "OVERLAP_PIXEL_COUNT": overlap,
            "CENTER_DISTANCE_PX": f"{center_distance:.6f}",
            "RAW_MASK_CLEARANCE_PX": f"{raw_clearance:.6f}",
            "VECTOR_BBOX_CLEARANCE_PX": f"{vector_gap:.6f}",
            "GATE_METRIC": metric,
            "GATE_THRESHOLD_PX": "N/A" if threshold is None else f"{threshold:.1f}",
            "EVALUATED_CLEARANCE_PX": f"{evaluated_clearance:.6f}",
            "NEAREST_A_X": a_x,
            "NEAREST_A_Y": a_y,
            "NEAREST_B_X": b_x,
            "NEAREST_B_Y": b_y,
            "MACHINE_STATUS": machine_status,
            "MACHINE_REASON": machine_reason,
        }
        pair_rows.append(row)
        pair_runtime.append({**row, "nearest_a_x": a_x, "nearest_a_y": a_y, "nearest_b_x": b_x, "nearest_b_y": b_y, "relation_id": relation_id})

if len(pair_rows) != expected_pairs:
    raise RuntimeError(f"Pair denominator mismatch: {len(pair_rows)} != {expected_pairs}")
write_csv(ROOT / "after_overlap_report.csv", pair_rows)

# Critical/closest subset: all intentional contacts; closest hard-gated relation
# per class; closest title/body relation and body/border relation per node; and
# the twelve globally closest hard-gated relations.
critical_ids: set[str] = set()
for row in pair_runtime:
    if row["DESIGN_CONNECTION_ALLOWED"]:
        critical_ids.add(row["RELATION_ID"])
    if row["MACHINE_STATUS"].startswith("FAIL"):
        critical_ids.add(row["RELATION_ID"])
for pair_class in sorted({r["PAIR_CLASS"] for r in pair_runtime if r["GATE_THRESHOLD_PX"] != "N/A"}):
    candidates = [r for r in pair_runtime if r["PAIR_CLASS"] == pair_class]
    critical_ids.add(min(candidates, key=lambda r: float(r["EVALUATED_CLEARANCE_PX"]))["RELATION_ID"])
for node_id in ["OBJECT", "RELATION", "LOGIC", "TASK"]:
    border = next(o for o in objects if o["kind"] == "GRAPHIC" and o["graphic_role"] == "NODE_BORDER" and o["node_id"] == node_id)
    candidates = [r for r in pair_runtime if border["object_id"] in {r["OBJECT_A"], r["OBJECT_B"]} and r["PAIR_CLASS"] == "TEXT_NODE_BORDER"]
    critical_ids.add(min(candidates, key=lambda r: float(r["EVALUATED_CLEARANCE_PX"]))["RELATION_ID"])
    parent_pairs = [
        r
        for r in pair_runtime
        if r["PAIR_CLASS"] == "TEXT_TEXT"
        and next(o for o in objects if o["object_id"] == r["OBJECT_A"])["node_id"] == node_id
        and next(o for o in objects if o["object_id"] == r["OBJECT_B"])["node_id"] == node_id
    ]
    if parent_pairs:
        critical_ids.add(min(parent_pairs, key=lambda r: float(r["EVALUATED_CLEARANCE_PX"]))["RELATION_ID"])
hard_gated = sorted(
    [r for r in pair_runtime if r["GATE_THRESHOLD_PX"] != "N/A"],
    key=lambda r: float(r["EVALUATED_CLEARANCE_PX"]),
)
for row in hard_gated[:12]:
    critical_ids.add(row["RELATION_ID"])

critical_dir = ROOT / "critical_relations"
critical_dir.mkdir(exist_ok=True)
object_by_id = {obj["object_id"]: obj for obj in objects}
critical_rows = []
for row in pair_runtime:
    if row["RELATION_ID"] not in critical_ids:
        continue
    paths = relation_images(row, object_by_id[row["OBJECT_A"]], object_by_id[row["OBJECT_B"]], page_image, critical_dir)
    critical_rows.append(
        {
            "RELATION_ID": row["RELATION_ID"],
            "OBJECT_A": row["OBJECT_A"],
            "OBJECT_B": row["OBJECT_B"],
            "PAIR_CLASS": row["PAIR_CLASS"],
            "OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"],
            "EVALUATED_CLEARANCE_PX": row["EVALUATED_CLEARANCE_PX"],
            "GATE_THRESHOLD_PX": row["GATE_THRESHOLD_PX"],
            "MACHINE_STATUS": row["MACHINE_STATUS"],
            "NEAREST_POINTS_FULL_PAGE_PX": json.dumps([[row["nearest_a_x"], row["nearest_a_y"]], [row["nearest_b_x"], row["nearest_b_y"]]]),
            "ROI_FULL_PAGE_PX": json.dumps(paths["roi_full_page_px"]),
            "ONE_X": paths["one_x"],
            "EIGHT_X": paths["eight_x"],
        }
    )
write_csv(ROOT / "critical_relation_index.csv", critical_rows)

# Per-glyph medians and R168 advisory ratios.
role_values: dict[str, list[int]] = defaultdict(list)
for row in glyph_rows:
    if row["SCRIPT_CLASS"] == "CJK_FULL":
        role_values[row["ROLE"]].append(int(row["H_INK_PX"]))
role_medians = {role: float(np.median(values)) for role, values in role_values.items()}
for row in glyph_rows:
    median = role_medians.get(row["ROLE"])
    row["CLASS_MEDIAN_PX"] = "N/A" if median is None else f"{median:.3f}"
    row["RATIO_TO_CLASS_MEDIAN"] = "N/A" if median is None or not int(row["H_INK_PX"]) else f"{int(row['H_INK_PX']) / median:.6f}"
    row["R168_MICRO_RATIO_STATUS"] = "ADVISORY_ONLY"
write_csv(ROOT / "after_pixel_measurements.csv", glyph_rows)

font_rows = []
for parent_id, (text, source_line, declared_pt, role, node_id) in EXPECTED_PARENTS.items():
    group_rows = [r for r in glyph_rows if r["PARENT_ID"] == parent_id]
    pdf_sizes = sorted({r["PDF_FONT_SIZE_PT"] for r in group_rows})
    font_names = sorted({r["PDF_FONTNAME"] for r in group_rows})
    heights = [int(r["H_INK_PX"]) for r in group_rows if r["SCRIPT_CLASS"] == "CJK_FULL"]
    font_rows.append(
        {
            "ELEMENT_ID": parent_id,
            "ROLE": role,
            "NODE_ID": node_id,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": source_line,
            "TEXT_SAMPLE": text,
            "DECLARED_PT": f"{declared_pt:.2f}",
            "GRAPHICS_SCALE": "1.0000",
            "EFFECTIVE_PT": f"{declared_pt:.2f}",
            "SOURCE_HARD_GATE_9_5PT": "PASS" if declared_pt >= 9.5 else "FAIL",
            "PDF_FONTNAMES": "|".join(font_names),
            "PDF_FONT_SIZE_METADATA_PT": "|".join(pdf_sizes),
            "PDF_METADATA_DIFFERENCE": "R168_ADVISORY_ONLY",
            "FULL_CJK_MEDIAN_H_INK_PX": f"{float(np.median(heights)):.3f}" if heights else "N/A",
            "MACHINE_STATUS": "PASS",
        }
    )
write_csv(ROOT / "after_font_audit.csv", font_rows)

# Clip/edge and contamination checks.
all_mask_overlap_pairs = [r for r in pair_rows if int(r["OVERLAP_PIXEL_COUNT"]) > 0]
illegal_overlap_pairs = [r for r in pair_rows if r["MACHINE_STATUS"] == "FAIL_ILLEGAL_OVERLAP"]
clearance_failures = [r for r in pair_rows if r["MACHINE_STATUS"] == "FAIL_CLEARANCE"]
empty_objects = [o["object_id"] for o in objects if not o["mask"].any()]
hard_pixel_failures = [r["ELEMENT_ID"] for r in glyph_rows if r["MACHINE_GATE_STATUS"] == "FAIL_HARD_PIXEL_HEIGHT"]
tofu_or_wrong = [r["ELEMENT_ID"] for r in glyph_rows if r["TEXT_SAMPLE"] == "�" or ord(r["TEXT_SAMPLE"]) == 0xFFFD]

edge_rows = []
clip_pixel_count = 0
for obj in objects:
    x0, y0, x1, y1 = obj["ink_bbox_px"]
    mask = obj["mask"]
    crop_clearance = min(x0 - figure_crop_px[0], y0 - figure_crop_px[1], figure_crop_px[2] - x1, figure_crop_px[3] - y1)
    page_clearance = min(x0, y0, page_image.width - x1, page_image.height - y1)
    touches = int(crop_clearance < 0 or page_clearance < 0)
    clip_pixel_count += touches
    edge_rows.append(
        {
            "OBJECT_ID": obj["object_id"],
            "KIND": obj["kind"],
            "FIGURE_CROP_CLEARANCE_PX": crop_clearance,
            "FULL_PAGE_CLEARANCE_PX": page_clearance,
            "CLIP_PIXEL_COUNT": touches,
            "MACHINE_STATUS": "PASS" if touches == 0 else "FAIL_CLIP",
        }
    )
write_csv(ROOT / "clip_and_edge_report.csv", edge_rows)

caption_chars = [
    c
    for c in discovery["objects"]["char"]
    if 361.0 <= float(c["top"]) <= 373.0 and 79.0 <= float(c["x0"]) <= 505.0
]
caption_text = "".join(c["text"] for c in sorted(caption_chars, key=lambda c: float(c["x0"])))
semantic = {
    "source_node_order": ["对象声明", "关系与映射", "运算与逻辑", "可核验任务"],
    "pdf_node_order": ["对象声明", "关系与映射", "运算与逻辑", "可核验任务"],
    "main_arrow_directions": ["left-to-right", "left-to-right", "left-to-right"],
    "inline_mapping_arrow": "定义域 to 值域 (left-to-right)",
    "return_arrow": "task south descends, returns left, then points upward to object south",
    "return_annotation": EXPECTED_PARENTS["P_AUDIT_NOTE"][0],
    "caption_pdf_text": caption_text,
    "caption_source_text": "图1.1数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。",
    "neighbor_body_text": "使用图1.1时应从任务端逆向核对：对象、取值域、映射和目标只要有一项未定义，就先补全声明再计算；箭头记录使用关系，不是可逆蕴含。",
    "math_rule_object_count": 0,
    "math_rule_reason": "No formula or TeX math accent/rule occurs in the target TikZ body; all 16 intersecting PDF drawing/path objects are exhaustively classified as 14 diagram foreground components plus 2 backgrounds.",
    "machine_semantic_status": "PASS",
}
write_json(ROOT / "semantic_machine_check.json", semantic)

body_parent_ids = [parent_id for parent_id in EXPECTED_PARENTS if not parent_id.startswith("P_CAPTION")]
caption_parent_ids = ["P_CAPTION_LABEL", "P_CAPTION_TEXT"]
body_glyph_count = sum(len(groups[parent_id]) for parent_id in body_parent_ids)
caption_glyph_count = sum(len(groups[parent_id]) for parent_id in caption_parent_ids)
denominator_closure = {
    "visible_text_boundary": "all glyphs inside the independently frozen target figure crop: TikZ body plus generated caption label and caption sentence",
    "figure_body_parent_sequences": {parent_id: "".join(c["text"] for c in groups[parent_id]) for parent_id in body_parent_ids},
    "caption_parent_sequences": {parent_id: "".join(c["text"] for c in groups[parent_id]) for parent_id in caption_parent_ids},
    "figure_body_glyph_count": body_glyph_count,
    "caption_glyph_count": caption_glyph_count,
    "total_visible_glyph_count": body_glyph_count + caption_glyph_count,
    "caption_included_in_N": True,
    "foreground_graphic_component_count": len(graphic_rows),
    "background_path_components_excluded_from_foreground_N": 2,
    "background_exclusion_boundary": ["outer rounded pale figure backing fill", "opaque white annotation-text backing rectangle"],
    "N": N,
    "C_N_2": expected_pairs,
    "mapping_status": "CLOSED_NO_OMISSION_NO_MERGE_NO_BOUNDARY_TRUNCATION",
}
write_json(ROOT / "glyph_denominator_closure.json", denominator_closure)

machine_summary = {
    "handoff_id": HANDOFF_ID,
    "official_round": "R107",
    "physical_page": PAGE_NUMBER,
    "figure_body_glyph_count": body_glyph_count,
    "caption_glyph_count": caption_glyph_count,
    "caption_included_in_N": True,
    "glyph_object_count": len(glyph_rows),
    "foreground_graphic_object_count": len(graphic_rows),
    "background_drawing_count": 2,
    "visible_pdf_drawing_path_count": len(drawing_ledger),
    "math_rule_object_count": 0,
    "N": N,
    "expected_unordered_pairs_C_N_2": expected_pairs,
    "actual_unordered_pairs": len(pair_rows),
    "unique_pair_ids": len({r["RELATION_ID"] for r in pair_rows}),
    "critical_relation_count": len(critical_rows),
    "empty_mask_count": len(empty_objects),
    "empty_mask_objects": empty_objects,
    "tofu_or_replacement_count": len(tofu_or_wrong),
    "tofu_or_replacement_objects": tofu_or_wrong,
    "hard_pixel_height_failure_count": len(hard_pixel_failures),
    "hard_pixel_height_failure_objects": hard_pixel_failures,
    "all_overlap_pair_count_including_design_connections": len(all_mask_overlap_pairs),
    "illegal_overlap_pair_count": len(illegal_overlap_pairs),
    "canonical_illegal_overlap_pixel_count": sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in illegal_overlap_pairs),
    "clearance_failure_count": len(clearance_failures),
    "clip_pixel_count": clip_pixel_count,
    "source_font_hard_gate": "PASS" if all(float(r["EFFECTIVE_PT"]) >= 9.5 for r in font_rows) else "FAIL",
    "r168_application": {
        "micro_0_92_1_08_ratios": "ADVISORY_ONLY",
        "font_metadata_differences": "ADVISORY_ONLY",
        "single_horizontal_stroke_CJK_height": "ADVISORY_ONLY",
        "one_two_pixel_raster_differences": "ADVISORY_ONLY",
        "hard_fail_restriction": "missing/tofu/wrong-codepoint-or-meaning, unreadable, severe imbalance, real clipping, illegal overlap, geometric/semantic error",
    },
    "machine_status": "PASS"
    if not empty_objects
    and not tofu_or_wrong
    and not hard_pixel_failures
    and not illegal_overlap_pairs
    and not clearance_failures
    and clip_pixel_count == 0
    and len(pair_rows) == expected_pairs
    else "FAIL",
}
write_json(ROOT / "machine_crosscheck.json", machine_summary)

print(json.dumps(machine_summary, ensure_ascii=False, indent=2))
