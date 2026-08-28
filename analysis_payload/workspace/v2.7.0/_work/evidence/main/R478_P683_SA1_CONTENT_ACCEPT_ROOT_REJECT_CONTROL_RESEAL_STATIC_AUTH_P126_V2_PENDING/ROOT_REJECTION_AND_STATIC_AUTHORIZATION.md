# R478 P683 SA1内容接受、原root拒收与control reseal静态授权

时间：2026-08-28T07:42:07+08:00

## Main独立结论

P683 fresh R115 SA1业务/视觉方向接受为`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`，但原root控制分类为`ROOT_REJECT_MANIFEST_SHA_BINDING_MISSING`。P683保持SA1，不计local pass，不授权SA3。

## 内容与视觉复核

- current R115 physical732/printed719/Fig35.2；N24=18 nodes+5 directed draws+complete caption，C276。
- machine/manual pairs均276且ID集合差0；manual objects24、pair required blanks0、views17、glyph156。
- Main实际打开`figure_caption_native_300dpi.png`、`figure_caption_grayscale_300dpi.png`与`roi_phi_diagonal_arrow_nearest8x.png`；plate M/N/K nesting、五条依赖、箭头终点、observed/latent/hyper编码、caption与灰度均无hard反证。
- missing/tofu/wrong-codepoint、clip、illegal visible-ink overlap、unresolved、semantic/math/geometry hard均0。

## 原root控制拒收

原root37 files=35 material+MANIFEST+WRITE_STOPPED；manifest35与FS set/bytes/LastWrite mismatch0，37/37 files与4/4 dirs含root ReadOnly。WSTOP13 physical KEY=VALUE lines，bad/duplicate0，strict latest且at-or-after excluding marker0。

决定性缺口：`MANIFEST.csv` header严格只有`RelativePath,Bytes,LastWriteUtc`，没有逐payload SHA256；`WRITE_STOPPED`也没有`MANIFEST_SHA256`键。故最终控制未绑定35份payload内容，也未绑定manifest自身身份。原root永久ReadOnly/零写，不得原地修改、retimestamp或reseal。

原manifest文件SHA-256=`0A96A24F0ED097B6C1B2CBCE2B14860980A95A910E53C9A0FAEF14CCE3792521`；原WSTOP SHA-256=`2E15CF2BA14232CCCD1A91CC1A88664122EFCA46B4FCB6CE6C544CBD7A861C55`。

## 唯一sibling evidence-only control reseal静态授权

- HANDOFF_ID=`C-FIG-P683-01-R115-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1`
- operation=`P683_R115_SA1_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- destination=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa1_r115_fresh_isolated_v1_control_reseal_v1`
- Main immediate gate：Leaf=false、Container=false、Any=false、Parent=true。
- 仅读原MANIFEST绑定35 material；旧MANIFEST/WSTOP复制0。
- COPY_IDENTITY与resolved COPY_PROVENANCE作为新增payload，故payload37。
- controls恰`PAYLOAD_MANIFEST.csv`、`SEAL_AUDIT.json`、`WRITE_STOPPED`三项；ordinary40。

C当前仅可物化root-external controller与separate auditor。要求PowerShell7 AST0、StrictMode empty-safe微测、delete/destructive0、retry-loop0、TeX/process-management0；controller唯一Move-Item必须是root-external预制、已ReadOnly、future-FILETIME、语法逐行严格通过的WSTOP最终入根。controller/auditor必须独立验证source→destination relative path/bytes/SHA/Creation+LastWrite FILETIME、payload manifest path/bytes/SHA/ticks、全files/dirs/root ReadOnly、marker严格晚于files/dirs/root且at-or-after0、postmarker0、CSV/JSON/ADS/cache-pyc/reparse0、old root before/after0差。

回静态脚本bytes/SHA/ReadOnly/AST/sites与new-root/stage/results absence后暂停；controller/auditor invocation必须0/0。在Main明确ACK前不得创建destination、调用脚本、重跑PDF/render/visual/N/C/pair/manual/math/semantic、读其他旧UID、启动SA3、TeX/source/Git/central/process/第二UID-role。

## 并行边界

A/P126仅继续R477所授权的R1A V2静态脚本修订，仍不得调用或激活source scope。inventory保持`32 SA1 / 31 SA2 / 0 SA3 / 37 local pass`，严格最终0/99。
