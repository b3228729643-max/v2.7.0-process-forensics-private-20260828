# R393：P067 R113静态补丁接受与唯一direct build槽

- 时间：2026-08-27T19:48:32+08:00。
- HANDOFF=`A-R113-P067-SA2-STATIC-P4-COORDINATE-PATCH-20260827`。
- 目标源：`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`。

## 静态补丁验收

- before=4014 bytes/SHA-256=`2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`；after=4014 bytes/SHA-256=`11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144`。
- A worktree仅该源modified；name-only1、numstat1+/1-、staged0、`git diff --check` PASS。
- exact唯一diff：`at (axis cs:4.08,.89) {$p_4$};`→`at (axis cs:4.08,.85) {$p_4$};`。x、文本、anchor、mass style、font、fill/opacity、inner sep、CDF/PMF、端点、guides、axes、题注及其他token0变。
- R10 static root payload5/controls3/ordinary8；manifest5/FS5 unique且path/bytes/SHA/NTFS ticks mismatch0。8/8 files与root只读；`WRITE_STOPPED.json`唯一严格最后+583,372,812 ticks，at-or-after0；postmarker0，JSON/ADS/cache-pyc/reparse0。
- current-mask只读投影为约8 native px下移：对其余128对象交集0；G008 center/blank=6/5px，G009=7/6px，下一对象20.10px。仅为build授权依据，不计render或local PASS。

## 唯一构建锁

- preflight：TeX-family process count0。
- 唯一新根（授权时file=false/dir=false）：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827`。
- 允许恰一次root-external PowerShell7 controller invocation，内部恰一次direct LuaLaTeX typeset child；`invocation=1`、`retry=0`、`latexmk=0`、`version-probe=0`。
- 必须使用R11新root下独立`TEXMFVAR/TEXMFCACHE/TEXMFCONFIG`，记录controller/child PID、开始/结束UTC、自然exit、唯一PDF bytes/SHA，及source/wrapper/controller前后bytes/SHA。
- 禁止fullbook、第二controller、第二typeset、Resume/retry、并发TeX、超时中断后自动重启、源写、第二源、commit、fresh role、第二UID、central state写。
- 成功或失败均须先确认controller/child自然终止并回终态TeX四类进程；仅自然成功释放后可进行非TeX全图/N/C/manual证据。构建失败不得自行消费第二槽。

## 当前库存

- inventory=`31 SA1 / 38 SA2 / 0 SA3 / 31 local pass`；严格最终0/99，B累计66/66。
