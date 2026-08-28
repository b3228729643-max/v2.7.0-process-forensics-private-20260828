from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R1_SA2_R168_READONLY_R111_20260827")


def read_csv(path: Path, delimiter: str = ",") -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def main() -> None:
    denominator = read_csv(ROOT / "machine" / "atomic_denominator.csv")
    manual = read_csv(ROOT / "manual" / "atomic_id_manual_ledger.psv", "|")
    pairs = read_csv(ROOT / "machine" / "all_unordered_pairs.csv")
    relations = read_csv(ROOT / "manual" / "critical_relationship_manual_ledger.psv", "|")
    den_ids = [r["atom_id"] for r in denominator]
    manual_ids = [r["atom_id"] for r in manual]
    pair_keys = [tuple(sorted((r["atom_a"], r["atom_b"]))) for r in pairs]
    required_views = [
        "full_page_200dpi.png",
        "figure_body_native_crop_300dpi.png",
        "figure_caption_native1x_300dpi.png",
        "figure_caption_grayscale_300dpi.png",
        "atomic_bbox_overlay_300dpi.png",
        "figure_caption_nearest8x.png",
        "critical_bottom_y_ticks_native1x_300dpi.png",
        "critical_bottom_y_ticks_nearest8x.png",
    ]
    facts = {
        "denominator_count": len(denominator),
        "manual_id_count": len(manual),
        "manual_missing_id_count": len(set(den_ids) - set(manual_ids)),
        "manual_extra_id_count": len(set(manual_ids) - set(den_ids)),
        "manual_duplicate_id_count": len(manual_ids) - len(set(manual_ids)),
        "pair_expected_count": len(denominator) * (len(denominator) - 1) // 2,
        "pair_written_count": len(pairs),
        "pair_duplicate_count": len(pair_keys) - len(set(pair_keys)),
        "pair_self_count": sum(r["atom_a"] == r["atom_b"] for r in pairs),
        "manual_relation_count": len(relations),
        "required_view_missing_count": sum(not (ROOT / "views" / name).is_file() for name in required_views),
        "write_stopped_marker_preseal_count": len(list(ROOT.rglob("WRITE_STOPPED*"))),
        "status_code": "READY_FOR_SINGLE_SEAL",
    }
    if any(
        facts[key] != 0
        for key in (
            "manual_missing_id_count", "manual_extra_id_count", "manual_duplicate_id_count",
            "pair_duplicate_count", "pair_self_count", "required_view_missing_count",
            "write_stopped_marker_preseal_count",
        )
    ):
        raise SystemExit(json.dumps(facts, ensure_ascii=False, indent=2))
    if facts["pair_written_count"] != facts["pair_expected_count"] or facts["denominator_count"] != 145:
        raise SystemExit(json.dumps(facts, ensure_ascii=False, indent=2))
    (ROOT / "audit" / "preseal_validation.json").write_text(
        json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
