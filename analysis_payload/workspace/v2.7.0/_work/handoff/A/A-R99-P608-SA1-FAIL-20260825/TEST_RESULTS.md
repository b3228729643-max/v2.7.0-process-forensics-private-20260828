# P608 R99 SA1 test results

- Frozen R99 identity: PASS, 814 pages / 4,940,207 bytes / expected SHA-256.
- Location: physical page 660 / printed page 647.
- Objects: PASS for denominator, N=170 = 112 glyphs + 58 paths.
- Pairs: PASS for denominator, 14,365 / 14,365.
- Object manual review: PASS for coverage, 170 / 170.
- Critical-pair review: PASS for coverage, 13 / 13.
- Pixel height: FAIL only for GLYPH_0025 and GLYPH_0056, natural-script `t`, each 10 px < 15 px.
- Final overlap / pair failures / clip: PASS, all zero.
- D/E, punctuation calibration, semantics and required views: PASS.
- R5A reuse integrity: PASS, 794 / 794 byte-size-hash matches.
- Package / ADS / seal: PASS, 802 files / ADS0 / stop marker strictly latest.
- Verdict: `FAIL_TO_SA2`.
