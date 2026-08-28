"""Final R8 terminal: verify evidence closure without changing figure findings.

The terminal distinguishes evidence-integrity PASS from the independent figure
gate result.  In this audit the evidence closes, while nine native H-gate
failures route the figure to SA2.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent / "PATH_ISOLATED_R8_CID_KNOCKOUT_AUTHORITY_SAFE"
IDENTITY_HASH = "3e8d102b15d1d40e9d08d8426b0cd7e849eb0cdb81625385c4e591a25f5cd4dd"
EXPECTED_HARD_FAILURES = [
    "T030:G01", "T037:G01", "T039:G01", "T045:G03", "T046:G14",
    "T046:G28", "T046:G37", "T047:G06", "T047:G28",
]
REQUIRED_MASK_KINDS = {
    "RAW_GLYPH", "PDF_REPLAY_SHAPE_SUPPORT", "OFFICIAL_FINAL_VISIBLE_TARGET",
    "COLOUR_RAY_CANDIDATE", "COLOUR_RAY_NONPATH", "COMPLETENESS_MISSING",
    "FOREIGN_PIXEL", "REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE",
}
VIEWS = {"FULL_PAGE_200DPI", "FIGURE_CROP_300DPI", "STANDALONE_300DPI", "GRAYSCALE_300DPI"}


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_int(value: str) -> int:
    return int(float(value))


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def no_unresolved(row: dict[str, str]) -> bool:
    return all("PENDING" not in value.upper() and "UNKNOWN" not in value.upper() for value in row.values())


def ads_paths(root: Path) -> tuple[list[str], str | None]:
    """Use the NTFS stream provider; a normal :$DATA stream is not an ADS."""
    if os.name != "nt":
        return [], None
    literal = str(root).replace("'", "''")
    command = (
        "$ErrorActionPreference='Stop'; "
        "$bad=[System.Collections.Generic.List[string]]::new(); "
        f"Get-ChildItem -LiteralPath '{literal}' -Recurse -File | ForEach-Object {{ "
        "Get-Item -LiteralPath $_.FullName -Stream * | "
        "Where-Object {$_.Stream -ne ':$DATA'} | "
        "ForEach-Object {$bad.Add(($_.FileName + '|' + $_.Stream))} "
        "}; $bad"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except Exception as exc:  # terminal must disclose if ADS cannot be examined
        return [], f"ADS scan launch failed: {exc}"
    if result.returncode:
        return [], f"ADS scan failed ({result.returncode}): {result.stderr.strip()}"
    return [line.strip() for line in result.stdout.splitlines() if line.strip()], None


def main() -> int:
    errors: list[str] = []
    checks: dict[str, object] = {}

    def require(condition: bool, label: str) -> None:
        if not condition:
            errors.append(label)

    # Required files and ordinary non-empty files first.
    required = [
        "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv",
        "after_text_measurement_overlay_300dpi.png", "after_visual_acceptance.md",
        "all_foreground_pairs.csv", "required_relations.csv", "semantic_text_inventory.csv",
        "final_visible_graphics_inventory.csv", "glyph_shape_mapping.csv",
        "glyph_file_manifest.csv", "glyph_safe_filename_map.csv",
        "glyph_mask_ownership.csv",
        "glyph_background_and_completeness_ledger.csv", "glyph_mask_contamination_report.csv",
        "glyph_pdf_content_replay_manifest.csv", "glyph_final_visibility_knockout_manifest.csv",
        "glyph_colour_ray_nonpath_attribution.csv", "glyph_replay_integer_lattice_quantization_ledger.csv",
        "glyph_subthreshold_aa_drift_ledger.csv", "glyph_manual_review.csv",
        "manual_glyph_review_completion.csv", "glyph_contact_sheet_coverage.csv",
        "glyph_manual_review_identity.json", "manual_glyph_review_join_manifest.json",
        "contact_sheet_manual_sync_manifest.json", "manual_visual_harmony_ledger.csv",
        "manual_visual_harmony_completion.csv", "manual_visual_harmony_join_manifest.json",
        "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png",
        "grayscale_300dpi.png", "math_semantic_review.md",
    ]
    missing_required = [name for name in required if not (ROOT / name).is_file() or (ROOT / name).stat().st_size == 0]
    require(not missing_required, f"missing/zero required artifacts: {missing_required}")
    all_files = [path for path in ROOT.rglob("*") if path.is_file()]
    zero_files = [str(path.relative_to(ROOT)) for path in all_files if path.stat().st_size == 0]
    require(not zero_files, f"zero-byte evidence files: {zero_files[:20]}")
    checks["ordinary_file_count"] = len(all_files)
    checks["zero_byte_file_count"] = len(zero_files)

    # Identity and per-glyph reviewer closure.
    identity = json.loads((ROOT / "glyph_manual_review_identity.json").read_text(encoding="utf-8"))
    require(identity.get("evidence_identity_sha256") == IDENTITY_HASH, "identity hash mismatch")
    require(identity.get("status") == "REVIEW_COMPLETE_EXPLICIT_193_GLYPH_8X_RECORDS", "identity review status not complete")
    payload = identity.get("identity_payload", [])
    require(len(payload) == 193 and len({row["glyph_id"] for row in payload}) == 193, "identity payload is not 193 unique glyphs")
    glyph_review = read_csv("glyph_manual_review.csv")
    glyph_manual = read_csv("manual_glyph_review_completion.csv")
    coverage = read_csv("glyph_contact_sheet_coverage.csv")
    require(len(glyph_review) == len(glyph_manual) == len(coverage) == 193, "glyph review/coverage row count mismatch")
    review_ids = {row["GLYPH_ID"] for row in glyph_review}
    require(len(review_ids) == 193 and review_ids == {row["GLYPH_ID"] for row in glyph_manual} == {row["GLYPH_ID"] for row in coverage}, "glyph review IDs mismatch")
    require(all(row["EVIDENCE_IDENTITY_SHA256"] == IDENTITY_HASH for row in glyph_review), "glyph review identity join mismatch")
    for row in glyph_review:
        require(no_unresolved(row), f"unresolved glyph review: {row['GLYPH_ID']}")
        require(all(row[field] == "PASS" for field in ("ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE", "DECISION")), f"manual glyph review fail: {row['GLYPH_ID']}")
        require(row["MISSING_STROKE_PX"] == "0" and row["FOREIGN_PIXEL_PX"] == "0", f"manual glyph mask nonzero: {row['GLYPH_ID']}")
    for row in coverage:
        require(row["MANUAL_8X_REVIEW"] == "PASS" and no_unresolved(row), f"contact coverage not closed: {row['GLYPH_ID']}")
        require((ROOT / "glyph_contact_sheets" / row["SHEET"]).is_file(), f"missing contact sheet: {row['SHEET']}")
    require(len({row["SHEET"] for row in coverage}) == 14, "contact sheet coverage does not span 14 sheets")
    checks["glyph_manual_rows"] = len(glyph_review)
    checks["glyph_contact_sheet_rows"] = len(coverage)
    checks["glyph_contact_sheet_count"] = len({row["SHEET"] for row in coverage})

    # Four-view reviewer closure is entirely reviewer-entered, then join-checked.
    visual = read_csv("manual_visual_harmony_ledger.csv")
    visual_manual = read_csv("manual_visual_harmony_completion.csv")
    visual_keys = {(row["VIEW_ID"], row["ELEMENT_ID"], row["SCRIPT_CLASS"]) for row in visual}
    manual_visual_keys = {(row["VIEW_ID"], row["ELEMENT_ID"], row["SCRIPT_CLASS"]) for row in visual_manual}
    require(len(visual) == len(visual_manual) == 192 and len(visual_keys) == len(manual_visual_keys) == 192, "visual ledger row/key count mismatch")
    require(visual_keys == manual_visual_keys, "visual reviewer/template keys mismatch")
    require({row["VIEW_ID"] for row in visual} == VIEWS, "four-view set mismatch")
    for view in VIEWS:
        require(sum(row["VIEW_ID"] == view for row in visual) == 48, f"not 48 visual rows for {view}")
    for row in visual:
        require(row["EVIDENCE_IDENTITY_SHA256"] == IDENTITY_HASH and no_unresolved(row), f"unresolved visual ledger: {row['VIEW_ID']}:{row['ELEMENT_ID']}:{row['SCRIPT_CLASS']}")
        require(row["VIEW_OPENED"] == "PASS", f"view not opened: {row['VIEW_ID']}:{row['ELEMENT_ID']}:{row['SCRIPT_CLASS']}")
        require(all(row[field] in {"PASS", "FAIL"} for field in ("FONT_SIZE_HARMONY", "WEIGHT_FAMILY_HARMONY", "BASELINE_ALIGNMENT", "GRAY_HIERARCHY", "PAGE_INTEGRATION", "CROWDING_OR_INTRUSION", "CROSS_PANEL_CONSISTENCY", "DECISION")), f"invalid visual judgement: {row['VIEW_ID']}:{row['ELEMENT_ID']}")
    visual_fail_rows = [row for row in visual if row["DECISION"] == "FAIL"]
    visual_font_fail_groups = {(row["ELEMENT_ID"], row["SCRIPT_CLASS"]) for row in visual if row["FONT_SIZE_HARMONY"] == "FAIL"}
    require(len(visual_fail_rows) == 24, f"unexpected visual FAIL count {len(visual_fail_rows)}")
    checks["visual_ledger_rows"] = len(visual)
    checks["visual_fail_rows"] = len(visual_fail_rows)
    checks["font_visual_harmony_pass"] = not bool(visual_font_fail_groups)

    # SVG/PDF character mapping and CID final-visible closure.
    mapping = read_csv("glyph_shape_mapping.csv")
    background = read_csv("glyph_background_and_completeness_ledger.csv")
    final_manifest = read_csv("glyph_final_visibility_knockout_manifest.csv")
    replay = read_csv("glyph_pdf_content_replay_manifest.csv")
    ownership = read_csv("glyph_mask_ownership.csv")
    contamination = read_csv("glyph_mask_contamination_report.csv")
    mapping_ids = {row["GLYPH_ID"] for row in mapping}
    require(len(mapping) == len(background) == len(final_manifest) == len(replay) == 193, "CID mapping ledger count mismatch")
    require(len(ownership) == 193 and len({row["GLYPH_ID"] for row in ownership}) == 193, "same-parent ownership ledger count mismatch")
    require(len(contamination) == 193 * 21, "glyph/foreground-graphic contamination ledger count mismatch")
    require(mapping_ids == review_ids == {row["GLYPH_ID"] for row in background} == {row["GLYPH_ID"] for row in final_manifest} == {row["GLYPH_ID"] for row in replay}, "CID mapping/review ID mismatch")
    core_zero_mapping = (
        "RAW_EFFECTIVE_TO_ISOLATED_CID_ALPHA_MISSING_PIXELS", "OFFICIAL_TARGET_MASK_FOREIGN_PIXELS",
        "REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE_PIXELS", "BASELINE_DIRECT_UNSAFE_MISMATCH_PIXELS",
        "BASELINE_DIRECT_EFFECTIVE_XOR_PIXELS", "RAW_EFFECTIVE_OUTSIDE_ISOLATED_CID_ALPHA_PIXELS",
        "BASELINE_EFFECTIVE_OUTSIDE_ISOLATED_CID_ALPHA_PIXELS", "UNEXPLAINED_COLOUR_RAY_NONPATH_PIXELS",
    )
    for row in mapping:
        require(row["MAPPING_STATUS"] == "PASS", f"mapping fail: {row['GLYPH_ID']}")
        require(all(is_true(row[field]) for field in ("PDF_REPLAY_MAPPING_PASS", "PDF_TEXTTRACE_MAPPING_PASS", "PDF_REPLAY_GRID_PASS", "PDF_SVG_FILL_OPACITY_CROSSCHECK", "OFFICIAL_FINAL_VISIBLE_GRID_PASS", "PDF_REPLAY_ISOLATION_PASS", "QUANTIZATION_BOUNDARY_EXPLANATION_PASS")), f"mapping source closure fail: {row['GLYPH_ID']}")
        require(all(as_int(row[field]) == 0 for field in core_zero_mapping), f"mapping core mask closure nonzero: {row['GLYPH_ID']}")
        require(row["PDF_CID_HEX"] and row["PDF_CONTENT_OP_INDEX"] and row["PDF_TEXTTRACE_SEQNO"], f"missing CID/text trace: {row['GLYPH_ID']}")
    for row in background:
        require(row["COMPLETENESS_STATUS"] == "PASS" and is_true(row["QUANTIZATION_BOUNDARY_EXPLANATION_PASS"]) and is_true(row["PDF_SVG_FILL_OPACITY_CROSSCHECK"]), f"background/completeness status fail: {row['GLYPH_ID']}")
        require(all(as_int(row[field]) == 0 for field in core_zero_mapping), f"background core closure nonzero: {row['GLYPH_ID']}")
    for row in final_manifest:
        require(row["STATUS"] == "PASS" and row["BASELINE_RENDERED_GRID"] == row["KNOCKOUT_RENDERED_GRID"], f"final knockout grid/status fail: {row['GLYPH_ID']}")
        require(all(as_int(row[field]) == 0 for field in ("BASELINE_DIRECT_UNSAFE_MISMATCH_PIXELS", "BASELINE_DIRECT_EFFECTIVE_XOR_PIXELS", "RAW_EFFECTIVE_OUTSIDE_ISOLATED_ALPHA_PIXELS", "BASELINE_EFFECTIVE_OUTSIDE_ISOLATED_ALPHA_PIXELS")), f"final knockout closure nonzero: {row['GLYPH_ID']}")
    for row in replay:
        require(row["REPLAY_STATUS"] == "PASS" and row["PDF_SCOPE_NON_TEXT_PAINT_COUNT"] == "0", f"CID no-paint replay fail: {row['GLYPH_ID']}")
        require(all(row[field] for field in ("PDF_FONT_RESOURCE", "PDF_CID_HEX", "PDF_CTM", "PDF_TEXT_MATRIX", "PDF_FILL_RGB_0_1", "PDF_FILL_OPACITY")), f"CID replay source-state missing: {row['GLYPH_ID']}")
    for row in ownership:
        require(row["OWNERSHIP_STATUS"] == "PASS" and as_int(row["PIXELS_REMOVED_TO_LATER_SVG_USE"]) == 0, f"same-parent glyph ownership failure: {row['GLYPH_ID']}")
    for row in contamination:
        require(is_true(row["CONTAMINATION_PASS"]) and as_int(row["FINAL_VISIBLE_RAW_MASK_INTERSECTION_PX"]) == 0, f"glyph/graphic contamination: {row['GLYPH_ID']}:{row['GRAPHIC_ID']}")
    checks["mapping_rows"] = len(mapping)
    checks["raw_effective_missing_px"] = sum(as_int(row["RAW_EFFECTIVE_TO_ISOLATED_CID_ALPHA_MISSING_PIXELS"]) for row in mapping)
    checks["target_foreign_px"] = sum(as_int(row["OFFICIAL_TARGET_MASK_FOREIGN_PIXELS"]) for row in mapping)
    checks["later_paint_occluded_px"] = sum(as_int(row["REAL_LATER_PAINT_OCCLUDED_RAW_EFFECTIVE_PIXELS"]) for row in mapping)
    checks["baseline_direct_effective_xor_px"] = sum(as_int(row["BASELINE_DIRECT_EFFECTIVE_XOR_PIXELS"]) for row in mapping)
    checks["same_parent_glyph_mask_overlap_px"] = sum(as_int(row["PIXELS_REMOVED_TO_LATER_SVG_USE"]) for row in ownership)
    checks["glyph_graphic_contamination_rows"] = len(contamination)
    checks["glyph_graphic_contamination_px"] = sum(as_int(row["FINAL_VISIBLE_RAW_MASK_INTERSECTION_PX"]) for row in contamination)

    # Quantization, subthreshold, and all claimed non-path pixels remain explanatory only.
    quant = read_csv("glyph_replay_integer_lattice_quantization_ledger.csv")
    subthreshold = read_csv("glyph_subthreshold_aa_drift_ledger.csv")
    nonpath = read_csv("glyph_colour_ray_nonpath_attribution.csv")
    require(len(quant) == 148 and all(is_true(row["EXPLANATION_PASS"]) for row in quant), "quantization ledger is not 148 explained rows")
    t020 = [row for row in quant if row["GLYPH_ID"] in {"T020:G01", "T020:G02"} and row["DIAGNOSTIC_CLASS"] == "TRANSPARENT_ALPHA_OVERPREDICT"]
    require(len(t020) == 4 and all(row["REPLAY_ALPHA_0_255"] == "23" and row["BASELINE_EFFECTIVE_GE20"] == row["DIRECT_EFFECTIVE_GE20"] == "False" for row in t020), "T020 four alpha=23 diagnostic rows not closed")
    require(len(subthreshold) == 5 and all(row["DIRECT_EFFECTIVE_GE20"] == row["BASELINE_EFFECTIVE_GE20"] == "False" and row["EFFECTIVE_SUPPORT_XOR_DIRECT_BASELINE"] == "False" for row in subthreshold), "subthreshold AA ledger not safely non-gating")
    require(len(nonpath) == 88 and all(row["DISPOSITION"] == "ATTRIBUTED_NON_TARGET_PIXEL" and row["OWNER_PHASE"] and row["PAINT_ORDER_PROOF"] and row["TARGET_ALPHA_GE20"] == "False" for row in nonpath), "nonpath owner/paint order ledger does not close")
    checks["quantization_rows"] = len(quant)
    checks["t020_alpha23_overpredict_rows"] = len(t020)
    checks["subthreshold_aa_rows"] = len(subthreshold)
    checks["nonpath_owner_rows"] = len(nonpath)

    # Every raw glyph / support mask is independently name-safe, ordinary, openable,
    # dimension-consistent, hash-consistent, and represented exactly once in the manifest.
    file_manifest = read_csv("glyph_file_manifest.csv")
    safe_map = read_csv("glyph_safe_filename_map.csv")
    require(len(file_manifest) == 1544 and len(safe_map) == 193, "file-manifest/safe-map row count mismatch")
    require(len({(row["GLYPH_ID"], row["MASK_KIND"]) for row in file_manifest}) == 1544, "duplicate glyph mask manifest key")
    require({row["MASK_KIND"] for row in file_manifest} == REQUIRED_MASK_KINDS, "mask-kind inventory mismatch")
    require(all(sum(row["MASK_KIND"] == kind for row in file_manifest) == 193 for kind in REQUIRED_MASK_KINDS), "mask kind does not have 193 files")
    require({row["GLYPH_ID"] for row in safe_map} == review_ids and all(is_true(row["WINDOWS_PORTABLE_PASS"]) for row in safe_map), "safe map mismatch")
    invalid_name = re.compile(r'[<>:"/\\|?*]')
    for row in file_manifest:
        relative = row["RELATIVE_PATH"]
        path = ROOT / relative
        require(is_true(row["SAFE_FILENAME_PASS"]) and is_true(row["COLON_OR_ADS_RISK_PASS"]) and is_true(row["ORDINARY_ENUMERATED_EXACTLY_ONCE"]) and is_true(row["EXISTS"]) and is_true(row["PNG_OPEN_AND_SIZE_PASS"]) and is_true(row["PASS"]), f"manifest status fail: {row['GLYPH_ID']} {row['MASK_KIND']}")
        require(not invalid_name.search(row["SAFE_FILENAME"]) and ":" not in relative, f"unsafe glyph filename: {relative}")
        require(path.is_file(), f"manifest path absent: {relative}")
        if path.is_file():
            try:
                with Image.open(path) as image:
                    image.load()
                    actual_size = f"{image.width}x{image.height}"
            except Exception as exc:
                errors.append(f"PNG open error {relative}: {exc}")
                actual_size = "ERROR"
            require(actual_size == row["EXPECTED_PNG_SIZE"] == row["ACTUAL_PNG_SIZE"], f"PNG dimensions mismatch: {relative}")
            require(sha256(path) == row["SHA256"], f"PNG SHA mismatch: {relative}")
    for row in safe_map:
        safe = row["SAFE_FILENAME"]
        require(safe == row["GLYPH_ID"].replace(":", "_") + ".png", f"unsafe filename mapping mismatch: {row['GLYPH_ID']}")
        require((ROOT / row["RAW_MASK_RELATIVE_PATH"]).is_file() and (ROOT / row["SHAPE_SUPPORT_RELATIVE_PATH"]).is_file(), f"safe-map referenced mask absent: {row['GLYPH_ID']}")
    require(sum(1 for _ in (ROOT / "masks" / "glyphs").glob("*.png")) == 193, "ordinary raw-glyph PNG count !=193")
    require(sum(1 for _ in (ROOT / "masks" / "glyph_shape_support").glob("*.png")) == 193, "ordinary support PNG count !=193")
    payload_by_id = {row["glyph_id"]: row for row in payload}
    for glyph_id, item in payload_by_id.items():
        safe = glyph_id.replace(":", "_") + ".png"
        require(sha256(ROOT / "masks" / "glyphs" / safe) == item["raw_mask_sha256"], f"identity raw hash mismatch: {glyph_id}")
        require(sha256(ROOT / "masks" / "glyph_shape_support" / safe) == item["shape_support_sha256"], f"identity support hash mismatch: {glyph_id}")
        require(sha256(ROOT / "masks" / "glyph_final_visible_target" / safe) == item["final_visible_sha256"], f"identity final-visible hash mismatch: {glyph_id}")
    ads, ads_error = ads_paths(ROOT)
    require(ads_error is None, ads_error or "ADS scan error")
    require(not ads, f"NTFS alternate streams found: {ads[:20]}")
    checks["glyph_file_manifest_rows"] = len(file_manifest)
    checks["safe_filename_rows"] = len(safe_map)
    checks["raw_glyph_png_count"] = sum(1 for _ in (ROOT / "masks" / "glyphs").glob("*.png"))
    checks["shape_support_png_count"] = sum(1 for _ in (ROOT / "masks" / "glyph_shape_support").glob("*.png"))
    checks["ads_stream_count"] = len(ads)
    checks["ads_scan_error"] = ads_error

    # Pair/relation and typography measurements.
    semantic = read_csv("semantic_text_inventory.csv")
    graphics = read_csv("final_visible_graphics_inventory.csv")
    relations = read_csv("required_relations.csv")
    pairs = read_csv("all_foreground_pairs.csv")
    overlap = read_csv("after_overlap_report.csv")
    font = read_csv("after_font_audit.csv")
    pixels = read_csv("after_pixel_measurements.csv")
    require(len(semantic) == 41 and all(is_true(row["NONEMPTY"]) for row in semantic), "semantic inventory not 41 nonempty elements")
    require(len(graphics) == 25 and all(as_int(row["RAW_MASK_PIXELS"]) > 0 for row in graphics), "graphics inventory is not 25 nonempty final-visible masks")
    require(len(relations) == len(overlap) == 1681 and all(row["status"] == "PASS" for row in relations) and all(row["status"] == "PASS" for row in overlap), "required relation status/count failure")
    require(len(pairs) == 1891 and all(row["status"] == "PASS" for row in pairs), "all foreground pair status/count failure")
    foreground_graphics = [row for row in graphics if is_true(row["FOREGROUND"])]
    require(len(foreground_graphics) == 21, "foreground graphic count is not 21")
    foreground_object_count = len(semantic) + len(foreground_graphics)
    require(len(pairs) == foreground_object_count * (foreground_object_count - 1) // 2, "all pair count does not equal nC2")
    require(len(font) == 47 and all(is_true(row["FONT_PASS"]) for row in font), "font audit failure")
    glyph_hard = [row for row in pixels if row["AUDIT_LEVEL"] == "GLYPH_OR_KEY_SUBSTRING" and row["PASS_FAIL"] == "FAIL"]
    semantic_hard = [row for row in pixels if row["AUDIT_LEVEL"] == "SEMANTIC_ELEMENT" and row["PASS_FAIL"] == "FAIL"]
    hard_ids = [row["ELEMENT_ID"] for row in glyph_hard]
    require(hard_ids == EXPECTED_HARD_FAILURES, f"hard failure ID set/order mismatch: {hard_ids}")
    require(len(semantic_hard) == 6, f"semantic hard failure count mismatch: {len(semantic_hard)}")
    require(visual_font_fail_groups == {(row["ELEMENT_ID"].split(":", 1)[0], row["SCRIPT_CLASS"]) for row in semantic_hard}, "manual visual / semantic H-fail groups mismatch")
    require(all((ROOT / "ROIs" / f"{glyph_id.replace(':', '_')}_native_1x.png").is_file() and (ROOT / "ROIs" / f"{glyph_id.replace(':', '_')}_8x_nearest.png").is_file() for glyph_id in hard_ids), "missing native/8x ROI for hard pixel failure")
    checks["semantic_text_elements"] = len(semantic)
    checks["final_visible_graphics"] = len(graphics)
    checks["foreground_objects"] = foreground_object_count
    checks["all_foreground_pairs"] = len(pairs)
    checks["required_relations"] = len(relations)
    checks["font_fail_count"] = sum(not is_true(row["FONT_PASS"]) for row in font)
    checks["pixel_fail_count"] = len(glyph_hard)
    checks["semantic_pixel_fail_count"] = len(semantic_hard)
    checks["hard_failure_ids"] = hard_ids
    checks["min_hard_failure_h_ink_px"] = min(float(row["H_INK_PX"]) for row in glyph_hard)

    # Targeted final artifacts must contain no unresolved status token.
    final_text_artifacts = [
        "glyph_manual_review.csv", "manual_glyph_review_completion.csv", "glyph_contact_sheet_coverage.csv",
        "glyph_manual_review_identity.json", "manual_glyph_review_join_manifest.json", "contact_sheet_manual_sync_manifest.json",
        "manual_visual_harmony_ledger.csv", "manual_visual_harmony_completion.csv", "manual_visual_harmony_join_manifest.json",
        "after_visual_acceptance.md", "math_semantic_review.md", "effective_foreground_quantization_protocol.md",
    ]
    unresolved_hits: list[str] = []
    for name in final_text_artifacts:
        text = (ROOT / name).read_text(encoding="utf-8-sig")
        if re.search(r"\b(?:PENDING|UNKNOWN)\b", text, flags=re.IGNORECASE):
            unresolved_hits.append(name)
    require(not unresolved_hits, f"unresolved token in final artifact: {unresolved_hits}")
    checks["unresolved_final_artifact_count"] = len(unresolved_hits)

    # The failure CSV is a small immutable-friendly handoff, copied only from the
    # authoritative child rows instead of synthesized from a visual decision.
    failure_fields = ["ELEMENT_ID", "PARENT_ID", "ROLE", "SCRIPT_CLASS", "TEXT_SAMPLE", "H_INK_PX", "PIXEL_THRESHOLD_PX", "PASS_FAIL", "REASON"]
    with (ROOT / "final_hard_pixel_failure_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=failure_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(glyph_hard)

    terminal_ok = not errors
    terminal = {
        "schema": "FIG_P634_01_R8_FINAL_MACHINE_TERMINAL_V1",
        "evidence_identity_sha256": IDENTITY_HASH,
        "official_pdf_anchor": "main_full.pdf physical=682 printed=669 Figure=33.3 native=2481x3508@300dpi",
        "evidence_integrity_result": "PASS" if terminal_ok else "FAIL",
        "figure_gate_result": "FAIL",
        "routing": "FAIL_TO_SA2",
        "checks": checks,
        "errors": errors,
        "conclusion_consistency": {
            "machine_mapping_manual_glyph_join_pass": terminal_ok,
            "manual_glyph_mask_review_pass": True,
            "manual_visual_font_harmony_pass": False,
            "hard_pixel_gate_pass": False,
            "final_result": "FAIL_TO_SA2",
        },
    }
    (ROOT / "machine_terminal_integrity.json").write_text(json.dumps(terminal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Replace the preliminary construction snapshot so its old manual-review
    # placeholder cannot be mistaken for a final unresolved status.
    old_machine = json.loads((ROOT / "machine_integrity.json").read_text(encoding="utf-8"))
    old_machine.update({
        "phase": "FINAL_R8_TERMINAL_AFTER_EXPLICIT_MANUAL_REVIEWS",
        "glyph_manual_8x_review_pass": True,
        "glyph_manual_review_pending_count": 0,
        "manual_visual_review_pending_count": 0,
        "manual_visual_harmony_pass": False,
        "manual_visual_fail_count": len(visual_fail_rows),
        "failure_ids": hard_ids,
        "result_at_machine_stage": "FAIL_HARD_NATIVE_PIXEL_GATE",
        "evidence_integrity_result": "PASS" if terminal_ok else "FAIL",
        "terminal_integrity_file": "machine_terminal_integrity.json",
        "final_result": "FAIL_TO_SA2",
    })
    (ROOT / "machine_integrity.json").write_text(json.dumps(old_machine, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown = [
        "# FIG-P634-01 R8 final machine terminal",
        "",
        f"- Evidence-integrity result: **{'PASS' if terminal_ok else 'FAIL'}**.",
        "- Figure gate result: **FAIL → SA2** (nine hard native pixel-height failures; evidence integrity itself is not the failure).",
        f"- Identity: `{IDENTITY_HASH}`; official anchor physical 682 / printed 669 / Figure 33.3 / 2481×3508 @300 dpi.",
        f"- Objects: semantic=41, graphics=25, foreground=62, all unordered pairs=1891, required relations=1681.",
        f"- Glyph closure: 193 mapping/reviewer/contact rows, 14 contact sheets, 1544 manifest masks, 193 ordinary raw PNGs, 193 ordinary support PNGs, ADS={len(ads)}.",
        f"- CID final-visible closure: missing=0, foreign=0, later-occluded=0, B/D effective XOR=0; subthreshold AA rows=5 and T020 alpha=23 diagnostic rows=4 are non-gating and fully ledgered.",
        f"- Manual visual closure: 192 rows/4 views, font-visual harmony=FAIL, explicit visual failure rows=24.",
        f"- Pixel hard failures ({len(hard_ids)}; min H={checks['min_hard_failure_h_ink_px']:.0f}px): " + ", ".join(hard_ids) + ".",
    ]
    if errors:
        markdown += ["", "## Terminal errors", ""] + [f"- {error}" for error in errors]
    (ROOT / "machine_terminal_integrity.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps(terminal, ensure_ascii=False))
    return 0 if terminal_ok else 1


if __name__ == "__main__":
    sys.exit(main())
