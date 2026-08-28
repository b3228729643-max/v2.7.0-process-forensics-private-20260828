# FIG-P634-01 R4 SA2 本地视觉验收

生成时间：2026-08-24 01:56 +08:00

范围：`STRICT_R4_SA2/local_validation.pdf`。这是 SA2 的局部候选，不是官方全书候选，也不替代新全书 PDF 上的独立 SA1。

## 四视图

- `full_page_200dpi.png`：PASS。图体、标准自动题注“图 33.3”、随后引用“图 33.3”均完整；局部验证页无裁切或异常字号跳变。
- `figure_crop_300dpi.png`：PASS。直接由 PDF 以原生 300 dpi 渲染后按原像素裁切，未 resize、插值或膨胀。八个位置、顺序箭头、两张状态卡与两行题注完整。
- `standalone_300dpi.png`：PASS。阅读顺序自左向右；变量均为正文一致的小写 `j/d/t`，没有拉伸、孤立放大或整体缩放。
- `grayscale_300dpi.png`：PASS。已更新的斜线粗框、当前的金色实框、未更新的点框在灰度下仍可由纹理、线型和文字三重区分。

## 字体、数学与题注协调

`FONT_VISUAL_HARMONY_PASS = true`

- 图内普通文字 9.6pt，状态说明 9.8pt，状态公式与公共题注 10.0pt，标题 10.6pt；最小有效基字号 9.6pt。
- `j/d/t`、`x^{[j]}`、`x^{[d]}`、`x^{(t)}` 与正文数学风格一致；没有变量大小写映射或额外解释负担。
- 标准自动题注标签由公共 caption 体系生成：CJK `NotoSansSC-Bold 9.96pt`，数字和分隔句点 `STIXTwoText-Bold 10.06pt`，正文 `NotoSerifSC-ExtraLight 9.96pt`；字号、字重和格式均不突兀。
- 题注编号句点保留为独立可见标点：原生非膨胀 mask 为 `H=6px, W=6px, area=32px`，在 `33.3` 中清楚可辨；它按题注编号分隔标点审核，不误套基准数学运算符 22px 门。

## 间距、纹理与最终可见前景

`OVERLAP_PIXEL_COUNT = 0`

- 状态标题与下一行状态说明保持独立对象；最近一对为 `23px >= 4px`，没有 parent 合并或像素切分。
- 四个已更新节点采用原斜线框加正常不透明白底文字牌。`texture_paint_order_audit.csv` 保留绘制前纹理 mask、真实 PDF 白底 halo mask、最终可见纹理 mask、overlay 与 8 倍近邻视图。
- 7 个同节点文字/公式—最终可见纹理 pair 全部 `overlap=0`，净空依次为 `7,5,8,5,7,7,14.04px`，最小 `5px >= 3px`。跨节点无语义关系的纹理 pair 仅登记为不适用，但仍要求且实测 overlap 为 0。
- 其余最小净空：独立 text-text `23px >= 4px`；text-line/arrow `15px >= 3px`；text-node-border `6px >= 5px`。clip 为 0。

## 语义与页面一致性

`MATH_SEMANTICS_PASS = true`

`TEXT_CONSISTENCY_PASS = true`

`LOCAL_PAGE_INTEGRATION_PASS = true`

- 固定顺序明确为 `1,2,…,j−1,j,j+1,…,d`。
- `x^[j]` 只表示轮内状态；左侧为同轮新值，右侧为上一轮旧值。
- 只有完成第 `d` 步后的 `x^[d]` 与 `x^(t)` 由“双向箭头 + 同一状态”表示等价，再由单向“仅此记录”箭头成为轮末样本。
- 可见题注、同页引用、`.aux` 标签、`.lof` numberline 与 LoF 渲染均为 `33.3`；只有一条 LoF 项，无重复题注或手工编号。

## 结论

本地 SA2 的四视图、灰度、视觉协调与最终可见前景门均 PASS，可交 root 构建新的全书候选并派独立 SA1。这里不声明最终逐图 PASS。
