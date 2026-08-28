# Independent SA3 review report

## Identity and scope

- HANDOFF_ID: `C-FIG-P609-01-R109-SA3-FRESH-ISOLATED-REPLACEMENT-V2`
- actual instance: `/root/sa3_fig_p609_r109_fresh_isolated_replacement_v2`
- model / reasoning: `gpt-5.6-sol` / `xhigh`
- assigned UID: `FIG-P609-01`
- assigned candidate: official R109 only
- decision: `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`
- N/C decision: `NO_CHANGE`

This report makes no C_LOCAL, global, or final acceptance claim and reviews no other UID or role.

## Candidate identity and independent localization

- Official PDF: 4,967,054 bytes; SHA-256 `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`; 817 A4 pages.
- Current figure source: 2,602 bytes; SHA-256 `20687D1EE01AABA9B605591A61781CF688328026E0645AD51B6E02E921DC98A2`.
- Independent text localization found current Figure 32.9 on physical page 661 / printed page 648. The caption is “固定窗口内的正经验自相关增大方差权重，因而使同长度轨迹的有效样本量减小。”

## Views actually opened

- full page at 200 dpi and native 300 dpi;
- native-300-dpi figure body and figure+caption;
- native-300-dpi grayscale figure+caption and native-300-dpi grayscale full page;
- left panel, right panel, and caption at native 300 dpi;
- nearest-neighbor 8x versions of all three critical ROIs;
- word measurement overlay, semantic-object overlay, foreground mask, and outline overlay.

## Source-font and pixel evidence

- General visible source text is explicitly 9.6 pt; axis labels are 9.8 pt; both panel titles are 10.4 pt; compiled `normalsize` caption text is 10.90909 pt.
- There is no `resizebox`, `scalebox`, `transform shape`, or outer graphic scale; cumulative graphics scale is 1.0. The minimum general-visible effective source font is therefore 9.6 pt, above 9.5 pt.
- At native 300 dpi, all 57 hard-class word fragments meet their class thresholds. The remaining 19 fragments are low-profile operators, accents, or punctuation tracked as R168 advisory metadata, not hidden hard failures.
- Observed hard-class minima: CJK/mixed 34 px; digits 26 px; ordinary Latin/Greek lowercase 22 px; uppercase/mixed 27 px; base math symbol 27 px; naturally derived math script 16 px.
- Tick labels use a single 9.6 pt source role and measure 26-27 px, ratio 1.0385, within the 1.08 pixel-role tolerance. Corresponding left/right title CJK fragments are both 41 px and the numeric panel prefixes are both 29 px. Raw whole-word extrema with different glyph repertoires were not misused as like-for-like peer measurements.
- Relative source-role scale to the 9.6 pt base is 1.0208 for axis labels and 1.0833 for panel titles; formula and explanatory bases remain 1.0. No role is visibly inflated, shrunken, or dominant for the wrong reason.

## Complete object and pair review

- The fresh denominator contains 26 semantic text/formula elements plus 6 semantic graphic objects, 32 total.
- All `32*31/2 = 496` unordered pairs are present once in `unordered_pairs.csv`.
- Manual decisions cover all 32 object IDs and all 496 pair IDs with no missing or extra ID: 492 `CLEAR`, 2 legal background overlays, 1 legal stem-axis contact, and 1 legal cutoff-boundary-axis contact.
- Prohibited independent-foreground candidate pixels: 0. Confirmed true illegal overlap pixels: 0. Mask contamination pixels: 0. Unresolved candidates: 0.
- Clip pixels: 0. Conservative native-300-dpi minimum external-ink clearance: 7 px; required text-text, text-line, text-border, edge, and cross-panel clearances are satisfied.

## Semantics and geometry

- The plotted ACF sequence is `(1,.86,.74,.64,.55,.47,.40)` at lags `0..6`; only lags `1..6` enter the correction sum.
- Independent recomputation gives `sum rho_k=3.66`, `sum k rho_k=11.21`, hence `tauhat_{6,n}=8.32-22.42/n`. With the stated `n>6`, this is positive and greater than one, so `Nhat_eff=n/tauhat_{6,n}<n`.
- The weighted finite-sample rule, positive-denominator condition, preset-window limitation, omission of post-window lags, and “not a convergence proof” caveat are all present and correct.
- Reading order is unambiguous: inspect the positive ACF window, follow the connector to the finite-sample weighted ESS formulas, then read the three-line limitation. Axes, stems, markers, cutoff, ellipsis, formulas, and caption agree with the adjacent V5-C03 text.

## Visual and page integration

- No missing glyph, tofu, wrong codepoint, clipped arrowhead, clipped marker, clipped text, overflow, or illegal overlap is visible at native scale or nearest-neighbor 8x.
- Color is not the sole semantic carrier: stem height/marker geometry, dashed cutoff, panel structure, formulas, and text preserve meaning in grayscale. The gold cutoff annotation remains readable in grayscale.
- Figure 32.9 is balanced on printed page 648 beneath Figure 32.8, with caption and follow-up reading paragraph intact; no orphan, collision, or abnormal whitespace is introduced.

## Final independent conclusion

`SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`

No source change is requested. The next authorized action is main-thread C_LOCAL acceptance or a main-thread rework packet if independent integration evidence later changes.

