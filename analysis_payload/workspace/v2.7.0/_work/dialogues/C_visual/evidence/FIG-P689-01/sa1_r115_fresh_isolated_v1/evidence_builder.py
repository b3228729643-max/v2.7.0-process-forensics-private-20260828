from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa1_r115_fresh_isolated_v1")
PAGE_PNG = ROOT / "full_page_300dpi.png"
CROP_PNG = ROOT / "figure_caption_native_300dpi.png"
SCALE = 300.0 / 72.0
CROP_X = 320
CROP_Y = 1320


# Fixed manually from the current PDF vector text spans. Bboxes are page PDF points.
# No verdict fields are emitted by this script.
ELEMENTS = [
    ("E01", "L", "TITLE", "证据的长度分解", (144.653, 331.272, 221.017, 347.069), "bold node; rendered 10.95pt", 10.95, "HAN"),
    ("E02", "L", "FORMULA_LABEL", "log p(w)", (168.440, 348.551, 202.899, 357.716), "9.2pt inherited", 9.20, "MATH_LATIN"),
    ("E03", "L", "BAR_LABEL", "L(q)：证据下界", (129.978, 379.219, 196.007, 389.035), "9.2pt inherited", 9.20, "MIXED"),
    ("E04", "L", "BAR_LABEL", "KL 间隙", (226.222, 379.728, 258.503, 389.544), "9.2pt inherited", 9.20, "MIXED"),
    ("E05", "L", "FORMULA_BLOCK", "log p(w)=L(q)+KL(q(h)||p(h|w))", (99.212, 408.164, 257.233, 417.631), "9.2pt inherited", 9.20, "MATH_LATIN"),
    ("E06", "L", "NOTE", "KL>=0，故 L(q)<=log p(w)；变分族受限", (99.212, 437.318, 266.462, 447.135), "9.2pt inherited", 9.20, "MIXED"),
    ("E07", "L", "NOTE", "时，间隙可保持为正。", (99.212, 448.278, 190.868, 458.094), "9.2pt inherited", 9.20, "HAN"),
    ("E08", "R", "TITLE", "坐标更新下的 ELBO 非降阶梯", (329.113, 331.272, 473.091, 347.069), "bold node; rendered 10.95pt", 10.95, "MIXED"),
    ("E09", "R", "ANNOTATION", "未知全局上限", (322.476, 359.501, 376.274, 369.104), "explicit 9.0pt", 9.00, "HAN"),
    ("E10", "R", "ANNOTATION", "坐标稳定／局部驻点", (394.575, 402.526, 475.272, 412.129), "explicit 9.0pt", 9.00, "HAN"),
    ("E11", "R", "AXIS_LABEL", "坐标更新轮次", (371.577, 459.585, 425.375, 469.188), "explicit 9.0pt", 9.00, "HAN"),
    ("E12", "R", "TICK", "0", (312.171, 444.378, 317.545, 453.643), "footnotesize; rendered 9.31pt", 9.31, "DIGIT"),
    ("E13", "R", "TICK", "1", (339.045, 444.359, 343.761, 453.624), "footnotesize; rendered 9.31pt", 9.31, "DIGIT"),
    ("E14", "R", "TICK", "2", (365.521, 444.396, 370.376, 453.661), "footnotesize; rendered 9.31pt", 9.31, "DIGIT"),
    ("E15", "R", "TICK", "3", (392.067, 444.396, 396.922, 453.661), "footnotesize; rendered 9.31pt", 9.31, "DIGIT"),
    ("E16", "R", "TICK", "4", (418.427, 444.387, 423.653, 453.652), "footnotesize; rendered 9.31pt", 9.31, "DIGIT"),
    ("E17", "R", "TICK", "5", (445.259, 444.257, 449.910, 453.522), "footnotesize; rendered 9.31pt", 9.31, "DIGIT"),
    ("E18", "R", "TICK", "6", (471.610, 444.405, 476.650, 453.670), "footnotesize; rendered 9.31pt", 9.31, "DIGIT"),
    ("E19", "C", "CAPTION_LABEL", "图 35.5", (76.138, 483.734, 107.435, 498.160), "caption label; rendered 10.0pt", 10.00, "MIXED"),
    ("E20", "C", "CAPTION", "观测对数证据等于 ELBO 与变分分布到真实后验的 KL 散度之和；平均场坐标更新可使", (117.398, 487.321, 507.793, 497.991), "caption; rendered 10.0pt", 10.00, "MIXED"),
    ("E21", "C", "CAPTION", "ELBO 逐步不降，但非凸目标下有限运行通常只得到坐标稳定点或局部驻点，多启动比较也不构成", (76.138, 500.711, 507.798, 511.381), "caption; rendered 10.0pt", 10.00, "MIXED"),
    ("E22", "C", "CAPTION", "全局最优证明", (76.138, 514.101, 135.914, 524.771), "caption; rendered 10.0pt", 10.00, "HAN"),
]


def page_px(bbox):
    return tuple(int(round(v * SCALE)) for v in bbox)


def crop_px(bbox):
    x0, y0, x1, y1 = page_px(bbox)
    return x0 - CROP_X, y0 - CROP_Y, x1 - CROP_X, y1 - CROP_Y


def bbox_metrics(a, b):
    ax0, ay0, ax1, ay1 = page_px(a)
    bx0, by0, bx1, by1 = page_px(b)
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    ix = max(0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0, min(ay1, by1) - max(ay0, by0))
    return dx, dy, math.hypot(dx, dy), ix * iy


def raw_ink_height(image_arr, bbox):
    x0, y0, x1, y1 = page_px(bbox)
    x0 = max(0, x0 - 1)
    y0 = max(0, y0 - 1)
    x1 = min(image_arr.shape[1], x1 + 2)
    y1 = min(image_arr.shape[0], y1 + 2)
    region = image_arr[y0:y1, x0:x1, :3].astype(np.int16)
    if region.size == 0:
        return 0, [255, 255, 255], 0
    border = np.concatenate((region[0], region[-1], region[:, 0], region[:, -1]), axis=0)
    bg = np.median(border, axis=0)
    diff = np.max(np.abs(region - bg), axis=2)
    mask = diff >= 20
    rows = np.where(mask.any(axis=1))[0]
    height = int(rows[-1] - rows[0] + 1) if len(rows) else 0
    return height, [int(round(v)) for v in bg], int(mask.sum())


def font():
    for candidate in (
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\consola.ttf"),
    ):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), 18)
    return ImageFont.load_default()


def add_box(draw, box, color, label, width=3, fill=None):
    draw.rectangle(box, outline=color, width=width, fill=fill)
    x0, y0, _, _ = box
    label_box = (x0, max(0, y0 - 20), x0 + 52, y0)
    draw.rectangle(label_box, fill=(255, 255, 255, 220), outline=color, width=1)
    draw.text((x0 + 2, max(0, y0 - 19)), label, font=font(), fill=color)


def write_indices_and_metrics():
    page = np.asarray(Image.open(PAGE_PNG).convert("RGB"))
    with (ROOT / "denominator.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ORDINAL", "ELEMENT_ID", "PANEL", "ROLE", "TEXT", "SOURCE_DECLARATION", "EFFECTIVE_PT_REFERENCE", "GRAPHICS_SCALE", "SCRIPT_CLASS", "BBOX_PAGE_PX"])
        for n, e in enumerate(ELEMENTS, 1):
            eid, panel, role, text, bbox, decl, eff, script = e
            w.writerow([n, eid, panel, role, text, decl, f"{eff:.2f}", "1.000", script, page_px(bbox)])
    with (ROOT / "pair_index.csv").open("w", encoding="utf-8", newline="") as f_idx, (ROOT / "raw_pair_geometry.csv").open("w", encoding="utf-8", newline="") as f_geo:
        wi = csv.writer(f_idx)
        wg = csv.writer(f_geo)
        wi.writerow(["PAIR_ID", "ELEMENT_A", "ELEMENT_B"])
        wg.writerow(["PAIR_ID", "ELEMENT_A", "ELEMENT_B", "BBOX_DX_GAP_PX", "BBOX_DY_GAP_PX", "BBOX_EUCLIDEAN_GAP_PX", "BBOX_INTERSECTION_AREA_PX2"])
        k = 0
        for i in range(len(ELEMENTS)):
            for j in range(i + 1, len(ELEMENTS)):
                k += 1
                a = ELEMENTS[i]
                b = ELEMENTS[j]
                pid = f"P{k:03d}"
                wi.writerow([pid, a[0], b[0]])
                dx, dy, dist, area = bbox_metrics(a[4], b[4])
                wg.writerow([pid, a[0], b[0], dx, dy, f"{dist:.3f}", area])
        if k != 231:
            raise RuntimeError(f"pair count mismatch: {k}")
    with (ROOT / "raw_text_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ELEMENT_ID", "PANEL", "ROLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "RAW_H_INK_PX", "RAW_FOREGROUND_PIXEL_COUNT", "ESTIMATED_LOCAL_BG_RGB"])
        for e in ELEMENTS:
            eid, panel, role, _, bbox, _, _, script = e
            bb = page_px(bbox)
            h, bg, count = raw_ink_height(page, bbox)
            w.writerow([eid, panel, role, script, *bb, h, count, json.dumps(bg)])


def write_overlays_and_rois():
    base = Image.open(CROP_PNG).convert("RGBA")
    text_img = base.copy()
    text_draw = ImageDraw.Draw(text_img, "RGBA")
    role_colors = {
        "TITLE": (191, 35, 40, 255),
        "FORMULA_LABEL": (26, 91, 171, 255),
        "BAR_LABEL": (26, 91, 171, 255),
        "FORMULA_BLOCK": (26, 91, 171, 255),
        "NOTE": (34, 139, 34, 255),
        "ANNOTATION": (217, 95, 14, 255),
        "AXIS_LABEL": (125, 60, 152, 255),
        "TICK": (125, 60, 152, 255),
        "CAPTION_LABEL": (186, 85, 211, 255),
        "CAPTION": (186, 85, 211, 255),
    }
    for e in ELEMENTS:
        eid, _, role, _, bbox, *_ = e
        add_box(text_draw, crop_px(bbox), role_colors[role], eid)
    text_img.convert("RGB").save(ROOT / "text_measurement_overlay_300dpi.png")

    objects = [
        ("O01 LEFT_PANEL_BORDER", (45, 56, 838, 684), (100, 100, 100, 255)),
        ("O02 RIGHT_PANEL_BORDER", (955, 56, 1748, 684), (100, 100, 100, 255)),
        ("O03 TOTAL_ARROW", (120, 143, 785, 222), (230, 120, 20, 255)),
        ("O04 ELBO_KL_BAR", (120, 230, 785, 325), (0, 130, 180, 255)),
        ("O05 IDENTITY", (90, 365, 805, 430), (0, 95, 180, 255)),
        ("O06 NONNEG_NOTE", (88, 490, 805, 558), (20, 150, 80, 255)),
        ("O07 AXIS_AND_TICKS", (987, 105, 1693, 574), (135, 80, 170, 255)),
        ("O08 UNKNOWN_UPPER", (988, 138, 1682, 226), (230, 120, 20, 255)),
        ("O09 STAIRCASE_MARKS", (984, 217, 1670, 500), (0, 145, 125, 255)),
        ("O10 LOCAL_POINT_NOTE", (1314, 348, 1669, 409), (200, 45, 45, 255)),
        ("O11 CAPTION", (0, 690, 1838, 878), (186, 85, 211, 255)),
    ]
    obj_img = base.copy()
    obj_draw = ImageDraw.Draw(obj_img, "RGBA")
    for label, box, color in objects:
        add_box(obj_draw, box, color, label.split()[0])
    obj_img.convert("RGB").save(ROOT / "object_overlay_300dpi.png")

    sem_img = base.copy()
    sem_draw = ImageDraw.Draw(sem_img, "RGBA")
    category_color = {
        "TEXT": (0, 145, 80, 255),
        "FORMULA": (30, 90, 210, 255),
        "TICK": (125, 60, 152, 255),
        "CAPTION": (186, 85, 211, 255),
    }
    for e in ELEMENTS:
        eid, _, role, _, bbox, *_ = e
        if role in {"FORMULA_LABEL", "FORMULA_BLOCK", "BAR_LABEL"}:
            cat = "FORMULA"
        elif role == "TICK":
            cat = "TICK"
        elif role.startswith("CAPTION"):
            cat = "CAPTION"
        else:
            cat = "TEXT"
        box = crop_px(bbox)
        sem_draw.rectangle(box, outline=category_color[cat], width=3)
    sem_draw.rectangle((45, 56, 838, 684), outline=(100, 100, 100, 255), width=4)
    sem_draw.rectangle((955, 56, 1748, 684), outline=(100, 100, 100, 255), width=4)
    sem_draw.line([(120, 205), (785, 205)], fill=(230, 120, 20, 255), width=5)
    sem_draw.rectangle((120, 230, 785, 325), outline=(0, 130, 180, 255), width=4)
    sem_draw.rectangle((988, 138, 1682, 226), outline=(230, 120, 20, 255), width=4)
    sem_draw.rectangle((984, 217, 1670, 500), outline=(0, 145, 125, 255), width=4)
    legend = [
        ("TEXT", (0, 145, 80, 255)),
        ("FORMULA", (30, 90, 210, 255)),
        ("TICK", (125, 60, 152, 255)),
        ("CAPTION", (186, 85, 211, 255)),
        ("LINE/ARROW", (230, 120, 20, 255)),
        ("CURVE/MARKER", (0, 145, 125, 255)),
        ("PANEL BORDER", (100, 100, 100, 255)),
    ]
    lx, ly = 5, 5
    for label, color in legend:
        sem_draw.rectangle((lx, ly, lx + 18, ly + 18), fill=color)
        sem_draw.text((lx + 23, ly), label, font=font(), fill=(0, 0, 0, 255))
        ly += 23
    sem_img.convert("RGB").save(ROOT / "semantic_overlay_300dpi.png")

    rois = {
        "A_left_total": (105, 45, 810, 226),
        "B_left_bar": (105, 220, 805, 338),
        "C_left_identity": (75, 355, 815, 438),
        "D_left_nonneg_note": (75, 480, 815, 610),
        "E_right_title_upper": (970, 45, 1725, 232),
        "F_right_stair_local": (970, 205, 1725, 505),
        "G_right_ticks_xlabel": (970, 495, 1725, 650),
        "H_caption": (0, 685, 1840, 885),
        "I_panel_gap_edges": (815, 45, 980, 690),
    }
    for name, box in rois.items():
        roi = base.crop(box).convert("RGB")
        roi.save(ROOT / f"roi_{name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(ROOT / f"roi_{name}_nearest8x.png")


if __name__ == "__main__":
    if len(ELEMENTS) != 22:
        raise RuntimeError("denominator mismatch")
    write_indices_and_metrics()
    write_overlays_and_rois()
    print("N=22")
    print("C=231")
    print("manual_verdict_fields_written=0")
