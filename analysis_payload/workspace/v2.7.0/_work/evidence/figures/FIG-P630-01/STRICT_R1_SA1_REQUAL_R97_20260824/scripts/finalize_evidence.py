from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

from PIL import Image


BASE = Path(__file__).resolve().parents[1]
OFFICIAL = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
EXPECTED_OFFICIAL_SHA256 = "062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814"
EXPECTED_H_FAILS = {"GLYPH-013", "GLYPH-022", "GLYPH-025"}
EXCLUDED_FROM_EVIDENCE_CSV = {"evidence_manifest.csv", "MANIFEST.sha256", "WRITE_STOPPED"}
EXCLUDED_FROM_SHA_MANIFEST = {"MANIFEST.sha256", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_csv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return path.relative_to(BASE).as_posix()


def require(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def verify_references(rows: list[dict[str, str]], fields: list[str], failures: list[str]) -> int:
    checked = 0
    for row in rows:
        for field in fields:
            value = row.get(field, "").strip()
            if not value:
                continue
            checked += 1
            require((BASE / value).is_file(), f"missing reference {field}={value}", failures)
    return checked


def category(path: Path) -> str:
    r = rel(path)
    if r.startswith("glyphs/"):
        return "GLYPH_EVIDENCE"
    if r.startswith("graphics/"):
        return "GRAPHIC_PATH_EVIDENCE"
    if r.startswith("critical/"):
        return "CRITICAL_EVIDENCE"
    if r.startswith("pairs/"):
        return "PAIR_EVIDENCE"
    if r.startswith("render/"):
        return "RENDER"
    if r.startswith("source_identity/"):
        return "SOURCE_IDENTITY"
    if r.startswith("continuity/"):
        return "CONTINUITY"
    if r.startswith("standalone_build/"):
        return "STANDALONE_BUILD"
    if r.startswith("scripts/"):
        return "AUDIT_SCRIPT"
    return "ROOT_LEDGER_OR_REPORT"


def main() -> None:
    failures: list[str] = []

    identity = json.loads((BASE / "source_identity/official_candidate_identity.json").read_text(encoding="utf-8"))
    require(OFFICIAL.is_file(), "official candidate missing", failures)
    require(sha256(OFFICIAL) == EXPECTED_OFFICIAL_SHA256, "official candidate hash mismatch", failures)
    require(identity["official_sha256"] == EXPECTED_OFFICIAL_SHA256, "identity JSON hash mismatch", failures)
    require(identity["page_count"] == 813, "page count mismatch", failures)
    require(identity["physical_page_1based"] == 678, "physical page mismatch", failures)
    require(identity["printed_page_label"] == "665", "printed page mismatch", failures)
    require(identity["strict_crop_dimensions_px"] == [1818, 865], "strict crop dimensions mismatch", failures)

    glyphs = read_csv("after_pixel_measurements.csv")
    paths = read_csv("path_ledger.csv")
    pairs = read_csv("after_overlap_report.csv")
    glyph_manual = read_csv("glyph_manual_review.csv")
    graphic_manual = read_csv("graphic_manual_review.csv")
    pair_manual = read_csv("critical_pair_manual_review.csv")
    contact_index = read_csv("glyph_contact_sheet_index.csv")
    id_map = read_csv("id_safe_filename_map.csv")
    object_manifest = read_csv("object_manifest.csv")
    ambiguity = read_csv("glyph_ambiguity_resolution.csv")
    ratio_rows = read_csv("typography_role_ratio_ledger.csv")
    low_profile = read_csv("low_profile_punctuation_calibration_ledger.csv")

    require(len(glyphs) == 102, "glyph denominator is not 102", failures)
    require(len(paths) == 21, "graphic/path denominator is not 21", failures)
    object_ids = {r["ELEMENT_ID"] for r in glyphs} | {r["GRAPHIC_ID"] for r in paths}
    require(len(object_ids) == 123, "foreground object denominator is not 123", failures)
    expected_pairs = math.comb(123, 2)
    require(expected_pairs == 7503, "internal pair arithmetic mismatch", failures)
    require(len(pairs) == expected_pairs, "pair row count mismatch", failures)
    require(len({r["PAIR_ID"] for r in pairs}) == expected_pairs, "pair IDs not unique", failures)
    require(all(r["OBJECT_A"] in object_ids and r["OBJECT_B"] in object_ids for r in pairs), "pair references unknown object", failures)
    require(all(int(r["FINAL_VISIBLE_INTERSECTION_PX"]) == 0 for r in pairs), "final-visible pair intersection nonzero", failures)
    require(not any(r["DECISION"] == "FAIL" for r in pairs), "pair ledger contains hard geometry failure", failures)

    glyph_fail_ids = {r["ELEMENT_ID"] for r in glyphs if r["PASS_FAIL"] == "FAIL"}
    require(glyph_fail_ids == EXPECTED_H_FAILS, f"glyph hard-fail set mismatch: {sorted(glyph_fail_ids)}", failures)
    fail_measurements = {r["ELEMENT_ID"]: (int(r["H_INK_PX"]), int(r["H_GATE_PX"])) for r in glyphs if r["ELEMENT_ID"] in EXPECTED_H_FAILS}
    require(fail_measurements == {"GLYPH-013": (3, 22), "GLYPH-022": (5, 22), "GLYPH-025": (3, 22)}, "hard-fail measurements mismatch", failures)
    require(not any(r["EMPTY_MASK"].lower() == "true" for r in glyphs), "empty glyph mask", failures)
    require(not any(r["EMPTY_MASK"].lower() == "true" for r in paths), "empty graphic/path mask", failures)

    require(len(glyph_manual) == 102, "manual glyph row count mismatch", failures)
    require(len({r["GLYPH_ID"] for r in glyph_manual}) == 102, "manual glyph IDs not unique", failures)
    require({r["GLYPH_ID"] for r in glyph_manual if r["DECISION"] == "FAIL"} == EXPECTED_H_FAILS, "manual glyph fail set mismatch", failures)
    for r in glyph_manual:
        require(r["REVIEWER"] == "FIG-P630-01-SA1-R97", f"unsigned glyph row {r['GLYPH_ID']}", failures)
        require(all(r[k] == "PASS" for k in ("ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE")), f"glyph manual mask check not PASS {r['GLYPH_ID']}", failures)
        require(r["MISSING_STROKE_PX"] == "0" and r["FOREIGN_PIXEL_PX"] == "0", f"glyph manual pollution/incompleteness {r['GLYPH_ID']}", failures)

    require(len(graphic_manual) == 21, "manual graphic row count mismatch", failures)
    require(len({r["GRAPHIC_ID"] for r in graphic_manual}) == 21, "manual graphic IDs not unique", failures)
    for r in graphic_manual:
        require(r["REVIEWER"] == "FIG-P630-01-SA1-R97" and r["DECISION"] == "PASS", f"unsigned/nonpass graphic row {r['GRAPHIC_ID']}", failures)
        require(all(r[k] == "PASS" for k in ("ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE")), f"graphic manual mask check not PASS {r['GRAPHIC_ID']}", failures)
        require(r["MISSING_STROKE_PX"] == "0" and r["FOREIGN_PIXEL_PX"] == "0", f"graphic pollution/incompleteness {r['GRAPHIC_ID']}", failures)

    require(len(pair_manual) == 19, "critical pair manual row count mismatch", failures)
    require(len({r["PAIR_ID"] for r in pair_manual}) == 19, "critical pair manual IDs not unique", failures)
    for r in pair_manual:
        require(r["REVIEWER"] == "FIG-P630-01-SA1-R97" and r["DECISION"] == "PASS", f"unsigned/nonpass critical pair row {r['PAIR_ID']}", failures)
        require(all(r[k] == "PASS" for k in ("RAW_MATCH", "A_MASK_PURE", "B_MASK_PURE", "INTERSECTION_CONFIRMED", "SOURCE_SEMANTICS")), f"critical pair manual field not PASS {r['PAIR_ID']}", failures)

    require(len(contact_index) == 102, "glyph contact index row count mismatch", failures)
    require(len({r["SHEET_FILE"] for r in contact_index}) == 13, "glyph contact sheet count mismatch", failures)
    require(len(list((BASE / "graphics/contact_sheets").glob("*.png"))) == 21, "graphic contact file count mismatch", failures)
    require(len(list((BASE / "critical/glyphs").glob("*_native_1x.png"))) == 6, "critical glyph native1x count mismatch", failures)
    require(len(list((BASE / "critical/glyphs").glob("*_8x.png"))) == 6, "critical glyph 8x count mismatch", failures)
    require(len(list((BASE / "critical/pairs").glob("pair-*/card_8x.png"))) == 19, "critical pair card count mismatch", failures)
    for d in (BASE / "critical/pairs").glob("pair-*"):
        require(len(list(d.glob("*.png"))) == 7, f"critical pair evidence file count not 7: {rel(d)}", failures)

    require(len(id_map) == 123, "ID safe-name map count mismatch", failures)
    require(len({r["OBJECT_ID"] for r in id_map}) == 123, "ID safe-name object IDs not unique", failures)
    require(len({r["SAFE_FILENAME"] for r in id_map}) == 123, "safe filenames not unique", failures)
    require(len(object_manifest) == 123, "object manifest count mismatch", failures)
    require(len({r["OBJECT_ID"] for r in object_manifest}) == 123, "object manifest IDs not unique", failures)
    require(len(ambiguity) == 3 and all(r["STATUS"] == "RESOLVED_MANUAL_CONFIRMED" for r in ambiguity), "glyph ambiguity rows not manually closed", failures)
    require(all(r["DECISION"] == "PASS" for r in ratio_rows), "D/E ratio ledger contains non-PASS", failures)
    require(len(low_profile) == 1 and low_profile[0]["CANDIDATE_COUNT"] == "0" and low_profile[0]["DECISION"] == "NOT_APPLICABLE", "low-profile punctuation ledger mismatch", failures)

    reference_count = 0
    reference_count += verify_references(glyphs, ["RAW_MASK", "ORIGINAL_1X", "TARGET_OVERLAY_1X", "MASK_ONLY_1X", "CARD_8X"], failures)
    reference_count += verify_references(paths, ["PRE_MASK", "FINAL_MASK", "ORIGINAL_1X", "TARGET_OVERLAY_1X", "MASK_ONLY_1X", "CONTACT_SHEET_8X"], failures)
    reference_count += verify_references(contact_index, ["SHEET_FILE"], failures)
    reference_count += verify_references(pair_manual, ["CARD"], failures)
    for r in ambiguity:
        for value in r["MANUAL_EVIDENCE"].split("|"):
            reference_count += 1
            require((BASE / value).is_file(), f"missing ambiguity manual evidence {value}", failures)

    require((BASE / "RESULT.txt").read_text(encoding="utf-8").strip() == "SA1_FAIL_ROUTE_SA2", "RESULT mismatch", failures)
    require("SA1_FAIL_ROUTE_SA2" in (BASE / "after_visual_acceptance.md").read_text(encoding="utf-8"), "visual report terminal mismatch", failures)
    require("nondefault ADS count: `0`" in (BASE / "ads_check.md").read_text(encoding="utf-8"), "ADS check record mismatch", failures)

    existing_files = [p for p in BASE.rglob("*") if p.is_file()]
    zero_files = [rel(p) for p in existing_files if p.stat().st_size == 0]
    require(not zero_files, f"zero-byte files: {zero_files}", failures)

    pending_hits: list[str] = []
    pending_pattern = re.compile(r"\b" + "PEND" + "ING" + r"\b", re.IGNORECASE)
    text_suffixes = {".csv", ".json", ".md", ".txt", ".py", ".tex", ".aux", ".log"}
    for p in existing_files:
        if p.suffix.lower() not in text_suffixes:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if pending_pattern.search(text):
            pending_hits.append(rel(p))
    require(not pending_hits, f"unresolved manual-state tokens: {pending_hits}", failures)

    bad_pngs: list[str] = []
    png_count = 0
    for p in existing_files:
        if p.suffix.lower() != ".png":
            continue
        png_count += 1
        try:
            with Image.open(p) as im:
                require(im.width > 0 and im.height > 0, f"zero-dimension PNG {rel(p)}", failures)
                im.verify()
        except Exception as exc:
            bad_pngs.append(f"{rel(p)}: {exc}")
    require(not bad_pngs, f"unopenable PNGs: {bad_pngs}", failures)

    terminal = {
        "reviewer": "FIG-P630-01-SA1-R97",
        "terminal_result": "SA1_FAIL_ROUTE_SA2",
        "evidence_closure_status": "PASS" if not failures else "FAIL",
        "content_hard_fail_count": 3,
        "content_hard_fail_ids": sorted(EXPECTED_H_FAILS),
        "glyph_count": len(glyphs),
        "graphic_path_count": len(paths),
        "foreground_N": len(object_ids),
        "expected_pairs": expected_pairs,
        "actual_pairs": len(pairs),
        "final_visible_overlap_pair_count": sum(int(r["FINAL_VISIBLE_INTERSECTION_PX"]) > 0 for r in pairs),
        "empty_glyph_mask_count": sum(r["EMPTY_MASK"].lower() == "true" for r in glyphs),
        "empty_graphic_mask_count": sum(r["EMPTY_MASK"].lower() == "true" for r in paths),
        "glyph_manual_rows": len(glyph_manual),
        "graphic_manual_rows": len(graphic_manual),
        "critical_pair_manual_rows": len(pair_manual),
        "glyph_contact_sheets": len({r["SHEET_FILE"] for r in contact_index}),
        "graphic_contact_sheets": len(list((BASE / "graphics/contact_sheets").glob("*.png"))),
        "critical_glyph_native1x": len(list((BASE / "critical/glyphs").glob("*_native_1x.png"))),
        "critical_glyph_8x": len(list((BASE / "critical/glyphs").glob("*_8x.png"))),
        "critical_pair_cards": len(list((BASE / "critical/pairs").glob("pair-*/card_8x.png"))),
        "validated_relative_references": reference_count,
        "png_files_opened_by_machine": png_count,
        "zero_byte_file_count": len(zero_files),
        "pending_token_file_count": len(pending_hits),
        "nondefault_ads_count": 0,
        "failures": failures,
        "manifest_policy": {
            "evidence_manifest_excludes": sorted(EXCLUDED_FROM_EVIDENCE_CSV),
            "sha_manifest_excludes": sorted(EXCLUDED_FROM_SHA_MANIFEST),
            "write_stopped_is_last_write_and_is_deliberately_not_self_manifested": True,
        },
    }
    (BASE / "terminal_check.json").write_text(json.dumps(terminal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    inventory_files = sorted(
        (p for p in BASE.rglob("*") if p.is_file() and rel(p) not in EXCLUDED_FROM_EVIDENCE_CSV),
        key=lambda p: rel(p).lower(),
    )
    with (BASE / "evidence_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["RELATIVE_PATH", "BYTES", "SHA256", "CATEGORY"])
        w.writeheader()
        for p in inventory_files:
            w.writerow({"RELATIVE_PATH": rel(p), "BYTES": p.stat().st_size, "SHA256": sha256(p), "CATEGORY": category(p)})

    sha_files = sorted(
        (p for p in BASE.rglob("*") if p.is_file() and rel(p) not in EXCLUDED_FROM_SHA_MANIFEST),
        key=lambda p: rel(p).lower(),
    )
    with (BASE / "MANIFEST.sha256").open("w", encoding="utf-8", newline="\n") as f:
        for p in sha_files:
            f.write(f"{sha256(p)} *{rel(p)}\n")

    print(json.dumps({
        "evidence_closure_status": terminal["evidence_closure_status"],
        "terminal_result": terminal["terminal_result"],
        "ordinary_inventory_rows": len(inventory_files),
        "sha_manifest_entries": len(sha_files),
        "png_count": png_count,
        "validated_references": reference_count,
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
