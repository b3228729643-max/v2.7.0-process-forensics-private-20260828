from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P634-01\sa3_r110_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_coordinate_sweep.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C04.tex")
PAGE_NUMBER = 684
PAGE_INDEX = PAGE_NUMBER - 1
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
FIGURE_RECT = fitz.Rect(108.0, 330.0, 497.0, 500.0)
FIGURE_CAPTION_RECT = fitz.Rect(78.0, 330.0, 525.0, 535.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def save_pix(page: fitz.Page, dpi: int, path: Path) -> None:
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False)
    pix.save(path)


def rect_to_px(rect: tuple[float, float, float, float], origin=(0.0, 0.0), scale=SCALE_300):
    x0, y0, x1, y1 = rect
    ox, oy = origin
    return tuple(int(round((v - o) * scale)) for v, o in zip((x0, y0, x1, y1), (ox, oy, ox, oy)))


def edge_distance(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def intersection_area(a, b):
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return w * h


def ink_height(image: Image.Image, bbox_px: tuple[int, int, int, int]) -> int:
    x0, y0, x1, y1 = bbox_px
    pad = 2
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(image.width, x1 + pad)
    y1 = min(image.height, y1 + pad)
    crop = image.crop((x0, y0, x1, y1)).convert("RGB")
    rows = []
    for y in range(crop.height):
        count = 0
        for x in range(crop.width):
            r, g, b = crop.getpixel((x, y))
            if max(255 - r, 255 - g, 255 - b) >= 20:
                count += 1
        if count >= 2:
            rows.append(y)
    return 0 if not rows else rows[-1] - rows[0] + 1


OBJECTS = [
    ("O001", "TEXT", "TITLE", "单轮系统扫描坐标带", (238.53, 336.38, 333.57, 351.68), 17),
    ("O002", "TEXT", "ORDER_LABEL", "1", (136.28, 359.67, 141.02, 369.23), 18),
    ("O003", "TEXT", "ORDER_LABEL", "2", (178.80, 359.69, 183.54, 369.25), 19),
    ("O004", "TEXT", "ORDER_LABEL", "省略", (214.12, 359.88, 233.25, 370.12), 20),
    ("O005", "TEXT", "ORDER_LABEL", "前位", (256.64, 359.88, 275.77, 370.12), 21),
    ("O006", "TEXT", "ORDER_LABEL", "当前", (299.16, 359.88, 318.29, 370.12), 22),
    ("O007", "TEXT", "ORDER_LABEL", "后位", (341.68, 359.88, 360.81, 370.12), 23),
    ("O008", "TEXT", "ORDER_LABEL", "省略", (384.20, 359.88, 403.33, 370.12), 24),
    ("O009", "TEXT", "ORDER_LABEL", "末位", (426.72, 359.88, 445.85, 370.12), 25),
    ("O010", "LINE_ARROW", "UPDATE_SEQUENCE", "left-to-right update arrow", (129.58, 371.9, 444.45, 377.0), 26),
    ("O011", "TEXT", "ARROW_LABEL", "更新顺序", (453.28, 370.65, 491.53, 380.89), 27),
    ("O012", "NODE_BORDER", "UPDATED_SLOT", "slot 1 patterned border", (119.94, 392.39, 157.36, 419.31), 28),
    ("O013", "NODE_BORDER", "UPDATED_SLOT", "slot 2 patterned border", (162.46, 392.39, 199.88, 419.31), 29),
    ("O014", "NODE_BORDER", "UPDATED_SLOT", "middle-updated patterned border", (204.98, 392.39, 242.40, 419.31), 30),
    ("O015", "NODE_BORDER", "UPDATED_SLOT", "last-updated patterned border", (247.50, 392.39, 284.92, 419.31), 31),
    ("O016", "NODE_BORDER", "CURRENT_SLOT", "current highlighted border", (290.02, 392.39, 327.44, 419.31), 36),
    ("O017", "NODE_BORDER", "OLD_SLOT", "first old dotted border", (332.54, 392.39, 369.96, 419.31), 37),
    ("O018", "NODE_BORDER", "OLD_SLOT", "middle old dotted border", (375.06, 392.39, 412.48, 419.31), 38),
    ("O019", "NODE_BORDER", "OLD_SLOT", "last old dotted border", (417.58, 392.39, 455.00, 419.31), 39),
    ("O020", "TEXT", "SLOT_LABEL", "坐标 1", (127.59, 394.67, 149.71, 418.06), 32),
    ("O021", "TEXT", "SLOT_LABEL", "坐标 2", (170.11, 394.67, 192.23, 418.06), 33),
    ("O022", "TEXT", "SLOT_LABEL", "中间坐标", (212.63, 394.09, 234.75, 417.80), 34),
    ("O023", "TEXT", "SLOT_LABEL", "前段末位", (255.15, 394.09, 277.27, 417.80), 35),
    ("O024", "TEXT", "SLOT_LABEL", "当前坐标", (299.16, 396.10, 318.29, 417.80), 36),
    ("O025", "TEXT", "SLOT_LABEL", "后段首位", (341.68, 396.10, 360.81, 417.80), 37),
    ("O026", "TEXT", "SLOT_LABEL", "中间坐标", (384.20, 396.10, 403.33, 417.80), 38),
    ("O027", "TEXT", "SLOT_LABEL", "末位坐标", (426.72, 396.10, 445.85, 417.80), 39),
    ("O028", "TEXT", "STATE_LABEL", "本轮新值", (184.72, 423.38, 222.97, 433.62), 40),
    ("O029", "TEXT", "STATE_LABEL", "当前新值", (289.60, 423.38, 327.86, 433.62), 41),
    ("O030", "TEXT", "STATE_LABEL", "前轮旧值", (374.64, 423.38, 412.89, 433.62), 42),
    ("O031", "PANEL_BORDER", "SUBSTEP_CARD", "substep-state card", (118.80, 434.06, 453.30, 463.82), 44),
    ("O032", "FORMULA", "SUBSTEP_FORMULA", "x^[j]", (246.21, 438.31, 263.38, 451.43), 45),
    ("O033", "TEXT", "SUBSTEP_HEADING", "当前子步状态", (266.12, 440.76, 325.89, 451.43), 45),
    ("O034", "TEXT", "SUBSTEP_DESCRIPTION", "起始至当前坐标 本轮新值", (152.35, 453.06, 269.51, 463.51), 46),
    ("O035", "TEXT", "SUBSTEP_DESCRIPTION", "后续至末位坐标 前轮旧值", (302.59, 453.06, 419.75, 463.51), 48),
    ("O036", "PANEL_BORDER", "ROUND_CARD", "round-end card", (111.72, 467.36, 460.38, 498.54), 51),
    ("O037", "FORMULA", "ROUND_STATE", "x^[d]", (201.63, 482.23, 219.83, 495.02), 52),
    ("O038", "LINE_ARROW", "STATE_EQUIVALENCE", "bidirectional equivalence arrow", (223.77, 484.8, 297.94, 489.6), 55),
    ("O039", "TEXT", "ARROW_LABEL", "状态相同", (241.73, 470.48, 279.98, 480.73), 56),
    ("O040", "FORMULA", "ROUND_STATE", "x^(t)", (301.48, 482.06, 318.41, 494.85), 53),
    ("O041", "LINE_ARROW", "RECORD_ARROW", "record arrow", (321.50, 484.8, 383.40, 489.6), 57),
    ("O042", "TEXT", "ARROW_LABEL", "仅此记录", (333.77, 470.48, 372.03, 480.73), 58),
    ("O043", "TEXT", "SAMPLE_LABEL", "轮末样本", (386.99, 483.10, 426.05, 493.56), 54),
    ("O044", "TEXT", "CAPTION_NUMBER", "图 33.3", (87.48, 501.61, 117.95, 516.04), 61),
    ("O045", "TEXT", "CAPTION_BODY_LINE", "系统扫描按固定次序即时写回；当前子步的前段使用本轮新值，后段沿用前轮旧值；末位", (127.92, 505.20, 519.13, 515.87), 61),
    ("O046", "TEXT", "CAPTION_BODY_LINE", "更新结束后，末位状态与本轮样本状态相同并记录为轮末样本。", (87.48, 518.59, 366.43, 529.26), 61),
]


def main() -> None:
    for folder in (ROOT / "renders", ROOT / "data", ROOT / "review", ROOT / "scripts"):
        folder.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    if len(doc) != 817:
        raise RuntimeError(f"unexpected page count: {len(doc)}")

    full300 = ROOT / "renders" / "page_0684_native300dpi.png"
    full200 = ROOT / "renders" / "page_0684_full_page_200dpi.png"
    save_pix(page, 300, full300)
    save_pix(page, 200, full200)
    full = Image.open(full300).convert("RGB")

    fig_cap_box = rect_to_px(tuple(FIGURE_CAPTION_RECT))
    fig_box = rect_to_px(tuple(FIGURE_RECT))
    fig_cap = full.crop(fig_cap_box)
    fig = full.crop(fig_box)
    fig_cap.save(ROOT / "renders" / "figure_caption_complete_native300dpi.png")
    fig.save(ROOT / "renders" / "figure_crop_native300dpi.png")
    fig.convert("L").save(ROOT / "renders" / "figure_crop_grayscale_native300dpi.png")

    colors = {
        "TEXT": (210, 30, 30),
        "FORMULA": (135, 40, 180),
        "LINE_ARROW": (0, 135, 80),
        "NODE_BORDER": (15, 90, 210),
        "PANEL_BORDER": (245, 130, 15),
    }
    font = ImageFont.load_default()
    for name, grouped in (("object", False), ("semantic", True)):
        overlay = fig_cap.copy()
        draw = ImageDraw.Draw(overlay)
        for oid, cls, role, label, bbox, source_line in OBJECTS:
            px = rect_to_px(bbox, (FIGURE_CAPTION_RECT.x0, FIGURE_CAPTION_RECT.y0))
            color = colors[cls]
            draw.rectangle(px, outline=color, width=2)
            tag = cls if grouped else oid
            tx, ty = px[0] + 2, max(0, px[1] - 10)
            draw.rectangle((tx, ty, tx + 7 * len(tag) + 3, ty + 10), fill=(255, 255, 255))
            draw.text((tx + 1, ty), tag, fill=color, font=font)
        overlay.save(ROOT / "renders" / f"{name}_overlay_native300dpi.png")

    text_overlay = fig_cap.copy()
    draw = ImageDraw.Draw(text_overlay)
    for oid, cls, role, label, bbox, source_line in OBJECTS:
        if cls not in {"TEXT", "FORMULA"}:
            continue
        px = rect_to_px(bbox, (FIGURE_CAPTION_RECT.x0, FIGURE_CAPTION_RECT.y0))
        draw.rectangle(px, outline=(220, 0, 130), width=2)
        tx, ty = px[0] + 1, max(0, px[1] - 10)
        draw.rectangle((tx, ty, tx + 7 * len(oid) + 2, ty + 10), fill=(255, 255, 255))
        draw.text((tx + 1, ty), oid, fill=(220, 0, 130), font=font)
    text_overlay.save(ROOT / "renders" / "text_overlay_native300dpi.png")

    with (ROOT / "data" / "objects_machine.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["object_id", "class", "role", "label", "source_file", "source_line", "pdf_x0", "pdf_y0", "pdf_x1", "pdf_y1", "px_x0", "px_y0", "px_x1", "px_y1"])
        for oid, cls, role, label, bbox, source_line in OBJECTS:
            px = rect_to_px(bbox)
            writer.writerow([oid, cls, role, label, str(SOURCE), source_line, *bbox, *px])

    with (ROOT / "data" / "all_unordered_pairs_machine.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["pair_id", "object_a", "object_b", "class_a", "class_b", "bbox_edge_distance_pdf_pt", "bbox_edge_distance_300dpi_px", "bbox_intersection_pdf_pt2", "machine_close_le_12px"])
        for idx, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), 1):
            dist_pt = edge_distance(a[4], b[4])
            area = intersection_area(a[4], b[4])
            dist_px = dist_pt * SCALE_300
            writer.writerow([f"P{idx:04d}", a[0], b[0], a[1], b[1], f"{dist_pt:.3f}", f"{dist_px:.2f}", f"{area:.3f}", str(dist_px <= 12.0 or area > 0).lower()])

    text_rows = []
    text_dict = page.get_text("dict")
    tid = 0
    for block in text_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                x0, y0, x1, y1 = span["bbox"]
                if y0 < FIGURE_CAPTION_RECT.y0 or y1 > FIGURE_CAPTION_RECT.y1:
                    continue
                if not span["text"].strip():
                    continue
                tid += 1
                bbox = tuple(float(v) for v in span["bbox"])
                px = rect_to_px(bbox)
                text = span["text"]
                if any(ord(c) > 0x2FFF and not (0x1D400 <= ord(c) <= 0x1D7FF) for c in text):
                    script = "CJK_OR_FULLWIDTH"
                elif any(0x1D400 <= ord(c) <= 0x1D7FF for c in text) or any(c in "[]()" for c in text):
                    script = "MATH_OR_SCRIPT"
                elif any(c.isdigit() for c in text):
                    script = "LATIN_DIGIT"
                else:
                    script = "LATIN_OTHER"
                text_rows.append({
                    "text_id": f"T{tid:03d}",
                    "text": text,
                    "font": span["font"],
                    "reported_pt": f"{span['size']:.2f}",
                    "script_class": script,
                    "pdf_x0": f"{x0:.2f}",
                    "pdf_y0": f"{y0:.2f}",
                    "pdf_x1": f"{x1:.2f}",
                    "pdf_y1": f"{y1:.2f}",
                    "bbox_height_300dpi_px": str(px[3] - px[1]),
                    "ink_height_300dpi_px": str(ink_height(full, px)),
                    "unicode_codepoints": " ".join(f"U+{ord(c):04X}" for c in text),
                })
    with (ROOT / "data" / "text_spans_machine.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(text_rows[0]))
        writer.writeheader()
        writer.writerows(text_rows)

    rois = {
        "roi01_update_order_arrow": (124.0, 354.0, 496.0, 385.0),
        "roi02_updated_current_old_slots": (114.0, 388.0, 460.0, 438.0),
        "roi03_substep_state_formula": (115.0, 432.0, 457.0, 466.0),
        "roi04_round_state_equivalence_record": (108.0, 466.0, 464.0, 500.0),
        "roi05_caption_codepoints": (82.0, 498.0, 523.0, 533.0),
    }
    for key, rect in rois.items():
        box = rect_to_px(rect)
        roi = full.crop(box)
        roi.save(ROOT / "renders" / f"{key}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(ROOT / "renders" / f"{key}_nearest8x.png")

    page_text = page.get_text(sort=True)
    (ROOT / "data" / "page_0684_extracted_text.txt").write_text(page_text, encoding="utf-8")
    identity = {
        "owner_dialogue": "C_visual",
        "handoff_id": "C-FIG-P634-01-R110-SA3-FRESH-ISOLATED-V1",
        "role": "SA3",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "fork_turns": "none",
        "figure_uid": "FIG-P634-01",
        "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF), "pages": len(doc)},
        "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
        "chapter_context": {"path": str(CHAPTER), "include_line": 219, "reading_order_line": 221},
        "located": {
            "physical_page": PAGE_NUMBER,
            "printed_page": 671,
            "figure_number": "33.3",
            "caption": "系统扫描按固定次序即时写回；当前子步的前段使用本轮新值，后段沿用前轮旧值；末位更新结束后，末位状态与本轮样本状态相同并记录为轮末样本。",
            "label": "fig:V5-C04-coordinate-sweep",
        },
        "object_count": len(OBJECTS),
        "all_unordered_pair_count": len(OBJECTS) * (len(OBJECTS) - 1) // 2,
    }
    (ROOT / "data" / "identity_and_localization.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
