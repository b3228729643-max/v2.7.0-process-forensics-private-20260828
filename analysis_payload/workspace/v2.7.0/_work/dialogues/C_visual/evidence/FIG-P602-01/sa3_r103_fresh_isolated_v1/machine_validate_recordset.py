from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_csv(name: str, delimiter: str = ",") -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def unique(values: list[str]) -> bool:
    return len(values) == len(set(values))


objects = read_csv("machine_object_inventory.csv")
glyphs = read_csv("machine_glyph_inventory.csv")
pairs = read_csv("machine_unordered_pairs.csv")
runs = read_csv("machine_text_run_coverage.csv")
drawings = read_csv("machine_drawing_coverage.csv")

manual_objects = read_csv("manual_object_reviewer.tsv", "\t")
manual_glyphs = read_csv("manual_glyph_reviewer.tsv", "\t")
manual_pairs = read_csv("manual_pair_reviewer.tsv", "\t")
manual_critical = read_csv("manual_critical_roi_reviewer.tsv", "\t")
manual_clips = read_csv("manual_clip_reviewer.tsv", "\t")
manual_roles = read_csv("manual_role_peer_reviewer.tsv", "\t")
manual_primitives = read_csv("manual_primitive_reviewer.tsv", "\t")
manual_views = read_csv("manual_view_reviewer.tsv", "\t")
manual_semantics = read_csv("manual_semantic_reviewer.tsv", "\t")
manual_hard = read_csv("manual_hard_gate_reviewer.tsv", "\t")
manual_render_paths = read_csv("manual_render_path_coverage.tsv", "\t")

object_ids = [row["object_id"] for row in objects]
text_object_ids = [row["object_id"] for row in objects if row["object_id"].startswith("T")]
glyph_ids = [row["glyph_id"] for row in glyphs]
pair_keys = [(row["pair_id"], row["object_a"], row["object_b"]) for row in pairs]
manual_pair_keys = [(row["pair_id"], row["object_a"], row["object_b"]) for row in manual_pairs]
critical_ids = [row["pair_id"] for row in pairs if row["critical_machine_flag"] == "True"]
actual_render_paths = sorted(
    path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.png") if path.is_file()
)
primary_view_paths = [row["file"].replace("\\", "/") for row in manual_views]
linked_render_paths = []
for row in manual_render_paths:
    for item in row["exact_render_paths"].split(";"):
        linked_render_paths.append(item.split("#", 1)[0].replace("\\", "/"))
covered_render_paths = sorted(set(primary_view_paths + linked_render_paths))

checks = {
    "object_denominator_33": len(objects) == 33,
    "object_ids_unique": unique(object_ids),
    "manual_object_exact_identity": [row["object_id"] for row in manual_objects] == object_ids,
    "manual_object_notes_unique": unique([row["note"] for row in manual_objects]),
    "glyph_denominator_194": len(glyphs) == 194,
    "glyph_ids_unique": unique(glyph_ids),
    "manual_glyph_exact_identity": [row["glyph_id"] for row in manual_glyphs] == glyph_ids,
    "manual_glyph_notes_unique": unique([row["note"] for row in manual_glyphs]),
    "text_runs_65": len(runs) == 65,
    "all_text_runs_mapped": all(row["disposition"] == "MAPPED_FIGURE_FOREGROUND" for row in runs),
    "all_text_run_parents_valid": all(row["parent_object_id"] in text_object_ids for row in runs),
    "pair_denominator_528": len(pairs) == 528,
    "pair_ids_unique": unique([row["pair_id"] for row in pairs]),
    "manual_pair_exact_identity_and_order": manual_pair_keys == pair_keys,
    "manual_pair_notes_unique": unique([row["note"] for row in manual_pairs]),
    "manual_pair_all_1x": all(row["reviewed_1x"] == "YES" for row in manual_pairs),
    "critical_denominator_37": len(critical_ids) == 37,
    "manual_critical_exact_identity": [row["pair_id"] for row in manual_critical] == critical_ids,
    "manual_critical_all_1x_8x": all(
        row["reviewed_1x"] == "YES" and row["reviewed_8x"] == "YES"
        for row in manual_critical
    ),
    "manual_critical_notes_unique": unique([row["note"] for row in manual_critical]),
    "clip_exact_object_identity": [row["object_id"] for row in manual_clips] == object_ids,
    "clip_boundary_touch_zero": all(row["boundary_touch_px"] == "0" for row in manual_clips),
    "role_exact_text_object_identity": [row["object_id"] for row in manual_roles] == text_object_ids,
    "drawing_denominator_28": len(drawings) == 28,
    "manual_drawing_exact_identity": [row["drawing_index"] for row in manual_primitives]
    == [row["drawing_index"] for row in drawings],
    "primary_view_rows_7": len(manual_views) == 7,
    "render_path_coverage_rows_264": len(manual_render_paths) == 264,
    "actual_render_files_717": len(actual_render_paths) == 717,
    "render_paths_complete_exact": covered_render_paths == actual_render_paths,
    "semantic_rows_10": len(manual_semantics) == 10,
    "hard_gate_rows_19": len(manual_hard) == 19,
}

manual_tables = {
    "objects": manual_objects,
    "glyphs": manual_glyphs,
    "pairs": manual_pairs,
    "critical": manual_critical,
    "clips": manual_clips,
    "roles": manual_roles,
    "primitives": manual_primitives,
    "views": manual_views,
    "semantics": manual_semantics,
    "hard_gates": manual_hard,
}

non_pass = {
    name: [
        row.get("pair_id")
        or row.get("glyph_id")
        or row.get("object_id")
        or row.get("drawing_index")
        or row.get("view_id")
        or row.get("semantic_id")
        or row.get("gate_id")
        or "UNIDENTIFIED"
        for row in table
        if row.get("decision", row.get("manual_decision", "PASS")) != "PASS"
    ]
    for name, table in manual_tables.items()
}

result = {
    "kind": "MACHINE_VALIDATION_OF_MANUAL_RECORDSET",
    "handoff_id": "C-FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1",
    "counts": {
        "objects": len(objects),
        "text_objects": len(text_object_ids),
        "glyphs": len(glyphs),
        "text_runs": len(runs),
        "drawings": len(drawings),
        "pairs": len(pairs),
        "critical_pairs": len(critical_ids),
        "manual_views": len(manual_views),
        "manual_render_path_coverage_rows": len(manual_render_paths),
        "actual_render_files": len(actual_render_paths),
        "covered_unique_render_files": len(covered_render_paths),
        "manual_semantics": len(manual_semantics),
        "manual_hard_gates": len(manual_hard),
    },
    "checks": checks,
    "failed_checks": [name for name, passed in checks.items() if not passed],
    "render_paths_missing_from_manual_coverage": sorted(set(actual_render_paths) - set(covered_render_paths)),
    "render_paths_not_present_on_disk": sorted(set(covered_render_paths) - set(actual_render_paths)),
    "manual_non_pass_ids_by_table": non_pass,
    "manual_non_pass_total": sum(len(items) for items in non_pass.values()),
}

with (ROOT / "machine_manual_recordset_validation.json").open("w", encoding="utf-8", newline="\n") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

print(json.dumps(result, ensure_ascii=False, indent=2))
