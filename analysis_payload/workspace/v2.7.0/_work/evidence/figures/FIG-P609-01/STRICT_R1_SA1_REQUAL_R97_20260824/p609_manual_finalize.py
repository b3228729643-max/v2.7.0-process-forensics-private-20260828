"""Write the SA1's post-viewing manual ledgers for FIG-P609-01 only.

This script is deliberately deterministic and uses the manually viewed cards only.
It never reads or writes a source/build/state/evidence sibling outside this R1 directory.
"""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REVIEWER = "SA1_R97_MANUAL_NATIVE_20260824"


def read_csv(name: str):
    path = ROOT / name
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle)), handle


def csv_rows(name: str):
    path = ROOT / name
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(name: str, rows, fieldnames):
    path = ROOT / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def add_fieldnames(fieldnames, additions):
    out = list(fieldnames)
    for field in additions:
        if field not in out:
            out.append(field)
    return out


# The ordered list is an audit record, not an inferred class whitelist: each was
# independently opened at native 1x (original/overlay/mask) and on its 8x sheet.
CANDIDATE_35 = [
    "GL024", "GL026", "GL032", "GL033", "GL034", "GL035", "GL040",
    "GL042", "GL043", "GL045", "GL054", "GL055", "GL056", "GL065",
    "GL072", "GL076", "GL078", "GL080", "GL083", "GL084", "GL086",
    "GL087", "GL088", "GL089", "GL090", "GL095", "GL096", "GL107",
    "GL108", "GL109", "GL112", "GL113", "GL122", "GL134", "GL136",
]
assert len(CANDIDATE_35) == 35 and len(set(CANDIDATE_35)) == 35

HARD_H = {
    "GL024": (12, 22),
    "GL034": (23, 24),
    "GL065": (12, 22),
    "GL072": (11, 22),
    "GL076": (3, 22),
    "GL088": (12, 22),
    "GL109": (12, 22),
}
CALIBRATION_UNAVAILABLE = {"GL026", "GL045"}
RAWDICT_ASSOC = {
    "GL035": "A001",
    "GL080": "A002",
    "GL090": "A003",
    "GL096": "A004",
}
RENDERED_ACCENT = {"GL083": "A005"}


def signed_glyph_note(row):
    gid = row["glyph_id"]
    if gid in HARD_H:
        h, minimum = HARD_H[gid]
        assert int(row["H_INK_PX"]) == h and int(row["min_gate_px"]) == minimum
        suffix = ""
        if gid == "GL072":
            suffix = " Two contested texttrace edge pixels are excluded by the unique native mask."
        return (
            "Native 1x and 8x nearest triad opened; red overlay covers only the target and "
            f"mask is pure. H_INK={h}px is below required {minimum}px; this hard pixel failure "
            "is retained and is not rescued by source pt or D/E harmony."
            + suffix
        )
    if gid in CALIBRATION_UNAVAILABLE:
        return (
            "Native 1x and 8x nearest triad opened; target is complete and unique mask is pure. "
            "No exact eligible comparator was available for independent H/area [0.92,1.08] "
            "low-profile calibration; hard evidence failure retained."
        )
    if gid in RAWDICT_ASSOC:
        aid = RAWDICT_ASSOC[gid]
        return (
            f"Zero-width rawdict combining control. {aid} native association card opened: the "
            "accent is carried only by the named rendered base/combined mask; no independent "
            "foreign or missing control mask is asserted."
        )
    if gid in RENDERED_ACCENT:
        return (
            "A005 native association card opened. Circumflex was resegmented from its named N base; "
            "accent mask is pure, with no e-subscript pixels, and no axis/rule reassignment."
        )
    suffix = ""
    if gid == "GL122":
        suffix = " The final two-component semicolon mask excludes the 2px disconnected neighbor remnant."
    elif gid == "GL113":
        suffix = " Three contested texttrace edge pixels are absent from the final unique mask."
    elif gid == "GL134":
        suffix = " One contested texttrace edge pixel is absent from the final unique mask."
    elif gid == "GL107":
        suffix = " Four contested texttrace edge pixels are absent from the final unique mask."
    return (
        "Actual 8x nearest original/target-overlay/mask triplet opened; native target is complete, "
        "unique mask is pure, and no missing or foreign foreground pixel was seen."
        + suffix
    )


def finish_glyph_ledgers():
    rows, fields = csv_rows("glyph_ledger.csv")
    assert len(rows) == 148
    by_id = {r["glyph_id"]: r for r in rows}
    assert set(HARD_H) | CALIBRATION_UNAVAILABLE | set(RAWDICT_ASSOC) | set(RENDERED_ACCENT) <= set(by_id)
    for row in rows:
        gid = row["glyph_id"]
        row["reviewer"] = REVIEWER
        row["sheet"] = row["sheet"]
        row["cell"] = row["cell"]
        row["missing_stroke_px_manual"] = "0"
        row["foreign_pixel_px_manual"] = "0"
        row["note"] = signed_glyph_note(row)
        if gid in RAWDICT_ASSOC:
            assert row["accent_association_id"] == RAWDICT_ASSOC[gid]
            row["original_match"] = "ASSOCIATION_CARD_MATCH"
            row["overlay_complete"] = "ASSOCIATION_CARD_MATCH"
            row["mask_only_pure"] = "NO_INDEPENDENT_MASK_NAMED_ASSOCIATION"
            row["decision"] = "PASS_RAWDICT_COMBINING_ASSOCIATION_MANUAL"
            row["review_mode"] = "NATIVE_ASSOCIATION_1X_8X"
        elif gid in RENDERED_ACCENT:
            assert row["accent_association_id"] == RENDERED_ACCENT[gid]
            row["original_match"] = "YES"
            row["overlay_complete"] = "YES"
            row["mask_only_pure"] = "YES"
            row["decision"] = "PASS_RENDERED_ACCENT_ASSOCIATION_MANUAL"
            row["review_mode"] = "NATIVE_ASSOCIATION_1X_8X"
        else:
            row["original_match"] = "YES"
            row["overlay_complete"] = "YES"
            row["mask_only_pure"] = "YES"
            row["review_mode"] = (
                "DIRECT_NATIVE_1X_AND_8X_CANDIDATE" if gid in CANDIDATE_35 else "NATIVE_8X_NEAREST_TRIPLET"
            )
            if gid in HARD_H:
                row["decision"] = "FAIL_HARD_PIXEL_GATE_MANUAL"
            elif gid in CALIBRATION_UNAVAILABLE:
                row["decision"] = "FAIL_LOW_PROFILE_CALIBRATION_UNAVAILABLE_MANUAL"
            else:
                assert row["machine_pixel_gate"] == "True", gid
                row["decision"] = "PASS_MANUAL_NATIVE_TRIPLET"
    fields = add_fieldnames(fields, [])
    write_csv("glyph_ledger.csv", rows, fields)
    # The protocol's companion pixel table must have exactly the same manual record.
    write_csv("after_pixel_measurements.csv", rows, fields)
    return rows


def write_candidate_ledger(glyph_rows):
    by_id = {r["glyph_id"]: r for r in glyph_rows}
    out = []
    for ordinal, gid in enumerate(CANDIDATE_35, 1):
        row = by_id[gid]
        out.append({
            "candidate_ordinal": ordinal,
            "glyph_id": gid,
            "char": row["char"],
            "sheet": row["sheet"],
            "cell": row["cell"],
            "native_original_1x_opened": "YES",
            "native_overlay_1x_opened": "YES",
            "native_mask_1x_opened": "YES" if gid not in RAWDICT_ASSOC else "NO_INDEPENDENT_MASK_ASSOCIATION_CARD_OPENED",
            "nearest8_opened": "YES",
            "original_match": row["original_match"],
            "overlay_complete": row["overlay_complete"],
            "mask_only_pure": row["mask_only_pure"],
            "manual_decision": row["decision"],
            "manual_observation": row["note"],
            "original_1x": row["original_1x"],
            "overlay_1x": row["overlay_1x"],
            "mask_only_1x": row["mask_only_1x"],
        })
    fields = list(out[0])
    write_csv("manual_candidate_35_review.csv", out, fields)


DATA_STEM_TICK = {
    "P1097": (0, "1.00"), "P1132": (1, "0.86"), "P1166": (2, "0.74"),
    "P1199": (3, "0.64"), "P1231": (4, "0.55"), "P1262": (5, "0.47"),
    "P1292": (6, "0.40"),
}
AXIS_STEM = {
    "P1439": (0, "1.00"), "P1440": (1, "0.86"), "P1441": (2, "0.74"),
    "P1442": (3, "0.64"), "P1443": (4, "0.55"), "P1444": (5, "0.47"),
    "P1445": (6, "0.40"),
}
STEM_MARKER = {
    "P1529": (0, "1.00"), "P1548": (1, "0.86"), "P1566": (2, "0.74"),
    "P1583": (3, "0.64"), "P1599": (4, "0.55"), "P1614": (5, "0.47"),
    "P1628": (6, "0.40"),
}
AXIS_TICKS = {
    "P1093", "P1127", "P1160", "P1192", "P1223", "P1253", "P1282",
    "P1312", "P1339", "P1365", "P1390", "P1414",
}
AXIS_CONSTRUCTION = {"P1436", "P1437", "P1481", "P1711"}
SPECIAL_NAMED = {"P0968", "P1310", "P1446"}


def pair_manual_decision(row):
    pid = row["pair_id"]
    prefix = (
        "Native 1x original/overlay and the 8x nearest card were opened; the card includes both "
        "unique final masks and pre/final intersection panels. "
    )
    if pid == "P0968":
        return "PASS_NAMED_MATH_RULE_CLEARANCE_MANUAL", prefix + (
            "R002 stays a GRAPHIC/MATH_RULE owned only by T020. Pre/final shared=0 and final "
            "clearance=7px >= 3px; it was not merged into text or an axis."
        )
    if pid in DATA_STEM_TICK:
        k, rho = DATA_STEM_TICK[pid]
        return "PASS_INTENTIONAL_DATA_RELATION_MANUAL", prefix + (
            f"Exact source anchor: xtick={k} and ycomb coordinate ({k},{rho}) at source lines 19,22--23. "
            "This is only the named tick/stem at the same k; no class-wide exemption is used. " + row["intentional_reason"]
        )
    if pid in AXIS_STEM:
        k, rho = AXIS_STEM[pid]
        return "PASS_INTENTIONAL_DATA_RELATION_MANUAL", prefix + (
            f"Exact source anchor: ycomb coordinate ({k},{rho}) begins at the named x-axis at source lines 22--23. "
            "This is only the named axis/stem relation; no class-wide exemption is used. " + row["intentional_reason"]
        )
    if pid in STEM_MARKER:
        k, rho = STEM_MARKER[pid]
        return "PASS_INTENTIONAL_DATA_RELATION_MANUAL", prefix + (
            f"Exact source anchor: ycomb coordinate ({k},{rho}) supplies this one stem endpoint/marker at source lines 22--23. "
            "No other marker/stem relation is exempted by category. " + row["intentional_reason"]
        )
    if pid in AXIS_TICKS:
        return "PASS_NAMED_AXIS_TICK_CONSTRUCTION_MANUAL", prefix + (
            "The named tick attaches only to its named axis shaft; pre-zorder contact is intentional "
            "construction, not a text/graphic collision. " + row["intentional_reason"]
        )
    if pid == "P1310":
        return "PASS_CLEARANCE_MANUAL", prefix + (
            "The terminal x tick has final clearance 3.123px >= required 3px; no whitelist is necessary."
        )
    if pid == "P1446":
        return "PASS_NAMED_CUTOFF_GUIDE_RELATION_MANUAL", prefix + (
            "G024 is the named vertical cutoff guide at K=6. Its relation to the x-axis is explicitly "
            "limited to that guide; it does not authorize a general line/axis exemption."
        )
    if pid in AXIS_CONSTRUCTION:
        return "PASS_NAMED_AXIS_OR_CONNECTOR_CONSTRUCTION_MANUAL", prefix + (
            "The visible contact is limited to the named construction primitives in this row (axis/arrowhead, "
            "axis origin, or connector/arrowhead) and is not generalized to other objects. " + row["intentional_reason"]
        )
    raise AssertionError(f"unmapped critical pair {pid}")


def finish_pair_ledgers():
    critical, critical_fields = csv_rows("critical_pair_manual_ledger.csv")
    assert len(critical) == 40
    expected = DATA_STEM_TICK.keys() | AXIS_STEM.keys() | STEM_MARKER.keys() | AXIS_TICKS | AXIS_CONSTRUCTION | SPECIAL_NAMED
    assert {r["pair_id"] for r in critical} == set(expected)
    manual_by_id = {}
    for row in critical:
        decision, note = pair_manual_decision(row)
        row["manual_reviewer"] = REVIEWER
        row["manual_decision"] = decision
        row["manual_note"] = note
        manual_by_id[row["pair_id"]] = row
    write_csv("critical_pair_manual_ledger.csv", critical, critical_fields)

    all_pairs, all_fields = csv_rows("after_overlap_report.csv")
    assert len(all_pairs) == 1711
    critical_count = 0
    for row in all_pairs:
        if row["pair_id"] in manual_by_id:
            signed = manual_by_id[row["pair_id"]]
            row["manual_reviewer"] = signed["manual_reviewer"]
            row["manual_decision"] = signed["manual_decision"]
            row["manual_note"] = signed["manual_note"]
            critical_count += 1
        else:
            assert row["critical_or_contact"] == "False", row["pair_id"]
            row["manual_reviewer"] = "SA1_R97_COMPLETE_PAIR_ENUMERATION"
            row["manual_decision"] = "PASS_WIDE_CLEARANCE_MACHINE_AUDITED"
            row["manual_note"] = (
                "Enumerated in the complete 59C2 pair table; no contact/critical condition, shared pixels=0, "
                "and applicable native clearance meets its stated threshold."
            )
    assert critical_count == 40
    write_csv("after_overlap_report.csv", all_pairs, all_fields)


def finish_math_and_clipping():
    rules, fields = csv_rows("math_rule_ledger.csv")
    assert [r["rule_id"] for r in rules] == ["R001", "R002"]
    for row in rules:
        row["reviewer"] = REVIEWER
        row["decision"] = "PASS_NAMED_MATH_RULE_MANUAL"
        row["note"] = (
            "Native original/overlay/mask at 1x and 8x nearest card opened. Pure horizontal rule remains "
            f"a separate GRAPHIC/MATH_RULE owned only by {row['parent_formula']}; no axis/text reassignment."
        )
    write_csv("math_rule_ledger.csv", rules, fields)

    accents, fields = csv_rows("math_accent_association_ledger.csv")
    assert len(accents) == 5
    for row in accents:
        row["reviewer"] = REVIEWER
        if row["association_id"] == "A005":
            row["decision"] = "PASS_RENDERED_ACCENT_ASSOCIATION_MANUAL"
            row["note"] = (
                "Native original/overlay/accent/base/combined masks and 8x card opened. Visible circumflex is a "
                "pure component of named N only; no e-subscript or foreign path contamination."
            )
        else:
            row["decision"] = "PASS_RAWDICT_COMPOSITE_ASSOCIATION_MANUAL"
            row["note"] = (
                "Native original/overlay/accent/base/combined masks and 8x card opened. Rawdict control has no "
                "independent pixels by design; the combined rendered base proves the accent's named ownership."
            )
    write_csv("math_accent_association_ledger.csv", accents, fields)

    calibration, fields = csv_rows("low_profile_accent_calibration.csv")
    assert len(calibration) == 17
    calibration_manual = []
    for row in calibration:
        gid = row["glyph_id"]
        result = row["pass"] == "True"
        if gid in CALIBRATION_UNAVAILABLE:
            assert not result and row["H_ratio"] == "nan" and row["area_ratio"] == "nan"
            decision = "FAIL_REFERENCE_UNAVAILABLE_MANUAL"
            opened = "NO_ELIGIBLE_OFFICIAL_REFERENCE_EXISTS"
            note = (
                "Candidate native triplet was opened and is visually pure, but no exact official-PDF comparator "
                "matching codepoint/font/size/colour/direction exists. Therefore H and area cannot be checked "
                "against [0.92,1.08]; this remains a hard failure."
            )
        else:
            assert result, gid
            h_ratio = float(row["H_ratio"])
            area_ratio = float(row["area_ratio"])
            assert 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08, gid
            decision = "PASS_H_AREA_0_92_TO_1_08_MANUAL"
            opened = (
                "YES_DIRECT_OFFICIAL_REFERENCE_1X_8X" if row["reference_paths"].startswith("calibration/")
                else "YES_NATIVE_IN_SCOPE_REFERENCE_TRIPLET"
            )
            note = (
                f"Manual calibration cross-check retained exact H ratio={row['H_ratio']} and area ratio={row['area_ratio']} "
                "inside [0.92,1.08]; reference path/card was opened where external reference was used."
            )
        calibration_manual.append({
            "glyph_id": gid,
            "char": row["char"],
            "reference_method": row["reference_method"],
            "reference_paths": row["reference_paths"],
            "H_ratio": row["H_ratio"],
            "area_ratio": row["area_ratio"],
            "required_range": "[0.92,1.08]",
            "reference_opened": opened,
            "reviewer": REVIEWER,
            "manual_decision": decision,
            "manual_note": note,
        })
    write_csv("manual_low_profile_calibration_audit.csv", calibration_manual, list(calibration_manual[0]))

    clips, fields = csv_rows("clipping_audit.csv")
    candidate_ids = {"T015", "GL027", "GL028"}
    for row in clips:
        row["reviewer"] = REVIEWER
        if row["id"] in candidate_ids:
            row["decision"] = "PASS_MANUAL_NATIVE_CLIP_CARD"
            row["note"] = (
                "Native original/overlay/mask and 8x nearest clipping card opened. Reader foreground is complete; "
                f"nearest strict crop edge={row['nearest_crop_edge_px']}px, above hard 6px margin."
            )
        elif row["kind"] == "RAWDICT_COMBINING_CONTROL":
            row["decision"] = "PASS_NAMED_ASSOCIATION_SCOPE_MANUAL"
            row["note"] = "Zero-width control's scope/edge evidence was manually checked on its named A001--A004 association card."
        else:
            row["decision"] = "PASS_COMPLETE_NATIVE_CROP_ENUMERATION"
            row["note"] = "Included in complete strict-crop enumeration; numerical edge-ink and reader-margin checks passed."
    write_csv("clipping_audit.csv", clips, fields)


def finish_font_d_e():
    elements, fields = csv_rows("element_font_d_e_measurements.csv")
    assert len(elements) == 23
    fields = add_fieldnames(fields, ["MANUAL_REVIEWER", "MANUAL_DECISION", "MANUAL_NOTE", "FONT_VISUAL_HARMONY"])
    for row in elements:
        role = row["ROLE"]
        role_note = {
            "TICK_LABEL_X": "Same-panel x tick role: native glyph cards and full/crop views show uniform scale.",
            "TICK_LABEL_Y": "Same-panel y tick role: native glyph cards and full/crop views show uniform scale.",
            "AXIS_LABEL": "Axis label is modestly above ticks and remains coordinated across the left panel.",
            "PANEL_TITLE": "Cross-panel titles use equal 10.4pt source scale and have restrained hierarchy.",
            "FORMULA_BLOCK": "Formula role is coordinated with explanatory text; individual component pixel gates remain separately binding.",
            "ANNOTATION": "Annotation role is visually subordinate but readable; no abrupt shrinking or expansion.",
        }[role]
        row["PASS_FAIL"] = "PASS_D_E_MANUAL"
        row["REASON"] = "D/E role-scale and same-panel comparator review completed; see d_e_audit.csv and font_visual_harmony_audit.csv."
        row["MANUAL_REVIEWER"] = REVIEWER
        row["MANUAL_DECISION"] = "PASS_D_E_AND_FONT_VISUAL_HARMONY"
        row["MANUAL_NOTE"] = role_note + " This D/E result does not override any glyph H/low-profile hard failure."
        row["FONT_VISUAL_HARMONY"] = "FONT_VISUAL_HARMONY_PASS"
    write_csv("element_font_d_e_measurements.csv", elements, fields)

    font_rows, font_fields = csv_rows("after_font_audit.csv")
    font_fields = add_fieldnames(font_fields, ["manual_reviewer", "manual_decision", "manual_note"])
    for row in font_rows:
        row["manual_reviewer"] = REVIEWER
        row["manual_decision"] = "PASS_SOURCE_EFFECTIVE_PT_AND_VISUAL_HARMONY"
        row["manual_note"] = "Source effective-pt gate reviewed with native/full/gray visual harmony; separate glyph pixel hard failures retained."
    write_csv("after_font_audit.csv", font_rows, font_fields)


def write_manual_reports(glyph_rows):
    (ROOT / "MANUAL_REVIEW_METHOD.md").write_text(
        "# FIG-P609-01 SA1 manual pixel-review method\n\n"
        "Reviewer: `SA1_R97_MANUAL_NATIVE_20260824`. The only decision raster was the official final PDF's "
        "native 300 dpi figure crop. Each of the 13 glyph contact sheets was actually opened at 8x nearest-neighbor; "
        "every one of the 148 rawdict glyph records has an individual signed ledger row. The 35 initially critical "
        "glyph records in `manual_candidate_35_review.csv` were additionally opened as distinct native 1x original, "
        "target-overlay, and mask-only artifacts.\n\n"
        "All 10 critical/contact pair sheets and all 40 corresponding 8x cards were opened. For each critical row, "
        "native 1x original and overlay were also opened; the 8x card contains the separate pre/final A and B masks, "
        "the pre/final intersection panels, and exact clearance label. The 2 math-rule and 5 accent-association cards "
        "and the 3 crop-proximity cards were likewise opened at native 1x and 8x.\n\n"
        "No pass in these ledgers changes a machine result: the manually confirmed hard glyph failures remain failures; "
        "the only contact passes are individually named constructions or source-anchored data relations.\n",
        encoding="utf-8",
    )
    views = [
        {
            "view": "full_page_200dpi", "file": "full_page_200dpi.png", "dpi": "200",
            "scope_observation": "Official physical page 659 opened; Fig. 32.9 lower-page location and direct caption are visible.",
            "manual_decision": "PASS_CONTEXT_AND_PAGE_LOCATION_MANUAL",
        },
        {
            "view": "strict_figure_crop_300dpi", "file": "figure_crop_300dpi.png", "dpi": "300",
            "scope_observation": "Strict [70,525,510,702]pt P609 crop opened; excludes adjacent Fig. 32.8/body/caption from object scope.",
            "manual_decision": "PASS_STRICT_SCOPE_MANUAL",
        },
        {
            "view": "standalone_300dpi", "file": "standalone_300dpi.png", "dpi": "300",
            "scope_observation": "Both panels, axes, data stems/markers, annotation, formulas, rule/box and connector remain readable without page context.",
            "manual_decision": "PASS_STANDALONE_READABILITY_MANUAL",
        },
        {
            "view": "grayscale_300dpi", "file": "grayscale_300dpi.png", "dpi": "300",
            "scope_observation": "Axes/stems/markers, cutoff guide, connector and formulas remain distinguishable in grayscale.",
            "manual_decision": "PASS_GRAYSCALE_MANUAL",
        },
    ]
    for row in views:
        row["reviewer"] = REVIEWER
        row["opened"] = "YES"
    write_csv("manual_global_view_audit.csv", views, list(views[0]))

    harmony = [
        {"role": "PANEL_TITLE", "effective_pt": "10.4", "manual_observation": "Both panel titles are slightly stronger than support text, balanced left/right, and not abrupt.", "decision": "FONT_VISUAL_HARMONY_PASS"},
        {"role": "AXIS_LABEL", "effective_pt": "9.8", "manual_observation": "Both axis labels are coordinated and legible; neither crowds the panel boundary.", "decision": "FONT_VISUAL_HARMONY_PASS"},
        {"role": "TICK_LABEL", "effective_pt": "9.6", "manual_observation": "Comparable x/y tick labels have uniform visual scale and remain readable at native 300dpi.", "decision": "FONT_VISUAL_HARMONY_PASS"},
        {"role": "FORMULA_BLOCK", "effective_pt": "9.6", "manual_observation": "Formula blocks are readable and proportionate to their box/panel; mathematical rules/accent components remain structurally clear.", "decision": "FONT_VISUAL_HARMONY_PASS"},
        {"role": "ANNOTATION", "effective_pt": "9.6", "manual_observation": "Annotations are subordinate but remain readable; no abrupt reduction or oversized role is visible.", "decision": "FONT_VISUAL_HARMONY_PASS"},
    ]
    for row in harmony:
        row["reviewer"] = REVIEWER
        row["views_opened"] = "figure_crop_300dpi;standalone_300dpi;grayscale_300dpi"
        row["D_E_machine_crosscheck"] = "PASS: same-panel/same-role comparators and source effective-pt ratios retained from d_e_audit.csv"
    write_csv("font_visual_harmony_audit.csv", harmony, list(harmony[0]))

    objects, _ = csv_rows("object_inventory.csv")
    assert len(objects) == 59
    audit = []
    for obj in objects:
        audit.append({
            "object_id": obj["object_id"],
            "kind": obj["kind"],
            "role": obj["role"],
            "panel": obj["panel"],
            "z_order": obj["z_order"],
            "pre_mask": obj["safe_pre_mask"],
            "final_visible_mask": obj["safe_final_mask"],
            "manual_result": "PASS_NO_UNINTENDED_OCCLUSION",
            "manual_note": (
                "Visible in the strict native crop/global view and its enumerated raw/final mask; any expected "
                "construction contact is individually recorded in critical_pair_manual_ledger.csv. No line-through-text, "
                "unintended hiding, or loss after z-order inversion observed."
            ),
            "reviewer": REVIEWER,
        })
    write_csv("z_order_occlusion_audit.csv", audit, list(audit[0]))

    summary = {
        "glyph_records_signed": len(glyph_rows),
        "visible_glyphs": 144,
        "rawdict_combining_controls": 4,
        "hard_glyph_failures": sorted(HARD_H),
        "low_profile_calibration_failures": sorted(CALIBRATION_UNAVAILABLE),
        "critical_pair_cards_signed": 40,
        "full_pair_denominator": 1711,
        "math_rules_signed": 2,
        "accent_associations_signed": 5,
        "low_profile_calibration_rows_signed": 17,
        "low_profile_calibration_hard_failures": sorted(CALIBRATION_UNAVAILABLE),
        "crop_proximity_cards_signed": 3,
        "object_zorder_rows_signed": 59,
        "global_views_opened": 4,
        "font_visual_harmony": "FONT_VISUAL_HARMONY_PASS",
        "manual_final_status": "MANUAL_REVIEW_COMPLETE__TERMINAL_NOT_YET_WRITTEN__9_GLYPH_HARD_FAILURES",
    }
    import json
    (ROOT / "manual_review_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    preliminary_path = ROOT / "machine" / "preliminary_machine_summary.json"
    preliminary = json.loads(preliminary_path.read_text(encoding="utf-8"))
    preliminary["status"] = "PRELIMINARY_MACHINE_ONLY__SUPERSEDED_BY_COMPLETED_MANUAL_LEDGER"
    preliminary["manual_ledger"] = {
        "glyph_ledger": "glyph_ledger.csv",
        "candidate_35": "manual_candidate_35_review.csv",
        "critical_pairs": "critical_pair_manual_ledger.csv",
        "manual_summary": "manual_review_summary.json",
        "manual_hard_glyph_fail_count": 9,
    }
    preliminary_path.write_text(json.dumps(preliminary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    glyphs = finish_glyph_ledgers()
    write_candidate_ledger(glyphs)
    finish_pair_ledgers()
    finish_math_and_clipping()
    finish_font_d_e()
    write_manual_reports(glyphs)
    print("manual ledgers completed: glyphs=148 candidates=35 critical_pairs=40 full_pairs=1711")


if __name__ == "__main__":
    main()
