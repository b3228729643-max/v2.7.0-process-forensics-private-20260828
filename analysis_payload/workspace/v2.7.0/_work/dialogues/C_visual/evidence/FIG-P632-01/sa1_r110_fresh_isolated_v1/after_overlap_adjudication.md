# FIG-P632-01 overlap adjudication

- Reviewer: SA1, gpt-5.6-sol/xhigh
- Native source: physical page 682 rendered directly by Poppler at 300 dpi, 2481 x 3508 px, no post-render resize
- Visible semantic-object denominator: 23
- Complete unordered-pair denominator: 253
- Coarse bbox candidate pairs: 46
- Direct native-pixel candidate illegal shared pixels: 0
- Mask-contamination pixels: 0
- Confirmed illegal overlap pixels: 0
- Unresolved candidates: 0
- Pixel adjudication status: CLEAR

Every pair is individually documented in `manual_pair_adjudication.md`. The following visible contacts are intentional geometry, not illegal semantic collisions: coordinate axes with nested contours; slice lines with contours; the two slice lines and marker at `(a,b)`; horizontal/vertical slice handoffs to their matching mapping routes; conditional curves approaching the x-axis at tails; each mean guide meeting its curve at the peak and its x-axis at the baseline. These contacts do not obscure text, formulas, arrow direction, probability meaning, or numerical labels.

The 46 bbox intersections are coarse rectangular-screening results. Native pixels, the semantic overlay, source coordinates, and the applicable 8x ROIs show that their non-intended cases contain whitespace rather than shared foreground. No case requires `MASK_CONTAMINATION` because no pixel-mask process reported a positive pixel cluster. No case is `UNRESOLVED`, and no pixel dispute exists.

Minimum reviewed clearances include approximately 9.2 px from `(a,b)` label ink to its leader, about 11 px from the third note line to the note border, and about 12.6 px from the note border bottom to the caption bbox top. Arrowhead-to-conditional-y-axis gaps are roughly 15 PDF pt (over 60 px). Applicable text/graphic, node-border, and adjacent-object thresholds are satisfied.
