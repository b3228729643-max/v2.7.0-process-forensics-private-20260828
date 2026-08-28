# SA-ORIGINAL-D — 原对话 v2.7.0 已完成图的附加独立像素/字体专审

审计员：D。审计日期：2026-08-23。  
审计范围：原 Codex 对话 <code>v2.7.0</code> 中已完成并被接受的 FIG-P630-01、FIG-P654-01、FIG-P715-01。  
执行协议：已在本轮开始时完整读取 <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md</code>。ROOT-ACCEPTANCE 的既有 PASS 只用于定位接受 round/jobname；本报告没有把它当作视觉或字体结论。

## 方法、独立性与口径

- 对每个 UID 先读取其 ROOT-ACCEPTANCE，再只打开该接受轮次/job set 的最终彩色 page、gray page、standalone/正式 figure crop。三图的图源也在本轮重新读取。
- 所列 PNG 先以 original/high detail 查看，再以原生像素查看本轮生成的 1:1 raw ROI；ROI 用直接像素裁剪，无缩放、无插值。临时文件唯一位于 <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\tmp_original_D</code>。
- 审查的交互区包括每一条箭头/引线、箭头头部、框线、文字/数学字形、公式上下限、矩阵格线、题头、图例式标签和相邻面板。抗锯齿像素按可见实墨处理。
- glyph ink bbox 高度在 300 dpi 原图的 raw ROI 取样；CJK、Latin、数学字符按其同类/同脚本比较，并检查 x-height、字重、基线和行距。没有坐标轴或图例的图将该类别明确标为 N/A，而以实际存在的卡片标签/警示/公式替代测量。
- 本审计没有构建、修复或改变图源、wrapper、manifest、状态或既有证据；除本报告和上述诊断裁剪外无持久写入。

## 汇总

| UID | accepted round / jobname | GEOMETRY | TYPOGRAPHY | UID_RESULT |
|---|---|---:|---:|---:|
| FIG-P630-01 | R3 / p630_root_r3 | PASS | PASS | PASS |
| FIG-P654-01 | R3 / p654_root_r3 | PASS | PASS | PASS |
| FIG-P715-01 | R3 / current evidence set | PASS | FAIL | FAIL |

## FIG-P630-01

- accepted_round=R3；accepted_jobname=<code>p630_root_r3_page</code> / <code>p630_root_r3_standalone</code>。接受图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_dependency_graph.tex</code>。
- 实检最终证据（均为 native 2481×3508、299.9994 dpi，即 300 dpi）：
  1. 彩色 page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P630-01\R3\p630_root_r3_page_300dpi.png</code>。
  2. gray page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P630-01\R3\p630_root_r3_gray_page_300dpi.png</code>。
  3. standalone：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P630-01\R3\p630_root_r3_standalone_300dpi.png</code>。
- 原生 1:1 ROI：彩色 <code>tmp_original_D\D_FIG-P630-01_page_raw_x240_y350_w2000_h1500.png</code>，[240,350,2000,1500]；gray <code>tmp_original_D\D_FIG-P630-01_gray_raw_x240_y350_w2000_h1500.png</code>，[240,350,2000,1500]；standalone <code>tmp_original_D\D_FIG-P630-01_standalone_raw_x200_y100_w2080_h1800.png</code>，[200,100,2080,1800]。每个 ROI 覆盖六节点主链、两张侧卡、两条引线、底部警示框及其相邻文字。
- 几何观察：large_operator_present=NO。五条主箭头只停在目标框边；两条 leader 与其语义目标框的端点连接是有意连接，未穿入任何字形。逐项检查节点正文、<code>\pi_j</code>/<code>K_j</code>、侧卡、MCSE/ESS、底部“正确内核≠快速混合”、箭头和框线，未发现独立对象实墨接触、1–3 px 净空或裁切。最近的无关文字/线或文字/框线白隙约 16 px；三个最终证据一致。
- 静态字体：全局图样式 9.6/11.6 pt；<code>every node</code> 只设 align，继承全局；core 9.6/11.8 pt；side 9.6/11.6 pt；boundary 10.0/12.0 pt 粗体。扫描未命中 <code>tiny/scriptsize/footnotesize/small/large</code>、<code>scale=</code>、<code>transform shape</code> 或整体缩放。
- 300 dpi 实墨测量：普通 core/side CJK、Latin 标签 33–36 px（中位 35）；数学基线字符 <code>\pi,K,x</code> 32–36 px（中位 34）；底部语义警示粗体 38–40 px（中位 39）。无轴/刻度、无图例，均为 N/A。六个 core 与两张 side 的同类 CJK 最大高度比 36/34=1.06；警示 39/35=1.11，具有明确总结层级且未挤压空间。CJK/Latin/数学的基线同齐，字重和行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

## FIG-P654-01

- accepted_round=R3；accepted_jobname=<code>p654_root_r3_page</code> / <code>p654_root_r3_standalone</code>。接受图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex</code>。
- 实检最终证据（均为 native 2481×3508、299.9994 dpi，即 300 dpi）：
  1. 彩色 page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P654-01\R3\p654_root_r3_page_300dpi.png</code>。
  2. gray page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P654-01\R3\p654_root_r3_gray_page_300dpi.png</code>。
  3. standalone：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P654-01\R3\p654_root_r3_standalone_300dpi.png</code>。
- 原生 1:1 ROI：彩色 <code>tmp_original_D\D_FIG-P654-01_page_raw_x180_y350_w2130_h1400.png</code>，[180,350,2130,1400]；gray <code>tmp_original_D\D_FIG-P654-01_gray_raw_x180_y350_w2130_h1400.png</code>，[180,350,2130,1400]；standalone <code>tmp_original_D\D_FIG-P654-01_standalone_raw_x180_y100_w2130_h1650.png</code>，[180,100,2130,1650]。覆盖两条输入、主链、11.8 pt 后验/预测公式、两条无箭头解释线、虚线应用出口及下方对象。
- 几何观察：large_operator_present=NO。所有四条实线主箭头、两条无箭头解释线和一条虚线应用箭头均终止于相应框边；没有线穿入文字。后验 <code>Dir(\alpha+\boldsymbol n)</code> 与预测分式、分数横线、括号、上下标和框线均分离；分式没有贴到边框，解释线未贴到下方标签。最近无关实墨之间的可见连续白隙约 18 px（公式/框或解释线/标签邻域）；彩色、gray、standalone 一致，未发现 1–3 px、接触或边界截断。
- 静态字体：全局与 every node 为 9.6/11.5 pt；posterior/predictive 中的关键公式为 11.8/14.2 pt；虚线出口“应用” 9.6/11.5 pt。无 <code>tiny/scriptsize/footnotesize/small/large</code>、<code>scale=</code>、<code>transform shape</code>、<code>resizebox</code> 或 <code>scalebox</code> 命中。
- 300 dpi 实墨测量：普通 CJK/Latin 卡片/解释标签 34–36 px（中位 35）；“应用”标签 34–35 px（中位 35）；关键公式的基线字符、Greek/Latin/数字 42–44 px（中位 43）。无坐标轴/刻度、无独立图例，均为 N/A。两侧输入和下方解释卡的同类最大比 36/34=1.06；公式比为 43/35=1.23，低于 1.35，且是后验/预测的唯一明确语义层级，不主导或挤压图形。CJK、Latin 与数学的 x-height/字重、基线及行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

## FIG-P715-01

- accepted_round=R3；accepted_jobname=<code>current evidence set</code>。接受图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex</code>。
- 本轮重新锁定并实检的最终 evidence：
  1. 接受目录内的彩色 page 预览：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P715-01\R3\current_full_page_200dpi.png</code>，native 1654×2339、199.9996 dpi。
  2. **DERIVED_FROM_ACCEPTED_PDF** 的最终彩色 page 300 dpi：只读从同一 R3 job 的 <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P715-01\R3\v260_FIG-P715-01_page.pdf</code> 用 Poppler <code>pdftoppm -r 300</code> 导出到 <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\tmp_original_D\D_FIG-P715-01_page_DERIVED_FROM_ACCEPTED_PDF_300dpi-1.png</code>；native 2481×3508、299.9994 dpi。其同一 job 身份由 <code>v260_FIG-P715-01_page.fls</code> 锁定：该 FLS 记录此 PDF 输出并输入 <code>web_random_walk.tex</code>。
  3. gray page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P715-01\R3\current_gray_page_300dpi.png</code>，native 2481×3508、299.9994 dpi。
  4. 正式 figure crop：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P715-01\R3\current_figure_crop_300dpi.png</code>，native 1810×875、299.9994 dpi。
- 原生 1:1 ROI：DERIVED_FROM_ACCEPTED_PDF 彩色 page <code>tmp_original_D\D_FIG-P715-01_page_DERIVED_raw_x200_y350_w2100_h1850.png</code>，[200,350,2100,1850]；gray <code>tmp_original_D\D_FIG-P715-01_gray_raw_x200_y350_w2100_h1850.png</code>，[200,350,2100,1850]；正式 crop <code>tmp_original_D\D_FIG-P715-01_figurecrop_raw_x0_y0_w1810_h875.png</code>，[0,0,1810,875]。200 dpi 预览也重新查看（<code>tmp_original_D\D_FIG-P715-01_page200_raw_x80_y300_w1490_h1200.png</code>，[80,300,1490,1200]），但不作为 300 dpi 门的替代。三个 300 dpi 审核 ROI 均覆盖网页图、箭头、<code>\sum</code>、A/M/P 矩阵、数学行、标题和两个 panel 边界。
- 几何观察：large_operator_present=YES（<code>c_j=\sum_rA_{rj}</code>）。在 DERIVED_FROM_ACCEPTED_PDF 彩色 300 dpi、gray 300 dpi 和正式 crop 300 dpi 中，Σ/下标、行内公式、矩阵格线、橙色选格框、箭头头部、节点圆、标题和 panel 边框均未见独立实墨接触；最小可见无关对象净空约 12 px。三类 300 dpi 证据一致，均大于等于 4 px；无接触坐标、无 1–3 px 邻域、无抗锯齿归属不确定或边界截断。
- 静态字体：全局图样式和 every node 均为 **9.5/11.5 pt**；title 10.4/12.4 pt 粗体；page/cell 10.2/12.2 pt；edge note/note 9.5/11.5 pt；formula 12/14 pt。无 <code>tiny/scriptsize/footnotesize/small/large</code>、<code>scale=</code>、<code>transform shape</code> 或整体缩放命中。普通可见节点、edge note 与 note 的 9.5 pt 低于协议的 9.6 pt 硬下限。
- 300 dpi 实墨测量（gray/crop）：普通 note/edge note 34–35 px（中位 35）；page/cell 字符 38–40 px（中位 39）；formula 的数学基线字形 42–44 px（中位 43），Σ 轮廓约 48 px，属大运算符自身构形。无坐标轴/刻度/图例。可用的两个 300 dpi 证据中同类最大比 1.06；CJK/Latin/数学的基线、字重、行距本身协调。但这些像素测量不能豁免实际图源已明示的 9.5 pt 下限违反。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=FAIL（9.5 pt < 9.6 pt）；UID_RESULT=FAIL。

## 最终计数

- COVERAGE=3/3
- UID_RESULT：PASS=2；FAIL=1；AMBIGUOUS=0。
- GEOMETRY：PASS=3；FAIL=0；AMBIGUOUS=0。
- TYPOGRAPHY：PASS=2；FAIL=1；AMBIGUOUS=0。
- 非 PASS UID：FIG-P715-01（仅 TYPOGRAPHY=FAIL：9.5 pt < 9.6 pt）。其几何 PASS 来自同一接受 PDF/job/FLS 的只读 DERIVED_FROM_ACCEPTED_PDF 300 dpi 彩页，而非 TeX 重建或旧结论补证。
