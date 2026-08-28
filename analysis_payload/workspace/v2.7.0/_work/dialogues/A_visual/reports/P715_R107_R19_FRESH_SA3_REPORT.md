# FIG-P715-01 — R107 R19 fresh isolated SA3 final report

## Final outcome

`SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`

This report covers the sole fresh isolated SA3 handoff `A-R107-P715-SA3-FRESH-ISOLATED-20260826`, executed with `gpt-5.6-sol` / `xhigh`. SA3 did not write `A_LOCAL_PASS`, state, inventory, source, mainline, or build output.

## Frozen input identity and independent location

- R107 PDF: 817 pages; 4,967,249 bytes; SHA256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- P715 source: 4,057 bytes; SHA256 `900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`.
- Independently located target: physical PDF page 765; printed page 752; unique caption `图 36.2`.
- Figure-plus-caption crop: `[66.0,67.5,518.0,288.5]` pt, native 300-dpi crop 1884×922 px.
- Standalone figure-body crop: `[66.0,67.5,518.0,269.9]` pt, native 1884×844 px.

No previous P715 evidence, prior role result, previous page choice, previous candidate set, or previous conclusion was read or reused.

## Frozen N/C and caption boundary

SA3 conservatively included the visible caption within the figure evidence boundary:

- figure-body glyphs: 216;
- caption glyphs: 39;
- visible glyph objects: 255;
- figure-body drawing/path objects: 43;
- `N=255+43=298`;
- complete unordered-pair ledger `C=choose(298,2)=44,253`.

The denominator difference from SA1 is explained solely by this independently chosen caption-inclusion boundary. SA3 neither queried nor reused SA1's N, C, object identities, candidates, page choice, or decision.

All 43 drawing/path objects have exact two-way ownership: each appears once in the machine inventory and once in the manual drawing ledger, with zero ID delta. The set comprises 2 panel borders, 3 node borders, 4 edge shafts, 4 arrowheads, 27 matrix-cell borders, and 3 focus borders.

## Machine evidence

- 298 unique visible objects; 44,253 unique valid unordered pairs; no self-pair or out-of-set pair.
- Machine candidate count: 0; candidate intersection pixels: 0.
- Minimum independent raw-mask clearance: 9.434 px (`G0118` versus `G0129`), above the 4 px hard text-text threshold.
- Other inspected hard-class minima: 31.6228 px node text-to-border, 10.0 px formula text-to-graphic, and 19.0 px title text-to-panel border.
- Empty masks: 0; replacement/tofu codepoints: 0; crop-boundary touches: 0; mask contamination: 0.
- All panel, matrix, focus, node, arrow-shaft, and arrowhead paths are represented; all four sides remain intact.

Four raw drawing intersections were separately reviewed and are intentional: focus-over-cell, graph endpoint attachment, shared matrix grid, and arrow shaft/head join. None is an illegal overlap.

## Actual manual terminal review

After final machine artifacts were fixed, SA3 actually opened:

- 8 glyph contact sheets covering `G0001–G0255`;
- 2 drawing contact sheets covering `D0001–D0043`;
- 4 final views: full page, figure-plus-caption, standalone body, and grayscale;
- all 8 final critical relationship images.

Only after those openings, SA3 hand-authored the row-level ledgers:

- glyph ledger: 255/255 unique rows, non-PASS 0, missing-stroke pixels 0, foreign pixels 0;
- drawing ledger: 43/43 unique rows, non-PASS 0;
- relation ledger: 8/8 unique rows, non-PASS 0;
- view/sheet/relation ledger: 22 rows, non-PASS 0.

The final views show balanced panels, readable titles/formulas/matrices, correct graph endpoints, continuous borders, intact caption, natural page integration, and preserved grayscale hierarchy. No clipping, illegal overlap, tofu, wrong codepoint, unreadability, obvious severe imbalance, or geometric error is visible.

Under R168, font metadata, micro-font size, pixel taxonomy, peer ratios including `[0.92,1.08]`, and 1–2 px differences were advisory. The low ink boxes of the CJK stroke `一` and low-profile punctuation/operators are expected glyph geometry and were manually found complete. Explicit source sizes are ≥9.5 pt at scale 1.0; the caption is a 9.963 pt PDF vector span. No R168 hard-fail condition exists.

## Mathematical and random-walk semantics

The arrows encode `i→j`, `j→i`, `j→h`, and `h→i`. With row/column order `(i,j,h)` and `A_ij>0 ⇔ j→i`, the displayed matrices are internally exact:

- `A=[[0,1,1],[1,0,0],[0,1,0]]`;
- column sums `(1,2,1)`;
- `M=[[0,1/2,1],[1,0,0],[0,1/2,0]]` and `1^T M=1^T`;
- `P=M^T=[[0,1,0],[1/2,0,1/2],[1,0,0]]` and `P1=1`;
- `P_ji=M_ij=Pr(X_(t+1)=i|X_t=j)`, `p^(t+1)=Mp^(t)`, `rho_(t+1)=rho_tP`, and `rho_t=(p^(t))^T` agree.

The focused A, M, and P cells track the same transposed transition entry. No wrong matrix entry, reversed edge, wrong index, missing rule, or random-walk semantic error was found.

## Seal audit

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R19_SA3_FRESH_ISOLATED_R107_20260826`
- Common payload: 648 files; 16,076,880 bytes.
- `MANIFEST_A_SHA256.csv`: 648 payload rows; SHA256 `25228F346ED6B65B3000C9199404779F678D2AF760B4B029DA7DBB0F20FA5D2C`.
- `MANIFEST_B_SHA256.csv`: 648 payload rows; same SHA256 `25228F346ED6B65B3000C9199404779F678D2AF760B4B029DA7DBB0F20FA5D2C`.
- Manifest set delta: 0; control rows inside manifests: 0; payload hash mismatches: 0.
- Three self-excluded controls: the two manifests and `WRITE_STOPPED`.
- `WRITE_STOPPED` was the last content write inside the evidence root and is read-only.
- Final root: 651 ordinary files; read-only failures 0; ADS 0; cache/pyc 0; reparse points 0.

Machine evidence, manual ledgers, the consolidated adjudication, and `RESULT.txt` all resolve to PASS.
