from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parents[1]
PAGE_PNG = ROOT / "02_page" / "page_300dpi.png"
PAGE_WIDTH_PT = 595.276
PAGE_HEIGHT_PT = 841.89
FIGURE_BOX_PT = (95.0, 62.0, 490.0, 202.0)


TEXT_OBJECTS = [
    ("TXT-U-YTICK-100", "U", "TICK_TEXT", "1", 20, 8.8, (136.950, 70.830, 141.410, 79.600)),
    ("TXT-U-P4", "U", "FORMULA_LABEL", "p_4", 51, 9.2, (442.160, 76.270, 451.560, 86.700)),
    ("TXT-U-YTICK-080", "U", "TICK_TEXT", "0.8", 20, 8.8, (129.150, 80.600, 141.410, 89.370)),
    ("TXT-U-NOTE-RC", "U", "ANNOTATION", "右连续：实心点取跳后值", 59, 9.2, (158.885, 82.690, 259.707, 92.507)),
    ("TXT-U-YLABEL-FX", "U", "AXIS_LABEL", "F_X(t)", 33, 9.4, (107.840, 87.190, 118.500, 108.540)),
    ("TXT-U-P3", "U", "FORMULA_LABEL", "p_3", 55, 9.2, (359.640, 87.290, 368.790, 97.730)),
    ("TXT-U-YTICK-045", "U", "TICK_TEXT", "0.45", 20, 8.8, (124.410, 97.740, 141.410, 106.500)),
    ("TXT-U-P2", "U", "FORMULA_LABEL", "p_2", 53, 9.2, (278.730, 103.210, 287.870, 113.650)),
    ("TXT-U-P1", "U", "FORMULA_LABEL", "p_1", 51, 9.2, (199.440, 113.500, 208.590, 123.940)),
    ("TXT-U-YTICK-000", "U", "TICK_TEXT", "0", 20, 8.8, (136.320, 119.780, 141.410, 128.550)),
    ("TXT-L-YTICK-035", "L", "TICK_TEXT", "0.35", 68, 8.6, (126.590, 135.200, 141.410, 143.770)),
    ("TXT-L-NOTE-JUMP", "L", "ANNOTATION", "同一 t_i：跳高=p_i", 82, 9.2, (395.176, 137.110, 469.449, 147.894)),
    ("TXT-L-YLABEL-PX", "L", "AXIS_LABEL", "p_X(t)", 69, 9.4, (109.920, 141.090, 120.580, 163.400)),
    ("TXT-L-YTICK-030", "L", "TICK_TEXT", "0.3", 76, 8.6, (129.570, 144.360, 141.540, 152.930)),
    ("TXT-L-YTICK-015", "L", "TICK_TEXT", "0.15", 68, 8.6, (126.590, 153.420, 141.410, 161.990)),
    ("TXT-L-YTICK-000", "L", "TICK_TEXT", "0", 68, 8.6, (137.170, 167.100, 141.410, 175.670)),
    ("TXT-L-XTICK-1", "L", "TICK_TEXT", "1", 68, 8.6, (189.690, 176.080, 194.050, 184.640)),
    ("TXT-L-XTICK-2", "L", "TICK_TEXT", "2", 68, 8.6, (270.530, 176.110, 275.020, 184.680)),
    ("TXT-L-XTICK-3", "L", "TICK_TEXT", "3", 68, 8.6, (351.440, 176.110, 355.930, 184.680)),
    ("TXT-L-XTICK-4", "L", "TICK_TEXT", "4", 68, 8.6, (432.180, 176.100, 437.010, 184.670)),
    ("TXT-L-XLABEL-T", "L", "AXIS_LABEL", "t", 69, 9.4, (311.580, 188.640, 314.750, 198.000)),
]


GRAPHIC_OBJECTS = [
    ("GFX-U-AXIS-X", "U", "LINE_ARROW", 28, "upper horizontal axis including arrowhead"),
    ("GFX-U-AXIS-Y", "U", "LINE_ARROW", 28, "upper vertical axis including arrowhead"),
    ("GFX-U-YTICK-000", "U", "TICK_MARK", 33, "upper y tick at 0"),
    ("GFX-U-YTICK-045", "U", "TICK_MARK", 33, "upper y tick at 0.45"),
    ("GFX-U-YTICK-080", "U", "TICK_MARK", 33, "upper y tick at 0.8"),
    ("GFX-U-YTICK-100", "U", "TICK_MARK", 33, "upper y tick at 1"),
    ("GFX-U-CDF-CURVE", "U", "DATA_CURVE", 37, "right-continuous CDF step curve"),
    ("GFX-U-CLOSED-1", "U", "MARKER", 39, "closed CDF marker at t=1"),
    ("GFX-U-CLOSED-2", "U", "MARKER", 39, "closed CDF marker at t=2"),
    ("GFX-U-CLOSED-3", "U", "MARKER", 39, "closed CDF marker at t=3"),
    ("GFX-U-CLOSED-4", "U", "MARKER", 39, "closed CDF marker at t=4"),
    ("GFX-U-OPEN-1", "U", "MARKER", 42, "open CDF marker at t=1"),
    ("GFX-U-OPEN-2", "U", "MARKER", 42, "open CDF marker at t=2"),
    ("GFX-U-OPEN-3", "U", "MARKER", 42, "open CDF marker at t=3"),
    ("GFX-U-OPEN-4", "U", "MARKER", 42, "open CDF marker at t=4"),
    ("GFX-U-GUIDE-Y100", "U", "GUIDE_LINE", 45, "horizontal reference guide at F=1"),
    ("GFX-U-GUIDE-X1", "U", "GUIDE_LINE", 47, "vertical guide at t=1"),
    ("GFX-U-GUIDE-X2", "U", "GUIDE_LINE", 48, "vertical guide at t=2"),
    ("GFX-U-GUIDE-X3", "U", "GUIDE_LINE", 49, "vertical guide at t=3"),
    ("GFX-U-GUIDE-X4", "U", "GUIDE_LINE", 50, "vertical guide at t=4"),
    ("GFX-L-AXIS-X", "L", "LINE_ARROW", 63, "lower horizontal axis including arrowhead"),
    ("GFX-L-AXIS-Y", "L", "LINE_ARROW", 63, "lower vertical axis including arrowhead"),
    ("GFX-L-XTICK-1", "L", "TICK_MARK", 68, "lower x tick at 1"),
    ("GFX-L-XTICK-2", "L", "TICK_MARK", 68, "lower x tick at 2"),
    ("GFX-L-XTICK-3", "L", "TICK_MARK", 68, "lower x tick at 3"),
    ("GFX-L-XTICK-4", "L", "TICK_MARK", 68, "lower x tick at 4"),
    ("GFX-L-YTICK-000", "L", "TICK_MARK", 68, "lower y tick at 0"),
    ("GFX-L-YTICK-015", "L", "TICK_MARK", 68, "lower y tick at 0.15"),
    ("GFX-L-YTICK-030", "L", "TICK_MARK", 68, "lower y tick at 0.30"),
    ("GFX-L-YTICK-035", "L", "TICK_MARK", 68, "lower y tick at 0.35"),
    ("GFX-L-PMF-STEM-1", "L", "DATA_CURVE", 73, "PMF stem at t=1"),
    ("GFX-L-PMF-STEM-2", "L", "DATA_CURVE", 73, "PMF stem at t=2"),
    ("GFX-L-PMF-STEM-3", "L", "DATA_CURVE", 73, "PMF stem at t=3"),
    ("GFX-L-PMF-STEM-4", "L", "DATA_CURVE", 73, "PMF stem at t=4"),
    ("GFX-L-PMF-MARK-1", "L", "MARKER", 73, "PMF marker at t=1"),
    ("GFX-L-PMF-MARK-2", "L", "MARKER", 73, "PMF marker at t=2"),
    ("GFX-L-PMF-MARK-3", "L", "MARKER", 73, "PMF marker at t=3"),
    ("GFX-L-PMF-MARK-4", "L", "MARKER", 73, "PMF marker at t=4"),
    ("GFX-L-GUIDE-X1", "L", "GUIDE_LINE", 78, "lower vertical guide at t=1"),
    ("GFX-L-GUIDE-X2", "L", "GUIDE_LINE", 79, "lower vertical guide at t=2"),
    ("GFX-L-GUIDE-X3", "L", "GUIDE_LINE", 80, "lower vertical guide at t=3"),
    ("GFX-L-GUIDE-X4", "L", "GUIDE_LINE", 81, "lower vertical guide at t=4"),
]


def pt_box_to_px(box: tuple[float, float, float, float], image: Image.Image) -> tuple[int, int, int, int]:
    sx = image.width / PAGE_WIDTH_PT
    sy = image.height / PAGE_HEIGHT_PT
    x0, y0, x1, y1 = box
    return (round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy))


def ink_metrics(gray: Image.Image, box_px: tuple[int, int, int, int]) -> tuple[int, int, int]:
    x0, y0, x1, y1 = box_px
    region = gray.crop((x0, y0, x1 + 1, y1 + 1))
    coords = []
    for y in range(region.height):
        for x in range(region.width):
            if region.getpixel((x, y)) <= 235:
                coords.append((x, y))
    if not coords:
        return 0, 0, 0
    ys = [p[1] for p in coords]
    return max(ys) - min(ys) + 1, len(set(ys)), len(coords)


def save_crops(page: Image.Image) -> dict[str, tuple[int, int, int, int]]:
    figure_box_px = pt_box_to_px(FIGURE_BOX_PT, page)
    figure = page.crop(figure_box_px)
    figure.save(ROOT / "03_figure" / "figure_native1x_300dpi.png")
    figure.resize((figure.width * 8, figure.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "03_figure" / "figure_nearest8x.png"
    )
    figure.convert("L").save(ROOT / "03_figure" / "figure_grayscale_300dpi.png")

    roi_boxes_pt = {
        "roi01_upper_note_axis": (101.0, 65.0, 279.0, 132.0),
        "roi02_jump_markers_labels": (185.0, 65.0, 478.0, 132.0),
        "roi03_lower_pmf_annotation": (101.0, 130.0, 484.0, 202.0),
    }
    roi_boxes_px: dict[str, tuple[int, int, int, int]] = {}
    rois: list[tuple[str, Image.Image]] = []
    for name, box_pt in roi_boxes_pt.items():
        box_px = pt_box_to_px(box_pt, page)
        roi_boxes_px[name] = box_px
        roi = page.crop(box_px)
        roi.save(ROOT / "04_critical" / f"{name}_native1x.png")
        rois.append((name, roi))

    pad = 18
    label_h = 20
    sheet_w = max(im.width for _, im in rois) + 2 * pad
    sheet_h = sum(im.height + label_h + pad for _, im in rois) + pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    y = pad
    for name, roi in rois:
        draw.text((pad, y), name, fill="black")
        y += label_h
        sheet.paste(roi, (pad, y))
        y += roi.height + pad
    sheet.save(ROOT / "04_critical" / "critical_contact_sheet_native1x.png")
    return roi_boxes_px


def write_text_measurements(page: Image.Image) -> None:
    gray = page.convert("L")
    gray_array = np.asarray(gray)
    foreground = gray_array <= 235
    out_path = ROOT / "01_locator" / "text_bbox_mechanical.csv"
    rows = []
    for object_id, panel, role, text, source_line, declared_pt, box_pt in TEXT_OBJECTS:
        box_px = pt_box_to_px(box_pt, page)
        h_span, occupied_rows, dark_pixels = ink_metrics(gray, box_px)
        x0, y0, x1, y1 = box_px
        radius = 160
        rx0 = max(0, x0 - radius)
        ry0 = max(0, y0 - radius)
        rx1 = min(page.width - 1, x1 + radius)
        ry1 = min(page.height - 1, y1 + radius)
        local_foreground = foreground[ry0 : ry1 + 1, rx0 : rx1 + 1]
        target = np.zeros_like(local_foreground)
        lx0, ly0, lx1, ly1 = x0 - rx0, y0 - ry0, x1 - rx0, y1 - ry0
        target[ly0 : ly1 + 1, lx0 : lx1 + 1] = local_foreground[ly0 : ly1 + 1, lx0 : lx1 + 1]
        other = local_foreground.copy()
        self_halo = 2
        hx0 = max(0, lx0 - self_halo)
        hy0 = max(0, ly0 - self_halo)
        hx1 = min(other.shape[1] - 1, lx1 + self_halo)
        hy1 = min(other.shape[0] - 1, ly1 + self_halo)
        other[hy0 : hy1 + 1, hx0 : hx1 + 1] = False
        distance_to_other = distance_transform_edt(~other)
        center_distance = float(distance_to_other[target].min()) if target.any() else 0.0
        edge_clearance = max(0.0, center_distance - 1.0 - self_halo)
        rows.append(
            {
                "OBJECT_ID": object_id,
                "PANEL": panel,
                "ROLE": role,
                "TEXT_SAMPLE": text,
                "SOURCE_LINE": source_line,
                "DECLARED_PT": declared_pt,
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": declared_pt,
                "BBOX_X0_PT": box_pt[0],
                "BBOX_Y0_PT": box_pt[1],
                "BBOX_X1_PT": box_pt[2],
                "BBOX_Y1_PT": box_pt[3],
                "BBOX_X0_PX": box_px[0],
                "BBOX_Y0_PX": box_px[1],
                "BBOX_X1_PX": box_px[2],
                "BBOX_Y1_PX": box_px[3],
                "INK_HEIGHT_SPAN_PX_AT_GRAY_LE_235": h_span,
                "OCCUPIED_INK_ROWS_PX": occupied_rows,
                "DARK_PIXEL_COUNT": dark_pixels,
                "NEAREST_EXTERNAL_FOREGROUND_CENTER_DISTANCE_PX": f"{center_distance:.3f}",
                "NEAREST_EXTERNAL_FOREGROUND_EDGE_CLEARANCE_PX": f"{edge_clearance:.3f}",
            }
        )
    with out_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_overlay(page: Image.Image) -> None:
    overlay = page.copy()
    draw = ImageDraw.Draw(overlay)
    for object_id, panel, role, text, source_line, declared_pt, box_pt in TEXT_OBJECTS:
        x0, y0, x1, y1 = pt_box_to_px(box_pt, page)
        draw.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), outline=(220, 0, 0), width=2)
        draw.text((x0, max(0, y0 - 12)), object_id, fill=(190, 0, 0))
    crop = overlay.crop(pt_box_to_px(FIGURE_BOX_PT, page))
    crop.save(ROOT / "03_figure" / "text_bbox_overlay_300dpi.png")


def write_denominator_and_pairs() -> tuple[int, int]:
    denominator_rows = []
    for object_id, panel, role, text, source_line, declared_pt, box_pt in TEXT_OBJECTS:
        denominator_rows.append(
            {
                "OBJECT_ID": object_id,
                "PANEL": panel,
                "OBJECT_KIND": "TEXT_OR_FORMULA",
                "ROLE": role,
                "SOURCE_LINE": source_line,
                "VISIBLE_CONTENT_OR_DESCRIPTION": text,
            }
        )
    for object_id, panel, role, source_line, description in GRAPHIC_OBJECTS:
        denominator_rows.append(
            {
                "OBJECT_ID": object_id,
                "PANEL": panel,
                "OBJECT_KIND": "GRAPHIC",
                "ROLE": role,
                "SOURCE_LINE": source_line,
                "VISIBLE_CONTENT_OR_DESCRIPTION": description,
            }
        )
    denominator_path = ROOT / "00_control" / "visible_object_denominator_mechanical.csv"
    with denominator_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(denominator_rows[0]))
        writer.writeheader()
        writer.writerows(denominator_rows)

    object_kind = {row["OBJECT_ID"]: row["OBJECT_KIND"] for row in denominator_rows}
    pair_rows = []
    for number, (left, right) in enumerate(
        itertools.combinations([row["OBJECT_ID"] for row in denominator_rows], 2), start=1
    ):
        pair_rows.append(
            {
                "PAIR_ID": f"PAIR-{number:04d}",
                "OBJECT_ID_A": left,
                "OBJECT_ID_B": right,
                "KIND_A": object_kind[left],
                "KIND_B": object_kind[right],
                "MECHANICAL_PAIR_CLASS": f"{object_kind[left]}__{object_kind[right]}",
            }
        )
    pair_path = ROOT / "00_control" / "all_unordered_pairs_mechanical.csv"
    with pair_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(pair_rows)
    return len(denominator_rows), len(pair_rows)


def main() -> None:
    page = Image.open(PAGE_PNG).convert("RGB")
    roi_boxes = save_crops(page)
    write_text_measurements(page)
    write_overlay(page)
    denominator_count, pair_count = write_denominator_and_pairs()
    summary = {
        "page_png_pixels": [page.width, page.height],
        "page_width_pt": PAGE_WIDTH_PT,
        "page_height_pt": PAGE_HEIGHT_PT,
        "figure_box_pt": list(FIGURE_BOX_PT),
        "figure_box_px": list(pt_box_to_px(FIGURE_BOX_PT, page)),
        "roi_boxes_px": {key: list(value) for key, value in roi_boxes.items()},
        "text_object_count": len(TEXT_OBJECTS),
        "graphic_object_count": len(GRAPHIC_OBJECTS),
        "visible_object_denominator": denominator_count,
        "all_unordered_pair_count": pair_count,
        "manual_review_fields_generated": False,
    }
    (ROOT / "00_control" / "mechanical_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
