# B-EXM-P02 SA1 预审与复核

- OWNER_DIALOGUE: `B_content`
- objects: `M04-EXM-8.1, 19.1, 26.1, 33.3, 37.2`
- baseline_head: `b2801d2ec38b7d1aabf65bf8374454abf480517c`
- mode: 只读、独立复算、禁止子代理
- final_decision: `PASS`

## 预审边界

五题数学主体基本正确，但均需局部改写：8.1 与 26.1 有工程状态码；19.1 与 33.3 信息密度高且缺独立核验/唯一结论阶段；37.2 缺专属计划与可执行规格。

## R1 复核发现

首次改写后，8.1、19.1、26.1 通过；33.3 与 37.2 有三项定向发现：

1. 37.2 将条件均值代入任意非线性 `h`，错误地推广了 Rao--Blackwell 公式。
2. 37.2 的生成模型遗漏 `varphi_k ~ Dir(beta)`，与随后使用 beta 的塌缩满条件不闭合。
3. 33.3 的答案把缩放变量 `u,v` 的 Beta 混合直接称为 `theta,eta` 的普通 Beta 混合，未说明支持区间缩放。

协调器只修改上述三处。

## R2 关闭证据

- 37.2 已补主题词先验 `varphi_k ~ Dir(beta)`。
- Rao--Blackwell 公式已限定为线性文档主题均值 `E[theta_dk | w]`，不再声称适用于任意 `h`。
- 33.3 已明确 `theta=(1-eta)u`、`eta=(1-theta)v`，两个满条件为缩放 Beta 混合。
- 五题七阶段均各出现一次，恰一个 `SolAnswer`；无 `mathtt` 工程状态码、无独立重复“结论”块、无通用模板命中。
- `python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts`：9 tests，OK。
- `git diff --check`：PASS。
- 最终 findings：0。

SA1 全程未修改或创建工作树文件，未提交，未启动子代理。
