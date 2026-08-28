"""Write the R5 SA1 terminal package exactly once after a passing integrity gate.

WRITE_STOPPED is intentionally the final filesystem write in this script.  Do not
run this script unless the preterminal check is PASS and no terminal marker exists.
"""

from __future__ import annotations

import json
from pathlib import Path


R5 = Path(__file__).resolve().parents[1]
REPORTS = R5 / "reports"
STOP = R5 / "WRITE_STOPPED"

if STOP.exists():
    raise SystemExit("WRITE_STOPPED already exists; terminal package is immutable")

preterminal = json.loads((REPORTS / "preterminal_integrity_check.json").read_text(encoding="utf-8"))
if preterminal.get("all_pass") is not True:
    raise SystemExit("preterminal integrity check is not PASS; terminalization refused")

source_sha = preterminal["source_sha256"]
pdf_sha = preterminal["pdf_sha256"]

visual = f"""# FIG-P580-01 R5 SA1 visual acceptance — closed

SOURCE_FONT_PASS = true
PIXEL_HEIGHT_PASS = true
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = true
LOW_PROFILE_CALIBRATION_PASS = true
GLYPH_ENUMERATION_BOUNDARY_PASS = true
GRAPHIC_ENUMERATION_BOUNDARY_PASS = true
ILLEGAL_OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_INDEPENDENT_TT_CLEARANCE_PX = 11.1803
MIN_INDEPENDENT_TG_CLEARANCE_PX = 11.1803
FONT_VISUAL_HARMONY_PASS = true
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

Manual closure: 235/235 glyph three-view cells across 30/30 contact sheets; 212/212 critical relations (TT=152, TG=1, GG=59); full page, crop, standalone, and grayscale views manually reviewed.

The generic same-parent raw separation floor is 1 native pixel only because explicitly allocated components (including the combining-overlay case) are not independent text objects.  The independent native clearances above are the applicable non-contact figures.  The 48 retained raw graphic contacts are all individually named source-intent contacts; they are not illegal overlaps.

RESULT = PASS_TO_SA3
"""

decision = f"""# FIG-P580-01 — R5 SA1 terminal decision

**RESULT = PASS_TO_SA3**

## Frozen identity

- Authority PDF: `D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\build\\strict_current_r96_fullbook\\main_full.pdf`
- Physical page / printed page / figure: `628 / 615 / 31.6`
- PDF SHA-256: `{pdf_sha}`
- FLS-located frozen source: `D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\绘图源码\\第05册_采样方法主题模型与图排序\\V5-C02\\fig_v5_c02_is_support.tex`
- Source SHA-256: `{source_sha}`

## Strict-gate closure

- Native final-PDF 300 dpi direct page/crop evidence; 8x-nearest used only for visual inspection.
- Glyph boundary: 235/235 final-PDF glyphs, no body-text entry and no missing in-scope glyph; graphic boundary: 25/25 foreground graphic objects.
- Manual glyph evidence: 30/30 contact sheets and 235/235 Original / Target-overlay / Mask-only cells PASS; low-profile `G0199` eight exact controls PASS.
- Pair universe: all `C(260,2)=33,670` unordered pairs, including `C(25,2)=300` GG pairs, evaluated at native 1x; illegal overlap `0` px / `0` pairs, clipping `0` px, clearance failures `0`.
- Critical-relation manual ledger: 212/212 PASS (`TT=152`, `TG=1`, `GG=59`); the 60 non-TT relations were directly viewed at 8x with native relation evidence, while all TT constituents are closed in the glyph three-view ledger.
- Exact relation classification for the 48 prior raw-overlap candidates: same-parent `0`; named source-intent GG contact `48`; mask artifact `0`; true illegal `0`.  Four separate same-parent glyph ownership allocations are recorded in `reports/same_parent_mask_allocation.csv`; the U+0338/U+226A composite is separately attributed and has no residual raw overlap.
- Font/size D gate: all 235 rows PASS.  There are no final role-ratio failures.  The only low raw-ink diagnostic candidates, `G0085`--`G0088` (`支持不足`, `PANEL_TITLE`), use the source/effective role ratio `10.2/9.6=1.0625`, within required `[1.05,1.20]`; their `1.035` ink diagnostic is not the role-size decision metric.
- D/E semantic, mathematical, font-coordination, full-page, crop, standalone, and grayscale review PASS.  Source/PDF agree on the support gap for `q_L`, support coverage by `q_R`, and weights `24/25, 3/2, 24/25`.
- The 32 abandoned color-projection assertions are `ABORTED_NON_DECISIONAL`, excluded from every R5 numerator, denominator, pair classification, and conclusion.

The evidence package passed `reports/preterminal_integrity_check.json` before this decision.  This terminal conclusion authorizes SA3 review only; it is not a source modification or a build approval.
"""

manifest = {
    "figure_id": "FIG-P580-01",
    "review": "STRICT_R5_SA1_CONT_R96_20260824",
    "terminal_state": "PASS_TO_SA3",
    "decision_date": "2026-08-24",
    "canonical_work_root": r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work",
    "authority": {
        "pdf": r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r96_fullbook\main_full.pdf",
        "pdf_sha256": pdf_sha,
        "source": r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex",
        "source_sha256": source_sha,
        "physical_page": 628,
        "printed_page": 615,
        "figure": "31.6",
    },
    "manual_closure": {
        "glyph_tri_view": {"passed": 235, "total": 235, "contact_sheets": {"passed": 30, "total": 30}},
        "low_profile_controls": {"passed": 8, "total": 8, "glyph": "G0199"},
        "critical_relations": {"passed": 212, "total": 212, "classes": {"TT": 152, "TG": 1, "GG": 59}, "direct_8x_non_tt": 60},
        "four_view_math_font_coordination": "PASS",
    },
    "pair_universe": {
        "foreground_objects": 260,
        "all_unordered_pairs": 33670,
        "gg_pairs": 300,
        "illegal_overlap_pairs": 0,
        "illegal_overlap_pixels": 0,
        "clip_pixels": 0,
        "clearance_failure_pairs": 0,
        "raw_overlap_candidate_classification": {"same_parent": 0, "named_source_intent": 48, "mask_artifact": 0, "true_illegal": 0},
        "separate_same_parent_allocations": 4,
        "independent_min_clearance_px": {"TT": 11.1803, "TG": 11.1803},
    },
    "font_role": {
        "all_235_rows_pass": True,
        "final_role_ratio_failures": [],
        "title_to_base_effective_ratio": 1.0625,
        "required_cjk_title_base_interval": [1.05, 1.20],
    },
    "excluded_non_decisional_legacy_color_projection_assertions": 32,
    "preterminal_integrity": "reports/preterminal_integrity_check.json",
    "terminal_report": "reports/SA1_FINAL_DECISION.md",
    "stop_marker": "WRITE_STOPPED",
}

# These are the final evidence writes before the immutable stop marker.
(R5 / "after_visual_acceptance.md").write_text(visual, encoding="utf-8")
(REPORTS / "SA1_FINAL_DECISION.md").write_text(decision, encoding="utf-8")
(R5 / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Must remain the final R5 write.  Do not modify the package after this marker.
STOP.write_text("WRITE_STOPPED\nterminal_state=PASS_TO_SA3\nreview=STRICT_R5_SA1_CONT_R96_20260824\n", encoding="utf-8")
print(json.dumps({"terminal_state": "PASS_TO_SA3", "write_stopped": str(STOP)}, ensure_ascii=False))
