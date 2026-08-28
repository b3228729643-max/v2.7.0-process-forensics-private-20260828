import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01"
    r"\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828"
)
EVIDENCE = ROOT / "evidence"
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src"
    r"\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex"
)
CHAPTER = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src"
    r"\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C08.tex"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


machine = json.loads((EVIDENCE / "MACHINE_RESULT.json").read_text(encoding="utf-8"))
machine_objects = read_csv("LOGICAL_OBJECTS.csv")
machine_pairs = read_csv("ALL_UNORDERED_PAIRS_MACHINE.csv")
raw_atoms = read_csv("RAW_ATOMS.csv")
manual_objects = read_csv("MANUAL_OBJECT_LEDGER.csv")
manual_pairs = read_csv("MANUAL_PAIR_LEDGER.csv")
manual_views = read_csv("MANUAL_VIEW_LEDGER.csv")
manual_math = read_csv("MANUAL_MATH_SEMANTIC_LEDGER.csv")
manual_glyphs = read_csv("MANUAL_GLYPH_CODEPOINT_LEDGER.csv")

errors: list[str] = []


def require(condition: bool, label: str) -> None:
    if not condition:
        errors.append(label)


object_ids = [row["object_id"] for row in machine_objects]
manual_object_ids = [row["object_id"] for row in manual_objects]
require(len(object_ids) == 14 and len(set(object_ids)) == 14, "machine object denominator is not 14 unique IDs")
require(manual_object_ids == object_ids, "manual object IDs/order do not exactly match machine objects")

pair_ids = [row["pair_id"] for row in machine_pairs]
manual_pair_ids = [row["pair_id"] for row in manual_pairs]
require(len(pair_ids) == 91 and len(set(pair_ids)) == 91, "machine pair denominator is not 91 unique IDs")
require(manual_pair_ids == pair_ids, "manual pair IDs/order do not exactly match all machine pairs")
for machine_row, manual_row in zip(machine_pairs, manual_pairs, strict=True):
    require(machine_row["object_a"] == manual_row["object_a"], f"pair {machine_row['pair_id']} object_a mismatch")
    require(machine_row["object_b"] == manual_row["object_b"], f"pair {machine_row['pair_id']} object_b mismatch")

char_ids = [row["atom_id"] for row in raw_atoms if row["atom_type"] == "char"]
manual_glyph_ids = [row["atom_id"] for row in manual_glyphs]
require(len(char_ids) == 25 and len(set(char_ids)) == 25, "raw character denominator is not 25")
require(manual_glyph_ids == char_ids, "manual glyph IDs/order do not exactly match raw characters")

for ledger_name, rows in (
    ("objects", manual_objects),
    ("pairs", manual_pairs),
    ("views", manual_views),
    ("math", manual_math),
    ("glyphs", manual_glyphs),
):
    require(all(row.get("reviewer", "").strip() for row in rows), f"{ledger_name} has blank reviewer")
    require(all(row.get("opened_at_utc", "").strip() for row in rows), f"{ledger_name} has blank opened_at_utc")
    require(
        all(
            row.get("opened_evidence", row.get("evidence_or_input", row.get("evidence_path", ""))).strip()
            for row in rows
        ),
        f"{ledger_name} has blank opened evidence",
    )
    require(all(row.get("decision", "") in {"PASS", "FAIL"} for row in rows), f"{ledger_name} has invalid decision")
    require(all(row.get("note", "").strip() for row in rows), f"{ledger_name} has blank note")

for row in manual_views:
    for item in row["evidence_path"].split("|"):
        require((EVIDENCE / item).is_file(), f"opened view is missing: {item}")

require(PDF.stat().st_size == 33952, "PDF byte count changed")
require(sha256(PDF) == "19F221487DB1930170608EAE0E09F019313791D808C724D05DBAC23465F746B2", "PDF SHA changed")
require(SOURCE.stat().st_size == 4224, "source byte count changed")
require(sha256(SOURCE) == "366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20", "source SHA changed")
require(CHAPTER.stat().st_size == 59218, "chapter byte count changed")
require(sha256(CHAPTER) == "3C60FABCACA8BFC390323033F3CF6539CA5497EBF5A09641B8C4B78E81A0816C", "chapter SHA changed")

manual_failure_rows = []
for ledger_name, rows in (
    ("objects", manual_objects),
    ("pairs", manual_pairs),
    ("views", manual_views),
    ("math", manual_math),
    ("glyphs", manual_glyphs),
):
    for row in rows:
        if row["decision"] == "FAIL" or row["hard_defect"].lower() == "true":
            manual_failure_rows.append({"ledger": ledger_name, "row": row})

require(len(manual_objects) == 14, "manual object count mismatch")
require(len(manual_pairs) == 91, "manual pair count mismatch")
require(len(manual_views) == 17, "manual view count mismatch")
require(len(manual_math) == 10, "manual math-semantic count mismatch")
require(len(manual_glyphs) == 25, "manual glyph count mismatch")

crosscheck = {
    "handoff_id": "A-R115-P126-SA2-DIRECT-BUILD-R3A-20260828",
    "stage": "POST_BUILD_NON_TEX_FINAL_CROSSCHECK",
    "manual_fields_generated_by_script": 0,
    "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
    "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
    "chapter": {"path": str(CHAPTER), "bytes": CHAPTER.stat().st_size, "sha256": sha256(CHAPTER)},
    "machine": {
        "N": len(machine_objects),
        "C": len(machine_pairs),
        "formula_C": len(machine_objects) * (len(machine_objects) - 1) // 2,
        "candidate_pairs": sum(row["machine_candidate"].lower() == "true" for row in machine_pairs),
        "raw_visible_atoms": len(raw_atoms),
        "raw_chars": len(char_ids),
        "unassigned_atoms": machine.get("denominator", {}).get("unassigned_atoms", 0),
        "duplicate_assigned_atoms": machine.get("denominator", {}).get("duplicate_assigned_atoms", 0),
    },
    "manual": {
        "objects": len(manual_objects),
        "pairs": len(manual_pairs),
        "views": len(manual_views),
        "math_semantic": len(manual_math),
        "glyph_codepoint": len(manual_glyphs),
        "failure_rows": manual_failure_rows,
        "unique_hard_defects": 1,
    },
    "unique_hard_defect": {
        "id": "HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE",
        "objects": ["O13", "O14"],
        "pair": "P0091",
        "fact": "The x2 legend swatch renders as one continuous horizontal run rather than the requested multi-dash sample; both legend swatches appear solid in grayscale native1x and nearest8x evidence.",
        "r168_classification": "HARD_SEMANTIC_ROLE_FAILURE_NOT_FONT_PIXEL_ADVISORY",
    },
    "errors": errors,
    "hard_gate": len(errors) == 0,
}

(EVIDENCE / "FINAL_CROSSCHECK.json").write_text(
    json.dumps(crosscheck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

result = {
    "handoff_id": crosscheck["handoff_id"],
    "result": "LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE",
    "sealed_result_direction": "FAIL",
    "N": 14,
    "C": 91,
    "machine_candidate_pairs": 33,
    "manual_objects": 14,
    "manual_pairs": 91,
    "manual_views": 17,
    "manual_math_semantic": 10,
    "manual_glyph_codepoint": 25,
    "hard_defect_count_unique": 1,
    "hard_defect_id": "HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE",
    "crosscheck_errors": len(errors),
    "crosscheck_hard_gate": len(errors) == 0,
    "no_commit": True,
    "no_additional_tex": True,
    "manual_fields_generated_by_script": 0,
}
(EVIDENCE / "RESULT.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

print(json.dumps(result, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
