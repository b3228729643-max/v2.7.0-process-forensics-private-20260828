# R210｜FIG-P639-01 R104 fresh isolated SA1 中央接受

- 中央裁决：`ACCEPT_SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`
- HANDOFF_ID：`C-FIG-P639-01-R104-SA1-FRESH-ISOLATED-V1`
- 官方候选：R104，物理页 689（印刷页 676，图 33.6）
- 证据根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa1_r104_fresh_isolated_v1`

## 接受结论

fresh SA1 从零闭合 N=32（20 text/formula + 12 graphic）、C=496/496、147 glyph、36 critical pair、22 peer-role、32 clip 与 14 multiview。数学与当前正文一致：两条满条件正态分布分别为 `N(0.45,0.64)` 与 `N(0.60,0.64)`，共同方差和均值参考线正确；caption、图号、曲线、均值线和正文命题/证明一致。

全部 pair 的共享像素总数为 843，逐项归因于轴—刻度—箭头连接、填充区域基线闭合、密度曲线交点和均值参考线与曲线交点等合法几何；非法重叠、mask contamination 与 clip 均为 0。R168 下未见缺字/tofu/错码/数学语义错误、实际不可读或明显严重字号失衡。

主线实际打开彩色/灰度 figure crop、object overlay 与 critical contact sheet；两条曲线、虚实线冗余、均值参考线、共同方差说明、坐标、caption与页面融合均清楚。P639 从 SA1 迁入一个完全 fresh isolated R104 SA3，不计 A_LOCAL_PASS。

## 中央机械复核

- manifest 声明/行数/实际 payload：503/503/503；ordinary=505；
- path、resolved path、bytes、SHA-256、NTFS FILETIME、duplicate、missing、extra：差异均 0；
- payload 与 manifest 只读失败 0；非默认 ADS=0；cache/pyc=0；
- WSTOP 严格最新，领先前一文件 270,806,921 ticks；
- manifest SHA-256：`7F2375275808C897D2B6A020BCDE41097824AA10C62F63D4F39B99813D9B3944`；
- manual object/all-pair/glyph/critical/view/peer/clip：32/496/147/36/14/22/32；空观察 0；
- `analysis_pipeline.py` 不生成或覆盖 manual ledgers；
- TeX、源码修改、提交：均为 0。

## Inventory 迁移

- 迁移前：`34 SA1 / 53 SA2 / 0 SA3 / 12 A_LOCAL_PASS`
- 迁移后：`33 SA1 / 53 SA2 / 1 SA3 / 12 A_LOCAL_PASS`
- 全书严格最终：仍为 `0/99`

