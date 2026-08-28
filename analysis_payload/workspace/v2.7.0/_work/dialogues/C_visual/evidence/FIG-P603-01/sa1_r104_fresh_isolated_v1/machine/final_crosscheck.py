"""Final machine-only consistency check for the sealed SA1 package.

This script validates inventories, denominators, file presence/image readability,
and already-authored manual-ledger completeness. It never creates, fills, or
changes reviewer booleans, decisions, or notes.
"""
from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
MACHINE = ROOT / "machine"
MANUAL = ROOT / "manual"


def read_csv(name: str) -> list[dict[str, str]]:
    with (MACHINE / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def unique(rows: list[dict], key: str) -> bool:
    values = [row[key] for row in rows]
    return len(values) == len(set(values))


def image_ok(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            return im.width > 0 and im.height > 0
    except Exception:
        return False


summary = json.loads((MACHINE / "machine_summary.json").read_text(encoding="utf-8"))
drawing = json.loads((MACHINE / "drawing_coverage_machine.json").read_text(encoding="utf-8"))
glyphs = read_csv("glyph_inventory_machine.csv")
objects = read_csv("object_inventory_machine.csv")
pairs = read_csv("pair_inventory_machine.csv")
clips = read_csv("clip_inventory_machine.csv")

glyph_manual = read_jsonl(MANUAL / "glyph_reviewer_ledger.jsonl")
object_manual = read_jsonl(MANUAL / "object_reviewer_ledger.jsonl")
pair_manual = read_jsonl(MANUAL / "pair_reviewer_ledger.jsonl")
view_manual = read_jsonl(MANUAL / "view_reviewer_ledger.jsonl")
role_manual = read_jsonl(MANUAL / "role_reviewer_ledger.jsonl")
sem_manual = read_jsonl(MANUAL / "content_semantics_reviewer_ledger.jsonl")
gate_manual = read_jsonl(MANUAL / "hard_gate_ledger.jsonl")

glyph_ids = [row["glyph_id"] for row in glyphs]
object_ids = [row["object_id"] for row in objects]
pair_ids = [row["pair_id"] for row in pairs]
critical_ids = [row["pair_id"] for row in pairs if row["critical_le_12px"] == "True"]
overlap_ids = [row["pair_id"] for row in pairs if int(row["overlap_pixel_count"]) > 0]

expected_pairs = {
    frozenset((a, b)) for a, b in itertools.combinations(object_ids, 2)
}
actual_pairs = {
    frozenset((row["object_a"], row["object_b"])) for row in pairs
}

glyph_assets = []
for row in glyphs:
    safe = row["safe_filename"]
    glyph_assets.extend([
        ROOT / "masks" / "glyph" / f"{safe}.png",
        ROOT / "contact" / "glyph_cards" / f"{safe}.png",
    ])
glyph_assets.extend(sorted((ROOT / "contact" / "glyph_sheets").glob("glyph_contact_sheet_*.png")))

object_assets = [ROOT / "masks" / "object" / f"{oid}.png" for oid in object_ids]
critical_assets = []
for pid in critical_ids:
    critical_assets.append(ROOT / "pairs" / f"{pid}_critical_card.png")
    critical_assets.extend(
        ROOT / "pairs" / pid / name
        for name in [
            "critical_tight_1x.png",
            "critical_tight_8x_nearest.png",
            "critical_tight_overlay_1x.png",
            "critical_tight_overlay_8x_nearest.png",
            "intersection.png",
            "mask_A.png",
            "mask_B.png",
            "overlay.png",
            "roi_1x.png",
            "roi_8x_nearest.png",
        ]
    )
critical_assets.extend(sorted((ROOT / "pairs").glob("critical_pair_contact_sheet_*.png")))
critical_assets.extend(sorted((ROOT / "contact" / "math_rules").glob("*.png")))

render_assets = [
    ROOT / "render" / name
    for name in [
        "full_page_200dpi.png",
        "full_page_300dpi.png",
        "figure_crop_300dpi.png",
        "standalone_300dpi.png",
        "grayscale_300dpi.png",
        "text_and_object_overlay_300dpi.png",
    ]
]

view_paths = [ROOT / row["path"] for row in view_manual if row["native_or_text"] != "TEXT_SOURCE"]
sem_paths = [ROOT / rel for row in sem_manual for rel in row["evidence"] if not rel.startswith("whitelisted ")]

checks = {
    "pdf_identity_exact": summary["physical_page"] == 655 and summary["printed_page"] == 642,
    "glyph_denominator_150": len(glyphs) == summary["glyph_count"] == 150,
    "glyph_machine_ids_unique": len(glyph_ids) == len(set(glyph_ids)),
    "glyph_masks_nonempty_machine": all(row["mask_nonempty"] == "True" for row in glyphs),
    "glyph_manual_exact_ids": unique(glyph_manual, "glyph_id") and {row["glyph_id"] for row in glyph_manual} == set(glyph_ids),
    "glyph_manual_pixel_integrity": all(
        row["original_match"] is True
        and row["overlay_complete"] is True
        and row["mask_only_pure"] is True
        and row["missing_stroke_px"] == 0
        and row["foreign_pixel_px"] == 0
        for row in glyph_manual
    ),
    "object_denominator_24": len(objects) == summary["foreground_object_count"] == 24,
    "object_split_11_13": sum(row["kind"] == "TEXT" for row in objects) == 11 and sum(row["kind"] == "GRAPHIC" for row in objects) == 13,
    "object_machine_ids_unique": len(object_ids) == len(set(object_ids)),
    "object_masks_nonempty_machine": all(row["mask_nonempty"] == "True" for row in objects),
    "object_manual_exact_ids": unique(object_manual, "object_id") and {row["object_id"] for row in object_manual} == set(object_ids),
    "object_manual_integrity": all(
        row["content_correct"] is True
        and row["mask_complete"] is True
        and row["mask_pure"] is True
        and row["readable"] is True
        and row["clipped"] is False
        for row in object_manual
    ),
    "pair_denominator_c24_2": len(pairs) == summary["pair_count"] == summary["expected_pair_count"] == 276,
    "pair_machine_ids_unique": len(pair_ids) == len(set(pair_ids)),
    "pair_universe_exact": len(actual_pairs) == len(expected_pairs) and actual_pairs == expected_pairs,
    "pair_manual_exact_ids": unique(pair_manual, "pair_id") and {row["pair_id"] for row in pair_manual} == set(pair_ids),
    "pair_manual_zero_illegal_overlap": all(row["illegal_overlap_px"] == 0 for row in pair_manual),
    "pair_manual_no_fail_or_pending": all("FAIL" not in row["manual_decision"] and "PENDING" not in row["manual_decision"] for row in pair_manual),
    "critical_pair_count_23": len(critical_ids) == summary["critical_pair_count_le_12px_or_overlap"] == 23,
    "critical_pair_ids_exact": critical_ids == summary["critical_pair_ids"],
    "machine_overlap_count_11": len(overlap_ids) == summary["machine_pair_overlap_present_count"] == 11,
    "machine_below_clearance_zero": summary["machine_pair_below_clearance_count"] == 0 and all(row["machine_gate"] != "BELOW_REQUIRED_CLEARANCE" for row in pairs),
    "clip_denominator_24": len(clips) == 24 and {row["object_id"] for row in clips} == set(object_ids),
    "clip_zero": summary["clip_pixel_count"] == 0 and all(int(row["clip_pixel_count"]) == 0 and row["inside_crop"] == "True" for row in clips),
    "minimum_crop_edge_clearance_18": min(int(row["minimum_crop_edge_clearance_px"]) for row in clips) == 18,
    "drawing_coverage_complete": drawing["uncovered_indices"] == [] and drawing["covered_or_excluded_indices"] == list(range(drawing["page_drawing_count"])),
    "role_manual_11_unique": len(role_manual) == 11 and unique(role_manual, "element_id") and {row["element_id"] for row in role_manual} == set(object_ids[:11]),
    "role_r168_readability": all(row["E_rendered_size"] == "PASS_R168_READABLE" and row["visual_harmony"] is True for row in role_manual),
    "semantic_manual_9_unique_pass": len(sem_manual) == 9 and unique(sem_manual, "check_id") and all(row["pass"] is True for row in sem_manual),
    "hard_gate_manual_13_unique_pass": len(gate_manual) == 13 and unique(gate_manual, "gate_id") and all(row["hard_pass"] is True for row in gate_manual),
    "view_manual_28_unique_opened": len(view_manual) == 28 and unique(view_manual, "view_id") and all(row["opened"] is True for row in view_manual),
    "glyph_assets_count": len(glyph_assets) == 315,
    "object_assets_count": len(object_assets) == 24,
    "critical_assets_count": len(critical_assets) == 260,
    "all_glyph_assets_openable": all(image_ok(path) for path in glyph_assets),
    "all_object_assets_openable": all(image_ok(path) for path in object_assets),
    "all_critical_assets_openable": all(image_ok(path) for path in critical_assets),
    "all_render_assets_openable": all(image_ok(path) for path in render_assets),
    "all_manual_view_paths_exist": all(path.is_file() for path in view_paths),
    "all_semantic_internal_paths_exist": all(path.is_file() for path in sem_paths),
    "report_result_consistent": "SA1_RESULT=PASS" in (ROOT / "report" / "SA1_REPORT.md").read_text(encoding="utf-8") and "Result: `SA1_PASS`" in (ROOT / "report" / "SA1_RESULT_CARD.md").read_text(encoding="utf-8"),
    "no_global_or_c_local_pass_claim": "`C_LOCAL_PASS=NOT_CLAIMED`" in (ROOT / "report" / "SA1_REPORT.md").read_text(encoding="utf-8") and "`GLOBAL_PASS=NOT_CLAIMED`" in (ROOT / "report" / "SA1_REPORT.md").read_text(encoding="utf-8"),
}

failed = [name for name, value in checks.items() if not value]
result = {
    "script_scope": "machine consistency verification only; no reviewer boolean, decision, or note generation",
    "root": str(ROOT),
    "counts": {
        "glyphs": len(glyphs),
        "objects": len(objects),
        "pairs": len(pairs),
        "critical_pairs": len(critical_ids),
        "machine_overlap_pairs": len(overlap_ids),
        "manual_views": len(view_manual),
        "manual_roles": len(role_manual),
        "manual_semantic_checks": len(sem_manual),
        "manual_hard_gates": len(gate_manual),
        "image_assets_verified": len(set(glyph_assets + object_assets + critical_assets + render_assets)),
    },
    "checks": checks,
    "failed_checks": failed,
    "all_checks_pass": not failed,
}

(MACHINE / "final_crosscheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = [
    "FIG-P603-01 R104 fresh isolated SA1 final machine cross-check",
    f"all_checks_pass={str(not failed).lower()}",
    f"check_count={len(checks)}",
    f"failed_check_count={len(failed)}",
    f"failed_checks={','.join(failed) if failed else 'NONE'}",
    "scope=machine consistency verification only; no reviewer boolean/decision/note generation",
]
(MACHINE / "final_crosscheck.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

if failed:
    raise SystemExit("Final cross-check failed: " + ", ".join(failed))
print(json.dumps(result, ensure_ascii=False, indent=2))
