from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
EXPECTED_PDF_SHA = "C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78"
EXPECTED_SOURCE_SHA = "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161"
REVIEWER = "SA3_FRESH_ISOLATED_R108"


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def no_blank_or_pending(records: list[dict]) -> bool:
    bad = {"", "PENDING", "UNKNOWN", "NOT_REVIEWED"}
    return all(all(str(v).strip().upper() not in bad for v in r.values()) for r in records)


def image_ok(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


def check(condition: bool, name: str, checks: dict) -> None:
    checks[name] = bool(condition)


def main() -> None:
    checks = {}
    ident = json.loads((ROOT / "controls/source_identity.json").read_text(encoding="utf-8-sig"))
    check(ident["pdf_sha256"] == EXPECTED_PDF_SHA and ident["pdf_pages"] == 817 and ident["pdf_bytes"] == 4_967_161, "official_pdf_identity", checks)
    check(ident["source_sha256"] == EXPECTED_SOURCE_SHA and ident["source_bytes"] == 5_580, "single_source_identity", checks)
    check(ident["physical_page"] == 630 and ident["printed_page"] == 617 and ident["figure_number"] == "31.6", "independent_locator_identity", checks)
    check(all(ident[k] == 0 for k in ("tex_engine_invocations", "source_edits", "git_writes", "central_state_writes", "second_uid_or_role")), "zero_forbidden_operations", checks)

    manifest = rows(ROOT / "objects/object_manifest.csv")
    glyphs = [r for r in manifest if r["object_type"] == "TEXT_GLYPH"]
    graphics = [r for r in manifest if r["object_type"] == "GRAPHIC"]
    check(len(manifest) == 219 and len({r["object_id"] for r in manifest}) == 219, "object_denominator_219_unique", checks)
    check(len(glyphs) == 194 and len(graphics) == 25, "glyph194_graphic25", checks)
    check(sum(len(r["codepoints"].split("+U")) for r in glyphs) == 195, "visible_codepoint_count_195", checks)
    idmap = rows(ROOT / "objects/id_safe_filename.csv")
    check(len(idmap) == 219 and {r["object_id"] for r in idmap} == {r["object_id"] for r in manifest}, "id_filename_bijection", checks)
    mask_paths = [ROOT / r["mask_path"] for r in manifest]
    check(len(mask_paths) == 219 and all(p.is_file() and image_ok(p) for p in mask_paths), "all_219_masks_open", checks)
    check(all(int(r["area_px"]) > 0 for r in manifest), "empty_mask_count_zero", checks)

    pairs = rows(ROOT / "after_overlap_report.csv")
    pair_keys = {tuple(sorted((r["object_a"], r["object_b"]))) for r in pairs}
    check(len(pairs) == 23_871 and len(pair_keys) == 23_871 and 219 * 218 // 2 == 23_871, "all_unordered_pairs_23871_unique", checks)
    critical = [r for r in pairs if r["critical"].lower() == "true"]
    raw_machine_fail = [r for r in pairs if r["machine_decision"].startswith("FAIL")]
    check(len(critical) == 114, "critical_relation_count_114", checks)
    check(len(raw_machine_fail) == 74, "raw_machine_detection_count_74_preserved", checks)
    check(all(r["relation_id"] in {q["relation_id"] for q in critical} for r in raw_machine_fail), "all_raw_detections_have_critical_evidence", checks)

    glyph_manual = rows(ROOT / "manual/manual_glyph_review.csv")
    graphic_manual = rows(ROOT / "manual/manual_graphic_review.csv")
    relation_manual = rows(ROOT / "manual/manual_relation_review.csv")
    harmony_manual = rows(ROOT / "manual/manual_visual_harmony_review.csv")
    opened_manual = rows(ROOT / "manual/manual_opened_evidence_inventory.csv")
    check(len(glyph_manual) == 194 and len({r["object_id"] for r in glyph_manual}) == 194 and {r["object_id"] for r in glyph_manual} == {r["object_id"] for r in glyphs}, "manual_glyph_ledger_exact", checks)
    check(all(r["decision"] == "PASS" and r["original_match"] == "TRUE" and r["overlay_complete"] == "TRUE" and r["mask_only_pure"] == "TRUE" and r["missing_stroke_px"] == "0" and r["foreign_pixel_px"] == "0" for r in glyph_manual), "manual_glyph_fields_pass", checks)
    check(len(graphic_manual) == 25 and len({r["object_id"] for r in graphic_manual}) == 25 and {r["object_id"] for r in graphic_manual} == {r["object_id"] for r in graphics}, "manual_graphic_ledger_exact", checks)
    check(all(r["decision"].startswith("PASS") and r["original_match"] == "TRUE" and r["overlay_complete"] == "TRUE" and r["mask_only_pure"] == "TRUE" for r in graphic_manual), "manual_graphic_fields_pass", checks)
    check(len(relation_manual) == 114 and len({r["relation_id"] for r in relation_manual}) == 114 and {r["relation_id"] for r in relation_manual} == {r["relation_id"] for r in critical}, "manual_relation_ledger_exact", checks)
    check(all(r["actual_hard_failure"] == "FALSE" and r["original_observed"] == "TRUE" and r["overlay_observed"] == "TRUE" and r["mask_pair_observed"] == "TRUE" for r in relation_manual), "manual_relation_fields_no_hard_failure", checks)
    check(all(r["reviewer"] == REVIEWER for records in (glyph_manual, graphic_manual, relation_manual, harmony_manual, opened_manual) for r in records), "single_reviewer_identity", checks)
    check(all(no_blank_or_pending(records) for records in (glyph_manual, graphic_manual, relation_manual, harmony_manual, opened_manual)), "manual_fields_complete_no_pending", checks)

    opened_counts = {}
    for r in opened_manual:
        opened_counts[r["evidence_kind"]] = opened_counts.get(r["evidence_kind"], 0) + 1
    check(opened_counts == {"VIEW": 5, "CORRECTION": 1, "GLYPH_SHEET": 25, "GRAPHIC_SHEET": 5, "RELATION_SHEET": 23}, "opened_inventory_exact_counts", checks)
    check(all(r["opened"] == "TRUE" and r["decision"] == "PASS" and (ROOT / r["path"]).is_file() and image_ok(ROOT / r["path"]) for r in opened_manual), "all_opened_inventory_images_exist_and_open", checks)
    check(any(r["evidence_or_group"] == "FONT_VISUAL_HARMONY_PASS" and r["decision"] == "PASS" and r["opened"] == "TRUE" for r in harmony_manual), "font_visual_harmony_manual_pass", checks)

    corr = json.loads((ROOT / "r168_correction/correction_summary.json").read_text(encoding="utf-8-sig"))
    corr_rows = rows(ROOT / "r168_correction/card_border_text_recheck.csv")
    check(corr["automated_correction_gate"] == "PASS" and corr["text_objects_rechecked"] == 44 and corr["nonzero_text_intersections"] == 0, "corrected_card_border_gate", checks)
    check(len(corr_rows) == 44 and all(r["corrected_border_intersection_px"] == "0" and r["automated_correction_decision"] == "PASS" for r in corr_rows), "corrected_card_border_rows", checks)

    semantic = json.loads((ROOT / "machine/semantic_numerical_recomputation.json").read_text(encoding="utf-8-sig"))
    critical_cp = json.loads((ROOT / "machine/critical_codepoint_check.json").read_text(encoding="utf-8-sig"))
    check(semantic.get("semantic_decision") == "PASS", "semantic_numerical_gate", checks)
    check(critical_cp.get("machine_decision") == "PASS", "critical_codepoint_gate", checks)
    check(all(r["machine_pixel_decision"] == "PASS" for r in rows(ROOT / "after_pixel_measurements.csv")), "glyph_pixel_machine_gate", checks)
    check(len(list((ROOT / "contacts/glyph").glob("glyph_contact_sheet_*.png"))) == 25, "glyph_sheet_count_25", checks)
    check(len(list((ROOT / "contacts/graphic").glob("graphic_contact_sheet_*.png"))) == 5, "graphic_sheet_count_5", checks)
    check(len(list((ROOT / "relations/sheets").glob("relation_sheet_*.png"))) == 23, "relation_sheet_count_23", checks)
    check(len(list((ROOT / "relations/evidence").glob("REL_*.png"))) == 114, "critical_evidence_count_114", checks)
    manual_result = json.loads((ROOT / "SA3_RESULT.json").read_text(encoding="utf-8-sig"))
    check(manual_result["reviewer"] == REVIEWER and manual_result["decision"] == "A_LOCAL_PASS" and manual_result["manual_actual_hard_failure_count"] == 0, "manual_result_alignment", checks)
    check((ROOT / "RESULT.txt").read_text(encoding="utf-8-sig").splitlines()[0] == "A_LOCAL_PASS" and "Manual SA3 decision: `A_LOCAL_PASS`" in (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8-sig"), "result_narrative_alignment", checks)

    result = {
        "check_count": len(checks),
        "passed_check_count": sum(checks.values()),
        "failed_checks": [k for k, v in checks.items() if not v],
        "checks": checks,
        "automated_crosscheck_gate": "PASS" if all(checks.values()) else "FAIL",
        "manual_fields_created_or_modified": False,
        "frozen_object_denominator": 219,
        "frozen_unordered_pair_denominator": 23871,
        "manual_glyph_rows": len(glyph_manual),
        "manual_graphic_rows": len(graphic_manual),
        "manual_relation_rows": len(relation_manual),
        "actual_hard_failure_count_from_manual_ledger": sum(r["actual_hard_failure"] == "TRUE" for r in relation_manual),
    }
    (ROOT / "controls/final_crosscheck.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise SystemExit(json.dumps(result["failed_checks"]))


if __name__ == "__main__":
    main()
