# FIG-P092-01｜独立 SA1 严格复核（新 Goal R1）

- RESULT: **FAIL**
- ROUTE: `SA2_REQUIRED`
- OFFICIAL_PAGE: R89 物理页 96、书页 83、图 6.1
- SOURCE_WRITES: `NONE`

## 确定性硬失败

1. 图内刻度 8.8pt、注释/公式 9.2pt、轴标签 9.4pt，均低于 9.5pt；仅题注约 10pt 达标。
2. x 轴同类刻度像素高度：`0=27px`、竖排 `1/2=71px`、`1=26px`；max/min=`2.73`、`1/2` 对类中位数=`2.63`，远超同类 `[0.92,1.08]`。根因是 `\tfrac12` 破坏横轴层级。
3. 峰值文字“最大不确定性：1 比特”的最近文字像素 `(1328,776)` 与峰值圆点最近图形像素 `(1328,777)` 仅 1px，低于文字—标记 3px 门。
4. 以刻度中位数 27px 为基准，`H_2(p)=41px`、公式块 39px、“确定性”35px，角色比约 1.52/1.44/1.30，超过相应上限。

## 其余实测

- 官方页直接原生渲染 `2481×3508 @ 300dpi`；CJK 最小 34px、数字最小 26px、小写 p 30px、基准公式 39px、自然下标 19px，像素高度下限通过。
- `OVERLAP_PIXEL_COUNT=0`、`CLIP_PIXEL_COUNT=0`；但 `MIN_TEXT_CLEARANCE_PX=1`，仍为硬失败。
- 数学语义、题注/正文一致性、灰度与页面融合通过。

## 必须修复

把所有图内基准字号统一到至少 9.6pt，不整体缩放；把 x tick 的 `\tfrac12` 改为横排 `$1/2$`；峰值标签至少上移 1.5pt，并从新官方页验证文字—圆点净空至少 3px。之后生成全量五类证据并重新走独立 SA1/SA3。

## 门矩阵

| 门 | 结果 |
|---|---|
| SOURCE_FONT | FAIL |
| PIXEL_HEIGHT | PASS |
| SAME_CLASS_RATIO | FAIL |
| ROLE_RATIO | FAIL |
| OVERLAP / CLIP | PASS / PASS |
| MIN_CLEARANCE | FAIL（1px） |
| VISUAL_HARMONY | FAIL |
| MATH / TEXT / GRAYSCALE / PAGE | PASS |
