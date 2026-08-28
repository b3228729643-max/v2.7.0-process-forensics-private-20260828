from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa1_r114_fresh_isolated_v1")
PAGE_NUMBER = 717
PAGE_INDEX = PAGE_NUMBER - 1
FIGURE_RECT = fitz.Rect(55.0, 65.0, 540.0, 228.0)
KEY_ROI_RECT = fitz.Rect(64.0, 103.0, 215.0, 163.0)

RENDERS = ROOT / "renders"
MACHINE = ROOT / "machine"
RENDERS.mkdir(exist_ok=True)
MACHINE.mkdir(exist_ok=True)

# Complete visible semantic-object denominator for the figure and its caption.
# Coordinates are PDF points on physical page 717.
OBJECTS = [
    ("OBJ01", "left_title", 67.7370, 84.0865, 203.0665, 98.2238),
    ("OBJ02", "left_count_row", 67.3692, 101.1430, 234.6150, 118.1510),
    ("OBJ03", "left_predictive_formula", 82.0100, 136.0348, 195.7388, 159.0705),
    ("OBJ04", "left_probability_bar", 75.8732, 123.2533, 203.4339, 133.0890),
    ("OBJ05", "observation_node", 256.8902, 107.5436, 297.3809, 148.0343),
    ("OBJ06", "prediction_arrow_and_label", 203.4339, 83.7593, 256.8902, 129.0000),
    ("OBJ07", "update_arrow_and_label", 297.3809, 72.3693, 349.5602, 129.0000),
    ("OBJ08", "right_title", 365.0790, 84.0865, 449.9760, 98.2238),
    ("OBJ09", "right_count_row", 333.8291, 101.1430, 519.5006, 118.1510),
    ("OBJ10", "right_update_formula", 344.7960, 139.7408, 498.6027, 150.8314),
    ("OBJ11", "right_probability_bar", 356.5065, 123.2533, 484.0672, 133.0890),
    ("OBJ12", "takeaway_box", 111.3066, 161.1909, 482.6499, 178.8607),
    ("OBJ13", "caption_label", 76.1380, 181.8573, 110.3722, 196.2832),
    ("OBJ14", "caption_line_1", 120.3350, 185.4439, 507.8065, 196.1139),
    ("OBJ15", "caption_line_2", 76.1380, 198.8339, 507.8004, 209.5039),
    ("OBJ16", "caption_line_3", 76.1380, 212.2239, 96.0633, 222.8939),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def render(page: fitz.Page, dpi: int, clip: fitz.Rect | None, path: Path, colorspace=fitz.csRGB) -> None:
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pixmap = page.get_pixmap(matrix=matrix, clip=clip, colorspace=colorspace, alpha=False)
    pixmap.save(path)


def point_bbox_to_crop_pixels(bbox: tuple[float, float, float, float], scale: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        round((x0 - FIGURE_RECT.x0) * scale),
        round((y0 - FIGURE_RECT.y0) * scale),
        round((x1 - FIGURE_RECT.x0) * scale),
        round((y1 - FIGURE_RECT.y0) * scale),
    )


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]

full_200 = RENDERS / "full_page_200dpi.png"
full_300 = RENDERS / "full_page_native_300dpi.png"
crop_300 = RENDERS / "figure_crop_native_300dpi.png"
gray_300 = RENDERS / "figure_crop_grayscale_300dpi.png"
roi_1x = RENDERS / "key_roi_native1x_300dpi.png"
roi_8x = RENDERS / "key_roi_nearest_neighbor_8x.png"
overlay_path = RENDERS / "semantic_object_overlay_300dpi.png"

render(page, 200, None, full_200)
render(page, 300, None, full_300)
render(page, 300, FIGURE_RECT, crop_300)
render(page, 300, FIGURE_RECT, gray_300, colorspace=fitz.csGRAY)
render(page, 300, KEY_ROI_RECT, roi_1x)

with Image.open(roi_1x) as roi:
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(roi_8x)

scale = 300.0 / 72.0
with Image.open(crop_300).convert("RGB") as base:
    overlay = base.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for index, (object_id, role, x0, y0, x1, y1) in enumerate(OBJECTS):
        box = point_bbox_to_crop_pixels((x0, y0, x1, y1), scale)
        color = (214, 39 + (index * 29) % 160, 40 + (index * 47) % 180)
        draw.rectangle(box, outline=color, width=4)
        label_xy = (box[0] + 3, max(0, box[1] - 13))
        draw.rectangle((label_xy[0] - 1, label_xy[1] - 1, label_xy[0] + 38, label_xy[1] + 12), fill=(255, 255, 255))
        draw.text(label_xy, object_id, fill=color, font=font)
    overlay.save(overlay_path)

with (MACHINE / "object_denominator.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["OBJECT_ID", "ROLE", "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT"])
    writer.writerows(OBJECTS)

with (MACHINE / "unordered_pair_geometry.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B", "BBOX_INTERSECTION_AREA_PT2", "BBOX_EDGE_GAP_PT"])
    for pair_index, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), start=1):
        aid, _, ax0, ay0, ax1, ay1 = a
        bid, _, bx0, by0, bx1, by1 = b
        ix = max(0.0, min(ax1, bx1) - max(ax0, bx0))
        iy = max(0.0, min(ay1, by1) - max(ay0, by0))
        dx = max(0.0, max(ax0, bx0) - min(ax1, bx1))
        dy = max(0.0, max(ay0, by0) - min(ay1, by1))
        gap = (dx * dx + dy * dy) ** 0.5
        writer.writerow([f"PAIR{pair_index:03d}", aid, bid, f"{ix * iy:.4f}", f"{gap:.4f}"])

span_records = []
with (MACHINE / "pdf_text_spans.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["SPAN_ID", "TEXT", "FONT", "SIZE_PT", "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT"])
    span_index = 0
    text_dict = page.get_text("dict", clip=FIGURE_RECT)
    for block in text_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text.strip():
                    continue
                span_index += 1
                x0, y0, x1, y1 = span["bbox"]
                record = [
                    f"SPAN{span_index:03d}", text, span.get("font", ""), f"{span.get('size', 0.0):.4f}",
                    f"{x0:.4f}", f"{y0:.4f}", f"{x1:.4f}", f"{y1:.4f}",
                ]
                writer.writerow(record)
                span_records.append((f"SPAN{span_index:03d}", text, x0, y0, x1, y1))

with Image.open(full_300).convert("L") as page_gray, (MACHINE / "pixel_ink_measurements.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.writer(handle)
    writer.writerow(["SPAN_ID", "TEXT", "BBOX_WIDTH_PX", "BBOX_HEIGHT_PX", "INK_WIDTH_PX", "INK_HEIGHT_PX", "INK_PIXEL_COUNT", "MIN_GRAY"])
    for span_id, text, x0, y0, x1, y1 in span_records:
        px_box = (
            max(0, int(x0 * scale)),
            max(0, int(y0 * scale)),
            min(page_gray.width, int(x1 * scale + 0.9999)),
            min(page_gray.height, int(y1 * scale + 0.9999)),
        )
        region = page_gray.crop(px_box)
        pixels = list(region.getdata())
        coords = [(idx % region.width, idx // region.width) for idx, value in enumerate(pixels) if value <= 190]
        if coords:
            xs = [coord[0] for coord in coords]
            ys = [coord[1] for coord in coords]
            ink_width = max(xs) - min(xs) + 1
            ink_height = max(ys) - min(ys) + 1
            min_gray = min(pixels)
        else:
            ink_width = 0
            ink_height = 0
            min_gray = min(pixels) if pixels else 255
        writer.writerow([
            span_id,
            text,
            region.width,
            region.height,
            ink_width,
            ink_height,
            len(coords),
            min_gray,
        ])

drawings = page.get_drawings()
with (MACHINE / "pdf_vector_drawings.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["DRAWING_ID", "TYPE", "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT", "ITEM_COUNT"])
    drawing_index = 0
    for drawing in drawings:
        rect = drawing["rect"]
        if not rect.intersects(FIGURE_RECT):
            continue
        drawing_index += 1
        writer.writerow([
            f"DRAW{drawing_index:03d}", drawing.get("type", ""), f"{rect.x0:.4f}", f"{rect.y0:.4f}",
            f"{rect.x1:.4f}", f"{rect.y1:.4f}", len(drawing.get("items", [])),
        ])

metadata = {
    "pdf": str(PDF),
    "pdf_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "pdf_page_count": doc.page_count,
    "physical_page": PAGE_NUMBER,
    "printed_page": "704",
    "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
    "figure_rect_pt": [FIGURE_RECT.x0, FIGURE_RECT.y0, FIGURE_RECT.x1, FIGURE_RECT.y1],
    "key_roi_rect_pt": [KEY_ROI_RECT.x0, KEY_ROI_RECT.y0, KEY_ROI_RECT.x1, KEY_ROI_RECT.y1],
    "rendered_dpi": [200, 300],
    "semantic_object_count": len(OBJECTS),
    "unordered_pair_count": len(OBJECTS) * (len(OBJECTS) - 1) // 2,
    "text_span_count": span_index,
    "vector_drawing_count": drawing_index,
}
(MACHINE / "render_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps(metadata, ensure_ascii=False))
