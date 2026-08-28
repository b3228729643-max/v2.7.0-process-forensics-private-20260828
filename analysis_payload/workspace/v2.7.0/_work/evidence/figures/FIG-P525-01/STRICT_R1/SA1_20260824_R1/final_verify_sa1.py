#!/usr/bin/env python3
"""Read-only cross-file consistency check for the completed SA1 evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path


OUT = Path(__file__).resolve().parent


def load_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    summary = json.loads((OUT / "strict_audit_summary.json").read_text(encoding="utf-8"))
    reconciliation = json.loads((OUT / "overlap_reconciliation.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "render_manifest.json").read_text(encoding="utf-8"))
    font = load_csv("after_font_audit.csv")
    pixel = load_csv("after_pixel_measurements.csv")
    relations = load_csv("after_overlap_report.csv")
    formal = load_csv("strict_eight_column_report.csv")
    result = (OUT / "SA1_RESULT.md").read_text(encoding="utf-8")
    visual = (OUT / "after_visual_acceptance.md").read_text(encoding="utf-8")

    font_failures = [row for row in font if row["SOURCE_FONT_PASS"] == "false"]
    overlap_failures = [row for row in relations if int(row["OVERLAP_PIXEL_COUNT"]) > 0]
    expected_pairs = [("REL_0164", 88), ("REL_0177", 126), ("REL_0191", 170), ("REL_0272", 3)]
    required_artifacts = [
        "full_page_200dpi.png", "full_page_300dpi_native.png", "figure_crop_300dpi.png",
        "standalone_300dpi.png", "grayscale_300dpi.png", "after_text_measurement_overlay_300dpi.png",
        "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv",
        "glyph_inventory.csv", "semantic_component_inventory.csv", "graphic_component_inventory.csv",
        "mask_manifest.csv", "critical_artifacts.csv", "strict_eight_column_report.csv",
        "strict_audit_summary.json", "render_manifest.json", "math_semantics_recheck.md",
        "shared_style_font_context.tex", "overlap_reconciliation.json", "overlap_reconciliation.csv",
        "SA1_RESULT.md", "after_visual_acceptance.md", "final_integrity_check.md",
    ]
    checks = {
        "required_artifacts_present": all((OUT / name).is_file() for name in required_artifacts),
        "sha256_present": len(manifest["frozen_pdf_sha256"]) == 64,
        "ordinary_node_effective_10pt": manifest["effective_font_provenance"]["ordinary_node_effective_pt"] == 10.0,
        "source_font_only_explicit_legends_fail": len(font_failures) == 19 and set(row["PARENT_ELEMENT_ID"] for row in font_failures) == {"SEM_LEGEND_TOPIC", "SEM_LEGEND_DOCUMENT"},
        "source_font_counts_match_summary": summary["hard_gates"]["SOURCE_FONT_FAILURE_COUNT"] == 19 and summary["hard_gates"]["SOURCE_FONT_FAILURE_COMPONENT_COUNT"] == 2,
        "pixel_failure_count_matches": sum(row["PIXEL_HEIGHT_PASS"] == "false" for row in pixel) == 11 and summary["hard_gates"]["PIXEL_HEIGHT_PASS"] is False,
        "failed_overlap_pairs_exact": [(row["RELATION_ID"], int(row["OVERLAP_PIXEL_COUNT"])) for row in overlap_failures] == expected_pairs,
        "unique_overlap_accounted": reconciliation["status"] == "PASS" and reconciliation["unique_overlap_pixels"] == reconciliation["pair_sum_overlap_pixels"] == 387 and reconciliation["duplicate_pixels_across_failed_pairs"] == 0,
        "clip_zero": reconciliation["all_registered_relation_clip_pixels"] == 0 and summary["hard_gates"]["CLIP_PIXEL_COUNT"] == 0,
        "critical_pair_artifacts_complete": all(all((OUT / "critical" / f"{row['RELATION_ID']}_{suffix}.png").is_file() for suffix in ("raw", "mask_a", "mask_b", "overlap", "overlay", "overlay_8x")) for row in overlap_failures),
        "formal_report_final_fail": next(row for row in formal if row["CHECK_ID"] == "R19")["STATUS"] == "FAIL" and "unique=387" in next(row for row in formal if row["CHECK_ID"] == "R10")["OBSERVED"],
        "reports_reflect_corrections": all(fragment in result and fragment in visual for fragment in ("8.8/10.0=0.8800", "pair-sum=unique=387", "det(Phi)=0.4288")),
        "no_old_normal_9_4_failure": not any(fragment in text for text in (result, visual) for fragment in ("8.8/9.4", "9.4pt base", "base=9.4pt")),
        "final_route": summary["result"] == "FAIL" and summary["handoff"] == "SA2",
    }
    payload = {
        "audit_id": summary["audit_id"],
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    (OUT / "final_consistency_check.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if payload["status"] != "PASS":
        raise SystemExit("final consistency check FAILED")


if __name__ == "__main__":
    main()
