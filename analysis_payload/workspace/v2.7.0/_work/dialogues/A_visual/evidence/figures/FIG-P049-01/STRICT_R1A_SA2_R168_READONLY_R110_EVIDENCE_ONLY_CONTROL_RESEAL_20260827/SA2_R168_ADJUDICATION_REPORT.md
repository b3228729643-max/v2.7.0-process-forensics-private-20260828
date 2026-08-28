# FIG-P049-01 — R110 read-only SA2 adjudication under R168

## Result

- `RESULT`: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
- `HARD_DEFECT_COUNT`: `0`
- `SOURCE_CHANGE_REQUESTED`: `false`
- `HANDOFF_ID`: `A-R110-P049-SA2-R168-READONLY-20260827`
- `ROLE`: `SA2 read-only adjudicator`
- `MODEL`: `gpt-5.6-sol`
- `REASONING_EFFORT`: `xhigh`
- `FIGURE_ID`: `FIG-P049-01`
- `CANDIDATE`: `R110 frozen current candidate`
- `PDF_PHYSICAL_PAGE`: `48`
- `PRINTED_PAGE`: `35`

## Immutable identities checked at startup

- Evidence root did not exist before startup:
  `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R1_SA2_R168_READONLY_R110_20260827`
- Current figure source:
  `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C03\fig_v1_c03_gradient_contour.tex`
  - bytes: `4189`
  - SHA-256: `F9D4040ABB708F8043C619FB8C59B9CCCFDB2938E1BBD54B03B1E5D940F2999C`
- Official R110 PDF:
  `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf`
  - bytes: `4967063`
  - pages: `817`
  - SHA-256: `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`

## Isolation and method

- Only the named R110 PDF, current figure source, root `GOAL.md`, directly applicable strict figure-protocol sections, and the necessary current `V1-C03.tex` context were used.
- No prior P049 evidence, conclusion, role output, handoff, state, inventory, chat, Git conclusion, main-acceptance conclusion, second UID, or second role was consulted.
- No source, PDF, Git, central state, or inventory file was modified. No TeX engine or `latexmk` was run.
- Fig. 3.1 was independently located from the R110 PDF text layer on physical page 48. The page was rendered directly by Poppler at 200 dpi and 300 dpi; a native 300 dpi figure crop and native 300 dpi grayscale crop were manually opened and inspected. A native 600 dpi detail was used only to inspect the right-angle and guide-line cluster.
- R168 adjudication was applied: old font-size, pixel-height, micro-clearance, and micro-outline thresholds were treated as advisory. A hard failure was reserved for missing/tofu/wrong codepoints, mathematical-semantic failure, actual unreadability or obvious imbalance, real clipping, illegal overlap, or geometric/semantic error.

## Independent manual observations

### Rendering, legibility, and page integration

- The complete page and figure are present. No text, formula, arrowhead, marker, contour, axis, caption, or adjacent paragraph is clipped.
- No tofu, missing glyph, or wrong-codepoint symptom is visible. The R110 text layer extracts the labels and formula consistently, including `∇f(P)`, `v_tan`, and `∇f(P)^T v_tan = 0`; fonts used on physical page 48 are embedded and Unicode-mapped.
- The note column, contour panel, caption, and following paragraph remain legible at page scale. The figure is visually balanced on the page and does not crowd the following example.
- No illegal overlap is visible. Intended contacts are the point on its contour, the gradient/tangent origins at the point, and the right-angle construction touching its two rays. Guide leaders do not obscure label ink or change a mathematical object.
- In the native grayscale crop, the three contour levels remain separable by solid/dashed/dash-dot encoding; the gradient, tangent, axes, point, right-angle marker, and note leaders remain distinguishable without color.

### Geometry and mathematical semantics

- The displayed function is `f(x_1,x_2)=x_1^2/9+x_2^2/3.24` and the displayed point is `P=(2.4,1.08)`.
- `f(P)=2.4^2/9+1.08^2/3.24=0.64+0.36=1`, so `P` lies on the outer displayed level curve. The source radii give levels `0.25`, `0.64`, and `1.00`, consistent with the labels and `c_1<c_2<c_3`.
- `∇f(P)=(2(2.4)/9,2(1.08)/3.24)=(0.533333...,0.666666...)`. The drawn gradient displacement is `G-P=(0.72,0.90)=1.35∇f(P)`, so its direction and increasing-function sense are correct.
- The tangent endpoints have midpoint `((1.46+3.34)/2,(1.83+0.33)/2)=(2.4,1.08)=P`, so the tangent passes through `P`.
- With the rounded source tangent displacement `T-P=(0.94,-0.75)`, `∇f(P)·(T-P)=0.001333...` and the angle is `89.92559°`. This approximately `0.07441°` deviation is solely the visible-coordinate rounding of the plotted tangent and is not a perceptible or semantic loss of orthogonality. The right-angle marker is present at `P` between the tangent and positive-gradient rays.

### Guide-line semantics

- Guide 1 starts at “定位 P 所在等值线” and converges on the `P`/outer-contour construction. Its source endpoint `(2.75,1.36)` is offset from the point ink rather than literally drawn onto the contour, but the native crop shows an unambiguous local target and no contradictory geometric assertion.
- Guide 2 ends at `G`, the head of the positive gradient arrow, matching “梯度指向函数增大”.
- Guide 3 converges on the right-angle/point cluster, matching `∇f(P)^T v_tan=0`.
- The guides preserve the intended reading order 1 → 2 → 3 and do not redirect any note to an incompatible object. Therefore no R168 hard guide-line semantic defect is present.

### Labels, caption, and current text consistency

- Figure labels use `P`, `∇f(P)`, `v_tan`, `x_1`, `x_2`, `c_1<c_2<c_3`, the displayed function, and “f 增大” consistently.
- The caption states that the arrow at the point is perpendicular to the local tangent and points toward increasing function values; the drawing supports both claims.
- The current adjacent `V1-C03.tex` text states `∇f^T v_tan=0` and distinguishes the tangent vector from the normalized steepest-ascent direction `u_max=∇f/||∇f||_2`. This agrees with the figure and avoids symbol reuse.

## R168 advisory observations

- The source declares visible roles at `8.8pt`, `9.2pt`, and `9.4pt`, which would fall below older strict source-size thresholds. Under the assigned R168 rule these values alone are advisory, not a hard failure.
- Manual inspection of the native page and native 300 dpi crop found no actual unreadability or obvious role imbalance caused by those declarations.

## Decision

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`.

No narrow source change is justified under R168. This is a sealed SA2-only conclusion and is not a fresh SA1 result or a final/main acceptance. The required next action is a fresh, independently isolated SA1 review of the same frozen R110 PDF and the same source identity.
