from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R1_SA2_R168_READONLY_R114_20260828")


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    registry = rows("visible_object_registry.csv")
    machine_pairs = rows("machine_unordered_pair_universe.csv")
    manual_objects = rows("manual_object_observations.csv")
    manual_pairs = rows("manual_unordered_pair_adjudication.csv")
    opened_views = rows("manual_view_open_ledger.csv")

    object_ids = [row["OBJECT_ID"] for row in registry]
    machine_pair_keys = [
        (row["PAIR_ID"], row["OBJECT_A_ID"], row["OBJECT_B_ID"]) for row in machine_pairs
    ]
    manual_pair_keys = [
        (row["PAIR_ID"], row["OBJECT_A_ID"], row["OBJECT_B_ID"]) for row in manual_pairs
    ]

    expected_view_files = [row["FILE"] for row in opened_views]
    missing_view_files = [name for name in expected_view_files if not (ROOT / name).is_file()]
    missing_object_reviews = sorted(set(object_ids) - {row["OBJECT_ID"] for row in manual_objects})
    extra_object_reviews = sorted({row["OBJECT_ID"] for row in manual_objects} - set(object_ids))
    missing_pair_reviews = sorted(set(machine_pair_keys) - set(manual_pair_keys))
    extra_pair_reviews = sorted(set(manual_pair_keys) - set(machine_pair_keys))

    audit = {
        "frozen_denominator_count": len(object_ids),
        "unique_object_id_count": len(set(object_ids)),
        "expected_unordered_pair_count": len(object_ids) * (len(object_ids) - 1) // 2,
        "machine_pair_count": len(machine_pairs),
        "unique_machine_pair_key_count": len(set(machine_pair_keys)),
        "manual_object_review_count": len(manual_objects),
        "manual_pair_review_count": len(manual_pairs),
        "unique_manual_pair_key_count": len(set(manual_pair_keys)),
        "manual_opened_view_count": len(opened_views),
        "missing_view_files": missing_view_files,
        "missing_object_reviews": missing_object_reviews,
        "extra_object_reviews": extra_object_reviews,
        "missing_pair_reviews": missing_pair_reviews,
        "extra_pair_reviews": extra_pair_reviews,
        "blank_manual_object_observation_rows": [
            row["OBJECT_ID"] for row in manual_objects if not row["OBSERVATION"].strip()
        ],
        "blank_manual_pair_note_rows": [
            row["PAIR_ID"] for row in manual_pairs if not row["POST_OBSERVATION_NOTE"].strip()
        ],
    }

    if any(
        [
            len(object_ids) != 21,
            len(set(object_ids)) != 21,
            len(machine_pairs) != 210,
            len(set(machine_pair_keys)) != 210,
            len(manual_objects) != 21,
            len(manual_pairs) != 210,
            len(set(manual_pair_keys)) != 210,
            len(opened_views) != 11,
            missing_view_files,
            missing_object_reviews,
            extra_object_reviews,
            missing_pair_reviews,
            extra_pair_reviews,
            audit["blank_manual_object_observation_rows"],
            audit["blank_manual_pair_note_rows"],
        ]
    ):
        raise RuntimeError(json.dumps(audit, ensure_ascii=False, indent=2))

    (ROOT / "machine_ledger_consistency_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, ensure_ascii=True))


if __name__ == "__main__":
    main()
