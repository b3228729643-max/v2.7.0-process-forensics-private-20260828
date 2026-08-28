from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "evidence_file_manifest.csv"
MARKER = ROOT / "WRITE_STOPPED.json"
PAYLOAD_NAMES = ["HANDOFF.md", "IDENTITY.json", "seal_handoff.py"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def require_identity(path: Path, expected_bytes: int, expected_sha256: str) -> None:
    if not path.is_file():
        raise SystemExit(f"missing identity target: {path}")
    if path.stat().st_size != expected_bytes or sha256(path) != expected_sha256:
        raise SystemExit(f"identity mismatch: {path}")


if MANIFEST.exists() or MARKER.exists():
    raise SystemExit("handoff root already sealed")

actual_names = sorted(path.name for path in ROOT.iterdir() if path.is_file())
if actual_names != sorted(PAYLOAD_NAMES):
    raise SystemExit(f"unexpected pre-seal files: {actual_names}")

identity = json.loads((ROOT / "IDENTITY.json").read_text(encoding="utf-8"))
if identity["status"] != "P602_R3_SEALED_READY_FOR_MAIN" or identity["unresolved"] != "NONE":
    raise SystemExit("handoff status is not final")

worktree = Path("D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/worktrees/dialogue_C_visual")
git_env = os.environ.copy()
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree, check=True, text=True, encoding="utf-8", capture_output=True, env=git_env).stdout.strip()
parent = subprocess.run(["git", "rev-parse", "HEAD^"], cwd=worktree, check=True, text=True, encoding="utf-8", capture_output=True, env=git_env).stdout.strip()
status = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain"], cwd=worktree, check=True, text=True, encoding="utf-8", capture_output=True, env=git_env).stdout
changed = [line for line in subprocess.run(["git", "-c", "core.quotepath=false", "show", "--format=", "--name-only", "HEAD"], cwd=worktree, check=True, text=True, encoding="utf-8", capture_output=True, env=git_env).stdout.splitlines() if line]
if head != identity["commit"]["sha"] or parent != identity["commit"]["parent_sha"]:
    raise SystemExit("commit or parent mismatch")
if status:
    raise SystemExit("worktree is not clean")
if changed != [identity["source"]["repository_path"]]:
    raise SystemExit(f"commit scope mismatch: {changed}")

require_identity(Path(identity["source"]["path"]), identity["source"]["bytes"], identity["source"]["sha256"])
require_identity(Path(identity["candidate_pdf"]["path"]), identity["candidate_pdf"]["bytes"], identity["candidate_pdf"]["sha256"])

evidence_root = Path(identity["sealed_evidence_root"]["path"])
require_identity(evidence_root / identity["sealed_evidence_root"]["manifest_path"], identity["sealed_evidence_root"]["manifest_bytes"], identity["sealed_evidence_root"]["manifest_sha256"])
require_identity(evidence_root / identity["sealed_evidence_root"]["write_stopped_path"], identity["sealed_evidence_root"]["write_stopped_bytes"], identity["sealed_evidence_root"]["write_stopped_sha256"])

acceptance_root = Path(identity["fresh_root_acceptance"]["path"])
require_identity(acceptance_root / "ROOT_ACCEPTANCE.json", identity["fresh_root_acceptance"]["root_acceptance_bytes"], identity["fresh_root_acceptance"]["root_acceptance_sha256"])
require_identity(acceptance_root / "HANDOFF.md", identity["fresh_root_acceptance"]["handoff_bytes"], identity["fresh_root_acceptance"]["handoff_sha256"])
require_identity(acceptance_root / "WRITE_STOPPED.json", identity["fresh_root_acceptance"]["write_stopped_bytes"], identity["fresh_root_acceptance"]["write_stopped_sha256"])

r168_root = Path(identity["r168_route_addendum"]["path"])
require_identity(r168_root / "evidence_file_manifest.csv", identity["r168_route_addendum"]["manifest_bytes"], identity["r168_route_addendum"]["manifest_sha256"])
require_identity(r168_root / "ROUTE_ADDENDUM.json", identity["r168_route_addendum"]["route_addendum_bytes"], identity["r168_route_addendum"]["route_addendum_sha256"])
require_identity(r168_root / "HANDOFF.md", identity["r168_route_addendum"]["handoff_bytes"], identity["r168_route_addendum"]["handoff_sha256"])
require_identity(r168_root / "WRITE_STOPPED.json", identity["r168_route_addendum"]["write_stopped_bytes"], identity["r168_route_addendum"]["write_stopped_sha256"])

files = [ROOT / name for name in PAYLOAD_NAMES]
rows: list[dict[str, object]] = []
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

time.sleep(0.1)
marker = {
    "schema": "P602_R3_COMMIT_HANDOFF_WRITE_STOPPED_V1",
    "status": "P602_R3_SEALED_READY_FOR_MAIN",
    "uid": "FIG-P602-01",
    "write_stopped": True,
    "sealed_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    "root": str(ROOT),
    "ordinary_files_expected": 5,
    "manifest_rows": 3,
    "unique_unlisted": ["evidence_file_manifest.csv", "WRITE_STOPPED.json"],
    "canonical_recordset_sha256": recordset_sha256,
    "manifest_bytes": MANIFEST.stat().st_size,
    "manifest_sha256": manifest_sha256,
    "identity_sha256": sha256(ROOT / "IDENTITY.json"),
    "handoff_sha256": sha256(ROOT / "HANDOFF.md"),
    "commit_sha": head,
    "parent_sha": parent,
    "source_sha256": identity["source"]["sha256"],
    "candidate_pdf_sha256": identity["candidate_pdf"]["sha256"],
    "strict_original_route": "PASS",
    "r168_user_route": "PASS",
    "unresolved": "NONE",
    "tex_disabled": True,
    "central_state_written": False,
    "central_inventory_written": False,
    "second_commit_performed": False,
    "fresh_role_started": False,
    "next_business_source_started": False,
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
    "identity_sha256": sha256(ROOT / "IDENTITY.json"),
    "handoff_sha256": sha256(ROOT / "HANDOFF.md"),
    "commit_sha": head,
    "parent_sha": parent,
    "unresolved": "NONE",
}, ensure_ascii=False))
