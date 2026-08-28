# FIG-P020-01 根线程路由验收

- 验收时间：2026-08-24T09:25:11+08:00
- 候选：官方 R95，物理页 17，图 1.1
- 角色：历史旧 PASS 的独立严格 SA1 重新资格认定
- 根结论：`EVIDENCE_INTEGRITY_PASS=false`；`FIGURE_HARD_GATES_PASS=false`；保守 `FAIL→SA2`

## 根线程独立复核

- 根线程独立枚举 524 个文件：488 PNG、15 CSV、6 JSON、15 other；全部 PNG 可打开、全部 CSV/JSON 可解析，零字节 0、不安全/ADS 名称 0。
- 108/108 个字形均有 raw mask、1×三联、8× nearest 与逐格人工 ledger；18/18 张 contact sheet 已由根线程逐张打开。逐格可见目标覆盖与 mask 纯净性无新的反例。
- 关系底表为 45 TEXT_TEXT、140 TEXT_LINE_ARROW/TEXT_NODE_BORDER、12 CROSS_PANEL_TEXT，加 10 个图边关系；208 条 after-overlap 行均记 PASS。根线程查看整页、彩色裁图、灰度、overlay 与遮挡反演，未发现额外文字—图形重叠或突兀字号。
- 唯一已证实图硬门失败为 `F020_G091`：题注 CJK `一` 的原生 300dpi final raw mask 为 90 个 ink pixels，bbox `38×5px`，根线程逐像素复算 `H_INK=5<30px`。该字不是 revision111 的低轮廓标点例外；7/7 真正低轮廓标点校准均通过。
- G091 失败足以否决旧 PASS。后续 SA2 应优先重写/重排含该单笔字的题注表达，避免用突兀的纵向拉伸或整体放大伪造 30px；仍须保持有效字号、净空与整页协调。

## 证据完整性否决

- `terminal/WRITE_STOPPED.md` 的时间为 09:21:04，且声明其后不得再写；但 `terminal/MACHINE_INTEGRITY.json` 与 `terminal/TERMINAL_MANIFEST.json` 均在 09:21:12 写入。根线程独立枚举得到 `writes_after_stop=2`。
- 因代理同时声称 `WRITE_STOPPED` 是最后写入，这一终态顺序与磁盘事实矛盾，故代理的 evidence-integrity PASS 被 root 降为 FAIL。此缺陷不推翻直接从 R95/G091 raw mask 复算出的图形失败，只禁止迁移本轮任何 PASS 字段。

## 路由

FIG-P020-01 从 `SA1` 转入唯一业务源码写者串行 `SA2` 队列。修复后必须生成新的非覆盖证据并重新走新官方候选、全新独立 SA1、隔离 SA3 与 root 签发；当前不得计入 99 图最终完成。

