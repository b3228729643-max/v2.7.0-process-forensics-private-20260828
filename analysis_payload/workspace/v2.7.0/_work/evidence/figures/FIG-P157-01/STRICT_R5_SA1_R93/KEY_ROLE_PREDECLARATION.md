# Predeclared key-role evidence for the role-ratio gate

This note records only evidence already present in the frozen current figure source before the SA1 review. SA1 did not add or edit any source comment, style, or role name.

Source: `fig_v1_c10_complexity.tex`.

- line 2 is an explicit candidate-plan comment: `Proposed post-v2.3.1 polish for FIG-P157-01: protect key-label size and stroke hierarchy.` This predeclares that a key-label tier is intentionally protected as part of the figure hierarchy; it is not an acceptance-time relabelling.
- lines 8--9 define the dedicated `slfig-FIG-P157-01-key` style and its 9.2 pt declared base.
- lines 49--50 bind only `最低验证误差` to that key style immediately above the selected validation-minimum marker.
- lines 51--52 bind only `选择复杂度` to that key style at the selected x-coordinate.
- lines 53--58 separately bind the three ordinary region labels to the smaller `region` role. The source therefore distinguishes key decision outputs from ordinary region annotations before rendering and before this review.

The semantic reason is explicit in the bound labels and their geometry: the two key labels identify the validation criterion's minimum and the complexity chosen from it. They are the decision outputs of the figure, while the region labels supply lower-tier context.

Native 300 dpi role medians are BASE region = 35 px and key = 39 px, hence `39/35 = 1.114286`. This lies within the Goal's predeclared-emphasis band `[0.90,1.25]`. It does not rely on a post-hoc role name or on mere readability.

If line 2 plus the dedicated style/application chain were absent, the key elements would have to use the ordinary-annotation upper limit 1.10 and the measured 1.114286 would fail. The PASS therefore expressly depends on this pre-existing source-plan chain.
