from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "manual"
OUT = ROOT / "CONSUMER_VALIDATION.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value: str) -> float:
    return float(value.strip())


def normalized_note(value: str) -> str:
    value = re.sub(r"\d+(?:\.\d+)?", "#", value.casefold())
    return re.sub(r"[^\w\u3400-\u9fff]+", "", value)


errors: list[str] = []
checks: list[dict[str, object]] = []


def check(name: str, condition: bool, detail: object) -> None:
    checks.append({"name": name, "pass": bool(condition), "detail": detail})
    if not condition:
        errors.append(f"{name}: {detail}")


paths = {
    "glyph": MANUAL / "GLYPH_MANUAL_DECISIONS.csv",
    "graphic": MANUAL / "GRAPHIC_MANUAL_DECISIONS.csv",
    "critical": MANUAL / "CRITICAL_PAIR_MANUAL_DECISIONS.csv",
    "schema": MANUAL / "SCHEMA_MANUAL_DECISIONS.csv",
}
for label, path in paths.items():
    check(f"manual_file_exists_{label}", path.is_file(), str(path))

rows = {label: read_csv(path) for label, path in paths.items()}
expected_counts = {"glyph": 95, "graphic": 21, "critical": 50, "schema": 37}
for label, expected in expected_counts.items():
    check(f"row_count_{label}", len(rows[label]) == expected, {"actual": len(rows[label]), "expected": expected})

all_rows = [row for group in rows.values() for row in group]
decision_ids = [row["DECISION_ID"] for row in all_rows]
check("decision_count_total", len(all_rows) == 203, len(all_rows))
check("decision_ids_unique", len(set(decision_ids)) == 203, [key for key, count in Counter(decision_ids).items() if count > 1])
check("opened_all_true", all(row.get("OPENED") == "TRUE" for row in all_rows), [row["DECISION_ID"] for row in all_rows if row.get("OPENED") != "TRUE"])
check("reviewer_all_explicit", all(row.get("REVIEWER") == "SA2-gpt-5.6-sol-max" for row in all_rows), [row["DECISION_ID"] for row in all_rows if row.get("REVIEWER") != "SA2-gpt-5.6-sol-max"])
check("no_boolean_pass_decisions", all(row.get("DECISION") != "PASS" for row in all_rows), [row["DECISION_ID"] for row in all_rows if row.get("DECISION") == "PASS"])

notes = [row.get("NOTE", "").strip() for row in all_rows]
note_duplicates = [note for note, count in Counter(notes).items() if count > 1]
normalized_duplicates = [note for note, count in Counter(normalized_note(note) for note in notes).items() if count > 1]
check("notes_nonempty_specific_length", all(len(note) >= 20 for note in notes), [decision_ids[i] for i, note in enumerate(notes) if len(note) < 20])
check("notes_exact_unique", not note_duplicates, note_duplicates)
check("notes_numeric_normalized_unique", not normalized_duplicates, normalized_duplicates)
forbidden = re.compile(r"\bdefault\b|global\s+boolean|bulk\s+template|统一note", re.IGNORECASE)
check("notes_no_forbidden_template_marker", all(not forbidden.search(note) for note in notes), [decision_ids[i] for i, note in enumerate(notes) if forbidden.search(note)])

for label, group in rows.items():
    evidence_fields = [key for key in group[0] if key.startswith("EVIDENCE")]
    missing_evidence: list[dict[str, str]] = []
    for row in group:
        for field in evidence_fields:
            rel = row.get(field, "")
            if not rel or not (ROOT / rel).is_file():
                missing_evidence.append({"decision_id": row["DECISION_ID"], "field": field, "path": rel})
    check(f"evidence_exists_{label}", not missing_evidence, missing_evidence)

manifest = read_csv(ROOT / "machine_reuse" / "object_manifest.csv")
by_id = {row["ELEMENT_ID"]: row for row in manifest}
glyph_expected = {row["ELEMENT_ID"] for row in manifest if row["KIND"] in {"TEXT", "FORMULA"}}
graphic_expected = {row["ELEMENT_ID"] for row in manifest if row["KIND"] in {"NODE_BORDER", "LINE_ARROW", "ARROWHEAD", "MATH_RULE"}}
check("glyph_exact_subject_set", {row["SUBJECT_ID"] for row in rows["glyph"]} == glyph_expected, sorted(glyph_expected ^ {row["SUBJECT_ID"] for row in rows["glyph"]}))
check("graphic_exact_subject_set", {row["SUBJECT_ID"] for row in rows["graphic"]} == graphic_expected, sorted(graphic_expected ^ {row["SUBJECT_ID"] for row in rows["graphic"]}))

glyph_mismatches: list[str] = []
for row in rows["glyph"]:
    machine = by_id[row["SUBJECT_ID"]]
    pairs = [("H_PX", "H_INK_PX"), ("AREA_PX", "INK_AREA_PX"), ("MISSING_PX", "MISSING_STROKE_PX"), ("FOREIGN_PX", "FOREIGN_PIXEL_PX")]
    if any(number(row[left]) != number(machine[right]) for left, right in pairs):
        glyph_mismatches.append(row["SUBJECT_ID"])
check("glyph_machine_fields_match", not glyph_mismatches, glyph_mismatches)

graphic_mismatches: list[str] = []
for row in rows["graphic"]:
    machine = by_id[row["SUBJECT_ID"]]
    pairs = [("PRE_AREA_PX", "PRE_OCCLUSION_AREA_PX"), ("OCCLUDED_PX", "OCCLUDED_PX"), ("MISSING_PX", "MISSING_STROKE_PX"), ("FOREIGN_PX", "FOREIGN_PIXEL_PX"), ("CLIP_PX", "CLIP_PIXEL_COUNT")]
    if row["KIND"] != machine["KIND"] or any(number(row[left]) != number(machine[right]) for left, right in pairs):
        graphic_mismatches.append(row["SUBJECT_ID"])
check("graphic_machine_fields_match", not graphic_mismatches, graphic_mismatches)

critical_root = ROOT / "machine_reuse" / "pairs" / "critical"
critical_expected = {path.name for path in critical_root.iterdir() if path.is_dir()}
critical_actual = {row["PAIR_ID"] for row in rows["critical"]}
check("critical_exact_pair_set", critical_actual == critical_expected, sorted(critical_actual ^ critical_expected))
critical_mismatches: list[str] = []
for row in rows["critical"]:
    machine = json.loads((critical_root / row["PAIR_ID"] / "pair.json").read_text(encoding="utf-8-sig"))
    nearest_a = f"{machine['NEAREST_A_X']},{machine['NEAREST_A_Y']}"
    nearest_b = f"{machine['NEAREST_B_X']},{machine['NEAREST_B_Y']}"
    same = (
        row["OBJECT_A"] == machine["OBJECT_A"]
        and row["OBJECT_B"] == machine["OBJECT_B"]
        and row["RELATION"] == machine["RELATION_CLASS"]
        and number(row["PRE_INTERSECTION_PX"]) == float(machine["PRE_OCCLUSION_INTERSECTION_PX"])
        and number(row["FINAL_INTERSECTION_PX"]) == float(machine["FINAL_RAW_INTERSECTION_PX"])
        and abs(number(row["RAW_CLEARANCE_PX"]) - float(machine["RAW_MIN_CLEARANCE_PX"])) < 0.0005
        and row["NEAREST_A"] == nearest_a
        and row["NEAREST_B"] == nearest_b
    )
    if not same:
        critical_mismatches.append(row["PAIR_ID"])
check("critical_machine_fields_match", not critical_mismatches, critical_mismatches)

schema_expected = {
    *(f"R7A-VIEW-{i:03d}" for i in range(1, 6)),
    *(f"R7A-SEMANTIC-{i:03d}" for i in range(1, 4)),
    *(f"R7A-DE-{i:03d}" for i in range(1, 9)),
    *(f"R7A-HIER-{i:03d}" for i in range(1, 6)),
    *(f"R7A-RATIO-{i:03d}" for i in range(1, 17)),
}
check("schema_exact_decision_set", {row["DECISION_ID"] for row in rows["schema"]} == schema_expected, sorted(schema_expected ^ {row["DECISION_ID"] for row in rows["schema"]}))
check("schema_subjects_unique", len({row["SUBJECT_ID"] for row in rows["schema"]}) == 37, [key for key, count in Counter(row["SUBJECT_ID"] for row in rows["schema"]).items() if count > 1])

target = by_id["FRM_TRIAL_005"]
target_ok = (
    number(target["H_INK_PX"]) == 22
    and number(target["INK_AREA_PX"]) == 297
    and number(target["MISSING_STROKE_PX"]) == 0
    and number(target["FOREIGN_PIXEL_PX"]) == 0
    and number(target["CLIP_PIXEL_COUNT"]) == 0
    and number(target["PRE_OCCLUSION_AREA_PX"]) == number(target["INK_AREA_PX"])
)
check("target_machine_gate", target_ok, {key: target[key] for key in ["H_INK_PX", "INK_AREA_PX", "PRE_OCCLUSION_AREA_PX", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX", "CLIP_PIXEL_COUNT"]})

summary = json.loads((ROOT / "machine_reuse" / "machine" / "machine_summary_pre_manual.json").read_text(encoding="utf-8-sig"))
summary_ok = (
    summary["object_count_N"] == 116
    and summary["expected_unordered_pairs"] == 6670
    and summary["actual_unordered_pairs"] == 6670
    and not summary["object_machine_failures"]
    and not summary["pair_machine_failures"]
    and summary["overlap_candidate_pixel_count"] == 0
    and summary["mask_contamination_pixel_count"] == 0
    and summary["overlap_pixel_count"] == 0
    and summary["clip_pixel_count"] == 0
    and summary["critical_pair_count"] == 50
)
check("machine_summary_gates", summary_ok, summary)
check("all_unordered_pair_rows", len(read_csv(ROOT / "machine_reuse" / "all_unordered_pairs.csv")) == 6670, len(read_csv(ROOT / "machine_reuse" / "all_unordered_pairs.csv")))

identity_rows = read_csv(ROOT / "MACHINE_REUSE_IDENTITY_LEDGER.csv")
check("reuse_identity_count", len(identity_rows) == 935, len(identity_rows))
check("reuse_identity_all_match", all(row["IDENTITY_MATCH"] == "True" for row in identity_rows), [row["DESTINATION_RELATIVE_PATH"] for row in identity_rows if row["IDENTITY_MATCH"] != "True"])

frozen = {
    "source": (ROOT / "frozen_identity" / "fig_v5_c05_dependency_graph.tex", 3122, "EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D"),
    "wrapper": (ROOT / "frozen_identity" / "v260_FIG-P654-01_standalone.tex", 397, "FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1"),
    "pdf": (ROOT / "machine_reuse" / "build" / "v260_FIG-P654-01_standalone.pdf", 43385, "A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6"),
}
for label, (path, expected_bytes, expected_sha) in frozen.items():
    check(f"frozen_identity_{label}", path.is_file() and path.stat().st_size == expected_bytes and sha256(path) == expected_sha, {"path": str(path), "bytes": path.stat().st_size if path.exists() else None, "sha256": sha256(path) if path.exists() else None})

result = {
    "validator": {"path": str(Path(__file__).resolve()), "bytes": Path(__file__).stat().st_size, "sha256": sha256(Path(__file__).resolve())},
    "status": "PASS" if not errors else "FAIL",
    "manual_decision_counts": {**{key: len(value) for key, value in rows.items()}, "total": len(all_rows)},
    "manual_files": {label: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for label, path in paths.items()},
    "checks": checks,
    "errors": errors,
    "writes_to_manual_ledgers": 0,
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "check_count": len(checks), "error_count": len(errors), "output": str(OUT)}, ensure_ascii=False))
sys.exit(0 if not errors else 2)
