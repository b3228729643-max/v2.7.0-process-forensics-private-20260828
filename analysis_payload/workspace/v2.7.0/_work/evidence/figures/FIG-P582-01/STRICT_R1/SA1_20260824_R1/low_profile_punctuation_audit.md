# Revision 111 low-profile punctuation audit

Coordinate system: the candidate PDF's native 300dpi render, using final-visible pure raw masks at 1:1 for all counts. Enlarged nearest-neighbor 8x packages are retained only for the individual visual review.

The 21 applicable low-profile glyphs are listed in `low_profile_punctuation_calibration.csv` and manually recorded in `low_profile_reviewer_ledger.csv`. Each target has a package under `low_profile_calibration/packages/<GLYPH_ID>/` with source/reference mask, target final-visible mask, a native 1x strip, an 8x-nearest strip, and a manifest. Reference selection is same codepoint, font, weight, color, and effective point size within 0.25pt; CJK caption punctuation uses the recorded project-small independent render.

The hard gate is `LOW_PROFILE_TOTAL_GATE_PASS`, not a generic height threshold or a `STATUS` column. It requires a complete, pure final mask, source effective size at least 9.5pt, and both H_INK and ink-area ratios in [0.92, 1.08].

Results:

- 21 targets were calibrated and manually reviewed.
- G0082 (caption full stop) fails calibration: H_INK ratio 1.1667 and ink-area ratio 1.5769.
- G0114 (caption fullwidth semicolon) fails calibration: H_INK ratio 0.9032 and ink-area ratio 0.5437. Its final mask is nevertheless pure and complete; this is a true calibration failure, not contamination.
- Eleven tick/numeric decimal dots calibrate geometrically but fail the independent source-size floor because their effective sizes are 8.6pt or 8.5pt.
- Thus two calibration failures plus eleven size-floor failures give 13 `LOW_PROFILE_TOTAL_GATE_PASS=false` rows. The low-profile hard gate is false.

The evidence does not relax any required figure gate: it records a precise revision-111 measurement basis for punctuation that is too small for the old generic H_INK thresholds.
