# FIG-P580-01 — strict SA1 R1 visual acceptance

## Frozen candidate and scope

- Candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf`
- Re-located by caption/body anchors: physical PDF page 628; printed page 615.
- Render basis: direct Poppler `pdftoppm` PDF raster, 300 dpi native 2481×3508 pixels; all figures/crops use integer coordinates with no resampling. 8× nearest files are inspection-only.
- Scope: every semantic figure/caption text element, every non-background final-visible vector/pattern object, and all unordered pairs of those objects. Adjacent explanatory body text is read for consistency but not misclassified as figure text.

## Gate matrix

- SOURCE_FONT_PASS = True
- PIXEL_HEIGHT_PASS = False
- FINAL_VISIBLE_MASK_CLOSURE_PASS = True
- CONTAMINATION_GATE_PASS = True
- CHAR_SHAPE_MAPPING_RESOLUTION_PASS = True
- CHAR_SHAPE_PARENT_MAPPING_PASS = False
- MANUAL_CONTACT_LEDGER_COMPLETE = True
- TEXT_COMPLETENESS_PASS = False
- TEXT_HALO_GRAPHIC_COVERAGE_PASS = False
- TEXT_TRANSLUCENT_LABEL_GRAPHIC_COVERAGE_PASS = False
- SAME_CLASS_RATIO_PASS = False
- ROLE_RATIO_PASS = False
- OVERLAP_PIXEL_COUNT = 0
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 0.0
- FONT_VISUAL_HARMONY_PASS = False
- VISUAL_HARMONY_PASS = False
- MATH_SEMANTICS_PASS = True
- TEXT_CONSISTENCY_PASS = True
- GRAYSCALE_PASS = False
- PAGE_INTEGRATION_PASS = False
- MANUAL_VISUAL_LEDGER_COMPLETE = True
- MANUAL_VISUAL_METADATA_RECONCILIATION_PASS = True
- EVIDENCE_COMPLETE = True
- MACHINE_CROSSCHECK = FAIL
- FINAL_VISIBLE_GLYPHS = 228; FINAL_VISIBLE_NECESSARY_SUBSTRINGS = 6; SOURCE_ONLY_FULLY_OCCLUDED_GLYPHS = 3; SOURCE_ONLY_NECESSARY_SUBSTRINGS = 1; RETAINED_PARTIAL_GLYPHS = 0.

## Required findings

- PIXEL_HEIGHT_FAIL: 30 independent glyph/substrings fail; first entries: G0005='：' (9<30), G0014='：' (9<30), G0020='=' (7<22), G0027='一' (6<30), G0035='.' (17<22), G0039='（' (13<30), G0042='：' (7<30), G0045='1' (12<15), G0046='）' (12<30), G0062='：' (16<30), G0067='=' (7<22), G0069='.' (13<22).
- CHAR_SHAPE_MAPPING_FAIL: 1 final-visible records have explicit machine-proven shape/coverage failure evidence; no complete CHAR→shape PASS is claimed.
- TEXT_HALO_GRAPHIC_COVERAGE_FAIL: 8 actual opaque label-ground coverage relation(s) erase a curve/line/nonbackground graphic; see text_halo_graphic_relations.csv.
- TEXT_TRANSLUCENT_LABEL_GRAPHIC_COVERAGE_FAIL: 3 actual translucent label-ground coverage relation(s) cover a curve/line/pattern; see text_translucent_label_graphic_relations.csv.
- D_FAIL: 13 same-panel/same-role/same-script element medians outside [0.92,1.08].
- E_FAIL: 6 role ratios outside their prescribed BASE range.
- CLEARANCE_FAIL: 17 non-intentional relation(s) below requirement or with raw overlap.
- TEXT_OCCLUSION/TEXT_COMPLETENESS_FAIL: actual native final-mask classification shows that the later boundary-label opaque fill removes required q_L suffix source slots and its required fraction composite. Those zero-pixel objects are excluded from final-visible inventory and retained only in source_occlusion_ledger.csv / source_occlusion_substring_ledger.csv with pre/order/halo/final evidence.
- B44 task-card conflict is real: caption/source/body say support coverage; the card's unique-reading conclusion and modification plan incorrectly describe accept–reject. Review is anchored to source/caption/body, not the stale card text.
- Final-visible inventory is derived from actual native masks: source-only glyph IDs = G0095, G0096, G0106; source-only required substring IDs = S002; retained partial glyph IDs = none. No zero-pixel object is represented as final-visible.
- Manual visual ledger: 63/63 native-view/panel-role rows; FONT_VISUAL_HARMONY_PASS=False, GRAYSCALE_PASS=False, PAGE_INTEGRATION_PASS=False. Reviewer decisions are in `manual_visual_harmony_ledger.csv`; current medians/D/E join is `manual_visual_harmony_ledger_CURRENT_MACHINE_JOIN.csv` with before/after provenance in `manual_visual_harmony_metadata_reconciliation.csv`.
- Mathematical recomputation, figure labels, shading, left/right proposals, ratio card, caption, and adjacent reading instruction agree. Support coverage is necessary but not a variance/reliability guarantee.
- Gray-scale reading path judgement is ledger-backed; it cannot be inferred from the presence of a grayscale PNG alone.

## Result

RESULT: FAIL → SA2

A PASS is prohibited because all source-font/actual-pixel/pair gates must be true simultaneously. This R94 SA1 package is read-only and does not modify source, build input, Goal, or central status.
