# FIG-P736-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与限域

- canonical UID：`FIG-P736-01`
- legacy/source object：`FIG-V5-C08-02`
- label：`fig:V5-C08-method-map`
- 当前正式图保持单一 `figure`、单一 `tikzpicture`，由四个方法族、四个计算引擎、
  四条代表性主路线和两条条件性复用线组成，无需拆图。
- 专属 SA2 只改本图源、V5-C08 首次引用邻域及 R2 报告；根线程同步两个
  wrapper、V5-C08 source JSON、中央 CSV 与本 R3 证据。本图无 numeric manifest 记录。

## 关系语义检查

- 四条近似竖直实线分别把降维、话题分析、聚类、图分析连接到 SVD、后验推断、
  EM、幂法；图内与正文只称其为“本讲义中的代表性主路线”，没有宣称宽泛方法族
  对这些引擎存在普遍必要依赖。
- 话题分析到 SVD、EM 的两条短虚线分别标注“如 LSA”“如 PLSA”，只表示特定
  模型/求解方案中的条件性复用；旧绕行长线和分组边框错觉已消除。
- 图例、caption、对象级 alt、source JSON、首次引用和图后读图检查均明确：
  线型只区分关系类型，不编码强弱；两类边均非必要或充分关系；共享引擎不使方法等价。
- 方法族使用圆角框、引擎使用直角框，实线/虚线再由箭头、实例标签与文字图例冗余编码。
- 章节与 page wrapper 均为“首次引用及作用域边界 -> input -> FloatBarrier ->
  P736 专属读图检查”，后续 P737 内容未被并入本图。

## 构建与机器门

- 使用项目已有、不会自动安装宏包的 TeX Live 2026 LuaLaTeX 工具链定向构建。
- `p736_root_r3_page.pdf`：64,993 bytes，A4 单页；AUX 为图 37.2、页 733。
- `p736_root_r3_standalone.pdf`：45,019 bytes，A4 单页。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、
  fatal/no-page、duplicate label、overfull/underfull 与 missing-character 硬命中均为 0。
- page 的 4 个字体与 standalone 的 3 个字体全部 `emb/sub/uni=yes`。
- 两份 FLS 均回指各自 v2.7.0 wrapper 与当前 canonical source；PDF metadata
  均为 v2.7.0。
- 图源普通可见字号为 9.6pt、行标题为 10.2pt；未使用整体缩放、`resizebox`、
  `scalebox`、`transform shape` 或 `scale=`。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；三图均无裁切、遮挡、
  文字碰线、箭头丢失、标签溢出或节点越界。
- 四条主路线近似竖直；两条短虚线从话题分析扇出到相邻 SVD/EM，彼此不交叉，
  “如 LSA/如 PLSA”标签与箭头均有净空。
- 三行图例、题注与图后读图检查均在同一 page 上且换行自然；灰度下圆角/直角框、
  实线/虚线、箭头、标签与文字图例仍可独立辨认，颜色不是唯一语义通道。

## 根级结论

当前 P736 源码、正文、wrapper、source JSON、双 PDF、机器证据与三视图均通过
根级局部门。中央 CSV 总体验收更新为 `待独立复核`；须等待独立 SA1 与隔离盲审
SA3 双 PASS 后，根线程才能写最终接受报告并关闭本图。tagged PDF/ActualText
不属于本轮权威硬门；对象级语义替代说明以图源和 source JSON 为证。
