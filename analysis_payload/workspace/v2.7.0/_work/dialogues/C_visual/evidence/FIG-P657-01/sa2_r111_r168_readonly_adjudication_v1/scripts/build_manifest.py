from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.json"
WSTOP = ROOT / "WRITE_STOPPED"
CONTROL_EXCLUSIONS = {MANIFEST.name, WSTOP.name}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    if MANIFEST.exists() or WSTOP.exists():
        raise SystemExit("refusing to replace an existing manifest or seal marker")

    files = []
    directories = []
    for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            raise SystemExit(f"reparse/symlink not permitted: {relative}")
        if path.is_dir():
            directories.append(relative)
        elif path.is_file() and relative not in CONTROL_EXCLUSIONS:
            files.append(
                {
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )

    payload = {
        "schema": "sealed-evidence-manifest-v1",
        "handoff_id": "C-FIG-P657-01-R111-SA2-R168-READONLY-ADJUDICATION-V1",
        "root": str(ROOT),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inventory_policy": "All ordinary preseal files and directories under root. MANIFEST.json and WRITE_STOPPED are the only control exclusions; final exact equality is manifest paths plus those two control files equals filesystem paths.",
        "control_file_exclusions": ["MANIFEST.json", "WRITE_STOPPED"],
        "file_count": len(files),
        "directory_count": len(directories),
        "directories": directories,
        "files": files,
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    temporary = ROOT / ".MANIFEST.json.tmp"
    temporary.write_bytes(encoded)
    temporary.replace(MANIFEST)
    print(f"manifest_files={len(files)} manifest_directories={len(directories)}")


if __name__ == "__main__":
    main()
