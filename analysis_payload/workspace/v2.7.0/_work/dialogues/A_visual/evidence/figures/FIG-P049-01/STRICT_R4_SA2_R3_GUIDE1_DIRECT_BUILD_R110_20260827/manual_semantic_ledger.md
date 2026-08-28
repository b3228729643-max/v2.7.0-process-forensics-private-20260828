# FIG-P049-01 R4 manual semantic adjudication

- Reviewer: Dialogue A visual domain, direct observation before ledger write.
- Candidate: standalone PDF SHA-256 `DF2418922BA64F670443F509194588764D760E193B306D445E5EEFC78A5752D9`.
- Source SHA-256: `27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E`.
- Final denominator: 27 visible semantic objects and all 351 unordered pairs; 45 relations received focused review.

## Geometry and mathematics

Guide1 uses the source polyline `(4.12,2.78) -> (1.20,2.45) -> (0.84,1.728)`. Its endpoint is exactly on the outer level curve `c3`: `0.84^2/9 + 1.728^2/3.24 = 49/625 + 576/625 = 1`. The only in-path `c3` root is segment 2 at `t=1`, so this is an endpoint relation, not an internal crossing. The final PDF shows zero shared visible pixels between Guide1 and Guide2, Guide3, the gradient, tangent, right-angle marker, P, axes, c1, c2, all labels, and all three note texts. The closest text relation is note 1 at 9.197 px; the gradient label retains 22 px. Guide1 and Guide2 retain 72.591 px clearance.

The point `P` remains on `c3`; the gradient and tangent meet there at approximately 89.926 degrees, and the right-angle marker remains clear. The objective formula, level ordering `c1<c2<c3`, increase direction, axes, notes, labels, colours and all other source tokens remain semantically unchanged.

## Raw mask alert

Raw pair `P0110` records four candidate pixels between `G_CONTOUR_C3` and `T_CONTOUR_C2`. I opened both `rois/c2_outer_candidate_native1x.png` and its nearest-neighbour 8x enlargement. Both show a continuous white gap between the visible `c2` glyph ink and the outer curve. The raw row remains unchanged; `machine/MACHINE_ADJUDICATION.json` records the object-specific mask-contamination decision. Final illegal overlap is zero.

## Caption and page regression boundary

The authorized standalone wrapper suppresses the caption, so caption glyphs are not silently added to the standalone N=27 denominator. The source caption token and wrapper identity are unchanged by the one-line Guide1 geometry patch. The official R110 page/caption was the frozen integration reference, while the new standalone crop remains inside the unchanged figure bounds. This local result therefore validates the changed figure geometry and records caption/page preservation as a source-and-bounds regression; it does not claim to be a new official full-book candidate.

## R168 verdict

No missing glyph, tofu, wrong codepoint or mathematical meaning, unreadable text, obvious scale imbalance, true clipping, illegal overlap, or broken geometry was observed. Minor raster or font-outline variation is advisory only. Manual object decisions are 27/27 PASS and focused relation decisions are 45/45 PASS. Final R168 hard failures: 0.
