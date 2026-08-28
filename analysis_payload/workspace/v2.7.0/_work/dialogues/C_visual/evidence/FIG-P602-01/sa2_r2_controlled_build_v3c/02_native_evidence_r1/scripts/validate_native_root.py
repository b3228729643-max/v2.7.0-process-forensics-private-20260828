from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "qa" / "validation_report_r2.json"


def read_csv(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def ids(rows: list[dict[str, str]], field: str) -> list[str]:
    return [row[field] for row in rows]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


checks: list[dict[str, object]] = []


def check(name: str, condition: bool, detail: object) -> None:
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


machine_objects = read_csv("objects/object_manifest.csv")
manual_objects = read_csv("ledgers/manual_object_review.csv")
machine_glyphs = read_csv("glyphs/glyph_machine_measurements.csv")
manual_glyphs = read_csv("ledgers/manual_glyph_review.csv")
machine_pairs = read_csv("pairs/all_pairs_machine.csv")
manual_pairs = read_csv("ledgers/manual_pair_review.csv")
machine_critical = read_csv("pairs/critical_machine_index.csv")
manual_critical = read_csv("ledgers/manual_critical_pair_review.csv")
machine_peer = read_csv("ledgers/peer_machine.csv")
manual_peer = read_csv("ledgers/manual_peer_review.csv")
machine_role = read_csv("ledgers/role_machine.csv")
manual_role = read_csv("ledgers/manual_role_review.csv")
machine_clip = read_csv("ledgers/clip_machine.csv")
manual_clip = read_csv("ledgers/manual_clip_review.csv")
machine_view = read_csv("ledgers/view_machine.csv")
manual_view = read_csv("ledgers/manual_view_review.csv")
manual_hard = read_csv("ledgers/manual_hard_gate_review.csv")

expected = {
    "objects": (machine_objects, manual_objects, "object_id", 30),
    "glyphs": (machine_glyphs, manual_glyphs, "glyph_id", 154),
    "pairs": (machine_pairs, manual_pairs, "pair_id", 435),
    "critical_pairs": (machine_critical, manual_critical, "pair_id", 16),
    "roles": (machine_role, manual_role, "role_id", 3),
    "clips": (machine_clip, manual_clip, "object_id", 30),
    "views": (machine_view, manual_view, "view_id", 4),
}

for label, (machine, manual, field, denominator) in expected.items():
    machine_ids = ids(machine, field)
    manual_ids = ids(manual, field)
    check(
        f"{label}_denominator_and_id_closure",
        len(machine) == denominator
        and len(manual) == denominator
        and len(set(machine_ids)) == denominator
        and len(set(manual_ids)) == denominator
        and set(machine_ids) == set(manual_ids),
        {
            "expected": denominator,
            "machine_rows": len(machine),
            "manual_rows": len(manual),
            "machine_unique": len(set(machine_ids)),
            "manual_unique": len(set(manual_ids)),
            "missing_manual": sorted(set(machine_ids) - set(manual_ids)),
            "extra_manual": sorted(set(manual_ids) - set(machine_ids)),
        },
    )

peer_machine_keys = {
    (row["element_id"], row["role"], row["peer_class"]) for row in machine_peer
}
peer_manual_keys = {
    (row["element_id"], row["role"], row["peer_class"]) for row in manual_peer
}
peer_manual_ids = ids(manual_peer, "peer_id")
check(
    "peers_denominator_and_id_closure",
    len(machine_peer) == len(manual_peer) == 28
    and len(peer_machine_keys) == len(peer_manual_keys) == 28
    and peer_machine_keys == peer_manual_keys
    and len(set(peer_manual_ids)) == 28,
    {
        "expected": 28,
        "machine_rows": len(machine_peer),
        "manual_rows": len(manual_peer),
        "manual_peer_id_unique": len(set(peer_manual_ids)),
        "compound_key_missing_manual": sorted(peer_machine_keys - peer_manual_keys),
        "compound_key_extra_manual": sorted(peer_manual_keys - peer_machine_keys),
    },
)

check(
    "hard_gate_denominator",
    len(manual_hard) == 12 and len(set(ids(manual_hard, "gate_id"))) == 12,
    {"expected": 12, "rows": len(manual_hard), "unique": len(set(ids(manual_hard, "gate_id")))},
)

pair_machine_by_id = {row["pair_id"]: row for row in machine_pairs}
pair_endpoint_mismatch = [
    row["pair_id"]
    for row in manual_pairs
    if row["pair_id"] not in pair_machine_by_id
    or row["object_a"] != pair_machine_by_id[row["pair_id"]]["object_a"]
    or row["object_b"] != pair_machine_by_id[row["pair_id"]]["object_b"]
]
check("pair_endpoints_match_machine", not pair_endpoint_mismatch, pair_endpoint_mismatch)
check(
    "pair_combinatorial_denominator",
    len(machine_pairs) == len(machine_objects) * (len(machine_objects) - 1) // 2 == 435,
    {"objects": len(machine_objects), "pairs": len(machine_pairs), "c_n_2": 435},
)

manual_decision_sets = {
    "objects": sorted({row["manual_decision"] for row in manual_objects}),
    "pairs": sorted({row["manual_decision"] for row in manual_pairs}),
    "critical": sorted({row["manual_decision"] for row in manual_critical}),
    "peers": sorted({row["manual_decision"] for row in manual_peer}),
    "roles": sorted({row["manual_decision"] for row in manual_role}),
    "clips": sorted({row["manual_decision"] for row in manual_clip}),
    "views": sorted({row["manual_decision"] for row in manual_view}),
}
check(
    "non_glyph_manual_ledgers_all_explicit_pass",
    all(values == ["PASS"] for values in manual_decision_sets.values()),
    manual_decision_sets,
)

glyph_visual_failures = [row["glyph_id"] for row in manual_glyphs if row["manual_visual_decision"] != "PASS"]
glyph_hard_failures = [row["glyph_id"] for row in manual_glyphs if row["hard_gate_status"] != "PASS"]
glyph_machine_failures = [row["glyph_id"] for row in machine_glyphs if row["machine_threshold_pass"].lower() != "true"]
check("glyph_visual_results", glyph_visual_failures == [], glyph_visual_failures)
check(
    "glyph_hard_failure_exactly_g032",
    glyph_hard_failures == ["G032"] and glyph_machine_failures == ["G032"],
    {"manual": glyph_hard_failures, "machine": glyph_machine_failures},
)

hard_failures = [row["gate_id"] for row in manual_hard if row["manual_decision"] != "PASS"]
check("hard_gate_failure_exactly_h06", hard_failures == ["H06"], hard_failures)

machine_pair_failures = [row["pair_id"] for row in machine_pairs if row["machine_decision"] != "PASS"]
machine_peer_failures = [row["element_id"] for row in machine_peer if row["machine_peer_pass"].lower() != "true"]
machine_role_failures = [row["role_id"] for row in machine_role if row["machine_role_pass"].lower() != "true"]
machine_clip_failures = [row["object_id"] for row in machine_clip if row["machine_clip_pass"].lower() != "true"]
check("machine_pair_failures_zero", machine_pair_failures == [], machine_pair_failures)
check("machine_peer_failures_zero", machine_peer_failures == [], machine_peer_failures)
check("machine_role_failures_zero", machine_role_failures == [], machine_role_failures)
check("machine_clip_failures_zero", machine_clip_failures == [], machine_clip_failures)

observation_fields = {
    "objects": (manual_objects, "object_specific_observation"),
    "glyphs": (manual_glyphs, "glyph_specific_observation"),
    "pairs": (manual_pairs, "pair_specific_observation"),
    "critical": (manual_critical, "critical_specific_observation"),
    "peers": (manual_peer, "peer_specific_observation"),
    "roles": (manual_role, "role_specific_observation"),
    "clips": (manual_clip, "clip_specific_observation"),
    "views": (manual_view, "view_specific_observation"),
    "hard_gates": (manual_hard, "gate_specific_observation"),
}
for label, (rows, field) in observation_fields.items():
    values = [row[field].strip() for row in rows]
    check(
        f"{label}_observations_nonblank_unique",
        all(values) and len(values) == len(set(values)),
        {"rows": len(values), "nonblank": sum(bool(value) for value in values), "unique": len(set(values))},
    )

csv_files = sorted(ROOT.rglob("*.csv"))
csv_parse_failures: list[dict[str, str]] = []
for path in csv_files:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            list(csv.reader(handle))
    except Exception as exc:  # pragma: no cover - evidence capture
        csv_parse_failures.append({"path": path.relative_to(ROOT).as_posix(), "error": repr(exc)})
check("all_csv_parse", not csv_parse_failures, {"count": len(csv_files), "failures": csv_parse_failures})

json_files = sorted(path for path in ROOT.rglob("*.json") if path != REPORT)
json_parse_failures: list[dict[str, str]] = []
for path in json_files:
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - evidence capture
        json_parse_failures.append({"path": path.relative_to(ROOT).as_posix(), "error": repr(exc)})
check("all_json_parse", not json_parse_failures, {"count": len(json_files), "failures": json_parse_failures})

png_files = sorted(ROOT.rglob("*.png"))
png_open_failures: list[dict[str, str]] = []
for path in png_files:
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:  # pragma: no cover - evidence capture
        png_open_failures.append({"path": path.relative_to(ROOT).as_posix(), "error": repr(exc)})
check("all_png_open", not png_open_failures, {"count": len(png_files), "failures": png_open_failures})

cache_artifacts = sorted(
    path.relative_to(ROOT).as_posix()
    for path in ROOT.rglob("*")
    if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}
)
check("no_python_cache_artifacts", not cache_artifacts, cache_artifacts)

ads_command = (
    "$root='" + str(ROOT).replace("'", "''") + "'; "
    "$extra=@(Get-ChildItem -LiteralPath $root -Recurse -File | Get-Item -Stream * | "
    "Where-Object { $_.Stream -ne ':$DATA' }); "
    "$extra | ForEach-Object { $_.FileName + '|' + $_.Stream }"
)
ads_process = subprocess.run(
    ["powershell.exe", "-NoProfile", "-Command", ads_command],
    text=True,
    encoding="utf-8",
    errors="replace",
    capture_output=True,
    check=False,
)
ads_lines = [line for line in ads_process.stdout.splitlines() if line.strip()]
check(
    "no_alternate_data_streams",
    ads_process.returncode == 0 and not ads_lines,
    {"exit_code": ads_process.returncode, "streams": ads_lines, "stderr": ads_process.stderr.strip()},
)

identity = json.loads((ROOT / "identity/candidate_and_source_identity.json").read_text(encoding="utf-8"))
check(
    "frozen_pdf_identity",
    identity["candidate_pdf_bytes"] == 41240
    and identity["candidate_pdf_sha256"] == "203977543DB0F41686A955D33D83A55BA272A7AAE07599AED58227914019EE2C",
    {"bytes": identity["candidate_pdf_bytes"], "sha256": identity["candidate_pdf_sha256"]},
)
check(
    "frozen_source_identity",
    identity["source_sha256"] == "2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349",
    {"bytes": identity["source_bytes"], "sha256": identity["source_sha256"]},
)

failure_names = [item["name"] for item in checks if not item["pass"]]
report = {
    "uid": "FIG-P602-01",
    "round": "SA2_R2_V3C_NATIVE_R1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "validator_path": str(Path(__file__).resolve()),
    "validator_sha256_pre_run": sha256(Path(__file__).resolve()),
    "outcome": "PASS" if not failure_names else "FAIL",
    "expected_evidence_outcome": "STRICT_FAIL_G032_H06",
    "failure_count": len(failure_names),
    "failure_names": failure_names,
    "checks": checks,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"report": str(REPORT), "validation_outcome": report["outcome"], "failures": failure_names}, ensure_ascii=False))
raise SystemExit(0 if not failure_names else 1)
