# FIG-P632-01 R110 / R168 visual acceptance

## Identity and route

- HANDOFF_ID: `C-FIG-P632-01-R110-SA2-R168-READONLY-ADJUDICATION-V1`
- Actual instance: `/root/sa2_fig_p632_r110_r168_readonly_adjudication_v1`
- Role: `R110 READONLY_R168_ADJUDICATION_FIRST SA2`
- Model / reasoning: `gpt-5.6-sol / xhigh`
- Candidate: official R110 full book, physical page 682, printed page 669, Figure 33.2
- UID: `FIG-P632-01`

## R168 acceptance matrix

- SOURCE_FONT_PASS = true
- PIXEL_HEIGHT_PASS = true
- SAME_CLASS_RATIO_PASS = true
- ROLE_RATIO_PASS = true
- OVERLAP_CANDIDATE_PIXEL_COUNT = 8196
- MASK_CONTAMINATION_PIXEL_COUNT = 8196
- OVERLAP_PIXEL_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED
- PIXEL_ARBITER_MODEL = NOT_USED
- PIXEL_ARBITER_REASONING = NOT_USED
- CLIP_PIXEL_COUNT = 0
- MIN_TEXT_CLEARANCE_PX = 8
- VISUAL_HARMONY_PASS = true
- MATH_SEMANTICS_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true

## Font and readability adjudication

The current source declares `\fontsize{9.6pt}{11.5pt}\selectfont` for every figure node and applies no whole-figure or panel-level text scaling. The official PDF reports the base figure spans at approximately 9.5641 pt, with only TeX-natural scripts at approximately 6.6949 pt. All semantic base text, formulas, numerical values, labels and Chinese notice lines are readable in the unresized 300 dpi crop. The natural fraction/script digits measure 20--27 ink pixels in the mechanical span table. A small degree glyph is visibly recognizable; under R168 its glyph-outline/pixel-height microcharacteristic is advisory, not a hard defect. No text is actually unreadable or obviously imbalanced.

All page-682 fonts are embedded subsets with Unicode mappings. Native text extraction preserves the Chinese caption/notice and the mathematical values; there is no tofu, missing glyph, wrong codepoint, or fallback-font substitution visible in the complete page or critical ROIs.

## Mathematical and probability-model adjudication

For the zero-mean unit-variance bivariate normal with `rho=3/5`, the joint normalization `5/(8pi)`, exponent factor `25/32`, and quadratic `x1^2-(6/5)x1*x2+x2^2` are correct. With `b=4/5`, `X1|X2=b` has mean `12/25` and variance `16/25`; with `a=1`, `X2|X1=a` has mean `3/5` and the same variance. `phi(4/5)` is approximately 0.290 and `phi(1)` approximately 0.242. Both conditional curves integrate to one and have the displayed peak `5/(4 sqrt(2pi))`.

The positive-correlation contour major axis is at 45 degrees and the covariance eigen-axis lengths are proportional to `sqrt(1+rho)` and `sqrt(1-rho)`. Horizontal and vertical section routes, division by the corresponding marginal, and the zero-marginal regular-conditional-version warning agree with the current caption and adjacent V5-C04 text.

## Views actually opened

- complete physical page at 200 dpi and 300 dpi;
- figure plus caption at native 300 dpi / native 1x;
- native 300 dpi grayscale figure plus caption;
- object, semantic, text-span and candidate-pixel overlays;
- object-mask contact sheet;
- nearest-neighbor 8x ROIs for the joint slice/marker, both mean-guide peaks, notice/caption boundary, and lower mapping arrow versus geometry formula.

## Decision

`P632_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

Source changes: 0. TeX/LuaLaTeX/latexmk calls: 0. The existing source and official R110 PDF were read only.
