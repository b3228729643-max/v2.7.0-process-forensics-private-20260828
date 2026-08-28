from __future__ import annotations

import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import time

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa3_r111_fresh_isolated_v1")
CONTENT_MANIFEST = ROOT / "CONTENT_MANIFEST.csv"
SEAL_AUDIT = ROOT / "SEAL_AUDIT.json"
FINAL_MANIFEST = ROOT / "FINAL_MANIFEST.json"
STOP = ROOT / "WRITE_STOPPED"
RESERVED = {CONTENT_MANIFEST.name, SEAL_AUDIT.name, FINAL_MANIFEST.name, STOP.name}

FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
EPOCH_AS_FILETIME_TICKS = 621355968000000000


class WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [
        ("StreamSize", ctypes.c_int64),
        ("cStreamName", wintypes.WCHAR * (260 + 36)),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
kernel32.GetFileAttributesW.restype = wintypes.DWORD
kernel32.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
kernel32.SetFileAttributesW.restype = wintypes.BOOL
kernel32.FindFirstStreamW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(WIN32_FIND_STREAM_DATA), wintypes.DWORD]
kernel32.FindFirstStreamW.restype = wintypes.HANDLE
kernel32.FindNextStreamW.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
kernel32.FindNextStreamW.restype = wintypes.BOOL
kernel32.FindClose.argtypes = [wintypes.HANDLE]
kernel32.FindClose.restype = wintypes.BOOL


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def ns_to_dotnet_ticks(ns: int) -> int:
    return EPOCH_AS_FILETIME_TICKS + ns // 100


def file_record(path: Path) -> dict:
    stat = path.stat()
    attrs = int(kernel32.GetFileAttributesW(str(path)))
    return {
        "relative_path": path.relative_to(ROOT).as_posix(),
        "bytes": stat.st_size,
        "sha256": sha256(path),
        "creation_time_utc_ticks": ns_to_dotnet_ticks(stat.st_ctime_ns),
        "last_write_time_utc_ticks": ns_to_dotnet_ticks(stat.st_mtime_ns),
        "windows_attributes": attrs,
        "expected_final_readonly": True,
    }


def alternate_streams(path: Path) -> list[str]:
    data = WIN32_FIND_STREAM_DATA()
    handle = kernel32.FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    if handle == INVALID_HANDLE_VALUE:
        return []
    names = []
    try:
        names.append(data.cStreamName)
        while kernel32.FindNextStreamW(handle, ctypes.byref(data)):
            names.append(data.cStreamName)
    finally:
        kernel32.FindClose(handle)
    return [name for name in names if name != "::$DATA"]


def parse_file(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".png":
        with Image.open(path) as image:
            image.verify()
    elif suffix == ".json":
        with path.open("r", encoding="utf-8") as stream:
            json.load(stream)
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
        if not rows:
            raise ValueError(f"empty CSV: {path.name}")
        width = len(rows[0])
        if width == 0 or any(len(row) != width for row in rows):
            raise ValueError(f"ragged CSV: {path.name}")
    else:
        path.read_text(encoding="utf-8")


def set_readonly(path: Path) -> None:
    attrs = int(kernel32.GetFileAttributesW(str(path)))
    if attrs == 0xFFFFFFFF:
        raise OSError(ctypes.get_last_error(), f"GetFileAttributesW failed: {path}")
    if not kernel32.SetFileAttributesW(str(path), attrs | FILE_ATTRIBUTE_READONLY):
        raise OSError(ctypes.get_last_error(), f"SetFileAttributesW failed: {path}")


def is_readonly(path: Path) -> bool:
    attrs = int(kernel32.GetFileAttributesW(str(path)))
    return attrs != 0xFFFFFFFF and bool(attrs & FILE_ATTRIBUTE_READONLY)


def current_files() -> list[Path]:
    return sorted([path for path in ROOT.iterdir() if path.is_file()], key=lambda p: p.name.casefold())


def main() -> None:
    if not ROOT.is_dir():
        raise RuntimeError("mandated root missing")
    if any(path.exists() for path in (CONTENT_MANIFEST, SEAL_AUDIT, FINAL_MANIFEST, STOP)):
        raise RuntimeError("seal output already exists; refusing restart or duplicate seal")
    subdirs = [path for path in ROOT.iterdir() if path.is_dir()]
    if subdirs:
        raise RuntimeError(f"unexpected subdirectories: {[p.name for p in subdirs]}")

    evidence_files = current_files()
    with CONTENT_MANIFEST.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["RELATIVE_PATH", "BYTES", "SHA256", "CREATION_TIME_UTC_TICKS", "LAST_WRITE_TIME_UTC_TICKS", "EXPECTED_FINAL_READONLY"])
        for path in evidence_files:
            record = file_record(path)
            writer.writerow([
                record["relative_path"],
                record["bytes"],
                record["sha256"],
                record["creation_time_utc_ticks"],
                record["last_write_time_utc_ticks"],
                "true",
            ])

    audit_files = current_files()
    parse_errors = []
    ads_rows = []
    reparse_rows = []
    cache_rows = []
    pyc_rows = []
    for path in audit_files:
        try:
            parse_file(path)
        except Exception as exc:
            parse_errors.append({"relative_path": path.name, "error": f"{type(exc).__name__}: {exc}"})
        for stream_name in alternate_streams(path):
            ads_rows.append({"relative_path": path.name, "stream": stream_name})
        attrs = int(kernel32.GetFileAttributesW(str(path)))
        if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
            reparse_rows.append(path.name)
        lower = path.name.casefold()
        if lower in {"__pycache__", ".cache", "cache"}:
            cache_rows.append(path.name)
        if path.suffix.casefold() in {".pyc", ".pyo"}:
            pyc_rows.append(path.name)

    root_attrs = int(kernel32.GetFileAttributesW(str(ROOT)))
    if root_attrs & FILE_ATTRIBUTE_REPARSE_POINT:
        reparse_rows.append(".")
    if parse_errors or ads_rows or reparse_rows or cache_rows or pyc_rows:
        raise RuntimeError(json.dumps({
            "parse_errors": parse_errors,
            "alternate_streams": ads_rows,
            "reparse_points": reparse_rows,
            "cache_entries": cache_rows,
            "pyc_entries": pyc_rows,
        }, ensure_ascii=False))

    audit = {
        "schema": "FIG-P657-01-SA3-SEAL-AUDIT-1",
        "root": str(ROOT),
        "audited_file_count": len(audit_files),
        "parse_error_count": 0,
        "alternate_data_stream_count": 0,
        "cache_entry_count": 0,
        "pyc_entry_count": 0,
        "reparse_point_count": 0,
        "subdirectory_count": 0,
        "content_manifest": file_record(CONTENT_MANIFEST),
    }
    SEAL_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    parse_file(SEAL_AUDIT)

    pre_final_files = current_files()
    max_mtime_ns = max(path.stat().st_mtime_ns for path in pre_final_files)
    root_final_ns = max(time.time_ns(), max_mtime_ns) + 5_000_000_000
    marker_final_ns = root_final_ns + 1_000_000_000
    final_manifest_payload = {
        "schema": "FIG-P657-01-SA3-FINAL-MANIFEST-1",
        "root_absolute_path": str(ROOT),
        "result": "PASS",
        "handoff_id": "C-FIG-P657-01-R111-SA3-FRESH-ISOLATED-V1",
        "files_before_final_manifest": [file_record(path) for path in pre_final_files],
        "file_count_before_final_manifest": len(pre_final_files),
        "content_manifest_relative_path": CONTENT_MANIFEST.name,
        "content_manifest_sha256": sha256(CONTENT_MANIFEST),
        "seal_audit_relative_path": SEAL_AUDIT.name,
        "seal_audit_sha256": sha256(SEAL_AUDIT),
        "parse_error_count": 0,
        "alternate_data_stream_count": 0,
        "cache_entry_count": 0,
        "pyc_entry_count": 0,
        "reparse_point_count": 0,
        "planned_final_root_last_write_utc_ticks": ns_to_dotnet_ticks(root_final_ns),
        "planned_write_stopped_last_write_utc_ticks": ns_to_dotnet_ticks(marker_final_ns),
        "expected_final_all_paths_readonly": True,
        "expected_unique_write_stopped_count": 1,
        "expected_postmarker_later_path_count": 0,
    }
    FINAL_MANIFEST.write_text(json.dumps(final_manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    parse_file(FINAL_MANIFEST)
    final_manifest_record = file_record(FINAL_MANIFEST)

    marker_text = "\n".join([
        "WRITE_STOPPED",
        "RESULT=PASS",
        "HANDOFF_ID=C-FIG-P657-01-R111-SA3-FRESH-ISOLATED-V1",
        "LOCAL_ACCEPTANCE_TOKEN=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
        f"FINAL_MANIFEST_RELATIVE_PATH={FINAL_MANIFEST.name}",
        f"FINAL_MANIFEST_BYTES={final_manifest_record['bytes']}",
        f"FINAL_MANIFEST_SHA256={final_manifest_record['sha256']}",
        f"FINAL_MANIFEST_CREATION_TIME_UTC_TICKS={final_manifest_record['creation_time_utc_ticks']}",
        f"FINAL_MANIFEST_LAST_WRITE_TIME_UTC_TICKS={final_manifest_record['last_write_time_utc_ticks']}",
        f"ROOT_FINAL_LAST_WRITE_TIME_UTC_TICKS={ns_to_dotnet_ticks(root_final_ns)}",
        f"WRITE_STOPPED_LAST_WRITE_TIME_UTC_TICKS={ns_to_dotnet_ticks(marker_final_ns)}",
        "PARSE_ERROR_COUNT=0",
        "ALTERNATE_DATA_STREAM_COUNT=0",
        "CACHE_ENTRY_COUNT=0",
        "PYC_ENTRY_COUNT=0",
        "REPARSE_POINT_COUNT=0",
        "POSTMARKER_LATER_PATH_COUNT=0",
        "",
    ])

    STOP.write_text(marker_text, encoding="utf-8")

    # Final metadata sequence. The last mutating operation in the root is the
    # ReadOnly-attribute set on WRITE_STOPPED itself.
    os.utime(ROOT, ns=(root_final_ns, root_final_ns))
    for path in current_files():
        if path != STOP:
            set_readonly(path)
    set_readonly(ROOT)
    os.utime(STOP, ns=(marker_final_ns, marker_final_ns))
    set_readonly(STOP)

    # Read-only postseal verification: no root mutation from this point onward.
    files_after = current_files()
    marker_ticks = ns_to_dotnet_ticks(STOP.stat().st_mtime_ns)
    later = [
        path.name
        for path in files_after
        if path != STOP and ns_to_dotnet_ticks(path.stat().st_mtime_ns) >= marker_ticks
    ]
    stop_count = sum(1 for path in files_after if path.name == STOP.name)
    readonly_failures = [path.name for path in files_after if not is_readonly(path)]
    if not is_readonly(ROOT):
        readonly_failures.append(".")
    parse_file(FINAL_MANIFEST)
    STOP.read_text(encoding="utf-8")
    for path in files_after:
        if alternate_streams(path):
            raise RuntimeError(f"postseal ADS found: {path.name}")
    reparse_after = [path.name for path in files_after if int(kernel32.GetFileAttributesW(str(path))) & FILE_ATTRIBUTE_REPARSE_POINT]
    cache_after = [path.name for path in files_after if path.name.casefold() in {"__pycache__", ".cache", "cache"}]
    pyc_after = [path.name for path in files_after if path.suffix.casefold() in {".pyc", ".pyo"}]
    if stop_count != 1 or later or readonly_failures or reparse_after or cache_after or pyc_after:
        raise RuntimeError(json.dumps({
            "stop_count": stop_count,
            "later_or_equal_paths": later,
            "readonly_failures": readonly_failures,
            "reparse_after": reparse_after,
            "cache_after": cache_after,
            "pyc_after": pyc_after,
        }, ensure_ascii=False))

    receipt = {
        "sealed": True,
        "result": "PASS",
        "file_count_including_marker": len(files_after),
        "write_stopped_count": stop_count,
        "write_stopped_bytes": STOP.stat().st_size,
        "write_stopped_sha256": sha256(STOP),
        "write_stopped_last_write_utc_ticks": marker_ticks,
        "root_last_write_utc_ticks": ns_to_dotnet_ticks(ROOT.stat().st_mtime_ns),
        "postmarker_later_path_count": len(later),
        "readonly_failure_count": len(readonly_failures),
        "alternate_data_stream_count": 0,
        "cache_entry_count": 0,
        "pyc_entry_count": 0,
        "reparse_point_count": 0,
        "final_manifest": final_manifest_record,
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
