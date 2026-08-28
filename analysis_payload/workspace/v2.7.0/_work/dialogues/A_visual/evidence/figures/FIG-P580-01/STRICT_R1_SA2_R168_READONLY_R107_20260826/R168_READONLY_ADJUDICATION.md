# FIG-P580-01 R107 R168 SA2 read-only adjudication

- HANDOFF_ID: `A-R107-P580-SA2-R168-READONLY-20260826`
- Candidate: R107, physical page 630, printed page 617, figure 31.6.
- Source SHA-256: `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161`.
- Source changes: none. TeX invocations: zero.

## Independent current observation

The full page, 300 dpi figure crop, standalone crop, grayscale crop, native glyph crops, and nearest-neighbour 8x review crops were actually opened. The two panels, axes, curves, q-support guides, endpoint and evaluation markers, support hatching, formula card, labels, and caption are clear. No visible object is clipped, no formula or label is involved in a true collision, and no mark is unreadable or obviously out of scale.

The left title contains a visible STIXTwoMath U+0338 overlay and an intact U+226A; the caption contains another intact U+226A. Both relations preserve the intended mathematics. There is no tofu or replacement character.

All visible explicit source font sizes are 9.6 pt or 10.2 pt, so the source minimum is 9.6 pt, above the 9.5 pt requirement. No resize, scale, or transform-shape mechanism is present.

## Semantic and numerical cross-check

For `p(x)=6x(5-x)/125` on `[0,5]`, direct integration gives 1. For `q_L=(2/5)1_[0,5/2]` and `q_R=1/5` on `[0,5]`, both integrals are 1. Because q_L vanishes on `(5/2,5]` while p is positive there, `p` is not absolutely continuous with respect to q_L. Because q_R is positive throughout the common domain, `p` is absolutely continuous with respect to q_R.

The displayed ratios also recompute exactly: `p(1)/q_R(1)=24/25`, `p(5/2)/q_R(5/2)=3/2`, and `p(4)/q_R(4)=24/25`. These definitions, support statements, ratios, and the caption agree with the current V5-C02 body.

## R168 verdict

Hard failures are zero. Any residual native-pixel contour, mask, taxonomy, or peer-ratio variation is advisory under R168 and does not justify a source edit or a new build.

**Decision: `P580_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`.**
