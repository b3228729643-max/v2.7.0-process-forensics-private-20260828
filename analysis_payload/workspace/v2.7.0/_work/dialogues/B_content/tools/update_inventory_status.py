from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


inventory_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
m02_evidence_path = Path(sys.argv[3])

m02 = json.loads(m02_evidence_path.read_text(encoding="utf-8"))
if not all(m02["acceptance"].values()):
    raise RuntimeError("M02 current-sync acceptance is not complete")

with inventory_path.open("r", encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle)
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)

priority = {"10.2", "11.1", "12.2", "24.1", "29.1", "33.2"}
for row in rows:
    if row["domain"] == "READING_BLOCKER":
        row["current_state"] = "CURRENT_SOURCE_PASS_B_M02_SYNC_R1"
        row["evidence_ref"] = "B_M02_CURRENT_SYNC.json"
    elif row["domain"] == "EXAMPLE" and row["object_key"] in priority:
        row["current_state"] = "COORDINATOR_EDITED_SA1_PASS"
        row["evidence_ref"] = "B_EXM_P01_SA1_REVIEW.md"

with inventory_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)

summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary["m02_current_sync"] = {
    "evidence": "B_M02_CURRENT_SYNC.json",
    "records": m02["records"],
    "source_files": m02["source_files"],
    "match_mode_counts": m02["match_mode_counts"],
    "acceptance": m02["acceptance"],
}
summary["status_counts"] = dict(Counter(row["current_state"] for row in rows))
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps(summary["status_counts"], ensure_ascii=False, indent=2))
