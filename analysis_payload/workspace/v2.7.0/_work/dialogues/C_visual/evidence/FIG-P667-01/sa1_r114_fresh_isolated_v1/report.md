# FIG-P667-01 — fresh isolated R114 SA1 report

HANDOFF_ID = C-FIG-P667-01-R114-SA1-FRESH-ISOLATED-V1  
UID = FIG-P667-01  
INSTANCE = /root/sa1_fig_p667_r114_fresh_isolated_v1  
SA1_MODEL = gpt-5.6-sol  
SA1_REASONING = xhigh

## Input identity and independent location

The official PDF identity is 4,967,122 bytes with SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`. The current figure source identity is 3,252 bytes with SHA-256 `1E2D755428EC466C6DF44B7684B81A354352653AE60476B4F717AD19F9D6CE15`. Both exactly match the required identities.

An independent whole-PDF semantic search for all three current-rendered needles — `指数逐分量相加`, `保留归一化常数还可得到`, and `Dirichlet– 多项共轭` — found one and only one page: physical PDF page 714, whose printed page number is 701. No prior role page number or conclusion was used.

## Frozen denominator

The complete figure-plus-caption reader-visible denominator is frozen as 23 semantic objects in `machine/object_denominator.csv`: 16 text/formula objects and 7 independent graphic objects (one brace, two arrows, three strip borders, and one posterior-result border). The complete unordered denominator is therefore `23 × 22 / 2 = 253` pairs. `machine/unordered_pair_metrics.csv` contains exactly 253 distinct pair IDs with no duplicates or omissions.

The 300 dpi native crop is 1839 × 1172 pixels and was not resized. The decisive ROI set contains six native-1x crops directly cut from that native rendering and six nearest-neighbor-8x companions.

## Independent mathematics and semantics

The recomputation is:

`p(theta|alpha) ∝ product_i theta_i^(alpha_i-1)` and `p(n|theta) ∝ product_i theta_i^n_i`, so multiplication adds exponents componentwise and yields `product_i theta_i^(alpha_i+n_i-1)`. Hence the conjugate posterior is `Dir(alpha+n)`. Retaining the multinomial coefficient and both multivariate-Beta normalizers gives

`p(n|alpha) = N!/(product_i n_i!) × B(alpha+n)/B(alpha)`.

The figure, caption, and current V5-C05 prose all express this same result. The posterior result box abbreviates conditioning as `theta|n`, but the same box explicitly displays `Dir(alpha+n)`, the preceding posterior-kernel row displays `p(theta|n,alpha)`, and the local context treats alpha as fixed; this is an unambiguous shorthand rather than a change of mathematical meaning.

## Source/font and current-pixel observation

The source declares 9.4 pt for ordinary nodes, 8.5 pt for underbrace annotations, 8.8 pt for the brace/marginal notes, 15 pt for multiplication, and `\small` bold row labels, with no whole-figure resize/scalebox. The final PDF spans report 9.365 pt formula bases, 8.468/8.767 pt annotations, 9.963 pt row labels/caption, and natural mathematical scripts at 6.555/4.682 pt.

Under R168 those old point declarations are advisory and cannot alone cause a hard failure. The current-R114 native 300 dpi observations are decisive: the three row labels each have 40 px visible-ink height; the four comparable CJK annotations range from 32 to 34 px (maximum/minimum 1.063); legal mathematical scripts reach at least 16 px; every low-profile operator and punctuation glyph is recognizable in the native-1x and nearest-8x views. There is no actual unreadability, tofu, wrong codepoint, severe visual imbalance, clipping, or semantic confusion.

## Pair, overlap, clearance, and clipping adjudication

Mechanical pair enumeration produced four candidate pairs. Manual post-observation adjudication is recorded in `manual_candidate_pair_ledger.csv`:

- O02/O03 and O11/O12 have 0 shared visible-ink pixels; their conservative 3 px and 2 px clearances are advisory under R168, while both native and 8x views are actually clear and readable.
- O16/O17 has 0 shared visible-ink pixels. Its nearest-center-derived clearance is conservatively 0 px because the two masks occupy adjacent raster rows, but the native and 8x views show distinct, readable formula and note with no shared ink or ambiguity.
- O15/O21 contributes 14 pixels only because the approximate arrow and rounded-border masks share their intentional graphic connector junction. This is `MASK_CONTAMINATION_CONFIRMED`, not a text/formula collision.

Therefore `OVERLAP_CANDIDATE_PIXEL_COUNT=14`, `MASK_CONTAMINATION_PIXEL_COUNT=14`, canonical `OVERLAP_PIXEL_COUNT=0`, and `PIXEL_ADJUDICATION_STATUS=MASK_CONTAMINATION_CONFIRMED`. The page-edge clip audit is 0 pixels, and manual viewing confirms no internal semantic object is clipped.

## Geometry, flow, caption, grayscale, and page integration

The reading path is unique: prior kernel × likelihood kernel → posterior kernel → posterior distribution, with a dashed secondary branch to the marginal evidence. Arrowheads stop at node boundaries; the brace groups only the prior and likelihood rows; no line crosses text. The aligned strips and posterior box are visually balanced, and the row-label emphasis does not overwhelm the formulas.

The caption states the same sufficient-statistic and componentwise exponent-addition conclusion as the diagram and adjacent prose. At full-page scale the figure fits naturally between the preceding explanation and the following subsection. No overflow, abnormal blank block, orphaning, caption collision, or adverse page break is visible. Grayscale preserves the solid/dashed distinction, border structure, hierarchy, and reading order without depending on color alone.

## Final SA1 matrix

SOURCE_FONT_PASS = true  
PIXEL_HEIGHT_PASS = true  
SAME_CLASS_RATIO_PASS = true  
ROLE_RATIO_PASS = true  
OVERLAP_CANDIDATE_PIXEL_COUNT = 14  
MASK_CONTAMINATION_PIXEL_COUNT = 14  
OVERLAP_PIXEL_COUNT = 0  
PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED  
PIXEL_ARBITER_MODEL = NOT_USED  
PIXEL_ARBITER_REASONING = NOT_USED  
CLIP_PIXEL_COUNT = 0  
MIN_TEXT_CLEARANCE_PX = 0.000 (conservative adjacent-row metric; R168 post-observation adjudication finds no actual unreadability or overlap)  
VISUAL_HARMONY_PASS = true  
MATH_SEMANTICS_PASS = true  
TEXT_CONSISTENCY_PASS = true  
GRAYSCALE_PASS = true  
PAGE_INTEGRATION_PASS = true

VERDICT = PASS  
PASS_WORDING = SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3
