# FIG-P445-01 strict SA1 R1 — final-PDF visual acceptance

RESULT: **FAIL**

## Frozen input and location

- Frozen input: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`
- Final-PDF physical page: **485**; printed page: **472**; figure: **图 25.1**.
- The page was re-located from the frozen final PDF by the unique caption phrase `树的纵坐标表示合并高度`. The task card's legacy physical-page value was not used as evidence.
- Render: native 300 dpi `2481×3508` px, then cropped only (never resized). Source and adjacent-body reading record: `source_and_adjacent_context_read.md`.

## Required decision matrix

```text
SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = false
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 90
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0.000
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true
READING_ORDER_PASS = false
FIGURE_EDGE_CLEARANCE_PASS = true
```

## Hard-gate findings

- Source-font failures: **28/69** reader-visible glyph elements. The explicit 9.4pt axis/leaf text, 8.6pt ticks, and 9.2pt cut annotation are below 9.5pt. Natural scripts inherited from a 9.4pt or 9.2pt parent also fail because their parent formula is below 9.5pt. See `after_font_audit.csv`.
- Pixel-height failures: **8/69**. Every element was measured as an independent final-PDF glyph mask; operators and punctuation are separate elements rather than being hidden by a parent formula bbox. See `after_pixel_measurements.csv`.
- Illegal checked pairs: **5**; unioned illegal foreground overlap: **90px**. The all-object pair ledger keeps intentional tree/cut-line connections distinct from text collisions.
- Exact minimum clearances: text--text **0.000px** (threshold 4px); text--line/arrow **0.000px** (threshold 3px); text--node-border **1.000px** (threshold 5px). There is one panel, so the 8px cross-panel rule is not applicable rather than unknown.
- Clip audit: **0** independent objects touch a final-PDF edge. The native figure-crop minimum edge clearance is **34.000px** (>=6px pass); all object masks and vector bboxes are retained in `after_edge_clip_report.csv` / `vector_object_manifest.csv`.

## Four-view assessment

- `after_full_page_200dpi.png`: full-page layout is stable; figure, caption and following body remain on the page without crop.
- `after_full_page_300dpi.png`: native full-page source for every pixel measurement.
- `after_standalone_300dpi.png`: lossless native-300dpi final-PDF crop of the graphic alone; no scale-up/down is applied.
- `after_grayscale_300dpi.png`: cluster membership remains readable from tree topology and C1/C2/C3 labels; color is supplemental. This does not cure the failed font/collision gates.

## Mathematical, text, caption and page review

The displayed branch heights (0.65, 0.95, 2.10, 3.00) and the cut at `h_c=1.4` encode exactly the three classes stated immediately after the figure: `{x_1,x_2}`, `{x_3}`, and `{x_4,x_5}`. The source caption and adjacent prose agree with that reading. The caption is a single reading conclusion and the page itself is integrated cleanly. These semantic/content checks pass, but they cannot override typography or collision FAILs.

## Required SA2 repair scope

1. Raise every source-owned reader-facing baseline to at least 9.5pt **after all transforms**; this includes the 8.6pt ticks, 9.4pt axis/leaf labels and 9.2pt cut annotation. Do not use whole-figure downscaling.
2. Reposition or redesign the axis-title/tick area so all independent final foreground masks have at least 4px text--text clearance. Fix every failed pair listed in `after_overlap_report.csv`; do not treat tree-line intersections as a reason to retain a text collision.
3. Re-measure `h_c=1.4` as independent CJK, lowercase, subscript, equals, digit and decimal-punctuation substrings. A nominal 9.5pt change alone is insufficient if the `=` or punctuation pixels remain below their 22px gate.
4. Rebuild against a new final candidate PDF and regenerate all evidence. The next role is **SA2**, not SA3.
