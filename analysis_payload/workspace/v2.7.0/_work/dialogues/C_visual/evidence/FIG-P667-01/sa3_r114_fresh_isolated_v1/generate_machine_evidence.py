from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import unicodedata
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P667-01\sa3_r114_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_conjugate_update.tex")
PAGE_PNG = ROOT / "page_0714_native300dpi.png"
PHYSICAL_PAGE = 714
PAGE_INDEX = PHYSICAL_PAGE - 1
PDF_EXPECTED_BYTES = 4_967_122
PDF_EXPECTED_SHA256 = "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6"
TEX_EXPECTED_BYTES = 3_252
TEX_EXPECTED_SHA256 = "1E2D755428EC466C6DF44B7684B81A354352653AE60476B4F717AD19F9D6CE15"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pt_to_page_px(rect: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (math.floor(x0 * sx), math.floor(y0 * sy), math.ceil(x1 * sx), math.ceil(y1 * sy))


def clip_rect(rect: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (max(0, x0), max(0, y0), min(width, x1), min(height, y1))


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def bbox_union(rects: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(r[0] for r in rects),
        min(r[1] for r in rects),
        max(r[2] for r in rects),
        max(r[3] for r in rects),
    )


pdf_bytes = PDF.stat().st_size
tex_bytes = TEX.stat().st_size
pdf_hash = sha256(PDF)
tex_hash = sha256(TEX)
assert pdf_bytes == PDF_EXPECTED_BYTES
assert tex_bytes == TEX_EXPECTED_BYTES
assert pdf_hash == PDF_EXPECTED_SHA256
assert tex_hash == TEX_EXPECTED_SHA256

doc = fitz.open(PDF)
assert doc.page_count == 817
page = doc[PAGE_INDEX]
page_image = Image.open(PAGE_PNG).convert("RGB")
page_np = np.asarray(page_image)
sx = page_image.width / page.rect.width
sy = page_image.height / page.rect.height
assert abs(sx - 300 / 72) < 0.01 and abs(sy - 300 / 72) < 0.01

# The crop was fixed from the vector/text geometry of the independently located figure.
# It contains the complete TikZ object and the complete two-line caption, with white padding.
crop_pt = (80.0, 320.0, 525.0, 608.0)
crop_page_px = pt_to_page_px(crop_pt, sx, sy)
crop_image = page_image.crop(crop_page_px)
crop_image.save(ROOT / "figure_caption_native300dpi.png")
ImageOps.grayscale(crop_image).save(ROOT / "figure_caption_grayscale_native300dpi.png")
crop_np = np.asarray(crop_image)
crop_w, crop_h = crop_image.size

raw = page.get_text("dict")
spans: list[dict[str, object]] = []
for block in raw["blocks"]:
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            spans.append(span)


def in_range(span: dict[str, object], x0: float, y0: float, x1: float, y1: float) -> bool:
    b = span["bbox"]
    cx = (b[0] + b[2]) / 2
    cy = (b[1] + b[3]) / 2
    return x0 <= cx <= x1 and y0 <= cy <= y1


def exact(text: str, y0: float = 0, y1: float = 999) -> list[dict[str, object]]:
    return [s for s in spans if s["text"] == text and y0 <= s["bbox"][1] <= y1]


text_defs = [
    {"object_id": "T01", "role": "row_label_prior", "expected_text": "先验核", "source_lines": "18", "declared_pt": 10.0, "parts": exact("先验核")},
    {"object_id": "T02", "role": "prior_kernel_formula", "expected_text": "p(θ|α)∝∏ᵢθᵢ^(αᵢ−1)", "source_lines": "18-19", "declared_pt": 9.4, "parts": [s for s in spans if in_range(s, 190, 330, 305, 366) and s["text"] != "先验指数"]},
    {"object_id": "T03", "role": "prior_underbrace_label", "expected_text": "先验指数", "source_lines": "19", "declared_pt": 8.5, "parts": exact("先验指数")},
    {"object_id": "T04", "role": "multiplication_symbol", "expected_text": "×", "source_lines": "25-26", "declared_pt": 15.0, "parts": exact("×")},
    {"object_id": "T05", "role": "row_label_likelihood", "expected_text": "似然核", "source_lines": "20", "declared_pt": 10.0, "parts": exact("似然核")},
    {"object_id": "T06", "role": "likelihood_kernel_formula", "expected_text": "p(n|θ)∝∏ᵢθᵢ^nᵢ", "source_lines": "20-21", "declared_pt": 9.4, "parts": [s for s in spans if in_range(s, 200, 395, 300, 432) and s["text"] != "计数"]},
    {"object_id": "T07", "role": "likelihood_underbrace_label", "expected_text": "计数", "source_lines": "21", "declared_pt": 8.5, "parts": exact("计数")},
    {"object_id": "T08", "role": "brace_annotation", "expected_text": "指数逐分量相加", "source_lines": "27-30", "declared_pt": 8.8, "parts": exact("指数逐分量相加")},
    {"object_id": "T09", "role": "row_label_posterior", "expected_text": "后验核", "source_lines": "22", "declared_pt": 10.0, "parts": exact("后验核")},
    {"object_id": "T10", "role": "posterior_kernel_formula", "expected_text": "p(θ|n,α)∝∏ᵢθᵢ^(αᵢ+nᵢ−1)", "source_lines": "22-23", "declared_pt": 9.4, "parts": [s for s in spans if in_range(s, 185, 460, 315, 498) and s["text"] != "逐分量相加"]},
    {"object_id": "T11", "role": "posterior_underbrace_label", "expected_text": "逐分量相加", "source_lines": "23", "declared_pt": 8.5, "parts": exact("逐分量相加")},
    {"object_id": "T12", "role": "posterior_result_line1", "expected_text": "θ|n", "source_lines": "31-34", "declared_pt": 9.4, "parts": [s for s in spans if in_range(s, 425, 465, 490, 481)]},
    {"object_id": "T13", "role": "posterior_result_line2", "expected_text": "∼Dir(α+n)", "source_lines": "31-34", "declared_pt": 9.4, "parts": [s for s in spans if in_range(s, 425, 481, 490, 496)]},
    {"object_id": "T14", "role": "marginal_formula", "expected_text": "p(n|α)=N!/∏ᵢnᵢ! · B(α+n)/B(α)", "source_lines": "36-39", "declared_pt": 8.8, "parts": [s for s in spans if in_range(s, 395, 534, 515, 562) and s["text"] != "保留归一化常数"], "drawing_indices": [16, 17]},
    {"object_id": "T15", "role": "marginal_note", "expected_text": "保留归一化常数", "source_lines": "36-39", "declared_pt": 8.8, "parts": exact("保留归一化常数")},
    {"object_id": "T16", "role": "caption_label", "expected_text": "图34.7", "source_lines": "42-43", "declared_pt": 10.0, "parts": [s for s in spans if 572 <= s["bbox"][1] <= 590 and s["text"] in {"图", "34.7"}]},
    {"object_id": "T17", "role": "caption_sentence", "expected_text": "Dirichlet–多项共轭来自先验核与多项似然核中同一组logθᵢ充分统计量：相乘只把指数逐分量相加，因此后验参数是α+n；保留归一化常数还可得到Dirichlet–多项边缘分布", "source_lines": "42-43", "declared_pt": 10.0, "parts": [s for s in spans if in_range(s, 80, 570, 525, 606) and s["text"] not in {"图", "34.7"}]},
]

graphic_defs = [
    {"object_id": "G01", "role": "prior_strip_border", "source_lines": "9-10,17-19", "drawing_indices": [9]},
    {"object_id": "G02", "role": "likelihood_strip_border", "source_lines": "9-10,17,20-21", "drawing_indices": [10]},
    {"object_id": "G03", "role": "posterior_strip_border", "source_lines": "9-10,17,22-23", "drawing_indices": [11]},
    {"object_id": "G04", "role": "exponent_brace", "source_lines": "27-30", "drawing_indices": [12]},
    {"object_id": "G05", "role": "main_arrow", "source_lines": "11,35", "drawing_indices": [14, 15]},
    {"object_id": "G06", "role": "posterior_result_box_border", "source_lines": "31-34", "drawing_indices": [13]},
    {"object_id": "G07", "role": "marginal_branch_arrow", "source_lines": "12-13,40", "drawing_indices": [18, 19]},
]

for definition in text_defs:
    assert definition["parts"], definition["object_id"]

drawings = page.get_drawings()
mask_dir = ROOT / "masks"
mask_dir.mkdir(exist_ok=True)
objects: list[dict[str, object]] = []
masks: dict[str, np.ndarray] = {}
measurement_rows: list[dict[str, object]] = []
codepoint_rows: list[dict[str, object]] = []


def add_region_foreground(mask: np.ndarray, rect_pt: tuple[float, float, float, float], threshold: int = 20, expand_px: int = 1, against_white: bool = False) -> None:
    page_rect = pt_to_page_px(rect_pt, sx, sy)
    x0 = page_rect[0] - crop_page_px[0] - expand_px
    y0 = page_rect[1] - crop_page_px[1] - expand_px
    x1 = page_rect[2] - crop_page_px[0] + expand_px
    y1 = page_rect[3] - crop_page_px[1] + expand_px
    x0, y0, x1, y1 = clip_rect((x0, y0, x1, y1), crop_w, crop_h)
    if x1 <= x0 or y1 <= y0:
        return
    region = crop_np[y0:y1, x0:x1].astype(np.int16)
    if against_white:
        background = np.array([255, 255, 255], dtype=np.int16)
    else:
        background = np.median(region.reshape(-1, 3), axis=0)
    local = np.max(np.abs(region - background), axis=2) >= threshold
    mask[y0:y1, x0:x1] |= local


def point_to_crop_px(point: fitz.Point) -> tuple[float, float]:
    return (point.x * sx - crop_page_px[0], point.y * sy - crop_page_px[1])


def cubic_points(p0: fitz.Point, p1: fitz.Point, p2: fitz.Point, p3: fitz.Point, samples: int = 40) -> list[tuple[float, float]]:
    values: list[tuple[float, float]] = []
    for step in range(samples + 1):
        t = step / samples
        u = 1.0 - t
        x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
        values.append((x * sx - crop_page_px[0], y * sy - crop_page_px[1]))
    return values


def vector_drawing_mask(indices: list[int], fill_indices: set[int] | None = None) -> np.ndarray:
    fill_indices = fill_indices or set()
    canvas = Image.new("L", (crop_w, crop_h), 0)
    painter = ImageDraw.Draw(canvas)
    for index in indices:
        drawing = drawings[index]
        width = max(1, int(round(float(drawing.get("width") or 0.5) * (sx + sy) / 2)))
        polygon_points: list[tuple[float, float]] = []
        for item in drawing["items"]:
            if item[0] == "l":
                p0, p1 = item[1], item[2]
                a, b = point_to_crop_px(p0), point_to_crop_px(p1)
                painter.line((a, b), fill=255, width=width)
                if not polygon_points:
                    polygon_points.append(a)
                polygon_points.append(b)
            elif item[0] == "c":
                points = cubic_points(item[1], item[2], item[3], item[4])
                painter.line(points, fill=255, width=width)
                if not polygon_points:
                    polygon_points.append(points[0])
                polygon_points.extend(points[1:])
            else:
                raise RuntimeError(f"Unhandled drawing command {item[0]!r} for drawing {index}")
        if index in fill_indices and len(polygon_points) >= 3:
            painter.polygon(polygon_points, fill=255)
    return np.asarray(canvas) > 0


for definition in text_defs:
    object_id = definition["object_id"]
    mask = np.zeros((crop_h, crop_w), dtype=bool)
    part_rects: list[tuple[float, float, float, float]] = []
    part_heights: list[int] = []
    part_font_sizes: list[float] = []
    for span in definition["parts"]:
        rect = tuple(float(v) for v in span["bbox"])
        part_rects.append(rect)
        part_font_sizes.append(float(span["size"]))
        before = mask.copy()
        add_region_foreground(mask, rect, threshold=20, expand_px=0)
        delta = mask & ~before
        local_bbox = bbox_from_mask(delta)
        if local_bbox:
            part_heights.append(local_bbox[3] - local_bbox[1])
    for index in definition.get("drawing_indices", []):
        r = drawings[index]["rect"]
        rect = (r.x0, r.y0, r.x1, r.y1)
        part_rects.append(rect)
    if definition.get("drawing_indices"):
        mask |= vector_drawing_mask(list(definition["drawing_indices"]))
    actual_bbox = bbox_from_mask(mask)
    assert actual_bbox is not None, object_id
    masks[object_id] = mask
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(mask_dir / f"{object_id}.png")
    extracted_parts = [str(s["text"]) for s in sorted(definition["parts"], key=lambda s: (s["bbox"][1], s["bbox"][0]))]
    extracted = "|".join(extracted_parts)
    bbox_pt = bbox_union(part_rects)
    base_vector_pt = max(part_font_sizes)
    min_vector_pt = min(part_font_sizes)
    declared_pt = float(definition["declared_pt"])
    objects.append({
        "object_id": object_id,
        "object_class": "TEXT",
        "role": definition["role"],
        "source_lines": definition["source_lines"],
        "expected_text": definition["expected_text"],
        "pdf_bbox_pt": ",".join(f"{v:.3f}" for v in bbox_pt),
        "rendered_ink_bbox_crop_px": ",".join(str(v) for v in actual_bbox),
        "mask_ink_pixel_count": int(mask.sum()),
    })
    measurement_rows.append({
        "object_id": object_id,
        "role": definition["role"],
        "source_declared_pt": f"{declared_pt:.3f}",
        "graphics_scale_from_base_vector": f"{base_vector_pt / declared_pt:.6f}",
        "base_vector_font_pt": f"{base_vector_pt:.6f}",
        "minimum_vector_span_pt": f"{min_vector_pt:.6f}",
        "union_ink_height_px": actual_bbox[3] - actual_bbox[1],
        "minimum_nonempty_span_ink_height_px": min(part_heights) if part_heights else "",
        "mask_ink_pixel_count": int(mask.sum()),
        "span_count": len(definition["parts"]),
    })
    cps = [ord(ch) for ch in extracted]
    codepoint_rows.append({
        "object_id": object_id,
        "expected_text": definition["expected_text"],
        "extracted_text_parts": extracted,
        "extracted_codepoints": " ".join(f"U+{cp:04X}" for cp in cps),
        "replacement_character_count": sum(cp == 0xFFFD for cp in cps),
        "private_use_count": sum(0xE000 <= cp <= 0xF8FF for cp in cps),
        "null_count": sum(cp == 0 for cp in cps),
        "white_square_codepoint_count": sum(cp == 0x25A1 for cp in cps),
        "unicode_names": " | ".join(unicodedata.name(ch, "UNNAMED") for ch in extracted if ch != "|"),
    })

for definition in graphic_defs:
    object_id = definition["object_id"]
    mask = np.zeros((crop_h, crop_w), dtype=bool)
    rects: list[tuple[float, float, float, float]] = []
    for index in definition["drawing_indices"]:
        r = drawings[index]["rect"]
        rect = (r.x0, r.y0, r.x1, r.y1)
        rects.append(rect)
    fill_indices = {15} if object_id == "G05" else set()
    mask |= vector_drawing_mask(list(definition["drawing_indices"]), fill_indices=fill_indices)
    actual_bbox = bbox_from_mask(mask)
    assert actual_bbox is not None, object_id
    masks[object_id] = mask
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(mask_dir / f"{object_id}.png")
    bbox_pt = bbox_union(rects)
    objects.append({
        "object_id": object_id,
        "object_class": "GRAPHIC",
        "role": definition["role"],
        "source_lines": definition["source_lines"],
        "expected_text": "",
        "pdf_bbox_pt": ",".join(f"{v:.3f}" for v in bbox_pt),
        "rendered_ink_bbox_crop_px": ",".join(str(v) for v in actual_bbox),
        "mask_ink_pixel_count": int(mask.sum()),
    })

objects.sort(key=lambda row: row["object_id"])
object_ids = [row["object_id"] for row in objects]
assert object_ids == [f"G{i:02d}" for i in range(1, 8)] + [f"T{i:02d}" for i in range(1, 18)]
assert len(objects) == 24

write_csv(
    ROOT / "object_denominator_machine.csv",
    ["object_id", "object_class", "role", "source_lines", "expected_text", "pdf_bbox_pt", "rendered_ink_bbox_crop_px", "mask_ink_pixel_count"],
    objects,
)
write_csv(
    ROOT / "text_measurements_machine.csv",
    ["object_id", "role", "source_declared_pt", "graphics_scale_from_base_vector", "base_vector_font_pt", "minimum_vector_span_pt", "union_ink_height_px", "minimum_nonempty_span_ink_height_px", "mask_ink_pixel_count", "span_count"],
    measurement_rows,
)
write_csv(
    ROOT / "codepoint_report_machine.csv",
    ["object_id", "expected_text", "extracted_text_parts", "extracted_codepoints", "replacement_character_count", "private_use_count", "null_count", "white_square_codepoint_count", "unicode_names"],
    codepoint_rows,
)

distance_fields = {object_id: distance_transform_edt(~masks[object_id]) for object_id in object_ids}
pair_rows: list[dict[str, object]] = []
for left, right in itertools.combinations(object_ids, 2):
    intersection = int(np.count_nonzero(masks[left] & masks[right]))
    if intersection:
        center_distance = 0.0
        empty_clearance = 0.0
    else:
        center_distance = float(distance_fields[left][masks[right]].min())
        empty_clearance = max(0.0, center_distance - 1.0)
    pair_rows.append({
        "pair_id": f"{left}__{right}",
        "left_object_id": left,
        "right_object_id": right,
        "visible_ink_intersection_px": intersection,
        "minimum_pixel_center_distance_px": f"{center_distance:.3f}",
        "minimum_empty_pixel_clearance_px": f"{empty_clearance:.3f}",
        "machine_close_candidate": int(intersection > 0 or empty_clearance < 16.0),
    })
assert len(pair_rows) == math.comb(len(object_ids), 2) == 276
write_csv(
    ROOT / "unordered_pair_table_machine.csv",
    ["pair_id", "left_object_id", "right_object_id", "visible_ink_intersection_px", "minimum_pixel_center_distance_px", "minimum_empty_pixel_clearance_px", "machine_close_candidate"],
    pair_rows,
)

candidate_dir = ROOT / "candidate_pair_overlays"
candidate_dir.mkdir(exist_ok=True)
candidate_rows = []
for row in pair_rows:
    if int(row["visible_ink_intersection_px"]) == 0:
        continue
    left = str(row["left_object_id"])
    right = str(row["right_object_id"])
    left_box = bbox_from_mask(masks[left])
    right_box = bbox_from_mask(masks[right])
    assert left_box is not None and right_box is not None
    pad = 18
    roi_box = clip_rect((
        min(left_box[0], right_box[0]) - pad,
        min(left_box[1], right_box[1]) - pad,
        max(left_box[2], right_box[2]) + pad,
        max(left_box[3], right_box[3]) + pad,
    ), crop_w, crop_h)
    base = np.asarray(crop_image.crop(roi_box)).astype(np.float32)
    left_roi = masks[left][roi_box[1]:roi_box[3], roi_box[0]:roi_box[2]]
    right_roi = masks[right][roi_box[1]:roi_box[3], roi_box[0]:roi_box[2]]
    both_roi = left_roi & right_roi
    base[left_roi] = 0.30 * base[left_roi] + 0.70 * np.array([220, 20, 60], dtype=np.float32)
    base[right_roi] = 0.30 * base[right_roi] + 0.70 * np.array([0, 100, 255], dtype=np.float32)
    base[both_roi] = np.array([255, 215, 0], dtype=np.float32)
    candidate = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    pair_id = str(row["pair_id"])
    native_path = candidate_dir / f"{pair_id}_native1x.png"
    nearest_path = candidate_dir / f"{pair_id}_nearest8x.png"
    candidate.save(native_path)
    candidate.resize((candidate.width * 8, candidate.height * 8), resample=Image.Resampling.NEAREST).save(nearest_path)
    candidate_rows.append({
        "pair_id": pair_id,
        "left_color": "red",
        "right_color": "blue",
        "intersection_color": "yellow",
        "intersection_px": row["visible_ink_intersection_px"],
        "crop_bbox_px": ",".join(str(v) for v in roi_box),
        "native1x_width_px": candidate.width,
        "native1x_height_px": candidate.height,
    })
write_csv(
    ROOT / "candidate_pair_overlay_index_machine.csv",
    ["pair_id", "left_color", "right_color", "intersection_color", "intersection_px", "crop_bbox_px", "native1x_width_px", "native1x_height_px"],
    candidate_rows,
)

union_mask = np.zeros((crop_h, crop_w), dtype=bool)
for mask in masks.values():
    union_mask |= mask
Image.fromarray((union_mask.astype(np.uint8) * 255), mode="L").save(ROOT / "visible_ink_union_mask_native300dpi.png")

palette = [
    (220, 20, 60), (0, 120, 255), (0, 170, 80), (255, 140, 0),
    (150, 50, 200), (0, 170, 170), (220, 80, 160), (110, 80, 40),
]
overlay = np.asarray(crop_image).astype(np.float32)
for index, object_id in enumerate(object_ids):
    color = np.array(palette[index % len(palette)], dtype=np.float32)
    mask = masks[object_id]
    overlay[mask] = 0.35 * overlay[mask] + 0.65 * color
Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8)).save(ROOT / "semantic_object_mask_overlay_native300dpi.png")

bbox_overlay = crop_image.copy()
draw = ImageDraw.Draw(bbox_overlay)
try:
    label_font = ImageFont.truetype("arial.ttf", 24)
except OSError:
    label_font = ImageFont.load_default()
for index, object_id in enumerate(object_ids):
    box = bbox_from_mask(masks[object_id])
    assert box is not None
    color = palette[index % len(palette)]
    draw.rectangle(box, outline=color, width=3)
    tx, ty = box[0], max(0, box[1] - 26)
    draw.rectangle((tx, ty, tx + 52, ty + 25), fill=(255, 255, 255))
    draw.text((tx + 2, ty), object_id, fill=color, font=label_font)
bbox_overlay.save(ROOT / "object_bbox_overlay_native300dpi.png")

edge_width = 6
edge_ink = int(
    union_mask[:edge_width, :].sum()
    + union_mask[-edge_width:, :].sum()
    + union_mask[:, :edge_width].sum()
    + union_mask[:, -edge_width:].sum()
)
clip_rows = []
for row in objects:
    object_id = str(row["object_id"])
    box = bbox_from_mask(masks[object_id])
    assert box is not None
    clip_rows.append({
        "object_id": object_id,
        "left_margin_px": box[0],
        "top_margin_px": box[1],
        "right_margin_px": crop_w - box[2],
        "bottom_margin_px": crop_h - box[3],
        "crop_boundary_contact_pixel_count": int(
            masks[object_id][:edge_width, :].sum()
            + masks[object_id][-edge_width:, :].sum()
            + masks[object_id][:, :edge_width].sum()
            + masks[object_id][:, -edge_width:].sum()
        ),
    })
write_csv(
    ROOT / "clip_check_machine.csv",
    ["object_id", "left_margin_px", "top_margin_px", "right_margin_px", "bottom_margin_px", "crop_boundary_contact_pixel_count"],
    clip_rows,
)

roi_defs = [
    ("ROI01_prior_exponent_label", (250.0, 330.0, 307.0, 366.0)),
    ("ROI02_likelihood_exponent_label", (258.0, 395.0, 300.0, 432.0)),
    ("ROI03_multiply_brace_annotation", (240.0, 366.0, 435.0, 397.0)),
    ("ROI04_posterior_exponent_label", (250.0, 460.0, 316.0, 498.0)),
    ("ROI05_main_arrow_and_result", (342.0, 454.0, 518.0, 507.0)),
    ("ROI06_branch_and_marginal", (395.0, 495.0, 518.0, 575.0)),
    ("ROI07_caption_line1", (82.0, 569.0, 523.0, 590.0)),
    ("ROI08_caption_line2", (82.0, 587.0, 465.0, 604.0)),
]
roi_dir = ROOT / "decisive_rois"
roi_dir.mkdir(exist_ok=True)
roi_rows = []
for roi_id, rect_pt in roi_defs:
    page_rect = pt_to_page_px(rect_pt, sx, sy)
    roi = page_image.crop(page_rect)
    roi_1x = roi_dir / f"{roi_id}_native1x.png"
    roi_8x = roi_dir / f"{roi_id}_nearest8x.png"
    roi.save(roi_1x)
    roi.resize((roi.width * 8, roi.height * 8), resample=Image.Resampling.NEAREST).save(roi_8x)
    roi_rows.append({
        "roi_id": roi_id,
        "pdf_bbox_pt": ",".join(f"{v:.3f}" for v in rect_pt),
        "native1x_width_px": roi.width,
        "native1x_height_px": roi.height,
        "nearest8x_width_px": roi.width * 8,
        "nearest8x_height_px": roi.height * 8,
    })
write_csv(
    ROOT / "decisive_roi_index_machine.csv",
    ["roi_id", "pdf_bbox_pt", "native1x_width_px", "native1x_height_px", "nearest8x_width_px", "nearest8x_height_px"],
    roi_rows,
)

write_json(
    ROOT / "machine_material_identity.json",
    {
        "pdf": {"path": str(PDF), "bytes": pdf_bytes, "sha256": pdf_hash, "page_count": doc.page_count},
        "tex": {"path": str(TEX), "bytes": tex_bytes, "sha256": tex_hash},
        "selected_physical_page": PHYSICAL_PAGE,
        "selection_basis": "caption and figure semantics: Dirichlet-multinomial conjugacy, componentwise exponent addition, posterior alpha+n, and marginal beta-function ratio",
        "page_size_pt": [page.rect.width, page.rect.height],
        "native300dpi_page_size_px": [page_image.width, page_image.height],
        "native300dpi_scale_px_per_pt": [sx, sy],
        "figure_caption_crop_pt": list(crop_pt),
        "figure_caption_crop_page_px": list(crop_page_px),
    },
)

write_json(
    ROOT / "machine_summary.json",
    {
        "uid": "FIG-P667-01",
        "physical_page": PHYSICAL_PAGE,
        "reader_visible_object_count": len(object_ids),
        "unordered_pair_count": len(pair_rows),
        "expected_unordered_pair_count": math.comb(len(object_ids), 2),
        "text_object_count": len(text_defs),
        "graphic_object_count": len(graphic_defs),
        "machine_close_candidate_pair_count": sum(int(r["machine_close_candidate"]) for r in pair_rows),
        "machine_nonzero_intersection_pair_count": sum(int(r["visible_ink_intersection_px"]) > 0 for r in pair_rows),
        "union_crop_boundary_edge_ink_count": edge_ink,
        "codepoint_replacement_character_count": sum(int(r["replacement_character_count"]) for r in codepoint_rows),
        "codepoint_private_use_count": sum(int(r["private_use_count"]) for r in codepoint_rows),
        "codepoint_null_count": sum(int(r["null_count"]) for r in codepoint_rows),
        "codepoint_white_square_count": sum(int(r["white_square_codepoint_count"]) for r in codepoint_rows),
        "decisive_roi_count": len(roi_rows),
        "machine_only_notice": "No manual reviewer, verdict, decision, acceptance, or note fields are generated by this script.",
    },
)

print(json.dumps({
    "physical_page": PHYSICAL_PAGE,
    "object_count": len(object_ids),
    "pair_count": len(pair_rows),
    "close_candidate_pair_count": sum(int(r["machine_close_candidate"]) for r in pair_rows),
    "nonzero_intersection_pair_count": sum(int(r["visible_ink_intersection_px"]) > 0 for r in pair_rows),
    "crop_edge_ink_count": edge_ink,
}, ensure_ascii=False))
