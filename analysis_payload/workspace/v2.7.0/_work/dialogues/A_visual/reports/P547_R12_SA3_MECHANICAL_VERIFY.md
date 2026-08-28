# FIG-P547-01 R12 SA3 机械独立复核

结论：**MECHANICAL FAIL**

范围仅为已封存 SA3 包的机械核验；不宣称最终全书 PASS，不重做语义审计。

## assigned_scope

封存包：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P547-01\STRICT_R12_SA3_BLIND_R98_20260824`

核验 WRITE_STOPPED 终止顺序、manifest/terminal/report/summary 可读性与引用、inventory、ADS/大小写重名、分母与失败字段、9 个路径接点、R98/C01 SHA、C01 工作树相对 baseline/HEAD 差异及 P654 SA2 授权源隔离。

## completed

- `WRITE_STOPPED` 内容最后一行是 `NO_WRITES_AFTER_THIS_MARKER`；其写入时间晚于其他文件（最大其他文件时间早约 1 ms）。`terminal_crosscheck.json` 声明 `manifest_then_WRITE_STOPPED`，manifest 的 `next` 为 `WRITE_STOPPED`，顺序一致。
- manifest 1860 entries；独立递归计数（排除 manifest 与 marker）=1860；所有 1860 项存在、可读，bytes 与 SHA-256 均与 manifest 一致。
- 大小写折叠重名=0。
- 分母在 summary/report/底层 CSV 对齐：objects 57、object pairs 1596、glyphs 193、path records 71、path pairs 2485、commands 143、within-record command pairs 186；text parents 23、vector parents 34 亦与声明及 CSV 对齐。
- final CSV 机械计数：object pair PASS=1596、glyph PASS=193、path record PASS=71、command replay PASS=143、within-record 74 `PASS_DISJOINT` +112 `PASS_SAME_RECORD_COMPOSITION`=186；role-ratio PASS=53；unassigned component pixels=0；clip boundary pixels=0；各失败计数=0。
- path pair final ledger：2450 `PASS_DISJOINT` +26 `SAME_SEMANTIC_DESIGN_COMPOSITION` +9 `DESIGN_CONNECTION_CONFIRMED`=2485。9 个 pair 逐条记录为：0276(D005,D007)、0282(D005,D013)、0344(D006,D010)、0352(D006,D018)、1674(D031,D040)、2162(D046,D048)、2168(D046,D054)、2189(D047,D051)、2197(D047,D059)。
- 独立复算 SHA：官方 R98 PDF=`52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`；C01 source=`DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`，均与 identity/summary/manifest/report 声明一致。
- C01 业务源在 `dialogue_A_visual` 工作树相对 HEAD 无 diff；本次未触碰当前 P654 SA2 授权源。

## files_changed

仅新增本报告：`v2.7.0/_work/dialogues/A_visual/reports/P547_R12_SA3_MECHANICAL_VERIFY.md`。封存包、业务源及 P654 SA2 源未修改。

## decisions

- **MECHANICAL FAIL**：封存包检测到 2 个非 `:$DATA` NTFS alternate data streams（ADS），均挂在 `_tmp/texmf-cache/luatexja/extra_notoserifsc-extralight`：`1.lua.gz`（72949 bytes）与 `1.luc`（422176 bytes）。该项违反“有无 ADS”机械门槛。
- 其余机械核验项通过；ADS 是唯一发现的机械失败项。

## unresolved

- 封存包 ADS 未处理；按要求不修改封存包，因此保持 MECHANICAL FAIL。

## validation

- manifest 全量存在/可读/大小/SHA 校验：`missing=0 bad_manifest_entries=0 unread=0`。
- 递归 inventory、大小写重名、NTFS stream 枚举及时间顺序均独立复算。
- `git -C ...dialogue_A_visual diff --quiet HEAD -- C01/fig_v5_c01_transition_graph.tex` 返回 0。

## next_action

由 root 决定是否在新的授权封存流程中清除 ADS 并重新生成/复核封存包；本报告不授权任何封存包或业务源改动。
