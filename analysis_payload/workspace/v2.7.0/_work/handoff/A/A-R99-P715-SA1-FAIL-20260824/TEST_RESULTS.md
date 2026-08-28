# P715 R99 SA1 test results

- Frozen R99 identity: PASS, 814 pages / 4,940,207 bytes / expected SHA-256.
- Independent location: physical page 763 / printed page 750.
- Object denominator: PASS, 298 = 255 glyphs + 43 paths.
- Pair denominator: PASS, 44,253 / 44,253.
- Object review: PASS for coverage, 298 native 1x/nearest-8x rows.
- Critical-pair review: PASS for coverage, 20 / 20 opened and adjudicated.
- Pixel typography: FAIL, 44 glyph failures; `G0012` CJK_FULL `一` is 6 px < 30 px.
- Geometry: FAIL, 16 raw-collision pairs / 943 native pixels and 3 clearance-only failures.
- Clip / mask contamination: PASS, both zero.
- Manifest: PASS, 833 / 833 hashes and sizes, zero mismatches.
- ADS: PASS, zero non-default streams.
- Seal order: PASS, `WRITE_STOPPED` strictly newest.
- Verdict: `FAIL_TO_SA2`.
