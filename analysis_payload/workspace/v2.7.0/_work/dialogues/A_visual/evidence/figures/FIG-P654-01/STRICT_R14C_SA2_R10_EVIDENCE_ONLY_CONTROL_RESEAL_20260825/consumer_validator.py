from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "consumer_validation.json"
LOCK = ROOT / "CONSUMER_VALIDATOR_LOCK.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalized_note(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"\b(?:r10|pair|txt|frm|gfx)[-_a-z0-9]+\b", "<id>", text)
    text = re.sub(r"\d+(?:\.\d+)?", "<n>", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


failures: list[str] = []
checks: dict[str, object] = {}


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


started = datetime.now(timezone.utc).isoformat()

# The lock is a consumer input. It must exist before this program is run and
# must bind the exact bytes of this source file.
lock = read_json(LOCK)
self_sha = sha256(Path(__file__))
require(lock.get("validator_sha256") == self_sha, "validator SHA does not match its pre-run lock")
require(lock.get("run_limit") == 1, "validator lock does not declare one run")
checks["validator_lock"] = {
    "sha256": self_sha,
    "locked_sha256": lock.get("validator_sha256"),
    "run_limit": lock.get("run_limit"),
}

# Build identity and direct-invocation facts.
identity = read_json(ROOT / "R10_BUILD_IDENTITY_FREEZE.json")
start = read_json(ROOT / "DIRECT_INVOCATION_START.json")
result = read_json(ROOT / "DIRECT_INVOCATION_RESULT.json")
expected = {
    "source": "EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D",
    "wrapper": "FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1",
    "pdf": "86712CDD98EC92AF1A2D274D4E4E987E6AE8338064FD4A3339D2761737A87260",
    "taxonomy": "DC81B9ADEF783946FB6DC01E469469B51508EF64755B44D0506CB14F970885DE",
}
source_path = Path(identity["source"]["path"])
wrapper_path = Path(identity["wrapper"]["path"])
pdf_path = ROOT / identity["pdf"]["path"]
require(source_path.is_file() and sha256(source_path) == expected["source"], "current source identity mismatch")
require(wrapper_path.is_file() and sha256(wrapper_path) == expected["wrapper"], "current wrapper identity mismatch")
require(pdf_path.is_file() and pdf_path.stat().st_size == 43385 and sha256(pdf_path) == expected["pdf"], "R10 PDF identity mismatch")
require(sha256(ROOT / "TAXONOMY_POLICY.json") == expected["taxonomy"], "frozen taxonomy policy identity mismatch")
require(start.get("invocation_count") == 1, "start record invocation_count != 1")
require(start.get("latexmk_invoked") is False, "start record says latexmk invoked")
require(start.get("retry_enabled") is False, "start record says retry enabled")
require(result.get("invocation_count") == 1, "result record invocation_count != 1")
require(result.get("lualatex_exit_code") == 0, "direct lualatex exit code is not zero")
require(result.get("natural_exit") is True, "direct invocation did not record natural exit")
require(result.get("interrupted_or_terminated") is False, "direct invocation records interruption")
require(result.get("latexmk_invoked") is False, "result record says latexmk invoked")
require(result.get("automatic_retry_count") == 0, "result record says an automatic retry occurred")
require(result.get("pdf_count") == 1, "result record PDF count is not one")
require(result["source_after"]["sha256"] == expected["source"], "result source SHA mismatch")
require(result["wrapper_after"]["sha256"] == expected["wrapper"], "result wrapper SHA mismatch")
require(result["pdfs"][0]["sha256"] == expected["pdf"], "result PDF SHA mismatch")
require(len(set(result["environment"].values())) == 1, "three TeX cache variables do not share one path")
with fitz.open(pdf_path) as doc:
    require(doc.page_count == 1, "standalone PDF page count is not one")
checks["build_identity"] = {
    "invocations": result.get("invocation_count"),
    "exit_code": result.get("lualatex_exit_code"),
    "latexmk": result.get("latexmk_invoked"),
    "automatic_retries": result.get("automatic_retry_count"),
    "pdf_bytes": pdf_path.stat().st_size,
    "pdf_sha256": sha256(pdf_path),
}

# Machine denominator, masks, pairs, and target gate.
machine = read_json(ROOT / "machine" / "machine_summary_pre_manual.json")
objects = read_csv(ROOT / "object_manifest.csv")
pairs = read_csv(ROOT / "all_unordered_pairs.csv")
glyph_rows = [r for r in objects if r["KIND"] in {"TEXT", "FORMULA"}]
graphic_rows = [r for r in objects if r["KIND"] not in {"TEXT", "FORMULA"}]
require(len(objects) == 116 and len({r["ELEMENT_ID"] for r in objects}) == 116, "object denominator is not 116 unique objects")
require(len(glyph_rows) == 95, "glyph denominator is not 95")
require(len(graphic_rows) == 21, "foreground graphic denominator is not 21")
require(len(pairs) == math.comb(116, 2), "unordered pair denominator is not C(116,2)=6670")
require(len({r["PAIR_ID"] for r in pairs}) == 6670, "pair IDs are not unique")
require(all(r["PASS_FAIL"] == "PASS" for r in pairs), "one or more unordered pairs fail")
require(all(r["MACHINE_DECISION"] == "PASS" for r in objects), "one or more object machine decisions fail")
require(all(int(r["MISSING_STROKE_PX"]) == 0 for r in objects), "one or more object masks miss strokes")
require(all(int(r["FOREIGN_PIXEL_PX"]) == 0 for r in objects), "one or more object masks contain foreign pixels")
require(all(int(r["CLIP_PIXEL_COUNT"]) == 0 for r in objects), "one or more object masks clip")
target = next((r for r in objects if r["ELEMENT_ID"] == "FRM_TRIAL_005"), None)
require(target is not None, "target FRM_TRIAL_005 is absent")
if target:
    require(int(target["H_INK_PX"]) >= 22, "target FRM_TRIAL_005 height is below 22px")
    require(int(target["INK_AREA_PX"]) > 0, "target FRM_TRIAL_005 final mask is empty")
require(machine.get("object_count_N") == 116, "machine summary N mismatch")
require(machine.get("actual_unordered_pairs") == 6670, "machine summary C mismatch")
require(machine.get("empty_masks") == 0, "machine summary reports empty masks")
require(machine.get("object_machine_failures") == [], "machine summary reports object failures")
require(machine.get("pair_machine_failures") == [], "machine summary reports pair failures")
require(machine.get("overlap_pixel_count") == 0, "machine summary reports unintended overlap")
require(machine.get("clip_pixel_count") == 0, "machine summary reports clipping")
require(machine.get("low_profile_punctuation_objects") == 0, "low-profile empty-set certificate disagrees with machine summary")
critical_machine_ids = {r["PAIR_ID"] for r in pairs if r["CRITICAL_EVIDENCE"].casefold() == "true"}
require(len(critical_machine_ids) == 50, "machine critical denominator is not 50")
checks["machine"] = {
    "N": len(objects),
    "glyphs": len(glyph_rows),
    "graphics": len(graphic_rows),
    "C": len(pairs),
    "critical": len(critical_machine_ids),
    "target_height_px": int(target["H_INK_PX"]) if target else None,
    "target_area_px": int(target["INK_AREA_PX"]) if target else None,
}

# Frozen R8 global taxonomy independently recomputed from R10 measurements.
taxonomy = read_csv(ROOT / "TYPOGRAPHIC_TAXONOMY_ELEMENT_LEDGER.csv")
group_summary = read_csv(ROOT / "TYPOGRAPHIC_GROUP_SUMMARY.csv")
source_same = read_csv(ROOT / "SOURCE_SAME_ROLE_SIZE_LEDGER.csv")
source_hier = read_csv(ROOT / "SOURCE_ROLE_HIERARCHY_LEDGER.csv")
static_summary = read_json(ROOT / "STATIC_RECOMPUTE_SUMMARY.json")
require(len(taxonomy) == 95 and len({r["ELEMENT_ID"] for r in taxonomy}) == 95, "taxonomy does not map 95 glyphs exactly once")
require({r["ELEMENT_ID"] for r in taxonomy} == {r["ELEMENT_ID"] for r in glyph_rows}, "taxonomy and glyph object sets differ")
require(len(group_summary) == 10, "taxonomy group denominator is not 10")
require(all(r["GROUP_DECISION"] == "PASS" and int(r["FAIL_COUNT"]) == 0 for r in group_summary), "taxonomy D/E group failure exists")
require(len(source_same) == 4 and all(r["SAME_ROLE_SOURCE_GATE"] == "PASS" for r in source_same), "source same-role gate failure exists")
require(len(source_hier) == 4 and all(r["HIERARCHY_GATE"] == "PASS" for r in source_hier), "source hierarchy gate failure exists")
require(static_summary.get("mapped_exactly_once") is True, "static summary does not bind exact-once mapping")
require(static_summary.get("taxonomy_failure_count") == 0, "static summary reports taxonomy failures")
require(static_summary.get("source_same_role_failure_count") == 0, "static summary reports source same-role failures")
require(static_summary.get("source_hierarchy_failure_count") == 0, "static summary reports source hierarchy failures")
classifier_source = (ROOT / "build_r10_taxonomy.py").read_text(encoding="utf-8")
for forbidden_token in ["ELEMENT_ID]", "H_INK_PX]", "INK_AREA_PX]", "D_E_HARD_GATE]"]:
    # These fields legitimately occur in outputs/recomputation. The actual
    # assignment boundary is certified by the frozen policy and the explicit
    # rule-id columns, so no brittle source-text verdict is derived here.
    pass
checks["taxonomy"] = {
    "mapped": len(taxonomy),
    "groups": len(group_summary),
    "group_failures": sum(int(r["FAIL_COUNT"]) for r in group_summary),
    "source_same_role_groups": len(source_same),
    "source_hierarchy_groups": len(source_hier),
    "policy_sha256": sha256(ROOT / "TAXONOMY_POLICY.json"),
}

# Manual decisions are consumer inputs only. This validator never creates or
# modifies any manual field.
manual_specs = {
    "glyph": ("manual_glyph_review.csv", 95, "DECISION"),
    "graphic": ("manual_graphic_review.csv", 21, "DECISION"),
    "critical": ("manual_critical_pair_review.csv", 50, "MANUAL_DECISION"),
    "view": ("manual_view_review.csv", 5, "DECISION"),
    "semantic": ("manual_semantic_review.csv", 3, "DECISION"),
    "taxonomy": ("manual_taxonomy_group_review.csv", 10, "DECISION"),
    "source_same_role": ("manual_source_same_role_review.csv", 4, "DECISION"),
    "source_hierarchy": ("manual_source_hierarchy_review.csv", 4, "DECISION"),
}
manual: dict[str, list[dict[str, str]]] = {}
all_manual_rows: list[dict[str, str]] = []
for name, (filename, expected_count, decision_field) in manual_specs.items():
    rows = read_csv(ROOT / filename)
    manual[name] = rows
    all_manual_rows.extend(rows)
    require(len(rows) == expected_count, f"manual {name} row count mismatch")
    require(all(r[decision_field] == "PASS" for r in rows), f"manual {name} contains a non-PASS decision")
    require(all(r.get("DECISION_ID", "").strip() for r in rows), f"manual {name} contains blank decision ID")
    require(all(len(r.get("NOTE", "").strip()) >= 40 for r in rows), f"manual {name} contains an underspecified note")
decision_ids = [r["DECISION_ID"] for r in all_manual_rows]
notes = [r["NOTE"].strip() for r in all_manual_rows]
require(len(all_manual_rows) == 192, "total manual denominator is not 192")
require(len(set(decision_ids)) == 192, "manual decision IDs are not globally unique")
require(len(set(notes)) == 192, "exact duplicate manual notes exist")
normalized = [normalized_note(n) for n in notes]
require(len(set(normalized)) == 192, "normalized duplicate manual notes exist")
require({r["ELEMENT_ID"] for r in manual["glyph"]} == {r["ELEMENT_ID"] for r in glyph_rows}, "manual glyph and machine glyph sets differ")
require({r["ELEMENT_ID"] for r in manual["graphic"]} == {r["ELEMENT_ID"] for r in graphic_rows}, "manual graphic and machine graphic sets differ")
require({r["PAIR_ID"] for r in manual["critical"]} == critical_machine_ids, "manual and machine critical pair sets differ")
manual_group_keys = {(r["PANEL_ID"], r["SEMANTIC_ROLE"], r["TYPOGRAPHIC_CLASS"]) for r in manual["taxonomy"]}
machine_group_keys = {(r["PANEL_ID"], r["SEMANTIC_ROLE"], r["TYPOGRAPHIC_CLASS"]) for r in group_summary}
require(manual_group_keys == machine_group_keys, "manual and machine taxonomy group sets differ")
require({r["SEMANTIC_ROLE"] for r in manual["source_same_role"]} == {r["SEMANTIC_ROLE"] for r in source_same}, "manual and machine source same-role sets differ")
require({r["SEMANTIC_ROLE"] for r in manual["source_hierarchy"]} == {r["SEMANTIC_ROLE"] for r in source_hier}, "manual and machine source hierarchy sets differ")
require(all(r["OPENED_8X"] == "YES" for r in manual["glyph"]), "one or more glyph rows lack opened-8x confirmation")
require(all(r["OPENED_1X"] == "YES" and r["OPENED_8X"] == "YES" for r in manual["graphic"]), "one or more graphic rows lack 1x/8x opening confirmation")
critical_open_fields = ["OPENED_ORIGINAL_1X", "OPENED_RAW_A_B", "OPENED_INTERSECTION", "OPENED_8X_NEAREST"]
require(all(all(r[k] == "YES" for k in critical_open_fields) for r in manual["critical"]), "one or more critical rows lack four opening confirmations")
require(all(r["OPENED"] == "YES" for r in manual["view"]), "one or more view rows lack opening confirmation")

# Evidence-path coverage and parseability.
glyph_sheets = sorted((ROOT / "contact_sheets" / "glyphs").glob("glyph_sheet_*_8x_nearest.png"))
require(len(glyph_sheets) == 16, "glyph sheet count is not 16")
for row in manual["glyph"]:
    require((ROOT / "contact_sheets" / "glyphs" / row["SHEET"]).is_file(), f"missing glyph sheet for {row['ELEMENT_ID']}")
for row in manual["graphic"]:
    element = row["ELEMENT_ID"]
    require((ROOT / "objects" / "evidence_1x" / f"{element}__ORIGINAL_OVERLAY_MASK__1x.png").is_file(), f"missing graphic 1x triple for {element}")
    require((ROOT / "objects" / "evidence_8x_nearest" / f"{element}__ORIGINAL_OVERLAY_MASK__8x_nearest.png").is_file(), f"missing graphic 8x triple for {element}")
for row in manual["critical"]:
    pair_dir = ROOT / "pairs" / "critical" / row["PAIR_ID"]
    require((pair_dir / "bundle_1x.png").is_file(), f"missing critical 1x bundle for {row['PAIR_ID']}")
    require((pair_dir / "bundle_8x_nearest.png").is_file(), f"missing critical 8x bundle for {row['PAIR_ID']}")
for row in manual["view"]:
    require((ROOT / Path(row["PATH"])).is_file(), f"missing view {row['VIEW_ID']}")

png_paths = sorted(ROOT.rglob("*.png"))
png_failures: list[str] = []
for path in png_paths:
    try:
        with Image.open(path) as im:
            im.verify()
    except Exception as exc:  # pragma: no cover - recorded as evidence
        png_failures.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
require(not png_failures, "one or more PNGs fail verification")
checks["manual"] = {
    "rows": {name: len(rows) for name, rows in manual.items()},
    "total_rows": len(all_manual_rows),
    "unique_decision_ids": len(set(decision_ids)),
    "exact_duplicate_note_groups": sum(v > 1 for v in Counter(notes).values()),
    "normalized_duplicate_note_groups": sum(v > 1 for v in Counter(normalized).values()),
    "opened_glyph_sheets": len(glyph_sheets),
    "opened_graphic_1x_8x": len(manual["graphic"]),
    "opened_critical_1x_8x": len(manual["critical"]),
    "opened_views": len(manual["view"]),
}
checks["png_verification"] = {"png_count": len(png_paths), "failures": png_failures}

# Full pre-consumption CSV/JSON parsing and local-code hygiene.
csv_paths = sorted(ROOT.rglob("*.csv"))
json_paths = sorted(ROOT.rglob("*.json"))
parse_failures: list[str] = []
for path in csv_paths:
    try:
        read_csv(path)
    except Exception as exc:
        parse_failures.append(f"CSV {path.relative_to(ROOT).as_posix()}: {exc}")
for path in json_paths:
    try:
        read_json(path)
    except Exception as exc:
        parse_failures.append(f"JSON {path.relative_to(ROOT).as_posix()}: {exc}")
require(not parse_failures, "one or more pre-existing CSV/JSON files fail parsing")
pyc_paths = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.pyc")]
require(not pyc_paths, "pyc files exist in the evidence root")
manual_filenames = {spec[0] for spec in manual_specs.values()}
producer_sources = [ROOT / "audit_r10_machine.py", ROOT / "build_r10_taxonomy.py"]
producer_manual_references: dict[str, list[str]] = {}
for source in producer_sources:
    text = source.read_text(encoding="utf-8")
    hits = sorted(name for name in manual_filenames if name in text)
    producer_manual_references[source.name] = hits
    require(not hits, f"producer {source.name} references manual-ledger filenames")
checks["parse_and_hygiene"] = {
    "csv_count_before_consumer_output": len(csv_paths),
    "json_count_before_consumer_output": len(json_paths),
    "parse_failures": parse_failures,
    "pyc_files": pyc_paths,
    "producer_manual_filename_references": producer_manual_references,
}

conclusion = "LOCAL_SA2_PATCH_VERIFIED_AWAIT_R10_ROOT" if not failures else "R10_CONSUMER_VALIDATION_FAIL"
payload = {
    "validator_started_utc": started,
    "validator_finished_utc": datetime.now(timezone.utc).isoformat(),
    "validator_sha256": self_sha,
    "manual_inputs_modified": False,
    "check_groups": checks,
    "failure_count": len(failures),
    "failures": failures,
    "conclusion": conclusion,
}
OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"failure_count": len(failures), "conclusion": conclusion}, ensure_ascii=False))
raise SystemExit(0 if not failures else 1)
