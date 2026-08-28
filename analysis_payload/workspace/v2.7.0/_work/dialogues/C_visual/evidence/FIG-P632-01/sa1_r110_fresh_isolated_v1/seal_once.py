from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa1_r110_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.json"
STAGED = ROOT / ".WRITE_STOPPED.staged"
WSTOP = ROOT / "WRITE_STOPPED"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def readonly(path: Path) -> None:
    FILE_ATTRIBUTE_READONLY = 0x1
    INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
    get_attrs = ctypes.windll.kernel32.GetFileAttributesW
    set_attrs = ctypes.windll.kernel32.SetFileAttributesW
    attrs = get_attrs(str(path))
    if attrs == INVALID_FILE_ATTRIBUTES:
        raise OSError(f"GetFileAttributesW failed: {path}")
    if not set_attrs(str(path), attrs | FILE_ATTRIBUTE_READONLY):
        raise OSError(f"SetFileAttributesW failed: {path}")


def is_readonly(path: Path) -> bool:
    return bool(ctypes.windll.kernel32.GetFileAttributesW(str(path)) & 0x1)


if ROOT != EXPECTED_ROOT:
    raise SystemExit(f"wrong evidence root: {ROOT}")
for forbidden in (MANIFEST, STAGED, WSTOP):
    if forbidden.exists():
        raise SystemExit(f"seal already started or completed: {forbidden.name}")

# The evidence root is intentionally flat; this also makes manifest closure exact.
subdirs = [p for p in ROOT.rglob("*") if p.is_dir()]
if subdirs:
    raise SystemExit(f"unexpected subdirectories: {[p.name for p in subdirs]}")

# Parse every existing JSON/CSV before the manifest is built.
for path in sorted(ROOT.glob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
for path in sorted(ROOT.glob("*.csv")):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        list(csv.reader(f))

# Verify that no manual-ID denominator was silently skipped or reordered.
object_text = (ROOT / "manual_object_adjudication.md").read_text(encoding="utf-8")
pair_text = (ROOT / "manual_pair_adjudication.md").read_text(encoding="utf-8")
critical_text = (ROOT / "manual_critical_glyph_view_hardgates.md").read_text(encoding="utf-8")
object_ids = re.findall(r"^- O(\d{2}) ", object_text, re.M)
pair_ids = re.findall(r"^- (P\d{3}) ", pair_text, re.M)
roi_ids = re.findall(r"^- (R\d{2}_[^ ]+)", critical_text, re.M)
glyph_ids = re.findall(r"^- (G\d{2}) ", critical_text, re.M)
view_ids = re.findall(r"^- (V\d{2}) ", critical_text, re.M)
gate_ids = re.findall(r"^- (HG\d{2}) ", critical_text, re.M)
with (ROOT / "pair_denominator_machine.csv").open("r", encoding="utf-8-sig", newline="") as f:
    machine_pair_ids = [row["PAIR_ID"] for row in csv.DictReader(f)]
with (ROOT / "manual_text_element_adjudication.csv").open("r", encoding="utf-8-sig", newline="") as f:
    text_ids = [row["ELEMENT_ID"] for row in csv.DictReader(f)]

coverage = {
    "objects": len(object_ids),
    "pairs": len(pair_ids),
    "text_elements": len(text_ids),
    "critical_rois": len(roi_ids),
    "glyph_controls": len(glyph_ids),
    "views": len(view_ids),
    "hard_gates": len(gate_ids),
}
expected_coverage = {
    "objects": 23,
    "pairs": 253,
    "text_elements": 29,
    "critical_rois": 9,
    "glyph_controls": 24,
    "views": 9,
    "hard_gates": 22,
}
if coverage != expected_coverage:
    raise SystemExit(f"manual coverage mismatch: {coverage}")
if any(len(ids) != len(set(ids)) for ids in (object_ids, pair_ids, text_ids, roi_ids, glyph_ids, view_ids, gate_ids)):
    raise SystemExit("duplicate manual IDs")
if pair_ids != machine_pair_ids:
    raise SystemExit("manual pair order/coverage does not match machine denominator")

# Forbidden residue checks before the terminal files exist.
all_paths = list(ROOT.rglob("*"))
cache_names = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache"}
cache_paths = [p for p in all_paths if p.name in cache_names]
pyc_paths = [p for p in all_paths if p.suffix.lower() in {".pyc", ".pyo"}]
reparse_paths = [p for p in all_paths if p.is_symlink() or (hasattr(p.stat(), "st_file_attributes") and p.stat().st_file_attributes & 0x400)]
if cache_paths or pyc_paths or reparse_paths:
    raise SystemExit("cache/pyc/reparse residue present")

ps = (
    "$r='" + str(ROOT).replace("'", "''") + "';"
    "$s=Get-ChildItem -LiteralPath $r -Recurse -Force -File|ForEach-Object{Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction Stop};"
    "@($s|Where-Object{$_.Stream -ne ':$DATA'}).Count"
)
ads_result = subprocess.run(
    [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe", "-NoProfile", "-Command", ps],
    check=True,
    capture_output=True,
    text=True,
)
ads_count = int(ads_result.stdout.strip().splitlines()[-1])
if ads_count != 0:
    raise SystemExit(f"ADS present: {ads_count}")

payload_paths = sorted(
    [p for p in ROOT.iterdir() if p.is_file() and p.name not in {MANIFEST.name, STAGED.name, WSTOP.name}],
    key=lambda p: p.name.lower(),
)
entries = [
    {
        "path": p.name,
        "bytes": p.stat().st_size,
        "sha256": sha256_file(p),
        "kind": "payload",
    }
    for p in payload_paths
]

seal_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
manifest_obj = {
    "schema_version": "1.0",
    "uid": "FIG-P632-01",
    "handoff_id": "C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-V1",
    "outcome": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
    "root": str(ROOT),
    "generated_utc": seal_time,
    "model": {
        "role": "SA1",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "fork_turns": "none",
    },
    "entries": entries,
    "self_and_control_exclusions": [
        {
            "path": "MANIFEST.json",
            "reason": "manifest self-hash is excluded to avoid recursion; its hash is recorded in WRITE_STOPPED"
        },
        {
            "path": "WRITE_STOPPED",
            "reason": "terminal control marker is excluded from payload; its content records the manifest hash and no file write follows its atomic appearance"
        },
        {
            "path": ".WRITE_STOPPED.staged",
            "reason": "transient read-only staging name used only before the terminal atomic rename; it must be absent from the final filesystem"
        }
    ],
    "closure": {
        "payload_entry_count": len(entries),
        "expected_final_file_count": len(entries) + 2,
        "expected_final_directory_count_including_root": 1,
        "final_allowed_unlisted_files": ["MANIFEST.json", "WRITE_STOPPED"],
        "transient_staging_must_be_absent": ".WRITE_STOPPED.staged",
        "filesystem_closed": True,
    },
    "validation": {
        "all_json_csv_parse": True,
        "manual_coverage": coverage,
        "manual_pair_order_matches_machine": True,
        "ads_count": 0,
        "cache_count": 0,
        "pyc_pyo_count": 0,
        "reparse_count": 0,
        "subdirectory_count": 0,
        "all_files_and_directories_readonly_before_terminal_rename": True,
        "postmarker_writes": 0,
    },
}
manifest_bytes = (json.dumps(manifest_obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
manifest_sha = sha256_bytes(manifest_bytes)
marker_bytes = (
    "WRITE_STOPPED\n"
    f"handoff_id=C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-V1\n"
    f"outcome=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3\n"
    f"manifest_sha256={manifest_sha}\n"
    f"payload_entry_count={len(entries)}\n"
    "postmarker_writes=0\n"
).encode("utf-8")

# Stage the final marker before writing the manifest so its content can carry the
# exact manifest hash. The terminal atomic rename below is the final filesystem mutation.
STAGED.write_bytes(marker_bytes)
MANIFEST.write_bytes(manifest_bytes)
if sha256_file(MANIFEST) != manifest_sha:
    raise SystemExit("manifest write/hash mismatch")
json.loads(MANIFEST.read_text(encoding="utf-8"))

pre_rename_names = {p.name for p in ROOT.iterdir() if p.is_file()}
expected_pre_rename = {e["path"] for e in entries} | {MANIFEST.name, STAGED.name}
if pre_rename_names != expected_pre_rename:
    raise SystemExit(f"pre-rename closure mismatch: {sorted(pre_rename_names ^ expected_pre_rename)}")

# Set every payload, manifest, staged marker, and the root directory read-only.
for path in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
    readonly(path)
readonly(ROOT)
if not all(is_readonly(p) for p in ROOT.iterdir()) or not is_readonly(ROOT):
    raise SystemExit("read-only attribute verification failed before terminal rename")

# ABSOLUTELY LAST FILESYSTEM MUTATION. Do not add any file/metadata writes below.
os.replace(STAGED, WSTOP)

result = {
    "outcome": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
    "payload_entries": len(entries),
    "final_expected_files": len(entries) + 2,
    "manifest": {"path": str(MANIFEST), "bytes": len(manifest_bytes), "sha256": manifest_sha},
    "write_stopped": {"path": str(WSTOP), "bytes": len(marker_bytes), "sha256": sha256_bytes(marker_bytes)},
    "postmarker_writes": 0,
}
print(json.dumps(result, ensure_ascii=False))
