# R528 静态拒收与 V2 授权

- 时间：2026-08-28T15:09:04+08:00
- Goal：active Goal 2,812 行已完整读取；SHA-256=`4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`。
- 主线：`v2.7.0/integration`，HEAD=`bd6efc7eaef9fc8fff82919e89934b60c2e2cbcf`，恢复时 clean。
- inventory：`30 SA1 / 30 SA2 / 1 SA3 / 39 local pass`；严格最终0/99；B 66/66。

## P126 R12A V1 裁决

Main全文读取并核对当前冻结脚本：

- controller：18,212 bytes，SHA-256=`44C4E5FB398425F82BA30D145CE4161197D25A9B6A37E8005BC7CBA2159D1A3F`，ReadOnly，invocation0；
- auditor：19,183 bytes，SHA-256=`59D1A62DE49B1D05858F34E72F64B15CC243B51BF3B3F0F1CE6F6560AF88CFEC`，ReadOnly，invocation0；
- destination、stage、controller result、auditor result均不存在。

决定性静态缺口：controller没有在复制前对source full tree、marker前对destination full tree执行真实ADS首错门；auditor仅对ordinary files查询stream，使用`-ErrorAction SilentlyContinue`，既遗漏child directories/root，也可能把stream查询失败吞成0。该实现不满足R527明确要求的files、child dirs、root全覆盖与first-error-stop。

裁决：V1 `STATIC_REJECT_FULL_TREE_ADS_GATE_INCOMPLETE`。两脚本保持当前身份永久冻结，不得编辑、调用或作为后续执行依据。

## 唯一后续授权

仅授权V2 STATIC PREPARATION，不授权执行：

- HANDOFF=`A-R115-P126-SA2-DIRECT-BUILD-R12-CONTROL-RESEAL-V2-20260828`
- operation=`P126_R115_R12_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V2`
- destination仍为startup-absent `STRICT_R12A_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`
- copy137 material、old controls0、added identity/provenance2、payload139、controls3、ordinary142。

V2须保留规范路径、containment、relative/resolved path、bytes、SHA256、Creation/LastWrite FILETIME、全树ReadOnly、root-external future ReadOnly marker sole-final move、old-root before/after0、postmarker0、dynamic CSV/JSON、cache-pyc/reparse门；另必须加入：

1. controller在copy前对source每个file、child directory、root执行`Get-Item -Stream * -Force -ErrorAction Stop`并要求nondefault ADS总数0；
2. controller在marker前对destination同一范围执行同样首错门；
3. auditor独立对source和sealed destination同一范围复算；
4. marker、seal audit、controller result、auditor result绑定file/dir/root ADS counts=0；
5. 用冻结helper在controller file、old R12 root、一个child directory、一个ordinary file上完成StrictMode无写微测。

V2须回报新脚本bytes/SHA/ReadOnly、AST/sites、V1→V2 exact diff、真实helper微测、destination/stage/results absence及invocation0/0，然后暂停等待Main逐文件审查。

## P689

P689保持同一accepted fresh SA3 actual=`/root/sa3_fig_p689_r115_fresh_isolated_v1`继续运行；不得重启、替换、注入旧角色材料或自计local pass。Main仅在收到sealed结果后做独立root、账本、数学语义与视觉验收。
