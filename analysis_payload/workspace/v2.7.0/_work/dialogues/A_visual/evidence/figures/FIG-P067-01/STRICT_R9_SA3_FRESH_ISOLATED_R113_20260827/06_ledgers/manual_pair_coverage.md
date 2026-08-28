# Manual relationship coverage

- Frozen visible-object denominator: 130 objects (95 glyphs and 35 final-visible foreground graphics).
- Complete unordered-pair ledger: `after_overlap_report.csv`, exactly 8,385 distinct unordered pairs, equal to C(130,2).
- Manually opened close/overlap/topology set: 71 pair ROIs in the six latest `critical_pair_contact_01_8x_nearest.png` through `critical_pair_contact_06_8x_nearest.png` sheets. Every row has a genuine manual decision in `manual_critical_pair_review.csv`.
- Remaining noncritical set: 8,314 pairs. These were reviewed through the native figure, full-page integration view, text overlay, graphic overlay, and complete machine bbox/mask ledger. None was a final-visible independent-overlap candidate.
- Final relationship resolution: 69 of 71 critical pairs are clear, genuinely occluded, or intentional topology; two are hard failures: P01916 and P01917.
- Pre-occlusion-to-final correction is preserved: P01217 changes from 17 px to 0 px because of the real p1 white node background, and P05606 changes from 41 px to 0 px because of the real annotation background. The two p4 failures remain 34 px both before and after real-background masking.

The denominator and pair enumeration were frozen before manual decisions. No script generated reviewer, decision, boolean, or note fields in the manual ledgers.
