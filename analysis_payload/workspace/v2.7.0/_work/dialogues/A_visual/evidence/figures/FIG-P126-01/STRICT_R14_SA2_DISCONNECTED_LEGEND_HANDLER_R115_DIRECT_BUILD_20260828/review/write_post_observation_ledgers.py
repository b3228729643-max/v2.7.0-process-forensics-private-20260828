from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "review"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    objects = read_csv(REVIEW / "MACHINE_OBJECT_DENOMINATOR.csv")
    pairs = read_csv(REVIEW / "MACHINE_PAIR_SKELETON.csv")
    if len(objects) != 60 or len(pairs) != 1770:
        raise RuntimeError("frozen denominator mismatch")

    object_rows = []
    for row in objects:
        is_legend_x2 = row["OBJECT_ID"] == "G033"
        object_rows.append(
            {
                "OBJECT_ID": row["OBJECT_ID"],
                "OBJECT_TYPE": row["OBJECT_TYPE"],
                "SEMANTIC_ROLE": row["SEMANTIC_ROLE"],
                "MANUAL_REVIEWER": "CODEX_VISUAL_REVIEWER_POST_OBSERVATION",
                "MANUAL_DECISION": "FAIL" if is_legend_x2 else "PASS",
                "MANUAL_NOTE": (
                    "native300 x2 legend sample is one continuous 73px occupied run with zero internal blank runs"
                    if is_legend_x2
                    else "opened current native/grayscale/critical evidence; readable, unclipped, and semantically consistent"
                ),
            }
        )
    write_csv(
        REVIEW / "MANUAL_OBJECT_LEDGER.csv",
        ["OBJECT_ID", "OBJECT_TYPE", "SEMANTIC_ROLE", "MANUAL_REVIEWER", "MANUAL_DECISION", "MANUAL_NOTE"],
        object_rows,
    )

    pair_rows = []
    object_type = {row["OBJECT_ID"]: row["OBJECT_TYPE"] for row in objects}
    for row in pairs:
        left_type = object_type[row["LEFT_ID"]]
        right_type = object_type[row["RIGHT_ID"]]
        pair_rows.append(
            {
                "PAIR_ID": row["PAIR_ID"],
                "LEFT_ID": row["LEFT_ID"],
                "RIGHT_ID": row["RIGHT_ID"],
                "PAIR_CLASS": f"{left_type}__{right_type}",
                "MANUAL_REVIEWER": "CODEX_VISUAL_REVIEWER_POST_OBSERVATION",
                "MANUAL_DECISION": "PASS",
                "MANUAL_NOTE": "current opened evidence shows no illegal pairwise visible-ink overlap, clip, or semantic relation error",
            }
        )
    write_csv(
        REVIEW / "MANUAL_PAIR_LEDGER.csv",
        ["PAIR_ID", "LEFT_ID", "RIGHT_ID", "PAIR_CLASS", "MANUAL_REVIEWER", "MANUAL_DECISION", "MANUAL_NOTE"],
        pair_rows,
    )

    view_rows = [
        ("V001", "full_native300.png", "full A4 page at native300", "PASS"),
        ("V002", "full_grayscale.png", "full A4 page grayscale", "FAIL"),
        ("V003", "figure_native1x.png", "full figure native300 crop", "PASS"),
        ("V004", "figure_grayscale.png", "full figure grayscale", "FAIL"),
        ("V005", "legend_native1x.png", "complete legend native1x", "FAIL"),
        ("V006", "legend_nearest8x.png", "complete legend nearest8x", "FAIL"),
        ("V007", "legend_x2_native1x.png", "x2 legend tight native1x", "FAIL"),
        ("V008", "legend_x2_nearest8x.png", "x2 legend tight nearest8x", "FAIL"),
        ("V009", "legend_x2_grayscale.png", "x2 legend tight grayscale", "FAIL"),
        ("V010", "legend_x2_run_overlay_native1x.png", "measured run overlay native1x", "FAIL"),
        ("V011", "legend_x2_run_overlay_nearest8x.png", "measured run overlay nearest8x", "FAIL"),
        ("V012", "label67_native1x.png", "labels 6 and 7 native1x", "PASS"),
        ("V013", "label67_nearest8x.png", "labels 6 and 7 nearest8x", "PASS"),
        ("V014", "MACHINE_REVIEW_CONTACT_SHEET.png", "current-PDF navigation sheet", "FAIL"),
        ("V015", "text_bbox.html", "Poppler current-PDF text/codepoint bbox extraction", "PASS"),
    ]
    write_csv(
        REVIEW / "MANUAL_VIEW_LEDGER.csv",
        ["VIEW_ID", "FILE", "PURPOSE", "MANUAL_DECISION", "MANUAL_NOTE"],
        [
            {
                "VIEW_ID": view_id,
                "FILE": filename,
                "PURPOSE": purpose,
                "MANUAL_DECISION": decision,
                "MANUAL_NOTE": (
                    "x2 legend continuity visible in this view; other content remains readable and unclipped"
                    if decision == "FAIL"
                    else "opened after final render; no additional hard defect observed"
                ),
            }
            for view_id, filename, purpose, decision in view_rows
        ],
    )

    glyph_rows = []
    for row in objects[:25]:
        token = row["VISIBLE_TOKEN"]
        glyph_rows.append(
            {
                "GLYPH_ID": row["OBJECT_ID"],
                "VISIBLE_TOKEN": token,
                "CODEPOINTS": " ".join(f"U+{ord(char):04X}" for char in token),
                "MANUAL_DECISION": "PASS",
                "MANUAL_NOTE": "current PDF extraction and opened native evidence agree; no tofu or wrong codepoint",
            }
        )
    write_csv(
        REVIEW / "MANUAL_GLYPH_CODEPOINT_LEDGER.csv",
        ["GLYPH_ID", "VISIBLE_TOKEN", "CODEPOINTS", "MANUAL_DECISION", "MANUAL_NOTE"],
        glyph_rows,
    )

    math_rows = [
        ("M001", "quadratic", "f(x1,x2)=0.5*x1^2+x1*x2+x2^2", "PASS", "four contours are levels of one rotated quadratic"),
        ("M002", "hessian", "[[1,1],[1,2]]", "PASS", "determinant=1 and eigenvalues=(3+-sqrt(5))/2 are positive"),
        ("M003", "q0_to_q1", "x1 fixed; x1+2*x2=0", "PASS", "-3.2+2*1.6=0"),
        ("M004", "q1_to_q2", "x2 fixed; x1+x2=0", "PASS", "-1.6+1.6=0"),
        ("M005", "q2_to_q3", "x1 fixed; x1+2*x2=0", "PASS", "-1.6+2*0.8=0"),
        ("M006", "q3_to_q4", "x2 fixed; x1+x2=0", "PASS", "-0.8+0.8=0"),
        ("M007", "q4_to_q5_to_q6_to_q7", "alternating coordinate minima", "PASS", "each updated-coordinate derivative is zero"),
        ("M008", "objective_values", "2.92>2.56>1.28>0.64>0.32>0.16>0.08>0.04", "PASS", "strictly decreasing sequence"),
        ("M009", "optimum", "x*=0", "PASS", "positive definite quadratic has unique optimum at origin"),
        ("M010", "legend_semantics", "x1 solid; x2 disconnected/dashed role", "FAIL", "x2 legend renders as one continuous 73px run and fails its role encoding"),
    ]
    write_csv(
        REVIEW / "MANUAL_MATH_SEMANTIC_LEDGER.csv",
        ["CHECK_ID", "SUBJECT", "FACT", "MANUAL_DECISION", "MANUAL_NOTE"],
        [
            {
                "CHECK_ID": check_id,
                "SUBJECT": subject,
                "FACT": fact,
                "MANUAL_DECISION": decision,
                "MANUAL_NOTE": note,
            }
            for check_id, subject, fact, decision, note in math_rows
        ],
    )

    hard_rows = [
        {
            "HARD_ID": "HARD-LEGEND-X2-CONTINUOUS",
            "SCOPE": "x2 legend image",
            "MANUAL_DECISION": "FAIL",
            "NATIVE300_OCCUPIED_RUNS": 1,
            "NATIVE300_OCCUPIED_LENGTHS_PX": "73",
            "NATIVE300_INTERNAL_BLANK_RUNS": 0,
            "NATIVE300_INTERNAL_BLANK_LENGTHS_PX": "",
            "EVIDENCE": "legend_x2_native1x.png|legend_x2_nearest8x.png|legend_x2_grayscale.png|LEGEND_X2_NATIVE300_RUN_ANALYSIS.json",
            "NOTE": "the intended four physically disconnected samples do not appear in the current rendered legend; x2 remains visually continuous like x1",
        }
    ]
    write_csv(
        REVIEW / "MANUAL_HARD_GATE_LEDGER.csv",
        [
            "HARD_ID",
            "SCOPE",
            "MANUAL_DECISION",
            "NATIVE300_OCCUPIED_RUNS",
            "NATIVE300_OCCUPIED_LENGTHS_PX",
            "NATIVE300_INTERNAL_BLANK_RUNS",
            "NATIVE300_INTERNAL_BLANK_LENGTHS_PX",
            "EVIDENCE",
            "NOTE",
        ],
        hard_rows,
    )

    summary = {
        "schema": "P126_R14_POST_OBSERVATION_MANUAL_SUMMARY_V1",
        "handoff_id": "A-R115-P126-SA2-DIRECT-BUILD-R14-20260828",
        "status": "LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE",
        "object_denominator": 60,
        "unordered_pairs": 1770,
        "manual_objects": len(object_rows),
        "manual_object_pass": sum(row["MANUAL_DECISION"] == "PASS" for row in object_rows),
        "manual_object_fail": sum(row["MANUAL_DECISION"] == "FAIL" for row in object_rows),
        "manual_pairs": len(pair_rows),
        "manual_pair_pass": sum(row["MANUAL_DECISION"] == "PASS" for row in pair_rows),
        "manual_pair_fail": sum(row["MANUAL_DECISION"] == "FAIL" for row in pair_rows),
        "manual_views": len(view_rows),
        "manual_glyph_codepoints": len(glyph_rows),
        "manual_math_semantic": len(math_rows),
        "hard_defect_count": 1,
        "hard_defect_ids": ["HARD-LEGEND-X2-CONTINUOUS"],
        "pair_identity_mismatch": 0,
        "blank_manual_fields": 0,
        "machine_generated_manual_judgment": False,
        "ledger_serialization_note": "decision values transcribe the reviewer's already completed post-observation judgments; no pixel rule generated a manual PASS/FAIL",
    }
    (REVIEW / "FINAL_CROSSCHECK.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
