from __future__ import annotations

import csv
from pathlib import Path

import fitz


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa1_r115_fresh_isolated_v1")
PAGE_INDEX = 736
Y0 = 375.0
Y1 = 646.0


def fmt_box(rect) -> list[str]:
    return [f"{float(value):.3f}" for value in rect]


def main() -> None:
    document = fitz.open(PDF)
    page = document[PAGE_INDEX]

    with (ROOT / "pdf_page_geometry.txt").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(f"PHYSICAL_PAGE=737\n")
        stream.write(f"PRINTED_PAGE=724\n")
        stream.write(f"PAGE_WIDTH_PT={page.rect.width:.3f}\n")
        stream.write(f"PAGE_HEIGHT_PT={page.rect.height:.3f}\n")
        stream.write(f"FIGURE_VECTOR_REGION_Y0_PT={Y0:.3f}\n")
        stream.write(f"FIGURE_VECTOR_REGION_Y1_PT={Y1:.3f}\n")

    with (ROOT / "vector_text_spans.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["span_id", "text", "font", "size_pt", "x0_pt", "y0_pt", "x1_pt", "y1_pt"])
        span_index = 0
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    x0, y0, x1, y1 = span["bbox"]
                    if y1 < Y0 or y0 > Y1:
                        continue
                    span_index += 1
                    writer.writerow([
                        f"S{span_index:03d}",
                        span["text"],
                        span["font"],
                        f"{span['size']:.3f}",
                        *fmt_box(span["bbox"]),
                    ])

    with (ROOT / "vector_drawings.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["drawing_id", "seqno", "type", "x0_pt", "y0_pt", "x1_pt", "y1_pt", "stroke_width_pt", "item_count"])
        drawing_index = 0
        for drawing in page.get_drawings():
            if drawing["rect"].y1 < Y0 or drawing["rect"].y0 > Y1:
                continue
            drawing_index += 1
            width = "" if drawing["width"] is None else f"{drawing['width']:.3f}"
            writer.writerow([
                f"D{drawing_index:03d}",
                drawing["seqno"],
                drawing["type"],
                *fmt_box(drawing["rect"]),
                width,
                len(drawing["items"]),
            ])

    print(f"page=737 spans={span_index} drawings={drawing_index}")


if __name__ == "__main__":
    main()
