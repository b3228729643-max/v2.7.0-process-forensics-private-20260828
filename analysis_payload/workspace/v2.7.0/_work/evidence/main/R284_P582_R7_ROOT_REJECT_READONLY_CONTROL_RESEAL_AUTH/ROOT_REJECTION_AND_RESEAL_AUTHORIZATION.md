# R284 — P582 R110 R7 根拒收与一次 evidence-only 重封授权

- 时间：2026-08-27T02:04:30+08:00
- UID=`FIG-P582-01`
- HANDOFF_ID=`A-R110-P582-SA1-FRESH-ISOLATED-20260827`
- actual instance=`/root/p582_r110_fresh_sa1`
- 旧根=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7_SA1_FRESH_ISOLATED_R110_20260827`

## 主线裁决

- 内容PASS方向保留：R110 physical632/Fig31.7，44 objects、946 unordered pairs、139 glyph、35 critical、13 view-role；overlap/clip/clearance hard failure=0，语义与整页融合PASS。
- 主线已在R280打开R110官方整页、图体和“↓ 再下降”/`.380`目标局部，无真实硬缺陷反证；等号微轮廓仅R168 advisory。
- R7 manifest声明的140 payload与FS path/bytes/SHA归一化差0；payload bytes=4,733,173；PNG116 parse0；ADS/cache/pyc0；WSTOP严格最新且at-or-after0。
- 但实际payload readonly=0/140、controls readonly=0/3、ordinary readonly=0/143，root与全部子目录也可写。报告的read-only PASS声明与FS冲突，是决定性控制缺口。
- 正式结论：`ROOT_REJECT_R7_READONLY_CONTROL / CONTENT_PASS_DIRECTION_PRESERVED`。R7永久禁止修改、原地freeze、retimestamp、reseal或用于SA3路由；P582保持SA1。

## 唯一一次重封授权

- 允许创建一个启动前不存在的全新 evidence-only control reseal root；禁止第二次调用、retry或原地修补。
- 只从R7 manifest绑定的140 material payload复制；旧manifest/checksum/WSTOP三个controls复制0。
- 逐项保存并回读140 material的relative path、bytes、SHA-256、NTFS mtime ticks，source→destination mismatch=0。
- 新增且仅新增两个payload controls-data文件：`COPY_IDENTITY.csv`与`COPY_PROVENANCE.json`（resolved绝对source/destination roots）；因此新payload恰142。
- 新控制文件恰3个：覆盖142 payload的`PAYLOAD_MANIFEST.json`、写前闭合的`SEAL_AUDIT.json`、唯一最终`WRITE_STOPPED`；最终ordinary恰145。
- 写WSTOP前完成payload/manifest/audit的身份、数量、parse、ADS/cache/pyc/reparse、全文件与全目录read-only门；WSTOP写入并设只读后，根内不得再创建/修改内容。
- 根外只读auditor复算：142 manifest rows、duplicate/missing/extra/path/bytes/SHA/ticks差0；145/145文件及全部目录只读；WSTOP唯一严格最新，at-or-after excluding marker=0，postmarker writes0。
- 禁止任何PDF/视觉/对象/pair/manual/语义重跑或修改，禁止TeX/源码/Git/第二UID/SA3/中央状态写。

旧根外reject report SHA=`E27C9538C8BD0B4E2B3B21C5C455631AF591BFA4B2E0708A12748CE7CAD6930A`；handoff SHA=`3C359E486343FC3E0CA08F42444A3383F16D9E92E0364CB36D319C1CB2A76162`。

inventory保持`33 SA1 / 45 SA2 / 0 SA3 / 21 local pass`；严格最终0/99。
