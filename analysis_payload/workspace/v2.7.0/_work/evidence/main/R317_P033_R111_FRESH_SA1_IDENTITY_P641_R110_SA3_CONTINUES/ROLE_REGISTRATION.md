# R317 — P033 R111 fresh SA1 身份登记；P641 R110 SA3 继续

## P033

- UID：`FIG-P033-01`
- HANDOFF_ID：`A-R111-P033-SA1-FRESH-ISOLATED-20260827`
- actual instance：`/root/p033_r111_fresh_sa1`
- model/effort/fork：`gpt-5.6-sol/xhigh/fork_turns=none`
- evidence root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827`
- 启动前实例自证：2026-08-27T07:55:49.884+08:00 时 DirectoryExists=false、FileExists=false，parent exists=true，尚无 evidence write。
- 冻结输入：R111 PDF 4,967,076 bytes / SHA-256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`；main当前P033 source SHA-256 `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`。
- 白名单与绝对禁读边界按 R316 完整生效；PDF/main/source只读，TeX/Git/central/第二UID/第二角色/agent状态查询均为0。同一实例从零直跑一次sealed PASS/FAIL；PASS只请求另一个fresh isolated SA3。
- P049保持冻结，不与P033并发启动。

## P641

- `/root/sa3_fig_p641_r110_fresh_isolated_v1` 已确认继续且仅继续启动时冻结的R110 PDF/current P641 source与同一证据根。
- 禁止读取、比较、引用或迁移R111及新候选结论；禁止重启或重复角色。TeX/source/Git/central/第二UID/第二角色保持0。

Inventory：`32 SA1 / 42 SA2 / 1 SA3 / 24 local pass`。
