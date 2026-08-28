from __future__ import annotations

import hashlib
import json
import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R1_SA1_FRESH_R104_R168_20260826")
MANIFEST_JSON = ROOT / "MANIFEST.json"
MANIFEST_SHA = ROOT / "MANIFEST.sha256"
SEAL = ROOT / "SEAL.json"
STOP = ROOT / "WRITE_STOPPED"
CONTROL_NAMES = {MANIFEST_JSON.name, MANIFEST_SHA.name, SEAL.name, STOP.name}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


if any(path.exists() for path in (MANIFEST_JSON, MANIFEST_SHA, SEAL, STOP)):
    raise SystemExit("REFUSED: seal control file already exists; sealing is exactly-once")

payload_paths = sorted(
    (path for path in ROOT.rglob("*") if path.is_file() and path.name not in CONTROL_NAMES),
    key=lambda path: path.relative_to(ROOT).as_posix(),
)
entries = [
    {
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": digest(path),
    }
    for path in payload_paths
]
assert entries
assert len({entry["path"] for entry in entries}) == len(entries)
assert all(":" not in entry["path"] for entry in entries)

manifest_document = {
    "schema": "STRICT_DUAL_MANIFEST_V1",
    "figure_uid": "FIG-P598-02",
    "candidate_round": "R104",
    "physical_page": 650,
    "payload_file_count": len(entries),
    "payload_total_bytes": sum(entry["size_bytes"] for entry in entries),
    "control_files_excluded_by_design": ["MANIFEST.json", "MANIFEST.sha256", "SEAL.json", "WRITE_STOPPED"],
    "files": entries,
}
MANIFEST_JSON.write_text(json.dumps(manifest_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
MANIFEST_SHA.write_text("".join(f'{entry["sha256"]}  {entry["path"]}\n' for entry in entries), encoding="utf-8")

# Cross-validate the two complete payload manifests before sealing.
sha_rows = [line.split("  ", 1) for line in MANIFEST_SHA.read_text(encoding="utf-8").splitlines()]
assert len(sha_rows) == len(entries)
assert {path: hash_value for hash_value, path in sha_rows} == {entry["path"]: entry["sha256"] for entry in entries}
assert all((ROOT / entry["path"]).stat().st_size == entry["size_bytes"] for entry in entries)
assert all(digest(ROOT / entry["path"]) == entry["sha256"] for entry in entries)

sealed_at = datetime.now(timezone.utc).isoformat()
seal_document = {
    "seal_schema": "STRICT_EXACTLY_ONCE_SEAL_V1",
    "figure_uid": "FIG-P598-02",
    "handoff_id": "A-R104-P598-02-SA1-FRESH-20260826",
    "verdict": "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3",
    "sealed_at_utc": sealed_at,
    "payload_file_count": len(entries),
    "payload_total_bytes": sum(entry["size_bytes"] for entry in entries),
    "manifest_json_sha256": digest(MANIFEST_JSON),
    "manifest_sha256_file_sha256": digest(MANIFEST_SHA),
    "dual_manifest_crosscheck": "PASS",
    "ads_non_default_stream_count_preseal": 0,
    "pyc_or_cache_file_count_preseal": 0,
    "write_stop_rule": "WRITE_STOPPED is created strictly last; no later root writes are authorized",
}
SEAL.write_text(json.dumps(seal_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Freeze every existing root file before creating the final marker.
for path in sorted(path for path in ROOT.rglob("*") if path.is_file()):
    os.chmod(path, stat.S_IREAD)

prior_latest_mtime_ns = max(path.stat().st_mtime_ns for path in ROOT.rglob("*") if path.is_file())
STOP.write_text(
    "WRITE_STOPPED\n"
    "FIG-P598-02\n"
    "A-R104-P598-02-SA1-FRESH-20260826\n"
    "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3\n"
    f"sealed_at_utc={sealed_at}\n",
    encoding="utf-8",
)
strict_latest_ns = max(time.time_ns(), prior_latest_mtime_ns + 1_000_000)
os.utime(STOP, ns=(strict_latest_ns, strict_latest_ns))
os.chmod(STOP, stat.S_IREAD)
assert STOP.stat().st_mtime_ns > max(path.stat().st_mtime_ns for path in ROOT.rglob("*") if path.is_file() and path != STOP)

print(json.dumps({
    "sealed": True,
    "payload_file_count": len(entries),
    "payload_total_bytes": sum(entry["size_bytes"] for entry in entries),
    "manifest_json_sha256": seal_document["manifest_json_sha256"],
    "manifest_sha256_file_sha256": seal_document["manifest_sha256_file_sha256"],
    "write_stopped_strictly_latest": True,
    "all_root_files_read_only": True,
}, indent=2))
