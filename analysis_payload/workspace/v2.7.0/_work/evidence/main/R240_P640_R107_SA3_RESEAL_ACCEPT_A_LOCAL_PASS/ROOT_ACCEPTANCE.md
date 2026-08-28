# FIG-P640-01 R107 fresh SA3 与只读重封根验收

- revision: `240`
- accepted_at: `2026-08-26T15:32:10+08:00`
- verdict: `ROOT_ACCEPT_RESEAL / SA3_PASS / A_LOCAL_PASS`
- strict_final_book_pass: `false`

## 合法角色与业务结论

- HANDOFF_ID=`C-FIG-P640-01-R107-SA3-FRESH-ISOLATED-V1`
- actual instance=`/root/sa3_fig_p640_r107_fresh_isolated_v1`
- model/effort=`gpt-5.6-sol/xhigh`
- fork_turns=`none`
- official candidate=`R107`，physical page `690` / printed page `677` / Figure `33.7`
- 分母 `N=28`、`C=378`，glyph `145`、drawing `20`、critical `42`；真实硬失败、canonical illegal overlap、clip、unresolved 均为 `0`。
- `.99` marker、`|\rho|\to1^-`、ACF `rho^(2k)`、ESS `(1-rho^2)/(1+rho^2)`、题注及页面融合均通过；R168 微小像素/排印差异仅保留 advisory。

主线已在 Revision 239 独立确认原内容根除“未设只读”外的所有门均通过；本 revision 不重跑视觉或角色，仅验收一次 evidence-only control reseal。

## 新重封根

根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa3_r107_fresh_isolated_v1_reseal_v1`

- 原根普通文件=`621`；新 `material` 文件=`621`；`COPY_IDENTITY.csv` 行=`621`，relative path duplicate=`0`。
- source/destination resolved path、bytes、SHA-256、NTFS mtime 对 `621/621` 均完全一致；差异=`0`。
- `MANIFEST.sha256` 行=`623`，解析=`623`；目标恰为 `621 material + COPY_IDENTITY.csv + RESEAL_PROVENANCE.json`，missing/extra/duplicate/path/hash mismatch均=`0`。
- 最终普通文件=`625=623 payload+manifest+WRITE_STOPPED`；`625/625` 只读，writable=`0`；根目录 ReadOnly bit=`true`。
- `WRITE_STOPPED` 是唯一最新文件；同mtime或更晚的其他文件=`0`。ADS/cache/pyc/reparse=`0/0/0/0`。
- 控制引用哈希逐项一致：
  - COPY_IDENTITY=`704A23C80074B9CE1189C8F1FFA87D87EEE9C64670A175A3424E40543B901006`
  - RESEAL_PROVENANCE=`0BF450774B86372E093B00871D459D1A72B895759E5B75D4E5FAC99E361D60EE`
  - MANIFEST=`D5DA3E820F66D5A65D939EE15B3C5252EB54F53181AAF0491A2A927C7483E164`
  - WRITE_STOPPED=`8BBC1B4520D3849EC9FC6287B83F75D7A86FB761F14F12A7BAC1A6857ADED867`

## 中央迁移

FIG-P640-01 在同一 revision 内按合法实际身份完成 `SA1 → SA3 → A_LOCAL_PASS`。不得重复该 UID 的 SA1/SA3，不需 SA2、源码修改、PDF 重建或 TeX。全书严格最终仍为 `0/99`，本接受仅是单图 local pass。

