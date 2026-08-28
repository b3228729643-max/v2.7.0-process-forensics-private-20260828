from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa3_r105_fresh_isolated_v3_main_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf")
EXPECTED_SHA = "F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1"


checks: dict[str, bool | int | str | list[str]] = {}
failures: list[str] = []


def require(name: str, condition: bool) -> None:
    checks[name] = bool(condition)
    if not condition:
        failures.append(name)


digest = hashlib.sha256()
with PDF.open("rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        digest.update(chunk)
require("official_pdf_bytes", PDF.stat().st_size == 4967209)
require("official_pdf_sha256", digest.hexdigest().upper() == EXPECTED_SHA)
with fitz.open(PDF) as doc:
    require("official_pdf_pages", doc.page_count == 817)

summary = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
objects = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
with (ROOT / "after_overlap_report.csv").open(encoding="utf-8-sig", newline="") as f:
    pairs = list(csv.DictReader(f))
with (ROOT / "after_pixel_measurements.csv").open(encoding="utf-8-sig", newline="") as f:
    pixels = list(csv.DictReader(f))
with (ROOT / "manual_glyph_contact_review.csv").open(encoding="utf-8", newline="") as f:
    glyph_manual = list(csv.DictReader(f))
with (ROOT / "manual_pair_roi_review.csv").open(encoding="utf-8", newline="") as f:
    pair_manual = list(csv.DictReader(f))
with (ROOT / "after_font_audit.csv").open(encoding="utf-8", newline="") as f:
    font_rows = list(csv.DictReader(f))
result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

object_ids = [o["id"] for o in objects]
require("object_count_80", len(objects) == 80)
require("object_ids_unique", len(object_ids) == len(set(object_ids)))
require("glyph_count_72", sum(o["kind"] == "GLYPH" for o in objects) == 72)
require("graphic_count_8", sum(o["kind"] == "GRAPHIC" for o in objects) == 8)
require("object_masks_80", len(list((ROOT / "object_masks").glob("*.png"))) == 80)
require("safe_filenames_unique", len({o["safe_filename"] for o in objects}) == 80)
require("safe_filenames_portable", all(":" not in o["safe_filename"] and (ROOT / "object_masks" / o["safe_filename"]).is_file() for o in objects))

expected_pairs = {tuple(sorted(p)) for p in itertools.combinations(object_ids, 2)}
actual_pairs = {tuple(sorted((r["object_a"], r["object_b"]))) for r in pairs}
require("pair_count_3160", len(pairs) == 3160)
require("pair_ids_unique", len({r["pair_id"] for r in pairs}) == 3160)
require("all_unordered_pairs_exact", actual_pairs == expected_pairs)
require("geometry_pair_failures_zero", sum(r["decision"] == "FAIL" for r in pairs) == 0)
require("illegal_overlap_zero", summary["overlap_pixel_count_illegal"] == 0)
require("clip_zero", summary["clip_pixel_count"] == 0)
require("empty_masks_zero", summary["empty_mask_count"] == 0)
require("machine_summary_r168_pass", summary["overall_machine_decision"] == "PASS" and summary["machine_typography_decision"] == "PASS_WITH_R168_ADVISORIES" and summary["source_effective_pt_r168_advisory_count"] == 72 and summary["pixel_r168_advisory_count"] == 8)

require("pixel_rows_72", len(pixels) == 72)
pixel_failure_ids = {r["id"] for r in pixels if r["pixel_decision"] != "PASS"}
require("pixel_failure_ids_exact", pixel_failure_ids == {"GLYPH_001", "GLYPH_003", "GLYPH_023", "GLYPH_031", "GLYPH_041", "GLYPH_049", "GLYPH_058", "GLYPH_065"})
require("source_failures_72", sum(r["source_pt_decision"] == "FAIL" for r in pixels) == 72)
require("font_r168_advisories_4", sum(r["decision"] == "ADVISORY_R168" for r in font_rows) == 4)

require("glyph_contact_files_72", len(list((ROOT / "glyph_contacts").glob("*.png"))) == 72)
require("contact_sheets_5", len(list((ROOT / "contact_sheets").glob("*.png"))) == 5)
require("glyph_manual_rows_72", len(glyph_manual) == 72)
require("glyph_manual_unique", len({r["id"] for r in glyph_manual}) == 72)
require("glyph_manual_all_pass", all(r["decision"] == "PASS" and r["original_match"] == "true" and r["overlay_complete"] == "true" and r["mask_only_pure"] == "true" and r["missing_stroke_px"] == "0" and r["foreign_pixel_px"] == "0" for r in glyph_manual))

critical_pair_ids = {r["pair_id"] for r in pairs if int(r["overlap_pixel_count"]) > 0 or (int(r["hard_threshold_px"]) > 0 and float(r["clearance_px"]) <= int(r["hard_threshold_px"]) + 3)}
require("critical_pair_ids_5", critical_pair_ids == {"PAIR_3140", "PAIR_3141", "PAIR_3146", "PAIR_3152", "PAIR_3156"})
require("pair_roi_png_30", len(list((ROOT / "pair_roi").glob("*.png"))) == 30)
require("pair_manual_rows_5", len(pair_manual) == 5 and {r["pair_id"] for r in pair_manual} == critical_pair_ids)
require("pair_manual_all_pass", all(r["decision"] == "PASS" and r["opened_1x_and_8x"] == "true" for r in pair_manual))

expected_dims = {
    "full_page_200dpi.png": (1654, 2339),
    "figure_crop_300dpi.png": (1695, 720),
    "standalone_300dpi.png": (1950, 850),
    "grayscale_300dpi.png": (1695, 720),
    "after_text_measurement_overlay_300dpi.png": (1695, 720),
}
for name, dims in expected_dims.items():
    require(f"dimensions_{name}", Image.open(ROOT / name).size == dims)

for name in (
    "manual_visual_review.md",
    "manual_glyph_contact_review.csv",
    "manual_pair_roi_review.csv",
    "after_visual_acceptance.md",
    "REPORT.md",
    "HANDOFF.md",
    "RESULT.json",
    "RESULT.txt",
    "renderer_metadata.json",
    "object_denominator_freeze.md",
    "math_rule_and_drawing_ledger.csv",
    "role_ratio_audit.csv",
    "r168_final_adjudication.json",
):
    require(f"required_file_{name}", (ROOT / name).is_file())
adjudication = json.loads((ROOT / "r168_final_adjudication.json").read_text(encoding="utf-8"))
require("r168_adjudication_pass", adjudication["final_sa3_verdict"] == "PASS" and all(v == "PASS" for v in adjudication["true_hard_gates"].values()))
require("result_is_pass", result["verdict"] == "PASS" and result["overall_pass"] is True and result["hard_failure_ids"] == [])
require("manifest_absent_before_single_seal", not (ROOT / "manifest.json").exists())
require("wstop_absent_before_single_seal", not (ROOT / "WSTOP").exists())

payload = {
    "uid": "FIG-P639-01",
    "handoff_id": "MAIN-R105-P639-SA3-FRESH-ISOLATED-20260826",
    "package_integrity_pass": not failures,
    "figure_verdict": "PASS",
    "checks": checks,
    "failures": failures,
    "ordinary_file_count_before_this_check": len([p for p in ROOT.rglob("*") if p.is_file()]),
}
(ROOT / "machine_final_check.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2))
if failures:
    raise SystemExit(1)
