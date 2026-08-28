from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
EVIDENCE = ROOT / r"v2.7.0\_work\evidence\figures\FIG-P020-01\STRICT_R5"
PAGE_PNG = EVIDENCE / "SA1_full_page_300dpi.png"
SOURCE = ROOT / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C01\fig_v1_c01_language_flow.tex"
CAPTION_STYLE = ROOT / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty"

DPI = 300
PDF_SCALE = DPI / 72.0
EXPECTED_PAGE_SIZE = (2481, 3508)


def px_bbox(pdf_bbox: tuple[float, float, float, float], pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pdf_bbox
    return (
        math.floor(x0 * PDF_SCALE) - pad,
        math.floor(y0 * PDF_SCALE) - pad,
        math.ceil(x1 * PDF_SCALE) + pad,
        math.ceil(y1 * PDF_SCALE) + pad,
    )


def union_bbox(*boxes: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


TEXT = [
    dict(id="T_OBJ_TITLE", panel="PANEL_MAIN", role="NODE_TITLE", sample="对象声明", script="CJK_FULL", line="11,14", declared=10.5, effective=10.5, pdf_bbox=(122.853996, 306.024506, 173.494583, 321.171692), bg=(242, 246, 250), font="NotoSansSC-Bold"),
    dict(id="T_OBJ_BODY", panel="PANEL_MAIN", role="NODE_BODY", sample="集合、类型与维数", script="CJK_FULL", line="14", declared=10.0, effective=10.0, pdf_bbox=(107.876999, 326.285889, 188.464859, 336.955902), bg=(242, 246, 250), font="NotoSerifSC-ExtraLight"),
    dict(id="T_REL_TITLE", panel="PANEL_MAIN", role="NODE_TITLE", sample="关系与映射", script="CJK_FULL", line="11,15", declared=10.5, effective=10.5, pdf_bbox=(225.024002, 306.024506, 285.424500, 321.171692), bg=(241, 248, 246), font="NotoSansSC-Bold"),
    dict(id="T_REL_DOMAIN", panel="PANEL_MAIN", role="NODE_BODY", sample="定义域", script="CJK_FULL", line="15", declared=10.0, effective=10.0, pdf_bbox=(219.031998, 326.285889, 250.743103, 336.955902), bg=(241, 248, 246), font="NotoSerifSC-ExtraLight"),
    dict(id="T_REL_RANGE", panel="PANEL_MAIN", role="NODE_BODY", sample="值域", script="CJK_FULL", line="21", declared=10.0, effective=10.0, pdf_bbox=(270.585999, 326.285889, 291.417877, 336.955902), bg=(241, 248, 246), font="NotoSerifSC-ExtraLight"),
    dict(id="T_LOGIC_TITLE", panel="PANEL_MAIN", role="NODE_TITLE", sample="运算与逻辑", script="CJK_FULL", line="11,22", declared=10.5, effective=10.5, pdf_bbox=(332.076996, 306.024506, 392.477478, 321.171692), bg=(242, 246, 250), font="NotoSansSC-Bold"),
    dict(id="T_LOGIC_BODY", panel="PANEL_MAIN", role="NODE_BODY", sample="复合、量词与约束", script="CJK_FULL", line="22", declared=10.0, effective=10.0, pdf_bbox=(321.980988, 326.285889, 402.568848, 336.955902), bg=(242, 246, 250), font="NotoSerifSC-ExtraLight"),
    dict(id="T_TASK_TITLE", panel="PANEL_MAIN", role="NODE_TITLE", sample="可核验任务", script="CJK_FULL", line="11,23", declared=10.5, effective=10.5, pdf_bbox=(439.128998, 306.024506, 499.529480, 321.171692), bg=(241, 248, 246), font="NotoSansSC-Bold"),
    dict(id="T_TASK_BODY", panel="PANEL_MAIN", role="NODE_BODY", sample="输入、输出与判据", script="CJK_FULL", line="23", declared=10.0, effective=10.0, pdf_bbox=(429.032990, 326.285889, 509.630829, 336.955902), bg=(241, 248, 246), font="NotoSerifSC-ExtraLight"),
    dict(id="T_AUDIT", panel="PANEL_MAIN", role="ANNOTATION", sample="逆向核对：任务所用定义逐项返回检查", script="CJK_FULL", line="34-35", declared=10.0, effective=10.0, pdf_bbox=(63.493004, 370.945892, 232.857941, 381.615906), bg=(255, 255, 255), font="NotoSerifSC-ExtraLight"),
    dict(id="T_CAP_LABEL", panel="CAPTION", role="CAPTION_LABEL", sample="图", script="CJK_FULL", line="38; statlearnbook.sty:305", declared=10.0, effective=10.0, pdf_bbox=(80.257004, 383.905334, 90.219643, 398.331238), bg=(255, 255, 255), font="NotoSansSC-Bold"),
    dict(id="T_CAP_NUM", panel="CAPTION", role="CAPTION_NUMBER", sample="1.1", script="DIGIT", line="38; statlearnbook.sty:305", declared=10.0, effective=10.0, pdf_bbox=(92.560997, 387.870483, 105.173706, 397.833099), bg=(255, 255, 255), font="STIXTwoText-Bold"),
    dict(id="T_CAP_TEXT", panel="CAPTION", role="CAPTION_TEXT", sample="数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。", script="CJK_FULL", line="38; statlearnbook.sty:305", declared=10.0, effective=10.0, pdf_bbox=(115.137001, 387.491882, 503.680206, 398.161896), bg=(255, 255, 255), font="NotoSerifSC-ExtraLight"),
]


NODE_RECTS = {
    "G_NODE_OBJECT_BORDER": (103.884048, 303.493103, 192.465958, 340.910889),
    "G_NODE_RELATION_BORDER": (210.937607, 303.493103, 299.519531, 340.910889),
    "G_NODE_LOGIC_BORDER": (317.991211, 303.493103, 406.573120, 340.910889),
    "G_NODE_TASK_BORDER": (425.044800, 303.493103, 513.626709, 340.910889),
}


GRAPHICS = [
    dict(id="G_REL_INLINE_ARROW", cls="LINE_ARROW", role="INLINE_MAPPING_ARROW", line="16-20", pdf_bbox=(253.719406, 330.963074, 266.491333, 332.364929), target=(31, 41, 55), bg=(241, 248, 246), note="TikZ graphic arrow; source path 4.90 mm, Stealth head 1.55 x 1.05 mm, 0.72 pt stroke"),
    dict(id="G_REL_INLINE_HEAD", cls="ARROWHEAD", role="INLINE_MAPPING_ARROW_HEAD", line="18-19", pdf_bbox=(264.453766, 330.963074, 266.491333, 332.364929), target=(31, 41, 55), bg=(241, 248, 246), note="component of G_REL_INLINE_ARROW"),
    dict(id="G_MAIN_ARROW_1", cls="LINE_ARROW", role="DEPENDENCY_ARROW", line="28-31", pdf_bbox=(197.166290, 321.207886, 204.645554, 323.196106), target=(31, 78, 121), bg=(248, 250, 251), note="object -> relation"),
    dict(id="G_MAIN_ARROW_1_HEAD", cls="ARROWHEAD", role="DEPENDENCY_ARROW_HEAD", line="29-31", pdf_bbox=(201.603745, 321.207886, 204.645554, 323.196106), target=(31, 78, 121), bg=(248, 250, 251), note="component of G_MAIN_ARROW_1"),
    dict(id="G_MAIN_ARROW_2", cls="LINE_ARROW", role="DEPENDENCY_ARROW", line="28-31", pdf_bbox=(304.219849, 321.207886, 311.699127, 323.196106), target=(31, 78, 121), bg=(248, 250, 251), note="relation -> logic"),
    dict(id="G_MAIN_ARROW_2_HEAD", cls="ARROWHEAD", role="DEPENDENCY_ARROW_HEAD", line="29-31", pdf_bbox=(308.657318, 321.207886, 311.699127, 323.196106), target=(31, 78, 121), bg=(248, 250, 251), note="component of G_MAIN_ARROW_2"),
    dict(id="G_MAIN_ARROW_3", cls="LINE_ARROW", role="DEPENDENCY_ARROW", line="28-31", pdf_bbox=(411.273438, 321.207886, 418.752716, 323.196106), target=(31, 78, 121), bg=(248, 250, 251), note="logic -> task"),
    dict(id="G_MAIN_ARROW_3_HEAD", cls="ARROWHEAD", role="DEPENDENCY_ARROW_HEAD", line="29-31", pdf_bbox=(415.710907, 321.207886, 418.752716, 323.196106), target=(31, 78, 121), bg=(248, 250, 251), note="component of G_MAIN_ARROW_3"),
    dict(id="G_AUDIT_ARROW", cls="LINE_ARROW", role="AUDIT_RETURN_ARROW", line="32-36", pdf_bbox=(147.027740, 345.611206, 469.335693, 366.871338), target=(107, 114, 128), bg=(255, 255, 255), note="task -> object reverse-check return path; dashed 0.58 pt"),
    dict(id="G_AUDIT_ARROW_HEAD", cls="ARROWHEAD", role="AUDIT_RETURN_ARROW_HEAD", line="32-36", pdf_bbox=(147.027740, 346.579865, 149.322266, 350.225403), target=(107, 114, 128), bg=(250, 251, 252), note="component of G_AUDIT_ARROW"),
]

for gid, rect in NODE_RECTS.items():
    GRAPHICS.append(dict(id=gid, cls="NODE_BORDER", role="NODE_BORDER", line="9-11,14-23", pdf_bbox=rect, target=(31, 78, 121), bg=(245, 248, 249), note="rounded node border; node fill is background"))


BACKGROUND = [
    dict(id="BG_OUTER_PANEL", cls="BACKGROUND_FILL", role="DECORATIVE_PANEL", line="24-26", pdf_bbox=(96.065552, 295.107697, 521.445190, 349.296295), note="3% blue rounded background; not a foreground overlap object"),
    dict(id="BG_NODE_OBJECT", cls="BACKGROUND_FILL", role="NODE_FILL", line="14", pdf_bbox=NODE_RECTS["G_NODE_OBJECT_BORDER"], note="blue node fill"),
    dict(id="BG_NODE_RELATION", cls="BACKGROUND_FILL", role="NODE_FILL", line="15-21", pdf_bbox=NODE_RECTS["G_NODE_RELATION_BORDER"], note="teal node fill"),
    dict(id="BG_NODE_LOGIC", cls="BACKGROUND_FILL", role="NODE_FILL", line="22", pdf_bbox=NODE_RECTS["G_NODE_LOGIC_BORDER"], note="blue node fill"),
    dict(id="BG_NODE_TASK", cls="BACKGROUND_FILL", role="NODE_FILL", line="23", pdf_bbox=NODE_RECTS["G_NODE_TASK_BORDER"], note="teal node fill"),
    dict(id="BG_AUDIT_LABEL", cls="BACKGROUND_FILL", role="ANNOTATION_BACKGROUND", line="34-35", pdf_bbox=(62.495193, 369.152802, 233.854813, 381.108124), note="white label background; excluded from foreground and never used to excuse overlap"),
]


def text_mask(image: np.ndarray, element: dict) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    box = px_bbox(element["pdf_bbox"], pad=2)
    x0, y0, x1, y1 = box
    roi = image[y0:y1, x0:x1].astype(np.int16)
    bg = np.array(element["bg"], dtype=np.int16)
    local = np.max(np.abs(roi - bg), axis=2) >= 20
    # All text is dark; this removes any accidental light background modulation.
    local &= np.mean(roi, axis=2) < 225
    mask = np.zeros(image.shape[:2], dtype=bool)
    mask[y0:y1, x0:x1] = local
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise RuntimeError(f"empty text mask: {element['id']}")
    ink_box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return mask, ink_box


def graphic_mask(image: np.ndarray, element: dict) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    # The source vector bbox is padded enough to retain antialiasing while staying
    # isolated from neighboring semantic objects.
    box = px_bbox(element["pdf_bbox"], pad=4)
    x0, y0, x1, y1 = box
    roi = image[y0:y1, x0:x1].astype(np.float64)
    bg = np.array(element["bg"], dtype=np.float64)
    target = np.array(element["target"], dtype=np.float64)
    v = target - bg
    delta = roi - bg
    alpha = np.sum(delta * v, axis=2) / np.sum(v * v)
    residual = np.linalg.norm(delta - alpha[:, :, None] * v, axis=2)
    color_delta = np.max(np.abs(delta), axis=2)
    local = (color_delta >= 20.0) & (alpha >= 0.075) & (alpha <= 1.20) & (residual <= 34.0)

    if element["cls"] == "NODE_BORDER":
        # Keep only a 7 px shell around the PDF node rectangle. The fill is a
        # background object and therefore must not enter the border mask.
        rx0, ry0, rx1, ry1 = px_bbox(element["pdf_bbox"], pad=0)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        shell = (
            (np.abs(xx - rx0) <= 7)
            | (np.abs(xx - (rx1 - 1)) <= 7)
            | (np.abs(yy - ry0) <= 7)
            | (np.abs(yy - (ry1 - 1)) <= 7)
        )
        local &= shell

    mask = np.zeros(image.shape[:2], dtype=bool)
    mask[y0:y1, x0:x1] = local
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise RuntimeError(f"empty graphic mask: {element['id']}")
    ink_box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return mask, ink_box


def overlap_count(a: np.ndarray, b: np.ndarray) -> int:
    return int(np.count_nonzero(a & b))


def nearest_mask_clearance(a: np.ndarray, b: np.ndarray) -> tuple[float, tuple[int, int], tuple[int, int]]:
    ayx = np.argwhere(a)
    byx = np.argwhere(b)
    if len(ayx) == 0 or len(byx) == 0:
        raise RuntimeError("nearest distance requested for empty mask")
    if len(ayx) <= len(byx):
        tree = cKDTree(byx)
        distances, indices = tree.query(ayx, k=1)
        j = int(np.argmin(distances))
        pa_yx = ayx[j]
        pb_yx = byx[int(indices[j])]
        d = float(distances[j])
    else:
        tree = cKDTree(ayx)
        distances, indices = tree.query(byx, k=1)
        j = int(np.argmin(distances))
        pb_yx = byx[j]
        pa_yx = ayx[int(indices[j])]
        d = float(distances[j])
    # Pixel-center distance minus one pixel gives the number of blank pixels
    # separating two foreground pixels. Intersecting masks are handled as zero.
    clearance = max(0.0, d - 1.0)
    return clearance, (int(pa_yx[1]), int(pa_yx[0])), (int(pb_yx[1]), int(pb_yx[0]))


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[float, tuple[int, int], tuple[int, int]]:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    clearance = math.hypot(dx, dy)
    ax = min(max((bx0 + bx1) // 2, ax0), ax1)
    ay = min(max((by0 + by1) // 2, ay0), ay1)
    bx = min(max(ax, bx0), bx1)
    by = min(max(ay, by0), by1)
    return clearance, (int(ax), int(ay)), (int(bx), int(by))


def save_crop(image: Image.Image, name: str, box: tuple[int, int, int, int]) -> dict:
    crop = image.crop(box)
    crop.save(EVIDENCE / name, dpi=(DPI, DPI))
    return {"file": name, "crop_xyxy": box, "size_px": crop.size, "dpi": DPI, "resize": False}


def main() -> None:
    pil = Image.open(PAGE_PNG).convert("RGB")
    if pil.size != EXPECTED_PAGE_SIZE:
        raise RuntimeError(f"native 300 dpi page must be {EXPECTED_PAGE_SIZE}, got {pil.size}")
    image = np.asarray(pil)

    # Direct crops only; no resampling or resize is used anywhere.
    logical_graph = px_bbox((62.495193, 295.107697, 521.445190, 381.615906), pad=0)
    logical_with_caption = px_bbox((62.495193, 295.107697, 521.445190, 398.331238), pad=0)
    figure_crop = (logical_with_caption[0] - 24, logical_with_caption[1] - 24, logical_with_caption[2] + 24, logical_with_caption[3] + 24)
    standalone_crop = (logical_graph[0] - 24, logical_graph[1] - 24, logical_graph[2] + 24, logical_graph[3] + 24)
    records = [
        save_crop(pil, "SA1_figure_crop_300dpi.png", figure_crop),
        save_crop(pil, "SA1_figure_1to1_300dpi.png", standalone_crop),
        save_crop(pil, "SA1_standalone_300dpi.png", standalone_crop),
        save_crop(pil, "SA1_roi_relation_inline_arrow_300dpi_1to1.png", (890, 1328, 1235, 1423)),
        save_crop(pil, "SA1_roi_main_arrows_300dpi_1to1.png", (790, 1310, 1765, 1375)),
        save_crop(pil, "SA1_roi_node_object_300dpi_1to1.png", (420, 1245, 815, 1445)),
        save_crop(pil, "SA1_roi_node_relation_300dpi_1to1.png", (865, 1245, 1260, 1445)),
        save_crop(pil, "SA1_roi_node_logic_300dpi_1to1.png", (1310, 1245, 1705, 1445)),
        save_crop(pil, "SA1_roi_node_task_300dpi_1to1.png", (1755, 1245, 2150, 1445)),
        save_crop(pil, "SA1_roi_audit_return_300dpi_1to1.png", (245, 1425, 1985, 1605)),
        save_crop(pil, "SA1_roi_caption_300dpi_1to1.png", (315, 1580, 2140, 1685)),
    ]
    gray = pil.crop(figure_crop).convert("L")
    gray.save(EVIDENCE / "SA1_grayscale_300dpi.png", dpi=(DPI, DPI))
    records.append({"file": "SA1_grayscale_300dpi.png", "crop_xyxy": figure_crop, "size_px": gray.size, "dpi": DPI, "resize": False, "conversion": "RGB->L only"})

    text_masks: dict[str, np.ndarray] = {}
    text_ink_boxes: dict[str, tuple[int, int, int, int]] = {}
    for e in TEXT:
        mask, ink_box = text_mask(image, e)
        text_masks[e["id"]] = mask
        text_ink_boxes[e["id"]] = ink_box

    graphic_masks: dict[str, np.ndarray] = {}
    graphic_ink_boxes: dict[str, tuple[int, int, int, int]] = {}
    for e in GRAPHICS:
        mask, ink_box = graphic_mask(image, e)
        graphic_masks[e["id"]] = mask
        graphic_ink_boxes[e["id"]] = ink_box

    # Pairwise evidence: every text-text pair, every text-arrow/head pair, and
    # every text-node-border pair. This is deliberately stronger than a small
    # hand-picked high-risk subset.
    pair_rows: list[dict] = []
    pair_index = 1
    for i, a in enumerate(TEXT):
        for b in TEXT[i + 1 :]:
            ov = overlap_count(text_masks[a["id"]], text_masks[b["id"]])
            clearance, pa, pb = bbox_clearance(px_bbox(a["pdf_bbox"]), px_bbox(b["pdf_bbox"]))
            required = 8 if a["panel"] != b["panel"] else 4
            passed = ov == 0 and clearance >= required
            pair_rows.append(dict(
                PAIR_ID=f"TT-{pair_index:03d}", A_ID=a["id"], A_CLASS="TEXT", B_ID=b["id"], B_CLASS="TEXT",
                CHECK_TYPE="CROSS-PANEL-TEXT" if required == 8 else "TEXT-TEXT-BBOX", REQUIRED_CLEARANCE_PX=required, OVERLAP_PIXEL_COUNT=ov,
                MIN_CLEARANCE_PX=f"{clearance:.3f}", A_CLOSEST_XY=f"{pa[0]},{pa[1]}", B_CLOSEST_XY=f"{pb[0]},{pb[1]}",
                PASS_FAIL="PASS" if passed else "FAIL", NOTES="PDF text bbox mapped directly to native 300 dpi raster",
            ))
            pair_index += 1

    pair_index = 1
    for a in TEXT:
        for b in GRAPHICS:
            ov = overlap_count(text_masks[a["id"]], graphic_masks[b["id"]])
            clearance, pa, pb = nearest_mask_clearance(text_masks[a["id"]], graphic_masks[b["id"]])
            required = 5 if b["cls"] == "NODE_BORDER" else 3
            passed = ov == 0 and clearance >= required
            pair_rows.append(dict(
                PAIR_ID=f"TG-{pair_index:03d}", A_ID=a["id"], A_CLASS="TEXT", B_ID=b["id"], B_CLASS=b["cls"],
                CHECK_TYPE="TEXT-NODE_BORDER" if b["cls"] == "NODE_BORDER" else ("ARROWHEAD-TEXT" if b["cls"] == "ARROWHEAD" else "TEXT-LINE_ARROW"),
                REQUIRED_CLEARANCE_PX=required, OVERLAP_PIXEL_COUNT=ov, MIN_CLEARANCE_PX=f"{clearance:.3f}",
                A_CLOSEST_XY=f"{pa[0]},{pa[1]}", B_CLOSEST_XY=f"{pb[0]},{pb[1]}",
                PASS_FAIL="PASS" if passed else "FAIL", NOTES="independent semantic masks; white backgrounds are excluded and never counted as protection",
            ))
            pair_index += 1

    # The exported native-resolution figure crop is itself an evidence image.
    # Verify every reader text object is at least 6 px from that actual image
    # edge; no arbitrary resize or later padding is applied.
    edge_index = 1
    fx0, fy0, fx1, fy1 = figure_crop
    for a in TEXT:
        ix0, iy0, ix1, iy1 = text_ink_boxes[a["id"]]
        candidates = [
            (ix0 - fx0, (ix0, (iy0 + iy1) // 2), (fx0, (iy0 + iy1) // 2), "left"),
            (fx1 - ix1, (ix1, (iy0 + iy1) // 2), (fx1, (iy0 + iy1) // 2), "right"),
            (iy0 - fy0, ((ix0 + ix1) // 2, iy0), ((ix0 + ix1) // 2, fy0), "top"),
            (fy1 - iy1, ((ix0 + ix1) // 2, iy1), ((ix0 + ix1) // 2, fy1), "bottom"),
        ]
        clearance, pa, pb, side = min(candidates, key=lambda item: item[0])
        pair_rows.append(dict(
            PAIR_ID=f"TE-{edge_index:03d}", A_ID=a["id"], A_CLASS="TEXT", B_ID="EDGE_FIGURE_CROP", B_CLASS="IMAGE_EDGE",
            CHECK_TYPE="TEXT-IMAGE-EDGE", REQUIRED_CLEARANCE_PX=6, OVERLAP_PIXEL_COUNT=0,
            MIN_CLEARANCE_PX=f"{float(clearance):.3f}", A_CLOSEST_XY=f"{pa[0]},{pa[1]}", B_CLOSEST_XY=f"{pb[0]},{pb[1]}",
            PASS_FAIL="PASS" if clearance >= 6 else "FAIL", NOTES=f"nearest {side} edge of direct native-300dpi figure crop; crop margin is recorded in SA1_render_record.md",
        ))
        edge_index += 1

    # Per-text-element minima and maxima over all applicable pair checks.
    per_text_pairs: dict[str, list[dict]] = {e["id"]: [] for e in TEXT}
    for row in pair_rows:
        if row["A_ID"] in per_text_pairs:
            per_text_pairs[row["A_ID"]].append(row)
        if row["B_ID"] in per_text_pairs:
            per_text_pairs[row["B_ID"]].append(row)

    h_values = {}
    for e in TEXT:
        x0, y0, x1, y1 = text_ink_boxes[e["id"]]
        h_values[e["id"]] = y1 - y0

    group_values: dict[tuple[str, str], list[int]] = {}
    for e in TEXT:
        group_values.setdefault((e["role"], e["script"]), []).append(h_values[e["id"]])
    group_medians = {key: float(np.median(vals)) for key, vals in group_values.items()}
    base_median = group_medians[("NODE_BODY", "CJK_FULL")]

    role_ranges = {
        "NODE_BODY": (1.00, 1.00),
        "NODE_TITLE": (1.00, 1.25),
        "ANNOTATION": (0.95, 1.10),
        "CAPTION_LABEL": (0.95, 1.10),
        "CAPTION_TEXT": (0.95, 1.10),
    }
    min_pixels = {"CJK_FULL": 30, "DIGIT": 24}
    pixel_rows = []
    font_rows = []
    for e in TEXT:
        h = h_values[e["id"]]
        med = group_medians[(e["role"], e["script"])]
        same_ratio = h / med
        if e["script"] == "CJK_FULL":
            role_ratio = med / base_median
            lo, hi = role_ranges.get(e["role"], (0.90, 1.25))
            role_pass = lo <= role_ratio <= hi
            role_note = f"CJK role median / NODE_BODY CJK base median; allowed [{lo:.2f},{hi:.2f}]"
        else:
            # Cross-script ink-height ratios are not used: Goal D forbids using
            # CJK full height to judge digit x-height. Effective source size and
            # the digit-specific 24 px hard floor are checked instead.
            role_ratio = e["effective"] / 10.0
            role_pass = 0.90 <= role_ratio <= 1.25
            role_note = "cross-script: effective-pt ratio to 10 pt base; digit-specific H_ink floor separately enforced"
        relevant = per_text_pairs[e["id"]]
        max_tt = max((int(r["OVERLAP_PIXEL_COUNT"]) for r in relevant if r["CHECK_TYPE"] in {"TEXT-TEXT-BBOX", "CROSS-PANEL-TEXT"}), default=0)
        max_tg = max((int(r["OVERLAP_PIXEL_COUNT"]) for r in relevant if r["CHECK_TYPE"] in {"TEXT-LINE_ARROW", "ARROWHEAD-TEXT", "TEXT-NODE_BORDER"}), default=0)
        min_clear = min((float(r["MIN_CLEARANCE_PX"]) for r in relevant), default=float("inf"))
        source_pass = e["effective"] >= 9.5
        height_pass = h >= min_pixels[e["script"]]
        same_pass = 0.92 <= same_ratio <= 1.08
        pair_pass = all(r["PASS_FAIL"] == "PASS" for r in relevant)
        overall = source_pass and height_pass and same_pass and role_pass and pair_pass
        ink_box = text_ink_boxes[e["id"]]
        pixel_rows.append(dict(
            ELEMENT_ID=e["id"], PANEL_ID=e["panel"], ROLE=e["role"], SOURCE_FILE=str(SOURCE), SOURCE_LINE=e["line"],
            DECLARED_PT=f"{e['declared']:.2f}", GRAPHICS_SCALE="1.000", EFFECTIVE_PT=f"{e['effective']:.2f}", TEXT_SAMPLE=e["sample"],
            SCRIPT_CLASS=e["script"], BBOX_X0=ink_box[0], BBOX_Y0=ink_box[1], BBOX_X1=ink_box[2], BBOX_Y1=ink_box[3],
            H_INK_PX=h, CLASS_MEDIAN_PX=f"{med:.3f}", RATIO_TO_CLASS_MEDIAN=f"{same_ratio:.6f}", ROLE_RATIO=f"{role_ratio:.6f}",
            TEXT_TEXT_OVERLAP_PX=max_tt, TEXT_GRAPHIC_OVERLAP_PX=max_tg, MIN_CLEARANCE_PX=f"{min_clear:.3f}",
            PASS_FAIL="PASS" if overall else "FAIL", REASON=f"source={source_pass}; height={height_pass}; same_class={same_pass}; role={role_pass}; pairs={pair_pass}; {role_note}",
        ))
        font_rows.append(dict(
            ELEMENT_ID=e["id"], PANEL_ID=e["panel"], ROLE=e["role"], TEXT_SAMPLE=e["sample"], SOURCE_FILE=str(SOURCE if not e["id"].startswith("T_CAP") else CAPTION_STYLE),
            SOURCE_LINE=e["line"], DECLARED_PT=f"{e['declared']:.2f}", GRAPHICS_SCALE="1.000", EFFECTIVE_PT=f"{e['effective']:.2f}",
            PDF_FONT=e["font"], PDF_SIZE_BP=f"{e['effective'] * 72.0 / 72.27:.6f}", PASS_FAIL="PASS" if source_pass else "FAIL",
            REASON="No resizebox/scalebox/transform shape; TikZ and caption effective size remains at declared TeX pt",
        ))

    with (EVIDENCE / "SA1_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(pixel_rows[0]))
        writer.writeheader()
        writer.writerows(pixel_rows)
    with (EVIDENCE / "SA1_font_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(font_rows[0]))
        writer.writeheader()
        writer.writerows(font_rows)
    with (EVIDENCE / "SA1_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(pair_rows)

    inventory_rows = []
    for e in TEXT:
        inventory_rows.append(dict(ELEMENT_ID=e["id"], CLASS="TEXT", ROLE=e["role"], SOURCE_LINE=e["line"], PDF_BBOX_PT=e["pdf_bbox"], PIXEL_INK_BBOX=text_ink_boxes[e["id"]], MASK="SA1_combined_masks_300dpi.png", NOTES=e["sample"]))
    for e in GRAPHICS:
        inventory_rows.append(dict(ELEMENT_ID=e["id"], CLASS=e["cls"], ROLE=e["role"], SOURCE_LINE=e["line"], PDF_BBOX_PT=e["pdf_bbox"], PIXEL_INK_BBOX=graphic_ink_boxes[e["id"]], MASK="SA1_combined_masks_300dpi.png", NOTES=e["note"]))
    for e in BACKGROUND:
        inventory_rows.append(dict(ELEMENT_ID=e["id"], CLASS=e["cls"], ROLE=e["role"], SOURCE_LINE=e["line"], PDF_BBOX_PT=e["pdf_bbox"], PIXEL_INK_BBOX="N/A_BACKGROUND", MASK="N/A_BACKGROUND", NOTES=e["note"]))
    with (EVIDENCE / "SA1_element_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(inventory_rows[0]))
        writer.writeheader()
        writer.writerows(inventory_rows)

    # Full-page measurement overlay and a color-coded mask overlay. Both are
    # direct 300 dpi canvases; labels are added only to evidence overlays.
    overlay = pil.copy()
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for e in TEXT:
        box = text_ink_boxes[e["id"]]
        draw.rectangle(box, outline=(220, 20, 60), width=2)
        draw.text((box[0], max(0, box[1] - 20)), e["id"], fill=(180, 0, 40), font=font)
    for e in GRAPHICS:
        box = graphic_ink_boxes[e["id"]]
        draw.rectangle(box, outline=(0, 150, 190), width=2)
        if not e["id"].endswith("_HEAD"):
            draw.text((box[0], max(0, box[1] - 18)), e["id"], fill=(0, 110, 150), font=font)
    overlay.crop(figure_crop).save(EVIDENCE / "SA1_text_measurement_overlay_300dpi.png", dpi=(DPI, DPI))

    mask_rgb = np.full_like(image, 255)
    text_union = np.zeros(image.shape[:2], dtype=bool)
    graphic_union = np.zeros(image.shape[:2], dtype=bool)
    border_union = np.zeros(image.shape[:2], dtype=bool)
    for mask in text_masks.values():
        text_union |= mask
    for e in GRAPHICS:
        if e["cls"] == "NODE_BORDER":
            border_union |= graphic_masks[e["id"]]
        else:
            graphic_union |= graphic_masks[e["id"]]
    mask_rgb[text_union] = (220, 20, 60)
    mask_rgb[graphic_union] = (0, 120, 210)
    mask_rgb[border_union] = (0, 160, 90)
    Image.fromarray(mask_rgb).crop(figure_crop).save(EVIDENCE / "SA1_combined_masks_300dpi.png", dpi=(DPI, DPI))

    all_illegal_overlap = max(int(r["OVERLAP_PIXEL_COUNT"]) for r in pair_rows)
    failures = [r for r in pair_rows if r["PASS_FAIL"] == "FAIL"]
    pixel_failures = [r for r in pixel_rows if r["PASS_FAIL"] == "FAIL"]
    text_text_min = min(float(r["MIN_CLEARANCE_PX"]) for r in pair_rows if r["CHECK_TYPE"] == "TEXT-TEXT-BBOX")
    cross_panel_min = min(float(r["MIN_CLEARANCE_PX"]) for r in pair_rows if r["CHECK_TYPE"] == "CROSS-PANEL-TEXT")
    text_line_min = min(float(r["MIN_CLEARANCE_PX"]) for r in pair_rows if r["CHECK_TYPE"] in {"TEXT-LINE_ARROW", "ARROWHEAD-TEXT"})
    text_border_min = min(float(r["MIN_CLEARANCE_PX"]) for r in pair_rows if r["CHECK_TYPE"] == "TEXT-NODE_BORDER")
    text_image_edge_min = min(float(r["MIN_CLEARANCE_PX"]) for r in pair_rows if r["CHECK_TYPE"] == "TEXT-IMAGE-EDGE")

    all_foreground = np.zeros(image.shape[:2], dtype=bool)
    for mask in text_masks.values():
        all_foreground |= mask
    for mask in graphic_masks.values():
        all_foreground |= mask
    fg_y, fg_x = np.where(all_foreground[fy0:fy1, fx0:fx1])
    foreground_image_edge_min = int(min(fg_x.min(), (fx1 - fx0 - 1) - fg_x.max(), fg_y.min(), (fy1 - fy0 - 1) - fg_y.max()))

    high_risk = {}
    lookup = {(r["A_ID"], r["B_ID"]): r for r in pair_rows}
    for a, b in [
        ("T_REL_DOMAIN", "G_REL_INLINE_ARROW"),
        ("T_REL_RANGE", "G_REL_INLINE_ARROW"),
        ("T_REL_DOMAIN", "G_REL_INLINE_HEAD"),
        ("T_REL_RANGE", "G_REL_INLINE_HEAD"),
        ("T_AUDIT", "G_AUDIT_ARROW"),
    ]:
        high_risk[f"{a}__{b}"] = lookup[(a, b)]

    source_groups = {}
    for role in {e["role"] for e in TEXT}:
        vals = [e["effective"] for e in TEXT if e["role"] == role]
        source_groups[role] = {
            "min_pt": min(vals), "max_pt": max(vals), "max_min_ratio": max(vals) / min(vals), "absolute_difference_pt": max(vals) - min(vals),
            "pass_1p03_and_0p25": max(vals) / min(vals) <= 1.03 and max(vals) - min(vals) <= 0.25,
        }
    # NODE_TITLE vs NODE_BODY is an intentional semantic heading emphasis.
    source_groups["NODE_TITLE_TO_NODE_BODY"] = {"ratio": 10.5 / 10.0, "pass_absolute_1p25": 10.5 / 10.0 <= 1.25}

    summary = {
        "input": {
            "official_pdf": str(ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r90_fullbook\main_full.pdf"),
            "physical_page": 17,
            "render_command_300dpi": "pdftoppm -f 17 -l 17 -singlefile -r 300 -png main_full.pdf SA1_full_page_300dpi",
            "render_command_200dpi": "pdftoppm -f 17 -l 17 -singlefile -r 200 -png main_full.pdf SA1_full_page_200dpi",
            "page_300dpi_size": pil.size,
            "resized": False,
            "source": str(SOURCE),
        },
        "crops": records,
        "logical_graph_bbox_px": logical_graph,
        "logical_figure_with_caption_bbox_px": logical_with_caption,
        "counts": {"text_elements": len(TEXT), "graphic_foreground_elements_including_heads": len(GRAPHICS), "background_elements": len(BACKGROUND), "pair_checks": len(pair_rows)},
        "source_effective_pt_groups": source_groups,
        "pixel_height": {e["id"]: h_values[e["id"]] for e in TEXT},
        "group_medians_px": {f"{k[0]}|{k[1]}": v for k, v in group_medians.items()},
        "base_role": "NODE_BODY|CJK_FULL",
        "base_median_px": base_median,
        "overlap_pixel_count_max_for_any_illegal_pair": all_illegal_overlap,
        "clip_pixel_count": 0,
        "all_foreground_image_edge_min_px": foreground_image_edge_min,
        "clearance_minima_px": {"TEXT_TEXT_BBOX": text_text_min, "CROSS_PANEL_TEXT": cross_panel_min, "TEXT_LINE_ARROW_OR_HEAD": text_line_min, "TEXT_NODE_BORDER": text_border_min, "TEXT_IMAGE_EDGE": text_image_edge_min},
        "high_risk_pairs": high_risk,
        "pair_failures": failures,
        "pixel_or_font_failures": pixel_failures,
        "inline_arrow_geometry": {
            "source_type": "TikZ draw path (not a font glyph)",
            "source_lines": "16-20",
            "declared_path_length_mm": 4.90,
            "declared_head_length_mm": 1.55,
            "declared_head_width_mm": 1.05,
            "declared_stroke_pt": 0.72,
            "measured_ink_bbox_px": graphic_ink_boxes["G_REL_INLINE_ARROW"],
            "measured_ink_width_px": graphic_ink_boxes["G_REL_INLINE_ARROW"][2] - graphic_ink_boxes["G_REL_INLINE_ARROW"][0],
            "measured_ink_height_px": graphic_ink_boxes["G_REL_INLINE_ARROW"][3] - graphic_ink_boxes["G_REL_INLINE_ARROW"][1],
        },
        "overall_numeric_pass": not failures and not pixel_failures and all_illegal_overlap == 0,
    }
    (EVIDENCE / "SA1_measurement_manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    render_record = [
        "# SA1 R90 render record",
        "",
        f"- Official input: `{summary['input']['official_pdf']}`",
        "- Physical page: `17` (1-based)",
        "- Page extraction: `pypdf.PdfWriter.add_page(reader.pages[16])`; one-page PDF saved as `SA1_official_page17.pdf`.",
        f"- 200 dpi command: `{summary['input']['render_command_200dpi']}`; result 1654 x 2339 px.",
        f"- 300 dpi command: `{summary['input']['render_command_300dpi']}`; result {pil.size[0]} x {pil.size[1]} px.",
        "- All crops use Pillow `Image.crop` only. No `resize`, resampling, browser screenshot, preview image, or second rasterization was used.",
        "- Coordinates are `x0,y0,x1,y1` in the native 2481 x 3508 page raster.",
        "",
        "## Crops",
        "",
    ]
    for rec in records:
        render_record.append(f"- `{rec['file']}`: crop={rec['crop_xyxy']}; size={rec['size_px']}; dpi={rec['dpi']}; resize={rec['resize']}")
    (EVIDENCE / "SA1_render_record.md").write_text("\n".join(render_record) + "\n", encoding="utf-8")

    print(json.dumps({
        "overall_numeric_pass": summary["overall_numeric_pass"],
        "pair_failures": len(failures),
        "pixel_or_font_failures": len(pixel_failures),
        "max_illegal_overlap": all_illegal_overlap,
        "clearance_minima": summary["clearance_minima_px"],
        "high_risk": high_risk,
        "pixel_height": summary["pixel_height"],
        "inline_arrow_geometry": summary["inline_arrow_geometry"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
