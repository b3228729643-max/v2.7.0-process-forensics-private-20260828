# Revision 265｜P582 集成、P609 fresh SA1 identity、R109 build lock

时间：2026-08-26T21:52:37+08:00

## P582 integration

- A atomic commit=`a5ac3100915781bd7ce918b534de46f7611dceb6`，parent=`7a0c4f45c8be66cc53c5a73d0d01685b2559ea43`。
- 主线独立核验 exact name-only 恰为 `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_running_mean.tex`，numstat=`12/12`，source SHA=`4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`，A worktree clean。
- 主线从 clean HEAD `e33a3b7490ba39304181c25f775221e63a35b6a4` cherry-pick 成功，new HEAD=`59e7afd81ba3171ab9de5c90ed589fed3424155e`；主线 source SHA 与 A 同一，主线 worktree clean。
- P582 local evidence/commit/handoff 现冻结；在新官方候选前不启 fresh role。

## P609 fresh SA1 actual identity

- UID=`FIG-P609-01`；HANDOFF_ID=`C-FIG-P609-01-R108-SA1-FRESH-ISOLATED-V1`。
- actual instance=`/root/sa1_fig_p609_r108_fresh_isolated_v1`；model/effort=`gpt-5.6-sol/xhigh`；fork_turns=`none`。
- new root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa1_r108_fresh_isolated_v1`，启动前不存在；status LIVE，未restart/duplicate。
- 白名单/禁读边界与 Revision264 完全一致；同一实例直跑至sealed结果，TeX/source/Git/central writes/second UID-role均为0。
- 中央角色迁移 `P609 SA2→SA1`。

## R109 unique build lock

- P582已集成，必须冻结新官方候选后才能对P582执行fresh SA1；主线现发布唯一R109全书构建锁。
- 计划唯一父调用：`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r109_fullbook -NoPublish`，从main clean HEAD `59e7afd81ba3171ab9de5c90ed589fed3424155e`执行。
- 禁止A/B/C启动、终止或管理任何latexmk/lualatex/luatex/luahbtex；P609 fresh SA1可继续纯只读并行。
- 主线不自动启动第二父调用；若平台中断或失败，先如实冻结状态再单独裁决。

## Central accounting

- inventory=`32 SA1 / 48 SA2 / 0 SA3 / 19 local pass`；严格最终仍为`0/99`；B累计66/66。

