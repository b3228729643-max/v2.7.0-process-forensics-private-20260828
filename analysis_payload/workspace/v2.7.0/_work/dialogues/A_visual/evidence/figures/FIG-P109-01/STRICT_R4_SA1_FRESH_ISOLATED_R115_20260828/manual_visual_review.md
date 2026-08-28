# Manual visual review

Reviewer identity: `A-R115-P109-SA1-FRESH-ISOLATED-20260828`, fresh isolated SA1, `gpt-5.6-sol/xhigh`.

## Opened evidence gate

Before authoring any manual verdict field, the reviewer actually opened:

- official physical page 116 at 300 dpi;
- the final figure/caption crop at native 1x, 300 dpi;
- the same crop at nearest-neighbor 8x;
- the grayscale 300 dpi crop;
- the 200 dpi page-integration view;
- the object-denominator and text-measurement overlays;
- all six critical ROIs at both native 1x and nearest-neighbor 8x.

The frozen denominator contains 15 reader-visible semantic objects, O01 through O15. The frozen pair denominator contains all 105 unordered pairs. Every row in `after_overlap_report.csv` was then reviewed manually against the opened evidence.

## Per-object manual findings

| Object | Manual finding | R168 hard result |
|---|---|---|
| O01 convex region | Smooth closed visibly convex region; no indentation, open seam, or crop. | CLEAR |
| O02 chord | Straight segment joins x and y and remains within O01 for its full visible length. | CLEAR |
| O03 x marker | Complete circular endpoint marker at the left endpoint. | CLEAR |
| O04 y marker | Complete circular endpoint marker at the right endpoint. | CLEAR |
| O05 interior marker | Lies on the chord at the first interior location. | CLEAR |
| O06 interior marker | Lies on the chord at the middle interior location. | CLEAR |
| O07 interior marker | Lies on the chord at the third interior location. | CLEAR |
| O08 x label | Correct italic x, readable, separated from marker and chord. | CLEAR |
| O09 y label | Correct italic y, readable, separated from marker, chord, and region label. | CLEAR |
| O10 z formula | Correct convex-combination formula; opaque backing and whitespace prevent line-through-text. | CLEAR |
| O11 region label | “凸可行域 C” is complete and readable. Its opaque backing masks the nearby boundary before compositing, so no visible boundary ink crosses glyph ink. | CLEAR |
| O12 conclusion border | Rounded border is complete, not clipped, and has a visible interior inset. | CLEAR |
| O13 conclusion formula | Correct premise and implication for convexity; all glyphs are intact and clear of O12. | CLEAR |
| O14 caption number | “图 7.1” is complete, aligned, and separated from O15. | CLEAR |
| O15 caption text | Exact current caption is complete and readable at page scale. | CLEAR |

## Mathematical, semantic, and geometric review

- The depicted claim is correct: for `x,y in C` and `lambda in [0,1]`, `lambda x + (1-lambda)y` lies in `C` when `C` is convex.
- O03 and O04 are inside O01. O02 is the entire segment between them and visually stays within O01.
- O05-O07 lie on O02 and correctly illustrate intermediate convex combinations. Because they carry no numerical lambda labels, their order cannot contradict the formula convention.
- O10 defines `z` using the same `x`, `y`, and `lambda` used by O08, O09, and O13.
- The chapter prose uses the equivalent generic symbols `x_1,x_2,t`; this is a harmless variable renaming, not a contradiction.
- The caption states exactly the single visible conclusion and agrees with both the figure and adjacent prose.

## Rendering, grayscale, and page integration

- No missing glyph, tofu box, wrong codepoint, broken operator, or clipped extremum was visible at native 1x or nearest 8x.
- The former numerical thresholds are advisory under R168. The source's explicit 9.2 pt labels are plainly readable; natural glyph-shape height differences between italic x and y do not create an obvious imbalance.
- Grayscale preserves the region, chord, dark endpoints, lighter interior markers, formulas, and caption. Color is not the sole carrier of meaning.
- On physical page 116 the figure is centered between the preceding geometry explanation and the following prose. It creates no collision, orphaned caption, abnormal whitespace block, or disruptive reading-order break.

Hard direction: `PASS`.
