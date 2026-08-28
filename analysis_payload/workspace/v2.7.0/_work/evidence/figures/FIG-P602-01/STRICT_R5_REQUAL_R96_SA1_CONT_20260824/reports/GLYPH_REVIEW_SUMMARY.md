# R5 SA1 glyph evidence — FIG-P602-01

Canonical evidence directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.

The frozen input is physical page 651 of `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r96_fullbook\main_full.pdf`, directly rasterized at native 300 dpi.  This review used no earlier FIG-P602-01 pass material.

## Coverage and manual evidence

`glyph_map.csv` has 175 unique non-space glyphs.  The completed `glyph_reviewer_ledger.csv` has exactly 175 rows and no pending decision.  It links every glyph to a native 1x original, native 1x target-overlay, raw mask, and one of 20 O/T/M 8x-nearest contact sheets.  `after_text_measurement_overlay_300dpi.png` gives the full-figure placement check.  All 20 sheets were manually reviewed as original / target overlay / mask only; every ledger row records that review separately from the pixel-floor verdict.

- Ledger PASS: 152 glyphs.
- Ledger FAIL: 23 glyphs.
- Mandatory raw-ink floor failures: 10 glyphs.
- Raw peer-bbox mask-purity failures: 15 glyphs.
- Two accents, GLYPH-051 and GLYPH-062, appear in both failure sets; the union is therefore 23, not 25.

## Mandatory raw 300 dpi floor failures

| Glyph | Codepoint | Raw ink height | Mandatory floor |
|---|---:|---:|---:|
| GLYPH-007 `=` | U+003D | 12 px | 22 px |
| GLYPH-014 `⋅` | U+22C5 | 5 px | 22 px |
| GLYPH-021 `=` | U+003D | 12 px | 22 px |
| GLYPH-044 `=` | U+003D | 14 px | 22 px |
| GLYPH-051 `˜` | U+02DC | 6 px | 22 px |
| GLYPH-062 `˜` | U+02DC | 6 px | 22 px |
| GLYPH-077 `∼` | U+223C | 9 px | 22 px |
| GLYPH-104 `=` | U+003D | 12 px | 22 px |
| GLYPH-118 `=` | U+003D | 12 px | 22 px |
| GLYPH-160 `一` | U+4E00 | 5 px | 30 px |

These are direct final-PDF observations.  They are not remediated, rounded up, or waived by source point size, optical appearance, low-profile punctuation calibration, or nearest-neighbor enlargement.

## Mask-purity failures

The raw target mask overlaps peer-glyph foreground in the following 15 rows: GLYPH-028, 029, 051, 052, 053, 054, 057, 058, 062, 063, 064, 120, 121, 145, and 146.  The exact foreign-pixel counts are retained in `glyph_map.csv`, `after_pixel_measurements.csv`, and the reviewer ledger.  This is reported as a separate mask-ownership failure even where the glyph itself has an adequate ink height.

## Low-profile punctuation is independently closed

`calibration/low_profile_calibration.csv` and its native calibration PDF/raster compare the same codepoint, font/weight, color, and effective size for en dash, dunhao, full-width colon, full stop, math comma, and caption dot.  All six comparisons pass.  That result validates the six low-profile contexts only; it does not apply to `=`, `⋅`, `∼`, `˜`, or the CJK stroke `一` above.

## Gate conclusion

The source-font declaration gate passes, but the strict final-PDF glyph gate fails because of the 10 hard-floor failures and 15 impurity failures.  This is the sole blocking class for the R5 terminal outcome.
