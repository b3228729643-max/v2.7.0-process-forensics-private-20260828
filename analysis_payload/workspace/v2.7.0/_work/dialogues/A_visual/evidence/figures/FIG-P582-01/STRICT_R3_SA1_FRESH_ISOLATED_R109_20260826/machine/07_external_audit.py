from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R3_SA1_FRESH_ISOLATED_R109_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf")
EXPECTED_PDF_SHA256 = "936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9"
EXPECTED_PDF_SIZE = 4967054


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def is_readonly(path: Path) -> bool:
    attrs = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_READONLY", 1))


def is_reparse(path: Path) -> bool:
    attrs = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def scan() -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = [ROOT]
    for base, dirnames, filenames in os.walk(ROOT, followlinks=False):
        base_path = Path(base)
        dirs.extend(base_path / name for name in dirnames)
        files.extend(base_path / name for name in filenames)
    return sorted(files), sorted(dirs)


def named_ads() -> list[str]:
    ps = (
        "$ErrorActionPreference='Stop';"
        f"$r={json.dumps(str(ROOT), ensure_ascii=False)};"
        "Get-ChildItem -LiteralPath $r -Recurse -Force -File | ForEach-Object {"
        "$p=$_.FullName; Get-Item -LiteralPath $p -Stream * | "
        "Where-Object { $_.Stream -ne ':$DATA' -and $_.Stream -ne '$DATA' } | "
        "ForEach-Object { $p + '::' + $_.Stream } }"
    )
    cp = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return [line.strip() for line in cp.stdout.splitlines() if line.strip()]


def main() -> None:
    files, dirs = scan()
    rel = lambda p: str(p.relative_to(ROOT)).replace("\\", "/")
    payload_manifest = ROOT / "PAYLOAD_MANIFEST.csv"
    seal_manifest = ROOT / "SEAL_MANIFEST.json"
    marker = ROOT / "WRITE_STOPPED"
    with payload_manifest.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    seal = json.loads(seal_manifest.read_text(encoding="utf-8"))
    marker_data = json.loads(marker.read_text(encoding="utf-8"))
    payload_actual = [p for p in files if p.name not in {payload_manifest.name, seal_manifest.name, marker.name}]
    expected_paths = [r["relative_path"] for r in rows]
    actual_paths = [rel(p) for p in payload_actual]
    identity_errors = []
    if actual_paths != expected_paths:
        identity_errors.append("payload path set/order differs")
    row_map = {r["relative_path"]: r for r in rows}
    for path in payload_actual:
        rp = rel(path)
        row = row_map.get(rp)
        if row is None:
            identity_errors.append(f"unmanifested:{rp}")
            continue
        st = path.stat()
        if st.st_size != int(row["size_bytes"]):
            identity_errors.append(f"size:{rp}")
        if st.st_mtime_ns != int(row["mtime_ns"]):
            identity_errors.append(f"mtime:{rp}")
        if sha256(path) != row["sha256"]:
            identity_errors.append(f"sha256:{rp}")
        if row["readonly"].lower() != "true" or not is_readonly(path):
            identity_errors.append(f"readonly:{rp}")
    payload_sha = sha256(payload_manifest)
    seal_sha = sha256(seal_manifest)
    marker_sha = sha256(marker)
    if payload_sha != seal["payload_manifest"]["sha256"]:
        identity_errors.append("payload manifest hash vs seal")
    if payload_sha != marker_data["payload_manifest_sha256"]:
        identity_errors.append("payload manifest hash vs marker")
    if seal_sha != marker_data["seal_manifest_sha256"]:
        identity_errors.append("seal manifest hash vs marker")
    if seal["payload_files"] != rows:
        identity_errors.append("seal embedded payload rows differ")
    readonly_failures = [rel(p) for p in files if not is_readonly(p)]
    reparse = [rel(p) for p in files + dirs if is_reparse(p)]
    pyc_cache = [rel(p) for p in files + dirs if p.name == "__pycache__" or p.suffix.lower() == ".pyc"]
    ads = named_ads()
    markers = [p for p in files if p.name == "WRITE_STOPPED"]
    other_files = [p for p in files if p != marker]
    marker_strict_latest = len(markers) == 1 and markers[0] == marker and all(p.stat().st_mtime_ns < marker.stat().st_mtime_ns for p in other_files)
    postmarker = [rel(p) for p in other_files if p.stat().st_mtime_ns > marker.stat().st_mtime_ns]
    pdf_identity = {
        "size_bytes": PDF.stat().st_size,
        "sha256": sha256(PDF),
        "pass": PDF.stat().st_size == EXPECTED_PDF_SIZE and sha256(PDF) == EXPECTED_PDF_SHA256,
    }
    audit = {
        "audit": "ROOT_EXTERNAL_READ_ONLY_AUDITOR",
        "root": str(ROOT),
        "manifest_fs_identity_pass": not identity_errors,
        "manifest_fs_identity_errors": identity_errors,
        "payload_files": len(rows),
        "root_files_total": len(files),
        "all_files_readonly_pass": not readonly_failures,
        "readonly_failures": readonly_failures,
        "ads_count": len(ads),
        "ads": ads,
        "pyc_or_cache_count": len(pyc_cache),
        "pyc_or_cache": pyc_cache,
        "reparse_count": len(reparse),
        "reparse": reparse,
        "write_stopped_unique": len(markers) == 1 and markers[0] == marker,
        "write_stopped_strict_latest": marker_strict_latest,
        "postmarker_file_count": len(postmarker),
        "postmarker_files": postmarker,
        "official_pdf_identity": pdf_identity,
        "payload_manifest_sha256": payload_sha,
        "seal_manifest_sha256": seal_sha,
        "write_stopped_sha256": marker_sha,
    }
    audit["external_audit_pass"] = all(
        [
            audit["manifest_fs_identity_pass"],
            audit["all_files_readonly_pass"],
            audit["ads_count"] == 0,
            audit["pyc_or_cache_count"] == 0,
            audit["reparse_count"] == 0,
            audit["write_stopped_unique"],
            audit["write_stopped_strict_latest"],
            audit["postmarker_file_count"] == 0,
            audit["official_pdf_identity"]["pass"],
        ]
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if not audit["external_audit_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
