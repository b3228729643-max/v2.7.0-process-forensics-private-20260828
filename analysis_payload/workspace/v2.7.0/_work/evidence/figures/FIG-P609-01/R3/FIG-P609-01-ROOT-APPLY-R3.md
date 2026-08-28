# FIG-P609-01｜根线程应用与局部验收（R3）

- FIGURE_ID: `FIG-P609-01`
- ROUND: `R3`
- ROOT_LOCAL_RESULT: `PASS_LOCAL`
- SPLIT_REQUIRED: `NO`
- BLOCKERS: `NONE`
- unresolved: `NONE`
- FINAL_STATUS: `PENDING_INDEPENDENT_SA1_AND_BLIND_SA3`

## 当前候选

- 图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_autocorrelation_ess.tex`
- 正文邻域：`src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C03.tex`
- standalone wrapper：`src/讲义源码/合并总册/v260_FIG-P609-01_standalone.tex`
- page wrapper：`src/讲义源码/合并总册/v260_FIG-P609-01_page.tex`
- 数值清单：`src/绘图源码/figure_numeric_manifest_v16.json` 中 `FIG-V5-C03-10`

## 数学与统计语义

当前图把经验 ACF 与同一预设窗口下的有限样本加权 ESS 统一为

$$
\widehat\tau_{K,n}=1+2\sum_{k=1}^{K}\left(1-\frac{k}{n}\right)\widehat\rho_k,
\qquad
\widehat N_{\mathrm{eff}}=\frac{n}{\widehat\tau_{K,n}},
\qquad \widehat\tau_{K,n}>0.
$$

图内明确规定 $K=6<n$，仅纳入 $1\le k\le K$；省略号对应的后续滞后未绘出且未纳入。由于没有固定样本量 $n$，图中没有伪造一个数值 ESS，并保留“有限轨迹诊断，不是收敛证明”的边界。

对源内固定坐标 $(\widehat\rho_1,\ldots,\widehat\rho_6)=(0.86,0.74,0.64,0.55,0.47,0.40)$ 的根线程独立复算为：

- $\sum_{k=1}^{6}\widehat\rho_k=3.66$；
- $\sum_{k=1}^{6}k\widehat\rho_k=11.21$；
- $\widehat\tau_{6,n}=8.32-22.42/n$；
- 最小允许整数 $n=7$ 时，$\widehat\tau_{6,7}=5.1171428571$，$\widehat N_{\mathrm{eff}}=1.3679508654$。

复算结果与 numeric manifest 精确一致。

## 构建、身份与机器核验

- LuaLaTeX/TeX Live 2026 局部构建成功：`p609_root_r3_standalone.pdf` 为 44,980 字节，`p609_root_r3_page.pdf` 为 63,036 字节；均为 1 页 A4、PDF 1.7、未加密。
- 两份 PDF 元数据均标识“统计学习方法讲义 v2.7.0”；全部列出字体均嵌入、子集化且有 Unicode 映射。
- 两份最终日志的 fatal、emergency、undefined/multiply-defined、overfull/underfull、missing character 等硬诊断命中均为 0。
- 两份 FLS 各精确记录 1 次正式 wrapper、`release_version.tex` 和当前 P609 图源。
- page AUX/LoF/label 为图 32.9、印刷页 644、`figure.caption.1`。局部 page PDF 的物理页为 1，不把印刷页码 644 误称为局部物理页。
- PDF 文本顺序为“首引图 32.9 → 图 → 单结论题注 → 读图顺序”；交叉引用已经解析。
- `figure_sources.json` 与 numeric manifest 均可解析；目标顶层图记录各唯一。中央 CSV 为 99 行 × 19 列、99 个唯一 canonical UID，P609 唯一。
- 图源中只有一组七点坐标，无旧 K=8 或双序列残留；普通文字 9.6pt、轴标签 9.8pt、标题 10.4pt，未使用整体缩放。

## 四张 PNG 亲看

- `p609_root_r3_standalone_300dpi.png`：独立图结构完整；七根 stem、K=6 虚线、箭头和公式卡无重叠、穿字、裁切或溢出。
- `p609_root_r3_full_page_200dpi.png`：页头、首引、图 32.9、短题注和导读在印刷页 644 上连续，局部 wrapper 结束后的页底留白不构成浮动体缺陷。
- `p609_root_r3_page_300dpi.png`：公式上下标、$1-k/n$、$K=6<n$、正分母与边界提示均清晰。
- `p609_root_r3_gray_page_300dpi.png`：stem 线段与圆点、窗口浅底与虚线、直接文字和方向箭头在灰度下仍提供冗余编码。

该图只有一个“ACF窗口 → 有限样本加权 ESS → 诊断边界”的单一阅读任务；两面板必须并读，拆图会削弱对象关系，故 `SPLIT_REQUIRED=NO`。

## 根线程结论

ROOT_LOCAL_RESULT: **PASS_LOCAL**  
SPLIT_REQUIRED: **NO**  
BLOCKERS: **NONE**  
NEXT_ACTION: **等待全新 SA1 与隔离 SA3 只读独立复审；二者均通过后再冻结候选。**
