# FIG-P740-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与限域

- canonical UID：`FIG-P740-01`
- legacy/source object：`FIG-V5-C08-04`
- label：`fig:V5-C08-matrix-probability`
- 当前正式图保持单一 `figure`、单一 `tikzpicture` 与上下两层桥接结构，无需拆图。
- 专属 SA2 只改本图源与 V5-C08 首次引用邻域；根线程同步两个 wrapper、
  V5-C08 source JSON、中央 CSV 与本 R3 证据。source JSON 已用
  `legacy_figure_id` 和 `canonical_uid` 建立身份桥；本图无 numeric manifest 记录。

## 数学与语义检查

- 上层以 $X\in\mathbb{R}^{M\times N}$、$W\in\mathbb{R}^{M\times K}$、
  $H\in\mathbb{R}^{K\times N}$ 的共同低秩外形 $X\approx WH$ 为入口；
  第 $n$ 列 $h_n\in\mathbb{R}^{K}$，故 $Wh_n\in\mathbb{R}^{M}$ 与
  $x_n\in\mathbb{R}^{M}$ 维度一致。
- LSA、NMF 与概率因子模型分别由损失、约束、归一化、似然和先验口径区分；
  图内明确说明共同乘积不等于模型语义相同。
- 虚线图例明确为“概率建模分支（非强弱编码）”，没有把线型误作关系强弱。
- 下层有向边为 $W,h_n\to x_n$，与
  $x_n\mid W,h_n\sim\mathcal N(Wh_n,\sigma^2I)$ 的生成方向一致；正文同时限定为
  条件高斯表示，不冒充给全部因子配置先验的完整贝叶斯模型。
- 章节与 page wrapper 均为“首次引用 -> input -> FloatBarrier -> 专属读图检查”；
  题注、图内 alt、source JSON 与正文均使用“下层”方位并保持上述边界。

## 构建与机器门

- `p740_root_r3_standalone.pdf`：53,079 bytes，A4 单页。
- `p740_root_r3_page.pdf`：72,646 bytes，A4 单页；AUX 为图 37.4、页 737。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、
  fatal/no-page、duplicate label、overfull/underfull 与 missing-character 硬命中均为 0。
- standalone 的 6 个字体与 page 的 7 个字体全部 `emb/sub/uni=yes`。
- 两份 FLS 均回指各自 v2.7.0 wrapper 与当前 canonical source；PDF metadata
  均为 v2.7.0。
- 图源普通可见字号为 9.6pt、层标题为 10.2pt、关键公式为 11.8pt；未使用
  整体缩放、`resizebox`、`scalebox`、`transform shape` 或 `scale=`。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；三图均无裁切、
  遮挡、文字碰线、公式溢出或节点越界。
- 上层三方法分支、虚线语义图例、下层有向生成结构、题注与图后读图检查均有清楚留白。
- 灰度下实线/虚线、框形、箭头方向和文本标签仍可独立辨认；颜色不是唯一语义通道。

## 根级结论

当前 P740 源码、正文、wrapper、source JSON、双 PDF、机器证据与三视图均通过
根级局部门。中央 CSV 总体验收更新为 `待独立复核`；须等待独立 SA1 与隔离盲审
SA3 双 PASS 后，根线程才能写最终接受报告并关闭本图。tagged PDF/ActualText
不属于本轮权威硬门；对象级语义替代说明以图源和 source JSON 为证。
