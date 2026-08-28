# FIG-P598-01 fresh isolated SA1 visual acceptance

- HANDOFF_ID: `A-R104-P598-01-SA1-FRESH-20260825`
- Instance: `/root/p598_01_r104_fresh_sa1`
- Reviewer UID: `SA1_FRESH_gpt-5.6-sol_xhigh`
- Model / effort: `gpt-5.6-sol / xhigh`
- Frozen PDF: `main_full.pdf`, SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`, 4,967,222 bytes, 817 pages
- Target: physical page 649; A4 MediaBox 595.276 x 841.890 pt
- R168 verdict: `PASS`
- Route: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`

## Independent extraction and denominator

The page was independently rendered at native 300 dpi (2481 x 3508 px) and as a 200 dpi whole-page context view (1654 x 2339 px). The complete figure crop is page-pixel box `(250,2054,2180,2760)`, width 1930 px and height 706 px. A tighter standalone content box `(408,2058,2010,2625)` was also inspected. The complete visible denominator is 142 non-space glyphs plus 22 visible foreground graphics, `N=164`. Four white double-border separator paths are auxiliary occlusion paths and were separately adjudicated as OCC001-OCC004; they are not visible-foreground denominator objects.

All `C(164,2)=13,366` unordered visible-object pairs were measured. There are 17 raw intersecting pairs, all manually observed as intentional structural joins (axis-line/arrowhead, transition-line/node, transition-line/arrowhead, arrowhead/target-node, and relation-arc/node). Illegal overlap count is therefore zero.

`OVERLAP_PIXEL_COUNT=0` (illegal overlaps only).  
`RAW_STRUCTURAL_OVERLAP_PAIR_COUNT=17`.  
`CLIP_PIXEL_COUNT=0`.  
`FONT_VISUAL_HARMONY_PASS=true`.

## Geometry and continuity hard gates

All 17 critical clearances were inspected in their per-ID overlays. Their measured clearances are 20.4709-27.0179 px for state-glyph/border relationships, 8.4340-8.8489 px for the two time-label/repeat-arc relationships, 43.0454 px for repeat annotation/arc, 39.0000 px for keep-b/transition, 39.8167 and 88.0000 px for kernel formula/transition and formula/arrowhead, 35.0000 px for keep-c/transition, 55.0000 px for bottom note/axis, and 15.4924 and 12.6015 px for axis-title/axis and axis-title/arrowhead. Every critical intersection is zero and every clearance exceeds its numeric gate.

All six directed transition endpoints were inspected at native scale and 8x. Four have intersecting or adjacent core masks. The last two have core-mask clearances 1.8284 and 2.6056 px, but the original raster visibly contains the expected low-contrast antialias bridge; neither presents a visible discontinuity. Every source-border/line and line/arrowhead connection is continuous.

The minimum crop-edge clearance is 9 px, belonging to the lowest caption glyph; no text, circle, arrow, axis, or annotation is clipped. Whole-page context and grayscale inspection show clean integration, adequate surrounding whitespace, and no neighboring-body collision.

## Semantic hard gates

- The seven displayed states are exactly `a,b,b,c,c,b,a` at `t=0,1,2,3,4,5,T`.
- Six left-to-right transition arrows connect all consecutive displayed times; the horizontal time axis and its arrowhead are continuous.
- The displayed kernel is `K(x_t, d x_{t+1})`, with correct subscripts and differential `d`. The caption's `K(x,dy)` semantics correctly describe positive transition probability mass near `y` conditional on current state `x`.
- Consecutive repeated states `b,b` and `c,c` are visually explicit. Their four repeated-state nodes have clean double-circle borders; the explanatory arc/note correctly conveys adjacent correlation from repeated states. The caption's state-space self-transition wording is consistent with consecutive equal sampled states, even though the temporal path uses distinct time-indexed nodes.
- Exact vector centers give six time increments of approximately 53.85898 pt; their range is only 0.000435 pt. Equal time spacing passes.

## Typography under R168

Machine extraction found zero empty glyph masks and zero replacement/tofu code points. Per-ID contact-sheet review found no missing stroke, foreign pixel, wrong glyph/codepoint, wrong math semantics, unreadability, severe visible imbalance, clipping, or text/graphic collision. The source uses 9.2 pt for the top style, 9.4 pt for state labels, and 8.6 pt for annotations and formulas; these values and legacy pixel-height/taxonomy comparisons are advisory under R168, not hard gates. The 4 px-high CJK glyph `一` (G0078) is a complete intended single horizontal stroke, not clipping or loss. All punctuation and natural subscripts remain legible.

## Manual observation record

The reviewer visually opened every one of the 12 glyph sheets, 6 graphic sheets, the 4-cell occlusion sheet, 17 critical overlays, 17 raw-relationship overlays, 6 endpoint overlays, and the 7 global overlays/matrices, in addition to the 4 base page/crop/grayscale views. `manual_view_ledger.csv` records 70 opened final visuals. `manual_element_adjudication.csv` contains 168 human-authored per-ID rows (142 glyphs, 22 visible graphics, 4 auxiliary occlusion paths); no script authored or overwrote reviewer, boolean, decision, or note fields.

No R168 hard failure is present. Final SA1 decision: `PASS`; next route: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`. This is not `A_LOCAL_PASS` and does not constitute central acceptance.

The evidence package is closed by one final seal operation. `SEALED_MANIFEST.sha256` and `SEALED_MANIFEST.json` are complete dual listings of every non-self-referential evidence file plus the external report and handoff; `WRITE_STOPPED` is created after both manifests and is required to have the strictly latest modification time. Seal completion makes all evidence, report, and handoff files read-only; no post-seal writes are permitted.
