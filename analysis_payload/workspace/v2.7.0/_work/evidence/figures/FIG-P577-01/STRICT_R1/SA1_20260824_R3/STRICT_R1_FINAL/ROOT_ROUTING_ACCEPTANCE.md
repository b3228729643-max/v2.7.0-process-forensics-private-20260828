# FIG-P577-01 root 路由验收

- 结论：`FIGURE=FAIL → SA2`；`EVIDENCE_INTEGRITY=FAIL`。本文件覆盖该轮 terminal 中的 `evidence_integrity_result=PASS`，但不改变已经由 root 独立确认的六项图本身硬失败。
- 权威：官方 R95 物理页 625／印刷页 612，PDF SHA-256 `24CC8BE127D00435CC544E4E9142D45272675DA0D9967C89ADAC294D08910496`；R94→R95 该页与裁图均为 0 像素差。
- root 复算：345/345 唯一字形、345/345 人工 ledger、reviewer 空值 0、ledger 非 PASS 0；59,340/59,340 唯一无序文字对、非法对 0；3 条精化必查关系中 1 FAIL；6 条曲线—底板遮挡关系中 5 FAIL，`PRE∩GROUND` 合计 3825px。
- root 文件终检：expected=actual=2075；9/9 JSON 可解析；2021/2021 PNG 可打开；零字节文件 0；普通文件名冒号 0；2075 个文件均只有主 `:$DATA` 流，ADS 0。
- 证据完整性否决：`text_graphic_relations.csv` 与 `text_graphic_relations_initial_projection_SUPERSEDED.csv` 的表头各重复一次 `TERMINAL_DISPOSITION,TERMINAL_REASON`，两表不能由 `Import-Csv` 无歧义解析。严格 schema 要求底层 CSV 与汇总可复核，因此不得保留 evidence PASS。
- 已独立确认的源码返修白名单：TG457 中 `0.8` 刻度到接受框边界仅 2px＜5px；五个 opacity=1 白底分别覆盖 p(y) 曲线 302、304、609、1571、1039px。第六个青色 q 图例底板覆盖为 0，不能误报。
- revision111 处置：该轮旧的低轮廓标点机械绝对像素行只作非终态历史，不进入 SA2 白名单；后续修复后全新 SA1 必须按同码点/字体/字重/有效字号的 H_INK 与面积双比例重新校准。运算符及分数主体门不变。
- 该结论只允许把 P577 保守路由到唯一串行 SA2 队列，不构成任何严格最终 PASS；修复后必须从新官方 PDF 由全新独立 SA1→隔离 SA3→root 重走闭环。

签发时间：2026-08-24T08:38:21+08:00
