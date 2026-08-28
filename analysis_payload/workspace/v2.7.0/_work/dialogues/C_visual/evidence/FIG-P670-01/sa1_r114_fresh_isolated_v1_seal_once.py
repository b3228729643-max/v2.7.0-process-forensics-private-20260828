from __future__ import annotations

import csv
import hashlib
import os
import stat
import time
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa1_r114_fresh_isolated_v1")
STAGE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa1_r114_fresh_isolated_v1.WRITE_STOPPED.stage")
MARKER = ROOT / "WRITE_STOPPED"
MANIFEST = ROOT / "MANIFEST.csv"
EXPECTED_DIRS = {"machine", "renders"}
EXPECTED = {
    "HANDOFF_ID": "C-FIG-P670-01-R114-SA1-FRESH-ISOLATED-V1",
    "UID": "FIG-P670-01",
    "SEALED_ROOT": str(ROOT),
    "MANIFEST_ROWS": "24",
    "MANIFEST_SHA256": "03FD9EE825D961C1DA3F215653F9F7A35C37850CE5575B648B12E27828AC5B81",
    "VERDICT": "PASS",
    "MARKER_ENCODING": "UTF-8_NO_BOM",
    "FINAL_TOKEN": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if not ROOT.is_dir() or not STAGE.is_file() or MARKER.exists():
    raise SystemExit("precondition failure")

raw = STAGE.read_bytes()
if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n"):
    raise SystemExit("stage encoding/newline failure")
text = raw.decode("utf-8")
lines = text.splitlines()
bad_lines = [line for line in lines if not line or line.count("=") != 1 or not all(line.split("=", 1))]
if len(lines) != 8 or bad_lines:
    raise SystemExit("stage physical-line failure")
parsed = dict(line.split("=", 1) for line in lines)
if len(parsed) != 8 or parsed != EXPECTED:
    raise SystemExit("stage key/value failure")

with MANIFEST.open(newline="", encoding="utf-8") as handle:
    manifest_rows = list(csv.DictReader(handle))
if len(manifest_rows) != 24 or sha256(MANIFEST) != EXPECTED["MANIFEST_SHA256"]:
    raise SystemExit("manifest identity failure")
manifest_rel = {row["RELATIVE_PATH"] for row in manifest_rows}
actual_files: set[str] = set()
actual_dirs: set[str] = set()
for current, dirs, files in os.walk(ROOT):
    current_path = Path(current)
    actual_dirs.update((current_path / directory).relative_to(ROOT).as_posix() for directory in dirs)
    actual_files.update((current_path / filename).relative_to(ROOT).as_posix() for filename in files)
if actual_files != manifest_rel | {"MANIFEST.csv"} or actual_dirs != EXPECTED_DIRS:
    raise SystemExit("pre-seal filesystem identity failure")
for row in manifest_rows:
    path = ROOT / row["RELATIVE_PATH"]
    if path.stat().st_size != int(row["BYTES"]) or sha256(path) != row["SHA256"]:
        raise SystemExit("pre-seal row identity failure: " + row["RELATIVE_PATH"])

root_items = [ROOT, ROOT / "machine", ROOT / "renders", MANIFEST]
root_items.extend(ROOT / row["RELATIVE_PATH"] for row in manifest_rows)
latest_ns = max(path.stat().st_mtime_ns for path in root_items)
future_ns = max(time.time_ns() + 3_600_000_000_000, latest_ns + 3_600_000_000_000)
os.utime(STAGE, ns=(future_ns, future_ns))

for path in root_items:
    os.chmod(path, stat.S_IREAD)
os.chmod(STAGE, stat.S_IREAD)

stage_stat = STAGE.stat()
readonly_bit = getattr(stat, "FILE_ATTRIBUTE_READONLY", 0x1)
if not (getattr(stage_stat, "st_file_attributes", 0) & readonly_bit):
    raise SystemExit("stage readonly failure")
if stage_stat.st_mtime_ns <= latest_ns or stage_stat.st_mtime_ns <= time.time_ns():
    raise SystemExit("stage strict-future FILETIME failure")

print("STAGE_UTF8_NO_BOM=True")
print("STAGE_PHYSICAL_LINES=8")
print("STAGE_BAD_LINES=0")
print("STAGE_UNIQUE_KEYS=8")
print("STAGE_READONLY=True")
print("STAGE_STRICT_FUTURE=True")
print("PRESEAL_FS_IDENTITY_DIFF=0")
print("FINAL_OPERATION=single_move")

os.replace(STAGE, MARKER)
