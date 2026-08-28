# FIG-P602-01 — SA2 严格定向修复 R2

RESULT: FIXED_PENDING_ROOT_BUILD

FIGURE_ID: FIG-P602-01

SPLIT_REQUIRED: NO

## assigned_scope

- 固定角色：逐图 SA2，负责修复新 Goal §9.2.1 与 §9.4 下 SA1-R1 指出的定向失败。
- 唯一获准业务源：`fig_v5_c03_mh_accept_reject.tex`。
- 唯一获准证据文件：本报告。
- 未修改章节、wrapper、公共宏、清单、状态、构建入口或其他图；未构建，也未生成或伪造像素 PASS。

## reproduced_failures

1. 源级公式角色比原为 `11.8pt / 9.6pt = 1.2292`，超过公式块对 BASE 的硬上限 `1.18`。
2. 接受率标题与公式之间原使用 `\\[-.1ex]`；SA1 在原始 300 dpi 候选中测得有效前景净空仅 `3px`，低于文字—文字/公式 `4px` 下限。
3. SA1 所见测试页存在约 `85.5mm` 连续页尾空白。该项需要连续章节或整书页流复核，超出本次白名单。

## completed

### 逐行修改

- 图源第 19 行：将标题后的 `\\[-.1ex]` 改为 `\\[.6ex]`。这删除负间距并净增加 `0.7ex`；按 9.6pt 中文基准估算约增加 `3.0--3.4pt`，即约 `12--14px@300dpi`。相对于 SA1 的旧 `3px`，新候选预期标题—公式有效前景净空约为 `15--17px`，为 `>=4px` 留出安全余量。该数字是源级预测，必须由根线程对新 300 dpi 原图逐像素复测，不能当作 PASS。
- 图源第 20 行：将接受率公式 `\fontsize{11.8pt}{14.2pt}` 改为 `\fontsize{11.2pt}{13.6pt}`。无整体缩放，因此公式基准 `effective_pt=11.2pt`；相对普通文字 BASE `9.6pt` 的源级角色比为 `11.2/9.6=1.1667`，落在 `[1.00,1.18]`，且显著高于 `9.5pt` 下限。
- 接受率表达式、`g(x,y)>0` 条件、提议/判定/接受/拒绝/自环结构、节点坐标、箭头、题注与 label 均未改变。

### 预期像素影响（非验收结论）

- 以 SA1 旧候选大公式 `alpha` 约 `46px`、普通 BASE `alpha` 约 `38px` 为参照，线性估算新公式同字形约为 `46*(11.2/11.8)=43.7px`，相对 BASE 约 `1.15`；预期不再突兀且仍远高于基准数学主体 `22px` 下限。
- 旧候选自然上下标/脚本约 `20--29px`；字号仅降低约 `5.1%`，源级估算仍高于自然脚本 `15px` 下限。根线程仍须逐 ELEMENT_ID 实测，不能用该估算替代 `after_pixel_measurements.csv`。
- 正行距会使接受率框的自然高度可能略增；其与上下节点、箭头及边标签是否仍满足零重叠与 `>=3px` 净空，必须在新候选中重新测量。

## decisions

- 采用 `11.2pt` 而非上限附近的 `11.3pt`，给字体度量与实际墨迹角色比保留余量，同时保持公式比 9.6pt BASE 略强调。
- 采用正的 `.6ex` 行间安全距，不用白色遮挡块、halo、整体缩小或改变数学表达式规避重叠。
- 不拆图：当前单向 MH 一步流程只有一个判定和两个终点，失败来自局部字号/行距，不是结构容量不足。

## files_changed

1. `v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mh_accept_reject.tex`
2. `v2.7.0/_work/evidence/figures/FIG-P602-01/STRICT_R2/FIG-P602-01-SA2-STRICT-R2.md`

## build_and_evidence

- STANDALONE_BUILD: `PENDING_ROOT_BUILD`（按本次任务要求，SA2 不构建）。
- PAGE_BUILD: `PENDING_ROOT_BUILD`。
- NEW_EVIDENCE: 仅本修复报告；规定的四视图、三份 CSV、测量 overlay 与 `after_visual_acceptance.md` 均须由根线程从新最终候选 PDF 生成。
- FONT_AUDIT_RESULT: 源级公式角色比预期已修复；全量 ELEMENT_ID 审计待根线程。
- PIXEL_MEASUREMENT_RESULT: `UNKNOWN_PENDING_ROOT_BUILD`。
- OVERLAP_PIXEL_COUNT: `UNKNOWN_PENDING_ROOT_BUILD`，不得记为 0。
- CLIP_PIXEL_COUNT: `UNKNOWN_PENDING_ROOT_BUILD`，不得记为 0。
- MIN_TEXT_CLEARANCE_PX: 旧值 `3px`；新值仅预测 `15--17px`，待原始 300 dpi 实测。

## unresolved

### 页面整合

- SA1 的大空白来自 `讲义源码/合并总册/v260_FIG-P602-01_page.tex` 这一单图测试 wrapper；该文件在图后读图句后立即 `\end{document}`，所以它不能证明连续书稿在图后同样没有后续内容。
- 根线程应先从连续 `V5-C03.tex` 或最终 `main_full.tex` 构建定位真实图页；章节权威上下文在 `V5-C03.tex:298--303`，图后紧接读图句与“MH核的可逆性”定理，必须用该连续页流重新判断 `PAGE_INTEGRATION_PASS`。
- 若连续最终页仍出现约 `85.5mm` 级异常空白，章节单写者应定向检查 `V5-C03.tex:300` 的 `\FloatBarrier` 与本图 `[htbp]` 浮动位置，调整浮动屏障/分页或相邻段落布局后重建；本 SA2 不越权修改章节或 wrapper。

### 严格视觉证据

- 新候选仍必须从 PDF 直接渲染 `full_page_200dpi`、`figure_crop_300dpi`、`standalone_300dpi`、`grayscale_300dpi`，300 dpi 图不得 resize。
- 必须全量生成并复核 `after_font_audit.csv`、`after_pixel_measurements.csv`、`after_overlap_report.csv`、`after_text_measurement_overlay_300dpi.png`、`after_visual_acceptance.md`；任何未知、缺项、非法重叠像素 `>=1` 或裁切像素 `>=1` 均为 FAIL。

## validation

- 源级定向检查：普通文字仍为 9.6pt；公式为 11.2pt；没有 `resizebox`、`scalebox`、`adjustbox`、`transform shape` 或整体 `scale`；公式角色比从 `1.2292` 降至 `1.1667`。
- 数学与文本一致性：未改 `alpha(x,y)` 的定义、正流条件、随机判定或状态更新语义。
- 像素/构建/页面整合：未执行，准确保持为待根线程验证。

## next_action

根线程以新 jobname 独立构建 standalone 与连续书稿页，从最终候选 PDF 直接生成规定视图和五项严格证据；逐元素复测字号、像素高度、角色比、标题—公式净空、全部必查重叠组合及页面整合。全部硬门有证据后再创建全新独立 SA1；SA1 PASS 后才进入 SA3。
