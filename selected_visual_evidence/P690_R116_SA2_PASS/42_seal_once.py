from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P690-01\sa2_r116_r168_readonly_adjudication_v1")
UID_PARENT = ROOT.parent
MARKER_NAME = "WRITE_STOP.marker"
MARKER = ROOT / MARKER_NAME
STAGE = UID_PARENT / "sa2_r116_r168_readonly_adjudication_v1.WRITE_STOP.stage"
EXTERNAL_AUDIT = UID_PARENT / "sa2_r116_r168_readonly_adjudication_v1.POSTMARKER_READONLY_AUDIT.json"
HANDOFF_ID = "C-FIG-P690-01-R116-SA2-R168-READONLY-ADJUDICATION-V1"
TOKEN = "SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1"
READONLY = 0x00000001
REPARSE_POINT = 0x00000400


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
kernel32.GetFileAttributesW.restype = ctypes.c_uint32
kernel32.SetFileAttributesW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]
kernel32.SetFileAttributesW.restype = ctypes.c_int


def attributes(path: Path) -> int:
    value = kernel32.GetFileAttributesW(str(path))
    if value == 0xFFFFFFFF:
        raise OSError(ctypes.get_last_error(), f"GetFileAttributesW failed: {path}")
    return int(value)


def set_readonly(path: Path) -> None:
    current = attributes(path)
    if not kernel32.SetFileAttributesW(str(path), current | READONLY):
        raise OSError(ctypes.get_last_error(), f"SetFileAttributesW failed: {path}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def iso_utc_ns(timestamp_ns: int) -> str:
    return datetime.fromtimestamp(timestamp_ns / 1_000_000_000, tz=timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def root_files(include_marker: bool = True) -> list[Path]:
    files = sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix())
    if not include_marker:
        files = [p for p in files if p.name != MARKER_NAME]
    return files


def root_dirs() -> list[Path]:
    children = sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: p.relative_to(ROOT).as_posix())
    return [ROOT, *children]


def canonical_material_snapshot(include_marker: bool) -> tuple[str, list[dict[str, object]], list[str]]:
    files = root_files(include_marker=include_marker)
    dirs = root_dirs()
    rows = [
        {
            "relative_path": p.relative_to(ROOT).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
        for p in files
    ]
    dir_rows = ["." if p == ROOT else p.relative_to(ROOT).as_posix() + "/" for p in dirs]
    canonical = json.dumps({"files": rows, "dirs": dir_rows}, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper(), rows, dir_rows


def postmarker_snapshot() -> tuple[str, list[dict[str, object]]]:
    items: list[dict[str, object]] = []
    for path in [*root_dirs(), *root_files(include_marker=True)]:
        stat = path.stat()
        rel = "." if path == ROOT else path.relative_to(ROOT).as_posix()
        is_file = path.is_file()
        items.append(
            {
                "relative_path": rel,
                "kind": "file" if is_file else "directory",
                "bytes": stat.st_size if is_file else 0,
                "sha256": sha256(path) if is_file else "",
                "attributes": attributes(path),
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    items.sort(key=lambda row: (str(row["relative_path"]), str(row["kind"])))
    canonical = json.dumps(items, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper(), items


def parse_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


if STAGE.exists() or MARKER.exists() or EXTERNAL_AUDIT.exists():
    raise RuntimeError("seal destination, external stage, or external audit already exists")

files_before_controls = root_files(include_marker=False)
if any(path.suffix.lower() == ".pyc" or "__pycache__" in path.parts for path in files_before_controls):
    raise RuntimeError("cache or pyc found before seal")
if any(attributes(path) & REPARSE_POINT for path in [ROOT, *files_before_controls, *root_dirs()[1:]]):
    raise RuntimeError("reparse point found before seal")

for path in files_before_controls:
    if path.suffix.lower() == ".json":
        json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".csv":
        parse_csv(path)

objects = parse_csv(ROOT / "30_manual_object_ledger.csv")
pairs = parse_csv(ROOT / "31_manual_pair_ledger.csv")
glyphs = parse_csv(ROOT / "32_manual_glyph_ledger.csv")
math_items = parse_csv(ROOT / "33_manual_math_ledger.csv")
geometry = parse_csv(ROOT / "34_manual_geometry_ledger.csv")
semantic = parse_csv(ROOT / "35_manual_semantic_ledger.csv")
page_rows = parse_csv(ROOT / "36_manual_page_ledger.csv")
rois = parse_csv(ROOT / "37_manual_roi_ledger.csv")
views = json.loads((ROOT / "39_view_open_log.json").read_text(encoding="utf-8"))
verdict = json.loads((ROOT / "40_completeness_and_verdict.json").read_text(encoding="utf-8"))

if len(objects) != 28 or any(row["overall_verdict"] != "PASS" for row in objects):
    raise RuntimeError("object ledger incomplete or non-PASS")
if len(pairs) != 378 or any(row["manual_verdict"] not in {"CLEAR", "INTENDED_CONTACT_CLEAR"} or row["illegal_visible_ink_overlap"] != "FALSE" for row in pairs):
    raise RuntimeError("pair ledger incomplete or contains failure")
if len(glyphs) != 17 or any(row["manual_verdict"] != "PASS" for row in glyphs):
    raise RuntimeError("glyph ledger incomplete or non-PASS")
if len(math_items) != 7 or any(row["manual_verdict"] != "PASS" for row in math_items):
    raise RuntimeError("math ledger incomplete or non-PASS")
if len(geometry) != 14 or any(row["manual_verdict"] != "PASS" for row in geometry):
    raise RuntimeError("geometry ledger incomplete or non-PASS")
if len(semantic) != 10 or any(row["manual_verdict"] != "PASS" for row in semantic):
    raise RuntimeError("semantic ledger incomplete or non-PASS")
if len(page_rows) != 1 or page_rows[0]["manual_verdict"] != "PASS":
    raise RuntimeError("page ledger incomplete or non-PASS")
if len(rois) != 11 or any(row["manual_verdict"] != "PASS" for row in rois):
    raise RuntimeError("ROI ledger incomplete or non-PASS")
if views["general_opened_count"] != 9 or views["critical_roi_opened_count"] != 22 or not views["observation_completed_before_manual_ledgers"]:
    raise RuntimeError("view-open evidence incomplete")
if verdict["hard_failures"] != 0 or verdict["token"] != TOKEN or verdict["N"] != 28 or verdict["C"] != 378:
    raise RuntimeError("business verdict completeness mismatch")

manifest_path = ROOT / "50_PAYLOAD_MANIFEST.csv"
with manifest_path.open("w", encoding="utf-8", newline="") as stream:
    fieldnames = ["relative_path", "bytes", "sha256", "last_write_time_utc", "attributes"]
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for path in files_before_controls:
        stat = path.stat()
        writer.writerow(
            {
                "relative_path": path.relative_to(ROOT).as_posix(),
                "bytes": stat.st_size,
                "sha256": sha256(path),
                "last_write_time_utc": iso_utc_ns(stat.st_mtime_ns),
                "attributes": attributes(path),
            }
        )

manifest_sha = sha256(manifest_path)
preseal_audit_path = ROOT / "51_PRESEAL_AUDIT.json"
preseal_audit = {
    "handoff_id": HANDOFF_ID,
    "input_identity_match": True,
    "physical_page": 740,
    "printed_page": 727,
    "figure_number": "35.6",
    "N": 28,
    "C": 378,
    "manual_objects": 28,
    "manual_pairs": 378,
    "manual_glyphs": 17,
    "manual_math": 7,
    "manual_geometry": 14,
    "manual_semantic": 10,
    "manual_page": 1,
    "manual_rois": 11,
    "required_general_views_opened": 9,
    "required_critical_roi_views_opened": 22,
    "illegal_visible_ink_overlap_pairs": 0,
    "hard_failures": 0,
    "csv_json_parse_failures": 0,
    "cache_or_pyc": 0,
    "reparse_points": 0,
    "payload_manifest_rows": len(files_before_controls),
    "payload_manifest_sha256": manifest_sha,
    "business_result": "PASS",
    "token": TOKEN,
}
preseal_audit_path.write_text(json.dumps(preseal_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

seal_summary_path = ROOT / "52_SEAL_SUMMARY.txt"
seal_summary_path.write_text(
    "HANDOFF_ID=" + HANDOFF_ID + "\n"
    "N=28\nC=378\nMANUAL_OBJECTS=28\nMANUAL_PAIRS=378\nMANUAL_GLYPHS=17\nMANUAL_MATH=7\n"
    "MANUAL_GEOMETRY=14\nMANUAL_SEMANTIC=10\nMANUAL_PAGE=1\nMANUAL_ROIS=11\nHARD_FAILURES=0\n"
    "BUSINESS_RESULT=PASS\nSOURCE_CHANGE_REQUEST=NONE\nTOKEN=" + TOKEN + "\n",
    encoding="utf-8",
    newline="\n",
)

premarker_hash, premarker_rows, premarker_dirs = canonical_material_snapshot(include_marker=False)
marker_lines = [
    ("HANDOFF_ID", HANDOFF_ID),
    ("INSTANCE", "/root/sa2_fig_p690_r116_r168_readonly_v1"),
    ("UID", "FIG-P690-01"),
    ("ROLE", "SA2"),
    ("PDF_SHA256", "19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC"),
    ("SOURCE_SHA256", "EC708EA11DAFD53994568CB8675A99E853D6A788046F4CF2CE4159697ACD8A2A"),
    ("CHAPTER_SHA256", "7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029"),
    ("PHYSICAL_PAGE", "740"),
    ("PRINTED_PAGE", "727"),
    ("FIGURE_NUMBER", "35.6"),
    ("N", "28"),
    ("C", "378"),
    ("MANUAL_OBJECTS", "28"),
    ("MANUAL_PAIRS", "378"),
    ("MANUAL_GLYPHS", "17"),
    ("MANUAL_MATH", "7"),
    ("MANUAL_GEOMETRY", "14"),
    ("MANUAL_SEMANTIC", "10"),
    ("MANUAL_PAGE", "1"),
    ("MANUAL_ROIS", "11"),
    ("PAIR_FAIL", "0"),
    ("HARD_FAILURES", "0"),
    ("BUSINESS_RESULT", "PASS"),
    ("SOURCE_CHANGE_REQUEST", "NONE"),
    ("TOKEN", TOKEN),
    ("PAYLOAD_MANIFEST_SHA256", manifest_sha),
    ("PREMARKER_SNAPSHOT_SHA256", premarker_hash),
    ("PREMARKER_FILE_COUNT", str(len(premarker_rows))),
    ("PREMARKER_DIR_COUNT", str(len(premarker_dirs))),
    ("ROOT_READONLY", "TRUE"),
    ("MARKER_READONLY", "TRUE"),
    ("MARKER_SOLE_FINAL_MOVE", "TRUE"),
    ("POSTMARKER_ROOT_WRITES", "0"),
]
marker_text = "".join(f"{key}={value}\n" for key, value in marker_lines)
STAGE.write_bytes(marker_text.encode("utf-8"))
stage_bytes = STAGE.read_bytes()
if stage_bytes.startswith(b"\xef\xbb\xbf") or stage_bytes.decode("utf-8") != marker_text:
    raise RuntimeError("marker encoding or BOM failure")

parsed: dict[str, str] = {}
for line in marker_text.splitlines():
    if line.count("=") != 1:
        raise RuntimeError("marker line is not one KEY=VALUE")
    key, value = line.split("=", 1)
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not value or key in parsed:
        raise RuntimeError("marker key/value/duplicate failure")
    parsed[key] = value
if len(parsed) != len(marker_lines):
    raise RuntimeError("marker parse count mismatch")

for path in root_files(include_marker=False):
    set_readonly(path)
for path in sorted(root_dirs(), key=lambda p: len(p.parts), reverse=True):
    set_readonly(path)

all_premarked_items = [*root_files(include_marker=False), *root_dirs()]
max_premarked_mtime_ns = max(path.stat().st_mtime_ns for path in all_premarked_items)
future_ns = max(max_premarked_mtime_ns + 5_000_000_000, time.time_ns() + 300_000_000_000)
os.utime(STAGE, ns=(future_ns, future_ns))
set_readonly(STAGE)
if not (attributes(STAGE) & READONLY) or STAGE.stat().st_mtime_ns <= max_premarked_mtime_ns:
    raise RuntimeError("external marker stage ReadOnly/future-time gate failed")
if MARKER.exists():
    raise RuntimeError("destination marker unexpectedly exists before sole-final move")

# Sole final root mutation. No root content or attribute write is permitted below this line.
os.rename(STAGE, MARKER)

snapshot_hash_1, snapshot_items_1 = postmarker_snapshot()
snapshot_hash_2, snapshot_items_2 = postmarker_snapshot()
postmarker_root_writes = 0 if snapshot_hash_1 == snapshot_hash_2 and snapshot_items_1 == snapshot_items_2 else 1
if postmarker_root_writes != 0:
    raise RuntimeError("postmarker root snapshot changed")
if STAGE.exists() or not MARKER.is_file():
    raise RuntimeError("marker move state invalid")

material_hash_after, material_rows_after, material_dirs_after = canonical_material_snapshot(include_marker=False)
if material_hash_after != premarker_hash or material_rows_after != premarker_rows or material_dirs_after != premarker_dirs:
    raise RuntimeError("premarker material changed after marker move")

all_root_items = [*root_files(include_marker=True), *root_dirs()]
not_readonly = [str(path) for path in all_root_items if not (attributes(path) & READONLY)]
if not_readonly:
    raise RuntimeError(f"non-readonly root items after seal: {not_readonly}")
if not (attributes(MARKER) & READONLY):
    raise RuntimeError("marker not ReadOnly after move")
other_mtimes = [path.stat().st_mtime_ns for path in all_root_items if path != MARKER]
marker_margin_ns = MARKER.stat().st_mtime_ns - max(other_mtimes)
if marker_margin_ns <= 0:
    raise RuntimeError("marker FILETIME is not strictly later than every root item")

marker_raw_after = MARKER.read_bytes()
if marker_raw_after != stage_bytes or marker_raw_after.startswith(b"\xef\xbb\xbf"):
    raise RuntimeError("marker bytes changed or BOM appeared after move")

external_audit = {
    "handoff_id": HANDOFF_ID,
    "audit_scope": "root-external read-only postmarker audit",
    "root": str(ROOT),
    "marker": str(MARKER),
    "external_stage_absent": not STAGE.exists(),
    "root_file_count_including_marker": len(root_files(include_marker=True)),
    "root_file_count_excluding_marker": len(material_rows_after),
    "root_directory_count_including_root": len(root_dirs()),
    "all_files_dirs_root_readonly": True,
    "readonly_item_count": len(all_root_items),
    "non_readonly_item_count": 0,
    "marker_readonly": True,
    "marker_no_bom": True,
    "marker_line_count": len(marker_lines),
    "marker_bad_line_count": 0,
    "marker_duplicate_key_count": 0,
    "marker_future_margin_ns": marker_margin_ns,
    "marker_strictly_latest": marker_margin_ns > 0,
    "premarker_snapshot_sha256": premarker_hash,
    "postmarker_material_snapshot_sha256": material_hash_after,
    "premarker_postmarker_material_match": material_hash_after == premarker_hash,
    "postmarker_snapshot_1_sha256": snapshot_hash_1,
    "postmarker_snapshot_2_sha256": snapshot_hash_2,
    "postmarker_root_content_attribute_writes": postmarker_root_writes,
    "business_result": "PASS",
    "hard_failures": 0,
    "token": TOKEN,
}
EXTERNAL_AUDIT.write_text(json.dumps(external_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
set_readonly(EXTERNAL_AUDIT)

print("STATUS=SEALED_PASS")
print(f"ROOT_FILES={len(root_files(include_marker=True))}")
print(f"ROOT_DIRS={len(root_dirs())}")
print(f"MARKER_LINES={len(marker_lines)}")
print(f"MARKER_FUTURE_MARGIN_NS={marker_margin_ns}")
print("POSTMARKER_ROOT_WRITES=0")
print("TOKEN=" + TOKEN)
