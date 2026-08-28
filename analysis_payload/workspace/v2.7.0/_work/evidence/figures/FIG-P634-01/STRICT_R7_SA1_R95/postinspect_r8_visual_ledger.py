"""Join explicit four-view reviewer records to the R8 visual-harmony template.

The completion CSV is a manual transcription of the four images actually opened
by SA1.  This utility only verifies one row per view/panel/role/script and
copies the reviewer-entered findings; it does not infer visual PASS values from
the renderer, masks, or measurement gates.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "PATH_ISOLATED_R8_CID_KNOCKOUT_AUTHORITY_SAFE"
TEMPLATE = ROOT / "manual_visual_harmony_ledger.csv"
MANUAL = ROOT / "manual_visual_harmony_completion.csv"
PIXELS = ROOT / "after_pixel_measurements.csv"
IDENTITY = ROOT / "glyph_manual_review_identity.json"

KEY = ("VIEW_ID", "ELEMENT_ID", "SCRIPT_CLASS")
MANUAL_FIELDS = (
    "REVIEWER", "VIEW_OPENED", "FONT_SIZE_HARMONY", "WEIGHT_FAMILY_HARMONY",
    "BASELINE_ALIGNMENT", "GRAY_HIERARCHY", "PAGE_INTEGRATION",
    "CROWDING_OR_INTRUSION", "CROSS_PANEL_CONSISTENCY", "DECISION", "NOTE",
)
JUDGEMENT_FIELDS = MANUAL_FIELDS[1:-1]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def key(row: dict[str, str]) -> tuple[str, str, str]:
    return tuple(row[name] for name in KEY)  # type: ignore[return-value]


def write_rows(path: Path, values: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(values)


def main() -> None:
    template = rows(TEMPLATE)
    manual = rows(MANUAL)
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))["evidence_identity_sha256"]
    if len(template) != 192 or len(manual) != 192:
        raise SystemExit("expected exactly 192 template and 192 explicit manual visual rows")
    template_keys = [key(row) for row in template]
    manual_keys = [key(row) for row in manual]
    if len(set(template_keys)) != 192 or len(set(manual_keys)) != 192:
        raise SystemExit("visual ledger keys must be unique")
    if set(template_keys) != set(manual_keys):
        raise SystemExit("manual/template view-element-script key sets differ")
    manual_by_key = {key(row): row for row in manual}

    out: list[dict[str, str]] = []
    for base in template:
        item = manual_by_key[key(base)]
        if any(not item.get(field, "").strip() for field in MANUAL_FIELDS):
            raise SystemExit(f"empty manual visual field for {key(base)}")
        if any(item[field] == "PENDING" or item[field] == "UNKNOWN" for field in MANUAL_FIELDS):
            raise SystemExit(f"pending/unknown manual visual field for {key(base)}")
        if item["VIEW_OPENED"] != "PASS":
            raise SystemExit(f"view was not explicitly opened for {key(base)}")
        if any(item[field] not in {"PASS", "FAIL"} for field in JUDGEMENT_FIELDS):
            raise SystemExit(f"invalid visual judgement for {key(base)}")
        base.update({field: item[field] for field in MANUAL_FIELDS})
        base["EVIDENCE_IDENTITY_SHA256"] = identity
        out.append(base)

    views = {row["VIEW_ID"] for row in out}
    if views != {"FULL_PAGE_200DPI", "FIGURE_CROP_300DPI", "STANDALONE_300DPI", "GRAYSCALE_300DPI"}:
        raise SystemExit(f"four-view coverage mismatch: {sorted(views)}")
    if any(sum(1 for row in out if row["VIEW_ID"] == view) != 48 for view in views):
        raise SystemExit("each view must carry exactly 48 panel/role/script reviews")

    # Cross-consistency only: every semantic pixel-gate failure needs a distinct
    # recorded visual size failure in every actual view; no verdict is generated
    # here from the pixel CSV.
    semantic_fails = {
        (row["ELEMENT_ID"].split(":", 1)[0], row["SCRIPT_CLASS"])
        for row in rows(PIXELS)
        if row["AUDIT_LEVEL"] == "SEMANTIC_ELEMENT" and row["PASS_FAIL"] == "FAIL"
    }
    visual_size_fails = {
        (row["ELEMENT_ID"], row["SCRIPT_CLASS"])
        for row in out
        if row["FONT_SIZE_HARMONY"] == "FAIL"
    }
    if semantic_fails != visual_size_fails:
        raise SystemExit(
            f"manual visual size-fail groups {sorted(visual_size_fails)} do not match "
            f"semantic pixel-fail groups {sorted(semantic_fails)}"
        )
    if any(row["DECISION"] != "FAIL" for row in out if row["FONT_SIZE_HARMONY"] == "FAIL"):
        raise SystemExit("size-harmony failures require explicit visual FAIL verdict")

    write_rows(TEMPLATE, out, list(template[0]))
    manifest = {
        "schema": "R8_POSTINSPECTION_VISUAL_LEDGER_JOIN_V1",
        "evidence_identity_sha256": identity,
        "template_row_count": len(template),
        "manual_input_row_count": len(manual),
        "unique_view_element_script_count": len(set(manual_keys)),
        "views": sorted(views),
        "rows_per_view": 48,
        "pending_or_unknown_count": 0,
        "manual_visual_fail_count": sum(row["DECISION"] == "FAIL" for row in out),
        "font_visual_harmony_pass": not any(row["FONT_SIZE_HARMONY"] == "FAIL" for row in out),
        "decision_source": "manual_visual_harmony_completion.csv; explicit reviewer records after opening four views",
        "result": "PASS",
    }
    (ROOT / "manual_visual_harmony_join_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
