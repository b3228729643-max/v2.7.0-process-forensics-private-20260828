# R479 P126 R1A V2静态门通过与调用授权

时间：2026-08-28T07:48:48+08:00

## 通过身份

- Controller：`P126_R1A_CONTROL_RESEAL_CONTROLLER_V2_20260828.ps1`，26,109 bytes，SHA-256=`899F9491F1C8FCCFECF0AF72922B3AEF434E2B9CC11605CA22F70AE8A04D6B7E`，ReadOnly，PowerShell7 AST errors0。
- Auditor：`P126_R1A_CONTROL_RESEAL_AUDITOR_V2_20260828.ps1`，21,071 bytes，SHA-256=`948D6BA8247D06FADF35208CBFADCF2A693414D90950E09FE1EE4159A2BEE760`，ReadOnly，AST errors0。
- Controller Move-Item恰1，目标为root-external staged marker到固定R1A的最终move；auditor Move-Item0。两脚本destructive/delete、process-management、TeX-engine、retry-specific while/do均0。
- V1两脚本保持原身份ReadOnly且invocation0，永久不得调用。

## Main逐文件与真实manifest复核

V2在导入source manifest后立即把反斜杠转为forward slash，并以canonical relative path贯穿resolved rows、copy、COPY_IDENTITY、COPY_PROVENANCE、PAYLOAD_MANIFEST及expected sets；Group-Object全部使用属性访问，无PSCustomObject字典索引器。Main对真实旧manifest只读复算：rows52、backslash rows40、canonical duplicate groups0、canonical expected/simulated actual case-sensitive difference0；固定destination仍Leaf/Container/Any=false。

Controller代码闭合：source manifest/marker固定SHA门；安全相对路径与escape门；52份material复制并保持path/bytes/SHA/Creation+LastWrite FILETIME；新增identity/provenance后payload54；controls3、ordinary57；premarker56 files与全部dirs/root先ReadOnly并核验；25行marker在root外生成、语法/unique key通过、future FILETIME且ReadOnly，唯一final move入根；随后含root strict-latest、at-or-after0、postmarker双快照同一、old root before/after同一；result仅写root外。

Separate auditor代码独立复算copy identity、payload manifest path/bytes/SHA/ticks、ordinary canonical set、全files/dirs/root ReadOnly、marker key/hash/count/order、structured parse、ADS/cache-pyc/reparse、destination snapshot与controller同一、old root未变；audit result仅写root外。

固定模型：HANDOFF=`A-R115-P126-SA2-R168-READONLY-CONTROL-RESEAL-V1-20260828`；operation=`P126_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`；copy52→payload54/controls3/ordinary57。

## 唯一调用授权

1. 执行上述冻结controller恰一次，`invocation=1/retry=0`，首错即停。
2. 只有controller自然success且冻结身份未变时，执行上述冻结separate auditor恰一次，`invocation=1/retry=0`，首错即停。
3. 禁止任何脚本修改、自动或手工第二调用、原地repair/reseal、业务PDF/render/visual/N/C/pair/manual/math/semantic重跑、旧R1写、source scope、source/TeX/build/Git/process/其他UID-role。
4. 成功后回controller/auditor start/end/exit、root counts/identity/readonly/marker/order/postmarker/source0差、root controls SHA及root-external immutable result/audit/handoff；失败则只回首错与保留状态。

P126仍SA2，业务`FAIL_TO_MAIN_SOURCE_SCOPE`仅在Main接受新control reseal后才可进入source scope。P683仅按R478继续静态准备。inventory保持`32 SA1 / 31 SA2 / 0 SA3 / 37 local pass`。
