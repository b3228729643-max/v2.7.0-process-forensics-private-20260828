#!/usr/bin/env python3
"""Seal the R21 lean evidence root without creating or changing manual fields."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from PIL import Image

ROOT = Path(__file__).resolve().parent
JSON_MANIFEST = ROOT / "PAYLOAD_MANIFEST.json"
CSV_MANIFEST = ROOT / "SHA256_MANIFEST.csv"
AUDIT = ROOT / "FINAL_FILESYSTEM_AUDIT.json"
SENTINEL = ROOT / "WRITE_STOPPED.md"
CONTROLS = {JSON_MANIFEST, CSV_MANIFEST, SENTINEL}
WINDOWS_EPOCH_TICKS = 116_444_736_000_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def ticks(path: Path) -> str:
    return str(path.stat().st_mtime_ns // 100 + WINDOWS_EPOCH_TICKS)


def utc7(path: Path) -> str:
    value = path.stat().st_mtime_ns
    seconds, remainder = divmod(value, 1_000_000_000)
    head = datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{head}.{remainder // 100:07d}Z"


def payload_files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob("*")) if p.is_file() and p not in CONTROLS]


def all_files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob("*")) if p.is_file()]


def stream_audit() -> dict:
    root = str(ROOT).replace("'", "''")
    code = (
        f"$files=Get-ChildItem -LiteralPath '{root}' -Recurse -File;"
        "$ads=@();foreach($f in $files){foreach($s in (Get-Item -LiteralPath $f.FullName -Stream *)){"
        "if($s.Stream -ne ':$DATA' -and $s.Stream -ne '::$DATA'){"
        "$ads += [pscustomobject]@{file=$f.FullName;stream=$s.Stream;length=$s.Length}}}};"
        f"$dirs=Get-ChildItem -LiteralPath '{root}' -Recurse -Directory;"
        "[pscustomobject]@{ordinary_file_count=$files.Count;ads_count=$ads.Count;ads=$ads;"
        "pyc_count=($files|Where-Object {$_.Extension -in '.pyc','.pyo'}).Count;"
        "cache_dir_count=($dirs|Where-Object {$_.Name -eq '__pycache__'}).Count;"
        "colon_filename_count=($files|Where-Object {$_.Name -match ':'}).Count}|ConvertTo-Json -Depth 5 -Compress"
    )
    completed = subprocess.run(
        ["D:\\PowerShell7\\pwsh.exe", "-NoProfile", "-Command", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(completed.stdout)


def parse_status(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        json.loads(path.read_text(encoding="utf-8"))
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            list(csv.reader(stream))
    elif suffix == ".png":
        with Image.open(path) as image:
            image.verify()
    elif suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        if len(reader.pages) < 1:
            raise RuntimeError(f"PDF has no pages: {path}")
    else:
        with path.open("rb") as stream:
            stream.read(1)
    return "OPEN_OK"


def entry(path: Path) -> dict:
    return {
        "relative_path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "mtime_utc_ticks": ticks(path),
        "mtime_utc_7digit": utc7(path),
        "suffix": path.suffix.lower(),
        "parse_status": parse_status(path),
    }


def extension_counts(paths: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        key = path.suffix.lower() or "<none>"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def validate_manifest(entries: list[dict]) -> None:
    json_document = json.loads(JSON_MANIFEST.read_text(encoding="utf-8"))
    json_rows = json_document["entries"]
    with CSV_MANIFEST.open("r", encoding="utf-8-sig", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    if len(entries) != len(json_rows) or len(entries) != len(csv_rows):
        raise RuntimeError("manifest row denominator mismatch")
    json_by_path = {row["relative_path"]: row for row in json_rows}
    csv_by_path = {row["relative_path"]: row for row in csv_rows}
    if len(json_by_path) != len(entries) or len(csv_by_path) != len(entries):
        raise RuntimeError("duplicate path in manifest")
    expected_paths = {row["relative_path"] for row in entries}
    if set(json_by_path) != expected_paths or set(csv_by_path) != expected_paths:
        raise RuntimeError("manifest path-set mismatch")
    for expected in entries:
        path = expected["relative_path"]
        for field in ("bytes", "sha256", "mtime_utc_ticks", "mtime_utc_7digit", "suffix", "parse_status"):
            if str(json_by_path[path][field]) != str(expected[field]):
                raise RuntimeError(f"JSON manifest mismatch: {path} {field}")
            if str(csv_by_path[path][field]) != str(expected[field]):
                raise RuntimeError(f"CSV manifest mismatch: {path} {field}")


def main() -> None:
    existing_controls = [p.name for p in CONTROLS if p.exists()]
    if existing_controls:
        raise RuntimeError(f"refusing to overwrite existing controls: {existing_controls}")
    pre = stream_audit()
    if any(pre[key] for key in ("ads_count", "pyc_count", "cache_dir_count", "colon_filename_count")):
        raise RuntimeError(f"pre-seal filesystem audit failed: {pre}")

    before_audit_count = len(payload_files())
    audit = {
        "figure_uid": "FIG-P654-01",
        "round": "R21",
        "policy": "USER_FONT_REVIEW_RELAXATION_R168",
        "stage": "immediately before manifests and WRITE_STOPPED",
        "ordinary_files_before_audit": before_audit_count,
        "expected_payload_files": before_audit_count + 1,
        "expected_control_files": 3,
        "expected_final_ordinary_files": before_audit_count + 4,
        "preseal_filesystem": pre,
        "hard_gate_result": "PASS",
        "route": "P654_R21_LEAN_LOCAL_PASS_READY_REQUEST_COMMIT",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    paths = payload_files()
    entries = [entry(path) for path in paths]
    manifest = {
        "manifest_id": "FIG-P654-01-R21-R168-LEAN-PAYLOAD",
        "scope": "Every ordinary payload file except the two manifests and WRITE_STOPPED.",
        "excluded_controls": ["PAYLOAD_MANIFEST.json", "SHA256_MANIFEST.csv", "WRITE_STOPPED.md"],
        "payload_file_count": len(entries),
        "payload_byte_sum": sum(row["bytes"] for row in entries),
        "payload_extension_counts": extension_counts(paths),
        "all_payload_parse_open": all(row["parse_status"] == "OPEN_OK" for row in entries),
        "entries": entries,
    }
    JSON_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    with CSV_MANIFEST.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["relative_path", "bytes", "sha256", "mtime_utc_ticks", "mtime_utc_7digit", "suffix", "parse_status"],
        )
        writer.writeheader()
        writer.writerows(entries)

    validate_manifest(entries)
    final_pre = stream_audit()
    if any(final_pre[key] for key in ("ads_count", "pyc_count", "cache_dir_count", "colon_filename_count")):
        raise RuntimeError(f"pre-sentinel filesystem audit failed: {final_pre}")
    expected_final = len(entries) + 3
    if final_pre["ordinary_file_count"] + 1 != expected_final:
        raise RuntimeError("final ordinary denominator mismatch")

    payload_ext = extension_counts(paths)
    control_ext = {".csv": 1, ".json": 1, ".md": 1}
    ordinary_ext = dict(payload_ext)
    for key, value in control_ext.items():
        ordinary_ext[key] = ordinary_ext.get(key, 0) + value
    sentinel = (
        "# WRITE_STOPPED — FIG-P654-01 R21 lean R168\n\n"
        "- VERDICT: `P654_R21_LEAN_LOCAL_PASS_READY_REQUEST_COMMIT`\n"
        f"- payload_file_count: {len(entries)}\n"
        "- manifest_control_file_count: 2\n"
        "- write_stopped_control_file_count: 1\n"
        "- control_file_count: 3\n"
        f"- ordinary_file_total: {expected_final}\n"
        f"- payload_extension_counts: `{json.dumps(payload_ext, ensure_ascii=False, sort_keys=True)}`\n"
        f"- control_extension_counts: `{json.dumps(control_ext, ensure_ascii=False, sort_keys=True)}`\n"
        f"- ordinary_extension_counts: `{json.dumps(dict(sorted(ordinary_ext.items())), ensure_ascii=False, sort_keys=True)}`\n"
        f"- PAYLOAD_MANIFEST SHA-256: `{sha256(JSON_MANIFEST)}`\n"
        f"- SHA256_MANIFEST SHA-256: `{sha256(CSV_MANIFEST)}`\n"
        "- dual manifest and live filesystem path/bytes/SHA-256/NTFS ticks: zero differences before this sentinel\n"
        "- ADS / pyc / cache dirs / colon filenames: 0 / 0 / 0 / 0\n"
        "- all payload files parse/open: true\n"
        "- all files set read-only after this sentinel write: true\n"
        "- post-seal writes, imports, or execution inside this root are forbidden\n"
        "- this sentinel is the strict latest filesystem write in the evidence root\n"
    )
    SENTINEL.write_text(sentinel, encoding="utf-8", newline="\n")
    other_latest = max(path.stat().st_mtime_ns for path in all_files() if path != SENTINEL)
    desired = max(time.time_ns(), other_latest + 100)
    os.utime(SENTINEL, ns=(desired, desired))
    sentinel_mtime = SENTINEL.stat().st_mtime_ns
    if any(path.stat().st_mtime_ns >= sentinel_mtime for path in all_files() if path != SENTINEL):
        raise RuntimeError("WRITE_STOPPED is not strictly latest")

    for path in all_files():
        os.chmod(path, stat.S_IREAD)
    print(json.dumps({
        "verdict": "P654_R21_LEAN_LOCAL_PASS_READY_REQUEST_COMMIT",
        "payload_files": len(entries),
        "control_files": 3,
        "ordinary_files": expected_final,
        "payload_extensions": payload_ext,
        "control_extensions": control_ext,
        "ordinary_extensions": ordinary_ext,
        "json_manifest_sha256": sha256(JSON_MANIFEST),
        "csv_manifest_sha256": sha256(CSV_MANIFEST),
        "write_stopped_mtime_ns": sentinel_mtime,
        "readonly_applied": True,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
