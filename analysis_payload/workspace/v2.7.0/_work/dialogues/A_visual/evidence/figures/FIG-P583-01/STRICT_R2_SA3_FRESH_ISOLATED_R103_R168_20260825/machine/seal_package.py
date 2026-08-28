from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "seal"
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P583_R2_R103_FRESH_SA3_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R103-P583-SA3-FRESH-ISOLATED-20260825.md")
INVENTORY = SEAL / "PACKAGE_INVENTORY.json"
MANIFEST_CSV = SEAL / "MANIFEST.csv"
MANIFEST_SHA = SEAL / "MANIFEST.sha256"
TEMP_MARKER = SEAL / ".WRITE_STOPPED.tmp"
FINAL_MARKER = ROOT / "WRITE_STOPPED"
SELF_EXCLUDED = {MANIFEST_CSV.resolve(), MANIFEST_SHA.resolve(), TEMP_MARKER.resolve(), FINAL_MARKER.resolve()}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest().upper()


def evidence_payload_files() -> list[Path]:
    return sorted(
        (
            path for path in ROOT.rglob("*")
            if path.is_file() and path.resolve() not in SELF_EXCLUDED
        ),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def enumerate_ads() -> list[str]:
    ps = (
        "$ErrorActionPreference='Stop';"
        "$target=[System.IO.Path]::GetFullPath($env:SA3_EVIDENCE_ROOT);"
        "$hits=@();"
        "Get-ChildItem -LiteralPath $target -Recurse -Force -File | ForEach-Object {"
        "Get-Item -LiteralPath $_.FullName -Stream * | Where-Object { $_.Stream -ne ':$DATA' } | ForEach-Object {"
        "$hits += ($_.FileName + ':' + $_.Stream)"
        "}};"
        "$hits | ConvertTo-Json -Compress"
    )
    child_env = os.environ.copy()
    child_env["SA3_EVIDENCE_ROOT"] = str(ROOT)
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", ps],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=child_env,
    )
    text = completed.stdout.strip()
    if not text:
        return []
    decoded = json.loads(text)
    return [decoded] if isinstance(decoded, str) else list(decoded)


def make_read_only(path: Path) -> None:
    os.chmod(path, path.stat().st_mode & ~stat.S_IWRITE)


def main() -> None:
    if FINAL_MARKER.exists() or TEMP_MARKER.exists() or MANIFEST_CSV.exists() or MANIFEST_SHA.exists():
        raise SystemExit("seal artifacts already exist; refusing a second seal")
    if not REPORT.is_file() or not HANDOFF.is_file():
        raise SystemExit("external report or handoff is missing")

    cache_dirs = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_dir() and "cache" in path.name.casefold()
    ]
    bytecode_files = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".pyc", ".pyo"}
    ]
    ads = enumerate_ads()
    if cache_dirs or bytecode_files or ads:
        raise SystemExit(
            json.dumps(
                {"cache_dirs": cache_dirs, "bytecode_files": bytecode_files, "alternate_data_streams": ads},
                ensure_ascii=False,
            )
        )

    crosscheck = json.loads((ROOT / "machine/final_crosscheck.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    if crosscheck["crosscheck_status"] != "PASS" or crosscheck["package_error_count"] != 0:
        raise SystemExit("final crosscheck is not clean PASS")
    if result["verdict"] != "PASS" or result["route"] != "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE":
        raise SystemExit("RESULT verdict or route mismatch")

    pre_inventory = evidence_payload_files()
    inventory_content = {
        "uid": "FIG-P583-01",
        "handoff_id": "A-R103-P583-SA3-FRESH-ISOLATED-20260825",
        "round": "R103",
        "physical_page": 633,
        "policy": "R168",
        "evidence_root": str(ROOT),
        "payload_file_count_including_inventory": len(pre_inventory) + 1,
        "directory_count_including_root": 1 + sum(path.is_dir() for path in ROOT.rglob("*")),
        "external_file_count": 2,
        "manifest_rule": "all evidence files except MANIFEST.csv, MANIFEST.sha256, temporary marker, and WRITE_STOPPED; plus external report and handoff",
        "manifest_self_exclusions": [
            "seal/MANIFEST.csv",
            "seal/MANIFEST.sha256",
            "seal/.WRITE_STOPPED.tmp",
            "WRITE_STOPPED",
        ],
        "cache_directory_count": 0,
        "bytecode_file_count": 0,
        "alternate_data_stream_count": 0,
        "verdict": "PASS",
        "route": "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE",
    }
    INVENTORY.write_text(json.dumps(inventory_content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload = evidence_payload_files()
    if len(payload) != inventory_content["payload_file_count_including_inventory"]:
        raise SystemExit("payload count changed during inventory creation")

    entries: list[dict[str, str | int]] = []
    for path in payload:
        entries.append(
            {
                "scope": "EVIDENCE_ROOT",
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    for scope, path in (("EXTERNAL_REPORT", REPORT), ("EXTERNAL_HANDOFF", HANDOFF)):
        entries.append(
            {
                "scope": scope,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    with MANIFEST_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["scope", "path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(entries)
    with MANIFEST_SHA.open("w", encoding="utf-8", newline="\n") as stream:
        for entry in entries:
            stream.write(f"{entry['sha256']}  {entry['bytes']}  {entry['scope']}:{entry['path']}\n")

    manifest_csv_hash = sha256(MANIFEST_CSV)
    manifest_sha_hash = sha256(MANIFEST_SHA)
    inventory_hash = sha256(INVENTORY)
    report_hash = sha256(REPORT)
    handoff_hash = sha256(HANDOFF)
    result_hash = sha256(ROOT / "RESULT.json")
    sealed_at = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    marker_text = (
        "WRITE_STOPPED=TRUE\n"
        "UID=FIG-P583-01\n"
        "HANDOFF_ID=A-R103-P583-SA3-FRESH-ISOLATED-20260825\n"
        f"SEALED_AT_UTC={sealed_at}\n"
        f"EVIDENCE_PAYLOAD_FILE_COUNT={len(payload)}\n"
        "EXTERNAL_FILE_COUNT=2\n"
        f"MANIFEST_ENTRY_COUNT={len(entries)}\n"
        f"MANIFEST_CSV_SHA256={manifest_csv_hash}\n"
        f"MANIFEST_SHA256_FILE_SHA256={manifest_sha_hash}\n"
        f"PACKAGE_INVENTORY_SHA256={inventory_hash}\n"
        f"RESULT_JSON_SHA256={result_hash}\n"
        f"EXTERNAL_REPORT_SHA256={report_hash}\n"
        f"EXTERNAL_HANDOFF_SHA256={handoff_hash}\n"
        "CACHE_DIRECTORY_COUNT=0\n"
        "BYTECODE_FILE_COUNT=0\n"
        "ALTERNATE_DATA_STREAM_COUNT=0\n"
        "POST_SEAL_WRITE_COUNT=0\n"
        "VERDICT=PASS\n"
        "ROUTE=SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE\n"
        "MANIFEST_SELF_EXCLUSIONS=seal/MANIFEST.csv|seal/MANIFEST.sha256|seal/.WRITE_STOPPED.tmp|WRITE_STOPPED\n"
    )

    TEMP_MARKER.write_text(marker_text, encoding="utf-8", newline="\n")

    for path in evidence_payload_files() + [MANIFEST_CSV, MANIFEST_SHA, TEMP_MARKER, REPORT, HANDOFF]:
        make_read_only(path)
    directories = sorted(
        (path for path in ROOT.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        make_read_only(directory)
    make_read_only(ROOT)

    os.replace(TEMP_MARKER, FINAL_MARKER)
    print(
        json.dumps(
            {
                "sealed": True,
                "payload_file_count": len(payload),
                "manifest_entry_count": len(entries),
                "write_stopped": str(FINAL_MARKER),
                "route": "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
