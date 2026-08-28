# Post-observation unordered-pair ledger

Reviewer identity: `C-FIG-P680-01-R114-SA1-FRESH-ISOLATED-V1`.

The frozen denominator is `T01`–`T16`, `N01`–`N06`, `E01`–`E04`, exactly 26 reader-visible objects. `all_unordered_pairs.csv` enumerates every unordered pair as `P001`–`P325`, exactly `26 choose 2 = 325`. The following map is exhaustive and assigns a post-observation disposition to every pair ID.

## P001–P280: every pair containing at least one TEXT/FORMULA object

- Legal contained-text/border pairs: `P016 T01–N01`, `P040 T02–N01`, `P086 T04–N02`, `P107 T05–N02`, `P128 T06–N03`, `P147 T07–N03`, `P183 T09–N04`, `P199 T10–N04`, `P215 T11–N05`, `P229 T12–N05`, `P243 T13–N06`. The text ink is inside the node fill and does not touch the border. Measured bbox-to-border minima are respectively 35, 23, 30, 26, 30, 26, 40, 16, 42, 14, and 33 px.
- Every other pair ID in `P001`–`P280` is post-observation `DISJOINT_VISIBLE_INK`. The closest TEXT/FORMULA–TEXT/FORMULA pairs are `P073`, `P116`, `P173`, and `P206`, each with 7 px bbox clearance. The closest TEXT/FORMULA–LINE_ARROW pairs are `P046` and `P047`, each with 15 px bbox clearance.
- Result for every `P001`–`P280`: illegal visible-ink overlap = 0 px; clip = 0 px; unresolved = 0.

## P281–P319: NODE_BORDER–NODE_BORDER and NODE_BORDER–LINE_ARROW pairs

- Declared graph-topology endpoint contacts: `P286 N01–E01`, `P287 N01–E02`, `P294 N02–E01`, `P296 N02–E03`, `P302 N03–E02`, `P304 N03–E04`, `P309 N04–E03`, `P315 N05–E04`. These eight contacts are the intended incident endpoints of four directed edges. They do not cross text, formulas, or unrelated borders and are not illegal overlap.
- Every other pair ID in `P281`–`P319` is post-observation `DISJOINT_VISIBLE_INK`.
- Result for every `P281`–`P319`: illegal visible-ink overlap = 0 px; clip = 0 px; unresolved = 0.

## P320–P325: LINE_ARROW–LINE_ARROW pairs

All six pairs are post-observation `DISJOINT_VISIBLE_INK`. The two upper curved branches separate immediately after the shared node; the two vertical arrows occupy different columns; no arrowheads or strokes cross.

## Canonical pair outcome

- Frozen pair denominator: 325/325 adjudicated.
- Illegal-overlap candidate pixel count after excluding declared incident endpoints: 0.
- True illegal collision pixel count: 0.
- Mask-contamination pixel count: 0.
- Declared legal topology-contact cluster count: 8.
- Unresolved pair count: 0.
- Clip pixel count: 0.

Evidence actually opened: `native_page_300dpi.png`, `figure_caption_300dpi.png`, `object_id_overlay_300dpi.png`, `semantic_class_overlay_300dpi.png`, `critical_roi_native1x.png`, and `critical_roi_nearest8x.png`.
