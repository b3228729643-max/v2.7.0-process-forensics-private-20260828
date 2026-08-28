# SA1 manual all-pair ledger

Reviewer: SA1 (`/root/p049_r111_fresh_sa1`, `gpt-5.6-sol`, `xhigh`)

I reviewed the final native-300-dpi scope, the nearest-neighbor 8x view, the atomic-ID overlay, the all-pair relation matrix, the five relation ROIs, the 135-glyph inspection sheet, and the 17-path context sheet before writing this ledger. The machine table enumerates every unordered pair exactly once and contains no manual judgment fields.

## Complete pair partition

| Manual ledger ID | Exact machine predicate | Count | Manual observation | Decision | PASS |
|---|---:|---:|---|---|---|
| ML-PAIR-01 | `machine_candidate_class=BBOX_CLEAR` and glyph-glyph | 8,940 | The matrix and final scope show separated glyph atoms belonging to different positions/strings; no shared visible ink and no ambiguity. | ACCEPT | TRUE |
| ML-PAIR-02 | `machine_candidate_class=BBOX_CLEAR` and glyph-path | 2,221 | Glyph and path bboxes are separated by at least 8 px; the final scope confirms no line-through-text, clipping, or semantic attachment error. | ACCEPT | TRUE |
| ML-PAIR-03 | `machine_candidate_class=BBOX_CLEAR` and path-path | 96 | The path atoms are spatially separate; the full figure preserves the intended geometry. | ACCEPT | TRUE |
| ML-PAIR-04 | `machine_candidate_class=BBOX_WITHIN_8PX` and glyph-glyph | 98 | These are adjacent glyphs within the same readable text/math runs or normal base/script constructions. Tight glyph spacing is intentional typesetting, not an illegal overlap between independent semantic objects. | ACCEPT | TRUE |
| ML-PAIR-05 | `machine_candidate_class=BBOX_WITHIN_8PX` and glyph-path | 14 | I inspected each close case in the relation ROIs. Note leaders stop outside glyph ink; axis arrowheads stay clear of labels; the lower formula backing plate prevents the y-axis from running through text. The smallest independent simultaneously visible text-to-path bbox clearance is about 3.17 px (`G-065/P-002`), above the 3 px text/line criterion. The smaller raw bbox value for `G-081/P-003` is not simultaneously visible because the later formula backing plate occludes the axis there. | ACCEPT | TRUE |
| ML-PAIR-06 | `machine_candidate_class=BBOX_WITHIN_8PX` and path-path | 13 | These are joined shaft/arrowhead pairs or intended axis/contour geometry. No unintended collision, malformed join, or misleading contact is present. | ACCEPT | TRUE |
| ML-PAIR-07 | `machine_candidate_class=BBOX_INTERSECTION` and glyph-glyph | 7 | Exact pairs are `G-001/G-002`, `G-028/G-029`, `G-038/G-039`, `G-064/G-065`, `G-079/G-080`, `G-087/G-088`, `G-093/G-094`. They are normal base/subscript or base/superscript PDF bboxes; the glyph sheet shows distinct intact ink and correct math meaning. | ACCEPT | TRUE |
| ML-PAIR-08 | `machine_candidate_class=BBOX_INTERSECTION` and glyph-path | 60 | These are conservative bbox hits caused chiefly by whole-ellipse/whole-guide path bboxes. The native and 8x relation ROIs show that label backing plates remove line-through-text; `v_tan`, `P=(2.4,1.08)`, contour labels, and `f`-increase text retain distinct visible ink. No actual illegal shared foreground pixel is visible. | ACCEPT | TRUE |
| ML-PAIR-09 | `machine_candidate_class=BBOX_INTERSECTION` and path-path | 27 | The actual contacts are mathematically intentional: axes cross each other and level sets; the outer contour, point marker, tangent, and gradient meet at P; shaft/arrowhead and right-angle guide joins are deliberate; note leaders terminate at the referenced geometry. Large contour bboxes also create false intersection candidates. No unintended path collision or semantic error is present. | ACCEPT | TRUE |

The nine rows are mutually exclusive and exhaustive: `8,940 + 2,221 + 96 + 98 + 14 + 13 + 7 + 60 + 27 = 11,476 = C(152,2)`. Pair identity and row-level machine measurements remain in `machine/all_unordered_pair_spatial_candidates_machine.csv`; this manual ledger supplies the reviewer observations and decisions without modifying that machine table.

## Pixel adjudication conclusion

- `OVERLAP_PIXEL_COUNT` (real illegal overlap): `0`.
- `CLIP_PIXEL_COUNT`: `0`.
- Intentional geometry contacts: axis/axis, axis/contours, contour/P, P/tangent, P/gradient, shaft/arrowhead, and right-angle construction. These are semantically required and are not illegal overlap.
- Background plate cases: eleven explicitly enumerated white label plates occlude underlying guide/axis/contour ink where necessary. The faint antialias/opacity residue visible only under nearest-neighbor enlargement does not hide or alter a glyph and is advisory under R168, not a hard failure.
- Pixel adjudication status: `CLEAR`.
