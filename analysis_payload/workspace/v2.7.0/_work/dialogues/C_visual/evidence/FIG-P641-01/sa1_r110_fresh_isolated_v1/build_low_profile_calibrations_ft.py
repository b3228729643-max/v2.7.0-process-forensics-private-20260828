from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import fitz
import freetype
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
PAGE_INDEX = 690
TARGETS = [
    dict(element_id="TXT_0026_UFF1A", char="：", codepoint="U+FF1A", xref=48, gid=30581,
         font="NotoSerifSC-ExtraLight", declared_pt=9.2, pdf_bp=9.165630340576172,
         rgb=(15, 118, 110), bbox=(1317, 2329, 1356, 2368), mask="txt_0026_uff1a.png"),
    dict(element_id="TXT_0088_U002E", char=".", codepoint="U+002E", xref=47, gid=1829,
         font="STIXTwoText-Bold", declared_pt=10.0, pdf_bp=10.061773300170898,
         rgb=(31, 35, 40), bbox=(413, 2919, 425, 2962), mask="txt_0088_u002e.png"),
    dict(element_id="TXT_0125_UFF1B", char="；", codepoint="U+FF1B", xref=48, gid=30582,
         font="NotoSerifSC-ExtraLight", declared_pt=10.0, pdf_bp=9.962639808654785,
         rgb=(31, 35, 40), bbox=(1754, 2920, 1797, 2963), mask="txt_0125_uff1b.png"),
    dict(element_id="TXT_0141_UFF0C", char="，", codepoint="U+FF0C", xref=48, gid=29783,
         font="NotoSerifSC-ExtraLight", declared_pt=10.0, pdf_bp=9.962639808654785,
         rgb=(31, 35, 40), bbox=(418, 2976, 460, 3019), mask="txt_0141_uff0c.png"),
]


def binary_target_mask(machine_mask: Image.Image) -> Image.Image:
    return machine_mask.convert("L").point(lambda p: 255 if p < 128 else 0)


def metrics(mask: Image.Image):
    bbox = mask.getbbox()
    if bbox is None:
        return None, 0, 0
    area = sum(1 for value in mask.get_flattened_data() if value)
    return bbox, bbox[3] - bbox[1], area


def render_glyph(font_bytes: bytes, glyph_id: int, size_bp: float, rgb):
    face = freetype.Face.from_bytes(font_bytes)
    face.set_char_size(0, round(size_bp * 64), 300, 300)
    face.load_glyph(glyph_id, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
    bitmap = face.glyph.bitmap
    gray = Image.frombytes("L", (bitmap.width, bitmap.rows), bytes(bitmap.buffer))
    mask = gray.point(lambda p: 255 if p >= 20 else 0)
    raster = Image.new("RGB", gray.size, "white")
    ink = Image.new("RGB", gray.size, rgb)
    raster.paste(ink, (0, 0), gray)
    return raster, mask


def centered_panel(image: Image.Image, width=330, height=250):
    canvas = Image.new("RGB", (width, height), "white")
    item = image.convert("RGB")
    item.thumbnail((width - 20, height - 45), Image.Resampling.NEAREST)
    canvas.paste(item, ((width - item.width) // 2, (height - item.height) // 2))
    return canvas


def main():
    out = ROOT / "calibrations"
    out.mkdir(exist_ok=True)
    doc = fitz.open(PDF)
    full = Image.open(ROOT / "full_page_native300dpi.png").convert("RGB")
    rows = []
    font_meta = {}
    for target in TARGETS:
        extracted = doc.extract_font(target["xref"])
        font_bytes = extracted[3]
        font_meta[str(target["xref"])] = {
            "embedded_name": extracted[0], "extension": extracted[1],
            "bytes": len(font_bytes), "sha256": hashlib.sha256(font_bytes).hexdigest().upper(),
        }
        current_raster = full.crop(target["bbox"])
        current_mask = binary_target_mask(Image.open(ROOT / "masks" / "glyph" / target["mask"]))
        cal_raster, cal_mask = render_glyph(font_bytes, target["gid"], target["pdf_bp"], target["rgb"])
        current_bbox, current_h, current_area = metrics(current_mask)
        cal_bbox, cal_h, cal_area = metrics(cal_mask)

        stem = target["element_id"].lower()
        current_raster.save(out / f"{stem}_current_native1x.png")
        current_mask.save(out / f"{stem}_current_mask_native1x.png")
        cal_raster.save(out / f"{stem}_calibration_native1x.png")
        cal_mask.save(out / f"{stem}_calibration_mask_native1x.png")
        overlay = cal_raster.copy()
        overlay.paste(Image.new("RGB", overlay.size, (255, 0, 0)), (0, 0), cal_mask)
        overlay.save(out / f"{stem}_calibration_overlay_native1x.png")
        overlay8 = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
        overlay8.save(out / f"{stem}_calibration_overlay_8x_nearest.png")

        current_tight = current_raster.crop(current_bbox)
        current_mask_tight = current_mask.crop(current_bbox)
        cal_tight = cal_raster.crop(cal_bbox)
        cal_mask_tight = cal_mask.crop(cal_bbox)
        views = [
            current_tight, cal_tight, cal_mask_tight,
            current_tight.resize((current_tight.width * 8, current_tight.height * 8), Image.Resampling.NEAREST),
            cal_tight.resize((cal_tight.width * 8, cal_tight.height * 8), Image.Resampling.NEAREST),
            overlay8,
        ]
        sheet = Image.new("RGB", (990, 500), "white")
        labels = ["CURRENT 1x", "CALIBRATION 1x", "CAL MASK 1x", "CURRENT 8x NN", "CALIBRATION 8x NN", "CAL OVERLAY 8x NN"]
        draw = ImageDraw.Draw(sheet)
        for i, view in enumerate(views):
            x = (i % 3) * 330
            y = (i // 3) * 250
            sheet.paste(centered_panel(view), (x, y))
            draw.text((x + 8, y + 8), labels[i], fill=(0, 0, 0))
        sheet.save(out / f"{stem}_calibration_contact.png")

        rows.append({
            "element_id": target["element_id"], "codepoint": target["codepoint"],
            "font": target["font"], "font_xref": target["xref"], "pdf_glyph_id": target["gid"],
            "declared_pt": target["declared_pt"], "pdf_size_bp": round(target["pdf_bp"], 6),
            "rgb": str(target["rgb"]), "current_h_px": current_h, "calibration_h_px": cal_h,
            "h_ratio_current_over_cal": round(current_h / cal_h, 6),
            "current_area_px": current_area, "calibration_area_px": cal_area,
            "area_ratio_current_over_cal": round(current_area / cal_area, 6),
            "contact_sheet": f"calibrations/{stem}_calibration_contact.png",
        })

    with (ROOT / "low_profile_external_calibration_metrics.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    provenance = {
        "source_pdf": str(PDF), "source_page_1_based": PAGE_INDEX + 1,
        "render_dpi": 300, "contrast_threshold": 20,
        "font_sources": font_meta,
        "method": "FreeType isolated glyph-index rerender at 300dpi from exact embedded PDF font program and PDF text size; no TeX and no saved PDF",
        "machine_decisions_generated": False,
    }
    (ROOT / "low_profile_external_calibration_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
