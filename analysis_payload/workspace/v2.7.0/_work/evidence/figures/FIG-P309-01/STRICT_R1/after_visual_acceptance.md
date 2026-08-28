# FIG-P309-01 严格视觉验收（SA1 / STRICT_R1）

## 候选与独立性

- 冻结候选：`strict_current_r92_fullbook/main_full.pdf`
- 正式整书物理页：334；印刷页：321；图号：图 18.1。
- 图源：`fig_v3_c02_margin.tex`。
- 本轮从正式候选、当前图源和相邻正文重新取证；未读取或继承本图此前任何 R1、SA2、SA3、ROOT 或中央库存结论。
- 图源、正文、构建物、库存和状态均未修改；本轮只写本隔离证据目录。

## 证据完整性

- 300dpi Poppler 原图，无二次 resize；200dpi 仅用于整页总览。
- 16 个可见文字/公式 token 均具有唯一 `ELEMENT_ID`、源码行、角色、有效字号、300dpi 实测墨迹框与像素高度。
- 8 个文字语义组与 25 个独立图形前景对象逐对检测，共 200 条 TEXT-GRAPHIC 关系；另有 28 条 TEXT-TEXT bbox 关系。
- 25 个图形对象分别建掩膜：两条坐标轴、三条边界线、三组箭头/连接线、三条直标引线、10 个类别标记、4 个支持向量外圈。未用合并大掩膜替代逐对象结论。
- 文字层与图形层由透明全页 redaction 独立分层；逐图形对象从 PDF drawing record 单独重放并由 Poppler 渲染。逐对象掩膜并集与原图形层 Dice=0.985797；文字语义组并集与原文字层 Dice=1.000000。
- 已人工查看四视图、六组最近像素 ROI、各文字组 1:1 原生 ROI；记录见 `manual_pixel_roi_review.csv`。

## 硬门矩阵

```text
SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = false
ROLE_RATIO_PASS = true
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 8.8489
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true
```

补充净空：TEXT-TEXT 最小 bbox 净空 28px；TEXT-GRAPHIC 最小前景净空 8.8489px；最终图裁图边缘留白 12px；正式页边缘最小留白 657px。均分别高于 4px、3px、6px 的适用下限。单面板图，跨面板门不适用；无节点边框。

## 失败项

1. **源级字号下限失败。** `w` 标签（53-54 行）、`2/\lVert w\rVert`（59-60 行）、“外圈：支持向量”（73-74 行）均由 9.2pt 基准产生，低于 9.5pt；审计表中对应 7 个 token 行失败。图内无整体缩放，`graphics_scale=1.0000`。
2. **实际像素高度失败。** `T11_HMINUS_SUBMINUS` 的自然下标减号只有 3px，低于 15px 下限。
3. **同类比例失败。** 同角色基础数学运算符中，斜线 33px、两条范数竖线 36px，中位数 36px，斜线比例 0.9167<0.92；直线标签的自然脚本符号中，`+` 为 19px、`-` 为 3px，中位数 11px，比例分别为 1.7273 与 0.2727，均超出 [0.92,1.08]。
4. 上述字号、像素与同类比例硬失败使 `VISUAL_HARMONY_PASS=false`；尤其 `H_-` 的减号在 1:1 ROI 中明显过薄。不能用“仍可辨认”覆盖硬门。

## 通过项

- **零重叠与净空：** 所有 200 条 TEXT-GRAPHIC 和 28 条 TEXT-TEXT 关系重叠均为 0；最近对象为 `H_+`/`H_-` 与各自引线，净空 8.8489px。
- **裁切：** 所有文字、线、箭头头部、标记和外圈均完整，`CLIP_PIXEL_COUNT=0`。
- **数学语义：** 三条线分别满足 `g(x)=0,+1,-1`；四个外圈点精确位于对应间隔边界；间隔箭头长度与 `2/||w||` 一致，误差小于 0.0001；`w` 箭头与法向量 `(-0.7,1)` 同向。
- **图文一致：** 图注只保留分类超平面、两条间隔边界与几何间隔这一条结论；相邻正文对虚线、法向量、距离和支持向量位置的描述与图一致。
- **灰度与阅读路径：** 实线/虚线/点划线及实心圆/空心三角/外圈均可在灰度下区分；读者可依次识别三条平行线、外圈支持向量、法向量和间隔距离。
- **页面融合：** 物理页 334 无图文遮挡、孤行、异常留白或裁切；题注与相邻正文位置稳定。

## 结论

`RESULT: FAIL`。不得启动 subagent3。必须由 subagent2 定向修复后重新编译、重新生成正式候选，并全量重做 300dpi 字号/像素/比例/重叠验收。

