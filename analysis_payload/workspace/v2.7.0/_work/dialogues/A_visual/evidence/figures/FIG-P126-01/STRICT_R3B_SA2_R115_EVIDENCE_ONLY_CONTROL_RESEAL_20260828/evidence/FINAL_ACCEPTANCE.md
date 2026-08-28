# P126 R3A non-TeX final acceptance

Verdict: `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`.

The frozen denominator is N=14 reader-visible logical objects and C=91 all unordered pairs. Raw mapping covers 58 visible atoms exactly once (25 characters, 9 lines, 20 curves and 4 rectangles). Machine candidates are 33. Manual ledgers were written only after the final color, grayscale, object, candidate and critical native1x/nearest8x evidence was actually opened; no script generated or overwrote reviewer, decision, hard-defect or note fields.

All geometry, clipping, glyph/codepoint, coordinate-descent mathematics, caption/chapter semantics and page-integration checks pass except one unique hard defect: `HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE`. The `更新 x_2` legend swatch is expected to be dashed but renders as one continuous solid horizontal run. The `更新 x_1` sample is also continuous, so the two roles cannot be distinguished by the promised solid-versus-multi-dash encoding in grayscale. Native1x, nearest8x and objective pixel-run evidence agree.

This failure is not a small font, contour or 1--2px advisory. No source change, additional TeX call or commit was performed after the successful R3A build. Main must decide any subsequent source scope.

