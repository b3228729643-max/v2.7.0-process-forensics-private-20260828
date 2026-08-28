# P654 R100 fresh SA1 test results

- Frozen R100 identity: PASS, 814 pages / 4,943,206 bytes / expected SHA-256.
- Location: physical page 702 / printed page 689 / Figure 34.1.
- Objects: PASS for denominator, `N=116 = 95 glyphs + 21 graphics`.
- Pairs: PASS for denominator, `6,670 / 6,670`, all unique.
- Pixel height: FAIL only for `FRM_TRIAL_005` (`𝑛`), `21px < 22px`.
- Failure-mask integrity: PASS, pre=final=262px and missing/foreign/clip/ownership-loss all zero.
- Final overlap / pair failures / clearance failures / clip: PASS, all zero.
- Fonts, D/E, semantics, drawing/text dual inventory and mathematical rule inventory: PASS.
- Manual coverage: 95/95 glyphs, 21/21 graphics, 50/50 critical pairs and 5/5 views; no pending/unknown.
- Package: PASS, 946 readable ordinary files / 943 manifest payload entries / unexpected extras 0 / ADS 0 / stop marker strictly latest.
- Verdict: `FAIL_TO_SA2`.
