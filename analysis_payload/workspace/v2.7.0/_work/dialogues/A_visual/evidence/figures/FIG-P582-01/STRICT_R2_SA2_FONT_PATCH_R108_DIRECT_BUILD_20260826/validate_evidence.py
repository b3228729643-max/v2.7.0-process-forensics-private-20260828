from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826")


def read_delimited(path: Path, delimiter: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=delimiter))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


machine = json.loads((ROOT / "MACHINE_RESULT.json").read_text(encoding="utf-8"))
objects = read_delimited(ROOT / "object_inventory.csv", ",")
pairs = read_delimited(ROOT / "all_unordered_pairs.csv", ",")
manual_objects = read_delimited(ROOT / "MANUAL_OBJECT_LEDGER.tsv", "\t")
manual_relations = read_delimited(ROOT / "MANUAL_RELATION_LEDGER.tsv", "\t")
manual_views = read_delimited(ROOT / "MANUAL_VIEW_SEMANTIC_LEDGER.tsv", "\t")

object_ids = [row["id"] for row in objects]
manual_object_ids = [row["object_id"] for row in manual_objects]
pair_ids = [row["pair_id"] for row in pairs]
critical_pair_ids = [row["pair_id"] for row in pairs if row["machine_class"] != "CLEAR"]
manual_relation_ids = [row["pair_id"] for row in manual_relations]

checks = {
    "object_count_95": len(objects) == 95,
    "glyph_count_78": sum(row["kind"] == "glyph" for row in objects) == 78,
    "graphic_count_17": sum(row["kind"] == "graphic" for row in objects) == 17,
    "object_ids_unique": len(object_ids) == len(set(object_ids)),
    "manual_object_count_95": len(manual_objects) == 95,
    "manual_object_ids_exact": set(manual_object_ids) == set(object_ids),
    "manual_object_ids_unique": len(manual_object_ids) == len(set(manual_object_ids)),
    "manual_object_notes_nonblank": all(row["object_specific_note"].strip() for row in manual_objects),
    "manual_object_decisions_all_pass": all(row["decision"] == "PASS" for row in manual_objects),
    "pair_count_4465": len(pairs) == 4465,
    "pair_count_formula": len(pairs) == 95 * 94 // 2,
    "pair_ids_unique": len(pair_ids) == len(set(pair_ids)),
    "critical_pair_count_33": len(critical_pair_ids) == 33,
    "manual_relation_count_33": len(manual_relations) == 33,
    "manual_relation_ids_exact": set(manual_relation_ids) == set(critical_pair_ids),
    "manual_relation_ids_unique": len(manual_relation_ids) == len(set(manual_relation_ids)),
    "manual_relation_notes_nonblank": all(row["pair_specific_note"].strip() for row in manual_relations),
    "manual_relation_hard_failure_zero": all(row["hard_failure"].lower() == "false" for row in manual_relations),
    "manual_view_rows_15": len(manual_views) == 15,
    "manual_view_notes_nonblank": all(row["check_specific_note"].strip() for row in manual_views),
    "manual_view_decisions_all_pass": all(row["decision"] == "PASS" for row in manual_views),
    "machine_empty_masks_zero": machine["machine"]["empty_masks"] == 0,
    "machine_page_edge_clip_zero": machine["machine"]["page_edge_clip_candidates"] == 0,
    "machine_manual_fields_generated_zero": machine["manual_fields_generated_by_machine"] == 0,
    "source_semantic_hard_pass": all(
        [
            machine["semantic_checks"]["raw_sequence_exact"],
            machine["semantic_checks"]["running_mean_sequence_exact"],
            machine["semantic_checks"]["truth_line_exact"],
            machine["semantic_checks"]["raw_values_present_in_pdf_text"],
            machine["semantic_checks"]["labels_present_in_pdf_text"],
            machine["semantic_checks"]["axis_semantics_present"],
            machine["semantic_checks"]["formula_tokens_present"],
            machine["semantic_checks"]["all_visible_explicit_fonts_ge_9_5pt"],
            machine["semantic_checks"]["forbidden_scale_token_count"] == 0,
        ]
    ),
}

manual_paths = [ROOT / "MANUAL_OBJECT_LEDGER.tsv", ROOT / "MANUAL_RELATION_LEDGER.tsv", ROOT / "MANUAL_VIEW_SEMANTIC_LEDGER.tsv"]
time_integrity = {}
for path in manual_paths:
    rows = read_delimited(path, "\t")
    max_observed = max(datetime.fromisoformat(row["observed_at_utc"].replace("Z", "+00:00")) for row in rows)
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    time_integrity[path.name] = {
        "max_observed_at_utc": max_observed.isoformat(),
        "file_mtime_utc": mtime.isoformat(),
        "mtime_not_before_observation": mtime >= max_observed,
    }
checks["manual_time_integrity_all_pass"] = all(row["mtime_not_before_observation"] for row in time_integrity.values())

png_failures = []
for path in ROOT.rglob("*.png"):
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        png_failures.append({"path": str(path.relative_to(ROOT)), "error": str(exc)})
checks["png_parse_failures_zero"] = len(png_failures) == 0

result = {
    "uid": "FIG-P582-01",
    "round": "STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826",
    "validated_at_utc": datetime.now(timezone.utc).isoformat(),
    "N": 95,
    "C": 4465,
    "critical_relations": 33,
    "manual_object_rows": len(manual_objects),
    "manual_relation_rows": len(manual_relations),
    "manual_view_semantic_rows": len(manual_views),
    "hard_failures": 0 if all(checks.values()) else 1,
    "checks": checks,
    "time_integrity": time_integrity,
    "png_parse_failures": png_failures,
    "machine_result_sha256": sha256(ROOT / "MACHINE_RESULT.json"),
    "status": "LOCAL_SA2_PASS_READY_TO_SEAL" if all(checks.values()) else "VALIDATION_FAIL",
}
(ROOT / "FINAL_VALIDATION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print(json.dumps({"status": result["status"], "checks": len(checks), "failed": [key for key, value in checks.items() if not value]}, ensure_ascii=True))
