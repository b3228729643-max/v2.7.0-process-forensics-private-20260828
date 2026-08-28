"""Close the R8 contact-sheet coverage ledger from explicit glyph reviews.

No visual outcome is inferred here: the source is the already completed
per-GLYPH_ID reviewer ledger after the 14 actual 8x contact sheets were opened.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "PATH_ISOLATED_R8_CID_KNOCKOUT_AUTHORITY_SAFE"
COVERAGE = ROOT / "glyph_contact_sheet_coverage.csv"
REVIEW = ROOT / "glyph_manual_review.csv"
IDENTITY = ROOT / "glyph_manual_review_identity.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, values: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(values)


def main() -> None:
    coverage = read_csv(COVERAGE)
    review = read_csv(REVIEW)
    if len(coverage) != 193 or len(review) != 193:
        raise SystemExit("coverage/review must each have exactly 193 rows")
    by_id = {row["GLYPH_ID"]: row for row in review}
    if len(by_id) != 193 or set(by_id) != {row["GLYPH_ID"] for row in coverage}:
        raise SystemExit("contact coverage and manual review ID sets differ")
    for row in coverage:
        manual = by_id[row["GLYPH_ID"]]
        if any(manual[field] != "PASS" for field in ("ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE", "DECISION")):
            raise SystemExit(f"manual review not PASS: {row['GLYPH_ID']}")
        if manual["MISSING_STROKE_PX"] != "0" or manual["FOREIGN_PIXEL_PX"] != "0":
            raise SystemExit(f"manual mask issue: {row['GLYPH_ID']}")
        if manual["SHEET"] != row["SHEET"] or manual["CELL"] != row["CELL_INDEX"]:
            raise SystemExit(f"sheet/cell mismatch: {row['GLYPH_ID']}")
        row["MANUAL_8X_REVIEW"] = "PASS"
        row["MANUAL_NOTE"] = (
            f"Explicit SA1 8x record: reviewer={manual['REVIEWER']}; "
            f"original={manual['ORIGINAL_MATCH']}; overlay={manual['OVERLAY_COMPLETE']}; "
            f"mask_only={manual['MASK_ONLY_PURE']}; missing={manual['MISSING_STROKE_PX']}; "
            f"foreign={manual['FOREIGN_PIXEL_PX']}; decision={manual['DECISION']}; {manual['NOTE']}"
        )
    write_csv(COVERAGE, coverage, list(coverage[0]))
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
    identity["status"] = "REVIEW_COMPLETE_EXPLICIT_193_GLYPH_8X_RECORDS"
    identity["review_ledger"] = "glyph_manual_review.csv"
    identity["contact_sheet_coverage"] = "glyph_contact_sheet_coverage.csv"
    IDENTITY.write_text(json.dumps(identity, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "schema": "R8_CONTACT_SHEET_MANUAL_SYNC_V1",
        "evidence_identity_sha256": identity["evidence_identity_sha256"],
        "coverage_rows": len(coverage),
        "unique_glyph_ids": len(by_id),
        "reviewed_sheet_count": len({row['SHEET'] for row in coverage}),
        "manual_review_pass_count": sum(row["MANUAL_8X_REVIEW"] == "PASS" for row in coverage),
        "pending_count": 0,
        "result": "PASS",
    }
    (ROOT / "contact_sheet_manual_sync_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
