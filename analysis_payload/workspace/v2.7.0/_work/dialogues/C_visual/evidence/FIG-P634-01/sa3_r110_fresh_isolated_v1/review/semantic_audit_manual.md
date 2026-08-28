# Independent semantic audit — FIG-P634-01 / Figure 33.3

Reviewer: SA3, gpt-5.6-sol, xhigh. This audit was performed after opening the current R110 native 300 dpi page and crops. It does not reuse another reviewer’s verdict or denominator.

## Identity and integration

- Current figure location: physical PDF page 684, printed page 671, Figure 33.3.
- Source label: `fig:V5-C04-coordinate-sweep`.
- Chapter context at V5-C04 lines 217–221 introduces systematic scanning, references Figure 33.3, includes the current source, and then gives the reading order.
- The complete caption in the current PDF matches source line 61 exactly: “系统扫描按固定次序即时写回；当前子步的前段使用本轮新值，后段沿用前轮旧值；末位更新结束后，末位状态与本轮样本状态相同并记录为轮末样本。”

## Coordinate-sweep/Gibbs semantics

1. The top sequence is fixed and left-to-right: `1, 2, 省略, 前位, 当前, 后位, 省略, 末位`. The single update arrow points in that same direction. PASS.
2. Four hatched solid boxes precede the highlighted current box. They represent coordinates already written in the current round. The label `本轮新值` confirms that interpretation. PASS.
3. The highlighted box is the current coordinate and is separately labelled `当前新值`. It is not shown as parallel with the old portion. PASS.
4. Three dotted boxes follow the current coordinate. They are explicitly labelled `前轮旧值`, so later coordinates have not yet been overwritten. PASS.
5. The substep card writes `x^{[j]}` and states: from the beginning through the current coordinate, values are new this round; from the following coordinate through the last, values are from the previous round. This matches the chapter formula using same-round values for indices `<j` and previous-round values for indices `>j`. PASS.
6. The lower card writes `x^{[d]}` and `x^{(t)}` with a bidirectional arrow labelled `状态相同`. This is equality of the completed within-round state and the round-indexed state, not an extra Markov transition. PASS.
7. A separate rightward arrow labelled `仅此记录` leads from `x^{(t)}` to `轮末样本`, correctly excluding intermediate `x^{[j]}` states from the round-end sample trace. PASS.
8. The visual therefore encodes immediate write-back and rules out an erroneous parallel/Jacobi update. PASS.

## Formulas, codepoints, and numeric labels

- `x^{[j]}`: base mathematical italic x is U+1D465; superscript uses U+005B, U+1D457, U+005D. Correct.
- `x^{[d]}`: base mathematical italic x is U+1D465; superscript uses U+005B, U+1D451, U+005D. Correct.
- `x^{(t)}`: base mathematical italic x is U+1D465; superscript uses U+0028, U+1D461, U+0029. Correct.
- Order digits are U+0031 and U+0032; caption number is `33.3` with U+002E. Correct.
- Caption punctuation includes fullwidth semicolons U+FF1B, comma U+FF0C, and final ideographic full stop U+3002. Correct.
- No U+FFFD, tofu box, missing glyph, substituted bracket, or wrong mathematical codepoint is present.

## Geometry and page behavior

- Eight coordinate boxes form one straight row, with 21.25 px gaps between adjacent borders.
- Minimum internal text-ink to node-border clearance is 5 px, attained in the first two coordinate boxes; other representative boxes measure 6–14 px.
- Group labels above the first card have 10 px actual ink-to-border clearance.
- Descriptions inside the first card have 10 px actual ink-to-lower-border clearance.
- The two panel borders have 14.75 px vertical separation.
- Formula-to-arrow and arrow-to-label gaps in the lower card are 12.87–16.96 px.
- Lower card to caption-number bbox gap is 12.79 px.
- No arrowhead enters text, no border crosses text, no box is clipped, and no caption line collides with another line.

## Grayscale and hierarchy

The figure does not rely on color alone. Updated slots are solid and hatched; the current slot has a heavier solid outline and unique position; old slots use dotted outlines; all three groups also have explicit text labels. The title is strongest, the coordinate band is primary, and explanatory cards are secondary. Grayscale inspection preserves this hierarchy.

## R168 application

The three mathematical italic x spans measure 21 px in the raster extraction. They are lowercase x-height glyphs, for which the relevant readability floor is 17 px, and are visibly crisp in native1x and nearest8x views. Even if a different taxonomy treated a base mathematical symbol as targeting 22 px, the one-pixel difference is a raster/font-outline classification edge only. Under R168 it is advisory, because there is no missing glyph, wrong codepoint, semantic error, actual unreadability, clipping, illegal overlap, imbalance, or substantive geometry defect.

Final semantic finding: PASS.
