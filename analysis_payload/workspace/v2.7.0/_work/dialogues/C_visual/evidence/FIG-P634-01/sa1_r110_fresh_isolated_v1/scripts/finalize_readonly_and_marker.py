from __future__ import annotations

import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P634-01\sa1_r110_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"


def make_read_only(path: Path) -> None:
    os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def main() -> None:
    if not MANIFEST.is_file():
        raise SystemExit("MANIFEST.json must exist before sealing")
    if MARKER.exists():
        raise SystemExit("WRITE_STOPPED already exists; refusing second seal")
    existing = [p for p in ROOT.rglob("*") if p.is_file()]
    latest_ns = max(p.stat().st_mtime_ns for p in existing)
    for p in existing:
        make_read_only(p)
    for p in sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        make_read_only(p)
    make_read_only(ROOT)
    while time.time_ns() <= latest_ns:
        time.sleep(0.01)
    content = (
        "HANDOFF_ID=C-FIG-P634-01-R110-SA1-FRESH-ISOLATED-V1\n"
        "RESULT=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3\n"
        f"SEALED_AT_UTC={datetime.now(timezone.utc).isoformat()}\n"
    )
    with MARKER.open("x", encoding="ascii", newline="\n") as f:
        f.write(content)
    make_read_only(MARKER)
    make_read_only(ROOT)
    print("WRITE_STOPPED created exactly once and last")


if __name__ == "__main__":
    main()
