from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R2_SA1_FRESH_ISOLATED_R114_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C05\fig_v1_c05_gaussian.tex")
PAGE_INDEX = 78
FIGURE_RECT_PT = (80.0, 420.0, 515.0, 615.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()


def px_box(box_pt, sx, sy):
    x0, y0, x1, y1 = box_pt
    return tuple(int(round(v)) for v in (x0 * sx, y0 * sy, x1 * sx, y1 * sy))


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return (dx * dx + dy * dy) ** 0.5


def bbox_intersection_area(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def ink_metrics(gray: Image.Image, box, threshold=205):
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0 - 2), max(0, y0 - 2)
    x1, y1 = min(gray.width, x1 + 2), min(gray.height, y1 + 2)
    crop = gray.crop((x0, y0, x1, y1))
    pix = crop.load()
    pts = [(x, y) for y in range(crop.height) for x in range(crop.width) if pix[x, y] <= threshold]
    if not pts:
        return 0, 0, 0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, len(pts)


def main():
    visual = ROOT / "visual"
    machine = ROOT / "machine"
    full = Image.open(visual / "full_page_native300dpi.png").convert("RGB")
    gray = full.convert("L")

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx = full.width / page.rect.width
    sy = full.height / page.rect.height
    crop_box = px_box(FIGURE_RECT_PT, sx, sy)
    crop = full.crop(crop_box)
    crop.save(visual / "figure_crop_native300dpi.png")
    crop.convert("L").save(visual / "figure_crop_grayscale_native300dpi.png")

    identity = {
        "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
        "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
    }
    (machine / "input_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")
    locator = {
        "page_count": len(doc),
        "physical_page": PAGE_INDEX + 1,
        "printed_page": 66,
        "caption": "图 5.1 方差增大使高斯密度变宽、峰值降低，但曲线下面积保持为1",
        "page_points": [page.rect.width, page.rect.height],
        "native300_pixels": [full.width, full.height],
        "scale_px_per_pdf_point": [sx, sy],
        "figure_rect_pdf_points": FIGURE_RECT_PT,
        "figure_crop_pixels_on_page": crop_box,
    }
    (machine / "page_locator.json").write_text(json.dumps(locator, ensure_ascii=False, indent=2), encoding="utf-8")

    spans = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                x0, y0, x1, y1 = span["bbox"]
                if FIGURE_RECT_PT[0] <= x1 and x0 <= FIGURE_RECT_PT[2] and FIGURE_RECT_PT[1] <= y1 and y0 <= FIGURE_RECT_PT[3]:
                    box = px_box(span["bbox"], sx, sy)
                    iw, ih, count = ink_metrics(gray, box)
                    spans.append({
                        "span_index": len(spans) + 1,
                        "text": span["text"],
                        "font": span["font"],
                        "pdf_size_pt": round(span["size"], 4),
                        "pdf_x0": round(x0, 4),
                        "pdf_y0": round(y0, 4),
                        "pdf_x1": round(x1, 4),
                        "pdf_y1": round(y1, 4),
                        "px_x0": box[0], "px_y0": box[1], "px_x1": box[2], "px_y1": box[3],
                        "ink_width_px_threshold205": iw,
                        "ink_height_px_threshold205": ih,
                        "ink_pixel_count_threshold205": count,
                    })
    with (machine / "pdf_text_spans_and_raster_ink.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(spans[0]))
        writer.writeheader()
        writer.writerows(spans)

    # Source-construct-level visible-object denominator geometry.  Manual review fields
    # are deliberately absent and are maintained only in manual/ ledgers.
    text_objects = [
        ("T01", "TEXT", "x-axis title x", (303.05, 578.45, 308.62, 588.41), "23"),
        ("T02", "TEXT", "y-axis title 密度", (94.93, 486.10, 105.60, 506.02), "23"),
        ("T03", "TEXT", "x tick −4", (144.10, 566.63, 156.48, 575.89), "26"),
        ("T04", "TEXT", "x tick 0", (303.20, 566.62, 308.57, 575.89), "26"),
        ("T05", "TEXT", "x tick 4", (458.86, 566.63, 464.09, 575.89), "26"),
        ("T06", "TEXT", "y tick 0", (119.51, 540.31, 124.88, 549.57), "26"),
        ("T07", "TEXT", "y tick 0.2", (111.94, 487.42, 124.88, 496.69), "26"),
        ("T08", "TEXT", "y tick 0.4", (111.57, 434.52, 124.88, 443.79), "26"),
        ("T09", "FORMULA_TEXT", "N(0,1); peak label", (344.13, 451.98, 433.02, 463.27), "44-45"),
        ("T10", "FORMULA_TEXT", "N(0,2^2); peak label", (386.92, 496.94, 492.34, 508.23), "46-47"),
        ("T11", "FORMULA_TEXT", "area equals 1 label", (265.58, 553.87, 346.18, 563.68), "51-53"),
        ("T12", "TEXT", "figure number 图5.1", (141.30, 592.58, 166.22, 607.00), "56"),
        ("T13", "TEXT", "caption conclusion", (176.18, 596.16, 442.63, 606.83), "56"),
    ]
    graphics = [
        ("G01", "AXIS", "x axis and arrowhead", (130.84, 559.39, 480.93, 563.65), "21-27"),
        ("G02", "AXIS", "y axis and arrowhead", (128.72, 430.60, 132.97, 561.52), "21-27"),
        ("G03", "TICK_MARK", "x tick at −4", (150.29, 559.39, 150.30, 563.65), "26"),
        ("G04", "TICK_MARK", "x tick at 0", (305.88, 559.39, 305.90, 563.65), "26"),
        ("G05", "TICK_MARK", "x tick at 4", (461.48, 559.39, 461.49, 563.65), "26"),
        ("G06", "TICK_MARK", "y tick at 0", (128.72, 544.32, 132.97, 544.34), "26"),
        ("G07", "TICK_MARK", "y tick at 0.2", (128.72, 491.42, 132.97, 491.44), "26"),
        ("G08", "TICK_MARK", "y tick at 0.4", (128.72, 438.53, 132.97, 438.54), "26"),
        ("G09", "DATA_CURVE", "narrow N(0,1) solid curve", (130.84, 438.82, 480.93, 544.33), "37-38"),
        ("G10", "DATA_FILL", "narrow N(0,1) fill", (130.84, 438.82, 480.93, 544.33), "33-36"),
        ("G11", "DATA_CURVE", "wide N(0,2^2) dashed curve", (130.84, 491.57, 480.93, 540.13), "39-41"),
        ("G12", "DATA_FILL", "wide N(0,2^2) fill", (130.84, 491.57, 480.93, 544.33), "29-32"),
        ("G13", "REFERENCE_LINE", "vertical x=0 reference", (305.88, 437.21, 305.90, 544.33), "42-43"),
        ("G14", "BRACE", "area brace", (169.74, 549.09, 442.03, 552.08), "48-50"),
        ("G15", "LABEL_BACKGROUND", "narrow-label white background", (343.04, 450.16, 434.12, 463.46), "44-45"),
        ("G16", "LABEL_BACKGROUND", "wide-label white background", (385.83, 495.12, 493.44, 508.42), "46-47"),
        ("G17", "LABEL_BACKGROUND", "area-label white background", (264.79, 552.34, 346.98, 563.10), "51-53"),
    ]
    objects = []
    for oid, category, label, box_pt, source_lines in text_objects + graphics:
        box = px_box(box_pt, sx, sy)
        objects.append({
            "object_id": oid, "category": category, "label": label,
            "source_lines": source_lines,
            "pdf_x0": box_pt[0], "pdf_y0": box_pt[1], "pdf_x1": box_pt[2], "pdf_y1": box_pt[3],
            "px_x0": box[0], "px_y0": box[1], "px_x1": box[2], "px_y1": box[3],
        })
    with (machine / "visible_object_geometry.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(objects[0]))
        writer.writeheader()
        writer.writerows(objects)

    pairs = []
    for seq, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        ba = (a["px_x0"], a["px_y0"], a["px_x1"], a["px_y1"])
        bb = (b["px_x0"], b["px_y0"], b["px_x1"], b["px_y1"])
        pairs.append({
            "pair_id": f"P{seq:03d}", "object_a": a["object_id"], "object_b": b["object_id"],
            "bbox_gap_px": round(bbox_gap(ba, bb), 3),
            "bbox_intersection_area_px": bbox_intersection_area(ba, bb),
        })
    with (machine / "all_unordered_pairs_geometry.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)

    # Two overlays: text-only and complete denominator.  They are mechanical
    # locators, not review decisions.
    colors = {"TEXT": "#d7191c", "FORMULA_TEXT": "#d7191c", "DATA_CURVE": "#0066ff",
              "DATA_FILL": "#55a868", "AXIS": "#6a3d9a", "TICK_MARK": "#6a3d9a",
              "REFERENCE_LINE": "#ff7f00", "BRACE": "#ff7f00", "LABEL_BACKGROUND": "#00a6a6"}
    for filename, selected in (("text_measurement_overlay_native300dpi.png", objects[:13]),
                               ("visible_object_denominator_overlay_native300dpi.png", objects)):
        overlay = full.copy()
        draw = ImageDraw.Draw(overlay)
        for obj in selected:
            box = (obj["px_x0"], obj["px_y0"], obj["px_x1"], obj["px_y1"])
            color = colors.get(obj["category"], "#000000")
            draw.rectangle(box, outline=color, width=3)
            draw.text((box[0] + 2, max(0, box[1] - 14)), obj["object_id"], fill=color)
        overlay.crop(crop_box).save(visual / filename)

    # Native 1x critical regions and exact nearest-neighbour 8x magnifications.
    rois_pt = {
        "narrow_label": (338.0, 432.0, 440.0, 469.0),
        "wide_label": (380.0, 486.0, 500.0, 515.0),
        "area_brace_label": (160.0, 545.0, 450.0, 568.0),
        "caption": (136.0, 588.0, 448.0, 611.0),
        "axis_ticks_titles": (88.0, 426.0, 486.0, 591.0),
        "area_center_tick": (292.0, 548.0, 320.0, 568.0),
    }
    roi_records = []
    for name, rect_pt in rois_pt.items():
        box = px_box(rect_pt, sx, sy)
        im = full.crop(box)
        one = visual / f"critical_{name}_native1x.png"
        eight = visual / f"critical_{name}_nearest8x.png"
        im.save(one)
        im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST).save(eight)
        roi_records.append({"roi_id": name, "pdf_rect_pt": rect_pt, "page_pixel_rect": box,
                            "native1x_pixels": [im.width, im.height], "nearest8x_pixels": [im.width * 8, im.height * 8]})
    (machine / "critical_roi_geometry.json").write_text(json.dumps(roi_records, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "object_count": len(objects),
        "text_object_count": len(text_objects),
        "graphic_object_count": len(graphics),
        "unordered_pair_count": len(pairs),
        "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "pdf_text_span_count_in_figure_rect": len(spans),
        "figure_crop_native300_pixels": [crop.width, crop.height],
    }
    (machine / "mechanical_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
