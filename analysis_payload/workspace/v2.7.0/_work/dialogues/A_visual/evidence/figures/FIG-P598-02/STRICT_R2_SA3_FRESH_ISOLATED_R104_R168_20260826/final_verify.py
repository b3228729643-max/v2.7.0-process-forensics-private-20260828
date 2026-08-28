import csv
import json
from pathlib import Path

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R2_SA3_FRESH_ISOLATED_R104_R168_20260826")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P598_02_R2_R104_FRESH_SA3_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R104-P598-02-SA3-FRESH-ISOLATED-20260826.md")
EXPECTED_RESULT = "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

manifest = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
machine = json.loads((ROOT / "machine_crosscheck.json").read_text(encoding="utf-8"))
objects = manifest["objects"]
obj_ids = {o["object_id"] for o in objects}
manual_obj = read_csv(ROOT / "manual_object_reviewer.csv")
manual_rel = read_csv(ROOT / "manual_relationship_reviewer.csv")
manual_view = read_csv(ROOT / "manual_view_reviewer.csv")
pairs = read_csv(ROOT / "all_unordered_pairs.csv")
critical_machine = read_csv(ROOT / "critical_relationships_machine.csv")

manual_obj_ids = [r["object_id"] for r in manual_obj]
contact_index = read_csv(ROOT / "contact_sheet_index.csv")
contact_ids = [r["object_id"] for r in contact_index]

checks = {
    "expected_result_exact": (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip() == EXPECTED_RESULT,
    "report_exists_and_mentions_result": REPORT.is_file() and EXPECTED_RESULT in REPORT.read_text(encoding="utf-8"),
    "handoff_exists_and_mentions_result": HANDOFF.is_file() and EXPECTED_RESULT in HANDOFF.read_text(encoding="utf-8"),
    "machine_crosscheck_pass": machine.get("machine_crosscheck_pass") is True,
    "object_manifest_163": len(objects) == 163,
    "object_ids_unique_163": len(obj_ids) == 163,
    "manual_object_rows_163": len(manual_obj) == 163,
    "manual_object_ids_exact": set(manual_obj_ids) == obj_ids and len(manual_obj_ids) == len(set(manual_obj_ids)),
    "manual_object_all_pass": all(r["decision"] == "PASS" for r in manual_obj),
    "manual_object_boolean_complete": all(r["original_match"] == r["overlay_complete"] == r["mask_only_pure"] == "true" for r in manual_obj),
    "manual_object_zero_missing_foreign": all(r["missing_stroke_px"] == r["foreign_pixel_px"] == "0" for r in manual_obj),
    "contact_index_163_exact": len(contact_ids) == 163 and len(set(contact_ids)) == 163 and set(contact_ids) == obj_ids,
    "manual_relationship_rows_16": len(manual_rel) == 16,
    "manual_relationship_all_pass": all(r["decision"] == "PASS" for r in manual_rel),
    "manual_relationship_boolean_complete": all(r["opened_1x"] == r["opened_8x"] == r["object_identity_correct"] == r["mask_a_pure"] == r["mask_b_pure"] == "true" for r in manual_rel),
    "relationship_overlay_files_exist": all((ROOT / "critical_relationships" / r["overlay_file"]).is_file() for r in manual_rel),
    "critical_machine_rows_16": len(critical_machine) == 16,
    "manual_view_rows_8": len(manual_view) == 8,
    "manual_view_all_pass": all(r["decision"] == "PASS" for r in manual_view),
    "view_files_exist": all((ROOT / r["file"]).is_file() for r in manual_view),
    "pairs_13203": len(pairs) == 13203,
    "pair_ids_unique": len({r["pair_id"] for r in pairs}) == 13203,
    "all_pair_intersections_zero": all(int(r["intersection_px"]) == 0 for r in pairs),
    "all_masks_nonempty": all(not o["empty_mask_machine"] for o in objects),
    "raw_masks_163": len(list((ROOT / "raw_masks").glob("*.png"))) == 163,
    "contact_sheets_19": len(list((ROOT / "contact_sheets").glob("*.png"))) == 19,
    "matrices_2": len(list((ROOT / "matrices").glob("*.png"))) == 2,
    "critical_overlays_16": len(list((ROOT / "critical_relationships").glob("*.png"))) == 16,
    "no_pyc": not any(ROOT.rglob("*.pyc")),
    "no_cache_dirs": not any(p.is_dir() and p.name == "__pycache__" for p in ROOT.rglob("*")),
    "semantic_flags_true": all(token in (ROOT / "manual_semantic_adjudication.md").read_text(encoding="utf-8") for token in ["FONT_VISUAL_HARMONY_PASS=true","SEMANTICS_PASS=true","GEOMETRY_PASS=true","GRAYSCALE_PASS=true","PAGE_INTEGRATION_PASS=true"]),
}
checks["terminal_crosscheck_pass"] = all(checks.values())
out = {
    "figure_uid": "FIG-P598-02",
    "handoff_id": "A-R104-P598-02-SA3-FRESH-ISOLATED-20260826",
    "result": EXPECTED_RESULT,
    "checks": checks,
}
(ROOT / "final_machine_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
if not checks["terminal_crosscheck_pass"]:
    failed = [k for k,v in checks.items() if not v]
    raise SystemExit("FINAL_VERIFY_FAIL: " + ",".join(failed))
print(json.dumps(out, ensure_ascii=False, indent=2))
