# FIG-P033-01 — R110 fresh isolated SA1 sealed report

## Identity and isolation

- Handoff: `A-R110-P033-SA1-FRESH-ISOLATED-20260827`
- Instance: `/root/p033_r110_fresh_sa1`
- Model/effort: `gpt-5.6-sol/xhigh`
- Fork: `none`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R2_SA1_FRESH_ISOLATED_R110_20260827`
- Isolation boundary: no SA2 evidence and no prior P033/other-UID evidence, report, handoff, state, inventory, chat, Git-history conclusion, or main acceptance was read.

The official candidate was independently located from its current caption as physical PDF page 29, printed page 16, Figure 2.1, `向量的正交分解`.

## Frozen denominator and machine closure

- Official PDF: 817 pages, 4,967,063 bytes, SHA-256 `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`.
- Current source: 2,383 bytes, SHA-256 `4BCD50FE3BFDF1A3DCFC9089E103D256555949D859EC650F047CECB3A04EF6D4`.
- Visible denominator: 85 glyphs plus 14 drawings/paths, N=99.
- Complete unordered pairs: C(99,2)=4,851, all present exactly once.
- Empty masks: 0. Foreign/unassigned objects: 0. Clip pixels: 0.
- Corrected final machine hard relations: 1. Critical relations: 10.

## Selector correction before manual review

The initial provisional selector squared color differences in `int16`, which overflowed and invalidated the predicate; its seven provisional hard relations were withdrawn. After color distance was corrected to `float32`, three provisional hits remained because same-color drawing geometry contaminated glyph bounding boxes. The final selector used exact single-use SVG glyph geometry from the same official PDF page: 720 SVG uses matched 720 extracted PDF characters, and exactly 85 uses belonged to the frozen crop. Each selector was intersected back with the native Poppler 300 dpi raster, and opaque-halo occlusion was accounted for. The complete N=99/C=4,851 analysis was then recomputed. Manual review used only those corrected sheets and ROIs.

## Pre-seal crosscheck correction

The first invocation of the newly written final crosscheck exited 1 for three crosscheck-assertion errors: it misread `foreign_pixel_px_removed_by_vector_selector` as residual contamination, searched only the top level of the nested mask directory, and assumed ten PNGs per relation rather than the actual six ROI files plus their combined 8x contact-sheet panels. These assertions were corrected to the actual frozen schema and dynamic denominator. No selector scan was rerun; no final mask, relation metric, manual ledger, or R2886 decision changed. The corrected rerun exited 0 and is the sole seal result: official PDF/source identities pass; N=99; C=4,851; machine hard=1 (`R2886`); critical=10; contact sheets=20; manual object ledger=99/99; critical manual ledger=10/10; view ledger=4/4.

## Actual visual and manual review

- Opened and reviewed 11/11 glyph contact sheets, 4/4 drawing contact sheets, and 5/5 corrected critical-relation contact sheets.
- Opened the full page, native 300 dpi crop, standalone crop, grayscale crop, and individual raw/mask/intersection/overlay ROIs for every critical relation.
- Handwritten ledgers cover 85/85 glyphs, 14/14 drawings, 10/10 critical relations, and 4/4 whole-view checks.
- Typography/harmony: PASS. The 9.4 pt base and 9.2 pt local text are readable and balanced; their being below a former 9.5 pt threshold is R168 advisory only.
- Mathematical semantics: PASS. Projection, residual, orthogonality, norm identity, and shortest-distance meanings are correct.
- Grayscale, page fusion, legibility, balance, and clipping: PASS.

## Sealed decision

**FAIL.** R2886 is a genuine illegal overlap: 24 native 300 dpi pixels overlap between the top horizontal stroke of G036 (`子` in the subspace label) and diagonal lower plane boundary D002, with clearance 0 px against a 3 px requirement. The corrected raw, isolated masks, intersection, and 8x overlay all agree. This is not a 1–2 px micro-raster advisory.

Return this candidate to SA2 for correction. Do not request fresh isolated SA3 for the current candidate.
