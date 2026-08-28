from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "seal"
REPORTS = ROOT / "reports"
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex"
SOURCE = WORKTREE / Path(SOURCE_REL)
PAGE_PDF = ROOT / "build" / "page" / "v260_FIG-P654-01_page.pdf"
STANDALONE_PDF = ROOT / "build" / "standalone" / "v260_FIG-P654-01_standalone.pdf"
HANDOFF = "A-R130-P654-SA2-REPAIR-V2-20260824"
ROUTE = "LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1"
EXPECTED_HEAD = "e933f09e757d406954edd09f8ce0a326248c7da9"
EXPECTED_SOURCE_SHA = "8041DAF98B04D763958DA9C83AF3472FA346D003F0FDCEF13A42FE1AA046B5F8"
EXPECTED_R98_SHA = "52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41"
EXPECTED_INTENTIONAL = {
    "PAIR_096_105", "PAIR_097_107", "PAIR_098_106", "PAIR_098_108",
    "PAIR_098_109", "PAIR_098_113", "PAIR_099_110", "PAIR_099_111",
    "PAIR_099_114", "PAIR_100_112", "PAIR_100_115", "PAIR_102_113",
    "PAIR_103_114", "PAIR_104_116", "PAIR_105_106", "PAIR_107_108",
    "PAIR_109_110", "PAIR_111_112", "PAIR_115_116",
}
EXPECTED_CRITICAL = EXPECTED_INTENTIONAL - {"PAIR_098_106", "PAIR_098_108"}


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalized_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_text(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=WORKTREE,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def git_nul(*args: str) -> list[str]:
    data = subprocess.run(["git", *args], cwd=WORKTREE, check=True, capture_output=True).stdout
    return [part.decode("utf-8") for part in data.split(b"\0") if part]


checks: dict[str, object] = {}
failures: list[str] = []


def check(name: str, passed: bool, detail: object) -> None:
    checks[name] = {"pass": bool(passed), "detail": detail}
    if not passed:
        failures.append(name)


check(
    "preseal_marker_absent",
    not (SEAL / "WRITE_STOPPED").exists() and not (ROOT / "WRITE_STOPPED").exists(),
    "no WRITE_STOPPED exists before terminal",
)

identity = json.loads((REPORTS / "candidate_identity.json").read_text(encoding="utf-8"))
matrix = json.loads((REPORTS / "final_matrix.json").read_text(encoding="utf-8"))
summary = json.loads((REPORTS / "denominator_and_machine_summary.json").read_text(encoding="utf-8"))
consistency = json.loads((REPORTS / "standalone_page_consistency.json").read_text(encoding="utf-8"))
crop = json.loads((REPORTS / "crop_safety_audit.json").read_text(encoding="utf-8"))
semantics = json.loads((REPORTS / "text_and_math_semantics.json").read_text(encoding="utf-8"))
build_logs = json.loads((REPORTS / "build_log_audit.json").read_text(encoding="utf-8"))
views = json.loads((REPORTS / "view_opening_attestation.json").read_text(encoding="utf-8"))
low_audit = json.loads((REPORTS / "low_profile_zero_target_audit.json").read_text(encoding="utf-8"))

local_identity = identity["local_sa2_candidate_identity"]
r98_identity = identity["official_r98_frozen_identity"]
check("identity_handoff_route", identity["handoff_id"] == HANDOFF and identity["route_boundary"] == ROUTE, {"handoff": identity["handoff_id"], "route": identity["route_boundary"]})
check("source_identity", normalized_sha(SOURCE) == EXPECTED_SOURCE_SHA == local_identity["source_normalized_sha256"] == matrix["source_normalized_sha256"], normalized_sha(SOURCE))
check("r98_identity_declaration", r98_identity["identity_match"] is True and r98_identity["sha256"] == EXPECTED_R98_SHA and r98_identity["pages"] == 813 and r98_identity["bytes"] == 4_934_249 and r98_identity["pdf_target_physical_page"] == 702 and r98_identity["pdf_target_printed_label"] == "689", r98_identity)
r98_path = Path(r98_identity["path"])
check("r98_identity_recheck", r98_path.is_file() and r98_path.stat().st_size == 4_934_249 and file_sha(r98_path) == EXPECTED_R98_SHA, {"path": str(r98_path), "bytes": r98_path.stat().st_size if r98_path.exists() else None})
check("local_page_pdf_identity", file_sha(PAGE_PDF) == local_identity["page_wrapper"]["sha256"] and PAGE_PDF.stat().st_size == local_identity["page_wrapper"]["bytes"], local_identity["page_wrapper"])
check("local_standalone_pdf_identity", file_sha(STANDALONE_PDF) == local_identity["standalone_wrapper"]["sha256"] and STANDALONE_PDF.stat().st_size == local_identity["standalone_wrapper"]["bytes"], local_identity["standalone_wrapper"])

head = git_text("rev-parse", "HEAD").strip()
unstaged = git_nul("diff", "--name-only", "-z")
staged = git_nul("diff", "--cached", "--name-only", "-z")
untracked = git_nul("ls-files", "--others", "--exclude-standard", "-z")
diff_bytes = subprocess.run(["git", "diff", "--binary", "--", SOURCE_REL], cwd=WORKTREE, check=True, capture_output=True).stdout
check("git_base_head_unchanged", head == EXPECTED_HEAD == local_identity["base_head"], head)
check("sole_unstaged_business_source", unstaged == [SOURCE_REL] and not staged and not untracked, {"unstaged": unstaged, "staged": staged, "untracked": untracked})
check("source_diff_frozen", hashlib.sha256(diff_bytes).hexdigest().upper() == local_identity["source_diff_sha256"] and local_identity["source_diff_numstat"] == {"insertions": 21, "deletions": 23, "files": 1}, {"diff_sha": hashlib.sha256(diff_bytes).hexdigest().upper(), "numstat": local_identity["source_diff_numstat"]})
check("commit_deferred_to_root", local_identity["commit_deferred_to_root_after_write_stopped"] is True, local_identity["commit_deferred_to_root_after_write_stopped"])

glyphs = rows("inventory/glyph_inventory.csv")
graphics = rows("inventory/graphic_path_inventory.csv")
pairs = rows("ledgers/all_unordered_pairs.csv")
glyph_manual = rows("ledgers/glyph_manual_review.csv")
graphic_manual = rows("ledgers/graphic_manual_review.csv")
critical = rows("ledgers/critical_pair_manual_review.csv")
low = rows("inventory/low_profile_reference_results.csv")
elements = rows("inventory/semantic_elements.csv")
parent = rows("ledgers/parent_text_bbox_audit.csv")
visual = rows("ledgers/visual_review.csv")
font = rows("after_font_audit.csv")
pixel = rows("after_pixel_measurements.csv")

ids = [row["object_id"] for row in glyphs + graphics]
check("denominator_N116", len(glyphs) == 95 and len(graphics) == 21 and len(ids) == 116 and len(set(ids)) == 116, {"glyphs": len(glyphs), "graphics": len(graphics), "unique": len(set(ids))})
check("pair_denominator_6670", len(pairs) == 6670 and len({row["pair_id"] for row in pairs}) == 6670 and len(pairs) == len(ids) * (len(ids) - 1) // 2, len(pairs))
check("pair_endpoints_known", all(row["object_a"] in ids and row["object_b"] in ids for row in pairs), "all 6,670 endpoints resolve")
check("math_rule_one", sum(row["graphic_class"] == "MATH_RULE" for row in graphics) == 1 and [row["object_id"] for row in graphics if row["graphic_class"] == "MATH_RULE"] == ["P006"], [row["object_id"] for row in graphics if row["graphic_class"] == "MATH_RULE"])
check("trace_and_coverage_closure", summary["raw_trace_character_slots_in_crop"] == 95 and summary["invisible_space_exclusions"] == 0 and summary["unassigned_text_pixels"] == 0 and summary["foreground_coverage_residual_pixels"] == 0 and summary["foreground_coverage_excess_pixels"] == 0, {key: summary[key] for key in ("raw_trace_character_slots_in_crop", "invisible_space_exclusions", "unassigned_text_pixels", "foreground_coverage_residual_pixels", "foreground_coverage_excess_pixels")})
check("empty_masks_zero", all(row["empty_mask"] == "0" for row in glyphs + graphics), "all 116 masks nonempty")
check(
    "glyph_numeric_all_pass",
    len(glyphs) == 95
    and all(
        row["numeric_status"] == "PASS_NUMERIC"
        and float(row["declared_pt"]) >= 9.5
        and (row["script_class"] == "NATURAL_SCRIPT" or float(row["effective_pt"]) >= 9.5)
        and int(row["h_ink_px"]) >= int(row["h_threshold_px"])
        for row in glyphs
    ),
    {
        "numeric_failures": [row["object_id"] for row in glyphs if row["numeric_status"] != "PASS_NUMERIC"],
        "note": "natural mathematical subscripts use the protocol's NATURAL_SCRIPT pixel gate; declared source size remains 11.6pt",
    },
)
check("low_profile_zero_target", not low and not [row for row in glyphs if row["script_class"] == "LOW_PROFILE_PUNCTUATION"] and low_audit["status"] == "PASS_ZERO_TARGET" and low_audit["target_count"] == 0, low_audit)
check("graphic_numeric_all_pass", len(graphics) == 21 and all(row["graphic_status"] == "PASS_NUMERIC" for row in graphics), [row["object_id"] for row in graphics if row["graphic_status"] != "PASS_NUMERIC"])
check("object_mask_manual_purity", all(row["foreign_pixel_px"] == "0" and row["missing_stroke_px"] == "0" for row in glyphs + graphics), "all 116 foreign=0/missing=0")
check("glyph_manual_95", len(glyph_manual) == 95 and all(row["decision"] == "PASS_MASK" and row["opened_native_1x"] == "YES" and row["opened_8x"] == "YES" and "PENDING" not in "|".join(row.values()) for row in glyph_manual), len(glyph_manual))
check("graphic_manual_21", len(graphic_manual) == 21 and all(row["decision"] == "PASS_MASK" and row["opened_native_1x"] == "YES" and row["opened_8x"] == "YES" and "PENDING" not in "|".join(row.values()) for row in graphic_manual), len(graphic_manual))

intentional_ids = {row["pair_id"] for row in pairs if row["intentional_contact"] == "1"}
raw_contact_ids = {row["pair_id"] for row in pairs if int(row["raw_pre_overlap_px"]) > 0}
critical_ids = {row["pair_id"] for row in critical}
check("pair_specific_whitelist_exact", intentional_ids == EXPECTED_INTENTIONAL, sorted(intentional_ids))
check("raw_contacts_exact_critical", raw_contact_ids == EXPECTED_CRITICAL == critical_ids, {"raw": sorted(raw_contact_ids), "critical": sorted(critical_ids)})
check("critical_manual_17", len(critical) == 17 and all(row["opened_native_1x"] == "YES" and row["opened_8x"] == "YES" and row["source_semantics_checked"] == "YES" and row["z_order_checked"] == "YES" and row["decision"] == "PASS_INTENTIONAL_GEOMETRIC_CONTACT" for row in critical), len(critical))
check("all_pair_manual_6670", all(row.get("manual_reviewer") and row.get("manual_basis") and row.get("manual_decision") and row.get("manual_note") and row.get("final_status", "").startswith("PASS") for row in pairs), "every pair has row-specific PASS adjudication")
check("pair_machine_final_zero_failures", not [row for row in pairs if row["status"] == "FAIL" or row.get("final_status") == "FAIL"] and sum(int(row["final_overlap_px"]) for row in pairs) == 0, {"machine_failures": sum(row["status"] == "FAIL" for row in pairs), "final_failures": sum(row.get("final_status") == "FAIL" for row in pairs), "final_overlap_sum": sum(int(row["final_overlap_px"]) for row in pairs)})
check("parent_bbox_clearance", len(parent) == 55 and not [row for row in parent if row["status"] != "PASS"] and min(float(row["bbox_clearance_px"]) for row in parent) >= 4, {"rows": len(parent), "minimum_px": min(float(row["bbox_clearance_px"]) for row in parent)})
check("D_E_zero_failures", len(elements) == 19 and not [row for row in elements if row["D_status"] == "FAIL"] and not [row for row in elements if row["E_status"] == "FAIL"], {"elements": len(elements), "D": sum(row["D_status"] == "FAIL" for row in elements), "E": sum(row["E_status"] == "FAIL" for row in elements)})
check("font_audit_all_pass", len(font) == 25 and all(row["decision"] == "PASS" and "PENDING" not in "|".join(row.values()) for row in font) and {row["id"] for row in font if row["record_type"] == "SUMMARY_GATE"} == {"SOURCE_FONT_PASS", "PIXEL_HEIGHT_PASS", "LOW_PROFILE_REFERENCE_PASS", "SAME_CLASS_RATIO_PASS", "ROLE_RATIO_PASS", "FONT_VISUAL_HARMONY_PASS"}, {"rows": len(font), "summary": [row["id"] for row in font if row["record_type"] == "SUMMARY_GATE"]})
check("pixel_report_95", len(pixel) == 95 and all(row["status"] == "PASS_NUMERIC" and row["missing_stroke_px"] == "0" and row["foreign_pixel_px"] == "0" for row in pixel), len(pixel))
check("visual_ledger_complete", len(visual) >= 23 and all(row["opened"] == "YES" and row["decision"].startswith("PASS") and row["note"] for row in visual), len(visual))

check("crop_final_pass", crop["status"] == "PASS" and crop["candidate_page_pdf_complete"] is True and crop["final_crop_fullpage_px"] == [310, 428, 2245, 1032] and crop["final_crop_grid_px"] == [1935, 604] and crop["final_foreground_margins_px"] == {"left": 10, "top": 10, "right": 37, "bottom": 11} and crop["final_foreground_edge_min_px"] == 10 and crop["final_text_bbox_edge_min_px"] == 30, crop)
check("crop_trial_distinguished", crop["rejected_trial_crop_fullpage_px"] == [326, 435, 2237, 1025] and crop["rejected_trial_foreground_margins_px"] == {"left": 0, "top": 3, "right": 29, "bottom": 4} and crop["rejected_trial_disposition"] == "excluded from final conclusions" and (ROOT / crop["rejected_trial_path"]).is_file(), crop["rejected_trial_path"])
check("standalone_page_consistency", consistency["status"] == "PASS" and consistency["drawing_count"] == 21 and consistency["visible_nonspace_glyphs"] == 95 and consistency["text_sequence_exact"] is True and not consistency["drawing_failures"] and not consistency["text_failures"] and consistency["max_text_translation_residual_pt"] <= consistency["tolerance_pt"], {"translation": consistency["translation_page_minus_standalone_pt"], "max_text_residual": consistency["max_text_translation_residual_pt"]})
check("text_math_semantics", semantics["status"] == "PASS" and all(semantics["source_invariants"].values()) and len(semantics["rendered_parent_text"]) == 11 and semantics["direction_and_endpoint_manual_review"] == "PASS", semantics["source_invariants"])
check("build_logs_pass", build_logs["status"] == "PASS" and len(build_logs["rows"]) == 2 and all(row["status"] == "PASS" and not row["hard_pattern_hits"] and row["output_written_one_page"] for row in build_logs["rows"]), build_logs)

with fitz.open(PAGE_PDF) as document:
    page_pdf_ok = document.page_count == 1 and len(document[0].get_drawings()) == 21 and document[0].get_label() == "685"
with fitz.open(STANDALONE_PDF) as document:
    standalone_pdf_ok = document.page_count == 1 and len(document[0].get_drawings()) == 21
check("compiled_pdfs_openable", page_pdf_ok and standalone_pdf_ok, {"page": page_pdf_ok, "standalone": standalone_pdf_ok})

check("matrix_local_route", matrix["LOCAL_SA2_GATE_PASS"] is True and matrix["OFFICIAL_FULLBOOK_CANDIDATE_EVALUATED"] is False and matrix["FRESH_SA1_REQUIRED"] is True and matrix["route"] == ROUTE and not matrix["hard_failures"] and matrix["OVERLAP_PIXEL_COUNT"] == 0 and matrix["CLIP_PIXEL_COUNT"] == 0, {"route": matrix["route"], "local": matrix["LOCAL_SA2_GATE_PASS"], "official_evaluated": matrix["OFFICIAL_FULLBOOK_CANDIDATE_EVALUATED"]})
check("matrix_all_gates", all(matrix[key] is True for key in ("SOURCE_FONT_PASS", "PIXEL_HEIGHT_PASS", "LOW_PROFILE_REFERENCE_PASS", "SAME_CLASS_RATIO_PASS", "ROLE_RATIO_PASS", "FONT_VISUAL_HARMONY_PASS", "MASK_PURITY_COMPLETENESS_PASS", "DENOMINATOR_PASS", "PAIR_DENOMINATOR_PASS", "CLEARANCE_PASS", "TEXT_TO_IMAGE_EDGE_PASS", "FINAL_EVIDENCE_CROP_PASS", "CANDIDATE_PAGE_PDF_COMPLETE", "OLD_EVIDENCE_CROP_REJECTED", "STANDALONE_PAGE_CONSISTENCY_PASS", "TEXT_AND_MATH_SEMANTICS_PASS", "GRAYSCALE_PASS", "PAGE_INTEGRATION_LOCAL_WRAPPER_PASS", "MANUAL_LEDGER_COMPLETE")), "all local gate booleans true")
check("result_exact", (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip() == ROUTE, (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip())
check("summary_final_route", summary["foreground_object_denominator_N"] == 116 and summary["unordered_pair_denominator_C_N_2"] == 6670 and summary["expected_C_N_2"] == 6670 and summary["manual_state"] == "COMPLETE_BY_SA2" and summary["final_route"] == ROUTE and summary["final_foreground_margins_px"] == {"left": 10, "top": 10, "right": 37, "bottom": 11}, {"N": summary["foreground_object_denominator_N"], "pairs": summary["unordered_pair_denominator_C_N_2"], "route": summary["final_route"]})

required_root = [
    "candidate_identity.json", "full_page_200dpi.png", "figure_crop_300dpi.png",
    "standalone_300dpi.png", "grayscale_300dpi.png", "after_font_audit.csv",
    "after_pixel_measurements.csv", "after_overlap_report.csv",
    "after_text_measurement_overlay_300dpi.png", "after_visual_acceptance.md",
    "after_overlap_adjudication.md", "after_crop_safety.md",
    "after_text_and_math_semantics.md", "after_model_route.md",
    "denominator_and_machine_summary.json", "SA2_REPAIR_REPORT.md",
    "SA2_HANDOFF.json", "RESULT.txt",
]
check("required_root_files", all((ROOT / name).is_file() for name in required_root), [name for name in required_root if not (ROOT / name).is_file()])
check("root_render_copies_exact", all((ROOT / name).read_bytes() == (ROOT / "renders" / name).read_bytes() for name in ("full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png", "after_text_measurement_overlay_300dpi.png")), "all five root/render copies byte-identical")
check("report_route_boundary", ROUTE in (ROOT / "SA2_REPAIR_REPORT.md").read_text(encoding="utf-8") and "does not claim `A_LOCAL_PASS`" in (ROOT / "SA2_REPAIR_REPORT.md").read_text(encoding="utf-8"), "report states exact local route and scope limit")

all_view_paths: list[str] = []
for key in (
    "global_views", "glyph_native_1x_contact_sheets", "glyph_nearest_8x_contact_sheets",
    "graphic_native_1x_contact_sheets", "graphic_nearest_8x_contact_sheets",
    "critical_pair_native_1x_contacts", "critical_pair_nearest_8x_cards", "trial_views_opened",
):
    all_view_paths.extend(views[key])
check("view_attestation_counts", views["status"] == "COMPLETE" and len(views["global_views"]) == 5 and len(views["glyph_native_1x_contact_sheets"]) == 24 and len(views["glyph_nearest_8x_contact_sheets"]) == 24 and len(views["glyph_object_coverage"]) == 95 and len(views["graphic_native_1x_contact_sheets"]) == 6 and len(views["graphic_nearest_8x_contact_sheets"]) == 6 and len(views["graphic_object_coverage"]) == 21 and set(views["critical_pair_ids"]) == EXPECTED_CRITICAL and len(views["critical_pair_native_1x_contacts"]) == 17 and len(views["critical_pair_nearest_8x_cards"]) == 17, {key: len(views[key]) if isinstance(views[key], list) else views[key] for key in views if key != "reviewer"})
check("attested_views_exist", all((ROOT / relative).is_file() for relative in all_view_paths), [relative for relative in all_view_paths if not (ROOT / relative).is_file()])
check("contact_sheet_counts", len(list((ROOT / "contacts").glob("glyph_native_1x_sheet_*.png"))) == 24 and len(list((ROOT / "contacts").glob("glyph_sheet_*.png"))) == 24 and len(list((ROOT / "contacts").glob("graphic_native_1x_sheet_*.png"))) == 6 and len(list((ROOT / "contacts").glob("graphic_sheet_*.png"))) == 6, {"glyph_native": len(list((ROOT / "contacts").glob("glyph_native_1x_sheet_*.png"))), "glyph_8x": len(list((ROOT / "contacts").glob("glyph_sheet_*.png"))), "graphic_native": len(list((ROOT / "contacts").glob("graphic_native_1x_sheet_*.png"))), "graphic_8x": len(list((ROOT / "contacts").glob("graphic_sheet_*.png")))})

expected_critical_files = {
    f"{pair_id}_{suffix}.png"
    for pair_id in EXPECTED_CRITICAL
    for suffix in ("raw_1x", "overlay_1x", "A_mask_1x", "B_mask_1x", "intersection_1x", "card_8x", "native_1x_contact")
}
actual_critical_files = {path.name for path in (ROOT / "critical").glob("*.png")}
check("critical_directory_exact", actual_critical_files == expected_critical_files, {"expected": len(expected_critical_files), "actual": len(actual_critical_files), "extra": sorted(actual_critical_files - expected_critical_files), "missing": sorted(expected_critical_files - actual_critical_files)})

png_refs: set[Path] = set(ROOT / relative for relative in all_view_paths)
for row in glyphs:
    png_refs.update(ROOT / row[key] for key in ("original_1x", "overlay_1x", "mask_only_1x", "card_8x"))
for row in graphics:
    png_refs.update(ROOT / row[key] for key in ("original_1x", "overlay_1x", "mask_only_1x", "card_8x"))
for row in pairs:
    if row["critical_files"]:
        png_refs.update(ROOT / relative for relative in row["critical_files"].split("|"))
png_refs.update(ROOT / name for name in required_root if name.endswith(".png"))

bad_png: list[str] = []
for path in sorted(png_refs):
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as error:
        bad_png.append(f"{path.relative_to(ROOT)}: {error}")
check("referenced_png_openable", not bad_png, {"count": len(png_refs), "bad": bad_png})
check("render_dimensions", Image.open(ROOT / "renders" / "full_page_200dpi.png").size == (1654, 2339) and Image.open(ROOT / "renders" / "figure_crop_300dpi.png").size == (1935, 604) and Image.open(ROOT / "renders" / "standalone_300dpi.png").size == (1935, 604) and Image.open(ROOT / "renders" / "grayscale_300dpi.png").size == (1935, 604), {name: Image.open(ROOT / "renders" / name).size for name in ("full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png")})
check("safe_relative_names", all(":" not in path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()), "no colon/ADS-style relative names")

result = {
    "figure_uid": "FIG-P654-01",
    "handoff_id": HANDOFF,
    "route": ROUTE,
    "terminal_check": "PASS" if not failures else "FAIL",
    "failure_count": len(failures),
    "failures": failures,
    "checks": checks,
    "referenced_png_opened": len(png_refs),
    "seal_order_next": "finalize report with terminal result, then MANIFEST.json, then WRITE_STOPPED absolute last",
}
SEAL.mkdir(exist_ok=True)
(SEAL / "terminal_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
(REPORTS / "terminal_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"terminal_check": result["terminal_check"], "failure_count": len(failures), "check_count": len(checks), "png_opened": len(png_refs)}, ensure_ascii=False))
if failures:
    raise SystemExit(1)
