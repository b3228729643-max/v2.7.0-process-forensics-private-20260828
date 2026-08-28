from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa3_r113_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_exponential_family_moments.tex")
FULL_PAGE = ROOT / "full_page_300dpi.png"

PDF_EXPECTED_BYTES = 4_967_121
PDF_EXPECTED_SHA256 = "6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D"
SOURCE_EXPECTED_BYTES = 2_800
SOURCE_EXPECTED_SHA256 = "65F9C440D3058569C920F8C2E7E7B50545241EDAA6B6DAD4AA27EEF858324E6B"
PDF_PAGE_NUMBER_1BASED = 713
DPI = 300
PX_PER_PT = DPI / 72.0
CROP_PT = (60.0, 60.0, 522.0, 260.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def pt_to_page_px_box(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (
        math.floor(x0 * PX_PER_PT),
        math.floor(y0 * PX_PER_PT),
        math.ceil(x1 * PX_PER_PT),
        math.ceil(y1 * PX_PER_PT),
    )


CROP_PAGE_PX = pt_to_page_px_box(CROP_PT)
CROP_X0, CROP_Y0, CROP_X1, CROP_Y1 = CROP_PAGE_PX


def page_to_crop_px(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pt_to_page_px_box(box)
    return (x0 - CROP_X0, y0 - CROP_Y0, x1 - CROP_X0, y1 - CROP_Y0)


OBJECTS = [
    dict(id="O01", panel="L", category="TEXT", role="PANEL_TITLE", label="left panel title", bbox=(105.616, 70.979, 252.628, 81.649), expected="左：Dirichlet 密度的指数族拆分"),
    dict(id="O02", panel="L", category="FORMULA", role="DENSITY_FORMULA", label="Dirichlet exponential-family density", bbox=(94.153, 93.690, 264.091, 106.431), expected="p(theta|alpha)=h(theta) exp{sum_k eta_k T_k(theta)-A(alpha)}"),
    dict(id="O03", panel="L", category="BRACE", role="RELATION_BRACE", label="density decomposition brace", bbox=(75.655, 107.442, 281.169, 111.427), expected="brace"),
    dict(id="O04", panel="L", category="TEXT", role="ANNOTATION", label="brace explanatory note", bbox=(114.901, 118.957, 241.925, 127.425), expected="三项与对数配分函数共同确定密度"),
    dict(id="O05", panel="L", category="BACKGROUND_CONTAINER", role="TERM_BOX", label="base-measure pale box", bbox=(74.238, 137.750, 173.452, 163.908), expected="base measure container"),
    dict(id="O06", panel="L", category="TEXT_FORMULA", role="TERM_CONTENT", label="base-measure label and formula", bbox=(91.186, 140.638, 156.508, 162.033), expected="base measure; h(theta)=indicator_Delta(theta)"),
    dict(id="O07", panel="L", category="BACKGROUND_CONTAINER", role="TERM_BOX", label="natural-parameter pale box", bbox=(184.790, 136.861, 284.004, 164.797), expected="natural parameter container"),
    dict(id="O08", panel="L", category="TEXT_FORMULA", role="TERM_CONTENT", label="natural-parameter label and formula", bbox=(209.697, 141.646, 259.096, 162.738), expected="自然参数; eta_k=alpha_k-1"),
    dict(id="O09", panel="L", category="BACKGROUND_CONTAINER", role="TERM_BOX", label="sufficient-statistic pale box", bbox=(129.514, 176.240, 228.728, 204.222), expected="sufficient statistic container"),
    dict(id="O10", panel="L", category="TEXT_FORMULA", role="TERM_CONTENT", label="sufficient-statistic label and formula", bbox=(149.196, 181.024, 208.681, 202.117), expected="充分统计量; T_k(theta)=log theta_k"),
    dict(id="O11", panel="GUTTER", category="PANEL_BORDER", role="PANEL_DIVIDER", label="vertical panel divider", bbox=(304.90, 68.340, 305.63, 217.444), expected="vertical divider"),
    dict(id="O12", panel="R", category="TEXT", role="PANEL_TITLE", label="right panel title", bbox=(365.353, 70.979, 497.458, 81.649), expected="右：对数配分函数给出对数矩"),
    dict(id="O13", panel="R", category="FORMULA", role="LOG_PARTITION", label="log-partition formula", bbox=(363.396, 92.984, 499.414, 105.725), expected="A(alpha)=sum_k log Gamma(alpha_k)-log Gamma(alpha_0)"),
    dict(id="O14", panel="R", category="LINE_ARROW", role="DERIVATION_ARROW", label="downward implication arrow", bbox=(425.667, 107.378, 437.144, 123.318), expected="down arrow"),
    dict(id="O15", panel="R", category="FORMULA", role="DERIVATIVE", label="partial derivative formula", bbox=(422.934, 125.213, 439.876, 147.583), expected="partial A / partial alpha_k"),
    dict(id="O16", panel="R", category="NODE_BORDER", role="RESULT_CONTAINER", label="blue result container", bbox=(359.123, 147.994, 503.692, 179.175), expected="blue result box"),
    dict(id="O17", panel="R", category="FORMULA", role="RESULT_FORMULA", label="expected log-moment identity", bbox=(374.956, 159.304, 487.855, 169.740), expected="E[log Theta_k]=psi(alpha_k)-psi(alpha_0)"),
    dict(id="O18", panel="R", category="NODE_BORDER", role="WARNING_CONTAINER", label="red warning container", bbox=(353.453, 191.365, 509.361, 219.712), expected="red warning box"),
    dict(id="O19", panel="R", category="FORMULA", role="WARNING_FORMULA", label="noncommutation warning", bbox=(386.174, 201.257, 476.636, 211.693), expected="E[log Theta_k] != log E[Theta_k]"),
    dict(id="O20", panel="CAPTION", category="TEXT", role="CAPTION_LABEL", label="caption label", bbox=(76.138, 226.811, 107.581, 237.272), expected="图 34.6"),
    dict(id="O21", panel="CAPTION", category="TEXT_FORMULA", role="CAPTION_TEXT", label="caption line 1", bbox=(117.544, 226.811, 507.792, 239.560), expected="把 Dirichlet 分布写成指数族后，充分统计量是 log theta_k，对数配分函数对 alpha_k 的导数给出"),
    dict(id="O22", panel="CAPTION", category="TEXT_FORMULA", role="CAPTION_TEXT", label="caption line 2", bbox=(76.138, 240.201, 340.523, 252.950), expected="E[log Theta_k]=psi(alpha_k)-psi(alpha_0)；该对数矩不能用均值取对数替代"),
]


MEASUREMENTS = [
    dict(id="E01", object_id="O01", role="PANEL_TITLE", script="CJK_LATIN_MIXED", bbox=(105.616, 70.979, 252.628, 81.649), declared="10.2", source_line="10", source_note="title style"),
    dict(id="E02", object_id="O02", role="FORMULA_BASE", script="MATH_MIXED_WITH_SCRIPTS", bbox=(94.153, 93.690, 264.091, 106.431), declared="9.2", source_line="11-12", source_note="every node base"),
    dict(id="E03", object_id="O04", role="ANNOTATION", script="CJK_FULLHEIGHT", bbox=(114.901, 118.957, 241.925, 127.425), declared="8.5", source_line="16", source_note="brace note explicit font"),
    dict(id="E04", object_id="O06", role="BOX_HEADER", script="LATIN_XHEIGHT", bbox=(97.766, 140.638, 149.928, 149.803), declared="9.2", source_line="13", source_note="every node base"),
    dict(id="E05", object_id="O06", role="BOX_FORMULA", script="MATH_MIXED_WITH_SCRIPTS", bbox=(91.186, 151.597, 156.508, 162.033), declared="9.2", source_line="13", source_note="every node base"),
    dict(id="E06", object_id="O08", role="BOX_HEADER", script="CJK_FULLHEIGHT", bbox=(216.066, 141.646, 252.729, 150.812), declared="9.2", source_line="14", source_note="every node base"),
    dict(id="E07", object_id="O08", role="BOX_FORMULA", script="MATH_MIXED_WITH_SCRIPTS", bbox=(209.697, 152.303, 259.096, 162.738), declared="9.2", source_line="14", source_note="every node base"),
    dict(id="E08", object_id="O10", role="BOX_HEADER", script="CJK_FULLHEIGHT", bbox=(156.208, 181.024, 202.036, 190.190), declared="9.2", source_line="15", source_note="every node base"),
    dict(id="E09", object_id="O10", role="BOX_FORMULA", script="MATH_MIXED_WITH_SCRIPTS", bbox=(149.196, 191.681, 208.681, 202.117), declared="9.2", source_line="15", source_note="every node base"),
    dict(id="E10", object_id="O12", role="PANEL_TITLE", script="CJK_FULLHEIGHT", bbox=(365.353, 70.979, 497.458, 81.649), declared="10.2", source_line="20", source_note="title style"),
    dict(id="E11", object_id="O13", role="FORMULA_BASE", script="MATH_MIXED_WITH_SCRIPTS", bbox=(363.396, 92.984, 499.414, 105.725), declared="9.2", source_line="21", source_note="every node base"),
    dict(id="E12", object_id="O14", role="ARROW_GLYPH", script="MATH_SYMBOL", bbox=(425.667, 107.378, 437.144, 123.318), declared="16.0", source_line="22", source_note="explicit arrow font"),
    dict(id="E13", object_id="O15", role="FORMULA_BLOCK", script="MATH_FRACTION_WITH_SCRIPT", bbox=(422.934, 125.213, 439.876, 147.583), declared="9.2", source_line="23", source_note="every node base with display fraction"),
    dict(id="E14", object_id="O17", role="FORMULA_BLOCK", script="MATH_MIXED_WITH_SCRIPTS", bbox=(374.956, 159.304, 487.855, 169.740), declared="9.2", source_line="24-25", source_note="every node base"),
    dict(id="E15", object_id="O19", role="FORMULA_BLOCK", script="MATH_MIXED_WITH_SCRIPTS", bbox=(386.174, 201.257, 476.636, 211.693), declared="9.2", source_line="26-27", source_note="every node base"),
    dict(id="E16", object_id="O20", role="CAPTION_LABEL", script="CJK_LATIN_MIXED", bbox=(76.138, 226.811, 107.581, 237.272), declared="DOCUMENT_STYLE", source_line="31-32", source_note="caption style resolved in PDF"),
    dict(id="E17", object_id="O21", role="CAPTION_TEXT", script="CJK_MATH_MIXED", bbox=(117.544, 226.811, 507.792, 239.560), declared="DOCUMENT_STYLE", source_line="31-32", source_note="caption style resolved in PDF"),
    dict(id="E18", object_id="O22", role="CAPTION_TEXT", script="CJK_MATH_MIXED", bbox=(76.138, 240.201, 340.523, 252.950), declared="DOCUMENT_STYLE", source_line="31-32", source_note="caption style resolved in PDF"),
]


PARENT_CONTENT = {
    frozenset(("O05", "O06")): "BACKGROUND_CONTAINMENT",
    frozenset(("O07", "O08")): "BACKGROUND_CONTAINMENT",
    frozenset(("O09", "O10")): "BACKGROUND_CONTAINMENT",
    frozenset(("O16", "O17")): "BORDERED_PARENT_CONTENT",
    frozenset(("O18", "O19")): "BORDERED_PARENT_CONTENT",
    frozenset(("O21", "O22")): "SAME_CAPTION_PARAGRAPH",
}


def csv_write(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_labeled_box(draw: ImageDraw.ImageDraw, box, color, label, width=3):
    draw.rectangle(box, outline=color, width=width)
    x0, y0, _, _ = box
    tw = max(44, 10 + len(label) * 10)
    draw.rectangle((x0, max(0, y0 - 22), x0 + tw, y0), fill=color)
    draw.text((x0 + 4, max(0, y0 - 20)), label, fill=(255, 255, 255), font=font(16))


def local_ink_mask(gray: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(gray.shape[1], x1)
    y1 = min(gray.shape[0], y1)
    out = np.zeros_like(gray, dtype=bool)
    if x1 <= x0 or y1 <= y0:
        return out
    roi = gray[y0:y1, x0:x1]
    bg = float(np.percentile(roi, 95))
    local = roi <= (bg - 20.0)
    out[y0:y1, x0:x1] = local
    return out


def mask_bbox(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def bbox_relation(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    if ax0 <= bx0 and ay0 <= by0 and ax1 >= bx1 and ay1 >= by1:
        return "A_CONTAINS_B"
    if bx0 <= ax0 and by0 <= ay0 and bx1 >= ax1 and by1 >= ay1:
        return "B_CONTAINS_A"
    if ax1 > bx0 and bx1 > ax0 and ay1 > by0 and by1 > ay0:
        return "INTERSECTS"
    return "DISJOINT"


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def containment_margin(parent, child):
    px0, py0, px1, py1 = parent
    cx0, cy0, cx1, cy1 = child
    if px0 <= cx0 and py0 <= cy0 and px1 >= cx1 and py1 >= cy1:
        return float(min(cx0 - px0, cy0 - py0, px1 - cx1, py1 - cy1))
    return 0.0


def pair_threshold(a, b, relation):
    cats = {a["category"], b["category"]}
    textish = {"TEXT", "TEXT_FORMULA", "FORMULA"}
    if relation == "BORDERED_PARENT_CONTENT":
        return 5.0, "node content to node border"
    if relation in {"BACKGROUND_CONTAINMENT", "SAME_CAPTION_PARAGRAPH"}:
        return 0.0, "semantic grouping; no independent-object clearance rule"
    if a["panel"] in {"L", "R"} and b["panel"] in {"L", "R"} and a["panel"] != b["panel"]:
        return 8.0, "cross-panel reader objects"
    if a["category"] in textish and b["category"] in textish:
        return 4.0, "text-text bbox"
    if (a["category"] in textish) ^ (b["category"] in textish):
        other = b["category"] if a["category"] in textish else a["category"]
        if other in {"BRACE", "LINE_ARROW", "PANEL_BORDER", "NODE_BORDER"}:
            return 3.0, "text/formula to line-arrow-marker-border"
    return 0.0, "no independent foreground clearance rule"


def extracted_text(page, bbox):
    text = page.crop(bbox).extract_text(x_tolerance=1, y_tolerance=2) or ""
    return " ".join(text.replace("\n", " ⏎ ").split())


def make_object_masks(crop_gray: np.ndarray, crop_rgb: np.ndarray):
    masks = {}
    for obj in OBJECTS:
        box = page_to_crop_px(obj["bbox"])
        visible = local_ink_mask(crop_gray, box)
        collision = visible.copy()
        if obj["category"] == "BACKGROUND_CONTAINER":
            collision[:] = False
        elif obj["category"] == "NODE_BORDER":
            x0, y0, x1, y1 = box
            band = np.zeros_like(visible)
            band[max(0, y0):min(visible.shape[0], y0 + 8), max(0, x0):min(visible.shape[1], x1)] = True
            band[max(0, y1 - 8):min(visible.shape[0], y1), max(0, x0):min(visible.shape[1], x1)] = True
            band[max(0, y0):min(visible.shape[0], y1), max(0, x0):min(visible.shape[1], x0 + 8)] = True
            band[max(0, y0):min(visible.shape[0], y1), max(0, x1 - 8):min(visible.shape[1], x1)] = True
            collision &= band
        masks[obj["id"]] = dict(visible=visible, collision=collision)
    return masks


def save_bool_mask(mask: np.ndarray, path: Path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    masks_dir = ROOT / "masks"
    rois_dir = ROOT / "rois"
    masks_dir.mkdir(exist_ok=True)
    rois_dir.mkdir(exist_ok=True)

    pdf_bytes = PDF.stat().st_size
    source_bytes = SOURCE.stat().st_size
    pdf_sha = sha256(PDF)
    source_sha = sha256(SOURCE)
    if (pdf_bytes, pdf_sha) != (PDF_EXPECTED_BYTES, PDF_EXPECTED_SHA256):
        raise RuntimeError("official PDF identity mismatch")
    if (source_bytes, source_sha) != (SOURCE_EXPECTED_BYTES, SOURCE_EXPECTED_SHA256):
        raise RuntimeError("main figure source identity mismatch")

    full = Image.open(FULL_PAGE).convert("RGB")
    if full.size != (2481, 3508):
        raise RuntimeError(f"unexpected 300dpi full-page size: {full.size}")
    crop = full.crop(CROP_PAGE_PX)
    crop.save(ROOT / "figure_caption_native_300dpi.png")
    full.convert("L").save(ROOT / "full_page_grayscale_native_300dpi.png")
    crop_gray_img = crop.convert("L")
    crop_gray_img.save(ROOT / "figure_caption_grayscale_native_300dpi.png")
    figure_only_page_px = (CROP_X0, CROP_Y0, CROP_X1, math.ceil(222.0 * PX_PER_PT))
    full.crop(figure_only_page_px).save(ROOT / "figure_only_native_300dpi.png")

    location = full.copy()
    dloc = ImageDraw.Draw(location)
    dloc.rectangle(CROP_PAGE_PX, outline=(220, 20, 60), width=8)
    dloc.text((CROP_X0 + 8, CROP_Y0 + 8), "FIG-P665-01 figure+caption native crop", fill=(220, 20, 60), font=font(22))
    location.save(ROOT / "full_page_figure_location_overlay_300dpi.png")

    crop_arr = np.asarray(crop)
    gray = np.asarray(crop_gray_img)
    object_rows = []
    codepoint_rows = []
    with pdfplumber.open(PDF) as doc:
        page = doc.pages[PDF_PAGE_NUMBER_1BASED - 1]
        if abs(float(page.width) - 595.276) > 0.01 or abs(float(page.height) - 841.890) > 0.01:
            raise RuntimeError("unexpected PDF page geometry")
        for obj in OBJECTS:
            page_px = pt_to_page_px_box(obj["bbox"])
            crop_px = page_to_crop_px(obj["bbox"])
            text = extracted_text(page, obj["bbox"]) if obj["category"] in {"TEXT", "TEXT_FORMULA", "FORMULA", "LINE_ARROW"} else ""
            cps = " ".join(f"U+{ord(ch):04X}" for ch in text if not ch.isspace() and ch != "⏎")
            suspicious = sum(text.count(ch) for ch in ("�", "□", "▯", "�"))
            object_rows.append({
                "OBJECT_ID": obj["id"],
                "PANEL": obj["panel"],
                "CATEGORY": obj["category"],
                "ROLE": obj["role"],
                "SEMANTIC_LABEL": obj["label"],
                "EXPECTED_SEMANTICS": obj["expected"],
                "BBOX_PT_X0": obj["bbox"][0], "BBOX_PT_TOP": obj["bbox"][1], "BBOX_PT_X1": obj["bbox"][2], "BBOX_PT_BOTTOM": obj["bbox"][3],
                "PAGE_PX_X0": page_px[0], "PAGE_PX_Y0": page_px[1], "PAGE_PX_X1": page_px[2], "PAGE_PX_Y1": page_px[3],
                "CROP_PX_X0": crop_px[0], "CROP_PX_Y0": crop_px[1], "CROP_PX_X1": crop_px[2], "CROP_PX_Y1": crop_px[3],
                "EXTRACTED_TEXT": text,
            })
            codepoint_rows.append({
                "OBJECT_ID": obj["id"], "CATEGORY": obj["category"], "EXPECTED_SEMANTICS": obj["expected"],
                "EXTRACTED_TEXT": text, "EXTRACTED_CODEPOINTS": cps,
                "REPLACEMENT_OR_TOFU_CODEPOINT_COUNT": suspicious,
            })

        measure_rows = []
        heights_by_comparable_class = {}
        for m in MEASUREMENTS:
            box = page_to_crop_px(m["bbox"])
            mask = local_ink_mask(gray, box)
            ib = mask_bbox(mask)
            h = 0 if ib is None else ib[3] - ib[1]
            heights_by_comparable_class.setdefault((m["role"], m["script"]), []).append(h)
            chars = [c for c in page.chars if m["bbox"][0] <= (c["x0"] + c["x1"]) / 2 <= m["bbox"][2] and m["bbox"][1] <= (c["top"] + c["bottom"]) / 2 <= m["bbox"][3]]
            pdf_sizes = sorted({round(float(c["size"]), 6) for c in chars})
            measure_rows.append({
                "ELEMENT_ID": m["id"], "OBJECT_ID": m["object_id"], "ROLE": m["role"], "SCRIPT_CLASS": m["script"],
                "SOURCE_FILE": str(SOURCE), "SOURCE_LINE": m["source_line"], "DECLARED_PT": m["declared"], "GRAPHICS_SCALE": "1.0",
                "PDF_EXTRACTED_FONT_SIZES_PT": "|".join(str(v) for v in pdf_sizes), "SOURCE_NOTE": m["source_note"],
                "BBOX_X0": box[0], "BBOX_Y0": box[1], "BBOX_X1": box[2], "BBOX_Y1": box[3],
                "INK_BBOX_X0": "" if ib is None else ib[0], "INK_BBOX_Y0": "" if ib is None else ib[1],
                "INK_BBOX_X1": "" if ib is None else ib[2], "INK_BBOX_Y1": "" if ib is None else ib[3],
                "H_INK_PX": h,
            })
        medians = {key: float(np.median(vals)) for key, vals in heights_by_comparable_class.items()}
        for row in measure_rows:
            med = medians[(row["ROLE"], row["SCRIPT_CLASS"])]
            row["COMPARABLE_CLASS_MEDIAN_H_INK_PX"] = med
            row["RATIO_TO_COMPARABLE_CLASS_MEDIAN"] = "" if med == 0 else round(float(row["H_INK_PX"]) / med, 6)

    object_fields = list(object_rows[0].keys())
    csv_write(ROOT / "object_denominator_frozen.csv", object_rows, object_fields)
    csv_write(ROOT / "codepoint_audit_machine.csv", codepoint_rows, list(codepoint_rows[0].keys()))
    csv_write(ROOT / "pixel_measurements_machine.csv", measure_rows, list(measure_rows[0].keys()))
    font_rows = [{k: row[k] for k in ("ELEMENT_ID", "OBJECT_ID", "ROLE", "SCRIPT_CLASS", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "PDF_EXTRACTED_FONT_SIZES_PT", "SOURCE_NOTE")} for row in measure_rows]
    csv_write(ROOT / "source_font_audit_machine.csv", font_rows, list(font_rows[0].keys()))

    masks = make_object_masks(gray, crop_arr)
    text_union = np.zeros_like(gray, dtype=bool)
    geometry_union = np.zeros_like(gray, dtype=bool)
    visible_union = np.zeros_like(gray, dtype=bool)
    for obj in OBJECTS:
        mid = obj["id"]
        save_bool_mask(masks[mid]["collision"], masks_dir / f"{mid}_collision_mask.png")
        visible_union |= masks[mid]["visible"]
        if obj["category"] in {"TEXT", "TEXT_FORMULA", "FORMULA"}:
            text_union |= masks[mid]["collision"]
        if obj["category"] in {"BRACE", "LINE_ARROW", "PANEL_BORDER", "NODE_BORDER"}:
            geometry_union |= masks[mid]["collision"]
    save_bool_mask(visible_union, ROOT / "visible_object_union_mask_300dpi.png")
    save_bool_mask(text_union, ROOT / "text_union_mask_300dpi.png")
    save_bool_mask(geometry_union, ROOT / "geometry_union_mask_300dpi.png")

    pair_rows = []
    for a, b in itertools.combinations(OBJECTS, 2):
        aid, bid = a["id"], b["id"]
        abox, bbox = page_to_crop_px(a["bbox"]), page_to_crop_px(b["bbox"])
        relation = PARENT_CONTENT.get(frozenset((aid, bid)), "INDEPENDENT")
        geom_relation = bbox_relation(abox, bbox)
        threshold, rule = pair_threshold(a, b, relation)
        if relation == "BORDERED_PARENT_CONTENT":
            parent, child = (abox, bbox) if a["category"] == "NODE_BORDER" else (bbox, abox)
            clearance = containment_margin(parent, child)
        elif relation == "BACKGROUND_CONTAINMENT":
            parent, child = (abox, bbox) if a["category"] == "BACKGROUND_CONTAINER" else (bbox, abox)
            clearance = containment_margin(parent, child)
        elif relation == "SAME_CAPTION_PARAGRAPH":
            clearance = bbox_gap(abox, bbox)
        else:
            clearance = bbox_gap(abox, bbox)
        overlap_px = int(np.count_nonzero(masks[aid]["collision"] & masks[bid]["collision"]))
        delta = float(clearance) - threshold
        machine_risk = "MASK_OVERLAP_CANDIDATE" if overlap_px else ("NUMERIC_CLEARANCE_RISK" if delta < 0 else "")
        pair_rows.append({
            "PAIR_ID": f"P-{aid}-{bid}", "OBJECT_A": aid, "OBJECT_B": bid,
            "CATEGORY_A": a["category"], "CATEGORY_B": b["category"],
            "PANEL_A": a["panel"], "PANEL_B": b["panel"],
            "SEMANTIC_RELATION": relation, "BBOX_RELATION": geom_relation,
            "COLLISION_MASK_OVERLAP_PX": overlap_px,
            "CLEARANCE_METRIC_PX": round(clearance, 6), "RULE_THRESHOLD_PX": threshold,
            "DISTANCE_MINUS_RULE_PX": round(delta, 6), "RULE_BASIS": rule,
            "MACHINE_RISK_TRIGGER": machine_risk,
        })
    csv_write(ROOT / "all_unordered_pairs_machine.csv", pair_rows, list(pair_rows[0].keys()))

    clip_rows = []
    h, w = gray.shape
    for obj in OBJECTS:
        box = page_to_crop_px(obj["bbox"])
        visible = masks[obj["id"]]["visible"]
        edge = np.zeros_like(visible)
        edge[:2, :] = True; edge[-2:, :] = True; edge[:, :2] = True; edge[:, -2:] = True
        touch = int(np.count_nonzero(visible & edge))
        bx0, by0, bx1, by1 = box
        page_box = pt_to_page_px_box(obj["bbox"])
        outside_page_bbox_px = max(0, -page_box[0]) + max(0, -page_box[1]) + max(0, page_box[2] - full.width) + max(0, page_box[3] - full.height)
        clip_rows.append({
            "OBJECT_ID": obj["id"], "VISIBLE_MASK_PIXELS": int(np.count_nonzero(visible)),
            "VISIBLE_MASK_TOUCH_CROP_EDGE_2PX": touch,
            "BBOX_MARGIN_LEFT_CROP_PX": bx0, "BBOX_MARGIN_TOP_CROP_PX": by0,
            "BBOX_MARGIN_RIGHT_CROP_PX": w - bx1, "BBOX_MARGIN_BOTTOM_CROP_PX": h - by1,
            "BBOX_OUTSIDE_FULL_PAGE_PX_SUM": outside_page_bbox_px,
        })
    csv_write(ROOT / "clip_check_machine.csv", clip_rows, list(clip_rows[0].keys()))

    colors = {
        "TEXT": (25, 110, 210), "TEXT_FORMULA": (10, 150, 150), "FORMULA": (140, 60, 200),
        "BRACE": (235, 150, 0), "BACKGROUND_CONTAINER": (120, 120, 120), "PANEL_BORDER": (0, 0, 0),
        "LINE_ARROW": (230, 80, 30), "NODE_BORDER": (190, 30, 80),
    }
    bbox_overlay = crop.copy()
    db = ImageDraw.Draw(bbox_overlay)
    for obj in OBJECTS:
        draw_labeled_box(db, page_to_crop_px(obj["bbox"]), colors[obj["category"]], obj["id"], width=3)
    bbox_overlay.save(ROOT / "object_bbox_overlay_300dpi.png")

    semantic_rgba = crop.convert("RGBA")
    layer = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(layer)
    for obj in OBJECTS:
        c = colors[obj["category"]]
        box = page_to_crop_px(obj["bbox"])
        ds.rectangle(box, fill=(*c, 30), outline=(*c, 220), width=3)
        ds.text((box[0] + 3, box[1] + 3), f"{obj['id']} {obj['role']}", fill=(*c, 255), font=font(14))
    Image.alpha_composite(semantic_rgba, layer).convert("RGB").save(ROOT / "semantic_role_overlay_300dpi.png")

    measure_overlay = crop.copy()
    dm = ImageDraw.Draw(measure_overlay)
    for row, m in zip(measure_rows, MEASUREMENTS):
        box = page_to_crop_px(m["bbox"])
        draw_labeled_box(dm, box, (0, 135, 70), f"{m['id']} h={row['H_INK_PX']}px", width=2)
    measure_overlay.save(ROOT / "text_measurement_overlay_300dpi.png")

    order_groups = [
        ["O01", "O02", "O04", "O06", "O08", "O10"],
        ["O12", "O13", "O14", "O15", "O17", "O19"],
        ["O20", "O21", "O22"],
    ]
    obj_map = {o["id"]: o for o in OBJECTS}
    order_overlay = crop.copy()
    do = ImageDraw.Draw(order_overlay)
    do.rectangle((610, 3, 1315, 31), fill=(255, 255, 255))
    do.text((620, 6), "READ: LEFT 1-6  ->  RIGHT 7-12  ->  CAPTION 13-15", fill=(170, 70, 0), font=font(18))
    n = 0
    for group_index, group in enumerate(order_groups):
        centers = []
        for oid in group:
            n += 1
            box = page_to_crop_px(obj_map[oid]["bbox"])
            center = ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
            centers.append(center)
            r = 16
            do.ellipse((center[0]-r, center[1]-r, center[0]+r, center[1]+r), fill=(255, 235, 60), outline=(70, 50, 0), width=2)
            do.text((center[0]-7, center[1]-10), str(n), fill=(30, 25, 0), font=font(14))
        if group_index == 2:
            continue
        for p0, p1 in zip(centers, centers[1:]):
            do.line((p0, p1), fill=(220, 90, 0), width=4)
            ang = math.atan2(p1[1]-p0[1], p1[0]-p0[0])
            head = 12
            for da in (2.55, -2.55):
                q = (p1[0] + int(head * math.cos(ang + da)), p1[1] + int(head * math.sin(ang + da)))
                do.line((p1, q), fill=(220, 90, 0), width=4)
    order_overlay.save(ROOT / "reading_order_overlay_300dpi.png")

    closest = min((r for r in pair_rows if r["RULE_THRESHOLD_PX"] > 0), key=lambda r: r["DISTANCE_MINUS_RULE_PX"])
    clear_overlay = crop.copy()
    dc = ImageDraw.Draw(clear_overlay)
    for oid in (closest["OBJECT_A"], closest["OBJECT_B"]):
        draw_labeled_box(dc, page_to_crop_px(obj_map[oid]["bbox"]), (230, 120, 0), oid, width=4)
    dc.text((20, crop.height - 40), f"closest numeric rule margin: {closest['PAIR_ID']} delta={closest['DISTANCE_MINUS_RULE_PX']} px", fill=(180, 60, 0), font=font(18))
    clear_overlay.save(ROOT / "closest_pair_numeric_risk_overlay_300dpi.png")

    roi_specs = [
        ("R01_brace_note", (70.0, 104.0, 286.0, 132.0)),
        ("R02_left_term_content", (84.0, 134.0, 266.0, 207.0)),
        ("R03_right_derivation", (355.0, 88.0, 506.0, 184.0)),
        ("R04_warning_formula", (350.0, 187.0, 513.0, 222.0)),
        ("R05_caption_math", (72.0, 223.0, 514.0, 256.0)),
    ]
    roi_rows = []
    for rid, ptbox in roi_specs:
        page_box = pt_to_page_px_box(ptbox)
        one = full.crop(page_box)
        one_path = rois_dir / f"{rid}_native1x.png"
        eight_path = rois_dir / f"{rid}_nearest8x.png"
        one.save(one_path)
        eight = one.resize((one.width * 8, one.height * 8), resample=Image.Resampling.NEAREST)
        eight.save(eight_path)
        roi_rows.append({
            "ROI_ID": rid, "SOURCE_VIEW": "full_page_300dpi.png", "PAGE_PX_X0": page_box[0], "PAGE_PX_Y0": page_box[1],
            "PAGE_PX_X1": page_box[2], "PAGE_PX_Y1": page_box[3], "NATIVE_WIDTH": one.width, "NATIVE_HEIGHT": one.height,
            "NEAREST_SCALE": 8, "NATIVE_PATH": str(one_path.relative_to(ROOT)), "NEAREST8X_PATH": str(eight_path.relative_to(ROOT)),
        })
    csv_write(ROOT / "risk_roi_index_machine.csv", roi_rows, list(roi_rows[0].keys()))

    metadata = {
        "handoff_id": "C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1",
        "uid": "FIG-P665-01",
        "official_pdf": {"path": str(PDF), "bytes": pdf_bytes, "sha256": pdf_sha},
        "main_source": {"path": str(SOURCE), "bytes": source_bytes, "sha256": source_sha},
        "located_physical_pdf_page_1based": PDF_PAGE_NUMBER_1BASED,
        "page_size_pt": [595.276, 841.890],
        "full_page_native_300dpi_px": list(full.size),
        "figure_caption_crop_pt": list(CROP_PT),
        "figure_caption_crop_page_px": list(CROP_PAGE_PX),
        "figure_caption_native_300dpi_px": list(crop.size),
        "visible_object_denominator": len(OBJECTS),
        "all_unordered_pairs": len(pair_rows),
        "formula_n_choose_2": len(OBJECTS) * (len(OBJECTS) - 1) // 2,
        "machine_mask_overlap_pair_count": sum(1 for r in pair_rows if r["COLLISION_MASK_OVERLAP_PX"] > 0),
        "machine_numeric_clearance_risk_pair_count": sum(1 for r in pair_rows if r["MACHINE_RISK_TRIGGER"] == "NUMERIC_CLEARANCE_RISK"),
        "replacement_or_tofu_codepoint_count": sum(r["REPLACEMENT_OR_TOFU_CODEPOINT_COUNT"] for r in codepoint_rows),
        "clip_crop_edge_touch_object_count": sum(1 for r in clip_rows if r["VISIBLE_MASK_TOUCH_CROP_EDGE_2PX"] > 0),
        "manual_fields_generated_by_script": 0,
        "global_pass_booleans_generated_by_script": 0,
    }
    (ROOT / "machine_evidence_summary.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "input_identity_machine.txt").write_text(
        "\n".join([
            "HANDOFF_ID=C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1",
            "UID=FIG-P665-01",
            f"PDF_PATH={PDF}", f"PDF_BYTES={pdf_bytes}", f"PDF_SHA256={pdf_sha}",
            f"SOURCE_PATH={SOURCE}", f"SOURCE_BYTES={source_bytes}", f"SOURCE_SHA256={source_sha}",
            f"LOCATED_PHYSICAL_PDF_PAGE_1BASED={PDF_PAGE_NUMBER_1BASED}",
            "LOCATION_BASIS=current source/caption semantics independently matched in official R113 PDF text and page raster",
            "",
        ]), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
