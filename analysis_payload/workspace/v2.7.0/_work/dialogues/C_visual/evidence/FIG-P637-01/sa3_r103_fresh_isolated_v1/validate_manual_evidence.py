from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MACHINE = ROOT / "machine"
MANUAL = ROOT / "manual"
OUT = MACHINE / "manual_crosscheck.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def duplicate_ids(rows: list[dict[str, str]], field: str) -> list[str]:
    counts = Counter(row[field] for row in rows)
    return sorted(key for key, value in counts.items() if value != 1)


glyph_machine = read_csv(MACHINE / "glyph_inventory.csv")
glyph_manual = read_csv(MANUAL / "glyph_review.csv")
sheet_index = {row["glyph_id"]: row for row in read_csv(MACHINE / "glyph_contact_sheet_index.csv")}
pair_machine = read_csv(MACHINE / "all_unordered_pairs.csv")
critical_machine = read_csv(MACHINE / "critical_pair_inventory.csv")
critical_manual = read_csv(MANUAL / "critical_pair_review.csv")
clip_machine = read_csv(MACHINE / "clip_inventory.csv")
clip_manual = read_csv(MANUAL / "object_clip_review.csv")
graphic_machine = read_csv(MACHINE / "graphic_inventory.csv")
graphic_manual = read_csv(MANUAL / "graphic_review.csv")
render_machine = read_csv(MACHINE / "render_inventory.csv")
render_manual = read_csv(MANUAL / "render_view_review.csv")
parent_machine = read_csv(MACHINE / "text_parent_inventory.csv")
parent_manual = read_csv(MANUAL / "text_parent_review.csv")

g_m = {row["glyph_id"]: row for row in glyph_machine}
g_u = {row["glyph_id"]: row for row in glyph_manual}
p_m = {row["pair_id"]: row for row in critical_machine}
p_u = {row["pair_id"]: row for row in critical_manual}
c_m = {row["object_id"]: row for row in clip_machine}
c_u = {row["object_id"]: row for row in clip_manual}
d_m = {row["object_id"]: row for row in graphic_machine}
d_u = {row["object_id"]: row for row in graphic_manual}
v_m = {row["view_id"]: row for row in render_machine}
v_u = {row["view_id"]: row for row in render_manual}
t_m = {row["parent_id"]: row for row in parent_machine}
t_u = {row["parent_id"]: row for row in parent_manual}

glyph_field_mismatches: list[str] = []
for gid in sorted(set(g_m) & set(g_u)):
    machine = g_m[gid]
    manual = g_u[gid]
    idx = sheet_index[gid]
    expected_cell = f"{int(idx['sheet'].split('_')[-1].split('.')[0]):03d}-{idx['cell']}"
    expected = (machine["char"], machine["codepoint"], machine["parent_id"], expected_cell)
    observed = (manual["character"], manual["codepoint"], manual["parent_id"], manual["sheet_cell"])
    if expected != observed:
        glyph_field_mismatches.append(gid)

pair_field_mismatches: list[str] = []
for pid in sorted(set(p_m) & set(p_u)):
    expected = (p_m[pid]["object_a"], p_m[pid]["object_b"], p_m[pid]["raw_mask_intersection_px"])
    observed = (p_u[pid]["object_a"], p_u[pid]["object_b"], p_u[pid]["raw_intersection_px"])
    if expected != observed:
        pair_field_mismatches.append(pid)

clip_field_mismatches: list[str] = []
for oid in sorted(set(c_m) & set(c_u)):
    expected = (c_m[oid]["container"], c_m[oid]["min_bbox_to_crop_edge_px"], c_m[oid]["touches_crop_edge"].lower())
    observed = (c_u[oid]["container"], c_u[oid]["min_clearance_px"], c_u[oid]["touches_edge"].lower())
    if expected != observed:
        clip_field_mismatches.append(oid)

summary = json.loads((MACHINE / "machine_summary.json").read_text(encoding="utf-8"))
n = int(summary["foreground_object_count_n"])

result = {
    "identity": {
        "uid": "FIG-P637-01",
        "release": "R103",
        "role": "SA3_FRESH_ISOLATED",
        "handoff_id": "C-FIG-P637-01-R103-SA3-FRESH-ISOLATED-V1",
        "machine_script_authorship_scope": "read and cross-check only; no manual field generated or overwritten",
    },
    "machine_denominators": {
        "glyph_rows": len(glyph_machine),
        "foreground_graphic_rows": sum(row["pair_denominator_included"].lower() == "true" for row in graphic_machine),
        "excluded_background_graphic_rows": sum(row["pair_denominator_included"].lower() != "true" for row in graphic_machine),
        "foreground_object_n": n,
        "unordered_pair_formula": f"C({n},2)",
        "unordered_pair_expected": n * (n - 1) // 2,
        "unordered_pair_rows": len(pair_machine),
        "unordered_pair_unique_ids": len({row["pair_id"] for row in pair_machine}),
        "critical_pair_rows": len(critical_machine),
    },
    "manual_ledger_counts": {
        "glyph_review": len(glyph_manual),
        "critical_pair_review": len(critical_manual),
        "object_clip_review": len(clip_manual),
        "graphic_review": len(graphic_manual),
        "render_view_review": len(render_manual),
        "text_parent_review": len(parent_manual),
        "peer_role_review": len(read_csv(MANUAL / "peer_role_review.csv")),
        "semantic_content_review": len(read_csv(MANUAL / "semantic_content_review.csv")),
        "hard_gate_review": len(read_csv(MANUAL / "hard_gate_review.csv")),
    },
    "id_set_differences": {
        "glyph_missing_manual": sorted(set(g_m) - set(g_u)),
        "glyph_extra_manual": sorted(set(g_u) - set(g_m)),
        "critical_pair_missing_manual": sorted(set(p_m) - set(p_u)),
        "critical_pair_extra_manual": sorted(set(p_u) - set(p_m)),
        "clip_missing_manual": sorted(set(c_m) - set(c_u)),
        "clip_extra_manual": sorted(set(c_u) - set(c_m)),
        "graphic_missing_manual": sorted(set(d_m) - set(d_u)),
        "graphic_extra_manual": sorted(set(d_u) - set(d_m)),
        "view_missing_manual": sorted(set(v_m) - set(v_u)),
        "view_extra_manual": sorted(set(v_u) - set(v_m)),
        "text_parent_missing_manual": sorted(set(t_m) - set(t_u)),
        "text_parent_extra_manual": sorted(set(t_u) - set(t_m)),
    },
    "duplicate_id_rows": {
        "glyph": duplicate_ids(glyph_manual, "glyph_id"),
        "critical_pair": duplicate_ids(critical_manual, "pair_id"),
        "clip": duplicate_ids(clip_manual, "object_id"),
        "graphic": duplicate_ids(graphic_manual, "object_id"),
        "view": duplicate_ids(render_manual, "view_id"),
        "text_parent": duplicate_ids(parent_manual, "parent_id"),
    },
    "field_mismatch_ids": {
        "glyph_char_codepoint_parent_sheet_cell": glyph_field_mismatches,
        "critical_pair_objects_and_intersection": pair_field_mismatches,
        "clip_container_clearance_and_edge_touch": clip_field_mismatches,
    },
    "observed_manual_value_counts": {
        "glyph_decision": dict(Counter(row["decision"] for row in glyph_manual)),
        "pair_decision": dict(Counter(row["decision"] for row in critical_manual)),
        "pair_true_collision": dict(Counter(row["true_collision"] for row in critical_manual)),
        "clip_decision": dict(Counter(row["decision"] for row in clip_manual)),
        "render_decision": dict(Counter(row["decision"] for row in render_manual)),
        "parent_r168_hard_decision": dict(Counter(row["r168_hard_decision"] for row in parent_manual)),
    },
    "nonempty_note_counts": {
        "glyph": sum(bool(row["note"].strip()) for row in glyph_manual),
        "critical_pair": sum(bool(row["note"].strip()) for row in critical_manual),
        "clip": sum(bool(row["note"].strip()) for row in clip_manual),
    },
    "referenced_file_counts": {
        "glyph_cards_existing": sum(Path(row["card_path"]).is_file() for row in glyph_machine),
        "graphic_cards_existing": sum((ROOT / "cards" / "graphic" / f"{row['object_id']}_card_1x.png").is_file() for row in graphic_machine),
        "render_views_existing": sum(Path(row["path"]).is_file() for row in render_machine),
        "critical_pair_cards_8x_existing": sum((ROOT / "pairs" / row["pair_id"] / "card_8x_nearest.png").is_file() for row in critical_machine),
    },
}

OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
