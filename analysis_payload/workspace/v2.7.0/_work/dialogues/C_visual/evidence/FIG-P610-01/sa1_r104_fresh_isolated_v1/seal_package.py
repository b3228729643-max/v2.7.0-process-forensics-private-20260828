from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import stat
import subprocess


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P610-01\sa1_r104_fresh_isolated_v1").resolve()
MANIFEST = ROOT / "MANIFEST.csv"
MARKER = ROOT / "WRITE_STOPPED"
PREFLIGHT = ROOT / "SEAL_PREFLIGHT.json"
HANDOFF_ID = "C-FIG-P610-01-R104-SA1-FRESH-ISOLATED-V1"
REVIEWER_TYPE = "AI_SA1_VISUAL_REVIEW"
REVIEWER_INSTANCE = "/root/sa1_fig_p610_r104_fresh_isolated"
EXPECTED_CRITICAL = {
    "PAIR-0598", "PAIR-0634", "PAIR-0654", "PAIR-0670", "PAIR-0686",
    "PAIR-0691", "PAIR-0704", "PAIR-0738", "PAIR-0748", "PAIR-0751",
    "PAIR-0756",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def ads_count() -> int:
    root_text = str(ROOT).replace("'", "''")
    command = (
        f"$n=0; Get-ChildItem -LiteralPath '{root_text}' -Recurse -File | "
        "ForEach-Object { $n += @(Get-Item -LiteralPath $_.FullName -Stream * "
        "-ErrorAction Stop | Where-Object Stream -ne ':$DATA').Count }; "
        "Write-Output $n"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return int(completed.stdout.strip().splitlines()[-1])


def cache_pyc_count() -> int:
    count = 0
    for path in ROOT.rglob("*"):
        lower = path.name.lower()
        if lower in {"__pycache__", ".cache", "cache"} or path.suffix.lower() == ".pyc":
            count += 1
    return count


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


require(ROOT.is_dir(), "evidence root missing")
require(not MANIFEST.exists(), "manifest already exists")
require(not MARKER.exists(), "marker already exists")

glyph_machine = read_csv(ROOT / "inventories" / "glyph_inventory_machine.csv")
glyph_review = read_csv(ROOT / "review" / "manual_glyph_ledger_ai_sa1.csv")
pair_machine = read_csv(ROOT / "inventories" / "pair_inventory_machine.csv")
pair_review = read_csv(ROOT / "review" / "manual_pair_ledger_ai_sa1.csv")
hard_gates = read_csv(ROOT / "review" / "AI_SA1_HARD_GATE_LEDGER.csv")
roles = read_csv(ROOT / "review" / "AI_SA1_ROLE_PEER_LEDGER.csv")

require(len(glyph_machine) == 132 and len(glyph_review) == 132, "glyph count mismatch")
require(len(pair_machine) == 780 and len(pair_review) == 780, "pair count mismatch")
require(len({row["glyph_id"] for row in glyph_review}) == 132, "duplicate glyph review ID")
require(len({row["pair_id"] for row in pair_review}) == 780, "duplicate pair review ID")
require({row["glyph_id"] for row in glyph_machine} == {row["glyph_id"] for row in glyph_review}, "glyph ID set mismatch")
require({row["pair_id"] for row in pair_machine} == {row["pair_id"] for row in pair_review}, "pair ID set mismatch")

pair_review_by_id = {row["pair_id"]: row for row in pair_review}
for machine in pair_machine:
    review = pair_review_by_id[machine["pair_id"]]
    require(review["a_id"] == machine["a_id"] and review["b_id"] == machine["b_id"], f"pair member mismatch: {machine['pair_id']}")
    require(float(review["observed_overlap_px"]) == float(machine["raw_mask_overlap_px"]), f"pair overlap mismatch: {machine['pair_id']}")
    require(float(review["observed_clearance_px"]) == float(machine["raw_mask_clearance_px"]), f"pair clearance mismatch: {machine['pair_id']}")

for rows in (glyph_review, pair_review, hard_gates, roles):
    require(all(row.get("human_certification") == "false" for row in rows), "non-false human certification field")
    require(all(row.get("reviewer_type") == REVIEWER_TYPE for row in rows), "reviewer type mismatch")
    require(all(row.get("reviewer_instance") == REVIEWER_INSTANCE for row in rows), "reviewer instance mismatch")

critical_review = {
    row["pair_id"]
    for row in pair_review
    if row["decision_basis"] == "opened_contact_cell_plus_final_1x_and_8x_evidence"
}
require(critical_review == EXPECTED_CRITICAL, "critical review set mismatch")
require(ads_count() == 0, "ADS present before seal")
require(cache_pyc_count() == 0, "cache or pyc present before seal")

preflight_payload = {
    "handoff_id": HANDOFF_ID,
    "reviewer_type_value": REVIEWER_TYPE,
    "reviewer_instance_value": REVIEWER_INSTANCE,
    "glyph_machine_count": len(glyph_machine),
    "glyph_ai_review_count": len(glyph_review),
    "pair_machine_count": len(pair_machine),
    "pair_ai_review_count": len(pair_review),
    "critical_ai_review_count": len(critical_review),
    "hard_gate_row_count": len(hard_gates),
    "role_peer_row_count": len(roles),
    "human_certification_nonfalse_count": 0,
    "ads_count": 0,
    "cache_pyc_count": 0,
}
with PREFLIGHT.open("w", encoding="utf-8", newline="\n") as handle:
    json.dump(preflight_payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

excluded = {MANIFEST.resolve(), MARKER.resolve()}
files = sorted(
    (path.resolve() for path in ROOT.rglob("*") if path.is_file() and path.resolve() not in excluded),
    key=lambda path: str(path).casefold(),
)
require(PREFLIGHT.resolve() in files, "preflight not selected for manifest")
require(Path(__file__).resolve() in files, "seal script not selected for manifest")

with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=["resolved_path", "bytes", "sha256", "utc_mtime", "filetime_100ns"],
        lineterminator="\n",
    )
    writer.writeheader()
    for path in files:
        info = path.stat()
        utc_mtime = datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        filetime_100ns = info.st_mtime_ns // 100 + 116444736000000000
        writer.writerow(
            {
                "resolved_path": str(path),
                "bytes": info.st_size,
                "sha256": sha256(path),
                "utc_mtime": utc_mtime,
                "filetime_100ns": filetime_100ns,
            }
        )

manifest_rows = read_csv(MANIFEST)
require(len(manifest_rows) == len(files), "manifest row count mismatch")
require(MANIFEST.resolve() not in {Path(row["resolved_path"]).resolve() for row in manifest_rows}, "manifest self-listed")
require(MARKER.resolve() not in {Path(row["resolved_path"]).resolve() for row in manifest_rows}, "marker listed")
for row in manifest_rows:
    path = Path(row["resolved_path"])
    require(path.is_file(), f"manifest target missing: {path}")
    require(path.stat().st_size == int(row["bytes"]), f"manifest size mismatch: {path}")
    require(sha256(path) == row["sha256"], f"manifest hash mismatch: {path}")

for path in files:
    os.chmod(path, stat.S_IREAD)
os.chmod(MANIFEST, stat.S_IREAD)

sealed_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
with MARKER.open("x", encoding="utf-8", newline="\n") as handle:
    handle.write(f"HANDOFF_ID={HANDOFF_ID}\n")
    handle.write(f"SEALED_UTC={sealed_utc}\n")
    handle.write("MANIFEST=MANIFEST.csv\n")
    handle.write("POST_SEAL_WRITE_PROHIBITED=true\n")
