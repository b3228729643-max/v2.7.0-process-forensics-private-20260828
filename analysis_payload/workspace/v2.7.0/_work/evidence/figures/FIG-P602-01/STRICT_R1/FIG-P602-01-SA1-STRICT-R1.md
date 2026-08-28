# FIG-P602-01 — SA1 严格复核 R1

- 角色：SA1（独立、只读）
- 结论：`RESULT=FAIL`
- `SPLIT_REQUIRED=NO`
- 候选：`R3/p602_root_r3_*`
- 规则：新 Goal §9.2.1、§9.3；旧 PASS 不迁移

## 严格硬失败

1. `ROLE_RATIO_PASS=FALSE`：普通正文 BASE 为 9.6pt；接受率公式显式 11.8pt，源级比 `11.8/9.6=1.229`，超过公式块上限 1.18。原始 300dpi 中大公式 α 约 46px，普通 α 约 38px，实际比约 1.21，亦越界。
2. `MIN_TEXT_TEXT_CLEARANCE_PX=3`：接受率标题和紧随的公式分子为独立 TEXT/FORMULA 对象；有效前景最近像素中心距仅 3px，低于 4px。
3. `PAGE_INTEGRATION_PASS=FALSE`：当前页末正文下界约 599.414pt，A4 页底 841.890pt，留下约 242.476pt（85.5mm，约 1010px@300dpi）连续页尾空白。

## 严格门结论

| 门 | 结论 | 独立证据 |
|---|---|---|
| `SOURCE_FONT_PASS` | FAIL | 普通文字 9.6pt、题注约 10pt 均达下限，但缺 `after_font_audit.csv`。 |
| `PIXEL_HEIGHT_PASS` | FAIL | 原始 300dpi 抽测：中文 34–35px，数学自然脚本约 20–29px，大公式主体 46–50px；抽测未发现低于脚本阈值对象，但缺全量 ELEMENT_ID CSV 和 overlay。 |
| `SAME_CLASS_RATIO_PASS` | FAIL | 抽测普通边标签 34–35px，未见抽测越界；缺全量同类测量。 |
| `ROLE_RATIO_PASS` | FAIL | 11.8pt/9.6pt=1.229；实际 α 高度比约 1.21，均超过 1.18。 |
| `OVERLAP_PIXEL_COUNT` | FAIL (`UNKNOWN`) | 无完整语义掩膜与 `after_overlap_report.csv`，不得伪报 0。 |
| `CLIP_PIXEL_COUNT` | FAIL (`UNKNOWN`) | 无裁切报告。 |
| `VISUAL_HARMONY_PASS` | FAIL | 公式层级突兀、标题—公式净空不足、页尾大块空白。 |
| `MATH_SEMANTICS_PASS` | PASS | 提议、MH 接受率、U 判定、接受更新和拒绝留驻与正文一致。 |
| `TEXT_CONSISTENCY_PASS` | PASS | 图文术语及读图顺序一致。 |
| `GRAYSCALE_PASS` | PASS | 当前灰度中流程形状和线型仍可区分。 |
| `PAGE_INTEGRATION_PASS` | FAIL | 约 85.5mm 连续页尾空白。 |

## 精确修复

1. 将接受率公式有效字号降至不高于约 11.3pt，或提供预先批准且满足 Goal 的强调证据；优先采用前者。
2. 把标题与公式间的负间距改为足以保证有效前景净空至少 4px 的正间距，重建后逐像素复测。
3. 从连续最终书稿重新排浮动体/后续正文，消除异常页尾空白。
4. 从新最终 PDF 直接生成规定视图、五项强制证据及全量语义掩膜；仅在重叠像素=0、裁切像素=0、全部净空和字号比率通过后复审。

