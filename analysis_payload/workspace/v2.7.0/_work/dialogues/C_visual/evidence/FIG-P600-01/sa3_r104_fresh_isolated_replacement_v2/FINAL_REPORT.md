# FIG-P600-01 / R104 / SA3 replacement v2 独立终审报告

## 1. 结论

`RESULT = C_LOCAL_PASS_ONLY`

本结论只表示本 SA3 replacement v2 隔离审查包在 R104 官方候选上的本地硬门通过，不表示全局 PASS、不更新中央 state/inventory，也不覆盖根线程或其他角色的结论。若主线需要修改，处置权仍归 source-writer；本实例 `source-writer=NONE`，未修改任何 TeX、正文、PDF 或构建入口。

## 2. 实例与候选身份

- HANDOFF_ID：`C-FIG-P600-01-R104-SA3-FRESH-ISOLATED-REPLACEMENT-V2`
- UID：`FIG-P600-01`
- 官方候选：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`
- 身份核验：817 页；A4 `595.276 × 841.890 pt`；4,967,222 bytes；SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 独立定位：物理页 651；印刷页 638；图 32.4；未继承旧页码、旧分母或旧结论。
- 唯一图源：`fig_v5_c03_mh_balance_flux.tex`，只读。
- 必要正文一致性核对：`V5-C03.tex` 第 217–223 行语境；正文明确说明该图分开绘制双向提议流与截平后的成对接受流。
- 两个先前中断实例根未读取、未列举内容、未复制、未哈希、未续写。未读取任何旧 P600 证据、中央报告/状态/路由、其他 UID 证据或其他 agent 输出。

## 3. 原生渲染身份

所有视图均由同一官方 PDF 的物理页 651 只读派生，未 resize；8× 图只使用 nearest-neighbour 目视放大，计数始终回到 300 dpi 1× 网格。

| 视图 | 原生尺寸 | 说明 |
|---|---:|---|
| `full_page_300dpi.png` | 2481 × 3508 px | Poppler 300 dpi 整页 |
| `full_page_200dpi.png` | 1654 × 2339 px | Poppler 200 dpi 页面融合 |
| `figure_crop_300dpi.png` | 2000 × 888 px | 整页像素坐标 `[217,1867,2000,888]`，含图体与题注 |
| `standalone_300dpi.png` | 1435 × 740 px | 整页像素坐标 `[500,1875,1435,740]`，图体独立视图 |
| `grayscale_300dpi.png` | 2000 × 888 px | 同 figure crop 的原生灰度视图 |
| `machine_native_full_page_300dpi.png` | 2481 × 3508 px | PyMuPDF 机器掩膜对齐网格 |

## 4. 对象、绘制与全 pair 分母

- 文字/公式语义父对象：11。
- 图形对象：12。
- 总对象：`N=23`。
- 全部无序对象对：`C(23,2)=253`；`all_pairs_machine.csv` 与 `manual_pair_review.csv` 均恰好覆盖 253 个唯一 `PAIR_ID`。
- PDF 前景绘制记录：18；全部映射到 12 个图形父对象，并在 `drawing_map_machine.csv` / `manual_drawing_review.csv` 闭合。
- 数学规则对象：0。源中不存在 overline/underline/重音/根号横线/分数线/cancel 等独立公式规则；物理页图体的 18 条可见绘制记录均为节点/框/连线/箭头，不存在未归属数学规则路径。
- 每个对象均有安全普通文件名、非空 mask、bbox、面积和人工映射行；无冒号文件名、无 ADS 路径。

## 5. 字形与字体裁决

- 可见字形：197；非空 raw mask：197；人工行：197；安全文件名映射：197。
- Contact sheets：17；每格包含 `ORIGINAL 1× / TARGET OVERLAY 1× / MASK ONLY 1× / exact 8× nearest`，并另存 197 个逐字形 exact 8× 文件。
- 人工逐格结果：197/197 original-match、overlay-complete、mask-only-pure 均为 true；missing-stroke=0；foreign-pixel=0；未见 tofu、错 codepoint、数学语义错字形或缺笔。
- 旧协议像素分类：151 项达到旧阈值；30 项低于旧阈值；16 项为低轮廓标点需校准。R168 明确把微比例/metadata/taxonomy/1–2 px 等降为 advisory；本轮只在 tofu/错字形或 codepoint/数学语义、实际不可读、明显严重字号失衡、真实裁切/非法重叠时判字体硬 FAIL。上述 46 项均已在 1×/8× 实际打开，轮廓完整、可读且语义正确，因此只登记 advisory，不构成 R168 字体硬 FAIL。
- 源级实际值：图内基准 9.2 pt；次级标题 8.6 pt；无 resizebox/scalebox/transform shape。相对旧 9.5 pt 门为 advisory；在 full-page/figure/standalone/grayscale 四视图中未出现实际不可读或严重失衡。
- 角色同侪：proposal A/B 中位数比 1.000；双 accepted-flow 行 1.055；结论两行 1.000；均协调。状态 `x/y` 的 raw 高度差来自 x-height 与 y descender，源字号同为 9.2 pt，非字号失配。
- `FONT_VISUAL_HARMONY_PASS = true`（R168 硬门）。

## 6. 重叠、净空与裁切

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 136`：全部来自 13 个箭头—语义端口/节点边框的设计性连接。
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`。
- `OVERLAP_PIXEL_COUNT = 0`：人工确认的真实非法重叠为零。
- `CLIP_PIXEL_COUNT = 0`：23/23 对象 outside=0、edge-touch=0。
- 独立文字—文字最小净空：8 px（门值 4 px）。
- 文字/公式—图形最小净空：23 px（门值 3 px）。
- 节点内部文字—自身边框最小净空：9 px（门值 5 px）。
- 独立图形—图形最小净空：20 px；设计连接另行逐对白名单，不计非法重叠。
- 15 个机器 critical pair 均已打开 raw/A/B/intersection/1×/8×；13 项是设计连接，另两项分别为 9 px 节点文字边框净空和 8 px 两公式父对象净空。

## 7. 几何、关系、数学语义与正文一致性

- 几何：左右状态、左右 proposal、中央 `min(a,b)`、双主流、四 proposal 流和结论卡片的层次、对称与阅读路径清楚。
- 关系：双主流方向分别为 `x→y` 和 `y→x`；proposal 流分别由状态进入 `a/b`，再进入中央截平框；箭头端口无歧义。
- 数学：`a=π(x)q(x,y)`、`b=π(y)q(y,x)`；两个 accepted-flow 等式都等于 `min(a,b)`；“细致平衡充分推出 π 平稳但非必要”表述正确。
- 内容/题注：图体、题注和正文语境一致；没有把细致平衡误写成平稳性的必要条件。
- 灰度：颜色编码在灰度下仍有可辨的线宽/明度层次，所有文字和箭头可读。
- 页面融合：图号、题注、前后正文和页面留白自然，无真实裁切、非法重叠或明显严重字号失衡。

## 8. 硬门矩阵

| 硬门 | 结果 |
|---|---|
| OFFICIAL_CANDIDATE_IDENTITY | PASS |
| NATIVE_RENDER_IDENTITY | PASS |
| OBJECT_AND_DRAWING_COVERAGE | PASS |
| ALL_C_N_2_PAIR_COVERAGE | PASS |
| GLYPH_MAPPING_AND_PURITY | PASS |
| R168_FONT_HARD_GATE | PASS |
| GEOMETRY_AND_RELATION | PASS |
| MATH_SEMANTICS | PASS |
| CONTENT_AND_CHAPTER_CONSISTENCY | PASS |
| ILLEGAL_OVERLAP | PASS (`0 px`) |
| CLIP | PASS (`0 px`) |
| FOUR_VIEW_RENDER_AND_HARMONY | PASS |
| GRAYSCALE | PASS |
| EVIDENCE_INTEGRITY | PASS（28/28 machine checks，failed=0） |

## 9. 边界与处置

- TeX/LuaLaTeX/latexmk/texlua：未使用。
- 源码、正文、PDF、main：只读。
- source-writer：`NONE`。
- 中央 state/inventory：未写入。
- 结论仅为 `C_LOCAL_PASS_ONLY`；不宣称 global PASS。
