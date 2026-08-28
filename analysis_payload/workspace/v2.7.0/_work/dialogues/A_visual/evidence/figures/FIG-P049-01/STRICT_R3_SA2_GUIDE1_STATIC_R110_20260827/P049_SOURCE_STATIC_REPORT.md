# FIG-P049-01 Guide 1 static-only patch

- HANDOFF_ID: `A-R110-P049-SA2-GUIDE1-STATIC-R3-20260827`
- route: `P049_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`
- status: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`
- only source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C03/fig_v1_c03_gradient_contour.tex`
- source before: 4,189 bytes, SHA-256 `F9D4040ABB708F8043C619FB8C59B9CCCFDB2938E1BBD54B03B1E5D940F2999C`
- source after: 4,189 bytes, SHA-256 `27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E`
- exact Git scope: one file, 1 insertion, 1 deletion; `git diff --check` PASS; index empty.

## Exact change

The Guide 1 polyline alone changes from

`(s1.west)--(axis cs:3.72,2.66)--(axis cs:2.75,1.36)`

to

`(s1.west)--(axis cs:1.20,2.45)--(axis cs:.84,1.728)`.

The bend count remains exactly one. No note position/text, Guide 2/3, P/G/T/Tm, contour, formula, axis, label style, font, color, caption, or other token changes.

## Endpoint proof

The new endpoint is exactly `(21/25,216/125)=(.84,1.728)`. For `c3`,

`x^2/9 = 49/625`, `y^2/3.24 = 576/625`, and their sum is `625/625=1`.

Thus the endpoint lies exactly on the outer contour named by “定位 P 所在等值线”; it does not substitute a near-contour point.

## Intersection and clearance proof

The first segment stays outside `c3`, going from `f=4.2713530864` to `f=2.0126234568`. On the second segment, the two algebraic roots of `f=1` occur at `t=1` and `t=5.7768426242`; only the final endpoint is within `t∈[0,1]`. Therefore Guide 1 touches `c3` only at its intentional endpoint and never reaches `c1` or `c2`.

Analytical line-segment checks give zero intersections with Guide 2, Guide 3, the gradient arrow, tangent, right-angle/P cluster, axes, and unrelated contours. At the current 300-dpi axis scale, the smallest centerline clearances are 74.49px to Guide 2, 154.03px to Guide 3, 80.90px to the gradient arrow, 60.36px to the tangent, 163.23px to the right-angle/P cluster, 99.55px to the y-axis, and 204.78px to the x-axis.

Using the current R110 text bounding boxes projected through the same axis mapping, the limiting label clearance is 19.83px to `∇f(P)`; tangent label clearance is 33.38px, note 2 is 64.71px, note 3 is 128.94px, the P label is 103.56px, and the caption is 493.69px away. Guide 1 intentionally begins at `s1.west` and immediately leaves note 1 to the left. Its highest point is `y=2.78`, leaving 0.52 axis units (61.62px) to the plot top.

The rejected nearer endpoint `(1.8,1.44)` was not used because its straight segment intersects the tangent internally. The chosen one-bend route avoids that hidden regression.

## Risk and next gate

Static geometry has substantial predicted clearance, but this is not a rendered PASS. A single explicitly granted standalone/direct LuaLaTeX build must produce a new PDF, followed by from-zero native1x/8x verification of the new Guide 1 endpoint, all guide relations, gradient/tangent/right-angle cluster, labels, outer contour, caption, page integration, full visible denominator, all unordered pairs, and true manual review.

No TeX, Git commit, fresh role, second source, second UID, or central-state write occurred in this static stage.
