# R488：P683 SA3 control reseal V1 首错冻结与 V2 静态修订授权

时间：2026-08-28T09:15:26+08:00

## 裁决

- P683 fresh isolated SA3 的业务结论继续保留为 `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`：physical732/printed719，N31/C465，manual elements31/31、pairs465/465，hard/clip/illegal/unresolved均0；P683仍处于SA3，不计C_LOCAL。
- 原业务root继续永久标记 `ROOT_REJECT_PREMATURE_MARKER_BEFORE_READONLY_FREEZE`，不得写入、修补、重封或作为合规seal接受。
- V1 sibling control-reseal 分类为 `CONTROL_RESEAL_V1_FAIL_UNDEFINED_MANIFEST_PROPERTY_BEFORE_NEW_ROOT`。本失败是控制脚本静态字段名错误，不回退业务结论，也不迁移角色。

## V1 已冻结事实

- 冻结controller：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P683_R115_SA3_CONTROL_RESEAL_V1\P683_SA3_CONTROL_RESEAL_V1_CONTROLLER.ps1`，23,517 bytes，SHA-256=`D516DA1B25B6BC6BB3F3878B0B3BE4841B89D0592A73C3551E129039436A831B`。
- 唯一controller调用：PID2524，invocation1/retry0/second=false，`2026-08-28T01:12:47.3865511Z`至`2026-08-28T01:12:47.9985569Z`，natural success=false，exit1。
- 首个且唯一异常：`The property 'RelativePath' cannot be found on this object. Verify that the property exists.`
- Main只读复核旧`MANIFEST_SHA256.csv`的属性名严格为`TYPE,RELATIVE_PATH,BYTES,SHA256`；V1 controller错误访问`$row.RelativePath`，因此在copy/new-root阶段前即失败。
- auditor invocation0；required V1 new root Leaf/Container/Any=false；`SOURCE_ROOT_BEFORE.csv`存在，7,823 bytes/SHA-256=`E6FEC3FB12DDD16980D98E5212103FAB065C70C71E8BA5F818EA1C3CA8F3E8F8`；postmarker/controller-result/auditor-result/staged-marker均不存在。
- rejected source root仍41 files/3 dirs incl root，全ReadOnly；old manifest SHA=`6552FAD53836A9D0E3A0368A98C868AD3BB8B4C2BC955C27F1D231D89920294E`、old marker SHA=`435C310BEBB54CE13403133A7487D4769954F53D223F87049BA1C7684E1B66D9`不变。
- V1脚本、外部失败场景和旧root永久冻结；禁止脚本编辑、第二调用、retry、repair、cleanup、原地reseal或复用V1 new root。

## 仅授权 V2 STATIC PREPARATION

- HANDOFF_ID=`C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V2`
- OPERATION=`P683_R115_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V2`
- required new root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1_control_reseal_v2`
- Main授权时精确门：Leaf=false、Container=false、Any=false、Parent=true。
- 必须使用新的root-external V2 controller/auditor与独立空artifacts目录；不得修改、调用或清理V1脚本与V1 artifacts。
- V2导入旧manifest后必须先严格验证`PSObject.Properties.Name`含且仅按合同提供`TYPE,RELATIVE_PATH,BYTES,SHA256`所需列，并验证39个FILE material行的四字段均非空；后续明确使用`$row.RELATIVE_PATH`、`$row.BYTES`、`$row.SHA256`。
- 静态包必须包含真实旧manifest的只读微测：rows42、FILE39、undefined-property failures0、canonical file/dir set diff0、duplicate0；不得只用合成对象证明。
- 保持既定控制合同：只复制39 FILE material，old MANIFEST/WSTOP复制0；COPY_IDENTITY+resolved COPY_PROVENANCE后payload41；controls恰PAYLOAD_MANIFEST/SEAL_AUDIT/WRITE_STOPPED三项；ordinary44。复制与manifest绑定canonical relative/resolved path、bytes、SHA-256、Creation/LastWrite FILETIME。
- 所有premarker files/dirs/root必须先设ReadOnly并核验；root外生成一行一键、no-BOM、已解析完整、ReadOnly且future-FILETIME的marker；唯一final root operation为marker move；之后只能root-external只读snapshot/audit，要求含root strict latest、at-or-after0、postmarker0、source-root before/after0及JSON/CSV/ADS/cache-pyc/reparse0。
- C只回传V2 controller/auditor路径、bytes、SHA、ReadOnly、AST/site统计、schema/canonical真实微测、new-root与artifacts absence、controller/auditor invocation0/0，然后必须PAUSE。此revision没有授予任何V2执行token或调用。

## 并行边界

- A/P126继续且仅继续R3A唯一PDF的非TeX全量回归、真实manual与single seal；不得再TeX/build、commit、fresh role或第二UID。
- 禁止其他UID/role、source/Git/central/process操作。inventory保持`31 SA1 / 31 SA2 / 1 SA3 / 37 local pass`，严格最终0/99。
