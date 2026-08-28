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


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "09_manifest" / "evidence_file_manifest.csv"
MARKER = ROOT / "identity" / "WRITE_STOPPED.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def category(rel: str) -> str:
    if rel.startswith(("identity/", "qa/", "scripts/")) or rel in {"HANDOFF.md", "REVIEW_SUMMARY.md", "MANUAL_REVIEW_PROTOCOL.md"}:
        return "control"
    return "payload"


if MANIFEST.exists() or MARKER.exists():
    raise SystemExit("seal target already exists; immutable root is not resealed")

MANIFEST.parent.mkdir(parents=True, exist_ok=True)
files = sorted(
    (p for p in ROOT.rglob("*") if p.is_file() and p not in {MANIFEST, MARKER}),
    key=lambda p: p.relative_to(ROOT).as_posix(),
)
entries: list[dict[str, object]] = []
for path in files:
    rel = path.relative_to(ROOT).as_posix()
    st = path.stat()
    entries.append({
        "path": rel,
        "category": category(rel),
        "bytes": st.st_size,
        "sha256": sha256(path),
        "mtime_ns_100": st.st_mtime_ns // 100,
        "mtime_utc": datetime.fromtimestamp(st.st_mtime_ns / 1_000_000_000, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    })

canonical = "".join(
    f"{e['path']}|{e['category']}|{e['bytes']}|{e['sha256']}|{e['mtime_ns_100']}\n"
    for e in entries
).encode("utf-8")
recordset_sha = hashlib.sha256(canonical).hexdigest().upper()

with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=MANIFEST.parent, prefix="evidence_file_manifest.", suffix=".tmp") as tmp:
    writer = csv.DictWriter(tmp, fieldnames=["path", "category", "bytes", "sha256", "mtime_ns_100", "mtime_utc"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(entries)
    tmp.flush()
    os.fsync(tmp.fileno())
    manifest_tmp = Path(tmp.name)
os.replace(manifest_tmp, MANIFEST)
manifest_sha = sha256(MANIFEST)
manifest_bytes = MANIFEST.stat().st_size

for path in files:
    os.chmod(path, stat.S_IREAD)
os.chmod(MANIFEST, stat.S_IREAD)

time.sleep(0.05)
payload_count = sum(e["category"] == "payload" for e in entries)
control_count = sum(e["category"] == "control" for e in entries)
marker = {
    "uid": "FIG-P602-01",
    "round": "SA2_R3_V1_NATIVE_R1",
    "write_stopped": True,
    "sealed_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    "root": str(ROOT),
    "ordinary_files_expected": len(entries) + 2,
    "manifest_rows": len(entries),
    "manifest_model": {
        "payload": payload_count,
        "control": control_count,
        "seal": 1,
        "manifest_self": 1,
        "unique_unlisted": [
            MANIFEST.relative_to(ROOT).as_posix(),
            MARKER.relative_to(ROOT).as_posix(),
        ],
    },
    "canonical_payload_control_recordset_sha256": recordset_sha,
    "manifest": {
        "path": MANIFEST.relative_to(ROOT).as_posix(),
        "bytes": manifest_bytes,
        "sha256": manifest_sha,
    },
    "candidate_pdf_sha256": "68188DAAAF9B3C4233D5A032C3D8BE20A73B51D5E6058D0E1C12FDE6471093E7",
    "source_sha256": "6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D",
    "denominators": {
        "objects": 30,
        "glyphs": 154,
        "unordered_pairs": 435,
        "critical_pairs": 16,
        "peer_rows": 28,
        "role_rows": 3,
        "clip_rows": 30,
        "views": 4,
        "hard_gates": 12,
    },
    "machine_failures": 0,
    "manual_failures": 0,
    "root_validation": "PASS",
    "decision": "C_LOCAL_PASS_CANDIDATE_PENDING_MAIN_ACCEPTANCE",
    "tex_disabled": True,
    "central_inventory_written": False,
    "commit_created": False,
    "global_pass_claimed": False,
    "post_seal_writes_expected": 0,
}
MARKER.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=MARKER.parent, prefix="WRITE_STOPPED.", suffix=".tmp") as tmp:
    json.dump(marker, tmp, ensure_ascii=False, indent=2)
    tmp.write("\n")
    tmp.flush()
    os.fsync(tmp.fileno())
    marker_tmp = Path(tmp.name)
os.replace(marker_tmp, MARKER)
os.chmod(MARKER, stat.S_IREAD)

print(json.dumps({
    "ordinary_files_expected": len(entries) + 2,
    "manifest_rows": len(entries),
    "payload": payload_count,
    "control": control_count,
    "manifest_sha256": manifest_sha,
    "marker_sha256": sha256(MARKER),
    "recordset_sha256": recordset_sha,
}, ensure_ascii=False))
