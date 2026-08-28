from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
SOURCE = WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex"
PAGE_WRAPPER = WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\v260_FIG-P580-01_page.tex"
STANDALONE_WRAPPER = WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\v260_FIG-P580-01_standalone.tex"
SCHEMA = WORKSPACE / r"v2.7.0\_work\evidence\audits\STRICT-GOAL-20260823\STRICT_FIGURE_EVIDENCE_SCHEMA.md"
GOAL = WORKSPACE / r"v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md"
CLEANED_RESIDUE_DIRS = [
    WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\$page",
    WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\$stand",
]

SELF_OUTPUTS = {
    "machine_terminal_input_file_manifest.csv",
    "final_file_integrity.csv",
    "machine_final_check.json",
    "machine_final_check.md",
    "WRITE_STOPPED.md",
}
NONAUTHORITATIVE_PREFIXES = (
    "critical_relations/",
    "pixel_failures/",
    "draft_render_01/",
    "draft_render_02/",
    "draft_render_03/",
    "__pycache__/",
)
NONAUTHORITATIVE_FILES = {
    "diagnostic_text_only.pdf",
    "diagnostic_text_only.png",
    "masks/glyphs/S_FRACTION_01_raw.png",
    "masks/glyphs/S_FRACTION_02_raw.png",
    "masks/glyphs/S_FRACTION_03_raw.png",
    "masks/glyphs/VBAR01_raw.png",
    "masks/glyphs/VBAR02_raw.png",
    "masks/glyphs/VBAR03_raw.png",
}
AUTHORITATIVE_BUILD_FILES = {
    "build/page/v260_FIG-P580-01_page.pdf",
    "build/page/v260_FIG-P580-01_page.log",
    "build/page/v260_FIG-P580-01_page.fls",
    "build/standalone/v260_FIG-P580-01_standalone.pdf",
    "build/standalone/v260_FIG-P580-01_standalone.log",
    "build/standalone/v260_FIG-P580-01_standalone.fls",
    "build/calibration/calibration_low_profile_punctuation.pdf",
    "build/calibration/calibration_low_profile_punctuation.log",
}
KNOWN_EMPTY_LATEX_PLACEHOLDERS = {".idx", ".ind"}

issues: list[str] = []
checks: dict[str, dict[str, object]] = {}


def add_check(name: str, passed: bool, detail: object) -> None:
    checks[name] = {"status": "PASS" if passed else "FAIL", "detail": detail}
    if not passed:
        issues.append(f"{name}: {detail}")


def csv_rows(name: str) -> list[dict[str, str]]:
    path = ROOT / name
    if not path.is_file():
        add_check(f"file_exists::{name}", False, "missing")
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:
        add_check(f"csv_parse::{name}", False, repr(exc))
        return []
    add_check(f"csv_parse::{name}", True, f"rows={len(rows)}")
    return rows


def json_obj(name: str) -> dict:
    path = ROOT / name
    if not path.is_file():
        add_check(f"file_exists::{name}", False, "missing")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        add_check(f"json_parse::{name}", False, repr(exc))
        return {}
    add_check(f"json_parse::{name}", isinstance(value, dict), "object parsed")
    return value if isinstance(value, dict) else {}


def is_true(value: object) -> bool:
    return str(value).strip().lower() in {"true", "yes", "pass", "1"}


def is_pass(value: object) -> bool:
    return str(value).strip().upper() == "PASS"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def nonauthoritative(reason_path: str) -> bool:
    return reason_path in NONAUTHORITATIVE_FILES or reason_path.startswith(NONAUTHORITATIVE_PREFIXES)


def authoritative_category(reason_path: str) -> str | None:
    if reason_path in SELF_OUTPUTS or nonauthoritative(reason_path):
        return None
    if reason_path.startswith("build/"):
        return "FINAL_BUILD" if reason_path in AUTHORITATIVE_BUILD_FILES else None
    if reason_path.startswith("before/"):
        return "PRE_CHANGE_EVIDENCE"
    if reason_path.startswith("masks/"):
        return "CURRENT_NATIVE_MASK"
    if reason_path.startswith("glyph_shape_contact_sheets/"):
        return "CURRENT_CONTACT_SHEET"
    if reason_path.startswith("low_profile_punctuation/"):
        return "CURRENT_LOW_PROFILE_PACKAGE"
    return "CURRENT_REPORT_OR_VIEW"


core = json_obj("core_audit_summary.json")
render = json_obj("render_manifest.json")
math_body = json_obj("math_and_body_consistency.json")
source_anchor = json_obj("source_text_anchor.json")
replay = json_obj("text_only_replay_probe.json")
ownership = json_obj("glyph_ownership_report.json")

font_rows = csv_rows("after_font_audit.csv")
pixel_rows = csv_rows("after_pixel_measurements.csv")
all_pairs = csv_rows("all_unordered_pairs.csv")
required_rows = csv_rows("required_relations.csv")
overlap_rows = csv_rows("after_overlap_report.csv")
d_rows = csv_rows("after_D_same_class.csv")
e_rows = csv_rows("after_E_role_ratios.csv")
objects = csv_rows("object_inventory.csv")
mask_rows = csv_rows("mask_manifest.csv")
glyph_manifest = csv_rows("glyph_contact_manifest.csv")
manual_glyph = csv_rows("manual_glyph_contact_ledger.csv")
manual_visual = csv_rows("manual_visual_harmony_ledger.csv")
opaque_rows = csv_rows("opaque_label_graphic_coverage.csv")
translucent_rows = csv_rows("translucent_label_graphic_coverage.csv")
clip_rows = csv_rows("clip_and_edge_clearance.csv")
completeness_rows = csv_rows("text_completeness_ledger.csv")
role_rows = csv_rows("role_assignment_ledger.csv")
low_profile_rows = csv_rows("low_profile_punctuation_calibration.csv")

expected_core = {
    "uid": "FIG-P580-01",
    "strict_schema_revision": 111,
    "glyph_count": 234,
    "necessary_substring_count": 18,
    "text_element_count": 32,
    "graphic_count": 25,
    "semantic_object_count": 57,
    "expected_unordered_pair_count": 1596,
    "actual_unordered_pair_count": 1596,
    "required_relation_count": 445,
    "critical_relation_package_count": 0,
    "pixel_failure_count": 0,
    "low_profile_punctuation_count": 1,
    "low_profile_calibration_failure_count": 0,
    "font_failure_count": 0,
    "D_failure_count": 0,
    "E_failure_count": 0,
    "pair_failure_count": 0,
    "required_relation_failure_count": 0,
    "clip_failure_count": 0,
    "opaque_label_ground_count": 1,
    "opaque_graphic_coverage_failure_count": 0,
    "translucent_label_ground_count": 0,
    "translucent_graphic_coverage_failure_count": 0,
    "source_unassigned_text_pixels": 0,
    "source_duplicate_text_pixels": 0,
    "glyph_missing_stroke_total": 0,
    "glyph_foreign_pixel_total": 0,
    "contact_sheet_count": 15,
    "contact_manifest_count": 234,
    "visual_template_count": 50,
}
core_mismatches = {key: (core.get(key), value) for key, value in expected_core.items() if core.get(key) != value}
add_check("core_exact_counts", not core_mismatches, core_mismatches or expected_core)
add_check("core_boolean_gates", all(core.get(key) is True for key in (
    "text_completeness_pass", "math_body_consistency_pass", "anchor_checks_pass", "text_replay_exact"
)), {key: core.get(key) for key in ("text_completeness_pass", "math_body_consistency_pass", "anchor_checks_pass", "text_replay_exact")})
add_check("core_empty_mask_ids", core.get("empty_mask_ids") == [], core.get("empty_mask_ids"))

add_check("font_rows", len(font_rows) == 32 and all(is_true(r.get("SOURCE_FONT_PASS")) and r.get("REASON") == "PASS" and float(r.get("EFFECTIVE_PT", 0)) >= 9.5 for r in font_rows), f"rows={len(font_rows)} min_effective_pt={min((float(r['EFFECTIVE_PT']) for r in font_rows), default=-1):.2f}")
add_check("pixel_rows", len(pixel_rows) == 252 and len({r.get("MEASURE_ID") for r in pixel_rows}) == 252 and all(is_pass(r.get("PASS_FAIL")) and is_true(r.get("PIXEL_HEIGHT_PASS")) and int(r.get("MISSING_STROKE_PX", -1)) == 0 and int(r.get("FOREIGN_PIXEL_PX", -1)) == 0 for r in pixel_rows), f"rows={len(pixel_rows)} unique={len({r.get('MEASURE_ID') for r in pixel_rows})}")

object_ids = [r.get("OBJECT_ID", "") for r in objects]
expected_pairs = {tuple(sorted((a, b))) for i, a in enumerate(object_ids) for b in object_ids[i + 1:]}
actual_pairs = [tuple(sorted((r.get("OBJECT_A", ""), r.get("OBJECT_B", "")))) for r in all_pairs]
add_check("object_inventory", len(objects) == 57 and len(set(object_ids)) == 57 and all(is_true(r.get("NONEMPTY")) and int(r.get("PIXELS", 0)) > 0 for r in objects), f"rows={len(objects)} text={sum(r.get('KIND') == 'TEXT' for r in objects)} graphic={sum(r.get('KIND') == 'GRAPHIC' for r in objects)}")
add_check("unordered_pair_formula", len(expected_pairs) == 57 * 56 // 2 == 1596 and len(all_pairs) == 1596 and len(set(actual_pairs)) == 1596 and set(actual_pairs) == expected_pairs, f"expected={len(expected_pairs)} actual={len(all_pairs)} unique={len(set(actual_pairs))}")
add_check("all_pair_results", all(is_pass(r.get("PASS_FAIL")) and not r.get("EVIDENCE_PACKAGE", "").strip() for r in all_pairs), f"failures={sum(not is_pass(r.get('PASS_FAIL')) for r in all_pairs)}")
add_check("required_relations", len(required_rows) == 445 and len({r.get("RELATION_ID") for r in required_rows}) == 445 and all(is_pass(r.get("PASS_FAIL")) and not r.get("EVIDENCE_PACKAGE", "").strip() for r in required_rows), f"rows={len(required_rows)} failures={sum(not is_pass(r.get('PASS_FAIL')) for r in required_rows)}")
overlap_ids = {r.get("PAIR_ID") for r in overlap_rows}
union_ids = {r.get("PAIR_ID") for r in all_pairs} | {r.get("RELATION_ID") for r in required_rows}
add_check("overlap_report_union", len(overlap_rows) == 2041 and overlap_ids == union_ids, f"rows={len(overlap_rows)} union={len(union_ids)}")

add_check("D_gate", len(d_rows) == 79 and all(is_true(r.get("D_PASS")) and r.get("REASON") == "PASS" and 0.92 <= float(r.get("RATIO_TO_CLASS_MEDIAN", 0)) <= 1.08 for r in d_rows), f"rows={len(d_rows)} failures={sum(not is_true(r.get('D_PASS')) for r in d_rows)}")
valid_e = [r for r in e_rows if r.get("E_PASS", "").strip().upper() != "N/A"]
na_e = [r for r in e_rows if r.get("E_PASS", "").strip().upper() == "N/A"]
e_na_reasons = Counter(r.get("REASON", "") for r in na_e)
expected_e_na_reasons = Counter({
    "no same-panel same-script tick base": 26,
    "no eligible all-C-pass sample for role": 2,
})
e_assessed_ok = True
for row in valid_e:
    match = re.fullmatch(r"\[([0-9.]+),([0-9.]+)\]", row.get("EXPECTED_RANGE", ""))
    if not match:
        e_assessed_ok = False
        break
    lower, upper = map(float, match.groups())
    ratio = float(row.get("ROLE_RATIO", "nan"))
    if not (is_true(row.get("E_PASS")) and row.get("REASON") == "PASS" and lower <= ratio <= upper):
        e_assessed_ok = False
        break
e_na_ok = all(
    (
        row.get("REASON") == "no same-panel same-script tick base"
        and row.get("BASE_MEDIAN_PX") == "N/A"
        and row.get("ROLE_RATIO") == "N/A"
        and row.get("ROLE_MEDIAN_PX", "").strip() not in {"", "N/A"}
        and row.get("SCRIPT_CLASS", "").strip() not in {"", "N/A"}
    )
    or (
        row.get("REASON") == "no eligible all-C-pass sample for role"
        and row.get("BASE_MEDIAN_PX") == "N/A"
        and row.get("ROLE_MEDIAN_PX") == "N/A"
        and row.get("ROLE_RATIO") == "N/A"
        and row.get("SCRIPT_CLASS") == "N/A"
    )
    for row in na_e
)
add_check(
    "E_gate",
    len(e_rows) == 38
    and len(valid_e) == 10
    and len(na_e) == 28
    and e_assessed_ok
    and e_na_ok
    and e_na_reasons == expected_e_na_reasons,
    {
        "rows": len(e_rows),
        "assessed": len(valid_e),
        "assessed_failures": sum(not is_true(r.get("E_PASS")) for r in valid_e),
        "justified_NA": len(na_e),
        "NA_reason_counts": dict(e_na_reasons),
    },
)

opaque_nonzero = [r for r in opaque_rows if int(r.get("OVERLAP_PIXEL_COUNT", -1)) != 0]
opaque_zero = [r for r in opaque_rows if int(r.get("OVERLAP_PIXEL_COUNT", -1)) == 0]
opaque_own_node_ok = len(opaque_nonzero) == 1 and all(
    opaque_nonzero[0].get(key) == value
    for key, value in {
        "HALO_ID": "HALO01",
        "GRAPHIC_ID": "GR021",
        "GRAPHIC_ROLE": "NODE_BORDER",
        "OVERLAP_PIXEL_COUNT": "2943",
        "PASS_FAIL": "PASS",
        "REASON": "associated card border; intentional same-node fill/stroke",
    }.items()
)
add_check(
    "opaque_coverage",
    len(opaque_rows) == 25
    and len(opaque_zero) == 24
    and opaque_own_node_ok
    and all(is_pass(r.get("PASS_FAIL")) for r in opaque_rows)
    and all((ROOT / r.get(field, "")).is_file() for r in opaque_rows for field in ("PRE_MASK", "HALO_MASK", "FINAL_VISIBLE_MASK")),
    {
        "rows": len(opaque_rows),
        "zero_overlap_graphics": len(opaque_zero),
        "same_node_border_fill_stroke_overlap": opaque_nonzero,
        "failures": sum(not is_pass(r.get("PASS_FAIL")) for r in opaque_rows),
    },
)
add_check("translucent_coverage", len(translucent_rows) == 0, f"rows={len(translucent_rows)}")
add_check("clip_gate", len(clip_rows) == 32 and all(is_pass(r.get("PASS_FAIL")) and int(r.get("CLIP_PIXEL_COUNT", -1)) == 0 for r in clip_rows), f"rows={len(clip_rows)}")
add_check("text_completeness", len(completeness_rows) == 8 and all(is_pass(r.get("PASS_FAIL")) and r.get("EVIDENCE", "").strip() for r in completeness_rows), f"rows={len(completeness_rows)}")

roles = {r.get("ELEMENT_ID"): r.get("ROLE") for r in role_rows}
role_basis_complete = len(role_rows) == 32 and len(roles) == 32 and all(r.get("SOURCE_LINE", "").strip() and r.get("ROLE_BASIS", "").strip() for r in role_rows)
role_semantics = roles.get("E030") == "LEGEND" and roles.get("E031") == "LEGEND" and roles.get("E004") == "ANNOTATION" and roles.get("E028") == "AXIS_TITLE" and roles.get("E029") == "AXIS_TITLE"
add_check("role_assignment", role_basis_complete and role_semantics, {key: roles.get(key) for key in ("E004", "E028", "E029", "E030", "E031")})

low_ok = len(low_profile_rows) == 1
if low_ok:
    lp = low_profile_rows[0]
    low_ok = (
        lp.get("MEASURE_ID") == "G0198"
        and is_pass(lp.get("PASS_FAIL"))
        and is_true(lp.get("CALIBRATION_PASS"))
        and is_true(lp.get("CALIBRATION_FONT_MATCH"))
        and is_true(lp.get("CALIBRATION_COLOUR_MATCH"))
        and float(lp.get("CALIBRATION_SIZE_DELTA_PT", 99)) <= 0.25
        and 0.92 <= float(lp.get("H_RATIO_TO_CALIBRATION", 0)) <= 1.08
        and 0.92 <= float(lp.get("AREA_RATIO_TO_CALIBRATION", 0)) <= 1.08
    )
add_check("rev111_low_profile_punctuation", low_ok, low_profile_rows[0] if low_profile_rows else "missing")
low_expected = {
    "reference_full_page_300dpi.png",
    "reference_measurement.json",
    "reference_pure_mask_1x.png",
    "reference_pure_mask_8x_nearest.png",
    "reference_source_raw_1x.png",
    "reference_source_raw_8x_nearest.png",
    "G0198/candidate_pure_mask_1x.png",
    "G0198/candidate_pure_mask_8x_nearest.png",
    "G0198/candidate_source_raw_1x.png",
    "G0198/candidate_source_raw_8x_nearest.png",
    "G0198/candidate_target_overlay_1x.png",
    "G0198/candidate_target_overlay_8x_nearest.png",
    "G0198/comparison.json",
}
low_actual = {p.relative_to(ROOT / "low_profile_punctuation").as_posix() for p in (ROOT / "low_profile_punctuation").rglob("*") if p.is_file()}
add_check("low_profile_evidence_package", low_actual == low_expected and all((ROOT / "low_profile_punctuation" / p).stat().st_size > 0 for p in low_expected), f"expected={len(low_expected)} actual={len(low_actual)}")

manifest_ids = [r.get("MAP_ID") for r in glyph_manifest]
manual_ids = [r.get("MAP_ID") for r in manual_glyph]
manual_cells_ok = True
for row in manual_glyph:
    match = re.fullmatch(r"G(\d{4})", row.get("MAP_ID", ""))
    if not match:
        manual_cells_ok = False
        break
    ordinal = int(match.group(1))
    expected_sheet = f"S{((ordinal - 1) // 16) + 1:02d}"
    expected_cell = ((ordinal - 1) % 16) + 1
    if row.get("SHEET") != expected_sheet or int(row.get("CELL", 0)) != expected_cell:
        manual_cells_ok = False
        break
manual_glyph_ok = (
    len(glyph_manifest) == len(manual_glyph) == 234
    and len(set(manifest_ids)) == len(set(manual_ids)) == 234
    and set(manifest_ids) == set(manual_ids)
    and manual_cells_ok
    and all(
        r.get("REVIEWER") == "SA2"
        and r.get("ACTUALLY_OPENED") == "YES"
        and is_pass(r.get("ORIGINAL_MATCH"))
        and is_pass(r.get("OVERLAY_COMPLETE"))
        and is_pass(r.get("MASK_ONLY_PURE"))
        and int(r.get("MISSING_STROKE_PX", -1)) == 0
        and int(r.get("FOREIGN_PIXEL_PX", -1)) == 0
        and is_pass(r.get("DECISION"))
        and r.get("NOTE", "").strip()
        for r in manual_glyph
    )
)
add_check("manual_glyph_ledger", manual_glyph_ok, f"manifest={len(glyph_manifest)} manual={len(manual_glyph)} unique={len(set(manual_ids))}")

contact_files = sorted((ROOT / "glyph_shape_contact_sheets").glob("contact_sheet_*_triple_8x_nearest.png"))
add_check("contact_sheet_set", len(contact_files) == 15 and len({p.name for p in contact_files}) == 15 and all(p.stat().st_size > 0 for p in contact_files), f"count={len(contact_files)}")
manual_visual_ok = (
    len(manual_visual) == 50
    and len({r.get("CHECK_ID") for r in manual_visual}) == 50
    and all(
        r.get("REVIEWER") == "SA2"
        and r.get("ACTUALLY_OPENED") == "YES"
        and r.get("FONT_TOO_SMALL") == "NO"
        and r.get("FONT_ABRUPT_OR_OVERSIZED") == "NO"
        and is_pass(r.get("FONT_VISUAL_HARMONY_PASS"))
        and is_pass(r.get("GRAYSCALE_PASS"))
        and is_pass(r.get("PAGE_INTEGRATION_PASS"))
        and is_pass(r.get("DECISION"))
        and r.get("NOTE", "").strip()
        for r in manual_visual
    )
)
add_check("manual_visual_ledger", manual_visual_ok, f"rows={len(manual_visual)} unique={len({r.get('CHECK_ID') for r in manual_visual})}")

mask_ids = [r.get("MASK_ID", "") for r in mask_rows]
mask_raw_paths = {r.get("RAW_MASK", "").replace("\\", "/") for r in mask_rows}
mask_kind_counts = Counter(r.get("KIND", "") for r in mask_rows)
expected_mask_kind_counts = Counter({
    "GLYPH": 234,
    "GRAPHIC": 25,
    "NODE_BORDER_EDGE": 4,
    "TEXT": 32,
    "TEXT_SUBSTRING": 18,
})
mask_logical_ok = (
    len(mask_rows) == 313
    and len(set(mask_ids)) == 313
    and len(mask_raw_paths) == 313
    and mask_kind_counts == expected_mask_kind_counts
    and all(
        is_true(row.get("NONEMPTY"))
        and int(row.get("PIXELS", 0)) > 0
        and (ROOT / row.get("RAW_MASK", "")).is_file()
        and (ROOT / row.get("RAW_MASK", "")).stat().st_size > 0
        for row in mask_rows
    )
)
add_check(
    "mask_manifest_logical_rows",
    mask_logical_ok,
    {
        "rows": len(mask_rows),
        "unique_ids": len(set(mask_ids)),
        "unique_raw_paths": len(mask_raw_paths),
        "kind_counts": dict(mask_kind_counts),
    },
)

glyph_mask_ids = {row["MASK_ID"] for row in mask_rows if row.get("KIND") == "GLYPH"}
graphic_mask_ids = {row["MASK_ID"] for row in mask_rows if row.get("KIND") == "GRAPHIC"}
source_shape_paths = {f"masks/text_source_shapes/{mask_id}_source.png" for mask_id in glyph_mask_ids}
pre_occlusion_paths = {f"masks/pre_occlusion/{mask_id}_pre_occlusion.png" for mask_id in graphic_mask_ids}
global_derived_mask_paths = {
    "masks/opaque_halos/HALO01_weight_card_opaque_fill.png",
    "masks/text_only_replay_ink_300dpi.png",
}
deprecated_mask_paths = {
    "masks/glyphs/S_FRACTION_01_raw.png",
    "masks/glyphs/S_FRACTION_02_raw.png",
    "masks/glyphs/S_FRACTION_03_raw.png",
    "masks/glyphs/VBAR01_raw.png",
    "masks/glyphs/VBAR02_raw.png",
    "masks/glyphs/VBAR03_raw.png",
}
expected_physical_mask_paths = (
    mask_raw_paths
    | source_shape_paths
    | pre_occlusion_paths
    | global_derived_mask_paths
    | deprecated_mask_paths
)
actual_physical_mask_paths = {
    rel(path) for path in (ROOT / "masks").rglob("*") if path.is_file()
}
add_check(
    "mask_physical_file_formula",
    len(actual_physical_mask_paths) == 580
    and len(expected_physical_mask_paths) == 580
    and actual_physical_mask_paths == expected_physical_mask_paths
    and all((ROOT / path).stat().st_size > 0 for path in actual_physical_mask_paths),
    {
        "logical_raw": len(mask_raw_paths),
        "glyph_source_shape_derivatives": len(source_shape_paths),
        "graphic_pre_occlusion_derivatives": len(pre_occlusion_paths),
        "global_current_derivatives": len(global_derived_mask_paths),
        "declared_deprecated_auxiliary": len(deprecated_mask_paths),
        "formula": "313 + 234 + 25 + 2 + 6 = 580",
        "actual_files": len(actual_physical_mask_paths),
        "missing": sorted(expected_physical_mask_paths - actual_physical_mask_paths),
        "unexpected": sorted(actual_physical_mask_paths - expected_physical_mask_paths),
    },
)
add_check(
    "deprecated_mask_auxiliary_isolation",
    deprecated_mask_paths <= actual_physical_mask_paths
    and deprecated_mask_paths <= NONAUTHORITATIVE_FILES
    and not (deprecated_mask_paths & mask_raw_paths),
    {
        "paths": sorted(deprecated_mask_paths),
        "status": "six pre-final fraction/vbar composites retained as explicitly nonauthoritative; none is a manifest row or current measurement input",
    },
)
add_check("ownership_pollution", ownership.get("source_unassigned_text_pixels") == 0 and ownership.get("source_duplicate_text_pixels") == 0 and ownership.get("source_text_pixels_in_scope", 0) > 0 and ownership.get("rule", "").startswith("BT/ET replay"), {key: ownership.get(key) for key in ("source_text_pixels_in_scope", "source_unassigned_text_pixels", "source_duplicate_text_pixels", "rule")})

add_check("render_identity", render.get("measurement_dpi") == 300 and render.get("resize_after_render") is False and render.get("full_page_300dpi_grid") == [2481, 3508] and render.get("full_page_200dpi_grid") == [1654, 2339] and render.get("standalone_300dpi_grid") == [2481, 3508] and render.get("figure_crop_full_page_px") == [250, 583, 2230, 1525] and render.get("build_exit_codes") == {"page": 0, "standalone": 0}, render)
add_check("math_body_consistency", math_body.get("result") == "PASS" and all(value is True for value in math_body.get("checks", {}).values()), math_body)
add_check("source_anchor", source_anchor.get("result") == "PASS" and all(value is True for value in source_anchor.get("checks", {}).values()), source_anchor)
add_check("text_replay", replay.get("character_stream_exact") is True and replay.get("text_trace_visual_properties_exact") is True and replay.get("parser", {}).get("preserved_clipping_paths") == 0 and replay.get("parser", {}).get("unclosed_path_buffer_entries") == 0, replay)

required_views = {
    "full_page_200dpi.png": (1654, 2339),
    "full_page_300dpi.png": (2481, 3508),
    "figure_crop_300dpi.png": (1980, 942),
    "standalone_300dpi.png": (2481, 3508),
    "grayscale_300dpi.png": (1980, 942),
    "after_text_measurement_overlay_300dpi.png": (2481, 3508),
}
view_details = {}
view_ok = True
for name, expected_size in required_views.items():
    path = ROOT / name
    try:
        with Image.open(path) as image:
            image.load()
            size = image.size
        view_details[name] = size
        view_ok &= size == expected_size
    except Exception as exc:
        view_details[name] = repr(exc)
        view_ok = False
add_check("required_view_openability", view_ok, view_details)

visual_md = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8-sig") if (ROOT / "after_visual_acceptance.md").is_file() else ""
residue_md = (ROOT / "NONAUTHORITATIVE_STALE_INTERMEDIATE_EVIDENCE.md").read_text(encoding="utf-8-sig") if (ROOT / "NONAUTHORITATIVE_STALE_INTERMEDIATE_EVIDENCE.md").is_file() else ""
build_md = (ROOT / "build_commands.md").read_text(encoding="utf-8-sig") if (ROOT / "build_commands.md").is_file() else ""
add_check("manual_markdown_closure", all(token in visual_md for token in ("234 PASS", "Font size and harmony", "Formula card", "Standalone semantic gate", "SA2 local judgment")), "required visual statements present")
add_check("build_markdown_closure", build_md.count("Exit code: `0`") >= 3 and "No official full-book build" in build_md, "commands and exit codes recorded")
add_check(
    "stale_evidence_declaration",
    all(token in residue_md for token in (
        "616",
        "9,684,761",
        "49",
        "42,126",
        "1,366",
        "CLEANED_CURRENT_ROUND_AUXILIARY_RESIDUE",
        "11,205",
    )),
    "stale packages, six deprecated masks, and exact cleaned auxiliary residue declared",
)

for path in (SOURCE, PAGE_WRAPPER, STANDALONE_WRAPPER, SCHEMA, GOAL):
    add_check(f"external_input_exists::{path.name}", path.is_file() and path.stat().st_size > 0, str(path))

page_pdf = ROOT / "build/page/v260_FIG-P580-01_page.pdf"
standalone_pdf = ROOT / "build/standalone/v260_FIG-P580-01_standalone.pdf"
page_fls = ROOT / "build/page/v260_FIG-P580-01_page.fls"
stand_fls = ROOT / "build/standalone/v260_FIG-P580-01_standalone.fls"
fls_ok = all(p.is_file() and "fig_v5_c02_is_support.tex" in p.read_text(encoding="utf-8", errors="ignore") for p in (page_fls, stand_fls))
mtime_ok = all(p.is_file() and p.stat().st_mtime >= SOURCE.stat().st_mtime for p in (page_pdf, standalone_pdf))
add_check("final_build_uses_source", fls_ok and mtime_ok and page_pdf.stat().st_size == 69542 and standalone_pdf.stat().st_size == 40522, {"fls_mentions_source": fls_ok, "pdf_after_source": mtime_ok, "page_bytes": page_pdf.stat().st_size if page_pdf.exists() else None, "standalone_bytes": standalone_pdf.stat().st_size if standalone_pdf.exists() else None})

residue_summary = []
for path in CLEANED_RESIDUE_DIRS:
    files = [p for p in path.rglob("*") if p.is_file()] if path.is_dir() else []
    residue_summary.append({
        "path": str(path),
        "resolved": str(path.resolve()) if path.exists() else None,
        "files": len(files),
        "bytes": sum(p.stat().st_size for p in files),
        "extensions": sorted({p.suffix for p in files}),
    })
add_check(
    "current_round_auxiliary_residue_cleanup",
    len(residue_summary) == 2
    and all(row["resolved"] is None and row["files"] == 0 and row["bytes"] == 0 for row in residue_summary),
    {
        "removed_before_counts": {"files": 8, "bytes": 11205},
        "post_cleanup": residue_summary,
    },
)

integrity_rows = []
png_count = 0
png_failures = []
ordinary_zero = []
nonordinary_zero = []
unsafe_names = []
for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and rel(p) not in SELF_OUTPUTS):
    relative = rel(path)
    size = path.stat().st_size
    nonordinary_empty = relative.startswith("build/") and path.suffix.lower() in KNOWN_EMPTY_LATEX_PLACEHOLDERS
    ordinary = not nonordinary_empty
    if size == 0:
        (ordinary_zero if ordinary else nonordinary_zero).append(relative)
    invalid_parts = [part for part in Path(relative).parts if re.search(r'[<>:"|?*]', part)]
    if invalid_parts:
        unsafe_names.append(relative)
    png_openable = "N/A"
    dimensions = ""
    if path.suffix.lower() == ".png":
        png_count += 1
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                dimensions = f"{image.width}x{image.height}"
            png_openable = "true"
        except Exception as exc:
            png_openable = "false"
            png_failures.append(f"{relative}: {exc!r}")
    category = authoritative_category(relative) or ("NONAUTHORITATIVE_STALE" if nonauthoritative(relative) else "NONAUTHORITATIVE_BUILD_AUX")
    passed = not (ordinary and size == 0) and png_openable != "false" and not invalid_parts
    integrity_rows.append({
        "PATH": relative,
        "CATEGORY": category,
        "ORDINARY_FILE": str(ordinary).lower(),
        "BYTES": size,
        "PNG_OPENABLE": png_openable,
        "DIMENSIONS": dimensions,
        "SAFE_FILENAME": str(not invalid_parts).lower(),
        "PASS_FAIL": "PASS" if passed else "FAIL",
    })
add_check("ordinary_zero_byte_files", not ordinary_zero, {"ordinary_zero": ordinary_zero, "known_nonordinary_empty_latex_placeholders": nonordinary_zero})
add_check("all_png_openable", not png_failures, {"png_count": png_count, "failures": png_failures})
add_check("safe_portable_filenames", not unsafe_names, unsafe_names or f"checked={len(integrity_rows)}")

with (ROOT / "final_file_integrity.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(integrity_rows[0]))
    writer.writeheader()
    writer.writerows(integrity_rows)

dynamic_terminal_products = sorted(SELF_OUTPUTS)
preterminal_local_paths = {
    rel(path)
    for path in ROOT.rglob("*")
    if path.is_file() and rel(path) not in SELF_OUTPUTS
}
manifest_rows = []
for relative in sorted(preterminal_local_paths):
    path = ROOT / relative
    category = authoritative_category(relative) or (
        "NONAUTHORITATIVE_STALE" if nonauthoritative(relative) else "NONAUTHORITATIVE_BUILD_AUX"
    )
    manifest_rows.append({
        "CATEGORY": category,
        "PATH": relative,
        "BYTES": path.stat().st_size,
        "SHA256": sha256(path),
    })
external_entries = [
    ("BUSINESS_SOURCE", SOURCE),
    ("READ_ONLY_BUILD_INPUT", PAGE_WRAPPER),
    ("READ_ONLY_BUILD_INPUT", STANDALONE_WRAPPER),
    ("AUTHORITY_INPUT", SCHEMA),
    ("AUTHORITY_INPUT", GOAL),
]
for category, path in external_entries:
    if path.is_file():
        manifest_rows.append({"CATEGORY": category, "PATH": str(path), "BYTES": path.stat().st_size, "SHA256": sha256(path)})
with (ROOT / "machine_terminal_input_file_manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["CATEGORY", "PATH", "BYTES", "SHA256"])
    writer.writeheader()
    writer.writerows(manifest_rows)

manifest_paths = {r["PATH"] for r in manifest_rows}
manifest_local_paths = {path for path in manifest_paths if not re.match(r"^[A-Za-z]:", path)}
required_manifest_paths = {
    "after_font_audit.csv",
    "after_pixel_measurements.csv",
    "after_overlap_report.csv",
    "after_text_measurement_overlay_300dpi.png",
    "after_visual_acceptance.md",
    "all_unordered_pairs.csv",
    "core_audit_summary.json",
    "figure_crop_300dpi.png",
    "full_page_200dpi.png",
    "grayscale_300dpi.png",
    "manual_glyph_contact_ledger.csv",
    "manual_visual_harmony_ledger.csv",
    "object_inventory.csv",
    "required_relations.csv",
    "role_assignment_ledger.csv",
    "standalone_300dpi.png",
    "text_completeness_ledger.csv",
    "preterminal_manifest_exclusions.md",
    "build/page/v260_FIG-P580-01_page.pdf",
    "build/standalone/v260_FIG-P580-01_standalone.pdf",
}
add_check(
    "preterminal_input_manifest",
    required_manifest_paths <= manifest_paths
    and manifest_local_paths == preterminal_local_paths
    and len(manifest_paths) == len(manifest_rows)
    and set(dynamic_terminal_products) == {
        "WRITE_STOPPED.md",
        "final_file_integrity.csv",
        "machine_final_check.json",
        "machine_final_check.md",
        "machine_terminal_input_file_manifest.csv",
    },
    {
        "entries": len(manifest_rows),
        "local_input_entries": len(manifest_local_paths),
        "external_inputs": len(external_entries),
        "missing_required": sorted(required_manifest_paths - manifest_paths),
        "unlisted_local_inputs": sorted(preterminal_local_paths - manifest_local_paths),
        "unexpected_local_entries": sorted(manifest_local_paths - preterminal_local_paths),
        "excluded_dynamic_products": dynamic_terminal_products,
    },
)

assessed_pairs = [r for r in all_pairs if is_true(r.get("ASSESSED")) and not is_true(r.get("INTENTIONAL_GEOMETRY"))]
text_text = [r for r in assessed_pairs if r.get("RELATION_TYPE") == "TEXT_TEXT"]
card_types = ("CARD_GLYPH_TO_BORDER_EDGE", "CARD_GLYPH_TO_Y_AXIS", "CARD_GLYPH_TO_Y_TICK_TEXT")
card_metrics = {}
for relation_type in card_types:
    subset = [r for r in required_rows if r.get("RELATION_TYPE") == relation_type]
    minimum = min(subset, key=lambda r: float(r["CLEARANCE_PX"])) if subset else {}
    card_metrics[relation_type] = {
        "count": len(subset),
        "minimum_relation": minimum.get("RELATION_ID"),
        "minimum_clearance_px": float(minimum["CLEARANCE_PX"]) if minimum else None,
        "required_clearance_px": float(minimum["REQUIRED_CLEARANCE_PX"]) if minimum else None,
    }

height_metrics = {}
by_script: dict[str, list[dict[str, str]]] = defaultdict(list)
for row in pixel_rows:
    by_script[row.get("SCRIPT_CLASS", "")].append(row)
for script_class, rows in sorted(by_script.items()):
    height_metrics[script_class] = {
        "count": len(rows),
        "minimum_h_ink_px": min(int(r["H_INK_PX"]) for r in rows),
        "maximum_threshold_px": max(int(r["THRESHOLD_PX"]) for r in rows),
        "failures": sum(not is_pass(r.get("PASS_FAIL")) for r in rows),
    }

metrics = {
    "minimum_effective_pt": min(float(r["EFFECTIVE_PT"]) for r in font_rows),
    "glyphs": len(glyph_manifest),
    "necessary_substrings": core.get("necessary_substring_count"),
    "pixel_measurements": len(pixel_rows),
    "text_elements": core.get("text_element_count"),
    "graphics": core.get("graphic_count"),
    "objects": len(objects),
    "unordered_pairs": len(all_pairs),
    "required_relations": len(required_rows),
    "minimum_assessed_pair_clearance_px": min(float(r["CLEARANCE_PX"]) for r in assessed_pairs),
    "minimum_text_text_clearance_px": min(float(r["CLEARANCE_PX"]) for r in text_text),
    "card_relations": card_metrics,
    "height_by_script_class": height_metrics,
    "D_rows": len(d_rows),
    "D_failures": sum(not is_true(r.get("D_PASS")) for r in d_rows),
    "E_rows": len(e_rows),
    "E_assessed": len(valid_e),
    "E_justified_NA": len(na_e),
    "E_failures": sum(not is_true(r.get("E_PASS")) for r in valid_e),
    "opaque_label_grounds": core.get("opaque_label_ground_count"),
    "opaque_coverage_relations": len(opaque_rows),
    "translucent_label_grounds": core.get("translucent_label_ground_count"),
    "clip_rows": len(clip_rows),
    "contact_sheets": len(contact_files),
    "manual_glyph_rows": len(manual_glyph),
    "manual_visual_rows": len(manual_visual),
    "png_files_opened_by_machine": png_count,
    "known_nonordinary_empty_latex_placeholders": len(nonordinary_zero),
    "ordinary_zero_byte_files": len(ordinary_zero),
    "preterminal_input_manifest_entries": len(manifest_rows),
}

source_hashes = {
    "business_source_sha256": sha256(SOURCE),
    "page_pdf_sha256": sha256(page_pdf),
    "standalone_pdf_sha256": sha256(standalone_pdf),
    "figure_crop_sha256": sha256(ROOT / "figure_crop_300dpi.png"),
}

result = "SA2_LOCAL_PASS_AWAIT_ROOT_R96" if not issues else "SA2_LOCAL_FAIL"
final = {
    "uid": "FIG-P580-01",
    "schema_revision": 111,
    "result": result,
    "issues": issues,
    "checks": checks,
    "metrics": metrics,
    "freeze_hashes": source_hashes,
    "cleaned_current_round_auxiliary_residue": {
        "before": {"files": 8, "bytes": 11205},
        "after": residue_summary,
    },
    "nonauthoritative_stale_evidence": {
        "critical_relations": {"files": 616, "bytes": 9684761},
        "pixel_failures": {"files": 49, "bytes": 42126},
        "deprecated_fraction_vbar_masks": {"files": 6, "bytes": 1366},
        "included_in_preterminal_manifest_as_nonauthoritative": True,
    },
    "preterminal_input_manifest": {
        "file": "machine_terminal_input_file_manifest.csv",
        "entries": len(manifest_rows),
        "excluded_dynamic_products": dynamic_terminal_products,
        "self_reference_rule": "Only the manifest itself, final integrity output, two dynamic terminal outputs, and future stop marker are excluded.",
    },
}
(ROOT / "machine_final_check.json").write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# FIG-P580-01 SA2 machine final check",
    "",
    f"Result: `{result}`",
    "",
    f"Schema revision: `{final['schema_revision']}`",
    "",
    "## Check matrix",
    "",
    "| Check | Result | Detail |",
    "|---|---|---|",
]
for name, value in checks.items():
    detail = json.dumps(value["detail"], ensure_ascii=False, sort_keys=True).replace("|", "\\|")
    lines.append(f"| `{name}` | {value['status']} | {detail} |")
lines += [
    "",
    "## Final numeric closure",
    "",
    f"- Objects/pairs: {metrics['objects']} objects; {metrics['unordered_pairs']}/{57 * 56 // 2} unordered pairs; {metrics['required_relations']} required relations.",
    f"- Native text: {metrics['glyphs']} glyphs plus {metrics['necessary_substrings']} necessary substrings = {metrics['pixel_measurements']} measurements; minimum effective size {metrics['minimum_effective_pt']:.2f} pt.",
    f"- Failures: pixel 0; font 0; D {metrics['D_failures']}; E {metrics['E_failures']}; pair 0; required relation 0; clip 0; opaque coverage 0; translucent coverage 0.",
    f"- Clearances: minimum assessed pair {metrics['minimum_assessed_pair_clearance_px']:.6f} px; minimum text-text {metrics['minimum_text_text_clearance_px']:.6f} px.",
    f"- Formula card minima: border {card_metrics['CARD_GLYPH_TO_BORDER_EDGE']['minimum_clearance_px']:.0f}/5 px; y-axis {card_metrics['CARD_GLYPH_TO_Y_AXIS']['minimum_clearance_px']:.0f}/3 px; y-tick text {card_metrics['CARD_GLYPH_TO_Y_TICK_TEXT']['minimum_clearance_px']:.0f}/4 px.",
    f"- E gate: {metrics['E_assessed']} assessed PASS plus {metrics['E_justified_NA']} explicitly justified N/A rows; opaque coverage: 24 zero-overlap graphic rows plus the permitted GR021/HALO01 same-node border-fill/stroke row.",
    "- Mask closure: 313 logical raw-mask rows + 234 glyph source shapes + 25 graphic pre-occlusion masks + 2 global current derivatives + 6 explicitly nonauthoritative pre-final composites = 580 physical files; no missing or unexpected path.",
    f"- Manual evidence: {metrics['manual_glyph_rows']} glyph ledger rows and {metrics['manual_visual_rows']} visual/harmony rows; all PASS with no pending/unknown.",
    f"- File integrity: {metrics['png_files_opened_by_machine']} PNG files machine-opened; {metrics['ordinary_zero_byte_files']} ordinary zero-byte files; {metrics['known_nonordinary_empty_latex_placeholders']} known empty LaTeX `.idx/.ind` placeholders classified nonordinary.",
    f"- Pre-terminal input manifest: {metrics['preterminal_input_manifest_entries']} entries; exact dynamic exclusions: {', '.join(dynamic_terminal_products)}.",
    "",
    "## Freeze hashes",
    "",
]
for name, value in source_hashes.items():
    lines.append(f"- `{name}`: `{value}`")
lines += [
    "",
    "Retained stale packages are explicitly classified nonauthoritative in the pre-terminal input manifest. The two verified current-round literal auxiliary directories were precisely removed (8 files, 11,205 bytes; both paths now absent). No official full-book build was run. This local result awaits root R96 review and is not a strict final PASS declaration.",
]
(ROOT / "machine_final_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

emitted_paths = (
    ROOT / "final_file_integrity.csv",
    ROOT / "machine_terminal_input_file_manifest.csv",
    ROOT / "machine_final_check.json",
    ROOT / "machine_final_check.md",
)
emitted_ok = all(path.is_file() and path.stat().st_size > 0 for path in emitted_paths)
if emitted_ok:
    emitted_ok = json.loads((ROOT / "machine_final_check.json").read_text(encoding="utf-8"))["result"] == result
print(json.dumps({"result": result, "issue_count": len(issues), "emitted_ok": emitted_ok, "metrics": metrics, "freeze_hashes": source_hashes}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not issues and emitted_ok else 1)
