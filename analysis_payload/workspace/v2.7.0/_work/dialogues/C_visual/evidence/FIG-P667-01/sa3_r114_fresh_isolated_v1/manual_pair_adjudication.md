# Exhaustive pair coverage and candidate adjudication — post-observation SA3

`unordered_pair_table_machine.csv` enumerates every one of the `C(24,2)=276` unordered pairs exactly once. The machine table has no manual decision field. After opening the complete native crop, mask/bbox overlays, all eight decisive ROI pairs and both nonzero-candidate overlays, I manually adjudicated the eight closest pairs below.

| Pair ID | Machine fact | Manual post-observation adjudication |
|---|---:|---|
| G03__G05 | 0 intersecting pixels; 0 px empty-pixel clearance | Intended source-defined border-to-arrow start alignment. The arrow leaves the posterior strip cleanly and does not hide text or create an ambiguous shape. Legal geometric junction. |
| G05__G06 | 0 intersecting pixels; 6 px empty-pixel clearance | Arrowhead remains visibly distinct before the result-box border; direction is unambiguous and no text is approached. |
| G06__G07 | 3 intersecting pixels | Intended source-defined attachment of the dashed branch to the result-box bottom border. The three common pixels are a legal connector junction, not an illegal overlap. |
| T02__T03 | 0 intersecting pixels; 2 px empty-pixel clearance | Tight underbrace stack, but native 300 dpi and nearest-neighbor 8× show separate legible glyphs with no crossing or wrong reading. Advisory spacing only under R168. |
| T06__T07 | 3 mask-intersection pixels | `T06` lower product/subscript bbox begins at y=421.178 pt while `T07` ends at y=421.013 pt, leaving a positive 0.165 pt vector gap. The colored 8× overlay localizes yellow pixels to bbox/antialias attribution beside the neighboring subscript; the original native pixels show no formula-stroke/label-stroke crossing or unreadability. `MASK_CONTAMINATION_CONFIRMED`. |
| T10__T11 | 0 intersecting pixels; 0 px empty-pixel clearance | Tight posterior underbrace annotation belonging to one mathematical construct. Original native and 8× views remain fully decipherable with no ink crossing or semantic ambiguity. Advisory spacing only under R168. |
| T12__T13 | 0 intersecting pixels; 10.045 px empty-pixel clearance | Two centered result lines remain clearly separated and form one coherent posterior statement. |
| T14__T15 | 0 intersecting pixels; 14 px empty-pixel clearance | Marginal formula and explanatory note remain visibly separate; neither competes with the dashed arrow or caption. |

The other 268 pair IDs in the exhaustive table all have zero mask intersection and at least 19.881 px machine-measured empty-pixel clearance. Their bboxes and semantic masks were inspected together in the complete overlays; none creates a hidden crossing, clipping condition, confusing contact or reading-path obstruction.

Canonical manual totals:

- machine nonzero candidate pixels: 6;
- mask-contamination pixels: 3 (`T06__T07`);
- legal connector-junction pixels: 3 (`G06__G07`);
- true illegal visible-ink collision pixels: 0;
- unresolved candidate pixels/pairs: 0;
- adjudication status: `MASK_CONTAMINATION_CONFIRMED`.
