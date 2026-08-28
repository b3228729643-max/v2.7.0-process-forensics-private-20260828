"""Strict read/validate pass for the completed SA1 evidence package.

This checker never creates a verdict by itself.  It closes count, path, and
ledger identities, then serialises a reviewable result for the human SA1
terminal decision.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

OUT = Path(__file__).resolve().parent

def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().upper()

def safe_rel(value: str) -> Path:
    p = Path(value.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or any(":" in part for part in p.parts):
        raise RuntimeError(f"unsafe/nonportable relative path: {value}")
    return p

def png_ok(rel: str, errors: list[str]) -> bool:
    p = OUT / safe_rel(rel)
    if not p.is_file():
        errors.append(f"missing PNG {rel}"); return False
    try:
        with Image.open(p) as im:
            im.verify()
        return True
    except Exception as exc:
        errors.append(f"unopenable PNG {rel}: {exc}"); return False

def no_blank(rows: list[dict[str, str]], fields: list[str], errors: list[str], label: str) -> None:
    for idx, row in enumerate(rows, start=2):
        for field in fields:
            if not str(row.get(field, "")).strip(): errors.append(f"{label} row {idx} blank {field}")

def main() -> None:
    errors: list[str] = []
    ident = json.loads((OUT / "candidate_identity.json").read_text(encoding="utf-8"))
    pdf = Path(ident["candidate_pdf"])
    source = Path(ident["source_file"])
    if not pdf.is_file() or sha(pdf) != ident["candidate_sha256"] or sha(pdf) != ident["candidate_sha256_expected"]:
        errors.append("candidate PDF SHA identity mismatch")
    if not source.is_file() or sha(source) != ident["source_sha256"]:
        errors.append("source SHA identity mismatch")
    with fitz.open(pdf) as doc:
        if len(doc) != 813: errors.append(f"candidate page count {len(doc)} != 813")
    aux = pdf.with_suffix(".aux")
    fls = pdf.with_suffix(".fls")
    if not aux.is_file() or "fig:V5-C08-course-map" not in aux.read_text(encoding="utf-8", errors="replace"):
        errors.append("aux label identity missing")
    if not fls.is_file() or "full_course_synthesis_map.tex" not in fls.read_text(encoding="utf-8", errors="replace"):
        errors.append("fls source identity missing")

    pixels = read_csv("after_pixel_measurements.csv")
    rawdict = read_csv("rawdict_character_reconciliation.csv")
    glyph_manual = read_csv("reviewer_glyph_manual_ledger.csv")
    sheet_index = read_csv("glyph_contact_sheet_index.csv")
    glyph_cards = read_csv("glyph_contact_sheet_index.csv")
    visible = [r for r in rawdict if r["STATUS"] == "MAPPED_VISIBLE_GLYPH"]
    nonink = [r for r in rawdict if r["STATUS"] == "NONINK_WHITESPACE_OR_EMPTY"]
    if len(pixels) != 251 or len(visible) != 251 or len(nonink) != 2 or len(rawdict) != 253:
        errors.append("rawdict/glyph cardinality not 253=251+2")
    pix_ids, vis_ids, manual_ids = {r["GLYPH_ID"] for r in pixels}, {r["MAPPED_GLYPH_ID"] for r in visible}, {r["GLYPH_ID"] for r in glyph_manual}
    if len(pix_ids) != 251 or pix_ids != vis_ids or pix_ids != manual_ids:
        errors.append("glyph IDs do not close across pixels/rawdict/manual")
    if any(r["STATUS"] == "FAIL_UNRESOLVED_COMBINING_OR_ZERO_WIDTH" for r in rawdict): errors.append("unresolved combining/zero-width glyph")
    no_blank(glyph_manual, ["REVIEWER","SHEET","CELL","ORIGINAL_MATCH","OVERLAY_COMPLETE","MASK_ONLY_PURE","MISSING_STROKE_PX","FOREIGN_PIXEL_PX","DECISION","NOTE"], errors, "glyph manual")
    for r in glyph_manual:
        if any(r[x] != "YES" for x in ["ORIGINAL_MATCH","OVERLAY_COMPLETE","MASK_ONLY_PURE"]) or r["MISSING_STROKE_PX"] != "0" or r["FOREIGN_PIXEL_PX"] != "0" or r["DECISION"] == "PENDING": errors.append(f"glyph manual nonclear {r['GLYPH_ID']}")
    if len(sheet_index) != 251 or len({(r["SHEET"], r["CELL"]) for r in sheet_index}) != 251:
        errors.append("glyph contact-cell cardinality not 251")
    sheets = {r["SHEET"] for r in sheet_index}
    if len(sheets) != 16: errors.append("glyph contact-sheet count not 16")
    for r in pixels:
        png_ok(r["RAW_MASK_FILE"], errors); png_ok(r["CARD_8X_FILE"], errors); png_ok(r["PRESEGMENT_CLAIM_MASK_FILE"], errors)
        if r["MASK_PURITY_PASS"] != "True" or r["PIXEL_PASS"] != "True" or float(r["EFFECTIVE_PT"]) < 9.5: errors.append(f"glyph gate nonpass {r['GLYPH_ID']}")
    for r in sheet_index: png_ok(r["CARD"], errors)

    lows = read_csv("low_profile_calibration.csv")
    low_manual = read_csv("reviewer_low_profile_manual_ledger.csv")
    if len(lows) != 8 or {r["GLYPH_ID"] for r in lows} != {r["GLYPH_ID"] for r in low_manual}:
        errors.append("low-profile calibration/manual identity mismatch")
    for r in lows:
        if r["STATUS"] != "PASS": errors.append(f"low-profile calibration fail {r['GLYPH_ID']}")
        png_ok(r["REFERENCE_MASK"], errors); png_ok(r["REFERENCE_CARD_8X"], errors)
    no_blank(low_manual, ["REVIEWER","TARGET_CARD_8X_OPENED","REFERENCE_CARD_8X_OPENED","DECISION","NOTE"], errors, "low-profile manual")
    for r in low_manual:
        if r["DECISION"] == "PENDING" or r["FOREIGN_COMPONENTS"] != "0": errors.append(f"low-profile manual nonclear {r['GLYPH_ID']}")

    objects = json.loads((OUT / "object_inventory.json").read_text(encoding="utf-8"))
    graphics = [o for o in objects if o["kind"] == "GRAPHIC"]
    texts = [o for o in objects if o["kind"] == "TEXT"]
    graphic_inv = read_csv("graphic_object_inventory.csv")
    object_cards = read_csv("graphic_object_review_card_index.csv")
    graphic_manual = read_csv("reviewer_graphic_object_manual_ledger.csv")
    if len(objects) != 69 or len(texts) != 25 or len(graphics) != 44 or len(graphic_inv) != 44 or len(object_cards) != 44 or len(graphic_manual) != 44:
        errors.append("object/graphic cardinality mismatch")
    if {o["id"] for o in graphics} != {r["OBJECT_ID"] for r in object_cards} or {r["OBJECT_ID"] for r in object_cards} != {r["OBJECT_ID"] for r in graphic_manual}:
        errors.append("graphic card/manual ID mapping mismatch")
    for o in graphics:
        png_ok(o["mask_file"], errors)
        if o["opaque_geometry_mask_file"]: png_ok(o["opaque_geometry_mask_file"], errors)
    for r in object_cards: png_ok(r["CARD_FILE"], errors)
    no_blank(graphic_manual, ["REVIEWER","CONTACT_SHEET","DECISION","NOTE"], errors, "graphic manual")
    if any(r["DECISION"] == "PENDING" for r in graphic_manual): errors.append("graphic manual pending")
    paths = read_csv("all_pdf_drawing_path_inventory.csv")
    infig = [r for r in paths if r["INTERSECTS_FIGURE_BODY"] == "True"]
    if len(paths) != 53 or len(infig) != 39 or any(r["COVERAGE_STATUS"] != "PASS_MAPPED_FIGURE_PATH" for r in infig): errors.append("PDF drawing/path coverage mismatch")
    if sum(int(r["PATH_TO_OBJECT_COUNT"]) for r in infig) != 44: errors.append("39 path -> 44 semantic object mapping mismatch")
    # This is an explicit zero-denominator reconciliation, not a suppression:
    # every one of the 39 in-figure PDF drawing paths is a mapped TikZ
    # non-formula path, while the source/context ledger independently records
    # that the figure contains no rawdict-external mathematical rule.
    nonformula_path_class = "NONE_TIKZ_NONFORMULA_PATH"
    if any(r["MATH_RULE_CLASS"] != nonformula_path_class for r in infig):
        errors.append("unclassified or unreviewed mathematical drawing/path rule")
    z = read_csv("z_order_evidence/G030_G031_zorder_measurement.csv")
    zmanual = read_csv("reviewer_g030_g031_zorder_manual_ledger.csv")
    if len(z) != 1 or z[0]["UNIQUE_MASK_INTERSECTION_PIXELS"] != "0" or len(zmanual) != 1 or zmanual[0]["DECISION"] != "Z_ORDER_WHITE_SEPARATOR_VERIFIED": errors.append("G030/G031 z-order proof mismatch")
    for rel in [z[0][x] for x in ["NATIVE_1X","DARK_MASK","WHITE_MASK","OVERLAY","OVERLAY_8X_NEAREST","GRAYSCALE_1X","FOUR_VIEW"]]: png_ok(rel, errors)

    pairs = read_csv("object_pair_report.csv")
    critical = read_csv("critical_pair_index.csv")
    review_index = read_csv("critical_pair_review_card_index.csv")
    pair_manual = read_csv("reviewer_pair_manual_ledger.csv")
    if len(pairs) != 2346 or len(critical) != 32 or len(review_index) != 32 or len(pair_manual) != 32:
        errors.append("pair/critical/manual cardinality mismatch")
    cats = {cat: sum(r["CATEGORY"] == cat for r in pairs) for cat in ["TT","TG","GG"]}
    if cats != {"TT":300,"TG":1100,"GG":946}: errors.append(f"pair partition mismatch {cats}")
    if any(r["STATUS"].startswith("FAIL") or r["OVERLAP_PIXELS"] != "0" for r in pairs): errors.append("pair failure or final overlap exists")
    critids, reviewids, manualpairids = {r["PAIR_ID"] for r in critical}, {r["PAIR_ID"] for r in review_index}, {r["PAIR_ID"] for r in pair_manual}
    if critids != reviewids or critids != manualpairids: errors.append("critical index/review/manual IDs mismatch")
    if len(list((OUT / "critical_pair_review_cards").glob("*.png"))) != 32 or len(list((OUT / "critical_pair_cards").glob("*.png"))) != 160: errors.append("current critical card directory count mismatch")
    for r in critical:
        files = r["PIXEL_EVIDENCE"].split(";")
        if len(files) != 5: errors.append(f"critical evidence list not 5: {r['PAIR_ID']}")
        for rel in files: png_ok(rel, errors)
    for r in review_index: png_ok(r["CARD"], errors)
    no_blank(pair_manual, ["REVIEWER","NATIVE_1X_OPENED","MASK_A_UNIQUE","MASK_B_UNIQUE","OVERLAY_OPENED","NEAREST_8X_OPENED","ORIGINAL_MATCH","DECISION","NOTE"], errors, "pair manual")
    for r in pair_manual:
        if any(r[x] != "YES" for x in ["NATIVE_1X_OPENED","MASK_A_UNIQUE","MASK_B_UNIQUE","OVERLAY_OPENED","NEAREST_8X_OPENED","ORIGINAL_MATCH"]): errors.append(f"pair manual incomplete {r['PAIR_ID']}")
        if r["DECISION"] == "PENDING": errors.append(f"pair manual pending {r['PAIR_ID']}")
    delta = read_csv("critical_set_delta_35_to_32.csv")
    if len(delta) != 3 or any(r["FINAL_STATUS"] != "PASS" or r["RETAINED_IN_FULL_PAIR_TABLE"] != "YES" for r in delta): errors.append("35->32 delta evidence mismatch")

    fonts = read_csv("after_font_audit.csv")
    font_element = read_csv("font_harmony_by_element.csv")
    crossfont = read_csv("font_harmony_crosspanel_source.csv")
    fontmanual = read_csv("reviewer_font_visual_harmony_by_element.csv")
    visual = read_csv("reviewer_visual_harmony_ledger.csv")
    if len(fonts) != 25 or len(fontmanual) != 25 or {r["ELEMENT_ID"] for r in fonts} != {r["ELEMENT_ID"] for r in fontmanual}:
        errors.append("font inventory/manual cardinality mismatch")
    if any(float(r["EFFECTIVE_PT"]) < 9.5 for r in fonts): errors.append("source font under 9.5pt")
    if any("FAIL" in r.values() for r in font_element) or any(r["CROSS_PANEL_SOURCE_GATE_LE_1.05"] == "FAIL" for r in crossfont): errors.append("font D/E gate fail")
    no_blank(fontmanual, ["REVIEWER","DECISION","NOTE"], errors, "font manual")
    if any(r["DECISION"] == "PENDING" or any(r[x] != "YES" for x in ["FULL_PAGE_200_VIEWED","FIGURE_300_VIEWED","STANDALONE_300_VIEWED","KEY_ROI_8X_VIEWED","NOT_TOO_SMALL","NOT_TOO_LARGE","SAME_ROLE_COORDINATED"]) for r in fontmanual): errors.append("font manual nonclear")
    if len(visual) != 6 or any(r["DECISION"] == "PENDING" for r in visual): errors.append("visual ledger mismatch")
    for rel in ["full_page_200dpi-801.png","figure_crop_300dpi.png","standalone_300dpi.png","grayscale_300dpi.png","full_page_native_300dpi-801.png"]: png_ok(rel, errors)
    visual_md = OUT / "after_visual_acceptance.md"
    if not visual_md.is_file() or "FONT_VISUAL_HARMONY_PASS: true" not in visual_md.read_text(encoding="utf-8"): errors.append("manual visual acceptance/FONT flag missing")
    semantic = read_csv("reviewer_semantic_context_ledger.csv")
    if len(semantic) != 5 or any(r["RESULT"] in {"PENDING", "FAIL", ""} for r in semantic): errors.append("semantic-context ledger mismatch")
    math_context = [r for r in semantic if r["CHECK_ID"] == "MATH_AND_PATH_RULES"]
    if len(math_context) != 1 or math_context[0]["RESULT"] != "NOT_APPLICABLE_NO_MATH_RULE":
        errors.append("math-rule zero-denominator source/context reconciliation missing")
    source_lines = read_csv("source_line_reconciliation.csv")
    if len(source_lines) != 69 or any(r["LINE_EXISTS"] != "YES" for r in source_lines): errors.append("source-line reconciliation mismatch")

    final_report = OUT / "SA1_STRICT_FINAL_REPORT.md"
    if not final_report.is_file() or "`PASS_TO_ROOT`" not in final_report.read_text(encoding="utf-8"):
        errors.append("final strict report/declared terminal missing")
    terminal_path = OUT / "TERMINAL_RESULT.txt"
    result_path = OUT / "RESULT.json"
    terminal_exists = terminal_path.is_file()
    if terminal_exists:
        terminal_value = terminal_path.read_text(encoding="utf-8").strip()
        if terminal_value not in {"PASS_TO_ROOT", "FAIL_TO_SA2"}:
            errors.append("invalid terminal value")
        if not result_path.is_file():
            errors.append("terminal exists without RESULT.json")
        else:
            try:
                result_record = json.loads(result_path.read_text(encoding="utf-8"))
                if result_record.get("uid") != "FIG-P756-01" or result_record.get("terminal") != terminal_value:
                    errors.append("RESULT.json terminal identity mismatch")
            except Exception as exc:
                errors.append(f"unreadable RESULT.json: {exc}")
    elif result_path.exists():
        errors.append("RESULT.json exists without terminal")

    # All final-package expected PNG paths were opened above.  The isolated
    # archival subtree is deliberately excluded from acceptance counts.
    result = {
        "uid": "FIG-P756-01", "terminal_exists": terminal_exists,
        "candidate_sha256": ident["candidate_sha256"], "source_sha256": ident["source_sha256"],
        "glyphs": len(pixels), "rawdict": len(rawdict), "visible_rawdict": len(visible), "nonink_rawdict": len(nonink),
        "text_objects": len(texts), "graphic_objects": len(graphics), "objects": len(objects),
        "figure_pdf_paths": len(infig), "math_rules": 0, "pairs": len(pairs), "pair_partition": cats,
        "critical_pairs": len(critical), "glyph_manual_rows": len(glyph_manual), "graphic_manual_rows": len(graphic_manual),
        "pair_manual_rows": len(pair_manual), "low_profile_manual_rows": len(low_manual), "font_manual_rows": len(fontmanual),
        "visual_rows": len(visual), "errors": errors, "ready_for_human_terminal": not errors,
    }
    (OUT / "FINAL_MACHINE_CROSSCHECK.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if errors: raise SystemExit(2)

if __name__ == "__main__":
    main()
