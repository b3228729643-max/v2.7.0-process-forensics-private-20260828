# FIG-P157-01 root final acceptance — R93 / R6

ROOT_RESULT: STRICT_PASS

- Frozen official input: `strict_current_r93_fullbook/main_full.pdf`, physical PDF page 170, printed page 157, 图 10.1.
- Independent role chain is complete: corrected official-R93 SA1 R5 PASS, isolated official-R93 SA3 R6 PASS, followed by this root evidence review. Superseded contaminated prepasses are not acceptance evidence.
- Root recomputed the SA3 aggregates: source-font 12/12 PASS with effective size 9.856--11.200 pt; native-300-dpi pixel rows 12/12 PASS, CJK minimum 36 px and caption digit minimum 27 px; all same-class ratios pass. Axis-title-to-base ratios 1.108--1.135 are inside the Goal's dedicated axis-title interval [1.00,1.18].
- Root parsed all 210 SA3 object-pair rows: 210 PASS, zero positive final-mask overlap and zero illegal overlap. The closest independent text--graphic pair is `P157-T03__P157-G09` at 15 px, above the 3 px requirement. The closest independent text--text PDF/vector bbox clearance is 35 px, above the 4 px requirement.
- Root parsed 27 edge/clip rows: 27 PASS and total clip count 0.
- Root opened the native 300 dpi figure crop, standalone/grayscale/text-overlay views, the full-page integration view, and the 1:1 raw/overlay evidence for the limiting pair and the intentional training/validation-curve junction. No label, formula, line, marker, axis, caption, or page-flow collision remains; font size is readable and visually subordinate to the curves.
- Mathematical semantics, caption/body consistency, reading order, grayscale encoding and page integration are consistent with the source and adjacent text.

Disposition: `FIG-P157-01` is closed as `STRICT_PASS`. It is counted as the fourth strict-final figure, after P020, P632 and P756. Reopen only if its source or an affecting shared style changes.
