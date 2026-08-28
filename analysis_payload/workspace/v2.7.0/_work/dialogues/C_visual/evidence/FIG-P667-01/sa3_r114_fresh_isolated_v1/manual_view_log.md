# SA3 post-observation view log

Reviewer identity: `/root/sa3_fig_p667_r114_fresh_isolated_v1`  
HANDOFF_ID: `C-FIG-P667-01-R114-SA3-FRESH-ISOLATED-V1`  
UID: `FIG-P667-01`  
Observation date: 2026-08-28 (Asia/Shanghai)

All entries below were actually opened before the manual ledgers and final verdict were authored.

## Page and complete-object views opened

1. `page_0714_native300dpi.png` — complete R114 physical page; figure placement, surrounding proof end, preceding cross-reference, following heading/self-check/proposition, margins and footer inspected.
2. `page_0714_native200dpi.png` — normal-page integration view; figure remains readable and does not create a bad page break, orphan, collision or severe whitespace imbalance.
3. `figure_caption_native300dpi.png` — complete figure and two-line caption at native 300 dpi; every reader-visible element inspected.
4. `figure_caption_grayscale_native300dpi.png` — grayscale hierarchy and line-style redundancy inspected.
5. `object_bbox_overlay_native300dpi.png` — all frozen IDs and bboxes inspected against the native rendering.
6. `semantic_object_mask_overlay_native300dpi.png` — all 24 semantic masks inspected for attribution and missing coverage.
7. `visible_ink_union_mask_native300dpi.png` — complete visible-ink coverage and crop-edge separation inspected.

## Decisive native1x and nearest-neighbor8x ROIs opened

1. `ROI01_prior_exponent_label_native1x.png` and `ROI01_prior_exponent_label_nearest8x.png` — prior exponent, underbrace, label and nearby product subscript.
2. `ROI02_likelihood_exponent_label_native1x.png` and `ROI02_likelihood_exponent_label_nearest8x.png` — likelihood exponent, underbrace, label and the T06/T07 candidate.
3. `ROI03_multiply_brace_annotation_native1x.png` and `ROI03_multiply_brace_annotation_nearest8x.png` — multiplication sign, tall brace and its annotation.
4. `ROI04_posterior_exponent_label_native1x.png` and `ROI04_posterior_exponent_label_nearest8x.png` — posterior exponent, underbrace and annotation.
5. `ROI05_main_arrow_and_result_native1x.png` and `ROI05_main_arrow_and_result_nearest8x.png` — solid flow arrow, result box and both result lines.
6. `ROI06_branch_and_marginal_native1x.png` and `ROI06_branch_and_marginal_nearest8x.png` — dashed branch, arrowhead, marginal formula and note.
7. `ROI07_caption_line1_native1x.png` and `ROI07_caption_line1_nearest8x.png` — caption label, mixed Chinese/Latin/math codepoints and first line.
8. `ROI08_caption_line2_native1x.png` and `ROI08_caption_line2_nearest8x.png` — second caption line, α+n and Dirichlet–multinomial wording.

## Nonzero-candidate overlays opened

1. `G06__G07_native1x.png` and `G06__G07_nearest8x.png` — red box border, blue dashed branch, yellow three-pixel common junction.
2. `T06__T07_native1x.png` and `T06__T07_nearest8x.png` — red formula mask, blue label mask, yellow three-pixel bbox/antialias attribution candidate.

Observation summary: no missing or tofu glyph, wrong rendered codepoint, actual unreadability, severe imbalance, true clipping, illegal visible-ink overlap, or semantic/geometric error was seen. The only six machine intersection pixels are fully adjudicated in `manual_pair_adjudication.md`.
