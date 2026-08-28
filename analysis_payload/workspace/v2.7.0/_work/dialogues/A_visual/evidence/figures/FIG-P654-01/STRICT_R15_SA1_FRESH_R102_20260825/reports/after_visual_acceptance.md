# FIG-P654-01 R102 fresh SA1 visual acceptance

- VERDICT: `SA1_FAIL_TO_SA2`
- PDF/physical/printed: R102 / 704 / 691
- SOURCE_FONT_PASS: true
- PIXEL_HEIGHT_PASS: true
- SAME_CLASS_RATIO_PASS: false
- ROLE_RATIO_PASS: true
- OVERLAP_PIXEL_COUNT: 0
- CLIP_PIXEL_COUNT: 0
- PIXEL_ADJUDICATION_STATUS: CLEAR
- FONT_VISUAL_HARMONY_PASS: true
- MATH_SEMANTICS_PASS: true
- TEXT_CONSISTENCY_PASS: true
- GRAYSCALE_PASS: true
- PAGE_INTEGRATION_PASS: true

The diagram is visually coherent, semantically consistent, unclipped, and has no illegal native-pixel overlap. It nevertheless fails the frozen strict D/E same-panel same-role/script glyph-to-median gate; visual harmony cannot override that hard failure.

## Exact hard failures

- `G0005` `𝑛` in `N_TRIAL_FORMULA`: H=22px, frozen median=24.0px, ratio=0.916666666667, allowed [0.92,1.08].
- `G0014` `t` in `N_GAMMA_BODY_1`: H=27px, frozen median=22.0px, ratio=1.227272727273, allowed [0.92,1.08].
- `G0042` `+` in `N_POSTERIOR_FORMULA`: H=29px, frozen median=24.0px, ratio=1.208333333333, allowed [0.92,1.08].
- `G0061` `+` in `N_PREDICTIVE_FRAC_NUM`: H=29px, frozen median=24.0px, ratio=1.208333333333, allowed [0.92,1.08].
- `G0066` `+` in `N_PREDICTIVE_FRAC_DEN`: H=29px, frozen median=24.0px, ratio=1.208333333333, allowed [0.92,1.08].
- `G0067` `𝑁` in `N_PREDICTIVE_FRAC_DEN`: H=33px, frozen median=24.0px, ratio=1.375000000000, allowed [0.92,1.08].

## Denominators

- glyph/graphic/object: 95/21/116
- all unordered pairs: 6670
- critical pairs with native 1x/8x evidence: 121
- manual glyph/graphic/pair/view rows: 95/21/6670/5
- low-profile punctuation/calibration: 0/0 (closed N/A, not silently omitted)
