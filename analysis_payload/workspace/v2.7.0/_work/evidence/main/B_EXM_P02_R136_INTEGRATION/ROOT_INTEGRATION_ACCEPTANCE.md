# B-EXM-P02 主线集成验收

- 验收时间：`2026-08-24T23:28:45+08:00`
- B handoff：`_work/handoff/B/B-EXM-P02/`
- B 原子提交：`907f65346dfca3960bad92fc36203f7242584ef5`
- B 提交父项：`b2801d2ec38b7d1aabf65bf8374454abf480517c`
- 主线集成提交：`a37b2ca`（`v2.7.0/integration`）
- 结论：`PASS_INTEGRATED`

## 提交与写域

- B 工作树在交接提交后干净；主线在集成前后均无未提交业务源码变化。
- `CHANGED_FILES.csv` 与提交实际差异均为 5 个章节文件，内容对象恰为例题 8.1、19.1、26.1、33.3、37.2。
- 差异统计为 60 insertions / 60 deletions；`git diff --check` 通过。
- 五个目标文件在 B-P01 父基线之后未被主线/A 改动，提交无冲突集成。
- 未修改图源、共享宏/样式、测试、manifest、索引、构建入口、A 域或主线状态文件。

## 内容与角色证据

- 五题均具备且仅具备一组完整七阶段：读题、已知、触发、计划、推导、独立核验、唯一答案。
- B SA1 R1 的 3 个定向问题已局部修复；SA1 R2 为 PASS，0 open findings。
- 隔离 SA3 对五题独立复算、结构、视觉和写域给出 PASS，findings `NONE`。
- 主线完整读取 handoff、机械证据、SA1、SA3 与 unresolved/shared requests；外层 wrapper 的 exit 1 仅由 Perl locale warning 被 PowerShell 升格造成，TeX 日志正常结束，不伪记为 clean wrapper exit。

## 主线独立门

- `python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts`
- 结果：9 tests，`OK`，0 skipped/failures/errors。
- 主线打开并逐页检查 B R7 的 10 张 150 dpi 渲染：133、361--362、502--503、692--694、799--800；五个对象及其续页无裁切、重叠、断裂、畸形公式或不可接受分页。
- B R7 终态为 814 页 A4、4,941,530 bytes；最终日志六类硬错误及 over/underfull hbox/vbox 均为 0。

## 候选与后续边界

- 本次内容提交已进入主线，但 P654 正占用 A 侧唯一受控排版时隙，因此主线不并发启动新的全书构建。
- 官方候选继续保持 R99；它不包含本次 P02 内容提交。下一次合法候选构建必须覆盖 `a37b2ca` 及其后的已接受输入，再执行相应全局门。
- `B_LOCAL_PASS` 仅关闭本批 5 道例题。B 内容累计已集成 11/66 道例题；其余内容对象与全书最终验收仍未完成。
- 独立分册入口的 `block/itemize` 键错误登记为主线共享域非阻塞请求，不能由 B 越权修改，也不阻塞本批内容集成。
