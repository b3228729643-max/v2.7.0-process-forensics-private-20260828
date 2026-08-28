# FIG-P748-01 / ROOT-APPLY-R3.1

**RESULT: PASS_LOCAL_PENDING_POSTFIX_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 触发与数学纠偏

- 初始 R3 的隔离 SA3 发现唯一真实阻塞：标准 Adjusted Rand Index 可为负，稳定性卡却无条件写成 `ARI [0,1]`。其四对象交叉分组反例给出 `ARI=-1/2`，故原范围会排除合法结果。
- 同一专属 SA2 在 R2.1 中只改稳定性卡与源级 alt：保留 `ARI↑` 和 `中位数＋IQR`，把错误范围改为 `无量纲；可为负`；不声明固定精确下界，也不引入截断、平移或归一化变体。
- 根线程同步 source JSON 对象级 alt；其余四卡、五卡结构、微图、结论条、caption、label、正文、wrapper 与中央身份均未改变。
- 初始 R3 的 SA1 PASS 与 SA3 FAIL 均作为历史证据保留，不用于放行修正后的对象；R3.1 必须重新取得 post-fix SA1 与 SA3 双 PASS。

## R3.1 构建与机器门

- 使用 TeX Live 2026 LuaLaTeX 在新 jobname 下重建，未覆盖初始 R3 PDF/PNG。
- `p748_root_r3p1_page.pdf`：66,679 bytes，A4 单页；AUX 为图 37.6、页 745。
- `p748_root_r3p1_standalone.pdf`：52,994 bytes，A4 单页。
- 两份最终日志硬诊断均为 0；page 的 5 个字体与 standalone 的 4 个字体全部嵌入、子集化且具 Unicode 映射。
- 两份 FLS 均回指当前 v2.7.0 wrapper 与修正后的 `evaluation_dashboard.tex`；PDF 文本层明确含 `ARI↑`、`无量纲；可为负`、`中位数＋IQR`。
- source JSON 的 canonical/legacy/label 身份桥仍唯一，alt 已同步“ARI 向上、无量纲且可为负”；本图仍无 numeric manifest 记录。

## R3.1 视觉门

- 已实看 `p748_root_r3p1_page_300dpi.png`、`p748_root_r3p1_gray_page_300dpi.png` 与 `p748_root_r3p1_standalone_300dpi.png`；三图均为 2481×3508、300 dpi。
- 稳定性卡的新文字在 40 mm 等宽卡内完整显示，无换行溢出、碰框、遮挡或裁切；ARI、无量纲/可为负与中位数/IQR三层清楚。
- 其余四卡、五类微图、联合报告条、caption 和专属读图检查保持清晰；灰度纹理与线型冗余未回归。

## 根级结论

SA3 的 B1 已在源码、对象级 alt、双 PDF 文本层和三视图中闭环消除。当前 R3.1 通过根级局部门，中央 CSV 保持 `待独立复核 / RESOLVED_EVIDENCE_CLEAR`；须等待新的 post-fix SA1 与隔离 SA3 双 PASS 后方可最终接受。tagged PDF/ActualText 仍不属于本轮权威硬门。
