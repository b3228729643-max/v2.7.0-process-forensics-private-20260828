# Frozen denominator

- Target: R110 official PDF physical page 632, printed page 619, Figure 31.7.
- Included region: complete visible Figure 31.7 body plus its two-line caption; surrounding prose and Figure 31.8 are excluded by semantic ownership and disjoint vertical bands.
- Visible non-empty denominator: `N=156` objects = `139 GLYPH + 17 DRAWING/PATH`.
- PDF formula-rule reconciliation: `MATH_RULE=0`; no visible overline, underline, radical rule, fraction rule, cancellation slash, or accent path occurs in this figure/caption. The visible `1/3` slashes, arrows, equals sign, parentheses, superscript, and subscripts are PDF text glyphs and are counted in the 139-glyph denominator.
- Drawing/path denominator: x/y tick groups, x/y axis lines and arrowheads, ycomb stems, running-mean curve, truth reference line, four square sample markers, and four circular mean markers; all 17 are non-empty and have individual replayed vector masks.
- Complete unordered-pair denominator: `C(156,2)=12,090`; every pair has exactly one row in `after_overlap_report.csv` and `unordered_pairs.json`.
- Filename mapping: `G0001..G0139` and `D0001..D0017`; exactly 156 ordinary `.png` mask files exist, with no colon-containing path, ADS, duplicate ID, or safe-name collision.

Freeze status: `DENOMINATOR_FROZEN=true`.
