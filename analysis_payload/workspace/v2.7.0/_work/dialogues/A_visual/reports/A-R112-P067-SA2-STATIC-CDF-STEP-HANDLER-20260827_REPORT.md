# FIG-P067-01 static CDF step-handler patch

- HANDOFF_ID: `A-R112-P067-SA2-STATIC-CDF-STEP-HANDLER-20260827`
- Role: SA2 static-only
- Status: `P067_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`
- Rendered candidate: none
- Local pass claimed: no

## Exact source scope

The only modified file is `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`.

- Before: 4,015 bytes; SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`.
- After: 4,014 bytes; SHA-256 `2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`.
- Exact change: `const plot mark right` → `const plot mark left`.
- Git boundary: one file, 1 insertion / 1 deletion, index empty, `git diff --check` exit 0.
- Reverse-substituting the single new token reconstructs the exact baseline byte stream and baseline SHA, proving every other source byte is unchanged.

## Static semantic proof

The coordinate list remains `(.5,0) (1,.15) (2,.45) (3,.80) (4,1) (4.5,1)`. With the left-mark handler, horizontal intervals are:

- `[.5,1): 0`
- `[1,2): .15`
- `[2,3): .45`
- `[3,4): .80`
- `[4,4.5]: 1`

These values equal the successive cumulative sums of the unchanged PMF masses `.15,.30,.35,.20`. The existing filled endpoints retain the jump-inclusive value, and the existing open endpoints retain the left limit, so the curve is right-continuous and consistent with the PMF and caption.

The CDF coordinates, four filled endpoints, four open endpoints, PMF coordinates, integrated tick-label repair, axes, fonts, colors, strokes, annotations, labels, alt text, and caption remain unchanged.

This is static evidence only. A newly authorized PDF must remeasure the step geometry, endpoint alignment, tick labels, grayscale, caption/page integration, full object denominator, and all unordered pairs before any PASS can be claimed.

## Static evidence seal

Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R6_SA2_STATIC_CDF_STEP_HANDLER_R112_20260827`

- payload=4, controls=3, ordinary=7;
- manifest rows=4; duplicate/missing/extra/path-bytes-SHA-NTFS-ticks mismatch=0;
- files read-only=7/7; directories/root read-only=1/1;
- `WRITE_STOPPED.json` unique and strictly latest by 50,307,387 ticks;
- at-or-after marker excluding marker=0; post-marker root writes=0;
- JSON parse failures, ADS, cache/pyc, reparse points=0.

Control SHA-256:

- `PAYLOAD_MANIFEST.csv`: `1F381F7CF60FB624A5A1453450728DF8F566A71778CDEDED94EC9206D0D4678E`
- `PRESEAL_AUDIT.json`: `2E3B9831C96A73639BAA86DDF5D9895E7BA68217BCCC5CB23ECEB7F1A8E09AA6`
- `WRITE_STOPPED.json`: `395C749860638D00EC8412F33B55D4AE660788CEADC1406EE43E61DEB215D1CC`

No TeX, build, commit, fresh role, second source, second UID, or central state write occurred. Main review and one explicitly controlled standalone/direct LuaLaTeX slot are requested.
