# Pixel overlap and clearance adjudication

The exhaustive `all_unordered_pairs.csv` contains exactly 44,253 unordered pairs for the frozen `N=298` object set. Independent foreground pixels were partitioned to one visible owner before pair comparison, preventing a common parent from manufacturing a false intersection.

- Machine candidate pair count: 0.
- Candidate intersection pixel sum: 0.
- Empty masks: 0.
- Replacement/tofu codepoints: 0.
- Crop-boundary touches: 0.
- Minimum thresholded independent clearance: 9.434 px for `G0118` versus `G0129`, above the 4 px text-text hard threshold.
- Other explicitly inspected clearances: 31.6228 px node text to node border; 10.0 px formula text to matrix graphic; 19.0 px title text to panel border.

Four zero-distance drawing relationships were separately inspected because raw vector ownership intentionally meets or overlays:

1. `D0025` / `D0033`: focus border over its own M cell frame.
2. `D0004` / `D0006`: directed graph shaft attached to node-j boundary.
3. `D0027` / `D0028`: adjacent matrix cells sharing a grid rule.
4. `D0006` / `D0007`: arrow shaft joined to its arrowhead.

Each is a required structural relationship rather than illegal overlap. The eight final relation images were individually opened and adjudicated in `manual_relation_reviewer_ledger.csv`.

`OVERLAP_CANDIDATE_PIXEL_COUNT=0`  
`MASK_CONTAMINATION_PIXEL_COUNT=0`  
`OVERLAP_PIXEL_COUNT=0`  
`PIXEL_ADJUDICATION_STATUS=CLEAR`  
`PIXEL_ARBITER=NOT_USED`
