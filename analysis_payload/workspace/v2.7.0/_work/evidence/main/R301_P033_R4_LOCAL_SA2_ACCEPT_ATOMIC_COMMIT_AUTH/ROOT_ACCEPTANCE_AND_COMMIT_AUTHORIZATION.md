# R301 P033 R4本地SA2验收与原子提交授权

- 时间：`2026-08-27T05:01:32+08:00`
- HANDOFF_ID：`A-R110-P033-SA2-DIRECT-BUILD-R4-20260827`
- 中央裁决：`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`；尚非A_LOCAL_PASS。

## 构建与内容

- 唯一direct LuaLaTeX已自然exit0并释放；invocation1/retry0/latexmk0，TeX终态NONE。
- 新PDF：31,553 bytes，SHA-256 `CECFB8085EE0DB6327607879DE4600A45F4F8B312D4E1B2A9BAE9B675156153A`。
- N52=38 glyph+14 drawing；C=1,326；manual glyph38/drawing14/critical16/views6，全PASS，R168 hard FAIL0。
- 旧R2886映射为G0001“子”—D0003下边界：native300dpi shared0、21个连续空白行；PDF保守bbox净距9px。
- 主线实际打开整图彩色/灰度、target native1x与overlay nearest8x，确认标签与下平面边界清楚分离，无裁切、不可读或新回归。

## 根封存

- root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R4_SA2_R3_COORDINATE_DIRECT_BUILD_R110_20260827`。
- manifest122/122；主线复算path/bytes/SHA mismatch0。
- ordinary125；125/125文件与13/13目录只读。
- WSTOP严格最后，margin4,715,821 ticks，at-or-after0。
- CSV manifest SHA `3D9FEB33F5114B8D39ED3D974F62AC872E97DC4F11C907581AAEAA6A9F34FA5B`；JSON SHA `82CC454038DFF72C546D27A3F95065D15C317932792677B6DBF98ECF39C4B9D6`；WSTOP SHA `DB29767B8123D785BCEC6FE6E559201D9CECEA2C713D45CDF221175206DBEC62`。

## Git授权

- A worktree branch=`v2.7.0/dialogue-a-visual`，HEAD=`4a8c489488fd12e5584e2042535fefcd548b62b7`。
- 当前精确仅`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex` modified；numstat1+/1-、diff-check PASS、index empty。
- 唯一差异：`(-.18,-.23)`→`(-.18,-.39)`；after source SHA-256 `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`。
- 授权恰一个仅含该源的原子commit；禁止第二commit、TeX、fresh角色、第二UID与central state/inventory写入。完成后回不可变commit handoff供主线集成。

- inventory保持`31 SA1 / 44 SA2 / 0 SA3 / 24 local pass`。
