from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import time


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "evidence_file_manifest.csv"
MARKER = ROOT / "WRITE_STOPPED.json"
PAYLOAD = ["HANDOFF.md", "ROOT_AUDIT.json", "seal_handoff.py"]
OLD_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa1_r101_fresh_v1")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def root_snapshot(root: Path) -> str:
    records = []
    for path in sorted((item for item in root.iterdir() if item.is_file()), key=lambda item: item.name.casefold()):
        file_stat = path.stat()
        records.append({"path": path.name, "bytes": file_stat.st_size, "sha256": sha256(path), "mtime_ns": file_stat.st_mtime_ns})
    raw = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for record in records).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


if MANIFEST.exists() or MARKER.exists():
    raise SystemExit("handoff already sealed")
actual = sorted(path.name for path in ROOT.iterdir() if path.is_file())
if actual != sorted(PAYLOAD):
    raise SystemExit(f"unexpected pre-seal files: {actual}")

audit = json.loads((ROOT / "ROOT_AUDIT.json").read_text(encoding="utf-8"))
if audit["status"] != "ROOT_REJECT_CONTROL_ONLY":
    raise SystemExit("audit status mismatch")
if root_snapshot(OLD_ROOT) != audit["sealed_root_mechanical_audit"]["complete_root_snapshot_sha256"]:
    raise SystemExit("old evidence root changed")
if sha256(OLD_ROOT / "MANIFEST.json") != audit["sealed_root_mechanical_audit"]["manifest_sha256"]:
    raise SystemExit("old manifest changed")
if sha256(OLD_ROOT / "WRITE_STOPPED") != audit["sealed_root_mechanical_audit"]["write_stopped_sha256"]:
    raise SystemExit("old marker changed")

files = [ROOT / name for name in PAYLOAD]
rows = []
for path in sorted(files, key=lambda item: item.name):
    file_stat = path.stat()
    rows.append({
        "path": path.name,
        "bytes": file_stat.st_size,
        "sha256": sha256(path),
        "mtime_ns_100": file_stat.st_mtime_ns // 100,
        "mtime_utc": datetime.fromtimestamp(file_stat.st_mtime_ns / 1_000_000_000, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    })

canonical = "".join(f"{row['path']}|{row['bytes']}|{row['sha256']}|{row['mtime_ns_100']}\n" for row in rows).encode("utf-8")
recordset_sha256 = hashlib.sha256(canonical).hexdigest().upper()
with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=ROOT, prefix="evidence_file_manifest.", suffix=".tmp") as temporary:
    writer = csv.DictWriter(temporary, fieldnames=["path", "bytes", "sha256", "mtime_ns_100", "mtime_utc"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    temporary.flush()
    os.fsync(temporary.fileno())
    temporary_manifest = Path(temporary.name)
os.replace(temporary_manifest, MANIFEST)
manifest_sha256 = sha256(MANIFEST)
for path in files:
    os.chmod(path, stat.S_IREAD)
os.chmod(MANIFEST, stat.S_IREAD)

time.sleep(0.12)
marker = {
    "schema": "C_P600_R101_SA1_ROOT_REJECT_HANDOFF_SEAL_V1",
    "status": "P600_R101_SA1_ROOT_REJECT_CONTROL_ONLY_REQUEST_RESEAL",
    "write_stopped": True,
    "sealed_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    "ordinary_files_expected": 5,
    "manifest_rows": 3,
    "unique_unlisted": ["evidence_file_manifest.csv", "WRITE_STOPPED.json"],
    "canonical_recordset_sha256": recordset_sha256,
    "manifest_bytes": MANIFEST.stat().st_size,
    "manifest_sha256": manifest_sha256,
    "root_audit_sha256": sha256(ROOT / "ROOT_AUDIT.json"),
    "handoff_sha256": sha256(ROOT / "HANDOFF.md"),
    "old_root_snapshot_sha256": audit["sealed_root_mechanical_audit"]["complete_root_snapshot_sha256"],
    "content_result": "STRICT_FAIL_S07",
    "root_control_result": "REJECT",
    "old_root_modified": False,
    "tex_invoked": False,
    "source_modified": False,
    "central_state_written": False,
    "central_inventory_written": False,
    "post_seal_writes_expected": 0,
}
with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=ROOT, prefix="WRITE_STOPPED.", suffix=".tmp") as temporary:
    json.dump(marker, temporary, ensure_ascii=False, indent=2)
    temporary.write("\n")
    temporary.flush()
    os.fsync(temporary.fileno())
    temporary_marker = Path(temporary.name)
os.replace(temporary_marker, MARKER)
os.chmod(MARKER, stat.S_IREAD)

print(json.dumps({
    "ordinary_files": 5,
    "manifest_rows": 3,
    "manifest_sha256": manifest_sha256,
    "marker_sha256": sha256(MARKER),
    "recordset_sha256": recordset_sha256,
    "root_audit_sha256": sha256(ROOT / "ROOT_AUDIT.json"),
    "handoff_sha256": sha256(ROOT / "HANDOFF.md"),
}, ensure_ascii=False))
