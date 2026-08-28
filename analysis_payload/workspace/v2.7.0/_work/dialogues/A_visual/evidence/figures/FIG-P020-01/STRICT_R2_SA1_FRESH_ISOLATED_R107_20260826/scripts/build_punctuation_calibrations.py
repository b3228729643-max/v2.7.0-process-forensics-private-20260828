from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path

import cairosvg
import fitz
import numpy as np
from fontTools.cffLib import CFFFontSet
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R2_SA1_FRESH_ISOLATED_R107_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
PAGE_INDEX = 16
PX_PER_FONT_UNIT = (10.0 * 300.0 / 72.0) / 1000.0


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def trace_glyph_ids(page: fitz.Page) -> dict[str, int]:
    result: dict[str, int] = {}
    for span in page.get_texttrace():
        font = span["font"]
        color = tuple(round(float(v), 6) for v in span["color"])
        size = float(span["size"])
        for unicode_value, glyph_id, _origin, _bbox in span["chars"]:
            if unicode_value == 65306 and font == "NotoSerifSC-ExtraLight" and abs(size - 9.96264) < 0.01 and color == (0.41962, 0.44707, 0.50195):
                result["G053"] = int(glyph_id)
            if unicode_value == 46 and font == "STIXTwoText-Bold" and abs(size - 9.96264) < 0.01 and color == (0.12158, 0.13725, 0.15686):
                result["G068"] = int(glyph_id)
    return result


def font_xrefs(page: fitz.Page) -> dict[str, int]:
    result: dict[str, int] = {}
    for xref, _ext, _type, basefont, _name, _encoding, _referencer in page.get_fonts(full=True):
        clean = basefont.split("+", 1)[-1]
        result[clean] = int(xref)
    return result


def outline_from_font(font_bytes: bytes, extension: str, glyph_id: int) -> tuple[str, tuple[float, float, float, float], str, int]:
    if extension.lower() in {"ttf", "otf"}:
        font = TTFont(io.BytesIO(font_bytes))
        glyph_order = font.getGlyphOrder()
        if glyph_id >= len(glyph_order):
            raise RuntimeError(f"Glyph id {glyph_id} exceeds font glyph count {len(glyph_order)}")
        glyph_name = glyph_order[glyph_id]
        glyph = font.getGlyphSet()[glyph_name]
        bounds_pen = BoundsPen(font.getGlyphSet())
        glyph.draw(bounds_pen)
        svg_pen = SVGPathPen(font.getGlyphSet())
        glyph.draw(svg_pen)
        units_per_em = int(font["head"].unitsPerEm)
        return svg_pen.getCommands(), tuple(float(v) for v in bounds_pen.bounds), glyph_name, units_per_em

    cff = CFFFontSet()
    cff.decompile(io.BytesIO(font_bytes), None)
    top = cff[cff.fontNames[0]]
    glyph_name = f"cid{glyph_id:05d}"
    if glyph_name not in top.CharStrings:
        raise RuntimeError(f"CFF glyph {glyph_name} not found")
    glyph = top.CharStrings[glyph_name]
    bounds_pen = BoundsPen(None)
    glyph.draw(bounds_pen)
    svg_pen = SVGPathPen(None)
    glyph.draw(svg_pen)
    units_per_em = int(round(1.0 / float(top.FontMatrix[0])))
    return svg_pen.getCommands(), tuple(float(v) for v in bounds_pen.bounds), glyph_name, units_per_em


def render_outline(commands: str, bounds: tuple[float, float, float, float], units_per_em: int, target_rgb: tuple[int, int, int], stem: Path) -> tuple[int, int, int, list[int]]:
    x0, y0, x1, y1 = bounds
    px_per_unit = (10.0 * 300.0 / 72.0) / float(units_per_em)
    pad_units = 4.0 / px_per_unit
    vx0 = x0 - pad_units
    vy0 = -(y1 + pad_units)
    vw = (x1 - x0) + 2 * pad_units
    vh = (y1 - y0) + 2 * pad_units
    width = max(1, int(math.ceil(vw * px_per_unit)))
    height = max(1, int(math.ceil(vh * px_per_unit)))
    color = f"rgb({target_rgb[0]},{target_rgb[1]},{target_rgb[2]})"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx0} {vy0} {vw} {vh}" width="{width}" height="{height}">'
        '<rect x="-100000" y="-100000" width="200000" height="200000" fill="white"/>'
        f'<path d="{commands}" transform="scale(1,-1)" fill="{color}"/>'
        '</svg>\n'
    )
    svg_path = stem.with_suffix(".svg")
    svg_path.write_text(svg, encoding="utf-8")
    png_path = stem.with_name(stem.name + "_original_1x.png")
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=width, output_height=height)
    image = Image.open(png_path).convert("RGB")
    arr = np.array(image)
    bg = np.array([255, 255, 255], dtype=np.int16)
    contrast = np.max(np.abs(arr.astype(np.int16) - bg), axis=2)
    mask = contrast >= 20
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise RuntimeError(f"Empty calibration mask for {stem.name}")
    h_ink = int(ys.max() - ys.min() + 1)
    area = int(mask.sum())
    mask_img = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L").convert("RGB")
    mask_img.save(stem.with_name(stem.name + "_mask_only_1x.png"))
    overlay = arr.copy()
    overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
    overlay_img = Image.fromarray(overlay, "RGB")
    overlay_img.save(stem.with_name(stem.name + "_overlay_1x.png"))
    overlay_img.resize((overlay_img.width * 8, overlay_img.height * 8), Image.Resampling.NEAREST).save(
        stem.with_name(stem.name + "_overlay_8x_nearest.png")
    )
    return h_ink, area, units_per_em, [width, height]


def main() -> None:
    output_dir = ROOT / "02_extraction" / "punctuation_calibrations"
    output_dir.mkdir(parents=True, exist_ok=True)
    font_dir = output_dir / "fonts_from_official_pdf"
    font_dir.mkdir(parents=True, exist_ok=True)

    glyph_rows = {row["object_id"]: row for row in load_rows(ROOT / "02_extraction" / "glyph_inventory.csv")}
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    glyph_ids = trace_glyph_ids(page)
    xrefs = font_xrefs(page)
    specs = {
        "G053": {"char": "：", "font": "NotoSerifSC-ExtraLight"},
        "G068": {"char": ".", "font": "STIXTwoText-Bold"},
    }
    if set(glyph_ids) != set(specs):
        raise RuntimeError(f"Could not uniquely trace both calibration glyphs: {glyph_ids}")

    rows: list[dict[str, object]] = []
    font_meta: list[dict[str, object]] = []
    for object_id, spec in specs.items():
        xref = xrefs[spec["font"]]
        name, extension, font_type, font_bytes = doc.extract_font(xref)
        font_path = font_dir / f"xref{xref}_{spec['font']}.{extension}"
        font_path.write_bytes(font_bytes)
        commands, bounds, glyph_name, units_per_em = outline_from_font(font_bytes, extension, glyph_ids[object_id])
        target_rgb = tuple(json.loads(glyph_rows[object_id]["font_color_rgb"]))
        stem = output_dir / f"{object_id}_actual_pdf_font_calibration"
        h_ink, area, units_per_em, native_size = render_outline(commands, bounds, units_per_em, target_rgb, stem)
        target_h = int(glyph_rows[object_id]["h_ink_px"])
        target_area = int(glyph_rows[object_id]["ink_area_px"])
        h_ratio = target_h / h_ink
        area_ratio = target_area / area
        rows.append(
            {
                "glyph_id": object_id,
                "char": spec["char"],
                "codepoint": f"U+{ord(spec['char']):04X}",
                "font_name": spec["font"],
                "pdf_font_xref": xref,
                "pdf_trace_glyph_id": glyph_ids[object_id],
                "actual_font_glyph_name": glyph_name,
                "effective_pt": 10.0,
                "dpi": 300,
                "threshold_delta_from_white": 20,
                "target_h_ink_px": target_h,
                "calibration_h_ink_px": h_ink,
                "h_ratio_target_to_calibration": round(h_ratio, 6),
                "target_ink_area_px": target_area,
                "calibration_ink_area_px": area,
                "area_ratio_target_to_calibration": round(area_ratio, 6),
                "raster_difference_px": abs(target_h - h_ink),
                "native_calibration_px": native_size,
                "machine_calibration_gate": "WITHIN_0_92_1_08" if 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 else "R168_ADVISORY_RASTER_OR_ENGINE_DIFFERENCE",
                "source_svg": str(stem.relative_to(ROOT).with_suffix(".svg")).replace("\\", "/"),
                "original_1x": str(stem.relative_to(ROOT).with_name(stem.name + "_original_1x.png")).replace("\\", "/"),
                "mask_only_1x": str(stem.relative_to(ROOT).with_name(stem.name + "_mask_only_1x.png")).replace("\\", "/"),
                "overlay_1x": str(stem.relative_to(ROOT).with_name(stem.name + "_overlay_1x.png")).replace("\\", "/"),
                "overlay_8x_nearest": str(stem.relative_to(ROOT).with_name(stem.name + "_overlay_8x_nearest.png")).replace("\\", "/"),
            }
        )
        font_meta.append(
            {
                "font_name": spec["font"],
                "pdf_xref": xref,
                "extracted_name": name,
                "extension": extension,
                "font_type": font_type,
                "bytes": len(font_bytes),
                "sha256": sha256(font_bytes),
                "units_per_em": units_per_em,
                "stored_path": str(font_path.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    write_csv(ROOT / "05_ledgers" / "punctuation_separate_calibration_machine.csv", rows)
    (ROOT / "02_extraction" / "punctuation_calibrations" / "font_extraction_metadata.json").write_text(
        json.dumps(font_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "02_extraction" / "punctuation_calibrations" / "calibration_machine_summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
