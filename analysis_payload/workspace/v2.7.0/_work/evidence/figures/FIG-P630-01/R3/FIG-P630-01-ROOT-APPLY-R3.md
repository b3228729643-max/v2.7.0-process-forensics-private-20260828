# FIG-P630-01 — ROOT APPLY / LOCAL ACCEPTANCE R3

- timestamp: \`2026-08-22T23:57:08+08:00\`
- owner: \`/root\`（正式 wrapper、JSON、中央 CSV 与 R3 候选单写者）
- result: **PASS_LOCAL**
- split: **NO**
- independent gate: **PENDING SA1-R3 + SA3-R3**

## 应用范围

根线程完整回读 \`R2/FIG-P630-01-SA2-R2.md\` 后，接受专属 SA2 对以下两处生产源码的限域修订：

1. \`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_dependency_graph.tex\`
2. \`src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C04.tex\` 的 FIG-P630-01 相邻块。

根线程随后只做单写集成：

- 把图源身份注释和两个 \`v260_FIG-P630-01_*.tex\` wrapper 同步为 v2.7.0；
- 以当前 805 页整书 \`main_full.aux\` 冻结正式身份为图 33.1／印刷页 662，并由整书物理页 675 单页文本复核该映射；
- 使 page wrapper 精确复现“首次引用→图→短题注→\`\FloatBarrier\`→专属读图句”；
- 同步 V5-C04 \`figure_sources.json\` 的目标唯一记录和中央 \`figure_manifest.csv\` 的 P630 唯一行；
- 本图是概念依赖图，无冻结绘图坐标，numeric manifest 中 \`FIG-V5-C04-01\` 记录数保持 0。

未修改公共样式、其他图、旧整书 PDF 或最终构建；未运行整书 L1。

## A--I 局部门

| 门 | 结果 | 根线程证据 |
|---|---|---|
| A 数学与语义 | PASS | 图中“给定 \(x_{-j}\) 的满条件→只更新 \(x_j\) 的 \(K_j\)→扫描核→相关样本→诊断”与正文 \(K_j(x,dy)=\Pi_j(dy_j\mid x_{-j})\delta_{x_{-j}}(dy_{-j})\) 一致；侧卡不冒充自动推论。 |
| B 图文一致 | PASS | 正文首次引用、图内六节点、短题注、读图句、figure_sources 和中央 CSV 使用同一对象—关系—结论；已删除图中不存在的 LDA 出口。 |
| C 阅读路径 | PASS | page PDF 的 \`pdftotext -layout\` 中首次“图 33.1”索引 77、题注首个 MCSE 索引 432、读图句索引 748，顺序正确。 |
| D 字号与密度 | PASS | 根样式与核心节点/侧卡为 9.6pt，底部护栏 10.0pt；\`resizebox/scalebox/adjustbox/transform shape/scale=\` 命中为 0。 |
| E 布局 | PASS | 六节点蛇形主链、两侧卡和护栏均在版心内；五个箭头停边，无交叉、重叠、穿字、裁切、越界或异常换行。 |
| F 冗余编码 | PASS | 主链为五条深色独立有向边；两侧卡仅用浅色无箭头 leader；框体、线型、箭头和直接文字共同编码，灰度不依赖颜色。 |
| G 题注 | PASS | 题注压缩为“满条件把联合目标转为单坐标更新，扫描后得到需以MCSE、ESS与轨迹诊断的相关样本”这一条结论；条件边界留在正文。 |
| H 页面融合 | PASS | 彩色 200/300dpi page 中首引、图、题注和导读形成连续教学单元；局部 page 后续空白来自 wrapper 到此结束，不作为生产页留白回归。 |
| I 技术 | PASS | 两份 LuaLaTeX 日志的错误、致命错误、未定义/重复引用、缺字、Overfull 与 Underfull 硬命中均为 0；AUX 唯一给出图 33.1／页 662／\`figure.caption.1\`，FLS 命中正确 wrapper 和图源各 1 次。 |

## 五条独立有向边

源码中 \`\draw[flow]\` 精确为 5，端点依次为：

1. \`joint.east -> cond.west\`
2. \`cond.east -> coord.west\`
3. \`coord.south -> scan.north\`
4. \`scan.west -> sample.east\`
5. \`sample.west -> diag.east\`

\`\draw[leader]\` 精确为 2，均无箭头，只连接“正确性条件”与“混合效率”侧卡。该修复消除了 R1 中“单一 TikZ path 只有末段箭头”的硬错误。

## 构建、身份与原始证据

- 引擎：TeX Live 2026 LuaHBTeX / LuaLaTeX。
- 缓存：\`C:/Users/ASUS/AppData/Local/Temp/statlearn-v2.7.0-texmf-cache\`。
- \`p630_root_r3_standalone.pdf\`：A4，1 页，43,428 bytes，v2.7.0。
- \`p630_root_r3_page.pdf\`：A4，1 页，65,921 bytes，v2.7.0，页 662／图 33.1。
- 两份 PDF 字体正常嵌入；\`Tagged: no\` 是公共模板当前能力，权威 A--I/B58 未把局部 PDF tagging 规定为本图硬门。
- 根线程亲自查看并通过：
  - \`p630_root_r3_standalone_300dpi.png\`
  - \`p630_root_r3_full_page_200dpi.png\`
  - \`p630_root_r3_page_300dpi.png\`
  - \`p630_root_r3_gray_page_300dpi.png\`

V5-C04 JSON 可解析，目标 \`FIG-V5-C04-01\` 唯一；中央 CSV 可解析为 99 行×19列、99 个 canonical UID 唯一、P630 唯一。P630 当前总体验收保持 \`待R3独立复审\`，resolution 保持 \`PENDING_R3_INDEPENDENT_REVIEW\`。

## 拆图与下一门

**SPLIT_REQUIRED=NO**。六个主节点共享一个从联合目标到诊断的单一依赖链；两张侧卡只是约束，不构成第二教学对象。当前密度、方向和灰度均清楚，拆成两个正式图不会增加必要可读性。

根线程局部门结论为 **PASS_LOCAL**，但本报告不替代独立放行。下一步由全新隔离 SA1-R3 与另一全新盲审 SA3-R3 分别从当前原始对象和 R3 非 Markdown 原始证据独立复核；两者均 PASS 后才签署最终接受。
