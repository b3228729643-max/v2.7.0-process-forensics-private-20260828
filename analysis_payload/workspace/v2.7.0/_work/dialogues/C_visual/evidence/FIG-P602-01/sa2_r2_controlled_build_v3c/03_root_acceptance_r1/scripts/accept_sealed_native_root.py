from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


SOURCE_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3c\02_native_evidence_r1")
ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = SOURCE_ROOT / "09_manifest" / "evidence_file_manifest.csv"
SOURCE_MARKER = SOURCE_ROOT / "WRITE_STOPPED.json"
REPORT = ROOT / "ROOT_ACCEPTANCE.json"
HANDOFF = ROOT / "HANDOFF.md"
MANIFEST = ROOT / "09_manifest" / "acceptance_file_manifest.csv"
MARKER = ROOT / "WRITE_STOPPED.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def is_readonly(path: Path) -> bool:
    attrs = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attrs & stat.FILE_ATTRIBUTE_READONLY)


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    if temp.exists():
        raise RuntimeError(f"unexpected temp file: {temp}")
    with temp.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


if REPORT.exists() or HANDOFF.exists() or MANIFEST.exists() or MARKER.exists():
    raise SystemExit("fresh acceptance root refused: output already exists")

checks: list[dict[str, object]] = []


def check(name: str, condition: bool, detail: object) -> None:
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


source_rows = read_csv(SOURCE_MANIFEST)
source_marker = json.loads(SOURCE_MARKER.read_text(encoding="utf-8-sig"))
source_files = sorted(path for path in SOURCE_ROOT.rglob("*") if path.is_file())
listed_paths = [row["path"] for row in source_rows]
actual_rel_paths = [path.relative_to(SOURCE_ROOT).as_posix() for path in source_files]
unlisted = sorted(set(actual_rel_paths) - set(listed_paths))

check(
    "source_manifest_model",
    len(source_files) == 900
    and len(source_rows) == 898
    and len(set(listed_paths)) == 898
    and unlisted == ["09_manifest/evidence_file_manifest.csv", "WRITE_STOPPED.json"],
    {
        "ordinary_files": len(source_files),
        "manifest_rows": len(source_rows),
        "unique_manifest_paths": len(set(listed_paths)),
        "unlisted": unlisted,
    },
)

category_counts = {
    "PAYLOAD": sum(row["category"] == "PAYLOAD" for row in source_rows),
    "CONTROL": sum(row["category"] == "CONTROL" for row in source_rows),
}
check("source_category_counts", category_counts == {"PAYLOAD": 882, "CONTROL": 16}, category_counts)

missing: list[str] = []
bytes_mismatch: list[str] = []
sha_mismatch: list[str] = []
mtime_mismatch: list[str] = []
for row in source_rows:
    path = SOURCE_ROOT / row["path"]
    if not path.is_file():
        missing.append(row["path"])
        continue
    file_stat = path.stat()
    if file_stat.st_size != int(row["bytes"]):
        bytes_mismatch.append(row["path"])
    if sha256(path) != row["sha256"]:
        sha_mismatch.append(row["path"])
    if file_stat.st_mtime_ns != int(row["mtime_ns"]):
        mtime_mismatch.append(row["path"])

check("listed_files_present", not missing, missing)
check("listed_bytes_exact", not bytes_mismatch, bytes_mismatch)
check("listed_sha256_exact", not sha_mismatch, sha_mismatch)
check("listed_ntfs_mtime_ns_exact", not mtime_mismatch, mtime_mismatch)

canonical_recordset = "".join(
    f'{row["category"]}|{row["path"]}|{row["bytes"]}|{row["sha256"]}|{row["mtime_ns"]}\n'
    for row in source_rows
).encode("utf-8")
recordset_sha = hashlib.sha256(canonical_recordset).hexdigest().upper()
source_manifest_sha = sha256(SOURCE_MANIFEST)
source_marker_sha = sha256(SOURCE_MARKER)
source_handoff_sha = sha256(SOURCE_ROOT / "HANDOFF.md")
manifest_model = source_marker["manifest_model"]
check(
    "source_manifest_sha",
    source_manifest_sha == manifest_model["manifest_sha256"] == "F26B3535E001550815A6616883FD3B9261F1D1B99A240AA956456047195D4F68",
    {"computed": source_manifest_sha, "marker": manifest_model["manifest_sha256"]},
)
check(
    "source_recordset_sha",
    recordset_sha == manifest_model["canonical_listed_recordset_sha256"] == "9DD45215B3ACF6DBD9AFD761004E827868C2BE04C19BE1861AEDC2A3C2923A85",
    {"computed": recordset_sha, "marker": manifest_model["canonical_listed_recordset_sha256"]},
)

marker_mtime_ns = SOURCE_MARKER.stat().st_mtime_ns
other_latest_mtime_ns = max(path.stat().st_mtime_ns for path in source_files if path != SOURCE_MARKER)
readonly_failures = [path.relative_to(SOURCE_ROOT).as_posix() for path in source_files if not is_readonly(path)]
check(
    "source_marker_strictly_latest",
    marker_mtime_ns > other_latest_mtime_ns,
    {"marker_mtime_ns": marker_mtime_ns, "other_latest_mtime_ns": other_latest_mtime_ns},
)
check("source_all_files_readonly", not readonly_failures, readonly_failures)

csv_files = sorted(SOURCE_ROOT.rglob("*.csv"))
csv_failures: list[dict[str, str]] = []
for path in csv_files:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            list(csv.reader(handle))
    except Exception as exc:
        csv_failures.append({"path": path.relative_to(SOURCE_ROOT).as_posix(), "error": repr(exc)})
check("source_csv_parse", not csv_failures, {"count": len(csv_files), "failures": csv_failures})

json_files = sorted(SOURCE_ROOT.rglob("*.json"))
json_failures: list[dict[str, str]] = []
for path in json_files:
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        json_failures.append({"path": path.relative_to(SOURCE_ROOT).as_posix(), "error": repr(exc)})
check("source_json_parse", not json_failures, {"count": len(json_files), "failures": json_failures})

png_files = sorted(SOURCE_ROOT.rglob("*.png"))
png_failures: list[dict[str, str]] = []
for path in png_files:
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        png_failures.append({"path": path.relative_to(SOURCE_ROOT).as_posix(), "error": repr(exc)})
check("source_png_open", not png_failures, {"count": len(png_files), "failures": png_failures})

cache_artifacts = sorted(
    path.relative_to(SOURCE_ROOT).as_posix()
    for path in SOURCE_ROOT.rglob("*")
    if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}
)
check("source_no_python_cache", not cache_artifacts, cache_artifacts)

ads_command = (
    "$root='" + str(SOURCE_ROOT).replace("'", "''") + "'; "
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
    "source_no_ads",
    ads_process.returncode == 0 and not ads_lines,
    {"exit_code": ads_process.returncode, "streams": ads_lines, "stderr": ads_process.stderr.strip()},
)

manual_specs = {
    "objects": ("ledgers/manual_object_review.csv", "object_id", 30),
    "glyphs": ("ledgers/manual_glyph_review.csv", "glyph_id", 154),
    "pairs": ("ledgers/manual_pair_review.csv", "pair_id", 435),
    "critical_pairs": ("ledgers/manual_critical_pair_review.csv", "pair_id", 16),
    "peers": ("ledgers/manual_peer_review.csv", "peer_id", 28),
    "roles": ("ledgers/manual_role_review.csv", "role_id", 3),
    "clips": ("ledgers/manual_clip_review.csv", "object_id", 30),
    "views": ("ledgers/manual_view_review.csv", "view_id", 4),
    "hard_gates": ("ledgers/manual_hard_gate_review.csv", "gate_id", 12),
}
manual_counts: dict[str, dict[str, int]] = {}
for label, (rel, key, expected) in manual_specs.items():
    rows = read_csv(SOURCE_ROOT / rel)
    unique = len({row[key] for row in rows})
    manual_counts[label] = {"rows": len(rows), "unique": unique, "expected": expected}
    check(f"manual_{label}_count", len(rows) == unique == expected, manual_counts[label])

machine_pairs = read_csv(SOURCE_ROOT / "pairs/all_pairs_machine.csv")
manual_pairs = read_csv(SOURCE_ROOT / "ledgers/manual_pair_review.csv")
machine_by_pair = {row["pair_id"]: row for row in machine_pairs}
pair_mismatch = [
    row["pair_id"]
    for row in manual_pairs
    if row["pair_id"] not in machine_by_pair
    or row["object_a"] != machine_by_pair[row["pair_id"]]["object_a"]
    or row["object_b"] != machine_by_pair[row["pair_id"]]["object_b"]
]
pair_notes = [row["pair_specific_observation"].strip() for row in manual_pairs]
check("manual_pair_endpoint_identity", not pair_mismatch, pair_mismatch)
check(
    "manual_pair_observations_explicit_unique",
    len(pair_notes) == 435 and all(pair_notes) and len(set(pair_notes)) == 435,
    {"rows": len(pair_notes), "nonblank": sum(bool(note) for note in pair_notes), "unique": len(set(pair_notes))},
)

manual_glyphs = read_csv(SOURCE_ROOT / "ledgers/manual_glyph_review.csv")
machine_glyphs = read_csv(SOURCE_ROOT / "glyphs/glyph_machine_measurements.csv")
manual_glyph_hard_failures = [row["glyph_id"] for row in manual_glyphs if row["hard_gate_status"] != "PASS"]
manual_glyph_visual_failures = [row["glyph_id"] for row in manual_glyphs if row["manual_visual_decision"] != "PASS"]
machine_glyph_failures = [row["glyph_id"] for row in machine_glyphs if row["machine_threshold_pass"].lower() != "true"]
hard_rows = read_csv(SOURCE_ROOT / "ledgers/manual_hard_gate_review.csv")
hard_failures = [row["gate_id"] for row in hard_rows if row["manual_decision"] != "PASS"]
check("manual_glyph_visual_failures_zero", manual_glyph_visual_failures == [], manual_glyph_visual_failures)
check(
    "strict_glyph_failure_exact",
    manual_glyph_hard_failures == machine_glyph_failures == ["G032"],
    {"manual": manual_glyph_hard_failures, "machine": machine_glyph_failures},
)
check("strict_hard_gate_failure_exact", hard_failures == ["H06"], hard_failures)

identity = json.loads((SOURCE_ROOT / "identity/candidate_and_source_identity.json").read_text(encoding="utf-8"))
candidate_pdf = Path(identity["candidate_pdf_path"])
source_tex = Path(identity["source_path"])
check(
    "candidate_pdf_external_identity",
    candidate_pdf.is_file()
    and candidate_pdf.stat().st_size == 41240
    and sha256(candidate_pdf) == "203977543DB0F41686A955D33D83A55BA272A7AAE07599AED58227914019EE2C",
    {"path": str(candidate_pdf), "exists": candidate_pdf.is_file()},
)
check(
    "source_external_identity",
    source_tex.is_file()
    and sha256(source_tex) == "2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349",
    {"path": str(source_tex), "exists": source_tex.is_file()},
)

tex_process = subprocess.run(
    [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        "@(Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue).Count",
    ],
    text=True,
    encoding="utf-8",
    errors="replace",
    capture_output=True,
    check=False,
)
try:
    tex_count = int(tex_process.stdout.strip())
except ValueError:
    tex_count = -1
check(
    "tex_processes_zero",
    tex_process.returncode == 0 and tex_count == 0,
    {"exit_code": tex_process.returncode, "count": tex_count, "stderr": tex_process.stderr.strip()},
)

check(
    "source_marker_semantics",
    source_marker["seal_status"] == "WRITE_STOPPED"
    and source_marker["final_evidence_outcome"] == "STRICT_FAIL_G032_H06"
    and source_marker["local_pass_claimed"] is False
    and source_marker["tex_invocations_in_native_evidence_phase"] == 0,
    {
        "seal_status": source_marker["seal_status"],
        "final_evidence_outcome": source_marker["final_evidence_outcome"],
        "local_pass_claimed": source_marker["local_pass_claimed"],
        "tex_invocations": source_marker["tex_invocations_in_native_evidence_phase"],
    },
)

failure_names = [item["name"] for item in checks if not item["pass"]]
acceptance_status = "ROOT_ACCEPTED_STRICT_FAIL_G032_H06" if not failure_names else "ROOT_REJECTED"
report = {
    "uid": "FIG-P602-01",
    "acceptance_round": "SA2_R2_V3C_NATIVE_ROOT_ACCEPTANCE_R1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "acceptance_status": acceptance_status,
    "evidence_outcome": "STRICT_FAIL_G032_H06",
    "source_root": str(SOURCE_ROOT),
    "source_root_ordinary_files": len(source_files),
    "source_manifest_rows": len(source_rows),
    "source_payload_control_self_seal": [882, 16, 1, 1],
    "source_manifest_sha256": source_manifest_sha,
    "source_marker_sha256": source_marker_sha,
    "source_handoff_sha256": source_handoff_sha,
    "source_recordset_sha256": recordset_sha,
    "failure_count": len(failure_names),
    "failure_names": failure_names,
    "manual_counts": manual_counts,
    "checks": checks,
}
atomic_write(REPORT, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

handoff_text = f"""# FIG-P602-01 fresh root acceptance R1

- Acceptance status: `{acceptance_status}`.
- Evidence outcome: `STRICT_FAIL_G032_H06`; this is not a local or global PASS.
- Sealed source root ordinary files / manifest rows: {len(source_files)} / {len(source_rows)}.
- Source payload/control/self/seal: 882/16/1/1.
- Manifest mismatch counts: missing {len(missing)}; bytes {len(bytes_mismatch)}; SHA256 {len(sha_mismatch)}; NTFS mtime-ns {len(mtime_mismatch)}; duplicate paths {len(listed_paths) - len(set(listed_paths))}.
- Unique unlisted files: `{unlisted}`.
- Source manifest SHA256: `{source_manifest_sha}`.
- Canonical listed recordset SHA256: `{recordset_sha}`.
- Source WRITE_STOPPED SHA256: `{source_marker_sha}`.
- Source HANDOFF SHA256: `{source_handoff_sha}`.
- Parse/open/hygiene: CSV failures {len(csv_failures)}; JSON failures {len(json_failures)}; PNG failures {len(png_failures)} across {len(png_files)} PNG files; ADS {len(ads_lines)}; pyc/cache {len(cache_artifacts)}.
- Seal checks: all 900 files read-only; marker strictly latest; post-marker source writes zero by manifest/mtime identity.
- Denominators rechecked: objects 30; glyphs 154; unordered pairs 435; critical 16; peers 28; roles 3; clips 30; views 4; hard gates 12.
- Manual pair rows: 435 unique IDs; endpoints match; 435 nonblank unique observations.
- Sole strict failure: G032 (`一`) manual visual PASS but CJK_FULL 36×4px versus required 30px height; H06 FAIL.
- TeX processes at acceptance: {tex_count}; no TeX command was invoked by this acceptance.
- Acceptance-check failures: {len(failure_names)} `{failure_names}`.
"""
atomic_write(HANDOFF, handoff_text.encode("utf-8"))

accept_files = sorted(
    path
    for path in ROOT.rglob("*")
    if path.is_file() and path not in {MANIFEST, MARKER} and not path.name.endswith(".tmp")
)
accept_rows: list[dict[str, object]] = []
for path in accept_files:
    rel = path.relative_to(ROOT).as_posix()
    file_stat = path.stat()
    accept_rows.append(
        {
            "path": rel,
            "bytes": file_stat.st_size,
            "sha256": sha256(path),
            "mtime_ns": file_stat.st_mtime_ns,
        }
    )

MANIFEST.parent.mkdir(parents=True, exist_ok=True)
manifest_temp = MANIFEST.with_name(MANIFEST.name + ".tmp")
with manifest_temp.open("x", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "mtime_ns"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(accept_rows)
    handle.flush()
    os.fsync(handle.fileno())
os.replace(manifest_temp, MANIFEST)

accept_recordset = "".join(
    f'{row["path"]}|{row["bytes"]}|{row["sha256"]}|{row["mtime_ns"]}\n' for row in accept_rows
).encode("utf-8")
accept_recordset_sha = hashlib.sha256(accept_recordset).hexdigest().upper()
accept_manifest_sha = sha256(MANIFEST)
report_sha = sha256(REPORT)
handoff_sha = sha256(HANDOFF)

for path in [*accept_files, MANIFEST]:
    path.chmod(path.stat().st_mode & ~stat.S_IWRITE)

time.sleep(0.05)
accept_marker = {
    "uid": "FIG-P602-01",
    "acceptance_status": acceptance_status,
    "evidence_outcome": "STRICT_FAIL_G032_H06",
    "seal_status": "WRITE_STOPPED",
    "write_stopped_utc": datetime.now(timezone.utc).isoformat(),
    "source_root": str(SOURCE_ROOT),
    "source_manifest_sha256": source_manifest_sha,
    "source_marker_sha256": source_marker_sha,
    "source_handoff_sha256": source_handoff_sha,
    "source_recordset_sha256": recordset_sha,
    "acceptance_report_sha256": report_sha,
    "acceptance_handoff_sha256": handoff_sha,
    "acceptance_manifest_rows": len(accept_rows),
    "acceptance_manifest_sha256": accept_manifest_sha,
    "acceptance_recordset_sha256": accept_recordset_sha,
    "expected_final_ordinary_files": len(accept_rows) + 2,
    "unlisted_paths": ["09_manifest/acceptance_file_manifest.csv", "WRITE_STOPPED.json"],
    "post_seal_policy": "No further writes in this acceptance root.",
}
atomic_write(MARKER, (json.dumps(accept_marker, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
MARKER.chmod(MARKER.stat().st_mode & ~stat.S_IWRITE)

final_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
if len(final_files) != len(accept_rows) + 2:
    raise RuntimeError("acceptance-root final file count mismatch")
if MARKER.stat().st_mtime_ns <= max(path.stat().st_mtime_ns for path in final_files if path != MARKER):
    raise RuntimeError("acceptance WRITE_STOPPED is not strictly latest")

print(
    json.dumps(
        {
            "acceptance_status": acceptance_status,
            "evidence_outcome": "STRICT_FAIL_G032_H06",
            "failure_count": len(failure_names),
            "acceptance_ordinary_files": len(final_files),
            "acceptance_manifest_rows": len(accept_rows),
            "report_sha256": report_sha,
            "handoff_sha256": handoff_sha,
            "manifest_sha256": accept_manifest_sha,
            "recordset_sha256": accept_recordset_sha,
            "marker_sha256": sha256(MARKER),
            "marker_strictly_latest": True,
        },
        ensure_ascii=False,
    )
)
raise SystemExit(0 if not failure_names else 1)
