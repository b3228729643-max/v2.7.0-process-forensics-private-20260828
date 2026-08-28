from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
from ctypes import wintypes
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R1_SA2_R168_READONLY_R111_20260827")
REPORTS = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports")
MANIFEST = REPORTS / "FIG-P067-01_A-R111-P067-SA2-R168-READONLY-20260827_SEALED_ROOT_MANIFEST.csv"
AUDIT = REPORTS / "FIG-P067-01_A-R111-P067-SA2-R168-READONLY-20260827_ROOT_EXTERNAL_AUDIT.json"
MARKER_NAME = "WRITE_STOPPED"
READONLY = 0x1
REPARSE = 0x400


class WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", wintypes.WCHAR * 296)]


FindFirstStreamW = ctypes.windll.kernel32.FindFirstStreamW
FindFirstStreamW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(WIN32_FIND_STREAM_DATA), wintypes.DWORD]
FindFirstStreamW.restype = wintypes.HANDLE
FindNextStreamW = ctypes.windll.kernel32.FindNextStreamW
FindNextStreamW.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
FindNextStreamW.restype = wintypes.BOOL
FindClose = ctypes.windll.kernel32.FindClose
FindClose.argtypes = [wintypes.HANDLE]
FindClose.restype = wintypes.BOOL
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def ntfs_ticks_from_ns(unix_ns: int) -> int:
    return unix_ns // 100 + 116444736000000000


def named_stream_count(path: Path) -> int:
    data = WIN32_FIND_STREAM_DATA()
    handle = FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    if handle == INVALID_HANDLE_VALUE:
        return 0
    names = []
    try:
        names.append(data.cStreamName)
        while FindNextStreamW(handle, ctypes.byref(data)):
            names.append(data.cStreamName)
    finally:
        FindClose(wintypes.HANDLE(handle))
    return sum(name != "::$DATA" for name in names)


def snapshot() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for path in sorted([ROOT] + list(ROOT.rglob("*"))):
        stat = path.stat()
        rel = "." if path == ROOT else path.relative_to(ROOT).as_posix()
        attrs = getattr(stat, "st_file_attributes", 0)
        rows[rel] = {
            "type": "directory" if path.is_dir() else "file",
            "bytes": 0 if path.is_dir() else stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "mtime_ntfs_ticks": ntfs_ticks_from_ns(stat.st_mtime_ns),
            "ctime_ntfs_ticks": ntfs_ticks_from_ns(stat.st_ctime_ns),
            "attributes_decimal": attrs,
        }
    return rows


def parse_error_count(files: list[Path]) -> int:
    errors = 0
    for path in files:
        try:
            suffix = path.suffix.lower()
            if suffix == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
            elif suffix == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as stream:
                    list(csv.reader(stream))
            elif suffix == ".psv":
                with path.open("r", encoding="utf-8-sig", newline="") as stream:
                    list(csv.reader(stream, delimiter="|"))
            elif suffix in {".md", ".txt", ".py", ".ps1"}:
                text = path.read_text(encoding="utf-8-sig")
                if suffix == ".py":
                    compile(text, str(path), "exec")
            elif suffix == ".svg":
                ET.parse(path)
            elif suffix == ".png":
                with Image.open(path) as image:
                    image.verify()
        except Exception:
            errors += 1
    return errors


def main() -> None:
    if MANIFEST.exists() or AUDIT.exists():
        raise SystemExit("external audit outputs already exist")
    first = snapshot()
    files = sorted(p for p in ROOT.rglob("*") if p.is_file())
    manifest_rows = []
    for path in files:
        stat = path.stat()
        manifest_rows.append(
            {
                "relative_path": path.relative_to(ROOT).as_posix(),
                "bytes": stat.st_size,
                "sha256": sha256(path),
                "mtime_ntfs_ticks": ntfs_ticks_from_ns(stat.st_mtime_ns),
                "ctime_ntfs_ticks": ntfs_ticks_from_ns(stat.st_ctime_ns),
                "attributes_decimal": getattr(stat, "st_file_attributes", 0),
            }
        )
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    time.sleep(0.15)
    second = snapshot()
    manifest_back = list(csv.DictReader(MANIFEST.open("r", encoding="utf-8-sig", newline="")))
    manifest_paths = [r["relative_path"] for r in manifest_back]
    fs_paths = [p.relative_to(ROOT).as_posix() for p in files]
    marker_paths = [p for p in fs_paths if Path(p).name == MARKER_NAME]
    marker_rel = marker_paths[0] if len(marker_paths) == 1 else ""
    marker_ticks = second.get(marker_rel, {}).get("mtime_ntfs_ticks", -1)
    other_at_or_after = sum(
        row["mtime_ntfs_ticks"] >= marker_ticks
        for rel, row in second.items()
        if rel not in {marker_rel} and marker_ticks >= 0
    )
    changes = sum(first.get(rel) != second.get(rel) for rel in set(first) | set(second))
    manifest_map = {r["relative_path"]: r for r in manifest_back}
    bytes_mismatch = 0
    sha_mismatch = 0
    ticks_mismatch = 0
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        row = manifest_map[rel]
        stat = path.stat()
        bytes_mismatch += int(int(row["bytes"]) != stat.st_size)
        sha_mismatch += int(row["sha256"] != sha256(path))
        ticks_mismatch += int(int(row["mtime_ntfs_ticks"]) != ntfs_ticks_from_ns(stat.st_mtime_ns))
    all_items = [ROOT] + list(ROOT.rglob("*"))
    audit = {
        "root": str(ROOT),
        "sealed_file_count": len(files),
        "sealed_directory_count_including_root": sum(p.is_dir() for p in all_items),
        "manifest_entry_count": len(manifest_back),
        "manifest_duplicate_path_count": len(manifest_paths) - len(set(manifest_paths)),
        "manifest_missing_path_count": len(set(fs_paths) - set(manifest_paths)),
        "manifest_extra_path_count": len(set(manifest_paths) - set(fs_paths)),
        "manifest_bytes_mismatch_count": bytes_mismatch,
        "manifest_sha256_mismatch_count": sha_mismatch,
        "manifest_ntfs_tick_mismatch_count": ticks_mismatch,
        "parse_error_count": parse_error_count(files),
        "named_ads_count": sum(named_stream_count(p) for p in files),
        "cache_or_pyc_count": sum(p.name == "__pycache__" or p.suffix.lower() == ".pyc" for p in all_items),
        "reparse_point_count": sum(bool(getattr(p.stat(), "st_file_attributes", 0) & REPARSE) for p in all_items),
        "non_readonly_file_count": sum(not (getattr(p.stat(), "st_file_attributes", 0) & READONLY) for p in files),
        "non_readonly_directory_count": sum(not (getattr(p.stat(), "st_file_attributes", 0) & READONLY) for p in all_items if p.is_dir()),
        "write_stopped_marker_count": len(marker_paths),
        "write_stopped_relative_path": marker_rel,
        "write_stopped_mtime_ntfs_ticks": marker_ticks,
        "nonmarker_at_or_after_marker_count": other_at_or_after,
        "postmarker_content_or_attribute_change_count": changes,
        "status_code": "SEALED_ROOT_CLOSED" if all(
            value == 0
            for value in (
                len(manifest_paths) - len(set(manifest_paths)),
                len(set(fs_paths) - set(manifest_paths)),
                len(set(manifest_paths) - set(fs_paths)),
                bytes_mismatch, sha_mismatch, ticks_mismatch,
                parse_error_count(files),
                sum(named_stream_count(p) for p in files),
                sum(p.name == "__pycache__" or p.suffix.lower() == ".pyc" for p in all_items),
                sum(bool(getattr(p.stat(), "st_file_attributes", 0) & REPARSE) for p in all_items),
                sum(not (getattr(p.stat(), "st_file_attributes", 0) & READONLY) for p in files),
                sum(not (getattr(p.stat(), "st_file_attributes", 0) & READONLY) for p in all_items if p.is_dir()),
                other_at_or_after, changes,
            )
        ) and len(marker_paths) == 1 else "SEALED_ROOT_NOT_CLOSED",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
