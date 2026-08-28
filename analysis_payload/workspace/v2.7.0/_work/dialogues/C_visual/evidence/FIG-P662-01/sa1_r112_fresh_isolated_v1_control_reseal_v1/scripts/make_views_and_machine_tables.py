from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa1_r112_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf")
PAGE_INDEX = 709
SCALE = 300.0 / 72.0


# PDF coordinates use x from the left and top/bottom from the top.
TEXT_ELEMENTS = [
    ("T01", "INPUT_FORMULA", "Y_1~Gamma(alpha_1,lambda)", 92.0, 289.8, 178.5, 301.5),
    ("T02", "INPUT_FORMULA", "Y_2~Gamma(alpha_2,lambda)", 92.0, 318.2, 178.5, 329.8),
    ("T03", "ELLIPSIS", "vertical ellipsis", 131.0, 334.7, 140.0, 348.7),
    ("T04", "INPUT_FORMULA", "Y_K~Gamma(alpha_K,lambda)", 90.0, 358.7, 181.0, 370.4),
    ("T05", "BADGE_TEXT", "1", 132.4, 264.0, 138.3, 274.3),
    ("T06", "NOTE", "independent, common rate lambda", 88.3, 382.1, 182.4, 393.0),
    ("T07", "NODE_TITLE", "total", 224.5, 314.4, 245.0, 325.4),
    ("T08", "NODE_FORMULA", "S=sum_k Y_k", 206.7, 322.9, 262.1, 340.4),
    ("T09", "BADGE_TEXT", "2", 231.6, 288.4, 237.5, 298.8),
    ("T10", "OPERATOR_FORMULA", "divide by S", 303.9, 321.5, 318.2, 332.7),
    ("T11", "BADGE_TEXT", "3", 308.1, 288.3, 314.0, 298.8),
    ("T12", "NODE_TITLE", "ratio", 367.8, 316.2, 388.3, 327.3),
    ("T13", "NODE_FORMULA", "Theta_k=Y_k/S", 354.1, 326.8, 401.7, 339.2),
    ("T14", "RESULT_FORMULA", "Theta~Dir(alpha)", 449.8, 314.2, 498.5, 325.4),
    ("T15", "RESULT_FORMULA", "sum_k Theta_k=1", 450.6, 325.2, 497.7, 340.0),
    ("T16", "NOTE", "simplex point", 485.1, 287.7, 521.0, 298.2),
    ("T17", "RESULT_FORMULA", "S independent Theta; S~Gamma(alpha_0,lambda)", 271.4, 372.7, 390.5, 385.3),
    ("T18", "SPECIAL_CASE_TITLE", "K=2 special case", 429.3, 367.7, 485.9, 379.2),
    ("T19", "SPECIAL_CASE_FORMULA", "Theta_1~Beta(alpha_1,alpha_2)", 429.3, 378.7, 504.8, 391.2),
    ("T20", "CAPTION_LABEL", "Figure 34.5", 86.5, 398.3, 119.0, 410.9),
    ("T21", "CAPTION_BODY", "Gamma normalization caption", 126.5, 398.3, 520.2, 424.1),
]


# Composite semantic objects. Each node includes its border/fill and its internal text.
OBJECTS = [
    ("O01", "INPUT_NODE", "Y1 input node", 88.16, 283.05, 182.64, 307.14),
    ("O02", "INPUT_NODE", "Y2 input node", 88.17, 311.40, 182.63, 335.49),
    ("O03", "ELLIPSIS", "input continuation", 131.0, 334.7, 140.0, 348.7),
    ("O04", "INPUT_NODE", "YK input node", 85.73, 351.93, 185.07, 376.03),
    ("O05", "BADGE", "step badge 1", 127.46, 260.80, 143.34, 276.67),
    ("O06", "NOTE", "common-rate independence note", 88.3, 382.1, 182.4, 393.0),
    ("O07", "CALC_NODE", "sum node", 197.76, 310.59, 271.46, 341.96),
    ("O08", "BADGE", "step badge 2", 226.68, 285.18, 242.55, 301.05),
    ("O09", "OPERATOR_NODE", "divide-by-S node", 296.97, 312.10, 325.32, 340.45),
    ("O10", "RESULT_NODE", "ratio node", 336.94, 310.69, 419.15, 341.87),
    ("O11", "BADGE", "step badge 3", 303.21, 285.18, 319.09, 301.05),
    ("O12", "RESULT_NODE", "Dirichlet result node", 431.62, 310.69, 516.66, 341.87),
    ("O13", "SIMPLEX_ICON", "simplex triangle and point", 461.39, 280.64, 486.90, 302.75),
    ("O14", "NOTE", "simplex point note", 485.1, 287.7, 521.0, 298.2),
    ("O15", "RESULT_NODE", "independence result node", 261.54, 363.98, 400.44, 392.33),
    ("O16", "SPECIAL_CASE_NODE", "K=2 beta node", 413.20, 363.98, 520.91, 392.33),
    ("O17", "MAIN_ARROW", "Y1 to sum", 182.96, 295.10, 196.76, 316.75),
    ("O18", "MAIN_ARROW", "Y2 to sum", 182.95, 323.44, 196.22, 326.59),
    ("O19", "MAIN_ARROW", "YK to sum", 185.40, 335.91, 196.95, 363.98),
    ("O20", "MAIN_ARROW", "sum to divide", 271.81, 325.06, 295.41, 327.50),
    ("O21", "MAIN_ARROW", "divide to ratio", 325.67, 325.06, 335.38, 327.50),
    ("O22", "MAIN_ARROW", "ratio to Dirichlet", 419.50, 325.06, 430.06, 327.50),
    ("O23", "AUX_PATH", "sum to independence evidence path", 234.61, 342.22, 291.31, 364.1),
    ("O24", "AUX_PATH", "ratio to independence evidence path", 370.68, 342.22, 378.05, 364.1),
    ("O25", "CAPTION", "caption label and body", 86.5, 398.3, 520.2, 424.1),
]


def px_box(box):
    _, _, _, x0, top, x1, bottom = box
    return tuple(round(v * SCALE) for v in (x0, top, x1, bottom))


def nearest_distance(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return (dx * dx + dy * dy) ** 0.5


def ink_height(img, box, inverted=False):
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - 2)
    y0 = max(0, y0 - 2)
    x1 = min(img.width, x1 + 2)
    y1 = min(img.height, y1 + 2)
    g = ImageOps.grayscale(img.crop((x0, y0, x1, y1)))
    pix = g.load()
    rows = []
    for y in range(g.height):
        present = False
        for x in range(g.width):
            v = pix[x, y]
            if (v >= 210 if inverted else v <= 220):
                present = True
                break
        if present:
            rows.append(y)
    return (max(rows) - min(rows) + 1) if rows else 0


def main():
    page_png = ROOT / "native" / "r112_physical_0710_page_300dpi.png"
    page = Image.open(page_png).convert("RGB")
    internal_box = (330, 1070, 2205, 1655)
    subject_box = (330, 1070, 2205, 1780)
    internal = page.crop(internal_box)
    subject = page.crop(subject_box)
    internal.save(ROOT / "native" / "figure_internal_300dpi_native1x.png")
    subject.save(ROOT / "native" / "figure_with_caption_300dpi_native1x.png")
    ImageOps.grayscale(subject).save(ROOT / "views" / "figure_with_caption_grayscale_300dpi.png")

    risks = {
        "risk_input_scripts": (360, 1190, 780, 1560),
        "risk_common_rate_note": (355, 1575, 785, 1660),
        "risk_sum_formula": (815, 1280, 1110, 1435),
        "risk_divide_ratio": (1215, 1260, 1705, 1440),
        "risk_dirichlet_simplex": (1800, 1150, 2195, 1445),
        "risk_lower_results": (1070, 1505, 2185, 1655),
    }
    for name, box in risks.items():
        roi = page.crop(box)
        roi.save(ROOT / "roi" / f"{name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
            ROOT / "roi" / f"{name}_nearest8x.png"
        )

    try:
        font = ImageFont.truetype("arial.ttf", 22)
        small = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
        small = font

    text_overlay = page.copy()
    d = ImageDraw.Draw(text_overlay)
    text_rows = []
    for element in TEXT_ELEMENTS:
        eid, role, sample, x0, top, x1, bottom = element
        box = px_box(element)
        d.rectangle(box, outline=(220, 25, 25), width=3)
        d.text((box[0], max(0, box[1] - 24)), eid, fill=(220, 25, 25), font=font)
        height = ink_height(page, box, inverted=(role == "BADGE_TEXT"))
        text_rows.append(
            {
                "ELEMENT_ID": eid,
                "ROLE": role,
                "TEXT_SAMPLE": sample,
                "BBOX_X0": box[0],
                "BBOX_Y0": box[1],
                "BBOX_X1": box[2],
                "BBOX_Y1": box[3],
                "H_INK_PX_MACHINE": height,
            }
        )
    text_overlay.crop(subject_box).save(ROOT / "overlays" / "text_measurement_overlay_300dpi.png")

    object_overlay = page.copy()
    d = ImageDraw.Draw(object_overlay)
    obj_rows = []
    for obj in OBJECTS:
        oid, role, desc, x0, top, x1, bottom = obj
        box = px_box(obj)
        color = (25, 100, 220) if role not in {"MAIN_ARROW", "AUX_PATH"} else (220, 120, 20)
        d.rectangle(box, outline=color, width=3)
        d.text((box[0], max(0, box[1] - 22)), oid, fill=color, font=small)
        obj_rows.append(
            {
                "OBJECT_ID": oid,
                "ROLE": role,
                "DESCRIPTION": desc,
                "BBOX_X0": box[0],
                "BBOX_Y0": box[1],
                "BBOX_X1": box[2],
                "BBOX_Y1": box[3],
            }
        )
    object_overlay.crop(subject_box).save(ROOT / "overlays" / "visible_object_overlay_300dpi.png")

    semantic_overlay = subject.copy()
    d = ImageDraw.Draw(semantic_overlay)
    bands = [
        ("INPUTS", (30, 110, 80), (25, 170, 875, 565)),
        ("TRANSFORM", (30, 70, 180), (490, 185, 1420, 580)),
        ("OUTPUT", (150, 80, 20), (1250, 155, 1865, 585)),
        ("CONSEQUENCES", (100, 40, 140), (720, 470, 1870, 600)),
        ("CAPTION", (80, 80, 80), (25, 585, 1870, 710)),
    ]
    for label, color, box in bands:
        d.rectangle(box, outline=color, width=5)
        d.text((box[0] + 6, box[1] + 6), label, fill=color, font=font)
    semantic_overlay.save(ROOT / "overlays" / "semantic_reading_order_overlay_300dpi.png")

    with (ROOT / "ledgers" / "machine_text_measurements.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(text_rows[0]))
        w.writeheader()
        w.writerows(text_rows)

    with (ROOT / "ledgers" / "visible_object_denominator.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(obj_rows[0]))
        w.writeheader()
        w.writerows(obj_rows)

    pairs = []
    by_id = {row["OBJECT_ID"]: row for row in obj_rows}
    for idx, (a, b) in enumerate(itertools.combinations([o[0] for o in OBJECTS], 2), 1):
        ra, rb = by_id[a], by_id[b]
        ba = (ra["BBOX_X0"], ra["BBOX_Y0"], ra["BBOX_X1"], ra["BBOX_Y1"])
        bb = (rb["BBOX_X0"], rb["BBOX_Y0"], rb["BBOX_X1"], rb["BBOX_Y1"])
        pairs.append(
            {
                "PAIR_ID": f"P{idx:03d}",
                "OBJECT_A": a,
                "OBJECT_B": b,
                "BBOX_NEAREST_DISTANCE_PX_MACHINE": f"{nearest_distance(ba, bb):.2f}",
            }
        )
    with (ROOT / "ledgers" / "machine_all_unordered_pairs.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pairs[0]))
        w.writeheader()
        w.writerows(pairs)

    with pdfplumber.open(PDF) as pdf:
        pg = pdf.pages[PAGE_INDEX]
        words = pg.extract_words(x_tolerance=1, y_tolerance=2, extra_attrs=["fontname", "size"])
        selected = [w for w in words if 250 <= w["top"] <= 430 and w["x1"] >= 80 and w["x0"] <= 530]
        vectors = {
            "page_width_pt": pg.width,
            "page_height_pt": pg.height,
            "physical_page": PAGE_INDEX + 1,
            "words": selected,
            "lines": [o for o in pg.lines if o.get("bottom", 0) >= 250 and o.get("top", 999) <= 430 and o.get("x1", 0) >= 80 and o.get("x0", 999) <= 530],
            "curves": [o for o in pg.curves if o.get("bottom", 0) >= 250 and o.get("top", 999) <= 430 and o.get("x1", 0) >= 80 and o.get("x0", 999) <= 530],
        }
    (ROOT / "source_identity" / "r112_page0710_vector_extract.json").write_text(
        json.dumps(vectors, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    summary = {
        "physical_page": 710,
        "printed_page": 697,
        "page_png_px": [page.width, page.height],
        "figure_internal_crop_px": internal_box,
        "figure_with_caption_crop_px": subject_box,
        "visible_object_denominator": len(OBJECTS),
        "all_unordered_pairs": len(pairs),
        "text_element_denominator": len(TEXT_ELEMENTS),
        "risk_roi_count": len(risks),
    }
    (ROOT / "controls" / "machine_generation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
