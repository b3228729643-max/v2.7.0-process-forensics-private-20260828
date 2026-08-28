# R509：P126 R7 控制失败裁决与 R7A 静态准备授权

时间：2026-08-28T12:22:00+08:00

## 业务方向

P126 R7 fresh业务证据已闭合为N58/C1653，保留`LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`方向。三项hard：

1. `HARD-LEGEND-X2-CONTINUOUS`：x2图例样线仍为连续实线，未形成断开段。
2. `HARD-LABEL6-AXIS-CONTOUR-OVERLAP`：数字6被纵轴与contour穿过实墨。
3. `HARD-LABEL7-MARKER-ARROW-OCCLUSION`：数字7被marker与arrow遮蔽。

Main已实际打开H01/H02/H03 color nearest8x并确认三项；数学、题注、clip、tofu与unresolved无新增反证。该业务方向尚未激活source scope，须先取得合规sealed control root。

## R7 root拒收

- 唯一seal controller invocation1/retry0；auditor invocation0。
- controller 9,931 bytes/SHA-256 `6D811AB2DFA92A5A021F816DD05B34C22CD6C4C314D55006853C35CDAFCC61B9`，ReadOnly。
- 首错发生于任何control写前：188个`[ordered]` rows经`Group-Object -Property relative_path`均得到空键，误报duplicate；显式`{ [string]$_['relative_path'] }`对相同冻结rows复算duplicate groups0。
- Main核对R7 root：188 files、106,277,337 bytes、13 dirs including root；188/188 files及13/13 dirs/root均可写；`PAYLOAD_MANIFEST.csv/json`、`PRESEAL_VALIDATION`与`WRITE_STOPPED`均不存在。
- 正式分类=`UNSEALED_CONTROL_FAILURE_BEFORE_ANY_CONTROL_WRITE`。旧R7 root、失败controller及现场永久冻结，不原地repair/retry/reseal/retimestamp。

## 仅授权 R7A STATIC PREPARATION

HANDOFF_ID=`A-R115-P126-SA2-DIRECT-BUILD-R7A-CONTROL-RESEAL-V1-20260828`  
operation=`P126_R115_R7_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`  
fixed root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7A_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`

Main即时门：destination Leaf/Container/Any=false、Parent=true；TeX-family0。

本轮只允许在root外物化并冻结ReadOnly controller/auditor scripts，随后回报并PAUSE。静态合同：

- 精确复制R7当前188 material，old controls copied0；保持canonical relative/resolved source+destination path、bytes、SHA256、CreationTimeUtc ticks、LastWriteTimeUtc ticks。
- 新增`COPY_IDENTITY`与resolved `COPY_PROVENANCE`，形成payload190；controls恰`PAYLOAD_MANIFEST`、`SEAL_AUDIT`、`WRITE_STOPPED`三项；ordinary193。
- controller必须StrictMode empty-safe，禁止缺失属性访问；所有dictionary字段使用显式indexer或强类型对象；CaseSensitive duplicate/set闭合。
- 全部premarker files/dirs/root先设ReadOnly并验证；marker在root外生成no-BOM、one nonempty KEY=VALUE per line、绑定resolved roots/counts/manifest+seal SHA/verdict/business-rerun=false/postwrites0，设strict-future FILETIME+ReadOnly后，以唯一Move作为绝对final root content/attribute operation。
- move后仅root-external只读snapshot/result；auditor独立复算copy/provenance/manifest/full-tree readonly、marker schema/binding、strict latest including root、at-or-after0、old-root before/after0、postmarker0、CSV/JSON/ADS/cache-pyc/reparse0。
- scripts必须AST0；controller Move-Item恰1且仅final marker move，auditor0；destructive/process-management/TeX/retry-loop0。

静态准备回报须包含scripts bytes/SHA/ReadOnly、AST/sites、真实188-row canonical/duplicate/set与StrictMode微测、destination/stage/results absence、controller/auditor invocation0/0。没有后续Main显式ACK不得执行。

未授权PDF/render/business/manual/math/semantic重跑、source修改、TeX/build、commit、fresh role、第二UID或central写。
