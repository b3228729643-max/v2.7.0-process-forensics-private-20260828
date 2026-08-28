# Manual review scope and method

Reviewer route: `SA2 = gpt-5.6-sol / max`.

Actual opened work:

- 16 glyph contact sheets, every cell, yielding 95 distinct glyph decisions.
- 21 graphic objects, each with native 1x and 8x nearest-neighbor original/overlay/mask triples.
- 50 critical pair directories, each with `bundle_1x.png` and `bundle_8x_nearest.png`; red/blue objects and nearest contours were judged independently of the machine adjudication field.
- 5 view artifacts: standalone 300 dpi, grayscale 300 dpi, full page 200 dpi, figure crop 300 dpi, and measurement overlay 300 dpi.
- Current source lines 1-52 for 3 semantic decisions, plus numeric source/object evidence for 8 D/E, 5 hierarchy, and 16 ratio decisions.

Decision inventory: `95 + 21 + 50 + 5 + 3 + 8 + 5 + 16 = 203` unique human decisions. Each row was written explicitly with `apply_patch`. No script generated or modified `REVIEWER`, `DECISION`, `NOTE`, `OPENED`, or human pixel fields.

