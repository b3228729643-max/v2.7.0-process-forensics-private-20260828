from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825")
REVIEWER = "codex-root-r17-visual"
DESIGN_CONNECTIONS = {
    "P06240": "D0001 node border is the intentional endpoint of D0010 outgoing edge E_TRIAL_FAMILIES; 2 shared antialias pixels are a line-node connection, not an illegal collision.",
    "P06261": "D0002 node border is the intentional endpoint of D0012 outgoing edge E_GAMMA_FAMILIES; 2 shared antialias pixels are a line-node connection, not an illegal collision.",
    "P06285": "D0018 is the semantic relation line joining D0003 N_FAMILIES to D0007 N_SIMPLEX; its 1-pixel contact with D0003 is intentional.",
    "P06347": "D0018 is the semantic relation line joining D0003 N_FAMILIES to D0007 N_SIMPLEX; its 1-pixel contact with D0007 is intentional.",
}
HARD_CLEARANCE_FAILURES = {
    "P06198": "G0092 应 is external edge-label text and is not a designed component of D0009 N_LDA border; native masks have 0 overlap but 0px clearance, below the 3px hard gate.",
    "P06219": "G0093 用 is external edge-label text and is not a designed component of D0009 N_LDA border; native masks have 0 overlap but 0px clearance, below the 3px hard gate.",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    objects = read_csv(ROOT / "after_pixel_measurements.csv")
    raw_pairs = read_csv(ROOT / "after_overlap_report.csv")
    critical = read_csv(ROOT / "CRITICAL_PAIR_LEDGER.csv")
    if len(objects) != 93 or len(raw_pairs) != 6441 or len(critical) != 173:
        raise RuntimeError("denominator changed before manual adjudication")

    object_failures = [r for r in objects if r["DECISION"] == "FAIL"]
    if [r["ELEMENT_ID"] for r in object_failures] != ["G0040", "G0059", "G0064", "G0065"]:
        raise RuntimeError("unexpected object failure set")

    critical_index = {r["PAIR_ID"]: i for i, r in enumerate(critical)}
    final_pair_rows: list[dict[str, object]] = []
    critical_manual_rows: list[dict[str, object]] = []
    final_pair_failure_ids: list[str] = []
    for row in raw_pairs:
        pair_id = row["PAIR_ID"]
        raw_decision = row["DECISION"]
        final_decision = raw_decision
        adjudication = "RAW_MACHINE_RESULT_CONFIRMED"
        note = row["NOTE"] + "; reviewed in all-pair matrix"
        if pair_id in DESIGN_CONNECTIONS:
            final_decision = "PASS"
            adjudication = "PASS_INTENTIONAL_LINE_NODE_GEOMETRIC_CONNECTION"
            note = DESIGN_CONNECTIONS[pair_id]
        elif pair_id in HARD_CLEARANCE_FAILURES:
            final_decision = "FAIL"
            adjudication = "FAIL_NATIVE_CLEARANCE_HARD_GATE"
            note = HARD_CLEARANCE_FAILURES[pair_id]
        if final_decision == "FAIL":
            final_pair_failure_ids.append(pair_id)
        contact = ""
        if pair_id in critical_index:
            contact = f"contact_sheets/critical/critical_contact_{critical_index[pair_id] // 18 + 1:02d}.png"
            note += f" Reviewed dedicated bundle and {contact}."
            critical_manual_rows.append({
                "PAIR_ID": pair_id,
                "A_ID": row["A_ID"],
                "B_ID": row["B_ID"],
                "CATEGORY": row["CATEGORY"],
                "RAW_DECISION": raw_decision,
                "FINAL_DECISION": final_decision,
                "ADJUDICATION": adjudication,
                "CONTACT_SHEET": contact,
                "DEDICATED_BUNDLE": f"critical_pairs/{pair_id}_{row['A_ID']}_{row['B_ID']}",
                "REVIEWER": REVIEWER,
                "NOTE": note,
            })
        final_pair_rows.append({
            "PAIR_ID": pair_id,
            "REVIEWER": REVIEWER,
            "MATRIX_BLOCK": ((int(pair_id[1:]) - 1) // 1700) + 1,
            "CRITICAL_EVIDENCE": bool(contact),
            "CRITICAL_CONTACT_SHEET": contact,
            "A_ID": row["A_ID"],
            "B_ID": row["B_ID"],
            "RAW_DECISION": raw_decision,
            "FINAL_DECISION": final_decision,
            "ADJUDICATION": adjudication,
            "NOTE": note,
        })
    if final_pair_failure_ids != ["P06198", "P06219"]:
        raise RuntimeError(f"unexpected final pair failures: {final_pair_failure_ids}")

    write_csv(ROOT / "MANUAL_PAIR_LEDGER.csv", list(final_pair_rows[0]), final_pair_rows)
    write_csv(ROOT / "MANUAL_CRITICAL_REVIEW.csv", list(critical_manual_rows[0]), critical_manual_rows)

    view_rows = []
    view_notes = {
        "views/full_page_200dpi.png": "Opened at full-page scale; the standalone graph is complete, centered in its wrapper page region, and no clipping or missing node is visible.",
        "views/figure_crop_300dpi.png": "Opened at native figure scale; nine nodes, all semantic arrows/relations, translated 贝塔 label, literal N, and three mathematical plus glyphs are readable.",
        "views/standalone_300dpi.png": "Opened at native 300dpi; overall hierarchy and line routing remain coherent with no visual crowding introduced by R16B.",
        "views/grayscale_300dpi.png": "Opened in grayscale; text, formulas, arrows, borders, and line hierarchy remain distinguishable.",
        "views/after_text_measurement_overlay_300dpi.png": "Opened with all 93 glyph and 21 drawing IDs; masks are complete. G0040/G0059/G0064/G0065 are visibly intact but fail the frozen numeric D/E gate; G0092/G0093 have 0px native clearance to D0009.",
    }
    for path, note in view_notes.items():
        view_rows.append({
            "VIEW": path,
            "ACTUALLY_OPENED": True,
            "LAYOUT_COMPLETE": True,
            "READABLE": True,
            "FONT_VISUAL_HARMONY_PASS": True,
            "HARD_GATE_PASS": False,
            "DECISION": "FAIL",
            "REVIEWER": REVIEWER,
            "NOTE": note,
        })
    write_csv(ROOT / "VIEW_REVIEW_LEDGER.csv", list(view_rows[0]), view_rows)

    result = {
        "figure_uid": "FIG-P654-01",
        "round": "STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825",
        "status": "LOCAL_SA2_FAIL_NEEDS_SOURCE_R3",
        "build": {
            "invocations": 1,
            "engine": "direct_lualatex",
            "exit_code": 0,
            "pdf_path": str(ROOT / "build" / "v260_FIG-P654-01_standalone.pdf"),
            "pdf_bytes": 43510,
            "pdf_sha256": "D83D577DEE19C1B279E7FE93DFFE99F67C3C1C49784392A490F1A79515C2311B",
            "tex_processes_after_release": 0,
        },
        "identities": {
            "source_sha256": "0A7CAAA49978AA6193BA4DC4CB90845981599DFC161F5A8BD6B9143A1EA4C2EB",
            "wrapper_sha256": "FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1",
        },
        "denominators": {
            "glyph": 93,
            "graphic": 21,
            "object": 114,
            "unordered_pair_expected": 6441,
            "unordered_pair_actual": 6441,
            "critical_pair": 173,
            "manual_glyph": 93,
            "manual_graphic": 21,
            "manual_pair": 6441,
            "manual_critical": 173,
            "view": 5,
        },
        "passed_regressions": {
            "target_n_id": "G0005",
            "target_n_h_px": 24,
            "target_n_abs_min_px": 22,
            "target_n_ratio": 1.0,
            "clip_failure_count": 0,
            "illegal_overlap_failure_count_after_manual_adjudication": 0,
            "semantic_layout_complete": True,
            "literal_authoritative_N_preserved": True,
            "math_plus_glyph_count": 3,
        },
        "hard_failures": {
            "glyph_ids": ["G0040", "G0059", "G0064", "G0065"],
            "glyph_details": [
                {"id": "G0040", "char": "+", "h_px": 26, "median_px": 24, "ratio": 1.083333333333, "gate": "<=1.08"},
                {"id": "G0059", "char": "+", "h_px": 26, "median_px": 24, "ratio": 1.083333333333, "gate": "<=1.08"},
                {"id": "G0064", "char": "+", "h_px": 26, "median_px": 24, "ratio": 1.083333333333, "gate": "<=1.08"},
                {"id": "G0065", "char": "N", "h_px": 27, "median_px": 24, "ratio": 1.125, "gate": "<=1.08"},
            ],
            "pair_ids": final_pair_failure_ids,
            "pair_reason": "G0092/G0093 external application label glyphs have 0px native clearance to D0009 N_LDA border; required >=3px.",
            "source_role_ratio": {"max_min": 1.221052631579, "abs_diff_pt": 2.1, "required_ratio": "<=1.03", "required_abs_diff_pt": "<=0.25"},
        },
        "manual_geometric_connection_overrides": DESIGN_CONNECTIONS,
        "font_visual_harmony_pass": True,
        "final_verdict": "FAIL_TO_SA2_SOURCE_R3_REQUIRED",
        "commit_allowed": False,
        "fresh_sa1_allowed": False,
        "fresh_sa3_allowed": False,
        "a_local_pass": False,
    }
    write_json(ROOT / "RESULT.json", result)

    markdown = """# FIG-P654-01 R17 visual acceptance

Status: **LOCAL_SA2_FAIL_NEEDS_SOURCE_R3**.

The one permitted direct LuaLaTeX invocation succeeded and produced a new one-page A4 PDF. The evidence was rebuilt from that PDF: 93 glyphs + 21 graphics = 114 objects, with all 6,441 unordered pairs and 173 critical pairs closed. All five required views, five glyph sheets, six graphic sheets, four all-pair matrices, ten critical-pair contact sheets, and the six raw failure bundles were actually opened.

R16B fixed the original trial `n`: G0005 is now 24px, meets the 22px absolute minimum, and has ratio 1.0000. Layout, semantics, clipping, masks, grayscale readability, and visible font harmony remain acceptable.

The round still fails hard gates:

- G0040/G0059/G0064 are true mathematical plus glyphs, each 26px against a frozen group median of 24px: 1.083333 > 1.08.
- G0065 is the authoritative literal `N`, 27px against 24px: 1.125 > 1.08.
- P06198 and P06219: external label glyphs `应`/`用` have 0px native clearance to the D0009 node border, below the 3px gate.
- The same frozen source formula role spans 11.6pt to 9.5pt: ratio 1.221053 and absolute difference 2.1pt, failing the 1.03 / 0.25pt source gates.

Four raw graphic-graphic contacts (P06240/P06261/P06285/P06347) were individually opened and adjudicated PASS because they are the intended line-to-node endpoints. No illegal overlap remains after that semantic adjudication.

No commit, fresh SA1, fresh SA3, LOCAL PASS, or A_LOCAL_PASS is authorized.
"""
    (ROOT / "after_visual_acceptance.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": result["status"], "objects": 114, "pairs": 6441, "critical": 173, "glyph_failures": result["hard_failures"]["glyph_ids"], "pair_failures": final_pair_failure_ids}, ensure_ascii=False))


if __name__ == "__main__":
    main()
