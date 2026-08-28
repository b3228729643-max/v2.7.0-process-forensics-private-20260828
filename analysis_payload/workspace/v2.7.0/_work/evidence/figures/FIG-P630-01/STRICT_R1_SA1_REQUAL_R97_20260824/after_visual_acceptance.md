# FIG-P630-01（图33.1）R97 独立 SA1 严格重新资格审查

## 结论

`SA1_FAIL_ROUTE_SA2`

三项 `BASE_MATH_OPERATOR` 字形违反不可四舍五入的 `H_INK_PX >= 22` 硬门。任何整体可读、几何或语义 PASS 均不能抵消。因此本轮不得进入 SA3。

## 审查身份与隔离

- reviewer：`FIG-P630-01-SA1-R97`，全新独立 SA1。
- 只读输入仅为强制主提示词、AGENTS、两份严格协议、当前直接正文、当前图源与 R97 官方 PDF；未读取、搜索、列举或继承任何既有 FIG-P630-01 evidence、旧 PASS、库存结论或其他代理人工判断。
- 唯一写入根：本目录 `STRICT_R1_SA1_REQUAL_R97_20260824`。
- 未修改图源、正文、公共样式、官方构建、中央状态或库存。

## 权威候选与定位

- 官方 PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf`
- SHA256：`062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`，813 页。
- aux label `fig:V5-C04-dependency-graph` 给出印刷页 665；PDF page labels 将 665 映射到物理页 678；直接正文、图题和当前源共同确认图 33.1。没有把 UID 当页码。
- 页面：`595.276001 x 841.890015 pt`；300dpi 原生整页 `2481 x 3508 px`；200dpi 整页 `1654 x 2339 px`。
- 严格 vector bbox：`[85.745438,329.370422,520.868591,535.742371] pt`。
- 300dpi 整数半开裁框：`[355,1370,2173,2235]`；严格图框 `1818 x 865 px`；pad 2px。
- standalone 为视觉交叉核对，尺寸 `1818 x 865 px`，不参与像素计数；所有计数只绑定官方 PDF 原生 300dpi 图框。

## 实际打开记录

- 当前 whole views：5/5（200dpi 整页、300dpi 图框、300dpi standalone、300dpi 灰度、300dpi 测量 overlay）。
- glyph contact sheets：13/13；逐格 102/102，详见 `glyph_manual_review.csv`。
- critical glyph：native 1x 6/6 与 8x 6/6，包含三张失败卡和三张临界通过卡。
- graphic/path contacts：21/21，详见 `graphic_manual_review.csv`。
- critical/contact pair cards：19/19，详见 `critical_pair_manual_review.csv`。
- 所有 8x 图均只用于 nearest-neighbour 人工复核；计数仍来自原生 1x mask。

## 对象与 pair 分母

- reader-visible glyph：102；visible foreground drawing/path：21；数学 rule path：0。
- 双向盘点确认数学符号均在 PDF text tracing 中；21 条 drawing/path 分别是 9 个节点/结论边框、5 个箭杆、5 个箭头、2 个 leader；没有未归属数学规则、文字或可见前景 path。
- 总对象 `N=123`；应有无序 pair `C(123,2)=7503`；实际 `7503`；漏 pair 0、重复 pair 0。
- 空 glyph mask 0；空 graphic mask 0；最终可见非法交叠 pair 0；`CLIP_PIXEL_COUNT=0`。
- 十对 source-semantic 边框—箭杆或箭杆—箭头 pre-occlusion 接触均逐对命名；另九对端点近邻逐卡核验。19 张卡的双方 mask 均完整纯净且 final-visible intersection 为 0，未使用类别式豁免。

## 几何门

- `OVERLAP_PIXEL_COUNT=0`：PASS。
- `CLIP_PIXEL_COUNT=0`：PASS；123 个 final-visible 对象均不触碰裁框边，最近 drawing/path 到图框边 1px；文字到图像边最小 19px，满足 6px 门。
- 独立文字—文字最小 vector bbox 净空 `116.24px >= 4px`：PASS。
- 文字/公式—线箭最小 raw-mask 净空 `18px >= 3px`：PASS。
- 节点文字/公式—自身最终可见边框最小净空 `12px >= 5px`：PASS。
- 文字—其他边框最小净空 `73.20px >= 3px`：PASS。
- 单 panel，无跨面板 8px 比较对象：N/A。
- 未见线穿字、文字挤框、裁切、反向遮挡或错误 z-order。

## 源字号、D/E 与视觉协调

- 普通节点、公式节点和支持注释均为 effective 9.6pt；强调结论 10.0pt；一般文字最小 9.6pt，均不低于 9.5pt。
- graphics scale 均 1.0；无 `resizebox`、`scalebox` 或 `transform shape` 累计缩放。
- 同角色源字号 max/min 均 1.0；强调/base 精确比 `10/9.6=1.0416666666666667`，位于允许区间。
- 同脚本同角色像素中位数：base-node CJK 33/33/33/33；formula CJK 33/33；formula x-height 20/20；formula natural-script 29/28.5，极值比 `1.0175438596491228 <= 1.08`；support CJK 33/33。均 PASS，未四舍五入掩盖失败。
- `U+1D43E MATHEMATICAL ITALIC CAPITAL K` 按 uppercase 正确分类，H=27px >=24；不误并入 x-height 组。
- `FONT_VISUAL_HARMONY_PASS=true`：9.6pt 节点文字与同页正文、图题、框线和节点容量协调，未显突兀、喧宾夺主或过密；10pt 加粗边界结论形成适度层级。此视觉 PASS 不抵消下述逐字形硬 FAIL。

## 低轮廓标点校准

- 候选数 0，N/A。102 个 codepoint 中没有句点、小数点、逗号、顿号、冒号、分号、省略点或其 CJK 变体。
- `U+22C5 ⋅` 是语义数学乘点，必须按 22px operator 门，不能借用低轮廓标点校准。

## 逐字形硬失败

1. `GLYPH-013`，父对象 `E002_CORE_CONDITIONAL`，`U+2212 −`，STIXTwoMath-Regular，bbox `[860,303,883,332]`，raw mask H=`3px`、area=`57px`，operator gate=`22px`：FAIL。
2. `GLYPH-022`，父对象 `E002_CORE_CONDITIONAL`，`U+22C5 ⋅`，STIXTwoMath-Regular，bbox `[876,334,889,375]`，raw mask H=`5px`、area=`25px`，operator gate=`22px`：FAIL。
3. `GLYPH-025`，父对象 `E002_CORE_CONDITIONAL`，`U+2212 −`，STIXTwoMath-Regular，bbox `[943,352,967,381]`，raw mask H=`3px`、area=`57px`，operator gate=`22px`：FAIL。

三张 mask 均非空、完整且纯净；失败来自实际 reader-visible ink 高度，不是污染、缺笔或映射错误。`−` 即使出现在自然下标排版中仍是语义 operator，协议禁止降格为 15px script 门。

## 唯一 mask 歧义闭合

GLYPH-025 与 GLYPH-026 的 PDF char bbox 在 crop x=966 边界重叠，形成 3 个候选 antialias 像素。逐像素 bbox、中心归一化距离、RGB 和候选 owner 均记录在 `glyph_ambiguity_resolution.csv`。实际打开 GLYPH-025/026 的 1x 与 8x 卡确认三个像素属于 `j` 左下 descender 边缘而不属于水平 minus；已唯一分配给 GLYPH-026。最终 102 个 mask 唯一、完整、纯净。

## 数学语义、连线和版式

- 条件式 `π_j(⋅ | x_{−j})`、单坐标核 `K_j` 及只更新 `x_j` 的标签归属正确；符号、括号、条件竖线与上下标映射闭合。
- 主链阅读方向为上排左到右、向下、下排右到左：联合目标/局部因子 → 满条件 → 单坐标核 → 扫描核 → 相关样本 → MCSE/ESS/轨迹诊断。五个箭头方向与端点正确。
- 正确性 leader 指向联合目标侧，混合效率 leader 指向扫描侧；正文明确主链箭头表示学习/计算依赖而非概率图生成时间方向，图文一致。
- 灰度中框、箭头、leader、文字和强调层级仍可辨；整体布局无拥挤、裁切或不自然空洞；页面融合与图题协调。

## Gate matrix

| Gate | 结论 |
|---|---|
| 官方候选身份/定位 | PASS |
| 四视图与测量 overlay | PASS |
| 源级一般字号 >=9.5pt | PASS |
| D/E 同类与角色比例 | PASS |
| 102/102 glyph 映射与唯一 mask | PASS |
| H_INK 逐字形 | **FAIL：3 项** |
| 低轮廓标点参照 | N/A（0 候选） |
| 21/21 drawing/path 双向盘点 | PASS |
| N=123 与 7503/7503 pair 闭包 | PASS |
| overlap/clearance/clip | PASS |
| 19/19 critical/contact cards | PASS |
| FONT_VISUAL_HARMONY | PASS |
| 数学语义/端点/箭向/标签归属 | PASS |
| 灰度/整体布局/页面融合 | PASS |
| 总结论 | **SA1_FAIL_ROUTE_SA2** |

PASS 项不能抵消任一 H_INK 硬失败。本结论只路由 SA2，不宣布最终关闭。
