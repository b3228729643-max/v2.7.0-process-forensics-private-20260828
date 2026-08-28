from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def image_ok(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except Exception:
        return False


glyphs = rows("06_manual/glyph_manual_ledger.csv")
graphics = rows("06_manual/graphic_manual_ledger.csv")
pairs = rows("06_manual/critical_pair_manual_ledger.csv")
views = rows("06_manual/view_manual_ledger.csv")
math_rules = rows("06_manual/math_rule_manual_ledger.csv")
denominator = rows("03_inventory/current_visible_denominator.csv")
all_pairs = rows("05_pairs/all_unordered_pairs.csv")
machine = json.loads((ROOT / "07_machine/machine_gate.json").read_text(encoding="utf-8"))
semantics = json.loads((ROOT / "07_machine/semantic_recomputation.json").read_text(encoding="utf-8"))
freeze = json.loads((ROOT / "03_inventory/denominator_and_pairs_freeze.json").read_text(encoding="utf-8"))
tile_gate = json.loads((ROOT / "07_machine/graphic_8x_tile_gate.json").read_text(encoding="utf-8"))

glyph_ids = [f"T{i:03d}" for i in range(1, 140)]
graphic_ids = [f"G{i:03d}" for i in range(1, 18)]
critical_ids = ["P04848", "P05554", "P05555", "P05668", "P09144", "P09145"]
now = datetime.now(timezone.utc)
manual_paths = sorted((ROOT / "06_manual").glob("*"))
timestamp_errors: list[str] = []
for rel, data in [
    ("06_manual/glyph_manual_ledger.csv", glyphs),
    ("06_manual/graphic_manual_ledger.csv", graphics),
    ("06_manual/critical_pair_manual_ledger.csv", pairs),
    ("06_manual/view_manual_ledger.csv", views),
    ("06_manual/math_rule_manual_ledger.csv", math_rules),
]:
    mtime = datetime.fromtimestamp((ROOT / rel).stat().st_mtime, tz=timezone.utc)
    for index, row in enumerate(data, start=2):
        observed = datetime.fromisoformat(row["observed_at_utc"].replace("Z", "+00:00"))
        if observed > now:
            timestamp_errors.append(f"{rel}:{index}:future_observation")
        if mtime < observed:
            timestamp_errors.append(f"{rel}:{index}:mtime_before_observation")

referenced_images: set[Path] = set()
for row in glyphs:
    referenced_images.add(ROOT / "04_glyphs/sheets" / row["sheet_1x"])
    referenced_images.add(ROOT / "04_glyphs/sheets" / row["sheet_8x"])
for row in graphics:
    referenced_images.add(ROOT / "04_glyphs/sheets" / row["sheet_1x"])
    for tile in row["authoritative_8x_tiles"].split("|"):
        referenced_images.add(ROOT / "04_glyphs/graphic_8x_tiles" / tile)
for row in pairs:
    referenced_images.add(ROOT / "05_pairs/critical" / row["roi_1x"])
    referenced_images.add(ROOT / "05_pairs/critical" / row["roi_8x"])
for row in views:
    referenced_images.add(ROOT / row["file"])

missing_images = [str(path.relative_to(ROOT)) for path in sorted(referenced_images) if not path.is_file()]
bad_images = [str(path.relative_to(ROOT)) for path in sorted(referenced_images) if path.is_file() and not image_ok(path)]
p05555 = next(row for row in pairs if row["pair_id"] == "P05555")

checks = {
    "glyph_row_count_139": len(glyphs) == 139,
    "glyph_ids_complete_unique": [row["object_id"] for row in glyphs] == glyph_ids,
    "glyph_masks_all_pure": all(row["mask_only_pure"] == "TRUE" and row["decision"] == "PASS" for row in glyphs),
    "graphic_row_count_17": len(graphics) == 17,
    "graphic_ids_complete_unique": [row["object_id"] for row in graphics] == graphic_ids,
    "graphic_masks_all_pure": all(row["mask_only_pure"] == "TRUE" and row["decision"] == "PASS" for row in graphics),
    "critical_row_count_6": len(pairs) == 6,
    "critical_ids_complete_unique": [row["pair_id"] for row in pairs] == critical_ids,
    "view_row_count_4": len(views) == 4,
    "math_rule_row_count_1": len(math_rules) == 1,
    "manual_timestamps_valid": not timestamp_errors,
    "all_referenced_images_exist": not missing_images,
    "all_referenced_images_open": not bad_images,
    "denominator_count_156": len(denominator) == 156,
    "pair_count_12090": len(all_pairs) == 12090,
    "pair_formula_exact": len(all_pairs) == len(denominator) * (len(denominator) - 1) // 2,
    "machine_pair_completeness": machine["pair_completeness_met"] is True,
    "machine_masks_complete": machine["empty_mask_count"] == 0 and machine["mask_png_open_failure_count"] == 0,
    "machine_intersection_set_exact": machine["independent_raw_mask_intersection_pairs"] == ["P05555"],
    "p05555_manual_true_overlap": p05555["decision"] == "FAIL_TRUE_ILLEGAL_OVERLAP" and p05555["raw_mask_intersection_px"] == "14",
    "semantic_recomputation_pass": all([
        semantics["sample_coordinates_match"],
        semantics["running_coordinates_match"],
        semantics["trend_labels_match"],
    ]),
    "graphic_8x_tile_coverage": tile_gate["all_native_mask_pixels_covered"] is True and tile_gate["graphic_object_count"] == 17,
    "frozen_denominator_hash_matches": sha256(ROOT / "03_inventory/current_visible_denominator.csv") == freeze["denominator_csv_sha256"].upper(),
    "frozen_pairs_hash_matches": sha256(ROOT / "05_pairs/all_unordered_pairs.csv") == freeze["all_pairs_csv_sha256"].upper(),
    "final_result_fail": "RESULT=FAIL" in (ROOT / "06_manual/final_sa3_result.txt").read_text(encoding="utf-8"),
    "superseded_run_explicitly_excluded": "non-authoritative" in (ROOT / "AUTHORITY_AND_SCOPE.md").read_text(encoding="utf-8"),
}

result = {
    "generated_at_utc": now.isoformat(),
    "manual_fields_generated_by_this_script": False,
    "checks": checks,
    "timestamp_errors": timestamp_errors,
    "missing_images": missing_images,
    "bad_images": bad_images,
    "all_checks_pass": all(checks.values()),
    "sa3_decision": "FAIL",
    "binding_failure": "P05555 T042/T062 true illegal overlap; 14 native 300dpi intersection pixels",
}
(ROOT / "07_machine/final_crosscheck.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False, indent=2))
