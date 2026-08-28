# FIG-P020-01 R6 R111 SA1 final verdict

## SA1 RESULT: FAIL

The sole verified figure-gate failure is `F020_G091` (caption CJK `一`): direct R95 page-17 native 300 dpi raw mask has `H_INK_PX=5`, below the revision-111 CJK/fullheight minimum of `30px`. Its 1× original, unique red overlay, mask-only image, 8× nearest triad, and CS016 contact cell are retained. This is not a low-profile-punctuation exception.

All 108 glyph masks were manually reviewed and are complete/pure; all 45 unordered text-text pairs, 140 text-graphic relations, 12 cross-panel relations, and 10 crop-edge relations passed. The real opaque white return-label ground has a closed pre/ground/final reversal with zero covered return-arrow pixels. Low-profile punctuation calibration passed 7/7. D/E and the four-view font visual harmony ledger passed. Those pass results do not waive the G091 hard threshold.

## Required route

Route only to SA2. Suggested fix: replace or rework the one-stroke caption wording/typography so every retained CJK glyph reaches `H_INK_PX>=30` at native 300 dpi while retaining `effective_pt>=9.5`, clearance, and visual harmony. Rebuild the frozen candidate and regenerate a wholly new audit. No SA3 handoff is authorized from this FAIL verdict.
