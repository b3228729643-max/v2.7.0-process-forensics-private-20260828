from __future__ import annotations

import csv
import hashlib
import json
from itertools import combinations
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R9_SA3_FRESH_ISOLATED_R113_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
PDF_HASH = "6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D"
SOURCE_HASH = "2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920"
FAIL_PAIR_IDS = {"P01916", "P01917"}
MANUAL_ONLY_FIELDS = {"reviewer", "decision", "note", "actually_opened"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def headers(rel: str) -> set[str]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as f:
        return set(next(csv.reader(f)))


def png_ok(path: Path) -> bool:
    with Image.open(path) as im:
        im.verify()
    return True


checks: dict[str, object] = {}
errors: list[str] = []


def require(name: str, condition: bool, detail: object) -> None:
    checks[name] = {"ok": bool(condition), "detail": detail}
    if not condition:
        errors.append(name)


identity = json.loads((ROOT / "01_identity/candidate_identity.json").read_text(encoding="utf-8"))
require("root_exists", ROOT.is_dir(), str(ROOT))
require("pdf_identity", PDF.stat().st_size == 4_967_121 and digest(PDF) == PDF_HASH, {"bytes": PDF.stat().st_size, "sha256": digest(PDF)})
require("source_identity", SOURCE.stat().st_size == 4_014 and digest(SOURCE) == SOURCE_HASH, {"bytes": SOURCE.stat().st_size, "sha256": digest(SOURCE)})
require("candidate_identity", identity["uid"] == "FIG-P067-01" and identity["official_round"] == "R113" and identity["physical_page"] == 69 and identity["printed_page"] == 56 and identity["figure_number"] == "4.1", identity)

glyphs = rows("03_objects/glyph_manifest.csv")
graphics = rows("03_objects/graphic_manifest.csv")
occluders = rows("03_objects/occluder_ledger.csv")
safe_map = rows("03_objects/id_safe_filename_map.csv")
glyph_ids = {r["element_id"] for r in glyphs}
graphic_ids = {r["element_id"] for r in graphics}
object_ids = glyph_ids | graphic_ids
require("object_denominator", len(glyphs) == 95 and len(graphics) == 35 and len(object_ids) == 130 and len(occluders) == 5, {"glyphs": len(glyphs), "graphics": len(graphics), "objects": len(object_ids), "occluders": len(occluders)})
require("id_safe_map", len(safe_map) == 130 and len({r["element_id"] for r in safe_map}) == 130 and len({r["safe_filename"] for r in safe_map}) == 130, len(safe_map))

glyph_masks = sorted((ROOT / "03_objects/glyph_masks").glob("*.png"))
graphic_masks = sorted((ROOT / "03_objects/graphic_masks").glob("*.png"))
require("mask_counts", len(glyph_masks) == 95 and len(graphic_masks) == 35, {"glyph_masks": len(glyph_masks), "graphic_masks": len(graphic_masks)})
require("masks_openable", all(png_ok(p) for p in glyph_masks + graphic_masks), len(glyph_masks) + len(graphic_masks))

pair_rows = rows("06_ledgers/after_overlap_report.csv")
pairs = {frozenset((r["a_id"], r["b_id"])) for r in pair_rows}
expected_pairs = {frozenset(pair) for pair in combinations(sorted(object_ids), 2)}
require("all_pairs_exact", len(pair_rows) == 8_385 and len(pairs) == 8_385 and pairs == expected_pairs, {"rows": len(pair_rows), "unique": len(pairs), "expected": len(expected_pairs)})
pair_class_counts: dict[str, int] = {}
for row in pair_rows:
    pair_class_counts[row["relation_class"]] = pair_class_counts.get(row["relation_class"], 0) + 1
require("pair_class_counts", pair_class_counts == {"GRAPHIC_GRAPHIC_TOPOLOGY": 595, "TEXT_GRAPHIC": 3325, "TEXT_TEXT_INDEPENDENT": 3882, "TEXT_TEXT_SAME_PARENT": 583}, pair_class_counts)

critical = rows("05_pairs/critical_pair_manifest.csv")
critical_ids = {r["pair_id"] for r in critical}
require("critical_manifest", len(critical) == 71 and len(critical_ids) == 71, {"rows": len(critical), "unique": len(critical_ids)})
require("critical_graphic_coverage", {x for r in critical for x in (r["a_id"], r["b_id"]) if x.startswith("G")} == graphic_ids, len({x for r in critical for x in (r["a_id"], r["b_id"]) if x.startswith("G")}))
require("critical_pair_assets", all((ROOT / "05_pairs" / r["original_1x"]).is_file() and (ROOT / "05_pairs" / r["overlay_8x"]).is_file() for r in critical), len(critical))

manual_objects = rows("06_ledgers/manual_object_review.csv")
require("manual_object_ledger", len(manual_objects) == 130 and {r["element_id"] for r in manual_objects} == object_ids and all(r["reviewer"] and r["decision"] and r["note"] for r in manual_objects), len(manual_objects))

manual_pairs = rows("06_ledgers/manual_critical_pair_review.csv")
manual_pair_ids = {r["pair_id"] for r in manual_pairs}
manual_fail_ids = {r["pair_id"] for r in manual_pairs if r["decision"].startswith("FAIL")}
require("manual_pair_ledger", len(manual_pairs) == 71 and manual_pair_ids == critical_ids and all(r["reviewer"] and r["decision"] and r["note"] for r in manual_pairs), {"rows": len(manual_pairs), "unique": len(manual_pair_ids)})
require("hard_fail_pairs", manual_fail_ids == FAIL_PAIR_IDS, sorted(manual_fail_ids))
critical_by_id = {r["pair_id"]: r for r in critical}
require("manual_machine_pair_metrics_match", all(r["final_intersection_px"] == critical_by_id[r["pair_id"]]["mask_intersection_px"] and r["pre_occlusion_intersection_px"] == critical_by_id[r["pair_id"]]["pre_occlusion_mask_intersection_px"] and float(r["final_clearance_px"]) == float(critical_by_id[r["pair_id"]]["clearance_px"]) for r in manual_pairs), len(manual_pairs))

views = rows("06_ledgers/manual_view_review.csv")
typography = rows("06_ledgers/manual_typography_review.csv")
math_review = rows("06_ledgers/manual_math_semantic_review.csv")
require("manual_view_ledger", len(views) == 10 and all(r["reviewer"] and r["actually_opened"] == "true" and r["decision"] and r["note"] for r in views), len(views))
require("manual_typography_ledger", len(typography) == 18 and sum(r["kind"] == "SOURCE_FONT" for r in typography) == 9 and sum(r["kind"] == "GLYPH" for r in typography) == 9 and all(r["actually_opened"] == "true" and r["decision"] == "ADVISORY_ONLY" for r in typography), len(typography))
require("manual_math_ledger", len(math_review) == 12 and all(r["decision"] == "PASS" and r["reviewer"] for r in math_review), len(math_review))

math_machine = json.loads((ROOT / "06_ledgers/math_semantic_machine.json").read_text(encoding="utf-8"))
require("math_machine", math_machine["pmf_values"] == [0.15, 0.3, 0.35, 0.2] and math_machine["pmf_sum"] == 1.0 and math_machine["cdf_values_at_support"] == [0.15, 0.45, 0.8, 1.0] and math_machine["cdf_jump_differences"] == [0.15, 0.3, 0.35, 0.2] and math_machine["pmf_nonnegative"] and math_machine["cdf_nondecreasing"] and math_machine["cdf_terminal_value"] == 1.0, math_machine)

required_views = [
    "02_render/page_069_300dpi.png",
    "02_render/full_page_200dpi.png",
    "02_render/figure_crop_300dpi.png",
    "02_render/standalone_300dpi.png",
    "02_render/grayscale_300dpi.png",
    "02_render/figure_crop_300dpi_8x_nearest.png",
    "02_render/after_text_measurement_overlay_300dpi.png",
    "02_render/after_graphic_overlay_300dpi.png",
]
glyph_sheets = [f"04_contacts/glyph_contact_sheet_{i:02d}_{suffix}.png" for i in range(1, 9) for suffix in ("1x", "8x_nearest")]
pair_sheets = [f"05_pairs/critical_pair_contact_{i:02d}_8x_nearest.png" for i in range(1, 7)]
required_pngs = [ROOT / p for p in required_views + glyph_sheets + pair_sheets]
require("required_pngs", all(p.is_file() and png_ok(p) for p in required_pngs), len(required_pngs))

for rel in ["03_objects/glyph_manifest.csv", "03_objects/graphic_manifest.csv", "05_pairs/critical_pair_manifest.csv", "06_ledgers/after_font_audit.csv", "06_ledgers/after_pixel_measurements.csv", "06_ledgers/after_overlap_report.csv"]:
    require(f"machine_headers_no_manual_fields:{rel}", not (headers(rel) & MANUAL_ONLY_FIELDS), sorted(headers(rel) & MANUAL_ONLY_FIELDS))

require("coverage_record", "8,314" in (ROOT / "06_ledgers/manual_pair_coverage.md").read_text(encoding="utf-8") and "8,385" in (ROOT / "06_ledgers/manual_pair_coverage.md").read_text(encoding="utf-8"), "manual_pair_coverage.md")
require("correction_history", "N=117/C=6,786" in (ROOT / "PRE_MANUAL_CORRECTION_HISTORY.md").read_text(encoding="utf-8") and "N=130" in (ROOT / "PRE_MANUAL_CORRECTION_HISTORY.md").read_text(encoding="utf-8"), "PRE_MANUAL_CORRECTION_HISTORY.md")
require("result_status", (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip() == "SA3_FAIL_RETURN_TO_SA2", (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip())

summary = {
    "crosscheck_ok": not errors,
    "errors": errors,
    "status_under_review": "SA3_FAIL_RETURN_TO_SA2",
    "hard_fail_pair_ids": sorted(FAIL_PAIR_IDS),
    "checks": checks,
}
out = ROOT / "07_validation/final_crosscheck.json"
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"crosscheck_ok": not errors, "error_count": len(errors), "errors": errors}, ensure_ascii=False))
raise SystemExit(0 if not errors else 1)
