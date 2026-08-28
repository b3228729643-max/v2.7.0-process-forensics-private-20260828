# R168 manual adjudication

HANDOFF_ID=`C-FIG-P667-01-R114-SA2-R168-READONLY-ADJUDICATION-V1`

UID=`FIG-P667-01`

ROLE=`SA2 isolated read-only adjudicator`

MODEL=`gpt-5.6-sol`

REASONING=`xhigh`

## R168 application

The source contains 8.5 pt underbrace labels, 8.8 pt brace/marginal material, and 9.4 pt kernel/result material. Under R168 those values, including values below the old 9.5 pt threshold, are advisory-only and cannot alone cause hard failure or source return. Native 300 dpi, full-page, grayscale, and nearest-neighbor 8x observation confirms that all of them remain readable and correctly distinguished.

## Hard-defect search

- Missing/tofu/wrong codepoint: none. The figure+caption inventory contains 223 codepoint occurrences, no U+FFFD and no U+0000. The corrected exact codepoint query `Dir(𝛼+𝑛)` occurs twice on physical page 714. The isolated hollow square is the preceding proof's QED mark, not a missing glyph.
- Mathematical meaning: correct under independent recomputation.
- Actual unreadability: none observed.
- Visibly severe imbalance: none; the 15 pt multiplication sign is an intentional operator accent, while the three kernel rows and result/marginal branches remain visually dominant and coherent.
- True clipping: none. Crop-edge foreground count is 0; no object crosses the crop; minimum object-to-crop margin is 24.417 px.
- Illegal visible-ink overlap: none. Ten machine bbox intersections reduce to compound-scope or container nesting. Their unique union is 14,708 thresholded foreground samples, all manually classified as mask/bbox contamination; canonical true illegal overlap is 0 pixels.
- Semantic/geometric error: none. Solid and dashed flows attach to intended boundaries, avoid text, and preserve the correct derivation direction.

## Decisive clearances

- T13 marginal formula to T14 label: 15 empty thresholded-ink pixels.
- T02 to G01 minimum bbox-to-border clearance: greater than 30 px.
- T05 to G02 minimum bbox-to-border clearance: greater than 32 px.
- T08 to G03 minimum bbox-to-border clearance: greater than 28 px.
- T12 to G06 minimum bbox-to-border clearance: greater than 39 px.

## Manual outcome fields

R168_LOW_FONT_STATUS=`ADVISORY_ONLY_READABLE`

OVERLAP_CANDIDATE_UNIQUE_UNION_PX=`14708`

MASK_CONTAMINATION_PIXEL_COUNT=`14708`

OVERLAP_PIXEL_COUNT=`0`

PIXEL_ADJUDICATION_STATUS=`MASK_CONTAMINATION_CONFIRMED`

CLIP_PIXEL_COUNT=`0`

MIN_DECISIVE_TEXT_TEXT_EMPTY_CLEARANCE_PX=`15`

MATH_SEMANTICS=`CLEAR`

TEXT_CONSISTENCY=`CLEAR`

GRAYSCALE=`CLEAR`

PAGE_INTEGRATION=`CLEAR`

HARD_DEFECT_FOUND=`false`

FINAL_VERDICT=`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
