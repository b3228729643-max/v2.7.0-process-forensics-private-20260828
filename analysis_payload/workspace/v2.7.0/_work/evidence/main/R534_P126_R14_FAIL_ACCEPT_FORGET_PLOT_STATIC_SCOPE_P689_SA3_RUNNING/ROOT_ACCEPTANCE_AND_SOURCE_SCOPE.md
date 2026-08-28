# R534：P126 R14 sealed FAIL 接受与最窄 `forget plot` 静态范围

时间：2026-08-28T16:40:47+08:00

## 主线裁决

- 正式接受 HANDOFF `A-R115-P126-SA2-DIRECT-BUILD-R14-20260828` 的 sealed 业务结果：`LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`。
- 唯一 hard defect 为 `HARD-LEGEND-X2-CONTINUOUS`。P126 保持 SA2，不计 local pass。
- R14 PDF、sealed root、root-external report/handoff/controllers/results 从本裁决起冻结；不得重跑、改写、重封、retimestamp 或作为新的业务输入。

## 独立根与人工账验收

- 唯一 PDF：34,054 bytes，SHA-256 `204CC34980BF059DFFA4016314C1FBFEFC94A0066C01FF7E77A4A26946B65F3D`。
- sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R14_SA2_DISCONNECTED_LEGEND_HANDLER_R115_DIRECT_BUILD_20260828`。
- files=134；dirs including root=11；payload=130；CSV/JSON 两份 manifest 均为 130 rows。duplicate/set/path/bytes/SHA/CreationTimeUtc/LastWriteTimeUtc mismatch 全 0；134/134 files 与 11/11 dirs/root ReadOnly。
- `WRITE_STOPPED` 为 1,167 bytes/SHA-256 `DDF5BD361BE7DED15E23187BC60505C77D6E17A500384923FEF877346965BC13`；27 physical lines/27 unique keys，bad/duplicate/BOM/binding mismatch 0。Main 逐项复算的含 root strict-latest margin 为 2,999,565,647 ticks，at-or-after excluding marker=0；与 handoff 展示值相差 14 ticks，不改变严格序关系或任何身份门。postmarker content/attribute drift=0；CSV/JSON parse、ADS、cache/pyc、reparse=0。
- N60/C1770；machine pair skeleton 与 manual pair ledger 的 ID/tuple/order 完全一致，unique1770、自配对0、坏引用0、blank0；manual objects60（PASS59/FAIL1），pairs1770 全 PASS，views15、glyph/codepoint25、math-semantic10、hard ledger1。
- 唯一被通用空字段检查命中的字段是 hard ledger 的 `NATIVE300_INTERNAL_BLANK_LENGTHS_PX`。同一行明确记录 `NATIVE300_INTERNAL_BLANK_RUNS=0`，其 JSON 数组也为 `[]`，因此该空值是“没有内部空白段”的规范空列表表示，不是漏填。
- native300 x2 legend occupied run 恰 1 个，x=1258..1330、length=73px；internal blank run=0。Main fresh Poppler render与A证据一致，实际打开的 legend 图显示 x1/x2 两条样线均为灰色连续线。
- 外部 final report 2,827 bytes/SHA-256 `54DE2A2ACAEB3AABFCC498CC6AF60C0127C82B00228D264EE20BFEC6085EDA5C`/ReadOnly；final handoff 1,648 bytes/SHA-256 `600604FC6D01198C33B7EA4552294B00AC0FCEB9023787CCB4C93702504C0F34`/ReadOnly。

## 新的决定性因果定位

- 当前 sole source 为 4,626 bytes/SHA-256 `6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`。
- 两条 manual `\addlegendimage` 之前存在 5 条实际 `\addplot`：四层灰色 contour 与一条 square-marker plot；五者都没有 `forget plot`。
- installed pgfplots primary source `pgfplotscoordprocessing.code.tex` lines 3716--3720 表明：普通 plot 会调用 `\pgfplots@rememberplotspec`，`forget plot` 才只保留 label 信息而不进入 legend plot-spec list。
- `pgfplots.code.tex` lines 5794--5796 表明 `\addlegendimage` 也向同一 plot-spec list 追加条目；lines 5721--5739 与 5760--5768 按顺序把 plot specs 与已有 legend entries 配对，并以较小数量截断。
- 本图只有 2 条 legend entries，但在 manual images 前已有 5 条普通 plot specs；所以最终 legend 实际消费的是前两条灰色 contour spec，而不是后面的 blue/x2 custom specs。这同时解释了两条样线均灰且连续，也解释了多轮修改 x2 handler 后 PDF 图例仍完全不变。

## 唯一授权的 STATIC_ONLY source scope

仅授权 A 在当前 sole source 的以下 5 个既有 `\addplot[...]` option list 中各加入一次 `forget plot`：

1. 四层 contour plots（当前 lines 20、22、24、26）；
2. square-marker plot（当前 line 56）。

除此之外全部冻结：五条 plot 的 domain/coordinates/colors/line widths/marks、全部 q0--q7/contours/arrows/markers/labels/backgrounds、两条 `\addlegendimage` 与 disconnected handler block、legend entries/style、fonts/axis/layout/math/caption/label/alt/shared macros/build entry及任何第二文件。不得删除、移动或改写现有 disconnected handler。

A 必须先返回 sealed `STATIC_ONLY_NOT_RENDERED_NOT_PASS`：当前 source 身份、after 身份、精确 5 处增量、内存反向重构、`forget plot` 对 5 个既有 plot-spec 的静态因果证明、工作树边界与合法 control seal。未授权 TeX/build/commit/fresh role/second UID/central write；Main 接受静态根后才会另行决定是否释放唯一 direct LuaLaTeX 槽。

## 并行边界

- P689 保持同一 fresh SA3 `/root/sa3_fig_p689_r115_fresh_isolated_v1`，未计 local pass；继续只等待一个 sealed PASS/FAIL。
- inventory 不变：`30 SA1 / 30 SA2 / 1 SA3 / 39 local pass`；strict final `0/99`，B `66/66`。

