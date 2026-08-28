# FIG-P632-01 根线程路由验收

- 验收时间：2026-08-24T11:04:01+08:00
- 候选：官方 R95，物理页 645／印刷页 632／图 33.2
- 角色：历史旧 PASS 的当前 schema 独立 SA1 重新资格认定
- 根结论：`EVIDENCE_INTEGRITY_PASS=false`；`FIGURE_HARD_GATES_PASS=false`；`FAIL→SA2`

## 根线程独立复核

- SA1 目录在 root 签发前共有 2123 个普通文件：2069 PNG、24 CSV、8 JSON、11 PDF、5 Markdown、4 Python、1 PYC 与 1 个无扩展名 stop 文件。根线程验证 2069/2069 PNG 均可解析，24/24 CSV 与 8/8 JSON 均可读取；零字节文件、ADS、路径逃逸和 stop 时间之后写入均为 0。
- 根线程逐张打开 42/42 glyph contact sheet，覆盖 413/413 个 glyph 的原生 1× original、target overlay、mask only 与 8× nearest；未见目标字形缺笔、夹带外来笔画或裁切。人工 ledger 的 413 行均为 `ACTUAL_OPEN=YES`，但严格原生像素门仍为 383 PASS／30 FAIL；声明有效字号 413/413 达到 9.5pt 不足以抵消像素字号失败。
- 根线程打开 full-page、figure-crop、standalone 与 grayscale 四视图。字重与颜色层级可辨，数学语义、灰度和页面融入未见新增错误；但 30 个 glyph 像素门失败使字号视觉协调项必须 FAIL。D 门为 15 PASS／13 FAIL，跨面板 E 门为 16 PASS／12 FAIL，不能以主观“整体尚可”放行。
- 全量文字—图形关系为 390 行，原始前景 overlap 均为 0；其中 36 行净空小于硬门阈值，故 physical relation 为 354 PASS／36 FAIL。根线程另打开 R0018、R0046、R0188 的 original、intersection 与 8× overlay：三个 intersection 均为空白；R0018 为 4px<8px、R0188 为 1px<3px 的真实净空失败。R0046 实际 overlap=0、raw clearance=16px≥8px，属于物理 PASS；旧表把复合父级包络的 bbox 结果写成 FAIL，形成唯一 `RESULT_CONSISTENCY_FAIL`，不得把它计作第 37 个物理关系失败。
- G204–G209 的 `π(a,t)` 被记录到 P06 顶部刻度组，实际应属于 P07 底部条件公式；六行当前身份语义父级映射均 FAIL。经正确父级重测，P06↔P07 仍为 overlap=0、clearance=20.518285px，但错误映射本身尚未闭合。
- `role_ratio_recomputed_R111_SA1.csv` 的 helper 计算可复核，但旧 `after_pixel_measurements.csv` 的 413 行仍全部是 `ACTUAL_BASELINE_PENDING`，因此原始 role-ratio 证据门 FAIL。该缺口不能由二次重算 helper 代替。
- 代理报告、manifest 与 `WRITE_STOPPED` 的 UTC tick 完全相同（639231370048562596）。虽无文件晚于 stop，但 stop 是否为代理绝对最后写入无法证明，新增 `WRITE_STOPPED_LAST_WRITE_UNPROVABLE` 完整性失败。结合 R0046 结果一致性、G204–G209 语义父级和 413 行 raw role-ratio 未闭合，代理目录的 evidence integrity 总结只能为 FAIL。

## 路由

FIG-P632-01 从 `SA1` 转入唯一业务源码写者串行 `SA2` 队列。后续须修复 30 个原生像素字号失败、D/E 比例、36 个真实净空失败、G204–G209 父级映射及 raw role-ratio 证据链，同时保持字号、字重和颜色与正文协调；可适度缩小局部文字以解除挤压，但不得低于 9.5pt、不得损害可读性，也不得用遮盖、伪 halo、整体缩放或突兀放大规避。修复后必须进入新的官方候选、全新独立 SA1、隔离 SA3 与 root 签发，本轮不得计入 99 图最终完成。
