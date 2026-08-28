# FIG-P715-01 R107 fresh isolated SA3 主线验收

- revision: `241`
- accepted_at: `2026-08-26T15:55:20+08:00`
- verdict: `MAIN_SCOPE_ADJUDICATION_ACCEPT / SA3_PASS / A_LOCAL_PASS`
- strict_final_book_pass: `false`

## 角色与候选身份

- HANDOFF_ID=`A-R107-P715-SA3-FRESH-ISOLATED-20260826`
- actual instance=`/root/p715_r107_fresh_sa3`
- model/effort=`gpt-5.6-sol/xhigh`
- fork_turns=`none`
- R107 PDF=`817 pages / 4,967,249 bytes / 8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`
- 当前P715单源=`4,057 bytes / 900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`
- 独立定位 physical page `765` / printed page `752` / Figure `36.2`。

## 业务与证据闭合

- SA3以保守边界纳入39个题注glyph：`255 glyph + 43 drawing = N298`，`C(298,2)=44,253`。SA1的N259只排除题注；该粒度差异已独立解释，不构成对象漏计或角色污染。
- glyph/drawing ID分别`255/255`、`43/43`唯一；对象并集298。pair行44253、pair ID唯一44253、unordered key唯一44253、membership/self-pair失败0，故全无序pair闭合。
- machine candidate=0；独立最小实墨净距`9.434px>4px`。四个零距离drawing关系分别为focus覆盖本格、边连接node、矩阵共享格线、shaft与arrowhead连接，人工逐项确认为合法结构。
- 实际打开8 glyph sheets、2 drawing sheets、4主视图与8关系图后，人工ledger为glyph255、drawing43、relation8、view/sheet/relation22；全部PASS、空note0、ID差0。
- 题注中两个不同位置的同字U+673A“机”使用相同短note；它们的ID、char_index、bbox、sheet/cell均不同，其余253条不同。该单个同字描述重复不是批量模板，也不构成人工账缺口。
- 主线实际打开整图、灰度、题注contact与最小净距ROI，确认无tofu/错码/不可读/严重失衡/真实裁切/非法重叠；A/M/P矩阵、四条边、列归一、转置桥与随机游走语义正确。R168微小字体/像素差异仅advisory。

## 封存机械门

- common payload=`648 files / 16,076,880 bytes`；双manifest各648行且set/row完全相同，SHA均=`25228F346ED6B65B3000C9199404779F678D2AF760B4B029DA7DBB0F20FA5D2C`。
- manifest→FS path/bytes/SHA missing/extra/duplicate/mismatch均0；CSV/JSON解析失败0；620张PNG全部可打开。
- ordinary=`651=648 payload+2 manifests+WRITE_STOPPED`；`651/651`普通文件只读，writable0；ADS/cache/pyc/reparse0；WSTOP唯一最新且其他文件mtime>=WSTOP为0。
- 正式report SHA=`65B0D720DD94A6839F0D6DAC4EC4AD1F7F2ABA6B3F076B1B5C499D2AF7559D39`；handoff SHA=`5DEF2DE457787C1DEFA6F3F40300AB63852DB0BBDC1EF741A896C615B8DB0A11`。

## 范围裁决

独立root auditor复算后仅因sealed根目录对象的Windows DOS `ReadOnly` bit为false而给出REJECT；其余门全部通过。主线不接受该额外条件：Goal、A任务包与既有中央口径要求的是普通文件全只读、manifest身份闭合、WSTOP最后及封后0写，并未要求目录DOS属性。Windows目录ReadOnly位也不是写权限控制，不能替代或增强上述真实封存门。因此该审计派发附加条件被裁定为超范围，不触发无意义的复制重封。

FIG-P715-01 正式由 `SA3 → A_LOCAL_PASS`。禁止重复P715 SA1/SA3、SA2返修、TeX或源码修改。全书严格最终仍为`0/99`。

