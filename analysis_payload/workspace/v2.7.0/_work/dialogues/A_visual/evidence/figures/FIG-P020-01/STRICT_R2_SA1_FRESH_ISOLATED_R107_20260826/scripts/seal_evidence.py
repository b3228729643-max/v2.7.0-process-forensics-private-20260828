from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_MANIFEST = ROOT / "MANIFEST_SHA256.json"
CSV_MANIFEST = ROOT / "MANIFEST_SHA256.csv"
WRITE_STOPPED = ROOT / "WRITE_STOPPED"
EXCLUDED = {JSON_MANIFEST.name, CSV_MANIFEST.name, WRITE_STOPPED.name}
CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


for target in (JSON_MANIFEST, CSV_MANIFEST, WRITE_STOPPED):
    if target.exists():
        raise SystemExit(f"refusing reseal because {target.name} already exists")

bad_cache = [
    path.relative_to(ROOT).as_posix()
    for path in ROOT.rglob("*")
    if path.name in CACHE_NAMES or path.suffix.lower() in {".pyc", ".pyo"}
]
if bad_cache:
    raise SystemExit(f"cache/bytecode artifacts found: {bad_cache}")

entries = []
for path in sorted((item for item in ROOT.rglob("*") if item.is_file() and item.name not in EXCLUDED), key=lambda item: item.relative_to(ROOT).as_posix()):
    entries.append(
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    )

payload = {
    "schema": "common-payload-dual-manifest-v1",
    "handoff_id": "A-R107-P020-SA1-FRESH-ISOLATED-20260826",
    "canonical_uid": "FIG-P020-01",
    "official_round": "R107",
    "payload_exclusions": sorted(EXCLUDED),
    "payload_file_count": len(entries),
    "payload_byte_count": sum(row["bytes"] for row in entries),
    "entries": entries,
}
JSON_MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with CSV_MANIFEST.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=["path", "bytes", "sha256"])
    writer.writeheader()
    writer.writerows(entries)

with CSV_MANIFEST.open("r", encoding="utf-8", newline="") as fh:
    csv_entries = [
        {"path": row["path"], "bytes": int(row["bytes"]), "sha256": row["sha256"]}
        for row in csv.DictReader(fh)
    ]
json_entries = json.loads(JSON_MANIFEST.read_text(encoding="utf-8"))["entries"]
if csv_entries != json_entries:
    raise SystemExit("dual manifest common payload mismatch")

print(json.dumps({"payload_file_count": len(entries), "payload_byte_count": payload["payload_byte_count"], "common_payload_identical": True}, ensure_ascii=False))
