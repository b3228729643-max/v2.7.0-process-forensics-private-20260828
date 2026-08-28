from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = Path(r"src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
SOURCE = WORKTREE / SOURCE_REL
R18_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R18_SA2_SOURCE_R3_STATIC_ONLY_20260825")
BEFORE_SNAPSHOT = R18_ROOT / "SOURCE_R3_SNAPSHOT.tex"
R19_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R19_SA2_R18_DIRECT_BUILD_20260825")
BEFORE_R4_SHA = "CDAD08C2FDD21B4DA1C1F67431B6743C703CA6629C5F6E346C671FC48C01DB0D"
IBM = Path(r"D:\texlive\2026\texmf-dist\fonts\opentype\ibm\plex\IBMPlexMath-Regular.otf")
LIBERTINUS = Path(r"D:\texlive\2026\texmf-dist\fonts\opentype\public\libertinus-fonts\LibertinusMath-Regular.otf")
MEZENETS = Path(r"D:\texlive\2026\texmf-dist\fonts\opentype\public\fonts-churchslavonic\MezenetsUnicode.otf")
STIX = Path(r"D:\texlive\2026\texmf-dist\fonts\opentype\public\stix2-otf\STIXTwoMath-Regular.otf")
ROLE_PT = 11.6
SCALE_300 = 300 / 72


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=False)


def write_json(name: str, value: object) -> None:
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def glyph_metrics(font_path: Path, codepoint: int, point_size: float) -> dict[str, object]:
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    glyph_name = cmap.get(codepoint)
    if glyph_name is None:
        raise RuntimeError(f"{font_path.name} lacks U+{codepoint:04X}")
    glyph_set = font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    if pen.bounds is None:
        raise RuntimeError(f"empty glyph U+{codepoint:04X}")
    x0, y0, x1, y1 = pen.bounds
    units_per_em = font["head"].unitsPerEm
    height_units = y1 - y0
    continuous_px = height_units / units_per_em * point_size * SCALE_300
    return {
        "font": font_path.name,
        "codepoint": f"U+{codepoint:04X}",
        "glyph_name": glyph_name,
        "bounds_font_units": [x0, y0, x1, y1],
        "height_units": height_units,
        "units_per_em": units_per_em,
        "point_size": point_size,
        "continuous_height_at_300dpi_px": round(continuous_px, 9),
        "conservative_integer_envelope_px": [math.floor(continuous_px), math.ceil(continuous_px)],
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    before_bytes = BEFORE_SNAPSHOT.read_bytes()
    text = source_bytes.decode("utf-8")
    before_text = before_bytes.decode("utf-8")
    after_sha = sha256(SOURCE)
    if hashlib.sha256(before_bytes).hexdigest().upper() != BEFORE_R4_SHA:
        raise RuntimeError("R18 snapshot is not the authorized R4 before identity")

    status = run("git", "-C", str(WORKTREE), "status", "--short")
    status_lines = [line for line in status.stdout.splitlines() if line.strip()]
    if status.returncode != 0 or len(status_lines) != 1 or "fig_v5_c05_dependency_graph.tex" not in status_lines[0]:
        raise RuntimeError(f"scope violation: {status_lines} {status.stderr}")
    diff_check = run("git", "-C", str(WORKTREE), "diff", "--check")
    if diff_check.returncode != 0 or diff_check.stdout or diff_check.stderr:
        raise RuntimeError(f"git diff-check failed: {diff_check.stdout}{diff_check.stderr}")
    exact_diff = run("git", "diff", "--no-index", "--", str(BEFORE_SNAPSHOT), str(SOURCE))
    if exact_diff.returncode not in (0, 1):
        raise RuntimeError(exact_diff.stderr)

    before_lines = before_text.splitlines()
    after_lines = text.splitlines()
    if len(before_lines) != len(after_lines):
        raise RuntimeError("R4 changed line count")
    changes = [
        {"line": index + 1, "before": old, "after": new}
        for index, (old, new) in enumerate(zip(before_lines, after_lines))
        if old != new
    ]
    if len(changes) != 7:
        raise RuntimeError(f"R4 exact changed-line denominator {len(changes)} != 7")
    for change in changes:
        old, new = change["before"], change["after"]
        allowed = (
            ("10.7pt BASE_MATH" in old and "11.6pt BASE_MATH" in new)
            or (old.count('at 10.7pt') == 1 and new == old.replace('at 10.7pt', 'at 11.6pt'))
            or (old.count(r"\fontsize{10.7pt}{12.8pt}") == 1 and new == old.replace(r"\fontsize{10.7pt}{12.8pt}", r"\fontsize{11.6pt}{13.8pt}"))
        )
        if not allowed:
            raise RuntimeError(f"unapproved R4 line change: {change}")

    checks = {
        "status": "P654_SOURCE_R4_STATIC_READY_REQUEST_BUILD_SLOT",
        "before_r4_sha256": BEFORE_R4_SHA,
        "after_r4_sha256": after_sha,
        "after_r4_bytes": SOURCE.stat().st_size,
        "modified_business_source_count": 1,
        "exact_changed_line_count": len(changes),
        "exact_changed_lines": changes,
        "git_diff_check_pass": True,
        "direct_font_at_11_6_count": len(re.findall(r'at 11\.6pt', text)),
        "wrapper_fontsize_11_6_13_8_count": text.count(r"\fontsize{11.6pt}{13.8pt}"),
        "legacy_direct_font_at_10_7_count": len(re.findall(r'at 10\.7pt', text)),
        "legacy_wrapper_fontsize_10_7_count": text.count(r"\fontsize{10.7pt}{12.8pt}"),
        "math_plus_u002b_definition_count": text.count(r'\char"002B'),
        "uppercase_total_N_u004e_definition_count": text.count(r'\char"004E'),
        "target_n_u1d45b_definition_count": text.count(r'\char"1D45B'),
        "alpha_u1d6fc_definition_count": text.count(r'\char"1D6FC'),
        "small_cap_u0274_count": text.count(r'\char"0274'),
        "undefined_n0_count": text.count("n_0"),
        "text_plus_count": len(re.findall(r"\\text\s*\{\s*\+\s*\}", text)),
        "resizebox_count": text.count(r"\resizebox"),
        "scalebox_count": text.count(r"\scalebox"),
        "transform_shape_count": text.count("transform shape"),
        "lda_coordinate_retained_count": text.count("(6.35,-2.75)"),
        "seven_relation_count": len(re.findall(r"\\draw\[(?:arr|interp|application)\]", text)),
        "tex_invocations": 0,
        "commit_created": False,
        "fresh_role_started": False,
        "manual_fields_created": 0,
    }
    expected = {
        "direct_font_at_11_6_count": 3,
        "wrapper_fontsize_11_6_13_8_count": 3,
        "legacy_direct_font_at_10_7_count": 0,
        "legacy_wrapper_fontsize_10_7_count": 0,
        "math_plus_u002b_definition_count": 1,
        "uppercase_total_N_u004e_definition_count": 1,
        "target_n_u1d45b_definition_count": 1,
        "alpha_u1d6fc_definition_count": 1,
        "small_cap_u0274_count": 0,
        "undefined_n0_count": 0,
        "text_plus_count": 0,
        "resizebox_count": 0,
        "scalebox_count": 0,
        "transform_shape_count": 0,
        "lda_coordinate_retained_count": 1,
        "seven_relation_count": 7,
    }
    mismatches = {key: {"actual": checks[key], "expected": value} for key, value in expected.items() if checks[key] != value}
    if mismatches:
        raise RuntimeError(f"static source checks failed: {mismatches}")
    checks["hard_check_mismatches"] = mismatches
    checks["hard_check_pass"] = True

    base_n = glyph_metrics(IBM, 0x1D45B, ROLE_PT)
    base_alpha = glyph_metrics(IBM, 0x1D6FC, ROLE_PT)
    plus = glyph_metrics(LIBERTINUS, 0x002B, ROLE_PT)
    uppercase_n = glyph_metrics(MEZENETS, 0x004E, ROLE_PT)
    base_units = sorted([base_n["height_units"]] * 6 + [plus["height_units"]] * 3 + [uppercase_n["height_units"]])
    base_median = (base_units[4] + base_units[5]) / 2
    base_ratios = {
        "italic_n": base_n["height_units"] / base_median,
        "italic_alpha": base_alpha["height_units"] / base_median,
        "binary_plus": plus["height_units"] / base_median,
        "uppercase_total_N": uppercase_n["height_units"] / base_median,
    }
    base_envelopes = [g["conservative_integer_envelope_px"] for g in (base_n, base_alpha, plus, uppercase_n)]
    base_regression = {
        "status": "STATIC_BASE_ROLE_REGRESSION_PASS_AWAIT_NEW_RASTER",
        "role": "PANEL_MAIN|FORMULA_BLOCK|BASE_MATH",
        "uniform_source_point_size": ROLE_PT,
        "source_max_min_ratio": 1.0,
        "source_span_pt": 0.0,
        "glyphs": {"italic_n": base_n, "italic_alpha": base_alpha, "binary_plus": plus, "uppercase_total_N": uppercase_n},
        "median_height_units": base_median,
        "ratios_to_frozen_role_median": {key: round(value, 12) for key, value in base_ratios.items()},
        "all_contour_ratios_pass": all(0.92 <= value <= 1.08 for value in base_ratios.values()),
        "minimum_conservative_integer_height_px": min(envelope[0] for envelope in base_envelopes),
        "all_conservative_integer_heights_pass_22px": min(envelope[0] for envelope in base_envelopes) >= 22,
        "note": "Codepoints and font faces are unchanged from R19; only the complete source role changes uniformly from 10.7pt to 11.6pt. Native R20 remeasurement remains mandatory.",
    }
    if not base_regression["all_contour_ratios_pass"] or not base_regression["all_conservative_integer_heights_pass_22px"]:
        raise RuntimeError("base role static regression failed")

    stix_i = glyph_metrics(STIX, 0x1D456, 8.08963)
    stix_zero = glyph_metrics(STIX, 0x0030, 8.08963)
    r17_rows = [row for row in read_csv(R19_ROOT.parent / "STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825" / "after_pixel_measurements.csv") if row["TAXONOMY_KEY"] == "PANEL_MAIN|FORMULA_SUBSCRIPT|SUBSCRIPT_MATH"]
    prior_native = [
        {"element_id": row["ELEMENT_ID"], "char": row["CHAR"], "pdf_font_size_pt": float(row["PDF_FONT_SIZE_PT"]), "h_ink_px": int(row["H_INK_PX"]), "group_median_h_px": float(row["GROUP_MEDIAN_H_PX"]), "ratio": float(row["H_TO_MEDIAN_RATIO"]), "decision": row["DECISION"]}
        for row in r17_rows
    ]
    if [row["h_ink_px"] for row in prior_native] != [26, 26, 24] or any(row["decision"] != "PASS" for row in prior_native):
        raise RuntimeError(f"same-project 11.6pt natural-script reference drift: {prior_native}")
    subscript = {
        "status": "STATIC_COMPLETE_SUBSCRIPT_ROLE_PASS_AWAIT_NEW_RASTER",
        "frozen_key": "PANEL_MAIN|FORMULA_SUBSCRIPT|SUBSCRIPT_MATH",
        "complete_semantic_denominator": ["two genuine mathematical italic i subscripts", "one genuine digit 0 subscript"],
        "base_formula_source_point_size": ROLE_PT,
        "natural_tex_script_pdf_point_size_reference": 8.08963,
        "per_glyph_fontsize_override_count": 0,
        "exact_glyph_taxonomy_split_count": 0,
        "font_outline_metrics": {"italic_i": stix_i, "digit_zero": stix_zero},
        "zero_to_i_outline_height_ratio": round(stix_zero["height_units"] / stix_i["height_units"], 12),
        "outline_ratio_gate": [0.92, 1.08],
        "same_project_same_base_size_native_reference": prior_native,
        "same_project_native_reference_ratio_zero_to_median": 24 / 26,
        "same_project_native_reference_pass": 0.92 <= 24 / 26 <= 1.08,
        "note": "This historical same-engine reference supports the static mechanism but is not migrated as the R20 verdict; the next PDF must rebuild all three current IDs and the full denominator.",
    }
    if not 0.92 <= subscript["zero_to_i_outline_height_ratio"] <= 1.08 or not subscript["same_project_native_reference_pass"]:
        raise RuntimeError("subscript role static preflight failed")

    glyph_rows = read_csv(R19_ROOT / "after_pixel_measurements.csv")
    drawing_rows = read_csv(R19_ROOT / "DRAWING_INVENTORY_PREMEASUREMENT.csv")
    pair_rows = read_csv(R19_ROOT / "after_overlap_report.csv")
    glyph_by_id = {row["ELEMENT_ID"]: row for row in glyph_rows}
    risks = []
    for parent, border in (("N_POSTERIOR", "D0004"), ("N_PREDICTIVE", "D0005")):
        boxes = [json.loads(row["BBOX_PDF_PT"]) for row in glyph_rows if row["PARENT"] == parent]
        union = [min(box[0] for box in boxes), min(box[1] for box in boxes), max(box[2] for box in boxes), max(box[3] for box in boxes)]
        border_box = json.loads(next(row["bbox_pdf_pt"] for row in drawing_rows if row["id"] == border))
        current_width = union[2] - union[0]
        current_height = union[3] - union[1]
        factor = 11.6 / 10.7
        projected_width = current_width * factor
        projected_height = current_height * factor
        relevant = []
        for row in pair_rows:
            other = None
            if row["A_ID"] == border and row["B_ID"] in glyph_by_id and glyph_by_id[row["B_ID"]]["PARENT"] == parent:
                other = row["B_ID"]
            elif row["B_ID"] == border and row["A_ID"] in glyph_by_id and glyph_by_id[row["A_ID"]]["PARENT"] == parent:
                other = row["A_ID"]
            if other:
                relevant.append(float(row["MIN_CLEARANCE_PX"]))
        current_min = min(relevant)
        horizontal_loss_px = (projected_width - current_width) / 2 * SCALE_300
        vertical_loss_px = (projected_height - current_height) / 2 * SCALE_300
        projected_lower_bound = current_min - max(horizontal_loss_px, vertical_loss_px)
        risks.append({
            "parent": parent,
            "border": border,
            "current_all_glyph_union_pdf_pt": union,
            "border_bbox_pdf_pt": border_box,
            "current_union_width_pt": round(current_width, 9),
            "projected_conservative_all_glyph_width_pt": round(projected_width, 9),
            "border_width_pt": round(border_box[2] - border_box[0], 9),
            "projected_centered_horizontal_margin_px": round(((border_box[2] - border_box[0]) - projected_width) / 2 * SCALE_300, 6),
            "current_min_glyph_to_own_border_clearance_px": current_min,
            "projected_clearance_lower_bound_px": round(projected_lower_bound, 6),
            "hard_gate_px": 5,
            "static_risk_pass": projected_lower_bound >= 5 and projected_width < border_box[2] - border_box[0] and projected_height < border_box[3] - border_box[1],
        })
    layout = {
        "status": "STATIC_LAYOUT_RISK_PASS_AWAIT_NEW_RASTER",
        "uniform_size_factor": 11.6 / 10.7,
        "node_risks": risks,
        "application_to_lda_clearance_r19_px": [19.0, 19.0],
        "application_label_or_lda_geometry_changed_in_r4": False,
        "node_coordinate_changes_in_r4": 0,
        "relationship_changes_in_r4": 0,
        "all_static_risk_pass": all(item["static_risk_pass"] for item in risks),
        "note": "The projection pessimistically scales every glyph in each node, including labels that R4 does not enlarge. Native geometry and all 6441 pairs still require a new PDF.",
    }
    if not layout["all_static_risk_pass"]:
        raise RuntimeError("layout static risk failed")

    snapshot = ROOT / "SOURCE_R4_SNAPSHOT.tex"
    snapshot.write_bytes(source_bytes)
    if sha256(snapshot) != after_sha:
        raise RuntimeError("R4 snapshot mismatch")
    identity = {
        "round": "STRICT_R20_SA2_SOURCE_R4_STATIC_ONLY_20260825",
        "source": str(SOURCE),
        "before_snapshot": str(BEFORE_SNAPSHOT),
        "before_r4_sha256": BEFORE_R4_SHA,
        "after_r4_sha256": after_sha,
        "after_r4_bytes": SOURCE.stat().st_size,
        "snapshot_sha256": sha256(snapshot),
        "snapshot_bytes": snapshot.stat().st_size,
        "snapshot_byte_identical_to_source": True,
        "git_head": run("git", "-C", str(WORKTREE), "rev-parse", "HEAD").stdout.strip(),
        "modified_business_source_count": 1,
        "font_files": [
            {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in (IBM, LIBERTINUS, MEZENETS, STIX)
        ],
        "tex_invocations": 0,
        "commit_created": False,
    }

    report = f"""# P654 SOURCE R4 static-only preflight

Status: `P654_SOURCE_R4_STATIC_READY_REQUEST_BUILD_SLOT`.

Only `{SOURCE}` is modified. The exact R4 before SHA-256 is `{BEFORE_R4_SHA}` and the after SHA-256 is `{after_sha}`. The R4 delta has exactly seven changed lines: one comment, three direct-font declarations and three formula wrappers. All direct fonts and wrappers change uniformly from 10.7pt to 11.6pt; no codepoint, font face, formula token, node, coordinate or relation changes.

The complete natural subscript role remains one frozen key with two mathematical italic i glyphs and one digit 0. There is no per-glyph size override or exact-glyph taxonomy split. STIX outline heights are 674 and 653 units, ratio {subscript['zero_to_i_outline_height_ratio']:.12f}. The same-project 11.6pt natural-script reference is 26/26/24px, so 24/26={24/26:.12f} passes the unchanged [0.92,1.08] gate. This is only a static mechanism proof; the next candidate must independently remeasure the current three glyphs.

The already-passing base formula objects remain genuine IBM mathematical n/alpha, Libertinus U+002B mathbin plus and Mezenets uppercase U+004E mathord N. Their 11.6pt contour ratios remain within [0.92,1.08], and their conservative native-height lower envelope remains at least {base_regression['minimum_conservative_integer_height_px']}px. U+0274, n_0, text plus, resize/scalebox and transform remain absent.

The width/clearance projection pessimistically scales every glyph in the posterior and predictive nodes. Projected all-glyph widths are {risks[0]['projected_conservative_all_glyph_width_pt']:.6f}pt inside {risks[0]['border_width_pt']:.6f}pt and {risks[1]['projected_conservative_all_glyph_width_pt']:.6f}pt inside {risks[1]['border_width_pt']:.6f}pt. Projected own-border clearance lower bounds remain {risks[0]['projected_clearance_lower_bound_px']:.6f}px and {risks[1]['projected_clearance_lower_bound_px']:.6f}px versus the 5px gate. The application label, LDA node and their R19 19px/19px clearances are untouched.

No TeX, commit, fresh role or manual field was created. A new native-300dpi full denominator, all unordered pairs/critical, 1x/8x and genuinely observed manual evidence remain mandatory after an explicit build grant.
"""

    (ROOT / "SOURCE_R4.diff").write_text(exact_diff.stdout, encoding="utf-8")
    write_json("SOURCE_IDENTITY.json", identity)
    write_json("SUBSCRIPT_ROLE_PREFLIGHT.json", subscript)
    write_json("BASE_ROLE_REGRESSION_PREFLIGHT.json", base_regression)
    write_json("LAYOUT_RISK_PREFLIGHT.json", layout)
    write_json("STATIC_CHECKS.json", checks)
    (ROOT / "P654_SOURCE_R4_STATIC_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "status": checks["status"],
        "before_sha256": BEFORE_R4_SHA,
        "after_sha256": after_sha,
        "bytes": SOURCE.stat().st_size,
        "exact_changed_lines": len(changes),
        "subscript_outline_ratio_zero_to_i": subscript["zero_to_i_outline_height_ratio"],
        "same_project_11_6_native_ratio": subscript["same_project_native_reference_ratio_zero_to_median"],
        "projected_clearance_lower_bounds_px": [item["projected_clearance_lower_bound_px"] for item in risks],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
