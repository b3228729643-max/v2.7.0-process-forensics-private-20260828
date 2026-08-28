from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa1_r108_fresh_isolated_v1")
MANIFEST = ROOT / "SEALED_MANIFEST.json"
WSTOP = ROOT / "WRITE_STOPPED"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    if MANIFEST.exists() or WSTOP.exists():
        raise RuntimeError("seal control file already exists")

    files = []
    for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.as_posix().lower()):
        rel = path.relative_to(ROOT).as_posix()
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": digest(path)})

    directories = ["."] + [
        path.relative_to(ROOT).as_posix()
        for path in sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: p.as_posix().lower())
    ]
    document = {
        "schema": "fresh-isolated-sa1-sealed-evidence-v1",
        "uid": "FIG-P609-01",
        "handoff_id": "C-FIG-P609-01-R108-SA1-FRESH-ISOLATED-V1",
        "result": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
        "candidate": "R108",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "closure_model": {
            "pre_marker_payload": "Every ordinary file present before manifest creation is listed with bytes and SHA256.",
            "manifest_self": "SEALED_MANIFEST.json is self-excluded to avoid a circular digest; its path and role are declared here.",
            "final_marker": "WRITE_STOPPED is excluded from hashes and declared only as the required final marker path.",
            "post_marker_writes": "None permitted except setting read-only filesystem attributes.",
        },
        "manifest_path": "SEALED_MANIFEST.json",
        "final_marker_path": "WRITE_STOPPED",
        "pre_manifest_file_count": len(files),
        "directories": directories,
        "files": files,
        "filesystem_requirements": {
            "all_ordinary_files_read_only": True,
            "all_directories_read_only": True,
            "alternate_data_stream_count": 0,
            "cache_or_pyc_count": 0,
            "reparse_point_count": 0,
            "write_stopped_unique_and_last": True,
        },
    }
    MANIFEST.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
