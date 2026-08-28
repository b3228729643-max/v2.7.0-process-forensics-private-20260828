# FIG-P639-01 R104 SA3 visual acceptance

RESULT: FAIL
FIGURE_ID: FIG-P639-01
HANDOFF_ID: C-FIG-P639-01-R104-SA3-FRESH-ISOLATED-V1
REVIEWER_TYPE: AI_SA3_VISUAL_REVIEW
HUMAN_CERTIFICATION: false
SA3_MODEL: gpt-5.6-sol
SA3_REASONING: xhigh

SOURCE_FONT_PASS: true
PIXEL_HEIGHT_PASS: true
SAME_CLASS_RATIO_PASS: true
ROLE_RATIO_PASS: true
OVERLAP_CANDIDATE_PIXEL_COUNT: 0
MASK_CONTAMINATION_PIXEL_COUNT: 0
OVERLAP_PIXEL_COUNT: 0
PIXEL_ADJUDICATION_STATUS: CLEAR
PIXEL_ARBITER_MODEL: NOT_USED
PIXEL_ARBITER_REASONING: NOT_USED
CLIP_PIXEL_COUNT: 0
MIN_TEXT_CLEARANCE_PX: 12
VISUAL_HARMONY_PASS: true
MATH_SEMANTICS_PASS: true
TEXT_CONSISTENCY_PASS: true
GRAYSCALE_PASS: true
PAGE_INTEGRATION_PASS: false

INDEPENDENT_FINDINGS: The figure's formulas, object positions, two conditional densities, mean guides, note, caption, typography, native pixel heights, grayscale distinction, actual-object clearances, and clipping all pass the R168 hard gates. Source font values 8.5/9.2 pt, small peer-role deviations, and caption line-content height variation are recorded only as advisory because the actual glyphs are readable and balanced.

SOURCE_FONT_AUDIT: 20/20 reader-visible text IDs manually reviewed; no missing glyph, tofu, wrong codepoint, unreadable element, or obvious severe size imbalance.
PIXEL_HEIGHT_AUDIT: minimum natural-script glyph height 19 px; digit ticks 25–26 px; lower-case math t 26 px; CJK cross-baseline height at least 34 px; base formula labels 39 px.
SAME_CLASS_RATIO_AUDIT: curve-label bases 1.000; natural subscripts 1.000; x ticks 1.000–1.040; y ticks 1.000; note lines 1.000. Caption line ink 38/42 is content-driven advisory under R168.
ROLE_RATIO_AUDIT: no visually severe hierarchy inversion; role-to-digit ratios are script/taxonomy-sensitive and advisory under R168.
VISUAL_HARMONY: Figure-local hierarchy is stable; data curves dominate and direct labels/notes do not cover data.
NEW_REGRESSIONS: The R104 page places FIG-P639-01 inside the next figure's sentence, leaving `下的混合速度。` isolated below the caption and a large blank lower page.
BLOCKERS: PAGE_INTEGRATION and READING_ORDER hard failure on physical page 689.
REQUIRED_FIXES: SA2 must repair source-local float containment/placement so the figure-33.7 sentence stays contiguous, rebuild the official candidate, and regenerate all measurements and views.

EVIDENCE_USED: page_689_native_300dpi.png; full_page_200dpi.png; figure_crop_native_300dpi.png; standalone_equivalent_native_300dpi.png; grayscale_300dpi.png; page_context_native_300dpi.png; measurement_overlay_native_300dpi.png; semantic_object_masks_300dpi.png; critical_glyph_object_contact_1x.png; critical_glyph_object_contact_8x.png; pixel_inventory.csv; glyph_component_inventory.csv; peer_role_measurements.csv; unordered_pair_measurements.csv; critical_pair_measurements.csv; clip_measurements.csv; manual_element_font_glyph_review.csv; manual_object_geometry_review.csv; after_overlap_adjudication.md; manual_semantics_page_review.md.

DISPOSITION: RETURN_TO_SA2
GLOBAL_OR_FINAL_CLAIM: false
C_LOCAL_PASS_ONLY: false

