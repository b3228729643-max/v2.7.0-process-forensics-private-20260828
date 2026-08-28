# M10 R98 导航、索引与版本预检

状态：`PASS_PREFLIGHT_NOT_FINAL_RELEASE`

候选沿用 Revision 130 已冻结身份：`src/build/strict_current_r98_fullbook/main_full.pdf`，813 页，4,934,249 bytes，SHA-256 `52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`。本检查只读现有 R98，不重复计算候选哈希、不构建 R99。

## PDF 导航与版本

- 273 个书签；5 个分册书签连续为 1--5；37 个章节书签连续为 1--37。
- `符号索引`、`主题索引` 两个书签均存在。
- 4,939 个命名内部链接，7,418 个命名目标；封面外 812/812 页均有链接；坏书签和坏链接均为 0。
- PDF title、subject、keywords 三个元数据字段均含 `v2.7.0`，没有其他版本号。
- 813/813 页均为未旋转 A4；全书可见版本集合只有 `{v2.7.0}`，出现页为封面物理页 1。
- 机器证据：`navigation_audit.json`，结论 `PASS`。

## 两类索引

- 主题索引：`main_full.idx` 731 条全部接受、0 rejected；`main_full.ind` 719 行、0 warning。
- 符号索引：`symbols.idx` 355 条全部接受、0 rejected；`symbols.ind` 572 行、0 warning。
- 源码顺序为 `\SLPrintContents` 后立即 `\SLPrintSymbolIndex`，正文结束后由 `\printbookindexes` 输出主题索引；公共样式分别定义 `主题索引` 与 `符号索引` 并加入目录。

## 结论边界

该 PASS 只关闭 R98 上的 M10 预检，不是最终发布验收。B、A 依次合入并生成最终候选后，必须在最终 PDF 和独立源码复建 PDF 上重新执行同一审计；正式文件名、最终页数、最终全书扫描及 `FINAL_BOOK_RELEASE_GATE` 仍待完成。
