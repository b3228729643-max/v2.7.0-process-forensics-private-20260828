from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import platform
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps


HANDOFF_ID = "C-FIG-P670-01-R114-SA3-FRESH-ISOLATED-V1"
UID = "FIG-P670-01"
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa3_r114_fresh_isolated_v1")
PDF_PATH = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
TEX_PATH = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_posterior_predictive.tex")
EXPECTED_PDF_BYTES = 4_967_122
EXPECTED_PDF_SHA256 = "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6"
EXPECTED_TEX_BYTES = 4_833
EXPECTED_TEX_SHA256 = "614C1E5C0FACF9A7C2E6F0CB126EB6EA4F18F1BF00F48744C8E248A8DE89F781"
CAPTION_NEEDLE = "下一类别的后验预测概率等于当前伪计数占总伪计数的比例"
DPI_200 = 200
DPI_300 = 300
SCALE_300 = DPI_300 / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rect_tuple(rect: fitz.Rect) -> tuple[float, float, float, float]:
    return tuple(round(float(x), 4) for x in (rect.x0, rect.y0, rect.x1, rect.y1))


def pixmap_image(page: fitz.Page, dpi: int, clip: fitz.Rect | None = None) -> Image.Image:
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def pt_rect_to_full_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        int(math.floor(rect.x0 * SCALE_300)),
        int(math.floor(rect.y0 * SCALE_300)),
        int(math.ceil(rect.x1 * SCALE_300)),
        int(math.ceil(rect.y1 * SCALE_300)),
    )


def union_word_bbox(words: list[tuple], region: fitz.Rect) -> tuple[fitz.Rect, str]:
    selected = []
    for w in words:
        wr = fitz.Rect(w[:4])
        center = fitz.Point((wr.x0 + wr.x1) / 2.0, (wr.y0 + wr.y1) / 2.0)
        if region.contains(center):
            selected.append(w)
    if not selected:
        return region, ""
    bbox = fitz.Rect(selected[0][:4])
    for w in selected[1:]:
        bbox |= fitz.Rect(w[:4])
    selected.sort(key=lambda w: (round(w[1], 1), w[0]))
    return bbox, " ".join(str(w[4]) for w in selected)


def bbox_gap(a: fitz.Rect, b: fitz.Rect) -> float:
    dx = max(a.x0 - b.x1, b.x0 - a.x1, 0.0)
    dy = max(a.y0 - b.y1, b.y0 - a.y1, 0.0)
    return math.hypot(dx, dy)


def bbox_relation(a: fitz.Rect, b: fitz.Rect) -> tuple[str, float]:
    inter = a & b
    area = max(0.0, inter.width) * max(0.0, inter.height)
    if area <= 0:
        return "DISJOINT", 0.0
    if a.contains(b):
        return "A_CONTAINS_B", area
    if b.contains(a):
        return "B_CONTAINS_A", area
    return "BBOX_INTERSECTION", area


def ink_height_px(full_300: Image.Image, bbox: fitz.Rect) -> tuple[int, int, int, int, int]:
    px = pt_rect_to_full_px(bbox)
    x0 = max(0, px[0])
    y0 = max(0, px[1])
    x1 = min(full_300.width, px[2])
    y1 = min(full_300.height, px[3])
    crop = ImageOps.grayscale(full_300.crop((x0, y0, x1, y1)))
    if crop.width == 0 or crop.height == 0:
        return x0, y0, x1, y1, 0
    vals = list(crop.getdata())
    border = []
    for x in range(crop.width):
        border.append(crop.getpixel((x, 0)))
        border.append(crop.getpixel((x, crop.height - 1)))
    for y in range(crop.height):
        border.append(crop.getpixel((0, y)))
        border.append(crop.getpixel((crop.width - 1, y)))
    border.sort()
    background = border[len(border) // 2] if border else 255
    ys = []
    for y in range(crop.height):
        for x in range(crop.width):
            if abs(int(crop.getpixel((x, y))) - int(background)) >= 20:
                ys.append(y)
    height = max(ys) - min(ys) + 1 if ys else 0
    return x0, y0, x1, y1, height


def main() -> None:
    if not ROOT.is_dir():
        raise RuntimeError("sealed-root candidate does not exist")
    pdf_bytes = PDF_PATH.stat().st_size
    tex_bytes = TEX_PATH.stat().st_size
    pdf_hash = sha256(PDF_PATH)
    tex_hash = sha256(TEX_PATH)
    if (pdf_bytes, pdf_hash) != (EXPECTED_PDF_BYTES, EXPECTED_PDF_SHA256):
        raise RuntimeError("PDF identity differs from fixed R114 identity")
    if (tex_bytes, tex_hash) != (EXPECTED_TEX_BYTES, EXPECTED_TEX_SHA256):
        raise RuntimeError("TeX identity differs from fixed current-source identity")

    doc = fitz.open(PDF_PATH)
    hits = []
    page_texts = []
    for index in range(doc.page_count):
        text = doc.load_page(index).get_text("text")
        if CAPTION_NEEDLE in text:
            hits.append(index)
            page_texts.append(text)
    if len(hits) != 1:
        raise RuntimeError(f"caption uniqueness count is {len(hits)}")
    page_index = hits[0]
    page = doc.load_page(page_index)
    physical_page = page_index + 1

    figure_rect = fitz.Rect(62.0, 65.0, 522.0, 180.5)
    figure_caption_rect = fitz.Rect(62.0, 65.0, 522.0, 224.0)
    caption_rect = fitz.Rect(72.0, 180.0, 512.0, 224.0)

    full_200 = pixmap_image(page, DPI_200)
    full_300 = pixmap_image(page, DPI_300)
    figure_300 = pixmap_image(page, DPI_300, figure_rect)
    figure_caption_300 = pixmap_image(page, DPI_300, figure_caption_rect)
    full_200.save(ROOT / "full_page_200dpi.png")
    full_300.save(ROOT / "full_page_native_300dpi.png")
    figure_300.save(ROOT / "figure_crop_native_300dpi.png")
    figure_caption_300.save(ROOT / "figure_caption_crop_native_300dpi.png")
    ImageOps.grayscale(figure_caption_300).save(ROOT / "grayscale_figure_caption_300dpi.png")

    words = page.get_text("words")

    left_nodes = [
        ("T_L_NODE_01", "1", 15, fitz.Rect(67.37, 101.14, 84.38, 118.15)),
        ("T_L_NODE_02", "1", 15, fitz.Rect(85.79, 101.14, 102.80, 118.15)),
        ("T_L_NODE_03", "1", 15, fitz.Rect(104.22, 101.14, 121.23, 118.15)),
        ("T_L_NODE_04", "1", 15, fitz.Rect(122.65, 101.14, 139.65, 118.15)),
        ("T_L_NODE_05", "2", 16, fitz.Rect(142.49, 101.14, 159.50, 118.15)),
        ("T_L_NODE_06", "2", 16, fitz.Rect(160.91, 101.14, 177.92, 118.15)),
        ("T_L_NODE_07", "2", 16, fitz.Rect(179.34, 101.14, 196.35, 118.15)),
        ("T_L_NODE_08", "3", 17, fitz.Rect(199.18, 101.14, 216.19, 118.15)),
        ("T_L_NODE_09", "3", 17, fitz.Rect(217.61, 101.14, 234.61, 118.15)),
    ]
    right_nodes = [
        ("T_R_NODE_01", "1", 36, fitz.Rect(333.83, 101.14, 350.84, 118.15)),
        ("T_R_NODE_02", "1", 36, fitz.Rect(352.25, 101.14, 369.26, 118.15)),
        ("T_R_NODE_03", "1", 36, fitz.Rect(370.68, 101.14, 387.69, 118.15)),
        ("T_R_NODE_04", "1", 36, fitz.Rect(389.11, 101.14, 406.11, 118.15)),
        ("T_R_NODE_05", "2", 37, fitz.Rect(408.95, 101.14, 425.96, 118.15)),
        ("T_R_NODE_06", "2", 37, fitz.Rect(427.37, 101.14, 444.38, 118.15)),
        ("T_R_NODE_07", "2", 37, fitz.Rect(445.80, 101.14, 462.81, 118.15)),
        ("T_R_NODE_08", "2", 38, fitz.Rect(464.22, 101.14, 481.23, 118.15)),
        ("T_R_NODE_09", "3", 50, fitz.Rect(484.07, 101.14, 501.08, 118.15)),
        ("T_R_NODE_10", "3", 50, fitz.Rect(502.49, 101.14, 519.50, 118.15)),
    ]

    text_specs = [
        ("T_L_TITLE", "PANEL_TITLE", "时刻 N：伪计数 α+n=(4,3,2)", 14, fitz.Rect(67.0, 82.0, 230.0, 100.0)),
        *[(i, "TOKEN_LABEL", t, line, r) for i, t, line, r in left_nodes],
        ("T_L_FORMULA", "FORMULA", "P(Y_(N+1)=k|n)=(α_k+n_k)/(α_0+N)", 18, fitz.Rect(80.0, 134.0, 198.0, 160.0)),
        ("T_L_PROB_01", "PROBABILITY", "4/9", 25, fitz.Rect(75.87, 116.0, 132.57, 136.0)),
        ("T_L_PROB_02", "PROBABILITY", "3/9", 25, fitz.Rect(132.57, 116.0, 175.09, 136.0)),
        ("T_L_PROB_03", "PROBABILITY", "2/9", 25, fitz.Rect(175.09, 116.0, 203.43, 136.0)),
        ("T_OBSERVATION", "STATE_LABEL", "观察 j=2", 28, fitz.Rect(256.0, 106.0, 299.0, 150.0)),
        ("T_PREDICT", "ARROW_LABEL", "预测", 30, fitz.Rect(230.0, 80.0, 255.0, 97.0)),
        ("T_UPDATE_ONLY", "ARROW_LABEL", "只更新 第j类", 32, fitz.Rect(303.0, 68.0, 334.0, 100.0)),
        ("T_R_TITLE", "PANEL_TITLE", "时刻 N+1：(4,4,2)", 35, fitz.Rect(334.0, 82.0, 480.0, 100.0)),
        *[(i, "TOKEN_LABEL", t, line, r) for i, t, line, r in right_nodes],
        ("T_R_FORMULA", "FORMULA", "n_2←n_2+1, α_0+N←α_0+N+1", 51, fitz.Rect(342.0, 136.0, 501.0, 153.0)),
        ("T_R_PROB_01", "PROBABILITY", "4/10", 58, fitz.Rect(356.51, 116.0, 407.53, 136.0)),
        ("T_R_PROB_02", "PROBABILITY", "4/10", 58, fitz.Rect(407.53, 116.0, 458.55, 136.0)),
        ("T_R_PROB_03", "PROBABILITY", "2/10", 58, fitz.Rect(458.55, 116.0, 484.07, 136.0)),
        ("T_SUMMARY", "SUMMARY", "顺序更新产生平滑与强化；积分掉 θ 后序列可交换，但它不是固定参数条件下的 iid 序列。", 60, fitz.Rect(112.0, 160.0, 484.0, 180.0)),
        ("T_CAPTION", "CAPTION", "图34.10及完整题注", 65, caption_rect),
    ]

    graphic_specs = []
    for idx, (_, _, line, rect) in enumerate(left_nodes, 1):
        graphic_specs.append((f"G_L_NODE_{idx:02d}", "NODE_BORDER_FILL", line, rect))
    graphic_specs += [
        ("G_L_BAR_SEG_01", "PROBABILITY_BAR_SEGMENT", 20, fitz.Rect(75.87, 123.25, 132.57, 132.32)),
        ("G_L_BAR_SEG_02", "PROBABILITY_BAR_SEGMENT", 21, fitz.Rect(132.57, 123.25, 175.09, 132.32)),
        ("G_L_BAR_SEG_03", "PROBABILITY_BAR_SEGMENT", 22, fitz.Rect(175.09, 123.25, 203.43, 132.32)),
        ("G_OBSERVATION_NODE", "STATE_NODE_BORDER_FILL", 28, fitz.Rect(256.89, 107.54, 297.38, 148.03)),
        ("G_ARROW_PREDICT", "LINE_ARROW", 29, fitz.Rect(207.69, 126.70, 255.25, 128.90)),
        ("G_ARROW_UPDATE", "LINE_ARROW", 31, fitz.Rect(297.74, 126.70, 349.56, 128.90)),
    ]
    for idx, (_, _, line, rect) in enumerate(right_nodes, 1):
        role = "UPDATED_TOKEN_BORDER_FILL" if idx == 8 else "NODE_BORDER_FILL"
        graphic_specs.append((f"G_R_NODE_{idx:02d}", role, line, rect))
    graphic_specs += [
        ("G_R_BAR_SEG_01", "PROBABILITY_BAR_SEGMENT", 52, fitz.Rect(356.51, 123.25, 407.53, 132.32)),
        ("G_R_BAR_SEG_02", "UPDATED_PROBABILITY_BAR_SEGMENT", 53, fitz.Rect(407.53, 123.25, 458.55, 132.32)),
        ("G_R_BAR_SEG_03", "PROBABILITY_BAR_SEGMENT", 54, fitz.Rect(458.55, 123.25, 484.07, 132.32)),
        ("G_SUMMARY_BOX", "SUMMARY_BORDER_FILL", 60, fitz.Rect(111.31, 161.19, 482.65, 178.86)),
    ]

    objects = []
    source_text_rows = []
    for object_id, role, expected_text, source_line, region in text_specs:
        bbox, extracted_text = union_word_bbox(words, region)
        objects.append({
            "OBJECT_ID": object_id,
            "OBJECT_KIND": "TEXT",
            "ROLE": role,
            "SOURCE_LINE": source_line,
            "EXPECTED_TEXT": expected_text,
            "EXTRACTED_TEXT": extracted_text,
            "BBOX_X0_PT": round(bbox.x0, 4),
            "BBOX_Y0_PT": round(bbox.y0, 4),
            "BBOX_X1_PT": round(bbox.x1, 4),
            "BBOX_Y1_PT": round(bbox.y1, 4),
        })
        source_text_rows.append({
            "ELEMENT_ID": object_id,
            "ROLE": role,
            "SOURCE_LINE": source_line,
            "SOURCE_DECLARATION": expected_text,
            "PDF_EXTRACTED_TEXT": extracted_text,
        })
    for object_id, role, source_line, bbox in graphic_specs:
        objects.append({
            "OBJECT_ID": object_id,
            "OBJECT_KIND": "VECTOR",
            "ROLE": role,
            "SOURCE_LINE": source_line,
            "EXPECTED_TEXT": "",
            "EXTRACTED_TEXT": "",
            "BBOX_X0_PT": round(bbox.x0, 4),
            "BBOX_Y0_PT": round(bbox.y0, 4),
            "BBOX_X1_PT": round(bbox.x1, 4),
            "BBOX_Y1_PT": round(bbox.y1, 4),
        })
    objects.sort(key=lambda row: row["OBJECT_ID"])

    object_fields = [
        "OBJECT_ID", "OBJECT_KIND", "ROLE", "SOURCE_LINE", "EXPECTED_TEXT", "EXTRACTED_TEXT",
        "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT",
    ]
    inventory_path = ROOT / "visible_object_inventory.csv"
    write_csv(inventory_path, objects, object_fields)
    write_csv(
        ROOT / "source_visible_text_register.csv",
        source_text_rows,
        ["ELEMENT_ID", "ROLE", "SOURCE_LINE", "SOURCE_DECLARATION", "PDF_EXTRACTED_TEXT"],
    )

    object_by_id = {row["OBJECT_ID"]: row for row in objects}
    pairs = []
    pair_candidates = []
    for pair_index, (a_id, b_id) in enumerate(itertools.combinations(sorted(object_by_id), 2), 1):
        a = object_by_id[a_id]
        b = object_by_id[b_id]
        ar = fitz.Rect(a["BBOX_X0_PT"], a["BBOX_Y0_PT"], a["BBOX_X1_PT"], a["BBOX_Y1_PT"])
        br = fitz.Rect(b["BBOX_X0_PT"], b["BBOX_Y0_PT"], b["BBOX_X1_PT"], b["BBOX_Y1_PT"])
        relation, area = bbox_relation(ar, br)
        gap = bbox_gap(ar, br)
        row = {
            "PAIR_ID": f"PAIR_{pair_index:04d}",
            "OBJECT_A": a_id,
            "OBJECT_B": b_id,
            "KIND_A": a["OBJECT_KIND"],
            "KIND_B": b["OBJECT_KIND"],
            "BBOX_RELATION": relation,
            "BBOX_INTERSECTION_AREA_PT2": round(area, 6),
            "BBOX_GAP_PT": round(gap, 6),
        }
        pairs.append(row)
        if relation != "DISJOINT" or gap <= 1.5:
            pair_candidates.append(row)
    pair_fields = [
        "PAIR_ID", "OBJECT_A", "OBJECT_B", "KIND_A", "KIND_B",
        "BBOX_RELATION", "BBOX_INTERSECTION_AREA_PT2", "BBOX_GAP_PT",
    ]
    write_csv(ROOT / "all_unordered_pairs.csv", pairs, pair_fields)
    write_csv(ROOT / "bbox_pair_candidates.csv", pair_candidates, pair_fields)

    text_measurements = []
    for row in objects:
        if row["OBJECT_KIND"] != "TEXT":
            continue
        bbox = fitz.Rect(row["BBOX_X0_PT"], row["BBOX_Y0_PT"], row["BBOX_X1_PT"], row["BBOX_Y1_PT"])
        x0, y0, x1, y1, h_ink = ink_height_px(full_300, bbox)
        text_measurements.append({
            "ELEMENT_ID": row["OBJECT_ID"],
            "ROLE": row["ROLE"],
            "EXTRACTED_TEXT": row["EXTRACTED_TEXT"],
            "BBOX_X0_PX": x0,
            "BBOX_Y0_PX": y0,
            "BBOX_X1_PX": x1,
            "BBOX_Y1_PX": y1,
            "BBOX_HEIGHT_PX": y1 - y0,
            "MEASURED_INK_EXTENT_PX": h_ink,
        })
    write_csv(
        ROOT / "text_raster_measurements.csv",
        text_measurements,
        ["ELEMENT_ID", "ROLE", "EXTRACTED_TEXT", "BBOX_X0_PX", "BBOX_Y0_PX", "BBOX_X1_PX", "BBOX_Y1_PX", "BBOX_HEIGHT_PX", "MEASURED_INK_EXTENT_PX"],
    )

    overlay = figure_caption_300.copy()
    draw = ImageDraw.Draw(overlay)
    origin_x = figure_caption_rect.x0 * SCALE_300
    origin_y = figure_caption_rect.y0 * SCALE_300
    for row in objects:
        color = (0, 130, 35) if row["OBJECT_KIND"] == "TEXT" else (190, 0, 150)
        x0 = row["BBOX_X0_PT"] * SCALE_300 - origin_x
        y0 = row["BBOX_Y0_PT"] * SCALE_300 - origin_y
        x1 = row["BBOX_X1_PT"] * SCALE_300 - origin_x
        y1 = row["BBOX_Y1_PT"] * SCALE_300 - origin_y
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        draw.text((x0 + 2, y0 + 1), row["OBJECT_ID"], fill=color)
    overlay.save(ROOT / "semantic_object_overlay_300dpi.png")

    text_overlay = figure_caption_300.copy()
    text_draw = ImageDraw.Draw(text_overlay)
    for row in objects:
        if row["OBJECT_KIND"] != "TEXT":
            continue
        x0 = row["BBOX_X0_PT"] * SCALE_300 - origin_x
        y0 = row["BBOX_Y0_PT"] * SCALE_300 - origin_y
        x1 = row["BBOX_X1_PT"] * SCALE_300 - origin_x
        y1 = row["BBOX_Y1_PT"] * SCALE_300 - origin_y
        text_draw.rectangle((x0, y0, x1, y1), outline=(0, 120, 25), width=3)
        text_draw.text((x0 + 2, y0 + 1), row["OBJECT_ID"], fill=(0, 90, 20))
    text_overlay.save(ROOT / "text_object_overlay_300dpi.png")

    vector_overlay = figure_caption_300.copy()
    vector_draw = ImageDraw.Draw(vector_overlay)
    for row in objects:
        if row["OBJECT_KIND"] != "VECTOR":
            continue
        x0 = row["BBOX_X0_PT"] * SCALE_300 - origin_x
        y0 = row["BBOX_Y0_PT"] * SCALE_300 - origin_y
        x1 = row["BBOX_X1_PT"] * SCALE_300 - origin_x
        y1 = row["BBOX_Y1_PT"] * SCALE_300 - origin_y
        vector_draw.rectangle((x0, y0, x1, y1), outline=(190, 0, 150), width=3)
        vector_draw.text((x0 + 2, y0 + 1), row["OBJECT_ID"], fill=(150, 0, 115))
    vector_overlay.save(ROOT / "vector_object_overlay_300dpi.png")

    rois = [
        ("ROI01_left_header_nodes", fitz.Rect(64.0, 78.0, 238.0, 121.0)),
        ("ROI02_left_formula_probability", fitz.Rect(70.0, 115.0, 207.0, 161.0)),
        ("ROI03_center_arrows_observation", fitz.Rect(203.0, 67.0, 352.0, 152.0)),
        ("ROI04_right_header_nodes", fitz.Rect(330.0, 78.0, 522.0, 121.0)),
        ("ROI05_right_formula_probability", fitz.Rect(339.0, 115.0, 502.0, 156.0)),
        ("ROI06_summary_box", fitz.Rect(107.0, 157.0, 487.0, 181.0)),
        ("ROI07_caption", caption_rect),
    ]
    roi_rows = []
    for roi_id, rect in rois:
        image_1x = pixmap_image(page, DPI_300, rect)
        path_1x = ROOT / f"{roi_id}_native1x_300dpi.png"
        path_8x = ROOT / f"{roi_id}_nearest8x.png"
        image_1x.save(path_1x)
        image_1x.resize((image_1x.width * 8, image_1x.height * 8), Image.Resampling.NEAREST).save(path_8x)
        roi_rows.append({
            "ROI_ID": roi_id,
            "X0_PT": rect.x0,
            "Y0_PT": rect.y0,
            "X1_PT": rect.x1,
            "Y1_PT": rect.y1,
            "NATIVE_WIDTH_PX": image_1x.width,
            "NATIVE_HEIGHT_PX": image_1x.height,
            "NATIVE_FILE": path_1x.name,
            "NEAREST8X_FILE": path_8x.name,
        })
    write_csv(
        ROOT / "roi_register.csv",
        roi_rows,
        ["ROI_ID", "X0_PT", "Y0_PT", "X1_PT", "Y1_PT", "NATIVE_WIDTH_PX", "NATIVE_HEIGHT_PX", "NATIVE_FILE", "NEAREST8X_FILE"],
    )

    identity_rows = [
        {"RESOURCE": "R114_PDF", "PATH": str(PDF_PATH), "EXPECTED_BYTES": EXPECTED_PDF_BYTES, "ACTUAL_BYTES": pdf_bytes, "EXPECTED_SHA256": EXPECTED_PDF_SHA256, "ACTUAL_SHA256": pdf_hash},
        {"RESOURCE": "CURRENT_SOURCE", "PATH": str(TEX_PATH), "EXPECTED_BYTES": EXPECTED_TEX_BYTES, "ACTUAL_BYTES": tex_bytes, "EXPECTED_SHA256": EXPECTED_TEX_SHA256, "ACTUAL_SHA256": tex_hash},
    ]
    write_csv(ROOT / "input_identity.csv", identity_rows, ["RESOURCE", "PATH", "EXPECTED_BYTES", "ACTUAL_BYTES", "EXPECTED_SHA256", "ACTUAL_SHA256"])
    (ROOT / "page_text_extract.txt").write_text(page_texts[0], encoding="utf-8", newline="\n")

    inventory_hash = sha256(inventory_path)
    freeze = {
        "HANDOFF_ID": HANDOFF_ID,
        "UID": UID,
        "PDF_PHYSICAL_PAGE": physical_page,
        "PDF_PAGE_INDEX_ZERO_BASED": page_index,
        "SCOPE_RECT_PT": rect_tuple(figure_caption_rect),
        "TEXT_OBJECTS": sum(1 for row in objects if row["OBJECT_KIND"] == "TEXT"),
        "VECTOR_OBJECTS": sum(1 for row in objects if row["OBJECT_KIND"] == "VECTOR"),
        "VISIBLE_OBJECT_DENOMINATOR": len(objects),
        "ALL_UNORDERED_PAIRS": len(pairs),
        "PAIR_FORMULA": "N*(N-1)/2",
        "VISIBLE_OBJECT_INVENTORY_SHA256": inventory_hash,
        "PAIR_TABLE_FILE": "all_unordered_pairs.csv",
    }
    (ROOT / "denominator_freeze.json").write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    environment = {
        "HANDOFF_ID": HANDOFF_ID,
        "UID": UID,
        "PYTHON": sys.version,
        "PLATFORM": platform.platform(),
        "PYMUPDF": fitz.VersionBind,
        "PILLOW": Image.__version__,
        "PDF_PAGE_COUNT": doc.page_count,
        "MATCHED_PHYSICAL_PAGE": physical_page,
        "FULL_300_WIDTH_PX": full_300.width,
        "FULL_300_HEIGHT_PX": full_300.height,
        "FIGURE_CROP_WIDTH_PX": figure_300.width,
        "FIGURE_CROP_HEIGHT_PX": figure_300.height,
    }
    (ROOT / "mechanical_environment.json").write_text(json.dumps(environment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    doc.close()


if __name__ == "__main__":
    main()
