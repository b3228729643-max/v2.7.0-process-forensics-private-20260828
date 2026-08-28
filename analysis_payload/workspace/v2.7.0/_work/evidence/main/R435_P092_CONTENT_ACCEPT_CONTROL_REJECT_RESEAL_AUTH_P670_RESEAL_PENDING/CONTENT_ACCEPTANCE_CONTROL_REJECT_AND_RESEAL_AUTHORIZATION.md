# Revision 435：P092业务接受、控制根拒绝与唯一evidence-only reseal授权

时间：2026-08-28T02:33:30+08:00

## Main独立裁决

P092 fresh SA1业务方向接受为`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`，但R2 root正式`ROOT_REJECT_WSTOP_NOT_STRICT_LATEST`。该root不得作为sealed PASS，也不得原地修补、retimestamp或重封；P092继续计SA1，Main未授权SA3。

Main只读机械复算：root22 files、22/22 ReadOnly、root ReadOnly；`CONTENT_MANIFEST.csv`共20 rows，其中19个`ROOT_CONTENT` material和1个`FINAL_MARKER_EXPECTED`，19 material relative path/bytes/SHA mismatch均0。manifest=2,900 bytes/SHA `4DB477C19EE05CE8228BFA65FFC956FFEF3D5E67C131F758A840A267CFFF3E76`；WSTOP=283 bytes/SHA `6F2E8FD548248DEECD9580A34DC922D8F7B264FAB1E9F9BFBE608DFA9E29666C`。

决定性控制失败：WSTOP ticks=`639234517090705074`；`CONTENT_MANIFEST.csv` ticks=`639234517862341766`，晚`771636692` ticks；`PREMARKER_AUDIT.md` ticks=`639234518257890719`，晚`1167185645` ticks。files-at-or-after excluding marker=`2`，strict-latest margin=`-1167185645` ticks。最后move只能证明目录membership操作顺序，不能替代WSTOP文件mtime严格最新硬门。

## 业务证据接受

fresh denominator N21、all unordered pairs C210。object/pair machine rows与unique counts分别21/210，self/bad-ref0；manual objects21、pairs210、views7、math/semantic10、font advisory6，ID/tuple集合差0、blank0、non-PASS0。pair classes合计210，illegal visible-ink overlap、clip、unresolved均0。Main实际打开physical-page native300、figure crop native300、grayscale及critical nearest8x；二元熵端点、中心最大值、对称式、guides、labels、caption与页面融合清楚，无missing/tofu/wrong-codepoint、不可读、明显失衡、裁切、非法实墨重叠或数学语义反证。R168数值门仅advisory。

## 唯一控制重封授权

- HANDOFF=`A-R114-P092-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1-20260828`
- operation=`P092_R2_SA1_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- new root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R2A_SA1_R114_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`
- Main授权门：Leaf=false、Container=false、Any=false、Parent=true。

只复制旧`CONTENT_MANIFEST.csv`绑定的19个`ROOT_CONTENT` material；旧`CONTENT_MANIFEST.csv`、`PREMARKER_AUDIT.md`与`WSTOP`复制0。逐项保存source→destination relative path、bytes、SHA、CreationTimeUtc/LastWriteTimeUtc FILETIME并生成`COPY_IDENTITY.csv`与resolved `COPY_PROVENANCE.json`，故payload21。新controls恰`PAYLOAD_MANIFEST.csv`、`SEAL_AUDIT.json`、`WRITE_STOPPED`，ordinary24。

Root-external PowerShell7 controller/auditor执行前回静态path/bytes/SHA、AST parse errors0，并证明delete/retry-loop/TeX token0；controller唯一invocation1、retry0。完成全部payload/controls后，先将现有files/dirs/root设ReadOnly并核验；在root外生成一physical line一resolved nonempty `KEY=VALUE`的WRITE_STOPPED，禁止bare value、placeholder、TAB+`rue`、single-line concatenation，先设ReadOnly与严格晚于全部目标files/dirs/root的future NTFS mtime，再以single move作为唯一最终root content/attribute-affecting operation。marker后root content/attribute writes0；独立root-external auditor只写根外结果并复算old-root0写、new copy identity、manifest set、readonly、marker syntax/latest、at-or-after0、postmarker0、parse/ADS/cache-pyc/reparse0。

不得重跑PDF/render/visual/N/C/pair/manual/math/semantic，不得改source/PDF/Git/central，不得启动fresh role/第二UID/第二P092角色，不得TeX/build/process management。Main接受R2A前P092保持SA1且不派SA3。P670唯一replacement V2 control reseal V1仍按R434授权等待结果。

Inventory保持`32 SA1 / 35 SA2 / 0 SA3 / 33 local pass`，严格最终0/99，B累计66/66。
