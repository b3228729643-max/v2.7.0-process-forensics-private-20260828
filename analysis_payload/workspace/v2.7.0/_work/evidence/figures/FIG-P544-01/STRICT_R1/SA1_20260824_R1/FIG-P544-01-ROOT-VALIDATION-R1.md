# FIG-P544-01 ROOT VALIDATION R1

## Root verdict

- `RESULT: FAIL`
- `NEXT_ROLE: SA2`
- Frozen input: `strict_current_r93_fullbook/main_full.pdf`, physical page 588, printed page 575, figure 30.1.
- Root independently reopened the native 300 dpi color/grayscale crop, semantic overlay, the dashed-legend critical pair and its two separated raw masks, the figure source, the standalone page text, and the chapter's row/column convention bridge.

## Confirmed hard failures

1. Three of 11 semantic source elements fail the 9.5 pt floor: both legend labels and the edge label are explicitly 8.8 pt. The public `every node/.append style={font=\small}` makes the ordinary node/formula layer 10.0 pt, so it does not excuse the three explicit overrides.
2. Eight literal glyph/operator/punctuation measurements fail the native 300 dpi height gates. The evidence measures `=`, caption-number dot, colons, comma and semicolon as their own substrings rather than substituting a parent formula/paragraph height. Thirty glyph rows fail after source-size, pixel, role or collision propagation; all visible glyphs are mapped.
3. Role hierarchy fails: legend/node `0.921`, edge-label/node `0.895`, and formula-block/node `0.763`; `FONT_VISUAL_HARMONY_PASS=false`. The 8.8 pt legend/edge layer is visibly weak and must not be repaired by further shrinking.
4. The dashed legend arrowhead intersects the final legend glyph in six separated-mask raw pixels. Root inspection of the original-size ROI and the independent text/arrowhead masks confirms a true collision with 0 px clearance, not a dilated-mask artifact. Clipping remains zero.
5. `\pi=\pi P` mixes notation with this chapter's explicit row-vector convention `\rho_\star=\rho_\star A`; the chapter uses `P=A^{\mathsf T}` only together with a column vector `\boldsymbol p_\star=P\boldsymbol p_\star`. The node therefore does not state either convention completely.
6. The structure node says “返性”, while the adjacent dependency route and formal section consistently require “正常返”. The single top node also merges time-average and stepwise-convergence conclusions without showing that nonperiodicity is an additional condition for the latter.

## Passing/nonblocking findings

- Same-class ratios, grayscale redundancy, reading order and whole-page integration pass.
- Apart from the dashed-legend collision, registered critical pairs satisfy their applicable clearance gates; the minimum passing text--text clearance is 5.35 px and the fixed-equation/node-border clearance is 13 px.
- The reversible/detailed-balance dashed route correctly communicates a sufficient, nonnecessary path to stationarity.

The R93 candidate must not proceed to SA3 for this figure. SA2 must use one complete row/column convention, restore “正常返”, separate the condition scopes of time-average versus stepwise convergence, raise all explicit 8.8 pt text to at least 9.5 pt, repair every literal pixel/role failure, and move the dashed legend arrow clear of the text. A rebuilt frozen candidate then requires fresh independent SA1 evidence.
