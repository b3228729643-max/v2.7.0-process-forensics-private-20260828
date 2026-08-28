# P608 R12 manual semantic and geometry adjudication

- Observation completed before ledger creation; the timestamps in the CSV files are observation-window lower bounds, not planned or future opening times.
- Actual views opened: full page, figure crop, standalone page, grayscale, text measurement overlay, four glyph sheets, five graphic sheets, two critical-pair sheets, and the dedicated former-failure relation sheet.
- The 68 glyph and 60 graphic objects were reviewed through their indexed contact sheets. No tofu, wrong codepoint, unreadable glyph, real clipping, foreign object, or obvious visual imbalance was found under the R168 policy.
- The machine denominator is 128 objects and 8,128 unordered pairs. Machine gates report zero empty masks, zero illegal overlaps, zero clearance flags, zero clip failures, and zero hard readability failures.
- Both former failures are closed by native geometry: PAIR-06596 has 0 shared pixels and 16.464 px clearance; PAIR-06650 has 0 shared pixels and 12.928 px clearance.
- Semantic source checks preserve all 15 running-mean values, the final value `2.0000`, tick labels, annotations, caption, two-panel structure, and all data paths. The only source change remains the shared x-domain expansion from `[1,20]` to `[0.5,20.5]`.
- Decision: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`. This is not SA1, SA3, A_LOCAL_PASS, or permission to commit.
