# FIG-P608-01 fresh isolated SA1 review

## Decision

`FAIL_TO_SA2`

One mandatory hard gate fails: `PEER-TXT-098` (`FULLBOOK_LOW_PROFILE_RATIO`). The caption semicolon has target height 28 px and peer height 28 px (ratio 1.0), but target area 56 px versus deterministic exact-metadata peer area 72 px, ratio **0.7777777777777778**, outside **[0.92,1.08]**. The threshold remains 20/255 and no fallback peer or relaxation is used.

## Candidate and domain

The exact 814-page R101 candidate is confirmed at 4,947,496 bytes and SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`. The target is current physical page 659, printed page 646, Figure 32.8. The complete same-number caption paragraph is inside the crop.

The independently reconstructed denominator is **N=172** = 112 glyphs + 58 explicit PDF drawings + 2 hatch-pattern layers. The pair universe is **C=14,706**, fully covered once. There are zero clipped pixels, zero empty masks, zero illegal final-visible overlaps, and all 102 critical pairs are individually adjudicated.

## Typography calibration

The complete R101 was searched under a policy frozen before looking at peer ink height/area: same codepoint, font/weight, colour, and effective point size within 0.25 pt; candidates ordered without pixel-result information. `TXT-072` has 99 exact candidates and passes against physical page 17/raw sequence 251. `TXT-098` has 64 exact candidates; the deterministic selected peer is physical page 187/raw sequence 345 and fails only the area ratio. No different glyph, font, weight, colour, or size is substituted.

## Preliminary rebuild provenance

The deterministic v1 replay exactly regenerates all 64 preliminary apparent failures. Accepted rebuilding resolves 63 as ownership contamination or fractional glyph-edge attribution while preserving the 20/255 threshold; one item, `TXT-098`, remains. Each of the 64 rows has its own before/after masks, contamination accounting, bbox/paint-order basis, missing/foreign-pixel check, and manual decision. The x-tick text `15` is conserved as two characters and two glyph objects (`TXT-034`, `TXT-035`) under one semantic tick parent.

## Manual ledger counts

- object decisions: 172
- critical-pair decisions: 102
- preliminary-item decisions: 64
- low-profile peer decisions: 13
- role decisions: 35
- view decisions: 4
- hard-failure decisions: 1

SA3 is not started. This result is not `A_LOCAL_PASS`.
