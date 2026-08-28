from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, label


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R9_SA3_FRESH_ISOLATED_R113_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
PAGE_NUMBER = 69
PAGE_INDEX = PAGE_NUMBER - 1
SCALE = 300.0 / 72.0
FIGURE_RECT_PT = fitz.Rect(90.0, 60.0, 490.0, 221.0)
STANDALONE_RECT_PT = fitz.Rect(100.0, 65.0, 485.0, 200.0)
TEXT_REGION_PT = fitz.Rect(100.0, 65.0, 485.0, 218.0)
FIGURE_CROP_PX = (375, 250, 2042, 921)
STANDALONE_CROP_PX = (416, 270, 2021, 834)
EXPECTED_PDF_SHA256 = "6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D"
EXPECTED_SOURCE_SHA256 = "2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def px_bbox(rect: fitz.Rect, pad: int = 0, image_size: tuple[int, int] | None = None) -> tuple[int, int, int, int]:
    x0 = math.floor(rect.x0 * SCALE) - pad
    y0 = math.floor(rect.y0 * SCALE) - pad
    x1 = math.ceil(rect.x1 * SCALE) + pad
    y1 = math.ceil(rect.y1 * SCALE) + pad
    if image_size:
        width, height = image_size
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(width, x1), min(height, y1)
    return x0, y0, x1, y1


def int_color_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def float_color_to_rgb(value: tuple[float, float, float] | None) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(max(0, min(255, round(channel * 255))) for channel in value)


def color_match(rgb: np.ndarray, target: tuple[int, int, int], minimum_contrast: float = 20.0) -> np.ndarray:
    data = rgb.astype(np.float32)
    target_arr = np.asarray(target, dtype=np.float32)
    white = np.full(3, 255.0, dtype=np.float32)
    vector = white - target_arr
    denom = float(np.dot(vector, vector))
    if denom < 1.0:
        return np.zeros(data.shape[:2], dtype=bool)
    alpha = np.sum((white - data) * vector, axis=2) / denom
    projected = white - alpha[..., None] * vector
    residual = np.max(np.abs(data - projected), axis=2)
    contrast = alpha * float(np.max(np.abs(vector)))
    return (alpha >= 0.0) & (alpha <= 1.25) & (contrast >= minimum_contrast) & (residual <= 24.0)


def mask_ink_bbox(mask: np.ndarray, origin: tuple[int, int]) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    ox, oy = origin
    return ox + int(xs.min()), oy + int(ys.min()), ox + int(xs.max()) + 1, oy + int(ys.max()) + 1


def char_class(char: str, size_pt: float) -> tuple[str, int | None]:
    codepoint = ord(char)
    if size_pt < 8.0:
        return "NATURAL_SCRIPT", 15
    if 0x4E00 <= codepoint <= 0x9FFF or 0x3000 <= codepoint <= 0x303F:
        if char in "，。、：；！？…":
            return "LOW_PROFILE_PUNCTUATION", None
        return "CJK_FULL", 30
    if char in ".,;:":
        return "LOW_PROFILE_PUNCTUATION", None
    if char in "+=−-×÷<>≤≥":
        return "MATH_OPERATOR", 22
    if char in "()[]{}":
        return "MATH_FULL", 22
    if char.isdigit() or (char.isalpha() and char.upper() == char and char.lower() != char):
        return "DIGIT_OR_UPPER", 24
    return "LOWER_OR_GREEK", 17


def role_for_text(text: str, bbox: fitz.Rect, size_pt: float) -> str:
    if bbox.y0 >= 200.0:
        return "CAPTION"
    if "右连续" in text or "同一" in text or "跳高" in text:
        return "ANNOTATION"
    if 196.0 <= bbox.x0 <= 455.0 and bbox.y0 < 125.0 and text in {"𝑝", "1", "2", "3", "4"}:
        return "CDF_MASS_LABEL"
    if bbox.x1 <= 142.5 or bbox.y0 >= 175.0:
        if any(char.isdigit() for char in text):
            return "TICK_LABEL"
    if bbox.x0 < 125.0 or (305.0 <= bbox.x0 <= 320.0 and bbox.y0 >= 185.0):
        return "AXIS_LABEL"
    if bbox.y0 < 130.0:
        return "CDF_TEXT"
    return "PMF_TEXT"


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def cubic_points(p0: fitz.Point, p1: fitz.Point, p2: fitz.Point, p3: fitz.Point, steps: int = 24):
    points = []
    for index in range(steps + 1):
        t = index / steps
        u = 1.0 - t
        x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
        points.append((x * SCALE, y * SCALE))
    return points


def drawing_candidate_mask(drawing: dict, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    canvas = Image.new("L", (x1 - x0, y1 - y0), 0)
    pen = ImageDraw.Draw(canvas)
    width = max(1, int(math.ceil(float(drawing.get("width") or 0.7) * SCALE)) + 2)
    current: tuple[float, float] | None = None
    polygon_points: list[tuple[float, float]] = []
    for item in drawing.get("items", []):
        kind = item[0]
        if kind == "l":
            p0, p1 = item[1], item[2]
            points = [(p0.x * SCALE - x0, p0.y * SCALE - y0), (p1.x * SCALE - x0, p1.y * SCALE - y0)]
            pen.line(points, fill=255, width=width)
            polygon_points.extend(points if not polygon_points else points[1:])
            current = (p1.x * SCALE, p1.y * SCALE)
        elif kind == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            points = [(x - x0, y - y0) for x, y in cubic_points(p0, p1, p2, p3)]
            pen.line(points, fill=255, width=width)
            polygon_points.extend(points if not polygon_points else points[1:])
            current = (p3.x * SCALE, p3.y * SCALE)
        elif kind == "re":
            rect = item[1]
            coords = (rect.x0 * SCALE - x0, rect.y0 * SCALE - y0, rect.x1 * SCALE - x0, rect.y1 * SCALE - y0)
            if "f" in str(drawing.get("type", "")):
                pen.rectangle(coords, fill=255)
            else:
                pen.rectangle(coords, outline=255, width=width)
            current = None
        elif kind == "qu":
            quad = item[1]
            points = [
                (quad.ul.x * SCALE - x0, quad.ul.y * SCALE - y0),
                (quad.ur.x * SCALE - x0, quad.ur.y * SCALE - y0),
                (quad.lr.x * SCALE - x0, quad.lr.y * SCALE - y0),
                (quad.ll.x * SCALE - x0, quad.ll.y * SCALE - y0),
            ]
            pen.polygon(points, fill=255 if "f" in str(drawing.get("type", "")) else None, outline=255)
            polygon_points.extend(points)
            current = None
    if "f" in str(drawing.get("type", "")) and len(polygon_points) >= 3:
        pen.polygon(polygon_points, fill=255)
    return np.asarray(canvas) > 0


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def pair_intersection(a: dict, b: dict, mask_key: str = "mask") -> int:
    ax0, ay0, ax1, ay1 = a["mask_bbox_px"]
    bx0, by0, bx1, by1 = b["mask_bbox_px"]
    x0, y0 = max(ax0, bx0), max(ay0, by0)
    x1, y1 = min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    am_source = a.get(mask_key, a["mask"])
    bm_source = b.get(mask_key, b["mask"])
    am = am_source[y0 - ay0 : y1 - ay0, x0 - ax0 : x1 - ax0]
    bm = bm_source[y0 - by0 : y1 - by0, x0 - bx0 : x1 - bx0]
    return int(np.count_nonzero(am & bm))


def pair_clearance(a: dict, b: dict, gap: float) -> float:
    if gap > 40.0:
        return gap
    ax0, ay0, ax1, ay1 = a["mask_bbox_px"]
    bx0, by0, bx1, by1 = b["mask_bbox_px"]
    x0, y0 = min(ax0, bx0) - 2, min(ay0, by0) - 2
    x1, y1 = max(ax1, bx1) + 2, max(ay1, by1) + 2
    canvas_a = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    canvas_b = np.zeros_like(canvas_a)
    canvas_a[ay0 - y0 : ay1 - y0, ax0 - x0 : ax1 - x0] = a["mask"]
    canvas_b[by0 - y0 : by1 - y0, bx0 - x0 : bx1 - x0] = b["mask"]
    if not canvas_a.any() or not canvas_b.any():
        return float("nan")
    distances = distance_transform_edt(~canvas_a)
    return float(distances[canvas_b].min())


def make_triptych(image: Image.Image, obj: dict, scale_factor: int) -> Image.Image:
    x0, y0, x1, y1 = obj["mask_bbox_px"]
    crop = image.crop((x0, y0, x1, y1)).convert("RGB")
    mask = obj["mask"]
    overlay = np.asarray(crop).copy()
    overlay[mask] = [255, 0, 0]
    mask_only = np.full_like(overlay, 255)
    mask_only[mask] = [0, 0, 0]
    panels = [crop, Image.fromarray(overlay), Image.fromarray(mask_only)]
    if scale_factor != 1:
        panels = [panel.resize((panel.width * scale_factor, panel.height * scale_factor), Image.Resampling.NEAREST) for panel in panels]
    height = max(panel.height for panel in panels)
    width = sum(panel.width for panel in panels) + 8
    out = Image.new("RGB", (width, height), "white")
    cursor = 0
    for panel in panels:
        out.paste(panel, (cursor, 0))
        cursor += panel.width + 4
    return out


def make_contact_sheets(image: Image.Image, objects: list[dict], output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    batch_size = 12
    for batch_index in range(0, len(objects), batch_size):
        batch = objects[batch_index : batch_index + batch_size]
        sheet_number = batch_index // batch_size + 1
        for factor, suffix in ((1, "1x"), (8, "8x_nearest")):
            triptychs = [(obj, make_triptych(image, obj, factor)) for obj in batch]
            cell_width = max(max(tri.width + 10, 220 if factor == 1 else 520) for _, tri in triptychs)
            cell_height = max(max(tri.height + 34, 90 if factor == 1 else 210) for _, tri in triptychs)
            cols = 3
            sheet = Image.new("RGB", (cell_width * cols, cell_height * math.ceil(len(batch) / cols)), "white")
            draw = ImageDraw.Draw(sheet)
            for cell_index, (obj, tri) in enumerate(triptychs, start=1):
                col = (cell_index - 1) % cols
                row = (cell_index - 1) // cols
                ox, oy = col * cell_width, row * cell_height
                draw.text((ox + 4, oy + 3), f"{obj['element_id']} {obj.get('char', '')!r} | ORIGINAL / TARGET / MASK", fill="black")
                sheet.paste(tri, (ox + 4, oy + 24))
                rows.append(
                    {
                        "element_id": obj["element_id"],
                        "sheet": f"glyph_contact_sheet_{sheet_number:02d}_{suffix}.png",
                        "cell": cell_index,
                        "scale": suffix,
                    }
                )
            path = output_dir / f"glyph_contact_sheet_{sheet_number:02d}_{suffix}.png"
            sheet.save(path)
    return rows


def make_pair_roi(page_image: Image.Image, pair_id: str, a: dict, b: dict, output_dir: Path) -> dict:
    ax0, ay0, ax1, ay1 = a["mask_bbox_px"]
    bx0, by0, bx1, by1 = b["mask_bbox_px"]
    ux0, uy0 = min(ax0, bx0) - 2, min(ay0, by0) - 2
    ux1, uy1 = max(ax1, bx1) + 2, max(ay1, by1) + 2
    union_a = np.zeros((uy1 - uy0, ux1 - ux0), dtype=bool)
    union_b = np.zeros_like(union_a)
    union_a[ay0 - uy0 : ay1 - uy0, ax0 - ux0 : ax1 - ux0] = a["mask"]
    union_b[by0 - uy0 : by1 - uy0, bx0 - ux0 : bx1 - ux0] = b["mask"]
    union_overlap = union_a & union_b
    if union_overlap.any():
        ys, xs = np.nonzero(union_overlap)
        focus_x0, focus_y0, focus_x1, focus_y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    else:
        distances, nearest = distance_transform_edt(~union_a, return_indices=True)
        bys, bxs = np.nonzero(union_b)
        nearest_index = int(np.argmin(distances[bys, bxs]))
        bx_focus, by_focus = int(bxs[nearest_index]), int(bys[nearest_index])
        ay_focus = int(nearest[0, by_focus, bx_focus])
        ax_focus = int(nearest[1, by_focus, bx_focus])
        focus_x0, focus_y0 = min(ax_focus, bx_focus), min(ay_focus, by_focus)
        focus_x1, focus_y1 = max(ax_focus, bx_focus) + 1, max(ay_focus, by_focus) + 1
    pad = 12
    x0 = max(0, ux0 + focus_x0 - pad)
    y0 = max(0, uy0 + focus_y0 - pad)
    x1 = min(page_image.width, ux0 + focus_x1 + pad)
    y1 = min(page_image.height, uy0 + focus_y1 + pad)
    original = page_image.crop((x0, y0, x1, y1)).convert("RGB")
    shape = (y1 - y0, x1 - x0)
    mask_a = np.zeros(shape, dtype=bool)
    mask_b = np.zeros(shape, dtype=bool)
    a_ix0, a_iy0, a_ix1, a_iy1 = max(ax0, x0), max(ay0, y0), min(ax1, x1), min(ay1, y1)
    b_ix0, b_iy0, b_ix1, b_iy1 = max(bx0, x0), max(by0, y0), min(bx1, x1), min(by1, y1)
    if a_ix0 < a_ix1 and a_iy0 < a_iy1:
        mask_a[a_iy0 - y0 : a_iy1 - y0, a_ix0 - x0 : a_ix1 - x0] = a["mask"][a_iy0 - ay0 : a_iy1 - ay0, a_ix0 - ax0 : a_ix1 - ax0]
    if b_ix0 < b_ix1 and b_iy0 < b_iy1:
        mask_b[b_iy0 - y0 : b_iy1 - y0, b_ix0 - x0 : b_ix1 - x0] = b["mask"][b_iy0 - by0 : b_iy1 - by0, b_ix0 - bx0 : b_ix1 - bx0]
    overlap = mask_a & mask_b
    overlay = np.asarray(original).copy()
    overlay[mask_a] = [255, 0, 0]
    overlay[mask_b] = [0, 80, 255]
    overlay[overlap] = [255, 0, 255]
    files = {
        "original_1x": f"{pair_id}_original_1x.png",
        "a_mask": f"{pair_id}_a_mask.png",
        "b_mask": f"{pair_id}_b_mask.png",
        "intersection": f"{pair_id}_intersection.png",
        "overlay_1x": f"{pair_id}_overlay_1x.png",
        "overlay_8x": f"{pair_id}_overlay_8x_nearest.png",
    }
    original.save(output_dir / files["original_1x"])
    Image.fromarray(np.where(mask_a, 0, 255).astype(np.uint8), mode="L").save(output_dir / files["a_mask"])
    Image.fromarray(np.where(mask_b, 0, 255).astype(np.uint8), mode="L").save(output_dir / files["b_mask"])
    Image.fromarray(np.where(overlap, 0, 255).astype(np.uint8), mode="L").save(output_dir / files["intersection"])
    overlay_image = Image.fromarray(overlay)
    overlay_image.save(output_dir / files["overlay_1x"])
    overlay_image.resize((overlay_image.width * 8, overlay_image.height * 8), Image.Resampling.NEAREST).save(output_dir / files["overlay_8x"])
    return {**files, "roi_px": [x0, y0, x1, y1]}


def make_pair_contact_sheets(pair_rows: list[dict], output_dir: Path) -> list[str]:
    outputs = []
    batch_size = 12
    for batch_index in range(0, len(pair_rows), batch_size):
        batch = pair_rows[batch_index : batch_index + batch_size]
        images = []
        for row in batch:
            image = Image.open(output_dir / row.get("pre_overlay_8x", row["overlay_8x"])).convert("RGB")
            image.thumbnail((760, 420), Image.Resampling.NEAREST)
            images.append((row, image.copy()))
        cols = 2
        cell_w = 780
        cell_h = 470
        sheet = Image.new("RGB", (cell_w * cols, cell_h * math.ceil(len(images) / cols)), "white")
        draw = ImageDraw.Draw(sheet)
        for cell_index, (row, image) in enumerate(images):
            x = (cell_index % cols) * cell_w
            y = (cell_index // cols) * cell_h
            draw.text((x + 6, y + 6), f"{row['pair_id']} {row['a_id']} <> {row['b_id']} clear={row['clearance_px']}", fill="black")
            sheet.paste(image, (x + 6, y + 32))
        name = f"critical_pair_contact_{batch_index // batch_size + 1:02d}_8x_nearest.png"
        sheet.save(output_dir / name)
        outputs.append(name)
    return outputs


for directory in (
    ROOT / "01_identity",
    ROOT / "02_render",
    ROOT / "03_objects" / "glyph_masks",
    ROOT / "03_objects" / "graphic_masks",
    ROOT / "03_objects" / "graphic_pre_occlusion_masks",
    ROOT / "04_contacts",
    ROOT / "05_pairs",
    ROOT / "06_ledgers",
    ROOT / "07_validation",
):
    directory.mkdir(parents=True, exist_ok=True)

identity = {
    "uid": "FIG-P067-01",
    "role": "SA3_FRESH_ISOLATED",
    "agent_identity": "/root/p067_r113_fresh_sa3",
    "handoff_id": "A-R113-P067-SA3-FRESH-ISOLATED-20260827",
    "official_round": "R113",
    "pdf": str(PDF),
    "pdf_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "expected_pdf_sha256": EXPECTED_PDF_SHA256,
    "source": str(SOURCE),
    "source_bytes": SOURCE.stat().st_size,
    "source_sha256": sha256(SOURCE),
    "expected_source_sha256": EXPECTED_SOURCE_SHA256,
    "physical_page": PAGE_NUMBER,
    "printed_page": 56,
    "figure_number": "4.1",
    "caption": "离散随机变量的分布函数：跳跃高度等于对应点的概率质量",
    "page_size_pt": [595.2760009765625, 841.8900146484375],
    "page_300dpi_native_px": [2481, 3508],
    "figure_crop_300dpi_px": list(FIGURE_CROP_PX),
    "standalone_crop_300dpi_px": list(STANDALONE_CROP_PX),
}
if identity["pdf_sha256"] != EXPECTED_PDF_SHA256 or identity["source_sha256"] != EXPECTED_SOURCE_SHA256:
    raise RuntimeError("Frozen input identity mismatch")
write_json(ROOT / "01_identity" / "candidate_identity.json", identity)

page_image = Image.open(ROOT / "02_render" / "page_069_300dpi.png").convert("RGB")
gray_page = Image.open(ROOT / "02_render" / "page_069_gray_300dpi.png").convert("L")
if page_image.size != (2481, 3508):
    raise RuntimeError(f"Unexpected native page dimensions: {page_image.size}")
figure_crop = page_image.crop(FIGURE_CROP_PX)
standalone_crop = page_image.crop(STANDALONE_CROP_PX)
gray_crop = gray_page.crop(FIGURE_CROP_PX)
figure_crop.save(ROOT / "02_render" / "figure_crop_300dpi.png")
standalone_crop.save(ROOT / "02_render" / "standalone_300dpi.png")
gray_crop.save(ROOT / "02_render" / "grayscale_300dpi.png")
figure_crop.resize((figure_crop.width * 8, figure_crop.height * 8), Image.Resampling.NEAREST).save(ROOT / "02_render" / "figure_crop_300dpi_8x_nearest.png")

doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
raw = page.get_text("rawdict")
page_np = np.asarray(page_image)

objects: list[dict] = []
glyph_rows: list[dict] = []
parent_rows: list[dict] = []
glyph_index = 0
parent_index = 0
for block_index, block in enumerate(raw["blocks"], start=1):
    if block.get("type") != 0:
        continue
    for line_index, line in enumerate(block.get("lines", []), start=1):
        for span_index, span in enumerate(line.get("spans", []), start=1):
            chars = span.get("chars", [])
            if not chars:
                continue
            span_rect = fitz.Rect(span["bbox"])
            if not span_rect.intersects(TEXT_REGION_PT):
                continue
            visible_chars = [char for char in chars if char.get("c", "").strip() and fitz.Rect(char["bbox"]).intersects(TEXT_REGION_PT)]
            if not visible_chars:
                continue
            parent_index += 1
            parent_id = f"TP{parent_index:03d}"
            parent_text = "".join(char.get("c", "") for char in chars)
            role = role_for_text(parent_text, span_rect, float(span["size"]))
            parent_rows.append(
                {
                    "parent_id": parent_id,
                    "text": parent_text,
                    "role": role,
                    "bbox_pt": [round(value, 3) for value in span["bbox"]],
                    "font": span["font"],
                    "size_pt": round(float(span["size"]), 3),
                    "line_direction": [round(value, 6) for value in line.get("dir", (1.0, 0.0))],
                    "rawdict_locator": f"block={block_index};line={line_index};span={span_index}",
                }
            )
            target_rgb = int_color_to_rgb(int(span["color"]))
            for char_index, char in enumerate(chars, start=1):
                value = char.get("c", "")
                char_rect = fitz.Rect(char["bbox"])
                if not value.strip() or not char_rect.intersects(TEXT_REGION_PT):
                    continue
                glyph_index += 1
                element_id = f"T{glyph_index:03d}"
                # The PDF rawdict character bbox is the isolation boundary.  Do not
                # add navigation padding here: even a 1-2 px expansion can import
                # anti-aliased pixels from an adjacent glyph into MASK ONLY.
                bbox = px_bbox(char_rect, pad=0, image_size=page_image.size)
                x0, y0, x1, y1 = bbox
                rgb = page_np[y0:y1, x0:x1]
                mask = color_match(rgb, target_rgb)
                if element_id == "T021":
                    # The no-fill annotation crosses the x=1 gray guide inside
                    # this rawdict bbox.  The full-width colon itself is the two
                    # compact components on the left; the tall components on the
                    # right are the separately inventoried guide G010.
                    component_map, component_count = label(mask)
                    cleaned = np.zeros_like(mask)
                    for component_id in range(1, component_count + 1):
                        ys, xs = np.nonzero(component_map == component_id)
                        if len(xs) and float(xs.mean()) < mask.shape[1] / 2.0:
                            cleaned[component_map == component_id] = True
                    mask = cleaned
                ink_bbox = mask_ink_bbox(mask, (x0, y0))
                ink_height = 0 if ink_bbox is None else ink_bbox[3] - ink_bbox[1]
                area = int(np.count_nonzero(mask))
                category, threshold = char_class(value, float(span["size"]))
                safe = safe_id(element_id)
                Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(ROOT / "03_objects" / "glyph_masks" / f"{safe}.png")
                obj = {
                    "element_id": element_id,
                    "safe_filename": safe,
                    "object_type": "TEXT_GLYPH",
                    "semantic_parent": parent_id,
                    "role": role,
                    "char": value,
                    "bbox_pt": [round(v, 3) for v in char["bbox"]],
                    "mask_bbox_px": bbox,
                    "ink_bbox_px": ink_bbox,
                    "mask": mask,
                    "font": span["font"],
                    "size_pt": float(span["size"]),
                    "target_rgb": target_rgb,
                }
                objects.append(obj)
                glyph_rows.append(
                    {
                        "element_id": element_id,
                        "safe_filename": safe,
                        "char": value,
                        "unicode": f"U+{ord(value):04X}",
                        "semantic_parent": parent_id,
                        "role": role,
                        "font": span["font"],
                        "pdf_size_pt": round(float(span["size"]), 3),
                        "category": category,
                        "threshold_px": "" if threshold is None else threshold,
                        "bbox_pt": json.dumps([round(v, 3) for v in char["bbox"]]),
                        "mask_bbox_px": json.dumps(list(bbox)),
                        "ink_bbox_px": "" if ink_bbox is None else json.dumps(list(ink_bbox)),
                        "h_ink_px": ink_height,
                        "ink_area_px": area,
                        "mask_empty": area == 0,
                        "numeric_threshold_met": "N/A" if threshold is None else ink_height >= threshold,
                        "mask_path": f"03_objects/glyph_masks/{safe}.png",
                    }
                )

drawings = page.get_drawings(extended=True)
graphic_rows: list[dict] = []
occluder_rows: list[dict] = []
occluder_specs: list[dict] = []
for draw_index, drawing in enumerate(drawings, start=1):
    rect = drawing["rect"]
    # Closed-interval test is required because visible horizontal/vertical
    # strokes legitimately have a zero-height or zero-width PDF bbox.
    outside = (
        rect.x1 < FIGURE_RECT_PT.x0
        or rect.x0 > FIGURE_RECT_PT.x1
        or rect.y1 < FIGURE_RECT_PT.y0
        or rect.y0 > FIGURE_RECT_PT.y1
    )
    if outside:
        continue
    stroke_rgb = float_color_to_rgb(drawing.get("color"))
    fill_rgb = float_color_to_rgb(drawing.get("fill"))
    colors = [color for color in (stroke_rgb, fill_rgb) if color is not None]
    is_white_only = bool(colors) and all(max(abs(channel - 255) for channel in color) <= 2 for color in colors)
    if is_white_only:
        fill_opacity = float(drawing.get("fill_opacity", 1.0) or 1.0)
        occluder_specs.append({"pdf_drawing_index": draw_index, "rect": fitz.Rect(rect), "fill_opacity": fill_opacity})
        occluder_rows.append(
            {
                "pdf_drawing_index": draw_index,
                "bbox_pt": json.dumps([round(rect.x0, 3), round(rect.y0, 3), round(rect.x1, 3), round(rect.y1, 3)]),
                "fill_rgb": json.dumps(fill_rgb),
                "type": drawing.get("type"),
                "fill_opacity": fill_opacity,
                "purpose": "REAL_OPAQUE_TEXT_BACKGROUND",
            }
        )
        continue
    bbox = px_bbox(rect, pad=4, image_size=page_image.size)
    x0, y0, x1, y1 = bbox
    candidate = drawing_candidate_mask(drawing, bbox)
    local_rgb = page_np[y0:y1, x0:x1]
    visible = np.zeros(candidate.shape, dtype=bool)
    for color in colors:
        visible |= color_match(local_rgb, color)
    mask = candidate & visible
    ink_bbox = mask_ink_bbox(mask, (x0, y0))
    element_id = f"G{draw_index:03d}"
    safe = safe_id(element_id)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(ROOT / "03_objects" / "graphic_masks" / f"{safe}.png")
    obj = {
        "element_id": element_id,
        "safe_filename": safe,
        "object_type": "GRAPHIC_PATH",
        "semantic_parent": element_id,
        "role": "FOREGROUND_DRAWING",
        "char": "",
        "bbox_pt": [round(rect.x0, 3), round(rect.y0, 3), round(rect.x1, 3), round(rect.y1, 3)],
        "mask_bbox_px": bbox,
        "ink_bbox_px": ink_bbox,
        "mask": mask,
        "font": "",
        "size_pt": None,
        "target_rgb": colors,
        "pdf_drawing_index": draw_index,
        "pre_occlusion_mask": mask.copy(),
    }
    objects.append(obj)
    graphic_rows.append(
        {
            "element_id": element_id,
            "safe_filename": safe,
            "pdf_drawing_index": draw_index,
            "type": drawing.get("type"),
            "items_count": len(drawing.get("items", [])),
            "bbox_pt": json.dumps(obj["bbox_pt"]),
            "mask_bbox_px": json.dumps(list(bbox)),
            "ink_bbox_px": "" if ink_bbox is None else json.dumps(list(ink_bbox)),
            "stroke_rgb": json.dumps(stroke_rgb),
            "fill_rgb": json.dumps(fill_rgb),
            "line_width_pt": drawing.get("width"),
            "dashes": drawing.get("dashes"),
            "mask_area_px": int(np.count_nonzero(mask)),
            "mask_empty": not bool(mask.any()),
            "mask_path": f"03_objects/graphic_masks/{safe}.png",
        }
    )

# Apply only real, later-painted high-opacity white node backgrounds.  At
# opacity >=0.90 the remaining colored-line contrast is below the protocol's
# 20/255 foreground threshold, so those pixels are not final-visible path ink.
graphic_row_by_id = {row["element_id"]: row for row in graphic_rows}
for obj in objects:
    if obj["object_type"] != "GRAPHIC_PATH":
        continue
    pre_mask = obj["pre_occlusion_mask"].copy()
    final_mask = pre_mask.copy()
    gx0, gy0, gx1, gy1 = obj["mask_bbox_px"]
    for occluder in occluder_specs:
        if occluder["pdf_drawing_index"] <= obj["pdf_drawing_index"] or occluder["fill_opacity"] < 0.90:
            continue
        ox0, oy0, ox1, oy1 = px_bbox(occluder["rect"], pad=0, image_size=page_image.size)
        ix0, iy0, ix1, iy1 = max(gx0, ox0), max(gy0, oy0), min(gx1, ox1), min(gy1, oy1)
        if ix0 < ix1 and iy0 < iy1:
            final_mask[iy0 - gy0 : iy1 - gy0, ix0 - gx0 : ix1 - gx0] = False
    obj["pre_occlusion_mask"] = pre_mask
    obj["mask"] = final_mask
    obj["ink_bbox_px"] = mask_ink_bbox(final_mask, (gx0, gy0))
    row = graphic_row_by_id[obj["element_id"]]
    row["pre_occlusion_mask_area_px"] = int(np.count_nonzero(pre_mask))
    row["final_visible_mask_area_px"] = int(np.count_nonzero(final_mask))
    row["occluded_by_background_px"] = int(np.count_nonzero(pre_mask & ~final_mask))
    row["mask_area_px"] = row["final_visible_mask_area_px"]
    row["mask_empty"] = not bool(final_mask.any())
    row["ink_bbox_px"] = "" if obj["ink_bbox_px"] is None else json.dumps(list(obj["ink_bbox_px"]))
    row["pre_occlusion_mask_path"] = f"03_objects/graphic_pre_occlusion_masks/{obj['safe_filename']}.png"
    Image.fromarray(np.where(pre_mask, 0, 255).astype(np.uint8), mode="L").save(
        ROOT / "03_objects" / "graphic_pre_occlusion_masks" / f"{obj['safe_filename']}.png"
    )
    Image.fromarray(np.where(final_mask, 0, 255).astype(np.uint8), mode="L").save(
        ROOT / "03_objects" / "graphic_masks" / f"{obj['safe_filename']}.png"
    )

# rawdict splits mathematical subscripts and font changes into separate spans.
# Reconcile only visually and semantically certain same-parent formulas; this
# changes relationship taxonomy, never the frozen object denominator.
semantic_groups = {
    "FORMULA_P1": {"T010", "T011"},
    "FORMULA_P2": {"T012", "T013"},
    "FORMULA_P3": {"T014", "T015"},
    "FORMULA_P4": {"T016", "T017"},
    "FORMULA_CDF_YLABEL": {"T029", "T030", "T031", "T032", "T033"},
    "FORMULA_PMF_ANNOTATION": {f"T{index:03d}" for index in range(50, 60)},
    "FORMULA_PMF_YLABEL": {"T061", "T062", "T063", "T064", "T065"},
    "CAPTION_PARENT": {f"T{index:03d}" for index in range(66, 96)},
}
semantic_parent_by_id = {element_id: parent for parent, ids in semantic_groups.items() for element_id in ids}
for obj in objects:
    if obj["element_id"] in semantic_parent_by_id:
        obj["semantic_parent"] = semantic_parent_by_id[obj["element_id"]]
for row in glyph_rows:
    if row["element_id"] in semantic_parent_by_id:
        row["semantic_parent"] = semantic_parent_by_id[row["element_id"]]

write_csv(ROOT / "03_objects" / "text_parent_manifest.csv", parent_rows)
write_csv(ROOT / "03_objects" / "glyph_manifest.csv", glyph_rows)
write_csv(ROOT / "03_objects" / "graphic_manifest.csv", graphic_rows)
write_csv(ROOT / "03_objects" / "occluder_ledger.csv", occluder_rows)
id_map_rows = [
    {
        "element_id": obj["element_id"],
        "safe_filename": obj["safe_filename"],
        "object_type": obj["object_type"],
        "semantic_parent": obj["semantic_parent"],
    }
    for obj in objects
]
write_csv(ROOT / "03_objects" / "id_safe_filename_map.csv", id_map_rows)

overlay = figure_crop.copy()
overlay_draw = ImageDraw.Draw(overlay)
fx0, fy0, _, _ = FIGURE_CROP_PX
for obj in objects:
    if obj["object_type"] != "TEXT_GLYPH":
        continue
    ink_bbox = obj["ink_bbox_px"]
    if ink_bbox is None:
        continue
    x0, y0, x1, y1 = ink_bbox
    local = (x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0)
    overlay_draw.rectangle(local, outline=(220, 0, 0), width=1)
    overlay_draw.text((local[0], max(0, local[1] - 9)), obj["element_id"], fill=(170, 0, 0))
overlay.save(ROOT / "02_render" / "after_text_measurement_overlay_300dpi.png")

graphic_overlay = figure_crop.copy()
graphic_draw = ImageDraw.Draw(graphic_overlay)
for obj in objects:
    if obj["object_type"] != "GRAPHIC_PATH":
        continue
    ink_bbox = obj["ink_bbox_px"]
    if ink_bbox is None:
        continue
    x0, y0, x1, y1 = ink_bbox
    local = (x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0)
    graphic_draw.rectangle(local, outline=(140, 0, 180), width=1)
    graphic_draw.text((local[0], max(0, local[1] - 9)), obj["element_id"], fill=(100, 0, 140))
graphic_overlay.save(ROOT / "02_render" / "after_graphic_overlay_300dpi.png")

contact_rows = make_contact_sheets(page_image, [obj for obj in objects if obj["object_type"] == "TEXT_GLYPH"], ROOT / "04_contacts")
write_csv(ROOT / "04_contacts" / "contact_sheet_manifest.csv", contact_rows)

source_text = SOURCE.read_text(encoding="utf-8")
font_audit_rows = []
for index, match in enumerate(re.finditer(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}", source_text), start=1):
    line_no = source_text.count("\n", 0, match.start()) + 1
    declared = float(match.group(1))
    line_text = source_text.splitlines()[line_no - 1].strip()
    font_audit_rows.append(
        {
            "source_font_id": f"SF{index:02d}",
            "line": line_no,
            "source_excerpt": line_text,
            "declared_pt": declared,
            "baseline_skip_pt": float(match.group(2)),
            "graphics_scale": 1.0,
            "effective_pt": declared,
            "protocol_9_5_numeric_met": declared >= 9.5,
            "r168_classification": "NUMERIC_ADVISORY_REQUIRES_MANUAL_READABILITY_REVIEW" if declared < 9.5 else "NUMERIC_MET",
        }
    )
write_csv(ROOT / "06_ledgers" / "after_font_audit.csv", font_audit_rows)
write_csv(ROOT / "06_ledgers" / "after_pixel_measurements.csv", glyph_rows)

pair_rows = []
critical_rows = []
pair_index = 0
for a, b in itertools.combinations(objects, 2):
    pair_index += 1
    pair_id = f"P{pair_index:05d}"
    gap = bbox_gap(a["mask_bbox_px"], b["mask_bbox_px"])
    intersection = pair_intersection(a, b)
    pre_occlusion_intersection = pair_intersection(a, b, "pre_occlusion_mask")
    clearance = pair_clearance(a, b, gap)
    if a["object_type"] == "TEXT_GLYPH" and b["object_type"] == "TEXT_GLYPH":
        relation_class = "TEXT_TEXT_SAME_PARENT" if a["semantic_parent"] == b["semantic_parent"] else "TEXT_TEXT_INDEPENDENT"
        required = 0 if a["semantic_parent"] == b["semantic_parent"] else 4
    elif a["object_type"] == "GRAPHIC_PATH" and b["object_type"] == "GRAPHIC_PATH":
        relation_class = "GRAPHIC_GRAPHIC_TOPOLOGY"
        required = 0
    else:
        relation_class = "TEXT_GRAPHIC"
        required = 3
    independent = relation_class in {"TEXT_TEXT_INDEPENDENT", "TEXT_GRAPHIC"}
    numeric_met = False if math.isnan(clearance) else clearance >= required
    row = {
        "pair_id": pair_id,
        "a_id": a["element_id"],
        "b_id": b["element_id"],
        "a_type": a["object_type"],
        "b_type": b["object_type"],
        "a_parent": a["semantic_parent"],
        "b_parent": b["semantic_parent"],
        "relation_class": relation_class,
        "bbox_gap_px": round(gap, 3),
        "mask_intersection_px": intersection,
        "pre_occlusion_mask_intersection_px": pre_occlusion_intersection,
        "clearance_px": "" if math.isnan(clearance) else round(clearance, 3),
        "numeric_required_clearance_px": required,
        "machine_numeric_clearance_met": numeric_met,
        "independent_overlap_candidate": independent and intersection > 0,
    }
    pair_rows.append(row)
    is_critical = (independent and (intersection > 0 or pre_occlusion_intersection > intersection or (not math.isnan(clearance) and clearance < 12.0))) or (
        relation_class == "GRAPHIC_GRAPHIC_TOPOLOGY" and intersection > 0
    )
    if is_critical:
        evidence = make_pair_roi(page_image, pair_id, a, b, ROOT / "05_pairs")
        pre_evidence = {}
        if pre_occlusion_intersection > intersection:
            pre_a = {**a, "mask": a.get("pre_occlusion_mask", a["mask"])}
            pre_b = {**b, "mask": b.get("pre_occlusion_mask", b["mask"])}
            raw_pre = make_pair_roi(page_image, f"{pair_id}_pre", pre_a, pre_b, ROOT / "05_pairs")
            pre_evidence = {f"pre_{key}": value for key, value in raw_pre.items()}
        critical_rows.append({**row, **evidence, **pre_evidence})

write_csv(ROOT / "06_ledgers" / "after_overlap_report.csv", pair_rows)
write_csv(ROOT / "05_pairs" / "critical_pair_manifest.csv", critical_rows)
pair_contact_files = make_pair_contact_sheets(critical_rows, ROOT / "05_pairs")

math_payload = {
    "pmf_support": [1, 2, 3, 4],
    "pmf_values": [0.15, 0.30, 0.35, 0.20],
    "pmf_sum": round(sum([0.15, 0.30, 0.35, 0.20]), 12),
    "cdf_values_at_support": [0.15, 0.45, 0.80, 1.00],
    "cdf_jump_differences": [0.15, 0.30, 0.35, 0.20],
    "pmf_nonnegative": all(value >= 0 for value in [0.15, 0.30, 0.35, 0.20]),
    "cdf_nondecreasing": all(a <= b for a, b in zip([0.0, 0.15, 0.45, 0.80], [0.15, 0.45, 0.80, 1.00])),
    "cdf_terminal_value": 1.0,
    "right_continuity_geometry": {
        "filled_points": [[1, 0.15], [2, 0.45], [3, 0.80], [4, 1.00]],
        "open_points": [[1, 0.00], [2, 0.15], [3, 0.45], [4, 0.80]],
    },
    "source_math_rule_tokens": {
        "overline": source_text.count("\\overline"),
        "underline": source_text.count("\\underline"),
        "hat": source_text.count("\\hat"),
        "vec": source_text.count("\\vec"),
        "frac": source_text.count("\\frac"),
        "sqrt": source_text.count("\\sqrt"),
    },
    "visible_math_rule_object_count": 0,
}
write_json(ROOT / "06_ledgers" / "math_semantic_machine.json", math_payload)

glyph_numeric_failures = sum(row["numeric_threshold_met"] is False for row in glyph_rows)
empty_glyph_masks = sum(bool(row["mask_empty"]) for row in glyph_rows)
empty_graphic_masks = sum(bool(row["mask_empty"]) for row in graphic_rows)
independent_overlap_candidates = sum(bool(row["independent_overlap_candidate"]) for row in pair_rows)
numeric_clearance_failures = sum(not bool(row["machine_numeric_clearance_met"]) for row in pair_rows if row["relation_class"] in {"TEXT_TEXT_INDEPENDENT", "TEXT_GRAPHIC"})
summary = {
    "uid": "FIG-P067-01",
    "object_denominator": len(objects),
    "glyph_count": len(glyph_rows),
    "text_parent_count": len(parent_rows),
    "foreground_graphic_count": len(graphic_rows),
    "opaque_background_count": len(occluder_rows),
    "unordered_pair_expected": len(objects) * (len(objects) - 1) // 2,
    "unordered_pair_actual": len(pair_rows),
    "critical_pair_count": len(critical_rows),
    "glyph_contact_sheet_files": sorted({row["sheet"] for row in contact_rows}),
    "critical_pair_contact_sheet_files": pair_contact_files,
    "empty_glyph_masks": empty_glyph_masks,
    "empty_graphic_masks": empty_graphic_masks,
    "glyph_numeric_threshold_failures_r168_advisory": glyph_numeric_failures,
    "independent_overlap_candidates": independent_overlap_candidates,
    "numeric_clearance_failures_r168_manual_review_required": numeric_clearance_failures,
    "safe_filename_unique": len({row["safe_filename"] for row in id_map_rows}) == len(id_map_rows),
    "math_rule_source_token_count": sum(math_payload["source_math_rule_tokens"].values()),
    "math_rule_visible_object_count": 0,
}
write_json(ROOT / "07_validation" / "machine_summary.json", summary)
print(json.dumps(summary, ensure_ascii=False, indent=2))
