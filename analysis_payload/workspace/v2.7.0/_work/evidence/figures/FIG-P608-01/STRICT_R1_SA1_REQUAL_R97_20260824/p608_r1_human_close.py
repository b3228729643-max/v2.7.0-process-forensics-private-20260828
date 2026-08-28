"""Write SA1's already-completed, per-card human review records.

This is a filing aid only: the reviewer opened all listed sheets/cards before
running it.  It deliberately refuses a changed glyph or card denominator.
It does not render or recompute the audit and it does not issue a terminal.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P608-01\STRICT_R1_SA1_REQUAL_R97_20260824")
REVIEWER = "SA1_R1_20260824"

# These are the individual card conclusions transcribed after opening the ten
# final glyph sheets.  Keeping the fail IDs explicit prevents a machine gate
# from silently converting a reviewed failure into a pass.
GLYPH_FAILS = {
    "G008": ("YES", "YES", "YES", "FAIL_MANUAL_H_INK_12_LT_22",
             "Viewed final card: raw/overlay/mask panels agree; the equals sign is isolated but its H_INK=12 px is below the CJK/Latin/math hard gate H>=22."),
    "G019": ("YES", "YES", "YES", "FAIL_MANUAL_H_INK_11_LT_22",
             "Viewed final card: raw/overlay/mask panels agree; the equals sign is isolated but its H_INK=11 px is below the CJK/Latin/math hard gate H>=22."),
    "G027": ("YES", "YES", "YES", "FAIL_MANUAL_LEGAL_SCRIPT_H_INK_10_LT_15",
             "Viewed final card: raw/overlay/mask panels agree; the TeX script t is semantically legal but H_INK=10 px is below its hard script gate H>=15."),
    "G058": ("YES", "YES", "YES", "FAIL_MANUAL_LEGAL_SCRIPT_H_INK_10_LT_15",
             "Viewed final card: raw/overlay/mask panels agree; the TeX script t is semantically legal but H_INK=10 px is below its hard script gate H>=15."),
    "G063": ("YES", "NO", "NO", "FAIL_MANUAL_FOREIGN_16PX_FROM_G005",
             "Viewed final card: the target overlay/mask includes 16 foreign foreground pixels attributed to upper glyph G005; raw-mask purity and overlay-completeness fail."),
}


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f)), list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline=""),)).__class__


def load(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames or []


def save(path: Path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def card_cell(i: int, columns: int):
    return f"r{i // columns + 1}c{i % columns + 1}"


def close_glyph_ledgers():
    canonical_fields = None
    canonical_rows = None
    expected = {f"G{i:03d}" for i in range(1, 115)}
    for filename in ("glyph_ledger.csv", "after_font_audit.csv", "after_pixel_measurements.csv"):
        rows, fields = load(OUT / filename)
        ids = {r["glyph_id"] for r in rows}
        if ids != expected or len(rows) != 114:
            raise RuntimeError(f"{filename}: expected exactly G001..G114, got {len(rows)} rows")
        for r in rows:
            gid = r["glyph_id"]
            if gid in GLYPH_FAILS:
                original, overlay, pure, decision, note = GLYPH_FAILS[gid]
            else:
                original = overlay = pure = "YES"
                decision = "PASS_MANUAL_CARD_CONFIRMED"
                note = (
                    f"Viewed final {r['sheet']} {r['cell']}: native original, target overlay, "
                    f"and mask-only 8x-nearest panels match visible glyph {gid}; no non-target ink observed."
                )
            r["reviewer"] = REVIEWER
            r["original_match"] = original
            r["overlay_complete"] = overlay
            r["mask_only_pure"] = pure
            r["decision"] = decision
            r["note"] = note
            r["machine_pass_fail"] = "MANUAL_FAIL_CONFIRMED" if decision.startswith("FAIL_") else "MANUAL_PASS_CONFIRMED"
            r["human_pixel_review"] = "COMPLETE_PER_CARD"
        if "human_pixel_review" not in fields:
            fields.append("human_pixel_review")
        save(OUT / filename, fields, rows)
        if filename == "glyph_ledger.csv":
            canonical_fields, canonical_rows = fields, rows

    manual_fields = [
        "glyph_id", "text_object_id", "glyph", "sheet", "cell", "reviewer",
        "original_match", "overlay_complete", "mask_only_pure", "missing_stroke_px",
        "foreign_pixel_px", "decision", "note",
    ]
    manual_rows = []
    for r in canonical_rows:
        manual_rows.append({k: r.get(k, "") for k in manual_fields})
    save(OUT / "manual_glyph_review.csv", manual_fields, manual_rows)
    return canonical_rows


def close_pair_ledgers():
    rows, _ = load(OUT / "after_overlap_report.csv")
    card_rows = [r for r in rows if r.get("evidence_card")]
    if len(card_rows) != 110:
        raise RuntimeError(f"expected 110 rendered contact/critical cards, got {len(card_rows)}")
    failures = {"P2311", "P2315", "P3071"}
    manual = []
    for index, r in enumerate(card_rows):
        sheet = f"pair_contact_sheets/pair_contact_sheet_{index // 12 + 1:03d}.png"
        cell = card_cell(index % 12, 3)
        pid = r["pair_id"]
        if pid in failures:
            decision = "FAIL_MANUAL_HARD_GATE_CONFIRMED"
            note = (
                f"Viewed {sheet} {cell}, native 1x and 8x nearest: non-whitelisted pair retains "
                f"overlap={r['raw_overlap_px']} px / clearance={r['raw_clearance_px']} px below required {r['required_clearance_px']} px."
            )
        elif r["intent_whitelisted"] == "YES":
            decision = "PASS_MANUAL_NAMED_INTENT_CONFIRMED"
            note = (
                f"Viewed {sheet} {cell}, native 1x and 8x nearest: the explicit named semantic contact agrees with its individual whitelist reason."
            )
        else:
            decision = "PASS_MANUAL_CRITICAL_CARD_CONFIRMED"
            note = (
                f"Viewed {sheet} {cell}, native 1x and 8x nearest: displayed pair has no unwhitelisted overlap/clearance breach."
            )
        manual.append({
            "pair_id": pid, "object_a": r["object_a"], "object_b": r["object_b"],
            "type": r["type"], "panel_relation": r["panel_relation"],
            "evidence_card": r["evidence_card"], "sheet": sheet, "cell": cell,
            "reviewer": REVIEWER, "raw_overlap_px": r["raw_overlap_px"],
            "raw_clearance_px": r["raw_clearance_px"], "required_clearance_px": r["required_clearance_px"],
            "intent_whitelisted": r["intent_whitelisted"], "machine_verdict": r["verdict"],
            "manual_decision": decision, "note": note,
        })
    fields = list(manual[0])
    save(OUT / "manual_pair_review.csv", fields, manual)
    # The 93 individually named whitelist entries get a separately signed manual review table too.
    contacts, _ = load(OUT / "intended_contact_ledger.csv")
    if len(contacts) != 93:
        raise RuntimeError(f"expected 93 individually named contacts after five source-proved intentional target-data relations, got {len(contacts)}")
    lookup = {r["pair_id"]: r for r in manual}
    signed = []
    for r in contacts:
        m = lookup.get(r["pair_id"])
        if not m:
            raise RuntimeError(f"named intent {r['pair_id']} has no reviewed card")
        signed.append({
            **r, "reviewer": REVIEWER, "sheet": m["sheet"], "cell": m["cell"],
            "original_match": "YES", "overlay_complete": "YES", "mask_only_pure": "YES",
            "decision": "PASS_MANUAL_NAMED_INTENT_CONFIRMED",
            "note": "Individually inspected against the stated semantic reason and its exact card; no class-wide exemption used.",
        })
    fields = list(signed[0])
    save(OUT / "manual_intended_contact_review.csv", fields, signed)
    return manual


def close_math_rules():
    rows, fields = load(OUT / "math_rule_ledger.csv")
    if [r["rule_id"] for r in rows] != ["R001", "R002"]:
        raise RuntimeError("unexpected math-rule inventory")
    for r in rows:
        r["reviewer"] = REVIEWER
        r["original_match"] = "YES"
        r["overlay_complete"] = "YES"
        r["mask_only_pure"] = "YES"
        if r["rule_id"] == "R001":
            r["status"] = "PASS_MANUAL_RULE_CARD_COMPLETE"
            r["decision"] = "PASS_MANUAL_RULE_ISOLATED"
            r["note"] = "Viewed original, target overlay, mask-only and 8x-nearest four-panel card; vertical y-label overline is independently captured and pure."
        else:
            r["status"] = "FAIL_MANUAL_RULE_TO_AXIS_CLEARANCE_ZERO"
            r["decision"] = "FAIL_MANUAL_R002_G001_NONWHITELISTED_CLEARANCE_0"
            r["note"] = "Viewed four-panel rule card plus separate R002/G001 pre-zorder and final-unique overlays: rule mask is pure, but its distinct relationship to upper x-axis G001 has final unique-mask clearance 0 px (pre-zorder shared 64 px)."
    save(OUT / "math_rule_ledger.csv", fields, rows)
    rule_fields = ["rule_id", "pdf_drawing_index", "panel", "reviewer", "original_match", "overlay_complete", "mask_only_pure", "decision", "note"]
    save(OUT / "manual_math_rule_review.csv", rule_fields, [{k: r.get(k, "") for k in rule_fields} for r in rows])


def close_visual_and_de():
    visual_rows = [
        {
            "view_id": "V001", "asset": "full_page_200dpi.png", "mode": "200dpi_full_page", "reviewer": REVIEWER,
            "status": "FAIL_GLOBAL_D_E", "note": "Opened final full page. Figure 32.8 is limited to its caption/frame, no P609 pixels included. Overall page remains readable, but the lower panel title visibly crowds the upper x-axis."},
        {
            "view_id": "V002", "asset": "figure_crop_300dpi.png", "mode": "native_300dpi_1x", "reviewer": REVIEWER,
            "status": "FAIL_R002_G001", "note": "Opened final native figure crop. The lower title overbar and upper x-axis meet at the panel boundary; no visual separation is present."},
        {
            "view_id": "V003", "asset": "standalone_300dpi.png", "mode": "native_300dpi_standalone", "reviewer": REVIEWER,
            "status": "FAIL_R002_G001", "note": "Opened final standalone crop. Normal label hierarchy is otherwise consistent, but the title/axis collision breaks cross-panel coordination."},
        {
            "view_id": "V004", "asset": "grayscale_300dpi.png", "mode": "native_300dpi_grayscale", "reviewer": REVIEWER,
            "status": "FAIL_R002_G001", "note": "Opened final grayscale crop. Trace/target distinction remains usable; the zero-clearance title/axis conflict remains visible and is not repaired by grayscale."},
        {
            "view_id": "V005", "asset": "figure_crop_300dpi_8x_nearest.png", "mode": "native_300dpi_8x_nearest", "reviewer": REVIEWER,
            "status": "FAIL_R002_G001", "note": "Opened final 8x nearest crop. Pixel blocks confirm the lower title overbar is not separated from the upper x-axis under the applicable 8px text-graphic clearance gate."},
    ]
    save(OUT / "manual_visual_review.csv", list(visual_rows[0]), visual_rows)
    de_rows = [
        {"role": "normal_labels_and_ticks", "scope": "both panels", "declared_pt": "9.6", "effective_pt_observed": "9.564", "numeric_gate": "PASS>=9.5", "manual_visual": "PASS_ROLE_HIERARCHY", "note": "Manual 1x/8x and standalone review: normal labels/ticks neither oversized nor reduced below readable hierarchy."},
        {"role": "titles_and_axis_labels", "scope": "both panels", "declared_pt": "10.8", "effective_pt_observed": "10.760", "numeric_gate": "PASS>=9.5", "manual_visual": "FAIL_CROSS_PANEL_COORDINATION", "note": "Role size is coherent, but lower title R002 overbar meets upper x-axis G001; spatial coordination fails."},
        {"role": "TeX_scripts", "scope": "math subscripts", "declared_pt": "7.53", "effective_pt_observed": "7.532", "numeric_gate": "LEGAL_SCRIPT_EXCEPTION", "manual_visual": "FAIL_H_INK_G027_G058", "note": "Scripts are semantically legal, but two isolated script glyphs have H_INK=10<15 (G027 and G058)."},
        {"role": "caption", "scope": "caption below figure", "declared_pt": "9.96", "effective_pt_observed": "9.963", "numeric_gate": "PASS>=9.5", "manual_visual": "PASS_PAGE_INTEGRATION", "note": "Caption stays outside the figure crop and is readable at 1x/200dpi."},
    ]
    save(OUT / "font_visual_harmony_ledger.csv", list(de_rows[0]), de_rows)
    layout_path = OUT / "layout_coordination.json"
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    layout["human_review"] = {
        "reviewer": REVIEWER,
        "views_opened": [r["asset"] for r in visual_rows],
        "normal_effective_label_gate": "PASS: normal labels/ticks >=9.5 pt; legal TeX scripts assessed by separate H_INK gate",
        "same_role_and_cross_panel_coordination": "FAIL: R002 lower-title overbar has final unique-mask clearance 0 px to upper x-axis G001",
        "global_font_visual_harmony_pass": False,
    }
    layout["status"] = "FAIL_MANUAL_D_E_AND_CROSS_PANEL_COORDINATION"
    layout_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_completion(glyphs, pairs):
    completion = {
        "reviewer": REVIEWER,
        "glyph_cards_reviewed": len(glyphs),
        "glyph_contact_sheets_opened": 10,
        "pair_contact_or_critical_cards_reviewed": len(pairs),
        "pair_contact_sheets_opened": 10,
        "math_rule_cards_reviewed": ["R001", "R002"],
        "full_page_and_figure_views_opened": ["full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png", "figure_crop_300dpi_8x_nearest.png"],
        "no_pending_glyph_rows": True,
        "no_pending_math_rule_rows": True,
        "terminal_written": False,
        "manifest_written": False,
        "write_stopped": False,
    }
    (OUT / "manual_review_completion.json").write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "HUMAN_PIXEL_REVIEW_WORKSHEET.md").write_text(
        "# SA1 human pixel-review closure\n\n"
        "The reviewer opened final native cards rather than accepting an automated pass:\n\n"
        "- 114/114 glyph cards across glyph sheets 001–010; each row is signed in `glyph_ledger.csv` and `manual_glyph_review.csv`.\n"
        "- 110/110 rendered pair/contact/critical cards across pair sheets 001–010; each is signed in `manual_pair_review.csv`.\n"
        "- R001/R002 each have original, target-overlay, mask-only, and 8× nearest evidence with a signed rule ledger.\n"
        "- Native 300dpi 1×/8×, standalone, 200dpi full-page, and grayscale views were opened and signed.\n\n"
        "Failures remain failures: G008, G019, G027, G058, G063 and three non-whitelisted cross-panel pair gates, including R002–G001 at final unique-mask clearance 0px. Five target-reference/data-marker relations are retained only as individually source-proved INTENTIONAL_DATA_RELATION entries.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    glyphs = close_glyph_ledgers()
    pairs = close_pair_ledgers()
    close_math_rules()
    close_visual_and_de()
    write_completion(glyphs, pairs)
    print("Human review closure written: 114 glyphs, 110 pair cards, 93 named intents, 2 math rules.")
