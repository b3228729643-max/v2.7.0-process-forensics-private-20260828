#!/usr/bin/env python3
"""Verify H2 without creating another hash manifest."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256SUMS.txt"
RECORD = re.compile(r"^([0-9a-f]{64})  (.+)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if not MANIFEST.is_file():
        raise FileNotFoundError(MANIFEST)
    failures: list[str] = []
    records = 0
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        match = RECORD.fullmatch(line)
        if not match:
            continue
        records += 1
        expected, name = match.groups()
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts:
            failures.append(f"unsafe: {name}")
            continue
        path = ROOT.joinpath(*relative.parts)
        if not path.is_file():
            failures.append(f"missing: {name}")
        elif sha256(path) != expected:
            failures.append(f"mismatch: {name}")
    if not records or failures:
        raise RuntimeError(f"H2 verification failed: {failures}")
    print("H2_VERIFY=PASS")
    print(f"H2_ENTRIES={records}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

