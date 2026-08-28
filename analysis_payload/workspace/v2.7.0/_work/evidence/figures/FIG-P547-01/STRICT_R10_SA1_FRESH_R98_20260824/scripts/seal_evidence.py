from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R10_SA1_FRESH_R98_20260824")
MANIFEST = ROOT / "MANIFEST.csv"
WSTOP = ROOT / "WSTOP.txt"
STATUS = "SA1_PASS_TO_FRESH_ISOLATED_SA3_NOT_FINAL"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def iso_utc_ns(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1_000_000_000, timezone.utc).isoformat(timespec="microseconds")


def write_fsynced(path: Path, data: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def main() -> None:
    if MANIFEST.exists() or WSTOP.exists():
        raise RuntimeError("Refusing to reseal: MANIFEST.csv or WSTOP.txt already exists")
    payload = sorted(
        (p for p in ROOT.rglob("*") if p.is_file() and p not in {MANIFEST, WSTOP}),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    if not payload:
        raise RuntimeError("No payload files")
    zero = [p for p in payload if p.stat().st_size == 0]
    if zero:
        raise RuntimeError(f"Zero-byte payload files: {zero}")
    rows = []
    for path in payload:
        stat = path.stat()
        rows.append({
            "RELATIVE_PATH": path.relative_to(ROOT).as_posix(),
            "BYTES": stat.st_size,
            "SHA256": sha256(path),
            "LAST_WRITE_UTC": iso_utc_ns(stat.st_mtime_ns),
            "LAST_WRITE_NS": stat.st_mtime_ns,
        })
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        f.flush()
        os.fsync(f.fileno())
    manifest_bytes = MANIFEST.stat().st_size
    manifest_hash = sha256(MANIFEST)
    manifest_mtime_ns = MANIFEST.stat().st_mtime_ns
    max_payload_mtime_ns = max(p.stat().st_mtime_ns for p in payload)
    if manifest_mtime_ns < max_payload_mtime_ns:
        raise RuntimeError("Manifest is not newer than every payload file")
    seal_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    wstop_text = (
        f"{STATUS}\n"
        "FIGURE_ID=FIG-P547-01\n"
        "EVIDENCE_STATE=SEALED_READ_ONLY_BY_PROTOCOL\n"
        f"SEALED_UTC={seal_utc}\n"
        f"PAYLOAD_FILE_COUNT={len(payload)}\n"
        f"EXPECTED_FULL_SET_COUNT={len(payload) + 2}\n"
        "CONTROL_FILES=MANIFEST.csv;WSTOP.txt\n"
        "SET_EQUALITY=actual_full_set == manifest_payload_set union {MANIFEST.csv,WSTOP.txt}\n"
        "ZERO_BYTE_FILE_COUNT=0\n"
        "POST_SEAL_WRITES=0\n"
        "WSTOP_LAST=true\n"
        f"MANIFEST_BYTES={manifest_bytes}\n"
        f"MANIFEST_SHA256={manifest_hash}\n"
        "MANIFEST_SELF_HASH_POLICY=manifest lists every payload file; WSTOP binds MANIFEST bytes and SHA256; control files are excluded from manifest rows\n"
        "NEXT_ROUTE=fresh isolated SA3 only; SA1 did not dispatch SA3; not final acceptance\n"
    )
    write_fsynced(WSTOP, wstop_text)
    if WSTOP.stat().st_mtime_ns < MANIFEST.stat().st_mtime_ns:
        raise RuntimeError("WSTOP is not last")
    # No writes are permitted after this point.
    print(STATUS)
    print(f"PAYLOAD_FILE_COUNT={len(payload)}")
    print(f"MANIFEST_SHA256={manifest_hash}")
    print("WSTOP_LAST=true")


if __name__ == "__main__":
    main()
