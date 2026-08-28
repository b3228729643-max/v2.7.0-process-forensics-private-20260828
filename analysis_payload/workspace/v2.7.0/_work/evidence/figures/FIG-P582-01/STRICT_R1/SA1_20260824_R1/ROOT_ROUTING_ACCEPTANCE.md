# FIG-P582-01 根线程路由验收

- 验收时间：2026-08-24T09:16:47+08:00
- 候选：官方 R95，物理页 595（图 31.7）
- 角色：独立严格 SA1（Terra/max），只读审查
- 根结论：`EVIDENCE_INTEGRITY_PASS=true`；`FIGURE_HARD_GATES_PASS=false`；`FAIL→SA2`

## 根线程独立复核

- 证据包封存后共有 1,540 个普通文件；0 个零字节文件、0 个不安全/ADS 名称。28 个 CSV 与 68 个 JSON 均可解析，1,329 个 PNG 均由根线程独立打开成功。
- 62 个对象由 45 个语义/文字对象与 17 个图形对象构成；全无序 pair 为 `62 choose 2 = 1,891`，必审关系为 1,686，覆盖与唯一性闭合。
- 139/139 个可见字形均有 final raw mask、`ORIGINAL / TARGET OVERLAY / MASK ONLY` 证据和逐格人工 ledger；12/12 张 final contact sheet 已由根线程逐张打开核看。
- revision 111 低轮廓标点覆盖 21 个目标：校准失败 2、源字号下限失败 11、合计硬门失败 13；没有把句点/分号机械套用 22px/30px。
- 45 个文字元素中源字号失败 29；139 个字形中像素/校准失败 6，源字号或像素合并失败 68。实际 final-mask `H_INK` 的 D 门失败 3、E 门失败 2；字体视觉协调失败。
- `P0717` 的 E014 向下箭头与 E016 `.380` 末位 `0` 在原生 300dpi raw mask 中真实共享 3px，净空为 0px（要求 4px）。根线程已打开双方 mask、交集、overlay 的 1:1 与 8× nearest 包；这是图中真实碰撞，不是 mask 污染。
- clip 失败为 0；这不能抵消字号、像素、协调、D/E 与真实碰撞硬门失败。
- `machine_terminal.json` 的 `issues=[]`，终态与底层表一致；初始两份 raw glyph ledger 已明确标为 `SUPERSEDED_INITIAL_RAW`，不参与最终完整性计数。`WRITE_STOPPED.md` 为目录最后写入。

## 路由

FIG-P582-01 从 `SA1` 转入唯一业务源码写者串行 `SA2` 队列。不得迁移任何 PASS 字段；修复后须生成新的非覆盖证据、进入新的官方候选，并由全新独立 SA1 重新审查。

