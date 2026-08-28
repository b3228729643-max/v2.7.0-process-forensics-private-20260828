# FIG-P067-01 fresh isolated R112 SA3 semantic audit

- Reviewer: `SA3-R112-FRESH`
- Official PDF located independently at `page_index0=68`, `physical_page1=69` (printed page 56).
- Figure caption: “离散随机变量的分布函数：跳跃高度等于对应点的概率质量”.

## PMF and intended cumulative values

The lower panel shows masses `0.15, 0.30, 0.35, 0.20` at `t=1,2,3,4`; they are nonnegative and sum to `1.00`. The closed CDF markers at the four support points are `0.15, 0.45, 0.80, 1.00`, which are the correct cumulative sums. The corresponding open markers show the left limits `0, 0.15, 0.45, 0.80`. These marker sets correctly express the intended right-continuous discrete CDF.

## Hard semantic/geometric failure

The connecting blue path `GFX-007` does not follow those markers. The rendered horizontal plateaus are placed one support interval too early:

- `0.15` is drawn on roughly `0.5 <= t < 1`, where the CDF should be `0`;
- `0.45` is drawn on `1 <= t < 2`, where the right-continuous CDF should be `0.15`;
- `0.80` is drawn on `2 <= t < 3`, where it should be `0.45`;
- `1.00` is drawn on `3 <= t < 4`, where it should be `0.80`.

Thus at `t=1,2,3` the closed marker is the correct post-jump value, but the path immediately to its right is already the *next* cumulative value. The plot therefore contradicts its own open/closed endpoints, the annotation “右连续：实心点取跳后值”, the PMF/CDF relation, and the caption. This is a hard `FAIL` under R168.

The current source contains `const plot mark right` with coordinates `(.5,0) (1,.15) (2,.45) (3,.80) (4,1) (4.5,1)`, which explains the rendered one-interval left shift. This source observation is diagnostic only; SA3 made no source change.

## Other checks

- Monotonicity of the numeric levels: nondecreasing, but attached to incorrect intervals.
- Right continuity: `FAIL` for the rendered path at the first three support points.
- Open/closed endpoint convention: marker symbols themselves are correct; relation between markers and path is `FAIL`.
- Axes and labels: readable and correctly named.
- Dual-panel relation: PMF and marker cumulative sums agree; connecting CDF path disagrees.
- Caption: mathematically correct statement, but not realized by the drawn path.
- Tofu/wrong code/unreadability/obvious imbalance/real clipping: none observed.
- Grayscale and page fusion: readable and natural.
- Font and micro-grid differences: advisory only under R168; no hard font failure.
