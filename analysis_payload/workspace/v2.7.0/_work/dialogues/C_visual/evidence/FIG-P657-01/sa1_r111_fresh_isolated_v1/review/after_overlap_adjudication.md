# Manual pixel-overlap adjudication

I opened the native 300 dpi figure, the text foreground mask, the graphics foreground mask, the combined overlay, the labeled text-box overlay, and every critical native1x/nearest8x ROI before making these decisions.

- `TEXT–TEXT PASS`: the maximum actual-ink intersection over all independent measured text pairs is 0 px. T13 is an aggregate measurement alias and is excluded from independence comparisons with its own T13A/T13B substrings.
- `TEXT/FORMULA–LINE_ARROW PASS`: the separated masks contain 0 shared pixels. The tightest manually checked label-to-line clearance is T18 at 15 px.
- `TEXT/FORMULA–MARKER PASS`: no marker objects exist in this figure.
- `TEXT/FORMULA–NODE_BORDER PASS`: all node labels are inside their intended fills without touching borders; the minimum node text-to-border clearance is 12 px.
- `TEXT/FORMULA–PANEL_BORDER PASS`: the figure has no panel border; every glyph is fully inside the page and local figure extent.
- `LEGEND–DATA_CURVE PASS`: no data curve exists; both legend arrow samples are isolated from their labels by 31 px and 28 px respectively.
- `ANNOTATION–DATA_CURVE PASS`: no data curve or annotation overlay exists.
- `ARROWHEAD–TEXT PASS`: all seven diagram arrowheads and both legend arrowheads are outside text ink. The nearest arrowhead/label clearance is 15 px.
- `CLIP PASS`: the full-page and figure+caption native renders show every glyph, node corner, line end, arrowhead, legend sample, and caption line complete. `CLIP_PIXEL_COUNT=0`.

The all-object raw bbox sheet contains expected node–relation contacts at legal topology attachments. Those are not text collisions. Pair P190 also has a rectangle-union intersection because the two-line caption-body envelope extends under the caption label; the actual ink masks are disjoint. Neither case creates an actual foreground candidate cluster.

- `OVERLAP_CANDIDATE_PIXEL_COUNT=0`
- `MASK_CONTAMINATION_PIXEL_COUNT=0`
- `OVERLAP_PIXEL_COUNT=0`
- `PIXEL_ADJUDICATION_STATUS=CLEAR`
- `PIXEL_ARBITER_MODEL=NOT_USED`
- `PIXEL_ARBITER_REASONING=NOT_USED`

Manual overlap decision: `PASS`; there is no true collision, mask-contamination candidate, or unresolved cluster.

