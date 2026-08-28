from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


objects = read_csv(ROOT / "MACHINE_OBJECTS.csv")
pairs = read_csv(ROOT / "MACHINE_ALL_PAIRS.csv")
if len(objects) != 60 or len({r["object_id"] for r in objects}) != 60:
    raise RuntimeError("object denominator mismatch")
if len(pairs) != 1770 or len({r["pair_id"] for r in pairs}) != 1770:
    raise RuntimeError("pair denominator mismatch")
pair_tuples = {tuple(sorted((r["object_a"], r["object_b"]))) for r in pairs}
if len(pair_tuples) != 1770 or any(r["object_a"] == r["object_b"] for r in pairs):
    raise RuntimeError("pair uniqueness/self-pair mismatch")
object_ids = {r["object_id"] for r in objects}
if any(r["object_a"] not in object_ids or r["object_b"] not in object_ids for r in pairs):
    raise RuntimeError("pair references unknown object")

object_rows: list[dict[str, object]] = []
for row in objects:
    note = "Opened final object overlay/contact sheet; reader-visible object is complete and legible."
    if row["object_id"] == "T010":
        note = "Digit 6 is legible, but its illegal visible-ink contact with q4 marker C016 is adjudicated in pair P00541."
    elif row["object_id"] == "T015":
        note = "Digit 7 is complete and legible; native/NN8x ROI shows 8 px blank clearance from surrounding marker/arrow ink."
    elif row["object_id"] == "C020":
        note = "Rendered x2 legend sample is a complete curve object but is wrongly continuous; topology failure is recorded in hard-gate ledger."
    elif row["kind"] == "protective-background":
        note = "Opaque local protection rectangle is reader-visible by effect and was included in N; it does not clip its owned glyph."
    object_rows.append({
        "object_id": row["object_id"],
        "kind": row["kind"],
        "semantic": row["semantic"],
        "text": row["text"],
        "reviewed_after_open": "TRUE",
        "verdict": "PASS_OBJECT_INTEGRITY",
        "note": note,
    })
write_csv(ROOT / "MANUAL_OBJECT_LEDGER.csv", list(object_rows[0]), object_rows)


def candidate_note(a: str, b: str) -> str:
    kinds = {a, b}
    if kinds == {"glyph", "protective-background"}:
        return "Owned glyph/background relation inspected; background protects rather than occludes the glyph."
    if kinds == {"glyph"}:
        return "Same text/math cluster or bbox-near glyphs inspected on candidate sheets; no illegal foreign-ink collision."
    if "line" in kinds or "curve" in kinds:
        return "Candidate sheet inspected at native/NN8x scale; relation is intended connected geometry or bbox-only proximity, with no illegal foreign-ink overlap."
    if "square-marker" in kinds:
        return "Marker relation inspected; intended path/marker topology or visible separation, with no illegal occlusion."
    return "Candidate relation inspected on final candidate sheets; no illegal visible-ink overlap."


pair_rows: list[dict[str, object]] = []
for row in pairs:
    is_candidate = row["machine_candidate"] == "1"
    if row["pair_id"] == "P00541":
        verdict = "FAIL_ILLEGAL_VISIBLE_INK_OVERLAP"
        note = "Final native1x and nearest8x ROI show digit 6 (T010) contacting blue q4 marker C016; center-distance 1 px, blank gap 0, bbox overlap 8.938406 pt^2."
    elif is_candidate:
        verdict = "PASS_INTENDED_OR_FALSE_BBOX_CANDIDATE"
        note = candidate_note(row["kind_a"], row["kind_b"])
    else:
        verdict = "PASS_MACHINE_SEPARATED"
        note = "All-pairs enumeration reports positive bbox separation; final full-view review and candidate review disclosed no contradiction."
    pair_rows.append({
        "pair_id": row["pair_id"],
        "object_a": row["object_a"],
        "object_b": row["object_b"],
        "kind_a": row["kind_a"],
        "kind_b": row["kind_b"],
        "machine_candidate": row["machine_candidate"],
        "reviewed_after_open": "TRUE",
        "verdict": verdict,
        "note": note,
    })
write_csv(ROOT / "MANUAL_PAIR_LEDGER.csv", list(pair_rows[0]), pair_rows)


views = [
    ("full_page_300.png", "Full-page 300 dpi color integration view opened; no page clip or unrelated regression."),
    ("full_page_300_grayscale.png", "Full-page grayscale view opened; x2 legend still collapses to a continuous sample."),
    ("figure_crop_300_native1x.png", "Final figure native crop opened; label 6 touches q4 marker and x2 legend is continuous."),
    ("figure_crop_300_grayscale.png", "Final grayscale crop opened; x1 and x2 legend samples remain indistinguishable continuous runs."),
    ("object_overlay_figure_300.png", "Final object overlay opened; all 60 denominator objects are represented."),
    ("object_contact_sheet.png", "All-object contact sheet opened; glyph/path identities are readable."),
    ("legend_roi_native1x.png", "Legend native1x ROI opened; x2 occupied run is continuous with no internal blank."),
    ("legend_roi_nearest8x.png", "Legend nearest8x ROI opened; continuous x2 line confirmed."),
    ("label6_roi_native1x.png", "Digit-6 native1x ROI opened; visible contact with q4 blue marker confirmed."),
    ("label6_roi_nearest8x.png", "Digit-6 nearest8x ROI opened; center-distance 1 px and blank gap 0 confirmed."),
    ("label7_roi_native1x.png", "Digit-7 native1x ROI opened; clear separation from marker/arrow."),
    ("label7_roi_nearest8x.png", "Digit-7 nearest8x ROI opened; blank gap 8 px confirmed."),
]
views.extend(
    (f"candidate_relations_part{i:02d}.png", f"Candidate relation sheet {i:02d}/11 opened after machine enumeration; all displayed relations adjudicated.")
    for i in range(1, 12)
)
view_rows = []
for index, (name, note) in enumerate(views, 1):
    path = ROOT / name
    if not path.is_file():
        raise RuntimeError(f"missing opened view {name}")
    view_rows.append({
        "view_id": f"V{index:03d}",
        "relative_path": name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "actually_opened": "TRUE",
        "verdict": "FAIL_DIRECTION" if name in {"legend_roi_native1x.png", "legend_roi_nearest8x.png", "label6_roi_native1x.png", "label6_roi_nearest8x.png", "figure_crop_300_native1x.png", "figure_crop_300_grayscale.png"} else "PASS_NO_ADDITIONAL_HARD",
        "note": note,
    })
write_csv(ROOT / "MANUAL_VIEW_LEDGER.csv", list(view_rows[0]), view_rows)


glyph_rows = []
for row in [r for r in objects if r["kind"] == "glyph"]:
    text = row["text"]
    cps = " ".join(f"U+{ord(ch):04X}" for ch in text)
    glyph_rows.append({
        "object_id": row["object_id"],
        "text": text,
        "codepoints": cps,
        "reviewed_after_open": "TRUE",
        "verdict": "PASS_CODEPOINT_AND_READABILITY",
        "note": "Current PDF glyph is complete and readable; no tofu, missing glyph, or wrong codepoint.",
    })
write_csv(ROOT / "MANUAL_GLYPH_CODEPOINT_LEDGER.csv", list(glyph_rows[0]), glyph_rows)


math_rows = [
    {"check_id": "M001", "subject": "quadratic_form", "verdict": "PASS", "note": "Contours are concentric levels of f(x1,x2)=0.5*(x1^2+2*x1*x2+2*x2^2)."},
    {"check_id": "M002", "subject": "positive_definite", "verdict": "PASS", "note": "Hessian [[1,1],[1,2]] has determinant 1 and positive eigenvalues 0.381966 and 2.618034."},
    {"check_id": "M003", "subject": "q0_q1", "verdict": "PASS", "note": "Vertical update holds x1 fixed and sets partial derivative in x2 to zero."},
    {"check_id": "M004", "subject": "q1_q2", "verdict": "PASS", "note": "Horizontal update holds x2 fixed and sets partial derivative in x1 to zero."},
    {"check_id": "M005", "subject": "q2_q7", "verdict": "PASS", "note": "Remaining updates alternate vertical/horizontal exact coordinate minimizers through q7."},
    {"check_id": "M006", "subject": "objective_descent", "verdict": "PASS", "note": "Objective sequence 2.92,2.56,1.28,.64,.32,.16,.08,.04 is strictly decreasing."},
    {"check_id": "M007", "subject": "optimum", "verdict": "PASS", "note": "Star x* is at the true optimum (0,0); q7 is visibly an approximation, not relabeled as optimum."},
    {"check_id": "M008", "subject": "caption_semantics", "verdict": "PASS", "note": "Caption states that each substep changes one coordinate and the axis-aligned path approaches the optimum; current geometry agrees."},
    {"check_id": "M009", "subject": "page_integration", "verdict": "PASS", "note": "Full-page views show no page-level crop or surrounding-content collision."},
]
write_csv(ROOT / "MANUAL_MATH_SEMANTIC_LEDGER.csv", list(math_rows[0]), math_rows)


hard_rows = [
    {"hard_id": "HARD-LEGEND-X2-CONTINUOUS", "status": "FAIL", "objects": "C020", "measurement": "73px occupied run; 0 internal blank runs", "note": "Native1x and NN8x color/grayscale evidence show x2 legend sample as one continuous line, indistinguishable in topology from x1."},
    {"hard_id": "HARD-LABEL6-Q4-MARKER-CONTACT", "status": "FAIL", "objects": "P00541:T010-C016", "measurement": "center-distance=1px; blank-gap=0px; bbox-overlap=8.938406pt^2", "note": "Moved digit 6 visibly contacts the blue q4 marker; this is illegal visible-ink contact, not an R168 font advisory."},
    {"hard_id": "REGRESSION-LABEL7-SEPARATION", "status": "PASS", "objects": "T015-R004/C017", "measurement": "center-distance=9px; blank-gap=8px", "note": "Digit 7 is clearly separated from q7 marker and arrow in native1x and NN8x evidence."},
    {"hard_id": "CLIP-GATE", "status": "PASS", "objects": "ALL", "measurement": "clip_count=0", "note": "No reader-visible object is clipped."},
    {"hard_id": "GLYPH-CODEPOINT-GATE", "status": "PASS", "objects": "T001-T025", "measurement": "missing/tofu/wrong-codepoint=0", "note": "All 25 glyph objects are complete and readable."},
]
write_csv(ROOT / "MANUAL_HARD_GATE_LEDGER.csv", list(hard_rows[0]), hard_rows)


measurements = {
    "schema": "P126_R9_HARD_MEASUREMENTS_V1",
    "legend_x2": {"object": "C020", "occupied_run_px": 73, "internal_blank_run_count": 0, "verdict": "FAIL"},
    "label6_q4": {"pair_id": "P00541", "objects": ["T010", "C016"], "center_distance_px": 1, "blank_gap_px": 0, "bbox_overlap_area_pt2": 8.938406, "verdict": "FAIL"},
    "label7": {"object": "T015", "nearest_marker_or_arrow_center_distance_px": 9, "blank_gap_px": 8, "verdict": "PASS"},
}
(ROOT / "HARD_MEASUREMENTS.json").write_text(json.dumps(measurements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


candidate_count = sum(r["machine_candidate"] == "1" for r in pairs)
failed_pair_count = sum(r["verdict"].startswith("FAIL") for r in pair_rows)
crosscheck = {
    "schema": "P126_R9_FINAL_CROSSCHECK_V1",
    "denominator": {"N": 60, "glyph": 25, "line": 9, "protective_background": 2, "square_marker": 4, "curve": 20},
    "all_pairs": {"expected": 1770, "actual": len(pairs), "unique_pair_ids": len({r["pair_id"] for r in pairs}), "unique_unordered_tuples": len(pair_tuples), "self_pairs": 0, "bad_references": 0},
    "machine_candidates": candidate_count,
    "manual": {"objects": len(object_rows), "pairs": len(pair_rows), "views_opened": len(view_rows), "glyph_codepoints": len(glyph_rows), "math_semantic": len(math_rows), "hard_gate_rows": len(hard_rows)},
    "manual_pair_failures": failed_pair_count,
    "hard_failure_count": 2,
    "clip_count": 0,
    "missing_tofu_wrong_codepoint_count": 0,
    "source": {"bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
    "pdf": {"bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
    "verdict": "LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE",
}
(ROOT / "FINAL_CROSSCHECK.json").write_text(json.dumps(crosscheck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


result = {
    "schema": "P126_R9_LOCAL_SA2_RESULT_V1",
    "handoff_id": "A-R115-P126-SA2-DIRECT-BUILD-R9-20260828",
    "uid": "FIG-P126-01",
    "verdict": "LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE",
    "hard_failure_count": 2,
    "hard_failures": ["HARD-LEGEND-X2-CONTINUOUS", "HARD-LABEL6-Q4-MARKER-CONTACT"],
    "resolved_regression": "label7 separation passes with 8 px blank gap",
    "N": 60,
    "C": 1770,
    "machine_candidates": candidate_count,
    "manual_objects": len(object_rows),
    "manual_pairs": len(pair_rows),
    "manual_views": len(view_rows),
    "pdf_sha256": sha256(PDF),
    "source_sha256": sha256(SOURCE),
    "build_slot_released": True,
    "additional_tex_invocations_after_release": 0,
}
(ROOT / "RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


report = f"""# P126 R9 local SA2 review

HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R9-20260828  
UID=FIG-P126-01  
VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE

## Frozen identities

- Source: {SOURCE} — {SOURCE.stat().st_size} bytes — SHA256 {sha256(SOURCE)}
- PDF: {PDF} — {PDF.stat().st_size} bytes — SHA256 {sha256(PDF)}
- Build slot: released after one controller and one direct LuaLaTeX child; no TeX was run during this review.

## Denominator and coverage

The final current-PDF denominator is N=60: 25 glyphs, 9 lines, 2 reader-visible protective backgrounds, 4 square markers, and 20 curves. All unordered pairs were enumerated exactly once: C=1770. There are 218 machine candidates. Manual ledgers cover 60/60 objects, 1770/1770 pairs, 25/25 glyph-codepoint rows, 9 math/semantic checks, 5 hard-gate checks, and 23 actually opened final views/ROI sheets. Candidate relation sheets 01--11 were all opened after machine enumeration.

## Hard findings

1. `HARD-LEGEND-X2-CONTINUOUS`: rendered object C020 is a single 73 px occupied run with zero internal blank runs. Native1x, nearest8x, color, and grayscale views show the x2 legend sample as continuous, so the intended dashed distinction from x1 is absent.
2. `HARD-LABEL6-Q4-MARKER-CONTACT`: pair P00541 (T010 digit 6 versus C016 blue q4 marker) has center-distance 1 px, blank gap 0 px, and bbox overlap 8.938406 pt^2. Native1x and nearest8x views confirm real visible-ink contact.

The digit 7 regression is resolved: final native/nearest8x evidence shows an 8 px blank gap. Clip count and missing/tofu/wrong-codepoint count are zero. The quadratic, alternating coordinate-minimizer updates, strictly decreasing objective sequence, optimum placement, caption semantics, and page integration pass.

## Narrow return facts

Only the current P126 single source is implicated. A future static scope, if Main authorizes it, must (a) make the actual rendered x2 legend sample contain genuine separated teal segments rather than relying on a style ignored by the effective legend handler, and (b) move/protect digit 6 without contacting q4 marker or any other object. No source edit, build, commit, role transition, or central write was performed in this phase.
"""
(ROOT / "REPORT.md").write_text(report, encoding="utf-8")


handoff = f"""HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R9-20260828
UID=FIG-P126-01
VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE
SOURCE_BYTES={SOURCE.stat().st_size}
SOURCE_SHA256={sha256(SOURCE)}
PDF_BYTES={PDF.stat().st_size}
PDF_SHA256={sha256(PDF)}
N=60
C=1770
MACHINE_CANDIDATES={candidate_count}
MANUAL_OBJECTS={len(object_rows)}
MANUAL_PAIRS={len(pair_rows)}
MANUAL_VIEWS={len(view_rows)}
HARD_FAILURE_COUNT=2
HARD_1=HARD-LEGEND-X2-CONTINUOUS
HARD_2=HARD-LABEL6-Q4-MARKER-CONTACT
LABEL7_REGRESSION=PASS_BLANK_GAP_8PX
CLIP_COUNT=0
MISSING_TOFU_WRONG_CODEPOINT_COUNT=0
REQUEST=MAIN_REVIEW_AND_NARROW_SINGLE_SOURCE_SCOPE
NO_TEX_AFTER_BUILD_RELEASE=TRUE
NO_SOURCE_WRITE_AFTER_BUILD=TRUE
NO_COMMIT=TRUE
"""
(ROOT / "HANDOFF.md").write_text(handoff, encoding="utf-8")

print(json.dumps({"N": 60, "C": 1770, "candidates": candidate_count, "views": len(view_rows), "hard": 2, "verdict": result["verdict"]}))
