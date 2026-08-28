# R529 V2 静态拒收与 V3 授权

- 时间：2026-08-28T15:19:27+08:00
- inventory：`30 SA1 / 30 SA2 / 1 SA3 / 39 local pass`；严格最终0/99；B 66/66。

## 已验证事实

P126 R12A V2冻结身份：

- controller 20,415 bytes，SHA-256=`18667C412C90E6FE7BB846E0EE8A08D129F55AF0062891CEEC189CA77E306E7B`，ReadOnly，AST0，Move1；
- auditor 21,270 bytes，SHA-256=`45106F81B60EB98EA18C829212B883EC138A16860505AC22DAA0A5E9D9503A7D`，ReadOnly，AST0，Move0；
- invocation0/0；destination、V2 stage、controller result、auditor result均不存在；
- V1 current identities保持18,212/`44C4E5FB...D1A3F`与19,183/`59D1A62D...8CFEC`，未调用。

Main从两份V2冻结脚本分别提取实际`Get-FullTreeAdsAudit`并无写运行。Old R12 root为items147=137 files+9 child directories+root，streams137、nondefault ADS0；代表child `build`、`BUILD_RESULT.json`与controller script均成功且nondefault0。V2所有stream调用均为`-ErrorAction Stop`，SilentlyContinue0。

## 决定性拒收原因

Auditor line149--150读取并要求28行marker，line158要求28个unique keys；controller result同样记录28/28。Auditor line190却将待写出的结果硬编码为`marker_lines=26;marker_keys=26`。因此一次自然成功的V2链也会生成与刚刚验证的marker和controller result相冲突的外部审计事实。

裁决：`STATIC_REJECT_AUDITOR_MARKER_COUNT_RESULT_DRIFT`。V2不得执行或编辑，保持invocation0/0永久冻结。

## 唯一后续授权

只授权V3 STATIC PREPARATION：

- HANDOFF=`A-R115-P126-SA2-DIRECT-BUILD-R12-CONTROL-RESEAL-V3-20260828`
- operation=`P126_R115_R12_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V3`
- destination继续为startup-absent `STRICT_R12A_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`
- 新冻结V3 controller/auditor与V3唯一stage/results；不得创建destination或执行。

V3保留V2 copy137→payload139、controls3、ordinary142以及规范路径、五字段复制、source/destination full-tree ADS Stop门、全树ReadOnly、root-external future ReadOnly marker sole-final move、old-root before/after0、postmarker0、dynamic CSV/JSON、cache-pyc/reparse合同。唯一控制修复为auditor result的marker counts必须从已验证集合派生为28/28，并通过pre-write in-memory consistency check；V3中不得残留语义上的literal26。

返回V1/V2身份不变、V3 identities/ReadOnly/AST/sites、V2→V3 exact diff、helper/parser-result微测、destination/stage/results absence与invocation0/0后，再次暂停等待Main逐文件审查。

P689同一fresh SA3 actual继续独立运行，未接受sealed结果前不迁移inventory。
