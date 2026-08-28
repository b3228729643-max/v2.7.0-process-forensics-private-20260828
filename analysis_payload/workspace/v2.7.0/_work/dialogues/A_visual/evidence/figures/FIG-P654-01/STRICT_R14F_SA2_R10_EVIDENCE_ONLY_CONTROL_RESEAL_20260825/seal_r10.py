from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parent
MANIFEST_JSON = ROOT / "PAYLOAD_MANIFEST.json"
MANIFEST_CSV = ROOT / "PAYLOAD_MANIFEST.csv"
WRITE_STOPPED = ROOT / "WRITE_STOPPED.json"
EXCLUDED = {MANIFEST_JSON.name, MANIFEST_CSV.name, WRITE_STOPPED.name}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def utc_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def ordinary_files() -> list[Path]:
    return sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix())


def parse_gate(paths: list[Path]) -> dict[str, object]:
    csv_paths = [p for p in paths if p.suffix.casefold() == ".csv"]
    json_paths = [p for p in paths if p.suffix.casefold() == ".json"]
    png_paths = [p for p in paths if p.suffix.casefold() == ".png"]
    pdf_paths = [p for p in paths if p.suffix.casefold() == ".pdf"]
    failures: list[str] = []
    for path in csv_paths:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                list(csv.DictReader(f))
        except Exception as exc:
            failures.append(f"CSV {path.relative_to(ROOT).as_posix()}: {exc}")
    for path in json_paths:
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            failures.append(f"JSON {path.relative_to(ROOT).as_posix()}: {exc}")
    for path in png_paths:
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception as exc:
            failures.append(f"PNG {path.relative_to(ROOT).as_posix()}: {exc}")
    for path in pdf_paths:
        try:
            with fitz.open(path) as document:
                if document.page_count < 1:
                    raise ValueError("zero pages")
        except Exception as exc:
            failures.append(f"PDF {path.relative_to(ROOT).as_posix()}: {exc}")
    return {
        "csv_count": len(csv_paths),
        "json_count": len(json_paths),
        "png_count": len(png_paths),
        "pdf_count": len(pdf_paths),
        "failure_count": len(failures),
        "failures": failures,
    }


def ads_gate() -> dict[str, object]:
    ps_root = str(ROOT).replace("'", "''")
    command = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
        f"$root='{ps_root}';"
        "$items=@();"
        "foreach($f in @(Get-ChildItem -LiteralPath $root -Recurse -File)){"
        "$streams=@(Get-Item -LiteralPath $f.FullName -Stream * -ErrorAction Stop | "
        "Where-Object {$_.Stream -ne ':$DATA'});"
        "foreach($s in $streams){$items += [pscustomobject]@{"
        "path=$f.FullName.Substring($root.Length+1);stream=$s.Stream;length=$s.Length}}};"
        "[pscustomobject]@{ads=$items} | ConvertTo-Json -Depth 5 -Compress"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        return {
            "failure_count": 1,
            "failures": [completed.stderr.strip() or f"PowerShell exit {completed.returncode}"],
            "alternate_data_stream_count": None,
            "alternate_data_streams": [],
        }
    payload = json.loads(completed.stdout.lstrip("\ufeff"))
    ads = payload.get("ads") or []
    if isinstance(ads, dict):
        ads = [ads]
    return {
        "failure_count": 0,
        "failures": [],
        "alternate_data_stream_count": len(ads),
        "alternate_data_streams": ads,
    }


if any(path.exists() for path in (MANIFEST_JSON, MANIFEST_CSV, WRITE_STOPPED)):
    raise SystemExit("seal controls already exist; refusing rerun")

# Refuse sealing unless the already locked, single-run consumer passed.
consumer = json.loads((ROOT / "consumer_validation.json").read_text(encoding="utf-8"))
if consumer.get("failure_count") != 0 or consumer.get("conclusion") != "LOCAL_SA2_PATCH_VERIFIED_AWAIT_R10_ROOT":
    raise SystemExit("consumer validation is not a clean local SA2 result")
lock = json.loads((ROOT / "CONSUMER_VALIDATOR_LOCK.json").read_text(encoding="utf-8"))
if sha256(ROOT / "consumer_validator.py") != lock.get("validator_sha256"):
    raise SystemExit("consumer validator changed after pre-run lock")

# Confirm every frozen manual ledger still has the recorded bytes and SHA.
manual_identity = json.loads((ROOT / "MANUAL_LEDGER_IDENTITY.json").read_text(encoding="utf-8"))
for entry in manual_identity["ledgers"]:
    path = ROOT / entry["path"]
    if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
        raise SystemExit(f"manual ledger changed after lock: {entry['path']}")

pre_paths = ordinary_files()
pre_parse = parse_gate(pre_paths)
pre_ads = ads_gate()
pyc = [p.relative_to(ROOT).as_posix() for p in pre_paths if p.suffix.casefold() == ".pyc"]
pycache = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("__pycache__") if p.is_dir()]
if pre_parse["failure_count"] or pre_ads["failure_count"] or pre_ads["alternate_data_stream_count"] or pyc or pycache:
    raise SystemExit(json.dumps({"parse": pre_parse, "ads": pre_ads, "pyc": pyc, "pycache": pycache}, ensure_ascii=False))

payload_paths = [p for p in pre_paths if p.name not in EXCLUDED]
entries: list[dict[str, object]] = []
for path in payload_paths:
    entries.append(
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "mtime_utc": utc_mtime(path),
            "sha256": sha256(path),
        }
    )

manifest_payload = {
    "root": ROOT.name,
    "algorithm": "SHA-256",
    "self_excluded": sorted(EXCLUDED),
    "payload_count": len(entries),
    "payload_bytes": sum(int(e["bytes"]) for e in entries),
    "entries": entries,
}
MANIFEST_JSON.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with MANIFEST_CSV.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["path", "bytes", "mtime_utc", "sha256"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(entries)

# Read both manifests back and prove file set, bytes, mtime, and SHA equality.
json_manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
with MANIFEST_CSV.open("r", encoding="utf-8", newline="") as f:
    csv_manifest = list(csv.DictReader(f))
json_map = {e["path"]: e for e in json_manifest["entries"]}
csv_map = {e["path"]: e for e in csv_manifest}
if set(json_map) != set(csv_map):
    raise SystemExit("CSV/JSON manifest file sets differ")
for rel in json_map:
    a, b = json_map[rel], csv_map[rel]
    if str(a["bytes"]) != b["bytes"] or a["mtime_utc"] != b["mtime_utc"] or a["sha256"] != b["sha256"]:
        raise SystemExit(f"CSV/JSON manifest identity mismatch: {rel}")

with_manifests = ordinary_files()
final_parse = parse_gate(with_manifests)
final_ads = ads_gate()
final_pyc = [p.relative_to(ROOT).as_posix() for p in with_manifests if p.suffix.casefold() == ".pyc"]
final_pycache = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("__pycache__") if p.is_dir()]
if final_parse["failure_count"] or final_ads["failure_count"] or final_ads["alternate_data_stream_count"] or final_pyc or final_pycache:
    raise SystemExit(json.dumps({"parse": final_parse, "ads": final_ads, "pyc": final_pyc, "pycache": final_pycache}, ensure_ascii=False))

manifest_json_identity = {
    "path": MANIFEST_JSON.name,
    "bytes": MANIFEST_JSON.stat().st_size,
    "mtime_utc": utc_mtime(MANIFEST_JSON),
    "sha256": sha256(MANIFEST_JSON),
}
manifest_csv_identity = {
    "path": MANIFEST_CSV.name,
    "bytes": MANIFEST_CSV.stat().st_size,
    "mtime_utc": utc_mtime(MANIFEST_CSV),
    "sha256": sha256(MANIFEST_CSV),
}
prior_latest_ns = max(p.stat().st_mtime_ns for p in with_manifests)
prior_latest_path = max(with_manifests, key=lambda p: p.stat().st_mtime_ns)
while time.time_ns() <= prior_latest_ns:
    time.sleep(0.001)

seal = {
    "sealed_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "root": ROOT.name,
    "terminal": "LOCAL_SA2_PATCH_VERIFIED_AWAIT_R10_ROOT",
    "payload_excludes": sorted(EXCLUDED),
    "payload_count": len(entries),
    "payload_bytes": manifest_payload["payload_bytes"],
    "ordinary_file_count_after_write_stopped": len(entries) + 3,
    "csv_manifest": manifest_csv_identity,
    "json_manifest": manifest_json_identity,
    "manifest_file_set_diff_count": 0,
    "manifest_bytes_diff_count": 0,
    "manifest_mtime_diff_count": 0,
    "manifest_sha256_diff_count": 0,
    "parse_gate": final_parse,
    "ads_gate": final_ads,
    "pyc_file_count": len(final_pyc),
    "pycache_directory_count": len(final_pycache),
    "consumer_validator": {
        "sha256": lock["validator_sha256"],
        "run_limit": lock["run_limit"],
        "failure_count": consumer["failure_count"],
        "conclusion": consumer["conclusion"],
    },
    "denominators": {
        "objects_N": 116,
        "glyphs": 95,
        "graphics": 21,
        "unordered_pairs_C": 6670,
        "critical_pairs": 50,
        "manual_rows": 192,
        "taxonomy_groups": 10,
    },
    "previous_latest_path": prior_latest_path.relative_to(ROOT).as_posix(),
    "previous_latest_mtime_utc": utc_mtime(prior_latest_path),
    "write_stopped_is_strictly_latest": True,
    "no_post_seal_writes_authorized": True,
}
WRITE_STOPPED.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
stop_ns = WRITE_STOPPED.stat().st_mtime_ns
if stop_ns <= prior_latest_ns:
    raise SystemExit("WRITE_STOPPED is not strictly newer than every prior ordinary file")
if len(ordinary_files()) != len(entries) + 3:
    raise SystemExit("ordinary-file inventory changed unexpectedly during sealing")

print(
    json.dumps(
        {
            "payload_count": len(entries),
            "ordinary_file_count": len(entries) + 3,
            "payload_bytes": manifest_payload["payload_bytes"],
            "csv_count": final_parse["csv_count"],
            "json_count": final_parse["json_count"],
            "png_count": final_parse["png_count"],
            "pdf_count": final_parse["pdf_count"],
            "ads_count": final_ads["alternate_data_stream_count"],
            "pyc_count": len(final_pyc),
            "pycache_count": len(final_pycache),
            "write_stopped_strictly_latest": True,
            "terminal": seal["terminal"],
        },
        ensure_ascii=False,
    )
)
