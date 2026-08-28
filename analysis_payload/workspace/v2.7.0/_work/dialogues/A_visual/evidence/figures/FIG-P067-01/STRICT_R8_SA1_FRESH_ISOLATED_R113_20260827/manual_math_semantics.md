# FIG-P067-01 mathematical and semantic verification

## PMF/CDF reconstruction

The PMF panel shows masses

`p_1=0.15`, `p_2=0.30`, `p_3=0.35`, `p_4=0.20`.

They are nonnegative and sum to `1.00`. Their cumulative sums are `0.15`, `0.45`, `0.80`, and `1.00`, exactly the four plateau values drawn in the CDF panel. The CDF is nondecreasing, begins at zero before the first support point, and terminates at one.

## Right continuity and endpoints

At each `t_i`, the filled marker is on the post-jump value and the open marker is on the pre-jump value. Thus the displayed value is `F_X(t_i)=P(X<=t_i)`, not the left limit. The annotation “右连续：实心点取跳后值” and the open/filled endpoint geometry agree. The jump height at every support point equals the corresponding PMF stem height, agreeing with “同一 t_i：跳高 = p_i”.

## Axes, labels, caption and codepoints

The upper ordinate is `F_X(t)`, the lower ordinate is `p_X(t)`, and the shared abscissa is `t`. Lower-panel support labels 1-4 align with both panels. The caption “离散随机变量的分布函数：跳跃高度等于对应点的概率质量” states exactly the relation shown. PDF extraction and all contact originals contain no replacement character, tofu box, missing label, or wrong codepoint.

There is no visible overline, underline, fraction bar, radical rule, accent rule, or other formula-rule path in this figure. All subscripts are ordinary PDF text glyphs and are included in G001-G095. Drawing records D001-D035 and the five real opaque backgrounds close the visible path inventory.

Hard semantic result under R168: **PASS**.

