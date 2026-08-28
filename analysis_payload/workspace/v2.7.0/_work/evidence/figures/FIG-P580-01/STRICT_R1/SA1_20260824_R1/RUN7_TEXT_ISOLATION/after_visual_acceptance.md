# FIG-P580-01 — strict SA1 R1 visual acceptance (05:30 ATTEMPT SUPERSEDED)

> **WITHDRAWN:** evidence-completeness was false and 236/236 manual contact
> review had not occurred. This file is retained only to explain the aborted
> attempt; it is not an acceptance report.

## Frozen candidate and scope

- Candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf`
- Re-located by caption/body anchors: physical PDF page 628; printed page 615.
- Render basis: direct Poppler `pdftoppm` PDF raster, 300 dpi native 2481×3508 pixels; all figures/crops use integer coordinates with no resampling. 8× nearest files are inspection-only.
- Scope: every semantic figure/caption text element, every non-background final-visible vector/pattern object, and all unordered pairs of those objects. Adjacent explanatory body text is read for consistency but not misclassified as figure text.

## Gate matrix

- SOURCE_FONT_PASS = True
- PIXEL_HEIGHT_PASS = False
- FINAL_VISIBLE_MASK_CLOSURE_PASS = False
- CHAR_SHAPE_MAPPING_RESOLUTION_PASS = False
- CHAR_SHAPE_PARENT_MAPPING_PASS = False
- TEXT_COMPLETENESS_PASS = False
- SAME_CLASS_RATIO_PASS = True
- ROLE_RATIO_PASS = True
- OVERLAP_PIXEL_COUNT = 0
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 0.0
- VISUAL_HARMONY_PASS = True
- MATH_SEMANTICS_PASS = True
- TEXT_CONSISTENCY_PASS = True
- GRAYSCALE_PASS = True
- PAGE_INTEGRATION_PASS = True
- EVIDENCE_COMPLETE = False
- MACHINE_CROSSCHECK = FAIL
- FINAL_VISIBLE_GLYPHS = 229; SOURCE_ONLY_FULLY_OCCLUDED = 2; RETAINED_PARTIAL_FRAGMENTS = 1 glyph + S002 substring.

## Required findings

- PIXEL_HEIGHT_FAIL: 39 independent glyph/substrings fail; first entries: G0005='：' (9<30), G0014='：' (9<30), G0020='=' (7<22), G0027='一' (6<30), G0032='.' (6<22), G0035='.' (6<22), G0039='（' (11<30), G0042='：' (5<30), G0045='1' (12<15), G0046='）' (12<30), G0062='：' (10<30), G0067='=' (7<22).
- CHAR_SHAPE_MAPPING_PENDING: 234 records await required 8× nearest contact-sheet inspection.
- CHAR_SHAPE_MAPPING_FAIL: 2 final-visible records are proven opaque-halo fragments, so no complete CHAR→shape PASS is claimed.
- CLEARANCE_FAIL: 22 non-intentional relation(s) below requirement or with raw overlap.
- TEXT_OCCLUSION/TEXT_COMPLETENESS_FAIL: later boundary-label opaque fill fully hides q_L '=' and numerator '2', leaves only a denominator fragment, and makes the required left q_L '=2/5' suffix unreadable. Fully hidden source slots are excluded from final-visible inventory and retained in source_occlusion_ledger.csv; pre/order/halo/final evidence is retained without synthetic pre-text ink.
- B44 task-card conflict is real: caption/source/body say support coverage; the card's unique-reading conclusion and modification plan incorrectly describe accept–reject. Review is anchored to source/caption/body, not the stale card text.
- Final-visible inventory closure excludes only G0095 '=' and G0096 '2', whose complete source slots lie under the later real opaque halo; G0106 '5' and required S002 remain as documented nonempty fragments and fail CHAR-shape/TEXT_COMPLETENESS instead of being silently treated as complete.
- Source-font coordination: 9.6 pt normal figure text, 10.2 pt panel titles, and 10 pt `small` caption are proportionate in the direct full-page/crop/grayscale review; no enlargement competes with the curves. This visual harmony cannot override a per-glyph pixel hard failure.
- Mathematical recomputation, figure labels, shading, left/right proposals, ratio card, caption, and adjacent reading instruction agree. Support coverage is necessary but not a variance/reliability guarantee.
- Gray-scale reading path remains left support gap → right full support → caption conclusion; solid/dashed lines, hatch, and marker shapes supplement colour.

## Result

RESULT: FAIL → SA2

A PASS is prohibited because all source-font/actual-pixel/pair gates must be true simultaneously. This R94 SA1 package is read-only and does not modify source, build input, Goal, or central status.
