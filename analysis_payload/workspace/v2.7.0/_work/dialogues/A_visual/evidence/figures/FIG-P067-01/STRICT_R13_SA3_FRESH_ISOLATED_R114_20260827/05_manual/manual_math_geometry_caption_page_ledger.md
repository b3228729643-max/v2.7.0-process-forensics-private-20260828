# Manual mathematics, geometry, caption, and page-integration ledger

Reviewer: `SA3_FRESH_ISOLATED`  
Candidate: official read-only R114 PDF and current read-only `fig_v1_c04_cdf.tex` only.

## Independent locator

I located the target from the current caption text, not from any prior P067 page information. The exact caption occurs once in the extracted official PDF and resolves to physical page 69, whose printed page number is 56. The page shows Figure 4.1 with the same caption and the immediately following current chapter sentence.

## PMF normalization and CDF reconstruction

The lower panel encodes

`p_1 = 0.15`, `p_2 = 0.30`, `p_3 = 0.35`, `p_4 = 0.20`.

All masses are nonnegative and

`0.15 + 0.30 + 0.35 + 0.20 = 1.00`.

The upper panel therefore correctly encodes

- `F_X(t)=0` for `t<1`;
- `F_X(t)=0.15` for `1<=t<2`;
- `F_X(t)=0.45` for `2<=t<3`;
- `F_X(t)=0.80` for `3<=t<4`;
- `F_X(t)=1` for `t>=4`.

The four jump heights are respectively `0.15`, `0.30`, `0.35`, and `0.20`, exactly matching the four lower-panel masses. The CDF is nondecreasing, starts at zero before the support, and reaches one at and after the last support point.

## Right continuity and marker geometry

At each `t_i`, the filled marker is on the post-jump value and the open marker is on the excluded pre-jump value. This is the correct right-continuous convention. The vertical alignment guides and common support positions `1,2,3,4` make each lower mass correspond to exactly one upper jump. Marker order, step direction, and plateau endpoints are all correct.

## Ticks and labels

- Upper y ticks `0, 0.45, 0.8, 1` are the baseline, two internal cumulative levels, and terminal value.
- Lower y ticks `0, 0.15, 0.3, 0.35` expose the baseline, first/second masses, and largest mass; the unlabeled generated `0.30` tick is correctly replaced by the manual `0.3` label.
- Lower x ticks `1,2,3,4` align with every PMF stem and all cross-panel guides.
- Axis labels `F_X(t)`, `p_X(t)`, and `t` use the same variable convention as the chapter context.

## Caption and adjacent text

The current caption, “离散随机变量的分布函数：跳跃高度等于对应点的概率质量”, is a single accurate reading conclusion. The current adjacent sentence describes both reconstruction directions, the right-continuous upper-end convention, monotonicity, and terminal value one. Figure, caption, and prose agree exactly; no stale variable, value, or direction was observed.

## Page integration and R168 hard observations

The figure occupies the top of the page at an appropriate width. The caption is centered beneath it, the explanatory sentence begins with adequate separation, and the following section content flows without collision, clipping, orphaning, or severe blank-space imbalance. Header, printed page number, caption number, and body are all legible.

Across opened native, nearest-8x, grayscale, page, overlay, and critical evidence there is no tofu, wrong codepoint, real unreadability, true clipping, illegal ink overlap, severe visual imbalance, or mathematical/semantic/geometry error. Dashed guides remain distinguishable from solid probability objects in grayscale; open versus filled markers provide a non-color cue.

Manual decision: `PASS`.
