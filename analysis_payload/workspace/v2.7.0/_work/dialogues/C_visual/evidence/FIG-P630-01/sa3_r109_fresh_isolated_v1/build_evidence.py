from __future__ import annotations

import csv
import itertools
import math
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P630-01\sa3_r109_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf")
FULL_300 = ROOT / "r109_p680_full_native300dpi.png"
FULL_200 = ROOT / "r109_p680_full_200dpi.png"
PAGE_INDEX = 679
CROP_PT = (80.0, 318.0, 525.0, 558.0)


def font(size: int = 18):
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for item in candidates:
        if Path(item).exists():
            return ImageFont.truetype(item, size=size)
    return ImageFont.load_default()


def pbox(x0, y0, x1, y1):
    return (float(x0), float(y0), float(x1), float(y1))


OBJECTS = [
    ("O01", "correctness_callout", "NODE_COMPOSITE", pbox(85.745, 329.370, 158.030, 379.275)),
    ("O02", "joint_target_local_factors", "NODE_COMPOSITE", pbox(148.982, 389.756, 242.196, 426.607)),
    ("O03", "full_conditional", "NODE_COMPOSITE", pbox(259.369, 389.756, 347.245, 426.607)),
    ("O04", "single_coordinate_kernel", "NODE_COMPOSITE", pbox(367.087, 389.756, 454.963, 426.607)),
    ("O05", "scan_kernel", "NODE_COMPOSITE", pbox(367.087, 443.615, 454.963, 480.466)),
    ("O06", "correlated_samples", "NODE_COMPOSITE", pbox(259.369, 443.615, 347.245, 480.466)),
    ("O07", "diagnostics", "NODE_COMPOSITE", pbox(151.652, 443.615, 239.527, 480.466)),
    ("O08", "mixing_efficiency_callout", "NODE_COMPOSITE", pbox(448.584, 488.970, 520.869, 534.325)),
    ("O09", "correct_kernel_not_fast_mixing", "NODE_COMPOSITE", pbox(195.589, 510.230, 411.025, 535.742)),
    ("O10", "flow_joint_to_conditional", "LINE_ARROW", pbox(242.555, 407.306, 257.531, 409.057)),
    ("O11", "flow_conditional_to_coordinate", "LINE_ARROW", pbox(347.603, 407.306, 365.249, 409.057)),
    ("O12", "flow_coordinate_to_scan", "LINE_ARROW", pbox(410.150, 426.966, 411.900, 441.776)),
    ("O13", "flow_scan_to_sample", "LINE_ARROW", pbox(349.083, 461.165, 366.729, 462.916)),
    ("O14", "flow_sample_to_diagnostics", "LINE_ARROW", pbox(241.365, 461.165, 259.011, 462.916)),
    ("O15", "leader_correctness_to_joint", "LEADER_LINE", pbox(148.623, 379.548, 158.304, 389.398)),
    ("O16", "leader_mixing_to_scan", "LEADER_LINE", pbox(448.310, 480.824, 455.321, 488.696)),
    ("O17", "figure_number_and_caption", "CAPTION", pbox(89.982, 538.896, 516.632, 553.322)),
]


TEXT = [
    ("T01", "correctness_line_1", "NODE_LABEL", 29, 9.6, 9.6, "正确性条件", "CJK_FULL", pbox(95.631, 332.972, 148.148, 343.215)),
    ("T02", "correctness_line_2", "NODE_LABEL", 29, 9.6, 9.6, "目标保持", "CJK_FULL", pbox(99.721, 344.528, 144.051, 354.771)),
    ("T03", "correctness_line_3", "NODE_LABEL", 29, 9.6, 9.6, "支持可达", "CJK_FULL", pbox(99.721, 356.085, 144.051, 366.328)),
    ("T04", "correctness_line_4", "NODE_LABEL", 29, 9.6, 9.6, "遍历性", "CJK_FULL", pbox(104.516, 367.642, 139.263, 377.885)),
    ("T05", "joint_label", "NODE_LABEL", 18, 9.6, 9.6, "联合目标 / 局部因子", "CJK_FULL", pbox(153.236, 404.165, 237.946, 414.408)),
    ("T06", "conditional_line_1", "NODE_LABEL", 19, 9.6, 9.6, "给定 x_{-j} 的满条件", "CJK_MATH", pbox(264.980, 397.077, 341.634, 408.329)),
    ("T07", "conditional_line_2", "FORMULA", 19, 9.6, 9.6, "pi_j(dot|x_{-j})", "MATH_BASE", pbox(282.080, 409.196, 324.534, 420.085)),
    ("T08", "coordinate_line_1", "NODE_LABEL", 20, 9.6, 9.6, "单坐标核 K_j", "CJK_MATH", pbox(385.484, 396.464, 435.846, 407.717)),
    ("T09", "coordinate_line_2", "NODE_LABEL", 20, 9.6, 9.6, "只更新 x_j", "CJK_MATH", pbox(390.845, 409.445, 430.485, 420.698)),
    ("T10", "scan_line_1", "NODE_LABEL", 21, 9.6, 9.6, "扫描核", "CJK_FULL", pbox(396.677, 452.145, 425.369, 462.388)),
    ("T11", "scan_line_2", "NODE_LABEL", 21, 9.6, 9.6, "系统 / 随机", "CJK_FULL", pbox(387.797, 463.901, 434.250, 474.144)),
    ("T12", "sample_label", "NODE_LABEL", 22, 9.6, 9.6, "相关样本", "CJK_FULL", pbox(284.179, 458.023, 322.436, 468.266)),
    ("T13", "diagnostic_line_1", "NODE_LABEL", 23, 9.6, 9.6, "诊断", "CJK_FULL", pbox(186.026, 452.145, 205.154, 462.388)),
    ("T14", "diagnostic_line_2", "NODE_LABEL", 23, 9.6, 9.6, "MCSE / ESS / 轨迹", "LATIN_CJK", pbox(157.128, 463.901, 234.052, 474.144)),
    ("T15", "mixing_line_1", "NODE_LABEL", 30, 9.6, 9.6, "混合效率", "CJK_FULL", pbox(462.555, 496.073, 506.885, 506.316)),
    ("T16", "mixing_line_2", "NODE_LABEL", 30, 9.6, 9.6, "自相关长度", "CJK_FULL", pbox(458.465, 507.629, 510.982, 517.872)),
    ("T17", "mixing_line_3", "NODE_LABEL", 30, 9.6, 9.6, "有效样本量", "CJK_FULL", pbox(458.465, 519.186, 510.982, 529.429)),
    ("T18", "boundary_label", "EMPHASIS_LABEL", 34, 10.0, 10.0, "正确内核 != 快速混合", "CJK_MATH", pbox(257.529, 515.014, 349.086, 529.440)),
    ("T19", "caption_number", "CAPTION", 37, 10.0, 9.963, "图 33.1", "CJK_LATIN", pbox(89.982, 538.896, 119.830, 553.322)),
    ("T20", "caption_text", "CAPTION", 37, 10.0, 9.963, "满条件...MCSE、ESS...相关样本", "CJK_LATIN", pbox(129.793, 542.483, 516.632, 553.153)),
    ("T21", "x_minus_j_subscript", "MATH_SCRIPT", 19, 9.6, 6.695, "-j", "MATH_SCRIPT", pbox(291.702, 401.635, 300.412, 408.329)),
    ("T22", "pi_j_first_subscript", "MATH_SCRIPT", 19, 9.6, 6.695, "j", "MATH_SCRIPT", pbox(288.143, 413.391, 291.497, 420.085)),
    ("T23", "pi_arg_minus_j_subscript", "MATH_SCRIPT", 19, 9.6, 6.695, "-j", "MATH_SCRIPT", pbox(311.693, 413.391, 320.403, 420.085)),
    ("T24", "K_j_subscript", "MATH_SCRIPT", 20, 9.6, 6.695, "j", "MATH_SCRIPT", pbox(432.492, 401.023, 435.846, 407.717)),
    ("T25", "x_j_subscript", "MATH_SCRIPT", 20, 9.6, 6.695, "j", "MATH_SCRIPT", pbox(427.131, 414.004, 430.485, 420.698)),
    ("T26", "not_equal_operator", "FORMULA", 34, 10.0, 9.963, "!=", "MATH_BASE", pbox(299.721, 518.979, 306.894, 528.942)),
]


ROIS = [
    ("R01", "x_minus_j", pbox(284.0, 394.0, 304.0, 411.0)),
    ("R02", "pi_full_conditional", pbox(278.0, 405.0, 329.0, 424.0)),
    ("R03", "K_j", pbox(422.0, 393.0, 440.0, 411.0)),
    ("R04", "x_j", pbox(418.0, 407.0, 434.0, 424.0)),
    ("R05", "upper_arrowheads", pbox(251.0, 402.0, 369.0, 414.0)),
    ("R06", "vertical_arrowhead", pbox(404.0, 433.0, 418.0, 446.0)),
    ("R07", "lower_arrowheads", pbox(237.0, 456.0, 355.0, 468.0)),
    ("R08", "correctness_leader", pbox(144.0, 375.0, 163.0, 394.0)),
    ("R09", "mixing_leader", pbox(444.0, 477.0, 459.0, 493.0)),
    ("R10", "not_equal", pbox(294.0, 513.0, 312.0, 533.0)),
]


def bbox_distance(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy)


def pt_to_px(box, sx, sy):
    x0, y0, x1, y1 = box
    return (
        int(math.floor(x0 * sx)),
        int(math.floor(y0 * sy)),
        int(math.ceil(x1 * sx)),
        int(math.ceil(y1 * sy)),
    )


def modal_rgb(arr):
    pixels = arr.reshape(-1, arr.shape[-1])[:, :3]
    q = (pixels // 4) * 4
    key, _ = Counter(map(tuple, q.tolist())).most_common(1)[0]
    return np.array(key, dtype=np.int16)


def ink_measure(image, box_px):
    x0, y0, x1, y1 = box_px
    arr = np.asarray(image.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.int16)
    bg = modal_rgb(arr)
    delta = np.max(np.abs(arr[:, :, :3] - bg), axis=2)
    mask = delta >= 20
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if not len(rows) or not len(cols):
        return 0, 0, 0, tuple(map(int, bg)), (0, 0, 0, 0)
    global_box = (x0 + int(cols[0]), y0 + int(rows[0]), x0 + int(cols[-1]) + 1, y0 + int(rows[-1]) + 1)
    return int(rows[-1] - rows[0] + 1), int(cols[-1] - cols[0] + 1), int(mask.sum()), tuple(map(int, bg)), global_box


def save_contact(items, out_path, upscale=1):
    label_font = font(20)
    prepared = []
    for rid, name, tile in items:
        if upscale != 1:
            tile = tile.resize((tile.width * upscale, tile.height * upscale), Image.Resampling.NEAREST)
        prepared.append((rid, name, tile))
    cell_w = max(tile.width for _, _, tile in prepared) + 24
    cell_h = max(tile.height for _, _, tile in prepared) + 58
    cols = 2 if upscale == 8 else 5
    rows = math.ceil(len(prepared) / cols)
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (rid, name, tile) in enumerate(prepared):
        col, row = i % cols, i // cols
        ox, oy = col * cell_w + 12, row * cell_h + 42
        sheet.paste(tile, (ox, oy))
        draw.text((ox, row * cell_h + 10), f"{rid} {name} {'8x NN' if upscale == 8 else 'native1x'}", fill="black", font=label_font)
        draw.rectangle((ox - 1, oy - 1, ox + tile.width, oy + tile.height), outline=(100, 100, 100), width=1)
    sheet.save(out_path)


def main():
    ROOT.mkdir(parents=False, exist_ok=True)
    full300 = Image.open(FULL_300).convert("RGB")
    full200 = Image.open(FULL_200).convert("RGB")
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx300 = full300.width / page.rect.width
    sy300 = full300.height / page.rect.height
    sx200 = full200.width / page.rect.width
    sy200 = full200.height / page.rect.height
    crop_px = pt_to_px(CROP_PT, sx300, sy300)
    crop = full300.crop(crop_px)
    crop.save(ROOT / "r109_p680_figure_caption_native300dpi.png")
    crop.convert("L").save(ROOT / "r109_p680_figure_caption_grayscale_native300dpi.png")

    integration = full200.copy()
    integration_draw = ImageDraw.Draw(integration)
    integration_draw.rectangle(pt_to_px(CROP_PT, sx200, sy200), outline=(220, 0, 0), width=4)
    integration_draw.text((pt_to_px(CROP_PT, sx200, sy200)[0], pt_to_px(CROP_PT, sx200, sy200)[1] - 28), "FIG-P630-01 figure+caption review region", fill=(180, 0, 0), font=font(20))
    integration.save(ROOT / "r109_p680_page_integration_overlay_200dpi.png")

    overlay = crop.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")
    palette = {
        "NODE_COMPOSITE": (0, 120, 255, 210),
        "LINE_ARROW": (220, 0, 0, 230),
        "LEADER_LINE": (150, 0, 190, 230),
        "CAPTION": (0, 150, 70, 230),
    }
    cpx0, cpy0, _, _ = crop_px
    for oid, name, kind, box in OBJECTS:
        px = pt_to_px(box, sx300, sy300)
        local = (px[0] - cpx0, px[1] - cpy0, px[2] - cpx0, px[3] - cpy0)
        color = palette[kind]
        draw.rectangle(local, outline=color, width=4)
        draw.rectangle((local[0], local[1], local[0] + 52, local[1] + 26), fill=(255, 255, 255, 215))
        draw.text((local[0] + 2, local[1] + 2), oid, fill=color, font=font(18))
    overlay.save(ROOT / "r109_p680_semantic_object_overlay_native300dpi.png")

    text_overlay = crop.copy()
    text_draw = ImageDraw.Draw(text_overlay, "RGBA")
    for tid, name, role, source_line, declared, effective, sample, script, box in TEXT:
        px = pt_to_px(box, sx300, sy300)
        local = (px[0] - cpx0, px[1] - cpy0, px[2] - cpx0, px[3] - cpy0)
        text_draw.rectangle(local, outline=(235, 0, 160, 220), width=2)
        text_draw.text((local[0], max(0, local[1] - 20)), tid, fill=(160, 0, 110, 255), font=font(14))
    text_overlay.save(ROOT / "r109_p680_text_measurement_overlay_native300dpi.png")

    with (ROOT / "machine_visible_object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["OBJECT_ID", "NAME", "SEMANTIC_CLASS", "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT"])
        for oid, name, kind, box in OBJECTS:
            w.writerow([oid, name, kind, *[f"{v:.3f}" for v in box]])

    with (ROOT / "machine_unordered_pair_geometry.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B", "BBOX_DISTANCE_PT", "BBOX_DISTANCE_NATIVE300_PX"])
        for idx, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
            dist = bbox_distance(a[3], b[3])
            w.writerow([f"P{idx:03d}", a[0], b[0], f"{dist:.3f}", f"{dist * min(sx300, sy300):.2f}"])

    with (ROOT / "machine_text_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "ELEMENT_ID", "NAME", "ROLE", "SOURCE_LINE", "DECLARED_PT", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS",
            "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT", "H_INK_PX", "W_INK_PX", "INK_PIXEL_COUNT", "MODAL_BACKGROUND_RGB",
            "INK_X0_PX", "INK_Y0_PX", "INK_X1_PX", "INK_Y1_PX",
        ])
        for item in TEXT:
            tid, name, role, source_line, declared, effective, sample, script, box = item
            h, width, count, bg, ink_box = ink_measure(full300, pt_to_px(box, sx300, sy300))
            w.writerow([tid, name, role, source_line, declared, effective, sample, script, *[f"{v:.3f}" for v in box], h, width, count, str(bg), *ink_box])

    roi_items = []
    for rid, name, box in ROIS:
        tile = full300.crop(pt_to_px(box, sx300, sy300))
        roi_items.append((rid, name, tile))
    save_contact(roi_items, ROOT / "r109_p680_critical_rois_native1x.png", upscale=1)
    save_contact(roi_items, ROOT / "r109_p680_critical_rois_nearest8x.png", upscale=8)

    print(f"page={PAGE_INDEX + 1}")
    print(f"page_size_pt={page.rect.width:.3f}x{page.rect.height:.3f}")
    print(f"native300={full300.width}x{full300.height}; scale={sx300:.6f},{sy300:.6f}")
    print(f"crop_px={crop_px}; crop_size={crop.width}x{crop.height}")
    print(f"visible_objects={len(OBJECTS)}; unordered_pairs={len(OBJECTS) * (len(OBJECTS) - 1) // 2}")
    print(f"text_measurements={len(TEXT)}; critical_rois={len(ROIS)}")


if __name__ == "__main__":
    main()
