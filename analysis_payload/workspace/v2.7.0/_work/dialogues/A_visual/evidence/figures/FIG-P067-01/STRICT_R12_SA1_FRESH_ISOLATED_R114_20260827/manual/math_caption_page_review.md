# Post-observation mathematics, caption, and page review

Reviewer role: fresh isolated SA1  
HANDOFF_ID: `A-R114-P067-SA1-FRESH-ISOLATED-20260827`  
Evidence actually opened before these decisions: `figure_native1x_300dpi.png`, `figure_nearest8x.png`, all listed nearest8x detail tiles, `figure_grayscale_300dpi.png`, and `page_069_200dpi.png`.

## PMF and CDF arithmetic

The source gives the PMF masses

\[
(p_1,p_2,p_3,p_4)=(0.15,0.30,0.35,0.20),
\qquad \sum_{i=1}^4 p_i=1.00.
\]

The rendered CDF has the post-jump cumulative values

\[
F(1)=0.15,\quad F(2)=0.45,\quad F(3)=0.80,\quad F(4)=1.00.
\]

| support point | left limit | post-jump value | observed jump | PMF mass | manual result |
|---:|---:|---:|---:|---:|---|
| 1 | 0.00 | 0.15 | 0.15 | 0.15 | exact match |
| 2 | 0.15 | 0.45 | 0.30 | 0.30 | exact match |
| 3 | 0.45 | 0.80 | 0.35 | 0.35 | exact match |
| 4 | 0.80 | 1.00 | 0.20 | 0.20 | exact match |

Manual mathematics decision: `PASS`. The CDF is nondecreasing, begins at 0 before the first support point, ends at 1 after the last support point, and each jump equals its aligned PMF stem height.

## Right continuity and endpoints

At every support point the filled marker is at the post-jump value and the open marker is at the left-limit value. The step continues horizontally to the right from the filled marker. The terminal filled marker is at `(4,1)` and the plateau remains at 1 to the right. The initial plateau remains at 0 to the left of `t=1`.

Manual right-continuity decision: `PASS`. No endpoint is reversed or ambiguous.

## Ticks and labels

The lower panel supplies the shared support ticks `1,2,3,4`. Its displayed probability ticks and supplementary label cover `0`, `0.15`, `0.30`, and `0.35`, which are the distinct ordinate values needed for the PMF. The upper panel shows `0`, `0.45`, `0.8`, and `1`; the intermediate cumulative level `0.15` is visually recoverable from the aligned first jump and `p_1` label without a false tick. Axis labels `F_X(t)`, `p_X(t)`, and `t` are correct and complete.

Manual tick decision: `PASS`.

## Caption and adjacent-page consistency

The current caption is “离散随机变量的分布函数：跳跃高度等于对应点的概率质量”. It states one direct reading conclusion and matches both panels exactly. The immediately following page text says that Figure 4.1 supports a bidirectional check: recover probability masses from jumps or accumulate masses to obtain the CDF; it also states that right continuity selects the upper endpoint and that monotonicity and terminal value 1 are legality checks. Those claims agree with the observed markers, plateaus, and PMF stems.

Manual caption decision: `PASS`.  
Manual text-consistency decision: `PASS`.

## Grayscale and page integration

In grayscale the CDF remains identifiable as a step curve with filled/open endpoint coding, while the PMF remains identifiable as four stems with filled markers. The dashed reference and alignment guides remain subordinate. The figure occupies the upper portion of the page at a balanced width, the caption is directly below it, and the following paragraph begins with an explicit Figure 4.1 cross-reference. There is no clipped ink, illegal overlap, isolated caption, anomalous blank block, or collision with the subsequent section content.

Manual grayscale decision: `PASS`.  
Manual page-integration decision: `PASS`.

## R168 advisory retained without promotion to a blocker

`T21-G46` has a measured one-native-pixel blank clearance in the direct 300 dpi render. The focused nearest8x evidence shows zero shared glyph/guide foreground and no loss or ambiguity in “跳高”. Under R168 this micro-clearance is advisory because it is not a true overlap, unreadability, clipping, wrong codepoint, semantic error, or obvious imbalance. It is recorded; it is not silently treated as satisfying the older generic clearance threshold.
