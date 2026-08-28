# FIG-P578-01｜专属 SA2 严格返修（R3 candidate3）

- RESULT: **PARTIAL / SOURCE_REPAIR_COMPLETE**
- FINAL_PASS_CLAIMED: `NO`
- NEXT_GATE: `ROOT_FULL_EVIDENCE`
- SOURCE_CHANGED: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex`
- OTHER_FILES_CHANGED_BY_SA2: `NONE`

## 定向修复

- 新增局部 `\slfigRejMath`（10.7pt/12.4pt），仅提升短变量、运算符与公式基式；长 precheck 与 `\mathtt` 状态码保持 9.6pt，避免换行或越框。
- failure 节点 `inner ysep` 从 2pt 改为 3.3pt。
- 新增右侧标签走廊样式：`xshift=8mm`、`inner ysep=.3pt`；下接矩形的三处另加 `yshift=3.5pt`。
- 七个原纵向标签全部移到右侧走廊，重排中轴和分支节点坐标；`merge` 改到 `(0,-11.20)`，回路仍返回 `goal.west`。
- UID、figure/caption/label/alt、21 节点、16 分支标签、回路注记和状态语义未改。

## 构建

- page 与 standalone 均 LuaLaTeX exit 0、A4 单页。
- 两份日志的 Overfull/Underfull/LaTeX Error/Package Error 等硬模式均为 0。
- page、standalone、gray 均直接生成 `2481×3508 @ 300dpi`，未 resize。

## 原生 300 dpi 定向复测

- CJK 最小实墨 34px；题注数字 `31.5` 为 28px。
- 10.7pt 短基准数学最小有意义 run 为 23px（`m=` / `a=` / 独立 `m,a`）。
- precheck 行级 run：含 `∈` 32px、含 `≤` 31px、含 `⇒` 35px、含 `ρ` 39px。
- `supp` 与完整状态码的独立 H_ink 尚未逐子串落盘，是剩余证据缺口。

## 净空与重叠

- 四个原失败组件净空：`goal→budgetcheck=16.94px`、`countproposal→uniform=15.81px`、`uniform→evaluate=23.94px`、`numericok→envelopeok=15.44px`。
- 全部中轴相邻组件最小 11.60px（`evaluate→numericok`）。
- 21 个节点文字—自身边框 overlap=0；最小内边距 8.00px。
- 七个标签白底—节点边框交集 0，最小正间距 3.00px；标签字形—非关联节点边框最小 9.00px；标签字形—意图中轴路径最小 100.40px；文字行 bbox 间最小 6.81px。
- 图体—题注净空 14.79px；图体到最近页面边缘约 454px；局部裁切 0。

## 为什么仍是 PARTIAL

SA2 没有完成全图所有 `TEXT/FORMULA/LINE_ARROW/NODE_BORDER` 组合的正式全量掩膜计数，灰度图也未做逐对象独立验收；因此不能把修改范围内的 overlap=0 外推为最终全图 `OVERLAP_PIXEL_COUNT=0`。根线程还须补齐全部元素 H_ink、同类/角色比例、全图 overlap/clip/clearance CSV、叠加图和四视图结论，之后才能启动新的独立 SA1。

## 已固化候选

- `candidate_page.pdf`, `candidate_page.log`
- `candidate_standalone.pdf`, `candidate_standalone.log`
- `full_page_200dpi.png`, `full_page_300dpi.png`
- `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`
- `crop_top_300.png`, `crop_mid_300.png`, `crop_bottom_300.png`
