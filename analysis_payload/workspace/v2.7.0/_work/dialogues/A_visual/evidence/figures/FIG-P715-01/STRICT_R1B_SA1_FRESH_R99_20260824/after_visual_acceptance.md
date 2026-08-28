# FIG-P715-01 — fresh isolated SA1 evidence (frozen R99)

HANDOFF_ID: `A-R99-P715-SA1-FRESH-B-20260824`  
Official candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf`  
Identity: 4,940,207 bytes; SHA-256 `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6` (recomputed matched).  
Independent R99 location: physical PDF page **763** / printed page **750**. The B85 card's historical physical-page 826 cannot exist in this 814-page frozen candidate and was not used as evidence.

## Mandatory gate matrix

| Gate | Result |
|---|---:|
| SOURCE_FONT_PASS | true |
| PIXEL_HEIGHT_PASS | false |
| SAME_CLASS_RATIO_PASS | false |
| ROLE_RATIO_PASS | false |
| ILLEGAL_CANDIDATE_PAIR_COUNT | 19 |
| TRUE_RAW_COLLISION_PAIR_COUNT | 16 |
| CLEARANCE_ONLY_FAILURE_PAIR_COUNT | 3 |
| MASK_CONTAMINATION_PIXEL_COUNT | 0 |
| OVERLAP_PIXEL_COUNT | 943 |
| PIXEL_ADJUDICATION_STATUS | TRUE_COLLISION_AND_CLEARANCE_FAILURE |
| CLIP_PIXEL_COUNT | 0 |
| MIN_TEXT_CLEARANCE_PX | 0.0 |
| FONT_VISUAL_HARMONY_PASS | false |
| FOUR_VIEW_COMPLETE | true |
| FOUR_VIEW_ALL_PASS | false |
| OBJECT_REVIEW_COMPLETE | true (298/298) |
| RAW_MASK_PURITY_COMPLETE | true |
| CRITICAL_PAIR_ADJUDICATION_COMPLETE | true (20/20) |
| MATH_SEMANTICS_PASS | true |
| TEXT_CONSISTENCY_PASS | true |
| GRAYSCALE_PASS | true |
| PAGE_INTEGRATION_PASS | true |

## Fresh findings

The figure passes source-size, vector identity, semantics, four-view coverage, and raw-mask-purity checks. It **fails** the strict pixel gate: the all-glyph ledger contains low-stroke CJK `一` glyphs that remain classed as `CJK_FULL` as required by the protocol, with actual final native-300dpi ink heights below the mandatory 30px threshold. The same glyphs also break the same-role/class ratio when measured as individual glyph masks. This is not reclassified as script or punctuation.

It also fails geometry: `after_overlap_adjudication.csv` records 19 independently non-whitelisted critical relations, consisting of 16 actual raw-mask collisions (943 native pixels in total) and 3 clearance-only failures. The latter are explicitly not called ink collisions: their raw masks are separated, but the applicable text/vector-bbox or text-to-border clearance gate is still below its hard minimum. `MASK_CONTAMINATION_PIXEL_COUNT=0` does not erase a real collision or a clearance failure.

The failure is evidence-based and not a mask-contamination claim: every target glyph/path has an isolated final-visible raw mask, a unique safe filename, a seqno/replay ownership record (paths), and actual native 1x/nearest-8x review cards. No `GRAPHIC/MATH_RULE` path exists in this source/PDF figure; all visible formula content is covered by texttrace glyph objects.

## Required SA2 action

Target the strict `CJK_FULL` per-glyph-height and same-class-ratio failures in `web_random_walk.tex` without global scaling, then issue a new official candidate and a completely fresh evidence round. Do not treat this report as a final goal PASS.

## Result

`FAIL_TO_SA2`
