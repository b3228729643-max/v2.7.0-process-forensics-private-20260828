from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


PAGE_INDEX = 679
RED = np.array((255, 0, 0), dtype=np.uint8)


def read_csv(path: Path) -> tuple[list[dict], list[str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), reader.fieldnames or []


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rgb(hex_color: str) -> np.ndarray:
    return np.array(tuple(int(hex_color.lstrip("#")[n:n + 2], 16) for n in (0, 2, 4)), dtype=np.float32)


def mode_color(image: np.ndarray) -> np.ndarray:
    colors, counts = np.unique(image.reshape(-1, 3), axis=0, return_counts=True)
    return colors[np.argmax(counts)].astype(np.float32)


def foreground_for_color(image: np.ndarray, foreground: np.ndarray) -> np.ndarray:
    bg = mode_color(image)
    direction = bg - foreground
    denom = float(np.dot(direction, direction))
    pixels = image.astype(np.float32)
    alpha = np.einsum("...i,i->...", bg - pixels, direction) / denom
    reconstructed = bg - alpha[..., None] * direction
    residual = np.linalg.norm(pixels - reconstructed, axis=2)
    return (alpha >= 20.0 / 255.0) & (alpha <= 1.05) & (residual <= 18.0)


def mask_image(mask: np.ndarray) -> Image.Image:
    arr = np.full((mask.shape[0], mask.shape[1], 3), 255, dtype=np.uint8)
    arr[mask] = (0, 0, 0)
    return Image.fromarray(arr, "RGB")


def triad(original: Image.Image, overlay: Image.Image, only: Image.Image) -> Image.Image:
    images = [piece.resize((piece.width * 8, piece.height * 8), Image.Resampling.NEAREST) for piece in (original, overlay, only)]
    out = Image.new("RGB", (sum(item.width for item in images) + 16, max(item.height for item in images)), "white")
    x = 0
    for item in images:
        out.paste(item, (x, 0))
        x += item.width + 8
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    rows, fields = read_csv(root / "after_font_audit.csv")
    cal_rows, cal_fields = read_csv(root / "calibration" / "low_profile_punctuation_calibration.csv")
    rows_by_id = {row["GLYPH_ID"]: row for row in rows}
    cal_by_id = {row["GLYPH_ID"]: row for row in cal_rows}
    source = fitz.open(args.pdf)
    for gid, cal in cal_by_id.items():
        if cal["CALIBRATION_TYPE"] != "R95_PDF_FORM_XOBJECT_1_TO_1_RERENDER":
            continue
        glyph = rows_by_id[gid]
        x0, y0, x1, y1 = [float(value) for value in glyph["PDF_BBOX_PT"].split(",")]
        # Rawdict char bbox plus 0.25pt gives one native-pixel safety margin without admitting neighbors.
        margin = 0.25
        clip = fitz.Rect(x0 - margin, y0 - margin, x1 + margin, y1 + margin)
        pdf_path = root / "calibration" / f"cal_{glyph['SAFE_STEM']}_r95_form_calibrator.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
        output = fitz.open()
        page = output.new_page(width=clip.width, height=clip.height)
        page.show_pdf_page(page.rect, source, PAGE_INDEX, clip=clip)
        output.save(pdf_path)
        output.close()
        prefix = pdf_path.with_suffix("")
        png_path = prefix.with_suffix(".png")
        if png_path.exists():
            png_path.unlink()
        subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(pdf_path), str(prefix)], check=True)
        original = Image.open(png_path).convert("RGB")
        arr = np.asarray(original)
        mask = foreground_for_color(arr, rgb(glyph["COLOR_HEX"]))
        ref_h = int(mask.any(axis=1).sum())
        ref_area = int(mask.sum())
        over_arr = arr.copy()
        over_arr[mask] = RED
        overlay = Image.fromarray(over_arr, "RGB")
        only = mask_image(mask)
        base = root / "calibration" / f"cal_{glyph['SAFE_STEM']}"
        original.save(base.with_name(base.name + "_original_1x.png"))
        overlay.save(base.with_name(base.name + "_target_overlay_1x.png"))
        only.save(base.with_name(base.name + "_mask_only_1x.png"))
        triad(original, overlay, only).save(base.with_name(base.name + "_triad_8x_nearest.png"))
        h_ratio = int(glyph["H_INK_PX"]) / ref_h if ref_h else 0.0
        area_ratio = int(glyph["INK_AREA_PX"]) / ref_area if ref_area else 0.0
        result = "PASS" if 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 else "FAIL"
        cal.update({
            "CALIBRATION_SOURCE": str(pdf_path.relative_to(root)).replace("\\", "/"),
            "CALIBRATION_H_INK_PX": str(ref_h), "CALIBRATION_AREA_PX": str(ref_area),
            "H_INK_RATIO": f"{h_ratio:.6f}", "AREA_RATIO": f"{area_ratio:.6f}", "RESULT": result,
            "EVIDENCE_8X": str(base.with_name(base.name + "_triad_8x_nearest.png").relative_to(root)).replace("\\", "/"),
        })
        glyph["LOW_PROFILE_CALIBRATION_RESULT"] = result
        glyph["LOW_PROFILE_H_RATIO"] = f"{h_ratio:.6f}"
        glyph["LOW_PROFILE_AREA_RATIO"] = f"{area_ratio:.6f}"
        glyph["PIXEL_GATE_RESULT"] = result
        glyph["PASS_FAIL"] = "PASS" if glyph["EFFECTIVE_PT_RESULT"] == "PASS" and result == "PASS" and int(glyph["MASK_PIXELS"]) > 0 else "FAIL"
    source.close()
    write_csv(root / "after_font_audit.csv", rows, fields)
    write_csv(root / "calibration" / "low_profile_punctuation_calibration.csv", cal_rows, cal_fields)
    (root / "calibration" / "low_profile_punctuation_calibration.json").write_text(json.dumps(cal_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    pixels, pix_fields = read_csv(root / "after_pixel_measurements.csv")
    for row in pixels:
        glyph = rows_by_id[row["ELEMENT_ID"]]
        row["PASS_FAIL"] = glyph["PASS_FAIL"]
    write_csv(root / "after_pixel_measurements.csv", pixels, pix_fields)
    summary_path = root / "final_table_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["glyph_font_failures"] = [row["GLYPH_ID"] for row in rows if row["PASS_FAIL"] == "FAIL"]
    summary["low_profile_calibration_failures"] = [row["GLYPH_ID"] for row in cal_rows if row["RESULT"] != "PASS"]
    summary["overall_pre_manual_result"] = "FAIL" if summary["glyph_font_failures"] or summary["relation_failures"] or summary["edge_failures"] or summary["graphic_mask_failures"] else "PENDING_MANUAL_AND_VISUAL"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"fixed_form_calibrations": sum(1 for row in cal_rows if row["CALIBRATION_TYPE"] == "R95_PDF_FORM_XOBJECT_1_TO_1_RERENDER"), "remaining_low_profile_failures": summary["low_profile_calibration_failures"], "glyph_fails": len(summary["glyph_font_failures"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
