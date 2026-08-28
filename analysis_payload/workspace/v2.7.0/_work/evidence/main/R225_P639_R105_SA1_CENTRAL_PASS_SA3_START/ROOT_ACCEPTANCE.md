# Revision 225｜P639 R105 SA1中央纠正假失败并启动fresh SA3

- 时间：`2026-08-26T07:20:00+08:00`
- UID：`FIG-P639-01`
- SA1 HANDOFF_ID：`MAIN-R105-P639-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
- 官方候选：R105物理页689，PDF SHA-256 `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`。

## SA1 证据与中央裁决

- SA1分母：147 glyph + 10 visible graphics=`N157`；全部unordered pairs=`12,246/12,246`；empty masks0、independent illegal overlap0、clip0。
- SA1唯一报告失败R00008：x轴`−2`的minus与y轴`0`的PDF/vector bboxes clearance=0，但final-visible raw masks交集0、墨迹净距28.0689px。
- 主线独立打开`R00008_native1x_8x.png`：两枚实际可见墨迹明显分离，远高于4px门；字框相触只来自不可见font bbox留白，不能替代final-visible ink geometry。
- 因此撤销`FAIL_TO_SA2`，中央裁决=`SA1_PASS_ACCEPTED`。R168字体微差仍advisory；页面融合、灰度、数学语义、题注文字及可读性全部PASS。
- 封存机械：manifest197/declared197，ordinary199；逐文件path/bytes/SHA 0 mismatch；199/199只读，ADS0，WSTOP绝对最后/封后0写，manifest SHA `2F539AEA41BFC2ABBB84B953B219DDDD80890DBD3A473723B09F20C9524F1998`。

## SA3 实际身份

- HANDOFF_ID：`MAIN-R105-P639-SA3-FRESH-ISOLATED-20260826`
- instance：`/root/r105_p639_fresh_sa3`
- evidence root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa3_r105_fresh_isolated_v3_main_20260826`
- fork_turns=none；绝对禁读本SA1及全部旧P639结论，仅读R105/当前单源/Goal-protocol-schema/必要正文；禁TeX/源码写入/提交/第二UID。

## 中央状态

- P639由SA1迁至SA3。
- inventory=`32 SA1 / 53 SA2 / 2 SA3 / 12 A_LOCAL_PASS`；严格最终`0/99`。
