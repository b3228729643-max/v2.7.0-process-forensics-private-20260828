# Revision 541：P126 提交集成与 R116 唯一全书构建锁

时间：2026-08-28T18:19:15+08:00

## P126 原子提交验收与主线集成

- A 提交=`e2f4a08c6228f237bbbed9110b9d9f1c1b7f6042`，父提交=`a19fe984d7bde5d982081899c599c635e9965bed`，subject=`fix(fig-p126): correct coordinate descent geometry and legend`。
- 提交边界严格为唯一文件`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`，numstat=`38+/31-`，`git show --check`通过。
- Main 集成前分支=`v2.7.0/integration`、HEAD=`bd6efc7eaef9fc8fff82919e89934b60c2e2cbcf`、worktree/index clean；Main 目标源 blob 与 A 父提交目标源 blob 同为`9203a764919b1e31e2d7cd9dd1889c4617b1accc`。
- Main 仅执行一次精确 cherry-pick，生成集成提交=`f1874b2a4f1ffe823968d417019cfdc2c5641888`，父提交=`bd6efc7eaef9fc8fff82919e89934b60c2e2cbcf`；subject、唯一name-only与`38+/31-`均保持，worktree/index clean。
- 集成后P126源=4,686 bytes/SHA-256=`2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`。

## R116 只读 preflight

- Build script=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\build_v2.7.0.ps1`，6,379 bytes/SHA-256=`4DE115D8D99855273DB0E12511ABB983A17750684071FDA36E3F3FC51482CD65`。
- 唯一entry=`src\讲义源码\合并总册\main_full.tex`，185 bytes；DryRun解析为唯一`merged_full` target。
- 计划输出root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r116_fullbook`；pre-lock Leaf=false、Container=false、Any=false、Parent=true。
- Pre-lock `latexmk/lualatex/luatex/luahbtex=0/0/0/0`。
- DryRun确认engine=`lualatex`，参数含`-g -interaction=nonstopmode -file-line-error -halt-on-error`，`NoPublish=true`、`Resume=false`、network_required=false、automatic_install=false；未创建输出root或启动TeX。

## 唯一父调用锁

Main 仅授权一次：

`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r116_fullbook -NoPublish`

只允许一个PowerShell父链；内部latexmk自然收敛、LuaLaTeX与makeindex调用属于同一父链。禁止manual retry、`Resume`、第二父调用、并发TeX、source/Git/central写、fresh role、进程中断或管理。若失败或平台中断，保留输出并回Main裁决，不repair/restart。自然完成后先释放lock，再冻结PDF/log/index/page/font/navigation身份。成功构建本身不计图PASS或Goal完成；P126在R116冻结前保持SA2，P689永久冻结。

Inventory保持`30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`，严格最终`0/99`，B累计`66/66`。
