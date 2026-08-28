"""Independent, same-glyph low-profile calibration for FIG-P602-01 R5.

Only the frozen R96 page and the R5 evidence-only calibration PDF are read.
All masks are native 300 dpi masks with a 20/255 contrast threshold; 8x-nearest
files are made solely for human review.  The calibration never borrows the
height of a surrounding CJK or mathematical parent glyph.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
WORK_ROOT = WORKSPACE / "v2.7.0" / "_work"
OUT = Path(__file__).resolve().parent
CAL_DIR = OUT / "calibration"
CANDIDATE_PNG = OUT / "official_R96_physical_651_full_page_300dpi.png"
CAL_PDF = CAL_DIR / "build" / "low_profile_calibration.pdf"
CAL_PNG = CAL_DIR / "low_profile_calibration_300dpi.png"
GLYPH_MAP = OUT / "glyph_map.csv"
FONT_AUDIT = OUT / "after_font_audit.csv"
DPI = 300
SCALE = DPI / 72.0

# The first four are the required low-profile contexts; the final two make the
# matching record explicit for the other punctuation contexts used by the page.
SPECS = [
    ("LP01_EN_DASH", "GLYPH-151", "–", "caption: Metropolis--Hastings"),
    ("LP02_CJK_DUNHAO", "GLYPH-167", "、", "caption CJK punctuation"),
    ("LP03_CJK_COLON", "GLYPH-132", "：", "edge label: 自环：保留 x"),
    ("LP04_CJK_FULL_STOP", "GLYPH-175", "。", "caption terminal punctuation"),
    ("LP05_MATH_COMMA", "GLYPH-013", ",", "proposal math q(x,·)"),
    ("LP06_CAPTION_DOT", "GLYPH-139", ".", "caption number 32.5"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def font_key(name: str) -> str:
    """Remove a PDF subset prefix but retain exact font family/weight."""
    return name.split("+", 1)[-1]


def rect_px(values: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = values
    return (
        max(0, int(math.floor(x0 * SCALE))),
        max(0, int(math.floor(y0 * SCALE))),
        min(width, int(math.ceil(x1 * SCALE))),
        min(height, int(math.ceil(y1 * SCALE))),
    )


def native_mask(image: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[np.ndarray, int, int, tuple[float, float, float]]:
    x0, y0, x1, y1 = bbox
    pad = 2
    ax0, ay0 = max(0, x0 - pad), max(0, y0 - pad)
    ax1, ay1 = min(image.shape[1], x1 + pad), min(image.shape[0], y1 + pad)
    region = image[ay0:ay1, ax0:ax1].astype(np.int16)
    background = np.percentile(region.reshape(-1, 3), 97, axis=0)
    contrast = np.max(np.abs(region - background), axis=2)
    mask = contrast[y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0] >= 20
    ys, _ = np.where(mask)
    h = int(ys.max() - ys.min() + 1) if len(ys) else 0
    return mask, int(mask.sum()), h, tuple(float(v) for v in background)


def crop_triplet(image: np.ndarray, bbox: tuple[int, int, int, int], mask: np.ndarray) -> tuple[Image.Image, Image.Image, Image.Image]:
    x0, y0, x1, y1 = bbox
    pad = 3
    cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
    cx1, cy1 = min(image.shape[1], x1 + pad), min(image.shape[0], y1 + pad)
    raw = image[cy0:cy1, cx0:cx1]
    local = np.zeros(raw.shape[:2], dtype=bool)
    local[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0] = mask
    overlay = raw.copy()
    overlay[local] = (235, 64, 52)
    white = Image.fromarray((local * 255).astype(np.uint8), "L").convert("RGB")
    return Image.fromarray(raw), Image.fromarray(overlay), white


def comparison_sheet(path: Path, title: str, candidate: tuple[Image.Image, Image.Image, Image.Image], calibration: tuple[Image.Image, Image.Image, Image.Image], candidate_note: str, calibration_note: str) -> None:
    font = ImageFont.load_default()
    max_w = max(item.width for item in (*candidate, *calibration))
    max_h = max(item.height for item in (*candidate, *calibration))
    cell_w = (max_w + 4) * 8
    cell_h = (max_h + 4) * 8 + 32
    canvas = Image.new("RGB", (cell_w * 3, cell_h * 2 + 22), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((2, 2), title, fill="black", font=font)
    for row, (items, note) in enumerate(((candidate, candidate_note), (calibration, calibration_note))):
        by = 18 + row * cell_h
        draw.text((2, by), note, fill="black", font=font)
        for col, item in enumerate(items):
            enlarged = item.resize((item.width * 8, item.height * 8), Image.Resampling.NEAREST)
            canvas.paste(enlarged, (col * cell_w + 2, by + 13))
    canvas.save(path)


def calibration_chars(doc: fitz.Document) -> list[dict[str, object]]:
    page = doc[0]
    chars: list[dict[str, object]] = []
    for block in page.get_text("rawdict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span["chars"]:
                    value = char["c"]
                    if value.strip():
                        chars.append({
                            "char": value,
                            "font": str(span["font"]),
                            "size": float(span["size"]),
                            "color": int(span["color"]),
                            "bbox_pt": tuple(float(v) for v in char["bbox"]),
                        })
    return chars


def main() -> None:
    for required in (CANDIDATE_PNG, CAL_PDF, CAL_PNG, GLYPH_MAP, FONT_AUDIT):
        if not required.exists():
            raise RuntimeError(f"Missing R5 calibration input: {required}")

    candidate_img = np.asarray(Image.open(CANDIDATE_PNG).convert("RGB"))
    calibration_img = np.asarray(Image.open(CAL_PNG).convert("RGB"))
    glyphs = {record["GLYPH_ID"]: record for record in rows(GLYPH_MAP)}
    fonts = {record["ELEMENT_ID"]: record for record in rows(FONT_AUDIT)}
    doc = fitz.open(CAL_PDF)
    if doc.page_count != 1:
        raise RuntimeError(f"Calibration must be exactly one page, got {doc.page_count}")
    cal_chars = calibration_chars(doc)
    records: list[dict[str, object]] = []

    for spec_id, glyph_id, codepoint_char, role in SPECS:
        target = glyphs[glyph_id]
        target_font = fonts[glyph_id]
        if target["CHAR"] != codepoint_char:
            raise RuntimeError(f"{glyph_id} expected {codepoint_char!r}, got {target['CHAR']!r}")
        candidates = [item for item in cal_chars if item["char"] == codepoint_char]
        exact_candidates = [item for item in candidates if font_key(str(item["font"])) == font_key(target_font["PDF_FONT"]) and abs(float(item["size"]) - float(target_font["PDF_FONT_SIZE_PT"])) <= 0.01 and int(item["color"]) == int(target_font["COLOR_INT"])]
        if len(exact_candidates) != 1:
            raise RuntimeError(f"{spec_id}: expected exactly one same-context calibration glyph; found {len(exact_candidates)} of {len(candidates)} matching candidates")
        calibration = exact_candidates[0]

        target_bbox = tuple(int(target[field]) for field in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        cal_bbox = rect_px(calibration["bbox_pt"], calibration_img.shape[1], calibration_img.shape[0])
        target_mask, target_area, target_h, target_bg = native_mask(candidate_img, target_bbox)
        cal_mask, cal_area, cal_h, cal_bg = native_mask(calibration_img, cal_bbox)
        target_area_map = int(target["RAW_MASK_PIXELS"])
        target_h_map = int(target["H_INK_PX"])
        candidate_reproducible = target_area == target_area_map and target_h == target_h_map
        font_match = font_key(str(calibration["font"])) == font_key(target_font["PDF_FONT"])
        size_match = abs(float(calibration["size"]) - float(target_font["PDF_FONT_SIZE_PT"])) <= 0.01
        color_match = int(calibration["color"]) == int(target_font["COLOR_INT"])
        area_ratio = target_area / cal_area if cal_area else float("inf")
        h_delta = abs(target_h - cal_h)
        metric_match = 0.92 <= area_ratio <= 1.08 and h_delta <= 1
        decision = "PASS" if (candidate_reproducible and font_match and size_match and color_match and metric_match) else "FAIL"
        sheet = CAL_DIR / f"{spec_id}_candidate_vs_calibration_8x_nearest.png"
        comparison_sheet(
            sheet,
            f"{spec_id} {codepoint_char} U+{ord(codepoint_char):04X}",
            crop_triplet(candidate_img, target_bbox, target_mask),
            crop_triplet(calibration_img, cal_bbox, cal_mask),
            f"candidate O/T/M: H={target_h}px A={target_area}px", 
            f"calibration O/T/M: H={cal_h}px A={cal_area}px",
        )
        records.append({
            "CALIBRATION_ID": spec_id,
            "ROLE": role,
            "TARGET_GLYPH_ID": glyph_id,
            "CODEPOINT": f"U+{ord(codepoint_char):04X}",
            "CHAR": codepoint_char,
            "TARGET_FONT": target_font["PDF_FONT"],
            "CALIBRATION_FONT": calibration["font"],
            "FONT_MATCH": font_match,
            "TARGET_EFFECTIVE_PT": target_font["PDF_FONT_SIZE_PT"],
            "CALIBRATION_EFFECTIVE_PT": round(float(calibration["size"]), 3),
            "SIZE_MATCH": size_match,
            "TARGET_COLOR_INT": target_font["COLOR_INT"],
            "CALIBRATION_COLOR_INT": calibration["color"],
            "COLOR_MATCH": color_match,
            "TARGET_H_PX": target_h,
            "CALIBRATION_H_PX": cal_h,
            "H_DELTA_PX": h_delta,
            "TARGET_AREA_PX": target_area,
            "CALIBRATION_AREA_PX": cal_area,
            "AREA_RATIO_TARGET_TO_CAL": round(area_ratio, 4),
            "TARGET_MAP_REPRODUCIBLE": candidate_reproducible,
            "METRIC_MATCH": metric_match,
            "THRESHOLD": "raw 300dpi contrast>=20; area ratio [0.92,1.08]; |H delta|<=1px",
            "COMPARISON_SHEET": str(sheet.relative_to(OUT)).replace("\\", "/"),
            "DECISION": decision,
            "NOTE": "Same codepoint/font/weight/color/effective size; no parent-height substitution.",
        })

    write_csv(CAL_DIR / "low_profile_calibration.csv", records)
    manifest = {
        "method": "same-codepoint, same font/weight/color/effective-size calibration on native 300 dpi raster; contrast >=20; 8x nearest evidence only",
        "candidate_pdf_render": str(CANDIDATE_PNG),
        "calibration_tex": str(CAL_DIR / "low_profile_calibration.tex"),
        "calibration_pdf": str(CAL_PDF),
        "calibration_pdf_sha256": sha256(CAL_PDF),
        "calibration_png": str(CAL_PNG),
        "calibration_png_sha256": sha256(CAL_PNG),
        "records": len(records),
        "passed": sum(row["DECISION"] == "PASS" for row in records),
        "failed": sum(row["DECISION"] == "FAIL" for row in records),
    }
    (CAL_DIR / "low_profile_calibration_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (CAL_DIR / "low_profile_calibration_report.md").open("w", encoding="utf-8") as stream:
        stream.write("# Independent low-profile calibration — R5 SA1\n\n")
        stream.write("All comparisons use the same codepoint, font/weight, color and PDF-measured effective size; native 300dpi raw masks are measured at contrast >=20.  The 8x-nearest comparison sheets are manual evidence only.\n\n")
        stream.write(f"- contexts: {len(records)}; pass: {manifest['passed']}; fail: {manifest['failed']}.\n")
        stream.write(f"- calibration PDF SHA-256: `{manifest['calibration_pdf_sha256']}`.\n")
        stream.write(f"- calibration raster SHA-256: `{manifest['calibration_png_sha256']}`.\n")
        for row in records:
            stream.write(f"- {row['CALIBRATION_ID']} / {row['TARGET_GLYPH_ID']} / {row['CODEPOINT']}: `{row['DECISION']}`; H {row['TARGET_H_PX']}→{row['CALIBRATION_H_PX']} px, area ratio {row['AREA_RATIO_TARGET_TO_CAL']}.\n")


if __name__ == "__main__":
    main()
