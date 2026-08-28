from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFESTS = ROOT / "manifests"
PAYLOAD_MANIFEST = MANIFESTS / "PAYLOAD_MANIFEST.csv"
FILESYSTEM_MANIFEST = MANIFESTS / "FILESYSTEM_MANIFEST.csv"
WSTOP = ROOT / "WRITE_STOPPED"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def files_excluding(excluded: set[str]) -> list[Path]:
    return sorted(
        (p for p in ROOT.rglob("*") if p.is_file() and rel(p) not in excluded),
        key=lambda p: rel(p).casefold(),
    )


def write_manifest(path: Path, domain: str, paths: list[Path]) -> None:
    with path.open("x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "relative_path", "bytes", "sha256"])
        w.writeheader()
        for p in paths:
            w.writerow({"domain": domain, "relative_path": rel(p), "bytes": p.stat().st_size, "sha256": sha256(p)})


def read_manifest(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def readonly(path: Path) -> bool:
    attrs = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attrs & stat.FILE_ATTRIBUTE_READONLY)


def set_readonly(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def validate_manifest(path: Path, actual: list[Path]) -> None:
    rows = read_manifest(path)
    expected = {rel(p): p for p in actual}
    if len(rows) != len(expected) or {r["relative_path"] for r in rows} != set(expected):
        raise RuntimeError(f"manifest path closure failed: {path.name}")
    for r in rows:
        p = expected[r["relative_path"]]
        if int(r["bytes"]) != p.stat().st_size or r["sha256"] != sha256(p):
            raise RuntimeError(f"manifest bytes/hash closure failed: {path.name}:{r['relative_path']}")


def main() -> None:
    if WSTOP.exists() or list(ROOT.rglob("WRITE_STOPPED")):
        raise RuntimeError("WRITE_STOPPED already exists; refusing second seal")
    if PAYLOAD_MANIFEST.exists() or FILESYSTEM_MANIFEST.exists():
        raise RuntimeError("manifest already exists; refusing reseal")
    cross = json.loads((ROOT / "controls/final_crosscheck.json").read_text(encoding="utf-8-sig"))
    result = json.loads((ROOT / "SA3_RESULT.json").read_text(encoding="utf-8-sig"))
    if cross["automated_crosscheck_gate"] != "PASS" or cross["failed_checks"] or result["decision"] != "A_LOCAL_PASS":
        raise RuntimeError("final controls are not ready for seal")
    if any(p.is_symlink() for p in ROOT.rglob("*")):
        raise RuntimeError("symlink/reparse candidate present")
    if any("__pycache__" in p.parts or p.suffix.lower() in {".pyc", ".pyo"} for p in ROOT.rglob("*")):
        raise RuntimeError("cache/bytecode present")

    MANIFESTS.mkdir(exist_ok=False)
    excluded_payload = {"manifests/PAYLOAD_MANIFEST.csv", "manifests/FILESYSTEM_MANIFEST.csv", "WRITE_STOPPED"}
    payload = files_excluding(excluded_payload)
    write_manifest(PAYLOAD_MANIFEST, "PAYLOAD_EXCLUDES_BOTH_MANIFESTS_AND_WRITE_STOPPED", payload)
    for p in payload:
        set_readonly(p)
    set_readonly(PAYLOAD_MANIFEST)

    excluded_fs = {"manifests/FILESYSTEM_MANIFEST.csv", "WRITE_STOPPED"}
    filesystem_domain = files_excluding(excluded_fs)
    write_manifest(FILESYSTEM_MANIFEST, "FILESYSTEM_EXCLUDES_SELF_AND_WRITE_STOPPED", filesystem_domain)
    set_readonly(FILESYSTEM_MANIFEST)

    validate_manifest(PAYLOAD_MANIFEST, files_excluding(excluded_payload))
    validate_manifest(FILESYSTEM_MANIFEST, files_excluding(excluded_fs))
    pre_wstop = files_excluding({"WRITE_STOPPED"})
    if not all(readonly(p) for p in pre_wstop):
        raise RuntimeError("not every payload/manifest file is read-only")

    max_prior_mtime_ns = max(p.stat().st_mtime_ns for p in pre_wstop)
    target_ns = max_prior_mtime_ns + 2_000_000_000
    while time.time_ns() <= target_ns:
        time.sleep(0.05)
    stopped_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    content = (
        "HANDOFF_ID=A-R108-P580-SA3-FRESH-ISOLATED-20260826\n"
        "UID=FIG-P580-01\n"
        "ROUND=R108\n"
        "ROLE=SA3_FRESH_ISOLATED_R108\n"
        f"WRITE_STOPPED_UTC={stopped_utc}\n"
        "ROOT_WRITES_AFTER_THIS_FILE=0\n"
    )
    with WSTOP.open("x", encoding="utf-8", newline="\n") as f:
        f.write(content)
    set_readonly(WSTOP)

    all_files = files_excluding(set())
    other = [p for p in all_files if p != WSTOP]
    if len([p for p in all_files if p.name == "WRITE_STOPPED"]) != 1:
        raise RuntimeError("WRITE_STOPPED is not unique")
    if not readonly(WSTOP) or not all(readonly(p) for p in other):
        raise RuntimeError("post-seal read-only check failed")
    wstop_mtime_ns = WSTOP.stat().st_mtime_ns
    if not all(wstop_mtime_ns > p.stat().st_mtime_ns for p in other):
        raise RuntimeError("WRITE_STOPPED is not strictly latest")
    if any(p.stat().st_mtime_ns >= wstop_mtime_ns for p in other):
        raise RuntimeError("files-at-or-after WRITE_STOPPED is nonzero")
    print(json.dumps({
        "seal": "PASS",
        "payload_manifest_rows": len(read_manifest(PAYLOAD_MANIFEST)),
        "filesystem_manifest_rows": len(read_manifest(FILESYSTEM_MANIFEST)),
        "root_file_count_including_manifests_and_wstop": len(all_files),
        "write_stopped_utc": stopped_utc,
        "write_stopped_mtime_ns": wstop_mtime_ns,
        "max_other_mtime_ns": max(p.stat().st_mtime_ns for p in other),
        "files_at_or_after_wstop": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
