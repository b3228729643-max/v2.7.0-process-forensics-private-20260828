# FIG-P521-01 · SA1 独立严格 R1 首审

RESULT: **FAIL**  
NEXT_ROLE: **SA2（定向修复）**  
SA3 建议：**不建议**（存在硬门失败）。

## 冻结输入与覆盖

- 冻结唯一输入：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`
- 本图在冻结 PDF 的实际物理页为 **567**，印刷页为 **554**；由 `图 29.1` 题注、前后文与 `fig:V4-C06-plsa-dag` 交叉定位。任务卡中的历史物理页 620 与当前冻结版不一致，未将 620 页作为本图证据。
- 图源：`src/绘图源码/第04册_无监督学习与矩阵分解/V4-C06/fig_v4_c06_plsa_dag.tex`（行 3–46）。相邻正文：`src/讲义源码/第04册_无监督学习与矩阵分解/chapters/V4-C06.tex:213–225`。
- 覆盖：13 个可见语义文字对象、103 个可见 glyph/数学子串（空白胶水不计）、16 个原始 PDF vector 对象、78 个文字—文字对、208 个文字—图形对、4 个有意线—节点连接关系。未读取任何旧 SA/根报告、旧截图、旧测量或旧结论；未修改源码、公共样式、构建或状态。
- 渲染：`pdftocairo` 从冻结最终 PDF 原生输出 200/300 dpi；局部图是 300 dpi PNG 的像素裁切，未 resize。前景只取局部背景差 ≥20/255 的 raw mask；无形态膨胀；文字和 vector mask 分离后才做交集/距离。

## 正式八栏审查表

| 审查门 | 对象/范围 | 强制阈值 | 方法与证据 | 精确结果 | 显式布尔 | 结论/影响 | SA2 可执行动作 |
|---|---|---|---|---|---|---|---|
| 定位、题注、相邻正文 | `图29.1`、页 567/554、图源及 `V4-C06.tex:213–225` | 图号、题注、上下文必须一一对应 | `final_full_page_200dpi.png`、`final_full_page_300dpi.png`、PDF 文本/源行交叉定位 | 图号、题注文本与源 `\caption` 一致；实际页 567，不是历史页 620 | `REFERENCE_LOCATION_PASS=true` | 定位成立；历史页号应由主线程台账更新，但不构成图形几何失败 | 修复后沿用 PDF 搜索定位，不按旧页号取证 |
| 源级有效字号 | T01–T13 | 一般读者文字有效字号 ≥9.5pt；无法还原即 FAIL | `after_font_audit.csv`，源行 3、15–16、33、35、39–44、46；caption 公共样式行 305 | T01–T05、T08–T09 = **9.4pt**；T06–T07、T10–T12 = **8.8pt**；只有 T13 caption = 10.0pt。12/13 对象失败 | `SOURCE_FONT_PASS=false` | 绝对下限失败，不能以图面尚可读放行 | 不要整体缩放。先重排/拆层，令主文字、plate、legend 的最终有效字号均 ≥9.5pt，并重新从最终 PDF 还原 scale |
| 300 dpi raw H_ink | 103 个 glyph/子串；含 `=`,`∶`,`→`,`：`,`，`,`；`, caption `.` | CJK/全角 ≥30；数字/大写 ≥24；小写/希腊 ≥17；数学运算符/标点 ≥22；自然上下标 ≥15 px | `after_pixel_measurements.csv`；每个 PDF glyph bbox 映射到原生 300 dpi；raw foreground 无膨胀 | **15/103** 失败：`=` 12/13px（4 个，需 22）；`∶` 21px（2 个，需 22）；`→` 16px（2 个，需 22）；legend `：` 19px（3 个，需 30）；caption `.` 7px、`：` 22px、`，` 13px、`；` 28px（各低于门） | `PIXEL_HEIGHT_PASS=false` | 父公式高度未替代这些字符；任一失败即硬 FAIL | 以重新排版后的 300 dpi 实测为准。仅把 9.4 升到 9.5 不会满足 `=`/箭头/标点门；按当前 raw 比例，`=` 约需 17.3pt 等量级，caption `.` 更需单独的局部字形/编号方案与实测验证 |
| 同类像素比例 | 同角色、同 script-class 组件 | 每个 H_ink/类中位数 ∈[0.92,1.08]；角色中位数 max/min ≤1.08 | `after_pixel_measurements.csv` 的 `CLASS_MEDIAN_PX`、`RATIO_TO_CLASS_MEDIAN` | **26/103** 组件越界，范围 **0.3288–1.6744**；例如参数式 `=` 0.3288，summary `∣` 1.6744，legend `：` 0.5758 | `SAME_CLASS_RATIO_PASS=false` | 真实墨迹的同类比例未满足严格门 | 修复字号/字形后再测 103 个组件；不要以父公式 bbox 或视觉主观判断覆盖此项 |
| 语义角色比例与字体视觉协调 | NODE=9.4pt 为 BASE；formula、plate、legend、caption | legend/注释 [0.95,1.10]；formula [1.00,1.18]；普通层级不可突兀 | `audit.json.role_audit`、四视图 | plate = **0.9362**，legend = **0.9362**，均低于 0.95；formula=1.0000、caption=1.0638。200dpi 整页中 plate/legend 视觉偏弱 | `ROLE_RATIO_PASS=false`; `FONT_VISUAL_HARMONY_PASS=false`; `VISUAL_HARMONY_PASS=false` | 角色层级与绝对字号双重失败 | 在满足 raw 像素门的前提下，保持 plate/legend 与 NODE 的有效字号比例 ≥0.95；用扩展布局/分图腾出空间，不能缩小文字 |
| 零重叠、净空、裁切 | 78 TEXT–TEXT + 208 TEXT–GRAPHIC；另登记 4 条有意边连接 | overlap=0；TEXT–TEXT bbox ≥4px；TEXT–线/箭/marker ≥3px；节点文字–边框 ≥5px；clip=0 | `after_overlap_report.csv`、`masks/`、`rois/`；原图 ROI、双方分离 mask 与 overlay 已生成 | 非豁免对 **286** 个均为 raw overlap **0**；最小 TEXT–TEXT bbox 净空 **19px**（T11–T12）；最小 TEXT–GRAPHIC raw 净空 **9px**（T08–summary box，阈值 3）；节点文字—自身边框全部 ≥5；CLIP=0 | `OVERLAP_PIXEL_COUNT=0`; `CLIP_PIXEL_COUNT=0`; `CLEARANCE_PASS=true` | 几何门目前通过；4 条有意 line–node 连接已单列为 exempt，未冒充文字重叠 | 语义/字号修复后保留或增加净空；完整重测 286 个非豁免对和 4 个边关系 |
| 四视图、灰度、整页融合 | 200dpi 整页、300dpi crop、standalone crop、300dpi gray | 四视图均不得破坏层级/可辨性/页面融合 | `final_full_page_200dpi.png`、`final_figure_crop_300dpi.png`、`final_standalone_crop_300dpi.png`、`final_grayscale_300dpi.png` | 圆/矩形、实心/空心和线条在灰度下仍可分；图号题注单行，整页无异常空白或分页断裂 | `GRAYSCALE_PASS=true`; `PAGE_INTEGRATION_PASS=true` | 视图本身无额外失败，但不抵消字号/语义硬 FAIL | 修复后在同四视图重验；不要借图面整体缩小维持当前融合 |
| PLSA 概率语义、条件依赖、观测/潜变量、plate、箭头与正文 | `d,z,w,θ_d,φ_z`、内/外 plate、正文 213–225 | 箭头、条件独立、变量角色、重复次数和参数作用域须与正文一致 | 图源、页 567、`critical_phi_inside_D_plate_*` 三件套、正文行 213/217/220 | 正确：`d→z→w`、`w⊥d∣z`、`d,w`观测、`z`潜变量、θ/φ 公式。失败：**φ_z=P(w∣z) 被画在 `d=1:D` 外层 plate 内**，使本应跨文档共享的主题—词分布看成逐文档复制；内 plate 写 `n=1:N_d`，正文却定义文档 `d_j` 的重复次数为 `L_j` | `MATH_SEMANTICS_PASS=false`; `TEXT_CONSISTENCY_PASS=false` | 该图的 plate 作用域与正文符号不一致；不能在数学语义上 PASS | 将 φ_z 置于 D-plate 外（箭头可跨边界）；只将 θ 与 document/token-local 对象置于 D-plate。统一为正文的一套索引/长度符号（例如外层 `j=1:D`、内层 `n=1:L_j`，并同步 node/θ 下标和相邻一句正文）；若保留联合 `P(d)` 视角，明确其参数/条件口径 |

## 已查看的关键可视证据

- `final_full_page_200dpi.png`、`final_full_page_300dpi.png`
- `final_figure_crop_300dpi.png`、`final_standalone_crop_300dpi.png`、`final_grayscale_300dpi.png`
- `after_text_measurement_overlay_300dpi.png`
- `rois/critical_phi_inside_D_plate_original.png`、`..._A_mask.png`、`..._B_mask.png`、`..._overlay.png`：红色为 φ 文本、蓝色为外层 plate；证明的是错误的 plate 成员关系，不是像素重叠。
- `rois/critical_D_plate_label_clearance_*`：最近的 plate label/border 高风险对；raw overlap=0、clearance=13px。
- `rois/critical_theta_operator_*`：9.4pt 公式与 `=` 的 raw mask 证据。

## SA2 最小修复闭环

1. 先修数学结构：把全局 `φ_z=P(w|z)` 和其 parameter box 移到 `d=1:D` plate 外；让只有文档相关的 θ、以及当前文档内的 token 过程处于外 plate。确认 `d→z→w` 与 `w⊥d\mid z` 不变。
2. 统一正文和 plate 记号：图中 `N_d`/`d=1:D` 不得继续与正文 `L_j`/`d_j` 并存。选择一套并同步图源与直接相邻说明，保留概率归一化和条件关系。
3. 以重新布局而非整体缩放取得足够空间。把所有读者文字的有效字号提高到 ≥9.5pt，并特别对本轮失败的运算符/标点采取可实测的字形与字号方案；9.5pt 本身不是 raw H_ink 通过保证。
4. 从修改后的最终 PDF 新建证据，不复用本轮数字：原生 200/300dpi 整页、300dpi crop/standalone/gray、overlay、13 元素 source-font CSV、全部 glyph CSV、286 非豁免 pair CSV、critical ROI/masks，并由新的 SA1 再审。只有全部硬门 true 才可送 SA3。
