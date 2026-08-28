# Manual visual, grayscale, clipping, and page-integration ledger

## Views actually opened

- Official physical page 739 at 200 dpi and native 300 dpi.
- Native 300 dpi figure-plus-caption crop, 1980 x 875 px.
- Native 300 dpi figure-only crop.
- Native grayscale figure-plus-caption crop.
- Native text, semantic, and 33-object overlays.
- Seven selected critical ROIs, each at native1x and nearest-neighbor 8x: identity formula; KL inequality; unknown upper bound; stationary label/curve; ticks/x-label; caption label; inter-panel gap.

## Manual findings

- Page placement is balanced: the figure follows the KL-ELBO proof and lead-in, then precedes the point-parameter variational derivation. It neither crowds nor strands surrounding prose.
- Both 67 mm panels have equal visual weight. Titles align; margins and internal whitespace are deliberate rather than excessive.
- The left decomposition reads top-to-bottom: evidence length, partitioned ELBO/KL bar, identity, then inequality explanation.
- The right plot reads from axes to monotone staircase to upper-reference caveat and endpoint caveat. Annotation does not cover any step or marker.
- Grayscale preserves meaning: the upper reference remains dashed, the trajectory remains solid with circular markers, and left subregions remain explicitly labelled and divided. Color is not the sole carrier of meaning.
- The smallest rendered text objects are the 0--6 ticks at 26--27 ink pixels and 9.0 pt annotations/axis label at 32--33 ink pixels. All are clear at native1x and nearest8x and show no actual unreadability.
- R168 advisory: source declarations of 9.2 pt overall and 9.0 pt for selected plot labels are below an older 9.5 pt numeric target, and title vector spans are larger through the local bold font behavior. Actual output shows neither missing/wrong glyphs, unreadability, obvious imbalance, clipping, illegal overlap, nor semantic error.
- Nearest observed text-to-line clearance is the x tick digits to their ticks/axis, visibly at least 9 native pixels. Text-to-panel-border clearance is at least 18 native pixels. Adjacent panel borders are separated by about 116 native pixels. Caption line ink gaps are at least 11 native pixels.
- No visible ink reaches the crop boundary; all panel borders, arrowheads, markers, labels, caption lines, and the final caption phrase are complete.

SOURCE_FONT_PASS=true
PIXEL_HEIGHT_PASS=true
SAME_CLASS_RATIO_PASS=true
ROLE_RATIO_PASS=true
GRAYSCALE_PASS=true
PAGE_INTEGRATION_PASS=true
VISUAL_HARMONY_PASS=true
CLIP_PIXEL_COUNT=0
MIN_TEXT_CLEARANCE_PX=9
