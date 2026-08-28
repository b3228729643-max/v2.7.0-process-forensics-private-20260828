from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path

from render_evidence import OBJECTS


root = Path(__file__).resolve().parent
ids = [row[0] for row in OBJECTS]
with (root / "pair_index_no_verdict.csv").open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B"])
    for a, b in combinations(ids, 2):
        writer.writerow([f"{a}__{b}", a, b])

print(f"objects={len(ids)}")
print(f"pairs={len(ids) * (len(ids) - 1) // 2}")
