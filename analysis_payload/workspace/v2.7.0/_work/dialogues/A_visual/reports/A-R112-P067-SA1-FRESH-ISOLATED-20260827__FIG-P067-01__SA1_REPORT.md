# FIG-P067-01 — R112 fresh isolated SA1 report

`HANDOFF_ID`: `A-R112-P067-SA1-FRESH-ISOLATED-20260827`

## Assigned scope

Fresh isolated SA1 review of `FIG-P067-01` only, using the R112 official full-book PDF and current single P067 TeX source. No source, build, Git, central state, inventory, second UID, or second role was modified.

## Candidate identity and independent localization

- R112 PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf`
- PDF identity: 4,967,100 bytes; SHA-256 `D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2`
- current single source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex`
- source identity: 4,015 bytes; SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`
- exact caption was independently and uniquely located on physical page 69, printed page 56: `图 4.1 离散随机变量的分布函数：跳跃高度等于对应点的概率质量`
- page: 595.276 pt × 841.890 pt; 300 dpi grid 2481 × 3508 px
- figure crop: page pt `[100,62,489,221]`; integer page px `[416,258,2038,921]`; native 1622 × 663 px
- standalone crop: page pt `[100,62,489,201]`; integer page px `[416,258,2038,838]`; native 1622 × 580 px

## Evidence coverage

- frozen visible-object denominator: 150 = 95 characters + 50 foreground graphics + 5 opaque backgrounds
- all unordered pairs frozen: 11,175 = 150 × 149 / 2
- manual object ledger: 150/150 unique IDs
- critical/near pair ledger: 12/12, with raw 1×, raw nearest8×, A/B masks, intersection, overlay 1×, and overlay nearest8×
- all eight glyph contact sheets actually opened; all 95 character cells reviewed
- full page 200 dpi, full page 300 dpi, native color crop, standalone crop, grayscale crop, whole-figure nearest8×, ID overlay, and all 12 critical raw/overlay ROIs actually opened
- empty masks: 0; crop-edge clip pixels: 0; portable filenames with colon: 0

## Findings

The PMF masses are 0.15, 0.30, 0.35, and 0.20, summing to 1. Their cumulative values are 0.15, 0.45, 0.80, and 1.00, exactly matching the CDF step levels. The CDF is monotone and right-continuous, with open pre-jump markers and filled post-jump markers. Both panels share support points 1–4, axes and annotations match the mathematics, and the caption is exact.

Six machine hard candidates were all rejected after opening their raw and overlay evidence. Two are ordinary TeX formula-internal relations (`p_2` and `F_X`); the other four are bbox/paint-order attribution involving `p_4`, the colon near the t=1 guide, or `跳` near the t=4 guide. The reader-visible native pixels show separation or background occlusion, not an actual illegal collision. Actual hard count is therefore zero.

Nine source font declarations below the older 9.5 pt line and several low-profile/script pixel heights are retained as R168 advisories. In the actual native and page views there is no missing glyph, tofu, wrong encoding, mathematical unreadability, obvious imbalance, true clipping, illegal overlap, semantic error, or geometric error. Font harmony, grayscale, caption, and page fusion all pass.

## Decision

`FINAL_DECISION=PASS_R168` for this fresh isolated SA1 role.

This does not count as `A_LOCAL_PASS`, does not update central state, and does not authorize source changes. The main line should dispatch a different fresh isolated SA3 against the same locked official candidate.

Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R4_SA1_FRESH_ISOLATED_R112_20260827`
