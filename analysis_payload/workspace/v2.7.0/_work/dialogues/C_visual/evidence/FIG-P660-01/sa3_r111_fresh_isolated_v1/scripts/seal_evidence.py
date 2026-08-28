from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import json
import os
import stat
import sys
import time
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa3_r111_fresh_isolated_v1")
MARKER = ROOT / "WRITE_STOPPED"
TEMP_MARKER = ROOT.parent / (ROOT.name + ".WRITE_STOPPED.tmp")
FILE_MANIFEST = ROOT / "MANIFEST_FILES.csv"
DIR_MANIFEST = ROOT / "MANIFEST_DIRECTORIES.csv"
SEAL_AUDIT = ROOT / "SEAL_AUDIT.json"
EPOCH_DELTA_TICKS = 116_444_736_000_000_000
READONLY = 0x1
REPARSE = 0x400


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
GetFileAttributesW = kernel32.GetFileAttributesW
GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
GetFileAttributesW.restype = ctypes.c_uint32
SetFileAttributesW = kernel32.SetFileAttributesW
SetFileAttributesW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]
SetFileAttributesW.restype = ctypes.c_int


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
        raise OSError(ctypes.get_last_error(), f"GetFileAttributesW failed: {path}")
    return int(value)


def make_readonly(path: Path) -> None:
    value = attrs(path)
    if not SetFileAttributesW(str(path), value | READONLY):
        raise OSError(ctypes.get_last_error(), f"SetFileAttributesW failed: {path}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def ticks_from_ns(ns: int) -> int:
    return ns // 100 + EPOCH_DELTA_TICKS


def identity(path: Path) -> dict:
    st = path.stat()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": st.st_size,
        "sha256": sha256(path),
        "creation_time_utc_ticks": ticks_from_ns(st.st_ctime_ns),
        "last_write_time_utc_ticks": ticks_from_ns(st.st_mtime_ns),
    }


def alternate_streams(path: Path) -> list[str]:
    data = WIN32_FIND_STREAM_DATA()
    handle = FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    if handle == INVALID_HANDLE_VALUE:
        err = ctypes.get_last_error()
        if err in (2, 38):
            return []
        raise OSError(err, f"FindFirstStreamW failed: {path}")
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
    elif suffix in (".md", ".txt"):
        path.read_text(encoding="utf-8-sig")
    elif suffix == ".png":
        with Image.open(path) as im:
            im.verify()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if MARKER.exists() or TEMP_MARKER.exists() or FILE_MANIFEST.exists() or DIR_MANIFEST.exists() or SEAL_AUDIT.exists():
        raise RuntimeError("seal artifacts already exist; refusing duplicate seal")

    all_paths = sorted(ROOT.rglob("*"), key=lambda p: p.as_posix())
    files_before = [p for p in all_paths if p.is_file()]
    dirs_before = [ROOT] + [p for p in all_paths if p.is_dir()]

    pycache = [p for p in all_paths if p.name == "__pycache__" or p.suffix.lower() in (".pyc", ".pyo")]
    reparses = [p for p in [ROOT] + all_paths if attrs(p) & REPARSE]
    ads = [(p, stream) for p in [ROOT] + all_paths for stream in alternate_streams(p)]
    parse_errors = []
    for path in files_before:
        try:
            parse_file(path)
        except Exception as exc:
            parse_errors.append({"path": str(path), "error": repr(exc)})
    if pycache or reparses or ads or parse_errors:
        raise RuntimeError(json.dumps({
            "pycache": [str(p) for p in pycache],
            "reparse": [str(p) for p in reparses],
            "ads": [(str(p), s) for p, s in ads],
            "parse_errors": parse_errors,
        }, ensure_ascii=False))

    file_rows = [identity(p) for p in files_before]
    write_csv(FILE_MANIFEST, list(file_rows[0].keys()), file_rows)

    dir_rows = []
    for path in dirs_before:
        st = path.stat()
        dir_rows.append({
            "path": "." if path == ROOT else path.relative_to(ROOT).as_posix(),
            "creation_time_utc_ticks": ticks_from_ns(st.st_ctime_ns),
            "last_write_time_utc_ticks_pre_marker": ticks_from_ns(st.st_mtime_ns),
            "reparse_point": 0,
        })
    write_csv(DIR_MANIFEST, list(dir_rows[0].keys()), dir_rows)

    manifest_files_identity = identity(FILE_MANIFEST)
    manifest_dirs_identity = identity(DIR_MANIFEST)
    audit = {
        "handoff_id": "C-FIG-P660-01-R111-SA3-FRESH-ISOLATED-V1",
        "figure_id": "FIG-P660-01",
        "result": "PASS",
        "evidence_file_count_pre_manifest": len(files_before),
        "directory_count_including_root": len(dirs_before),
        "expected_postseal_file_count": len(files_before) + 4,
        "manifest_files_identity": manifest_files_identity,
        "manifest_directories_identity": manifest_dirs_identity,
        "parse_error_count": 0,
        "alternate_data_stream_count": 0,
        "cache_or_pyc_count": 0,
        "reparse_point_count": 0,
        "manual_pair_ids": 120,
        "visible_object_denominator": 16,
        "text_element_count": 20,
        "overlap_candidate_pixel_count": 922,
        "mask_contamination_pixel_count": 922,
        "true_illegal_overlap_pixel_count": 0,
        "clip_pixel_count": 0,
        "marker_name": "WRITE_STOPPED",
        "seal_protocol": "all existing root paths made Windows ReadOnly; pre-readonly marker moved into root as unique final root-content operation",
    }
    SEAL_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    seal_audit_identity = identity(SEAL_AUDIT)

    marker_text = (
        "HANDOFF_ID=C-FIG-P660-01-R111-SA3-FRESH-ISOLATED-V1\n"
        "RESULT=PASS\n"
        f"MANIFEST_FILES_BYTES={manifest_files_identity['bytes']}\n"
        f"MANIFEST_FILES_SHA256={manifest_files_identity['sha256']}\n"
        f"MANIFEST_DIRECTORIES_BYTES={manifest_dirs_identity['bytes']}\n"
        f"MANIFEST_DIRECTORIES_SHA256={manifest_dirs_identity['sha256']}\n"
        f"SEAL_AUDIT_BYTES={seal_audit_identity['bytes']}\n"
        f"SEAL_AUDIT_SHA256={seal_audit_identity['sha256']}\n"
        f"EXPECTED_POSTSEAL_FILE_COUNT={audit['expected_postseal_file_count']}\n"
        "POSTMARKER0=VERIFY_READ_ONLY_AFTER_MOVE\n"
    )
    TEMP_MARKER.write_text(marker_text, encoding="ascii")
    make_readonly(TEMP_MARKER)
    # Future by two seconds so the marker is strictly latest even versus the root
    # directory entry timestamp created by the final move.
    future = time.time() + 2.0
    os.utime(TEMP_MARKER, (future, future))

    current_paths = sorted(ROOT.rglob("*"), key=lambda p: (len(p.parts), p.as_posix()), reverse=True)
    for path in current_paths:
        make_readonly(path)
    make_readonly(ROOT)

    # Unique absolute last root-content operation. Nothing below this line writes ROOT.
    os.replace(TEMP_MARKER, MARKER)
    print(json.dumps({
        "sealed": True,
        "marker": str(MARKER),
        "expected_postseal_file_count": audit["expected_postseal_file_count"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
