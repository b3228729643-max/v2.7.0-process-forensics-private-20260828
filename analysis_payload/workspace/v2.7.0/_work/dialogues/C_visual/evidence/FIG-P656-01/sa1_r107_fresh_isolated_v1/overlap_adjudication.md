# Frozen mask ownership and overlap adjudication

## Final machine definition

The only final machine definition uses the official 300 dpi raster, one raw mask per leaf object, no dilation, and a two-native-pixel vector bbox allowance covering visible half-stroke/antialias extent. Text masks are confined to the rounded half-open PDF glyph advance box; patterned digit `2` masks use a neutral-color gate plus the single visible digit component. `G086` (`∏`) uses a narrow vertical bbox expansion solely to include its complete top bar and feet.

The final leaf denominator is 115 and the all-pairs table contains 6,555 unique rows. Empty glyph masks=0, empty drawing masks=0, mask-contamination pixels=0, clip pixels=0.

## Why the unsealed diagnostic changed from 4 relations / 252 pixels

The earlier unsealed diagnostic drawing mask used a four-pixel vector bbox pad. At adjacent same-blue objects, that crop admitted visible pixels owned by the neighbor. Those were mask-ownership artifacts, not changes to the PDF and not actual geometry. Tightening the allowance to the visible two-pixel half-stroke/antialias extent produced the following final values:

| Relation | Initial diagnostic | Final frozen | Explanation |
|---|---:|---:|---|
| D019–D021 | 4 px | 0 px, 2 px clearance (`P6536`, `CR028`) | Count-box border had imported adjacent arrowhead blue pixels under the 4px pad; the correctly owned masks are separate. |
| D019–D024 | 54 px | 18 px (`P6539`) | The arrow shaft originates at the count-box east border; 18 px are the actual intentional line-to-node connection. |
| D020–D021 | 99 px | 41 px (`P6541`, `CR027`) | The shaft and head are parts of one arrow; 41 px are the actual shared construction pixels. |
| D024–D025 | 95 px | 38 px (`P6555`, `CR029`) | The second shaft/head pair intentionally shares 38 construction pixels. |

Thus the unique final raw-intersection denominator is exactly three nonzero relations totaling 97 pixels: `P6539=18`, `P6541=41`, and `P6555=38`. All three are intentional graphic connections. `OVERLAP_PIXEL_COUNT` for illegal independent-object intersections is zero. The second arrowhead-to-coefficient relation is `P6554`/`CR030`, with zero intersection and 3 px approach clearance.

The punctuation-table correction that added `G055` as a no-exact-9.2pt peer row is unrelated to drawing-mask ownership and did not cause any overlap value to change.

After the final generator run, I reopened `CR027`, `CR028`, `CR029`, and `CR030` at native/8× evidence size. I visually confirmed the two intended shaft/head joins and the 2 px / 3 px arrow-to-box approach gaps. The manual critical ledger was reviewed against these final images and carries the same relation IDs and pixel values.

The final consistency run also detected five clearance-only ledger values that predated the last frozen regeneration. I reopened each affected final ROI rather than mechanically copying numbers: `CR004`, `CR010`, and `CR015` each show a pure digit `2` with 12 px clearance to the final perimeter-band derivative; `CR020` shows 21.561 px label-to-shaft clearance; `CR021` shows 16.263 px label-to-head clearance. All remain safely above their applicable hard thresholds, all have zero intersection, and the durable manual ledger now matches these final machine values.
