# FIG-P583-01 — R103 R168 fresh isolated SA1 visual acceptance

- Reviewer UID: `/root/p583_r103_fresh_sa1`
- HANDOFF_ID: `A-R103-P583-SA1-FRESH-20260825`
- Model/effort: `gpt-5.6-sol/xhigh`
- Official candidate: `main_full.pdf`, R103, physical page 633
- Frozen identity: 817 pages, A4 595.276×841.890 pt, 4,967,184 bytes, SHA-256 `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`

## Render identity

- Native 300 dpi full page: 2481×3508 px.
- Native 200 dpi full page: 1654×2339 px.
- Figure crop: page-pixel rect `[250,250,2180,1055]`, 1930×805 px.
- Chart-body standalone: page-pixel rect `[570,250,1842,913]`, 1272×663 px.
- Measurement views came directly from the frozen PDF at 300 dpi and received integer cropping only; no resizing was used for counts.
- TeX source was read only. No TeX engine was invoked.

## Object and pair closure

- 71 visible glyph objects (`G001`–`G071`) and 19 final-visible graphic objects (`P001`–`P019`): `N=90`.
- Complete unordered-pair denominator: `C(90,2)=4005`; actual pair rows: 4005.
- 18 critical hard-gated pairs: five annotation-to-triangle pairs and thirteen node-text-to-border pairs. All 1×/8× evidence and three critical contact sheets were actually opened.
- Path reconciliation: 10 figure-body PDF drawing groups mapped; 19 foreground graphic objects, two white background/occluder roles, zero unassigned visible paths.
- Path-based math rules: zero; `O(N^{-1/2})` is fully represented in the PDF character stream.

## Hard geometry result

- `OVERLAP_PIXEL_COUNT=0` for illegal independent-object relations.
- `CLIP_PIXEL_COUNT=0`.
- Independent text–text minimum bbox clearance: 33.242 px (threshold 4 px).
- Text/formula–line/marker minimum raw-mask clearance: 5 px (threshold 3 px).
- Node text–final-visible border minimum raw-mask clearance: 13 px (threshold 5 px).
- Text to chart crop edge minimum: 20 px (threshold 6 px).
- Twenty-one nonzero intersections are fully accounted as design geometry: 16 same-parent formula/axis-system pairs, four coordinate-system connections, and the one curve–rate-triangle construction pair. The curve–triangle pair has 36 shared final pixels on the intended `×4/÷2` construction and is not an illegal collision.

## Glyph and graphic manual review

- All nine glyph contact sheets and all three graphic contact sheets were opened at original evidence resolution.
- Glyph manual ledger: 71/71 unique IDs, `original_match=true`, `overlay_complete=true`, `mask_only_pure=true`, missing-stroke=0, foreign-pixel=0, decision PASS.
- Graphic manual ledger: 19/19 unique IDs with the same closure and decision PASS.
- The gold triangle and the nearby gold annotation were separated by PDF drawing geometry. G045–G049 have 5–8 px final-visible clearance to P018; no triangle pixels remain in glyph masks and no annotation pixels enter the triangle mask.

## R168 typography disposition

- Source declarations: ticks 8.6 pt; default/triangle note/condition node 9.2 pt; axis labels and rate formula 9.6 pt; no scale/resize transform.
- Those sub-9.5 pt declarations are advisory under the instructed R168 rule because the actual page and native 300 dpi views remain clear and balanced.
- Three pixel-reference outliers are also advisory only: G035 superscript minus `−` has a complete low-profile 7 px rule; rotated `S` (G070) is 19 px and `E` (G071) is 23 px. All are correct codepoints, complete, unambiguous and readily readable.
- Axis-title and natural-script within-role ratio flags arise from intrinsic glyph-outline/taxonomy differences, not font scaling or visible imbalance.
- No tofu, missing glyph, wrong codepoint, mathematical glyph error, actual unreadability, serious visual imbalance, clipping or overlap was observed.
- `FONT_VISUAL_HARMONY_PASS=true`.

## Semantics, grayscale and page fusion

- Curve and label consistently express `O(N^{-1/2})` on log-log axes.
- The triangle correctly encodes sample size `×4` and RMSE approximately `÷2` from `(16,1/4)` to `(64,1/8)`.
- Applicability condition `iid 且方差有限` matches the caption; the caption correctly warns that correlated samples or infinite variance cannot directly reuse the line.
- Axis titles, tick values, object content and caption agree.
- Grayscale preserves curve/triangle/condition-box distinction and readability.
- The 200 dpi whole-page view shows natural page integration with the caption and the following example; no collision, crop or hierarchy break.

## Manual booleans and verdict

- `GLYPH_MAPPING_PASS=true`
- `GRAPHIC_MAPPING_PASS=true`
- `OVERLAP_CLEARANCE_PASS=true`
- `FONT_VISUAL_HARMONY_PASS=true`
- `SEMANTICS_PASS=true`
- `GRAYSCALE_PASS=true`
- `PAGE_FUSION_PASS=true`
- `CAPTION_OBJECT_MATCH_PASS=true`
- `MACHINE_FINAL_CROSSCHECK=PASS`

Final fresh isolated SA1 verdict: **PASS**.

Route: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`. This review does not start SA3 and does not write `A_LOCAL_PASS`, central inventory or central state.
