# FIG-P608-01 — fresh isolated SA1 R99 R5A metadata reseal

HANDOFF_ID: `A-R99-P608-SA1-FRESH-R5A-METADATA-RESEAL-20260824`  
ORIGIN_HANDOFF_ID: `A-R99-P608-SA1-FRESH-20260824`  
ACTUAL_ROOT_ORCHESTRATION_ROUTE: `SA1=gpt-5.6-terra/max`  
RESULT: `FAIL_TO_SA2`  
STRICT_LATEST: `true` (relative to R5/R5A only)

This is a packaging-only reseal. It does not rerender the official R99 PDF, rerun
the audit, alter an object/pair count, alter any evidence bytes, or alter the
`FAIL_TO_SA2` decision. It is not a root acceptance and does not assert a
final-book PASS.

## R5 quarantine

R5 is not used as a strict seal because its `WRITE_STOPPED` LastWriteTimeUtc was
exactly tied with its terminal, manifest, report, and result files. The defect is
timestamp ordering only; it does not convert any transient extractor condition
into a design failure. R5A byte-copies and hashes every non-replaced bottom
evidence file, then writes a new sentinel after all other R5A files.

- Reused evidence files: 794; byte mismatches: 0; reused bytes: 12216514.
- The per-file source/destination checksum ledger is `reused_evidence_integrity.csv`.
- The only retained design failures remain `GLYPH_0025` and `GLYPH_0056`, natural-script `t`, each `H=10px < 15px`.

## Preserved R5 audit payload

## Candidate and four native views

- Official R99 PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf`
- SHA-256: `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`; bytes: `4940207`
- Physical PDF page: 660; printed page: 647
- Page grid at 300 dpi: [2481, 3508]; figure crop integer box: [291, 916, 2250, 1876]; crop grid: [1959, 960]
- Views opened: full page 200 dpi, colour crop 300 dpi, direct clipped standalone 300 dpi, grayscale 300 dpi, and protanopia/deuteranopia/tritanopia simulations.

## Terminal bottom-up recalculation

- Visible foreground object universe N = 170; full unordered denominator C(N,2) = 14365; emitted pair rows = 14365.
- Rawdict glyphs = 112; TextTrace z-order matches = 112.
- Pre-occlusion candidate pixel-pair sum = 99; confirmed illegal final-visible overlap pixels = 0; clip pixels = 0.
- Critical pair ROIs reviewed at native1x and nearest8x = 13; every object reviewed at native1x and nearest8x = 170.

## Gate matrix

| Gate | Verdict |
|---|---|
| candidate_identity_locked | PASS |
| rawdict_to_texttrace_closed | PASS |
| preliminary_machine_counts_recomputed | PASS |
| unique_object_ids | PASS |
| all_object_files_exist | PASS |
| all_masks_nonempty | PASS |
| character_mapping_closed | PASS |
| all_foreground_paths_accounted | PASS |
| math_rules_accounted | PASS |
| pair_universe_complete | PASS |
| all_pairs_pass | PASS |
| zero_final_overlap | PASS |
| zero_clip | PASS |
| text_crop_edge_clearance | PASS |
| source_font_pass | PASS |
| source_font_control_coverage | PASS |
| source_scale_control_pass | PASS |
| pixel_height_pass | FAIL |
| punctuation_calibrated | PASS |
| calibration_artifacts_exist | PASS |
| same_class_d_ratio_pass | PASS |
| role_e_ratio_pass | PASS |
| semantic_consistency_pass | PASS |
| four_required_views_exist | PASS |
| text_measurement_overlay_exists | PASS |
| three_colour_vision_views_exist | PASS |
| contact_coverage_closed | PASS |
| manual_object_review_closed | PASS |
| manual_mask_integrity | PASS |
| critical_pair_review_closed | PASS |
| four_view_manual_pass | PASS |
| three_colour_vision_manual_pass | PASS |
| role_panel_manual_pass | PASS |

## Strict review conclusions

- SOURCE_FONT_PASS = true
- PIXEL_HEIGHT_PASS = false
- SAME_CLASS_RATIO_PASS = true
- ROLE_RATIO_PASS = true
- PRE_OCCLUSION_CANDIDATE_PIXEL_PAIR_SUM = 99
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = HARD_FAIL_IDENTIFIED
- PIXEL_ARBITER_MODEL = NOT_USED
- PIXEL_ARBITER_REASONING = NOT_USED
- CLIP_PIXEL_COUNT = 0
- MIN_REQUIRED_CLASS_CLEARANCE_PX = 13.0
- FONT_VISUAL_HARMONY_PASS = true
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- THREE_COLOUR_VISION_PASS = true
- PAGE_INTEGRATION_PASS = true

## Design failures (terminal)

- [GLYPH_0025] (TOP_YLABEL, 𝑡): H=10px < 15px; H_INK_PX 10 < 15
- [GLYPH_0056] (BOTTOM_YLABEL, 𝑡): H=10px < 15px; H_INK_PX 10 < 15

## Extractor correction history (not a design failure)

- A transient first-pass CJK rawdict/TextTrace join did not handle CID encoding and therefore produced empty masks. The terminal package uses an exact-or-unique font/x-extent PDF-sequence join: 112/112 glyphs are mapped.
- A transient broad paint-colour mask admitted low-opacity gray pixels into the blue curve bbox. The terminal package uses the white-to-paint compositing ray with residual separation; the full 14,365-pair terminal table has no pair failure.
- A transient horizontal punctuation reference was unsuitable for the rotated ylabel matrix. The terminal punctuation ledger now carries a same-font, same-size, same-colour rotated reference with the native text direction.

The two custom equality signs are measured as semantic unions of their two individually ledgered `GRAPHIC/MATH_RULE` paths; all overline/rule paths are listed in `math_rule_ledger.csv`. No category-wide overlap exemption is used: the only whitelists are per-pair intra-parent typography, same-series paint order, or stated formula composition.
