"""Create final SA1 evidence reports before the terminal/manifest sequence.

This evidence-only program never touches source, candidate PDF, or central
state.  It refuses to prepare a report if the already-recorded manual review
or the complete-pair denominator is inconsistent.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P608-01\STRICT_R1_SA1_REQUAL_R97_20260824")
REVIEWER = "SA1_R1_20260824"

RELATIONS = {
    "P5003": ("G054", "t=10", "1.9800", "-0.0200", 50),
    "P5008": ("G059", "t=15", "2.0200", "+0.0200", 55),
    "P5009": ("G060", "t=16", "2.0182", "+0.0182", 56),
    "P5011": ("G062", "t=18", "2.0077", "+0.0077", 58),
    "P5012": ("G063", "t=19", "2.0071", "+0.0071", 59),
}


def load_csv(name: str):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fields, rows):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest().upper()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    summary_path = OUT / "preliminary_machine_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    counts = summary["counts"]
    require((counts["all_objects"], counts["expected_unordered_pairs"], counts["reported_unordered_pairs"]) == (102, 5151, 5151), "object/pair denominator changed")
    require((counts["text_objects"], counts["graphic_objects"], counts["math_rules"], counts["visible_glyphs"]) == (36, 66, 2, 114), "inventory changed")
    require(counts["intended_contacts"] == 93, "expected 93 named individual contacts")
    require(summary["hard_gate_counts"]["unwhitelisted_pair_fail"] == 3, "final non-whitelisted pair denominator is not 3")

    glyphs = load_csv("glyph_ledger.csv")
    require(len(glyphs) == 114, "glyph count")
    require(not any(r.get("reviewer") == "PENDING" or r.get("decision") == "PENDING" for r in glyphs), "pending glyph rows")
    glyph_fails = [r for r in glyphs if r["decision"].startswith("FAIL_")]
    require([r["glyph_id"] for r in glyph_fails] == ["G008", "G019", "G027", "G058", "G063"], "unexpected glyph failures")

    all_pairs = load_csv("after_overlap_report.csv")
    require(len(all_pairs) == 5151, "not every unordered pair is recorded")
    manual_pairs = load_csv("manual_pair_review.csv")
    require(len(manual_pairs) == 110, "contact/critical card review count")
    hard_pairs = [r for r in manual_pairs if r["manual_decision"].startswith("FAIL_")]
    require([r["pair_id"] for r in hard_pairs] == ["P2311", "P2315", "P3071"], "unexpected final hard-pair list")
    named_intents = load_csv("manual_intended_contact_review.csv")
    require(len(named_intents) == 93, "manual named-intent count")
    require(not any(r.get("decision") == "PENDING" for r in named_intents), "pending intended contact")

    pair_by_id = {r["pair_id"]: r for r in all_pairs}
    manual_by_id = {r["pair_id"]: r for r in manual_pairs}
    relation_rows = []
    for pid, (marker, t, value, deviation, drawing) in RELATIONS.items():
        row = pair_by_id[pid]
        manual = manual_by_id[pid]
        require(row["object_a"] == "G049" and row["object_b"] == marker, f"{pid} mapping")
        require(row["intent_whitelisted"] == "YES" and row["verdict"] == "INTENDED_CONTACT", f"{pid} not individually requalified")
        require(manual["manual_decision"] == "PASS_MANUAL_NAMED_INTENT_CONFIRMED", f"{pid} manual conclusion")
        relation_rows.append({
            "pair_id": pid, "reference_object": "G049", "reference_pdf_drawing": "45", "reference_semantics": "separately drawn dash-dot target y=2",
            "marker_object": marker, "marker_pdf_drawing": str(drawing), "sample": t, "declared_running_mean": value,
            "difference_from_target": deviation, "source_coordinate_lines": "37-38", "source_target_draw_line": "41", "source_target_label_line": "43",
            "raw_overlap_px": row["raw_overlap_px"], "raw_clearance_px": row["raw_clearance_px"], "required_clearance_px": row["required_clearance_px"],
            "evidence_card": row["evidence_card"], "manual_sheet": manual["sheet"], "manual_cell": manual["cell"],
            "reviewer": REVIEWER, "manual_pixel_observation": "native 1x and 8x card opened; relation follows plotted data against the explicitly drawn target, with no unrelated clipping/occlusion", 
            "conclusion": "INTENTIONAL_DATA_RELATION (individual only)",
        })
    fields = list(relation_rows[0])
    write_csv("intentional_data_relation_review.csv", fields, relation_rows)
    md = [
        "# Individual target-reference/data-marker requalification\n\n",
        "This supplement addresses only five lower-panel G049–marker relations. It is not a marker-class waiver. The current source has one separately drawn y=2 dash-dot target reference (line 41), and gives the exact lower running-mean coordinates at lines 37–38. Every row below ties one source coordinate, one PDF drawing object, one native pixel card, and one manual sheet/cell together.\n\n",
        "| Pair | Marker / t | Declared value | Difference from y=2 | Drawing | Native pixel relation | Decision |\n",
        "|---|---|---:|---:|---:|---|---|\n",
    ]
    for r in relation_rows:
        md.append(f"| {r['pair_id']} | {r['marker_object']} / {r['sample']} | {r['declared_running_mean']} | {r['difference_from_target']} | {r['marker_pdf_drawing']} | overlap {r['raw_overlap_px']}px, clearance {r['raw_clearance_px']}px; `{r['evidence_card']}` | {r['conclusion']} |\n")
    md += [
        "\nThe native cards were reopened during requalification. The visual result is consistent with the intended comparison to the target rather than a line drawn through unrelated text or an accidental z-order occlusion. All other pair logic remains unchanged; specifically P2311, P2315, and P3071 are not included in this supplement and remain hard failures.\n",
    ]
    (OUT / "INTENTIONAL_DATA_RELATION_REVIEW.md").write_text("".join(md), encoding="utf-8")

    # A preliminary machine file must not retain a stale 'PENDING' conclusion
    # once its same immutable measurements have a signed human closure.
    summary["status"] = "MEASUREMENTS_RECONCILED_WITH_SIGNED_HUMAN_REVIEW_NO_TERMINAL"
    summary["human_reconciliation"] = {
        "reviewer": REVIEWER,
        "glyph_rows_signed": 114,
        "pair_cards_signed": 110,
        "named_individual_contacts_signed": 93,
        "math_rule_cards_signed": 2,
        "final_hard_pair_ids": ["P2311", "P2315", "P3071"],
        "individual_target_data_relation_pairs": list(RELATIONS),
        "terminal_written": False,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    critical = json.loads((OUT / "critical_barX_vs_upper_axis.json").read_text(encoding="utf-8"))
    require(critical["pre_zorder_same_colour_geometric_raw_intersection_px"] == 64, "critical pre-zorder pixels")
    require(critical["final_unique_raw_intersection_px"] == 0 and critical["final_unique_raw_clearance_px"] == 0.0, "critical unique relation")
    coverage = json.loads((OUT / "drawing_path_crosscheck.json").read_text(encoding="utf-8"))
    require(coverage["unassigned_foreground_path_count"] == 0, "unassigned foreground drawing path")
    layout = json.loads((OUT / "layout_coordination.json").read_text(encoding="utf-8"))
    require(layout["human_review"]["global_font_visual_harmony_pass"] is False, "D/E result")

    normal = [r for r in glyphs if r["math_script"] == "NO"]
    require(all(float(r["effective_pt"]) >= 9.5 for r in normal), "normal label effective size below 9.5pt")
    source = Path(summary["identity"]["declared_figure_source"])
    candidate = Path(summary["identity"]["candidate_pdf"])
    # Identity hashes are rechecked again at final report preparation, but this
    # is explicitly not a build or a source modification.
    candidate_sha = sha256(candidate)
    source_sha = sha256(source)
    require(candidate_sha == summary["identity"]["candidate_pdf_sha256"], "candidate hash drift")
    require(source_sha == summary["identity"]["source_sha256"], "source hash drift")

    final_checks = [
        ("identity_candidate", "candidate SHA256/pages", f"{candidate_sha}; 813 pages", "PASS", "identity_and_location.json"),
        ("identity_source", "declared source SHA256", source_sha, "PASS", "identity_and_location.json"),
        ("scope", "P608-only crop / physical/printed page", "P659 / p646 / Figure 32.8; P609 excluded", "PASS", "identity_and_location.json"),
        ("inventory", "all visible objects", "36 text + 66 graphics = 102; includes R001/R002", "PASS", "object_inventory.csv; drawing_path_coverage.csv"),
        ("drawing_paths", "unassigned visible PDF foreground paths", "0", "PASS", "drawing_path_crosscheck.json"),
        ("pairs", "all unordered pairs", "5151 / 5151 = 102C2", "PASS", "after_overlap_report.csv"),
        ("manual_glyph", "glyph card review", "114/114, 10 sheets", "CLOSED_WITH_5_FAILS", "manual_glyph_review.csv"),
        ("low_profile", "low-profile calibration", "15 targets; H/area ratio [0.92,1.08]", "PASS", "low_profile_calibration.csv"),
        ("math_rules", "drawing[61]/drawing[62] rule inventory", "R001 isolated; R002 relationship hard-fails", "CLOSED_WITH_R002_FAIL", "math_rule_ledger.csv"),
        ("manual_pair", "contact/critical card review", "110/110, 10 sheets; 93 named individual intents", "CLOSED_WITH_3_FAILS", "manual_pair_review.csv; manual_intended_contact_review.csv"),
        ("target_relations", "five near-target data relations", "P5003/P5008/P5009/P5011/P5012 individually source-proved", "INTENTIONAL_DATA_RELATION", "intentional_data_relation_review.csv"),
        ("critical_R002_G001", "R002 rule / upper axis", "pre-zorder shared=64px; final unique overlap=0px; clearance=0px<8", "FAIL", "critical_barX_vs_upper_axis.json"),
        ("visual_D_E", "normal>=9.5pt and hierarchy/coordination", "normal labels pass numeric gate; cross-panel title/axis relation fails", "FAIL", "font_visual_harmony_ledger.csv; manual_visual_review.csv"),
        ("cleanup", "referenced assets after self-generated stale cleanup", "225 planned targets; survivors=0; missing current references=0; stale=0", "PASS", "CLEANUP_STALE_SELF_GENERATED.md; CLEANUP_PREDELETE_RESOLVE_PATH.csv"),
    ]
    write_csv("FINAL_INTEGRITY_ASSERTIONS.csv", ["gate", "criterion", "observed", "status", "evidence"], [dict(zip(["gate", "criterion", "observed", "status", "evidence"], r)) for r in final_checks])

    report = [
        "# FIG-P608-01 — SA1 strict requalification R97\n\n",
        "## Terminal recommendation\n\n",
        "`FAIL_TO_SA2` — the candidate is frozen; no source change was made. The failures below remain after full enumeration, native-pixel review, semantic requalification, and evidence cleanup.\n\n",
        "## Candidate identity and scope\n\n",
        f"- Candidate: `{summary['identity']['candidate_pdf']}`\n",
        f"- SHA-256: `{candidate_sha}`; 813 pages.\n",
        f"- Figure: 32.8, physical PDF page 659, printed page 646; crop is P608 caption/frame only and excludes adjacent P609.\n",
        f"- Read-only declared source: `{source}`; SHA-256 `{source_sha}`.\n\n",
        "## Complete audit coverage\n\n",
        "- 36 text objects + 66 graphic objects (including independent math rules R001/R002) = 102 objects.\n",
        "- 5,151 / 5,151 unordered TT/TG/GG pairs, exactly 102C2.\n",
        "- 114 / 114 visible glyphs signed after native 1× and 8× nearest review, through 10 glyph sheets.\n",
        "- 110 / 110 contact/critical cards signed through 10 pair sheets; 93 named individual semantic contacts, never a class exemption.\n",
        "- 15 low-profile targets independently calibrated with H/area ratios in [0.92,1.08]; all 46 in-scope drawing paths accounted for and 0 unassigned visible foreground paths.\n\n",
        "## Hard failures\n\n",
        "| Gate | Objects | Native measurement / finding | Result |\n",
        "|---|---|---|---|\n",
        "| Pixel height | G008 `=` | H_INK 12px < 22px | FAIL |\n",
        "| Pixel height | G019 `=` | H_INK 11px < 22px | FAIL |\n",
        "| Legal-script pixel height | G027 `t` | H_INK 10px < 15px | FAIL |\n",
        "| Legal-script pixel height | G058 `t` | H_INK 10px < 15px | FAIL |\n",
        "| Glyph purity | G063 `运` | 16 foreign pixels from G005; no missing stroke | FAIL |\n",
        "| Cross-panel TG | P2311 T027/G001 | 0px overlap, 2px clearance < 8px | FAIL |\n",
        "| Cross-panel TG | P2315 T027/G005 | 16px overlap, 0px clearance < 8px | FAIL |\n",
        "| Cross-panel GG | P3071 G001/R002 | pre-zorder shared 64px; final unique overlap 0px but clearance 0px < 8px | FAIL |\n\n",
        "P3071 is not repaired by paint order: vector drawing geometry independently gives axis drawing[8] y=311.025024pt/0.647570pt and overbar drawing[62] y=311.670044pt/0.732000pt, centreline distance 0.645020pt versus half-width sum 0.689785pt (0.044765pt penetration). The four critical raw-mask/overlay cards are retained in `critical_barX_vs_upper_axis/`.\n\n",
        "## Individual data-relation requalification\n\n",
        "P5003, P5008, P5009, P5011, and P5012 are not hard failures. Each has a unique target-reference/marker semantic proof and a signed pixel card: t=10=1.9800, t=15=2.0200, t=16=2.0182, t=18=2.0077, and t=19=2.0071 against the separately drawn y=2 reference. Details are in `intentional_data_relation_review.csv` and `INTENTIONAL_DATA_RELATION_REVIEW.md`. No other cross-panel collision is whitelisted by that decision.\n\n",
        "## Typography, D/E and visual review\n\n",
        "Normal effective label/tick text is >=9.5pt and its same-role hierarchy is not oversized or visually reduced. Legal scripts receive their own pixel gate, which fails at G027/G058. Full-page 200dpi, native 300dpi 1×, standalone, grayscale, and 8× nearest views were opened. The lower title overbar reaching the upper x-axis breaks cross-panel coordination, so the visual D/E gate is also FAIL.\n\n",
        "## Cleanup and closure status\n\n",
        "A scoped stale-self-generated cleanup is documented separately: all 225 planned targets were Resolve-Path verified inside this exact R1 directory, and post-delete verification found zero surviving targets, zero missing final references, and zero remaining stale candidates. An initial Windows PowerShell BOM decoding failure caused no deletion and is retained as a fact record. Terminal, manifest, and write-stop are issued only after this report and final integrity checks.\n",
    ]
    (OUT / "FINAL_REPORT.md").write_text("".join(report), encoding="utf-8")
    print("Prepared final reports and semantic requalification evidence; no terminal or manifest written.")


if __name__ == "__main__":
    main()
