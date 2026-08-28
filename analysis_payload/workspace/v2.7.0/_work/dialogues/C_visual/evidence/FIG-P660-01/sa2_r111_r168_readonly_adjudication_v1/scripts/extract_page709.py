from __future__ import annotations

import csv
from pathlib import Path

import fitz


PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf"
)
ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1"
)
PAGE_INDEX = 708
SCALE = 300.0 / 72.0
REGION = fitz.Rect(40.0, 35.0, 555.0, 370.0)


def rgb_hex(value: int) -> str:
    return f"#{value & 0xFFFFFF:06X}"


def main() -> None:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]

    span_path = ROOT / "06_machine_tables" / "page709_text_spans.csv"
    with span_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "span_id",
                "block_index",
                "line_index",
                "span_index",
                "x0_pt",
                "y0_pt",
                "x1_pt",
                "y1_pt",
                "x0_px_300",
                "y0_px_300",
                "x1_px_300",
                "y1_px_300",
                "font_size_pt",
                "font",
                "flags",
                "color_rgb",
                "text",
            ]
        )
        span_number = 0
        data = page.get_text("dict")
        for block_index, block in enumerate(data["blocks"]):
            if block.get("type") != 0:
                continue
            for line_index, line in enumerate(block.get("lines", [])):
                for span_index, span in enumerate(line.get("spans", [])):
                    rect = fitz.Rect(span["bbox"])
                    if not rect.intersects(REGION):
                        continue
                    span_number += 1
                    writer.writerow(
                        [
                            f"S{span_number:03d}",
                            block_index,
                            line_index,
                            span_index,
                            f"{rect.x0:.4f}",
                            f"{rect.y0:.4f}",
                            f"{rect.x1:.4f}",
                            f"{rect.y1:.4f}",
                            round(rect.x0 * SCALE),
                            round(rect.y0 * SCALE),
                            round(rect.x1 * SCALE),
                            round(rect.y1 * SCALE),
                            f"{span['size']:.4f}",
                            span["font"],
                            span["flags"],
                            rgb_hex(span["color"]),
                            span["text"],
                        ]
                    )

    drawing_path = ROOT / "06_machine_tables" / "page709_drawings.csv"
    with drawing_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "drawing_id",
                "seqno",
                "x0_pt",
                "y0_pt",
                "x1_pt",
                "y1_pt",
                "x0_px_300",
                "y0_px_300",
                "x1_px_300",
                "y1_px_300",
                "draw_type",
                "stroke_color",
                "fill_color",
                "line_width_pt",
                "dashes",
                "item_count",
            ]
        )
        drawing_number = 0
        for drawing in page.get_drawings():
            rect = fitz.Rect(drawing["rect"])
            if not rect.intersects(REGION):
                continue
            drawing_number += 1
            writer.writerow(
                [
                    f"D{drawing_number:03d}",
                    drawing.get("seqno", ""),
                    f"{rect.x0:.4f}",
                    f"{rect.y0:.4f}",
                    f"{rect.x1:.4f}",
                    f"{rect.y1:.4f}",
                    round(rect.x0 * SCALE),
                    round(rect.y0 * SCALE),
                    round(rect.x1 * SCALE),
                    round(rect.y1 * SCALE),
                    drawing.get("type", ""),
                    repr(drawing.get("color")),
                    repr(drawing.get("fill")),
                    drawing.get("width", ""),
                    drawing.get("dashes", ""),
                    len(drawing.get("items", [])),
                ]
            )

    info_path = ROOT / "02_location" / "page709_location_machine.txt"
    info_path.write_text(
        "\n".join(
            [
                "PDF_PHYSICAL_PAGE_1_BASED=709",
                "PRINTED_PAGE_NUMBER=696",
                "FIGURE_NUMBER=34.4",
                "TEXT_NEEDLE=图 34.4 三类别概率向量位于二维单纯形上",
                f"PAGE_WIDTH_PT={page.rect.width:.4f}",
                f"PAGE_HEIGHT_PT={page.rect.height:.4f}",
                "MACHINE_EXTRACTION_ONLY=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
