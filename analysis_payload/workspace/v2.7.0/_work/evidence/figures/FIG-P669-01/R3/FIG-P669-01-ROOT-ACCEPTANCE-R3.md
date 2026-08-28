# FIG-P669-01｜根线程最终验收（R3）

- FIGURE_ID: `FIG-P669-01`
- ROUND: `R3`
- ROOT_ACCEPTANCE: `PASS`
- OVERALL: `PASS`
- SPLIT_REQUIRED: `NO`
- BLOCKERS: `NONE`
- unresolved: `NONE`

## 验收依据

根线程已直接核验当前图源、V5-C05 正文邻域、page/standalone wrapper、source/numeric JSON、中央 CSV 唯一行以及 R3 PDF/PNG/LOG/FLS/AUX，并完整回读三份独立证据：

1. `FIG-P669-01-ROOT-APPLY-R3.md`：根线程局部构建与实看为 `PASS_LOCAL / NO SPLIT`；
2. `FIG-P669-01-SA1-R3.md`：全新 SA1 独立复审为 `PASS / NO SPLIT / NONE`；
3. `FIG-P669-01-SA3-R3.md`：隔离历史结论的 SA3 盲审为 `PASS / NO SPLIT / NONE`。

三条证据链结论一致，未用旧状态或 P668 的证据替代本图的独立检查。

## 根线程复核结论

- 数学与几何：固定 $m=(.5,.3,.2)$，线性轴上的 $\alpha_0=3/10/30$ 对应三组参数正确；投影协方差分子为 `[[3.04,.277128129211],[.277128129211,1.92]]`，三组 Cholesky 最大重构残差不超过 `4.486e-13`。
- 椭圆语义：三条 0.8σ 椭圆共心、面积比精确为 `1:4/11:4/31`；最大椭圆的三个概率坐标下界为 `.30/.116696972202/.04`，支持域越界数为 0。图和题注明确它不是密度等高线或置信域。
- 教学闭环：段题、首次引用、图、`\FloatBarrier`、题注与专属读图句一致；左轴点形/线型与右侧椭圆边界有实际一一连接。
- 字号与视觉：默认 9.6pt、标题 10.1pt，无整体缩放；彩色、灰度和 standalone 均无碰撞、裁切或路径穿字，灰度下点形、线型和轴位置仍可独立辨认。
- 技术身份：standalone/page 分别为 53,736/71,485 bytes、A4 单页；AUX 为图 34.9、页 666；两日志硬诊断 0，FLS 指向当前 wrapper/图源，字体全部嵌入、子集化并为 Unicode。
- 拆分判断：参数轴与协方差椭圆构成一个连续因果链，拆开会破坏一对一连接，不拆图。

## 最终裁决

`FIG-P669-01` 已满足专属 SA2、根线程 R3、全新 SA1 与隔离 SA3 的完整闭环，接受当前候选并关闭本图。

ROOT_ACCEPTANCE: **PASS**  
SPLIT_REQUIRED: **NO**  
BLOCKERS: **NONE**  
NEXT_ACTION: **中央清单保持 `RESOLVED_EVIDENCE_CLEAR`；后续不再为本图重复构建。**
