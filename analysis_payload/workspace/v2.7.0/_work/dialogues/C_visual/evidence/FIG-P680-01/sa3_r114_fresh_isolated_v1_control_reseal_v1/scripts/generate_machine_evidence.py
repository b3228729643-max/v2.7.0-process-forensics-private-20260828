from __future__ import annotations

import csv
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from statistics import median

import pdfplumber
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


HANDOFF_ID = "C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-V1"
UID = "FIG-P680-01"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
FIG_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_dependency_graph.tex")
CHAPTER_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C06.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1")
MACHINE = ROOT / "machine"
PAGE_300 = MACHINE / "full_page_300dpi-729.png"
PAGE_200 = MACHINE / "full_page_200dpi-729.png"
PDF_PAGE_NUMBER = 729
SCALE = 300.0 / 72.0


# These are reader-visible text lines, not verdicts. Bboxes use PDF points
# in top-origin coordinates and were recovered from the official R114 PDF.
TEXT_ELEMENTS = [
    ("T01", "shared_line_1", "共享“文档–主题–单词”条件结构", 16, "node_text", 9.4, (240.831, 147.397, 390.669, 157.071)),
    ("T02", "shared_line_2", "两层混合、条件独立与词袋计数", 16, "node_text", 9.4, (250.196, 159.064, 381.304, 168.429)),
    ("T03", "row_model", "模型目标", 17, "row_label", 9.8, (107.035, 198.766, 146.089, 208.530)),
    ("T04", "full_line_1", "完整 Bayes LDA", 18, "node_text", 9.4, (195.670, 192.298, 260.082, 201.972)),
    ("T05", "full_line_2", "theta,varphi 均为随机变量", 18, "node_formula_text", 9.4, (191.387, 203.655, 264.365, 213.329)),
    ("T06", "point_line_1", "点参数 LDA 变体", 19, "node_text", 9.4, (368.679, 192.298, 438.570, 201.972)),
    ("T07", "point_line_2", "varphi 作为待估参数", 19, "node_formula_text", 9.4, (371.587, 203.655, 435.661, 213.329)),
    ("T08", "row_inference", "推断方法", 20, "row_label", 9.8, (107.035, 244.120, 146.089, 253.884)),
    ("T09", "gibbs_line_1", "折叠 Gibbs", 21, "node_text", 9.4, (205.967, 237.652, 249.786, 247.326)),
    ("T10", "gibbs_line_2", "积分消去 theta,varphi", 21, "node_formula_text", 9.4, (200.752, 249.009, 254.994, 258.683)),
    ("T11", "vem_line_1", "平均场变分 EM", 22, "node_text", 9.4, (371.990, 238.106, 435.259, 247.780)),
    ("T12", "vem_line_2", "ELBO 坐标上升", 22, "node_text", 9.4, (371.779, 249.463, 435.470, 259.137)),
    ("T13", "warning", "模型与后验不同，结果不可只按算法名直接比较", 29, "warning_text", 9.2, (219.511, 285.265, 411.989, 294.431)),
    ("T14", "caption_line_1", "图35.1 本章从共享的文档–主题–单词条件结构分出两个模型目标：完整Bayes LDA由折叠Gibbs", 32, "caption", None, (76.138, 308.361, 507.799, 318.822)),
    ("T15", "caption_line_2", "推断，点参数LDA变体由平均场变分EM估计；箭头表示学习依赖，不表示两个后验相同", 32, "caption", None, (76.138, 321.750, 469.801, 332.042)),
]


# The complete reader-visible semantic denominator. Node objects include their
# border/fill and their contained text; text-line evidence remains separately
# addressable through T01--T15 above.
OBJECTS = [
    ("O01", "node", "shared_structure_node", (230.0, 139.0, 401.0, 174.0)),
    ("O02", "text", "model_target_row_label", (107.0, 198.7, 146.2, 208.6)),
    ("O03", "node", "full_bayes_lda_node", (162.0, 185.0, 294.0, 222.0)),
    ("O04", "node", "point_parameter_lda_node", (337.0, 185.0, 470.0, 222.0)),
    ("O05", "text", "inference_method_row_label", (107.0, 244.0, 146.2, 254.0)),
    ("O06", "node", "collapsed_gibbs_node", (162.0, 230.0, 294.0, 268.0)),
    ("O07", "node", "mean_field_vem_node", (337.0, 230.0, 470.0, 268.0)),
    ("O08", "node", "warning_node", (151.0, 275.0, 480.0, 302.0)),
    ("O09", "arrow", "shared_to_full_arrow", (225.0, 173.0, 294.0, 187.0)),
    ("O10", "arrow", "shared_to_point_arrow", (337.0, 173.0, 407.0, 187.0)),
    ("O11", "arrow", "full_to_gibbs_arrow", (225.0, 221.0, 231.0, 231.0)),
    ("O12", "arrow", "point_to_vem_arrow", (401.0, 221.0, 407.0, 231.0)),
    ("O13", "caption", "caption_line_1", (76.0, 308.2, 508.0, 319.0)),
    ("O14", "caption", "caption_line_2", (76.0, 321.6, 470.0, 333.0)),
]


ROIS = [
    ("roi_top_arrows", (155.0, 136.0, 475.0, 225.0)),
    ("roi_vertical_arrows", (155.0, 214.0, 475.0, 271.0)),
    ("roi_warning_caption", (70.0, 271.0, 520.0, 336.0)),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pt_bbox_to_px(bbox: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return tuple(round(v * SCALE) for v in (x0, y0, x1, y1))


def background_median(crop: Image.Image) -> tuple[int, int, int]:
    rgb = crop.convert("RGB")
    w, h = rgb.size
    samples = []
    for x in range(w):
        samples.append(rgb.getpixel((x, 0)))
        samples.append(rgb.getpixel((x, h - 1)))
    for y in range(h):
        samples.append(rgb.getpixel((0, y)))
        samples.append(rgb.getpixel((w - 1, y)))
    return tuple(int(median([p[k] for p in samples])) for k in range(3))


def ink_bbox_and_height(page: Image.Image, bbox_pt: tuple[float, float, float, float]):
    x0, y0, x1, y1 = pt_bbox_to_px(bbox_pt)
    pad = 3
    crop_box = (max(0, x0 - pad), max(0, y0 - pad), min(page.width, x1 + pad), min(page.height, y1 + pad))
    crop = page.crop(crop_box).convert("RGB")
    bg = background_median(crop)
    bg_img = Image.new("RGB", crop.size, bg)
    diff = ImageChops.difference(crop, bg_img)
    r, g, b = diff.split()
    strength = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mask = strength.point(lambda v: 255 if v >= 20 else 0)
    ib = mask.getbbox()
    if ib is None:
        return None, 0, bg
    gx0 = crop_box[0] + ib[0]
    gy0 = crop_box[1] + ib[1]
    gx1 = crop_box[0] + ib[2]
    gy1 = crop_box[1] + ib[3]
    return (gx0, gy0, gx1, gy1), gy1 - gy0, bg


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    inter_w = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    inter_h = max(0.0, min(ay1, by1) - max(ay0, by0))
    return dx, dy, (dx * dx + dy * dy) ** 0.5, inter_w * inter_h


def median_pdf_char_size(chars, bbox):
    x0, y0, x1, y1 = bbox
    sizes = [float(c["size"]) for c in chars if c["x0"] >= x0 - 0.5 and c["x1"] <= x1 + 0.5 and c["top"] >= y0 - 0.5 and c["bottom"] <= y1 + 0.5]
    return round(median(sizes), 4) if sizes else None


def draw_overlay(page: Image.Image, entries, out_path: Path, crop_pt=(70.0, 134.0, 520.0, 338.0)):
    crop_px = pt_bbox_to_px(crop_pt)
    canvas = page.crop(crop_px).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    colors = ["#d7191c", "#2c7bb6", "#1a9641", "#fdae61", "#7b3294", "#008837"]
    for idx, entry in enumerate(entries):
        eid, kind, name, bbox = entry
        bx = pt_bbox_to_px(bbox)
        rel = (bx[0] - crop_px[0], bx[1] - crop_px[1], bx[2] - crop_px[0], bx[3] - crop_px[1])
        color = colors[idx % len(colors)]
        draw.rectangle(rel, outline=color, width=3)
        draw.rectangle((rel[0], max(0, rel[1] - 13), rel[0] + 34, rel[1]), fill="white")
        draw.text((rel[0] + 1, max(0, rel[1] - 12)), eid, fill=color, font=font)
    canvas.save(out_path)


def main():
    MACHINE.mkdir(parents=True, exist_ok=True)
    page_300 = Image.open(PAGE_300).convert("RGB")
    page_200 = Image.open(PAGE_200).convert("RGB")

    with pdfplumber.open(PDF) as doc:
        assert len(doc.pages) == 817
        hits = []
        for index in range(650, 751):
            text = doc.pages[index].extract_text() or ""
            if "模型与后验不同，结果不可只按算法名直接比较" in text and "本章从共享的文档" in text:
                hits.append(index + 1)
        if hits != [PDF_PAGE_NUMBER]:
            raise RuntimeError(f"caption/source localization not unique: {hits}")
        page = doc.pages[PDF_PAGE_NUMBER - 1]
        chars = [c for c in page.chars if c["x0"] >= 70.0 and c["x1"] <= 520.0 and c["top"] >= 134.0 and c["bottom"] <= 338.0]

    figure_crop_pt = (70.0, 134.0, 520.0, 338.0)
    figure_crop_px = pt_bbox_to_px(figure_crop_pt)
    figure = page_300.crop(figure_crop_px)
    figure.save(MACHINE / "figure_native300.png")
    ImageOps.grayscale(figure).save(MACHINE / "figure_grayscale_native300.png")
    draw_overlay(page_300, [(eid, role, name, bbox) for eid, name, _text, _line, role, _pt, bbox in TEXT_ELEMENTS], MACHINE / "overlay_text_ids_native300.png", figure_crop_pt)
    draw_overlay(page_300, OBJECTS, MACHINE / "overlay_object_ids_native300.png", figure_crop_pt)

    for roi_name, roi_pt in ROIS:
        roi = page_300.crop(pt_bbox_to_px(roi_pt))
        roi.save(MACHINE / f"{roi_name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(MACHINE / f"{roi_name}_nearest8x.png")

    with (MACHINE / "source_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ELEMENT_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT_SOURCE", "PDF_VECTOR_SIZE_PT", "TEXT_SAMPLE"])
        for eid, _name, text, line, role, pt, bbox in TEXT_ELEMENTS:
            writer.writerow([eid, role, str(FIG_SOURCE), line, "" if pt is None else pt, 1.0, "" if pt is None else pt, median_pdf_char_size(chars, bbox), text])

    measurements = []
    with (MACHINE / "native300_text_measurements.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ELEMENT_ID", "ROLE", "TEXT_SAMPLE", "BBOX_PT_X0", "BBOX_PT_TOP", "BBOX_PT_X1", "BBOX_PT_BOTTOM", "BBOX_PX_X0", "BBOX_PX_Y0", "BBOX_PX_X1", "BBOX_PX_Y1", "H_INK_PX", "LOCAL_BG_RGB", "FOREGROUND_DELTA_THRESHOLD"])
        for eid, _name, text, _line, role, _pt, bbox in TEXT_ELEMENTS:
            ib, h_ink, bg = ink_bbox_and_height(page_300, bbox)
            px = pt_bbox_to_px(bbox)
            measurements.append((eid, role, h_ink))
            writer.writerow([eid, role, text, *bbox, *px, h_ink, "/".join(map(str, bg)), 20])

    with (MACHINE / "glyph_inventory.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["GLYPH_ID", "TEXT", "UNICODE_CODEPOINTS", "FONTNAME", "PDF_SIZE_PT", "X0_PT", "TOP_PT", "X1_PT", "BOTTOM_PT"])
        for idx, char in enumerate(chars, 1):
            text = char.get("text", "")
            cps = " ".join(f"U+{ord(c):04X}" for c in text)
            writer.writerow([f"G{idx:04d}", text, cps, char.get("fontname", ""), char.get("size", ""), char["x0"], char["top"], char["x1"], char["bottom"]])

    with (MACHINE / "object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["OBJECT_ID", "OBJECT_CLASS", "OBJECT_NAME", "BBOX_X0_PT", "BBOX_TOP_PT", "BBOX_X1_PT", "BBOX_BOTTOM_PT"])
        writer.writerows(OBJECTS)

    pairs = list(itertools.combinations(OBJECTS, 2))
    with (MACHINE / "all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B"])
        for idx, (a, b) in enumerate(pairs, 1):
            writer.writerow([f"P{idx:03d}", a[0], b[0]])

    with (MACHINE / "pair_bbox_geometry.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B", "DX_PT", "DY_PT", "EUCLIDEAN_GAP_PT", "BBOX_INTERSECTION_AREA_PT2"])
        for idx, (a, b) in enumerate(pairs, 1):
            writer.writerow([f"P{idx:03d}", a[0], b[0], *[round(v, 4) for v in bbox_gap(a[3], b[3])]])

    arrows = [obj for obj in OBJECTS if obj[1] == "arrow"]
    with (MACHINE / "text_arrow_bbox_clearance.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["TEXT_ELEMENT_ID", "ARROW_OBJECT_ID", "DX_PT", "DY_PT", "EUCLIDEAN_GAP_PT", "BBOX_INTERSECTION_AREA_PT2", "EUCLIDEAN_GAP_PX_AT_300DPI"])
        for text_element in TEXT_ELEMENTS:
            for arrow in arrows:
                dx, dy, gap, area = bbox_gap(text_element[6], arrow[3])
                writer.writerow([text_element[0], arrow[0], round(dx, 4), round(dy, 4), round(gap, 4), round(area, 4), round(gap * SCALE, 2)])

    internal_map = {
        "O01": ["T01", "T02"],
        "O03": ["T04", "T05"],
        "O04": ["T06", "T07"],
        "O06": ["T09", "T10"],
        "O07": ["T11", "T12"],
        "O08": ["T13"],
    }
    object_by_id = {obj[0]: obj for obj in OBJECTS}
    text_by_id = {text_element[0]: text_element for text_element in TEXT_ELEMENTS}
    with (MACHINE / "node_internal_text_border_clearance.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["NODE_OBJECT_ID", "TEXT_ELEMENT_ID", "LEFT_PT", "TOP_PT", "RIGHT_PT", "BOTTOM_PT", "MIN_CLEARANCE_PT", "MIN_CLEARANCE_PX_AT_300DPI"])
        for object_id, text_ids in internal_map.items():
            ox0, oy0, ox1, oy1 = object_by_id[object_id][3]
            for text_id in text_ids:
                tx0, ty0, tx1, ty1 = text_by_id[text_id][6]
                clearances = (tx0 - ox0, ty0 - oy0, ox1 - tx1, oy1 - ty1)
                min_clearance = min(clearances)
                writer.writerow([object_id, text_id, *[round(v, 4) for v in clearances], round(min_clearance, 4), round(min_clearance * SCALE, 2)])

    role_heights = {}
    for eid, role, height in measurements:
        role_heights.setdefault(role, []).append((eid, height))
    with (MACHINE / "same_role_native300_height_ratios.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ROLE", "ELEMENT_ID", "H_INK_PX", "ROLE_MEDIAN_H_INK_PX", "RATIO_TO_ROLE_MEDIAN"])
        for role, values in sorted(role_heights.items()):
            role_median = median([height for _eid, height in values])
            for eid, height in values:
                writer.writerow([role, eid, height, role_median, round(height / role_median, 4) if role_median else ""])

    extracted = "".join(c.get("text", "") for c in chars)
    (MACHINE / "figure_region_extracted_text.txt").write_text(extracted, encoding="utf-8")

    font_counts = Counter(c.get("fontname", "") for c in chars)
    metadata = {
        "handoff_id": HANDOFF_ID,
        "uid": UID,
        "pdf": str(PDF),
        "pdf_page_number": PDF_PAGE_NUMBER,
        "printed_page_number": 716,
        "page_count": 817,
        "page_size_pt": [595.276, 841.89],
        "full_page_300_px": list(page_300.size),
        "full_page_200_px": list(page_200.size),
        "localized_by_current_caption_and_source_text": True,
        "caption_match_pages_in_651_to_751": [PDF_PAGE_NUMBER],
        "figure_crop_pt": list(figure_crop_pt),
        "figure_crop_px": list(figure_crop_px),
        "reader_visible_object_count": len(OBJECTS),
        "text_element_count": len(TEXT_ELEMENTS),
        "unordered_pair_count": len(pairs),
        "glyph_record_count": len(chars),
        "font_counts": dict(sorted(font_counts.items())),
        "input_identity": {
            "pdf_bytes": PDF.stat().st_size,
            "pdf_sha256": sha256(PDF),
            "figure_source_bytes": FIG_SOURCE.stat().st_size,
            "figure_source_sha256": sha256(FIG_SOURCE),
            "chapter_source_bytes": CHAPTER_SOURCE.stat().st_size,
            "chapter_source_sha256": sha256(CHAPTER_SOURCE),
        },
        "machine_measurement_note": "No manual verdict field is generated by this script. Pixel and bbox results are measurements only.",
    }
    (MACHINE / "evidence_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    inventory = []
    for path in sorted(MACHINE.iterdir(), key=lambda p: p.name):
        if path.is_file() and path.name != "machine_file_inventory.json":
            inventory.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    (MACHINE / "machine_file_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
