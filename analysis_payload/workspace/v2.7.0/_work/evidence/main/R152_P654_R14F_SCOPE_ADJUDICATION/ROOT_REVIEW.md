# R152 P654 R14F 主线范围裁决

## 结论

`MAIN_SCOPE_ADJUDICATION_ACCEPT_R14F_LOCAL_SA2_EVIDENCE`

保留fresh root的`ROOT_REJECT_R14F`报告与handoff为不可变审计历史；其唯一拒绝点来自派发范围过宽，不触发第二root、R14G或重复证据重建。

## 主线只读复算

- sealed root：`_work/dialogues/A_visual/evidence/figures/FIG-P654-01/STRICT_R14F_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- CSV manifest：1059行；JSON manifest：1059行；实际payload：1059文件。
- 两manifest字段均为：`relative_path,bytes,sha256,mtime_utc_ticks,mtime_utc_7digit`。
- CSV/JSON duplicate：0/0。
- CSV↔JSON path set：0差；五字段：0差。
- manifest↔FS path set：0差；五字段：0差。
- ordinary：1062；readonly：1062。
- 不早于WRITE_STOPPED的文件：0；WRITE_STOPPED领先：828027 ticks。

## 范围解释

Goal、严格figure evidence schema与Revision151 grant要求最终manifest对FS闭合path、bytes、SHA与100ns ticks；R14F已经满足。`csv_equals_json_all_six_fields`位于1052行R10 source/destination copy identity双表的约束，其中六字段包括source_relative_path与destination_relative_path。最终单根manifest没有第二个源/目标路径，因此五字段是正确且完整的身份模式。

## 后继授权

A只允许对P654唯一图源做一个原子提交并返回immutable handoff，状态为`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`。在主线核验并集成前，不更新中央inventory，不启TeX，不派fresh SA1/SA3。
