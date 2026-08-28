# Revision 221｜R105 fresh SA1 实际身份登记

- 登记时间：`2026-08-26T06:19:28+08:00`
- 官方候选：R105，817页，4,967,209 bytes，SHA-256 `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`。
- 构建锁：空闲且未授权；三个角色均只读、禁TeX、禁源码写入。

## 实际运行身份

1. FIG-P608-01
   - HANDOFF_ID：`A-R105-P608-SA1-FRESH-ISOLATED-20260826`
   - instance：`/root/p608_r105_fresh_sa1`
   - evidence root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R13_SA1_FRESH_ISOLATED_R105_20260826`
2. FIG-P639-01
   - HANDOFF_ID：`MAIN-R105-P639-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
   - instance：`/root/r105_p639_fresh_sa1`
   - evidence root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826`
3. FIG-P640-01
   - HANDOFF_ID：`MAIN-R105-P640-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
   - instance：`/root/r105_p640_fresh_sa1`
   - evidence root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826`

## 中断件处置

- `FIG-P639-01\sa1_r105_fresh_isolated_v1` 仅创建空目录，未形成实际身份或证据；标记 `UNSEALED_INTERRUPTED`，永久不读不写、不用于裁决。
- `FIG-P640-01\sa1_r105_fresh_isolated_v1` 仅含两张未封存渲染PNG，未形成实际身份、人工账、报告或handoff；标记 `UNSEALED_INTERRUPTED`，永久不读不写、不用于裁决。

## 中央迁移

- P608、P639、P640各从SA2迁至SA1。
- inventory：`35 SA1 / 52 SA2 / 0 SA3 / 12 A_LOCAL_PASS`。
- 严格最终仍为`0/99`；任何SA1 PASS只转另一个fresh isolated SA3，不能直接计本地通过。
