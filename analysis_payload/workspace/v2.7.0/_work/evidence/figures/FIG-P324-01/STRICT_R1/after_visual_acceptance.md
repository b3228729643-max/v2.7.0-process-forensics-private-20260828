# FIG-P324-01 SA1 STRICT_R1 视觉验收矩阵

- 冻结候选：`strict_current_r92_fullbook/main_full.pdf`
- 正式整书物理页：349；印刷页：336；图号：图 19.1
- 原生测量：Poppler 300 dpi，2481 x 3508 px，不进行 resize
- 文字审计：43 个 ELEMENT_ID，合并为 12 个独立语义文本对象
- 图形审计：15 个逐条分离的线、箭头与节点边框对象
- 人工查看：`full_page_200dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`，以及三个原生 1:1 ROI

```text
SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = false
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0.0  # O10/O11 的 PDF/vector bbox 净空；二者实际前景净空为 6.0px
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true
```

## 精确失败

1. 源级字号：E31--E35 的边标签基准公式为 8.8pt；E36 说明文字和 E37--E43 形状编码为 8.5pt。共 13 个 ELEMENT_ID 未达到 9.5pt。E32/E35 虽为自然下标，但其母公式仅 8.8pt，仍失败。
2. 300 dpi 像素高度：E23 `=` 为 12px，E33 `mapsto` 为 15px，均低于基准运算符 22px 下限。
3. 同类比例：12 个 ELEMENT_ID 超出 [0.92,1.08]；此外节点大写/数字类跨通道中位数比为 37/33=1.1212，节点自然下标类为 24.5/21=1.1667，均超过 1.10。
4. 角色比例：19 个 ELEMENT_ID 超出对应角色带。最明确的字号层级失衡是 E36 与 E37/E39/E41/E43 的 CJK 高度均为 31px，相对普通节点 CJK 中位数 36.5px 仅 0.8493，低于注释/图例下限 0.95。
5. 文字净空：O10 `e_m mapsto alpha_m` 与 O11 “仅权重更新返回训练”的分色语义掩膜交集为 0，最近有效前景坐标分别为 (1514,1583) 与 (1514,1589)，前景净空 6px；但两个 PDF/vector bbox 相交，bbox 净空为 0px，低于文字—文字 4px 硬门。因此这不是“非法前景像素交叠”，而是独立的 bbox 净空失败。

## 已通过但不能抵消失败的项目

- 所有独立语义前景组合的非法交叠总数为 0；裁切为 0。
- 文字到图形的最小值是 O09 集成模型文字到自身 G10 双边框 11px，达到节点内 5px 下限；其余 text-line/arrow/node-border 组合也通过。
- AdaBoost 的 `D_m -> G_m -> e_m -> D_{m+1}`、`e_m -> alpha_m`、`G_m/alpha_m -> F_m` 关系与正文、图注一致。
- 灰度下形状和实/虚线仍可区分；整页图注、正文与页边界没有相互碰撞。

## 结论

`RESULT = FAIL`。不得启动 SA3。应由 subagent2 定向修复字号、两个运算符像素高度、O10/O11 bbox 净空和同类/角色比例；重新构建正式整书候选并全量重测。
