# R370 P067 R112 static handler patch 接受与唯一 direct build 授权

时间：2026-08-27T17:00:21+08:00

## static source 独立验收

- HANDOFF_ID：`A-R112-P067-SA2-STATIC-CDF-STEP-HANDLER-20260827`。
- A worktree：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual`；branch=`v2.7.0/dialogue-a-visual`，HEAD=`ab199fc685753015c3aa4d930ea1217e80aedf63`。
- 唯一source：`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`；当前4,014 bytes/SHA=`2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`。
- 主线独立Git复算：worktree恰1个modified file、numstat1+/1-、index empty、`git diff --check` exit0；唯一diff为`const plot mark right`改成`const plot mark left`。坐标、filled/open endpoints及其他源行零变。
- before身份4,015 bytes/SHA=`C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`；反向单token替换恢复baseline，且实际diff证明其余字节未变。
- 区间证明闭合：left handler与冻结坐标产生`[.5,1):0`、`[1,2):.15`、`[2,3):.45`、`[3,4):.80`、`[4,4.5]:1`；与PMF累计、既有open/filled endpoints、右连续和题注一致。此仅为静态机制证明，像素回归仍必须由新PDF完成。

## static evidence root 验收

- root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R6_SA2_STATIC_CDF_STEP_HANDLER_R112_20260827`。
- payload4、controls3、ordinary7；manifest4行，duplicate/missing/extra/path/bytes/SHA/mtime .NET ticks mismatch0。
- 7/7文件与root ReadOnly；JSON/CSV parse0，ADS/reparse0。
- WSTOP ticks=`639234177829868761`，max other=`639234177779561374`，严格最后margin=`50,307,387` ticks，at-or-after excluding marker0。
- manifest SHA=`1F381F7CF60FB624A5A1453450728DF8F566A71778CDEDED94EC9206D0D4678E`；PRESEAL SHA=`2E3B9831C96A73639BAA86DDF5D9895E7BA68217BCCC5CB23ECEB7F1A8E09AA6`；WSTOP SHA=`395C749860638D00EC8412F33B55D4AE660788CEADC1406EE43E61DEB215D1CC`。
- report 2,893 bytes/SHA=`7597C0D0220262F5E095FEAF0E05848B082A22B69728F1E1DEE5A4AA5211D897`；handoff 1,930 bytes/SHA=`68B5F9044F179B9F376F62BBFDFA1845F28CB5F361A13F21DD4F61EDD84AAD09`，均ReadOnly。

## 唯一 controlled standalone/direct LuaLaTeX build slot

- 新HANDOFF_ID：`A-R112-P067-SA2-DIRECT-BUILD-R7-20260827`。
- 唯一new root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R7_SA2_CDF_STEP_HANDLER_R112_DIRECT_BUILD_20260827`；主线授权前file=false、directory=false、parent=true。
- wrapper：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex`，当前388 bytes/SHA=`ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF`。
- engine固定为`D:\texlive\2026\bin\windows\lualatex.exe`；root-external PowerShell7 controller执行前AST0。允许恰一个真正typeset direct LuaLaTeX child，typeset invocation1、retry0、latexmk0、version probe0；不得并发或第二调用。
- `TEXMFVAR/TEXMFCACHE/TEXMFCONFIG`均绑定R7 root内唯一`texcache`；working directory固定wrapper所在目录，output directory固定R7 `build`。自然结束，不中止；首错即停且不自动retry。
- 成功门：controller/child exit0、natural=true/interrupted=false；PDF恰1；source before/after均4,014 bytes/SHA=`2881377A...0920`，wrapper before/after均388 bytes/SHA=`ADDF75D1...14BF`；terminal latexmk/lualatex/luatex/luahbtex0并立即释放槽。失败则如实回传，不得补跑。
- build结束后仅允许从该新PDF进行非TeX全量对象/all-pairs/native1x+nearest8x/灰度/page integration/真实manual复核，重点验证CDF各区间、open/filled endpoints、PMF相邻ticks及全部旧回归；不得复用R5 SA3 manual结论。
- 当前未授权commit、fresh角色、第二UID、第二source或central state/inventory写。仅在新PDF sealed LOCAL_SA2_PASS经主线接受后，才可另授唯一原子commit。

P662 completely fresh SA3同一实例并行，只读official R112/current P662 source；两链不得互相中止、查询或管理。inventory保持`31 SA1 / 38 SA2 / 1 SA3 / 29 local pass`。
