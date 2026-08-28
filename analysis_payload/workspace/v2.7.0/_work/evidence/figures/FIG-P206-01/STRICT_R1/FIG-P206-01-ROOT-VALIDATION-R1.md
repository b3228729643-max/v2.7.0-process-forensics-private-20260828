# FIG-P206-01 — root validation of independent SA1 R1

Root reviewed the independent report, the native 1:1 q1/q2-label ROIs, the x/y tick ROIs, and the full figure crop from official R91 physical page 222.

- The q2 label visibly touches its query marker (0 px clearance); q1 is only 2.2 px away. Both fail the 3 px text-to-marker minimum.
- Several `-1`/`1` ticks are visibly painted through by the three boundary curves. The semantic masks measure 22, 9, 82, and 21 illegal pixels, totaling 134.
- Tick labels are 8.5 pt and curve/query/annotation labels are 9.2 pt, below the 9.5 pt effective-source floor. Five displayed math/operator glyphs additionally fail their 22 px native-pixel floor.
- The caption promises an ordering of training points entering the query neighborhood, but the figure does not encode a training-point set or its order.

Root decision: the independent `RESULT: FAIL` is confirmed. `CLIP_PIXEL_COUNT=0` and correct Lp geometry do not override the font, pixel, overlap, clearance, and caption-consistency failures. Next role is the figure-specific SA2.
