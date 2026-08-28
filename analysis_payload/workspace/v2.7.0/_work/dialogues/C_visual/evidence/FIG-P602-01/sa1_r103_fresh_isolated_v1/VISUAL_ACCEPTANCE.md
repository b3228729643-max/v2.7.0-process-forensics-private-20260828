# Visual acceptance

| Gate | Decision | Evidence-backed finding |
|---|---|---|
| complete page | PASS | Physical page 653 / printed 640 is intact at 200 and native 300 dpi. |
| figure crop | PASS | Figure, self-loop, and caption have positive outer margins; no true crop. |
| color | PASS | Blue/gray hierarchy is restrained and the main flow remains dominant. |
| grayscale | PASS | Solid, dashed, dash-dot, double-border, and light-fill roles remain distinguishable. |
| direct 1x | PASS | All 194 visible glyphs and 24 critical regions are actually readable. |
| nearest 8x | PASS | No hidden tofu, missing stroke, wrong codepoint, line-through-text, or pixel collision appears. |
| geometry | PASS | Six nodes, six directed relations, branch endpoints, and rejection self-loop are correctly placed. |
| formula semantics | PASS | Numerator is `pi_u(Y)q(X_t|Y)` and denominator is `pi_u(X_t)q(Y|X_t)` under positive forward flow. |
| object content | PASS | Proposal, calculation, decision, accept update, reject retention, and caption are complete. |
| chapter consistency | PASS | The figure matches chapter lines 269–305 and 617–627 on directed/common flow, alpha, rejection mass, and self-loop. |
| font hard gate under R168 | PASS | Missing/tofu/wrong glyph/codepoint, actual unreadability, severe visible imbalance, true clip, and true overlap are all absent. |
| pixel overlap | PASS | Illegal overlap 0; 115 raw shared pixels are exactly two permitted topology endpoints. |

R168 advisory-only observations do not alter the hard result: `T05` π and `u` have small measured ink boxes but are readable; `T13` machine run height includes nearby arrow pixels while direct cards show the same 9.6 pt label scale; peer ratios arise from glyph shape or legal derived scripts. No advisory observation independently triggers repair, reconstruction, or reseal.
