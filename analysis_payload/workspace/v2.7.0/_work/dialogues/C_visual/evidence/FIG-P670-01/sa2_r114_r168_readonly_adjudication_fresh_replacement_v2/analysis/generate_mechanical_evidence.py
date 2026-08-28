from __future__ import annotations

import csv
import itertools
import json
import math
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa2_r114_r168_readonly_adjudication_fresh_replacement_v2")
PAGE_PNG = ROOT / "renders" / "physical_717_full_page_native_300dpi.png"
GRAY_PAGE_PNG = ROOT / "renders" / "physical_717_full_page_grayscale_native_300dpi.png"
BBOX_HTML = ROOT / "analysis" / "physical_717_bbox.html"

DPI = 300
PT_TO_PX = DPI / 72.0
FIGURE_CROP_PT = (60.0, 64.0, 535.0, 225.0)


def element(element_id, role, text, bbox, declared_pt, panel, source_line):
    return {
        "element_id": element_id,
        "role": role,
        "text": text,
        "bbox_pt": bbox,
        "declared_pt": declared_pt,
        "panel": panel,
        "source_line": source_line,
    }


ELEMENTS = [
    element("E01", "LEFT_TITLE", "时刻 N：伪计数 α+n=(4,3,2)", (67.4, 82.5, 203.4, 98.6), "9.8", "LEFT", 14),
    element("E02", "TOKEN_LABEL", "1", (72.8, 104.9, 78.9, 115.4), "9.2", "LEFT", 15),
    element("E03", "TOKEN_LABEL", "1", (91.3, 104.9, 97.3, 115.4), "9.2", "LEFT", 15),
    element("E04", "TOKEN_LABEL", "1", (109.7, 104.9, 115.7, 115.4), "9.2", "LEFT", 15),
    element("E05", "TOKEN_LABEL", "1", (128.1, 104.9, 134.2, 115.4), "9.2", "LEFT", 15),
    element("E06", "TOKEN_LABEL", "2", (147.9, 104.9, 154.0, 115.4), "9.2", "LEFT", 16),
    element("E07", "TOKEN_LABEL", "2", (166.4, 104.9, 172.4, 115.4), "9.2", "LEFT", 16),
    element("E08", "TOKEN_LABEL", "2", (184.8, 104.9, 190.9, 115.4), "9.2", "LEFT", 16),
    element("E09", "TOKEN_LABEL", "3", (204.7, 104.9, 210.7, 115.4), "9.2", "LEFT", 17),
    element("E10", "TOKEN_LABEL", "3", (223.1, 104.9, 229.1, 115.4), "9.2", "LEFT", 17),
    element("E11", "PROBABILITY_LABEL", "4/9", (96.7, 123.5, 111.8, 133.7), "8.5", "LEFT", 25),
    element("E12", "PROBABILITY_LABEL", "3/9", (146.5, 123.5, 161.2, 133.7), "8.5", "LEFT", 25),
    element("E13", "PROBABILITY_LABEL", "2/9", (181.9, 123.5, 196.6, 133.7), "8.5", "LEFT", 25),
    element("E14", "FORMULA", "P(Y_(N+1)=k|n)=(α_k+n_k)/(α_0+N)", (81.2, 135.2, 195.0, 158.9), "9.2", "LEFT", 19),
    element("E15", "ARROW_LABEL", "预测", (232.4, 83.1, 251.4, 93.8), "8.8", "CENTER", 31),
    element("E16", "OBSERVATION_NODE", "观察 j=2", (265.4, 117.2, 288.8, 139.2), "9.2", "CENTER", 28),
    element("E17", "ARROW_LABEL", "只更新 第j类", (306.1, 71.6, 334.0, 92.9), "8.8", "CENTER", 32),
    element("E18", "RIGHT_TITLE", "时刻 N+1：(4,4,2)", (364.4, 82.5, 450.7, 98.6), "9.8", "RIGHT", 35),
    element("E19", "TOKEN_LABEL", "1", (339.3, 104.9, 345.4, 115.4), "9.2", "RIGHT", 36),
    element("E20", "TOKEN_LABEL", "1", (357.7, 104.9, 363.8, 115.4), "9.2", "RIGHT", 36),
    element("E21", "TOKEN_LABEL", "1", (376.1, 104.9, 382.2, 115.4), "9.2", "RIGHT", 36),
    element("E22", "TOKEN_LABEL", "1", (394.6, 104.9, 400.6, 115.4), "9.2", "RIGHT", 36),
    element("E23", "TOKEN_LABEL", "2", (414.4, 104.9, 420.5, 115.4), "9.2", "RIGHT", 37),
    element("E24", "TOKEN_LABEL", "2", (432.8, 104.9, 438.9, 115.4), "9.2", "RIGHT", 37),
    element("E25", "TOKEN_LABEL", "2", (451.3, 104.9, 457.3, 115.4), "9.2", "RIGHT", 37),
    element("E26", "TOKEN_LABEL", "2", (469.7, 104.9, 475.8, 115.4), "9.2", "RIGHT", 45),
    element("E27", "TOKEN_LABEL", "3", (489.5, 104.9, 495.6, 115.4), "9.2", "RIGHT", 50),
    element("E28", "TOKEN_LABEL", "3", (508.0, 104.9, 514.0, 115.4), "9.2", "RIGHT", 50),
    element("E29", "PROBABILITY_LABEL", "4/10", (372.0, 123.5, 392.1, 133.7), "8.5", "RIGHT", 58),
    element("E30", "PROBABILITY_LABEL", "4/10", (423.0, 123.5, 443.1, 133.7), "8.5", "RIGHT", 58),
    element("E31", "PROBABILITY_LABEL", "2/10", (461.4, 123.5, 481.2, 133.7), "8.5", "RIGHT", 58),
    element("E32", "FORMULA", "n_2←n_2+1, α_0+N←α_0+N+1", (344.0, 138.9, 499.4, 151.0), "9.2", "RIGHT", 51),
    element("E33", "SUMMARY", "顺序更新产生平滑与强化；积分掉θ后序列可交换，但它不是固定参数条件下的iid序列。", (119.0, 165.4, 479.5, 176.7), "9.2", "GLOBAL", 62),
    element("E34", "CAPTION_LABEL", "图34.10", (75.4, 181.1, 111.2, 197.0), "INHERITED", "CAPTION", 65),
    element("E35", "CAPTION_TEXT", "积分消去θ后，下一类别的后验预测概率等于当前伪计数占总伪计数的比例；观测到类别j只增加该类计数，因而实现平滑并产生可顺序更新的强化预测，但这不是固定参数下的独立同分布序列", (75.4, 184.7, 508.6, 223.6), "INHERITED", "CAPTION", 65),
]


SEMANTIC_OBJECTS = [
    ("S01", "left pseudocount tokens", (67.0, 82.0, 231.0, 119.5)),
    ("S02", "left probability partition", (74.5, 118.2, 205.5, 136.7)),
    ("S03", "left predictive formula", (79.0, 133.5, 198.0, 161.0)),
    ("S04", "prediction arrow", (213.0, 91.0, 263.5, 128.0)),
    ("S05", "observed category node", (258.0, 101.0, 296.0, 145.0)),
    ("S06", "single-category update arrow", (296.0, 68.0, 353.0, 128.0)),
    ("S07", "right updated tokens", (334.0, 82.0, 517.0, 119.5)),
    ("S08", "right probability partition", (357.0, 118.2, 491.5, 136.7)),
    ("S09", "right update formula", (341.0, 136.0, 502.0, 153.5)),
    ("S10", "exchangeability summary", (112.0, 158.0, 487.0, 181.0)),
    ("S11", "caption", (72.0, 179.0, 511.0, 225.0)),
]


def pt_box_to_px(box):
    return tuple(int(round(v * PT_TO_PX)) for v in box)


def crop_box_to_local_px(box):
    x0, y0, _, _ = FIGURE_CROP_PT
    bx0, by0, bx1, by1 = box
    return (
        int(round((bx0 - x0) * PT_TO_PX)),
        int(round((by0 - y0) * PT_TO_PX)),
        int(round((bx1 - x0) * PT_TO_PX)),
        int(round((by1 - y0) * PT_TO_PX)),
    )


def ink_metrics(page_gray, box):
    x0, y0, x1, y1 = pt_box_to_px(box)
    x0 = max(0, x0 - 2)
    y0 = max(0, y0 - 2)
    x1 = min(page_gray.width, x1 + 2)
    y1 = min(page_gray.height, y1 + 2)
    a = np.asarray(page_gray.crop((x0, y0, x1, y1)), dtype=np.int16)
    if a.size == 0:
        return {"h_ink_px": 0, "w_ink_px": 0, "ink_pixel_count": 0, "threshold": 0}
    border = np.concatenate((a[0, :], a[-1, :], a[:, 0], a[:, -1]))
    bg = float(np.percentile(border, 80))
    threshold = max(0.0, bg - 20.0)
    mask = a <= threshold
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {"h_ink_px": 0, "w_ink_px": 0, "ink_pixel_count": 0, "threshold": round(threshold, 2)}
    return {
        "h_ink_px": int(ys.max() - ys.min() + 1),
        "w_ink_px": int(xs.max() - xs.min() + 1),
        "ink_pixel_count": int(mask.sum()),
        "threshold": round(threshold, 2),
    }


def write_denominator_and_pairs():
    out = ROOT / "analysis" / "visible_denominator_frozen.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["element_id", "panel", "role", "text", "source_line", "declared_pt", "bbox_x0_pt", "bbox_y0_pt", "bbox_x1_pt", "bbox_y1_pt"])
        for e in ELEMENTS:
            w.writerow([e["element_id"], e["panel"], e["role"], e["text"], e["source_line"], e["declared_pt"], *e["bbox_pt"]])

    pair_out = ROOT / "analysis" / "all_unordered_pairs_frozen.csv"
    with pair_out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["pair_id", "element_a", "element_b"])
        for idx, (a, b) in enumerate(itertools.combinations(ELEMENTS, 2), start=1):
            w.writerow([f"P{idx:04d}", a["element_id"], b["element_id"]])


def write_metrics(gray_page):
    rows = []
    for e in ELEMENTS:
        m = ink_metrics(gray_page, e["bbox_pt"])
        rows.append({**e, **m})
    out = ROOT / "analysis" / "raster_object_measurements.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["element_id", "panel", "role", "text", "declared_pt", "bbox_x0_pt", "bbox_y0_pt", "bbox_x1_pt", "bbox_y1_pt", "h_ink_px", "w_ink_px", "ink_pixel_count", "local_threshold"])
        for r in rows:
            w.writerow([r["element_id"], r["panel"], r["role"], r["text"], r["declared_pt"], *r["bbox_pt"], r["h_ink_px"], r["w_ink_px"], r["ink_pixel_count"], r["threshold"]])

    numeric = [r["h_ink_px"] for r in rows if r["h_ink_px"] > 0]
    summary = {
        "element_count": len(ELEMENTS),
        "unordered_pair_count": math.comb(len(ELEMENTS), 2),
        "measured_positive_ink_count": len(numeric),
        "minimum_measured_ink_height_px": min(numeric),
        "median_measured_ink_height_px": statistics.median(numeric),
        "maximum_measured_ink_height_px": max(numeric),
        "scope": "all reader-visible figure and caption text objects; page furniture and adjacent example excluded",
    }
    (ROOT / "analysis" / "mechanical_measurement_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_crops_and_overlays(page, gray_page):
    crop_px = pt_box_to_px(FIGURE_CROP_PT)
    figure = page.crop(crop_px)
    gray_figure = gray_page.crop(crop_px)
    figure.save(ROOT / "renders" / "figure_34_10_native_300dpi.png")
    gray_figure.save(ROOT / "renders" / "figure_34_10_grayscale_native_300dpi.png")

    overlay = figure.convert("RGB")
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    colors = {
        "LEFT": (220, 20, 60),
        "CENTER": (148, 0, 211),
        "RIGHT": (0, 120, 40),
        "GLOBAL": (255, 90, 0),
        "CAPTION": (0, 80, 220),
    }
    for e in ELEMENTS:
        b = crop_box_to_local_px(e["bbox_pt"])
        color = colors[e["panel"]]
        draw.rectangle(b, outline=color, width=3)
        tx = b[0]
        ty = max(0, b[1] - 14)
        label = e["element_id"]
        tb = draw.textbbox((tx, ty), label, font=font)
        draw.rectangle((tb[0] - 2, tb[1] - 1, tb[2] + 2, tb[3] + 1), fill=(255, 255, 255))
        draw.text((tx, ty), label, fill=color, font=font)
    overlay.save(ROOT / "renders" / "figure_34_10_text_object_overlay_300dpi.png")

    semantic = figure.convert("RGB")
    draw = ImageDraw.Draw(semantic)
    semantic_colors = [(220, 20, 60), (0, 130, 180), (120, 70, 200), (0, 125, 50), (230, 120, 0)]
    for idx, (sid, _name, box) in enumerate(SEMANTIC_OBJECTS):
        b = crop_box_to_local_px(box)
        color = semantic_colors[idx % len(semantic_colors)]
        draw.rectangle(b, outline=color, width=4)
        tx, ty = b[0] + 3, b[1] + 3
        tb = draw.textbbox((tx, ty), sid, font=font)
        draw.rectangle((tb[0] - 2, tb[1] - 1, tb[2] + 2, tb[3] + 1), fill=(255, 255, 255))
        draw.text((tx, ty), sid, fill=color, font=font)
    semantic.save(ROOT / "renders" / "figure_34_10_semantic_object_overlay_300dpi.png")

    with (ROOT / "analysis" / "semantic_object_legend.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["semantic_object_id", "description", "bbox_x0_pt", "bbox_y0_pt", "bbox_x1_pt", "bbox_y1_pt"])
        for sid, name, box in SEMANTIC_OBJECTS:
            w.writerow([sid, name, *box])

    roi_specs = [
        ("roi_left_formula_probability", (72.0, 117.0, 207.0, 161.0)),
        ("roi_center_arrows_observation", (208.0, 66.0, 356.0, 151.0)),
        ("roi_right_updated_counts", (333.0, 80.0, 520.0, 154.0)),
        ("roi_summary_caption", (72.0, 158.0, 512.0, 225.0)),
    ]
    for name, box in roi_specs:
        raw = page.crop(pt_box_to_px(box))
        raw.save(ROOT / "roi" / f"{name}_native1x_300dpi.png")
        raw.resize((raw.width * 8, raw.height * 8), resample=Image.Resampling.NEAREST).save(ROOT / "roi" / f"{name}_nearest_neighbor_8x.png")


def verify_bbox_html():
    tree = ET.parse(BBOX_HTML)
    root = tree.getroot()
    ns = {"x": "http://www.w3.org/1999/xhtml"}
    page = root.find(".//x:page", ns)
    if page is None:
        raise RuntimeError("bbox page missing")
    if page.attrib.get("width") != "595.276000" or page.attrib.get("height") != "841.890000":
        raise RuntimeError("unexpected page geometry")


def main():
    verify_bbox_html()
    page = Image.open(PAGE_PNG).convert("RGB")
    gray_page = Image.open(GRAY_PAGE_PNG).convert("L")
    if page.size != (2481, 3508):
        raise RuntimeError(f"unexpected 300-dpi render size: {page.size}")
    write_denominator_and_pairs()
    write_metrics(gray_page)
    make_crops_and_overlays(page, gray_page)
    print(f"ELEMENT_COUNT={len(ELEMENTS)}")
    print(f"UNORDERED_PAIR_COUNT={math.comb(len(ELEMENTS), 2)}")
    print(f"RENDER_SIZE={page.width}x{page.height}")


if __name__ == "__main__":
    main()
