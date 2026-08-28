"""Evidence-local low-profile punctuation calibration for FIG-P020-01."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "calibration"
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf"
)
SCALE = 300.0 / 72.0


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fields} for row in rows)


def mode_rgb(array: np.ndarray) -> np.ndarray:
    values, counts = np.unique(array.reshape(-1, 3), axis=0, return_counts=True)
    return values[int(counts.argmax())].astype(float)


def mask_for_char(image: np.ndarray, bbox: list[float], color: int) -> tuple[np.ndarray, tuple[int, int, int, int], dict]:
    h, w = image.shape[:2]
    x0 = max(0, int(math.floor(bbox[0] * SCALE)))
    y0 = max(0, int(math.floor(bbox[1] * SCALE)))
    x1 = min(w, int(math.ceil(bbox[2] * SCALE)))
    y1 = min(h, int(math.ceil(bbox[3] * SCALE)))
    outer = image[max(0, y0 - 2) : min(h, y1 + 2), max(0, x0 - 2) : min(w, x1 + 2)]
    background = mode_rgb(outer)
    target = np.array(((color >> 16) & 255, (color >> 8) & 255, color & 255), dtype=float)
    pixels = image[y0:y1, x0:x1].astype(float)
    delta = target - background
    denom = float(np.dot(delta, delta))
    norm = math.sqrt(denom)
    alpha = ((pixels - background) * delta).sum(axis=2) / denom
    reconstructed = background + alpha[:, :, None] * delta
    residual = np.sqrt(((pixels - reconstructed) ** 2).sum(axis=2))
    local = (alpha >= 20.0 / norm) & (alpha <= 1.15) & (residual <= max(10.0, 0.08 * norm))
    mask = np.zeros((h, w), dtype=bool)
    mask[y0:y1, x0:x1] = local
    ys, xs = np.nonzero(mask)
    metrics = {
        "raw_bbox_px": [x0, y0, x1, y1],
        "mask_bbox_px": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
        "ink_area_px": int(mask.sum()),
        "h_ink_px": int(ys.max() - ys.min() + 1),
        "background_rgb": [int(v) for v in background],
    }
    return mask, (x0, y0, x1, y1), metrics


def triad(page: np.ndarray, mask: np.ndarray, raw_box: tuple[int, int, int, int], prefix: Path, label: str) -> dict:
    h, w = page.shape[:2]
    x0, y0, x1, y1 = raw_box
    box = (max(0, x0 - 5), max(0, y0 - 5), min(w, x1 + 5), min(h, y1 + 5))
    bx0, by0, bx1, by1 = box
    original = Image.fromarray(page[by0:by1, bx0:bx1], "RGB")
    overlay_np = np.asarray(original).copy()
    local = mask[by0:by1, bx0:bx1]
    overlay_np[local] = (255, 0, 0)
    overlay = Image.fromarray(overlay_np, "RGB")
    only_np = np.full_like(overlay_np, 255)
    only_np[local] = (0, 0, 0)
    only = Image.fromarray(only_np, "RGB")
    original_path = prefix.with_name(prefix.name + "_original_1x.png")
    overlay_path = prefix.with_name(prefix.name + "_target_overlay_1x.png")
    only_path = prefix.with_name(prefix.name + "_mask_only_1x.png")
    triad_path = prefix.with_name(prefix.name + "_triad_8x_nearest.png")
    original.save(original_path)
    overlay.save(overlay_path)
    only.save(only_path)
    panels = [image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST) for image in (original, overlay, only)]
    canvas = Image.new("RGB", (sum(p.width for p in panels) + 64, max(p.height for p in panels) + 52), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((8, 5), f"{label} | ORIGINAL | TARGET OVERLAY | MASK ONLY | 8x nearest", fill="black", font=font)
    x = 16
    for panel in panels:
        canvas.paste(panel, (x, 32))
        x += panel.width + 16
    canvas.save(triad_path)
    return {
        "RAW_1X": rel(original_path),
        "TARGET_OVERLAY_1X": rel(overlay_path),
        "MASK_ONLY_1X": rel(only_path),
        "TRIAD_8X": rel(triad_path),
    }


def candidate_char(pdf: Path, page_number: int, codepoint: str, font: str, color: int, size: float) -> tuple[dict, dict]:
    document = fitz.open(pdf)
    page = document[page_number - 1]
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if span["font"] != font or span["color"] != color or abs(float(span["size"]) - size) > 0.25:
                    continue
                for char in span["chars"]:
                    if char["c"] == codepoint:
                        return span, char
    raise RuntimeError(f"No matching calibration char {codepoint} on page {page_number}")


def read_table(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    CAL.mkdir(parents=True, exist_ok=True)
    manifest = read_table(ROOT / "glyph_id_filename_manifest.csv")
    pixel = {row["ELEMENT_ID"]: row for row in read_table(ROOT / "after_pixel_measurements.csv")}
    info = {row["ELEMENT_ID"]: row for row in manifest}

    # External direct-R95 candidates for the two unpaired codepoints.
    colon_pdf = CAL / "colon_r95_form_rerender_calibrator.pdf"
    colon_png = CAL / "colon_form_calibrator_page_native300.png"
    dot_png = CAL / "r95_page_048_dot_reference_native300.png"
    colon_span, colon_char = candidate_char(colon_pdf, 1, "：", "NotoSerifSC-ExtraLight", 7041664, 9.96264)
    colon_image = np.asarray(Image.open(colon_png).convert("RGB"))
    colon_mask, colon_box, colon_metrics = mask_for_char(colon_image, colon_char["bbox"], colon_span["color"])
    colon_paths = triad(colon_image, colon_mask, colon_box, CAL / "cal_colon_r95_form", "CAL_COLON_R95_FORM")

    dot_span, dot_char = candidate_char(PDF, 48, ".", "STIXTwoText-Bold", 2040616, 9.96264)
    dot_image = np.asarray(Image.open(dot_png).convert("RGB"))
    dot_mask, dot_box, dot_metrics = mask_for_char(dot_image, dot_char["bbox"], dot_span["color"])
    dot_paths = triad(dot_image, dot_mask, dot_box, CAL / "cal_dot_r95_page048", "CAL_DOT_R95_P048")

    external = {
        "F020_G053": {
            "id": "CAL_COLON_R95_FORM",
            "origin": "frozen R95 page 17 Form-XObject re-render of the isolated original colon paint operation",
            "span": colon_span,
            "char": colon_char,
            "metrics": colon_metrics,
            "paths": colon_paths,
            "page": "R95 page 17 re-rendered at 300dpi",
        },
        "F020_G068": {
            "id": "CAL_DOT_R95_P048",
            "origin": "independent visible R95 page 48 figure-caption digit run",
            "span": dot_span,
            "char": dot_char,
            "metrics": dot_metrics,
            "paths": dot_paths,
            "page": "R95 physical page 48 direct 300dpi",
        },
    }
    internal_map = {
        "F020_G007": "F020_G030",
        "F020_G030": "F020_G043",
        "F020_G043": "F020_G007",
        "F020_G089": "F020_G108",
        "F020_G108": "F020_G089",
    }

    rows: list[dict] = []
    targets = ["F020_G007", "F020_G030", "F020_G043", "F020_G053", "F020_G068", "F020_G089", "F020_G108"]
    for target in targets:
        target_info, target_pixel = info[target], pixel[target]
        if target in internal_map:
            reference = internal_map[target]
            reference_info, reference_pixel = info[reference], pixel[reference]
            cal_id = reference
            cal_origin = "separate visible glyph in this same final FIG-P020-01 raster"
            cal_font = reference_info["PDF_FONT"]
            cal_color = int(reference_info["PDF_COLOR"])
            cal_pt = float(reference_info["EFFECTIVE_PT"])
            cal_h = int(reference_pixel["H_INK_PX"])
            cal_area = int(reference_pixel["INK_AREA_PX"])
            paths = {
                "RAW_1X": reference_pixel["RAW_1X"],
                "TARGET_OVERLAY_1X": reference_pixel["TARGET_OVERLAY_1X"],
                "MASK_ONLY_1X": reference_pixel["MASK_ONLY_1X"],
                "TRIAD_8X": reference_pixel["TRIAD_8X"],
            }
            source_page = "R95 physical page 17 direct 300dpi"
        else:
            ref = external[target]
            cal_id = ref["id"]
            cal_origin = ref["origin"]
            cal_font = ref["span"]["font"]
            cal_color = int(ref["span"]["color"])
            cal_pt = float(ref["span"]["size"])
            cal_h = int(ref["metrics"]["h_ink_px"])
            cal_area = int(ref["metrics"]["ink_area_px"])
            paths = ref["paths"]
            source_page = ref["page"]
        h_ratio = cal_h / int(target_pixel["H_INK_PX"])
        area_ratio = cal_area / int(target_pixel["INK_AREA_PX"])
        metadata_equal = (
            target_info["CHAR"] == ("：" if target == "F020_G053" else "." if target == "F020_G068" else target_info["CHAR"])
            and target_info["PDF_FONT"] == cal_font
            and int(target_info["PDF_COLOR"]) == cal_color
            and abs(float(target_info["EFFECTIVE_PT"]) - cal_pt) <= 0.25
        )
        decision = "PASS" if metadata_equal and 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 else "FAIL"
        rows.append(
            {
                "TARGET_ELEMENT_ID": target,
                "CHAR": target_info["CHAR"],
                "CODEPOINT": target_info["CODEPOINT"],
                "TARGET_FONT": target_info["PDF_FONT"],
                "TARGET_EFFECTIVE_PT": round(float(target_info["EFFECTIVE_PT"]), 4),
                "TARGET_COLOR": target_info["PDF_COLOR"],
                "TARGET_H_INK_PX": target_pixel["H_INK_PX"],
                "TARGET_AREA_PX": target_pixel["INK_AREA_PX"],
                "CALIBRATOR_ID": cal_id,
                "CALIBRATOR_ORIGIN": cal_origin,
                "CALIBRATOR_SOURCE": source_page,
                "CALIBRATOR_FONT": cal_font,
                "CALIBRATOR_EFFECTIVE_PT": round(cal_pt, 4),
                "CALIBRATOR_COLOR": cal_color,
                "CALIBRATOR_H_INK_PX": cal_h,
                "CALIBRATOR_AREA_PX": cal_area,
                "FONT_WEIGHT_MATCH": target_info["PDF_FONT"] == cal_font,
                "COLOR_MATCH": int(target_info["PDF_COLOR"]) == cal_color,
                "EFFECTIVE_PT_ABS_DELTA": round(abs(float(target_info["EFFECTIVE_PT"]) - cal_pt), 4),
                "HINK_RATIO": round(h_ratio, 4),
                "AREA_RATIO": round(area_ratio, 4),
                "HINK_RATIO_PASS": 0.92 <= h_ratio <= 1.08,
                "AREA_RATIO_PASS": 0.92 <= area_ratio <= 1.08,
                "RESULT": decision,
                "CALIBRATOR_RAW_1X": paths["RAW_1X"],
                "CALIBRATOR_TARGET_OVERLAY_1X": paths["TARGET_OVERLAY_1X"],
                "CALIBRATOR_MASK_ONLY_1X": paths["MASK_ONLY_1X"],
                "CALIBRATOR_TRIAD_8X": paths["TRIAD_8X"],
            }
        )

    fields = list(rows[0])
    write_csv(CAL / "low_profile_punctuation_calibration.csv", rows, fields)
    with (CAL / "low_profile_punctuation_calibration.json").open("w", encoding="utf-8") as handle:
        json.dump({"rows": rows, "result": "PASS" if all(row["RESULT"] == "PASS" for row in rows) else "FAIL"}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"calibration_rows": len(rows), "result": [r["RESULT"] for r in rows]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
