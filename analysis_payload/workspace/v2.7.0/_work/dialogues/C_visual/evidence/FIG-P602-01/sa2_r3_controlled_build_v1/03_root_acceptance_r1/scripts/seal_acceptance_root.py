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
MANIFEST = ROOT / "evidence_file_manifest.csv"
MARKER = ROOT / "WRITE_STOPPED.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


if MANIFEST.exists() or MARKER.exists():
    raise SystemExit("acceptance root already sealed")

files = sorted((p for p in ROOT.rglob("*") if p.is_file() and p not in {MANIFEST, MARKER}), key=lambda p: p.relative_to(ROOT).as_posix())
entries: list[dict[str, object]] = []
for path in files:
    st = path.stat()
    entries.append({
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": st.st_size,
        "sha256": sha256(path),
        "mtime_ns_100": st.st_mtime_ns // 100,
        "mtime_utc": datetime.fromtimestamp(st.st_mtime_ns / 1_000_000_000, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    })

canonical = "".join(f"{r['path']}|{r['bytes']}|{r['sha256']}|{r['mtime_ns_100']}\n" for r in entries).encode("utf-8")
recordset_sha = hashlib.sha256(canonical).hexdigest().upper()
with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=ROOT, prefix="evidence_file_manifest.", suffix=".tmp") as tmp:
    writer = csv.DictWriter(tmp, fieldnames=["path", "bytes", "sha256", "mtime_ns_100", "mtime_utc"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(entries)
    tmp.flush()
    os.fsync(tmp.fileno())
    temp_manifest = Path(tmp.name)
os.replace(temp_manifest, MANIFEST)
manifest_sha = sha256(MANIFEST)
for path in files:
    os.chmod(path, stat.S_IREAD)
os.chmod(MANIFEST, stat.S_IREAD)

time.sleep(0.05)
marker = {
    "audit_id": "C-FIG-P602-01-SA2-R3-V1-ROOT-ACCEPTANCE-R1",
    "write_stopped": True,
    "sealed_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    "root": str(ROOT),
    "ordinary_files_expected": len(entries) + 2,
    "manifest_rows": len(entries),
    "unique_unlisted": ["evidence_file_manifest.csv", "WRITE_STOPPED.json"],
    "canonical_recordset_sha256": recordset_sha,
    "manifest_bytes": MANIFEST.stat().st_size,
    "manifest_sha256": manifest_sha,
    "root_acceptance_bytes": (ROOT / "ROOT_ACCEPTANCE.json").stat().st_size,
    "root_acceptance_sha256": sha256(ROOT / "ROOT_ACCEPTANCE.json"),
    "handoff_bytes": (ROOT / "HANDOFF.md").stat().st_size,
    "handoff_sha256": sha256(ROOT / "HANDOFF.md"),
    "accepted_status": "C_LOCAL_PASS_CANDIDATE_PENDING_MAIN_ACCEPTANCE",
    "tex_disabled": True,
    "central_inventory_written": False,
    "commit_created": False,
    "global_pass_claimed": False,
    "post_seal_writes_expected": 0
}
with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=ROOT, prefix="WRITE_STOPPED.", suffix=".tmp") as tmp:
    json.dump(marker, tmp, ensure_ascii=False, indent=2)
    tmp.write("\n")
    tmp.flush()
    os.fsync(tmp.fileno())
    temp_marker = Path(tmp.name)
os.replace(temp_marker, MARKER)
os.chmod(MARKER, stat.S_IREAD)
print(json.dumps({
    "ordinary_files_expected": len(entries) + 2,
    "manifest_rows": len(entries),
    "manifest_sha256": manifest_sha,
    "marker_sha256": sha256(MARKER),
    "recordset_sha256": recordset_sha,
    "root_acceptance_sha256": sha256(ROOT / "ROOT_ACCEPTANCE.json"),
    "handoff_sha256": sha256(ROOT / "HANDOFF.md")
}, ensure_ascii=False))
