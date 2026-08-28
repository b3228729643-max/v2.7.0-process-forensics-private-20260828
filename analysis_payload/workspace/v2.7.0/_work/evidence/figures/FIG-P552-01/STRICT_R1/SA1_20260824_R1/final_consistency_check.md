# FIG-P552-01｜SA1 最终机器可读一致性终检

`CHECK_STATUS: PASS` 仅表示证据文件彼此一致；本图的严格验收结论仍为 `FIGURE_RESULT: FAIL`，应移交 SA2。

## 固定口径

唯一权威测量由冻结最终 PDF 的完整物理页直接 rasterize 为原生 300 dpi 固定网格，再从该页切片图裁；没有 resize。direct-clip 因 clip 原点和抗锯齿相位可能不同而为 `SUPERSEDED`；其 187/189 旧中间数不属于任何有效结论。

## 机器终检结果

| 项目 | 结果 |
|---|---|
| Required artifacts | 20/20 存在；missing=0 |
| `audit_metrics.json` | overlap=221；failure-pairs=4；same-class=false；clip=0 |
| `measurement_consistency.json` | overlap=221；`22 + 55 + 33 + 111 = 221` |
| `after_overlap_report.csv` | 4 个 FAIL 行，像素 `[22,55,33,111]`，和=221 |
| 31 个 critical pairs | 31/31 均有 raw/overlay/overlap 的最近邻 `8x` ROI；missing=0 |
| 有效旧结论扫描 | `OVERLAP_PIXEL_COUNT: 187/189` 和 `SAME_CLASS_RATIO_PASS: true` 均无匹配 |

去重规则：每一个无序文字--文字或文字--图形 pair 只以双方分离、未膨胀 raw mask 计一次；不把绘制顺序、underlay 或重复 CSV 行加入总数。

完整字段与空缺清单见 `final_consistency_check.json`。
