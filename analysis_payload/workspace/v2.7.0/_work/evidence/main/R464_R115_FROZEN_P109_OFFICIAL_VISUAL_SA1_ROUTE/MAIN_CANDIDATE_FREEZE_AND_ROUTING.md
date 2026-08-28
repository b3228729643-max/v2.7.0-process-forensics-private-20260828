# R464 — R115 candidate freeze, P109 official visual acceptance, and P680 control reseal route

时间：2026-08-28T05:30:37+08:00

## R115 唯一构建闭合

- R463授权的唯一父调用自然`exit 0`，wrapper result=`PASS`；无retry、Resume、第二父调用、并发TeX、进程中断、源码或Git写。
- 同一latexmk父链内部自然执行三遍LuaLaTeX与两条makeindex规则；主索引`731 accepted / 0 rejected / 0 warnings`，符号索引`355 accepted / 0 rejected / 0 warnings`。
- 终态`latexmk/lualatex/luatex/luahbtex=0/0/0/0`，R115 build lock正式释放。
- Main repo branch=`v2.7.0/integration`，HEAD=`bd6efc7eaef9fc8fff82919e89934b60c2e2cbcf`，worktree/index clean。

## 冻结 R115 身份

- PDF=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf`
- bytes=`4,967,161`；SHA-256=`93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`
- pages=`817`；全部页面A4 `595.276 x 841.89 pt`、rotation=`0`；PDF1.7、encrypted=false、JavaScript=none、suspects=none。
- navigation=`273` bookmarks（5册、37章、符号索引、主题索引），named destinations=`7,421`，links=`4,961`，result=PASS。
- fonts=`17/17` embedded、subset、Unicode mapped，missing-character log matches=`0`；终稿包含`TOWNOR+IBMPlexMath-Regular`，构建输出中的cache reload仅advisory。
- `main_full.log`=`260,299` bytes/SHA=`4F86A496FF2BF28943D0CDCCA5111AFAE29D91F48523B7F575AF7B392532D1C3`；fatal/emergency/LaTeX-package error/undefined control-reference-citation/rerun/over-underfull/missing character/duplicate-unreferenced destination/final font-not-found均`0`。
- `main_full.toc`=`118,583` bytes/SHA=`EA5F09079A670A22A63FF08CDD061A3106E3999994963A9FBBD61CEC1C7E560D`；`main_full.ind`=`23,734`/`B32C889C28CAE7E4D6D7BB209D544715497AC7567C55435B9EF8B9851E7AB472`；`symbols.ind`=`25,820`/`E62CD6894BACCB383FAB12A058B9F83C91BE89AE6687104CF8D89E19CB7BC49A`。

R115自本记录起成为唯一正式候选；R114保持不可变历史输入。

## P109 官方页主线验收

- 当前P109 source=`1,922` bytes/SHA=`887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355`；current exact V1-C07 chapter=`56,386` bytes/SHA=`7E3B9DD542327B56022FE6E8358ABD3F87F81386CF5D9CD609DC0A7B0E532E37`。
- 由R115当前页面文本与题注独立定位physical page`116` / printed page`103` / Fig.`7.1`。
- Main实际打开R115 full-page300、figure+caption native300、grayscale300、domain-label native300与nearest-neighbour8x；图、题注、相邻正文和页面融合均完整。
- R114中set boundary真实穿过数学字形`C`；R115白底完整遮蔽该段，中文、`C`与`y`清晰，边界在保护区两端自然续接，无clip、tofu/错码、非法实墨重叠、不可读、严重失衡、语义或几何回归。
- R114→R115 physical116整页300dpi像素差：image=`2481x3508`，changed pixels=`8,084`，changed bbox=`(1569,1610)-(1767,1661)`，bbox外changed pixels=`0`。差异严格局限于domain-label保护区。

P109维持`LOCAL_SA2_PASS`/inventory SA2，直至新R115 fresh角色返回。

## P109 fresh R115 SA1 授权

- 授权A启动恰一个`gpt-5.6-sol/xhigh/fork_turns=none` completely fresh isolated SA1：HANDOFF_ID=`A-R115-P109-SA1-FRESH-ISOLATED-20260828`，requested actual=`/root/p109_r115_fresh_sa1`，new root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4_SA1_FRESH_ISOLATED_R115_20260828`。
- Parent immediate gate已确认new root Leaf=false、Container=false、Any=false、Parent=true；child必须在任何artifact前独立复证并只创建一次。
- Fresh prompt只可含exact R115/current P109 source/current exact V1-C07/Goal-direct protocol-schema；不得暴露或读取R3 local SA2、R114 SA2、任何旧P109页号/N/C/pair/pixel/metric/verdict/acceptance/root/evidence/report/handoff，亦禁其他UID、Main state/history/Git/chat、目录级search/enumeration/glob/fallback及agent/thread/task状态工具。
- PDF/main/source只读；TeX/build/source/Git/central/process management/second UID/second P109 role=`0`。必须独立定位R115、冻结完整visible denominator/all unordered pairs、实际打开native1x/NN8x/grayscale/page evidence、写真post-observation manual并一次seal。

## P680 SA3 原根拒收与control reseal授权

- 原HANDOFF=`C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-V1`业务内容保持PASS方向：physical729/printed716，N14/C91，manual objects14/pairs91/glyph15/math3/semantic9/page1，hard/clip/illegal/unresolved0。Main实际打开native figure与warning+caption NN8x，无视觉反证。
- 原root manifest payload37/ordinary39、identity0差、39/39 files与5/5 dirs/root ReadOnly、marker含root strict-latest、postmarker0；但`meta/WRITE_STOPPED.txt`物理8行中首行是裸`WRITE_STOPPED`，严格每行一assignment解析bad lines=`1`。故原root正式`ROOT_REJECT_MARKER_SYNTAX`，永久冻结，不计C_LOCAL，不原地repair/reseal/retimestamp。
- 仅授权C执行恰一次startup-absent sibling evidence-only control reseal：HANDOFF_ID=`C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1`，operation=`P680_R114_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V1`，new root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1_control_reseal_v1`；Main gate Leaf=false、Container=false、Any=false、Parent=true。
- 只复制旧manifest绑定37 material，旧manifest/WSTOP复制0；保持relative path/bytes/SHA/Creation+LastWrite FILETIME逐项一致。新增resolved `COPY_IDENTITY.csv`+`COPY_PROVENANCE.json`后payload39；controls恰`PAYLOAD_MANIFEST.csv`+`SEAL_AUDIT.json`+`WRITE_STOPPED`，ordinary42。
- Controller/auditor必须root-external、PowerShell7 AST0、empty-safe、delete/retry-loop/TeX/process-management0；controller invocation1/retry0/首错停。WSTOP在root外完成内容与严格解析，每物理行恰一nonempty `KEY=VALUE`、无bare header/BOM/TAB/placeholder，先ReadOnly并设future FILETIME，再唯一final move；严格晚于files/dirs/root，at-or-after0，postmarker content+attribute0。旧root零写。
- 禁PDF/render/visual/N/C/pair/manual/math/semantic重跑；禁TeX/source/PDF/Git/central/process/second UID/second role。仅在Main接受新control root后方可裁决P680 C_LOCAL_PASS。

## Inventory boundary

在两条actual/控制结果回传前维持`31 SA1 / 33 SA2 / 1 SA3 / 35 local pass`；严格最终仍`0/99`，B仍`66/66`。候选构建、局部视觉与内容PASS均不等于Goal完成。
