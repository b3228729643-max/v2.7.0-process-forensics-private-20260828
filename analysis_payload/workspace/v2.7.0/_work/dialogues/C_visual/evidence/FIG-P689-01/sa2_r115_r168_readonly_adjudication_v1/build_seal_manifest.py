from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MATERIAL = ROOT / "material_manifest.tsv"
SEAL = ROOT / "seal_manifest.txt"
FINAL_MARKER_NAME = "WSTOP.SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1.marker"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


excluded = {MATERIAL.name, SEAL.name, FINAL_MARKER_NAME}
files = sorted(
    (p for p in ROOT.rglob("*") if p.is_file() and p.name not in excluded),
    key=lambda p: p.relative_to(ROOT).as_posix(),
)
rows = ["RELATIVE_PATH\tBYTES\tSHA256"]
total_bytes = 0
for path in files:
    size = path.stat().st_size
    total_bytes += size
    rows.append(f"{path.relative_to(ROOT).as_posix()}\t{size}\t{sha256(path)}")
MATERIAL.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")

material_hash = sha256(MATERIAL)
seal_lines = [
    "HANDOFF_ID=C-FIG-P689-01-R115-SA2-R168-READONLY-ADJUDICATION-V1",
    "INSTANCE=/root/sa2_fig_p689_r115_r168_readonly_v1",
    f"ROOT={ROOT}",
    "RESULT=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1",
    f"MATERIAL_FILE_COUNT={len(files)}",
    f"MATERIAL_TOTAL_BYTES={total_bytes}",
    f"MATERIAL_MANIFEST_BYTES={MATERIAL.stat().st_size}",
    f"MATERIAL_MANIFEST_SHA256={material_hash}",
    "MANUAL_OBJECT_COUNT=31",
    "MANUAL_PAIR_COUNT=465",
    "MANUAL_PAIR_CLEAR=452",
    "MANUAL_PAIR_LEGAL=13",
    "UNRESOLVED_COUNT=0",
    "HARD_DEFECT_COUNT=0",
    "SOURCE_CHANGE=NONE",
    "FINAL_MARKER_EXCLUDED_UNTIL_SOLE_FINAL_MOVE=true",
]
SEAL.write_text("\n".join(seal_lines) + "\n", encoding="utf-8", newline="\n")
print(f"MATERIAL_FILE_COUNT={len(files)}")
print(f"MATERIAL_TOTAL_BYTES={total_bytes}")
print(f"MATERIAL_MANIFEST_SHA256={material_hash}")
print(f"SEAL_MANIFEST_SHA256={sha256(SEAL)}")
