from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


inventory_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
status = sys.argv[3]
evidence_ref = sys.argv[4]
task_ids = set(sys.argv[5:])

with inventory_path.open("r", encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle)
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)

matched: set[str] = set()
for row in rows:
    if row["task_id"] in task_ids:
        row["current_state"] = status
        row["evidence_ref"] = evidence_ref
        matched.add(row["task_id"])

missing = task_ids - matched
if missing:
    raise RuntimeError(f"task IDs not found: {sorted(missing)}")

with inventory_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)

summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary["status_counts"] = dict(Counter(row["current_state"] for row in rows))
summary_path.write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({"matched": sorted(matched), "status_counts": summary["status_counts"]}, ensure_ascii=False, indent=2))
