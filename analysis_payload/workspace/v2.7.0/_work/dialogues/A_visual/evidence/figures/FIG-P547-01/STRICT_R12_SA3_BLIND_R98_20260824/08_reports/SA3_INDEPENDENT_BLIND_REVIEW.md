# FIG-P547-01 SA3 独立盲审报告

- HANDOFF_ID: `A-R130-P547-SA3-RESUME-20260824`
- OWNER_DIALOGUE: `DIALOGUE_A_VISUAL`
- REVIEWER: `SA3_gpt-5.6-sol_xhigh`
- 结论: **SA3_INDEPENDENT_PASS**
- 适用范围: A 本地第二盲审证据；不等同于全书最终放行。

## 身份与隔离

- 官方 R98 PDF SHA-256: `52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`。
- 只读业务源 SHA-256: `DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`；该 C01 源相对共同基线无差异。
- 审查未读取 P547 R10/R11、SA1 报告、root 结论、中央旧 PASS 或其他 P547 证据。
- 所有生成与修订均位于 A 本地证据复制件；业务源码和官方 PDF 未写入。

## 四视图与可访问性

`full_page_200dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png` 均已原图打开；图面清楚、层级一致、无裁切或非设计碰撞。protanopia、deuteranopia、tritanopia 三视图亦已打开，编码在颜色退化下仍可辨。独立 wrapper 仅有 tight-page 宽盒提示，不造成可见裁切。

## 完整分母

| 账本 | 分母 | 结果 |
|---|---:|---|
| text parents | 23 | PASS |
| vector parents | 34 | PASS |
| object parents | 57 | PASS |
| object pairs | 1596 | 0 machine failure；人工临界图 PASS |
| glyphs | 193 | missing=0、foreign=0、全部 PASS |
| path records | 71 | 独立重放均非空、1x/8x PASS |
| path pairs | 2485 | 2450 DISJOINT、26 DESIGN、9 设计接点确认 |
| commands | 143 | 独立重放均非空、1x/8x PASS |
| within-record command pairs | 186 | 同记录组合或分离，全部 PASS |

全部要求的原生 1x 与 8x 接触表已逐张打开。对象 pair 最小可见间距：TEXT_TEXT=5px（门槛4px）、TEXT_VECTOR=3px（门槛3px）、TEXT_NODE_BORDER=9px（门槛5px）。`+` 的 G057/G143 均为 H=22px，满足关系号/运算符 22px 门；等号与箭头按独立矢量规则审计。

## ownership 判定

- G054：H=28px、area=53px、missing=0、foreign=0，PASS。
- G139：component 174 初始候选为 G140=401px、G139=1px，401:1 超过 20:1；整条 402px 连通分量归 G140。该 1px 是后继 `p` 的边界抗锯齿外延，不是 G139 分号缺笔。G139 独立重放 H=28px、area=53px、missing=0、foreign=0，PASS。
- G035/G048/G120/G133 的伸展括号使用 native 300dpi 可见轮廓窄 ROI 恢复；G120 收回曾错归 G114/G115 的 20+8=28px，四个括号均为完整、纯净轮廓。
- 4 个 multi-owner component 均无未归属像素。未达到 20:1 的 component 26/33 使用 PDF candidate support 精确拆分；component 91 用完整可见伸展括号覆盖；component 174 使用 20:1 主导连通分量规则。

## 9 个路径接点

`PATHPAIR_0276/0282/0344/0352/1674/2162/2168/2189/2197` 的原生 1x、8x 临界图均已打开。八个是箭头/边在圆形节点边界上的设计端点，一个是桥接框 C01 与 C03 箭头的设计连接；人工结论均为 `DESIGN_CONNECTION_CONFIRMED`，不计非法覆盖。

## 规范字段

- SOURCE_FONT_PASS=true
- PIXEL_HEIGHT_PASS=true
- SAME_CLASS_RATIO_PASS=true
- ROLE_RATIO_PASS=true
- FONT_VISUAL_HARMONY_PASS=true
- MATH_SEMANTICS_PASS=true
- TEXT_CONSISTENCY_PASS=true
- GRAYSCALE_PASS=true
- PAGE_INTEGRATION_PASS=true
- OVERLAP_PIXEL_COUNT=0
- CLIP_BOUNDARY_PIXEL_COUNT=0
- PIXEL_ADJUDICATION_STATUS=MASK_OWNERSHIP_CONTAMINATION_CORRECTED

## 未解决项

无。
