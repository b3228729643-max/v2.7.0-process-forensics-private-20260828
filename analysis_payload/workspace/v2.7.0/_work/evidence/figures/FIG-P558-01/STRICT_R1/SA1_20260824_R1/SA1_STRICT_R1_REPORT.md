# FIG-P558-01｜独立 SA1 严格视觉与数学首审（SA1_20260824_R1）

## 1. 范围、冻结输入与定位

- 冻结输入：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`；直接定位为 PDF 物理页 **605**（PyMuPDF index 604）、印刷页 **592**，题注为“图30.7 三节点路径的简单游走与惰性游走：加入自环保持平稳分布并消除周期振荡”。
- 只读取当前图源 `绘图源码/第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_random_walk.tex`、相邻正文 `讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C01.tex` 和公共样式 `common/statlearnbook.sty`；未读取本图任何旧 SA/根结论、截图或测量。
- 300 dpi 测量来自一次性直接渲染整页 `2481×3508` 固定网格；所有局部图均为该网格的像素切片、未 resize。

## 2. 源级有效字号

- 源级对象 43 个；`effective_pt<9.5` 的读者对象 **40** 个。具体为状态标签 9.4pt、边/自环概率 8.8pt、刻度 8.6pt、轴标题/公式基准 9.2pt、注释 8.8pt、摘要 9.2pt；详见 `after_font_audit.csv`。
- 同面板同角色源级字号一致性与跨面板同角色比均已记录；它们不能抵消 9.5pt 硬下限失败。
- `SOURCE_FONT_PASS = false`。

## 3. 原生 300dpi 逐字形测量

- 已枚举 171 个 PDF 字形/字面运算符/标点；每一项有 PDF bbox、无膨胀 raw mask、H_ink 与类别阈值，见 `after_pixel_measurements.csv` 与 `masks/glyph_raw/`。
- `PIXEL_HEIGHT_PASS = false`；逐字形高度失败 **10** 个。父公式或中文行高未替代任何数字、`/`、`=`、逗号/句点等子串。
- 图中文字测量框在 `after_text_measurement_overlay_300dpi.png`；自然题注作为单一父段 `CAPTION`，未人为拆行为文字—文字碰撞对象。

## 4. 同类比例、角色层级与字体协调

- 每个字形仍单独做 C 节 H_ink 门；D/E 的比例单位为“同一语义父对象 × 同一 script class”的实际 raw mask H_ink，因此不会把自然题注/标题拆成单字制造伪比例，也未按 exact glyph 分组或跨脚本混比。跨面板同角色同脚本的实际中位数另列，见 `same_class_ratio_audit.csv`/`role_ratio_audit.csv`。
- `SAME_CLASS_RATIO_PASS = false`；失败行 **33**。`ROLE_RATIO_PASS = false`；失败行 **4**。无可比 script 的角色层级明示 `N/A`，未伪造跨脚本比例。
- `FONT_VISUAL_HARMONY_PASS = false`：刻度、边标签与注释的 8.6–8.8pt 明显低于此图其他文本的教学阅读基准；本轮未以“可读”或缩小建议覆盖硬门。

## 5. 零重叠、净空、halo 与裁切

- 已枚举 **76** 条当前图非文字矢量路径，其中 **13** 条是明确白底 halo，另 **63** 条为曲线、标记、节点边框、箭头、箭头头、轴或摘要框；全部独立 raw mask 与最终可见 mask 位于 `masks/vector_raw/`、`masks/vector_visible_raw/`、`masks/halo_raw/`。
- `VECTOR_PAIR_TRACEABILITY_PASS = true`：`vector_pair_traceability.json` 已逐行核对 `VECTOR_ID/DRAWING_INDEX/CATEGORY/OWNER/raw/final-visible mask` 与内存 components，并核对所有 pair 的 `B_CATEGORY/THRESHOLD_PX`；halo=13、非halo=63、unknown=0。
- 全对数 **3612**；最终非法重叠为 **4 对 / 693 像素**，`CLIP_PIXEL_COUNT = 0`；另有 **3 对**虽经 halo 已无最终交集但仅 1px 净空。最小实测 pair 净空 **0.0 px**。halo 前遮挡量单独列 `PRE_OCCLUSION_OVERLAP_PX`，不混入最终非法重叠。
- `OVERLAP_PASS = false`；`CLIP_PASS = true`；`CLEARANCE_PASS = false`。所有失败/临界或 halo 接触 pair 均有原图、双方 raw mask、交集、overlay 和 8× 最近邻版本（文件索引：`critical_pair_manifest.md`）：
- `TV__SIMPLE_P23__ARROW_10` — FAIL_CLEARANCE; final overlap=0; pre-occlusion=1; clearance=1.0 px; 8× `critical_pairs/TV__SIMPLE_P23__ARROW_10_8xNN.png`
- `TV__SIMPLE_P32__ARROW_13` — PASS; final overlap=0; pre-occlusion=0; clearance=5.0 px; 8× `critical_pairs/TV__SIMPLE_P32__ARROW_13_8xNN.png`
- `TV__LAZY_P12__ARROW_19` — FAIL_CLEARANCE; final overlap=0; pre-occlusion=2; clearance=1.0 px; 8× `critical_pairs/TV__LAZY_P12__ARROW_19_8xNN.png`
- `TV__LAZY_P23__ARROW_25` — FAIL_CLEARANCE; final overlap=0; pre-occlusion=1; clearance=1.0 px; 8× `critical_pairs/TV__LAZY_P23__ARROW_25_8xNN.png`
- `TV__LAZY_LOOP_2__ARROW_34` — PASS_HALO_COVERED; final overlap=0; pre-occlusion=37; clearance=7.81 px; 8× `critical_pairs/TV__LAZY_LOOP_2__ARROW_34_8xNN.png`
- `TT__PLOT_SIMPLE_YTICK_0_25__PLOT_SIMPLE_YTICK_0_5` — FAIL_OVERLAP; final overlap=181; pre-occlusion=0; clearance=0.0 px; 8× `critical_pairs/TT__PLOT_SIMPLE_YTICK_0_25__PLOT_SIMPLE_YTICK_0_5_8xNN.png`
- `TT__PLOT_SIMPLE_YTICK_0_5__PLOT_SIMPLE_YTICK_0_75` — FAIL_OVERLAP; final overlap=165; pre-occlusion=0; clearance=0.0 px; 8× `critical_pairs/TT__PLOT_SIMPLE_YTICK_0_5__PLOT_SIMPLE_YTICK_0_75_8xNN.png`
- `TT__PLOT_LAZY_YTICK_0_25__PLOT_LAZY_YTICK_0_5` — FAIL_OVERLAP; final overlap=182; pre-occlusion=0; clearance=0.0 px; 8× `critical_pairs/TT__PLOT_LAZY_YTICK_0_25__PLOT_LAZY_YTICK_0_5_8xNN.png`
- `TT__PLOT_LAZY_YTICK_0_5__PLOT_LAZY_YTICK_0_75` — FAIL_OVERLAP; final overlap=165; pre-occlusion=0; clearance=0.0 px; 8× `critical_pairs/TT__PLOT_LAZY_YTICK_0_5__PLOT_LAZY_YTICK_0_75_8xNN.png`

## 6. 数学、图文与阅读语义

- 上部 simple 图的边概率是三节点路径随机游走；lazy 图等于 `A_L=1/2(I+A)`，两者的 `π=(1/4,1/2,1/4)` 均为平稳分布，simple 周期 2、lazy 周期 1，和相邻正文第30章相符。
- 但右下曲线与右上惰性链不相容：对任意分布 `mu`，`(mu A_L)_2 = 1/2`，故从 t=1 起 `P(X_t=2)` 必恒为 0.5；图中 t=1 标为 0.375，继而画出阻尼振荡。初始分布也未声明。该量化数据/图内命题错误详见 `math_text_semantics_audit.json`。
- `MATH_SEMANTICS_PASS = false`；`TEXT_CONSISTENCY_PASS = false`。阅读顺序（上：链；下：曲线；末：摘要/题注）本身清晰，但不能修复上述数学矛盾。

## 7. 四视图、灰度与页面融合

- 已核看 `full_page_200dpi.png`、`full_page_300dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`。上下结构和曲线/虚线/点型在灰度中仍可分辨；页面嵌入与题注自然。
- `GRAYSCALE_PASS = true`，`READING_ORDER_PASS = true`，`PAGE_INTEGRATION_PASS = true`。它们不覆盖字号与数学硬失败。

## 8. 结论与路由

```
RESULT: FAIL
FIGURE_ID: FIG-P558-01
SOURCE_FONT_PASS: false
PIXEL_HEIGHT_PASS: false
SAME_CLASS_RATIO_PASS: false
ROLE_RATIO_PASS: false
FONT_VISUAL_HARMONY_PASS: false
OVERLAP_PIXEL_COUNT: 693
OVERLAP_FAIL_PAIR_COUNT: 4
CLIP_PIXEL_COUNT: 0
VECTOR_PAIR_TRACEABILITY_PASS: true
MATH_SEMANTICS_PASS: false
TEXT_CONSISTENCY_PASS: false
EVIDENCE_INTEGRITY_PASS: true
NEXT_ROLE: SA2
```

SA2 应先修正惰性链曲线（或改变所画链/明确初始条件使数据可由转移矩阵推得），再将所有普通可见文字提高至至少 9.5pt，同时重新安排以通过逐字形、比例和净空门；不得仅整体缩放。
