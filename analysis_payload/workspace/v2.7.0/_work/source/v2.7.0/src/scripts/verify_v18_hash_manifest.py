"""Verify an existing v1.8.0 SHA-256 manifest without modifying it."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = args.manifest.absolute()
    base = args.base.absolute()
    if not manifest.is_file():
        raise FileNotFoundError(manifest)
    if not base.is_dir():
        raise NotADirectoryError(base)

    records: list[tuple[str, str]] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split("  ", 1)
        records.append((expected, relative))

    missing: list[str] = []
    mismatches: list[str] = []
    outside_base: list[str] = []
    for expected, relative in records:
        path = (base / Path(relative)).absolute()
        try:
            path.relative_to(base)
        except ValueError:
            outside_base.append(relative)
            continue
        if not path.is_file():
            missing.append(relative)
        elif digest(path) != expected:
            mismatches.append(relative)

    passed = not missing and not mismatches and not outside_base
    report = {
        "schema_version": 1,
        "verified_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "manifest": manifest.name,
        "records": len(records),
        "missing": missing,
        "hash_mismatches": mismatches,
        "outside_base": outside_base,
        "passed": passed,
    }
    if args.output:
        output = args.output.absolute()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

