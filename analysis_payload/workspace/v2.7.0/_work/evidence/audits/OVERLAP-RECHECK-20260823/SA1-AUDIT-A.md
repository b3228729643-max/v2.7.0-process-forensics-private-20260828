# SA1-AUDIT-A — 已接受图的原生像素/字体层级复查

审计日期：2026-08-23  
审计范围：FIG-P547-01、FIG-P577-01、FIG-P578-01、FIG-P580-01、FIG-P596-01、FIG-P602-01、FIG-P608-01、FIG-P609-01、FIG-P630-01、FIG-P634-01、FIG-P640-01、FIG-P654-01、FIG-P668-01、FIG-P669-01。  
执行约束：只读接受轮次工件、实际图源及用户提供的 P580 截图；未构建、未修复、未改动图源、wrapper、JSON、manifest、状态或既有证据。本报告是唯一正式写入。临时无插值 PNG ROI 位于 D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/audits/OVERLAP-RECHECK-20260823/tmp_A。

## 方法与判据

1. 逐 UID 先读取其 R3 目录的 ROOT-ACCEPTANCE；旧 PASS 仅用于锁定真正的接受 round/jobname，不作为视觉证据。
2. 所列 ROI 均从所列原 PNG 以 1:1 原生像素裁出（无缩放、无插值）；完整 standalone 内容再被 top/middle/bottom 三条带无遗漏地分区实看。所有 PNG 以 original/high detail 读取。P547/P602 原目录的彩色 page PNG 仅为200dpi，因此仅只读地以其 ROOT-ACCEPTANCE 锁定的同一 page PDF/jobname/FLS 用 Poppler 导出300dpi至 tmp_A，文件名含 DERIVED_FROM_ACCEPTED_PDF；未重编译。
3. 几何判据严格采用 STRICT-PIXEL-TYPOGRAPHY-PROTOCOL：独立实墨接触或覆盖为 FAIL；连续纯白净空 1--3px 为 FAIL；只有三类所需 300dpi 证据的相关区均至少 4px 才可 GEOMETRY=PASS。彩色 page 300dpi 缺失时不以局部 crop 替代。
4. 字高是同一基线上的代表 glyph 实墨 bbox 高度，而不是含上下标/分式整体的行高。列出的范围由 standalone 1:1 ROI 中的轴/刻度、普通说明、图例或公式/警示框代表字形取得；同类跨面板只比较同类 glyph。CJK、拉丁和数学字形的 x-height、字重、基线与行距均逐图实看。

## 汇总结论

| UID | 接受 round / artifact jobname | GEOMETRY | TYPOGRAPHY | OVERLAP_RESULT / UID |
|---|---|---:|---:|---:|
| FIG-P547-01 | R3 / root_p547_*_r3 | FAIL | PASS | FAIL |
| FIG-P577-01 | R3.2 / p577_root_r3p2 | FAIL | PASS | FAIL |
| FIG-P578-01 | R3.3 / p578_root_r3p3 | PASS | PASS | PASS |
| FIG-P580-01 | R3.1 / p580_root_r3p1 | FAIL | PASS | FAIL |
| FIG-P596-01 | R3.1 / p596_root_r3p1 | PASS | PASS | PASS |
| FIG-P602-01 | R3 / p602_root_r3 | PASS | PASS | PASS |
| FIG-P608-01 | R3 / p608_root_r3 | FAIL | PASS | FAIL |
| FIG-P609-01 | R3 / p609_root_r3 | PASS | PASS | PASS |
| FIG-P630-01 | R3 / p630_root_r3 | PASS | PASS | PASS |
| FIG-P634-01 | R3 / p634_root_r3 | PASS | PASS | PASS |
| FIG-P640-01 | R3 / p640_root_r3 | FAIL | PASS | FAIL |
| FIG-P654-01 | R3 / p654_root_r3 | PASS | PASS | PASS |
| FIG-P668-01 | R3 / p668_root_r3 | PASS | PASS | PASS |
| FIG-P669-01 | R3 / p669_root_r3 | PASS | PASS | PASS |

## 逐 UID 证据

### FIG-P547-01

原对话 v2.7.0 已完成项：是。accepted_round=R3；实际 artifact jobname=root_p547_*_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_transition_graph.tex。large_operator_present=NO。

三类终稿：

- 彩色 page 300dpi（DERIVED_FROM_ACCEPTED_PDF，只读 Poppler 导出自同轮 D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P547-01/R3/root_p547_page_r3.pdf；FLS 的输入锁定为 V5-C01/fig_v5_c01_transition_graph.tex）：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/audits/OVERLAP-RECHECK-20260823/tmp_A/P547_DERIVED_FROM_ACCEPTED_PDF_page_300dpi.png，2481x3508。
- 原目录彩色 page locator（不作为像素终审）：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P547-01/R3/root_p547_full_page_r3_200dpi.png，1654x2339。
- 灰度整页 300dpi：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P547-01/R3/root_p547_gray_page_r3_300dpi.png，2481x3508。
- standalone 300dpi：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P547-01/R3/root_p547_standalone_r3_300dpi.png，2481x3508。
- 仅作局部交叉核验、不能替代彩色整页：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P547-01/R3/root_p547_figure_crop_r3_300dpi.png，2120x900。

关键 1:1 ROI：派生彩页左弧/标签紧裁 [585,620,230,100]；灰页同区 [585,620,230,100]；standalone 同区 [630,390,230,100]；standalone 全图 [352,283,1811,522]，并分为 [352,283,1811,174]、[352,457,1811,174]、[352,631,1811,174]；彩色 figure crop 全域 [0,0,2120,900]。

几何 FAIL：左图 a12=0.3 标签框的金色下边与表达 1→2 的金色弧线连成同一实墨组件，而非仅是语义箭头与节点的有意相连。派生彩页中框下边实墨 [665,683] RGB(183,121,31) 与弧线实墨 [665,684] RGB(183,121,31) 垂直相邻，连续白隙=0px（同一段 x=665..745 都无白隙）；灰页对应 [665,683] 与 [665,684] RGB(130,130,130)，白隙=0px；standalone 中框边 [711,452] 与弧线 [711,453] RGB(183,121,31)，白隙=0px。三张 1:1 紧裁均可见框边压到弧线。其余节点、概率自环、矩阵和中部转置桥无额外碰撞，但不能抵消此独立“标签框--曲线”覆盖。

源级字体：全局 slfig=9.8pt；局部 title=10.2pt bold、lab=11.6pt、matrix=9.8pt、focus-lab=9.6pt，桥内 P=A^T=12.0pt、关联说明=11.6/11.8pt；无 tiny/scriptsize/footnotesize/small/large 覆盖。实墨代表高度：普通状态/概率字 29--32px（中位 30px）；矩阵/普通说明 30--34px（中位 32px）；桥公式的同类拉丁/CJK glyph 35--38px（中位 37px），可比最大比值 1.23。两面板的同类节点字形、字重和基线一致，较大的桥公式有明确“转置对应”语义且不挤压图形。

GEOMETRY=FAIL。TYPOGRAPHY=PASS。OVERLAP_RESULT=FAIL。

### FIG-P577-01

accepted_round=R3.2；actual artifact jobname=p577_root_r3p2。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_envelope.tex。large_operator_present=YES（min 与积分）。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P577-01/R3/p577_root_r3p2_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P577-01/R3/p577_root_r3p2_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P577-01/R3/p577_root_r3p2_standalone_300dpi.png

关键 1:1 ROI：彩/灰整页内容框均为 [243,145,1947,2513]；standalone 内容框 [327,267,1879,1499]，分区 [327,267,1879,500]、[327,767,1879,499]、[327,1266,1879,500]。非 PASS 紧裁：standalone [1500,900,350,420]；彩/灰 page [1300,1150,400,480]。

几何 FAIL：右侧“普通拒绝（三角点；包络合法）”白底公式框遮入下降的蓝色 p(y) 曲线。standalone 中曲线实墨 [1596,1027] RGB(31,78,121) 与橙色框边实墨 [1597,1027] RGB(183,121,31) 水平相邻，连续白隙=0px；曲线在左边框处进入框所占区域并在底边附近再次出现。彩页同一冲突为蓝线 [1554,1261] RGB(31,78,121) 对橙边 [1555,1261] RGB(183,121,31)，白隙=0px；灰页对应 [1554,1261] RGB(69,69,69) 对 [1555,1261] RGB(130,130,130)，白隙=0px。该框与曲线是独立语义对象，白底遮盖不消除“公式块与图占同一位置”的冲突。上方 min/积分式本身未与边框或图形相撞，但不改变此结论。

源级字体：slfig、tick、axis label 均为 9.6pt；顶部框标题 10.2pt bold；无 every-node 额外缩小或 tiny/scriptsize/footnotesize/small/large 覆盖。实墨高度：刻度 27--31px（中位29px）；普通曲线/区域注释 29--34px（中位31px）；公式/说明框内同类 glyph 29--35px（中位31px）；标题 31--34px（中位32px），可比最大比值 1.10。CJK/数学混排基线和行距协调，字体门不导致本图失败。

GEOMETRY=FAIL。TYPOGRAPHY=PASS。OVERLAP_RESULT=FAIL。

### FIG-P578-01

accepted_round=R3.3；actual artifact jobname=p578_root_r3p3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P578-01/R3/p578_root_r3p3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P578-01/R3/p578_root_r3p3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P578-01/R3/p578_root_r3p3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [292,155,1943,3023]；standalone [477,267,1563,2564]，分区 [477,267,1563,855]、[477,1122,1563,854]、[477,1976,1563,855]。

观察：流程节点、成功/拒绝/预算停止等分支、边词和箭头逐一检查。带文字的边词均有白底，箭头只接触其语义起止节点；不存在箭头穿越字形、标签覆盖分支、相邻面板或边界截断。三类证据中所有可能独立交互区均可确认至少 6px 纯白净空。

源级字体：slfig 与 every node=9.6pt，edgeword=9.6pt；无局部字号缩写或放大命令。实墨高度：普通节点 29--34px（中位31px）；边词 28--33px（中位30px）；公式/状态符号 29--34px（中位31px），最大比值1.13。跨分支的同类状态字形、字重、行距一致。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P580-01

accepted_round=R3.1；actual artifact jobname=p580_root_r3p1。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P580-01/R3/p580_root_r3p1_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P580-01/R3/p580_root_r3p1_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P580-01/R3/p580_root_r3p1_standalone_300dpi.png

用户直接证据：C:/Users/ASUS/AppData/Local/Temp/codex-clipboard-f46bcb2-6b84-4cd9-bdfa-f6685dc6b449.png。该截图只用于定位；以下三张接受终稿均已独立原生复现。

关键 1:1 ROI：彩/灰内容框 [292,154,1944,1657]；standalone [502,283,1527,797]，分区 [502,283,1527,266]、[502,549,1527,265]、[502,814,1527,266]。紧裁的三类证据：standalone 比率卡 [720,350,1000,300]、轴/左溢出 [1250,390,300,180]、右溢出 [1700,390,500,180]；彩/灰比率卡 [1200,650,900,250]。

几何 FAIL：右图比率卡第二行没有容纳公式。standalone 卡边界 x=1366..1919、y=395..518，而第二行的实墨水平包络 x=1274..2012，左、右分别出框约 92px、93px；page/gray 卡边界 x=1373..1923、y=704..828，而该行实墨包络 x=1279..2017，左右均出框约94px。左溢 w(1)=0.96 位于纵轴/0.4 刻度走廊；其最近字墨--纵轴净空为 standalone 5px（[1349,483] 到轴列 x=1354）和 page/gray 4px（[1354,793] 到轴列 x=1358），没有可接受的卡内留白。右溢 w(4)=0.96 穿出右框体。即使把轴的 4--5px 局部物理净空单独看作临界，本公式对象对卡边界的负净空约92--94px 已构成确定的公式块/边界覆盖 FAIL，并与用户截图所示的侵轴可读性问题一致。

源级字体：slfig、tick、label=9.6pt；title=10.2pt；无 tiny/scriptsize/footnotesize/small/large 覆盖。实墨高度：刻度 27--32px（中位29px）；曲线普通说明 29--34px（中位31px）；比率卡公式 glyph 29--36px（中位31px）；标题 31--34px（中位32px），可比最大比值1.10。字体大小、混排、基线和行距本身合格；FAIL 完全来自几何容纳失败。

GEOMETRY=FAIL。TYPOGRAPHY=PASS。OVERLAP_RESULT=FAIL。

### FIG-P596-01

accepted_round=R3.1；actual artifact jobname=p596_root_r3p1。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_dependency_graph.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P596-01/R3/p596_root_r3p1_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P596-01/R3/p596_root_r3p1_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P596-01/R3/p596_root_r3p1_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [292,154,1943,1646]；standalone [396,267,1725,875]，分区 [396,267,1725,292]、[396,559,1725,291]、[396,850,1725,292]。

观察：依赖图的箭头只在语义相关节点边缘收止，文字没有被箭头、连线或边框穿过；所有盒内文字、外围说明与箭头之间均确认至少 6px 白隙，且无裁断。彩/灰/standalone 的关系一致。

源级字体：slfig=9.6pt，every node=9.6pt；无局部字号覆盖。实墨高度：普通节点 29--34px（中位31px）；关系注释 29--33px（中位30px）；公式/强调节点 30--34px（中位31px），最大比值1.13。无无理由的小字/突兀大字，混排协调。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P602-01

原对话 v2.7.0 已完成项：是。accepted_round=R3；actual artifact jobname=p602_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mh_accept_reject.tex。large_operator_present=YES（min）。

三类终稿：

- 彩色 page 300dpi（DERIVED_FROM_ACCEPTED_PDF，只读 Poppler 导出自同轮 D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P602-01/R3/p602_root_r3_page.pdf；FLS 的输入锁定为 V5-C03/fig_v5_c03_mh_accept_reject.tex）：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/audits/OVERLAP-RECHECK-20260823/tmp_A/P602_DERIVED_FROM_ACCEPTED_PDF_page_300dpi.png，2481x3508。
- 原目录彩色 page locator（不作为像素终审）：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P602-01/R3/p602_root_r3_full_page_200dpi.png，1654x2339。
- 灰度整页 300dpi：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P602-01/R3/p602_root_r3_gray_page_300dpi.png，2481x3508。
- standalone 300dpi：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P602-01/R3/p602_root_r3_standalone_300dpi.png，2481x3508。
- 仅作局部交叉核验、不能替代彩色整页：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P602-01/R3/p602_root_r3_figure_caption_guide_crop_300dpi.png，2120x2450。

关键 1:1 ROI：派生彩页全内容框 [244,145,1947,2360]，分区 [244,145,1947,787]、[244,932,1947,787]、[244,1719,1947,786]，并检查公式/判定 [400,900,1650,700]；灰页内容框 [244,145,1947,2360]；standalone [345,267,1579,1471]，分区 [345,267,1579,491]、[345,758,1579,490]、[345,1248,1579,490]；300dpi 图+题注 crop [0,0,2120,2450]。

观察：proposal/accept/reject/self-loop 的箭头只接触关联节点；min 接受率公式在宽框中有充分内边距，菱形、双框和自环标签之间均无碰撞或截断。接受 PDF 的派生彩页、灰页、standalone 及300dpi图+题注 crop 对所有局部交互给出至少4px白隙；彩色派生页的顶部/中部/底部分区和公式/判定紧裁均无独立对象接触。

源级字体：slfig=9.6pt，every node=9.6pt，edge-label=9.6pt；核心接受率公式=11.8pt；无 tiny/scriptsize/footnotesize/small/large 覆盖。实墨高度：普通节点/边词 29--34px（中位31px）；公式块普通 glyph 30--35px（中位32px）；11.8pt 核心公式的可比 glyph 35--38px（中位37px），比值1.19。关键公式有明确层级、不主导画面，CJK/数学基线稳定。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P608-01

原对话 v2.7.0 已完成项：是。accepted_round=R3；actual artifact jobname=p608_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P608-01/R3/p608_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P608-01/R3/p608_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P608-01/R3/p608_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [292,154,1943,1451]；standalone [577,284,1365,803]，分区 [577,284,1365,268]、[577,552,1365,267]、[577,819,1365,268]；预热标注紧裁 [590,390,620,310]。针对复核触发点另从三张原生 PNG 无插值裁出轴--下方面板标题紧裁：彩页 [1350,810,300,120]（tmp_A/P608_page_axis_title_1to1_x1350_y810_w300_h120.png）、灰页同坐标（tmp_A/P608_gray_axis_title_1to1_x1350_y810_w300_h120.png）、standalone [1350,570,300,120]（tmp_A/P608_standalone_axis_title_1to1_x1350_y570_w300_h120.png）；三张均以 original 读取。

几何 FAIL（对原 PASS 的更正）：上面板黑色 x 轴与下面板独立标题“保留样本运行均值 $\overline X_{6:t}$”的 $\overline X$ 横线实墨接触。彩页的轴实线为 y=864--866，而标题横线从 y=867--869 开始；代表点 [1477,866] 与 [1477,867] 均为 RGB(31,35,40)，连续白隙=0px，且接触段横跨 x=1477..1509。灰页同坐标 [1477,866]/[1477,867] 均 RGB(34,34,34)，白隙=0px、同一 x 段接触。standalone 中轴实线 y=628--630 与标题横线 y=631--632 相邻；[1472,630]/[1472,631] 均 RGB(31,35,40)，白隙=0px，接触段 x=1472..1503。三类终稿的 1:1 紧裁均可见轴线与字形横线连成连续实墨；这两个对象没有共同语义，故直接 FAIL。预热段文字仍有半不透明白底和约 1.5pt 内边距，斜线纹理不会穿入字形；点/方形标记仅贴在各自曲线上，边界完整。此前草稿的 PASS 是因只作宽带目视和一般邻域扫描，未将上下两面板交界处的 1px 轴线--overbar 边界单独逐行取样；本次原生像素复核据此撤回该 PASS。

源级字体：slfig/tick=9.6pt；axis label/title=10.8pt；预热、保留、目标值注释=9.6pt；无缩小命令。实墨高度：刻度 27--31px（中位29px）；普通注释 29--34px（中位31px）；轴标签/标题 31--35px（中位33px），可比最大比值1.14。上下两面板同类刻度和注释字重、基线、行距一致。

GEOMETRY=FAIL。TYPOGRAPHY=PASS。OVERLAP_RESULT=FAIL。

### FIG-P609-01

原对话 v2.7.0 已完成项：是。accepted_round=R3；actual artifact jobname=p609_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_autocorrelation_ess.tex。large_operator_present=YES（Σ）。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P609-01/R3/p609_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P609-01/R3/p609_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P609-01/R3/p609_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [244,145,1943,1219]；standalone [384,282,1765,713]，分区 [384,282,1765,238]、[384,520,1765,237]、[384,757,1765,238]；ESS 公式卡 [1300,330,800,500]。

观察：左侧 ACF 柱、截断 K=6 虚线与文字保持清晰分离；右侧 Σ 及上下限位于卡内，和框线/箭头/卡边均有远大于4px的留白。箭头从图到 ESS 卡停在外边界，卡内段落未被穿过；三类证据无裁断。

源级字体：slfig/tick/every node=9.6pt；label=9.8pt；title 与 ESS 卡头=10.4pt bold；卡内正文=9.6pt；caption 的 normalsize 非图内节点。实墨高度：刻度27--31px（中位29px）；普通说明29--34px（中位31px）；Σ/公式 glyph29--37px（中位32px）；卡头32--35px（中位33px），最大可比比值1.17。跨面板同类标签偏差不超过10%，混排协调。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P630-01

原对话 v2.7.0 已完成项：是。accepted_round=R3；actual artifact jobname=p630_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_dependency_graph.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P630-01/R3/p630_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P630-01/R3/p630_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P630-01/R3/p630_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [244,146,1944,1506]；standalone [334,267,1849,895]，分区 [334,267,1849,299]、[334,566,1849,298]、[334,864,1849,298]。

观察：所有水平/竖直流程箭头及两个斜引线都只在它们说明的盒边相接；“正确性条件”和“混合效率”等外部说明框与引线未穿字。盒中文字距离边框、无关连线至少6px；灰页中的层级同样清楚，无裁边。

源级字体：slfig=9.6pt；every node 未另设字号而继承；core=9.6pt、side=9.6pt、boundary=10.0pt bold；无缩小/异常放大命令。实墨高度：核心节点29--34px（中位31px）；侧注29--33px（中位30px）；边界强调30--35px（中位32px），最大比值1.10。10.0pt 仅用于“正确内核”等结论节点，层级有语义理由。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P634-01

accepted_round=R3；actual artifact jobname=p634_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_coordinate_sweep.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P634-01/R3/p634_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P634-01/R3/p634_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P634-01/R3/p634_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [244,146,1944,1645]；standalone [421,283,1658,653]，分区 [421,283,1658,218]、[421,501,1658,217]、[421,718,1658,218]。

观察：更新顺序轴、索引、状态小框、已更新/当前/未更新标签和两条底部公式卡均有明确白隙。x[j] 公式没有被任何框线或箭头切入；状态框内数学符号和相邻框不重合。三类证据的最小独立对象净空均至少5px。

源级字体：slfig/every node=9.6pt；标题=10.6pt bold；索引/状态标签=9.6pt；第一公式卡=10.0pt，第二说明卡=9.8pt；无禁用字号命令。实墨高度：轴索引/刻度29--33px（中位30px）；普通说明29--34px（中位31px）；卡内公式30--36px（中位32px）；标题32--36px（中位34px），最大比值1.17。面板内同类状态字一致，标题层级合理。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P640-01

accepted_round=R3；actual artifact jobname=p640_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_mixing_rho_comparison.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P640-01/R3/p640_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P640-01/R3/p640_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P640-01/R3/p640_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [291,154,1943,1420]；standalone [384,282,1745,797]，分区 [384,282,1745,266]、[384,548,1745,265]、[384,813,1745,266]；右图注释/曲线 [1600,350,500,450]。非 PASS 紧裁：standalone [1850,525,100,100]，page [1850,610,100,100]，gray page [1850,610,100,100]。

几何 FAIL：右图金色渐近 ESS 曲线与独立说明“Neff/N→0”的 N 左下方相贴。standalone 中曲线实墨 [1884,557] RGB(183,121,31) 至说明字墨 [1885,555] RGB(183,121,31) 的欧氏像素距离约2.24px；page 为 [1884,647] 至 [1886,646]，同为 RGB(183,121,31)，约2.24px；gray page 同坐标是 RGB(130,130,130)，约2.24px。紧裁中可见斜曲线贴入 N 的左下字形邻域；抗锯齿也按可见墨迹计，故连续白隙不足4px，三类都不安全。端点标记、(.99,.010) 标签、坐标轴与标题分式另行检查无冲突，但不能抵消该曲线--文字碰撞。

源级字体：tick/title/legend/注释=9.6pt，axis label=9.8pt；every node 未设全局缩小，所有可见 node 的局部 font 为9.6pt；无 tiny/scriptsize/footnotesize/small/large 覆盖。实墨高度：刻度27--31px（中位29px）；轴标签/图例28--33px（中位30px）；右图公式说明28--33px（中位30px）；标题分式同类 glyph30--34px（中位32px），最大比值1.10。字体层级正常；本图失败不是排印比例而是曲线与说明的几何净空。

GEOMETRY=FAIL。TYPOGRAPHY=PASS。OVERLAP_RESULT=FAIL。

### FIG-P654-01

原对话 v2.7.0 已完成项：是。accepted_round=R3；actual artifact jobname=p654_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P654-01/R3/p654_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P654-01/R3/p654_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P654-01/R3/p654_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [292,154,1943,1169]；standalone [313,267,1891,566]，分区 [313,267,1891,189]、[313,456,1891,188]、[313,644,1891,189]；预测公式框 [1500,350,800,430]。

观察：多项/Dirichlet、共轭后验及类别预测箭头都在相关框边结束；预测概率分式与框边有足够留白，虚线“应用”引线未穿入文字。所有独立对象的最小可见净空至少6px，彩/灰/standalone 无截断。

源级字体：slfig/every node=9.6pt；后验与预测公式=11.8pt；应用标签=9.6pt；无缩小命令。实墨高度：普通节点29--34px（中位31px）；应用/关系注释28--33px（中位30px）；关键公式可比 glyph35--38px（中位37px），比值1.23。关键公式有明确计算语义且未挤压框边或图形，混排稳定。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P668-01

accepted_round=R3；actual artifact jobname=p668_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dirichlet_shape_atlas.tex。large_operator_present=YES（Π）。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P668-01/R3/p668_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P668-01/R3/p668_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P668-01/R3/p668_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [291,154,1943,1458]；standalone [417,283,1666,835]，分区 [417,283,1666,279]、[417,562,1666,278]、[417,840,1666,278]；底部总公式/色阶说明 [1200,800,1050,300]。

观察：三角形顶点/边界标签、p→0/p→∞白底标签、众数与“顶点邻域最强”说明框都逐个检查。箭头只从说明框指向其语义顶点；白底内边距保证纹理和等值线不穿字。底部 Π 公式在横框内，色阶和右侧说明与框边/相邻文字的最小独立净空至少4px；三类证据一致，未出现截断。

源级字体：slfig/every node=9.6pt；三面板标题与全域均匀强调=10.1pt bold；其余注释/公式=9.6pt；无 tiny/scriptsize/footnotesize/small/large 覆盖。实墨高度：角点标签27--32px（中位29px）；普通注释29--34px（中位31px）；公式/色阶说明29--36px（中位32px）；标题31--35px（中位33px），最大比值1.17。三面板同类角点/公式样式一致，CJK/数学/拉丁混排协调。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

### FIG-P669-01

accepted_round=R3；actual artifact jobname=p669_root_r3。实际接受源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_concentration_mean.tex。large_operator_present=NO。

三类终稿均为 2481x3508：

- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P669-01/R3/p669_root_r3_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P669-01/R3/p669_root_r3_gray_page_300dpi.png
- D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/evidence/figures/FIG-P669-01/R3/p669_root_r3_standalone_300dpi.png

关键 1:1 ROI：彩/灰内容框 [244,145,1943,1461]；standalone [384,283,1749,847]，分区 [384,283,1749,283]、[384,566,1749,282]、[384,848,1749,282]。

观察：总浓度轴、曲线、标记、单纯形、协方差椭圆、右侧图例、顶部说明框及底部公式框均逐一检查。曲线只在意义相关的均值处收束，椭圆和中心标记未穿入说明字；底部 Var/Cov/Σ 公式在框内且无边界/相邻文本接触。三类证据均确认最小独立对象净空至少5px。

源级字体：slfig/every node=9.6pt；两侧标题=10.1pt bold；其他说明、图例、公式=9.6pt；无缩小/突兀放大命令。实墨高度：轴/刻度28--31px（中位29px）；普通说明29--34px（中位31px）；图例/公式30--35px（中位32px）；标题31--35px（中位33px），最大比值1.17。两侧面板的同类标签尺寸差不超过10%，字重、基线和行距协调。

GEOMETRY=PASS。TYPOGRAPHY=PASS。OVERLAP_RESULT=PASS。

## 覆盖与处置结论

COVERAGE=14/14  
PASS=9；FAIL=5；AMBIGUOUS=0。  
所有非 PASS UID：FIG-P547-01（a12=0.3 标签框下边与金色弧线 0px 接触）、FIG-P577-01（普通拒绝公式框与 p(y) 曲线 0px 接触）、FIG-P580-01（右图比率公式左右出框并侵入纵轴/刻度走廊）、FIG-P608-01（上面板 x 轴与下方面板标题 $\overline X$ 横线在三类证据均0px接触）、FIG-P640-01（右图曲线与 Neff/N→0 说明约2.24px）。

本报告仅报告，不改变中央“通过”状态；后续是否撤回、修复、重建及重新独立终审由根线程单写者处置。
