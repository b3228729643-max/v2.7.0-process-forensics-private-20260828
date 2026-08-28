# Revision 463：R115唯一全书构建锁

时间：2026-08-28T05:01:40+08:00

## 只读preflight

- Main branch=`v2.7.0/integration`，HEAD=`bd6efc7eaef9fc8fff82919e89934b60c2e2cbcf`，worktree/index clean。
- P109 integrated source=1,922 bytes/SHA `887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355`。
- Build script=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\build_v2.7.0.ps1`，6,379 bytes/SHA `4DE115D8D99855273DB0E12511ABB983A17750684071FDA36E3F3FC51482CD65`。
- Entry=`src\讲义源码\合并总册\main_full.tex`，存在且185 bytes；DryRun解析为唯一merged_full target。
- Output root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook`；pre-lock Leaf=false、Container=false、Any=false、Parent=true。
- Pre-lock `latexmk/lualatex/luatex/luahbtex=0/0/0/0`。
- DryRun确认engine=`lualatex`、`-g -interaction=nonstopmode -file-line-error -halt-on-error`、NoPublish、network_required=false、automatic_install=false；DryRun未创建输出或启动TeX。

## 唯一父调用锁

授权且仅授权Main执行一次：

`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r115_fullbook -NoPublish`

只允许一个PowerShell父链；内部latexmk自然收敛、LuaLaTeX与makeindex调用属于该同一父链。禁止manual retry、`Resume`、第二父调用、并发TeX、source/Git/central写、fresh role、进程中断或管理。若失败或平台中断，保留输出并回Main裁决，不repair/restart。自然完成后先释放lock，再冻结PDF/log/index/page/font/navigation身份；成功构建本身不计图PASS或Goal完成。

P680同一fresh SA3可继续纯只读manual/seal，不得查询、管理或中止该Main build chain。Inventory保持`31 SA1 / 33 SA2 / 1 SA3 / 35 local pass`，严格最终0/99，B累计66/66。
