# SA3-AUDIT-B — 已接受图的原生像素叠压与字体层级独立复核

审计员：B（独立于旧验收 PASS 文本）。  
审计日期：2026-08-23。  
适用协议：<code>STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md</code>。旧 ROOT-ACCEPTANCE 仅用于锁定候选轮次、jobname 和图源；本报告的结论来自本轮在原始 PNG 上的检查。

## 判定方法与范围

- 逐 UID 先读取对应 R3/R3.1 的 ROOT-ACCEPTANCE；下列三张 PNG 均来自该接受 job set，不跨轮次混用。
- 每张列出的 PNG 都以 original/high detail 查看；随后在原生像素上查看下列 <code>tmp_B</code> 的无缩放、无插值 raw ROI。ROI 文件名中的 <code>x/y/w/h</code> 与表内原图坐标一致。
- 对所有文字、数学、轴/刻度、曲线、箭头、边框、图例、标记和相邻面板的邻域逐一复核。PASS 的最小净空均指连续可见白隙，且不把抗锯齿边缘当作白隙；数值均大于等于 4 px。若有坐标轴，轴本身与其刻度的有意连接不计作冲突。
- 像素高度是 300 dpi 原图中代表 glyph 的实墨 bounding-box 高度（px），按同一语义类别比较；CJK、拉丁、数学字符的字形结构不同，因此不以跨脚本单个 glyph 高度代替字号比较。每项均同时检查基线、字重和行距。
- 图源静态扫描覆盖全局图样式、<code>every node</code> 和所有命中的 <code>fontsize/tiny/scriptsize/footnotesize/small/large</code> 覆盖；未发现 <code>tiny/scriptsize/footnotesize/small/large</code> 或 <code>scale/transform shape</code> 规避项，除非各 UID 条目另述。
- 仅写入本报告和既有获准的 <code>tmp_B</code> 诊断裁剪；未构建、未修复、未修改图源、wrapper、manifest、JSON 或中央状态。

路径约定：以下路径均为完整 Windows 路径；<code>tmp_B</code> 位于 <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\tmp_B</code>。

## 汇总

| UID | accepted round / jobname | OVERLAP_RESULT | TYPOGRAPHY | UID_RESULT |
|---|---|---:|---:|---:|
| FIG-P684-01 | R3 / p684_root_r3 | PASS | PASS | PASS |
| FIG-P694-01 | R3 / p694_root_r3 | PASS | PASS | PASS |
| FIG-P695-01 | R3 / p695_root_r3 | PASS | PASS | PASS |
| FIG-P715-01 | R3 / current evidence set | AMBIGUOUS | FAIL | FAIL |
| FIG-P716-01 | R3 / p716_root_r3 | PASS | PASS | PASS |
| FIG-P717-01 | R3 / p717_root_r3 | PASS | PASS | PASS |
| FIG-P721-01 | R3 / p721_root_r3 | PASS | PASS | PASS |
| FIG-P736-01 | R3 / p736_root_r3 | PASS | PASS | PASS |
| FIG-P737-01 | R3 / p737_root_r3 | PASS | PASS | PASS |
| FIG-P740-01 | R3 / p740_root_r3 | PASS | PASS | PASS |
| FIG-P745-01 | R3 / p745_root_r3 | PASS | PASS | PASS |
| FIG-P748-01 | R3.1 / p748_root_r3p1 | PASS | PASS | PASS |
| FIG-P750-01 | R3 / p750_root_r3 | PASS | PASS | PASS |
| FIG-P756-01 | R3.1 / p756_root_r3p1 | PASS | PASS | PASS |

## 逐 UID 记录

### FIG-P684-01

- accepted_round=R3；accepted_jobname=<code>p684_root_r3_page</code> / <code>p684_root_r3_standalone</code>。接受图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_generative_process.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. 彩色 page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P684-01\R3\p684_root_r3_page_300dpi.png</code>
  2. gray page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P684-01\R3\p684_root_r3_gray_page_300dpi.png</code>
  3. standalone：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P684-01\R3\p684_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：彩色 <code>tmp_B\B_FIG-P684-01_page_ALL_x280_y350_w1940_h1100.png</code> [280,350,1940,1100]；gray <code>tmp_B\B_FIG-P684-01_gray_ALL_x280_y350_w1940_h1100.png</code> [280,350,1940,1100]；standalone <code>tmp_B\B_FIG-P684-01_standalone_ALL_x280_y180_w1940_h1100.png</code> [280,180,1940,1100]。
- large_operator_present=NO。生成过程的主题/词/文档框、五组箭头、右侧弧形关系和标签均分离；未见箭头、弧线或框线穿字。最小观察净空约 14 px（右侧标签—弧线/邻框）；三类一致。
- 静态字号：全局及 every node 为 9.6/11.5 pt；局部标题 10.2/12.2 pt 粗体；局部注释 9.6/11.5 pt。无其他命中覆盖。
- 300 dpi 实墨：普通 CJK/拉丁注释 34–36 px（中位 35）；标题 38–40 px（中位 39，语义标题）；数学/图例式符号 33–36 px（中位 35）。同类跨块最大比 1.06；CJK、拉丁、数学基线同齐、字重和行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P694-01

- accepted_round=R3；accepted_jobname=<code>p694_root_r3_page</code> / <code>p694_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_variational_updates.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P694-01\R3\p694_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P694-01\R3\p694_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P694-01\R3\p694_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P694-01_page_ALL_x250_y300_w2000_h2600.png</code> [250,300,2000,2600]；<code>tmp_B\B_FIG-P694-01_gray_ALL_x250_y300_w2000_h2600.png</code> [250,300,2000,2600]；<code>tmp_B\B_FIG-P694-01_standalone_ALL_x250_y200_w2000_h2500.png</code> [250,200,2000,2500]。
- large_operator_present=YES（多处 <code>\sum</code>）。Local VI/VEM 的各公式框、求和号的上下限、分隔线和相邻箭头逐处查看：求和号与上下限未同轴线/边框连笔，框内留白清楚；B4 底行与框线、箭头与文字均无接触。最小观察净空约 12 px（公式实墨—框线）；三类一致。
- 静态字号：全局/every node 9.6/10.3 pt；标题 10.2/12.2 pt 粗体；局部公式/注释 9.6/9.9 pt。无其他命中覆盖。
- 300 dpi 实墨：普通说明 34–36 px（中位 35）；标题 38–40 px（39）；公式基线字形 33–36 px（35），大型 Σ 的轮廓高约 48–49 px 仅为数学运算符的固有构形，并未改变同类基线字号。重复面板普通标签最大比 1.06；CJK/Latin/数学的基线、间距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P695-01

- accepted_round=R3；accepted_jobname=<code>p695_root_r3_page</code> / <code>p695_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_method_comparison.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P695-01\R3\p695_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P695-01\R3\p695_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P695-01\R3\p695_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P695-01_page_ALL_x250_y350_w2000_h1800.png</code> [250,350,2000,1800]；<code>tmp_B\B_FIG-P695-01_gray_ALL_x250_y350_w2000_h1800.png</code> [250,350,2000,1800]；<code>tmp_B\B_FIG-P695-01_standalone_ALL_x250_y200_w2000_h1900.png</code> [250,200,2000,1900]。
- large_operator_present=YES（<code>\sum</code>）。比较卡片/表格的求和、分式、行标签、分隔框逐处检查；上下限未碰到行线，公式块与表格边界、相邻卡片不重叠。最小观察净空约 14 px；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；标题 10.2/12.2 pt 粗体；强调行 9.6/11.6 pt 粗体。无其他命中覆盖。
- 300 dpi 实墨：普通卡片文字 34–36 px（35）；栏目标题 38–40 px（39）；公式/比较符号基线 33–36 px（35），Σ 轮廓约 48 px 为固有数学形状。重复卡同类最大比 1.06；文字、数学与细框间距平衡。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P715-01

- accepted_round=R3；accepted_jobname=<code>current evidence set</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex</code>。
- 实检 PNG：
  1. 彩色 page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P715-01\R3\current_full_page_200dpi.png</code>，1654×2339, 200 dpi。
  2. gray page：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P715-01\R3\current_gray_page_300dpi.png</code>，2481×3508, 300 dpi。
  3. 正式 figure crop：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P715-01\R3\current_figure_crop_300dpi.png</code>，1810×875, 300 dpi。
- 1:1 ROI：<code>tmp_B\B_FIG-P715-01_page_ALL_x100_y200_w1450_h750.png</code> [100,200,1450,750]（仅 200 dpi，不能替代协议要求）；<code>tmp_B\B_FIG-P715-01_gray_ALL_x150_y300_w2180_h1125.png</code> [150,300,2180,1125]；<code>tmp_B\B_FIG-P715-01_standalone_ALL_x0_y0_w1810_h875.png</code> [0,0,1810,875]。
- large_operator_present=YES（<code>c_j=\sum_r...</code>）。现有三项中，随机游走节点、边注、求和公式、表格和箭头的实墨未观察到重合；可见的最小净空约 12 px。但协议要求的“最终彩色 page 300 dpi”不存在；200 dpi 彩色页不能证明 300 dpi 的 4 px 门槛。因此这是**证据缺口**，不是以缩略/重建补证的几何 PASS。
- 静态字号：全局图样式及 every node 均为 **9.5/11.5 pt**；标题 10.4/12.4 pt 粗体；圆形 page/cell 10.2/12.2 pt；edge note/note 9.5/11.5 pt；formula 12/14 pt。无其它命中覆盖。9.5 pt 低于项目可见节点下限 9.6 pt，已构成独立硬失败。
- 300 dpi 实墨（gray/crop）：普通边注 34–35 px（中位 35）；节点文字 38–40 px（39）；公式基线 42–44 px（43）。同类在可用的两个 300 dpi 证据中最大比 1.06，混排本身协调；但像素表象不能豁免 9.5 pt 的源级下限违反。
- GEOMETRY=AMBIGUOUS；OVERLAP_RESULT=AMBIGUOUS；TYPOGRAPHY=FAIL；UID_RESULT=FAIL。
- 非通过原因分离记录：几何为缺少彩色 300 dpi page 的证据不足；字体为明确的 9.5 pt < 9.6 pt。未重建或补写证据。

### FIG-P716-01

- accepted_round=R3；accepted_jobname=<code>p716_root_r3_page</code> / <code>p716_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\periodic_dangling_failures.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P716-01\R3\p716_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P716-01\R3\p716_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P716-01\R3\p716_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P716-01_page_R2_ALL_x250_y350_w2000_h1500.png</code> [250,350,2000,1500]；<code>tmp_B\B_FIG-P716-01_gray_R2_ALL_x250_y350_w2000_h1500.png</code> [250,350,2000,1500]；<code>tmp_B\B_FIG-P716-01_standalone_R2_ALL_x250_y150_w2000_h1550.png</code> [250,150,2000,1550]。其中 R2 是诊断 crop 的批次标签，不是图证据轮次；其原图均为上列接受的 R3 PNG。
- large_operator_present=NO。两个状态面板、过渡箭头、圆节点与框标签均无穿字或相碰；下边框完整、无截断。最小观察净空约 17 px（箭头/转移标签）；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；左右标题 10.2/12.2 pt 粗体；transition label 9.6/11.6 pt。无其它命中覆盖。
- 300 dpi 实墨：普通状态/转移标签 34–36 px（35）；标题 38–40 px（39）；图例/公式式转移标记 34–36 px（35）。左右同类最大比 1.06；CJK/Latin 基线、粗细与行距一致。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P717-01

- accepted_round=R3；accepted_jobname=<code>p717_root_r3_page</code> / <code>p717_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\inbound_contribution.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P717-01\R3\p717_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P717-01\R3\p717_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P717-01\R3\p717_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P717-01_page_R2_FULL_x300_y250_w2100_h1500.png</code> [300,250,2100,1500]；<code>tmp_B\B_FIG-P717-01_gray_R2_FULL_x300_y250_w2100_h1500.png</code> [300,250,2100,1500]；<code>tmp_B\B_FIG-P717-01_standalone_R2_FULL_x350_y250_w1900_h1400.png</code> [350,250,1900,1400]。R2 同样只是诊断 crop 批次标签，原图为接受 R3。
- large_operator_present=YES（显示型 <code>\displaystyle\sum</code>）。入边箭头、标签和两处显示求和式均清晰分离；Σ、上下限和公式框/箭头不存在连笔或框线侵入。最小观察净空约 13 px；三类一致。
- 静态字号：全局/every node 9.6/11.5 pt；局部转移/注释 9.6/11.5 pt；标题 10.2/12.2 pt 粗体。无其它命中覆盖。
- 300 dpi 实墨：普通节点/注释 34–36 px（35）；标题 38–40 px（39）；公式基线 34–36 px（35），显示 Σ 约 48–49 px 是运算符构形。重复入边标签最大比 1.06；CJK、Latin、数学对齐正常。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P721-01

- accepted_round=R3；accepted_jobname=<code>p721_root_r3_page</code> / <code>p721_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\numerical_rank_trajectory.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P721-01\R3\p721_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P721-01\R3\p721_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P721-01\R3\p721_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P721-01_page_R2_FULL_x250_y500_w2200_h1100.png</code> [250,500,2200,1100]；<code>tmp_B\B_FIG-P721-01_gray_R2_FULL_x250_y500_w2200_h1100.png</code> [250,500,2200,1100]；<code>tmp_B\B_FIG-P721-01_standalone_R2_FULL_x300_y250_w1900_h950.png</code> [300,250,1900,950]。R2 是诊断 crop 批次标签，原图为接受 R3。
- large_operator_present=NO。轴、刻度、曲线、橙色 cutoff、峰位、标签与图例逐一查看。standalone 的橙色 cutoff 线实墨为 x=1042–1045，邻近 cutoff 文本实墨始于 x=1065，净空 19 px；其余轴/曲线—文字交互区更大。无字形被轴线穿过、无边界截断；三类一致。
- 静态字号：全局/every node/every pin 9.6/11.5 pt；title 10.2/12.2 pt；axis label/tick label 9.6/11.5 pt；加粗标记 9.6/11.5 pt。无其它命中覆盖。
- 300 dpi 实墨：轴刻度数字 26–27 px（中位 27，数字 glyph 的窄高度）；普通 CJK 注释 35–36 px（35）；图例 CJK 35–36 px（35）；标题 38–40 px（39）。同类跨两图最大比 1.04；数字与 CJK 的高度差符合字形/x-height，不是字号漂移，基线和行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P736-01

- accepted_round=R3；accepted_jobname=<code>p736_root_r3_page</code> / <code>p736_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\method_family_relationships.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P736-01\R3\p736_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P736-01\R3\p736_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P736-01\R3\p736_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P736-01_page_R2_FULL_x250_y250_w2100_h1600.png</code> [250,250,2100,1600]；<code>tmp_B\B_FIG-P736-01_gray_R2_FULL_x250_y250_w2100_h1600.png</code> [250,250,2100,1600]；<code>tmp_B\B_FIG-P736-01_standalone_R2_FULL_x350_y200_w1800_h1300.png</code> [350,200,1800,1300]。R2 是诊断 crop 批次标签，原图为接受 R3。
- large_operator_present=NO。方法家族卡片、行标题、路由箭头、箭头头部、框线及注释均无接触；未见路径穿入字框。最小观察净空约 14 px；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；rowtitle 10.2/12.2 pt 粗体；card/routeexample 9.6/11.6 pt。无其它命中覆盖。
- 300 dpi 实墨：普通 CJK card/legend 35–37 px（中位 36）；行标题 39–40 px（39）；route/图例同类 35–36 px（35）。各行同类最大比 1.06；CJK、Latin、箭头文字的基线与字重协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P737-01

- accepted_round=R3；accepted_jobname=<code>p737_root_r3_page</code> / <code>p737_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\task_representation_inference_cube.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P737-01\R3\p737_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P737-01\R3\p737_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P737-01\R3\p737_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P737-01_page_ALL_x250_y400_w2000_h2200.png</code> [250,400,2000,2200]；<code>tmp_B\B_FIG-P737-01_gray_ALL_x250_y400_w2000_h2200.png</code> [250,400,2000,2200]；<code>tmp_B\B_FIG-P737-01_standalone_ALL_x300_y200_w2000_h2100.png</code> [300,200,2000,2100]。
- large_operator_present=NO。三轴网格、分支卡片、连线、底部规格公式和边界逐处检查；无连线穿字、无公式挤贴卡片/边框。最小观察净空约 13 px；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；coltitle/branchhead/底部标题 10.2/12.2 pt 粗体；规格中的 <code>(T,R,I)</code> 与完整可核验公式 12/14 pt。无其它命中覆盖。
- 300 dpi 实墨：普通卡片 34–36 px（35）；标题 38–40 px（39）；公式 42–44 px（43）。公式为唯一、明确语义的规格层级，比例 43/35=1.23，小于 1.35，且有完整外侧留白，未主导画面；重复卡同类最大比 1.06。混排基线/行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P740-01

- accepted_round=R3；accepted_jobname=<code>p740_root_r3_page</code> / <code>p740_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\matrix_probability_bridge.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P740-01\R3\p740_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P740-01\R3\p740_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P740-01\R3\p740_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P740-01_page_ALL_x300_y400_w1900_h1300.png</code> [300,400,1900,1300]；<code>tmp_B\B_FIG-P740-01_gray_ALL_x300_y400_w1900_h1300.png</code> [300,400,1900,1300]；<code>tmp_B\B_FIG-P740-01_standalone_ALL_x300_y150_w1900_h1400.png</code> [300,150,1900,1400]。
- large_operator_present=NO。矩阵桥接、条件高斯面板、公式块、坐标标记、曲线与连接箭头均分离；未见曲线/框线侵入数学字形。最小观察净空约 15 px；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；sectiontitle 10.2/12.2 pt 粗体；两处关键公式 11.8/14.0 pt。无其它命中覆盖。
- 300 dpi 实墨：普通注释/刻度 34–36 px（35）；section title 38–40 px（39）；公式 42–43 px（42）。公式比例 42/35=1.20，有明确桥接语义且未挤占图形；同类最大比 1.06，CJK/Latin/math 基线、字重、行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P745-01

- accepted_round=R3；accepted_jobname=<code>p745_root_r3_page</code> / <code>p745_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\fig_v5_c08_validation_protocols.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P745-01\R3\p745_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P745-01\R3\p745_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P745-01\R3\p745_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P745-01_page_ALL_x300_y750_w1900_h1350.png</code> [300,750,1900,1350]；<code>tmp_B\B_FIG-P745-01_gray_ALL_x300_y750_w1900_h1350.png</code> [300,750,1900,1350]；<code>tmp_B\B_FIG-P745-01_standalone_ALL_x300_y200_w1900_h1500.png</code> [300,200,1900,1500]。
- large_operator_present=NO。双验证路径、禁用反馈虚线、橙色 X、箭头头部、数据/公式节点和边框全部检查。standalone 中左 X bbox=[396,877,35,32]，邻虚线箭头头部=[478,885,23,17]，x 向净空 47 px；右箭头头部约 [2016,886,23,15]，右 X bbox=[2085,877,35,32]，净空 46 px。不存在警示符与箭头/文字重叠；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；lane title 10.2/12.2 pt 粗体；crossmark 和数据数学 span 12/14 pt；bottomnote 9.6/11.6 pt。无其它命中覆盖。
- 300 dpi 实墨：普通流程/底注 34–36 px（35）；lane title 38–40 px（39）；数学 span/crossmark 42–44 px（43）。12 pt 为数据符号和警示的明确语义层级；43/35=1.23，且 X 外侧具有上述 46–47 px 安全区，不主导/挤压面板。左右同类最大比 1.06；混排协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P748-01

- accepted_round=R3.1；accepted_jobname=<code>p748_root_r3p1_page</code> / <code>p748_root_r3p1_standalone</code>（证据目录按接受报告为 R3，jobname 后缀 r3p1）。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\evaluation_dashboard.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P748-01\R3\p748_root_r3p1_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P748-01\R3\p748_root_r3p1_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P748-01\R3\p748_root_r3p1_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P748-01_page_R2_FULL_x250_y350_w2100_h1400.png</code> [250,350,2100,1400]；<code>tmp_B\B_FIG-P748-01_gray_R2_FULL_x250_y350_w2100_h1400.png</code> [250,350,2100,1400]；<code>tmp_B\B_FIG-P748-01_standalone_R2_FULL_x350_y250_w1800_h1100.png</code> [350,250,1800,1100]。R2 是诊断 crop 批次标签，原图为接受 R3.1 job set。
- large_operator_present=NO。五个 dashboard card、微图、标题、指标文本、报告条带、边框与相邻卡片均无实墨接触或截断。最小观察净空约 19 px；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；每张卡标题 10.2/12.2 pt 粗体；每张卡的指标/单位/不确定性文本均为 12/14 pt。无其它命中覆盖。
- 300 dpi 实墨：报告条带的普通说明 34–36 px（35）；五张卡标题 38–40 px（39）；五张卡重复的指标 CJK/Latin 42–45 px（中位 43）。12 pt 指标在所有 card 中一致、属于面板主读数，且 43/35=1.23、小于 1.25 的无语义异常阈值；同类跨五卡最大比 1.07。白字报告条带与色块对比清楚，混排基线/行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P750-01

- accepted_round=R3；accepted_jobname=<code>p750_root_r3_page</code> / <code>p750_root_r3_standalone</code>。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\method_selection_decision_map.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P750-01\R3\p750_root_r3_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P750-01\R3\p750_root_r3_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P750-01\R3\p750_root_r3_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P750-01_page_ALL_x200_y400_w2100_h950.png</code> [200,400,2100,950]；<code>tmp_B\B_FIG-P750-01_gray_ALL_x200_y400_w2100_h950.png</code> [200,400,2100,950]；<code>tmp_B\B_FIG-P750-01_standalone_ALL_x200_y200_w2100_h1000.png</code> [200,200,2100,1000]。
- large_operator_present=NO。决策根、分支箭头、反馈路线、终止框、标签和边框均有明确白隙；无箭头头部撞入文字或框线、无边缘截断。最小观察净空约 18 px；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；root 10.2/12.2 pt 粗体；其余可见节点为 9.6/11.6 pt。无其它命中覆盖。
- 300 dpi 实墨：普通节点/路线标签 34–36 px（35）；root 38–40 px（39）；图例/终止说明 34–36 px（35）。同类最大比 1.06；root 是唯一语义起点，层级适度；混排协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

### FIG-P756-01

- accepted_round=R3.1；accepted_jobname=<code>p756_root_r3p1_page</code> / <code>p756_root_r3p1_standalone</code>。仅使用 r3p1 原图；未使用目录中的遗留 r3 PNG 或旧诊断 crop。图源：<code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex</code>。
- 实检 PNG（均为 2481×3508, 300 dpi）：
  1. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P756-01\R3\p756_root_r3p1_page_300dpi.png</code>
  2. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P756-01\R3\p756_root_r3p1_gray_page_300dpi.png</code>
  3. <code>D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P756-01\R3\p756_root_r3p1_standalone_300dpi.png</code>
- 1:1 ROI：<code>tmp_B\B_FIG-P756-01_page_R3P1_FULL_x200_y200_w2050_h2400.png</code> [200,200,2050,2400]；<code>tmp_B\B_FIG-P756-01_gray_R3P1_FULL_x200_y200_w2050_h2400.png</code> [200,200,2050,2400]；<code>tmp_B\B_FIG-P756-01_standalone_R3P1_FULL_x300_y250_w1900_h1350.png</code> [300,250,1900,1350]。
- large_operator_present=NO。五站环、两条任务路径、引擎/报告块、节点文字、图例、边框和箭头头部在实际 r3p1 三证据中均无接触/覆盖；无路径穿字或边界裁切。最小观察净空约 20 px；三类一致。
- 静态字号：全局/every node 9.6/11.6 pt；panel title 10.2/12.2 pt 粗体；report 白色粗体 9.6/11.6 pt；legend 9.6/11.6 pt。无其它命中覆盖。
- 300 dpi 实墨：普通节点/legend CJK 34–36 px（35）；panel title 38–40 px（39）；report 白色字 34–36 px（35）。同类跨环/路径最大比 1.06；白字在原生阅读尺度保持清楚，CJK/Latin/数学符号基线、字重、行距协调。
- GEOMETRY=PASS；OVERLAP_RESULT=PASS；TYPOGRAPHY=PASS；UID_RESULT=PASS。

## 最终计数与处置提示

- COVERAGE=14/14
- UID_RESULT：PASS=13；FAIL=1；AMBIGUOUS=0。
- 几何门：PASS=13；FAIL=0；AMBIGUOUS=1。
- 字体门：PASS=13；FAIL=1；AMBIGUOUS=0。
- 所有非 PASS UID：FIG-P715-01（GEOMETRY/OVERLAP_RESULT=AMBIGUOUS：缺少最终彩色 page 300 dpi；TYPOGRAPHY=FAIL：实际接受图源的可见默认/edge-note/note 为 9.5 pt，低于 9.6 pt 下限；故 UID_RESULT=FAIL）。

本报告不修改中央状态；由根线程在收齐独立审查后按单写者规则处理状态与后续修复。
