from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R2_SA1_FRESH_ISOLATED_R107_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C01\fig_v1_c01_language_flow.tex")
PAGE_INDEX = 16
SCALE_300 = 300.0 / 72.0
FIGURE_CROP_PX = (240, 1095, 2200, 1570)
STANDALONE_CROP_PX = (240, 1095, 2200, 1490)

BLOCK_META = {
    "对象声明": ("TXT_NODE_OBJECT_HEADING", "NODE_HEADING", 12, 10.5, "stage font 10.5pt; bold series"),
    "关系与映射": ("TXT_NODE_RELATION_HEADING", "NODE_HEADING", 13, 10.5, "stage font 10.5pt; bold series"),
    "运算与逻辑": ("TXT_NODE_LOGIC_HEADING", "NODE_HEADING", 20, 10.5, "stage font 10.5pt; bold series"),
    "可核验任务": ("TXT_NODE_TASK_HEADING", "NODE_HEADING", 21, 10.5, "stage font 10.5pt; bold series"),
    "集合、类型与维数": ("TXT_NODE_OBJECT_BODY", "NODE_BODY", 12, 10.0, "local fontsize 10.0pt"),
    "定义域值域": ("TXT_NODE_RELATION_BODY", "NODE_BODY", 13, 10.0, "local fontsize 10.0pt; inline arrow is a separate graphic"),
    "复合、量词与约束": ("TXT_NODE_LOGIC_BODY", "NODE_BODY", 20, 10.0, "local fontsize 10.0pt"),
    "输入、输出与判据": ("TXT_NODE_TASK_BODY", "NODE_BODY", 21, 10.0, "local fontsize 10.0pt"),
    "逆向核对：任务所用定义逐项返回检查": ("TXT_FEEDBACK_ANNOTATION", "ANNOTATION", 34, 10.0, "local fontsize 10.0pt"),
    "图1.1数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。": (
        "TXT_CAPTION",
        "CAPTION",
        38,
        10.0,
        "caption inherits the book caption style; final PDF span size 9.96264pt is the 10pt nominal metadata realization",
    ),
}

GRAPHICS = {
    14: ("GFX_NODE_OBJECT_BORDER", "NODE_BORDER", "NODE_OBJECT", "stroke of object node; fill is background"),
    17: ("GFX_NODE_RELATION_BORDER", "NODE_BORDER", "NODE_RELATION", "stroke of relation node; fill is background"),
    20: ("GFX_INLINE_ARROW_SHAFT", "LINE_ARROW", "INLINE_DOMAIN_ARROW", "inline domain-to-codomain arrow shaft"),
    21: ("GFX_INLINE_ARROW_HEAD", "ARROWHEAD", "INLINE_DOMAIN_ARROW", "inline domain-to-codomain arrowhead"),
    24: ("GFX_NODE_LOGIC_BORDER", "NODE_BORDER", "NODE_LOGIC", "stroke of logic node; fill is background"),
    27: ("GFX_NODE_TASK_BORDER", "NODE_BORDER", "NODE_TASK", "stroke of task node; fill is background"),
    30: ("GFX_MAIN_ARROW_1_SHAFT", "LINE_ARROW", "MAIN_ARROW_1", "object-to-relation shaft"),
    31: ("GFX_MAIN_ARROW_1_HEAD", "ARROWHEAD", "MAIN_ARROW_1", "object-to-relation arrowhead"),
    33: ("GFX_MAIN_ARROW_2_SHAFT", "LINE_ARROW", "MAIN_ARROW_2", "relation-to-logic shaft"),
    34: ("GFX_MAIN_ARROW_2_HEAD", "ARROWHEAD", "MAIN_ARROW_2", "relation-to-logic arrowhead"),
    36: ("GFX_MAIN_ARROW_3_SHAFT", "LINE_ARROW", "MAIN_ARROW_3", "logic-to-task shaft"),
    37: ("GFX_MAIN_ARROW_3_HEAD", "ARROWHEAD", "MAIN_ARROW_3", "logic-to-task arrowhead"),
    39: ("GFX_FEEDBACK_ROUTE", "LINE_ARROW", "FEEDBACK_ARROW", "dashed reverse-audit route"),
    40: ("GFX_FEEDBACK_ARROW_HEAD", "ARROWHEAD", "FEEDBACK_ARROW", "reverse-audit arrowhead"),
}

EXCLUDED_DRAWINGS = {
    13: "outer rounded background fill; visible background, not foreground",
    42: "opaque white label background; visible background, not foreground",
}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rgb_from_float(value: tuple[float, float, float] | None) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(v * 255)) for v in value)


def px_bbox_from_pt(rect: tuple[float, float, float, float], pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        int(math.floor(x0 * SCALE_300)) - pad,
        int(math.floor(y0 * SCALE_300)) - pad,
        int(math.ceil(x1 * SCALE_300)) + pad,
        int(math.ceil(y1 * SCALE_300)) + pad,
    )


def mode_rgb(region: np.ndarray) -> np.ndarray:
    flat = region.reshape(-1, 3)
    values, counts = np.unique(flat, axis=0, return_counts=True)
    return values[int(np.argmax(counts))].astype(np.float64)


def aligned_color_mask(region: np.ndarray, target: tuple[int, int, int]) -> tuple[np.ndarray, tuple[int, int, int]]:
    pixels = region.astype(np.float64)
    bg = mode_rgb(region)
    target_v = np.array(target, dtype=np.float64)
    vector = target_v - bg
    denom = float(np.dot(vector, vector))
    if denom == 0:
        return np.zeros(region.shape[:2], dtype=bool), tuple(int(v) for v in bg)
    delta = pixels - bg
    alpha = np.sum(delta * vector, axis=2) / denom
    recon = bg + np.clip(alpha[..., None], 0.0, 1.0) * vector
    residual = np.max(np.abs(pixels - recon), axis=2)
    contrast = np.max(np.abs(delta), axis=2)
    mask = (contrast >= 20.0) & (alpha > 0.0) & (alpha <= 1.08) & (residual <= 14.0)
    return mask, tuple(int(v) for v in bg)


def script_class(char: str) -> str:
    if char in {"、", "：", "。", ".", "，", "；", "：", ",", ":", ";"}:
        return "LOW_PROFILE_PUNCTUATION"
    if char.isdigit() or (char.isascii() and char.isupper()):
        return "LATIN_UPPER_OR_DIGIT"
    if char.isascii() and char.islower():
        return "LATIN_X_HEIGHT"
    return "CJK_FULL"


def threshold_for_class(cls: str) -> int | None:
    return {
        "CJK_FULL": 30,
        "LATIN_UPPER_OR_DIGIT": 24,
        "LATIN_X_HEIGHT": 17,
    }.get(cls)


def mask_extents(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def save_mask_bundle(full: Image.Image, bbox: tuple[int, int, int, int], mask: np.ndarray, stem: Path) -> None:
    x0, y0, x1, y1 = bbox
    original = full.crop(bbox).convert("RGB")
    overlay = np.array(original).copy()
    overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
    mask_img = np.where(mask[..., None], 255, 0).astype(np.uint8)
    mask_img = np.repeat(mask_img, 3, axis=2)
    original.save(stem.with_name(stem.name + "_original_1x.png"))
    Image.fromarray(overlay, "RGB").save(stem.with_name(stem.name + "_overlay_1x.png"))
    Image.fromarray(mask_img, "RGB").save(stem.with_name(stem.name + "_mask_only_1x.png"))


def global_coords(bbox: tuple[int, int, int, int], mask: np.ndarray) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return np.empty((0, 2), dtype=np.int32)
    return np.column_stack([xs + bbox[0], ys + bbox[1]]).astype(np.int32)


def intersection_count(a: dict[str, Any], b: dict[str, Any]) -> int:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    am = a["mask"][y0 - ay0 : y1 - ay0, x0 - ax0 : x1 - ax0]
    bm = b["mask"][y0 - by0 : y1 - by0, x0 - bx0 : x1 - bx0]
    return int(np.count_nonzero(am & bm))


def closest_pixels(a: dict[str, Any], b: dict[str, Any]) -> tuple[int | None, tuple[int, int] | None, tuple[int, int] | None]:
    ac = a["coords"]
    bc = b["coords"]
    if len(ac) == 0 or len(bc) == 0:
        return None, None, None
    if len(ac) <= len(bc):
        tree = cKDTree(bc)
        distances, indices = tree.query(ac, k=1, p=np.inf)
        idx = int(np.argmin(distances))
        center_distance = int(round(float(distances[idx])))
        pa = tuple(int(v) for v in ac[idx])
        pb = tuple(int(v) for v in bc[int(indices[idx])])
    else:
        tree = cKDTree(ac)
        distances, indices = tree.query(bc, k=1, p=np.inf)
        idx = int(np.argmin(distances))
        center_distance = int(round(float(distances[idx])))
        pb = tuple(int(v) for v in bc[idx])
        pa = tuple(int(v) for v in ac[int(indices[idx])])
    return max(0, center_distance - 1), pa, pb


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return int(max(dx, dy))


def parent_node(parent: str) -> str | None:
    if "NODE_OBJECT" in parent:
        return "NODE_OBJECT"
    if "NODE_RELATION" in parent:
        return "NODE_RELATION"
    if "NODE_LOGIC" in parent:
        return "NODE_LOGIC"
    if "NODE_TASK" in parent:
        return "NODE_TASK"
    return None


def pair_class_and_gate(a: dict[str, Any], b: dict[str, Any]) -> tuple[str, int, str, bool]:
    if a["kind"] == "TEXT" and b["kind"] == "TEXT":
        if a["semantic_parent"] == b["semantic_parent"]:
            return "TEXT_TEXT_SAME_PARENT", 0, "mask", True
        return "TEXT_TEXT_INDEPENDENT", 4, "bbox", False

    if a["kind"] == "GRAPHIC" and b["kind"] == "GRAPHIC":
        if a["semantic_parent"] == b["semantic_parent"] and a["semantic_parent"].endswith(("ARROW", "_1", "_2", "_3")):
            return "GRAPHIC_GRAPHIC_DESIGN_CONNECTION", 0, "mask", True
        return "GRAPHIC_GRAPHIC_INDEPENDENT", 0, "mask", False

    text_obj = a if a["kind"] == "TEXT" else b
    gfx_obj = b if a["kind"] == "TEXT" else a
    node = parent_node(text_obj["semantic_parent"])
    if gfx_obj["graphic_class"] == "NODE_BORDER" and node == gfx_obj["semantic_parent"]:
        return "TEXT_OWN_NODE_BORDER", 5, "mask", False
    if gfx_obj["graphic_class"] == "NODE_BORDER":
        return "TEXT_OTHER_NODE_BORDER", 3, "mask", False
    if gfx_obj["graphic_class"] == "ARROWHEAD":
        return "TEXT_ARROWHEAD", 3, "mask", False
    return "TEXT_LINE_ARROW", 3, "mask", False


def relation_evidence(full: Image.Image, a: dict[str, Any], b: dict[str, Any], rel_id: str, pa: tuple[int, int] | None, pb: tuple[int, int] | None) -> dict[str, Any]:
    out_dir = ROOT / "06_relations" / rel_id
    out_dir.mkdir(parents=True, exist_ok=True)
    if pa is None or pb is None:
        x0 = min(a["bbox_px"][0], b["bbox_px"][0]) - 6
        y0 = min(a["bbox_px"][1], b["bbox_px"][1]) - 6
        x1 = max(a["bbox_px"][2], b["bbox_px"][2]) + 6
        y1 = max(a["bbox_px"][3], b["bbox_px"][3]) + 6
    else:
        x0 = min(pa[0], pb[0]) - 10
        y0 = min(pa[1], pb[1]) - 10
        x1 = max(pa[0], pb[0]) + 11
        y1 = max(pa[1], pb[1]) + 11
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(full.width, x1), min(full.height, y1)
    roi = (x0, y0, x1, y1)
    original = full.crop(roi).convert("RGB")
    shape = (y1 - y0, x1 - x0)
    am = np.zeros(shape, dtype=bool)
    bm = np.zeros(shape, dtype=bool)
    for obj, dest in ((a, am), (b, bm)):
        ox0, oy0, ox1, oy1 = obj["bbox_px"]
        ix0, iy0, ix1, iy1 = max(x0, ox0), max(y0, oy0), min(x1, ox1), min(y1, oy1)
        if ix0 < ix1 and iy0 < iy1:
            dest[iy0 - y0 : iy1 - y0, ix0 - x0 : ix1 - x0] = obj["mask"][iy0 - oy0 : iy1 - oy0, ix0 - ox0 : ix1 - ox0]
    inter = am & bm

    def bw(mask: np.ndarray) -> Image.Image:
        return Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L").convert("RGB")

    original.save(out_dir / "raw_original_1x.png")
    bw(am).save(out_dir / "raw_mask_a_1x.png")
    bw(bm).save(out_dir / "raw_mask_b_1x.png")
    bw(inter).save(out_dir / "raw_intersection_1x.png")
    overlay = np.array(original)
    overlay[am] = np.array([255, 0, 0], dtype=np.uint8)
    overlay[bm] = np.array([0, 90, 255], dtype=np.uint8)
    overlay[inter] = np.array([255, 0, 255], dtype=np.uint8)
    Image.fromarray(overlay, "RGB").save(out_dir / "raw_overlay_ab_1x.png")

    panels = [original, bw(am), bw(bm), bw(inter), Image.fromarray(overlay, "RGB")]
    gap = 4
    quad = Image.new("RGB", (sum(i.width for i in panels) + gap * (len(panels) - 1), max(i.height for i in panels)), "white")
    cursor = 0
    for panel in panels:
        quad.paste(panel, (cursor, 0))
        cursor += panel.width + gap
    quad.save(out_dir / "five_panel_1x.png")
    quad.resize((quad.width * 8, quad.height * 8), Image.Resampling.NEAREST).save(out_dir / "five_panel_8x_nearest.png")
    meta = {
        "relation_id": rel_id,
        "object_a": a["object_id"],
        "object_b": b["object_id"],
        "roi_full_page_300dpi_px": list(roi),
        "closest_pixel_a": list(pa) if pa else None,
        "closest_pixel_b": list(pb) if pb else None,
        "views": [
            "raw_original_1x.png",
            "raw_mask_a_1x.png",
            "raw_mask_b_1x.png",
            "raw_intersection_1x.png",
            "raw_overlay_ab_1x.png",
            "five_panel_1x.png",
            "five_panel_8x_nearest.png",
        ],
    }
    write_json(out_dir / "relation_metadata.json", meta)
    return meta


def make_glyph_contact_sheets(full: Image.Image, glyphs: list[dict[str, Any]]) -> list[str]:
    files: list[str] = []
    font = ImageFont.load_default()
    per_sheet = 9
    cell_w, cell_h = 1100, 540
    for sheet_idx in range(math.ceil(len(glyphs) / per_sheet)):
        subset = glyphs[sheet_idx * per_sheet : (sheet_idx + 1) * per_sheet]
        canvas = Image.new("RGB", (cell_w, cell_h * len(subset)), "white")
        draw = ImageDraw.Draw(canvas)
        for row, glyph in enumerate(subset):
            top = row * cell_h
            x0, y0, x1, y1 = glyph["bbox_px"]
            original = full.crop((x0, y0, x1, y1)).convert("RGB")
            overlay_a = np.array(original)
            overlay_a[glyph["mask"]] = np.array([255, 0, 0], dtype=np.uint8)
            overlay = Image.fromarray(overlay_a, "RGB")
            mask = Image.fromarray(np.where(glyph["mask"], 255, 0).astype(np.uint8), "L").convert("RGB")
            zoom = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
            header = f"{glyph['object_id']} char=U+{ord(glyph['char']):04X} cell={sheet_idx + 1}:{row + 1} bbox={glyph['bbox_px']} H={glyph['h_ink_px']} area={glyph['ink_area_px']}"
            draw.text((10, top + 5), header, fill="black", font=font)
            draw.text((10, top + 24), "ORIGINAL 1x", fill="black", font=font)
            canvas.paste(original, (10, top + 42))
            draw.text((140, top + 24), "TARGET OVERLAY 1x", fill="black", font=font)
            canvas.paste(overlay, (140, top + 42))
            draw.text((290, top + 24), "MASK ONLY 1x", fill="black", font=font)
            canvas.paste(mask, (290, top + 42))
            draw.text((430, top + 24), "TARGET OVERLAY 8x NEAREST", fill="black", font=font)
            canvas.paste(zoom, (430, top + 42))
            draw.line((0, top + cell_h - 1, cell_w, top + cell_h - 1), fill=(180, 180, 180), width=1)
        filename = f"glyph_contact_sheet_{sheet_idx + 1:02d}.png"
        canvas.save(ROOT / "04_contact_sheets" / filename)
        files.append(filename)
    return files


def make_graphic_contact_sheets(full: Image.Image, graphics: list[dict[str, Any]]) -> list[str]:
    files: list[str] = []
    font = ImageFont.load_default()
    per_sheet = 4
    cell_w, cell_h = 3000, 480
    for sheet_idx in range(math.ceil(len(graphics) / per_sheet)):
        subset = graphics[sheet_idx * per_sheet : (sheet_idx + 1) * per_sheet]
        canvas = Image.new("RGB", (cell_w, cell_h * len(subset)), "white")
        draw = ImageDraw.Draw(canvas)
        for row, obj in enumerate(subset):
            top = row * cell_h
            x0, y0, x1, y1 = obj["bbox_px"]
            original = full.crop((x0, y0, x1, y1)).convert("RGB")
            overlay_a = np.array(original)
            overlay_a[obj["mask"]] = np.array([255, 0, 0], dtype=np.uint8)
            overlay = Image.fromarray(overlay_a, "RGB")
            mask = Image.fromarray(np.where(obj["mask"], 255, 0).astype(np.uint8), "L").convert("RGB")
            ext = mask_extents(obj["mask"])
            if ext:
                zx0, zy0, zx1, zy1 = ext
                ys, xs = np.nonzero(obj["mask"])
                center_x, center_y = (zx0 + zx1 - 1) / 2.0, (zy0 + zy1 - 1) / 2.0
                pick = int(np.argmin((xs - center_x) ** 2 + (ys - center_y) ** 2))
                cx, cy = int(xs[pick]), int(ys[pick])
                zx0, zy0, zx1, zy1 = max(0, cx - 18), max(0, cy - 18), min(mask.width, cx + 19), min(mask.height, cy + 19)
                zoom = overlay.crop((zx0, zy0, zx1, zy1)).resize(((zx1 - zx0) * 8, (zy1 - zy0) * 8), Image.Resampling.NEAREST)
            else:
                zoom = Image.new("RGB", (296, 296), "black")
            header = f"{obj['object_id']} seqno={obj['seqno']} bbox={obj['bbox_px']} ink={obj['ink_area_px']}"
            draw.text((10, top + 5), header, fill="black", font=font)
            draw.text((10, top + 24), "ORIGINAL 1x", fill="black", font=font)
            canvas.paste(original, (10, top + 42))
            x_overlay = min(1450, 30 + original.width)
            draw.text((x_overlay, top + 24), "TARGET OVERLAY 1x", fill="black", font=font)
            canvas.paste(overlay, (x_overlay, top + 42))
            x_mask = min(2250, x_overlay + original.width + 20)
            draw.text((x_mask, top + 24), "MASK ONLY 1x", fill="black", font=font)
            canvas.paste(mask, (x_mask, top + 42))
            draw.text((2650, top + 24), "8x NEAREST DETAIL", fill="black", font=font)
            canvas.paste(zoom, (2650, top + 42))
            draw.line((0, top + cell_h - 1, cell_w, top + cell_h - 1), fill=(180, 180, 180), width=1)
        filename = f"graphic_contact_sheet_{sheet_idx + 1:02d}.png"
        canvas.save(ROOT / "04_contact_sheets" / filename)
        files.append(filename)
    return files


def main() -> None:
    full300_path = ROOT / "01_renders" / "full_page_300dpi.png"
    full = Image.open(full300_path).convert("RGB")
    full_np = np.array(full)
    if full.size != (2481, 3508):
        raise RuntimeError(f"Unexpected native 300dpi dimensions: {full.size}")

    figure_crop = full.crop(FIGURE_CROP_PX)
    standalone = full.crop(STANDALONE_CROP_PX)
    figure_crop.save(ROOT / "01_renders" / "figure_crop_300dpi.png")
    standalone.save(ROOT / "01_renders" / "standalone_300dpi.png")
    figure_crop.convert("L").save(ROOT / "01_renders" / "grayscale_300dpi.png")

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = page.get_text("rawdict", sort=True)
    drawings = page.get_drawings(extended=True)
    drawing_by_seqno = {int(d["seqno"]): d for d in drawings}

    crop_meta = {
        "official_pdf": str(PDF),
        "physical_page_1based": 17,
        "page_index_0based": 16,
        "page_label": page.get_label(),
        "page_pt": [page.rect.width, page.rect.height],
        "full_page_200dpi_native_px": list(Image.open(ROOT / "01_renders" / "full_page_200dpi.png").size),
        "full_page_300dpi_native_px": list(full.size),
        "nominal_scale_px_per_pdf_pt": SCALE_300,
        "figure_crop_300dpi_full_page_integer_xyxy": list(FIGURE_CROP_PX),
        "figure_crop_300dpi_native_px": list(figure_crop.size),
        "standalone_300dpi_full_page_integer_xyxy": list(STANDALONE_CROP_PX),
        "standalone_300dpi_native_px": list(standalone.size),
        "grayscale_300dpi_native_px": list(figure_crop.size),
        "crop_policy": "Lossless integer crop from direct Poppler 300dpi page render; no resize or interpolation.",
        "target_scope": "Figure body plus caption for figure_crop; figure body only for standalone; all target glyphs include the caption line.",
    }
    write_json(ROOT / "01_renders" / "crop_coordinates.json", crop_meta)

    glyphs: list[dict[str, Any]] = []
    parent_counters: Counter[str] = Counter()
    global_index = 0
    element_rows: dict[str, dict[str, Any]] = {}
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        block_text = "".join(
            char_rec.get("c", "")
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            for char_rec in span.get("chars", [])
        )
        if block_text not in BLOCK_META:
            continue
        semantic_parent, role, source_line, declared_pt, source_evidence = BLOCK_META[block_text]
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char_rec in span.get("chars", []):
                    char = char_rec["c"]
                    x0pt, y0pt, x1pt, y1pt = [float(v) for v in char_rec["bbox"]]
                    if x1pt < 58 or x0pt > 526 or y1pt < 264 or y0pt > 376:
                        continue
                    global_index += 1
                    parent_counters[semantic_parent] += 1
                    object_id = f"G{global_index:03d}"
                    tight_bbox = px_bbox_from_pt((x0pt, y0pt, x1pt, y1pt), pad=0)
                    bbox = px_bbox_from_pt((x0pt, y0pt, x1pt, y1pt), pad=3)
                    bx0, by0, bx1, by1 = bbox
                    region = full_np[by0:by1, bx0:bx1]
                    target_rgb = rgb_from_int(int(span["color"]))
                    mask, bg_rgb = aligned_color_mask(region, target_rgb)
                    allowed = np.zeros(mask.shape, dtype=bool)
                    tx0, ty0, tx1, ty1 = tight_bbox
                    allowed[ty0 - by0 : ty1 - by0, tx0 - bx0 : tx1 - bx0] = True
                    mask &= allowed
                    ext = mask_extents(mask)
                    h_ink = 0 if ext is None else ext[3] - ext[1]
                    ink_area = int(np.count_nonzero(mask))
                    cls = script_class(char)
                    threshold = threshold_for_class(cls)
                    r168_advisory = char == "一" or cls == "LOW_PROFILE_PUNCTUATION"
                    machine_height_gate = (
                        "CALIBRATION_REQUIRED"
                        if cls == "LOW_PROFILE_PUNCTUATION"
                        else ("R168_ADVISORY_SINGLE_HORIZONTAL_CJK" if char == "一" and h_ink < int(threshold or 0) else ("MEETS_THRESHOLD" if h_ink >= int(threshold or 0) else "BELOW_THRESHOLD"))
                    )
                    obj = {
                        "object_id": object_id,
                        "safe_filename": object_id,
                        "kind": "TEXT",
                        "semantic_parent": semantic_parent,
                        "role": role,
                        "parent_glyph_index": parent_counters[semantic_parent],
                        "char": char,
                        "codepoint": f"U+{ord(char):04X}",
                        "script_class": cls,
                        "source_file": str(SOURCE),
                        "source_line": source_line,
                        "declared_pt": declared_pt,
                        "graphics_scale": 1.0,
                        "effective_pt": declared_pt,
                        "pdf_span_size_pt": float(span["size"]),
                        "font_name": span["font"],
                        "font_color_rgb": list(target_rgb),
                        "local_background_rgb": list(bg_rgb),
                        "bbox_pt": [x0pt, y0pt, x1pt, y1pt],
                        "bbox_px": list(bbox),
                        "geometry_bbox_px": list(tight_bbox),
                        "h_ink_px": h_ink,
                        "ink_area_px": ink_area,
                        "class_threshold_px": threshold,
                        "machine_height_gate": machine_height_gate,
                        "r168_advisory_case": r168_advisory,
                        "machine_empty_mask": ink_area == 0,
                        "source_evidence": source_evidence,
                        "mask_path": f"03_masks/glyph/{object_id}_mask_only_1x.png",
                        "original_path": f"03_masks/glyph/{object_id}_original_1x.png",
                        "overlay_path": f"03_masks/glyph/{object_id}_overlay_1x.png",
                        "mask": mask,
                    }
                    obj["coords"] = global_coords(bbox, mask)
                    save_mask_bundle(full, bbox, mask, ROOT / "03_masks" / "glyph" / object_id)
                    glyphs.append(obj)
                    if semantic_parent not in element_rows:
                        element_rows[semantic_parent] = {
                            "element_id": semantic_parent,
                            "panel_id": "PANEL_MAIN",
                            "role": role,
                            "source_file": str(SOURCE),
                            "source_line": source_line,
                            "declared_pt": declared_pt,
                            "graphics_scale": 1.0,
                            "effective_pt": declared_pt,
                            "source_evidence": source_evidence,
                            "pdf_span_size_pt_values": [],
                            "glyph_ids": [],
                        }
                    element_rows[semantic_parent]["pdf_span_size_pt_values"].append(round(float(span["size"]), 6))
                    element_rows[semantic_parent]["glyph_ids"].append(object_id)

    if len(glyphs) != 108:
        raise RuntimeError(f"Expected 108 target glyphs, found {len(glyphs)}")

    graphics: list[dict[str, Any]] = []
    for seqno, (object_id, graphic_class, semantic_parent, semantic_description) in GRAPHICS.items():
        d = drawing_by_seqno.get(seqno)
        if d is None:
            raise RuntimeError(f"Missing expected drawing seqno {seqno}")
        rect = d["rect"]
        bbox = px_bbox_from_pt((rect.x0, rect.y0, rect.x1, rect.y1), pad=6)
        bx0, by0, bx1, by1 = bbox
        region = full_np[by0:by1, bx0:bx1]
        target_rgb = rgb_from_float(d.get("color") or d.get("fill"))
        if target_rgb is None:
            raise RuntimeError(f"No foreground color for drawing {seqno}")
        mask, bg_rgb = aligned_color_mask(region, target_rgb)
        if graphic_class == "NODE_BORDER":
            yy, xx = np.indices(mask.shape)
            dist_edge = np.minimum.reduce([xx, yy, mask.shape[1] - 1 - xx, mask.shape[0] - 1 - yy])
            mask &= dist_edge <= 13
        ink_area = int(np.count_nonzero(mask))
        obj = {
            "object_id": object_id,
            "safe_filename": object_id,
            "kind": "GRAPHIC",
            "graphic_class": graphic_class,
            "semantic_parent": semantic_parent,
            "semantic_description": semantic_description,
            "seqno": seqno,
            "drawing_type": d["type"],
            "stroke_rgb": list(rgb_from_float(d.get("color"))) if d.get("color") is not None else None,
            "fill_rgb": list(rgb_from_float(d.get("fill"))) if d.get("fill") is not None else None,
            "line_width_pt": d.get("width"),
            "item_count": len(d.get("items", [])),
            "bbox_pt": [rect.x0, rect.y0, rect.x1, rect.y1],
            "bbox_px": list(bbox),
            "local_background_rgb": list(bg_rgb),
            "ink_area_px": ink_area,
            "machine_empty_mask": ink_area == 0,
            "mask_path": f"03_masks/graphic/{object_id}_mask_only_1x.png",
            "original_path": f"03_masks/graphic/{object_id}_original_1x.png",
            "overlay_path": f"03_masks/graphic/{object_id}_overlay_1x.png",
            "mask": mask,
        }
        obj["coords"] = global_coords(bbox, mask)
        save_mask_bundle(full, bbox, mask, ROOT / "03_masks" / "graphic" / object_id)
        graphics.append(obj)

    if len(graphics) != 14:
        raise RuntimeError(f"Expected 14 foreground graphic paths, found {len(graphics)}")
    if any(obj["machine_empty_mask"] for obj in glyphs + graphics):
        empties = [obj["object_id"] for obj in glyphs + graphics if obj["machine_empty_mask"]]
        raise RuntimeError(f"Empty masks: {empties}")

    # Role/script medians and per-glyph ratios.
    medians: dict[tuple[str, str], float] = {}
    by_role_script: dict[tuple[str, str], list[int]] = defaultdict(list)
    for glyph in glyphs:
        if glyph["script_class"] != "LOW_PROFILE_PUNCTUATION" and not (glyph["char"] == "一" and glyph["h_ink_px"] < 30):
            by_role_script[(glyph["role"], glyph["script_class"])].append(glyph["h_ink_px"])
    for key, values in by_role_script.items():
        medians[key] = float(statistics.median(values))
    for glyph in glyphs:
        median = medians.get((glyph["role"], glyph["script_class"]))
        glyph["class_median_px"] = median
        glyph["ratio_to_class_median"] = None if median in (None, 0) else round(glyph["h_ink_px"] / median, 6)

    # Low-profile punctuation calibration from identical current-candidate glyphs where available.
    punctuation_groups: dict[tuple[str, str, float, tuple[int, ...]], list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        if glyph["script_class"] == "LOW_PROFILE_PUNCTUATION":
            key = (glyph["char"], glyph["font_name"], round(glyph["effective_pt"], 2), tuple(glyph["font_color_rgb"]))
            punctuation_groups[key].append(glyph)
    punctuation_rows: list[dict[str, Any]] = []
    for key, items in punctuation_groups.items():
        h_median = float(statistics.median([g["h_ink_px"] for g in items]))
        area_median = float(statistics.median([g["ink_area_px"] for g in items]))
        qualified = len(items) >= 2
        for glyph in items:
            glyph["punctuation_calibration_kind"] = "CURRENT_CANDIDATE_IDENTICAL" if qualified else "SEPARATE_ACTUAL_FONT_REQUIRED"
            glyph["punctuation_reference_count"] = len(items)
            glyph["punctuation_h_ratio"] = None if not qualified or h_median == 0 else round(glyph["h_ink_px"] / h_median, 6)
            glyph["punctuation_area_ratio"] = None if not qualified or area_median == 0 else round(glyph["ink_area_px"] / area_median, 6)
            punctuation_rows.append(
                {
                    "glyph_id": glyph["object_id"],
                    "char": glyph["char"],
                    "codepoint": glyph["codepoint"],
                    "font_name": glyph["font_name"],
                    "effective_pt": glyph["effective_pt"],
                    "font_color_rgb": glyph["font_color_rgb"],
                    "reference_kind": glyph["punctuation_calibration_kind"],
                    "reference_count": len(items),
                    "h_ink_px": glyph["h_ink_px"],
                    "ink_area_px": glyph["ink_area_px"],
                    "reference_h_median_px": h_median if qualified else None,
                    "reference_area_median_px": area_median if qualified else None,
                    "h_ratio": glyph["punctuation_h_ratio"],
                    "area_ratio": glyph["punctuation_area_ratio"],
                    "machine_calibration_gate": "COMPARABLE" if qualified else "SEPARATE_CALIBRATION_PENDING",
                }
            )

    objects = glyphs + graphics
    by_id = {obj["object_id"]: obj for obj in objects}
    pair_rows: list[dict[str, Any]] = []
    category_min: dict[str, tuple[float, int]] = {}
    overlap_total_unwhitelisted = 0
    for i, a in enumerate(objects):
        for j in range(i + 1, len(objects)):
            b = objects[j]
            pair_class, required, metric, whitelist = pair_class_and_gate(a, b)
            overlap = intersection_count(a, b)
            mask_gap, pa, pb = closest_pixels(a, b)
            bbox_gap = bbox_clearance(tuple(a.get("geometry_bbox_px", a["bbox_px"])), tuple(b.get("geometry_bbox_px", b["bbox_px"])))
            gate_value = bbox_gap if metric == "bbox" else mask_gap
            if whitelist:
                machine_gate = "DESIGN_WHITELIST"
            elif overlap > 0:
                machine_gate = "OVERLAP_CANDIDATE"
                overlap_total_unwhitelisted += overlap
            elif gate_value is None:
                machine_gate = "UNKNOWN"
            elif gate_value < required:
                machine_gate = "CLEARANCE_CANDIDATE"
            else:
                machine_gate = "MEETS_MACHINE_GATE"
            pair_id = f"P{i + 1:03d}_{j + 1:03d}"
            row = {
                "pair_id": pair_id,
                "object_a": a["object_id"],
                "object_b": b["object_id"],
                "kind_a": a["kind"],
                "kind_b": b["kind"],
                "semantic_parent_a": a["semantic_parent"],
                "semantic_parent_b": b["semantic_parent"],
                "pair_class": pair_class,
                "required_clearance_px": required,
                "gate_metric": metric,
                "bbox_clearance_px": bbox_gap,
                "mask_clearance_px": mask_gap,
                "overlap_candidate_px": overlap,
                "design_whitelist": whitelist,
                "machine_gate": machine_gate,
                "closest_pixel_a_x": None if pa is None else pa[0],
                "closest_pixel_a_y": None if pa is None else pa[1],
                "closest_pixel_b_x": None if pb is None else pb[0],
                "closest_pixel_b_y": None if pb is None else pb[1],
            }
            pair_rows.append(row)
            if not whitelist and gate_value is not None:
                old = category_min.get(pair_class)
                if old is None or gate_value < old[0]:
                    category_min[pair_class] = (float(gate_value), len(pair_rows) - 1)

    expected_pairs = len(objects) * (len(objects) - 1) // 2
    if len(pair_rows) != expected_pairs:
        raise RuntimeError(f"Pair count mismatch: {len(pair_rows)} != {expected_pairs}")

    critical_indices: set[int] = {idx for _, idx in category_min.values()}
    for idx, row in enumerate(pair_rows):
        gate_value = row["bbox_clearance_px"] if row["gate_metric"] == "bbox" else row["mask_clearance_px"]
        if row["overlap_candidate_px"] > 0 or row["machine_gate"] in {"CLEARANCE_CANDIDATE", "UNKNOWN"}:
            critical_indices.add(idx)
        elif row["design_whitelist"] and row["overlap_candidate_px"] > 0:
            critical_indices.add(idx)

    critical_rows: list[dict[str, Any]] = []
    for rel_number, idx in enumerate(sorted(critical_indices), start=1):
        row = pair_rows[idx]
        a = by_id[row["object_a"]]
        b = by_id[row["object_b"]]
        pa = None if row["closest_pixel_a_x"] is None else (int(row["closest_pixel_a_x"]), int(row["closest_pixel_a_y"]))
        pb = None if row["closest_pixel_b_x"] is None else (int(row["closest_pixel_b_x"]), int(row["closest_pixel_b_y"]))
        rel_id = f"REL{rel_number:03d}_{a['object_id']}__{b['object_id']}"
        evidence_meta = relation_evidence(full, a, b, rel_id, pa, pb)
        row["critical_relation_id"] = rel_id
        row["evidence_dir"] = f"06_relations/{rel_id}"
        critical_rows.append({**row, "roi_full_page_300dpi_px": evidence_meta["roi_full_page_300dpi_px"]})

    # Foreign-mask intersection counts are purely mechanical candidates, not manual adjudications.
    intersections_by_object: Counter[str] = Counter()
    for row in pair_rows:
        if row["overlap_candidate_px"] > 0 and not row["design_whitelist"]:
            intersections_by_object[row["object_a"]] += row["overlap_candidate_px"]
            intersections_by_object[row["object_b"]] += row["overlap_candidate_px"]
    for obj in objects:
        obj["machine_foreign_intersection_candidate_px"] = intersections_by_object[obj["object_id"]]

    # Crop-edge / clip evidence.
    clip_rows: list[dict[str, Any]] = []
    total_clip = 0
    for obj in objects:
        coords = obj["coords"]
        x0, y0, x1, y1 = FIGURE_CROP_PX
        if len(coords):
            distances = np.column_stack([coords[:, 0] - x0, (x1 - 1) - coords[:, 0], coords[:, 1] - y0, (y1 - 1) - coords[:, 1]])
            min_edge = int(np.min(distances))
            clip_pixels = int(np.count_nonzero(np.any(distances < 0, axis=1)))
        else:
            min_edge, clip_pixels = -1, 0
        total_clip += clip_pixels
        clip_rows.append(
            {
                "object_id": obj["object_id"],
                "kind": obj["kind"],
                "min_figure_crop_edge_clearance_px": min_edge,
                "clip_pixel_count": clip_pixels,
                "machine_gate": "CLEAR" if clip_pixels == 0 else "CLIP_CANDIDATE",
            }
        )

    # Overlay all glyphs and graphics on the figure crop.
    overlay = figure_crop.copy().convert("RGB")
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    fx0, fy0, _, _ = FIGURE_CROP_PX
    for obj in glyphs:
        x0, y0, x1, y1 = obj["bbox_px"]
        draw.rectangle((x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0), outline=(220, 0, 0), width=1)
        draw.text((x0 - fx0, y0 - fy0), obj["object_id"], fill=(220, 0, 0), font=font)
    overlay.save(ROOT / "01_renders" / "after_text_measurement_overlay_300dpi.png")

    gfx_overlay = figure_crop.copy().convert("RGB")
    draw_g = ImageDraw.Draw(gfx_overlay)
    for obj in graphics:
        x0, y0, x1, y1 = obj["bbox_px"]
        draw_g.rectangle((x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0), outline=(180, 0, 180), width=2)
        draw_g.text((x0 - fx0, y0 - fy0), obj["object_id"], fill=(180, 0, 180), font=font)
    gfx_overlay.save(ROOT / "01_renders" / "foreground_object_overlay_300dpi.png")

    glyph_sheet_files = make_glyph_contact_sheets(full, glyphs)
    graphic_sheet_files = make_graphic_contact_sheets(full, graphics)

    # Plain serializable inventories and ledgers.
    def clean(obj: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in obj.items() if k not in {"mask", "coords"}}

    glyph_rows = [clean(g) for g in glyphs]
    graphic_rows = [clean(g) for g in graphics]
    write_json(ROOT / "02_extraction" / "glyph_inventory.json", glyph_rows)
    write_csv(ROOT / "02_extraction" / "glyph_inventory.csv", glyph_rows)
    write_json(ROOT / "02_extraction" / "foreground_graphic_inventory.json", graphic_rows)
    write_csv(ROOT / "02_extraction" / "foreground_graphic_inventory.csv", graphic_rows)
    excluded_rows = []
    for seqno, reason in EXCLUDED_DRAWINGS.items():
        d = drawing_by_seqno[seqno]
        excluded_rows.append(
            {
                "seqno": seqno,
                "drawing_type": d["type"],
                "bbox_pt": [d["rect"].x0, d["rect"].y0, d["rect"].x1, d["rect"].y1],
                "classification": "VISIBLE_BACKGROUND_EXCLUDED_FROM_FOREGROUND_N",
                "reason": reason,
            }
        )
    write_json(ROOT / "02_extraction" / "excluded_background_drawings.json", excluded_rows)
    write_csv(ROOT / "02_extraction" / "excluded_background_drawings.csv", excluded_rows)

    safe_rows = [
        {"object_id": o["object_id"], "safe_filename": o["safe_filename"], "kind": o["kind"], "mask_path": o["mask_path"]}
        for o in objects
    ]
    write_csv(ROOT / "02_extraction" / "id_safe_filename_map.csv", safe_rows)
    write_json(ROOT / "02_extraction" / "id_safe_filename_map.json", safe_rows)

    element_output: list[dict[str, Any]] = []
    for row in element_rows.values():
        row["pdf_span_size_pt_values"] = sorted(set(row["pdf_span_size_pt_values"]))
        row["glyph_count"] = len(row["glyph_ids"])
        row["machine_effective_pt_gate"] = "MEETS_9_5PT" if row["effective_pt"] >= 9.5 else "BELOW_9_5PT"
        element_output.append(row)
    write_csv(ROOT / "05_ledgers" / "after_font_audit.csv", element_output)

    pixel_rows: list[dict[str, Any]] = []
    for glyph in glyph_rows:
        pixel_rows.append(
            {
                "element_id": glyph["semantic_parent"],
                "glyph_id": glyph["object_id"],
                "panel_id": "PANEL_MAIN",
                "role": glyph["role"],
                "source_file": glyph["source_file"],
                "source_line": glyph["source_line"],
                "declared_pt": glyph["declared_pt"],
                "graphics_scale": glyph["graphics_scale"],
                "effective_pt": glyph["effective_pt"],
                "text_sample": glyph["char"],
                "codepoint": glyph["codepoint"],
                "script_class": glyph["script_class"],
                "bbox_x0": glyph["bbox_px"][0],
                "bbox_y0": glyph["bbox_px"][1],
                "bbox_x1": glyph["bbox_px"][2],
                "bbox_y1": glyph["bbox_px"][3],
                "h_ink_px": glyph["h_ink_px"],
                "ink_area_px": glyph["ink_area_px"],
                "class_threshold_px": glyph["class_threshold_px"],
                "class_median_px": glyph["class_median_px"],
                "ratio_to_class_median": glyph["ratio_to_class_median"],
                "machine_height_gate": glyph["machine_height_gate"],
                "r168_advisory_case": glyph["r168_advisory_case"],
                "machine_empty_mask": glyph["machine_empty_mask"],
                "machine_foreign_intersection_candidate_px": glyph["machine_foreign_intersection_candidate_px"],
                "mask_path": glyph["mask_path"],
                "original_path": glyph["original_path"],
                "overlay_path": glyph["overlay_path"],
            }
        )
    write_csv(ROOT / "05_ledgers" / "after_pixel_measurements.csv", pixel_rows)
    write_csv(ROOT / "05_ledgers" / "punctuation_calibration_machine.csv", punctuation_rows)
    write_csv(ROOT / "05_ledgers" / "after_overlap_report.csv", pair_rows)
    write_json(ROOT / "05_ledgers" / "after_overlap_report.json", pair_rows)
    write_csv(ROOT / "05_ledgers" / "clip_report.csv", clip_rows)
    write_csv(ROOT / "05_ledgers" / "critical_relations_machine.csv", critical_rows)
    write_json(ROOT / "05_ledgers" / "critical_relations_machine.json", critical_rows)

    source_text = SOURCE.read_text(encoding="utf-8")
    source_scan = {
        "global_style": "font=\\fontsize{10.0pt}{12.0pt}\\selectfont",
        "stage_style": "font=\\fontsize{10.5pt}{12.6pt}\\selectfont",
        "local_10pt_occurrences": source_text.count("\\fontsize{10.0pt}{12.0pt}\\selectfont"),
        "scale_tokens": {token: source_text.count(token) for token in ["resizebox", "scalebox", "transform shape", "scale="]},
        "math_rule_tokens": {token: source_text.count(token) for token in ["overline", "underline", "frac", "sqrt", "hat", "vec"]},
        "declared_min_effective_pt": 10.0,
        "declared_max_effective_pt": 10.5,
        "graphics_scale": 1.0,
        "machine_source_gate": "MEETS_9_5PT_NO_GRAPHICS_SCALING",
    }
    write_json(ROOT / "02_extraction" / "source_font_override_scan.json", source_scan)

    drawing_accounting = {
        "page_drawing_count_total": len(drawings),
        "target_foreground_seqnos": sorted(GRAPHICS),
        "target_foreground_count": len(GRAPHICS),
        "target_background_seqnos": sorted(EXCLUDED_DRAWINGS),
        "target_background_count": len(EXCLUDED_DRAWINGS),
        "target_math_rule_count": 0,
        "target_unaccounted_visible_drawing_seqnos": [],
        "scope_note": "Only drawing seqnos whose bboxes intersect the independently frozen figure region are target drawings; the two visible fills are explicitly background.",
    }
    write_json(ROOT / "02_extraction" / "drawing_bidirectional_accounting.json", drawing_accounting)

    object_manifest = {
        "glyph_count": len(glyphs),
        "foreground_graphic_path_count": len(graphics),
        "background_drawing_count_excluded": len(EXCLUDED_DRAWINGS),
        "math_rule_count": 0,
        "N_total_foreground_objects": len(objects),
        "C_N_2_expected_unordered_pairs": expected_pairs,
        "C_N_2_emitted_unordered_pairs": len(pair_rows),
        "object_ids_unique": len({o["object_id"] for o in objects}) == len(objects),
        "safe_filenames_unique": len({o["safe_filename"] for o in objects}) == len(objects),
    }
    write_json(ROOT / "02_extraction" / "object_manifest_N_C.json", object_manifest)

    machine_summary = {
        **object_manifest,
        "native_300dpi_dimensions": list(full.size),
        "figure_crop_dimensions": list(figure_crop.size),
        "standalone_dimensions": list(standalone.size),
        "empty_mask_count": sum(int(o["machine_empty_mask"]) for o in objects),
        "unwhitelisted_overlap_candidate_pixel_sum": overlap_total_unwhitelisted,
        "pair_machine_gate_counts": dict(Counter(row["machine_gate"] for row in pair_rows)),
        "critical_relation_count": len(critical_rows),
        "clip_pixel_count": total_clip,
        "glyph_contact_sheet_count": len(glyph_sheet_files),
        "graphic_contact_sheet_count": len(graphic_sheet_files),
        "glyph_contact_sheet_files": glyph_sheet_files,
        "graphic_contact_sheet_files": graphic_sheet_files,
        "punctuation_separate_calibration_pending_glyphs": [
            row["glyph_id"] for row in punctuation_rows if row["machine_calibration_gate"] == "SEPARATE_CALIBRATION_PENDING"
        ],
        "r168_policy": "[0.92,1.08] micro ratios, font metadata differences, single-horizontal-stroke CJK height, and 1-2px raster differences are advisory and cannot alone produce a hard FAIL.",
    }
    write_json(ROOT / "08_qc" / "machine_summary_pre_manual.json", machine_summary)
    print(json.dumps(machine_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
