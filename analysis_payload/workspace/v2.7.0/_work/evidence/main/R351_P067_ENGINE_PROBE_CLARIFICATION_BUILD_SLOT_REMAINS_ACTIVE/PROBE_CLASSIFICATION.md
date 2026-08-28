# R351 P067 engine version probe 分类裁决

时间：2026-08-27T14:34:47+08:00

- A在R350实际controller、R3 root和排版启动前运行一次`D:\texlive\2026\bin\windows\lualatex.exe --version`，exit0，仅返回`LuaHBTeX 1.24.0 (TeX Live 2026)`，随后主动HOLD并请求口径裁决。
- 主线独立只读复核engine存在，6656 bytes，SHA-256 `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`；R3 build root仍file=false/dir=false；`latexmk/lualatex/luatex/luahbtex`进程0。
- 该命令不进入TeX排版、没有输入文档、没有aux/cache/PDF/root/source/wrapper写入。R350“唯一direct build”的控制意图是限制实际typeset、缓存和PDF生成，不把只读版本查询计为排版调用。
- 因此冻结计数为`engine_version_probe_count=1`、`typeset_invocation_count=0`；R350 build slot仍有效。A须在controller/build记录中分别披露两项计数；实际controller仍只允许一个direct lualatex typeset child、invocation1、retry0、latexmk0、无并发/自动重试/中止，其余R350边界不变。
