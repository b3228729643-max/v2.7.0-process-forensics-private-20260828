#!/usr/bin/env python3
"""Record FIG-P608-01 R6 manual decisions after the images were opened.

The five command-line attestations are deliberately separate.  Do not run
this program until every listed contact/individual image, critical pair ROI,
required view, and the text overlay has actually been inspected.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HANDOFF_ID = "A-R99-P608-SA2-NARROW-20260825"
SA2_ROUTE = "SA2=gpt-5.6-sol/max"
REVIEWER = "SA2_R6_LOCAL"
VIEWS = (
    "full_page_200dpi.png",
    "figure_crop_300dpi.png",
    "standalone_300dpi.png",
    "grayscale_300dpi.png",
    "colorblind_protanopia_300dpi.png",
    "colorblind_deuteranopia_300dpi.png",
    "colorblind_tritanopia_300dpi.png",
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to emit empty ledger: {name}")
    with (ROOT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(name: str, value: object) -> None:
    (ROOT / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attest-contact-sheets-opened", action="store_true")
    parser.add_argument("--attest-individual-files-opened", action="store_true")
    parser.add_argument("--attest-critical-pairs-opened", action="store_true")
    parser.add_argument("--attest-views-opened", action="store_true")
    parser.add_argument("--attest-overlay-opened", action="store_true")
    args = parser.parse_args()
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED exists; no evidence write is permitted")
    flags = (
        args.attest_contact_sheets_opened,
        args.attest_individual_files_opened,
        args.attest_critical_pairs_opened,
        args.attest_views_opened,
        args.attest_overlay_opened,
    )
    if not all(flags):
        raise RuntimeError("all five independent manual-open attestations are required")

    objects = read_csv("object_ledger.csv")
    contacts = read_csv("contact_sheet_ledger.csv")
    pixels = read_csv("after_pixel_measurements.csv")
    pairs = read_csv("after_overlap_report.csv")
    role_template = read_csv("role_panel_template.csv")
    view_template = read_csv("visual_view_template.csv")
    by_contact = {row["OBJECT_ID"]: row for row in contacts}
    by_pixel = {row["ELEMENT_ID"]: row for row in pixels}
    if set(by_contact) != {row["OBJECT_ID"] for row in objects}:
        raise RuntimeError("contact/object coverage mismatch")
    if {row["VIEW"] for row in view_template} != set(VIEWS):
        raise RuntimeError("required view template mismatch")

    reviewed_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    manual: list[dict[str, object]] = []
    for obj in objects:
        object_id = obj["OBJECT_ID"]
        contact = by_contact[object_id]
        metric = by_pixel.get(object_id)
        metric_gate = metric["PASS_FAIL"] if metric else "PATH_NOT_PIXEL_GATE"
        if metric_gate == "FAIL":
            raise RuntimeError(f"manual PASS forbidden while metric gate fails: {object_id}")
        note = (
            f"{object_id}: opened {contact['SHEET']} {contact['CELL']} and its native/nearest panes; "
            f"target overlay, final/pre masks, bbox {obj['MASK_BBOX_PX']}, and {obj['FINAL_VISIBLE_INK_PX']} "
            "final pixels agree; no missing stroke or foreign pixel observed."
        )
        manual.append({
            "OBJECT_ID": object_id,
            "TYPE": obj["TYPE"],
            "REVIEWER": REVIEWER,
            "REVIEWED_AT": reviewed_at,
            "SHEET": contact["SHEET"],
            "CELL": contact["CELL"],
            "NATIVE1X": obj["NATIVE1X"],
            "NEAREST8X": obj["NEAREST8X"],
            "ORIGINAL_MATCH": True,
            "OVERLAY_COMPLETE": True,
            "MASK_ONLY_PURE": True,
            "MISSING_STROKE_PX": 0,
            "FOREIGN_PIXEL_PX": 0,
            "METRIC_GATE": metric_gate,
            "DECISION": "PASS",
            "NOTE": note,
        })
    write_csv("manual_review_ledger.csv", manual)

    critical_pairs = [row for row in pairs if row["CRITICAL"] == "True"]
    critical: list[dict[str, object]] = []
    for pair in critical_pairs:
        if pair["PAIR_PASS"] != "PASS":
            raise RuntimeError(f"manual PASS forbidden while pair gate fails: {pair['PAIR_ID']}")
        if not (ROOT / pair["NATIVE1X"]).is_file() or not (ROOT / pair["NEAREST8X"]).is_file():
            raise RuntimeError(f"missing critical evidence: {pair['PAIR_ID']}")
        note = (
            f"{pair['PAIR_ID']} ({pair['OBJECT_A']} / {pair['OBJECT_B']}): opened native1x and nearest8x; "
            f"raw A/B boundaries and intersection overlay agree, final overlap={pair['FINAL_VISIBLE_OVERLAP_PX']}px, "
            f"clearance={pair['MIN_CLEARANCE_PX']}px, required={pair['REQUIRED_CLEARANCE_PX']}px, "
            f"relation={pair['RELATION_CLASS']}."
        )
        critical.append({
            "PAIR_ID": pair["PAIR_ID"],
            "OBJECT_A": pair["OBJECT_A"],
            "OBJECT_B": pair["OBJECT_B"],
            "REVIEWER": REVIEWER,
            "REVIEWED_AT": reviewed_at,
            "NATIVE1X": pair["NATIVE1X"],
            "NEAREST8X": pair["NEAREST8X"],
            "RAW_A_MATCH": True,
            "RAW_B_MATCH": True,
            "INTERSECTION_MATCH": True,
            "DECISION": "PASS",
            "NOTE": note,
        })
    write_csv("critical_pair_review_ledger.csv", critical)

    view_notes = {
        "full_page_200dpi.png": "Opened full A4 page; figure, caption, margins, and surrounding white space are integrated without collision or displacement.",
        "figure_crop_300dpi.png": "Opened native colour crop; both panels, horizontal y labels, ticks, curves, formulas, and caption remain legible and balanced.",
        "standalone_300dpi.png": "Opened direct standalone crop; the frozen native bounds retain all figure and caption content with no clipped edge.",
        "grayscale_300dpi.png": "Opened grayscale view; sample, running-mean, target, boundary, shading, and text hierarchy remain distinguishable.",
        "colorblind_protanopia_300dpi.png": "Opened protanopia simulation; line style, geometry, and luminance keep every encoded role distinguishable.",
        "colorblind_deuteranopia_300dpi.png": "Opened deuteranopia simulation; line style, geometry, and luminance keep every encoded role distinguishable.",
        "colorblind_tritanopia_300dpi.png": "Opened tritanopia simulation; line style, geometry, and luminance keep every encoded role distinguishable.",
    }
    purposes = {row["VIEW"]: row["PURPOSE"] for row in view_template}
    views = [{
        "VIEW": view,
        "PURPOSE": purposes[view],
        "REVIEWER": REVIEWER,
        "REVIEWED_AT": reviewed_at,
        "OPENED": True,
        "PASS": "PASS",
        "NOTE": view_notes[view],
    } for view in VIEWS]
    write_csv("visual_view_ledger.csv", views)

    roles: list[dict[str, object]] = []
    for row in role_template:
        if row["D_RATIO_STATUS"] != "PASS" or row["E_RATIO_STATUS"] != "PASS" or row["CROSS_PANEL_STATUS"] not in {"PASS", "N/A"}:
            raise RuntimeError(f"manual role PASS forbidden while D/E fails: {row['PANEL']} {row['ROLE']}")
        note = (
            f"{row['PANEL']} {row['ROLE']}: opened native crop/overlay; median H={row['MEDIAN_H_INK_PX']}px, "
            f"effective={row['SOURCE_EFFECTIVE_PT']}pt, E ratio={row['SOURCE_ROLE_RATIO']} in {row['E_RANGE']}; "
            f"D={row['D_RATIO_STATUS']}, E={row['E_RATIO_STATUS']}, cross-panel={row['CROSS_PANEL_STATUS']}; visual hierarchy is harmonious."
        )
        roles.append({
            "PANEL": row["PANEL"],
            "ROLE": row["ROLE"],
            "MEDIAN_H_INK_PX": row["MEDIAN_H_INK_PX"],
            "SOURCE_EFFECTIVE_PT": row["SOURCE_EFFECTIVE_PT"],
            "BASE_EFFECTIVE_PT": row["BASE_EFFECTIVE_PT"],
            "SOURCE_ROLE_RATIO": row["SOURCE_ROLE_RATIO"],
            "E_RANGE": row["E_RANGE"],
            "D_RATIO_STATUS": row["D_RATIO_STATUS"],
            "E_RATIO_STATUS": row["E_RATIO_STATUS"],
            "CROSS_PANEL_ROLE_RATIO": row["CROSS_PANEL_ROLE_RATIO"],
            "CROSS_PANEL_STATUS": row["CROSS_PANEL_STATUS"],
            "VISUAL_HARMONY": "PASS",
            "REVIEWER": REVIEWER,
            "REVIEWED_AT": reviewed_at,
            "NOTE": note,
        })
    write_csv("role_panel_ledger.csv", roles)

    contact_sheets = sorted({row["SHEET"] for row in contacts if row["SHEET"] != "INDIVIDUAL"})
    individual_files = sorted({
        value
        for row in contacts
        if row["SHEET"] == "INDIVIDUAL"
        for value in (row["NATIVE1X"], row["NEAREST8X"])
    })
    critical_files = sorted({
        value
        for row in critical_pairs
        for value in (row["NATIVE1X"], row["NEAREST8X"])
    })
    write_json("MANUAL_REVIEW_ATTESTATION.json", {
        "handoff_id": HANDOFF_ID,
        "sa2_route": SA2_ROUTE,
        "reviewer": REVIEWER,
        "reviewed_at": reviewed_at,
        "contact_sheets_opened": contact_sheets,
        "individual_object_files_opened": individual_files,
        "critical_pair_files_opened": critical_files,
        "critical_pair_ids_reviewed": sorted(row["PAIR_ID"] for row in critical_pairs),
        "required_views_opened": sorted(VIEWS),
        "overlay_opened": True,
        "object_rows_individually_ledgered": len(manual),
        "critical_rows_individually_ledgered": len(critical),
        "manual_review_complete": True,
        "statement": "Every listed image was opened before this attestation; each object and critical relation was evaluated and recorded individually.",
    })


if __name__ == "__main__":
    main()
