"""Last evidence validation and terminal issue; does not write a manifest/stop."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P608-01\STRICT_R1_SA1_REQUAL_R97_20260824")
REVIEWER = "SA1_R1_20260824"


def load_csv(name):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest().upper()


def check(ok, message):
    if not ok:
        raise RuntimeError(message)


def no_pending(rows, label):
    for r in rows:
        if any("PENDING" in str(v) for v in r.values()):
            raise RuntimeError(f"unresolved PENDING value in {label}: {r}")


def main():
    summary = json.loads((OUT / "preliminary_machine_summary.json").read_text(encoding="utf-8"))
    identity = summary["identity"]
    glyph = load_csv("glyph_ledger.csv")
    pixel = load_csv("after_pixel_measurements.csv")
    font = load_csv("after_font_audit.csv")
    manual_glyph = load_csv("manual_glyph_review.csv")
    pairs = load_csv("after_overlap_report.csv")
    manual_pairs = load_csv("manual_pair_review.csv")
    manual_intent = load_csv("manual_intended_contact_review.csv")
    rules = load_csv("math_rule_ledger.csv")
    low = load_csv("low_profile_calibration.csv")
    relations = load_csv("intentional_data_relation_review.csv")
    for rows, name in ((glyph, "glyph"), (pixel, "pixel"), (font, "font"), (manual_glyph, "manual_glyph"), (manual_pairs, "manual_pair"), (manual_intent, "manual_intent"), (rules, "math_rule"), (low, "low_profile"), (relations, "relations")):
        no_pending(rows, name)

    check(len(glyph) == len(pixel) == len(font) == len(manual_glyph) == 114, "glyph ledgers not 114")
    check(len(pairs) == 5151 and summary["counts"]["expected_unordered_pairs"] == 5151, "pair denominator mismatch")
    check(len(manual_pairs) == 110 and len(manual_intent) == 93 and len(relations) == 5, "manual pair/intention denominator")
    check(len(rules) == 2 and [r["rule_id"] for r in rules] == ["R001", "R002"], "math-rule denominator")
    check(len(low) == 15 and all(r["status"] == "PASS_REFERENCE_H_AND_AREA" for r in low), "low-profile calibration")
    check(summary["counts"]["all_objects"] == 102 and summary["counts"]["text_objects"] == 36 and summary["counts"]["graphic_objects"] == 66, "object denominator")
    check(summary["hard_gate_counts"] == {"font_size_fail": 0, "pixel_fail": 4, "purity_fail": 1, "unwhitelisted_pair_fail": 3}, "hard-gate counts")

    glyph_fail = [r["glyph_id"] for r in glyph if r["decision"].startswith("FAIL_")]
    pair_fail = [r["pair_id"] for r in manual_pairs if r["manual_decision"].startswith("FAIL_")]
    check(glyph_fail == ["G008", "G019", "G027", "G058", "G063"], "glyph failure identity")
    check(pair_fail == ["P2311", "P2315", "P3071"], "pair failure identity")

    # Every cited card/reference must exist inside the dedicated evidence root.
    refs = []
    refs += [r["card"] for r in glyph]
    refs += [r["evidence_card"] for r in pairs if r.get("evidence_card")]
    for r in low:
        refs += [r["calibration_source"], r["calibration_native"]]
        refs += list(json.loads(r["calibration_cards"]).values())
    critical = json.loads((OUT / "critical_barX_vs_upper_axis.json").read_text(encoding="utf-8"))
    refs += list(critical["files"].values())
    refs += ["full_page_200dpi.png", "figure_crop_300dpi.png", "figure_crop_300dpi_8x_nearest.png", "standalone_300dpi.png", "grayscale_300dpi.png"]
    missing = [r for r in refs if not (OUT / r).is_file()]
    check(not missing, f"missing referenced evidence: {missing}")
    cleanup = (OUT / "CLEANUP_STALE_SELF_GENERATED.md").read_text(encoding="utf-8")
    check("Listed targets still present: 0" in cleanup and "Missing current-ledger references: 0" in cleanup and "Remaining stale candidates in the four controlled generated folders: 0" in cleanup, "cleanup verification not closed")
    ads = json.loads((OUT / "PACKAGE_ZERO_EMPTY_ADS_CHECK.json").read_text(encoding="utf-8"))
    check(ads["status"] == "PASS_ZERO_EMPTY_ADS", "zero/empty/ADS check")
    coverage = json.loads((OUT / "drawing_path_crosscheck.json").read_text(encoding="utf-8"))
    check(coverage["unassigned_foreground_path_count"] == 0, "drawing path coverage")
    layout = json.loads((OUT / "layout_coordination.json").read_text(encoding="utf-8"))
    check(layout["human_review"]["global_font_visual_harmony_pass"] is False, "D/E result")
    check(critical["pre_zorder_same_colour_geometric_raw_intersection_px"] == 64, "R002 pre mask")
    check(critical["final_unique_raw_intersection_px"] == 0 and critical["final_unique_raw_clearance_px"] == 0.0, "R002 final mask")

    candidate = Path(identity["candidate_pdf"])
    source = Path(identity["declared_figure_source"])
    candidate_hash = sha256(candidate)
    source_hash = sha256(source)
    check(candidate_hash == identity["candidate_pdf_sha256"], "candidate hash changed")
    check(source_hash == identity["source_sha256"], "source hash changed")

    result = {
        "audit_id": summary["audit_id"],
        "reviewer": REVIEWER,
        "terminal_status": "FAIL_TO_SA2",
        "terminal_reason": "hard pixel/purity and non-whitelisted cross-panel clearance gates fail; frozen candidate/source were not modified",
        "candidate": {"path": str(candidate), "sha256": candidate_hash, "pages": 813},
        "source": {"path": str(source), "sha256": source_hash},
        "identity": {"figure": "32.8", "physical_page": 659, "printed_page": 646, "p609_excluded": True},
        "counts": {"objects": 102, "text_objects": 36, "graphic_objects": 66, "math_rules": 2, "glyphs": 114, "pairs_expected": 5151, "pairs_reported": 5151, "pair_cards_manual": 110, "named_individual_contacts": 93, "low_profile_glyphs": 15},
        "hard_gates": {"glyph_fail_ids": glyph_fail, "pair_fail_ids": pair_fail, "pixel_fail": 4, "purity_fail": 1, "unwhitelisted_pair_fail": 3, "normal_font_size_fail": 0},
        "critical_R002_G001": {"pre_zorder_shared_px": 64, "final_unique_overlap_px": 0, "final_unique_clearance_px": 0, "required_clearance_px": 8, "verdict": "FAIL"},
        "intentional_data_relation_pair_ids": [r["pair_id"] for r in relations],
        "drawing_path_coverage": {"in_scope_paths": coverage["in_scope_drawing_paths"], "unassigned_foreground_paths": 0},
        "visual_D_E": {"normal_effective_pt_gate": "PASS", "global_harmony": "FAIL", "reason": "lower title R002 overbar reaches upper x-axis G001"},
        "package_pre_manifest_check": ads,
        "cleanup": "PASS: 225 explicit stale self-generated targets removed; referenced assets all remain",
        "next_action": "SA2 must repair frozen-source defects before any requalification; this SA1 package is evidence-only.",
    }
    (OUT / "terminal_status.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Terminal status — FIG-P608-01 SA1 R97\n\n",
        "## `FAIL_TO_SA2`\n\n",
        "This is a terminal evidence finding, not a source edit. Candidate/source identity is hash-rechecked and unchanged.\n\n",
        f"- Candidate SHA-256: `{candidate_hash}` (813 pages)\n",
        f"- Source SHA-256: `{source_hash}`\n",
        "- Scope: Figure 32.8, PDF physical 659 / printed 646, P608-only crop.\n",
        "- Completed: 102 objects; 5,151/5,151 pairs; 114/114 signed glyph cards; 110/110 signed contact/critical cards; 93 individual intent records; R001/R002 independently reviewed; 15 low-profile calibrations.\n\n",
        "### Dispositive failures\n\n",
        "- Glyph gates: G008, G019, G027, G058, G063.\n",
        "- Cross-panel pair gates: P2311, P2315, P3071.\n",
        "- P3071 is R002 lower-title overbar to G001 upper x-axis: pre-zorder shared 64px; final unique overlap 0px; final clearance 0px < 8px.\n",
        "- Normal labels meet >=9.5pt, but D/E visual coordination still fails at that title/axis relationship.\n\n",
        "Five target-reference/data-marker pairs are individually justified `INTENTIONAL_DATA_RELATION` entries, not residual pair failures; see `intentional_data_relation_review.csv`.\n\n",
        "Manifest and `WRITE_STOPPED` follow this terminal file.\n",
    ]
    (OUT / "terminal_status.md").write_text("".join(md), encoding="utf-8")
    (OUT / "FINAL_CROSSCHECK.json").write_text(json.dumps({"status": "PASS_INTERNAL_CONSISTENCY_WITH_FAIL_TO_SA2", "terminal": result, "checks": "all assertions in p608_r1_terminal.py passed before terminal issuance"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("terminal issued: FAIL_TO_SA2; no manifest/write-stop written")


if __name__ == "__main__":
    main()
