from __future__ import annotations

import csv
import hashlib
import itertools
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def unique_check(name: str, key: str, expected: int, errors: list[dict]) -> list[dict[str, str]]:
    rows = read_csv(name)
    identifiers = [row.get(key, "") for row in rows]
    if len(rows) != expected or len(set(identifiers)) != expected or "" in identifiers:
        errors.append(
            {
                "check": "count_unique",
                "file": name,
                "rows": len(rows),
                "unique": len(set(identifiers)),
                "expected": expected,
                "blank_id": "" in identifiers,
            }
        )
    return rows


def main() -> int:
    errors: list[dict] = []
    with (ROOT / "identity.json").open("r", encoding="utf-8") as handle:
        identity = json.load(handle)
    expected_identity = {
        "uid": "FIG-P640-01",
        "handoff_id": "C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-REPLACEMENT-V2",
        "agent_identity": "/root/sa1_fig_p640_r106_fresh_isolated_replacement_v2",
        "model": "gpt-5.6-sol",
        "reasoning": "xhigh",
        "fork_turns": "none",
        "pdf_pages": 817,
        "pdf_bytes": 4967249,
        "pdf_sha256": "0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A",
        "physical_page": 690,
        "printed_page": 677,
        "render_dpi": 300,
    }
    identity_mismatches = {
        key: {"actual": identity.get(key), "expected": expected}
        for key, expected in expected_identity.items()
        if identity.get(key) != expected
    }
    if identity_mismatches:
        errors.append({"check": "identity", "mismatches": identity_mismatches})
    specs = [
        ("glyph_machine.csv", "glyph_id", 242),
        ("manual_glyph_ledger.csv", "glyph_id", 242),
        ("object_inventory_machine.csv", "object_id", 45),
        ("manual_object_ledger.csv", "object_id", 45),
        ("critical_relations_machine.csv", "pair_id", 37),
        ("manual_critical_relation_ledger.csv", "pair_id", 37),
        ("source_font_audit_machine.csv", "element_id", 32),
        ("manual_font_element_ledger.csv", "element_id", 32),
        ("peer_role_machine.csv", "comparison_id", 10),
        ("manual_peer_role_ledger.csv", "comparison_id", 10),
        ("views_machine.csv", "view_id", 6),
        ("manual_view_ledger.csv", "view_id", 6),
        ("manual_hard_gate_ledger.csv", "gate_id", 15),
        ("after_font_audit.csv", "element_id", 32),
        ("after_pixel_measurements.csv", "glyph_id", 242),
        ("after_overlap_report.csv", "pair_id", 37),
    ]
    tables: dict[str, list[dict[str, str]]] = {}
    for name, key, expected in specs:
        tables[name] = unique_check(name, key, expected, errors)

    crosswalks = [
        ("glyph_machine.csv", "manual_glyph_ledger.csv", "glyph_id"),
        ("object_inventory_machine.csv", "manual_object_ledger.csv", "object_id"),
        ("critical_relations_machine.csv", "manual_critical_relation_ledger.csv", "pair_id"),
        ("source_font_audit_machine.csv", "manual_font_element_ledger.csv", "element_id"),
        ("peer_role_machine.csv", "manual_peer_role_ledger.csv", "comparison_id"),
        ("views_machine.csv", "manual_view_ledger.csv", "view_id"),
    ]
    for machine_name, manual_name, key in crosswalks:
        machine_ids = {row[key] for row in tables[machine_name]}
        manual_ids = {row[key] for row in tables[manual_name]}
        if machine_ids != manual_ids:
            errors.append(
                {
                    "check": "crosswalk_set",
                    "machine": machine_name,
                    "manual": manual_name,
                    "machine_only": sorted(machine_ids - manual_ids),
                    "manual_only": sorted(manual_ids - machine_ids),
                }
            )

    report_crosswalks = [
        ("manual_font_element_ledger.csv", "after_font_audit.csv", "element_id"),
        ("glyph_machine.csv", "after_pixel_measurements.csv", "glyph_id"),
        ("critical_relations_machine.csv", "after_overlap_report.csv", "pair_id"),
    ]
    for source_name, report_name, key in report_crosswalks:
        source_ids = {row[key] for row in tables[source_name]}
        report_ids = {row[key] for row in tables[report_name]}
        if source_ids != report_ids:
            errors.append(
                {
                    "check": "report_crosswalk_set",
                    "source": source_name,
                    "report": report_name,
                    "source_only": sorted(source_ids - report_ids),
                    "report_only": sorted(report_ids - source_ids),
                }
            )

    boolean_columns = {
        "original_match",
        "overlay_complete",
        "mask_only_pure",
        "semantic_content_match",
        "mask_complete",
        "role_correct",
        "clip_clear",
        "source_size_hard_pass",
        "visual_font_hard_pass",
        "graphics_scale_confirmed",
        "role_hierarchy_correct",
        "visual_match",
        "hard_pass",
        "object_a_match",
        "object_b_match",
        "illegal_overlap",
    }
    manual_names = [
        "manual_glyph_ledger.csv",
        "manual_object_ledger.csv",
        "manual_critical_relation_ledger.csv",
        "manual_font_element_ledger.csv",
        "manual_peer_role_ledger.csv",
        "manual_view_ledger.csv",
        "manual_hard_gate_ledger.csv",
    ]
    manual_pass_rows = 0
    for name in manual_names:
        for row_number, row in enumerate(tables[name], start=2):
            if row.get("decision") != "PASS" or not row.get("reviewer", "").strip() or not row.get("note", "").strip():
                errors.append(
                    {
                        "check": "manual_required",
                        "file": name,
                        "row": row_number,
                        "decision": row.get("decision"),
                        "reviewer_present": bool(row.get("reviewer", "").strip()),
                        "note_present": bool(row.get("note", "").strip()),
                    }
                )
            else:
                manual_pass_rows += 1
            for column, value in row.items():
                if column in boolean_columns and value.lower() not in {"true", "false"}:
                    errors.append(
                        {
                            "check": "manual_boolean",
                            "file": name,
                            "row": row_number,
                            "column": column,
                            "value": value,
                        }
                    )

    object_ids = [row["object_id"] for row in tables["object_inventory_machine.csv"]]
    object_id_set = set(object_ids)
    pair_rows = read_csv("all_unordered_pairs_machine.csv")
    actual_pairs = {(row["object_a"], row["object_b"]) for row in pair_rows}
    expected_pairs = set(itertools.combinations(object_ids, 2))
    unknown_pair_ids = sorted(
        {
            value
            for row in pair_rows
            for value in (row["object_a"], row["object_b"])
            if value not in object_id_set
        }
    )
    if len(pair_rows) != 990 or len(actual_pairs) != 990 or actual_pairs != expected_pairs or unknown_pair_ids:
        errors.append(
            {
                "check": "all_unordered_pairs",
                "rows": len(pair_rows),
                "unique_pairs": len(actual_pairs),
                "expected": len(expected_pairs),
                "missing": len(expected_pairs - actual_pairs),
                "extra": len(actual_pairs - expected_pairs),
                "unknown_object_ids": unknown_pair_ids,
            }
        )

    with (ROOT / "machine_counts.json").open("r", encoding="utf-8") as handle:
        machine_counts = json.load(handle)
    expected_counts = {
        "semantic_text_objects": 32,
        "semantic_graphic_objects": 13,
        "semantic_objects_total_N": 45,
        "unordered_pairs_expected_C_N_2": 990,
        "unordered_pairs_actual": 990,
        "visible_nonspace_glyphs": 242,
        "drawing_primitives": 20,
        "critical_relations_total": 37,
        "critical_near_relations_with_roi": 19,
        "pair_raw_intersection_nonzero_rows": 0,
        "empty_foreground_object_masks": 0,
        "empty_glyph_masks": 0,
    }
    for key, expected in expected_counts.items():
        if machine_counts.get(key) != expected:
            errors.append(
                {
                    "check": "machine_count",
                    "key": key,
                    "actual": machine_counts.get(key),
                    "expected": expected,
                }
            )

    expected_png_counts = {
        "glyph_masks": 242,
        "glyph_rois_1x": 242,
        "glyph_rois_8x": 242,
        "glyph_contact_sheets_8x": 21,
        "object_masks": 43,
        "critical_pair_rois_1x": 19,
        "critical_pair_rois_8x": 19,
        "critical_pair_contact_sheets_8x": 4,
    }
    png_counts: dict[str, int] = {}
    for folder, expected in expected_png_counts.items():
        files = sorted((ROOT / folder).glob("*.png"))
        png_counts[folder] = len(files)
        if len(files) != expected:
            errors.append(
                {
                    "check": "png_count",
                    "folder": folder,
                    "actual": len(files),
                    "expected": expected,
                    "files": [path.name for path in files],
                }
            )

    expected_critical_ids = {
        row["pair_id"]
        for row in tables["critical_relations_machine.csv"]
        if row.get("roi_1x_path", "").strip()
    }
    for folder in ("critical_pair_rois_1x", "critical_pair_rois_8x"):
        actual_ids = {path.stem for path in (ROOT / folder).glob("*.png")}
        if actual_ids != expected_critical_ids:
            errors.append(
                {
                    "check": "critical_roi_set",
                    "folder": folder,
                    "expected_count": len(expected_critical_ids),
                    "actual_count": len(actual_ids),
                    "missing": sorted(expected_critical_ids - actual_ids),
                    "extra": sorted(actual_ids - expected_critical_ids),
                }
            )

    cache_files = sorted(
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}
    )
    if cache_files:
        errors.append({"check": "cache_files", "paths": cache_files})

    safe_rows = read_csv("id_safe_filename_machine.csv")
    safe_keys = {(row["id_kind"], row["element_id"]) for row in safe_rows}
    missing_ordinary_paths: list[str] = []
    for row in safe_rows:
        for value in row["ordinary_paths"].split("|"):
            if value.startswith("N/A_"):
                continue
            path = ROOT / value
            if not path.is_file() or path.stat().st_size <= 0:
                missing_ordinary_paths.append(value)
    if len(safe_rows) != 324 or len(safe_keys) != 324 or missing_ordinary_paths:
        errors.append(
            {
                "check": "safe_filename_mapping",
                "rows": len(safe_rows),
                "unique_keys": len(safe_keys),
                "expected": 324,
                "missing_or_empty_paths": sorted(set(missing_ordinary_paths)),
            }
        )

    required_current_files = [
        "full_page_200dpi.png",
        "figure_crop_300dpi.png",
        "standalone_300dpi.png",
        "grayscale_300dpi.png",
        "after_pixel_measurements.csv",
        "after_overlap_report.csv",
        "after_text_measurement_overlay_300dpi.png",
        "after_font_audit.csv",
        "after_overlap_adjudication.md",
        "after_visual_acceptance.md",
        "HANDOFF.md",
        "REPORT.md",
        "RESULT.txt",
    ]
    missing_required_current = [name for name in required_current_files if not (ROOT / name).is_file()]
    if missing_required_current:
        errors.append({"check": "required_current_files", "missing": missing_required_current})

    expected_outcome_lines = {
        "SA1_REVIEW_OUTCOME=CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE",
        "LOCAL_PASS_COUNTED=false",
        "GLOBAL_PASS_COUNTED=false",
        "SA3_AUTHORIZED=false",
    }
    result_lines = {
        line.strip()
        for line in (ROOT / "RESULT.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    } if (ROOT / "RESULT.txt").is_file() else set()
    if not expected_outcome_lines.issubset(result_lines):
        errors.append(
            {
                "check": "result_routing",
                "missing": sorted(expected_outcome_lines - result_lines),
                "unexpected": sorted(result_lines - expected_outcome_lines),
            }
        )

    final_mode = "--final" in sys.argv
    final_checks = {
        "ordinary_file_count": None,
        "manifest_listed_count": None,
        "manifest_payload_count": None,
        "manifest_control_count": None,
        "self_excluded_count": None,
        "manifest_identity_mismatch_count": None,
        "write_stopped_is_strict_last_mtime": None,
    }
    if final_mode:
        manifest_path = ROOT / "MANIFEST.csv"
        write_stopped_path = ROOT / "WRITE_STOPPED"
        if not manifest_path.is_file() or not write_stopped_path.is_file():
            errors.append(
                {
                    "check": "final_seal_files",
                    "manifest_exists": manifest_path.is_file(),
                    "write_stopped_exists": write_stopped_path.is_file(),
                }
            )
        else:
            manifest_rows = read_csv("MANIFEST.csv")
            manifest_paths = [row["relative_path"] for row in manifest_rows]
            listed_set = set(manifest_paths)
            final_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
            expected_listed = {
                path.relative_to(ROOT).as_posix()
                for path in final_files
                if path.name not in {"MANIFEST.csv", "WRITE_STOPPED"}
            }
            manifest_mismatches: list[dict] = []
            for row in manifest_rows:
                path = ROOT / row["relative_path"]
                if not path.is_file():
                    manifest_mismatches.append({"path": row["relative_path"], "problem": "missing"})
                    continue
                actual_size = path.stat().st_size
                actual_sha = file_sha256(path)
                if actual_size != int(row["bytes"]) or actual_sha != row["sha256"]:
                    manifest_mismatches.append(
                        {
                            "path": row["relative_path"],
                            "problem": "identity_mismatch",
                            "actual_bytes": actual_size,
                            "manifest_bytes": int(row["bytes"]),
                            "actual_sha256": actual_sha,
                            "manifest_sha256": row["sha256"],
                        }
                    )
            payload_count = sum(row["manifest_scope"] == "PAYLOAD" for row in manifest_rows)
            control_count = sum(row["manifest_scope"] == "CONTROL" for row in manifest_rows)
            self_excluded = {
                path.relative_to(ROOT).as_posix()
                for path in final_files
                if path.name in {"MANIFEST.csv", "WRITE_STOPPED"}
            }
            latest_other_mtime_ns = max(
                path.stat().st_mtime_ns for path in final_files if path.name != "WRITE_STOPPED"
            )
            strict_last = write_stopped_path.stat().st_mtime_ns >= latest_other_mtime_ns
            marker_text = write_stopped_path.read_text(encoding="utf-8")
            marker_required = [
                "SA1_REVIEW_OUTCOME=CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE",
                "LOCAL_PASS_COUNTED=false",
                "GLOBAL_PASS_COUNTED=false",
                "SA3_AUTHORIZED=false",
                "ORDINARY_FILE_COUNT=875",
                "MANIFEST_LISTED_COUNT=873",
                "MANIFEST_PAYLOAD_COUNT=859",
                "MANIFEST_CONTROL_COUNT=14",
                "SELF_EXCLUDED_COUNT=2",
                "POSTSEAL_WRITES=0",
            ]
            marker_missing = [line for line in marker_required if line not in marker_text]
            if (
                len(manifest_rows) != 873
                or len(listed_set) != 873
                or listed_set != expected_listed
                or payload_count != 859
                or control_count != 14
                or self_excluded != {"MANIFEST.csv", "WRITE_STOPPED"}
                or manifest_mismatches
                or not strict_last
                or marker_missing
            ):
                errors.append(
                    {
                        "check": "final_manifest_and_write_stop",
                        "manifest_rows": len(manifest_rows),
                        "manifest_unique": len(listed_set),
                        "expected_listed": len(expected_listed),
                        "missing_from_manifest": sorted(expected_listed - listed_set),
                        "extra_in_manifest": sorted(listed_set - expected_listed),
                        "payload_count": payload_count,
                        "control_count": control_count,
                        "self_excluded": sorted(self_excluded),
                        "identity_mismatches": manifest_mismatches,
                        "write_stopped_is_strict_last_mtime": strict_last,
                        "marker_missing": marker_missing,
                    }
                )
            final_checks = {
                "ordinary_file_count": len(final_files),
                "manifest_listed_count": len(manifest_rows),
                "manifest_payload_count": payload_count,
                "manifest_control_count": control_count,
                "self_excluded_count": len(self_excluded),
                "manifest_identity_mismatch_count": len(manifest_mismatches),
                "write_stopped_is_strict_last_mtime": strict_last,
            }

    result = {
        "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper(),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "identity_mismatch_count": len(identity_mismatches),
        "table_rows": {name: len(rows) for name, rows in tables.items()},
        "manual_pass_rows": manual_pass_rows,
        "all_unordered_pairs_rows": len(pair_rows),
        "all_unordered_pairs_unique": len(actual_pairs),
        "unknown_pair_object_ids": unknown_pair_ids,
        "png_counts": png_counts,
        "cache_entries": cache_files,
        "id_safe_filename_rows": len(safe_rows),
        "id_safe_filename_unique_keys": len(safe_keys),
        "missing_ordinary_paths": sorted(set(missing_ordinary_paths)),
        "final_mode": final_mode,
        "final_checks": final_checks,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if "--write" in sys.argv:
        (ROOT / "preseal_validation_machine.json").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
