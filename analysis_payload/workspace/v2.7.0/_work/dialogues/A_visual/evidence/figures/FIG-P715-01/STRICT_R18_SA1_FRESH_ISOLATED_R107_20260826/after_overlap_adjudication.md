# FIG-P715-01 overlap and clearance adjudication

The final denominator is `N=259` visible foreground objects: 216 text glyphs and 43 drawing/path objects. The complete unordered denominator is `C(N,2)=33,411`, present exactly once in `after_overlap_report.csv` and `machine/all_unordered_pairs.csv`.

Final machine results:

- illegal-overlap candidates: 0;
- clearance-failure candidates: 0;
- empty masks: 0;
- tofu/decode candidates: 0;
- critical relations: 16, each with native 1× and 8× nearest-neighbour evidence and an individual manual row;
- minimum independent text-text clearance: 8.434 px against 4 px;
- minimum matrix-entry-to-cell/focus clearance: 9 px against 5 px;
- minimum text/formula-to-line-or-arrow clearance: 14 px against 3 px;
- minimum node-text-to-node-border clearance: 30.6228 px against 5 px;
- minimum text/formula-to-panel-border clearance: 18 px against 6 px;
- minimum cross-panel reader-element clearance: 275 px against 8 px.

There are 86 nonzero intersections, all visually and semantically adjudicated as intended geometry: 18 focus-on-cell, 60 matrix-grid, 4 shaft-arrowhead joins, and 4 node-edge endpoint connections. The latter four are recorded separately in `review/manual_graphic_connection_ledger.tsv`; none is an illegal overlap.

During mask construction, three bbox-level same-colour candidates were tested and rejected because the claimed pixels belonged to adjacent glyphs on another baseline or source-order neighbour. Final raw masks assign each pixel to one object, and the regenerated final ledger contains none of those false candidates. This adjudication uses the final regenerated sheets, not the transient candidates.

`OVERLAP_PIXEL_HARD_FAIL_COUNT = 0`

`CLIP_PIXEL_HARD_FAIL_COUNT = 0`

`CLEARANCE_HARD_FAIL_COUNT = 0`

Decision: `PASS`.
