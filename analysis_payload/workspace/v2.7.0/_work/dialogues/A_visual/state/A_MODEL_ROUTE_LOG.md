# Dialogue A 模型路由日志

| HANDOFF_ID | FIGURE_ID | ROLE | MODEL | REASONING | STATUS | WRITE_SCOPE |
|---|---|---|---|---|---|---|
| A-R130-P608-SA2-RESUME-20260824 | FIG-P608-01 | SA2 | gpt-5.6-terra | high | local_sa2_accepted_await_r99 | 单一 P608 图源 + A 本地证据 |
| A-R130-P608-MECH-VERIFY-20260824 | FIG-P608-01 | MECH_VERIFY | gpt-5.6-luna | medium | mechanical_pass | A 本地只读验证 + 根报告 |
| A-R99-P608-SA1-FRESH-20260824 | FIG-P608-01 | SA1 | gpt-5.6-terra | max | fail_to_sa2_after_r5a_metadata_reseal | 官方 R99 + 主线 P608 源只读；R5 时间戳隔离、R5A 仅包装重封 |
| A-R130-P654-SA1-RESUME-20260824 | FIG-P654-01 | SA1 | gpt-5.6-sol | xhigh | fail_to_sa2 | A 本地 P654 证据；业务源只读 |
| A-R130-P654-SA2-REPAIR-20260824 | FIG-P654-01 | SA2 | gpt-5.6-terra | high | interrupted_before_evidence | 单一 P654 图源；保留 22+21 diff |
| A-R130-P654-SA2-REPAIR-V2-20260824 | FIG-P654-01 | SA2 | gpt-5.6-sol | max | local_sa2_pass_committed_e392bd8 | 单一 P654 图源 + 全新 A 本地证据 |
| A-R130-P547-SA3-RESUME-20260824 | FIG-P547-01 | SA3 | gpt-5.6-sol | xhigh | a_local_pass_after_r12a_reseal | A 本地 P547 证据；业务源只读、盲审隔离 |
| A-R130-P547-MECH-VERIFY-20260824 | FIG-P547-01 | MECH_VERIFY | gpt-5.6-luna | medium | fail_ads_only | A 本地只读验证 + 根报告 |
| A-R130-P547-R12A-MECH-VERIFY-20260824 | FIG-P547-01 | MECH_VERIFY | gpt-5.6-luna | medium | mechanical_pass | A 本地 R12A 只读验证 + 根报告 |
| A-R99-P715-SA1-FRESH-20260824 | FIG-P715-01 | SA1 | gpt-5.6-terra | max | invalid_isolation_state_files_read | 作废；4 个初步文件仅作污染历史，禁止引用 |
| A-R99-P715-SA1-FRESH-B-20260824 | FIG-P715-01 | SA1 | gpt-5.6-terra | max | fail_to_sa2_after_r1c_metadata_reseal | 官方 R99 + 主线 P715 源只读；R1B 元数据隔离、R1C 仅包装重封 |
| A-R99-P608-SA2-NARROW-20260825 | FIG-P608-01 | SA2 | gpt-5.6-sol | max | active_build_slot_granted | 单一 P608 图源 + 新 R6 本地证据；唯一受控 TeX 槽 |
| A-R100-P654-SA1-FRESH-20260825 | FIG-P654-01 | SA1 | gpt-5.6-sol | xhigh | active_fresh_isolated | 官方 R100 + 主线 P654 源只读；禁止任何旧 P654 结论与状态 |
| A-R141-P654-SA2-R11-EVIDENCE-RESEAL-20260825 | FIG-P654-01 | MECH_RESEAL | gpt-5.6-luna | medium | sealed_then_root_reject | 仅新R11证据根；R10/业务源只读，禁TeX |
| A-R141-P654-R11-ROOT-AUDIT-20260825 | FIG-P654-01 | ROOT_AUDIT | gpt-5.6-sol | xhigh | root_reject_r11 | R11只读；仅写外部root报告，禁TeX/源码/state/inventory |
| A-R141-P654-SA2-R12-CONTROL-RESEAL-20260825 | FIG-P654-01 | MECH_RESEAL | gpt-5.6-luna | medium | sealed_then_root_reject | 仅新R12证据根；R10/R11/业务源只读，禁TeX |
| A-R141-P654-R12-ROOT-AUDIT-20260825 | FIG-P654-01 | ROOT_AUDIT | gpt-5.6-sol | xhigh | root_reject_r12 | R12/R10/R11只读；仅写外部root报告，禁TeX/源码/state/inventory |
| A-R145-P654-SA2-R13-CONTROL-RESEAL-20260825 | FIG-P654-01 | MECH_RESEAL | gpt-5.6-luna | medium | sealed_then_root_reject | 仅新R13证据根；R10/R11/R12/业务源只读，禁TeX |
| A-R145-P654-R13-ROOT-AUDIT-20260825 | FIG-P654-01 | ROOT_AUDIT | gpt-5.6-sol | xhigh | root_reject_r13 | R13/R10/R11/R12只读；仅写外部root报告，禁TeX/源码/state/inventory |
