# P654 R12 主线复核与 R13 授权

- 时间：2026-08-25T09:30:00+08:00
- 对象：`FIG-P654-01`
- 中央角色：保持 `SA2`
- R12 root 报告：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R12_ROOT_AUDIT.md`
- 报告 SHA-256：`15C9104BAD871CD15CE0A5E14DAAABFC2452F8A6D6CDFB1DF6E9FDFBF8861C08`
- 主线裁决：接受 `ROOT_REJECT_R12`

## 决定性缺口

1. R12 文件系统实际 `ordinary=1062=payload1059+controls3`，但 `WRITE_STOPPED.json.ordinary_file_count=1059`。
2. `R12_PRESEAL_VALIDATION.json.ordinary_extension_denominator` 的 JSON 采用最终 payload 口径、CSV 采用最终 ordinary 口径，字段内无单一成立集合。

R10 基础 1052 的 path/bytes/SHA/NTFS ticks 零差、R12 payload1059 双 manifest、resolved provenance、解析/ADS/cache/seal卫生及内容层反证均可作为 R13 的差分输入；它们不能把 R12 变成接受包。R10/R11/R12 均永久只读。

## R13 唯一授权范围

- 仅做全新 evidence-only control reseal；业务源、TeX、Git、fresh SA1/SA3 均禁止。
- 直接复制 R10 基础 1052，不复制 R11/R12 新增控制 payload；重新生成 R13 的 identity、resolved structured provenance、prepare/validator/seal 与预验报告。
- manifest 只排除三个最终 controls：两个 manifest 与 `WRITE_STOPPED.json`。所有 R13 脚本、identity、provenance、预验报告均进入 payload。
- 所有集合字段必须以名称和快照显式区分：`payload_file_count`、`manifest_control_file_count=2`、`write_stopped_control_file_count=1`、`control_file_count=3`、`ordinary_file_total=payload+control`。若保留 `ordinary_file_count`，它必须与 `ordinary_file_total` 和最终文件系统普通文件数完全同一。
- 扩展名分母不得使用无快照限定的 `ordinary_extension_denominator`。预验报告须分别写 `expected_final_payload_extensions`、`expected_final_control_extensions`、`expected_final_ordinary_extensions`；最终 WSTOP 再写实际 `payload_extensions`、`control_extensions`、`ordinary_extensions`，并逐扩展满足 ordinary=payload+control。
- 封存前 validator 必须对总文件数与 JSON/CSV/PNG/PDF 四类逐项断言；seal 写 WSTOP 前须按“现有 payload + 两 manifest + 即将写入的 self”计算最终 ordinary，并在写入后由新的独立 root 回读验证。
- 任一未展开 `$` 占位符、任一口径不唯一、任一等式/字段/FS 不同即 FAIL，不得封成 PASS。
- R13 封存后启动另一全新独立 root；只回正式 accept/reject 与不可变 handoff。接受前 P654 保持 SA2，不提交、不派 fresh 角色、不计 A_LOCAL_PASS。

## 不变边界

- inventory：`43 SA1 / 55 SA2 / 0 SA3 / 1 A_LOCAL_PASS`。
- 严格最终：`0/99`。
- R101 不重建、不复验。
