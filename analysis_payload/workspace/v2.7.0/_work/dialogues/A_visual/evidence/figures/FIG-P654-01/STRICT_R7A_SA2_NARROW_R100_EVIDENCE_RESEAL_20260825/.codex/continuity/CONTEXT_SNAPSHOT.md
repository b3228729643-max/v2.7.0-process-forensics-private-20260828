---
snapshot_id: R7A-SNAPSHOT-001
checkpoint_id: R7A-INIT
task_id: P654-R7A-SA2-EVIDENCE-RESEAL
state_revision: 1
charter_revision: 1
compaction_generation: 0
created_at: 2026-08-24T21:32:49Z
---

# 当前目标

完成 P654 R7A evidence-only reseal，重新建立可信人工裁决和 provenance，不修改 source/R7，不运行 TeX。

# 硬性约束摘要

sealed R7 永久只读；R7A 为唯一写域；人工账必须逐项显式写入；consumer 只能只读验证；最终只可请求 R7A root audit。

# 明确排除内容

不构建、不提交、不启动 fresh SA1/SA3、不迁移 R7 人工结果、不宣称 central/A local pass。

# 权威输入

current Goal、strict protocol、strict schema、P654_R7_ROOT_MECHANICAL_AUDIT.md。

# 已完成

四份权威输入完整读取；R7 顶层和相关目录盘点；G1--G5 已建问题条目。

# 当前正在处理

白名单机器证据 staging 与 source/destination 身份账。

# 待完成

外部 current-state 探针；203 条人工 decision；consumer identity/validation；terminal/seal。

# 关键决策

D-001：不迁移任何 R7 人工/finalizer/result；D-002：人工账仅 apply_patch 显式写入。

# 当前问题

I-001 G1--G3；I-002 G4--G5。

# 验证状态

尚无 R7A terminal；R7 machine facts仅由 root audit确认，需在 R7A 逐文件绑定。

# 已确认事实

目标 source SHA `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`；wrapper SHA `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`；PDF 43385 bytes/SHA `A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6`。

# 尚未确认的假设

NONE；所有未复核门保持 pending。

# 不得重复

不执行 sealed R7 脚本，不依赖 R7 manual ledger/terminal/result，不启动 TeX，不修改业务源。

# 精确恢复位置

本 R7A `tools/stage_machine_evidence.ps1` 尚未运行。

# 下一条精确操作

执行 `tools/stage_machine_evidence.ps1` 一次，确认复制白名单中不含任何 banned manual/finalizer/result 路径，并核对 identity ledger source/destination SHA mismatch 为 0。

