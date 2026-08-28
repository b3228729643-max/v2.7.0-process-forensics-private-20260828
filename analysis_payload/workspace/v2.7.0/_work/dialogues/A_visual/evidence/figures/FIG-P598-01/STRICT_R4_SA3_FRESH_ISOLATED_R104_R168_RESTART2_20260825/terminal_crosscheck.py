from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
MACHINE = ROOT / "machine"
REVIEW = ROOT / "review"
OUT = MACHINE / "terminal_crosscheck.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


objects = json.loads((MACHINE / "object_ledger_machine.json").read_text(encoding="utf-8"))
pairs = json.loads((MACHINE / "all_unordered_pairs_machine.json").read_text(encoding="utf-8"))
summary = json.loads((MACHINE / "machine_summary.json").read_text(encoding="utf-8"))

object_ids = [row["object_id"] for row in objects]
pair_ids = [row["pair_id"] for row in pairs]
safe_names = [row["safe_filename"] for row in objects]

require(len(objects) == 168, "object JSON denominator is not 168")
require(len(set(object_ids)) == 168, "object IDs are not unique")
require(sum(x.startswith("T") for x in object_ids) == 142, "text denominator is not 142")
require(sum(x.startswith("G") for x in object_ids) == 26, "graphic denominator is not 26")
require(len(pairs) == 14028, "pair JSON denominator is not 14028")
require(len(set(pair_ids)) == 14028, "pair IDs are not unique")
require(len(set(safe_names)) == 168, "safe filenames are not unique")

with (MACHINE / "object_ledger_machine.csv").open(encoding="utf-8-sig", newline="") as fh:
    object_csv = list(csv.DictReader(fh))
with (MACHINE / "all_unordered_pairs_machine.csv").open(encoding="utf-8-sig", newline="") as fh:
    pair_csv = list(csv.DictReader(fh))
require(len(object_csv) == 168, "object CSV denominator is not 168")
require(len(pair_csv) == 14028, "pair CSV denominator is not 14028")

mask_dir = MACHINE / "object_masks"
mask_paths = [mask_dir / name for name in safe_names]
require(all(path.is_file() for path in mask_paths), "one or more safe-name masks are absent")
require(all(":" not in path.name for path in mask_paths), "unsafe colon in mask filename")
for path in mask_paths:
    with Image.open(path) as im:
        im.verify()

contact_dir = MACHINE / "contact_sheets"
glyph_sheets = sorted(contact_dir.glob("glyph_contacts_*.png"))
graphic_sheets = sorted(contact_dir.glob("graphic_contacts_*.png"))
matrix_paths = sorted((MACHINE / "matrices").glob("*.png"))
relationship_paths = sorted((MACHINE / "relationship_sheets").glob("critical_relationships_*.png"))
require(len(glyph_sheets) == 24, "glyph contact-sheet count is not 24")
require(len(graphic_sheets) == 5, "graphic contact-sheet count is not 5")
require(len(matrix_paths) == 2, "matrix count is not 2")
require(len(relationship_paths) == 4, "relationship sheet count is not 4")
for path in glyph_sheets + graphic_sheets + matrix_paths + relationship_paths:
    with Image.open(path) as im:
        im.verify()

object_manual = (REVIEW / "manual_object_adjudication.md").read_text(encoding="utf-8")
manual_object_rows = re.findall(
    r"^\| ((?:T|G)\d{3}) \|[^\n]*\| yes \| yes \| yes \| 0 \| 0 \| PASS \|",
    object_manual,
    flags=re.MULTILINE,
)
require(len(manual_object_rows) == 168, "manual object PASS row count is not 168")
require(set(manual_object_rows) == set(object_ids), "manual object IDs do not equal machine IDs")
require("Totals: `168/168 PASS`" in object_manual, "manual object terminal total absent")

pair_manual = (REVIEW / "manual_pair_adjudication.md").read_text(encoding="utf-8")
manual_pair_rows = re.findall(r"^\| (P\d{5}) \|[^\n]*\| no \| PASS \|$", pair_manual, flags=re.MULTILINE)
require(len(manual_pair_rows) == 19, "manual critical-pair PASS row count is not 19")
require(set(manual_pair_rows).issubset(set(pair_ids)), "manual pair ID absent from machine pair ledger")
require("`14,028/14,028` unordered pairs accounted for" in pair_manual, "manual pair terminal total absent")
require("`OVERLAP_PIXEL_COUNT=0`" in pair_manual, "manual illegal-overlap terminal absent")
require("`CLIP_PIXEL_COUNT=0`" in pair_manual, "manual clip terminal absent")

visual_manual = (REVIEW / "manual_visual_semantic_adjudication.md").read_text(encoding="utf-8")
require("`FONT_VISUAL_HARMONY_PASS=true`" in visual_manual, "manual font harmony result absent")
require("`SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`" in visual_manual, "manual terminal verdict absent")

require(summary["empty_mask_count"] == 0, "machine summary reports an empty mask")
require(summary["manual_fields_present"] is False, "machine output contains manual fields")
require(summary["machine_generator_never_writes_manual_review"] is True, "manual-write guard absent")
require(summary["clip_pixel_count_crop_boundary"] == 0, "machine summary reports clipping")
require(summary["raw_geometric_overlap_pair_count"] == 17, "raw overlap count is not 17")
require(summary["critical_relationship_count"] == 19, "critical relationship count is not 19")

result = {
    "figure_uid": "FIG-P598-01",
    "handoff_id": "A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825",
    "terminal_crosscheck_pass": True,
    "objects_json_csv_manual": "168/168/168",
    "text_graphic_counts": "142/26",
    "unique_object_ids": 168,
    "safe_openable_object_masks": 168,
    "unordered_pairs_json_csv": "14028/14028",
    "unique_pair_ids": 14028,
    "manual_critical_relationships": "19/19 PASS",
    "glyph_contact_sheets": 24,
    "graphic_contact_sheets": 5,
    "pair_matrices": 2,
    "critical_relationship_sheets": 4,
    "empty_masks": 0,
    "final_illegal_overlap_count": 0,
    "clip_pixel_count": 0,
    "manual_fields_in_machine_outputs": False,
    "decision": "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE",
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
