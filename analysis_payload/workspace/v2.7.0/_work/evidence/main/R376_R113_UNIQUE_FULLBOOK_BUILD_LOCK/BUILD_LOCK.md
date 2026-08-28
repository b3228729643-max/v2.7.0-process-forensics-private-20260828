# R376 R113 unique full-book build lock

时间：2026-08-27T17:41:27+08:00

- 前置闭合：P067新修复已集成，P662已计C_LOCAL_PASS；所有A/C在途角色归零并冻结。
- main branch=`v2.7.0/integration`，HEAD=`3bc644256d833272a789a7685b91996f98fa3336`，worktree/index clean。
- build script=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\build_v2.7.0.ps1`，6,379 bytes/SHA-256=`4DE115D8D99855273DB0E12511ABB983A17750684071FDA36E3F3FC51482CD65`。
- 唯一R113 output root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook`；锁定前file=false、directory=false。
- 锁定前`latexmk/lualatex/luatex/luahbtex` process count0。

唯一授权父调用：

`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r113_fullbook -NoPublish`

约束：恰一个PowerShell父调用；不得手工retry、Resume、第二父调用、并发A/B/C TeX、源写、commit、process interruption或新角色。latexmk内部自然多次LuaLaTeX/makeindex属于同一父链。失败或平台中断则保留输出原样回主线裁决，不自动修补/重启。自然完成后立即释放锁，并冻结PDF/log/index/page/font/navigation身份后才允许fresh review。

inventory保持`31 SA1 / 38 SA2 / 0 SA3 / 31 local pass`；严格最终0/99，B累计66/66。
