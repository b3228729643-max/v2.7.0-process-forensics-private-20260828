from __future__ import annotations

import csv
import hashlib
import itertools
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa1_r113_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_exponential_family_moments.tex")
PAGE_NUMBER = 713
SCALE = 300.0 / 72.0
FIG_RECT = (70.0, 60.0, 520.0, 222.0)
SUBJECT_RECT = (70.0, 60.0, 520.0, 257.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pdf_to_subject_px(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    sx0, sy0, _, _ = SUBJECT_RECT
    return tuple(round(v) for v in ((rect[0] - sx0) * SCALE, (rect[1] - sy0) * SCALE,
                                     (rect[2] - sx0) * SCALE, (rect[3] - sy0) * SCALE))


def pdf_to_figure_px(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    fx0, fy0, _, _ = FIG_RECT
    return tuple(round(v) for v in ((rect[0] - fx0) * SCALE, (rect[1] - fy0) * SCALE,
                                     (rect[2] - fx0) * SCALE, (rect[3] - fy0) * SCALE))


OBJECTS = [
    ("O01", "left_title", "TEXT", "LEFT", (104.0, 65.5, 254.0, 82.5)),
    ("O02", "density_formula", "FORMULA", "LEFT", (92.5, 91.5, 266.0, 107.5)),
    ("O03", "brace_and_explanatory_text", "ANNOTATION_GEOMETRY", "LEFT", (74.0, 106.0, 283.0, 129.0)),
    ("O04", "base_measure_card", "NODE", "LEFT", (73.5, 137.0, 174.2, 164.6)),
    ("O05", "natural_parameter_card", "NODE", "LEFT", (184.0, 136.0, 284.8, 165.5)),
    ("O06", "sufficient_statistic_card", "NODE", "LEFT", (128.8, 175.5, 229.5, 205.0)),
    ("O07", "panel_divider", "PANEL_BORDER", "GUTTER", (304.3, 67.0, 306.2, 218.3)),
    ("O08", "right_title", "TEXT", "RIGHT", (364.0, 65.5, 499.0, 82.5)),
    ("O09", "log_partition_formula", "FORMULA", "RIGHT", (361.8, 91.5, 501.0, 106.7)),
    ("O10", "downward_implication_glyph", "GLYPH", "RIGHT", (424.5, 106.5, 438.4, 124.2)),
    ("O11", "partial_derivative_fraction", "FORMULA", "RIGHT", (421.8, 124.3, 440.5, 148.5)),
    ("O12", "expected_log_result_card", "NODE", "RIGHT", (358.3, 147.2, 504.5, 180.0)),
    ("O13", "jensen_warning_card", "NODE", "RIGHT", (352.6, 190.6, 510.2, 220.5)),
    ("O14", "figure_caption", "CAPTION", "PAGE", (75.0, 222.0, 513.5, 254.0)),
]


TEXTS = [
    ("T01", "left_title", "TITLE", "LEFT", 13, 10.2, (105.62, 66.93, 252.63, 81.65), "CJK_LATIN"),
    ("T02", "density_formula", "FORMULA", "LEFT", 14, 9.2, (94.15, 93.69, 264.09, 106.43), "MATH_MIXED"),
    ("T03", "base_measure_label", "NODE_LABEL", "LEFT", 16, 9.2, (97.77, 140.64, 149.93, 149.80), "LATIN_LOWER"),
    ("T04", "base_measure_formula", "NODE_FORMULA", "LEFT", 16, 9.2, (91.19, 151.60, 156.51, 162.03), "MATH_MIXED"),
    ("T05", "natural_parameter_label", "NODE_LABEL", "LEFT", 17, 9.2, (216.07, 141.00, 252.73, 150.81), "CJK"),
    ("T06", "natural_parameter_formula", "NODE_FORMULA", "LEFT", 17, 9.2, (209.70, 152.30, 259.10, 162.74), "MATH_MIXED"),
    ("T07", "sufficient_statistic_label", "NODE_LABEL", "LEFT", 18, 9.2, (156.21, 180.37, 202.04, 190.19), "CJK"),
    ("T08", "sufficient_statistic_formula", "NODE_FORMULA", "LEFT", 18, 9.2, (149.20, 191.68, 208.68, 202.12), "MATH_MIXED"),
    ("T09", "brace_explanation", "ANNOTATION", "LEFT", 20, 8.5, (114.90, 118.36, 241.92, 127.42), "CJK"),
    ("T10", "right_title", "TITLE", "RIGHT", 23, 10.2, (365.35, 66.93, 497.46, 81.65), "CJK"),
    ("T11", "log_partition_formula", "FORMULA", "RIGHT", 24, 9.2, (363.40, 92.98, 499.41, 105.72), "MATH_MIXED"),
    ("T12", "downward_implication_glyph", "GLYPH", "RIGHT", 25, 16.0, (425.67, 107.38, 437.14, 123.32), "MATH_SYMBOL"),
    ("T13", "partial_derivative_fraction", "FORMULA", "RIGHT", 26, 9.2, (422.93, 125.21, 439.51, 147.58), "MATH_MIXED"),
    ("T14", "expected_log_identity", "NODE_FORMULA", "RIGHT", 28, 9.2, (374.96, 159.30, 487.86, 169.74), "MATH_MIXED"),
    ("T15", "jensen_inequality", "NODE_FORMULA", "RIGHT", 30, 9.2, (386.17, 201.26, 476.64, 211.69), "MATH_MIXED"),
    ("T16", "caption", "CAPTION", "PAGE", 33, 10.0, (75.0, 222.0, 513.5, 253.0), "CJK_MATH_MIXED"),
]


def local_ink_metrics(image: Image.Image, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int, int]:
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - 2)
    y0 = max(0, y0 - 2)
    x1 = min(image.width, x1 + 2)
    y1 = min(image.height, y1 + 2)
    crop = image.crop((x0, y0, x1, y1)).convert("RGB")
    # Median of the four corners gives the local page/card background.
    corners = [crop.getpixel((1, 1)), crop.getpixel((crop.width - 2, 1)),
               crop.getpixel((1, crop.height - 2)), crop.getpixel((crop.width - 2, crop.height - 2))]
    bg = tuple(sorted(c[i] for c in corners)[len(corners) // 2] for i in range(3))
    pts = []
    for yy in range(crop.height):
        for xx in range(crop.width):
            px = crop.getpixel((xx, yy))
            if max(abs(px[i] - bg[i]) for i in range(3)) >= 20:
                pts.append((xx, yy))
    if not pts:
        return 0, 0, 0, 0, 0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs) + x0, min(ys) + y0, max(xs) + x0 + 1, max(ys) + y0 + 1, max(ys) - min(ys) + 1


def draw_overlay(base: Image.Image, rows, label_color, path: Path, arrows=None) -> None:
    out = base.copy().convert("RGB")
    draw = ImageDraw.Draw(out)
    font = ImageFont.load_default()
    for row in rows:
        oid, name, category, panel, rect = row
        box = pdf_to_subject_px(rect)
        draw.rectangle(box, outline=label_color.get(panel, (180, 0, 180)), width=3)
        draw.rectangle((box[0], max(0, box[1] - 14), box[0] + 35, box[1]), fill=label_color.get(panel, (180, 0, 180)))
        draw.text((box[0] + 2, max(0, box[1] - 13)), oid, fill=(255, 255, 255), font=font)
    if arrows:
        centers = {oid: ((pdf_to_subject_px(rect)[0] + pdf_to_subject_px(rect)[2]) // 2,
                         (pdf_to_subject_px(rect)[1] + pdf_to_subject_px(rect)[3]) // 2)
                   for oid, _, _, _, rect in rows}
        for a, b, color in arrows:
            x0, y0 = centers[a]
            x1, y1 = centers[b]
            draw.line((x0, y0, x1, y1), fill=color, width=4)
            ang = math.atan2(y1 - y0, x1 - x0)
            length = 14
            for delta in (2.55, -2.55):
                draw.line((x1, y1, x1 + length * math.cos(ang + delta), y1 + length * math.sin(ang + delta)), fill=color, width=4)
    out.save(path)


def main() -> None:
    ROOT.mkdir(parents=False, exist_ok=True)
    document = fitz.open(PDF)
    page = document[PAGE_NUMBER - 1]
    matrix = fitz.Matrix(SCALE, SCALE)
    subject_pix = page.get_pixmap(matrix=matrix, clip=fitz.Rect(*SUBJECT_RECT), alpha=False)
    subject_path = ROOT / "subject_native_300dpi.png"
    subject_pix.save(subject_path)
    figure_pix = page.get_pixmap(matrix=matrix, clip=fitz.Rect(*FIG_RECT), alpha=False)
    figure_pix.save(ROOT / "standalone_300dpi.png")

    full = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
    fig_box_page = tuple(round(v * SCALE) for v in FIG_RECT)
    full.crop(fig_box_page).save(ROOT / "figure_crop_300dpi.png")
    subject = Image.open(subject_path).convert("RGB")
    ImageOps.grayscale(subject).save(ROOT / "grayscale_300dpi.png")

    full200 = Image.open(ROOT / "full_page_200dpi.png").convert("RGB")
    page_integration_box = (140, 115, 1515, 1030)
    full200.crop(page_integration_box).save(ROOT / "page_integration_200dpi.png")

    colors = {"LEFT": (0, 100, 220), "RIGHT": (210, 40, 40), "GUTTER": (130, 40, 170), "PAGE": (0, 145, 90)}
    draw_overlay(subject, OBJECTS, colors, ROOT / "object_overlay_300dpi.png")
    semantic_colors = {"LEFT": (0, 110, 220), "RIGHT": (220, 70, 0), "GUTTER": (145, 70, 175), "PAGE": (20, 145, 80)}
    draw_overlay(subject, OBJECTS, semantic_colors, ROOT / "semantic_overlay_300dpi.png")

    text_rows = [(tid, name, role, panel, rect) for tid, name, role, panel, _, _, rect, _ in TEXTS]
    draw_overlay(subject, text_rows, colors, ROOT / "text_overlay_300dpi.png")
    order = [
        ("O01", "O02", (0, 90, 220)), ("O02", "O03", (0, 90, 220)),
        ("O03", "O04", (0, 90, 220)), ("O03", "O05", (0, 90, 220)),
        ("O04", "O06", (0, 90, 220)), ("O05", "O06", (0, 90, 220)),
        ("O06", "O08", (120, 40, 170)), ("O08", "O09", (210, 40, 40)),
        ("O09", "O10", (210, 40, 40)), ("O10", "O11", (210, 40, 40)),
        ("O11", "O12", (210, 40, 40)), ("O12", "O13", (210, 40, 40)),
        ("O13", "O14", (0, 130, 80)),
    ]
    draw_overlay(subject, OBJECTS, colors, ROOT / "reading_order_overlay_300dpi.png", arrows=order)

    gray = ImageOps.grayscale(subject)
    stat = ImageStat.Stat(gray)
    threshold = min(245, int(stat.mean[0] - 8))
    mask = gray.point(lambda p: 255 if p < threshold else 0)
    mask.save(ROOT / "foreground_mask_300dpi.png")

    rois = [
        ("01", (72.0, 89.0, 287.0, 132.0)),
        ("02", (71.0, 133.0, 288.0, 208.0)),
        ("03", (349.0, 86.0, 515.0, 184.0)),
        ("04", (349.0, 186.0, 515.0, 223.0)),
    ]
    for rid, rect in rois:
        box = pdf_to_subject_px(rect)
        roi = subject.crop(box)
        roi.save(ROOT / f"risk_roi_{rid}_native1x_300dpi.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(ROOT / f"risk_roi_{rid}_nn8x.png")

    with (ROOT / "machine_object_bboxes.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["object_id", "name", "category", "panel", "pdf_x0", "pdf_y0", "pdf_x1", "pdf_y1", "px_x0", "px_y0", "px_x1", "px_y1"])
        for oid, name, category, panel, rect in OBJECTS:
            writer.writerow([oid, name, category, panel, *rect, *pdf_to_subject_px(rect)])

    object_by_id = {row[0]: row for row in OBJECTS}
    with (ROOT / "machine_unordered_pairs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["pair_id", "object_a", "object_b", "category_a", "category_b", "bbox_overlap_area_px", "bbox_gap_px"])
        for index, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
            ba = pdf_to_subject_px(a[4])
            bb = pdf_to_subject_px(b[4])
            ox = max(0, min(ba[2], bb[2]) - max(ba[0], bb[0]))
            oy = max(0, min(ba[3], bb[3]) - max(ba[1], bb[1]))
            overlap = ox * oy
            dx = max(0, max(ba[0], bb[0]) - min(ba[2], bb[2]))
            dy = max(0, max(ba[1], bb[1]) - min(ba[3], bb[3]))
            gap = round(math.hypot(dx, dy), 3)
            writer.writerow([f"P{index:03d}", a[0], b[0], a[2], b[2], overlap, gap])

    with (ROOT / "machine_text_measurements.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["text_id", "name", "role", "panel", "source_line", "declared_pt", "graphics_scale", "effective_pt", "script_class", "bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1", "ink_x0", "ink_y0", "ink_x1", "ink_y1", "h_ink_px"])
        for tid, name, role, panel, line, declared, rect, script in TEXTS:
            bbox = pdf_to_subject_px(rect)
            ink = local_ink_metrics(subject, bbox)
            writer.writerow([tid, name, role, panel, line, declared, 1.0, declared, script, *bbox, *ink[:4], ink[4]])

    with (ROOT / "identity_verification.txt").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(f"UID=FIG-P665-01\n")
        stream.write(f"PDF_PATH={PDF}\n")
        stream.write(f"PDF_BYTES={PDF.stat().st_size}\n")
        stream.write(f"PDF_SHA256={sha256(PDF)}\n")
        stream.write(f"PDF_PAGES={len(document)}\n")
        stream.write(f"LOCATED_PHYSICAL_PAGE={PAGE_NUMBER}\n")
        stream.write(f"SOURCE_PATH={TEX}\n")
        stream.write(f"SOURCE_BYTES={TEX.stat().st_size}\n")
        stream.write(f"SOURCE_SHA256={sha256(TEX)}\n")
        stream.write(f"OBJECT_DENOMINATOR={len(OBJECTS)}\n")
        stream.write(f"UNORDERED_PAIR_DENOMINATOR={len(OBJECTS) * (len(OBJECTS) - 1) // 2}\n")

    extracted = page.get_text("text")
    with (ROOT / "official_page_text_excerpt.txt").open("w", encoding="utf-8", newline="\n") as stream:
        start = extracted.find("左：Dirichlet")
        end = extracted.find("后验推导保留归一化常数")
        stream.write(extracted[start:end if end > start else None])

    with (ROOT / "machine_summary.txt").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(f"PAGE_NUMBER={PAGE_NUMBER}\n")
        stream.write(f"SUBJECT_PIXELS={subject.width}x{subject.height}\n")
        stream.write(f"OBJECT_ROWS={len(OBJECTS)}\n")
        stream.write(f"PAIR_ROWS={len(OBJECTS) * (len(OBJECTS) - 1) // 2}\n")
        stream.write(f"TEXT_ROWS={len(TEXTS)}\n")
        stream.write(f"MASK_THRESHOLD={threshold}\n")


if __name__ == "__main__":
    main()
