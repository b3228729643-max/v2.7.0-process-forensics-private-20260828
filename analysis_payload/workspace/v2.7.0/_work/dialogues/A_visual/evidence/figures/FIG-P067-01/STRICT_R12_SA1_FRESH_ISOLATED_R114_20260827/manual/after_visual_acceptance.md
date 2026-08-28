# FIG-P067-01 fresh isolated SA1 acceptance

HANDOFF_ID = `A-R114-P067-SA1-FRESH-ISOLATED-20260827`  
RESULT = `PASS`  
ROLE_SCOPE = `fresh isolated SA1 only`  
LOCAL_OR_BOOK_COUNT_CLAIM = `NONE`

## Required decision matrix

SA1_MODEL = `gpt-5.6-sol`  
SA1_REASONING = `xhigh`  
SA2_MODEL = `NOT_USED`  
SA2_REASONING = `NOT_USED`  
SA2_ESCALATED = `false`  
SA3_MODEL = `NOT_RUN`  
SA3_REASONING = `NOT_RUN`

SOURCE_FONT_PASS = `true` under R168 hard-gate semantics  
LEGACY_9_5PT_SOURCE_THRESHOLD = `advisory_not_met` for locally declared 8.6/8.8/9.2/9.4 pt elements  
PIXEL_HEIGHT_PASS = `true`  
SAME_CLASS_RATIO_PASS = `true`  
ROLE_RATIO_PASS = `true`  
OVERLAP_CANDIDATE_PIXEL_COUNT = `17244`  
MASK_CONTAMINATION_PIXEL_COUNT = `17244`  
OVERLAP_PIXEL_COUNT = `0`  
PIXEL_ADJUDICATION_STATUS = `MASK_CONTAMINATION_CONFIRMED`  
PIXEL_ARBITER_MODEL = `NOT_USED`  
PIXEL_ARBITER_REASONING = `NOT_USED`  
CLIP_PIXEL_COUNT = `0`  
MIN_TEXT_CLEARANCE_PX = `1`  
MIN_TEXT_CLEARANCE_DISPOSITION = `R168 micro-clearance advisory at T21-G46; shared foreground 0; readable and semantically unambiguous`  
VISUAL_HARMONY_PASS = `true`  
MATH_SEMANTICS_PASS = `true`  
TEXT_CONSISTENCY_PASS = `true`  
GRAYSCALE_PASS = `true`  
PAGE_INTEGRATION_PASS = `true`

## Denominator and pair closure

- Frozen visible-object denominator: `69` objects.
- Complete unordered-pair universe: `2,346` pairs.
- Post-observation manual object ledger: `69/69` identities.
- Mechanical bbox candidate pairs: `97`.
- Post-observation manual candidate ledger: `97/97` pair IDs.
- Candidate composite foreground pixels: `17,244/17,244` classified.
- Confirmed true illegal overlap pixels: `0`.
- Unresolved candidates: `0`.

The candidate pixel total is deliberately over-inclusive: it samples composite foreground inside intersecting source/PDF bbox envelopes. Manual per-pair review separates false bbox envelopes, annotation backplate separation, legal axis/tick junctions, legal curve/marker endpoint junctions, legal guide alignments, and legal stem/guide co-location. None is an unrelated semantic-foreground collision.

## Hard-gate reasoning under R168

No missing glyph, tofu, wrong codepoint, semantic mismatch, unreadable text, obvious imbalance, clipping, illegal overlap, endpoint error, or probability/geometry error was observed. The one-pixel `T21-G46` blank clearance and the locally declared sub-9.5 pt values remain explicit advisories; they are not hidden or converted into false threshold compliance. The native 300 dpi and full-page 200 dpi evidence show that all reader information remains clear.

## Mathematics and integration

The masses `(0.15,0.30,0.35,0.20)` sum to `1`. The successive CDF jumps are exactly `0.15`, `0.30`, `0.35`, and `0.20`; the CDF is nondecreasing and right-continuous with filled post-jump and open pre-jump endpoints. It begins at `0` before the support and reaches/stays at `1` after `t=4`. Caption, adjacent page explanation, ticks, annotations, grayscale structure, and page placement agree with these facts.

## Routing

Because this is an honest SA1 `PASS`, the only requested next role is a **different fresh isolated R114 SA3**. This file does not count an `A_LOCAL_PASS`, does not claim a book-level result, and does not start or emulate SA3.
