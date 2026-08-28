#!/usr/bin/env python3
"""Strict consumer-only validator and write-once sealer for P608 R6A.

The validator consumes explicit per-ID decisions.  It has no mechanism to
invent a review verdict, fill a missing ID, invoke TeX, or alter source files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
FIG_ROOT = ROOT.parent
R6 = FIG_ROOT / "STRICT_R6_SA2_REPAIR_R99_LOCAL_20260825"
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = Path("src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex")
SOURCE = WORKTREE / SOURCE_REL
OFFICIAL_R99 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf")
LOCAL_PDF = ROOT / "local_build_direct_r6" / "local_wrapper_r6_worktree.pdf"
HANDOFF_ID = "A-R99-P608-SA2-NARROW-R6A-EVIDENCE-RESEAL-20260825"
ORIGIN_HANDOFF_ID = "A-R99-P608-SA2-NARROW-20260825"
ROUTE = "SA2=gpt-5.6-sol/max"
RESULT = "LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1"
BASELINE_HEAD = "e392bd8e5f37dfd49f071f7251c281d46bb68ffd"
SOURCE_SHA = "78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05"
LOCAL_PDF_SHA = "638A722CC86D848E6B0FDEB69F08BB6DDBD3F0AD33E262AB36690C2943FD03BB"
OFFICIAL_R99_SHA = "E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6"
EXACT_INSERTION = "  ylabel style={rotate=-90,anchor=east,at={(axis description cs:-0.12,0.5)}},"
FORBIDDEN = ("PEND" + "ING", "UN" + "KNOWN")
ALL_VIEWS = {
    "full_page_200dpi.png",
    "figure_crop_300dpi.png",
    "standalone_300dpi.png",
    "grayscale_300dpi.png",
    "colorblind_protanopia_300dpi.png",
    "colorblind_deuteranopia_300dpi.png",
    "colorblind_tritanopia_300dpi.png",
}
NON_ILLEGAL_CLASSES = {"INTRA_PARENT_TYPOGRAPHY", "MATH_RULE_INTRA_PARENT", "INTENTIONAL_SAME_SERIES"}
FINAL_LEDGERS = (
    "after_font_audit.csv",
    "after_overlap_report.csv",
    "after_pixel_measurements.csv",
    "character_mapping.csv",
    "clip_crop_final.csv",
    "contact_sheet_ledger.csv",
    "critical_pair_review_ledger.csv",
    "drawing_path_inventory.csv",
    "manual_review_ledger.csv",
    "math_rule_ledger.csv",
    "object_ledger.csv",
    "punctuation_calibration.csv",
    "reused_evidence_integrity.csv",
    "role_panel_ledger.csv",
    "semantic_consistency.csv",
    "source_font_coverage.csv",
    "source_scale_control_scan.csv",
    "strict_low_profile_adjudication.csv",
    "visual_view_ledger.csv",
    "peer_calibration/peer_comparison_final_ownership.csv",
)
EXCLUDED = (
    "manual_review_template.csv",
    "critical_pair_review_template.csv",
    "visual_view_template.csv",
    "role_panel_template.csv",
    "metadata/preliminary_machine_summary.json",
    "record_manual_ledgers.py",
    "audit_extract.py",
    "audit_finalize.py",
)
TEXT_EXTENSIONS = {".csv", ".json", ".md", ".txt", ".py", ".tex", ".log", ".aux"}
TERMINAL_OUTPUTS = (
    "MACHINE_TERMINAL_RECALC.json",
    "manifest.json",
    "after_visual_acceptance.md",
    "RESULT.txt",
    "HANDOFF_REPORT.json",
    "WRITE_STOPPED",
)


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValidationError(f"duplicate JSON key: {key}")
        output[key] = value
    return output


def read_json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_pairs)


def read_csv(relative: str) -> list[dict[str, str]]:
    path = ROOT / relative
    require(path.is_file(), f"missing ledger: {relative}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        require(bool(reader.fieldnames), f"missing header: {relative}")
        rows = list(reader)
    require(bool(rows), f"empty ledger: {relative}")
    for index, row in enumerate(rows, 2):
        require(None not in row, f"extra CSV field at {relative}:{index}")
        for key, value in row.items():
            require(value is not None and value.strip() != "", f"blank cell {relative}:{index}:{key}")
            upper = value.upper()
            require(not any(token in upper for token in FORBIDDEN), f"unresolved sentinel {relative}:{index}:{key}")
    return rows


def recursively_closed(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(str(key).strip() != "", f"blank JSON key at {path}")
            recursively_closed(child, f"{path}.{key}")
    elif isinstance(value, list):
        require(bool(value), f"empty JSON list at {path}")
        for index, child in enumerate(value):
            recursively_closed(child, f"{path}[{index}]")
    elif isinstance(value, str):
        require(value.strip() != "", f"blank JSON string at {path}")
        upper = value.upper()
        require(not any(token in upper for token in FORBIDDEN), f"unresolved JSON sentinel at {path}")
    else:
        require(value is not None, f"null JSON value at {path}")


def is_na(value: str) -> bool:
    return value.upper().startswith("N/A") or value in {"INDIVIDUAL", "NOT_EXPOSED_BY_PYMUPDF_DRAWING_API"}


def require_rel(value: str, context: str) -> None:
    for part in value.split(";"):
        item = part.strip()
        if is_na(item):
            continue
        require(not Path(item).is_absolute(), f"evidence reference must be package-relative at {context}: {item}")
        resolved = (ROOT / item).resolve()
        require(str(resolved).lower().startswith(str(ROOT.resolve()).lower() + os.sep.lower()), f"reference escapes package at {context}: {item}")
        require(resolved.is_file(), f"missing evidence reference at {context}: {item}")


def git_output(args: list[str]) -> str:
    completed = subprocess.run(args, cwd=WORKTREE, check=True, capture_output=True, text=True, encoding="utf-8")
    return completed.stdout.strip()


def scan_nondefault_streams() -> int:
    escaped = str(ROOT).replace("'", "''")
    script = (
        f"$files=Get-ChildItem -LiteralPath '{escaped}' -Recurse -File -Force; "
        "$extra=@($files | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * | "
        "Where-Object { $_.Stream -ne ':$DATA' } }); Write-Output $extra.Count"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return int(completed.stdout.strip() or "0")


def ordinary_file_scan() -> dict[str, Any]:
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    files: list[Path] = []
    reparse: list[str] = []
    unsafe: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            reparse.append(rel)
            continue
        if path.is_file():
            files.append(path)
            name = path.name
            stem = name.split(".", 1)[0].upper()
            if name.endswith((" ", ".")) or any(char in name for char in '<>:"/\\|?*') or stem in reserved:
                unsafe.append(rel)
        elif not path.is_dir():
            reparse.append(rel)
    require(not reparse, f"non-ordinary entries: {reparse}")
    require(not unsafe, f"unsafe filenames: {unsafe}")
    return {"files": files, "reparse_count": 0, "unsafe_filename_count": 0}


def scan_text_sentinels() -> list[str]:
    bad: list[str] = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS):
        text = path.read_text(encoding="utf-8", errors="replace").upper()
        if any(token in text for token in FORBIDDEN):
            bad.append(path.relative_to(ROOT).as_posix())
    return bad


def validate_references(
    objects: list[dict[str, str]],
    contacts: list[dict[str, str]],
    pixels: list[dict[str, str]],
    pairs: list[dict[str, str]],
    manual: list[dict[str, str]],
    critical: list[dict[str, str]],
    views: list[dict[str, str]],
    roles: list[dict[str, str]],
    strict: list[dict[str, str]],
) -> int:
    checked = 0
    for row in objects:
        for key in ("FINAL_RAW_MASK", "PRE_RAW_MASK", "NATIVE1X", "NEAREST8X", "CONTACT_SHEET"):
            require_rel(row[key], f"object {row['OBJECT_ID']} {key}")
            checked += 1
    for row in contacts:
        for key in ("SHEET", "NATIVE1X", "NEAREST8X"):
            require_rel(row[key], f"contact {row['OBJECT_ID']} {key}")
            checked += 1
    for row in pixels:
        for key in ("RAW_MASK", "NATIVE1X", "NEAREST8X"):
            require_rel(row[key], f"pixel {row['ELEMENT_ID']} {key}")
            checked += 1
    for row in pairs:
        for key in ("RAW_A", "RAW_B", "NATIVE1X", "NEAREST8X"):
            require_rel(row[key], f"pair {row['PAIR_ID']} {key}")
            checked += 1
    for row in manual:
        for key in ("SHEET", "NATIVE1X", "NEAREST8X", "RAW_MASK"):
            require_rel(row[key], f"manual {row['OBJECT_ID']} {key}")
            checked += 1
    for row in critical:
        for key in ("NATIVE1X", "NEAREST8X"):
            require_rel(row[key], f"critical {row['PAIR_ID']} {key}")
            checked += 1
    for row in views:
        require_rel(row["EVIDENCE_FILE"], f"view {row['VIEW']}")
        checked += 1
    for row in roles:
        require_rel(row["EVIDENCE_FILES"], f"role {row['ROLE_ID']}")
        checked += 1
    for row in strict:
        for key in ("RAW_MASK", "NATIVE1X", "NEAREST8X", "REFERENCE_EVIDENCE"):
            require_rel(row[key], f"strict punctuation {row['ELEMENT_ID']} {key}")
            checked += 1
    for row in read_csv("drawing_path_inventory.csv"):
        require_rel(row["FINAL_MASK"], f"path inventory {row['OBJECT_ID']}")
        checked += 1
    for row in read_csv("math_rule_ledger.csv"):
        for key in ("RAW_MASK", "NATIVE1X", "NEAREST8X"):
            require_rel(row[key], f"math rule {row['RULE_ID']} {key}")
            checked += 1
    for row in read_csv("punctuation_calibration.csv"):
        for key in ("PDF", "PNG_300DPI", "RAW_MASK", "NATIVE1X", "NEAREST8X"):
            require_rel(row[key], f"calibration {row['CALIBRATION_ID']} {key}")
            checked += 1
    for row in read_csv("clip_crop_final.csv"):
        require_rel(row["EVIDENCE"], f"clip/crop {row['CHECK_ID']}")
        checked += 1
    return checked


def validate_package() -> tuple[dict[str, bool], dict[str, Any]]:
    for item in EXCLUDED:
        require(not (ROOT / item).exists(), f"excluded artifact present: {item}")
    require(not list(ROOT.glob("*_template.csv")), "template CSV present")
    require(not scan_text_sentinels(), f"package text sentinel scan failed: {scan_text_sentinels()}")
    for name in FINAL_LEDGERS:
        read_csv(name)

    objects = read_csv("object_ledger.csv")
    pairs = read_csv("after_overlap_report.csv")
    pixels = read_csv("after_pixel_measurements.csv")
    contacts = read_csv("contact_sheet_ledger.csv")
    manual = read_csv("manual_review_ledger.csv")
    critical = read_csv("critical_pair_review_ledger.csv")
    views = read_csv("visual_view_ledger.csv")
    roles = read_csv("role_panel_ledger.csv")
    strict = read_csv("strict_low_profile_adjudication.csv")
    object_ids = [row["OBJECT_ID"] for row in objects]
    object_set = set(object_ids)
    glyph_ids = {row["OBJECT_ID"] for row in objects if row["TYPE"] == "GLYPH"}
    path_ids = object_set - glyph_ids
    require(len(objects) == len(object_set) == 170, "object universe is not 170 unique IDs")
    require(len(glyph_ids) == 112 and len(path_ids) == 58, "glyph/path split is not 112/58")
    require(all(int(row["FINAL_VISIBLE_INK_PX"]) > 0 for row in objects), "empty final object mask")

    expected_pairs = len(objects) * (len(objects) - 1) // 2
    pair_ids = [row["PAIR_ID"] for row in pairs]
    pair_keys = [tuple(sorted((row["OBJECT_A"], row["OBJECT_B"]))) for row in pairs]
    expected_keys = set(itertools.combinations(sorted(object_set), 2))
    require(len(pairs) == expected_pairs == 14365, "pair row count mismatch")
    require(len(pair_ids) == len(set(pair_ids)), "duplicate pair IDs")
    require(len(pair_keys) == len(set(pair_keys)) and set(pair_keys) == expected_keys, "pair denominator is incomplete")
    require(all(row["PAIR_PASS"] == "PASS" for row in pairs), "pair failure exists")
    illegal = [row for row in pairs if row["RELATION_CLASS"] not in NON_ILLEGAL_CLASSES]
    illegal_overlap = sum(int(row["FINAL_VISIBLE_OVERLAP_PX"]) for row in illegal)
    require(illegal_overlap == 0, "illegal final overlap is nonzero")
    critical_expected = {row["PAIR_ID"] for row in pairs if row["CRITICAL"].lower() == "true"}
    require(len(critical_expected) == 13, "critical pair count mismatch")

    pixel_ids = {row["ELEMENT_ID"] for row in pixels}
    derived = {"MATH_OPERATOR_EQ_WARMUP", "MATH_OPERATOR_EQ_RETAINED"}
    require(len(pixels) == 114 and pixel_ids == glyph_ids | derived, "pixel ledger coverage mismatch")
    require(all(row["PASS_FAIL"] == "PASS" for row in pixels), "pixel failure exists")
    strict_ids = {row["ELEMENT_ID"] for row in strict}
    low_ids = {row["ELEMENT_ID"] for row in pixels if row["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION"}
    require(len(strict) == 15 and strict_ids == low_ids, "strict punctuation coverage mismatch")
    for row in strict:
        require(row["VERDICT"] == "PASS", f"strict punctuation failure: {row['ELEMENT_ID']}")
        require(0.92 <= float(row["H_RATIO"]) <= 1.08, f"strict H ratio failure: {row['ELEMENT_ID']}")
        require(0.92 <= float(row["AREA_RATIO"]) <= 1.08, f"strict area ratio failure: {row['ELEMENT_ID']}")
    row72 = next(row for row in strict if row["ELEMENT_ID"] == "GLYPH_0072")
    require(row72["REFERENCE_IDS"] == "OFFICIAL_R99_P652_FIG32.5_U002E", "GLYPH_0072 reference identity mismatch")
    require(float(row72["H_RATIO"]) == 1.0 and float(row72["AREA_RATIO"]) == 1.0, "GLYPH_0072 strict ratios are not 1/1")
    target_rows = {row["ELEMENT_ID"]: row for row in pixels}
    require(int(target_rows["GLYPH_0025"]["H_INK_PX"]) == 21, "GLYPH_0025 H mismatch")
    require(int(target_rows["GLYPH_0056"]["H_INK_PX"]) == 21, "GLYPH_0056 H mismatch")

    selection = read_json("peer_calibration/peer_selection_metadata.json")
    ownership = read_json("peer_calibration/peer_measurement_final_ownership.json")
    shape = read_json("peer_calibration/normalized_shape_comparison.json")
    recursively_closed(selection, "peer_selection")
    recursively_closed(ownership, "peer_ownership")
    recursively_closed(shape, "peer_shape")
    selected = selection["selected_peer_identity"]
    require(selection["pixel_metrics_deliberately_absent"] is True, "peer identity was not frozen before metrics")
    require(selected["figure_label"] == "图32.5" and int(selected["physical_page"]) == 652, "peer identity changed")
    require(selected["codepoint"] == "U+002E" and selected["font"] == "STIXTwoText-Bold", "peer font/codepoint mismatch")
    require(float(selected["size_pt"]) == 9.9626 and selected["color_rgb"] == [31, 35, 40] and selected["orientation"] == "HORIZONTAL", "peer attribute mismatch")
    require(ownership["same_preselected_peer"] is True and ownership["pdf_was_not_rerendered"] is True, "ownership used another render or peer")
    require(ownership["final_mask_complete_and_pure"] is True and int(ownership["final_mask_component_count_8_connected"]) == 1, "peer final mask integrity failed")
    require(int(ownership["peer_metrics"]["H_INK_PX"]) == 7 and int(ownership["peer_metrics"]["INK_AREA_PX"]) == 41, "peer final metrics mismatch")
    require(float(ownership["strict_comparison"]["H_RATIO"]) == 1.0 and float(ownership["strict_comparison"]["AREA_RATIO"]) == 1.0, "peer comparison mismatch")
    require(shape["normalized_masks_identical"] is True and int(shape["symmetric_difference_px"]) == 0, "peer/target normalized masks differ")

    decisions = read_json("explicit_review_decisions.json")
    recursively_closed(decisions, "explicit_decisions")
    require(decisions["no_global_boolean_attestation"] is True, "global attestation exclusion missing")
    require(decisions["no_default_decision"] is True, "automatic decision exclusion missing")
    require(decisions["missing_id_auto_decision"] is False, "missing-ID automatic decision enabled")
    require("default_decision" not in decisions, "automatic decision key present")
    object_map = decisions["object_decisions"]
    pair_map = decisions["critical_pair_decisions"]
    view_map = decisions["view_decisions"]
    role_map = decisions["role_decisions"]
    require(set(object_map) == object_set and len(object_map) == 170, "explicit object decision set mismatch")
    require(set(pair_map) == critical_expected and len(pair_map) == 13, "explicit critical decision set mismatch")
    require(set(view_map) == ALL_VIEWS and len(view_map) == 7, "explicit view decision set mismatch")
    expected_roles = {f"{row['PANEL']}|{row['ROLE']}" for row in roles}
    require(set(role_map) == expected_roles and len(role_map) == 9, "explicit role decision set mismatch")
    all_entries = [*object_map.values(), *pair_map.values(), *view_map.values(), *role_map.values()]
    require(len(all_entries) == 199, "explicit decision total mismatch")
    require(all(entry["decision"] == "PASS" for entry in all_entries), "explicit decision failure exists")
    require(all(entry["decision_source"] == "EXPLICIT_HUMAN_OPENED_EVIDENCE" for entry in all_entries), "non-explicit decision source")
    decision_ids = [entry["decision_id"] for entry in all_entries]
    notes = [entry["individual_note"] for entry in all_entries]
    require(len(decision_ids) == len(set(decision_ids)), "duplicate decision IDs")
    require(len(notes) == len(set(notes)), "non-individualized duplicate notes")
    for object_id, entry in object_map.items():
        require(entry["object_id"] == object_id, f"object map internal ID mismatch: {object_id}")
        require(entry["missing_stroke_px"] == 0 and entry["foreign_pixel_px"] == 0, f"object mask review failure: {object_id}")
        for key in ("native1x", "nearest8x", "raw_mask", "sheet"):
            require_rel(str(entry[key]), f"object decision {object_id} {key}")
    for pair_id, entry in pair_map.items():
        require(entry["pair_id"] == pair_id, f"pair map internal ID mismatch: {pair_id}")
        require_rel(entry["native1x"], f"pair decision {pair_id} native")
        require_rel(entry["nearest8x"], f"pair decision {pair_id} nearest")
    for view, entry in view_map.items():
        require(entry["view"] == view, f"view map internal ID mismatch: {view}")
        require_rel(entry["evidence_file"], f"view decision {view}")
    for role_id, entry in role_map.items():
        require(entry["role_id"] == role_id and int(entry["member_count"]) == len(entry["member_ids"]), f"role member mismatch: {role_id}")
        for path in entry["evidence_files"]:
            require_rel(path, f"role decision {role_id}")

    require({row["OBJECT_ID"] for row in manual} == object_set and len(manual) == 170, "manual ledger object set mismatch")
    require({row["PAIR_ID"] for row in critical} == critical_expected and len(critical) == 13, "critical ledger set mismatch")
    require({row["VIEW"] for row in views} == ALL_VIEWS and len(views) == 7, "view ledger set mismatch")
    require({row["ROLE_ID"] for row in roles} == expected_roles and len(roles) == 9, "role ledger set mismatch")
    require(all(row["DECISION"] == "PASS" for row in manual + critical + views + roles), "materialized manual decision failure")
    require(all(int(row["MISSING_STROKE_PX"]) == 0 and int(row["FOREIGN_PIXEL_PX"]) == 0 for row in manual), "manual missing/foreign ink failure")

    clip = {row["CHECK_ID"]: row for row in read_csv("clip_crop_final.csv")}
    require(int(clip["PAGE_EDGE_CLIP_PIXELS"]["MEASURED_VALUE"]) == 0, "clip count is nonzero")
    require(float(clip["TEXT_CROP_EDGE_CLEARANCE_PX"]["MEASURED_VALUE"]) >= 6.0, "crop-edge text clearance failed")
    require(all(row["VERDICT"] == "PASS" for row in clip.values()), "clip/crop ledger failure")
    require(all(row["PASS_FAIL"] == "PASS" for row in read_csv("after_font_audit.csv")), "font audit failure")
    require(all(row["STATUS"] == "PASS" for row in read_csv("source_scale_control_scan.csv")), "source-scale control failure")
    require(all(row["PASS"].lower() == "true" for row in read_csv("semantic_consistency.csv")), "semantic consistency failure")

    reference_count = validate_references(objects, contacts, pixels, pairs, manual, critical, views, roles, strict)
    integrity = read_csv("reused_evidence_integrity.csv")
    require(len(integrity) == 813, "reused integrity row count mismatch")
    for row in integrity:
        source = Path(row["SOURCE_PATH"])
        destination = ROOT / row["DEST_RELATIVE_PATH"]
        require(source.is_file() and destination.is_file(), f"integrity file missing: {row['DEST_RELATIVE_PATH']}")
        require(row["STATUS"] == "BYTE_IDENTICAL", f"integrity status failure: {row['DEST_RELATIVE_PATH']}")
        require(source.stat().st_size == int(row["SOURCE_BYTES"]), f"origin size changed: {source}")
        require(destination.stat().st_size == int(row["DEST_BYTES"]), f"destination size changed: {destination}")
        require(sha256(source) == row["SOURCE_SHA256"], f"origin hash changed: {source}")
        require(sha256(destination) == row["DEST_SHA256"], f"destination hash changed: {destination}")

    provenance = read_json("R6A_PREPARATION_PROVENANCE.json")
    recursively_closed(provenance, "provenance")
    require(provenance["handoff_id"] == HANDOFF_ID and provenance["route"] == ROUTE, "provenance route mismatch")
    require((R6 / "WRITE_STOPPED").stat().st_mtime_ns == int(provenance["origin_r6_marker_mtime_ns"]), "R6 marker changed")
    require(sha256(LOCAL_PDF) == LOCAL_PDF_SHA and LOCAL_PDF.stat().st_size == 42989, "local PDF identity mismatch")
    require(sha256(SOURCE) == SOURCE_SHA and SOURCE.read_text(encoding="utf-8").count(EXACT_INSERTION) == 1, "source identity mismatch")
    require(sha256(OFFICIAL_R99) == OFFICIAL_R99_SHA, "official R99 identity mismatch")
    require(git_output(["git", "rev-parse", "HEAD"]) == BASELINE_HEAD, "worktree HEAD changed")
    numstat = git_output(["git", "diff", "--numstat", "--", str(SOURCE_REL).replace("\\", "/")])
    parts = numstat.split("\t")
    require(len(parts) >= 3 and parts[0] == "1" and parts[1] == "0", f"source diff is not +1/-0: {numstat}")
    require(git_output(["git", "diff", "--check", "--", str(SOURCE_REL).replace("\\", "/")]) == "", "source diff check failed")
    changed_paths = git_output(["git", "-c", "core.quotepath=false", "diff", "--name-only"]).splitlines()
    expected_source_path = str(SOURCE_REL).replace("\\", "/")
    require(changed_paths == [expected_source_path], f"worktree changed paths mismatch: {changed_paths}")
    status_lines = [line for line in git_output(["git", "-c", "core.quotepath=false", "status", "--short"]).splitlines() if line]
    # git_output strips the porcelain line's leading index-column space.
    require(len(status_lines) == 1 and status_lines[0] == f"M {expected_source_path}", f"worktree scope changed: {status_lines}")

    ordinary = ordinary_file_scan()
    ads = scan_nondefault_streams()
    require(ads == 0, f"non-default stream count={ads}")
    checks = {
        "handoff_and_route_exact": True,
        "origin_r6_read_only_identity": True,
        "source_scope_exact": True,
        "local_pdf_identity_exact": True,
        "official_peer_selection_before_metrics": True,
        "official_peer_identity_exact": True,
        "official_peer_ownership_clean": True,
        "strict_low_profile_complete": True,
        "strict_low_profile_zero_failures": True,
        "object_universe_complete": True,
        "pair_universe_complete": True,
        "all_pairs_pass": True,
        "zero_final_illegal_overlap": True,
        "zero_clip": True,
        "crop_clearance_pass": True,
        "font_and_source_scale_pass": True,
        "semantic_consistency_pass": True,
        "explicit_object_decisions_exact": True,
        "explicit_critical_pair_decisions_exact": True,
        "explicit_view_decisions_exact": True,
        "explicit_role_decisions_exact": True,
        "no_global_or_automatic_review_decision": True,
        "final_ledgers_closed": True,
        "all_evidence_references_exist": True,
        "reused_evidence_byte_identical": True,
        "ordinary_files_only": True,
        "nondefault_stream_count_zero": True,
        "package_text_sentinel_scan_clean": True,
        "excluded_draft_artifacts_absent": True,
    }
    summary = {
        "N": 170,
        "glyph_rows": 112,
        "path_rows": 58,
        "pair_rows": 14365,
        "C_N_2_expected": 14365,
        "critical_pair_rows": 13,
        "pixel_rows": 114,
        "strict_low_profile_rows": 15,
        "strict_low_profile_failure_ids": [],
        "design_failure_ids": [],
        "explicit_decision_counts": {"objects": 170, "critical_pairs": 13, "views": 7, "roles": 9, "total": 199},
        "final_illegal_overlap_pixels": illegal_overlap,
        "clip_pixel_count": 0,
        "crop_edge_min_text_px": 72,
        "evidence_reference_checks": reference_count,
        "reused_integrity_rows": len(integrity),
        "ordinary_file_count_at_validation": len(ordinary["files"]),
        "nondefault_stream_count": ads,
        "local_pdf_sha256": LOCAL_PDF_SHA,
        "source_sha256": SOURCE_SHA,
        "official_r99_sha256": OFFICIAL_R99_SHA,
        "result": RESULT,
        "handoff_id": HANDOFF_ID,
        "route": ROUTE,
    }
    return checks, summary


def build_inventory() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inventory_path = ROOT / "accepted_payload_inventory.csv"
    require(not inventory_path.exists(), "payload inventory already exists")
    files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    rows: list[dict[str, Any]] = []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("peer_calibration/"):
            source_class = "ROOT_ADJUDICATED_PEER_EVIDENCE"
        elif rel in FINAL_LEDGERS or rel in {"explicit_review_decisions.json", "R6A_PREPARATION_PROVENANCE.json", "clip_crop_final.csv"}:
            source_class = "R6A_FINAL_DATA_OR_PROVENANCE"
        elif rel == "finalize_r6a.py":
            source_class = "R6A_CONSUMER_ONLY_VALIDATOR"
        else:
            source_class = "REUSED_FROZEN_R6_EVIDENCE"
        rows.append({
            "RELATIVE_PATH": rel,
            "BYTES": path.stat().st_size,
            "SHA256": sha256(path),
            "SOURCE_CLASS": source_class,
            "ORDINARY_FILE": True,
        })
    with inventory_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows, {
        "scope": "Every accepted payload file existing before inventory creation; excludes this inventory file and the six terminal/seal metadata files.",
        "row_count": len(rows),
        "excluded_self": inventory_path.name,
        "excluded_terminal_files": list(TERMINAL_OUTPUTS),
    }


def seal() -> dict[str, Any]:
    require(not any((ROOT / name).exists() for name in TERMINAL_OUTPUTS), "terminal output already exists")
    checks, summary = validate_package()
    inventory_rows, inventory_scope = build_inventory()
    read_csv("accepted_payload_inventory.csv")
    base_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    expected_final_file_count = len(base_files) + len(TERMINAL_OUTPUTS)
    terminal_time = datetime.now().astimezone().isoformat(timespec="seconds")
    terminal = {
        **summary,
        "checks": checks,
        "all_checks_true": all(checks.values()),
        "terminal_recalculation_time": terminal_time,
        "local_only": True,
        "official_candidate_reviewed": False,
        "fresh_sa1_started": False,
        "sa3_started": False,
        "inventory_scope": inventory_scope,
        "accepted_payload_inventory": "accepted_payload_inventory.csv",
        "expected_final_ordinary_file_count": expected_final_file_count,
        "write_stopped_next": True,
    }
    write_json(ROOT / "MACHINE_TERMINAL_RECALC.json", terminal)
    time.sleep(0.08)
    manifest = {
        "handoff_id": HANDOFF_ID,
        "origin_handoff_id": ORIGIN_HANDOFF_ID,
        "route": ROUTE,
        "result": RESULT,
        "scope": "FIG-P608-01 local direct-r6 evidence and explicit per-ID review reseal only",
        "not_root_acceptance": True,
        "official_candidate_required": True,
        "fresh_isolated_sa1_required": True,
        "object_universe": {"N": 170, "glyphs": 112, "paths": 58, "pairs": 14365, "expected_pairs": 14365},
        "explicit_decisions": {"source": "explicit_review_decisions.json", "objects": 170, "critical_pairs": 13, "views": 7, "roles": 9},
        "strict_low_profile": {
            "ledger": "strict_low_profile_adjudication.csv",
            "rows": 15,
            "failure_ids": [],
            "accepted_peer": "official R99 physical page 652 figure 32.5 U+002E",
            "target_ratios": {"GLYPH_0072_H": 1.0, "GLYPH_0072_AREA": 1.0},
        },
        "identities": {
            "baseline_head": BASELINE_HEAD,
            "source": str(SOURCE),
            "source_sha256": SOURCE_SHA,
            "source_diff": {"insertions": 1, "deletions": 0, "exact_insertion": EXACT_INSERTION},
            "local_pdf": str(LOCAL_PDF),
            "local_pdf_sha256": LOCAL_PDF_SHA,
            "local_pdf_bytes": 42989,
            "official_r99_sha256": OFFICIAL_R99_SHA,
        },
        "accepted_final_ledgers": list(FINAL_LEDGERS) + ["accepted_payload_inventory.csv"],
        "inventory_scope": inventory_scope,
        "expected_final_ordinary_file_count": expected_final_file_count,
        "checks": checks,
    }
    write_json(ROOT / "manifest.json", manifest)
    report = f"""# FIG-P608-01 SA2 R6A local evidence reseal

HANDOFF_ID: `{HANDOFF_ID}`  
ROUTE: `{ROUTE}`  
RESULT: `{RESULT}`

R6A preserves the sealed direct-r6 PDF and bottom evidence, replaces the
rejected aggregate review mechanism with 199 explicit per-ID decisions, and
applies the root-adjudicated strict low-profile calibration. It does not rerun
TeX, alter the business source, review an official candidate, or assert
`A_LOCAL_PASS`.

## Root-adjudicated peer

The peer identity was frozen before metrics by the predeclared nearest exact
other-figure-number rule. The unique choice is the U+002E period in `图32.5`,
official R99 physical page 652, bbox `(180.941010, 702.317444, 183.690704,
712.280090)`, STIXTwoText-Bold 9.9626pt, RGB(31,35,40), horizontal. The one
300-dpi Poppler render initially contained four padded-bbox pixels belonging to
the adjacent digit `5`; the R6 bare-bbox/centre-distance ownership rule removed
them without changing the peer or raster. Final peer and GLYPH_0072 masks are
both H=7px, area=41px, one component, with identical translation-normalized
pixel sets. Strict target/peer H and area ratios are both 1.000000.

## Bottom-up closure

- N=170: 112 glyphs and 58 foreground paths.
- Complete C(N,2)=14,365 pair ledger; pair failures=0.
- Strict low-profile rows=15; true design failures=0.
- Final illegal overlap pixels=0; clip pixels=0; crop text clearance=72px.
- Explicit decisions: 170 objects, 13 critical pairs, 7 views, 9 roles.
- Reused byte-identical evidence files={summary['reused_integrity_rows']}.
- Accepted payload inventory rows={len(inventory_rows)}; expected final ordinary files={expected_final_file_count}.
- Non-default NTFS stream count=0.

## Source and local candidate identity

- HEAD `{BASELINE_HEAD}`; sole source diff +1/-0.
- Source SHA-256 `{SOURCE_SHA}`.
- Local direct-r6 PDF SHA-256 `{LOCAL_PDF_SHA}`; 42,989 bytes.
- Official R99 source PDF SHA-256 `{OFFICIAL_R99_SHA}`.

## Terminal boundary

`MACHINE_TERMINAL_RECALC.json` precedes the manifest, this report, result, and
handoff. `WRITE_STOPPED` is written strictly last. A new official candidate and
fresh isolated SA1 remain mandatory; SA1 and SA3 were not started here.
"""
    (ROOT / "after_visual_acceptance.md").write_text(report, encoding="utf-8")
    (ROOT / "RESULT.txt").write_text(RESULT + "\n", encoding="utf-8")
    handoff = {
        "handoff_id": HANDOFF_ID,
        "origin_handoff_id": ORIGIN_HANDOFF_ID,
        "route": ROUTE,
        "result": RESULT,
        "local_only": True,
        "do_not_claim": "A_LOCAL_PASS",
        "official_candidate_required": True,
        "fresh_isolated_sa1_required": True,
        "sa1_started": False,
        "sa3_started": False,
        "expected_final_ordinary_file_count": expected_final_file_count,
        "terminal": "MACHINE_TERMINAL_RECALC.json",
        "manifest": "manifest.json",
    }
    write_json(ROOT / "HANDOFF_REPORT.json", handoff)

    premarker_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    require(len(premarker_files) == expected_final_file_count - 1, "pre-marker file count mismatch")
    require(scan_nondefault_streams() == 0, "pre-marker non-default stream found")
    require(not scan_text_sentinels(), "pre-marker text sentinel found")
    ordinary_file_scan()
    latest_other_ns = max(path.stat().st_mtime_ns for path in premarker_files)
    remaining_ns = 1_500_000_000 - (time.time_ns() - latest_other_ns)
    if remaining_ns > 0:
        time.sleep(remaining_ns / 1_000_000_000 + 0.25)
    marker = ROOT / "WRITE_STOPPED"
    marker.write_text(
        f"{datetime.now().astimezone().isoformat(timespec='seconds')}\n"
        f"{RESULT}\n{HANDOFF_ID}\n{ROUTE}\n"
        f"ordinary_files={expected_final_file_count}; nondefault_streams=0; terminal -> manifest/report/result/handoff -> marker; zero writes permitted after this marker.\n",
        encoding="utf-8",
    )
    final_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    latest_other_after = max(path.stat().st_mtime_ns for path in final_files if path != marker)
    margin_ns = marker.stat().st_mtime_ns - latest_other_after
    require(len(final_files) == expected_final_file_count, "final file count mismatch")
    require(margin_ns >= 1_000_000_000, "marker is not strictly latest by one second")
    require(scan_nondefault_streams() == 0, "post-marker non-default stream found")
    require(not scan_text_sentinels(), "post-marker text sentinel found")
    ordinary_file_scan()
    return {
        "result": RESULT,
        "handoff_id": HANDOFF_ID,
        "ordinary_file_count": len(final_files),
        "inventory_rows": len(inventory_rows),
        "marker_margin_ns": margin_ns,
        "nondefault_stream_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        checks, summary = validate_package()
        print(json.dumps({"checks": checks, **summary}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(seal(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
