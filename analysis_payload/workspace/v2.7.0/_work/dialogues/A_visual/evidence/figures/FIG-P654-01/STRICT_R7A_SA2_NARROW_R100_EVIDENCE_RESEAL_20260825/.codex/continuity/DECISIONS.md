# 持久决策

## D-001

- status: active
- date: 2026-08-25
- decision: R7A 只复制白名单机器证据；所有 R7 人工账、人工结论、finalizer、terminal、SA2_REPORT 与 RESULT 均不得迁移。
- reason: 主线 P654 R7 root audit 已因批量生成与循环确认拒绝 R7 人工证据。
- affected_scope: R7A evidence staging and validation
- affected_files: `machine_reuse/**`
- supersedes: NONE

## D-002

- status: active
- date: 2026-08-25
- decision: 所有人工 decision 行由当前 reviewer 实际打开证据后使用 apply_patch 显式写入；任何脚本只能只读消费。
- reason: 关闭 G1--G3，禁止 default/global/bulk-generated manual PASS。
- affected_scope: all R7A manual ledgers
- affected_files: `manual/**`, `tools/consumer_validator.py`
- supersedes: NONE

