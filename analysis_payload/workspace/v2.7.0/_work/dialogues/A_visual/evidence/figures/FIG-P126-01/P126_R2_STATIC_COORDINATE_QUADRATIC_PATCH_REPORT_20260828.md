# FIG-P126-01 R2 static source report

- HANDOFF_ID: `A-R115-P126-SA2-STATIC-COORDINATE-QUADRATIC-PATCH-20260828`
- UID: `FIG-P126-01`
- role/status: `SA2 / P126_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`
- acceptance boundary: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`
- TeX/build/commit/fresh-role invocations: `0/0/0/0`

## Exact source boundary

- only source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex`
- before: `4093 bytes / 328A61A7C16DC11546BA165D698A22E1431B1B6AA3C04B16A4C40B52E4F3673C`
- after: `4224 bytes / 366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`
- Git boundary: one modified file, `26+/26-`, index empty, `git diff --check` PASS.
- The exact unified diff is frozen in `SOURCE_EXACT_DIFF.md` inside the sealed root.

The source changes only the authorized axis limits, four contour parameterizations, q0--q7 coordinates, seven numeric-label placements, four square-marker coordinates, and the local teal dash pattern including its legend sample. Figure/caption/alt text, font declarations, axis names, colors, shared macros, chapter/build inputs, and every other source remain unchanged.

## Unified quadratic and coordinate-descent proof

All four contours are level sets of

`f(x1,x2)=0.5*(x1^2+2*x1*x2+2*x2^2)`.

The Hessian is `[[1,1],[1,2]]`; its determinant is 1 and its eigenvalues are `(3-sqrt(5))/2=0.381966...` and `(3+sqrt(5))/2=2.618034...`, so it is positive definite. The nonzero off-diagonal term makes the principal axes non-axis-aligned. Each contour uses `x1=r(cos(t)-sin(t)), x2=r sin(t)`, hence `(x1+x2)^2+x2^2=r^2`; sampled residual is at most `4.44e-15`.

The fixed-coordinate minimizers are `x2=-x1/2` for a vertical update and `x1=-x2` for a horizontal update. The new q0--q7 path alternates vertical/horizontal and satisfies the corresponding updated-coordinate derivative exactly at every step. Objective values are `2.92, 2.56, 1.28, 0.64, 0.32, 0.16, 0.08, 0.04`; all seven drops are strict. The true unique optimum remains `x*=(0,0)` while q7=`(-0.40,0.20)` is only an approximation.

## Static clearance and grayscale projections

At the conservative 300-dpi projection used for this static gate:

- x1 label to contour: `96.330671 px`
- step 1 label to contour: `25.555196 px`
- step 2 label to contour: `4.787626 px`
- step 5 label to contour: `6.763167 px`
- step 5 label to horizontal axis: `28.850145 px`
- minimum label-to-contour gap over all seven digits: `4.169367 px`
- minimum label-to-label gap: `16.321796 px`
- outer contour to x/y axis-window boundaries: `10.164805 / 12.453300 px`

The local teal dash period is `1.2pt on / 1.2pt off`. It projects at least five cycles in the 12pt legend sample and at least 2.5 cycles on the shortest vertical update, while the blue sample remains solid. These are static predictions only: native clearances, grayscale distinction, clipping, and all regression gates must be remeasured from the newly authorized standalone PDF.

## Static seal

- sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R2_SA2_STATIC_COORDINATE_QUADRATIC_PATCH_R115_20260828`
- payload/controls/ordinary/directories: `6/3/9/1`
- manifest rows/set/identity mismatches: `6/0/0`
- ReadOnly: `9/9 files`, `1/1 directories including root`
- WSTOP: 15 valid unique `KEY=VALUE` lines; SHA256 `1E14E10414E50E5F626ABEDB7970D6BF749446DA03431150CFCD41BFA92AE743`
- strict-latest margin: `2,999,142,591 ticks`; at-or-after excluding marker: `0`
- postmarker dual-snapshot mismatch: `0`
- JSON parse / ADS / cache-pyc / reparse errors: `0/0/0/0`
- payload manifest SHA256: `DD8412EA5A66B90829EBABAA55E6DC9212A23F7077DBCAED6675E1A0D4E2A6DA`
- seal audit SHA256: `9FD0A35C6F480F4CD22AA5880F216F47E4FCA5C0E51796DAAA8E147FC545A611`
- root snapshot SHA256: `1D105C092BB625603F5FD943451B3097CC9AF9BC2BCADA762DBA9A52D3B45CC9`

Controller and auditor both exited successfully. No root content or attribute writes followed the final external-to-root marker move. The requested next action is one explicit controlled standalone/direct LuaLaTeX build slot; no build has been started.
