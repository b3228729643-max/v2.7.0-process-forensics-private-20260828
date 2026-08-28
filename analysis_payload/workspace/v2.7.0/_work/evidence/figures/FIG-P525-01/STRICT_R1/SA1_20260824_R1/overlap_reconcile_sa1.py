#!/usr/bin/env python3
"""Independent accounting reconciliation for SA1 raw overlap evidence.

Reads only the fresh SA1 evidence folder.  It neither renders the PDF nor
touches project source.  It verifies the per-pair overlap PNG against the CSV
and proves that the four nonzero pair counts cannot double-count pixels because
their A-side semantic PDF bboxes are disjoint.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image


OUT = Path(__file__).resolve().parent


def parse_bbox(value: str) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = (float(v) for v in value.split(";"))
    return x0, y0, x1, y1


def bboxes_intersect(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def main() -> None:
    with (OUT / "after_overlap_report.csv").open(encoding="utf-8-sig", newline="") as f:
        relations = list(csv.DictReader(f))
    with (OUT / "semantic_component_inventory.csv").open(encoding="utf-8-sig", newline="") as f:
        semantic_bbox = {row["ELEMENT_ID"]: parse_bbox(row["PDF_BBOX"]) for row in csv.DictReader(f)}

    failed = [row for row in relations if int(row["OVERLAP_PIXEL_COUNT"]) > 0]
    rows: list[dict[str, object]] = []
    for row in failed:
        rid = row["RELATION_ID"]
        path = OUT / "critical" / f"{rid}_overlap.png"
        mask_count = int((np.asarray(Image.open(path).convert("L")) > 0).sum())
        csv_count = int(row["OVERLAP_PIXEL_COUNT"])
        rows.append({
            "RELATION_ID": rid,
            "ELEMENT_A": row["ELEMENT_A"],
            "ELEMENT_B": row["ELEMENT_B"],
            "OVERLAP_CSV_PIXELS": csv_count,
            "OVERLAP_RAW_MASK_PIXELS": mask_count,
            "NET_CLEARANCE_PX": row["CLEARANCE_PX"],
            "CLIP_PIXELS": row["CLIP_PIXEL_COUNT"],
            "MASK_COUNT_MATCH": "PASS" if mask_count == csv_count else "FAIL",
            "A_PDF_BBOX": ";".join(f"{v:.3f}" for v in semantic_bbox[row["ELEMENT_A"]]),
        })

    a_ids = [row["ELEMENT_A"] for row in failed]
    pairs = [(a_ids[i], a_ids[j]) for i in range(len(a_ids)) for j in range(i + 1, len(a_ids))]
    disjoint = len(a_ids) == len(set(a_ids)) and all(not bboxes_intersect(semantic_bbox[a], semantic_bbox[b]) for a, b in pairs)
    pair_sum = sum(int(row["OVERLAP_CSV_PIXELS"]) for row in rows)
    mask_sum = sum(int(row["OVERLAP_RAW_MASK_PIXELS"]) for row in rows)
    all_clip = sum(int(row["CLIP_PIXEL_COUNT"]) for row in relations)
    all_match = all(row["MASK_COUNT_MATCH"] == "PASS" for row in rows)
    unique_pixels = pair_sum if disjoint else None
    status = "PASS" if all_match and disjoint and all_clip == 0 else "FAIL"
    payload = {
        "audit_id": "FIG-P525-01/STRICT_R1/SA1_20260824_R1",
        "method": "Counts each native-300dpi no-dilation overlap mask; then uses disjoint A-side semantic PDF bboxes to prove pair counts are mutually exclusive.",
        "failed_pair_count": len(rows),
        "failed_pairs": rows,
        "pair_sum_overlap_pixels": pair_sum,
        "raw_mask_sum_overlap_pixels": mask_sum,
        "a_side_semantic_bboxes_pairwise_disjoint": disjoint,
        "duplicate_pixels_across_failed_pairs": 0 if disjoint else None,
        "unique_overlap_pixels": unique_pixels,
        "all_registered_relation_clip_pixels": all_clip,
        "status": status,
    }
    with (OUT / "overlap_reconciliation.json").open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with (OUT / "overlap_reconciliation.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    if status != "PASS":
        raise SystemExit("overlap reconciliation FAILED")


if __name__ == "__main__":
    main()
