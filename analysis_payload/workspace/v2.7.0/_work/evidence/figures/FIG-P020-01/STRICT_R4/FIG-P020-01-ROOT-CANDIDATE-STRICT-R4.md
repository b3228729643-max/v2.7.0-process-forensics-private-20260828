# FIG-P020-01｜根线程严格候选检查（R4，官方全书页）

- CANDIDATE_ID: `FIG-P020-01-STRICT-R4-OFFICIAL-R89`
- RESULT: **WITHDRAWN_AFTER_INDEPENDENT_SA1_FAIL**
- SA1_RESULT: `FAIL_ROLE_RATIO_AND_HARMONY`
- SA3_RESULT: `NOT_STARTED`
- CLOSED_FOR_THIS_CANDIDATE: `NO`

R3 因关系节点内局部 `\to` 的原生 300 dpi 实墨仅 21px 而失败。SA2 在严格白名单内仅将该箭头从 13.5pt 调为 14.5pt；R4 当前官方连续页实测为 23px。新独立 SA1 证明该做法引入新的角色比例与视觉协调失败，因此撤回本根候选结论。

## 正式构建与证据

- 官方增量全书：`build/strict_current_r89_fullbook/main_full.pdf`。
- 构建结果：813 页、A4、4,933,622 bytes；索引及 LuaLaTeX 收敛完成。
- 最终日志中 `LaTeX Error`、Package Error、`Float(s) lost`、`Undefined control sequence`、`Emergency stop`、Fatal、未定义引用、重跑提示、overfull h/vbox 均为 0。
- AUX 将本图记录为图 1.1、印刷页 4；真实物理页为 17，已抽取为 `fullbook_page_17.pdf`。

## 严格硬门

- 字号源级：13/13 PASS；最低一般有效字号 9.9626pt，节点标题 10.4608pt，箭头 14.4458pt。
- 原生像素：13/13 PASS；CJK 主体 35--40px、图注编号 26px、局部箭头 23px。
- overlap/clearance/clip：26/26 PASS；非法重叠 0px、裁切 0px、全局记录最小净空 14px。
- 已覆盖四个节点的标题—正文、文字—边框、文字—三段连接箭头，关系节点左右文字—`\to`，逆向注记—虚线路径，注记—图注，图注各部分、图注—后文、前文—图，以及页面/图裁/standalone/灰度边缘。
- 原始 1:1 彩色图裁、测量叠加、灰度连续页均未见文字—文字、文字—箭头/边框、裁切或字号突兀；逻辑方向、题注和后续读图说明一致。

## 页面稳定性

同一次官方构建中，已严格关闭的 P632（物理页 680）和 P756（物理页 801）相对各自 `STRICT_FINAL` 300 dpi 连续页均为逐像素差异 0，因此本次 P020 改动未使其页面证据失效。

独立 SA1 已判 FAIL：箭头有效字号/普通正文比为 1.450003，超过允许角色上限；箭头实墨/相邻 CJK 字高仅 0.6216。下一步必须返回 SA2，以图形箭头替代放大的文本 `\to`，生成 R5 后从头复核。R4 不得进入 SA3 或 `STRICT_FINAL`。
