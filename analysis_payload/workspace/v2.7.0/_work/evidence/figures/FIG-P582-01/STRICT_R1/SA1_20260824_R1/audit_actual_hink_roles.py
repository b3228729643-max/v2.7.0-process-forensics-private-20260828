"""Actual final-mask H_INK D/E audit, with no PDF-span proxy.

All heights below are measured from the 1:1 native 300dpi final glyph masks.
Cross-script font proxies are intentionally excluded from every PASS decision.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent


def med(values: list[float]) -> float:
    return float(statistics.median(values))


def h_ink(path: Path) -> int:
    arr = np.array(Image.open(path).convert("L")) < 128
    ys, xs = np.where(arr)
    return 0 if len(ys) == 0 else int(ys.max() - ys.min() + 1)


def panel(eid: str) -> str:
    return "CAPTION" if 36 <= int(eid[1:]) <= 45 else "BODY"


def keytext(key: tuple[str, str, str]) -> str:
    return "|".join(key)


def main() -> None:
    with (ROOT / "after_pixel_measurements.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        metrics = {r["GLYPH_ID"]: r for r in csv.DictReader(fh) if r["LEVEL"] == "GLYPH"}
    with (ROOT / "glyph_final_mask_manifest.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        final = {r["GLYPH_ID"]: r for r in csv.DictReader(fh)}
    with (ROOT / "glyph_file_manifest.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        glyph_manifest = list(csv.DictReader(fh))

    glyphs: list[dict[str, object]] = []
    for row in glyph_manifest:
        gid = row["GLYPH_ID"]
        m = metrics[gid]
        eid = row["ELEMENT_ID"]
        # Revision 111 keeps low-profile punctuation out of a misleading
        # comma/dot/semicolon mixed-height bucket.  It is still audited in
        # PANEL×ROLE×SCRIPT scope, but the scope carries its exact codepoint;
        # H_INK and ink-area calibration is closed separately in
        # low_profile_punctuation_calibration.csv.
        if m.get("LOW_PROFILE_PUNCTUATION") == "true":
            script = "LOW_PROFILE_PUNCTUATION_U" + f"{ord(row['CHAR']):04X}"
        else:
            script = m["SCRIPT_CLASS"]
        glyphs.append({
            "glyph_id": gid,
            "element_id": eid,
            "char": row["CHAR"],
            "panel": panel(eid),
            "role": m["ROLE"],
            "script": script,
            "effective_pt": float(m["EFFECTIVE_PT"]),
            "h_ink": h_ink(ROOT / final[gid]["FINAL_VISIBLE_MASK"]),
            "mask_status": final[gid]["STATUS"],
        })

    # First, use a robust median of glyph H_INK for each semantic element and
    # script class.  This avoids one unusually complex CJK glyph standing in
    # for a whole text object while retaining only actual final-mask pixels.
    element_groups: dict[tuple[str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for g in glyphs:
        element_groups[(g["panel"], g["role"], g["script"], g["element_id"])].append(g)
    element_rows: list[dict[str, object]] = []
    group_elements: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for (p, role, script, eid), items in sorted(element_groups.items()):
        values = [int(x["h_ink"]) for x in items]
        row = {
            "PANEL_ID": p, "ROLE": role, "SCRIPT_CLASS": script,
            "ELEMENT_ID": eid, "GLYPH_IDS": " ".join(str(x["glyph_id"]) for x in items),
            "GLYPH_COUNT": len(items), "H_INK_VALUES_PX": " ".join(str(v) for v in values),
            "H_INK_ELEMENT_MEDIAN_PX": round(med(values), 3),
            "H_INK_ELEMENT_MIN_PX": min(values), "H_INK_ELEMENT_MAX_PX": max(values),
            "FINAL_MASK_STATUS_SET": ";".join(sorted({str(x["mask_status"]) for x in items})),
            "COORDINATE": "native final-PDF 300dpi 1:1 final glyph masks",
        }
        element_rows.append(row)
        group_elements[(p, role, script)].append(row)

    audit_rows: list[dict[str, object]] = []
    group_medians: dict[tuple[str, str, str], float] = {}
    for key, rows in sorted(group_elements.items()):
        vals = [float(r["H_INK_ELEMENT_MEDIAN_PX"]) for r in rows]
        gm = med(vals)
        group_medians[key] = gm
        ratios = [v / gm for v in vals] if gm else []
        if len(rows) < 2:
            d_status, d_ok = "N/A_SINGLE_SEMANTIC_ELEMENT", True
        else:
            d_ok = min(ratios) >= 0.92 and max(ratios) <= 1.08
            d_status = "PASS" if d_ok else "FAIL"
        audit_rows.append({
            "AUDIT_LEVEL": "PANEL_ROLE_SCRIPT", "PANEL_ID": key[0], "ROLE": key[1], "SCRIPT_CLASS": key[2],
            "ELEMENT_IDS": " ".join(r["ELEMENT_ID"] for r in rows), "ELEMENT_COUNT": len(rows),
            "GLYPH_COUNT": sum(int(r["GLYPH_COUNT"]) for r in rows),
            "H_INK_ELEMENT_MEDIANS_PX": " ".join(str(r["H_INK_ELEMENT_MEDIAN_PX"]) for r in rows),
            "H_INK_GROUP_MEDIAN_PX": round(gm, 3), "H_INK_MIN_TO_GROUP_RATIO": round(min(ratios), 4) if ratios else "",
            "H_INK_MAX_TO_GROUP_RATIO": round(max(ratios), 4) if ratios else "", "D_REQUIRED_RANGE": "[0.92,1.08]",
            "D_STATUS": d_status, "D_PASS_OR_NA": str(d_ok).lower(),
            "SAME_ROLE_SCOPE": "computed separately in role_script scope", "SAME_ROLE_EXTREME_RATIO": "",
            "SAME_ROLE_STATUS": "SEE_ROLE_SCRIPT_ROWS", "E_STATUS": "SEE_role_e_actual_hink_audit.csv",
            "PASS_FAIL": "PASS" if d_ok else "FAIL",
            "NOTE": "actual H_INK only; no PDF_SPAN_PT or cross-script proxy",
        })

    # Same-role medians are comparable only in the same script class.  This
    # applies the schema's 1.08/1.10 limits without using cross-script proxies.
    role_script_rows: list[dict[str, object]] = []
    by_role_script: dict[tuple[str, str], list[tuple[tuple[str, str, str], float]]] = defaultdict(list)
    for k, v in group_medians.items():
        by_role_script[(k[1], k[2])].append((k, v))
    for (role, script), items in sorted(by_role_script.items()):
        vals = [v for _, v in items]
        panels = {k[0] for k, _ in items}
        ratio = max(vals) / min(vals) if min(vals) else float("inf")
        if len(items) < 2:
            status, ok, limit = "N/A_SINGLE_GROUP", True, "N/A"
        else:
            limit_value = 1.10 if len(panels) > 1 else 1.08
            limit = str(limit_value)
            ok = ratio <= limit_value
            status = "PASS" if ok else "FAIL"
        role_script_rows.append({
            "AUDIT_LEVEL": "ROLE_SCRIPT", "PANEL_ID": ";".join(sorted(panels)), "ROLE": role,
            "SCRIPT_CLASS": script, "ELEMENT_IDS": " ".join(k[0] + ":" + k[1] for k, _ in items),
            "ELEMENT_COUNT": len(items), "GLYPH_COUNT": "", "H_INK_ELEMENT_MEDIANS_PX": " ".join(str(round(v,3)) for _, v in items),
            "H_INK_GROUP_MEDIAN_PX": "", "H_INK_MIN_TO_GROUP_RATIO": "", "H_INK_MAX_TO_GROUP_RATIO": "",
            "D_REQUIRED_RANGE": "", "D_STATUS": "N/A_ROLE_SCOPE", "D_PASS_OR_NA": "true",
            "SAME_ROLE_SCOPE": "cross-panel same-role same-script" if len(panels) > 1 else "same-panel same-role same-script",
            "SAME_ROLE_EXTREME_RATIO": round(ratio, 4) if len(items) >= 2 else "", "SAME_ROLE_STATUS": status,
            "E_STATUS": "SEE_role_e_actual_hink_audit.csv", "PASS_FAIL": "PASS" if ok else "FAIL",
            "NOTE": f"actual H_INK limit {limit}; no cross-script proxy",
        })

    # Applicable E comparisons.  Every target and base is explicitly the same
    # script class.  Groups without a defensible same-script ordinary baseline
    # are listed as N/A with reason rather than being given a proxy verdict.
    def K(p: str, r: str, s: str) -> tuple[str, str, str]: return (p, r, s)
    # BASE is always a distinct, same-SCRIPT_CLASS visible group.  In
    # particular, an annotation group is never permitted to "pass" merely by
    # dividing its own median by itself.  No PDF emitted-span/font-size proxy
    # enters this list.
    e_specs = [
        ("E_AXIS_TITLE_CJK", K("BODY", "AXIS_TITLE", "CJK_FULL"), K("BODY", "ANNOTATION", "CJK_FULL"), 1.00, 1.18, "axis title/unit; body ordinary CJK annotation BASE"),
        ("E_ANNOTATION_DIGIT", K("BODY", "ANNOTATION", "DIGIT_OR_UPPER"), K("BODY", "TICK_LABEL", "DIGIT_OR_UPPER"), 0.95, 1.10, "ordinary numeric annotation; same-script tick BASE"),
        ("E_NUMERIC_VALUE_DIGIT", K("BODY", "NUMERIC_VALUE", "DIGIT_OR_UPPER"), K("BODY", "TICK_LABEL", "DIGIT_OR_UPPER"), 0.95, 1.10, "ordinary data value; same-script tick BASE"),
        ("E_NUMERIC_VALUE_DOT", K("BODY", "NUMERIC_VALUE", "LOW_PROFILE_PUNCTUATION_U002E"), K("BODY", "TICK_LABEL", "LOW_PROFILE_PUNCTUATION_U002E"), 0.95, 1.10, "numeric decimal point; same-codepoint same-script tick-dot BASE"),
        ("E_FORMULA_LOWER", K("BODY", "FORMULA", "LOWERCASE_OR_GREEK"), K("BODY", "AXIS_TITLE", "LOWERCASE_OR_GREEK"), 1.00, 1.18, "formula base glyph; only distinct same-script general-text BASE"),
        ("E_FORMULA_OPERATOR", K("BODY", "FORMULA", "MATH_OPERATOR"), K("BODY", "ANNOTATION", "MATH_OPERATOR"), 1.00, 1.18, "formula operator; distinct same-script annotation-operator BASE"),
        ("E_CAPTION_CJK", K("CAPTION", "CAPTION", "CJK_FULL"), K("BODY", "ANNOTATION", "CJK_FULL"), 0.90, 1.25, "predeclared caption emphasis; body ordinary CJK annotation BASE"),
        ("E_CAPTION_DIGIT", K("CAPTION", "CAPTION", "DIGIT_OR_UPPER"), K("BODY", "TICK_LABEL", "DIGIT_OR_UPPER"), 0.90, 1.25, "predeclared caption emphasis digit; same-script tick BASE"),
        ("E_CAPTION_LOWER", K("CAPTION", "CAPTION", "LOWERCASE_OR_GREEK"), K("BODY", "AXIS_TITLE", "LOWERCASE_OR_GREEK"), 0.90, 1.25, "predeclared caption emphasis lowercase; same-script axis-text BASE"),
        ("E_CAPTION_DOT", K("CAPTION", "CAPTION", "LOW_PROFILE_PUNCTUATION_U002E"), K("BODY", "TICK_LABEL", "LOW_PROFILE_PUNCTUATION_U002E"), 0.90, 1.25, "predeclared caption emphasis decimal point; same-codepoint same-script tick-dot BASE"),
    ]
    e_rows: list[dict[str, object]] = []
    covered: set[tuple[str, str, str]] = set()
    for rule_id, target, base, lo, hi, label in e_specs:
        if target not in group_medians or base not in group_medians:
            continue
        ratio = group_medians[target] / group_medians[base]
        ok = lo <= ratio <= hi
        covered.add(target)
        e_rows.append({
            "RULE_ID": rule_id, "TARGET_PANEL_ROLE_SCRIPT": keytext(target), "BASE_PANEL_ROLE_SCRIPT": keytext(base),
            "TARGET_H_INK_MEDIAN_PX": round(group_medians[target], 3), "BASE_H_INK_MEDIAN_PX": round(group_medians[base], 3),
            "E_RATIO": round(ratio, 4), "REQUIRED_RANGE": f"[{lo:.2f},{hi:.2f}]", "E_STATUS": "PASS" if ok else "FAIL",
            "E_PASS_OR_NA": str(ok).lower(), "BASE_SELECTION": keytext(base) + "; actual final-mask H_INK median",
            "BASIS": label + "; same SCRIPT_CLASS actual final-mask H_INK", "NOTE": "no PDF span proxy",
        })
    for key in sorted(group_medians):
        if key in covered:
            continue
        e_rows.append({
            "RULE_ID": "E_NA_" + "_".join(key), "TARGET_PANEL_ROLE_SCRIPT": keytext(key), "BASE_PANEL_ROLE_SCRIPT": "",
            "TARGET_H_INK_MEDIAN_PX": round(group_medians[key], 3), "BASE_H_INK_MEDIAN_PX": "", "E_RATIO": "",
            "REQUIRED_RANGE": "N/A", "E_STATUS": "N/A_WITH_BASIS", "E_PASS_OR_NA": "true",
            "BASE_SELECTION": "", "BASIS": "no distinct defensible ordinary BASE in the same script class; self-comparison and cross-script proxy prohibited", "NOTE": "not a PASS claim; source absolute font gate remains separately false",
        })
    # The figure contains neither a legend nor a panel label.  These rows
    # explicitly close the named E categories rather than silently omitting
    # them from the audit.
    for rule_id, target, reason in [
        ("E_NA_LEGEND_ABSENT", "ABSENT|LEGEND|N/A", "no visible legend in FIG-P582-01"),
        ("E_NA_PANEL_LABEL_ABSENT", "ABSENT|PANEL_LABEL|N/A", "no visible panel label in FIG-P582-01"),
    ]:
        e_rows.append({
            "RULE_ID": rule_id, "TARGET_PANEL_ROLE_SCRIPT": target, "BASE_PANEL_ROLE_SCRIPT": "",
            "TARGET_H_INK_MEDIAN_PX": "", "BASE_H_INK_MEDIAN_PX": "", "E_RATIO": "",
            "REQUIRED_RANGE": "N/A", "E_STATUS": "N/A_WITH_BASIS", "E_PASS_OR_NA": "true",
            "BASE_SELECTION": "", "BASIS": reason + "; no text object exists to compare", "NOTE": "not a PASS claim; no cross-script proxy",
        })

    fields = [
        "AUDIT_LEVEL", "PANEL_ID", "ROLE", "SCRIPT_CLASS", "ELEMENT_IDS", "ELEMENT_COUNT", "GLYPH_COUNT",
        "H_INK_ELEMENT_MEDIANS_PX", "H_INK_GROUP_MEDIAN_PX", "H_INK_MIN_TO_GROUP_RATIO", "H_INK_MAX_TO_GROUP_RATIO",
        "D_REQUIRED_RANGE", "D_STATUS", "D_PASS_OR_NA", "SAME_ROLE_SCOPE", "SAME_ROLE_EXTREME_RATIO",
        "SAME_ROLE_STATUS", "E_STATUS", "PASS_FAIL", "NOTE",
    ]
    with (ROOT / "role_hierarchy_audit.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(audit_rows + role_script_rows)
    with (ROOT / "role_hierarchy_actual_hink_elements.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(element_rows[0])); w.writeheader(); w.writerows(element_rows)
    with (ROOT / "role_e_actual_hink_audit.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(e_rows[0])); w.writeheader(); w.writerows(e_rows)

    d_fails = sum(r["D_STATUS"] == "FAIL" for r in audit_rows)
    role_fails = sum(r["SAME_ROLE_STATUS"] == "FAIL" for r in role_script_rows)
    e_fails = sum(r["E_STATUS"] == "FAIL" for r in e_rows)
    summary = {
        "coordinate": "native final-PDF 300dpi 1:1 final glyph masks",
        "pdf_span_proxy_used_for_pass": False,
        "panel_role_script_group_count": len(group_medians),
        "element_script_row_count": len(element_rows),
        "d_applicable_fail_count": d_fails,
        "same_role_applicable_fail_count": role_fails,
        "e_applicable_fail_count": e_fails,
        "e_na_with_basis_count": sum(r["E_STATUS"] == "N/A_WITH_BASIS" for r in e_rows),
        "d_hink_pass": d_fails == 0,
        "same_role_hink_pass": role_fails == 0,
        "e_hink_applicable_pass": e_fails == 0,
        "e_coverage_closed_with_basis": all(r["E_STATUS"] in {"PASS", "FAIL", "N/A_WITH_BASIS"} for r in e_rows),
    }
    (ROOT / "role_actual_hink_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
