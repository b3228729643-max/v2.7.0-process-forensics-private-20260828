from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "09_manifest" / "evidence_file_manifest.csv"
MARKER = ROOT / "WRITE_STOPPED.json"
MANIFEST_REL = MANIFEST.relative_to(ROOT).as_posix()
MARKER_REL = MARKER.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def category(rel: str) -> str:
    control_prefixes = ("identity/", "qa/", "scripts/")
    control_names = {
        "MANUAL_REVIEW_PROTOCOL.md",
        "SA2_R2_NATIVE_REVIEW.md",
        "HANDOFF.md",
    }
    if rel.startswith(control_prefixes) or rel in control_names:
        return "CONTROL"
    return "PAYLOAD"


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    if temp.exists():
        raise RuntimeError(f"unexpected temporary path: {temp}")
    with temp.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


if MANIFEST.exists() or MARKER.exists():
    raise SystemExit("seal refused: manifest or WRITE_STOPPED already exists")

all_before = sorted(
    path
    for path in ROOT.rglob("*")
    if path.is_file()
    and path.relative_to(ROOT).as_posix() not in {MANIFEST_REL, MARKER_REL}
    and not path.name.endswith(".tmp")
)

rows: list[dict[str, object]] = []
for path in all_before:
    rel = path.relative_to(ROOT).as_posix()
    file_stat = path.stat()
    rows.append(
        {
            "category": category(rel),
            "path": rel,
            "bytes": file_stat.st_size,
            "sha256": sha256(path),
            "mtime_utc": datetime.fromtimestamp(file_stat.st_mtime_ns / 1_000_000_000, timezone.utc).isoformat(),
            "mtime_ns": file_stat.st_mtime_ns,
        }
    )

if len({str(row["path"]) for row in rows}) != len(rows):
    raise RuntimeError("duplicate manifest path")

manifest_temp = MANIFEST.with_name(MANIFEST.name + ".render")
if manifest_temp.exists():
    raise RuntimeError(f"unexpected manifest render path: {manifest_temp}")
MANIFEST.parent.mkdir(parents=True, exist_ok=True)
with manifest_temp.open("x", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=["category", "path", "bytes", "sha256", "mtime_utc", "mtime_ns"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    handle.flush()
    os.fsync(handle.fileno())
os.replace(manifest_temp, MANIFEST)

recordset = "".join(
    f'{row["category"]}|{row["path"]}|{row["bytes"]}|{row["sha256"]}|{row["mtime_ns"]}\n'
    for row in rows
).encode("utf-8")
recordset_sha = hashlib.sha256(recordset).hexdigest().upper()
manifest_sha = sha256(MANIFEST)
payload_count = sum(row["category"] == "PAYLOAD" for row in rows)
control_count = sum(row["category"] == "CONTROL" for row in rows)
pre_seal_latest_mtime_ns = max(int(row["mtime_ns"]) for row in rows)

for path in [*all_before, MANIFEST]:
    path.chmod(path.stat().st_mode & ~stat.S_IWRITE)

time.sleep(0.05)
marker = {
    "uid": "FIG-P602-01",
    "round": "SA2_R2_V3C_NATIVE_R1",
    "seal_status": "WRITE_STOPPED",
    "sealed_root": str(ROOT),
    "write_stopped_utc": datetime.now(timezone.utc).isoformat(),
    "final_evidence_outcome": "STRICT_FAIL_G032_H06",
    "local_pass_claimed": False,
    "central_state_write_authorized": False,
    "tex_invocations_in_native_evidence_phase": 0,
    "candidate_pdf": {
        "bytes": 41240,
        "sha256": "203977543DB0F41686A955D33D83A55BA272A7AAE07599AED58227914019EE2C",
    },
    "source_sha256": "2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349",
    "denominators": {
        "objects": 30,
        "glyphs": 154,
        "unordered_pairs": 435,
        "critical_pairs": 16,
        "peers": 28,
        "roles": 3,
        "clips": 30,
        "views": 4,
        "hard_gates": 12,
    },
    "final_manual_ledger_state": {
        "objects": "30_UNIQUE_PASS",
        "glyph_visual": "154_UNIQUE_PASS",
        "glyph_hard": "153_PASS_1_FAIL_G032",
        "pairs": "435_UNIQUE_PASS",
        "critical_pairs": "16_UNIQUE_PASS",
        "peers": "28_UNIQUE_PASS",
        "roles": "3_UNIQUE_PASS",
        "clips": "30_UNIQUE_PASS",
        "views": "4_UNIQUE_PASS",
        "hard_gates": "11_PASS_1_FAIL_H06",
    },
    "strict_failure": {
        "glyph_id": "G032",
        "char": "一",
        "unicode": "U+4E00",
        "script_class": "CJK_FULL",
        "ink_width_px": 36,
        "ink_height_px": 4,
        "ink_pixel_count": 78,
        "required_height_px": 30,
        "manual_visual_decision": "PASS",
        "hard_gate_decision": "FAIL",
        "failed_gate": "H06",
    },
    "manifest_model": {
        "listed_payload": payload_count,
        "listed_control": control_count,
        "listed_rows": len(rows),
        "unlisted_self": 1,
        "unlisted_seal": 1,
        "expected_final_ordinary_files": len(rows) + 2,
        "unlisted_paths": [MANIFEST_REL, MARKER_REL],
        "manifest_path": MANIFEST_REL,
        "manifest_bytes": MANIFEST.stat().st_size,
        "manifest_sha256": manifest_sha,
        "canonical_listed_recordset_sha256": recordset_sha,
        "pre_seal_latest_listed_mtime_ns": pre_seal_latest_mtime_ns,
    },
    "post_seal_policy": "No file in this root may be modified, added, removed, or regenerated. Acceptance must use a separate fresh root.",
}
atomic_write_bytes(MARKER, (json.dumps(marker, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
MARKER.chmod(MARKER.stat().st_mode & ~stat.S_IWRITE)

final_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
marker_mtime_ns = MARKER.stat().st_mtime_ns
if len(final_files) != len(rows) + 2:
    raise RuntimeError("post-seal ordinary-file count mismatch")
if marker_mtime_ns <= max(path.stat().st_mtime_ns for path in final_files if path != MARKER):
    raise RuntimeError("WRITE_STOPPED is not strictly latest")

print(
    json.dumps(
        {
            "root": str(ROOT),
            "ordinary_files": len(final_files),
            "manifest_rows": len(rows),
            "payload": payload_count,
            "control": control_count,
            "self": 1,
            "seal": 1,
            "manifest_sha256": manifest_sha,
            "recordset_sha256": recordset_sha,
            "marker_sha256": sha256(MARKER),
            "marker_strictly_latest": True,
        },
        ensure_ascii=False,
    )
)
