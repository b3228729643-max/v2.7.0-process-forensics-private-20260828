from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path


sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R3_SA3_FRESH_ISOLATED_R107_20260826")
JSON_MANIFEST = ROOT / "SEALED_MANIFEST.json"
TSV_MANIFEST = ROOT / "SEALED_MANIFEST.tsv"
MARKER = ROOT / "WRITE_STOPPED.txt"
EXCLUDED_NAMES = {JSON_MANIFEST.name, TSV_MANIFEST.name, MARKER.name}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def recursive_entries() -> list[Path]:
    return sorted(ROOT.rglob("*"), key=lambda path: path.relative_to(ROOT).as_posix())


def hygiene_scan() -> dict:
    entries = recursive_entries()
    caches = [str(path.relative_to(ROOT)) for path in entries if path.name == "__pycache__" or path.suffix.lower() == ".pyc"]
    reparses = []
    for path in entries:
        attrs = getattr(path.lstat(), "st_file_attributes", 0)
        if attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            reparses.append(str(path.relative_to(ROOT)))
    quoted_root = str(ROOT).replace("'", "''")
    ps = "$root = '" + quoted_root + "'\n" + r"""
$ads = @()
$files = Get-ChildItem -LiteralPath $root -Recurse -Force -File
foreach ($f in $files) {
  foreach ($s in @(Get-Item -LiteralPath $f.FullName -Stream * -ErrorAction Stop)) {
    if ($s.Stream -ne ':$DATA') { $ads += ($f.FullName + ':' + $s.Stream) }
  }
}
$ads | ConvertTo-Json -Compress
"""
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    raw = completed.stdout.strip()
    if not raw:
        ads = []
    else:
        parsed = json.loads(raw)
        ads = parsed if isinstance(parsed, list) else [parsed]
    return {"cache_or_pyc": caches, "reparse_points": reparses, "alternate_data_streams": ads}


if MARKER.exists() or JSON_MANIFEST.exists() or TSV_MANIFEST.exists():
    raise RuntimeError("Seal artifacts already exist; exactly-once seal refused")

pre = hygiene_scan()
if any(pre.values()):
    raise RuntimeError(f"Pre-seal hygiene failure: {pre}")

payload_files = [path for path in recursive_entries() if path.is_file() and path.name not in EXCLUDED_NAMES]
entries = [
    {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    for path in payload_files
]
canonical_payload = json.dumps(entries, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
payload_sha256 = hashlib.sha256(canonical_payload).hexdigest().upper()

json_payload = {
    "schema": "DUAL_COMMON_PAYLOAD_V1",
    "root": str(ROOT),
    "payload_entry_count": len(entries),
    "common_payload_sha256": payload_sha256,
    "entries": entries,
    "excluded_self_referential_seal_files": [JSON_MANIFEST.name, TSV_MANIFEST.name, MARKER.name],
}
JSON_MANIFEST.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")

with TSV_MANIFEST.open("w", encoding="utf-8", newline="") as stream:
    stream.write("#schema\tDUAL_COMMON_PAYLOAD_V1\n")
    stream.write(f"#common_payload_sha256\t{payload_sha256}\n")
    writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(entries)

# Verify the two manifests carry byte-for-byte equivalent entry payloads.
loaded_json = json.loads(JSON_MANIFEST.read_text(encoding="utf-8"))
with TSV_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
    lines = [line for line in stream if not line.startswith("#")]
loaded_tsv = list(csv.DictReader(lines, delimiter="\t"))
normalized_tsv = [{"path": row["path"], "bytes": int(row["bytes"]), "sha256": row["sha256"]} for row in loaded_tsv]
if loaded_json["entries"] != normalized_tsv:
    raise RuntimeError("Dual manifest common payload mismatch")

manifest_identity = {
    "json": {"path": JSON_MANIFEST.name, "bytes": JSON_MANIFEST.stat().st_size, "sha256": sha256(JSON_MANIFEST)},
    "tsv": {"path": TSV_MANIFEST.name, "bytes": TSV_MANIFEST.stat().st_size, "sha256": sha256(TSV_MANIFEST)},
}

# Lock all ordinary evidence and both manifests before the final content write.
for path in [item for item in recursive_entries() if item.is_file()]:
    os.chmod(path, stat.S_IREAD)

sealed_at = datetime.now().astimezone().isoformat(timespec="seconds")
marker_text = "\n".join(
    [
        "WRITE_STOPPED",
        f"root={ROOT}",
        f"sealed_at={sealed_at}",
        f"payload_entry_count={len(entries)}",
        f"common_payload_sha256={payload_sha256}",
        f"json_manifest_bytes={manifest_identity['json']['bytes']}",
        f"json_manifest_sha256={manifest_identity['json']['sha256']}",
        f"tsv_manifest_bytes={manifest_identity['tsv']['bytes']}",
        f"tsv_manifest_sha256={manifest_identity['tsv']['sha256']}",
        "post_seal_root_content_writes=0",
        "outcome=SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE",
        "",
    ]
)

# ABSOLUTE FINAL ROOT CONTENT WRITE.  No content write under ROOT occurs below.
with MARKER.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(marker_text)
    stream.flush()
    os.fsync(stream.fileno())
os.chmod(MARKER, stat.S_IREAD)

post = hygiene_scan()
all_files = [path for path in recursive_entries() if path.is_file()]
readonly_failures = []
for path in all_files:
    attrs = getattr(path.stat(), "st_file_attributes", 0)
    if not (attrs & getattr(stat, "FILE_ATTRIBUTE_READONLY", 0x1)):
        readonly_failures.append(path.relative_to(ROOT).as_posix())

summary = {
    "status": "SEALED_PASS" if not any(post.values()) and not readonly_failures else "SEALED_FAIL",
    "sealed_at": sealed_at,
    "root": str(ROOT),
    "payload_entry_count": len(entries),
    "common_payload_sha256": payload_sha256,
    "manifest_identity": manifest_identity,
    "write_stopped": {"path": MARKER.name, "bytes": MARKER.stat().st_size, "sha256": sha256(MARKER)},
    "ordinary_file_count_including_manifests_and_marker": len(all_files),
    "readonly_failure_count": len(readonly_failures),
    "readonly_failures": readonly_failures,
    "cache_or_pyc_count": len(post["cache_or_pyc"]),
    "reparse_count": len(post["reparse_points"]),
    "ads_count": len(post["alternate_data_streams"]),
    "post_seal_root_content_writes": 0,
    "outcome": "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE",
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
if summary["status"] != "SEALED_PASS":
    raise SystemExit(1)
