# Fresh isolated SA3 visual acceptance

HANDOFF_ID = C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-V1  
UID = FIG-P680-01  
SA3_MODEL = gpt-5.6-sol  
SA3_REASONING = xhigh

## Current localization and denominator

The current source/caption independently localize to physical PDF page 729 (printed page 716) of the exact 817-page R114 PDF. The match is unique in the searched current chapter neighborhood and is corroborated by the full caption, warning sentence, both model labels, and both inference labels.

- Reader-visible semantic objects: `14/14`
- Addressable text/glyph groups: `15/15`
- Glyph records extracted from the current PDF region: `212`
- Unordered object pairs: `91/91`
- Manual object verdicts: `14 CLEAR`
- Manual pair verdicts: `91 CLEAR`
- Manual glyph-group verdicts: `15 CLEAR`
- Manual math verdicts: `3 CLEAR`
- Manual semantic verdicts: `9 CLEAR`
- Manual page-integration verdicts: `1 CLEAR`

## Views actually opened after machine generation

- Full page at 300 dpi and 200 dpi
- Figure crop at native 300 dpi
- Native-300 grayscale figure
- Native-300 object and text-ID overlays
- Top curved-arrow ROI at native 1× and nearest-neighbor 8×
- Vertical-arrow ROI at native 1× and nearest-neighbor 8×
- Complete warning-plus-caption ROI at native 1× and nearest-neighbor 8×

## R168 hard-failure review

R168 makes the older numeric font, pixel-height, and ratio thresholds advisory. The hard-failure review found none of the qualifying defects:

- Missing glyph, tofu, or wrong codepoint: `NO`
- Wrong math or formula meaning: `NO`
- Unreadability or severe visual imbalance: `NO`
- True clipping: `NO`
- Illegal visible-ink overlap: `NO`
- Semantic or geometric error: `NO`

The source uses 9.4 pt for ordinary node text, 9.8 pt for row labels, and 9.2 pt for the warning. The official PDF vector sizes agree closely; measured line ink heights are 34–44 px at native 300 dpi. One automated content-sensitive ratio reports T04 at 1.20 relative to the node-text median because that line mixes Chinese with tall Latin capitals; the source uses the same 9.4 pt as its peer nodes, and the opened native/8× views show neither unreadability nor severe imbalance. These old numeric observations are advisory under R168 and do not establish a hard failure.

## Acceptance matrix

- SOURCE_FONT_PASS = true (R168 actual-render criterion)
- PIXEL_HEIGHT_PASS = true (R168 actual readability criterion)
- SAME_CLASS_RATIO_PASS = true (R168; no severe imbalance in opened views)
- ROLE_RATIO_PASS = true (R168; row labels, node text, warning, and caption preserve hierarchy)
- OVERLAP_CANDIDATE_PIXEL_COUNT = 0 (illegal candidate set)
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = CLEAR
- PIXEL_ARBITER_MODEL = NOT_USED
- PIXEL_ARBITER_REASONING = NOT_USED
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 10.83 (closest independent caption-line bboxes; no shared ink)
- VISUAL_HARMONY_PASS = true
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

## SA3 verdict

`PASS`

This is one isolated SA3 verdict awaiting Main's local-pass acceptance. It is not a self-counted local, global, final-99, or release pass.
