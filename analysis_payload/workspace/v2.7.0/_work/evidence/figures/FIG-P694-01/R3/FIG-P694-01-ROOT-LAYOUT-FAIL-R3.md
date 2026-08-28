# FIG-P694-01｜根线程首轮 R3 版式失败记录

- FIGURE_ID: `FIG-P694-01`
- ROUND: `R3 initial`
- ROOT_RESULT: `FAIL_LAYOUT`
- SEMANTIC_INTEGRATION: `PENDING_LAYOUT_REMEDIATION`
- FINAL_ACCEPTANCE: `NO`

## 已完成的根线程集成

根线程完整回读 P694 设计确认与专属 SA2 报告，并单写同步 v2.7.0 standalone/page wrapper、V5-C06 `figure_sources.json` 以及 `figure_numeric_manifest_v16.json` 的算法语义契约记录。当前身份仍为 canonical UID `FIG-P694-01`、source object `FIG-V5-C06-07`、label `fig:V5-C06-variational-updates`、图 35.7、页 691；中央 CSV 尚未改成新候选通过。

## 首轮构建事实

- standalone 构建成功：`p694_root_r3_standalone.pdf`，103,994 bytes，A4、1 页。
- page wrapper 构建成功但输出 3 页：`p694_root_r3_page.pdf`，120,665 bytes；首引在页 691，图体与题注在页 692，专属读图句在页 693。
- standalone/page 日志各命中 6 处 `Overfull \hbox`，约为 24.70、21.98、8.85、22.07、23.53 与 33.22pt，来源集中在长公式与状态输出节点。

## 视觉失败

根线程亲自查看 `p694_initial_page_200dpi-1/2/3.png` 与 `p694_initial_standalone_200dpi.png`。图体存在大面积真实碰撞：菱形门覆盖相邻节点，长公式越出框体，多条反馈/失败边穿过文字，局部和外层面板交界拥挤，外层候选、`S_acc` 与输出区相互覆盖。即使语义文字已写入，当前视觉无法可靠追踪状态路径，也不满足首引—图—题注—读图句同页要求。

## 根线程裁决与返工边界

首轮 R3 明确失败，不得被“编译成功”或旧中央 `RESOLVED_EVIDENCE_CLEAR` 状态替代。当前已退回同一专属 SA2 作 R2.1 定向版式返工：只改 P694 图源和追加原 SA2 报告；保持同 UID/label、单 figure/tikzpicture、上下双面板、可见字号至少 9.5pt、无整体缩放，并保留全部不可协商状态语义。

ROOT_RESULT: **FAIL_LAYOUT**  
BLOCKERS: **3-page wrapper; 6 overfull boxes; severe node/text/edge collisions**  
NEXT_ACTION: **等待 R2.1 图源返工；根线程在同一 R3 目录以最终 jobname 重建并重新执行日志、AUX/FLS、彩色、灰度、standalone 与单页融合门。**

## R2.2 根级复测（仍失败）

- 2026-08-23 根线程在专属 SA2 交权后重建最终 jobname：standalone 为 1 页、97,108 bytes；page wrapper 为 1 页、113,285 bytes，原位页码 691。
- 两份日志均仍有 3 处真实 `Overfull \\hbox`：3.03pt、6.69pt、33.86pt；命中图源第 83--84、168--169、296--306 行附近。
- 根线程亲自查看新的 `p694_root_r3_page_300dpi.png`。单页条件虽已满足，但上面板的 A0/A1/A2/A3--A5、成功接口与三格状态带仍相压，公式和边线互穿；下半面板 B3/B4/B5--B6、失败状态带、预算/收敛候选和全宽输出出现大面积覆盖，流程不可可靠追踪。
- 因彩色原位页已构成硬视觉阻塞，本轮不把灰度/standalone 视图当作补救证据，不启动 SA1/SA3 独立复审，也不更新中央通过计数。

R2_2_ROOT_RESULT: **FAIL_LAYOUT**  
R2_2_BLOCKERS: **3 overfull boxes; severe node/text/edge collisions despite one-page output**  
R2_2_NEXT_ACTION: **退回同一专属 SA2 作 R2.3 结构性重绘；不得在现有坐标上微调冒充通过。**

## R2.3 根级复测（几何清理，但融合高度失败）

- standalone：1 页、90,014 bytes；page wrapper：3 页、110,933 bytes。两份日志的 Overfull、Underfull、未定义控制序列及致命错误均为 0。
- AUX 保持图号 `35.7`，但图题落在物理页 692；原位三页实看确认首引在 691、图体与题注在 692、专属读图句在 693。
- 根线程亲自查看 `p694_r23_standalone_300dpi.png` 与 `p694_r23_page_200dpi-1/2/3.png`。内容驱动 matrix 已消除 R2.2 的大面积覆盖：主节点、状态格、公式和边线可追踪，无真实碰撞。剩余局部观感问题是 A0 的 `alpha>0` 被不自然断行，以及 B4 标题把 Newton 断成 `New-ton`。
- 因首次引用—图—题注—读图句仍未同页，R2.3 不得进入独立复审或中央通过计数。下一轮只做垂直压缩和断行修正，不回退已通过的几何结构。

R2_3_ROOT_RESULT: **FAIL_INTEGRATION_HEIGHT**  
R2_3_PASSED_SUBGATES: **hard diagnostics 0; standalone one page; visual collision gate passed**  
R2_3_BLOCKER: **page wrapper remains 3 pages (691/692/693 chain)**  
R2_3_NEXT_ACTION: **R2.4 合并外层状态带与输出台、压缩上层状态格/行距，并保持 9.6pt 与无整体缩放。**
