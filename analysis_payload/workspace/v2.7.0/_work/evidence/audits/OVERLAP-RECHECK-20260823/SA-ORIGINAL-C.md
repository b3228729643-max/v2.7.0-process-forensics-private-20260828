# SA-ORIGINAL-C：v2.7.0 原对话已完成项的独立原生像素与字体审查

审查日期：2026-08-23  
审查范围：原对话已完成的 4/4 图，FIG-P547-01、FIG-P602-01、FIG-P608-01、FIG-P609-01。  
约束：仅按各 UID 的 ROOT-ACCEPTANCE 锁定 R3；旧报告的 PASS 未作为本轮结论依据。

## 方法与证据锁定

- 每个 UID 先读取对应 R3 ROOT-ACCEPTANCE，确认接受轮次、page jobname、standalone jobname 和实际图源；未使用 R1/R2 的 PNG。
- 逐图在最终彩色 page、gray page、standalone（以及存在的正式 figure crop）上读取 300 dpi 原始像素。P547/P602 没有现成的 R3 彩色 300 dpi page PNG，故直接由其已接受的 R3 page PDF 以 300 dpi 无缩放、无插值光栅化到本审查专属临时目录；这不是重建或改写候选。
- 这里的 ROI 坐标均为所列原始图的 [x,y,width,height]，裁剪使用原生像素 Clone，没有缩放或插值。抗锯齿边缘按可见墨迹处理。
- 对流程图中箭头到其定义节点边框的端点连接，按有意连接处理；注释/公式/标题与独立箭头、曲线、坐标轴的接触不享有该例外。

## FIG-P547-01

接受锁定：R3；page jobname=root_p547_page_r3；standalone jobname=root_p547_standalone_r3。  
实际图源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_transition_graph.tex。

证据与原生尺寸：

| 类型 | R3 文件 | native dimensions |
|---|---|---|
| 彩色 page | root_p547_page_r3.pdf 直接 300 dpi 光栅化为 tmp_original_C/p547_page_color_300dpi.png | 2481×3508 |
| gray page | root_p547_gray_page_r3_300dpi.png | 2481×3508 |
| standalone | root_p547_standalone_r3_300dpi.png | 2481×3508 |
| 正式 figure crop | root_p547_figure_crop_r3_300dpi.png | 2120×900 |

关键 1:1 ROI：

| 证据/ROI | 坐标 | 覆盖的潜在交互 | 结果 |
|---|---:|---|---|
| 彩色 page 主图 | [200,480,2080,900] | 左右节点、两对弧形箭头、标签框、矩阵、桥接框/箭头、caption/guide | 见下方实墨接触；其余独立对象均无接触 |
| gray page 主图 | [200,480,2080,900] | 与彩色页同一全部对象 | 同一实墨接触 |
| standalone 主图 | [100,160,2250,1000] | 同一全部对象 | 同一实墨接触 |
| 正式 crop 左图 | [70,0,750,400] | 行随机标题、a12 标签框、金色弧、反向弧、loop、矩阵 | FAIL 区可复现 |
| 正式 crop 中部 | [620,220,900,300] | 两矩阵、P=Aᵀ 桥接公式、边界、桥接箭头 | 独立对象净空至少 4 px |
| 正式 crop 右图 | [1230,0,820,400] | 列随机标题、P21 标签框、金色弧、反向弧、loop、矩阵 | FAIL 区可复现 |
| 正式 crop caption/guide | [40,500,2040,390] | caption、读图顺序、行内公式 | 独立对象净空至少 4 px |

几何失败证据（均为相邻实墨，中间连续纯白净空为 0 px，而非抗锯齿不确定）：

| 类型 | 对象与实际坐标 | 实墨 RGB | 判定 |
|---|---|---|---|
| 彩色 page | 左 a12 标签框下边 [665,683] 紧接金色弧 [665,684]；镜像右 P21 同样为 [1692,683] 与 [1692,684] | (183,121,31) / (183,121,31) | 独立标签框边与曲线 0 px，FAIL |
| gray page | 左 [665,683] 与 [665,684]；右 [1692,683] 与 [1692,684] | (130,130,130) / (130,130,130) | 0 px，FAIL |
| standalone | 左 [711,452] 与 [711,453]；右 [1738,452] 与 [1738,453] | (183,121,31) / (183,121,31) | 0 px，FAIL |
| 正式 crop | 左 [485,173] 与 [485,174]；右 [1512,173] 与 [1512,174] | (183,121,31) / (183,121,31) | 0 px，FAIL |

源级字号覆盖：无 every node 声明；全局 TikZ font=9.8/11.7 pt。state、title=10.2/12.0；lab=11.6/13.3，focus lab 继承 lab；matrix=9.8/11.7；bridge=9.6/11.5；矩阵说明为 11.8/13.6 与 11.6/13.3；桥接公式为 12.0/13.8 与 11.6/13.3。未发现 tiny、scriptsize、footnotesize、small、large 或缩放命令；所有可见节点下限不低于 9.6 pt。

300 dpi 实墨字体量测：

| 类别/示例 | ROI | glyph ink bbox | 高度与比例 |
|---|---:|---:|---|
| 普通左右说明 CJK（每行/每列） | [468,964,43,58]；[1470,964,45,58] | [476,970,35,37]；[1477,975,37,37] | 37、37 px；同类 max/min=1.00 |
| 面板题 CJK | [463,510,50,70] | [471,530,40,40] | 40 px；相对普通中位 1.08 |
| 中央桥接 CJK | [968,866,50,65] | [979,874,39,42] | 42 px；相对普通中位 1.14 |
| 公式 P | [1130,810,40,65] | [1136,824,30,33] | 33 px；数学字形相对 CJK 普通字 0.89 |

混排检查：CJK、拉丁/数学的基线和行距在两侧面板及中央桥接中协调；12 pt 桥接公式仍未超过普通注释中位的 1.35 倍，也未主导画面。  
GEOMETRY=FAIL（彩色、灰度、standalone 三类均实墨 0 px）。  
TYPOGRAPHY=PASS。  
UID=FAIL。

## FIG-P602-01

接受锁定：R3；page jobname=p602_root_r3_page；standalone jobname=p602_root_r3_standalone。  
实际图源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mh_accept_reject.tex。

证据与原生尺寸：

| 类型 | R3 文件 | native dimensions |
|---|---|---|
| 彩色 page | p602_root_r3_page.pdf 直接 300 dpi 光栅化为 tmp_original_C/p602_page_color_300dpi.png | 2481×3508 |
| gray page | p602_root_r3_gray_page_300dpi.png | 2481×3508 |
| standalone | p602_root_r3_standalone_300dpi.png | 2481×3508 |
| 正式 figure/caption/guide crop | p602_root_r3_figure_caption_guide_crop_300dpi.png | 2120×2450 |

关键 1:1 ROI：

| 证据/ROI | 坐标 | 覆盖的潜在交互 | 结果 |
|---|---:|---|---|
| 彩色 page 主图 | [180,680,2140,1660] | 所有节点、公式块、垂直箭头/标签、菱形、分支、双框、自环 | PASS；所有独立对保守净空下界至少 4 px |
| gray page 主图 | [180,680,2140,1660] | 同一对象及实线/虚线/点划线分辨 | PASS；至少 4 px，无灰阶归属歧义 |
| standalone 主图 | [200,220,2080,2720] | 同一对象 | PASS；至少 4 px |
| 正式 crop 顶部/公式 | [420,60,1280,820] | 状态框、提议/计算标签、公式与框边 | PASS；至少 4 px |
| 正式 crop 判定/分支 | [180,720,1780,780] | 判定菱形文字、接受/拒绝标签、两条分支箭头、下框边 | PASS；至少 4 px |
| 正式 crop 拒绝/自环 | [900,1150,1060,760] | 双框文字/边、点划回路、自环标签 | PASS；至少 4 px |
| 正式 crop caption/guide | [60,1740,2000,650] | caption、guide、行内公式 | PASS；至少 4 px |

未发现独立对象实墨接触、1--3 px 净空或抗锯齿归属不确定；箭头端点到各自流程节点为有意连接。

源级字号覆盖：全局 9.6/11.6 pt；every node=9.6/11.6；edge-label=9.6/11.6；中央接受率 display formula=11.8/14.2。未发现 tiny、scriptsize、footnotesize、small、large 或缩放命令；可见节点下限为 9.6 pt。

300 dpi 实墨字体量测：

| 类别/示例 | ROI | glyph ink bbox | 高度与比例 |
|---|---:|---:|---|
| 普通节点 CJK | [981,725,45,55] | [990,731,31,36] | 36 px |
| 普通分支标签 CJK | [583,1584,43,55] | [590,1589,36,37] | 37 px；普通同类范围 36--37，中位 36.5，max/min=1.03 |
| 公式块 α | [754,1184,42,62] | [763,1201,33,32] | 32 px；相对普通中位 0.88（不同数学字形） |

混排检查：节点内 CJK 与 Xt、Y、U、q、alpha 等数学字形基线清楚；显示公式置于专属中心框内，字号点值比 11.8/9.6=1.23，不触发 1.25 或 1.35 门槛，未挤压流程空间。  
GEOMETRY=PASS。  
TYPOGRAPHY=PASS。  
UID=PASS。

## FIG-P608-01

接受锁定：R3；page jobname=p608_root_r3_page；standalone jobname=p608_root_r3_standalone。  
实际图源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex。

证据与原生尺寸：

| 类型 | R3 文件 | native dimensions |
|---|---|---|
| 彩色 page | p608_root_r3_page_300dpi.png | 2481×3508 |
| gray page | p608_root_r3_gray_page_300dpi.png | 2481×3508 |
| standalone | p608_root_r3_standalone_300dpi.png | 2481×3508 |
| 正式 figure/caption/guide crop | p608_root_r3_figure_caption_guide_crop_300dpi.png | 1980×520 |

关键 1:1 ROI：

| 证据/ROI | 坐标 | 覆盖的潜在交互 | 结果 |
|---|---:|---|---|
| 彩色 page 主图 | [180,500,2140,1150] | 两面板、轴/刻度、轨迹、方/圆标记、虚线、阴影、两标题、注释 | 见下方实墨接触；其余独立对至少 4 px |
| gray page 主图 | [180,500,2140,1150] | 同一对象和灰阶线型 | 同一实墨接触 |
| standalone 主图 | [450,480,1600,1450] | 同一对象 | 同一实墨接触 |
| standalone 上图 | [620,500,1400,540] | 轨迹、预热注释、保留样本注释、上轴、下标题 | FAIL 区可复现 |
| standalone 下图 | [620,1000,1450,640] | 运行均值、方形标记、目标线、目标值、轴/刻度 | 其余独立对至少 4 px |
| 正式 crop | [0,0,1980,520] | 下图末段、caption、guide | PASS；至少 4 px |

几何失败证据：

| 类型 | 对象与实际坐标 | 实墨 RGB | 判定 |
|---|---|---|---|
| 彩色 page | 上面板 x 轴实线第 864--866 行与下面板标题 X̄ 的横线第 867--869 行相邻；区间 x=1477--1509，代表点 [1477,866] 与 [1477,867] | (31,35,40) / (31,35,40) | 坐标轴与独立标题公式 0 px，FAIL |
| gray page | 同一代表点 [1477,866] 与 [1477,867] | (34,34,34) / (34,34,34) | 0 px，FAIL |
| standalone | 轴线第 628--630 行与标题横线第 631--632 行相邻；x=1472--1503，代表点 [1472,630] 与 [1472,631] | (31,35,40) / (31,35,40) | 0 px，FAIL |

源级字号覆盖：全局 9.6/11.6 pt；tick label=9.6/11.6；label 与 title=10.8/13.0；预热、保留样本、目标值节点均显式 9.6/11.6。未发现 every node 覆盖、tiny、scriptsize、footnotesize、small、large 或缩放命令；可见节点下限为 9.6 pt。

300 dpi 实墨字体量测：

| 类别/示例 | ROI | glyph ink bbox | 高度与比例 |
|---|---:|---:|---|
| 上/下图刻度 2 | [703,612,30,55]；[703,1044,30,55] | [708,624,20,26]；[709,1056,18,26] | 26、26 px；跨面板 max/min=1.00 |
| 普通注释 CJK（保留/目标） | [1284,660,45,55]；[1717,940,46,55] | [1290,666,38,36]；[1731,946,26,35] | 36、35 px；中位 35.5，max/min=1.03 |
| 标题 CJK | [1254,531,54,67] | [1262,536,46,42] | 42 px；相对普通中位 1.18 |
| 数学标题 Xt | [1368,530,72,70] | [1368,544,32,40] | 40 px；数学上/下标为预期层级 |

混排检查：两面板同类刻度实测一致；CJK、拉丁/数学的字重、基线、行距在 1:1 下协调，标题只比普通注释高约 1.18 倍，不存在字号门失败。标题与轴的接触是几何问题，不是字体量测歧义。  
GEOMETRY=FAIL（彩色、灰度、standalone 三类均实墨 0 px）。  
TYPOGRAPHY=PASS。  
UID=FAIL。

## FIG-P609-01

接受锁定：R3；page jobname=p609_root_r3_page；standalone jobname=p609_root_r3_standalone。  
实际图源：D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_autocorrelation_ess.tex。

证据与原生尺寸：

| 类型 | R3 文件 | native dimensions |
|---|---|---|
| 彩色 page | p609_root_r3_page_300dpi.png | 2481×3508 |
| gray page | p609_root_r3_gray_page_300dpi.png | 2481×3508 |
| standalone | p609_root_r3_standalone_300dpi.png | 2481×3508 |
| 正式 figure crop | R3 未提供；standalone 为协议允许的第三类证据 | 2481×3508 |

关键 1:1 ROI：

| 证据/ROI | 坐标 | 覆盖的潜在交互 | 结果 |
|---|---:|---|---|
| 彩色 page 主图 | [180,330,2140,1100] | ACF 轴/刻度/柱/圆标记、阴影、截断线/注释、省略号、面板箭头、ESS 卡片/公式/边框 | PASS；所有独立对至少 4 px |
| gray page 主图 | [180,330,2140,1100] | 同一对象及色彩转换后的可分辨性 | PASS；至少 4 px，无归属歧义 |
| standalone 主图 | [280,500,1950,1550] | 同一对象 | PASS；至少 4 px |
| standalone ACF | [300,580,900,1250] | 轴/刻度、柱/圆、截断线、截断标签、省略号 | PASS；截断标签实墨到虚线实墨的保守白隙至少 24 px |
| standalone ESS | [1120,570,1100,1250] | 卡片边框/标题/公式/警示、面板箭头 | PASS；所有独立对至少 4 px |

未发现独立对象实墨接触、1--3 px 净空或抗锯齿不确定。彩色 page 上截断标签右侧实墨最靠近处约 x=1022，金色虚线实墨为 x=1051--1053，仍保守留有至少 24 px 连续白隙；gray page 与 standalone 一致。

源级字号覆盖：全局 9.6/11.8 pt；tick=9.6/11.8；label=9.8/12.0；title=10.4/12.6；every node=9.6/11.8；截断/省略号节点=9.6/11.8；ESS 卡片体=9.6/11.8、卡片题=10.4/12.6 bold。caption 有 normalsize 覆盖（非图节点）；未发现 tiny、scriptsize、footnotesize、small、large 或缩放命令；可见节点下限为 9.6 pt。

300 dpi 实墨字体量测：

| 类别/示例 | ROI | glyph ink bbox | 高度与比例 |
|---|---:|---:|---|
| 轴刻度 0 | [538,950,30,55] | [544,961,18,27] | 27 px |
| 普通注释 CJK（截断/预设窗口） | [831,512,45,55]；[1316,768,45,55] | [838,518,37,36]；[1322,788,38,35] | 36、35 px；中位 35.5，max/min=1.03 |
| 两处同层级标题 CJK | [688,358,52,72]；[1368,451,50,72] | [695,379,45,40]；[1376,472,40,41] | 40、41 px；中位 40.5，max/min=1.03 |
| 公式块 τ | [1290,570,65,70] | [1322,581,33,36] | 36 px；相对普通中位 1.01 |

混排检查：CJK、ACF/ESS 拉丁、tau/rho/分式数学的 apparent x-height、字重、基线及卡片行距均协调；标题相对普通注释约 1.14 倍，具有明确面板/卡片标题语义且不主导图形。  
GEOMETRY=PASS。  
TYPOGRAPHY=PASS。  
UID=PASS。

## 汇总

| UID | 原对话完成项 | GEOMETRY | TYPOGRAPHY | UID 结论 |
|---|---|---|---|---|
| FIG-P547-01 | 是 | FAIL | PASS | FAIL |
| FIG-P602-01 | 是 | PASS | PASS | PASS |
| FIG-P608-01 | 是 | FAIL | PASS | FAIL |
| FIG-P609-01 | 是 | PASS | PASS | PASS |

总计：PASS=2；FAIL=2；AMBIGUOUS=0。
