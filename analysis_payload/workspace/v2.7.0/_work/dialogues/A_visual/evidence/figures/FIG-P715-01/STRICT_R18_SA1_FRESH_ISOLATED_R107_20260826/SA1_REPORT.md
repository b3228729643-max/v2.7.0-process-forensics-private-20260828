# FIG-P715-01 R107 R18 fresh isolated SA1 report

## Identity and locator

- Handoff: `A-R107-P715-SA1-FRESH-ISOLATED-20260826`.
- Reviewer route: `gpt-5.6-sol`, reasoning `xhigh`, one UID and one SA1 role only.
- The evidence root did not exist at launch and was created for this review.
- Frozen PDF: 817 pages, 4,967,249 bytes, SHA256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- Frozen source: 4,057 bytes, SHA256 `900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`.
- Independently located at physical page 765, printed page 752, Figure 36.2.
- Left title: `网页图、邻接矩阵与列归一`; right title: `行随机转置桥`.

No TeX engine was invoked, and the PDF, source, and main tree were not modified.

## Denominators and machine gates

The final visible-object denominator contains 216 individual PDF text glyphs and 43 foreground drawing/path objects, hence `N=259` and `C(N,2)=33,411`. Drawing objects comprise 2 panel borders, 3 node borders, 4 edge shafts, 4 arrowheads, 27 cell borders, and 3 focus borders. PDF character-stream and foreground drawing/path inventories were kept separately; no drawn math rule exists in this figure.

All 33,411 unordered pairs are present exactly once. Final machine candidates are 0 illegal overlaps and 0 clearance failures. All 259 masks are nonempty; clip count and tofu/decode candidate count are both 0. Sixteen critical pairs have final native 1× and 8× nearest-neighbour evidence. Intended nonzero intersections consist only of focus/cell overlays, matrix-grid joins, shaft/arrowhead joins, and four correct node-edge endpoint connections.

## Actual manual review

- Opened the source, `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`, and `after_text_measurement_overlay_300dpi.png`.
- Opened all 18 final glyph contact sheets and recorded 216 individual glyph rows. Each row has an original match, complete target overlay, pure mask-only view, 0 missing-stroke pixels, 0 foreign pixels, and an object-specific note.
- Opened all 4 graphic contact sheets and recorded 43 individual graphic rows. All panel/node/edge/arrow/matrix/focus masks are complete and pure.
- Opened both final critical-pair sheets and recorded all 16 critical relations individually. Every relation has 0 intersection pixels and clearance above its applicable threshold.
- Separately adjudicated all four node-edge boundary intersections as intentional and geometrically correct.
- Checked four directed edges, adjacency semantics, column normalization, transpose bridge, matrices `A`, `M`, `P`, panel borders on four sides, crop, grayscale, and page integration. No wrong mathematics, direction, label, entry, or relation was found.

## Typography under R168

Source declarations are 9.5 pt or larger for ordinary text, 10.2 pt for node/matrix text, 10.4 pt for titles, and 12 pt for formulas. Whole-page and crop observations show no actually unreadable text, tofu, wrong code, crowding, or severe imbalance. Small punctuation and scripts, extracted PDF rounding, pixel/taxonomy/peer ratios, font metadata, `[0.92,1.08]` comparisons, and 1–2 px raster differences were treated as advisory and did not independently determine the verdict.

`FONT_VISUAL_HARMONY_PASS = TRUE`.

## Result

Machine hard failures: 0. Manual hard failures: 0.

Verdict: `PASS`.

Callback: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.
