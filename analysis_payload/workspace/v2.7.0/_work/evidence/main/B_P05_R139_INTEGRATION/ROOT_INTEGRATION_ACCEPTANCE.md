# B-EXM-P05 主线集成验收

- revision: `139`
- source handoff: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\B\B-EXM-P05`
- B commit: `73049af2eac24af285a29b627ad98c085bc7d699`
- B parent: `933fe1d00d9e0661d6a2dce6cc8e3d87b0ab649e`
- main integration commit: `d32aa49`
- main branch: `v2.7.0/integration`
- changed files: `9`
- diff stat: `75 insertions / 96 deletions`
- objects closed: `10 examples`（8.2、9.1、10.1、12.1、12.3、13.3、15.2、17.1、18.1、23.1）
- forbidden-scope changes: `0`
- main working tree after integration: `clean`

## 角色与证据

- fresh post-fix SA1：10/10独立复算PASS，findings 0。
- fresh isolated SA3：`FINAL_DECISION=PASS`，未读取旧R1失败SA3、SA1/state/handoff结论。
- R3唯一Resume：一个latexmk父进程与两遍自然LuaLaTeX子进程，wrapper/child exit0，R4未启动；完成时间以CONTROL的`2026-08-25T05:00:02.9654537+08:00`为准。
- R3 PDF：815页A4、4,948,175 bytes；硬错误、missing/I/O、memory、undefined、overfull、underfull与双索引拒绝/警告均为0。
- 主线独立打开物理页210--212、231--233、337--340、453--455共13页：页338/454异常间距消失，页211/232分页修复无回归，相邻页无裁切、重叠、断框或异常分页。

## 主线局部门

- `git diff --check 05a5f6e..d32aa49`: PASS。
- `python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts`: `Ran 10 tests`, `OK`。
- 主线集成树clean。

## 路由

本批接受为`B_LOCAL_PASS_MAIN_INTEGRATED`，B累计集成41/66道例题；这不等于B长期Goal或全书最终PASS。P05 handoff与证据保持冻结，B可在收到主线确认后进入P06源码/静态阶段，但任何TeX仍须重新申请唯一槽。

官方候选仍为R101。此次不重复全书构建/导航/哈希，因为A侧P608、P654尚处证据重封且没有可集成图源提交；下一共同候选应在新接受输入批次完整后按候选冻结门统一构建。
