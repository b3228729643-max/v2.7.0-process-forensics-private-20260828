from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa3_r111_fresh_isolated_v1")
MARKER = ROOT / "WRITE_STOPPED"
READONLY = 0x1
REPARSE = 0x400
EPOCH_DELTA_TICKS = 116_444_736_000_000_000


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
GetFileAttributesW = kernel32.GetFileAttributesW
GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
GetFileAttributesW.restype = ctypes.c_uint32


class WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", ctypes.c_wchar * 296)]


FindFirstStreamW = kernel32.FindFirstStreamW
FindFirstStreamW.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(WIN32_FIND_STREAM_DATA), ctypes.c_uint32]
FindFirstStreamW.restype = ctypes.c_void_p
FindNextStreamW = kernel32.FindNextStreamW
FindNextStreamW.argtypes = [ctypes.c_void_p, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
FindNextStreamW.restype = ctypes.c_int
FindClose = kernel32.FindClose
FindClose.argtypes = [ctypes.c_void_p]
FindClose.restype = ctypes.c_int
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


def attrs(path: Path) -> int:
    value = GetFileAttributesW(str(path))
    if value == 0xFFFFFFFF:
        raise OSError(ctypes.get_last_error(), str(path))
    return int(value)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def ticks_from_ns(ns: int) -> int:
    return ns // 100 + EPOCH_DELTA_TICKS


def alternate_streams(path: Path) -> list[str]:
    data = WIN32_FIND_STREAM_DATA()
    handle = FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    if handle == INVALID_HANDLE_VALUE:
        err = ctypes.get_last_error()
        if err in (2, 38):
            return []
        raise OSError(err, str(path))
    names = []
    try:
        while True:
            name = data.cStreamName
            if name and name != "::$DATA":
                names.append(name)
            if not FindNextStreamW(handle, ctypes.byref(data)):
                break
    finally:
        FindClose(handle)
    return names


def parse_file(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".py":
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    elif suffix == ".json":
        json.loads(path.read_text(encoding="utf-8"))
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            list(csv.reader(f))
    elif suffix in (".md", ".txt", ""):
        path.read_text(encoding="utf-8-sig")
    elif suffix == ".png":
        with Image.open(path) as im:
            im.verify()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    paths = [ROOT] + sorted(ROOT.rglob("*"), key=lambda p: p.as_posix())
    files = [p for p in paths if p.is_file()]
    marker_matches = [p for p in files if p.name == "WRITE_STOPPED"]
    if marker_matches != [MARKER]:
        raise RuntimeError(f"marker uniqueness failed: {marker_matches}")

    marker_lines = dict(
        line.split("=", 1) for line in MARKER.read_text(encoding="ascii").splitlines() if "=" in line
    )
    audit = json.loads((ROOT / "SEAL_AUDIT.json").read_text(encoding="utf-8"))
    if len(files) != int(marker_lines["EXPECTED_POSTSEAL_FILE_COUNT"]):
        raise RuntimeError(f"file count mismatch: {len(files)}")

    readonly_fail = [str(p) for p in paths if not (attrs(p) & READONLY)]
    reparse_fail = [str(p) for p in paths if attrs(p) & REPARSE]
    ads = [(str(p), s) for p in paths for s in alternate_streams(p)]
    cache = [str(p) for p in paths if p.name == "__pycache__" or p.suffix.lower() in (".pyc", ".pyo")]
    parse_errors = []
    for path in files:
        try:
            parse_file(path)
        except Exception as exc:
            parse_errors.append({"path": str(path), "error": repr(exc)})

    manifest_path = ROOT / "MANIFEST_FILES.csv"
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    identity_errors = []
    for row in rows:
        path = ROOT / Path(row["path"])
        st = path.stat()
        observed = {
            "bytes": str(st.st_size),
            "sha256": sha256(path),
            "creation_time_utc_ticks": str(ticks_from_ns(st.st_ctime_ns)),
            "last_write_time_utc_ticks": str(ticks_from_ns(st.st_mtime_ns)),
        }
        for key, value in observed.items():
            if value != row[key]:
                identity_errors.append({"path": row["path"], "field": key, "expected": row[key], "actual": value})

    closure_errors = []
    closure_targets = [
        (ROOT / "MANIFEST_FILES.csv", "MANIFEST_FILES"),
        (ROOT / "MANIFEST_DIRECTORIES.csv", "MANIFEST_DIRECTORIES"),
        (ROOT / "SEAL_AUDIT.json", "SEAL_AUDIT"),
    ]
    for path, prefix in closure_targets:
        if str(path.stat().st_size) != marker_lines[f"{prefix}_BYTES"]:
            closure_errors.append(f"{prefix}_BYTES")
        if sha256(path) != marker_lines[f"{prefix}_SHA256"]:
            closure_errors.append(f"{prefix}_SHA256")

    marker_ticks = ticks_from_ns(MARKER.stat().st_mtime_ns)
    other_latest = max(ticks_from_ns(p.stat().st_mtime_ns) for p in paths if p != MARKER)
    marker_strictly_latest = marker_ticks > other_latest

    result = {
        "postmarker0": not any((readonly_fail, reparse_fail, ads, cache, parse_errors, identity_errors, closure_errors)) and marker_strictly_latest,
        "file_count": len(files),
        "directory_count_including_root": len([p for p in paths if p.is_dir()]),
        "readonly_fail_count": len(readonly_fail),
        "reparse_point_count": len(reparse_fail),
        "alternate_data_stream_count": len(ads),
        "cache_or_pyc_count": len(cache),
        "parse_error_count": len(parse_errors),
        "manifest_identity_error_count": len(identity_errors),
        "closure_error_count": len(closure_errors),
        "marker_unique": True,
        "marker_strictly_latest": marker_strictly_latest,
        "marker_last_write_ticks": marker_ticks,
        "latest_other_path_ticks": other_latest,
        "seal_audit_result": audit["result"],
    }
    if not result["postmarker0"]:
        result["failures"] = {
            "readonly": readonly_fail,
            "reparse": reparse_fail,
            "ads": ads,
            "cache": cache,
            "parse": parse_errors,
            "identity": identity_errors,
            "closure": closure_errors,
        }
        raise RuntimeError(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
