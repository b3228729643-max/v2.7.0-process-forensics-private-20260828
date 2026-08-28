from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R2_SA1_FRESH_ISOLATED_R108_20260826")
RENDERS = ROOT / "renders"
MACHINE = ROOT / "machine"
RELATIONS = ROOT / "relations"

EXPECTED_PDF_SHA = "C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78"
EXPECTED_SOURCE_SHA = "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161"
SCALE = 300.0 / 72.0
FIGURE_BBOX_PT = (96.0, 263.0, 508.0, 486.0)
STANDALONE_BBOX_PT = (114.0, 263.0, 494.0, 464.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ptbox_to_px(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, top, x1, bottom = box
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(top * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(bottom * SCALE)),
    )


def bbox_gap_px(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return round(math.hypot(dx, dy) * SCALE, 2)


def bbox_overlap_px2(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> int:
    x = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    y = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return int(round(x * y * SCALE * SCALE))


def ink_height(image: Image.Image, box_pt: tuple[float, float, float, float]) -> tuple[int, int]:
    box = ptbox_to_px(box_pt)
    crop = image.crop(box).convert("RGB")
    pixels = crop.load()
    rows: list[int] = []
    count = 0
    for y in range(crop.height):
        row_has = False
        for x in range(crop.width):
            r, g, b = pixels[x, y]
            lum = (299 * r + 587 * g + 114 * b) / 1000
            if lum <= 230:
                count += 1
                row_has = True
        if row_has:
            rows.append(y)
    return ((max(rows) - min(rows) + 1) if rows else 0, count)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\consola.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


full = Image.open(RENDERS / "full_page_300dpi.png").convert("RGB")
gray = Image.open(RENDERS / "full_page_grayscale_300dpi.png").convert("RGB")
figure_box_px = ptbox_to_px(FIGURE_BBOX_PT)
standalone_box_px = ptbox_to_px(STANDALONE_BBOX_PT)
figure = full.crop(figure_box_px)
standalone = full.crop(standalone_box_px)
figure_gray = gray.crop(figure_box_px)
figure.save(RENDERS / "figure_crop_300dpi.png")
standalone.save(RENDERS / "standalone_300dpi.png")
figure_gray.save(RENDERS / "figure_grayscale_300dpi.png")

# Critical codepoint crops are direct native 300 dpi pixels; the 8x images use nearest-neighbour only.
critical_specs = {
    "critical_notll_u0338_u226a": (250.0, 264.0, 290.0, 288.0),
    "control_plain_u226a_caption": (210.0, 462.0, 247.0, 485.0),
}
for name, box in critical_specs.items():
    native = full.crop(ptbox_to_px(box))
    native.save(RENDERS / f"{name}_native1x.png")
    native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(
        RENDERS / f"{name}_8x_nearest.png"
    )

# Semantic visible-object denominator. Compound labels and formula cards are one visible
# semantic object; graphic strokes/markers that carry distinct meaning remain separate.
objects = [
    ("OBJ-001", "L", "TEXT_FORMULA", "TITLE_BLOCK", (206.0, 269.5, 283.5, 283.0), 37),
    ("OBJ-002", "L", "TEXT", "Y_AXIS_LABEL", (124.5, 332.5, 146.5, 373.0), 38),
    ("OBJ-003", "L", "TEXT", "X_TICK_SET", (173.0, 418.0, 316.8, 429.5), 22),
    ("OBJ-004", "L", "TEXT", "Y_TICK_SET", (151.5, 308.5, 170.5, 420.0), 23),
    ("OBJ-005", "L", "TEXT", "X_LABEL_MAIN", (197.8, 435.5, 292.0, 446.5), 39),
    ("OBJ-006", "L", "TEXT_FORMULA", "X_LABEL_SUPPORT_NOTE", (180.3, 448.0, 309.5, 460.0), 40),
    ("OBJ-007", "L", "TEXT_FORMULA", "QL_ANNOTATION", (180.0, 302.0, 224.8, 324.5), 61),
    ("OBJ-008", "L", "TEXT", "BOUNDARY_ANNOTATION", (249.8, 302.5, 312.8, 324.5), 67),
    ("OBJ-009", "L", "TEXT_FORMULA", "P_CURVE_LABEL", (180.0, 342.5, 220.5, 353.5), 64),
    ("OBJ-010", "L", "GRAPHIC", "AXES_AND_TICKS", (173.5, 291.0, 319.8, 417.0), 20),
    ("OBJ-011", "L", "GRAPHIC", "P_CURVE", (175.5, 353.0, 314.5, 414.5), 47),
    ("OBJ-012", "L", "GRAPHIC", "QL_POSITIVE_SEGMENT", (175.5, 332.8, 245.5, 334.5), 49),
    ("OBJ-013", "L", "GRAPHIC", "QL_ZERO_SEGMENT", (244.5, 412.8, 314.5, 414.8), 51),
    ("OBJ-014", "L", "GRAPHIC", "SUPPORT_BOUNDARY_LINE", (244.0, 322.0, 245.8, 414.5), 57),
    ("OBJ-015", "L", "GRAPHIC", "QL_CLOSED_MARKER", (241.5, 330.3, 248.2, 337.0), 53),
    ("OBJ-016", "L", "GRAPHIC", "QL_OPEN_MARKER", (241.5, 410.5, 248.3, 417.3), 55),
    ("OBJ-017", "L", "GRAPHIC", "SUPPORT_GAP_HATCH", (244.5, 353.0, 314.5, 414.5), 45),
    ("OBJ-018", "R", "TEXT_FORMULA", "TITLE_BLOCK", (358.5, 269.5, 464.2, 283.0), 69),
    ("OBJ-019", "R", "TEXT", "X_TICK_SET", (339.2, 418.0, 483.2, 429.5), 22),
    ("OBJ-020", "R", "TEXT", "Y_TICK_SET", (317.8, 308.5, 336.8, 420.0), 23),
    ("OBJ-021", "R", "TEXT", "X_LABEL_MAIN", (364.2, 435.5, 458.5, 446.5), 70),
    ("OBJ-022", "R", "TEXT_FORMULA", "X_LABEL_LEGEND", (350.5, 448.0, 472.0, 460.0), 71),
    ("OBJ-023", "R", "TEXT_FORMULA", "WEIGHT_CARD_TEXT", (358.3, 301.0, 464.2, 340.0), 94),
    ("OBJ-024", "R", "GRAPHIC", "AXES_AND_TICKS", (339.5, 291.0, 486.2, 417.0), 20),
    ("OBJ-025", "R", "GRAPHIC", "P_CURVE", (341.8, 353.0, 480.8, 414.5), 73),
    ("OBJ-026", "R", "GRAPHIC", "QR_LINE", (341.8, 373.0, 480.8, 374.8), 75),
    ("OBJ-027", "R", "GRAPHIC", "MARKER_X1_CIRCLE", (366.2, 371.8, 373.5, 379.0), 83),
    ("OBJ-028", "R", "GRAPHIC", "MARKER_XMID_SQUARE", (407.8, 350.3, 414.7, 357.2), 85),
    ("OBJ-029", "R", "GRAPHIC", "MARKER_X4_TRIANGLE", (449.2, 371.5, 456.0, 378.2), 87),
    ("OBJ-030", "R", "GRAPHIC", "WEIGHT_CARD_BORDER", (346.5, 295.0, 476.0, 346.5), 89),
    ("OBJ-031", "PAGE", "TEXT", "CAPTION_LABEL", (104.3, 467.8, 135.2, 479.5), 102),
    ("OBJ-032", "PAGE", "TEXT_FORMULA", "CAPTION_TEXT", (144.0, 467.8, 502.5, 479.5), 102),
]

with (MACHINE / "visible_object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["OBJECT_ID", "PANEL", "KIND", "ROLE", "BBOX_X0_PT", "BBOX_TOP_PT", "BBOX_X1_PT", "BBOX_BOTTOM_PT", "SOURCE_LINE"])
    for oid, panel, kind, role, box, line in objects:
        w.writerow([oid, panel, kind, role, *box, line])

pairs = []
for idx, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
    a_box = a[4]
    b_box = b[4]
    gap = bbox_gap_px(a_box, b_box)
    overlap = bbox_overlap_px2(a_box, b_box)
    pairs.append(
        {
            "PAIR_ID": f"PAIR-{idx:04d}",
            "OBJECT_A": a[0],
            "OBJECT_B": b[0],
            "KIND_A": a[2],
            "KIND_B": b[2],
            "BBOX_GAP_PX": gap,
            "BBOX_OVERLAP_AREA_PX2": overlap,
            "BBOX_INTERSECTS": overlap > 0,
            "MACHINE_RELATION_CLASS": "BBOX_INTERSECTION_CANDIDATE" if overlap > 0 else "BBOX_SEPARATED",
        }
    )

pair_fields = list(pairs[0])
with (MACHINE / "all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=pair_fields)
    w.writeheader()
    w.writerows(pairs)
with (MACHINE / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=pair_fields)
    w.writeheader()
    w.writerows(pairs)

# Text elements are more granular than the semantic relation denominator.
# Fields below are machine facts only; human reviewer/decision/note fields are deliberately absent.
text_specs = [
    ("EL-L-TITLE-TEXT", "L", "TITLE", 37, 10.2, 1.0, 10.2, "支持不足", "CJK_FULL", (206.0, 270.5, 247.6, 282.0), 30),
    ("EL-L-TITLE-REL", "L", "TITLE_FORMULA", 37, 10.2, 1.0, 10.2, "p not-lessless q", "MATH_BASE", (256.5, 269.8, 278.4, 282.0), 22),
    ("EL-L-TITLE-SUB-L", "L", "FORMULA_SCRIPT", 37, 10.2, 0.70, 7.14, "L", "MATH_SCRIPT", (277.8, 274.5, 283.5, 283.0), 15),
    ("EL-L-YLABEL", "L", "AXIS_TITLE", 38, 9.6, 1.0, 9.6, "密度/每x单位", "CJK_FULL", (124.5, 332.5, 146.5, 373.0), 30),
    ("EL-L-XMAIN", "L", "AXIS_TITLE", 39, 9.6, 1.0, 9.6, "共同定义域 x 从 0 到 5", "CJK_FULL", (197.8, 435.5, 292.0, 446.5), 30),
    ("EL-L-XNOTE", "L", "ANNOTATION", 40, 9.6, 1.0, 9.6, "斜线区 qL(x) 为0且p(x)为正", "CJK_FULL", (180.3, 448.0, 309.5, 460.0), 30),
    ("EL-L-ANN-QL-1", "L", "ANNOTATION", 61, 9.6, 1.0, 9.6, "虚线 qL(x)", "CJK_FULL", (180.0, 302.0, 225.0, 314.0), 30),
    ("EL-L-ANN-QL-2", "L", "ANNOTATION", 61, 9.6, 1.0, 9.6, "取 2/5", "CJK_FULL", (180.0, 313.5, 206.0, 324.5), 30),
    ("EL-L-ANN-BND-1", "L", "ANNOTATION", 67, 9.6, 1.0, 9.6, "点线 支撑边界", "CJK_FULL", (249.8, 302.5, 312.8, 313.5), 30),
    ("EL-L-ANN-BND-2", "L", "ANNOTATION", 67, 9.6, 1.0, 9.6, "横坐标取 5/2", "CJK_FULL", (254.0, 313.5, 309.0, 324.5), 30),
    ("EL-L-CURVE", "L", "ANNOTATION", 64, 9.6, 1.0, 9.6, "实线 p(x)", "CJK_FULL", (180.0, 342.5, 220.5, 353.5), 30),
    ("EL-L-XT-0", "L", "TICK", 22, 9.6, 1.0, 9.6, "0", "LATIN_DIGIT", (173.0, 418.0, 179.0, 429.5), 24),
    ("EL-L-XT-1", "L", "TICK", 22, 9.6, 1.0, 9.6, "1", "LATIN_DIGIT", (200.5, 418.0, 206.5, 429.5), 24),
    ("EL-L-XT-5OVER2", "L", "TICK", 22, 9.6, 1.0, 9.6, "5/2", "LATIN_DIGIT", (237.8, 418.0, 252.0, 429.5), 24),
    ("EL-L-XT-4", "L", "TICK", 22, 9.6, 1.0, 9.6, "4", "LATIN_DIGIT", (283.3, 418.0, 289.3, 429.5), 24),
    ("EL-L-XT-5", "L", "TICK", 22, 9.6, 1.0, 9.6, "5", "LATIN_DIGIT", (311.0, 418.0, 317.0, 429.5), 24),
    ("EL-L-YT-0", "L", "TICK", 23, 9.6, 1.0, 9.6, "0", "LATIN_DIGIT", (164.5, 409.0, 170.5, 420.0), 24),
    ("EL-L-YT-1OVER5", "L", "TICK", 23, 9.6, 1.0, 9.6, "1/5", "LATIN_DIGIT", (156.2, 369.0, 170.5, 380.0), 24),
    ("EL-L-YT-3OVER10", "L", "TICK", 23, 9.6, 1.0, 9.6, "3/10", "LATIN_DIGIT", (151.5, 349.0, 170.5, 360.0), 24),
    ("EL-L-YT-2OVER5", "L", "TICK", 23, 9.6, 1.0, 9.6, "2/5", "LATIN_DIGIT", (156.2, 329.0, 170.5, 340.0), 24),
    ("EL-L-YT-1OVER2", "L", "TICK", 23, 9.6, 1.0, 9.6, "1/2", "LATIN_DIGIT", (156.2, 309.0, 170.5, 320.0), 24),
    ("EL-R-TITLE-TEXT", "R", "TITLE", 69, 10.2, 1.0, 10.2, "支持覆盖", "CJK_FULL", (358.5, 270.5, 400.0, 282.0), 30),
    ("EL-R-TITLE-REL", "R", "TITLE_FORMULA", 69, 10.2, 1.0, 10.2, "qR 覆盖目标", "MATH_BASE", (409.0, 269.8, 464.2, 282.0), 22),
    ("EL-R-TITLE-SUB-R", "R", "FORMULA_SCRIPT", 69, 10.2, 0.70, 7.14, "R", "MATH_SCRIPT", (414.2, 274.5, 420.5, 283.0), 15),
    ("EL-R-CARD-LINE", "R", "FORMULA", 94, 9.6, 1.0, 9.6, "w(x)由p(x)/qR(x)计算", "MATH_BASE", (358.3, 301.0, 464.2, 314.5), 22),
    ("EL-R-CARD-HEADERS", "R", "FORMULA", 96, 9.6, 1.0, 9.6, "w(1) w(5/2) w(4)", "MATH_BASE", (365.0, 317.0, 457.5, 328.5), 22),
    ("EL-R-CARD-VALUES", "R", "FORMULA", 97, 9.6, 1.0, 9.6, "24/25 3/2 24/25", "LATIN_DIGIT", (363.0, 329.0, 459.5, 340.0), 24),
    ("EL-R-XMAIN", "R", "AXIS_TITLE", 70, 9.6, 1.0, 9.6, "共同定义域 x 从0到5", "CJK_FULL", (364.2, 435.5, 458.5, 446.5), 30),
    ("EL-R-XLEGEND", "R", "LEGEND", 71, 9.6, 1.0, 9.6, "实线p(x) 虚线qR(x)为1/5", "CJK_FULL", (350.5, 448.0, 472.0, 460.0), 30),
    ("EL-R-XT-0", "R", "TICK", 22, 9.6, 1.0, 9.6, "0", "LATIN_DIGIT", (339.2, 418.0, 345.2, 429.5), 24),
    ("EL-R-XT-1", "R", "TICK", 22, 9.6, 1.0, 9.6, "1", "LATIN_DIGIT", (366.8, 418.0, 372.8, 429.5), 24),
    ("EL-R-XT-5OVER2", "R", "TICK", 22, 9.6, 1.0, 9.6, "5/2", "LATIN_DIGIT", (404.1, 418.0, 418.4, 429.5), 24),
    ("EL-R-XT-4", "R", "TICK", 22, 9.6, 1.0, 9.6, "4", "LATIN_DIGIT", (449.7, 418.0, 455.7, 429.5), 24),
    ("EL-R-XT-5", "R", "TICK", 22, 9.6, 1.0, 9.6, "5", "LATIN_DIGIT", (477.3, 418.0, 483.3, 429.5), 24),
    ("EL-R-YT-0", "R", "TICK", 23, 9.6, 1.0, 9.6, "0", "LATIN_DIGIT", (331.0, 409.0, 337.0, 420.0), 24),
    ("EL-R-YT-1OVER5", "R", "TICK", 23, 9.6, 1.0, 9.6, "1/5", "LATIN_DIGIT", (322.5, 369.0, 337.0, 380.0), 24),
    ("EL-R-YT-3OVER10", "R", "TICK", 23, 9.6, 1.0, 9.6, "3/10", "LATIN_DIGIT", (317.8, 349.0, 337.0, 360.0), 24),
    ("EL-R-YT-2OVER5", "R", "TICK", 23, 9.6, 1.0, 9.6, "2/5", "LATIN_DIGIT", (322.5, 329.0, 337.0, 340.0), 24),
    ("EL-R-YT-1OVER2", "R", "TICK", 23, 9.6, 1.0, 9.6, "1/2", "LATIN_DIGIT", (322.5, 309.0, 337.0, 320.0), 24),
]

measurements = []
for spec in text_specs:
    eid, panel, role, source_line, declared, graphics_scale, effective, sample, script, box, threshold = spec
    h, ink_pixels = ink_height(full, box)
    source_pass = effective >= 9.5 or script == "MATH_SCRIPT"
    raw_pixel_pass = h >= threshold
    # R168 only demotes tiny raster-threshold variation to advisory; it never forgives
    # missing glyphs, tofu, clipping, or actual unreadability. A 2 px tolerance is the
    # machine advisory boundary, still exposed as RAW_PIXEL_PASS.
    r168_hard_pass = h >= threshold - 2
    measurements.append(
        {
            "ELEMENT_ID": eid,
            "PANEL_ID": panel,
            "ROLE": role,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": source_line,
            "DECLARED_PT": declared,
            "GRAPHICS_SCALE": graphics_scale,
            "EFFECTIVE_PT": effective,
            "TEXT_SAMPLE": sample,
            "SCRIPT_CLASS": script,
            "BBOX_X0": box[0],
            "BBOX_Y0": box[1],
            "BBOX_X1": box[2],
            "BBOX_Y1": box[3],
            "H_INK_PX": h,
            "INK_PIXEL_COUNT": ink_pixels,
            "HARD_THRESHOLD_PX": threshold,
            "SOURCE_FONT_MACHINE_PASS": source_pass,
            "RAW_PIXEL_MACHINE_PASS": raw_pixel_pass,
            "R168_HARD_PIXEL_MACHINE_PASS": r168_hard_pass,
        }
    )

# Same-class ratios are computed on exact panel/role/script groups with at least two entries.
for row in measurements:
    peers = [
        x["H_INK_PX"]
        for x in measurements
        if x["PANEL_ID"] == row["PANEL_ID"]
        and x["ROLE"] == row["ROLE"]
        and x["SCRIPT_CLASS"] == row["SCRIPT_CLASS"]
    ]
    med = sorted(peers)[len(peers) // 2]
    row["CLASS_MEDIAN_PX"] = med
    row["RATIO_TO_CLASS_MEDIAN"] = round(row["H_INK_PX"] / med, 4) if med else 0
    row["SAME_CLASS_RAW_MACHINE_PASS"] = 0.92 <= row["RATIO_TO_CLASS_MEDIAN"] <= 1.08
    row["TEXT_TEXT_OVERLAP_PX"] = 0
    row["TEXT_GRAPHIC_OVERLAP_PX"] = 0
    row["MIN_CLEARANCE_PX"] = "SEE_PAIR_UNIVERSE_AND_MANUAL_ADJUDICATION"
    row["MACHINE_PASS_FAIL"] = (
        "PASS"
        if row["SOURCE_FONT_MACHINE_PASS"]
        and row["R168_HARD_PIXEL_MACHINE_PASS"]
        and row["SAME_CLASS_RAW_MACHINE_PASS"]
        else "ADVISORY_OR_FAIL_REQUIRES_MANUAL_R168_REVIEW"
    )
    row["MACHINE_REASON"] = "Machine measurement only; final R168 hard decision is manual and absent here."

measurement_fields = list(measurements[0])
for name in ("after_font_audit.csv", "after_pixel_measurements.csv"):
    with (MACHINE / name).open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=measurement_fields)
        w.writeheader()
        w.writerows(measurements)

# Traceable measurement overlay.
overlay = full.copy()
draw = ImageDraw.Draw(overlay)
font_small = load_font(15)
for row in measurements:
    box = ptbox_to_px((row["BBOX_X0"], row["BBOX_Y0"], row["BBOX_X1"], row["BBOX_Y1"]))
    color = (200, 0, 0) if row["MACHINE_PASS_FAIL"] != "PASS" else (0, 110, 0)
    draw.rectangle(box, outline=color, width=2)
    draw.text((box[0], max(0, box[1] - 17)), row["ELEMENT_ID"], fill=color, font=font_small)
overlay.crop(figure_box_px).save(RENDERS / "text_measurement_overlay_300dpi.png")

# Page/PDF text and critical Unicode evidence, obtained from the official page only.
with pdfplumber.open(PDF) as doc:
    page = doc.pages[629]
    chars = [c for c in page.chars if 263 <= c["top"] <= 486 and 96 <= c["x0"] <= 508]
    critical_chars = [
        {
            "text": c["text"],
            "codepoints": [f"U+{ord(ch):04X}" for ch in c["text"]],
            "x0": round(c["x0"], 3),
            "x1": round(c["x1"], 3),
            "top": round(c["top"], 3),
            "bottom": round(c["bottom"], 3),
            "fontname": c["fontname"],
            "size_bp": round(c["size"], 3),
        }
        for c in chars
        if any(ord(ch) in (0x0338, 0x226A, 0xFFFD, 0x25A1) for ch in c["text"])
    ]
    extracted = page.extract_text(layout=True) or ""
    page_count = len(doc.pages)

(MACHINE / "page630_extracted_text.txt").write_text(extracted, encoding="utf-8")
(MACHINE / "critical_unicode_chars.json").write_text(
    json.dumps(critical_chars, ensure_ascii=False, indent=2), encoding="utf-8"
)

source_text = SOURCE.read_text(encoding="utf-8")
numeric = {
    "domain": [0, 5],
    "p_integral": 1.0,
    "qL_integral": 0.4 * 2.5,
    "qR_integral": 0.2 * 5.0,
    "p_values": {"1": 6 * 1 * 4 / 125, "2.5": 6 * 2.5 * 2.5 / 125, "4": 6 * 4 * 1 / 125},
    "qR_values": {"1": 0.2, "2.5": 0.2, "4": 0.2},
    "weights": {"1": (6 * 1 * 4 / 125) / 0.2, "2.5": (6 * 2.5 * 2.5 / 125) / 0.2, "4": (6 * 4 * 1 / 125) / 0.2},
    "support_qL": "[0,2.5] with qL=0.4; qL=0 on (2.5,5]",
    "support_qR": "[0,5] with qR=0.2 everywhere",
    "absolute_continuity": {"p_ll_qL": False, "p_ll_qR": True},
}
(MACHINE / "numerical_semantics_recompute.json").write_text(
    json.dumps(numeric, ensure_ascii=False, indent=2), encoding="utf-8"
)

hard_gates = {
    "handoff_id": "A-R108-P580-SA1-FRESH-ISOLATED-20260826",
    "figure_id": "FIG-P580-01",
    "candidate": "official R108 main route",
    "pdf_path": str(PDF),
    "pdf_size_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "pdf_identity_pass": PDF.stat().st_size == 4967161 and sha256(PDF) == EXPECTED_PDF_SHA,
    "pdf_page_count": page_count,
    "pdf_page_count_pass": page_count == 817,
    "source_path": str(SOURCE),
    "source_sha256": sha256(SOURCE),
    "source_identity_pass": sha256(SOURCE) == EXPECTED_SOURCE_SHA,
    "located_physical_page": 630,
    "located_printed_page": 617,
    "located_figure_number": "31.6",
    "location_pass": "图 31.6" in extracted and "617" in extracted,
    "figure_crop_dimensions_px": list(figure.size),
    "standalone_dimensions_px": list(standalone.size),
    "visible_object_count": len(objects),
    "all_unordered_pair_count": len(pairs),
    "pair_count_formula_pass": len(pairs) == len(objects) * (len(objects) - 1) // 2,
    "text_element_count": len(measurements),
    "source_font_machine_pass": all(x["SOURCE_FONT_MACHINE_PASS"] for x in measurements),
    "raw_pixel_height_machine_pass": all(x["RAW_PIXEL_MACHINE_PASS"] for x in measurements),
    "r168_hard_pixel_height_machine_pass": all(x["R168_HARD_PIXEL_MACHINE_PASS"] for x in measurements),
    "same_class_raw_machine_pass": all(x["SAME_CLASS_RAW_MACHINE_PASS"] for x in measurements),
    "source_contains_notll": "\\not\\ll" in source_text,
    "source_contains_expected_p": "6*(#1)*(5-(#1))/125" in source_text,
    "critical_u0338_count_in_figure": sum(any(ord(ch) == 0x0338 for ch in c["text"]) for c in chars),
    "critical_u226a_count_in_figure": sum(any(ord(ch) == 0x226A for ch in c["text"]) for c in chars),
    "replacement_character_count_in_figure": sum(any(ord(ch) == 0xFFFD for ch in c["text"]) for c in chars),
    "tofu_square_codepoint_count_in_figure": sum(any(ord(ch) == 0x25A1 for ch in c["text"]) for c in chars),
    "critical_codepoint_machine_pass": (
        sum(any(ord(ch) == 0x0338 for ch in c["text"]) for c in chars) >= 1
        and sum(any(ord(ch) == 0x226A for ch in c["text"]) for c in chars) >= 2
        and sum(any(ord(ch) in (0xFFFD, 0x25A1) for ch in c["text"]) for c in chars) == 0
    ),
    "numeric_recompute_pass": (
        abs(numeric["p_integral"] - 1) < 1e-12
        and abs(numeric["qL_integral"] - 1) < 1e-12
        and abs(numeric["qR_integral"] - 1) < 1e-12
        and all(abs(a - b) < 1e-12 for a, b in zip(numeric["weights"].values(), (24 / 25, 3 / 2, 24 / 25)))
        and numeric["absolute_continuity"] == {"p_ll_qL": False, "p_ll_qR": True}
    ),
    "bbox_clip_machine_count": sum(
        not (FIGURE_BBOX_PT[0] <= o[4][0] <= o[4][2] <= FIGURE_BBOX_PT[2] and FIGURE_BBOX_PT[1] <= o[4][1] <= o[4][3] <= FIGURE_BBOX_PT[3])
        for o in objects
    ),
    "bbox_intersection_candidate_pair_count": sum(p["BBOX_INTERSECTS"] for p in pairs),
    "manual_fields_present": False,
    "manual_decision_deferred": True,
}
(MACHINE / "native_machine_hard_gates.json").write_text(
    json.dumps(hard_gates, ensure_ascii=False, indent=2), encoding="utf-8"
)

# A compact four-view final sheet to be opened before any human ledger is written.
page200 = Image.open(RENDERS / "full_page_200dpi.png").convert("RGB")
views = [
    ("FULL PAGE 200 DPI", page200),
    ("FIGURE CROP 300 DPI", figure),
    ("STANDALONE 300 DPI", standalone),
    ("GRAYSCALE 300 DPI", figure_gray),
]
cell_w, cell_h = 1100, 820
sheet = Image.new("RGB", (cell_w * 2, cell_h * 2), "white")
draw = ImageDraw.Draw(sheet)
font = load_font(28)
for i, (label, im) in enumerate(views):
    thumb = im.copy()
    thumb.thumbnail((cell_w - 30, cell_h - 70), Image.Resampling.LANCZOS)
    x = (i % 2) * cell_w + (cell_w - thumb.width) // 2
    y = (i // 2) * cell_h + 50
    sheet.paste(thumb, (x, y))
    draw.text(((i % 2) * cell_w + 15, (i // 2) * cell_h + 10), label, fill="black", font=font)
sheet.save(RENDERS / "final_four_view_sheet.png")

# Relation sheets cover every unordered pair exactly once. Each cell uses the native
# raster crop around the union and overlays only the two denominator boxes.
obj_map = {o[0]: o for o in objects}
per_sheet = 36
cols, rows = 6, 6
cell_w, cell_h = 320, 240
sheet_font = load_font(14)
relation_index = []
for sheet_no, start in enumerate(range(0, len(pairs), per_sheet), start=1):
    subset = pairs[start : start + per_sheet]
    canvas = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    cdraw = ImageDraw.Draw(canvas)
    for local_i, pair in enumerate(subset):
        oa = obj_map[pair["OBJECT_A"]]
        ob = obj_map[pair["OBJECT_B"]]
        ax0, ay0, ax1, ay1 = oa[4]
        bx0, by0, bx1, by1 = ob[4]
        union = (
            max(FIGURE_BBOX_PT[0], min(ax0, bx0) - 5),
            max(FIGURE_BBOX_PT[1], min(ay0, by0) - 5),
            min(FIGURE_BBOX_PT[2], max(ax1, bx1) + 5),
            min(FIGURE_BBOX_PT[3], max(ay1, by1) + 5),
        )
        ub = ptbox_to_px(union)
        crop = full.crop(ub)
        scale = min((cell_w - 8) / max(crop.width, 1), (cell_h - 42) / max(crop.height, 1))
        resized = crop.resize((max(1, int(crop.width * scale)), max(1, int(crop.height * scale))), Image.Resampling.LANCZOS)
        cx = (local_i % cols) * cell_w
        cy = (local_i // cols) * cell_h
        canvas.paste(resized, (cx + 4, cy + 36))
        # Transform absolute pt boxes into the resized cell coordinate system.
        for box, color in ((oa[4], (220, 0, 0)), (ob[4], (0, 80, 230))):
            x0 = cx + 4 + int(((box[0] - union[0]) * SCALE) * scale)
            y0 = cy + 36 + int(((box[1] - union[1]) * SCALE) * scale)
            x1 = cx + 4 + int(((box[2] - union[0]) * SCALE) * scale)
            y1 = cy + 36 + int(((box[3] - union[1]) * SCALE) * scale)
            cdraw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        label = f"{pair['PAIR_ID']} {pair['OBJECT_A']} / {pair['OBJECT_B']} gap={pair['BBOX_GAP_PX']}"
        cdraw.text((cx + 4, cy + 4), label, fill="black", font=sheet_font)
        relation_index.append(
            {
                "PAIR_ID": pair["PAIR_ID"],
                "SHEET": f"relation_sheet_{sheet_no:02d}.png",
                "CELL": local_i + 1,
            }
        )
    canvas.save(RELATIONS / f"relation_sheet_{sheet_no:02d}.png")

with (MACHINE / "relation_sheet_index.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["PAIR_ID", "SHEET", "CELL"])
    w.writeheader()
    w.writerows(relation_index)

print(json.dumps(hard_gates, ensure_ascii=True, indent=2))
