# 当前问题与阻塞

## I-001

- status: active
- severity: fatal-until-closed
- description: R7 G1--G3 人工账由 finalizer 批量生成、备注不特异、critical 分类循环确认。
- location: sealed R7 manual/finalizer artifacts
- next_action: 在 R7A 重新实际打开全部规定证据并显式写入对象/关系特异人工账。
- related_decision: D-001, D-002

## I-002

- status: active
- severity: provenance
- description: R7 terminal 早于最终 finalizer 且缺 phase-time SHA；历史 TeX pre/post process 状态未机器捕获。
- location: sealed R7 build/process evidence
- next_action: 冻结 R7A consumer validator 执行前 SHA，并在 terminal 复核；另以当前外部只读探针和 reconciliation 明确 observed/authority/UNKNOWN。
- related_decision: D-001

