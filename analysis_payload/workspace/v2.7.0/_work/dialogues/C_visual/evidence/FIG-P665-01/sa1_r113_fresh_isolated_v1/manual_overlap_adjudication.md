# Manual native-pixel overlap adjudication

Reviewer identity: `C-FIG-P665-01-R113-SA1-FRESH-ISOLATED-V1`

The denominator is frozen at 14 visible semantic objects, including the caption, producing 91 unordered pairs. I opened the native 300 dpi subject, object/text/semantic overlays, all four native1x risk ROIs, and all four nearest-neighbor 8x versions before adjudicating.

The machine bounding boxes nominate five near/overlapping relations that require native-pixel interpretation:

- P014 O02--O03: the density formula bbox and combined brace/annotation bbox slightly overlap because the brace bbox includes its raised center cusp. In `risk_roi_01_native1x_300dpi.png` and its NN8x view, formula ink and brace ink are separate; annotation ink is farther below.
- P077 O09--O10: formula and arrow bboxes slightly overlap at their padded edges. In risk ROI 03, the last formula strokes and the top of the arrow have white separation.
- P082 O10--O11: arrow and derivative bboxes meet geometrically. Native ink shows the arrowhead ending above the derivative numerator with no shared pixel or misread contour.
- P086 O11--O12: the derivative bbox reaches the result-card top because the denominator and subscript descend toward it. NN8x native pixels show the subscript ending above the blue outline; neither touches the border.
- P091 O13--O14: warning-card and caption bboxes are close. The native subject and page-integration views show the red bottom outline above the first caption ink, with no contact, clipping, or obstructed reading.

All other pairs have visible spatial separation in the native subject and object overlay. The rounded-card fills are part of their composite semantic objects, so intended text-on-card composition is internal to O04/O05/O06/O12/O13 rather than an inter-object collision.

Canonical manual finding: zero illegal visible-ink overlaps; no unresolved candidate.
