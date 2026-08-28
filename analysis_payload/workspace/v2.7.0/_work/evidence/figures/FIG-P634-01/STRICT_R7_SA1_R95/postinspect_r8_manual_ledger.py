"""Join reviewer-entered R8 glyph observations to the immutable template.

This utility does not derive a pass/fail from masks or machine gates.  It only
validates and transcribes the 193 explicitly recorded observations made after
opening the 14 canonical 8x contact sheets.  The native-height failures remain
in the independent measurement CSV and are deliberately not converted into
mask-review failures here.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "PATH_ISOLATED_R8_CID_KNOCKOUT_AUTHORITY_SAFE"
TEMPLATE = ROOT / "glyph_manual_review.csv"
MANUAL = ROOT / "manual_glyph_review_completion.csv"
MAPPING = ROOT / "glyph_shape_mapping.csv"
IDENTITY = ROOT / "glyph_manual_review_identity.json"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, values: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(values)


def main() -> None:
    template = rows(TEMPLATE)
    manual = rows(MANUAL)
    mapping = {r["GLYPH_ID"]: r for r in rows(MAPPING)}
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
    identity_hash = identity["evidence_identity_sha256"]

    if len(template) != 193 or len(manual) != 193:
        raise SystemExit("expected exactly 193 template and 193 manually-recorded rows")
    if len({r["GLYPH_ID"] for r in template}) != 193 or len({r["GLYPH_ID"] for r in manual}) != 193:
        raise SystemExit("glyph IDs must be unique in both ledgers")

    by_id = {r["GLYPH_ID"]: r for r in manual}
    if set(by_id) != {r["GLYPH_ID"] for r in template} or set(by_id) != set(mapping):
        raise SystemExit("manual/template/mapping glyph ID sets differ")

    expected_fields = [
        "REVIEWER", "SHEET", "CELL", "ORIGINAL_MATCH", "OVERLAY_COMPLETE",
        "MASK_ONLY_PURE", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX", "DECISION", "NOTE",
    ]
    out: list[dict[str, str]] = []
    for base in template:
        item = by_id[base["GLYPH_ID"]]
        if any(not item.get(field, "").strip() for field in expected_fields):
            raise SystemExit(f"empty manual field for {base['GLYPH_ID']}")
        if item["SHEET"] != base["SHEET"] or item["CELL"] != base["CELL"]:
            raise SystemExit(f"sheet/cell mismatch for {base['GLYPH_ID']}")
        if any(item[key] != "PASS" for key in ("ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE", "DECISION")):
            raise SystemExit(f"non-PASS manual tri-view result for {base['GLYPH_ID']}")
        if item["MISSING_STROKE_PX"] != "0" or item["FOREIGN_PIXEL_PX"] != "0":
            raise SystemExit(f"nonzero manual mask issue for {base['GLYPH_ID']}")
        mapped = mapping[base["GLYPH_ID"]]
        base.update({key: item[key] for key in expected_fields})
        base["EVIDENCE_IDENTITY_SHA256"] = identity_hash
        base["NOTE"] = (
            f"{item['NOTE']} Exact CHAR={mapped['EXPECTED_CHAR']}; "
            f"PARENT={mapped['PARENT_ID']}; manual R8 8x tri-view record."
        )
        out.append(base)

    if any("PENDING" in str(value) for row in out for value in row.values()):
        raise SystemExit("PENDING may not remain after manual transcription")
    write_rows(TEMPLATE, out, list(template[0]))
    manifest = {
        "schema": "R8_POSTINSPECTION_GLYPH_LEDGER_JOIN_V1",
        "evidence_identity_sha256": identity_hash,
        "template_row_count": len(template),
        "manual_input_row_count": len(manual),
        "unique_glyph_id_count": len(by_id),
        "manual_hard_height_note_count": sum("hard FAIL" in r["NOTE"] for r in manual),
        "pending_count": 0,
        "decision_source": "manual_glyph_review_completion.csv; explicit per-GLYPH_ID reviewer records",
        "machine_decision_source": "after_pixel_measurements.csv; independent of mask-review decision",
        "result": "PASS",
    }
    (ROOT / "manual_glyph_review_join_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
