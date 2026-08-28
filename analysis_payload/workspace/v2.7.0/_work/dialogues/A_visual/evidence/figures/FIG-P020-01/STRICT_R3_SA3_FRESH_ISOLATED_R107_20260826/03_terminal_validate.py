from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image


sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R3_SA3_FRESH_ISOLATED_R107_20260826")


def read_csv(name: str) -> list[dict]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


machine = json.loads((ROOT / "machine_crosscheck.json").read_text(encoding="utf-8"))
closure = json.loads((ROOT / "glyph_denominator_closure.json").read_text(encoding="utf-8"))
identity = json.loads((ROOT / "input_identity.json").read_text(encoding="utf-8"))
objects = read_csv("object_manifest.csv")
glyphs = read_csv("after_pixel_measurements.csv")
graphics = read_csv("graphic_object_ledger.csv")
pairs = read_csv("after_overlap_report.csv")
critical = read_csv("critical_relation_index.csv")
manual_glyphs = read_csv("manual_glyph_review.csv")
manual_graphics = read_csv("manual_graphic_review.csv")
manual_relations = read_csv("manual_critical_relation_review.csv")
manual_views = read_csv("manual_view_role_review.csv")
acceptance = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
result = (ROOT / "RESULT.txt").read_text(encoding="utf-8")

checks: dict[str, bool] = {}
checks["identity_fork_none"] = identity["fork_turns"] == "none" and identity["parent_history_inherited"] is False
checks["input_pdf_identity_still_matches"] = sha256(Path(identity["official_pdf"]["path"])) == identity["official_pdf"]["sha256"]
checks["input_source_identity_still_matches"] = sha256(Path(identity["current_source"]["path"])) == identity["current_source"]["sha256"]
checks["body_caption_closure"] = closure["figure_body_glyph_count"] == 65 and closure["caption_glyph_count"] == 43 and closure["caption_included_in_N"] is True
checks["object_denominator"] = len(objects) == 122 == machine["N"] == closure["N"] and len({row["OBJECT_ID"] for row in objects}) == 122
checks["glyph_denominator"] = len(glyphs) == 108 == machine["glyph_object_count"] and len({row["ELEMENT_ID"] for row in glyphs}) == 108
checks["graphic_denominator"] = len(graphics) == 14 == machine["foreground_graphic_object_count"] and len({row["OBJECT_ID"] for row in graphics}) == 14
checks["drawing_path_coverage"] = len(read_csv("drawing_path_ledger.csv")) == 16 == machine["visible_pdf_drawing_path_count"]
checks["pair_denominator"] = len(pairs) == 7381 == machine["actual_unordered_pairs"] == closure["C_N_2"] and len({row["RELATION_ID"] for row in pairs}) == 7381
checks["all_machine_rows_pass"] = not any(row["MACHINE_GATE_STATUS"].startswith("FAIL") for row in glyphs) and not any(row["MACHINE_STATUS"].startswith("FAIL") for row in graphics + pairs)
checks["machine_hard_gates_zero"] = all(
    machine[key] == 0
    for key in [
        "empty_mask_count",
        "tofu_or_replacement_count",
        "hard_pixel_height_failure_count",
        "illegal_overlap_pair_count",
        "canonical_illegal_overlap_pixel_count",
        "clearance_failure_count",
        "clip_pixel_count",
    ]
)
checks["machine_status_pass"] = machine["machine_status"] == "PASS"

checks["manual_glyph_rows"] = (
    len(manual_glyphs) == 108
    and {row["ELEMENT_ID"] for row in manual_glyphs} == {row["ELEMENT_ID"] for row in glyphs}
    and all(row["MANUAL_DECISION"] == "PASS" and row["ORIGINAL_MATCH"] == "true" and row["OVERLAY_COMPLETE"] == "true" and row["MASK_ONLY_PURE"] == "true" for row in manual_glyphs)
    and len({row["NOTE"] for row in manual_glyphs}) == 108
)
checks["manual_graphic_rows"] = (
    len(manual_graphics) == 14
    and {row["OBJECT_ID"] for row in manual_graphics} == {row["OBJECT_ID"] for row in graphics}
    and all(row["MANUAL_DECISION"] == "PASS" and row["ORIGINAL_MATCH"] == "true" and row["OVERLAY_COMPLETE"] == "true" and row["MASK_ONLY_PURE"] == "true" for row in manual_graphics)
    and len({row["NOTE"] for row in manual_graphics}) == 14
)
checks["manual_critical_relation_rows"] = (
    len(manual_relations) == len(critical) == 22
    and {row["RELATION_ID"] for row in manual_relations} == {row["RELATION_ID"] for row in critical}
    and all(row["MANUAL_DECISION"] == "PASS" and row["ONE_X_OPENED"] == "true" and row["EIGHT_X_OPENED"] == "true" and row["INTERSECTION_CORRECT"] == "true" for row in manual_relations)
    and len({row["NOTE"] for row in manual_relations}) == 22
)
checks["manual_view_role_rows"] = len(manual_views) == 11 and all(row["MANUAL_DECISION"] == "PASS" and row["NOTE"] for row in manual_views)

required_acceptance_tokens = [
    "SA3_FINAL_VERDICT: `PASS`",
    "REQUIRED_OUTCOME: `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`",
    "OVERLAP_PIXEL_COUNT: `0`",
    "CLIP_PIXEL_COUNT: `0`",
    "FONT_VISUAL_HARMONY_PASS: `true`",
    "MATH_SEMANTICS_PASS: `true`",
    "TEXT_CONSISTENCY_PASS: `true`",
    "GRAYSCALE_PASS: `true`",
    "PAGE_INTEGRATION_PASS: `true`",
]
checks["acceptance_tokens"] = all(token in acceptance for token in required_acceptance_tokens)
checks["result_consistency"] = all(token in result for token in ["N=122", "C_N_2=7381", "FINAL_VERDICT=PASS", "OUTCOME=SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE", "A_LOCAL_PASS_WRITTEN=false"])

referenced_pngs = set()
for row in glyphs:
    referenced_pngs.update([row["ORIGINAL_1X"], row["TARGET_OVERLAY_1X"], row["MASK_ONLY_1X"], row["TRIPTYCH_8X"]])
for row in graphics:
    referenced_pngs.update([row["ORIGINAL_1X"], row["TARGET_OVERLAY_1X"], row["MASK_ONLY_1X"]])
for row in critical:
    referenced_pngs.update([row["ONE_X"], row["EIGHT_X"]])

all_pngs = list(ROOT.rglob("*.png"))
png_failures = []
for path in all_pngs:
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:  # pragma: no cover - evidence failure path
        png_failures.append({"path": str(path), "error": repr(exc)})
checks["all_pngs_open"] = not png_failures
checks["all_referenced_pngs_exist"] = all((ROOT / rel).is_file() for rel in referenced_pngs)
checks["contact_sheet_counts"] = len(list((ROOT / "contact_sheets").glob("glyph_contact_*_8x_nearest.png"))) == 11 and len(list((ROOT / "contact_sheets").glob("graphic_contact_*.png"))) == 2
checks["critical_image_counts"] = len(list((ROOT / "critical_relations").glob("*_1x.png"))) == 22 and len(list((ROOT / "critical_relations").glob("*_8x_nearest.png"))) == 22
checks["safe_filenames"] = all(":" not in path.name for path in ROOT.rglob("*"))
checks["no_manual_fields_in_machine_csv"] = all(
    forbidden not in {key.upper() for key in rows[0].keys()}
    for rows in [glyphs, graphics, pairs]
    for forbidden in ["REVIEWER", "MANUAL_DECISION", "NOTE"]
)

status = "PASS" if all(checks.values()) else "FAIL"
payload = {
    "status": status,
    "checks": checks,
    "counts": {
        "objects": len(objects),
        "glyphs": len(glyphs),
        "graphics": len(graphics),
        "pairs": len(pairs),
        "critical_relations": len(critical),
        "manual_glyph_rows": len(manual_glyphs),
        "manual_graphic_rows": len(manual_graphics),
        "manual_relation_rows": len(manual_relations),
        "manual_view_role_rows": len(manual_views),
        "png_files_opened_by_machine": len(all_pngs),
        "referenced_pngs": len(referenced_pngs),
    },
    "png_failures": png_failures,
    "result_outcome": "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE" if status == "PASS" else "FAIL_TO_SA2",
}
(ROOT / "terminal_crosscheck.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2))
if status != "PASS":
    raise SystemExit(1)
