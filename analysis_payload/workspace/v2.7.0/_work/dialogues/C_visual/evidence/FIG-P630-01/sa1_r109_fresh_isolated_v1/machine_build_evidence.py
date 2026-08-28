from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P630-01\sa1_r109_fresh_isolated_v1")
PAGE_PATH = ROOT / "full_page_300dpi.png"
SCALE = 300.0 / 72.0


def pt_box(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


page = Image.open(PAGE_PATH).convert("RGB")
page_np = np.asarray(page)

# Native 300 dpi / 1x evidence. Coordinates derive from physical PDF page 680.
figure_box_px = (300, 1350, 2230, 2255)
figure_caption_box_px = (300, 1330, 2230, 2365)
figure = page.crop(figure_box_px)
figure_caption = page.crop(figure_caption_box_px)
figure.save(ROOT / "figure_crop_native300dpi_1x.png")
figure_caption.save(ROOT / "figure_caption_native300dpi_1x.png")
figure.convert("L").save(ROOT / "figure_crop_grayscale_native300dpi_1x.png")

roi_boxes = {
    "roi_cond_formula_nearest8x.png": (1010, 1600, 1485, 1795),
    "roi_main_arrows_nearest8x.png": (970, 1615, 1580, 1800),
    "roi_side_leaders_nearest8x.png": (350, 1360, 2230, 2260),
    "roi_boundary_caption_nearest8x.png": (780, 2100, 2230, 2365),
}
for name, box in roi_boxes.items():
    roi = page.crop(box)
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(ROOT / name)

# Reader-visible text denominator. Boxes are Poppler/pdfplumber word geometry in PDF points.
text_elements = [
    dict(object_id="T01", role="core_node_text", source_line=18, text_sample="联合目标 / 局部因子", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(153.236, 404.528, 237.946, 414.408), parent="B01"),
    dict(object_id="T02", role="core_node_text", source_line=19, text_sample="给定 x_{-j} 的满条件", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(264.980, 397.440, 341.634, 408.329), parent="B02"),
    dict(object_id="T03", role="formula_block", source_line=19, text_sample="π_j(·|x_{-j})", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(282.080, 409.196, 324.534, 420.085), parent="B02"),
    dict(object_id="T04", role="core_node_text", source_line=20, text_sample="单坐标核 K_j", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(385.484, 396.827, 435.846, 407.717), parent="B03"),
    dict(object_id="T05", role="core_node_text", source_line=20, text_sample="只更新 x_j", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(390.845, 409.808, 430.485, 420.698), parent="B03"),
    dict(object_id="T06", role="core_node_text", source_line=21, text_sample="扫描核", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(396.677, 452.824, 425.369, 462.388), parent="B04"),
    dict(object_id="T07", role="core_node_text", source_line=21, text_sample="系统 / 随机", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(387.797, 464.264, 434.250, 474.144), parent="B04"),
    dict(object_id="T08", role="core_node_text", source_line=22, text_sample="相关样本", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(284.179, 458.702, 322.436, 468.266), parent="B05"),
    dict(object_id="T09", role="core_node_text", source_line=23, text_sample="诊断", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(186.026, 452.824, 205.154, 462.388), parent="B06"),
    dict(object_id="T10", role="core_node_text", source_line=23, text_sample="MCSE / ESS / 轨迹", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(157.128, 464.264, 234.052, 474.144), parent="B06"),
    dict(object_id="T11", role="side_node_text", source_line=29, text_sample="正确性条件", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(95.631, 333.651, 148.148, 343.215), parent="B07"),
    dict(object_id="T12", role="side_node_text", source_line=29, text_sample="目标保持", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(99.721, 345.207, 144.051, 354.771), parent="B07"),
    dict(object_id="T13", role="side_node_text", source_line=29, text_sample="支持可达", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(99.721, 356.764, 144.051, 366.328), parent="B07"),
    dict(object_id="T14", role="side_node_text", source_line=29, text_sample="遍历性", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(104.516, 368.321, 139.263, 377.885), parent="B07"),
    dict(object_id="T15", role="side_node_text", source_line=30, text_sample="混合效率", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(462.555, 496.752, 506.885, 506.316), parent="B08"),
    dict(object_id="T16", role="side_node_text", source_line=30, text_sample="自相关长度", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(458.465, 508.308, 510.982, 517.872), parent="B08"),
    dict(object_id="T17", role="side_node_text", source_line=30, text_sample="有效样本量", declared_pt=9.6, graphics_scale=1.0, effective_pt=9.6, pdf_font_size_bp=9.564, box=(458.465, 519.865, 510.982, 529.429), parent="B08"),
    dict(object_id="T18", role="boundary_statement", source_line=34, text_sample="正确内核 ≠ 快速混合", declared_pt=10.0, graphics_scale=1.0, effective_pt=10.0, pdf_font_size_bp=9.963, box=(257.529, 518.979, 349.086, 529.440), parent="B09"),
    dict(object_id="T19", role="caption_label", source_line=37, text_sample="图 33.1", declared_pt=10.0, graphics_scale=1.0, effective_pt=10.0, pdf_font_size_bp=9.963, box=(89.982, 542.861, 119.830, 553.322), parent="PAGE"),
    dict(object_id="T20", role="caption_text", source_line=37, text_sample="满条件把联合目标转为单坐标更新，扫描后得到需以 MCSE、ESS 与轨迹诊断的相关样本", declared_pt=10.0, graphics_scale=1.0, effective_pt=10.0, pdf_font_size_bp=9.963, box=(129.793, 542.861, 516.632, 553.153), parent="PAGE"),
]

# Source-derived node border geometry in PDF points. Core centers are separated by 3.8 cm horizontally
# and 1.9 cm vertically; stated minimum sizes are used because rendered contents do not enlarge them.
cx = 303.257
top_y = 408.943
lower_y = top_y + 53.858
core_w = 31.0 * 72.0 / 25.4
core_h = 13.0 * 72.0 / 25.4
side_w = 22.5 * 72.0 / 25.4 + 2.0 * 1.5 * 72.0 / 25.4
side_h = 16.0 * 72.0 / 25.4
boundary_w = 76.0 * 72.0 / 25.4
boundary_h = 9.0 * 72.0 / 25.4
joint_w = max(core_w, (237.946 - 153.236) + 2.0 * 1.5 * 72.0 / 25.4)
correct_h = max(side_h, (377.885 - 333.651) + 2.0 * 1.0 * 72.0 / 25.4)


def centered_box(x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    return (x - w / 2.0, y - h / 2.0, x + w / 2.0, y + h / 2.0)


objects = []
node_specs = [
    ("B01", "core_node_border", centered_box(cx - 3.8 * 72.0 / 2.54, top_y, joint_w, core_h), "joint"),
    ("B02", "core_node_border", centered_box(cx, top_y, core_w, core_h), "cond"),
    ("B03", "core_node_border", centered_box(cx + 3.8 * 72.0 / 2.54, top_y, core_w, core_h), "coord"),
    ("B04", "core_node_border", centered_box(cx + 3.8 * 72.0 / 2.54, lower_y, core_w, core_h), "scan"),
    ("B05", "core_node_border", centered_box(cx, lower_y, core_w, core_h), "sample"),
    ("B06", "core_node_border", centered_box(cx - 3.8 * 72.0 / 2.54, lower_y, core_w, core_h), "diag"),
    ("B07", "side_node_border", centered_box(cx - 6.4 * 72.0 / 2.54, top_y - 1.9 * 72.0 / 2.54, side_w, correct_h), "correct"),
    ("B08", "side_node_border", centered_box(cx + 6.4 * 72.0 / 2.54, top_y + 3.65 * 72.0 / 2.54, side_w, side_h), "mix"),
    ("B09", "boundary_node_border", centered_box(cx, top_y + 4.05 * 72.0 / 2.54, boundary_w, boundary_h), "boundary"),
]
for oid, kind, box, label in node_specs:
    objects.append(dict(object_id=oid, object_class=kind, source_line={"joint":18,"cond":19,"coord":20,"scan":21,"sample":22,"diag":23,"correct":29,"mix":30,"boundary":34}[label], semantic_label=label, box=box))

node_map = {x[0]: x[2] for x in node_specs}


def midpoint(box: tuple[float, float, float, float], side: str) -> tuple[float, float]:
    x0, y0, x1, y1 = box
    return {
        "east": (x1, (y0 + y1) / 2),
        "west": (x0, (y0 + y1) / 2),
        "north": ((x0 + x1) / 2, y0),
        "south": ((x0 + x1) / 2, y1),
        "nw": (x0, y0),
        "se": (x1, y1),
    }[side]


edge_specs = [
    ("F01", "flow_arrow", 24, "joint_to_cond", midpoint(node_map["B01"], "east"), midpoint(node_map["B02"], "west")),
    ("F02", "flow_arrow", 25, "cond_to_coord", midpoint(node_map["B02"], "east"), midpoint(node_map["B03"], "west")),
    ("F03", "flow_arrow", 26, "coord_to_scan", midpoint(node_map["B03"], "south"), midpoint(node_map["B04"], "north")),
    ("F04", "flow_arrow", 27, "scan_to_sample", midpoint(node_map["B04"], "west"), midpoint(node_map["B05"], "east")),
    ("F05", "flow_arrow", 28, "sample_to_diag", midpoint(node_map["B05"], "west"), midpoint(node_map["B06"], "east")),
    ("L01", "leader_line", 31, "correct_to_joint", midpoint(node_map["B07"], "se"), midpoint(node_map["B01"], "nw")),
    ("L02", "leader_line", 32, "mix_to_scan", midpoint(node_map["B08"], "nw"), midpoint(node_map["B04"], "se")),
]
for oid, kind, line, label, p0, p1 in edge_specs:
    pad = 2.5 if kind == "flow_arrow" else 1.5
    box = (min(p0[0], p1[0]) - pad, min(p0[1], p1[1]) - pad, max(p0[0], p1[0]) + pad, max(p0[1], p1[1]) + pad)
    objects.append(dict(object_id=oid, object_class=kind, source_line=line, semantic_label=label, box=box))

for t in text_elements:
    objects.append(dict(object_id=t["object_id"], object_class="text", source_line=t["source_line"], semantic_label=t["text_sample"], box=t["box"]))

# Machine-only pixel measurements. Extra nested rows measure legal TeX scripts without adding them
# to the disjoint visible-object denominator.
measurements = [dict(t) for t in text_elements]
script_measurements = [
    dict(object_id="M01S", parent="T02", role="legal_tex_script", source_line=19, text_sample="−j in x_{−j}", declared_pt=9.6, graphics_scale=1.0, effective_pt=6.72, pdf_font_size_bp=6.695, box=(291.702, 401.635, 300.412, 408.329), tex_script_level=1),
    dict(object_id="M02S", parent="T03", role="legal_tex_script", source_line=19, text_sample="j in π_j", declared_pt=9.6, graphics_scale=1.0, effective_pt=6.72, pdf_font_size_bp=6.695, box=(288.143, 413.391, 291.497, 420.085), tex_script_level=1),
    dict(object_id="M03S", parent="T03", role="legal_tex_script", source_line=19, text_sample="−j in x_{−j}", declared_pt=9.6, graphics_scale=1.0, effective_pt=6.72, pdf_font_size_bp=6.695, box=(311.693, 413.391, 320.403, 420.085), tex_script_level=1),
    dict(object_id="M04S", parent="T04", role="legal_tex_script", source_line=20, text_sample="j in K_j", declared_pt=9.6, graphics_scale=1.0, effective_pt=6.72, pdf_font_size_bp=6.695, box=(432.492, 401.023, 435.846, 407.717), tex_script_level=1),
    dict(object_id="M05S", parent="T05", role="legal_tex_script", source_line=20, text_sample="j in x_j", declared_pt=9.6, graphics_scale=1.0, effective_pt=6.72, pdf_font_size_bp=6.695, box=(427.131, 414.004, 430.485, 420.698), tex_script_level=1),
]
for m in measurements:
    m["tex_script_level"] = 0
measurements.extend(script_measurements)


def ink_metrics(box_pt: tuple[float, float, float, float]) -> tuple[int, int, tuple[int, int, int], tuple[int, int, int, int]]:
    x0, y0, x1, y1 = pt_box(box_pt)
    crop = page_np[max(0, y0):min(page_np.shape[0], y1), max(0, x0):min(page_np.shape[1], x1)]
    colors, counts = np.unique(crop.reshape(-1, 3), axis=0, return_counts=True)
    bg = colors[int(np.argmax(counts))].astype(np.int16)
    delta = np.max(np.abs(crop.astype(np.int16) - bg), axis=2)
    mask = delta >= 20
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return 0, 0, tuple(int(v) for v in bg), (x0, y0, x0, y0)
    ink_box = (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)
    return int(ys.max() - ys.min() + 1), int(mask.sum()), tuple(int(v) for v in bg), ink_box


measurement_rows = []
for m in measurements:
    h, ink_count, bg, ink_box = ink_metrics(m["box"])
    x0, y0, x1, y1 = pt_box(m["box"])
    measurement_rows.append({
        "measurement_id": m["object_id"],
        "parent_object_id": m["parent"],
        "role": m["role"],
        "source_line": m["source_line"],
        "text_sample": m["text_sample"],
        "declared_pt": f"{m['declared_pt']:.2f}",
        "graphics_scale": f"{m['graphics_scale']:.3f}",
        "effective_pt": f"{m['effective_pt']:.2f}",
        "pdf_font_size_bp": f"{m['pdf_font_size_bp']:.3f}",
        "tex_script_level": m["tex_script_level"],
        "bbox_x0_px": x0,
        "bbox_y0_px": y0,
        "bbox_x1_px": x1,
        "bbox_y1_px": y1,
        "h_ink_px": h,
        "ink_pixel_count": ink_count,
        "ink_bbox_x0_px": ink_box[0],
        "ink_bbox_y0_px": ink_box[1],
        "ink_bbox_x1_px": ink_box[2],
        "ink_bbox_y1_px": ink_box[3],
        "background_rgb": "/".join(str(v) for v in bg),
    })

measurement_fields = list(measurement_rows[0].keys())
write_csv(ROOT / "pixel_measurements_machine.csv", measurement_fields, measurement_rows)

text_ink_rows = []
primary = [r for r in measurement_rows if r["measurement_id"].startswith("T")]
for i, a in enumerate(primary):
    for b in primary[i + 1:]:
        dx = max(0, max(a["ink_bbox_x0_px"], b["ink_bbox_x0_px"]) - min(a["ink_bbox_x1_px"], b["ink_bbox_x1_px"]))
        dy = max(0, max(a["ink_bbox_y0_px"], b["ink_bbox_y0_px"]) - min(a["ink_bbox_y1_px"], b["ink_bbox_y1_px"]))
        ix = max(0, min(a["ink_bbox_x1_px"], b["ink_bbox_x1_px"]) - max(a["ink_bbox_x0_px"], b["ink_bbox_x0_px"]))
        iy = max(0, min(a["ink_bbox_y1_px"], b["ink_bbox_y1_px"]) - max(a["ink_bbox_y0_px"], b["ink_bbox_y0_px"]))
        text_ink_rows.append({
            "pair_id": f"TI{len(text_ink_rows)+1:03d}",
            "text_a": a["measurement_id"],
            "text_b": b["measurement_id"],
            "machine_ink_bbox_intersection_area_px": ix * iy,
            "machine_ink_bbox_gap_px": int(round(math.hypot(dx, dy))),
        })
write_csv(ROOT / "text_ink_pair_clearance_machine.csv", list(text_ink_rows[0].keys()), text_ink_rows)

text_rows = []
for t in text_elements:
    x0, y0, x1, y1 = pt_box(t["box"])
    text_rows.append({
        "object_id": t["object_id"],
        "object_class": "text",
        "role": t["role"],
        "parent_object_id": t["parent"],
        "source_line": t["source_line"],
        "text_sample": t["text_sample"],
        "declared_pt": f"{t['declared_pt']:.2f}",
        "graphics_scale": f"{t['graphics_scale']:.3f}",
        "effective_pt": f"{t['effective_pt']:.2f}",
        "bbox_x0_px": x0,
        "bbox_y0_px": y0,
        "bbox_x1_px": x1,
        "bbox_y1_px": y1,
    })
write_csv(ROOT / "visible_text_denominator.csv", list(text_rows[0].keys()), text_rows)

object_rows = []
for o in objects:
    x0, y0, x1, y1 = pt_box(o["box"])
    object_rows.append({
        "object_id": o["object_id"],
        "object_class": o["object_class"],
        "source_line": o["source_line"],
        "semantic_label": o["semantic_label"],
        "bbox_x0_px": x0,
        "bbox_y0_px": y0,
        "bbox_x1_px": x1,
        "bbox_y1_px": y1,
    })
write_csv(ROOT / "visible_object_denominator.csv", list(object_rows[0].keys()), object_rows)

pair_rows = []
for i, a in enumerate(object_rows):
    for b in object_rows[i + 1:]:
        ix = max(0, min(a["bbox_x1_px"], b["bbox_x1_px"]) - max(a["bbox_x0_px"], b["bbox_x0_px"]))
        iy = max(0, min(a["bbox_y1_px"], b["bbox_y1_px"]) - max(a["bbox_y0_px"], b["bbox_y0_px"]))
        dx = max(0, max(a["bbox_x0_px"], b["bbox_x0_px"]) - min(a["bbox_x1_px"], b["bbox_x1_px"]))
        dy = max(0, max(a["bbox_y0_px"], b["bbox_y0_px"]) - min(a["bbox_y1_px"], b["bbox_y1_px"]))
        pair_rows.append({
            "pair_id": f"P{len(pair_rows)+1:04d}",
            "object_a": a["object_id"],
            "class_a": a["object_class"],
            "object_b": b["object_id"],
            "class_b": b["object_class"],
            "machine_bbox_intersection_area_px": ix * iy,
            "machine_bbox_gap_px": int(round(math.hypot(dx, dy))),
        })
write_csv(ROOT / "unordered_object_pairs.csv", list(pair_rows[0].keys()), pair_rows)

# Source-coordinate text-to-parent-border clearances. Values are geometry, not review decisions.
clearance_rows = []
for t in text_elements:
    if t["parent"] not in node_map:
        continue
    tx0, ty0, tx1, ty1 = t["box"]
    bx0, by0, bx1, by1 = node_map[t["parent"]]
    distances = [(tx0 - bx0) * SCALE, (bx1 - tx1) * SCALE, (ty0 - by0) * SCALE, (by1 - ty1) * SCALE]
    clearance_rows.append({
        "text_object_id": t["object_id"],
        "border_object_id": t["parent"],
        "left_clearance_px": f"{distances[0]:.2f}",
        "right_clearance_px": f"{distances[1]:.2f}",
        "top_clearance_px": f"{distances[2]:.2f}",
        "bottom_clearance_px": f"{distances[3]:.2f}",
        "minimum_clearance_px": f"{min(distances):.2f}",
    })
write_csv(ROOT / "text_border_clearance_machine.csv", list(clearance_rows[0].keys()), clearance_rows)

# Object and semantic overlays remain native 300 dpi.
font = ImageFont.load_default()
text_overlay = page.copy()
draw = ImageDraw.Draw(text_overlay)
for t in text_elements:
    box = pt_box(t["box"])
    draw.rectangle(box, outline=(220, 0, 180), width=2)
    draw.rectangle((box[0], box[1] - 13, box[0] + 28, box[1]), fill=(255, 255, 255))
    draw.text((box[0] + 1, box[1] - 12), t["object_id"], fill=(160, 0, 130), font=font)
text_overlay.crop(figure_caption_box_px).save(ROOT / "text_measurement_overlay_native300dpi.png")

object_overlay = page.copy()
draw = ImageDraw.Draw(object_overlay)
colors = {
    "core_node_border": (0, 150, 0),
    "side_node_border": (255, 140, 0),
    "boundary_node_border": (210, 120, 0),
    "flow_arrow": (220, 0, 0),
    "leader_line": (140, 0, 220),
    "text": (0, 120, 220),
}
for o in objects:
    box = pt_box(o["box"])
    color = colors[o["object_class"]]
    draw.rectangle(box, outline=color, width=2)
    draw.text((box[0] + 2, box[1] + 2), o["object_id"], fill=color, font=font)
object_overlay.crop(figure_caption_box_px).save(ROOT / "object_overlay_native300dpi.png")

semantic = page.crop(figure_caption_box_px).convert("RGBA")
sem_draw = ImageDraw.Draw(semantic, "RGBA")
offset_x, offset_y = figure_caption_box_px[0], figure_caption_box_px[1]
for o in objects:
    if o["object_class"] == "text":
        continue
    box = pt_box(o["box"])
    local = (box[0] - offset_x, box[1] - offset_y, box[2] - offset_x, box[3] - offset_y)
    color = colors[o["object_class"]]
    sem_draw.rectangle(local, outline=(*color, 220), fill=(*color, 24), width=3)
semantic.convert("RGB").save(ROOT / "semantic_overlay_native300dpi.png")

summary = {
    "physical_pdf_page": 680,
    "printed_page": 667,
    "page_pixels_300dpi": list(page.size),
    "figure_crop_pixels": list(figure.size),
    "figure_caption_crop_pixels": list(figure_caption.size),
    "visible_text_element_count": len(text_elements),
    "visible_object_count": len(objects),
    "unordered_pair_count": len(pair_rows),
    "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
    "nested_script_measurement_count": len(script_measurements),
}
(ROOT / "machine_evidence_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

# Noncircular content manifest. MANIFEST.json cannot hash itself; WRITE_STOPPED must not exist yet
# and is explicitly excluded without a predicted size or hash.
manifest_entries = []
for path in sorted(ROOT.iterdir(), key=lambda p: p.name.casefold()):
    if not path.is_file() or path.name in {"MANIFEST.json", "WRITE_STOPPED"}:
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    manifest_entries.append({"path": path.name, "bytes": path.stat().st_size, "sha256": digest})
manifest = {
    "manifest_model": "noncircular_content_manifest_v1",
    "handoff_id": "C-FIG-P630-01-R109-SA1-FRESH-ISOLATED-V1",
    "root": str(ROOT),
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "entries": manifest_entries,
    "structural_exclusions": [
        {"path": "MANIFEST.json", "reason": "self-referential content hash excluded"},
        {"path": "WRITE_STOPPED", "reason": "must be created strictly last; no predicted size or hash"},
    ],
    "closure_rule": "After last-marker creation, actual root files must equal entries plus MANIFEST.json plus WRITE_STOPPED.",
}
(ROOT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
