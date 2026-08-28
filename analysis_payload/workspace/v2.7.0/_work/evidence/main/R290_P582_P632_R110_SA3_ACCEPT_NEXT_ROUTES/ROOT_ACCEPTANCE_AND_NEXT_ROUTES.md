# R290 — P582/P632 R110 fresh SA3 接受与下一并行路线

## P582：A_LOCAL_PASS

- actual=`A-R110-P582-SA3-FRESH-ISOLATED-20260827` / `/root/p582_r110_fresh_sa3` / `gpt-5.6-sol/xhigh/fork_turns=none`。
- 内容闭合：N156=139 glyph+17 drawing/path，C12090，critical89；manual=139/17/89/5/18，nonPASS0；illegal overlap/clip/empty/pair-hard/pixel-hard均0。
- 主线只读复算：ordinary217，217/217文件只读；5/5目录只读；JSON/CSV parse0，ADS/cache/pyc/reparse0；WSTOP唯一严格最后，margin393,210,220 ticks，at-or-after0。
- R8没有filesystem `PAYLOAD_MANIFEST.json`。R285的fresh SA3明确硬门为单次seal、WSTOP绝对最后与封后0写，并未授权后临时追加per-file FS manifest门；`object_manifest.json`与分母/人工账已闭合，因此主线不回派无损重封。
- 主线实际打开figure crop、grayscale及`critical_relations_03.png`；“↓ 再下降”与`.380`有清楚实墨净距，彩色/灰度/题注/页面融合无反证。
- 裁决：`A_LOCAL_PASS`；P582 source/evidence/report/handoff/角色永久冻结。

## P632：C_LOCAL_PASS

- actual=`C-FIG-P632-01-R110-SA3-FRESH-ISOLATED-V1` / `/root/sa3_fig_p632_r110_fresh_isolated_v1` / `gpt-5.6-sol/xhigh/fork_turns=none`。
- 内容闭合：N14/C91；另有22个文字语义ID覆盖151 spans/413 glyph records；manual objects14/pairs91/text22/ROI6/views7/hard12，nonPASS0；hard failure/illegal overlap/clip/unresolved均0，最小文字净距23px。
- N14是完整语义对象口径，文字与glyph另有全量覆盖，不是漏项；与SA1较细分母不作静默数值等同，只接受两种粒度均完整覆盖当前图面。
- 主线只读复算：ordinary40=manifested38+manifest+WSTOP；manifest38行对FS path/bytes/SHA差0；40/40文件、8/8目录只读；JSON/CSV parse、ADS/cache/pyc/reparse均0；WSTOP唯一严格最后，margin13,431,135 ticks，at-or-after0。
- 主线实际打开彩色、灰度、semantic overlay与note/caption nearest8x；联合等高线、两条截面/映射、条件密度公式、零边缘说明和题注均清楚，无裁切/错位/非法重叠。
- 裁决：`C_LOCAL_PASS`；P632 source/evidence/report/handoff/角色永久冻结。

## Inventory 与下一路线

- inventory=`31 SA1 / 45 SA2 / 0 SA3 / 23 local pass`；严格最终0/99；B保持66/66冻结。
- A获B02/`FIG-P033-01` R110 `READONLY_R168_ADJUDICATION_FIRST`：source=`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex`，2383 bytes，SHA=`4BCD50FE3BFDF1A3DCFC9089E103D256555949D859EC650F047CECB3A04EF6D4`。无真实硬缺陷则封`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`；有真实硬缺陷仅回最窄source scope。未授TeX/源写。
- C获B60/`FIG-P634-01` R110 `READONLY_R168_ADJUDICATION_FIRST`：source=`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_coordinate_sweep.tex`，4352 bytes，SHA=`903DE12067AF0B33F316EC09D65F6803F6BD212D64EB838F2FD8F264748F520E`。无真实硬缺陷则封`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`；有真实硬缺陷仅回最窄source scope。未授TeX/源写。
- 两路线actual identity回传前仍计SA2；各支线只启一个UID，不重复角色，不读取旧UID结论替代R110观察。
