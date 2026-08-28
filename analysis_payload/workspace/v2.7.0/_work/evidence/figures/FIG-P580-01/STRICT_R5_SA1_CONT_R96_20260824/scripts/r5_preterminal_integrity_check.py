"""Read-only validation of the R5 evidence package, followed by an integrity record.

This is deliberately a narrow R09 check: it re-hashes only the frozen source and
authoritative PDF, then checks the final evidence counts, manual closures, and
native-mask inventory before SA1 writes a terminal decision.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image


R5 = Path(__file__).resolve().parents[1]
WORK = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work")
SOURCE = WORK / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C02" / "fig_v5_c02_is_support.tex"
PDF = WORK / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.pdf"
EXPECTED_SOURCE_SHA256 = "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


records: list[dict[str, object]] = []


def check(gate: str, condition: bool, detail: object) -> None:
    records.append({"gate": gate, "pass": bool(condition), "detail": detail})


source_sha = sha256(SOURCE)
pdf_sha = sha256(PDF)
check("FROZEN_SOURCE_SHA256", source_sha == EXPECTED_SOURCE_SHA256, {"actual": source_sha, "expected": EXPECTED_SOURCE_SHA256})
check("AUTHORITY_PDF_PRESENT", PDF.is_file(), {"pdf": str(PDF), "sha256": pdf_sha})

identity = (R5 / "reports" / "identity_and_scope.md").read_text(encoding="utf-8")
check("FLS_AND_SCOPE_RECORD", all(token in identity for token in ("Physical page / printed page / figure: `628` / `615` / `31.6`", "FLS source locator", EXPECTED_SOURCE_SHA256)), "identity record preserves FLS, page, and source identity")

font_rows = read_csv(R5 / "after_font_audit.csv")
check("FONT_AUDIT_235_ALL_PASS", len(font_rows) == 235 and all(row["FONT_PASS"] == "True" and row["PIXEL_PASS"] == "True" and row["SAME_CLASS_RATIO_PASS"] == "True" and row["ROLE_RATIO_PASS"] == "True" and row["PASS_FAIL"] == "PASS" for row in font_rows), {"rows": len(font_rows)})

glyph_map = read_csv(R5 / "glyph_id_filename_map.csv")
glyph_ids = {row["GLYPH_ID"] for row in glyph_map}
check("GLYPH_ENUMERATION_235_UNIQUE", len(glyph_map) == 235 and len(glyph_ids) == 235, {"map_rows": len(glyph_map), "unique_ids": len(glyph_ids)})

glyph_ledger = read_csv(R5 / "glyph_reviewer_ledger.csv")
glyph_manual_ok = (
    len(glyph_ledger) == 235
    and {row["GLYPH_ID"] for row in glyph_ledger} == glyph_ids
    and all(
        row["ORIGINAL_MATCH"] == "YES"
        and row["OVERLAY_COMPLETE"] == "YES"
        and row["MASK_ONLY_PURE"] == "YES"
        and row["MISSING_STROKE_PX"] == "0"
        and row["FOREIGN_PIXEL_PX"] == "0"
        and row["DECISION"] == "PASS"
        for row in glyph_ledger
    )
)
check("MANUAL_GLYPH_TRI_VIEW_235_OF_235", glyph_manual_ok, {"ledger_rows": len(glyph_ledger)})

contacts = sorted((R5 / "contacts").glob("contact_sheet_*.png"))
check("CONTACT_SHEET_COVERAGE_30", len(contacts) == 30, {"sheets": len(contacts)})

glyph_masks = sorted((R5 / "glyph_masks").glob("*.png"))
vector_masks = sorted((R5 / "vector_masks").glob("*.png"))
nonempty_masks = 0
for mask in glyph_masks + vector_masks:
    with Image.open(mask) as image:
        extrema = image.getextrema()
        if isinstance(extrema[0], tuple):
            nonempty = any(lo != hi for lo, hi in extrema)
        else:
            nonempty = extrema[0] != extrema[1]
        nonempty_masks += int(nonempty)
check("NATIVE_MASKS_235_PLUS_25_NONEMPTY", len(glyph_masks) == 235 and len(vector_masks) == 25 and nonempty_masks == 260, {"glyph_masks": len(glyph_masks), "vector_masks": len(vector_masks), "nonempty": nonempty_masks})

pair_rows = read_csv(R5 / "relationships" / "all_unordered_pairs.csv")
objects = {row["OBJECT_A"] for row in pair_rows} | {row["OBJECT_B"] for row in pair_rows}
class_counts = Counter(row["RELATION_CLASS"] for row in pair_rows)
raw_overlap_rows = [row for row in pair_rows if int(row["RAW_OVERLAP_PX"]) > 0]
pair_ok = (
    len(objects) == 260
    and len(pair_rows) == math.comb(260, 2)
    and class_counts["GG"] == math.comb(25, 2)
    and all(row["STATUS"] == "PASS" for row in pair_rows)
)
check("ALL_UNORDERED_PAIRS_INCLUDING_GG", pair_ok, {"objects": len(objects), "pairs": len(pair_rows), "gg_pairs": class_counts["GG"]})
raw_overlap_ok = (
    len(raw_overlap_rows) == 48
    and all(row["RELATION_CLASS"] == "GG" and row["INTENT_WHITELIST"].strip() and row["SAME_SEMANTIC_PARENT"] == "False" for row in raw_overlap_rows)
)
check("RAW_OVERLAP_CLASSIFICATION_48_NAMED_GG", raw_overlap_ok, {"raw_overlap_rows": len(raw_overlap_rows), "same_parent": sum(row["SAME_SEMANTIC_PARENT"] == "True" for row in raw_overlap_rows), "non_GG": sum(row["RELATION_CLASS"] != "GG" for row in raw_overlap_rows), "unlisted": sum(not row["INTENT_WHITELIST"].strip() for row in raw_overlap_rows)})

critical_ledger = read_csv(R5 / "relationships" / "critical_relationship_reviewer_ledger.csv")
critical_classes = Counter(row["RELATION_CLASS"] for row in critical_ledger)
critical_modes = Counter(row["MANUAL_MODE"] for row in critical_ledger)
critical_ok = (
    len(critical_ledger) == 212
    and critical_classes == Counter({"TT": 152, "TG": 1, "GG": 59})
    and critical_modes == Counter({"COMPONENT_100PCT_TRI_VIEW": 152, "DIRECT_8X_OVERLAY": 60})
    and all(row["MANUAL_RESULT"] == "PASS" for row in critical_ledger)
)
check("MANUAL_CRITICAL_RELATIONS_212_OF_212", critical_ok, {"rows": len(critical_ledger), "classes": dict(critical_classes), "modes": dict(critical_modes)})

same_parent_allocations = read_csv(R5 / "reports" / "same_parent_mask_allocation.csv")
check("SAME_PARENT_ALLOCATION_RECORD", len(same_parent_allocations) == 4, {"allocations": len(same_parent_allocations)})

low_profile = (R5 / "calibration" / "manual_low_profile_review.md").read_text(encoding="utf-8")
four_view = (R5 / "reports" / "manual_four_view_math_coordination_review.md").read_text(encoding="utf-8")
check("LOW_PROFILE_MANUAL_CALIBRATION", "PASS" in low_profile and "8" in low_profile, "G0199 manual calibration record present")
check("FOUR_VIEW_MATH_COORDINATION_MANUAL", all(token in four_view for token in ("MATH_SEMANTICS_PASS = true", "FONT_VISUAL_HARMONY_PASS = true", "GRAYSCALE_PASS = true", "PAGE_INTEGRATION_PASS = true")), "four-view/manual-semantic closure present")

machine = json.loads((R5 / "reports" / "r5_machine_manifest.json").read_text(encoding="utf-8"))
machine_ok = (
    machine["glyph_count"] == 235
    and machine["vector_graphic_count"] == 25
    and machine["pair_stats"]["illegal_overlap_pair_count"] == 0
    and machine["pair_stats"]["illegal_overlap_pixel_count"] == 0
    and machine["pair_stats"]["clearance_failure_pair_count"] == 0
    and machine["pair_stats"]["empty_mask_pair_count"] == 0
    and machine["clip_pixel_count"] == 0
)
check("MACHINE_NATIVE_GATE_SUMMARY", machine_ok, machine["pair_stats"])

check("NO_PREMATURE_WRITE_STOPPED", not (R5 / "WRITE_STOPPED").exists(), "terminal stop marker absent before terminal decision")

all_pass = all(record["pass"] for record in records)
result = {
    "figure_id": "FIG-P580-01",
    "stage": "PRETERMINAL_INTEGRITY_CHECK",
    "all_pass": all_pass,
    "source_sha256": source_sha,
    "pdf_sha256": pdf_sha,
    "records": records,
}
(R5 / "reports" / "preterminal_integrity_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = ["# R5 preterminal integrity check", "", f"**RESULT = {'PASS' if all_pass else 'FAIL'}**", "", "| Gate | Result | Detail |", "|---|---|---|"]
for record in records:
    verdict = "PASS" if record["pass"] else "FAIL"
    detail = json.dumps(record["detail"], ensure_ascii=False, sort_keys=True).replace("|", "\\|")
    lines.append(f"| {record['gate']} | {verdict} | {detail} |")
lines.extend(["", "This record is non-terminal. A terminal SA1 decision may be written only when RESULT is PASS.", ""])
(R5 / "reports" / "preterminal_integrity_check.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"all_pass": all_pass, "failed_gates": [record["gate"] for record in records if not record["pass"]]}, ensure_ascii=False))
