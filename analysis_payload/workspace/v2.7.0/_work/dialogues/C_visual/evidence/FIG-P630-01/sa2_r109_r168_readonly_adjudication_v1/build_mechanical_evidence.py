from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P630-01\sa2_r109_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf")
PAGE_NUMBER = 680
SCALE = 300.0 / 72.0


def obj(oid, cls, parent, desc, bbox, source_line):
    return {
        "object_id": oid,
        "object_class": cls,
        "parent_context": parent,
        "description": desc,
        "bbox_pdf": bbox,
        "source_line": source_line,
    }


OBJECTS = [
    obj("T01", "TEXT", "joint", "联合目标 / 局部因子", (153.236, 404.165, 237.946, 414.408), 18),
    obj("T02", "TEXT", "cond", "给定 x_{-j} 的满条件", (264.980, 397.077, 341.634, 408.329), 19),
    obj("T03", "FORMULA", "cond", "pi_j(⋅ | x_{-j})", (282.080, 409.196, 324.534, 420.085), 19),
    obj("T04", "TEXT_FORMULA", "coord", "单坐标核 K_j", (385.484, 396.464, 435.846, 407.717), 20),
    obj("T05", "TEXT_FORMULA", "coord", "只更新 x_j", (390.845, 409.445, 430.485, 420.698), 20),
    obj("T06", "TEXT", "scan", "扫描核", (396.677, 452.145, 425.369, 462.388), 21),
    obj("T07", "TEXT", "scan", "系统 / 随机", (387.797, 463.901, 434.250, 474.144), 21),
    obj("T08", "TEXT", "sample", "相关样本", (284.179, 458.023, 322.436, 468.266), 22),
    obj("T09", "TEXT", "diag", "诊断", (186.026, 452.145, 205.154, 462.388), 23),
    obj("T10", "TEXT", "diag", "MCSE / ESS / 轨迹", (157.128, 463.901, 234.052, 474.144), 23),
    obj("T11", "TEXT", "correct", "正确性条件", (95.631, 332.972, 148.148, 343.215), 29),
    obj("T12", "TEXT", "correct", "目标保持", (99.721, 344.528, 144.051, 354.771), 29),
    obj("T13", "TEXT", "correct", "支持可达", (99.721, 356.085, 144.051, 366.328), 29),
    obj("T14", "TEXT", "correct", "遍历性", (104.516, 367.642, 139.263, 377.885), 29),
    obj("T15", "TEXT", "mix", "混合效率", (462.555, 496.073, 506.885, 506.316), 30),
    obj("T16", "TEXT", "mix", "自相关长度", (458.465, 507.629, 510.982, 517.872), 30),
    obj("T17", "TEXT", "mix", "有效样本量", (458.465, 519.186, 510.982, 529.429), 30),
    obj("T18", "TEXT_FORMULA", "boundary", "正确内核 ≠ 快速混合", (257.529, 515.014, 349.086, 529.440), 34),
    obj("T19", "TEXT", "caption", "图 33.1", (89.982, 538.896, 119.830, 553.322), 37),
    obj("T20", "TEXT", "caption", "满条件把联合目标转为单坐标更新，扫描后得到需以 MCSE、ESS 与轨迹诊断的相关样本", (129.793, 542.483, 516.632, 553.153), 37),
    obj("B01", "NODE_BORDER", "joint", "joint core node border", (148.982, 389.756, 242.196, 426.607), 18),
    obj("B02", "NODE_BORDER", "cond", "conditional core node border", (259.369, 389.756, 347.245, 426.607), 19),
    obj("B03", "NODE_BORDER", "coord", "coordinate-kernel core node border", (367.087, 389.756, 454.963, 426.607), 20),
    obj("B04", "NODE_BORDER", "scan", "scan-kernel core node border", (367.087, 443.615, 454.963, 480.466), 21),
    obj("B05", "NODE_BORDER", "sample", "correlated-sample core node border", (259.369, 443.615, 347.245, 480.466), 22),
    obj("B06", "NODE_BORDER", "diag", "diagnostics core node border", (151.652, 443.615, 239.527, 480.466), 23),
    obj("B07", "NODE_BORDER", "correct", "correctness side node border", (85.745, 329.370, 158.030, 379.275), 29),
    obj("B08", "NODE_BORDER", "mix", "mixing-efficiency side node border", (448.584, 488.970, 520.869, 534.325), 30),
    obj("B09", "NODE_BORDER", "boundary", "correct-kernel-not-fast-mixing boundary", (195.589, 510.230, 411.025, 535.742), 34),
    obj("A01", "FLOW_ARROW", "joint_to_cond", "joint -> conditional", (242.555, 407.306, 257.531, 409.057), 24),
    obj("A02", "FLOW_ARROW", "cond_to_coord", "conditional -> coordinate kernel", (347.603, 407.306, 365.249, 409.057), 25),
    obj("A03", "FLOW_ARROW", "coord_to_scan", "coordinate kernel -> scan kernel", (410.150, 426.966, 411.900, 441.776), 26),
    obj("A04", "FLOW_ARROW", "scan_to_sample", "scan kernel -> correlated sample", (349.083, 461.165, 366.729, 462.916), 27),
    obj("A05", "FLOW_ARROW", "sample_to_diag", "correlated sample -> diagnostics", (241.365, 461.165, 259.011, 462.916), 28),
    obj("L01", "LEADER_LINE", "correct_to_joint", "non-directional correctness leader", (148.623, 379.548, 158.304, 389.398), 31),
    obj("L02", "LEADER_LINE", "mix_to_scan", "non-directional mixing-efficiency leader", (448.310, 480.824, 455.321, 488.696), 32),
]


def px_bbox(bbox):
    return tuple(int(round(v * SCALE)) for v in bbox)


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy) * SCALE


def bbox_intersection_area(a, b):
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0) * SCALE * SCALE


def save_crops(page_img):
    crops = {
        "figure_caption_native300dpi.png": (330, 1360, 2210, 2335),
        "figure_native1x.png": (330, 1360, 2210, 2238),
        "page_integration_native300dpi.png": (280, 1110, 2250, 3180),
        "roi_conditional_math_native1x.png": (1160, 1640, 1365, 1765),
        "roi_not_equal_native1x.png": (1215, 2145, 1305, 2210),
        "roi_correctness_bottom_clearance_native1x.png": (410, 1480, 665, 1605),
    }
    for name, box in crops.items():
        page_img.crop(box).save(ROOT / name)
    page_img.crop(crops["figure_caption_native300dpi.png"]).convert("L").save(ROOT / "grayscale_figure_caption_native300dpi.png")
    for stem in ("roi_conditional_math", "roi_not_equal", "roi_correctness_bottom_clearance"):
        im = Image.open(ROOT / f"{stem}_native1x.png")
        im.resize((im.width * 8, im.height * 8), resample=Image.Resampling.NEAREST).save(ROOT / f"{stem}_nearest8x.png")


def write_denominator_and_pairs():
    with (ROOT / "visible_object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = [
            "frozen_order", "object_id", "object_class", "parent_context", "description", "source_line",
            "bbox_pdf_x0", "bbox_pdf_y0", "bbox_pdf_x1", "bbox_pdf_y1",
            "bbox_px_x0", "bbox_px_y0", "bbox_px_x1", "bbox_px_y1",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, x in enumerate(OBJECTS, 1):
            b = x["bbox_pdf"]
            p = px_bbox(b)
            w.writerow({
                "frozen_order": i,
                "object_id": x["object_id"],
                "object_class": x["object_class"],
                "parent_context": x["parent_context"],
                "description": x["description"],
                "source_line": x["source_line"],
                "bbox_pdf_x0": f"{b[0]:.3f}", "bbox_pdf_y0": f"{b[1]:.3f}",
                "bbox_pdf_x1": f"{b[2]:.3f}", "bbox_pdf_y1": f"{b[3]:.3f}",
                "bbox_px_x0": p[0], "bbox_px_y0": p[1], "bbox_px_x1": p[2], "bbox_px_y1": p[3],
            })
    with (ROOT / "unordered_object_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = [
            "pair_id", "object_a", "class_a", "object_b", "class_b",
            "pair_class", "bbox_gap_px", "bbox_intersection_area_px2",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
            w.writerow({
                "pair_id": f"P{i:04d}",
                "object_a": a["object_id"], "class_a": a["object_class"],
                "object_b": b["object_id"], "class_b": b["object_class"],
                "pair_class": "--".join(sorted((a["object_class"], b["object_class"]))),
                "bbox_gap_px": f"{bbox_gap(a['bbox_pdf'], b['bbox_pdf']):.3f}",
                "bbox_intersection_area_px2": f"{bbox_intersection_area(a['bbox_pdf'], b['bbox_pdf']):.3f}",
            })


def draw_geometry_mask(size):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    for x in OBJECTS:
        oid = x["object_id"]
        b = px_bbox(x["bbox_pdf"])
        if x["object_class"] == "NODE_BORDER":
            width = 3 if oid not in {"B07", "B08"} else 2
            radius = 9
            d.rounded_rectangle(b, radius=radius, outline=255, width=width)
        elif x["object_class"] == "LEADER_LINE":
            if oid == "L01":
                d.line((b[0], b[1], b[2], b[3]), fill=255, width=2)
            else:
                d.line((b[2], b[1], b[0], b[3]), fill=255, width=2)
        elif x["object_class"] == "FLOW_ARROW":
            if oid in {"A01", "A02"}:
                cy = (b[1] + b[3]) // 2
                d.line((b[0], cy, b[2] - 8, cy), fill=255, width=4)
                d.polygon([(b[2], cy), (b[2] - 9, cy - 5), (b[2] - 9, cy + 5)], fill=255)
            elif oid == "A03":
                cx = (b[0] + b[2]) // 2
                d.line((cx, b[1], cx, b[3] - 8), fill=255, width=4)
                d.polygon([(cx, b[3]), (cx - 5, b[3] - 9), (cx + 5, b[3] - 9)], fill=255)
            else:
                cy = (b[1] + b[3]) // 2
                d.line((b[2], cy, b[0] + 8, cy), fill=255, width=4)
                d.polygon([(b[0], cy), (b[0] + 9, cy - 5), (b[0] + 9, cy + 5)], fill=255)
    return mask


def draw_text_mask(page_img):
    gray = np.asarray(page_img.convert("L"))
    mask = np.zeros(gray.shape, dtype=np.uint8)
    for x in OBJECTS:
        if not x["object_class"].startswith("TEXT") and x["object_class"] != "FORMULA":
            continue
        x0, y0, x1, y1 = px_bbox(x["bbox_pdf"])
        crop = gray[max(0, y0 - 2):min(gray.shape[0], y1 + 2), max(0, x0 - 2):min(gray.shape[1], x1 + 2)]
        bg = float(np.percentile(crop, 92))
        local = crop <= bg - 20.0
        mask[max(0, y0 - 2):min(gray.shape[0], y1 + 2), max(0, x0 - 2):min(gray.shape[1], x1 + 2)] |= local.astype(np.uint8) * 255
    return Image.fromarray(mask, mode="L")


def save_masks_and_overlay(page_img):
    text_mask = draw_text_mask(page_img)
    geom_mask = draw_geometry_mask(page_img.size)
    text_mask.save(ROOT / "mask_text_native300dpi.png")
    geom_mask.save(ROOT / "mask_geometry_native300dpi.png")
    base = page_img.convert("RGBA")
    red = Image.new("RGBA", base.size, (255, 0, 0, 0))
    red.putalpha(text_mask.point(lambda p: 120 if p else 0))
    blue = Image.new("RGBA", base.size, (0, 80, 255, 0))
    blue.putalpha(geom_mask.point(lambda p: 130 if p else 0))
    composed = Image.alpha_composite(Image.alpha_composite(base, red), blue)
    composed.crop((330, 1360, 2210, 2335)).save(ROOT / "semantic_mask_overlay_native300dpi.png")
    intersection = np.logical_and(np.asarray(text_mask) > 0, np.asarray(geom_mask) > 0)
    return int(intersection.sum())


def save_object_overlay(page_img):
    im = page_img.convert("RGBA")
    d = ImageDraw.Draw(im)
    colors = {
        "TEXT": (220, 30, 30, 255), "FORMULA": (220, 30, 30, 255), "TEXT_FORMULA": (220, 30, 30, 255),
        "NODE_BORDER": (20, 80, 230, 255), "FLOW_ARROW": (0, 150, 60, 255), "LEADER_LINE": (150, 60, 190, 255),
    }
    for x in OBJECTS:
        b = px_bbox(x["bbox_pdf"])
        color = colors[x["object_class"]]
        d.rectangle(b, outline=color, width=2)
        d.text((b[0] + 2, max(0, b[1] - 11)), x["object_id"], fill=color)
    im.crop((330, 1360, 2210, 2335)).save(ROOT / "overlay_all_objects_native300dpi.png")


def script_class(text, size):
    if size < 8.0:
        return "MATH_SCRIPT"
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "CJK_OR_MIXED"
    if any(ch in "π⋅∣≠−" or 0x1D400 <= ord(ch) <= 0x1D7FF for ch in text):
        return "MATH_BASE"
    if any(ch.isupper() or ch.isdigit() for ch in text):
        return "LATIN_CAP_DIGIT"
    return "PUNCT_OR_OTHER"


def span_ink_height(gray, bbox):
    x0, y0, x1, y1 = px_bbox(bbox)
    x0 = max(0, x0 - 1)
    y0 = max(0, y0 - 1)
    x1 = min(gray.shape[1], x1 + 1)
    y1 = min(gray.shape[0], y1 + 1)
    crop = gray[y0:y1, x0:x1]
    bg = float(np.percentile(crop, 92))
    fg = crop <= bg - 20.0
    rows = np.flatnonzero(fg.any(axis=1))
    return int(rows[-1] - rows[0] + 1) if rows.size else 0


def write_span_measurements(page_img):
    gray = np.asarray(page_img.convert("L"))
    page = fitz.open(PDF)[PAGE_NUMBER - 1]
    spans = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                b = tuple(float(v) for v in span["bbox"])
                if 325 <= b[1] <= 560 and b[2] > 70 and b[0] < 530:
                    spans.append((span, b))
    counters = {}
    rows = []
    text_objects = [x for x in OBJECTS if x["object_class"].startswith("TEXT") or x["object_class"] == "FORMULA"]
    for span, b in spans:
        overlaps = []
        for x in text_objects:
            area = bbox_intersection_area(b, x["bbox_pdf"])
            if area > 0:
                overlaps.append((area, x))
        if not overlaps:
            continue
        parent = max(overlaps, key=lambda z: z[0])[1]
        counters[parent["object_id"]] = counters.get(parent["object_id"], 0) + 1
        mid = f"{parent['object_id']}.S{counters[parent['object_id']]:02d}"
        p = px_bbox(b)
        rows.append({
            "measurement_id": mid,
            "parent_object_id": parent["object_id"],
            "text_sample": span["text"],
            "font_name": span["font"],
            "pdf_font_size_pt": f"{span['size']:.3f}",
            "graphics_scale": "1.000",
            "script_class": script_class(span["text"], span["size"]),
            "bbox_px_x0": p[0], "bbox_px_y0": p[1], "bbox_px_x1": p[2], "bbox_px_y1": p[3],
            "h_ink_px": span_ink_height(gray, b),
        })
    with (ROOT / "pixel_measurements_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["measurement_id", "parent_object_id", "text_sample", "font_name", "pdf_font_size_pt", "graphics_scale", "script_class", "bbox_px_x0", "bbox_px_y0", "bbox_px_x1", "bbox_px_y1", "h_ink_px"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    page_img = Image.open(ROOT / "full_page_native300dpi.png").convert("RGB")
    save_crops(page_img)
    write_denominator_and_pairs()
    save_object_overlay(page_img)
    intersection_count = save_masks_and_overlay(page_img)
    measurements = write_span_measurements(page_img)
    metrics = {
        "uid": "FIG-P630-01",
        "pdf_page_number": PAGE_NUMBER,
        "render_dpi": 300,
        "page_pixel_size": list(page_img.size),
        "visible_object_count": len(OBJECTS),
        "unordered_pair_count": len(OBJECTS) * (len(OBJECTS) - 1) // 2,
        "text_or_formula_object_count": sum(x["object_class"].startswith("TEXT") or x["object_class"] == "FORMULA" for x in OBJECTS),
        "geometry_object_count": sum(not (x["object_class"].startswith("TEXT") or x["object_class"] == "FORMULA") for x in OBJECTS),
        "machine_text_span_measurement_count": len(measurements),
        "text_geometry_mask_intersection_pixels": intersection_count,
        "crop_box_figure_caption_px": [330, 1360, 2210, 2335],
        "denominator_granularity": "reader-visible text line/run plus separately identifiable foreground geometry; math spans measured beneath parent objects",
    }
    (ROOT / "mechanical_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
