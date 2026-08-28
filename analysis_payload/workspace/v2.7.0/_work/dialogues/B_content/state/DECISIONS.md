# 持久决策

## D-001

- status: active
- date: 2026-08-24
- decision: Revision 130 的 M02 验收只作为对象定位和历史证据引用；最新 B 任务包下仍建立当前 935 对象表并核对当前源码状态，不重复冻结输入哈希或全书构建。
- reason: 同时满足“旧状态不能直接作新证据”和 lean execution 的增量验证原则。
- affected_scope: 935 阅读阻塞残留及后续 B 状态判定
- affected_files: B 本地对象表、M02 当前核对证据
- supersedes: none

## D-002

- status: active
- date: 2026-08-24
- decision: 首个写批次覆盖任务包明示的六个错套/重复模板例题；协调者首改后才启动 SA1，只允许一个写者进入工作树。
- reason: 这些对象风险明确、局部边界清晰，可形成第一条完整证据链。
- affected_scope: EXM-10.2, EXM-11.1, EXM-12.2, EXM-24.1, EXM-29.1, EXM-33.2
- affected_files: V1-C10.tex, V1-C11.tex, V2-C01.tex, V4-C01.tex, V4-C06.tex, V5-C04.tex
- supersedes: none

## D-003

- status: active
- date: 2026-08-24
- decision: 主线点名的四个内容域失败在章节与合并总册局部源码中修复；不改共享样式、测试、图源或全局单写对象。
- reason: 失败均可由规范术语宏、分布名空格和 V5-C03 局部导航依赖修复，符合 B 专属写域。
- affected_scope: TERM canonicalization, distribution-name spacing, NAV-007
- affected_files: 7 个章节文件及 18 个合并总册局部页包装源码
- supersedes: none
