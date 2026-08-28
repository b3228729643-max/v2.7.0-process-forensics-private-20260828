# FIG-P157-01 根线程路由验收

- 验收时间：2026-08-24T10:55:46+08:00
- 候选：官方 R95，物理页 170／印刷页 157／图 10.1
- 角色：历史旧 PASS 的当前 schema 独立 SA1 重新资格认定
- 根结论：`EVIDENCE_INTEGRITY_PASS=true`；`FIGURE_HARD_GATES_PASS=false`；`FAIL→SA2`

## 根线程独立复核

- SA1 封存时共有 866 个普通文件：695 PNG、26 CSV、22 JSON 及其他构建/报告文件。根线程验证 695/695 PNG 均可解析，26/26 CSV 与 22/22 JSON 均可读取；零字节文件、ADS、不安全文件名和 stop 后写入均为 0。`WRITE_STOPPED.json` 是代理绝对最后写入；本文件是封存后由 root 单独追加的路由签发。
- 根线程逐张打开 10/10 glyph contact sheet，并回读 80/80 行人工 ledger：每个 glyph 的原生 1× original、target overlay、mask only 与 8× nearest 均记实际打开，missing/foreign ink 合计均为 0。字号最小 9.8192pt，11/11 元素达到 9.5pt；大小、字重、颜色、灰度与页面融合的逐角色人工台账为视觉协调 PASS，但该视觉判断不抵消数值硬门。
- 五个低轮廓字形的同 codepoint、字体、字重、颜色、有效字号和原生 300dpi 校准链均已验证有效；G0005、G0014、G0050、G0068、G0080 的 H_INK/ink-area 比例越界，故 pixel gate 为 75 PASS／5 FAIL。
- D 门 80/80 通过；E 门中 BODY/REGION_LABEL/CJK_FULL 的 35px／37px=`0.9459<0.95`，涉及 8 glyph，故角色比例硬门失败。clip 为 20/20 PASS；154/154 必查文字关系通过，文字最小净空 16px。
- 全无序 pair 为 190 行，189 PASS／1 FAIL。根线程已打开 P0155 新的独立 raw-mask 1×/8× original、双方 mask、intersection 与 overlay：训练/验证两条独立曲线 final-visible 共享 139px、净空 0。该结果使用同一原生 300dpi 坐标、两曲线独立重放且不做 peer 删除、膨胀或缩放；后续真实不透明对象与 pair intersection 为 0。
- 旧“516px”与 peer-removal“37px”均已在 canonical register、视觉报告、数学报告与机器终检中撤销。唯一有效曲线结果为 139px／0px。底层 CSV、JSON、Markdown 与 `R111_MACHINE_FINAL_CHECK.json` 的证据完整性 PASS／图形硬门 FAIL 一致。

## 路由

FIG-P157-01 从 `SA1` 转入唯一业务源码写者串行 `SA2` 队列。后续应定向分离两条曲线的可见笔画包络、修复五个低轮廓校准失败和 0.9459 角色比例，同时维持当前自然字号层级；不得以突兀放大、整体缩放、遮盖或伪 halo 规避。修复后必须进入新的官方候选、全新独立 SA1、隔离 SA3 与 root 签发，本轮不得计入 99 图最终完成。
