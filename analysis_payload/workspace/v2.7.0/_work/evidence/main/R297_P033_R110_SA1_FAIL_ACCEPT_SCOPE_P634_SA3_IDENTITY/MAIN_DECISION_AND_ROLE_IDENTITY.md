# R297｜P033 SA1 FAIL 接受、最窄源码范围与 P634 SA3 身份

## P033

- accepted handoff：`A-R110-P033-SA1-FRESH-ISOLATED-20260827`
- sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R2_SA1_FRESH_ISOLATED_R110_20260827`
- verdict：`FAIL_TO_SA2 / NO_SA3`
- denominator：`N99=85 glyph+14 drawing`，`C4851`，critical10

唯一R2886为G036“子”顶横与D002下侧平面斜边native300dpi共享24px、clearance0。主线实际打开raw1x、overlay1x、nearest8x、intersection和figure crop，确认是可见实墨相交，不属于R168字体微差。

根审计：`PAYLOAD_MANIFEST.csv`正确SHA=`24743D9EC710C67878F65C84E0197F1C2FB43E14432BA8C781EF951B0D8A6C21`；481/481 payload path/bytes/SHA mismatch0；ordinary493，493/493文件与22/22目录只读；WSTOP严格最后、at-or-after0。pre-manual int16 selector provisional7和首次preseal三项断言exit1均已透明纠正，未改变最终分母、人工账或R2886结论。

仅授权唯一源 `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex` 的static-only补丁：只可把第16行 `子空间 $S$` 节点的纵坐标向下做最小位移；x、文字、anchor、字体/字号/颜色、平面/向量/其他标签公式和其余坐标全部不变。先回before/after SHA、精确1+/1-、diff-check与300dpi静态净距估算；未授TeX/commit/fresh role。

## P634

- HANDOFF_ID：`C-FIG-P634-01-R110-SA3-FRESH-ISOLATED-V1`
- actual instance：`/root/sa3_fig_p634_r110_fresh_isolated_v1`
- model/effort/fork：`gpt-5.6-sol/xhigh/fork_turns=none`
- new root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P634-01\sa3_r110_fresh_isolated_v1`
- startup root existed：`false`

白名单与隔离边界符合R296：禁SA1/SA2/全部旧P634/其他UID/main acceptance和agent/thread/task查询；PDF/main/source只读，TeX/源写/Git/central writes/第二角色为0。

状态迁移：P033 `SA1→SA2`，P634 `SA1→SA3`；inventory=`31 SA1 / 44 SA2 / 1 SA3 / 23 local pass`。
