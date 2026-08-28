# B-EXM-P06 主线集成验收（Revision 141）

- B sealed commit：`bc713ff1505a84b8fd72f2a56a6386bc4dd84a50`；parent：`73049af2eac24af285a29b627ad98c085bc7d699`。
- 主线集成提交：`eea4060c5229168e2b973bbaea81cf391e7a9dfd`；parent：`d32aa49fd44662fbe33d31c021997ca4e9024058`。
- 精确写域：7 个授权章节文件，61 insertions / 55 deletions；未触碰共享宏、构建入口、索引或权威状态。
- 最终接受的构建身份仅为 `B-EXM-P06-R2-RESUME`：816 页 A4、4,953,900 bytes，log 249,751 bytes，wrapper/child exit 0；硬错误、undefined、duplicate、rerun、overfull、underfull 均为 0，双索引 731/355 accepted、0 rejected/warnings。
- R1 的 817 页身份与 37 页视觉抽检只保留为失败历史；fresh isolated SA3 发现物理页 557 孤立节标题后，R1 不属于最终接受输入。
- R2 只移动 V4-C05 中既有 `\Needspace{6\baselineskip}` 到同一节标题之前；最终 38 页视觉覆盖全部 PASS，物理页 557 已同时容纳节标题与例 28.1 开头。
- fresh post-fix SA1：10/10 数学复算 PASS、0 findings；另一全新 isolated SA3：`FINAL_DECISION=PASS`、findings=[]。
- 主线增量复核：`src.tests.test_style_term_solution_contracts` 与 `src.tests.test_layout_source_contracts` 共 10 tests OK；P06 checker 为 10 targets、70/70 stages、10/10 labels/headings、environment stacks balanced、forbidden scope 0；`git diff --check HEAD^ HEAD` PASS；主线工作树 clean。
- B 累计已集成 51/66 道例题；P01--P06 冻结。此结论仅为 P06 局部批次通过，不是全书最终 PASS。
- 官方候选仍为 R101；本次未重建、未重算其哈希、导航或既有视觉门。

结论：`B_EXM_P06_ROOT_ACCEPTED_AND_INTEGRATED`。
