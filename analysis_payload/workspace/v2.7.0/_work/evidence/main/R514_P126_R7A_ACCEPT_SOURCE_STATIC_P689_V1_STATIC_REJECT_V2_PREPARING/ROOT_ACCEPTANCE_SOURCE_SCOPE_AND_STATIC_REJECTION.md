# R514 Main root acceptance, narrow source scope, and static rejection

时间：2026-08-28T12:54:46+08:00

## P126 R7A

Main独立只读复算并接受`STRICT_R7A_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`。copy188、payload190、controls3、ordinary193、dirs含root13；COPY_IDENTITY与PAYLOAD_MANIFEST的path/bytes/SHA256/CreationTimeUtc ticks/LastWriteTimeUtc ticks及集合差均为0。193/193 files与13/13 dirs含root均ReadOnly。WRITE_STOPPED为1,466 bytes/SHA-256 `37530553BEB8BCD851A0513704D91D9E1E4B37DB3BF8F4D6090943E526AB40DD`，25 physical lines/25 unique keys/bad0，含root strict-latest margin 5,999,517,414 ticks，at-or-after excluding marker=0。Old R7 before/after snapshot同为`AD5807BDAE18B149FF92278E51D1031C03EF8917BF8DECCDCA3894E8DED10D5D`；destination postmarker double snapshots同为`D27F817643872E7D4087A13E04F243B61DE5D0945567AEE2B3C93BB78A919540`。CSV9/JSON11 parse、ADS、cache/pyc、reparse失败均0。

Root-external controller result为1,934 bytes/SHA-256 `7E0137E4BE30F3B9B2C0990D90430E093F8204817C89BE0CAC306D02BD25956F`且当前可写；它不位于sealed root，因此不构成root reject。Main绑定该当前身份并禁止后续修改。

P126继续计SA2，保留R7业务`LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`及三个hard。仅授权目标单源从4,366 bytes/SHA-256 `20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279`开始做STATIC_ONLY三项修复：真正断开的x2 legend segments、label6避开axis/contour、label7避开marker/arrow。未授权build、commit或fresh role。

## P689 V1 static scripts

Main全文静态审查V1 controller 32,756 bytes/SHA-256 `2E3E0916A10D20C6FCF691D1B7165133FD69E94A0F4650E4532F043D269265DA`与auditor 24,565 bytes/SHA-256 `4018D567B8DCF3D345CFF00B96315C0DAD10F86F1F561BE965D0091F07E889FB`。V1保持ReadOnly、invocation0/0且永久冻结。

V1静态拒收有两个决定性缺口：其一，auditor只解析控制CSV/JSON，却将`CSV_JSON_PARSE_PASS`概括为全root通过，没有动态枚举并严格解析最终root全部业务CSV/JSON；其二，controller/auditor没有通过root-external POSTMARKER_ROOT_STATE和CONTROLLER_RESULT绑定controller双快照，也没有证明controller S1=S2=auditor S1=S2。

仅授权V2 STATIC PREPARATION：保留clean43→payload45/controls3/ordinary48、五字段复制、全树ReadOnly、future marker sole-final、old-root/ADS/cache-pyc/reparse0合同；新增controller两次完整postmarker state及result绑定，auditor读取并验证result/state且自行双快照，四快照相等；动态枚举最终root全部CSV/JSON、严格UTF-8/no-BOM解析并报告exact counts/fail0。V2只回冻结身份、AST/sites、微测、absence与invocation0/0后PAUSE，未授权执行或fresh SA1。

Inventory保持`30 SA1 / 31 SA2 / 0 SA3 / 39 local pass`，严格最终0/99。
