from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R2_SA1_FRESH_ISOLATED_R108_20260826").resolve()
REPORT_DIR = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P580-01\R108_SA1_FRESH_ISOLATED").resolve()
EXPECTED_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R2_SA1_FRESH_ISOLATED_R108_20260826").resolve()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


if ROOT != EXPECTED_ROOT or not ROOT.is_dir():
    raise SystemExit("Refusing to seal an unexpected root")

wstop = ROOT / "WRITE_STOPPED"
if wstop.exists():
    raise SystemExit("WRITE_STOPPED already exists; refusing a second seal")

manifest_csv = ROOT / "PAYLOAD_MANIFEST.csv"
manifest_sha = ROOT / "PAYLOAD_MANIFEST.sha256"
excluded = {manifest_csv.name, manifest_sha.name, wstop.name}
payload = sorted(
    (p for p in ROOT.rglob("*") if p.is_file() and p.name not in excluded),
    key=lambda p: p.relative_to(ROOT).as_posix(),
)
rows = [
    {
        "RELATIVE_PATH": p.relative_to(ROOT).as_posix(),
        "SIZE_BYTES": p.stat().st_size,
        "SHA256": digest(p),
    }
    for p in payload
]

with manifest_csv.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["RELATIVE_PATH", "SIZE_BYTES", "SHA256"])
    writer.writeheader()
    writer.writerows(rows)

manifest_sha.write_text(
    "".join(f"{row['SHA256']}  {row['RELATIVE_PATH']}\n" for row in rows),
    encoding="utf-8",
)

# Prepare the final marker outside the root and make it read-only before the move.
# os.replace below is the absolute final mutation under ROOT.
prepared = REPORT_DIR / ".WRITE_STOPPED.prepared"
if prepared.exists():
    os.chmod(prepared, stat.S_IWRITE | stat.S_IREAD)
    prepared.unlink()
sealed_at = datetime.now().astimezone().isoformat()
prepared.write_text(
    "\n".join(
        [
            "WRITE_STOPPED",
            "HANDOFF_ID=A-R108-P580-SA1-FRESH-ISOLATED-20260826",
            f"SEALED_AT={sealed_at}",
            "VERDICT=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
            "ROOT_WRITES_AFTER_THIS_MOVE=FORBIDDEN",
            "",
        ]
    ),
    encoding="utf-8",
)
os.chmod(prepared, stat.S_IREAD)

for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=str):
    os.chmod(path, stat.S_IREAD)

os.replace(prepared, wstop)  # ABSOLUTE LAST ROOT MUTATION

# From here onward the root is read only. The audit result is written outside it.
with manifest_csv.open("r", newline="", encoding="utf-8-sig") as f:
    audited_rows = list(csv.DictReader(f))

hash_failures = []
size_failures = []
missing = []
for row in audited_rows:
    path = ROOT / Path(row["RELATIVE_PATH"])
    if not path.is_file():
        missing.append(row["RELATIVE_PATH"])
        continue
    if path.stat().st_size != int(row["SIZE_BYTES"]):
        size_failures.append(row["RELATIVE_PATH"])
    if digest(path) != row["SHA256"]:
        hash_failures.append(row["RELATIVE_PATH"])

actual_payload = sorted(
    p.relative_to(ROOT).as_posix()
    for p in ROOT.rglob("*")
    if p.is_file() and p.name not in excluded
)
manifest_paths = sorted(row["RELATIVE_PATH"] for row in audited_rows)
readonly_failures = [
    p.relative_to(ROOT).as_posix()
    for p in ROOT.rglob("*")
    if p.is_file() and (p.stat().st_mode & stat.S_IWRITE)
]

sha_lines = [line for line in manifest_sha.read_text(encoding="utf-8").splitlines() if line]
audit = {
    "handoff_id": "A-R108-P580-SA1-FRESH-ISOLATED-20260826",
    "root": str(ROOT),
    "sealed_at": sealed_at,
    "wstop_present": wstop.is_file(),
    "wstop_readonly": not bool(wstop.stat().st_mode & stat.S_IWRITE),
    "manifest_csv_rows": len(audited_rows),
    "manifest_sha_lines": len(sha_lines),
    "dual_manifest_count_match": len(audited_rows) == len(sha_lines),
    "payload_path_set_match": actual_payload == manifest_paths,
    "missing": missing,
    "size_failures": size_failures,
    "hash_failures": hash_failures,
    "readonly_failures": readonly_failures,
    "unexpected_root_files": sorted(
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.relative_to(ROOT).as_posix() not in set(manifest_paths)
        and p.name not in {manifest_csv.name, manifest_sha.name, wstop.name}
    ),
}
audit["audit_pass"] = all(
    [
        audit["wstop_present"],
        audit["wstop_readonly"],
        audit["dual_manifest_count_match"],
        audit["payload_path_set_match"],
        not missing,
        not size_failures,
        not hash_failures,
        not readonly_failures,
        not audit["unexpected_root_files"],
    ]
)
(REPORT_DIR / "ROOT_EXTERNAL_READONLY_AUDIT.json").write_text(
    json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(audit, ensure_ascii=True, indent=2))
