from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R10_SA1_FRESH_R98_20260824")
REPORTS = ROOT / "reports"
EXPECTED_PDF_SHA = "52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41"
EXPECTED_SOURCE_SHA = "DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    if (ROOT / "MANIFEST.csv").exists() or (ROOT / "WSTOP.txt").exists():
        raise RuntimeError("Control files already exist before pre-seal verification")
    files = [p for p in ROOT.rglob("*") if p.is_file()]
    zero = [str(p.relative_to(ROOT)) for p in files if p.stat().st_size == 0]
    if zero:
        raise RuntimeError(f"Zero-byte files: {zero}")
    pngs = [p for p in files if p.suffix.lower() == ".png"]
    bad_png = []
    for path in pngs:
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception as exc:
            bad_png.append(f"{path.relative_to(ROOT)}: {exc}")
    if bad_png:
        raise RuntimeError(f"Unopenable PNGs: {bad_png}")
    pdf_copy = ROOT / "inputs" / "official_R98_main_full.pdf"
    source_copy = ROOT / "inputs" / "direct_source_snapshot.tex"
    if pdf_copy.stat().st_size != 4_934_249 or sha256(pdf_copy) != EXPECTED_PDF_SHA:
        raise RuntimeError("Self-contained PDF copy identity failed")
    if sha256(source_copy) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("Self-contained source copy identity failed")
    with fitz.open(pdf_copy) as doc:
        if doc.page_count != 813:
            raise RuntimeError("Self-contained PDF page count failed")
    counts = {
        "glyph_inventory": len(csv_rows(REPORTS / "glyph_inventory_193.csv")),
        "pixel_measurements": len(csv_rows(REPORTS / "after_pixel_measurements_193.csv")),
        "font_elements": len(csv_rows(REPORTS / "font_audit_21_elements.csv")),
        "primitives": len(csv_rows(REPORTS / "vector_primitive_assignment_71_FINAL.csv")),
        "graphics": sum(r["KIND"] == "GRAPHIC" for r in csv_rows(REPORTS / "semantic_object_inventory_N61.csv")),
        "semantic_objects": len(csv_rows(REPORTS / "semantic_object_inventory_N61.csv")),
        "internal_primitive_pairs": len(csv_rows(REPORTS / "internal_primitive_pairs_37.csv")),
        "all_pairs": len(csv_rows(REPORTS / "all_pairs_1830_FINAL.csv")),
        "endpoint_pairs": len(csv_rows(REPORTS / "endpoint_contacts_14_source_anchored.csv")),
        "critical_cards": len(list((ROOT / "cards" / "pair").glob("P*_card.png"))),
        "opened_assets": len(csv_rows(REPORTS / "actually_opened_assets.csv")),
    }
    expected = {
        "glyph_inventory": 193, "pixel_measurements": 193, "font_elements": 21,
        "primitives": 71, "graphics": 40, "semantic_objects": 61,
        "internal_primitive_pairs": 37, "all_pairs": 1830,
        "endpoint_pairs": 14, "critical_cards": 94, "opened_assets": 337,
    }
    if counts != expected:
        raise RuntimeError(f"Denominator mismatch: {counts} != {expected}")
    pair_rows = csv_rows(REPORTS / "all_pairs_1830_FINAL.csv")
    hard = {
        "manual_unconfirmed": sum(r["MANUAL_REVIEW"] != "CONFIRMED_SA1" for r in pair_rows),
        "automated_fail": sum(r["AUTOMATED_GATE"] != "PASS" for r in pair_rows),
        "illegal_overlap_sum": sum(int(r["ILLEGAL_OVERLAP_PX"]) for r in pair_rows),
        "actual_overlap_rows": sum(int(r["FOREGROUND_OVERLAP_PX"]) > 0 for r in pair_rows),
        "actual_overlap_pixels": sum(int(r["FOREGROUND_OVERLAP_PX"]) for r in pair_rows),
        "zero_byte_count": len(zero),
        "unopenable_png_count": len(bad_png),
    }
    if hard != {
        "manual_unconfirmed": 0, "automated_fail": 0, "illegal_overlap_sum": 0,
        "actual_overlap_rows": 9, "actual_overlap_pixels": 92,
        "zero_byte_count": 0, "unopenable_png_count": 0,
    }:
        raise RuntimeError(f"Hard-gate mismatch: {hard}")
    decision = (REPORTS / "FINAL_DECISION.txt").read_text(encoding="utf-8").strip()
    if decision != "SA1_PASS_TO_FRESH_ISOLATED_SA3_NOT_FINAL":
        raise RuntimeError(f"Unexpected decision: {decision}")
    print(json.dumps({
        "preseal_ok": True, "file_count_before_controls": len(files),
        "png_count_verified_openable": len(pngs), "counts": counts, "hard": hard,
    }, indent=2))


if __name__ == "__main__":
    main()
