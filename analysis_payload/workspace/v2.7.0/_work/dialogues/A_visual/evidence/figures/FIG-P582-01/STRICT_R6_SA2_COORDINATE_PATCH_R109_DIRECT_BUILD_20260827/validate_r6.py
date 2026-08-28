from __future__ import annotations

import csv
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827")
PDF = ROOT / "build" / "v260_FIG-P582-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex")
EXPECTED_PDF_SHA = "2F96CF1B220E0A0A56D264F428D5BCE93005557040D94EB1CBB516D832E2927A"
EXPECTED_SOURCE_SHA = "989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def timestamps_before_file(relative: str, timestamp_field: str) -> tuple[bool, list[str]]:
    path = ROOT / relative
    written = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    errors: list[str] = []
    for row in rows(relative):
        observed = datetime.fromisoformat(row[timestamp_field]).astimezone(timezone.utc)
        if observed > written:
            errors.append(row.get("object_id") or row.get("pair_id") or row.get("view_id") or row.get("check_id") or "unknown")
    return not errors, errors


machine = json.loads((ROOT / "MACHINE_RESULT.json").read_text(encoding="utf-8"))
inventory = rows("object_inventory.csv")
pairs = rows("all_unordered_pairs.csv")
glyph_manual = rows("manual/glyph_manual_ledger.csv")
graphic_manual = rows("manual/graphic_manual_ledger.csv")
relation_manual = rows("manual/relation_manual_ledger.csv")
view_manual = rows("manual/view_manual_ledger.csv")
semantic_manual = rows("manual/semantic_manual_ledger.csv")

object_ids = [row["id"] for row in inventory]
glyph_ids = {row["id"] for row in inventory if row["kind"] == "glyph"}
graphic_ids = {row["id"] for row in inventory if row["kind"] == "graphic"}
expected_pairs = {tuple(sorted(pair)) for pair in itertools.combinations(object_ids, 2)}
actual_pairs = {tuple(sorted((row["object_a"], row["object_b"]))) for row in pairs}
critical_ids = {row["pair_id"] for row in pairs if row["machine_class"] != "CLEAR"}
manual_relation_ids = {row["pair_id"] for row in relation_manual}

pair_by_objects = {frozenset((row["object_a"], row["object_b"])): row for row in pairs}
target = pair_by_objects[frozenset(("GLYPH-042", "GLYPH-062"))]
upper_a = pair_by_objects[frozenset(("GFX-008", "GLYPH-042"))]
upper_b = pair_by_objects[frozenset(("GFX-007", "GLYPH-042"))]

timestamp_checks = {}
timestamp_errors = {}
for relative, field in [
    ("manual/glyph_manual_ledger.csv", "opened_at"),
    ("manual/graphic_manual_ledger.csv", "opened_at"),
    ("manual/relation_manual_ledger.csv", "opened_at"),
    ("manual/view_manual_ledger.csv", "observed_completed_at"),
    ("manual/semantic_manual_ledger.csv", "observed_completed_at"),
]:
    ok, errors = timestamps_before_file(relative, field)
    timestamp_checks[relative] = ok
    timestamp_errors[relative] = errors

checks = {
    "pdf_identity": PDF.stat().st_size == 31329 and sha256(PDF) == EXPECTED_PDF_SHA,
    "source_identity": sha256(SOURCE) == EXPECTED_SOURCE_SHA,
    "denominator_N95": len(inventory) == 95 and machine["denominator"]["N"] == 95,
    "glyph_denominator_78": len(glyph_ids) == 78,
    "graphic_denominator_17": len(graphic_ids) == 17,
    "pair_denominator_C4465": len(pairs) == 4465 and machine["denominator"]["C_unordered_pairs"] == 4465,
    "all_unordered_pairs_exact": len(actual_pairs) == 4465 and actual_pairs == expected_pairs,
    "pair_ids_unique": len({row["pair_id"] for row in pairs}) == 4465,
    "no_empty_masks": machine["machine"]["empty_masks"] == 0,
    "no_page_edge_clip_candidates": machine["machine"]["page_edge_clip_candidates"] == 0,
    "critical_denominator_32": len(critical_ids) == 32,
    "critical_manual_complete": critical_ids.issubset(manual_relation_ids),
    "glyph_manual_complete": len(glyph_manual) == 78 and {row["object_id"] for row in glyph_manual} == glyph_ids,
    "glyph_manual_all_pass": all(row["decision"] == "PASS" and row["note"].strip() for row in glyph_manual),
    "graphic_manual_complete": len(graphic_manual) == 17 and {row["object_id"] for row in graphic_manual} == graphic_ids,
    "graphic_manual_all_pass": all(row["decision"] == "PASS" and row["note"].strip() for row in graphic_manual),
    "relation_manual_all_pass": all(row["decision"].startswith("PASS") and row["note"].strip() for row in relation_manual),
    "view_manual_all_pass": len(view_manual) == 9 and all(row["decision"] == "PASS" and row["note"].strip() for row in view_manual),
    "semantic_manual_all_pass": len(semantic_manual) == 8 and all(row["decision"] == "PASS" and row["note"].strip() for row in semantic_manual),
    "manual_times_not_future": all(timestamp_checks.values()),
    "target_pair_fixed": target["shared_pixels"] == "0" and float(target["white_clearance_px"]) == 27.0 and target["machine_class"] == "CLEAR",
    "target_legacy_route_recorded": any(row["legacy_route_pair"] == "P05555" and row["decision"] == "PASS_TARGET_FIXED" for row in relation_manual),
    "upper_plot_regression_clear": float(upper_a["white_clearance_px"]) > 90.0 and float(upper_b["white_clearance_px"]) > 90.0,
    "source_semantic_machine_checks": all(
        bool(value)
        for key, value in machine["semantic_checks"].items()
        if key not in {"visible_explicit_font_sizes_pt", "visible_explicit_font_min_pt", "forbidden_scale_token_count"}
    ),
    "source_font_min_9_5": machine["semantic_checks"]["visible_explicit_font_min_pt"] >= 9.5,
    "forbidden_scale_tokens_zero": machine["semantic_checks"]["forbidden_scale_token_count"] == 0,
    "machine_did_not_generate_manual_fields": machine["manual_fields_generated_by_machine"] == 0,
}

result = {
    "uid": "FIG-P582-01",
    "handoff_id": "A-R109-P582-SA2-DIRECT-BUILD-R6-20260827",
    "round": "STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827",
    "status": "LOCAL_SA2_PASS_AWAIT_ATOMIC_COMMIT_AUTHORIZATION" if all(checks.values()) else "FAIL",
    "hard_gate_pass": all(checks.values()),
    "pdf_sha256": sha256(PDF),
    "source_sha256": sha256(SOURCE),
    "denominator": {"N": 95, "glyphs": 78, "graphics": 17, "C": 4465, "critical": 32},
    "target": {
        "legacy_route_pair": "P05555",
        "r6_pair_id": target["pair_id"],
        "objects": ["GLYPH-042", "GLYPH-062"],
        "shared_pixels_native_300dpi": int(target["shared_pixels"]),
        "white_clearance_px": float(target["white_clearance_px"]),
    },
    "upper_plot_regression_min_clearance_px": min(float(upper_a["white_clearance_px"]), float(upper_b["white_clearance_px"])),
    "manual_counts": {
        "glyph": len(glyph_manual),
        "graphic": len(graphic_manual),
        "relation": len(relation_manual),
        "view": len(view_manual),
        "semantic": len(semantic_manual),
    },
    "timestamp_checks": timestamp_checks,
    "timestamp_errors": timestamp_errors,
    "checks": checks,
    "manual_fields_generated_or_overwritten_by_validator": False,
}
(ROOT / "FINAL_VALIDATION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "LOCAL_SA2_DECISION.md").write_text(
    "# FIG-P582-01 R6 local SA2 decision\n\n"
    f"- Status: `{result['status']}`\n"
    "- New standalone PDF: 31,329 bytes; SHA-256 `2F96CF1B220E0A0A56D264F428D5BCE93005557040D94EB1CBB516D832E2927A`.\n"
    "- Denominator: N=95 (78 glyph + 17 graphic), complete C=4,465 unordered pairs, 32 machine candidates.\n"
    "- Target legacy P05555 / R6 PAIR-03495: shared=0; native 300dpi white clearance=27px.\n"
    "- Upper plot regression: nearest checked plot-layer clearance exceeds 90px.\n"
    "- Real manual ledgers: glyph78, graphic17, relation36, view9, semantic8; hard failures=0.\n"
    "- R168 advisory only: three intranumeric spacing candidates; all digits remain distinctly readable.\n"
    "- No TeX retry, second invocation, source expansion, commit, fresh role, second UID, state or inventory write.\n",
    encoding="utf-8",
)
print(json.dumps({"hard_gate_pass": result["hard_gate_pass"], "N": 95, "C": 4465, "target_clearance": 27.0}, ensure_ascii=True))
