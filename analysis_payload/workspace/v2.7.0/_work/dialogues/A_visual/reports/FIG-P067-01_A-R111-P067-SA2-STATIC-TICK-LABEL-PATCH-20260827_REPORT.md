# FIG-P067-01 R2 static-only patch report

## Outcome

`P067_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`

This stage is `STATIC_ONLY_NOT_RENDERED_NOT_PASS`. No TeX, build, commit, fresh role, second UID, second source, or central-state write occurred.

## Exact source change

Only `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex` changed.

- Before: 3,866 bytes; SHA-256 `03372740AB8015EFFB7BC6CFBBDC669A1E8FBF52246291491B1B0C506513B864`.
- After: 4,015 bytes; SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`.
- Diff: 3 insertions, 1 deletion; index empty; `git diff --check` exit 0.

The unchanged y-tick list remains `{0,.15,.30,.35}`. Only the automatic 0.30 label is suppressed and the same visible `0.3` text is replayed at `(axis cs:.45,.30)` with the existing 8.6/10.3 pt font, `xshift=-2pt`, and `yshift=-4.5pt`. The 0.35 automatic label/tick is unchanged.

All four PMF values and positions, all CDF coordinates/levels, axes, panel order, endpoint encoding, guide lines, annotations, caption, fonts, colors, strokes, and other geometry remain unchanged.

## Static clearance and risk

Using the accepted R111 native glyph boxes, the 4.5 TeX-pt local downward shift projects the replayed 0.30 box to roughly 144.36--152.93 PDF pt. Projected vertical clearance is about 2.0 native-300-dpi pixels from 0.35 above and 2.5 pixels from 0.15 below. The label remains tied to the same tick and within the existing left page margin. A controlled render is required to verify actual ink clearance and all-page regression; this report does not claim PASS.

## Seal

The static root contains five manifest-bound payloads plus `PAYLOAD_MANIFEST.csv` and a sole final `WRITE_STOPPED`: seven ordinary files. Root-external audit found path/bytes/SHA/NTFS-tick mismatch 0, all 7 files and the root directory read-only, ADS/cache/pyc/reparse/parse errors 0, and `WRITE_STOPPED` strictly latest by 589,462,304 ticks with no at-or-after nonmarker and no postmarker root write.

