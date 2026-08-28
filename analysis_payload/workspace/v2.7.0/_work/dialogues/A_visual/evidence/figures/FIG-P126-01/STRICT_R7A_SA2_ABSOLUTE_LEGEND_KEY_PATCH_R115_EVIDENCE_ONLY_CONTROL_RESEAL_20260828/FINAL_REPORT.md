# FIG-P126-01 R7 local SA2 report

Verdict: `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`.

## Frozen input and build

- HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R7-20260828`
- PDF: `build/v260_FIG-P126-01_standalone.pdf`
- PDF identity: 33,952 bytes; SHA-256 `8EB275DEB382AD25E26C19F4B9A0EFBE01771317FE7DE475C5F2E330BCD789D6`
- Build controller/direct child: 1/1, natural exit0/0; retry/latexmk/version-probe/second invocation all0.
- Source stayed 4,366 bytes/SHA `20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279`; wrapper/controller/engine also stayed byte-identical.
- No TeX invocation occurred after build-slot release.

## Fresh denominator and all pairs

The reader-visible atomic denominator was independently frozen from this R7 PDF as 25 glyphs, 9 lines, 4 rectangles and 20 curves: `N=58`. `MACHINE_ALL_PAIRS.csv` enumerates every unordered pair exactly once: `C=1,653`. Pair IDs and tuples are unique; no self-pair or bad reference exists. The machine candidate set contains 179 pairs. Post-observation manual object review covers 58/58 objects, and the manual pair-class ledger partitions all 1,653 pairs as 1,474 noncandidates, 175 lawful candidates, and four confirmed illegal relations.

## Confirmed hard defects

1. `HARD-LEGEND-X2-CONTINUOUS`: C020, the x2 legend sample, is a single continuous 73-pixel run in both color and grayscale with zero internal blank. It is visually the same topology as the solid x1 sample C019, despite the source requesting four separated segments. The absolute key patch therefore did not change the rendered handler.
2. `HARD-LABEL6-AXIS-CONTOUR-OVERLAP`: pair P00494 (G010-L002) and pair P00510 (G010-C005) are genuine visible-ink overlaps. The vertical x2 axis and a gray contour pass through numeral 6.
3. `HARD-LABEL7-MARKER-ARROW-OCCLUSION`: pair P00560 (G011-C008) and pair P00568 (G011-C016) are genuine visible-ink occlusions. The numeral 7 is materially covered by the blue arrowhead and blue filled node and is not presented as a complete reader-visible glyph.

These are not R168 legacy font-size or micro-raster advisories. Color, grayscale, native1x and nearest8x evidence agree.

## Regression checks

- No clipping, tofu, missing codepoint, unresolved reference or page-boundary failure was found.
- The Hessian `[[1,1],[1,2]]` is positive definite: determinant1, eigenvalues0.381966 and2.618034.
- q0--q7 alternate x2/x1 updates; every updated-coordinate derivative residual is zero.
- Objective values `2.92, 2.56, 1.28, .64, .32, .16, .08, .04` strictly decrease.
- The four contours share the same rotated quadratic, the star remains the true optimum, the last point remains an approximation, and the caption semantics agree with the trajectory.
- Page placement and overall figure balance pass. The legend topology and numerals6/7 do not.

No source edit, commit, fresh role, second UID or second build was performed. This root requests Main to decide the narrowest single-source correction scope; it does not self-authorize a patch.
