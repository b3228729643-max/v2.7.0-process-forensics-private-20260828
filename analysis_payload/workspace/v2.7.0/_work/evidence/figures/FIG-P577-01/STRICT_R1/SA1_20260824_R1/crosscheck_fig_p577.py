#!/usr/bin/env python3
"""Independent terminal cross-check for FIG-P577-01 SA1 strict evidence.

This does not re-score quality gates.  It checks that all CSV/JSON/MD-facing
counts, object IDs, masks and evidence packs are mutually consistent, keeping
pixel-height, D and E as separate columns.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


def load_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def nonempty_mask(path: Path) -> bool:
    if not path.exists():
        return False
    with Image.open(path) as im:
        return im.convert("L").getbbox() is not None


def main() -> int:
    terminal = json.loads((ROOT / "machine_terminal.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
    inventory = manifest["inventory"]
    font = load_csv("after_font_audit.csv")
    pixel = load_csv("after_pixel_measurements.csv")
    glyph = load_csv("glyph_measurements.csv")
    pairs = load_csv("after_overlap_report.csv")
    checks: list[dict[str, object]] = []

    def add(name: str, passed: bool, observed: object, expected: object, detail: str) -> None:
        checks.append({"CHECK": name, "PASS": "PASS" if passed else "FAIL", "OBSERVED": observed, "EXPECTED": expected, "DETAIL": detail})

    ids = [x["id"] for x in inventory]
    add("inventory_unique_ids", len(ids) == len(set(ids)), len(ids), len(set(ids)), "object_manifest IDs are unique")
    raw_missing: list[str] = []
    raw_empty: list[str] = []
    for item in inventory:
        p = ROOT / "masks" / "raw" / f"{item['id']}.png"
        if not p.exists():
            raw_missing.append(item["id"])
        elif item.get("kind") != "BACKGROUND_FILL" and not nonempty_mask(p):
            raw_empty.append(item["id"])
    add("inventory_raw_masks_present", not raw_missing, raw_missing, "[]", "every inventory object has its raw-mask file")
    add("inventory_raw_masks_nonempty", not raw_empty, raw_empty, "[]", "every non-background inventory object has pixels")

    primitive_ids = {x["id"] for x in inventory if x["kind"] == "TEXT_PRIMITIVE"}
    parent_ids = {x["id"] for x in inventory if x["kind"] in {"TEXT", "FORMULA"}}
    graphic_ids = {x["id"] for x in inventory if x["kind"] not in {"TEXT_PRIMITIVE", "TEXT", "FORMULA", "BACKGROUND_FILL"}}
    add("visible_primitive_count", len(primitive_ids) == terminal["final_visible_text_primitives"], len(primitive_ids), terminal["final_visible_text_primitives"], "source-occluded y=0.4 is intentionally not final-visible")
    add("semantic_font_element_count", len(font) == terminal["semantic_font_elements"] == len(parent_ids), f"font={len(font)},parents={len(parent_ids)}", terminal["semantic_font_elements"], "semantic font rows and parent object set agree")
    add("pixel_primitive_count", len(pixel) == len(primitive_ids), len(pixel), len(primitive_ids), "after_pixel covers every final-visible primitive")
    add("glyph_trace_count", len(glyph) == terminal["glyph_traces"], len(glyph), terminal["glyph_traces"], "glyph table count agrees with terminal")
    glyph_ids = [x["GLYPH_ID"] for x in glyph]
    add("glyph_unique_ids", len(glyph_ids) == len(set(glyph_ids)), len(glyph_ids), len(set(glyph_ids)), "glyph IDs are unique")
    bad_glyph_members = sorted({x["ELEMENT_ID"] for x in glyph} - primitive_ids)
    add("glyph_parent_membership", not bad_glyph_members, bad_glyph_members, "[]", "every glyph belongs to a visible primitive")
    glyph_missing = [x["GLYPH_ID"] for x in glyph if not (ROOT / x["RAW_MASK"]).exists()]
    add("glyph_raw_masks_present", not glyph_missing, glyph_missing, "[]", "all glyph raw-mask paths resolve")

    pixel_fail = sum(x["PIXEL_HEIGHT_PASS"] == "FAIL" for x in glyph)
    d_fail = sum(x["D_SAME_SCRIPT_PASS"] == "FAIL" for x in glyph)
    e_fail = sum(x["E_ROLE_RATIO_PASS"] == "FAIL" for x in pixel)
    add("pixel_height_separate_count", pixel_fail == terminal["pixel_height_fail"], pixel_fail, terminal["pixel_height_fail"], "D/E are not included in the pixel-height count")
    add("D_separate_count", d_fail == terminal["same_script_d_fail"], d_fail, terminal["same_script_d_fail"], "D remains a same-role/same-script diagnostic")
    add("E_separate_count", e_fail == terminal["role_e_fail"], e_fail, terminal["role_e_fail"], "E has explicit BASE or N/A, never cross-script")
    invalid_e = [x["ELEMENT_ID"] for x in pixel if x["E_ROLE_RATIO_PASS"] == "N/A" and x["E_BASE_ID"] != "N/A"]
    add("E_na_base_consistency", not invalid_e, invalid_e, "[]", "N/A E rows carry no invented BASE")

    relation = [x for x in pairs if not x["CHECK_ID"].startswith("EDGE_")]
    add("pair_relation_row_count", len(relation) == terminal["pair_relation_rows"] == terminal["expected_relation_rows"], f"actual={len(relation)}", terminal["expected_relation_rows"], "all unordered text-text and text-graphic relations are present")
    relation_ids = [x["CHECK_ID"] for x in relation]
    add("pair_relation_unique_ids", len(relation_ids) == len(set(relation_ids)), len(relation_ids), len(set(relation_ids)), "relation IDs are unique")
    valid_relation_objects = parent_ids | graphic_ids
    bad_relation_refs = [x["CHECK_ID"] for x in relation if x["ELEMENT_A_ID"] not in valid_relation_objects or x["ELEMENT_B_ID"] not in valid_relation_objects]
    add("pair_relation_object_refs", not bad_relation_refs, bad_relation_refs, "[]", "relations refer only to semantic text or non-background graphics")
    pair_fail_rows = [x for x in pairs if x["PASS_FAIL"] == "FAIL"]
    add("pair_fail_count", len(pair_fail_rows) == terminal["pair_fail"], len(pair_fail_rows), terminal["pair_fail"], "pair failure count agrees with terminal")
    package_ids = [x["CHECK_ID"] for x in pairs if x["EVIDENCE_ROI"]]
    add("critical_package_list", package_ids == terminal["critical_or_failed_pair_ids"], package_ids, terminal["critical_or_failed_pair_ids"], "terminal and CSV point to same critical/failing pairs")
    required_pair_files = {"raw.png", "A_raw_mask.png", "B_raw_mask.png", "intersection_raw_mask.png", "overlay.png", "roi_1to1.png", "roi_8x_nearest.png", "focus_raw.png", "focus_A_raw_mask.png", "focus_B_raw_mask.png", "focus_intersection_raw_mask.png", "focus_overlay.png", "focus_roi_1to1.png", "focus_roi_8x_nearest.png", "manifest.json"}
    bad_pair_packs: list[str] = []
    for pair in pairs:
        if pair["EVIDENCE_ROI"]:
            d = ROOT / pair["EVIDENCE_ROI"]
            miss = sorted(name for name in required_pair_files if not (d / name).exists())
            if miss:
                bad_pair_packs.append(f"{pair['CHECK_ID']}:{','.join(miss)}")
    add("critical_pair_packages_complete", not bad_pair_packs, bad_pair_packs, "[]", "raw/A/B/intersection/overlay/1:1/8x and focus set exist")

    fail_glyph_ids = [x["GLYPH_ID"] for x in glyph if x["PIXEL_HEIGHT_PASS"] == "FAIL"]
    add("glyph_failure_list", fail_glyph_ids == terminal["glyph_failure_ids"], len(fail_glyph_ids), len(terminal["glyph_failure_ids"]), "failure IDs agree exactly")
    bad_glyph_packs: list[str] = []
    required_glyph_files = {"raw.png", "raw_mask.png", "roi_1to1.png", "roi_8x_nearest.png", "manifest.json"}
    for gid in fail_glyph_ids:
        d = ROOT / "glyph_evidence" / gid
        miss = sorted(name for name in required_glyph_files if not (d / name).exists())
        if miss:
            bad_glyph_packs.append(f"{gid}:{','.join(miss)}")
    add("glyph_failure_packages_complete", not bad_glyph_packs, bad_glyph_packs, "[]", "all failed glyphs have raw/1:1/8x packages")

    bad_halos: list[str] = []
    for h in terminal["halos"]:
        d = ROOT / "halos" / h["id"]
        need = {"pre_source_vector.svgfrag", "halo_source_vector.svgfrag", "halo_raw_mask.png", "final_visible_raw_mask.png", "manifest.json"}
        miss = sorted(name for name in need if not (d / name).exists())
        if h["halo_raw_pixels"] <= 0 or miss:
            bad_halos.append(f"{h['id']}:{','.join(miss)}")
    add("opaque_halo_triplets_complete", terminal.get("halo_integrity_pass") and not bad_halos, bad_halos, "[]", "real pre-vector/halo-raw/final-visible triplets exist")

    output_json = {
        "figure": "FIG-P577-01",
        "strict_run": "SA1_20260824_R1",
        "machine_integrity_pass": all(x["PASS"] == "PASS" for x in checks),
        "quality_result": "FAIL→SA2",
        "quality_failure_counts": {"pixel_height_fail": pixel_fail, "D_fail": d_fail, "E_fail": e_fail, "pair_fail": len(pair_fail_rows)},
        "checks": checks,
    }
    (ROOT / "machine_crosscheck.json").write_text(json.dumps(output_json, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "machine_crosscheck.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["CHECK", "PASS", "OBSERVED", "EXPECTED", "DETAIL"])
        writer.writeheader()
        writer.writerows(checks)
    lines = ["# FIG-P577-01 SA1 terminal machine cross-check", "", f"- INTEGRITY: `{'PASS' if output_json['machine_integrity_pass'] else 'FAIL'}`", "- QUALITY RESULT: `FAIL→SA2` (quality failure is intentionally distinct from evidence integrity)", f"- Separate gate counts: pixel `{pixel_fail}`, D `{d_fail}`, E `{e_fail}`, relation `{len(pair_fail_rows)}`.", "", "| Check | Status |", "| --- | --- |"]
    lines.extend(f"| {x['CHECK']} | {x['PASS']} |" for x in checks)
    (ROOT / "machine_crosscheck.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"machine_integrity_pass": output_json["machine_integrity_pass"], "checks": len(checks)}, ensure_ascii=False))
    return 0 if output_json["machine_integrity_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
