# FIG-P689-01 R115 SA3 fresh isolated manual object ledger

HANDOFF_ID: C-FIG-P689-01-R115-SA3-FRESH-ISOLATED-V1

Canonical instance: /root/sa3_fig_p689_r115_fresh_isolated_v1

Observation basis: official R115 physical page 739 (printed page 726), opened at full-page 200 dpi and 300 dpi; native 300 dpi figure-only and figure-plus-caption crops; native grayscale; text, semantic, and object overlays; and all seven selected critical ROIs at native1x and nearest8x.

Denominator rule: the complete reader-visible semantic foreground of Figure 35.5 plus its caption is frozen below. Uniform pale fills are background and are not independent foreground objects. Adjacent body prose is evaluated in the page-integration ledger but is outside the figure-plus-caption pair denominator.

DENOMINATOR_N: 33

UNORDERED_PAIR_COUNT_C: 33*32/2 = 528

R168 application: the source-level 9.0 pt and 9.2 pt declarations and vector spans around 8.97--9.27 pt are advisory numeric facts. Hard failure was assessed only from actual missing/tofu/wrong glyph or math, unreadability/obvious imbalance, true clipping, confirmed illegal visible-ink overlap, or semantic/geometric/math error. None was observed.

| ID | Category | Reader-visible object | Post-observation finding | Manual verdict |
|---|---|---|---|---|
| O01 | PANEL_BORDER | Left rounded panel border | Continuous, fully visible, ample inset from all text; no clipping. | CLEAR |
| O02 | TEXT | “证据的长度分解” | Correct glyphs; bold hierarchy balanced; vector 10.909 pt; measured ink 43 px. | CLEAR |
| O03 | LINE_ARROW | Bidirectional log-evidence arrow | Both arrowheads intact; clear of O04 and O05. | CLEAR |
| O04 | FORMULA | `log p(w)` above arrow | Correct italic math glyphs; vector 9.166 pt; measured ink 38 px; no collision. | CLEAR |
| O05 | NODE_BORDER | ELBO/KL decomposition bar border | Complete rectangle; contains labels with generous clearance. | CLEAR |
| O06 | LINE | Bar divider | Meets O05 at intended border junctions only; does not touch text. | INTENDED_CONTACT_CLEAR |
| O07 | TEXT_FORMULA | `L(q): 证据下界` | Calligraphic L and Chinese glyphs correct; vector 9.166 pt; measured ink 39 px. | CLEAR |
| O08 | TEXT | `KL 间隙` | Latin and Chinese glyphs correct; vector 9.166 pt; measured ink 33 px; balanced against O07. | CLEAR |
| O09 | FORMULA | Log-evidence/ELBO/KL identity | `log p(w)=L(q)+KL(q(h)∥p(h∣w))` renders with correct relation and conditional bars; vector 9.166 pt; measured ink 38 px. | CLEAR |
| O10 | TEXT_FORMULA | KL inequality annotation, line 1 | `KL≥0` and `L(q)≤log p(w)` correct; vector about 9.07--9.17 pt; measured ink 39 px. | CLEAR |
| O11 | TEXT | KL inequality annotation, line 2 | Correct Chinese continuation; vector 9.166 pt; measured ink 37 px; line spacing is comfortable. | CLEAR |
| O12 | PANEL_BORDER | Right rounded panel border | Continuous and fully visible; no axis, title, or data clipping. | CLEAR |
| O13 | TEXT | “坐标更新下的 ELBO 非降阶梯” | Correct mixed Chinese/Latin glyphs; bold hierarchy balanced with O02; vector 10.909 pt; measured ink 43 px. | CLEAR |
| O14 | LINE_ARROW | x axis | Baseline and arrowhead intact. Axis-origin and tick attachments are intended graph structure. | INTENDED_CONTACT_CLEAR |
| O15 | LINE_ARROW | y axis | Shaft and arrowhead intact; meets x axis, reference line, first data point, and zero tick only as intended coordinate geometry. | INTENDED_CONTACT_CLEAR |
| O16 | LINE | x tick marks group | Seven ticks present and aligned to 0--6; intended attachment to x axis only. | INTENDED_CONTACT_CLEAR |
| O17 | TEXT | x tick label 0 | Correct codepoint; vector 9.265 pt; measured ink 27 px; clear of axis/tick. | CLEAR |
| O18 | TEXT | x tick label 1 | Correct codepoint; vector 9.265 pt; measured ink 26 px; clear of axis/tick. | CLEAR |
| O19 | TEXT | x tick label 2 | Correct codepoint; vector 9.265 pt; measured ink 26 px; clear of axis/tick. | CLEAR |
| O20 | TEXT | x tick label 3 | Correct codepoint; vector 9.265 pt; measured ink 27 px; clear of axis/tick. | CLEAR |
| O21 | TEXT | x tick label 4 | Correct codepoint; vector 9.265 pt; measured ink 26 px; clear of axis/tick. | CLEAR |
| O22 | TEXT | x tick label 5 | Correct codepoint; vector 9.265 pt; measured ink 27 px; clear of axis/tick. | CLEAR |
| O23 | TEXT | x tick label 6 | Correct codepoint; vector 9.265 pt; measured ink 27 px; clear of axis/tick. | CLEAR |
| O24 | TEXT | “坐标更新轮次” | Correct Chinese glyphs; vector 8.966 pt; measured ink 32 px; centered and readable. | CLEAR_R168_ADVISORY |
| O25 | DATA_REFERENCE | Dashed unknown-upper-bound line | Continuous dashed coding, distinct from solid step curve in color and grayscale; meets y axis at intended reference origin. | INTENDED_CONTACT_CLEAR |
| O26 | TEXT | “未知全局上限” | Correct glyphs; vector 8.966 pt; measured ink 32 px; clear of dashed line and y axis. | CLEAR_R168_ADVISORY |
| O27 | DATA_CURVE | Nondecreasing ELBO step curve | Seven values form a nondecreasing staircase with no descending segment; starts on y axis by coordinate definition. | INTENDED_CONTACT_CLEAR |
| O28 | MARKER | Seven update markers | All seven markers intact and centered on O27; first marker lies on y axis as intended. | INTENDED_CONTACT_CLEAR |
| O29 | TEXT | “坐标稳定／局部驻点” | Correct fullwidth slash and Chinese glyphs; vector 8.966 pt; measured ink 33 px; visibly separated from curve and markers. | CLEAR_R168_ADVISORY |
| O30 | TEXT | Caption label “图 35.5” | Bold label and decimal number correct; vector about 9.96--10.06 pt; measured ink 38 px; no tofu or clipping. | CLEAR |
| O31 | TEXT | Caption line 1 | Complete and readable; vector about 9.96--10.06 pt; measured ink 37 px; consistent with source. | CLEAR |
| O32 | TEXT | Caption line 2 | Complete and readable; vector about 9.96--10.06 pt; measured ink 41 px; line break is natural. | CLEAR |
| O33 | TEXT | Caption line 3 | “全局最优证明” complete; vector 9.963 pt; measured ink 35 px; no clipping. | CLEAR |

Manual denominator conclusion: all 33/33 objects were individually observed after evidence opening. No object is missing, unreadable, wrongly encoded, clipped, semantically wrong, or obviously imbalanced.
