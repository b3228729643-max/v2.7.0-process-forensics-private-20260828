# FIG-P547-01 R12A SA3 机械独立复核

结论：**MECHANICAL PASS**

范围仅为 R12A ADS 修复重封包的机械核验；不重做语义审计，不宣称最终全书 PASS。

## assigned_scope

目标包：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P547-01\STRICT_R12A_SA3_BLIND_R98_ADSFIX_20260824`

核验旧包未动证明、普通证据树对账、最终 inventory/manifest、ADS、终止顺序、分母与失败计数、R98/C01 SHA、C01 工作树及 P654 SA2 隔离。

## completed

- `ADS_RESEAL_REPORT.md`、`sa3_reseal_summary.json` 与 terminal crosscheck 均声明旧包只读未改；R12A 对旧包排除 6 个授权重生成 seal-metadata 后的 1856 个普通证据文件独立逐文件对账：missing=0、mismatch=0；1856 文件树 SHA=`4be1180bfed14b94b761c39c13615a3ac21986f8f7b4ea3ed48aa078c30cb224`，与声明一致。
- 普通文件实际总数=1864；manifest 列出 1862 个可哈希文件，全部存在、可读且 bytes/SHA 一致（missing=0、bad=0）；排除 manifest 与 marker 后实际普通文件=1862。manifest inventory 的 listed_file_count=1862、final_expected_ordinary_file_count=1864 一致。
- 大小写折叠重名=0；全包 NTFS stream 枚举非默认 ADS=0、非默认 stream bytes=0。
- `WRITE_STOPPED` 最后写入：2026-08-24T22:32:11.7836115+08:00；其他文件最大写入：2026-08-24T22:31:38.3916620+08:00。marker 内容以 `WRITE_STOPPED` 结尾；terminal crosscheck 的 `next=reports_then_manifest_then_WRITE_STOPPED` 与实际顺序一致。
- 分母未漂移：text parents 23、vector parents 34、objects 57、object pairs 1596、glyphs 193、path records 71、path pairs 2485、commands 143、within-record command pairs 186。
- 失败/归属机械计数均为零：object pairs PASS=1596、glyph PASS=193、path records PASS=71、command replay PASS=143；role-ratio PASS=53；unassigned component pixels=0；clip boundary pixels=0；glyph/object/role/ownership 失败计数均为 0。within-record 74 `PASS_DISJOINT` +112 `PASS_SAME_RECORD_COMPOSITION`=186；path pairs 2450 disjoint +26 same-semantic design +9 `DESIGN_CONNECTION_CONFIRMED`=2485。
- 官方 R98 PDF SHA 独立复算=`52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`；C01 source SHA 独立复算=`DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`；均与 identity/summary/manifest 声明一致。
- C01 业务源相对 dialogue_A_visual HEAD 无 diff（`git diff --quiet` 返回 0）；P654 SA2 授权源无 status 变化，本次未触碰。

## files_changed

仅新增本报告：`v2.7.0/_work/dialogues/A_visual/reports/P547_R12A_MECHANICAL_VERIFY.md`。R12A 包、旧 R12 包、C01 业务源及 P654 SA2 源均未修改。

## decisions

- **MECHANICAL PASS**：R12A 包通过本次全部机械门槛。
- 结论限定为本封存包机械复核通过，不是全书最终接受。

## unresolved

无机械未决项。

## validation

- R12A manifest 1862 项全量可读并独立验证 bytes/SHA；实际最终普通文件 1864。
- 旧包→新包 preserved evidence：1856/1856 路径、大小、普通流 SHA 全部一致。
- ADS 全量扫描：非默认 ADS=0。
- C01 工作树 HEAD diff=0；P654 status 检索无变更。

## next_action

由 root 继续后续流程；本报告不授权任何语义重审、源文件修改或全书最终放行。
