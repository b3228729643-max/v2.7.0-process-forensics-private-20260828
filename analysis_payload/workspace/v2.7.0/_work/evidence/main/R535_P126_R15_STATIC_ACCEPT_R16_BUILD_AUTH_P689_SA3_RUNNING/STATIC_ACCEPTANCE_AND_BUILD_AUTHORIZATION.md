# R535：P126 R15 `forget plot` 静态接受与 R16 唯一构建槽

时间：2026-08-28T16:58:26+08:00

## R15 静态内容接受

- HANDOFF：`A-R115-P126-SA2-STATIC-FORGET-PLOT-PATCH-20260828`。
- 状态保持 `STATIC_ONLY_NOT_RENDERED_NOT_PASS`；P126 仍为 SA2。
- Sole source：before 4,626 bytes/SHA-256 `6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`；after 4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`。
- Main 独立确认 5 个 `,forget plot` token；内存精确移除后恢复 before 的 4,626 bytes 与 SHA。五个普通 `\addplot` 均恰含一次 `forget plot`，两条 manual legend images 与两条 legend entries 未改。
- pgfplots 因果闭合：普通 plot options 在 `curplot@isirrelevant` 判断前应用；`forget plot` 使其不进入 remembered plot-spec list；两条 manual images 因而成为仅有的两个 legend specs，并按顺序配对两条 entries。仅证明机制，未把静态结果当成 rendered PASS。

## R15 sealed root 接受

- Root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R15_SA2_STATIC_FORGET_PLOT_PATCH_R115_20260828`。
- payload9/controls3/ordinary12；files12、dirs including root1，全 ReadOnly。Manifest rows9，与实际 payload 的 path/bytes/SHA/CreationTimeUtc ticks/LastWriteTimeUtc ticks mismatch0。
- `WRITE_STOPPED` 1,049 bytes/SHA-256 `3EBED5EE76B48045ACA85CDBE5EAE9C8DE8481443A22F76F745767296081D63A`；25 physical lines/25 unique keys，bad/duplicate/BOM/binding0。Marker ticks=`639235042397543779`，max-other（root）=`639235039398051411`，strict margin=`2,999,492,368` ticks，at-or-after excluding marker0。
- Manifest SHA-256=`E2A9AFECA46BE5D4AF016E3C51B93C9C251D598693AF6E1C2C374D33E304E00C`；seal-audit SHA-256=`84660255D8EC6A7CD0093BAEBD229BF43A78807323818CDC0B91DC2718AEEB9C`；marker bindings精确。
- CSV/JSON parse、ADS、cache/pyc、reparse、live source/after copy、reverse reconstruction mismatch均0。
- 首个 root-external auditor 仅在只读 `Where-Object` spacing 语法处 exit1，result/root writes0。不同命名的 V2 auditor只调用一次并 PASS；其脚本9,995/SHA-256 `AC7305E4183B87C5AE8511B8509AD1B16544346B838F4A7F4226828DAE39A820`，result1,067/SHA-256 `01F44B985CB145E8B4C4584B198634A54944B7CA31216683811C7F48FBF5CE47`/ReadOnly，与 Main 复算一致。该透明只读审计纠正不构成 root reject 或业务重跑。
- R15 root、scripts/results、internal/external report/handoff 从本裁决起冻结。

## 唯一 R16 direct LuaLaTeX 槽

- HANDOFF：`A-R115-P126-SA2-DIRECT-BUILD-R16-20260828`。
- Fixed fresh root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R16_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828`。
- Main immediate gate：Leaf=false、Container=false、Any=false、Parent=true；latexmk/lualatex/luatex/luahbtex=`0/0/0/0`。
- Source 必须在 controller 前后均为 4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`。
- Wrapper 必须复用冻结内容 395 bytes/SHA-256 `706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`；engine 为 `D:\texlive\2026\bin\windows\lualatex.exe`，6,656 bytes/SHA-256 `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`。
- 只允许一个 root-external controller invocation 与一个 direct LuaLaTeX child invocation；retry/latexmk/version-probe/second invocation均0。`TEXMFVAR=TEXMFCACHE=TEXMFCONFIG=TEXMFHOME`必须解析到同一个 fresh R16 `texcache`。
- 任一首错立即停止并保留现场，不修改cache配置、不修补、不第二调用。成功必须自然 exit0，回 controller/child PID、UTC、duration、source/wrapper/controller/engine before/after identities、唯一 PDF identity与terminal TeX-family0，随后明确释放槽。
- 成功后永久禁止更多 TeX；只允许从唯一新 PDF 做一次非TeX完整 N/C/manual/native1x+NN8x/color/grayscale/overlap/clip/math/caption/page回归与 single legal seal。必须重点量化 x1/x2 legend 的颜色、occupied runs 与 internal blanks，不能只凭静态因果宣称 PASS。
- 未授权 source edit、commit、fresh role、second UID 或 central write。

## 并行状态

- P689 保持同一 fresh SA3 `/root/sa3_fig_p689_r115_fresh_isolated_v1`，等待一个 sealed PASS/FAIL；未计 local pass。
- Inventory 不变：`30 SA1 / 30 SA2 / 1 SA3 / 39 local pass`；strict final `0/99`，B `66/66`。

