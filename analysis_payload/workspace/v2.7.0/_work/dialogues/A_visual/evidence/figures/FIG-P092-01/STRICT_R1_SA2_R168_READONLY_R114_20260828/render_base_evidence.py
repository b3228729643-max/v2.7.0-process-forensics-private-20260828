from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R1_SA2_R168_READONLY_R114_20260828")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C06\fig_v1_c06_binary_entropy.tex")

EXPECTED = {
    PDF: (4_967_122, "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6"),
    SOURCE: (2_094, "EA3FB7B92ED3B7B2755D513B5F3DEECF7D7114E8DC711F3AB2FE50E9C7EE8608"),
}

PAGE_INDEX = 95  # independently located current R114 physical page 96
FIGURE_CLIP_PT = fitz.Rect(115.0, 145.0, 483.0, 359.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def assert_identity() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path, (expected_bytes, expected_hash) in EXPECTED.items():
        actual_bytes = path.stat().st_size
        actual_hash = sha256(path)
        if (actual_bytes, actual_hash) != (expected_bytes, expected_hash):
            raise RuntimeError(f"identity mismatch: {path}")
        rows.append(
            {
                "path": str(path),
                "bytes": actual_bytes,
                "sha256": actual_hash,
            }
        )
    return rows


def rect_values(rect: fitz.Rect) -> list[float]:
    return [round(value, 4) for value in (rect.x0, rect.y0, rect.x1, rect.y1)]


def main() -> None:
    ROOT.mkdir(parents=False, exist_ok=True)
    identity = assert_identity()
    document = fitz.open(PDF)
    if document.page_count != 817:
        raise RuntimeError(f"unexpected page count: {document.page_count}")
    page = document[PAGE_INDEX]
    caption_hits = page.search_for("二元熵在")
    if len(caption_hits) != 1:
        raise RuntimeError(f"caption hit count on page 96: {len(caption_hits)}")

    full_200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72), alpha=False)
    full_200.save(ROOT / "full_page_200dpi.png")

    full_300 = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False)
    full_300.save(ROOT / "full_page_native_300dpi.png")

    crop_300 = page.get_pixmap(
        matrix=fitz.Matrix(300 / 72, 300 / 72), clip=FIGURE_CLIP_PT, alpha=False
    )
    crop_path = ROOT / "figure_crop_native_300dpi.png"
    crop_300.save(crop_path)
    with Image.open(crop_path) as image:
        image.convert("L").save(ROOT / "figure_crop_grayscale_300dpi.png")

    spans: list[dict[str, object]] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bbox = fitz.Rect(span["bbox"])
                if bbox.intersects(FIGURE_CLIP_PT):
                    spans.append(
                        {
                            "text": span["text"],
                            "bbox_pt": rect_values(bbox),
                            "font": span["font"],
                            "size_pt": round(span["size"], 4),
                            "color": span["color"],
                            "flags": span["flags"],
                        }
                    )

    drawings: list[dict[str, object]] = []
    for index, drawing in enumerate(page.get_drawings()):
        rect = fitz.Rect(drawing["rect"])
        if rect.intersects(FIGURE_CLIP_PT):
            drawings.append(
                {
                    "drawing_index": index,
                    "rect_pt": rect_values(rect),
                    "type": drawing["type"],
                    "fill": drawing.get("fill"),
                    "color": drawing.get("color"),
                    "width": drawing.get("width"),
                    "dashes": drawing.get("dashes"),
                    "item_count": len(drawing.get("items", [])),
                }
            )

    metadata = {
        "input_identity": identity,
        "page_count": document.page_count,
        "physical_page_1based": PAGE_INDEX + 1,
        "printed_page": 83,
        "page_rect_pt": rect_values(page.rect),
        "figure_clip_pt": rect_values(FIGURE_CLIP_PT),
        "caption_search_bbox_pt": [rect_values(rect) for rect in caption_hits],
        "render_contract": {
            "full_page_200dpi": "direct PDF raster, no post-resize",
            "full_page_native_300dpi": "direct PDF raster, no post-resize",
            "figure_crop_native_300dpi": "direct clipped PDF raster, no post-resize",
            "figure_crop_grayscale_300dpi": "mode-L conversion of the native 300 dpi crop, no resize",
        },
    }
    (ROOT / "machine_render_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "machine_pdf_text_spans.json").write_text(
        json.dumps(spans, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "machine_pdf_drawings.json").write_text(
        json.dumps(drawings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (ROOT / "machine_pdf_text_spans.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["text", "x0_pt", "y0_pt", "x1_pt", "y1_pt", "font", "size_pt", "color", "flags"],
        )
        writer.writeheader()
        for span in spans:
            x0, y0, x1, y1 = span["bbox_pt"]
            writer.writerow(
                {
                    "text": span["text"],
                    "x0_pt": x0,
                    "y0_pt": y0,
                    "x1_pt": x1,
                    "y1_pt": y1,
                    "font": span["font"],
                    "size_pt": span["size_pt"],
                    "color": span["color"],
                    "flags": span["flags"],
                }
            )

    print(json.dumps({"page": PAGE_INDEX + 1, "span_count": len(spans), "drawing_count": len(drawings)}))


if __name__ == "__main__":
    main()
