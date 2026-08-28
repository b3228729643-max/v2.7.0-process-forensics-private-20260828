# R518 — P126 R9 review and P689 V3 control failure routing

时间：2026-08-28T13:26:44+08:00

## P126 R9

- 唯一direct build自然完成并释放：controller/direct child=`1/1`，retry/latexmk/version-probe/second=`0/0/0/0`，exit=`0/0`，终态TeX-family0。
- 唯一PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828\build\v260_FIG-P126-01_standalone.pdf`，34,051 bytes，SHA-256=`CE80FD14D39FE32269BF8535B0381006338AD14D9490292FB5B07230AFDA5573`。
- source4,361/SHA=`85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81`、wrapper/controller/engine前后身份同一。
- Main实际打开300dpi整图、legend crop与label crop；x2短图例仍视觉连续，故不预判PASS。A继续同一PDF唯一非TeX全量复审与single seal；未授权任何新source写、commit或fresh role。

## P689 V3 first-error stop

- Frozen controller：38,490 bytes/SHA-256=`0BE8E71908C95DCF3D5B8020E98874F10C0B5E9B30EBADC4616505CF75FEF975`，ReadOnly；唯一invocation1/retry0，exit1。Frozen auditor：39,674 bytes/SHA-256=`80443BC0EC8DF7085E3FCA8ECCFB54F8C3B30FF2250499EEE9163B4FC7479C87`，invocation0。
- 首错=`A parameter cannot be found that matches parameter name 'ne'.`。决定性站点为controller L345与L527：`if (Get-NonDefaultAdsCount -LiteralPath ... -ne 0)`未将函数调用括起，PowerShell把`-ne`解析为函数参数。
- 失败发生在copy前。Destination仅被创建为空、可写、无reparse/ADS的目录；actual stage、POSTMARKER_ROOT_STATE、CONTROLLER_RESULT、AUDITOR_RESULT、COPY_IDENTITY、COPY_PROVENANCE、PAYLOAD_MANIFEST、SEAL_AUDIT、WRITE_STOPPED均absent。
- 正式分类=`UNSEALED_CONTROL_FAILURE_BEFORE_COPY`。V3 scripts、空destination与全部失败现场永久冻结，不得复用、删除、重命名、retimestamp、补写、retry、repair或手工封存。旧P689业务root与业务方向保持不变。

## V4 STATIC_ONLY route

- 新HANDOFF=`C-FIG-P689-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V2`。
- 新OPERATION=`P689_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V2`。
- 必须startup-absent sibling root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa2_r115_r168_readonly_adjudication_v1_control_reseal_v2`。
- V4仅把两处比较改为`if ((Get-NonDefaultAdsCount -LiteralPath ...) -ne 0)`，并更新新身份/root/control-dir；不得扩大V3合同。
- 仍须clean43→payload45/controls3/final48、五字段、全树ReadOnly、唯一actual stage、future sole-final marker、strict latest含root、at-or-after0、old-root0write、controller S1=S2=auditor S1=S2、动态CSV8/JSON2 strict parse、真实files/dirs/root ADS、cache-pyc/reparse/postmarker0。
- 仅授权脚本静态物化与无写微测，invocation0/0后PAUSE；未授权执行、fresh SA1、source/TeX/build/Git/central/process/new UID或second role。

Inventory仍为`30 SA1 / 31 SA2 / 0 SA3 / 39 local pass`；严格最终0/99。
