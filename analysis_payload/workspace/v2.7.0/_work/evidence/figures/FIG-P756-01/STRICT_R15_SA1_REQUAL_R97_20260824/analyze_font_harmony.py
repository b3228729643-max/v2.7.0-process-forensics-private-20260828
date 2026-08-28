"""Derive element-level D/E typography metrics without making visual decisions."""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent

def med(values: list[float]) -> float:
    return float(statistics.median(values))

def fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.6f}"

def main() -> None:
    px = list(csv.DictReader((OUT / "after_pixel_measurements.csv").open(encoding="utf-8-sig")))
    fonts = {r["ELEMENT_ID"]: r for r in csv.DictReader((OUT / "after_font_audit.csv").open(encoding="utf-8-sig"))}
    # Low-profile punctuation follows its own independently calibrated gate;
    # it is intentionally excluded from general height-median comparisons.
    comparable = [r for r in px if r["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION"]
    role_script_values: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    elem_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in comparable:
        key = (r["PANEL_ID"], r["ROLE"], r["SCRIPT_CLASS"])
        role_script_values[key].append(float(r["H_INK_PX"]))
        elem_values[(r["ELEMENT_ID"], r["SCRIPT_CLASS"])].append(float(r["H_INK_PX"]))
    role_medians = {key: med(values) for key, values in role_script_values.items()}
    element_rows = []
    per_role_element_medians: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for (element, script), values in sorted(elem_values.items()):
        f = fonts[element]
        key = (f["PANEL_ID"], f["ROLE"], script)
        element_median = med(values)
        baseline = role_medians[key]
        ratio = element_median / baseline
        per_role_element_medians[key].append(element_median)
        element_rows.append({
            "ELEMENT_ID": element, "PANEL_ID": f["PANEL_ID"], "ROLE": f["ROLE"], "SCRIPT_CLASS": script,
            "EFFECTIVE_PT": f["EFFECTIVE_PT"], "SOURCE_PT_GATE": "PASS" if float(f["EFFECTIVE_PT"]) >= 9.5 else "FAIL",
            "VISIBLE_GLYPH_COUNT_CLASS": len(values), "ELEMENT_MEDIAN_H_INK_PX": fmt(element_median),
            "ROLE_SCRIPT_MEDIAN_H_INK_PX": fmt(baseline), "ELEMENT_TO_ROLE_MEDIAN_RATIO": fmt(ratio),
            "ELEMENT_RATIO_GATE_0.92_TO_1.08": "PASS" if 0.92 <= ratio <= 1.08 else "FAIL",
            "SOURCE_LINE": f["SOURCE_LINE"],
        })
    extrema = {key: (min(vals), max(vals), max(vals) / min(vals)) for key, vals in per_role_element_medians.items()}
    for row in element_rows:
        key = (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        lo, hi, ratio = extrema[key]
        row["SAME_PANEL_ROLE_SCRIPT_MIN_ELEMENT_MEDIAN"] = fmt(lo)
        row["SAME_PANEL_ROLE_SCRIPT_MAX_ELEMENT_MEDIAN"] = fmt(hi)
        row["SAME_PANEL_ROLE_SCRIPT_EXTREME_RATIO"] = fmt(ratio)
        row["SAME_PANEL_ROLE_SCRIPT_GATE_LE_1.08"] = "PASS" if ratio <= 1.08 else "FAIL"
    # Cross-panel comparisons are meaningful only where the exact role/script
    # has observations on more than one panel.
    cross: dict[tuple[str, str], list[tuple[float, int]]] = defaultdict(list)
    for key, values in per_role_element_medians.items():
        panel, role, script = key
        cross[(role, script)].append((med(values), len(role_script_values[key])))
    # A singleton `a` versus a singleton `b` is the same broad script class
    # but not a reliable cross-panel size sample: ascender/x-height geometry
    # would falsely turn a common declared size into a size failure.  Mark this
    # explicitly N/A rather than grouping by exact characters or silently PASS.
    cross_ratio = {
        key: max(v for v, _ in vals) / min(v for v, _ in vals)
        for key, vals in cross.items()
        if len(vals) > 1 and all(n >= 3 for _, n in vals)
    }
    for row in element_rows:
        key = (row["ROLE"], row["SCRIPT_CLASS"])
        if key not in cross_ratio:
            values = cross.get(key, [])
            reason = "N/A_SINGLE_PANEL" if len(values) <= 1 else "N/A_INSUFFICIENT_UNMATCHED_GLYPH_DISTRIBUTION"
            row["CROSS_PANEL_ROLE_SCRIPT_EXTREME_RATIO"] = reason
            row["CROSS_PANEL_GATE_LE_1.10"] = reason
        else:
            ratio = cross_ratio[key]
            row["CROSS_PANEL_ROLE_SCRIPT_EXTREME_RATIO"] = fmt(ratio)
            row["CROSS_PANEL_GATE_LE_1.10"] = "PASS" if ratio <= 1.10 else "FAIL"
    # Add the eight calibrated low-profile rows for a complete 25-element
    # source-font inventory while preserving their distinct gate.
    low_by_element: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in px:
        if r["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION": low_by_element[r["ELEMENT_ID"]].append(r)
    for element, rows in sorted(low_by_element.items()):
        f = fonts[element]
        element_rows.append({
            "ELEMENT_ID": element, "PANEL_ID": f["PANEL_ID"], "ROLE": f["ROLE"], "SCRIPT_CLASS": "LOW_PROFILE_PUNCTUATION",
            "EFFECTIVE_PT": f["EFFECTIVE_PT"], "SOURCE_PT_GATE": "PASS" if float(f["EFFECTIVE_PT"]) >= 9.5 else "FAIL",
            "VISIBLE_GLYPH_COUNT_CLASS": len(rows), "ELEMENT_MEDIAN_H_INK_PX": fmt(med([float(x["H_INK_PX"]) for x in rows])),
            "ROLE_SCRIPT_MEDIAN_H_INK_PX": "N/A_CALIBRATED", "ELEMENT_TO_ROLE_MEDIAN_RATIO": "N/A_CALIBRATED",
            "ELEMENT_RATIO_GATE_0.92_TO_1.08": "N/A_CALIBRATED", "SOURCE_LINE": f["SOURCE_LINE"],
            "SAME_PANEL_ROLE_SCRIPT_MIN_ELEMENT_MEDIAN": "N/A_CALIBRATED", "SAME_PANEL_ROLE_SCRIPT_MAX_ELEMENT_MEDIAN": "N/A_CALIBRATED",
            "SAME_PANEL_ROLE_SCRIPT_EXTREME_RATIO": "N/A_CALIBRATED", "SAME_PANEL_ROLE_SCRIPT_GATE_LE_1.08": "N/A_CALIBRATED",
            "CROSS_PANEL_ROLE_SCRIPT_EXTREME_RATIO": "N/A_CALIBRATED", "CROSS_PANEL_GATE_LE_1.10": "N/A_CALIBRATED",
        })
    element_rows.sort(key=lambda r: (r["ELEMENT_ID"], r["SCRIPT_CLASS"]))
    failures = [r for r in element_rows if "FAIL" in r.values()]
    with (OUT / "font_harmony_by_element.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(element_rows[0])); writer.writeheader(); writer.writerows(element_rows)
    # Role / source hierarchy summary needed for explicit manual visual review.
    source_groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in fonts.values(): source_groups[(row["PANEL_ID"], row["ROLE"])].append(float(row["EFFECTIVE_PT"]))
    summary = []
    for (panel, role), vals in sorted(source_groups.items()):
        summary.append({"PANEL_ID": panel, "ROLE": role, "EFFECTIVE_PT_MIN": fmt(min(vals)), "EFFECTIVE_PT_MAX": fmt(max(vals)),
                        "SOURCE_SAME_PANEL_RATIO": fmt(max(vals)/min(vals)), "SOURCE_SAME_PANEL_ABS_DIFF_PT": fmt(max(vals)-min(vals)),
                        "SOURCE_GATE": "PASS" if max(vals)/min(vals) <= 1.03 and max(vals)-min(vals) <= .25 else "FAIL"})
    all_pts = [float(r["EFFECTIVE_PT"]) for r in fonts.values()]
    summary.append({"PANEL_ID": "ALL", "ROLE": "NORMAL_TEXT_AND_TITLES", "EFFECTIVE_PT_MIN": fmt(min(all_pts)), "EFFECTIVE_PT_MAX": fmt(max(all_pts)),
                    "SOURCE_SAME_PANEL_RATIO": fmt(max(all_pts)/min(all_pts)), "SOURCE_SAME_PANEL_ABS_DIFF_PT": fmt(max(all_pts)-min(all_pts)),
                    "SOURCE_GATE": "INFO: panel-title emphasis ratio"})
    with (OUT / "font_harmony_role_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    cross_source = []
    for role in sorted({role for _, role in source_groups}):
        panels = sorted({panel for panel, r in source_groups if r == role})
        vals = [v for (panel, r), group in source_groups.items() if r == role for v in group]
        if len(panels) <= 1:
            ratio, gate = "N/A_SINGLE_PANEL", "N/A_SINGLE_PANEL"
        else:
            value = max(vals) / min(vals)
            ratio, gate = fmt(value), "PASS" if value <= 1.05 else "FAIL"
        cross_source.append({"ROLE": role, "PANELS": ";".join(panels), "EFFECTIVE_PT_MIN": fmt(min(vals)),
                             "EFFECTIVE_PT_MAX": fmt(max(vals)), "CROSS_PANEL_SOURCE_RATIO": ratio,
                             "CROSS_PANEL_SOURCE_GATE_LE_1.05": gate})
    with (OUT / "font_harmony_crosspanel_source.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(cross_source[0])); writer.writeheader(); writer.writerows(cross_source)
    print(f"element_script_rows={len(element_rows)} failures={len(failures)} min_pt={min(all_pts):.2f} max_pt={max(all_pts):.2f}")

if __name__ == "__main__":
    main()
