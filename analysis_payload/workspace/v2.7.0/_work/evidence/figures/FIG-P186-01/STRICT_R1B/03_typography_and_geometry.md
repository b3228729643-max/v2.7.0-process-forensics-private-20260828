# Typography and native geometry

## Text inventory and effective source sizes

| IDs | Elements | Effective source size | 9.5 pt gate |
|---|---|---:|---|
| T01--T03 | `w^T x+b>0`, `w^T x+b<0`, `w^T x+b=0` | 9.2 pt | FAIL |
| T04 | `w: 分数增大` | 9.2 pt | FAIL |
| T05--T06 | `x^(2)`, `x^(1)` | 9.5 pt | PASS |

The 9.2 pt declarations occur in the figure source styles for the base figure, direct labels, and normal label. This is below the required effective minimum of 9.5 pt; it alone blocks a PASS.

The native raster nevertheless resolves the relevant glyph categories clearly: lower-case math spans are 19 px, base `+` is 24 px, `>` is 23 px, `<` is 22 px, number `0` is 25 px, natural superscripts are 19--25 px, and the four CJK glyph cells in T04 are 34 px high. Thus the failure is the explicit source-point-size gate, not a rescaling judgement.

Same-role source ratios are 1.000 with zero point difference (all direct labels 9.2 pt; both axis labels 9.5 pt). There is one panel, so cross-panel checks are not applicable.

## Native geometry ledger

| Check | Native measurement | Requirement | Result |
|---|---:|---:|---|
| Region-fill to plot edge | 8.526 px | >=6 px | PASS |
| Separator endpoints to horizontal plot edge | 8.526 px | >=6 px | PASS |
| T03 text to visible separator | 1.000 px | >=3 px | FAIL |
| T04 text to normal-arrow | 20.000 px | >=3 px | PASS |
| T05 text to y-axis arrowhead | 32.202 px | >=3 px | PASS |
| T06 text to x-axis arrowhead | 27.203 px | >=3 px | PASS |
| Minimum text-to-text gap (T03/T06) | 111.328 px | >=4 px | PASS |
| Five blue disk size ratio | 1.0000 x 1.0000 | [0.92, 1.08] | PASS |
| Five teal triangle size ratio | 0.9600 x 0.9545 | [0.92, 1.08] | PASS |

The T03 result is evaluated on the 1:1 native RGB grid. Its semitransparent white label field leaves separator pixels/antialias coverage only 1 px from the boundary-label foreground. This is a clearance failure, even though no unmasked glyph-on-glyph overlap was observed. `roi/boundary_label_native_1x.png` is the corresponding key ROI.

There are no drawn node borders to which the 5 px node-text rule applies; the figure has a single panel, so cross-panel spacing and size ratios are N/A. No separate interval/margin line beyond the separator is present.

The detailed machine-readable results are in `metrics/text_element_audit.csv`, `metrics/text_glyph_spans_native.csv`, `metrics/native_color_components.csv`, and `metrics/geometry_ledger_native.csv`.
