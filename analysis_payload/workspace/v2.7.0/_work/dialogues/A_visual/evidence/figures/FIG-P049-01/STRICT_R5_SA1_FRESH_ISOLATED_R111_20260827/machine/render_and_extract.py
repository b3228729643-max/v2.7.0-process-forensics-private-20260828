from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r111_fullbook\main_full.pdf"
)
ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence"
    r"\figures\FIG-P049-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827"
)
OUT = ROOT / "visual"
MACHINE = ROOT / "machine"
PAGE_INDEX_ZERO = 47
CLIP_PT = fitz.Rect(138.0, 60.0, 465.0, 230.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def save_pixmap(page: fitz.Page, dpi: int, path: Path, clip: fitz.Rect | None = None) -> None:
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False, clip=clip)
    pix.save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MACHINE.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX_ZERO]

    full_200 = OUT / "01_full_page_physical_048_200dpi.png"
    full_300 = OUT / "02_full_page_physical_048_300dpi.png"
    native = OUT / "03_figure_roi_native300dpi_native1x.png"
    gray = OUT / "04_figure_roi_grayscale_native300dpi.png"
    nearest8 = OUT / "05_figure_roi_nearest_neighbor8x.png"
    overlay = OUT / "06_machine_text_bbox_overlay_native300dpi.png"

    save_pixmap(page, 200, full_200)
    save_pixmap(page, 300, full_300)
    save_pixmap(page, 300, native, CLIP_PT)

    with Image.open(native) as image:
        rgb = image.convert("RGB")
        rgb.convert("L").save(gray)
        rgb.resize((rgb.width * 8, rgb.height * 8), Image.Resampling.NEAREST).save(nearest8)

        annotated = rgb.copy()
        draw = ImageDraw.Draw(annotated)
        font = ImageFont.load_default()
        scale = 300.0 / 72.0
        words = []
        for word_index, word in enumerate(page.get_text("words", sort=True), start=1):
            x0, y0, x1, y1, text, block, line, word_no = word[:8]
            rect = fitz.Rect(x0, y0, x1, y1)
            if not rect.intersects(CLIP_PT):
                continue
            px = [
                round((x0 - CLIP_PT.x0) * scale, 3),
                round((y0 - CLIP_PT.y0) * scale, 3),
                round((x1 - CLIP_PT.x0) * scale, 3),
                round((y1 - CLIP_PT.y0) * scale, 3),
            ]
            words.append(
                {
                    "machine_word_id": f"MW-{word_index:03d}",
                    "text": text,
                    "pdf_bbox_pt": [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)],
                    "roi_bbox_px": px,
                    "pdf_block": block,
                    "pdf_line": line,
                    "pdf_word_no": word_no,
                }
            )
            draw.rectangle(px, outline=(220, 0, 0), width=2)
            draw.text((px[0] + 2, max(0, px[1] - 11)), f"MW-{word_index:03d}", fill=(220, 0, 0), font=font)
        annotated.save(overlay)

    drawings = []
    for drawing_index, drawing in enumerate(page.get_drawings(), start=1):
        rect = drawing["rect"]
        if not rect.intersects(CLIP_PT):
            continue
        drawings.append(
            {
                "machine_drawing_id": f"MD-{drawing_index:03d}",
                "type": drawing.get("type"),
                "pdf_bbox_pt": [round(rect.x0, 4), round(rect.y0, 4), round(rect.x1, 4), round(rect.y1, 4)],
                "item_count": len(drawing.get("items", [])),
                "stroke_width_pt": drawing.get("width"),
                "stroke_color": drawing.get("color"),
                "fill_color": drawing.get("fill"),
                "dashes": drawing.get("dashes"),
            }
        )

    (MACHINE / "pdf_text_word_candidates.json").write_text(
        json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (MACHINE / "pdf_vector_drawing_candidates.json").write_text(
        json.dumps(drawings, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    outputs = {}
    for path in sorted(OUT.iterdir()):
        with Image.open(path) as image:
            outputs[path.name] = {
                "width_px": image.width,
                "height_px": image.height,
                "mode": image.mode,
                "sha256": sha256(path),
            }

    metadata = {
        "source_pdf": str(PDF),
        "source_pdf_sha256": sha256(PDF),
        "page_count": doc.page_count,
        "independently_located_physical_page_1based": PAGE_INDEX_ZERO + 1,
        "printed_page_number_visible": 35,
        "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
        "figure_clip_pt": [CLIP_PT.x0, CLIP_PT.y0, CLIP_PT.x1, CLIP_PT.y1],
        "native_scale_px_per_pt": 300.0 / 72.0,
        "nearest_neighbor8x_source": native.name,
        "nearest_neighbor8x_resampling": "PIL.Image.Resampling.NEAREST",
        "machine_text_candidate_count": len(words),
        "machine_vector_drawing_candidate_count": len(drawings),
        "outputs": outputs,
    }
    (MACHINE / "render_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
