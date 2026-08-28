# FIG-P683-01 post-observation manual object adjudication

This file was written only after the reviewer actually opened the R115 full-page 200 dpi, full-page 300 dpi, full-page grayscale 300 dpi, native figure-plus-caption crop, semantic overlay, object overlay, text overlay, and all ten selected critical ROIs at native 1x and nearest-neighbor 8x. Numeric legacy thresholds are treated as advisory under R168; the manual hard-defect questions are missing/tofu/wrong codepoint, actual unreadability or severe imbalance, true clipping, confirmed illegal visible-ink overlap, and semantic/geometric/mathematical error.

Denominator: the current source contains 18 reader-visible TikZ `node` constructs and 5 reader-visible directed `draw` constructs. Therefore `N=23` and the unordered-pair universe is `C(23,2)=253`. The caption is audited as page text in the native crop and text overlay; it is not a TikZ graph object and is therefore outside this graph-object denominator.

| ID | Post-observation manual judgment |
|---|---|
| O01 | `alpha` renders as the intended mathematical alpha, with no tofu, substitution, clipping, or confusion with Latin `a`; it is visibly outside the M plate and has clear space before the dependency line. |
| O02 | `theta_m` is the intended latent document-topic vector node: correct theta and subscript `m`, unfilled latent styling, readable at page scale, inside M but outside N, with clean incoming/outgoing border attachments. |
| O03 | `z_mn` is the intended latent position-topic assignment node: correct `z` with `mn` subscript, unfilled latent styling, readable, nested inside both N and M plates, and cleanly attached to its two horizontal dependencies. |
| O04 | `w_mn` is the intended observed word node: correct `w` and `mn` subscript in white on the filled observed node, readable in color and grayscale, inside N and M, with two distinct incoming arrowheads meeting the border without obscuring text. |
| O05 | `beta` renders as the intended mathematical beta, with no tofu, wrong codepoint, clipping, or ambiguity; it is outside all plates and separated from its outgoing line. |
| O06 | `varphi_k` renders as the intended topic-word probability vector symbol and subscript `k`, not an unknown glyph; the latent styling, K-plate containment, incoming beta edge, and outgoing edge are all clear. |
| O07 | The N_m plate is a complete rounded dashed boundary enclosing exactly `z_mn` and `w_mn`; it is nested in M, is not clipped, and its label remains clear above it. |
| O08 | The M plate is a complete rounded dashed boundary enclosing `theta_m` and the entire N_m plate; intended dependency lines cross its boundary without masking labels or nodes. |
| O09 | The K plate is a complete rounded dashed boundary enclosing only `varphi_k`; it is geometrically separate from M/N and its label is legible below. |
| O10 | `N_m 个词位` is present with the correct mathematical N, subscript m, and Chinese text; it is readable, balanced, and does not touch the N or M plate border. |
| O11 | `M 篇文档` is present with the correct M and Chinese text; it sits below the M plate with clear separation from the diagonal dependency and caption. |
| O12 | `K 个主题` is present with the correct K and Chinese text; it sits below the K plate without clipping or overlap. |
| O13 | The observed-variable legend swatch is a filled blue circle matching O04; its shape is complete in color and grayscale and does not touch the legend text. |
| O14 | `观测变量` is fully rendered with the intended Chinese codepoints, readable and aligned with O13; no clipping or missing initial glyph is present in the native image. |
| O15 | The latent-variable legend swatch is an unfilled teal circle matching O02/O03/O06; it is complete and visually distinct from O13 in color and grayscale. |
| O16 | `潜变量` is fully rendered with the intended Chinese codepoints, readable and aligned with O15, with no clipping or tofu. |
| O17 | The legend glyphs `alpha,beta` are correct mathematical Greek codepoints, readable in gray, and visibly separated from the explanatory text. |
| O18 | `超参数（plate 外）` is complete, readable, and accurately states that O01/O05 are outside plates; Latin `plate` and Chinese parentheses/text render correctly. |
| O19 | The directed alpha-to-theta dependency points from the external hyperparameter to the latent document vector. Its M-plate boundary crossing and theta-border endpoint are intentional structural junctions, not illegal collisions. |
| O20 | The directed theta-to-z dependency has the correct direction. Its N-plate boundary crossing and node-border endpoints are intentional and leave both labels unobscured. |
| O21 | The directed z-to-w dependency has the correct direction and stays inside N/M. Its arrowhead terminates cleanly at O04 without touching the `w_mn` ink. |
| O22 | The directed beta-to-varphi dependency has the correct direction. Its K-plate boundary crossing and O06 border endpoint are intentional and do not obscure either glyph. |
| O23 | The directed varphi-to-w dependency has the correct direction for complete-Bayes LDA. It intentionally exits K and enters M/N, crosses only plate borders, meets O04 at a distinct lower-left border point, and does not mask labels or node text. |

Manual object conclusion: all 23 source-visible graph objects are present, readable, unclipped, semantically correct, and free of confirmed illegal visible-ink overlap. Intended node-border attachments and intended plate-boundary crossings are structural, not defects.
