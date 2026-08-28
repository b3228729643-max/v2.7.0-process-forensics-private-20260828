# R313 — P641 R110 fresh SA1 接受与 fresh SA3 授权

- 时间：2026-08-27T06:57:03+08:00
- UID：`FIG-P641-01`
- 接受 HANDOFF：`C-FIG-P641-01-R110-SA1-FRESH-ISOLATED-V1`
- actual instance：`/root/sa1_fig_p641_r110_fresh_isolated_v1`
- sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa1_r110_fresh_isolated_v1`
- 主线裁决：`SA1_PASS_ACCEPTED / READY_FOR_DIFFERENT_FRESH_ISOLATED_SA3`

## 内容接受

- 独立定位 current R110 physical 691 / printed 678 / Fig33.8。
- fresh 分母 `N=177`（162 visible non-whitespace glyph + 15 foreground drawing/path），完整 unordered pairs `C=15,576`，critical subset 154。
- 人工账 glyph162、graphic15、critical154、low-profile7、role/script13、view/role17，均无 blank/pending/non-PASS。
- 真实 hard failure、illegal overlap、clip、missing/tofu/wrong codepoint/math/semantic/geometric error均为0。
- 显式9.2pt blanket annotation 已逐字 native1x/nearest8x 打开；字形完整、清楚、平衡，按R168仅 `ADVISORY_ONLY`。
- 条件核与Markov毯语义重算一致：`p(alpha)`在theta更新中消去，保留`p(theta|alpha)p(z,y|theta)`，毯变量为`{alpha,z,y}`。

## 主线独立机械核对

- manifest declared/entries=`1208/1208`，ordinary/expected=`1210/1210`。
- manifest↔FS missing/extra/path-bytes-SHA mismatch=`0/0/0`。
- files readonly=`1210/1210`；dirs readonly=`7/7`。
- ADS/cache/pyc/reparse=`0/0/0/0`。
- `WRITE_STOPPED`唯一，严格最后 margin=`436,972,017` NTFS ticks；at-or-after excluding marker=`0`。
- manifest SHA-256=`5862A3F2C54AD0821FF060FF0317B938BF90F51598AF4960AC5D53C7AD616397`。
- WSTOP SHA-256=`0D185413AE95B3D8BA0B091D58C6BF3D832F8DCC93F7571638402F66CD4215A6`。

## 主线代表性视觉复核

主线实际打开 `figure_crop_300dpi.png`、`grayscale_300dpi.png`、`semantic_object_overlay_300dpi.png`、包含9.2pt说明的 `glyph_contact_sheet_03.png` 与 `critical_contact_sheet_01.png`。图、题注、灰度、公式、节点/边/虚线毯与说明均完整清晰；无裁切、非法重叠、错位或明显失衡反证。

## 授权

授权 C 启动一个且仅一个不同实例的 completely fresh isolated R110 SA3：

- 必须 `gpt-5.6-sol/xhigh/fork_turns=none`、全新 HANDOFF_ID 与启动前不存在的新root；
- 白名单仅R110/current P641 source/root `GOAL.md`/direct strict protocol-schema/必要当前V5-C04正文；
- 绝对禁读本SA1、既有SA2与全部旧P641/其他UID/main acceptance/state/inventory/chat/Git-history结论；
- 禁止 `collaboration.list_agents` 及任何agent/thread/task状态或身份查询；
- PDF/main/source只读，TeX/source write/Git/central writes/第二UID/第二角色=0；
- 从零定位、分母、all-pairs、native1x/8x、语义、真实人工账、一次WSTOP-last封存；PASS仅回主线等待`C_LOCAL_PASS`接受。

actual identity回传前，inventory保持`32 SA1 / 43 SA2 / 0 SA3 / 24 local pass`。

