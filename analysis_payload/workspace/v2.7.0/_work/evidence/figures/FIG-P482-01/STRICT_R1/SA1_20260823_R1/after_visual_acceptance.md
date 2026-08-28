# FIG-P482-01｜STRICT_R1｜SA1 独立严格视觉复核

RESULT: **FAIL**

本轮只读取指定源文件、相邻 V4-C04 正文及冻结输入 `strict_current_r93_fullbook/main_full.pdf`；未读取或沿用旧轮次截图、测量数字或结论，也未修改任何源码、公共样式、构建、inventory 或状态文件。

## 定位与覆盖

- 冻结 PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`；813 页 A4。
- 重新在冻结 PDF 全文检索题注后，唯一命中为 PDF 物理页 **526**（PDF 印刷页 **513**），图号 **图27.1**；这与旧索引中“物理页 575”不一致，故本审查不使用旧页码。
- 图号/题注：`图27.1 二维协方差椭圆与主轴示意`。
- 相邻正文：`V4-C04.tex:315–316` 说明保留最长协方差主轴、把正交剩余变化计入重构误差；与图中的最长轴 $\lambda_1$、短轴 $\lambda_2$、正交投影、$2\sigma/1\sigma$ 标记一致。
- 所有 10 个读者可见语义文字对象、其单字/数学字形、8 个线/曲线对象和 23 个标记对象均由最终 PDF 的 vector bbox + 原生 300dpi raw foreground mask 覆盖。白色半透明标签底板仅作为背景，不被误计为文字—图形前景重叠。

## 9.2.1 硬门结论

| 项 | 结果 | 证据 |
|---|---:|---|
| SOURCE_FONT_PASS | `false` | `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | `true` | `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | `true` | `same_class_ratio_audit.csv` |
| ROLE_RATIO_PASS | `false` | `role_ratio_audit.csv` |
| OVERLAP_PIXEL_COUNT | `435` | `after_overlap_report.csv`, `masks/illegal_overlap_raw.png` |
| CLIP_PIXEL_COUNT | `0` | `after_edge_clip_report.csv` |
| MIN_TEXT_CLEARANCE_PX | `0.000` | `after_overlap_report.csv` |
| VISUAL_HARMONY_PASS | `false` | 四视图 + 比例表 |
| MATH_SEMANTICS_PASS | `true` | 正文/图源/PDF 比对 |
| TEXT_CONSISTENCY_PASS | `true` | 图号、题注、变量和正文比对 |
| GRAYSCALE_PASS | `true` | `after_grayscale_300dpi.png` |
| PAGE_INTEGRATION_PASS | `true` | 整页 200/300dpi 视图 |

## 决定性失败项

1. **源级有效字号未达 9.5pt。** `fig_v4_c04_ellipse.tex:3,48,53,54` 明确使用 9.4pt：`均值 μ`、`2σ`、`1σ`。`figure-style-v2.3.1.tex:40` 的 `slfig direct label` 又覆盖图内 9.4pt picture font 为 `\footnotesize`；在 11pt `ctexbook` 中为 9.0pt。故第一/第二主轴、样本 q、正交投影均为 9.0pt。共有 **7/10** 语义文字对象低于 9.5pt；仅 $x_1/x_2$ 轴标题与 10pt 题注满足基准字号。
2. **同一普通注释角色的源字号协调性失败。** 普通注释混用 9.0pt 和 9.4pt：max/min = 1.0444，绝对差 = 0.40pt，超过同角色 ≤1.03 且 ≤0.25pt 的双门。像素同类和角色比例的实际结果见各独立 CSV；任何其中一个 false 均不得 PASS。
3. **四对真实文本—图形非法原生前景碰撞。** 在 raw 300dpi、阈值 20/255、未膨胀掩膜下：`T02_AXIS1—G04_OUTER_ELLIPSE=164px`、`T05_1SIGMA—M17_SAMPLE=162px`、`T07_PROJECTION—G03_INNER_ELLIPSE=80px`、`T07_PROJECTION—M20_SAMPLE=29px`，合计 **435px**。它们是文字与独立椭圆/样本标记的碰撞，不属于数据几何的意图交点；相应原生最小净空均为 0px。裁切仍为 0，但不能抵消字号、角色比例与碰撞硬性 FAIL。

## 四视图实际检查

- `after_full_page_200dpi.png`：图居页面中段，图前“几何/概率/优化解释”和图后“样本主成分”阅读顺序连续，无异常留白或分页断裂。
- `after_full_page_300dpi.png`：原生 300dpi A4 页，无二次缩放。
- `after_standalone_300dpi.png` / `after_figure_crop_300dpi.png`：逐一检查图内标签、轴、曲线、样本点、投影虚线和直角标记；白底标签正确隔离了线条。
- `after_grayscale_300dpi.png`：椭圆、主轴、虚线投影、样本形状和颜色亮度仍有可区分的线型/形状结构；无单靠颜色才能阅读的结论。

## 输出与下一角色

严格结论为 **FAIL**。本图不得进入 SA3；下一角色应为 **SA2**，只在 `fig_v4_c04_ellipse.tex` 内将所有普通读者文字（包括 `slfig direct label` 的局部覆盖）统一恢复到至少 9.5pt，并在保证轴标题/标签层级范围、零重叠和净空的前提下重新构建冻结候选，再重新走独立 SA1。

测量方法：最终 PDF 直接以 300dpi 渲染且不 resize；前景阈值为相对局部白背景至少 20/255。每一对象使用 PDF/vector bbox 映射后的**未膨胀 raw foreground mask**。曲线/线条使用 PDF 向量路径作定位门，但输出 mask 始终由 raw render 的阈值前景相交得到；因此不会将几何定位缓冲、形态膨胀或绘制顺序污染算成 overlap。
