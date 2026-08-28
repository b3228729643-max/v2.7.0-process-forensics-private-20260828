# R357 — R112 candidate freeze, P067 official-page acceptance, and next-route authorization

## Main build disposition

- The single authorized parent invocation completed naturally with exit code `0` and wrapper result `PASS`:
  `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r112_fullbook -NoPublish`.
- It remained one `latexmk` parent chain. Its three LuaLaTeX passes and two makeindex rules were internal convergence, not a retry or a second build.
- Final TeX-family process count is `0`; the R112 build lock is released. No A/C role, source write, retry, resume, interruption, or concurrent TeX action occurred under the lock.
- Main repository remains clean at HEAD `27fca4d1a0c9034807a161c1bffa4f4d8f099339`.

## Frozen R112 identity

- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf`
- bytes: `4,967,100`
- SHA-256: `D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2`
- pages: `817`; every page is `595.276 x 841.89 pt (A4)` and rotation `0`
- PDF version `1.7`; encrypted `false`; JavaScript `none`; suspects `none`
- outline entries `273`; named destinations `7,421`; annotations `4,961`, all `4,961` link annotations
- font table: `17/17` fonts embedded, subset, and Unicode mapped
- `main_full.log`: `260,299` bytes; SHA-256 `1D8B54B964F21C3491EFD3E510091ECD2B2E50BB93F9FDF7E23C2E413313809D`
- final-log counts: fatal/emergency `0`; LaTeX/package error `0`; undefined reference/citation `0`; rerun signal `0`; overfull `0`; underfull `0`; missing character `0`; multiply defined `0`; PDF-backend warning `0`; missing input file `0`
- the single `luaotfload` cache-reload line for `IBMPlexMath-Regular.otf` is advisory: the final PDF embeds `TOWNOR+IBMPlexMath-Regular` with Unicode mapping.
- `main_full.toc`: `118,583` bytes / SHA-256 `EA5F09079A670A22A63FF08CDD061A3106E3999994963A9FBBD61CEC1C7E560D`
- `main_full.ind`: `23,734` bytes / SHA-256 `B32C889C28CAE7E4D6D7BB209D544715497AC7567C55435B9EF8B9851E7AB472`
- `symbols.ind`: `25,820` bytes / SHA-256 `E62CD6894BACCB383FAB12A058B9F83C91BE89AE6687104CF8D89E19CB7BC49A`

R112 is now the sole official candidate. R111 remains immutable historical input.

## P067 official-page main review

- Current source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`, `4,015` bytes, SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`.
- The caption was independently found in R112 at physical page `69`, printed page `56`, Fig. `4.1`.
- Main actually opened the complete 200 dpi page, native 300 dpi page, native 300 dpi figure+caption, grayscale figure+caption, native 300 dpi tick-label ROI, and nearest-neighbour 8x tick-label ROI.
- The CDF/PMF panels, right-continuous open/closed endpoints, four probability masses, axes, explanatory text, caption, and page integration are complete and readable. No clipping, semantic shift, illegal overlap, or visible imbalance was found.
- In the native 300 dpi tick ROI, ink rows are `67–90` for `0.35`, `104–128` for `0.3`, and `143–166` for `0.15`; therefore the adjacent labels retain `13` and `14` completely blank raster rows. The nearest-8x view preserves clear separation.
- Representative evidence SHA-256: full page 200 dpi `44075A8D8C4A942AA64F46A1C77E599BB4E7C917C4EDDC4F77E047880F162966`; figure+caption native300 `BCE8A2ABB6EC3CF0FD8545B0D8F08486FA10EE14FC088383C8C6998F5FB55F82`; grayscale `A191C45F60D3C6AFB81393232C67D5079B4BC5C2E89C41A7016C506959545D84`; tick native300 `797269FF5D6B85A499658F668C5C579165970954E7BF917EE488F76A0CBB2FF5`; tick nearest8x `AA242853776626E9D2DC8DFF83AD969BA409B95020D8A8332E6BC210254FF00A`.

P067 remains `LOCAL_SA2_PASS` until a new independent R112 SA1 is sealed and accepted.

## Explicit next-role authorizations

### A — P067 R112 fresh isolated SA1

Authorize exactly one new `gpt-5.6-sol/xhigh/fork_turns=none` P067 SA1, with a different HANDOFF/instance and startup-absent root:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R4_SA1_FRESH_ISOLATED_R112_20260827`.

Whitelist only frozen R112, current main P067 source, active Goal/direct protocol-schema, and narrow necessary current V1-C04 context. Deny all old P067 evidence/roles/reports/handoffs/conclusions, Main acceptance/state/history, other UID conclusions, Git history, and every agent/thread/task status or identity tool. PDF/main/source are read-only; TeX/build/source/Git/central/process management/second UID/second role are `0`. Review must start from current R112, freeze a complete visible denominator/all unordered pairs, open native1x/nearest8x/grayscale/page evidence, write genuine post-observation manual ledgers, and seal once. PASS may request a different fresh isolated SA3 only.

### C — P662 R112 R168 read-only SA2

Authorize exactly one new `gpt-5.6-sol/xhigh/fork_turns=none` P662 read-only SA2, startup-absent root:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa2_r112_r168_readonly_adjudication_v1`.

Current source is `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_gamma_normalization.tex`, `3,588` bytes, SHA-256 `B5232526402FEF6735DC3F9C07B418D7BF49E0D8C17EAEFB82A54B450B63113E`. Whitelist only frozen R112/current source/Goal/direct protocol-schema/narrow current V5-C05 context. The B69/B70 catalog conclusions are swapped; current source, caption, R112 pixels, and necessary chapter text define the subject, and the stale catalog sentence is neither inherited nor counted as a source/PDF defect. Old P662/other UID/Main acceptance/state/history/Git/status tools are denied. PDF/source are read-only; TeX/source/Git/central/process/second UID/second role are `0`. Under R168, old numeric font thresholds alone are advisory; only actual missing/tofu/wrong codepoint or math, unreadability, severe imbalance, clipping, illegal overlap, or semantic/geometric error may hard-fail.

## Inventory and completion boundary

- Before actual role identities return: `31 SA1 / 39 SA2 / 0 SA3 / 29 local pass`.
- Strict final remains `0/99`; B remains `66/66` accumulated.
- Candidate build success and local visual acceptance do not constitute final Goal completion.

