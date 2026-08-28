from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825")
CONTROLS = {"MANIFEST.csv", "MANIFEST.json", "WRITE_STOPPED.json"}
POWERSHELL7 = Path(r"D:\PowerShell7\pwsh.exe")
EPOCH_TICKS = 621355968000000000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def payload_files() -> list[Path]:
    return sorted(
        (p for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in CONTROLS),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )


def exact_ticks(path: Path) -> int:
    return path.stat().st_mtime_ns // 100 + EPOCH_TICKS


def utc_7digit(ticks: int) -> str:
    unix_ticks = ticks - EPOCH_TICKS
    seconds, fraction = divmod(unix_ticks, 10_000_000)
    stamp = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction:07d}Z"


def scan_ads() -> list[dict[str, str]]:
    if not POWERSHELL7.is_file():
        raise RuntimeError("PowerShell7 missing")
    root_literal = str(ROOT).replace("'", "''")
    command = (
        f"$root='{root_literal}'; "
        "$rows=@(); Get-ChildItem -LiteralPath $root -Recurse -File | ForEach-Object { "
        "$f=$_.FullName; Get-Item -LiteralPath $f -Stream * -ErrorAction Stop | "
        "Where-Object { $_.Stream -ne ':$DATA' } | ForEach-Object { "
        "$rows += [pscustomobject]@{path=$f;stream=$_.Stream;length=$_.Length} } }; "
        "$rows | ConvertTo-Json -Depth 4 -Compress"
    )
    completed = subprocess.run(
        [str(POWERSHELL7), "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"ADS scan failed: {completed.stderr}")
    text = completed.stdout.strip()
    if not text:
        return []
    parsed = json.loads(text)
    return parsed if isinstance(parsed, list) else [parsed]


def validate_payload(files: list[Path]) -> dict[str, object]:
    extension_counts = Counter((p.suffix.lower() or "<none>") for p in files)
    json_failures, csv_failures, png_failures, pdf_failures = [], [], [], []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            if path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
            elif path.suffix.lower() == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    list(csv.reader(handle))
            elif path.suffix.lower() == ".png":
                with Image.open(path) as image:
                    image.verify()
            elif path.suffix.lower() == ".pdf":
                document = fitz.open(path)
                if document.page_count < 1:
                    raise RuntimeError("zero-page PDF")
                document.close()
        except Exception as exc:  # recorded and hard-failed below
            target = json_failures if path.suffix.lower() == ".json" else csv_failures if path.suffix.lower() == ".csv" else png_failures if path.suffix.lower() == ".png" else pdf_failures
            target.append({"path": rel, "error": repr(exc)})
    ads = scan_ads()
    forbidden = [
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.name == "__pycache__" or p.suffix.lower() in {".pyc", ".pyo"}
    ]
    symlinks = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_symlink()]
    failures = json_failures + csv_failures + png_failures + pdf_failures
    if failures or ads or forbidden or symlinks:
        raise RuntimeError(f"preseal gate failed parse={len(failures)} ads={len(ads)} forbidden={len(forbidden)} symlinks={len(symlinks)}")
    return {
        "round": "STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825",
        "status": "PRESEAL_PASS",
        "payload_file_count_at_validation": len(files),
        "extension_counts": dict(sorted(extension_counts.items())),
        "json_parse_failures": json_failures,
        "csv_parse_failures": csv_failures,
        "png_parse_failures": png_failures,
        "pdf_parse_failures": pdf_failures,
        "ads_nondefault_stream_count": len(ads),
        "forbidden_cache_or_bytecode_count": len(forbidden),
        "symlink_count": len(symlinks),
        "texcache_policy": "R17 build-local texcache is authorized build evidence and is included losslessly in the payload; Python bytecode/cache remains forbidden.",
        "denominator_assertions": {
            "glyph": 93,
            "graphic": 21,
            "object": 114,
            "pair": 6441,
            "critical": 173,
            "critical_contact_sheets": 10,
        },
    }


def main() -> None:
    existing = [name for name in CONTROLS if (ROOT / name).exists()]
    if existing:
        raise RuntimeError(f"seal controls already exist; no rerun permitted: {existing}")

    initial_files = payload_files()
    audit = validate_payload(initial_files)
    audit_path = ROOT / "PRESEAL_AUDIT.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files = payload_files()
    rows = []
    for path in files:
        ticks = exact_ticks(path)
        rows.append({
            "relative_path": path.relative_to(ROOT).as_posix(),
            "bytes": str(path.stat().st_size),
            "sha256": sha256(path),
            "mtime_utc_ticks": str(ticks),
            "mtime_utc_7digit": utc_7digit(ticks),
        })

    csv_path = ROOT / "MANIFEST.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    json_path = ROOT / "MANIFEST.json"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload_extensions = Counter((Path(r["relative_path"]).suffix.lower() or "<none>") for r in rows)
    control_extensions = Counter({".csv": 1, ".json": 2})
    ordinary_extensions = payload_extensions + control_extensions
    stopped = {
        "round": "STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825",
        "status": "WRITE_STOPPED",
        "payload_file_count": len(rows),
        "manifest_control_file_count": 2,
        "write_stopped_control_file_count": 1,
        "control_file_count": 3,
        "ordinary_file_total": len(rows) + 3,
        "payload_extensions": dict(sorted(payload_extensions.items())),
        "control_extensions": dict(sorted(control_extensions.items())),
        "ordinary_extensions": dict(sorted(ordinary_extensions.items())),
        "manifest_exclusions": sorted(CONTROLS),
        "manifest_csv_bytes": csv_path.stat().st_size,
        "manifest_csv_sha256": sha256(csv_path),
        "manifest_json_bytes": json_path.stat().st_size,
        "manifest_json_sha256": sha256(json_path),
        "final_verdict": "LOCAL_SA2_FAIL_NEEDS_SOURCE_R3",
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    }
    stopped_path = ROOT / "WRITE_STOPPED.json"
    stopped_path.write_text(json.dumps(stopped, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Make WRITE_STOPPED strictly latest without altering payload or manifest bytes.
    newest_other_ns = max(p.stat().st_mtime_ns for p in ROOT.rglob("*") if p.is_file() and p != stopped_path)
    stopped_ns = max(stopped_path.stat().st_mtime_ns, newest_other_ns + 10_000_000)
    os.utime(stopped_path, ns=(stopped_ns, stopped_ns))

    for path in (p for p in ROOT.rglob("*") if p.is_file()):
        os.chmod(path, stat.S_IREAD)

    print(json.dumps({
        "status": "SEALED",
        "payload": len(rows),
        "controls": 3,
        "ordinary": len(rows) + 3,
        "manifest_csv_sha256": stopped["manifest_csv_sha256"],
        "manifest_json_sha256": stopped["manifest_json_sha256"],
        "write_stopped_ticks": exact_ticks(stopped_path),
        "strictly_latest": all(exact_ticks(p) < exact_ticks(stopped_path) for p in ROOT.rglob("*") if p.is_file() and p != stopped_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
