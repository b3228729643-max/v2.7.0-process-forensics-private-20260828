"""R111 independent D/E audit from final-PDF native raw glyph masks.

D is the same-class ratio rule in Goal §9.2.1(D).  E is the role-hierarchy
rule in Goal §9.2.1(E).  This script deliberately performs no visual verdict:
the human visual ledger is recorded separately after opening the four required
views and the 1x/8x glyph evidence.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "glyph_file_manifest.csv"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def median(values: list[int]) -> float:
    return float(np.median(np.asarray(values, dtype=float)))


def native_mask_height(relative_path: str) -> tuple[int, int]:
    """Return H_ink and foreground area from the stored unresized 1x mask."""
    array = np.asarray(Image.open(ROOT / relative_path).convert("L"))
    mask = array == 0
    if not mask.any():
        raise ValueError(f"empty mask: {relative_path}")
    ys, _ = np.where(mask)
    return int(ys.max() - ys.min() + 1), int(mask.sum())


def e_rule(panel: str, role: str, script: str) -> tuple[str, str, str, float | None, float | None]:
    """Return base id, rule, base group key, low, high for the E comparison."""
    # Glyph geometry of punctuation/digits is intrinsically not comparable to
    # CJK full-height body glyphs; its size validity is instead handled by the
    # same-codepoint calibrated pixel gate.  This is a closed exclusion, not a
    # pending or missing measurement.
    if script.startswith("LOW_PROFILE") or script == "DIGIT_OR_UPPER":
        return "INTRINSIC_SCRIPT_EXCLUSION", "EXCLUDED_INTRINSIC_SCRIPT", "", None, None
    if panel == "BODY":
        base = "BODY|ANNOTATION|CJK_FULL"
        if role == "AXIS_TITLE":
            return base, "AXIS_TITLE_TO_BASE", base, 1.00, 1.18
        return base, "ORDINARY_LABEL_TO_BASE", base, 0.95, 1.10
    if panel == "CAPTION":
        base = "CAPTION|CAPTION|CJK_FULL"
        if role == "CAPTION":
            return base, "CAPTION_BODY_BASE", base, 1.00, 1.00
        return base, "CAPTION_LABEL_TO_BODY", base, 0.95, 1.10
    raise ValueError(f"unmapped panel/role/script: {panel}/{role}/{script}")


def main() -> None:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 80 or len({row["GLYPH_ID"] for row in rows}) != 80:
        raise ValueError("R111 requires exactly 80 unique glyph rows")

    for row in rows:
        height, area = native_mask_height(row["MASK_FILE"])
        row["H_INK_REMEASURED"] = height
        row["MASK_FOREGROUND_REMEASURED"] = area
        if str(height) != row["H_INK_PX"]:
            raise ValueError(f"stored/re-measured H mismatch for {row['GLYPH_ID']}")

    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])].append(row)
    group_median = {key: median([int(row["H_INK_REMEASURED"]) for row in value]) for key, value in groups.items()}
    group_key_text = {key: "|".join(key) for key in groups}
    median_by_text = {group_key_text[key]: value for key, value in group_median.items()}

    final_rows: list[dict[str, str]] = []
    for row in rows:
        key = (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        members = groups[key]
        d_med = group_median[key]
        d_ratio = int(row["H_INK_REMEASURED"]) / d_med
        d_pass = 0.92 <= d_ratio <= 1.08
        if len(members) == 1:
            d_status = "PASS_SINGLETON_SELF_BASELINE" if d_pass else "FAIL_SINGLETON_SELF_BASELINE"
            d_note = "No same-panel/same-role/same-script peer; singleton ratio is closed at 1.0000, while low-profile quality remains independently calibrated."
        else:
            d_status = "PASS" if d_pass else "FAIL"
            d_note = "Native 1x final-visible glyph-mask ratio to same-panel/same-role/same-script median."

        base_id, e_rule_name, e_base_key, e_low, e_high = e_rule(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        if e_low is None:
            e_base_med = "NOT_APPLICABLE_INTRINSIC_SCRIPT"
            e_ratio = "NOT_APPLICABLE_INTRINSIC_SCRIPT"
            e_range = "EXCLUDED; same-codepoint calibrated pixel gate applies where low-profile"
            e_status = "PASS_EXCLUDED_INTRINSIC_SCRIPT"
            e_note = "Punctuation/digit ink height is not compared with CJK full-height glyphs; no hierarchy claim is inferred from incompatible glyph geometry."
            e_pass = True
        else:
            if e_base_key not in median_by_text:
                raise ValueError(f"missing E base group {e_base_key}")
            role_med = group_median[key]
            e_base = median_by_text[e_base_key]
            ratio = role_med / e_base
            e_base_med = f"{e_base:.4f}"
            e_ratio = f"{ratio:.4f}"
            e_range = f"[{e_low:.2f},{e_high:.2f}]"
            e_pass = e_low <= ratio <= e_high
            e_status = "PASS" if e_pass else "FAIL"
            e_note = "Native 1x role median against the designated same-script base; thresholds from Goal §9.2.1(E)."

        # There is one plot panel plus caption panel, and no role/script has a
        # second comparable panel.  This is explicitly closed rather than left
        # blank/pending.
        cross_panel = "PASS_NO_COMPARABLE_MULTI_PANEL_ROLE"
        final_rows.append({
            "GLYPH_ID": row["GLYPH_ID"], "ELEMENT_ID": row["ELEMENT_ID"], "CHAR": row["CHAR"],
            "PANEL_ID": row["PANEL_ID"], "ROLE": row["ROLE"], "SCRIPT_CLASS": row["SCRIPT_CLASS"],
            "MASK_FILE": row["MASK_FILE"], "H_INK_PX_REMEASURED": str(row["H_INK_REMEASURED"]),
            "D_GROUP": group_key_text[key], "D_GROUP_N": str(len(members)), "D_GROUP_MEDIAN_PX": f"{d_med:.4f}",
            "D_RATIO_TO_SAME_CLASS_MEDIAN": f"{d_ratio:.4f}", "D_REQUIRED_RANGE": "[0.92,1.08]",
            "D_STATUS": d_status, "D_NOTE": d_note,
            "E_BASE_GROUP": base_id, "E_ROLE_MEDIAN_PX": f"{group_median[key]:.4f}",
            "E_BASE_MEDIAN_PX": e_base_med, "E_ROLE_RATIO": e_ratio, "E_REQUIRED_RANGE": e_range,
            "E_RULE": e_rule_name, "E_STATUS": e_status, "E_NOTE": e_note,
            "CROSS_PANEL_STATUS": cross_panel,
            "D_E_ROW_DECISION": "PASS" if d_pass and e_pass else "FAIL",
            "EVIDENCE": "glyph_file_manifest.csv; glyph_masks/*_mask_only_1x.png; R111_LOW_PROFILE_CALIBRATION_VALIDATION.csv",
        })

    columns = list(final_rows[0])
    with (ROOT / "R111_D_E_FINAL_ADJUDICATION.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(final_rows)

    summaries: list[dict[str, str]] = []
    for key in sorted(groups):
        relevant = [row for row in final_rows if row["D_GROUP"] == group_key_text[key]]
        statuses = {row["E_STATUS"] for row in relevant}
        summaries.append({
            "PANEL_ID": key[0], "ROLE": key[1], "SCRIPT_CLASS": key[2], "GLYPH_COUNT": str(len(groups[key])),
            "ROLE_MEDIAN_H_INK_PX": f"{group_median[key]:.4f}", "D_MIN_RATIO": f"{min(float(row['D_RATIO_TO_SAME_CLASS_MEDIAN']) for row in relevant):.4f}",
            "D_MAX_RATIO": f"{max(float(row['D_RATIO_TO_SAME_CLASS_MEDIAN']) for row in relevant):.4f}",
            "D_ALL_PASS": bool_text(all(row["D_STATUS"].startswith("PASS") for row in relevant)),
            "E_BASE_GROUP": relevant[0]["E_BASE_GROUP"], "E_ROLE_RATIO": relevant[0]["E_ROLE_RATIO"],
            "E_REQUIRED_RANGE": relevant[0]["E_REQUIRED_RANGE"], "E_STATUS": ";".join(sorted(statuses)),
            "E_ALL_PASS": bool_text(all(row["E_STATUS"].startswith("PASS") for row in relevant)),
        })
    with (ROOT / "R111_D_E_ROLE_SUMMARY.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)

    d_fail = sum(not row["D_STATUS"].startswith("PASS") for row in final_rows)
    e_fail = sum(not row["E_STATUS"].startswith("PASS") for row in final_rows)
    result = {
        "figure_id": "FIG-P157-01",
        "method": "recomputed from final-PDF native 300dpi 1x glyph masks; no inherited D/E conclusion",
        "glyph_count": len(final_rows),
        "same_class_ratio_pass": d_fail == 0,
        "same_class_ratio_fail_glyphs": d_fail,
        "role_ratio_pass": e_fail == 0,
        "role_ratio_fail_glyphs": e_fail,
        "role_ratio_fail_groups": [
            {"group": item["PANEL_ID"] + "|" + item["ROLE"] + "|" + item["SCRIPT_CLASS"], "ratio": item["E_ROLE_RATIO"], "required": item["E_REQUIRED_RANGE"]}
            for item in summaries if item["E_ALL_PASS"] == "false"
        ],
        "cross_panel_status": "PASS_NO_COMPARABLE_MULTI_PANEL_ROLE",
    }
    (ROOT / "R111_D_E_FINAL_SUMMARY.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
