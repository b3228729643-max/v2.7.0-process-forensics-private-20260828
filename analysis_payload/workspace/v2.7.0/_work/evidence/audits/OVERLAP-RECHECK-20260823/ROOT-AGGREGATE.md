# 已接受绘图全量重审：根汇总

审查日期：2026-08-23  
协议：`STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`  
结论：**COVERAGE=28/28；PASS=22；FAIL=6；AMBIGUOUS=0。**

本汇总撤销旧验收文本对六个失败 UID 的放行效力。旧 ROOT-ACCEPTANCE 仅用于锁定实际接受 round、PDF/jobname/FLS 身份，不再作为视觉通过证据。审查均在原生 300 dpi 像素上完成；ROI 为 1:1 无缩放、无插值裁剪。若接受目录没有保存彩色 300 dpi 页图，但存在可锁定的同一接受 PDF/jobname/FLS，则只读从该 PDF 派生 300 dpi 页图，并标记 `DERIVED_FROM_ACCEPTED_PDF`，未重编译 TeX。

## 强制门

- 文字、公式与坐标轴、曲线、箭头、刻度、边框或其他独立实墨接触/覆盖：FAIL。
- 连续纯白净空 1--3 native px：FAIL；只有彩色页、灰度页、独立图相关区域均至少 4 px 才可通过。抗锯齿归属不能确定时记 AMBIGUOUS，不能写 PASS。
- 所有可见 node 的源级字号至少 9.6 pt；代表字形在 300 dpi 原图上量实墨 bbox。跨面板同类字形无解释差异超过 10%、无语义依据地大于中位数 1.25 倍或小于 0.85 倍、关键公式/警示超过普通文字 1.35 倍且造成视觉主导或拥挤，均 FAIL。
- 同时复核 CJK、Latin、数学字形的 x-height、字重、基线、行距和面板层级。不得用缩小字号、白底遮盖或整体缩放制造假净空。

## 28/28 汇总

| UID | 实际接受 round / jobname | 几何 | 字体层级 | 最终 |
|---|---|---:|---:|---:|
| FIG-P547-01 | R3 / `root_p547_*_r3` | FAIL | PASS | FAIL |
| FIG-P577-01 | R3.2 / `p577_root_r3p2` | FAIL | PASS | FAIL |
| FIG-P578-01 | R3.3 / `p578_root_r3p3` | PASS | PASS | PASS |
| FIG-P580-01 | R3.1 / `p580_root_r3p1` | FAIL | PASS | FAIL |
| FIG-P596-01 | R3.1 / `p596_root_r3p1` | PASS | PASS | PASS |
| FIG-P602-01 | R3 / `p602_root_r3` | PASS | PASS | PASS |
| FIG-P608-01 | R3 / `p608_root_r3` | FAIL | PASS | FAIL |
| FIG-P609-01 | R3 / `p609_root_r3` | PASS | PASS | PASS |
| FIG-P630-01 | R3 / `p630_root_r3` | PASS | PASS | PASS |
| FIG-P634-01 | R3 / `p634_root_r3` | PASS | PASS | PASS |
| FIG-P640-01 | R3 / `p640_root_r3` | FAIL | PASS | FAIL |
| FIG-P654-01 | R3 / `p654_root_r3` | PASS | PASS | PASS |
| FIG-P668-01 | R3 / `p668_root_r3` | PASS | PASS | PASS |
| FIG-P669-01 | R3 / `p669_root_r3` | PASS | PASS | PASS |
| FIG-P684-01 | R3 / `p684_root_r3` | PASS | PASS | PASS |
| FIG-P694-01 | R3 / `p694_root_r3` | PASS | PASS | PASS |
| FIG-P695-01 | R3 / `p695_root_r3` | PASS | PASS | PASS |
| FIG-P715-01 | R3 / accepted PDF+FLS | PASS | FAIL | FAIL |
| FIG-P716-01 | R3 / `p716_root_r3` | PASS | PASS | PASS |
| FIG-P717-01 | R3 / `p717_root_r3` | PASS | PASS | PASS |
| FIG-P721-01 | R3 / `p721_root_r3` | PASS | PASS | PASS |
| FIG-P736-01 | R3 / `p736_root_r3` | PASS | PASS | PASS |
| FIG-P737-01 | R3 / `p737_root_r3` | PASS | PASS | PASS |
| FIG-P740-01 | R3 / `p740_root_r3` | PASS | PASS | PASS |
| FIG-P745-01 | R3 / `p745_root_r3` | PASS | PASS | PASS |
| FIG-P748-01 | R3.1 / `p748_root_r3p1` | PASS | PASS | PASS |
| FIG-P750-01 | R3 / `p750_root_r3` | PASS | PASS | PASS |
| FIG-P756-01 | R3.1 / `p756_root_r3p1` | PASS | PASS | PASS |

集合核验：A 组 14、B 组 14，交集为 0，合并后与既往接受 UID 集合完全一致；无缺失、无重复。

## 六个撤销项的确定证据

1. `FIG-P547-01`：标签框下边界与金色弧线 0 px 接触；彩色页 `(665,683)/(665,684)`、灰度页同位、独立图 `(711,452)/(711,453)`。
2. `FIG-P577-01`：普通拒绝公式框与 `p(y)` 曲线 0 px 接触；独立图 `(1596,1027)/(1597,1027)`，彩色/灰度页 `(1554,1261)/(1555,1261)`。
3. `FIG-P580-01`：右图密度比第二行在说明框左右各溢出约 92--94 px，并侵入纵轴/`0.4` 刻度走廊；用户放大截图与三类原证据一致。
4. `FIG-P608-01`：上面板横轴与下面板标题上划线 0 px 接触；彩色/灰度页 `(1477,866)/(1477,867)`，独立图 `(1472,630)/(1472,631)`。
5. `FIG-P640-01`：金色曲线与 `N_eff/N→0` 标签最小距离约 2.24 px；独立图 `(1884,557)/(1885,555)`，彩色/灰度页 `(1884,647)/(1886,646)`，低于 4 px。
6. `FIG-P715-01`：几何由同一接受 PDF/FLS 只读派生的 300 dpi 彩页、原灰度页和正式 crop 一致确认 PASS；但全局/every node/edge note/note 为 9.5 pt，低于 9.6 pt 硬下限，故 TYPOGRAPHY=FAIL。

## 原对话完成项的附加双审

原对话标记完成的七图另由两名独立 subagent 分组复核：C 组覆盖 P547/P602/P608/P609，D 组覆盖 P630/P654/P715。合并 `COVERAGE=7/7`，无重复、无缺失；`PASS=4`（P602/P609/P630/P654），`FAIL=3`（P547/P608/P715），`AMBIGUOUS=0`。其结果与 28 图全量审查一致。

## 审查纠偏与中央处置

- A 组初看宽 ROI 时漏报 P608；C 组给出 1:1 紧 ROI 和相邻像素后，A 组在不读取 C 结论替代实检的前提下重新制作紧 ROI，独立复现 0 px 接触并纠正为 FAIL。由此固定后续流程：宽 ROI 只能定位，所有潜在交互必须另做紧 1:1 ROI 并记录原图坐标。
- 中央 `figure_manifest.csv` 的正式通过数由 28 撤回至 22；P547/P577/P580/P608/P640/P715 转入定向视觉/字体返修。数学、数值和变量一致性既有证据不因纯视觉撤销而失效。
- 其余 22 图保持通过，不重开、不重建。六个失败 UID 只有在新 SA2 修复、根构建与三类 300 dpi 像素检查、全新独立 SA1 和隔离 SA3 均通过后，才可恢复为“通过”。
- `FIG-P632-01` 不属于上述 28 个旧接受 UID；它是另行进行中的新闭环，继续按同一像素和字体协议处理。

## 权威明细

- `SA1-AUDIT-A.md`
- `SA3-AUDIT-B.md`
- `SA-ORIGINAL-C.md`
- `SA-ORIGINAL-D.md`
- `USER-REPORTED-FINDINGS.md`
- `STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`

RESULT: **22_PASS_6_WITHDRAWN_0_AMBIGUOUS**
