from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R1_SA2_R168_READONLY_R114_20260828")
MANIFEST = ROOT / "SEAL_MANIFEST.csv"
EXCLUDED = {"SEAL_MANIFEST.csv", "WSTOP"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    files = sorted(
        path
        for path in ROOT.iterdir()
        if path.is_file() and path.name not in EXCLUDED
    )
    nested = [path for path in ROOT.rglob("*") if path.parent != ROOT]
    if nested:
        raise RuntimeError(f"unexpected nested entries: {nested}")
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["RELATIVE_PATH", "BYTES", "SHA256", "MANIFEST_SCOPE"])
        for path in files:
            writer.writerow([path.name, path.stat().st_size, sha256(path), "PRE_WSTOP_ROOT_FILE"])
    print(f"manifested_files={len(files)} manifest={MANIFEST.name}")


if __name__ == "__main__":
    main()
