from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R5_SA3_FRESH_ISOLATED_R115_20260828")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf")
EXPECTED_BYTES = 4_967_161
EXPECTED_SHA256 = "93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F"
PAGE_NUMBER = 116
FIGURE_RECT = fitz.Rect(125, 338, 470, 552)
PAGE_INTEGRATION_RECT = fitz.Rect(60, 250, 535, 635)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def render(page: fitz.Page, rect: fitz.Rect, dpi: int, path: Path, colorspace=fitz.csRGB) -> dict:
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pixmap = page.get_pixmap(matrix=matrix, clip=rect, alpha=False, colorspace=colorspace)
    pixmap.save(path)
    return {
        "file": path.name,
        "dpi": dpi,
        "rect_pt": [rect.x0, rect.y0, rect.x1, rect.y1],
        "width_px": pixmap.width,
        "height_px": pixmap.height,
        "colorspace": "GRAY" if colorspace == fitz.csGRAY else "RGB",
    }


def nearest8(source: Path, target: Path) -> dict:
    with Image.open(source) as image:
        enlarged = image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)
        enlarged.save(target)
        return {
            "file": target.name,
            "source": source.name,
            "scale": 8,
            "resampling": "NEAREST",
            "width_px": enlarged.width,
            "height_px": enlarged.height,
        }


def main() -> None:
    if not ROOT.is_dir():
        raise SystemExit("fixed evidence root missing")
    if not PDF.is_file():
        raise SystemExit("allowlisted R115 PDF missing")
    if PDF.stat().st_size != EXPECTED_BYTES or sha256(PDF) != EXPECTED_SHA256:
        raise SystemExit("allowlisted R115 PDF identity mismatch")

    output = ROOT / "render"
    output.mkdir(exist_ok=False)
    document = fitz.open(PDF)
    if len(document) != 817:
        raise SystemExit("unexpected R115 page count")
    page = document[PAGE_NUMBER - 1]

    manifest: dict[str, object] = {
        "input_pdf": str(PDF),
        "input_bytes": EXPECTED_BYTES,
        "input_sha256": EXPECTED_SHA256,
        "physical_page": PAGE_NUMBER,
        "page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
        "renders": [],
        "nearest_enlargements": [],
    }
    renders = manifest["renders"]
    enlargements = manifest["nearest_enlargements"]
    assert isinstance(renders, list)
    assert isinstance(enlargements, list)

    renders.append(render(page, page.rect, 200, output / "full_page_200dpi.png"))
    renders.append(render(page, PAGE_INTEGRATION_RECT, 300, output / "page_integration_300dpi.png"))
    renders.append(render(page, FIGURE_RECT, 72, output / "figure_native1x_72dpi.png"))
    enlargements.append(nearest8(output / "figure_native1x_72dpi.png", output / "figure_nearest8x_from_72dpi.png"))
    renders.append(render(page, FIGURE_RECT, 300, output / "figure_raw_300dpi.png"))
    renders.append(render(page, FIGURE_RECT, 300, output / "figure_grayscale_300dpi.png", fitz.csGRAY))

    roi_rows: list[dict[str, str]] = []
    with (ROOT / "critical_roi_registry.csv").open("r", encoding="utf-8", newline="") as stream:
        roi_rows.extend(csv.DictReader(stream))
    for row in roi_rows:
        roi_id = row["ROI_ID"]
        rect = fitz.Rect([float(value) for value in row["PDF_RECT_PT"].split(",")])
        raw = output / f"{roi_id}_raw_300dpi.png"
        native = output / f"{roi_id}_native1x_72dpi.png"
        enlarged = output / f"{roi_id}_nearest8x.png"
        renders.append(render(page, rect, 300, raw))
        renders.append(render(page, rect, 72, native))
        enlargements.append(nearest8(native, enlarged))

    overlay_path = output / "reader_text_overlay_300dpi.png"
    figure_300 = output / "figure_raw_300dpi.png"
    with Image.open(figure_300).convert("RGB") as overlay:
        draw = ImageDraw.Draw(overlay)
        scale = 300.0 / 72.0
        with (ROOT / "denominator_freeze.csv").open("r", encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                if row["PANEL_ID"] != "P1":
                    continue
                x0, y0, x1, y1 = [float(value) for value in row["PDF_BBOX_PT"].split(",")]
                box = (
                    int(round((x0 - FIGURE_RECT.x0) * scale)),
                    int(round((y0 - FIGURE_RECT.y0) * scale)),
                    int(round((x1 - FIGURE_RECT.x0) * scale)),
                    int(round((y1 - FIGURE_RECT.y0) * scale)),
                )
                draw.rectangle(box, outline=(220, 0, 0), width=3)
                draw.text((box[0], max(0, box[1] - 14)), row["ELEMENT_ID"], fill=(220, 0, 0))
        overlay.save(overlay_path)
        renders.append({
            "file": overlay_path.name,
            "source": figure_300.name,
            "width_px": overlay.width,
            "height_px": overlay.height,
            "overlay": "frozen reader-visible element boxes and IDs",
        })

    text_blocks = []
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text, block_no, block_type = block
        if fitz.Rect(x0, y0, x1, y1).intersects(PAGE_INTEGRATION_RECT):
            text_blocks.append({
                "block_no": block_no,
                "block_type": block_type,
                "bbox_pt": [x0, y0, x1, y1],
                "text": text,
            })
    (ROOT / "page116_target_text_blocks.json").write_text(
        json.dumps(text_blocks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "mechanical_render_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
