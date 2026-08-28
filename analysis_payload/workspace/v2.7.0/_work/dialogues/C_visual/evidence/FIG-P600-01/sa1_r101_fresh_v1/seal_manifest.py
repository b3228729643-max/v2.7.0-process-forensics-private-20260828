from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa1_r101_fresh_v1")
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
MARKER_TMP = ROOT / ".WRITE_STOPPED.tmp"

CONTROL_NAMES = {
    "analyze_machine.py",
    "seal_manifest.py",
    "protocol_applied.md",
    "identity_and_localization.json",
    "machine_summary.txt",
    "pdfinfo.txt",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def canonical_record(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def make_readonly(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def main() -> None:
    if MANIFEST.exists() or MARKER.exists() or MARKER_TMP.exists():
        raise RuntimeError("seal artifacts already exist; refusing to reseal")
    if any(p.is_dir() for p in ROOT.iterdir()):
        raise RuntimeError("unexpected subdirectory in flat evidence root")

    ordinary_paths = sorted((p for p in ROOT.iterdir() if p.is_file()), key=lambda p: p.name.casefold())
    if len(ordinary_paths) != 50:
        raise RuntimeError(f"ordinary denominator mismatch: expected 50, got {len(ordinary_paths)}")
    actual_control = {p.name for p in ordinary_paths if p.name in CONTROL_NAMES}
    if actual_control != CONTROL_NAMES:
        raise RuntimeError(f"control set mismatch: {sorted(actual_control)}")

    payload_count = len(ordinary_paths) - len(CONTROL_NAMES)
    control_count = len(CONTROL_NAMES)
    ordinary_count = len(ordinary_paths)
    total_manifest_model_count = ordinary_count + 1 + 1

    marker_text = (
        "WRITE_STOPPED\n"
        "UID=FIG-P600-01\n"
        "ROLE=SA1_FRESH_READ_ONLY_R101\n"
        "RESULT=FAIL\n"
        "FAILED_IDS=S07,H07_TEXT_CONSISTENCY,H14_FINAL\n"
        "REQUIRES_FIGURE_SOURCE_WRITER=NO\n"
        "REQUIRES_CHAPTER_TEXT_WRITER=YES\n"
        "REQUIRES_FUTURE_TEX_SLOT=YES\n"
        f"PAYLOAD_COUNT={payload_count}\n"
        f"CONTROL_COUNT={control_count}\n"
        f"ORDINARY_COUNT={ordinary_count}\n"
        "SEAL_COUNT=1\n"
        "SELF_COUNT=1\n"
        f"MANIFEST_MODEL_COUNT={total_manifest_model_count}\n"
        "UNLISTED_COUNT=0\n"
        "ADS_COUNT=0\n"
        "CACHE_PYC_COUNT=0\n"
        "POST_SEAL_WRITES=0\n"
    )
    marker_bytes = marker_text.encode("utf-8")
    marker_sha = sha256_bytes(marker_bytes)

    # Prepare and protect the marker before the manifest.  The final rename below
    # is intentionally the last filesystem mutation in this script.
    with MARKER_TMP.open("xb") as f:
        f.write(marker_bytes)
        f.flush()
        os.fsync(f.fileno())
    make_readonly(MARKER_TMP)

    ordinary_records = []
    for path in ordinary_paths:
        st = path.stat()
        ordinary_records.append({
            "path": path.name,
            "class": "control" if path.name in CONTROL_NAMES else "payload",
            "bytes": st.st_size,
            "sha256": sha256_file(path),
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        })

    seal_record = {
        "path": MARKER.name,
        "class": "seal",
        "bytes": len(marker_bytes),
        "sha256": marker_sha,
    }
    recordset_input = "".join(canonical_record(r) + "\n" for r in ordinary_records + [seal_record]).encode("utf-8")
    recordset_sha = sha256_bytes(recordset_input)

    manifest = {
        "schema": "FIGURE_SA1_EVIDENCE_MANIFEST_V1",
        "uid": "FIG-P600-01",
        "task_row": "B51",
        "figure_number": "32.4",
        "role": "SA1 fresh isolated read-only R101",
        "result": "FAIL",
        "failed_ids": ["S07", "H07_TEXT_CONSISTENCY", "H14_FINAL"],
        "counts": {
            "payload": payload_count,
            "control": control_count,
            "ordinary": ordinary_count,
            "seal": 1,
            "self": 1,
            "manifest_model_total": total_manifest_model_count,
            "unlisted": 0,
            "ads": 0,
            "cache_pyc": 0,
        },
        "coverage": {
            "semantic_objects": 22,
            "unordered_pairs": 231,
            "glyphs": 133,
            "critical_candidates": 24,
            "peer_role_assignments": 10,
            "peer_comparisons": 4,
            "clip_objects": 22,
            "views": 6,
            "hard_gates": 14,
        },
        "recordset_sha256": recordset_sha,
        "recordset_scope": "canonical JSON lines for all ordinary records plus expected seal record; manifest self excluded to avoid self-hash recursion",
        "ordinary_files": ordinary_records,
        "seal_file": seal_record,
        "self_file": {
            "path": MANIFEST.name,
            "class": "self",
            "sha256": "EXTERNAL_AFTER_WRITE",
        },
        "unlisted_files": [],
        "post_seal_write_policy": "WRITE_STOPPED is introduced by the final rename; zero filesystem writes are permitted afterward",
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with MANIFEST.open("xb") as f:
        f.write(manifest_bytes)
        f.flush()
        os.fsync(f.fileno())

    for path in ordinary_paths:
        make_readonly(path)
    make_readonly(MANIFEST)

    manifest_sha = sha256_bytes(manifest_bytes)
    # Strictly last mutation: rename the already read-only, fully written marker.
    os.replace(MARKER_TMP, MARKER)

    # Console output only; no file operations that mutate state follow the rename.
    print(json.dumps({
        "payload": payload_count,
        "control": control_count,
        "ordinary": ordinary_count,
        "seal": 1,
        "self": 1,
        "manifest_model_total": total_manifest_model_count,
        "unlisted": 0,
        "manifest_sha256": manifest_sha,
        "marker_sha256": marker_sha,
        "recordset_sha256": recordset_sha,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
