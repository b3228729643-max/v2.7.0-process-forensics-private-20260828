from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


errors: list[str] = []
json_parse_errors = 0
csv_parse_errors = 0
png_decode_errors = 0

for path in sorted(ROOT.rglob("*.json")):
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        json_parse_errors += 1
        errors.append(f"json:{path.relative_to(ROOT).as_posix()}:{exc}")

for path in sorted(ROOT.rglob("*.csv")):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            list(csv.reader(handle))
    except Exception as exc:
        csv_parse_errors += 1
        errors.append(f"csv:{path.relative_to(ROOT).as_posix()}:{exc}")

for path in sorted(ROOT.rglob("*.png")):
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        png_decode_errors += 1
        errors.append(f"png:{path.relative_to(ROOT).as_posix()}:{exc}")

glyphs = read_csv("after_pixel_measurements.csv")
graphics = read_csv("graphics_inventory.csv")
pairs = read_csv("all_unordered_pairs.csv")
critical = read_csv("critical_relations_machine.csv")
texts = read_csv("text_elements.csv")
manual_glyphs = read_csv("manual_glyph_ledger.csv")
manual_graphics = read_csv("manual_graphic_ledger.csv")
manual_critical = read_csv("manual_critical_relation_ledger.csv")
manual_semantic = read_csv("manual_semantic_text_ledger.csv")
manual_hard = read_csv("manual_hard_gate_ledger.csv")
manual_views = read_csv("manual_view_ledger.csv")
manual_typography = read_csv("manual_typography_ledger.csv")

glyph_ids = [row["element_id"] for row in glyphs]
graphic_ids = [row["object_id"] for row in graphics]
object_ids = glyph_ids + graphic_ids
pair_keys = [(row["object_a"], row["object_b"]) for row in pairs]
expected_pair_keys = set(itertools.combinations(object_ids, 2))
observed_pair_keys = set(pair_keys)

checks = {
    "visible_glyph_rows": len(glyphs),
    "visible_graphic_rows": len(graphics),
    "visible_object_denominator": len(object_ids),
    "unique_visible_object_ids": len(set(object_ids)),
    "all_unordered_pair_rows": len(pairs),
    "unique_unordered_pair_rows": len(observed_pair_keys),
    "missing_expected_pair_rows": len(expected_pair_keys - observed_pair_keys),
    "foreign_pair_rows": len(observed_pair_keys - expected_pair_keys),
    "raw_nonzero_overlap_pairs": sum(int(row["raw_mask_overlap_px"]) > 0 for row in pairs),
    "raw_overlap_pixel_sum": sum(int(row["raw_mask_overlap_px"]) for row in pairs),
    "critical_relation_rows": len(critical),
    "semantic_text_rows": len(texts),
    "semantic_text_mismatches": sum(
        row["expected_visible_text"] != row["extracted_visible_text"] for row in texts
    ),
    "empty_glyph_masks": sum(int(row["ink_area_px"]) <= 0 for row in glyphs),
    "empty_graphic_masks": sum(int(row["ink_area_px"]) <= 0 for row in graphics),
    "manual_glyph_rows": len(manual_glyphs),
    "manual_graphic_rows": len(manual_graphics),
    "manual_critical_rows": len(manual_critical),
    "manual_semantic_rows": len(manual_semantic),
    "manual_hard_gate_rows": len(manual_hard),
    "manual_view_rows": len(manual_views),
    "manual_typography_rows": len(manual_typography),
    "manual_glyph_id_symmetric_difference": len(
        set(glyph_ids) ^ {row["glyph_id"] for row in manual_glyphs}
    ),
    "manual_graphic_id_symmetric_difference": len(
        set(graphic_ids) ^ {row["graphic_id"] for row in manual_graphics}
    ),
    "manual_critical_id_symmetric_difference": len(
        {row["relation_id"] for row in critical}
        ^ {row["relation_id"] for row in manual_critical}
    ),
    "manual_non_pass_rows": sum(
        row.get("decision") != "PASS"
        for rows in (
            manual_glyphs,
            manual_graphics,
            manual_critical,
            manual_semantic,
            manual_hard,
            manual_views,
            manual_typography,
        )
        for row in rows
    ),
    "manual_hard_failure_present_rows": sum(
        row["hard_failure_present"] != "NO" for row in manual_hard
    ),
    "json_parse_errors": json_parse_errors,
    "csv_parse_errors": csv_parse_errors,
    "png_decode_errors": png_decode_errors,
    "pyc_or_cache_paths": sum(
        path.suffix.lower() == ".pyc" or path.name == "__pycache__"
        for path in ROOT.rglob("*")
    ),
}

expected = {
    "visible_glyph_rows": 162,
    "visible_graphic_rows": 18,
    "visible_object_denominator": 180,
    "unique_visible_object_ids": 180,
    "all_unordered_pair_rows": 16110,
    "unique_unordered_pair_rows": 16110,
    "missing_expected_pair_rows": 0,
    "foreign_pair_rows": 0,
    "raw_nonzero_overlap_pairs": 14,
    "raw_overlap_pixel_sum": 258,
    "critical_relation_rows": 41,
    "semantic_text_rows": 11,
    "semantic_text_mismatches": 0,
    "empty_glyph_masks": 0,
    "empty_graphic_masks": 0,
    "manual_glyph_rows": 162,
    "manual_graphic_rows": 18,
    "manual_critical_rows": 41,
    "manual_semantic_rows": 11,
    "manual_hard_gate_rows": 6,
    "manual_view_rows": 36,
    "manual_typography_rows": 7,
    "manual_glyph_id_symmetric_difference": 0,
    "manual_graphic_id_symmetric_difference": 0,
    "manual_critical_id_symmetric_difference": 0,
    "manual_non_pass_rows": 0,
    "manual_hard_failure_present_rows": 0,
    "json_parse_errors": 0,
    "csv_parse_errors": 0,
    "png_decode_errors": 0,
    "pyc_or_cache_paths": 0,
}

for key, wanted in expected.items():
    if checks[key] != wanted:
        errors.append(f"count:{key}:observed={checks[key]}:expected={wanted}")

for row in glyphs:
    if not (ROOT / row["mask_path"]).is_file():
        errors.append(f"missing_glyph_mask:{row['element_id']}:{row['mask_path']}")
for row in graphics:
    if not (ROOT / row["mask_path"]).is_file():
        errors.append(f"missing_graphic_mask:{row['object_id']}:{row['mask_path']}")
for row in critical:
    for field in (
        "native1x_path",
        "nearest8x_path",
        "mask_a_path",
        "mask_b_path",
        "intersection_path",
    ):
        if not (ROOT / row[field]).is_file():
            errors.append(f"missing_critical_artifact:{row['relation_id']}:{field}:{row[field]}")

checks["validation_error_count"] = len(errors)
checks["root_ordinary_file_count"] = sum(path.is_file() for path in ROOT.rglob("*"))
checks["root_directory_count_excluding_root"] = sum(path.is_dir() for path in ROOT.rglob("*"))
checks["combined_non_manifest_sha256"] = hashlib.sha256(
    "".join(
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ROOT.rglob("*"), key=lambda item: item.relative_to(ROOT).as_posix())
        if path.is_file() and path.name not in {"MANIFEST.sha256.csv", "WRITE_STOPPED.json"}
    ).encode("ascii")
).hexdigest().upper()

print(json.dumps({"counts": checks, "errors": errors}, ensure_ascii=False, indent=2))
