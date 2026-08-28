# R477 P126 R1A V1静态拒收与V2修订授权

时间：2026-08-28T07:36:27+08:00

## 结论

P126 R1A evidence-only control reseal的V1 controller与auditor不得调用。拒收发生在controller/auditor invocation均为0、目标R1A root Leaf/Container/Any均为false、external stage/result/audit均不存在时，因此未消费唯一封存调用，也未创建目标root或写旧R1 root。

P126 substantive `FAIL_TO_MAIN_SOURCE_SCOPE`与原R1 root的`ROOT_REJECT_NONATOMIC_SEAL_CONTINUATION_AFTER_PREMARKER_FAILURE`均不变。source scope仍未激活。

## Main只读复现实证

- 旧`PREMARKER_MANIFEST.csv`含52行；40行相对路径包含反斜杠。
- 在PowerShell StrictMode Latest下，`Import-Csv`所得`PSCustomObject`执行`Group-Object -Property { $_['RELATIVE_PATH'] }`直接报错：`Unable to index into an object of type System.Management.Automation.PSObject`。V1 controller一处、auditor两处存在同型错误。
- 改用`Group-Object -Property { [string]$_.RELATIVE_PATH }`的只读微测通过，duplicate-groups=0。
- V1 auditor将actual文件路径统一为forward slash，但PAYLOAD_MANIFEST沿用旧manifest反斜杠。对原始52路径与forward-slash规范化路径做`Compare-Object -CaseSensitive`得到80条差异，恰对应40个嵌套路径双向差异。因此修完索引器后仍会在ordinary set门确定失败。

V1冻结身份：controller 26,755 bytes/SHA-256 `F2B02BA913DBBDF7C8F6C5C217BA1BFEFEFD8100273C4CCCEBCCD225F7571E62`；auditor 23,194 bytes/SHA-256 `B275EBDC1716DFE94DE947333D2D2BB91AE8D3DAFA67D01FFC0A1BC1265626DC`。二者保持ReadOnly，不得编辑或调用。

## 唯一授权的V2静态修订

保持以下内容不变：

- HANDOFF_ID=`A-R115-P126-SA2-R168-READONLY-CONTROL-RESEAL-V1-20260828`
- operation=`P126_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- destination root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1A_SA2_R168_READONLY_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`
- copy52 material；加入COPY_IDENTITY与COPY_PROVENANCE后payload54；controls3；ordinary57
- controller invocation1/retry0、separate auditor invocation1/retry0的预算尚未消费

A仅可在root外另物化V2 controller/auditor，不得修改V1：

1. 导入源manifest后立即把每个相对路径规范化为forward slash，并以该canonical值贯穿resolved rows、COPY_IDENTITY、PAYLOAD_MANIFEST与provenance。
2. 所有`Group-Object`键改为显式属性访问；不得对`PSCustomObject`使用字典索引器。
3. controller与auditor的expected/actual set比较必须在双方完成同一canonicalization之后进行。
4. 加入只读静态微测，至少包含一个top-level路径与一个nested反斜杠路径，证明canonical expected与模拟actual的case-sensitive set difference=0；同时保留StrictMode empty/equal/different/duplicate微测。
5. 回传V2 bytes/SHA/ReadOnly/AST errors、Move/delete/retry/TeX/process sites、上述微测结果，以及destination/stage/controller-result/auditor-result全部absent。invocation必须仍为0/0并再次暂停等待Main ACK。

在Main下一次明确ACK前，不得创建R1A、调用controller/auditor、读取或重跑PDF/render/visual/N/C/pair/manual/math/semantic证据、触碰旧R1、激活source scope、编辑业务源、运行TeX/build/Git/process management或启动其他UID/角色。

## 并行状态

C/P683同一fresh SA1实例继续；其current-input-only checkpoint为physical732/printed719/Fig35.2、fresh N24/C276，仅full-page200/300已打开，manual verdict尚未写，blocker=NONE。inventory保持`32 SA1 / 31 SA2 / 0 SA3 / 37 local pass`，严格最终0/99。
