# FIG-P665-01 SA3 manual visible-object ledger

- Reviewer identity: `C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1`
- Review time (UTC): `2026-08-27T11:19:57.0244835Z`
- Frozen denominator: 22 reader-visible semantic objects, `O01` through `O22`.
- Views actually opened before this ledger: official-page native 300 dpi; figure+caption native 300 dpi; figure+caption native grayscale; object, semantic, text-measurement, and reading-order overlays; text and geometry masks; the closest-pair overlay; and every native1x/nearest8x ROI listed in `risk_roi_index_machine.csv`.
- R168 rule applied: small source-size, outline, or bbox/taxonomy differences are advisory. A hard defect requires missing/tofu/wrong codepoint or mathematics, unreadability, visibly severe imbalance, true clipping, illegal visible-ink overlap, or semantic/geometric error.

| ID | Manual disposition | Reviewer note from opened pixels and current source |
|---|---|---|
| O01 | CLEAR | Left title is complete, high-contrast, and visually subordinate only to the figure's two-panel structure; no clipping or glyph loss. |
| O02 | CLEAR | Density formula visibly contains the conditional bar, base measure, exponential, summation, natural parameter, sufficient statistic, and subtraction of `A(alpha)`; scripts remain distinct and the brace does not touch the ink. |
| O03 | CLEAR | The decomposition brace is continuous end to end, centered on the density formula, and neither clipped nor merged with formula or note ink. |
| O04 | CLEAR_WITH_R168_ADVISORY | The source's 8.5 pt annotation is below the older nominal value, but the native raster has 29 px full-height Chinese ink, reads cleanly at 1x, and remains intact at nearest8x; no hard readability defect. |
| O05 | CLEAR | Pale base-measure container is fully visible with rounded corners and functions as allowed background behind O06; it does not encode a conflicting foreground boundary. |
| O06 | CLEAR | `base measure` and `h(theta)=1_Delta^(K-1)(theta)` are complete; the indicator, simplex symbol, superscript, subscript, and parentheses are distinguishable in both decisive ROI scales. |
| O07 | CLEAR | Pale natural-parameter container is balanced with O05 and O09 and has no crop-edge or ink conflict. |
| O08 | CLEAR | `自然参数` and `eta_k=alpha_k-1` are legible; both `k` subscripts and the minus-one term are present and correctly associated. |
| O09 | CLEAR | Pale sufficient-statistic container is intact, centered below the upper pair, and does not crowd the panel divider or caption. |
| O10 | CLEAR | `充分统计量` and `T_k(theta)=log theta_k` are complete; both subscripts attach to the intended symbols and no character touches the container edge. |
| O11 | CLEAR | Vertical panel divider is continuous, light enough not to dominate, and separated from every reader object on both sides. |
| O12 | CLEAR | Right title is complete, aligned with O01, and establishes the second panel without codepoint or clipping defects. |
| O13 | CLEAR | `A(alpha)=sum_k log Gamma(alpha_k)-log Gamma(alpha_0)` shows both Gamma functions, the summation index, and the `alpha_0` total-concentration subscript correctly; no tofu or symbol substitution is visible. |
| O14 | CLEAR | Down arrow is complete, points from the log-partition formula to its derivative, and is separated from both neighboring formula inks. |
| O15 | CLEAR_AFTER_DECISIVE_ROI | Fraction `partial A / partial alpha_k` is intact. The sole machine logical-bbox risk against O16 was opened at native1x and nearest8x; foreground masks give 8 px center distance and 7 blank pixels, so no actual overlap or unreadable crowding exists. |
| O16 | CLEAR | Blue result container border is continuous on all four sides, not clipped, and leaves visibly ample internal space around O17. |
| O17 | CLEAR | Expected-log identity is complete: expectation brackets, `log`, capital Theta with subscript `k`, equality, both digamma terms, and `alpha_k/alpha_0` are all present and unambiguous. |
| O18 | CLEAR | Red warning container and pale fill are continuous and visually separated from O16 and the caption. |
| O19 | CLEAR | Noncommutation warning uses the correct `not equal` sign and preserves the distinct placement of logarithm and expectation on both sides; native and nearest8x views show no missing glyph. |
| O20 | CLEAR | Caption label `图 34.6` is complete, bold, and not fused with the following sentence. |
| O21 | CLEAR | Caption line 1 matches the displayed construction and reaches the phrase saying the derivative gives the result; mixed Chinese, Latin, and math symbols remain readable. |
| O22 | CLEAR | Caption line 2 contains the same expected-log identity as O17 and the warning that it cannot be replaced by log of the mean; no clipping, tofu, or line collision is visible. |

The denominator is closed at 22 objects. No unreviewed or unknown object ID remains.
