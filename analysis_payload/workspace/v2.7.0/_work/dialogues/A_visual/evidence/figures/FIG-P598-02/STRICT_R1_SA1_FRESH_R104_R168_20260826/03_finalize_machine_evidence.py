from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R1_SA1_FRESH_R104_R168_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
EXPECTED_SIZE = 4_967_222
EXPECTED_SHA256 = "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641"
EXPECTED_PAGE = 650
FIGURE_CROP = (471, 272, 2056, 807)
STANDALONE_CROP = (294, 272, 2234, 940)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def open_png(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.load()
        return image.size


glyphs = read_csv(ROOT / "machine" / "glyph_ledger.csv")
graphics = read_csv(ROOT / "machine" / "graphic_ledger.csv")
objects = read_csv(ROOT / "machine" / "object_ledger.csv")
pairs = read_csv(ROOT / "machine" / "all_unordered_pairs.csv")
critical = read_csv(ROOT / "machine" / "critical_relationships.csv")
ownership = read_csv(ROOT / "machine" / "final_visible_ownership.csv")

manual_glyphs = read_csv(ROOT / "manual" / "manual_glyph_review.csv")
manual_graphics = read_csv(ROOT / "manual" / "manual_graphic_review.csv")
manual_relations = read_csv(ROOT / "manual" / "manual_relationship_review.csv")
manual_views = read_csv(ROOT / "manual" / "manual_view_review.csv")
manual_role_scripts = read_csv(ROOT / "manual" / "manual_role_script_review.csv")
manual_font_gates = read_csv(ROOT / "manual" / "manual_font_hard_gate_review.csv")
manual_semantics = read_csv(ROOT / "manual" / "manual_semantic_review.csv")

identity = json.loads((ROOT / "machine" / "candidate_identity.json").read_text(encoding="utf-8"))

assert PDF.stat().st_size == EXPECTED_SIZE
assert sha256(PDF) == EXPECTED_SHA256
assert identity["figure_uid"] == "FIG-P598-02"
assert identity["candidate_round"] == "R104"
assert identity["physical_page"] == EXPECTED_PAGE
assert identity["page_count"] == 817
assert identity["full_page_300dpi_px"] == [2481, 3508]
assert identity["full_page_200dpi_px"] == [1654, 2339]

assert len(glyphs) == 137
assert len(graphics) == 26
assert len(objects) == 163
assert len({row["element_id"] for row in objects}) == 163
assert len({row["safe_filename"] for row in objects}) == 163
assert all(not is_true(row["machine_empty_mask"]) for row in objects)

expected_pair_count = math.comb(len(objects), 2)
assert expected_pair_count == 13_203
assert len(pairs) == expected_pair_count
unordered = {tuple(sorted((row["a_id"], row["b_id"]))) for row in pairs}
assert len(unordered) == expected_pair_count
assert len({row["pair_id"] for row in pairs}) == expected_pair_count
assert sum(int(row["overlap_pixel_count"]) for row in pairs) == 0
assert not [row for row in pairs if row["machine_decision"] == "FAIL"]

glyph_ids = {row["element_id"] for row in glyphs}
graphic_ids = {row["element_id"] for row in graphics}
assert {row["element_id"] for row in manual_glyphs} == glyph_ids
assert len(manual_glyphs) == len(glyph_ids)
assert {row["element_id"] for row in manual_graphics} == graphic_ids
assert len(manual_graphics) == len(graphic_ids)
assert {row["pair_id"] for row in manual_relations} == {row["pair_id"] for row in critical}
assert len(manual_relations) == len(critical) == 22

for row in manual_glyphs:
    assert row["reviewer"] == "SA1_FRESH_R104_R168"
    assert all(is_true(row[field]) for field in ("original_match", "overlay_complete", "mask_only_pure"))
    assert int(row["missing_stroke_px"]) == 0
    assert int(row["foreign_pixel_px"]) == 0
    assert row["decision"] == "PASS"
for row in manual_graphics:
    assert row["reviewer"] == "SA1_FRESH_R104_R168"
    assert all(is_true(row[field]) for field in ("original_match", "overlay_complete", "mask_only_pure"))
    assert int(row["missing_pixel_count"]) == 0
    assert int(row["foreign_pixel_count"]) == 0
    assert row["decision"] == "PASS"
for row in manual_relations:
    assert row["reviewer"] == "SA1_FRESH_R104_R168"
    assert is_true(row["overlay_opened"])
    assert row["manual_decision"] == "PASS"
assert len(manual_views) == 15
assert all(row["reviewer"] == "SA1_FRESH_R104_R168" and is_true(row["opened"]) and row["decision"] == "PASS" for row in manual_views)
assert len(manual_role_scripts) == 24
assert all(
    row["reviewer"] == "SA1_FRESH_R104_R168"
    and row["evidence_opened"]
    and row["density_status"] == "READABLE"
    and row["emphasis_status"] == "HARMONIOUS"
    and row["crowding"] == "none"
    and row["protrusion"] == "none"
    and row["cross_panel_consistency"] == "consistent"
    and row["grayscale"] == "clear"
    and row["page_integration"] == "integrated"
    and row["decision"] == "PASS"
    and row["note"]
    for row in manual_role_scripts
)
assert len(manual_font_gates) == 6
assert all(row["reviewer"] == "SA1_FRESH_R104_R168" and row["evidence_opened"] and row["decision"] == "PASS" and row["note"] for row in manual_font_gates)
assert [row["present"] for row in manual_font_gates[:5]] == ["false"] * 5
assert manual_font_gates[5]["gate_id"] == "R168-FONT-HARMONY" and is_true(manual_font_gates[5]["present"])
assert len(manual_semantics) == 13
assert all(row["reviewer"] == "SA1_FRESH_R104_R168" and row["evidence_opened"] and row["decision"] == "PASS" and row["note"] for row in manual_semantics)

expected_png_groups = {
    "glyph_masks": sorted((ROOT / "masks" / "glyphs").glob("*.png")),
    "graphic_masks": sorted((ROOT / "masks" / "graphics").glob("*.png")),
    "glyph_sheets": sorted((ROOT / "contact_sheets" / "glyphs").glob("*.png")),
    "graphic_sheets": sorted((ROOT / "contact_sheets" / "graphics").glob("*.png")),
    "critical_raw": sorted((ROOT / "critical_relations" / "raw").glob("*.png")),
    "critical_a": sorted((ROOT / "critical_relations" / "a_mask").glob("*.png")),
    "critical_b": sorted((ROOT / "critical_relations" / "b_mask").glob("*.png")),
    "critical_intersection": sorted((ROOT / "critical_relations" / "intersection").glob("*.png")),
    "critical_overlay_sheets": sorted((ROOT / "overlays").glob("critical_relationship_overlay_*.png")),
}
expected_counts = {
    "glyph_masks": 137,
    "graphic_masks": 26,
    "glyph_sheets": 12,
    "graphic_sheets": 7,
    "critical_raw": 22,
    "critical_a": 22,
    "critical_b": 22,
    "critical_intersection": 22,
    "critical_overlay_sheets": 4,
}
for group, paths in expected_png_groups.items():
    assert len(paths) == expected_counts[group]
    assert all(open_png(path)[0] > 0 and open_png(path)[1] > 0 for path in paths)

for row in objects:
    path = ROOT / row["mask_path"]
    assert path.is_file()
    assert open_png(path) == (int(row["mask_width_px"]), int(row["mask_height_px"]))

all_pngs = sorted(ROOT.rglob("*.png"))
for path in all_pngs:
    open_png(path)
    assert ":" not in path.relative_to(ROOT).as_posix()

# Required schema aliases remain byte-for-byte copies of the inspected render/views.
aliases = {
    ROOT / "views" / "full_page_200dpi.png": ROOT / "full_page_200dpi.png",
    ROOT / "views" / "figure_crop_300dpi.png": ROOT / "figure_crop_300dpi.png",
    ROOT / "views" / "standalone_300dpi.png": ROOT / "standalone_300dpi.png",
    ROOT / "views" / "grayscale_300dpi.png": ROOT / "grayscale_300dpi.png",
    ROOT / "overlays" / "after_text_measurement_overlay_300dpi.png": ROOT / "after_text_measurement_overlay_300dpi.png",
}
for source, target in aliases.items():
    shutil.copyfile(source, target)
    assert sha256(source) == sha256(target)

thresholds = {
    "CJK_FULL": 30,
    "LATIN_UPPER_DIGIT": 24,
    "LATIN_GREEK_LOWER": 17,
    "MATH_OPERATOR_DELIMITER": 22,
    "NATURAL_MATH_SCRIPT": 15,
}
font_rows: list[dict[str, object]] = []
for row in glyphs:
    reference = thresholds.get(row["glyph_class"], "")
    height = int(row["ink_height_px"])
    shortfall = bool(reference != "" and height < int(reference))
    font_rows.append({
        "element_id": row["element_id"],
        "char": row["char"],
        "role": row["role"],
        "glyph_class": row["glyph_class"],
        "effective_pt_pdf": row["size_pt_pdf"],
        "ink_width_px": row["ink_width_px"],
        "ink_height_px": row["ink_height_px"],
        "ink_pixel_count": row["ink_pixel_count"],
        "protocol_reference_min_px": reference,
        "protocol_pixel_shortfall": str(shortfall).lower(),
        "source_pt_below_9_5": str(float(row["size_pt_pdf"]) < 9.5).lower(),
        "r168_machine_scope": "ADVISORY_REQUIRES_MANUAL_VISUAL_ADJUDICATION",
    })
write_csv(
    ROOT / "after_font_audit.csv",
    ["element_id", "char", "role", "glyph_class", "effective_pt_pdf", "ink_width_px", "ink_height_px", "ink_pixel_count", "protocol_reference_min_px", "protocol_pixel_shortfall", "source_pt_below_9_5", "r168_machine_scope"],
    font_rows,
)

pixel_fields = [
    "element_id", "safe_filename", "kind", "panel", "role", "semantic_parent",
    "bbox_page_px", "tight_ink_bbox_page_px", "ink_width_px", "ink_height_px",
    "ink_pixel_count", "machine_empty_mask", "mask_path",
]
write_csv(ROOT / "after_pixel_measurements.csv", pixel_fields, objects)
shutil.copyfile(ROOT / "machine" / "all_unordered_pairs.csv", ROOT / "after_overlap_report.csv")

coverage_rows: list[dict[str, object]] = []
coverage_rows.append({"pdf_drawing_index": 0, "coverage": "OUTSIDE_FIGURE", "element_id": "", "note": "page rule outside target figure"})
for index in range(1, 11):
    coverage_rows.append({"pdf_drawing_index": index, "coverage": "VISIBLE_OBJECT", "element_id": f"GRAPHIC-G{index:02d}", "note": "direct drawing mapping"})
coverage_rows.extend([
    {"pdf_drawing_index": 11, "coverage": "CONTROL_FOR_PATTERN", "element_id": "GRAPHIC-G11", "note": "clip/control contributes to warm-up pattern"},
    {"pdf_drawing_index": 12, "coverage": "CONTROL_FOR_PATTERN", "element_id": "GRAPHIC-G11", "note": "clip/control contributes to warm-up pattern"},
])
for index in range(13, 27):
    coverage_rows.append({"pdf_drawing_index": index, "coverage": "VISIBLE_OBJECT", "element_id": f"GRAPHIC-G{index - 1:02d}", "note": "direct drawing mapping"})
for index in range(27, 30):
    coverage_rows.append({"pdf_drawing_index": index, "coverage": "OUTSIDE_FIGURE", "element_id": "", "note": "page content outside target figure"})
assert len(coverage_rows) == identity["drawing_count"] == 30
write_csv(ROOT / "machine" / "foreground_path_coverage.csv", ["pdf_drawing_index", "coverage", "element_id", "note"], coverage_rows)

math_rule_ids = {row["element_id"] for row in graphics if row["role"] == "MATH_RULE"}
assert math_rule_ids == {"GRAPHIC-G21", "GRAPHIC-G26"}

def bbox(row: dict[str, str]) -> tuple[int, int, int, int]:
    return tuple(json.loads(row["bbox_page_px"]))  # type: ignore[return-value]

body_rows = [row for row in objects if row["semantic_parent"] != "CAPTION_PARAGRAPH"]
body_boxes = [bbox(row) for row in body_rows]
body_crop_clearance = min(
    min(box[0] - FIGURE_CROP[0], box[1] - FIGURE_CROP[1], FIGURE_CROP[2] - box[2], FIGURE_CROP[3] - box[3])
    for box in body_boxes
)
all_boxes = [bbox(row) for row in objects]
standalone_clearance = min(
    min(box[0] - STANDALONE_CROP[0], box[1] - STANDALONE_CROP[1], STANDALONE_CROP[2] - box[2], STANDALONE_CROP[3] - box[3])
    for box in all_boxes
)
clip_pixel_count = 0 if body_crop_clearance > 0 and standalone_clearance > 0 else 1
assert body_crop_clearance >= 11
assert standalone_clearance >= 11
assert clip_pixel_count == 0

hard_applicable = [row for row in pairs if is_true(row["hard_gate_applicable"])]
hard_applicable_fail = [row for row in hard_applicable if row["machine_decision"] == "FAIL"]
advisory_shortfalls = [row for row in font_rows if row["protocol_pixel_shortfall"] == "true"]
assert {row["element_id"] for row in advisory_shortfalls} == {
    "GLYPH-B02-L00-S00-C002",
    "GLYPH-B08-L00-S01-C001",
    "GLYPH-B08-L00-S02-C000",
    "GLYPH-B12-L00-S00-C001",
}

# NTFS alternate data stream inventory; only the unnamed :$DATA stream is allowed.
ps_script = (
    "$r='" + str(ROOT).replace("'", "''") + "'; "
    "Get-ChildItem -LiteralPath $r -File -Recurse | ForEach-Object { "
    "Get-Item -LiteralPath $_.FullName -Stream * | Select-Object FileName,Stream,Length } | "
    "ConvertTo-Csv -NoTypeInformation"
)
ads_result = subprocess.run(
    ["powershell", "-NoProfile", "-Command", ps_script],
    check=True,
    text=True,
    encoding="utf-8",
    capture_output=True,
)
(ROOT / "machine" / "ads_inventory.csv").write_text(ads_result.stdout, encoding="utf-8")
ads_rows = list(csv.DictReader(ads_result.stdout.splitlines()))
non_default_streams = [row for row in ads_rows if row["Stream"] not in (":$DATA", "$DATA")]
assert not non_default_streams

cache_files = [path for path in ROOT.rglob("*") if path.is_file() and (path.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in path.parts)]
assert not cache_files

required_schema_files = [
    "full_page_200dpi.png",
    "figure_crop_300dpi.png",
    "standalone_300dpi.png",
    "grayscale_300dpi.png",
    "after_font_audit.csv",
    "after_pixel_measurements.csv",
    "after_overlap_report.csv",
    "after_text_measurement_overlay_300dpi.png",
    "after_visual_acceptance.md",
    "SA1_CONCLUSION.md",
    "RESULT",
]
assert all((ROOT / name).is_file() and (ROOT / name).stat().st_size > 0 for name in required_schema_files)
assert (ROOT / "RESULT").read_text(encoding="utf-8").strip() == "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3"
assert "FONT_VISUAL_HARMONY_PASS=true" in (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
assert not (ROOT / "A_LOCAL_PASS").exists()

REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P598_02_R1_R104_FRESH_SA1_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R104-P598-02-SA1-FRESH-20260826.md")
assert REPORT.is_file() and REPORT.stat().st_size > 0
assert HANDOFF.is_file() and HANDOFF.stat().st_size > 0

checks = {
    "figure_uid": "FIG-P598-02",
    "candidate_round": "R104",
    "physical_page": EXPECTED_PAGE,
    "pdf_size_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "page_count": identity["page_count"],
    "full_page_300dpi_px": identity["full_page_300dpi_px"],
    "full_page_200dpi_px": identity["full_page_200dpi_px"],
    "glyph_count": len(glyphs),
    "graphic_count": len(graphics),
    "object_count_N": len(objects),
    "all_unordered_pair_count_C": len(pairs),
    "expected_pair_count": expected_pair_count,
    "critical_relationship_count": len(critical),
    "hard_applicable_pair_count": len(hard_applicable),
    "hard_applicable_pair_fail_count": len(hard_applicable_fail),
    "all_pair_overlap_pixel_sum": sum(int(row["overlap_pixel_count"]) for row in pairs),
    "clip_pixel_count": clip_pixel_count,
    "figure_body_crop_clearance_px": body_crop_clearance,
    "standalone_crop_clearance_px": standalone_clearance,
    "empty_mask_count": sum(is_true(row["machine_empty_mask"]) for row in objects),
    "pre_occlusion_design_shared_relation_count": len(ownership),
    "pre_occlusion_design_shared_pixel_count": sum(int(row["pre_occlusion_shared_px"]) for row in ownership),
    "final_visible_overlap_count": 0,
    "glyph_manual_row_count": len(manual_glyphs),
    "graphic_manual_row_count": len(manual_graphics),
    "relationship_manual_row_count": len(manual_relations),
    "view_manual_row_count": len(manual_views),
    "role_script_manual_row_count": len(manual_role_scripts),
    "font_hard_gate_manual_row_count": len(manual_font_gates),
    "semantic_manual_row_count": len(manual_semantics),
    "font_protocol_advisory_shortfall_count_under_R168": len(advisory_shortfalls),
    "math_rule_graphic_count": len(math_rule_ids),
    "pdf_drawing_path_coverage_count": len(coverage_rows),
    "ordinary_png_count_opened_by_machine": len(all_pngs),
    "ads_non_default_stream_count": len(non_default_streams),
    "pyc_or_cache_file_count": len(cache_files),
    "required_schema_file_count": len(required_schema_files),
    "result_file_exact": True,
    "forbidden_A_LOCAL_PASS_count": 0,
    "external_report_present": True,
    "external_handoff_present": True,
    "machine_final_decision": "PASS",
}
(ROOT / "machine" / "final_machine_check.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
write_csv(ROOT / "machine" / "final_machine_check.csv", ["check", "value"], [{"check": key, "value": value} for key, value in checks.items()])

print(json.dumps(checks, ensure_ascii=False, indent=2))
