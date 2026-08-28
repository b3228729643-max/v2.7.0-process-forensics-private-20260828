# Manual pair denominator review

- Reviewer: `A-R110-P582-SA1-FRESH-ISOLATED-20260827`
- Frozen visible object denominator: `N=44` (`27 TEXT`, `17 GRAPHIC`). The complete ordered inventory is `object_manifest.json`.
- Complete unordered-pair denominator: every ID from `PAIR-0001` through `PAIR-0946`, exactly `C(44,2)=946`; the one-to-one rows are in `after_overlap_report.csv` and `pair_manifest.json`.
- Machine hard-gate read: all 946 rows were read through the count/minimum/exception cross-check; `final_visible_overlap_px>0` occurs in `0/946` rows, and text-related clearance below its class threshold occurs in `0/946` rows. The smallest text-related blank clearance is 13.036 px, above the applicable 3 px gate.
- Manual critical set: 35/35 rows were individually opened at 1x/8x in `relation_evidence/` and individually signed in `manual_critical_pair_reviewer_ledger.csv`. This set is exactly the 29 pairs with nonzero pre-occlusion contact plus six explicit regression relations covering the upper equation, `↓ 再下降`, `.380`, the i=3 polyline, and the i=3 marker.
- Noncritical complement: 911/911 rows have zero final-visible overlap and are above the applicable clearance threshold; their masks and object identities were reconciled against the four opened views and the complete text/object overlays. No hidden or unassigned math-rule path exists; all 17 PDF drawing/path records are assigned.
- Design-contact rationale: the 29 pre-occlusion contacts are axes/ticks/arrowheads, stem-marker endpoints, marker-polyline endpoints, deliberate guide/data crossings, or the intentionally coincident i=1 raw/mean point. Each remains semantically legible in the final paint order and has zero final-visible two-mask intersection.
- Manual denominator decision: `PASS` under the explicitly supplied R168 hard-failure scope.
