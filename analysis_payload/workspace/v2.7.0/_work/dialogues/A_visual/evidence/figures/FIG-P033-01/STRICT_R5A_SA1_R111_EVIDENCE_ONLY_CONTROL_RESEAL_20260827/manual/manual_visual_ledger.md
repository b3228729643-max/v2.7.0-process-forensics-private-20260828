# FIG-P033-01 R111 fresh isolated SA1 manual visual ledger

- HANDOFF_ID: `A-R111-P033-SA1-FRESH-ISOLATED-20260827`
- canonical task: `/root/p033_r111_fresh_sa1`
- model_effort: `gpt-5.6-sol/xhigh`
- review order honored: machine artifacts were completed and the denominator/pairs frozen before this ledger was written. The reviewer then actually opened the final full-page 300 dpi render, native1x body+caption crop, semantic overlay, native1x ROI sheet, nearest8x ROI sheet, all seven individual nearest8x ROIs, and the final 300 dpi grayscale crop.

## Frozen denominator and coverage

- Final N = 99 atomic visible PDF objects: 85 nonempty glyphs, 5 lines, 2 rectangles, and 7 curves.
- Final C(N,2) = 4,851 unordered pairs, fully enumerated in `machine/all_unordered_pairs.csv`.
- 4,770 pairs are closed by frozen machine dispositions (separated bbox, same text-run atoms, compound path atoms, or explicit support-background inclusion).
- 81 pairs required manual native-pixel review and are individually resolved in `manual/manual_pair_resolution.md`.
- Unresolved pairs: 0. Canonical illegal overlap pixels: 0.

## Actual-open observations

1. Full page integration: physical page 29 / printed page 16 visibly contains Figure 2.1 in the expected chapter context. The figure is centered, has normal whitespace, a complete caption, and no page-edge clipping or collision with surrounding prose.
2. Missing/tofu/codepoints: all eight frozen text groups match their expected Unicode strings exactly; all 85 glyph atoms have nonempty 300 dpi raster ink. In the opened native and 8x views, no tofu box, wrong codepoint, missing label, or broken mathematical symbol is visible.
3. Equation note: `||x||^2 = ||p||^2 + ||r||^2` is complete and centered inside its rounded box. The superscripts, double bars, and variables are intact; the visible border does not touch the ink.
4. Apex X: the blue x arrow and dashed gray residual share the endpoint X as required. Their arrowheads remain directionally distinct. This is intentional topology, not an illegal collision.
5. Residual label: `r=x-p in S-perp` is complete and offset to the right of the dashed residual. The white support background and the brace do not obscure any glyph.
6. Projection point P: the teal p vector, dashed residual, right-angle certificate, and distance construction meet/co-locate at P as required by the projection geometry. The native pixels preserve separate strokes and a readable orthogonality cue.
7. Distance annotation: `最短距离` remains readable. The white label support prevents the slanted plane boundary from crossing the glyph ink; the brace is visually distinct.
8. Projection and subspace labels: `p=P_S x in S`, `x`, and `子空间 S` are all complete and separated from the active strokes. No real foreground-on-glyph overlap appears despite broad slanted-path bboxes.
9. Caption: `图 2.1` and the full caption sentence are complete, single-line, uncut, and consistent with the source and adjacent V1-C02 prose.
10. Grayscale: x, p, residual dashes, plane band, brace, right-angle marker, labels, and equation remain distinguishable by line style/structure, not color alone.

## Geometry and mathematical semantics

- Source coordinates are O=(0,0), P=(3.2,0.8), X=(2.7,2.8), hence r=X-P=(-0.5,2.0).
- `P dot r = 3.2*(-0.5)+0.8*2 = 0`, so the displayed right angle is correct.
- `||x||^2=15.13`, `||p||^2=10.88`, `||r||^2=4.25`, and `15.13-(10.88+4.25)=0`.
- O->P is p in S, P->X is r=x-p in S-perp, and O->X is x. The caption's shortest-distance statement follows from the orthogonal residual and agrees with the necessary V1-C02 text.

## R168 hard/advisory decision

- Hard failures: none. No missing/tofu/wrong codepoint, wrong mathematics, unreadable or obviously unbalanced element, clipping, illegal overlap, or geometry/semantic error was found.
- Advisory only: local source declarations of 9.2 pt and 9.4 pt are below the older 9.5 pt target, but the opened 300 dpi native and nearest8x views are actually readable and balanced. Under the supplied R168 policy this is not a hard FAIL.
- Manual hard-gate result: PASS.
- Authorized route: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3` only. This ledger does not claim local pass, final pass, or SA3 completion.
