"""Revision-111 low-profile punctuation calibration for FIG-P582-01.

This is a measurement generator only.  The separate reviewer ledger is filled
after the generated 1x/8x packages are opened.  No low-profile character is
judged through a generic 15/22/30px threshold.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
CAL = ROOT / "low_profile_calibration"
OUT = CAL / "packages"
THRESHOLD = 235  # white 255 minus the required 20/255 local contrast
SCALE = 300 / 72
LOW_CHARS = {".", ",", "，", "；", ":", "：", "…"}

# Every candidate-PDF reference is a *different* same-codepoint glyph at the
# same effective size/style.  G0114/G0124 have no eligible in-figure peer and
# use the independent real-project \small calibration PDF below.
REF_GLYPH = {
    "G0002": "G0021", "G0021": "G0002", "G0024": "G0002", "G0038": "G0002",
    "G0043": "G0002", "G0059": "G0002", "G0062": "G0002",
    "G0012": "G0033", "G0033": "G0012", "G0045": "G0012", "G0054": "G0012",
    "G0082": "G0091", "G0091": "G0095", "G0095": "G0091", "G0099": "G0091", "G0103": "G0091",
    "G0093": "G0097", "G0097": "G0093", "G0101": "G0093",
    "G0114": "CAL_UFF1B", "G0124": "CAL_UFF0C",
}
CAL_PDF = CAL / "caption_cjk_punct_cal_r3.pdf"
CAL_SOURCE = CAL / "caption_cjk_punctuation_calibration.tex"


def mask_from_image(image: Image.Image) -> np.ndarray:
    return np.array(image.convert("L")) <= THRESHOLD


def metrics(mask: np.ndarray) -> tuple[int, int]:
    ys, _ = np.where(mask)
    return (0 if len(ys) == 0 else int(ys.max() - ys.min() + 1), int(mask.sum()))


def tight(mask: np.ndarray, pad: int = 3) -> np.ndarray:
    ys, xs = np.where(mask)
    if not len(ys):
        raise ValueError("empty calibration/target mask")
    y0, y1 = max(0, int(ys.min()) - pad), min(mask.shape[0], int(ys.max()) + pad + 1)
    x0, x1 = max(0, int(xs.min()) - pad), min(mask.shape[1], int(xs.max()) + pad + 1)
    return mask[y0:y1, x0:x1]


def to_png(mask: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def nearest(mask: np.ndarray, factor: int = 8) -> Image.Image:
    return Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").resize(
        (mask.shape[1] * factor, mask.shape[0] * factor), Image.Resampling.NEAREST
    )


def strip(a: np.ndarray, b: np.ndarray, label: str) -> Image.Image:
    h = max(a.shape[0], b.shape[0])
    w = a.shape[1] + 8 + b.shape[1]
    im = Image.new("L", (w, h + 12), 255)
    aa = Image.fromarray(np.where(a, 0, 255).astype(np.uint8), mode="L")
    bb = Image.fromarray(np.where(b, 0, 255).astype(np.uint8), mode="L")
    im.paste(aa, (0, 12)); im.paste(bb, (a.shape[1] + 8, 12))
    ImageDraw.Draw(im).text((0, 0), label, fill=0)
    return im


def raw_char_records(pdf: Path) -> tuple[dict[str, dict[str, object]], Image.Image]:
    doc = fitz.open(pdf)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    page_image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
    records: dict[str, dict[str, object]] = {}
    raw = page.get_text("rawdict")
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    c = char["c"]
                    if c not in {"；", "，"}:
                        continue
                    x0, y0, x1, y1 = char["bbox"]
                    # The crop stays on the native 300dpi raster.  It is not
                    # resized before thresholding or metric calculation.
                    px0 = max(0, math.floor(x0 * SCALE) - 4)
                    py0 = max(0, math.floor(y0 * SCALE) - 4)
                    px1 = min(page_image.width, math.ceil(x1 * SCALE) + 4)
                    py1 = min(page_image.height, math.ceil(y1 * SCALE) + 4)
                    raw_crop = page_image.crop((px0, py0, px1, py1))
                    m = mask_from_image(raw_crop)
                    records[c] = {
                        "mask": m,
                        "raw_crop": raw_crop,
                        "font": span.get("font", ""),
                        "size_pt": span.get("size", ""),
                        "bbox_pt": [x0, y0, x1, y1],
                        "crop_px": [px0, py0, px1, py1],
                    }
    if set(records) != {"；", "，"}:
        raise RuntimeError(f"calibration PDF missing expected CJK punctuation: {records.keys()}")
    return records, page_image


def make_contact_sheet(paths: list[Path], out: Path) -> None:
    images = [Image.open(p).convert("L") for p in paths]
    width = max(im.width for im in images)
    height = sum(im.height + 3 for im in images)
    sheet = Image.new("L", (width, height), 255)
    y = 0
    for im in images:
        sheet.paste(im, (0, y)); y += im.height + 3
    sheet.save(out)


def main() -> None:
    if not CAL_PDF.exists() or not CAL_SOURCE.exists():
        raise FileNotFoundError("independent project-font calibration source/PDF missing")
    OUT.mkdir(parents=True, exist_ok=True)
    records, full = raw_char_records(CAL_PDF)
    full.save(CAL / "caption_cjk_punct_cal_r3_native_300dpi.png")
    cal_refs: dict[str, dict[str, object]] = {}
    for c, key in [("；", "CAL_UFF1B"), ("，", "CAL_UFF0C")]:
        rec = records[c]
        raw_crop: Image.Image = rec["raw_crop"]  # type: ignore[assignment]
        raw_crop.save(CAL / f"{key}_source_raw_1x.png")
        m = tight(rec["mask"])  # type: ignore[arg-type]
        to_png(m, CAL / f"{key}_mask_only_1x.png")
        nearest(m).save(CAL / f"{key}_mask_only_8x_nearest.png")
        h, area = metrics(m)
        cal_refs[key] = {"mask": m, "h_ink_px": h, "ink_area_px": area, **{k: v for k, v in rec.items() if k not in {"mask", "raw_crop"}}}

    with (ROOT / "glyph_final_mask_manifest.csv").open(encoding="utf-8-sig", newline="") as fh:
        final = {r["GLYPH_ID"]: r for r in csv.DictReader(fh)}
    with (ROOT / "glyph_file_manifest.csv").open(encoding="utf-8-sig", newline="") as fh:
        glyphs = {r["GLYPH_ID"]: r for r in csv.DictReader(fh)}
    with (ROOT / "after_pixel_measurements.csv").open(encoding="utf-8-sig", newline="") as fh:
        old_rows = list(csv.DictReader(fh))

    targets = [r for r in old_rows if r["LEVEL"] == "GLYPH" and r["TEXT_SAMPLE"] in LOW_CHARS]
    ids = {r["GLYPH_ID"] for r in targets}
    if ids != set(REF_GLYPH):
        raise RuntimeError(f"unexpected low-profile target set: {sorted(ids)}")

    output_rows: list[dict[str, object]] = []
    manifests: list[dict[str, object]] = []
    one_x: list[Path] = []
    eight_x: list[Path] = []
    by_id = {r["GLYPH_ID"]: r for r in old_rows if r["LEVEL"] == "GLYPH"}
    for row in sorted(targets, key=lambda r: r["GLYPH_ID"]):
        gid = row["GLYPH_ID"]
        target_mask = tight(mask_from_image(Image.open(ROOT / final[gid]["FINAL_VISIBLE_MASK"])))
        th, ta = metrics(target_mask)
        reference_id = REF_GLYPH[gid]
        if reference_id.startswith("CAL_"):
            ref_mask = cal_refs[reference_id]["mask"]  # type: ignore[assignment]
            rh, ra = int(cal_refs[reference_id]["h_ink_px"]), int(cal_refs[reference_id]["ink_area_px"])
            ref_kind = "INDEPENDENT_PROJECT_TEX_SMALL"
            ref_detail = str(CAL_SOURCE.relative_to(ROOT)) + "; " + str(CAL_PDF.relative_to(ROOT))
            ref_font = str(cal_refs[reference_id]["font"])
            ref_pt = float(cal_refs[reference_id]["size_pt"])
        else:
            ref_mask = tight(mask_from_image(Image.open(ROOT / final[reference_id]["FINAL_VISIBLE_MASK"])))
            rh, ra = metrics(ref_mask)
            ref_kind = "CANDIDATE_PDF_SAME_CODEPOINT_REFERENCE"
            ref_detail = reference_id
            ref_font = "same actual candidate PDF text run / source font command"
            ref_pt = float(by_id[reference_id]["EFFECTIVE_PT"])
        if glyphs[gid]["CHAR"] != glyphs.get(reference_id, glyphs[gid])["CHAR"] and not reference_id.startswith("CAL_"):
            raise RuntimeError(f"codepoint mismatch {gid} -> {reference_id}")
        tr = th / rh if rh else float("inf")
        ar = ta / ra if ra else float("inf")
        calibration_ok = 0.92 <= tr <= 1.08 and 0.92 <= ar <= 1.08
        font_ok = float(row["EFFECTIVE_PT"]) >= 9.5
        package = OUT / gid
        package.mkdir(exist_ok=True)
        to_png(ref_mask, package / "source_reference_mask_1x.png")
        to_png(target_mask, package / "target_final_visible_mask_1x.png")
        nearest(ref_mask).save(package / "source_reference_mask_8x_nearest.png")
        nearest(target_mask).save(package / "target_final_visible_mask_8x_nearest.png")
        comp = strip(ref_mask, target_mask, f"source|target {gid}")
        comp.save(package / "comparison_strip_1x.png")
        comp.resize((comp.width * 8, comp.height * 8), Image.Resampling.NEAREST).save(package / "comparison_strip_8x_nearest.png")
        one_x.append(package / "comparison_strip_1x.png")
        eight_x.append(package / "comparison_strip_8x_nearest.png")
        package_manifest = {
            "target_glyph_id": gid, "char": glyphs[gid]["CHAR"], "reference_id": reference_id,
            "reference_kind": ref_kind, "reference_detail": ref_detail,
            "coordinate": "native 300dpi 1:1; 8x nearest only for observation",
            "target_h_ink_px": th, "reference_h_ink_px": rh, "h_ink_ratio": round(tr, 4),
            "target_ink_area_px": ta, "reference_ink_area_px": ra, "ink_area_ratio": round(ar, 4),
            "calibration_pass": calibration_ok,
        }
        (package / "package_manifest.json").write_text(json.dumps(package_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        data = {
            "GLYPH_ID": gid, "ELEMENT_ID": row["ELEMENT_ID"], "CHAR": glyphs[gid]["CHAR"],
            "PANEL_ID": row["PANEL_ID"], "ROLE": row["ROLE"], "EFFECTIVE_PT": row["EFFECTIVE_PT"],
            "REFERENCE_ID": reference_id, "REFERENCE_KIND": ref_kind, "REFERENCE_DETAIL": ref_detail,
            "REFERENCE_FONT": ref_font, "REFERENCE_EFFECTIVE_PT": ref_pt,
            "TARGET_H_INK_PX": th, "REFERENCE_H_INK_PX": rh, "H_INK_RATIO": round(tr, 4),
            "TARGET_INK_AREA_PX": ta, "REFERENCE_INK_AREA_PX": ra, "INK_AREA_RATIO": round(ar, 4),
            "H_INK_AND_AREA_RANGE": "[0.92,1.08]", "CALIBRATION_PASS": str(calibration_ok).lower(),
            "SOURCE_EFFECTIVE_PT_PASS": str(font_ok).lower(),
            "LOW_PROFILE_TOTAL_GATE_PASS": str(calibration_ok and font_ok).lower(),
            "PACKAGE": str(package.relative_to(ROOT)).replace("\\", "/"),
        }
        output_rows.append(data); manifests.append(data)

    make_contact_sheet(one_x, CAL / "low_profile_comparison_contact_sheet_1x.png")
    make_contact_sheet(eight_x, CAL / "low_profile_comparison_contact_sheet_8x_nearest.png")
    fields = list(output_rows[0])
    with (ROOT / "low_profile_punctuation_calibration.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(output_rows)
    (CAL / "low_profile_calibration_manifest.json").write_text(json.dumps({
        "revision": "111", "source_tex": str(CAL_SOURCE.relative_to(ROOT)), "source_pdf": str(CAL_PDF.relative_to(ROOT)),
        "threshold": "foreground contrast >=20/255", "target_count": len(output_rows), "targets": manifests,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    calibration = {r["GLYPH_ID"]: r for r in output_rows}
    new_fields = list(old_rows[0]) + [
        "LOW_PROFILE_PUNCTUATION", "LOW_PROFILE_CALIBRATION_ID", "LOW_PROFILE_H_INK_RATIO",
        "LOW_PROFILE_INK_AREA_RATIO", "LOW_PROFILE_CALIBRATION_PASS", "LOW_PROFILE_TOTAL_GATE_PASS",
    ]
    updated: list[dict[str, str]] = []
    for r in old_rows:
        for field in new_fields:
            r.setdefault(field, "")
        if r["GLYPH_ID"] in calibration:
            c = calibration[r["GLYPH_ID"]]
            # Preserve the source font result; PIXEL_PASS now means the
            # revision-111 calibrated raw-mask comparison rather than a fake
            # generic-height threshold.  Overall PASS_FAIL still requires both.
            r["H_INK_THRESHOLD_PX"] = "LOW_PROFILE_CALIBRATED_H_INK_AND_AREA_[0.92,1.08]"
            r["CLASS_MEDIAN_PX"] = c["REFERENCE_H_INK_PX"]
            r["RATIO_TO_CLASS_MEDIAN"] = c["H_INK_RATIO"]
            r["PIXEL_PASS"] = c["CALIBRATION_PASS"]
            r["PASS_FAIL"] = "PASS" if r["FONT_PASS"] == "true" and c["CALIBRATION_PASS"] == "true" else "FAIL"
            r["REASON"] = "LOW_PROFILE_PUNCTUATION calibrated against same-codepoint/font/pt native-300dpi reference; see low_profile_punctuation_calibration.csv"
            r["LOW_PROFILE_PUNCTUATION"] = "true"
            r["LOW_PROFILE_CALIBRATION_ID"] = c["REFERENCE_ID"]
            r["LOW_PROFILE_H_INK_RATIO"] = c["H_INK_RATIO"]
            r["LOW_PROFILE_INK_AREA_RATIO"] = c["INK_AREA_RATIO"]
            r["LOW_PROFILE_CALIBRATION_PASS"] = c["CALIBRATION_PASS"]
            r["LOW_PROFILE_TOTAL_GATE_PASS"] = c["LOW_PROFILE_TOTAL_GATE_PASS"]
        updated.append(r)
    with (ROOT / "after_pixel_measurements.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=new_fields, extrasaction="ignore"); w.writeheader(); w.writerows(updated)

    summary = {
        "revision": "111", "low_profile_target_count": len(output_rows),
        "calibration_fail_count": sum(r["CALIBRATION_PASS"] == "false" for r in output_rows),
        "font_floor_fail_count": sum(r["SOURCE_EFFECTIVE_PT_PASS"] == "false" for r in output_rows),
        "total_low_profile_gate_fail_count": sum(r["LOW_PROFILE_TOTAL_GATE_PASS"] == "false" for r in output_rows),
        "all_packages_have_1x_and_8x": all((OUT / r["GLYPH_ID"] / "comparison_strip_1x.png").exists() and (OUT / r["GLYPH_ID"] / "comparison_strip_8x_nearest.png").exists() for r in output_rows),
    }
    (CAL / "low_profile_calibration_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
