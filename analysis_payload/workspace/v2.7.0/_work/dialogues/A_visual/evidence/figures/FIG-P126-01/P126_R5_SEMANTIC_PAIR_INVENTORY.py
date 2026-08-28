from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828")
MACHINE = ROOT / "review" / "machine"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    semantic = read_csv(MACHINE / "SEMANTIC_DENOMINATOR.csv")
    mapping = read_csv(MACHINE / "RAW_TO_SEMANTIC_MAP.csv")
    raw = read_csv(MACHINE / "FINAL_RAW_VISIBLE_OBJECTS.csv")
    if len(semantic) != 15 or len({row["object_id"] for row in semantic}) != 15:
        raise RuntimeError("semantic denominator must be unique N=15")
    raw_ids = {row["object_id"] for row in raw}
    mapped_ids = [row["raw_id"] for row in mapping]
    if len(mapping) != 58 or len(set(mapped_ids)) != 58 or set(mapped_ids) != raw_ids:
        raise RuntimeError("raw-to-semantic partition does not close N=58")
    semantic_ids = {row["object_id"] for row in semantic}
    if any(row["semantic_id"] not in semantic_ids for row in mapping):
        raise RuntimeError("mapping contains unknown semantic object")

    pairs = []
    for index, (left, right) in enumerate(itertools.combinations(semantic, 2), 1):
        pairs.append(
            {
                "pair_id": f"SP{index:03d}",
                "left_id": left["object_id"],
                "right_id": right["object_id"],
                "left_role": left["role"],
                "right_role": right["role"],
            }
        )
    if len(pairs) != 105 or len({row["pair_id"] for row in pairs}) != 105:
        raise RuntimeError("semantic all-pairs is not C(15,2)=105")
    write_csv(MACHINE / "SEMANTIC_ALL_UNORDERED_PAIRS.csv", pairs, list(pairs[0]))
    summary = {
        "schema": "P126_R5_SEMANTIC_DENOMINATOR_V1",
        "raw_visible_count": len(raw),
        "raw_mapping_rows": len(mapping),
        "raw_mapping_missing": 0,
        "raw_mapping_duplicate": 0,
        "semantic_visible_count": len(semantic),
        "semantic_unordered_pair_count": len(pairs),
        "expected_pair_count": len(semantic) * (len(semantic) - 1) // 2,
        "manual_fields_generated": 0,
    }
    (MACHINE / "SEMANTIC_DENOMINATOR_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
