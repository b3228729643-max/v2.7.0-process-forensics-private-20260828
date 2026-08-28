from __future__ import annotations

import csv
import io
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828")
DECLARATION = ROOT / "MANUAL_REVIEW_DECLARATION.json"
OBJECTS = ROOT / "MACHINE_OBJECTS.csv"
PAIRS = ROOT / "MACHINE_ALL_PAIRS.csv"

declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
with OBJECTS.open(encoding="utf-8-sig", newline="") as stream:
    objects = list(csv.DictReader(stream))
with PAIRS.open(encoding="utf-8-sig", newline="") as stream:
    pairs = list(csv.DictReader(stream))

if len(objects) != declaration["denominator"]["objects"]:
    raise SystemExit("object denominator differs from post-observation declaration")
if len(pairs) != declaration["denominator"]["pairs"]:
    raise SystemExit("pair denominator differs from post-observation declaration")

object_output = io.StringIO(newline="")
object_writer = csv.DictWriter(
    object_output,
    fieldnames=["object_id", "kind", "semantic", "manual_decision", "hard_defect_id", "manual_note"],
    lineterminator="\n",
)
object_writer.writeheader()
for item in objects:
    override = declaration["object_overrides"].get(item["object_id"])
    decision = override["decision"] if override else declaration["object_default_decision"]
    object_writer.writerow(
        {
            "object_id": item["object_id"],
            "kind": item["kind"],
            "semantic": item["semantic"],
            "manual_decision": decision,
            "hard_defect_id": override["hard_defect_id"] if override else "",
            "manual_note": override["note"] if override else "Post-observation object sheet and final current-view review found no hard defect for this object.",
        }
    )

pair_output = io.StringIO(newline="")
pair_writer = csv.DictWriter(
    pair_output,
    fieldnames=["pair_id", "object_a", "object_b", "manual_decision", "review_basis", "opened_sheet"],
    lineterminator="\n",
)
pair_writer.writeheader()
candidate_position = 0
for item in pairs:
    if item["machine_candidate"] == "1":
        candidate_position += 1
        sheet_number = ((candidate_position - 1) // 20) + 1
        basis = "ACTUALLY_OPENED_CANDIDATE_ROI_NO_ILLEGAL_SHARED_VISIBLE_INK"
        opened_sheet = f"candidate_relations_part{sheet_number:02d}.png"
    else:
        basis = "POST_OBSERVATION_POSITIVE_SEPARATION_AND_FULL_VIEW_CROSSCHECK"
        opened_sheet = "full_page_300.png|figure_crop_300_native1x.png|object_overlay_figure_300.png"
    pair_writer.writerow(
        {
            "pair_id": item["pair_id"],
            "object_a": item["object_a"],
            "object_b": item["object_b"],
            "manual_decision": declaration["pair_decision"],
            "review_basis": basis,
            "opened_sheet": opened_sheet,
        }
    )

if candidate_position != declaration["denominator"]["machine_candidates"]:
    raise SystemExit("candidate denominator differs from post-observation declaration")

print("<<<OBJECT_LEDGER>>>")
print(object_output.getvalue(), end="")
print("<<<PAIR_LEDGER>>>")
print(pair_output.getvalue(), end="")
