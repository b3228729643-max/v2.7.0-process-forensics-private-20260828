# FIG-P640-01 R107 fresh SA3 根验收裁决

- revision: `239`
- timestamp: `2026-08-26T15:18:58+08:00`
- verdict: `ROOT_REJECT_READONLY_FREEZE_REQUIRED`
- content_direction: `PASS`
- central_status: `SA1`（在合法 actual identity 与新封存根一并回传前保守不迁移）
- A_LOCAL_PASS: `false`

## 已确认通过

- fresh SA3 内容证据方向为 PASS：`N=28`、`C=378`、glyph `145`、drawing `20`、critical `42`，真实硬缺陷、非法重叠、裁切和 unresolved 均为 0。
- `.99`、`|\rho|\to1^-`、ACF/ESS、题注与页面融合均通过。
- 原根 manifest 为 `618` 个目标、`7,458,269` bytes，manifest SHA-256=`CF91CE6FF27038BD797BA69A547697D91A69BF38578A12940DFEF0B1E74DE523`。
- `WRITE_STOPPED` 晚于 manifest 与 seal，且其后根内内容写入为 0；ADS/cache/pyc/reparse 均为 0。

## 唯一拒绝点

原 sealed root 的 `621/621` 个普通文件均仍可写，`readonly=0`。这违反最终证据根“全部普通文件只读”的机械硬门。因此当前根不得直接计 SA3 PASS 或 `A_LOCAL_PASS`；但该缺口不推翻已完成的业务/视觉 PASS，也不要求重跑 SA3。

## 唯一授权的最小修复

授权支线3执行一次 evidence-only control reseal/freeze：

1. 原根永久不修改；创建一个全新根。
2. 将原根 `621` 个普通文件逐字节复制到新根 `material/`，并以 resolved source/target path、bytes、SHA-256 证明 `621/621` 同一。
3. 新增 `COPY_IDENTITY.csv` 与 `RESEAL_PROVENANCE.json`，明确原 manifest、seal、WSTOP 的身份和本次只读重封原因。
4. 新 `MANIFEST.sha256` 覆盖 `621` 个 material 文件及上述两个控制载荷，共 `623` 个 payload；最后仅写一个新 `WRITE_STOPPED`。预期最终普通文件数为 `625=623 payload+manifest+WSTOP`。
5. 将新根及 `625/625` 个普通文件全部设为只读；属性冻结不得改变内容、bytes、SHA 或既有 mtime。
6. 根外只读终检必须证明：`625/625` readonly、WSTOP 唯一最新、WSTOP 后 0 写、missing/extra/duplicate/hash mismatch=0、ADS/cache/pyc/reparse=0。

禁止重新执行视觉、对象分母、pair、人工账或角色；禁止 TeX、源码修改、提交、第二 SA3、第二 UID。回传时必须补全本次 SA3 的 actual instance、model/effort、fork_turns 和原/新根身份。

