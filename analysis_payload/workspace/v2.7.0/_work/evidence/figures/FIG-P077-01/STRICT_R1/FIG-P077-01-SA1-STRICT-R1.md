# FIG-P077-01｜独立 SA1 严格复核（新 Goal R1）

- RESULT: **FAIL**
- ROUTE: `SA2_REQUIRED`
- OFFICIAL_PAGE: R89 物理页 79、图 5.1
- SOURCE_WRITES: `NONE`

## 确定性硬失败

- x/y 刻度 8.8pt，轴标题 9.4pt，两个曲线直标及“两条曲线：面积=1”均为 9.2pt；graphics scale=1，无整体缩放。全部低于一般可见文字 9.5pt。
- 官方 PDF 物理页 79 已直接渲染为 `2481×3508 @ 300dpi`、未 resize。抽样数字、CJK、公式与脚本像素下限本身通过，但没有可签发的逐 ELEMENT_ID 正式全量对象分割、重叠、裁切、净空和角色比例证据；UNKNOWN 按 FAIL。
- 初步 1:1 掩膜未发现确定性碰撞；当前最紧候选为面积标注到 brace 约 6px、面积标注到底部刻度约 15px。但这不能替代正式全量 `OVERLAP_PIXEL_COUNT=0` 与 `CLIP_PIXEL_COUNT=0`。

## 数学与页面

两条密度为 `N(0,1)` 与 `N(0,2^2)`，面积均为 1；题注、正文引用和灰度线型语义正确。页面图体边缘、前后正文与题注的观测净空正常。

## 必须修复

把 tick、axis label、曲线直标和面积注释统一提高到至少 9.6pt，不整体缩放；面积注释可把 `below=3pt` 调为 `below=4pt` 留安全余量。随后重新编译并生成全量字号、300dpi 像素、同类/角色比例、对象掩膜、重叠/裁切/净空和四视图证据，再交新的独立 SA1/SA3。

## 门矩阵

| 门 | 结果 |
|---|---|
| SOURCE_FONT | FAIL |
| PIXEL_HEIGHT | 抽样通过、全量证据缺失 → FAIL |
| SAME_CLASS / ROLE | UNKNOWN → FAIL |
| OVERLAP / CLIP / CLEARANCE | UNKNOWN → FAIL |
| MATH / TEXT | PASS |
| GRAYSCALE / PAGE | 观测正常，但正式证据不足 → FAIL |
