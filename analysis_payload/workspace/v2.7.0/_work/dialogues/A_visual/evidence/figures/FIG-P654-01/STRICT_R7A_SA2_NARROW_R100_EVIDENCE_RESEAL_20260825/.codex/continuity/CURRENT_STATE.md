---
task_id: P654-R7A-SA2-EVIDENCE-RESEAL
state_revision: 1
charter_revision: 1
status: active
current_phase: machine-evidence-staging
last_checkpoint_id: R7A-INIT
last_updated_at: 2026-08-24T21:32:49Z
---

# 已完成里程碑

- 完整读取 current Goal、strict protocol、strict schema、P654 R7 root mechanical audit。
- 锁定 R7 rejection 的 G1--G5 与 R7A 唯一写域。

# 当前工作集

- sealed R7 只读机器证据。
- 本 R7A 新根、staging 工具与 continuity 文件。

# 已修改文件

- 仅本 R7A 中的 continuity、authority 和工具文件。

# 当前正在执行

- 精确复制允许复用的 R7 机器证据并生成 source/destination 身份账。

# 待完成

- 当前外部 PowerShell 进程/Git scope 探针与 G5 reconciliation。
- 203 条独立人工裁决。
- consumer validator 身份冻结、执行和 terminal 复核。
- manifest/parse/ADS/WRITE_STOPPED 封存。

# 当前阻塞项

- NONE。

# 最近一次验证

## 验证范围

- 权威文件存在并已完整读取；R7 顶层与证据目录只读盘点完成。

## 尚未验证

- R7A staged artifact 身份、全部人工门、terminal 和 seal。

# 不得重复

- 不执行 R7 内脚本；不复制 R7 manual/finalizer/result artifacts；不启动 TeX；不修改业务源。

# 下一条精确操作

运行本 R7A `tools/stage_machine_evidence.ps1` 一次，仅把白名单机器证据复制到 `machine_reuse/`，生成逐文件身份账并验证所有 source/destination SHA 相等。

