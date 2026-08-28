from __future__ import annotations

import csv
import ctypes
import hashlib
import os
import stat
import time
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa1_r114_fresh_isolated_v1")
STAGE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa1_r114_fresh_isolated_v1.WRITE_STOPPED.stage")
AUDIT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa1_r114_fresh_isolated_v1.seal_audit.txt")
MANIFEST = ROOT / "MANIFEST.csv"
MARKER = ROOT / "WRITE_STOPPED"
EXPECTED_DIRS = {"machine", "renders"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class Win32FindStreamData(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_longlong), ("StreamName", ctypes.c_wchar * 296)]


def alternate_streams(path: Path) -> list[str]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    find_first = kernel32.FindFirstStreamW
    find_first.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(Win32FindStreamData), ctypes.c_ulong]
    find_first.restype = ctypes.c_void_p
    find_next = kernel32.FindNextStreamW
    find_next.argtypes = [ctypes.c_void_p, ctypes.POINTER(Win32FindStreamData)]
    find_next.restype = ctypes.c_int
    find_close = kernel32.FindClose
    find_close.argtypes = [ctypes.c_void_p]
    find_close.restype = ctypes.c_int
    data = Win32FindStreamData()
    invalid = ctypes.c_void_p(-1).value
    handle = find_first(str(path), 0, ctypes.byref(data), 0)
    if handle == invalid:
        return []
    names = [data.StreamName]
    try:
        while find_next(handle, ctypes.byref(data)):
            names.append(data.StreamName)
    finally:
        find_close(handle)
    return [name for name in names if name != "::$DATA"]


raw_marker = MARKER.read_bytes()
utf8_no_bom = not raw_marker.startswith(b"\xef\xbb\xbf")
marker_text = raw_marker.decode("utf-8")
physical_lines = marker_text.splitlines()
nonempty_lines = [line for line in physical_lines if line]
bad_lines = [line for line in physical_lines if not line or line.count("=") != 1 or not all(line.split("=", 1))]
parsed = dict(line.split("=", 1) for line in nonempty_lines if line.count("=") == 1)
unique_key_count = len(set(line.split("=", 1)[0] for line in nonempty_lines if line.count("=") == 1))

with MANIFEST.open(newline="", encoding="utf-8") as handle:
    manifest_rows = list(csv.DictReader(handle))
manifest_rel = {row["RELATIVE_PATH"] for row in manifest_rows}
actual_files: set[str] = set()
actual_dirs: set[str] = set()
paths: list[Path] = [ROOT]
for current, dirs, files in os.walk(ROOT):
    current_path = Path(current)
    for directory in dirs:
        path = current_path / directory
        actual_dirs.add(path.relative_to(ROOT).as_posix())
        paths.append(path)
    for filename in files:
        path = current_path / filename
        actual_files.add(path.relative_to(ROOT).as_posix())
        paths.append(path)

actual_manifest_scope = actual_files - {"MANIFEST.csv", "WRITE_STOPPED"}
file_diff = sorted(manifest_rel ^ actual_manifest_scope)
dir_diff = sorted(EXPECTED_DIRS ^ actual_dirs)
readonly_missing = []
reparse_paths = []
cache_paths = []
ads_paths = []
readonly_bit = getattr(stat, "FILE_ATTRIBUTE_READONLY", 0x1)
reparse_bit = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
for path in paths:
    info = path.lstat()
    attrs = getattr(info, "st_file_attributes", 0)
    rel = "." if path == ROOT else path.relative_to(ROOT).as_posix()
    if not (attrs & readonly_bit):
        readonly_missing.append(rel)
    if attrs & reparse_bit:
        reparse_paths.append(rel)
    lowered_parts = [part.lower() for part in path.parts]
    if "__pycache__" in lowered_parts or path.suffix.lower() in {".pyc", ".pyo"} or path.name.lower() == ".cache":
        cache_paths.append(rel)
    if path.is_file():
        streams = alternate_streams(path)
        if streams:
            ads_paths.append(rel + ":" + ",".join(streams))

marker_stat = MARKER.stat()
other_paths = [path for path in paths if path != MARKER]
at_or_after = [
    "." if path == ROOT else path.relative_to(ROOT).as_posix()
    for path in other_paths
    if path.stat().st_mtime_ns >= marker_stat.st_mtime_ns
]
postmarker = [
    path.relative_to(ROOT).as_posix()
    for path in other_paths
    if path != ROOT and path.stat().st_ctime_ns > marker_stat.st_ctime_ns
]
marker_name_count = sum(1 for name in actual_files if name == "WRITE_STOPPED")
manifest_hash = sha256(MANIFEST)
manifest_hash_mismatches = []
for row in manifest_rows:
    path = ROOT / row["RELATIVE_PATH"]
    if path.stat().st_size != int(row["BYTES"]) or sha256(path) != row["SHA256"]:
        manifest_hash_mismatches.append(row["RELATIVE_PATH"])

checks = {
    "ROOT_EXISTS": ROOT.is_dir(),
    "STAGE_ABSENT": not STAGE.exists(),
    "UTF8_NO_BOM": utf8_no_bom,
    "MARKER_ENDS_NEWLINE": raw_marker.endswith(b"\n"),
    "MARKER_PHYSICAL_LINES": len(physical_lines),
    "MARKER_NONEMPTY_LINES": len(nonempty_lines),
    "MARKER_BAD_LINES": len(bad_lines),
    "MARKER_UNIQUE_KEYS": unique_key_count,
    "HANDOFF_ID_MATCH": parsed.get("HANDOFF_ID") == "C-FIG-P670-01-R114-SA1-FRESH-ISOLATED-V1",
    "UID_MATCH": parsed.get("UID") == "FIG-P670-01",
    "SEALED_ROOT_MATCH": parsed.get("SEALED_ROOT") == str(ROOT),
    "MANIFEST_ROWS_MATCH": parsed.get("MANIFEST_ROWS") == str(len(manifest_rows)),
    "MANIFEST_SHA256_MATCH": parsed.get("MANIFEST_SHA256") == manifest_hash,
    "VERDICT_MATCH": parsed.get("VERDICT") == "PASS",
    "FS_IDENTITY_DIFF": len(file_diff),
    "DIR_IDENTITY_DIFF": len(dir_diff),
    "MANIFEST_HASH_MISMATCHES": len(manifest_hash_mismatches),
    "READONLY_MISSING": len(readonly_missing),
    "MARKER_NAME_COUNT": marker_name_count,
    "AT_OR_AFTER_MARKER": len(at_or_after),
    "POSTMARKER": len(postmarker),
    "ADS": len(ads_paths),
    "CACHE_PYC": len(cache_paths),
    "REPARSE": len(reparse_paths),
    "MARKER_FUTURE_VS_AUDIT_NS": marker_stat.st_mtime_ns - time.time_ns(),
}

audit_pass = (
    checks["ROOT_EXISTS"]
    and checks["STAGE_ABSENT"]
    and checks["UTF8_NO_BOM"]
    and checks["MARKER_ENDS_NEWLINE"]
    and checks["MARKER_PHYSICAL_LINES"] == 8
    and checks["MARKER_NONEMPTY_LINES"] == 8
    and checks["MARKER_BAD_LINES"] == 0
    and checks["MARKER_UNIQUE_KEYS"] == 8
    and checks["HANDOFF_ID_MATCH"]
    and checks["UID_MATCH"]
    and checks["SEALED_ROOT_MATCH"]
    and checks["MANIFEST_ROWS_MATCH"]
    and checks["MANIFEST_SHA256_MATCH"]
    and checks["VERDICT_MATCH"]
    and checks["FS_IDENTITY_DIFF"] == 0
    and checks["DIR_IDENTITY_DIFF"] == 0
    and checks["MANIFEST_HASH_MISMATCHES"] == 0
    and checks["READONLY_MISSING"] == 0
    and checks["MARKER_NAME_COUNT"] == 1
    and checks["AT_OR_AFTER_MARKER"] == 0
    and checks["POSTMARKER"] == 0
    and checks["ADS"] == 0
    and checks["CACHE_PYC"] == 0
    and checks["REPARSE"] == 0
    and checks["MARKER_FUTURE_VS_AUDIT_NS"] > 0
)

lines = [f"{key}={value}" for key, value in checks.items()]
lines.extend(
    [
        "FILE_DIFF=" + "|".join(file_diff),
        "DIR_DIFF=" + "|".join(dir_diff),
        "HASH_MISMATCH_LIST=" + "|".join(manifest_hash_mismatches),
        "READONLY_MISSING_LIST=" + "|".join(readonly_missing),
        "AT_OR_AFTER_LIST=" + "|".join(at_or_after),
        "POSTMARKER_LIST=" + "|".join(postmarker),
        "ADS_LIST=" + "|".join(ads_paths),
        "CACHE_PYC_LIST=" + "|".join(cache_paths),
        "REPARSE_LIST=" + "|".join(reparse_paths),
        f"AUDIT_PASS={str(audit_pass).lower()}",
    ]
)
AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
if not audit_pass:
    raise SystemExit(1)
