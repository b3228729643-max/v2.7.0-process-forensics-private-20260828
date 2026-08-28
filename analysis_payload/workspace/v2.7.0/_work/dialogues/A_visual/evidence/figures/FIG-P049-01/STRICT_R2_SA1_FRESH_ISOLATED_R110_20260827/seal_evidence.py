from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MARKER = ROOT / "WRITE_STOPPED"
MANIFEST = ROOT / "FINAL_MANIFEST.csv"
SUMMARY = ROOT / "SEAL_SUMMARY.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


if MARKER.exists():
    raise SystemExit("Refusing a second seal: WRITE_STOPPED already exists")

sealed_at = now_iso()
SUMMARY.write_text(
    json.dumps(
        {
            "HANDOFF_ID": "A-R110-P049-SA1-FRESH-ISOLATED-20260827",
            "UID": "FIG-P049-01",
            "sealed_at": sealed_at,
            "RESULT": "FAIL",
            "ROUTE": "SA2",
            "VISIBLE_OBJECT_COUNT": 28,
            "UNORDERED_PAIR_COUNT": 378,
            "OVERLAP_CANDIDATE_PIXEL_COUNT": 10,
            "MASK_CONTAMINATION_PIXEL_COUNT": 10,
            "OVERLAP_PIXEL_COUNT": 0,
            "CLIP_PIXEL_COUNT": 0,
            "BLOCKERS": [
                "Guide 1 endpoint does not target P or c3.",
                "Guide lines 1 and 2 cross internally and make the callout routing ambiguous."
            ],
            "seal_contract": "All payload/control files and all directories read-only; WRITE_STOPPED is unique and the last content write; no postmarker root writes."
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

payload_files = sorted(p for p in ROOT.rglob("*") if p.is_file() and p not in (MARKER, MANIFEST))
with MANIFEST.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["relative_path", "bytes", "sha256", "last_write_time_local"])
    for p in payload_files:
        st = p.stat()
        w.writerow([
            p.relative_to(ROOT).as_posix(),
            st.st_size,
            sha256(p),
            datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds"),
        ])

all_files_before_marker = sorted(p for p in ROOT.rglob("*") if p.is_file())
for p in all_files_before_marker:
    os.chmod(p, stat.S_IREAD)
for d in sorted((p for p in ROOT.rglob("*") if p.is_dir()), reverse=True):
    os.chmod(d, stat.S_IREAD)
os.chmod(ROOT, stat.S_IREAD)

# Guarantee strict filesystem timestamp ordering before the unique final write.
time.sleep(1.1)
marker_payload = {
    "HANDOFF_ID": "A-R110-P049-SA1-FRESH-ISOLATED-20260827",
    "UID": "FIG-P049-01",
    "sealed_at": now_iso(),
    "RESULT": "FAIL",
    "ROUTE": "SA2",
    "manifest_sha256": sha256(MANIFEST),
    "payload_file_count_before_marker": len(all_files_before_marker),
    "postmarker_root_writes": 0,
}
with MARKER.open("x", encoding="utf-8") as f:
    f.write(json.dumps(marker_payload, ensure_ascii=False, indent=2) + "\n")
os.chmod(MARKER, stat.S_IREAD)

marker_mtime = MARKER.stat().st_mtime_ns
late = [p.relative_to(ROOT).as_posix() for p in all_files_before_marker if p.stat().st_mtime_ns >= marker_mtime]
markers = [p for p in ROOT.rglob("WRITE_STOPPED") if p.is_file()]
file_not_readonly = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and not (p.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)]
dir_not_readonly = [p.relative_to(ROOT).as_posix() for p in [ROOT, *(q for q in ROOT.rglob("*") if q.is_dir())] if not (p.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)]
result = {
    "marker_count": len(markers),
    "strictly_last": not late,
    "late_files": late,
    "file_not_readonly": file_not_readonly,
    "dir_not_readonly": dir_not_readonly,
    "postmarker_root_writes": 0,
    "marker": str(MARKER),
}
print(json.dumps(result, ensure_ascii=False))
if len(markers) != 1 or late or file_not_readonly or dir_not_readonly:
    raise SystemExit(2)
