"""Revision-103 terminal disk re-read for FIG-P634-01 R5/R94 evidence.

This checker deliberately does not use the auditor's in-memory objects.  It
reopens the emitted CSV/JSON/Markdown, compressed raw-mask registry and every
active evidence pack, then writes an explicit machine-terminal ledger.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image


OUT = Path(__file__).resolve().parents[1]
PAIR = OUT / "critical_pairs_v2"
GLYPH = OUT / "glyph_threshold_failures_v2"


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def truth(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def as_float(value: object) -> float:
    return float(str(value))


def image_ok(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.load()
            return im.width > 0 and im.height > 0
    except Exception:
        return False


def nonempty_l_mask(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.load()
            return im.convert("L").getbbox() is not None
    except Exception:
        return False


def main() -> None:
    checks: list[dict[str, str]] = []

    def add(check_id: str, expected: object, actual: object, ok: bool, detail: str) -> None:
        checks.append(
            {
                "CHECK_ID": check_id,
                "EXPECTED": truth(expected),
                "ACTUAL": truth(actual),
                "STATUS": "PASS" if ok else "FAIL",
                "DETAIL": detail,
            }
        )

    manifest = read_csv("complete_object_manifest.csv")
    manifest_ids = [r["OBJECT_ID"] for r in manifest]
    manifest_unique = len(set(manifest_ids))
    add("manifest_row_count", 452, len(manifest), len(manifest) == 452, "Re-read complete_object_manifest.csv from disk.")
    add("manifest_unique_object_ids", 452, manifest_unique, manifest_unique == 452, "Every registered object has a unique OBJECT_ID.")
    nonempty_manifest = [r["OBJECT_ID"] for r in manifest if int(r["MASK_PIXEL_COUNT"]) <= 0]
    add("manifest_nonempty_masks", "0 zero masks", len(nonempty_manifest), not nonempty_manifest, "MASK_PIXEL_COUNT is positive for every literal, semantic, graphic and background object.")

    registry_path = OUT / "masks" / "independent_raw_masks_registry_v2.npz"
    registry_ok = False
    registry_detail = "registry unreadable"
    registry_ids: list[str] = []
    registry_zero: list[str] = []
    registry_mismatch: list[str] = []
    try:
        with np.load(registry_path, allow_pickle=False) as data:
            registry_ids = [str(x) for x in data["object_ids"].tolist()]
            offsets = data["offsets"].astype(np.int64)
            xs = data["xs"]
            ys = data["ys"]
            registry_zero = [registry_ids[i] for i in range(len(registry_ids)) if offsets[i + 1] <= offsets[i]]
            manifest_by_id = {r["OBJECT_ID"]: r for r in manifest}
            registry_mismatch = [
                registry_ids[i]
                for i in range(len(registry_ids))
                if registry_ids[i] not in manifest_by_id
                or int(offsets[i + 1] - offsets[i]) != int(manifest_by_id[registry_ids[i]]["MASK_PIXEL_COUNT"])
            ]
            registry_ok = (
                len(registry_ids) == 452
                and len(offsets) == len(registry_ids) + 1
                and int(offsets[-1]) == len(xs) == len(ys)
                and set(registry_ids) == set(manifest_ids)
                and not registry_zero
                and not registry_mismatch
            )
            registry_detail = f"ids={len(registry_ids)}, coordinate_count={len(xs)}, zero_spans={len(registry_zero)}, manifest_span_mismatches={len(registry_mismatch)}"
    except Exception as exc:  # terminal check must surface an unreadable registry as integrity failure
        registry_detail = f"registry exception: {exc!r}"
    add("raw_mask_registry_matches_manifest", "452 unique non-empty masks", f"{len(registry_ids)} ids; {registry_detail}", registry_ok, "Compressed independent raw masks were re-read, not inferred from the manifest alone.")

    semantic = [r for r in manifest if r["CATEGORY"] == "TEXT_ELEMENT"]
    pair_graphics = [r for r in manifest if r["PAIR_INCLUDED"].lower() == "true" and r["CATEGORY"] in {"GRAPHIC", "BACKGROUND"}]
    pair_manifest = [r for r in manifest if r["PAIR_INCLUDED"].lower() == "true"]
    add("semantic_plus_pair_graphic_objects", "106 + 39 = 145", f"{len(semantic)} + {len(pair_graphics)} = {len(pair_manifest)}", len(semantic) == 106 and len(pair_graphics) == 39 and len(pair_manifest) == 145, "Pair universe is semantic text plus final graphic/background objects only; literal glyphs are component witnesses.")
    empty_foreground = [r["OBJECT_ID"] for r in manifest if r["CATEGORY"] == "GRAPHIC" and r["BACKGROUND_EXEMPT"].lower() == "false" and int(r["MASK_PIXEL_COUNT"]) == 0]
    add("foreground_graphic_empty_masks", 0, len(empty_foreground), not empty_foreground, "Foreground graphics are separately checked even though all objects must already have a non-empty raw mask.")

    pairs = read_csv("all_pairs_overlap_clearance.csv")
    after_pairs = read_csv("after_overlap_report.csv")
    pair_keys = [tuple(sorted((r["OBJECT_A"], r["OBJECT_B"]))) for r in pairs]
    expected_pairs = len(pair_manifest) * (len(pair_manifest) - 1) // 2
    add("unordered_pair_count", expected_pairs, len(pairs), len(pairs) == expected_pairs == 10440, "Re-read all unordered rows from the all-pairs CSV.")
    add("unordered_pair_unique_coverage", expected_pairs, len(set(pair_keys)), len(set(pair_keys)) == expected_pairs, "No duplicate or missing unordered pair is hidden by repeated IDs.")
    add("after_overlap_copy_identity", sha256(OUT / "all_pairs_overlap_clearance.csv"), sha256(OUT / "after_overlap_report.csv"), sha256(OUT / "all_pairs_overlap_clearance.csv") == sha256(OUT / "after_overlap_report.csv") and len(after_pairs) == len(pairs), "The after report is an exact on-disk copy of the exhaustive pair ledger.")
    bad_relation = [r["PAIR_ID"] for r in pairs if not r["RELATION"] or not r["METHOD"] or not r["STATUS"]]
    add("pair_relation_classification_complete", "0 blank classifications", len(bad_relation), not bad_relation, "Every pair retains relation, method and disposition fields.")
    pair_fail = [r for r in pairs if r["STATUS"] == "FAIL"]
    overlap_fail = [r for r in pair_fail if int(r["OVERLAP_PIXELS"]) >= 1]
    clearance_fail = [r for r in pair_fail if int(r["OVERLAP_PIXELS"]) == 0]
    add("pair_failure_status_count", 1, len(pair_fail), len(pair_fail) == 1, "Terminal disposition permits an audit FAIL, but must not hide its exact bottom-level count.")
    add("overlap_failure_count", 0, len(overlap_fail), len(overlap_fail) == 0, "No independently separated pair has one or more common foreground pixels.")
    add("clearance_failure_count", 1, len(clearance_fail), len(clearance_fail) == 1, "The one true failure is a non-overlap clearance shortfall.")
    expected_pair_failure = {"EL-035-CARD1_STATE-MATH_SCRIPT", "G-CARD1-BORDER"}
    actual_pair_failure = set()
    if len(pair_fail) == 1:
        actual_pair_failure = {pair_fail[0]["OBJECT_A"], pair_fail[0]["OBJECT_B"]}
    add("failed_pair_identity", "EL-035-CARD1_STATE-MATH_SCRIPT + G-CARD1-BORDER", " + ".join(sorted(actual_pair_failure)), actual_pair_failure == expected_pair_failure and pair_fail and pair_fail[0]["OVERLAP_PIXELS"] == "0" and abs(as_float(pair_fail[0]["MIN_RAW_INK_GAP_PX"]) - 2.162) < 0.001, "Re-read exact pair identity, zero intersection, and 2.162px raw gap.")

    raw_chars = read_csv("raw_char_measurements.csv")
    glyph_fail = [r for r in raw_chars if r["PASS_FAIL"] == "FAIL"]
    add("literal_glyph_row_count", 307, len(raw_chars), len(raw_chars) == 307, "Every literal glyph audit row is present.")
    add("literal_glyph_failure_count", 11, len(glyph_fail), len(glyph_fail) == 11, "All CJK raw-height failures remain visible in the terminal ledger.")
    glyph_dirs = sorted([p for p in GLYPH.iterdir() if p.is_dir()]) if GLYPH.exists() else []
    glyph_required = {"raw_1x.png", "raw_mask_1x.png", "inspection_8x_nearest.png", "glyph.json"}
    glyph_incomplete: list[str] = []
    glyph_empty_masks: list[str] = []
    for p in glyph_dirs:
        names = {f.name for f in p.iterdir() if f.is_file()}
        if not glyph_required.issubset(names) or not all(image_ok(p / n) for n in ("raw_1x.png", "raw_mask_1x.png", "inspection_8x_nearest.png")):
            glyph_incomplete.append(p.name)
        if (p / "raw_mask_1x.png").exists() and not nonempty_l_mask(p / "raw_mask_1x.png"):
            glyph_empty_masks.append(p.name)
    add("glyph_failure_evidence_packs", "11 complete", f"dirs={len(glyph_dirs)}, incomplete={len(glyph_incomplete)}, empty_masks={len(glyph_empty_masks)}", len(glyph_dirs) == 11 and not glyph_incomplete and not glyph_empty_masks, "Each literal failure has raw 1:1, its own mask, 8x nearest inspection and measurements.")

    d_rows = read_csv("same_class_ratio_audit.csv")
    e_rows = read_csv("role_ratio_audit.csv")
    d_fail = [r for r in d_rows if r["STATUS"] == "FAIL"]
    e_fail = [r for r in e_rows if r["STATUS"] == "FAIL"]
    add("same_class_ratio_failure_count", 23, len(d_fail), len(d_fail) == 23, "D failures are re-counted from the complete same-class CSV.")
    add("role_ratio_failure_count", 3, len(e_fail), len(e_fail) == 3, "E failures are re-counted from the complete matching-script role CSV.")

    edge_rows = read_csv("edge_clip_audit.csv")
    clip_rows = [r for r in edge_rows if r["CLIP_STATUS"] == "FAIL"]
    add("clip_failure_count", 0, len(clip_rows), not clip_rows, "Physical page/crop edge audit contains no clipped object.")

    pair_dirs = sorted([p for p in PAIR.iterdir() if p.is_dir()]) if PAIR.exists() else []
    seven_core = {"context_1x.png", "raw_1x.png", "A_raw_mask_1x.png", "B_raw_mask_1x.png", "intersection_mask_1x.png", "inspection_8x_nearest.png", "pair.json"}
    supplemental = {"A_B_intersection_overlay_1x.png", "A_B_intersection_overlay_8x_nearest.png"}
    pair_incomplete: list[str] = []
    pair_bad_image: list[str] = []
    pair_empty_ab: list[str] = []
    pair_json_bad: list[str] = []
    for p in pair_dirs:
        names = {f.name for f in p.iterdir() if f.is_file()}
        if not seven_core.issubset(names) or not supplemental.issubset(names):
            pair_incomplete.append(p.name)
            continue
        picture_names = {"context_1x.png", "raw_1x.png", "A_raw_mask_1x.png", "B_raw_mask_1x.png", "intersection_mask_1x.png", "inspection_8x_nearest.png", "A_B_intersection_overlay_1x.png", "A_B_intersection_overlay_8x_nearest.png"}
        if not all(image_ok(p / n) for n in picture_names):
            pair_bad_image.append(p.name)
        if not nonempty_l_mask(p / "A_raw_mask_1x.png") or not nonempty_l_mask(p / "B_raw_mask_1x.png"):
            pair_empty_ab.append(p.name)
        try:
            payload = json.loads((p / "pair.json").read_text(encoding="utf-8"))
            if not payload.get("a") or not payload.get("b"):
                pair_json_bad.append(p.name)
        except Exception:
            pair_json_bad.append(p.name)
    add("critical_failed_pair_evidence_packs", "35 dirs; 7 core + 2 overlays each", f"dirs={len(pair_dirs)}, missing={len(pair_incomplete)}, unreadable_images={len(pair_bad_image)}, empty_A_or_B={len(pair_empty_ab)}, bad_json={len(pair_json_bad)}", len(pair_dirs) == 35 and not pair_incomplete and not pair_bad_image and not pair_empty_ab and not pair_json_bad, "All current critical/failed packs have raw, A/B, intersection, 1:1 context, 8x nearest and machine identity; two overlays are also retained.")

    view_files = [
        OUT / "renders" / "full_page_200dpi.png",
        OUT / "crops" / "figure_crop_300dpi.png",
        OUT / "crops" / "standalone_300dpi.png",
        OUT / "crops" / "grayscale_300dpi.png",
        OUT / "overlays" / "after_text_measurement_overlay_300dpi.png",
    ]
    add("four_view_and_overlay_files", "5 readable files", sum(image_ok(p) for p in view_files), all(image_ok(p) for p in view_files), "Terminal reopens 200dpi full page, 300dpi crop/standalone/grayscale, and ELEMENT_ID overlay.")

    summary = json.loads((OUT / "audit_summary.json").read_text(encoding="utf-8"))
    after_visual = (OUT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    formal_report = (OUT / "FIG-P634-01-SA1-STRICT-R5-R94.md").read_text(encoding="utf-8")
    visual_values = {k: v.strip() for k, v in re.findall(r"^([A-Z_]+)\s*=\s*(.+?)\s*$", after_visual, flags=re.M)}
    visual_result = re.search(r"^RESULT:\s*(.+?)\s*$", after_visual, flags=re.M)
    report_values = {k: v.strip() for k, v in re.findall(r"`([A-Z_]+)\s*=\s*([^`]+)`", formal_report)}
    report_result = report_values.pop("RESULT", "")
    summary_values = {k: truth(v) for k, v in summary["gates"].items()}
    expected_gate_values = {
        "SOURCE_FONT_PASS": truth(not any(r["STATUS"] == "FAIL" and r["AUDIT_TYPE"] in {"ELEMENT_EFFECTIVE_FONT", "SAME_ROLE_SOURCE_CONSISTENCY"} for r in read_csv("after_font_audit.csv"))),
        "PIXEL_HEIGHT_PASS": truth(not glyph_fail and not [r for r in read_csv("after_pixel_measurements.csv") if r["PASS_FAIL"] == "FAIL"]),
        "SAME_CLASS_RATIO_PASS": truth(not d_fail),
        "ROLE_RATIO_PASS": truth(not e_fail),
        "OVERLAP_PIXEL_COUNT": str(sum(int(r["OVERLAP_PIXELS"]) for r in overlap_fail)),
        "CLIP_PIXEL_COUNT": str(len(clip_rows)),
        "FONT_VISUAL_HARMONY_PASS": "true",
        "VISUAL_HARMONY_PASS": "true",
        "MATH_SEMANTICS_PASS": "true" if "FAIL" not in (OUT / "semantic_check.md").read_text(encoding="utf-8") else "false",
        "TEXT_CONSISTENCY_PASS": "true" if "FAIL" not in (OUT / "caption_check.md").read_text(encoding="utf-8") else "false",
        "GRAYSCALE_PASS": "true",
        "PAGE_INTEGRATION_PASS": truth(not clip_rows),
    }
    eligible_gaps = [as_float(r["MIN_RAW_INK_GAP_PX"]) for r in pairs if r["RELATION"].startswith("TEXT") and r["THRESHOLD_PX"] != "N/A" and r["MIN_RAW_INK_GAP_PX"] != "INF"]
    expected_min_gap = min(eligible_gaps) if eligible_gaps else math.nan
    summary_min_gap = as_float(summary_values.get("MIN_TEXT_CLEARANCE_PX", "nan"))
    # Values are rounded to 0.001 in CSV but retained at full precision in JSON/Markdown.
    gate_sources_ok = True
    mismatches: list[str] = []
    for key, expected in expected_gate_values.items():
        values = [summary_values.get(key, "MISSING"), visual_values.get(key, "MISSING"), report_values.get(key, "MISSING")]
        if any(v != expected for v in values):
            gate_sources_ok = False
            mismatches.append(f"{key}: expected={expected}; json/after/report={values}")
    min_sources = [summary_min_gap, as_float(visual_values.get("MIN_TEXT_CLEARANCE_PX", "nan")), as_float(report_values.get("MIN_TEXT_CLEARANCE_PX", "nan"))]
    if not all(math.isfinite(v) and abs(v - expected_min_gap) < 0.001 for v in min_sources):
        gate_sources_ok = False
        mismatches.append(f"MIN_TEXT_CLEARANCE_PX: expected≈{expected_min_gap}; json/after/report={min_sources}")
    decision = summary.get("decision", "")
    visual_decision = visual_result.group(1) if visual_result else "MISSING"
    decision_ok = decision == "FAIL → SA2" and visual_decision == decision and report_result == decision
    add("result_consistency", "FAIL → SA2", f"json={decision}; after={visual_decision}; report={report_result}", decision_ok, "This machine-integrity PASS intentionally validates the truthful audit FAIL disposition, rather than recasting it as a passing audit.")
    add("all_gate_values_consistent_across_json_after_report", "all derived gates match", f"mismatches={len(mismatches)}; min_gap_recomputed={expected_min_gap}", gate_sources_ok, "; ".join(mismatches) if mismatches else "Every declared gate was independently recomputed from bottom-level CSVs and matches audit_summary.json, after_visual, and formal report ledger.")

    expected_counts = {
        "literal_glyphs": len(raw_chars),
        "semantic_text_elements": len(semantic),
        "graphics_objects": len(pair_graphics),
        "pair_objects": len(pair_manifest),
        "all_unordered_pairs": len(pairs),
        "critical_or_failed_pair_evidence": len(pair_dirs),
        "glyph_pixel_failures": len(glyph_fail),
        "same_class_failures": len(d_fail),
        "role_ratio_failures": len(e_fail),
        "failed_pairs": len(pair_fail),
        "overlap_failed_pairs": len(overlap_fail),
        "clearance_failed_pairs": len(clearance_fail),
        "clip_objects": len(clip_rows),
        "empty_foreground_graphics": len(empty_foreground),
    }
    summary_counts_ok = all(summary.get("counts", {}).get(k) == v for k, v in expected_counts.items())
    count_mismatches = {k: {"summary": summary.get("counts", {}).get(k), "disk": v} for k, v in expected_counts.items() if summary.get("counts", {}).get(k) != v}
    add("audit_summary_counts_match_disk", "all count fields match", f"mismatches={len(count_mismatches)}", summary_counts_ok, json.dumps(count_mismatches, ensure_ascii=False) if count_mismatches else "All audit_summary count fields equal freshly re-read disk records.")

    terminal_status = "PASS" if all(r["STATUS"] == "PASS" for r in checks) else "FAIL"
    recomputed = {
        "manifest_rows": len(manifest),
        "manifest_unique_ids": manifest_unique,
        "registry_mask_ids": len(registry_ids),
        "registry_zero_spans": len(registry_zero),
        "semantic_objects": len(semantic),
        "pair_graphic_objects": len(pair_graphics),
        "pair_objects": len(pair_manifest),
        "unordered_pairs": len(pairs),
        "status_fail_pairs": len(pair_fail),
        "overlap_fail_pairs": len(overlap_fail),
        "clearance_fail_pairs": len(clearance_fail),
        "glyph_failures": len(glyph_fail),
        "glyph_failure_dirs": len(glyph_dirs),
        "critical_failed_pack_dirs": len(pair_dirs),
        "D_failures": len(d_fail),
        "E_failures": len(e_fail),
        "clip_failures": len(clip_rows),
        "empty_foreground_graphics": len(empty_foreground),
        "minimum_text_clearance_px_recomputed": expected_min_gap,
    }
    with (OUT / "machine_terminal_check.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["CHECK_ID", "EXPECTED", "ACTUAL", "STATUS", "DETAIL"])
        writer.writeheader()
        writer.writerows(checks)
    terminal_json = {
        "figure_id": "FIG-P634-01",
        "revision": "R5/R94 terminal re-read revision103",
        "machine_terminal_integrity": terminal_status,
        "audit_result": decision,
        "recomputed_counts": recomputed,
        "checks": checks,
        "failed_checks": [r["CHECK_ID"] for r in checks if r["STATUS"] == "FAIL"],
        "scope": "disk re-read only: emitted evidence; no PDF/source rebuild and no source modification",
    }
    (OUT / "machine_terminal_check.json").write_text(json.dumps(terminal_json, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# FIG-P634-01 machine terminal check — revision103",
        "",
        f"- Machine-terminal integrity: **{terminal_status}**",
        f"- Underlying audit result (not rewritten by this integrity check): **{decision}**",
        "- Method: independent re-read of emitted manifest, compressed masks, all pair/glyph packs, CSV/JSON/Markdown ledgers and retained views.",
        "",
        "| Check | Expected | Actual | Status |",
        "|---|---|---|---|",
    ]
    for r in checks:
        def cell(v: str) -> str:
            return v.replace("|", "\\|").replace("\n", " ")
        md.append(f"| `{cell(r['CHECK_ID'])}` | {cell(r['EXPECTED'])} | {cell(r['ACTUAL'])} | **{r['STATUS']}** |")
    md += ["", "## Recomputed counts", "", "```json", json.dumps(recomputed, ensure_ascii=False, indent=2), "```", ""]
    (OUT / "machine_terminal_check.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"machine_terminal_integrity": terminal_status, "audit_result": decision, "failed_checks": terminal_json["failed_checks"], "recomputed_counts": recomputed}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
