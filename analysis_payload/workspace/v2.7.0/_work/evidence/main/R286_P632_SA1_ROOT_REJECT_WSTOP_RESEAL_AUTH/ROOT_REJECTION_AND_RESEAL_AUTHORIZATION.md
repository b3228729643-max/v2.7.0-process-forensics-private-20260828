# R286 — P632 fresh SA1 内容PASS、WSTOP顺序拒收与重封授权

- 时间：2026-08-27T02:16:30+08:00
- UID=`FIG-P632-01`
- HANDOFF_ID=`C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-V1`
- actual instance=`/root/sa1_fig_p632_r110_fresh_isolated_v1`
- 原根=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa1_r110_fresh_isolated_v1`

## 裁决

- 内容PASS方向保留：N23/C253，人工objects23/pairs253/text29/critical9/glyph24/views9/hard gates22，hard failure/overlap/clip/unresolved均0，min clearance9px。
- ordinary48，manifest-bound payload46，duplicate/missing/extra/path/bytes/SHA mismatch=0；48/48文件及root/目录只读；JSON/CSV parse、ADS/cache/pyc/reparse均0；source与TeX边界保持。
- 决定性失败：WSTOP ticks=`639233654580842550`，manifest ticks=`639233654580892433`，manifest晚`49883` ticks；at-or-after excluding WSTOP=1，WSTOP不是唯一严格最新。
- 正式结论：`CONTENT_PASS_DIRECTION / ROOT_REJECT_WSTOP_ORDER`。原根永久只读，不修改、不原地重封、不重跑角色，不能用于SA3；P632保持SA1。

## 唯一一次 evidence-only readonly reseal 授权

- 新root启动前不存在；根外PowerShell7 controller经AST/identity静态门后invocation=1、retry=0。
- 仅复制原manifest绑定的46 material payload；旧`MANIFEST.json`与`WRITE_STOPPED`复制0。
- 逐项保持relative path、bytes、SHA-256、NTFS mtime ticks，source→destination mismatch=0。
- 新增仅`COPY_IDENTITY.csv`与`COPY_PROVENANCE.json`两个payload，provenance写resolved绝对roots；最终payload恰48。
- 新controls恰3个：覆盖48 payload的`PAYLOAD_MANIFEST.json`、`SEAL_AUDIT.json`、唯一最终`WRITE_STOPPED`；ordinary恰51。
- WSTOP前完成identity/count/parse/ADS/cache/pyc/reparse与payload/manifest/audit及目录只读门；WSTOP写入并设只读后根内0内容写。
- 根外只读auditor复算48 rows、dup/missing/extra/path/bytes/SHA/ticks差0；51/51文件和全部目录只读；WSTOP唯一严格最新、at-or-after excluding marker=0、postmarker0。
- 禁视觉/对象/pair/manual/语义重跑或修改；禁TeX/源码/Git/第二UID/SA3/central writes。

原report SHA=`2F261C50D4F53009A16F1525DF654E6FB70EF0AEA134B6F7188F1E7C376CB9E7`；handoff SHA=`78229630FAE200DD3241E2944CED4A8643648379553CCD0A6C09A21E5D9BC26A`；manifest SHA=`1603663F3E6A0AEAC0AB570753100BCDF04F833A5BE04AA4BBA6CBDB85DF5B12`；WSTOP SHA=`6EB000A064DA7D16D74E10FFA6A61A10B9E19E1EDE976348DDCF430A04BC6170`。

inventory保持`33 SA1 / 45 SA2 / 0 SA3 / 21 local pass`。
