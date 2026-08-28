from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
ROWS = [
    ("G0005", "E001", "U+FF1A", "：", 1, "NotoSerifSC-ExtraLight", "normal", (31, 78, 121), 10.2655),
    ("G0014", "E002", "U+FF1A", "：", 2, "NotoSerifSC-ExtraLight", "normal", (15, 118, 110), 10.2655),
    ("G0050", "E010", "U+002E", ".", 3, "STIXTwoText-Bold", "bold", (31, 35, 40), 9.9626),
    ("G0068", "E011", "U+FF0C", "，", 4, "NotoSerifSC-ExtraLight", "normal", (31, 35, 40), 9.9626),
    ("G0080", "E011", "U+3002", "。", 5, "NotoSerifSC-ExtraLight", "normal", (31, 35, 40), 9.9626),
]


def bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if not len(xs):
        return (0, 0, 0, 0)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def crop_assets(image: Image.Image, mask: np.ndarray, stem: str) -> tuple[int, int, tuple[int, int, int, int]]:
    mask_bbox = bbox(mask)
    x0, y0, x1, y1 = mask_bbox
    if x1 <= x0:
        Image.new("RGB", (1, 1), "white").save(ROOT / f"{stem}_raw_1x.png")
        Image.new("L", (1, 1), 255).save(ROOT / f"{stem}_raw_mask_1x.png")
        return 0, 0, (0, 0, 0, 0)
    pad = 4
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(image.width, x1 + pad), min(image.height, y1 + pad)
    raw = image.crop((x0, y0, x1, y1)).convert("RGB")
    local = mask[y0:y1, x0:x1]
    raw.save(ROOT / f"{stem}_raw_1x.png")
    mask_img = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), "L")
    mask_img.save(ROOT / f"{stem}_raw_mask_1x.png")
    for suffix, asset in (("raw", raw), ("raw_mask", mask_img)):
        asset.resize((asset.width * 8, asset.height * 8), Image.Resampling.NEAREST).save(ROOT / f"{stem}_{suffix}_8x_nearest.png")
    return int(local.sum()), int(local.any(axis=1).sum()), mask_bbox


def main() -> None:
    report = []
    for glyph_id, element_id, codepoint, char, page, font, weight, color, effective_pt in ROWS:
        full = Image.open(ROOT / f"calibration_page-{page}.png").convert("RGB")
        arr = np.asarray(full, dtype=np.int16)
        # One-glyph calibration pages are white except for the desired glyph.
        # The same 20/255 local-background foreground definition is used.
        mask = np.max(255 - arr, axis=2) >= 20
        cal_area, _, cal_crop = crop_assets(full, mask, f"{glyph_id}_calibration")
        cal_h = cal_crop[3] - cal_crop[1]
        target = np.asarray(Image.open(EVIDENCE / "glyph_masks" / f"{glyph_id}_mask_only_1x.png").convert("L")) == 0
        target_area = int(target.sum())
        target_box = bbox(target)
        target_h = target_box[3] - target_box[1]
        h_ratio = cal_h / target_h if target_h else 0.0
        area_ratio = cal_area / target_area if target_area else 0.0
        passed = 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 and effective_pt >= 9.5 and cal_area > 0
        report.append({
            "GLYPH_ID": glyph_id, "ELEMENT_ID": element_id, "CODEPOINT": codepoint, "CHAR": char,
            "PDF_FONT": font, "WEIGHT": weight, "TARGET_RGB": "/".join(map(str, color)), "TARGET_EFFECTIVE_PT": f"{effective_pt:.4f}",
            "CALIBRATION_SOURCE": "low_profile_calibration/calibration_source.tex", "CALIBRATION_PDF_PAGE": page,
            "CALIBRATION_FULL_NATIVE_300DPI": f"low_profile_calibration/calibration_page-{page}.png",
            "CALIBRATION_RAW_1X": f"low_profile_calibration/{glyph_id}_calibration_raw_1x.png",
            "CALIBRATION_MASK_1X": f"low_profile_calibration/{glyph_id}_calibration_raw_mask_1x.png",
            "CALIBRATION_RAW_8X": f"low_profile_calibration/{glyph_id}_calibration_raw_8x_nearest.png",
            "CALIBRATION_MASK_8X": f"low_profile_calibration/{glyph_id}_calibration_raw_mask_8x_nearest.png",
            "TARGET_H_INK_PX": target_h, "CALIBRATION_H_INK_PX": cal_h, "H_INK_RATIO": f"{h_ratio:.4f}",
            "TARGET_INK_AREA_PX": target_area, "CALIBRATION_INK_AREA_PX": cal_area, "INK_AREA_RATIO": f"{area_ratio:.4f}",
            "CALIBRATION_CROP_BBOX_PX": "/".join(map(str, cal_crop)), "LOW_PROFILE_TOTAL_GATE_PASS": str(passed).lower(),
            "MACHINE_REASON": "same-codepoint/font/weight/colour/effective-size native-300dpi reference; ratios evaluated against [0.92,1.08]",
        })
    fields = list(report[0])
    with (ROOT / "low_profile_calibration.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(report)
    summary = {"low_profile_count": len(report), "low_profile_total_gate_pass_count": sum(row["LOW_PROFILE_TOTAL_GATE_PASS"] == "true" for row in report), "low_profile_total_gate_fail_count": sum(row["LOW_PROFILE_TOTAL_GATE_PASS"] != "true" for row in report), "all_pass": all(row["LOW_PROFILE_TOTAL_GATE_PASS"] == "true" for row in report), "coordinate": "native 300dpi direct PDF render; 1x is sole counting coordinate"}
    (ROOT / "low_profile_machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
