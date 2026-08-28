from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C05\fig_v1_c05_gaussian.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R3_SA3_FRESH_ISOLATED_R114_20260828")
QUERY = "方差增大使高斯密度变宽"
SCALE = 300.0 / 72.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def render(page: fitz.Page, clip: fitz.Rect, output: Path) -> None:
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, alpha=False)
    pix.save(output)


def crop_pixels(full: Image.Image, pdf_rect: fitz.Rect) -> Image.Image:
    return full.crop(tuple(round(value * SCALE) for value in pdf_rect))


def main() -> None:
    doc = fitz.open(PDF)
    hit_pages: list[int] = []
    hit_rects: dict[str, list[list[float]]] = {}
    for index in range(doc.page_count):
        rects = doc[index].search_for(QUERY)
        if rects:
            hit_pages.append(index + 1)
            hit_rects[str(index + 1)] = [list(rect) for rect in rects]
    if len(hit_pages) != 1:
        raise RuntimeError(f"Expected one current-PDF caption hit, got {hit_pages}")

    physical_page = hit_pages[0]
    page = doc[physical_page - 1]
    page_rect = page.rect
    figure_rect = fitz.Rect(82.0, 420.0, 510.0, 614.0)

    raw = {
        "pdf": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "source": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "query": QUERY,
        "page_count": doc.page_count,
        "hit_physical_pages": hit_pages,
        "hit_rects_pdf_points": hit_rects,
        "page_rect_pdf_points": list(page_rect),
        "figure_rect_pdf_points": list(figure_rect),
        "render_dpi": 300,
        "scale_px_per_pdf_point": SCALE,
    }
    (ROOT / "00_raw_locator_and_identity.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    render(page, page_rect, ROOT / "01_full_page_native_300dpi.png")
    full = Image.open(ROOT / "01_full_page_native_300dpi.png").convert("RGB")
    full.convert("L").save(ROOT / "02_full_page_grayscale_native_300dpi.png")

    figure = crop_pixels(full, figure_rect)
    figure.save(ROOT / "03_figure_crop_native_300dpi.png")
    figure.convert("L").save(ROOT / "04_figure_crop_grayscale_native_300dpi.png")

    # Raw text-span overlay: rectangles and block indices only, with no reviewer fields.
    overlay = figure.copy()
    draw = ImageDraw.Draw(overlay)
    span_rows: list[dict[str, object]] = []
    block_index = 0
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                rect = fitz.Rect(span["bbox"])
                if not rect.intersects(figure_rect):
                    continue
                px = [
                    round((rect.x0 - figure_rect.x0) * SCALE),
                    round((rect.y0 - figure_rect.y0) * SCALE),
                    round((rect.x1 - figure_rect.x0) * SCALE),
                    round((rect.y1 - figure_rect.y0) * SCALE),
                ]
                block_index += 1
                draw.rectangle(px, outline=(220, 0, 220), width=2)
                draw.text((px[0] + 2, max(0, px[1] - 12)), f"S{block_index:02d}", fill=(220, 0, 220))
                span_rows.append(
                    {
                        "raw_span_id": f"S{block_index:02d}",
                        "text": span["text"],
                        "bbox_pdf_points": list(rect),
                        "bbox_crop_pixels": px,
                        "font": span["font"],
                        "size_pdf_points": span["size"],
                    }
                )
    overlay.save(ROOT / "05_raw_text_span_overlay_native_300dpi.png")
    (ROOT / "05_raw_text_spans.json").write_text(
        json.dumps(span_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Critical native 300 dpi views and exact nearest-neighbour 8x derivatives.
    rois = {
        "roi_a_upper_annotation": fitz.Rect(330.0, 438.0, 448.0, 474.0),
        "roi_b_lower_annotation": fitz.Rect(372.0, 486.0, 505.0, 518.0),
        "roi_c_area_brace": fitz.Rect(245.0, 540.0, 365.0, 574.0),
        "roi_d_axes_ticks": fitz.Rect(88.0, 425.0, 155.0, 590.0),
        "roi_e_caption": fitz.Rect(132.0, 588.0, 456.0, 611.0),
    }
    roi_meta: dict[str, object] = {}
    for name, rect in rois.items():
        image = crop_pixels(full, rect)
        native_path = ROOT / f"06_{name}_native1x_300dpi.png"
        zoom_path = ROOT / f"06_{name}_nearest8x.png"
        image.save(native_path)
        image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(zoom_path)
        roi_meta[name] = {
            "rect_pdf_points": list(rect),
            "native_pixels": [image.width, image.height],
            "nearest8x_pixels": [image.width * 8, image.height * 8],
        }
    (ROOT / "06_roi_geometry.json").write_text(
        json.dumps(roi_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
