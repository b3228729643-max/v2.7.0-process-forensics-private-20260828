from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa1_r104_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
EXCLUDED = {"MANIFEST.json", "WRITE_STOPPED"}
WINDOWS_EPOCH_100NS = 116_444_736_000_000_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest().upper()


def iso_utc_100ns(mtime_ns: int) -> str:
    sec, ns = divmod(mtime_ns, 1_000_000_000)
    dt = datetime.fromtimestamp(sec, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{ns // 100:07d}Z"


def classification(rel: str) -> str:
    if rel in {"build_machine_evidence.py", "validate_recordset.py", "seal_recordset.py"}:
        return "control"
    return "payload"


def main() -> None:
    assert ROOT.is_dir()
    assert not MANIFEST.exists() and not MARKER.exists()
    forbidden_cache = [p for p in ROOT.rglob("*") if p.name == "__pycache__" or p.suffix.lower() in {".pyc", ".pyo"}]
    assert not forbidden_cache, forbidden_cache

    paths = sorted(
        (p for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDED),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    entries = []
    for p in paths:
        rel = p.relative_to(ROOT).as_posix()
        stat = p.stat()
        entries.append({
            "relative_path": rel,
            "resolved_path": str(p.resolve()),
            "classification": classification(rel),
            "bytes": stat.st_size,
            "sha256": sha256(p),
            "utc_mtime_exact_100ns": iso_utc_100ns(stat.st_mtime_ns),
            "windows_filetime_100ns": stat.st_mtime_ns // 100 + WINDOWS_EPOCH_100NS,
        })

    canonical = "".join(
        f"{e['relative_path']}\0{e['classification']}\0{e['bytes']}\0{e['sha256']}\0{e['utc_mtime_exact_100ns']}\0{e['windows_filetime_100ns']}\n"
        for e in entries
    ).encode("utf-8")
    recordset_sha = hashlib.sha256(canonical).hexdigest().upper()
    manifest = {
        "manifest_version": "FIGURE_SA1_FRESH_ISOLATED_V1",
        "uid": "FIG-P600-01",
        "handoff_id": "C-FIG-P600-01-R104-SA1-FRESH-ISOLATED-V1",
        "official_pdf_sha256": "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641",
        "result": "SA1_PASS_REQUEST_FRESH_ISOLATED_SA3",
        "hard_failure_ids": [],
        "recordset_sha256": recordset_sha,
        "recordset_canonicalization": "SHA256 over UTF-8 ordered lines: relative_path NUL classification NUL bytes NUL sha256 NUL exact_utc_mtime NUL windows_filetime_100ns LF; excludes manifest self and WRITE_STOPPED marker",
        "classification_policy": {
            "payload": "review evidence, native renders/masks/cards, machine inventories, manual reviewer ledgers, identity/report/result",
            "control": "the three local generation/validation/seal scripts; they never authored manual decisions",
            "seal": "WRITE_STOPPED; excluded because it must be the strictly latest write",
            "self": "MANIFEST.json; excluded so the manifest does not self-list",
        },
        "excluded_paths": [
            {"relative_path": "MANIFEST.json", "classification": "self", "reason": "manifest must not self-list"},
            {"relative_path": "WRITE_STOPPED", "classification": "seal", "reason": "strictly latest marker created only after manifest and readonly transition"},
        ],
        "listed_file_count": len(entries),
        "payload_file_count": sum(e["classification"] == "payload" for e in entries),
        "control_file_count": sum(e["classification"] == "control" for e in entries),
        "entries": entries,
    }
    with MANIFEST.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    manifest_sha = sha256(MANIFEST)

    # Payload, control files and manifest become read-only before the marker.
    for p in paths + [MANIFEST]:
        p.chmod(0o444)

    time.sleep(0.02)
    seal_utc = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    marker_text = (
        "WRITE_STOPPED\n"
        "UID=FIG-P600-01\n"
        "HANDOFF_ID=C-FIG-P600-01-R104-SA1-FRESH-ISOLATED-V1\n"
        f"SEALED_UTC={seal_utc}\n"
        f"LISTED_FILE_COUNT={len(entries)}\n"
        f"RECORDSET_SHA256={recordset_sha}\n"
        f"MANIFEST_SHA256={manifest_sha}\n"
        "POST_MARKER_WRITES_ALLOWED=0\n"
    )
    with MARKER.open("x", encoding="ascii", newline="\n") as f:
        f.write(marker_text)
        f.flush()
        os.fsync(f.fileno())

    print(json.dumps({
        "status": "SEALED",
        "listed_file_count": len(entries),
        "recordset_sha256": recordset_sha,
        "manifest_sha256": manifest_sha,
        "marker": str(MARKER),
    }, indent=2))


if __name__ == "__main__":
    main()
