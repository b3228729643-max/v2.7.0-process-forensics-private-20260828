from __future__ import annotations

import csv
import json
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "denominator" / "object_manifest.csv"
PAIRS = ROOT / "denominator" / "all_unordered_pairs.csv"
MANUAL_OBJECTS = ROOT / "manual" / "manual_object_review.csv"
MANUAL_PAIRS = ROOT / "manual" / "manual_pair_adjudication.csv"
OUTPUT = ROOT / "mechanical" / "manual_ledger_validation.json"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    manifest = rows(MANIFEST)
    all_pairs = rows(PAIRS)
    manual_objects = rows(MANUAL_OBJECTS)
    manual_pairs = rows(MANUAL_PAIRS)

    manifest_ids = [row["OBJECT_ID"] for row in manifest]
    expected_pair_ids = {
        row["PAIR_ID"]
        for row in all_pairs
        if row["BBOX_RELATION_MECHANICAL"] == "BBOX_TOUCH_OR_OVERLAP"
    }
    manual_pair_ids = {row["PAIR_ID"] for row in manual_pairs}
    canonical_pair_keys = {(row["OBJECT_A"], row["OBJECT_B"]) for row in all_pairs}
    expected_pair_keys = set(combinations(manifest_ids, 2))

    checks = {
        "manifest_object_count_69": len(manifest) == 69,
        "manifest_ids_unique": len(manifest_ids) == len(set(manifest_ids)),
        "all_pair_count_2346": len(all_pairs) == 2346,
        "all_pair_keys_complete": canonical_pair_keys == expected_pair_keys,
        "manual_object_count_69": len(manual_objects) == 69,
        "manual_object_ids_exact": {row["OBJECT_ID"] for row in manual_objects} == set(manifest_ids),
        "manual_object_ids_unique": len(manual_objects) == len({row["OBJECT_ID"] for row in manual_objects}),
        "manual_object_fields_nonblank": all(
            all(row[field].strip() for field in ("MANUAL_DECISION", "POST_OBSERVATION_NOTE", "OBSERVED_EVIDENCE"))
            for row in manual_objects
        ),
        "manual_candidate_count_97": len(manual_pairs) == 97,
        "manual_candidate_ids_exact": manual_pair_ids == expected_pair_ids,
        "manual_candidate_ids_unique": len(manual_pairs) == len(manual_pair_ids),
        "manual_candidate_fields_nonblank": all(
            all(row[field].strip() for field in ("MANUAL_CLASS", "POST_OBSERVATION_NOTE", "OPENED_EVIDENCE"))
            for row in manual_pairs
        ),
        "manual_candidate_pixel_total_17244": sum(int(row["COMPOSITE_CANDIDATE_PX"]) for row in manual_pairs) == 17244,
        "manual_true_illegal_overlap_total_zero": sum(int(row["TRUE_ILLEGAL_OVERLAP_PX"]) for row in manual_pairs) == 0,
        "manual_unresolved_zero": all(row["UNRESOLVED"].lower() == "false" for row in manual_pairs),
    }
    summary = {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "manifest_object_count": len(manifest),
        "all_unordered_pair_count": len(all_pairs),
        "manual_object_review_count": len(manual_objects),
        "manual_candidate_adjudication_count": len(manual_pairs),
        "manual_candidate_pixel_total": sum(int(row["COMPOSITE_CANDIDATE_PX"]) for row in manual_pairs),
        "true_illegal_overlap_pixel_total": sum(int(row["TRUE_ILLEGAL_OVERLAP_PX"]) for row in manual_pairs),
        "unresolved_candidate_count": sum(row["UNRESOLVED"].lower() != "false" for row in manual_pairs),
        "manual_fields_generated_or_overwritten": False,
    }
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not summary["all_checks_pass"]:
        raise RuntimeError(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
