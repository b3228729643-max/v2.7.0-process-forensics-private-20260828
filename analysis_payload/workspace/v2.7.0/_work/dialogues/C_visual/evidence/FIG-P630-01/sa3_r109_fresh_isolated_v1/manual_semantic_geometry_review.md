# Independent semantic and geometry review

## Views actually opened

1. `r109_p680_full_native300dpi.png`
2. `r109_p680_full_200dpi.png`
3. `r109_p680_figure_caption_native300dpi.png`
4. `r109_p680_figure_caption_grayscale_native300dpi.png`
5. `r109_p680_semantic_object_overlay_native300dpi.png`
6. `r109_p680_text_measurement_overlay_native300dpi.png`
7. `r109_p680_page_integration_overlay_200dpi.png`
8. `r109_p680_critical_rois_native1x.png`
9. `r109_p680_critical_rois_nearest8x.png`

## Visible-object denominator

The complete semantic denominator is 17 objects: nine composite labeled nodes/banners (`O01`-`O09`), five directed flow arrows (`O10`-`O14`), two non-arrow leader lines (`O15`-`O16`), and the figure number plus caption (`O17`). The denominator intentionally treats each labeled node as one semantic composite; its constituent text is separately closed by the 26-element font/pixel audit. This yields exactly C(17,2)=136 unordered object pairs, all present in `after_overlap_report.csv` with a manual per-ID observation.

## Mathematical semantics and reading order

The directed main chain is correct and complete:

`联合目标 / 局部因子` -> `给定 x_{-j} 的满条件 pi_j(dot | x_{-j})` -> `单坐标核 K_j，只更新 x_j` -> `扫描核（系统 / 随机）` -> `相关样本` -> `诊断（MCSE / ESS / 轨迹）`.

All five arrowheads face the intended downstream object. The two gray leader segments have no arrowheads, so the correctness and mixing-efficiency callouts are visually distinguished from the computational chain. This agrees with the adjacent current chapter text, which states that the arrows encode learning/computational dependence rather than probabilistic generation time.

The formulas and labels are semantically correct: `x_{-j}` denotes all other coordinates; `pi_j(dot | x_{-j})` is the j-th full conditional; `K_j` is the single-coordinate Gibbs kernel; and `x_j` is the only updated coordinate. `MCSE`, `ESS`, and trajectory diagnostics are correctly downstream of correlated samples. The boundary statement uses a true not-equal operator and correctly warns that a target-preserving kernel does not imply fast mixing.

No missing node, missing edge, reversed edge, wrong subscript, wrong codepoint, tofu glyph, or semantic ambiguity is visible.

## Geometry, collision, clipping, and readability

The core nodes form a stable 3-by-2 chain with straight noncrossing arrows. Node padding is ample; ordinary labels are centered and no arrow or leader approaches text ink. The two callouts remain secondary, connected only to their intended core node. The synthesis banner is separated from the chain and caption. The caption is one line, fully visible, and consistent with both diagram and adjacent prose.

The native 300 dpi crop and nearest8x ROIs show complete arrowheads, continuous rounded borders, distinct minus and not-equal strokes, and fully formed subscripts. The tightest reader-text gap is exactly 4 pixels between the two full-conditional lines; it meets the text-text minimum. No semantic foreground objects share illegal pixels. No element is clipped at the page, figure, node, or caption boundary.

## Font, pixel, class, and role balance

All ordinary figure text is unscaled source-level 9.6 pt; the synthesis banner is 10.0 pt bold. The caption renders at 9.963 pt. Natural TeX scripts render at 6.695 pt from compliant 9.6 pt bases and measure 28-29 ink pixels, above the 15 px script threshold. Chinese ordinary labels measure 34-36 ink pixels around a 35 px median. Mixed math/CJK line boxes measure 47-48 pixels because scripts extend the full line bbox; the primary glyph scale remains the same as neighboring labels.

Same-class ordinary variation is at most 1.029, and math-script variation is at most 1.036. The synthesis emphasis is only 1.042x the 9.6 pt node base and is semantically justified. No label dominates the flow. The 1 px outline differences recorded for a few CJK/math glyphs are R168-advisory raster variation, not unreadability or imbalance.

## Grayscale and page integration

In grayscale, the chain, callouts, banner, arrowheads, and caption remain distinct without relying on hue. On the full 200 dpi page, the diagram sits between the chapter map and the explicit reading-order paragraph with sufficient whitespace; it neither crowds adjacent prose nor appears detached. Figure number and caption alignment are stable.

## Independent conclusion

No hard failure was found under the R168 decision boundary. The SA3-only result is `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`.
