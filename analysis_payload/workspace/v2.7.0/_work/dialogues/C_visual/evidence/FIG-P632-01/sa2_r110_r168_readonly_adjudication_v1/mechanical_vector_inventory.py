from __future__ import annotations

import csv
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r110_fullbook\main_full.pdf"
)


def main() -> None:
    page = fitz.open(PDF)[681]
    rows = []
    for index, drawing in enumerate(page.get_drawings(), start=1):
        rect = drawing["rect"]
        if rect.y1 < 55 or rect.y0 > 451:
            continue
        rows.append(
            {
                "drawing_id": f"D{index:03d}",
                "pdf_x0": f"{rect.x0:.3f}",
                "pdf_y0": f"{rect.y0:.3f}",
                "pdf_x1": f"{rect.x1:.3f}",
                "pdf_y1": f"{rect.y1:.3f}",
                "draw_type": drawing.get("type"),
                "stroke_color": repr(drawing.get("color")),
                "fill_color": repr(drawing.get("fill")),
                "line_width_pt": drawing.get("width"),
                "line_cap": repr(drawing.get("lineCap")),
                "line_join": drawing.get("lineJoin"),
                "dashes": drawing.get("dashes"),
                "item_count": len(drawing.get("items", [])),
            }
        )
    path = ROOT / "mechanical_vector_drawings.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "mechanical_vector_summary.txt").write_text(
        f"drawing_count={len(rows)}\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
