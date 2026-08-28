from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P634-01\sa1_r110_fresh_isolated_v1")
PAGE = ROOT / "render" / "physical_0684_fullpage_300dpi.png"
SCALE = 300.0 / 72.0


def obj(oid, cls, group, sample, source_lines, bbox_pt):
    return {
        "object_id": oid,
        "object_class": cls,
        "semantic_group": group,
        "sample": sample,
        "source_lines": source_lines,
        "bbox_pt": bbox_pt,
    }


# Manually frozen semantic-foreground denominator. Composite node fills/hatching are
# grouped with their node border; white halos are backgrounds under protocol 9.2.1-F.
OBJECTS = [
    obj("O001", "TEXT_TITLE", "TITLE", "单轮系统扫描坐标带", "17", (238.53, 341.11, 333.57, 351.68)),
    obj("O002", "TEXT_NUMERIC", "ORDER_HEADERS", "1", "18", (136.28, 359.67, 141.02, 369.23)),
    obj("O003", "TEXT_NUMERIC", "ORDER_HEADERS", "2", "19", (178.80, 359.69, 183.54, 369.25)),
    obj("O004", "TEXT", "ORDER_HEADERS", "省略", "20", (214.12, 360.56, 233.25, 370.12)),
    obj("O005", "TEXT", "ORDER_HEADERS", "前位", "21", (256.64, 360.56, 275.77, 370.12)),
    obj("O006", "TEXT", "ORDER_HEADERS", "当前", "22", (299.16, 360.56, 318.29, 370.12)),
    obj("O007", "TEXT", "ORDER_HEADERS", "后位", "23", (341.68, 360.56, 360.81, 370.12)),
    obj("O008", "TEXT", "ORDER_HEADERS", "省略", "24", (384.20, 360.56, 403.33, 370.12)),
    obj("O009", "TEXT", "ORDER_HEADERS", "末位", "25", (426.72, 360.56, 445.85, 370.12)),
    obj("O010", "LINE_ARROW", "ORDER_FLOW", "left-to-right update arrow", "26-27", (129.00, 373.10, 444.60, 376.00)),
    obj("O011", "TEXT", "ORDER_FLOW", "更新顺序", "27", (453.28, 371.33, 491.53, 380.89)),
    obj("O012", "NODE_BORDER", "UPDATED_SLOTS", "slot border/hatch: coordinate 1", "28,32", (119.94, 392.39, 157.36, 419.31)),
    obj("O013", "NODE_BORDER", "UPDATED_SLOTS", "slot border/hatch: coordinate 2", "29,33", (162.46, 392.39, 199.88, 419.31)),
    obj("O014", "NODE_BORDER", "UPDATED_SLOTS", "slot border/hatch: middle coordinate", "30,34", (204.98, 392.39, 242.40, 419.31)),
    obj("O015", "NODE_BORDER", "UPDATED_SLOTS", "slot border/hatch: updated-prefix last", "31,35", (247.50, 392.39, 284.92, 419.31)),
    obj("O016", "NODE_BORDER", "CURRENT_SLOT", "gold current-coordinate slot border/fill", "36", (290.02, 392.39, 327.44, 419.31)),
    obj("O017", "NODE_BORDER", "OLD_SLOTS", "dotted old slot: suffix first", "37", (332.54, 392.39, 369.96, 419.31)),
    obj("O018", "NODE_BORDER", "OLD_SLOTS", "dotted old slot: middle coordinate", "38", (375.06, 392.39, 412.48, 419.31)),
    obj("O019", "NODE_BORDER", "OLD_SLOTS", "dotted old slot: last coordinate", "39", (417.58, 392.39, 455.00, 419.31)),
    obj("O020", "TEXT_NUMERIC", "UPDATED_SLOTS", "坐标 1", "32", (129.08, 397.36, 148.21, 418.06)),
    obj("O021", "TEXT_NUMERIC", "UPDATED_SLOTS", "坐标 2", "33", (171.60, 397.36, 190.73, 418.06)),
    obj("O022", "TEXT", "UPDATED_SLOTS", "中间坐标", "34", (214.12, 396.78, 233.25, 417.80)),
    obj("O023", "TEXT", "UPDATED_SLOTS", "前段末位", "35", (256.64, 396.78, 275.77, 417.80)),
    obj("O024", "TEXT", "CURRENT_SLOT", "当前坐标", "36", (299.16, 396.78, 318.29, 417.80)),
    obj("O025", "TEXT", "OLD_SLOTS", "后段首位", "37", (341.68, 396.78, 360.81, 417.80)),
    obj("O026", "TEXT", "OLD_SLOTS", "中间坐标", "38", (384.20, 396.78, 403.33, 417.80)),
    obj("O027", "TEXT", "OLD_SLOTS", "末位坐标", "39", (426.72, 396.78, 445.85, 417.80)),
    obj("O028", "TEXT", "UPDATED_SLOTS", "本轮新值", "40", (184.72, 424.05, 222.97, 433.62)),
    obj("O029", "TEXT", "CURRENT_SLOT", "当前新值", "41", (289.60, 424.05, 327.86, 433.62)),
    obj("O030", "TEXT", "OLD_SLOTS", "前轮旧值", "42", (374.64, 424.05, 412.89, 433.62)),
    obj("O031", "NODE_BORDER", "SUBSTEP_STATE", "rounded current-substep state card", "44", (118.80, 434.06, 453.30, 463.82)),
    obj("O032", "FORMULA", "SUBSTEP_STATE", "x^[j]", "45", (246.21, 438.31, 263.38, 451.10)),
    obj("O033", "TEXT", "SUBSTEP_STATE", "当前子步状态", "45", (266.12, 441.47, 325.89, 451.43)),
    obj("O034", "TEXT", "SUBSTEP_STATE", "起始至当前坐标  本轮新值", "46-47", (152.35, 453.75, 269.51, 463.51)),
    obj("O035", "TEXT", "SUBSTEP_STATE", "后续至末位坐标  前轮旧值", "48-49", (302.59, 453.75, 419.75, 463.51)),
    obj("O036", "NODE_BORDER", "ROUND_END", "rounded sweep-end/record card", "51", (111.72, 467.36, 460.38, 498.54)),
    obj("O037", "TEXT", "ROUND_END", "状态相同", "55-56", (241.73, 471.16, 279.98, 480.73)),
    obj("O038", "LINE_ARROW", "ROUND_END", "bidirectional state-equivalence arrow", "55-56", (223.77, 485.75, 297.94, 488.66)),
    obj("O039", "FORMULA", "ROUND_END", "x^[d]", "52", (201.63, 482.23, 219.83, 495.02)),
    obj("O040", "TEXT", "ROUND_END", "仅此记录", "57-58", (333.77, 471.16, 372.03, 480.73)),
    obj("O041", "LINE_ARROW", "ROUND_END", "record-only right arrow", "57-58", (321.50, 486.38, 383.40, 488.66)),
    obj("O042", "FORMULA", "ROUND_END", "x^(t)", "53", (301.48, 482.06, 318.41, 494.85)),
    obj("O043", "TEXT", "ROUND_END", "轮末样本", "54", (387.00, 483.80, 426.05, 493.56)),
    obj("O044", "TEXT_CAPTION_LABEL", "CAPTION", "图 33.3", "61", (87.48, 505.58, 117.95, 516.04)),
    obj("O045", "TEXT_CAPTION", "CAPTION", "系统扫描按固定次序即时写回；当前子步的前段使用本轮新值，后段沿用前轮旧值；末位", "61", (127.92, 505.91, 519.13, 515.87)),
    obj("O046", "TEXT_CAPTION", "CAPTION", "更新结束后，末位状态与本轮样本状态相同并记录为轮末样本。", "61", (87.48, 519.30, 366.43, 529.26)),
]


TEXT_META = {
    "O001": (10.6, "TITLE", "CJK_FULL", 30),
    "O002": (9.6, "ORDER_LABEL", "LATIN_DIGIT", 24),
    "O003": (9.6, "ORDER_LABEL", "LATIN_DIGIT", 24),
    "O004": (9.6, "ORDER_LABEL", "CJK_FULL", 30),
    "O005": (9.6, "ORDER_LABEL", "CJK_FULL", 30),
    "O006": (9.6, "ORDER_LABEL", "CJK_FULL", 30),
    "O007": (9.6, "ORDER_LABEL", "CJK_FULL", 30),
    "O008": (9.6, "ORDER_LABEL", "CJK_FULL", 30),
    "O009": (9.6, "ORDER_LABEL", "CJK_FULL", 30),
    "O011": (9.6, "ORDER_ANNOTATION", "CJK_FULL", 30),
    "O028": (9.6, "STATE_ANNOTATION", "CJK_FULL", 30),
    "O029": (9.6, "STATE_ANNOTATION", "CJK_FULL", 30),
    "O030": (9.6, "STATE_ANNOTATION", "CJK_FULL", 30),
    "O032": (10.0, "FORMULA", "MATH_MIXED", 22),
    "O033": (10.0, "FORMULA_DESCRIPTOR", "CJK_FULL", 30),
    "O034": (9.8, "STATE_DESCRIPTOR", "CJK_FULL", 30),
    "O035": (9.8, "STATE_DESCRIPTOR", "CJK_FULL", 30),
    "O037": (9.6, "RELATION_LABEL", "CJK_FULL", 30),
    "O039": (10.0, "FORMULA", "MATH_MIXED", 22),
    "O040": (9.6, "RELATION_LABEL", "CJK_FULL", 30),
    "O042": (10.0, "FORMULA", "MATH_MIXED", 22),
    "O043": (9.8, "STATE_DESCRIPTOR", "CJK_FULL", 30),
    "O044": (10.0, "CAPTION_LABEL", "CJK_LATIN_DIGIT_MIXED", 24),
    "O045": (10.0, "CAPTION_BODY", "CJK_FULL", 30),
    "O046": (10.0, "CAPTION_BODY", "CJK_FULL", 30),
}


TEXT_SUBELEMENTS = [
    ("TE_020A", "O020", "坐标", "32", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (129.08, 397.36, 148.21, 406.92)),
    ("TE_020B", "O020", "1", "32", 9.6, "SLOT_LABEL", "LATIN_DIGIT", 24, (136.28, 408.50, 141.02, 418.06)),
    ("TE_021A", "O021", "坐标", "33", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (171.60, 397.36, 190.73, 406.92)),
    ("TE_021B", "O021", "2", "33", 9.6, "SLOT_LABEL", "LATIN_DIGIT", 24, (178.80, 408.50, 183.54, 418.06)),
    ("TE_022A", "O022", "中间", "34", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (214.12, 396.78, 233.25, 406.35)),
    ("TE_022B", "O022", "坐标", "34", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (214.12, 408.24, 233.25, 417.80)),
    ("TE_023A", "O023", "前段", "35", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (256.64, 396.78, 275.77, 406.35)),
    ("TE_023B", "O023", "末位", "35", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (256.64, 408.24, 275.77, 417.80)),
    ("TE_024A", "O024", "当前", "36", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (299.16, 396.78, 318.29, 406.35)),
    ("TE_024B", "O024", "坐标", "36", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (299.16, 408.24, 318.29, 417.80)),
    ("TE_025A", "O025", "后段", "37", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (341.68, 396.78, 360.81, 406.35)),
    ("TE_025B", "O025", "首位", "37", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (341.68, 408.24, 360.81, 417.80)),
    ("TE_026A", "O026", "中间", "38", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (384.20, 396.78, 403.33, 406.35)),
    ("TE_026B", "O026", "坐标", "38", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (384.20, 408.24, 403.33, 417.80)),
    ("TE_027A", "O027", "末位", "39", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (426.72, 396.78, 445.85, 406.35)),
    ("TE_027B", "O027", "坐标", "39", 9.6, "SLOT_LABEL", "CJK_FULL", 30, (426.72, 408.24, 445.85, 417.80)),
]


GLYPHS = [
    ("GL001", "O002", "1", "U+0031", "LATIN_DIGIT", 24, (136.28, 359.67, 141.02, 369.23)),
    ("GL002", "O003", "2", "U+0032", "LATIN_DIGIT", 24, (178.80, 359.69, 183.54, 369.25)),
    ("GL003", "O032", "x", "U+1D465", "LATIN_LOWER_XHEIGHT", 17, (246.21, 441.14, 251.78, 451.10)),
    ("GL004", "O032", "[", "U+005B", "MATH_SCRIPT", 15, (251.87, 438.31, 255.33, 447.28)),
    ("GL005", "O032", "j", "U+1D457", "MATH_SCRIPT", 15, (255.33, 438.31, 259.48, 447.28)),
    ("GL006", "O032", "]", "U+005D", "MATH_SCRIPT", 15, (259.93, 438.31, 263.38, 447.28)),
    ("GL007", "O039", "x", "U+1D465", "LATIN_LOWER_XHEIGHT", 17, (201.63, 485.05, 207.20, 495.02)),
    ("GL008", "O039", "[d]", "U+005B U+1D451 U+005D", "MATH_SCRIPT", 15, (207.30, 482.23, 219.83, 491.19)),
    ("GL009", "O042", "x", "U+1D465", "LATIN_LOWER_XHEIGHT", 17, (301.48, 484.88, 307.05, 494.85)),
    ("GL010", "O042", "(t)", "U+0028 U+1D461 U+0029", "MATH_SCRIPT", 15, (307.15, 482.06, 318.41, 491.02)),
    ("GL011", "O044", "33.3", "U+0033 U+0033 U+002E U+0033", "LATIN_DIGIT", 24, (100.06, 505.58, 117.95, 515.54)),
    ("GL012", "O045", "；", "U+FF1B", "LOW_PROFILE_PUNCTUATION_R168_ADVISORY", 0, (258.42, 505.91, 268.38, 515.87)),
    ("GL013", "O045", "，", "U+FF0C", "LOW_PROFILE_PUNCTUATION_R168_ADVISORY", 0, (398.89, 505.91, 408.85, 515.87)),
    ("GL014", "O045", "；", "U+FF1B", "LOW_PROFILE_PUNCTUATION_R168_ADVISORY", 0, (489.17, 505.91, 499.13, 515.87)),
    ("GL015", "O046", "。", "U+3002", "LOW_PROFILE_PUNCTUATION_R168_ADVISORY", 0, (356.47, 519.30, 366.43, 529.26)),
]


TEXT_COLORS = {
    "O001": ((31, 78, 121), 72),
    "O011": ((107, 114, 128), 58),
    "O028": ((31, 78, 121), 72),
    "O029": ((183, 121, 31), 72),
    "O030": ((107, 114, 128), 58),
    "O034": ((31, 78, 121), 72),
    "O035": ((107, 114, 128), 58),
    "O037": ((107, 114, 128), 58),
    "O040": ((107, 114, 128), 58),
    "O043": ((107, 114, 128), 58),
}


GROUP_COLORS = {
    "TITLE": (0, 92, 184),
    "ORDER_HEADERS": (10, 150, 85),
    "ORDER_FLOW": (125, 75, 175),
    "UPDATED_SLOTS": (15, 110, 205),
    "CURRENT_SLOT": (230, 125, 0),
    "OLD_SLOTS": (105, 105, 105),
    "SUBSTEP_STATE": (0, 145, 160),
    "ROUND_END": (190, 30, 120),
    "CAPTION": (190, 50, 35),
}

CLASS_COLORS = {
    "TEXT": (0, 150, 70),
    "TEXT_TITLE": (0, 120, 220),
    "TEXT_NUMERIC": (40, 180, 180),
    "FORMULA": (210, 20, 160),
    "LINE_ARROW": (115, 55, 190),
    "NODE_BORDER": (230, 125, 0),
    "TEXT_CAPTION_LABEL": (200, 40, 30),
    "TEXT_CAPTION": (200, 40, 30),
}


def pxbox(b):
    return tuple(int(round(v * SCALE)) for v in b)


def expanded(b, n=2):
    x0, y0, x1, y1 = pxbox(b)
    return x0 - n, y0 - n, x1 + n, y1 + n


def draw_box(draw, b, color, label, offset=(0, 0), width=3):
    x0, y0, x1, y1 = pxbox(b)
    ox, oy = offset
    bb = (x0 - ox, y0 - oy, x1 - ox, y1 - oy)
    draw.rectangle(bb, outline=color, width=width)
    tx, ty = bb[0] + 2, max(0, bb[1] - 14)
    draw.rectangle((tx - 1, ty - 1, tx + 31, ty + 11), fill=(255, 255, 255))
    draw.text((tx, ty), label, fill=color, font=ImageFont.load_default())


def foreground_mask(sub, object_id=None):
    target, tol = TEXT_COLORS.get(object_id, ((31, 35, 40), 86))
    target = np.array(target, dtype=np.int16)
    delta = np.max(np.abs(sub.astype(np.int16) - target), axis=2)
    contrast = np.max(255 - sub.astype(np.int16), axis=2)
    return (delta <= tol) & (contrast >= 20)


def ink_stats(arr, b, object_id=None):
    x0, y0, x1, y1 = expanded(b, 1)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(arr.shape[1], x1), min(arr.shape[0], y1)
    sub = arr[y0:y1, x0:x1]
    mask = foreground_mask(sub, object_id)
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return 0, 0, 0, 0, 0
    return int(xs.min() + x0), int(ys.min() + y0), int(xs.max() + x0), int(ys.max() + y0), int(ys.max() - ys.min() + 1)


def object_mask(arr, o):
    mask = np.zeros(arr.shape[:2], dtype=bool)
    x0, y0, x1, y1 = expanded(o["bbox_pt"], 3)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(arr.shape[1], x1), min(arr.shape[0], y1)
    sub = arr[y0:y1, x0:x1].astype(np.int16)
    cls = o["object_class"]
    if cls == "NODE_BORDER":
        oid = o["object_id"]
        if oid in {"O012", "O013", "O014", "O015"}:
            target = np.array([31, 78, 121], dtype=np.int16)
        elif oid == "O016":
            target = np.array([183, 121, 31], dtype=np.int16)
        else:
            target = np.array([184, 192, 200], dtype=np.int16)
        dist = np.max(np.abs(sub - target), axis=2)
        yy, xx = np.indices(dist.shape)
        edge_band = (xx <= 8) | (yy <= 8) | (xx >= dist.shape[1] - 9) | (yy >= dist.shape[0] - 9)
        local = (dist <= 34) & edge_band
    elif cls == "LINE_ARROW":
        target = np.array([107, 114, 128], dtype=np.int16)
        local = np.max(np.abs(sub - target), axis=2) <= 45
    else:
        local = foreground_mask(sub.astype(np.uint8), o["object_id"])
    mask[y0:y1, x0:x1] = local
    return mask


def bbox_metrics(a, b):
    ax0, ay0, ax1, ay1 = pxbox(a["bbox_pt"])
    bx0, by0, bx1, by1 = pxbox(b["bbox_pt"])
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    ix = max(0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0, min(ay1, by1) - max(ay0, by0))
    return dx, dy, math.hypot(dx, dy), ix * iy


def min_mask_gap(ma, mb, limit_box):
    overlap = int(np.count_nonzero(ma & mb))
    if overlap:
        return overlap, 0.0
    x0, y0, x1, y1 = limit_box
    apts = np.argwhere(ma[y0:y1, x0:x1])
    bpts = np.argwhere(mb[y0:y1, x0:x1])
    if not len(apts) or not len(bpts):
        return 0, None
    apts = apts + np.array([y0, x0])
    bpts = bpts + np.array([y0, x0])
    if len(apts) > len(bpts):
        apts, bpts = bpts, apts
    best2 = float("inf")
    for start in range(0, len(apts), 256):
        chunk = apts[start:start + 256]
        for j in range(0, len(bpts), 2048):
            other = bpts[j:j + 2048]
            d = chunk[:, None, :] - other[None, :, :]
            v = np.min(np.sum(d * d, axis=2))
            if v < best2:
                best2 = float(v)
                if best2 <= 1:
                    return 0, math.sqrt(best2)
    return 0, math.sqrt(best2)


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    im = Image.open(PAGE).convert("RGB")
    arr = np.asarray(im)
    crop_caption = (330, 1385, 2200, 2225)
    crop_figure = (450, 1390, 2080, 2080)
    cap = im.crop(crop_caption)
    fig = im.crop(crop_figure)
    cap.save(ROOT / "crops" / "figure_with_caption_300dpi.png")
    fig.save(ROOT / "crops" / "figure_only_300dpi.png")
    fig.convert("L").save(ROOT / "crops" / "figure_only_grayscale_300dpi.png")
    cap.convert("L").save(ROOT / "crops" / "figure_with_caption_grayscale_300dpi.png")
    im.convert("L").save(ROOT / "render" / "physical_0684_fullpage_grayscale_300dpi.png")

    object_rows = []
    for o in OBJECTS:
        x0, y0, x1, y1 = pxbox(o["bbox_pt"])
        object_rows.append({
            "object_id": o["object_id"], "object_class": o["object_class"],
            "semantic_group": o["semantic_group"], "sample": o["sample"],
            "source_lines": o["source_lines"],
            "bbox_x0_px": x0, "bbox_y0_px": y0, "bbox_x1_px": x1, "bbox_y1_px": y1,
            "bbox_width_px": x1 - x0, "bbox_height_px": y1 - y0,
        })
    write_csv(ROOT / "tables" / "object_denominator_machine.csv", list(object_rows[0]), object_rows)

    masks = {o["object_id"]: object_mask(arr, o) for o in OBJECTS}
    pair_rows = []
    for i, a in enumerate(OBJECTS):
        for b in OBJECTS[i + 1:]:
            dx, dy, gap, iarea = bbox_metrics(a, b)
            raw_overlap = ""
            raw_gap = ""
            if gap <= 55 or iarea:
                ax0, ay0, ax1, ay1 = pxbox(a["bbox_pt"])
                bx0, by0, bx1, by1 = pxbox(b["bbox_pt"])
                lim = (max(0, min(ax0, bx0) - 8), max(0, min(ay0, by0) - 8),
                       min(im.width, max(ax1, bx1) + 8), min(im.height, max(ay1, by1) + 8))
                ov, mg = min_mask_gap(masks[a["object_id"]], masks[b["object_id"]], lim)
                raw_overlap = ov
                raw_gap = "" if mg is None else f"{mg:.3f}"
            pair_rows.append({
                "pair_id": f"{a['object_id']}__{b['object_id']}",
                "object_a": a["object_id"], "object_b": b["object_id"],
                "class_a": a["object_class"], "class_b": b["object_class"],
                "bbox_dx_px": dx, "bbox_dy_px": dy,
                "bbox_euclidean_gap_px": f"{gap:.3f}",
                "bbox_intersection_area_px": iarea,
                "raw_mask_intersection_px": raw_overlap,
                "raw_mask_min_distance_px": raw_gap,
            })
    write_csv(ROOT / "tables" / "all_unordered_pairs_machine.csv", list(pair_rows[0]), pair_rows)

    text_rows = []
    provisional = []
    for oid, (pt, role, script_class, threshold) in TEXT_META.items():
        o = next(x for x in OBJECTS if x["object_id"] == oid)
        ix0, iy0, ix1, iy1, h = ink_stats(arr, o["bbox_pt"], oid)
        provisional.append((f"TE_{oid[1:]}", oid, pt, role, script_class, threshold, o["sample"], o["source_lines"], o["bbox_pt"], ix0, iy0, ix1, iy1, h))
    for eid, oid, sample, source_lines, pt, role, script_class, threshold, b in TEXT_SUBELEMENTS:
        ix0, iy0, ix1, iy1, h = ink_stats(arr, b, oid)
        provisional.append((eid, oid, pt, role, script_class, threshold, sample, source_lines, b, ix0, iy0, ix1, iy1, h))
    medians = {}
    for _, _, _, role, script_class, _, _, _, _, _, _, _, _, h in provisional:
        medians.setdefault((role, script_class), []).append(h)
    medians = {k: float(np.median(v)) for k, v in medians.items()}
    for eid, oid, pt, role, script_class, threshold, sample, source_lines, b, ix0, iy0, ix1, iy1, h in provisional:
        med = medians[(role, script_class)]
        text_rows.append({
            "element_id": eid, "object_id": oid, "panel_id": "PANEL_MAIN",
            "role": role, "source_file": "fig_v5_c04_coordinate_sweep.tex",
            "source_lines": source_lines, "declared_pt": f"{pt:.1f}",
            "graphics_scale": "1.000", "effective_pt": f"{pt:.1f}",
            "text_sample": sample, "script_class": script_class,
            "bbox_x0_px": pxbox(b)[0], "bbox_y0_px": pxbox(b)[1],
            "bbox_x1_px": pxbox(b)[2], "bbox_y1_px": pxbox(b)[3],
            "ink_x0_px": ix0, "ink_y0_px": iy0, "ink_x1_px": ix1, "ink_y1_px": iy1,
            "h_ink_px": h, "class_threshold_px": threshold,
            "class_median_px": f"{med:.3f}",
            "ratio_to_class_median": "" if med == 0 else f"{h / med:.5f}",
        })
    write_csv(ROOT / "tables" / "text_elements_machine.csv", list(text_rows[0]), text_rows)

    glyph_rows = []
    for gid, parent, sample, cps, script_class, threshold, b in GLYPHS:
        ix0, iy0, ix1, iy1, h = ink_stats(arr, b, parent)
        glyph_rows.append({
            "glyph_id": gid, "parent_object_id": parent, "sample": sample,
            "expected_codepoints": cps, "script_class": script_class,
            "bbox_x0_px": pxbox(b)[0], "bbox_y0_px": pxbox(b)[1],
            "bbox_x1_px": pxbox(b)[2], "bbox_y1_px": pxbox(b)[3],
            "ink_x0_px": ix0, "ink_y0_px": iy0, "ink_x1_px": ix1, "ink_y1_px": iy1,
            "h_ink_px": h, "class_threshold_px": threshold,
        })
    write_csv(ROOT / "tables" / "glyph_tokens_machine.csv", list(glyph_rows[0]), glyph_rows)

    # Object overlay: stable per-object boxes and IDs.
    over = cap.copy()
    d = ImageDraw.Draw(over)
    for o in OBJECTS:
        draw_box(d, o["bbox_pt"], CLASS_COLORS[o["object_class"]], o["object_id"], (crop_caption[0], crop_caption[1]), 2)
    over.save(ROOT / "overlays" / "object_overlay_300dpi.png")

    # Semantic overlay: group-colored boxes and IDs.
    sem = cap.copy()
    d = ImageDraw.Draw(sem)
    for o in OBJECTS:
        draw_box(d, o["bbox_pt"], GROUP_COLORS[o["semantic_group"]], o["object_id"], (crop_caption[0], crop_caption[1]), 3)
    sem.save(ROOT / "overlays" / "semantic_overlay_300dpi.png")

    # Text-measurement overlay: measured ink rectangles plus H_ink labels.
    txt = cap.copy()
    d = ImageDraw.Draw(txt)
    for row in text_rows:
        x0, y0, x1, y1 = (int(row[k]) for k in ("ink_x0_px", "ink_y0_px", "ink_x1_px", "ink_y1_px"))
        x0 -= crop_caption[0]; x1 -= crop_caption[0]
        y0 -= crop_caption[1]; y1 -= crop_caption[1]
        d.rectangle((x0, y0, x1, y1), outline=(230, 0, 160), width=2)
        label = f"{row['element_id']} H={row['h_ink_px']}"
        d.rectangle((x0, max(0, y0 - 13), x0 + 76, max(11, y0 - 1)), fill=(255, 255, 255))
        d.text((x0 + 1, max(0, y0 - 13)), label, fill=(150, 0, 105), font=ImageFont.load_default())
    txt.save(ROOT / "overlays" / "text_measurement_overlay_300dpi.png")

    rois = [
        ("ROI01_order_arrow", (1815, 1535, 1975, 1605), "O010,O011"),
        ("ROI02_updated_slots", (545, 1670, 625, 1755), "O012,O020"),
        ("ROI03_current_old_slots", (1325, 1625, 1420, 1760), "O016,O017,O024,O025"),
        ("ROI04_substep_card", (1040, 1870, 1125, 1940), "O031,O034"),
        ("ROI05_round_end", (1220, 1995, 1380, 2070), "O036,O041,O042"),
        ("ROI06_caption", (1050, 2090, 1140, 2160), "O045,GL012"),
    ]
    roi_rows = []
    for rid, box, ids in rois:
        r = im.crop(box)
        p1 = ROOT / "rois" / f"{rid}_native1x.png"
        p8 = ROOT / "rois" / f"{rid}_nearest8x.png"
        r.save(p1)
        r.resize((r.width * 8, r.height * 8), Image.Resampling.NEAREST).save(p8)
        roi_rows.append({
            "roi_id": rid, "x0_px": box[0], "y0_px": box[1], "x1_px": box[2], "y1_px": box[3],
            "relevant_object_ids": ids,
            "native1x_file": p1.name, "nearest8x_file": p8.name,
        })
    write_csv(ROOT / "tables" / "critical_rois_machine.csv", list(roi_rows[0]), roi_rows)

    print(f"objects={len(OBJECTS)} pairs={len(pair_rows)} text_elements={len(text_rows)} glyph_tokens={len(glyph_rows)} rois={len(rois)}")


if __name__ == "__main__":
    main()
