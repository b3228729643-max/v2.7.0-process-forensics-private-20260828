# FIG-P482-01 STRICT_R1 SA1 正式报告

## 结论

**RESULT: FAIL**

FIGURE_ID: FIG-P482-01  
冻结 PDF 物理页: 526  
PDF 印刷页: 513  
图号: 图27.1  
证据目录: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P482-01\STRICT_R1\SA1_20260823_R1`

## 覆盖

- 读源：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第04册_无监督学习与矩阵分解\V4-C04\fig_v4_c04_ellipse.tex`（完整 73 行）、相邻正文 `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第04册_无监督学习与矩阵分解\chapters\V4-C04.tex:299–335`、相关局部样式 `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\styles\figure-style-v2.3.1.tex:40,92`、图注设定 `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty:305`。
- 定位：独立扫描冻结 PDF 813 页的题注文本，命中第 526 页；旧索引的 575 不能作为本轮取证页面。
- 原生渲染：整页 200dpi、整页 300dpi、裁图/standalone 300dpi、灰度 300dpi 均已保存。300dpi 图片没有 resize。
- 文字：10 个语义对象、所有单字/数字/希腊字形/上下标均有 PDF bbox、raw foreground mask 和像素高度记录。
- 图形：8 个线/曲线与 23 个标记对象均有 vector bbox、raw separated mask；所有对象成对列表已写入 overlap CSV。

## 失败汇总

- 源字号失败对象数: 7 / 10
- 像素高度失败字形数: 0 / 47
- 具有独立文字碰撞/净空失败的字形数: 12 / 47
- 同类比例失败条目数: 0 / 10
- 角色比例失败条目数: 2 / 3
- 必查文本关系失败对数: 4
- 非法 overlap 像素: 435
- clip 像素: 0
- 最小文字关系净空: 0.000px

四对必查且真实的文本—图形碰撞为：`T02_AXIS1—G04_OUTER_ELLIPSE=164px`、`T05_1SIGMA—M17_SAMPLE=162px`、`T07_PROJECTION—G03_INNER_ELLIPSE=80px`、`T07_PROJECTION—M20_SAMPLE=29px`；总计 435px。每一对都有 `critical_pairs/` 的原生 300dpi 掩膜叠加证据。其余图形—图形交点（样本点/轴/椭圆）被明确标为意图几何，未混入文本碰撞总数。

## 数学、文本和版面复核

1. 均值点 $(0.3,-0.1)$ 位于协方差椭圆中心；长轴和短轴按源注释的 $\lambda_1=2.25>\lambda_2=.36$ 的方向和长度关系绘制。
2. 查询三角形与方形投影点之间的红色虚线同最长主轴垂直，直角标记位于投影点附近；与正文“保留最长主轴、把正交剩余变化计入重构误差”一致。
3. 图内 $\mu,\lambda_1,\lambda_2,1\sigma,2\sigma,q$ 与题注/正文没有符号漂移；题注简洁且为单一读图结论。
4. 视觉上主轴、两层椭圆、样本散点、投影虚线和正交符号具有可辨认层级；灰度下仍可依靠实线/虚线/标记形状识别。

## 可执行 SA2 修复动作

仅修改指定图源：

1. 将 picture-local node font 从 9.4pt 提升为至少 9.5pt（建议统一 10pt）。
2. 在本图局部覆写 `slfig direct label` 的 `font=\fontsize{10pt}{12pt}\selectfont`，不要依赖公共 `\footnotesize` 默认值。
3. 保留 $x_1/x_2$ 的 10pt 基准与自然 subscript；重建后以原生 300dpi 逐一重测所有文本和重新审查同类/角色比例、overlap 与净空。
4. 不要通过 resizebox、scalebox、整体缩图或减小画布处理该失败。

下一角色: **SA2**。仅当新候选的所有布尔项 true、overlap=0、clip=0、所有净空和字号门通过，才可重新启动新的独立 SA1；当前候选不得建议 SA3。
