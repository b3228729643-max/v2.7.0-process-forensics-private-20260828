# R373 P067 R7 local acceptance and P662 SA3 control adjudication

时间：2026-08-27T17:29:00+08:00

## P067：接受 R7 LOCAL_SA2_PASS，并授权唯一原子提交

- 接受 `A-R112-P067-SA2-DIRECT-BUILD-R7-20260827` 的新 PDF 业务与封存结果为 `LOCAL_SA2_PASS`。目标源仍唯一为 `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`，4014 bytes，SHA-256=`2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`；唯一差异为 `const plot mark right` → `const plot mark left`，1+/1-，index 空，diff-check PASS。
- 主线独立机械复算：payload135、ordinary139；CSV/JSON manifest 均135行且与 FS path/bytes/SHA/NTFS ticks 差0；139/139 files、13/13 dirs/root ReadOnly；JSON/CSV parse、ADS、prohibited cache、reparse均0。WSTOP exact ticks=`639234192033231040`，max other file=`639234192032231038`，严格最后+1,000,002 ticks；max directory=`639234192032730524`，仍早于marker 500,516 ticks；at-or-after0/postmarker0。外部报告中的浮点margin 1,000,064与exact ticks有62 ticks显示漂移，不影响严格时序门。
- machine N115=65 glyph+50 path、C6555；manual object115/relation16/view16全PASS，pair table6555 unique/self0/orderbad0。主线实际打开standalone、CDF/PMF native与8x、y-ticks native/8x、grayscale，确认CDF区间 `[.5,1):0`、`[1,2):.15`、`[2,3):.45`、`[3,4):.80`、`[4,4.5]:1`，open/filled endpoints、PMF质量与右连续一致；相邻PMF刻度清楚分离，1px native间距仅R168 advisory。
- 授权A在 `v2.7.0/dialogue-a-visual` 上创建恰一个原子commit：只允许上述P067目标源，name-only恰该文件、numstat恰1+/1-、subject=`fix(fig-p067): align CDF steps with right-continuous values`；提交前diff-check，提交后worktree/index clean，禁第二commit、push、TeX、fresh role、第二UID与central写。提交后仅回传commit/parent/source identity及不可变handoff，等待主线集成与新官方候选。

## P662：内容PASS方向保留，原SA3根因WSTOP格式拒收

- `C-FIG-P662-01-R112-SA3-FRESH-ISOLATED-V1` 的fresh业务内容方向经主线独立复核无反证：N26/C325，manual objects26、pair IDs P001--P325共325 unique且无缺号、text/glyph31、views20、geometry10、hard gates8。机器3项nonzero/196px均为simplex containment、composite-mask attribution或合法endpoint；illegal overlap/clip/tofu/wrong codepoint/unreadable/math-semantic-geometric error/unresolved均0。
- 主线实际打开full page、figure+caption、grayscale、semantic overlay及simplex/aux/fan-in/result/bottom/sum六组nearest8x ROI；结构连接、公式、文字、灰度与页面融合无内容反证。
- 原root机械内容身份闭合：manifest37、payload37、ordinary39，duplicate/missing/extra/unlisted/path-bytes-SHA-creation-lastwrite FILETIME差0；39/39 files与root ReadOnly，parse/ADS/cache-pyc/reparse0；WSTOP严格最后+23,598,377 ticks、at-or-after0/postmarker0。
- 决定性控制失败：`WSTOP.txt`物理行数1，把六个`KEY=VALUE`以空格拼接。严格“一物理行一个assignment”解析只有1个key，required六键仅1/6精确。因此正式裁决 `ROOT_REJECT_MALFORMED_SINGLE_LINE_WSTOP`；不得把原root计为C_LOCAL_PASS，不得原地修补/reseal/retimestamp。

## P662：授权一次 sibling evidence-only control reseal

- 唯一授权HANDOFF=`C-FIG-P662-01-R112-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1`；新root固定为 `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa3_r112_fresh_isolated_v1_control_reseal_v1`，执行前必须确认file/dir均不存在；controller/auditor须root-external PowerShell7、AST0、invocation1/retry0。
- 只复制原manifest绑定37项material，旧MANIFEST/WSTOP复制0；新增resolved `COPY_IDENTITY.csv` 与 `COPY_PROVENANCE.json` 后payload39；controls恰 `PAYLOAD_MANIFEST.csv`、`SEAL_AUDIT.json`、resolved multiline `WRITE_STOPPED`，最终ordinary42。
- 复制与新manifest必须逐项闭合relative/resolved path、bytes、SHA、creation+lastwrite FILETIME；duplicate/missing/extra/unlisted差0，旧root zero-write。WSTOP必须每物理行恰一个`KEY=VALUE`，至少精确绑定HANDOFF_ID、UID、SEALED_ROOT、MANIFEST_ROWS=39、MANIFEST_SHA256、VERDICT；禁止placeholder、TAB、`rue`、孤立value或单行拼接。
- 新root全部files/dirs/root ReadOnly，唯一WSTOP绝对最后，at-or-after0，postmarker content+attribute0；JSON/CSV parse、ADS/cache-pyc/reparse0；root-external只读auditor复算。严禁重跑PDF/render/visual/object/pair/manual/math/semantic、TeX/source/Git/central、fresh role、第二UID。
- 只有主线独立接受该control reseal后，P662才可计 `C_LOCAL_PASS`；此前保持SA3并冻结业务内容，不启动下一UID。

inventory更新为 `31 SA1 / 38 SA2 / 1 SA3 / 30 local pass`：仅P067新增LOCAL_SA2_PASS；P662仍为待控制重封的SA3。
