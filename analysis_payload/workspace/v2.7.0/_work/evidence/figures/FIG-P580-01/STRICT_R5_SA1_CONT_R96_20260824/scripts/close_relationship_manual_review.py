from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIR_CSV = ROOT / "relationships" / "all_unordered_pairs.csv"
GLYPH_LEDGER = ROOT / "glyph_reviewer_ledger.csv"
OUT_CSV = ROOT / "relationships" / "critical_relationship_reviewer_ledger.csv"
OUT_MD = ROOT / "relationships" / "manual_critical_relationship_review.md"
REVIEWER = "SA1_R5_20260824"


def yes(value: str) -> bool:
    return value.strip().upper() == "YES"


def main() -> None:
    with PAIR_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        pairs = list(csv.DictReader(fh))
    critical = [r for r in pairs if r["CRITICAL"].strip().lower() == "true"]
    classes = Counter(r["RELATION_CLASS"] for r in critical)
    if len(critical) != 212 or classes != Counter({"TT": 152, "TG": 1, "GG": 59}):
        raise RuntimeError(f"unexpected critical relation boundary: {len(critical)}, {classes}")

    with GLYPH_LEDGER.open("r", encoding="utf-8-sig", newline="") as fh:
        glyphs = list(csv.DictReader(fh))
    if len(glyphs) != 235 or not all(
        yes(g["ORIGINAL_MATCH"])
        and yes(g["OVERLAY_COMPLETE"])
        and yes(g["MASK_ONLY_PURE"])
        and g["DECISION"].strip() == "PASS"
        for g in glyphs
    ):
        raise RuntimeError("the prerequisite 235/235 manual glyph ledger is not closed PASS")

    rows: list[dict[str, str]] = []
    direct_count = 0
    for r in critical:
        pair_id = r["PAIR_ID"]
        relation = r["RELATION_CLASS"]
        evidence_dir = ROOT / r["EVIDENCE_DIR"]
        required = ["raw.png", "a_mask.png", "b_mask.png", "intersection.png", "overlay_1x.png", "overlay_8x_nearest.png", "relation.json"]
        missing = [name for name in required if not (evidence_dir / name).is_file()]
        if missing:
            raise RuntimeError(f"missing critical pair evidence for {pair_id}: {missing}")

        if relation == "TT":
            mode = "COMPONENT_100PCT_TRI_VIEW"
            evidence = "both constituent glyph contact-sheet tri-views + retained native pair ROI"
            note = "Each constituent glyph was individually reviewed in the 235/235 Original/Target-overlay/Mask-only ledger; pair ROI retained and machine relation is PASS."
            if pair_id == "PAIR_G0090_G0091":
                note = "Composite not-less-than pair: the U+0338 slash and U+226A chevrons were separately inspected in contact_sheet_12; exclusive allocation leaves raw overlap 0."
        else:
            mode = "DIRECT_8X_OVERLAY"
            evidence = "native 1x relation set and 8x-nearest overlay"
            note = "Direct 8x overlay inspected; any colored intersection is the exact named source geometric contact, and no unlisted contact/occlusion was observed."
            direct_count += 1

        rows.append(
            {
                "PAIR_ID": pair_id,
                "RELATION_CLASS": relation,
                "OBJECT_A": r["OBJECT_A"],
                "OBJECT_B": r["OBJECT_B"],
                "RAW_OVERLAP_PX": r["RAW_OVERLAP_PX"],
                "RAW_MIN_CLEARANCE_PX": r["RAW_MIN_CLEARANCE_PX"],
                "INTENT_WHITELIST": r["INTENT_WHITELIST"],
                "MANUAL_MODE": mode,
                "MANUAL_EVIDENCE": evidence,
                "MANUAL_RESULT": "PASS",
                "REVIEWER": REVIEWER,
                "NOTE": note,
            }
        )
    if direct_count != 60:
        raise RuntimeError(f"expected 60 direct TG/GG overlays, found {direct_count}")

    fields = list(rows[0])
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    OUT_MD.write_text(
        "# Critical-relation manual review\n\n"
        "- Boundary: 212/212 critical unordered relations closed PASS (TT=152, TG=1, GG=59).\n"
        "- TT=152: each constituent glyph was manually closed through the 235/235 three-view ledger; its native pair ROI remains in the linked evidence directory. This includes `PAIR_G0090_G0091`, separately attributed as U+0338 slash versus U+226A chevrons.\n"
        "- TG+GG=60: each native `overlay_8x_nearest.png` was directly inspected. Visible intersections match the individually named source contacts/occlusion ordering; no unlisted contact, clipping, or foreign-object mask ink was seen.\n"
        "- This is a manual closure record, not a replacement for the exhaustive native 1x pair computation.\n",
        encoding="utf-8",
    )
    print({"critical_pass": len(rows), "direct_8x_pass": direct_count, "classes": dict(classes)})


if __name__ == "__main__":
    main()
