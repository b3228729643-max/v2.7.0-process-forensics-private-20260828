from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa1_r108_fresh_isolated_v1")
VIEWS = ROOT / "views"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex")
FULL_300 = VIEWS / "r108_p661_full_300dpi.png"
PAGE_INDEX = 660
PAGE_NUMBER = 661
FIGURE_RECT = fitz.Rect(60, 525, 530, 730)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def px_box(rect: fitz.Rect, sx: float, sy: float) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * sx),
        math.floor(rect.y0 * sy),
        math.ceil(rect.x1 * sx),
        math.ceil(rect.y1 * sy),
    )


def bbox_gap(a: fitz.Rect, b: fitz.Rect) -> float:
    dx = max(a.x0 - b.x1, b.x0 - a.x1, 0.0)
    dy = max(a.y0 - b.y1, b.y0 - a.y1, 0.0)
    return math.hypot(dx, dy)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    VIEWS.mkdir(exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    full = Image.open(FULL_300).convert("RGB")
    sx = full.width / page.rect.width
    sy = full.height / page.rect.height

    identity = {
        "uid": "FIG-P609-01",
        "handoff_id": "C-FIG-P609-01-R108-SA1-FRESH-ISOLATED-V1",
        "candidate": "R108",
        "pdf_path": str(PDF),
        "pdf_pages": doc.page_count,
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "source_path": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "located_physical_page": PAGE_NUMBER,
        "located_printed_page": 648,
        "page_size_pt": [page.rect.width, page.rect.height],
        "full_300_size_px": list(full.size),
        "scale_px_per_pdf_pt": [sx, sy],
        "figure_crop_pdf_rect": list(FIGURE_RECT),
    }
    (ROOT / "machine_identity.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    crop_box = px_box(FIGURE_RECT, sx, sy)
    crop = full.crop(crop_box)
    crop.save(VIEWS / "r108_p661_figure_caption_300dpi.png")
    crop.convert("L").save(VIEWS / "r108_p661_figure_caption_grayscale_300dpi.png")

    roi_rects = {
        "critical_cutoff": fitz.Rect(145, 528, 282, 590),
        "critical_formula": fitz.Rect(305, 548, 505, 630),
        "critical_notes_caption": fitz.Rect(70, 628, 520, 724),
    }
    for name, rect in roi_rects.items():
        native = full.crop(px_box(rect, sx, sy))
        native.save(VIEWS / f"{name}_native1x.png")
        native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(
            VIEWS / f"{name}_nearest8x.png"
        )

    text_rows: list[dict] = []
    span_counter = 0
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            direction = line.get("dir", (1.0, 0.0))
            for span in line.get("spans", []):
                rect = fitz.Rect(span["bbox"])
                if not rect.intersects(FIGURE_RECT):
                    continue
                span_counter += 1
                text_rows.append(
                    {
                        "span_id": f"S{span_counter:03d}",
                        "text": span["text"],
                        "font": span["font"],
                        "pdf_size_pt": f"{span['size']:.3f}",
                        "flags": span["flags"],
                        "direction_x": f"{direction[0]:.3f}",
                        "direction_y": f"{direction[1]:.3f}",
                        "bbox_x0_pt": f"{rect.x0:.3f}",
                        "bbox_y0_pt": f"{rect.y0:.3f}",
                        "bbox_x1_pt": f"{rect.x1:.3f}",
                        "bbox_y1_pt": f"{rect.y1:.3f}",
                        "bbox_x0_px": px_box(rect, sx, sy)[0],
                        "bbox_y0_px": px_box(rect, sx, sy)[1],
                        "bbox_x1_px": px_box(rect, sx, sy)[2],
                        "bbox_y1_px": px_box(rect, sx, sy)[3],
                    }
                )
    write_csv(
        ROOT / "machine_pdf_text_spans.csv",
        list(text_rows[0].keys()),
        text_rows,
    )

    drawing_rows: list[dict] = []
    drawing_counter = 0
    for drawing in page.get_drawings():
        rect = fitz.Rect(drawing["rect"])
        if not rect.intersects(FIGURE_RECT):
            continue
        drawing_counter += 1
        drawing_rows.append(
            {
                "drawing_id": f"D{drawing_counter:03d}",
                "type": drawing["type"],
                "bbox_x0_pt": f"{rect.x0:.3f}",
                "bbox_y0_pt": f"{rect.y0:.3f}",
                "bbox_x1_pt": f"{rect.x1:.3f}",
                "bbox_y1_pt": f"{rect.y1:.3f}",
                "stroke_width_pt": "" if drawing.get("width") is None else f"{drawing['width']:.3f}",
                "stroke_color": repr(drawing.get("color")),
                "fill_color": repr(drawing.get("fill")),
                "item_count": len(drawing.get("items", [])),
            }
        )
    write_csv(
        ROOT / "machine_pdf_drawings.csv",
        list(drawing_rows[0].keys()),
        drawing_rows,
    )

    objects = [
        ("T01", "TEXT", "PANEL_TITLE", "1. 经验 ACF：预设窗口", (155.42, 532.84, 262.46, 547.84), "17"),
        ("T02", "TEXT", "AXIS_LABEL", "经验 ACF rho-hat-k", (86.54, 588.10, 98.03, 640.86), "18"),
        ("T03", "TEXT", "AXIS_LABEL", "滞后 k", (195.40, 690.33, 222.43, 700.78), "18"),
        ("T04", "TEXT", "X_TICK", "0", (130.56, 674.64, 135.29, 684.20), "19"),
        ("T05", "TEXT", "X_TICK", "1", (148.99, 674.61, 153.72, 684.17), "19"),
        ("T06", "TEXT", "X_TICK", "2", (167.41, 674.65, 172.15, 684.22), "19"),
        ("T07", "TEXT", "X_TICK", "3", (185.84, 674.65, 190.58, 684.22), "19"),
        ("T08", "TEXT", "X_TICK", "4", (204.27, 674.66, 209.00, 684.23), "19"),
        ("T09", "TEXT", "X_TICK", "5", (222.70, 674.52, 227.43, 684.08), "19"),
        ("T10", "TEXT", "X_TICK", "6", (241.12, 674.67, 245.86, 684.24), "19"),
        ("T11", "TEXT", "Y_TICK", "0", (115.78, 665.55, 120.51, 675.12), "19"),
        ("T12", "TEXT", "Y_TICK", "0.25", (103.97, 639.84, 120.51, 649.40), "19"),
        ("T13", "TEXT", "Y_TICK", "0.5", (108.70, 614.12, 120.51, 623.68), "19"),
        ("T14", "TEXT", "Y_TICK", "0.75", (103.97, 588.41, 120.51, 597.97), "19"),
        ("T15", "TEXT", "Y_TICK", "1", (115.78, 562.74, 120.51, 572.31), "19"),
        ("T16", "TEXT", "ANNOTATION", "截断 K=6", (200.91, 569.52, 246.10, 579.76), "25-26"),
        ("T17", "TEXT", "ANNOTATION", "ellipsis", (267.50, 647.60, 276.61, 657.16), "27-28"),
        ("T18", "TEXT", "PANEL_TITLE", "2. 有限样本加权 ESS", (317.24, 555.14, 413.16, 570.14), "32"),
        ("T19", "FORMULA", "FORMULA_BLOCK", "tau_K,n weighted ACF", (317.24, 574.17, 427.95, 602.92), "33"),
        ("T20", "FORMULA", "FORMULA_BLOCK", "N_eff and positivity", (317.24, 603.70, 422.63, 626.84), "34"),
        ("T21", "TEXT", "ANNOTATION", "预设窗口 K=6<n，仅纳入 1<=k<=K", (317.24, 630.79, 497.77, 644.64), "35"),
        ("T22", "TEXT", "ANNOTATION", "后续滞后未绘出且未纳入", (317.24, 647.98, 432.01, 658.22), "36"),
        ("T23", "TEXT", "ANNOTATION", "有限轨迹诊断，不是收敛证明", (317.24, 661.73, 451.14, 671.97), "37"),
        ("T24", "TEXT", "CAPTION_LABEL", "图 32.9", (76.14, 704.87, 108.13, 720.67), "41"),
        ("T25", "TEXT", "CAPTION_TEXT", "固定窗口内的正经验自相关增大方差权重，因而使同长度轨迹的有效样本量减小", (119.04, 708.80, 509.79, 720.48), "41"),
        ("G01", "LINE_ARROW", "X_AXIS", "x-axis, ticks, arrowhead", (124.35, 667.69, 291.40, 671.95), "14-20"),
        ("G02", "LINE_ARROW", "Y_AXIS", "y-axis, ticks, arrowhead", (124.35, 558.75, 128.60, 671.77), "14-20"),
        ("G03", "BACKGROUND", "WINDOW_SHADE", "predeclared k=1..6 window shading", (142.14, 561.83, 252.71, 669.82), "21"),
        ("G04", "DATA_CURVE", "ACF_SERIES", "seven stems and endpoint markers k=0..6", (131.03, 565.08, 245.38, 669.82), "22-23"),
        ("G05", "LINE_ARROW", "CUTOFF_LINE", "gold dashed cutoff after k=6", (252.20, 561.83, 253.20, 669.82), "24"),
        ("G06", "PANEL_BORDER", "ESS_BOX", "rounded panel border", (308.74, 550.67, 501.49, 677.90), "30-37"),
        ("G07", "LINE_ARROW", "CONNECTOR", "left-to-right diagnostic flow arrow", (294.20, 612.74, 305.90, 615.83), "38"),
    ]
    object_rows: list[dict] = []
    rect_by_id: dict[str, fitz.Rect] = {}
    for object_id, kind, role, description, coords, source_lines in objects:
        rect = fitz.Rect(*coords)
        rect_by_id[object_id] = rect
        pxb = px_box(rect, sx, sy)
        object_rows.append(
            {
                "object_id": object_id,
                "kind": kind,
                "role": role,
                "description": description,
                "source_lines": source_lines,
                "bbox_x0_pt": f"{rect.x0:.3f}",
                "bbox_y0_pt": f"{rect.y0:.3f}",
                "bbox_x1_pt": f"{rect.x1:.3f}",
                "bbox_y1_pt": f"{rect.y1:.3f}",
                "bbox_x0_px": pxb[0],
                "bbox_y0_px": pxb[1],
                "bbox_x1_px": pxb[2],
                "bbox_y1_px": pxb[3],
            }
        )
    write_csv(ROOT / "object_denominator.csv", list(object_rows[0].keys()), object_rows)

    pair_rows: list[dict] = []
    for index, (a, b) in enumerate(itertools.combinations([row[0] for row in objects], 2), start=1):
        ra, rb = rect_by_id[a], rect_by_id[b]
        gap_pt = bbox_gap(ra, rb)
        pair_rows.append(
            {
                "pair_id": f"P{index:04d}",
                "object_a": a,
                "object_b": b,
                "bbox_intersects": str(ra.intersects(rb)).lower(),
                "bbox_gap_pt": f"{gap_pt:.3f}",
                "bbox_gap_px_300dpi": f"{gap_pt * 300 / 72:.2f}",
            }
        )
    write_csv(ROOT / "all_unordered_pairs.csv", list(pair_rows[0].keys()), pair_rows)

    overlay = full.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for object_id, kind, _role, _description, coords, _source_lines in objects:
        rect = fitz.Rect(*coords)
        x0, y0, x1, y1 = px_box(rect, sx, sy)
        color = (220, 30, 30) if kind in {"TEXT", "FORMULA"} else (0, 100, 220)
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        draw.rectangle((x0, max(0, y0 - 13), x0 + 30, y0), fill=(255, 255, 255))
        draw.text((x0 + 1, max(0, y0 - 12)), object_id, fill=color, font=font)
    overlay.crop(crop_box).save(VIEWS / "r108_p661_figure_caption_object_overlay_300dpi.png")

    span_overlay = full.copy()
    span_draw = ImageDraw.Draw(span_overlay)
    for row in text_rows:
        x0 = int(row["bbox_x0_px"])
        y0 = int(row["bbox_y0_px"])
        x1 = int(row["bbox_x1_px"])
        y1 = int(row["bbox_y1_px"])
        span_draw.rectangle((x0, y0, x1, y1), outline=(170, 0, 170), width=1)
    span_overlay.crop(crop_box).save(VIEWS / "r108_p661_figure_caption_span_overlay_300dpi.png")

    summary = {
        "semantic_object_count": len(objects),
        "unordered_pair_count": len(pair_rows),
        "text_span_count": len(text_rows),
        "vector_drawing_count": len(drawing_rows),
        "crop_size_px": list(crop.size),
        "roi_count": len(roi_rects),
    }
    (ROOT / "machine_denominator_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
