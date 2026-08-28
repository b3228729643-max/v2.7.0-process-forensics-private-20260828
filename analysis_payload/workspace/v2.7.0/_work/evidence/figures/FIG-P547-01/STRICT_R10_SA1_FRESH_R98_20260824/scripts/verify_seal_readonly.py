from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R10_SA1_FRESH_R98_20260824")
MANIFEST = ROOT / "MANIFEST.csv"
WSTOP = ROOT / "WSTOP.txt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    wstop_text = WSTOP.read_text(encoding="utf-8")
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    manifest_paths = {r["RELATIVE_PATH"] for r in rows}
    actual_paths = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    expected_actual = manifest_paths | {"MANIFEST.csv", "WSTOP.txt"}
    missing = sorted(expected_actual - actual_paths)
    extra = sorted(actual_paths - expected_actual)
    duplicate_manifest_rows = len(rows) - len(manifest_paths)
    zero = sorted(p for p in actual_paths if (ROOT / p).stat().st_size == 0)
    size_mismatch = []
    hash_mismatch = []
    for r in rows:
        path = ROOT / r["RELATIVE_PATH"]
        if path.stat().st_size != int(r["BYTES"]):
            size_mismatch.append(r["RELATIVE_PATH"])
        if sha256(path) != r["SHA256"]:
            hash_mismatch.append(r["RELATIVE_PATH"])
    manifest_hash_match = re.search(r"^MANIFEST_SHA256=([0-9A-F]{64})$", wstop_text, re.M)
    manifest_bytes_match = re.search(r"^MANIFEST_BYTES=(\d+)$", wstop_text, re.M)
    recorded_payload_count = re.search(r"^PAYLOAD_FILE_COUNT=(\d+)$", wstop_text, re.M)
    recorded_full_count = re.search(r"^EXPECTED_FULL_SET_COUNT=(\d+)$", wstop_text, re.M)
    control_binding_ok = bool(
        manifest_hash_match and manifest_hash_match.group(1) == sha256(MANIFEST)
        and manifest_bytes_match and int(manifest_bytes_match.group(1)) == MANIFEST.stat().st_size
        and recorded_payload_count and int(recorded_payload_count.group(1)) == len(rows)
        and recorded_full_count and int(recorded_full_count.group(1)) == len(actual_paths)
    )
    max_non_wstop_mtime = max((ROOT / p).stat().st_mtime_ns for p in actual_paths if p != "WSTOP.txt")
    wstop_last = WSTOP.stat().st_mtime_ns >= max_non_wstop_mtime
    post_seal_writes = sum((ROOT / p).stat().st_mtime_ns > WSTOP.stat().st_mtime_ns for p in actual_paths if p != "WSTOP.txt")
    result = {
        "seal_verified": not any((missing, extra, duplicate_manifest_rows, zero, size_mismatch, hash_mismatch)) and control_binding_ok and wstop_last and post_seal_writes == 0,
        "manifest_payload_rows": len(rows), "actual_full_file_count": len(actual_paths),
        "set_equality": not missing and not extra, "missing": missing, "extra": extra,
        "duplicate_manifest_rows": duplicate_manifest_rows,
        "zero_byte_file_count": len(zero), "size_mismatch_count": len(size_mismatch),
        "hash_mismatch_count": len(hash_mismatch), "manifest_control_binding_ok": control_binding_ok,
        "wstop_last": wstop_last, "post_seal_writes": post_seal_writes,
        "terminal_status_first_line": wstop_text.splitlines()[0],
    }
    if not result["seal_verified"]:
        raise RuntimeError(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
