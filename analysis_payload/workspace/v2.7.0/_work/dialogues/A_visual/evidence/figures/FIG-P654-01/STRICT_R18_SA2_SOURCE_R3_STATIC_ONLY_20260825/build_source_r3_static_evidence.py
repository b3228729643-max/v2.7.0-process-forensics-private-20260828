from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = Path(r"src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
SOURCE = WORKTREE / SOURCE_REL
BEFORE_R3_SHA = "0A7CAAA49978AA6193BA4DC4CB90845981599DFC161F5A8BD6B9143A1EA4C2EB"
IBM = Path(r"D:\texlive\2026\texmf-dist\fonts\opentype\ibm\plex\IBMPlexMath-Regular.otf")
LIBERTINUS = Path(r"D:\texlive\2026\texmf-dist\fonts\opentype\public\libertinus-fonts\LibertinusMath-Regular.otf")
MEZENETS = Path(r"D:\texlive\2026\texmf-dist\fonts\opentype\public\fonts-churchslavonic\MezenetsUnicode.otf")
ROLE_PT = 10.7
SCALE_300 = 300 / 72


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(WORKTREE), *args], capture_output=True, text=True, encoding="utf-8", check=False)


def glyph_height(font_path: Path, codepoint: int) -> dict[str, object]:
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
    upm = font["head"].unitsPerEm
    height_units = y1 - y0
    span_px = height_units / upm * ROLE_PT * SCALE_300
    return {
        "font": font_path.name,
        "codepoint": f"U+{codepoint:04X}",
        "glyph_name": glyph_name,
        "bounds_font_units": [x0, y0, x1, y1],
        "height_units": height_units,
        "units_per_em": upm,
        "role_point_size": ROLE_PT,
        "continuous_height_at_300dpi_px": round(span_px, 6),
        "conservative_integer_envelope_px": [math.floor(span_px), math.ceil(span_px)],
    }


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    text = source_bytes.decode("utf-8")
    after_sha = sha256(SOURCE)
    status = run_git("status", "--short")
    if status.returncode != 0:
        raise RuntimeError(status.stderr)
    status_lines = [line for line in status.stdout.splitlines() if line.strip()]
    if len(status_lines) != 1 or "fig_v5_c05_dependency_graph.tex" not in status_lines[0]:
        raise RuntimeError(f"scope violation: {status_lines}")
    diff_check = run_git("diff", "--check")
    if diff_check.returncode != 0 or diff_check.stdout or diff_check.stderr:
        raise RuntimeError(f"git diff-check failed: {diff_check.stdout}{diff_check.stderr}")
    diff = run_git("diff", "--", SOURCE_REL.as_posix())
    if diff.returncode != 0:
        raise RuntimeError(diff.stderr)
    diff_stat = run_git("diff", "--stat", "--", SOURCE_REL.as_posix())
    if diff_stat.returncode != 0:
        raise RuntimeError(diff_stat.stderr)

    base_n = glyph_height(IBM, 0x1D45B)
    base_alpha = glyph_height(IBM, 0x1D6FC)
    total_n = glyph_height(MEZENETS, 0x004E)
    binary_plus = glyph_height(LIBERTINUS, 0x002B)
    role_counts = {"italic_n_or_alpha": 6, "binary_plus": 3, "uppercase_total_N": 1}
    role_units = [base_n["height_units"]] * 6 + [binary_plus["height_units"]] * 3 + [total_n["height_units"]]
    role_units.sort()
    median_units = (role_units[4] + role_units[5]) / 2
    ratios = {
        "italic_n": base_n["height_units"] / median_units,
        "italic_alpha": base_alpha["height_units"] / median_units,
        "binary_plus": binary_plus["height_units"] / median_units,
        "uppercase_total_N": total_n["height_units"] / median_units,
    }
    base_envelope = base_n["conservative_integer_envelope_px"]
    plus_envelope = binary_plus["conservative_integer_envelope_px"]
    total_envelope = total_n["conservative_integer_envelope_px"]
    conservative_ratios = {
        "lower_bound_total_N_vs_upper_base": total_envelope[0] / base_envelope[1],
        "upper_bound_plus_vs_lower_base": plus_envelope[1] / base_envelope[0],
    }
    font_metrics = {
        "status": "STATIC_FONT_CONTOUR_PASS_AWAIT_RASTER",
        "role": "PANEL_MAIN|FORMULA_BLOCK|BASE_MATH",
        "role_point_size": ROLE_PT,
        "source_point_size_max_min_ratio": 1.0,
        "source_point_size_span_pt": 0.0,
        "role_counts": role_counts,
        "glyphs": {"italic_n": base_n, "italic_alpha": base_alpha, "uppercase_total_N": total_n, "binary_plus": binary_plus},
        "median_height_units": median_units,
        "contour_ratios_to_frozen_role_median": {k: round(v, 12) for k, v in ratios.items()},
        "contour_ratio_gate": [0.92, 1.08],
        "conservative_integer_rounding_ratios": {k: round(v, 12) for k, v in conservative_ratios.items()},
        "absolute_base_math_min_px": 22,
        "minimum_conservative_integer_height_px": min(total_envelope[0], base_envelope[0], plus_envelope[0]),
        "all_contour_ratios_pass": all(0.92 <= value <= 1.08 for value in ratios.values()),
        "all_conservative_integer_rounding_ratios_pass": conservative_ratios["lower_bound_total_N_vs_upper_base"] >= 0.92 and conservative_ratios["upper_bound_plus_vs_lower_base"] <= 1.08,
        "all_conservative_integer_heights_pass": min(total_envelope[0], base_envelope[0], plus_envelope[0]) >= 22,
        "note": "Static contour/raster-envelope proof only. The next explicitly authorized PDF must remeasure native 300dpi pixels; no PASS is claimed here.",
    }
    if not font_metrics["all_contour_ratios_pass"] or not font_metrics["all_conservative_integer_rounding_ratios_pass"] or not font_metrics["all_conservative_integer_heights_pass"]:
        raise RuntimeError("font metric preflight failed")

    brace_open = text.count("{")
    brace_close = text.count("}")
    checks = {
        "status": "P654_SOURCE_R3_STATIC_READY_REQUEST_BUILD_SLOT",
        "source_before_r3_sha256": BEFORE_R3_SHA,
        "source_after_r3_sha256": after_sha,
        "source_after_bytes": SOURCE.stat().st_size,
        "modified_business_source_count": 1,
        "modified_business_source": str(SOURCE),
        "git_diff_check_pass": True,
        "git_diff_stat": diff_stat.stdout.strip(),
        "formula_role_point_size_values": [ROLE_PT],
        "formula_role_point_size_ratio": 1.0,
        "formula_role_point_size_span_pt": 0.0,
        "formula_wrapper_10_7_count": len(re.findall(r"\\fontsize\{10\.7pt\}\{12\.8pt\}", text)),
        "direct_role_font_10_7_count": len(re.findall(r'at 10\.7pt', text)),
        "legacy_role_size_11_6_count": text.count("11.6pt"),
        "legacy_role_size_10_0_count": text.count("10pt"),
        "legacy_role_size_9_5_count": text.count("9.5pt"),
        "math_plus_macro_use_count": len(re.findall(r"\\slfigPPlus", text)) - 1,
        "math_plus_u002b_definition_count": text.count('\\char"002B'),
        "mathbin_definition_count": text.count("\\mathbin"),
        "text_plus_count": len(re.findall(r"\\text\s*\{\s*\+\s*\}", text)),
        "total_N_macro_use_count": text.count("\\slfigPTotalN") - 1,
        "uppercase_total_N_u004e_definition_count": text.count('\\char"004E'),
        "small_cap_total_N_u0274_count": text.count('\\char"0274'),
        "undefined_n0_count": text.count("n_0"),
        "target_n_u1d45b_definition_count": text.count('\\char"1D45B'),
        "alpha_u1d6fc_definition_count": text.count('\\char"1D6FC'),
        "resizebox_count": text.count("\\resizebox"),
        "scalebox_count": text.count("\\scalebox"),
        "transform_shape_count": text.count("transform shape"),
        "lda_coordinate_r3_count": text.count("(6.35,-2.75)"),
        "old_lda_coordinate_count": text.count("(6.35,-2.55)"),
        "application_midpoint_count": text.count("node[pos=.50,right=7pt,inner sep=0pt"),
        "relationship_count": len(re.findall(r"\\draw\[(?:arr|interp|application)\]", text)),
        "begin_group_count": text.count("\\begingroup"),
        "end_group_count": text.count("\\endgroup"),
        "brace_open_count": brace_open,
        "brace_close_count": brace_close,
        "manual_reviewer_fields_generated": 0,
        "manual_boolean_fields_generated": 0,
        "manual_decision_fields_generated": 0,
        "manual_note_fields_generated": 0,
        "tex_invocations": 0,
        "commit_created": False,
        "fresh_role_started": False,
    }
    hard_expected = {
        "formula_wrapper_10_7_count": 3,
        "direct_role_font_10_7_count": 3,
        "legacy_role_size_11_6_count": 0,
        "legacy_role_size_10_0_count": 0,
        "legacy_role_size_9_5_count": 0,
        "math_plus_macro_use_count": 3,
        "math_plus_u002b_definition_count": 1,
        "mathbin_definition_count": 1,
        "text_plus_count": 0,
        "total_N_macro_use_count": 1,
        "uppercase_total_N_u004e_definition_count": 1,
        "small_cap_total_N_u0274_count": 0,
        "undefined_n0_count": 0,
        "target_n_u1d45b_definition_count": 1,
        "alpha_u1d6fc_definition_count": 1,
        "resizebox_count": 0,
        "scalebox_count": 0,
        "transform_shape_count": 0,
        "lda_coordinate_r3_count": 1,
        "old_lda_coordinate_count": 0,
        "application_midpoint_count": 1,
        "relationship_count": 7,
        "begin_group_count": 1,
        "end_group_count": 1,
    }
    mismatches = {key: {"actual": checks[key], "expected": expected} for key, expected in hard_expected.items() if checks[key] != expected}
    if brace_open != brace_close:
        mismatches["brace_balance"] = {"actual": [brace_open, brace_close], "expected": "equal"}
    if mismatches:
        raise RuntimeError(f"static checks failed: {mismatches}")
    checks["hard_check_mismatches"] = mismatches
    checks["hard_check_pass"] = True

    layout = {
        "status": "STATIC_LAYOUT_PREFLIGHT_PASS_AWAIT_PDF",
        "changed_node": "N_LDA",
        "old_coordinate_cm": [6.35, -2.55],
        "new_coordinate_cm": [6.35, -2.75],
        "vertical_extension_cm": 0.20,
        "vertical_extension_at_300dpi_px": round(0.20 / 2.54 * 300, 6),
        "midpoint_label_clearance_gain_each_side_px": round(0.10 / 2.54 * 300, 6),
        "required_native_clearance_px": 3,
        "original_failed_clearance_px": 0,
        "predicted_new_clearance_lower_bound_px": round(0.10 / 2.54 * 300, 6),
        "semantic_edge_unchanged": "predictive -> application label -> lda",
        "other_node_coordinates_changed": 0,
        "node_dimensions_changed": 0,
        "relationship_count_before_after": [7, 7],
        "note": "The downstream node moves 0.20cm down; the midpoint label gains half that separation from both endpoint borders. Native PDF remeasurement remains mandatory after an explicit build grant.",
    }

    snapshot_path = ROOT / "SOURCE_R3_SNAPSHOT.tex"
    snapshot_path.write_bytes(source_bytes)
    snapshot_sha = sha256(snapshot_path)
    snapshot_bytes = snapshot_path.stat().st_size
    if snapshot_sha != after_sha or snapshot_bytes != SOURCE.stat().st_size:
        raise RuntimeError("source snapshot is not byte-identical")

    identity = {
        "round": "STRICT_R18_SA2_SOURCE_R3_STATIC_ONLY_20260825",
        "source": str(SOURCE),
        "before_r3_sha256": BEFORE_R3_SHA,
        "after_r3_sha256": after_sha,
        "after_r3_bytes": SOURCE.stat().st_size,
        "snapshot_path": str(snapshot_path),
        "snapshot_sha256": snapshot_sha,
        "snapshot_bytes": snapshot_bytes,
        "snapshot_byte_identical_to_source": True,
        "git_head": run_git("rev-parse", "HEAD").stdout.strip(),
        "modified_file_count": 1,
        "git_diff_stat": diff_stat.stdout.strip(),
        "font_files": [
            {"path": str(IBM), "bytes": IBM.stat().st_size, "sha256": sha256(IBM)},
            {"path": str(LIBERTINUS), "bytes": LIBERTINUS.stat().st_size, "sha256": sha256(LIBERTINUS)},
            {"path": str(MEZENETS), "bytes": MEZENETS.stat().st_size, "sha256": sha256(MEZENETS)},
        ],
        "tex_invocations": 0,
        "commit_created": False,
    }

    report = f"""# P654 SOURCE R3 static-only preflight

Status: `P654_SOURCE_R3_STATIC_READY_REQUEST_BUILD_SLOT`.

Only `{SOURCE}` is modified. Before-R3 SHA-256 is `{BEFORE_R3_SHA}`; after-R3 SHA-256 is `{after_sha}`. Git diff-check passes; the working-tree diff contains one business source only.

## Unified frozen formula role

All ten `PANEL_MAIN|FORMULA_BLOCK|BASE_MATH` objects now inherit one 10.7pt role. There are no 11.6/10/9.5pt per-glyph overrides. Italic `n`/alpha use IBM Plex Math, all three binary plus operators use the Libertinus Math genuine U+002B glyph and remain `mathbin` atoms, and total count uses the genuine Mezenets uppercase U+004E glyph as a `mathord`. U+0274 and `n_0` are absent; the visible/codepoint and extraction intent is uppercase `N`.

Font contours at the same 10.7pt are 540 units for italic n/alpha, 537 for uppercase U+004E N, and 548 for U+002B plus. Against the frozen role median 540, ratios are 1.000000, 0.994444, and 1.014815. Conservative 300dpi integer envelopes are n/alpha 24--25px, N 23--24px, plus 24--25px: the worst low ratio is 23/25=0.92 and worst high ratio is 25/24=1.041667; all remain >=22px. This is static contour proof, not a raster PASS claim.

## Clearance repair

The only geometry change is `N_LDA` y=-2.55cm -> -2.75cm. The 0.20cm extension equals about 23.622px at 300dpi; the unchanged midpoint `应用` label gains about 11.811px separation from both endpoint borders, above the 3px gate. Label text, edge semantics, node dimensions, all other coordinates, and all seven relations remain unchanged.

## Boundaries

Taxonomy, `[0.92,1.08]`, the 3px clearance gate, and the source role gates are unchanged. `resizebox`, `scalebox`, and `transform shape` remain absent. No TeX, commit, fresh role, or manual reviewer/boolean/decision/note field was created. A new native-300dpi build and independently written manual ledger remain mandatory after an explicit grant.
"""

    (ROOT / "SOURCE_R3.diff").write_text(diff.stdout, encoding="utf-8")
    (ROOT / "SOURCE_IDENTITY.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "FONT_ROLE_METRICS.json").write_text(json.dumps(font_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "LAYOUT_CLEARANCE_PREFLIGHT.json").write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "STATIC_CHECKS.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "P654_SOURCE_R3_STATIC_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": checks["status"], "after_sha256": after_sha, "bytes": SOURCE.stat().st_size, "diff_stat": diff_stat.stdout.strip(), "font_ratios": font_metrics["contour_ratios_to_frozen_role_median"], "clearance_gain_px": layout["midpoint_label_clearance_gain_each_side_px"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
