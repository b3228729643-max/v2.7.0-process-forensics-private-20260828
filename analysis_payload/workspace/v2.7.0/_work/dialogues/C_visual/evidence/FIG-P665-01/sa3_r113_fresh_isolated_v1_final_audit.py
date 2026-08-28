from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import itertools
import json
import os
import sys
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa3_r113_fresh_isolated_v1")
MANIFEST = ROOT / "manifest.csv"
MARKER = ROOT / "FINAL_SEAL_MARKER.txt"
DIR_SNAPSHOT = ROOT / "directory_attributes_premarker.csv"
VERDICT = "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE"
HANDOFF_ID = "C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1"
UID = "FIG-P665-01"
WINDOWS_EPOCH_100NS = 116_444_736_000_000_000
FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def filetime_from_ns(ns: int) -> int:
    return ns // 100 + WINDOWS_EPOCH_100NS


def stat_creation_ns(st) -> int:
    return int(getattr(st, "st_birthtime_ns", st.st_ctime_ns))


def attrs(path: Path) -> int:
    st = path.stat(follow_symlinks=False)
    value = getattr(st, "st_file_attributes", None)
    if value is None:
        fail(f"Windows file attributes unavailable: {path}")
    return int(value)


class WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", ctypes.c_wchar * 296)]


def streams(path: Path) -> list[str]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    find_first = kernel32.FindFirstStreamW
    find_first.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(WIN32_FIND_STREAM_DATA), ctypes.c_uint32]
    find_first.restype = ctypes.c_void_p
    find_next = kernel32.FindNextStreamW
    find_next.argtypes = [ctypes.c_void_p, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
    find_next.restype = ctypes.c_int
    find_close = kernel32.FindClose
    find_close.argtypes = [ctypes.c_void_p]
    find_close.restype = ctypes.c_int
    data = WIN32_FIND_STREAM_DATA()
    handle = find_first(str(path), 0, ctypes.byref(data), 0)
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        fail(f"FindFirstStreamW failed for {path}: {ctypes.get_last_error()}")
    names = [data.cStreamName]
    try:
        while find_next(handle, ctypes.byref(data)):
            names.append(data.cStreamName)
        error = ctypes.get_last_error()
        if error not in (0, 38):
            fail(f"FindNextStreamW failed for {path}: {error}")
    finally:
        find_close(handle)
    return names


def parse_text_payloads(files: list[Path]) -> tuple[int, int, int, int, int]:
    csv_count = json_count = py_count = text_count = errors = 0
    for path in files:
        try:
            suffix = path.suffix.lower()
            if suffix == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as f:
                    rows = list(csv.reader(f))
                if not rows or len(rows[0]) == 0 or any(len(row) != len(rows[0]) for row in rows):
                    fail(f"ragged/empty CSV: {path}")
                csv_count += 1
            elif suffix == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
                json_count += 1
            elif suffix == ".py":
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
                py_count += 1
            elif suffix in {".md", ".txt", ".ps1"}:
                text = path.read_text(encoding="utf-8-sig")
                if "\x00" in text:
                    fail(f"NUL in text: {path}")
                text_count += 1
        except Exception:
            errors += 1
    return csv_count, json_count, py_count, text_count, errors


def main() -> None:
    if not ROOT.is_dir() or not MANIFEST.is_file() or not MARKER.is_file() or not DIR_SNAPSHOT.is_file():
        fail("sealed root, manifest, marker, or directory snapshot missing")

    marker_text = MARKER.read_text(encoding="utf-8-sig")
    physical_lines = marker_text.splitlines()
    expected_keys = ["HANDOFF_ID", "UID", "SEALED_ROOT", "MANIFEST_ROWS", "MANIFEST_SHA256", "VERDICT"]
    if len(physical_lines) != 6 or any(not line or line.count("=") != 1 for line in physical_lines):
        fail(f"marker physical-line format invalid: {physical_lines}")
    marker_pairs = [line.split("=", 1) for line in physical_lines]
    if [k for k, _ in marker_pairs] != expected_keys or any(not v for _, v in marker_pairs):
        fail("marker keys/order/nonempty constraint failed")
    marker = dict(marker_pairs)
    if marker["HANDOFF_ID"] != HANDOFF_ID or marker["UID"] != UID or marker["SEALED_ROOT"] != str(ROOT) or marker["VERDICT"] != VERDICT:
        fail("marker identity/verdict mismatch")

    manifest_sha = sha256(MANIFEST)
    if marker["MANIFEST_SHA256"] != manifest_sha:
        fail("marker manifest SHA mismatch")
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if int(marker["MANIFEST_ROWS"]) != len(rows):
        fail("marker manifest row count mismatch")

    all_files = sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.as_posix())
    all_dirs = [ROOT] + sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: p.as_posix())
    actual_payload = {p.relative_to(ROOT).as_posix(): p for p in all_files if p not in {MANIFEST, MARKER}}
    manifest_paths = [row["REL_PATH"] for row in rows]
    if len(set(manifest_paths)) != len(manifest_paths):
        fail("duplicate manifest paths")
    if set(manifest_paths) != set(actual_payload):
        fail(f"manifest/FS path-set mismatch: missing={sorted(set(actual_payload)-set(manifest_paths))}, extra={sorted(set(manifest_paths)-set(actual_payload))}")

    identity_mismatches = []
    attribute_mismatches = []
    for row in rows:
        path = actual_payload[row["REL_PATH"]]
        st = path.stat(follow_symlinks=False)
        actual = {
            "BYTES": str(st.st_size),
            "SHA256": sha256(path),
            "LAST_WRITE_FILETIME_UTC": str(filetime_from_ns(st.st_mtime_ns)),
            "CREATION_FILETIME_UTC": str(filetime_from_ns(stat_creation_ns(st))),
            "ATTRIBUTES_DECIMAL": str(attrs(path)),
        }
        for key in ("BYTES", "SHA256", "LAST_WRITE_FILETIME_UTC", "CREATION_FILETIME_UTC"):
            if actual[key] != row[key]:
                identity_mismatches.append(f"{row['REL_PATH']}:{key}:{row[key]}!={actual[key]}")
        if actual["ATTRIBUTES_DECIMAL"] != row["ATTRIBUTES_DECIMAL"]:
            attribute_mismatches.append(f"{row['REL_PATH']}:{row['ATTRIBUTES_DECIMAL']}!={actual['ATTRIBUTES_DECIMAL']}")
    if identity_mismatches:
        fail(f"manifest bytes/SHA/FILETIME mismatch: {identity_mismatches[:5]}")
    if attribute_mismatches:
        fail(f"manifest attribute mismatch: {attribute_mismatches[:5]}")

    with DIR_SNAPSHOT.open("r", encoding="utf-8-sig", newline="") as f:
        dir_rows = list(csv.DictReader(f))
    snapshot_dirs = {row["REL_DIR"]: row["ATTRIBUTES_DECIMAL"] for row in dir_rows}
    actual_dirs = {".": ROOT}
    actual_dirs.update({p.relative_to(ROOT).as_posix(): p for p in all_dirs if p != ROOT})
    if set(snapshot_dirs) != set(actual_dirs):
        fail("directory snapshot path-set mismatch")
    dir_attr_mismatches = [rel for rel, path in actual_dirs.items() if str(attrs(path)) != snapshot_dirs[rel]]
    if dir_attr_mismatches:
        fail(f"directory attribute mismatch: {dir_attr_mismatches}")

    not_readonly_files = [p.relative_to(ROOT).as_posix() for p in all_files if not (attrs(p) & FILE_ATTRIBUTE_READONLY)]
    not_readonly_dirs = ["." if p == ROOT else p.relative_to(ROOT).as_posix() for p in all_dirs if not (attrs(p) & FILE_ATTRIBUTE_READONLY)]
    if not_readonly_files or not_readonly_dirs:
        fail(f"ReadOnly failure files={not_readonly_files}, dirs={not_readonly_dirs}")

    reparse_items = [p for p in all_files + all_dirs if attrs(p) & FILE_ATTRIBUTE_REPARSE_POINT]
    if reparse_items:
        fail(f"reparse items present: {reparse_items}")
    cache_items = [p for p in all_files + all_dirs if p.name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} or p.suffix.lower() in {".pyc", ".pyo"}]
    if cache_items:
        fail(f"cache/pyc items present: {cache_items}")
    nondefault_ads = []
    for path in all_files:
        extra = [name for name in streams(path) if name != "::$DATA"]
        if extra:
            nondefault_ads.append((path.relative_to(ROOT).as_posix(), extra))
    if nondefault_ads:
        fail(f"nondefault ADS present: {nondefault_ads}")

    csv_count, json_count, py_count, text_count, parse_errors = parse_text_payloads(all_files)
    if parse_errors:
        fail(f"postseal parse errors: {parse_errors}")

    with (ROOT / "object_denominator_frozen.csv").open("r", encoding="utf-8-sig", newline="") as f:
        object_rows = list(csv.DictReader(f))
    object_ids = [row["OBJECT_ID"] for row in object_rows]
    if object_ids != [f"O{i:02d}" for i in range(1, 23)]:
        fail("sealed object denominator mismatch")
    with (ROOT / "all_unordered_pairs_machine.csv").open("r", encoding="utf-8-sig", newline="") as f:
        pair_rows = list(csv.DictReader(f))
    pair_set = {(row["OBJECT_A"], row["OBJECT_B"]) for row in pair_rows}
    if len(pair_rows) != 231 or pair_set != set(itertools.combinations(object_ids, 2)):
        fail("sealed all-pairs mismatch")

    acceptance = (ROOT / "manual_visual_acceptance.md").read_text(encoding="utf-8-sig")
    report = (ROOT / "sa3_report.md").read_text(encoding="utf-8-sig")
    preseal = json.loads((ROOT / "preseal_validation.json").read_text(encoding="utf-8-sig"))
    if f"`VERDICT = {VERDICT}`" not in acceptance or f"`RESULT: {VERDICT}`" not in report or preseal.get("status") != "PRESEAL_VALID":
        fail("sealed verdict/preseal parse mismatch")

    marker_named_files = [p for p in all_files if p.name == "FINAL_SEAL_MARKER.txt"]
    if marker_named_files != [MARKER]:
        fail(f"final marker is not unique: {marker_named_files}")
    marker_mtime = filetime_from_ns(MARKER.stat().st_mtime_ns)
    other_items = [p for p in all_files + all_dirs if p != MARKER]
    at_or_after = [p for p in other_items if filetime_from_ns(p.stat(follow_symlinks=False).st_mtime_ns) >= marker_mtime]
    if at_or_after:
        fail(f"items at-or-after marker: {at_or_after}")

    result = {
        "FINAL_AUDIT_OK": 1,
        "HANDOFF_ID": HANDOFF_ID,
        "UID": UID,
        "SEALED_ROOT": str(ROOT),
        "VERDICT": VERDICT,
        "MANIFEST_ROWS": len(rows),
        "MANIFEST_SHA256": manifest_sha,
        "MANIFEST_FS_PATH_MISMATCHES": 0,
        "MANIFEST_BYTES_SHA_FILETIME_MISMATCHES": 0,
        "FILE_ATTRIBUTE_MISMATCHES": 0,
        "DIRECTORY_ATTRIBUTE_MISMATCHES": 0,
        "NOT_READONLY_FILES": 0,
        "NOT_READONLY_DIRECTORIES_INCLUDING_ROOT": 0,
        "UNIQUE_FINAL_MARKER_COUNT": 1,
        "MARKER_STRICT_LATEST": 1,
        "AT_OR_AFTER_EXCLUDING_MARKER": 0,
        "POSTMARKER_CONTENT_COUNT": 0,
        "POSTMARKER_ATTRIBUTE_VIOLATION_COUNT": 0,
        "PARSE_ERRORS": 0,
        "NONDEFAULT_ADS": 0,
        "CACHE_PYC_ITEMS": 0,
        "REPARSE_ITEMS": 0,
        "OBJECT_DENOMINATOR": len(object_rows),
        "ALL_UNORDERED_PAIRS": len(pair_rows),
        "PARSED_CSV": csv_count,
        "PARSED_JSON": json_count,
        "PARSED_PYTHON": py_count,
        "PARSED_TEXT": text_count,
        "MARKER_LAST_WRITE_FILETIME_UTC": marker_mtime,
        "MAX_OTHER_LAST_WRITE_FILETIME_UTC": max(filetime_from_ns(p.stat(follow_symlinks=False).st_mtime_ns) for p in other_items),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"FINAL_AUDIT_OK": 0, "ERROR": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
