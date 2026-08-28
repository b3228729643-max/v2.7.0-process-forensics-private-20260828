# FIG-P583-01 R103 Fresh Isolated SA3 Report

## Assignment identity

- HANDOFF_ID: `A-R103-P583-SA3-FRESH-ISOLATED-20260825`
- Instance: `/root/p583_r103_fresh_sa3`
- Model/effort: `gpt-5.6-sol/xhigh`
- Role: fresh isolated SA3
- Target: FIG-P583-01, official frozen R103 full-book PDF, physical page 633
- Policy: R168 visual hard gates plus strict geometry, relation, semantic, crop, and evidence-denominator gates
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R2_SA3_FRESH_ISOLATED_R103_R168_20260825`

## Candidate identity and isolation boundary

The only candidate PDF used was:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`

- pages: 817
- bytes: 4,967,184
- SHA-256: `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- target physical page: 633

The current P583 source, Goal, and strict protocol/schema were read only. No prior P583 evidence, verdict, report, handoff, acceptance history, state, inventory, task packet, route log, git history/diff/log/blame, or P654 evidence was read. No TeX or LuaLaTeX-family engine was started, stopped, or managed. No business source, main tree, central state, inventory, or acceptance state was written.

## Native rendering and opened evidence

Physical page 633 is 595.276 x 841.890 pt. The direct native render is 2481 x 3508 px at 300 dpi, and the lower-resolution context render is 1654 x 2339 px at 200 dpi. The figure crop is the integer rectangle [250, 258, 2188, 1063] px, producing 1938 x 805 px. The standalone plot crop is [583, 270, 1846, 917] px, producing 1263 x 647 px. No 300 dpi measurement image was resized.

Actual human opening and observation covered:

- native whole page, 200 dpi context, figure crop, standalone crop, grayscale view, and text-measurement overlay;
- all 15 glyph contact sheets at 1x plus 8x nearest detail;
- all 3 graphic contact sheets at 1x plus 8x nearest detail;
- the complete unordered-pair matrix and semantic relationship matrix;
- all 8 critical/relationship overlays.

The opened-artifact ledger contains 34/34 PASS rows.

## Independent denominator reconstruction

The page reconstruction closed on:

- 119 visible glyph objects;
- 23 visible graphic components;
- total N = 142 visible objects;
- C = 142 x 141 / 2 = 10,011 unique unordered pairs;
- 10 figure PDF drawing paint operations;
- 340 assigned path-item rows;
- 328 critical-or-relationship pair rows;
- 8 consolidated critical/relationship overlays.

There are zero unmapped visible glyphs, zero empty glyph masks, zero empty graphic masks, and no unassigned visible formula rule or chart foreground component in the denominator. Safe filenames are unique ordinary files; the sealed package has no NTFS alternate data stream.

## Manual per-ID observation

The manual ledger was written after observation and contains exactly 142 unique rows, one per visible object. It records 119 glyphs and 23 graphics, with reviewer, sheet, cell, original-match, overlay-complete, mask-only-pure, missing-stroke count, foreign-pixel count, decision, and an individualized note.

- observed: 142/142
- original match: 142/142 TRUE
- overlay complete: 142/142 TRUE
- mask-only pure: 142/142 TRUE
- missing strokes: 0
- foreign pixels: 0
- outcome: 142 PASS, 0 FAIL, 0 pending

No script generated or overwrote manual reviewer, manual boolean, decision, or note fields.

## R168 font and visual-harmony verdict

The source declares 9.2 pt base text, 8.6 pt tick labels, 9.6 pt axis labels and rate formula, and 9.2 pt annotation/condition text, with the exponent naturally generated from the 9.6 pt formula. No resizing/scaling command is present.

Under the assigned R168 rule, the legacy 9.5 pt floor, `[0.92,1.08]` and related fine taxonomy/peer/metadata metrics, readable absolute-min metadata, and 1-2 px raster differences are advisory only. The hard font gates are missing/tofu, wrong glyph/codepoint/math semantics, genuine unreadability, obvious severe visible imbalance, and real clipping/overlap.

Native page, crop, standalone, grayscale, contact-sheet, and overlay observation found none of those hard failures. `FONT_VISUAL_HARMONY_PASS=TRUE`: axis, tick, formula, annotation, condition, and caption typography forms a readable hierarchy without an obvious severe imbalance.

## Hard geometry and relationship gates

- illegal overlap pixels: 0
- clip pixels: 0
- hard pair failures: 0
- independent text-text minimum: 39.8121 px against 4 px hard minimum
- text/formula-line minimum: 6 px against 3 px hard minimum
- node text-border minimum: 14 px against 5 px hard minimum
- reader glyph-to-crop-edge minimum: 11 px against 6 px hard minimum

The intentional curve connection at the y-axis/top tick was semantically whitelisted and visually confirmed. The triangle diagonal aligns with the rate curve; the horizontal leg represents sample size x4 and the vertical leg represents error divided by 2. Annotation text, rate formula, and condition text retain real foreground clearance. Axes, tick marks, labels, and arrowheads form a correct, unclipped system.

## Semantic, caption, grayscale, and page result

The log-log axes have x ticks 1, 4, 16, 64, 256, 1024 and y ticks 1/32, 1/16, 1/8, 1/4, 1/2, 1. The plotted `x^(-.5)` curve and `O(N^-1/2)` label are correct. The triangle encodes x4 in sample size and divided-by-2 in RMSE. The condition is iid with finite variance. The caption correctly states the theoretical root-mean-square-error rate and warns that correlated samples or infinite variance cannot directly reuse the line.

The figure remains readable and distinguishable in grayscale. The figure float and surrounding body integrate cleanly on the full page with no collision, crop, or page-level imbalance.

## Verdict and route

Verdict: `PASS`

Route: `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`

This report records only the isolated SA3 result. It does not write a main acceptance state; that decision remains with the root single writer after independent validation of the sealed package.
