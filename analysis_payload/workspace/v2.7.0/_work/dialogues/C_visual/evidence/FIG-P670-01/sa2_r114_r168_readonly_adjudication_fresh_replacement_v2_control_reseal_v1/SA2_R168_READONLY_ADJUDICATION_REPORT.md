# FIG-P670-01 R114 / R168 fresh read-only SA2 adjudication

HANDOFF_ID=C-FIG-P670-01-R114-SA2-R168-READONLY-ADJUDICATION-FRESH-REPLACEMENT-V2  
UID=FIG-P670-01  
ACTUAL_INSTANCE=/root/sa2_fig_p670_r114_r168_readonly_fresh_v2  
MODEL=gpt-5.6-sol  
REASONING_EFFORT=xhigh  
ROLE=SA2_R114_R168_READONLY_ADJUDICATION  

## Input identity and scope

- Official R114 PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf`
- PDF bytes: `4,967,122`
- PDF SHA-256: `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`
- Current P670 source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_posterior_predictive.tex`
- Source bytes: `4,833`
- Source SHA-256: `614C1E5C0FACF9A7C2E6F0CB126EB6EA4F18F1BF00F48744C8E248A8DE89F781`
- Necessary adjacent semantics were read only from the exact allowlisted chapter file `V5-C05.tex`, especially lines 621-681.
- No earlier P670 evidence, role result, report, handoff, snippet, page number, denominator, pair count, metric, manual result, or verdict was read or injected.
- The PDF and source remained read-only; no TeX, latexmk, build, source write, Git, central state, inventory, process management, second UID, or second P670 role was used.

## Independent location

The source caption phrase `下一类别的后验预测概率等于当前伪计数占总伪计数的比例` was searched only inside the exact official R114 PDF text extraction. It produced one hit at physical page 717. The page itself identifies printed page 704 and figure 34.10. The complete caption, internal summary, formulas, and update diagram on that page match the current allowlisted source.

## Frozen visible denominator and all unordered pairs

The frozen denominator is all reader-visible text belonging to the figure and its caption. Page furniture and the adjacent example are outside the figure denominator but were still inspected for page integration.

- Visible elements: `N=35`, IDs `E01` through `E35`.
- Frozen pair universe: `C(35,2)=595`, IDs `P0001` through `P0595`.
- `analysis/visible_denominator_frozen.csv` records every element with panel, role, exact visible text, source line, declared point size where explicit, and PDF-coordinate bbox.
- `analysis/all_unordered_pairs_frozen.csv` records every unordered element pair exactly once.
- `manual_element_ledger.csv` contains an actually viewed manual entry for every `E` ID.
- `manual_pair_adjudication.csv` contains an actually adjudicated entry for every `P` ID; its 595 IDs exactly equal the frozen pair universe with no omission or duplicate.
- `P0595` is the only bookkeeping special case: the single union bbox used for multiline caption text E35 geometrically includes the caption-label area E34, but the native 300 dpi ink is disjoint. The native 1x and nearest-neighbor 8x caption ROI confirm no actual ink collision.

## Views actually opened

- Physical page 717 full-page native 300 dpi color.
- Physical page 717 full-page native 300 dpi grayscale.
- Figure 34.10 native 300 dpi crop.
- Figure text-object overlay with E01-E35.
- Semantic/object overlay with S01-S11.
- Native 1x / 300 dpi and nearest-neighbor 8x ROIs for:
  - left probability partition and posterior-predictive formula;
  - prediction/update arrows and observation node;
  - right updated counts, probabilities, and update formula;
  - summary and full caption.

## Independent mathematical and semantic check

- Left state `(4,3,2)` contains four category-1 tokens, three category-2 tokens, and two category-3 tokens; the total is 9.
- The displayed left probabilities `4/9`, `3/9`, and `2/9` are normalized and equal the corresponding pseudocount proportions.
- The displayed equation `P(Y_(N+1)=k|n)=(alpha_k+n_k)/(alpha_0+N)` is the posterior expectation of the category probability under the Dirichlet posterior and matches the chapter proposition and proof.
- The observation is `j=2`. Only the second count increases, producing `(4,4,2)` and total 10.
- The displayed updates `n_2 <- n_2+1` and `alpha_0+N <- alpha_0+N+1` are correct.
- The displayed right probabilities `4/10`, `4/10`, and `2/10` are normalized and equal the updated pseudocount proportions.
- The newly added category-2 token and its probability-bar contribution are hatched, so the update remains identifiable in grayscale.
- Arrow directions are left state -> observation -> updated state. Arrowheads terminate before semantic content and do not cross labels.
- The summary and caption correctly state smoothing, reinforcement, exchangeability after integrating out theta, and the loss of independence of the marginal predictive sequence. This agrees with the exact chapter statement that observations are conditionally independent given Theta but positively reinforced and exchangeable after Theta is integrated out.
- Figure, caption, and adjacent body use consistent theta, alpha, n, N, j, and category indexing.

## R168 hard-defect adjudication

R168 makes legacy point-size, pixel-height, and ratio thresholds advisory. They cannot independently cause hard FAIL or source return. The source explicitly uses 9.8 pt titles, 9.2 pt main labels/formulas/summary, 8.8 pt arrow labels, and 8.5 pt probability labels. Those values are preserved as advisory evidence only.

The current official PDF was therefore tested for the allowed hard-defect classes:

- Missing glyph, tofu, or wrong codepoint: none observed. Theta, alpha, subscripts, arrows, Chinese, digits, fractions, and italic `iid` render correctly.
- Unreadable or seriously imbalanced content: none observed. Native 300 dpi and 8x nearest-neighbor views remain clean; titles, token labels, probabilities, formulas, arrows, summary, and caption form a coherent hierarchy.
- Clipping: none observed in the figure, caption, arrowheads, token outlines, hatching, or page integration.
- Illegal visible-ink overlap: none observed across all 595 frozen unordered text-object pairs or between text/formula ink and semantic lines, arrowheads, node borders, bar borders, or hatching.
- Semantic, geometric, or mathematical error: none observed.
- Grayscale or page-integration failure: none observed. Category roles remain structurally separated and the newly updated category-2 contribution remains hatched; the caption and following example have clear separation.

Mechanical raster measurements and bboxes are corroborative only. They did not generate this manual verdict. In particular, grouped multiline or framed objects can include border pixels or disjoint line unions, so native-pixel inspection controls the collision adjudication.

## Final verdict

VERDICT=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1

No hard R168 defect was found. No source return is warranted. This SA2 does not launch fresh SA1, start another UID, modify source, build, or write central inventory/state.
