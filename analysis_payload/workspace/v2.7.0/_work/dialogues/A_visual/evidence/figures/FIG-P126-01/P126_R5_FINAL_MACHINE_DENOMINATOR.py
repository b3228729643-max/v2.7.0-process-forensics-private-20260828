from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828")
MACHINE = ROOT / "review" / "machine"

PREFIX = {"char": "T", "line": "L", "curve": "V", "rect": "R"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def intersection(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0, 0.0, 0.0
    return x1 - x0, y1 - y0, (x1 - x0) * (y1 - y0)


def main():
    provisional = read_csv(MACHINE / "RAW_VISIBLE_OBJECTS.csv")
    counters = {key: 0 for key in PREFIX}
    final = []
    provisional_duplicate_ids = len(provisional) - len({row["object_id"] for row in provisional})
    for row in provisional:
        kind = row["kind"]
        counters[kind] += 1
        corrected = dict(row)
        corrected["object_id"] = f"{PREFIX[kind]}{counters[kind]:03d}"
        final.append(corrected)
    if len(final) != 58 or len({row["object_id"] for row in final}) != 58:
        raise RuntimeError("corrected raw denominator is not unique N=58")
    write_csv(MACHINE / "FINAL_RAW_VISIBLE_OBJECTS.csv", final, list(final[0]))

    pairs = []
    for index, (left, right) in enumerate(itertools.combinations(final, 2), 1):
        a = tuple(float(left[key]) for key in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))
        b = tuple(float(right[key]) for key in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))
        width, height, area = intersection(a, b)
        pairs.append(
            {
                "pair_id": f"RP{index:04d}",
                "left_id": left["object_id"],
                "right_id": right["object_id"],
                "bbox_intersects": str(int(area > 0)),
                "intersection_width_pt": f"{width:.6f}",
                "intersection_height_pt": f"{height:.6f}",
                "intersection_area_pt2": f"{area:.6f}",
            }
        )
    if len(pairs) != 1653 or len({row["pair_id"] for row in pairs}) != 1653:
        raise RuntimeError("corrected raw pair denominator is not C(58,2)=1653")
    write_csv(MACHINE / "FINAL_RAW_ALL_UNORDERED_PAIRS.csv", pairs, list(pairs[0]))

    trace = {
        "schema": "P126_R5_FINAL_RAW_DENOMINATOR_CORRECTION_V1",
        "correction_stage": "pre_manual",
        "provisional_raw_count": len(provisional),
        "provisional_duplicate_object_ids": provisional_duplicate_ids,
        "provisional_issue": "char and curve rows both used C-prefix identifiers",
        "correction": "renamed char=C to T and curve=C to V without changing row order, geometry, text, or colors",
        "final_raw_count": len(final),
        "final_raw_unique_ids": len({row["object_id"] for row in final}),
        "final_raw_pair_count": len(pairs),
        "expected_pair_count": len(final) * (len(final) - 1) // 2,
        "manual_fields_generated": 0,
    }
    (MACHINE / "FINAL_RAW_DENOMINATOR_CORRECTION.json").write_text(
        json.dumps(trace, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    main()
