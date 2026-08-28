from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P582-02\STRICT_R10_REQUAL_R115_SA1_20260824")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def strict_gate(row: dict[str, str]) -> tuple[str, int | None, bool, str]:
    char = row["CHAR"]
    old_class = row["SCRIPT_CLASS"]
    if char in {".", ",", "，", "；", "：", "、"}:
        return "LOW_PROFILE_PUNCTUATION", None, True, "requires independent same-codepoint/font/weight/effective-pt calibration"
    if char in {"一"} or old_class == "CJK_FULLHEIGHT":
        return "CJK_FULLHEIGHT", 30, False, "CJK full gate; low-stroke CJK is not script"
    if char in {"=", "≈"}:
        return "BASE_MATH_RELATION", 22, False, "base math operator/relation gate"
    if char in {"∑", "/"}:
        return "BASE_MATH_OPERATOR", 22, False, "base math operator gate"
    if old_class == "NATURAL_SCRIPT":
        return "LEGAL_NATURAL_SCRIPT", 15, False, "legal TeX script gate"
    if char.isdigit():
        return "DIGIT", 24, False, "digit gate"
    if char.isupper():
        return "LATIN_UPPER", 24, False, "Latin uppercase gate"
    if old_class == "LOWER_OR_GREEK":
        return "LATIN_LOWER_OR_GREEK", 17, False, "x-height/Greek lower gate"
    return old_class, 22, False, "default base-math/full-glyph gate"


def main() -> None:
    if (ROOT / "WRITE_STOPPED").exists():
        raise SystemExit("WRITE_STOPPED already exists; refusing to write")
    font_rows = read_csv(ROOT / "after_font_audit.csv")
    output: list[dict[str, str]] = []
    for row in font_rows:
        strict_class, threshold, needs_cal, basis = strict_gate(row)
        h = int(float(row["H_INK_PX"]))
        missing = int(float(row["MISSING_STROKE_PX"]))
        foreign = int(float(row["FOREIGN_PIXEL_PX"]))
        clip = int(float(row["CLIP_PIXEL_COUNT"]))
        raw_d = "PASS" if threshold is None or h >= threshold else "FAIL"
        e = "PASS" if missing == 0 and foreign == 0 and clip == 0 else "FAIL"
        calibration = "FAIL" if needs_cal else "NOT_APPLICABLE"
        font = row["EFFECTIVE_PT_RESULT"]
        physical = "PASS" if raw_d == "PASS" and e == "PASS" else "FAIL"
        overall = "PASS" if physical == "PASS" and calibration != "FAIL" and font == "PASS" else "FAIL"
        reasons: list[str] = []
        if raw_d == "FAIL":
            reasons.append(f"H_INK_PX={h} < strict threshold {threshold}")
        if e == "FAIL":
            reasons.append(f"mask quality missing={missing}; foreign={foreign}; clip={clip}")
        if calibration == "FAIL":
            reasons.append("CALIBRATION_CLOSURE_FAIL: no independent qualifying same-codepoint/font/weight/effective-pt raw calibration")
        if font == "FAIL":
            reasons.append(f"effective_pt={row['EFFECTIVE_PT']} < 9.5")
        output.append({
            "ELEMENT_ID": row["GLYPH_ID"], "PARENT_ID": row["PARENT_ID"], "PANEL_ID": row["PANEL_ID"],
            "ROLE": row["ROLE"], "CHAR": char if (char := row["CHAR"]) else "", "UNICODE": row["UNICODE"],
            "SOURCE_SCRIPT_CLASS": old if (old := row["SCRIPT_CLASS"]) else "", "STRICT_SCRIPT_CLASS": strict_class,
            "STRICT_THRESHOLD_PX": "" if threshold is None else str(threshold), "H_INK_PX": row["H_INK_PX"],
            "INK_AREA_PX": row["INK_AREA_PX"], "MISSING_STROKE_PX": row["MISSING_STROKE_PX"],
            "FOREIGN_PIXEL_PX": row["FOREIGN_PIXEL_PX"], "CLIP_PIXEL_COUNT": row["CLIP_PIXEL_COUNT"],
            "EFFECTIVE_PT": row["EFFECTIVE_PT"], "FONT_SIZE_RESULT": font,
            "D_RESULT": raw_d, "E_RESULT": e, "LOW_PROFILE_CALIBRATION_REQUIRED": "YES" if needs_cal else "NO",
            "LOW_PROFILE_CALIBRATION_RESULT": calibration, "PHYSICAL_RAW_PIXEL_RESULT": physical,
            "OVERALL_STRICT_RESULT": overall, "GATE_BASIS": basis, "REASON": "; ".join(reasons) if reasons else "all strict raw gates pass"
        })
    fields = list(output[0])
    write_csv(ROOT / "after_pixel_measurements.csv", output, fields)

    relation_rows = read_csv(ROOT / "relations" / "text_graphic_relations.csv")
    edge_rows = read_csv(ROOT / "relations" / "text_figure_edge_relations.csv")
    overlap_rows: list[dict[str, str]] = []
    for r in relation_rows:
        overlap_rows.append({
            "CHECK_SCOPE": r["RELATION_SCOPE"], "CHECK_ID": r["RELATION_ID"], "A_ID": r["A_ID"], "B_ID": r["B_ID"],
            "OVERLAP_PIXEL_COUNT": r["OVERLAP_PIXEL_COUNT"], "MIN_CLEARANCE_PX": r["MIN_CLEARANCE_PX"],
            "THRESHOLD_PX": r["THRESHOLD_PX"], "CLIP_PIXEL_COUNT": "0", "RESULT": r["RESULT"]
        })
    for index, r in enumerate(edge_rows, start=1):
        overlap_rows.append({
            "CHECK_SCOPE": r["RELATION_SCOPE"], "CHECK_ID": f"EDGE{index:03d}", "A_ID": r["PARENT_ID"], "B_ID": "FIGURE_CROP_EDGE",
            "OVERLAP_PIXEL_COUNT": "0", "MIN_CLEARANCE_PX": r["MIN_CLEARANCE_PX"],
            "THRESHOLD_PX": r["THRESHOLD_PX"], "CLIP_PIXEL_COUNT": r["CLIP_PIXEL_COUNT"], "RESULT": r["RESULT"]
        })
    write_csv(ROOT / "after_overlap_report.csv", overlap_rows, list(overlap_rows[0]))

    # The exact root-level figure crop is native 300dpi. Native bboxes are page coordinates.
    image = Image.open(ROOT / "figure_crop_300dpi.png").convert("RGB")
    draw = ImageDraw.Draw(image)
    x_offset, y_offset = 250, 2120
    for row in font_rows:
        x0, y0, x1, y1 = [int(v) for v in row["NATIVE_BBOX_PX"].split(",")]
        box = (x0 - x_offset, y0 - y_offset, x1 - x_offset, y1 - y_offset)
        draw.rectangle(box, outline=(220, 0, 0), width=1)
        draw.text((box[0], max(0, box[1] - 8)), row["GLYPH_ID"].replace("F582_", ""), fill=(220, 0, 0))
    image.save(ROOT / "after_text_measurement_overlay_300dpi.png")


if __name__ == "__main__":
    main()
