# R310 — P049 R110 fresh SA1 FAIL acceptance and narrow source scope

- Accepted HANDOFF_ID: `A-R110-P049-SA1-FRESH-ISOLATED-20260827`.
- Accepted role result: `FAIL_TO_SA2`; SA3 is forbidden.
- Sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R2_SA1_FRESH_ISOLATED_R110_20260827`.
- Independent location: R110 physical page 48, printed page 35.
- Frozen denominator: N=28, C=378.
- Main root recomputation: manifest rows 64; ordinary files 66; duplicate/missing/extra/bytes/SHA mismatch 0; files read-only 66/66; directories read-only 3/3; WSTOP strict-latest margin 11,627,884 ticks; files at or after marker 0.
- Main opened the native 300-dpi figure, grayscale figure, guide-lines 8x ROI, and gradient/tangent/right-angle 8x ROI.
- The initial c2/outer-contour mask hit is accepted as corrected mask contamination: native visible ink has a clear gap. Final true illegal overlap and clip counts are zero.
- The contour ordering, P membership, increasing-gradient direction, tangent orthogonality, and right-angle geometry are correct. The approximately 89.9256-degree value is source-coordinate rounding and not a hard defect.
- Two genuine, related semantic/geometry defects are confirmed:
  1. Guide1 says `定位 P 所在等值线`, but its endpoint `(2.75,1.36)` is neither P nor on c3; its function value is approximately 1.41114 while P and c3 correspond to 1.
  2. Guide1 and Guide2 cross internally near `(3.22952321,2.00265997)` with 33 shared visible vector pixels, making the first two callouts ambiguous.
- R168 font and micro-raster observations are not failure causes.

Authorized source scope:

- Exactly one source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C03/fig_v1_c03_gradient_contour.tex`.
- Static-only first; no TeX, commit, second source, second UID, or fresh role is authorized.
- Only the Guide1 polyline on the current source line containing `(s1.west)--(axis cs:3.72,2.66)--(axis cs:2.75,1.36)` may change.
- Guide1's endpoint must become exactly P or an analytically demonstrated point on c3, and its interior must not intersect Guide2, Guide3, the gradient, tangent, right-angle marker, note text, labels, axes, or unrelated contours. An intended final endpoint contact with P or c3 is allowed.
- Intermediate Guide1 bend coordinates may be minimally adjusted or added solely to satisfy those conditions.
- The three note texts/positions, Guide2, Guide3, P/G/T/Tm, contours, formula, axes, label styles, fonts, colors, caption, and every other source token remain unchanged.
- Static evidence must explicitly recompute the endpoint equation, all Guide1 intersections/clearances, and regression clearances to the gradient label, P/right-angle cluster, guide notes, outer contour, and page/caption region.
- A new PDF and full native regression are mandatory after a separately granted single build slot; static analysis must not claim PASS.

Inventory after routing P049 SA1 back to SA2: `32 SA1 / 43 SA2 / 0 SA3 / 24 local pass`. P641 fresh SA1 continues independently.
