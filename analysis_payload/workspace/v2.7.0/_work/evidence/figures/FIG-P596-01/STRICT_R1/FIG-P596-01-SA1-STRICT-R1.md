# FIG-P596-01 — SA1 严格复核 R1

- 角色：SA1（独立、只读）
- 结论：`RESULT=FAIL`
- `SPLIT_REQUIRED=NO`
- 候选：`R3/p596_root_r3p1_*`
- 规则：新 Goal §9.2.1、§9.3；旧 PASS 不迁移

## 严格门结论

| 门 | 结论 | 独立证据 |
|---|---|---|
| `SOURCE_FONT_PASS` | FAIL | 图内文字源级均为 9.6pt、scale=1；PDF span 约 9.5641–9.6593pt，题注约 9.9626pt，抽查未见局部缩放。但缺 `after_font_audit.csv`。 |
| `PIXEL_HEIGHT_PASS` | FAIL | 原始 300dpi 抽测：中文 36–37px、拉丁大写 27–28px、希腊小写 π/α 20px、拉丁小写 d 30px、完整基准公式块最小 28px；抽测达下限，但缺全 ELEMENT_ID 测量表和叠加图。 |
| `SAME_CLASS_RATIO_PASS` | FAIL | 抽测同类比例：中文 1.028、拉丁大写 1.037、π/α 1.000、两行平衡证书 1.000；缺全量分类 CSV。 |
| `ROLE_RATIO_PASS` | FAIL | `$\pi K=\pi$` 公式组实测约 28px，相对普通节点 BASE 37px 为 0.757；若按公式块计入，低于 [1.00,1.18]。缺正式基准与逐元素记录，不能放行。 |
| `OVERLAP_PIXEL_COUNT` | FAIL (`UNKNOWN`) | 未生成独立语义前景掩膜与 `after_overlap_report.csv`，不得把未知写成 0。 |
| `CLIP_PIXEL_COUNT` | FAIL (`UNKNOWN`) | 未生成裁切像素报告，不能证明为 0。 |
| `VISUAL_HARMONY_PASS` | FAIL | 当前候选视觉层次基本正常，但规定视图和验收记录不完整。 |
| `MATH_SEMANTICS_PASS` | PASS | 细致平衡只推出平稳；有限不可约/正 Harris 常返对应时间平均；非周期性对应边缘收敛；独立核反例与诊断分支正确。 |
| `TEXT_CONSISTENCY_PASS` | PASS | 图、题注与章节正文一致；四种线型与图例语义一致。 |
| `GRAYSCALE_PASS` | FAIL | 现有灰度图中线型可辨，但缺最终命名灰度证据与验收记录。 |
| `PAGE_INTEGRATION_PASS` | FAIL | 当前页面未见明显碰撞，但缺强制完整页 200dpi 证据。 |

## 原像素净空抽查（非正式替代证据）

| 类别 | 最小观察值 | 最近对象 |
|---|---:|---|
| TEXT–TEXT | 6px | E14–E15 |
| TEXT/FORMULA–LINE/ARROW | 12.7px | E15–诊断连接线 |
| TEXT/FORMULA–NODE_BORDER | 12.7px | E09–结果框 |
| ARROWHEAD–TEXT | 17.0px | E25–分支箭头 |
| TEXT–图像边 | 299px | standalone 顶边 |

这些数值仅说明抽查对象未见接触，不能替代逐对象掩膜和全组合报告。

## 必须补齐

1. 四个最终视图：完整页 200dpi、裁图 300dpi、独立图 300dpi、灰度 300dpi，均由最终 PDF 直接渲染且不得 resize。
2. 为 E01–E32、题注、四条图例及所有公式子串建立唯一 ID，并补齐五项强制证据。
3. 正式消解 `$\pi K=\pi$` 的角色归类与 0.757 比例；若合规测量仍越界，必须修改实际字形高度并重建。
4. 以 TEXT、FORMULA、LINE_ARROW、NODE_BORDER、ARROWHEAD 独立掩膜证明零非法重叠、零裁切及全部净空。

