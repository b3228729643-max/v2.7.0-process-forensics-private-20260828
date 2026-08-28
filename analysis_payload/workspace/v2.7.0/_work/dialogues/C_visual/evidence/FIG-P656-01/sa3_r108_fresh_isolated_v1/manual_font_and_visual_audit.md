# Manual source-font and visual audit

## Source-level effective TeX sizes

The sole source has no `scale=`, `transform shape`, `resizebox`, or `scalebox` operation. The `tikzpicture` inherits `slfig-FIG-P656-01` at `9.5pt`, and `every node` repeats the same `9.5pt` declaration. Therefore cumulative graphics scale is `1.0`.

- General internal text, token numerals, formulas, arrow label, warning, and coefficient node: declared/effective `9.5 TeX pt`.
- Left-group title: declared/effective `9.9 TeX pt`.
- Caption: inherited rather than declared locally; the official PDF reports `9.96 PDF bp`, which converts to about `9.997 TeX pt` using `TeX pt = PDF bp * 72.27/72`.

The apparent `9.46` value reported for most figure text by PDF extraction is PDF big points, not a failure of the `9.5 TeX pt` source declaration: `9.46 bp * 72.27/72 = 9.495 TeX pt` after normal rounding.

Natural math subscripts and lower limits are reported at `6.63 PDF bp` (about `6.655 TeX pt`). They are naturally derived from a `9.5 TeX pt` base formula and are not evidence that the whole formula was forced into script style.

## Native 300 dpi ink measurements

All 37 independently tracked font runs meet their applicable protocol floor:

- CJK runs: minimum observed ink height `32 px` against a `30 px` floor.
- Token digits: observed `26-29 px` against a `24 px` floor.
- Base mathematics: observed composite/base heights `38-47 px` against a `22 px` floor.
- Natural scripts/limits: observed `19-23 px` against a `15 px` floor.
- Caption: observed `35-39 px` against a `30 px` floor.

The three category-2 numerals were measured with neutral-dark color separation so teal hatch pixels were not counted as black glyph ink. Independent masks confirm readable `2` glyphs at native scale and in nearest-neighbor 8x views.

## Ratio and R168 treatment

All token labels have exactly the same `9.5 TeX pt` source/effective size and are visually balanced. Their measured digit ink heights range from `26` to `29 px`; the raw max/min ratio `29/26 = 1.115` is driven by glyph outline and the color-separation boundary around patterned peers. The two caption-line ink boxes differ as `39/35 = 1.114` although the PDF font size is identical. Under user R168 these raster/outline/peer-taxonomy differences are advisory and cannot fail by themselves. Native and 8x inspection shows no conspicuous size imbalance, unreadability, wrong codepoint, missing glyph, or semantic distortion.

Role hierarchy is also stable: the title is deliberately bold and only `9.9/9.5 = 1.042` by source size; ordinary node labels, formulas, arrow label, and warning all share the same `9.5pt` base. No ordinary element visually overwhelms the token grid or the left-to-right flow.

## Overlap, containment, and clearance

- Complete all-pair denominator: `C(50,2)=1,225`; every pair has one unique record.
- Separate-pair candidate overlap: `0` pixels.
- Manual/unresolved candidate clusters: none.
- Canonical true illegal overlap: `0` pixels.
- Mask contamination count: `0` pixels after color-separated digit/hatch masks.
- Canonical minimum relevant text clearance: `7 px`, between the coefficient label and its formula; required text-text minimum is `4 px`.
- Minimum token-label to true circle-boundary clearance: `13.892 px`; required node-border minimum is `5 px`.
- Count formula to count-box boundary: `36 px`; warning text to warning boundary: `11 px`; coefficient label/formula to coefficient boundary: `19/18 px`.
- Arrow label to arrow: `20 px`; required text-line minimum is `3 px`.
- Rendered arrow attachment gaps are `8 px` at the left arrow tip, `2 px` at the right arrow tail, and `7 px` at the right arrow tip. The source explicitly attaches those paths to node anchors, and the native/8x views show unambiguous intended attachment. They are not illegal text/graphic clearances.
- Foreground pixels on the figure+caption crop boundary: `0`; clipping count: `0`.

The one-pixel proximity between category-2 digit ink and internal hatch texture is a legal node-fill texture relation, not contact with the circle boundary. It remains readable and, under R168, cannot become a hard failure merely from a 1-2 px raster detail.

Manual font/visual result: `CLEAR`.
