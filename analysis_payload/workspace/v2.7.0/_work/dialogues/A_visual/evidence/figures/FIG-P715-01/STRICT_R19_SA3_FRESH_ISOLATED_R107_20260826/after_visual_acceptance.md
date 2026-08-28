# Manual visual acceptance

After the final machine artifacts were fixed, I actually opened and inspected four final views, all eight glyph contact sheets, both drawing contact sheets, and all eight critical relationship images. I then authored the row-level ledgers by hand. The ledgers contain 255 unique glyph decisions, 43 unique drawing/path decisions, 8 relationship decisions, and 22 view/sheet/relation decisions. All rows are PASS; missing-stroke and foreign-pixel totals are zero.

## Human observations

- Full-page integration is natural on physical PDF page 765 / printed page 752, with no abnormal whitespace, page break, header conflict, or surrounding-text collision.
- The standalone figure has two balanced panels. Titles, graph, matrices, formulas, focus frames, and caption are readable at the native render and remain coherent in grayscale.
- All four arrows have correct orientation, clear endpoints, and no accidental crossing or node penetration.
- Every matrix entry matches the declared row/column order and its focus rectangle. Shared cell borders are geometrically aligned.
- The figure and caption are wholly contained by their crops. The standalone body crop retains every body object. Four-side masks show continuous panel and matrix borders.
- No clipping, illegal overlap, tofu, wrong codepoint, missing stroke, unreadable item, severe imbalance, or wrong mathematical meaning is visible.

## R168 handling

Font metadata, the advisory `[0.92,1.08]` peer ratio window, taxonomy, micro-font observations, and 1–2 px antialiasing differences were used as diagnostic context only. The two CJK glyphs `一` and low-profile punctuation/operators naturally have short ink boxes; direct review shows complete intended strokes. All explicit source sizes are at least 9.5 pt at graphics scale 1.0; the inherited caption is a 9.963 pt PDF vector span. Matrix and node text is 10.2 pt, titles 10.4 pt, and formulas 12.0 pt. No hard R168 failure condition is present.

`SOURCE_FONT_PASS=true`  
`PIXEL_HEIGHT_PASS=true`  
`SAME_CLASS_RATIO_PASS=true`  
`ROLE_RATIO_PASS=true`  
`TEXT_CONSISTENCY_PASS=true`  
`VISUAL_HARMONY_PASS=true`  
`GRAYSCALE_PASS=true`  
`PAGE_INTEGRATION_PASS=true`  
`FOUR_SIDE_CLIP_PASS=true`  
`OBJECT_CONTENT_PASS=true`
