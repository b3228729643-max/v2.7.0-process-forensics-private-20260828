# FIG-P670-01 fresh isolated SA3 semantic review

HANDOFF_ID: C-FIG-P670-01-R114-SA3-FRESH-ISOLATED-V1

UID: FIG-P670-01

Reviewer instance: /root/sa3_fig_p670_r114_fresh_isolated_v1

Actual model/reasoning: gpt-5.6-sol / xhigh

Observed current candidate: official R114 PDF, physical page 717, printed page 704.

## Images actually opened before this review was written

- `full_page_200dpi.png`
- `figure_caption_crop_native_300dpi.png`
- `grayscale_figure_caption_300dpi.png`
- `semantic_object_overlay_300dpi.png`
- all seven `ROI*_native1x_300dpi.png` files
- all seven `ROI*_nearest8x.png` files

## Posterior-predictive semantics

The displayed formula

`P(Y_(N+1)=k | n) = (alpha_k+n_k)/(alpha_0+N)`

is the correct Dirichlet-categorical posterior-predictive probability after integrating out theta. The left pseudo-count vector `(4,3,2)` totals 9, and the displayed probabilities `4/9, 3/9, 2/9` sum to 1.

The observation is `j=2`. Only the second component is incremented, so `(4,3,2)` becomes `(4,4,2)` and the total becomes 10. The displayed update equations `n_2 <- n_2+1` and `alpha_0+N <- alpha_0+N+1` agree with the token transition. The right probabilities `4/10, 4/10, 2/10` also sum to 1.

The newly added class-2 token is shown by hatching inside the fourth gold token. The matching hatched increment in the second probability-bar segment lies to the right of the `4/10` text and does not obscure it.

The statement that integrating out theta yields an exchangeable sequence but not an iid sequence conditional on one fixed parameter is mathematically appropriate: observations are conditionally iid given theta, while the marginal Polya-urn sequence after integrating theta is exchangeable and dependent.

## Arrows and geometry

The reading direction is unique and left-to-right: current pseudo-counts and predictive distribution, observation `j=2`, then updated pseudo-counts and predictive distribution. Both arrowheads point right. Arrow ink does not pass through any label, token, probability number, formula, or caption. The node connector at the observation circle is intentional and does not create an illegal foreground collision.

All 19 token circles are complete and mutually distinct. Every digit is centered and clear of its circle border. Probability-bar dividers remain outside numeric glyph ink. The summary box and caption are uncut.

## Caption and necessary body context

The PDF text layer contains the complete caption exactly once. Its conclusion matches the figure: pseudo-count proportions give the posterior predictive probability; observing class `j` increments that class; the sequential reinforcement is exchangeable after integrating theta but is not a fixed-parameter iid sequence.

The immediately following example on the same page uses the same Dirichlet-multinomial update pattern and states that the posterior mean is also the next-observation predictive vector. This context is consistent with the figure and introduces no contradictory convention.

## R168 application

Source declarations include 8.5pt, 8.8pt, 9.2pt and 9.8pt roles. Under R168 those inherited numeric thresholds are advisory and cannot independently create a hard failure. The current PDF was therefore judged on actual glyph integrity, correct codepoints, mathematical meaning, readability, balance, clipping and illegal visible-ink overlap. All visible text remains readable in native 300dpi, grayscale, native1x and nearest8x evidence. The measured minimum visible-ink gap is 1 px at a probability fraction near the colored bar frame; the ink remains disjoint and clearly readable, so this advisory number is not a hard failure.

## Manual outcome

All 63 frozen visible objects were reviewed by ID after the images were opened. All 45 bbox-near/intersection candidates were reviewed after image opening; none is a true visible-ink collision. No object is missing, tofu, wrong-codepoint, clipped, semantically wrong, geometrically misleading, or severely unbalanced.

Verdict: PASS
