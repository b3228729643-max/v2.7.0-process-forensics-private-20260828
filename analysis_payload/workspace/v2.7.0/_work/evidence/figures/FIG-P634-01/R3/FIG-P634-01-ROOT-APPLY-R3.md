# FIG-P634-01 — ROOT APPLY / LOCAL ACCEPTANCE R3

- timestamp: 2026-08-23T01:20:15+08:00
- owner: /root（正式 wrapper、V5-C04 JSON、中央 CSV 与 R3 候选单写者）
- result: **PASS_LOCAL**
- split: **NO**
- independent gate: **PENDING SA1-R3 + SA3-R3**

## 应用范围

根线程完整回读 R2/FIG-P634-01-SA2-R2.md 后，接受中断前已落盘且由专属 SA2 恢复确认的限域候选：

1. src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_coordinate_sweep.tex
2. src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C04.tex 的 FIG-P634-01 相邻块

根线程随后只做单写集成：

- 把图源身份注释和两个 v260_FIG-P634-01_*.tex wrapper 同步为 v2.7.0；
- 依据当前 805 页整书 main_full.aux 将正式身份冻结为图 33.3／印刷页 666，并以整书物理页 679 文本核对该映射；
- 使 page wrapper 精确复现“首次引用→图→短题注→\FloatBarrier→专属读图句→轮内/轮末边界”；
- 同步 V5-C04 figure_sources.json 的 FIG-V5-C04-03 唯一记录和中央 figure_manifest.csv 的 P634 唯一行；
- 本图是概念流程示意，无冻结数值坐标，不新增 numeric manifest 记录。

未修改公共样式、其他图、当前整书 PDF 或最终发布文件；未运行整书 L1。

## A--I 局部门

| 门 | 结果 | 根线程证据 |
|---|---|---|
| A 数学与语义 | PASS | 固定顺序为 $1,2,\ldots,j-1,j,j+1,\ldots,d$；第 $j$ 步左侧与当前格均为同轮新值，右侧为上一轮旧值；公式卡完整给出 $x^{[j]}$。 |
| B 图文一致 | PASS | 首次引用、图内槽位、题注、图后读图句、JSON 与中央 CSV 均只把 $x^{[d]}=x^{(t)}$ 称为轮末样本，不把中间状态误称样本。 |
| C 阅读路径 | PASS | page PDF 文本顺序为首次“图 33.3”索引 382、题注索引 1001、读图句索引 1238、轮内/轮末补充索引 1369。 |
| D 字号与密度 | PASS | 10 处显式字号仅为 9.6/9.8/10.0/10.6pt，源级最小 9.6pt；无 tiny/scriptsize/footnotesize/small，也无 resizebox/scalebox/transform shape/scale=。 |
| E 布局 | PASS | 八个坐标槽位、箭头、三态标签与两张说明卡均在版心内；无穿字、卡片碰撞、裁切、溢出或异常换行。 |
| F 冗余编码 | PASS | 已更新态由斜线纹理与粗框编码，当前态由实框和位置编码，未更新态由点状框编码；文字、序号、框型和线宽使灰度不依赖颜色。 |
| G 题注 | PASS | 题注压缩为固定次序立即写回、新旧值边界与唯一轮末样本三项同一结论，共两行；条件解释留在图后正文。 |
| H 页面融合 | PASS | 300dpi 彩色与灰度整页中，首引、图、题注、导读和轮内/轮末补充构成连续教学单元；页面下方空白来自局部 wrapper 结束，不是生产页回归。 |
| I 技术 | PASS | 两份最终 LuaLaTeX 日志的错误、致命错误、未定义/重复引用、缺字、Overfull 与 Underfull 硬命中均为 0；AUX 唯一给出图 33.3／页 666／figure.caption.1，FLS 对目标 wrapper 与图源各命中 1 次。 |

## 构建、身份与原始证据

- 引擎：TeX Live 2026 LuaHBTeX / LuaLaTeX。
- 首次并行尝试中 standalone 遇到字体缓存竞争；未修改源码，改为串行直接 LuaLaTeX 后成功，最终日志已由成功构建覆盖。
- p634_root_r3_standalone.pdf：A4，1 页，39,022 bytes，v2.7.0。
- p634_root_r3_page.pdf：A4，1 页，69,008 bytes，v2.7.0，页 666／图 33.3。
- 两份 PDF 字体均嵌入并可提取 Unicode；Tagged:no 是公共模板当前能力，不是本图 A--I/B60 的硬门。
- 根线程亲自查看并通过：
  - p634_root_r3_standalone_300dpi.png
  - p634_root_r3_page_300dpi.png
  - p634_root_r3_gray_page_300dpi.png

V5-C04 JSON 可解析，目标 FIG-V5-C04-03 唯一；中央 CSV 可解析为 99 行×19列、99 个 canonical UID 唯一、P634 唯一。P634 当前总体验收保持“待R3独立复审”，resolution 为 PENDING_R3_INDEPENDENT_REVIEW。

## 拆图与下一门

**SPLIT_REQUIRED=NO**。本图只承担“一轮系统扫描中第 $j$ 步的新旧值边界与轮末提交”这一单一教学任务；当前八槽位、两张说明卡与读图句形成一条连续路径，拆图不会增加必要可读性。

根线程局部门结论为 **PASS_LOCAL**，但本报告不替代独立放行。下一步由全新隔离 SA1-R3 与另一全新盲审 SA3-R3 分别从当前候选和 R3 非 Markdown 原始证据独立复核；两者均 PASS 后才签署最终接受。
