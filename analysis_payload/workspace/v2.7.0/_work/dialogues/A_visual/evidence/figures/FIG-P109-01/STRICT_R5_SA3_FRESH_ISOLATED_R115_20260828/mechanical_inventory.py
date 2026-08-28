from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R5_SA3_FRESH_ISOLATED_R115_20260828")
OUTPUT = ROOT / "premarker_inventory.csv"


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("premarker inventory already exists")
    items = sorted(
        path for path in ROOT.rglob("*")
        if path != OUTPUT and path.name != "WSTOP.txt"
    )
    with OUTPUT.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["RELATIVE_PATH", "KIND", "BYTES"])
        for path in items:
            relative = path.relative_to(ROOT).as_posix()
            writer.writerow([relative, "directory" if path.is_dir() else "file", "" if path.is_dir() else path.stat().st_size])
    print(f"inventoried_items_excluding_inventory_and_wstop={len(items)}")


if __name__ == "__main__":
    main()
