# FIG-P608-01 overlap and clearance adjudication

The frozen denominator is **N=172**: 112 visible glyphs, 58 explicit PDF drawings, and two visible hatch-pattern layers. Therefore **C=172×171/2=14,706**, and `all_unordered_pairs.csv` contains every unordered pair exactly once.

After paint-order ownership and foreground visibility are applied, the illegal-overlap count is zero, the final-mask intersection count is zero, and no object is empty or clipped. The minimum independent text/text clearance is 4 px (floor 4 px); text/graphic is 14 px (floor 3 px); non-whitelisted graphic/graphic is 5 px; same-parent internal clearance is 2.16 px. All 102 critical pairs have six-image evidence packets and unique manual decisions.

## Marker/axis boundary pairs

`PAIR-117-125` and `PAIR-118-125` were adjudicated separately. The top-panel plotted trace begins at x=1, exactly the axis minimum, and the first data marker is centered at that plot-path start. The y-axis/arrow is the boundary whose x coordinate is also the minimum. The target/source geometry therefore establishes an axis-data boundary relation, a protocol-whitelisted intended design contact rather than a collision between unrelated objects. Both marker and axis/arrow retain complete, nonempty final-visible masks; the marker remains readable and the axis/arrow line type is not lost. The two pair ledgers contain different decision IDs and pair-specific notes.

## Scope of the remaining failure

No overlap, clearance, crop, or ownership gate fails. The overall SA1 result is nevertheless `FAIL_TO_SA2` because the caption semicolon `TXT-098` fails its mandatory exact-metadata peer area-ratio calibration; that typography failure is not waived by the passing overlap adjudication.
