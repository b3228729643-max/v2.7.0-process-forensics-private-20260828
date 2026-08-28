# FIG-P660-01 critical-pair manual adjudication

The complete machine denominator contains 946 unordered pairs in `machine/all_unordered_pairs_evidence.csv`. Eight hundred five pairs have disjoint conservative bboxes. The 41 reader-critical pairs below were selected from label-guide, label-boundary, container-text, stacked-text, and caption-integration relations. Their latest evidence was opened in `overlays/critical_pair_contact_sheet_01.png` through `_06.png`, with tight native1x/nearest8x ROIs opened for the four stacked-line cases.

- `P0601` (`G18`,`T01`): the `theta2` guide ends well to the right of the label; measured ink-bbox gap is 34.482 px. Manual classification: clear, no shared foreground.
- `P0576` (`G17`,`T02`): the `theta1` guide endpoint and label remain visually separate; measured gap is 41.725 px. Manual classification: clear.
- `P0628` (`G19`,`T03`): the vertical `theta3` guide stops at the baseline above the label; measured gap is 48.795 px. Manual classification: clear.
- `P0578` (`G17`,`T04`): the right projection guide and tuple label are separated by 76 px at the ink-bbox level. Manual classification: clear.
- `P0653` (`G20`,`T04`): the point marker is left of the tuple with 188 px bbox separation. Manual classification: clear.
- `P0069` (`G02`,`T05`): the top formula is above the apex/left edge, with 64 px conservative separation. Manual classification: clear.
- `P0110` (`G03`,`T05`): the top formula is above the apex/right edge, also with 64 px separation. Manual classification: clear.
- `P0070` (`G02`,`T06`): the top Chinese description remains 32 px from the left-edge bbox. Manual classification: clear.
- `P0111` (`G03`,`T06`): the top Chinese description remains 32 px from the right-edge bbox. Manual classification: clear.
- `P0071` (`G02`,`T07`): the left vertex formula lies below/outside the side with 30 px measured separation. Manual classification: clear.
- `P0152` (`G04`,`T07`): the left vertex formula is 30 px below the bottom boundary. Manual classification: clear.
- `P0072` (`G02`,`T08`): the left vertex description is farther below the side, with 74 px conservative gap. Manual classification: clear.
- `P0153` (`G04`,`T08`): the left vertex description is 74 px below the baseline bbox. Manual classification: clear.
- `P0114` (`G03`,`T09`): the right vertex formula lies below/outside the side with 30 px separation. Manual classification: clear.
- `P0154` (`G04`,`T09`): the right vertex formula is 30 px below the bottom boundary. Manual classification: clear.
- `P0115` (`G03`,`T10`): the right vertex description is 74 px from the right/bottom boundary bboxes. Manual classification: clear.
- `P0155` (`G04`,`T10`): the right vertex description is 74 px below the baseline bbox. Manual classification: clear.
- `P0683` (`G21`,`T11`): bbox containment is intentional card membership; native pixels show 36 px minimum text-to-card-edge clearance for this line. Manual classification: intended containment, no border collision.
- `P0684` (`G21`,`T12`): bbox containment is intentional; native pixels show 32 px minimum text-to-card-edge clearance. Manual classification: intended containment, no border collision.
- `P0707` (`G22`,`T13`): the interior statement is inside its card with 23 px minimum edge clearance. Manual classification: intended containment, no collision.
- `P0708` (`G22`,`T14`): the edge statement is inside its card with 52 px minimum edge clearance. Manual classification: intended containment, no collision.
- `P0709` (`G22`,`T15`): the vertex statement is inside its card with 37 px minimum edge clearance. Manual classification: intended containment, no collision.
- `P0731` (`G23`,`T16`): the first conclusion line is inside its card with 34 px minimum edge clearance. Manual classification: intended containment, no collision.
- `P0732` (`G23`,`T17`): the second conclusion line is inside its card with 53 px minimum edge clearance. Manual classification: intended containment, no collision.
- `P0733` (`G23`,`T18`): the closing conclusion line is inside its card with 34 px minimum edge clearance. Manual classification: intended containment, no collision.
- `P0811` (`T05`,`T06`): conservative ink bboxes overlap because the formula includes a subscript, but the exact native scan contains five consecutive empty foreground rows (336–340) between the rendered lines. Manual classification: bbox false positive, native foreground clear.
- `P0842` (`T07`,`T08`): the exact native scan contains six consecutive empty foreground rows (1204–1209). Manual classification: bbox false positive, native foreground clear.
- `P0869` (`T09`,`T10`): the exact native scan likewise contains six consecutive empty foreground rows (1204–1209). Manual classification: bbox false positive, native foreground clear.
- `P0892` (`T11`,`T12`): formula bboxes overlap due superscript/subscript extents, while native rows 608–611 are wholly empty between the two rendered lines. Manual classification: bbox false positive, native foreground clear.
- `P0911` (`T13`,`T14`): the two card lines have 11 px ink-bbox separation and remain visually independent. Manual classification: clear.
- `P0919` (`T14`,`T15`): the second and third card lines have 10 px ink-bbox separation. Manual classification: clear.
- `P0932` (`T16`,`T17`): the first and second conclusion lines have 10 px ink-bbox separation. Manual classification: clear.
- `P0937` (`T17`,`T18`): the second and third conclusion lines have 11 px ink-bbox separation. Manual classification: clear.
- `P0944` (`T19`,`T20`): the bold caption tag and caption prose have 43 px horizontal separation and form a readable single caption line. Manual classification: clear.
- `P0946` (`T20`,`T21`): the two caption lines have 14 px ink-bbox separation; no ascender/descender contact is present. Manual classification: clear.
- `P0853` (`T07`,`T19`): the left vertex formula is 75 px above the caption tag. Manual classification: clear.
- `P0866` (`T08`,`T19`): the left vertex description is 43 px above the caption tag. Manual classification: clear.
- `P0879` (`T09`,`T20`): the right vertex formula is 75 px above the caption prose. Manual classification: clear.
- `P0890` (`T10`,`T20`): the right vertex description is 43 px above the caption prose. Manual classification: clear.
- `P0735` (`G23`,`T20`): the conclusion card border and first caption line are vertically separated by 53 px. Manual classification: clear.
- `P0736` (`G23`,`T21`): the conclusion card border and second caption line are vertically separated by 109 px. Manual classification: clear.

Adjudication result: none of the 41 reader-critical pairs has true shared foreground, clipping, obscuration, or an unresolved native-pixel ambiguity. Geometry-only lattice crossings, shared endpoints, marker-guide joins, and card containment are source-defined intentional topology, not illegal overlap. Canonical true-illegal-overlap pixel count is zero.
