from __future__ import annotations

import csv
import hashlib
import json
import stat
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.sha256.csv"
MARKER = ROOT / "WRITE_STOPPED.json"
EXCLUDED = {MANIFEST, MARKER}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))

manifest_map = {row["relative_path"]: row for row in rows}
ordinary_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
expected_files = {
    path.relative_to(ROOT).as_posix(): path
    for path in ordinary_files
    if path not in EXCLUDED
}

manifest_missing_paths = sorted(set(expected_files) - set(manifest_map))
manifest_foreign_paths = sorted(set(manifest_map) - set(expected_files))
manifest_byte_mismatches: list[str] = []
manifest_hash_mismatches: list[str] = []

for relative, path in expected_files.items():
    row = manifest_map.get(relative)
    if row is None:
        continue
    if int(row["bytes"]) != path.stat().st_size:
        manifest_byte_mismatches.append(relative)
    if row["sha256"].upper() != sha256(path):
        manifest_hash_mismatches.append(relative)

all_paths = [ROOT, *ROOT.rglob("*")]
readonly_failures = []
reparse_paths = []
cache_or_pyc_paths = []
for path in all_paths:
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    if not attributes & stat.FILE_ATTRIBUTE_READONLY:
        readonly_failures.append(path.relative_to(ROOT).as_posix() or ".")
    if attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        reparse_paths.append(path.relative_to(ROOT).as_posix() or ".")
    if path.name == "__pycache__" or path.suffix.lower() == ".pyc":
        cache_or_pyc_paths.append(path.relative_to(ROOT).as_posix())

json_parse_errors: list[str] = []
csv_parse_errors: list[str] = []
png_decode_errors: list[str] = []

for path in sorted(ROOT.rglob("*.json")):
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        json_parse_errors.append(f"{path.relative_to(ROOT).as_posix()}:{exc}")

for path in sorted(ROOT.rglob("*.csv")):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            list(csv.reader(handle))
    except Exception as exc:
        csv_parse_errors.append(f"{path.relative_to(ROOT).as_posix()}:{exc}")

for path in sorted(ROOT.rglob("*.png")):
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        png_decode_errors.append(f"{path.relative_to(ROOT).as_posix()}:{exc}")

markers = [path for path in ordinary_files if path.name == "WRITE_STOPPED.json"]
marker_mtime_ns = MARKER.stat().st_mtime_ns if MARKER.exists() else -1
other_mtimes = [path.stat().st_mtime_ns for path in ordinary_files if path != MARKER]
strict_latest_marker = int(
    len(markers) == 1
    and marker_mtime_ns > max(other_mtimes, default=-1)
)
postmarker_files = [
    path.relative_to(ROOT).as_posix()
    for path in ordinary_files
    if path != MARKER and path.stat().st_mtime_ns > marker_mtime_ns
]

result = {
    "root": str(ROOT),
    "ordinary_file_count": len(ordinary_files),
    "directory_count_including_root": sum(path.is_dir() for path in all_paths),
    "manifest_rows": len(rows),
    "manifest_missing_path_count": len(manifest_missing_paths),
    "manifest_foreign_path_count": len(manifest_foreign_paths),
    "manifest_byte_mismatch_count": len(manifest_byte_mismatches),
    "manifest_hash_mismatch_count": len(manifest_hash_mismatches),
    "readonly_failure_count": len(readonly_failures),
    "write_stopped_count": len(markers),
    "strict_latest_write_stopped": strict_latest_marker,
    "postmarker_file_count": len(postmarker_files),
    "json_parse_error_count": len(json_parse_errors),
    "csv_parse_error_count": len(csv_parse_errors),
    "png_decode_error_count": len(png_decode_errors),
    "cache_or_pyc_path_count": len(cache_or_pyc_paths),
    "reparse_path_count": len(reparse_paths),
    "report": {
        "path": str(ROOT / "REPORT.md"),
        "bytes": (ROOT / "REPORT.md").stat().st_size,
        "sha256": sha256(ROOT / "REPORT.md"),
    },
    "handoff": {
        "path": str(ROOT / "HANDOFF.json"),
        "bytes": (ROOT / "HANDOFF.json").stat().st_size,
        "sha256": sha256(ROOT / "HANDOFF.json"),
    },
    "manifest": {
        "path": str(MANIFEST),
        "bytes": MANIFEST.stat().st_size,
        "sha256": sha256(MANIFEST),
    },
    "write_stopped": {
        "path": str(MARKER),
        "bytes": MARKER.stat().st_size,
        "sha256": sha256(MARKER),
    },
    "details": {
        "manifest_missing_paths": manifest_missing_paths,
        "manifest_foreign_paths": manifest_foreign_paths,
        "manifest_byte_mismatches": manifest_byte_mismatches,
        "manifest_hash_mismatches": manifest_hash_mismatches,
        "readonly_failures": readonly_failures,
        "postmarker_files": postmarker_files,
        "json_parse_errors": json_parse_errors,
        "csv_parse_errors": csv_parse_errors,
        "png_decode_errors": png_decode_errors,
        "cache_or_pyc_paths": cache_or_pyc_paths,
        "reparse_paths": reparse_paths,
    },
}

print(json.dumps(result, ensure_ascii=False, indent=2))
