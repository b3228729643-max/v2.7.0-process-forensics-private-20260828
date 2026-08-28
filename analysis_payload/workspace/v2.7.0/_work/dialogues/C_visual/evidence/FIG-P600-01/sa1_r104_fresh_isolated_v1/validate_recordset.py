from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa1_r104_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
PDF_SHA = "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641"


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest().upper()


def assert_ids(data: list[dict[str, str]], field: str, prefix: str, count: int, width: int = 4) -> None:
    expected = [f"{prefix}{i:0{width}d}" for i in range(1, count + 1)]
    actual = [r[field] for r in data]
    assert actual == expected, (field, len(actual), actual[:3], actual[-3:])


def main() -> None:
    checks: dict[str, object] = {}
    assert PDF.stat().st_size == 4_967_222
    assert file_sha(PDF) == PDF_SHA
    checks["official_pdf_identity"] = "PASS"

    glyph_machine = rows("machine/glyph_machine_inventory.csv")
    glyph_manual = rows("ledgers/manual_glyph_reviewer_ledger.csv")
    assert_ids(glyph_machine, "GLYPH_ID", "GLY", 197)
    assert_ids(glyph_manual, "GLYPH_ID", "GLY", 197)
    for machine, manual in zip(glyph_machine, glyph_manual):
        assert manual["CHAR"] == machine["CHAR"] and manual["CODEPOINT"] == machine["CODEPOINT"]
        assert manual["ACTUALLY_OPENED"] == "true"
        assert manual["ORIGINAL_MATCH"] == manual["OVERLAY_COMPLETE"] == manual["MASK_ONLY_PURE"] == "true"
        assert manual["MISSING_STROKE_PX"] == manual["FOREIGN_PIXEL_PX"] == "0"
        assert manual["TOFU_OR_WRONG_GLYPH"] == "false"
        assert manual["ACTUAL_READABILITY"] == "READABLE" and manual["R168_DECISION"] == "PASS"
        assert manual["NOTE"].strip()
    checks["glyph_manual_rows"] = 197

    graphic_machine = rows("machine/graphic_machine_inventory.csv")
    graphic_manual = rows("ledgers/manual_graphic_reviewer_ledger.csv")
    assert len(graphic_machine) == len(graphic_manual) == 18
    assert [r["GRAPHIC_ID"] for r in graphic_machine] == [r["GRAPHIC_ID"] for r in graphic_manual]
    for m in graphic_machine:
        assert m["EMPTY_MASK"] == "False" and int(m["RAW_MASK_PIXEL_COUNT"]) > 0
    for m in graphic_manual:
        assert m["ACTUALLY_OPENED"] == "true" and m["DECISION"] == "PASS"
        assert m["ORIGINAL_MATCH"] == m["OVERLAY_COMPLETE"] == m["MASK_ONLY_PURE"] == "true"
        assert m["EMPTY_MASK"] == "false" and m["NOTE"].strip()
    checks["graphic_manual_rows"] = 18

    objects = rows("machine/object_machine_inventory.csv")
    assert len(objects) == 29 and len({r["OBJECT_ID"] for r in objects}) == 29
    assert all(int(r["RAW_MASK_PIXEL_COUNT"]) > 0 for r in objects)
    checks["object_denominator"] = 29

    pair_machine = rows("machine/all_unordered_pairs_machine.csv")
    pair_manual = rows("ledgers/manual_pair_reviewer_ledger.csv")
    assert_ids(pair_machine, "PAIR_ID", "PAIR", 406)
    assert_ids(pair_manual, "PAIR_ID", "PAIR", 406)
    critical = []
    for machine, manual in zip(pair_machine, pair_manual):
        assert int(machine["RAW_INTERSECTION_PIXEL_COUNT"]) == 0
        assert manual["ACTUALLY_REVIEWED"] == "true" and manual["MANUAL_DECISION"] == "PASS"
        assert manual["ILLEGAL_OVERLAP_PX"] == "0" and manual["NOTE"].strip()
        assert abs(float(machine["MIN_RAW_MASK_CLEARANCE_PX"]) - float(manual["MEASURED_CLEARANCE_PX"])) < 0.00011
        if machine["MACHINE_CRITICAL_LT12_OR_INTERSECTION"] == "True":
            critical.append(machine)
    assert len(critical) == 29
    checks["all_unordered_pairs"] = 406
    checks["pair_intersection_candidates"] = 0
    checks["critical_pair_rows"] = 29

    for rel, expected in (
        ("ledgers/manual_clip_reviewer_ledger.csv", 29),
        ("ledgers/manual_view_hard_gate_ledger.csv", 5),
        ("ledgers/manual_source_font_reviewer_ledger.csv", 8),
        ("ledgers/manual_peer_role_reviewer_ledger.csv", 11),
        ("ledgers/manual_semantic_reviewer_ledger.csv", 12),
        ("ledgers/manual_r168_advisory_ledger.csv", 12),
    ):
        data = rows(rel)
        assert len(data) == expected and all(all(v.strip() for v in r.values()) for r in data)
        checks[rel] = expected
    assert all(r["CLIP_PIXEL_COUNT"] == "0" and r["DECISION"] == "PASS" for r in rows("ledgers/manual_clip_reviewer_ledger.csv"))

    expected_file_counts = {
        "glyph_cards": 197,
        "glyph_native": 197 * 4,
        "glyph_contact_sheets": 17,
        "graphic_cards": 18,
        "graphic_native": 18 * 5,
        "graphic_contact_sheets": 2,
        "pair_cards": 29,
        "pair_native": 29 * 6,
    }
    for dirname, expected in expected_file_counts.items():
        count = sum(1 for p in (ROOT / dirname).iterdir() if p.is_file())
        assert count == expected, (dirname, count, expected)
    checks["ordinary_file_counts"] = expected_file_counts

    expected_pair_cards = {Path(r["CRITICAL_CARD"]).name for r in critical}
    actual_pair_cards = {p.name for p in (ROOT / "pair_cards").glob("*.png")}
    assert actual_pair_cards == expected_pair_cards
    for r in critical:
        pid = r["PAIR_ID"]
        for suffix in ("original_1x", "a_mask_1x", "b_mask_1x", "intersection_1x", "overlay_1x", "overlay_8x_nearest"):
            assert (ROOT / "pair_native" / f"{pid}_{suffix}.png").is_file()

    pngs = sorted(ROOT.rglob("*.png"))
    for p in pngs:
        with Image.open(p) as im:
            im.verify()
    checks["png_files_opened_by_machine_crosscheck"] = len(pngs)

    required = [
        "IDENTITY.md", "after_visual_acceptance.md", "RESULT.md",
        "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png",
        "grayscale_300dpi.png", "after_text_measurement_overlay_300dpi.png",
        "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv",
    ]
    assert all((ROOT / rel).is_file() for rel in required)
    checks["required_schema_named_payloads"] = required

    summary = {
        "status": "PASS",
        "uid": "FIG-P600-01",
        "handoff_id": "C-FIG-P600-01-R104-SA1-FRESH-ISOLATED-V1",
        "tex": "DISABLED",
        "source_writer": "NONE",
        "manual_decision_generated_by_machine": False,
        "overlap_pixel_count": 0,
        "clip_pixel_count": 0,
        "hard_failure_ids": [],
        "sa1_result": "SA1_PASS_REQUEST_FRESH_ISOLATED_SA3",
        "checks": checks,
    }
    (ROOT / "machine" / "final_crosscheck.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
