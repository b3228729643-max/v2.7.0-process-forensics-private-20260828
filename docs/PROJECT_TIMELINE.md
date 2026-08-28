# 项目过程时间线（压缩版）

完整逐 revision 事实见：

- `analysis_payload/workspace/v2.7.0/_work/state/CURRENT_STATUS.md`
- `analysis_payload/workspace/v2.7.0/_work/evidence/main/`
- `analysis_payload/workspace/v2.7.0/_work/handoff/`

## 阶段 1：恢复、冻结输入与建立权威索引

- 从 GOAL、runtime core、context capsule、current task 恢复任务。
- 冻结原书、候选 PDF、源文件身份和图表 scope。
- 建立 A/B/C 分工、单写者、构建锁和中央 inventory。

## 阶段 2：B 内容线批量闭合

- 内容/数学线完成 66/66。
- 主要工作转移到图形视觉、构建与多角色复核。

## 阶段 3：A/C 视觉线逐图 SA2/SA1/SA3

- 每图独立定位 PDF 页、冻结 reader-visible denominator、生成 all-pairs ledger。
- 打开 full/native/grayscale/overlay/ROI/NN8x。
- 逐对象、逐 pair、glyph、math、semantic、page 复核。
- PASS 后再进入 fresh isolated 后续角色。

## 阶段 4：发现 hard defect 后的局部源码修复

- Main 授最窄 single-source scope。
- A 做 STATIC_ONLY 补丁与静态几何投影。
- Main 授一次 direct LuaLaTeX build。
- 从新 PDF 全量回归。
- 若 hard 仍存在，再回 source scope。

P126 是该循环的典型：geometry、legend、label6/7、text–curve collision 多轮修订，最终形成 R116，但 fresh SA1 又发现新的曲线与文字实墨碰撞。

## 阶段 5：控制封存与 evidence-only reseal

- 业务账闭合后生成 manifest/audit。
- 全树设 ReadOnly。
- root 外构造 future-dated marker，唯一 final move 入根。
- controller 与独立 auditor 验证 snapshots/strict-latest/ADS/cache/reparse。

许多轮次在此阶段因一次性 PowerShell 细节失败，转入 sibling control reseal，成为主要额外耗时来源。

## 阶段 6：提交、集成与官方全书候选

- 局部 source 在业务与控制接受后才获 atomic commit。
- Main 以一次 cherry-pick 集成。
- 再执行唯一 fullbook 构建与全书审计。
- 当前官方候选为 R116。

## 归档时阶段

- 中央 revision 550。
- B 线已完成；视觉线仍在 P126/P690 等 UID 上推进。
- P690 已在归档过程中回 sealed SA2 PASS，等待 Main 接受。
- P126 R19A V2 控制重封仍处静态审查/未执行状态。

