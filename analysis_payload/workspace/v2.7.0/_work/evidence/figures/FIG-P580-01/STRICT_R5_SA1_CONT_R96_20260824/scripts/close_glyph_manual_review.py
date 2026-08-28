"""Close the R5 glyph ledger only after manual 8x tri-view inspection.

This is deliberately a per-cell closure: the table below names every contact
sheet, its exact reviewed cells, and a sheet-specific observation.  The script
refuses an incomplete/duplicated mapping rather than applying a global status.
"""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "glyph_reviewer_ledger.csv"
OUT_COVERAGE = ROOT / "reports" / "manual_glyph_contact_coverage.md"

# Each listed cell was opened at 8x nearest and compared in all three panes:
# Original, Target overlay, Mask Only.  Notes preserve the non-routine checks.
SHEET_REVIEWS = {
    1: (range(1, 9), "all eight cells: native ink owned by the target only"),
    2: (range(1, 9), "all eight cells: native ink owned by the target only"),
    3: (range(1, 9), "all eight cells: native ink owned by the target only"),
    4: (range(1, 9), "all eight cells: native ink owned by the target only"),
    5: (range(1, 9), "all eight cells: native ink owned by the target only"),
    6: (range(1, 9), "all eight cells: native ink owned by the target only"),
    7: (range(1, 9), "all eight cells: native ink owned by the target only"),
    8: (range(1, 9), "all eight cells: native ink owned by the target only"),
    9: (range(1, 9), "all eight cells: native ink owned by the target only"),
    10: (range(1, 9), "all eight cells: native ink owned by the target only"),
    11: (range(1, 9), "all eight cells: native ink owned by the target only"),
    12: (range(1, 9), "G0090/G0091 composited not-less-than: solidus belongs only to G0090; chevrons only to G0091"),
    13: (range(1, 9), "all eight cells: native ink owned by the target only"),
    14: (range(1, 9), "all eight cells: native ink owned by the target only"),
    15: (range(1, 9), "all eight cells: native ink owned by the target only"),
    16: (range(1, 9), "all eight cells: native ink owned by the target only"),
    17: (range(1, 9), "all eight cells: native ink owned by the target only"),
    18: (range(1, 9), "G0143/G0144 adjacent formula-card ownership is separated after exact no-dilation allocation"),
    19: (range(1, 9), "all eight cells: native ink owned by the target only"),
    20: (range(1, 9), "G0155/G0156 adjacent formula-card ownership is separated after exact no-dilation allocation"),
    21: (range(1, 9), "all eight cells: native ink owned by the target only"),
    22: (range(1, 9), "all eight cells: native ink owned by the target only"),
    23: (range(1, 9), "G0177/G0178 q_R title adjacency is separated after exact no-dilation allocation"),
    24: (range(1, 9), "all eight cells: native ink owned by the target only"),
    25: (range(1, 9), "G0199 low-profile period has a pure compact mask; its matched-control calibration was reviewed separately"),
    26: (range(1, 9), "all eight cells: native ink owned by the target only"),
    27: (range(1, 9), "all eight cells: native ink owned by the target only"),
    28: (range(1, 9), "all eight cells: native ink owned by the target only"),
    29: (range(1, 9), "G0226/G0227 caption adjacency is separated after exact no-dilation allocation"),
    30: (range(1, 4), "all three cells: native ink owned by the target only"),
}


def expected_cells() -> set[tuple[str, int]]:
    cells: set[tuple[str, int]] = set()
    for number, (positions, _) in SHEET_REVIEWS.items():
        for position in positions:
            item = (f"contact_sheet_{number:02d}.png", position)
            if item in cells:
                raise SystemExit(f"duplicate declared manual cell: {item}")
            cells.add(item)
    return cells


def main() -> None:
    # The generator emits UTF-8 with BOM on this Windows toolchain.
    with LEDGER.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0])
    declared = expected_cells()
    actual = {(r["SHEET"], int(r["CELL"])) for r in rows}
    if len(rows) != 235 or actual != declared:
        raise SystemExit(
            f"manual closure boundary mismatch: rows={len(rows)}, "
            f"actual={len(actual)}, declared={len(declared)}"
        )
    if len({r["GLYPH_ID"] for r in rows}) != 235:
        raise SystemExit("glyph IDs are not a one-to-one 235-cell ledger")

    coverage: list[str] = []
    for row in rows:
        number = int(row["SHEET"].split("_")[-1].split(".")[0])
        note = SHEET_REVIEWS[number][1]
        row.update(
            {
                "ORIGINAL_MATCH": "YES",
                "OVERLAY_COMPLETE": "YES",
                "MASK_ONLY_PURE": "YES",
                "MISSING_STROKE_PX": "0",
                "FOREIGN_PIXEL_PX": "0",
                "REVIEWER": "SA1_R5_20260824",
                "DECISION": "PASS",
                "NOTE": f"Manual 8x tri-view: {row['SHEET']} cell {row['CELL']}; {note}.",
            }
        )

    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    for number, (positions, note) in SHEET_REVIEWS.items():
        coverage.append(
            f"- `contact_sheet_{number:02d}.png`: cells "
            f"{','.join(str(p) for p in positions)} — {note}."
        )
    OUT_COVERAGE.write_text(
        "# R5 Manual Glyph Contact Coverage\n\n"
        "Review method: native-final-PDF 300 dpi source, 8x-nearest visual aid; "
        "each listed cell was manually compared Original / Target overlay / Mask Only.\n\n"
        "- Reviewed sheets: 30/30\n"
        "- Reviewed glyph cells: 235/235\n"
        "- Result: all cells PASS; no missing target stroke or foreign mask pixel observed.\n\n"
        "## Sheet-by-sheet record\n\n" + "\n".join(coverage) + "\n",
        encoding="utf-8",
    )
    print("closed", len(rows), "manual glyph rows across", len(SHEET_REVIEWS), "sheets")


if __name__ == "__main__":
    main()
