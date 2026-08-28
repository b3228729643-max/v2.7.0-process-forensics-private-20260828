# FIG-P756-01 — root 对 R97 独立 SA1 的路由验收

- 角色结论：`ROOT_ACCEPTS_SA1_PASS_TO_FRESH_ISOLATED_SA3`
- 最终图状态：`NOT_CLOSED`
- 官方候选：`strict_current_r97_fullbook/main_full.pdf`
- PDF SHA-256：`062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`
- 图源 SHA-256：`00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA`
- 位置：物理页 801／印刷页 788／图 37.8
- SA1 证据：`STRICT_R15_SA1_REQUAL_R97_20260824`

## 根线程独立复核

1. 完整性：root 独立复算 `evidence_manifest.json` 的 1408 项与 `MANIFEST.sha256` 的 1409 项，missing、bytes 与 SHA-256 mismatch 均为 0；实际文件 1411 个，零字节文件 0，非默认 ADS 0，`WRITE_STOPPED.md` 为绝对最后写入，stop 后写入 0。
2. 分母闭合：253 个 rawdict 字符记录明确闭合为 251 个可见 glyph 与 2 个 non-ink 记录；25 个文字对象、44 个语义图形对象合计 69 个对象，全部 `C(69,2)=2346` 个无序关系闭合。图内 39 条 PDF drawing path 全部归属；本图没有显示数学规则，`GRAPHIC/MATH_RULE` 分母以 source/path 的 0↔0 对账明确闭合。
3. 逐字像素：root 实际打开 16/16 张 glyph contact sheet，共覆盖 251/251 字形；original、target overlay 与 mask-only 三视图未见缺笔、邻字或图形夹带。8 个低轮廓标点均有同字体、字号、颜色的独立校准与人工记录。
4. 图形对象：root 实际打开 11/11 张 graphic contact sheet，覆盖 44/44 图形对象；节点边框、箭杆、箭头、徽章 fill/border、双报告框与白色分隔均有非空唯一 mask，未见污染或遗漏。
5. 关系：root 实际打开当前 32/32 个关键关系五联卡，逐项查看原生 1×、双方唯一 mask、overlay 与 8× nearest。9 个箭杆—箭头组件、5 个徽章—节点边框叠放和 9 个端点接触均仅止于其逐项源码锚点；其余 9 个近邻关系未见接触。23 项 `INTENTIONAL_CONTACT` 仍是逐关系许可，不形成类别白名单。
6. 遮挡顺序：root 打开 G030/G031 四视图、双方 mask 与 8× nearest。最终深色双框 3890 px、白色分隔几何 3385 px、双方唯一 mask 交集 0；270 个候选深色像素按绘制顺序归属白色分隔，未掩盖文字或其他前景。
7. 整体视觉：root 打开官方 native 300 dpi 整页、300 dpi 图体、standalone、灰度与文字对象 overlay。图题、五站闭环、两条任务路线、共享引擎池、隔离验证及单向报告出口的阅读顺序一致；无图题/正文侵入、裁边或颜色依赖。普通文字最小 9.60 pt、面板标题 10.20 pt、全图 max/min=1.0625，字号、字重与页面融合协调。
8. 最终硬门：非法 overlap 0、clip 0、空 graphic mask 0、glyph 失败 0、字体 D/E 失败 0；底表、人工 ledger、索引、报告与最终机器交叉检查一致，`FINAL_MACHINE_CROSSCHECK.json` 的 errors 为 `[]`。

## 路由边界

本记录只接受 R97 独立 SA1 包并把 P756 从 `SA1` 路由到全新、隔离、只读的 `SA3`。它不是图件最终 PASS，不能增加严格完成计数；只有新的独立 SA3 从官方 R97 与当前图源自行重建完整证据并经 root 再验收后，P756 才可能关闭。SA3 不得读取或迁移本 SA1 包、本 root 结论、旧 P756 PASS、中央库存结论或历史人工标志。
