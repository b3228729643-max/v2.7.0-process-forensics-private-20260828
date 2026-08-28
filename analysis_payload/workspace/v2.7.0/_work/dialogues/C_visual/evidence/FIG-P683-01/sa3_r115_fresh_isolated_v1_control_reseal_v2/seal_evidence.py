from __future__ import annotations

import csv
import ctypes
import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST_SHA256.csv"
MARKER = ROOT / "WRITE_STOPPED"
FUTURE_UTC = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

FILE_ATTRIBUTE_READONLY = 0x00000001
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
FILE_WRITE_ATTRIBUTES = 0x0100
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
kernel32.GetFileAttributesW.restype = ctypes.c_uint32
kernel32.SetFileAttributesW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]
kernel32.SetFileAttributesW.restype = ctypes.c_int
kernel32.CreateFileW.argtypes = [
    ctypes.c_wchar_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_void_p,
]
kernel32.CreateFileW.restype = ctypes.c_void_p
kernel32.SetFileTime.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(FILETIME),
    ctypes.POINTER(FILETIME),
    ctypes.POINTER(FILETIME),
]
kernel32.SetFileTime.restype = ctypes.c_int
kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype = ctypes.c_int


def fail_win32(action: str, path: Path) -> None:
    code = ctypes.get_last_error()
    raise OSError(code, f"{action} failed for {path}")


def add_readonly(path: Path) -> None:
    raw = str(path)
    attrs = kernel32.GetFileAttributesW(raw)
    if attrs == INVALID_FILE_ATTRIBUTES:
        fail_win32("GetFileAttributesW", path)
    if not kernel32.SetFileAttributesW(raw, attrs | FILE_ATTRIBUTE_READONLY):
        fail_win32("SetFileAttributesW", path)


def set_all_marker_times(path: Path, moment: datetime) -> None:
    unix_seconds = moment.timestamp()
    windows_ticks = int((unix_seconds + 11644473600) * 10_000_000)
    ft = FILETIME(windows_ticks & 0xFFFFFFFF, windows_ticks >> 32)
    handle = kernel32.CreateFileW(
        str(path),
        FILE_WRITE_ATTRIBUTES,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        0,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        fail_win32("CreateFileW", path)
    try:
        if not kernel32.SetFileTime(handle, ctypes.byref(ft), ctypes.byref(ft), ctypes.byref(ft)):
            fail_win32("SetFileTime", path)
    finally:
        kernel32.CloseHandle(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def rel(path: Path) -> str:
    if path == ROOT:
        return "."
    return path.relative_to(ROOT).as_posix()


if not ROOT.is_dir():
    raise RuntimeError("fixed evidence root is absent")
if MANIFEST.exists() or MARKER.exists():
    raise RuntimeError("seal outputs must be absent before the one-time seal")

# Validate the frozen denominator and genuine manual ledgers before binding them.
denominator = csv_rows(ROOT / "reader_visible_denominator.csv")
base_pairs = csv_rows(ROOT / "pair_enumeration_base.csv")
manual_pairs = csv_rows(ROOT / "manual_pair_judgments.csv")
manual_elements = csv_rows(ROOT / "manual_element_judgments.csv")
if len(denominator) != 31 or len({row["ELEMENT_ID"] for row in denominator}) != 31:
    raise RuntimeError("denominator validation failed")
if len(base_pairs) != 465 or len(manual_pairs) != 465:
    raise RuntimeError("pair-count validation failed")
base_identity = [(row["PAIR_ID"], row["A_ID"], row["B_ID"]) for row in base_pairs]
manual_identity = [(row["PAIR_ID"], row["A_ID"], row["B_ID"]) for row in manual_pairs]
if base_identity != manual_identity or len(set(base_identity)) != 465:
    raise RuntimeError("pair-identity validation failed")
if len(manual_elements) != 31:
    raise RuntimeError("manual-element validation failed")
if any(not row["MANUAL_JUDGMENT"].strip() or not row["MANUAL_OBSERVATION"].strip() for row in manual_pairs):
    raise RuntimeError("blank manual pair field")
if any("ILLEGAL" in row["MANUAL_JUDGMENT"].upper() or "UNRESOLVED" in row["MANUAL_JUDGMENT"].upper() for row in manual_pairs):
    raise RuntimeError("hard pair finding present")
element_manual_columns = [
    "MANUAL_GLYPH_CODEPOINT_JUDGMENT",
    "MANUAL_READABILITY_CLIP_JUDGMENT",
    "MANUAL_SEMANTIC_OBJECT_JUDGMENT",
    "OBSERVATION_BASIS",
]
if any(any(not row[column].strip() for column in element_manual_columns) for row in manual_elements):
    raise RuntimeError("blank manual element field")

# Create a deterministic material manifest. The manifest cannot hash itself; its hash is
# bound by the final WRITE_STOPPED marker. The marker is the only later content creation.
material_files = sorted(
    (path for path in ROOT.rglob("*") if path.is_file() and path not in {MANIFEST, MARKER}),
    key=lambda path: rel(path).casefold(),
)
material_directories = [ROOT] + sorted(
    (path for path in ROOT.rglob("*") if path.is_dir()),
    key=lambda path: rel(path).casefold(),
)
with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["TYPE", "RELATIVE_PATH", "BYTES", "SHA256"])
    for path in material_directories:
        writer.writerow(["ROOT" if path == ROOT else "DIRECTORY", rel(path), "", ""])
    for path in material_files:
        writer.writerow(["FILE", rel(path), path.stat().st_size, sha256(path)])

manifest_hash = sha256(MANIFEST)
file_count_excluding_marker = sum(1 for path in ROOT.rglob("*") if path.is_file() and path != MARKER)
directory_count_excluding_root = sum(1 for path in ROOT.rglob("*") if path.is_dir())
if file_count_excluding_marker != len(material_files) + 1:
    raise RuntimeError("unexpected file appeared during manifest creation")

marker_items = [
    ("HANDOFF_ID", "C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-V1"),
    ("UID", "FIG-P683-01"),
    ("ROLE", "SA3"),
    ("MODEL", "gpt-5.6-sol"),
    ("REASONING_EFFORT", "xhigh"),
    ("OFFICIAL_PDF_SHA256", "93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F"),
    ("SOURCE_SHA256", "6C26EB8DE73F26D37078C03D82A27A45E32BECFD6E71C091BD96F9571562DFFF"),
    ("CHAPTER_SHA256", "7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029"),
    ("PHYSICAL_PAGE", "732"),
    ("PRINTED_PAGE", "719"),
    ("DENOMINATOR_N", "31"),
    ("PAIR_EXPECTED", "465"),
    ("PAIR_MANUAL", "465"),
    ("MANUAL_ELEMENT_COUNT", "31"),
    ("OVERLAP_CANDIDATE_PIXEL_COUNT", "0"),
    ("MASK_CONTAMINATION_PIXEL_COUNT", "0"),
    ("OVERLAP_PIXEL_COUNT", "0"),
    ("PIXEL_ADJUDICATION_STATUS", "CLEAR"),
    ("CLIP_PIXEL_COUNT", "0"),
    ("MIN_TEXT_CLEARANCE_PX", "4"),
    ("VERDICT", "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE"),
    ("MANIFEST_SHA256", manifest_hash),
    ("MANIFEST_COVERED_FILE_COUNT", str(len(material_files))),
    ("MANIFEST_COVERED_DIRECTORY_COUNT", str(len(material_directories))),
    ("TREE_FILE_COUNT_EXCLUDING_MARKER", str(file_count_excluding_marker)),
    ("TREE_DIRECTORY_COUNT_EXCLUDING_ROOT", str(directory_count_excluding_root)),
    ("STRICT_FUTURE_FILETIME_UTC", "2099-12-31T23:59:59.0000000Z"),
    ("AT_OR_AFTER_EXCLUDING_MARKER", "0"),
    ("POSTMARKER_WRITES", "0"),
    ("WRITE_STOPPED", "TRUE"),
]
marker_text = "".join(f"{key}={value}\n" for key, value in marker_items)
marker_lines = marker_text.splitlines()
if len(marker_lines) != len(marker_items):
    raise RuntimeError("marker line-count validation failed")
if len({key for key, _ in marker_items}) != len(marker_items):
    raise RuntimeError("duplicate marker key")
if any(not re.fullmatch(r"[A-Z0-9_]+=[^\r\n]+", line) or line.count("=") != 1 for line in marker_lines):
    raise RuntimeError("marker KEY=VALUE validation failed")
if FUTURE_UTC <= datetime.now(timezone.utc):
    raise RuntimeError("configured marker FILETIME is not strictly future")

# Absolute final content creation in the root.
MARKER.write_text(marker_text, encoding="ascii", newline="\n")

# Seal every other file, then every subdirectory and root. Marker FILETIME and its
# ReadOnly bit are last; SetFileAttributesW(MARKER) is the absolute final mutation.
all_nonmarker_files = sorted(
    (path for path in ROOT.rglob("*") if path.is_file() and path != MARKER),
    key=lambda path: rel(path).casefold(),
)
all_subdirectories = sorted(
    (path for path in ROOT.rglob("*") if path.is_dir()),
    key=lambda path: (len(path.parts), rel(path).casefold()),
    reverse=True,
)
for path in all_nonmarker_files:
    add_readonly(path)
for path in all_subdirectories:
    add_readonly(path)
add_readonly(ROOT)
set_all_marker_times(MARKER, FUTURE_UTC)
add_readonly(MARKER)

print(f"SEALED_ROOT={ROOT}")
print(f"MATERIAL_FILES={len(material_files)}")
print(f"MANIFEST_SHA256={manifest_hash}")
print("FINAL_MUTATION=WRITE_STOPPED_READONLY")
