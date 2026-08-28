# Source font and scaling audit

Reviewer: `A-R110-P582-SA1-FRESH-ISOLATED-20260827`

The only audited source is the frozen mainline file `fig_v5_c02_running_mean.tex` with SHA-256 `989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57`.

| Source scope | Declared size | PDF-reported base size | D/E | Manual result |
|---|---:|---:|---:|---|
| `slfig-FIG-P582-01` default nodes | 9.5 pt / 11.4 pt leading | 9.46451 pt | 1.00375 | PASS; the 0.03549 pt renderer delta is advisory under R168 |
| axis tick labels | 9.5 pt / 11.4 pt | 9.46451 pt | 1.00375 | PASS |
| axis labels | 9.6 pt / 11.5 pt | 9.56414 pt | 1.00375 | PASS |
| equation and all three trend annotations | 9.5 pt / 11.4 pt | 9.46451 pt | 1.00375 | PASS |
| truth and four running-value annotations | 9.5 pt / 11.4 pt | 9.46451 pt | 1.00375 | PASS |
| caption | no local size override in the frozen figure source | 9.96264 pt base; 8.96638 pt natural scripts | N/A | PASS from final-PDF visible evidence |

No `tiny`, `scriptsize`, `footnotesize`, `small`, `large`, `resizebox`, `scalebox`, `scale=`, or `transform shape` override occurs in the source. The `width=10.2cm` and `height=5.6cm` settings size the pgfplots geometry and do not transform the declared text nodes. Natural subscripts/superscripts are the only smaller formula glyphs; their measured ink heights are 19-23 px in the plot equation and 28-33 px in the caption.

Within-role source sizes are identical except the intentional 9.6 pt axis-label versus 9.5 pt ordinary-label distinction. Observed same-role ink medians remain within the `[0.92,1.08]` band: ticks and running-value digits have extreme median ratio `27/26=1.0385`; the three CJK trend labels have extreme median ratio `35/34=1.0294`. The rotated y-axis title is marked directionally incomparable rather than forced into a cross-orientation height ratio.

The sole old-grid exception is the complete equals sign in `h(U_i)=U_i^2`: its own two-rule ink height is 12 px. It is neither missing nor malformed, and the formula is immediately readable in color, grayscale, and full-page views. Per the task's explicit R168 rule, this is recorded as an advisory rather than a hard failure.
