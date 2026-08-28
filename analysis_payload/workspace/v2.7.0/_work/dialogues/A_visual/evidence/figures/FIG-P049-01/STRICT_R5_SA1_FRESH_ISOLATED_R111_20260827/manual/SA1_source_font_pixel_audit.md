# SA1 source-font and native-pixel audit

Reviewer: SA1, after opening the final full page, native 300-dpi ROI, grayscale ROI, nearest-neighbor 8x ROI, all-glyph sheet, and all-path sheet.

## Source audit

| Visible role | Source declaration | Scale | Effective TeX pt | R111 PDF size evidence | Manual R168 decision |
|---|---|---:|---:|---:|---|
| Axis labels, contour labels, point label, gradient label, tangent label | `\fontsize{9.4pt}{11.2pt}`; source lines 5-8, 17-20, 40-60 | 1.0 | 9.4 | about 9.36488 PDF points | Advisory 0.1 pt below legacy 9.5 threshold; actually crisp/readable and balanced, so no R168 hard failure |
| Three numbered notes | `\fontsize{9.2pt}{11.2pt}`; source lines 9-12, 67-72 | 1.0 | 9.2 | about 9.16563 PDF points | Advisory 0.3 pt below legacy threshold; Chinese ink is about 34 px high at native 300 dpi and is plainly readable |
| Ordering, increase label, function formula | `\fontsize{9.2pt}{11.0pt}`; source lines 46-47, 62-65, 76-78 | 1.0 | 9.2 | about 9.16563 PDF points | Advisory only under R168; no unreadability or imbalance |
| Caption | document caption style; source line 81 | 1.0 | rendered about 10.0 | about 9.96264 PDF points | Pass; full caption and bold figure number are intact |
| Tick labels | `\fontsize{8.8pt}{10.4pt}`; source line 18 | 1.0 | not applicable | no visible tick-label glyphs | `xtick=\empty, ytick=\empty` on line 29, so this style contributes no visible denominator element |
| Natural math scripts | derived from the 9.2/9.4 pt bases | 1.0 | about 6.4-6.6 | 6.41590-6.55537 PDF points | Pass; machine ink heights are 13-26 px, with the relevant numeral/letter scripts at or above 15 px except punctuation-like strokes; no script is missing or unreadable |

There is no `resizebox`, `scalebox`, `transform shape`, or other text-scaling wrapper. Axis coordinate mapping changes geometry, not text size.

## Native 300-dpi evidence

- All 135 nonempty visible glyph atoms have nonzero native-raster ink (`zero_ink=0`).
- Chinese body glyphs from the 9.2 pt note role measure about 34 ink pixels high.
- Caption Chinese glyphs have a median of about 37 px and maxima around 38 px.
- Main math glyphs at 9.2/9.4 pt have typical ink heights around 25-38 px depending on glyph shape; lowercase/x-height glyphs are around 19-26 px.
- The global raw minimum is 6 px and belongs to punctuation/minimal-stroke glyph shapes, not a missing or unreadable content glyph. Natural scripts are separately visible in the all-glyph inspection sheet.
- The nearest-neighbor 8x sheet shows normal antialias outlines, not raster loss, codepoint substitution, or tofu.

## Manual result

- `SOURCE_FONT_PASS=true` under the controlling R168 hard-gate interpretation.
- `PIXEL_HEIGHT_PASS=true` under R168: no actual unreadability.
- `SAME_CLASS_RATIO_PASS=true`: identical role declarations and consistent native appearance; no same-class drift or cross-panel issue (single panel).
- `ROLE_RATIO_PASS=true`: notes, math labels, axes, and caption form a coherent hierarchy without an obviously oversized or undersized role.
- Advisory only: the source-level 9.2/9.4 pt declarations are 0.1-0.3 pt below the earlier nominal 9.5 pt target. R168 explicitly makes tiny font/raster/outline differences advisory; this does not override any hard failure because none is present.
