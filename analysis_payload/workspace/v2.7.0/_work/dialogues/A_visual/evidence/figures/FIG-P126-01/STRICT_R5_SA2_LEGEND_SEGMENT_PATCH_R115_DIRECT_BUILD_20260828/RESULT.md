# FIG-P126-01 R5 local SA2 result

Verdict: `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`.

The unique R5 direct LuaLaTeX build completed naturally with one PDF, 33,952 bytes, SHA-256 `58BA180DBC92ED6DFEECCA2D77FE021C55B9D9B5DE0A1F6DB5F4B8D7316CAD06`, and the build slot was released with terminal TeX-family counts zero.

The current PDF was reviewed from scratch after build. The final reader-visible denominator is N=15 semantic objects, partitioning all 58 extracted raw primitives exactly once; all unordered semantic pairs C=105 and raw pairs C=1,653 are closed. Manual ledgers cover 15 objects, 105 pairs, 18 opened views, 10 math/semantic checks, and 25 extracted glyph/codepoint checks.

One hard defect remains: `HARD-LEGEND-X2-SEGMENTS-COLLAPSE`. At native 300 dpi, the x1 and x2 legend samples both form continuous 73-pixel runs. The x2 sample has zero internal blank runs in color and grayscale, so the intended four disconnected segments and grayscale role distinction are absent. The actual plotted horizontal and vertical coordinate-update paths, quadratic geometry, markers, labels, glyphs, caption semantics, clipping, and page integration otherwise pass.

No source edit, commit, fresh role, second UID, or additional TeX run followed the released R5 build.
