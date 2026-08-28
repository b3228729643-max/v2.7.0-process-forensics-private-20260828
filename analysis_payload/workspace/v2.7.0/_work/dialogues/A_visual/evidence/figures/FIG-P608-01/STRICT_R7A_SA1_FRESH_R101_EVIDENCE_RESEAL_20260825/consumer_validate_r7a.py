from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
MACHINE = ROOT / "machine_reuse"
OUT = ROOT / "consumer_validation.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require(condition: bool, code: str, failures: list[str]) -> None:
    if not condition:
        failures.append(code)


failures: list[str] = []
checks: dict[str, object] = {}

# Source and candidate identity are consumed, never created or repaired here.
identity = json.loads((ROOT / "source_identity_and_parse.json").read_text(encoding="utf-8"))
source = Path(identity["source"]["absolute_path"])
pdf = Path(identity["r101"]["absolute_path"])
require(source.is_file(), "SOURCE_NOT_ORDINARY", failures)
require(source.stat().st_size == 3429, "SOURCE_BYTES", failures)
require(sha256(source) == "78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05", "SOURCE_SHA", failures)
require(pdf.is_file(), "PDF_NOT_ORDINARY", failures)
require(pdf.stat().st_size == 4_947_496, "PDF_BYTES", failures)
require(sha256(pdf) == "0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1", "PDF_SHA", failures)
require(identity["r101"]["pages"] == 814, "PDF_PAGE_COUNT", failures)
require(identity["r101"]["physical_page_1based"] == 659, "PDF_PAGE_MAPPING", failures)
checks["source_pdf_identity"] = "PASS" if not failures else "CHECK_FAILURES"

# R7 machine-only reuse ledger: every source/destination pair is re-opened and re-hashed.
reuse = json.loads((ROOT / "reuse_identity_ledger.json").read_text(encoding="utf-8"))
require(reuse["entry_count"] == 1893 == len(reuse["entries"]), "REUSE_COUNT", failures)
reuse_ids: set[str] = set()
for e in reuse["entries"]:
    require(e["reuse_id"] not in reuse_ids, f"REUSE_DUP:{e['reuse_id']}", failures)
    reuse_ids.add(e["reuse_id"])
    src = Path(e["r7_source_path"])
    dst = Path(e["r7a_destination_path"])
    require(src.is_file() and dst.is_file(), f"REUSE_MISSING:{e['reuse_id']}", failures)
    if src.is_file() and dst.is_file():
        require(src.stat().st_size == e["r7_bytes"] == dst.stat().st_size == e["r7a_bytes"], f"REUSE_BYTES:{e['reuse_id']}", failures)
        require(sha256(src) == e["r7_sha256"] == sha256(dst) == e["r7a_sha256"], f"REUSE_SHA:{e['reuse_id']}", failures)
    require(e["bound_r101_physical_page_1based"] == 659, f"REUSE_PAGE:{e['reuse_id']}", failures)
    require(e["bound_r101_pdf_sha256"] == "0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1", f"REUSE_PDF_BIND:{e['reuse_id']}", failures)
    require(e["bound_p608_source_sha256"] == "78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05", f"REUSE_SOURCE_BIND:{e['reuse_id']}", failures)
    rel = e["r7_relative_path"].replace("\\", "/").lower()
    banned = ("manual_", "sa1_review", "result", "handoff", "event_log", "after_visual_acceptance", "hard_failures", "write_stopped", "seal")
    require(not any(token in rel for token in banned), f"REUSE_FORBIDDEN:{rel}", failures)
checks["reuse_identity"] = {"entries": len(reuse_ids), "status": "PASS" if not any(x.startswith("REUSE_") for x in failures) else "FAIL"}

# Machine denominator and complete unordered pair set.
objects = read_csv(MACHINE / "object_inventory.csv")
object_ids = [r["ELEMENT_ID"] for r in objects]
require(len(objects) == 172 and len(set(object_ids)) == 172, "OBJECT_DENOMINATOR", failures)
require(sum(r["CLASS"] == "GLYPH" for r in objects) == 112, "GLYPH_DENOMINATOR", failures)
require(sum(r["CLASS"] == "GRAPHIC" for r in objects) == 60, "GRAPHIC_DENOMINATOR", failures)
require(sum(r["OBJECT_TYPE"] == "MATH_RULE" for r in objects) == 6, "MATH_RULE_COUNT", failures)
require(sum(r["OBJECT_TYPE"] == "PATTERN" for r in objects) == 2, "PATTERN_COUNT", failures)
pairs = read_csv(MACHINE / "all_unordered_pairs.csv")
pair_ids = [r["PAIR_ID"] for r in pairs]
require(len(pairs) == 14_706 == 172 * 171 // 2, "PAIR_COUNT", failures)
require(len(set(pair_ids)) == 14_706, "PAIR_UNIQUENESS", failures)
object_set = set(object_ids)
require(all(r["A_ID"] in object_set and r["B_ID"] in object_set and r["A_ID"] != r["B_ID"] for r in pairs), "PAIR_ENDPOINTS", failures)
denom = json.loads((MACHINE / "denominator_conservation.json").read_text(encoding="utf-8"))
require(denom["page_rawdict_total_chars"] == 837 and denom["domain_final_glyphs"] == 112, "CHAR_CONSERVATION", failures)
require(denom["page_get_drawings_total"] == 89 and denom["target_explicit_drawings"] == 58 and denom["visible_pattern_layers_not_emitted_by_get_drawings"] == 2, "DRAWING_CONSERVATION", failures)
checks["denominator"] = {"N": 172, "glyph": 112, "graphic": 60, "math_rule": 6, "pattern": 2, "C": 14706}

# Required masks/contact evidence must be ordinary, nonempty, uniquely named and parseable.
for sub, expected in (("masks/final_native", 172), ("masks/final_8x_nearest", 172), ("masks/pre_native", 172), ("masks/pre_8x_nearest", 172)):
    files = sorted((MACHINE / sub).glob("*.png"))
    require(len(files) == expected and len({p.name.lower() for p in files}) == expected, f"MASK_COUNT:{sub}", failures)
    for p in files:
        try:
            with Image.open(p) as im:
                im.verify()
        except Exception:
            failures.append(f"MASK_PARSE:{p.relative_to(ROOT)}")
for sub, expected in (("contact_sheets/glyph", 10), ("contact_sheets/graphic", 3), ("critical_pair_contact_sheets", 13), ("preliminary_run/navigation_contact_sheets", 8)):
    files = sorted((MACHINE / sub).glob("*.png"))
    require(len(files) == expected, f"SHEET_COUNT:{sub}", failures)
    for p in files:
        try:
            with Image.open(p) as im:
                im.verify()
        except Exception:
            failures.append(f"SHEET_PARSE:{p.relative_to(ROOT)}")

# Manual ledgers existed before this script and are only consumed below.
ledger_specs = {
    "object_manual.csv": (172, "R7A-OBJ-"),
    "critical_manual.csv": (102, "R7A-CRT-"),
    "preliminary_manual.csv": (64, "R7A-PRE-"),
    "peer_manual.csv": (13, "R7A-PEER-"),
    "role_manual.csv": (35, "R7A-ROLE-"),
    "view_manual.csv": (4, "R7A-VIEW-"),
    "hard_manual.csv": (1, "R7A-HARD-"),
}
all_decisions: list[str] = []
ledger_rows: dict[str, list[dict[str, str]]] = {}
for name, (expected, prefix) in ledger_specs.items():
    rows = read_csv(ROOT / "manual_ledgers" / name)
    ledger_rows[name] = rows
    require(len(rows) == expected, f"LEDGER_COUNT:{name}", failures)
    ids = [r["decision_id"] for r in rows]
    require(len(set(ids)) == expected and all(x.startswith(prefix) for x in ids), f"LEDGER_IDS:{name}", failures)
    require(all(r.get("reviewer") == "SA1_R7A" and r.get("decision") in {"PASS", "FAIL"} for r in rows), f"LEDGER_DECISION:{name}", failures)
    require(all(r.get("note", "").strip() for r in rows), f"LEDGER_NOTES:{name}", failures)
    forbidden = ("PENDING_LEDGER", "UNKNOWN", "TBD", "DEFAULT", "BULK", "HARDCODE")
    require(not any(any(token in "|".join(r.values()).upper() for token in forbidden) for r in rows), f"LEDGER_FORBIDDEN:{name}", failures)
    all_decisions.extend(ids)
require(len(all_decisions) == 391 and len(set(all_decisions)) == 391, "MANUAL_TOTAL_UNIQUE", failures)
require({r["target_id"] for r in ledger_rows["object_manual.csv"]} == object_set, "OBJECT_LEDGER_SET", failures)
critical_machine = read_csv(MACHINE / "critical_pairs_with_evidence.csv")
require({r["pair_id"] for r in ledger_rows["critical_manual.csv"]} == {r["PAIR_ID"] for r in critical_machine}, "CRITICAL_LEDGER_SET", failures)
checks["manual_ledgers"] = {"object": 172, "critical": 102, "preliminary": 64, "peer": 13, "role": 35, "view": 4, "hard": 1, "total": 391}

# Accepted preliminary primary artifacts: no pending values and complete asset references.
accepted = read_csv(ROOT / "preliminary_run" / "preliminary_64_accepted.csv")
accepted_json = json.loads((ROOT / "preliminary_run" / "preliminary_64_accepted.json").read_text(encoding="utf-8"))["records"]
machine_pre = read_csv(MACHINE / "preliminary_run" / "preliminary_64_failures.csv")
require(len(accepted) == len(accepted_json) == len(machine_pre) == 64, "PRELIM_ACCEPTED_COUNT", failures)
require({r["prelim_id"] for r in accepted} == {r["PRELIM_FAIL_ID"] for r in machine_pre}, "PRELIM_ACCEPTED_SET", failures)
require({r["decision_id"] for r in accepted} == {r["decision_id"] for r in accepted_json}, "PRELIM_JSON_SET", failures)
for r in accepted:
    require(r["manual_missing_px"] != "" and r["manual_foreign_px"] != "", f"PRELIM_MANUAL_EMPTY:{r['prelim_id']}", failures)
    require("PENDING" not in "|".join(r.values()).upper(), f"PRELIM_PENDING:{r['prelim_id']}", failures)
    refs = ("a_before", "a_after")
    if r["prelim_id"].startswith("PAIR-"):
        refs += ("b_before", "b_after", "intersection_before", "intersection_after", "overlay_before", "overlay_after")
    else:
        refs += ("b_after", "overlay_after")
    for field in refs:
        rel = r[field]
        require(rel not in {"", "N/A"} and (ROOT / rel).is_file(), f"PRELIM_ASSET:{r['prelim_id']}:{field}", failures)
require(sum(r["status"] == "FAIL" for r in accepted) == 1 and next(r for r in accepted if r["status"] == "FAIL")["prelim_id"] == "PEER-TXT-098", "PRELIM_FAIL_SET", failures)

# Peer/role/hard artifacts must agree on the single independent hard failure.
peer_rows = ledger_rows["peer_manual.csv"]
role_rows = ledger_rows["role_manual.csv"]
hard_rows = ledger_rows["hard_manual.csv"]
require([r["target_id"] for r in peer_rows if r["decision"] == "FAIL"] == ["TXT-098"], "PEER_FAIL_SET", failures)
require(len([r for r in role_rows if r["decision"] == "FAIL"]) == 1 and [r for r in role_rows if r["decision"] == "FAIL"][0]["panel"] == "CAPTION", "ROLE_FAIL_SET", failures)
require(len(hard_rows) == 1 and hard_rows[0]["target_id"] == "TXT-098" and hard_rows[0]["decision"] == "FAIL", "HARD_FAIL_SET", failures)
peer_098 = next(r for r in peer_rows if r["target_id"] == "TXT-098")
require(peer_098["peer_foreign_px"] == "11" and abs(float(peer_098["area_ratio_clean"]) - 56 / 61) < 1e-9, "PEER098_MEASURE", failures)
checks["accepted_failure_consistency"] = {"hard_failure_count": 1, "hard_failure_id": "HARD-LOWPROFILE-TXT-098", "target": "TXT-098"}

result = {
    "validator": "consumer-only; does not create or alter manual decision rows",
    "handoff_id": identity["handoff_id"],
    "route": identity["route"],
    "status": "PASS" if not failures else "FAIL",
    "checks": checks,
    "failure_count": len(failures),
    "failures": failures,
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "failures": len(failures), "manual_rows": 391, "reuse_entries": len(reuse_ids), "N": 172, "C": 14706}))
raise SystemExit(0 if not failures else 1)
