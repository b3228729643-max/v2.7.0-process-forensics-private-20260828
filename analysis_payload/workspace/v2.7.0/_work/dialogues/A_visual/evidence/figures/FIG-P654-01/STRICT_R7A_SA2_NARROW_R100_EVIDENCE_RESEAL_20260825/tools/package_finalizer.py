from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
EXCLUDED_FROM_PAYLOAD_MANIFEST = {
    "PACKAGE_MANIFEST.csv",
    "PACKAGE_MANIFEST.json",
    "PACKAGE_SHA256SUMS.txt",
    "TERMINAL_VALIDATION.json",
    "TERMINAL_VALIDATION_R2.json",
    "WRITE_STOPPED",
}
JSON_DECODE_FALLBACKS: list[dict[str, str]] = []


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(path: Path):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("gbk")
        JSON_DECODE_FALLBACKS.append({
            "relative_path": path.relative_to(ROOT).as_posix(),
            "raw_bytes_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "decode_method": "GBK/CP936 fallback after UTF-8 decode failure",
        })
    return json.loads(text)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_package() -> dict[str, object]:
    fallback_start = len(JSON_DECODE_FALLBACKS)
    json_files = sorted(ROOT.rglob("*.json"))
    csv_files = sorted(ROOT.rglob("*.csv"))
    json_errors: list[dict[str, str]] = []
    csv_errors: list[dict[str, str]] = []
    csv_rows: dict[str, int] = {}
    for path in json_files:
        try:
            read_json(path)
        except Exception as exc:  # evidence needs the exact parse error
            json_errors.append({"path": path.relative_to(ROOT).as_posix(), "error": repr(exc)})
    for path in csv_files:
        try:
            count = 0
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader, None)
                if not header or any(value == "" for value in header):
                    raise ValueError("empty or missing CSV header field")
                width = len(header)
                for row in reader:
                    count += 1
                    if len(row) != width:
                        raise ValueError(f"row {count + 1} has {len(row)} fields; expected {width}")
            csv_rows[path.relative_to(ROOT).as_posix()] = count
        except Exception as exc:
            csv_errors.append({"path": path.relative_to(ROOT).as_posix(), "error": repr(exc)})
    return {
        "observed_at_utc": utc_now(),
        "json_file_count": len(json_files),
        "csv_file_count": len(csv_files),
        "json_errors": json_errors,
        "csv_errors": csv_errors,
        "json_decode_fallbacks": JSON_DECODE_FALLBACKS[fallback_start:],
        "selected_csv_row_counts": {key: value for key, value in csv_rows.items() if key.startswith("manual/") or key in {"MACHINE_REUSE_IDENTITY_LEDGER.csv", "machine_reuse/object_manifest.csv", "machine_reuse/all_unordered_pairs.csv"}},
        "status": "PASS" if not json_errors and not csv_errors else "FAIL",
    }


def inspect_ads() -> dict[str, object]:
    env = dict(os.environ)
    env["R7A_ADS_ROOT"] = str(ROOT)
    command = (
        "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; "
        "$items=@(Get-ChildItem -LiteralPath $env:R7A_ADS_ROOT -Recurse -Force -File | "
        "ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Stream -ne ':$DATA' } | Select-Object FileName,Stream,Length }); "
        "$items | ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    raw = completed.stdout.strip()
    streams = [] if raw in {"", "null", "[]"} else json.loads(raw)
    if isinstance(streams, dict):
        streams = [streams]
    return {
        "observed_at_utc": utc_now(),
        "command_exit_code": completed.returncode,
        "stderr": completed.stderr,
        "alternate_stream_count": len(streams),
        "alternate_streams": streams,
        "status": "PASS" if completed.returncode == 0 and not streams else "FAIL",
    }


def manifest_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDED_FROM_PAYLOAD_MANIFEST:
            continue
        stat = path.stat()
        entries.append({
            "relative_path": rel,
            "bytes": stat.st_size,
            "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
            "sha256": sha256(path),
        })
    return entries


started = utc_now()
phase = read_json(ROOT / "PHASE_IDENTITY_BEFORE_CONSUMER.json")
consumer = read_json(ROOT / "CONSUMER_VALIDATION.json")
result = read_json(ROOT / "RESULT.json")
validator = ROOT / phase["validator"]["relative_path"]
manual_mismatches: list[str] = []
for item in phase["manual_ledgers"]:
    path = ROOT / item["relative_path"]
    if not path.is_file() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
        manual_mismatches.append(item["relative_path"])

preconditions = {
    "consumer_status_pass": consumer.get("status") == "PASS" and not consumer.get("errors"),
    "local_result_status_exact": result.get("status") == "LOCAL_SA2_PATCH_VERIFIED_AWAIT_R7A_ROOT",
    "validator_identity_matches_pre_execution": validator.stat().st_size == phase["validator"]["bytes"] and sha256(validator) == phase["validator"]["sha256"],
    "manual_identity_matches_pre_execution": not manual_mismatches,
    "consumer_declares_zero_manual_writes": consumer.get("writes_to_manual_ledgers") == 0,
}
if not all(preconditions.values()):
    raise SystemExit(json.dumps({"status": "PRECONDITION_FAIL", "preconditions": preconditions, "manual_mismatches": manual_mismatches}))

parse_result = parse_package()
write_json(ROOT / "PARSE_CHECK_R2.json", parse_result)
if parse_result["status"] != "PASS":
    raise SystemExit("package parse failed")

finalizer_result = {
    "status": "PACKAGE_ASSEMBLED_PENDING_TERMINAL",
    "started_at_utc": started,
    "assembled_at_utc": utc_now(),
    "finalizer": {"relative_path": SELF.relative_to(ROOT).as_posix(), "bytes": SELF.stat().st_size, "sha256": sha256(SELF)},
    "preconditions": preconditions,
    "manual_mismatches": manual_mismatches,
    "manual_files_modified": 0,
    "local_status": result["status"],
}
write_json(ROOT / "FINALIZER_RESULT_R2.json", finalizer_result)

ads_result = inspect_ads()
write_json(ROOT / "ADS_CHECK_R2.json", ads_result)
if ads_result["status"] != "PASS":
    raise SystemExit("ADS check failed")

entries = manifest_entries()
manifest_meta = {
    "generated_at_utc": utc_now(),
    "payload_file_count": len(entries),
    "self_referential_exclusions": sorted(EXCLUDED_FROM_PAYLOAD_MANIFEST),
    "entries": entries,
}
write_json(ROOT / "PACKAGE_MANIFEST.json", manifest_meta)
with (ROOT / "PACKAGE_MANIFEST.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["relative_path", "bytes", "mtime_utc", "sha256"])
    writer.writeheader()
    writer.writerows(entries)
(ROOT / "PACKAGE_SHA256SUMS.txt").write_text("".join(f"{item['sha256']}  {item['relative_path']}\n" for item in entries), encoding="utf-8")

manifest_mismatches: list[str] = []
for item in entries:
    path = ROOT / item["relative_path"]
    if not path.is_file() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
        manifest_mismatches.append(item["relative_path"])

terminal_parse = parse_package()
terminal_ads = inspect_ads()
terminal_validator_sha = sha256(validator)
terminal = {
    "status": "PACKAGE_SEALED_LOCAL_STATUS_UNCHANGED" if not manifest_mismatches and terminal_parse["status"] == "PASS" and terminal_ads["status"] == "PASS" and terminal_validator_sha == phase["validator"]["sha256"] else "FAIL",
    "terminal_at_utc": utc_now(),
    "actual_finalizer_result_relative_path": "FINALIZER_RESULT_R2.json",
    "actual_finalizer_result_exists": (ROOT / "FINALIZER_RESULT_R2.json").is_file(),
    "actual_finalizer_result_sha256": sha256(ROOT / "FINALIZER_RESULT_R2.json"),
    "consumer_validator_pre_sha256": phase["validator"]["sha256"],
    "consumer_validator_terminal_sha256": terminal_validator_sha,
    "consumer_validator_same_sha": terminal_validator_sha == phase["validator"]["sha256"],
    "consumer_validator_bytes": validator.stat().st_size,
    "consumer_status": consumer["status"],
    "consumer_errors": len(consumer["errors"]),
    "manual_decisions": consumer["manual_decision_counts"]["total"],
    "manifest_payload_file_count": len(entries),
    "manifest_mismatches": manifest_mismatches,
    "terminal_parse": terminal_parse,
    "terminal_ads": terminal_ads,
    "local_status": result["status"],
    "writes_after_write_stopped": 0,
}
write_json(ROOT / "TERMINAL_VALIDATION_R2.json", terminal)
if terminal["status"] == "FAIL":
    raise SystemExit("terminal validation failed")

terminal_path = ROOT / "TERMINAL_VALIDATION_R2.json"
write_stopped = {
    "status": "WRITE_STOPPED",
    "written_at_utc": utc_now(),
    "terminal_relative_path": "TERMINAL_VALIDATION_R2.json",
    "terminal_bytes": terminal_path.stat().st_size,
    "terminal_sha256": sha256(terminal_path),
    "local_status": result["status"],
    "instruction": "No further writes are permitted in this sealed R7A root."
}
write_json(ROOT / "WRITE_STOPPED", write_stopped)
print(json.dumps({"status": terminal["status"], "payload_files": len(entries), "validator_same_sha": terminal["consumer_validator_same_sha"], "write_stopped": True}))
sys.exit(0)
