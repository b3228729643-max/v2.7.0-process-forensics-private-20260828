from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "renders" / "physical_0684_300dpi.png"
OBJECTS_CSV = ROOT / "ledgers" / "object_denominator.csv"
TEXT_CSV = ROOT / "ledgers" / "text_denominator.csv"
ROI_CSV = ROOT / "ledgers" / "critical_roi_denominator.csv"
COMPONENTS_CSV = ROOT / "ledgers" / "object_geometry_components.csv"
FULL_CROP = (300, 1390, 2225, 2225)
PT_TO_PX = 300.0 / 72.0


COLORS = {
    "TEXT": (220, 20, 60),
    "FORMULA": (145, 30, 180),
    "LINE_ARROW": (0, 140, 70),
    "NODE_BORDER": (255, 125, 0),
    "PANEL_BORDER": (0, 90, 200),
}


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def page_px_box(row: dict[str, str]) -> tuple[int, int, int, int]:
    return tuple(
        round(float(row[key]) * PT_TO_PX)
        for key in ("x_min_pt", "y_min_pt", "x_max_pt", "y_max_pt")
    )


def crop_px_box(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    return x1 - FULL_CROP[0], y1 - FULL_CROP[1], x2 - FULL_CROP[0], y2 - FULL_CROP[1]


def draw_id(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, color: tuple[int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.rectangle(box, outline=color, width=3)
    label_font = font(16)
    tb = draw.textbbox((0, 0), label, font=label_font)
    w = tb[2] - tb[0] + 6
    h = tb[3] - tb[1] + 4
    lx = max(0, x1)
    ly = max(0, y1 - h)
    draw.rectangle((lx, ly, lx + w, ly + h), fill=(255, 255, 255), outline=color, width=1)
    draw.text((lx + 3, ly + 1), label, font=label_font, fill=color)


page = Image.open(PAGE).convert("RGB")
base = page.crop(FULL_CROP)
objects = load_csv(OBJECTS_CSV)
text_rows = load_csv(TEXT_CSV)
text_by_object = {row["object_id"]: row["text_id"] for row in text_rows}

# Object ID overlay.
obj_overlay = base.copy()
obj_draw = ImageDraw.Draw(obj_overlay)
for row in objects:
    draw_id(obj_draw, crop_px_box(page_px_box(row)), row["object_id"], COLORS[row["class"]])
obj_overlay.save(ROOT / "overlays" / "object_id_overlay_300dpi.png")

# Semantic class overlay.
sem_overlay = base.copy()
sem_draw = ImageDraw.Draw(sem_overlay)
for row in objects:
    box = crop_px_box(page_px_box(row))
    sem_draw.rectangle(box, outline=COLORS[row["class"]], width=4)
legend_y = 8
for index, (klass, color) in enumerate(COLORS.items()):
    x = 8 + index * 190
    sem_draw.rectangle((x, legend_y, x + 18, legend_y + 18), fill=color)
    sem_draw.text((x + 24, legend_y), klass, font=font(16), fill=color)
sem_overlay.save(ROOT / "overlays" / "semantic_class_overlay_300dpi.png")

# Text/formula measurement overlay.
text_overlay = base.copy()
text_draw = ImageDraw.Draw(text_overlay)
for row in objects:
    if row["object_id"] not in text_by_object:
        continue
    color = COLORS[row["class"]]
    draw_id(text_draw, crop_px_box(page_px_box(row)), text_by_object[row["object_id"]], color)
text_overlay.save(ROOT / "overlays" / "text_measurement_overlay_300dpi.png")

# Complete unordered pair geometry, with no reviewer or decision fields.
pair_path = ROOT / "raw" / "all_unordered_pair_geometry.csv"
candidate_path = ROOT / "raw" / "machine_candidate_pair_geometry.csv"
pair_fields = [
    "pair_id", "object_a", "class_a", "object_b", "class_b", "bbox_relation",
    "dx_gap_pt", "dy_gap_pt", "euclidean_gap_pt", "intersection_area_pt2", "containment_code",
]
candidate_rows: list[dict[str, str]] = []
with pair_path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=pair_fields)
    writer.writeheader()
    for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
        ax1, ay1, ax2, ay2 = (float(a[k]) for k in ("x_min_pt", "y_min_pt", "x_max_pt", "y_max_pt"))
        bx1, by1, bx2, by2 = (float(b[k]) for k in ("x_min_pt", "y_min_pt", "x_max_pt", "y_max_pt"))
        ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
        iy = max(0.0, min(ay2, by2) - max(ay1, by1))
        intersection = ix * iy
        dx = max(ax1 - bx2, bx1 - ax2, 0.0)
        dy = max(ay1 - by2, by1 - ay2, 0.0)
        distance = math.hypot(dx, dy)
        contains_ab = ax1 <= bx1 and ay1 <= by1 and ax2 >= bx2 and ay2 >= by2
        contains_ba = bx1 <= ax1 and by1 <= ay1 and bx2 >= ax2 and by2 >= ay2
        containment = "A_CONTAINS_B" if contains_ab else "B_CONTAINS_A" if contains_ba else "NONE"
        relation = "BBOX_INTERSECTION" if intersection > 0 else "BBOX_SEPARATED"
        result = {
            "pair_id": f"P{pair_index:04d}",
            "object_a": a["object_id"],
            "class_a": a["class"],
            "object_b": b["object_id"],
            "class_b": b["class"],
            "bbox_relation": relation,
            "dx_gap_pt": f"{dx:.3f}",
            "dy_gap_pt": f"{dy:.3f}",
            "euclidean_gap_pt": f"{distance:.3f}",
            "intersection_area_pt2": f"{intersection:.3f}",
            "containment_code": containment,
        }
        writer.writerow(result)
        if intersection > 0 or distance <= 2.0:
            candidate_rows.append(result)
with candidate_path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=pair_fields)
    writer.writeheader()
    writer.writerows(candidate_rows)

# Pixel masks are objective extraction aids. TEXT/FORMULA use dark raster ink;
# border classes use only a measured perimeter band; arrows use their local ink.
components_by_object: dict[str, list[dict[str, str]]] = {}
for component in load_csv(COMPONENTS_CSV):
    components_by_object.setdefault(component["object_id"], []).append(component)
page_array = np.asarray(page)
page_width = page.width


def object_pixel_codes(row: dict[str, str]) -> np.ndarray:
    regions = components_by_object.get(row["object_id"], [row])
    codes: list[np.ndarray] = []
    for region in regions:
        x1, y1, x2, y2 = page_px_box(region)
        patch = page_array[y1:y2, x1:x2]
        if patch.size == 0:
            continue
        gray_patch = np.asarray(ImageOps.grayscale(Image.fromarray(patch)))
        if row["class"] in {"TEXT", "FORMULA"}:
            local = gray_patch < 180
        elif row["class"] in {"NODE_BORDER", "PANEL_BORDER"}:
            local = gray_patch < 245
            band = np.zeros_like(local)
            edge = min(9, max(1, min(local.shape) // 3))
            band[:edge, :] = True
            band[-edge:, :] = True
            band[:, :edge] = True
            band[:, -edge:] = True
            local &= band
        else:
            local = gray_patch < 245
        yy, xx = np.nonzero(local)
        if len(xx):
            codes.append((yy.astype(np.int64) + y1) * page_width + (xx.astype(np.int64) + x1))
    if not codes:
        return np.empty(0, dtype=np.int64)
    return np.unique(np.concatenate(codes))


pixel_codes = {row["object_id"]: object_pixel_codes(row) for row in objects}


def chebyshev_center_distance(a_codes: np.ndarray, b_codes: np.ndarray) -> int:
    if len(a_codes) == 0 or len(b_codes) == 0:
        return -1
    if len(a_codes) > len(b_codes):
        a_codes, b_codes = b_codes, a_codes
    ay = a_codes // page_width
    ax = a_codes % page_width
    by = b_codes // page_width
    bx = b_codes % page_width
    best = 1 << 30
    for start in range(0, len(a_codes), 192):
        cy = ay[start:start + 192, None]
        cx = ax[start:start + 192, None]
        distances = np.maximum(np.abs(cy - by[None, :]), np.abs(cx - bx[None, :]))
        candidate = int(distances.min())
        if candidate < best:
            best = candidate
        if best == 0:
            break
    return best


pixel_fields = [
    "pair_id", "object_a", "object_b", "object_a_mask_pixels", "object_b_mask_pixels",
    "mask_intersection_pixels", "chebyshev_center_distance_px", "empty_pixel_clearance_px", "mask_method",
]
pixel_rows: list[dict[str, str | int]] = []
for pair in candidate_rows:
    a_codes = pixel_codes[pair["object_a"]]
    b_codes = pixel_codes[pair["object_b"]]
    intersection = int(np.intersect1d(a_codes, b_codes, assume_unique=True).size)
    center_distance = chebyshev_center_distance(a_codes, b_codes)
    clearance = -1 if center_distance < 0 else max(center_distance - 1, 0)
    pixel_rows.append({
        "pair_id": pair["pair_id"],
        "object_a": pair["object_a"],
        "object_b": pair["object_b"],
        "object_a_mask_pixels": len(a_codes),
        "object_b_mask_pixels": len(b_codes),
        "mask_intersection_pixels": intersection,
        "chebyshev_center_distance_px": center_distance,
        "empty_pixel_clearance_px": clearance,
        "mask_method": "dark_ink180_text_formula;perimeter_band9_gray245_border;gray245_arrow",
    })
with (ROOT / "raw" / "candidate_pixel_metrics.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=pixel_fields)
    writer.writeheader()
    writer.writerows(pixel_rows)

# Foreground semantic-mask overlay restricted to the figure+caption crop.
mask_overlay = base.convert("RGBA")
color_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
color_array = np.asarray(color_layer).copy()
for row in objects:
    color = COLORS[row["class"]]
    codes = pixel_codes[row["object_id"]]
    yy = codes // page_width - FULL_CROP[1]
    xx = codes % page_width - FULL_CROP[0]
    keep = (yy >= 0) & (yy < base.height) & (xx >= 0) & (xx < base.width)
    color_array[yy[keep], xx[keep], :] = (*color, 145)
color_layer = Image.fromarray(color_array, mode="RGBA")
mask_overlay.alpha_composite(color_layer)
mask_overlay.convert("RGB").save(ROOT / "overlays" / "semantic_foreground_mask_overlay_300dpi.png")

# Objective text box and raster-ink dimensions, without pass/fail fields.
gray = ImageOps.grayscale(page)
metric_fields = [
    "text_id", "object_id", "class", "vector_width_pt", "vector_height_pt",
    "vector_width_px", "vector_height_px", "ink_width_px", "ink_height_px", "ink_pixel_count_threshold230",
]
with (ROOT / "raw" / "text_raster_metrics.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=metric_fields)
    writer.writeheader()
    for row in objects:
        text_id = text_by_object.get(row["object_id"])
        if text_id is None:
            continue
        px_box = page_px_box(row)
        patch = gray.crop(px_box)
        mask = patch.point(lambda value: 255 if value < 230 else 0, mode="1")
        ink_bbox = mask.getbbox()
        ink_width = 0 if ink_bbox is None else ink_bbox[2] - ink_bbox[0]
        ink_height = 0 if ink_bbox is None else ink_bbox[3] - ink_bbox[1]
        ink_count = sum(1 for value in mask.getdata() if value)
        vw = float(row["x_max_pt"]) - float(row["x_min_pt"])
        vh = float(row["y_max_pt"]) - float(row["y_min_pt"])
        writer.writerow({
            "text_id": text_id,
            "object_id": row["object_id"],
            "class": row["class"],
            "vector_width_pt": f"{vw:.3f}",
            "vector_height_pt": f"{vh:.3f}",
            "vector_width_px": px_box[2] - px_box[0],
            "vector_height_px": px_box[3] - px_box[1],
            "ink_width_px": ink_width,
            "ink_height_px": ink_height,
            "ink_pixel_count_threshold230": ink_count,
        })

# Native 1x and nearest-neighbour 8x critical ROIs plus contact sheets.
roi_rows = load_csv(ROI_CSV)
native_items: list[tuple[str, Image.Image]] = []
zoom_items: list[tuple[str, Image.Image]] = []
for row in roi_rows:
    box = tuple(int(row[k]) for k in ("x_min_px", "y_min_px", "x_max_px", "y_max_px"))
    roi = page.crop(box)
    roi_name = row["roi_id"]
    roi.save(ROOT / "rois" / f"{roi_name}_native1x_300dpi.png")
    zoom = roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST)
    zoom.save(ROOT / "rois" / f"{roi_name}_nearest8x.png")
    native_items.append((roi_name, roi))
    zoom_items.append((roi_name, zoom))


def contact(items: list[tuple[str, Image.Image]], output: Path, max_width: int) -> None:
    label_height = 30
    margin = 12
    rows: list[tuple[str, Image.Image]] = []
    for label, item in items:
        if item.width > max_width:
            ratio = max_width / item.width
            item = item.resize((max_width, max(1, round(item.height * ratio))), Image.Resampling.NEAREST)
        rows.append((label, item))
    width = max(item.width for _, item in rows) + margin * 2
    height = sum(item.height + label_height + margin for _, item in rows) + margin
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    y = margin
    for label, item in rows:
        draw.text((margin, y), label, font=font(20), fill="black")
        y += label_height
        sheet.paste(item, (margin, y))
        y += item.height + margin
    sheet.save(output)


contact(native_items, ROOT / "rois" / "critical_rois_native1x_contact.png", 1905)
contact(zoom_items, ROOT / "rois" / "critical_rois_nearest8x_contact.png", 1905)

page_bytes = PAGE.read_bytes()
identity = {
    "page_image_path": str(PAGE),
    "page_image_bytes": len(page_bytes),
    "page_image_sha256": hashlib.sha256(page_bytes).hexdigest().upper(),
    "page_width_px": page.width,
    "page_height_px": page.height,
    "render_dpi": 300,
    "object_denominator": len(objects),
    "unordered_pair_denominator": len(objects) * (len(objects) - 1) // 2,
    "text_denominator": len(text_rows),
    "critical_roi_denominator": len(roi_rows),
    "machine_candidate_pair_count": len(candidate_rows),
    "machine_candidate_mask_intersection_pixel_sum": sum(int(row["mask_intersection_pixels"]) for row in pixel_rows),
}
with (ROOT / "raw" / "mechanical_identity_and_counts.json").open("w", encoding="utf-8") as stream:
    json.dump(identity, stream, ensure_ascii=False, indent=2)

print(json.dumps(identity, ensure_ascii=False))
