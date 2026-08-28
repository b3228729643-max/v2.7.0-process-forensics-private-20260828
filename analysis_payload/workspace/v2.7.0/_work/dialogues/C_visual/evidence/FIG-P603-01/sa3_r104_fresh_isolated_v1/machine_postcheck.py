from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
FIGURE_RECT = (250, 2100, 2184, 2871)
STANDALONE_RECT = (454, 2100, 1980, 2738)
PAGE_RECT = (0, 0, 2481, 3508)


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_rect(value: str) -> tuple[int, int, int, int] | None:
    if not value or value == "null":
        return None
    vals = json.loads(value)
    return tuple(int(v) for v in vals)


def margins(rect: tuple[int, int, int, int], container: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    cx0, cy0, cx1, cy1 = container
    return x0 - cx0, y0 - cy0, cx1 - x1, cy1 - y1


def inside(m: tuple[int, int, int, int]) -> bool:
    return min(m) >= 0


def verify_png(path: Path) -> bool:
    with Image.open(path) as image:
        image.verify()
    return True


objects = read_csv("machine_object_inventory.csv")
pairs = read_csv("machine_all_pairs.csv")
glyphs = [r for r in objects if r["object_type"] == "GLYPH"]
graphics = [r for r in objects if r["object_type"] == "GRAPHIC"]

clip_rows: list[dict[str, object]] = []
for row in objects:
    basis = parse_rect(row["ink_bbox_px"]) or parse_rect(row["mask_rect_px"])
    assert basis is not None
    page_m = margins(basis, PAGE_RECT)
    figure_m = margins(basis, FIGURE_RECT)
    standalone_eligible = row["semantic_parent"] != "CAPTION_FIG32_6"
    standalone_m = margins(basis, STANDALONE_RECT) if standalone_eligible else None
    clip_rows.append(
        {
            "object_id": row["object_id"],
            "basis": "ink_bbox_px" if parse_rect(row["ink_bbox_px"]) else "mapped_fill_rect_px",
            "bbox_px": json.dumps(basis, separators=(",", ":")),
            "page_margins_ltrb_px": json.dumps(page_m, separators=(",", ":")),
            "within_page": inside(page_m),
            "figure_margins_ltrb_px": json.dumps(figure_m, separators=(",", ":")),
            "within_figure_crop": inside(figure_m),
            "standalone_eligible": standalone_eligible,
            "standalone_margins_ltrb_px": "" if standalone_m is None else json.dumps(standalone_m, separators=(",", ":")),
            "within_standalone_crop": "N/A" if standalone_m is None else inside(standalone_m),
            "machine_note": "coordinate containment only; no manual clipping decision",
        }
    )

with (ROOT / "machine_clip_inventory.csv").open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(clip_rows[0]))
    writer.writeheader()
    writer.writerows(clip_rows)

expected_pairs = len(objects) * (len(objects) - 1) // 2
actual_keys = {tuple(sorted((r["object_a"], r["object_b"]))) for r in pairs}
expected_keys = set(combinations(sorted(r["object_id"] for r in objects), 2))
critical = [r for r in pairs if r["manual_review_required"] == "True"]

png_sets = {
    "glyph_masks": sorted((ROOT / "glyph_masks").glob("*.png")),
    "glyph_evidence": sorted((ROOT / "glyph_evidence").glob("*.png")),
    "graphic_masks": sorted((ROOT / "graphic_masks").glob("*.png")),
    "graphic_evidence": sorted((ROOT / "graphic_evidence").glob("*.png")),
    "glyph_contact_sheets": sorted((ROOT / "glyph_contact_sheets").glob("*.png")),
    "graphic_contact_sheets": sorted((ROOT / "graphic_contact_sheets").glob("*.png")),
    "critical_pair_evidence": sorted((ROOT / "critical_pair_evidence").glob("*.png")),
    "critical_pair_contact_sheets": sorted((ROOT / "critical_pair_contact_sheets").glob("*.png")),
}
png_openable = {name: sum(1 for p in paths if verify_png(p)) for name, paths in png_sets.items()}

manual_glyph = read_csv("manual_glyph_review.csv")
manual_graphic = read_csv("manual_graphic_review.csv")
manual_pair = read_csv("manual_pair_review.csv")
manual_peer = read_csv("manual_peer_role_review.csv")
manual_view = read_csv("manual_view_review.csv")
manual_math = read_csv("manual_math_rule_review.csv")
manual_source_font = read_csv("manual_source_font_review.csv")
manual_clip = read_csv("manual_clip_boundary_review.csv")
manual_hard_gate = read_csv("manual_hard_gate_review.csv")
after_font = read_csv("after_font_audit.csv")
after_pixel = read_csv("after_pixel_measurements.csv")
after_overlap = read_csv("after_overlap_report.csv")

manual_counts = {
    "manual_glyph_review_rows": len(manual_glyph),
    "manual_graphic_review_rows": len(manual_graphic),
    "manual_pair_review_rows": len(manual_pair),
    "manual_peer_role_review_rows": len(manual_peer),
    "manual_view_review_rows": len(manual_view),
    "manual_math_rule_review_rows": len(manual_math),
    "manual_source_font_review_rows": len(manual_source_font),
    "manual_clip_boundary_review_rows": len(manual_clip),
    "manual_hard_gate_review_rows": len(manual_hard_gate),
}

machine_glyph_by_id = {r["object_id"]: r for r in glyphs}
manual_glyph_by_id = {r["object_id"]: r for r in manual_glyph}
machine_graphic_ids = {r["object_id"] for r in graphics}
manual_graphic_ids = {r["object_id"] for r in manual_graphic}
critical_ids = {r["pair_id"] for r in critical}
manual_pair_ids = {r["pair_id"] for r in manual_pair}

glyph_mapping_exact = (
    len(manual_glyph_by_id) == len(manual_glyph)
    and set(manual_glyph_by_id) == set(machine_glyph_by_id)
    and all(
        manual_glyph_by_id[oid]["char"] == row["char"]
        and manual_glyph_by_id[oid]["codepoint"] == row["codepoint"]
        for oid, row in machine_glyph_by_id.items()
    )
)
graphic_mapping_exact = len(manual_graphic_ids) == len(manual_graphic) and manual_graphic_ids == machine_graphic_ids
critical_mapping_exact = len(manual_pair_ids) == len(manual_pair) and manual_pair_ids == critical_ids

manual_reviewer_rows = manual_glyph + manual_graphic + manual_pair + manual_peer + manual_view + manual_math + manual_source_font + manual_clip + manual_hard_gate
manual_reviewer_complete = all(r.get("reviewer") == "SA3" for r in manual_reviewer_rows)
manual_glyph_fields_complete = all(
    r["native_viewed"] == "YES"
    and r["overlay_complete"] == "YES"
    and r["mask_only_pure"] == "YES"
    and r["missing_stroke_px"] == "0"
    and r["foreign_pixel_px"] == "0"
    and r["codepoint_correct"] == "YES"
    and r["readable"] == "YES"
    and r["clip"] == "NO"
    and r["hard_font_issue"] == "NO"
    and r["decision"] == "PASS"
    and bool(r["note"].strip())
    for r in manual_glyph
)
manual_pair_fields_complete = all(
    r["native_1x_viewed"] == "YES"
    and r["zoom_8x_viewed"] == "YES"
    and r["illegal_overlap"] == "NO"
    and r["decision"] == "PASS"
    and bool(r["note"].strip())
    for r in manual_pair
)

top_level_png_names = [
    "full_page_200dpi.png",
    "full_page_300dpi.png",
    "figure_crop_300dpi.png",
    "standalone_300dpi.png",
    "grayscale_300dpi.png",
    "standalone_grayscale_300dpi.png",
    "after_text_measurement_overlay_300dpi.png",
]
top_level_png_openable = all(verify_png(ROOT / name) for name in top_level_png_names)
inventory_references_exist = all((ROOT / r["mask_path"]).is_file() and (ROOT / r["evidence_path"]).is_file() for r in objects)
critical_references_exist = all((ROOT / r["evidence_path"]).is_file() for r in critical)
safe_filenames = [r["safe_filename"] for r in objects]
safe_filenames_unique_portable = len(set(safe_filenames)) == len(safe_filenames) and all(":" not in name and "/" not in name and "\\" not in name for name in safe_filenames)

with (ROOT / "RESULT_CARD.json").open("r", encoding="utf-8") as f:
    result_card = json.load(f)
pixel_metrics = {r["metric"]: r["value"] for r in after_pixel}
result_card_consistent = (
    result_card["handoff_id"] == "C-FIG-P603-01-R104-SA3-FRESH-ISOLATED-V1"
    and result_card["decision"] == "PASS"
    and result_card["authority"] == "C_LOCAL_PASS_ONLY"
    and result_card["next_state"] == "WAIT_MAINLINE"
    and result_card["global_pass_claimed"] is False
    and result_card["object_count"] == len(objects)
    and result_card["glyph_count"] == len(glyphs)
    and result_card["graphic_count"] == len(graphics)
    and result_card["unordered_pair_count"] == len(pairs)
    and result_card["critical_pair_count"] == len(critical)
    and result_card["raw_overlap_pair_count"] == sum(1 for r in pairs if int(r["overlap_px"]) > 0)
    and result_card["raw_overlap_candidate_pixel_count"] == sum(int(r["overlap_px"]) for r in pairs)
    and result_card["overlap_pixel_count"] == 0
    and result_card["clip_pixel_count"] == 0
    and all(result_card["hard_gates"].values())
)
after_summary_consistent = (
    pixel_metrics.get("OBJECT_COUNT") == "165"
    and pixel_metrics.get("GLYPH_COUNT") == "150"
    and pixel_metrics.get("GRAPHIC_OBJECT_COUNT") == "15"
    and pixel_metrics.get("UNORDERED_PAIR_COUNT") == "13530"
    and pixel_metrics.get("RAW_OVERLAP_CANDIDATE_PIXEL_COUNT") == "259"
    and pixel_metrics.get("OVERLAP_PIXEL_COUNT") == "0"
    and pixel_metrics.get("CLIP_PIXEL_COUNT") == "0"
    and len(after_font) == 9
    and all(r["hard_failure_count"] == "0" for r in after_font)
    and len(after_overlap) == 10
    and all(r["illegal_overlap_pixels"] == "0" and r["status"] == "PASS" for r in after_overlap)
)
required_reports_exist = all((ROOT / name).is_file() for name in [
    "REPORT.md",
    "RESULT_CARD.md",
    "RESULT_CARD.json",
    "after_visual_acceptance.md",
    "after_font_audit.csv",
    "after_pixel_measurements.csv",
    "after_overlap_report.csv",
])

cache_entries = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.name == "__pycache__" or p.suffix.lower() in {".pyc", ".pyo"}]

checks = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "machine_only_scope": "counts, identity coverage, coordinate containment, and PNG decodability; no manual reviewer/boolean/decision/note fields generated or overwritten",
    "object_count": len(objects),
    "glyph_count": len(glyphs),
    "graphic_count": len(graphics),
    "expected_unordered_pair_count": expected_pairs,
    "actual_pair_row_count": len(pairs),
    "unique_pair_key_count": len(actual_keys),
    "all_c_n_2_pairs_present": actual_keys == expected_keys,
    "manual_required_critical_pair_count": len(critical),
    "raw_overlap_pair_count": sum(1 for r in pairs if int(r["overlap_px"]) > 0),
    "raw_overlap_candidate_pixel_sum": sum(int(r["overlap_px"]) for r in pairs),
    "all_objects_within_page": all(r["within_page"] for r in clip_rows),
    "all_objects_within_figure_crop": all(r["within_figure_crop"] for r in clip_rows),
    "all_standalone_eligible_objects_within_standalone_crop": all(r["within_standalone_crop"] is True for r in clip_rows if r["standalone_eligible"]),
    "minimum_figure_crop_edge_margin_px": min(min(json.loads(r["figure_margins_ltrb_px"])) for r in clip_rows),
    "minimum_standalone_crop_edge_margin_px": min(min(json.loads(r["standalone_margins_ltrb_px"])) for r in clip_rows if r["standalone_eligible"]),
    "png_counts": {name: len(paths) for name, paths in png_sets.items()},
    "png_openable_counts": png_openable,
    "all_enumerated_pngs_openable": all(len(png_sets[k]) == png_openable[k] for k in png_sets),
    "top_level_required_pngs_openable": top_level_png_openable,
    "inventory_references_exist": inventory_references_exist,
    "critical_references_exist": critical_references_exist,
    "safe_filenames_unique_portable": safe_filenames_unique_portable,
    "glyph_manual_mapping_exact": glyph_mapping_exact,
    "graphic_manual_mapping_exact": graphic_mapping_exact,
    "critical_pair_manual_mapping_exact": critical_mapping_exact,
    "manual_reviewer_complete": manual_reviewer_complete,
    "manual_glyph_fields_complete": manual_glyph_fields_complete,
    "manual_pair_fields_complete": manual_pair_fields_complete,
    "result_card_consistent": result_card_consistent,
    "after_summary_consistent": after_summary_consistent,
    "required_reports_exist": required_reports_exist,
    **manual_counts,
    "cache_or_pyc_entries": cache_entries,
    "cache_or_pyc_count": len(cache_entries),
}

expected = {
    "object_count": 165,
    "glyph_count": 150,
    "graphic_count": 15,
    "expected_unordered_pair_count": 13530,
    "actual_pair_row_count": 13530,
    "unique_pair_key_count": 13530,
    "manual_required_critical_pair_count": 53,
    "raw_overlap_pair_count": 17,
    "raw_overlap_candidate_pixel_sum": 259,
    "manual_glyph_review_rows": 150,
    "manual_graphic_review_rows": 15,
    "manual_pair_review_rows": 53,
    "manual_peer_role_review_rows": 32,
    "manual_view_review_rows": 5,
    "manual_math_rule_review_rows": 3,
    "manual_source_font_review_rows": 6,
    "manual_clip_boundary_review_rows": 4,
    "manual_hard_gate_review_rows": 12,
    "cache_or_pyc_count": 0,
}
checks["expected_scalar_checks"] = {key: checks[key] == value for key, value in expected.items()}
checks["terminal_machine_checks_pass"] = (
    all(checks["expected_scalar_checks"].values())
    and checks["all_c_n_2_pairs_present"]
    and checks["all_objects_within_page"]
    and checks["all_objects_within_figure_crop"]
    and checks["all_standalone_eligible_objects_within_standalone_crop"]
    and checks["all_enumerated_pngs_openable"]
    and checks["top_level_required_pngs_openable"]
    and checks["inventory_references_exist"]
    and checks["critical_references_exist"]
    and checks["safe_filenames_unique_portable"]
    and checks["glyph_manual_mapping_exact"]
    and checks["graphic_manual_mapping_exact"]
    and checks["critical_pair_manual_mapping_exact"]
    and checks["manual_reviewer_complete"]
    and checks["manual_glyph_fields_complete"]
    and checks["manual_pair_fields_complete"]
    and checks["result_card_consistent"]
    and checks["after_summary_consistent"]
    and checks["required_reports_exist"]
)

with (ROOT / "machine_terminal_check.json").open("w", encoding="utf-8") as f:
    json.dump(checks, f, ensure_ascii=False, indent=2)
    f.write("\n")

with (ROOT / "machine_terminal_check.csv").open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["metric", "value"])
    for key, value in checks.items():
        writer.writerow([key, json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value])

print(json.dumps(checks, ensure_ascii=False, indent=2))
