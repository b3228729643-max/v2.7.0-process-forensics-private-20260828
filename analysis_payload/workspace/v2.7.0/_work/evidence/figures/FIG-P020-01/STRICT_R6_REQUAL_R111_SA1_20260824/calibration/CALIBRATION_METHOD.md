# Low-profile punctuation calibration method

The seven low-profile glyphs are calibrated in `low_profile_punctuation_calibration.csv` against an independently visible or independently re-rendered glyph. Each row checks the required same codepoint, PDF font/weight, RGB color, effective point size (absolute delta at most `0.25pt`), native 300 dpi, raw `H_INK_PX`, and raw ink-area ratio.

- `、` uses a different visible `、` in the same final figure; the three instances are cyclically cross-referenced.
- `。` uses the other visible `。` in the same final figure.
- `.` uses the independently visible R95 physical-page-48 figure-caption dot, directly rendered at 300 dpi.
- `：` has no second same-color instance in R95. `colon_r95_form_rerender_calibrator.pdf` is a separate PDF Form-XObject render of the original R95 page-17 colon paint operation at the original coordinate and scale. Its raw dictionary independently verifies `U+FF1A`, `NotoSerifSC-ExtraLight`, color `7041664` / RGB `(107,114,128)`, and `9.96264pt`; the direct 300 dpi render has exactly the same `H_INK=22` and area `38` as F020_G053.

`colon_same_font_same_pt.tex` records an attempted local XeLaTeX equivalent. Its PDF driver rejected the installed variable CJK font, so it produced no valid PDF and is not used by any terminal metric. The final colon calibration above uses the frozen-R95 embedded font and actual R95 paint operation instead.
