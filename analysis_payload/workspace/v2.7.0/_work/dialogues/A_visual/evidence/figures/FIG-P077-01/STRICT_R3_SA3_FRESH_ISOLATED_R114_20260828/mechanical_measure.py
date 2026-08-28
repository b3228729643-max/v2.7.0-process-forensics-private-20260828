from __future__ import annotations

import csv
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R3_SA3_FRESH_ISOLATED_R114_20260828")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
PHYSICAL_PAGE = 79
FIGURE_RECT = fitz.Rect(82.0, 420.0, 510.0, 614.0)
SCALE = 300.0 / 72.0


TEXT_GROUPS = {
    "T01": ["S01"],
    "T02": ["S02"],
    "T03": ["S03"],
    "T04": ["S04"],
    "T05": ["S05"],
    "T06": ["S06"],
    "T07": ["S07", "S08", "S09"],
    "T08": ["S10", "S12", "S13", "S14"],
    "T09": ["S11"],
    "T10": ["S15", "S16"],
    "T11": ["S17"],
    "T12": ["S18"],
    "T13": ["S19", "S20"],
    "T14": ["S21", "S22"],
}

GRAPHICS = {
    "G01": [130.8420, 559.3940, 480.9314, 563.6461],
    "G02": [128.7160, 430.6004, 132.9680, 561.5200],
    "G03": [130.8420, 438.8158, 480.9297, 544.3245],
    "G04": [130.8420, 491.5723, 480.9297, 540.1315],
    "G05": [130.8420, 438.8158, 480.9314, 544.3286],
    "G06": [130.8420, 491.5723, 480.9314, 544.3286],
    "G07": [305.8867, 437.2125, 305.8867, 544.3286],
    "G08": [169.7408, 549.0893, 442.0326, 552.0781],
    "B01": [343.0398, 450.1584, 434.1180, 463.4617],
    "B02": [385.8285, 495.1207, 493.4444, 508.4240],
    "B03": [264.7889, 552.3371, 346.9845, 563.0969],
}


def union_rect(rows: list[dict[str, object]]) -> fitz.Rect:
    rect = fitz.Rect(rows[0]["bbox_pdf_points"])
    for row in rows[1:]:
        rect.include_rect(fitz.Rect(row["bbox_pdf_points"]))
    return rect


def crop_box(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return tuple(round(value * SCALE) for value in (
        rect.x0 - FIGURE_RECT.x0,
        rect.y0 - FIGURE_RECT.y0,
        rect.x1 - FIGURE_RECT.x0,
        rect.y1 - FIGURE_RECT.y0,
    ))


def main() -> None:
    spans = json.loads((ROOT / "05_raw_text_spans.json").read_text(encoding="utf-8"))
    span_by_id = {row["raw_span_id"]: row for row in spans}
    image = Image.open(ROOT / "03_figure_crop_native_300dpi.png").convert("RGB")
    gray_image = image.convert("L")
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)

    measurements: list[dict[str, object]] = []
    for element_id, span_ids in TEXT_GROUPS.items():
        rows = [span_by_id[span_id] for span_id in span_ids]
        rect = union_rect(rows)
        x0, y0, x1, y1 = crop_box(rect)
        tile = gray_image.crop((max(0, x0), max(0, y0), min(gray_image.width, x1), min(gray_image.height, y1)))
        pixels = tile.load()
        foreground = [
            (x, y)
            for y in range(tile.height)
            for x in range(tile.width)
            if pixels[x, y] <= 210
        ]
        if foreground:
            xs = [point[0] for point in foreground]
            ys = [point[1] for point in foreground]
            ink_height = max(ys) - min(ys) + 1
            ink_width = max(xs) - min(xs) + 1
        else:
            ink_height = 0
            ink_width = 0
        measurements.append({
            "ELEMENT_ID": element_id,
            "RAW_SPAN_IDS": "+".join(span_ids),
            "TEXT": "".join(str(row["text"]) for row in rows),
            "BBOX_X0_PX": x0,
            "BBOX_Y0_PX": y0,
            "BBOX_X1_PX": x1,
            "BBOX_Y1_PX": y1,
            "BBOX_HEIGHT_PX": y1 - y0,
            "INK_HEIGHT_PX_THRESHOLD_210": ink_height,
            "INK_WIDTH_PX_THRESHOLD_210": ink_width,
            "PDF_SPAN_SIZE_PT_MIN": min(float(row["size_pdf_points"]) for row in rows),
            "PDF_SPAN_SIZE_PT_MAX": max(float(row["size_pdf_points"]) for row in rows),
        })
        draw.rectangle((x0, y0, x1, y1), outline=(220, 0, 0), width=3)
        draw.text((x0 + 3, max(0, y0 - 14)), element_id, fill=(220, 0, 0))

    with (ROOT / "07_raw_text_measurements.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(measurements[0]))
        writer.writeheader()
        writer.writerows(measurements)

    vector_rows = []
    for object_id, values in GRAPHICS.items():
        rect = fitz.Rect(values)
        x0, y0, x1, y1 = crop_box(rect)
        color = (0, 90, 220) if object_id.startswith("G") else (160, 80, 0)
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        draw.text((x0 + 3, max(0, y0 - 14)), object_id, fill=color)
        vector_rows.append({
            "OBJECT_ID": object_id,
            "BBOX_PDF_POINTS": values,
            "BBOX_CROP_PIXELS": [x0, y0, x1, y1],
        })
    (ROOT / "07_raw_graphic_geometry.json").write_text(
        json.dumps(vector_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    overlay.save(ROOT / "07_semantic_object_overlay_native_300dpi.png")


if __name__ == "__main__":
    main()
