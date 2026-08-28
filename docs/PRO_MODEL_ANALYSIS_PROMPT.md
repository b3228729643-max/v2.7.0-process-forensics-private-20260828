# 给 GitHub 网页端 Pro 模型的建议提示词

请把下面内容作为新对话的第一条消息：

---

你正在审阅一个私有 GitHub 仓库，其中保存了《统计学习方法讲义》v2.7.0 的长期 Codex 执行过程。请不要只总结 README，而要对照仓库中的状态、handoff、controller/auditor 脚本、manifest、manual ledgers、构建报告和文件清单做证据驱动的流程取证。

目标：解释为什么任务耗时异常长，并提出不降低视觉、数学和可追溯质量的优化方案。

请依次完成：

1. 阅读 `README.md`、`docs/WHY_THIS_TOOK_SO_LONG.md`、`docs/OPTIMIZATION_RECOMMENDATIONS.md`、`docs/CURRENT_STATUS_SNAPSHOT.md`。
2. 抽样检查 `analysis_payload/workspace/v2.7.0/_work/state/`、`_work/evidence/main/`、`_work/handoff/` 与 `_work/dialogues/`，验证文档中的判断。
3. 对 controller/auditor 失败做 taxonomy：语法、StrictMode、类型适配、路径、marker、权限、language mode、流程协议。
4. 计算或估计：
   - 重复 control reseal 的时间占比；
   - 全配对 `C(N,2)` 相对增量审查的浪费；
   - TeX cache/PNG/manifest 复制的体积与 I/O 成本；
   - 中央 revision/checkpoint 过密导致的协调成本。
5. 区分“质量所必需的门”和“可以合并、抽样、缓存或自动化的门”。
6. 给出一个新的端到端协议，包括：状态机、artifact schema、公共工具、dry-run、增量影响集、角色独立性、构建锁、seal、Main acceptance。
7. 给出可量化 KPI 和迁移顺序：本周可改、下一版本可改、长期架构。
8. 标注任何与本仓库现有 `AGENTS.md` / GOAL 冲突的建议。

输出格式：

- 执行摘要
- 根因树
- 证据表（路径 + 事实）
- 浪费估算
- 必须保留的质量门
- 可删除/合并/缓存的门
- 新流程图
- 30/60/90 天优化计划
- 风险与回滚方案

不要假设“更多审计总是更安全”；请评价审计本身引入失败和延迟的风险。

---

